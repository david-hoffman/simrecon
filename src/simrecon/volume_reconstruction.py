"""Recombine known five-order volume measurements on a signed output window."""

import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from ._volume_phase import separate_volume_phases

_RANGE = "unrepresentable_volume_reconstruction"
_GRID = "unrepresentable_volume_reconstruction_grid"
_OTFS = "invalid_volume_reconstruction_otfs"


@dataclass(frozen=True)
class Reconstruction3D:
    """Complex reconstruction with frozen fields and independently mutable arrays.

    Attributes
    ----------
    volume : numpy.ndarray
        Owned native complex128 spatial samples, with origin at index zero.
    spectrum : numpy.ndarray
        Owned native complex128 centered, masked Fourier coefficients.
    fz_per_um, fy_per_um, fx_per_um : numpy.ndarray
        Owned native float64 centered axes, in cycles per micrometre.
    voxel_size_um : tuple of float
        Output z/y/x spacings in micrometres, preserving the input field of view.

    Notes
    -----
    Direct construction performs no validation. Array contents remain mutable.
    """

    volume: npt.NDArray[np.complex128]
    spectrum: npt.NDArray[np.complex128]
    fz_per_um: npt.NDArray[np.float64]
    fy_per_um: npt.NDArray[np.float64]
    fx_per_um: npt.NDArray[np.float64]
    voxel_size_um: tuple[float, float, float]


def _real_scalar(value: object, code: str) -> float:
    """Convert only a nonboolean Python or NumPy real scalar."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "a real nonboolean scalar is required")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "scalar conversion failed") from error
    if not np.isfinite(result):
        raise SimreconError(code, "converted scalar must be finite")
    return result


def _integer(value: object, code: str) -> int:
    """Accept integer scalars without rounding or modular reduction."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise SimreconError(code, "a nonboolean integer is required")
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "integer conversion failed") from error


def _container(value: Any, count: int, code: str) -> Any:
    """Check an exact tuple or list of the required length."""
    if type(value) not in (tuple, list) or len(value) != count:
        raise SimreconError(code, "an exact tuple or list of the required length is needed")
    return value


def _real_array(
    value: Any, shape: tuple[int, ...], code: str, finite_code: str
) -> npt.NDArray[np.float64]:
    """Validate source values and take an independent native float64 snapshot."""
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf" or value.shape != shape:
        raise SimreconError(code, "a plain real ndarray of the required shape is needed")
    if not np.isfinite(value).all():
        raise SimreconError(finite_code, "source values must be finite")
    try:
        result = value.astype(np.float64, order="C", copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "array conversion failed") from error
    if not np.isfinite(result).all():
        raise SimreconError(finite_code, "converted values must be finite")
    return result


def _ordered(vector: npt.NDArray[np.float64], code: str) -> None:
    """Require a finite noncollapsed centered frequency vector."""
    middle = vector.size // 2
    if (
        not np.isfinite(vector).all()
        or vector[middle] != 0
        or not np.all(vector[1:] > vector[:-1])
        or np.any(vector[:middle] == 0)
        or np.any(vector[middle + 1 :] == 0)
    ):
        raise SimreconError(code, "frequency coordinates must be finite and strictly ordered")


def _frequencies(length: int, detector_length: int, spacing: float) -> npt.NDArray[np.float64]:
    """Round exact coordinate ratios without overflowing a field-length product."""
    field = detector_length * Fraction(spacing)
    try:
        result = np.array(
            [float(Fraction(k) / field) for k in range(-(length // 2), (length + 1) // 2)],
            dtype=np.float64,
        )
    except OverflowError as error:
        raise SimreconError(_GRID, "output frequency cannot be represented") from error
    _ordered(result, _GRID)
    return result


def _calibration(
    record: Any, shape: tuple[int, int, int]
) -> tuple[npt.NDArray[np.complex128], tuple[float, float, float]]:
    """Validate every directly constructed calibration field before computation."""
    if not isinstance(record, VolumeOrderOtf):
        raise SimreconError(_OTFS, "each calibration must be a VolumeOrderOtf")
    values = record.values
    if (
        type(values) is not np.ndarray
        or values.dtype.kind != "c"
        or values.dtype.itemsize != 16
        or values.shape != (3, *shape)
        or not np.isfinite(values).all()
    ):
        raise SimreconError(_OTFS, "calibration values must be finite complex128 on the detector")
    copied = values.astype(np.complex128, order="C", copy=True)
    dz, dy, dx = (_real_scalar(v, _OTFS) for v in _container(record.voxel_size_um, 3, _OTFS))
    spacing = (dz, dy, dx)
    if any(d <= 0 for d in spacing):
        raise SimreconError(_OTFS, "voxel spacings must be positive")
    origin = _container(record.origin_zyx, 3, _OTFS)
    for v, length in zip(origin, shape, strict=True):
        if not 0 <= _integer(v, _OTFS) < length:
            raise SimreconError(_OTFS, "origin must be in bounds")
    if not isinstance(record.source, str) or not record.source.strip():
        raise SimreconError(_OTFS, "source must be a nonblank string")
    for vector, length, d in zip(
        (record.fz_per_um, record.fy_per_um, record.fx_per_um), shape, spacing, strict=True
    ):
        if (
            type(vector) is not np.ndarray
            or vector.dtype.kind != "f"
            or vector.dtype.itemsize != 8
            or vector.shape != (length,)
        ):
            raise SimreconError(_OTFS, "calibration frequencies must be float64 vectors")
        snapshot = vector.astype(np.float64, order="C", copy=True)
        _ordered(snapshot, _OTFS)
        field = length * Fraction(d)
        for value, k in zip(snapshot, range(-(length // 2), (length + 1) // 2), strict=True):
            exact = Fraction(k) / field
            budget = Fraction(8, 2**52) * abs(exact) + Fraction(1, 2**1074)
            if abs(Fraction(float(value)) - exact) > budget:
                raise SimreconError(_OTFS, "calibration frequency is outside the canonical budget")
    return copied, spacing


def _finite(value: npt.NDArray[Any]) -> None:
    """Reject a nonfinite operational estimator or restoration stage."""
    if not np.isfinite(value).all():
        raise SimreconError(_RANGE, "computed stage is outside finite float64 range")


def _transform(
    band: npt.NDArray[np.float64] | npt.NDArray[np.complex128], *, inverse: bool
) -> npt.NDArray[np.complex128]:
    """Scale real coordinates before FFT sums, then restore each component."""
    maximum = max(float(np.max(np.abs(band.real))), float(np.max(np.abs(band.imag))))
    # Binary scaling also preserves subnormal-only bands without a tiny divisor.
    exponent = int(np.frexp(maximum)[1]) if maximum else 0
    scaled = np.empty(band.shape, dtype=np.complex128)
    scaled.real = np.ldexp(band.real, -exponent)
    scaled.imag = np.ldexp(band.imag, -exponent)
    code = "volume_reconstruction_transform_failure"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            if inverse:
                normalized = np.fft.ifftn(np.fft.ifftshift(scaled), axes=(0, 1, 2), norm="forward")
            else:
                normalized = np.fft.fftshift(np.fft.fftn(scaled, axes=(0, 1, 2), norm="forward"))
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical FFT execution failed") from error
    if not np.isfinite(normalized).all():
        raise SimreconError(code, "FFT returned nonfinite normalized coordinates")
    result = np.empty(band.shape, dtype=np.complex128)
    result.real = np.ldexp(normalized.real, exponent)
    result.imag = np.ldexp(normalized.imag, exponent)
    _finite(result)
    return result


def reconstruct_volume(
    images: npt.NDArray[Any],
    *,
    order_otfs: tuple[VolumeOrderOtf, ...] | list[VolumeOrderOtf],
    phases_rad: npt.NDArray[Any],
    carriers_bins: npt.NDArray[Any],
    gains: npt.NDArray[Any],
    regularization: object,
    output_shape_yx: object,
    apodization: npt.NDArray[Any],
) -> Reconstruction3D:
    """Separate and combine five known orders on an explicit signed volume grid.

    Parameters
    ----------
    images : numpy.ndarray
        Plain finite real array (R,N,Nz,Ny,Nx), R >= 1 and N >= 5.
    order_otfs : tuple or list of VolumeOrderOtf
        Fully validated complex transfers for orders 0,+1,+2 per orientation.
    phases_rad : numpy.ndarray
        Plain finite real array (R,N) of known fundamental phases in radians.
    carriers_bins : numpy.ndarray
        Plain integer array (R,2) of exact signed y/x detector-bin carriers.
    gains : numpy.ndarray
        Plain real array (R,) of finite positive converted gains.
    regularization : real scalar
        Explicit finite nonnegative ridge, in squared-transfer units.
    output_shape_yx : tuple or list of int
        Complete positive lateral window, at least detector size plus four
        times each axis's largest absolute carrier.
    apodization : numpy.ndarray
        Plain real amplitude mask (Nz,Ly,Lx), with finite values in [0,1].

    Returns
    -------
    Reconstruction3D
        Complex volume and centered masked spectrum in image intensity units,
        with independent mutable arrays and field-of-view-preserving coordinates.

    Raises
    ------
    SimreconError
        If validation, grid representation, FFT execution or an operational
        arithmetic stage fails. Prerequisite phase errors propagate unchanged.

    Notes
    -----
    All inputs are snapshotted before separation or transforms. Negative orders
    use modular detector negation on all axes. Lateral placement never wraps.
    Native z and the single signed even-Nyquist coefficient are preserved.
    Gains enter transfers once; synthesis has no output-count division.
    A finite unmasked quotient is required before applying the mask. This is
    a finite stored-input estimator, with no general physical recovery promise.
    Caller floating and warning policies are preserved; unrelated exceptions
    and allocation failures propagate.
    """
    if type(images) is not np.ndarray:
        raise SimreconError(
            "invalid_volume_reconstruction_images", "images must be a plain ndarray"
        )
    if images.dtype.kind not in "iuf":
        raise SimreconError("invalid_volume_reconstruction_dtype", "images must have real dtype")
    if images.ndim != 5 or images.shape[0] < 1 or images.shape[1] < 5 or 0 in images.shape[2:]:
        raise SimreconError("invalid_volume_reconstruction_shape", "invalid acquisition shape")
    r_count, n, nz, ny, nx = images.shape
    detector = (nz, ny, nx)
    with np.errstate(all="ignore"):
        observed = _real_array(
            images,
            images.shape,
            "invalid_volume_reconstruction_dtype",
            "nonfinite_volume_reconstruction_images",
        )
        phases = _real_array(
            phases_rad,
            (r_count, n),
            "invalid_volume_reconstruction_phases",
            "nonfinite_volume_reconstruction_phases",
        )
        gain = _real_array(
            gains,
            (r_count,),
            "invalid_volume_reconstruction_gains",
            "invalid_volume_reconstruction_gain_values",
        )
        if np.any(gain <= 0):
            raise SimreconError(
                "invalid_volume_reconstruction_gain_values", "gains must be positive"
            )
        carrier_code = "invalid_volume_reconstruction_carriers"
        if (
            type(carriers_bins) is not np.ndarray
            or carriers_bins.dtype.kind not in "iu"
            or carriers_bins.shape != (r_count, 2)
        ):
            raise SimreconError(carrier_code, "carriers must be an exact-integer ndarray (R,2)")
        carriers = [(int(y), int(x)) for y, x in carriers_bins.copy()]
        shape_code = "invalid_volume_reconstruction_output_shape"
        ly, lx = (_integer(v, shape_code) for v in _container(output_shape_yx, 2, shape_code))
        if any(v <= 0 or v > np.iinfo(np.intp).max for v in (ly, lx)):
            raise SimreconError(shape_code, "output dimensions must be positive native indices")
        if ly < ny + 4 * max(abs(y) for y, _ in carriers) or lx < nx + 4 * max(
            abs(x) for _, x in carriers
        ):
            raise SimreconError(shape_code, "output window must retain every signed order")
        penalty_code = "invalid_volume_reconstruction_regularization"
        penalty = _real_scalar(regularization, penalty_code)
        if penalty < 0:
            raise SimreconError(penalty_code, "regularization must be nonnegative")
        output = (nz, ly, lx)
        mask_code = "invalid_volume_reconstruction_apodization_values"
        mask = _real_array(
            apodization, output, "invalid_volume_reconstruction_apodization", mask_code
        )
        if (
            np.any(apodization < 0)
            or np.any(apodization > 1)
            or np.any(mask < 0)
            or np.any(mask > 1)
        ):
            raise SimreconError(mask_code, "source and converted mask must be in [0,1]")
        calibrations = [
            _calibration(record, detector) for record in _container(order_otfs, r_count, _OTFS)
        ]
        spacing = calibrations[0][1]
        if any(d != spacing for _, d in calibrations):
            raise SimreconError(_OTFS, "all orientations must have identical converted spacing")
        out_spacing = tuple(
            float(Fraction(d) * k / length)
            for d, k, length in zip(spacing, detector, output, strict=True)
        )
        if any(not np.isfinite(d) or d <= 0 for d in out_spacing):
            raise SimreconError(_GRID, "output spacing must be finite and positive")
        fz, fy, fx = (
            _frequencies(length, k, d)
            for length, k, d in zip(output, detector, spacing, strict=True)
        )

        numerator = np.zeros(output, dtype=np.complex128)
        denominator = np.zeros(output, dtype=np.float64)
        negation = np.ix_(*[(2 * (k // 2) - np.arange(k)) % k for k in detector])
        for r, ((transfers, _), (cy, cx)) in enumerate(zip(calibrations, carriers, strict=True)):
            separated = separate_volume_phases(observed[r], phases_rad=phases[r])
            bands = (separated.dc, separated.c1, separated.c2)
            for m in (-2, -1, 0, 1, 2):
                band = bands[abs(m)]
                transfer = transfers[abs(m)]
                if m < 0:
                    band = np.conj(band)
                    transfer = np.conj(transfer[negation])
                coefficients = _transform(band, inverse=False)
                t = transfer * gain[r]
                _finite(t)
                weight = t.real * t.real + t.imag * t.imag
                _finite(weight)
                contribution = np.conj(t) * coefficients
                _finite(contribution)
                y0 = ly // 2 - ny // 2 - m * cy
                x0 = lx // 2 - nx // 2 - m * cx
                window = (slice(None), slice(y0, y0 + ny), slice(x0, x0 + nx))
                numerator[window] += contribution
                denominator[window] += weight
                _finite(numerator[window])
                _finite(denominator[window])
        denominator += penalty
        _finite(denominator)
        quotient = np.zeros(output, dtype=np.complex128)
        np.divide(numerator.real, denominator, out=quotient.real, where=denominator > 0)
        np.divide(numerator.imag, denominator, out=quotient.imag, where=denominator > 0)
        _finite(quotient)
        spectrum = np.empty(output, dtype=np.complex128)
        spectrum.real = quotient.real * mask
        spectrum.imag = quotient.imag * mask
        _finite(spectrum)
        volume = _transform(spectrum, inverse=True)
    return Reconstruction3D(
        volume, spectrum, fz, fy, fx, (out_spacing[0], out_spacing[1], out_spacing[2])
    )
