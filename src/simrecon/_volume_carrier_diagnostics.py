"""Diagnose caller-listed volume carriers against one fixed empirical response."""

import math
import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from ._array_validation import require_finite
from ._empirical_frequency import sample_empirical_volume_transfer
from ._empirical_response import EmpiricalVolumeResponse
from ._empirical_shared_nodes import _integers
from ._empirical_transfer import _RESPONSE_CODE, _array, _frequency, _real, _sequence
from ._model import SimreconError
from ._volume_phase import separate_volume_phases
from .volume_order_gain import _inputs

_FIT = "unrepresentable_volume_carrier_fit"
ComplexArray = npt.NDArray[np.complex128]


@dataclass(frozen=True)
class VolumeCarrierCandidate:
    """One immutable scalar diagnostic in the caller's candidate order.

    Attributes
    ----------
    gain : complex or None
        Dimensionless free complex least-squares gain, absent for unavailable fits.
    relative_residual, coherence : float or None
        Direct normalized residual and amplitude correlation, dimensionless.
    overlap_count : int
        Full geometric pair count, including zeros and uncovered pairs.
    status : str
        Information/coverage outcome, or ``fitted``; no ranking is implied.
    order : int
        Selected positive harmonic, one or two.
    carrier_bins_yx : tuple of int
        Exact fundamental lateral carrier in specimen frequency bins.
    source : str
        Unchanged opaque caller pairing label; authenticates no provenance.

    Notes
    -----
    Direct construction performs no validation. Only field bindings are frozen.
    """

    gain: complex | None
    relative_residual: float | None
    coherence: float | None
    overlap_count: int
    status: str
    order: int
    carrier_bins_yx: tuple[int, int]
    source: str


def _response_snapshot(response: EmpiricalVolumeResponse) -> EmpiricalVolumeResponse:
    """Validate and snapshot all six public fields before any numerical work."""
    if not isinstance(response, EmpiricalVolumeResponse):
        raise SimreconError(_RESPONSE_CODE, "expected EmpiricalVolumeResponse")
    try:
        raw = response.values
        raw_spacing = response.voxel_size_um
        raw_origin = response.origin_zyx
        raw_axes = (response.fz_per_um, response.fy_per_um, response.fx_per_um)
    except AttributeError as error:
        raise SimreconError(_RESPONSE_CODE, "missing response field") from error
    if type(raw) is not np.ndarray or raw.ndim != 4 or raw.shape[0] != 3 or 0 in raw.shape:
        raise SimreconError(_RESPONSE_CODE, "expected positive (3,Nz,Ny,Nx) values")
    values = _array(raw, "c", 16, raw.shape)
    dz, dy, dx = (_real(v, _RESPONSE_CODE) for v in _sequence(raw_spacing, 3, _RESPONSE_CODE))
    spacing = (dz, dy, dx)
    if min(spacing) <= 0:
        raise SimreconError(_RESPONSE_CODE, "source spacings must be positive")
    oz, oy, ox = _integers(raw_origin, 3, _RESPONSE_CODE)
    origin = (oz, oy, ox)
    if any(o < 0 or o >= n for o, n in zip(origin, raw.shape[1:], strict=True)):
        raise SimreconError(_RESPONSE_CODE, "source origin must be in bounds")
    axes = tuple(
        _frequency(a, n, d) for a, n, d in zip(raw_axes, raw.shape[1:], spacing, strict=True)
    )
    return EmpiricalVolumeResponse(values, axes[0], axes[1], axes[2], spacing, origin)


def _candidates(value: Any) -> tuple[tuple[int, int], ...]:
    """Snapshot only the declared table grammar, preserving exact integers."""
    code = "invalid_volume_carrier_candidates"
    if type(value) is np.ndarray:
        if value.dtype.kind not in "iu" or value.ndim != 2 or value.shape[1] != 2:
            raise SimreconError(code, "expected an integer (C,2) table")
        rows = value.tolist()
    else:
        rows = _sequence(value, len(value) if type(value) in (tuple, list) else 0, code)
    if not rows:
        raise SimreconError(code, "expected at least one candidate")
    result = []
    for row in rows:
        ky, kx = _integers(row, 2, code)
        result.append((ky, kx))
    return tuple(result)


def _axis(size: int, spacing: float) -> npt.NDArray[np.float64]:
    """Round each exact rational bin coordinate independently, once."""
    code = "unrepresentable_otf_frequencies"
    period = size * Fraction.from_float(spacing)
    values = np.empty(size, dtype=np.float64)
    previous = -math.inf
    for index in range(size):
        mode = index - size // 2
        try:
            coordinate = float(mode / period)
        except OverflowError:
            coordinate = math.inf
        if (
            not math.isfinite(coordinate)
            or (mode != 0 and coordinate == 0)
            or coordinate <= previous
        ):
            raise SimreconError(code, "physical axis cannot be represented distinctly")
        values[index] = coordinate
        previous = coordinate
    return values


def _finite(value: Any) -> None:
    """Check components without taking a potentially overflowing magnitude."""
    require_finite(value, _FIT, "computed fit component is nonfinite")


def _scaled(value: Any) -> tuple[ComplexArray, float]:
    """Bound each complex operand independently and retain its component scale."""
    maximum = max(float(np.max(np.abs(value.real))), float(np.max(np.abs(value.imag)))) or 1.0
    scaled = np.empty(value.shape, dtype=np.complex128)
    scaled.real = value.real / maximum
    scaled.imag = value.imag / maximum
    return scaled, maximum


def _transform(band: Any) -> tuple[ComplexArray, float]:
    """Normalize a component-scaled public FFT while retaining the band scale."""
    scaled, scale = _scaled(band)
    code = "volume_carrier_transform_failure"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            transformed = np.fft.fftshift(np.fft.fftn(scaled, axes=(0, 1, 2), norm="forward"))
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical FFT execution failed") from error
    if not np.isfinite(transformed).all():
        raise SimreconError(code, "FFT returned nonfinite normalized components")
    # Do not restore the spectrum: its components need not fit binary64.
    return transformed, scale


def _product(left: ComplexArray, right: ComplexArray) -> tuple[ComplexArray, tuple[float, ...]]:
    """Multiply bounded operands without constructing their raw physical product."""
    a, sa = _scaled(left)
    b, sb = _scaled(right)
    return a * b, (sa, sb)


def _unit(value: ComplexArray) -> tuple[ComplexArray, tuple[float, float]]:
    """Return a unit vector and factored norm, or a computed zero norm."""
    scaled, maximum = _scaled(value)
    length = float(np.sqrt(np.sum(scaled.real**2 + scaled.imag**2)))
    _finite(length)
    if length == 0:
        return scaled, (maximum, 0.0)
    unit = scaled / length
    _finite(unit)
    return unit, (maximum, length)


def _restore(
    component: float, numerator: tuple[float, ...], denominator: tuple[float, ...]
) -> float:
    """Restore one gain coordinate with correlation included before range testing."""
    mantissa, exponent = math.frexp(component)
    for factor in numerator:
        fraction, power = math.frexp(factor)
        mantissa *= fraction
        exponent += power
    for factor in denominator:
        fraction, power = math.frexp(factor)
        mantissa /= fraction
        exponent -= power
    try:
        value = math.ldexp(mantissa, exponent)
    except OverflowError as error:
        raise SimreconError(_FIT, "restored gain component overflows") from error
    _finite(value)
    return value


def _fit(
    f0: ComplexArray,
    fm: ComplexArray,
    d0: ComplexArray,
    dm: ComplexArray,
    dc_scale: float,
    side_scale: float,
) -> tuple[complex | None, float | None, float | None, str]:
    """Fit all pairs using scaled norms, correlation and a direct residual."""
    x, xs = _product(fm, d0)
    y, ys = _product(f0, dm)
    u, xn = _unit(x)
    v, yn = _unit(y)
    if xn[1] == 0:
        return None, None, None, "zero_predictor"
    if yn[1] == 0:
        return 0j, 0.0, 0.0, "zero_response"
    correlation = complex(np.sum(np.conj(u) * v))
    _finite(correlation)
    if correlation == 0:
        return 0j, 1.0, 0.0, "zero_correlation"
    numerator = (*ys, *yn, side_scale)
    denominator = (*xs, *xn, dc_scale)
    gain = complex(
        _restore(correlation.real, numerator, denominator),
        _restore(correlation.imag, numerator, denominator),
    )
    difference = v - correlation * u
    _, residual_factors = _unit(difference)
    residual = residual_factors[0] * residual_factors[1]
    coherence = abs(correlation)
    _finite((residual, coherence))
    return gain, float(residual), float(coherence), "fitted"


def scan_volume_carriers(
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
) -> tuple[VolumeCarrierCandidate, ...]:
    """Report free complex fits for caller-listed nonwrapping integer carriers.

    Parameters
    ----------
    images : numpy.ndarray
        Plain finite real (phase,z,y,x) observations; at least five phases.
    response : EmpiricalVolumeResponse
        Fixed six-field calibration response, including all unused samples.
    voxel_size_um : tuple or list
        Three positive converted binary64 specimen spacings, z/y/x, in µm.
    phase_steps_rad : numpy.ndarray
        Known actual fundamental phases, radians, passed to the five-column fit.
    candidate_carriers_yx : tuple, list or numpy.ndarray
        Nonempty exact integer pair table. Order and duplicates are preserved.
    order : integer scalar
        Nonboolean positive harmonic, one or two.
    calibration_carrier_bins : tuple or list
        Exact integer y/x calibration carrier, fixed across candidates.
    coordinate_offset_yx : tuple or list
        Exact integer y/x offsets in calibration samples, fixed across candidates.
    phase_reference_shift_rad : real scalar
        Finite specimen-minus-calibration reference shift, radians.
    source : str
        Required nonblank opaque pairing label, retained unchanged.

    Returns
    -------
    tuple of VolumeCarrierCandidate
        Distinct frozen records in caller order, including local unavailable fits.

    Raises
    ------
    SimreconError
        For invalid inputs, inherited phase/interpolation failures, unrepresentable
        physical axes, handled FFT failures or nonfinite final fitting components.
        Unrelated exceptions and allocation failures propagate unchanged.

    Notes
    -----
    Each full pair p,j=p+order*carrier uses independently rounded exact rational
    physical coordinates. With normalized negative-exponent Fourier coefficients,
    x=Fm(j)*D0(p), y=F0(p)*Dm(j). All geometric pairs enter the unweighted fit,
    including zeros. Missing calibration coverage is a local absent fit; no
    wrapping, observation interpolation or support threshold is applied.

    The response and calibration gauge remain fixed across candidates. Gains,
    direct normalized residuals and amplitude correlations identify no physical
    winner, confidence probability or unknown phase. Preserve raw/calibration
    identities externally. All inputs are snapshotted before numerical work;
    caller floating/warning policies and storage are preserved.
    """
    with np.errstate(all="ignore"):
        values, steps = _inputs(images, phase_steps_rad)
        fixed = _response_snapshot(response)
        code = "invalid_volume_carrier_voxel_size"
        spacing = tuple(_real(v, code) for v in _sequence(voxel_size_um, 3, code))
        if min(spacing) <= 0:
            raise SimreconError(code, "specimen spacings must be positive")
        candidates = _candidates(candidate_carriers_yx)
        (selected,) = _integers((order,), 1, "invalid_volume_carrier_order")
        if selected not in (1, 2):
            raise SimreconError("invalid_volume_carrier_order", "expected order one or two")
        calibration = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        offset = _integers(coordinate_offset_yx, 2, "invalid_empirical_transfer_coordinate_offset")
        delta = _real(phase_reference_shift_rad, "invalid_empirical_transfer_phase_shift")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")
        shape = values.shape[1:]
        axes = tuple(_axis(n, d) for n, d in zip(shape, spacing, strict=True))
        components = separate_volume_phases(values, phases_rad=steps)
        dc, dc_scale = _transform(components.dc)
        side, side_scale = _transform(components.c1 if selected == 1 else components.c2)
        rows = []
        for ky, kx in candidates:
            sy, sx = selected * ky, selected * kx
            count = shape[0] * max(shape[1] - abs(sy), 0) * max(shape[2] - abs(sx), 0)
            gain = residual = coherence = None
            status = "no_overlap"
            if count:
                p = (
                    slice(None),
                    slice(max(-sy, 0), min(shape[1] - sy, shape[1])),
                    slice(max(-sx, 0), min(shape[2] - sx, shape[2])),
                )
                j = (
                    slice(None),
                    slice(max(sy, 0), min(shape[1] + sy, shape[1])),
                    slice(max(sx, 0), min(shape[2] + sx, shape[2])),
                )
                sampled = []
                try:
                    for harmonic, region in ((0, p), (selected, j)):
                        query = np.stack(
                            np.meshgrid(
                                *(a[s] for a, s in zip(axes, region, strict=True)), indexing="ij"
                            ),
                            axis=-1,
                        ).reshape(-1, 3)
                        sampled.append(
                            sample_empirical_volume_transfer(
                                fixed,
                                order=harmonic,
                                frequencies_zyx_per_um=query,
                                calibration_carrier_bins=calibration,
                                coordinate_offset_yx=offset,
                                phase_reference_shift_rad=delta,
                                source=source,
                            ).values
                        )
                except SimreconError as error:
                    if error.code != "incomplete_empirical_transfer_coverage":
                        raise
                    status = "incomplete_coverage"
                else:
                    gain, residual, coherence, status = _fit(
                        sampled[0], sampled[1], dc[p].ravel(), side[j].ravel(), dc_scale, side_scale
                    )
            rows.append(
                VolumeCarrierCandidate(
                    gain, residual, coherence, count, status, selected, (ky, kx), source
                )
            )
    return tuple(rows)
