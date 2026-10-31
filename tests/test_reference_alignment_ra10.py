"""Blind public-contract tests for RA10, with independent finite raw oracles.

P01–P16 mapping and pre-observation tolerances are in A1/design.md and handoff.
Named positive controls require recovery; other starts preserve failed attempts.
"""

import copy
import warnings
from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from reference_alignment_ra10_fixture import (
    RECOVERY_HELDOUT_ATOL,
    RECOVERY_PHASE_ATOL_RAD,
    Arguments,
    Oracle,
    band_matrix,
    cutoff_sensitivity_controls,
    make_case,
    make_recovery_case,
    oracle,
    phases_for,
    reimage,
    secant_oracle,
)
from simrecon import (
    ExposurePhaseCandidate,
    ExposurePhaseFit,
    SimreconError,
    fit_exposure_phases,
)


def fit(arguments: Arguments) -> Any:
    keywords = arguments.copy()
    images = keywords.pop("images")
    return fit_exposure_phases(images, **keywords)


def close(actual: Any, expected: Any, allowance: float) -> None:
    scale = max(1.0, float(np.linalg.norm(np.asarray(expected).reshape(-1))))
    assert_allclose(actual, expected, rtol=allowance, atol=allowance * scale)


def assert_candidate(arguments: Arguments, candidate: Any, seed: Any) -> Oracle:
    """One strongest boundary proof for raw fit, diagnostics and search policy."""
    assert isinstance(candidate, ExposurePhaseCandidate)
    offsets = candidate.offsets_rad
    assert_array_equal(candidate.initial_offsets_rad, seed)
    assert np.all(offsets >= arguments["offset_bounds_rad"][0])
    assert np.all(offsets <= arguments["offset_bounds_rad"][1])
    expected = oracle(arguments, offsets)
    close(candidate.phases_rad, phases_for(arguments, offsets), 2e-14)
    for name, value in (
        ("source", expected.source),
        ("predicted_images", expected.prediction),
        ("residual_images", expected.residual),
        ("source_singular_values", expected.source_singular),
        ("phase_singular_values", expected.phase_singular),
        ("objective", expected.objective),
    ):
        close(getattr(candidate, name), value, expected.allowance)
    assert candidate.source_rank == expected.source_rank
    assert candidate.free_parameter_count == expected.free
    # Independent singular-value accuracy and the exact returned rank rule are
    # separate claims. Structural near-zero projections need absolute budgets.
    values = candidate.phase_singular_values
    rank_from_values = (
        int(np.count_nonzero(values > arguments["phase_rank_rtol"] * values[0]))
        if values.size and values[0] > 0
        else 0
    )
    assert candidate.phase_rank == rank_from_values
    if expected.phase_singular.size and expected.phase_singular[0] > 100 * expected.allowance:
        margins = np.abs(
            expected.phase_singular / expected.phase_singular[0] - arguments["phase_rank_rtol"]
        )
        assert np.min(margins) >= 1e-8
        assert candidate.phase_rank == expected.phase_rank
    metric, continuous, diagnostic_count, metric_error = secant_oracle(arguments, offsets, expected)
    assert_allclose(
        candidate.projected_gradient,
        metric,
        rtol=expected.allowance,
        atol=max(metric_error, expected.allowance),
    )
    assert candidate.diagnostics_continuous is continuous
    assert candidate.diagnostic_evaluations == diagnostic_count
    assert candidate.stationary is bool(
        candidate.diagnostics_continuous
        and candidate.projected_gradient <= arguments["gradient_tolerance"]
    )
    known = arguments["mode"] == "known"
    if known:
        information = "known"
    elif not np.any(arguments["fit_mask"]):
        information = "no_training_data"
    elif expected.free == 0:
        information = "no_free_parameters"
    else:
        information = (
            "full_local_rank" if candidate.phase_rank == expected.free else "rank_deficient"
        )
    assert candidate.information_status == information
    assert candidate.global_ambiguity == ("not_inferred" if known else "unresolved")
    assert 1 <= candidate.search_evaluations <= arguments["max_evaluations"]
    if known or expected.free == 0:
        assert candidate.search_evaluations == 1
    status = (
        "known"
        if known
        else "fixed"
        if expected.free == 0
        else "stationary"
        if candidate.stationary
        else "evaluation_limit"
        if candidate.search_evaluations == arguments["max_evaluations"]
        else "stopped"
    )
    assert candidate.search_status == status
    initial = oracle(arguments, np.asarray(seed, dtype=np.float64))
    assert candidate.objective <= initial.objective + initial.allowance * max(
        1.0, initial.objective
    )
    mode = arguments["mode"]
    if known:
        assert candidate.common_offset_rad is None
        assert_array_equal(
            candidate.independent_deviations_rad, np.zeros(len(candidate.phases_rad))
        )
    else:
        assert type(candidate.common_offset_rad) is float
        assert candidate.common_offset_rad == float(offsets[0])
        close(
            candidate.independent_deviations_rad,
            offsets - offsets[0] if mode == "independent" else np.zeros(len(candidate.phases_rad)),
            2e-14,
        )
    for name in ("objective", "projected_gradient"):
        assert type(getattr(candidate, name)) is float
        assert np.isfinite(getattr(candidate, name))
    for name in (
        "source_rank",
        "phase_rank",
        "free_parameter_count",
        "search_evaluations",
        "diagnostic_evaluations",
    ):
        assert type(getattr(candidate, name)) is int
    for name in ("stationary", "diagnostics_continuous"):
        assert type(getattr(candidate, name)) is bool
    return expected


def assert_fit(arguments: Arguments, result: Any) -> list[Oracle]:
    assert isinstance(result, ExposurePhaseFit)
    assert result.mode == arguments["mode"]
    assert_array_equal(result.input_phases_rad, arguments["phases_rad"])
    assert_array_equal(result.fit_mask, arguments["fit_mask"])
    assert type(result.carrier_per_um_yx) is tuple
    assert type(result.source_spacing_um_zyx) is tuple
    assert result.carrier_per_um_yx == tuple(arguments["carrier_per_um_yx"])
    assert result.source_spacing_um_zyx == arguments["source_spacing_um_zyx"]
    assert type(result.candidates) is tuple
    assert len(result.candidates) == len(arguments["initial_offsets_rad"])
    return [
        assert_candidate(arguments, candidate, seed)
        for candidate, seed in zip(result.candidates, arguments["initial_offsets_rad"], strict=True)
    ]


def test_known_monitor_finite_geometry_and_covariance() -> None:
    """P01/P03–P07/P09/P11/P14/P15: full 3D exterior-zero raw reference."""
    case = make_case()
    result = fit(case.arguments)
    expected = assert_fit(case.arguments, result)[0]
    assert expected.source_rank == case.source.size
    close(result.candidates[0].source, case.source, expected.allowance)
    close(result.candidates[0].predicted_images, case.arguments["images"], expected.allowance)
    assert result.candidates[0].phases_rad[0] != 0
    # Monitor labels are actual observations. Commands alone are a wrong control.
    commands = copy.deepcopy(case.arguments)
    commands["phases_rad"] -= np.array([0.27, -0.23, 0.19, 0.42, -0.36, 0.14, -0.09])
    command_result = fit(commands)
    assert_fit(commands, command_result)
    assert command_result.candidates[0].objective > 1e-5


@pytest.mark.parametrize("mode", ["common", "independent"])
def test_search_common_and_independent_positive_recovery(mode: str) -> None:
    """P07–P11/P15/P16: command-start positive inference and held-out prediction."""
    case = make_recovery_case(mode)
    result = fit(case.arguments)
    expected = assert_fit(case.arguments, result)
    assert all(item.phase_rank == item.free for item in expected)
    actual_offsets = case.actual_phases - case.arguments["phases_rad"]
    if mode == "common":
        actual_offsets = actual_offsets[:1]
    # Truth is used only by the independent evaluator, never as a product seed.
    truth_profile = oracle(case.arguments, actual_offsets)
    close(truth_profile.source, case.source, truth_profile.allowance)
    assert truth_profile.objective < 1e-24
    # The first caller start is the command-only zero-offset control. Neither
    # truth nor a returned objective/success flag chooses the tested candidate.
    candidate = result.candidates[0]
    assert_array_equal(candidate.initial_offsets_rad, np.zeros_like(actual_offsets))
    assert np.max(np.abs(case.arguments["phases_rad"] - case.actual_phases)) > 0.15
    assert_allclose(candidate.phases_rad, case.actual_phases, rtol=0, atol=RECOVERY_PHASE_ATOL_RAD)
    mask = case.arguments["fit_mask"]
    assert np.any(mask) and np.any(~mask)
    assert_allclose(
        candidate.predicted_images[:, ~mask],
        case.arguments["images"][:, ~mask],
        rtol=0,
        atol=RECOVERY_HELDOUT_ATOL,
    )
    assert candidate.global_ambiguity == "unresolved"


def test_noise_cutoff_minimum_norm_and_covariance_gauge() -> None:
    """P05/P06/P16: signed/noisy source, discarded directions and raw J."""
    case = make_case()
    arguments = case.arguments
    arguments["images"] += np.linspace(-0.07, 0.09, arguments["images"].size).reshape(
        arguments["images"].shape
    )
    arguments["source_rtol"] = 0.24
    result = fit(arguments)
    expected = assert_fit(arguments, result)[0]
    assert 0 < expected.source_rank < case.source.size
    assert result.candidates[0].objective > 0
    assert np.min(result.candidates[0].source) < 0
    diagonal = copy.deepcopy(arguments)
    diagonal["exposure_covariance"] = np.diag(np.diag(arguments["exposure_covariance"]))
    diagonal_expected = assert_fit(diagonal, fit(diagonal))[0]
    assert np.linalg.norm(expected.source - diagonal_expected.source) > 1e-4
    # A signal-gauge change is not a candidate-energy normalization.
    scaled = copy.deepcopy(arguments)
    scaled["images"] *= 2.5
    scaled["exposure_covariance"] *= 2.5**2
    scaled_candidate = fit(scaled).candidates[0]
    scaled_expected = assert_candidate(scaled, scaled_candidate, scaled["initial_offsets_rad"][0])
    close(scaled_candidate.source, 2.5 * result.candidates[0].source, scaled_expected.allowance)
    close(scaled_candidate.objective, result.candidates[0].objective, scaled_expected.allowance)


def strict_cutoff_arguments() -> Arguments:
    """Construct an exactly diagonal known-phase design with singulars 1, 1/2."""
    arguments = make_case("known", n=1).arguments
    arguments.update(
        images=np.array([-1.0, 2.0]).reshape(1, 1, 1, 2),
        order_kernels=np.array([0.75, 0.125, 0.0], dtype=np.complex128).reshape(3, 1, 1, 1),
        kernel_origin_zyx=(0, 0, 0),
        source_shape_zyx=(1, 1, 2),
        detector_crop_zyx=((0, 1), (0, 1), (0, 2)),
        source_spacing_um_zyx=(1.0, 1.0, 1.0),
        carrier_per_um_yx=np.array([0.0, 0.5]),
        fit_mask=np.ones((1, 1, 2), dtype=bool),
        phases_rad=np.zeros(1),
        source_rtol=0.5,
    )
    return arguments


def test_source_cutoff_is_strict_and_discarded_component_stays_discarded() -> None:
    """P06: exact cutoff is outside separated-cutoff regime but representable."""
    arguments = strict_cutoff_arguments()
    candidate = fit(arguments).candidates[0]
    # Exact simple arithmetic independently fixes the oracle at the boundary;
    # the general oracle deliberately rejects cutoff-near fixtures.
    assert_array_equal(candidate.source_singular_values, [1.0, 0.5])
    assert candidate.source_rank == 1
    close(candidate.source, np.array([-1.0, 0.0]).reshape(1, 1, 2), 2e-14)
    close(candidate.predicted_images, np.array([-1.0, 0.0]).reshape(1, 1, 1, 2), 2e-14)
    assert candidate.objective == 1.0


def test_held_out_data_never_enter_training_or_phase_diagnostics() -> None:
    """P05/P16: change only false-mask sites, preserve all fitted quantities."""
    case = make_case("independent")
    case.arguments["max_evaluations"] = 1
    result = fit(case.arguments)
    assert_fit(case.arguments, result)
    changed = copy.deepcopy(case.arguments)
    changed["images"][:, ~changed["fit_mask"]] += np.arange(1, 8)[:, None] * 0.8
    other = fit(changed)
    assert_fit(changed, other)
    for before, after in zip(result.candidates, other.candidates, strict=True):
        for name in (
            "offsets_rad",
            "source",
            "predicted_images",
            "objective",
            "source_singular_values",
            "phase_singular_values",
            "projected_gradient",
        ):
            close(getattr(before, name), getattr(after, name), 2e-11)
        assert_array_equal(
            before.residual_images[:, case.arguments["fit_mask"]],
            after.residual_images[:, case.arguments["fit_mask"]],
        )
        assert np.linalg.norm(before.residual_images - after.residual_images) > 1


@pytest.mark.parametrize("mode", ["known", "common", "independent"])
def test_no_training_data_is_explicitly_unavailable(mode: str) -> None:
    """P05/P06/P09/P10: valid empty mask, including status precedence."""
    case = make_case(mode)
    case.arguments["fit_mask"][:] = False
    case.arguments["max_evaluations"] = 1
    result = fit(case.arguments)
    assert_fit(case.arguments, result)
    for candidate in result.candidates:
        assert_array_equal(candidate.source, np.zeros(case.source.shape))
        assert_array_equal(candidate.predicted_images, np.zeros_like(case.arguments["images"]))
        assert candidate.objective == 0.0
        assert candidate.source_rank == candidate.phase_rank == 0
        assert candidate.stationary


def test_fixed_boxes_and_partial_free_directions() -> None:
    """P07/P09/P10: fixed precedence; tangent directions exclude fixed axes."""
    case = make_case("independent")
    case.arguments["initial_offsets_rad"] = np.array([[0.18] * 7])
    case.arguments["offset_bounds_rad"][:] = 0.18
    result = fit(case.arguments)
    assert_fit(case.arguments, result)
    candidate = result.candidates[0]
    assert candidate.search_status == "fixed"
    assert candidate.information_status == "no_free_parameters"
    assert candidate.projected_gradient == 0.0
    assert candidate.diagnostic_evaluations == 0
    partial = copy.deepcopy(case.arguments)
    partial["offset_bounds_rad"][:, [1, 4]] = np.array([[-0.6], [0.6]])
    partial["max_evaluations"] = 1
    partial_result = fit(partial)
    assert_fit(partial, partial_result)
    assert partial_result.candidates[0].free_parameter_count == 2
    assert partial_result.candidates[0].phase_singular_values.shape == (2,)


@pytest.mark.parametrize("seed", [-0.6, 0.6, 0.0])
def test_one_evaluation_budget_keeps_seed_and_feasible_secants(seed: float) -> None:
    """P08/P09: seed counts, boundary one-sided secants, no diagnostic update."""
    case = make_case("common")
    case.arguments["initial_offsets_rad"] = np.array([[seed]])
    case.arguments["max_evaluations"] = 1
    case.arguments["gradient_tolerance"] = 0.0
    result = fit(case.arguments)
    expected = assert_fit(case.arguments, result)[0]
    candidate = result.candidates[0]
    assert_array_equal(candidate.offsets_rad, [seed])
    assert candidate.search_evaluations == 1
    assert candidate.diagnostic_evaluations == (2 if seed == 0 else 1)
    metric, _, _, _ = secant_oracle(case.arguments, candidate.offsets_rad, expected)
    assert metric > 1e-5
    assert not candidate.stationary
    assert candidate.search_status == "evaluation_limit"


def test_rank_change_secants_are_not_stationary_even_with_loose_tolerance() -> None:
    """P09: an exactly zero retained design can gain rank at neighbors."""
    case = make_case("common", n=1)
    arguments = case.arguments
    arguments.update(
        images=np.ones((1, 1, 1, 1)),
        order_kernels=np.array([0.0, 1j, 0.0], dtype=np.complex128).reshape(3, 1, 1, 1),
        kernel_origin_zyx=(0, 0, 0),
        source_shape_zyx=(1, 1, 1),
        detector_crop_zyx=((0, 1), (0, 1), (0, 1)),
        fit_mask=np.ones((1, 1, 1), dtype=bool),
        phases_rad=np.zeros(1),
        initial_offsets_rad=np.zeros((1, 1)),
        gradient_tolerance=1e20,
        max_evaluations=1,
    )
    result = fit(arguments)
    assert_fit(arguments, result)
    candidate = result.candidates[0]
    assert candidate.source_rank == 0
    assert not candidate.diagnostics_continuous
    assert not candidate.stationary
    assert candidate.search_status == "evaluation_limit"


def test_informative_weak_and_unavailable_phase_information() -> None:
    """P10/P12: absolute information scale, absent harmonics and zero model."""
    case = make_case("common")
    case.arguments["initial_offsets_rad"] = np.zeros((1, 1))
    case.arguments["max_evaluations"] = 1
    strong = fit(case.arguments)
    assert_fit(case.arguments, strong)
    weak = copy.deepcopy(case.arguments)
    weak["images"] *= 1e-5
    weak_result = fit(weak)
    assert_fit(weak, weak_result)
    close(
        weak_result.candidates[0].phase_singular_values,
        1e-5 * strong.candidates[0].phase_singular_values,
        2e-11,
    )
    assert strong.candidates[0].phase_rank == weak_result.candidates[0].phase_rank == 1
    assert weak_result.candidates[0].phase_singular_values[0] < 1e-5
    absent = copy.deepcopy(case.arguments)
    absent["order_kernels"][1:] = 0
    absent_result = fit(absent)
    assert_fit(absent, absent_result)
    candidate = absent_result.candidates[0]
    assert candidate.phase_rank == 0
    assert candidate.information_status == "rank_deficient"
    assert candidate.stationary
    zero = copy.deepcopy(absent)
    zero["order_kernels"][:] = 0
    zero_result = fit(zero)
    assert_fit(zero, zero_result)
    assert zero_result.candidates[0].source_rank == 0
    assert zero_result.candidates[0].objective > 0
    zero["images"][:] = 0
    zero_data = fit(zero)
    assert_fit(zero, zero_data)
    assert zero_data.candidates[0].objective == 0


def test_active_cutoff_uses_frozen_retained_source_subspace() -> None:
    """P10: discarded nonzero source directions do not enter this conditional E."""
    case = make_case("common")
    arguments = case.arguments
    arguments["source_rtol"] = 0.24
    arguments["initial_offsets_rad"] = np.zeros((1, 1))
    arguments["max_evaluations"] = 1
    offsets = np.zeros(1)
    expected = oracle(arguments, offsets)
    all_source, profile_h, profile_half_h, margin = cutoff_sensitivity_controls(arguments, offsets)
    assert expected.source_rank == 10 < case.source.size
    assert expected.phase_rank == expected.free == 1
    assert margin > 0.005
    required = float(expected.phase_singular[0])
    # Finite-difference derivative accuracy is separate from stored-input E.
    # h^2 truncation plus two propagated profile errors divided by h/2 fits
    # 1e-5 here; the wrong definitions differ by more than 0.01 signal/rad.
    assert abs(profile_h - profile_half_h) < 1e-5
    assert abs(required - all_source) > 0.01
    assert abs(required - profile_half_h) > 0.01
    result = fit(arguments)
    assert_fit(arguments, result)
    candidate = result.candidates[0]
    assert_array_equal(candidate.offsets_rad, offsets)
    assert_allclose(
        candidate.phase_singular_values,
        expected.phase_singular,
        rtol=expected.allowance,
        atol=expected.allowance,
    )
    # This is the declared cutoff-conditional status, not identifiability of
    # the unrestricted source or a derivative of the profiled residual.
    assert candidate.information_status == "full_local_rank"
    assert candidate.global_ambiguity == "unresolved"


def test_calibration_gauge_equivalence_and_unwrapped_output() -> None:
    """P04/P11: fixed input gauge; no fitted first-phase alignment."""
    case = make_case("independent")
    case.arguments["max_evaluations"] = 1
    result = fit(case.arguments)
    assert_fit(case.arguments, result)
    transformed = copy.deepcopy(case.arguments)
    gamma = 0.73
    for order in (1, 2):
        transformed["order_kernels"][order] *= np.exp(-1j * order * gamma)
    transformed["phases_rad"] += gamma
    other = fit(transformed)
    assert_fit(transformed, other)
    for before, after in zip(result.candidates, other.candidates, strict=True):
        close(after.source, before.source, 2e-10)
        close(after.predicted_images, before.predicted_images, 2e-10)
        close(after.phases_rad, before.phases_rad + gamma, 2e-14)
        close(after.offsets_rad, before.offsets_rad, 2e-14)
    shifted = copy.deepcopy(case.arguments)
    shifted["phases_rad"] += 2 * np.pi
    shifted_result = fit(shifted)
    assert_fit(shifted, shifted_result)
    for before, after in zip(result.candidates, shifted_result.candidates, strict=True):
        close(after.predicted_images, before.predicted_images, 2e-10)
        close(after.phases_rad, before.phases_rad + 2 * np.pi, 2e-14)
        assert after.phases_rad[0] > 2 * np.pi


def test_all_starts_duplicates_and_second_order_aliases_are_preserved() -> None:
    """P08/P12: retain caller order, equivalent alternatives and exact ties."""
    case = make_case("common", n=5)
    arguments = case.arguments
    arguments["order_kernels"][1] = 0
    reimage(case)
    arguments["initial_offsets_rad"] = np.array([[0.0], [np.pi], [0.0], [2 * np.pi]])
    arguments["offset_bounds_rad"] = np.array([[-1.0], [8.0]])
    arguments["max_evaluations"] = 1
    result = fit(arguments)
    assert_fit(arguments, result)
    assert len(result.candidates) == 4
    for candidate, seed in zip(result.candidates, arguments["initial_offsets_rad"], strict=True):
        assert_array_equal(candidate.offsets_rad, seed)
        close(candidate.predicted_images, result.candidates[0].predicted_images, 2e-10)
        assert candidate.global_ambiguity == "unresolved"
    flat = copy.deepcopy(arguments)
    flat["order_kernels"][:] = 0
    flat["max_evaluations"] = 16
    flat_result = fit(flat)
    assert_fit(flat, flat_result)
    for candidate, seed in zip(flat_result.candidates, flat["initial_offsets_rad"], strict=True):
        assert_array_equal(candidate.offsets_rad, seed)


def test_five_arbitrary_bands_do_not_identify_phases() -> None:
    """P12: algebraic alternative; conditional shared source is a restriction."""
    case = make_case("independent", n=5)
    case.arguments["max_evaluations"] = 1
    # Both phase designs were fixed independently of the observed image values.
    alternative_phases = np.array([0.12, 1.29, 2.42, 3.91, 5.36])
    observed = case.arguments["images"].reshape(5, -1)
    original_design = band_matrix(case.actual_phases)
    alternative_design = band_matrix(alternative_phases)
    assert np.linalg.cond(original_design) < 20
    assert np.linalg.cond(alternative_design) < 20
    original_coefficients = np.linalg.solve(original_design, observed)
    alternative_coefficients = np.linalg.solve(alternative_design, observed)
    assert_allclose(original_design @ original_coefficients, observed, rtol=2e-12, atol=2e-12)
    assert_allclose(alternative_design @ alternative_coefficients, observed, rtol=2e-12, atol=2e-12)
    assert np.linalg.norm(original_coefficients - alternative_coefficients) > 0.1
    result = fit(case.arguments)
    assert_fit(case.arguments, result)
    for candidate in result.candidates:
        assert candidate.phase_rank == 5
        assert candidate.information_status == "full_local_rank"
        assert candidate.global_ambiguity == "unresolved"
        assert candidate.objective > 1e-6


def test_redundant_frames_do_not_create_a_uniqueness_claim() -> None:
    """P10/P12: repeated independent observations preserve normalized tangent."""
    case = make_case("common", n=5)
    arguments = case.arguments
    arguments["exposure_covariance"] = np.eye(5)
    arguments["initial_offsets_rad"] = np.zeros((1, 1))
    arguments["max_evaluations"] = 1
    single = fit(arguments)
    assert_fit(arguments, single)
    repeated = copy.deepcopy(arguments)
    repeated["images"] = np.tile(arguments["images"], (2, 1, 1, 1))
    repeated["phases_rad"] = np.tile(arguments["phases_rad"], 2)
    repeated["exposure_covariance"] = np.eye(10)
    doubled = fit(repeated)
    assert_fit(repeated, doubled)
    a, b = single.candidates[0], doubled.candidates[0]
    close(a.source, b.source, 2e-10)
    close(a.objective, b.objective, 2e-10)
    close(a.phase_singular_values, b.phase_singular_values, 2e-10)
    close(b.source_singular_values, np.sqrt(2) * a.source_singular_values, 2e-10)
    assert a.phase_rank == b.phase_rank == 1
    assert b.global_ambiguity == "unresolved"


def all_output_arrays(result: Any) -> list[Any]:
    arrays = [result.input_phases_rad, result.fit_mask]
    for candidate in result.candidates:
        arrays.extend(
            getattr(candidate, name)
            for name in (
                "initial_offsets_rad",
                "offsets_rad",
                "phases_rad",
                "independent_deviations_rad",
                "source",
                "predicted_images",
                "residual_images",
                "source_singular_values",
                "phase_singular_values",
            )
        )
    return arrays


@pytest.mark.parametrize("mode", ["known", "common", "independent"])
def test_owned_snapshots_frozen_bindings_and_ambient_state(mode: str) -> None:
    """P01/P13: mutable independent arrays; frozen field bindings, no effects."""
    case = make_case(mode)
    case.arguments["max_evaluations"] = 1
    caller_arrays = [value for value in case.arguments.values() if isinstance(value, np.ndarray)]
    for array in caller_arrays:
        array.flags.writeable = False
    snapshots = [array.copy() for array in caller_arrays]
    previous_policy = np.seterr(all="raise")
    filters = warnings.filters[:]
    try:
        first, second = fit(case.arguments), fit(case.arguments)
        assert np.geterr() == dict.fromkeys(("divide", "over", "under", "invalid"), "raise")
        assert warnings.filters == filters
        assert_fit(case.arguments, first)
        for array, snapshot in zip(caller_arrays, snapshots, strict=True):
            assert_array_equal(array, snapshot)
            assert not array.flags.writeable
        arrays = all_output_arrays(first) + all_output_arrays(second)
        for i, array in enumerate(arrays):
            assert type(array) is np.ndarray
            assert array.dtype == (
                np.dtype(bool)
                if array is first.fit_mask or array is second.fit_mask
                else np.dtype(np.float64)
            )
            assert array.dtype.isnative
            assert array.flags.c_contiguous and array.flags.writeable
            assert np.all(np.isfinite(array))
            for other in arrays[i + 1 :] + caller_arrays:
                assert array is not other
                assert not np.shares_memory(array, other)
        with pytest.raises((AttributeError, FrozenInstanceError)):
            first.mode = "known"
        with pytest.raises((AttributeError, FrozenInstanceError)):
            first.candidates[0].objective = 0.0
        second_snapshots = [array.copy() for array in all_output_arrays(second)]
        for array in all_output_arrays(first):
            array[...] = False if array.dtype == bool else 123.0
        for array, snapshot in zip(all_output_arrays(second), second_snapshots, strict=True):
            assert_array_equal(array, snapshot)
    finally:
        np.seterr(**previous_policy)


@pytest.mark.parametrize(
    "layout", ["big_endian", "fortran", "strided", "integer", "float16", "float32", "longdouble"]
)
def test_permitted_numeric_layouts_and_scalar_widths(layout: str) -> None:
    """P02: paired valid values defeat overbroad type/layout rejection."""
    case = make_case()
    if layout == "integer":
        # These controls describe a different valid scene, not rounded truth.
        case.arguments["carrier_per_um_yx"] = np.array([0, 0], dtype=np.int16)
        case.arguments["phases_rad"] = np.array([0, 1, 2, 3, 4, 5, 6], dtype=np.uint8)
        case.arguments["images"] = np.arange(56, dtype=np.int8).reshape(7, 2, 2, 2) % 11 - 5
        case.arguments["exposure_covariance"] = np.eye(7, dtype=np.uint16)
    else:
        for key, value in list(case.arguments.items()):
            if not isinstance(value, np.ndarray) or value.dtype == bool:
                continue
            if layout == "big_endian":
                case.arguments[key] = value.astype(value.dtype.newbyteorder(">"))
            elif layout == "fortran":
                case.arguments[key] = np.asfortranarray(value)
            elif layout in ("float16", "float32", "longdouble") and value.dtype.kind != "c":
                dtype = {"float16": np.float16, "float32": np.float32, "longdouble": np.longdouble}[
                    layout
                ]
                case.arguments[key] = value.astype(dtype)
            elif layout == "strided":
                holder = np.empty((*value.shape, 2), dtype=value.dtype)
                holder[..., 0] = value
                case.arguments[key] = holder[..., 0]
    case.arguments["source_rtol"] = np.float32(1e-6)
    case.arguments["phase_rank_rtol"] = np.float64(1e-6)
    case.arguments["gradient_tolerance"] = np.int64(0)
    case.arguments["max_evaluations"] = np.uint16(2)
    assert_fit(case.arguments, fit(case.arguments))


def test_no_artificial_exposure_or_start_cap_on_small_zero_model() -> None:
    """P02/P08: >12 exposures and >4 seeds are valid beyond mandatory bounds."""
    arguments = make_case("common").arguments
    arguments.update(
        images=np.zeros((13, 1, 1, 1)),
        order_kernels=np.zeros((3, 1, 1, 1), dtype=np.complex128),
        kernel_origin_zyx=(0, 0, 0),
        source_shape_zyx=(1, 1, 1),
        detector_crop_zyx=((0, 1), (0, 1), (0, 1)),
        fit_mask=np.ones((1, 1, 1), dtype=bool),
        phases_rad=np.linspace(0.0, 7.2, 13),
        exposure_covariance=np.eye(13),
        initial_offsets_rad=np.array([[-0.5], [0.25], [0.0], [0.25], [0.5]]),
        max_evaluations=1,
    )
    result = fit(arguments)
    assert_fit(arguments, result)
    assert len(result.candidates) == 5


def test_large_representable_known_angles_have_bounded_finite_model() -> None:
    """P04/P14: require finite evaluation, without claiming huge-angle accuracy."""
    arguments = make_case("known", n=1).arguments
    arguments.update(
        images=np.ones((1, 1, 1, 1)),
        order_kernels=np.array([2.0, 0.1, 0.05], dtype=np.complex128).reshape(3, 1, 1, 1),
        kernel_origin_zyx=(0, 0, 0),
        source_shape_zyx=(1, 1, 1),
        detector_crop_zyx=((0, 1), (0, 1), (0, 1)),
        fit_mask=np.ones((1, 1, 1), dtype=bool),
        carrier_per_um_yx=np.zeros(2),
        phases_rad=np.array([1e100]),
    )
    result = fit(arguments)
    candidate = result.candidates[0]
    assert_array_equal(candidate.phases_rad, arguments["phases_rad"])
    # For any reduced argument, 1.7 <= 2 + .2*cos(phi) + .1*cos(2phi) <= 2.3.
    assert 1 / 2.3 - 1e-12 <= float(candidate.source.item()) <= 1 / 1.7 + 1e-12
    close(candidate.predicted_images, arguments["images"], 2e-12)
    assert candidate.objective < 1e-24
    assert candidate.search_status == "known"


class ArraySubclass(np.ndarray):
    """Invalid array subclass; accepted data must use the plain ndarray type."""


def invalid_arguments(name: str) -> Arguments:
    arguments = make_case("independent").arguments
    replacements: dict[str, tuple[str, Any]] = {
        "mode": ("mode", "Independent"),
        "images_list": ("images", arguments["images"].tolist()),
        "images_bool": ("images", np.ones((7, 2, 2, 2), dtype=bool)),
        "images_complex": ("images", arguments["images"].astype(np.complex128)),
        "images_object": ("images", arguments["images"].astype(object)),
        "images_subclass": ("images", arguments["images"].view(ArraySubclass)),
        "images_masked": ("images", np.ma.array(arguments["images"])),
        "images_shape": ("images", np.zeros((7, 2, 2))),
        "images_nonfinite": ("images", np.full((7, 2, 2, 2), np.nan)),
        "no_exposures": ("images", np.zeros((0, 2, 2, 2))),
        "kernel_real": ("order_kernels", arguments["order_kernels"].real.copy()),
        "kernel_complex64": ("order_kernels", arguments["order_kernels"].astype(np.complex64)),
        "kernel_zero_imag": ("order_kernels", arguments["order_kernels"].copy()),
        "kernel_nonfinite": ("order_kernels", np.full((3, 2, 3, 4), complex(0, np.inf))),
        "kernel_order_count": ("order_kernels", np.zeros((2, 2, 3, 4), dtype=np.complex128)),
        "kernel_empty_axis": ("order_kernels", np.zeros((3, 0, 3, 4), dtype=np.complex128)),
        "shape_list": ("source_shape_zyx", [2, 2, 3]),
        "shape_bool": ("source_shape_zyx", (True, 2, 3)),
        "shape_numpy_int": ("source_shape_zyx", (np.int64(2), 2, 3)),
        "shape_nonpositive": ("source_shape_zyx", (0, 2, 3)),
        "origin_outside": ("kernel_origin_zyx", (2, 1, 2)),
        "origin_float": ("kernel_origin_zyx", (0.0, 1, 2)),
        "crop_list": ("detector_crop_zyx", [[0, 2], [0, 2], [1, 3]]),
        "crop_outside": ("detector_crop_zyx", ((0, 2), (0, 2), (1, 4))),
        "crop_empty": ("detector_crop_zyx", ((0, 2), (0, 2), (1, 1))),
        "crop_data_mismatch": ("detector_crop_zyx", ((0, 1), (0, 2), (1, 3))),
        "spacing_zero": ("source_spacing_um_zyx", (0.0, 1.25, 0.5)),
        "spacing_bool": ("source_spacing_um_zyx", (True, 1.25, 0.5)),
        "spacing_infinite": ("source_spacing_um_zyx", (np.inf, 1.25, 0.5)),
        "carrier_shape": ("carrier_per_um_yx", np.zeros((1, 2))),
        "carrier_complex": ("carrier_per_um_yx", np.zeros(2, dtype=complex)),
        "labels_shape": ("phases_rad", np.zeros(6)),
        "covariance_asymmetric": ("exposure_covariance", np.eye(7)),
        "covariance_not_positive": ("exposure_covariance", -np.eye(7)),
        "covariance_singular": ("exposure_covariance", np.ones((7, 7))),
        "covariance_shape": ("exposure_covariance", np.eye(6)),
        "mask_numeric": ("fit_mask", np.ones((2, 2, 2))),
        "mask_shape": ("fit_mask", np.ones((2, 2, 1), dtype=bool)),
        "empty_starts": ("initial_offsets_rad", np.zeros((0, 7))),
        "start_dimension": ("initial_offsets_rad", np.zeros((1, 6))),
        "start_outside": ("initial_offsets_rad", np.ones((1, 7))),
        "reversed_bounds": ("offset_bounds_rad", np.array([np.ones(7), -np.ones(7)])),
        "bounds_shape": ("offset_bounds_rad", np.zeros((7, 2))),
        "zero_step": ("difference_step_rad", np.zeros(7)),
        "negative_step": ("difference_step_rad", -np.ones(7)),
        "step_shape": ("difference_step_rad", np.ones(6)),
        "source_rtol_zero": ("source_rtol", 0.0),
        "source_rtol_one": ("source_rtol", 1.0),
        "phase_rtol_bool": ("phase_rank_rtol", True),
        "phase_rtol_array": ("phase_rank_rtol", np.array(0.01)),
        "gradient_negative": ("gradient_tolerance", -0.1),
        "gradient_nan": ("gradient_tolerance", np.nan),
        "budget_bool": ("max_evaluations", True),
        "budget_float": ("max_evaluations", 1.0),
        "budget_zero": ("max_evaluations", 0),
    }
    if name in replacements:
        key, value = replacements[name]
        arguments[key] = value
    if name == "kernel_zero_imag":
        arguments["order_kernels"][0, 0, 0, 0] += 1e-300j
    if name == "covariance_asymmetric":
        arguments["exposure_covariance"][0, 1] = 1e-14
    if name == "unrepresentable_step":
        arguments["offset_bounds_rad"][:] = np.array([[1e16], [1e16 + 4]])
        arguments["initial_offsets_rad"][:] = 1e16
        arguments["difference_step_rad"][:] = 0.1
    if name.startswith("known_"):
        arguments = make_case("known").arguments
        if name == "known_extra_seed":
            arguments["initial_offsets_rad"] = np.zeros((2, 0))
        else:
            arguments["initial_offsets_rad"] = np.zeros((1, 1))
    return arguments


INVALID_CASES = [
    "mode",
    "images_list",
    "images_bool",
    "images_complex",
    "images_object",
    "images_subclass",
    "images_masked",
    "images_shape",
    "images_nonfinite",
    "no_exposures",
    "kernel_real",
    "kernel_complex64",
    "kernel_zero_imag",
    "kernel_nonfinite",
    "kernel_order_count",
    "kernel_empty_axis",
    "shape_list",
    "shape_bool",
    "shape_numpy_int",
    "shape_nonpositive",
    "origin_outside",
    "origin_float",
    "crop_list",
    "crop_outside",
    "crop_empty",
    "crop_data_mismatch",
    "spacing_zero",
    "spacing_bool",
    "spacing_infinite",
    "carrier_shape",
    "carrier_complex",
    "labels_shape",
    "covariance_asymmetric",
    "covariance_not_positive",
    "covariance_singular",
    "covariance_shape",
    "mask_numeric",
    "mask_shape",
    "empty_starts",
    "start_dimension",
    "start_outside",
    "reversed_bounds",
    "bounds_shape",
    "zero_step",
    "negative_step",
    "step_shape",
    "unrepresentable_step",
    "source_rtol_zero",
    "source_rtol_one",
    "phase_rtol_bool",
    "phase_rtol_array",
    "gradient_negative",
    "gradient_nan",
    "budget_bool",
    "budget_float",
    "budget_zero",
    "known_extra_seed",
    "known_nonempty_offsets",
]


@pytest.mark.parametrize("name", INVALID_CASES)
def test_invalid_input_classification_and_preservation(name: str) -> None:
    """P02/P14: one representative per decision, no Cartesian validation grid."""
    arguments = invalid_arguments(name)
    snapshots = {
        key: (value.copy(), value.flags.writeable)
        for key, value in arguments.items()
        if type(value) is np.ndarray
    }
    policy = np.geterr()
    filters = warnings.filters[:]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        active_filters = warnings.filters[:]
        with pytest.raises(SimreconError) as error:
            fit(arguments)
        assert warnings.filters == active_filters
    assert error.value.code == "invalid_exposure_phase_input"
    assert not any(issubclass(item.category, RuntimeWarning) for item in caught)
    assert np.geterr() == policy
    assert warnings.filters == filters
    for key, (snapshot, writable) in snapshots.items():
        assert_array_equal(arguments[key], snapshot)
        assert arguments[key].flags.writeable is writable


@pytest.mark.parametrize("kind", ["phase_sum", "geometry", "model", "objective", "conversion"])
def test_representational_range_errors_without_runtime_warnings(kind: str) -> None:
    """P14: finite caller input may exceed required binary64 arithmetic."""
    arguments = make_case("common").arguments
    arguments["initial_offsets_rad"] = np.zeros((1, 1))
    arguments["max_evaluations"] = 1
    if kind == "phase_sum":
        arguments["phases_rad"][:] = 1.3e308
        arguments["initial_offsets_rad"][:] = 1.3e308
        arguments["offset_bounds_rad"][:] = 1.3e308
    elif kind == "geometry":
        arguments["source_spacing_um_zyx"] = (1.0, 1.3e308, 1.3e308)
        arguments["carrier_per_um_yx"][:] = 3.0
    elif kind == "model":
        arguments["order_kernels"][1:] = complex(1.3e308, 1.3e308)
    elif kind == "objective":
        arguments["order_kernels"][:] = 0
        arguments["images"][:] = 1.3e308
    else:
        # Python arbitrary-precision integer conversion is deterministic and
        # does not require a platform with wider-than-binary64 long doubles.
        arguments["source_spacing_um_zyx"] = (10**1000, 1.0, 1.0)
    policy = np.geterr()
    filters = warnings.filters[:]
    snapshots = {
        key: (value.copy(), value.flags.writeable)
        for key, value in arguments.items()
        if type(value) is np.ndarray
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        active_filters = warnings.filters[:]
        with pytest.raises(SimreconError) as error:
            fit(arguments)
        assert warnings.filters == active_filters
    assert error.value.code == "exposure_phase_range"
    assert not any(issubclass(item.category, RuntimeWarning) for item in caught)
    assert np.geterr() == policy
    assert warnings.filters == filters
    for key, (snapshot, writable) in snapshots.items():
        assert_array_equal(arguments[key], snapshot)
        assert arguments[key].flags.writeable is writable
