"""Interpolate signed empirical responses on closed physical Cartesian grids."""

import math
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

import numpy as np
import numpy.typing as npt

from ._empirical_response import EmpiricalVolumeResponse
from ._empirical_shared_nodes import _integers
from ._empirical_transfer import _RESPONSE_CODE, _array, _frequency, _phasor, _real, _sequence
from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf

type _Stencil = tuple[tuple[int, Fraction], ...]


@dataclass(frozen=True)
class TrilinearVolumeTransfer:
    """Target orders and independently owned declarations for one grid pairing.

    Attributes
    ----------
    orders : VolumeOrderOtf
        Mutable, owned target arrays for orders 0,+1,+2. The target origin is
        (0,0,0); reconstruction consumes this record explicitly.
    provenance : dict
        Mutable declaration snapshot, read-only by convention. Upstream raw,
        correction and calibration identities must be retained separately.

    Notes
    -----
    Only bindings are frozen. Direct construction performs no validation.
    """

    orders: VolumeOrderOtf
    provenance: dict[str, object]


def _axis(nc: int, dc: float, ns: int, ds: float) -> tuple[npt.NDArray[np.float64], list[_Stencil]]:
    """Build RN64 target coordinates and exact source-index stencils."""
    source_period = nc * Fraction.from_float(dc)
    target_period = ns * Fraction.from_float(ds)
    ratio = source_period / target_period
    stencils: list[_Stencil] = []
    frequencies = np.empty(ns, dtype=np.float64)
    previous = -math.inf
    for index in range(ns):
        mode = index - ns // 2
        position = mode * ratio + nc // 2
        if not 0 <= position <= nc - 1:
            raise SimreconError(
                "incomplete_empirical_transfer_coverage", "target lies outside source closed hull"
            )
        lower = position.numerator // position.denominator
        fraction = position - lower
        stencils.append(
            ((lower, 1 - fraction), (lower + 1, fraction)) if fraction else ((lower, Fraction(1)),)
        )
        exact_coordinate = mode / target_period
        try:
            coordinate = float(exact_coordinate)
        except OverflowError:
            # Normalize conversion overflow for the common representation check.
            coordinate = math.inf
        if (
            not math.isfinite(coordinate)
            or (mode != 0 and coordinate == 0)
            or coordinate <= previous
        ):
            raise SimreconError(
                "unrepresentable_otf_frequencies", "target coordinates collapse or exceed range"
            )
        frequencies[index] = coordinate
        previous = coordinate
    return frequencies, stencils


def _interpolate(samples: list[complex], weights: list[Fraction], phase: complex) -> complex:
    """Sum and rotate at a common power-of-two scale before restoring range.

    Exact rational weights are multiplied by represented components *before*
    conversion to the scaled binary64 summands. Thus neither an axis weight
    nor a tensor weight has to be representable on its own. Scaling by the
    largest weighted component leaves summation/rotation safely bounded. Summand
    rounding and underflow are bounded by the stencil's component mass; fsum
    preserves cancellation without overflowing an unscaled partial sum.
    """
    components = [
        (w * Fraction.from_float(v.real), w * Fraction.from_float(v.imag))
        for v, w in zip(samples, weights, strict=True)
    ]
    exponent = math.frexp(float(max(max(abs(re), abs(im)) for re, im in components)))[1]
    scale = Fraction(2) ** -exponent
    real = math.fsum(float(re * scale) for re, _ in components)
    imag = math.fsum(float(im * scale) for _, im in components)
    try:
        return complex(
            math.ldexp(real * phase.real - imag * phase.imag, exponent),
            math.ldexp(real * phase.imag + imag * phase.real, exponent),
        )
    except OverflowError as error:
        raise SimreconError(
            "unrepresentable_empirical_interpolation", "final computed component exceeds range"
        ) from error


def adapt_empirical_volume_response_trilinear(
    response: EmpiricalVolumeResponse,
    *,
    target_shape_zyx: object,
    target_voxel_size_um: object,
    calibration_carrier_bins: object,
    specimen_carrier_bins: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
) -> TrilinearVolumeTransfer:
    """Interpolate full complex orders and apply a declared constant phase gauge.

    Parameters
    ----------
    response : EmpiricalVolumeResponse
        Centered calibration orders 0,+1,+2. Every public field and all source
        samples are validated and snapshotted, including unused samples.
    target_shape_zyx : tuple or list
        Three positive odd integer dimensions within native index range.
    target_voxel_size_um : tuple or list
        Three positive finite binary64 spacings in micrometres. Every target
        frequency must lie in the closed ideal source Cartesian hull.
    calibration_carrier_bins, specimen_carrier_bins : tuple or list
        Exact integer y/x carriers on the respective grids. Their nonwrapping
        physical frequencies must agree exactly.
    coordinate_offset_yx : tuple or list
        Exact integer source-sample offsets mapping the observed bead origin
        into common illumination coordinates. Target index zero is common zero.
    phase_reference_shift_rad : real scalar
        Finite converted specimen-minus-calibration reference shift, radians.
        Actual phase schedules remain separate inputs to other operations.
    source : str
        Nonblank opaque caller label, retained unchanged.

    Returns
    -------
    TrilinearVolumeTransfer
        Independently owned, mutable native target arrays and eight provenance
        declarations. Bindings are frozen, contents are not.

    Raises
    ------
    SimreconError
        For invalid declarations/response, even target dimensions, missing
        coverage, unequal physical carriers, unrepresentable target coordinates
        or computed final components. Unrelated/allocation failures propagate.

    Notes
    -----
    Geometry uses exact represented spacings, never tolerated source metadata.
    Weights interpolate real and imaginary components identically. Order m is
    then rotated by exp(-i*m*(2*pi*rho+delta)), with exact reduced rho from the
    carrier at origin plus offset. There is no second centering or scale change.
    Exact nodes copy order-zero bits; integral rho and zero delta copy all bits.

    Physical use assumes matching effective response, axes and focal-plane
    model. Interpolation supplies no experimental validity or physical accuracy
    guarantee. There is no extrapolation, wrapping, gain fit or normalization.
    Inputs and caller floating/warning state are preserved. There is no size or
    performance promise. See the public contract for the arithmetic allowance
    and sufficient-success condition; approximation error is separate.
    """
    with np.errstate(all="ignore"):
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
        shape = raw.shape[1:]
        snapshot = _array(raw, "c", 16, raw.shape)
        dz, dy, dx = (_real(v, _RESPONSE_CODE) for v in _sequence(raw_spacing, 3, _RESPONSE_CODE))
        spacing = (dz, dy, dx)
        if min(spacing) <= 0:
            raise SimreconError(_RESPONSE_CODE, "source spacings must be strictly positive")
        oz, oy, ox = _integers(raw_origin, 3, _RESPONSE_CODE)
        origin = (oz, oy, ox)
        if any(o < 0 or o >= n for o, n in zip(origin, shape, strict=True)):
            raise SimreconError(_RESPONSE_CODE, "source origin must be in bounds")
        for axis, n, d in zip(raw_axes, shape, spacing, strict=True):
            _frequency(axis, n, d)

        shape_code = "invalid_empirical_transfer_target_shape"
        nz, ny, nx = _integers(target_shape_zyx, 3, shape_code)
        target_shape = (nz, ny, nx)
        if any(n <= 0 or n > np.iinfo(np.intp).max for n in target_shape):
            raise SimreconError(shape_code, "target dimensions must be positive native indices")
        if any(n % 2 == 0 for n in target_shape):
            raise SimreconError(
                "unsupported_empirical_interpolation_target_nyquist",
                "target dimensions must be odd",
            )
        spacing_code = "invalid_empirical_transfer_target_voxel_size"
        tz, ty, tx = (
            _real(v, spacing_code) for v in _sequence(target_voxel_size_um, 3, spacing_code)
        )
        target_spacing = (tz, ty, tx)
        if min(target_spacing) <= 0:
            raise SimreconError(spacing_code, "target spacings must be strictly positive")
        ky, kx = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        sy, sx = _integers(specimen_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        offset_y, offset_x = _integers(
            coordinate_offset_yx, 2, "invalid_empirical_transfer_coordinate_offset"
        )
        delta = _real(phase_reference_shift_rad, "invalid_empirical_transfer_phase_shift")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")
        for kc, ks, nc, dc, ns, ds in zip(
            (ky, kx),
            (sy, sx),
            shape[1:],
            spacing[1:],
            target_shape[1:],
            target_spacing[1:],
            strict=True,
        ):
            if Fraction(kc, nc) / Fraction.from_float(dc) != Fraction(ks, ns) / Fraction.from_float(
                ds
            ):
                raise SimreconError(
                    "mismatched_empirical_transfer_carrier", "physical lateral carriers differ"
                )
        axes_and_maps = tuple(
            _axis(nc, dc, ns, ds)
            for nc, dc, ns, ds in zip(shape, spacing, target_shape, target_spacing, strict=True)
        )
        fz, fy, fx = (entry[0] for entry in axes_and_maps)
        maps = tuple(entry[1] for entry in axes_and_maps)
        cycles = (
            Fraction(ky * (oy + offset_y), shape[1]) + Fraction(kx * (ox + offset_x), shape[2])
        ) % 1
        identity = cycles == 0 and delta == 0
        phase = _phasor(cycles, delta)
        phases = (1 + 0j, phase, phase * phase)
        values = np.empty((3, *target_shape), dtype=np.complex128)
        for index in np.ndindex(target_shape):
            vertices = list(product(*(axis[i] for axis, i in zip(maps, index, strict=True))))
            indices = [tuple(v[0] for v in vertex) for vertex in vertices]
            weights = [vertex[0][1] * vertex[1][1] * vertex[2][1] for vertex in vertices]
            for order in range(3):
                if len(indices) == 1 and (order == 0 or identity):
                    values[(order, *index)] = snapshot[(order, *indices[0])]
                else:
                    samples = [complex(snapshot[(order, *i)]) for i in indices]
                    values[(order, *index)] = _interpolate(samples, weights, phases[order])
    orders = VolumeOrderOtf(values, fz, fy, fx, target_spacing, (0, 0, 0), source)
    return TrilinearVolumeTransfer(
        orders,
        {
            "sampling": "complex_cartesian_trilinear_v1",
            "source_shape_zyx": shape,
            "source_voxel_size_um": spacing,
            "source_origin_zyx": origin,
            "calibration_carrier_bins": (ky, kx),
            "specimen_carrier_bins": (sy, sx),
            "coordinate_offset_yx": (offset_y, offset_x),
            "phase_reference_shift_rad": delta,
        },
    )
