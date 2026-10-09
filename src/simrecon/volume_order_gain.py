"""Fit one relative complex order correction on a nonwrapping volume overlap."""

import math
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from ._volume_phase import separate_volume_phases
from .volume_reconstruction import _calibration, _integer, _real_array

_RANGE = "unrepresentable_volume_order_gain"


@dataclass(frozen=True)
class VolumeOrderGainEstimate:
    """Immutable scalar fit metadata for one caller-selected positive order.

    Attributes
    ----------
    gain : complex
        Dimensionless relative correction to the supplied selected transfer.
    relative_residual, coherence : float
        Direct normalized residual and amplitude correlation, respectively.
    overlap_count : int
        Number of geometric pairs, including zero-transfer samples.
    status : str
        ``fitted``, ``zero_response`` or ``zero_correlation``.
    order : int
        Selected positive order, one or two.
    carrier_bins_yx : tuple of int
        Exact fundamental y/x carrier in detector frequency bins.
    source : str
        Unchanged opaque calibration label, without authentication.
    """

    gain: complex
    relative_residual: float
    coherence: float
    overlap_count: int
    status: str
    order: int
    carrier_bins_yx: tuple[int, int]
    source: str


def _inputs(images: Any, steps: Any) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Snapshot phase inputs before any numerical work or caller mutation seam."""
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_volume_phase_images", "images must be a plain ndarray")
    if images.dtype.kind not in "iuf":
        raise SimreconError("invalid_volume_phase_dtype", "images must have real numeric dtype")
    if images.ndim != 4 or images.shape[0] < 5 or 0 in images.shape[1:]:
        raise SimreconError("invalid_volume_phase_shape", "invalid acquisition shape")
    if type(steps) is not np.ndarray:
        raise SimreconError("invalid_volume_phase_angles", "steps must be a plain ndarray")
    if steps.dtype.kind not in "iuf":
        raise SimreconError("invalid_volume_phase_angles_dtype", "steps must have real dtype")
    if steps.shape != (images.shape[0],):
        raise SimreconError("invalid_volume_phase_angles_shape", "steps must have shape (N,)")
    return (
        _real_array(
            images, images.shape, "invalid_volume_phase_dtype", "nonfinite_volume_phase_images"
        ),
        _real_array(
            steps, steps.shape, "invalid_volume_phase_angles_dtype", "nonfinite_volume_phase_angles"
        ),
    )


def _carrier(value: Any) -> tuple[int, int]:
    """Extract exact integers from only the approved y/x containers."""
    code = "invalid_volume_order_gain_carrier"
    if type(value) is np.ndarray:
        if value.shape != (2,) or value.dtype.kind not in "iu":
            raise SimreconError(code, "carrier must be a length-two integer vector")
        items = value.copy()
    elif type(value) in (tuple, list) and len(value) == 2:
        items = tuple(value)
    else:
        raise SimreconError(code, "carrier must be an exact tuple, list or plain integer vector")
    return _integer(items[0], code), _integer(items[1], code)


def _finite(value: Any) -> None:
    """Reject nonfinite components without inspecting complex magnitudes."""
    if not np.isfinite(value).all():
        raise SimreconError(_RANGE, "computed component is outside finite float64 range")


def _scaled(value: npt.NDArray[np.complex128]) -> tuple[npt.NDArray[np.complex128], float]:
    """Independently bound real and imaginary components of an operand."""
    maximum = max(float(np.max(np.abs(value.real))), float(np.max(np.abs(value.imag)))) or 1.0
    result = np.empty(value.shape, dtype=np.complex128)
    result.real = value.real / maximum
    result.imag = value.imag / maximum
    _finite(result)
    return result, maximum


def _transform(
    band: npt.NDArray[np.float64] | npt.NDArray[np.complex128],
) -> tuple[npt.NDArray[np.complex128], int]:
    """Retain binary band scale after a safely scaled normalized forward FFT."""
    maximum = max(float(np.max(np.abs(band.real))), float(np.max(np.abs(band.imag))))
    exponent = math.frexp(maximum)[1] if maximum else 0
    scaled = np.empty(band.shape, dtype=np.complex128)
    scaled.real = np.ldexp(band.real, -exponent)
    scaled.imag = np.ldexp(band.imag, -exponent)
    code = "volume_order_gain_transform_failure"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            transformed = np.fft.fftshift(np.fft.fftn(scaled, axes=(0, 1, 2), norm="forward"))
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical FFT execution failed") from error
    if not np.isfinite(transformed).all():
        raise SimreconError(code, "FFT returned nonfinite normalized components")
    # Keep the scale for regression, but enforce the restored-band range rule.
    _finite(np.ldexp(transformed.real, exponent))
    _finite(np.ldexp(transformed.imag, exponent))
    return transformed, exponent


def _unit(value: npt.NDArray[np.complex128]) -> tuple[npt.NDArray[np.complex128], float]:
    """Normalize a bounded product using an independently scaled norm."""
    scaled, maximum = _scaled(value)
    length = float(np.sqrt(np.sum(scaled.real * scaled.real + scaled.imag * scaled.imag)))
    _finite(length)
    if length == 0:
        return scaled, 0.0
    unit = scaled / length
    norm = maximum * length
    _finite(unit)
    _finite(norm)
    return unit, norm


def _restore(
    component: float, numerator: tuple[float, ...], denominator: tuple[float, ...], exponent: int
) -> float:
    """Include correlation before restoring a gain component's binary scale."""
    if component == 0:
        return component
    mantissa, power = math.frexp(component)
    exponent += power
    for factor in numerator:
        fraction, power = math.frexp(factor)
        mantissa *= fraction
        exponent += power
    for factor in denominator:
        fraction, power = math.frexp(factor)
        mantissa /= fraction
        exponent -= power
    try:
        result = math.ldexp(mantissa, exponent)
    except OverflowError as error:
        raise SimreconError(_RANGE, "restored gain component overflows") from error
    _finite(result)
    return result


def estimate_volume_order_gain(
    images: npt.NDArray[Any],
    *,
    order_otf: VolumeOrderOtf,
    phase_steps_rad: npt.NDArray[Any],
    carrier_bins_yx: object,
    order: object,
) -> VolumeOrderGainEstimate:
    """Estimate one cross-weighted relative complex transfer correction.

    Parameters
    ----------
    images : numpy.ndarray
        Plain finite real acquisition of shape (N >= 5, Nz, Ny, Nx).
    order_otf : VolumeOrderOtf
        Fully validated nominal transfers on the detector's centered grid.
    phase_steps_rad : numpy.ndarray
        Supplied fundamental steps (N,), in radians, passed unchanged to the
        five-column separator even when fitting order two.
    carrier_bins_yx : tuple, list or numpy.ndarray
        Exact integer fundamental y/x carrier in detector frequency bins.
    order : int
        Nonboolean Python or NumPy integer, one or two.

    Returns
    -------
    VolumeOrderGainEstimate
        Immutable scalar gain and diagnostics over every geometric pair.

    Raises
    ------
    SimreconError
        For invalid inputs, empty overlap, zero predictor or handled numerical
        failures. Phase-separation errors propagate with their original codes.

    Notes
    -----
    For q and j=q+order*carrier inside the canonical detector window, fit
    x=Em(j)*D0(q), y=E0(q)*Dm(j) with normalized negative-sign Fourier bands.
    The gain is sum(conj(x)*y)/sum(abs(x)**2). Scaled operands, stable norms
    and exponent-aware component restoration avoid raw product/ratio overflow.
    Residual is computed directly from normalized vectors. Zero response and
    orthogonal response have distinct conventions and statuses; no threshold
    or clipping is applied. Calibration correction/reconstruction remains an
    explicit caller operation. Correlation alone does not establish physical
    identifiability or alias freedom. All inputs and caller policies survive.
    """
    with np.errstate(all="ignore"):
        selected = _integer(order, "invalid_volume_order_gain_order")
        if selected not in (1, 2):
            raise SimreconError("invalid_volume_order_gain_order", "order must be one or two")
        carrier = _carrier(carrier_bins_yx)
        observed, steps = _inputs(images, phase_steps_rad)
        shape = (observed.shape[1], observed.shape[2], observed.shape[3])
        try:
            transfers, _ = _calibration(order_otf, shape)
        except SimreconError as error:
            raise SimreconError("invalid_volume_order_gain_otf", error.message) from error
        source = order_otf.source
        sy, sx = (selected * k for k in carrier)
        nz, ny, nx = shape
        count = nz * max(ny - abs(sy), 0) * max(nx - abs(sx), 0)
        if count == 0:
            raise SimreconError("no_volume_order_gain_overlap", "geometric overlap is empty")
        q = (
            slice(None),
            slice(max(-sy, 0), min(ny - sy, ny)),
            slice(max(-sx, 0), min(nx - sx, nx)),
        )
        j = (slice(None), slice(max(sy, 0), min(ny + sy, ny)), slice(max(sx, 0), min(nx + sx, nx)))
        separated = separate_volume_phases(observed, phases_rad=steps)
        d0, p0 = _transform(separated.dc)
        dm, pm = _transform(separated.c1 if selected == 1 else separated.c2)
        e0, a0 = _scaled(transfers[0][q])
        em, am = _scaled(transfers[selected][j])
        b0, s0 = _scaled(d0[q])
        bm, sm = _scaled(dm[j])
        u, norm_x = _unit(em * b0)
        v, norm_y = _unit(e0 * bm)
        if norm_x == 0:
            raise SimreconError("unidentifiable_volume_order_gain", "computed predictor is zero")
        gain, residual, coherence, status = 0j, 0.0, 0.0, "zero_response"
        if norm_y != 0:
            correlation = complex(np.vdot(u, v))
            _finite(correlation)
            if correlation.real == 0 and correlation.imag == 0:
                residual, status = 1.0, "zero_correlation"
            else:
                numerator, denominator = (a0, sm, norm_y), (am, s0, norm_x)
                gain = complex(
                    _restore(correlation.real, numerator, denominator, pm - p0),
                    _restore(correlation.imag, numerator, denominator, pm - p0),
                )
                coherence = abs(correlation)
                _, residual = _unit(v - correlation * u)
                _finite(coherence)
                status = "fitted"
    return VolumeOrderGainEstimate(
        gain, residual, coherence, count, status, selected, carrier, source
    )
