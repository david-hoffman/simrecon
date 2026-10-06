"""Fit the first harmonic at explicitly supplied image phases."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from ._model import SimreconError


@dataclass(frozen=True)
class PhaseComponents:
    """Image-space phase coefficients with independently owned mutable arrays.

    Attributes
    ----------
    dc : numpy.ndarray
        Fitted constant coefficient, a native C-contiguous float64 array of
        shape (y, x). It is not generally the arithmetic image mean.
    c1 : numpy.ndarray
        Coefficient of exp(+i*phase), a native C-contiguous complex128 array of
        shape (y, x). The negative-order coefficient is its complex conjugate.
    """

    dc: npt.NDArray[np.float64]
    c1: npt.NDArray[np.complex128]


def _as_finite_float64(
    array: npt.NDArray[np.generic], *, error_code: str, label: str
) -> npt.NDArray[np.float64]:
    """Copy a validated real array into owned finite float64 storage."""
    with np.errstate(all="ignore"):
        values = array.astype(np.float64, order="C", copy=True)
        if not (np.isfinite(array).all() & np.isfinite(values).all()):
            raise SimreconError(error_code, f"source and converted {label} must be finite")
    return values


def separate_phases(
    images: npt.NDArray[np.generic], *, phases_rad: npt.NDArray[np.generic]
) -> PhaseComponents:
    """Fit an unweighted first harmonic to three or more real phase images.

    Parameters
    ----------
    images : numpy.ndarray
        Plain real integer or floating array of shape (N, y, x), with N >= 3
        and positive spatial dimensions. Source and converted float64 values
        must be finite. Either byte order and strided or read-only storage work.
    phases_rad : numpy.ndarray
        Required keyword-only plain real integer or floating array of shape
        (N,), giving each image's known phase in radians. Source and converted
        float64 values must be finite. Angles are evaluated without reduction.

    Returns
    -------
    PhaseComponents
        Independently owned mutable dc and c1 arrays in input intensity units,
        at the acquired sampling. For I=A+B*cos(phi)+C*sin(phi), dc=A and
        c1=(B-i*C)/2. Off-model observations can have nonzero fit residuals.

    Raises
    ------
    SimreconError
        If inputs violate the domain, the represented separation matrix lacks
        numerical rank three, the numerical solver fails, or final coefficient
        coordinates cannot be stored as finite float64 values.

    Notes
    -----
    Float64 singular value decomposition supplies both the numerical rank and
    the least-squares solve. Singular values must strictly exceed eps*N*s_max;
    no additional conditioning cutoff or regularization is applied. Rank does
    not guarantee useful coefficient digits near deficiency. Per-pixel binary
    scaling protects the solve; harmonic lanes are halved before restoring
    scale. Inputs and the caller's floating-error policy are preserved.
    """
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_phase_images", "images must be a plain NumPy ndarray")
    if images.dtype.kind not in "iuf":
        raise SimreconError(
            "invalid_phase_dtype", "images must have real integer or floating dtype"
        )
    if images.ndim != 3 or images.shape[0] < 3 or 0 in images.shape[1:]:
        raise SimreconError(
            "invalid_phase_shape", "images must have shape (N >= 3, positive_y, positive_x)"
        )
    if type(phases_rad) is not np.ndarray:
        raise SimreconError("invalid_phase_angles", "phases must be a plain NumPy ndarray")
    if phases_rad.dtype.kind not in "iuf":
        raise SimreconError(
            "invalid_phase_angles_dtype", "phases must have real integer or floating dtype"
        )
    if phases_rad.shape != (images.shape[0],):
        raise SimreconError("invalid_phase_angles_shape", "phases must have shape (N,)")

    # Conversion, subnormal quantization and final overflow have explicit
    # outcomes, independent of the caller's warning and floating-error modes.
    values = _as_finite_float64(images, error_code="nonfinite_phase_images", label="images")
    angles = _as_finite_float64(phases_rad, error_code="nonfinite_phase_angles", label="phases")
    with np.errstate(all="ignore"):
        h = np.column_stack((np.ones(angles.size), np.cos(angles), np.sin(angles)))
        try:
            u, singular, vh = np.linalg.svd(h, full_matrices=False)
        except np.linalg.LinAlgError as error:
            raise SimreconError("phase_solver_failure", "phase SVD did not converge") from error
        if not (np.isfinite(u).all() & np.isfinite(singular).all() & np.isfinite(vh).all()):
            raise SimreconError("phase_solver_failure", "phase SVD returned nonfinite factors")
        cutoff = np.finfo(np.float64).eps * angles.size * singular[0]
        if np.count_nonzero(singular > cutoff) < 3:
            raise SimreconError(
                "rank_deficient_phases", "phase matrix has numerical rank below three"
            )

        # Each pixel gets its own power-of-two scale, including subnormal-only
        # pixels beside bright pixels. frexp assigns exponent zero to zero.
        _, exponent = np.frexp(np.max(np.abs(values), axis=0))
        scaled = np.ldexp(values, -exponent).reshape(angles.size, -1)
        coefficients = vh.T @ ((u.T @ scaled) / singular[:, None])
        shape = values.shape[1:]
        dc = np.array(np.ldexp(coefficients[0].reshape(shape), exponent), order="C", copy=True)
        c1 = np.empty(shape, dtype=np.complex128)
        c1.real = np.ldexp((coefficients[1] * 0.5).reshape(shape), exponent)
        c1.imag = np.ldexp((coefficients[2] * -0.5).reshape(shape), exponent)
        if not (np.isfinite(dc).all() & np.isfinite(c1).all()):
            raise SimreconError(
                "unrepresentable_phase_components", "final phase coefficient coordinates overflow"
            )
    return PhaseComponents(dc, c1)
