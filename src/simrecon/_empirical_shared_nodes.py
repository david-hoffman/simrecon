"""Transport signed empirical responses at exact shared physical native nodes."""

from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from ._array_validation import conversion_errors
from ._empirical_response import EmpiricalVolumeResponse
from ._empirical_transfer import (
    _RESPONSE_CODE,
    _array,
    _frequency,
    _phasor,
    _real,
    _rotate,
    _sequence,
)
from ._empirical_transfer import (
    _integers as _parse_integers,
)
from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf


@dataclass(frozen=True)
class SharedNodeVolumeTransfer:
    """A target transfer and the declarations used for exact native lookup.

    Attributes
    ----------
    orders : VolumeOrderOtf
        Target orders 0,+1,+2, with independent mutable native arrays and
        displacement origin (0,0,0). Pass this record to reconstruction.
    provenance : dict
        Independent mutable declaration snapshot, read-only by convention.
        Records source geometry, origin, selected indices, carriers and gauge.

    Notes
    -----
    Bindings are frozen. Direct construction adds no validation or deep freeze.
    Declarations certify neither physical pairing nor upstream provenance.
    """

    orders: VolumeOrderOtf
    provenance: dict[str, object]


def _integers(value: object, count: int, code: str) -> tuple[int, ...]:
    """Reuse integer grammar while translating expected scalar conversion errors."""
    with conversion_errors(code, "integer declaration conversion failed"):
        return _parse_integers(value, count, code)


def _axis_indices(nc: int, dc: float, ns: int, ds: float) -> tuple[int, ...]:
    """Map exact rational physical nodes to source centered array indices."""
    ratio = nc * Fraction.from_float(dc) / (ns * Fraction.from_float(ds))
    indices = []
    for j in range(-(ns // 2), (ns + 1) // 2):
        i = j * ratio
        if i.denominator != 1 or not -(nc // 2) <= i < (nc + 1) // 2:
            raise SimreconError(
                "incomplete_empirical_transfer_coverage", "target node has no exact source node"
            )
        indices.append(int(i) + nc // 2)
    return tuple(indices)


def _require_negation(indices: tuple[int, ...], nc: int) -> None:
    """Require lookup to commute with canonical modular frequency negation."""
    ns = len(indices)
    for position, index in enumerate(indices):
        j = position - ns // 2
        i = index - nc // 2
        if indices[(-j + ns // 2) % ns] != (-i + nc // 2) % nc:
            raise SimreconError(
                "incompatible_empirical_transfer_negation",
                "shared nodes do not commute with modular negation",
            )


def adapt_empirical_volume_response_shared_nodes(
    response: EmpiricalVolumeResponse,
    *,
    target_shape_zyx: object,
    target_voxel_size_um: object,
    calibration_carrier_bins: object,
    specimen_carrier_bins: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
) -> SharedNodeVolumeTransfer:
    """Select exact shared native nodes and apply a declared specimen phase gauge.

    Parameters
    ----------
    response : EmpiricalVolumeResponse
        Full signed calibration responses. Every public field is validated,
        including unselected values and coordinates of direct records.
    target_shape_zyx : tuple or list
        Three positive nonboolean integer dimensions within native index range.
    target_voxel_size_um : tuple or list
        Three positive finite converted binary64 spacings in micrometres.
        Target index zero declares common illumination coordinate zero.
    calibration_carrier_bins, specimen_carrier_bins : tuple or list
        Exact integer y/x carriers on the respective grids. Physical frequencies
        must agree exactly, without wrapping or a principal-window limit.
    coordinate_offset_yx : tuple or list
        Exact integer offsets in source calibration samples, mapping the
        observed source origin into common lateral illumination coordinates.
    phase_reference_shift_rad : real scalar
        Finite converted specimen-minus-calibration separation origin, radians.
    source : str
        Nonblank opaque label identifying the caller's pairing/declarations.

    Returns
    -------
    SharedNodeVolumeTransfer
        Target VolumeOrderOtf and exactly nine provenance declarations. Arrays
        are independently owned, native, C-contiguous and mutable. Frequency
        components are copied from mapped source coordinates without arithmetic.

    Raises
    ------
    SimreconError
        On invalid declarations/response, missing exact nodes, incompatible
        modular negation, unequal physical carriers or computed side overflow.
        Allocation failures and unrelated exceptions propagate unchanged.

    Notes
    -----
    Spacings mean their exact converted rational values. With Lc=Nc*dc and
    Ls=Ns*ds, every target mode j must map to integer i=j*Lc/Ls inside the
    source canonical window. Lookup must commute with modular negation.
    A singleton target axis selects only source DC at any valid spacing.

    At selected nodes order m is multiplied by exp(-i*m*(2*pi*rho+delta)),
    where rho=ky_c*(origin_y+offset_y)/Ny_c +
    kx_c*(origin_x+offset_x)/Nx_c, reduced exactly modulo one. Order zero
    always copies components bit for bit; integral rho and either signed-zero
    delta copy all orders. Only selected side values rotate or face range checks.
    Side error is bounded by 128*2^-52*(abs(Re E)+abs(Im E))+16*2^-1074.
    The strict-interior sufficient-success bound is not a rejection cutoff.

    Physical use assumes equal paired effective transfers at these nodes,
    common axis directions/order and a common focal-plane-relative model.
    Geometry and labels cannot establish this assumption. There is no transform,
    interpolation, normalization, specimen translation or parameter inference.
    Reconstruction independently validates its signed window, gain and range.
    """
    with np.errstate(all="ignore"):
        if not isinstance(response, EmpiricalVolumeResponse):
            raise SimreconError(_RESPONSE_CODE, "expected EmpiricalVolumeResponse")
        raw = response.values
        if type(raw) is not np.ndarray or raw.ndim != 4 or raw.shape[0] != 3 or 0 in raw.shape:
            raise SimreconError(_RESPONSE_CODE, "expected positive (3,Nz,Ny,Nx) values")
        shape = raw.shape[1:]
        snapshot = _array(raw, "c", 16, raw.shape)
        dz, dy, dx = (
            _real(v, _RESPONSE_CODE) for v in _sequence(response.voxel_size_um, 3, _RESPONSE_CODE)
        )
        spacing = (dz, dy, dx)
        if min(spacing) <= 0:
            raise SimreconError(_RESPONSE_CODE, "converted spacings must be strictly positive")
        oz, oy, ox = _integers(response.origin_zyx, 3, _RESPONSE_CODE)
        origin = (oz, oy, ox)
        if any(o < 0 or o >= n for o, n in zip(origin, shape, strict=True)):
            raise SimreconError(_RESPONSE_CODE, "origin must be in bounds")
        frequencies = (
            _frequency(response.fz_per_um, shape[0], dz),
            _frequency(response.fy_per_um, shape[1], dy),
            _frequency(response.fx_per_um, shape[2], dx),
        )
        shape_code = "invalid_empirical_transfer_target_shape"
        nz, ny, nx = _integers(target_shape_zyx, 3, shape_code)
        target_shape = (nz, ny, nx)
        if any(n <= 0 or n > np.iinfo(np.intp).max for n in target_shape):
            raise SimreconError(shape_code, "target dimensions must be positive native indices")
        spacing_code = "invalid_empirical_transfer_target_voxel_size"
        tz, ty, tx = (
            _real(v, spacing_code) for v in _sequence(target_voxel_size_um, 3, spacing_code)
        )
        target_spacing = (tz, ty, tx)
        if min(target_spacing) <= 0:
            raise SimreconError(spacing_code, "target spacings must be strictly positive")
        ky, kx = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        sy, sx = _integers(specimen_carrier_bins, 2, "invalid_empirical_transfer_carrier")
        oy_c, ox_c = _integers(
            coordinate_offset_yx, 2, "invalid_empirical_transfer_coordinate_offset"
        )
        delta = _real(phase_reference_shift_rad, "invalid_empirical_transfer_phase_shift")
        if not isinstance(source, str) or not source.strip():
            raise SimreconError("invalid_otf_source", "source must be a nonblank string")

        maps = tuple(
            _axis_indices(nc, dc, ns, ds)
            for nc, dc, ns, ds in zip(shape, spacing, target_shape, target_spacing, strict=True)
        )
        for indices, nc in zip(maps, shape, strict=True):
            _require_negation(indices, nc)
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

        values = np.array(
            snapshot[np.ix_(range(3), *maps)], dtype=np.complex128, order="C", copy=True
        )
        fz, fy, fx = (
            np.array(vector[list(indices)], dtype=np.float64, order="C", copy=True)
            for vector, indices in zip(frequencies, maps, strict=True)
        )
        cycles = (Fraction(ky * (oy + oy_c), shape[1]) + Fraction(kx * (ox + ox_c), shape[2])) % 1
        if cycles != 0 or delta != 0:
            phase = _phasor(cycles, delta)
            _rotate(values[1], phase)
            _rotate(values[2], phase * phase)

    orders = VolumeOrderOtf(values, fz, fy, fx, target_spacing, (0, 0, 0), source)
    provenance = {
        "sampling": "exact_shared_native_nodes_v1",
        "source_shape_zyx": shape,
        "source_voxel_size_um": spacing,
        "source_origin_zyx": origin,
        "source_indices_zyx": maps,
        "calibration_carrier_bins": (ky, kx),
        "specimen_carrier_bins": (sy, sx),
        "coordinate_offset_yx": (oy_c, ox_c),
        "phase_reference_shift_rad": delta,
    }
    return SharedNodeVolumeTransfer(orders, provenance)
