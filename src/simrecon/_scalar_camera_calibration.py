"""Estimate finite scalar camera moments from dark, blank and flat images."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._array_validation import require_finite
from ._model import SimreconError

_INVALID = "invalid_scalar_camera_calibration"
_RANGE = "scalar_camera_calibration_range"
_Vector = npt.NDArray[np.float64]
_FrameVectors = tuple[_Vector, _Vector, _Vector]


@dataclass(frozen=True)
class ScalarCameraEstimate:
    """Finite image statistics with frozen bindings and independent mutable arrays.

    Attributes
    ----------
    means_counts : numpy.ndarray
        Group means in counts, ordered dark, blank, flat.
    variances_counts2 : numpy.ndarray
        Group averages of within-frame sample variances in counts squared.
    frame_means_counts : tuple of numpy.ndarray
        Separately owned frame-mean vectors in group order.
    frame_variances_counts2 : tuple of numpy.ndarray
        Separately owned within-frame variance vectors, using divisor K-1.
    empirical_mean_se_counts : numpy.ndarray
        Descriptive standard errors from the returned frame and group means.
    contrast_counts : float
        Returned flat mean minus returned blank mean, in counts.
    gain_counts_per_e : float or None
        Positive finite variance-contrast/mean-contrast ratio when available.
    information_codes : tuple of str
        Ordered unavailable-gain and signed-background diagnostics.
    source : str
        Unchanged opaque acquisition label, without authentication.
    """

    means_counts: _Vector
    variances_counts2: _Vector
    frame_means_counts: _FrameVectors
    frame_variances_counts2: _FrameVectors
    empirical_mean_se_counts: _Vector
    contrast_counts: float
    gain_counts_per_e: float | None
    information_codes: tuple[str, ...]
    source: str


def _snapshot(value: Any) -> _Vector:
    """Validate a plain repeated stack and independently normalize its samples."""
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        raise SimreconError(_INVALID, "counts must be plain real numeric ndarrays")
    if (
        value.ndim != 3
        or value.shape[0] < 2
        or value.shape[1] < 1
        or value.shape[2] < 1
        or value.shape[1] * value.shape[2] < 2
    ):
        raise SimreconError(_INVALID, "counts require axes (frame,y,x), at least two frames/pixels")
    require_finite(value, _INVALID, "original counts must be finite")
    result = value.astype(np.float64, order="C", copy=True)
    require_finite(result, _INVALID, "counts must convert to finite float64")
    return result


def _scaled(values: _Vector) -> tuple[_Vector, int]:
    """Retain a separate binary scale for each statistical component."""
    _, exponent = np.frexp(np.max(np.abs(values)))
    return np.ldexp(values, -int(exponent)), int(exponent)


def _mean(values: _Vector) -> np.float64:
    """Average bounded coordinates, preserving constant values exactly."""
    scaled, exponent = _scaled(values)
    anchor = scaled.flat[0]
    return np.ldexp(anchor + np.mean(scaled - anchor), exponent)


def _frame_moments(group: _Vector) -> tuple[_Vector, _Vector]:
    """Compute each frame independently before any averaging across frames."""
    means = np.empty(group.shape[0], dtype=np.float64)
    variances = np.empty(group.shape[0], dtype=np.float64)
    pixels = group.shape[1] * group.shape[2]
    for index, frame in enumerate(group):
        scaled, exponent = _scaled(frame)
        anchor = scaled.flat[0]
        differences = scaled - anchor
        mean_difference = np.mean(differences)
        means[index] = np.ldexp(anchor + mean_difference, exponent)
        centered = differences - mean_difference
        # Square in bounded coordinates and restore only the final variance.
        # Centering differences also gives constant frames exactly zero variance.
        variances[index] = np.ldexp(
            np.mean(centered * centered) * (pixels / (pixels - 1)), 2 * exponent
        )
    require_finite(means, _RANGE, "frame means are nonfinite")
    require_finite(variances, _RANGE, "frame variances are nonfinite")
    return means, variances


def _mean_se(frame_means: _Vector, group_mean: np.float64) -> np.float64:
    """Evaluate repeatability from returned points without squaring their scale."""
    scaled, exponent = _scaled(frame_means)
    differences = scaled - np.ldexp(group_mean, -exponent)
    return np.ldexp(np.sqrt(np.mean(differences * differences) / (frame_means.size - 1)), exponent)


def estimate_scalar_camera(
    dark_counts: npt.NDArray[Any],
    *,
    blank_counts: npt.NDArray[Any],
    flat_counts: npt.NDArray[Any],
    source: str,
) -> ScalarCameraEstimate:
    """Estimate finite camera statistics from three labeled repeated ensembles.

    Parameters
    ----------
    dark_counts, blank_counts, flat_counts : numpy.ndarray
        Plain finite real stacks (frame,y,x), with matching detector dimensions,
        at least two frames per group and at least two pixels per frame. Samples
        are independently copied to native float64 before computing moments.
    source : str
        Nonblank opaque label retained unchanged.

    Returns
    -------
    ScalarCameraEstimate
        Owned writable moments and descriptive repeatability, signed flat
        contrast, optional photon-transfer gain and ordered information codes.

    Raises
    ------
    SimreconError
        invalid_scalar_camera_calibration for input/source domain violations;
        scalar_camera_calibration_range for nonfinite required statistics.

    Notes
    -----
    Variances use K-1 within each frame, then average frames equally. Relative
    normalization uses the returned blank mean and positive flat-minus-blank
    mean contrast, independently of physical gain availability. Gain is the
    positive finite ratio of returned variance and mean contrasts. These finite
    statistics certify neither the stationary scalar camera model nor instrument
    accuracy. No true camera coefficients or illumination levels are inputs.
    Caller storage and error/warning policies survive; expected floating-point
    range events are handled locally. Allocation and unrelated exceptions pass
    through. Direct result construction adds no validation promise.
    """
    if type(source) is not str or not source.strip():
        raise SimreconError(_INVALID, "source must be a nonblank string")
    with np.errstate(all="ignore"):
        groups = tuple(_snapshot(group) for group in (dark_counts, blank_counts, flat_counts))
        if any(group.shape[1:] != groups[0].shape[1:] for group in groups[1:]):
            raise SimreconError(_INVALID, "detector y/x dimensions must match")
        # All three snapshots exist before moment computation starts.
        dark, blank, flat = (_frame_moments(group) for group in groups)
        frame_means = (dark[0], blank[0], flat[0])
        frame_variances = (dark[1], blank[1], flat[1])
        means = np.array([_mean(values) for values in frame_means], dtype=np.float64)
        variances = np.array([_mean(values) for values in frame_variances], dtype=np.float64)
        require_finite(means, _RANGE, "group means are nonfinite")
        require_finite(variances, _RANGE, "group variances are nonfinite")
        dm = np.subtract(means[2], means[1])
        dv = np.subtract(variances[2], variances[1])
        db = np.subtract(means[1], means[0])
        require_finite([dm, dv, db], _RANGE, "returned-point contrasts are nonfinite")
        standard_errors = np.array(
            [_mean_se(values, mean) for values, mean in zip(frame_means, means, strict=True)],
            dtype=np.float64,
        )
        require_finite(standard_errors, _RANGE, "empirical mean standard errors are nonfinite")
        codes = []
        if dm <= 0:
            codes.append("nonpositive_flat_contrast")
        if dv <= 0:
            codes.append("nonpositive_variance_contrast")
        gain = None
        if dm > 0 and dv > 0:
            quotient = np.divide(dv, dm)
            if np.isfinite(quotient) and quotient > 0:
                gain = float(quotient)
            else:
                codes.append("unrepresentable_gain")
        if db < 0:
            codes.append("negative_background_estimate")
    return ScalarCameraEstimate(
        means,
        variances,
        frame_means,
        frame_variances,
        standard_errors,
        float(dm),
        gain,
        tuple(codes),
        source,
    )
