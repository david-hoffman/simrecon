"""Known-parameter SVN307 native filtering and sampled real-space assembly.

This evaluates the selected mathematical procedure in binary64. It does not
estimate parameters or qualify a historical compiled reconstruction runtime.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from math import asin, atan2, ceil, cos, hypot, isfinite, sin, sqrt, tan, trunc
from numbers import Integral, Real
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.fft import ifftn

from ._acquisition_layout import ModeEvent, event
from ._acquisition_modes import AcquisitionBands, validate_used
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
    mode_trace: tuple[ModeEvent, ...] = ()
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
    lateral: int | float
    axial: int
    dxy: float
    dz: float
    scale: float
    mode: str = "3d"

    @property
    def output_shape(self) -> tuple[int, int, int]:
        z, y, x = self.shape[3:]
        return self.axial * z, int(self.lateral * y), int(self.lateral * x)


def _validate_bands(bands: Any) -> _Grid:
    if isinstance(bands, AcquisitionBands):
        shape, orders, lateral, axial, dxy, dz, scale, mode = validate_used(bands)
        for sh, size in (((shape[1], 2), 8), ((shape[1], orders), 16), (shape[3:], 16)):
            _extent(sh, size)
        return _Grid(shape, orders, lateral, axial, dxy, dz, scale, mode=mode)
    if not isinstance(bands, PreparedBands):
        raise ReconstructionError("bands must be a PreparedBands or AcquisitionBands record")
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


def _wrap_once(angle: float) -> float:
    if angle > np.pi:
        return angle - 2 * np.pi
    if angle < -np.pi:
        return angle + 2 * np.pi
    return angle


def _between_angle(angle: float, first: float, second: float) -> bool:
    lo, hi = min(first, second), max(first, second)
    if hi - lo < np.pi / 2:
        return angle > lo and angle <= hi
    return (angle > 0 and angle > hi and angle - 2 * np.pi <= lo) or (
        angle < 0 and angle <= lo and angle + 2 * np.pi > hi
    )


class _Precise:
    def __init__(
        self, carriers: _F64, orders: int, radius: float, trace: list[ModeEvent], time: int
    ):
        self.carriers, self.orders, self.radius = carriers, orders, radius
        self.trace, self.time = trace, time
        directions = len(carriers)
        angles = []
        for x, y in carriers:
            if x == 0 and y == 0:
                raise ReconstructionError("precise precompute: undefined zero carrier polar angle")
            angles.append(np.pi if y == 0 and x < 0 else atan2(y, x))
        starts = [angle - np.pi / (2 * directions) for angle in angles]
        self.boundaries = [_wrap_once(v) for v in (*starts, *(v + np.pi for v in starts))]
        _finite(self.boundaries, "precise sector boundaries")
        event(
            trace,
            "sector-boundaries",
            time,
            0,
            carrier_angles_rad=np.array(angles),
            boundary_angles_rad=np.array(self.boundaries),
        )

    def next_start(self, direction: int) -> float:
        target = self.boundaries[direction] + np.pi / len(self.carriers)
        best, saved = 2 * np.pi, direction
        for j, boundary in enumerate(self.boundaries):
            difference = _wrap_once(target - boundary)
            if abs(difference) < best:
                best, saved = abs(difference), j
        return self.boundaries[saved]

    def rho(self, x: float, y: float, direction: int) -> float:
        if x == 0 and y == 0:
            raise ReconstructionError("precise taper: undefined zero object-frequency polar angle")
        angle = np.pi if y == 0 and x < 0 else atan2(y, x)
        next_boundaries = [self.next_start(d) for d in range(len(self.carriers))]
        selected = None
        for d, boundary in enumerate(next_boundaries):
            if _between_angle(angle, self.boundaries[d], boundary) or _between_angle(
                angle, self.boundaries[d + len(self.carriers)], _wrap_once(boundary + np.pi)
            ):
                selected = d
                break
        if selected is None:
            raise ReconstructionError("precise taper sector leaves uninitialized intersection")
        x0, y0 = (self.orders - 1) * self.carriers[selected]
        k = tan(angle)
        v, denominator = x0 + k * y0, 1 + k * k
        discriminant = v * v - denominator * (x0 * x0 + y0 * y0 - self.radius * self.radius)
        _finite((k, v, denominator, discriminant), "precise tangent/intersection")
        if discriminant < 0:
            raise ReconstructionError("precise taper has negative discriminant")
        root = sqrt(discriminant)
        plus, minus = (v + root) / denominator, (v - root) / denominator
        limit = max(hypot(plus, k * plus), hypot(minus, k * minus))
        _positive(limit, "precise intersection limit")
        rho = hypot(x, y) / limit
        _finite(rho, "precise rho")
        event(
            self.trace,
            "precise-query",
            self.time,
            direction,
            object_frequency_xy=np.array([x, y]),
            angle_rad=float(angle),
            next_boundaries=np.array(next_boundaries),
            selected_direction=selected,
            discriminant=float(discriminant),
            limit=float(limit),
            rho=float(rho),
        )
        return rho


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
    power_exponent: float | None = None
    precise: _Precise | None = None
    overlaps: bool = True

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
                if not self.overlaps and not (order == 0 and signed_order == 0):
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
        if self.cosine or self.power_exponent is not None:
            if self.precise is not None and self.cutoffs[1] <= 0:
                rho = self.precise.rho(object_x, object_y, direction)
            else:
                rho = hypot(object_x, object_y) / self.taper_radius
                if self.cutoffs[1] > 0:
                    rho = hypot(rho, abs(z) / self.cutoffs[1])
            _finite(rho, "taper radius")
            rho = min(rho, 1.0)
            if self.cosine:
                scale *= cos((np.pi / 2) * rho)
            else:
                assert self.power_exponent is not None
                if rho == 1 and self.power_exponent < 0:
                    raise ReconstructionError("negative power taper at zero base is singular")
                scale *= (1 - rho) ** self.power_exponent
        if order:
            scale *= amplitude.conjugate()
        _finite(scale, "native filter scale")
        return scale


def _support(
    grid: _Grid, carriers: _F64, wavelength: int, na: float, immersion: float, dzf: float
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
    filtered: _C128,
    grid: _Grid,
    carriers: _F64,
    omit: bool,
    x_um: _F64,
    y_um: _F64,
    explode: float = 1.0,
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
                if zsize == 1:
                    spatial = np.zeros_like(padded)
                    spatial[0] = cast(_C128, ifftn(padded[0], norm="forward"))
                else:
                    spatial = cast(_C128, ifftn(padded, norm="forward"))
                _finite(spatial, "inverse transform result")
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * explode
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
    bands: PreparedBands | AcquisitionBands,
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
    wiener_increment: float = 0.0,
    power_taper_exponent: float | None = None,
    precise_taper: bool = False,
    filter_overlaps: bool = True,
    explode_factor: float = 1.0,
) -> KnownReconstruction:
    """Filter native bands and assemble a signed image with supplied parameters.

    Parameters
    ----------
    bands : PreparedBands or AcquisitionBands
        At least two orders are required. AcquisitionBands also supports native Z1.
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
    output_taper : {'cosine', 'none', 'power'}, optional
        Shifted object-frequency taper after native division. Power requires an exponent.
    wiener_increment : float, optional
        Full-series increment, applied as increment/T before each time.
    power_taper_exponent : float or None, optional
        Required exponent for power taper; exponent zero gives constant one.
    precise_taper : bool, optional
        Precompute source sectors and use their defined 2D intersections.
    filter_overlaps : bool, optional
        Include all overlaps, or only other center powers for center orders.
    explode_factor : float, optional
        Signed assembly-phase multiplier; filtering uses original carriers.

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
        increment = _scalar(wiener_increment, "wiener_increment")
        explode = _scalar(explode_factor, "explode_factor")
        exponent = (
            None
            if power_taper_exponent is None
            else _scalar(power_taper_exponent, "power_taper_exponent")
        )
        sr_bins = _scalar(suppression_radius_bins, "suppression_radius_bins")
        flags = {
            "suppress_singularities": suppress_singularities,
            "dampen_order0": dampen_order0,
            "omit_order0": omit_order0,
            "omit_kz0": omit_kz0,
            "precise_taper": precise_taper,
            "filter_overlaps": filter_overlaps,
        }
        for name, flag in flags.items():
            if not isinstance(flag, (bool, np.bool_)):
                raise ReconstructionError(f"{name} must be a boolean")
        if not issubclass(type(output_taper), str):
            raise ReconstructionError("output_taper must be cosine, none or power")
        taper_text = str.__str__(output_taper)
        extended = (
            isinstance(bands, AcquisitionBands)
            or increment != 0
            or exponent is not None
            or precise_taper
            or not filter_overlaps
            or explode != 1
            or taper_text == "power"
        )
        if extended:
            output_taper = taper_text
        taper_choices = ("cosine", "none", "power") if extended else ("cosine", "none")
        if output_taper not in taper_choices:
            raise ReconstructionError("output_taper must be cosine, none or power")
        power = extended and output_taper == "power"
        if power and exponent is None:
            raise ReconstructionError("output_taper='power' requires power_taper_exponent")
        if grid.mode == "2d":
            k = (
                transfer.samples.shape[-1]
                if transfer.layout == "radial"
                else transfer.samples.shape[1]
            )
            if k != 1:
                raise ReconstructionError("true 2d bands require transfer axial K=1")
        directions = grid.shape[1]
        carriers = _parameter_array(
            carriers_cyc_um, "carriers_cyc_um", (directions, 2), complex_ok=False
        )
        mods = _parameter_array(
            modulation, "modulation", (directions, grid.orders - 1), complex_ok=True
        )
        dzf = _positive(
            1 / (grid.shape[3] * grid.dz) if grid.dz > 0 else transfer.dkz_cyc_um, "dz sampling"
        )
        radius, cuts = _support(grid, carriers, wavelength, na, immersion, dzf)
        dx = _positive(1 / (grid.shape[-1] * grid.dxy), "dxy sampling")
        dy = _positive(1 / (grid.shape[-2] * grid.dxy), "dxy sampling")
        amplitudes = np.ones((directions, grid.orders), np.complex128)
        amplitudes[:, 1:] = mods
        inverse_noise = 1 / np.array(bands.noise_variance_factors, dtype=np.float64, copy=True)
        _finite(inverse_noise, "inverse noise weight")
        taper_radius = _positive(radius + hypot(*carriers[0]) * (grid.orders - 1), "taper cutoff")
        sr = sr_bins * min(dx, dy)
        _finite(sr, "suppression radius")
        original = np.array(bands.quadratures, dtype=np.complex128, copy=True)
        filtered = np.empty_like(original)
        mode_trace: list[ModeEvent] = []
        effective = []
        step = increment / grid.shape[0]
        current = w
        for t in range(grid.shape[0]):
            previous = current
            current = _positive(current + step, "effective Wiener parameter")
            square = _positive(current * current, "wiener square")
            effective.append(current)
            if extended:
                event(
                    mode_trace,
                    "wiener-step",
                    t,
                    0,
                    previous=previous,
                    increment=step,
                    effective=current,
                )
            precise = (
                _Precise(carriers, grid.orders, radius, mode_trace, t) if precise_taper else None
            )
            filtering = _Filter(
                transfer,
                carriers,
                amplitudes,
                inverse_noise[t] if isinstance(bands, AcquisitionBands) else inverse_noise,
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
                exponent if power else None,
                precise,
                bool(filter_overlaps),
            )
            filtered[t : t + 1] = _filter_quadratures(original[t : t + 1], grid, filtering)
        oz, oy, ox = grid.output_shape
        x_um = (np.arange(ox, dtype=np.float64) - ox // 2) * (grid.dxy / grid.lateral)
        y_um = (np.arange(oy, dtype=np.float64) - oy // 2) * (grid.dxy / grid.lateral)
        z_um = (np.arange(oz, dtype=np.float64) - oz // 2) * (grid.dz / grid.axial)
        for vector in (x_um, y_um, z_um):
            _finite(vector, "physical coordinates")
        image = _assemble(filtered, grid, carriers, bool(omit_order0), x_um, y_um, explode)
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
        if extended:
            resolved += (
                ("acquisition_mode", grid.mode),
                ("wiener_increment", increment),
                ("effective_wiener", tuple(effective)),
                ("power_taper_exponent", exponent),
                ("precise_taper", bool(precise_taper)),
                ("filter_overlaps", bool(filter_overlaps)),
                ("explode_factor", explode),
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
            tuple(mode_trace),
        )
