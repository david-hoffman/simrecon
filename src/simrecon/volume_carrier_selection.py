"""Apply explicit caller limits to a complete fixed-response volume scan."""

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, cast

import numpy as np
import numpy.typing as npt

from ._empirical_response import EmpiricalVolumeResponse
from ._model import SimreconError
from ._volume_carrier_diagnostics import VolumeCarrierCandidate, scan_volume_carriers

_POLICY = "invalid_volume_carrier_selection_policy"


@dataclass(frozen=True)
class VolumeCarrierSelection:
    """Complete scan and the outcome of the caller's inclusive policy.

    Attributes
    ----------
    candidates : tuple of VolumeCarrierCandidate
        Complete caller-ordered diagnostics, including unavailable and duplicate rows.
    eligible_indices : tuple of int
        Increasing zero-based indices passing every gate.
    selected_index : int or None
        Sole eligible index, otherwise None; no extra winner copy is made.
    failure_code : str or None
        no_acceptable_volume_carrier for none, ambiguous_volume_carrier for
        multiple eligible rows, otherwise None. These are result values.

    Notes
    -----
    Field bindings are frozen. Direct construction performs no validation.
    """

    candidates: tuple[VolumeCarrierCandidate, ...]
    eligible_indices: tuple[int, ...]
    selected_index: int | None
    failure_code: str | None


def _limit(value: object) -> float:
    """Validate the source scalar before converting a nonnegative binary64 limit."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(_POLICY, "limits must be nonboolean real scalars")
    try:
        with np.errstate(all="ignore"):
            if isinstance(value, float):
                source_finite = math.isfinite(float.__float__(value))
            else:
                source_finite = not isinstance(value, np.floating) or bool(np.isfinite(value))
            if not source_finite:
                raise SimreconError(_POLICY, "limits must be source-finite")
            converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(_POLICY, "limit cannot convert to binary64") from error
    if not math.isfinite(converted) or converted < 0:
        raise SimreconError(_POLICY, "converted limits must be finite and nonnegative")
    return converted


def _bounds(value: Any) -> tuple[Fraction, Fraction]:
    """Snapshot the exact declared container and return exact squared limits."""
    if type(value) is np.ndarray:
        if value.ndim != 1:
            raise SimreconError(_POLICY, "gain bounds must be one-dimensional")
    elif type(value) not in (tuple, list):
        raise SimreconError(_POLICY, "gain bounds must be a plain tuple, list or ndarray")
    if len(value) != 2:
        raise SimreconError(_POLICY, "gain bounds must contain exactly two limits")
    lower, upper = _limit(value[0]), _limit(value[1])
    if lower > upper:
        raise SimreconError(_POLICY, "gain lower limit exceeds upper limit")
    return Fraction(lower) ** 2, Fraction(upper) ** 2


def select_volume_carrier(
    images: npt.NDArray[Any],
    *,
    response: EmpiricalVolumeResponse,
    voxel_size_um: object,
    phase_steps_rad: npt.NDArray[Any],
    candidate_carriers_yx: object,
    order: object,
    calibration_carrier_bins: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
    max_relative_residual: object,
    min_overlap_count: object,
    gain_magnitude_bounds: object,
) -> VolumeCarrierSelection:
    """Select a sole passing row without ranking or reducing the complete scan.

    Parameters
    ----------
    images : numpy.ndarray
        Real phase/z/y/x observations under known actual phases.
    response : EmpiricalVolumeResponse
        Fixed empirical response; all scan validation and snapshots apply.
    voxel_size_um : tuple or list
        Positive specimen spacing z/y/x in micrometres.
    phase_steps_rad : numpy.ndarray
        Known actual fundamental phases in radians, at least five.
    candidate_carriers_yx : tuple, list or numpy.ndarray
        Exact integer lateral pairs, preserving order, signs and duplicates.
    order : integer scalar
        Positive harmonic one or two.
    calibration_carrier_bins, coordinate_offset_yx : tuple or list
        Fixed exact integer calibration carrier and coordinate offset.
    phase_reference_shift_rad : real scalar
        Fixed specimen-minus-calibration phase reference, radians.
    source : str
        Nonblank opaque pairing label; authenticates no provenance.
    max_relative_residual : real scalar
        Source-finite, finite nonnegative converted binary64 inclusive limit.
    min_overlap_count : integer scalar
        Nonboolean exact positive integer, with no magnitude cap.
    gain_magnitude_bounds : tuple, list or numpy.ndarray
        Two nonnegative finite converted limits with lower <= upper. Plain
        containers only; scalar rules match max_relative_residual.

    Returns
    -------
    VolumeCarrierSelection
        Every scan row and every passing index; selected_index exists only for
        sole acceptance. Zero-valued available fits follow the same gates.

    Raises
    ------
    SimreconError
        invalid_volume_carrier_selection_policy for rejected policy before
        scanning. All inherited scan errors propagate unchanged.

    Notes
    -----
    Compare squared gain components and bounds as exact represented rationals,
    avoiding overflow, underflow and rounded square-root boundary decisions.
    No tolerance, gain cap, nonzero test or status filter is added. Scan failures
    are global; allocation and unrelated exceptions propagate unchanged.
    Small residual and sole acceptance do not establish physical identification,
    unknown phases, informative support or confidence beyond the finite list.
    """
    residual_limit = _limit(max_relative_residual)
    if isinstance(min_overlap_count, (bool, np.bool_)) or not isinstance(
        min_overlap_count, (int, np.integer)
    ):
        raise SimreconError(_POLICY, "overlap count must be a nonboolean integer")
    try:
        count_limit = int(min_overlap_count)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(_POLICY, "overlap count cannot convert to integer") from error
    if count_limit < 1:
        raise SimreconError(_POLICY, "overlap count must be positive")
    lower_squared, upper_squared = _bounds(gain_magnitude_bounds)
    candidates = scan_volume_carriers(
        images,
        response=response,
        voxel_size_um=voxel_size_um,
        phase_steps_rad=phase_steps_rad,
        candidate_carriers_yx=candidate_carriers_yx,
        order=order,
        calibration_carrier_bins=calibration_carrier_bins,
        coordinate_offset_yx=coordinate_offset_yx,
        phase_reference_shift_rad=phase_reference_shift_rad,
        source=source,
    )
    eligible = tuple(
        index
        for index, row in enumerate(candidates)
        if row.gain is not None
        and cast(float, row.relative_residual) <= residual_limit
        and row.overlap_count >= count_limit
        and lower_squared
        <= Fraction(row.gain.real) ** 2 + Fraction(row.gain.imag) ** 2
        <= upper_squared
    )
    if len(eligible) == 1:
        return VolumeCarrierSelection(candidates, eligible, eligible[0], None)
    failure = "ambiguous_volume_carrier" if eligible else "no_acceptable_volume_carrier"
    return VolumeCarrierSelection(candidates, eligible, None, failure)
