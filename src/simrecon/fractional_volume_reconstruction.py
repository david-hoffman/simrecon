"""Filter native volume bands before finite fractional phase-ramp relocation."""

import math
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from ._volume_phase import separate_volume_phases
from .volume_reconstruction import (
    _GRID,
    _OTFS,
    Reconstruction3D,
    _calibration,
    _container,
    _finite,
    _frequencies,
    _integer,
    _real_array,
    _real_scalar,
    _transform,
)

_Carrier = tuple[Fraction, Fraction]
_Complex = npt.NDArray[np.complex128]


def _window(
    output_shape_yx: object, native: tuple[int, int, int], carriers: list[_Carrier]
) -> tuple[int, int, int]:
    """Check both exact size and closed translated-anchor conditions."""
    code = "invalid_volume_reconstruction_output_shape"
    lengths = tuple(_integer(v, code) for v in _container(output_shape_yx, 2, code))
    for axis, length in enumerate(lengths):
        if length <= 0 or length > np.iinfo(np.intp).max:
            raise SimreconError(code, "output dimensions must be positive native indices")
        k = native[axis + 1]
        extent = 2 * max(abs(c[axis]) for c in carriers)
        if (
            length < k + math.ceil(2 * extent)
            or -(k // 2) - extent < -(length // 2)
            or (k - 1) // 2 + extent > (length - 1) // 2
        ):
            raise SimreconError(code, "output window must retain every signed native anchor")
    return native[0], lengths[0], lengths[1]


def _axis_sample(values: _Complex, shift: Fraction, axis: int) -> _Complex:
    """Interpolate exact shifted native nodes along one closed canonical hull."""
    length = values.shape[axis]
    # The query at array index i is i + shift in array-index coordinates.
    # Exact rational comparisons decide availability and exact-node selection.
    start = max(0, math.ceil(-shift))
    stop = min(length, math.floor(length - 1 - shift) + 1)
    result = np.zeros(values.shape, dtype=np.complex128)
    if start >= stop:
        return result
    lower = math.floor(shift)
    fraction = shift - lower
    destination = [slice(None)] * 3
    source = [slice(None)] * 3
    destination[axis] = slice(start, stop)
    source[axis] = slice(start + lower, stop + lower)
    if not fraction:
        result[tuple(destination)] = values[tuple(source)]
    else:
        # Componentwise convex interpolation avoids complex magnitude/division
        # overflow and does not interpolate phase or absolute value.
        left = values[tuple(source)]
        source[axis] = slice(start + lower + 1, stop + lower + 1)
        right = values[tuple(source)]
        block = result[tuple(destination)]
        w0, w1 = float(1 - fraction), float(fraction)
        block.real = left.real * w0 + right.real * w1
        block.imag = left.imag * w0 + right.imag * w1
        _finite(block)
    return result


def _denominator(
    rows: list[list[_Complex]],
    carriers: list[_Carrier],
    gains: npt.NDArray[np.float64],
    carrier: _Carrier,
    order: int,
    penalty: float,
) -> npt.NDArray[np.float64]:
    """Sum signed transfer power at each native band's relocated coordinates."""
    result = np.zeros(rows[0][0].shape, dtype=np.float64)
    for s, signed in enumerate(rows):
        for ell, transfer in zip(range(-2, 3), signed, strict=True):
            query_y = ell * carriers[s][0] - order * carrier[0]
            query_x = ell * carriers[s][1] - order * carrier[1]
            sampled = _axis_sample(_axis_sample(transfer, query_y, 1), query_x, 2)
            sampled *= gains[s]
            _finite(sampled)
            power = sampled.real * sampled.real + sampled.imag * sampled.imag
            _finite(power)
            result += power
            _finite(result)
    result += penalty
    _finite(result)
    return result


def _phase_ramp(carrier: _Carrier, order: int, output: tuple[int, int, int]) -> _Complex:
    """Reduce exact rational cycles before evaluating a bounded negative angle."""
    _, ly, lx = output
    angles = np.array(
        [
            -math.tau * float((order * (carrier[0] * y / ly + carrier[1] * x / lx)) % 1)
            for y in range(ly)
            for x in range(lx)
        ],
        dtype=np.float64,
    ).reshape(ly, lx)
    ramp = np.empty((ly, lx), dtype=np.complex128)
    np.cos(angles, out=ramp.real)
    np.sin(angles, out=ramp.imag)
    return ramp


def _synthesize(
    observed: npt.NDArray[np.float64],
    phases: npt.NDArray[np.float64],
    rows: list[list[_Complex]],
    carriers: list[_Carrier],
    gains: npt.NDArray[np.float64],
    penalty: float,
    output: tuple[int, int, int],
) -> _Complex:
    """Filter native coefficients, embed, synthesize, ramp and accumulate."""
    native = observed.shape[2:]
    window = tuple(
        slice(length // 2 - k // 2, length // 2 - k // 2 + k)
        for k, length in zip(native, output, strict=True)
    )
    total = np.zeros(output, dtype=np.complex128)
    for r, carrier in enumerate(carriers):
        separated = separate_volume_phases(observed[r], phases_rad=phases[r])
        bands = (separated.dc, separated.c1, separated.c2)
        for m, transfer in zip(range(-2, 3), rows[r], strict=True):
            band = bands[abs(m)]
            if m < 0:
                band = np.conj(band)
            coefficients = _transform(band, inverse=False)
            t = transfer * gains[r]
            _finite(t)
            denominator = _denominator(rows, carriers, gains, carrier, m, penalty)
            filtered = np.conj(t) * coefficients
            _finite(filtered)
            positive = denominator > 0
            filtered[~positive] = 0
            np.divide(filtered.real, denominator, out=filtered.real, where=positive)
            np.divide(filtered.imag, denominator, out=filtered.imag, where=positive)
            _finite(filtered)
            embedded = np.zeros(output, dtype=np.complex128)
            embedded[window] = filtered
            synthesized = _transform(embedded, inverse=True)
            synthesized *= _phase_ramp(carrier, m, output)
            _finite(synthesized)
            total += synthesized
            _finite(total)
    return total


def reconstruct_volume_fractional(
    images: npt.NDArray[Any],
    *,
    order_otfs: tuple[VolumeOrderOtf, ...] | list[VolumeOrderOtf],
    phases_rad: npt.NDArray[Any],
    carriers_per_um: npt.NDArray[Any],
    gains: npt.NDArray[Any],
    regularization: object,
    output_shape_yx: object,
    apodization: npt.NDArray[Any],
) -> Reconstruction3D:
    """Reconstruct a complex volume with finite fractional band relocation.

    Parameters
    ----------
    images : numpy.ndarray
        Plain finite real exposures (R,N,Nz,Ny,Nx), with N >= 5.
    order_otfs : tuple or list of VolumeOrderOtf
        Complex native order 0,+1,+2 transfers with common voxel spacing.
    phases_rad : numpy.ndarray
        Known fundamental phases (R,N), in radians.
    carriers_per_um : numpy.ndarray
        Finite real lateral y/x carriers (R,2), in cycles per micrometre.
    gains : numpy.ndarray
        Finite positive transfer gains (R,).
    regularization : real scalar
        Finite nonnegative penalty, in squared-transfer units.
    output_shape_yx : tuple or list of int
        Explicit lateral window retaining every translated native anchor.
    apodization : numpy.ndarray
        Real centered amplitude taper (Nz,Ly,Lx), with values in [0,1].

    Returns
    -------
    Reconstruction3D
        Independently owned complex volume, centered spectrum and physical grids.

    Raises
    ------
    SimreconError
        For invalid inputs, unrepresentable grids/arithmetic or numerical
        transform failures. Existing phase separation errors propagate.

    Notes
    -----
    Geometry uses exact rational products of converted binary64 inputs.
    Signed transfers use all-axis modular reflection before interpolation.
    Native filtering precedes embedding and index-zero phase-ramp synthesis.
    Output tails and the complex canonical even endpoint are retained. This
    finite periodic estimator implies no zero exterior or continuum resolution.
    All snapshots precede numerical work. Caller buffers and numerical policies
    are preserved; unrelated exceptions and MemoryError propagate.
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
        carrier_code = "invalid_fractional_volume_carriers"
        physical_carriers = _real_array(carriers_per_um, (r_count, 2), carrier_code, carrier_code)
        penalty_code = "invalid_volume_reconstruction_regularization"
        penalty = _real_scalar(regularization, penalty_code)
        if penalty < 0:
            raise SimreconError(penalty_code, "regularization must be nonnegative")
        calibrations = [
            _calibration(record, detector) for record in _container(order_otfs, r_count, _OTFS)
        ]
        spacing = calibrations[0][1]
        if any(d != spacing for _, d in calibrations):
            raise SimreconError(_OTFS, "all orientations must have identical converted spacing")
        carriers = [
            (
                ny * Fraction(spacing[1]) * Fraction(float(y)),
                nx * Fraction(spacing[2]) * Fraction(float(x)),
            )
            for y, x in physical_carriers
        ]
        output = _window(output_shape_yx, detector, carriers)
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
        negation = np.ix_(*[(2 * (k // 2) - np.arange(k)) % k for k in detector])
        rows = [
            [
                np.conj(values[2][negation]),
                np.conj(values[1][negation]),
                values[0],
                values[1],
                values[2],
            ]
            for values, _ in calibrations
        ]
        total = _synthesize(observed, phases, rows, carriers, gain, penalty, output)
        spectrum = _transform(total, inverse=False)
        np.multiply(spectrum.real, mask, out=spectrum.real)
        np.multiply(spectrum.imag, mask, out=spectrum.imag)
        _finite(spectrum)
        volume = _transform(spectrum, inverse=True)
    return Reconstruction3D(
        volume, spectrum, fz, fy, fx, (out_spacing[0], out_spacing[1], out_spacing[2])
    )
