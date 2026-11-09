"""Known-parameter SVN307 native filtering and sampled real-space assembly.

This evaluates the selected mathematical procedure in binary64. It does not
estimate parameters or qualify a historical compiled reconstruction runtime.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from math import asin, ceil, cos, hypot, isfinite, sin, trunc
from numbers import Integral, Real
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.fft import ifftn

from ._model import SimreconError
from ._optical_transfer import OpticalTransfer, OtfError, _valid_transfer, sample_otf
from ._preparation import _REFERENCE as _BAND_REFERENCE
from ._preparation import PreparedBands

_F64 = NDArray[np.float64]
_C128 = NDArray[np.complex128]
_I64 = NDArray[np.int64]
_INT_MAX = 2**31 - 1
_UINT_MAX = 2**32 - 1
_INTP_MAX = int(np.iinfo(np.intp).max)
_F32_MAX = float(np.finfo(np.float32).max)
_REFERENCE = (
    _BAND_REFERENCE[1],
    _BAND_REFERENCE[2],
    _BAND_REFERENCE[0],
    *_BAND_REFERENCE[3:],
)


class ReconstructionError(SimreconError):
    """Invalid known-parameter input or undefined reconstruction operation."""

    def __init__(self, message: str):
        super().__init__("reconstruction-domain", message)


@dataclass(frozen=True)
class KnownReconstruction:
    """Owned read-only signed image, filtered bands and resolved parameters.

    Image axes are (time, z, y, x). Coordinates are in micrometres; supplied
    fundamental carriers are in cycles per micrometre. Image values retain
    the upstream detector-count scale, without gain fitting or positivity.
    """

    image: _F64
    filtered_quadratures: _C128
    x_um: _F64
    y_um: _F64
    z_um: _F64
    carriers_cyc_um: _F64
    modulation: _C128
    radial_cutoff_cyc_um: float
    axial_cutoffs_bins: _I64
    resolved_settings: tuple[tuple[str, Any], ...]
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = _REFERENCE


@contextmanager
def _operation() -> Iterator[None]:
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            yield
    except ReconstructionError:
        raise
    except Exception as error:
        raise ReconstructionError(f"reconstruction operation failed: {error}") from error


def _integer(value: Any, name: str, minimum: int = 1) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise ReconstructionError(f"{name} must be an integer")
    result = int(value)
    if not minimum <= result <= _INT_MAX:
        raise ReconstructionError(f"{name} exceeds positive signed32 representation")
    return result


def _scalar(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ReconstructionError(f"{name} must be a real scalar")
    # Extract without losing value: narrow floats widen, integers avoid fixed-width
    # abs overflow, and longdouble retains its precision. Check before float().
    if isinstance(value, np.generic):
        value = value.item()
    magnitude: Any = abs(value)
    if magnitude > _F32_MAX:
        raise ReconstructionError(f"{name} exceeds float32 magnitude")
    result = float(value)
    if not isfinite(result) or (positive and result <= 0):
        raise ReconstructionError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _finite(value: Any, name: str) -> None:
    if not np.isfinite(value).all():
        raise ReconstructionError(f"{name} contains nonfinite or unresolved arithmetic")


def _positive(value: float, name: str) -> float:
    if not isfinite(value) or value <= 0:
        raise ReconstructionError(f"{name} must remain finite and positive")
    return value


def _extent(shape: tuple[int, ...], itemsize: int) -> None:
    extent = itemsize
    for dimension in reversed(shape):
        if not 0 < dimension <= _INTP_MAX:
            raise ReconstructionError("array dimension exceeds native representation")
        extent *= dimension
        if extent > _INTP_MAX:
            raise ReconstructionError(
                "array shape/strides/byte extent exceeds native representation"
            )


def _source_extent(value: int, limit: int, name: str) -> None:
    if not 0 < value <= limit:
        raise ReconstructionError(f"{name} exceeds source integer/byte representation")


def _parameter_array(value: Any, name: str, shape: tuple[int, ...], *, complex_ok: bool) -> Any:
    if not isinstance(value, np.ndarray) or value.shape != shape:
        raise ReconstructionError(f"{name} must be a NumPy array of shape {shape}")
    dtype = value.dtype
    valid = (
        (dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        or (dtype.char in "efd" and dtype.itemsize in (2, 4, 8))
        or (complex_ok and dtype.char in "FD" and dtype.itemsize in (8, 16))
    )
    if not valid:
        raise ReconstructionError(
            f"{name} requires a standard {'real/complex' if complex_ok else 'real'} dtype"
        )
    _extent(shape, 16 if complex_ok else 8)
    _finite(value, name)
    result = np.array(value, dtype=np.complex128 if complex_ok else np.float64, copy=True)
    if (np.abs(result.real) > _F32_MAX).any() or (np.abs(result.imag) > _F32_MAX).any():
        raise ReconstructionError(f"{name} components exceed float32 magnitude")
    return result


@dataclass(frozen=True)
class _Grid:
    shape: tuple[int, ...]
    orders: int
    lateral: int
    axial: int
    dxy: float
    dz: float
    scale: float

    @property
    def output_shape(self) -> tuple[int, int, int]:
        z, y, x = self.shape[3:]
        return self.axial * z, self.lateral * y, self.lateral * x


def _validate_bands(bands: Any) -> _Grid:
    if not isinstance(bands, PreparedBands):
        raise ReconstructionError("bands must be an actual PreparedBands record")
    if not isinstance(bands.input_shape, tuple) or len(bands.input_shape) != 6:
        raise ReconstructionError("bands input_shape must contain six dimensions")
    shape = tuple(_integer(n, "bands dimension") for n in bands.input_shape)
    t, d, p, z, y, x = shape
    if z < 2 or x < 2 or x % 2:
        raise ReconstructionError("bands require Z>=2 and even X>=2")
    q = bands.quadratures
    if not isinstance(q, np.ndarray) or q.ndim != 6 or q.dtype != np.complex128:
        raise ReconstructionError("bands quadratures must be complex128 with six axes")
    slots = q.shape[2]
    orders = (slots + 1) // 2
    if orders < 2 or slots % 2 != 1 or slots > p:
        raise ReconstructionError("bands require at least two orders and odd Q<=P")
    if q.shape != (t, d, slots, z, y, x // 2 + 1):
        raise ReconstructionError("bands quadratures disagree with input_shape")
    noise = bands.noise_variance_factors
    if not isinstance(noise, np.ndarray) or noise.dtype != np.float64 or noise.shape != (d, orders):
        raise ReconstructionError("bands noise_variance_factors must be float64 (D,O)")
    lateral = _integer(bands.lateral_zoom, "lateral_zoom")
    axial = _integer(bands.axial_zoom, "axial_zoom")
    if int(np.float32(lateral)) != lateral:
        raise ReconstructionError("lateral_zoom must have exact float32 representation")
    grid = _Grid(
        shape,
        orders,
        lateral,
        axial,
        _scalar(bands.dxy_um, "dxy_um", positive=True),
        _scalar(bands.dz_um, "dz_um", positive=True),
        _scalar(bands.input_scale, "input_scale", positive=True),
    )
    oz, oy, ox = grid.output_shape
    for name, count in (
        ("native volume", x * y * z),
        ("native half volume", (x // 2 + 1) * y * z),
        ("direction/order product", d * orders),
        ("quadrature/phase product", slots * p),
        ("output X", ox),
        ("output Y", oy),
        ("output Z", oz),
        ("output plane", ox * oy),
        ("output volume", ox * oy * oz),
        ("signed lookup bytes", ox * oy * 4),
    ):
        _source_extent(count, _INT_MAX, name)
    for name, count in (
        ("complex native workspace bytes", x * y * z * 8),
        ("complex output workspace bytes", ox * oy * oz * 8),
        ("real output bytes", ox * oy * oz * 4),
        ("order allocation bytes", orders * 8),
    ):
        _source_extent(count, _UINT_MAX, name)
    for array_shape, itemsize in (
        (q.shape, 16),
        (noise.shape, 8),
        ((d, 2), 8),
        ((d, orders), 16),
        ((z, y, x), 16),
        (grid.output_shape, 16),
        ((t, oz, oy, ox), 8),
        ((oy, ox), 16),
        ((ox,), 8),
        ((oy,), 8),
        ((oz,), 8),
        ((orders,), 8),
    ):
        _extent(array_shape, itemsize)
    expected_scale = 1 / (x * y * z * lateral**2 * axial * d)
    if grid.scale != expected_scale:
        raise ReconstructionError("bands input_scale disagrees with CE02 normalization")
    if bands.source_revision != "SVN307" or bands.reference_sha256 != _BAND_REFERENCE:
        raise ReconstructionError("bands source identity is invalid")
    _finite(q, "bands quadratures")
    _finite(noise, "bands noise_variance_factors")
    if (noise <= 0).any():
        raise ReconstructionError("bands noise_variance_factors must be positive")
    return grid


@dataclass(frozen=True)
class _Filter:
    transfer: OpticalTransfer
    carriers: _F64
    amplitudes: _C128
    inverse_noise: _F64
    dx: float
    dy: float
    dzf: float
    radius: float
    cutoffs: tuple[int, ...]
    taper_radius: float
    suppression_radius: float
    wiener_square: float
    suppress: bool
    dampen: bool
    omit: bool
    omit_kz0: bool
    cosine: bool

    def damping(self, direction: int, order: int, radius: float, z: int) -> float:
        value = float(self.inverse_noise[direction, order])
        if (
            self.suppress
            and radius <= self.suppression_radius
            and (order != 0 or (not self.dampen and not self.omit))
        ):
            value *= 1 / (1 + 1000 / (radius * radius + 0.2))
        elif order == 0 and self.dampen:
            if self.cutoffs[0] == 0:
                raise ReconstructionError("dampen_order0 evaluates division by zero axial cutoff")
            value *= (radius / self.radius) ** 2 + abs(z / self.cutoffs[0]) ** 3
        elif order == 0 and self.omit:
            value = 0.0
        if order == 0 and z == 0 and self.omit_kz0:
            value = 0.0
        _finite(value, "damping weight")
        return value

    def sample(self, order: int, x: float, y: float, z: int) -> complex:
        # Do not skip the accepted sampler when a later multiplier is zero.
        try:
            return complex(
                sample_otf(self.transfer, x, y, z, dkz_cyc_um=self.dzf, order=order).item()
            )
        except OtfError as error:
            raise ReconstructionError(f"transfer sampling failed: {error}") from error

    def scale(self, direction: int, order: int, x: float, y: float, z: int) -> complex:
        h = self.sample(order, x, y, z)
        g = self.damping(direction, order, hypot(x, y), z)
        amplitude = complex(self.amplitudes[direction, order])
        denominator = abs(h) ** 2 * abs(amplitude) ** 2 * g
        object_x = x + order * float(self.carriers[direction, 0])
        object_y = y + order * float(self.carriers[direction, 1])
        for other in range(self.carriers.shape[0]):
            for signed_order in range(1 - self.amplitudes.shape[1], self.amplitudes.shape[1]):
                if (other, signed_order) == (direction, order):
                    continue
                qx = object_x - signed_order * float(self.carriers[other, 0])
                qy = object_y - signed_order * float(self.carriers[other, 1])
                radius = hypot(qx, qy)
                _finite(radius, "overlap frequency")
                if radius < self.radius:
                    m = abs(signed_order)
                    other_h = self.sample(m, qx, qy, z)
                    other_g = self.damping(other, m, radius, z)
                    denominator += (
                        abs(other_h) ** 2 * abs(complex(self.amplitudes[other, m])) ** 2 * other_g
                    )
        denominator += self.wiener_square
        _positive(denominator, "filter denominator")
        scale = g * h.conjugate() / denominator
        if self.cosine:
            rho = hypot(object_x, object_y) / self.taper_radius
            if self.cutoffs[1] > 0:
                rho = hypot(rho, abs(z) / self.cutoffs[1])
            _finite(rho, "taper radius")
            scale *= cos((np.pi / 2) * min(rho, 1.0))
        if order:
            scale *= amplitude.conjugate()
        _finite(scale, "native filter scale")
        return scale


def _support(
    grid: _Grid, carriers: _F64, wavelength: int, na: float, immersion: float
) -> tuple[float, tuple[int, ...]]:
    le = (wavelength / immersion) / 1000
    lx = 0.88 * le
    theta = asin(na / immersion)
    b = hypot(float(carriers[0, 0]), float(carriers[0, 1]))
    for argument in (b * lx / 2, b * lx / 2 - 0.1 * sin(theta)):
        if not isfinite(argument) or not -1 <= argument <= 1:
            raise ReconstructionError("carrier asin argument is outside its real domain")
        asin(argument)
    radius = _positive(min(2 * na / (wavelength / 1000), 1 / (2 * grid.dxy)), "radial cutoff")
    dzf = _positive(1 / (grid.shape[3] * grid.dz), "axial sampling")
    cutoff = ((1 - cos(theta)) / le) / dzf
    _finite(cutoff, "axial cutoff")
    c0 = ceil(cutoff)
    cuts = [c0, *[trunc((1 + le / lx) * c0) for _ in range(grid.orders - 2)], trunc(1.3 * c0)]
    for c in cuts:
        if not 0 <= c <= _INT_MAX:
            raise ReconstructionError("axial cutoff exceeds source signed32 integer representation")
    limit = grid.shape[3] // 2
    return radius, tuple(max(limit - 1, 0) if c >= limit else c for c in cuts)


def _filter_quadratures(original: _C128, grid: _Grid, filtering: _Filter) -> _C128:
    filtered = original.copy()
    tcount, directions, _, zsize, ysize, _ = original.shape
    xsize = grid.shape[-1]
    ys = range(1 - ysize // 2, ysize // 2 + 1)
    xs = range(1 - xsize // 2, xsize // 2 + 1)
    for t in range(tcount):
        for d in range(directions):
            for m, cutoff in enumerate(filtering.cutoffs):
                slots: tuple[int, ...] = (0,) if m == 0 else (2 * m - 1, 2 * m)
                plus = np.zeros((zsize, ysize, xsize), np.complex128) if m else None
                for y in ys:
                    for x in xs:
                        if m == 0 and x < 0:
                            continue
                        reflected = x < 0
                        row, column = (-y % ysize, -x) if reflected else (y % ysize, x)
                        fx, fy = x * filtering.dx, y * filtering.dy
                        if hypot(fx, fy) <= filtering.radius:
                            for z in range(-cutoff, cutoff + 1):
                                scale = filtering.scale(d, m, fx, fy, z)
                                axial = (-z if reflected else z) % zsize
                                # Read prepared coefficients, before any relocation.
                                even = original[t, d, slots[0], axial, row, column]
                                if reflected:
                                    even = even.conjugate()
                                if m == 0:
                                    filtered[t, d, 0, axial, row, column] = even * scale
                                else:
                                    odd = original[t, d, 2 * m, axial, row, column]
                                    if reflected:
                                        odd = odd.conjugate()
                                    assert plus is not None
                                    plus[z % zsize, y % ysize, x % xsize] = (
                                        even + 1j * odd
                                    ) * scale
                        else:
                            for z in range(-cutoff, cutoff + 1):
                                for slot in slots:
                                    filtered[t, d, slot, z % zsize, row, column] = 0
                        for slot in slots:
                            filtered[t, d, slot, cutoff + 1 : zsize - cutoff, row, column] = 0
                if plus is not None:
                    for y in ys:
                        for x in range(xsize // 2 + 1):
                            for z in range(-cutoff, cutoff + 1):
                                p = plus[z % zsize, y % ysize, x]
                                n = plus[-z % zsize, -y % ysize, -x % xsize].conjugate()
                                filtered[t, d, 2 * m - 1, z % zsize, y % ysize, x] = (p + n) / 2
                                filtered[t, d, 2 * m, z % zsize, y % ysize, x] = (p - n) / (2j)
    _finite(filtered, "filtered quadrature result")
    return filtered


def _lift(index: int, length: int) -> int:
    return index if index <= length // 2 else index - length


def _assemble(
    filtered: _C128, grid: _Grid, carriers: _F64, omit: bool, x_um: _F64, y_um: _F64
) -> _F64:
    tcount, directions, _, zsize, ysize, _ = filtered.shape
    xsize = grid.shape[-1]
    oz, oy, ox = grid.output_shape
    image = np.zeros((tcount, oz, oy, ox), np.float64)
    for t in range(tcount):
        for d in range(directions):
            for m in range(int(omit), grid.orders):
                padded = np.zeros(grid.output_shape, np.complex128)
                for k in range(zsize):
                    z = _lift(k, zsize)
                    for i in range(ysize):
                        y = _lift(i, ysize)
                        for j in range(xsize):
                            x = _lift(j, xsize)
                            if x < 0:
                                zi, yi, xi = -z % zsize, -y % ysize, -x
                            else:
                                zi, yi, xi = z % zsize, y % ysize, x
                            even = filtered[t, d, 0 if m == 0 else 2 * m - 1, zi, yi, xi]
                            if x < 0:
                                even = even.conjugate()
                            value = even
                            if m:
                                odd = filtered[t, d, 2 * m, zi, yi, xi]
                                if x < 0:
                                    odd = odd.conjugate()
                                value += 1j * odd
                            padded[z % oz, y % oy, x % ox] = value
                _finite(padded, "embedded coefficients")
                spatial = cast(_C128, ifftn(padded, norm="forward"))
                _finite(spatial, "inverse transform result")
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * m
                        * (carriers[d, 0] * x_um[None, :] + carriers[d, 1] * y_um[:, None])
                    )
                    _finite(phase, "assembly carrier phase")
                    image[t] += 2 * (spatial * np.exp(1j * phase)).real
                _finite(image[t], "assembled image result")
    return image


def _readonly(array: Any) -> Any:
    _finite(array, "result")
    array.setflags(write=False)
    return array


def reconstruct_known(
    bands: PreparedBands,
    transfer: OpticalTransfer,
    *,
    carriers_cyc_um: Any,
    modulation: Any,
    wavelength_nm: int,
    numerical_aperture: float,
    immersion_index: float,
    wiener: float,
    suppress_singularities: bool = True,
    suppression_radius_bins: float = 10.0,
    dampen_order0: bool = False,
    omit_order0: bool = False,
    omit_kz0: bool = False,
    output_taper: str = "cosine",
) -> KnownReconstruction:
    """Filter native bands and assemble a signed image with supplied parameters.

    Parameters
    ----------
    bands : PreparedBands
        Actual CE02 bands; at least two orders and Z>=2 are required.
    transfer : OpticalTransfer
        Complete accepted CE03 radial or full tables shared across directions.
    carriers_cyc_um : numpy.ndarray
        Fundamental (kx, ky), shape (direction, 2), cycles per micrometre.
    modulation : numpy.ndarray
        Complex positive-side modulation, shape (direction, orders-1).
    wavelength_nm : int
        Emission wavelength, 1 through 32767 nanometres.
    numerical_aperture, immersion_index : float
        Positive aperture <= min(2, immersion); immersion in [1, 2].
    wiener : float
        Explicit positive Wiener parameter; its square enters each denominator.
    suppress_singularities : bool, optional
        Apply source physical-radius suppression, including default order zero.
    suppression_radius_bins : float, optional
        Signed outer suppression radius in units of the smaller lateral step.
    dampen_order0, omit_order0, omit_kz0 : bool, optional
        Source order-zero branches. Dampening precedes omission in weights;
        final assembly omits order zero whenever omit_order0 is true.
    output_taper : {'cosine', 'none'}, optional
        Shifted object-frequency cosine taper after division, or no taper.

    Returns
    -------
    KnownReconstruction
        Owned read-only image, quadratures, coordinates and exact settings.

    Raises
    ------
    ReconstructionError
        For invalid inputs, unsafe actual transfer stencils, representation or
        numerical failures. Allocation/backend failures retain their causes.
    """
    with _operation():
        grid = _validate_bands(bands)
        transfer = _valid_transfer(transfer)
        if transfer.norders < grid.orders:
            raise ReconstructionError("transfer has insufficient orders")
        wavelength = _integer(wavelength_nm, "wavelength_nm")
        if wavelength > 32767:
            raise ReconstructionError("wavelength_nm exceeds signed-short representation")
        na = _scalar(numerical_aperture, "numerical_aperture", positive=True)
        immersion = _scalar(immersion_index, "immersion_index", positive=True)
        if not 1 <= immersion <= 2:
            raise ReconstructionError("immersion_index must lie in [1,2]")
        if na > min(2, immersion):
            raise ReconstructionError("numerical_aperture exceeds caller physical domain")
        w = _scalar(wiener, "wiener", positive=True)
        square = _positive(w * w, "wiener square")
        sr_bins = _scalar(suppression_radius_bins, "suppression_radius_bins")
        flags = {
            "suppress_singularities": suppress_singularities,
            "dampen_order0": dampen_order0,
            "omit_order0": omit_order0,
            "omit_kz0": omit_kz0,
        }
        for name, flag in flags.items():
            if not isinstance(flag, (bool, np.bool_)):
                raise ReconstructionError(f"{name} must be a boolean")
        if not isinstance(output_taper, str) or output_taper not in ("cosine", "none"):
            raise ReconstructionError("output_taper must be cosine or none")
        directions = grid.shape[1]
        carriers = _parameter_array(
            carriers_cyc_um, "carriers_cyc_um", (directions, 2), complex_ok=False
        )
        mods = _parameter_array(
            modulation, "modulation", (directions, grid.orders - 1), complex_ok=True
        )
        radius, cuts = _support(grid, carriers, wavelength, na, immersion)
        dx = _positive(1 / (grid.shape[-1] * grid.dxy), "dxy sampling")
        dy = _positive(1 / (grid.shape[-2] * grid.dxy), "dxy sampling")
        dzf = _positive(1 / (grid.shape[-3] * grid.dz), "dz sampling")
        amplitudes = np.ones((directions, grid.orders), np.complex128)
        amplitudes[:, 1:] = mods
        inverse_noise = 1 / np.array(bands.noise_variance_factors, dtype=np.float64, copy=True)
        _finite(inverse_noise, "inverse noise weight")
        taper_radius = _positive(radius + hypot(*carriers[0]) * (grid.orders - 1), "taper cutoff")
        sr = sr_bins * min(dx, dy)
        _finite(sr, "suppression radius")
        filtering = _Filter(
            transfer,
            carriers,
            amplitudes,
            inverse_noise,
            dx,
            dy,
            dzf,
            radius,
            cuts,
            taper_radius,
            sr,
            square,
            bool(suppress_singularities),
            bool(dampen_order0),
            bool(omit_order0),
            bool(omit_kz0),
            output_taper == "cosine",
        )
        original = np.array(bands.quadratures, dtype=np.complex128, copy=True)
        filtered = _filter_quadratures(original, grid, filtering)
        oz, oy, ox = grid.output_shape
        x_um = (np.arange(ox, dtype=np.float64) - ox // 2) * (grid.dxy / grid.lateral)
        y_um = (np.arange(oy, dtype=np.float64) - oy // 2) * (grid.dxy / grid.lateral)
        z_um = (np.arange(oz, dtype=np.float64) - oz // 2) * (grid.dz / grid.axial)
        for vector in (x_um, y_um, z_um):
            _finite(vector, "physical coordinates")
        image = _assemble(filtered, grid, carriers, bool(omit_order0), x_um, y_um)
        resolved = (
            ("wavelength_nm", wavelength),
            ("numerical_aperture", na),
            ("immersion_index", immersion),
            ("wiener", w),
            ("suppress_singularities", bool(suppress_singularities)),
            ("suppression_radius_bins", sr_bins),
            ("dampen_order0", bool(dampen_order0)),
            ("omit_order0", bool(omit_order0)),
            ("omit_kz0", bool(omit_kz0)),
            ("output_taper", output_taper),
            ("dxy_um", grid.dxy),
            ("dz_um", grid.dz),
            ("lateral_zoom", grid.lateral),
            ("axial_zoom", grid.axial),
            ("input_scale", grid.scale),
        )
        return KnownReconstruction(
            _readonly(image),
            _readonly(filtered),
            _readonly(x_um),
            _readonly(y_um),
            _readonly(z_um),
            _readonly(carriers),
            _readonly(mods),
            radius,
            _readonly(np.array(cuts, dtype=np.int64)),
            resolved,
        )
