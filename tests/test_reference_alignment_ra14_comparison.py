"""Blind public-contract tests for RA14 comparison composition, not recovery."""

from __future__ import annotations

import inspect
import math
import random
import subprocess
import sys
import textwrap
import warnings
from dataclasses import replace
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
import pytest
from scripts import simulation_inverse_operator as inverse
from scripts import simulation_optics as optics

from reference_alignment_ra14_fixture import (
    SPACING,
    direct_matrices,
    direct_prediction,
    j0_series,
    pupil,
    scales,
    tiny_case,
)

FIELDS = (
    "count",
    "reference_l2",
    "error_l2",
    "relative_l2",
    "error_rms",
    "error_max_abs",
    "error_mean",
    "unavailable_fields",
)


def product() -> Any:
    # Delayed import lets the independent existing-component controls execute
    # even at the declared missing-module baseline. Never skip or stub absence.
    import scripts.reference_alignment_ra14_comparison as comparison

    return comparison


@pytest.fixture(params=[1, 3], ids=["Q1", "Q3"], scope="module")
def optical(request: pytest.FixtureRequest) -> tuple[Any, Any, Any]:
    case = tiny_case(request.param)
    a, b = direct_matrices(case)
    return case, a, b


def snapshot(arrays: list[Any]) -> list[Any]:
    return [(a.shape, a.strides, a.dtype.str, a.flags.writeable, a.tobytes()) for a in arrays]


@pytest.fixture
def strict_policies() -> Any:
    """Catch silent global-policy mutation and unexpected arithmetic warnings."""
    python_random = random.getstate()
    numpy_random = np.random.get_state()
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        filters = warnings.filters[:]
        settings = np.geterr().copy()
        yield
        assert np.geterr() == settings
        assert warnings.filters == filters
        assert not caught
    assert random.getstate() == python_random
    after = np.random.get_state()
    assert after[0] == numpy_random[0]
    np.testing.assert_array_equal(after[1], numpy_random[1])
    assert after[2:] == numpy_random[2:]


def assert_invalid(call: Any, field: str) -> None:
    # Keep feature absence distinct from a malformed-input rejection defect.
    product()
    with pytest.raises(Exception) as caught:
        call()
    assert getattr(caught.value, "code", None) == "invalid_reference_alignment_ra14"
    assert field in str(caught.value)


def decimal_metrics(estimated: Any, reference: Any) -> dict[str, float | None]:
    """Exact represented-input differences and high precision scalar reductions.

    1000 decimal digits resolve binary64 extremes, cancellation and subnormals.
    Only final conversion to float is allowed to lose range.
    """
    with localcontext() as context:
        context.prec = 1000
        r = [Decimal.from_float(float(x)) for x in reference.flat]
        e = [Decimal.from_float(float(x)) - y for x, y in zip(estimated.flat, r, strict=True)]
        count = Decimal(len(r))
        r2 = sum((x * x for x in r), Decimal(0))
        e2 = sum((x * x for x in e), Decimal(0))
        exact = {
            "reference_l2": r2.sqrt(),
            "error_l2": e2.sqrt(),
            "relative_l2": (e2 / r2).sqrt() if r2 else None,
            "error_rms": (e2 / count).sqrt(),
            "error_max_abs": max(abs(x) for x in e),
            "error_mean": sum(e, Decimal(0)) / count,
        }
        result: dict[str, float | None] = {}
        for field, value in exact.items():
            number = float(value) if value is not None else None
            result[field] = number if number is None or math.isfinite(number) else None
        return result


def assert_metrics(summary: Any, estimated: Any, reference: Any) -> None:
    expected = decimal_metrics(estimated, reference)
    assert type(summary.count) is int
    assert summary.count == reference.size
    assert type(summary.unavailable_fields) is tuple
    reasons = {entry.field: entry.reason for entry in summary.unavailable_fields}
    assert len(reasons) == len(summary.unavailable_fields)
    assert set(reasons) == {field for field, value in expected.items() if value is None}
    for field, value in expected.items():
        actual = getattr(summary, field)
        if value is None:
            assert actual is None
            reason = (
                "zero_reference"
                if field == "relative_l2" and not np.any(reference)
                else "unrepresentable"
            )
            assert reasons[field] == reason
        else:
            assert type(actual) is float
            assert math.isfinite(actual)
            # Scalar reduction allowance, no floor that would hide subnormals.
            assert actual == pytest.approx(value, rel=4e-15, abs=0.0)


def test_observer_analytic_peak_and_side_signs() -> None:
    assert j0_series(0.0) == 1.0
    assert pupil(0.0, 0.0, 1) == pytest.approx(math.pi * (1.4 / 0.525) ** 2, rel=2e-15)
    assert pupil(0.0, 0.0, 3) == pytest.approx(math.pi * (1.4 / 0.525) ** 2, rel=2e-15)
    case = tiny_case()
    k0 = 1.515 / 0.488
    kappa = 1 / (4 * SPACING[0])
    q = math.sqrt(2 * k0 * kappa - kappa * kappa)
    carriers = np.tile([0.0, q], (3, 1))
    phases = np.full((3, 5), math.pi / 2 - 2 * math.pi * q * 0.5 * SPACING[2])
    a, b = direct_matrices(replace(case, carriers=carriers, phases=phases))
    # At theta=pi/2, axial +/-pi/2: |+/-4i+2i-i|^2/21.
    assert a[0, 0, 0, 24] / b[0, 24] == pytest.approx(25 / 21, rel=3e-15)
    assert a[0, 0, 6, 0] / b[6, 0] == pytest.approx(9 / 21, rel=3e-15)


def test_existing_inverse_direct_finite_control(optical: Any, strict_policies: Any) -> None:
    case, a, b = optical
    expected = direct_prediction(case, a)
    budget = scales(case, b)
    cache = inverse.build_kernel_cache(
        source_shape_zyx=case.source.shape,
        source_spacing_um_zyx=SPACING,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=case.order,
    )
    actual = np.stack(
        [
            inverse.forward(
                case.source,
                kernel_cache=cache,
                carrier_yx_per_um=case.carriers[o],
                phases_rad=case.phases[o],
                beam_amplitudes=tuple(float(v) for v in case.beams),
                excitation_um=0.488,
            )
            for o in range(3)
        ]
    )
    assert np.max(np.abs(actual - expected)) <= budget["inverse_bound"] + budget["observer"]
    assert budget["inverse_bound"] < 0.01 * float(np.max(np.abs(expected)))


def test_existing_generator_matched_positive_control(optical: Any, strict_policies: Any) -> None:
    case, a, b = optical
    positive = replace(case, source=np.abs(case.source))
    expected = direct_prediction(positive, a)
    unilluminated = b @ positive.source.ravel().astype(np.float64)
    t = float(np.max(unilluminated))
    actual = optics.expected_images(
        positive.source,
        detector_spacing_um_zyx=(SPACING[0], 2 * SPACING[1], 2 * SPACING[2]),
        source_refinement_zyx=(1, 2, 2),
        carriers_yx_per_um=case.carriers,
        phases_rad=case.phases,
        beam_amplitudes=tuple(float(v) for v in case.beams),
        excitation_um=0.488,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=case.order,
        pixel_subsamples_yx=(2, 2),
    )
    assert np.max(np.abs(actual - expected)) <= 1e-5 * t + scales(positive, b)["observer"]


def test_replay_all15_independent_physical_matrix(optical: Any, strict_policies: Any) -> None:
    case, a, b = optical
    arrays = [case.source, case.carriers, case.phases, case.beams]
    before = snapshot(arrays)
    actual = product().replay_source(case.source, **case.kwargs())
    expected = direct_prediction(case, a)
    budget = scales(case, b)
    assert type(actual) is np.ndarray
    assert actual.shape == (3, 5, 2, 2, 3)
    assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
    assert actual.flags.owndata and actual.flags.c_contiguous and actual.flags.writeable
    assert np.all(np.isfinite(actual))
    assert not any(np.shares_memory(actual, value) for value in arrays)
    for o in range(3):
        for p in range(5):
            assert (
                np.max(np.abs(actual[o, p] - expected[o, p]))
                <= budget["inverse_bound"] + budget["observer"]
            )
    assert snapshot(arrays) == before
    # Repeated calls cannot alias retained predictions.
    again = product().replay_source(case.source, **case.kwargs())
    actual.fill(123)
    assert not np.shares_memory(actual, again)
    assert np.max(np.abs(again - expected)) <= budget["inverse_bound"] + budget["observer"]


def test_tiny_control_distinguishes_wrong_physics(optical: Any) -> None:
    case, a, b = optical
    expected = direct_prediction(case, a)
    limit = scales(case, b)["inverse_bound"] + scales(case, b)["observer"]
    alternatives = [
        replace(case, beams=case.beams[[0, 2, 1]]),
        replace(case, phases=case.local_phases),
        replace(case, carriers=np.zeros_like(case.carriers)),
        replace(case, phases=case.phases[:, :1].repeat(5, axis=1)),
    ]
    for wrong in alternatives:
        wrong_a, _ = direct_matrices(wrong)
        assert np.max(np.abs(direct_prediction(wrong, wrong_a) - expected)) > 10 * limit
    assert np.max(np.abs(expected * math.prod(SPACING) - expected)) > 10 * limit
    assert np.max(np.abs(expected / 4 - expected)) > 10 * limit


@pytest.mark.parametrize("layout", ["strided", "fortran", "readonly", "endian", "zero_stride"])
def test_replay_legal_representations(layout: str, strict_policies: Any) -> None:
    case = tiny_case()
    if layout == "strided":
        source = case.source[:, :, ::-1].copy()[:, :, ::-1]
    elif layout == "fortran":
        source = np.asfortranarray(case.source)
    elif layout == "readonly":
        source = case.source.copy()
        source.flags.writeable = False
    elif layout == "endian":
        source = case.source.astype(np.dtype("float32").newbyteorder("S"))
    else:
        source = np.broadcast_to(np.array(-0.25, dtype=np.float32), case.source.shape)
    phases = np.asfortranarray(case.phases)
    phases.flags.writeable = False
    carriers = case.carriers[::-1].copy()[::-1]
    case = replace(case, source=source, phases=phases, carriers=carriers)
    before = snapshot([source, phases, carriers])
    a, b = direct_matrices(case)
    actual = product().replay_source(source, **case.kwargs())
    assert np.max(np.abs(actual - direct_prediction(case, a))) <= sum(
        scales(case, b)[key] for key in ("inverse_bound", "observer")
    )
    assert snapshot([source, phases, carriers]) == before


@pytest.mark.parametrize("beams", [[4.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 1.0]])
def test_replay_zero_carrier_duplicate_phase_single_beam(beams: list[float]) -> None:
    case = replace(
        tiny_case(), carriers=np.zeros((3, 2)), phases=np.full((3, 5), -0.73), beams=np.array(beams)
    )
    a, b = direct_matrices(case)
    actual = product().replay_source(case.source, **case.kwargs())
    assert np.max(np.abs(actual - direct_prediction(case, a))) <= sum(
        scales(case, b)[key] for key in ("inverse_bound", "observer")
    )
    zero = product().replay_source(np.zeros_like(case.source), **case.kwargs())
    np.testing.assert_array_equal(zero, np.zeros((3, 5, 2, 2, 3)))


def test_metric_small_signed_exact_and_frozen_records(strict_policies: Any) -> None:
    module = product()
    reference = np.array([3.0, -4.0, 0.0, 0.0])
    estimated = np.array([0.0, 0.0, -2.0, -1.0], dtype=np.float32)
    summary = module.compare_arrays(estimated, reference)
    assert isinstance(summary, module.MetricSummary)
    assert set(inspect.signature(module.MetricSummary).parameters) == set(FIELDS)
    assert summary.reference_l2 == 5.0
    assert summary.error_l2 == pytest.approx(math.sqrt(30), rel=2e-15)
    assert summary.relative_l2 == pytest.approx(math.sqrt(30) / 5, rel=2e-15)
    assert summary.error_rms == pytest.approx(math.sqrt(7.5), rel=2e-15)
    assert summary.error_max_abs == 4.0
    assert summary.error_mean == -0.5
    assert summary.unavailable_fields == ()
    assert_metrics(summary, estimated, reference)
    with pytest.raises((AttributeError, TypeError)):
        summary.count = 9
    zero = module.compare_arrays(np.zeros(1), np.zeros(1))
    entry = zero.unavailable_fields[0]
    assert isinstance(entry, module.UnavailableMetric)
    assert set(inspect.signature(module.UnavailableMetric).parameters) == {"field", "reason"}
    assert type(entry.field) is str and type(entry.reason) is str
    with pytest.raises((AttributeError, TypeError)):
        entry.reason = "made_up"


@pytest.mark.parametrize(
    "kind",
    [
        "all15",
        "scalar",
        "strided",
        "fortran",
        "readonly",
        "zero_stride",
        "mixed_width",
        "both_float32_extreme",
        "zero_reference",
        "both_zero",
    ],
)
def test_metric_positive_representations_and_full_array(kind: str, strict_policies: Any) -> None:
    reference = np.arange(1, 16, dtype=np.float64).reshape(3, 5, 1, 1, 1)
    estimated = reference + np.arange(-7, 8, dtype=np.float64).reshape(reference.shape)
    if kind == "scalar":
        reference, estimated = np.array(-4.0), np.array(2.0, dtype=np.float32)
    elif kind == "strided":
        reference = reference[::-1]
    elif kind == "fortran":
        reference = np.asfortranarray(reference)
    elif kind == "readonly":
        reference.flags.writeable = estimated.flags.writeable = False
    elif kind == "zero_stride":
        reference = np.broadcast_to(np.array(-3.0), (3, 5))
        estimated = np.broadcast_to(np.array(-2.0, dtype=np.float32), (3, 5))
    elif kind == "mixed_width":
        reference = reference.astype(np.float32)
    elif kind == "both_float32_extreme":
        reference = np.array([np.finfo(np.float32).max], dtype=np.float32)
        estimated = np.array([-np.finfo(np.float32).max], dtype=np.float32)
    elif kind in ("zero_reference", "both_zero"):
        reference = np.zeros(4)
        estimated = (
            np.array([-3.0, 1.0, -2.0, 0.0]) if kind == "zero_reference" else reference.copy()
        )
    before = snapshot([estimated, reference])
    summary = product().compare_arrays(estimated, reference)
    assert_metrics(summary, estimated, reference)
    assert snapshot([estimated, reference]) == before


@pytest.mark.parametrize(
    "estimated,reference",
    [
        ([1e200, -1e200, 3e200], [0.0, 1e200, -1e200]),
        ([0.0] * 4, [1e308] * 4),
        ([-1e308, 1e308, 0.0, 0.0], [1e308, -1e308, 0.0, 0.0]),
        ([-1e308, 1e308, 3.0, 0.0], [1e308, -1e308, 0.0, 0.0]),
        ([1e308, 1.0, -1e308], [0.0, 0.0, 0.0]),
        ([-1e308] * 4, [1e308] * 4),
        ([1.0], [float.fromhex("0x0.0000000000001p-1022")]),
        ([float.fromhex("0x0.0000000000002p-1022")], [float.fromhex("0x0.0000000000001p-1022")]),
        (
            [float.fromhex("0x1.fffffffffffffp+1023")] * 2
            + [-float.fromhex("0x1.fffffffffffffp+1023")] * 2,
            [0.0] * 4,
        ),
    ],
    ids=[
        "raw_squares",
        "norm_overflow",
        "subtraction_overflow_rms_available",
        "subtraction_overflow_small_signed_mean",
        "signed_sum_small_remainder",
        "ratio_only",
        "relative_overflow",
        "subnormal_norm",
        "signed_sum_cancellation",
    ],
)
def test_metric_independently_representable_extremes(
    estimated: list[float], reference: list[float], strict_policies: Any
) -> None:
    e, r = np.array(estimated), np.array(reference)
    before = snapshot([e, r])
    assert_metrics(product().compare_arrays(e, r), e, r)
    assert snapshot([e, r]) == before


class ArraySubclass(np.ndarray):
    """A real ndarray subclass, excluded by the plain-array public grammar."""


@pytest.mark.parametrize(
    "bad",
    [
        [1.0],
        np.array([], dtype=np.float64),
        np.array([True]),
        np.array([1], dtype=np.int64),
        np.array([1], dtype=np.float16),
        np.array([1j]),
        np.array([object()]),
        np.array([1.0]).astype(np.dtype("float64").newbyteorder("S")),
        np.array([1.0]).view(ArraySubclass),
        np.array([math.nan]),
        np.array([math.inf]),
    ],
)
@pytest.mark.parametrize("field", ["estimated", "reference"])
def test_metric_invalid_grammar(bad: Any, field: str, strict_policies: Any) -> None:
    args = {"estimated": np.ones(1), "reference": np.ones(1), field: bad}
    arrays = [v for v in args.values() if isinstance(v, np.ndarray)]
    before = snapshot(arrays)
    assert_invalid(lambda: product().compare_arrays(**args), field)
    assert snapshot(arrays) == before


def test_metric_same_shape_no_broadcast() -> None:
    module = product()
    with pytest.raises(Exception) as caught:
        module.compare_arrays(np.ones((1, 2)), np.ones(2))
    assert getattr(caught.value, "code", None) == "invalid_reference_alignment_ra14"
    assert any(field in str(caught.value) for field in ("estimated", "reference"))


@pytest.mark.parametrize(
    "field,bad,diagnostic",
    [
        ("source_relative", np.zeros((2, 4, 6), dtype=np.float64), "source"),
        ("source_relative", np.zeros((2, 4, 6), dtype=np.int32), "source"),
        ("source_relative", np.zeros((2, 3, 6), dtype=np.float32), "source"),
        ("source_relative", np.zeros((0, 4, 6), dtype=np.float32), "source"),
        ("source_relative", np.zeros((4, 6), dtype=np.float32), "source"),
        ("source_relative", np.zeros((2, 4, 6), dtype=np.float32).view(ArraySubclass), "source"),
        ("source_relative", np.full((2, 4, 6), math.inf, dtype=np.float32), "source"),
        ("source_relative", [[[1.0]]], "source"),
        ("source_spacing_um_zyx", [0.1, 0.1, 0.1], "spacing"),
        ("source_spacing_um_zyx", (0.1, 0.0, 0.1), "spacing"),
        ("source_spacing_um_zyx", (0.1, True, 0.1), "spacing"),
        ("source_spacing_um_zyx", (0.1, np.float64(0.1), 0.1), "spacing"),
        ("source_spacing_um_zyx", (0.1, math.inf, 0.1), "spacing"),
        ("source_spacing_um_zyx", (0.1, 0.1), "spacing"),
        ("carriers_yx_per_um", np.zeros((2, 3)), "carriers"),
        ("carriers_yx_per_um", np.zeros((3, 2), dtype=np.float32), "carriers"),
        ("carriers_yx_per_um", np.full((3, 2), math.nan), "carriers"),
        ("carriers_yx_per_um", np.full((3, 2), 4.0), "carriers"),
        (
            "carriers_yx_per_um",
            np.zeros((3, 2)).astype(np.dtype("float64").newbyteorder("S")),
            "carriers",
        ),
        ("phases_at_specimen_origin_rad", np.zeros((5, 3)), "phases"),
        ("phases_at_specimen_origin_rad", np.zeros((3, 5), dtype=np.int64), "phases"),
        ("phases_at_specimen_origin_rad", np.full((3, 5), math.inf), "phases"),
        ("beam_amplitudes", (4.0, 2.0, 1.0), "beam"),
        ("beam_amplitudes", np.ones(2), "beam"),
        ("beam_amplitudes", np.ones(3, dtype=np.float32), "beam"),
        ("beam_amplitudes", np.array([1.0, -0.1, 0.5]), "beam"),
        ("beam_amplitudes", np.zeros(3), "beam"),
        ("beam_amplitudes", np.array([1.0, 0.5, math.nan]), "beam"),
        ("pupil_order", 0, "pupil_order"),
        ("pupil_order", True, "pupil_order"),
        ("pupil_order", np.int64(3), "pupil_order"),
        ("pupil_order", 3.0, "pupil_order"),
    ],
)
def test_replay_invalid_grammar(
    field: str, bad: Any, diagnostic: str, strict_policies: Any
) -> None:
    case = tiny_case()
    args = {"source_relative": case.source, **case.kwargs(), field: bad}
    arrays = [v for v in args.values() if isinstance(v, np.ndarray)]
    before = snapshot(arrays)
    assert_invalid(lambda: product().replay_source(**args), diagnostic)
    assert snapshot(arrays) == before


def test_validation_precedes_numerical_work(strict_policies: Any) -> None:
    case = tiny_case()
    args = case.kwargs()
    args["source_spacing_um_zyx"] = (float.fromhex("0x1.fffffffffffffp+1023"), 0.1, 0.1)
    args["phases_at_specimen_origin_rad"] = np.zeros((1, 5))
    assert_invalid(lambda: product().replay_source(case.source, **args), "phases")


def test_public_binding_rejects_extra_truth_and_missing_arguments() -> None:
    module = product()
    case = tiny_case()
    with pytest.raises(TypeError):
        module.replay_source(case.source, **case.kwargs(), truth=case.source)
    with pytest.raises(TypeError):
        module.replay_source(case.source)
    with pytest.raises(TypeError):
        module.compare_arrays(np.zeros(1))
    with pytest.raises(TypeError):
        module.compare_arrays(np.zeros(1), np.zeros(1), acceptance_threshold=0.1)


@pytest.mark.parametrize(
    "mode",
    [
        "cache_memory",
        "cache_value",
        "forward_memory",
        "forward_value",
        "forward_warning",
        "invalid_before_cache",
        "real_range",
    ],
)
def test_public_dependency_failures_and_warning_propagation(mode: str) -> None:
    # Import absence keeps its own classification before any child assertion.
    product()
    # A fresh process binds only the public dependency before importing replay.
    # No private wrapper symbol, backend or new production seam is selected.
    code = textwrap.dedent("""
        import random, sys, warnings
        import numpy as np
        from simrecon import SimreconError
        from scripts import simulation_inverse_operator as inverse
        mode = sys.argv[1]
        original_build, original_forward = inverse.build_kernel_cache, inverse.forward
        error = (MemoryError("A1 allocation sentinel") if mode.endswith("memory")
                 else ValueError("A1 dependency sentinel"))
        calls = {"cache": 0, "forward": 0}
        dependency_errors = []
        source = np.ones((1, 2, 2), dtype=np.float32)
        spacing = (0.125, 0.04, 0.04)
        phases = np.arange(15, dtype=np.float64).reshape(3, 5) * 0.31
        if mode == "invalid_before_cache":
            phases = phases[:, :4]
        carriers = np.array([[0.1, -0.2], [0.3, 0.1], [-0.2, -0.1]])
        beams = np.array([4., 2., 1.])
        if mode == "real_range":
            spacing = (0.125, 1e155, 1e155)
            carriers = np.zeros((3, 2), dtype=np.float64)
            phases = np.zeros((3, 5), dtype=np.float64)
            beams = np.array([1., 0., 0.], dtype=np.float64)
        original_phases = phases.copy()
        inputs = (source, carriers, phases, beams)
        def input_state():
            return [(a.shape, a.strides, a.dtype.str, a.flags.writeable, a.tobytes())
                    for a in inputs]
        original_inputs = input_state()
        python_random, numpy_random = random.getstate(), np.random.get_state()
        cache = None
        def build(**kwargs):
            global cache
            calls["cache"] += 1
            assert mode != "invalid_before_cache", "numerical work before validation"
            assert kwargs == dict(source_shape_zyx=(1, 2, 2),
                source_spacing_um_zyx=spacing, emission_um=0.525,
                refractive_index=1.515, detection_na=1.4, pupil_order=1)
            if mode.startswith("cache"):
                raise error
            try:
                cache = original_build(**kwargs)
            except Exception as actual:
                if mode == "real_range":
                    dependency_errors.append(actual)
                raise
            return cache
        def forward(source_e, **kwargs):
            x = source_e
            calls["forward"] += 1
            assert type(x) is np.ndarray and x.dtype == source.dtype
            assert np.array_equal(x, source)
            o = calls["forward"] - 1
            assert kwargs["kernel_cache"] is cache
            assert np.array_equal(kwargs["carrier_yx_per_um"], carriers[o])
            assert np.array_equal(kwargs["phases_rad"], phases[o])
            assert np.array_equal(kwargs["beam_amplitudes"], beams)
            assert kwargs["excitation_um"] == 0.488
            if mode == "real_range":
                try:
                    return original_forward(source_e=x, **kwargs)
                except Exception as actual:
                    dependency_errors.append(actual)
                    raise
            if mode == "forward_warning":
                warnings.warn("A1 unrelated warning", UserWarning)
                return original_forward(x, **kwargs)
            # Fail after one complete orientation: never return a partial stack.
            if calls["forward"] == 2:
                raise error
            return original_forward(x, **kwargs)
        inverse.build_kernel_cache, inverse.forward = build, forward
        from scripts.reference_alignment_ra14_comparison import replay_source
        with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
            warnings.simplefilter("always", UserWarning)
            filters, settings = warnings.filters[:], np.geterr().copy()
            try:
                prediction = replay_source(source, source_spacing_um_zyx=spacing,
                    carriers_yx_per_um=carriers, phases_at_specimen_origin_rad=phases,
                    beam_amplitudes=beams, pupil_order=1)
            except Exception as actual:
                if mode == "real_range":
                    assert isinstance(actual, SimreconError)
                    assert actual.code == "simulation_inverse_operator_range"
                    assert any(actual is recorded for recorded in dependency_errors)
                elif mode == "invalid_before_cache":
                    assert getattr(actual, "code", None) == "invalid_reference_alignment_ra14"
                    assert "phases" in str(actual)
                else:
                    assert mode != "forward_warning"
                    assert actual is error
            else:
                assert mode == "forward_warning"
                assert prediction.shape == (3, 5, 1, 1, 1)
            assert warnings.filters == filters and np.geterr() == settings
        assert calls["cache"] == (0 if mode == "invalid_before_cache" else 1)
        if mode != "real_range":
            expected_calls = (0 if mode.startswith("cache") or mode == "invalid_before_cache"
                              else 3 if mode.endswith("warning") else 2)
            assert calls["forward"] == expected_calls
        assert len(caught) == (3 if mode.endswith("warning") else 0)
        for item in caught:
            assert item.category is UserWarning and str(item.message) == "A1 unrelated warning"
        assert np.all(source == 1)
        assert np.array_equal(phases, original_phases)
        assert input_state() == original_inputs
        assert random.getstate() == python_random
        after_random = np.random.get_state()
        assert after_random[0] == numpy_random[0]
        assert np.array_equal(after_random[1], numpy_random[1])
        assert after_random[2:] == numpy_random[2:]
        print("public dependency propagation passed", mode)
    """)
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/source_free_check.py",
            "--timeout",
            "120",
            "python",
            "-c",
            code,
            mode,
        ],
        capture_output=True,
        text=True,
        timeout=150,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "public dependency propagation passed" in completed.stdout
