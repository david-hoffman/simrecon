"""Compare every integer periodic translation against an explicit reference."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class TranslationEstimate:
    """Full mismatch surface and caller-defined translation ambiguity.

    Attributes
    ----------
    normalized_rms : numpy.ndarray
        Independently owned mutable native float64 C-contiguous surface, shape
        (Ny, Nx), in increasing canonical signed y/x displacement order.
    minimum_normalized_rms : float
        Actual minimum entry of the returned dimensionless RMS surface.
    candidate_displacements_pixels_yx : tuple of tuple of int
        Every displacement whose score minus the minimum is at most the
        supplied tolerance, in canonical row-major order, in pixels.
    displacement_pixels_yx : tuple of int or None
        Sole qualifying content displacement, otherwise None. Alignment uses
        its negative, with periodic boundaries.
    failure_code : str or None
        ambiguous_translation when multiple displacements qualify, else None.
        This result is not a physical motion or fit-acceptance guarantee.
    """

    normalized_rms: npt.NDArray[np.float64]
    minimum_normalized_rms: float
    candidate_displacements_pixels_yx: tuple[tuple[int, int], ...]
    displacement_pixels_yx: tuple[int, int] | None
    failure_code: str | None


def _image_snapshot(value: object) -> npt.NDArray[np.float64]:
    """Validate source values and snapshot the represented float64 image."""
    code = "invalid_translation_images"
    if (
        type(value) is not np.ndarray
        or value.dtype.kind not in "iuf"
        or value.ndim != 2
        or value.size == 0
    ):
        raise SimreconError(code, "images must be plain nonempty real two-dimensional arrays")
    if not np.isfinite(value).all():
        raise SimreconError(code, "source images must be finite")
    try:
        with np.errstate(all="ignore"):
            snapshot = np.array(value, dtype=np.float64, order="C", copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "image cannot convert to float64") from error
    if not np.isfinite(snapshot).all():
        raise SimreconError(code, "converted images must be finite")
    return snapshot


def _tolerance(value: object) -> float:
    """Validate the source sign before potentially underflowing conversion."""
    code = "invalid_translation_tolerance"
    if type(value) is np.ndarray and value.ndim == 0 and value.dtype.kind in "iuf":
        value = value[()]
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "tolerance must be a nonboolean real scalar or plain 0D array")
    # Python integers are finite without narrowing their arbitrary precision.
    if value < 0 or (isinstance(value, (float, np.floating)) and not np.isfinite(value)):
        raise SimreconError(code, "source tolerance must be finite and nonnegative")
    try:
        with np.errstate(all="ignore"):
            converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "tolerance cannot convert to float64") from error
    if not math.isfinite(converted) or converted < 0:
        raise SimreconError(code, "converted tolerance must be finite and nonnegative")
    return converted


def estimate_translation(
    moving: npt.NDArray[Any],
    *,
    reference: npt.NDArray[Any],
    ambiguity_tolerance: object,
) -> TranslationEstimate:
    """Estimate periodic integer content motion against an equal-intensity image.

    Parameters
    ----------
    moving : numpy.ndarray
        Plain finite real nonempty image, shape (Ny, Nx). Integer and floating
        dtypes, either byte order and arbitrary strides are permitted. Values
        must remain finite after float64 conversion; rounding and underflow
        are permitted. Caller storage is preserved.
    reference : numpy.ndarray
        Required reference with the same shape and representation rules.
    ambiguity_tolerance : int, float or numpy.ndarray
        Required nonboolean Python/NumPy real scalar or plain real 0D array.
        Source and float64 conversion must be finite and nonnegative. No cap.
        Inclusive absolute allowance above this call's minimum RMS score.

    Returns
    -------
    TranslationEstimate
        Full all-pixel normalized root mean square (RMS) mismatch surface and
        all qualifying integer displacements in y/x pixels. The canonical
        axis grid is -floor(L/2) through ceil(L/2)-1, so an even half-period
        uses the negative representative. Multiple candidates are ambiguous.

    Raises
    ------
    SimreconError
        invalid_translation_images for invalid images or nonfinite conversion;
        incompatible_translation_shape for unequal valid shapes;
        invalid_translation_tolerance for an invalid tolerance.
        Allocation and unrelated exceptions propagate unchanged.

    Notes
    -----
    Snapshot both inputs as float64, divide both by their common maximum
    absolute intensity B, then directly evaluate RMS pixel differences at
    every periodic shift. For B=0 every score is zero. No brightness fitting,
    mean subtraction, masking, interpolation or hidden acceptance policy is
    applied. Content motion (dy, dx) aligns with roll(-dy, -dx).

    This direct method costs O(P squared) work for P pixels and uses O(P)
    working storage. Use modest arrays. A unique candidate does not establish
    physical motion, confidence or model adequacy. Different raw structured
    illumination microscopy phase frames need not satisfy the equal-intensity
    translation model. NumPy error mode and unrelated warnings are preserved.
    """
    tolerance = _tolerance(ambiguity_tolerance)
    m, r = _image_snapshot(moving), _image_snapshot(reference)
    if m.shape != r.shape:
        raise SimreconError("incompatible_translation_shape", "images must have equal shapes")

    ny, nx = m.shape
    y_shifts = range(-(ny // 2), (ny + 1) // 2)
    x_shifts = range(-(nx // 2), (nx + 1) // 2)
    surface = np.empty((ny, nx), dtype=np.float64)
    with np.errstate(all="ignore"):
        scale = max(float(np.max(np.abs(m))), float(np.max(np.abs(r))))
        if scale == 0:
            surface.fill(0)
        else:
            # Divide directly: the reciprocal of a subnormal B can overflow.
            m /= scale
            r /= scale
            for iy, dy in enumerate(y_shifts):
                for ix, dx in enumerate(x_shifts):
                    difference = np.roll(m, (-dy, -dx), axis=(0, 1)) - r
                    surface[iy, ix] = np.sqrt(np.mean(difference * difference))

    minimum = float(np.min(surface))
    candidates = tuple(
        (dy, dx)
        for iy, dy in enumerate(y_shifts)
        for ix, dx in enumerate(x_shifts)
        if float(surface[iy, ix]) - minimum <= tolerance
    )
    sole = len(candidates) == 1
    return TranslationEstimate(
        surface,
        minimum,
        candidates,
        candidates[0] if sole else None,
        None if sole else "ambiguous_translation",
    )
