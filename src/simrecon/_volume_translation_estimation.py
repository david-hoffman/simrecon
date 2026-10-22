"""Full periodic integer-voxel mismatch against a supplied comparable volume."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._array_validation import conversion_errors, require_finite
from ._model import SimreconError
from ._translation import _tolerance


@dataclass(frozen=True)
class VolumeTranslationEstimate:
    """Complete mismatch surface and caller-defined translation ambiguity.

    Attributes
    ----------
    normalized_rms : numpy.ndarray
        Independently owned mutable native float64 C-contiguous array of shape
        (Nz, Ny, Nx), ordered by increasing canonical signed z/y/x shifts.
    minimum_normalized_rms : float
        Actual minimum entry of the dimensionless root mean square surface.
    candidate_displacements_voxels_zyx : tuple of tuple of int
        All canonical content-motion triples whose score minus the actual
        minimum is at most the caller tolerance, in increasing z/y/x order.
    displacement_voxels_zyx : tuple of int or None
        Sole qualifying triple, otherwise None. Alignment uses its negative.
    failure_code : str or None
        ambiguous_volume_translation for multiple candidates, otherwise None.
        Uniqueness supplies no physical-motion or fit-acceptance guarantee.
    """

    normalized_rms: npt.NDArray[np.float64]
    minimum_normalized_rms: float
    candidate_displacements_voxels_zyx: tuple[tuple[int, int, int], ...]
    displacement_voxels_zyx: tuple[int, int, int] | None
    failure_code: str | None


def _volume_snapshot(value: object) -> npt.NDArray[np.float64]:
    """Validate source finiteness and own a converted float64 snapshot."""
    code = "invalid_volume_translation_images"
    if (
        type(value) is not np.ndarray
        or value.dtype.kind not in "iuf"
        or value.ndim != 3
        or value.size == 0
    ):
        raise SimreconError(code, "volumes must be plain nonempty real three-dimensional arrays")
    require_finite(value, code, "source volumes must be finite")
    with conversion_errors(code, "volume cannot convert to float64"), np.errstate(all="ignore"):
        snapshot = np.array(value, dtype=np.float64, order="C", copy=True)
    require_finite(snapshot, code, "converted volumes must be finite")
    return snapshot


def estimate_volume_translation(
    moving: npt.NDArray[Any],
    *,
    reference: npt.NDArray[Any],
    ambiguity_tolerance: object,
) -> VolumeTranslationEstimate:
    """Estimate periodic integer content motion against an equal-intensity volume.

    Parameters
    ----------
    moving : numpy.ndarray
        Plain finite real nonempty volume, shape (Nz, Ny, Nx). Real integer
        and floating dtypes, either endian and arbitrary strides are accepted.
        Values must remain finite after float64 conversion. Rounding and
        underflow are permitted; caller storage is preserved.
    reference : numpy.ndarray
        Required comparable volume with the same shape and representation rules.
    ambiguity_tolerance : int, float or numpy.ndarray
        Required nonboolean Python/NumPy real scalar or plain real 0D array.
        Source and float64 values must be finite and nonnegative, with no cap.
        Inclusive allowance above this call's actual minimum normalized RMS.

    Returns
    -------
    VolumeTranslationEstimate
        Full all-voxel root mean square (RMS) surface and qualifying z/y/x
        content-motion triples in voxels. Each length D axis uses canonical
        shifts -floor(D/2) through ceil(D/2)-1. Multiple candidates are ambiguous.

    Raises
    ------
    SimreconError
        invalid_volume_translation_images for invalid images/conversion;
        incompatible_volume_translation_shape for unequal valid shapes;
        invalid_volume_translation_tolerance for invalid tolerance.
        MemoryError and unrelated exceptions propagate unchanged.

    Notes
    -----
    Snapshot both volumes, divide by their common maximum absolute value B,
    and evaluate RMS differences directly at every periodic shift using all
    voxels. B=0 gives an all-zero surface. No gain/background fit, independent
    normalization, masking or interpolation is applied. Content motion
    (dz, dy, dx) aligns with roll(-dz, -dy, -dx).

    For P voxels, direct evaluation costs O(P squared) work and O(P) working
    storage. Use modest volumes. Numerical uniqueness establishes neither
    physical motion nor model adequacy. Different raw illumination phases need
    not satisfy the supplied comparable-reference model. NumPy error mode and
    unrelated warnings are preserved.
    """
    tolerance = _tolerance(ambiguity_tolerance, code="invalid_volume_translation_tolerance")
    m, r = _volume_snapshot(moving), _volume_snapshot(reference)
    if m.shape != r.shape:
        raise SimreconError(
            "incompatible_volume_translation_shape", "volumes must have equal shapes"
        )

    nz, ny, nx = m.shape
    z_shifts = range(-(nz // 2), (nz + 1) // 2)
    y_shifts = range(-(ny // 2), (ny + 1) // 2)
    x_shifts = range(-(nx // 2), (nx + 1) // 2)
    surface = np.empty((nz, ny, nx), dtype=np.float64)
    with np.errstate(all="ignore"):
        scale = max(float(np.max(np.abs(m))), float(np.max(np.abs(r))))
        if scale == 0:
            surface.fill(0)
        else:
            # Direct division also handles subnormal B without reciprocal overflow.
            m /= scale
            r /= scale
            for iz, dz in enumerate(z_shifts):
                for iy, dy in enumerate(y_shifts):
                    for ix, dx in enumerate(x_shifts):
                        difference = np.roll(m, (-dz, -dy, -dx), axis=(0, 1, 2)) - r
                        surface[iz, iy, ix] = np.sqrt(np.mean(difference * difference))

    minimum = float(np.min(surface))
    candidates = tuple(
        (dz, dy, dx)
        for iz, dz in enumerate(z_shifts)
        for iy, dy in enumerate(y_shifts)
        for ix, dx in enumerate(x_shifts)
        if float(surface[iz, iy, ix]) - minimum <= tolerance
    )
    sole = len(candidates) == 1
    return VolumeTranslationEstimate(
        surface,
        minimum,
        candidates,
        candidates[0] if sole else None,
        None if sole else "ambiguous_volume_translation",
    )
