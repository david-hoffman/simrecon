"""Locate a unique positive grid maximum in an observed intensity volume."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._array_validation import conversion_errors, require_finite
from ._model import SimreconError


@dataclass(frozen=True)
class BeadPeak:
    """Scalar grid-peak observation with frozen bindings.

    Attributes
    ----------
    index_zyx : tuple of int
        Zero-based logical z/y/x coordinate of the selected sample.
    value : float
        Exact converted sample in the caller's supplied intensity unit.
    """

    index_zyx: tuple[int, int, int]
    value: float


def locate_bead_peak(volume: npt.NDArray[np.generic]) -> BeadPeak:
    """Return the sole positive global maximum after float64 conversion.

    Parameters
    ----------
    volume : numpy.ndarray
        Plain real integer or floating array with three positive dimensions,
        ordered z/y/x. Source and converted samples must all be finite.
        Read-only, strided, reversed and either byte-order storage are accepted.

    Returns
    -------
    BeadPeak
        Built-in integer coordinates and a built-in float value. The result
        retains no array storage. Direct record construction is unvalidated.

    Raises
    ------
    SimreconError
        Stable invalid_bead_peak_volume, invalid_bead_peak_dtype or
        invalid_bead_peak_shape for invalid representation;
        nonfinite_bead_peak_volume for nonfinite source/conversion;
        no_positive_bead_peak for a nonpositive converted maximum;
        ambiguous_bead_peak for multiple exactly equal positive maxima.

    Notes
    -----
    Selection uses an independent native float64 snapshot. Rounding may create
    ties and finite underflow is allowed. Positive subnormals, signed samples,
    lower ties and unequal secondary maxima are valid. There is no tolerance,
    normalization, correction, phase separation or hidden group selection.
    Caller storage and NumPy error settings are preserved; allocation and
    unrelated errors propagate. One full converted volume plus scratch is owned.

    A grid maximum neither certifies an isolated bead nor estimates a continuous
    emitter center. Its physical meaning requires an explicitly chosen detection
    peak-origin gauge. Units, spacing and physical coordinates are not inferred.
    """
    if type(volume) is not np.ndarray:
        raise SimreconError("invalid_bead_peak_volume", "volume must be a plain NumPy ndarray")
    if volume.dtype.kind not in "iuf":
        raise SimreconError("invalid_bead_peak_dtype", "volume must have a real numeric dtype")
    if volume.ndim != 3 or 0 in volume.shape:
        raise SimreconError("invalid_bead_peak_shape", "volume must have three positive dimensions")

    with np.errstate(all="ignore"):
        require_finite(volume, "nonfinite_bead_peak_volume", "source samples must be finite")
        with conversion_errors(
            "nonfinite_bead_peak_volume", "samples cannot be converted to float64"
        ):
            values = volume.astype(np.float64, order="C", copy=True)
        require_finite(values, "nonfinite_bead_peak_volume", "converted samples must be finite")

    peak = float(np.max(values))
    if peak <= 0:
        raise SimreconError("no_positive_bead_peak", "converted maximum must be positive")
    if np.count_nonzero(values == peak) > 1:
        raise SimreconError("ambiguous_bead_peak", "positive global maximum must be unique")
    z, y, x = np.unravel_index(np.argmax(values), values.shape)
    return BeadPeak((int(z), int(y), int(x)), peak)
