"""Empirical SVN307 bead transfers and literal complex table sampling.

The implementation evaluates the selected source mathematics in binary64.
It provides no file adapter or compiled-source equivalence claim.
The supported API is the documented package-root exports; other module helpers
remain implementation details. For array axes and Fourier conventions see
docs/architecture/reconstruction-walkthrough.md#axes-units-and-fourier-conventions.
"""

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial, wraps
from math import asin, atan, ceil, cos, floor, hypot, isfinite, pi, sin
from numbers import Integral, Real
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.fft import rfftn

_F64 = NDArray[np.float64]
_C128 = NDArray[np.complex128]
_I32_MIN = -(2**31)
_I32_MAX = 2**31 - 1
_INTP_MAX = int(np.iinfo(np.intp).max)
_F32_MAX = float(np.finfo(np.float32).max)
_REFERENCE = (
    ("mainfile.c", "b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/sfftw.h",
        "72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138",
    ),
    (
        "usr_local/include/srfftw.h",
        "d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a",
    ),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)


class OtfError(ValueError):
    """Invalid transfer input or undefined selected empirical operation."""


@dataclass(frozen=True)
class OpticalTransfer:
    """Owned complex orders with explicit frequency increments and provenance.

    Attributes
    ----------
    samples : numpy.ndarray
        Read-only complex128 storage: (order, radius, z) for radial layout,
        or (order, z, y, x-half) for full layout. Axial/y bins are unshifted;
        full x stores the nonnegative half. The last axis varies fastest.
    layout : {'radial', 'full'}
        Interpretation of the table axes, with each order supplied explicitly.
    dkr_cyc_um, dkz_cyc_um : float
        Positive lateral and axial increments in cycles per micrometre.
    norders : int
        Number of complete orders, including order zero.
    source_revision : str
        Selected source revision, SVN307.
    reference_sha256 : tuple of (str, str)
        Source filenames and their pinned hashes.

    Notes
    -----
    Producers copy their inputs. Frozen fields alone do not validate a manually
    constructed record; consumers check its storage, metadata and provenance.
    Empirical complex128 values need not be complex64-exact like declarations.
    See docs/architecture/reconstruction-walkthrough.md#axes-units-and-fourier-conventions.
    """

    samples: _C128
    layout: str
    dkr_cyc_um: float
    dkz_cyc_um: float
    norders: int
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = _REFERENCE


@dataclass(frozen=True)
class _CheckedTransfer:
    """Private sampling data borrowing the validated complex128 storage."""

    samples: _C128
    layout: str
    dkr_cyc_um: float
    dkz_cyc_um: float
    norders: int


_Transfer = OpticalTransfer | _CheckedTransfer


@dataclass(frozen=True)
class PreparedOtf:
    """Combined radial transfer and the retained empirical diagnostics.

    Attributes
    ----------
    transfer : OpticalTransfer
        Combined (order, radius, z) tables after optional final conjugation.
    center_pixels_xyz : numpy.ndarray
        Float64 (3,) center in x, y, z detector pixels.
    background_counts : numpy.ndarray
        Float64 (z, phase) offsets selected before edge treatment.
    phase_angles_rad : numpy.ndarray
        Float64 (phase,) uniform phases in radians.
    quadratures : numpy.ndarray
        Complex128 (phase-slot, radius, z) tables in 0,C1,S1,... order, after
        repairs, masking, origin fitting and scaling, before combination.
    normalization_factors : numpy.ndarray
        Float64 (phase-slot,) inverse maxima applied to the quadratures.
    quadrature_angles_rad : numpy.ndarray
        Float64 (order-minus-zero,) combination angles in radians.
    resolved_settings : tuple of (str, object)
        Resolved scalar, flag and bin options, including background policy.

    Notes
    -----
    Preparation returns independently owned, read-only arrays. Radius has
    X//2+1 bins and the transfer has (P+1)//2 orders for P input phases.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """

    transfer: OpticalTransfer
    center_pixels_xyz: _F64
    background_counts: _F64
    phase_angles_rad: _F64
    quadratures: _C128
    normalization_factors: _F64
    quadrature_angles_rad: _F64
    resolved_settings: tuple[tuple[str, Any], ...]


def _operation[F: Callable[..., Any]](function: F) -> F:
    """Translate operation failures, retaining cause and the wrapped name label."""

    @wraps(function)
    def checked(*args: Any, **kwargs: Any) -> Any:
        try:
            with np.errstate(over="raise", divide="raise", invalid="raise"):
                return function(*args, **kwargs)
        except OtfError:
            raise
        except Exception as exc:
            raise OtfError(f"{function.__name__} failed: {exc}") from exc

    return cast(F, checked)


def _i32(value: int, name: str = "source integer intermediate") -> int:
    """Check one actually evaluated signed32 source integer without truncation."""
    if not _I32_MIN <= value <= _I32_MAX:
        raise OtfError(f"{name} exceeds signed32 representation")
    return value


def _integer(value: Any, name: str, minimum: int = 0, *, require_actual: bool = False) -> int:
    """Resolve a nonboolean integral setting within signed32 and its lower bound."""
    valid = (
        not issubclass(type(value), (bool, np.bool_)) and issubclass(type(value), Integral)
        if require_actual
        else not isinstance(value, (bool, np.bool_)) and isinstance(value, Integral)
    )
    if not valid:
        raise OtfError(f"{name} must be an integer")
    result = _i32(int(value), name)
    if result < minimum:
        raise OtfError(f"{name} must be at least {minimum}")
    return result


def _scalar(
    value: Any,
    name: str,
    *,
    positive: bool = False,
    require_actual: bool = False,
    widen_signed_magnitude: bool = False,
) -> float:
    """Resolve a finite real setting within float32 magnitude, optionally positive."""
    valid = (
        not issubclass(type(value), (bool, np.bool_)) and issubclass(type(value), Real)
        if require_actual
        else not isinstance(value, (bool, np.bool_)) and isinstance(value, Real)
    )
    if not valid:
        raise OtfError(f"{name} must be a finite real scalar")
    magnitude_input = value
    if require_actual and issubclass(type(value), np.generic):
        scalar_value = cast("np.generic[Any]", value)
        if scalar_value.dtype.char == "e" or (
            widen_signed_magnitude and scalar_value.dtype.kind == "i"
        ):
            # Compare half values and signed magnitudes without input-width overflow.
            magnitude_input = np.generic.item(scalar_value)
    magnitude: Any = abs(magnitude_input)
    if magnitude > _F32_MAX:
        raise OtfError(f"{name} exceeds float32 magnitude")
    result = float(value)
    if not isfinite(result) or (positive and result <= 0):
        raise OtfError(f"{name} is outside its finite physical representation")
    if require_actual and abs(result) > _F32_MAX:
        raise OtfError(f"{name} exceeds float32 magnitude")
    return result


def _extent(shape: tuple[int, ...], itemsize: int) -> None:
    """Check native target shape/stride extent, including nominally empty arrays."""
    extent = itemsize
    for dimension in shape:
        if not 0 <= dimension <= _INTP_MAX:
            raise OtfError("array dimension exceeds native representation")
        extent *= max(dimension, 1)
        if extent > _INTP_MAX:
            raise OtfError("owned array shape/strides exceed native representation")


def _finite(array: NDArray[Any], name: str) -> None:
    """Reject unresolved arithmetic without changing the borrowed array."""
    if not np.isfinite(array).all():
        raise OtfError(f"{name} contains nonfinite or unresolved arithmetic")


def _numeric(value: Any, name: str, *, complex_ok: bool = False) -> NDArray[Any]:
    """Resolve numeric array input; boolean, object and string dtypes reject."""
    array = np.asarray(value)
    if array.dtype.kind not in ("iufc" if complex_ok else "iuf"):
        raise OtfError(f"{name} must contain real{' or complex' if complex_ok else ''} numbers")
    return array


def _values(
    array: NDArray[Any],
    name: str,
    *,
    exact: bool,
    complex_ok: bool = False,
    wide_bound: bool = False,
) -> None:
    """Check source-float magnitude and optional exact float32/complex64 values."""
    _finite(array, name)
    bound = np.float64(_F32_MAX) if wide_bound else _F32_MAX
    if complex_ok:
        if (np.abs(np.real(array)) > bound).any() or (np.abs(np.imag(array)) > bound).any():
            raise OtfError(f"{name} exceeds complex64 magnitude")
        if exact:
            _exact_values(array, np.complex64, name)
    else:
        if (array > bound).any() or (array < -bound).any():
            raise OtfError(f"{name} exceeds float32 magnitude")
        if exact:
            _exact_values(array, np.float32, name)


def _exact_values(array: NDArray[Any], dtype: Any, name: str) -> None:
    """Require an exact source-dtype round trip, retaining exact integer comparisons."""
    rounded = array.astype(dtype)
    if array.dtype.kind in "iu":
        # NumPy's mixed integer/float equality can itself round a large integer.
        # Python integers preserve its exact value on both sides of this check.
        differs = any(int(a) != int(b.real) for a, b in zip(array.flat, rounded.flat, strict=True))
    else:
        differs = not np.equal(array, rounded).all()
    if differs:
        raise OtfError(f"{name} must be exactly representable as {np.dtype(dtype).name}")


def _owned(value: Any, dtype: Any) -> NDArray[Any]:
    """Copy finite values to independently owned, C-order, read-only target storage."""
    shape = np.shape(value)
    _extent(shape, np.dtype(dtype).itemsize)
    result = np.array(value, dtype=dtype, copy=True, order="C")
    _finite(result, "output")
    result.setflags(write=False)
    return result


def _table_shape(
    array: NDArray[Any], layout: Any, *, describe_layout_mismatch: bool = False
) -> None:
    """Check nonempty layout axes, signed32 per-order counts and native target extent."""
    if not isinstance(layout, str) or layout not in ("radial", "full"):
        raise OtfError("unsupported transfer layout; use radial or full")
    expected_ndim = 3 if layout == "radial" else 4
    if array.ndim != expected_ndim or any(d < 1 for d in array.shape):
        if describe_layout_mismatch and array.ndim != expected_ndim:
            raise OtfError(
                f"{layout} transfer layout requires {expected_ndim} axes, got {array.ndim}"
            )
        raise OtfError("complete transfer requires nonempty order and table axes")
    for dimension in array.shape:
        _i32(dimension, "transfer dimension")
    if layout == "radial":
        _i32(array.shape[1] * array.shape[2], "per-order radial count")
    else:
        _, k, y, x = array.shape
        _i32(_i32(k * x) * y, "per-order full count")
        _i32(x * y, "full plane count")
    _extent(array.shape, 16)


@_operation
def declare_otf(
    samples: Any, *, layout: str, dkr_cyc_um: float, dkz_cyc_um: float
) -> OpticalTransfer:
    """Declare complete radial or full complex orders without normalization.

    Parameters
    ----------
    samples : array_like
        Complete (order, radius, z) or (order, z, y, x-half) tables, exactly
        representable as complex64. Values are copied into complex128 storage.
    layout : {'radial', 'full'}
        Explicit table layout.
    dkr_cyc_um, dkz_cyc_um : float
        Positive lateral and axial increments in cycles per micrometre.

    Returns
    -------
    OpticalTransfer
        An owned, read-only declaration of the supplied complete orders.

    Raises
    ------
    OtfError
        If input, source counts or native allocation representation is invalid,
        or copying fails.

    Notes
    -----
    Declaration changes no value, normalization, symmetry or order count.
    Finite zeros and asymmetric complex values are permitted. Each dimension
    and per-order source count must fit signed32; complex128 native allocation
    shape/stride extent must fit intp before copying. A computed empirical
    transfer is consumed directly rather than redeclared through this stricter
    complex64-exact input boundary. Caller storage is never mutated.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    array = _numeric(samples, "samples", complex_ok=True)
    _table_shape(array, layout)
    dkr = _scalar(dkr_cyc_um, "dkr_cyc_um", positive=True)
    dkz = _scalar(dkz_cyc_um, "dkz_cyc_um", positive=True)
    _values(array, "samples", exact=True, complex_ok=True)
    return OpticalTransfer(_owned(array, np.complex128), layout, dkr, dkz, array.shape[0])


def _matches_transfer_reference(reference: Any) -> bool:
    """Match actual immutable source-name/hash tuples rather than advertised equality."""
    if not issubclass(type(reference), tuple) or tuple.__len__(reference) != len(_REFERENCE):
        return False
    for pair, expected in zip(tuple.__iter__(reference), _REFERENCE, strict=True):
        if not issubclass(type(pair), tuple) or tuple.__len__(pair) != 2:
            return False
        if any(
            not issubclass(type(value), str) or str.__str__(value) != text
            for value, text in zip(tuple.__iter__(pair), expected, strict=True)
        ):
            return False
    return True


def validate_optical_transfer(transfer: Any, *, require_actual: bool = False) -> _Transfer:
    """Validate a transfer record without copying or quantizing its samples.

    Parameters
    ----------
    transfer : OpticalTransfer
        Complete finite, owned, read-only complex128 tables and source metadata.
        Unlike declaration input, computed samples need not be complex64-exact.
    require_actual : bool, optional
        Use actual Python/NumPy types and base descriptors when validating
        acquisition/workflow inputs rather than trusting advertised attributes.

    Returns
    -------
    OpticalTransfer or _CheckedTransfer
        The original record, or checked metadata borrowing the same sample
        storage. Neither path changes the caller's arrays or normalizes values.

    Raises
    ------
    OtfError
        If layout, finite values, ownership, counts, increments or provenance
        violate the accepted record domain.

    Notes
    -----
    This shared implementation helper does not add a supported package export.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    transfer_type_valid = (
        issubclass(type(transfer), OpticalTransfer)
        if require_actual
        else isinstance(transfer, OpticalTransfer)
    )
    if not transfer_type_valid:
        raise OtfError("transfer must be an OpticalTransfer record")
    array = transfer.samples
    array_type_valid = (
        issubclass(type(array), np.ndarray) if require_actual else isinstance(array, np.ndarray)
    )
    if not array_type_valid:
        raise OtfError("transfer samples must be an owned complex128 array")
    layout = transfer.layout
    if require_actual:
        if not issubclass(type(layout), str):
            raise OtfError("unsupported transfer layout; use radial or full")
        layout = str.__str__(layout)
    samples = np.asarray(array) if require_actual else array
    _table_shape(samples, layout, describe_layout_mismatch=require_actual)
    flags = np.ndarray.flags.__get__(array) if require_actual else array.flags
    if samples.dtype != np.complex128 or flags.writeable or not flags.owndata:
        raise OtfError("transfer samples must be owned, read-only complex128")
    _finite(samples, "transfer samples")
    dkr = _scalar(transfer.dkr_cyc_um, "transfer dkr", positive=True, require_actual=require_actual)
    dkz = _scalar(transfer.dkz_cyc_um, "transfer dkz", positive=True, require_actual=require_actual)
    norders = _integer(transfer.norders, "norders", 1, require_actual=require_actual)
    if norders != samples.shape[0]:
        raise OtfError("transfer norders disagrees with samples")
    revision = transfer.source_revision
    if require_actual:
        if not issubclass(type(revision), str) or str.__str__(revision) != "SVN307":
            raise OtfError("invalid transfer source identity: source_revision")
        if not _matches_transfer_reference(transfer.reference_sha256):
            raise OtfError("invalid transfer source identity: reference_sha256")
        return _CheckedTransfer(samples, layout, dkr, dkz, norders)
    if revision != "SVN307":
        raise OtfError("invalid transfer source identity")
    reference = transfer.reference_sha256
    if reference != _REFERENCE:
        raise OtfError("invalid transfer source identity")
    return transfer


def _floor32(value: float) -> int:
    """Floor a finite table coordinate into the signed32 source-index domain."""
    if not isfinite(value):
        raise OtfError("nonfinite source index")
    return _i32(floor(value), "floor index")


def _remainder(value: int, divisor: int) -> int:
    """Use C signed remainder, leaving a negative dividend's remainder nonpositive."""
    return value % divisor if value >= 0 else -((-value) % divisor)


def _address(value: int, count: int) -> int:
    """Validate an actual flat address, allowing safe aliases across conceptual axes."""
    _i32(value)
    if not 0 <= value < count:
        raise OtfError("source flat access leaves the order allocation")
    return value


def interpolate_radial_stencil(flat: _C128, k: int, u: float, t: float) -> complex:
    """Read one literal bilinear radial/axial stencil from a borrowed order.

    Parameters
    ----------
    flat : numpy.ndarray
        Borrowed complex128 order flattened from (radius, z), axial fastest.
    k : int
        Positive table axial length.
    u, t : float
        Radius and axial coordinates in table-bin units, not cycles/um.

    Returns
    -------
    complex
        Bilinear complex value; input storage is unchanged.

    Notes
    -----
    Negative t receives one addition of k. Only j==k-1 wraps its next vertex
    to zero. Actual signed32 flat addresses define the domain, including safe
    cross-row aliases; all four vertices must exist even at zero weight.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    if t < 0:
        t += k
    i, j = _floor32(u), _floor32(t)
    a, c = u - i, t - j
    j1 = 0 if j == k - 1 else _i32(j + 1)
    lower, upper = _i32(i * k), _i32(_i32(i + 1) * k)
    offsets = [_address(_i32(base + z), flat.size) for base in (lower, upper) for z in (j, j1)]
    v00, v01, v10, v11 = (complex(flat[index]) for index in offsets)
    return (1 - a) * ((1 - c) * v00 + c * v01) + a * ((1 - c) * v10 + c * v11)


def interpolate_full_stencil(
    flat: _C128, shape: tuple[int, ...], u: float, v: float, t: float
) -> complex:
    """Read one full-table trilinear stencil with half-space conjugation.

    Parameters
    ----------
    flat : numpy.ndarray
        Borrowed complex128 order, flattened from (z, y, x-half).
    shape : tuple of int
        Positive table lengths (z, y, x-half).
    u, v, t : float
        x, y and axial coordinates in table-bin units.

    Returns
    -------
    complex
        Trilinear complex value, conjugated when the original u was negative.
        Input storage is unchanged.

    Notes
    -----
    Negative x reflects all three coordinates; signed zero does not reflect.
    Negative y/z receive one period addition, then next-bin indices use C
    signed remainder. This preserves safe flat aliases rather than clipping
    each axis. Every vertex must fit signed32 and the selected allocation,
    including zero-weight vertices; outside support is not zero-filled.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    k, y, x = shape
    reflected = u < 0
    if reflected:
        u, v, t = -u, -v, -t
    if v < 0:
        v += y
    if t < 0:
        t += k
    i, j, axial = _floor32(u), _floor32(v), _floor32(t)
    a, b, c = u - i, v - j, t - axial
    i1 = _i32(i + 1)
    j1, l1 = _remainder(_i32(j + 1), y), _remainder(_i32(axial + 1), k)
    plane = _i32(x * y)
    vertices = []
    for z in (axial, l1):
        zbase = _i32(z * plane)
        for row in (j, j1):
            base = _i32(zbase + _i32(row * x))
            for column in (i, i1):
                vertices.append(complex(flat[_address(_i32(base + column), flat.size)]))
    weights = ((1 - b) * (1 - a), (1 - b) * a, b * (1 - a), b * a)
    value = (1 - c) * sum(w * cell for w, cell in zip(weights, vertices[:4], strict=True))
    value += c * sum(w * cell for w, cell in zip(weights, vertices[4:], strict=True))
    return value.conjugate() if reflected else value


@_operation
def sample_otf(
    transfer: OpticalTransfer,
    kx_cyc_um: Any,
    ky_cyc_um: Any,
    kz_index: Any,
    *,
    dkz_cyc_um: float,
    order: int = 0,
) -> _C128:
    """Sample complex transfer tables using every literal source vertex.

    Parameters
    ----------
    transfer : OpticalTransfer
        Complete declared or empirically prepared orders.
    kx_cyc_um, ky_cyc_um : array_like
        Finite real lateral frequencies in cycles per micrometre.
    kz_index : array_like of int
        Signed32 integral axial indices, broadcast with lateral coordinates.
    dkz_cyc_um : float
        Positive native axial frequency increment in cycles per micrometre.
    order : int, optional
        Selected complete order, starting at zero.

    Returns
    -------
    numpy.ndarray
        Owned complex128 values in the broadcast shape, including scalar and
        empty shapes. The result is writable; transfer and query inputs are
        borrowed unchanged.

    Raises
    ------
    OtfError
        If inputs or source intermediates are invalid, any vertex leaves the
        allocation (even at zero weight), or evaluation/allocation fails.

    Notes
    -----
    Axial table coordinates use kz_index*(native_dkz/table_dkz), allowing a
    different native grid. Negative full-table x reflects all coordinates
    and conjugates the result. Negative axial/y coordinates receive one
    period addition; safe flat aliases remain permitted. This is complex
    interpolation with literal vertices, without repeated wrapping, clipping
    or zero extension. Failure of one query rejects the entire call.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    return interpolate_transfer_queries(
        validate_optical_transfer(transfer), kx_cyc_um, ky_cyc_um, kz_index, dkz_cyc_um, order
    )


@_operation
def _sample_transfer(
    transfer: _Transfer,
    kx: Any,
    ky: Any,
    kz: Any,
    *,
    dkz_cyc_um: float,
    order: int,
) -> _C128:
    """Sample public or already-checked records for reconstruction consumers.

    Parameters
    ----------
    transfer : OpticalTransfer or _CheckedTransfer
        Validated record; checked records borrow their original sample storage.
    kx, ky : array_like
        Finite real lateral frequencies in cycles per micrometre.
    kz : array_like of int
        Nonboolean signed32 native axial indices, broadcast with kx and ky.
    dkz_cyc_um : float
        Positive native axial increment in cycles per micrometre.
    order : int
        Complete order to sample, starting at zero.

    Returns
    -------
    numpy.ndarray
        New owned complex128 values with the broadcast query shape. Inputs
        are borrowed unchanged; an unsafe vertex rejects the whole call.

    Notes
    -----
    Keep this decorated helper's name: _operation includes function.__name__
    in translated backend/allocation errors consumed by downstream wrappers.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    if type(transfer) is _CheckedTransfer:
        return interpolate_transfer_queries(transfer, kx, ky, kz, dkz_cyc_um, order)
    return sample_otf(
        cast(OpticalTransfer, transfer), kx, ky, kz, dkz_cyc_um=dkz_cyc_um, order=order
    )


def interpolate_transfer_queries(
    transfer: _Transfer,
    kx_cyc_um: Any,
    ky_cyc_um: Any,
    kz_index: Any,
    dkz_cyc_um: float,
    order: int,
) -> _C128:
    """Convert physical queries to table bins and sample a validated transfer.

    Parameters
    ----------
    transfer : OpticalTransfer or _CheckedTransfer
        Validated borrowed complex128 radial or full tables.
    kx_cyc_um, ky_cyc_um : array_like
        Finite real lateral frequencies in cycles per micrometre.
    kz_index : array_like of int
        Nonboolean signed32 axial indices in the native frequency grid.
    dkz_cyc_um : float
        Positive native axial increment, distinct from the transfer increment.
    order : int
        Complete order index, starting at zero.

    Returns
    -------
    numpy.ndarray
        New owned, writable complex128 array in the broadcast shape, including
        zero-dimensional and empty outputs. No caller storage is changed.

    Notes
    -----
    Axial coordinates use kz_index*(native_dkz/table_dkz). Radial queries use
    hypot(kx,ky)/dkr; full queries use (kx,ky)/dkr. There is no extrapolation
    or magnitude interpolation. Literal flat stencils govern admissibility;
    one failing query rejects the call rather than returning partial values.
    Native shape/stride extent is checked even when the output is empty.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    selected = _integer(order, "order")
    if selected >= transfer.norders:
        raise OtfError("order is outside the complete table")
    native_dkz = _scalar(dkz_cyc_um, "dkz_cyc_um", positive=True)
    x, y = _numeric(kx_cyc_um, "kx"), _numeric(ky_cyc_um, "ky")
    z = np.asarray(kz_index)
    if z.dtype.kind not in "iu":
        raise OtfError("kz_index must contain nonboolean integral indices")
    for array in (x, y, z):
        _finite(array, "query")
    if (z < _I32_MIN).any() or (z > _I32_MAX).any():
        raise OtfError("kz_index exceeds signed32")
    shape = np.broadcast_shapes(x.shape, y.shape, z.shape)
    scale = native_dkz / transfer.dkz_cyc_um
    if not isfinite(scale) or scale == 0:
        raise OtfError("unresolved axial frequency ratio")
    _extent(shape, 16)
    result = np.empty(shape, dtype=np.complex128)
    if result.size == 0:
        return result
    x, y, z = np.broadcast_arrays(x, y, z)
    flat = transfer.samples[selected].reshape(-1)
    for index in np.ndindex(shape):
        fx, fy = float(x[index]), float(y[index])
        t = int(z[index]) * scale
        if transfer.layout == "radial":
            value = interpolate_radial_stencil(
                flat, transfer.samples.shape[2], hypot(fx, fy) / transfer.dkr_cyc_um, t
            )
        else:
            value = interpolate_full_stencil(
                flat,
                transfer.samples.shape[1:],
                fx / transfer.dkr_cyc_um,
                fy / transfer.dkr_cyc_um,
                t,
            )
        if not isfinite(value.real) or not isfinite(value.imag):
            raise OtfError("nonfinite interpolation result")
        result[index] = value
    return result


def _bins(value: Any, name: str, length: int, *, require_actual: bool = False) -> tuple[int, ...]:
    """Resolve a fixed-length sequence of nonnegative signed32 integer bounds."""
    if isinstance(value, (str, bytes)):
        raise OtfError(f"{name} must be an integer sequence")
    items = tuple(value)
    if len(items) != length:
        raise OtfError(f"{name} requires {length} integers")
    return tuple(_integer(item, name, require_actual=require_actual) for item in items)


def _map(value: Any, name: str, shape: tuple[int, ...], *, wide_bound: bool = False) -> _F64 | None:
    """Copy an optional finite real correction map to writable float64 storage."""
    if value is None:
        return None
    array = _numeric(value, name)
    if array.shape != shape:
        raise OtfError(f"{name} must have shape {shape}")
    _extent(shape, 8)
    _values(array, name, exact=False, wide_bound=wide_bound)
    return np.array(array, dtype=np.float64, copy=True)


def apodize_bead_edges_inplace(plane: _F64) -> None:
    """Apply the fixed ten-pixel additive bead edge operation in place.

    Parameters
    ----------
    plane : numpy.ndarray
        Writable float64 (y, x) detector-count plane from owned bead storage.
        Validated geometry has even X>=8 and 10<=Y<=X+2.

    Notes
    -----
    Vertical updates precede horizontal updates in initialized (Y,X+2)
    padding. Horizontal subtraction uses Y-1-offset, including padding
    columns; it is not the specimen edge helper's X-based operation. Opposite
    strips can overlap, so writes remain sequential. Only detector columns
    are copied back; padding is not an additional Fourier input.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    y, x = plane.shape
    # The empirical caller uses a padded row and Y in its horizontal
    # subtraction address. Retain padding writes and their sequential order.
    padded = np.zeros((y, x + 2), dtype=np.float64)
    padded[:, :x] = plane
    difference = (padded[-1, :x] - padded[0, :x]) / 2
    for offset in range(10):
        change = difference * (1 - sin((offset + 0.5) * pi / 20))
        padded[offset, :x] += change
        padded[y - 1 - offset, :x] -= change
    for row in range(y):
        difference_x = (padded[row, x - 1] - padded[row, 0]) / 2
        for offset in range(10):
            change_x = difference_x * (1 - sin((offset + 0.5) * pi / 20))
            padded[row, offset] += change_x
            padded[row, y - 1 - offset] -= change_x
    plane[:] = padded[:, :x]


def locate_bead_center(images: _F64) -> _F64:
    """Locate the bead peak before subtraction of the selected backgrounds.

    Parameters
    ----------
    images : numpy.ndarray
        Borrowed float64 (phase, z, y, x) edge-treated detector counts.

    Returns
    -------
    numpy.ndarray
        New float64 (3,) center in x, y, z detector pixels. Input is unchanged.

    Notes
    -----
    Average phases, select the first maximum with a zero initial maximum,
    then use periodic nearest neighbors for a local parabolic offset. An
    offset outside [-1.5,1.5] is discarded, without wrapping the final center.
    The unused source background diagnostic still requires finite arithmetic
    and valid padded addresses; it never supplies preparation backgrounds.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    mean = images.mean(axis=0)
    _finite(mean, "mean bead")
    location = np.unravel_index(int(np.argmax(mean)), mean.shape)
    maximum = float(mean[location])
    if maximum <= 0:
        location, maximum = (0, 0, 0), 0.0
    center = []
    for axis, length in enumerate(mean.shape):
        low, high = list(location), list(location)
        low[axis], high[axis] = (low[axis] - 1) % length, (high[axis] + 1) % length
        minus, plus = float(mean[tuple(low)]), float(mean[tuple(high)])
        slope = (plus - minus) / 2
        curvature = plus + minus - 2 * maximum
        offset = -slope / curvature if curvature != 0 else 0.0
        if not isfinite(offset):
            raise OtfError("unresolved peak parabola")
        center.append(float(location[axis]) + (offset if abs(offset) <= 1.5 else 0.0))
    zc, yc, _ = center
    if yc == 20:
        raise OtfError("singular unused center background diagnostic")
    # The source diagnostic reads the original padded phase allocation. Check
    # actual addresses, even though its result is unused by preparation.
    p, z, y, x = images.shape
    rows = max(0, ceil(yc - 20))
    padded_plane = _i32((x + 2) * y)
    if rows:
        first = _i32(_floor32(zc) * padded_plane)
        last = _i32(_i32(first + _i32((rows - 1) * (x + 2))) + x - 1)
        count = _i32(padded_plane * z)
        _address(first, count)
        _address(last, count)
        diagnostic = images[:, floor(zc), :rows, :].sum() / (p * (yc - 20) * x)
        if not np.isfinite(diagnostic):
            raise OtfError("nonfinite unused center background diagnostic")
    return np.array(center[::-1], dtype=np.float64)


def separate_bead_phase_quadratures(images: _F64) -> tuple[_F64, _F64]:
    """Separate uniform bead phases with the calibration's 1/P convention.

    Parameters
    ----------
    images : numpy.ndarray
        Borrowed float64 (phase, z, y, x) background-subtracted counts, with
        phase count P in {1,3,5,7,9}.

    Returns
    -------
    separated : numpy.ndarray
        New float64 (phase-slot, z, y, x) spatial quadratures in 0,C1,S1,...
        order. Each cosine/sine sum and the zero-order sum is divided by P.
    phases : numpy.ndarray
        New float64 (phase,) uniform phases 2*pi*p/P in radians.

    Notes
    -----
    Input is unchanged. Every pixel participates, including x Nyquist; the
    specimen separator has a different normalization and Nyquist rule.
    Analytic phase pairing retains exact constant/symmetric nulls without
    introducing an intensity threshold.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    p = images.shape[0]
    phases = 2 * pi * np.arange(p) / p
    separated = np.empty_like(images)
    separated[0] = images.mean(axis=0)
    for order in range(1, (p + 1) // 2):
        cosine_terms = [np.zeros_like(images[0]) for _ in range(p // 2 + 1)]
        sine_terms = [np.zeros_like(images[0]) for _ in range(p // 2 + 1)]
        # Pair uniform phases analytically. sum cos=0 and sin(-phi)=-sin(phi)
        # remove exact constant/symmetric nulls without an intensity threshold.
        for phase in range(1, (p + 1) // 2):
            residue = (order * phase) % p
            sign = 1 if residue <= p // 2 else -1
            residue = min(residue, p - residue)
            cosine_terms[residue] += (images[phase] - images[0]) + (images[p - phase] - images[0])
            sine_terms[residue] += sign * (images[phase] - images[p - phase])
        c, s = cosine_terms[0], np.zeros_like(images[0])
        if p == 9:
            # cos(8pi/9)=-cos(2pi/9)-cos(4pi/9), and
            # sin(8pi/9)=sin(4pi/9)-sin(2pi/9). Reduce these exact
            # dependencies before evaluation, including order-three aliases.
            c -= cosine_terms[3] / 2
            c += (cosine_terms[1] - cosine_terms[4]) * cos(2 * pi / 9)
            c += (cosine_terms[2] - cosine_terms[4]) * cos(4 * pi / 9)
            s += (sine_terms[1] - sine_terms[4]) * sin(2 * pi / 9)
            s += (sine_terms[2] + sine_terms[4]) * sin(4 * pi / 9)
            s += sine_terms[3] * sin(2 * pi / 3)
        else:
            for residue in range(1, p // 2 + 1):
                cosine = -0.5 if p == 3 else cos(2 * pi * residue / p)
                c += cosine_terms[residue] * cosine
                s += sine_terms[residue] * sin(2 * pi * residue / p)
        separated[2 * order - 1], separated[2 * order] = c / p, s / p
    return separated, phases


def signed_fourier_indices(length: int) -> _F64:
    """Return unshifted float64 bin indices, retaining positive even Nyquist.

    Parameters
    ----------
    length : int
        Positive Fourier-axis length.

    Returns
    -------
    numpy.ndarray
        New (length,) indices q(i)=i for i<=length//2, otherwise i-length.
        Values are bin indices, not physical frequencies.

    Notes
    -----
    See docs/architecture/reconstruction-walkthrough.md#axes-units-and-fourier-conventions.
    """
    indices = np.arange(length, dtype=np.float64)
    return np.where(indices <= length // 2, indices, indices - length)


def build_bead_radial_quadratures(
    spatial: _F64,
    center: _F64,
    dkr: float,
    dkz: float,
    diameter: float,
    spacing: float,
    angle: float,
    compensate: bool,
) -> _C128:
    """Transform, center, compensate and radially average bead quadratures.

    Parameters
    ----------
    spatial : numpy.ndarray
        Borrowed float64 (phase-slot, z, y, x) separated spatial counts.
    center : numpy.ndarray
        Float64 (3,) center in x, y, z detector pixels.
    dkr, dkz : float
        Positive increments in cycles/um. The bead convention uses
        dkr=1/(Y*dxy) on both lateral axes, even for rectangular images.
    diameter, spacing : float
        Bead diameter and illumination line spacing in micrometres.
    angle : float
        Calibration carrier orientation in radians.
    compensate : bool
        Divide by the order-shifted continuum sphere response; requires
        multiple phases and positive diameter, with finite nonzero divisors.

    Returns
    -------
    numpy.ndarray
        New writable complex128 (phase-slot, X//2+1, Z) radial quadratures.
        Input arrays are unchanged. Empty radial bins retain zero.

    Notes
    -----
    The forward transform is an unnormalized negative-exponential sum over
    true Z,Y,X; the positive ramp recenters all three axes before compensation.
    Sphere shifts use order/(maximum_order*spacing), not native radius alone.
    Average actual stored x-half cells by rounded integer radius, without
    full-plane weights. Then project axial conjugate pairs, making z=0 and
    even self-paired Nyquist real while retaining other imaginary odd parts.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    p, z, ny, nx = spatial.shape
    transformed = rfftn(spatial, axes=(1, 2, 3))
    x = np.arange(nx // 2 + 1, dtype=np.float64)[None, None, :]
    y = signed_fourier_indices(ny)[None, :, None]
    axial = signed_fourier_indices(z)[:, None, None]
    transformed *= np.exp(
        2j * pi * (x * center[0] / nx + y * center[1] / ny + axial * center[2] / z)
    )
    if compensate:
        for slot in range(p):
            order = (slot + 1) // 2
            shift = order / (((p - 1) // 2) * spacing)
            rho = np.hypot(
                np.hypot(x * dkr + shift * cos(angle), y * dkr + shift * sin(angle)), axial * dkz
            )
            u = pi * diameter * rho
            _finite(u, "sphere argument")
            sphere = np.ones_like(u)
            nonzero = u != 0
            # Evaluate the same analytic sphere with a convergent power series
            # near zero. This evaluation switch changes no support decision.
            small = (u <= 1) & nonzero
            square = u[small] ** 2
            term = np.ones_like(square)
            series = term.copy()
            for degree in range(1, 21):
                term *= -square / (2 * degree * (2 * degree + 3))
                series += term
            sphere[small] = series
            large = u > 1
            argument = u[large]
            sphere[large] = (
                3 * ((np.sin(argument) / argument - np.cos(argument)) / argument) / argument
            )
            _finite(sphere, "sphere divisor")
            if (sphere == 0).any():
                raise OtfError("zero or unresolved continuum sphere divisor")
            transformed[slot] /= sphere
    _finite(transformed, "centered bead transform")
    radius = np.rint(np.hypot(x[0], y[0])).astype(np.int64)
    radial = np.zeros((p, nx // 2 + 1, z), dtype=np.complex128)
    for r in range(nx // 2 + 1):
        selected = radius == r
        count = int(selected.sum())
        if count:
            radial[:, r] = transformed[:, :, selected].sum(axis=-1) / count
    radial[:, :, 0] = radial[:, :, 0].real
    for j in range(1, z // 2 + 1):
        value = (radial[:, :, j] + radial[:, :, z - j].conj()) / 2
        radial[:, :, j], radial[:, :, z - j] = value, value.conj()
    return radial


def mask_bead_support_inplace(
    radial: _C128,
    bins: tuple[int, ...],
    dkr: float,
    dkz: float,
    wavelength: int,
    na: float,
    immersion: float,
) -> None:
    """Apply literal radial/axial support-cleanup writes in place.

    Parameters
    ----------
    radial : numpy.ndarray
        Writable complex128 (phase-slot, radius, z) quadratures after repairs.
    bins : tuple of int
        Nonnegative source bounds (l11,l12,l2); l11=0 bypasses all cleanup.
    dkr, dkz : float
        Positive radial and axial increments in cycles per micrometre.
    wavelength : int
        Positive wavelength in nanometres, converted to micrometres here.
    na, immersion : float
        Positive numerical aperture and refractive index, with na<=immersion.

    Notes
    -----
    Side slots use 0.92*na, including orders above two. A strict radial cutoff
    zeros whole rows; the remaining axial bounds execute ascending flat writes.
    Safe cross-row writes can affect later rows and must retain their order.
    Actual out-of-allocation writes reject rather than clipping to each row.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    if bins[0] == 0:
        return
    p, rcount, z = radial.shape
    lam = wavelength * 0.001
    for slot in range(p):
        order = (slot + 1) // 2
        aperture = na if order == 0 else 0.92 * na
        alpha = asin(aperture / immersion)
        cutoff = 2 * aperture / lam
        flat = radial[slot].reshape(-1)

        def write(r: int, j: int, *, partner: bool = False, flat: _C128 = flat) -> None:
            base = _i32(r * z)
            # Preserve the actual left-associated source r*Z+Z-j expression.
            address = _i32(_i32(base + z) - j) if partner else _i32(base + j)
            flat[_address(address, flat.size)] = 0

        for r in range(rcount):
            kr = r * dkr
            if kr > cutoff:
                flat[r * z : (r + 1) * z] = 0
                continue
            beta = asin((aperture - kr * lam) / immersion)
            edge = (immersion / lam) * (cos(beta) - cos(alpha)) / dkz
            if not isfinite(edge):
                raise OtfError("unresolved support boundary")
            if order == 0:
                start = _i32(round(edge + 1))
                end = _i32(z - start)
                for j in range(start, end + 1):
                    write(r, j)
                if start <= end:
                    _i32(end + 1)
            else:
                h = _i32(round(edge + 0.999))
                if order == 1:
                    end = _i32(bins[0] - h)
                    for j in range(end + 1):
                        write(r, j)
                        if j > 0:
                            write(r, j, partner=True)
                    if end >= 0:
                        _i32(end + 1)
                    start = _i32(_i32(bins[1] + h) + 1)
                else:
                    start = _i32(bins[2] + h)
                for j in range(start, z // 2 + 1):
                    write(r, j)
                    write(r, j, partner=True)


def normalize_and_combine_bead_quadratures(
    radial: _C128,
    origin: tuple[int, ...] | None,
    each: bool,
    forced: bool,
    conjugate: bool,
) -> tuple[_C128, _F64, _F64]:
    """Fit the origin, scale quadratures in place and combine complex orders.

    Parameters
    ----------
    radial : numpy.ndarray
        Writable complex128 (phase-slot, radius, z) tables after support cleanup.
    origin : tuple of int or None
        Inclusive radial interval 1<=a<b<=X//2 for order-zero real-sum fitting.
    each : bool
        Normalize each slot by its own maximum modulus; otherwise reuse the
        order-zero inverse maximum on all slots, preserving relative amplitude.
    forced : bool
        Apply the selected first-order pi-angle adjustment.
    conjugate : bool
        Conjugate combined output orders, leaving scaled quadratures unchanged.

    Returns
    -------
    combined : numpy.ndarray
        New writable complex128 ((P+1)//2, radius, z) combined orders.
    factors : numpy.ndarray
        New float64 (P,) inverse maxima applied in place to radial.
    angles : numpy.ndarray
        New float64 ((P-1)//2,) magnitude/sign combination angles in radians.

    Notes
    -----
    Origin fitting precedes maximum-modulus scaling; angles use the scaled
    quadratures. Side output is C*cos(angle)-S*sin(angle), not C+i*S. The
    angle starts at atan(sum(abs(S))/sum(abs(C))), followed by the literal
    sign decisions and optional first-order shift. Zero cosine magnitude
    rejects; zero sign samples retain their specified unchanged-angle branch.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    p, _, _ = radial.shape
    if origin is not None:
        a, b = origin
        totals = radial[0].real.sum(axis=1)
        totals[0] = radial[0, 0, 0].real
        mu = (a + b) / 2
        positions = np.arange(a, b + 1) - mu
        mean = totals[a : b + 1].mean()
        slope = np.dot(positions, totals[a : b + 1]) / np.dot(positions, positions)
        for r in range(a):
            radial[0, r, 0] += -totals[r] + mean + (r - mu) * slope
    factors = np.empty(p, dtype=np.float64)
    for slot in range(p):
        if slot == 0 or each:
            maximum = float(np.max(np.abs(radial[slot])))
            if maximum == 0 or not isfinite(maximum):
                raise OtfError("zero or nonfinite empirical normalization maximum")
            factor = 1 / maximum
            if not isfinite(factor):
                raise OtfError("nonfinite inverse empirical normalization")
        else:
            factor = float(factors[0])
        factors[slot] = factor
        radial[slot] *= factor
    combined = np.empty(((p + 1) // 2, *radial.shape[1:]), dtype=np.complex128)
    combined[0] = radial[0]
    angles = np.empty((p - 1) // 2, dtype=np.float64)
    for order in range(1, (p + 1) // 2):
        c, s = radial[2 * order - 1], radial[2 * order]
        a, b = float(np.abs(c).sum()), float(np.abs(s).sum())
        if a == 0 or not isfinite(a) or not isfinite(b):
            raise OtfError("singular or nonfinite cosine quadrature magnitude sum")
        ratio = b / a
        if not isfinite(ratio):
            raise OtfError("unresolved quadrature magnitude ratio")
        angle = atan(ratio)
        cv, sv = (
            float(c[(radial.shape[1] - 1) // 4, 0].real),
            float(s[(radial.shape[1] - 1) // 4, 0].real),
        )
        if cv < 0 and sv > 0:
            angle += pi
        elif cv < 0 and sv < 0:
            angle = pi - angle
        elif cv > 0 and sv > 0:
            angle = -angle
        if order == 1 and forced:
            angle = pi - angle
        angles[order - 1] = angle
        combined[order] = c * cos(angle) - s * sin(angle)
    if conjugate:
        np.conjugate(combined, out=combined)
    _finite(radial, "scaled quadratures")
    _finite(combined, "combined transfer")
    return combined, factors, angles


@_operation
def prepare_bead_otf(
    raw: Any,
    *,
    dxy_um: float,
    dz_um: float,
    linespacing_um: float,
    wavelength_nm: int,
    bead_diameter_um: float = 0.12,
    carrier_angle_rad: float = 0.0,
    background_counts: float | None = None,
    background_map: Any = None,
    slope_map: Any = None,
    exposure_background_counts: Any = None,
    compensate_bead: bool = True,
    fix_axial_axis: bool = True,
    fix_radial_from: int = 0,
    cleanup_axial_bins: tuple[int, int, int] = (0, 0, 0),
    numerical_aperture: float = 1.4,
    immersion_index: float = 1.515,
    origin_fit_bins: tuple[int, int] | None = None,
    rescale_each: bool = False,
    forced_pi_shift: bool = False,
    conjugate: bool = False,
) -> PreparedOtf:
    """Prepare empirical radial transfers from explicitly ordered bead exposures.

    Parameters
    ----------
    raw : array_like
        Finite float32-exact real observations with axes (phase, z, y, x).
        Odd phase counts 1 through 9, Z>=1, even X>=8 and 10<=Y<=X+2 apply.
    dxy_um, dz_um : float
        Positive lateral and axial pixel pitches in micrometres.
    linespacing_um : float
        Positive illumination line spacing in micrometres.
    wavelength_nm : int
        Explicit positive wavelength in nanometres.
    bead_diameter_um : float, optional
        Continuum bead diameter in micrometres; positive for compensation.
    carrier_angle_rad : float, optional
        Carrier angle in radians.
    background_counts : float or None, optional
        Nonnegative scalar background, or automatic corner-region background.
    background_map, slope_map : array_like or None, optional
        Paired real camera maps of shape (y, x). Signed slopes are allowed.
    exposure_background_counts : array_like or None, optional
        Real (z, phase) backgrounds; take priority over camera maps and scalar.
    compensate_bead : bool, optional
        Divide both quadratures by the shifted continuum sphere transform.
        Single-phase preparation requires False.
    fix_axial_axis : bool, optional
        Repair radial zero from radial one, retaining order-zero DC.
    fix_radial_from : int, optional
        First radial bin for axial-zero repair; zero disables it.
    cleanup_axial_bins : tuple of int, optional
        Literal source support bounds (l11, l12, l2); l11=0 bypasses cleanup.
    numerical_aperture, immersion_index : float, optional
        Positive optical settings with aperture <= immersion index.
    origin_fit_bins : tuple of int or None, optional
        Inclusive radial interval for optional order-zero origin regression.
    rescale_each : bool, optional
        Scale each quadrature separately instead of sharing order zero's scale.
    forced_pi_shift : bool, optional
        Apply the selected first-order pi shift during combination.
    conjugate : bool, optional
        Conjugate final combined orders.

    Returns
    -------
    PreparedOtf
        Owned, read-only combined orders, quadratures and resolved diagnostics.

    Raises
    ------
    OtfError
        If validation, an actual source address or a numerical operation fails.
        Backend and allocation exceptions retain their original causes.

    Notes
    -----
    All supplied corrections validate even when superseded. Select backgrounds
    before fixed10 edge updates, locate the center before subtracting those
    backgrounds, then separate uniform phases with 1/P and transform with an
    unnormalized negative exponential. The centering ramp has positive signs
    on all axes. Optional shifted-sphere division precedes radial averaging
    and axial conjugate projection. Axis repairs, support cleanup, origin fit,
    maximum-modulus scaling and magnitude/sign combination follow in order.

    Table increments are dkr=1/(Y*dxy_um) and dkz=1/(Z*dz_um), including
    rectangular inputs. Counts and executed source addresses fit signed32;
    float64/complex128 target extents fit native intp. These geometry bounds
    alone do not guarantee safe diagnostics, repairs or later sample stencils.
    No caller storage is changed. Returned arrays are independent read-only
    copies; empirical values retain complex128 precision for direct consumers.
    See
    docs/architecture/reconstruction-walkthrough.md#optical-transfer-explicit-tables-or-bead-calibration.
    """
    array = _numeric(raw, "raw")
    if array.ndim != 4:
        raise OtfError("raw axes must be (phase,z,y,x)")
    p, z, n, x = array.shape
    added_geometry = z == 1 or n != x
    if added_geometry and not issubclass(type(raw), np.ndarray) and isinstance(raw, np.ndarray):
        raise OtfError("raw advertises a NumPy array without being one")
    if x % 2:
        raise OtfError("odd lateral storage is unsupported; require even size")
    if p not in (1, 3, 5, 7, 9):
        raise OtfError("unsupported phase count; require odd phases 1,3,5,7,9")
    if z < 1 or x < 8 or n < 10 or n > x + 2:
        raise OtfError("fixed10 padded bead edges require Z>=1, even X>=8, Y>=10, Y<=X+2")
    for dimension in array.shape:
        _i32(dimension, "bead dimension")
    _i32(_i32(_i32(x + 2) * n) * z, "per-phase padded real count")
    _i32(z * p, "background count")
    _i32((x // 2 + 1) * z, "radial order count")
    _extent(array.shape, 8)
    _extent((p, z, n, x // 2 + 1), 16)
    _extent((p, x // 2 + 1, z), 16)
    resolve_scalar = partial(
        _scalar, require_actual=added_geometry, widen_signed_magnitude=added_geometry
    )
    scalars = {
        "dxy_um": resolve_scalar(dxy_um, "dxy_um", positive=True),
        "dz_um": resolve_scalar(dz_um, "dz_um", positive=True),
        "linespacing_um": resolve_scalar(linespacing_um, "linespacing_um", positive=True),
        "bead_diameter_um": resolve_scalar(bead_diameter_um, "bead_diameter_um"),
        "carrier_angle_rad": resolve_scalar(carrier_angle_rad, "carrier_angle_rad"),
        "numerical_aperture": resolve_scalar(
            numerical_aperture, "numerical_aperture", positive=True
        ),
        "immersion_index": resolve_scalar(immersion_index, "immersion_index", positive=True),
    }
    if scalars["bead_diameter_um"] < 0:
        raise OtfError("bead diameter must be nonnegative")
    if scalars["numerical_aperture"] > scalars["immersion_index"]:
        raise OtfError("numerical aperture exceeds immersion index")
    wavelength = _integer(wavelength_nm, "wavelength_nm", 1, require_actual=added_geometry)
    background = (
        None
        if background_counts is None
        else resolve_scalar(background_counts, "background_counts")
    )
    if background is not None and background < 0:
        raise OtfError("background_counts must be nonnegative")
    flags = {
        "compensate_bead": compensate_bead,
        "fix_axial_axis": fix_axial_axis,
        "rescale_each": rescale_each,
        "forced_pi_shift": forced_pi_shift,
        "conjugate": conjugate,
    }
    for name, value in flags.items():
        valid = (
            issubclass(type(value), (bool, np.bool_))
            if added_geometry
            else isinstance(value, (bool, np.bool_))
        )
        if not valid:
            raise OtfError(f"{name} must be a boolean")
    if compensate_bead and (p == 1 or scalars["bead_diameter_um"] == 0):
        raise OtfError("single-phase or zero-diameter bead compensation is unsupported")
    start = _integer(fix_radial_from, "fix_radial_from", require_actual=added_geometry)
    bins = _bins(cleanup_axial_bins, "cleanup_axial_bins", 3, require_actual=added_geometry)
    origin = (
        None
        if origin_fit_bins is None
        else _bins(origin_fit_bins, "origin_fit_bins", 2, require_actual=added_geometry)
    )
    if origin is not None and not 1 <= origin[0] < origin[1] <= x // 2:
        raise OtfError("origin fit needs 1<=a<b<=N/2")
    camera = _map(background_map, "background_map", (n, x), wide_bound=added_geometry)
    slopes = _map(slope_map, "slope_map", (n, x), wide_bound=added_geometry)
    if (camera is None) != (slopes is None):
        raise OtfError("background and slope maps must be supplied together")
    exposures = _map(
        exposure_background_counts, "exposure_background_counts", (z, p), wide_bound=added_geometry
    )
    _values(array, "raw", exact=True, wide_bound=added_geometry)
    dkr = 1 / (n * scalars["dxy_um"])
    dkz = 1 / (z * scalars["dz_um"])
    _scalar(dkr, "derived transfer dkr", positive=True)
    _scalar(dkz, "derived transfer dkz", positive=True)
    images = np.array(array, dtype=np.float64, copy=True)
    backgrounds = np.empty((z, p), dtype=np.float64)
    policy = (
        "exposure"
        if exposures is not None
        else "maps"
        if camera is not None
        else "scalar"
        if background is not None
        else "auto"
    )
    border = (np.arange(n) < 20) | (np.arange(n) > n - 20)
    border_x = (np.arange(x) < 20) | (np.arange(x) > x - 20)
    for section in range(z):
        for phase in range(p):
            plane = images[phase, section]
            if plane[-1, -1] < 0:
                plane[-1, -1] = plane[-1, -2]
            if exposures is not None:
                b = exposures[section, phase]
            elif camera is not None and slopes is not None:
                plane -= camera
                plane *= slopes
                b = 0.0
            elif background is not None:
                b = background
            else:
                b = plane[np.ix_(border, border_x)].mean()
            backgrounds[section, phase] = b
            apodize_bead_edges_inplace(plane)
    # Center the edge-treated observations before subtracting the chosen offsets.
    center = locate_bead_center(images)
    images -= backgrounds.T[:, :, None, None]
    separated, phases = separate_bead_phase_quadratures(images)
    radial = build_bead_radial_quadratures(
        separated,
        center,
        dkr,
        dkz,
        scalars["bead_diameter_um"],
        scalars["linespacing_um"],
        scalars["carrier_angle_rad"],
        compensate_bead,
    )
    # Repair r=0 first, then axial zero; source-safe flat aliases stay literal.
    if fix_axial_axis:
        dc = radial[0, 0, 0]
        radial[:, 0] = radial[:, 1]
        radial[0, 0, 0] = dc
    if start:
        for slot in range(p):
            flat = radial[slot].reshape(-1)
            for r in range(start, x // 2 + 1):
                base = _i32(r * z)
                low = _address(_i32(base + 1), flat.size)
                high = _address(_i32(base + z - 1), flat.size)
                flat[base] = (flat[low] + flat[high]) / 2
    mask_bead_support_inplace(
        radial,
        bins,
        dkr,
        dkz,
        wavelength,
        scalars["numerical_aperture"],
        scalars["immersion_index"],
    )
    # Cleanup precedes origin fitting and normalization; these steps do not commute.
    combined, factors, angles = normalize_and_combine_bead_quadratures(
        radial, origin, rescale_each, forced_pi_shift, conjugate
    )
    resolved = dict(scalars) | {
        "wavelength_nm": wavelength,
        "background_counts": background,
        "fix_radial_from": start,
        "cleanup_axial_bins": bins,
        "origin_fit_bins": origin,
        **{name: bool(value) for name, value in flags.items()},
        "background_policy": policy,
    }
    transfer = OpticalTransfer(_owned(combined, np.complex128), "radial", dkr, dkz, (p + 1) // 2)
    return PreparedOtf(
        transfer,
        _owned(center, np.float64),
        _owned(backgrounds, np.float64),
        _owned(phases, np.float64),
        _owned(radial, np.complex128),
        _owned(factors, np.float64),
        _owned(angles, np.float64),
        tuple(resolved.items()),
    )
