"""Separate three known, equally spaced phases at the acquired spatial sampling."""

from dataclasses import dataclass
from math import cos, isfinite, pi, sin, sqrt

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class PhaseComponents:
    """Image-space phase coefficients with independently owned mutable arrays.

    Attributes
    ----------
    dc : numpy.ndarray
        Zero-order coefficient, a native C-contiguous float64 array of shape (y, x).
    c1 : numpy.ndarray
        Coefficient of exp(+i*phase), a native C-contiguous complex128 array of
        shape (y, x). The negative-order coefficient is its complex conjugate.
    """

    dc: npt.NDArray[np.float64]
    c1: npt.NDArray[np.complex128]


def separate_phases(
    images: npt.NDArray[np.generic], *, phase_offset_rad: int | float | np.integer | np.floating
) -> PhaseComponents:
    """Separate three real images with explicit phase offset and 2*pi/3 spacing.

    Parameters
    ----------
    images : numpy.ndarray
        Plain array of shape (3, y, x), with positive spatial dimensions and
        finite uint16, float32 or float64 values. Either byte order and strided
        or read-only storage are accepted. Spatial axes retain their order.
    phase_offset_rad : int or float or numpy.integer or numpy.floating
        Required keyword-only first phase in radians. Its float64 conversion
        must be finite and within [-pi, pi]. Booleans are rejected.

    Returns
    -------
    PhaseComponents
        Independently owned mutable dc and c1 arrays in the input intensity
        units. Separation uses a negative exponential and divides by three.

    Raises
    ------
    SimreconError
        If the image object, dtype, shape, finite values or offset violates
        the public phase-separation contract. The input is never modified.

    Notes
    -----
    This is phase separation at the acquired sampling, with no modulation
    correction or spatial reconstruction. Per-pixel power-of-two scaling
    prevents intermediate overflow without a data-dependent intensity ceiling.
    """
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_phase_images", "images must be a plain NumPy ndarray")
    if images.dtype.newbyteorder("=") not in (
        np.dtype(np.uint16),
        np.dtype(np.float32),
        np.dtype(np.float64),
    ):
        raise SimreconError(
            "invalid_phase_dtype", "images must have uint16, float32 or float64 dtype"
        )
    if images.ndim != 3 or images.shape[0] != 3 or 0 in images.shape[1:]:
        raise SimreconError(
            "invalid_phase_shape", "images must have shape (3, positive_y, positive_x)"
        )
    if not np.all(np.isfinite(images)):
        raise SimreconError("nonfinite_phase_images", "images must contain only finite values")
    if isinstance(phase_offset_rad, (bool, np.bool_)) or not isinstance(
        phase_offset_rad, (int, float, np.integer, np.floating)
    ):
        raise SimreconError("invalid_phase_offset", "phase offset must be a real nonboolean scalar")
    try:
        offset = float(phase_offset_rad)
    except OverflowError as error:
        raise SimreconError(
            "invalid_phase_offset", "phase offset must convert to finite float64"
        ) from error
    if not isfinite(offset) or not -pi <= offset <= pi:
        raise SimreconError(
            "invalid_phase_offset", "phase offset must be finite and within [-pi, pi]"
        )

    values = np.array(images, dtype=np.float64, order="C", copy=True)
    # Scaling each pixel separately also preserves subnormal-only pixels beside
    # bright pixels. Zero has exponent zero; no division by its magnitude occurs.
    _, exponent = np.frexp(np.max(np.abs(values), axis=0))
    with np.errstate(under="ignore"):
        first, second, third = np.ldexp(values, -exponent)
        mean = (first + second + third) / 3
        # The exact mean is inside the input range. Clamp rounding overshoot
        # before restoring the exponent, including a constant at float64 max.
        mean = np.clip(
            mean,
            np.minimum.reduce((first, second, third)),
            np.maximum.reduce((first, second, third)),
        )
        dc = np.ldexp(mean, exponent)
        real = (2 * first - second - third) / 6
        imag = (third - second) * (sqrt(3) / 6)
        cosine, sine = cos(offset), sin(offset)
        c1 = np.empty(dc.shape, dtype=np.complex128)
        c1.real = np.ldexp(real * cosine + imag * sine, exponent)
        c1.imag = np.ldexp(imag * cosine - real * sine, exponent)
    return PhaseComponents(dc, c1)
