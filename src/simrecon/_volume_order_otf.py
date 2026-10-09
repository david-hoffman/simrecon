"""Prepare finite effective volume transfers for supplied axial profiles."""

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_otf import _prepare_volume_inputs


@dataclass(frozen=True)
class VolumeOrderOtf:
    """Three signed complex transfers with frozen bindings and mutable arrays.

    Attributes
    ----------
    values : numpy.ndarray
        Independently owned native complex128 array, ordered 0,+1,+2 then
        full centered z/y/x frequencies, with C-contiguous writable storage.
    fz_per_um, fy_per_um, fx_per_um : numpy.ndarray
        Separately owned native float64 axes in cycles/micrometre.
    voxel_size_um : tuple of float
        Converted z/y/x sampling in micrometres.
    origin_zyx : tuple of int
        Explicit zero-displacement sample coordinates.
    source : str
        Unchanged caller label, without provenance verification.

    Notes
    -----
    Direct construction performs no validation. Array contents remain mutable.
    """

    values: npt.NDArray[np.complex128]
    fz_per_um: npt.NDArray[np.float64]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    voxel_size_um: tuple[float, float, float]
    origin_zyx: tuple[int, int, int]
    source: str


def _coefficients(value: npt.NDArray[Any], nz: int) -> npt.NDArray[np.complex128]:
    """Snapshot finite real and imaginary components without magnitude tests."""
    if type(value) is not np.ndarray:
        raise SimreconError(
            "invalid_volume_order_coefficients", "coefficients must be a plain ndarray"
        )
    if value.dtype.kind not in "iufc":
        raise SimreconError(
            "invalid_volume_order_coefficients_dtype", "coefficients must have numeric dtype"
        )
    if value.shape != (2, nz):
        raise SimreconError(
            "invalid_volume_order_coefficients_shape", "coefficients must have shape (2,Nz)"
        )
    code = "nonfinite_volume_order_coefficients"
    if not np.isfinite(value).all():
        raise SimreconError(code, "source coefficient components must be finite")
    try:
        snapshot = value.astype(np.complex128, order="C", copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "coefficient conversion failed") from error
    if not np.isfinite(snapshot).all():
        raise SimreconError(code, "converted coefficient components must be finite")
    return snapshot


def prepare_volume_order_otfs(
    psf: npt.NDArray[Any],
    *,
    axial_coefficients: npt.NDArray[Any],
    voxel_size_um: object,
    origin_zyx: object,
    source: str,
) -> VolumeOrderOtf:
    """Prepare orders 0,+1,+2 from detection mass and axial displacement rows.

    Parameters
    ----------
    psf : numpy.ndarray
        Plain finite nonnegative real z/y/x intensity volume. Its independent
        float64 snapshot must have positive mass.
    axial_coefficients : numpy.ndarray
        Plain numeric array (2,Nz) supplying complex g1 and g2 in the PSF's
        displacement frame. Finite components are copied to complex128.
    voxel_size_um : tuple, list or numpy.ndarray
        Required finite positive real z/y/x sampling in micrometres.
    origin_zyx : tuple, list or numpy.ndarray
        Required in-bounds integer zero-displacement coordinates.
    source : str
        Required nonblank opaque caller label, retained unchanged.

    Returns
    -------
    VolumeOrderOtf
        Full centered negative-sign discrete transforms of p, p*g1 and p*g2,
        where p is detection mass normalized once. Side gain and phase remain.
        All four arrays independently own writable storage.

    Raises
    ------
    SimreconError
        On invalid representations, unrepresentable frequency grids, handled
        transform failures or nonfinite final rescaling. MemoryError and
        unrelated exceptions propagate unchanged.

    Notes
    -----
    This finite periodic algebra estimates no physical calibration. Effective
    kernel interpretation requires profiles fixed relative to the focal plane
    during scanning. Arbitrary finite profiles remain valid algebraic inputs.
    Componentwise scaling permits finite gains with overflowing magnitude.
    Absolute numerical budgets permit loss of tiny contributions. Caller
    floating-error and warning policies and all inputs are preserved.
    """
    with np.errstate(all="ignore"):
        mass, (fz, fy, fx), spacing, origin = _prepare_volume_inputs(
            psf, voxel_size_um, origin_zyx, source
        )
        coefficients = _coefficients(axial_coefficients, mass.shape[0])
        values = np.empty((3, *mass.shape), dtype=np.complex128)
        for order in range(3):
            gain = 1.0
            if order == 0:
                kernel = mass
            else:
                row = coefficients[order - 1]
                gain = float(max(np.max(np.abs(row.real)), np.max(np.abs(row.imag)))) or 1.0
                scaled = np.empty(row.shape, dtype=np.complex128)
                scaled.real = row.real / gain
                scaled.imag = row.imag / gain
                kernel = mass * scaled[:, None, None]
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    rolled = np.roll(kernel, tuple(-o for o in origin), axis=(0, 1, 2))
                    transformed = np.fft.fftshift(np.fft.fftn(rolled, axes=(0, 1, 2)))
            except (FloatingPointError, OverflowError, RuntimeWarning) as error:
                raise SimreconError(
                    "volume_order_transform_failure", "numerical transform failure"
                ) from error
            if not np.isfinite(transformed).all():
                raise SimreconError(
                    "volume_order_transform_failure",
                    "normalized transform returned nonfinite values",
                )
            values[order].real = transformed.real * gain
            values[order].imag = transformed.imag * gain
            if not np.isfinite(values[order]).all():
                raise SimreconError(
                    "unrepresentable_volume_order_otf", "final rescaling returned nonfinite values"
                )
    return VolumeOrderOtf(values, fz, fy, fx, spacing, origin, source)
