"""Prepare signed bead-referenced responses from separated observed volumes."""

import warnings
from dataclasses import dataclass
from fractions import Fraction

import numpy as np
import numpy.typing as npt

from ._bead_peak import locate_bead_peak
from ._model import SimreconError
from ._volume_otf import _frequencies, _spacing, _triple


@dataclass(frozen=True)
class EmpiricalVolumeResponse:
    """Relative observed responses with frozen bindings and mutable arrays.

    Attributes
    ----------
    values : numpy.ndarray
        Owned native C-contiguous complex128 array, ordered 0,+1,+2 then
        full centered z/y/x frequencies. Values are dimensionless.
    fz_per_um, fy_per_um, fx_per_um : numpy.ndarray
        Independently owned native float64 axes in cycles/micrometre.
    voxel_size_um : tuple of float
        Converted z/y/x spacings in micrometres.
    origin_zyx : tuple of int
        Sole positive maximum of the converted observed zero-order volume.

    Notes
    -----
    Direct construction performs no validation. Array contents remain writable.
    """

    values: npt.NDArray[np.complex128]
    fz_per_um: npt.NDArray[np.float64]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    voxel_size_um: tuple[float, float, float]
    origin_zyx: tuple[int, int, int]


def _snapshot(
    array: npt.NDArray[np.generic], *, real: bool
) -> npt.NDArray[np.float64 | np.complex128]:
    """Validate source components and independently copy their converted values."""
    code = "nonfinite_empirical_response_array"
    if not np.isfinite(array).all():
        raise SimreconError(code, "source components must be finite")
    try:
        snapshot = array.astype(np.float64 if real else np.complex128, order="C", copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "component conversion failed") from error
    if not np.isfinite(snapshot).all():
        raise SimreconError(code, "converted components must be finite")
    return snapshot


def _restore(component: float, scale: Fraction) -> float:
    """Round the exact transformed-component times gain over mass just once."""
    if component == 0:
        return component
    try:
        return float(Fraction.from_float(component) * scale)
    except OverflowError as error:
        raise SimreconError(
            "unrepresentable_empirical_response", "final rescaled component is nonfinite"
        ) from error


def prepare_empirical_volume_response(
    dc: npt.NDArray[np.generic],
    *,
    c1: npt.NDArray[np.generic],
    c2: npt.NDArray[np.generic],
    voxel_size_um: object,
) -> EmpiricalVolumeResponse:
    """Center and commonly normalize signed separated observed volume harmonics.

    Parameters
    ----------
    dc : numpy.ndarray
        Plain real integer or floating zero-order volume, in z/y/x order.
        Converted binary64 samples must have a unique positive maximum and
        a strictly positive exact sum. Signed samples are allowed.
    c1, c2 : numpy.ndarray
        Required plain real or complex numeric volumes of the same positive
        three-dimensional shape and intensity unit as dc. Finite source and
        converted real/imaginary components are required for all three inputs.
    voxel_size_um : tuple, list or numpy.ndarray
        Required three finite positive real nonboolean z/y/x spacings,
        individually converted to binary64, in micrometres.

    Returns
    -------
    EmpiricalVolumeResponse
        Owned full complex responses 0,+1,+2 with centered frequency axes.
        Every order uses the observed dc peak and exact converted dc mass.
        Zero-order DC is exactly one; relative side gains and phase remain.

    Raises
    ------
    SimreconError
        On invalid representation, absent/ambiguous positive peak, nonpositive
        exact mass, unrepresentable frequencies, handled transform failure or
        nonfinite final rescaled components. Allocation failures and unrelated
        dependency exceptions propagate unchanged.

    Notes
    -----
    Snapshots precede numerical processing. Separate componentwise binary64
    gain division supplies public NumPy backward-normalized forward transforms
    on all spatial axes. Exact rational restoration avoids intermediate scale,
    product and mass range restrictions. No conditioning threshold is applied.
    Inputs, caller NumPy modes and unrelated warning categories are preserved.

    The response describes a finite periodic native grid, loses common intensity
    scale and retains bead/separation phase gauge. It infers neither absolute
    throughput nor a physical model's validity. Full snapshots, scratch, output
    and exact arithmetic bookkeeping are owned; no working-set or performance
    bound, streaming, provenance or file I/O is promised.
    """
    arrays = (dc, c1, c2)
    for order, array in enumerate(arrays):
        if type(array) is not np.ndarray:
            raise SimreconError(
                "invalid_empirical_response_array", "components must be plain arrays"
            )
        if array.dtype.kind not in ("iuf" if order == 0 else "iufc"):
            raise SimreconError("invalid_empirical_response_dtype", "unsupported component dtype")
        if array.ndim != 3 or 0 in array.shape or array.shape != dc.shape:
            raise SimreconError(
                "invalid_empirical_response_shape", "components require equal positive z/y/x shapes"
            )

    with np.errstate(all="ignore"):
        a0 = _snapshot(dc, real=True)
        a1 = _snapshot(c1, real=False)
        a2 = _snapshot(c2, real=False)
        origin = locate_bead_peak(a0).index_zyx
        mass = sum((Fraction.from_float(float(v)) for v in a0.flat), Fraction())
        if mass <= 0:
            raise SimreconError(
                "nonpositive_empirical_response_mass", "exact dc mass must be positive"
            )

        dz, dy, dx = (_spacing(v) for v in _triple(voxel_size_um, "invalid_otf_voxel_size"))
        fz = _frequencies(dc.shape[0], dz)
        fy = _frequencies(dc.shape[1], dy)
        fx = _frequencies(dc.shape[2], dx)
        values = np.empty((3, *dc.shape), dtype=np.complex128)
        for order, snapshot in enumerate((a0, a1, a2)):
            gain = float(max(np.max(np.abs(snapshot.real)), np.max(np.abs(snapshot.imag)))) or 1.0
            scaled = np.empty(snapshot.shape, dtype=np.complex128)
            scaled.real = snapshot.real / gain
            scaled.imag = snapshot.imag / gain
            rolled = np.roll(scaled, tuple(-o for o in origin), axis=(0, 1, 2))
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    transformed = np.fft.fftn(rolled, axes=(0, 1, 2), norm="backward")
            except (FloatingPointError, OverflowError, RuntimeWarning) as error:
                raise SimreconError(
                    "empirical_response_transform_failure", "numerical transform failure"
                ) from error
            # Even a nonfinite zero-order DC is a transform failure. Only after
            # whole-transform validation may its exact identity replace it.
            if not np.isfinite(transformed).all():
                raise SimreconError(
                    "empirical_response_transform_failure", "scaled transform must be finite"
                )
            scale = Fraction.from_float(gain) / mass
            for index in np.ndindex(snapshot.shape):
                if order == 0 and index == (0, 0, 0):
                    values[(order, *index)] = 1 + 0j
                else:
                    component = transformed[index]
                    values[(order, *index)] = complex(
                        _restore(float(component.real), scale),
                        _restore(float(component.imag), scale),
                    )
        values = np.array(np.fft.fftshift(values, axes=(1, 2, 3)), order="C", copy=True)
    return EmpiricalVolumeResponse(values, fz, fy, fx, (dz, dy, dx), origin)
