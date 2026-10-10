"""Select the unique finite-scan row passing explicit caller limits."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._carrier import CarrierCandidate, scan_carriers
from ._model import SimreconError
from ._otf import Otf2D, _pair

_POLICY_ERROR = "invalid_carrier_selection_policy"


@dataclass(frozen=True)
class CarrierSelection:
    """Complete diagnostics and the outcome of an explicit acceptance policy.

    Attributes
    ----------
    candidates : tuple of CarrierCandidate
        Complete caller-ordered scan, including local failures and duplicates.
        Successful estimates retain independent mutable phase arrays.
    eligible_indices : tuple of int
        Increasing zero-based indices of every policy-passing row.
    selected_index : int or None
        Sole eligible index, otherwise None.
    failure_code : str or None
        no_acceptable_carrier for zero eligible rows, ambiguous_carrier for
        multiple eligible rows, otherwise None. These are result values.
    """

    candidates: tuple[CarrierCandidate, ...]
    eligible_indices: tuple[int, ...]
    selected_index: int | None
    failure_code: str | None


def _nonnegative_limit(value: object) -> float:
    """Validate source finiteness and convert a real policy limit to float64."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(_POLICY_ERROR, "limits must be nonboolean real scalars")
    # Integers are source-finite without converting arbitrary precision to float.
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        raise SimreconError(_POLICY_ERROR, "limits must be source-finite")
    try:
        with np.errstate(all="ignore"):
            converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(_POLICY_ERROR, "limit cannot convert to float64") from error
    if not math.isfinite(converted) or converted < 0:
        raise SimreconError(_POLICY_ERROR, "converted limits must be finite and nonnegative")
    return converted


def select_carrier(
    images: npt.NDArray[Any],
    *,
    otf: Otf2D,
    phase_steps_rad: npt.NDArray[Any],
    candidate_carriers_bins_yx: object,
    max_relative_residual: object,
    min_overlap_count: object,
    modulation_bounds: object,
) -> CarrierSelection:
    """Select exactly one passing row from a complete integer-carrier scan.

    Parameters
    ----------
    images : numpy.ndarray
        Real acquisition (N, Ny, Nx), following scan_carriers input rules.
    otf : Otf2D
        Full complex transfer on the matching detector grid.
    phase_steps_rad : numpy.ndarray
        Required relative phases (N,), in radians, evaluated as stored.
    candidate_carriers_bins_yx : tuple, list or numpy.ndarray
        Nonempty caller-ordered signed nonboolean integer (ky, kx) pairs.
    max_relative_residual : int or float
        Nonboolean Python/NumPy real scalar, source-finite and converting to
        finite nonnegative float64. Inclusive upper residual limit; no cap.
    min_overlap_count : int
        Nonboolean Python/NumPy integer >= 1, without a magnitude cap.
    modulation_bounds : tuple, list or numpy.ndarray
        Two limits with the residual scalar rules, converted lower <= upper.
        Plain one-dimensional arrays are allowed. Zero/equal/above-one bounds
        are permitted. Both limits are inclusive.

    Returns
    -------
    CarrierSelection
        All scan diagnostics and eligible indices. A sole passing row supplies
        selected_index; zero or multiple passing rows supply a failure_code.

    Raises
    ------
    SimreconError
        invalid_carrier_selection_policy for invalid limits, before scanning;
        otherwise inherited scan errors propagate unchanged. Allocation and
        unrelated failures propagate without a partial selection.

    Notes
    -----
    A row passes only if its estimate exists and all three limits pass. No
    ranking, deduplication, tolerance, fallback or automatic reconstruction is
    applied. Low residual and geometric overlap count do not establish the
    physical carrier, informative support or confidence. Frozen record bindings
    leave estimate arrays mutable; scan ownership and precision are preserved.
    """
    residual_limit = _nonnegative_limit(max_relative_residual)
    if isinstance(min_overlap_count, (bool, np.bool_)) or not isinstance(
        min_overlap_count, (int, np.integer)
    ):
        raise SimreconError(_POLICY_ERROR, "overlap count must be a nonboolean integer")
    count_limit = int(min_overlap_count)
    if count_limit < 1:
        raise SimreconError(_POLICY_ERROR, "overlap count must be positive")
    lower_value, upper_value = _pair(modulation_bounds, _POLICY_ERROR)
    lower, upper = _nonnegative_limit(lower_value), _nonnegative_limit(upper_value)
    if lower > upper:
        raise SimreconError(_POLICY_ERROR, "modulation lower limit exceeds upper limit")

    candidates = scan_carriers(
        images,
        otf=otf,
        phase_steps_rad=phase_steps_rad,
        candidate_carriers_bins_yx=candidate_carriers_bins_yx,
    )
    eligible = tuple(
        index
        for index, row in enumerate(candidates)
        if row.estimate is not None
        and row.estimate.relative_residual <= residual_limit
        and row.estimate.overlap_count >= count_limit
        and lower <= row.estimate.modulation <= upper
    )
    if len(eligible) == 1:
        return CarrierSelection(candidates, eligible, eligible[0], None)
    failure = "ambiguous_carrier" if eligible else "no_acceptable_carrier"
    return CarrierSelection(candidates, eligible, None, failure)
