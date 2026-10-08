"""Separate two known phase harmonics independently at each volume voxel."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class VolumePhaseComponents:
    """Observed-volume phase coefficients with frozen bindings and mutable arrays.

    Attributes
    ----------
    dc : numpy.ndarray
        Independently owned native C-contiguous float64 array of shape (z, y, x).
    c1 : numpy.ndarray
        Independently owned native C-contiguous complex128 first-harmonic
        coefficient of exp(+i*phase), of shape (z, y, x).
    c2 : numpy.ndarray
        Independently owned native C-contiguous complex128 second-harmonic
        coefficient of exp(+2i*phase), of shape (z, y, x).
    """

    dc: npt.NDArray[np.float64]
    c1: npt.NDArray[np.complex128]
    c2: npt.NDArray[np.complex128]


def _snapshot(
    array: npt.NDArray[np.generic], *, dtype_code: str, finite_code: str
) -> npt.NDArray[np.float64]:
    """Copy real input, allowing finite float64 rounding and underflow."""
    with np.errstate(all="ignore"):
        if not np.isfinite(array).all():
            raise SimreconError(finite_code, "source values must be finite")
        try:
            values = array.astype(np.float64, order="C", copy=True)
        except (TypeError, ValueError, OverflowError) as error:
            raise SimreconError(dtype_code, "values cannot be converted to float64") from error
        if not np.isfinite(values).all():
            raise SimreconError(finite_code, "converted values must be finite")
    return values


def separate_volume_phases(
    images: npt.NDArray[np.generic], *, phases_rad: npt.NDArray[np.generic]
) -> VolumePhaseComponents:
    """Fit DC and two phase harmonics to an acquisition volume.

    Parameters
    ----------
    images : numpy.ndarray
        Plain real integer or floating array of shape (N, z, y, x), with N >= 5
        and positive spatial dimensions. Source and converted float64 values
        must be finite. Strided, read-only and either byte-order storage work.
    phases_rad : numpy.ndarray
        Required keyword-only plain real integer or floating array of shape
        (N,), giving the known fundamental phases in radians for all voxels.
        Source and converted float64 values must be finite.

    Returns
    -------
    VolumePhaseComponents
        Owned mutable dc, c1 and c2 arrays at the input sampling and intensity
        units. For I=A+B1*cos(phi)+C1*sin(phi)+B2*cos(2*phi)+C2*sin(2*phi),
        dc=A, c1=(B1-i*C1)/2 and c2=(B2-i*C2)/2. Negative orders are conjugates.

    Raises
    ------
    SimreconError
        If an input violates the contract, the represented matrix lacks rank
        five, the numerical solver fails, or a final real coordinate overflows.

    Notes
    -----
    Both inputs are snapshotted before numerical processing. The represented
    second harmonic uses c*c-s*s and (2*c)*s, where c=cos(phi), s=sin(phi),
    without angle reduction or doubling. Float64 SVD supplies the unweighted
    least-squares fit and strict cutoff eps*max(N,5)*s_max; no additional
    conditioning rejection or regularization applies. Off-model observations
    can have nonzero residuals, and dc need not equal the image mean.

    Each voxel has its own binary scale. Harmonic coordinates are halved before
    restoring that scale, and complex arrays are filled by real coordinates.
    This protects safely finite coordinates even when unhalved coefficients or
    complex magnitudes exceed float64 range. Underflow is permitted. Inputs and
    the caller's NumPy error mode are preserved. These observed-volume phase
    harmonics do not constitute specimen reconstruction or axial-order recovery.
    """
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_volume_phase_images", "images must be a plain NumPy ndarray")
    if images.dtype.kind not in "iuf":
        raise SimreconError("invalid_volume_phase_dtype", "images must have a real numeric dtype")
    if images.ndim != 4 or images.shape[0] < 5 or 0 in images.shape[1:]:
        raise SimreconError(
            "invalid_volume_phase_shape",
            "images must have shape (N >= 5, positive_z, positive_y, positive_x)",
        )
    if type(phases_rad) is not np.ndarray:
        raise SimreconError("invalid_volume_phase_angles", "phases must be a plain NumPy ndarray")
    if phases_rad.dtype.kind not in "iuf":
        raise SimreconError(
            "invalid_volume_phase_angles_dtype", "phases must have a real numeric dtype"
        )
    if phases_rad.shape != (images.shape[0],):
        raise SimreconError("invalid_volume_phase_angles_shape", "phases must have shape (N,)")

    values = _snapshot(
        images, dtype_code="invalid_volume_phase_dtype", finite_code="nonfinite_volume_phase_images"
    )
    angles = _snapshot(
        phases_rad,
        dtype_code="invalid_volume_phase_angles_dtype",
        finite_code="nonfinite_volume_phase_angles",
    )
    with np.errstate(all="ignore"):
        c = np.cos(angles)
        s = np.sin(angles)
        h = np.column_stack((np.ones(angles.size), c, s, c * c - s * s, (2 * c) * s))
        try:
            u, singular, vh = np.linalg.svd(h, full_matrices=False)
        except np.linalg.LinAlgError as error:
            raise SimreconError(
                "volume_phase_solver_failure", "phase SVD did not converge"
            ) from error
        if not (np.isfinite(u).all() & np.isfinite(singular).all() & np.isfinite(vh).all()):
            raise SimreconError(
                "volume_phase_solver_failure", "phase SVD returned nonfinite factors"
            )
        cutoff = np.finfo(np.float64).eps * max(angles.size, 5) * singular[0]
        if np.count_nonzero(singular > cutoff) < 5:
            raise SimreconError(
                "rank_deficient_volume_phases", "phase matrix has numerical rank below five"
            )

        # frexp gives exponent zero for zero, and handles subnormal-only voxels.
        _, exponent = np.frexp(np.max(np.abs(values), axis=0))
        scaled = np.ldexp(values, -exponent).reshape(angles.size, -1)
        try:
            coefficients = vh.T @ ((u.T @ scaled) / singular[:, None])
        except np.linalg.LinAlgError as error:
            raise SimreconError("volume_phase_solver_failure", "phase fit failed") from error
        shape = values.shape[1:]
        dc = np.array(np.ldexp(coefficients[0].reshape(shape), exponent), order="C", copy=True)
        c1 = np.empty(shape, dtype=np.complex128)
        c2 = np.empty(shape, dtype=np.complex128)
        c1.real = np.ldexp((coefficients[1] * 0.5).reshape(shape), exponent)
        c1.imag = np.ldexp((coefficients[2] * -0.5).reshape(shape), exponent)
        c2.real = np.ldexp((coefficients[3] * 0.5).reshape(shape), exponent)
        c2.imag = np.ldexp((coefficients[4] * -0.5).reshape(shape), exponent)
        if not (np.isfinite(dc).all() & np.isfinite(c1).all() & np.isfinite(c2).all()):
            raise SimreconError(
                "unrepresentable_volume_phase_components",
                "final phase coefficient coordinates overflow",
            )
    return VolumePhaseComponents(dc, c1, c2)
