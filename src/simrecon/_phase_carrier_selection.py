"""Apply explicit caller policy to a complete unknown-phase carrier scan."""

import math
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._observable_volume_phase_estimation import ObservableVolumePhaseEstimate
from ._phase_carrier_scan import scan_volume_phase_carriers
from ._volume_order_otf import VolumeOrderOtf

_POLICY = "invalid_volume_phase_carrier_selection_policy"


@dataclass(frozen=True)
class VolumePhaseCarrierSelection:
    """Complete independent fits and the outcome of an inclusive caller policy.

    Attributes
    ----------
    candidates : tuple of ObservableVolumePhaseEstimate
        Every scan row in caller order, including duplicates and unavailable rows.
    eligible_indices : tuple of int
        Increasing indices passing stationarity, residual and phase-rank gates.
    selected_index : int or None
        Sole eligible index, otherwise None. No extra winner copy is made.
    failure_code : str or None
        no_acceptable_volume_phase_carrier for none, ambiguous_volume_phase_carrier
        for multiple eligible rows, otherwise None. These are result values.

    Notes
    -----
    Bindings are frozen; row arrays remain independently owned and mutable.
    Direct construction performs no validation.
    """

    candidates: tuple[ObservableVolumePhaseEstimate, ...]
    eligible_indices: tuple[int, ...]
    selected_index: int | None
    failure_code: str | None


def _residual_limit(value: object) -> float:
    """Check source finiteness and the converted binary64 policy value."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(_POLICY, "residual limit must be a nonboolean real scalar")
    try:
        with np.errstate(all="ignore"):
            if isinstance(value, float):
                source_finite = math.isfinite(float.__float__(value))
            else:
                source_finite = not isinstance(value, np.floating) or bool(np.isfinite(value))
            if not source_finite:
                raise SimreconError(_POLICY, "residual limit must be source-finite")
            converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(_POLICY, "residual limit cannot convert to binary64") from error
    if not math.isfinite(converted) or converted < 0:
        raise SimreconError(_POLICY, "converted residual limit must be finite and nonnegative")
    return converted


def select_volume_phase_carrier(
    images: npt.NDArray[np.generic],
    *,
    order_otf: VolumeOrderOtf,
    candidate_carriers_yx: object,
    initial_phases_rad: npt.NDArray[np.generic],
    max_nfev: int,
    gradient_tolerance: float,
    step_tolerance: float,
    source: str,
    max_relative_residual: object,
    min_phase_rank: object,
) -> VolumePhaseCarrierSelection:
    """Select only a sole stationary fit satisfying explicit inclusive limits.

    Parameters
    ----------
    images : numpy.ndarray
        Real observations with phase/z/y/x axes, at least five exposures.
    order_otf : VolumeOrderOtf
        Fixed complex calibration paired to the specimen grid and phase gauge.
    candidate_carriers_yx : tuple, list or numpy.ndarray
        Nonempty integer y/x detector-bin table; scan validation applies unchanged.
    initial_phases_rad : numpy.ndarray
        Nominal starting commands in radians, shared independently by every fit.
    max_nfev : int
        Positive residual evaluation limit for each candidate.
    gradient_tolerance, step_tolerance : float
        Per-row binary64 tolerances strictly between machine epsilon and one.
    source : str
        Nonblank caller pairing label, retained unchanged.
    max_relative_residual : real scalar
        Nonboolean Python/NumPy integer or floating scalar, source-finite and
        finite after binary64 conversion, with converted value >=0.
    min_phase_rank : integer scalar
        Nonboolean exact Python/NumPy integer >=0, without a magnitude cap.

    Returns
    -------
    VolumePhaseCarrierSelection
        Complete scan and increasing eligible indices. Only one eligible row
        yields selected_index; no rows yield no_acceptable_volume_phase_carrier,
        multiple yield ambiguous_volume_phase_carrier.

    Raises
    ------
    SimreconError
        invalid_volume_phase_carrier_selection_policy for invalid policy before
        scanning. Inherited scan errors propagate unchanged. Allocation failures
        and unrelated exceptions propagate.

    Notes
    -----
    Complete the scan before selection. Compare returned residual and phase rank
    directly, inclusively, only for stationary rows. No ranking, deduplication,
    hidden tolerance or physical-carrier identification is supplied. Zero rank
    policies can accept uninformative stationary rows.
    """
    residual_limit = _residual_limit(max_relative_residual)
    if isinstance(min_phase_rank, (bool, np.bool_)) or not isinstance(
        min_phase_rank, (int, np.integer)
    ):
        raise SimreconError(_POLICY, "phase rank limit must be a nonboolean integer")
    try:
        rank_limit = int(min_phase_rank)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(_POLICY, "phase rank limit cannot convert to integer") from error
    if rank_limit < 0:
        raise SimreconError(_POLICY, "phase rank limit must be nonnegative")
    candidates = scan_volume_phase_carriers(
        images,
        order_otf=order_otf,
        candidate_carriers_yx=candidate_carriers_yx,
        initial_phases_rad=initial_phases_rad,
        max_nfev=max_nfev,
        gradient_tolerance=gradient_tolerance,
        step_tolerance=step_tolerance,
        source=source,
    )
    eligible = tuple(
        index
        for index, row in enumerate(candidates)
        if row.termination == "stationary"
        and row.relative_residual <= residual_limit
        and row.phase_rank >= rank_limit
    )
    if len(eligible) == 1:
        return VolumePhaseCarrierSelection(candidates, eligible, eligible[0], None)
    failure = "ambiguous_volume_phase_carrier" if eligible else "no_acceptable_volume_phase_carrier"
    return VolumePhaseCarrierSelection(candidates, eligible, None, failure)
