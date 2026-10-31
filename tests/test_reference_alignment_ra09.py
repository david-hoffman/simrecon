"""Blind public-contract RA09 tests; no implementation or legacy oracle."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pytest

import simrecon
from reference_alignment_ra09_fixture import (
    DIAGNOSTIC_ATOL,
    NORM_FLOOR,
    RECOVERY_GAIN_ATOL,
    RECOVERY_PHASE_ATOL,
    VALUE_ATOL,
    arbitrary_case,
    calibration,
    diagnostics,
    evaluate,
    field_prediction,
    nonconstant_transfer_control,
    overlap,
    recovery_control,
    replace_calibration,
)


@pytest.fixture
def public_fit() -> Any:
    operation = getattr(simrecon, "fit_volume_overlap", None)
    assert callable(operation), "RA09 public fit_volume_overlap binding is required"
    assert isinstance(getattr(simrecon, "VolumeOverlapFit", None), type)
    assert isinstance(getattr(simrecon, "VolumeOverlapCandidate", None), type)
    return operation


def invoke(operation: Any, bands: Any, cal: Any, **changes: Any) -> Any:
    arguments = {
        "order_otf": cal,
        "initial_carriers_per_um": np.array([[0.0, 0.0]]),
        "carrier_bounds_per_um": np.zeros((2, 2)),
        "difference_step_per_um": np.array([1 / 1024, 1 / 1024]),
        "gradient_tolerance": 1e-8,
        "rank_rtol": 1e-6,
        "max_evaluations": 1,
    }
    arguments.update(changes)
    return operation(bands, **arguments)


def assert_point(candidate: Any, expected: Any, atol: float = VALUE_ATOL) -> None:
    assert candidate.order_status == expected.statuses
    assert candidate.objective == pytest.approx(expected.objective, abs=atol, rel=atol)
    for name, truth in (
        ("gains", expected.gains),
        ("coherence", expected.coherence),
        ("relative_residual", expected.relative),
        ("predictor_log2_norm", expected.logx),
        ("response_log2_norm", expected.logy),
    ):
        observed = getattr(candidate, name)
        assert isinstance(observed, tuple) and len(observed) == 2
        for got, want in zip(observed, truth, strict=True):
            if want is None:
                assert got is None
            else:
                assert got == pytest.approx(want, abs=atol, rel=atol)


def test_oracle_declared_controls_and_distinguishing_signal() -> None:
    """Pre-fit self-check: independent model, norms and diagnostic margins."""
    control = recovery_control()
    truth = evaluate(control.bands, control.calibration, control.bounds, control.truth)
    nominal = evaluate(control.bands, control.calibration, control.bounds, tuple(control.starts[0]))
    assert truth.objective < VALUE_ATOL**2
    assert nominal.objective > 100 * VALUE_ATOL
    assert truth.gains == pytest.approx(control.gains, abs=VALUE_ATOL)
    assert min(n for pair in truth.scaled_norms for n in pair) > NORM_FLOOR
    assert min(n for pair in nominal.scaled_norms for n in pair) > NORM_FLOOR
    assert max(np.max(np.abs(control.bands.real)), np.max(np.abs(control.bands.imag))) < 16
    assert control.bands[0].size <= 125
    assert np.max(np.abs(control.calibration.values)) < 2
    info = diagnostics(
        control.bands,
        control.calibration,
        control.bounds,
        tuple(control.starts[0]),
        control.step,
        1e-6,
    )
    assert info["rank"] == 2 and info["continuous"]
    assert info["singular"][1] / info["singular"][0] > 0.1


@pytest.mark.parametrize("carrier", [(0.0, 0.0), (0.11, -0.07), (-0.125, 0.08)])
def test_fixed_fractional_direct_sum_complex_interpolation(
    public_fit: Any, carrier: tuple[float, float]
) -> None:
    bands, cal = arbitrary_case()
    bounds = np.array([carrier, carrier])
    expected = evaluate(bands, cal, bounds, carrier)
    assert min(n for pair in expected.scaled_norms for n in pair) > 1e-8
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=np.array([carrier]),
        carrier_bounds_per_um=bounds,
    )
    candidate = result.candidates[0]
    assert_point(candidate, expected)
    assert candidate.carrier_per_um == carrier
    assert candidate.initial_carrier_per_um == carrier
    assert candidate.search_evaluations == 1
    assert candidate.projected_gradient == 0
    assert candidate.stationary is True
    assert candidate.information_rank == 0
    np.testing.assert_array_equal(candidate.information_singular_values, [0.0, 0.0])
    assert candidate.status == "finite_difference_stationary"
    assert candidate.global_ambiguity == "unresolved"
    assert candidate.diagnostics_continuous is True
    for m in (1, 2):
        np.testing.assert_array_equal(
            result.overlap_bins[m - 1], overlap(bands.shape[1:], cal.voxel_size_um, bounds, m)
        )


@pytest.mark.parametrize("layout", ["fortran", "strided", "readonly", "big_endian"])
def test_permitted_layouts_and_signed_nonphysical_harmonics(public_fit: Any, layout: str) -> None:
    bands, cal = arbitrary_case((2, 3, 4))
    bands[0] -= 3  # signed dc; positive rows need not obey Hermitian symmetry
    if layout == "fortran":
        bands = np.asfortranarray(bands)
    elif layout == "strided":
        backing = np.zeros((*bands.shape[:-1], 2 * bands.shape[-1]), dtype=np.complex128)
        backing[..., ::2] = bands
        bands = backing[..., ::2]
    elif layout == "readonly":
        bands.flags.writeable = False
    else:
        bands = bands.astype(">c16")
    expected = evaluate(bands, cal, np.zeros((2, 2)), (0.0, 0.0))
    assert_point(invoke(public_fit, bands, cal).candidates[0], expected)


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "complex64",
        "real",
        "object",
        "bool",
        "empty",
        "rank",
        "orders",
        "nan",
        "inf_imag",
        "dc_imag",
    ],
)
def test_bands_rejection(public_fit: Any, kind: str) -> None:
    bands, cal = arbitrary_case()
    bad: Any = bands.copy()
    if kind == "list":
        bad = bands.tolist()
    elif kind == "subclass":

        class Derived(np.ndarray):
            pass

        bad = bands.view(Derived)
    elif kind == "masked":
        bad = np.ma.array(bands)
    elif kind in ("complex64", "real", "object", "bool"):
        dtype = {"complex64": "c8", "real": "f8", "object": "O", "bool": "?"}[kind]
        bad = bands.real.astype(dtype) if kind == "real" else bands.astype(dtype)
    elif kind == "empty":
        bad = bands[:, :0]
    elif kind == "rank":
        bad = bands[0]
    elif kind == "orders":
        bad = bands[:2]
    elif kind == "nan":
        bad[1, 0, 0, 0] = complex(float("nan"), 0)
    elif kind == "inf_imag":
        bad[2, 0, 0, 0] = complex(0, float("inf"))
    else:
        bad[0, 0, 0, 0] += 1e-300j
    with pytest.raises(simrecon.SimreconError) as error:
        invoke(public_fit, bad, cal)
    assert error.value.code == "invalid_volume_overlap_bands"


@pytest.mark.parametrize(
    "field,value",
    [
        ("values", None),
        ("values", "wrong_width"),
        ("values", "nonfinite_unused"),
        ("values", "subclass"),
        ("values", "masked"),
        ("values", "shape"),
        ("fz_per_um", "wrong_width"),
        ("fy_per_um", "wrong_node"),
        ("fx_per_um", "nonfinite"),
        ("fx_per_um", "reverse"),
        ("fz_per_um", "shape"),
        ("fy_per_um", "subclass"),
        ("voxel_size_um", (1.0, 0.0, 1.0)),
        ("voxel_size_um", (True, 1.0, 1.0)),
        ("voxel_size_um", (1.0, 1.0)),
        ("voxel_size_um", (1.0, float("inf"), 1.0)),
        ("origin_zyx", (0, 0, 5)),
        ("origin_zyx", (False, 0, 0)),
        ("origin_zyx", (0.0, 0, 0)),
        ("source", "  "),
        ("source", None),
    ],
)
def test_all_calibration_fields_validated(public_fit: Any, field: str, value: Any) -> None:
    bands, cal = arbitrary_case()
    replacement = value
    if isinstance(value, str) and field != "source":
        array = getattr(cal, field).copy()
        if value == "wrong_width":
            replacement = array.astype("c8" if field == "values" else "f4")
        elif value == "nonfinite_unused":
            array[2, 0, 0, 0] = complex(0, float("inf"))
            replacement = array
        elif value == "masked":
            replacement = np.ma.array(array)
        elif value == "subclass":

            class Derived(np.ndarray):
                pass

            replacement = array.view(Derived)
        elif value == "shape":
            replacement = array[:-1]
        elif value == "wrong_node":
            array[0] += 0.01
            replacement = array
        elif value == "nonfinite":
            array[0] = float("nan")
            replacement = array
        else:
            replacement = array[::-1]
    bad = replace_calibration(cal, **{field: replacement})
    # RA09 names no OTF-specific stable code. Do not invent one from siblings.
    with pytest.raises(simrecon.SimreconError):
        invoke(public_fit, bands, bad)


def test_calibration_positive_endian_storage_and_nonzero_origin(public_fit: Any) -> None:
    bands, cal = arbitrary_case()
    fields = {}
    for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
        old = getattr(cal, name)
        copy = np.asfortranarray(old.astype(">c16" if name == "values" else ">f8"))
        copy.flags.writeable = False
        fields[name] = copy
    fields.update(origin_zyx=(1, 2, 3), voxel_size_um=list(cal.voxel_size_um))
    cal = replace_calibration(cal, **fields)
    expected = evaluate(bands, cal, np.zeros((2, 2)), (0.0, 0.0))
    result = invoke(public_fit, bands, cal)
    assert_point(result.candidates[0], expected)
    assert result.source == cal.source
    assert result.spacing_um == tuple(cal.voxel_size_um)
    with pytest.raises(simrecon.SimreconError):
        invoke(public_fit, bands, object())


@pytest.mark.parametrize(
    "name,value",
    [
        ("initial_carriers_per_um", []),
        ("initial_carriers_per_um", np.zeros((0, 2))),
        ("initial_carriers_per_um", np.zeros(2)),
        ("initial_carriers_per_um", np.zeros((1, 3))),
        ("initial_carriers_per_um", np.zeros((1, 2), dtype=bool)),
        ("initial_carriers_per_um", np.zeros((1, 2), dtype=complex)),
        ("initial_carriers_per_um", np.array([[float("nan"), 0]])),
        ("initial_carriers_per_um", np.array([[0.01, 0]])),
        ("carrier_bounds_per_um", [[0, 0], [0, 0]]),
        ("carrier_bounds_per_um", np.zeros((2, 2), dtype=complex)),
        ("carrier_bounds_per_um", np.zeros((1, 2))),
        ("carrier_bounds_per_um", np.array([[0.1, 0], [0, 0]])),
        ("carrier_bounds_per_um", np.array([[0, 0], [float("inf"), 0]])),
    ],
)
def test_search_rejection(public_fit: Any, name: str, value: Any) -> None:
    bands, cal = arbitrary_case()
    with pytest.raises(simrecon.SimreconError) as error:
        invoke(public_fit, bands, cal, **{name: value})
    assert error.value.code == "invalid_volume_overlap_search"


@pytest.mark.parametrize(
    "name,value",
    [
        ("difference_step_per_um", [0.01, 0.01]),
        ("difference_step_per_um", np.array([0.01])),
        ("difference_step_per_um", np.array([0.0, 0.01])),
        ("difference_step_per_um", np.array([-0.01, 0.01])),
        ("difference_step_per_um", np.array([float("nan"), 0.01])),
        ("difference_step_per_um", np.array([1j, 1j])),
        ("difference_step_per_um", np.array([True, True])),
        ("gradient_tolerance", True),
        ("gradient_tolerance", -1.0),
        ("gradient_tolerance", float("inf")),
        ("gradient_tolerance", 1j),
        ("gradient_tolerance", np.array(0.1)),
        ("rank_rtol", 0.0),
        ("rank_rtol", 1.0),
        ("rank_rtol", True),
        ("rank_rtol", float("nan")),
        ("max_evaluations", False),
        ("max_evaluations", 0),
        ("max_evaluations", 1.0),
        ("max_evaluations", np.array(1)),
    ],
)
def test_controls_rejection(public_fit: Any, name: str, value: Any) -> None:
    bands, cal = arbitrary_case()
    with pytest.raises(simrecon.SimreconError) as error:
        invoke(public_fit, bands, cal, **{name: value})
    assert error.value.code == "invalid_volume_overlap_controls"


@pytest.mark.parametrize(
    "name", ["initial_carriers_per_um", "carrier_bounds_per_um", "difference_step_per_um"]
)
@pytest.mark.parametrize("representation", ["subclass", "masked", "bool", "object", "string"])
def test_search_and_step_plain_numeric_array_grammar(
    public_fit: Any, name: str, representation: str
) -> None:
    bands, cal = arbitrary_case()
    shapes = {
        "initial_carriers_per_um": (1, 2),
        "carrier_bounds_per_um": (2, 2),
        "difference_step_per_um": (2,),
    }
    valid = np.ones(shapes[name]) if name == "difference_step_per_um" else np.zeros(shapes[name])
    if representation == "subclass":

        class Derived(np.ndarray):
            pass

        bad = valid.view(Derived)
    elif representation == "masked":
        bad = np.ma.array(valid)
    else:
        bad = valid.astype({"bool": "?", "object": "O", "string": "U4"}[representation])
    with pytest.raises(simrecon.SimreconError) as error:
        invoke(public_fit, bands, cal, **{name: bad})
    expected_code = (
        "invalid_volume_overlap_controls"
        if name == "difference_step_per_um"
        else "invalid_volume_overlap_search"
    )
    assert error.value.code == expected_code


def test_nonfixed_axis_requires_representable_step_at_each_endpoint(public_fit: Any) -> None:
    bands, cal = arbitrary_case((1, 2, 2))
    lower, upper = 1.0, float(np.nextafter(1.0, np.inf))
    bounds = np.array([[lower, 0.0], [upper, 0.0]])
    starts = np.array([[lower, 0.0], [upper, 0.0]])
    with pytest.raises(simrecon.SimreconError) as error:
        invoke(
            public_fit,
            bands,
            cal,
            initial_carriers_per_um=starts,
            carrier_bounds_per_um=bounds,
            difference_step_per_um=np.array([2.0**-1074, 1.0]),
        )
    assert error.value.code == "invalid_volume_overlap_controls"
    # Adjacent binary64 endpoints are valid with a representable positive step.
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=starts,
        carrier_bounds_per_um=bounds,
        difference_step_per_um=np.array([upper - lower, 1.0]),
    )
    assert len(result.candidates) == 2
    for candidate, start in zip(result.candidates, starts, strict=True):
        assert candidate.carrier_per_um == tuple(start)


@pytest.mark.parametrize("dtype", ["i2", "u8", ">f8", "f4"])
def test_permitted_search_numeric_representations(public_fit: Any, dtype: str) -> None:
    bands, cal = arbitrary_case((1, 3, 4))
    starts = np.zeros((3, 2), dtype=dtype)
    starts.flags.writeable = False
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=starts,
        carrier_bounds_per_um=np.zeros((2, 2), dtype=dtype),
        difference_step_per_um=np.array([1, 1], dtype=dtype),
        gradient_tolerance=np.float32(0),
        rank_rtol=np.float64(0.1),
        max_evaluations=np.uint64(1),
    )
    assert len(result.candidates) == 3
    assert all(c.initial_carrier_per_um == (0.0, 0.0) for c in result.candidates)


@pytest.mark.parametrize(
    "shape,start_count,budget",
    [((2, 7, 9), 1, 1), ((1, 1, 1), 5, 1), ((1, 1, 1), 1, 257)],
    ids=["126_voxels", "five_starts", "budget_257"],
)
def test_moderate_success_bounds_are_not_rejection_caps(
    public_fit: Any, shape: tuple[int, int, int], start_count: int, budget: int
) -> None:
    bands = np.zeros((3, *shape), dtype=np.complex128)
    cal = calibration(np.ones_like(bands), (1.0, 1.0, 1.0))
    starts = np.zeros((start_count, 2))
    bounds = np.zeros((2, 2))
    # Zero predictors and responses have exact unavailable-marker truth. This
    # needs no extended numerical accuracy promise or expensive local search.
    expected_overlap = [overlap(shape, cal.voxel_size_um, bounds, m) for m in (1, 2)]
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=starts,
        carrier_bounds_per_um=bounds,
        max_evaluations=budget,
    )
    assert len(result.candidates) == start_count
    for got, expected in zip(result.overlap_bins, expected_overlap, strict=True):
        np.testing.assert_array_equal(got, expected)
        assert len(got) == bands[0].size
    for candidate in result.candidates:
        assert candidate.initial_carrier_per_um == (0.0, 0.0)
        assert candidate.carrier_per_um == (0.0, 0.0)
        assert candidate.order_status == ("zero_predictor", "zero_predictor")
        assert candidate.gains == (None, None)
        assert candidate.coherence == (None, None)
        assert candidate.relative_residual == (None, None)
        assert candidate.predictor_log2_norm == (None, None)
        assert candidate.response_log2_norm == (None, None)
        assert candidate.objective == 2.0
        assert candidate.status == "unavailable"
        assert candidate.search_evaluations == 1
        assert candidate.information_rank == 0
        np.testing.assert_array_equal(candidate.information_singular_values, [0.0, 0.0])
        assert candidate.global_ambiguity == "unresolved"


@pytest.mark.parametrize("endpoint", [0.25, np.nextafter(0.25, 0), np.nextafter(0.25, 1)])
def test_exact_overlap_endpoint_no_tolerance(public_fit: Any, endpoint: float) -> None:
    bands, _ = arbitrary_case((1, 4, 4))
    cal = calibration(np.ones_like(bands), (1.0, 1.0, 1.0))
    carrier = (float(endpoint), 0.0)
    bounds = np.array([carrier, carrier])
    expected = [overlap((1, 4, 4), cal.voxel_size_um, bounds, m) for m in (1, 2)]
    # Crossing the exact one-bin endpoint removes a row, even by one ulp.
    counts = (8, 4) if endpoint > 0.25 else (12, 8)
    assert tuple(len(q) for q in expected) == counts
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=np.array([carrier]),
        carrier_bounds_per_um=bounds,
    )
    for got, want in zip(result.overlap_bins, expected, strict=True):
        np.testing.assert_array_equal(got, want)


def test_fixed_all_box_overlap_signed_duplicate_starts(public_fit: Any) -> None:
    bands, cal = arbitrary_case()
    bounds = np.array([[-0.12, -0.05], [0.13, 0.07]])
    starts = np.array([[0.0, 0.0], [-0.12, 0.07], [0.0, 0.0], [0.13, -0.05]])
    result = invoke(
        public_fit, bands, cal, initial_carriers_per_um=starts, carrier_bounds_per_um=bounds
    )
    assert len(result.candidates) == 4
    for candidate, start in zip(result.candidates, starts, strict=True):
        assert candidate.initial_carrier_per_um == tuple(start)
        assert candidate.carrier_per_um == tuple(start)  # seed consumes budget
        assert candidate.global_ambiguity == "unresolved"
        assert candidate.search_evaluations == 1
        assert candidate.budget_exhausted is True
        assert_point(candidate, evaluate(bands, cal, bounds, tuple(start)))
    for m in (1, 2):
        np.testing.assert_array_equal(
            result.overlap_bins[m - 1], overlap(bands.shape[1:], cal.voxel_size_um, bounds, m)
        )


@pytest.mark.parametrize(
    "mode,status,gain,objective",
    [
        ("all_zero", "zero_predictor", None, 2.0),
        ("transfer_zero", "zero_predictor", None, 2.0),
        ("response_zero", "zero_response", 0j, 2.0),
        ("orthogonal", "zero_correlation", 0j, 2.0),
    ],
)
def test_information_outcomes_and_precedence(
    public_fit: Any, mode: str, status: str, gain: complex | None, objective: float
) -> None:
    bands = np.zeros((3, 1, 1, 2), dtype=np.complex128)
    bands[:, 0, 0, 0] = 1
    values = np.ones_like(bands)
    if mode == "all_zero":
        bands[:] = 0
    elif mode == "transfer_zero":
        values[1:] = 0
    elif mode == "response_zero":
        bands[1:] = 0
    else:
        values[0, 0, 0] = [1, -1]
    result = invoke(public_fit, bands, calibration(values, (1.0, 1.0, 1.0)))
    candidate = result.candidates[0]
    assert candidate.order_status == (status, status)
    assert candidate.gains == (gain, gain)
    assert candidate.objective == pytest.approx(objective, abs=VALUE_ATOL)
    if mode == "orthogonal":
        assert candidate.coherence == (0.0, 0.0)
        assert candidate.relative_residual == (1.0, 1.0)
        assert candidate.status == "finite_difference_stationary"
    else:
        assert candidate.coherence == (None, None)
        assert candidate.relative_residual == (None, None)
        assert candidate.status == "unavailable"
    assert candidate.information_rank == 0


def test_singleton_empty_overlap_and_one_informative_order(public_fit: Any) -> None:
    bands = np.ones((3, 1, 1, 3), dtype=np.complex128)
    cal = calibration(np.ones_like(bands), (1.0, 1.0, 1.0))
    bounds = np.array([[0.0, 0.0], [0.01, 0.0]])
    result = invoke(public_fit, bands, cal, carrier_bounds_per_um=bounds)
    assert all(q.shape == (0, 3) for q in result.overlap_bins)
    assert result.candidates[0].order_status == ("no_overlap", "no_overlap")
    assert result.candidates[0].objective == 2.0
    assert result.candidates[0].status == "unavailable"
    control = recovery_control()
    control.bands[2] = 0
    expected = evaluate(
        control.bands, control.calibration, control.bounds, tuple(control.starts[0])
    )
    candidate = invoke(
        public_fit,
        control.bands,
        control.calibration,
        initial_carriers_per_um=control.starts,
        carrier_bounds_per_um=control.bounds,
    ).candidates[0]
    assert_point(candidate, expected)
    assert candidate.order_status == ("fitted", "zero_response")
    assert candidate.objective >= 1
    assert candidate.status != "unavailable"


@pytest.mark.parametrize(
    "location",
    [
        "interior",
        "lower",
        "upper",
        "one_fixed",
        "unequal_interior",
        "unequal_lower",
        "unequal_one_fixed",
        "near_lower_upper",
        "near_upper_lower_unequal",
        "both_sides_shortened",
    ],
)
def test_independent_projected_secants_and_profiled_information(
    public_fit: Any, location: str
) -> None:
    bands, cal = arbitrary_case()
    h = 1 / 1024
    wide = ((-0.12, -0.05), (0.13, 0.07))
    fixed = ((-0.12, 0.01), (0.13, 0.01))
    unequal = (1 / 512, 1 / 128)
    narrow = (
        (0.02 - unequal[0] / 4, 0.01 - unequal[1] / 2),
        (0.02 + unequal[0] / 2, 0.01 + unequal[1] / 4),
    )
    # Fractions below give the declared negative/positive distances on each
    # axis as multiples of that caller-supplied axis step.
    cases = {
        "interior": ((0.02, 0.01), wide, (h, h), ((1.0, 1.0), (1.0, 1.0))),
        "lower": (wide[0], wide, (h, h), ((0.0, 1.0), (0.0, 1.0))),
        "upper": (wide[1], wide, (h, h), ((1.0, 0.0), (1.0, 0.0))),
        "one_fixed": ((0.02, 0.01), fixed, (h, h), ((1.0, 1.0), (0.0, 0.0))),
        "unequal_interior": ((0.02, 0.01), wide, unequal, ((1.0, 1.0), (1.0, 1.0))),
        "unequal_lower": (wide[0], wide, unequal, ((0.0, 1.0), (0.0, 1.0))),
        "unequal_one_fixed": ((0.02, 0.01), fixed, unequal, ((1.0, 1.0), (0.0, 0.0))),
        "near_lower_upper": (
            (wide[0][0] + h / 4, wide[1][1] - h / 2),
            wide,
            (h, h),
            ((0.25, 1.0), (1.0, 0.5)),
        ),
        "near_upper_lower_unequal": (
            (wide[1][0] - unequal[0] / 2, wide[0][1] + unequal[1] / 4),
            wide,
            unequal,
            ((1.0, 0.5), (0.25, 1.0)),
        ),
        "both_sides_shortened": (
            (0.02, 0.01),
            narrow,
            unequal,
            ((0.25, 0.5), (0.5, 0.25)),
        ),
    }
    point, box, steps, distance_fractions = cases[location]
    bounds, step = np.array(box), np.array(steps)
    # The search budget permits only the seed. Independently enumerate the
    # distinct clipped diagnostic points from public box/step geometry, so
    # none can already have been visited by that search.
    fresh_points: set[tuple[float, float]] = set()
    distances = np.zeros((2, 2))
    for axis in range(2):
        for side, bound in enumerate(bounds[:, axis]):
            delta = float(bound) - point[axis]
            if delta == 0:
                continue
            distance = min(float(step[axis]), abs(delta))
            distances[axis, side] = distance
            neighbor = list(point)
            neighbor[axis] += distance if delta > 0 else -distance
            fresh_points.add((float(neighbor[0]), float(neighbor[1])))
    fresh_points.discard(point)
    np.testing.assert_array_equal(distances, step[:, None] * np.asarray(distance_fractions))
    for axis in range(2):
        span = max(k[axis] for k in fresh_points | {point}) - min(
            k[axis] for k in fresh_points | {point}
        )
        assert span == distances[axis].sum()
    expected_directions = int(np.count_nonzero(distances))
    assert len(fresh_points) == expected_directions
    # VALUE_ATOL is unchanged: dimensions <=125 and scaled norm floor 1/16.
    # Secant perturbations divide by the actual positive distance. Eight times
    # that budget/minimum distance also bounds the two-column Jacobian spectrum
    # perturbation; fixed axes have no denominator and contribute zero.
    diagnostic_atol = 8 * VALUE_ATOL / float(np.min(distances[distances > 0]))
    expected = evaluate(bands, cal, bounds, point)
    diagnostic = diagnostics(bands, cal, bounds, point, step, 1e-6)
    # Expected arrays, rank and status are fixed before the fit.
    free = int(np.count_nonzero(bounds[1] > bounds[0]))
    gtol = 1e-8
    status = (
        "information_deficient"
        if diagnostic["rank"] < free
        else "finite_difference_stationary"
        if diagnostic["gradient"] <= gtol
        else "evaluation_limit"
    )
    candidate = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=np.array([point]),
        carrier_bounds_per_um=bounds,
        difference_step_per_um=step,
    ).candidates[0]
    assert_point(candidate, expected)
    assert candidate.projected_gradient == pytest.approx(
        diagnostic["gradient"], abs=diagnostic_atol, rel=VALUE_ATOL
    )
    np.testing.assert_allclose(
        candidate.information_singular_values,
        diagnostic["singular"],
        atol=diagnostic_atol,
        rtol=VALUE_ATOL,
    )
    assert candidate.information_rank == diagnostic["rank"]
    assert candidate.stationary is (diagnostic["gradient"] <= gtol)
    assert candidate.status == status
    assert candidate.diagnostics_continuous is True
    assert candidate.search_evaluations == 1
    assert candidate.budget_exhausted is True
    # Central result must remain the seed, even if diagnostics find a decrease.
    assert candidate.carrier_per_um == point
    assert isinstance(candidate.diagnostic_evaluations, int)
    assert candidate.diagnostic_evaluations >= len(fresh_points)


def test_rank_relative_cutoff_and_finite_step_stationarity(public_fit: Any) -> None:
    bands, cal = arbitrary_case()
    bounds = np.array([[-0.12, -0.05], [0.13, 0.07]])
    point = (0.02, 0.01)
    step = np.array([1 / 1024, 1 / 1024])
    info = diagnostics(bands, cal, bounds, point, step, 1e-6)
    ratio = float(info["singular"][1] / info["singular"][0])
    assert 0.01 < ratio < 0.99
    for rtol, rank in ((ratio / 2, 2), ((1 + ratio) / 2, 1)):
        result = invoke(
            public_fit,
            bands,
            cal,
            initial_carriers_per_um=np.array([point]),
            carrier_bounds_per_um=bounds,
            difference_step_per_um=step,
            gradient_tolerance=1e6,
            rank_rtol=rtol,
        )
        candidate = result.candidates[0]
        assert candidate.stationary is True
        assert candidate.information_rank == rank
        assert candidate.status == (
            "finite_difference_stationary" if rank == 2 else "information_deficient"
        )
        assert candidate.budget_exhausted is True


@pytest.mark.parametrize("changing", [False, True])
def test_rank_deficiency_and_nonsmooth_marker_precedence(public_fit: Any, changing: bool) -> None:
    bands = np.zeros((3, 1, 1, 3), dtype=np.complex128)
    bands[:, 0, 0, 0] = 1
    values = np.ones_like(bands)
    if changing:
        values[1, 0, 0] = [-1, 0, 1]
    cal = calibration(values, (1.0, 1.0, 1.0))
    bounds = np.array([[0.0, -0.1], [0.0, 0.1]])
    expected = evaluate(bands, cal, bounds, (0.0, 0.0))
    info = diagnostics(bands, cal, bounds, (0.0, 0.0), np.array([1 / 1024, 1 / 1024]), 1e-6)
    candidate = invoke(public_fit, bands, cal, carrier_bounds_per_um=bounds).candidates[0]
    assert_point(candidate, expected)
    assert candidate.diagnostics_continuous is (not changing)
    assert candidate.status == ("nonsmooth_diagnostics" if changing else "information_deficient")
    assert candidate.stationary is (not changing)
    assert candidate.budget_exhausted is True
    assert candidate.projected_gradient == pytest.approx(info["gradient"], abs=DIAGNOSTIC_ATOL)
    if not changing:
        assert candidate.information_rank == 0
        np.testing.assert_array_equal(candidate.information_singular_values, [0.0, 0.0])


@pytest.mark.parametrize("budget", [1, 2, 8])
def test_search_keeps_seed_or_better_without_diagnostic_candidate_leak(
    public_fit: Any, budget: int
) -> None:
    control = recovery_control()
    initial = evaluate(control.bands, control.calibration, control.bounds, tuple(control.starts[0]))
    result = invoke(
        public_fit,
        control.bands,
        control.calibration,
        initial_carriers_per_um=control.starts,
        carrier_bounds_per_um=control.bounds,
        difference_step_per_um=control.step,
        max_evaluations=budget,
    )
    candidate = result.candidates[0]
    assert 1 <= candidate.search_evaluations <= budget
    assert candidate.objective <= initial.objective + VALUE_ATOL
    assert np.all(np.asarray(candidate.carrier_per_um) >= control.bounds[0])
    assert np.all(np.asarray(candidate.carrier_per_um) <= control.bounds[1])
    # Returned carrier is an observation here: this checks consistency with the
    # fixed estimator, not recovery against independent synthetic truth.
    at_returned = evaluate(
        control.bands, control.calibration, control.bounds, candidate.carrier_per_um
    )
    assert_point(candidate, at_returned)
    if budget == 1:
        assert candidate.carrier_per_um == tuple(control.starts[0])
        assert candidate.budget_exhausted is True


def test_flat_objective_first_tie_preserves_all_starts(public_fit: Any) -> None:
    bands = np.zeros((3, 1, 3, 3), dtype=np.complex128)
    cal = calibration(np.ones_like(bands), (1.0, 1.0, 1.0))
    starts = np.array([[0.1, -0.1], [-0.1, 0.1], [0.1, -0.1]])
    bounds = np.array([[-0.15, -0.15], [0.15, 0.15]])
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=starts,
        carrier_bounds_per_um=bounds,
        max_evaluations=8,
    )
    assert len(result.candidates) == len(starts)
    for candidate, initial in zip(result.candidates, starts, strict=True):
        assert candidate.carrier_per_um == tuple(initial)
        assert candidate.initial_carrier_per_um == tuple(initial)
        assert candidate.objective == 2
        assert candidate.status == "unavailable"
        assert 1 <= candidate.search_evaluations <= 8
        assert candidate.global_ambiguity == "unresolved"


@pytest.mark.parametrize("scale", [2.0**-900, 1.0, 2.0**900])
def test_component_scaling_and_raw_log_norms(public_fit: Any, scale: float) -> None:
    bands, cal = arbitrary_case((2, 3, 4))
    carrier = (0.0, 0.0)
    bounds = np.zeros((2, 2))
    base = evaluate(bands, cal, bounds, carrier)
    bands *= scale
    expected = evaluate(bands, cal, bounds, carrier)
    old_policy = np.geterr()
    old_filters = list(warnings.filters)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = invoke(public_fit, bands, cal)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.geterr() == old_policy
    assert warnings.filters == old_filters
    assert_point(result.candidates[0], expected)
    assert result.candidates[0].gains == pytest.approx(base.gains, abs=VALUE_ATOL)
    for raw, shifted in zip(base.logx, result.candidates[0].predictor_log2_norm, strict=True):
        assert shifted == pytest.approx(raw + np.log2(scale), abs=VALUE_ATOL)


@pytest.mark.parametrize(
    "mode",
    [
        "overflow_products",
        "overflow_complex_magnitude",
        "ratio_overflow_components_fit",
        "tiny_nonzero",
        "gain_underflow",
    ],
)
def test_scaled_extreme_analytic_single_voxel(public_fit: Any, mode: str) -> None:
    bands = np.ones((3, 1, 1, 1), dtype=np.complex128)
    values = np.ones_like(bands)
    expected_gain = 1 + 0j
    if mode == "overflow_products":
        bands *= 2.0**800
        values *= 2.0**800
        expected_logx = expected_logy = 1600.0
    elif mode == "overflow_complex_magnitude":
        values[:] = complex(1.7e308, 1.7e308)
        expected_logx = expected_logy = np.log2(1.7e308) + 0.5
    elif mode == "ratio_overflow_components_fit":
        bands[0] = 1 / 8
        bands[1:] = complex(1.5e308, 1.5e308)
        values[1:] = 8
        expected_gain = complex(1.5e308, 1.5e308)
        expected_logx = 0.0
        expected_logy = np.log2(1.5e308) + 0.5
    elif mode == "tiny_nonzero":
        bands[1:] = 2.0**-900
        expected_gain = complex(2.0**-900)
        expected_logx, expected_logy = 0.0, -900.0
    else:
        bands[1:] = 2.0**-1000
        values[1:] = 2.0**100
        expected_gain = 0j
        expected_logx, expected_logy = 100.0, -1000.0
    candidate = invoke(public_fit, bands, calibration(values, (1.0, 1.0, 1.0))).candidates[0]
    assert candidate.order_status == ("fitted", "fitted")
    for gain in candidate.gains:
        assert gain.real == pytest.approx(expected_gain.real, rel=1e-12, abs=0)
        assert gain.imag == pytest.approx(expected_gain.imag, rel=1e-12, abs=0)
    assert candidate.objective == pytest.approx(0, abs=VALUE_ATOL**2)
    assert candidate.predictor_log2_norm == pytest.approx(
        (expected_logx, expected_logx), abs=VALUE_ATOL
    )
    assert candidate.response_log2_norm == pytest.approx(
        (expected_logy, expected_logy), abs=VALUE_ATOL
    )


def test_unrepresentable_gain_is_range_error_and_preserves_caller_policy(public_fit: Any) -> None:
    bands = np.ones((3, 1, 1, 1), dtype=np.complex128)
    bands[0] = 2.0**-1000
    bands[1:] = 2.0**1000
    cal = calibration(np.ones_like(bands), (1.0, 1.0, 1.0))
    before = bands.copy()
    old = np.geterr()
    old_filters = list(warnings.filters)
    try:
        np.seterr(all="raise")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with pytest.raises(simrecon.SimreconError) as error:
                invoke(public_fit, bands, cal)
            assert error.value.code == "unrepresentable_volume_overlap"
            assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
        assert np.geterr() == dict.fromkeys(old, "raise")
        assert warnings.filters == old_filters
        np.testing.assert_array_equal(bands, before)
    finally:
        np.seterr(**old)


def test_exact_geometric_products_with_overflowing_field_length(public_fit: Any) -> None:
    bands = np.ones((3, 1, 2, 2), dtype=np.complex128)
    cal = calibration(np.ones_like(bands), (1.0, 1.0e308, 1.0e308))
    carrier = (1.0e-308, -1.0e-308)
    bounds = np.array([carrier, carrier])
    expected = [overlap((1, 2, 2), cal.voxel_size_um, bounds, m) for m in (1, 2)]
    assert all(len(q) == 0 for q in expected)
    result = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=np.array([carrier]),
        carrier_bounds_per_um=bounds,
    )
    for got, want in zip(result.overlap_bins, expected, strict=True):
        np.testing.assert_array_equal(got, want)
    assert result.candidates[0].status == "unavailable"


def test_output_snapshots_record_bindings_and_input_preservation(public_fit: Any) -> None:
    bands, cal = arbitrary_case()
    bounds = np.array([[-0.12, -0.05], [0.13, 0.07]])
    starts = np.array([[0.02, 0.01], [0.02, 0.01]])
    step = np.array([1 / 1024, 1 / 1024])
    inputs = [bands, cal.values, cal.fz_per_um, cal.fy_per_um, cal.fx_per_um, bounds, starts, step]
    snapshots = [(a.copy(), a.strides, a.flags.writeable) for a in inputs]
    expected = evaluate(bands, cal, bounds, tuple(starts[0]))
    options = {
        "initial_carriers_per_um": starts,
        "carrier_bounds_per_um": bounds,
        "difference_step_per_um": step,
    }
    first = invoke(public_fit, bands, cal, **options)
    second = invoke(public_fit, bands, cal, **options)
    fit_type = getattr(simrecon, "VolumeOverlapFit", None)
    assert isinstance(fit_type, type)
    assert isinstance(first, fit_type)
    assert isinstance(first.candidates, tuple)
    assert isinstance(first.overlap_bins, tuple)
    candidate = first.candidates[0]
    candidate_type = getattr(simrecon, "VolumeOverlapCandidate", None)
    assert isinstance(candidate_type, type)
    assert isinstance(candidate, candidate_type)
    assert_point(candidate, expected)
    for array, (snapshot, strides, writable) in zip(inputs, snapshots, strict=True):
        np.testing.assert_array_equal(array, snapshot)
        assert array.strides == strides and array.flags.writeable == writable
    outputs = [
        first.carrier_bounds_per_um,
        *first.overlap_bins,
        *(c.information_singular_values for c in first.candidates),
    ]
    later = [
        second.carrier_bounds_per_um,
        *second.overlap_bins,
        *(c.information_singular_values for c in second.candidates),
    ]
    assert first.carrier_bounds_per_um.dtype == np.dtype("float64")
    for q in first.overlap_bins:
        assert q.dtype == np.dtype(np.intp) and q.ndim == 2 and q.shape[1] == 3
    for c in first.candidates:
        assert c.information_singular_values.dtype == np.dtype("float64")
        assert c.information_singular_values.shape == (2,)
    for i, out in enumerate(outputs):
        assert out.flags.owndata and out.flags.writeable and out.dtype.isnative
        for other in inputs + outputs[:i] + later:
            assert not np.shares_memory(out, other)
    for record, name in ((first, "source"), (candidate, "objective")):
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, name, getattr(record, name))
        with pytest.raises((AttributeError, TypeError)):
            delattr(record, name)
    first.carrier_bounds_per_um[:] = 99
    first.overlap_bins[0][:] = 99
    first.candidates[0].information_singular_values[:] = 99
    assert_point(second.candidates[0], expected)
    np.testing.assert_array_equal(second.carrier_bounds_per_um, bounds)
    bands[:] = 0
    cal.values[:] = 0
    starts[:] = 0
    bounds[:] = 0
    assert_point(second.candidates[0], expected)


def test_required_python_bindings(public_fit: Any) -> None:
    bands, cal = arbitrary_case()
    keywords = {
        "order_otf": cal,
        "initial_carriers_per_um": np.zeros((1, 2)),
        "carrier_bounds_per_um": np.zeros((2, 2)),
        "difference_step_per_um": np.ones(2),
        "gradient_tolerance": 0.0,
        "rank_rtol": 0.1,
        "max_evaluations": 1,
    }
    for omitted in keywords:
        args = dict(keywords)
        del args[omitted]
        with pytest.raises(TypeError):
            public_fit(bands, **args)
    with pytest.raises(TypeError):
        public_fit(bands, *keywords.values())
    with pytest.raises(TypeError):
        public_fit(bands, **keywords, extra_option=True)


def test_integer_gain_and_phase_separator_public_composition(public_fit: Any) -> None:
    bands, old = arbitrary_case((2, 4, 4))
    cal = calibration(old.values, (1.0, 1.0, 1.0))
    phases = np.array([0.0, 0.61, 1.7, 2.4, 3.3, 4.8, 5.9])
    c, s = np.cos(phases), np.sin(phases)
    images = np.asarray(
        [
            bands[0].real
            + 2 * bands[1].real * cp
            - 2 * bands[1].imag * sp
            + 2 * bands[2].real * (cp * cp - sp * sp)
            - 2 * bands[2].imag * ((2 * cp) * sp)
            for cp, sp in zip(c, s, strict=True)
        ]
    )
    separated = simrecon.separate_volume_phases(images, phases_rad=phases)
    actual_bands = np.array([separated.dc, separated.c1, separated.c2], dtype=np.complex128)
    carrier = (-0.25, 0.25)
    bounds = np.array([carrier, carrier])
    expected = evaluate(bands, cal, bounds, carrier)
    candidate = invoke(
        public_fit,
        actual_bands,
        cal,
        initial_carriers_per_um=np.array([carrier]),
        carrier_bounds_per_um=bounds,
    ).candidates[0]
    assert_point(candidate, expected)
    for m in (1, 2):
        integer = simrecon.estimate_volume_order_gain(
            images, order_otf=cal, phase_steps_rad=phases, carrier_bins_yx=(-1, 1), order=m
        )
        assert integer.gain == pytest.approx(expected.gains[m - 1], abs=VALUE_ATOL)
        assert candidate.gains[m - 1] == pytest.approx(integer.gain, abs=VALUE_ATOL)
        assert candidate.relative_residual[m - 1] == pytest.approx(
            integer.relative_residual, abs=VALUE_ATOL
        )
        assert integer.overlap_count == len(overlap((2, 4, 4), cal.voxel_size_um, bounds, m))


def test_calibration_gauge_brightness_and_independent_order_gains(public_fit: Any) -> None:
    control = recovery_control()
    bounds = np.array([control.truth, control.truth])
    expected = evaluate(control.bands, control.calibration, bounds, control.truth)
    values = control.calibration.values.copy() * (0.4 + 0.7j)
    # A different nominal phase in each positive row changes its relative
    # correction once; order two need not be the square of order one.
    phase_factors = (0.6 + 0.8j, -0.8 + 0.6j)
    values[1] *= phase_factors[0]
    values[2] *= phase_factors[1]
    cal = replace_calibration(control.calibration, values=values, origin_zyx=(1, 2, 3))
    corrected_gains = []
    for gain, factor in zip(expected.gains, phase_factors, strict=True):
        assert gain is not None
        corrected_gains.append(gain / factor)
    candidate = invoke(
        public_fit,
        control.bands * 3,
        cal,
        initial_carriers_per_um=np.array([control.truth]),
        carrier_bounds_per_um=bounds,
    ).candidates[0]
    assert candidate.gains == pytest.approx(corrected_gains, abs=VALUE_ATOL)
    assert candidate.objective < VALUE_ATOL**2
    assert abs(candidate.gains[1] - candidate.gains[0] ** 2) > 0.1


@pytest.mark.parametrize("noise", [False, True])
def test_declared_local_recovery_and_independent_full_field_prediction(
    public_fit: Any, noise: bool
) -> None:
    control = recovery_control(noise=noise)
    truth_field = field_prediction(control, control.truth, control.gains)
    truth_heldout = field_prediction(control, control.truth, control.gains, heldout=True)
    nominal_objective = evaluate(
        control.bands, control.calibration, control.bounds, tuple(control.starts[0])
    ).objective
    # All truth, starts, basin and allowances above are frozen before this call.
    result = invoke(
        public_fit,
        control.bands,
        control.calibration,
        initial_carriers_per_um=control.starts,
        carrier_bounds_per_um=control.bounds,
        difference_step_per_um=control.step,
        gradient_tolerance=1e-6,
        rank_rtol=1e-6,
        max_evaluations=256,
    )
    candidate = result.candidates[0]
    assert candidate.objective < nominal_objective / 20
    assert candidate.gains == pytest.approx(control.gains, abs=RECOVERY_GAIN_ATOL)
    assert candidate.diagnostics_continuous is True
    assert candidate.information_rank == 2
    assert candidate.global_ambiguity == "unresolved"
    assert 1 <= candidate.search_evaluations <= 256
    # No phase offset, truth reinitialization or post-fit alignment is allowed.
    _, y, x = np.indices(control.specimen.shape)
    carrier_error = np.asarray(candidate.carrier_per_um) - control.truth
    for m in (1, 2):
        phase_error = (
            2
            * np.pi
            * m
            * (
                carrier_error[0] * control.calibration.voxel_size_um[1] * y
                + carrier_error[1] * control.calibration.voxel_size_um[2] * x
            )
        )
        assert np.max(np.abs(phase_error)) <= RECOVERY_PHASE_ATOL
    predicted = field_prediction(control, candidate.carrier_per_um, candidate.gains)
    predicted_heldout = field_prediction(
        control, candidate.carrier_per_um, candidate.gains, heldout=True
    )
    # |g_hat*exp(i*dphi)-g| <= |dg| + |g|*|dphi|, per voxel.
    for m in (1, 2):
        transfer = abs(control.calibration.values[m, 0, 0, 0])
        allowance = (
            transfer
            * np.max(control.specimen)
            * (RECOVERY_GAIN_ATOL + abs(control.gains[m - 1]) * RECOVERY_PHASE_ATOL)
        )
        heldout_allowance = (
            transfer
            * np.max(control.heldout_specimen)
            * (RECOVERY_GAIN_ATOL + abs(control.gains[m - 1]) * RECOVERY_PHASE_ATOL)
        )
        assert np.max(np.abs(predicted[m - 1] - truth_field[m - 1])) <= allowance
        assert np.max(np.abs(predicted_heldout[m - 1] - truth_heldout[m - 1])) <= heldout_allowance
    at_returned = evaluate(
        control.bands, control.calibration, control.bounds, candidate.carrier_per_um
    )
    assert_point(candidate, at_returned)


def test_nonconstant_transfer_windowing_mismatch_is_not_physical_recovery(public_fit: Any) -> None:
    bands, cal, bounds, truth = nonconstant_transfer_control()
    expected = evaluate(bands, cal, bounds, truth)
    assert expected.objective > 1e-5  # model limitation precomputed, not fitted away
    candidate = invoke(
        public_fit,
        bands,
        cal,
        initial_carriers_per_um=np.array([truth]),
        carrier_bounds_per_um=bounds,
    ).candidates[0]
    assert_point(candidate, expected)
    assert candidate.global_ambiguity == "unresolved"
