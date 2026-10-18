"""Public tests of explicit policy over complete independent carrier fits.

Policy comparisons use returned represented diagnostics only as observations.
Independent finite sums/matrices separately check numerical objective claims.
"""

import inspect
import warnings
from dataclasses import FrozenInstanceError
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from phase_carrier_selection_fixture import (
    Observation,
    direct_observation,
    independent_fit,
    observe,
    phase_blind_observation,
    raw_observation,
)
from simrecon import (
    ObservableVolumePhaseEstimate,
    SimreconError,
    VolumeOrderOtf,
    VolumePhaseCarrierSelection,
    estimate_observable_volume_phases,
    scan_volume_phase_carriers,
    select_volume_phase_carrier,
)

POLICY_ERROR = "invalid_volume_phase_carrier_selection_policy"
ARRAY_FIELDS = (
    "phases_rad",
    "phasors",
    "phase_deviations_rad",
    "specimen_normalized",
    "nuisance_singular_values",
    "phase_singular_values",
    "observable_fourier_mask",
)
ROW_FIELDS = set(ARRAY_FIELDS) | {
    "image_scale",
    "transfer_scale",
    "relative_residual",
    "normalized_residual_rms",
    "normalized_imaginary_rms",
    "calibration_reality_defect",
    "nuisance_rank",
    "phase_rank",
    "phase_design_rank",
    "gradient_inf_norm",
    "termination",
    "nfev",
    "njev",
    "carrier_bins_yx",
    "source",
    "global_ambiguity",
    "observable_dimension",
    "unobservable_dimension",
}


def public_field_names(record: Any) -> set[str]:
    """Observe public noncallable fields without reading private attributes."""
    return {
        name
        for name in dir(record)
        if not name.startswith("_") and not callable(getattr(record, name))
    }


def changed_orders(orders: VolumeOrderOtf, **changes: Any) -> VolumeOrderOtf:
    """Use the documented public record constructor, with selected changed fields."""
    values = {
        name: getattr(orders, name)
        for name in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }
    values.update(changes)
    return VolumeOrderOtf(**values)


def select(case: Observation, *, residual: Any = 1.0, rank: Any = 0, **changes: Any) -> Any:
    """Call the real public boundary with every required keyword explicit."""
    return select_volume_phase_carrier(
        case.images,
        **case.arguments(**changes),
        max_relative_residual=residual,
        min_phase_rank=rank,
    )


def assert_policy(result: Any, residual: float, rank: int) -> None:
    """Independently apply the exact specified relation, without numerical claims."""
    expected = tuple(
        i
        for i, row in enumerate(result.candidates)
        if row.termination == "stationary"
        and row.relative_residual <= residual
        and row.phase_rank >= rank
    )
    assert type(result.eligible_indices) is tuple
    assert all(type(i) is int for i in result.eligible_indices)
    assert result.eligible_indices == expected
    assert result.selected_index == (expected[0] if len(expected) == 1 else None)
    if result.selected_index is not None:
        assert type(result.selected_index) is int
    failure = (
        None
        if len(expected) == 1
        else "no_acceptable_volume_phase_carrier"
        if not expected
        else "ambiguous_volume_phase_carrier"
    )
    assert result.failure_code == failure


def assert_rows_compatible(actual: Any, expected: Any) -> None:
    """Supplemental public composition check; not an independent accuracy oracle."""
    assert type(actual) is ObservableVolumePhaseEstimate
    assert public_field_names(actual) == ROW_FIELDS
    for name in ROW_FIELDS:
        a, b = getattr(actual, name), getattr(expected, name)
        if name in ARRAY_FIELDS:
            np.testing.assert_allclose(a, b, atol=2e-8, rtol=2e-8)
        elif isinstance(a, float):
            assert a == pytest.approx(b, abs=2e-8, rel=2e-8)
        elif name not in ("nfev", "njev"):
            assert a == b
    # Counts are truthful per-row work, not a promise of identical organization.
    assert type(actual.nfev) is int and actual.nfev >= 0
    assert type(actual.njev) is int and actual.njev >= 0


def test_required_signature_and_frozen_four_field_result() -> None:
    signature = inspect.signature(select_volume_phase_carrier)
    keywords = set(direct_observation().arguments()) | {"max_relative_residual", "min_phase_rank"}
    assert set(signature.parameters) == {"images", *keywords}
    assert signature.parameters["images"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    for name in keywords:
        assert signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        assert signature.parameters[name].default is inspect.Parameter.empty
    case = phase_blind_observation()
    result = select(case, candidate_carriers_yx=[(0, 0)])
    assert type(result) is VolumePhaseCarrierSelection
    assert public_field_names(result) == {
        "candidates",
        "eligible_indices",
        "selected_index",
        "failure_code",
    }
    assert type(result.candidates) is tuple and len(result.candidates) == 1
    for name in ("candidates", "eligible_indices", "selected_index", "failure_code"):
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            setattr(result, name, None)
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            delattr(result, name)
    # Construction is a value record, with no new direct-construction validation.
    raw = VolumePhaseCarrierSelection(
        candidates=(), eligible_indices=(9,), selected_index=9, failure_code="caller value"
    )
    assert raw.selected_index == 9


@pytest.mark.parametrize(
    "missing",
    [
        "order_otf",
        "candidate_carriers_yx",
        "initial_phases_rad",
        "max_nfev",
        "gradient_tolerance",
        "step_tolerance",
        "source",
        "max_relative_residual",
        "min_phase_rank",
    ],
)
def test_every_keyword_is_required(missing: str) -> None:
    case = phase_blind_observation()
    arguments = dict(case.arguments(), max_relative_residual=1.0, min_phase_rank=0)
    del arguments[missing]
    with pytest.raises(TypeError):
        select_volume_phase_carrier(case.images, **arguments)


def test_argument_binding_errors_remain_python_type_errors() -> None:
    case = phase_blind_observation()
    with pytest.raises(TypeError):
        select_volume_phase_carrier(case.images, case.orders)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        select(case, unexpected=True)


INVALID_RESIDUALS = [
    True,
    np.bool_(False),
    -1,
    np.float32(-0.01),
    float("nan"),
    float("inf"),
    -float("inf"),
    complex(1, 0),
    "1",
    np.array(1.0),
    np.array([1.0]),
    Fraction(1, 2),
    Decimal(".5"),
    None,
    10**400,
    np.longdouble("nan"),
]


@pytest.mark.parametrize(
    "value", INVALID_RESIDUALS, ids=[f"residual-{i}" for i in range(len(INVALID_RESIDUALS))]
)
@pytest.mark.parametrize("unavailable", [False, True])
def test_invalid_residual_policy_even_for_unavailable_data(value: Any, unavailable: bool) -> None:
    with pytest.raises(SimreconError) as caught:
        select(phase_blind_observation(unavailable=unavailable), residual=value)
    assert caught.value.code == POLICY_ERROR


INVALID_RANKS = [
    True,
    np.bool_(False),
    -1,
    np.int64(-1),
    0.0,
    np.float64(1),
    float("nan"),
    complex(1, 0),
    "0",
    np.array(0),
    np.array([0]),
    Fraction(0),
    Decimal(0),
    None,
]


@pytest.mark.parametrize(
    "value", INVALID_RANKS, ids=[f"rank-{i}" for i in range(len(INVALID_RANKS))]
)
@pytest.mark.parametrize("unavailable", [False, True])
def test_invalid_rank_policy_even_for_unavailable_data(value: Any, unavailable: bool) -> None:
    with pytest.raises(SimreconError) as caught:
        select(phase_blind_observation(unavailable=unavailable), rank=value)
    assert caught.value.code == POLICY_ERROR


@pytest.mark.parametrize(
    "value",
    [
        0,
        -0.0,
        np.float16(0),
        np.float32(-0.0),
        np.float64(0),
        np.int64(0),
        np.uint64(0),
        1,
        np.float32(1),
        np.finfo(float).max,
        np.uint64(2**64 - 1),
    ],
)
def test_permitted_residual_scalar_representations(value: Any) -> None:
    case = phase_blind_observation()
    case.images[:] = 0
    result = select(case, residual=value, candidate_carriers_yx=[(0, 0)])
    assert_policy(result, float(value), 0)
    assert result.selected_index == 0
    assert result.candidates[0].relative_residual == 0
    assert result.candidates[0].phase_rank == 0


@pytest.mark.parametrize("value", [0, np.int8(0), np.uint64(0), 2**64, 10**400])
def test_exact_zero_and_huge_rank_limits_are_valid(value: Any) -> None:
    result = select(phase_blind_observation(), rank=value, candidate_carriers_yx=[(0, 0)])
    assert_policy(result, 1.0, int(value))
    assert result.selected_index == (0 if value == 0 else None)


def test_available_wider_float_source_and_conversion_boundaries() -> None:
    # No skip or invented wider platform state. These cases exist only when the
    # public NumPy scalar representation genuinely has a wider exponent range.
    if np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp:
        case = phase_blind_observation()
        case.images[:] = 0
        tiny = np.longdouble("1e-400")
        assert np.isfinite(tiny) and tiny > 0 and float(tiny) == 0
        for value in (tiny, -tiny):
            with np.errstate(all="raise"):
                result = select(case, residual=value, candidate_carriers_yx=[(0, 0)])
            assert result.selected_index == 0
        too_large = np.longdouble("1e400")
        assert np.isfinite(too_large)
        with pytest.raises(SimreconError) as caught:
            select(case, residual=too_large)
        assert caught.value.code == POLICY_ERROR
    else:
        assert np.finfo(np.longdouble).maxexp == np.finfo(np.float64).maxexp


@pytest.mark.parametrize("kind", [TypeError, ValueError, OverflowError, MemoryError, RuntimeError])
def test_residual_conversion_exception_boundary(kind: type[Exception]) -> None:
    class ConversionFailure(float):
        def __float__(self) -> float:
            raise kind("public scalar conversion failure")

    expected = SimreconError if kind in (TypeError, ValueError, OverflowError) else kind
    with pytest.raises(expected) as caught:
        select(phase_blind_observation(), residual=ConversionFailure(1.0))
    if expected is SimreconError:
        assert caught.value.code == POLICY_ERROR  # type: ignore[attr-defined]


@pytest.mark.parametrize("kind", [TypeError, ValueError, OverflowError, MemoryError, RuntimeError])
@pytest.mark.parametrize("exact_rank", [0, 10**400], ids=["zero", "huge"])
def test_rank_extraction_exception_boundary_or_legitimate_bypass(
    kind: type[Exception], exact_rank: int
) -> None:
    encountered: list[str] = []
    marker = kind("test-owned rank extraction failure")

    class ObservedRank(int):
        def __int__(self) -> int:
            encountered.append("__int__")
            raise marker

        def __index__(self) -> int:
            encountered.append("__index__")
            raise marker

    try:
        result = select(
            phase_blind_observation(),
            rank=ObservedRank(exact_rank),
            candidate_carriers_yx=[(0, 0)],
        )
    except SimreconError as error:
        assert encountered
        assert kind in (TypeError, ValueError, OverflowError)
        assert error.code == POLICY_ERROR
    except (MemoryError, RuntimeError) as error:
        assert encountered
        assert error is marker
    else:
        # Exact extraction may legitimately bypass an optional subtype hook.
        # Success after actually encountering its exception would swallow it.
        assert not encountered
        assert_policy(result, 1.0, exact_rank)
        assert result.eligible_indices == ((0,) if exact_rank == 0 else ())
        assert result.selected_index == (0 if exact_rank == 0 else None)


def test_policy_is_validated_before_numerical_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("numerical dependency ran before policy validation")

    monkeypatch.setattr(np.fft, "fftn", unexpected)
    for changes in ({"residual": -1}, {"rank": 1.0}):
        with pytest.raises(SimreconError) as caught:
            select(direct_observation(), **changes)
        assert caught.value.code == POLICY_ERROR


def test_inclusive_residual_and_rank_conjunction_exact_endpoints() -> None:
    case = phase_blind_observation()
    # Phase-independent alternating data have mean zero and relative residual 1
    # exactly. Their projected phase rank is zero, regardless of command rank.
    for threshold, rank, expected in [
        (1.0, 0, 0),
        (np.nextafter(1.0, 0.0), 0, None),
        (1.0, 1, None),
        (np.nextafter(1.0, 0.0), 1, None),
        (np.nextafter(1.0, 2.0), 0, 0),
    ]:
        result = select(case, residual=threshold, rank=rank, candidate_carriers_yx=[(0, 0)])
        assert result.candidates[0].termination == "stationary"
        assert result.candidates[0].relative_residual == 1.0
        assert result.candidates[0].phase_rank == 0
        assert result.selected_index == expected
        assert_policy(result, threshold, rank)


def test_positive_reported_rank_endpoint_without_a_hidden_information_cutoff() -> None:
    case = direct_observation()
    baseline = select(case, candidate_carriers_yx=[case.carrier])
    row = baseline.candidates[0]
    assert row.termination == "stationary" and row.phase_rank > 0
    # These are observations for an exact policy relation, not rank accuracy truth.
    for limit, rank in [
        (row.relative_residual, row.phase_rank),
        (np.nextafter(row.relative_residual, 0.0), row.phase_rank),
        (row.relative_residual, row.phase_rank + 1),
    ]:
        result = select(case, residual=limit, rank=rank, candidate_carriers_yx=[case.carrier])
        assert_policy(result, limit, rank)
    inclusive = select(
        case, residual=1.0, rank=row.phase_rank, candidate_carriers_yx=[case.carrier]
    )
    assert inclusive.selected_index == 0


@pytest.mark.parametrize("rank", [np.int64(1), np.uint64(1)])
def test_numpy_positive_rank_and_stationary_zero_observation_positives(rank: Any) -> None:
    case = direct_observation()
    informative = select(case, rank=rank, candidate_carriers_yx=[case.carrier])
    assert informative.selected_index == 0
    case.images[:] = 0
    zero = select(case, residual=-0.0, rank=0, max_nfev=1, candidate_carriers_yx=[case.carrier])
    row = zero.candidates[0]
    assert row.termination == "stationary"
    assert row.relative_residual == 0 and row.phase_rank == 0
    assert zero.selected_index == 0


@pytest.mark.parametrize(
    "kind", ["evaluation_limit", "stagnated", "no_observable_specimen", "nuisance_rank_deficient"]
)
def test_real_nonstationary_and_unavailable_rows_never_pass(kind: str) -> None:
    changes: dict[str, Any] = {}
    if kind == "evaluation_limit":
        case = direct_observation()
        changes.update(max_nfev=1, gradient_tolerance=1e-12)
    elif kind == "stagnated":
        case = direct_observation()
        changes.update(step_tolerance=0.9, gradient_tolerance=1e-14)
    else:
        case = phase_blind_observation(
            unavailable=kind == "no_observable_specimen",
            deficient=kind == "nuisance_rank_deficient",
        )
    result = select(case, residual=np.finfo(float).max, rank=0, **changes)
    assert all(row.termination == kind for row in result.candidates)
    assert result.eligible_indices == ()
    assert_policy(result, np.finfo(float).max, 0)


@pytest.mark.parametrize(
    "factory", [direct_observation, raw_observation], ids=["fourier", "raw-spatial"]
)
def test_complete_real_fits_independent_objective_and_policy(factory: Any) -> None:
    case = factory()
    result = select(case, residual=0.02, rank=1)
    assert len(result.candidates) == 3
    assert [r.carrier_bins_yx for r in result.candidates] == [case.carrier, (1, 0), (0, 4)]
    assert result.eligible_indices == (0, 2)
    assert result.failure_code == "ambiguous_volume_phase_carrier"
    assert_policy(result, 0.02, 1)
    for row in result.candidates:
        # Every informative real fit evaluates its residual and analytic
        # Jacobian. Their exact counts may vary with valid organization.
        assert type(row.nfev) is int and row.nfev > 0
        assert type(row.njev) is int and row.njev > 0
        expected = independent_fit(case, row)
        assert expected["condition"] <= 10
        assert expected["singular"][-1] >= 1 / 16
        assert expected["allowance"] <= 1 / 1024
        budget = expected["allowance"]
        assert row.observable_dimension == case.specimen.size
        assert row.nuisance_rank == expected["rank"] == case.specimen.size
        assert np.linalg.norm(row.specimen_normalized - expected["specimen"]) <= budget
        np.testing.assert_allclose(
            row.nuisance_singular_values, expected["singular"], atol=budget, rtol=0
        )
        assert abs(row.relative_residual - expected["relative"]) <= budget
        assert abs(row.normalized_residual_rms - expected["rms"]) <= budget
        assert abs(row.normalized_imaginary_rms - expected["imaginary"]) <= budget
        assert row.image_scale == expected["image_scale"]
        assert row.transfer_scale == expected["transfer_scale"]
        assert row.source == case.label and row.global_ambiguity == "unassessed"
    # Strong all-order model discrimination: true/aliased rows fit far better
    # than the off-model control. This is an objective comparison, not a claim
    # that stationarity proves physical truth or universal phase accuracy.
    assert result.candidates[0].relative_residual < 1e-6
    assert result.candidates[1].relative_residual > 0.05


def test_sole_none_multiple_order_and_no_residual_ranking() -> None:
    case = direct_observation()
    sole = select(case, residual=0.02, rank=1, candidate_carriers_yx=[(1, 0), case.carrier])
    assert sole.eligible_indices == (1,) and sole.selected_index == 1
    assert sole.failure_code is None
    none = select(case, residual=0.02, rank=10**400)
    assert none.eligible_indices == () and none.selected_index is None
    assert none.failure_code == "no_acceptable_volume_phase_carrier"
    # A loose criterion admits every genuinely stationary row; it never picks
    # the smallest residual among them. Nonstationary controls stay ineligible.
    multiple = select(case, residual=1.0, rank=0)
    assert_policy(multiple, 1.0, 0)
    assert multiple.selected_index is None


@pytest.mark.parametrize("sparse", [False, True], ids=["unequal-residual", "unequal-rank"])
def test_unequal_eligible_rows_remain_ambiguous_without_ranking(sparse: bool) -> None:
    case = direct_observation()
    if sparse:
        values = np.zeros_like(case.orders.values)
        values[:, 0, 1, 1] = [1, 0.1 + 0.03j, 0.05 - 0.02j]
        case.orders = changed_orders(case.orders, values=values)
        # Independently regenerate observations from the supplied transfer.
        # Hidden specimen/phases remain evaluator-only, outside selection inputs.
        case.images = observe(case.specimen, values, case.truth, case.carrier)
    carriers = [(0, 0), (0, 1)] if sparse else [(1, 0), (0, 1)]
    result = select(
        case,
        residual=1.0,
        rank=1,
        candidate_carriers_yx=carriers,
        gradient_tolerance=0.9,
        **({"max_nfev": 1} if sparse else {}),
    )
    assert len(result.candidates) == 2
    assert [row.carrier_bins_yx for row in result.candidates] == carriers
    # Reachability guards distinguish forbidden ranking from equal-value ties.
    # Returned values establish policy inputs, not diagnostic accuracy truth.
    assert all(row.termination == "stationary" for row in result.candidates)
    assert all(row.relative_residual <= 1.0 and row.phase_rank >= 1 for row in result.candidates)
    assert result.candidates[0].relative_residual != result.candidates[1].relative_residual
    if sparse:
        assert result.candidates[0].phase_rank != result.candidates[1].phase_rank
    assert_policy(result, 1.0, 1)
    assert result.eligible_indices == (0, 1)
    assert result.selected_index is None
    assert result.failure_code == "ambiguous_volume_phase_carrier"


@pytest.mark.parametrize(
    "carriers",
    [[(0, 1), (0, 1)], [(0, 4), (0, 1)], [(0, 1 + 3 * 10**400), (0, 1)]],
    ids=["duplicate", "period-alias", "huge-alias"],
)
def test_duplicate_and_period_alias_rows_count_separately(carriers: Any) -> None:
    result = select(direct_observation(), residual=0.02, rank=1, candidate_carriers_yx=carriers)
    assert result.eligible_indices == (0, 1)
    assert result.failure_code == "ambiguous_volume_phase_carrier"
    assert [r.carrier_bins_yx for r in result.candidates] == carriers
    assert result.candidates[0] is not result.candidates[1]


def test_row_fields_and_independent_same_command_starts_match_public_prerequisites() -> None:
    case = direct_observation()
    result = select(case, residual=0.02, rank=1)
    scanned = scan_volume_phase_carriers(case.images, **case.arguments())
    for row, scan in zip(result.candidates, scanned, strict=True):
        assert_rows_compatible(row, scan)
        arguments = case.arguments()
        del arguments["candidate_carriers_yx"]
        isolated = estimate_observable_volume_phases(
            case.images, **arguments, carrier_bins_yx=row.carrier_bins_yx
        )
        assert_rows_compatible(row, isolated)
    reversed_result = select(case, candidate_carriers_yx=[(0, 4), (1, 0), case.carrier])
    for row, reversed_row in zip(
        result.candidates, reversed(reversed_result.candidates), strict=True
    ):
        assert_rows_compatible(row, reversed_row)


@pytest.mark.parametrize(
    "carriers,eligible",
    [
        ([(0, 1), (0, 0)], (1,)),
        ([(0, 0), (0, 1), (0, 0)], (0, 2)),
    ],
)
def test_unavailable_rows_do_not_hide_later_rows(carriers: Any, eligible: tuple[int, ...]) -> None:
    case = direct_observation()
    # Only positive-order DC is observed. Repeated zero commands observe one
    # real coordinate. Carrier zero has r=1 and full nuisance rank; nonzero
    # carrier has a conjugate pair (r=2) but only its real coordinate is seen.
    values = np.zeros_like(case.orders.values)
    values[1, 0, 1, 1] = 1
    case.orders = changed_orders(case.orders, values=values)
    case.images[:] = 0
    case.commands[:] = 0
    result = select(case, rank=0, candidate_carriers_yx=carriers)
    assert len(result.candidates) == len(carriers)
    assert result.eligible_indices == eligible
    assert_policy(result, 1.0, 0)
    for row in result.candidates:
        assert row.termination == (
            "stationary" if row.carrier_bins_yx == (0, 0) else "nuisance_rank_deficient"
        )


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("images", [1], "invalid_volume_phase_estimation_images"),
        ("images", np.full((6, 1, 1, 2), np.nan), "nonfinite_volume_phase_estimation_images"),
        ("initial_phases_rad", [0] * 6, "invalid_volume_phase_estimation_initial_phases"),
        (
            "initial_phases_rad",
            np.full(6, np.inf),
            "nonfinite_volume_phase_estimation_initial_phases",
        ),
        ("max_nfev", 0, "invalid_volume_phase_estimation_controls"),
        ("gradient_tolerance", 0.0, "invalid_volume_phase_estimation_controls"),
        ("step_tolerance", 1.0, "invalid_volume_phase_estimation_controls"),
        ("source", " ", "invalid_otf_source"),
        ("candidate_carriers_yx", [(0, 0), (False, 1)], "invalid_volume_phase_carrier_candidates"),
        (
            "candidate_carriers_yx",
            np.array([[0.0, 0.0]]),
            "invalid_volume_phase_carrier_candidates",
        ),
        ("candidate_carriers_yx", [], "invalid_volume_phase_carrier_candidates"),
    ],
)
def test_inherited_validation_before_unavailable_return(field: str, value: Any, code: str) -> None:
    case = phase_blind_observation(unavailable=True)
    changes = {field: value}
    if field == "images":
        case.images = value
        changes = {}
    with pytest.raises(SimreconError) as caught:
        select(case, **changes)
    assert caught.value.code == code


@pytest.mark.parametrize("field", ["values", "fx_per_um", "origin_zyx", "voxel_size_um", "source"])
def test_entire_transfer_validated_even_when_observations_are_zero(field: str) -> None:
    case = phase_blind_observation(unavailable=True)
    values: dict[str, Any] = dict(
        values=case.orders.values.copy(),
        fx_per_um=np.array([-0.5, np.nan]),
        origin_zyx=(0, 0, 2),
        voxel_size_um=(1.0, 0.0, 1.0),
        source=" ",
    )
    values["values"][2, 0, 0, 1] = np.nan
    case.orders = changed_orders(case.orders, **{field: values[field]})
    case.images[:] = 0
    with pytest.raises(SimreconError) as caught:
        select(case)
    assert caught.value.code == "invalid_volume_phase_estimation_otf"


@pytest.mark.parametrize(
    "exception,code",
    [
        (FloatingPointError, "volume_phase_estimation_transform_failure"),
        (OverflowError, "volume_phase_estimation_transform_failure"),
        (RuntimeWarning, "volume_phase_estimation_transform_failure"),
        (MemoryError, None),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
    ],
)
def test_public_transform_failure_translation_and_propagation(
    monkeypatch: pytest.MonkeyPatch, exception: type[Exception], code: str | None
) -> None:
    case = direct_observation()
    marker = exception("public FFT failure")

    def fail(*args: Any, **kwargs: Any) -> Any:
        if exception is RuntimeWarning:
            warnings.warn("public FFT arithmetic failure", RuntimeWarning, stacklevel=2)
            raise AssertionError("arithmetic warning was swallowed")
        raise marker

    monkeypatch.setattr(np.fft, "fftn", fail)
    with pytest.raises(SimreconError if code else exception) as caught:
        select(case)
    if code:
        assert caught.value.code == code  # type: ignore[attr-defined]
    else:
        assert caught.value is marker


@pytest.mark.parametrize(
    "exception,code",
    [
        (np.linalg.LinAlgError, "volume_phase_estimation_solver_failure"),
        (MemoryError, None),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
    ],
)
@pytest.mark.parametrize("rank", [1, 10**400], ids=["early-eligible", "impossible-rank-policy"])
def test_late_real_solver_failure_aborts_after_an_eligible_candidate(
    monkeypatch: pytest.MonkeyPatch, exception: type[Exception], code: str | None, rank: int
) -> None:
    case = direct_observation()
    real_svd = np.linalg.svd
    calls = 0
    marker = exception("later genuine SVD failed")
    inputs = [case.images, case.commands, case.orders.values]
    snapshots = [array.copy() for array in inputs]

    def measured(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return real_svd(*args, **kwargs)

    monkeypatch.setattr(np.linalg, "svd", measured)
    baseline = select(case, residual=0.02, rank=1, candidate_carriers_yx=[case.carrier])
    assert baseline.selected_index == 0
    one_candidate_calls = calls
    assert one_candidate_calls > 0
    calls = 0

    def fail_later(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls > one_candidate_calls:
            raise marker
        return real_svd(*args, **kwargs)

    # The injection follows the actually observed work for one complete fit.
    # No fixed internal call count or fabricated finite SVD result is imposed.
    # Shared preparation may change exactly where in the second call it fails;
    # the guarantee proved is whole-call failure after genuine earlier work.
    monkeypatch.setattr(np.linalg, "svd", fail_later)
    with pytest.raises(SimreconError if code else exception) as caught:
        select(case, residual=0.02, rank=rank, candidate_carriers_yx=[case.carrier, case.carrier])
    assert calls == one_candidate_calls + 1
    if code:
        assert caught.value.code == code  # type: ignore[attr-defined]
    else:
        assert caught.value is marker
    for array, snapshot in zip(inputs, snapshots, strict=True):
        np.testing.assert_array_equal(array, snapshot)


def test_independent_owned_arrays_across_rows_fields_calls_and_inputs() -> None:
    case = direct_observation()
    result = select(case, candidate_carriers_yx=[case.carrier, case.carrier, (0, 4)])
    other = select(case, candidate_carriers_yx=[case.carrier])
    inputs = [
        case.images,
        case.commands,
        case.orders.values,
        case.orders.fz_per_um,
        case.orders.fy_per_um,
        case.orders.fx_per_um,
    ]
    arrays = [
        getattr(row, name)
        for row in (*result.candidates, *other.candidates)
        for name in ARRAY_FIELDS
    ]
    for i, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        assert array.dtype.isnative
        assert all(not np.shares_memory(array, source) for source in inputs)
        assert all(not np.shares_memory(array, earlier) for earlier in arrays[:i])
    before = [a.copy() for a in arrays[1:]]
    arrays[0][:] = 99
    for array, snapshot in zip(arrays[1:], before, strict=True):
        np.testing.assert_array_equal(array, snapshot)
    for row in result.candidates:
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            row.source = "changed"


@pytest.mark.parametrize("failure", [False, True])
def test_inputs_warning_filters_and_numpy_error_policy_preserved(failure: bool) -> None:
    case = direct_observation()
    # Storage alternatives are real caller inputs, including endian/strides/RO.
    case.images = np.asfortranarray(case.images).astype(">f8")
    case.commands = np.repeat(case.commands, 2)[::2]
    case.images.flags.writeable = False
    case.commands.flags.writeable = False
    candidates = np.array([[0, 1], [0, 4]], dtype=">i8")[:, ::-1][:, ::-1]
    candidates.flags.writeable = False
    arrays = [
        case.images,
        case.commands,
        case.orders.values,
        case.orders.fz_per_um,
        case.orders.fy_per_um,
        case.orders.fx_per_um,
        candidates,
    ]
    snapshots = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    filters = list(warnings.filters)
    with np.errstate(all="raise"):
        error_policy = np.geterr().copy()
        if failure:
            with pytest.raises(SimreconError) as caught:
                select(case, rank=-1, candidate_carriers_yx=candidates)
            assert caught.value.code == POLICY_ERROR
        else:
            result = select(case, candidate_carriers_yx=candidates)
            assert_policy(result, 1.0, 0)
        assert np.geterr() == error_policy
        assert warnings.filters == filters
    for array, expected in zip(arrays, snapshots, strict=True):
        assert (
            array.tobytes(),
            array.dtype,
            array.shape,
            array.strides,
            array.flags.writeable,
        ) == expected


def test_unrelated_dependency_warning_remains_observable(monkeypatch: pytest.MonkeyPatch) -> None:
    real_svd = np.linalg.svd

    def warning_solver(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("public dependency advisory", UserWarning, stacklevel=2)
        return real_svd(*args, **kwargs)

    monkeypatch.setattr(np.linalg, "svd", warning_solver)
    with pytest.warns(UserWarning, match="public dependency advisory"):
        result = select(direct_observation(), candidate_carriers_yx=[(0, 1)])
    assert_policy(result, 1.0, 0)
