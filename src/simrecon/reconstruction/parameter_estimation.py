"""Finite SVN307 carrier search and complex modulation estimation.

Carriers are fundamental (kx, ky) vectors in cycles per micrometre; native
arrays use (z, y, x) axes. The two overlap sides retain complex transfer
weighting and unnormalized inverse Fourier sums. See
``docs/architecture/reconstruction-walkthrough.md#carrier-and-modulation-estimation``
for the overlap/regression equations and
``docs/architecture/reconstruction-walkthrough.md#axes-units-and-fourier-conventions``
for axes, units and transform signs.
"""

from __future__ import annotations

import math
import struct
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ..acquisition.layout import integer as _acquisition_integer
from ..acquisition.layout import scalar as _acquisition_scalar
from ..acquisition.modes import AcquisitionBands, _UsedBands, validate_downstream_bands
from ..acquisition.preparation import _REFERENCE as _BAND_REFERENCE
from ..acquisition.preparation import PreparedBands
from ..models import SimreconError
from ..optical_transfer import (
    OpticalTransfer,
    OtfError,
    _sample_transfer,
    _Transfer,
    validate_optical_transfer,
)

_Array = NDArray[Any]
_I32 = 2**31 - 1
_INTP = int(np.iinfo(np.intp).max)
_F32 = float(np.finfo(np.float32).max)
_REFERENCE = (_BAND_REFERENCE[1], _BAND_REFERENCE[2], _BAND_REFERENCE[0], *_BAND_REFERENCE[3:])


class ParameterEstimationError(SimreconError):
    """Invalid estimation input or undefined finite estimation operation."""

    def __init__(self, message: str):
        super().__init__("parameter-estimation", message)


@dataclass(frozen=True)
class _Overlap:
    index: int
    time_index: int
    direction_index: int
    purpose: str
    orders: tuple[int, int]
    carrier_cyc_um: _Array
    fourier: _Array
    spatial: _Array
    written: _Array


@dataclass(frozen=True)
class _Event:
    kind: str
    time_index: int
    direction_index: int
    details: tuple[tuple[str, Any], ...]


@dataclass(frozen=True)
class EstimatedParameters:
    """Owned immutable carrier, modulation, overlap and finite-search records.

    Carriers have axes (time, direction, xy) in cycles per micrometre.
    Modulation arrays have axes (time, direction, positive order). Overlap
    arrays retain the unnormalized native Fourier and spatial representations.
    """

    carriers_cyc_um: _Array
    modulation: _Array
    raw_modulation: _Array
    initial_carriers_cyc_um: _Array
    branches: tuple[tuple[str, ...], ...]
    overlaps: tuple[_Overlap, ...]
    trace: tuple[_Event, ...]
    radial_cutoff_cyc_um: float
    axial_cutoff_bins: int
    resolved_settings: tuple[tuple[str, Any], ...]
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = _REFERENCE


@contextmanager
def _operation() -> Iterator[None]:
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            yield
    except ParameterEstimationError:
        raise
    except Exception as error:
        raise ParameterEstimationError(
            f"parameter estimation operation failed ({type(error).__name__}): {error}"
        ) from error


def _finite(value: Any, name: str) -> None:
    if not np.isfinite(value).all():
        raise ParameterEstimationError(f"{name}: nonfinite or unresolved arithmetic")


def _integer(value: Any, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ParameterEstimationError(f"{name} must be an integer scalar")
    result = int(value)
    _signed(result, name)
    if result < 1:
        raise ParameterEstimationError(f"{name} must be positive")
    return result


def _signed(value: int, name: str) -> None:
    if not -(2**31) <= value <= _I32:
        raise ParameterEstimationError(f"{name} exceeds signed32 source representation")


def _scalar(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ParameterEstimationError(f"{name} must be a nonboolean real scalar")
    if isinstance(value, np.generic):
        value = value.item()
    magnitude: Any = abs(value)
    if magnitude > _F32:
        raise ParameterEstimationError(f"{name} exceeds float32 magnitude")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ParameterEstimationError(
            f"{name} must be finite" + (" and positive" if positive else "")
        )
    return result


def _extent(shape: tuple[int, ...], itemsize: int) -> None:
    extent = itemsize
    for n in reversed(shape):
        if not 0 < n <= _INTP:
            raise ParameterEstimationError("array dimension exceeds native intp representation")
        extent *= n
        if extent > _INTP:
            raise ParameterEstimationError("array shape/stride/byte extent exceeds native intp")


def _append(sequence: list[Any], value: Any) -> None:
    # Bound the actual eventual immutable container, independently of all other
    # payloads. Allocation failures below this native bound retain their cause.
    if sys.getsizeof(()) + (len(sequence) + 1) * struct.calcsize("P") > _INTP:
        raise ParameterEstimationError("trace/overlap container exceeds native representation")
    sequence.append(value)


def _owned(value: _Array) -> _Array:
    _extent(value.shape, value.dtype.itemsize)
    result = np.array(value, copy=True)
    result.flags.writeable = False
    return result


def _real_array(
    value: Any, name: str, shape: tuple[int, ...], *, require_actual: bool = False
) -> _Array:
    if require_actual:
        value = np.asarray(value) if issubclass(type(value), np.ndarray) else None
    if not isinstance(value, np.ndarray) or value.shape != shape:
        raise ParameterEstimationError(f"{name} must be a NumPy array of shape {shape}")
    dtype = value.dtype
    if not (
        (dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        or (dtype.char in "efd" and dtype.itemsize in (2, 4, 8))
    ):
        raise ParameterEstimationError(f"{name} requires standard real numeric dtype")
    _extent(shape, 8)
    _finite(value, name)
    result = np.array(value, dtype=np.float64, copy=True)
    if (result > _F32).any() or (result < -_F32).any():
        raise ParameterEstimationError(f"{name} exceeds float32 magnitude")
    return result


@dataclass(frozen=True)
class _Grid:
    shape: tuple[int, ...]
    orders: int
    dxy: float
    dz: float
    lateral: int | float
    axial: int
    scale: float
    dx: float
    dy: float
    dzf: float
    mode: str = "3d"


def _validate_bands(bands: Any, transfer: _Transfer) -> tuple[_Grid, _UsedBands | None]:
    if issubclass(type(bands), AcquisitionBands):
        used = validate_downstream_bands(bands)
        shape = used.shape
        z, y, x = shape[3:]
        k = transfer.samples.shape[-1] if transfer.layout == "radial" else transfer.samples.shape[1]
        if used.mode == "2d" and k != 1:
            raise ParameterEstimationError("true 2d bands require transfer axial K=1")
        dzf = 1 / (z * used.dz) if used.dz > 0 else transfer.dkz_cyc_um
        frequencies = (1 / (x * used.dxy), 1 / (y * used.dxy), dzf)
        if any(not math.isfinite(f) or f <= 0 for f in frequencies):
            raise ParameterEstimationError("derived sampling must remain finite and positive")
        t, d = shape[:2]
        for sh, size in (
            ((2, z, y, x), 16),
            ((2, z, y, x), 1),
            ((t, d, 2), 8),
            ((t, d, used.orders - 1), 16),
        ):
            _extent(sh, size)
        grid = _Grid(
            shape,
            used.orders,
            used.dxy,
            used.dz,
            used.lateral,
            used.axial,
            used.scale,
            *frequencies,
            mode=used.mode,
        )
        return grid, used
    if not isinstance(bands, PreparedBands):
        raise ParameterEstimationError("bands must be a PreparedBands or AcquisitionBands record")
    if not isinstance(bands.input_shape, tuple) or len(bands.input_shape) != 6:
        raise ParameterEstimationError("bands input_shape requires six dimensions")
    shape = tuple(_integer(n, "bands dimension") for n in bands.input_shape)
    t, d, p, z, y, x = shape
    if z < 2 or x < 2 or x % 2:
        raise ParameterEstimationError("bands require Z>=2 and even X>=2")
    q = bands.quadratures
    if not isinstance(q, np.ndarray) or q.ndim != 6 or q.dtype != np.complex128:
        raise ParameterEstimationError("bands quadratures require six-axis complex128")
    slots = q.shape[2]
    orders = (slots + 1) // 2
    if slots % 2 != 1 or orders < 2 or slots > p:
        raise ParameterEstimationError("bands require at least two orders and odd Q<=P")
    if q.shape != (t, d, slots, z, y, x // 2 + 1):
        raise ParameterEstimationError("bands quadratures disagree with input_shape")
    noise = bands.noise_variance_factors
    if not isinstance(noise, np.ndarray) or noise.dtype != np.float64 or noise.shape != (d, orders):
        raise ParameterEstimationError("bands noise_variance_factors require float64 (D,O)")
    lateral = _integer(bands.lateral_zoom, "lateral_zoom")
    axial = _integer(bands.axial_zoom, "axial_zoom")
    if float(np.float32(lateral)) != lateral:
        raise ParameterEstimationError("lateral_zoom requires exact source float32 representation")
    dxy = _scalar(bands.dxy_um, "dxy_um", positive=True)
    dz = _scalar(bands.dz_um, "dz_um", positive=True)
    scale = _scalar(bands.input_scale, "input_scale", positive=True)
    for name, count in (
        ("quadrature count", slots),
        ("quadrature/phase product", slots * p),
        ("direction/order product", d * orders),
        ("CE02 real-transform extent", (x + 2) * y * z),
        ("CE02 direction/phase/axial product", d * p * z),
        ("native plane", x * y),
        ("native volume", x * y * z),
        ("native half volume", (x // 2 + 1) * y * z),
    ):
        _signed(count, name)
    for array_shape, size in (
        (q.shape, 16),
        (noise.shape, 8),
        ((2, z, y, x), 16),
        ((2, z, y, x), 1),
        ((y, x), 16),
        ((t, d, 2), 8),
        ((t, d, orders - 1), 16),
        ((d, 2), 8),
        ((orders - 1,), 8),
    ):
        _extent(array_shape, size)
    # The retained CE02 scale is a used field, not a hidden checksum of raw data.
    if scale != 1 / (x * y * z * lateral**2 * axial * d):
        raise ParameterEstimationError("bands input_scale disagrees with CE02 normalization")
    if bands.source_revision != "SVN307" or bands.reference_sha256 != _BAND_REFERENCE:
        raise ParameterEstimationError("bands source/reference identity is invalid")
    _finite(q, "bands quadratures")
    _finite(noise, "bands noise_variance_factors")
    if (noise <= 0).any():
        raise ParameterEstimationError("bands noise_variance_factors must be positive")
    frequencies = (1 / (x * dxy), 1 / (y * dxy), 1 / (z * dz))
    if any(not math.isfinite(f) or f <= 0 for f in frequencies):
        raise ParameterEstimationError(
            "derived sampling frequencies must remain finite and positive"
        )
    return _Grid(shape, orders, dxy, dz, lateral, axial, scale, *frequencies), None


class _ParameterEstimator:
    """Keep owned working quadratures and ordered records for one estimation call.

    Notes
    -----
    ``t`` and ``d`` select the current time and direction. Each overlap and
    diagnostic captures those indices; trials append records in execution order.
    """

    def __init__(
        self,
        quadratures: _Array,
        transfer: _Transfer,
        grid: _Grid,
        radial: float,
        cutoff: int,
        omit: bool,
    ):
        self.grid = grid
        self.data = np.array(quadratures, copy=True)
        self.transfer = transfer
        self.radial = radial
        self.cutoff = cutoff
        self.omit = omit
        self.overlaps: list[_Overlap] = []
        self.trace: list[_Event] = []
        self.t = 0
        self.d = 0

    def record_event(self, kind: str, **details: Any) -> None:
        """Append a finite diagnostic, copying array details into read-only storage.

        Parameters
        ----------
        kind : str
            Diagnostic identity; keyword order is retained in the detail tuple.
        **details : Any
            Stage-specific scalar values or arrays captured at the current t/d.
        """
        captured = []
        for name, value in details.items():
            if isinstance(value, np.ndarray):
                _finite(value, f"{kind} {name}")
                value = _owned(value)
            elif isinstance(value, (float, complex)):
                _finite(value, f"{kind} {name}")
            captured.append((name, value))
        _append(self.trace, _Event(kind, self.t, self.d, tuple(captured)))

    def sample_order_transfer(self, xy: tuple[float, float], z: int, order: int) -> complex:
        """Sample the complex order transfer at a lateral vector and axial bin.

        Parameters
        ----------
        xy : tuple of float
            (kx, ky) in cycles per micrometre, with the overlap's signed shift.
        z : int
            Signed axial Fourier bin; ``grid.dzf`` supplies cycles/um per bin.
        order : int
            Nonnegative transfer order.

        Returns
        -------
        complex
            Interpolated transfer, retaining its phase.
        """
        try:
            return complex(
                _sample_transfer(
                    self.transfer, xy[0], xy[1], z, dkz_cyc_um=self.grid.dzf, order=order
                ).item()
            )
        except OtfError as error:
            raise ParameterEstimationError(f"transfer sample/stencil failed: {error}") from error

    def reconstruct_complex_band(self, order: int, z: int, i: int, j: int) -> complex:
        """Read B0 or E+iO from native half-x quadrature storage.

        Parameters
        ----------
        order : int
            Zero for B0, otherwise the positive harmonic to combine.
        z, i, j : int
            Axial bin and full-grid y/x indices before half-space reflection.

        Returns
        -------
        complex
            Band coefficient. Reflection conjugates E and O separately before
            forming E+iO; the harmonic combination itself is not conjugated.
        """
        _, _, _, nz, ny, nx = self.grid.shape
        reflected = j > nx // 2
        if reflected:
            z, i, j = (-z) % nz, (-i) % ny, nx - j
        else:
            z %= nz
        q = self.data[self.t, self.d]
        first = complex(q[0 if order == 0 else 2 * order - 1, z, i, j])
        if reflected:
            first = first.conjugate()
        if order == 0:
            return first
        second = complex(q[2 * order, z, i, j])
        if reflected:
            second = second.conjugate()
        result = first + 1j * second
        _finite(result, "complex band combination")
        return result

    def build_order_overlap(
        self, carrier: _Array, order: int, purpose: str, lower: int = 0
    ) -> _Overlap:
        """Construct and record the two transfer-weighted order overlaps.

        Parameters
        ----------
        carrier : numpy.ndarray
            Fundamental (kx, ky) in cycles/um, before order-difference scaling.
        order, lower : int
            Higher and lower orders; their difference sets the lateral shift.
        purpose : str
            Diagnostic stage retained with the new overlap record.

        Returns
        -------
        _Overlap
            Read-only Fourier/spatial arrays of shape (2, Z, Y, X), the actual
            write mask, and an owned carrier copy. Side zero weights the lower
            band by the shifted higher transfer; side one reverses the roles.

        Notes
        -----
        Weighting divides by sqrt(|H_lower|**2 + |H_higher|**2), retaining the
        other transfer's complex phase. Sampling short-circuits on support and
        preceding transfer thresholds. The inverse transform is an unnormalized positive
        sum, as in the walkthrough's carrier-and-modulation-estimation section.
        """
        _, _, _, nz, ny, nx = self.grid.shape
        fourier = np.zeros((2, nz, ny, nx), dtype=np.complex128)
        written = np.zeros(fourier.shape, dtype=np.bool_)
        delta = ((order - lower) * float(carrier[0]), (order - lower) * float(carrier[1]))
        # The selected 3D map weights the higher-order threshold by five;
        # true 2D uses one. These are amplitude tests, not extra band weights.
        higher_multiplier = 1 if nz == 1 else 5
        _finite(delta, "order carrier separation")
        for i in range(ny):
            fy = (i if i <= ny // 2 else i - ny) * self.grid.dy
            for j in range(nx):
                fx = (j if j <= nx // 2 else j - nx) * self.grid.dx
                if math.hypot(fx, fy) > self.radial:
                    continue
                minus = (fx - delta[0], fy - delta[1])
                plus = (fx + delta[0], fy + delta[1])
                _finite((*minus, *plus), "shifted overlap frequencies")
                # Independent branches, in source order. Samples are requested
                # only after each preceding mask/threshold has succeeded.
                for side, shifted in ((0, minus), (1, plus)):
                    if math.hypot(*shifted) > self.radial:
                        continue
                    for z in range(-self.cutoff, self.cutoff + 1):
                        if z == 0 and self.omit:
                            continue
                        primary = self.sample_order_transfer(
                            (fx, fy), z, lower if side == 0 else order
                        )
                        if not ((1 if side == 0 else higher_multiplier) * abs(primary) > 0.006):
                            continue
                        other = self.sample_order_transfer(
                            shifted, z, order if side == 0 else lower
                        )
                        if not ((higher_multiplier if side == 0 else 1) * abs(other) > 0.006):
                            continue
                        denominator = math.sqrt(abs(primary) ** 2 + abs(other) ** 2)
                        _finite(denominator, "overlap denominator")
                        value = (
                            self.reconstruct_complex_band(lower if side == 0 else order, z, i, j)
                            * other
                            / denominator
                        )
                        _finite(value, "weighted overlap")
                        fourier[side, z % nz, i, j] = value
                        written[side, z % nz, i, j] = True
        # Undo NumPy's inverse normalization to retain the native overlap sum.
        axes = (2, 3) if nz == 1 else (1, 2, 3)
        spatial = np.fft.ifftn(fourier, axes=axes) * (nx * ny * nz)
        _finite(spatial, "overlap inverse transform")
        for array in (fourier, spatial, written):
            array.flags.writeable = False
        result = _Overlap(
            len(self.overlaps),
            self.t,
            self.d,
            purpose,
            (lower, order),
            _owned(carrier),
            fourier,
            spatial,
            written,
        )
        _append(self.overlaps, result)
        return result

    def fit_overlap_modulation(
        self,
        build: _Overlap,
        carrier: _Array,
        stage: str,
        remake: bool,
        angle: float | None = None,
        magnitude: float | None = None,
    ) -> tuple[complex, float | None]:
        """Fit forward modulation and record the full regression diagnostics.

        Parameters
        ----------
        build : _Overlap
            Fixed lower/higher spatial arrays and their order pair.
        carrier : numpy.ndarray
            Fundamental (kx, ky), cycles/um, for the positive centered ramp.
        stage : str
            Diagnostic stage; ``known`` omits the search objective calculation.
        remake : bool
            Recorded overlap-rebuild flag for this evaluation.
        angle, magnitude : float or None
            Trial polar coordinates, radians and cycles/um, when available.

        Returns
        -------
        complex
            Forward factor C/SX, with C=sum(conj(lower)*ramped_higher).
        float or None
            Squared forward magnitude for search, or None for a known carrier.

        Notes
        -----
        SX and SY are the respective spatial energies. Reverse/combined fits
        and normalized correlation remain diagnostics, including their existing
        singularity rules. See the walkthrough regression equations; the ramp
        uses centered spatial pixels and the positive order-difference phase.
        """
        _, _, _, _, ny, nx = self.grid.shape
        order = build.orders[1] - build.orders[0]
        x = np.arange(nx, dtype=np.float64) - nx // 2
        y = np.arange(ny, dtype=np.float64) - ny // 2
        phase = (
            2
            * math.pi
            * order
            * self.grid.dxy
            * (x[None, :] * carrier[0] + y[:, None] * carrier[1])
        )
        _finite(phase, "centered positive phase ramp")
        lower = build.spatial[0]
        higher = build.spatial[1] * np.exp(1j * phase)
        sx = float(np.sum(np.abs(lower) ** 2))
        sy = float(np.sum(np.abs(higher) ** 2))
        cross = complex(np.sum(np.conjugate(lower) * higher))
        _finite((sx, sy, cross), "regression energies/cross")
        if sx <= 0:
            raise ParameterEstimationError("no lower overlap energy (SX)")
        if sy <= 0:
            raise ParameterEstimationError("no higher overlap energy (SY)")
        if sx == sy:
            raise ParameterEstimationError("equal-energy combined-fit singularity")
        forward = cross / sx
        reverse = cross.conjugate() / sy
        difference = sx - sy
        numerator = 2 * abs(cross)
        ratio = numerator / difference
        _finite((difference, numerator, ratio), "combined regression ratio")
        beta = 0.5 * math.atan(ratio)
        if beta < 0:
            beta += math.pi / 2
        tangent = math.tan(beta)
        _finite(tangent, "combined regression tangent")
        combined = (
            0j
            if cross == 0
            else tangent
            * complex(
                math.cos(math.atan2(cross.imag, cross.real)),
                math.sin(math.atan2(cross.imag, cross.real)),
            )
        )
        power = abs(cross) * abs(cross)
        product = sx * sy
        _finite((power, product), "correlation numerator/denominator")
        correlation = math.sqrt(power / product)
        objective = None if stage == "known" else abs(forward) * abs(forward)
        _finite((forward, reverse, combined, correlation), "regression factors")
        if objective is not None:
            _finite(objective, "squared-forward objective")
        self.record_event(
            "evaluation",
            stage=stage,
            orders=build.orders,
            overlap_index=build.index,
            remake_overlaps=remake,
            angle_rad=angle,
            magnitude_cyc_um=magnitude,
            carrier_cyc_um=carrier,
            SX=sx,
            SY=sy,
            cross=cross,
            forward=forward,
            reverse=reverse,
            combined=combined,
            correlation=correlation,
            objective=objective,
        )
        return forward, objective

    def estimate_coarse_carrier(self, initial: _Array) -> _Array:
        """Locate the first strict correlation maximum and refine its position.

        Parameters
        ----------
        initial : numpy.ndarray
            Declared fundamental (kx, ky), cycles/um, used to build the overlap
            and select the literal ordered alias adjustments.

        Returns
        -------
        numpy.ndarray
            Fundamental carrier from pair (0, 1) in 2D or (0, 2) in 3D.

        Notes
        -----
        The forward Fourier sum has negative phase. Neighbor fits use wrapped
        bins; strict comparisons retain the first maximum in y-then-x traversal.
        """
        pair_order = 1 if self.grid.shape[3] == 1 else 2
        build = self.build_order_overlap(initial, pair_order, "coarse")
        _, _, _, _, ny, nx = self.grid.shape
        product = np.sum(build.spatial[0] * np.conjugate(build.spatial[1]), axis=0)
        correlation = np.fft.fft2(product)
        power = np.abs(correlation) ** 2
        _finite(correlation, "coarse forward transform")
        _finite(power, "coarse correlation power")
        best, i0, j0 = -1e11, 0, 0
        for i in range(ny):
            for j in range(nx):
                if float(power[i, j]) > best:
                    best, i0, j0 = float(power[i, j]), i, j
        xn = np.array([power[i0, (j0 - 1) % nx], power[i0, j0], power[i0, (j0 + 1) % nx]])
        yn = np.array([power[(i0 - 1) % ny, j0], power[i0, j0], power[(i0 + 1) % ny, j0]])
        ox, xs = _fit_peak_offset(xn)
        oy, ys = _fit_peak_offset(yn)
        px, py = j0 + ox, i0 + oy
        before = np.array([px, py], dtype=np.float64)
        # Retain the source's literal initial-carrier products and alias order.
        oldx, oldy = float(initial[0]) * self.grid.dx, float(initial[1]) * self.grid.dy
        _finite((oldx, oldy), "initial carrier alias products")
        decisions = []
        for axis, sign in ((0, -1), (0, 1), (1, -1), (1, 1)):
            position, old, size = (px, oldx, nx) if axis == 0 else (py, oldy, ny)
            selected = old < position - size // 2 if sign == -1 else old > position + size // 2
            decisions.append(bool(selected))
            if selected:
                if axis == 0:
                    px += sign * nx
                else:
                    py += sign * ny
        carrier = np.array(
            [px * self.grid.dx / pair_order, py * self.grid.dy / pair_order], dtype=np.float64
        )
        _finite(carrier, "coarse carrier")
        self.record_event(
            "coarse",
            overlap_index=build.index,
            correlation_complex=correlation,
            correlation_power=power,
            integer_peak_xy=(j0, i0),
            x_neighbors=xn,
            y_neighbors=yn,
            x_offset=ox,
            y_offset=oy,
            x_offset_status=xs,
            y_offset_status=ys,
            peak_before_alias_xy=before,
            alias_decisions=tuple(decisions),
            peak_after_alias_xy=np.array([px, py], dtype=np.float64),
            carrier_cyc_um=carrier,
        )
        return carrier

    def search_carrier_and_modulation(self, initial: _Array) -> tuple[_Array, list[complex]]:
        """Refine a coarse carrier by finite angle then magnitude trials.

        Parameters
        ----------
        initial : numpy.ndarray
            Declared fundamental (kx, ky), cycles/um, for the coarse search.

        Returns
        -------
        numpy.ndarray
            Fitted fundamental carrier in cycles/um.
        list of complex
            Forward factors in ascending positive-order slots, before caller
            postprocessing. In 2D, later orders use adjacent-order overlaps.

        Notes
        -----
        Trials use one frozen refinement overlap. Angle steps are 0.001 radians;
        magnitude steps are 0.1/(max(X,Y)*dxy) cycles/um. Each walk ends at the
        first failure of strict improvement, followed by a three-point fit.
        This finite procedure does not promise a global optimum.
        """
        coarse = self.estimate_coarse_carrier(initial)
        cx, cy = float(coarse[0]), float(coarse[1])
        if cx == 0 and cy == 0:
            raise ParameterEstimationError("zero coarse carrier: undefined polar angle atan2(0,0)")
        mag0 = math.hypot(cx, cy)
        angle0 = math.pi if cy == 0 and cx < 0 else math.atan2(cy, cx)
        _finite((mag0, angle0), "coarse polar conversion")
        pair_order = 1 if self.grid.shape[3] == 1 else 2
        build = self.build_order_overlap(coarse, pair_order, "refinement")
        # These bracket values carry across the angle and magnitude stages.
        x1, amp1 = 0.0, 0.0
        first = True

        def objective(angle: float, magnitude: float, stage: str) -> float:
            nonlocal first
            carrier = _carrier_from_polar(angle, magnitude)
            _, score = self.fit_overlap_modulation(build, carrier, stage, first, angle, magnitude)
            first = False
            assert score is not None
            return score

        def bracket(
            stage: str, branch: str, x2: float, amp2: float, x3: float, amp3: float
        ) -> None:
            self.record_event(
                "bracket",
                stage=stage,
                branch=branch,
                x1=x1,
                amp1=amp1,
                x2=x2,
                amp2=amp2,
                x3=x3,
                amp3=amp3,
                strict_improvement=amp3 > amp2,
            )

        angle = angle0
        magnitude = mag0
        dm = 0.1 / (max(self.grid.shape[4:]) * self.grid.dxy)
        if not math.isfinite(dm) or dm <= 0:
            raise ParameterEstimationError("unresolved finite magnitude search step")

        def score(coordinate: float, stage: str, fixed_angle: float) -> float:
            return (
                objective(coordinate, mag0, stage)
                if stage == "angle"
                else objective(fixed_angle, coordinate, stage)
            )

        for stage, start, step in (("angle", angle0, 0.001), ("magnitude", mag0, dm)):
            x2 = start
            amp2 = score(x2, stage, angle)
            x3 = _advance_search_coordinate(start, step)
            amp3 = score(x3, stage, angle)
            bracket(stage, "initial", x2, amp2, x3, amp3)
            if amp3 > amp2:
                candidate = x3
                direction = step
                bracket(stage, "positive", x2, amp2, x3, amp3)
            else:
                candidate = start
                direction = -step
                amp2, amp3 = amp3, amp2
                x2, x3 = x3, x2
                bracket(stage, "negative-swap", x2, amp2, x3, amp3)
            while amp3 > amp2:
                amp1, x1 = amp2, x2
                amp2, x2 = amp3, x3
                candidate = _advance_search_coordinate(candidate, direction)
                x3 = candidate
                amp3 = score(candidate, stage, angle)
                bracket(stage, "shift", x2, amp2, x3, amp3)
            bracket(stage, "stop", x2, amp2, x3, amp3)
            fitted, status = _fit_three_point_peak(x1, amp1, x2, amp2, x3, amp3)
            self.record_event(
                "parabola",
                stage=stage,
                x1=x1,
                y1=amp1,
                x2=x2,
                y2=amp2,
                x3=x3,
                y3=amp3,
                result=fitted,
                status=status,
            )
            if stage == "angle":
                angle = fitted
            else:
                magnitude = fitted
        carrier = _carrier_from_polar(angle, magnitude)
        factor, _ = self.fit_overlap_modulation(build, carrier, "final", False, angle, magnitude)
        factors = [0j] * (self.grid.orders - 1)
        factors[pair_order - 1] = factor
        for order in range(1, self.grid.orders):
            if order != pair_order:
                lower = order - 1 if self.grid.shape[3] == 1 else 0
                other = self.build_order_overlap(carrier, order, "later-order", lower)
                factors[order - 1], _ = self.fit_overlap_modulation(
                    other, carrier, "later-order", True, angle, magnitude
                )
        return carrier, factors


def _carrier_from_polar(angle: float, magnitude: float) -> _Array:
    """Convert a finite angle (radians) and magnitude (cycles/um) to (kx, ky).

    Parameters
    ----------
    angle : float
        Polar angle in radians.
    magnitude : float
        Carrier magnitude in cycles per micrometre.

    Returns
    -------
    numpy.ndarray
        Two float64 Cartesian carrier components in cycles per micrometre.
    """
    _finite((angle, magnitude), "fitted polar coordinates")
    result = np.array([magnitude * math.cos(angle), magnitude * math.sin(angle)], dtype=np.float64)
    _finite(result, "Cartesian fitted carrier")
    return result


def _advance_search_coordinate(value: float, step: float) -> float:
    """Advance a finite search coordinate, rejecting overflow or stagnation.

    Parameters
    ----------
    value, step : float
        Current coordinate and signed step, both radians or both cycles/um.

    Returns
    -------
    float
        Representably distinct next coordinate.
    """
    result = value + step
    if not math.isfinite(result) or result == value:
        raise ParameterEstimationError("nonfinite or stagnant finite-search candidate increment")
    return result


def _fit_peak_offset(values: _Array) -> tuple[float, str]:
    """Fit the sub-bin offset from equally spaced minus/center/plus powers.

    Parameters
    ----------
    values : numpy.ndarray
        Three neighboring correlation powers, spaced one Fourier bin apart.

    Returns
    -------
    float
        Negative slope/curvature, or zero for the retained fallback rules.
    str
        Diagnostic status: zero curvature, outside the literal 1.5-bin range,
        or a fitted offset.
    """
    minus, center, plus = (float(v) for v in values)
    slope = (plus - minus) / 2
    curvature = plus + minus - 2 * center
    _finite((slope, curvature), "coarse peak parabola")
    if curvature == 0:
        return 0.0, "zero-curvature"
    result = -slope / curvature
    _finite(result, "coarse peak offset")
    if result > 1.5 or result < -1.5:
        return 0.0, "outside-range"
    return result, "fitted"


def _fit_three_point_peak(
    x1: float, y1: float, x2: float, y2: float, x3: float, y3: float
) -> tuple[float, str]:
    """Fit a peak coordinate from the three ordered finite-search samples.

    Parameters
    ----------
    x1, x2, x3 : float
        Trial coordinates in radians or cycles/um; spacing need not be uniform.
    y1, y2, y3 : float
        Corresponding squared-forward objectives in the carried bracket order.

    Returns
    -------
    float
        Fitted coordinate, or the literal zero fallback for duplicate coordinates
        or zero curvature.
    str
        Status retained in the parabola diagnostic.
    """
    if x1 in (x2, x3) or x2 == x3:
        return 0.0, "duplicate-coordinate"
    sum1, sum2 = x1 + x2, x2 + x3
    dx1, dx2 = x2 - x1, x3 - x2
    dy1, dy2 = y2 - y1, y3 - y2
    _finite((sum1, sum2, dx1, dx2, dy1, dy2), "general parabola coordinate arithmetic")
    b1, b2 = sum1 / 2, sum2 / 2
    s1, s2 = dy1 / dx1, dy2 / dx2
    _finite((b1, b2, s1, s2), "general parabola midpoints/slopes")
    ds, db = s2 - s1, b2 - b1
    _finite((ds, db), "general parabola curvature differences")
    curvature = ds / db
    _finite(curvature, "general parabola curvature")
    if curvature == 0:
        return 0.0, "zero-curvature"
    displacement = s2 / curvature
    _finite(displacement, "general parabola displacement")
    result = b2 - displacement
    _finite(result, "general parabola fitted result")
    return result, "fitted"


def estimate_parameters(
    bands: PreparedBands | AcquisitionBands,
    transfer: OpticalTransfer,
    *,
    initial_carriers_cyc_um: _Array,
    wavelength_nm: int,
    numerical_aperture: float,
    immersion_index: float,
    search_carriers: bool = True,
    use_time0_carriers: bool = True,
    amplitude_floors: _Array | None = None,
    fit_all_phases: bool = True,
    omit_kz0: bool = False,
) -> EstimatedParameters:
    """Estimate carriers and complex positive-order modulation by the finite C map.

    Parameters
    ----------
    bands : PreparedBands or AcquisitionBands
        Accepted native quadratures and used preparation metadata.
    transfer : OpticalTransfer
        Accepted CE03 complete complex radial or full transfer tables.
    initial_carriers_cyc_um : numpy.ndarray
        Real (direction, 2) resolved fundamental carrier vectors, cycles/um.
    wavelength_nm : int
        Wavelength in nanometres, from 1 through 32767.
    numerical_aperture, immersion_index : float
        Positive optical aperture and index, with NA <= index and 1 <= index <= 2.
    search_carriers, use_time0_carriers : bool, optional
        Search with order pair (0,1) in 2D or (0,2) in 3D and reuse time-zero carriers.
        Reused carriers receive fresh modulation fits at each time.
    amplitude_floors : numpy.ndarray or None, optional
        Positive real floors for all positive orders, or disabled.
    fit_all_phases, omit_kz0 : bool, optional
        Retain all fitted phases and optionally skip axial zero during fitting.

    Returns
    -------
    EstimatedParameters
        Owned read-only arrays and complete immutable operation records.

    Raises
    ------
    ParameterEstimationError
        For invalid inputs, unsafe source representation or sampling, singular
        helper arithmetic, or unresolved numerical/backend/allocation operations.

    Notes
    -----
    ``raw_modulation`` captures direct fits before the 2D cumulative products.
    Magnitude floors preserve phase; optional higher-order phase replacement
    uses multiples of the post-floor order-one phase. Time-zero carrier reuse
    still builds overlaps and fits modulation from each current time's data.
    See ``docs/architecture/reconstruction-walkthrough.md#carrier-and-modulation-estimation``
    and ``#axes-units-and-fourier-conventions`` for equations and conventions.
    """
    with _operation():
        for name, flag in (
            ("search_carriers", search_carriers),
            ("use_time0_carriers", use_time0_carriers),
            ("fit_all_phases", fit_all_phases),
            ("omit_kz0", omit_kz0),
        ):
            if type(flag) is not bool:
                raise ParameterEstimationError(f"{name} must be an actual boolean")
        table = validate_optical_transfer(
            transfer, require_actual=issubclass(type(bands), AcquisitionBands)
        )
        grid, used = _validate_bands(bands, table)
        if search_carriers and grid.orders < (2 if grid.shape[3] == 1 else 3):
            raise ParameterEstimationError(
                "carrier search requires two orders in 2d or three in 3d"
            )
        if table.norders < grid.orders:
            raise ParameterEstimationError("transfer requires all used orders")
        acquisition = used is not None
        resolve_integer = _acquisition_integer if acquisition else _integer
        resolve_scalar = _acquisition_scalar if acquisition else _scalar
        wavelength = resolve_integer(wavelength_nm, "wavelength_nm")
        if wavelength > 32767:
            raise ParameterEstimationError("wavelength_nm exceeds 32767")
        na = resolve_scalar(numerical_aperture, "numerical_aperture", positive=True)
        index = resolve_scalar(immersion_index, "immersion_index", positive=True)
        if not 1 <= index <= 2 or na > min(2, index):
            raise ParameterEstimationError(
                "numerical_aperture/immersion_index outside optical domain"
            )
        times, directions = grid.shape[:2]
        initial = _real_array(
            initial_carriers_cyc_um,
            "initial_carriers_cyc_um",
            (directions, 2),
            require_actual=acquisition,
        )
        floors = None
        if amplitude_floors is not None:
            if grid.orders > 25:
                raise ParameterEstimationError("amplitude floors require O<=25")
            floors = _real_array(
                amplitude_floors, "amplitude_floors", (grid.orders - 1,), require_actual=acquisition
            )
            if (floors <= 0).any():
                raise ParameterEstimationError("amplitude_floors must be strictly positive")
        wavelength_um = wavelength / 1000
        medium_wavelength = (wavelength / index) / 1000
        alpha = math.asin(na / index)
        radial = min(2 * na / wavelength_um, 1 / (2 * grid.dxy))
        cutoff_real = ((1 - math.cos(alpha)) / medium_wavelength) / grid.dzf
        _finite((radial, cutoff_real), "optical radial/axial cutoff")
        cutoff = math.ceil(cutoff_real)
        _signed(cutoff, "axial cutoff before cast")
        z = grid.shape[3]
        if cutoff > z // 2:
            cutoff = max(z // 2 - 1, 0)
        _signed(z + cutoff, "wrapped axial z+Z")
        quadratures = bands.quadratures if used is None else used.quadratures
        estimator = _ParameterEstimator(quadratures, table, grid, radial, cutoff, omit_kz0)
        carriers = np.empty((times, directions, 2), dtype=np.float64)
        raw = np.empty((times, directions, grid.orders - 1), dtype=np.complex128)
        modulation = np.empty_like(raw)
        branches: list[tuple[str, ...]] = []
        for t in range(times):
            row: list[str] = []
            estimator.t = t
            for d in range(directions):
                estimator.d = d
                if search_carriers and not (t > 0 and use_time0_carriers):
                    carrier, factors = estimator.search_carrier_and_modulation(initial[d])
                    branch = "searched"
                else:
                    if search_carriers and t > 0 and use_time0_carriers:
                        carrier = carriers[0, d].copy()
                        branch = "time0-reused"
                        estimator.record_event("reuse", source_time=0, carrier_cyc_um=carrier)
                    else:
                        carrier = initial[d].copy()
                        branch = "known"
                    factors = []
                    for order in range(1, grid.orders):
                        build = estimator.build_order_overlap(carrier, order, "known")
                        factor, _ = estimator.fit_overlap_modulation(build, carrier, "known", True)
                        factors.append(factor)
                carriers[t, d] = carrier
                raw[t, d] = factors
                if grid.shape[3] == 1:
                    for b in range(1, len(factors)):
                        direct, previous = factors[b], factors[b - 1]
                        factors[b] *= previous
                        _finite(factors[b], "cumulative modulation product")
                        estimator.record_event(
                            "cumulative-product",
                            order=b + 1,
                            direct_forward=direct,
                            previous_cumulative=previous,
                            product=factors[b],
                        )
                after_floor = list(factors)
                applied = [False] * len(factors)
                for b, factor in enumerate(factors):
                    magnitude = abs(factor)
                    _finite(magnitude, "raw modulation magnitude")
                    if floors is not None and magnitude < float(floors[b]):
                        if magnitude == 0:
                            raise ParameterEstimationError(
                                "zero modulation: undefined amplitude floor scaling"
                            )
                        scale = float(floors[b]) / magnitude
                        _finite(scale, "amplitude floor scaling")
                        after_floor[b] = factor * scale
                        _finite(after_floor[b], "amplitude floor result")
                        applied[b] = True
                phi = None
                if not fit_all_phases:
                    if after_floor[0] == 0:
                        raise ParameterEstimationError(
                            "undefined order-one phase for phase replacement"
                        )
                    phi = math.atan2(after_floor[0].imag, after_floor[0].real)
                for b, factor in enumerate(after_floor):
                    replaced = not fit_all_phases and b >= 1
                    final = factor
                    if replaced:
                        assert phi is not None
                        phase = (b + 1) * phi
                        _finite(phase, "selected order phase replacement")
                        final = abs(factor) * complex(math.cos(phase), math.sin(phase))
                    _finite(final, "final modulation")
                    modulation[t, d, b] = final
                    estimator.record_event(
                        "adjustment",
                        order=b + 1,
                        raw_forward=factors[b],
                        floor=None if floors is None else float(floors[b]),
                        floor_applied=applied[b],
                        after_floor=factor,
                        phase_replaced=replaced,
                        final=final,
                    )
                _append(row, branch)
            _append(branches, tuple(row))
        settings = tuple(
            dict(
                wavelength_nm=wavelength,
                numerical_aperture=na,
                immersion_index=index,
                search_carriers=search_carriers,
                use_time0_carriers=use_time0_carriers,
                amplitude_floors=None if floors is None else tuple(float(f) for f in floors),
                fit_all_phases=fit_all_phases,
                omit_kz0=omit_kz0,
                dxy_um=grid.dxy,
                dz_um=grid.dz,
                lateral_zoom=grid.lateral,
                axial_zoom=grid.axial,
                input_scale=grid.scale,
            ).items()
        )
        if used is not None:
            settings += (
                ("acquisition_mode", grid.mode),
                ("acquisition_reference_sha256", used.reference),
            )
        return EstimatedParameters(
            _owned(carriers),
            _owned(modulation),
            _owned(raw),
            _owned(initial),
            tuple(branches),
            tuple(estimator.overlaps),
            tuple(estimator.trace),
            radial,
            cutoff,
            settings,
        )
