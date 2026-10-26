"""Finite, score-first specimen fitting in reference-flat-relative units.

The optical operations remain public inverse calls. Scores use float64
residuals; the separate approximate-gradient pass explicitly rounds to float32.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, fields, replace
from fractions import Fraction
from typing import Any, NoReturn

import numpy as np
from numpy.typing import NDArray
from scripts.simulation_inverse_operator import adjoint, build_kernel_cache, forward

from simrecon import ScalarCameraEstimate, SimreconError

Array = NDArray[Any]
Shape = tuple[int, int, int]
Spacing = tuple[float, float, float]
Rows = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class SpecimenScore:
    """Bind a complete score and compact residual summaries to its candidate."""

    candidate_id: int
    data_objective: float
    penalty_objective: float
    total_objective: float
    residual_mean: Rows
    residual_rms: Rows


@dataclass(frozen=True)
class SpecimenGradientSummary:
    """Identify one complete approximate gradient and its infinity norm."""

    candidate_id: int
    max_abs: float


@dataclass(frozen=True)
class SpecimenFitAttempt:
    """Describe one entered candidate without retaining its array payload."""

    candidate_id: int
    iteration: int
    trial: int
    from_candidate_id: int | None
    gradient_candidate_id: int | None
    step: float | None
    projected_gradient_max_abs: float | None
    outcome: str
    score: SpecimenScore | None
    gradient_state: str
    gradient: SpecimenGradientSummary | None


@dataclass(frozen=True)
class SpecimenFitCall:
    """Record one actual public inverse entry and its returned outcome."""

    call_index: int
    operation: str
    purpose: str
    candidate_id: int | None
    orientation: int | None
    outcome: str
    failure_code: str | None


@dataclass(frozen=True)
class SpecimenFitCounts:
    """Bind the operation, stage and candidate counts of one invocation."""

    cache_attempted: int
    cache_completed: int
    cache_failed: int
    forward_attempted: int
    forward_completed: int
    forward_failed: int
    adjoint_attempted: int
    adjoint_completed: int
    adjoint_failed: int
    score_attempts: int
    scores_completed: int
    gradient_attempts: int
    gradients_completed: int
    seed_attempts: int
    seeds_completed: int
    iterations_started: int
    trials_attempted: int
    trials_accepted: int
    trials_rejected: int
    trials_unrepresentable: int
    trials_stagnated: int
    best_updates: int


@dataclass(frozen=True)
class SpecimenFitResult:
    """Return the best complete candidate, metadata and finite-procedure traces."""

    status: str
    stage: str
    stop_reason: str | None
    message: str
    failure_code: str | None
    failure_component: str | None
    detector_shape_zyx: Shape
    source_shape_zyx: Shape
    detector_spacing_um_zyx: Spacing
    source_spacing_um_zyx: Spacing | None
    specimen_origin_um_zyx: Spacing
    excitation_um: float
    emission_um: float
    refractive_index: float
    detection_na: float
    pixel_samples_yx: tuple[int, int]
    pupil_order: int
    regularization: float
    max_iterations: int
    max_backtracking_trials: int
    camera_means_counts: Array
    blank_counts: float
    contrast_counts: float
    camera_source: str
    carriers_yx_per_um: Array
    phases_at_specimen_origin_rad: Array
    beam_amplitudes: Array
    illumination_source: str
    source_relative: Array | None
    initial_score: SpecimenScore | None
    best_score: SpecimenScore | None
    last_complete_gradient: SpecimenGradientSummary | None
    seed_step: float | None
    attempt_trace: tuple[SpecimenFitAttempt, ...]
    call_trace: tuple[SpecimenFitCall, ...]
    counts: SpecimenFitCounts


class _Incomplete(Exception):
    def __init__(self, component: str, code: str = "image_only_specimen_fit_range") -> None:
        self.component = component
        self.code = code
        super().__init__(f"Required {component} is not representable.")


def _invalid(field: str) -> NoReturn:
    raise SimreconError("invalid_image_only_specimen_fit", f"Invalid {field}.")


def _scalar(value: Any, field: str, *, positive: bool = False) -> float:
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


def _array(value: Any, shape: tuple[int, ...] | None, field: str) -> Array:
    if type(value) is not np.ndarray or value.dtype != np.dtype("=f8") or not value.dtype.isnative:
        _invalid(field)
    if shape is None:
        if value.ndim != 5 or value.shape[:2] != (3, 5) or min(value.shape[2:]) < 1:
            _invalid(field)
    elif value.shape != shape:
        _invalid(field)
    if not np.isfinite(value).all():
        _invalid(field)
    return value


def _triple(value: Any, field: str, *, positive: bool = False) -> Spacing:
    if type(value) is not tuple or len(value) != 3:
        _invalid(field)
    # Check representation of every component before its domain.
    if any(type(v) not in (int, float) for v in value):
        _invalid(field)
    return (
        _scalar(value[0], field, positive=positive),
        _scalar(value[1], field, positive=positive),
        _scalar(value[2], field, positive=positive),
    )


def _real(value: Fraction | float, component: str) -> float:
    try:
        result = float(value)
    except OverflowError:
        raise _Incomplete(component) from None
    if not math.isfinite(result):
        raise _Incomplete(component)
    return result


def _squares(values: Array) -> Fraction:
    """Reduce squared values with an unbounded scalar exponent.

    The array arithmetic stays in float64. Only the aggregate scale is rational,
    so neither raw squares nor an unnormalized norm impose a range restriction.
    """
    maximum = float(np.max(np.abs(values)))
    if maximum == 0:
        return Fraction(0)
    exponent = math.frexp(maximum)[1]
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        scaled = np.ldexp(values.astype(np.float64, copy=False), -exponent)
        square = float(np.sum(scaled * scaled, dtype=np.float64))
    scale = Fraction(2) ** (2 * exponent)
    return Fraction(square) * scale


def _mean(values: Array) -> float:
    try:
        total = Fraction(math.fsum(float(v) for v in values.flat))
    except OverflowError:
        # fsum can overflow a partial sum even when its signed mean is finite.
        total = sum((Fraction(float(v)) for v in values.flat), Fraction(0))
    return _real(total / int(values.size), "residual_mean")


def _root(value: Fraction) -> float:
    if value == 0:
        return 0.0
    exponent = (value.numerator.bit_length() - value.denominator.bit_length()) // 2
    scaled = float(value / Fraction(2) ** (2 * exponent))
    try:
        result = math.ldexp(math.sqrt(scaled), exponent)
    except OverflowError:
        raise _Incomplete("residual_rms") from None
    return _real(result, "residual_rms")


class _Run:
    """One invocation's state; no predictions or historical sources are archived."""

    def __init__(self, raw: Array, metadata: dict[str, Any]) -> None:
        self.raw = raw
        self.meta = metadata
        self.m = int(raw.size)
        self.n = math.prod(metadata["source_shape_zyx"])
        self.reg = metadata["regularization"]
        self.counts = {field.name: 0 for field in fields(SpecimenFitCounts)}
        self.calls: list[SpecimenFitCall] = []
        self.attempts: list[SpecimenFitAttempt] = []
        self.x: Array | None = None
        self.trial: Array | None = None
        self.g: Array | None = None
        self.initial: SpecimenScore | None = None
        self.best: SpecimenScore | None = None
        self.last_gradient: SpecimenGradientSummary | None = None
        self.seed: float | None = None
        self.cache: Any = None
        self.stage = "geometry"

    def result(
        self,
        status: str,
        *,
        stop: str | None = None,
        failure: _Incomplete | None = None,
    ) -> SpecimenFitResult:
        stage = "complete" if status == "completed_finite_fit" else self.stage
        return SpecimenFitResult(
            status=status,
            stage=stage,
            stop_reason=stop,
            message=f"Specimen fit {stage}: {stop or status}.",
            failure_code=None if failure is None else failure.code,
            failure_component=None if failure is None else failure.component,
            **self.meta,
            source_relative=self.x if self.best is not None else None,
            initial_score=self.initial,
            best_score=self.best,
            last_complete_gradient=self.last_gradient,
            seed_step=self.seed,
            attempt_trace=tuple(self.attempts),
            call_trace=tuple(self.calls),
            counts=SpecimenFitCounts(**self.counts),
        )

    def call(
        self,
        operation: str,
        purpose: str,
        candidate: int | None,
        orientation: int | None,
        values: Array | None = None,
    ) -> Any:
        name = "cache" if operation == "build_kernel_cache" else operation
        self.counts[name + "_attempted"] += 1
        code = None
        answer: Any = None
        try:
            if orientation is None:
                answer = build_kernel_cache(
                    source_shape_zyx=self.meta["source_shape_zyx"],
                    source_spacing_um_zyx=self.meta["source_spacing_um_zyx"],
                    emission_um=0.525,
                    refractive_index=1.515,
                    detection_na=1.4,
                    pupil_order=self.meta["pupil_order"],
                )
            else:
                function = forward if operation == "forward" else adjoint
                answer = function(
                    values,
                    kernel_cache=self.cache,
                    carrier_yx_per_um=self.meta["carriers_yx_per_um"][orientation],
                    phases_rad=self.meta["phases_at_specimen_origin_rad"][orientation],
                    beam_amplitudes=tuple(float(a) for a in self.meta["beam_amplitudes"]),
                    excitation_um=0.488,
                )
        except SimreconError as error:
            if error.code != "simulation_inverse_operator_range":
                raise
            code = error.code
        self.counts[name + ("_completed" if code is None else "_failed")] += 1
        self.calls.append(
            SpecimenFitCall(
                len(self.calls) + 1,
                operation,
                purpose,
                candidate,
                orientation,
                "completed" if code is None else "range_failure",
                code,
            )
        )
        if code is not None:
            raise _Incomplete("dependency", code)
        return answer

    def observations(self, orientation: int) -> Array:
        blank = self.meta["blank_counts"]
        contrast = self.meta["contrast_counts"]
        counts = self.raw[orientation]
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            observation = counts - blank
            bad_difference = ~np.isfinite(observation)
            observation /= contrast
        # Repair only subtraction overflow; a large temporary is not a failure
        # of the complete normalized expression. Rational conversion rounds once.
        if bad_difference.any():
            for index in zip(*np.nonzero(bad_difference), strict=True):
                observation[index] = _real(
                    (Fraction(float(counts[index])) - Fraction(blank)) / Fraction(contrast),
                    "observations",
                )
        if not np.isfinite(observation).all():
            raise _Incomplete("observations")
        return observation

    def residual(self, x: Array, candidate: int, orientation: int, purpose: str) -> Array:
        observation = self.observations(orientation)
        prediction = self.call("forward", purpose, candidate, orientation, x)
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            prediction -= observation
        if not np.isfinite(prediction).all():
            raise _Incomplete("residual")
        return prediction

    def score(self, x: Array, candidate: int) -> SpecimenScore:
        self.counts["score_attempts"] += 1
        penalty = _real(Fraction(self.reg) * _squares(x) / (2 * self.n), "penalty_objective")
        squares = Fraction(0)
        means: list[tuple[float, ...]] = []
        rmss: list[tuple[float, ...]] = []
        for orientation in range(3):
            residual = self.residual(x, candidate, orientation, "score")
            row_means, row_rmss = [], []
            for phase in range(5):
                row_means.append(_mean(residual[phase]))
                square = _squares(residual[phase])
                row_rmss.append(_root(square / int(residual[phase].size)))
                squares += square
            means.append(tuple(row_means))
            rmss.append(tuple(row_rmss))
            del residual
        data = _real(squares / (2 * self.m), "data_objective")
        total = _real(data + penalty, "total_objective")
        self.counts["scores_completed"] += 1
        return SpecimenScore(candidate, data, penalty, total, tuple(means), tuple(rmss))

    def gradient(self, x: Array, candidate: int) -> Array:
        self.counts["gradient_attempts"] += 1
        accumulated = np.zeros(x.shape, dtype=np.float64)
        exact: Array | None = None
        for orientation in range(3):
            residual = self.residual(x, candidate, orientation, "gradient")
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                residual32 = residual.astype(np.float32)
            del residual
            if not np.isfinite(residual32).all():
                raise _Incomplete("residual32")
            value = self.call("adjoint", "gradient", candidate, orientation, residual32)
            del residual32
            # Each ordinary term is bounded by DBL_MAX/M, M>=15; their
            # three-term sum cannot overflow. Switch to exact scalar sums if
            # division would lose subnormal contributions before cancellation.
            tiny = np.finfo(np.float64).tiny * self.m
            if exact is None and np.any((value != 0) & (np.abs(value) < tiny)):
                exact = np.empty(x.shape, dtype=object)
                for j in range(x.size):
                    exact.flat[j] = Fraction(float(accumulated.flat[j]))
            if exact is None:
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    accumulated += value / self.m
            else:
                for j in range(x.size):
                    exact.flat[j] += Fraction(float(value.flat[j])) / self.m
            del value
        coefficient = Fraction(self.reg) / self.n
        # Multiplication in rational scalar arithmetic is reserved for extreme
        # scales. It avoids a prematurely underflowed lambda/N and permits a
        # large positive penalty gradient to cancel a negative data gradient.
        scale = float(coefficient)
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            term = x.astype(np.float64) * scale
            result = accumulated + term
        extreme = (
            exact is not None
            or scale < np.finfo(np.float64).tiny
            or not np.isfinite(result).all()
            or np.any((x != 0) & (term < np.finfo(np.float64).tiny))
        )
        if extreme:
            for j in range(x.size):
                data = Fraction(float(accumulated.flat[j])) if exact is None else exact.flat[j]
                result.flat[j] = _real(data + coefficient * Fraction(float(x.flat[j])), "gradient")
        if not np.isfinite(result).all():
            raise _Incomplete("gradient")
        self.counts["gradients_completed"] += 1
        self.last_gradient = SpecimenGradientSummary(candidate, float(np.max(np.abs(result))))
        return result

    def evaluate(self, x: Array, attempt: SpecimenFitAttempt, *, final: bool) -> bool:
        candidate = attempt.candidate_id
        self.stage = "initial_score" if candidate == 0 else "trial_score"
        try:
            score = self.score(x, candidate)
        except _Incomplete:
            self.attempts.append(replace(attempt, outcome="score_incomplete"))
            raise
        accepted = self.best is None or score.total_objective < self.best.total_objective
        outcome = "initial_scored" if candidate == 0 else "accepted" if accepted else "rejected"
        attempt = replace(attempt, outcome=outcome, score=score)
        self.attempts.append(attempt)
        if not accepted:
            self.counts["trials_rejected"] += 1
            return False
        self.best = score
        self.counts["best_updates"] += 1
        if candidate == 0:
            self.initial = score
            self.x = x
        else:
            self.counts["trials_accepted"] += 1
            self.x, self.trial = x, self.x
        if final:
            return True
        self.stage = "initial_gradient" if candidate == 0 else "trial_gradient"
        self.attempts[-1] = replace(attempt, gradient_state="incomplete")
        self.g = None
        self.g = self.gradient(x, candidate)
        self.attempts[-1] = replace(attempt, gradient_state="complete", gradient=self.last_gradient)
        return True

    def curvature(self) -> bool:
        assert self.g is not None
        with np.errstate(over="ignore", under="ignore", invalid="ignore"):
            direction = np.maximum(0, -self.g)
            maximum = float(np.max(direction))
            if maximum == 0:
                return False
            self.trial = (direction / maximum).astype(np.float32)
        del direction
        self.stage = "curvature_seed"
        self.counts["seed_attempts"] += 1
        numerator = _squares(self.trial)
        squares = Fraction(0)
        for orientation in range(3):
            prediction = self.call("forward", "curvature_seed", 0, orientation, self.trial)
            squares += _squares(prediction)
            del prediction
        denominator = squares / self.m + Fraction(self.reg) * numerator / self.n
        self.seed = _real(numerator / denominator, "seed_step")
        if self.seed <= 0:
            self.seed = None
            raise _Incomplete("seed_step")
        self.counts["seeds_completed"] += 1
        return True

    def project(self, step: float) -> tuple[float, bool]:
        assert self.x is not None and self.g is not None and self.trial is not None
        # This diagnostic never forms t*g or an overflowing displacement.
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            magnitude = np.where(
                self.g < 0, -self.g, np.minimum(self.g, self.x.astype(np.float64) / step)
            )
            diagnostic = float(np.max(magnitude))
            projected = self.x.astype(np.float64) - step * self.g
            np.maximum(projected, 0, out=projected)
            np.copyto(self.trial, projected, casting="unsafe")
        return diagnostic, bool(np.isfinite(self.trial).all())

    def execute(self) -> SpecimenFitResult:
        if self.meta["contrast_counts"] <= 0:
            self.stage = "normalization"
            return self.result("normalization_unavailable")
        dz, dy, dx = self.meta["detector_spacing_um_zyx"]
        spacing = (dz, dy / 2, dx / 2)
        if not all(math.isfinite(v) and v > 0 for v in spacing):
            raise _Incomplete("source_geometry")
        self.meta["source_spacing_um_zyx"] = spacing
        shape = self.meta["source_shape_zyx"]
        if any(v > sys.maxsize for v in shape) or self.n > sys.maxsize // 8:
            raise _Incomplete("source_geometry")
        self.stage = "kernel_cache"
        self.cache = self.call("build_kernel_cache", "cache", None, None)
        self.x = np.zeros(shape, dtype=np.float32)
        initial = SpecimenFitAttempt(0, 0, 0, None, None, None, None, "", None, "not_needed", None)
        self.evaluate(self.x, initial, final=False)
        if not self.curvature():
            return self.result("completed_finite_fit", stop="no_projected_direction")
        assert self.seed is not None
        step = self.seed
        for iteration in range(1, self.meta["max_iterations"] + 1):
            self.counts["iterations_started"] += 1
            for trial in range(1, self.meta["max_backtracking_trials"] + 1):
                assert self.x is not None and self.trial is not None and self.best is not None
                candidate = len(self.attempts)
                self.counts["trials_attempted"] += 1
                diagnostic, representable = self.project(step)
                attempt = SpecimenFitAttempt(
                    candidate,
                    iteration,
                    trial,
                    self.best.candidate_id,
                    self.best.candidate_id,
                    step,
                    diagnostic,
                    "",
                    None,
                    "not_needed",
                    None,
                )
                if not representable:
                    self.counts["trials_unrepresentable"] += 1
                    self.attempts.append(replace(attempt, outcome="unrepresentable"))
                elif np.array_equal(self.trial, self.x):
                    self.counts["trials_stagnated"] += 1
                    self.attempts.append(replace(attempt, outcome="stagnated"))
                    return self.result("completed_finite_fit", stop="float32_stagnation")
                elif self.evaluate(
                    self.trial, attempt, final=iteration == self.meta["max_iterations"]
                ):
                    if iteration == self.meta["max_iterations"]:
                        return self.result("completed_finite_fit", stop="iteration_limit")
                    break
                if trial == self.meta["max_backtracking_trials"]:
                    return self.result("completed_finite_fit", stop="backtracking_limit")
                self.stage = "backtracking_step"
                step /= 2
                if not math.isfinite(step) or step <= 0:
                    raise _Incomplete("step")
        raise AssertionError("Positive iteration and trial bounds must terminate.")


def fit_specimen(
    raw_counts: Any,
    *,
    camera_estimate: Any,
    carriers_yx_per_um: Any,
    phases_at_specimen_origin_rad: Any,
    beam_amplitudes: Any,
    illumination_source: Any,
    detector_spacing_um_zyx: Any,
    specimen_origin_um_zyx: Any,
    pupil_order: Any,
    regularization: Any,
    max_iterations: Any,
    max_backtracking_trials: Any,
) -> SpecimenFitResult:
    """Run the declared finite projected procedure without inferring physical gain."""
    raw = _array(raw_counts, None, "raw_counts")
    if not isinstance(camera_estimate, ScalarCameraEstimate):
        _invalid("camera_estimate")
    means = _array(camera_estimate.means_counts, (3,), "camera_estimate.means_counts")
    contrast = _scalar(camera_estimate.contrast_counts, "camera_estimate.contrast_counts")
    camera_source = _string(camera_estimate.source, "camera_estimate.source")
    carriers = _array(carriers_yx_per_um, (3, 2), "carriers_yx_per_um")
    bound = (Fraction(1.515) / Fraction(0.488)) ** 2
    for row in carriers:
        if sum((Fraction(float(v)) ** 2 for v in row), Fraction(0)) > bound:
            _invalid("carriers_yx_per_um")
    phases = _array(phases_at_specimen_origin_rad, (3, 5), "phases_at_specimen_origin_rad")
    beams = _array(beam_amplitudes, (3,), "beam_amplitudes")
    if np.any(beams < 0) or not np.any(beams > 0):
        _invalid("beam_amplitudes")
    illumination = _string(illumination_source, "illumination_source")
    spacing = _triple(detector_spacing_um_zyx, "detector_spacing_um_zyx", positive=True)
    origin = _triple(specimen_origin_um_zyx, "specimen_origin_um_zyx")
    order = _integer(pupil_order, "pupil_order")
    penalty = _scalar(regularization, "regularization", positive=True)
    iterations = _integer(max_iterations, "max_iterations")
    trials = _integer(max_backtracking_trials, "max_backtracking_trials")
    shape = tuple(int(v) for v in raw.shape[2:])
    metadata = dict(
        detector_shape_zyx=shape,
        source_shape_zyx=(shape[0], 2 * shape[1], 2 * shape[2]),
        detector_spacing_um_zyx=spacing,
        source_spacing_um_zyx=None,
        specimen_origin_um_zyx=origin,
        excitation_um=0.488,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pixel_samples_yx=(2, 2),
        pupil_order=order,
        regularization=penalty,
        max_iterations=iterations,
        max_backtracking_trials=trials,
        camera_means_counts=np.array(means, dtype=np.float64, order="C", copy=True),
        blank_counts=float(means[1]),
        contrast_counts=contrast,
        camera_source=camera_source,
        carriers_yx_per_um=np.array(carriers, dtype=np.float64, order="C", copy=True),
        phases_at_specimen_origin_rad=np.array(phases, dtype=np.float64, order="C", copy=True),
        beam_amplitudes=np.array(beams, dtype=np.float64, order="C", copy=True),
        illumination_source=illumination,
    )
    run = _Run(raw, metadata)
    try:
        return run.execute()
    except _Incomplete as failure:
        return run.result("numerical_incomplete", failure=failure)
