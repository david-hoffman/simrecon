"""A1 public-entry keepers; the complete obligation/risk ledger is in the fixture.

No skip, xfail, product stub or test-only production seam. An absent module is
unavailable baseline evidence, not a product-red scientific result. All numerical
expectations come from the adopted contract and independent scalar mathematics.
"""

from __future__ import annotations

import importlib
import math
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from image_only_specimen_fit_fixture import (
    cache_application_reference,
    camera,
    decimal_gradient,
    decimal_score,
    decimal_seed,
    first_step_bounds,
    inputs,
    invoke,
    large_signal_inputs,
    nonuniform_enclosure,
    nonuniform_inputs,
    observe_public,
    one_pixel_physical_weight,
    projected_gradient,
    replace_camera,
    tiny_cache_exact_reference,
)

COUNTS = [
    "cache_attempted",
    "cache_completed",
    "cache_failed",
    "forward_attempted",
    "forward_completed",
    "forward_failed",
    "adjoint_attempted",
    "adjoint_completed",
    "adjoint_failed",
    "score_attempts",
    "scores_completed",
    "gradient_attempts",
    "gradients_completed",
    "seed_attempts",
    "seeds_completed",
    "iterations_started",
    "trials_attempted",
    "trials_accepted",
    "trials_rejected",
    "trials_unrepresentable",
    "trials_stagnated",
    "best_updates",
]
RESULT_FIELDS = [
    "status",
    "stage",
    "stop_reason",
    "message",
    "failure_code",
    "failure_component",
    "detector_shape_zyx",
    "source_shape_zyx",
    "detector_spacing_um_zyx",
    "source_spacing_um_zyx",
    "specimen_origin_um_zyx",
    "excitation_um",
    "emission_um",
    "refractive_index",
    "detection_na",
    "pixel_samples_yx",
    "pupil_order",
    "regularization",
    "max_iterations",
    "max_backtracking_trials",
    "camera_means_counts",
    "blank_counts",
    "contrast_counts",
    "camera_source",
    "carriers_yx_per_um",
    "phases_at_specimen_origin_rad",
    "beam_amplitudes",
    "illumination_source",
    "source_relative",
    "initial_score",
    "best_score",
    "last_complete_gradient",
    "seed_step",
    "attempt_trace",
    "call_trace",
    "counts",
]


@pytest.fixture(scope="module")
def fit_module() -> Any:
    return importlib.import_module("scripts.image_only_specimen_fit")


def assert_float(value: Any, *, nonnegative: bool = False) -> None:
    assert type(value) is float
    assert math.isfinite(value)
    if nonnegative:
        assert value >= 0


def assert_array(value: Any, shape: tuple[int, ...], dtype: Any) -> None:
    assert type(value) is np.ndarray
    assert value.shape == shape
    assert value.dtype == np.dtype(dtype) and value.dtype.isnative
    assert value.flags.owndata and value.flags.writeable and value.flags.c_contiguous
    assert np.isfinite(value).all()


def assert_score(score: Any, module: Any) -> None:
    assert isinstance(score, module.SpecimenScore)
    assert type(score.candidate_id) is int and score.candidate_id >= 0
    for name in ("data_objective", "penalty_objective", "total_objective"):
        assert_float(getattr(score, name), nonnegative=True)
    assert score.total_objective == score.data_objective + score.penalty_objective
    for name in ("residual_mean", "residual_rms"):
        values = getattr(score, name)
        assert type(values) is tuple and len(values) == 3
        for row in values:
            assert type(row) is tuple and len(row) == 5
            for value in row:
                assert_float(value, nonnegative=name == "residual_rms")


def assert_initial_score(result: Any, values: dict[str, Any]) -> None:
    raw = values["raw_counts"]
    expected = decimal_score(
        np.zeros(result.source_shape_zyx, dtype=np.float32),
        [np.zeros(raw.shape[1:], dtype=np.float64) for _ in range(3)],
        values,
    )
    score = result.initial_score
    assert score.candidate_id == 0
    # No inverse approximation allowance: inverse zero-source is exactly zero.
    for actual, target in zip(
        (score.data_objective, score.penalty_objective, score.total_objective),
        expected[:3],
        strict=True,
    ):
        assert math.isclose(actual, target, rel_tol=128 * np.finfo(np.float64).eps, abs_tol=0)
    for actual, target in zip((score.residual_mean, score.residual_rms), expected[3:], strict=True):
        np.testing.assert_allclose(actual, target, rtol=128 * np.finfo(np.float64).eps, atol=0)


def assert_protocol(result: Any, module: Any) -> None:
    """Public relational grammar, selection and accounting; no numerical truth claim."""
    assert isinstance(result, module.SpecimenFitResult)
    assert all(hasattr(result, name) for name in RESULT_FIELDS)
    for name in ("detector_shape_zyx", "source_shape_zyx", "pixel_samples_yx"):
        vector = getattr(result, name)
        assert type(vector) is tuple
        assert len(vector) == (2 if name == "pixel_samples_yx" else 3)
        assert all(type(x) is int and x > 0 for x in vector)
    for name in ("detector_spacing_um_zyx", "source_spacing_um_zyx", "specimen_origin_um_zyx"):
        vector = getattr(result, name)
        if name == "source_spacing_um_zyx" and vector is None:
            continue
        assert type(vector) is tuple and len(vector) == 3
        for x in vector:
            assert_float(x)
            if name != "specimen_origin_um_zyx":
                assert x > 0
    for name in ("pupil_order", "max_iterations", "max_backtracking_trials"):
        assert type(getattr(result, name)) is int and getattr(result, name) > 0
    for name in (
        "regularization",
        "blank_counts",
        "contrast_counts",
        "excitation_um",
        "emission_um",
        "refractive_index",
        "detection_na",
    ):
        assert_float(getattr(result, name))
    for name, shape in (
        ("camera_means_counts", (3,)),
        ("carriers_yx_per_um", (3, 2)),
        ("phases_at_specimen_origin_rad", (3, 5)),
        ("beam_amplitudes", (3,)),
    ):
        assert_array(getattr(result, name), shape, np.float64)
    for name in ("camera_source", "illumination_source"):
        assert type(getattr(result, name)) is str and getattr(result, name).strip()
    assert type(result.message) is str and result.message.strip()
    assert type(result.attempt_trace) is tuple and type(result.call_trace) is tuple
    assert isinstance(result.counts, module.SpecimenFitCounts)
    for name in COUNTS:
        value = getattr(result.counts, name)
        assert type(value) is int and value >= 0
    c = result.counts
    for operation in ("cache", "forward", "adjoint"):
        assert getattr(c, operation + "_attempted") == (
            getattr(c, operation + "_completed") + getattr(c, operation + "_failed")
        )
        entries = [
            call
            for call in result.call_trace
            if call.operation == ("build_kernel_cache" if operation == "cache" else operation)
        ]
        assert len(entries) == getattr(c, operation + "_attempted")
        assert sum(e.outcome == "completed" for e in entries) == getattr(
            c, operation + "_completed"
        )
        assert sum(e.outcome == "range_failure" for e in entries) == getattr(
            c, operation + "_failed"
        )
    for index, call in enumerate(result.call_trace, 1):
        assert isinstance(call, module.SpecimenFitCall)
        assert type(call.call_index) is int and call.call_index == index
        assert call.operation in ("build_kernel_cache", "forward", "adjoint")
        assert call.purpose in ("cache", "score", "gradient", "curvature_seed")
        assert call.outcome in ("completed", "range_failure")
        if call.outcome == "completed":
            assert call.failure_code is None
        else:
            assert call.failure_code == "simulation_inverse_operator_range"
        if call.purpose == "cache":
            assert call.operation == "build_kernel_cache"
            assert call.candidate_id is None and call.orientation is None
        else:
            assert type(call.candidate_id) is int and call.candidate_id >= 0
            assert type(call.orientation) is int and call.orientation in (0, 1, 2)
            if call.purpose in ("score", "curvature_seed"):
                assert call.operation == "forward"
            if call.purpose == "curvature_seed":
                assert call.candidate_id == 0
    complete_scores, complete_gradients = [], []
    incumbent = None
    previous_trial = None
    for index, attempt in enumerate(result.attempt_trace):
        assert isinstance(attempt, module.SpecimenFitAttempt)
        for name in ("candidate_id", "iteration", "trial"):
            assert type(getattr(attempt, name)) is int
        assert attempt.candidate_id == index
        assert attempt.outcome in (
            "initial_scored",
            "accepted",
            "rejected",
            "unrepresentable",
            "stagnated",
            "score_incomplete",
        )
        if index == 0:
            assert attempt.iteration == attempt.trial == 0
            assert attempt.from_candidate_id is None and attempt.gradient_candidate_id is None
            assert attempt.step is None and attempt.projected_gradient_max_abs is None
            assert attempt.outcome in ("initial_scored", "score_incomplete")
        else:
            assert incumbent is not None
            assert (
                attempt.from_candidate_id == incumbent.candidate_id == attempt.gradient_candidate_id
            )
            assert 1 <= attempt.iteration <= result.max_iterations
            assert 1 <= attempt.trial <= result.max_backtracking_trials
            assert_float(attempt.step)
            assert attempt.step > 0
            assert_float(attempt.projected_gradient_max_abs, nonnegative=True)
            if previous_trial is None:
                assert attempt.iteration == attempt.trial == 1
                assert attempt.step == result.seed_step
            elif previous_trial.outcome == "accepted":
                assert attempt.iteration == previous_trial.iteration + 1 and attempt.trial == 1
                assert attempt.step == previous_trial.step
            else:
                assert previous_trial.outcome in ("rejected", "unrepresentable")
                assert attempt.iteration == previous_trial.iteration
                assert attempt.trial == previous_trial.trial + 1
                assert attempt.step == previous_trial.step / 2
            previous_trial = attempt
        if attempt.outcome in ("initial_scored", "accepted", "rejected"):
            assert_score(attempt.score, module)
            assert attempt.score.candidate_id == index
            complete_scores.append(attempt.score)
            if index:
                assert incumbent is not None
                improves = attempt.score.total_objective < incumbent.total_objective
                assert (attempt.outcome == "accepted") == improves
            if attempt.outcome != "rejected":
                incumbent = attempt.score
        else:
            assert attempt.score is None
        assert attempt.gradient_state in ("complete", "incomplete", "not_needed")
        if attempt.gradient_state == "complete":
            assert isinstance(attempt.gradient, module.SpecimenGradientSummary)
            assert attempt.gradient.candidate_id == index
            assert_float(attempt.gradient.max_abs, nonnegative=True)
            complete_gradients.append(attempt.gradient)
        else:
            assert attempt.gradient is None
        if attempt.outcome not in ("initial_scored", "accepted"):
            assert attempt.gradient_state == "not_needed"
    trials = result.attempt_trace[1:]
    assert c.trials_attempted == len(trials)
    assert c.iterations_started == len({a.iteration for a in trials})
    for outcome in ("accepted", "rejected", "unrepresentable", "stagnated"):
        assert getattr(c, "trials_" + outcome) == sum(a.outcome == outcome for a in trials)
    assert c.best_updates == int(result.initial_score is not None) + c.trials_accepted
    assert c.scores_completed == len(complete_scores)
    assert c.score_attempts == sum(
        a.outcome in ("initial_scored", "accepted", "rejected", "score_incomplete")
        for a in result.attempt_trace
    )
    assert c.gradients_completed == len(complete_gradients)
    assert c.gradient_attempts == sum(
        a.gradient_state != "not_needed" for a in result.attempt_trace
    )
    assert result.last_complete_gradient == (complete_gradients[-1] if complete_gradients else None)
    assert result.best_score == incumbent
    assert c.seeds_completed == int(result.seed_step is not None)
    if result.seed_step is not None:
        assert_float(result.seed_step)
        assert result.seed_step > 0
        assert c.seed_attempts == 1
    if incumbent is None:
        assert result.source_relative is None
    else:
        assert_array(result.source_relative, result.source_shape_zyx, np.float32)
        assert np.all(result.source_relative >= 0)
        assert result.initial_score == complete_scores[0]
        with localcontext() as context:
            context.prec = 1600
            penalty = float(
                Decimal(result.regularization)
                * sum((Decimal(float(x)) ** 2 for x in result.source_relative.flat), Decimal(0))
                / (2 * result.source_relative.size)
            )
        assert math.isclose(incumbent.penalty_objective, penalty, rel_tol=128 * 2.0**-52, abs_tol=0)
    if result.status == "completed_finite_fit":
        assert incumbent is not None
        assert result.stage == "complete"
        assert result.failure_code is None and result.failure_component is None
        assert result.stop_reason in (
            "no_projected_direction",
            "float32_stagnation",
            "backtracking_limit",
            "iteration_limit",
        )
        if result.stop_reason == "iteration_limit":
            assert trials[-1].outcome == "accepted"
            assert trials[-1].iteration == result.max_iterations
            assert trials[-1].gradient_state == "not_needed"
    elif result.status == "normalization_unavailable":
        assert result.stage == "normalization"
        assert result.contrast_counts <= 0
        assert not result.attempt_trace and not result.call_trace
        assert all(getattr(c, name) == 0 for name in COUNTS)
        for name in (
            "stop_reason",
            "failure_code",
            "failure_component",
            "source_relative",
            "initial_score",
            "best_score",
            "last_complete_gradient",
            "seed_step",
            "source_spacing_um_zyx",
        ):
            assert getattr(result, name) is None
    else:
        assert result.status == "numerical_incomplete" and result.stop_reason is None
        assert result.stage in (
            "geometry",
            "kernel_cache",
            "initial_score",
            "initial_gradient",
            "curvature_seed",
            "trial_score",
            "trial_gradient",
            "backtracking_step",
        )
        assert result.failure_code in (
            "image_only_specimen_fit_range",
            "simulation_inverse_operator_range",
        )
        assert result.failure_component in (
            "source_geometry",
            "observations",
            "residual",
            "penalty_objective",
            "data_objective",
            "total_objective",
            "residual_mean",
            "residual_rms",
            "residual32",
            "gradient",
            "seed_step",
            "step",
            "dependency",
        )


class ArraySubclass(np.ndarray):
    """Represent the explicitly rejected nonplain array type."""


class IntSubclass(int):
    """Represent a rejected integer scalar subclass."""


class FloatSubclass(float):
    """Represent a rejected float scalar subclass."""


class StringSubclass(str):
    """Represent a rejected provenance string subclass."""


class TupleSubclass(tuple):
    """Represent a rejected geometry tuple subclass."""


def invalid_cases() -> list[Any]:
    """Every validation group; distinct rejection rules have explicit case IDs."""
    cases: list[Any] = []

    def add(field: str, label: str, value: Any) -> None:
        cases.append(pytest.param(field, value, id=field + "/" + label))

    raw_shape = (3, 5, 1, 1, 1)
    for label, value in (
        ("list", np.zeros(raw_shape).tolist()),
        ("subclass", np.zeros(raw_shape).view(ArraySubclass)),
        ("masked", np.ma.array(np.zeros(raw_shape))),
        ("rank", np.zeros((3, 5, 1, 1))),
        ("orientations", np.zeros((2, 5, 1, 1, 1))),
        ("phases", np.zeros((3, 4, 1, 1, 1))),
        ("empty-z", np.zeros((3, 5, 0, 1, 1))),
        ("empty-y", np.zeros((3, 5, 1, 0, 1))),
        ("empty-x", np.zeros((3, 5, 1, 1, 0))),
    ):
        add("raw_counts", label, value)
    foreign = ">f8" if np.little_endian else "<f8"
    for dtype in ("f4", "f2", "i8", "u8", "bool", "complex128", "object", foreign):
        add("raw_counts", dtype, np.zeros(raw_shape, dtype=dtype))
    for bad in (math.nan, math.inf, -math.inf):
        raw = np.zeros(raw_shape)
        raw.flat[-1] = bad
        add("raw_counts", repr(bad), raw)
    add("camera_estimate", "missing", None)
    add("camera_estimate", "duck", object())
    for field, shape in (
        ("carriers_yx_per_um", (3, 2)),
        ("phases_at_specimen_origin_rad", (3, 5)),
        ("beam_amplitudes", (3,)),
    ):
        for label, value in (
            ("list", np.ones(shape).tolist()),
            ("subclass", np.ones(shape).view(ArraySubclass)),
            ("float32", np.ones(shape, dtype=np.float32)),
            ("integer", np.ones(shape, dtype=np.int64)),
            ("non-native", np.ones(shape, dtype=foreign)),
            ("rank", np.ones((1, *shape))),
            ("shape", np.ones((*shape[:-1], shape[-1] + 1))),
            ("nan", np.full(shape, np.nan)),
            ("inf", np.full(shape, np.inf)),
        ):
            add(field, label, value)
    for label, value in (
        ("outside", np.full((3, 2), 4.0)),
        ("norm-overflow", np.full((3, 2), 1e308)),
        ("just-outside", np.array([[0, np.nextafter(1.515 / 0.488, math.inf)]] * 3)),
    ):
        add("carriers_yx_per_um", label, value)
    add("beam_amplitudes", "all-zero", np.zeros(3))
    add("beam_amplitudes", "negative", np.array([1.0, -0.1, 0.0]))
    for value in (None, "", " \t\n", StringSubclass("label"), 3):
        add("illumination_source", repr(value), value)
    scalar_bad = (
        True,
        np.float64(1),
        FloatSubclass(1),
        IntSubclass(1),
        math.inf,
        math.nan,
        10**1000,
    )
    for field in ("detector_spacing_um_zyx", "specimen_origin_um_zyx"):
        for label, value in (
            ("list", [1.0, 1.0, 1.0]),
            ("array", np.ones(3)),
            ("tuple-subclass", TupleSubclass((1.0, 1.0, 1.0))),
            ("short", (1.0, 1.0)),
            ("long", (1.0, 1.0, 1.0, 1.0)),
        ):
            add(field, label, value)
        for index, value in enumerate(scalar_bad):
            add(field, "scalar-" + str(index), (value, 1, 1))
    add("detector_spacing_um_zyx", "zero", (1, 0, 1))
    add("detector_spacing_um_zyx", "negative", (1, 1, -1))
    for field in ("pupil_order", "max_iterations", "max_backtracking_trials"):
        for label, value in enumerate((True, 1.0, np.int64(1), IntSubclass(1), 0, -1, "1")):
            add(field, str(label), value)
    for index, value in enumerate((*scalar_bad, 0, -1, "1")):
        add("regularization", str(index), value)
    return cases


@pytest.mark.parametrize(("field", "value"), invalid_cases())
def test_invalid_group_even_with_unavailable_normalization(
    fit_module: Any, field: str, value: Any
) -> None:
    """SF02/SF03: valid nonpositive contrast cannot bypass any validation group."""
    from simrecon import SimreconError

    values = (
        inputs(camera_estimate=camera(contrast=0), **{field: value})
        if field != "camera_estimate"
        else inputs(camera_estimate=value)
    )
    with pytest.raises(SimreconError) as caught:
        invoke(fit_module, values)
    assert caught.value.code == "invalid_image_only_specimen_fit"
    assert field in str(caught.value)


@pytest.mark.parametrize("consumed", ("means_counts", "contrast_counts", "source"))
@pytest.mark.parametrize("variant", range(9))
def test_camera_consumed_field_grammar(fit_module: Any, consumed: str, variant: int) -> None:
    from simrecon import SimreconError

    choices = {
        "means_counts": (
            [1.0, 2.0, 3.0],
            np.ones(3, dtype=np.float32),
            np.ones((1, 3)),
            np.ones(2),
            np.ones(3).view(ArraySubclass),
            np.ones(3, dtype=">f8" if np.little_endian else "<f8"),
            np.array([0.0, np.nan, 1.0]),
            np.array([0.0, np.inf, 1.0]),
            np.ma.array(np.ones(3)),
        ),
        "contrast_counts": (
            True,
            np.float64(1),
            FloatSubclass(1),
            IntSubclass(1),
            math.inf,
            -math.inf,
            math.nan,
            10**1000,
            "1",
        ),
        "source": (None, "", " ", "\t\n", StringSubclass("source"), 1, True, [], b"source"),
    }
    estimate = replace_camera(camera(contrast=0), **{consumed: choices[consumed][variant]})
    with pytest.raises(SimreconError) as caught:
        invoke(fit_module, inputs(camera_estimate=estimate))
    assert caught.value.code == "invalid_image_only_specimen_fit"
    assert "camera_estimate" in str(caught.value)


VALIDATION_ORDER = (
    "raw_counts",
    "camera_estimate",
    "carriers_yx_per_um",
    "phases_at_specimen_origin_rad",
    "beam_amplitudes",
    "illumination_source",
    "detector_spacing_um_zyx",
    "specimen_origin_um_zyx",
    "pupil_order",
    "regularization",
    "max_iterations",
    "max_backtracking_trials",
)


@pytest.mark.parametrize("winner", VALIDATION_ORDER)
def test_validation_group_order(fit_module: Any, winner: str) -> None:
    from simrecon import SimreconError

    # Each expected winner comes directly from the contract's fixed order.
    # inputs() supplies a valid prefix; every group in the suffix rejects None.
    suffix = VALIDATION_ORDER[VALIDATION_ORDER.index(winner) :]
    values = inputs(**dict.fromkeys(suffix))
    with pytest.raises(SimreconError) as caught:
        invoke(fit_module, values)
    assert caught.value.code == "invalid_image_only_specimen_fit"
    assert winner in str(caught.value)


@pytest.mark.parametrize("field", VALIDATION_ORDER)
def test_missing_required_argument_is_python_binding_error(fit_module: Any, field: str) -> None:
    values = inputs()
    del values[field]
    if field == "raw_counts":
        with pytest.raises(TypeError):
            fit_module.fit_specimen(**values)
    else:
        with pytest.raises(TypeError):
            invoke(fit_module, values)


@pytest.mark.parametrize(
    "extra",
    (
        "cache",
        "source_truth",
        "true_gain",
        "true_brightness",
        "noiseless_mean",
        "seed",
        "callback",
        "source_support_mask",
        "calibration_result",
        "intercept",
    ),
)
def test_extra_truth_or_configuration_channel_is_binding_error(fit_module: Any, extra: str) -> None:
    with pytest.raises(TypeError):
        invoke(fit_module, inputs(**{extra: None}))


def test_settings_are_keyword_only(fit_module: Any) -> None:
    with pytest.raises(TypeError):
        fit_module.fit_specimen(np.zeros((3, 5, 1, 1, 1)), camera())


@pytest.mark.parametrize("contrast", (0, -1.0, -0.0))
def test_nonpositive_contrast_is_metadata_only(fit_module: Any, contrast: Any) -> None:
    values = inputs(
        raw_counts=np.arange(3 * 5 * 2 * 3 * 4, dtype=np.float64).reshape(3, 5, 2, 3, 4),
        camera_estimate=camera(contrast=contrast),
        # Legal input; half-spacing would underflow, but must not be derived.
        detector_spacing_um_zyx=(1, float(np.nextafter(0.0, 1.0)), 1),
        pupil_order=10**100,
        max_iterations=10**100,
        max_backtracking_trials=10**100,
    )
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert result.status == "normalization_unavailable"
    assert result.detector_shape_zyx == (2, 3, 4) and result.source_shape_zyx == (2, 6, 8)
    for name in ("pupil_order", "max_iterations", "max_backtracking_trials"):
        assert getattr(result, name) == values[name]


@pytest.mark.parametrize(
    "layout", ("fortran", "reverse", "strided", "readonly", "broadcast", "native-equals")
)
def test_valid_raw_and_metadata_layouts_are_preserved(fit_module: Any, layout: str) -> None:
    values = inputs(camera_estimate=camera(contrast=0))
    raw = np.arange(60, dtype=np.float64).reshape(3, 5, 1, 2, 2)

    def transform(array: np.ndarray) -> np.ndarray:
        if layout == "fortran":
            return np.asfortranarray(array)
        if layout == "reverse":
            return array[..., ::-1]
        if layout == "strided":
            return np.repeat(array, 2, axis=-1)[..., ::2]
        if layout == "readonly":
            array.setflags(write=False)
        if layout == "broadcast":
            return np.broadcast_to(array.flat[0], array.shape)
        if layout == "native-equals":
            return array.astype("=f8")
        return array

    values["raw_counts"] = transform(raw)
    values["camera_estimate"] = replace_camera(
        camera(contrast=0), means_counts=transform(np.array([-2.0, 0.0, 7.0]))
    )
    values["carriers_yx_per_um"] = transform(np.zeros((3, 2)))
    values["phases_at_specimen_origin_rad"] = transform(
        np.arange(15, dtype=np.float64).reshape(3, 5)
    )
    values["beam_amplitudes"] = transform(np.ones(3))
    arrays = [values["raw_counts"], values["camera_estimate"].means_counts] + [
        values[name]
        for name in ("carriers_yx_per_um", "phases_at_specimen_origin_rad", "beam_amplitudes")
    ]
    before = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    for array, (copy, strides, writeable) in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, copy)
        assert array.strides == strides and array.flags.writeable == writeable


def test_metadata_snapshot_and_cross_call_independence(fit_module: Any) -> None:
    values = inputs(camera_estimate=camera(contrast=-1))
    result = invoke(fit_module, values)
    other = invoke(fit_module, values)
    pairs = [
        ("camera_means_counts", values["camera_estimate"].means_counts),
        ("carriers_yx_per_um", values["carriers_yx_per_um"]),
        ("phases_at_specimen_origin_rad", values["phases_at_specimen_origin_rad"]),
        ("beam_amplitudes", values["beam_amplitudes"]),
    ]
    outputs = [getattr(result, name) for name, _ in pairs]
    for name, original in pairs:
        out = getattr(result, name)
        assert_array(out, original.shape, np.float64)
        np.testing.assert_array_equal(out, original)
        assert not np.shares_memory(out, original)
        assert not np.shares_memory(out, getattr(other, name))
        original[:] = 9
        assert not np.all(out == 9)
    for i, out in enumerate(outputs):
        for other_out in outputs[i + 1 :]:
            assert not np.shares_memory(out, other_out)
    assert result.camera_source == values["camera_estimate"].source
    assert result.illumination_source == values["illumination_source"]


def test_camera_subclass_and_unconsumed_fields_are_legal(fit_module: Any) -> None:
    from simrecon import ScalarCameraEstimate

    class CameraSubclass(ScalarCameraEstimate):
        pass

    record = replace_camera(
        camera(),
        **{
            name: object()
            for name in (
                "variances_counts2",
                "frame_means_counts",
                "frame_variances_counts2",
                "empirical_mean_se_counts",
                "gain_counts_per_e",
                "information_codes",
            )
        },
    )
    subclass: Any = CameraSubclass
    fields = {
        name: getattr(record, name)
        for name in (
            "means_counts",
            "variances_counts2",
            "frame_means_counts",
            "frame_variances_counts2",
            "empirical_mean_se_counts",
            "contrast_counts",
            "gain_counts_per_e",
            "information_codes",
            "source",
        )
    }
    result = invoke(fit_module, inputs(camera_estimate=subclass(**fields)))
    assert result.status == "completed_finite_fit"
    assert result.stop_reason == "no_projected_direction"


@pytest.mark.parametrize("signal", (0.0, -2.0, float(np.nextafter(0.0, 1.0))))
def test_initial_zero_and_no_approximate_projected_direction(
    fit_module: Any, signal: float
) -> None:
    values = inputs(raw_counts=np.full((3, 5, 1, 1, 1), signal))
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert (
        result.status == "completed_finite_fit" and result.stop_reason == "no_projected_direction"
    )
    assert_initial_score(result, values)
    np.testing.assert_array_equal(result.source_relative, np.zeros((1, 2, 2), dtype=np.float32))
    c = result.counts
    assert (c.cache_attempted, c.forward_attempted, c.adjoint_attempted) == (1, 6, 3)
    assert (c.score_attempts, c.scores_completed, c.gradient_attempts, c.gradients_completed) == (
        1,
        1,
        1,
        1,
    )
    assert c.seed_attempts == c.seeds_completed == c.iterations_started == c.trials_attempted == 0
    expected: list[tuple[str, str, int | None, int | None]] = [
        ("build_kernel_cache", "cache", None, None)
    ]
    expected += [("forward", "score", 0, o) for o in range(3)]
    expected += [
        entry
        for o in range(3)
        for entry in (("forward", "gradient", 0, o), ("adjoint", "gradient", 0, o))
    ]
    assert [
        (c.operation, c.purpose, c.candidate_id, c.orientation) for c in result.call_trace
    ] == expected
    if signal in (0.0, float(np.nextafter(0.0, 1.0))):
        assert result.last_complete_gradient.max_abs == 0.0


@pytest.mark.parametrize("shape", ((1, 2, 3), (2, 1, 2)))
def test_full_signed_tail_loss_and_fixed_geometry(
    fit_module: Any, shape: tuple[int, int, int]
) -> None:
    raw = np.zeros((3, 5, *shape))
    raw.flat[-1] = -3.0
    values = inputs(raw_counts=raw, camera_estimate=camera(blank=0, contrast=2))
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert_initial_score(result, values)
    assert result.detector_shape_zyx == shape
    assert result.source_shape_zyx == (shape[0], 2 * shape[1], 2 * shape[2])
    assert result.source_spacing_um_zyx == (0.125, 0.04, 0.04)
    assert result.detector_spacing_um_zyx == (0.125, 0.08, 0.08)
    assert result.specimen_origin_um_zyx == (0.0, -1.0, 2.0)
    assert (
        result.excitation_um,
        result.emission_um,
        result.refractive_index,
        result.detection_na,
    ) == (0.488, 0.525, 1.515, 1.4)
    assert result.pixel_samples_yx == (2, 2)
    assert result.blank_counts == 0 and result.contrast_counts == 2


@pytest.mark.parametrize("sign", (-1.0, 1.0))
def test_subtraction_overflow_with_finite_normalized_observation(
    fit_module: Any, sign: float
) -> None:
    values = inputs(
        raw_counts=np.full((3, 5, 1, 1, 1), sign * 1e308),
        camera_estimate=camera(blank=-sign * 1e308, contrast=1e308),
        max_iterations=1,
    )
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert result.status == "completed_finite_fit"
    assert_initial_score(result, values)
    assert result.initial_score.data_objective == 2.0


def test_raw_square_overflow_still_has_complete_score(fit_module: Any) -> None:
    raw = np.zeros((3, 5, 1, 2, 2))
    raw.flat[-1] = 2e154
    values = inputs(raw_counts=raw)
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert_initial_score(result, values)
    assert result.status == "numerical_incomplete" and result.stage == "initial_gradient"
    assert result.failure_component == "residual32"
    assert result.best_score == result.initial_score and result.best_score.candidate_id == 0
    assert result.last_complete_gradient is None
    assert result.attempt_trace[0].outcome == "initial_scored"
    assert result.attempt_trace[0].gradient_state == "incomplete"
    assert result.counts.forward_completed == 6 and result.counts.adjoint_completed == 2
    assert result.call_trace[-1].purpose == "gradient" and result.call_trace[-1].orientation == 2


@pytest.mark.parametrize("orientation", (0, 1, 2))
def test_residual32_failure_retains_complete_initial_score(
    fit_module: Any, orientation: int
) -> None:
    raw = np.zeros((3, 5, 1, 1, 1))
    raw[orientation] = 1e40
    values = inputs(raw_counts=raw)
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert_initial_score(result, values)
    assert result.status == "numerical_incomplete"
    assert (result.stage, result.failure_code, result.failure_component) == (
        "initial_gradient",
        "image_only_specimen_fit_range",
        "residual32",
    )
    assert result.best_score == result.initial_score
    np.testing.assert_array_equal(result.source_relative, np.zeros((1, 2, 2), dtype=np.float32))
    assert result.last_complete_gradient is None and result.seed_step is None
    assert result.counts.forward_completed == 4 + orientation
    assert result.counts.adjoint_completed == orientation
    assert result.counts.gradient_attempts == 1 and result.counts.gradients_completed == 0
    assert result.attempt_trace[0].outcome == "initial_scored"
    assert result.attempt_trace[0].gradient_state == "incomplete"


@pytest.mark.parametrize("orientation", (0, 1, 2))
def test_unrepresentable_observation_fails_before_its_forward(
    fit_module: Any, orientation: int
) -> None:
    raw = np.zeros((3, 5, 1, 1, 1))
    raw[orientation] = 1.0
    values = inputs(raw_counts=raw, camera_estimate=camera(contrast=float(np.nextafter(0.0, 1.0))))
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert (result.status, result.stage, result.failure_component) == (
        "numerical_incomplete",
        "initial_score",
        "observations",
    )
    assert result.failure_code == "image_only_specimen_fit_range"
    assert result.counts.cache_completed == 1 and result.counts.forward_completed == orientation
    assert result.counts.score_attempts == 1 and result.counts.scores_completed == 0
    assert result.counts.gradient_attempts == 0
    assert (
        result.initial_score is None
        and result.best_score is None
        and result.source_relative is None
    )
    assert len(result.attempt_trace) == 1
    assert result.attempt_trace[0].outcome == "score_incomplete"


@pytest.mark.parametrize("signed", (False, True))
def test_required_data_objective_range_after_safe_means_and_rms(
    fit_module: Any, signed: bool
) -> None:
    raw = np.full((3, 5, 1, 2, 2), 1e308)
    if signed:
        raw[..., 1, :] *= -1
    result = invoke(fit_module, inputs(raw_counts=raw))
    assert_protocol(result, fit_module)
    assert (result.status, result.stage, result.failure_component) == (
        "numerical_incomplete",
        "initial_score",
        "data_objective",
    )
    assert result.counts.forward_completed == 3 and result.counts.adjoint_attempted == 0
    assert result.best_score is None and result.source_relative is None


def test_derived_half_spacing_underflow_is_geometry_failure(fit_module: Any) -> None:
    result = invoke(
        fit_module, inputs(detector_spacing_um_zyx=(1, float(np.nextafter(0.0, 1.0)), 1))
    )
    assert_protocol(result, fit_module)
    assert (result.status, result.stage, result.failure_code, result.failure_component) == (
        "numerical_incomplete",
        "geometry",
        "image_only_specimen_fit_range",
        "source_geometry",
    )
    assert result.source_shape_zyx == (1, 2, 2)
    assert result.source_spacing_um_zyx is None
    assert not result.call_trace and not result.attempt_trace
    assert all(getattr(result.counts, name) == 0 for name in COUNTS)


@pytest.mark.parametrize("regularization", (0.25, 16.0, 2.0**-400))
def test_independent_one_pixel_first_step_units_and_seed(
    fit_module: Any, regularization: float
) -> None:
    """Physical Q1 reference + explicit inherited error intervals, no recovery target.

    For four uniform columns k, g0=-k; v lies in [vmin,1]. The ratio
    ||Kv||^2/||v||^2 lies within the bounds below. Builder+application allowance
    eta=2e-4+1e-8; RN32 direction and trial rounding are budgeted separately.
    Thus this bounds the *first finite step*, not general optimizer accuracy.
    """
    values = inputs(
        raw_counts=np.ones((3, 5, 1, 1, 1)), regularization=regularization, max_iterations=1
    )
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert_initial_score(result, values)
    assert result.status == "completed_finite_fit" and result.stop_reason == "iteration_limit"
    eta = 2e-4 + 1e-8 + 1e-13  # Physical reference uncertainty, not extra inverse budget.
    eps32 = 2.0**-23
    weight = one_pixel_physical_weight()
    vmin = (1 - eta) / (1 + eta) * (1 - eps32)
    seed_lower = 1 / (4 * weight**2 * (1 + eta) ** 2 / vmin**2 + regularization / 4)
    seed_upper = 1 / (4 * weight**2 * (vmin - eta) ** 2 + regularization / 4)
    assert seed_lower <= result.seed_step <= seed_upper
    x_lower = seed_lower * weight * (1 - eta) * (1 - eps32)
    x_upper = seed_upper * weight * (1 + eta) * (1 + eps32)
    # These selected exponents keep the first coefficients in normal float32.
    assert x_lower >= np.finfo(np.float32).tiny
    assert np.all(result.source_relative >= x_lower)
    assert np.all(result.source_relative <= x_upper)
    assert result.counts.seed_attempts == result.counts.seeds_completed == 1
    assert result.counts.trials_attempted == result.counts.trials_accepted == 1
    assert result.counts.forward_completed == 12 and result.counts.adjoint_completed == 3
    assert result.counts.gradient_attempts == result.counts.gradients_completed == 1
    assert result.attempt_trace[-1].gradient_state == "not_needed"
    assert result.best_score.candidate_id == 1 and result.last_complete_gradient.candidate_id == 0


def test_large_regularization_can_round_trial_to_zero_without_convergence_claim(
    fit_module: Any,
) -> None:
    values = inputs(raw_counts=np.ones((3, 5, 1, 1, 1)), regularization=2.0**400)
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert result.status == "completed_finite_fit" and result.stop_reason == "float32_stagnation"
    assert result.best_score.candidate_id == 0
    assert result.attempt_trace[-1].outcome == "stagnated"
    assert result.attempt_trace[-1].projected_gradient_max_abs > 0
    assert result.counts.forward_completed == 9 and result.counts.adjoint_completed == 3


@pytest.mark.parametrize(
    "beam",
    (
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([1e308, 1e308, 0.0]),
        np.array([1e-300, 2e-300, 3e-300]),
    ),
)
def test_legal_beam_scales_and_repeated_signed_carriers(fit_module: Any, beam: np.ndarray) -> None:
    q = float(np.nextafter(1.515 / 0.488, 0.0))
    values = inputs(
        beam_amplitudes=beam,
        carriers_yx_per_um=np.array([[0.0, 0.0], [0.0, -q], [0.0, -q]]),
        phases_at_specimen_origin_rad=np.full((3, 5), 1e100),
    )
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert result.status == "completed_finite_fit"
    assert result.stop_reason == "no_projected_direction"
    np.testing.assert_array_equal(result.beam_amplitudes, beam)


def test_origin_is_only_a_label_and_supplied_phases_are_not_transferred(fit_module: Any) -> None:
    values = inputs(
        raw_counts=np.arange(15, dtype=np.float64).reshape(3, 5, 1, 1, 1) / 16,
        carriers_yx_per_um=np.array([[0.1, -0.3], [0.3, 0.1], [-0.2, -0.1]]),
        phases_at_specimen_origin_rad=np.arange(15, dtype=np.float64).reshape(3, 5) * 2.0,
        beam_amplitudes=np.array([0.7, 0.2, 0.5]),
        max_iterations=1,
    )
    first = invoke(fit_module, values)
    values["specimen_origin_um_zyx"] = (3.5, -200, 400)
    second = invoke(fit_module, values)
    assert_protocol(first, fit_module)
    assert_protocol(second, fit_module)
    assert first.status == second.status == "completed_finite_fit"
    assert first.best_score == second.best_score and first.attempt_trace == second.attempt_trace
    np.testing.assert_array_equal(first.source_relative, second.source_relative)
    np.testing.assert_array_equal(
        second.phases_at_specimen_origin_rad, values["phases_at_specimen_origin_rad"]
    )
    assert first.specimen_origin_um_zyx != second.specimen_origin_um_zyx
    assert not np.shares_memory(first.source_relative, second.source_relative)


@pytest.mark.parametrize("failure", (False, True))
def test_caller_arrays_and_global_policies_survive_success_or_invalid_input(
    fit_module: Any, failure: bool
) -> None:
    from simrecon import SimreconError

    values = inputs(raw_counts=np.ones((3, 5, 1, 1, 1)), max_iterations=1)
    arrays = [values["raw_counts"], values["camera_estimate"].means_counts] + [
        values[name]
        for name in ("carriers_yx_per_um", "phases_at_specimen_origin_rad", "beam_amplitudes")
    ]
    before = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    random_before = np.random.get_state()
    if failure:
        values["regularization"] = -1
    result: Any = None
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        filters_before = list(warnings.filters)
        with np.errstate(all="raise"):
            policy = np.geterr().copy()
            if failure:
                with pytest.raises(SimreconError):
                    invoke(fit_module, values)
            else:
                result = invoke(fit_module, values)
                assert result.status == "completed_finite_fit"
            assert np.geterr() == policy
        assert warnings.filters == filters_before
    random_after = np.random.get_state()
    assert random_after[0] == random_before[0] and random_after[2:] == random_before[2:]
    np.testing.assert_array_equal(random_after[1], random_before[1])
    for array, (copy, strides, writable) in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, copy)
        assert array.strides == strides and array.flags.writeable == writable
    if not failure:
        for record, field in (
            (result, "status"),
            (result.counts, "best_updates"),
            (result.initial_score, "candidate_id"),
            (result.last_complete_gradient, "max_abs"),
            (result.attempt_trace[0], "outcome"),
            (result.call_trace[0], "purpose"),
        ):
            value = getattr(record, field)
            with pytest.raises((AttributeError, TypeError)):
                setattr(record, field, value)


def assert_observed_protocol_math(result: Any, observer: Any, values: dict[str, Any]) -> None:
    """Independent arithmetic on real entered calls; cache math separately below."""
    expected: list[tuple[str, str, int | None, int | None]] = [
        ("build_kernel_cache", "cache", None, None)
    ]
    for attempt in result.attempt_trace:
        candidate = attempt.candidate_id
        if attempt.score is not None:
            expected.extend(("forward", "score", candidate, o) for o in range(3))
        if attempt.gradient_state == "complete":
            expected.extend(
                entry
                for o in range(3)
                for entry in (
                    ("forward", "gradient", candidate, o),
                    ("adjoint", "gradient", candidate, o),
                )
            )
        if candidate == 0 and result.seed_step is not None:
            expected.extend(("forward", "curvature_seed", 0, o) for o in range(3))
    assert [
        (c.operation, c.purpose, c.candidate_id, c.orientation) for c in result.call_trace
    ] == expected
    assert len(observer.events) == len(expected)
    assert all(e["outcome"] == "completed" for e in observer.events)
    assert [e["operation"] for e in observer.events] == [e[0] for e in expected]
    assert observer.events[0]["settings"] == {
        "source_shape_zyx": result.source_shape_zyx,
        "source_spacing_um_zyx": result.source_spacing_um_zyx,
        "emission_um": 0.525,
        "refractive_index": 1.515,
        "detection_na": 1.4,
        "pupil_order": values["pupil_order"],
    }
    groups: dict[tuple[str, int], list[Any]] = {}
    matrices = [cache_application_reference(observer.cache, values, o) for o in range(3)]
    from simulation_inverse_operator_fixture import apply_reference

    for event, (_, purpose, candidate, orientation) in zip(
        observer.events[1:], expected[1:], strict=True
    ):
        assert candidate is not None and orientation is not None
        settings = event["settings"]
        assert set(settings) == {
            "kernel_cache",
            "carrier_yx_per_um",
            "phases_rad",
            "beam_amplitudes",
            "excitation_um",
        }
        assert settings["kernel_cache"] is observer.cache
        assert settings["excitation_um"] == 0.488
        assert type(settings["beam_amplitudes"]) is tuple
        assert all(type(a) is float for a in settings["beam_amplitudes"])
        assert settings["beam_amplitudes"] == tuple(float(a) for a in values["beam_amplitudes"])
        np.testing.assert_array_equal(
            settings["carrier_yx_per_um"], values["carriers_yx_per_um"][orientation]
        )
        np.testing.assert_array_equal(
            settings["phases_rad"], values["phases_at_specimen_origin_rad"][orientation]
        )
        groups.setdefault((purpose, candidate), []).append(event)
        # These are independent cache-defined targets, NOT another product call.
        matrix, forward_scale, adjoint_scale = matrices[orientation]
        transpose = event["operation"] == "adjoint"
        target = apply_reference(matrix, event["array"], transpose=transpose)
        scale = (adjoint_scale if transpose else forward_scale) * float(
            np.max(np.abs(event["array"]))
        )
        allowance = (1e-4 + 256 * 2.0**-52) * scale
        np.testing.assert_allclose(event["returned"].ravel(), target, rtol=0, atol=allowance)
    sources: dict[int, np.ndarray] = {}
    gradients: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for attempt in result.attempt_trace:
        candidate = attempt.candidate_id
        if attempt.score is not None:
            events = groups[("score", candidate)]
            source = events[0]["array"]
            sources[candidate] = source
            for event in events:
                np.testing.assert_array_equal(event["array"], source)
            target = decimal_score(source, [e["returned"] for e in events], values)
            for name, wanted in zip(
                ("data_objective", "penalty_objective", "total_objective"), target[:3], strict=True
            ):
                assert math.isclose(
                    getattr(attempt.score, name), wanted, rel_tol=256 * 2.0**-52, abs_tol=0
                )
            for name, wanted in zip(("residual_mean", "residual_rms"), target[3:], strict=True):
                np.testing.assert_allclose(
                    getattr(attempt.score, name),
                    wanted,
                    rtol=256 * 2.0**-52,
                    atol=256 * 2.0**-52 * max(map(abs, np.ravel(target[4]))),
                )
        if attempt.gradient_state == "complete":
            events = groups[("gradient", candidate)]
            for o in range(3):
                forward_event, adjoint_event = events[2 * o : 2 * o + 2]
                np.testing.assert_array_equal(forward_event["array"], sources[candidate])
                with localcontext() as context:
                    context.prec = 1600
                    blank = Decimal(float(values["camera_estimate"].means_counts[1]))
                    contrast = Decimal(float(values["camera_estimate"].contrast_counts))
                    observation = np.array(
                        [
                            float((Decimal(float(c)) - blank) / contrast)
                            for c in values["raw_counts"][o].flat
                        ]
                    ).reshape(forward_event["returned"].shape)
                residual32 = (forward_event["returned"] - observation).astype(np.float32)
                np.testing.assert_array_equal(adjoint_event["array"], residual32)
            gradient, uncertainty = decimal_gradient(
                sources[candidate], [e["returned"] for e in events[1::2]], values
            )
            gradients[candidate] = gradient, uncertainty
            assert math.isclose(
                attempt.gradient.max_abs,
                float(np.max(np.abs(gradient))),
                rel_tol=256 * 2.0**-52,
                abs_tol=float(np.max(uncertainty)),
            )
    if result.seed_step is not None:
        events = groups[("curvature_seed", 0)]
        direction = events[0]["array"]
        g0, error = gradients[0]
        positive = np.maximum(0, -g0)
        target_v = (positive / np.max(positive)).astype(np.float32)
        np.testing.assert_allclose(
            direction,
            target_v,
            rtol=0,
            atol=2.0**-23 + 4 * float(np.max(error)) / float(np.max(positive)),
        )
        assert np.min(direction) >= 0 and np.max(direction) == 1
        for event in events:
            np.testing.assert_array_equal(event["array"], direction)
        wanted = decimal_seed(direction, [e["returned"] for e in events], values["regularization"])
        assert math.isclose(result.seed_step, wanted, rel_tol=256 * 2.0**-52, abs_tol=0)
    for attempt in result.attempt_trace[1:]:
        old = sources[attempt.from_candidate_id]
        gradient, error = gradients[attempt.gradient_candidate_id]
        wanted_pg = projected_gradient(old, gradient, attempt.step)
        assert math.isclose(
            attempt.projected_gradient_max_abs,
            wanted_pg,
            rel_tol=256 * 2.0**-52,
            abs_tol=float(np.max(error)),
        )
        # Ordinary RN64 projection first; uncertainty is solely the allowed
        # reduction order in assembling g. Monotonic endpoints allow a rounding
        # cell boundary without declaring an exact cross-platform trajectory.
        roundoff = 8 * 2.0**-52 * (np.abs(old) + attempt.step * np.abs(gradient))
        low = np.maximum(
            0, old.astype(np.float64) - attempt.step * (gradient + error) - roundoff
        ).astype(np.float32)
        high = np.maximum(
            0, old.astype(np.float64) - attempt.step * (gradient - error) + roundoff
        ).astype(np.float32)
        if attempt.candidate_id in sources:
            actual = sources[attempt.candidate_id]
            assert np.all(actual >= low) and np.all(actual <= high)
        elif attempt.outcome == "stagnated":
            assert np.all(old >= low) and np.all(old <= high)
    np.testing.assert_array_equal(result.source_relative, sources[result.best_score.candidate_id])
    assert observer.max_live_sources <= 2
    assert observer.max_live_predictions <= 2 and observer.max_live_adjoints <= 2
    assert all(ref() is None for ref in observer.predictions + observer.adjoints)
    for reference in observer.sources.values():
        live = reference()
        if live is not None:
            assert np.shares_memory(live, result.source_relative)


def test_observed_public_composition_and_rounded_protocol(
    fit_module: Any, monkeypatch: Any
) -> None:
    values = inputs(
        raw_counts=(np.arange(60, dtype=np.float64).reshape(3, 5, 1, 2, 2) % 11 - 2) / 8,
        camera_estimate=camera(blank=0.125, contrast=2),
        carriers_yx_per_um=np.array([[0.7, -0.3], [-0.4, 0.8], [0.2, 0.5]]),
        phases_at_specimen_origin_rad=np.arange(15, dtype=np.float64).reshape(3, 5) * 0.61 - 3,
        beam_amplitudes=np.array([0.7, 0.2, 0.5]),
        regularization=0.125,
        max_iterations=3,
        max_backtracking_trials=8,
    )
    with observe_public(fit_module, monkeypatch) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert result.status == "completed_finite_fit"
        assert result.counts.trials_accepted >= 1
        assert_observed_protocol_math(result, observer, values)


def test_reference_large_signal_margins() -> None:
    """Independent physical interval qualification; runs even while fit is absent."""
    eta = 2e-4 + 1e-8 + 1e-13
    a = one_pixel_physical_weight()
    low, high = first_step_bounds(0.001, mean_fraction=13 / 15)
    m = 3 * 2.0**126
    maximum = float(np.finfo(np.float32).max)
    g_low, g_high = a * (13 / 15 - eta) * m, a * (13 / 15 + eta) * m
    # RN64 projection and RN32 trial rounding use margins much larger than eps.
    e = 2.0**-22
    assert 1.26 < low * g_low / maximum < high * g_high / maximum < 1.28
    z_low, z_high = low * g_low / 2 * (1 - e), high * g_high / 2 * (1 + e)
    assert 0.63 < z_low / maximum < z_high / maximum < 0.64
    y_low, y_high = 4 * a * (z_low - eta * z_high) / m, 4 * a * (1 + eta) * z_high / m
    assert 0.43 < y_low < y_high < 0.44
    assert (1 + y_low) * m / maximum > 1.07
    # Sum 1 negative-observation and 14 positive-observation squared residuals.
    upper = ((1 + y_high) ** 2 + 14 * (1 - y_low) ** 2) / 30 + 0.001 * (z_high / m) ** 2 / 2
    assert upper < 0.23 < 0.5


@pytest.mark.parametrize(("iterations", "trials"), ((1, 1), (1, 2), (2, 2)))
def test_qualified_large_signal_retention(fit_module: Any, iterations: int, trials: int) -> None:
    values = large_signal_inputs(max_iterations=iterations, max_backtracking_trials=trials)
    result = invoke(fit_module, values)
    assert_protocol(result, fit_module)
    assert_initial_score(result, values)
    first = result.attempt_trace[1]
    assert first.outcome == "unrepresentable" and first.score is None
    assert first.gradient_state == "not_needed"
    low, high = first_step_bounds(0.001, mean_fraction=13 / 15)
    assert low <= result.seed_step <= high
    assert result.counts.forward_completed == (9 if trials == 1 else 12 if iterations == 1 else 13)
    assert result.counts.adjoint_completed == 3
    assert result.counts.trials_unrepresentable == 1 and result.counts.trials_rejected == 0
    if trials == 1:
        assert (result.status, result.stop_reason) == ("completed_finite_fit", "backtracking_limit")
        assert result.best_score.candidate_id == 0
        assert len(result.attempt_trace) == 2 and result.counts.score_attempts == 1
    else:
        accepted = result.attempt_trace[2]
        assert accepted.outcome == "accepted" and accepted.step == first.step / 2
        assert accepted.score == result.best_score and accepted.candidate_id == 2
        assert accepted.from_candidate_id == accepted.gradient_candidate_id == 0
        assert result.best_score.total_objective < result.initial_score.total_objective
        assert np.all(result.source_relative > 0.63 * np.finfo(np.float32).max)
        assert np.all(result.source_relative < 0.64 * np.finfo(np.float32).max)
        assert result.last_complete_gradient.candidate_id == 0
        assert result.counts.best_updates == 2 and result.counts.trials_accepted == 1
        if iterations == 1:
            assert (result.status, result.stop_reason) == (
                "completed_finite_fit",
                "iteration_limit",
            )
            assert accepted.gradient_state == "not_needed"
        else:
            assert (result.status, result.stage, result.failure_component) == (
                "numerical_incomplete",
                "trial_gradient",
                "residual32",
            )
            assert result.failure_code == "image_only_specimen_fit_range"
            assert accepted.gradient_state == "incomplete" and accepted.gradient is None
            assert result.counts.gradient_attempts == 2 and result.counts.gradients_completed == 1
            assert result.call_trace[-1].purpose == "gradient"
            assert (
                result.call_trace[-1].candidate_id == 2 and result.call_trace[-1].orientation == 0
            )


def test_rounded_subnormal_trial(fit_module: Any, monkeypatch: Any) -> None:
    values = inputs(
        raw_counts=np.full((3, 5, 1, 1, 1), 2.0**-140), regularization=16.0, max_iterations=1
    )
    with observe_public(fit_module, monkeypatch) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert result.status == "completed_finite_fit" and result.stop_reason == "iteration_limit"
        assert np.all(result.source_relative > 0)
        assert np.all(result.source_relative < np.finfo(np.float32).tiny)
        assert_observed_protocol_math(result, observer, values)


def assert_tiny_curvature_calls(result: Any, observer: Any, values: dict[str, Any]) -> None:
    """Public entry, exact subnormal application and trial-formation checks."""
    layout: list[tuple[str, str, int | None, int | None]] = [
        ("build_kernel_cache", "cache", None, None)
    ]
    layout += [("forward", "score", 0, o) for o in range(3)]
    layout += [
        entry
        for o in range(3)
        for entry in (("forward", "gradient", 0, o), ("adjoint", "gradient", 0, o))
    ]
    layout += [("forward", "curvature_seed", 0, o) for o in range(3)]
    for attempt in result.attempt_trace[1:]:
        assert attempt.outcome in ("accepted", "rejected", "score_incomplete")
        layout += [("forward", "score", attempt.candidate_id, o) for o in range(3)]
    assert len(result.call_trace) == len(observer.events)
    if result.status == "numerical_incomplete" and result.stage == "trial_score":
        assert observer.events[-1]["outcome"] == "raised"
        assert observer.events[-1]["failure_code"] == "simulation_inverse_operator_range"
        assert result.failure_code == "simulation_inverse_operator_range"
        assert result.failure_component == "dependency"
        layout = layout[: len(observer.events)]
        assert result.attempt_trace[-1].outcome == "score_incomplete"
        assert result.attempt_trace[-1].score is None
        assert result.attempt_trace[-1].gradient_state == "not_needed"
    else:
        assert all(e["outcome"] == "completed" for e in observer.events)
    assert [
        (c.operation, c.purpose, c.candidate_id, c.orientation) for c in result.call_trace
    ] == layout
    assert [c.operation for c in result.call_trace] == [e["operation"] for e in observer.events]
    assert [c.outcome for c in result.call_trace] == [
        "completed" if e["outcome"] == "completed" else "range_failure" for e in observer.events
    ]
    quantum = Fraction(1, 2**1074)
    groups: dict[int, list[Any]] = {}
    for event, call in zip(observer.events[1:], result.call_trace[1:], strict=True):
        settings = event["settings"]
        assert settings["kernel_cache"] is observer.cache
        np.testing.assert_array_equal(settings["carrier_yx_per_um"], np.zeros(2))
        np.testing.assert_array_equal(settings["phases_rad"], np.zeros(5))
        assert settings["beam_amplitudes"] == (1.0, 0.0, 0.0)
        assert settings["excitation_um"] == 0.488
        targets, allowance = tiny_cache_exact_reference(
            observer.cache, event["array"], transpose=event["operation"] == "adjoint"
        )
        if event["outcome"] == "completed":
            assert all(
                abs(Fraction(float(actual)) - target) <= allowance
                for actual, target in zip(event["returned"].flat, targets, strict=True)
            )
        else:
            assert call.purpose == "score" and call.candidate_id > 0
        if call.purpose == "score" and call.candidate_id > 0:
            groups.setdefault(call.candidate_id, []).append(event)
            # Independent output-grid qualification, with unchanged 1e-4 budget.
            closest_error = abs(Fraction(float(targets[0])) - targets[0])
            if values["regularization"] == 2.0**-1000:
                assert closest_error > allowance
                assert event["outcome"] == "raised"
            else:
                assert closest_error <= allowance
                assert allowance > quantum / 2
    adjoints = [observer.events[5 + 2 * o]["returned"] for o in range(3)]
    gradient = [
        sum((Fraction(float(a.flat[j])) for a in adjoints), Fraction()) / 15 for j in range(4)
    ]
    # The fixed three-term assembly is subnormal. A conservative 64-quantum
    # observer enclosure covers ordinary binary64 reduction/division rounding;
    # it does not relax the independent inverse application inequality above.
    error = 64 * quantum
    assert abs(Fraction(result.last_complete_gradient.max_abs) - max(map(abs, gradient))) <= error
    if result.seed_step is not None:
        seed_events = observer.events[10:13]
        direction = seed_events[0]["array"]
        assert direction.max() == 1 and direction.min() > 0.99
        for event in seed_events:
            np.testing.assert_array_equal(event["array"], direction)
        wanted_seed = decimal_seed(
            direction, [e["returned"] for e in seed_events], values["regularization"]
        )
        assert math.isclose(result.seed_step, wanted_seed, rel_tol=256 * 2.0**-52)
        for attempt in result.attempt_trace[1:]:
            events = groups[attempt.candidate_id]
            # Every entered trial here starts from initial zero: a last-iteration
            # acceptance returns immediately, while rejections keep candidate0.
            assert attempt.from_candidate_id == attempt.gradient_candidate_id == 0
            step = Fraction(attempt.step)
            lower = [
                float(np.float32(float(max(Fraction(), -step * (g + error))))) for g in gradient
            ]
            upper = [
                float(np.float32(float(max(Fraction(), -step * (g - error))))) for g in gradient
            ]
            for event in events:
                assert all(
                    lo <= float(x) <= hi
                    for lo, x, hi in zip(lower, event["array"].flat, upper, strict=True)
                )
            if attempt.score is not None:
                expected = decimal_score(
                    events[0]["array"], [e["returned"] for e in events], values
                )
                for field, target in zip(
                    ("data_objective", "penalty_objective", "total_objective"),
                    expected[:3],
                    strict=True,
                ):
                    assert abs(Fraction(getattr(attempt.score, field)) - Fraction(target)) <= (
                        abs(Fraction(target)) * Fraction(256, 2**52) + 8 * quantum
                    )


@pytest.mark.parametrize("regularization", (2.0**-1000, 2.0**-1010, float(np.nextafter(0.0, 1.0))))
def test_tiny_curvature_seed_range_and_finite_ratio(
    fit_module: Any, monkeypatch: Any, regularization: float
) -> None:
    # With dy=dx=2**-521, Q1 kernel is pi*(NA/lambda_em)^2 to
    # relative error <1e-300 (the J0 alternating-series argument is <1e-153).
    # The physical pixel coefficient is ~1.896e-312, strictly positive even
    # after the inherited bounds. Curvature O(1e-623) is negligible beside
    # lambda/4. Thus t is RN64(4/lambda) within ordinary reduction error:
    # finite near 2**1002 / 2**1012, genuinely above DBL_MAX for the
    # smallest-positive lambda. A finite seed does NOT promise later inverse
    # output precision. The -1010 example is supplemental post-C evidence.
    values = inputs(
        raw_counts=np.ones((3, 5, 1, 1, 1)),
        detector_spacing_um_zyx=(0.125, 2.0**-520, 2.0**-520),
        regularization=regularization,
        max_iterations=1,
        max_backtracking_trials=2,
    )
    with observe_public(fit_module, monkeypatch) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert_initial_score(result, values)
        assert result.last_complete_gradient.candidate_id == 0
        assert 1.8e-312 < result.last_complete_gradient.max_abs < 2.0e-312
        assert_tiny_curvature_calls(result, observer, values)
        if regularization in (2.0**-1000, 2.0**-1010):
            wanted = 2.0 ** (1002 if regularization == 2.0**-1000 else 1012)
            assert math.isclose(result.seed_step, wanted, rel_tol=256 * 2.0**-52)
            assert result.counts.seed_attempts == result.counts.seeds_completed == 1
            assert result.counts.trials_attempted >= 1
            if result.status == "numerical_incomplete":
                assert result.stage == "trial_score"
                assert result.failure_code == "simulation_inverse_operator_range"
                assert result.failure_component == "dependency"
                assert result.best_score.candidate_id == 0 and not result.source_relative.any()
            else:
                assert result.status == "completed_finite_fit"
            if regularization == 2.0**-1000:
                assert (result.status, result.stage) == ("numerical_incomplete", "trial_score")
                assert len(result.attempt_trace) == 2
                expected_counts = dict.fromkeys(COUNTS, 0)
                expected_counts.update(
                    cache_attempted=1,
                    cache_completed=1,
                    forward_attempted=10,
                    forward_completed=9,
                    forward_failed=1,
                    adjoint_attempted=3,
                    adjoint_completed=3,
                    score_attempts=2,
                    scores_completed=1,
                    gradient_attempts=1,
                    gradients_completed=1,
                    seed_attempts=1,
                    seeds_completed=1,
                    iterations_started=1,
                    trials_attempted=1,
                    best_updates=1,
                )
                assert {name: getattr(result.counts, name) for name in COUNTS} == expected_counts
        else:
            assert (result.status, result.stage, result.failure_component) == (
                "numerical_incomplete",
                "curvature_seed",
                "seed_step",
            )
            assert result.failure_code == "image_only_specimen_fit_range"
            assert result.seed_step is None and result.last_complete_gradient is not None
            assert result.best_score.candidate_id == 0 and not result.source_relative.any()
            assert len(result.attempt_trace) == 1
            assert result.counts.forward_completed == 9 and result.counts.adjoint_completed == 3
            assert result.counts.seed_attempts == 1 and result.counts.seeds_completed == 0
            assert result.counts.trials_attempted == result.counts.iterations_started == 0


def test_rounded_cancellation_path_obeys_measured_selection(
    fit_module: Any, monkeypatch: Any
) -> None:
    # A natural cancellation stressor, NOT a promised tie across legal inverse
    # errors/reduction trees. Every actually reached decision gets checked.
    raw = np.array([2.0**30, -(2.0**30), 2.0**30, -(2.0**30), 1.0])
    values = inputs(
        raw_counts=np.broadcast_to(raw[None, :, None, None, None], (3, 5, 1, 1, 1)),
        max_iterations=3,
        max_backtracking_trials=4,
    )
    with observe_public(fit_module, monkeypatch) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert result.status == "completed_finite_fit"
        assert_initial_score(result, values)
        assert_observed_protocol_math(result, observer, values)


def test_reference_nonuniform_decision_margins() -> None:
    """Qualify the fixed physical witness without any specimen/runtime output."""
    from simulation_inverse_operator_fixture import physical_kernel, pixel_matrix

    enclosure = nonuniform_enclosure()
    # Separate accepted finite-pupil helper has an independently computed pi,
    # canonical Q1 node and Bessel-tail arithmetic. Domain: Q=1, d=0, |arg|<6.
    kernel = physical_kernel((1, 2, 2), (0.125, 0.5, 0.04), 0.525, 1.515, 1.4, 1)
    matrix = pixel_matrix(kernel, (1, 2, 2), (0.125, 0.5, 0.04))
    np.testing.assert_allclose(matrix, enclosure["coefficient"], rtol=64 * 2.0**-52, atol=0)
    with localcontext() as context:
        context.prec = 160
        tail = Decimal(9) ** 120 / Decimal(math.factorial(120)) ** 2
        assert tail < Decimal("1e-270")
        pi = Decimal(
            "3.141592653589793238462643383279502884197169399375105820974944592307816406286"
        )
        phase_error = abs(Decimal(math.pi / 2) - pi / 2)
        assert phase_error < Decimal("1e-15")
        assert phase_error**2 / 2 < Decimal("1e-29")
    scores = enclosure["scores"]
    assert scores[1].high < scores[0].low
    assert scores[2].high < scores[1].low
    assert all(score.low > scores[2].high for score in scores[3:])
    # Distinct numerical risks: active projection and PG unlike gradient norm.
    assert all(v.low == v.high == 0 for v in enclosure["sources"][2][2:])
    assert enclosure["projected_gradient"][1].high < Decimal("0.015")
    assert enclosure["gradients"][1][2].low > Decimal("0.12")
    assert all(v.max_abs() < Decimal(1) for row in enclosure["gradients"] for v in row)
    # Examples of the proved quarter-quantum sufficient condition, NOT a claim
    # of general required-halving-underflow unreachability.
    q64 = float(np.nextafter(0.0, 1.0))
    assert q64 / 2 == 0
    source = np.array([0, 2.0**-149, 1, float(np.finfo(np.float32).max)], dtype=np.float32)
    for sign in (-1, 1):
        projected = np.maximum(0, source.astype(np.float64) - q64 * (sign * 2.0**923))
        np.testing.assert_array_equal(projected.astype(np.float32), source)


@pytest.mark.parametrize("iterations", (2, 3))
def test_nonuniform_projection_and_scored_backtracking(
    fit_module: Any, monkeypatch: Any, iterations: int
) -> None:
    values = nonuniform_inputs(max_iterations=iterations)
    enclosure = nonuniform_enclosure()
    with observe_public(fit_module, monkeypatch) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert_initial_score(result, values)
        assert_observed_protocol_math(result, observer, values)
        assert (result.status, result.stop_reason) == (
            "completed_finite_fit",
            "iteration_limit" if iterations == 2 else "backtracking_limit",
        )
        assert result.best_score.candidate_id == 2
        outcomes = [a.outcome for a in result.attempt_trace]
        assert outcomes == ["initial_scored", "accepted", "accepted"] + (
            ["rejected"] * 3 if iterations == 3 else []
        )
        for attempt in result.attempt_trace:
            assert enclosure["scores"][attempt.candidate_id].contains(attempt.score.total_objective)
        assert enclosure["seed"].contains(result.seed_step)
        steps = [a.step for a in result.attempt_trace[1:]]
        assert steps == [result.seed_step] * 2 + (
            [result.seed_step, result.seed_step / 2, result.seed_step / 4]
            if iterations == 3
            else []
        )
        for attempt, interval in zip(
            result.attempt_trace[1:], enclosure["projected_gradient"], strict=False
        ):
            assert interval.contains(attempt.projected_gradient_max_abs)
        # The physical oracle bounds every actually entered source, including
        # rejected candidates, independently of fit-reported scores/gradients.
        for event, call in zip(observer.events, result.call_trace, strict=True):
            if call.operation == "forward":
                intervals = (
                    enclosure["direction"]
                    if call.purpose == "curvature_seed"
                    else enclosure["sources"][call.candidate_id]
                )
                for actual, interval in zip(event["array"].flat, intervals, strict=True):
                    assert interval.contains(float(actual))
        for actual, interval in zip(
            result.source_relative.flat, enclosure["sources"][2], strict=True
        ):
            assert interval.contains(float(actual))
        np.testing.assert_array_equal(
            result.source_relative[:, 1, :], np.zeros((1, 2), dtype=np.float32)
        )
        assert result.attempt_trace[2].projected_gradient_max_abs < 0.015
        assert result.attempt_trace[1].gradient.max_abs > 0.12
        count = result.counts
        expected_counts = {
            "cache_attempted": 1,
            "cache_completed": 1,
            "cache_failed": 0,
            "forward_attempted": 18 if iterations == 2 else 30,
            "forward_completed": 18 if iterations == 2 else 30,
            "forward_failed": 0,
            "adjoint_attempted": 6 if iterations == 2 else 9,
            "adjoint_completed": 6 if iterations == 2 else 9,
            "adjoint_failed": 0,
            "score_attempts": 3 if iterations == 2 else 6,
            "scores_completed": 3 if iterations == 2 else 6,
            "gradient_attempts": 2 if iterations == 2 else 3,
            "gradients_completed": 2 if iterations == 2 else 3,
            "seed_attempts": 1,
            "seeds_completed": 1,
            "iterations_started": iterations,
            "trials_attempted": 2 if iterations == 2 else 5,
            "trials_accepted": 2,
            "trials_rejected": 0 if iterations == 2 else 3,
            "trials_unrepresentable": 0,
            "trials_stagnated": 0,
            "best_updates": 3,
        }
        assert set(expected_counts) == set(COUNTS)
        assert {name: getattr(count, name) for name in COUNTS} == expected_counts
        assert result.last_complete_gradient.candidate_id == (1 if iterations == 2 else 2)
        assert result.attempt_trace[2].gradient_state == (
            "not_needed" if iterations == 2 else "complete"
        )
        for rejected in result.attempt_trace[3:]:
            assert rejected.gradient_state == "not_needed" and rejected.gradient is None
            assert rejected.score.total_objective > result.best_score.total_objective


@pytest.mark.parametrize(
    ("operation", "ordinal", "stage"),
    (
        ("build_kernel_cache", 1, "kernel_cache"),
        ("forward", 1, "initial_score"),
        ("forward", 2, "initial_score"),
        ("forward", 3, "initial_score"),
        ("forward", 4, "initial_gradient"),
        ("forward", 5, "initial_gradient"),
        ("forward", 6, "initial_gradient"),
        ("adjoint", 1, "initial_gradient"),
        ("adjoint", 2, "initial_gradient"),
        ("adjoint", 3, "initial_gradient"),
        ("forward", 7, "curvature_seed"),
        ("forward", 8, "curvature_seed"),
        ("forward", 9, "curvature_seed"),
        ("forward", 10, "trial_score"),
        ("forward", 11, "trial_score"),
        ("forward", 12, "trial_score"),
        ("forward", 13, "trial_gradient"),
        ("forward", 14, "trial_gradient"),
        ("forward", 15, "trial_gradient"),
        ("adjoint", 4, "trial_gradient"),
        ("adjoint", 5, "trial_gradient"),
        ("adjoint", 6, "trial_gradient"),
    ),
)
def test_dependency_range_partial_trace(
    fit_module: Any, monkeypatch: Any, operation: str, ordinal: int, stage: str
) -> None:
    from simrecon import SimreconError

    error = SimreconError(
        code="simulation_inverse_operator_range", message="public inverse range sentinel"
    )
    values = inputs(raw_counts=np.ones((3, 5, 1, 1, 1)), max_iterations=2)
    with observe_public(fit_module, monkeypatch, fault=(operation, ordinal, error)) as observer:
        result = invoke(fit_module, values)
        assert_protocol(result, fit_module)
        assert (result.status, result.stage, result.failure_code, result.failure_component) == (
            "numerical_incomplete",
            stage,
            error.code,
            "dependency",
        )
        assert len(result.call_trace) == len(observer.events)
        layout: list[tuple[str, str, int | None, int | None]] = [
            ("build_kernel_cache", "cache", None, None)
        ]
        layout += [("forward", "score", 0, o) for o in range(3)]
        layout += [
            entry
            for o in range(3)
            for entry in (("forward", "gradient", 0, o), ("adjoint", "gradient", 0, o))
        ]
        layout += [("forward", "curvature_seed", 0, o) for o in range(3)]
        layout += [("forward", "score", 1, o) for o in range(3)]
        layout += [
            entry
            for o in range(3)
            for entry in (("forward", "gradient", 1, o), ("adjoint", "gradient", 1, o))
        ]
        failures = [i for i, entry in enumerate(layout) if entry[0] == operation]
        prefix = layout[: failures[ordinal - 1] + 1]
        assert [
            (c.operation, c.purpose, c.candidate_id, c.orientation) for c in result.call_trace
        ] == prefix
        assert [c.operation for c in result.call_trace] == [e["operation"] for e in observer.events]
        assert all(c.outcome == "completed" for c in result.call_trace[:-1])
        assert result.call_trace[-1].outcome == "range_failure"
        assert observer.events[-1]["outcome"] == "raised"
        assert result.call_trace[-1].operation == operation
        assert result.call_trace[-1].failure_code == error.code
        assert sum(e["operation"] == operation for e in observer.events) == ordinal
        assert (
            result.counts.cache_failed + result.counts.forward_failed + result.counts.adjoint_failed
            == 1
        )
        if stage in ("kernel_cache", "initial_score"):
            assert result.best_score is None and result.source_relative is None
            assert result.last_complete_gradient is None
        else:
            assert_initial_score(result, values)
            assert result.best_score is not None
            if stage == "trial_gradient":
                assert result.best_score.candidate_id == 1 and result.source_relative.max() > 0
                assert result.attempt_trace[-1].outcome == "accepted"
                assert result.attempt_trace[-1].gradient_state == "incomplete"
            else:
                assert result.best_score.candidate_id == 0 and not result.source_relative.any()
            if stage == "initial_gradient":
                assert result.last_complete_gradient is None
            else:
                assert result.last_complete_gradient.candidate_id == 0


@pytest.mark.parametrize(
    "kind",
    ("invalid_inverse", "other_range", "runtime", "value", "type", "allocation", "interrupt"),
)
@pytest.mark.parametrize(
    ("operation", "ordinal"), (("build_kernel_cache", 1), ("forward", 10), ("adjoint", 4))
)
def test_unrelated_dependency_failures_preserve_identity(
    fit_module: Any, monkeypatch: Any, kind: str, operation: str, ordinal: int
) -> None:
    from simrecon import SimreconError

    errors: dict[str, BaseException] = {
        "invalid_inverse": SimreconError(
            code="invalid_simulation_inverse_operator", message="public invalid sentinel"
        ),
        "other_range": SimreconError(
            code="image_only_calibration_pilot_range", message="public unrelated range sentinel"
        ),
        "runtime": RuntimeError("public runtime sentinel"),
        "value": ValueError("public value sentinel"),
        "type": TypeError("public type sentinel"),
        "allocation": MemoryError("public allocation sentinel"),
        "interrupt": KeyboardInterrupt("public interruption sentinel"),
    }
    error = errors[kind]
    values = inputs(raw_counts=np.ones((3, 5, 1, 1, 1)), max_iterations=2)
    arrays = [
        values["raw_counts"],
        values["camera_estimate"].means_counts,
        values["carriers_yx_per_um"],
        values["phases_at_specimen_origin_rad"],
        values["beam_amplitudes"],
    ]
    before = [(a.copy(), a.strides, a.flags.writeable) for a in arrays]
    with (
        observe_public(fit_module, monkeypatch, fault=(operation, ordinal, error)) as observer,
        warnings.catch_warnings(),
    ):
        warnings.simplefilter("error")
        filters = list(warnings.filters)
        with np.errstate(all="raise"):
            policy = np.geterr().copy()
            with pytest.raises(type(error)) as caught:
                invoke(fit_module, values)
            assert caught.value is error
            assert np.geterr() == policy and warnings.filters == filters
        assert observer.events[-1]["operation"] == operation
        assert observer.events[-1]["outcome"] == "raised"
        assert sum(e["operation"] == operation for e in observer.events) == ordinal
    for array, (original, strides, writable) in zip(arrays, before, strict=True):
        np.testing.assert_array_equal(array, original)
        assert array.strides == strides and array.flags.writeable == writable


@pytest.mark.parametrize("policy", ("always", "error"))
def test_backend_warning_policy_is_preserved(
    fit_module: Any, monkeypatch: Any, policy: Any
) -> None:
    values = inputs(raw_counts=np.ones((3, 5, 1, 1, 1)), max_iterations=1)
    with (
        observe_public(fit_module, monkeypatch, warning_at=("forward", 4)),
        warnings.catch_warnings(record=True) as caught,
    ):
        warnings.simplefilter(policy, UserWarning)
        filters = list(warnings.filters)
        if policy == "error":
            with pytest.raises(UserWarning, match="public inverse warning sentinel"):
                invoke(fit_module, values)
        else:
            assert invoke(fit_module, values).status == "completed_finite_fit"
            assert len(caught) == 1 and caught[0].category is UserWarning
            assert str(caught[0].message) == "public inverse warning sentinel"
        assert warnings.filters == filters


def test_mapped_subclass_rejected_but_plain_view_valid(fit_module: Any, tmp_path: Any) -> None:
    from simrecon import SimreconError

    # The same mapped payload tests a strict type boundary, not provenance.
    mapped = np.memmap(tmp_path / "raw.bin", mode="w+", dtype=np.float64, shape=(3, 5, 1, 1, 1))
    mapped[:] = -1
    with pytest.raises(SimreconError) as caught:
        invoke(fit_module, inputs(raw_counts=mapped))
    assert caught.value.code == "invalid_image_only_specimen_fit"
    view = np.asarray(mapped)
    assert type(view) is np.ndarray and np.shares_memory(view, mapped)
    result = invoke(fit_module, inputs(raw_counts=view))
    assert_protocol(result, fit_module)
    assert (
        result.status == "completed_finite_fit" and result.stop_reason == "no_projected_direction"
    )
    np.testing.assert_array_equal(view, -np.ones(view.shape))
