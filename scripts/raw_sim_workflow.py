"""Compose raw camera estimation, predictive calibration and finite specimen fitting."""

from __future__ import annotations

import hashlib
import math
import platform
from collections.abc import Iterator
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, NoReturn, cast

import numpy as np
import scipy
from numpy.typing import NDArray
from scripts.image_only_calibration_handoff import CalibrationHandoff, infer_calibration_handoff
from scripts.image_only_specimen_fit import SpecimenFitResult, fit_specimen

from simrecon import ScalarCameraEstimate, SimreconError, estimate_scalar_camera

_CALIBRATION_SPACING = (0.125, 0.080, 0.080)


@dataclass(frozen=True)
class RawSIMWorkflowResult:
    """Bind reached component records and independent in-memory provenance."""

    status: str
    stage: str
    reason_code: str | None
    failure_code: str | None
    message: str
    camera_estimate: ScalarCameraEstimate | None
    handoff: CalibrationHandoff | None
    specimen_fit: SpecimenFitResult | None
    provenance: dict[str, Any]


def _invalid(field: str) -> NoReturn:
    raise SimreconError("invalid_raw_sim_workflow", f"Invalid {field}.")


def _number(value: Any, field: str, *, positive: bool = False) -> float:
    if type(value) not in (int, float):
        _invalid(field)
    try:
        result = float(value)
    except OverflowError:
        _invalid(field)
    if not math.isfinite(result) or (positive and result <= 0):
        _invalid(field)
    return result


def _integer(value: Any, field: str) -> int:
    if type(value) is not int or value <= 0:
        _invalid(field)
    return value


def _string(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        _invalid(field)
    return value


def _triple(
    value: Any, field: str, *, positive: bool = False, tuple_subclass: bool = False
) -> tuple[float, float, float]:
    if not isinstance(value, tuple) or (not tuple_subclass and type(value) is not tuple):
        _invalid(field)
    if len(value) != 3:
        _invalid(field)
    return (
        _number(value[0], field, positive=positive),
        _number(value[1], field, positive=positive),
        _number(value[2], field, positive=positive),
    )


def _array(value: Any, field: str, *, specimen: bool = False) -> NDArray[Any]:
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        _invalid(field)
    if specimen and (value.dtype != np.dtype("=f8") or not value.dtype.isnative):
        _invalid(field)
    return value


def _chunks(array: NDArray[Any]) -> Iterator[NDArray[Any]]:
    # Buffering caps even a reversed or zero-stride logical traversal. No full
    # contiguous specimen snapshot or full-size finite-mask allocation is needed.
    with np.nditer(
        array,
        flags=["external_loop", "buffered"],
        op_flags=["readonly"],
        order="C",
        buffersize=65536,
    ) as iterator:
        # NumPy's general iterator stub also includes the multiple-operand case.
        yield from cast(Iterator[NDArray[Any]], iterator)


def _identity(array: NDArray[Any], axes: str) -> dict[str, Any]:
    digest = hashlib.sha256()
    for chunk in _chunks(array):
        digest.update(chunk.tobytes(order="C"))
    return dict(
        shape=tuple(array.shape),
        dtype=array.dtype.str,
        nbytes=array.nbytes,
        sha256=digest.hexdigest(),
        axes=axes,
    )


def _finite_values(array: NDArray[Any], field: str) -> None:
    for chunk in _chunks(array):
        if not np.isfinite(chunk).all():
            _invalid(field)
        # Finite underflow and conversion rounding are legal. Only conversion
        # range events are suppressed here; unrelated warning categories survive.
        with np.errstate(all="ignore"):
            normalized = chunk.astype(np.float64, copy=False)
        if not np.isfinite(normalized).all():
            _invalid(field)


def reconstruct_raw_sim(
    specimen_counts: Any,
    *,
    dark_counts: Any,
    blank_counts: Any,
    flat_counts: Any,
    central_counts: Any,
    structured_counts: Any,
    heldout_counts: Any,
    calibration_id: Any,
    specimen_calibration_id: Any,
    calibration_origin_um_zyx: Any,
    specimen_detector_spacing_um_zyx: Any,
    specimen_origin_um_zyx: Any,
    sweep_scales: Any,
    max_refinement_evaluations: Any,
    training_rms_limit: Any,
    calibration_atol: Any,
    operator_atol: Any,
    regularization: Any,
    max_iterations: Any,
    max_backtracking_trials: Any,
    source: Any,
) -> RawSIMWorkflowResult:
    """Run the RA13 finite observation-only composition without a recovery claim."""
    specimen = _array(specimen_counts, "specimen_counts", specimen=True)
    if specimen.ndim != 5 or specimen.shape[:2] != (3, 5) or min(specimen.shape[2:]) < 1:
        _invalid("specimen_counts")
    camera_arrays = dict(
        dark_counts=_array(dark_counts, "dark_counts"),
        blank_counts=_array(blank_counts, "blank_counts"),
        flat_counts=_array(flat_counts, "flat_counts"),
    )
    for name, array in camera_arrays.items():
        if (
            array.ndim != 3
            or array.shape[0] < 2
            or min(array.shape[1:]) < 1
            or array.shape[1] * array.shape[2] < 2
            or array.shape[1:] != camera_arrays["dark_counts"].shape[1:]
        ):
            _invalid(name)
    calibration_arrays = dict(
        central_counts=_array(central_counts, "central_counts"),
        structured_counts=_array(structured_counts, "structured_counts"),
        heldout_counts=_array(heldout_counts, "heldout_counts"),
    )
    central = calibration_arrays["central_counts"]
    if (
        central.ndim != 3
        or min(central.shape) < 1
        or any(
            n * Fraction(d) < Fraction(0.100)
            for n, d in zip(central.shape, _CALIBRATION_SPACING, strict=True)
        )
    ):
        _invalid("central_counts")
    for name, leading in (("structured_counts", (3, 9)), ("heldout_counts", (3, 5))):
        if calibration_arrays[name].shape != (*leading, *central.shape):
            _invalid(name)
    calibration_id = _string(calibration_id, "calibration_id")
    specimen_calibration_id = _string(specimen_calibration_id, "specimen_calibration_id")
    if calibration_id != specimen_calibration_id:
        _invalid("specimen_calibration_id / calibration_id pairing")
    source = _string(source, "source")
    calibration_origin = _triple(
        calibration_origin_um_zyx, "calibration_origin_um_zyx", tuple_subclass=True
    )
    specimen_origin = _triple(specimen_origin_um_zyx, "specimen_origin_um_zyx")
    spacing = _triple(
        specimen_detector_spacing_um_zyx, "specimen_detector_spacing_um_zyx", positive=True
    )
    if type(sweep_scales) is not tuple or not sweep_scales:
        _invalid("sweep_scales")
    scales = tuple(_number(v, "sweep_scales", positive=True) for v in sweep_scales)
    refinement_limit = _integer(max_refinement_evaluations, "max_refinement_evaluations")
    training_limit = _number(training_rms_limit, "training_rms_limit")
    if training_limit < 0:
        _invalid("training_rms_limit")
    cal_atol = _number(calibration_atol, "calibration_atol", positive=True)
    op_atol = _number(operator_atol, "operator_atol", positive=True)
    penalty = _number(regularization, "regularization", positive=True)
    iterations = _integer(max_iterations, "max_iterations")
    trials = _integer(max_backtracking_trials, "max_backtracking_trials")
    arrays = dict(specimen_counts=specimen, **camera_arrays, **calibration_arrays)
    # Hash the original representation before any float64 normalization.
    inputs = {
        name: _identity(
            array,
            "frame,y,x"
            if name in camera_arrays
            else ("z,y,x" if name == "central_counts" else "orientation,phase,z,y,x"),
        )
        for name, array in arrays.items()
    }
    for name, array in arrays.items():
        _finite_values(array, name)
    detector_shape = tuple(specimen.shape[2:])
    provenance = dict(
        schema="ra13.raw_sim_workflow.v1",
        source=source,
        calibration_id=calibration_id,
        specimen_calibration_id=specimen_calibration_id,
        inputs=inputs,
        geometry=dict(
            calibration_origin_um_zyx=calibration_origin,
            calibration_spacing_um_zyx=_CALIBRATION_SPACING,
            calibration_shape_zyx=tuple(central.shape),
            specimen_detector_shape_zyx=detector_shape,
            specimen_detector_spacing_um_zyx=spacing,
            specimen_origin_um_zyx=specimen_origin,
            specimen_source_shape_zyx=(
                detector_shape[0],
                2 * detector_shape[1],
                2 * detector_shape[2],
            ),
        ),
        controls=dict(
            sweep_scales=scales,
            max_refinement_evaluations=refinement_limit,
            training_rms_limit=training_limit,
            calibration_atol=cal_atol,
            operator_atol=op_atol,
            regularization=penalty,
            max_iterations=iterations,
            max_backtracking_trials=trials,
        ),
        units=dict(
            detector="counts",
            source="integrated reference-flat-relative source weights",
            geometry="micrometres",
            phases="radians",
            carriers="cycles per micrometre",
        ),
        model=dict(
            calibration="RA12 v1.1 finite clear-pupil three-beam synthetic model",
            specimen="specimen-fit v1 finite physical model",
            excitation_um=0.488,
            emission_um=0.525,
            refractive_index=1.515,
            detection_na=1.4,
            pixel_samples_yx=(2, 2),
            pupil_order=128,
            calibration_spheres=3,
            sphere_radius_um=0.050,
            calibration_source_refinement_zyx=(8, 8, 8),
            source_coordinates="half-cell coordinates; spacing (Dz,Dy/2,Dx/2)",
            phase_gauge=(
                "common gauge; first-five physical phases transferred once to specimen origin"
            ),
            acquisition="stationary scalar camera, common dose and known registration",
        ),
        versions=dict(
            python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__
        ),
        limits=(
            "Finite procedure only; global physical source and operator identification "
            "unestablished. "
            "No convergence, statistical confidence, instrument accuracy, resolution or recovery "
            "guarantee. Synthetic model only, not empirical instrument calibration. Noisy fits "
            "remain diagnostic; completed finite execution is not noiseless-control certification."
        ),
    )
    try:
        camera = estimate_scalar_camera(
            dark_counts, blank_counts=blank_counts, flat_counts=flat_counts, source=source
        )
    except SimreconError as error:
        if error.code != "scalar_camera_calibration_range":
            raise
        return RawSIMWorkflowResult(
            "numerical_incomplete",
            "camera",
            None,
            error.code,
            str(error),
            None,
            None,
            None,
            provenance,
        )
    handoff = infer_calibration_handoff(
        central_counts,
        structured_counts=structured_counts,
        heldout_counts=heldout_counts,
        camera_estimate=camera,
        calibration_origin_um_zyx=calibration_origin,
        specimen_detector_shape_zyx=detector_shape,
        specimen_detector_spacing_um_zyx=spacing,
        specimen_origin_um_zyx=specimen_origin,
        sweep_scales=scales,
        max_refinement_evaluations=refinement_limit,
        training_rms_limit=training_limit,
        calibration_atol=cal_atol,
        operator_atol=op_atol,
        source=source,
    )
    if handoff.status != "predictive_estimate" or handoff.specimen is None:
        return RawSIMWorkflowResult(
            handoff.status,
            "handoff",
            handoff.reason_code,
            handoff.failure_code,
            handoff.message,
            camera,
            handoff,
            None,
            provenance,
        )
    descriptor = handoff.specimen
    fit = fit_specimen(
        specimen_counts,
        camera_estimate=descriptor.camera_estimate,
        carriers_yx_per_um=descriptor.carriers_yx_per_um,
        phases_at_specimen_origin_rad=descriptor.phases_at_specimen_origin_rad,
        beam_amplitudes=descriptor.beam_amplitudes,
        illumination_source=descriptor.illumination_source,
        detector_spacing_um_zyx=descriptor.detector_spacing_um_zyx,
        specimen_origin_um_zyx=descriptor.specimen_origin_um_zyx,
        pupil_order=descriptor.pupil_order,
        regularization=penalty,
        max_iterations=iterations,
        max_backtracking_trials=trials,
    )
    if fit.status == "completed_finite_fit":
        return RawSIMWorkflowResult(
            "completed_finite_fit",
            "complete",
            None,
            None,
            "Finite specimen fit completed; convergence and recovery are not established.",
            camera,
            handoff,
            fit,
            provenance,
        )
    return RawSIMWorkflowResult(
        "unavailable" if fit.status == "normalization_unavailable" else fit.status,
        "specimen",
        fit.stop_reason,
        fit.failure_code,
        fit.message,
        camera,
        handoff,
        fit,
        provenance,
    )
