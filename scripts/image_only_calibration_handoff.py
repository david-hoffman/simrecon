"""Finite Q128 predictive handoff; global operator identification is unestablished.

Observation inference and supplied-candidate diagnostics have separate labels.
Only the declared direct alternatives are audited; no confidence certificate is
implied by a completed fit or by the finite field comparisons.
"""

from __future__ import annotations

import itertools
import math
import sys
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any, NoReturn

import numpy as np
import scipy
from numpy.typing import NDArray
from scipy import optimize
from scripts import image_only_bead_calibration as bead
from scripts.image_only_calibration_pilot import PilotCandidate
from scripts.physical_phase import _dec, _physical_pi, _transfer, _wrap

from simrecon import ScalarCameraEstimate, SimreconError

Real = NDArray[np.float64]
_D = (0.125, 0.080, 0.080)
_RANGE = "calibration_handoff_range"
_KNOWN = bead._KNOWN | {_RANGE}


@dataclass(frozen=True)
class RefinementScore:
    """One actual objective entry; unscored entries have no objective."""

    evaluation_index: int
    outcome: str
    objective: float | None


@dataclass(frozen=True)
class RefinementSummary:
    """Independent trace and unmodified optimizer termination diagnostics."""

    status: int | None
    message: str
    nfev: int | None
    njev: int | None
    objective_evaluations: int
    successful_evaluations: int
    infeasible_evaluations: int
    initial_objective: float | None
    best_objective: float | None
    best_evaluation_index: int | None
    trace: tuple[RefinementScore, ...]


@dataclass(frozen=True)
class HandoffAuditCase:
    """One direct alternative and the completed finite comparisons."""

    case_id: str
    outcome: str
    candidate: PilotCandidate | None
    calibration_max_abs_difference: float | None
    operator_max_abs_difference: float | None
    calibration_equivalent: bool | None
    material: bool | None
    reason: str
    failure_code: str | None


@dataclass(frozen=True)
class SpecimenIllumination:
    """Independent illumination payload for the physical specimen consumer."""

    carriers_yx_per_um: Real
    phases_at_specimen_origin_rad: Real
    beam_amplitudes: Real
    camera_estimate: ScalarCameraEstimate
    detector_shape_zyx: tuple[int, ...]
    detector_spacing_um_zyx: tuple[float, ...]
    source_shape_zyx: tuple[int, ...]
    source_spacing_um_zyx: tuple[float, ...]
    specimen_origin_um_zyx: tuple[float, ...]
    pupil_order: int
    illumination_source: str


@dataclass(frozen=True)
class CalibrationHandoff:
    """Frozen bindings to complete or partial finite-procedure evidence."""

    status: str
    stage: str
    reason_code: str | None
    message: str
    failure_code: str | None
    input_kind: str
    global_operator_identification: str
    candidate: PilotCandidate | None
    specimen: SpecimenIllumination | None
    seed_result: bead.BeadCalibrationResult | None
    refinement: RefinementSummary | None
    audit: tuple[HandoffAuditCase, ...]
    audit_complete: bool
    training_rms: float | None
    heldout_prediction: Real | None
    heldout_residual_mean: Real | None
    heldout_residual_rms: Real | None
    provenance: dict[str, Any]


def _invalid(message: str) -> NoReturn:
    raise SimreconError("invalid_calibration_handoff", message)


def _range(message: str) -> NoReturn:
    raise SimreconError(_RANGE, message)


def _copy(value: Any) -> Real:
    return np.array(value, dtype=np.float64, order="C", copy=True)


def _finite(value: Real, operation: str) -> Real:
    if not np.isfinite(value).all():
        _range(f"nonfinite {operation}")
    return value


def _number(value: Any, name: str) -> float:
    if type(value) not in (int, float):
        _invalid(f"{name} must be a built-in real scalar")
    try:
        result = float(value)
    except OverflowError:
        _invalid(f"{name} must normalize to finite float64")
    if not math.isfinite(result):
        _invalid(f"{name} must normalize to finite float64")
    return result


def _origin(value: Any) -> tuple[float, ...]:
    if not isinstance(value, tuple) or len(value) != 3:
        _invalid("origin must be a length-three tuple")
    return tuple(_number(v, "origin") for v in value)


def _shape(value: Any, *, calibration: bool = False) -> tuple[int, ...]:
    if (
        type(value) is not tuple
        or len(value) != 3
        or any(type(n) is not int or n <= 0 for n in value)
    ):
        _invalid("detector shape must be a built-in tuple of three positive built-in ints")
    if calibration and any(
        n * Fraction(d) < Fraction(0.100) for n, d in zip(value, _D, strict=True)
    ):
        _invalid("calibration sides must be at least 0.100 micrometres long")
    return value


def _camera(value: Any) -> ScalarCameraEstimate:
    if not isinstance(value, ScalarCameraEstimate):
        _invalid("camera_estimate must be a ScalarCameraEstimate")
    means = value.means_counts
    if (
        type(means) is not np.ndarray
        or means.dtype != np.dtype(np.float64)
        or not means.dtype.isnative
        or means.shape != (3,)
        or not np.isfinite(means).all()
    ):
        _invalid("camera means require plain finite native float64 shape (3,)")
    contrast = _number(value.contrast_counts, "contrast_counts")
    if not isinstance(value.source, str) or not value.source.strip():
        _invalid("camera source must be a nonblank string")
    return replace(value, means_counts=_copy(means), contrast_counts=contrast)


def _candidate(value: Any, shape: tuple[int, ...]) -> PilotCandidate:
    if not isinstance(value, PilotCandidate):
        _invalid("candidate must be a PilotCandidate")
    fields = {}
    for name, expected in (
        ("centers_um_zyx", (3, 3)),
        ("brightness_relative", (3,)),
        ("carriers_yx_per_um", (3, 2)),
        ("phases_rad", (3, 9)),
        ("beam_amplitudes", (3,)),
    ):
        raw = getattr(value, name)
        if type(raw) is not np.ndarray or raw.dtype.kind not in "iuf" or not np.isfinite(raw).all():
            _invalid(f"{name} must be a plain finite real numeric ndarray")
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            arr = _copy(raw)
        if arr.shape != expected or not np.isfinite(arr).all():
            _invalid(f"{name} requires shape {expected} and finite float64 conversion")
        fields[name] = arr
    if np.any(fields["brightness_relative"] < 0):
        _invalid("brightnesses must be nonnegative")
    beams = fields["beam_amplitudes"]
    if np.any(beams < 0) or not np.any(beams > 0):
        _invalid("beams must be nonnegative and not all zero")
    if not bead._geometry(fields["centers_um_zyx"], shape):
        _invalid("calibration spheres require containment and nonoverlap")
    if not bead._carrier_domain(fields["carriers_yx_per_um"]):
        _invalid("carriers must obey the physical propagating disk")
    return PilotCandidate(**fields, occupied_counts=(), stored_unit_masses_e=np.empty(0))


@dataclass(frozen=True)
class _Context:
    shape: tuple[int, ...]
    origin: tuple[float, ...]
    detector: tuple[int, ...]
    spacing: tuple[float, ...]
    destination: tuple[float, ...]
    camera: ScalarCameraEstimate
    calibration_atol: float
    operator_atol: float
    source: str

    @property
    def source_shape(self) -> tuple[int, ...]:
        return self.detector[0], 2 * self.detector[1], 2 * self.detector[2]

    @property
    def source_spacing(self) -> tuple[float, ...]:
        return self.spacing[0], self.spacing[1] / 2, self.spacing[2] / 2


def _context(
    shape: Any,
    origin: Any,
    detector: Any,
    spacing: Any,
    destination: Any,
    camera: Any,
    calibration_atol: Any,
    operator_atol: Any,
    source: Any,
) -> _Context:
    shape = _shape(shape, calibration=True)
    detector = _shape(detector)
    if type(spacing) is not tuple or len(spacing) != 3:
        _invalid("specimen spacing requires a built-in length-three tuple")
    spacing = tuple(_number(v, "specimen spacing") for v in spacing)
    if any(v <= 0 for v in spacing):
        _invalid("specimen spacing must be strictly positive")
    origin, destination = _origin(origin), _origin(destination)
    camera = _camera(camera)
    cal, op = _number(calibration_atol, "calibration_atol"), _number(operator_atol, "operator_atol")
    if cal <= 0 or op <= 0:
        _invalid("comparison tolerances must be strictly positive")
    if not isinstance(source, str) or not source.strip():
        _invalid("source must be a nonblank string")
    return _Context(shape, origin, detector, spacing, destination, camera, cal, op, source)


def _initial(ctx: _Context, kind: str, controls: dict[str, Any]) -> CalibrationHandoff:
    provenance = dict(
        model="ra12_clear_pupil_predictive_handoff_v1",
        source=ctx.source,
        global_operator_identification="unestablished",
        confidence_guarantee=None,
        output_unit="reference_flat_relative",
        pupil_order=128,
        calibration_shape_zyx=ctx.shape,
        calibration_origin_um_zyx=ctx.origin,
        specimen_detector_shape_zyx=ctx.detector,
        specimen_detector_spacing_um_zyx=ctx.spacing,
        specimen_source_shape_zyx=ctx.source_shape,
        specimen_source_spacing_um_zyx=ctx.source_spacing,
        specimen_origin_um_zyx=ctx.destination,
        camera=dict(
            means_counts=_copy(ctx.camera.means_counts),
            contrast_counts=ctx.camera.contrast_counts,
            source=ctx.camera.source,
        ),
        controls=dict(
            controls, calibration_atol=ctx.calibration_atol, operator_atol=ctx.operator_atol
        ),
        phase_transfer=dict(
            calibration_origin_um_zyx=ctx.origin,
            specimen_origin_um_zyx=ctx.destination,
            first_five_indices=(0, 1, 2, 3, 4),
            application_count=0,
        ),
        audit_scope="listed_direct_transformations_only",
        numpy_version=str(np.__version__),
        scipy_version=str(scipy.__version__),
        optics=dict(
            excitation_um=0.488,
            emission_um=0.525,
            refractive_index=1.515,
            detection_na=1.4,
            pupil="clear_matched_index_scalar",
            pixel_subsamples_yx=(2, 2),
        ),
        calibration_spacing_um_zyx=_D,
        calibration_source_refinement_zyx=(8, 8, 8),
        specimen_source_refinement_zyx=(1, 2, 2),
        phase_anchor="specimen_box_corner",
        limitations=(
            "Finite listed audit only; no exhaustive occupancy, continuous carrier, phase-branch "
            "or shared-nuisance search. Global operator identification is unestablished. "
            "No statistical confidence guarantee. Synthetic optics, float64 comparisons. "
            "Source-basis discrepancy and inverse arithmetic error remain separate; "
            "neither is certified by the illumination-field comparison."
        ),
    )
    return CalibrationHandoff(
        "unavailable",
        "seed",
        None,
        "procedure not yet completed",
        None,
        kind,
        "unestablished",
        None,
        None,
        None,
        None,
        (),
        False,
        None,
        None,
        None,
        None,
        provenance,
    )


def _representation(ctx: _Context) -> None:
    # These are actual ndarray/index representation limits, not resource caps.
    for shape in (
        tuple(8 * n for n in ctx.shape),
        ctx.source_shape,
        (3, 5, 2 * ctx.detector[0] - 1, *ctx.source_shape[1:]),
    ):
        if any(n > sys.maxsize for n in shape) or math.prod(shape) > sys.maxsize // 8:
            _range("required array shape or byte count exceeds native indexing")
    if any(d <= 0 for d in ctx.source_spacing):
        _range("specimen half-spacing is not representable as positive float64")


def _shift(
    phases: Real, multiple: float = 0, *, anchor: tuple[int, int, float, float] | None = None
) -> Real:
    with localcontext() as context:
        context.prec = 800
        offset = _dec(multiple) * _physical_pi()
        if anchor is not None:
            sign, n, d, center = anchor
            offset -= 2 * _physical_pi() * sign * _dec(center) / (Decimal(n) * _dec(d))
        return _copy([_wrap(_dec(p) + offset) for p in phases.flat]).reshape(phases.shape).copy()


class _Prediction(bead._Prediction):
    def predict(self, candidate: PilotCandidate, order: int, count: int = 9) -> tuple[Real, Real]:
        # The inherited harmonic assembly uses float64 trig; first reduce huge
        # represented phases with the physical period, without changing storage.
        return super().predict(
            replace(candidate, phases_rad=_shift(candidate.phases_rad)), order, count
        )


def _rebuild(prediction: _Prediction, c: PilotCandidate) -> PilotCandidate:
    return prediction.candidate(
        c.centers_um_zyx,
        c.brightness_relative,
        c.carriers_yx_per_um,
        c.phases_rad,
        c.beam_amplitudes,
    )


def _alternatives(c: PilotCandidate, shape: tuple[int, ...]):
    """104 direct cases, with stable family/index/sign order; no refitting."""
    swap = _copy(c.beam_amplitudes[[0, 2, 1]])
    yield (
        "global_reversal_side_exchange",
        replace(
            c,
            carriers_yx_per_um=-c.carriers_yx_per_um,
            phases_rad=_shift(-c.phases_rad),
            beam_amplitudes=swap,
        ),
    )
    yield "beam_side_exchange", replace(c, beam_amplitudes=swap)
    centers = _copy(c.centers_um_zyx)
    with localcontext() as context:
        context.prec = 800
        centers[:, 0] = [float(Decimal(shape[0]) * _dec(_D[0]) - _dec(v)) for v in centers[:, 0]]
    yield (
        "axial_center_reflection_side_exchange",
        replace(c, centers_um_zyx=centers, beam_amplitudes=swap),
    )
    # Exact represented discriminant avoids overflow/cancellation domain errors.
    with localcontext() as context:
        context.prec = 2200
        a0, ap, am = (_dec(v) for v in c.beam_amplitudes)
        disc = a0 * a0 - 4 * ap * am
        root = None
        if disc >= 0:
            norm = (a0 * a0 + ap * ap + am * am).sqrt()
            plus = (a0 + disc.sqrt()) / (2 * norm)
            # Rationalized small root also retains highly unequal valid beams.
            minus = 2 * ap * am / (norm * (a0 + disc.sqrt())) if a0 + disc.sqrt() else Decimal(0)
            root = _copy([float((ap + am) / norm), float(plus), float(minus)])
    yield "alternate_beam_root", None if root is None else replace(c, beam_amplitudes=root)
    yield (
        "alternate_beam_root_side_exchange",
        None if root is None else replace(c, beam_amplitudes=root[[0, 2, 1]]),
    )
    for b, a, sign in itertools.product(range(3), range(3), (-1, 1)):
        centers = _copy(c.centers_um_zyx)
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            centers[b, a] += sign * _D[a] / 8
        yield f"center_shift:{b}:{a}:{sign:+d}", replace(c, centers_um_zyx=centers)
    for o, a, sign in itertools.product(range(3), range(2), (-1, 1)):
        q, phases = _copy(c.carriers_yx_per_um), _copy(c.phases_rad)
        # Form the represented frequency through exact arithmetic; never form
        # overflowing N*D or an enormous phase addition in binary64.
        delta = float(Fraction(sign) / (shape[a + 1] * Fraction(_D[a + 1])))
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            q[o, a] += delta
        phases[o] = _shift(
            c.phases_rad[o],
            anchor=(sign, shape[a + 1], _D[a + 1], float(c.centers_um_zyx[0, a + 1])),
        )
        yield (
            f"carrier_box_shift:{o}:{a}:{sign:+d}",
            replace(c, carriers_yx_per_um=q, phases_rad=phases),
        )
    for o, a in itertools.product(range(3), range(2)):
        q = _copy(c.carriers_yx_per_um)
        q[o, a] *= -1
        yield f"carrier_component_reflection:{o}:{a}", replace(c, carriers_yx_per_um=q)
    for o, p in itertools.product(range(3), range(9)):
        phases = _copy(c.phases_rad)
        phases[o, p] = _shift(-c.phases_rad[o, p : p + 1])[0]
        yield f"phase_negation:{o}:{p}", replace(c, phases_rad=phases)
        phases = _copy(c.phases_rad)
        phases[o, p] = _shift(c.phases_rad[o, p : p + 1], 1)[0]
        yield f"phase_pi_addition:{o}:{p}", replace(c, phases_rad=phases)
    for o, multiple in itertools.product(range(3), (0.5, 1.0, 1.5)):
        phases = _copy(c.phases_rad)
        phases[o] = _shift(c.phases_rad[o], multiple)
        yield f"orientation_common_shift:{o}:{multiple}", replace(c, phases_rad=phases)


def _field(c: PilotCandidate, ctx: _Context) -> Real:
    """Complete normalized field on half-cells and all source-minus-focus lags.

    Decimal handles complete coordinate products and the irrational axial root
    before reduction. All trigonometric arguments passed to NumPy are bounded.
    """
    nz, ny, nx = ctx.detector
    phases = _transfer(c.phases_rad, c.carriers_yx_per_um, ctx.origin, ctx.destination)
    values = np.empty((3, 5, 2 * nz - 1, 2 * ny, 2 * nx))
    with localcontext() as context:
        # Finite binary64 products and native indices fit well inside this
        # precision; kappa uses exact-rational domain subtraction at the rim.
        context.prec = 2200
        pi = _physical_pi()
        a0, ap, am = (_dec(v) for v in c.beam_amplitudes)
        s = a0 * a0 + ap * ap + am * am
        u, v, w = (
            float(2 * a0 * (ap + am) / s),
            float(2 * a0 * (ap - am) / s),
            float(2 * ap * am / s),
        )
        for o in range(3):
            qy, qx = (_dec(q) for q in c.carriers_yx_per_um[o])
            squared = sum((Fraction(float(q)) ** 2 for q in c.carriers_yx_per_um[o]), Fraction(0))
            k0 = Fraction(1.515) / Fraction(0.488)
            remaining = k0 * k0 - squared
            root = (Decimal(remaining.numerator) / Decimal(remaining.denominator)).sqrt()
            kappa = (Decimal(squared.numerator) / Decimal(squared.denominator)) / (
                Decimal(k0.numerator) / Decimal(k0.denominator) + root
            )
            alpha = _copy(
                [_wrap(2 * pi * kappa * j * _dec(ctx.spacing[0])) for j in range(1 - nz, nz)]
            )
            ys = [
                qy * (Decimal(j) + Decimal("0.5")) * _dec(ctx.spacing[1]) / 2 for j in range(2 * ny)
            ]
            xs = [
                qx * (Decimal(j) + Decimal("0.5")) * _dec(ctx.spacing[2]) / 2 for j in range(2 * nx)
            ]
            for p in range(5):
                theta = _copy(
                    [[_wrap(2 * pi * (y + x) + _dec(phases[o, p])) for x in xs] for y in ys]
                )
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    values[o, p] = (
                        1
                        + u * np.cos(alpha)[:, None, None] * np.cos(theta)
                        + v * np.sin(alpha)[:, None, None] * np.sin(theta)
                        + w * np.cos(2 * theta)
                    )
    return _finite(values, "complete specimen illumination field")


def _max_difference(a: Real, b: Real) -> float:
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        return float(np.max(_finite(np.abs(a - b), "comparison difference")))


def _audit(
    result: CalibrationHandoff,
    ctx: _Context,
    prediction: _Prediction,
    seeds: tuple[tuple[str, PilotCandidate], ...] = (),
) -> CalibrationHandoff:
    c = result.candidate
    assert c is not None
    cases = []
    reference = None
    reference_error = None
    try:
        reference = prediction.predict(c, 128)
    except SimreconError as error:
        if error.code not in _KNOWN:
            raise
        reference_error = error
    reference_field = None
    alternatives = itertools.chain(_alternatives(c, ctx.shape), seeds)
    for case_id, alt in alternatives:
        current = HandoffAuditCase(
            case_id,
            "infeasible",
            None,
            None,
            None,
            None,
            None,
            "transformed physical domain is infeasible",
            None,
        )
        if (
            alt is None
            or not bead._geometry(alt.centers_um_zyx, ctx.shape)
            or not bead._carrier_domain(alt.carriers_yx_per_um)
            or not np.isfinite(alt.beam_amplitudes).all()
            or np.any(alt.beam_amplitudes < 0)
            or not np.any(alt.beam_amplitudes > 0)
        ):
            cases.append(current)
            continue
        try:
            alt = _rebuild(prediction, alt)
            current = replace(
                current,
                outcome="numerical_incomplete",
                candidate=bead._snapshot(alt),
                reason="comparison not completed",
            )
            if reference_error is not None:
                raise reference_error
            assert reference is not None
            ac, ast = prediction.predict(alt, 128)
            delta = max(_max_difference(ac, reference[0]), _max_difference(ast, reference[1]))
            equivalent = delta <= ctx.calibration_atol
            current = replace(
                current,
                calibration_max_abs_difference=delta,
                calibration_equivalent=equivalent,
                material=False,
                outcome="calibration_distinct",
                reason="complete Q128 calibration comparison is distinct",
            )
            if equivalent:
                if reference_field is None:
                    reference_field = _field(c, ctx)
                operator_delta = _max_difference(_field(alt, ctx), reference_field)
                material = operator_delta > ctx.operator_atol
                current = replace(
                    current,
                    operator_max_abs_difference=operator_delta,
                    material=material,
                    outcome="material_alternative" if material else "equivalent_harmless",
                    reason="complete finite specimen field comparison",
                )
        except SimreconError as error:
            if error.code not in _KNOWN:
                raise
            current = replace(
                current,
                outcome="numerical_incomplete",
                material=None,
                reason=str(error),
                failure_code=error.code,
            )
        cases.append(current)
    complete = all(case.outcome != "numerical_incomplete" for case in cases)
    p = dict(
        result.provenance,
        audited_case_ids=tuple(case.case_id for case in cases),
        audited_case_count=len(cases),
    )
    result = replace(result, audit=tuple(cases), audit_complete=complete, provenance=p)
    if not complete:
        failure = next(case for case in cases if case.outcome == "numerical_incomplete")
        return replace(
            result,
            status="numerical_incomplete",
            stage="audit",
            reason_code="audit_incomplete",
            message=failure.reason,
            failure_code=failure.failure_code,
        )
    if any(case.material for case in cases):
        return replace(
            result,
            status="unavailable",
            stage="audit",
            reason_code="material_alternative",
            message="a declared calibration-equivalent alternative changes the specimen field",
        )
    return result


def _payload(result: CalibrationHandoff, ctx: _Context) -> CalibrationHandoff:
    c = result.candidate
    assert c is not None
    phases = _finite(
        _transfer(c.phases_rad, c.carriers_yx_per_um, ctx.origin, ctx.destination), "phase transfer"
    )
    payload = SpecimenIllumination(
        _copy(c.carriers_yx_per_um),
        _copy(phases),
        _copy(c.beam_amplitudes),
        _camera(ctx.camera),
        ctx.detector,
        ctx.spacing,
        ctx.source_shape,
        ctx.source_spacing,
        ctx.destination,
        128,
        ctx.source,
    )
    provenance = dict(result.provenance)
    provenance["phase_transfer"] = dict(provenance["phase_transfer"], application_count=1)
    return replace(
        result,
        specimen=payload,
        provenance=provenance,
        status=(
            "predictive_estimate"
            if result.input_kind == "observations_only"
            else "diagnostic_candidate"
        ),
        stage="complete",
        reason_code=None,
        failure_code=None,
        message="finite predictive procedure completed; global identification is unestablished",
    )


def _failure(result: CalibrationHandoff, stage: str, error: SimreconError) -> CalibrationHandoff:
    if error.code not in _KNOWN:
        raise error
    return replace(
        result,
        status="numerical_incomplete",
        stage=stage,
        reason_code="numerical_range",
        message=str(error),
        failure_code=error.code,
        specimen=None,
    )


def audit_calibration_candidate(
    candidate: Any,
    *,
    calibration_shape_zyx: Any,
    calibration_origin_um_zyx: Any,
    specimen_detector_shape_zyx: Any,
    specimen_detector_spacing_um_zyx: Any,
    specimen_origin_um_zyx: Any,
    camera_estimate: Any,
    calibration_atol: Any,
    operator_atol: Any,
    source: Any,
) -> CalibrationHandoff:
    """Audit a supplied candidate, independently of any observation inference."""
    ctx = _context(
        calibration_shape_zyx,
        calibration_origin_um_zyx,
        specimen_detector_shape_zyx,
        specimen_detector_spacing_um_zyx,
        specimen_origin_um_zyx,
        camera_estimate,
        calibration_atol,
        operator_atol,
        source,
    )
    c = _candidate(candidate, ctx.shape)
    result = _initial(
        ctx,
        "supplied_candidate_diagnostic",
        dict(sweep_scales=None, max_refinement_evaluations=None, training_rms_limit=None),
    )
    if ctx.camera.contrast_counts <= 0:
        return replace(
            result,
            reason_code="normalization_unavailable",
            message="nonpositive estimated contrast",
        )
    try:
        _representation(ctx)
    except SimreconError as error:
        return _failure(result, "specimen_geometry", error)
    prediction = _Prediction(ctx.shape)
    try:
        result = replace(result, candidate=_rebuild(prediction, c))
    except SimreconError as error:
        return _failure(result, "audit", error)
    result = _audit(result, ctx, prediction)
    if not result.audit_complete or any(case.material for case in result.audit):
        return result
    try:
        return _payload(result, ctx)
    except SimreconError as error:
        return _failure(result, "transfer", error)


class _Refinement:
    """One fixed-center least-squares run, with an independent entry ledger."""

    def __init__(
        self,
        seed: bead.BeadCalibrationResult,
        central: Real,
        structured: Real,
        prediction: _Prediction,
    ) -> None:
        assert seed.frozen_candidate is not None and seed.frozen_coordinates is not None
        assert seed.initial_candidate is not None
        self.seed = seed
        self.central, self.structured = central, structured
        self.prediction = prediction
        self.start = _copy(seed.initial_candidate.brightness_relative)
        self.coordinates = _copy(seed.frozen_coordinates)
        self.trace: list[RefinementScore] = []
        self.best: PilotCandidate | None = None
        self.best_objective: float | None = None
        self.best_index: int | None = None
        self.evaluated: set[tuple[float, ...]] = set()
        self.optimizer: Any = None
        self.message = "refinement not completed"
        self.m = 28 * central.size

    def score(self, c: PilotCandidate) -> Real:
        """Exactly one actual objective entry, successful or numerical incomplete."""
        index = len(self.trace)
        try:
            pc, ps = self.prediction.predict(c, 128)
            with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
                rc = _finite(pc - self.central, "central residual")
                rs = _finite(ps - self.structured, "structured residual")
                objective = float(
                    (np.sum(rc**2, dtype=np.float64) + np.sum(rs**2, dtype=np.float64))
                    / (2 * self.m)
                )
                residual = _finite(
                    np.concatenate((rc.ravel(), rs.ravel())) / math.sqrt(self.m),
                    "scaled training residual",
                )
            if not math.isfinite(objective) or objective < 0:
                _range("nonfinite or negative training objective")
        except SimreconError as error:
            if error.code not in _KNOWN:
                raise
            self.trace.append(RefinementScore(index, "numerical_incomplete", None))
            raise
        self.trace.append(RefinementScore(index, "scored", objective))
        if self.best_objective is None or objective < self.best_objective:
            self.best, self.best_objective, self.best_index = bead._snapshot(c), objective, index
        return residual

    def objective(self, x: Real) -> Real:
        z = _copy(self.coordinates)
        z[9:] = x
        self.evaluated.add(tuple(float(v) for v in x))
        try:
            q = bead._carriers(z)
            if not bead._bounds(z) or not bead._carrier_domain(q):
                self.trace.append(RefinementScore(len(self.trace), "infeasible", None))
                # A finite penalty for SciPy only. It is never a scored model,
                # has no optical objective, and cannot be retained as best.
                return np.full(self.m, 1e100)
            candidate = bead._decode(z, self.start, self.prediction)
        except SimreconError as error:
            if error.code not in _KNOWN:
                raise
            self.trace.append(RefinementScore(len(self.trace), "numerical_incomplete", None))
            raise
        return self.score(candidate)

    def run(self, limit: int) -> None:
        assert self.seed.frozen_candidate is not None
        # Rescore the exact frozen physical seed first, before any decoder
        # rounding or optimizer boundary adjustment. Ties retain this entry.
        self.score(_rebuild(self.prediction, self.seed.frozen_candidate))
        lower = np.full(38, -1.0)
        upper = np.ones(38)
        lower[:6] = 0
        lower[[7, 9]] = 0
        upper[:3] = 100
        self.optimizer = optimize.least_squares(
            self.objective, _copy(self.coordinates[9:]), bounds=(lower, upper), max_nfev=limit
        )
        self.message = str(self.optimizer.message)
        if tuple(float(v) for v in self.optimizer.x) not in self.evaluated:
            self.objective(self.optimizer.x)

    def summary(self) -> RefinementSummary:
        optimizer = self.optimizer
        return RefinementSummary(
            None if optimizer is None else int(optimizer.status),
            self.message,
            None if optimizer is None else int(optimizer.nfev),
            None if optimizer is None or optimizer.njev is None else int(optimizer.njev),
            len(self.trace),
            sum(s.outcome == "scored" for s in self.trace),
            sum(s.outcome == "infeasible" for s in self.trace),
            self.trace[0].objective if self.trace else None,
            self.best_objective,
            self.best_index,
            tuple(self.trace),
        )


def infer_calibration_handoff(
    central_counts: Any,
    *,
    structured_counts: Any,
    heldout_counts: Any,
    camera_estimate: Any,
    calibration_origin_um_zyx: Any,
    specimen_detector_shape_zyx: Any,
    specimen_detector_spacing_um_zyx: Any,
    specimen_origin_um_zyx: Any,
    sweep_scales: Any,
    max_refinement_evaluations: Any,
    training_rms_limit: Any,
    calibration_atol: Any,
    operator_atol: Any,
    source: Any,
) -> CalibrationHandoff:
    """Infer from raw observations and an estimated camera; freeze before holdout."""
    central = bead._array(central_counts, "central_counts")
    structured = bead._array(structured_counts, "structured_counts")
    heldout = bead._array(heldout_counts, "heldout_counts")
    if central.ndim != 3:
        _invalid("central_counts requires three dimensions")
    ctx = _context(
        central.shape,
        calibration_origin_um_zyx,
        specimen_detector_shape_zyx,
        specimen_detector_spacing_um_zyx,
        specimen_origin_um_zyx,
        camera_estimate,
        calibration_atol,
        operator_atol,
        source,
    )
    if structured.shape != (3, 9, *central.shape) or heldout.shape != (3, 5, *central.shape):
        _invalid("structured/heldout require shapes (3,9,*N)/(3,5,*N)")
    if type(sweep_scales) is not tuple or not sweep_scales:
        _invalid("sweep_scales requires a nonempty built-in tuple")
    scales = tuple(_number(v, "sweep scale") for v in sweep_scales)
    if any(v <= 0 for v in scales):
        _invalid("sweep scales must be strictly positive")
    if type(max_refinement_evaluations) is not int or max_refinement_evaluations <= 0:
        _invalid("max_refinement_evaluations requires a positive built-in int")
    limit = _number(training_rms_limit, "training_rms_limit")
    if limit < 0:
        _invalid("training_rms_limit must be nonnegative")
    controls = dict(
        sweep_scales=scales,
        max_refinement_evaluations=max_refinement_evaluations,
        training_rms_limit=limit,
    )
    result = _initial(ctx, "observations_only", controls)
    seed = bead.fit_bead_calibration(
        central,
        structured_counts=structured,
        heldout_counts=heldout,
        camera_estimate=ctx.camera,
        origin_um_zyx=ctx.origin,
        sweep_scales=scales,
    )
    result = replace(result, seed_result=seed)
    # Only the training checkpoint's existence and completion matter here.
    # Seed holdout arrays, values and summaries are never read for selection.
    training_ready = (
        seed.frozen_candidate is not None
        and seed.frozen_coordinates is not None
        and seed.initial_candidate is not None
        and all(v is not None for v in seed.training_objectives_q128_q256_q512)
    )
    if not training_ready:
        if seed.status == "numerical_incomplete":
            return replace(
                result,
                status="numerical_incomplete",
                stage="seed",
                reason_code="seed_incomplete",
                failure_code=seed.failure_code,
                message=seed.message,
            )
        return replace(result, reason_code=seed.status, message=seed.message)
    prediction = _Prediction(ctx.shape)
    try:
        _representation(ctx)
    except SimreconError as error:
        return _failure(result, "specimen_geometry", error)
    # The seed's training correction already succeeded; repeat in the same
    # camera gauge to define this new Q128 objective, without using its scores.
    y = bead._correct(central, float(ctx.camera.means_counts[1]), ctx.camera.contrast_counts)
    training = bead._correct(
        structured, float(ctx.camera.means_counts[1]), ctx.camera.contrast_counts
    )
    refinement = _Refinement(seed, y, training, prediction)
    try:
        refinement.run(max_refinement_evaluations)
    except SimreconError as error:
        if error.code not in _KNOWN:
            raise
        refinement.message = str(error)
        summary = refinement.summary()
        result = replace(
            result,
            candidate=refinement.best,
            refinement=summary,
            training_rms=None
            if summary.best_objective is None
            else math.sqrt(2 * summary.best_objective),
        )
        return _failure(result, "refinement", error)
    summary = refinement.summary()
    assert refinement.best is not None and summary.best_objective is not None
    # This independently owned best snapshot is frozen before audit or holdout.
    result = replace(
        result,
        candidate=bead._snapshot(refinement.best),
        refinement=summary,
        training_rms=math.sqrt(2 * summary.best_objective),
    )
    assert result.training_rms is not None
    if result.training_rms > limit:
        return replace(
            result,
            stage="training_fit",
            reason_code="training_misfit",
            message="selected Q128 training RMS exceeds the declared limit",
        )
    assert seed.initial_candidate is not None and seed.frozen_candidate is not None
    result = _audit(
        result,
        ctx,
        prediction,
        (
            ("inference_seed_initial", seed.initial_candidate),
            ("inference_seed_frozen", seed.frozen_candidate),
        ),
    )
    if not result.audit_complete or any(case.material for case in result.audit):
        return result
    try:
        assert result.candidate is not None
        _, predicted = prediction.predict(result.candidate, 128, count=5)
        result = replace(result, heldout_prediction=_copy(predicted))
        corrected = bead._correct(
            heldout, float(ctx.camera.means_counts[1]), ctx.camera.contrast_counts
        )
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            residual = _finite(predicted - corrected, "held-out residual")
            mean = _finite(
                np.mean(residual, axis=(2, 3, 4), dtype=np.float64), "held-out residual mean"
            )
            rms = _finite(
                np.sqrt(np.mean(residual**2, axis=(2, 3, 4), dtype=np.float64)),
                "held-out residual RMS",
            )
        result = replace(result, heldout_residual_mean=_copy(mean), heldout_residual_rms=_copy(rms))
    except SimreconError as error:
        return _failure(result, "heldout", error)
    try:
        return _payload(result, ctx)
    except SimreconError as error:
        return _failure(result, "transfer", error)
