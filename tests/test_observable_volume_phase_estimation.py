"""Blind public-contract proofs for observable-subspace local phase estimation.

Expectation source: docs/contracts/observable-volume-phase-estimation-v1.md and
its explicitly inherited fixed-transfer contract.  No private production seam is
used.  Tests compare the full lifted representative, never a particular Q.
"""

import dataclasses
import json
import subprocess
import sys
import warnings
from itertools import combinations
from typing import Any, cast

import numpy as np
import pytest
import scipy.optimize
from numpy.testing import assert_allclose, assert_array_equal

import simrecon as sr
from observable_volume_phase_estimation_fixture import (
    EPS,
    QUANTUM,
    SOLVER_FAILURE_PAYLOAD,
    canonical,
    empirical_pair_fixture,
    geometry,
    inference_group,
    kernel_transfers,
    make_orders,
    normalize,
    observe,
    operator,
    orbit_basis,
    powers,
    rank_change_fixture,
    record_fields,
    reduced_inference_fixture,
    spatial_images,
    support,
)

PHASES = np.array([-2.7, -1.4, -0.2, 0.9, 2.2, 2.9])
SOURCE = "  specimen / supplied calibration; opaque  "
PREFIX = "invalid_volume_phase_estimation_"
ARRAY_FIELDS = {
    "phases_rad": np.dtype("float64"),
    "phasors": np.dtype("complex128"),
    "phase_deviations_rad": np.dtype("float64"),
    "specimen_normalized": np.dtype("float64"),
    "nuisance_singular_values": np.dtype("float64"),
    "phase_singular_values": np.dtype("float64"),
    "observable_fourier_mask": np.dtype("bool"),
}
SCALAR_FIELDS = {
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


def estimate(images: Any, values: Any = None, **overrides: Any) -> Any:
    """Call only the additive public entry with every required keyword explicit."""
    if values is None:
        values = np.ones((3, *images.shape[1:]), dtype=np.complex128)
    options: dict[str, Any] = {
        "order_otf": make_orders(values),
        "carrier_bins_yx": (0, 0),
        "initial_phases_rad": PHASES.copy(),
        "max_nfev": 1,
        "gradient_tolerance": 1e-9,
        "step_tolerance": 1e-10,
        "source": SOURCE,
    }
    options.update(overrides)
    # The additive API is absent before implementation. Keep its runtime lookup
    # and assertions active while typing the existing public API normally.
    return cast(Any, sr).estimate_observable_volume_phases(images, **options)


def expect_code(code: str, images: Any, values: Any = None, **changes: Any) -> None:
    with pytest.raises(sr.SimreconError) as caught:
        estimate(images, values, **changes)
    assert caught.value.code == code


def assert_profile(result: Any, images: Any, values: Any, carrier: tuple[int, int]) -> Any:
    """Compare independently recomputed stored-input targets at returned phases."""
    truth = observe(images, values, carrier, result.phases_rad)
    assert_array_equal(result.observable_fourier_mask, truth.mask)
    assert result.observable_dimension == int(np.count_nonzero(truth.mask))
    assert result.unobservable_dimension == images[0].size - result.observable_dimension
    assert result.nuisance_rank == truth.rank
    assert result.nuisance_singular_values.shape == (result.observable_dimension,)
    # Direct sums have O(M) bounded terms; the small fixtures are far from cutoffs.
    # 2e-11 is >1000 eps per term for M<=12, yet resolves all sign/factor examples.
    assert_allclose(result.specimen_normalized.ravel(), truth.u, rtol=2e-11, atol=2e-11)
    assert_allclose(result.nuisance_singular_values, truth.singular, rtol=2e-11, atol=2e-11)
    assert_allclose(result.phase_singular_values, truth.phase_singular, rtol=2e-10, atol=2e-11)
    assert result.phase_design_rank == truth.design_rank
    # Exact-zero information has no relative rank guarantee under a floating projection.
    if truth.phase_singular[0] > 1e-9:
        assert result.phase_rank == truth.phase_rank
    for field, expected in (
        ("relative_residual", truth.relative),
        ("normalized_residual_rms", truth.rms),
        ("normalized_imaginary_rms", truth.imaginary),
        ("calibration_reality_defect", truth.defect),
        ("gradient_inf_norm", truth.gradient),
    ):
        assert_allclose(getattr(result, field), expected, rtol=2e-10, atol=2e-11)
    if truth.singular.size and truth.rank == len(truth.singular):
        condition = truth.singular[0] / truth.singular[-1]
        if condition <= 10 and truth.singular[-1] >= 1 / 16 and truth.allowance <= 1 / 1024:
            assert np.linalg.norm(result.specimen_normalized.ravel() - truth.u) <= truth.allowance
            for field, expected in (
                ("relative_residual", truth.relative),
                ("normalized_residual_rms", truth.rms),
                ("normalized_imaginary_rms", truth.imaginary),
                ("calibration_reality_defect", truth.defect),
                ("gradient_inf_norm", truth.gradient),
            ):
                assert abs(getattr(result, field) - expected) <= truth.allowance
            error = np.max(np.abs(result.nuisance_singular_values - truth.singular))
            assert error <= truth.allowance
    assert result.global_ambiguity == "unassessed"
    return truth


def test_oracle_analytic_dc_pair_nyquist_and_fourier_isometry() -> None:
    """Self-check observer normalization, real orbit dimensions and signed gains."""
    for shape in ((1, 1, 1), (1, 1, 4), (2, 3, 2), (3, 1, 3)):
        _, _, u = geometry(shape)
        assert_allclose(u.conj().T @ u, np.eye(u.shape[0]), atol=5e-15)
        mask = np.ones(shape, dtype=np.bool_)
        q = orbit_basis(mask)
        assert q.shape == (u.shape[0], u.shape[0])
        assert_allclose(q.T @ q, np.eye(q.shape[1]), atol=5e-15)
    values = np.zeros((3, 1, 1, 4), dtype=np.complex128)
    values[0] = 2.0
    images = np.tile(np.array([[[1.0, -2.0, 3.0, -4.0]]]), (6, 1, 1, 1))
    truth = observe(images, values, (0, 0), PHASES)
    assert truth.rank == 4
    assert_allclose(truth.singular, np.sqrt(6.0), atol=5e-15)
    assert_allclose(truth.u, images[0].ravel() / 4, atol=5e-15)
    assert np.linalg.norm(truth.residual) < 1e-14
    scalar = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    scalar[:, 0, 0, 0] = [1.0, 0.2 + 0.1j, -0.1 + 0.05j]
    a, _ = operator(scalar, (0, 0), PHASES)
    expected = 1 + 2 * (powers(PHASES)[1] * (0.2 + 0.1j) + powers(PHASES)[2] * (-0.1 + 0.05j)).real
    assert_allclose(a[:6, 0], expected, atol=5e-15)
    assert_allclose(a[6:, 0], 0, atol=5e-15)


def test_public_bindings_frozen_record_and_independent_arrays() -> None:
    images = np.zeros((6, 1, 2, 3))
    values = np.ones((3, 1, 2, 3), dtype=np.complex128)
    initial = PHASES.copy()
    orders = make_orders(values)
    record = estimate(images, values, order_otf=orders, initial_phases_rad=initial)
    other = estimate(images, values, order_otf=orders, initial_phases_rad=initial)
    assert isinstance(record, cast(Any, sr).ObservableVolumePhaseEstimate)
    assert {field.name for field in dataclasses.fields(record)} == set(ARRAY_FIELDS) | SCALAR_FIELDS
    for name, dtype in ARRAY_FIELDS.items():
        array = getattr(record, name)
        assert type(array) is np.ndarray
        assert array.dtype == dtype and array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        for caller in (
            images,
            values,
            initial,
            orders.fz_per_um,
            orders.fy_per_um,
            orders.fx_per_um,
        ):
            assert not np.shares_memory(array, caller)
        for other_name in ARRAY_FIELDS:
            assert not np.shares_memory(array, getattr(other, other_name))
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            setattr(record, name, array)
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            delattr(record, name)
    for first, second in combinations(ARRAY_FIELDS, 2):
        assert not np.shares_memory(getattr(record, first), getattr(record, second))
    record.observable_fourier_mask.flat[0] = False
    assert other.observable_fourier_mask.all()
    record.specimen_normalized.flat[0] = -7
    assert other.specimen_normalized.flat[0] == 0
    assert record.phases_rad.shape == record.phasors.shape == (6,)
    assert record.phase_deviations_rad.shape == (6,)
    assert record.specimen_normalized.shape == (1, 2, 3)
    for name in (
        "nuisance_rank",
        "phase_rank",
        "phase_design_rank",
        "nfev",
        "njev",
        "observable_dimension",
        "unobservable_dimension",
    ):
        assert type(getattr(record, name)) is int
    for name in (
        "image_scale",
        "transfer_scale",
        "relative_residual",
        "normalized_residual_rms",
        "normalized_imaginary_rms",
        "calibration_reality_defect",
        "gradient_inf_norm",
    ):
        assert type(getattr(record, name)) is float
    assert record.source == SOURCE and record.carrier_bins_yx == (0, 0)
    # Direct construction is a passive public record, not another validation boundary.
    fields = {f.name: getattr(record, f.name) for f in dataclasses.fields(record)}
    fields["observable_dimension"] = -1
    assert cast(Any, sr).ObservableVolumePhaseEstimate(**fields).observable_dimension == -1


def test_required_keywords_and_only_images_positional() -> None:
    api = cast(Any, sr).estimate_observable_volume_phases
    images = np.zeros((6, 1, 1, 1))
    kwargs = dict(
        order_otf=make_orders(np.zeros((3, 1, 1, 1), dtype=np.complex128)),
        carrier_bins_yx=(0, 0),
        initial_phases_rad=PHASES,
        max_nfev=1,
        gradient_tolerance=1e-9,
        step_tolerance=1e-10,
        source=SOURCE,
    )
    for missing in kwargs:
        with pytest.raises(TypeError):
            api(images, **{key: value for key, value in kwargs.items() if key != missing})
    with pytest.raises(TypeError):
        api(images, kwargs["order_otf"], **{k: v for k, v in kwargs.items() if k != "order_otf"})
    with pytest.raises(TypeError):
        api(images, **kwargs, unsupported=True)


@pytest.mark.parametrize(
    "shape,index,dimension",
    [
        ((1, 1, 1), (0, 0, 0), 1),
        ((1, 1, 5), (0, 0, 3), 2),
        ((1, 1, 4), (0, 0, 0), 1),
        ((2, 4, 3), (0, 0, 1), 1),
        ((2, 3, 4), (1, 0, 0), 2),
        ((3, 1, 3), (0, 0, 2), 2),
    ],
)
def test_single_nonhermitian_zero_order_orbits(shape: Any, index: Any, dimension: int) -> None:
    values = np.zeros((3, *shape), dtype=np.complex128)
    values[(0, *index)] = 1.0 + 0.25j
    sites = np.arange(6 * np.prod(shape), dtype=np.float64)
    images = (np.sin(0.37 * sites) + 0.2 * np.cos(0.11 * sites**2)).reshape((6, *shape))
    result = estimate(images, values)
    truth = assert_profile(result, images, values, (0, 0))
    assert result.observable_dimension == dimension
    assert result.nuisance_rank == dimension
    assert result.termination == "stationary"
    # Non-Hermitian F0 is not silently replaced by its Hermitian projection.
    assert truth.defect > 0
    assert truth.imaginary > 0
    assert truth.relative > 0


@pytest.mark.parametrize(
    "shape,carrier,order,location",
    [
        ((2, 3, 4), (-1, 1), 1, (0, 1, 0)),
        ((3, 2, 3), (1, -1), 2, (0, 0, 2)),
        ((1, 1, 4), (0, -1), 2, (0, 0, 0)),
        ((1, 3, 1), (-2, 0), 1, (0, 2, 0)),
    ],
)
def test_signed_shift_reflection_and_full_axis_closure(
    shape: Any,
    carrier: Any,
    order: int,
    location: Any,
) -> None:
    values = np.zeros((3, *shape), dtype=np.complex128)
    values[(order, *location)] = 0.7 - 0.4j
    images = np.sin(np.arange(6 * np.prod(shape))).reshape((6, *shape))
    result = estimate(images, values, carrier_bins_yx=carrier)
    normalized, _, _, _ = normalize(values, images)
    expected = np.zeros(shape, dtype=np.bool_)
    frequency = tuple((a - n // 2) % n for a, n in zip(location, shape, strict=True))
    j = tuple((a - order * e) % n for a, e, n in zip(frequency, (0, *carrier), shape, strict=True))
    for mode in (j, tuple((-a) % n for a, n in zip(j, shape, strict=True))):
        centered = tuple((a + n // 2) % n for a, n in zip(mode, shape, strict=True))
        expected[centered] = True
    assert_array_equal(result.observable_fourier_mask, expected)
    assert_array_equal(support(normalized, carrier), expected)
    assert_profile(result, images, values, carrier)


@pytest.mark.parametrize(
    "coefficient,expected_dimension,expected_rank",
    [
        (0.0, 1, 1),
        (-0.0, 1, 1),
        (1e-200, 3, 1),
        (QUANTUM, 3, 1),
    ],
)
def test_exact_component_support_weak_is_not_absent(
    coefficient: float,
    expected_dimension: int,
    expected_rank: int,
) -> None:
    values = np.zeros((3, 1, 1, 5), dtype=np.complex128)
    values[0, 0, 0, 2] = 1
    values[0, 0, 0, 3] = complex(0.0, coefficient)
    images = np.ones((6, 1, 1, 5))
    result = estimate(images, values)
    assert result.observable_dimension == expected_dimension
    assert result.nuisance_rank == expected_rank
    assert result.termination == ("stationary" if coefficient == 0 else "nuisance_rank_deficient")
    assert result.nuisance_singular_values.shape == (expected_dimension,)
    assert_allclose(result.phases_rad, canonical(PHASES), atol=0, rtol=0)
    assert result.observable_fourier_mask[0, 0, 3] == (coefficient != 0)


def test_normalization_underflow_changes_support_without_original_value_promise() -> None:
    values = np.zeros((3, 1, 1, 5), dtype=np.complex128)
    values[0, 0, 0, 2] = np.finfo(np.float64).max
    values[0, 0, 0, 3] = QUANTUM
    result = estimate(np.ones((6, 1, 1, 5)), values)
    assert result.observable_dimension == result.nuisance_rank == 1
    assert result.termination == "stationary"
    assert not result.observable_fourier_mask[0, 0, 3]
    assert result.transfer_scale == np.finfo(np.float64).max


@pytest.mark.parametrize("nonzero", [False, True])
def test_zero_dimension_diagnostics_without_optimizer(nonzero: bool) -> None:
    images = np.arange(36, dtype=np.float64).reshape(6, 1, 2, 3) - 18
    if not nonzero:
        images.fill(0)
    values = np.zeros((3, 1, 2, 3), dtype=np.complex128)
    result = estimate(images, values)
    assert result.termination == "no_observable_specimen"
    assert result.observable_dimension == result.nuisance_rank == result.phase_rank == 0
    assert result.unobservable_dimension == 6
    assert result.nuisance_singular_values.shape == (0,)
    assert_array_equal(result.observable_fourier_mask, False)
    assert_array_equal(result.specimen_normalized, 0)
    assert_array_equal(result.phase_singular_values, np.zeros(6))
    assert result.gradient_inf_norm == result.normalized_imaginary_rms == 0
    assert result.relative_residual == (1.0 if nonzero else 0.0)
    scale = np.max(np.abs(images)) if nonzero else 1
    assert_allclose(
        result.normalized_residual_rms,
        np.linalg.norm(images / scale) / np.sqrt(images.size),
        atol=2e-15,
    )
    assert result.image_scale == scale and result.transfer_scale == 1
    assert result.phase_design_rank == 5
    assert_array_equal(result.phases_rad, canonical(PHASES))
    assert result.nfev >= 0 and result.njev >= 0


def test_deficiency_is_phase_specific_and_does_not_delete_retained_orbit() -> None:
    values = np.zeros((3, 1, 1, 2), dtype=np.complex128)
    values[0, 0, 0] = [1, 1]
    values[1, 0, 0, 0] = -0.5
    images = np.tile(np.array([[[1.0, -0.25]]]), (6, 1, 1, 1))

    result = estimate(images, values, initial_phases_rad=np.zeros(6))
    assert result.observable_dimension == 2 and result.nuisance_rank == 1
    assert result.termination == "nuisance_rank_deficient"
    assert_array_equal(result.phases_rad, np.zeros(6))
    assert_profile(result, images, values, (0, 0))
    available = estimate(images, values)
    assert available.observable_dimension == available.nuisance_rank == 2
    assert available.termination != "nuisance_rank_deficient"
    assert_profile(available, images, values, (0, 0))


def test_reduction_minimum_norm_and_unexplained_rows_are_retained() -> None:
    values = np.zeros((3, 1, 1, 5), dtype=np.complex128)
    values[0, 0, 0, 2:4] = [1, 0.8 + 0.2j]
    images = (np.sin(np.arange(30) * 0.7) - 0.2).reshape(6, 1, 1, 5)
    result = estimate(images, values)
    truth = assert_profile(result, images, values, (0, 0))
    full, _, _, _ = np.linalg.lstsq(truth.a, truth.y, rcond=EPS * len(truth.y))
    assert_allclose(truth.u, full, atol=1e-13)
    assert_allclose(truth.a @ truth.u, truth.b @ (truth.q.T @ truth.u), atol=1e-13)
    assert_allclose(
        np.linalg.norm(truth.y - truth.a @ full), np.linalg.norm(truth.residual), atol=1e-13
    )
    _, _, transform = geometry(images.shape[1:])
    spectrum = transform @ result.specimen_normalized.ravel()
    assert_allclose(spectrum[~truth.mask.ravel()], 0, atol=2e-13)
    invisible = orbit_basis(~truth.mask)[:, 0]
    assert_allclose(truth.a @ invisible, 0, atol=2e-14)
    assert np.linalg.norm(truth.u + invisible) > np.linalg.norm(truth.u)
    # Data outside the supported orbit contributes to the objective; no row masking.
    assert truth.relative > 0.1
    assert result.nuisance_rank == result.observable_dimension == 3
    assert result.termination == "stationary"


def test_oracle_off_model_jacobian_matches_central_differences() -> None:
    images, values, _, nominal, _, _ = inference_group(0)
    values[0, 0, 0, 0] += 0.3j  # Deliberately non-Hermitian calibration.
    images = images + 0.06 * np.sin(np.arange(images.size)).reshape(images.shape)
    initial = canonical(nominal)
    truth = observe(images, values, (0, 1), initial)
    correction = truth.jacobian + truth.information
    assert np.linalg.norm(correction) > 1e-4
    assert truth.rank == truth.q.shape[1]
    # Central differences have O(h^2) truncation and O(eps/h) cancellation.
    h = 2e-5
    finite_difference = []
    for p in range(len(initial)):
        step = np.zeros_like(initial)
        step[p] = h
        plus = observe(images, values, (0, 1), initial + step).residual
        minus = observe(images, values, (0, 1), initial - step).residual
        finite_difference.append((plus - minus) / (2 * h))
    assert_allclose(truth.jacobian, np.column_stack(finite_difference), atol=2e-8, rtol=2e-7)


def test_full_off_model_jacobian_changes_actual_selected_solver_step() -> None:
    images, values, _, nominal, _, _ = inference_group(0)
    values[0, 0, 0, 0] += 0.3j
    images += 0.06 * np.sin(np.arange(images.size)).reshape(images.shape)
    initial = canonical(nominal)
    fits = []
    for full in (True, False):

        def jacobian(angles: Any, use_full: bool = full) -> Any:
            point = observe(images, values, (0, 1), angles)
            return point.jacobian if use_full else -point.information

        fits.append(
            scipy.optimize.least_squares(
                lambda angles: observe(images, values, (0, 1), angles).residual,
                initial,
                jac=cast(Any, jacobian),
                method="trf",
                bounds=(-np.inf, np.inf),
                loss="linear",
                x_scale=1,
                tr_solver="exact",
                ftol=cast(Any, None),
                gtol=1e-9,
                xtol=1e-10,
                max_nfev=2,
            )
        )
    assert np.max(np.abs(fits[0].x - fits[1].x)) > 1e-5
    # Both independent paths use real SciPy results. The fixed small example's
    # 2e-9 rad comparison permits floating organization changes and still resolves
    # the >1e-5 rad effect of omitting the required residual-dependent term.
    result = estimate(
        images, values, carrier_bins_yx=(0, 1), initial_phases_rad=nominal, max_nfev=2
    )
    assert_allclose(result.phases_rad, canonical(fits[0].x), atol=2e-9, rtol=0)
    assert result.termination == "evaluation_limit"
    assert result.gradient_inf_norm > 1e-9
    assert_profile(result, images, values, (0, 1))


def test_phase_information_design_rank_and_nuisance_availability_are_separate() -> None:
    values = np.zeros((3, 1, 1, 3), dtype=np.complex128)
    values[0] = 1
    images = np.tile(np.array([[[1.0, -0.5, 0.25]]]), (6, 1, 1, 1))
    result = estimate(images, values, initial_phases_rad=np.ones(6) * 0.3)
    assert result.nuisance_rank == result.observable_dimension == 3
    assert result.phase_rank == 0 and result.phase_design_rank == 1
    assert_array_equal(result.phase_singular_values, np.zeros(6))
    assert result.gradient_inf_norm == 0 and result.termination == "stationary"
    assert result.global_ambiguity == "unassessed"
    assert_profile(result, images, values, (0, 0))


@pytest.mark.parametrize(
    "carrier", [(-2, 1), (0, 0), (2**130 + 1, -(2**141) + 2), (np.uint64(2**64 - 1), np.int64(-3))]
)
def test_carrier_aliases_preserve_original_exact_integers(carrier: Any) -> None:
    images, values, _, nominal, _, _ = inference_group(0)
    declared = (int(carrier[0]), int(carrier[1]))
    reduced = (declared[0] % 2, declared[1] % 3)
    first = estimate(images, values, carrier_bins_yx=list(carrier), initial_phases_rad=nominal)
    second = estimate(images, values, carrier_bins_yx=reduced, initial_phases_rad=nominal)
    assert first.carrier_bins_yx == declared
    assert all(type(x) is int for x in first.carrier_bins_yx)
    assert_array_equal(first.observable_fourier_mask, second.observable_fourier_mask)
    assert_allclose(first.specimen_normalized, second.specimen_normalized, atol=2e-12)
    assert_allclose(first.normalized_residual_rms, second.normalized_residual_rms, atol=2e-12)
    assert_profile(first, images, values, declared)


def test_huge_phases_native_canonicalization_branch_cut_and_wrapped_deviation() -> None:
    initial = np.array([np.finfo(np.float64).max, -1e250, np.pi, -np.pi, -0.0, 1e100])
    images = np.arange(6, dtype=np.float64).reshape(6, 1, 1, 1)
    values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    result = estimate(images, values, initial_phases_rad=initial)
    assert_array_equal(result.phases_rad, canonical(initial))
    assert np.all(result.phases_rad >= -np.pi) and np.all(result.phases_rad < np.pi)
    assert_array_equal(result.phasors, np.cos(result.phases_rad) + 1j * np.sin(result.phases_rad))
    assert_allclose(result.phase_deviations_rad, 0, atol=1e-15)
    # Native huge-angle reduction differs from modulo a rounded 2*pi.
    assert abs(result.phases_rad[0] - ((initial[0] + np.pi) % (2 * np.pi) - np.pi)) > 0.01
    active = np.array([1.0, 0.2 + 0.1j, 0.1 - 0.02j]).reshape(3, 1, 1, 1)
    fitted = estimate(images, active, initial_phases_rad=initial)
    assert_allclose(fitted.phases_rad, canonical(initial), atol=2e-15, rtol=0)
    assert_profile(fitted, images, active, (0, 0))


@pytest.mark.parametrize("which", [0, 1])
def test_independent_spatial_groups_hidden_steps_objective_and_local_gauge(which: int) -> None:
    images, values, actual, nominal, specimen, kernels = inference_group(which)
    # Establish this fixture's local recovery independently, with no hidden truth
    # supplied to the solve.  The 2e-6 rad example threshold is ten times this
    # observer check, not a universal estimator or physical accuracy promise.
    # SciPy's annotations omit the supported callable Jacobian and disabled ftol.
    # These two casts affect static typing only; the callable and None are retained.
    observer_fit = scipy.optimize.least_squares(
        lambda angles: observe(images, values, (0, 1), angles).residual,
        canonical(nominal),
        jac=cast(Any, lambda angles: observe(images, values, (0, 1), angles).jacobian),
        method="trf",
        loss="linear",
        x_scale=1,
        tr_solver="exact",
        ftol=cast(Any, None),
        gtol=1e-12,
        xtol=1e-12,
        max_nfev=200,
    )
    assert np.linalg.norm(canonical(observer_fit.x - actual), ord=np.inf) < 2e-7
    result = estimate(
        images,
        values,
        carrier_bins_yx=(0, 1),
        initial_phases_rad=nominal,
        max_nfev=200,
        gradient_tolerance=1e-12,
        step_tolerance=1e-12,
    )
    truth = assert_profile(result, images, values, (0, 1))
    initial = observe(images, values, (0, 1), canonical(nominal))
    hidden = observe(images, values, (0, 1), canonical(actual))
    assert np.linalg.norm(hidden.residual) < 1e-12
    assert np.linalg.norm(truth.residual) < np.linalg.norm(initial.residual) / 100
    assert result.termination == "stationary"
    # Recovery is tested only when independent local information resolves all N angles.
    assert hidden.phase_rank == len(actual)
    phase_error = canonical(result.phases_rad - actual)
    assert np.linalg.norm(phase_error, ord=np.inf) < 2e-6
    _, _, bscale, tscale = normalize(values, images)
    assert_allclose(result.specimen_normalized, specimen * tscale / bscale, atol=2e-6, rtol=2e-6)
    assert_allclose(
        result.phase_deviations_rad, canonical(result.phases_rad - canonical(nominal)), atol=1e-14
    )
    # A real independently generated calibration observation uses a point specimen.
    bead = np.zeros_like(specimen)
    bead.flat[-2] = 7.0 + which
    calibration_phases = np.array([-2.8, -1.9, -0.7, 0.3, 1.35, 2.45])
    calibration_images = spatial_images(bead, kernels, (0, 1), calibration_phases)
    assert calibration_images.shape == images.shape
    assert not np.array_equal(calibration_images, images)
    # The explicitly declared fixed calibration gauge transforms covariantly.
    delta = 0.31
    gauged = values.copy()
    gauged[1] *= np.exp(-1j * delta)
    gauged[2] *= np.exp(-2j * delta)
    shifted = estimate(
        images,
        gauged,
        carrier_bins_yx=(0, 1),
        initial_phases_rad=nominal + delta,
        max_nfev=200,
        gradient_tolerance=1e-12,
        step_tolerance=1e-12,
    )
    assert_allclose(canonical(shifted.phases_rad - result.phases_rad), delta, atol=2e-6)
    assert_allclose(shifted.specimen_normalized, result.specimen_normalized, atol=2e-6)
    assert shifted.global_ambiguity == "unassessed"


def test_existing_full_support_objective_compatibility_with_independent_truth() -> None:
    images, values, _, nominal, _, _ = inference_group(0)
    orders = make_orders(values)
    new = estimate(
        images, values, order_otf=orders, carrier_bins_yx=(0, 1), initial_phases_rad=nominal
    )
    old = sr.estimate_volume_phases(
        images,
        order_otf=orders,
        carrier_bins_yx=(0, 1),
        initial_phases_rad=nominal,
        max_nfev=1,
        gradient_tolerance=1e-9,
        step_tolerance=1e-10,
        source=SOURCE,
    )
    assert isinstance(old, sr.VolumePhaseEstimate)
    assert new.observable_dimension == images[0].size
    truth = assert_profile(new, images, values, (0, 1))
    # A one-evaluation start gives a common mathematical point, not a trajectory promise.
    assert_allclose(old.specimen_normalized.ravel(), truth.u, atol=2e-11)
    assert_allclose(old.normalized_residual_rms, truth.rms, atol=2e-11)
    assert not hasattr(old, "observable_fourier_mask")


def test_spatial_generator_and_direct_fourier_operator_agree_independently() -> None:
    for which in (0, 1):
        images, values, actual, _, specimen, kernels = inference_group(which)
        assert_allclose(kernel_transfers(kernels), values, atol=0, rtol=0)
        normalized, data, bscale, tscale = normalize(values, images)
        a, _ = operator(normalized, (0, 1), actual)
        _, _, transform = geometry(specimen.shape)
        y = data.reshape(len(actual), -1) @ transform.T
        realified = np.concatenate((y.real.ravel(), y.imag.ravel()))
        assert_allclose(a @ (specimen.ravel() * tscale / bscale), realified, atol=2e-14, rtol=2e-14)


class ArraySubclass(np.ndarray):
    """A rejected ndarray subclass, distinct from a permitted storage layout."""


@pytest.mark.parametrize("zero_support", [False, True])
@pytest.mark.parametrize(
    "case",
    [
        "list",
        "subclass",
        "masked",
        "bool",
        "complex",
        "object",
        "string",
        "rank3",
        "rank5",
        "few",
        "emptyz",
        "emptyy",
        "emptyx",
        "nan",
        "inf",
    ],
)
def test_images_validation_even_before_zero_dimension(case: str, zero_support: bool) -> None:
    images: Any = np.zeros((6, 1, 2, 3))
    values = np.full((3, 1, 2, 3), 0 if zero_support else 1, dtype=np.complex128)
    if case == "list":
        images = images.tolist()
    elif case == "subclass":
        images = images.view(ArraySubclass)
    elif case == "masked":
        images = np.ma.array(images)
    elif case in ("bool", "complex", "object", "string"):
        images = images.astype(
            {"bool": "bool", "complex": "complex128", "object": "object", "string": "U1"}[case]
        )
    elif case == "rank3":
        images = images[0]
    elif case == "rank5":
        images = images[None]
    elif case == "few":
        images = images[:4]
    elif case.startswith("empty"):
        axis = {"emptyz": 1, "emptyy": 2, "emptyx": 3}[case]
        lengths = list(images.shape)
        lengths[axis] = 0
        images = np.empty(lengths)
    else:
        images.flat[-1] = np.nan if case == "nan" else np.inf
    code = (
        "nonfinite_volume_phase_estimation_images" if case in ("nan", "inf") else PREFIX + "images"
    )
    expect_code(code, images, values)


@pytest.mark.parametrize("zero_support", [False, True])
@pytest.mark.parametrize(
    "case",
    [
        "list",
        "subclass",
        "masked",
        "bool",
        "complex",
        "object",
        "rank2",
        "short",
        "long",
        "nan",
        "inf",
    ],
)
def test_initial_phase_validation_before_every_unavailable_return(
    case: str,
    zero_support: bool,
) -> None:
    angles: Any = PHASES.copy()
    if case == "list":
        angles = angles.tolist()
    elif case == "subclass":
        angles = angles.view(ArraySubclass)
    elif case == "masked":
        angles = np.ma.array(angles)
    elif case in ("bool", "complex", "object"):
        angles = angles.astype({"bool": "bool", "complex": "complex128", "object": "object"}[case])
    elif case == "rank2":
        angles = angles[None]
    elif case == "short":
        angles = angles[:-1]
    elif case == "long":
        angles = np.append(angles, 0)
    else:
        angles[-1] = np.nan if case == "nan" else np.inf
    code = (
        "nonfinite_volume_phase_estimation_initial_phases"
        if case in ("nan", "inf")
        else PREFIX + "initial_phases"
    )
    values = np.full((3, 1, 2, 3), 0 if zero_support else 1, dtype=np.complex128)
    expect_code(code, np.zeros((6, 1, 2, 3)), values, initial_phases_rad=angles)


@pytest.mark.parametrize("dtype", ["i1", "u8", "f2", "f4", ">f8", "longdouble"])
@pytest.mark.parametrize("layout", ["C", "F", "reverse", "readonly"])
def test_permitted_real_widths_endian_layouts_and_signed_data(dtype: str, layout: str) -> None:
    data = np.arange(36).reshape(6, 1, 2, 3)
    if dtype != "u8":
        data = data - 18
    images = data.astype(dtype)
    phases = np.array([0, 1, 2, 3, 4, 5], dtype=dtype)
    if layout == "F":
        images, phases = np.asfortranarray(images), np.asfortranarray(phases)
    elif layout == "reverse":
        images, phases = images[..., ::-1], phases[::-1]
    elif layout == "readonly":
        images.setflags(write=False)
        phases.setflags(write=False)
    values = np.zeros((3, 1, 2, 3), dtype=np.complex128)
    values[0] = 1
    before, phase_before = images.copy(), phases.copy()
    strides, writeable = images.strides, images.flags.writeable
    result = estimate(images, values, initial_phases_rad=phases)
    assert result.observable_dimension == result.nuisance_rank == 6
    assert_profile(result, np.array(images, dtype=np.float64), values, (0, 0))
    assert_array_equal(images, before)
    assert_array_equal(phases, phase_before)
    assert images.strides == strides and images.flags.writeable == writeable


def native_representation_capabilities() -> dict[str, Any]:
    """Measure actual source domains instead of assuming a platform dtype name."""
    wide = np.finfo(np.longdouble)
    overflow_source = np.longdouble(wide.max)
    underflow_source = np.longdouble(wide.smallest_subnormal)
    assert np.isfinite(overflow_source) and overflow_source > 0
    assert np.isfinite(underflow_source) and underflow_source > 0
    # These are observer conversions, not fabricated wider values or product faults.
    with np.errstate(over="ignore", under="ignore"):
        maximum_snapshot = np.array([overflow_source], dtype=np.longdouble).astype(np.float64)
        minimum_snapshot = np.array([underflow_source], dtype=np.longdouble).astype(np.float64)
    return {
        "overflow_source": overflow_source,
        "underflow_source": underflow_source,
        "conversion_overflow": bool(np.isinf(maximum_snapshot[0])),
        "conversion_underflow": bool(minimum_snapshot[0] == 0),
        "longdouble_itemsize": np.dtype(np.longdouble).itemsize,
        "clongdouble_itemsize": np.dtype(np.clongdouble).itemsize,
    }


def assert_permitted_native_representation(
    images: Any, values: Any, phases: Any, operation: Any = estimate
) -> Any:
    """Check a real public operation against the one-voxel zero-order closed form."""
    assert images.shape == (6, 1, 1, 1) and values.shape == (3, 1, 1, 1)
    assert not np.any(values[1:]) and values[0, 0, 0, 0] != 0
    snapshots = (
        np.array(images, dtype=np.float64),
        np.array(values, dtype=np.complex128),
        np.array(phases, dtype=np.float64),
    )
    assert all(np.isfinite(array).all() for array in snapshots)
    orders = make_orders(values)
    arrays = [images, values, phases, orders.fz_per_um, orders.fy_per_um, orders.fx_per_um]
    for array in arrays:
        array.setflags(write=False)
    before = [(a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable) for a in arrays]
    mode, filters = np.geterr(), list(warnings.filters)
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        strict_mode, strict_filters = np.geterr(), list(warnings.filters)
        result = operation(
            images,
            order_otf=orders,
            carrier_bins_yx=(0, 0),
            initial_phases_rad=phases,
            max_nfev=1,
            gradient_tolerance=1e-9,
            step_tolerance=1e-10,
            source=SOURCE,
        )
        assert np.geterr() == strict_mode and warnings.filters == strict_filters
    assert np.geterr() == mode and warnings.filters == filters
    assert not any(issubclass(item.category, RuntimeWarning) for item in caught)
    data, transfer, angles = snapshots
    image_scale = float(np.max(np.abs(data))) if np.any(data) else 1.0
    transfer_scale = float(max(np.max(np.abs(transfer.real)), np.max(np.abs(transfer.imag))))
    d = (data / image_scale).ravel()
    a = transfer[0, 0, 0, 0] / transfer_scale
    # min_u sum_p |d_p-a*u|^2, u real: u=Re(a)*sum(d)/(N*|a|^2).
    target = a.real * np.sum(d) / (len(d) * (a.real * a.real + a.imag * a.imag))
    residual_norm = np.hypot(
        np.linalg.norm(d - a.real * target), np.sqrt(len(d)) * abs(a.imag * target)
    )
    expected = {
        "normalized_residual_rms": residual_norm / np.sqrt(len(d)),
        "relative_residual": residual_norm / np.linalg.norm(d) if np.any(d) else 0.0,
        "normalized_imaginary_rms": abs(a.imag * target),
        "calibration_reality_defect": 2 * abs(a.imag),
    }
    assert result.termination == "stationary" and result.nuisance_rank == 1
    assert result.phase_rank == 0 and result.gradient_inf_norm == 0
    assert result.image_scale == image_scale and result.transfer_scale == transfer_scale
    assert_allclose(result.specimen_normalized, target, atol=2e-11, rtol=2e-11)
    assert_allclose(
        result.nuisance_singular_values,
        [np.sqrt(len(d) * (a.real * a.real + a.imag * a.imag))],
        atol=2e-11,
        rtol=2e-11,
    )
    for name, value in expected.items():
        assert_allclose(getattr(result, name), value, atol=2e-11, rtol=2e-10)
    assert_allclose(result.phases_rad, canonical(angles), atol=2e-15, rtol=0)
    assert_array_equal(result.phase_singular_values, np.zeros(6))
    for field in ARRAY_FIELDS.keys() - {"observable_fourier_mask"}:
        returned = getattr(result, field)
        assert returned.flags.writeable
        assert all(not np.shares_memory(returned, array) for array in arrays)
    assert before == [
        (a.tobytes(), a.shape, a.strides, a.dtype.str, a.flags.writeable) for a in arrays
    ]
    return result


@pytest.mark.parametrize("field", ["images", "phases"])
def test_wider_source_finite_but_converted_infinite_is_nonfinite(field: str) -> None:
    capabilities = native_representation_capabilities()
    value = capabilities["overflow_source"]
    images = np.zeros((6, 1, 1, 1), dtype=np.longdouble)
    phases = PHASES.astype(np.longdouble)
    if field == "images":
        images.flat[-1] = value
    else:
        phases[-1] = value
    assert np.isfinite(images).all() and np.isfinite(phases).all()
    if capabilities["conversion_overflow"]:
        suffix = "images" if field == "images" else "initial_phases"
        code = "nonfinite_volume_phase_estimation_" + suffix
        expect_code(
            code,
            images,
            np.zeros((3, 1, 1, 1), dtype=np.complex128),
            initial_phases_rad=phases,
        )
    else:
        # No wider finite-to-infinite domain: exercise the actual finite maximum.
        if field == "phases":
            images.flat[-1] = 1
        values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
        values[0] = 1
        result = assert_permitted_native_representation(images, values, phases)
        assert_profile(result, images.astype(np.float64), values, (0, 0))
        assert_allclose(result.specimen_normalized, 1 / 6, atol=2e-11, rtol=2e-11)


@pytest.mark.parametrize(
    "carrier",
    [
        (True, 0),
        (0.0, 1),
        (0, 1 + 0j),
        (0,),
        (0, 1, 2),
        np.array([0, 1]),
        "01",
        None,
    ],
)
def test_carrier_grammar_rejection_before_zero_dimension(carrier: Any) -> None:
    expect_code(
        PREFIX + "carrier",
        np.zeros((6, 1, 1, 1)),
        np.zeros((3, 1, 1, 1), dtype=np.complex128),
        carrier_bins_yx=carrier,
    )


@pytest.mark.parametrize(
    "field,bad",
    [
        ("max_nfev", True),
        ("max_nfev", 0),
        ("max_nfev", -1),
        ("max_nfev", 1.0),
        ("max_nfev", "1"),
        ("max_nfev", np.array(1)),
        ("gradient_tolerance", True),
        ("gradient_tolerance", 0.0),
        ("gradient_tolerance", EPS),
        ("gradient_tolerance", 1.0),
        ("gradient_tolerance", np.inf),
        ("gradient_tolerance", np.nan),
        ("gradient_tolerance", 1e-9 + 0j),
        ("gradient_tolerance", "1e-9"),
        ("gradient_tolerance", np.array(1e-9)),
        ("step_tolerance", False),
        ("step_tolerance", -1.0),
        ("step_tolerance", EPS / 2),
        ("step_tolerance", 1.0),
        ("step_tolerance", np.inf),
        ("step_tolerance", np.nan),
        ("step_tolerance", object()),
    ],
)
def test_controls_validate_individually_before_unavailable(field: str, bad: Any) -> None:
    expect_code(
        PREFIX + "controls",
        np.zeros((6, 1, 1, 1)),
        np.zeros((3, 1, 1, 1), dtype=np.complex128),
        **{field: bad},
    )


def test_permitted_numpy_controls_and_unbounded_maximum_without_work_promise() -> None:
    result = estimate(
        np.zeros((6, 1, 1, 1)),
        np.zeros((3, 1, 1, 1), dtype=np.complex128),
        max_nfev=2**160,
        gradient_tolerance=np.float32(0.1),
        step_tolerance=np.nextafter(EPS, 1.0),
    )
    assert result.termination == "no_observable_specimen"
    other = estimate(
        np.zeros((6, 1, 1, 1)), np.zeros((3, 1, 1, 1), dtype=np.complex128), max_nfev=np.uint64(3)
    )
    assert other.termination == "no_observable_specimen"


@pytest.mark.parametrize("bad", [None, "", " \t\n", 12, b"label"])
def test_source_validation_before_unavailable(bad: Any) -> None:
    expect_code(
        "invalid_otf_source",
        np.zeros((6, 1, 1, 1)),
        np.zeros((3, 1, 1, 1), dtype=np.complex128),
        source=bad,
    )


@pytest.mark.parametrize(
    "case",
    [
        "instance",
        "values_list",
        "values_subclass",
        "values_bool",
        "values_real",
        "values_c64",
        "values_cwide",
        "values_rank",
        "values_orders",
        "values_shape",
        "values_nan",
        "values_inf",
        "fz_list",
        "fy_f32",
        "fx_subclass",
        "fx_wrong_length",
        "fx_nonfinite",
        "fx_reverse",
        "fx_dc",
        "fx_grid",
        "spacing_array",
        "spacing_count",
        "spacing_bool",
        "spacing_zero",
        "spacing_nan",
        "origin_array",
        "origin_count",
        "origin_bool",
        "origin_float",
        "origin_negative",
        "origin_outside",
        "source_blank",
    ],
)
def test_all_otf_fields_and_unused_samples_validated_with_zero_data(case: str) -> None:
    values = np.zeros((3, 2, 3, 4), dtype=np.complex128)
    fields = record_fields(make_orders(values))
    record: Any = None
    if case == "instance":
        record = fields
    elif case == "values_list":
        fields["values"] = values.tolist()
    elif case == "values_subclass":
        fields["values"] = values.view(ArraySubclass)
    elif case in ("values_bool", "values_real", "values_c64", "values_cwide"):
        dtype = {
            "values_bool": "bool",
            "values_real": "float64",
            "values_c64": "complex64",
            "values_cwide": "clongdouble",
        }[case]
        if case == "values_cwide" and np.dtype(dtype).itemsize == 16:
            # This actual representation meets the complex128-width rule.
            permitted = np.zeros((3, 1, 1, 1), dtype=dtype)
            permitted[0] = 1 + 0.25j
            images = np.array([1, -0.25, 0.5, -0.75, 0.125, -0.5]).reshape(6, 1, 1, 1)
            result = assert_permitted_native_representation(images, permitted, PHASES.copy())
            assert_profile(result, images, permitted.astype(np.complex128), (0, 0))
            assert_allclose(result.specimen_normalized, 1 / 51, atol=2e-11, rtol=2e-11)
            return
        fields["values"] = np.zeros(values.shape, dtype=dtype)
    elif case == "values_rank":
        fields["values"] = values[None]
    elif case == "values_orders":
        fields["values"] = values[:2]
    elif case == "values_shape":
        fields["values"] = values[..., :3]
    elif case in ("values_nan", "values_inf"):
        # Last order/last sample must validate even when everything else is zero.
        values[-1, -1, -1, -1] = complex(0, np.nan if case == "values_nan" else np.inf)
    elif case == "fz_list":
        fields["fz_per_um"] = fields["fz_per_um"].tolist()
    elif case == "fy_f32":
        fields["fy_per_um"] = fields["fy_per_um"].astype("float32")
    elif case == "fx_subclass":
        fields["fx_per_um"] = fields["fx_per_um"].view(ArraySubclass)
    elif case == "fx_wrong_length":
        fields["fx_per_um"] = fields["fx_per_um"][:-1]
    elif case == "fx_nonfinite":
        fields["fx_per_um"][-1] = np.inf
    elif case == "fx_reverse":
        fields["fx_per_um"] = fields["fx_per_um"][::-1]
    elif case == "fx_dc":
        fields["fx_per_um"][2] = QUANTUM
    elif case == "fx_grid":
        fields["fx_per_um"][-1] += 0.01
    elif case.startswith("spacing"):
        fields["voxel_size_um"] = {
            "spacing_array": np.ones(3),
            "spacing_count": (1, 1),
            "spacing_bool": (True, 1, 1),
            "spacing_zero": (0.0, 1, 1),
            "spacing_nan": (1, np.nan, 1),
        }[case]
    elif case.startswith("origin"):
        fields["origin_zyx"] = {
            "origin_array": np.zeros(3, dtype=int),
            "origin_count": (0, 0),
            "origin_bool": (False, 0, 0),
            "origin_float": (0.0, 0, 0),
            "origin_negative": (0, -1, 0),
            "origin_outside": (2, 0, 0),
        }[case]
    else:
        fields["source"] = "  "
    if case != "instance":
        record = sr.VolumeOrderOtf(**fields)
    expect_code(PREFIX + "otf", np.zeros((6, 2, 3, 4)), values, order_otf=record)


def test_otf_subclasses_missing_attributes_and_unrelated_getters() -> None:
    values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    fields = record_fields(make_orders(values))

    class Ordinary(sr.VolumeOrderOtf):
        pass

    class Missing(sr.VolumeOrderOtf):
        def __getattribute__(self, name: str) -> Any:
            if name == "source":
                raise AttributeError("missing supplied public source")
            return super().__getattribute__(name)

    class Unrelated(sr.VolumeOrderOtf):
        def __getattribute__(self, name: str) -> Any:
            if name == "source":
                raise RuntimeError("unrelated public getter failure")
            return super().__getattribute__(name)

    images = np.zeros((6, 1, 1, 1))
    ordinary = estimate(images, values, order_otf=Ordinary(**fields))
    assert ordinary.termination == "no_observable_specimen"
    expect_code(PREFIX + "otf", images, values, order_otf=Missing(**fields))
    with pytest.raises(RuntimeError, match="unrelated public getter failure"):
        estimate(images, values, order_otf=Unrelated(**fields))


@pytest.mark.parametrize("layout", ["endian", "strided", "readonly", "fortran"])
def test_otf_permitted_storage_extreme_grids_and_origin_provenance(layout: str) -> None:
    shape = (1, 2, 3)
    values = np.zeros((3, *shape), dtype=np.complex128)
    values[0] = 0.7 + 0.1j
    fields = record_fields(make_orders(values))
    if layout == "endian":
        for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
            fields[name] = fields[name].astype(fields[name].dtype.newbyteorder(">"))
    elif layout == "strided":
        for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
            old = fields[name]
            backing = np.zeros((*old.shape[:-1], old.shape[-1] * 2), dtype=old.dtype)
            backing[..., ::2] = old
            fields[name] = backing[..., ::2]
    elif layout == "fortran":
        fields["values"] = np.asfortranarray(values)
    else:
        for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
            fields[name].setflags(write=False)
    fields["voxel_size_um"] = [np.float64(1), np.int64(1), 1.0]
    fields["origin_zyx"] = [np.int64(0), np.uint64(1), 2]
    record = sr.VolumeOrderOtf(**fields)
    images = np.arange(36, dtype=np.float64).reshape(6, *shape) - 18
    result = estimate(images, values, order_otf=record)
    assert_profile(result, images, values, (0, 0))
    # A changed origin alone must not change values already encoded by the caller.
    fields["origin_zyx"] = (0, 0, 0)
    other = estimate(images, values, order_otf=sr.VolumeOrderOtf(**fields))
    assert_allclose(result.specimen_normalized, other.specimen_normalized, atol=0, rtol=0)
    # A singleton axis permits extreme spacing; no overflowing period is required.
    singleton = make_orders(
        np.zeros((3, 1, 1, 1), dtype=np.complex128),
        voxel_size_um=(np.finfo(np.float64).max, QUANTUM, 1.0),
    )
    result = estimate(np.zeros((6, 1, 1, 1)), order_otf=singleton)
    assert result.termination == "no_observable_specimen"


def test_common_component_scaling_extrema_zero_and_caller_policies() -> None:
    maximum = np.finfo(np.float64).max
    values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    values[0, 0, 0, 0] = complex(maximum, maximum)
    values[1, 0, 0, 0] = complex(maximum / 4, -maximum / 8)
    images = np.array([maximum, -maximum, maximum / 2, 0, -maximum / 4, maximum])
    images = images.reshape(6, 1, 1, 1)
    original_images, original_values = images.copy(), values.copy()
    old_mode, old_filters = np.geterr(), list(warnings.filters)
    with np.errstate(all="raise"):
        strict_mode = np.geterr()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            filters = list(warnings.filters)
            result = estimate(images, values)
            assert np.geterr() == strict_mode and warnings.filters == filters
        assert not any(issubclass(item.category, RuntimeWarning) for item in caught)
    assert np.geterr() == old_mode and warnings.filters == old_filters
    assert result.image_scale == result.transfer_scale == maximum
    assert_profile(result, images, values, (0, 0))
    assert_array_equal(images, original_images)
    assert_array_equal(values, original_values)


@pytest.mark.parametrize("failure", ["floating", "overflow", "memory", "runtime", "type", "value"])
def test_public_fft_exceptions_classify_without_finite_fabrication(failure: str) -> None:
    assert_solver_failure_report(run_dependency_probe("fft", failure), failure)


def test_arithmetic_runtime_warning_handled_under_caller_ignore() -> None:
    assert_solver_failure_report(run_dependency_probe("fft", "runtime_warning"), "runtime_warning")


def test_unrelated_warning_visible_and_input_bytes_preserved_after_failure() -> None:
    assert_solver_failure_report(run_dependency_probe("fft", "user_warning"), "user_warning")


def test_actual_solver_stagnation_vs_stationary_ordering() -> None:
    images, values, _, nominal, _, _ = inference_group(1)
    result = estimate(
        images,
        values,
        carrier_bins_yx=(0, 1),
        initial_phases_rad=nominal,
        max_nfev=200,
        gradient_tolerance=np.nextafter(EPS, 1.0),
        step_tolerance=0.9,
    )
    assert result.termination == "stagnated"
    assert result.gradient_inf_norm > np.nextafter(EPS, 1.0)
    assert_profile(result, images, values, (0, 1))
    zero = estimate(np.zeros_like(images), values, max_nfev=1)
    assert zero.termination == "stationary"  # Stationary precedes evaluation_limit.
    assert zero.gradient_inf_norm == 0
    assert_array_equal(zero.specimen_normalized, 0)
    assert_array_equal(zero.phase_singular_values, np.zeros(6))


@pytest.mark.parametrize("factor,expected", [(0.75, 1), (1.25, 2), (1.0, None)])
def test_cutoff_uses_all_realified_rows_and_returned_strict_rank(
    factor: float,
    expected: int | None,
) -> None:
    # DC and even Nyquist are orthogonal real columns, each with singular value
    # sqrt(N)*abs(F).  Both modes are structural even across numerical deficiency.
    values = np.zeros((3, 1, 1, 4), dtype=np.complex128)
    values[0, 0, 0, 2] = 1
    values[0, 0, 0, 0] = factor * EPS * (2 * 6 * 4)
    images = np.tile(np.array([[[1.0, -0.25, 1.0, -0.25]]]), (6, 1, 1, 1))
    result = estimate(images, values)
    assert result.observable_dimension == 2
    assert_allclose(result.nuisance_singular_values[0], np.sqrt(6), atol=2e-14)
    cutoff = EPS * images.size * 2 * result.nuisance_singular_values[0]
    assert result.nuisance_rank == int(np.count_nonzero(result.nuisance_singular_values > cutoff))
    if expected is not None:
        assert result.nuisance_rank == expected
    # At an exact mathematical boundary backend rounding can select either rank.
    assert result.termination == (
        "stationary" if result.nuisance_rank == 2 else "nuisance_rank_deficient"
    )


@pytest.mark.parametrize("which", [0, 1])
def test_even_only_independent_pi_alternatives_remain_unassessed(which: int) -> None:
    _, _, actual, _, specimen, kernels = inference_group(which)
    kernels[1] = 0
    values = kernel_transfers(kernels)
    images = spatial_images(specimen, kernels, (0, 1), actual)
    alternative = actual + np.pi * np.array([0, 1, -1, 0, 1, -1])
    result = estimate(images, values, carrier_bins_yx=(0, 1), initial_phases_rad=alternative)
    assert result.normalized_residual_rms < 1e-12
    assert result.termination == "stationary"
    assert result.global_ambiguity == "unassessed"
    assert_allclose(result.phases_rad, canonical(alternative), atol=1e-12)
    # Low residual cannot certify which of these discrete alternatives was physical.
    assert np.max(np.abs(canonical(result.phases_rad - actual))) > 3
    assert_profile(result, images, values, (0, 1))


def test_uniform_specimen_can_have_phase_information() -> None:
    _, _, actual, _, specimen, kernels = inference_group(0)
    specimen.fill(1)
    values = kernel_transfers(kernels)
    images = spatial_images(specimen, kernels, (0, 1), actual)
    independent = observe(images, values, (0, 1), canonical(actual))
    assert independent.phase_rank == len(actual)
    result = estimate(images, values, carrier_bins_yx=(0, 1), initial_phases_rad=actual)
    assert result.observable_dimension == result.nuisance_rank == specimen.size
    assert result.phase_rank == len(actual)
    assert result.normalized_residual_rms < 1e-12
    assert_profile(result, images, values, (0, 1))


def test_finite_conversion_underflow_is_permitted_for_data_and_initial_phases() -> None:
    capabilities = native_representation_capabilities()
    tiny = capabilities["underflow_source"]
    images = np.full((6, 1, 1, 1), tiny, dtype=np.longdouble)
    angles = np.full(6, -tiny, dtype=np.longdouble)
    values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    values[0] = 1
    assert np.all(images > 0) and np.all(angles < 0)
    result = assert_permitted_native_representation(images, values, angles)
    assert_profile(result, images.astype(np.float64), values, (0, 0))
    if capabilities["conversion_underflow"]:
        assert result.image_scale == 1
        assert_array_equal(result.specimen_normalized, 0)
        assert result.relative_residual == result.normalized_residual_rms == 0
        assert_allclose(result.phases_rad, 0, atol=0, rtol=0)
    else:
        # No smaller source domain: retain the actual nonzero subnormal instead.
        assert result.image_scale == QUANTUM
        assert np.all(images.astype(np.float64) == QUANTUM)
        assert_allclose(result.specimen_normalized, 1, atol=2e-11, rtol=2e-11)


def test_frequency_tolerance_and_overflowing_period_have_permitted_positives() -> None:
    values = np.zeros((3, 1, 2, 3), dtype=np.complex128)
    fields = record_fields(make_orders(values))
    fields["fx_per_um"][0] = np.nextafter(fields["fx_per_um"][0], -np.inf)
    result = estimate(np.zeros((6, 1, 2, 3)), values, order_otf=sr.VolumeOrderOtf(**fields))
    assert result.termination == "no_observable_specimen"
    maximum = np.finfo(np.float64).max
    singleton_y = np.zeros((3, 1, 2, 1), dtype=np.complex128)
    extreme = make_orders(
        singleton_y, voxel_size_um=(1.0, maximum, 1.0), fy_per_um=np.array([-0.5 / maximum, 0.0])
    )
    result = estimate(np.zeros((6, 1, 2, 1)), singleton_y, order_otf=extreme)
    assert result.termination == "no_observable_specimen"


@pytest.mark.parametrize("field", ["gradient_tolerance", "step_tolerance"])
@pytest.mark.parametrize(
    "exception",
    [
        TypeError,
        ValueError,
        OverflowError,
        MemoryError,
        RuntimeError,
    ],
)
def test_scalar_conversion_errors_stay_at_their_named_boundary(
    field: str,
    exception: type[Exception],
) -> None:
    error = exception("public real-scalar conversion probe")

    class DeclaredReal(float):
        def __float__(self) -> float:
            raise error

    images = np.zeros((6, 1, 1, 1))
    values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
    if exception in (TypeError, ValueError, OverflowError):
        expect_code(PREFIX + "controls", images, values, **{field: DeclaredReal(0.1)})
    else:
        with pytest.raises(exception) as caught:
            estimate(images, values, **{field: DeclaredReal(0.1)})
        assert caught.value is error


def test_fixed_coordinate_translation_is_observed_not_silently_registered() -> None:
    images, values, actual, _, specimen, kernels = inference_group(0)
    shift = (0, 1, 1)
    angle = 2 * np.pi / specimen.shape[2]
    translated_specimen = np.roll(specimen, shift, axis=(0, 1, 2))
    translated_images = spatial_images(translated_specimen, kernels, (0, 1), actual - angle)
    assert_allclose(translated_images, np.roll(images, shift, axis=(1, 2, 3)), atol=2e-15)
    result = estimate(
        translated_images, values, carrier_bins_yx=(0, 1), initial_phases_rad=actual - angle
    )
    assert result.termination == "stationary" and result.normalized_residual_rms < 1e-12
    _, _, bscale, tscale = normalize(values, translated_images)
    assert_allclose(
        result.specimen_normalized, translated_specimen * tscale / bscale, atol=2e-11, rtol=2e-11
    )
    assert_allclose(result.phases_rad, canonical(actual - angle), atol=2e-15, rtol=0)


@pytest.mark.parametrize("nz", [1, 2])
def test_oracle_rank_change_is_reached_by_real_local_solver(nz: int) -> None:
    images, values, phases = rank_change_fixture(nz)
    initial = observe(images, values, (0, 1), phases)
    assert initial.rank == initial.q.shape[1] == 4
    visits: list[Any] = []

    class ObservedRankChange(Exception):
        pass

    def residual(angles: Any) -> Any:
        point = observe(images, values, (0, 1), angles)
        visits.append(point)
        if point.rank != initial.rank:
            raise ObservedRankChange("real independent solver trial loses nuisance rank")
        return point.residual

    # No finite dependency record is manufactured: SciPy chooses the trial, and
    # the observer stops on the same algebraic availability condition as specified.
    with pytest.raises(ObservedRankChange):
        scipy.optimize.least_squares(
            residual,
            phases,
            jac=cast(Any, lambda angles: observe(images, values, (0, 1), angles).jacobian),
            method="trf",
            bounds=(-np.inf, np.inf),
            loss="linear",
            x_scale=1,
            tr_solver="exact",
            ftol=cast(Any, None),
            gtol=1e-9,
            xtol=1e-10,
            max_nfev=200,
        )
    assert len(visits) >= 2
    assert visits[-1].rank == 3


@pytest.mark.parametrize("nz", [1, 2])
def test_rank_changed_returns_initial_observable_candidate(nz: int) -> None:
    images, values, phases = rank_change_fixture(nz)
    result = estimate(
        images, values, carrier_bins_yx=(0, 1), initial_phases_rad=phases, max_nfev=200
    )
    assert result.termination == "rank_changed"
    assert result.observable_dimension == result.nuisance_rank == 4
    assert result.unobservable_dimension == 4 * nz - 4
    assert_allclose(result.phases_rad, canonical(phases), atol=2e-16, rtol=0)
    assert_profile(result, images, values, (0, 1))
    assert result.nfev >= 2


def test_derived_phase_diagnostic_overflow_rejects_finite_fit() -> None:
    # M=1, phi=0: F1=i cancels its signed partner in the prediction, while
    # d/dphi gives -2. F0=a>0 yields u=1/a finite, but |-2*u| exceeds Fmax.
    # a=3*2^-1025 leaves a margin of about 1/3 beyond the derivative range.
    a = float.fromhex("0x0.6p-1022")
    values = np.array([a, 1j, 0j], dtype=np.complex128).reshape(3, 1, 1, 1)
    expect_code(
        "unrepresentable_volume_phase_estimation",
        np.ones((6, 1, 1, 1)),
        values,
        initial_phases_rad=np.zeros(6),
    )


def test_oracle_one_sided_pair_has_analytic_lift_and_unexplained_residual() -> None:
    angle = 2 * np.pi * np.arange(5) / 5
    images = np.tile((np.cos(angle) + 0.4 * np.cos(2 * angle))[None, None, :], (6, 1, 1, 1))
    values = np.zeros((3, 1, 1, 5), dtype=np.complex128)
    values[0, 0, 0, 3] = 1 + 0.25j
    truth = observe(images, values, (0, 0), PHASES)
    assert_array_equal(truth.mask, np.array([False, True, False, True, False]).reshape(1, 1, 5))
    assert truth.rank == 2 and truth.q.shape == (5, 2)
    expected_u = (np.cos(angle) + 0.25 * np.sin(angle)) / (1.4 * (1 + 0.25**2))
    assert_allclose(truth.u, expected_u, atol=3e-15, rtol=0)
    assert_allclose(truth.singular, np.sqrt(6 * (1 + 0.25**2) / 2), atol=3e-15)
    assert_allclose(truth.relative, np.sqrt(33 / 58), atol=3e-15)
    # The contract defines prediction in Fourier coordinates. Its sole retained
    # coefficient is real here; inverse-transform imaginary energy is a different
    # quantity and is not the specified normalized_imaginary_rms.
    assert_allclose(truth.imaginary, 0, atol=3e-15)
    full = np.linalg.lstsq(truth.a, truth.y, rcond=EPS * len(truth.y))[0]
    assert_allclose(full, expected_u, atol=3e-15, rtol=0)


@pytest.mark.parametrize("weak", [0.0, -0.0, 1e-200, QUANTUM])
def test_oracle_support_uses_normalized_exact_components_not_singular_cutoff(weak: float) -> None:
    values = np.zeros((3, 1, 1, 5), dtype=np.complex128)
    values[0, 0, 0, 2] = 1
    values[0, 0, 0, 3] = complex(0, weak)
    normalized, _, _, _ = normalize(values, np.ones((6, 1, 1, 5)))
    expected = np.array([False, weak != 0, True, weak != 0, False]).reshape(1, 1, 5)
    assert_array_equal(support(normalized, (0, 0)), expected)
    values[0, 0, 0, 2] = np.finfo(np.float64).max
    values[0, 0, 0, 3] = QUANTUM
    normalized, _, _, _ = normalize(values, np.ones((6, 1, 1, 5)))
    assert_array_equal(
        support(normalized, (0, 0)), np.array([False, False, True, False, False]).reshape(1, 1, 5)
    )


def calibrate_generated_pair(pair: dict[str, Any]) -> Any:
    """Exercise actual public raw calibration and adapter with independent truth."""
    acquisition = sr.declare_acquisition(pair["raw_counts"], config=pair["config"])
    result = sr.calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=13.0,
        response=1.7,
        output_unit="electrons",
        phases_rad=pair["calibration_phases_rad"],
        voxel_size_um=pair["voxel_size_um"],
    )
    expected = pair["expected_components"]
    size = expected[0].size
    corrected = (pair["raw_counts"][0] - 13.0) / 1.7
    # Separator allowance plus a direct generator/camera rounding margin.
    e = (8192 * len(corrected) + 128 * size) * EPS * float(np.max(np.abs(corrected)))
    mass = 7.0
    assert size * e < mass / 1000
    assert result.response.origin_zyx == pair["origin"]
    assert_allclose(result.components.dc, expected[0].real, atol=e, rtol=0)
    assert_allclose(result.components.c1, expected[1], atol=e, rtol=0)
    assert_allclose(result.components.c2, expected[2], atol=e, rtol=0)
    # Propagate component/mass error before adding the empirical transform bound.
    limits = []
    for m in range(3):
        magnitude = float(np.max(np.abs(pair["expected_response"][m])))
        lam = float(np.sum(np.abs(expected[m].real) + np.abs(expected[m].imag)) / mass)
        limits.append(
            (size * e * (1 + magnitude)) / (mass - size * e)
            + 512 * size * EPS * lam
            + 16 * size * QUANTUM
        )
        assert np.max(np.abs(result.response.values[m] - pair["expected_response"][m])) <= limits[m]
    orders = sr.adapt_empirical_volume_response(
        result.response,
        carrier_bins=pair["carrier"],
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=pair["phase_reference_shift_rad"],
        source="actual raw calibration / independent specimen pairing",
    )
    for m in range(3):
        rotation_error = (
            128
            * EPS
            * float(
                np.max(
                    np.abs(pair["expected_response"][m].real)
                    + np.abs(pair["expected_response"][m].imag)
                )
            )
        )
        assert np.max(np.abs(orders.values[m] - pair["expected_orders"][m])) <= (
            limits[m] + rotation_error
        )
    assert orders.origin_zyx == pair["origin"]
    assert_array_equal(acquisition.nominal_phases_rad, np.zeros((1, 6)))
    assert result.provenance["phases_rad"]["source"] == "supplied_actual"
    return orders


def test_oracle_raw_calibration_has_independent_forward_components_and_gauge() -> None:
    pair = empirical_pair_fixture()
    phases = pair["calibration_phases_rad"]
    z = powers(phases)
    design = np.column_stack(
        (np.ones(len(phases)), 2 * z[1].real, -2 * z[1].imag, 2 * z[2].real, -2 * z[2].imag)
    )
    assert np.linalg.cond(design) < 10
    corrected = (pair["raw_counts"][0] - 13.0) / 1.7
    coordinates = np.linalg.lstsq(design, corrected.reshape(len(phases), -1), rcond=None)[0]
    inferred = np.stack(
        (
            coordinates[0].astype(np.complex128),
            coordinates[1] + 1j * coordinates[2],
            coordinates[3] + 1j * coordinates[4],
        )
    ).reshape(pair["expected_components"].shape)
    assert_allclose(inferred, pair["expected_components"], atol=2e-14, rtol=0)
    # Truth used for this check stays generator/evaluator-only, never operation input.
    assert np.unravel_index(np.argmax(inferred[0].real), inferred[0].shape) == pair["origin"]
    observed = np.roll(inferred, tuple(-x for x in pair["origin"]), axis=(1, 2, 3))
    _, _, unitary = geometry(inferred.shape[1:])
    response = (
        observed.reshape(3, -1) @ unitary.T * np.sqrt(inferred[0].size) / np.sum(inferred[0].real)
    ).reshape(inferred.shape)
    assert_allclose(response, pair["expected_response"], atol=2e-14, rtol=0)


def test_observable_estimator_consumes_actual_raw_empirical_calibration_adapter() -> None:
    pair = empirical_pair_fixture()
    orders = calibrate_generated_pair(pair)
    result = estimate(
        pair["specimen_images"],
        pair["expected_orders"],
        order_otf=orders,
        carrier_bins_yx=pair["carrier"],
        initial_phases_rad=pair["specimen_initial_rad"],
    )
    # The calibration was independently checked above. Its exact stored output is
    # now a supplied input; this observer checks the downstream stored-input fit,
    # not physical truth inferred from a returned estimator diagnostic.
    assert_profile(result, pair["specimen_images"], orders.values, pair["carrier"])


def run_dependency_probe(
    boundary: str, kind: str, api_name: str = "estimate_observable_volume_phases"
) -> dict[str, Any]:
    """Run the gate child; blind roles exercise its literal as a direct entry."""
    completed = subprocess.run(
        [sys.executable, "-c", SOLVER_FAILURE_PAYLOAD, api_name, boundary, kind],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    rows = [
        line.removeprefix("SOLVER_PUBLIC_PROBE ")
        for line in completed.stdout.splitlines()
        if line.startswith("SOLVER_PUBLIC_PROBE ")
    ]
    assert len(rows) == 1
    report = json.loads(rows[0])
    assert isinstance(report, dict)
    assert report["api"] == api_name and report["boundary"] == boundary
    assert report["kind"] == kind
    return report


def assert_solver_failure_report(report: dict[str, Any], kind: str) -> None:
    """Check normal science on a miss without claiming fault-handling proof."""
    assert report["schema"] == "public-dependency-control.v2"
    assert report["kind"] == kind
    boundary = report["boundary"]
    assert boundary in ("svd", "fft", "optimizer", "no_optimizer")
    assert report["installed"] and len(report["installed"]) == len(set(report["installed"]))
    baseline, observed = report["baseline"], report["observed"]
    for row in (baseline, observed):
        assert row["phase"] == "measured_public_operation"
        assert type(row["calls"]) is int and row["calls"] >= 0
        assert type(row["delivered"]) is int and 0 <= row["delivered"] <= row["calls"]
        assert row["mode_preserved"] and row["filters_preserved"]
        assert row["inputs_preserved"] and row["metadata_preserved"]
        assert isinstance(row["warnings"], list)
        for warning in row["warnings"]:
            assert isinstance(warning["category"], str)
            assert isinstance(warning["message"], str)
            assert isinstance(warning["filename"], str) and warning["filename"]
            assert type(warning["lineno"]) is int and warning["lineno"] > 0
    assert baseline["outcome"] == "normal" and baseline["science"]["checked"] is True
    assert baseline["delivered"] == 0 and baseline["requested_fault"] is False
    assert not baseline["warnings"]
    if boundary == "no_optimizer":
        assert kind in ("zero", "nonzero", "deficient")
        assert baseline["calls"] >= 1 and baseline["science"]["gradient"] > 1e-4
        assert observed["calls"] == observed["delivered"] == 0
        assert observed["requested_fault"] is False
        assert observed["outcome"] == "normal" and observed["science"]["checked"] is True
        assert not observed["warnings"]
        assert report["fault_evidence"] == "not_requested"
        return
    requested = kind != "none"
    assert observed["requested_fault"] is requested
    # A matched informative operation cannot disappear only in its fault run.
    assert (baseline["calls"] > 0) == (observed["calls"] > 0)
    if boundary in ("fft", "optimizer"):
        assert baseline["calls"] >= 1 and observed["calls"] >= 1
    if not requested or observed["delivered"] == 0:
        assert observed["delivered"] == 0
        assert not requested or (boundary == "svd" and observed["calls"] == 0)
        assert report["fault_evidence"] == ("unexercised" if requested else "not_requested")
        assert observed["outcome"] == "normal" and observed["science"]["checked"] is True
        assert not observed["warnings"]
        return
    assert report["fault_evidence"] == "delivered"
    if observed["outcome"] == "exception":
        diagnostic = observed["diagnostic"]
        while True:
            assert isinstance(diagnostic["type"], str)
            assert isinstance(diagnostic["message"], str)
            assert diagnostic["frames"]
            for frame in diagnostic["frames"]:
                assert isinstance(frame["filename"], str) and frame["filename"]
                assert isinstance(frame["function"], str) and frame["function"]
                assert type(frame["lineno"]) is int and frame["lineno"] > 0
            if "chained" not in diagnostic:
                break
            diagnostic = diagnostic["chained"]
    if kind in ("linalg", "floating", "overflow", "runtime_warning"):
        assert observed["outcome"] == "exception"
        expected = (
            "volume_phase_estimation_transform_failure"
            if boundary == "fft"
            else "volume_phase_estimation_solver_failure"
        )
        assert observed["code"] == expected and observed["domain_error"]
        assert not any(w["category"] == "RuntimeWarning" for w in observed["warnings"])
    elif kind == "user_warning":
        assert observed["outcome"] == "normal" and observed["science"]["checked"] is True
        assert any(
            w["category"] == "UserWarning" and w["message"] == "controlled public unrelated warning"
            for w in observed["warnings"]
        )
    else:
        assert observed["outcome"] == "exception" and observed["identical"]
        assert (
            observed["exception_type"]
            == {
                "memory": "MemoryError",
                "runtime": "RuntimeError",
                "type": "TypeError",
                "value": "ValueError",
            }[kind]
        )


@pytest.mark.parametrize("boundary", ["svd", "optimizer"])
@pytest.mark.parametrize(
    "kind",
    [
        "linalg",
        "floating",
        "overflow",
        "memory",
        "runtime",
        "type",
        "value",
        "runtime_warning",
        "user_warning",
    ],
)
def test_public_solver_failures_with_controls_before_product_import(
    boundary: str, kind: str
) -> None:
    assert_solver_failure_report(run_dependency_probe(boundary, kind), kind)


@pytest.mark.parametrize("boundary", ["fft", "svd", "optimizer"])
def test_preimport_dependency_controls_pass_through_real_product(boundary: str) -> None:
    assert_solver_failure_report(run_dependency_probe(boundary, "none"), "none")


@pytest.mark.parametrize("kind", ["zero", "nonzero", "deficient"])
def test_preimport_optimizer_counts_unavailable_and_informative_companion(kind: str) -> None:
    assert_solver_failure_report(run_dependency_probe("no_optimizer", kind), kind)


@pytest.mark.parametrize("api_name", ["lapack_direct", "lapack_selected"])
def test_finite_svd_controls_permit_genuine_lapack_alternatives(api_name: str) -> None:
    # These public numerical callers demonstrate the finite control scope. They
    # supply no product factors, solver record or exhaustive backend claim.
    report = run_dependency_probe("svd", "linalg", api_name)
    assert_solver_failure_report(report, "linalg")
    for row in (report["baseline"], report["observed"]):
        assert row["calls"] == row["delivered"] == 0
        assert row["science"]["info"] == 0
        assert_allclose(row["science"]["singular"], np.sqrt([14, 5]), atol=2e-14)
        assert row["science"]["reconstruction_error"] < 3e-14


@pytest.mark.parametrize("exposures", [5, 6])
def test_oracle_successful_reduced_phase_update_and_invisible_physical_content(
    exposures: int,
) -> None:
    pair = reduced_inference_fixture(exposures)
    images, values = pair["images"], pair["values"]
    visited = []

    def residual(phases: Any) -> Any:
        point = observe(images, values, (0, 1), phases)
        visited.append(point)
        return point.residual

    fit = scipy.optimize.least_squares(
        residual,
        canonical(pair["nominal"]),
        jac=cast(Any, lambda phases: observe(images, values, (0, 1), phases).jacobian),
        method="trf",
        bounds=(-np.inf, np.inf),
        loss="linear",
        x_scale=1,
        tr_solver="exact",
        ftol=cast(Any, None),
        gtol=1e-12,
        xtol=1e-12,
        max_nfev=200,
    )
    assert fit.status > 0
    assert all(
        point.rank == 6
        and point.singular[-1] >= 1 / 16
        and point.singular[0] / point.singular[-1] <= 10
        and point.allowance <= 1 / 1024
        for point in visited
    )
    assert np.max(np.abs(canonical(fit.x - pair["actual"]))) < 2e-7
    assert np.linalg.norm(visited[-1].residual) < np.linalg.norm(visited[0].residual) / 1000
    hidden = observe(images, values, (0, 1), canonical(pair["actual"]))
    assert hidden.phase_rank == exposures
    assert hidden.q.shape == (12, 6)
    assert_array_equal(hidden.mask[0], False)
    assert_array_equal(hidden.mask[1], True)
    assert np.linalg.norm(hidden.a @ pair["invisible"].ravel()) < 2e-14
    _, _, bscale, tscale = normalize(values, images)
    expected = pair["observable"].ravel() * tscale / bscale
    assert_allclose(hidden.u, expected, atol=2e-13, rtol=0)
    assert np.linalg.norm(hidden.u - pair["hidden"].ravel() * tscale / bscale) > 0.05
    predicted = spatial_images(pair["observable"], pair["kernels"], (0, 1), pair["actual"])
    assert_allclose(images, predicted, atol=3e-15, rtol=0)


@pytest.mark.parametrize("exposures", [5, 6])
def test_successful_reduced_fit_updates_phases_and_returns_observable_lift(exposures: int) -> None:
    pair = reduced_inference_fixture(exposures)
    images, values = pair["images"], pair["values"]
    initial = observe(images, values, (0, 1), canonical(pair["nominal"]))
    result = estimate(
        images,
        values,
        carrier_bins_yx=(0, 1),
        initial_phases_rad=pair["nominal"],
        max_nfev=200,
        gradient_tolerance=1e-12,
        step_tolerance=1e-12,
    )
    final = assert_profile(result, images, values, (0, 1))
    assert result.observable_dimension == result.nuisance_rank == initial.rank == 6
    assert result.unobservable_dimension == 6
    assert result.phase_rank == exposures
    assert result.termination == "stationary"
    assert result.phases_rad.shape == result.phasors.shape == (exposures,)
    assert result.phase_deviations_rad.shape == (exposures,)
    assert_allclose(result.phasors, powers(result.phases_rad)[1], atol=0, rtol=0)
    assert_allclose(
        result.phase_deviations_rad,
        canonical(result.phases_rad - canonical(pair["nominal"])),
        atol=1e-14,
        rtol=0,
    )
    assert np.max(np.abs(canonical(result.phases_rad - pair["nominal"]))) > 1e-3
    assert np.max(np.abs(canonical(result.phases_rad - pair["actual"]))) < 2e-6
    assert np.linalg.norm(final.residual) < np.linalg.norm(initial.residual) / 1000
    _, _, bscale, tscale = normalize(values, images)
    assert result.image_scale == bscale and result.transfer_scale == tscale
    representative = pair["observable"] * tscale / bscale
    hidden_physical = pair["hidden"] * tscale / bscale
    assert_allclose(result.specimen_normalized, representative, atol=2e-6, rtol=2e-6)
    assert np.linalg.norm(result.specimen_normalized - hidden_physical) > 0.05
    _, _, transform = geometry(pair["hidden"].shape)
    fourier = transform @ result.specimen_normalized.ravel()
    assert_allclose(fourier[~final.mask.ravel()], 0, atol=2e-11, rtol=0)
    full = np.linalg.lstsq(final.a, final.y, rcond=EPS * len(final.y))[0]
    assert_allclose(result.specimen_normalized.ravel(), full, atol=2e-11, rtol=2e-11)
