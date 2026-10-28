"""Deterministic image-only fitting of three finite midpoint spheres.

Brightness is reference-flat-relative. Detection uses the unchanged finite
clear-pupil engine; polling, decoding and evidence are specific to this module.
No truth, optimizer stopping criterion or held-out fitting term is used.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, NoReturn

import numpy as np
import scipy
from numpy.typing import NDArray
from scipy import ndimage
from scripts import image_only_calibration_pilot as pilot
from scripts.image_only_calibration_pilot import PilotCandidate

from simrecon import ScalarCameraEstimate, SimreconError

Real = NDArray[np.float64]
_D = (0.125, 0.080, 0.080)
_RADIUS = 0.050
_K0 = Fraction(1.515) / Fraction(0.488)
_RANGE = "image_only_bead_calibration_range"
_KNOWN = {
    _RANGE,
    "simulation_source_range",
    "simulation_optics_range",
    "image_only_calibration_pilot_range",
}
_EPS = np.finfo(np.float64).eps
_CODES = (
    "unchanged_coordinate",
    "unchanged_parameter",
    "occupancy_equivalent_center",
    "zero_brightness_center",
    "zero_carrier_angle",
    "single_beam_illumination",
    "zero_total_brightness",
    "equal_computed_objective",
)
_STEPS = np.array(
    [
        *(_D[a] / 8 for _ in range(3) for a in range(3)),
        0.1,
        0.1,
        0.1,
        0.05,
        0.05,
        *([0.01] * 6),
        *([0.05] * 27),
    ]
)


@dataclass(frozen=True)
class BeadCalibrationScore:
    """One completed or numerically failed score attempt."""

    stage: str
    pupil_order: int
    coordinates: Real | None
    candidate: PilotCandidate | None
    objective: float | None
    outcome: str
    failure_code: str | None


@dataclass(frozen=True)
class BeadCalibrationAttempt:
    """One signed poll and its eventual paired decision, if completed."""

    sweep_index: int
    coordinate_index: int
    sign: int
    base_score_index: int
    trial_coordinates: Real | None
    coordinate_changed: bool | None
    parameter_changed: bool | None
    outcome: str
    infeasibility_reason: str | None
    score_index: int | None
    selected: bool | None
    information_codes: tuple[str, ...]
    failure_code: str | None


@dataclass(frozen=True)
class BeadCoordinateEvidence:
    """Represented exploration and literal information limits per coordinate."""

    coordinate_index: int
    attempt_count: int
    scored_count: int
    distinct_coordinate_scored_count: int
    distinct_parameter_scored_count: int
    selected_count: int
    information_codes: tuple[str, ...]


@dataclass(frozen=True)
class BeadCalibrationCounts:
    """Counts derived from the declared schedule and actual ledgers."""

    planned_poll_attempts: int
    attempted_polls: int
    scored_polls: int
    infeasible_polls: int
    numerical_incomplete_polls: int
    completed_pairs: int
    completed_sweeps: int
    score_attempts: int
    successful_scores: int


@dataclass(frozen=True)
class BeadCalibrationResult:
    """Independent snapshots of completed work, including partial failures."""

    status: str
    stage: str
    message: str
    failure_code: str | None
    detector_shape_zyx: tuple[int, ...]
    origin_um_zyx: tuple[float, ...]
    scipy_version: str
    camera_source: str
    blank_counts: float
    contrast_counts: float
    sweep_scales: tuple[float, ...]
    initialization_notes: str | None
    initial_candidate: PilotCandidate | None
    initial_coordinates: Real | None
    best_candidate: PilotCandidate | None
    best_coordinates: Real | None
    best_score_index: int | None
    incumbent_score_index: int | None
    frozen_candidate: PilotCandidate | None
    frozen_coordinates: Real | None
    objective_trace: tuple[BeadCalibrationScore, ...]
    poll_attempts: tuple[BeadCalibrationAttempt, ...]
    coordinate_evidence: tuple[BeadCoordinateEvidence, ...]
    unprobed_coordinates: tuple[int, ...]
    counts: BeadCalibrationCounts
    training_objectives_q128_q256_q512: tuple[float | None, ...]
    heldout_prediction: Real | None
    heldout_residual_mean: Real | None
    heldout_residual_rms: Real | None


def _invalid(message: str) -> NoReturn:
    raise SimreconError("invalid_image_only_bead_calibration", message)


def _range(message: str) -> NoReturn:
    raise SimreconError(_RANGE, message)


def _copy(value: Any) -> Real:
    return np.array(value, dtype=np.float64, order="C", copy=True)


def _snapshot(candidate: PilotCandidate) -> PilotCandidate:
    return PilotCandidate(
        _copy(candidate.centers_um_zyx),
        _copy(candidate.brightness_relative),
        _copy(candidate.carriers_yx_per_um),
        _copy(candidate.phases_rad),
        _copy(candidate.beam_amplitudes),
        candidate.occupied_counts,
        _copy(candidate.stored_unit_masses_e),
    )


def _array(value: Any, name: str) -> Real:
    if type(value) is not np.ndarray or value.dtype.kind not in "iuf":
        _invalid(f"{name} must be a plain real numeric ndarray")
    if not np.isfinite(value).all():
        _invalid(f"{name} must have finite original values")
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        result = _copy(value)
    if not np.isfinite(result).all():
        _invalid(f"{name} must normalize to finite float64")
    return result


def _number(value: Any, name: str) -> float:
    if type(value) not in (int, float):
        _invalid(f"{name} must be a plain built-in real scalar")
    try:
        result = float(value)
    except OverflowError:
        _invalid(f"{name} cannot normalize to float64")
    if not math.isfinite(result):
        _invalid(f"{name} must be finite")
    return result


def _finite(value: Real, operation: str) -> Real:
    if not np.isfinite(value).all():
        _range(f"nonfinite {operation}")
    return value


def _correct(raw: Real, blank: float, contrast: float) -> Real:
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        return _finite((raw - blank) / contrast, "camera correction")


def _upper(n: int, spacing: float) -> float:
    exact = n * Fraction(spacing) - Fraction(_RADIUS)
    value = float(exact)
    return math.nextafter(value, -math.inf) if Fraction(value) > exact else value


def _geometry(centers: Real, shape: tuple[int, ...]) -> bool:
    for center in centers:
        for c, n, d in zip(center, shape, _D, strict=True):
            exact = Fraction(float(c))
            if exact < Fraction(_RADIUS) or exact + Fraction(_RADIUS) > n * Fraction(d):
                return False
    return all(
        sum((Fraction(float(x)) - Fraction(float(y))) ** 2 for x, y in zip(a, b, strict=True))
        >= (2 * Fraction(_RADIUS)) ** 2
        for a, b in itertools.combinations(centers, 2)
    )


def _initialize(y: Real) -> tuple[Real | None, Real | None, str | None]:
    # Only owned arithmetic is locally contained; unrelated warnings propagate.
    with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
        smooth = ndimage.gaussian_filter(
            y, sigma=(1, 1, 1), order=0, radius=4, mode="constant", cval=0.0, output=np.float64
        )
    _finite(smooth, "Gaussian initialization")
    available = np.ones(y.shape, dtype=bool)
    centers, maxima, windows = [], [], []
    clipped, clamped = 0, 0
    # Exact detector-center offsets implement the closed suppression ball.
    suppression = [
        delta
        for delta in itertools.product(
            *(range(-math.ceil(0.5 / d), math.ceil(0.5 / d) + 1) for d in _D)
        )
        if sum((i * Fraction(d)) ** 2 for i, d in zip(delta, _D, strict=True)) <= Fraction(1, 4)
    ]
    for _ in range(3):
        eligible = np.where(available, smooth, -np.inf)
        peak = np.unravel_index(int(np.argmax(eligible)), y.shape)
        if eligible[peak] <= 0:
            return None, None, None
        for delta in suppression:
            site = tuple(int(p) + i for p, i in zip(peak, delta, strict=True))
            if all(0 <= i < n for i, n in zip(site, y.shape, strict=True)):
                available[site] = False
        window = tuple(
            slice(max(0, int(p) - r), min(n, int(p) + r + 1))
            for p, r, n in zip(peak, (2, 3, 3), y.shape, strict=True)
        )
        clipped += int(
            any(
                int(p) - r < 0 or int(p) + r >= n
                for p, r, n in zip(peak, (2, 3, 3), y.shape, strict=True)
            )
        )
        windows.append(window)
        weights = np.maximum(y[window], 0)
        maximum = float(np.max(weights))
        if maximum == 0:
            return None, None, None
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            # Scale cancels from the centroid and avoids an overflowing mass.
            weights /= maximum
            mass = float(np.sum(weights, dtype=np.float64))
            center = []
            for axis, d in enumerate(_D):
                coordinate = np.arange(window[axis].start, window[axis].stop)
                view = [1, 1, 1]
                view[axis] = len(coordinate)
                raw = float(np.sum(weights * ((coordinate + 0.5) * d).reshape(view)) / mass)
                if not math.isfinite(raw):
                    _range("nonfinite initialization centroid")
                bounded = min(max(raw, _RADIUS), _upper(y.shape[axis], d))
                clamped += int(bounded != raw)
                center.append(bounded)
        centers.append(center)
        maxima.append(maximum)
    overlap = sum(
        all(max(a.start, b.start) < min(a.stop, b.stop) for a, b in zip(left, right, strict=True))
        for left, right in itertools.combinations(windows, 2)
    )
    notes = (
        f"SciPy {scipy.__version__}; clipped windows={clipped}, "
        f"overlapping window pairs={overlap}, clamped centroid coordinates={clamped}"
    )
    c = _copy(centers)
    return (c, _copy(maxima), notes) if _geometry(c, y.shape) else (None, None, notes)


class _Prediction(pilot._Prediction):
    """Reuse finite kernels, with a separate combined-image error budget.

    The inherited engine keeps the density/phase error with its cached values.
    Per-object acceptance alone is insufficient: here the scaled errors and
    assembly roundoff are summed and checked against a lower bound on the
    peak of the SUM of unilluminated images. Fractions keep this accounting
    finite even when a representable prediction has an enormous brightness.
    """

    def profile(self, center: Real) -> pilot._Profile:
        key = tuple(float(v) for v in center)
        if key not in self.profiles:
            fresh = pilot._Profile(center, self.shape)
            # Centers remain represented separately; reuse requires the full
            # midpoint set AND its represented weight, never just equal counts.
            shared = next(
                (
                    p
                    for p in self.profiles.values()
                    if p.weight == fresh.weight and np.array_equal(p.sites, fresh.sites)
                ),
                fresh,
            )
            self.profiles[key] = shared
        return self.profiles[key]

    def _unit_error(self, profile: pilot._Profile, order: int, slot: int) -> Fraction:
        kernel, density_error = profile.kernels[order]
        harmonics = profile.harmonics[(order, slot)]
        peak = float(np.max(harmonics.dc))
        operations = profile.count * math.prod(self.shape) * 4
        raw_error = (
            3 * Fraction(density_error) * profile.count
            + Fraction(harmonics.phase_error) * Fraction(peak)
            + Fraction(float(512 * _EPS * (1 + math.log2(max(2, operations))))) * profile.count
        )
        del kernel
        scale = Fraction(profile.weight)
        for factor in (_D[1], _D[2], math.pi, 1.4 / 0.525, 1.4 / 0.525):
            scale *= Fraction(factor)
        # Includes dimensional-factor evaluation, normalization/assembly and
        # storage rounding. Illumination is bounded by three times flat.
        return (raw_error + 256 * Fraction(float(_EPS)) * Fraction(peak)) * scale + Fraction(
            math.ulp(0.0)
        )

    def predict(self, candidate: PilotCandidate, order: int, count: int = 9) -> tuple[Real, Real]:
        central = np.zeros(self.shape)
        structured = np.zeros((3, count, *self.shape))
        central_error, structured_error = Fraction(0), Fraction(0)
        component_peaks = Fraction(0)
        for center, brightness in zip(
            candidate.centers_um_zyx, candidate.brightness_relative, strict=True
        ):
            profile = self.profile(center)
            flat = self.unit(profile, np.zeros(2), np.zeros(1), np.array([1.0, 0.0, 0.0]), order)[0]
            b = Fraction(float(brightness))
            central_error += b * self._unit_error(profile, order, -1)
            component_peaks += b * Fraction(float(np.max(flat)))
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                central += brightness * flat
            orientation_errors = []
            for o in range(3):
                unit = self.unit(
                    profile,
                    candidate.carriers_yx_per_um[o],
                    candidate.phases_rad[o, :count],
                    candidate.beam_amplitudes,
                    order,
                    o,
                )
                orientation_errors.append(self._unit_error(profile, order, o))
                with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                    structured[o] += brightness * unit
            structured_error += b * max(orientation_errors)
        _finite(central, "central prediction")
        _finite(structured, "structured prediction")
        # Three products and a three-term nonnegative assembly. The absolute
        # subnormal term vanishes for exactly zero brightness, whose products
        # and sums are exactly zero. Component peaks bound roundoff only; they
        # are NOT substituted for the total-image allowance.
        if np.any(candidate.brightness_relative):
            roundoff = 64 * Fraction(float(_EPS)) * component_peaks + 8 * Fraction(math.ulp(0.0))
            central_error += roundoff
            structured_error += 3 * roundoff
        lower_peak = Fraction(float(np.max(central))) - central_error
        if max(central_error, structured_error) > Fraction(1e-5) * lower_peak:
            _range("combined prediction cannot resolve the total unilluminated-peak allowance")
        return _copy(central), _copy(structured)


def _carriers(z: Real) -> Real:
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        rho = z[[14, 16, 18]] * (1.515 / 0.488)
        omega = z[[15, 17, 19]] * math.pi
        q = rho[:, None] * np.stack((np.sin(omega), np.cos(omega)), axis=1)
    return _finite(q, "carrier decoding")


def _carrier_domain(q: Real) -> bool:
    return all(sum((Fraction(float(v)) ** 2 for v in row), Fraction(0)) <= _K0**2 for row in q)


def _bounds(z: Real) -> bool:
    return bool(
        np.all((z[9:15] >= 0) & (z[9:15] <= np.array([100, 100, 100, 1, 1, 1])))
        and all(0 <= z[i] <= 1 for i in (16, 18))
        and all(-1 <= z[i] <= 1 for i in (15, 17, 19))
        and np.all((z[20:] >= -1) & (z[20:] <= 1))
    )


def _decode(z: Real, start: Real, prediction: _Prediction) -> PilotCandidate:
    with np.errstate(over="ignore", under="ignore", invalid="ignore"):
        brightness = _finite(z[9:12] * start, "brightness decoding")
        gamma, eta = z[12:14] * (math.pi / 2)
        beams = np.array([np.cos(gamma), np.sin(gamma) * np.cos(eta), np.sin(gamma) * np.sin(eta)])
        if z[12] == 0:
            beams[1:] = 0
        if z[12] == 1:
            beams[0] = 0
        if z[13] == 0:
            beams[2] = 0
        if z[13] == 1:
            beams[1] = 0
        phases = _finite(z[20:].reshape(3, 9) * (2 * math.pi), "phase decoding")
    return prediction.candidate(
        z[:9].reshape(3, 3), brightness, _carriers(z), phases, _finite(beams, "beam decoding")
    )


def _initial_coordinates(centers: Real) -> Real:
    return _copy(
        [
            *centers.reshape(-1),
            1,
            1,
            1,
            math.acos(1 / math.sqrt(3)) / (math.pi / 2),
            0.5,
            1.2 / 1.515,
            0,
            1.2 / 1.515,
            1 / 3,
            1.2 / 1.515,
            2 / 3,
            *([0, 1 / 5, 2 / 5, 3 / 5, 4 / 5, 1 / 10, 3 / 10, 7 / 10, 9 / 10] * 3),
        ]
    )


def _parameter(candidate: PilotCandidate, index: int) -> Real:
    if index < 9:
        return candidate.centers_um_zyx.reshape(-1)[index : index + 1]
    if index < 12:
        return candidate.brightness_relative[index - 9 : index - 8]
    if index < 14:
        return candidate.beam_amplitudes
    if index < 20:
        return candidate.carriers_yx_per_um[(index - 14) // 2]
    return candidate.phases_rad.reshape(-1)[index - 20 : index - 19]


def _information(
    index: int,
    changed: bool,
    parameter_changed: bool,
    before: PilotCandidate,
    after: PilotCandidate,
    equal_score: bool,
    prediction: _Prediction,
) -> tuple[str, ...]:
    occupancy, zero_bead, zero_angle = False, False, False
    if index < 9:
        bead = index // 3
        left, right = (prediction.profile(c.centers_um_zyx[bead]) for c in (before, after))
        occupancy = left.weight == right.weight and np.array_equal(left.sites, right.sites)
        zero_bead = bool(before.brightness_relative[bead] == after.brightness_relative[bead] == 0)
    if index in (15, 17, 19):
        orientation = (index - 14) // 2
        zero_angle = not np.any(before.carriers_yx_per_um[orientation]) and not np.any(
            after.carriers_yx_per_um[orientation]
        )
    flags = (
        not changed,
        not parameter_changed,
        occupancy,
        zero_bead,
        zero_angle,
        index >= 14 and np.count_nonzero(before.beam_amplitudes) == 1,
        (index < 9 or index >= 12)
        and not np.any(before.brightness_relative)
        and not np.any(after.brightness_relative),
        equal_score,
    )
    return tuple(code for code, flag in zip(_CODES, flags, strict=True) if flag)


class _Fit:
    """Call-local ledgers; no shared mutable state or observer hooks."""

    def __init__(self, result: BeadCalibrationResult, y: Real, training: Real) -> None:
        self.result = result
        self.y, self.training = y, training
        self.prediction = _Prediction(y.shape)
        self.trace: list[BeadCalibrationScore] = []
        self.attempts: list[BeadCalibrationAttempt] = []
        self.objectives: list[float | None] = [None, None, None]
        self.best_index: int | None = None
        self.incumbent_index: int | None = None
        self.stage = "initialization"

    def score(
        self, z: Real, build: Callable[[], PilotCandidate], stage: str, order: int
    ) -> tuple[PilotCandidate, Real]:
        try:
            candidate = build()
            central, structured = self.prediction.predict(candidate, order)
            with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
                residual_c, residual_s = self.y - central, self.training - structured
                # Direct float64 squares are intentional, including range loss
                # before division. No scaled norm or cached-total subtraction.
                loss = float(
                    (
                        np.sum(residual_c**2, dtype=np.float64)
                        + np.sum(residual_s**2, dtype=np.float64)
                    )
                    / (2 * 28 * self.y.size)
                )
            if not math.isfinite(loss) or loss < 0:
                _range("nonfinite or negative training objective")
        except SimreconError as error:
            if error.code in _KNOWN:
                self.trace.append(
                    BeadCalibrationScore(
                        stage, order, _copy(z), None, None, "numerical_incomplete", error.code
                    )
                )
            raise
        self.trace.append(
            BeadCalibrationScore(stage, order, _copy(z), _snapshot(candidate), loss, "scored", None)
        )
        best_cost = self.objectives[0]
        if order == 128 and (best_cost is None or loss < best_cost):
            self.best_index = len(self.trace) - 1
            self.objectives[0] = loss
        return candidate, structured

    def poll(
        self,
        sweep: int,
        index: int,
        sign: int,
        base_index: int,
        z: Real,
        start: Real,
        before: PilotCandidate,
        base_cost: float,
    ) -> None:
        attempt = BeadCalibrationAttempt(
            sweep,
            index,
            sign,
            base_index,
            None,
            None,
            None,
            "numerical_incomplete",
            None,
            None,
            None,
            (),
            None,
        )
        score_index = None
        try:
            with np.errstate(over="ignore", under="ignore", invalid="ignore"):
                step = np.float64(_STEPS[index]) * np.float64(self.result.sweep_scales[sweep])
                trial = _copy(z)
                trial[index] = z[index] + sign * step
            _finite(np.array([step, trial[index]]), "poll coordinate formation")
            changed = bool(trial[index] != z[index])
            attempt = replace(attempt, trial_coordinates=_copy(trial), coordinate_changed=changed)
            reason = None
            if not _bounds(trial):
                reason = "coordinate_bounds"
            elif not _geometry(trial[:9].reshape(3, 3), self.y.shape):
                reason = "center_geometry"
            elif not _carrier_domain(_carriers(trial)):
                reason = "carrier_domain"
            if reason is not None:
                self.attempts.append(
                    replace(attempt, outcome="infeasible", infeasibility_reason=reason)
                )
                return
            score_index = len(self.trace)
            candidate, _ = self.score(
                trial, lambda: _decode(trial, start, self.prediction), "poll", 128
            )
            cost = self.trace[score_index].objective
            parameter_changed = not np.array_equal(
                _parameter(before, index), _parameter(candidate, index)
            )
            codes = _information(
                index,
                changed,
                parameter_changed,
                before,
                candidate,
                cost == base_cost,
                self.prediction,
            )
            attempt = replace(
                attempt,
                outcome="scored",
                parameter_changed=parameter_changed,
                score_index=score_index,
                information_codes=codes,
            )
        except SimreconError as error:
            if error.code in _KNOWN:
                self.attempts.append(
                    replace(attempt, score_index=score_index, failure_code=error.code)
                )
            raise
        self.attempts.append(attempt)

    def run(self) -> BeadCalibrationResult:
        try:
            centers, maxima, notes = _initialize(self.y)
            self.result = replace(self.result, initialization_notes=notes)
            if centers is None or maxima is None:
                return self.finish(
                    "initialization_failed",
                    "initialization: unavailable separated positive centroids",
                )
            units = [
                self.prediction.unit(
                    self.prediction.profile(c),
                    np.zeros(2),
                    np.zeros(1),
                    np.array([1.0, 0.0, 0.0]),
                    128,
                )[0]
                for c in centers
            ]
            peaks = np.array([float(np.max(unit)) for unit in units])
            if np.any(peaks <= 0):
                return self.finish(
                    "initialization_failed", "initialization: unusable finite unit response"
                )
            with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
                start = _finite(maxima / peaks, "initial brightness")
            if np.any(start <= 0):
                return self.finish(
                    "initialization_failed", "initialization: unusable finite brightness"
                )
            z = _initial_coordinates(centers)
            candidate = _decode(z, start, self.prediction)
            self.result = replace(
                self.result, initial_candidate=_snapshot(candidate), initial_coordinates=_copy(z)
            )
            self.stage = "initial"
            candidate, _ = self.score(z, lambda: candidate, "initial", 128)
            self.incumbent_index = 0
            self.stage = "poll"
            for sweep in range(len(self.result.sweep_scales)):
                for index in range(47):
                    base_index = self.incumbent_index
                    base_cost = self.trace[base_index].objective
                    assert base_cost is not None
                    pair_start = len(self.attempts)
                    for sign in (-1, 1):
                        self.poll(sweep, index, sign, base_index, z, start, candidate, base_cost)
                    winner: int | None = None
                    winning_cost = base_cost
                    for ai in range(pair_start, pair_start + 2):
                        attempt = self.attempts[ai]
                        if attempt.outcome == "scored":
                            assert attempt.score_index is not None
                            cost = self.trace[attempt.score_index].objective
                            assert cost is not None
                            if cost < winning_cost:
                                winner, winning_cost = ai, cost
                    for ai in range(pair_start, pair_start + 2):
                        self.attempts[ai] = replace(self.attempts[ai], selected=ai == winner)
                    if winner is not None:
                        selected = self.attempts[winner]
                        assert selected.score_index is not None
                        self.incumbent_index = selected.score_index
                        scored = self.trace[self.incumbent_index]
                        assert scored.candidate is not None and scored.coordinates is not None
                        candidate, z = scored.candidate, scored.coordinates
                    self.prediction.retain(candidate)
            self.result = replace(
                self.result, frozen_candidate=_snapshot(candidate), frozen_coordinates=_copy(z)
            )
            for j, order in enumerate((256, 512), 1):
                self.stage = f"refinement_q{order}"
                _, _ = self.score(z, lambda: candidate, "refinement", order)
                self.objectives[j] = self.trace[-1].objective
            self.stage = "heldout_prediction"
            _, prediction = self.prediction.predict(candidate, 512, 5)
            self.result = replace(self.result, heldout_prediction=_copy(prediction))
            return self.finish(
                "completed_finite_fit", "heldout_prediction: complete; residuals pending"
            )
        except SimreconError as error:
            if error.code not in _KNOWN:
                raise
            return self.finish("numerical_incomplete", f"{self.stage}: {error}", error.code)

    def finish(
        self, status: str, message: str, failure_code: str | None = None
    ) -> BeadCalibrationResult:
        evidence = []
        for index in range(47):
            attempts = [a for a in self.attempts if a.coordinate_index == index]
            scored = [a for a in attempts if a.outcome == "scored"]
            evidence.append(
                BeadCoordinateEvidence(
                    index,
                    len(attempts),
                    len(scored),
                    sum(a.coordinate_changed is True for a in scored),
                    sum(a.parameter_changed is True for a in scored),
                    sum(a.selected is True for a in attempts),
                    tuple(
                        code for code in _CODES if any(code in a.information_codes for a in scored)
                    ),
                )
            )
        pairs = sum(a.selected is not None for a in self.attempts) // 2
        counts = BeadCalibrationCounts(
            94 * len(self.result.sweep_scales),
            len(self.attempts),
            sum(a.outcome == "scored" for a in self.attempts),
            sum(a.outcome == "infeasible" for a in self.attempts),
            sum(a.outcome == "numerical_incomplete" for a in self.attempts),
            pairs,
            pairs // 47,
            len(self.trace),
            sum(s.outcome == "scored" for s in self.trace),
        )
        best_candidate, best_coordinates = None, None
        if self.best_index is not None:
            best = self.trace[self.best_index]
            assert best.candidate is not None and best.coordinates is not None
            best_candidate, best_coordinates = _snapshot(best.candidate), _copy(best.coordinates)
        return replace(
            self.result,
            status=status,
            stage=self.stage,
            message=message,
            failure_code=failure_code,
            best_candidate=best_candidate,
            best_coordinates=best_coordinates,
            best_score_index=self.best_index,
            incumbent_score_index=self.incumbent_index,
            objective_trace=tuple(self.trace),
            poll_attempts=tuple(self.attempts),
            coordinate_evidence=tuple(evidence),
            unprobed_coordinates=tuple(
                e.coordinate_index for e in evidence if e.distinct_parameter_scored_count == 0
            ),
            counts=counts,
            training_objectives_q128_q256_q512=tuple(self.objectives),
        )


def fit_bead_calibration(
    central_counts: Any,
    *,
    structured_counts: Any,
    heldout_counts: Any,
    camera_estimate: Any,
    origin_um_zyx: Any,
    sweep_scales: Any,
) -> BeadCalibrationResult:
    """Fit every declared paired coordinate, then freeze and validate held-out images.

    Inputs are raw counts and an image-derived scalar camera estimate. Centers
    are local micrometres; brightness is integrated reference-flat-relative.
    Invalid representations raise SimreconError; known numerical ranges retain
    actual partial evidence. Unrelated exceptions and allocation failures escape.
    """
    central = _array(central_counts, "central_counts")
    structured = _array(structured_counts, "structured_counts")
    heldout = _array(heldout_counts, "heldout_counts")
    shape = central.shape
    if central.ndim != 3 or any(
        n == 0 or n * Fraction(d) < Fraction(0.100) for n, d in zip(shape, _D, strict=False)
    ):
        _invalid("central image requires three nonempty sides at least 0.100 micrometres long")
    if structured.shape != (3, 9, *shape) or heldout.shape != (3, 5, *shape):
        _invalid("structured and held-out shapes must be (3,9,*N) and (3,5,*N)")
    if not isinstance(camera_estimate, ScalarCameraEstimate):
        _invalid("camera_estimate must be a ScalarCameraEstimate")
    means = camera_estimate.means_counts
    if (
        type(means) is not np.ndarray
        or means.dtype != np.dtype(np.float64)
        or not means.dtype.isnative
        or means.shape != (3,)
        or not np.isfinite(means).all()
    ):
        _invalid("camera means require plain finite native float64 shape (3,)")
    blank = float(_copy(means)[1])
    contrast = _number(camera_estimate.contrast_counts, "contrast_counts")
    source = camera_estimate.source
    if not isinstance(source, str) or not source.strip():
        _invalid("camera source must be a nonblank string")
    if not isinstance(origin_um_zyx, tuple) or len(origin_um_zyx) != 3:
        _invalid("origin must be a length-three tuple")
    origin = tuple(_number(v, "origin") for v in origin_um_zyx)
    if type(sweep_scales) is not tuple or not sweep_scales:
        _invalid("sweep_scales must be a nonempty built-in tuple")
    scales = tuple(_number(v, "scale") for v in sweep_scales)
    if any(v <= 0 for v in scales):
        _invalid("every sweep scale must be strictly positive")
    result = BeadCalibrationResult(
        status="normalization_unavailable",
        stage="normalization",
        message="normalization: nonpositive estimated contrast",
        failure_code=None,
        detector_shape_zyx=shape,
        origin_um_zyx=origin,
        scipy_version=str(scipy.__version__),
        camera_source=str(source),
        blank_counts=blank,
        contrast_counts=contrast,
        sweep_scales=scales,
        initialization_notes=None,
        initial_candidate=None,
        initial_coordinates=None,
        best_candidate=None,
        best_coordinates=None,
        best_score_index=None,
        incumbent_score_index=None,
        frozen_candidate=None,
        frozen_coordinates=None,
        objective_trace=(),
        poll_attempts=(),
        coordinate_evidence=tuple(BeadCoordinateEvidence(i, 0, 0, 0, 0, 0, ()) for i in range(47)),
        unprobed_coordinates=tuple(range(47)),
        counts=BeadCalibrationCounts(94 * len(scales), 0, 0, 0, 0, 0, 0, 0, 0),
        training_objectives_q128_q256_q512=(None, None, None),
        heldout_prediction=None,
        heldout_residual_mean=None,
        heldout_residual_rms=None,
    )
    if contrast <= 0:
        return result
    try:
        y, training = _correct(central, blank, contrast), _correct(structured, blank, contrast)
    except SimreconError as error:
        if error.code not in _KNOWN:
            raise
        return replace(
            result,
            status="numerical_incomplete",
            message=f"normalization: {error}",
            failure_code=error.code,
        )
    result = _Fit(result, y, training).run()
    if result.heldout_prediction is None:
        return result
    # Prediction is complete and independently stored before accessing held-out
    # values for correction or arithmetic. Publish the summaries atomically.
    try:
        corrected = _correct(heldout, blank, contrast)
        with np.errstate(over="ignore", under="ignore", invalid="ignore", divide="ignore"):
            residual = _finite(corrected - result.heldout_prediction, "held-out residual")
            mean = _finite(
                np.mean(residual, axis=(2, 3, 4), dtype=np.float64), "held-out residual mean"
            )
            rms = _finite(
                np.sqrt(np.mean(residual**2, axis=(2, 3, 4), dtype=np.float64)),
                "held-out residual RMS",
            )
    except SimreconError as error:
        if error.code not in _KNOWN:
            raise
        return replace(
            result,
            status="numerical_incomplete",
            stage="heldout_residual",
            message=f"heldout_residual: {error}",
            failure_code=error.code,
        )
    return replace(
        result,
        status="completed_finite_fit",
        stage="complete",
        message="complete: prescribed finite fit and held-out summaries",
        heldout_residual_mean=_copy(mean),
        heldout_residual_rms=_copy(rms),
    )
