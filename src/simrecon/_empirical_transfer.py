"""Consume a declared same-grid empirical response in a specimen phase gauge."""

import math
from fractions import Fraction
from typing import cast

import numpy as np
import numpy.typing as npt

from ._empirical_response import EmpiricalVolumeResponse
from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf

_RESPONSE_CODE = "invalid_empirical_transfer_response"
_EPS = Fraction(1, 2**52)
_QUANTUM = Fraction(1, 2**1074)


def _sequence(value: object, count: int, code: str) -> tuple:
    if type(value) not in (tuple, list):
        raise SimreconError(code, f"expected a built-in tuple/list of length {count}")
    items = cast(tuple | list, value)
    if len(items) != count:
        raise SimreconError(code, f"expected a built-in tuple/list of length {count}")
    return tuple(items)


def _integers(value: object, count: int, code: str) -> tuple[int, ...]:
    items = _sequence(value, count, code)
    if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, (int, np.integer)) for v in items):
        raise SimreconError(code, "expected nonboolean integer scalars")
    return tuple(int(v) for v in items)


def _real(value: object, code: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise SimreconError(code, "expected a nonboolean real scalar")
    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SimreconError(code, "real scalar conversion failed") from error
    if not math.isfinite(converted):
        raise SimreconError(code, "converted scalar must be finite")
    return converted


def _array(value: object, kind: str, width: int, shape: tuple[int, ...]) -> np.ndarray:
    if (
        type(value) is not np.ndarray
        or value.dtype.kind != kind
        or value.dtype.itemsize != width
        or value.shape != shape
        or not np.isfinite(value).all()
    ):
        raise SimreconError(_RESPONSE_CODE, "invalid response array representation or components")
    return np.array(value, dtype=np.complex128 if kind == "c" else np.float64, order="C", copy=True)


def _frequency(value: object, size: int, spacing: float) -> npt.NDArray[np.float64]:
    vector = _array(value, "f", 8, (size,))
    if vector[size // 2] != 0 or np.any(vector[1:] <= vector[:-1]):
        raise SimreconError(_RESPONSE_CODE, "frequency bins must increase with centered zero DC")
    # Exact rational comparisons admit extreme periods and finite bins whose
    # exact target is slightly beyond binary64. No floating intermediate N*d.
    period = size * Fraction.from_float(spacing)
    for index, frequency in enumerate(vector):
        mode = index - size // 2
        expected = mode / period
        if (mode != 0 and frequency == 0) or abs(
            Fraction.from_float(float(frequency)) - expected
        ) > 8 * _EPS * abs(expected) + _QUANTUM:
            raise SimreconError(
                _RESPONSE_CODE, "frequency differs from the declared canonical grid"
            )
    return vector


def _phasor(cycles: Fraction, delta: float) -> complex:
    """Reduce rational cycles exactly; let libm reduce the finite delta itself."""
    quarters = cycles * 4
    if quarters.denominator == 1:
        carrier = (1 + 0j, -1j, -1 + 0j, 1j)[int(quarters) % 4]
    else:
        if cycles > Fraction(1, 2):
            cycles -= 1
        angle = -math.tau * float(cycles)
        carrier = complex(math.cos(angle), math.sin(angle))
    # Adding delta to the bounded carrier angle would lose that carrier for
    # huge delta. Squaring the fundamental later also avoids forming 2*delta.
    reference = complex(math.cos(delta), -math.sin(delta))
    return carrier * reference


def _rotate(values: npt.NDArray[np.complex128], phase: complex) -> None:
    """Rotate components at half scale, then restore their range independently."""
    real = values.real * 0.5
    imag = values.imag * 0.5
    values.real = np.ldexp(real * phase.real - imag * phase.imag, 1)
    values.imag = np.ldexp(real * phase.imag + imag * phase.real, 1)
    if not np.isfinite(values).all():
        raise SimreconError(
            "unrepresentable_empirical_transfer", "final computed side component is nonfinite"
        )


def adapt_empirical_volume_response(
    response: EmpiricalVolumeResponse,
    *,
    carrier_bins: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
) -> VolumeOrderOtf:
    """Rotate signed empirical transfers into an explicitly paired specimen gauge.

    Parameters
    ----------
    response : EmpiricalVolumeResponse
        Same-grid centered complex responses 0,+1,+2. All fields are validated,
        including directly constructed arbitrary algebraic records.
    carrier_bins : tuple or list
        Required exact integer y/x detector-bin carrier, with no magnitude cap.
    coordinate_offset_yx : tuple or list
        Required exact integer offset mapping stored indices to fixed lateral
        illumination coordinates, in detector samples.
    phase_reference_shift_rad : real scalar
        Required specimen minus calibration separation reference, converted to
        finite binary64 radians. Actual phase schedules are supplied separately.
    source : str
        Required nonblank opaque pairing/declaration label, retained unchanged.

    Returns
    -------
    VolumeOrderOtf
        Existing frozen-binding record with independent native mutable arrays.
        Order m is multiplied by exp(-i*m*(2*pi*rho+delta)); rho is the exact
        carrier phase at origin plus offset. Full order zero is copied exactly.

    Raises
    ------
    SimreconError
        On invalid public fields/declarations or nonfinite computed side output.
        Allocation failures and unrelated exceptions propagate unchanged.

    Notes
    -----
    All accepted data are snapshotted before rotation. Integral rho and zero
    converted delta copy every order bit for bit. Common normalization and
    signed complex information remain; no transform, resampling or physical
    certification occurs. The caller declares equal grids, spacing, axis
    directions, instrument response and focal-plane-relative model.

    Side-sample absolute error is at most 128*2^-52*(abs(Re E)+abs(Im E))
    +16*2^-1074. This is a dimensionless project budget, not physical accuracy
    or a relative/subnormal-retention promise. Safely finite components must
    succeed even when input complex magnitude overflows. Computed nonfiniteness
    rejects the whole call; no clipping, partial output or range fallback occurs.
    Inputs and caller floating/warning modes are preserved. There is no I/O,
    unknown-parameter inference, working-set or performance guarantee.
    """
    with np.errstate(all="ignore"):
        if not isinstance(response, EmpiricalVolumeResponse):
            raise SimreconError(_RESPONSE_CODE, "expected EmpiricalVolumeResponse")
        raw = response.values
        if type(raw) is not np.ndarray or raw.ndim != 4 or raw.shape[0] != 3 or 0 in raw.shape:
            raise SimreconError(_RESPONSE_CODE, "expected positive (3,Nz,Ny,Nx) values")
        shape = raw.shape[1:]
        values = _array(raw, "c", 16, raw.shape)
        dz, dy, dx = (
            _real(v, _RESPONSE_CODE) for v in _sequence(response.voxel_size_um, 3, _RESPONSE_CODE)
        )
        if min(dz, dy, dx) <= 0:
            raise SimreconError(_RESPONSE_CODE, "converted spacings must be strictly positive")
        oz, oy, ox = _integers(response.origin_zyx, 3, _RESPONSE_CODE)
        if any(o < 0 or o >= n for o, n in zip((oz, oy, ox), shape, strict=True)):
            raise SimreconError(_RESPONSE_CODE, "origin must be in bounds")
        fz = _frequency(response.fz_per_um, shape[0], dz)
        fy = _frequency(response.fy_per_um, shape[1], dy)
        fx = _frequency(response.fx_per_um, shape[2], dx)
        ky, kx = _integers(carrier_bins, 2, "invalid_empirical_transfer_carrier")
        ty, tx = _integers(coordinate_offset_yx, 2, "invalid_empirical_transfer_coordinate_offset")
        delta = _real(phase_reference_shift_rad, "invalid_empirical_transfer_phase_shift")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")
        cycles = (Fraction(ky * (oy + ty), shape[1]) + Fraction(kx * (ox + tx), shape[2])) % 1
        if cycles != 0 or delta != 0:
            phase = _phasor(cycles, delta)
            _rotate(values[1], phase)
            _rotate(values[2], phase * phase)
    return VolumeOrderOtf(values, fz, fy, fx, (dz, dy, dx), (oz, oy, ox), source)
