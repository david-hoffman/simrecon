"""Blind public-entry tests for the threshold-based integer-carrier selector."""

from __future__ import annotations

import math
import warnings
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from fractions import Fraction
from typing import Any, Literal

import numpy as np
import pytest
import scipy.fft

import simrecon
from carrier_selection_fixture import (
    SelectionFixture,
    expected_fit,
    landscape,
    sparse_landscape,
)


class ArraySubclass(np.ndarray):
    """Nonplain array representation for rejection examples."""


class NumericObject:
    """Convertible custom numeric objects remain outside the scalar contract."""

    def __float__(self) -> float:
        """Supply an otherwise valid value to distinguish type validation."""
        return 0.5


def selector() -> Any:
    function = getattr(simrecon, "select_carrier", None)
    assert callable(function), "public select_carrier export is required"
    return function


def arguments(fixture: SelectionFixture, **changes: Any) -> dict[str, Any]:
    result = {
        "otf": fixture.calibration(simrecon),
        "phase_steps_rad": fixture.steps,
        "candidate_carriers_bins_yx": [(0, 1)],
        "max_relative_residual": 1.0,
        "min_overlap_count": 1,
        "modulation_bounds": (0.0, 20.0),
    }
    result.update(changes)
    return result


def invoke(fixture: SelectionFixture | None = None, **changes: Any) -> Any:
    function = selector()
    if fixture is None:
        fixture = landscape()
    return function(fixture.images, **arguments(fixture, **changes))


def assert_code(code: str, function: Any, *args: Any, **kwargs: Any) -> Any:
    error_type: Any = getattr(simrecon, "SimreconError", None)
    with pytest.raises(error_type) as caught:
        function(*args, **kwargs)
    error: Any = caught.value
    assert error.code == code
    return error


def assert_decision(result: Any, residual: float, count: int, bounds: tuple[float, float]) -> None:
    """Policy truth from SAME returned diagnostics, not a numerical fit oracle."""
    expected = tuple(
        j
        for j, row in enumerate(result.candidates)
        if row.estimate is not None
        and row.estimate.relative_residual <= residual
        and row.estimate.overlap_count >= count
        and bounds[0] <= row.estimate.modulation <= bounds[1]
    )
    assert result.eligible_indices == expected
    assert type(result.eligible_indices) is tuple
    assert all(type(j) is int for j in result.eligible_indices)
    assert result.selected_index == (expected[0] if len(expected) == 1 else None)
    assert result.failure_code == (
        None
        if len(expected) == 1
        else "no_acceptable_carrier"
        if not expected
        else "ambiguous_carrier"
    )
    if result.selected_index is not None:
        assert type(result.selected_index) is int


def test_exports_binding_and_frozen_record() -> None:
    function = selector()
    fixture = landscape()
    result_type = getattr(simrecon, "CarrierSelection", None)
    assert isinstance(result_type, type), "public CarrierSelection export is required"
    result = invoke(fixture)
    assert isinstance(result, result_type)
    assert type(result.candidates) is tuple
    assert len(result.candidates) == 1
    for field in ("candidates", "eligible_indices", "selected_index", "failure_code"):
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(result, field, getattr(result, field))
    kwargs = arguments(fixture)
    for missing in kwargs:
        with pytest.raises(TypeError):
            function(
                fixture.images, **{key: value for key, value in kwargs.items() if key != missing}
            )
    with pytest.raises(TypeError):
        function(
            fixture.images,
            kwargs["otf"],
            **{key: value for key, value in kwargs.items() if key != "otf"},
        )
    with pytest.raises(TypeError):
        function(fixture.images, **kwargs, unknown_policy=True)


@pytest.mark.parametrize(
    "value",
    [
        0,
        -0.0,
        np.int8(1),
        np.uint64(2**63),
        np.float16(1),
        np.float32(1),
        np.float64(1),
        np.longdouble(1),
        10**200,
    ],
)
def test_valid_residual_scalars(value: Any) -> None:
    result = invoke(max_relative_residual=value)
    assert_decision(result, float(value), 1, (0.0, 20.0))


def invalid_reals() -> list[Any]:
    return [
        True,
        np.bool_(False),
        -1,
        -0.01,
        float("nan"),
        float("inf"),
        -float("inf"),
        complex(1),
        "1",
        None,
        [1],
        np.array(1.0),
        np.array([1.0]),
        Fraction(1, 2),
        Decimal("0.5"),
        NumericObject(),
        10**10000,
    ]


@pytest.mark.parametrize("value", invalid_reals(), ids=lambda value: type(value).__name__)
def test_invalid_residual_scalars(value: Any) -> None:
    selector()
    assert_code("invalid_carrier_selection_policy", invoke, max_relative_residual=value)


@pytest.mark.parametrize(
    "value",
    [1, np.int8(1), np.uint64(2**64 - 1), 10**10000],
    ids=["python", "numpy-signed", "numpy-unsigned", "arbitrary-precision"],
)
def test_valid_exact_integer_count(value: Any) -> None:
    result = invoke(min_overlap_count=value)
    assert_decision(result, 1.0, int(value), (0.0, 20.0))
    if int(value) > 35:
        assert result.eligible_indices == ()
        assert result.failure_code == "no_acceptable_carrier"


@pytest.mark.parametrize(
    "value",
    [0, -1, True, np.bool_(True), 1.0, np.float64(2), "1", np.array(1), [1], None, Fraction(1)],
)
def test_invalid_overlap_counts(value: Any) -> None:
    selector()
    assert_code("invalid_carrier_selection_policy", invoke, min_overlap_count=value)


def valid_bound_containers() -> list[Any]:
    readonly = np.array([[0.0, 7.0], [99.0, 99.0]]).T[:, 0]
    readonly.flags.writeable = False
    return [
        (0, 20),
        [np.int16(0), np.float32(20)],
        np.array([0, 20], dtype=">i8"),
        np.array([0, 20], dtype=">f8"),
        readonly,
        np.array([np.uint8(0), np.longdouble(20)], dtype=object),
        (0, 0),
        (-0.0, 0.0),
        (20, 20),
    ]


@pytest.mark.parametrize("value", valid_bound_containers(), ids=lambda value: type(value).__name__)
def test_valid_modulation_bounds(value: Any) -> None:
    result = invoke(modulation_bounds=value)
    assert_decision(result, 1.0, 1, (float(value[0]), float(value[1])))


def invalid_bound_containers() -> list[Any]:
    containers: list[Any] = [
        None,
        (),
        (0,),
        (0, 1, 2),
        {0, 1},
        iter([0, 1]),
        np.array(1),
        np.array([[0, 1]]),
        np.array([[0], [1]]),
        np.array([0, 1]).view(ArraySubclass),
        (-1, 1),
        (2, 1),
        (0, complex(1)),
        (0, "1"),
        np.array([0, 1], dtype=bool),
        np.array([0, 1], dtype=complex),
        np.array(["0", "1"]),
    ]
    for value in invalid_reals():
        containers.extend([(value, 2.0), (0.0, value)])
    return containers


@pytest.mark.parametrize(
    "value", invalid_bound_containers(), ids=lambda value: type(value).__name__
)
def test_invalid_modulation_bounds(value: Any) -> None:
    selector()
    assert_code("invalid_carrier_selection_policy", invoke, modulation_bounds=value)


def wide_values() -> tuple[Any, Any, Any]:
    """Derive real capability; no platform skips or invented wider exponent."""
    wide = np.finfo(np.longdouble)
    double = np.finfo(np.float64)
    if wide.maxexp > double.maxexp:
        overflow = np.ldexp(np.longdouble(1), double.maxexp)
    else:
        overflow = 10**10000
    if wide.minexp - wide.nmant < double.minexp - double.nmant:
        tiny = np.ldexp(np.longdouble(1), double.minexp - double.nmant - 2)
    else:
        tiny = np.nextafter(np.float64(0), np.float64(1))
    return overflow, tiny, -tiny


def test_source_and_converted_policy_representability() -> None:
    selector()
    overflow, tiny, negative = wide_values()
    if isinstance(overflow, np.floating):
        assert np.isfinite(overflow)
    for field, value in [
        ("max_relative_residual", overflow),
        ("modulation_bounds", (0, overflow)),
    ]:
        assert_code("invalid_carrier_selection_policy", invoke, **{field: value})
    with np.errstate(all="ignore"):
        converted = float(tiny)
    assert tiny > 0
    # Range applies AFTER conversion. A finite negative wide scalar that
    # becomes negative zero is permitted, just like an explicit -0.0.
    if float(negative) < 0:
        assert_code("invalid_carrier_selection_policy", invoke, max_relative_residual=negative)
        assert_code("invalid_carrier_selection_policy", invoke, modulation_bounds=(negative, 1))
    else:
        result = invoke(max_relative_residual=negative, modulation_bounds=(negative, 1))
        assert_decision(result, -0.0, 1, (-0.0, 1))
    for bounds in [(0, tiny), (tiny, tiny)]:
        result = invoke(modulation_bounds=bounds, max_relative_residual=tiny)
        assert_decision(result, converted, 1, (float(bounds[0]), float(bounds[1])))


def test_policy_validation_precedes_numerical_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    selector()
    fixture = landscape()
    sentinel = MemoryError("public numeric execution must not occur for invalid policy")

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    # Both supported Fourier families and phase SVD/solve: no product seam.
    for module, names in [
        (np.fft, ("fft", "fft2", "fftn")),
        (scipy.fft, ("fft", "fft2", "fftn")),
        (np.linalg, ("svd", "lstsq")),
    ]:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    for changes in [
        {"max_relative_residual": True},
        {"min_overlap_count": 1.0},
        {"modulation_bounds": (2, 1)},
    ]:
        assert_code("invalid_carrier_selection_policy", invoke, fixture, **changes)


def test_independent_complex_landscape_and_oracle_regime() -> None:
    selector()
    fixture = landscape()
    carriers = [(0, 0), (0, 1), (0, 2)]
    result = invoke(fixture, candidate_carriers_bins_yx=carriers)
    assert len(result.candidates) == len(carriers)
    matrix = np.column_stack(
        (np.ones(len(fixture.steps)), np.cos(fixture.steps), np.sin(fixture.steps))
    )
    assert np.linalg.cond(matrix) < 10
    budget = 8192 * len(fixture.steps) * 35 * 2**-52
    for row, carrier in zip(result.candidates, carriers, strict=True):
        truth = expected_fit(fixture, carrier)
        estimate = row.estimate
        assert row.carrier_bins_yx == carrier
        assert row.failure_code is None
        assert estimate is not None
        actual_gain = 0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad)
        # Finite sums and one final rational->float rounding are far below delta.
        assert abs(actual_gain - truth.gain) <= budget * max(1.0, abs(truth.gain))
        assert abs(estimate.relative_residual - truth.residual) <= budget
        assert estimate.overlap_count == truth.count
        assert type(estimate.overlap_count) is int
        assert estimate.source == fixture.source
        assert all(
            type(v) is float
            for v in (estimate.modulation, estimate.phase_offset_rad, estimate.relative_residual)
        )
        image_max = float(np.max(np.abs(fixture.images)))
        assert min(truth.norm_x, truth.norm_y) >= image_max / 8
        assert truth.correlation >= 0.25
        assert 1e-4 <= abs(truth.gain) <= 10
        assert abs(actual_gain - truth.gain) < 2e-11
        assert abs(estimate.relative_residual - truth.residual) < 2e-11
    assert_decision(result, 1.0, 1, (0, 20))


@pytest.mark.parametrize("position", [0, 1, 2, 4])
def test_sole_eligible_row_at_arbitrary_index(position: int) -> None:
    carriers = [(0, -1), (1, 1), (20, 0), (0, 0)]
    carriers.insert(position, (0, 1))
    result = invoke(
        candidate_carriers_bins_yx=carriers, max_relative_residual=0.1, modulation_bounds=(0.6, 1.0)
    )
    assert result.eligible_indices == (position,)
    assert result.selected_index == position
    assert result.failure_code is None
    assert len(result.candidates) == 5


@pytest.mark.parametrize(
    "changes",
    [
        {"max_relative_residual": 0.001},
        {"min_overlap_count": 31},
        {"modulation_bounds": (0.9, 2)},
        {"modulation_bounds": (0, 0.7)},
    ],
    ids=["residual", "count", "lower-modulation", "upper-modulation"],
)
def test_each_gate_is_necessary_in_conjunction(changes: dict[str, Any]) -> None:
    baseline = invoke()
    assert baseline.eligible_indices == (0,)
    result = invoke(**changes)
    assert result.eligible_indices == ()
    assert result.selected_index is None
    assert result.failure_code == "no_acceptable_carrier"
    assert result.candidates[0].estimate is not None


def test_exact_count_boundary_and_represented_float_boundaries() -> None:
    baseline = invoke()
    estimate = baseline.candidates[0].estimate
    count = estimate.overlap_count
    assert invoke(min_overlap_count=count).eligible_indices == (0,)
    assert invoke(min_overlap_count=count + 1).eligible_indices == ()
    # Reuse actual represented diagnostics, not ideal generating m or residual.
    # The predicate is checked against THIS call's returned diagnostics because
    # separate numerical calls are not promised to be bitwise identical.
    residual = estimate.relative_residual
    modulation = estimate.modulation
    for threshold in [np.nextafter(residual, -np.inf), residual, np.nextafter(residual, np.inf)]:
        result = invoke(max_relative_residual=threshold)
        assert_decision(result, float(threshold), 1, (0, 20))
    for bounds in [
        (modulation, modulation),
        (0, modulation),
        (modulation, 20),
        (0, np.nextafter(modulation, -np.inf)),
        (np.nextafter(modulation, np.inf), 20),
    ]:
        result = invoke(modulation_bounds=bounds)
        assert_decision(result, 1, 1, (float(bounds[0]), float(bounds[1])))


def test_ambiguity_has_no_residual_or_geometry_preference() -> None:
    fixture = landscape()
    carriers = [(0, 0), (0, 1), (0, 2)]
    result = invoke(fixture, candidate_carriers_bins_yx=carriers)
    assert result.eligible_indices == (0, 1, 2)
    assert result.selected_index is None
    assert result.failure_code == "ambiguous_carrier"
    truths = [expected_fit(fixture, carrier) for carrier in carriers]
    assert len({truth.count for truth in truths}) == 3
    assert max(truth.residual for truth in truths) - min(truth.residual for truth in truths) > 0.5


def test_duplicates_order_huge_and_signed_local_failures_are_retained() -> None:
    carriers = [(0, 10**100), (0, 1), (0, -1), (0, 1), (-(10**100), 0), (0, 0)]
    result = invoke(candidate_carriers_bins_yx=carriers, max_relative_residual=0.1)
    assert [row.carrier_bins_yx for row in result.candidates] == carriers
    assert result.eligible_indices == (1, 3)
    assert result.failure_code == "ambiguous_carrier"
    for index in (0, 4):
        assert result.candidates[index].estimate is None
        assert result.candidates[index].failure_code == "no_illumination_overlap"
    assert result.candidates[2].estimate is not None
    assert result.candidates[5].estimate is not None
    assert all(type(v) is int for row in result.candidates for v in row.carrier_bins_yx)


def test_all_local_failures_return_complete_no_match() -> None:
    fixture = landscape()
    fixture.images.fill(0)
    result = invoke(fixture, candidate_carriers_bins_yx=[(0, 1), (100, 0), (0, 0)])
    assert result.eligible_indices == ()
    assert result.failure_code == "no_acceptable_carrier"
    assert result.selected_index is None
    assert [row.failure_code for row in result.candidates] == [
        "unidentifiable_illumination",
        "no_illumination_overlap",
        "unidentifiable_illumination",
    ]
    assert all(row.estimate is None for row in result.candidates)


def test_sparse_above_one_fit_is_policy_accepted_without_confidence_claim() -> None:
    fixture = sparse_landscape()
    result = invoke(
        fixture,
        candidate_carriers_bins_yx=[(0, 1)],
        max_relative_residual=1e-8,
        modulation_bounds=(2.3, 2.5),
    )
    estimate = result.candidates[0].estimate
    assert result.eligible_indices == (0,)
    assert estimate.overlap_count == 4
    assert abs(estimate.modulation - 2.4) < 2e-11
    assert (
        abs(0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad) - 1.2 * np.exp(0.4j))
        < 2e-11
    )
    rejected = invoke(fixture, max_relative_residual=1e-8, modulation_bounds=(0, 1))
    assert rejected.failure_code == "no_acceptable_carrier"


def valid_candidates() -> list[Any]:
    readonly = np.array([[0, 1], [0, -1], [0, 1]], dtype=">i8")
    readonly.flags.writeable = False
    strided = np.array([[0, 99, 1, 99], [0, 99, -1, 99], [0, 99, 1, 99]])[:, ::2]
    return [
        [(0, 1), [np.int16(0), np.uint8(1)], (0, -1)],
        ((0, 1), (0, -1), (0, 1)),
        readonly,
        strided,
        np.array([[0, 1], [0, -1], [0, 1]], dtype=object),
    ]


@pytest.mark.parametrize("carriers", valid_candidates(), ids=lambda value: type(value).__name__)
def test_valid_candidate_representations(carriers: Any) -> None:
    result = invoke(candidate_carriers_bins_yx=carriers)
    expected = [tuple(int(v) for v in row) for row in carriers]
    assert [row.carrier_bins_yx for row in result.candidates] == expected
    assert_decision(result, 1, 1, (0, 20))


@pytest.mark.parametrize(
    "carriers",
    [
        [],
        (),
        iter([(0, 1)]),
        {(0, 1)},
        np.array([0, 1]),
        np.array([[[0, 1]]]),
        np.array([[0, 1]]).view(ArraySubclass),
        [(0, 1), (0, True)],
        [(0, 1), (0, 1.0)],
        [(0, 1), (0,)],
        [(0, 1), (0, 1, 2)],
        [(0, 1), np.array([0, 1]).view(ArraySubclass)],
    ],
    ids=lambda value: type(value).__name__,
)
def test_entire_candidate_validation_after_valid_prefix(carriers: Any) -> None:
    selector()
    assert_code("invalid_carrier_candidates", invoke, candidate_carriers_bins_yx=carriers)


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("images", [1, 2, 3], "invalid_phase_images"),
        ("images", np.zeros((5, 5, 7), dtype=complex), "invalid_phase_dtype"),
        ("images", np.zeros((2, 5, 7)), "invalid_phase_shape"),
        ("images", np.full((5, 5, 7), np.nan), "nonfinite_phase_images"),
        ("phase_steps_rad", [0, 1, 2, 3, 4], "invalid_phase_angles"),
        ("phase_steps_rad", np.ones(5, dtype=bool), "invalid_phase_angles_dtype"),
        ("phase_steps_rad", np.ones(4), "invalid_phase_angles_shape"),
        ("phase_steps_rad", np.full(5, np.inf), "nonfinite_phase_angles"),
        ("phase_steps_rad", np.zeros(5), "rank_deficient_phases"),
        ("otf", None, "invalid_illumination_otf"),
    ],
)
def test_common_input_validation_even_when_no_candidate_overlaps(
    field: str, value: Any, code: str
) -> None:
    function = selector()
    fixture = landscape()
    kwargs = arguments(fixture, candidate_carriers_bins_yx=[(10**100, 0)])
    images = fixture.images
    if field == "images":
        images = value
    else:
        kwargs[field] = value
    assert_code(code, function, images, **kwargs)


@pytest.mark.parametrize(
    "damage,code",
    [
        ("grid", "incompatible_illumination_otf_grid"),
        ("transfer", "invalid_illumination_otf"),
        ("source", "invalid_illumination_otf"),
    ],
)
def test_direct_otf_validation_without_success(damage: str, code: str) -> None:
    selector()
    fixture = landscape()
    calibration = fixture.calibration(simrecon)
    if damage == "grid":
        calibration = replace(calibration, fx_per_um=calibration.fx_per_um + 0.125)
    elif damage == "transfer":
        calibration.values[0, 0] = 3j
    else:
        calibration = replace(calibration, source="  ")
    assert_code(code, invoke, fixture, otf=calibration, candidate_carriers_bins_yx=[(100, 100)])


def test_result_arrays_independent_mutable_and_sources_preserved() -> None:
    selector()
    fixture = landscape()
    calibration = fixture.calibration(simrecon)
    carriers = np.array([[0, 1], [0, 1], [0, -1]], dtype=">i8")
    bounds = np.array([0, 20], dtype=object)
    sources = [
        fixture.images,
        fixture.steps,
        calibration.values,
        calibration.fy_per_um,
        calibration.fx_per_um,
        carriers,
        bounds,
    ]
    snapshots = [value.copy() for value in sources]
    result = invoke(
        fixture, otf=calibration, candidate_carriers_bins_yx=carriers, modulation_bounds=bounds
    )
    arrays = [row.estimate.phases_rad for row in result.candidates]
    for index, array in enumerate(arrays):
        assert array.dtype == np.dtype("float64")
        assert array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        assert array.shape == fixture.steps.shape
        for source in sources:
            assert not np.shares_memory(array, source)
        for other in arrays[index + 1 :]:
            assert not np.shares_memory(array, other)
    preserved = [value.copy() for value in arrays]
    arrays[0][0] = 123.0
    for actual, before in zip(arrays[1:], preserved[1:], strict=True):
        np.testing.assert_array_equal(actual, before)
    for row in result.candidates:
        with pytest.raises((FrozenInstanceError, AttributeError)):
            row.failure_code = "changed"
        with pytest.raises((FrozenInstanceError, AttributeError)):
            row.estimate.modulation = 9.0
    for actual, before in zip(sources, snapshots, strict=True):
        np.testing.assert_array_equal(actual, before)
    for changes in [
        {"modulation_bounds": (1, 0)},
        {"candidate_carriers_bins_yx": [(0, 1), (0, False)]},
    ]:
        assert_code(
            "invalid_carrier_selection_policy"
            if "modulation_bounds" in changes
            else "invalid_carrier_candidates",
            invoke,
            fixture,
            otf=calibration,
            **changes,
        )
    for actual, before in zip(sources, snapshots, strict=True):
        np.testing.assert_array_equal(actual, before)


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_error_mode_and_warning_preservation(
    mode: Literal["ignore", "warn", "raise", "call", "print", "log"],
) -> None:
    selector()
    fixture = landscape(off_model=False)
    fixture.images *= 2.0**1000
    overflow, tiny, _ = wide_values()
    before = np.geterr()
    with np.errstate(all=mode), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = invoke(fixture, max_relative_residual=1e-8, modulation_bounds=(0.7, 0.9))
        assert result.eligible_indices == (0,)
        assert_code("invalid_carrier_selection_policy", invoke, fixture, max_relative_residual=-1)
        assert_code(
            "invalid_carrier_selection_policy", invoke, fixture, max_relative_residual=overflow
        )
        result = invoke(fixture, max_relative_residual=tiny)
        assert_decision(result, float(tiny), 1, (0.0, 20.0))
        assert np.geterr() == dict.fromkeys(before, mode)
    assert np.geterr() == before
    assert not [warning for warning in caught if issubclass(warning.category, RuntimeWarning)]


@pytest.mark.parametrize("exponent", [-1020, 1000])
def test_safe_common_image_scales(exponent: int) -> None:
    fixture = landscape(off_model=False)
    fixture.images *= 2.0**exponent
    result = invoke(fixture, max_relative_residual=1e-8, modulation_bounds=(0.7, 0.9))
    estimate = result.candidates[0].estimate
    assert result.eligible_indices == (0,)
    assert (
        abs(
            0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad) - 0.4 * np.exp(0.63j)
        )
        < 2e-10
    )
    assert estimate.relative_residual < 2e-10


def test_huge_steps_use_represented_trigonometry_and_preserve_offset() -> None:
    steps = np.array([1e100, -1e200, 1e300, -1e50, 0.7, 4.1])
    fixture = landscape(off_model=False, steps=steps)
    result = invoke(fixture, max_relative_residual=1e-8, modulation_bounds=(0.7, 0.9))
    estimate = result.candidates[0].estimate
    assert result.eligible_indices == (0,)
    theta = estimate.phase_offset_rad
    expected = np.exp(1j * steps) * np.exp(1j * theta)
    assert np.max(np.abs(np.exp(1j * estimate.phases_rad) - expected)) < 2e-11
    assert np.max(np.abs(estimate.phases_rad)) <= np.pi
    truth = expected_fit(fixture, (0, 1))
    assert abs(0.5 * estimate.modulation * np.exp(1j * theta) - truth.gain) < 2e-11


def test_subnormal_images_have_no_arbitrary_positive_cutoff() -> None:
    # Dyadic stored intensities with thousands of subnormal quanta retain a
    # meaningful gain. Exact-real boundary digits are deliberately not assumed.
    fixture = landscape(off_model=False)
    quantum = np.nextafter(0.0, 1.0)
    fixture.images = np.rint(fixture.images * 2**15) * quantum
    result = invoke(fixture, max_relative_residual=0.01, modulation_bounds=(0.7, 0.9))
    assert result.eligible_indices == (0,)
    estimate = result.candidates[0].estimate
    assert math.isfinite(estimate.modulation)
    assert abs(estimate.modulation - 0.8) < 0.002


@pytest.mark.parametrize(
    "dtype", ["float16", "float32", "float64", "longdouble", ">f8", "int16", "uint16"]
)
def test_real_storage_and_readonly_strided_compatibility(dtype: str) -> None:
    fixture = landscape()
    if np.dtype(dtype).kind in "iu":
        fixture.images = np.rint(fixture.images * 100).astype(dtype)
    else:
        fixture.images = fixture.images.astype(dtype)
    backing = np.empty((len(fixture.steps), 10, 14), dtype=fixture.images.dtype)
    backing[:, ::2, ::2] = fixture.images
    fixture.images = backing[:, ::2, ::2]
    fixture.images.flags.writeable = False
    fixture.steps = fixture.steps.astype(">f8")
    fixture.steps.flags.writeable = False
    result = invoke(fixture)
    estimate = result.candidates[0].estimate
    truth = expected_fit(fixture, (0, 1))
    assert (
        abs(0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad) - truth.gain) < 2e-10
    )
    assert abs(estimate.relative_residual - truth.residual) < 2e-10


@pytest.mark.parametrize(
    "kind", ["value", "floating", "overflow", "nonfinite", "memory", "unrelated"]
)
def test_public_transform_errors_abort_without_partial_result(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    selector()
    fixture = landscape()
    sentinel: Exception
    if kind == "value":
        sentinel = ValueError("controlled public transform failure")
    elif kind == "floating":
        sentinel = FloatingPointError("controlled public transform failure")
    elif kind == "overflow":
        sentinel = OverflowError("controlled public transform failure")
    elif kind == "memory":
        sentinel = MemoryError("controlled public transform allocation failure")
    else:
        sentinel = RuntimeError("controlled unrelated public transform failure")
    calls = []

    def fail(array: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        if kind == "nonfinite":
            return np.full(np.shape(array), complex(np.nan, 0))
        raise sentinel

    for module in (np.fft, scipy.fft):
        for name in ("fft", "fft2", "fftn"):
            monkeypatch.setattr(module, name, fail)
    # The first row is independently known eligible; a valid prefix must never
    # become a partial selection if numerical execution fails for this call.
    kwargs = {"candidate_carriers_bins_yx": [(0, 1), (1, 1), (100, 0)]}
    if kind in ("memory", "unrelated"):
        with pytest.raises(type(sentinel)) as caught:
            invoke(fixture, **kwargs)
        assert caught.value is sentinel
    else:
        assert_code("illumination_solver_failure", invoke, fixture, **kwargs)
    assert calls, "controlled public Fourier boundary must actually execute"


def test_inherited_phase_failure_and_error_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    selector()
    error_type: Any = getattr(simrecon, "SimreconError", None)
    sentinel = error_type(code="phase_solver_failure", message="controlled existing domain error")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    monkeypatch.setattr(np.linalg, "svd", fail)
    monkeypatch.setattr(np.linalg, "lstsq", fail)
    error = assert_code("phase_solver_failure", invoke)
    assert error is sentinel


def test_public_scan_compatibility_is_supplemental_only() -> None:
    selector()
    fixture = landscape()
    carriers = [(0, 1), (0, -1), (100, 0), (0, 1)]
    result = invoke(fixture, candidate_carriers_bins_yx=carriers)
    scan: Any = getattr(simrecon, "scan_carriers", None)
    scanned = scan(
        fixture.images,
        otf=fixture.calibration(simrecon),
        phase_steps_rad=fixture.steps,
        candidate_carriers_bins_yx=carriers,
    )
    for actual, previous in zip(result.candidates, scanned, strict=True):
        assert actual.carrier_bins_yx == previous.carrier_bins_yx
        assert actual.failure_code == previous.failure_code
        if actual.estimate is not None:
            assert previous.estimate is not None
            assert abs(actual.estimate.modulation - previous.estimate.modulation) < 2e-10
            assert (
                abs(actual.estimate.relative_residual - previous.estimate.relative_residual) < 2e-10
            )
            np.testing.assert_allclose(
                np.exp(1j * actual.estimate.phases_rad),
                np.exp(1j * previous.estimate.phases_rad),
                atol=2e-10,
                rtol=0,
            )


def test_one_pair_can_select_an_unsupported_physical_interpretation() -> None:
    """An extreme closed-grid pair fits exactly, with no physical truth claim."""
    steps = np.array([0.0, 0.8, 2.2, 3.7, 5.5])
    x = np.arange(5)
    dc = 3 + 0.3 * np.cos(-4 * np.pi * x / 5 + 0.2)
    c1 = 0.1 * np.exp(4j * np.pi * x / 5 + 0.7j)
    images = np.array([dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p)) for p in steps])[
        :, None, :
    ]
    fixture = SelectionFixture(images, steps, np.ones((1, 5), dtype=complex))
    result = invoke(
        fixture,
        candidate_carriers_bins_yx=[(0, 4)],
        max_relative_residual=1e-8,
        modulation_bounds=(1.2, 1.4),
    )
    estimate = result.candidates[0].estimate
    # q=-2, q+k=+2 is the sole pair. x=.15*exp(.2i), y=.1*exp(.7i).
    assert result.eligible_indices == (0,)
    assert estimate.overlap_count == 1
    assert estimate.relative_residual < 2e-11
    assert (
        abs(
            0.5 * estimate.modulation * np.exp(1j * estimate.phase_offset_rad)
            - (2 / 3) * np.exp(0.5j)
        )
        < 2e-10
    )
    assert (
        invoke(fixture, candidate_carriers_bins_yx=[(0, 4)], min_overlap_count=2).failure_code
        == "no_acceptable_carrier"
    )
    duplicate = invoke(
        fixture,
        candidate_carriers_bins_yx=[(0, 4), (0, 4)],
        max_relative_residual=1e-8,
        modulation_bounds=(1.2, 1.4),
    )
    assert duplicate.eligible_indices == (0, 1)
    assert duplicate.failure_code == "ambiguous_carrier"


def test_candidate_prevalidation_precedes_numerics(monkeypatch: pytest.MonkeyPatch) -> None:
    selector()
    sentinel = RuntimeError("candidate representation must be completely checked first")

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise sentinel

    for module, names in [
        (np.fft, ("fft", "fft2", "fftn")),
        (scipy.fft, ("fft", "fft2", "fftn")),
        (np.linalg, ("svd", "lstsq")),
    ]:
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    assert_code("invalid_carrier_candidates", invoke, candidate_carriers_bins_yx=[(0, 1), (0, 1.5)])


@pytest.mark.parametrize("kind", ["memory", "unrelated"])
def test_late_public_numeric_failure_with_eligible_prefix(
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inject at the final observed public transform, without fixing call counts.

    This permits shared transforms and different NumPy/SciPy FFT choices. It
    proves whole-call propagation with a known eligible prefix and a late
    reachable operation failure; internal row-evaluation timing stays private.
    """
    selector()
    fixture = landscape()
    carriers = [(0, 1), (0, 0), (0, 2)]
    originals = [
        (module, name, getattr(module, name))
        for module in (np.fft, scipy.fft)
        for name in ("fft", "fft2", "fftn")
    ]
    observed = []

    def recorder(original: Any) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            observed.append(1)
            return original(*args, **kwargs)

        return wrapped

    for module, name, original in originals:
        monkeypatch.setattr(module, name, recorder(original))
    complete = invoke(fixture, candidate_carriers_bins_yx=carriers, max_relative_residual=0.1)
    assert complete.eligible_indices == (0,)
    assert len(complete.candidates) == 3
    total = len(observed)
    assert total > 0, "the selected public transform boundary must execute"
    sentinel = (
        MemoryError("late public allocation failure")
        if kind == "memory"
        else RuntimeError("late unrelated public numerical exception")
    )
    replay = []

    def injector(original: Any) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            replay.append(1)
            if len(replay) == total:
                raise sentinel
            return original(*args, **kwargs)

        return wrapped

    for module, name, original in originals:
        monkeypatch.setattr(module, name, injector(original))
    images_before = fixture.images.copy()
    with pytest.raises(type(sentinel)) as caught:
        invoke(fixture, candidate_carriers_bins_yx=carriers, max_relative_residual=0.1)
    assert caught.value is sentinel
    assert len(replay) == total
    np.testing.assert_array_equal(fixture.images, images_before)
