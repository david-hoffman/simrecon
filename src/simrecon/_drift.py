"""Prepare periodic images and illumination phases for known specimen drift."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class DriftCorrection:
    """Aligned observations and phases in reference specimen coordinates.

    Attributes
    ----------
    images : numpy.ndarray
        Independently owned mutable native float64 C-contiguous observations,
        shape (N, Ny, Nx), in input intensity units.
    phases_rad : numpy.ndarray
        Independently owned mutable native float64 C-contiguous principal
        phases, shape (N,), in radians within [-pi, pi].
    """

    images: npt.NDArray[np.float64]
    phases_rad: npt.NDArray[np.float64]


def _plain_array(value: object, *, kinds: str, code: str) -> npt.NDArray[Any]:
    """Reject containers, subclasses and dtype kinds outside the contract."""
    if type(value) is not np.ndarray or value.dtype.kind not in kinds:
        raise SimreconError(code, f"input must be a plain NumPy array of dtype kind {kinds}")
    return value


def _float_snapshot(values: npt.NDArray[Any], *, code: str) -> npt.NDArray[np.float64]:
    """Own the converted values, permitting finite rounding and underflow."""
    if not np.isfinite(values).all():
        raise SimreconError(code, "source values must be finite")
    try:
        with np.errstate(all="ignore"):
            snapshot = np.array(values, dtype=np.float64, order="C", copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "values cannot convert to float64") from error
    if not np.isfinite(snapshot).all():
        raise SimreconError(code, "converted values must be finite")
    return snapshot


def correct_integer_drift(
    images: npt.NDArray[Any],
    *,
    phases_rad: npt.NDArray[Any],
    carrier_bins_yx: npt.NDArray[Any],
    displacements_pixels_yx: npt.NDArray[Any],
) -> DriftCorrection:
    """Align known integer specimen translations and correct illumination phase.

    Parameters
    ----------
    images : numpy.ndarray
        Plain real integer or floating array, shape (N, Ny, Nx), with positive
        dimensions. Source and converted float64 values must be finite.
        Either endian, arbitrary strides and read-only storage are accepted.
    phases_rad : numpy.ndarray
        Required plain real array, shape (N,), in radians. The image conversion
        rules apply. Every finite phase is valid, with no phase-rank condition.
    carrier_bins_yx : numpy.ndarray
        Required plain signed or unsigned integer array, shape (2,), giving
        the stationary illumination carrier in detector Fourier bins (y, x).
    displacements_pixels_yx : numpy.ndarray
        Required plain signed or unsigned integer array, shape (N, 2), giving
        specimen content motion in pixels (y, x). All integer values and
        periodic aliases are valid for both integer inputs.

    Returns
    -------
    DriftCorrection
        Float64 snapshots aligned by the negative displacements, with positive
        carrier-dot-displacement phase increments represented as principal
        angles. Record bindings are frozen; both owned arrays remain mutable.

    Raises
    ------
    SimreconError
        invalid_drift_images, invalid_drift_phases, invalid_drift_carrier or
        invalid_drift_displacements for the corresponding invalid input.
        Allocation and unrelated exceptions propagate unchanged.

    Notes
    -----
    This operation estimates no displacement. It assumes periodic specimen
    translation before stationary illumination and fixed shift-invariant
    imaging. Integer arithmetic is exact before rational-to-float64 rounding.
    Direct sine/cosine evaluation retains the meaning of huge supplied phases;
    phase increments combine through phasors rather than angle addition.
    Inputs and NumPy error mode are preserved. Finite conversion underflow is
    permitted; handled arithmetic emits no RuntimeWarning. Separate phases or
    reconstruct afterward using both returned arrays and their existing rules.
    Fractional drift, camera motion and nonperiodic borders are outside scope.
    """
    images = _plain_array(images, kinds="iuf", code="invalid_drift_images")
    if images.ndim != 3 or 0 in images.shape:
        raise SimreconError("invalid_drift_images", "images must have positive shape (N, Ny, Nx)")
    n, ny, nx = images.shape
    phases_rad = _plain_array(phases_rad, kinds="iuf", code="invalid_drift_phases")
    if phases_rad.shape != (n,):
        raise SimreconError("invalid_drift_phases", "phases must have shape (N,)")
    carrier_bins_yx = _plain_array(carrier_bins_yx, kinds="iu", code="invalid_drift_carrier")
    if carrier_bins_yx.shape != (2,):
        raise SimreconError("invalid_drift_carrier", "carrier must have shape (2,)")
    displacements_pixels_yx = _plain_array(
        displacements_pixels_yx, kinds="iu", code="invalid_drift_displacements"
    )
    if displacements_pixels_yx.shape != (n, 2):
        raise SimreconError("invalid_drift_displacements", "displacements must have shape (N, 2)")

    # Snapshot all four arguments before processing; fixed-width integers are
    # copied in their original dtype and widened individually before arithmetic.
    values = _float_snapshot(images, code="invalid_drift_images")
    phases = _float_snapshot(phases_rad, code="invalid_drift_phases")
    carrier = carrier_bins_yx.copy()
    displacements = displacements_pixels_yx.copy()
    ky, kx = (int(v) for v in carrier)
    period = ny * nx
    increments = np.empty(n, dtype=np.float64)
    aligned = np.empty(values.shape, dtype=np.float64)
    for p, displacement in enumerate(displacements):
        dy, dx = (int(v) for v in displacement)
        aligned[p] = np.roll(values[p], (-(dy % ny), -(dx % nx)), axis=(0, 1))
        residue = (ky * dy * nx + kx * dx * ny) % period
        # Python integer division rounds the exact ratio once to float64.
        # A ratio rounding to 1.0 is valid and must not be wrapped again.
        increments[p] = (2 * np.pi) * (residue / period)

    with np.errstate(all="ignore"):
        a, b = np.cos(phases), np.sin(phases)
        c, d = np.cos(increments), np.sin(increments)
        # atan2 gives the normalized product's angle without needing to divide
        # by its near-unit magnitude. Products cannot overflow.
        corrected_phases = np.arctan2(a * d + b * c, a * c - b * d)
    return DriftCorrection(aligned, corrected_phases)
