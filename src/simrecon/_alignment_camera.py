"""Compose explicit paired camera correction and reference-exposure division."""

import copy
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from ._acquisition import RawAcquisition
from ._array_validation import conversion_errors
from ._linear_response import _coefficient, _normalized_array, correct_linear_response
from ._model import SimreconError
from ._scalar_camera_calibration import ScalarCameraEstimate

_Factor = float | npt.NDArray[np.float64]
_Coefficient = int | float | npt.NDArray[Any]
_INVALID = "invalid_alignment_camera"
_EXPOSURE = "invalid_alignment_exposure"


@dataclass(frozen=True)
class AlignmentCameraFrames:
    """Owned reference-exposure samples, source metadata and ordered provenance.

    Bindings are frozen; arrays and metadata remain mutable by convention.
    This separate record does not implicitly substitute for raw acquisitions.
    """

    data: npt.NDArray[np.float64]
    axes: tuple[str, ...]
    input_unit: str
    output_unit: str
    source_metadata: dict[str, Any]
    provenance: dict[str, Any]


@dataclass(frozen=True)
class AlignmentCameraPair:
    """Complete paired correction or unavailability with independent snapshots.

    Camera statistics describe the original calibration, without introducing
    a new noise law or certifying a physical intensity gauge.
    """

    status: str
    information_codes: tuple[str, ...]
    specimen: AlignmentCameraFrames | None
    bead: AlignmentCameraFrames | None
    mode: str
    output_unit: str
    gauge_source: str
    reference_sum_equalization: str
    specimen_exposure_factor: _Factor
    bead_exposure_factor: _Factor
    camera_estimate: ScalarCameraEstimate | None


def _exposure(value: Any, shape: tuple[int, ...]) -> tuple[Any, _Factor]:
    """Independently snapshot original and once-normalized positive factors."""
    if type(value) in (int, float):
        with conversion_errors(_EXPOSURE, "exposure cannot be converted to binary64"):
            applied = float(value)
        if not math.isfinite(applied) or applied <= 0:
            raise SimreconError(_EXPOSURE, "exposure must be finite and strictly positive")
        return value, applied
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        raise SimreconError(_EXPOSURE, "exposure must be a plain int/float or real numeric ndarray")
    if value.shape != shape:
        raise SimreconError(_EXPOSURE, "exposure map must match canonical sample shape")
    normalized = _normalized_array(value, code=_EXPOSURE)
    if not (normalized > 0).all():
        raise SimreconError(_EXPOSURE, "exposure must be strictly positive after normalization")
    return value.copy(order="C"), normalized


def _frames(
    acquisition: RawAcquisition,
    *,
    offset: _Coefficient,
    response: _Coefficient,
    exposure: tuple[Any, _Factor],
    output_unit: str,
    gauge_source: str,
    mode: str,
    camera_source: str | None,
) -> AlignmentCameraFrames:
    """Apply the public linear operation before a distinct exposure division."""
    linear = correct_linear_response(
        acquisition, offset=offset, response=response, output_unit=output_unit
    )
    with np.errstate(all="ignore"):
        data = np.divide(linear.data, exposure[1])
        if not np.isfinite(data).all():
            raise SimreconError(
                "alignment_camera_range", "exposure-corrected samples are nonfinite"
            )
    return AlignmentCameraFrames(
        data=data,
        axes=linear.axes,
        input_unit=linear.input_unit,
        output_unit=linear.output_unit,
        source_metadata=linear.source_metadata,
        provenance={
            "model": "alignment_camera_v1",
            "equation": "raw=offset+response*exposure_factor*signal",
            "gauge_source": gauge_source,
            "coefficient_origin": mode,
            "camera_source": camera_source,
            "linear_response": copy.deepcopy(linear.provenance),
            "operations": ("subtract_offset", "divide_response", "divide_exposure"),
            "exposure_factor": {
                "supplied": copy.deepcopy(exposure[0]),
                "applied": copy.deepcopy(exposure[1]),
            },
        },
    )


def correct_alignment_pair(
    specimen: RawAcquisition,
    *,
    bead: RawAcquisition,
    mode: str,
    output_unit: str,
    gauge_source: str,
    specimen_exposure_factor: _Coefficient,
    bead_exposure_factor: _Coefficient,
    reference_sum_equalization: str,
    specimen_offset: _Coefficient | None = None,
    specimen_response: _Coefficient | None = None,
    bead_offset: _Coefficient | None = None,
    bead_response: _Coefficient | None = None,
    camera_estimate: ScalarCameraEstimate | None = None,
) -> AlignmentCameraPair:
    """Correct paired raw acquisitions into one explicitly declared signal gauge.

    Parameters
    ----------
    specimen, bead : RawAcquisition
        Public specimen_sim and sim_beads records, respectively. Shapes may
        differ. Each input unit is a nonempty opaque label.
    mode : str
        Exactly declared or estimated. Estimated mode uses one scalar camera
        record's blank mean and flat contrast for both members.
    output_unit, gauge_source : str
        Nonblank labels retained exactly. Estimated output units must be
        reference_flat_relative, with identical input count-unit labels.
    specimen_exposure_factor, bead_exposure_factor : int, float or numpy.ndarray
        Positive finite dimensionless factors relative to one reference
        exposure. Arrays must match each member's full canonical shape.
    reference_sum_equalization : str
        Disabled performs no sum normalization; per_frame_sum is unavailable.
    specimen_offset, specimen_response, bead_offset, bead_response : optional
        All required in declared mode, all None in estimated mode. Each offset
        includes the applicable background. Responses are positive raw units
        per output unit at the reference exposure. Scalars are constant;
        plain real arrays must match the corresponding full canonical shape.
    camera_estimate : ScalarCameraEstimate, optional
        Required only in estimated mode. Its full independent snapshot retains
        noise, repeatability, gain and source statistics without reinterpretation.

    Returns
    -------
    AlignmentCameraPair
        Both corrected members, or neither when unavailable. Nonpositive
        estimated contrast, changed estimated exposure and per-frame sum
        equalization have ordered information codes, including all that apply.

    Raises
    ------
    SimreconError
        Invalid declarations use invalid_alignment_camera; invalid exposure
        uses invalid_alignment_exposure. Existing linear domain/range codes
        propagate; nonfinite final division uses alignment_camera_range.

    Notes
    -----
    Apply the real linear correction, then divide by exposure in binary64.
    Signed samples, subnormals and signed underflow are valid. Unavailable
    paths validate domains without evaluating correction arithmetic. Estimated
    mode requires every converted factor to equal one. Labels and calibration
    IDs assert no physical compatibility. No scale fitting, photon inference,
    uncertainty weighting or extra background subtraction is performed.
    Caller storage, NumPy error modes and warning policy are preserved;
    MemoryError and unrelated exceptions propagate. Corrected arrays are an
    explicit boundary: avoid a second blank/contrast normalization in fitters.
    """
    for acquisition, kind in ((specimen, "specimen_sim"), (bead, "sim_beads")):
        if not isinstance(acquisition, RawAcquisition) or acquisition.acquisition_kind != kind:
            raise SimreconError(_INVALID, "expected specimen_sim and sim_beads raw acquisitions")
        if type(acquisition.intensity_unit) is not str or not acquisition.intensity_unit:
            raise SimreconError(_INVALID, "each acquisition requires a nonempty input unit")
    if type(mode) is not str or mode not in ("declared", "estimated"):
        raise SimreconError(_INVALID, "mode must be declared or estimated")
    for label in (output_unit, gauge_source):
        if type(label) is not str or not label.strip():
            raise SimreconError(_INVALID, "output unit and gauge source must be nonblank strings")
    if type(reference_sum_equalization) is not str or reference_sum_equalization not in (
        "disabled",
        "per_frame_sum",
    ):
        raise SimreconError(_INVALID, "unknown reference sum equalization selector")

    coefficients = (specimen_offset, specimen_response, bead_offset, bead_response)
    if mode == "declared":
        if (
            camera_estimate is not None
            or specimen_offset is None
            or specimen_response is None
            or bead_offset is None
            or bead_response is None
        ):
            raise SimreconError(
                _INVALID, "declared mode requires four coefficients and no estimate"
            )
    else:
        if not isinstance(camera_estimate, ScalarCameraEstimate) or any(
            value is not None for value in coefficients
        ):
            raise SimreconError(
                _INVALID, "estimated mode requires one estimate and no coefficients"
            )
        if output_unit != "reference_flat_relative":
            raise SimreconError(_INVALID, "estimated mode requires reference_flat_relative units")
        if specimen.intensity_unit != bead.intensity_unit:
            raise SimreconError(
                _INVALID, "one scalar estimate requires identical input count units"
            )
        specimen_offset = bead_offset = float(camera_estimate.means_counts[1])
        specimen_response = bead_response = camera_estimate.contrast_counts

    specimen_exposure = _exposure(specimen_exposure_factor, specimen.data.shape)
    bead_exposure = _exposure(bead_exposure_factor, bead.data.shape)
    codes = []
    if reference_sum_equalization == "per_frame_sum":
        codes.append("reference_sum_equalization_unavailable")
    if camera_estimate is not None:
        if not all(np.all(entry[1] == 1) for entry in (specimen_exposure, bead_exposure)):
            codes.append("estimated_exposure_unavailable")
        if camera_estimate.contrast_counts <= 0:
            codes.append("nonpositive_flat_contrast")

    specimen_frames = bead_frames = None
    members = (
        (specimen, specimen_offset, specimen_response, specimen_exposure),
        (bead, bead_offset, bead_response, bead_exposure),
    )
    if codes:
        for acquisition, offset, response, _ in members:
            # Validate the primitive domain without invoking subtraction/division.
            _normalized_array(acquisition.data, code="invalid_linear_response_data")
            if mode == "declared":
                _coefficient(offset, name="offset", shape=acquisition.data.shape)
                _coefficient(response, name="response", shape=acquisition.data.shape)
    else:
        specimen_frames, bead_frames = (
            _frames(
                acquisition,
                offset=offset,
                response=response,
                exposure=exposure,
                output_unit=output_unit,
                gauge_source=gauge_source,
                mode=mode,
                camera_source=camera_estimate.source if camera_estimate is not None else None,
            )
            for acquisition, offset, response, exposure in members
        )

    return AlignmentCameraPair(
        status="unavailable" if codes else "corrected",
        information_codes=tuple(codes),
        specimen=specimen_frames,
        bead=bead_frames,
        mode=mode,
        output_unit=output_unit,
        gauge_source=gauge_source,
        reference_sum_equalization=reference_sum_equalization,
        specimen_exposure_factor=specimen_exposure[1],
        bead_exposure_factor=bead_exposure[1],
        camera_estimate=copy.deepcopy(camera_estimate),
    )
