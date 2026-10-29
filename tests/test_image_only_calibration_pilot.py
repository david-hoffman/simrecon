"""Blind public-contract tests for the fixed-pupil image-only calibration pilot.

No recovered-parameter accuracy or empirical-pupil claim is tested. Scripted
Powell calls exercise the mandated public optimizer boundary, not a replacement
pilot. All successful-image oracles use independent finite physical equations.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import itertools
import math
import warnings
from collections.abc import Callable
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
import scipy.optimize
from scipy.optimize import OptimizeResult

from image_only_calibration_pilot_fixture import (
    COMMANDS,
    EPS,
    RADIUS,
    SHAPE,
    D,
    assert_prediction_close,
    assert_scalar_close,
    camera,
    correction_reference_controls,
    initialization,
    inward_upper,
    loss_allowance,
    objective,
    observations,
    predictions,
    reference_controls,
    unit_sites,
)
from simrecon import SimreconError

# Intentional import failure when the authorized runtime does not yet exist.
# It is unavailable execution evidence, never a skip or manufactured product red.
PILOT = importlib.import_module("scripts.image_only_calibration_pilot")
SOURCE = importlib.import_module("scripts.simulation_sources")
OPTICS = importlib.import_module("scripts.simulation_optics")
MINIMIZE_SIGNATURE = inspect.signature(scipy.optimize.minimize)

CANDIDATE_FIELDS = {
    "centers_um_zyx",
    "brightness_relative",
    "carriers_yx_per_um",
    "phases_rad",
    "beam_amplitudes",
    "occupied_counts",
    "stored_unit_masses_e",
}
RESULT_FIELDS = {
    "status",
    "stage",
    "message",
    "failure_code",
    "detector_shape_zyx",
    "origin_um_zyx",
    "camera_source",
    "blank_counts",
    "contrast_counts",
    "initial_candidate",
    "frozen_candidate",
    "objective_trace",
    "optimizer_status",
    "optimizer_message",
    "optimizer_nfev",
    "optimizer_nit",
    "center_attempts",
    "training_objectives_q128_q256_q512",
    "heldout_prediction",
    "heldout_residual_mean",
    "heldout_residual_rms",
}
SCORE_FIELDS = {"stage", "pupil_order", "candidate", "objective", "outcome"}
ATTEMPT_FIELDS = {"bead_index", "axis_index", "sign", "outcome"}


class ScriptedPowell:
    """Drive feasible public coordinates and return deliberately unscored metadata."""

    def __init__(self, status: int = 0, *, explore: bool = False) -> None:
        self.status = status
        self.explore = explore
        self.values: list[float] = []
        self.vectors: list[np.ndarray] = []
        self.entered = 0

    def __call__(self, fun: Callable[..., float], x0: Any, *args: Any, **kwargs: Any) -> Any:
        self.entered += 1
        bound = MINIMIZE_SIGNATURE.bind(fun, x0, *args, **kwargs)
        bound.apply_defaults()
        settings = bound.arguments
        assert str(settings["method"]).lower() == "powell"
        options = settings["options"]
        assert {k: options[k] for k in ("maxfev", "maxiter", "xtol", "ftol")} == {
            "maxfev": 100,
            "maxiter": 4,
            "xtol": 1e-3,
            "ftol": 1e-3,
        }
        bounds = settings["bounds"]
        pairs = (
            np.column_stack((bounds.lb, bounds.ub))
            if isinstance(bounds, scipy.optimize.Bounds)
            else np.array(bounds)
        )
        expected = [(0, 100)] * 3 + [(0, 1)] * 2 + [(0, 1), (-1, 1)] * 3 + [(-1, 1)] * 27
        np.testing.assert_array_equal(pairs, expected)
        x = np.array(x0, dtype=np.float64, copy=True)
        assert x.shape == (38,)
        np.testing.assert_allclose(x[:3], 1, rtol=32 * EPS, atol=0)
        np.testing.assert_allclose(
            x[3:5], [math.acos(1 / math.sqrt(3)) / (math.pi / 2), 0.5], rtol=32 * EPS, atol=0
        )
        np.testing.assert_allclose(
            x[5:11], [1.2 / 1.515, 0, 1.2 / 1.515, 1 / 3, 1.2 / 1.515, 2 / 3], rtol=64 * EPS, atol=0
        )
        np.testing.assert_allclose(
            x[11:].reshape(3, 9), np.tile(COMMANDS / (2 * math.pi), (3, 1)), rtol=64 * EPS, atol=0
        )
        if self.explore:
            vectors = [x.copy()]
            asymmetric = x.copy()
            asymmetric[:3] = [0.4, 0.7, 0.2]
            asymmetric[3:5] = [0.67, 0.23]
            asymmetric[5:11] = [0.17, -0.31, 0.49, -0.73, 0.63, 0.11]
            asymmetric[11:] = np.linspace(-0.83, 0.91, 27)
            vectors.append(asymmetric)
            zero_beams = asymmetric.copy()
            zero_beams[3:5] = 0
            vectors.append(zero_beams)
            zero_brightness = asymmetric.copy()
            zero_brightness[:3] = 0
            zero_brightness[3:5] = 1
            vectors.append(zero_brightness)
            # The earlier zero-B trial is strictly better for the declared scenes.
            # A later worse score and the unscored return must not replace it.
            vectors.append(asymmetric.copy())
            for vector in vectors:
                self.vectors.append(vector.copy())
                self.values.append(float(fun(vector, *settings["args"])))
        returned = x.copy()
        returned[:3] = 100  # This unscored vector must never displace a scored incumbent.
        return OptimizeResult(
            x=returned,
            fun=-1e99,
            success=self.status == 0,
            status=self.status,
            message=f"scripted Powell status {self.status}",
            nfev=91,
            nit=4,
        )


@pytest.fixture
def invoke(monkeypatch: pytest.MonkeyPatch) -> Callable[..., Any]:
    """Patch public dependencies before loading their pilot caller, preserving import styles."""

    def run(*, solver: Any = None, **changes: Any) -> Any:
        central, structured, heldout = observations()
        values: dict[str, Any] = {
            "central_counts": central,
            "structured_counts": structured,
            "heldout_counts": heldout,
            "camera_estimate": camera(),
            "origin_um_zyx": (10, -3.25, 7.5),
        }
        values.update(changes)
        with monkeypatch.context() as patch:
            patch.setattr(
                scipy.optimize, "minimize", solver if solver is not None else ScriptedPowell()
            )
            module = importlib.reload(PILOT)
            return module.fit_small_pilot(values.pop("central_counts"), **values)

    return run


def assert_frozen(record: Any, names: set[str]) -> None:
    assert set(inspect.signature(type(record)).parameters) == names
    for name in names:
        with pytest.raises((AttributeError, TypeError, dataclasses.FrozenInstanceError)):
            setattr(record, name, getattr(record, name))


def candidate_arrays(candidate: Any) -> list[np.ndarray]:
    return [
        getattr(candidate, name)
        for name in (
            "centers_um_zyx",
            "brightness_relative",
            "carriers_yx_per_um",
            "phases_rad",
            "beam_amplitudes",
            "stored_unit_masses_e",
        )
    ]


def same_candidate(a: Any, b: Any) -> None:
    for left, right in zip(candidate_arrays(a), candidate_arrays(b), strict=True):
        np.testing.assert_array_equal(left, right)
    assert a.occupied_counts == b.occupied_counts


def assert_requested_optimizer_scores(result: Any, solver: ScriptedPowell) -> None:
    """Link actual callback returns and all public coordinates to their scored records."""
    scores = [s for s in result.objective_trace if s.stage == "optimizer"]
    assert len(scores) == len(solver.vectors) == len(solver.values)
    m = 28 * math.prod(result.detector_shape_zyx)
    # Two ordinary float64 reductions of the same scored evaluation may round
    # differently; no optical error is added to an unrelated callback scale.
    operations = 2 * (8 * m + 64)
    reduction = operations * EPS / (1 - operations * EPS)
    for vector, value, score in zip(solver.vectors, solver.values, scores, strict=True):
        assert score.outcome == "scored" and math.isfinite(value)
        assert abs(value - score.objective) <= reduction * abs(score.objective)
        candidate = score.candidate
        np.testing.assert_array_equal(
            candidate.centers_um_zyx, result.initial_candidate.centers_um_zyx
        )
        np.testing.assert_allclose(
            candidate.brightness_relative,
            vector[:3] * result.initial_candidate.brightness_relative,
            rtol=64 * EPS,
            atol=0,
        )
        gamma, eta = vector[3:5] * (math.pi / 2)
        sine = 0.0 if vector[3] == 0 else math.sin(gamma)
        expected_amplitudes = [
            0.0 if vector[3] == 1 else math.cos(gamma),
            0.0 if vector[4] == 1 else sine * math.cos(eta),
            0.0 if vector[4] == 0 else sine * math.sin(eta),
        ]
        np.testing.assert_allclose(
            candidate.beam_amplitudes, expected_amplitudes, rtol=64 * EPS, atol=0
        )
        expected_q = np.array(
            [
                [
                    vector[5 + 2 * o] * (1.515 / 0.488) * math.sin(vector[6 + 2 * o] * math.pi),
                    vector[5 + 2 * o] * (1.515 / 0.488) * math.cos(vector[6 + 2 * o] * math.pi),
                ]
                for o in range(3)
            ]
        )
        np.testing.assert_allclose(candidate.carriers_yx_per_um, expected_q, rtol=128 * EPS, atol=0)
        np.testing.assert_allclose(
            candidate.phases_rad, vector[11:].reshape(3, 9) * 2 * math.pi, rtol=64 * EPS, atol=0
        )
    # This witness concerns actual scored costs, not optimizer-return metadata.
    prior = [result.objective_trace[0], *scores]
    best_index = min(range(len(prior)), key=lambda i: prior[i].objective)
    assert 0 < best_index < len(prior) - 1
    assert prior[best_index].objective < prior[0].objective
    assert prior[-1].objective > prior[best_index].objective


def assert_candidate(candidate: Any, shape: tuple[int, int, int]) -> None:
    assert_frozen(candidate, CANDIDATE_FIELDS)
    assert [a.shape for a in candidate_arrays(candidate)] == [
        (3, 3),
        (3,),
        (3, 2),
        (3, 9),
        (3,),
        (3,),
    ]
    assert isinstance(candidate.occupied_counts, tuple) and len(candidate.occupied_counts) == 3
    for a in candidate_arrays(candidate):
        assert type(a) is np.ndarray and a.dtype == np.dtype("float64") and a.dtype.isnative
        assert a.flags.c_contiguous and a.flags.writeable and np.isfinite(a).all()
    for bead, center in enumerate(candidate.centers_um_zyx):
        for axis, c in enumerate(center):
            assert Fraction(float(c)) >= Fraction(RADIUS)
            assert Fraction(float(c)) + Fraction(RADIUS) <= shape[axis] * Fraction(D[axis])
        _, count, mass = unit_sites(tuple(float(v) for v in center), shape)
        assert type(candidate.occupied_counts[bead]) is int
        assert candidate.occupied_counts[bead] == count
        # Sum of represented equal weights; allow reduction roundoff, no volume factor.
        assert abs(candidate.stored_unit_masses_e[bead] - mass) <= 16 * count * EPS * abs(mass)
    assert all(
        math.dist(a, b) >= 2 * RADIUS
        for a, b in itertools.combinations(candidate.centers_um_zyx, 2)
    )
    assert np.all(candidate.brightness_relative >= 0)
    assert np.all(candidate.beam_amplitudes >= 0)
    assert math.isclose(
        math.fsum(float(v) ** 2 for v in candidate.beam_amplitudes), 1, rel_tol=64 * EPS
    )
    for q in candidate.carriers_yx_per_um:
        assert sum(Fraction(float(v)) ** 2 for v in q) <= (Fraction(1.515) / Fraction(0.488)) ** 2


def assert_empty(result: Any, status: str, stage: str) -> None:
    assert_frozen(result, RESULT_FIELDS)
    assert (result.status, result.stage, result.failure_code) == (status, stage, None)
    assert isinstance(result.message, str) and result.message.strip()
    for name in (
        "initial_candidate",
        "frozen_candidate",
        "optimizer_status",
        "optimizer_message",
        "optimizer_nfev",
        "optimizer_nit",
        "heldout_prediction",
        "heldout_residual_mean",
        "heldout_residual_rms",
    ):
        assert getattr(result, name) is None
    assert result.objective_trace == result.center_attempts == ()
    assert result.training_objectives_q128_q256_q512 == (None, None, None)


def test_independent_observers_have_physical_reference_controls() -> None:
    reference_controls()


def test_reference_uncertainty_does_not_reject_permitted_boundary_output() -> None:
    correction_reference_controls()


@pytest.mark.parametrize("contrast", [0, -2.0, -0.0])
def test_nonpositive_estimated_contrast_is_information_without_division(
    invoke: Any, contrast: Any
) -> None:
    # Large opposite finite counts would overflow a forbidden attempted correction.
    c = np.full(SHAPE, np.finfo(float).max)
    with np.errstate(all="raise"):
        result = invoke(
            central_counts=c,
            camera_estimate=camera(
                contrast_counts=contrast, means_counts=np.array([0.0, -np.finfo(float).max, 0.0])
            ),
        )
    assert_empty(result, "normalization_unavailable", "normalization")
    assert result.blank_counts == -np.finfo(float).max and result.contrast_counts == contrast


def test_unavailable_normalization_still_requires_valid_heldout_input(invoke: Any) -> None:
    bad = np.zeros((3, 5, *SHAPE))
    bad.flat[-1] = np.nan
    with pytest.raises(SimreconError) as caught:
        invoke(heldout_counts=bad, camera_estimate=camera(contrast_counts=0))
    assert caught.value.code == "invalid_image_only_calibration_pilot"


@pytest.mark.parametrize("data", [np.zeros(SHAPE), -np.ones(SHAPE), np.full(SHAPE, -0.125)])
def test_missing_positive_peaks_is_initialization_information(invoke: Any, data: Any) -> None:
    result = invoke(central_counts=5 + 2 * data)
    assert_empty(result, "initialization_failed", "initialization")


def test_suppressed_gaussian_tail_can_have_zero_centroid_weight(invoke: Any) -> None:
    y = np.zeros((1, 2, 16))
    y[0, 0, 0], y[0, 0, 7], y[0, 0, 10] = 8, 6, 0.01
    with pytest.raises(ValueError, match="zero centroid weight"):
        initialization(y)
    result = invoke(
        central_counts=5 + 2 * y,
        structured_counts=np.full((3, 9, *y.shape), 5.0),
        heldout_counts=np.full((3, 5, *y.shape), 5.0),
    )
    assert_empty(result, "initialization_failed", "initialization")


def test_centroid_overlap_fails_without_repair_or_further_peak_search(invoke: Any) -> None:
    y = np.zeros((1, 2, 16))
    y[0, 0, [1, 8, 15]] = [8, 6, 4]
    # Cancel the smoothing of these positive weights in row zero with signed
    # row-one data. Centroids still use the positive raw weights at x=4 and 5.
    y[0, 0, [4, 5]] = 1000
    y[0, 1, [4, 5]] = -math.exp(0.5) * 1000
    normalized = ((5 + 2 * y) - 5) / 2
    with pytest.raises(ValueError, match="overlapping centroids"):
        initialization(normalized)
    result = invoke(
        central_counts=5 + 2 * y,
        structured_counts=np.full((3, 9, *y.shape), 5.0),
        heldout_counts=np.full((3, 5, *y.shape), 5.0),
    )
    assert_empty(result, "initialization_failed", "initialization")


def test_exact_peak_ties_choose_lexicographic_indices(invoke: Any) -> None:
    y = np.zeros(SHAPE)
    y[0, 0, [0, 7, 14]] = 8
    centers, _, peaks = initialization(y)
    assert peaks == ((0, 0, 0), (0, 0, 7), (0, 0, 14))
    result = invoke(central_counts=5 + 2 * y)
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx, centers, rtol=128 * EPS, atol=0
    )


def initialization_boundary_scene(control: str) -> np.ndarray:
    """Declare small observation-only scenes for settled initialization boundaries."""
    if control == "inward":
        y = np.zeros((2, 4, 16))
        y[0, 3, [0, 7, 15]] = [8, 6, 4]
    elif control == "closed_suppression":
        y = np.zeros((9, 2, 2))
        y[[0, 4, 8], 0, 0] = [8, 6, 4]
    else:
        assert control in ("windows_positive", "windows_negative")
        y = np.zeros((4, 5, 16))
        y[0, 0, [0, 7, 15]] = [8, 6, 4]
        # The first centroid includes exactly the +2 z, +3 y and +3 x
        # supports, but excludes +3 z, +4 y and +4 x. Reflection tests the
        # negative limits too. The x=4 point also belongs to bead two's window.
        y[2, 0, 0] = y[0, 3, 0] = y[0, 0, 3] = 1
        y[3, 0, 0] = y[0, 4, 0] = y[0, 0, 4] = 0.5
        if control == "windows_negative":
            y = np.flip(y, axis=(0, 1, 2)).copy()
    return y


@pytest.mark.parametrize(
    "control", ["inward", "closed_suppression", "windows_positive", "windows_negative"]
)
def test_initialization_exact_bounds_suppression_and_windows(invoke: Any, control: str) -> None:
    y = initialization_boundary_scene(control)
    central = 5 + 2 * y
    normalized = (central - 5) / 2
    centers, _, peaks = initialization(normalized)
    if control == "inward":
        exact = 4 * Fraction(D[1]) - Fraction(RADIUS)
        upper = float.fromhex("0x1.147ae147ae147p-2")
        ordinary = 4 * D[1] - RADIUS
        assert Fraction(upper) <= exact < Fraction(ordinary)
        assert float(np.nextafter(upper, np.inf)) == ordinary
        np.testing.assert_array_equal(centers[:, 1], np.full(3, upper))
        assert peaks == ((0, 3, 0), (0, 3, 7), (0, 3, 15))
    elif control == "closed_suppression":
        assert 4 * Fraction(D[0]) == Fraction(1, 2)
        assert peaks == ((0, 0, 0), (8, 0, 0), (4, 1, 0))
        np.testing.assert_array_equal(centers[:, 0], [0.0625, 1.0625, 0.5625])
    else:
        # For the first peak, total positive window weight is 8+1+1+1=11.
        # Ten units have coordinate D/2; the included support has coordinate
        # 5*D_z/2 or 7*D_yx/2. The three half-weight outside points do not enter.
        first = np.array(
            [
                float(Fraction(D[0]) * Fraction(15, 22)),
                float(Fraction(D[1]) * Fraction(17, 22)),
                float(Fraction(D[2]) * Fraction(17, 22)),
            ]
        )
        if control == "windows_negative":
            first = np.array(y.shape) * np.array(D) - first
            assert peaks == ((3, 4, 15), (3, 4, 8), (3, 4, 0))
        else:
            assert peaks == ((0, 0, 0), (0, 0, 7), (0, 0, 15))
        np.testing.assert_allclose(centers[0], first, rtol=64 * EPS, atol=0)
    result = invoke(
        central_counts=central,
        structured_counts=np.full((3, 9, *y.shape), 5.0),
        heldout_counts=np.full((3, 5, *y.shape), 5.0),
    )
    assert result.status == "completed_local"
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx, centers, rtol=128 * EPS, atol=0
    )
    if control == "inward":
        np.testing.assert_array_equal(
            result.initial_candidate.centers_um_zyx[:, 1],
            np.full(3, float.fromhex("0x1.147ae147ae147p-2")),
        )
    if control == "closed_suppression":
        np.testing.assert_array_equal(
            result.initial_candidate.centers_um_zyx[:, 0], [0.0625, 1.0625, 0.5625]
        )
    assert_candidate(result.initial_candidate, (int(y.shape[0]), int(y.shape[1]), int(y.shape[2])))


def test_signed_smoothing_is_not_preclipped_and_uses_the_selected_gaussian(
    invoke: Any, monkeypatch: Any
) -> None:
    from scipy import ndimage

    y = np.zeros(SHAPE)
    y[0, 0, [0, 7, 14]] = [8, 6, 4]
    y[0, 0, 3] = 100
    y[0, 1, 3] = -math.exp(0.5) * 100
    central = 5 + 2 * y
    normalized = (central - 5) / 2
    centers, _, peaks = initialization(normalized)
    assert peaks == ((0, 0, 0), (0, 0, 7), (0, 0, 14))
    original = ndimage.gaussian_filter
    entered = []

    def observed(*args: Any, **kwargs: Any) -> Any:
        settings = inspect.signature(original).bind(*args, **kwargs)
        settings.apply_defaults()
        values = settings.arguments
        np.testing.assert_array_equal(values["input"], normalized)
        assert np.all(np.asarray(values["sigma"]) == 1)
        assert np.all(np.asarray(values["order"]) == 0)
        assert np.all(np.asarray(values["radius"]) == 4)
        assert np.all(np.asarray(values["mode"]) == "constant") and values["cval"] == 0
        output = values["output"]
        assert (output.dtype if isinstance(output, np.ndarray) else np.dtype(output)) == np.dtype(
            "float64"
        )
        entered.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(ndimage, "gaussian_filter", observed)
    result = invoke(central_counts=central)
    assert result.status == "completed_local"
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx, centers, rtol=256 * EPS, atol=0
    )


def test_zero_brightness_is_legal_and_equal_poll_costs_retain_incumbent(invoke: Any) -> None:
    result = invoke(
        solver=ScriptedPowell(explore=True), structured_counts=np.full((3, 9, *SHAPE), -19995.0)
    )
    np.testing.assert_array_equal(result.frozen_candidate.brightness_relative, [0, 0, 0])
    np.testing.assert_array_equal(
        result.frozen_candidate.centers_um_zyx, result.initial_candidate.centers_um_zyx
    )
    costs = [
        s.objective for s in result.objective_trace if s.stage == "center" and s.outcome == "scored"
    ]
    assert costs and all(v == result.training_objectives_q128_q256_q512[0] for v in costs)


def test_represented_domain_boundary_attempt_is_scored_or_recorded_infeasible(
    invoke: Any, monkeypatch: Any
) -> None:
    entries, values = [], []
    original = OPTICS.expected_images

    def observed(*args: Any, **kwargs: Any) -> Any:
        entries.append(True)
        return original(*args, **kwargs)

    monkeypatch.setattr(OPTICS, "expected_images", observed)

    def solve(fun: Any, x0: Any, *args: Any, **kwargs: Any) -> Any:
        vector = np.array(x0, copy=True)
        vector[5:11] = [1, -0.998, 0, 0, 0, 0]
        before = len(entries)
        bound = MINIMIZE_SIGNATURE.bind(fun, x0, *args, **kwargs)
        bound.apply_defaults()
        value = fun(vector, *bound.arguments["args"])
        values.append((value, before, len(entries)))
        return OptimizeResult(
            x=x0, fun=0, success=True, status=0, message="boundary attempt", nfev=1, nit=1
        )

    result = invoke(solver=solve)
    (score,) = [s for s in result.objective_trace if s.stage == "optimizer"]
    value, before, after = values[0]
    if score.outcome == "infeasible":
        assert value == math.inf and score.objective is score.candidate is None
        assert before == after
    else:
        assert score.outcome == "scored" and math.isfinite(value)
        assert_candidate(score.candidate, SHAPE)
        expected = [
            (1.515 / 0.488) * math.sin(-0.998 * math.pi),
            (1.515 / 0.488) * math.cos(-0.998 * math.pi),
        ]
        np.testing.assert_allclose(
            score.candidate.carriers_yx_per_um[0], expected, rtol=128 * EPS, atol=0
        )
        np.testing.assert_array_equal(score.candidate.carriers_yx_per_um[1:], np.zeros((2, 2)))
    # Different faithful trig evaluations can land on different sides of the exact
    # represented boundary. Successful candidates must satisfy the exact domain.
    assert result.status == "completed_local"


def test_complete_signed_finite_equation_scores_and_initialization(invoke: Any) -> None:
    central, structured, heldout = observations(edge=True)
    solver = ScriptedPowell(explore=True)
    result = invoke(
        central_counts=central, structured_counts=structured, heldout_counts=heldout, solver=solver
    )
    assert result.status == "completed_local" and result.stage == "complete"
    assert result.failure_code is None and solver.entered == 1
    assert result.detector_shape_zyx == SHAPE
    assert result.origin_um_zyx == (10.0, -3.25, 7.5)
    assert result.blank_counts == 5 and result.contrast_counts == 2
    y, s = (central - 5) / 2, (structured - 5) / 2
    centers, maxima, _ = initialization(y)
    initial = result.initial_candidate
    assert type(initial) is PILOT.PilotCandidate
    assert type(result) is PILOT.CalibrationPilotResult
    assert all(type(v) is float for v in result.origin_um_zyx)
    np.testing.assert_allclose(initial.centers_um_zyx, centers, rtol=128 * EPS, atol=0)
    assert initial.centers_um_zyx[0, 2] == RADIUS
    assert initial.centers_um_zyx[-1, 2] == inward_upper(SHAPE[2], D[2])
    assert initial.centers_um_zyx[0, 1] == RADIUS
    nominal = (1.2 / 0.488) * np.array(
        [[math.sin(w), math.cos(w)] for w in (0, math.pi / 3, 2 * math.pi / 3)]
    )
    np.testing.assert_allclose(initial.carriers_yx_per_um, nominal, rtol=64 * EPS, atol=0)
    np.testing.assert_allclose(initial.phases_rad, np.tile(COMMANDS, (3, 1)), rtol=64 * EPS, atol=0)
    np.testing.assert_allclose(
        initial.beam_amplitudes, np.ones(3) / math.sqrt(3), rtol=64 * EPS, atol=0
    )
    for bead in range(3):
        solo = type(initial)(
            **{
                name: (np.eye(3)[bead] if name == "brightness_relative" else getattr(initial, name))
                for name in CANDIDATE_FIELDS
            }
        )
        unit, _, delta = predictions(solo, SHAPE, 128)
        target = maxima[bead] / float(np.max(unit))
        peak = Fraction(float(np.max(unit)))
        relative = delta.total / (peak - delta.total) + Fraction(float(256 * y.size * EPS))
        assert_scalar_close(
            float(initial.brightness_relative[bead]), target, abs(Fraction(target)) * relative
        )
    assert result.optimizer_nfev == 91 and result.optimizer_nit == 4
    assert result.optimizer_status == 0 and result.optimizer_message == "scripted Powell status 0"
    assert isinstance(result.objective_trace, tuple)
    assert result.objective_trace[0].stage == "initial"
    assert sum(v.stage == "initial" for v in result.objective_trace) == 1
    assert [v.stage for v in result.objective_trace] == (
        ["initial"] + ["optimizer"] * 5 + ["center"] * 18 + ["refinement"] * 2
    )
    assert [v.pupil_order for v in result.objective_trace] == [128] * 24 + [256, 512]
    for v in result.objective_trace:
        assert type(v) is PILOT.PilotScore
    for v in result.center_attempts:
        assert type(v) is PILOT.PilotCenterAttempt
    scores = [score for score in result.objective_trace if score.outcome == "scored"]
    assert len([v for v in scores if v.stage == "optimizer"]) == len(solver.values) == 5
    assert len(scores) <= 121
    for score in scores:
        assert_frozen(score, SCORE_FIELDS)
        assert (
            type(score.objective) is float
            and math.isfinite(score.objective)
            and score.objective >= 0
        )
        assert_candidate(score.candidate, SHAPE)
    # Initial, asymmetric signed-field trial, and exact frozen rescores are
    # independent numerical obligations. The positive-brightness run below
    # covers axial/lateral rerasterization. The remaining
    # actual attempts retain full grammar, requested-score and paired checks.
    numerical = [scores[0], [v for v in scores if v.stage == "optimizer"][1]]
    numerical.extend(v for v in scores if v.pupil_order in (256, 512))
    for score in numerical:
        cp, sp, delta = predictions(score.candidate, SHAPE, score.pupil_order)
        target = objective(y, s, cp, sp)
        assert_scalar_close(score.objective, target, loss_allowance(y, s, cp, sp, delta))
    # The deliberately asymmetric public-coordinate trial distinguishes sign, bin rounding,
    # phase anchoring, S normalization and central-only versus structured response.
    asymmetric = [v for v in scores if v.stage == "optimizer"][1].candidate
    x = solver.vectors[1]
    expected_q = np.array(
        [
            [
                x[5 + 2 * o] * (1.515 / 0.488) * math.sin(x[6 + 2 * o] * math.pi),
                x[5 + 2 * o] * (1.515 / 0.488) * math.cos(x[6 + 2 * o] * math.pi),
            ]
            for o in range(3)
        ]
    )
    np.testing.assert_allclose(asymmetric.carriers_yx_per_um, expected_q, rtol=128 * EPS, atol=0)
    np.testing.assert_allclose(
        asymmetric.phases_rad, x[11:].reshape(3, 9) * 2 * math.pi, rtol=64 * EPS, atol=0
    )
    end0, end1 = [v for v in scores if v.stage == "optimizer"][2:4]
    np.testing.assert_array_equal(end0.candidate.beam_amplitudes, [1.0, 0.0, 0.0])
    np.testing.assert_array_equal(end1.candidate.beam_amplitudes, [0.0, 0.0, 1.0])
    np.testing.assert_array_equal(end1.candidate.brightness_relative, np.zeros(3))
    assert result.training_objectives_q128_q256_q512[0] == min(
        v.objective for v in scores if v.pupil_order == 128
    )
    assert_requested_optimizer_scores(result, solver)
    assert_poll_fold(result)
    for q, value in zip((256, 512), result.training_objectives_q128_q256_q512[1:], strict=True):
        score = next(v for v in scores if v.pupil_order == q)
        assert score.stage == "refinement" and score.objective == value
        same_candidate(score.candidate, result.frozen_candidate)
    cp, sp, delta = predictions(result.frozen_candidate, SHAPE, 512)
    assert_prediction_close(result.heldout_prediction, sp[:, :5], delta)
    residual = (heldout - 5) / 2 - sp[:, :5]
    for o, p in itertools.product(range(3), range(5)):
        samples = residual[o, p].ravel()
        mean = math.fsum(float(v) for v in samples) / len(samples)
        rms = math.sqrt(math.fsum(float(v) ** 2 for v in samples) / len(samples))
        reduction = (
            128 * len(samples) * Fraction(float(EPS)) * (Fraction(rms) + abs(Fraction(mean)))
        )
        allowance = delta.total + reduction
        assert_scalar_close(float(result.heldout_residual_mean[o, p]), mean, allowance)
        assert_scalar_close(float(result.heldout_residual_rms[o, p]), rms, allowance)

    # Absorb the distinct non-exploratory poll proof. Two planes are needed
    # for a legal axial movement of a contained 0.05 um sphere. The lateral
    # geometry retains the same 15-column peaks as the smaller default scene.
    shape = (2, 2, 15)
    central, structured, heldout = observations(shape=shape)
    positive = invoke(central_counts=central, structured_counts=structured, heldout_counts=heldout)
    assert (positive.status, positive.stage) == ("completed_local", "complete")
    assert np.all(positive.initial_candidate.brightness_relative > 0)
    assert_poll_fold(positive, numerical_inputs=(central, structured))
    y, s = (central - 5) / 2, (structured - 5) / 2
    for order in (256, 512):
        score = next(v for v in positive.objective_trace if v.pupil_order == order)
        same_candidate(score.candidate, positive.frozen_candidate)
        cp, sp, delta = predictions(score.candidate, shape, order)
        assert np.max(cp) > 0 and np.max(sp) > 0
        target = objective(y, s, cp, sp)
        assert_scalar_close(score.objective, target, loss_allowance(y, s, cp, sp, delta))
        if order == 512:
            assert_prediction_close(positive.heldout_prediction, sp[:, :5], delta)


def assert_poll_fold(result: Any, *, numerical_inputs: tuple[Any, Any] | None = None) -> None:
    """Fold paired public poll records from the strictly best actual training score."""
    trace = iter(v for v in result.objective_trace if v.stage == "center")
    shape = result.detector_shape_zyx
    certified_axes = set()
    incumbent = min(
        (
            v
            for v in result.objective_trace
            if v.stage in ("initial", "optimizer") and v.outcome == "scored"
        ),
        key=lambda v: v.objective,
    )
    assert len(result.center_attempts) == 18
    for bead, axis in itertools.product(range(3), range(3)):
        pair = result.center_attempts[2 * (3 * bead + axis) : 2 * (3 * bead + axis) + 2]
        trials = []
        for sign, attempt in zip((-1, 1), pair, strict=True):
            assert_frozen(attempt, ATTEMPT_FIELDS)
            assert (attempt.bead_index, attempt.axis_index, attempt.sign) == (bead, axis, sign)
            center = incumbent.candidate.centers_um_zyx.copy()
            center[bead, axis] += sign * D[axis] / 8
            contained = all(
                Fraction(float(v)) >= Fraction(RADIUS)
                and Fraction(float(v)) + Fraction(RADIUS) <= shape[a] * Fraction(D[a])
                for c in center
                for a, v in enumerate(c)
            )
            separated = all(
                math.dist(a, b) >= 2 * RADIUS for a, b in itertools.combinations(center, 2)
            )
            score = next(trace)
            assert score.pupil_order == 128
            if not (contained and separated):
                assert attempt.outcome == score.outcome == "infeasible"
                assert score.objective is score.candidate is None
            else:
                assert attempt.outcome == score.outcome == "scored"
                np.testing.assert_array_equal(score.candidate.centers_um_zyx, center)
                for name in (
                    "brightness_relative",
                    "carriers_yx_per_um",
                    "phases_rad",
                    "beam_amplitudes",
                ):
                    np.testing.assert_array_equal(
                        getattr(score.candidate, name), getattr(incumbent.candidate, name)
                    )
                assert_candidate(score.candidate, shape)
                if (
                    numerical_inputs is not None
                    and axis in (0, 2)
                    and axis not in certified_axes
                    and score.candidate.brightness_relative[bead] > 0
                ):
                    old_sites = unit_sites(tuple(incumbent.candidate.centers_um_zyx[bead]), shape)[
                        0
                    ]
                    new_sites = unit_sites(tuple(score.candidate.centers_um_zyx[bead]), shape)[0]
                    if set(map(tuple, old_sites)) != set(map(tuple, new_sites)):
                        central, structured = numerical_inputs
                        y, s = (central - 5) / 2, (structured - 5) / 2
                        cp, sp, delta = predictions(score.candidate, shape, 128)
                        target = objective(y, s, cp, sp)
                        assert_scalar_close(
                            score.objective, target, loss_allowance(y, s, cp, sp, delta)
                        )
                        certified_axes.add(axis)
                trials.append(score)
        best = min(trials, key=lambda v: v.objective) if trials else incumbent
        if best.objective < incumbent.objective:
            incumbent = best
    assert next(trace, None) is None
    same_candidate(incumbent.candidate, result.frozen_candidate)
    assert result.training_objectives_q128_q256_q512[0] == incumbent.objective
    if numerical_inputs is not None:
        assert certified_axes == {0, 2}


@pytest.mark.parametrize("status", [1, 2, 3])
def test_powell_limit_and_other_unsuccessful_outcomes(invoke: Any, status: int) -> None:
    result = invoke(solver=ScriptedPowell(status, explore=True))
    assert result.optimizer_status == status and result.optimizer_nfev == 91
    if status in (1, 2):
        assert result.status == "completed_budget_limited" and result.stage == "complete"
        assert result.heldout_prediction is not None and all(
            v is not None for v in result.training_objectives_q128_q256_q512
        )
    else:
        assert (result.status, result.stage, result.failure_code) == (
            "numerical_incomplete",
            "optimizer",
            "image_only_calibration_pilot_optimizer",
        )
        assert result.center_attempts == () and result.heldout_prediction is None
        assert all(v.pupil_order == 128 for v in result.objective_trace)
        assert result.training_objectives_q128_q256_q512[1:] == (None, None)


def test_installed_powell_is_called_with_finite_budget(invoke: Any) -> None:
    original = scipy.optimize.minimize
    calls = []

    def observed(fun: Any, x0: Any, *args: Any, **kwargs: Any) -> Any:
        count = 0

        def objective_call(*values: Any) -> Any:
            nonlocal count
            count += 1
            return fun(*values)

        answer = original(objective_call, x0, *args, **kwargs)
        calls.append((count, answer))
        return answer

    result = invoke(solver=observed)
    assert len(calls) == 1
    count, answer = calls[0]
    assert 0 < count <= 100
    assert len([v for v in result.objective_trace if v.stage == "optimizer"]) == count
    assert result.optimizer_status == answer.status and result.optimizer_nfev == answer.nfev
    assert result.optimizer_nit == answer.nit and result.optimizer_message == str(answer.message)
    assert result.status in ("completed_local", "completed_budget_limited")


def test_smallest_legal_z_and_readonly_strided_camera_means(invoke: Any) -> None:
    c, s, h = observations()
    means = np.array([-7.0, 999.0, 5.0, 999.0, 7.0, 999.0])[::2]
    means.flags.writeable = False
    result = invoke(
        central_counts=c[:1],
        structured_counts=s[:, :, :1],
        heldout_counts=h[:, :, :1],
        camera_estimate=camera(means_counts=means),
    )
    assert result.status == "completed_local" and result.detector_shape_zyx == SHAPE
    assert_candidate(result.frozen_candidate, SHAPE)
    assert means.flags.writeable is False and means.strides == (16,)


@pytest.mark.parametrize(
    "field,shape",
    [
        ("structured_counts", (2, 9, *SHAPE)),
        ("structured_counts", (3, 8, *SHAPE)),
        ("heldout_counts", (2, 5, *SHAPE)),
        ("heldout_counts", (3, 4, *SHAPE)),
    ],
)
def test_orientation_and_phase_counts_are_not_broadcast(
    invoke: Any, field: str, shape: Any
) -> None:
    with pytest.raises(SimreconError) as caught:
        invoke(**{field: np.zeros(shape)})
    assert caught.value.code == "invalid_image_only_calibration_pilot"


def test_heldout_is_deferred_until_freeze_and_origin_is_only_metadata(invoke: Any) -> None:
    baseline = invoke()
    _, _, h = observations()
    changed = invoke(heldout_counts=-1000 * h, origin_um_zyx=(-1e30, 0, 1e30))
    for name in ("initial_candidate", "frozen_candidate"):
        same_candidate(getattr(baseline, name), getattr(changed, name))
    for name in (
        "optimizer_status",
        "optimizer_message",
        "optimizer_nfev",
        "optimizer_nit",
        "training_objectives_q128_q256_q512",
    ):
        assert getattr(baseline, name) == getattr(changed, name)
    assert len(baseline.center_attempts) == len(changed.center_attempts)
    for a, b in zip(baseline.center_attempts, changed.center_attempts, strict=True):
        assert tuple(getattr(a, name) for name in sorted(ATTEMPT_FIELDS)) == tuple(
            getattr(b, name) for name in sorted(ATTEMPT_FIELDS)
        )
    assert len(baseline.objective_trace) == len(changed.objective_trace)
    for a, b in zip(baseline.objective_trace, changed.objective_trace, strict=True):
        assert (a.stage, a.pupil_order, a.objective, a.outcome) == (
            b.stage,
            b.pupil_order,
            b.objective,
            b.outcome,
        )
        if a.candidate is not None:
            same_candidate(a.candidate, b.candidate)
    np.testing.assert_array_equal(baseline.heldout_prediction, changed.heldout_prediction)
    expected_shift = np.mean((-1000 * h - h) / 2, axis=(-3, -2, -1))
    np.testing.assert_allclose(
        changed.heldout_residual_mean - baseline.heldout_residual_mean,
        expected_shift,
        rtol=256 * h.size * EPS,
        atol=0,
    )


def test_actual_estimated_camera_gauge_and_unused_fields(invoke: Any) -> None:
    # The public estimator supplies this record from images, with unavailable physical gain.
    from simrecon import estimate_scalar_camera

    dark = np.zeros((2, 1, 2))
    blank = np.full((2, 1, 2), 5.0)
    flat = np.full((2, 1, 2), 7.0)
    estimated = estimate_scalar_camera(
        dark, blank_counts=blank, flat_counts=flat, source="actual images"
    )
    assert estimated.gain_counts_per_e is None
    a = invoke(camera_estimate=estimated)
    unused = camera(
        gain_counts_per_e=float("nan"),
        variances_counts2=None,
        frame_means_counts=None,
        frame_variances_counts2=None,
        empirical_mean_se_counts=None,
        information_codes=None,
        source="actual images",
    )
    b = invoke(camera_estimate=unused)
    same_candidate(a.frozen_candidate, b.frozen_candidate)
    assert a.training_objectives_q128_q256_q512 == b.training_objectives_q128_q256_q512
    np.testing.assert_array_equal(a.heldout_prediction, b.heldout_prediction)
    central, structured, heldout = observations()
    affine = invoke(
        central_counts=4 * central - 13,
        structured_counts=4 * structured - 13,
        heldout_counts=4 * heldout - 13,
        camera_estimate=camera(means_counts=np.array([-41.0, 7.0, 15.0]), contrast_counts=8),
    )
    same_candidate(b.frozen_candidate, affine.frozen_candidate)
    np.testing.assert_array_equal(b.heldout_prediction, affine.heldout_prediction)


def test_owned_frozen_records_snapshot_inputs_and_every_candidate(invoke: Any) -> None:
    central, structured, heldout = observations()
    estimate = camera()
    originals = [a.copy() for a in (central, structured, heldout, estimate.means_counts)]
    result = invoke(
        central_counts=central,
        structured_counts=structured,
        heldout_counts=heldout,
        camera_estimate=estimate,
        solver=ScriptedPowell(explore=True),
    )
    assert_frozen(result, RESULT_FIELDS)
    assert result.camera_source == estimate.source
    candidates = [result.initial_candidate, result.frozen_candidate]
    candidates.extend(
        score.candidate for score in result.objective_trace if score.candidate is not None
    )
    arrays = [a for candidate in candidates for a in candidate_arrays(candidate)]
    arrays += [result.heldout_prediction, result.heldout_residual_mean, result.heldout_residual_rms]
    assert [a.shape for a in arrays[-3:]] == [(3, 5, *SHAPE), (3, 5), (3, 5)]
    for a in arrays:
        assert type(a) is np.ndarray and a.dtype == np.dtype("float64") and a.dtype.isnative
        assert a.flags.writeable and a.flags.c_contiguous
        assert all(
            not np.shares_memory(a, b)
            for b in (central, structured, heldout, estimate.means_counts)
        )
    for a, b in itertools.combinations(arrays, 2):
        assert not np.shares_memory(a, b)
    for actual, original in zip(
        (central, structured, heldout, estimate.means_counts), originals, strict=True
    ):
        np.testing.assert_array_equal(actual, original)
    saved = [a.copy() for a in arrays]
    central.fill(-999)
    structured.fill(-999)
    heldout.fill(-999)
    estimate.means_counts.fill(-999)
    for a, b in zip(arrays, saved, strict=True):
        np.testing.assert_array_equal(a, b)
    again = invoke(solver=ScriptedPowell(explore=True))
    other_arrays = candidate_arrays(again.frozen_candidate) + [again.heldout_prediction]
    assert all(not np.shares_memory(a, b) for a in arrays for b in other_arrays)
    same_candidate(result.frozen_candidate, again.frozen_candidate)


@pytest.mark.parametrize(
    "styles",
    [
        pytest.param(("endian", "strided", "fortran", "readonly"), id="equivalent-native-values"),
        pytest.param(("integer",), id="integer"),
        pytest.param(("unsigned",), id="unsigned"),
        pytest.param(("float32",), id="float32"),
        pytest.param(("wide",), id="wide"),
    ],
)
def test_legitimate_array_storage_and_conversion(invoke: Any, styles: tuple[str, ...]) -> None:
    reference = None
    reference_inputs = []
    for style in styles:
        original = observations()
        converted = []
        for a in original:
            if style == "endian":
                value = a.astype(">f8")
            elif style == "strided":
                storage = np.empty((*a.shape[:-1], 2 * a.shape[-1]))
                storage[..., ::2] = a
                value = storage[..., ::2]
            elif style == "fortran":
                value = np.asfortranarray(a)
            elif style == "readonly":
                value = a.copy()
                value.flags.writeable = False
            elif style == "integer":
                value = a.astype(np.int16)
            elif style == "unsigned":
                value = a.astype(np.uint16)
            elif style == "float32":
                value = a.astype(np.float32)
            else:
                value = a.astype(np.longdouble)
                value += np.longdouble(2) ** -60
            converted.append(value)
        normalized = [np.array(a, dtype=np.float64) for a in converted]
        if reference is None:
            reference_inputs = [a.copy() for a in normalized]
            for a in reference_inputs:
                a.flags.writeable = False
            reference = invoke(
                central_counts=normalized[0],
                structured_counts=normalized[1],
                heldout_counts=normalized[2],
            )
        else:
            for a, saved in zip(normalized, reference_inputs, strict=True):
                np.testing.assert_array_equal(a, saved)
        snapshots = [a.copy() for a in converted]
        flags = [(a.strides, a.flags.writeable) for a in converted]
        actual = invoke(
            central_counts=converted[0], structured_counts=converted[1], heldout_counts=converted[2]
        )
        assert actual.status == reference.status
        same_candidate(actual.frozen_candidate, reference.frozen_candidate)
        np.testing.assert_array_equal(actual.heldout_prediction, reference.heldout_prediction)
        for a, saved, flag in zip(converted, snapshots, flags, strict=True):
            np.testing.assert_array_equal(a, saved)
            assert (a.strides, a.flags.writeable) == flag


class ArraySubclass(np.ndarray):
    """An explicitly unsupported raw-array representation."""


@pytest.mark.parametrize(
    "field,kind",
    [
        *(
            (field, kind)
            for field in ("central_counts", "structured_counts", "heldout_counts")
            for kind in (
                "list",
                "bool",
                "complex",
                "object",
                "subclass",
                "nan",
                "rank",
                "empty",
                "mismatch",
            )
        ),
        ("central_counts", "inf"),
    ],
)
def test_invalid_image_representations_and_shapes(invoke: Any, field: str, kind: str) -> None:
    images: dict[str, Any] = dict(
        zip(("central_counts", "structured_counts", "heldout_counts"), observations(), strict=True)
    )
    a = images[field]
    if kind == "list":
        value = a.tolist()
    elif kind in ("bool", "complex", "object"):
        value = a.astype({"bool": bool, "complex": complex, "object": object}[kind])
    elif kind == "subclass":
        value = a.view(ArraySubclass)
    elif kind in ("nan", "inf"):
        value = a.copy()
        value.flat[0] = float(kind)
    elif kind == "rank":
        value = a[..., 0]
    elif kind == "empty":
        value = a[..., :0]
    else:
        value = a[..., :-1]
    with pytest.raises(SimreconError) as caught:
        invoke(**{field: value})
    assert caught.value.code == "invalid_image_only_calibration_pilot" and str(caught.value).strip()


@pytest.mark.parametrize("shape", [(0, 2, 16), (2, 1, 16), (2, 2, 1)])
def test_empty_or_physically_short_axis_rejects(invoke: Any, shape: Any) -> None:
    with pytest.raises(SimreconError) as caught:
        invoke(
            central_counts=np.zeros(shape),
            structured_counts=np.zeros((3, 9, *shape)),
            heldout_counts=np.zeros((3, 5, *shape)),
        )
    assert caught.value.code == "invalid_image_only_calibration_pilot"


@pytest.mark.parametrize(
    "field,value",
    [
        ("camera_estimate", None),
        ("camera_estimate", {}),
        ("origin_um_zyx", [0, 0, 0]),
        ("origin_um_zyx", (0, 0)),
        ("origin_um_zyx", (True, 0, 0)),
        ("origin_um_zyx", (np.float64(0), 0, 0)),
        ("origin_um_zyx", (float("nan"), 0, 0)),
        ("origin_um_zyx", (0, float("inf"), 0)),
        ("origin_um_zyx", (10**1000, 0, 0)),
    ],
)
def test_invalid_camera_record_and_origin(invoke: Any, field: str, value: Any) -> None:
    with pytest.raises(SimreconError) as caught:
        invoke(**{field: value})
    assert caught.value.code == "invalid_image_only_calibration_pilot"


@pytest.mark.parametrize(
    "changes",
    [
        {"means_counts": [0.0, 5.0, 7.0]},
        {"means_counts": np.array([0.0, 5.0, 7.0], dtype=">f8")},
        {"means_counts": np.array([0, 5, 7])},
        {"means_counts": np.zeros((1, 3))},
        {"means_counts": np.zeros(2)},
        {"means_counts": np.array([0.0, np.nan, 7.0])},
        {"means_counts": np.array([0.0, 5.0, 7.0]).view(ArraySubclass)},
        {"contrast_counts": True},
        {"contrast_counts": np.float64(2)},
        {"contrast_counts": np.inf},
        {"contrast_counts": 10**1000},
        {"source": " \t"},
        {"source": None},
    ],
)
def test_direct_camera_construction_does_not_bypass_consumed_validation(
    invoke: Any, changes: Any
) -> None:
    with pytest.raises(SimreconError) as caught:
        invoke(camera_estimate=camera(**changes))
    assert caught.value.code == "invalid_image_only_calibration_pilot"


def test_original_and_converted_nonfinite_values_are_invalid(invoke: Any) -> None:
    # A wider native representation is used only if the platform actually provides one.
    a = np.zeros(SHAPE, dtype=np.longdouble)
    a.flat[0] = np.finfo(np.longdouble).max
    if np.finfo(np.longdouble).max <= np.finfo(float).max:
        a.flat[0] = np.longdouble(np.inf)
    with np.errstate(all="raise"), pytest.raises(SimreconError) as caught:
        invoke(central_counts=a)
    assert caught.value.code == "invalid_image_only_calibration_pilot"


@pytest.mark.parametrize("case", ["subtract", "divide", "brightness", "loss"])
def test_required_nonfinite_arithmetic_has_truthful_stage(invoke: Any, case: str) -> None:
    changes: dict[str, Any] = {}
    stage = "normalization"
    if case == "subtract":
        changes = {
            "central_counts": np.full(SHAPE, np.finfo(float).max),
            "camera_estimate": camera(means_counts=np.array([0.0, -np.finfo(float).max, 0.0])),
        }
    elif case == "divide":
        changes = {"camera_estimate": camera(contrast_counts=float(np.nextafter(0.0, 1.0)))}
    elif case == "brightness":
        central = np.full(SHAPE, 5.0)
        central[0, 0, [0, 7, 14]] = np.finfo(float).max
        changes = {"central_counts": central}
        # h <= pi*(NA/lambda)^2 and pixel area=0.0064 um^2, so unit response
        # <=0.143 and these finite Y require brightness greater than float64 max.
        stage = "initialization"
    elif case == "loss":
        changes = {"structured_counts": np.full((3, 9, *SHAPE), 1e200)}
        stage = "initial"
    with warnings.catch_warnings(record=True) as observed, np.errstate(all="raise"):
        warnings.simplefilter("always")
        selected_filters = list(warnings.filters)
        result = invoke(**changes)
        assert np.geterr() == dict.fromkeys(("divide", "over", "under", "invalid"), "raise")
        assert warnings.filters == selected_filters
    assert not any(issubclass(w.category, RuntimeWarning) for w in observed)
    assert (result.status, result.stage, result.failure_code) == (
        "numerical_incomplete",
        stage,
        "image_only_calibration_pilot_range",
    )
    assert result.heldout_prediction is None
    assert result.heldout_residual_mean is result.heldout_residual_rms is None
    if stage == "initial":
        failed = result.objective_trace[-1]
        assert (failed.stage, failed.pupil_order, failed.outcome) == (
            "initial",
            128,
            "numerical_incomplete",
        )
        assert failed.objective is failed.candidate is None
        assert result.optimizer_status is None and result.center_attempts == ()


def test_large_finite_heldout_rms_allows_stable_evaluation_or_truthful_late_range(
    invoke: Any,
) -> None:
    baseline = invoke()
    result = invoke(heldout_counts=np.full((3, 5, *SHAPE), 1e200))
    same_candidate(baseline.frozen_candidate, result.frozen_candidate)
    assert baseline.training_objectives_q128_q256_q512 == result.training_objectives_q128_q256_q512
    if result.status == "numerical_incomplete":
        assert (
            result.stage == "heldout"
            and result.failure_code == "image_only_calibration_pilot_range"
        )
        assert result.heldout_residual_mean is result.heldout_residual_rms is None
    else:
        # Squaring 5e199 overflows, but its RMS is representable. A scaled
        # float64 reduction is a legitimate alternative to that overflow.
        assert result.status == "completed_local" and result.failure_code is None
        np.testing.assert_allclose(
            result.heldout_residual_mean, 5e199, rtol=128 * math.prod(SHAPE) * EPS, atol=0
        )
        np.testing.assert_allclose(
            result.heldout_residual_rms, 5e199, rtol=128 * math.prod(SHAPE) * EPS, atol=0
        )


def test_ordinary_correction_underflow_remains_an_information_outcome(invoke: Any) -> None:
    result = invoke(
        central_counts=np.full(SHAPE, np.nextafter(0.0, 1.0)),
        camera_estimate=camera(
            means_counts=np.zeros(3), contrast_counts=float(np.finfo(float).max)
        ),
    )
    assert_empty(result, "initialization_failed", "initialization")


def test_heldout_correction_overflow_cannot_enter_training(invoke: Any) -> None:
    d = float(np.nextafter(0.0, 1.0))
    y = np.zeros(SHAPE)
    y[0, 0, [0, 7, 14]] = 8
    central = y * d
    estimate = camera(means_counts=np.array([0.0, 0.0, d]), contrast_counts=d)
    common = {
        "central_counts": central,
        "structured_counts": np.zeros((3, 9, *SHAPE)),
        "camera_estimate": estimate,
    }
    baseline = invoke(heldout_counts=np.zeros((3, 5, *SHAPE)), **common)
    with np.errstate(all="raise"):
        result = invoke(heldout_counts=np.full((3, 5, *SHAPE), np.finfo(float).max), **common)
    assert (result.status, result.stage, result.failure_code) == (
        "numerical_incomplete",
        "heldout",
        "image_only_calibration_pilot_range",
    )
    same_candidate(result.frozen_candidate, baseline.frozen_candidate)
    assert result.training_objectives_q128_q256_q512 == baseline.training_objectives_q128_q256_q512
    assert result.heldout_residual_mean is result.heldout_residual_rms is None


@pytest.mark.parametrize("order", [256, 512])
def test_late_known_optics_range_preserves_only_scored_records(
    invoke: Any, monkeypatch: Any, order: int
) -> None:
    original = OPTICS.expected_images
    failure = SimreconError("simulation_optics_range", "injected public optics evaluation failure")
    entered = []

    def observed(*args: Any, **kwargs: Any) -> Any:
        if kwargs["pupil_order"] == order:
            entered.append(order)
            raise failure
        return original(*args, **kwargs)

    monkeypatch.setattr(OPTICS, "expected_images", observed)
    result = invoke()
    if entered:
        assert (result.status, result.stage, result.failure_code) == (
            "numerical_incomplete",
            f"refinement_q{order}",
            "simulation_optics_range",
        )
        assert result.heldout_prediction is None
        assert result.training_objectives_q128_q256_q512[0] is not None
        if order == 512:
            assert result.training_objectives_q128_q256_q512[1] is not None
        assert result.training_objectives_q128_q256_q512[(1 if order == 256 else 2)] is None
        failed = result.objective_trace[-1]
        assert (failed.stage, failed.pupil_order, failed.outcome) == (
            "refinement",
            order,
            "numerical_incomplete",
        )
        assert failed.objective is failed.candidate is None
    else:
        # A faithful cached/equation-equivalent bypass is legitimate; no private backend mandate.
        assert result.status == "completed_local"
        assert_completed_bypass(result)


def test_center_dependency_failure_records_the_actual_failed_attempt(
    invoke: Any, monkeypatch: Any
) -> None:
    original = OPTICS.expected_images
    state = {"poll": False, "entered": False}

    def observed(*args: Any, **kwargs: Any) -> Any:
        if state["poll"] and kwargs["pupil_order"] == 128:
            state["entered"] = True
            raise SimreconError("simulation_optics_range", "public poll failure")
        return original(*args, **kwargs)

    def solve(*args: Any, **kwargs: Any) -> Any:
        answer = ScriptedPowell()(*args, **kwargs)
        state["poll"] = True
        return answer

    monkeypatch.setattr(OPTICS, "expected_images", observed)
    result = invoke(solver=solve)
    if state["entered"]:
        assert (result.status, result.stage, result.failure_code) == (
            "numerical_incomplete",
            "center",
            "simulation_optics_range",
        )
        assert result.center_attempts[-1].outcome == "numerical_incomplete"
        last = result.objective_trace[-1]
        assert last.stage == "center" and last.outcome == "numerical_incomplete"
        assert last.candidate is last.objective is None
        assert result.training_objectives_q128_q256_q512[1:] == (None, None)
        assert result.heldout_prediction is None
    else:
        assert result.status == "completed_local"
        assert_completed_bypass(result)


@pytest.mark.parametrize("stage", ["optimizer", "heldout"])
def test_known_range_at_optimizer_or_heldout_preserves_stage_and_code(
    invoke: Any, monkeypatch: Any, stage: str
) -> None:
    original = OPTICS.expected_images
    state = {"inside_optimizer": False, "entered": False}

    def observed(*args: Any, **kwargs: Any) -> Any:
        target = (
            state["inside_optimizer"]
            if stage == "optimizer"
            else kwargs["pupil_order"] == 512 and np.shape(kwargs["phases_rad"])[1] == 5
        )
        if target:
            state["entered"] = True
            raise SimreconError("simulation_optics_range", "public late-stage range sentinel")
        return original(*args, **kwargs)

    def solve(fun: Any, x0: Any, *args: Any, **kwargs: Any) -> Any:
        bound = MINIMIZE_SIGNATURE.bind(fun, x0, *args, **kwargs)
        bound.apply_defaults()
        vector = np.array(x0, copy=True)
        vector[11] = 0.123
        state["inside_optimizer"] = True
        try:
            value = fun(vector, *bound.arguments["args"])
        finally:
            state["inside_optimizer"] = False
        return OptimizeResult(
            x=vector,
            fun=value,
            success=True,
            status=0,
            message="public objective probe",
            nfev=1,
            nit=1,
        )

    monkeypatch.setattr(OPTICS, "expected_images", observed)
    result = invoke(solver=solve)
    if state["entered"]:
        assert (result.status, result.stage, result.failure_code) == (
            "numerical_incomplete",
            stage,
            "simulation_optics_range",
        )
        assert result.heldout_residual_mean is result.heldout_residual_rms is None
        if stage == "optimizer":
            last = result.objective_trace[-1]
            assert last.stage == "optimizer" and last.outcome == "numerical_incomplete"
            assert last.objective is last.candidate is None
            assert result.center_attempts == ()
        else:
            assert all(v is not None for v in result.training_objectives_q128_q256_q512)
            assert result.objective_trace[-1].stage == "refinement"
            assert result.objective_trace[-1].outcome == "scored"
    else:
        assert result.status == "completed_local"
        assert_completed_bypass(result)


@pytest.mark.parametrize("fault_order", [128, 256])
def test_unusable_initial_central_response_is_an_information_outcome(
    invoke: Any, monkeypatch: Any, fault_order: int
) -> None:
    original = OPTICS.expected_images
    entered = []
    clock = {"after_solver": False}

    def solve(*args: Any, **kwargs: Any) -> Any:
        answer = ScriptedPowell()(*args, **kwargs)
        clock["after_solver"] = True
        return answer

    def observed(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        central = tuple(kwargs["beam_amplitudes"]) == (1.0, 0.0, 0.0)
        target = kwargs["pupil_order"] == fault_order and (
            fault_order == 256 or not clock["after_solver"]
        )
        if central and target:
            entered.append((kwargs["pupil_order"], clock["after_solver"]))
            return np.zeros_like(result)
        return result

    monkeypatch.setattr(OPTICS, "expected_images", observed)
    result = invoke(solver=solve)
    if result.status == "initialization_failed":
        # Only the pre-solver Q128 central work can be initialization. Its
        # arguments cannot distinguish B_start evaluation from later initial
        # scoring, so an entered observer alone does not require this outcome.
        assert fault_order == 128 and entered and not clock["after_solver"]
        assert_empty(result, "initialization_failed", "initialization")
    else:
        # Includes a partial bypass of B_start followed by faulted initial
        # scoring, and the explicit late-Q256 central-only fault. That fault
        # changes finite scored work, not a completed initialization. Once a
        # deliberately wrong zero image enters a cache, no physical prediction
        # oracle is promised for downstream uses of that corrupted dependency.
        assert result.status == "completed_local"
        assert_initial_unit_scale(result.initial_candidate, (observations()[0] - 5) / 2)
        assert result.failure_code is None
        assert all(
            v is not None and math.isfinite(v) for v in result.training_objectives_q128_q256_q512
        )
        assert_candidate(result.frozen_candidate, SHAPE)
        for array in (
            result.heldout_prediction,
            result.heldout_residual_mean,
            result.heldout_residual_rms,
        ):
            assert array is not None and np.isfinite(array).all()
    if not entered:
        # Only an unmodified full bypass promises the independent physical
        # output. Partial initial bypass is proved by the unit-scale check above.
        assert_completed_bypass(result)


def assert_completed_bypass(result: Any) -> None:
    """Require complete finite public work from a legal dependency bypass."""
    assert (result.status, result.stage, result.failure_code) == (
        "completed_local",
        "complete",
        None,
    )
    assert_candidate(result.initial_candidate, SHAPE)
    assert_candidate(result.frozen_candidate, SHAPE)
    assert len(result.center_attempts) == 18
    assert all(
        v is not None and math.isfinite(v) for v in result.training_objectives_q128_q256_q512
    )
    assert result.heldout_prediction.shape == (3, 5, *SHAPE)
    for value in (
        result.heldout_prediction,
        result.heldout_residual_mean,
        result.heldout_residual_rms,
    ):
        assert value is not None and np.isfinite(value).all()


def assert_initial_unit_scale(candidate: Any, y: Any) -> None:
    """Check a bypassed initialization from public observations and one-electron units."""
    shape = (int(y.shape[0]), int(y.shape[1]), int(y.shape[2]))
    centers, maxima, _ = initialization(y)
    np.testing.assert_allclose(candidate.centers_um_zyx, centers, rtol=128 * EPS, atol=0)
    for bead in range(3):
        solo = type(candidate)(
            **{
                name: (
                    np.eye(3)[bead] if name == "brightness_relative" else getattr(candidate, name)
                )
                for name in CANDIDATE_FIELDS
            }
        )
        unit, _, delta = predictions(solo, shape, 128)
        peak = float(np.max(unit))
        target = float(maxima[bead] / peak)
        allowance = abs(Fraction(target)) * (
            delta.total / (Fraction(peak) - delta.total) + Fraction(float(256 * y.size * EPS))
        )
        assert_scalar_close(float(candidate.brightness_relative[bead]), target, allowance)


def assert_fault_work_stage(result: Any, code: str, work: dict[str, Any]) -> None:
    """Assert only the stage distinctions observable at the faulted public work."""
    assert result.status == "numerical_incomplete" and result.failure_code == code
    if work["dependency"] == "source":
        allowed = {
            "initialization",
            "initial",
            "optimizer",
            "center",
            "refinement_q256",
            "refinement_q512",
            "heldout",
        }
        if work["after_solver"]:
            allowed -= {"initialization", "initial"}
    elif work["order"] == 256:
        allowed = {"refinement_q256"}
    elif work["order"] == 512:
        allowed = {"refinement_q512", "heldout"}
    elif work["after_solver"]:
        allowed = {"center", "optimizer"}
    else:
        allowed = {"initial", "optimizer"}
        if work["central"]:
            allowed.add("initialization")
    assert result.stage in allowed and result.heldout_prediction is None
    if result.stage == "initialization":
        assert result.objective_trace == () and result.initial_candidate is None
    elif result.stage == "heldout":
        assert all(v is not None for v in result.training_objectives_q128_q256_q512)
        assert result.objective_trace[-1].outcome == "scored"
    elif result.stage != "optimizer" or (
        result.objective_trace and result.objective_trace[-1].outcome == "numerical_incomplete"
    ):
        last = result.objective_trace[-1]
        expected_stage = "refinement" if result.stage.startswith("refinement_") else result.stage
        assert last.stage == expected_stage and last.outcome == "numerical_incomplete"
        assert last.objective is last.candidate is None


@pytest.mark.parametrize("fault_scope", ["any", "later_work"])
@pytest.mark.parametrize(
    "dependency,code",
    [("source", "simulation_source_range"), ("optics", "simulation_optics_range")],
)
def test_initial_known_dependency_range_is_not_a_fabricated_success(
    invoke: Any, monkeypatch: Any, dependency: str, code: str, fault_scope: str
) -> None:
    module, name = (
        (SOURCE, "make_sources") if dependency == "source" else (OPTICS, "expected_images")
    )
    entered = []
    original = getattr(module, name)
    clock = {"after_solver": False}

    def solve(*args: Any, **kwargs: Any) -> Any:
        answer = ScriptedPowell()(*args, **kwargs)
        clock["after_solver"] = True
        return answer

    def fail(*args: Any, **kwargs: Any) -> Any:
        work = {"dependency": dependency, "after_solver": clock["after_solver"]}
        if dependency == "optics":
            work.update(
                order=kwargs["pupil_order"],
                central=tuple(kwargs["beam_amplitudes"]) == (1.0, 0.0, 0.0),
            )
        later_work = clock["after_solver"] if dependency == "source" else not work["central"]
        if fault_scope == "later_work" and not later_work:
            # Permit initial central work through this public observer and
            # fault only later structured/profile work. Partial bypass is not
            # confused with initialization merely because this function enters.
            return original(*args, **kwargs)
        entered.append(work)
        raise SimreconError(code, "public dependency range sentinel")

    monkeypatch.setattr(module, name, fail)
    result = invoke(solver=solve)
    if entered:
        assert len(entered) == 1
        assert_fault_work_stage(result, code, entered[0])
    else:
        assert result.status == "completed_local"
        assert_completed_bypass(result)


@pytest.mark.parametrize(
    ("dependency", "work_scope"),
    [("optics", "any"), ("source", "any"), ("source", "after_solver")],
)
@pytest.mark.parametrize(
    "failure",
    [
        MemoryError("allocation sentinel"),
        ValueError("unrelated sentinel"),
        SimreconError("invalid_simulation_optics", "domain sentinel"),
    ],
)
def test_unrelated_dependency_failures_propagate_unchanged(
    invoke: Any, monkeypatch: Any, failure: Any, dependency: str, work_scope: str
) -> None:
    entered = []
    after_solver = False
    owner, name = (
        (OPTICS, "expected_images") if dependency == "optics" else (SOURCE, "make_sources")
    )
    original = getattr(owner, name)
    expected_failure = failure
    if dependency == "source" and isinstance(failure, SimreconError):
        expected_failure = SimreconError("invalid_simulation_source", "domain sentinel")

    def solve(*args: Any, **kwargs: Any) -> Any:
        nonlocal after_solver
        answer = ScriptedPowell()(*args, **kwargs)
        after_solver = True
        return answer

    def fail(*args: Any, **kwargs: Any) -> Any:
        if work_scope == "after_solver" and not after_solver:
            return original(*args, **kwargs)
        entered.append(after_solver)
        raise expected_failure

    monkeypatch.setattr(owner, name, fail)
    try:
        result = invoke(solver=solve)
    except BaseException as caught:
        assert entered and caught is expected_failure
    else:
        assert not entered and result.status == "completed_local"
        assert_completed_bypass(result)
    print("PUBLIC_DEPENDENCY_FAULT", dependency, work_scope, "fault_after_solver", entered)


def test_one_electron_dependency_units_and_unrelated_warnings(
    invoke: Any, monkeypatch: Any
) -> None:
    source_calls, optics_calls = [], []
    source_original, optics_original = SOURCE.make_sources, OPTICS.expected_images

    def source_observer(catalogue: Any, **kwargs: Any) -> Any:
        source_calls.append(True)
        assert catalogue.shape == (1, 5) and catalogue[0, 3] == RADIUS and catalogue[0, 4] == 1
        assert kwargs == {
            "detector_shape_zyx": SHAPE,
            "detector_spacing_um_zyx": D,
            "source_refinement_zyx": (8, 8, 8),
        }
        return source_original(catalogue, **kwargs)

    def optics_observer(source_e: Any, **kwargs: Any) -> Any:
        optics_calls.append(kwargs["pupil_order"])
        nonzero = source_e[source_e > 0]
        assert nonzero.size > 0
        np.testing.assert_array_equal(
            nonzero, np.full(nonzero.shape, float(Fraction(1, nonzero.size)))
        )
        assert source_e.shape == tuple(8 * n for n in SHAPE)
        for key, value in {
            "detector_spacing_um_zyx": D,
            "source_refinement_zyx": (8, 8, 8),
            "excitation_um": 0.488,
            "emission_um": 0.525,
            "refractive_index": 1.515,
            "detection_na": 1.4,
            "pixel_subsamples_yx": (2, 2),
        }.items():
            assert kwargs[key] == value
        if len(optics_calls) == 1:
            warnings.warn("public unrelated warning", UserWarning, stacklevel=2)
            warnings.warn("public unrelated deprecation", DeprecationWarning, stacklevel=2)
            warnings.warn("public unrelated runtime warning", RuntimeWarning, stacklevel=2)
        return optics_original(source_e, **kwargs)

    monkeypatch.setattr(SOURCE, "make_sources", source_observer)
    monkeypatch.setattr(OPTICS, "expected_images", optics_observer)
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        result = invoke()
    assert result.status == "completed_local"
    if optics_calls:
        assert {UserWarning, DeprecationWarning, RuntimeWarning} <= {w.category for w in observed}
    assert_completed_bypass(result)


def test_numpy_warning_rng_policies_and_inputs_survive_success_and_failure(invoke: Any) -> None:
    state = np.random.get_state()
    policy = np.geterr()
    filters = list(warnings.filters)
    try:
        np.seterr(all="raise")
        selected = np.geterr()
        result = invoke()
        assert result.status == "completed_local" and np.geterr() == selected
        with pytest.raises(SimreconError):
            invoke(origin_um_zyx=(False, 0, 0))
        assert np.geterr() == selected and warnings.filters == filters
        after = np.random.get_state()
        assert state[0] == after[0] and state[2:] == after[2:]
        np.testing.assert_array_equal(state[1], after[1])
    finally:
        np.seterr(**policy)


def test_python_binding_errors_are_ordinary_type_errors() -> None:
    with pytest.raises(TypeError):
        PILOT.fit_small_pilot()
    c, s, h = observations()
    with pytest.raises(TypeError):
        PILOT.fit_small_pilot(c, s, h, camera(), (0, 0, 0))
    with pytest.raises(TypeError):
        PILOT.fit_small_pilot(
            c,
            structured_counts=s,
            heldout_counts=h,
            camera_estimate=camera(),
            origin_um_zyx=(0, 0, 0),
            seed=0,
        )
