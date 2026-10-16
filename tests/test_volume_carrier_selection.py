"""Blind public-contract tests for caller-policy volume carrier selection.

Numerical truth comes from the independent stored-input observer. The Fraction
policy observer proves only the relation to genuinely returned diagnostics.
"""

from __future__ import annotations

import inspect
import math
import warnings
from decimal import Decimal
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from simrecon import (
    EmpiricalVolumeResponse,
    SimreconError,
    VolumeCarrierCandidate,
    VolumeCarrierSelection,
    scan_volume_carriers,
    select_volume_carrier,
)
from volume_carrier_selection_fixture import (
    case,
    independent_rows,
    matched_case,
    phase_matrix,
    simple_case,
    singleton_gain_case,
)

POLICY = {
    "max_relative_residual": 2.0,
    "min_overlap_count": 1,
    "gain_magnitude_bounds": (0.0, 100.0),
}
FIELDS = ("candidates", "eligible_indices", "selected_index", "failure_code")
ROW_FIELDS = (
    "gain",
    "relative_residual",
    "coherence",
    "overlap_count",
    "status",
    "order",
    "carrier_bins_yx",
    "source",
)


def select(images: Any, args: dict[str, Any], **policy: Any) -> Any:
    return select_volume_carrier(images, **args, **(POLICY | policy))


def exact_indices(rows: Any, policy: dict[str, Any]) -> tuple[int, ...]:
    """Exact real squared-component policy, no rounded hypot/square products."""
    lower, upper = map(lambda v: Fraction(float(v)), policy["gain_magnitude_bounds"])
    return tuple(
        i
        for i, row in enumerate(rows)
        if row.gain is not None
        and row.relative_residual <= float(policy["max_relative_residual"])
        and row.overlap_count >= int(policy["min_overlap_count"])
        and lower**2 <= Fraction(row.gain.real) ** 2 + Fraction(row.gain.imag) ** 2 <= upper**2
    )


def assert_selection(result: Any, policy: dict[str, Any]) -> None:
    assert isinstance(result, VolumeCarrierSelection)
    assert type(result.candidates) is tuple and result.candidates
    assert type(result.eligible_indices) is tuple
    assert all(type(i) is int for i in result.eligible_indices)
    expected = exact_indices(result.candidates, policy)
    assert result.eligible_indices == expected
    if len(expected) == 1:
        assert type(result.selected_index) is int
        assert result.selected_index == expected[0]
        assert result.failure_code is None
    else:
        assert result.selected_index is None
        assert result.failure_code == (
            "no_acceptable_volume_carrier" if not expected else "ambiguous_volume_carrier"
        )


def row_tuple(row: Any) -> tuple[Any, ...]:
    return tuple(getattr(row, field) for field in ROW_FIELDS)


@pytest.mark.parametrize("order", [1, 2])
def test_stored_input_numerical_truth_and_fixed_gauge(order: int) -> None:
    images, args = case(order)
    assert np.linalg.cond(phase_matrix(args["phase_steps_rad"])) < 2
    truth = independent_rows(images, args)
    result = select(images, args)
    assert_selection(result, POLICY)
    assert result.eligible_indices == (0, 1, 2)
    for row, expected, carrier in zip(
        result.candidates, truth, args["candidate_carriers_yx"], strict=True
    ):
        assert isinstance(row, VolumeCarrierCandidate)
        assert row.status == "fitted"
        assert type(row.gain) is complex
        assert type(row.relative_residual) is float and type(row.coherence) is float
        assert type(row.overlap_count) is int and type(row.order) is int
        assert type(row.carrier_bins_yx) is tuple
        assert all(type(v) is int for v in row.carrier_bins_yx)
        assert row.carrier_bins_yx == carrier and row.order == order
        assert row.source == args["source"]
        assert row.overlap_count == expected["overlap_count"]
        # 1e-60 dwarfs Decimal/truncation error; each rounded budget gets margin.
        for field, budget in (
            ("gain", "gain_budget"),
            ("relative_residual", "residual_budget"),
            ("coherence", "coherence_budget"),
        ):
            assert abs(getattr(row, field) - expected[field]) <= expected[budget] * 1.000001 + 1e-60
    if order == 2:
        assert abs(result.candidates[1].gain) > 4  # permissive gains above one


def test_required_keyword_binding_and_frozen_four_field_record() -> None:
    images, args = simple_case()
    kwargs = args | POLICY
    for key in kwargs:
        without = {k: v for k, v in kwargs.items() if k != key}
        with pytest.raises(TypeError):
            select_volume_carrier(images, **without)
    with pytest.raises(TypeError):
        select_volume_carrier(
            images, args["response"], **{k: v for k, v in kwargs.items() if k != "response"}
        )
    with pytest.raises(TypeError):
        select_volume_carrier(images, **kwargs, unexpected=True)
    assert tuple(inspect.signature(VolumeCarrierSelection).parameters) == FIELDS
    result = select(images, args)
    for field in FIELDS:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, field, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, field)
    row = result.candidates[0]
    for field in ROW_FIELDS:
        with pytest.raises((AttributeError, TypeError)):
            setattr(row, field, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(row, field)
    # Direct record construction is deliberately not a validation boundary.
    manual = VolumeCarrierSelection(
        candidates=(), eligible_indices=(99,), selected_index=-1, failure_code="opaque"
    )
    assert manual.selected_index == -1


@pytest.mark.parametrize("position", [0, 1, 2])
def test_sole_acceptance_at_any_position_and_complete_unavailable_rows(position: int) -> None:
    images, args = simple_case()
    huge = 10**400
    carriers = [(huge, -huge), (-huge, huge)]
    carriers.insert(position, (0, 0))
    args["candidate_carriers_yx"] = carriers
    result = select(images, args)
    assert_selection(result, POLICY)
    assert result.selected_index == position
    assert len(result.candidates) == 3
    for i, row in enumerate(result.candidates):
        assert row.carrier_bins_yx == carriers[i]
        if i != position:
            assert row.status == "no_overlap" and row.overlap_count == 0
            assert (row.gain, row.relative_residual, row.coherence) == (None, None, None)


def test_no_match_ambiguity_duplicates_and_each_gate_excludes() -> None:
    images, args = case(2)
    # Independent numerical truth above separates these gains/overlaps widely.
    for policy, expected in [
        ({"max_relative_residual": 0.1}, ()),
        ({"min_overlap_count": 25}, ()),
        ({"gain_magnitude_bounds": (10.0, 20.0)}, ()),
        ({"gain_magnitude_bounds": (0.0, 0.1)}, ()),
        ({"gain_magnitude_bounds": (1.0, 10.0)}, (1,)),
        ({"min_overlap_count": 24}, (0,)),
        ({"max_relative_residual": 0.3}, (0,)),
        ({}, (0, 1, 2)),
    ]:
        merged = POLICY | policy
        result = select(images, args, **policy)
        assert_selection(result, merged)
        assert result.eligible_indices == expected
    args["candidate_carriers_yx"] = [(0, 1), (0, 0), (0, 1), (10**300, 0)]
    result = select(images, args, gain_magnitude_bounds=(1, 10))
    assert result.eligible_indices == (0, 2) and result.failure_code == "ambiguous_volume_carrier"
    assert result.candidates[0] is not result.candidates[2]
    assert row_tuple(result.candidates[0]) == row_tuple(result.candidates[2])
    assert len(result.candidates) == 4 and result.candidates[-1].status == "no_overlap"


def test_exact_arbitrary_integer_minimum_and_all_unavailable() -> None:
    images, args = simple_case()
    for minimum in (2**53 + 1, 2**64 + 1, 2**128 + 1, 10**1000, np.uint64(2**64 - 1)):
        result = select(images, args, min_overlap_count=minimum)
        assert_selection(result, POLICY | {"min_overlap_count": minimum})
        assert result.eligible_indices == ()
    args["candidate_carriers_yx"] = [(10**1000, 0), (0, -(10**1000)), (10**1000, 0)]
    result = select(images, args)
    assert len(result.candidates) == 3
    assert all(row.status == "no_overlap" for row in result.candidates)
    assert_selection(result, POLICY)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("max_relative_residual", v)
        for v in (
            True,
            np.bool_(False),
            -1,
            -0.01,
            float("nan"),
            float("inf"),
            -float("inf"),
            10**1000,
            1j,
            "1",
            np.array(1.0),
            np.array([1.0]),
            Fraction(1, 2),
            Decimal("1"),
            None,
        )
    ]
    + [
        ("min_overlap_count", v)
        for v in (
            True,
            np.bool_(True),
            0,
            -1,
            1.0,
            np.float64(2),
            "1",
            np.array(1),
            Fraction(1),
            Decimal(1),
            None,
        )
    ]
    + [
        ("gain_magnitude_bounds", v)
        for v in (
            (),
            (1,),
            (0, 1, 2),
            {0, 1},
            range(2),
            iter((0, 1)),
            np.array(1),
            np.ones((1, 2)),
            np.ones((2, 1)),
            np.array([0, 1]).view(np.ma.MaskedArray),
            np.array([False, True]),
            np.array(["0", "100"]),
            np.array([0, Decimal("100")], dtype=object),
            (True, 1),
            (0, np.bool_(True)),
            (0j, 1),
            (0, "1"),
            (np.array(0), 1),
            (Fraction(0), 1),
            (0, Decimal(1)),
            (-1, 2),
            (2, 1),
            (0, float("inf")),
            (float("nan"), 1),
            (0, 10**1000),
        )
    ],
)
def test_rejected_policy_before_any_numerical_scan(field: str, bad: Any, monkeypatch: Any) -> None:
    images, args = simple_case()
    before = (
        images.tobytes(),
        args["phase_steps_rad"].tobytes(),
        args["response"].values.tobytes(),
    )

    def forbidden(*a: Any, **k: Any) -> Any:
        pytest.fail("invalid policy entered a public numerical dependency")

    monkeypatch.setattr(np.linalg, "lstsq", forbidden)
    monkeypatch.setattr(np.linalg, "svd", forbidden)
    monkeypatch.setattr(np.fft, "fftn", forbidden)
    with pytest.raises(SimreconError) as caught:
        select(images, args, **{field: bad})
    assert caught.value.code == "invalid_volume_carrier_selection_policy"
    assert (
        images.tobytes(),
        args["phase_steps_rad"].tobytes(),
        args["response"].values.tobytes(),
    ) == before


@pytest.mark.parametrize(
    "residual",
    [
        0,
        -0.0,
        np.float16(2),
        np.float32(2),
        np.float64(2),
        np.int64(2),
        np.uint64(2**64 - 1),
        10**200,
    ],
)
def test_valid_residual_scalars_without_upper_cap(residual: Any) -> None:
    images, args = simple_case()
    result = select(images, args, max_relative_residual=residual)
    assert_selection(result, POLICY | {"max_relative_residual": residual})


@pytest.mark.parametrize(
    "bounds",
    [
        [0, 100],
        (np.int8(0), np.float32(100)),
        np.array([0, 100], dtype=">i8"),
        np.array([0, 100], dtype=">f8"),
        np.array([0, 999, 100, 999.0])[::2],
        np.array([0, np.float32(100)], dtype=object),
        (0.0, 0.0),
        (-0.0, -0.0),
        (2, 2),
    ],
)
def test_valid_bound_containers_scalars_equal_and_signed_zero(bounds: Any) -> None:
    saved = bounds.copy() if isinstance(bounds, (list, np.ndarray)) else bounds
    if isinstance(bounds, np.ndarray):
        bounds.flags.writeable = False
    images, args = simple_case()
    result = select(images, args, gain_magnitude_bounds=bounds, min_overlap_count=np.uint16(1))
    assert_selection(result, POLICY | {"gain_magnitude_bounds": bounds})
    if isinstance(bounds, np.ndarray):
        assert np.array_equal(bounds, saved) and not bounds.flags.writeable
    else:
        assert bounds == saved


def test_extended_scalar_source_and_conversion_finiteness() -> None:
    images, args = simple_case()
    # No skips: only exercise distinct wider-range capabilities when available.
    if np.finfo(np.longdouble).max > np.finfo(np.float64).max:
        big = np.longdouble(np.finfo(np.float64).max) * np.longdouble(2)
        assert np.isfinite(big)
        for policy in ({"max_relative_residual": big}, {"gain_magnitude_bounds": (0, big)}):
            with pytest.raises(SimreconError) as caught:
                select(images, args, **policy)
            assert caught.value.code == "invalid_volume_carrier_selection_policy"
    if np.finfo(np.longdouble).smallest_subnormal < np.finfo(np.float64).smallest_subnormal:
        tiny = np.finfo(np.longdouble).smallest_subnormal
        assert tiny > 0 and float(tiny) == 0
        for policy in ({"max_relative_residual": tiny}, {"gain_magnitude_bounds": (tiny, tiny)}):
            assert_selection(select(images, args, **policy), POLICY | policy)
    for value in (np.longdouble("nan"), np.longdouble("inf")):
        with pytest.raises(SimreconError) as caught:
            select(images, args, max_relative_residual=value)
        assert caught.value.code == "invalid_volume_carrier_selection_policy"


@pytest.mark.parametrize(
    "field", ["max_relative_residual", "min_overlap_count", "gain_magnitude_bounds"]
)
@pytest.mark.parametrize(
    "error_type,translated",
    [
        (TypeError, True),
        (ValueError, True),
        (OverflowError, True),
        (MemoryError, False),
        (RuntimeError, False),
    ],
)
def test_policy_conversion_exception_boundaries(
    field: str, error_type: Any, translated: bool
) -> None:
    error = error_type("caller conversion sentinel")
    invoked = False

    class Real(float):
        def __float__(self) -> float:
            nonlocal invoked
            invoked = True
            raise error

    class Integer(int):
        def __int__(self) -> int:
            nonlocal invoked
            invoked = True
            raise error

    value: Any = Integer(1) if field == "min_overlap_count" else Real(1)
    if field == "gain_magnitude_bounds":
        value = (0, value)
    images, args = simple_case()
    try:
        result = select(images, args, **{field: value})
    except Exception as caught:
        assert invoked  # rejection cannot be a blanket scalar-subclass ban
        if translated:
            assert isinstance(caught, SimreconError)
            assert caught.code == "invalid_volume_carrier_selection_policy"
        else:
            assert caught is error
    else:
        # An exact extraction that bypasses these overridable methods is valid.
        # Do not prescribe int() versus index/base-value extraction organization.
        assert not invoked
        base: Any = (0, 1) if field == "gain_magnitude_bounds" else 1
        assert_selection(result, POLICY | {field: base})


def test_inclusive_residual_overlap_and_neighbouring_policies() -> None:
    images, args = case()
    args["candidate_carriers_yx"] = [(0, 0)]
    observed = select(images, args).candidates[0]
    # Repeated call observations are checked too: no classification-stability claim.
    for threshold in (
        math.nextafter(observed.relative_residual, -math.inf),
        observed.relative_residual,
        math.nextafter(observed.relative_residual, math.inf),
    ):
        result = select(images, args, max_relative_residual=threshold)
        assert_selection(result, POLICY | {"max_relative_residual": threshold})
    for count in (observed.overlap_count - 1, observed.overlap_count, observed.overlap_count + 1):
        result = select(images, args, min_overlap_count=count)
        assert_selection(result, POLICY | {"min_overlap_count": count})


@pytest.mark.parametrize(
    "transfer",
    [1 + 0j, complex(2.0**-1070, 0), complex(2.0**1000, 0), complex(7 * 2.0**1019, -(2.0**1019))],
)
def test_exact_represented_component_gain_gate_at_pythagorean_and_extreme_scales(
    transfer: complex,
) -> None:
    images, args = singleton_gain_case(transfer)
    observed = select(images, args).candidates[0]
    assert observed.status == "fitted" and observed.gain is not None
    magnitude = math.hypot(observed.gain.real, observed.gain.imag)
    upper = min(magnitude, float(np.finfo(np.float64).max))
    bounds_cases = [(0.0, upper), (upper, upper), (upper, float(np.finfo(np.float64).max))]
    if math.isfinite(magnitude) and magnitude > 0:
        bounds_cases += [
            (0.0, math.nextafter(magnitude, 0.0)),
            (math.nextafter(magnitude, math.inf), float(np.finfo(np.float64).max)),
        ]
    if transfer.imag == 0 and transfer.real > 0:
        boundary = 5 * transfer.real
        if math.isfinite(boundary):
            bounds_cases += [
                (boundary, boundary),
                (0.0, boundary),
                (boundary, float(np.finfo(float).max)),
            ]
    if transfer == 1:
        bounds_cases += [(5.0, 5.0), (0.0, 5.0), (5.0, 6.0)]
    for bounds in bounds_cases:
        if not all(math.isfinite(v) for v in bounds) or bounds[0] > bounds[1]:
            continue
        result = select(images, args, gain_magnitude_bounds=bounds)
        assert_selection(result, POLICY | {"gain_magnitude_bounds": bounds})


@pytest.mark.parametrize(
    "kind", ["zero_predictor", "zero_response", "zero_correlation", "incomplete_coverage"]
)
def test_local_statuses_and_zero_gain_eligibility(kind: str) -> None:
    images, args = matched_case()
    args["candidate_carriers_yx"] = [(0, 0), (10**300, 0), (0, 0)]
    r = args["response"]
    if kind == "zero_predictor":
        r.values[1] = 0
    elif kind == "zero_response":
        r.values[0] = 0
    elif kind == "zero_correlation":
        # Disjoint predictor/response support makes computed correlation exactly 0.
        r.values[1] = 0
        r.values[1, 1, 2, 2] = 1
        r.values[0, 1, 2, 2] = 0
    else:
        args["response"] = EmpiricalVolumeResponse(
            np.ones((3, 1, 1, 1), complex),
            np.array([0.0]),
            np.array([0.0]),
            np.array([0.0]),
            (1.0, 1.0, 1.0),
            (0, 0, 0),
        )
    for threshold, bounds in [(2.0, (0.0, 0.0)), (0.0, (0.0, 0.0)), (2.0, (0.1, 2.0))]:
        policy = POLICY | {"max_relative_residual": threshold, "gain_magnitude_bounds": bounds}
        result = select(images, args, max_relative_residual=threshold, gain_magnitude_bounds=bounds)
        assert_selection(result, policy)
        assert [row.status for row in result.candidates] == [kind, "no_overlap", kind]
        assert result.candidates[0].overlap_count == 32
        assert result.candidates[0] is not result.candidates[2]
        if kind in ("zero_response", "zero_correlation"):
            row = result.candidates[0]
            assert row.gain == 0j and row.coherence == 0.0
            assert row.relative_residual == (0.0 if kind == "zero_response" else 1.0)
        else:
            for row in result.candidates:
                assert (row.gain, row.relative_residual, row.coherence) == (None, None, None)


def test_fitted_gain_underflow_is_not_reclassified_or_cut_off() -> None:
    images, args = singleton_gain_case(
        complex(float.fromhex("0x0.0000000000001p-1022"), 0), complex(2.0**1000, 0)
    )
    result = select(images, args, gain_magnitude_bounds=(0, 0))
    row = result.candidates[0]
    assert row.status == "fitted" and row.gain == 0j
    assert result.eligible_indices == (0,)
    assert_selection(result, POLICY | {"gain_magnitude_bounds": (0, 0)})


@pytest.mark.parametrize(
    "mutate,code",
    [
        ("images", "invalid_volume_phase_shape"),
        ("phases", "rank_deficient_volume_phases"),
        ("response", "invalid_empirical_transfer_response"),
        ("spacing", "invalid_volume_carrier_voxel_size"),
        ("candidates", "invalid_volume_carrier_candidates"),
        ("order", "invalid_volume_carrier_order"),
        ("calibration", "invalid_empirical_transfer_carrier"),
        ("offset", "invalid_empirical_transfer_coordinate_offset"),
        ("shift", "invalid_empirical_transfer_phase_shift"),
        ("source", "invalid_otf_source"),
    ],
)
def test_inherited_validation_even_when_candidates_have_no_overlap(mutate: str, code: str) -> None:
    images, args = simple_case()
    args["candidate_carriers_yx"] = [(10**400, 0)]
    if mutate == "images":
        images = images[:, 0]
    elif mutate == "phases":
        args["phase_steps_rad"][:] = 0
    elif mutate == "response":
        args["response"].values[2, 0, 0, 0] = np.nan
    else:
        key, value = {
            "spacing": ("voxel_size_um", (1, 0, 1)),
            "candidates": ("candidate_carriers_yx", [(10**400, 0), (True, 0)]),
            "order": ("order", 3),
            "calibration": ("calibration_carrier_bins", (0.0, 0)),
            "offset": ("coordinate_offset_yx", (False, 0)),
            "shift": ("phase_reference_shift_rad", np.inf),
            "source": ("source", "  "),
        }[mutate]
        args[key] = value
    with pytest.raises(SimreconError) as caught:
        select(images, args)
    assert caught.value.code == code


@pytest.mark.parametrize(
    "error_type,code",
    [
        (FloatingPointError, "volume_carrier_transform_failure"),
        (OverflowError, "volume_carrier_transform_failure"),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
        (MemoryError, None),
    ],
)
def test_public_fft_failures_propagate_without_partial_selection(
    error_type: Any, code: str | None, monkeypatch: Any
) -> None:
    images, args = simple_case()
    error = error_type("real public dependency boundary")

    def fail(*a: Any, **k: Any) -> Any:
        raise error

    monkeypatch.setattr(np.fft, "fftn", fail)
    with pytest.raises(SimreconError if code else error_type) as caught:
        select(images, args)
    if code:
        assert caught.value.code == code
    else:
        assert caught.value is error


def test_public_fft_arithmetic_warning_even_under_ignore_and_unrelated_warning(
    monkeypatch: Any,
) -> None:
    images, args = simple_case()
    original = np.fft.fftn

    def arithmetic(*a: Any, **k: Any) -> Any:
        warnings.warn("overflow encountered in public FFT", RuntimeWarning, stacklevel=2)
        return original(*a, **k)

    monkeypatch.setattr(np.fft, "fftn", arithmetic)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(SimreconError) as caught:
            select(images, args)
        assert caught.value.code == "volume_carrier_transform_failure"

    def unrelated(*a: Any, **k: Any) -> Any:
        warnings.warn("public dependency advisory", UserWarning, stacklevel=2)
        return original(*a, **k)

    monkeypatch.setattr(np.fft, "fftn", unrelated)
    with pytest.warns(UserWarning, match="public dependency advisory"):
        assert_selection(select(images, args), POLICY)


def _late_failure_inputs(large_transfer_x_index: int) -> tuple[Any, dict[str, Any]]:
    images, args = matched_case()
    # The positive transfer has only its DC bin. For candidate +1, that bin
    # pairs with object bin -1. The x-index 1 is bin -1; index 3 is bin +1.
    r = args["response"]
    r.values[1] = 0
    r.values[1, 1, 2, 2] = 1
    r.values[0] = 0
    r.values[0, 1, 2, 2] = 1
    r.values[0, :, :, large_transfer_x_index] = float(np.finfo(float).max) / 4
    h = phase_matrix(args["phase_steps_rad"])
    dc = np.full((2, 4, 4), 2.0)
    dc[:, :, 1] += 0.25
    images = h[:, 0, None, None, None] * dc + h[:, 1, None, None, None] * 2
    args["candidate_carriers_yx"] = [(0, 0)]
    return images, args


def test_global_fit_failure_after_an_otherwise_eligible_first_row() -> None:
    # Preserve the original valid input: its huge transfer lies outside the
    # later nonwrapping objective, so both rows must remain legitimate fits.
    images, args = _late_failure_inputs(3)
    args["candidate_carriers_yx"] = [(0, 0), (0, 1)]
    control = select(images, args)
    assert_selection(control, POLICY)
    assert control.eligible_indices == (0, 1)
    assert [row.overlap_count for row in control.candidates] == [32, 24]
    later = control.candidates[1]
    assert later.gain == 0j and later.coherence == 0.0
    # The computed response norm may vanish with a different allowed solver.
    assert later.status in ("zero_response", "zero_correlation")
    assert later.relative_residual == (0.0 if later.status == "zero_response" else 1.0)

    # Move the large transfer into the later pair at p_x=-1, j_x=0.
    # D0(-1) is approximately i/16 and Dm(0) approximately 1, giving a
    # restored imaginary gain near -4*Fmax. The first row's gain stays finite.
    images, args = _late_failure_inputs(1)
    first = select(images, args)
    assert_selection(first, POLICY)
    assert first.eligible_indices == (0,)
    for candidates in ([(0, 1)], [(0, 0), (0, 1)]):
        args["candidate_carriers_yx"] = candidates
        with pytest.raises(SimreconError) as caught:
            select(images, args)
        assert caught.value.code == "unrepresentable_volume_carrier_fit"


def test_layouts_inputs_state_and_public_scan_compatibility() -> None:
    images, args = case()
    images = np.asfortranarray(images.astype(">f8"))
    images.flags.writeable = False
    args["phase_steps_rad"] = args["phase_steps_rad"].astype(">f8")
    args["phase_steps_rad"].flags.writeable = False
    args["candidate_carriers_yx"] = np.array([(0, 1), (0, 0), (-1, 0), (0, 1)], dtype=">i8")
    args["candidate_carriers_yx"].flags.writeable = False
    arrays = [
        images,
        args["phase_steps_rad"],
        args["candidate_carriers_yx"],
        args["response"].values,
        args["response"].fz_per_um,
        args["response"].fy_per_um,
        args["response"].fx_per_um,
    ]
    before = [(a.tobytes(), a.strides, a.flags.writeable) for a in arrays]
    with np.errstate(all="raise"), warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        filters = list(warnings.filters)
        modes = np.geterr()
        result = select(images, args)
        assert np.geterr() == modes and warnings.filters == filters
        with pytest.raises(SimreconError):
            select(images, args, gain_magnitude_bounds=(1, 0))
        assert np.geterr() == modes and warnings.filters == filters
    assert [(a.tobytes(), a.strides, a.flags.writeable) for a in arrays] == before
    rows = scan_volume_carriers(images, **args)
    for observed, prior in zip(result.candidates, rows, strict=True):
        assert row_tuple(observed)[3:] == row_tuple(prior)[3:]
        for field in ROW_FIELDS[:3]:
            assert getattr(observed, field) == pytest.approx(
                getattr(prior, field), abs=1e-12, rel=1e-12
            )
    saved = [row_tuple(row) for row in result.candidates]
    args["response"].values[:] = 0
    assert [row_tuple(row) for row in result.candidates] == saved
    assert result.candidates[0] is not result.candidates[3]


def test_snapshots_precede_public_solver_and_do_not_alias_later_inputs(monkeypatch: Any) -> None:
    images, args = simple_case()
    before = select(images, args)
    truth = independent_rows(images, args)
    originals = [
        (np.linalg, "lstsq", np.linalg.lstsq),
        (np.linalg, "svd", np.linalg.svd),
        (np.fft, "fftn", np.fft.fftn),
    ]
    bounds = [0.0, 100.0]
    original_policy = POLICY | {"gain_magnitude_bounds": tuple(bounds)}
    changed = False

    def at_boundary(original: Any) -> Any:
        def mutate_then_run(*a: Any, **k: Any) -> Any:
            nonlocal changed
            if not changed:
                changed = True
                bounds[:] = [1000.0, 2000.0]
                images[:] = 0
                args["phase_steps_rad"][:] = 0
                args["response"].values[:] = 0
                args["candidate_carriers_yx"][:] = [(999, 999)]
            return original(*a, **k)

        return mutate_then_run

    for module, name, original in originals:
        monkeypatch.setattr(module, name, at_boundary(original))
    after = select(images, args, gain_magnitude_bounds=bounds)
    assert changed
    assert bounds == [1000.0, 2000.0]
    assert_selection(after, original_policy)
    assert after.eligible_indices == (0, 1, 2)
    assert after.selected_index is None and after.failure_code == "ambiguous_volume_carrier"
    assert exact_indices(after.candidates, POLICY | {"gain_magnitude_bounds": bounds}) == ()
    assert len(after.candidates) == len(before.candidates)
    for observed, prior, expected in zip(after.candidates, before.candidates, truth, strict=True):
        assert row_tuple(observed)[3:] == row_tuple(prior)[3:]
        for field, budget in (
            ("gain", "gain_budget"),
            ("relative_residual", "residual_budget"),
            ("coherence", "coherence_budget"),
        ):
            assert (
                abs(getattr(observed, field) - expected[field])
                <= expected[budget] * 1.000001 + 1e-60
            )


def test_sparse_single_pair_can_mislead_and_alias_does_not_get_reduced() -> None:
    images, args = singleton_gain_case(1 + 0j)
    args["candidate_carriers_yx"] = [(0, 0), (0, 1), (0, 0)]
    result = select(images, args, max_relative_residual=0.01, gain_magnitude_bounds=(4, 6))
    assert result.eligible_indices == (0, 2)
    assert result.failure_code == "ambiguous_volume_carrier"
    assert result.candidates[0].overlap_count == 1
    truth = independent_rows(images, args | {"candidate_carriers_yx": [(0, 0)]})[0]
    assert abs(result.candidates[0].gain - truth["gain"]) <= truth["gain_budget"]
    assert result.candidates[1].status == "no_overlap"  # no periodic reduction
    args["candidate_carriers_yx"] = [(0, 0)]
    sole = select(images, args, max_relative_residual=0.01, gain_magnitude_bounds=(4, 6))
    assert sole.selected_index == 0  # says nothing about unexamined physical truth


class TupleSubclass(tuple):
    """Non-exact container excluded by the public grammar."""


class ListSubclass(list):
    """Non-exact container excluded by the public grammar."""


@pytest.mark.parametrize("bounds", [TupleSubclass((0, 100)), ListSubclass([0, 100])])
def test_bound_container_subclasses_are_rejected(bounds: Any) -> None:
    images, args = simple_case()
    with pytest.raises(SimreconError) as caught:
        select(images, args, gain_magnitude_bounds=bounds)
    assert caught.value.code == "invalid_volume_carrier_selection_policy"


@pytest.mark.parametrize(
    "error_type", [RuntimeError, MemoryError, TypeError, ValueError, OverflowError]
)
def test_unrelated_response_getter_exception_identity(error_type: Any) -> None:
    images, args = simple_case()
    r = args["response"]
    error = error_type("public response getter sentinel")

    class ResponseSubclass(EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                raise error
            return super().__getattribute__(name)

    args["response"] = ResponseSubclass(
        r.values, r.fz_per_um, r.fy_per_um, r.fx_per_um, r.voxel_size_um, r.origin_zyx
    )
    with pytest.raises(error_type) as caught:
        select(images, args)
    assert caught.value is error


@pytest.mark.parametrize("value", [float("inf"), float("nan")])
def test_source_nonfinite_scalar_cannot_hide_behind_finite_conversion(value: float) -> None:
    class HiddenNonfinite(float):
        def __float__(self) -> float:
            return 0.0

    images, args = simple_case()
    for policy in (
        {"max_relative_residual": HiddenNonfinite(value)},
        {"gain_magnitude_bounds": (0, HiddenNonfinite(value))},
    ):
        with pytest.raises(SimreconError) as caught:
            select(images, args, **policy)
        assert caught.value.code == "invalid_volume_carrier_selection_policy"
