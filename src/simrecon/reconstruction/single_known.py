"""Explicit single-storage, mixed-arithmetic stationary known reconstruction.

Declared half spectra already carry the CE04 normalization. Transfer sampling
and filter decisions retain binary64/complex128 arithmetic; consumed scales,
coefficients, spectra and inverse samples use complex64. Signed contributions
accumulate in binary64 before the final binary32 image conversion.
"""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from hashlib import sha256
from math import cos, floor, hypot, isfinite
from numbers import Real
from typing import TYPE_CHECKING, Any, Protocol, cast

import numpy as np
import scipy
import scipy.fft
from numpy.typing import NDArray

from ..optical_transfer import _REFERENCE as _OTF_REFERENCE
from ..optical_transfer import (
    OpticalTransfer,
    OtfError,
    _Transfer,
    validate_optical_transfer,
)
from .known_parameters import (
    _F32_MAX,
    _INT_MAX,
    _INTP_MAX,
    _REFERENCE,
    ReconstructionError,
    _extent,
    _Grid,
    _integer,
    calculate_native_support,
    signed_fourier_index,
)

if TYPE_CHECKING:
    _ParameterArray = NDArray[
        np.integer[Any] | np.float16 | np.float32 | np.float64 | np.complex64 | np.complex128
    ]

    class _ComparableMagnitude(Protocol):
        """Unconverted real magnitude supporting the declared scalar bound."""

        def __le__(self, other: float, /) -> bool | np.bool_:
            """Compare with the binary64 bound without converting this value."""
            ...


_C64 = NDArray[np.complex64]
_C128 = NDArray[np.complex128]
_F32 = NDArray[np.float32]
_F64 = NDArray[np.float64]
_I64 = NDArray[np.int64]
_Shape = tuple[int, int, int, int, int, int]
_PROFILE = "single-mixed-v1"
_MAPPING = "ce04-svn307-v1"
_BLOCK = 65536


@dataclass(frozen=True)
class PreparedBands32:
    """Canonical independent, owned declarations of single-storage half spectra.

    Quadrature axes are (time, direction, slot, z, y, half-x), with slots
    0,E1,O1,... . Noise has axes (time, direction, order), including order zero.
    Sampling uses micrometres; provenance preserves caller declarations only.
    """

    quadratures: _C64
    noise_variance_factors: _F64
    input_shape: _Shape
    input_scale: float
    dxy_um: float
    dz_um: float
    lateral_zoom: int
    axial_zoom: int
    mapping_revision: str
    precision_profile: str
    provenance: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class KnownReconstruction32:
    """Owned single-storage diagnostics and signed binary32 sampled image.

    Coordinates and supplied carriers retain binary64, modulation complex128.
    Precision provenance describes the interface and declared input identities;
    unknown backend internals remain explicitly unknown.
    """

    image: _F32
    filtered_quadratures: _C64
    x_um: _F64
    y_um: _F64
    z_um: _F64
    carriers_cyc_um: _F64
    modulation: _C128
    radial_cutoff_cyc_um: float
    axial_cutoffs_bins: _I64
    resolved_settings: tuple[tuple[str, Any], ...]
    mode_trace: tuple[()] = ()
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = _REFERENCE
    precision_profile: str = _PROFILE
    precision_provenance: tuple[tuple[str, str], ...] = ()


def _fail(stage: str, message: str) -> None:
    raise ReconstructionError(f"{_PROFILE} {stage}: {message}")


@contextmanager
def _operation(stage: str) -> Iterator[None]:
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            yield
    except ReconstructionError as error:
        if _PROFILE in str(error):
            raise
        raise ReconstructionError(f"{_PROFILE} {stage}: {error}") from error
    except Exception as error:
        raise ReconstructionError(f"{_PROFILE} {stage} failed: {error}") from error


def _blocks(array: NDArray[Any], dtype: Any = None) -> Iterator[NDArray[Any]]:
    """Iterate bounded logical C-order blocks without a whole-array conversion."""
    if array.flags.c_contiguous and (dtype is None or array.dtype == np.dtype(dtype)):
        # These are views, including for finite scans of the derived c128 ramp.
        # Do not allocate a second numerical buffer for that purpose.
        flat = array.reshape(-1)
        for start in range(0, array.size, _BLOCK):
            yield flat[start : start + _BLOCK]
        return
    options: dict[str, Any] = {}
    if dtype is not None:
        options["op_dtypes"] = [np.dtype(dtype)]
    with np.nditer(
        array,
        flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=["readonly"],
        order="C",
        buffersize=_BLOCK,
        **options,
    ) as iterator:
        # One ndarray operand yields one ndarray block. NumPy's common nditer
        # stub describes only the tuple form used for multiple operands.
        for block in cast("Iterator[NDArray[Any]]", iterator):
            for start in range(0, block.size, _BLOCK):
                yield block[start : start + _BLOCK]


def _finite(array: Any, stage: str) -> None:
    if isinstance(array, np.ndarray):
        for block in _blocks(array):
            if not np.isfinite(block).all():
                _fail(stage, "nonfinite arithmetic or values")
    elif not isfinite(array):
        _fail(stage, "nonfinite arithmetic or value")


def _real(value: float, stage: str, *, positive: bool = False) -> float:
    if not isfinite(value) or (positive and value <= 0):
        _fail(stage, "required value must remain finite" + (" and positive" if positive else ""))
    return value


def _complex(value: complex, stage: str) -> complex:
    _real(value.real, stage)
    _real(value.imag, stage)
    return value


def _builtin_integer(value: Any, name: str) -> int:
    if type(value) is not int or not 1 <= value <= _INT_MAX:
        _fail(name, "requires a positive exact Python int within signed32 representation")
    return value


def _scalar(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        _fail(name, "requires a nonboolean real scalar")
    original = value.item() if isinstance(value, np.generic) else value
    # This original-value comparison excludes NaN, infinity and excess magnitude
    # without first converting an arbitrary integer or extended real to f64.
    if not cast("_ComparableMagnitude", abs(original)) <= _F32_MAX:
        _fail(name, "original value must be finite and within float32 magnitude")
    if positive and original <= 0:
        _fail(name, "requires a positive original value")
    return _real(float(original), name, positive=positive)


def _array_kind(value: Any, dtype: Any, name: str) -> NDArray[Any]:
    if type(value) is not np.ndarray or value.dtype != np.dtype(dtype) or not value.dtype.isnative:
        _fail(name, f"requires an ordinary native {np.dtype(dtype).name} ndarray")
    return value


def _provenance(value: Any) -> None:
    if type(value) is not tuple:
        _fail("provenance", "requires an exact tuple")
    _extent((max(len(value), 1), 2), np.dtype(np.intp).itemsize)
    seen: set[str] = set()
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2:
            _fail("provenance", "entries must be exact two-element tuples")
        key, text = pair
        if type(key) is not str or not key or type(text) is not str:
            _fail(
                "provenance",
                "requires nonempty ordinary string keys and ordinary string values",
            )
        if key in seen:
            _fail("provenance", "keys must be unique")
        seen.add(key)


def _validate_declaration(
    quadratures: Any,
    noise: Any,
    input_shape: Any,
    input_scale: Any,
    dxy_um: Any,
    dz_um: Any,
    lateral_zoom: Any,
    axial_zoom: Any,
    mapping_revision: Any,
    precision_profile: Any,
    provenance: Any,
    *,
    consumer: bool,
) -> _Grid:
    q = _array_kind(quadratures, np.complex64, "quadratures")
    if q.ndim != 6:
        _fail("quadratures", "requires six axes")
    v = _array_kind(noise, np.float64, "noise_variance_factors")
    if type(input_shape) is not tuple or len(input_shape) != 6:
        _fail("input_shape", "requires an exact six-element tuple")
    shape = tuple(_builtin_integer(n, "input_shape dimension") for n in input_shape)
    t, d, p, z, y, x = shape
    if z < 2 or x < 2 or x % 2:
        _fail("input_shape", "requires Z>=2 and even X>=2")
    slots = q.shape[2]
    orders = (slots + 1) // 2
    if not 1 <= slots <= _INT_MAX or slots % 2 != 1 or slots > p or orders < 2:
        _fail("quadratures", "requires odd Q<=P and at least two orders")
    if q.shape != (t, d, slots, z, y, x // 2 + 1):
        _fail("quadratures shape", "disagrees with input_shape")
    if v.shape != (t, d, orders):
        _fail("noise_variance_factors shape", "requires exactly (T,D,O)")
    if consumer:
        if type(input_scale) is not float:
            _fail("input_scale", "requires an exact Python float")
        _real(input_scale, "input_scale", positive=True)
        # Agreement is an input_scale obligation before later scalar fields.
        # Read zoom metadata only where it already has its canonical integer
        # domain; invalid later zoom declarations are diagnosed in field order.
        if (
            type(lateral_zoom) is int
            and 1 <= lateral_zoom <= _INT_MAX
            and type(axial_zoom) is int
            and 1 <= axial_zoom <= _INT_MAX
        ):
            expected = 1 / (x * y * z * lateral_zoom**2 * axial_zoom * d)
            if input_scale != expected:
                _fail("input_scale", "disagrees with CE04 normalization")
        if type(dxy_um) is not float:
            _fail("dxy_um", "requires an exact Python float")
    dxy = _scalar(dxy_um, "dxy_um", positive=True)
    if consumer and type(dz_um) is not float:
        _fail("dz_um", "requires an exact Python float")
    dz = _scalar(dz_um, "dz_um", positive=True)
    lateral = _builtin_integer(lateral_zoom, "lateral_zoom")
    axial = _builtin_integer(axial_zoom, "axial_zoom")
    if int(np.float32(lateral)) != lateral:
        _fail("lateral_zoom", "requires exact float32 integer representation")
    if type(mapping_revision) is not str or mapping_revision != _MAPPING:
        _fail("mapping_revision", f"requires {_MAPPING}")
    if type(precision_profile) is not str or precision_profile != _PROFILE:
        _fail("precision_profile", f"requires {_PROFILE}")
    _provenance(provenance)
    oz, oy, ox = axial * z, lateral * y, lateral * x
    for name, count in (
        ("native volume", x * y * z),
        ("native half volume", (x // 2 + 1) * y * z),
        ("direction/order count D*O", d * orders),
        ("quadrature/phase count Q*P", slots * p),
        ("output X", ox),
        ("output Y", oy),
        ("output Z", oz),
        ("output plane", ox * oy),
        ("output volume", ox * oy * oz),
    ):
        if not 1 <= count <= _INT_MAX:
            _fail("geometry", f"{name} exceeds positive signed32 representation")
    # Actual widths dominate the five historical byte-only expressions. No
    # preparation-only padded-camera/frame/solve storage is used or constrained.
    for target, itemsize in (
        (q.shape, 8),
        (v.shape, 8),
        ((d, 2), 8),
        ((d, orders - 1), 16),
        ((d, orders), 16),
        ((z, y, x), 8),
        ((oz, oy, ox), 8),
        ((t, oz, oy, ox), 8),
        ((t, oz, oy, ox), 4),
        ((ox,), 8),
        ((oy,), 8),
        ((oz,), 8),
        ((orders,), 8),
        ((_BLOCK,), 16),
    ):
        _extent(target, itemsize)
    scale = _real(1 / (x * y * z * lateral**2 * axial * d), "input_scale", positive=True)
    if consumer:
        for array, name in ((q, "quadratures"), (v, "noise_variance_factors")):
            if not array.flags.owndata or array.flags.writeable or not array.flags.c_contiguous:
                _fail(name, "requires owned read-only C-contiguous storage")
    _finite(q, "quadratures")
    _finite(v, "noise_variance_factors")
    for block in _blocks(v):
        if (block <= 0).any():
            _fail("noise_variance_factors", "requires strictly positive values")
    return _Grid(shape, orders, lateral, axial, dxy, dz, scale)


def declare_prepared_bands32(
    quadratures: Any,
    noise_variance_factors: Any,
    *,
    input_shape: _Shape,
    dxy_um: float,
    dz_um: float,
    lateral_zoom: int,
    axial_zoom: int,
    mapping_revision: str = _MAPPING,
    provenance: tuple[tuple[str, str], ...] = (),
) -> PreparedBands32:
    """Snapshot independently declared complex64 half spectra without preparation.

    Parameters
    ----------
    quadratures : numpy.ndarray
        Native complex64, axes (T,D,Q,Z,Y,X//2+1), slots 0,E1,O1,... .
    noise_variance_factors : numpy.ndarray
        Native float64 positive per-time noise, axes (T,D,O).
    input_shape : tuple of int
        Exact Python dimensions (T,D,P,Z,Y,X), with Z>=2 and even X>=2.
    dxy_um, dz_um : float
        Positive detector spacings in micrometres.
    lateral_zoom, axial_zoom : int
        Positive exact Python integer enlargement factors.
    mapping_revision : str, optional
        Exactly ce04-svn307-v1.
    provenance : tuple of (str, str), optional
        Ordered unique caller declarations; not authenticated acquisition history.

    Returns
    -------
    PreparedBands32
        Independent owned C-contiguous read-only snapshots and canonical metadata.

    Raises
    ------
    ReconstructionError
        For invalid declarations or an allocation failure, retaining its cause.
    """
    with _operation("declaration"):
        grid = _validate_declaration(
            quadratures,
            noise_variance_factors,
            input_shape,
            None,
            dxy_um,
            dz_um,
            lateral_zoom,
            axial_zoom,
            mapping_revision,
            _PROFILE,
            provenance,
            consumer=False,
        )
        q = np.array(quadratures, dtype=np.complex64, order="C", copy=True, subok=False)
        noise = np.array(
            noise_variance_factors, dtype=np.float64, order="C", copy=True, subok=False
        )
        q.setflags(write=False)
        noise.setflags(write=False)
        return PreparedBands32(
            q,
            noise,
            cast(_Shape, grid.shape),
            grid.scale,
            grid.dxy,
            grid.dz,
            lateral_zoom,
            axial_zoom,
            mapping_revision,
            _PROFILE,
            provenance,
        )


def _boolean(value: Any, name: str) -> bool:
    if type(value) not in (bool, np.bool_):
        _fail(name, "requires an actual boolean")
    return bool(value)


def _parameter(value: Any, name: str, shape: tuple[int, ...], *, complex_ok: bool) -> Any:
    if not isinstance(value, np.ndarray) or value.shape != shape:
        _fail(name, f"requires a NumPy array of shape {shape}")
    dtype = value.dtype
    if not (
        (dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        or (dtype.kind == "f" and dtype.itemsize in (2, 4, 8))
        or (complex_ok and dtype.kind == "c" and dtype.itemsize in (8, 16))
    ):
        _fail(
            name,
            "requires a standard real/complex dtype"
            if complex_ok
            else "requires a standard real dtype",
        )
    _extent(shape, 16 if complex_ok else 8)
    original = np.asarray(value)
    _finite(original, name)
    bound = np.float64(_F32_MAX)
    for block in _blocks(original):
        # The original dtype gate above admits only these numeric scalar kinds;
        # iteration without a requested dtype preserves them, including byte order.
        block = cast("_ParameterArray", block)
        # Compare original components before conversion; comparisons avoid signed
        # integer abs overflow and preserve the declared standard dtype domain.
        for component in (block.real, block.imag) if complex_ok else (block,):
            if (component > bound).any() or (component < -bound).any():
                _fail(name, "original components exceed float32 magnitude")
    return np.array(
        original, dtype=np.complex128 if complex_ok else np.float64, order="C", copy=True
    )


def _round32(value: Any, stage: str) -> np.float32:
    result = np.float32(value)
    _real(float(result), stage)
    return result


def _c32(real: Any, imaginary: Any, stage: str) -> np.complex64:
    r, i = _round32(real, stage), _round32(imaginary, stage)
    return np.complex64(complex(float(r), float(i)))


def _harmonic(even: np.complex64, odd: np.complex64, stage: str) -> np.complex64:
    # Rotate O by i with component sign/swap, then round each addition to f32.
    real = _round32(even.real - odd.imag, stage)
    imaginary = _round32(even.imag + odd.real, stage)
    return _c32(real, imaginary, stage)


def _product32(left: np.complex64, right: np.complex64, stage: str) -> np.complex64:
    rr = _round32(left.real * right.real, stage)
    ii = _round32(left.imag * right.imag, stage)
    ri = _round32(left.real * right.imag, stage)
    ir = _round32(left.imag * right.real, stage)
    return _c32(_round32(rr - ii, stage), _round32(ri + ir, stage), stage)


def _recombine32(p: np.complex64, n: np.complex64) -> tuple[np.complex64, np.complex64]:
    stage = "native recombination"
    total_r = _round32(p.real + n.real, stage)
    total_i = _round32(p.imag + n.imag, stage)
    delta_r = _round32(p.real - n.real, stage)
    delta_i = _round32(p.imag - n.imag, stage)
    half = np.float32(0.5)
    return (
        _c32(total_r * half, total_i * half, stage),
        _c32(delta_i * half, -delta_r * half, stage),
    )


def _product64(left: complex, right: complex, stage: str) -> complex:
    rr = _real(left.real * right.real, stage)
    ii = _real(left.imag * right.imag, stage)
    ri = _real(left.real * right.imag, stage)
    ir = _real(left.imag * right.real, stage)
    return complex(_real(rr - ii, stage), _real(ri + ir, stage))


def _sample_i32(value: int) -> int:
    if not -(2**31) <= value <= _INT_MAX:
        raise OtfError("source sampling integer exceeds signed32 representation")
    return value


def _sample_floor(value: float) -> int:
    if not isfinite(value):
        raise OtfError("nonfinite source sampling coordinate")
    return _sample_i32(floor(value))


def _sample_cell(table: _Transfer, order: int, offset: int) -> complex:
    """Read a checked C-logical flat address from the original table, without copying."""
    _sample_i32(offset)
    shape = table.samples.shape
    if table.layout == "radial":
        _, radial, axial = shape
        if not 0 <= offset < radial * axial:
            raise OtfError("source flat access leaves the order allocation")
        r, z = divmod(offset, axial)
        return complex(table.samples[order, r, z])
    _, axial, height, width = shape
    if not 0 <= offset < axial * height * width:
        raise OtfError("source flat access leaves the order allocation")
    z, remainder = divmod(offset, height * width)
    y, x = divmod(remainder, width)
    return complex(table.samples[order, z, y, x])


def _sample_value(table: _Transfer, order: int, x: float, y: float, z: int, dzf: float) -> complex:
    """Evaluate the literal CE03 stencil using bounded scalar original-table reads."""
    if not isfinite(dzf) or not 0 < dzf <= _F32_MAX:
        raise OtfError("dkz_cyc_um is outside its finite physical representation")
    ratio = dzf / table.dkz_cyc_um
    if not isfinite(ratio) or ratio == 0:
        raise OtfError("unresolved axial frequency ratio")
    t = _sample_i32(z) * ratio
    if table.layout == "radial":
        k = table.samples.shape[2]
        u = hypot(x, y) / table.dkr_cyc_um
        if t < 0:
            t += k  # One wrap only, including when the result stays negative.
        i, j = _sample_floor(u), _sample_floor(t)
        a, c = u - i, t - j
        j1 = 0 if j == k - 1 else _sample_i32(j + 1)
        lower = _sample_i32(i * k)
        upper = _sample_i32(_sample_i32(i + 1) * k)
        offsets = tuple(_sample_i32(base + axial) for base in (lower, upper) for axial in (j, j1))
        # Every actual vertex is required even when its weight is zero.
        v00, v01, v10, v11 = (_sample_cell(table, order, index) for index in offsets)
        return (1 - a) * ((1 - c) * v00 + c * v01) + a * ((1 - c) * v10 + c * v11)
    k, height, width = table.samples.shape[1:]
    u, v = x / table.dkr_cyc_um, y / table.dkr_cyc_um
    reflected = u < 0
    if reflected:
        u, v, t = -u, -v, -t
    if v < 0:
        v += height
    if t < 0:
        t += k
    i, j, axial = _sample_floor(u), _sample_floor(v), _sample_floor(t)
    a, b, c = u - i, v - j, t - axial
    i1 = _sample_i32(i + 1)

    def remainder(value: int, divisor: int) -> int:
        return value % divisor if value >= 0 else -((-value) % divisor)

    j1 = remainder(_sample_i32(j + 1), height)
    l1 = remainder(_sample_i32(axial + 1), k)
    plane = _sample_i32(width * height)
    vertices: list[complex] = []
    for lz in (axial, l1):
        zbase = _sample_i32(lz * plane)
        for row in (j, j1):
            base = _sample_i32(zbase + _sample_i32(row * width))
            for column in (i, i1):
                vertices.append(_sample_cell(table, order, _sample_i32(base + column)))
    weights = ((1 - b) * (1 - a), (1 - b) * a, b * (1 - a), b * a)
    value = (1 - c) * sum(w * cell for w, cell in zip(weights, vertices[:4], strict=True))
    value += c * sum(w * cell for w, cell in zip(weights, vertices[4:], strict=True))
    return value.conjugate() if reflected else value


def _sample(table: _Transfer, order: int, x: float, y: float, z: int, dzf: float) -> complex:
    try:
        value = _sample_value(table, order, x, y, z, dzf)
        if not isfinite(value.real) or not isfinite(value.imag):
            raise OtfError("nonfinite interpolation result")
        return value
    except OtfError as error:
        raise ReconstructionError(f"{_PROFILE} transfer stencil sampling: {error}") from error
    except Exception as error:
        # Keep sampler-domain/operation failures as the CE03 cause category.
        cause = OtfError(f"transfer stencil operation failed: {error}")
        cause.__cause__ = error
        raise ReconstructionError(f"{_PROFILE} transfer stencil sampling: {cause}") from cause


@dataclass(frozen=True)
class _SingleFilter:
    table: _Transfer
    carriers: _F64
    amplitudes: _C128
    inverse_noise: _F64
    dx: float
    dy: float
    dzf: float
    radius: float
    cuts: tuple[int, ...]
    taper_radius: float
    suppression_radius: float
    square: float
    suppress: bool
    dampen: bool
    omit: bool
    omit_kz0: bool
    cosine: bool
    time: int = 0

    def weight(self, direction: int, order: int, radius: float, z: int) -> float:
        value = float(self.inverse_noise[self.time, direction, order])
        stage = "native damping weight"
        if (
            self.suppress
            and radius <= self.suppression_radius
            and (order != 0 or (not self.dampen and not self.omit))
        ):
            r2 = _real(radius * radius, stage)
            divisor = _real(r2 + 0.2, stage, positive=True)
            divisor = _real(1 + _real(1000 / divisor, stage), stage, positive=True)
            value = _real(value * _real(1 / divisor, stage), stage)
        elif order == 0 and self.dampen:
            if self.cuts[0] == 0:
                _fail(stage, "dampen_order0 evaluates division by zero axial cutoff")
            lateral = _real(radius / self.radius, stage)
            lateral = _real(lateral**2, stage)
            axial = _real(abs(z / self.cuts[0]) ** 3, stage)
            value = _real(value * _real(lateral + axial, stage), stage)
        elif order == 0 and self.omit:
            value = 0.0
        # Check the evaluated branch before a later omission can hide overflow.
        _real(value, stage)
        if order == 0 and z == 0 and self.omit_kz0:
            value = 0.0
        return value

    def power(self, h: complex, amplitude: complex, weight: float) -> float:
        stage = "native filter power"
        h_abs = _real(abs(h), stage)
        a_abs = _real(abs(amplitude), stage)
        h2 = _real(h_abs * h_abs, stage)
        a2 = _real(a_abs * a_abs, stage)
        return _real(_real(h2 * a2, stage) * weight, stage)

    def scale(self, direction: int, order: int, x: float, y: float, z: int) -> np.complex64:
        stage = "scalar filter scale float64"
        # Sample self before its weight, including when a multiplier is zero.
        h = _sample(self.table, order, x, y, z, self.dzf)
        g = self.weight(direction, order, _real(hypot(x, y), stage), z)
        amplitude = complex(self.amplitudes[direction, order])
        denominator = self.power(h, amplitude, g)
        object_x = _real(x + _real(order * float(self.carriers[direction, 0]), stage), stage)
        object_y = _real(y + _real(order * float(self.carriers[direction, 1]), stage), stage)
        orders = self.amplitudes.shape[1]
        for other in range(self.carriers.shape[0]):
            for signed in range(1 - orders, orders):
                if (other, signed) == (direction, order):
                    continue
                qx = _real(object_x - _real(signed * float(self.carriers[other, 0]), stage), stage)
                qy = _real(object_y - _real(signed * float(self.carriers[other, 1]), stage), stage)
                radius = _real(hypot(qx, qy), "overlap frequency")
                if radius < self.radius:
                    m = abs(signed)
                    other_h = _sample(self.table, m, qx, qy, z, self.dzf)
                    other_g = self.weight(other, m, radius, z)
                    term = self.power(other_h, complex(self.amplitudes[other, m]), other_g)
                    denominator = _real(denominator + term, "ordered filter denominator")
        denominator = _real(denominator + self.square, "filter denominator", positive=True)
        # Componentwise numerator and real division, then taper, then conj(a).
        numerator_r = _real(g * h.real, stage)
        numerator_i = _real(g * -h.imag, stage)
        scale = complex(
            _real(numerator_r / denominator, stage),
            _real(numerator_i / denominator, stage),
        )
        if self.cosine:
            rho = _real(
                _real(hypot(object_x, object_y), "taper radius") / self.taper_radius,
                "taper radius",
            )
            if self.cuts[1] > 0:
                rho = _real(hypot(rho, abs(z) / self.cuts[1]), "taper radius")
            taper = _real(cos((float(np.pi) / 2) * min(rho, 1.0)), "taper cosine")
            scale = complex(_real(scale.real * taper, stage), _real(scale.imag * taper, stage))
        if order:
            scale = _product64(scale, amplitude.conjugate(), stage)
        _complex(scale, stage)
        with _operation("consumed scale conversion complex64"):
            return _c32(scale.real, scale.imag, "consumed scale conversion")


def _filter(original: _C64, grid: _Grid, settings: _SingleFilter) -> _C64:
    filtered = np.array(original, dtype=np.complex64, order="C", copy=True)
    tcount, directions, _, zsize, ysize, _ = original.shape
    xsize = grid.shape[-1]
    ys = range(1 - ysize // 2, ysize // 2 + 1)
    xs = range(1 - xsize // 2, xsize // 2 + 1)
    with _operation("native coefficient filtering/recombination"):
        for t in range(tcount):
            filtering = replace(settings, time=t)
            for d in range(directions):
                for m, cutoff in enumerate(filtering.cuts):
                    slots = (0,) if m == 0 else (2 * m - 1, 2 * m)
                    plus = np.zeros((zsize, ysize, xsize), dtype=np.complex64) if m else None
                    for y in ys:
                        for x in xs:
                            if m == 0 and x < 0:
                                continue
                            reflected = x < 0
                            row, column = (-y % ysize, -x) if reflected else (y % ysize, x)
                            fx, fy = x * filtering.dx, y * filtering.dy
                            radius = _real(hypot(fx, fy), "native frequency")
                            if radius <= filtering.radius:
                                for z in range(-cutoff, cutoff + 1):
                                    scale = filtering.scale(d, m, fx, fy, z)
                                    axial = (-z if reflected else z) % zsize
                                    even = original[t, d, slots[0], axial, row, column]
                                    if reflected:
                                        even = even.conjugate()
                                    if m == 0:
                                        filtered[t, d, 0, axial, row, column] = _product32(
                                            even, scale, "native coefficient product"
                                        )
                                    else:
                                        odd = original[t, d, 2 * m, axial, row, column]
                                        if reflected:
                                            odd = odd.conjugate()
                                        value = _harmonic(even, odd, "native coefficient harmonic")
                                        assert plus is not None
                                        plus[z % zsize, y % ysize, x % xsize] = _product32(
                                            value, scale, "native coefficient product"
                                        )
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
                                    even, odd = _recombine32(p, n)
                                    filtered[t, d, 2 * m - 1, z % zsize, y % ysize, x] = even
                                    filtered[t, d, 2 * m, z % zsize, y % ysize, x] = odd
                        del plus
        _finite(filtered, "filtered quadratures")
    return filtered


def _ramp(x_um: _F64, y_um: float, kx: float, ky: float, order: int) -> _C64:
    """Evaluate one bounded complete f64/c128 ramp and consume it once in c64."""
    _extent(x_um.shape, 8)
    _extent(x_um.shape, 16)
    if x_um.size > _BLOCK:
        _fail("phase", "internal block exceeds bounded scratch extent")
    phase = kx * x_um
    _finite(phase, "phase x product")
    lateral_y = _real(ky * y_um, "phase y product")
    np.add(phase, lateral_y, out=phase)
    _finite(phase, "phase coordinate sum")
    factor = _real(_real(2 * float(np.pi), "phase factor") * order, "phase factor")
    np.multiply(phase, factor, out=phase)
    _finite(phase, "phase argument")
    unit = np.empty(phase.shape, dtype=np.complex128)
    unit.real = 0.0
    unit.imag = phase
    del phase
    np.exp(unit, out=unit)
    _finite(unit, "phase unit ramp")
    result = np.array(unit, dtype=np.complex64, order="C", copy=True)
    del unit
    _finite(result, "consumed phase conversion")
    return result


def _bulk_product32(left: _C64, right: _C64) -> _C64:
    """Separate binary32 products and sums, with no complex promotion or FMA."""
    stage = "side complex64 product"
    rr = np.multiply(left.real, right.real, dtype=np.float32)
    _finite(rr, stage)
    ii = np.multiply(left.imag, right.imag, dtype=np.float32)
    _finite(ii, stage)
    np.subtract(rr, ii, out=rr)
    _finite(rr, stage)
    del ii
    ri = np.multiply(left.real, right.imag, dtype=np.float32)
    _finite(ri, stage)
    ir = np.multiply(left.imag, right.real, dtype=np.float32)
    _finite(ir, stage)
    np.add(ri, ir, out=ri)
    _finite(ri, stage)
    del ir
    result = np.empty(left.shape, dtype=np.complex64)
    result.real, result.imag = rr, ri
    return result


def _assemble(
    filtered: _C64, grid: _Grid, carriers: _F64, omit: bool, x_um: _F64, y_um: _F64
) -> _F32:
    tcount, directions, _, zsize, ysize, _ = filtered.shape
    xsize = grid.shape[-1]
    oz, oy, ox = grid.output_shape
    image = np.zeros((tcount, oz, oy, ox), dtype=np.float64)
    for t in range(tcount):
        for d in range(directions):
            for m in range(int(omit), grid.orders):
                with _operation("embedding native complex64 harmonic"):
                    padded = np.zeros(grid.output_shape, dtype=np.complex64)
                    for k in range(zsize):
                        z = signed_fourier_index(k, zsize)
                        for i in range(ysize):
                            y = signed_fourier_index(i, ysize)
                            for j in range(xsize):
                                x = signed_fourier_index(j, xsize)
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
                                    value = _harmonic(even, odd, "embedded native harmonic")
                                padded[z % oz, y % oy, x % ox] = value
                    _finite(padded, "embedded complex64 coefficients")
                with _operation("FFT inverse transform"):
                    spatial = scipy.fft.ifftn(
                        padded,
                        axes=(0, 1, 2),
                        norm="forward",
                        workers=1,
                        overwrite_x=False,
                    )
                    del padded
                    if (
                        type(spatial) is not np.ndarray
                        or spatial.dtype != np.complex64
                        or spatial.shape != grid.output_shape
                    ):
                        _fail(
                            "FFT",
                            "requires actual complex64 inverse output with the declared shape",
                        )
                    _finite(spatial, "FFT inverse output")
                    spatial = cast(_C64, spatial)
                with _operation("phase/product/float64 accumulation"):
                    for y in range(oy):
                        for start in range(0, ox, _BLOCK):
                            stop = min(start + _BLOCK, ox)
                            ramp = (
                                None
                                if m == 0
                                else _ramp(
                                    x_um[start:stop],
                                    float(y_um[y]),
                                    float(carriers[d, 0]),
                                    float(carriers[d, 1]),
                                    m,
                                )
                            )
                            for z in range(oz):
                                samples = spatial[z, y, start:stop]
                                if ramp is None:
                                    contribution = samples.real.astype(np.float64)
                                else:
                                    product = _bulk_product32(samples, ramp)
                                    contribution = product.real.astype(np.float64)
                                    del product
                                    np.multiply(contribution, 2.0, out=contribution)
                                _finite(contribution, "signed contribution float64")
                                target = image[t, z, y, start:stop]
                                np.add(target, contribution, out=target)
                                _finite(target, "image accumulator float64")
                                del contribution
                            del ramp
                del spatial
    with _operation("final image float32 conversion"):
        result = np.array(image, dtype=np.float32, order="C", copy=True)
        _finite(result, "final image float32")
    return result


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _identity(domain: str, metadata: Any, arrays: tuple[tuple[str, NDArray[Any], str], ...]) -> str:
    """Hash framed canonical metadata and bounded little-endian C-order bytes."""
    digest = sha256()

    def header(length: int) -> None:
        if not 0 <= length <= _INTP_MAX:
            _fail("identity", "frame exceeds native byte extent")
        digest.update(length.to_bytes(8, "little"))

    def frame(payload: bytes) -> None:
        header(len(payload))
        digest.update(payload)

    frame(("sp113-framed-v1/" + domain).encode("ascii"))
    frame(_canonical(metadata))
    _extent((max(len(arrays), 1), 3), np.dtype(np.intp).itemsize)
    for name, array, dtype in arrays:
        _extent(array.shape, np.dtype(dtype).itemsize)
        frame(_canonical([name, dtype, array.shape]))
        header(array.size * np.dtype(dtype).itemsize)
        for block in _blocks(array, dtype):
            digest.update(block.tobytes(order="C"))
    return digest.hexdigest()


def _precision_provenance(
    bands: PreparedBands32,
    table: _Transfer,
    carriers: _F64,
    modulation: _C128,
    settings: tuple[tuple[str, Any], ...],
) -> tuple[tuple[str, str], ...]:
    band_metadata = {
        "input_shape": bands.input_shape,
        "input_scale": bands.input_scale,
        "dxy_um": bands.dxy_um,
        "dz_um": bands.dz_um,
        "lateral_zoom": bands.lateral_zoom,
        "axial_zoom": bands.axial_zoom,
        "mapping_revision": bands.mapping_revision,
        "precision_profile": bands.precision_profile,
        "provenance": bands.provenance,
    }
    transfer_metadata = {
        "layout": table.layout,
        "dkr_cyc_um": table.dkr_cyc_um,
        "dkz_cyc_um": table.dkz_cyc_um,
        "norders": table.norders,
        "source_revision": "SVN307",
        "reference_sha256": _OTF_REFERENCE,
    }
    bands_identity = _identity(
        "bands",
        band_metadata,
        (
            ("quadratures", bands.quadratures, "<c8"),
            ("noise_variance_factors", bands.noise_variance_factors, "<f8"),
        ),
    )
    transfer_identity = _identity(
        "transfer", transfer_metadata, (("samples", table.samples, "<c16"),)
    )
    parameters_identity = _identity(
        "parameters",
        {"resolved_settings": settings, "precision": _PROFILE},
        (("carriers_cyc_um", carriers, "<f8"), ("modulation", modulation, "<c16")),
    )
    return (
        ("requested_profile", _PROFILE),
        ("resolved_profile", _PROFILE),
        ("mapping_revision", _MAPPING),
        ("band_storage_dtype", "complex64"),
        ("noise_dtype", "float64"),
        ("parameter_dtypes", "float64/complex128"),
        ("transfer_source_dtype", "complex128"),
        ("transfer_query_dtype", "float64/int64"),
        ("transfer_interpolation_dtype", "complex128"),
        ("scalar_filter_dtypes", "float64/complex128"),
        ("consumed_scale_dtype", "complex64"),
        ("local_bulk_dtype", "complex64"),
        ("fft_input_dtype", "complex64"),
        ("fft_output_dtype", "complex64"),
        ("fft_interface", "scipy.fft.ifftn"),
        ("fft_axes", "0,1,2"),
        ("fft_norm", "forward"),
        ("fft_workers", "1"),
        # The public dispatch interface does not expose an independently
        # attributable active backend/version, internal precision or workspace.
        ("fft_backend", "unknown"),
        ("fft_backend_version", "unknown"),
        ("scipy_version", str(scipy.__version__)),
        ("numpy_version", str(np.__version__)),
        ("fft_internal_precision", "unknown"),
        ("fft_workspace", "unknown"),
        ("phase_query_dtype", "float64"),
        ("consumed_phase_dtype", "complex64"),
        ("accumulation_dtype", "float64"),
        ("image_dtype", "float32"),
        ("transfer_rounding", "sample-c128;scalar-c128/f64;scale-once-c64"),
        ("input_identity_encoding", "sp113-framed-v1"),
        ("bands_sha256", bands_identity),
        ("transfer_sha256", transfer_identity),
        ("parameters_sha256", parameters_identity),
    )


def _readonly(array: Any) -> Any:
    array.setflags(write=False)
    return array


def _reconstruct_single(
    bands: PreparedBands32,
    transfer: OpticalTransfer,
    *,
    carriers_cyc_um: Any,
    modulation: Any,
    wavelength_nm: int,
    numerical_aperture: float,
    immersion_index: float,
    wiener: float,
    suppress_singularities: bool,
    suppression_radius_bins: float,
    dampen_order0: bool,
    omit_order0: bool,
    omit_kz0: bool,
    output_taper: str,
    wiener_increment: float,
    power_taper_exponent: float | None,
    precise_taper: bool,
    filter_overlaps: bool,
    explode_factor: float,
) -> KnownReconstruction32:
    """Apply the ordered new-profile validation and complete arithmetic path."""
    with _operation("bands validation"):
        grid = _validate_declaration(
            bands.quadratures,
            bands.noise_variance_factors,
            bands.input_shape,
            bands.input_scale,
            bands.dxy_um,
            bands.dz_um,
            bands.lateral_zoom,
            bands.axial_zoom,
            bands.mapping_revision,
            bands.precision_profile,
            bands.provenance,
            consumer=True,
        )
    with _operation("transfer validation"):
        try:
            table = validate_optical_transfer(transfer, require_actual=True)
        except OtfError as error:
            raise ReconstructionError(f"{_PROFILE} transfer validation: {error}") from error
        if table.norders < grid.orders:
            _fail("transfer", "insufficient orders")
    with _operation("scalar declarations"):
        wavelength = _integer(wavelength_nm, "wavelength_nm")
        if wavelength > 32767:
            _fail("wavelength_nm", "exceeds signed-short representation")
        na = _scalar(numerical_aperture, "numerical_aperture", positive=True)
        immersion = _scalar(immersion_index, "immersion_index", positive=True)
        if not 1 <= immersion <= 2:
            _fail("immersion_index", "requires [1,2]")
        if na > min(2, immersion):
            _fail("numerical_aperture", "exceeds the physical optics domain")
        w = _scalar(wiener, "wiener", positive=True)
        suppress = _boolean(suppress_singularities, "suppress_singularities")
        sr_bins = _scalar(suppression_radius_bins, "suppression_radius_bins")
        dampen = _boolean(dampen_order0, "dampen_order0")
        omit = _boolean(omit_order0, "omit_order0")
        omit_z = _boolean(omit_kz0, "omit_kz0")
        if not isinstance(output_taper, str):
            _fail("output_taper", "requires cosine or none")
        taper = str.__str__(output_taper)
        if taper not in ("cosine", "none"):
            _fail("output_taper", "only cosine and none are supported")
        increment = _scalar(wiener_increment, "wiener_increment")
        if increment != 0:
            _fail("wiener_increment", "only numeric zero is supported")
        if power_taper_exponent is not None:
            _fail("power_taper_exponent", "only None is supported")
        if _boolean(precise_taper, "precise_taper"):
            _fail("precise_taper", "only False is supported")
        if not _boolean(filter_overlaps, "filter_overlaps"):
            _fail("filter_overlaps", "only True is supported")
        explode = _scalar(explode_factor, "explode_factor")
        if explode != 1:
            _fail("explode_factor", "only numeric one is supported")
    with _operation("parameter validation/conversion"):
        carriers = _parameter(
            carriers_cyc_um, "carriers_cyc_um", (grid.shape[1], 2), complex_ok=False
        )
        mods = _parameter(
            modulation, "modulation", (grid.shape[1], grid.orders - 1), complex_ok=True
        )
    with _operation("derived support/sampling/noise/coordinates"):
        dzf = _real(1 / (grid.shape[3] * grid.dz), "dz sampling frequency", positive=True)
        dx = _real(1 / (grid.shape[-1] * grid.dxy), "dxy sampling frequency", positive=True)
        dy = _real(1 / (grid.shape[-2] * grid.dxy), "dxy sampling frequency", positive=True)
        radius, cuts = calculate_native_support(grid, carriers, wavelength, na, immersion, dzf)
        inverse_noise = np.reciprocal(bands.noise_variance_factors)
        _finite(inverse_noise, "reciprocal noise")
        square = _real(w * w, "wiener square", positive=True)
        taper_radius = _real(
            radius + hypot(float(carriers[0, 0]), float(carriers[0, 1])) * (grid.orders - 1),
            "taper radius",
            positive=True,
        )
        suppression_radius = _real(sr_bins * min(dx, dy), "suppression radius")
        oz, oy, ox = grid.output_shape
        x_um = (np.arange(ox, dtype=np.float64) - ox // 2) * (grid.dxy / grid.lateral)
        y_um = (np.arange(oy, dtype=np.float64) - oy // 2) * (grid.dxy / grid.lateral)
        z_um = (np.arange(oz, dtype=np.float64) - oz // 2) * (grid.dz / grid.axial)
        for vector in (x_um, y_um, z_um):
            _finite(vector, "physical coordinates")
    with _operation("snapshot/filter/assembly/result"):
        amplitudes = np.ones((grid.shape[1], grid.orders), dtype=np.complex128)
        amplitudes[:, 1:] = mods
        settings = (
            ("wavelength_nm", wavelength),
            ("numerical_aperture", na),
            ("immersion_index", immersion),
            ("wiener", w),
            ("suppress_singularities", suppress),
            ("suppression_radius_bins", sr_bins),
            ("dampen_order0", dampen),
            ("omit_order0", omit),
            ("omit_kz0", omit_z),
            ("output_taper", taper),
            ("dxy_um", grid.dxy),
            ("dz_um", grid.dz),
            ("lateral_zoom", bands.lateral_zoom),
            ("axial_zoom", grid.axial),
            ("input_scale", grid.scale),
        )
        provenance = _precision_provenance(bands, table, carriers, mods, settings)
        original = np.array(bands.quadratures, dtype=np.complex64, order="C", copy=True)
        filtering = _SingleFilter(
            table,
            carriers,
            amplitudes,
            inverse_noise,
            dx,
            dy,
            dzf,
            radius,
            cuts,
            taper_radius,
            suppression_radius,
            square,
            suppress,
            dampen,
            omit,
            omit_z,
            taper == "cosine",
        )
        filtered = _filter(original, grid, filtering)
        del original, filtering, inverse_noise, amplitudes
        image = _assemble(filtered, grid, carriers, omit, x_um, y_um)
        cutoffs = np.array(cuts, dtype=np.int64)
        return KnownReconstruction32(
            _readonly(image),
            _readonly(filtered),
            _readonly(x_um),
            _readonly(y_um),
            _readonly(z_um),
            _readonly(carriers),
            _readonly(mods),
            float(radius),
            _readonly(cutoffs),
            settings,
            precision_provenance=provenance,
        )
