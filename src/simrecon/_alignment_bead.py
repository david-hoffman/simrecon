"""Calibrate already corrected matched beads and consume their complex transfer."""

import copy
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

from ._alignment_camera import AlignmentCameraFrames, AlignmentCameraPair
from ._bead_peak import locate_bead_peak
from ._empirical_frequency import EmpiricalFrequencySamples, sample_empirical_volume_transfer
from ._empirical_response import EmpiricalVolumeResponse, prepare_empirical_volume_response
from ._empirical_transfer import _integers, _real
from ._finite_bead_calibration import (
    _center,
    _divide,
    _fraction,
    _localization,
    _normalized_spectrum,
    _profile,
)
from ._model import SimreconError
from ._volume_otf import _frequencies, _spacing, _triple
from ._volume_phase import VolumePhaseComponents, separate_volume_phases

_INVALID = "invalid_alignment_bead_calibration"


@dataclass(frozen=True)
class AlignmentBeadCalibration:
    """Original observed harmonics, dimensionless response and owned metadata.

    Bindings are frozen; arrays and the plain provenance dict remain mutable.
    Components retain the pair's output unit. Direct construction adds no
    validation. Common response normalization discards absolute brightness.
    """

    components: VolumePhaseComponents
    response: EmpiricalVolumeResponse
    provenance: dict[str, Any]


def _frame_metadata(frame: AlignmentCameraFrames) -> dict[str, Any]:
    """Retain independent correction declarations without copying pixel data."""
    return {
        name: copy.deepcopy(getattr(frame, name))
        for name in ("axes", "input_unit", "output_unit", "source_metadata", "provenance")
    }


def _discrete_response(
    components: VolumePhaseComponents,
    mass: Fraction,
    voxel_size_um: object,
    bead_profile: object,
    carrier: tuple[int, ...],
    minimum: float,
) -> tuple[EmpiricalVolumeResponse, dict[str, Any]]:
    """Compose the existing finite-profile primitives on separated observations."""
    spacing = tuple(_spacing(v) for v in _triple(voxel_size_um, "invalid_otf_voxel_size"))
    dz, dy, dx = spacing
    shape = components.dc.shape
    fz, fy, fx = (_frequencies(n, d) for n, d in zip(shape, spacing, strict=True))
    supplied, normalized, profile = _profile(bead_profile, shape, minimum)
    compensated = np.empty((3, *shape), dtype=np.complex128)
    for order, observed in enumerate((components.dc, components.c1, components.c2)):
        spectrum = _normalized_spectrum(observed, mass, zero_order=order == 0)
        for index in np.ndindex(shape):
            shifted = (
                index[0],
                (index[1] - order * carrier[0]) % shape[1],
                (index[2] - order * carrier[1]) % shape[2],
            )
            compensated[(order, *index)] = _divide(spectrum[index], profile[shifted])
    localization = _localization(compensated[0])
    origin = locate_bead_peak(localization).index_zyx
    response = EmpiricalVolumeResponse(
        _center(compensated, origin), fz, fy, fx, (dz, dy, dx), origin
    )
    return response, {
        "bead_profile": {
            "source": "supplied_relative_site_weights",
            "supplied": supplied,
            "applied": normalized,
            "normalization": "exact_converted_sum",
        },
        "min_profile_transfer": minimum,
        "profile_transfer": np.array(np.fft.fftshift(profile), order="C", copy=True),
        "compensated_dc": localization,
        "response_gauge": "compensated_dc_peak_with_supplied_phase_origin",
    }


def calibrate_alignment_bead(
    pair: AlignmentCameraPair,
    *,
    group: dict[str, int],
    phases_rad: npt.NDArray[Any],
    voxel_size_um: object,
    calibration_carrier_bins: object,
    bead_mode: str,
    bead_profile: npt.NDArray[Any] | None,
    min_profile_transfer: object,
    source: str,
) -> AlignmentBeadCalibration:
    """Separate one corrected bead group and calibrate its relative response.

    Every keyword is required. Group indices refer to the bead's present
    time/channel/orientation axes, including singletons. Actual phases control
    separation; supplied z/y/x spacing in micrometres controls frequency axes.
    Point mode requires both profile arguments to be None. Discrete-profile
    mode certifies and divides native P(k-m*kc) before locating a common peak.

    Corrected samples receive no further camera, exposure or sum correction.
    All orders retain signed complex amplitudes and use the original exact dc
    mass once. No physical compatibility, absolute yield or unknown setting is
    inferred. Correction metadata and original harmonics remain available.
    Inherited numerical errors propagate; caller buffers and numeric/warning
    policy are preserved. Allocation and unrelated exceptions propagate.
    """
    if not isinstance(pair, AlignmentCameraPair):
        raise SimreconError(_INVALID, "expected AlignmentCameraPair")
    if pair.status != "corrected" or pair.bead is None or pair.specimen is None:
        raise SimreconError(
            "alignment_bead_correction_unavailable", "both corrected members are required"
        )
    bead = pair.bead
    if "z" not in bead.axes:
        raise SimreconError("invalid_alignment_bead_axes", "an explicit z axis is required")
    group_axes = tuple(a for a in bead.axes if a in ("time", "channel", "orientation"))
    if type(group) is not dict or set(group) != set(group_axes):
        raise SimreconError(
            "invalid_alignment_bead_group", "group must name every present group axis"
        )
    for axis in group_axes:
        index = group[axis]
        if type(index) is not int or not 0 <= index < bead.data.shape[bead.axes.index(axis)]:
            raise SimreconError(
                "invalid_alignment_bead_group", "group index must be a plain in-range int"
            )
    if type(bead_mode) is not str or bead_mode not in ("point", "discrete_profile"):
        raise SimreconError(_INVALID, "bead mode must be point or discrete_profile")
    if bead_mode == "point":
        if bead_profile is not None or min_profile_transfer is not None:
            raise SimreconError(_INVALID, "point mode requires no profile or threshold")
    elif bead_profile is None or min_profile_transfer is None:
        raise SimreconError(_INVALID, "discrete_profile mode requires a profile and threshold")
    if not isinstance(source, str) or not source.strip():
        raise SimreconError("invalid_otf_source", "source must be a nonblank string")
    carrier = _integers(calibration_carrier_bins, 2, "invalid_empirical_transfer_carrier")
    selected_group = group.copy()
    correction = {
        "mode": pair.mode,
        "reference_sum_equalization": pair.reference_sum_equalization,
        "camera_estimate": copy.deepcopy(pair.camera_estimate),
        "bead": _frame_metadata(bead),
        "specimen": _frame_metadata(pair.specimen),
    }
    supplied_phases = phases_rad.copy(order="C") if type(phases_rad) is np.ndarray else phases_rad
    supplied_spacing = copy.deepcopy(voxel_size_um)
    supplied_profile = (
        bead_profile.copy(order="C") if type(bead_profile) is np.ndarray else bead_profile
    )
    selection = tuple(selected_group[a] if a in group_axes else slice(None) for a in bead.axes)
    with np.errstate(all="ignore"):
        components = separate_volume_phases(bead.data[selection], phases_rad=supplied_phases)
        mass = sum((_fraction(v) for v in components.dc.flat), Fraction())
        if bead_mode == "point":
            response = prepare_empirical_volume_response(
                components.dc, c1=components.c1, c2=components.c2, voxel_size_um=supplied_spacing
            )
            diagnostics = {
                "bead_profile": None,
                "min_profile_transfer": None,
                "profile_transfer": None,
                "compensated_dc": None,
                "response_gauge": "observed_dc_peak_with_supplied_phase_origin",
            }
        else:
            if mass <= 0:
                raise SimreconError(
                    "nonpositive_empirical_response_mass", "exact dc mass must be positive"
                )
            minimum = _real(min_profile_transfer, "invalid_finite_bead_transfer_threshold")
            if not 0 < minimum <= 1:
                raise SimreconError(
                    "invalid_finite_bead_transfer_threshold", "minimum must be in (0, 1]"
                )
            response, diagnostics = _discrete_response(
                components, mass, supplied_spacing, supplied_profile, carrier, minimum
            )
        applied_phases = supplied_phases.astype(np.float64, order="C", copy=True)
    return AlignmentBeadCalibration(
        components,
        response,
        {
            "model": "alignment_bead_calibration_v1",
            "source": source,
            "bead_mode": bead_mode,
            "group": selected_group,
            "output_unit": pair.output_unit,
            "gauge_source": pair.gauge_source,
            "calibration_carrier_bins": carrier,
            "correction": correction,
            "phases_rad": {
                "source": "supplied_actual",
                "supplied": supplied_phases,
                "applied": applied_phases,
            },
            "voxel_size_um": {
                "source": "supplied",
                "supplied": supplied_spacing,
                "applied": response.voxel_size_um,
            },
            "dc_mass": {
                "numerator": mass.numerator,
                "denominator": mass.denominator,
                "unit": pair.output_unit,
            },
            **diagnostics,
        },
    )


def sample_alignment_order_transfer(
    calibration: AlignmentBeadCalibration,
    *,
    order: object,
    frequencies_zyx_per_um: object,
    coordinate_offset_yx: object,
    phase_reference_shift_rad: object,
    source: str,
) -> EmpiricalFrequencySamples:
    """Sample declared detector frequencies in cycles/µm with the retained carrier.

    Coordinate offsets use calibration samples. The phase shift is the
    specimen-minus-calibration phase reference in radians. The existing sampler
    owns response validation, signed reflection, gauge removal, closed-hull
    interpolation, safe arithmetic, errors and the unchanged output schema.
    Retain this calibration separately for its upstream provenance.
    """
    if not isinstance(calibration, AlignmentBeadCalibration):
        raise SimreconError(_INVALID, "expected AlignmentBeadCalibration")
    return sample_empirical_volume_transfer(
        calibration.response,
        order=order,
        frequencies_zyx_per_um=frequencies_zyx_per_um,
        calibration_carrier_bins=calibration.provenance["calibration_carrier_bins"],
        coordinate_offset_yx=coordinate_offset_yx,
        phase_reference_shift_rad=phase_reference_shift_rad,
        source=source,
    )
