"""Evaluate signed empirical transfer at explicit physical frequency points."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product

import numpy as np
import numpy.typing as npt

from ._empirical_response import EmpiricalVolumeResponse
from ._empirical_shared_nodes import _integers
from ._empirical_transfer import _RESPONSE_CODE, _array, _frequency, _phasor, _real, _sequence
from ._empirical_trilinear import _interpolate
from ._model import SimreconError


@dataclass(frozen=True)
class EmpiricalFrequencySamples:
    """Owned point samples and their explicit pairing declarations.

    Attributes
    ----------
    values : numpy.ndarray
        Mutable native C-contiguous complex128 vector, dimensionless.
    frequencies_zyx_per_um : numpy.ndarray
        Mutable native C-contiguous float64 (P,3) query snapshot, cycles/µm.
        Point order, duplicates and signed-zero coordinate bits are retained.
    order : int
        The selected signed order, from -2 through 2.
    source : str
        Unchanged opaque caller label for this physical pairing.
    provenance : dict
        Independent mutable declaration snapshot, read-only by convention.
        Upstream calibration identities must be retained separately.

    Notes
    -----
    Only bindings are frozen. Direct construction performs no validation.
    """

    values: npt.NDArray[np.complex128]
    frequencies_zyx_per_um: npt.NDArray[np.float64]
    order: int
    source: str
    provenance: dict[str, object]


def _bracket(coordinate: Fraction, period: Fraction, size: int) -> tuple[tuple[int, Fraction], ...]:
    """Locate an exact represented coordinate on the ideal closed source axis."""
    position = coordinate * period + size // 2
    if not 0 <= position <= size - 1:
        raise SimreconError(
            "incomplete_empirical_transfer_coverage", "query lies outside source closed hull"
        )
    lower = position.numerator // position.denominator
    fraction = position - lower
    if fraction:
        return ((lower, 1 - fraction), (lower + 1, fraction))
    return ((lower, Fraction(1)),)


def sample_empirical_volume_transfer(
    response: EmpiricalVolumeResponse,
    *,
    order: object,
    frequencies_zyx_per_um: object,
    calibration_carrier_bins: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
) -> EmpiricalFrequencySamples:
    """Sample one signed complex trilinear transfer with a declared gauge.

    Parameters
    ----------
    response : EmpiricalVolumeResponse
        Centered rows 0,+1,+2. Every source field and sample is validated and
        snapshotted, including unused rows and source frequency metadata.
    order : integer scalar
        Nonboolean Python/NumPy integer in {-2,-1,0,1,2}.
    frequencies_zyx_per_um : numpy.ndarray
        Plain finite float64-width array (P,3), P >= 1, in cycles/µm.
        Each component means its exact represented real value, without snapping.
    calibration_carrier_bins : tuple or list
        Exact integer y/x carrier used only for the calibration gauge.
    coordinate_offset_yx : tuple or list
        Exact integer y/x offsets in source calibration samples, mapping the
        observed origin into common illumination coordinates.
    phase_reference_shift_rad : real scalar
        Finite converted specimen-minus-calibration phase-reference shift,
        radians. Actual phase schedules remain separate inputs.
    source : str
        Required nonblank opaque physical-pairing label, retained unchanged.

    Returns
    -------
    EmpiricalFrequencySamples
        Independent mutable owned native arrays and seven provenance entries.

    Raises
    ------
    SimreconError
        For invalid response/declarations, any point outside the evaluated
        closed source hull, or unrepresentable computed final components.
        Allocation failures and unrelated exceptions propagate unchanged.

    Notes
    -----
    Source nodes are exactly k/(N*d) using converted spacing, independently of
    tolerated metadata rounding. Negative orders reflect all three query axes,
    evaluate the positive row and conjugate after applying the constant gauge
    exp(-i*abs(order)*(2*pi*rho+delta)) once. Even-axis physical endpoints are
    distinct; existing modular reconstruction consumers remain unchanged.

    Real and imaginary parts share convex tensor weights. Exact source nodes
    copy order-zero bits; integral rho and zero delta copy positive-order bits.
    Negative identity-gauge nodes toggle only the imaginary sign bit. Safe
    component arithmetic retains finite contributions from tiny exact weights.
    See the contract for absolute arithmetic bounds and range limitations.

    No observation interpolation, support inference, physical compatibility
    certification, normalization, estimation or reconstruction occurs. Inputs
    and caller floating/warning policy are preserved. Concurrent mutation and
    practical size/performance guarantees are outside this operation's scope.
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

        (signed_order,) = _integers((order,), 1, "invalid_empirical_transfer_order")
        if not -2 <= signed_order <= 2:
            raise SimreconError("invalid_empirical_transfer_order", "expected order -2 through 2")
        query = frequencies_zyx_per_um
        if (
            type(query) is not np.ndarray
            or query.dtype.kind != "f"
            or query.dtype.itemsize != 8
            or query.ndim != 2
            or query.shape[1] != 3
            or query.shape[0] == 0
            or not np.isfinite(query).all()
        ):
            raise SimreconError(
                "invalid_empirical_transfer_frequencies", "expected finite float64 (P,3) queries"
            )
        points = np.array(query, dtype=np.float64, order="C", copy=True)
        ky, kx = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        offset_y, offset_x = _integers(
            coordinate_offset_yx, 2, "invalid_empirical_transfer_coordinate_offset"
        )
        delta = _real(phase_reference_shift_rad, "invalid_empirical_transfer_phase_shift")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")

        periods = tuple(n * Fraction.from_float(d) for n, d in zip(shape, spacing, strict=True))
        cycles = (
            Fraction(ky * (oy + offset_y), shape[1]) + Fraction(kx * (ox + offset_x), shape[2])
        ) % 1
        identity = cycles == 0 and delta == 0
        phase = _phasor(cycles, delta)
        phases = (1 + 0j, phase, phase * phase)
        row = abs(signed_order)
        direction = -1 if signed_order < 0 else 1
        values = np.empty(len(points), dtype=np.complex128)
        for j, point in enumerate(points):
            vertices = list(
                product(
                    *(
                        _bracket(direction * Fraction.from_float(float(f)), period, n)
                        for f, period, n in zip(point, periods, shape, strict=True)
                    )
                )
            )
            indices = [tuple(v[0] for v in vertex) for vertex in vertices]
            if len(indices) == 1 and (row == 0 or identity):
                value = complex(snapshot[(row, *indices[0])])
            else:
                weights = [vertex[0][1] * vertex[1][1] * vertex[2][1] for vertex in vertices]
                samples = [complex(snapshot[(row, *i)]) for i in indices]
                value = _interpolate(samples, weights, phases[row])
            values[j] = value.conjugate() if signed_order < 0 else value
    return EmpiricalFrequencySamples(
        values,
        points,
        signed_order,
        source,
        {
            "sampling": "complex_cartesian_trilinear_points_v1",
            "source_shape_zyx": shape,
            "source_voxel_size_um": spacing,
            "source_origin_zyx": origin,
            "calibration_carrier_bins": (ky, kx),
            "coordinate_offset_yx": (offset_y, offset_x),
            "phase_reference_shift_rad": delta,
        },
    )
