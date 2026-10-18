"""Fit volume phases after removing structurally invisible real Fourier modes."""

from dataclasses import dataclass
from typing import cast

import numpy as np
import numpy.typing as npt

from ._volume_order_otf import VolumeOrderOtf
from ._volume_phase_estimation import (
    VolumePhaseEstimate,
    _estimate,
)


@dataclass(frozen=True)
class ObservableVolumePhaseEstimate(VolumePhaseEstimate):
    """Local phase fit and its structurally observable real nuisance domain.

    Attributes
    ----------
    observable_fourier_mask : numpy.ndarray
        Owned mutable native Boolean array in centered z/y/x frequency storage.
    observable_dimension, unobservable_dimension : int
        Retained and excluded real Fourier dimensions. The inherited specimen
        is the full-grid minimum-norm observable representative, not hidden
        physical specimen truth. All other fields inherit VolumePhaseEstimate.
    """

    observable_fourier_mask: npt.NDArray[np.bool_]
    observable_dimension: int
    unobservable_dimension: int


def estimate_observable_volume_phases(
    images: npt.NDArray[np.generic],
    *,
    order_otf: VolumeOrderOtf,
    carrier_bins_yx: tuple[int, int],
    initial_phases_rad: npt.NDArray[np.generic],
    max_nfev: int,
    gradient_tolerance: float,
    step_tolerance: float,
    source: str,
) -> ObservableVolumePhaseEstimate:
    """Fit all phases in a fixed calibration gauge on observable real modes.

    Parameters
    ----------
    images : numpy.ndarray
        Finite real observations, axes phase/z/y/x with at least five exposures.
    order_otf : VolumeOrderOtf
        Full complex positive-order transfers in the supplied fixed gauge.
    carrier_bins_yx : tuple of int
        Exact integer lateral carrier; only indexing is reduced periodically.
    initial_phases_rad : numpy.ndarray
        One finite real initial angle per exposure, in radians.
    max_nfev : int
        Positive residual evaluation limit for the single local TRF solve.
    gradient_tolerance, step_tolerance : float
        Binary64 tolerances strictly between machine epsilon and one.
    source : str
        Nonblank opaque caller label retained unchanged.

    Returns
    -------
    ObservableVolumePhaseEstimate
        Owned fit arrays and diagnostics. Zero structural dimension and initial
        numerical rank deficiency are unavailable outcomes without optimization.

    Raises
    ------
    SimreconError
        For inherited input, transform, numerical solver or derived range errors.
        Unrelated errors, warnings and allocation failures retain their behavior.

    Notes
    -----
    Structural visibility uses exact normalized signed transfer components and
    all-axis modular Hermitian closure. Retained weak modes still undergo the
    numerical SVD cutoff. The full real/imaginary objective and all phase
    coordinates remain in the supplied calibration gauge. The specimen is a
    minimum-norm observable representative; stationarity supplies no global
    uniqueness, physical accuracy or scalable-volume guarantee.
    """
    with np.errstate(all="ignore"):
        return cast(
            ObservableVolumePhaseEstimate,
            _estimate(
                images,
                order_otf,
                carrier_bins_yx,
                initial_phases_rad,
                max_nfev,
                gradient_tolerance,
                step_tolerance,
                source,
                observable=True,
            ),
        )
