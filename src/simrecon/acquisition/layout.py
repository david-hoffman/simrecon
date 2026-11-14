"""Acquisition value validation, diagnostic capture and literal 2D stream layout."""

from __future__ import annotations

import math
import struct
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ..models import SimreconError
from ..optical_transfer import _REFERENCE as _OTF_REFERENCE
from .preparation import _array_metadata, _raw_samples

# Private, context-local diagnostic policy. Public stage signatures and their
# default full capture remain unchanged; only the summary composition sets it.
_COMPACT_CAPTURE: ContextVar[bool] = ContextVar("simrecon_compact_capture", default=False)


@contextmanager
def _capture_policy(compact: bool) -> Iterator[None]:
    """Select private capture with exception-safe, reentrant token restoration."""
    token = _COMPACT_CAPTURE.set(compact)
    try:
        yield
    finally:
        _COMPACT_CAPTURE.reset(token)


def _scalar_tuple(value: Any) -> Any:
    """Freeze an event array without retaining its backing storage."""
    if isinstance(value, np.ndarray):
        return _scalar_tuple(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (tuple, list)):
        return tuple(_scalar_tuple(v) for v in value)
    return value


Array = NDArray[Any]
INT_MAX = 2**31 - 1
INTP_MAX = int(np.iinfo(np.intp).max)
F32_MAX = float(np.finfo(np.float32).max)
REFERENCE = (
    *_OTF_REFERENCE,
    ("drift_n_phasestep.c", "13d917fa4a59fd05c33bf307822d647ba4f408e52c4a664a210d1a4c396676d2"),
)


class AcquisitionModeError(SimreconError):
    """Invalid acquisition declaration or undefined selected source operation."""

    def __init__(self, message: str):
        super().__init__("acquisition-mode", message)


@contextmanager
def operation() -> Iterator[None]:
    """Retain causes of failed operations and let interruption propagate."""
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            yield
    except AcquisitionModeError:
        raise
    except Exception as error:
        raise AcquisitionModeError(
            f"acquisition operation failed ({type(error).__name__}): {error}"
        ) from error


def signed(value: int, name: str) -> int:
    """Check an actual signed32 source intermediate before its use."""
    if not -(2**31) <= value <= INT_MAX:
        raise AcquisitionModeError(f"{name} exceeds signed32 source representation")
    return value


def integer(value: Any, name: str, *, minimum: int = 1) -> int:
    """Resolve a nonboolean source integer declaration."""
    if issubclass(type(value), (bool, np.bool_)) or not issubclass(type(value), Integral):
        raise AcquisitionModeError(f"{name} must be an integer")
    result = signed(int(value), name)
    if result < minimum:
        raise AcquisitionModeError(f"{name} must be at least {minimum}")
    return result


def scalar(value: Any, name: str, *, positive: bool = False) -> float:
    """Resolve a finite source-float mathematical scalar without narrowing."""
    if issubclass(type(value), (bool, np.bool_)) or not issubclass(type(value), Real):
        raise AcquisitionModeError(f"{name} must be a finite real scalar")
    if issubclass(type(value), np.generic):
        value = value.item()
    magnitude: Any = abs(value)
    if magnitude > F32_MAX:
        raise AcquisitionModeError(f"{name} exceeds float32 magnitude")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise AcquisitionModeError(f"{name} must be finite" + (" and positive" if positive else ""))
    if abs(result) > F32_MAX:
        raise AcquisitionModeError(f"{name} exceeds float32 magnitude")
    return result


def finite(value: Any, name: str) -> None:
    """Reject nonfinite inputs or unresolved operation results."""
    if not np.isfinite(value).all():
        raise AcquisitionModeError(f"{name}: nonfinite or unresolved arithmetic")


def extent(shape: tuple[int, ...], itemsize: int) -> None:
    """Check native shape, stride and byte representation, including empty axes."""
    count = itemsize
    for n in reversed(shape):
        if not 0 <= n <= INTP_MAX:
            raise AcquisitionModeError("array dimension exceeds native intp representation")
        count *= max(n, 1)
        if count > INTP_MAX:
            raise AcquisitionModeError("array shape/stride/byte extent exceeds native intp")


def array_metadata(value: Any, name: str, shape: tuple[int, ...], *, raw: bool = False) -> Array:
    """Validate and return the plain array backing the supplied values."""
    extent(shape, 8)
    if not issubclass(type(value), np.ndarray):
        raise AcquisitionModeError(f"{name} must be a NumPy array")
    value = np.asarray(value)
    _array_metadata(value, name, shape)
    finite(value, name)
    if raw:
        try:
            _raw_samples(value, name)
        except SimreconError as error:
            if name != "off_exposures":
                raise
            raise AcquisitionModeError(
                "off_exposures samples must be exactly float32 representable"
            ) from error
    elif (value > np.float64(F32_MAX)).any() or (value < np.float64(-F32_MAX)).any():
        raise AcquisitionModeError(f"{name} exceeds float32 magnitude")
    return value


def real_array(value: Any, name: str, shape: tuple[int, ...]) -> Array:
    """Copy a validated real mathematical array as binary64."""
    checked = array_metadata(value, name, shape)
    return np.array(checked, dtype=np.float64, copy=True)


def owned(value: Array, *, writable: bool = False) -> Array:
    """Capture independent output storage with the selected mutability."""
    extent(value.shape, value.dtype.itemsize)
    finite(value, "result")
    result = np.array(value, copy=True)
    result.flags.writeable = writable
    return result


def _finish_owned(value: Array, *, writable: bool = False) -> Array:
    """Finish a private allocation after its last write, without a snapshot copy.

    Call only for independently allocated stage outputs. Event captures still
    use owned(), because their source workspaces can be changed later.
    """
    extent(value.shape, value.dtype.itemsize)
    finite(value, "result")
    value.flags.writeable = writable
    return value


def append(sequence: list[Any], value: Any) -> None:
    """Check the eventual immutable container's native pointer extent."""
    if sys.getsizeof(()) + (len(sequence) + 1) * struct.calcsize("P") > INTP_MAX:
        raise AcquisitionModeError("diagnostic container exceeds native intp representation")
    sequence.append(value)


@dataclass(frozen=True)
class ModeEvent:
    """Immutable operation event with independent read-only diagnostic arrays.

    Indices identify actual t/d/z/p traversal. Details preserve keyword insertion
    order; array snapshots cannot alias later mutable workspaces or each other.
    """

    kind: str
    time_index: int
    direction_index: int
    z_index: int | None
    phase_index: int | None
    details: tuple[tuple[str, Any], ...]


def event(
    trace: list[ModeEvent],
    kind: str,
    t: int,
    d: int,
    z: int | None = None,
    p: int | None = None,
    **details: Any,
) -> None:
    """Append a snapshot of an actually executed operation in detail-key order.

    Mutates trace only: ndarray details become independent read-only copies;
    NumPy scalar details become Python scalars. Indices retain the caller's
    actual time/direction/z/phase context, including failed later-stage routing.
    No diagnostic is synthesized for an unexecuted branch.
    """
    compact = _COMPACT_CAPTURE.get()
    omitted = {
        "between-build": ("centers", "fourier"),
        "drift-correlation": ("cross_spectrum", "correlation", "absolute_correlation"),
        "exposure-correction": ("phase_multiplier",),
        "between-correction": ("phase_multiplier",),
        "off-combination": ("quadratures_after",),
    }.get(kind, ())
    captured = []
    for key, value in details.items():
        if isinstance(value, np.ndarray):
            if compact:
                # owned() performs these checks even on captures we omit.
                extent(value.shape, value.dtype.itemsize)
                finite(value, "result")
                value = None if key in omitted else _scalar_tuple(value)
            else:
                value = owned(value)
        elif isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, (float, complex)):
            finite(value, f"{kind} {key}")
        if not compact or key not in omitted:
            captured.append((key, value))
    if compact and kind == "precise-query":
        indices = (t, d, z, p)
        if (
            trace
            and trace[-1].kind == "precise-query-count"
            and (
                trace[-1].time_index,
                trace[-1].direction_index,
                trace[-1].z_index,
                trace[-1].phase_index,
            )
            == indices
        ):
            count = trace[-1].details[0][1] + 1
            trace[-1] = ModeEvent("precise-query-count", t, d, z, p, (("count", count),))
            return
        kind, captured = "precise-query-count", [("count", 1)]
    append(trace, ModeEvent(kind, t, d, z, p, tuple(captured)))


def raw_images(images: Any) -> tuple[Array, tuple[int, ...]]:
    """Resolve raw image storage and validate dimensions and per-frame extents."""
    if not issubclass(type(images), np.ndarray):
        raise AcquisitionModeError("images must be a NumPy array")
    images = np.asarray(images)
    if images.ndim != 6:
        raise AcquisitionModeError("images must be a six-dimensional NumPy array")
    shape = tuple(integer(n, "images dimension") for n in images.shape)
    t, d, p, z, y, x = shape
    if x < 2 or x % 2:
        raise AcquisitionModeError("images require even X>=2")
    for name, count in (
        ("native volume", x * y * z),
        ("padded real volume", (x + 2) * y * z),
        ("half volume", (x // 2 + 1) * y * z),
        ("direction/z/phase count", d * z * p),
        ("time/direction/z/phase count", t * d * z * p),
    ):
        signed(count, name)
    extent(shape, 8)
    return images, shape


def literal(value: Any, name: str, choices: tuple[str, ...]) -> str:
    """Resolve a supported string's underlying text as a plain Python string."""
    if issubclass(type(value), str):
        text = str.__str__(value)
        if text in choices:
            return text
    raise AcquisitionModeError(f"{name} must be {' or '.join(choices)}")


def layout(value: Any) -> str:
    """Resolve the declared physical section stream order."""
    return literal(value, "storage_order", ("direction-major", "z-major"))


def raw_off(off: Any, shape: tuple[int, ...]) -> tuple[Array | None, int]:
    """Resolve off storage and validate dimensions and count before inspecting values."""
    if off is None:
        return None, 0
    t, d, p, z, y, x = shape
    if not issubclass(type(off), np.ndarray):
        raise AcquisitionModeError("off_exposures require a NumPy array with axes (T,D,P,Z,N,Y,X)")
    off = np.asarray(off)
    if off.ndim != 7:
        raise AcquisitionModeError("off_exposures require a NumPy array with axes (T,D,P,Z,N,Y,X)")
    n = integer(off.shape[4], "off_exposures N")
    if off.shape != (t, d, p, z, n, y, x):
        raise AcquisitionModeError("off_exposures shape disagrees with images")
    signed(n + 1, "off/on exposure stride")
    signed(d * p * (n + 1), "direction/phase/exposure count")
    signed(t * d * z * p * (n + 1), "header exposure count")
    extent(off.shape, 8)
    return off, n


def zoom(value: Any, y: int, x: int) -> float:
    """Resolve safe source-float enlargement with exact integral output extents."""
    result = scalar(value, "lateral_zoom", positive=True)
    if result < 1 or float(np.float32(result)) != result:
        raise AcquisitionModeError("lateral_zoom requires L>=1 and exact float32 representation")
    for n in (x, y):
        target = result * n
        if not math.isfinite(target) or not target.is_integer():
            raise AcquisitionModeError("lateral_zoom must give exactly integral output extents")
        signed(int(target), "zoom output extent")
    return result


def output_extents(shape: tuple[int, ...], lateral: float, axial: int) -> None:
    """Check signed output counts and exact native allocation-byte extents."""
    t, _, _, z, y, x = shape
    oz, oy, ox = axial * z, int(lateral * y), int(lateral * x)
    for name, count in (
        ("output Z", oz),
        ("output plane", ox * oy),
        ("output volume", ox * oy * oz),
    ):
        signed(count, name)
    # The actual complex128 volume bounds both historical output byte counts
    # (8/4 per voxel) and lookup bytes (4 per pixel), since oz>=1. The time-axis
    # binary64 image independently needs its aggregate native extent. Products
    # use Python integers, without narrowing or a historical byte-only cap.
    extent((oz, oy, ox), 16)
    extent((t, oz, oy, ox), 8)


@dataclass(frozen=True)
class TwoDPlaneInputs:
    """Literal source stream regrouping, with raw pixel bits and aligned metadata."""

    images: Array
    off_exposures: Array | None
    exposure_background: Array | None
    source_direction_z: Array
    original_shape: tuple[int, ...]
    storage_order: str
    source_revision: str = "SVN307"
    reference_sha256: tuple[tuple[str, str], ...] = REFERENCE


def reinterpret_2d_planes(
    images: Any,
    *,
    storage_order: str,
    off_exposures: Any = None,
    exposure_background: Any = None,
) -> TwoDPlaneInputs:
    """Regroup a declared physical exposure stream into native-Z1 time blocks.

    Parameters
    ----------
    images : numpy.ndarray
        Raw (T,D,P,Zstack,Y,X) array with exact finite float32 samples.
    storage_order : {'direction-major', 'z-major'}
        Physical stream declaration. Direction-major regrouping can mix planes.
    off_exposures : numpy.ndarray or None, optional
        Aligned raw (T,D,P,Zstack,N,Y,X) off frames, in their own dtype.
    exposure_background : numpy.ndarray or None, optional
        On-frame background counts in (T,D,P,Zstack) order.

    Returns
    -------
    TwoDPlaneInputs
        Independent read-only raw arrays in their respective input dtypes:
        images (T*Zstack,D,P,1,Y,X), optional off (T*Zstack,D,P,1,N,Y,X), and
        optional float64 backgrounds (T*Zstack,D,P,1). The int64
        source_direction_z array has shape (Zstack,D,2) with original (d,z)
        labels. Sample bits and caller storage are preserved.

    Raises
    ------
    AcquisitionModeError
        Invalid values, unsafe representation or allocation failure.

    Notes
    -----
    For effective time t*Zstack+q and direction d_new, z-major reads original
    (d_new,q); direction-major reads divmod(q*D+d_new,Zstack). This reinterprets
    the physical stream and can mix nominal planes/directions. It performs no
    camera correction, Fourier transform, resampling or scientific recovery.
    Keep storage_order when passing the result to acquisition preparation.
    See the repository-relative scientific walkthrough:
    docs/architecture/reconstruction-walkthrough.md#selected-acquisition-extensions
    """
    with operation():
        images, shape = raw_images(images)
        t, d, p, z, y, x = shape
        order = layout(storage_order)
        off_exposures, n = raw_off(off_exposures, shape)
        signed(t * z, "effective time count")
        target = (t * z, d, p, 1, y, x)
        extent(target, images.dtype.itemsize)
        extent((z, d, 2), 8)
        if off_exposures is not None:
            extent((t * z, d, p, 1, n, y, x), off_exposures.dtype.itemsize)
        array_metadata(images, "images", shape, raw=True)
        if off_exposures is not None:
            array_metadata(off_exposures, "off_exposures", off_exposures.shape, raw=True)
        extra = (
            None
            if exposure_background is None
            else real_array(exposure_background, "exposure_background", shape[:4])
        )
        result = np.empty(target, dtype=images.dtype)
        result_off = (
            None
            if off_exposures is None
            else np.empty((t * z, d, p, 1, n, y, x), dtype=off_exposures.dtype)
        )
        result_extra = None if extra is None else np.empty(target[:4], dtype=np.float64)
        labels = np.empty((z, d, 2), dtype=np.int64)
        for q in range(z):
            for direction in range(d):
                old_d, old_z = (
                    (direction, q) if order == "z-major" else divmod(q * d + direction, z)
                )
                labels[q, direction] = old_d, old_z
                for time in range(t):
                    result[time * z + q, direction, :, 0] = images[time, old_d, :, old_z]
                    if result_off is not None:
                        assert off_exposures is not None
                        result_off[time * z + q, direction, :, 0] = off_exposures[
                            time, old_d, :, old_z
                        ]
                    if result_extra is not None and extra is not None:
                        result_extra[time * z + q, direction, :, 0] = extra[time, old_d, :, old_z]
        return TwoDPlaneInputs(
            _finish_owned(result),
            None if result_off is None else _finish_owned(result_off),
            None if result_extra is None else _finish_owned(result_extra),
            _finish_owned(labels),
            shape,
            order,
        )
