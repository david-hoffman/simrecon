"""Expose caller-ordered integer-carrier illumination diagnostics."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._illumination import IlluminationEstimate, _carrier, estimate_illumination
from ._model import SimreconError
from ._otf import Otf2D


@dataclass(frozen=True)
class CarrierCandidate:
    """One supplied carrier's fit or local information failure.

    Attributes
    ----------
    carrier_bins_yx : tuple of int
        Supplied signed detector-bin shift (ky, kx), retained without wrapping.
    estimate : IlluminationEstimate or None
        Independently owned successful fit, otherwise None.
    failure_code : str or None
        Local no_illumination_overlap or unidentifiable_illumination, otherwise
        None. Other failures abort the whole scan.
    """

    carrier_bins_yx: tuple[int, int]
    estimate: IlluminationEstimate | None
    failure_code: str | None


def _candidates(value: object) -> tuple[tuple[int, int], ...]:
    """Copy and validate the entire collection before executing any candidate."""
    code = "invalid_carrier_candidates"
    if type(value) is np.ndarray:
        if value.ndim != 2 or value.shape[1] != 2:
            raise SimreconError(code, "candidate array must have shape (M, 2)")
        rows = value
    elif isinstance(value, (tuple, list)):
        rows = value
    else:
        raise SimreconError(code, "candidates must be a tuple, list or plain ndarray")
    if len(rows) == 0:
        raise SimreconError(code, "at least one candidate is required")
    try:
        return tuple(_carrier(row) for row in rows)
    except SimreconError as error:
        if error.code == "invalid_illumination_carrier":
            raise SimreconError(code, error.message) from None
        raise


def scan_carriers(
    images: npt.NDArray[Any],
    *,
    otf: Otf2D,
    phase_steps_rad: npt.NDArray[Any],
    candidate_carriers_bins_yx: object,
) -> tuple[CarrierCandidate, ...]:
    """Fit each supplied integer carrier without selecting or ranking a winner.

    Parameters
    ----------
    images : numpy.ndarray
        Real acquisition (N, Ny, Nx), with the estimate_illumination input rules.
    otf : Otf2D
        Full complex transfer on the matching detector grid.
    phase_steps_rad : numpy.ndarray
        Required relative phases (N,), in radians, evaluated as stored.
    candidate_carriers_bins_yx : tuple, list or numpy.ndarray
        Nonempty collection of signed nonboolean integer (ky, kx) pairs.
        A plain array must have shape (M, 2). No count cap or wrapping applies.

    Returns
    -------
    tuple of CarrierCandidate
        Complete caller-ordered results, preserving signs, zero and duplicates.
        Successful estimates own separate mutable phase arrays.

    Raises
    ------
    SimreconError
        For invalid candidates or inherited common, solver and range failures.
        Only no_illumination_overlap and unidentifiable_illumination become
        candidate-local records. Allocation and unrelated exceptions propagate.

    Notes
    -----
    The entire candidate representation is validated before fitting. Every
    candidate uses estimate_illumination, including common phase/OTF validation
    when no candidate succeeds. Any nonlocal failure aborts without a partial
    tuple. Low residual, geometric overlap count and above-one modulation do
    not establish physical carrier identifiability or recovery confidence.
    """
    carriers = _candidates(candidate_carriers_bins_yx)
    results = []
    for carrier in carriers:
        try:
            estimate = estimate_illumination(
                images, otf=otf, phase_steps_rad=phase_steps_rad, carrier_bins_yx=carrier
            )
        except SimreconError as error:
            if error.code not in ("no_illumination_overlap", "unidentifiable_illumination"):
                raise
            results.append(CarrierCandidate(carrier, None, error.code))
        else:
            results.append(CarrierCandidate(carrier, estimate, None))
    return tuple(results)
