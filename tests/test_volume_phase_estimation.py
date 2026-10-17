"""Blind public-contract tests for fixed-transfer local phase estimation v1.

Small dense examples deliberately make independent all-sample observation
possible. Missing exports are setup failures, never expected scientific red.
"""

from __future__ import annotations

import inspect
import warnings
from fractions import Fraction
from itertools import product
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

import simrecon
from volume_phase_estimation_fixture import (
    ORDER_FIELDS,
    Example,
    NuisanceSvdFailure,
    calibrated_example,
    canonical,
    copy_order_record,
    estimate,
    example,
    forward_observed_callbacks,
    local_phase_budget,
    observe,
    periodic_carrier,
    powers,
    public_observation,
    record,
    run_dependency_child,
    spatial_images,
    transfer_from_kernels,
)


@pytest.fixture
def api() -> Any:
    return phase_api()


def phase_api() -> Any:
    """Resolve the public operation after an isolated child's preimport setup."""
    operation = getattr(simrecon, "estimate_volume_phases", None)
    assert callable(operation), "setup: estimate_volume_phases public API unavailable"
    return operation


def check_observer(result: Any, e: Example, *, tight: bool = True) -> None:
    o = observe(e.images, e.orders.values, result.phases_rad, e.carrier)
    tol = 5e-10 if tight else o.allowance
    assert_allclose(result.specimen_normalized.ravel(), o.u, atol=tol, rtol=0)
    assert_allclose(result.nuisance_singular_values, o.nuisance_s, atol=tol, rtol=0)
    assert_allclose(result.phase_singular_values, o.phase_s, atol=tol, rtol=0)
    for field, expected in (
        ("relative_residual", o.relative),
        ("normalized_residual_rms", o.rms),
        ("normalized_imaginary_rms", o.imaginary),
        ("calibration_reality_defect", o.reality),
        ("gradient_inf_norm", o.gradient),
        ("image_scale", o.b),
        ("transfer_scale", o.t),
    ):
        assert getattr(result, field) == pytest.approx(expected, abs=tol, rel=0)
    assert result.nuisance_rank == o.nuisance_rank
    assert result.phase_design_rank == o.design_rank
    # No numerical-rank claim at an exact nullspace polluted by observer roundoff.
    if o.phase_rank == len(e.initial):
        assert result.phase_rank == o.phase_rank
    assert_allclose(result.phasors, powers(result.phases_rad)[1], atol=2e-15, rtol=0)
    assert_allclose(
        result.phase_deviations_rad,
        canonical(result.phases_rad - canonical(e.initial)),
        atol=2e-14,
        rtol=0,
    )
    assert np.all(result.phases_rad >= -np.pi)
    assert np.all(result.phases_rad < np.pi)
    assert result.global_ambiguity == "unassessed"
    assert result.carrier_bins_yx == e.carrier
    for field in ("nfev", "njev", "nuisance_rank", "phase_rank", "phase_design_rank"):
        assert type(getattr(result, field)) is int
    assert result.nfev >= 0 and result.njev >= 0
    if result.termination == "stationary":
        assert result.gradient_inf_norm <= 1e-9


@pytest.mark.parametrize(
    "group,n,uniform", [(0, 5, False), (0, 7, False), (1, 7, False), (1, 5, True)]
)
def test_hidden_independent_phase_steps(api: Any, group: int, n: int, uniform: bool) -> None:
    e = example(group, n=n, uniform=uniform)
    initial = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    truth = observe(e.images, e.orders.values, canonical(e.truth), e.carrier)
    assert truth.nuisance_rank == e.specimen.size
    assert truth.phase_rank == n
    assert np.linalg.norm(truth.r) < 2e-13
    assert initial.rms > 1e-4  # Initial commands cannot masquerade as actual phases.
    result = estimate(api, e)
    check_observer(result, e)
    assert result.termination == "stationary"
    # This checked local ball has an independent positive curvature lower bound.
    # It is not a global uniqueness or physical phase accuracy promise.
    phase_budget, mu = local_phase_budget(e)
    assert mu > 0
    assert np.linalg.norm(canonical(result.phases_rad - e.truth)) < 1e-4
    assert np.linalg.norm(canonical(result.phases_rad - e.truth)) <= phase_budget
    assert result.normalized_residual_rms < 1e-7
    assert result.normalized_residual_rms < initial.rms / 100


@pytest.mark.parametrize("group", [0, 1])
def test_correct_initialization_signed_specimen_and_conservative_envelope(
    api: Any, group: int
) -> None:
    e = example(group)
    e.specimen = e.specimen - 0.85
    e.images = spatial_images(e.specimen, e.kernels, e.truth, e.carrier)
    e.initial = e.truth.copy()
    o = observe(e.images, e.orders.values, canonical(e.truth), e.carrier)
    assert o.nuisance_s[0] / o.nuisance_s[-1] <= 10
    assert o.nuisance_s[-1] >= 1 / 16
    assert o.allowance <= 1 / 1024
    result = estimate(api, e)
    assert result.termination == "stationary"
    check_observer(result, e)
    check_observer(result, e, tight=False)
    assert_allclose(result.specimen_normalized, e.specimen * o.t / o.b, atol=2e-12, rtol=0)
    assert_allclose(result.phases_rad, canonical(e.truth), atol=2e-12, rtol=0)
    assert np.min(result.specimen_normalized) < 0


def test_api_binding_and_exact_frozen_record(api: Any) -> None:
    e = example(1)
    e.initial = e.truth.copy()
    result = estimate(api, e)
    expected = {
        "phases_rad",
        "phasors",
        "phase_deviations_rad",
        "specimen_normalized",
        "image_scale",
        "transfer_scale",
        "relative_residual",
        "normalized_residual_rms",
        "normalized_imaginary_rms",
        "calibration_reality_defect",
        "nuisance_rank",
        "nuisance_singular_values",
        "phase_rank",
        "phase_singular_values",
        "phase_design_rank",
        "gradient_inf_norm",
        "termination",
        "nfev",
        "njev",
        "carrier_bins_yx",
        "source",
        "global_ambiguity",
    }
    cls = getattr(simrecon, "VolumePhaseEstimate", None)
    assert cls is not None and isinstance(result, cls)
    public_data = {
        name
        for name in dir(result)
        if not name.startswith("_") and not callable(getattr(result, name))
    }
    assert public_data == expected
    assert result.source == " specimen/calibration pairing "
    assert inspect.signature(api).parameters["images"].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    required = {
        "order_otf",
        "carrier_bins_yx",
        "initial_phases_rad",
        "max_nfev",
        "gradient_tolerance",
        "step_tolerance",
        "source",
    }
    for name in required:
        parameter = inspect.signature(api).parameters[name]
        assert parameter.kind == inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty
    valid = dict(
        order_otf=e.orders,
        carrier_bins_yx=e.carrier,
        initial_phases_rad=e.initial,
        max_nfev=1,
        gradient_tolerance=1e-9,
        step_tolerance=1e-10,
        source="label",
    )
    for missing in required:
        with pytest.raises(TypeError):
            api(e.images, **{k: v for k, v in valid.items() if k != missing})
    with pytest.raises(TypeError):
        api(e.images, e.orders, **{k: v for k, v in valid.items() if k != "order_otf"})
    with pytest.raises(TypeError):
        api(e.images, **valid, unexpected=True)
    for name in expected:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, getattr(result, name))
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, name)
    direct = cls(**{name: None for name in expected})
    assert direct.phases_rad is None  # Direct construction does not validate.
    again = estimate(api, e)
    arrays = []
    other_call_arrays = [
        getattr(again, name)
        for name in (
            "phases_rad",
            "phasors",
            "phase_deviations_rad",
            "specimen_normalized",
            "nuisance_singular_values",
            "phase_singular_values",
        )
    ]
    for field, dtype, shape in (
        ("phases_rad", np.float64, (7,)),
        ("phasors", np.complex128, (7,)),
        ("phase_deviations_rad", np.float64, (7,)),
        ("specimen_normalized", np.float64, e.specimen.shape),
        ("nuisance_singular_values", np.float64, (e.specimen.size,)),
        ("phase_singular_values", np.float64, (7,)),
    ):
        a = getattr(result, field)
        assert type(a) is np.ndarray and a.dtype == np.dtype(dtype) and a.shape == shape
        assert a.flags.c_contiguous and a.flags.owndata and a.flags.writeable
        assert all(not np.shares_memory(a, other) for other in other_call_arrays)
        for other in [
            e.images,
            e.initial,
            e.orders.values,
            e.orders.fz_per_um,
            e.orders.fy_per_um,
            e.orders.fx_per_um,
            *arrays,
        ]:
            assert not np.shares_memory(a, other)
        arrays.append(a)
        a.flat[0] = 0
    for field in (
        "image_scale",
        "transfer_scale",
        "relative_residual",
        "normalized_residual_rms",
        "normalized_imaginary_rms",
        "calibration_reality_defect",
        "gradient_inf_norm",
    ):
        assert type(getattr(result, field)) is float


def test_full_off_model_jacobian_and_actual_scipy_controls(
    request: pytest.FixtureRequest,
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    e = example(1)
    e.orders.values[0] += 0.27j  # Algebraically valid, deliberately non-Hermitian.
    e.images[2, 1, 0, 3] += 0.13  # A genuinely off-model exposure.
    calls: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    observed: dict[str, Any] = {}
    residual_count = 0
    jacobian_count = 0

    def real_solver(original: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal residual_count, jacobian_count
        bound = inspect.signature(original).bind(*args, **kwargs)
        bound.apply_defaults()
        observed.update(bound.arguments)
        fun, x0, jac = (bound.arguments[name] for name in ("fun", "x0", "jac"))
        assert_allclose(x0, canonical(e.initial), atol=0, rtol=0)

        def residual(x: Any, *args: Any, **kw: Any) -> Any:
            nonlocal residual_count
            residual_count += 1
            return fun(x, *args, **kw)

        def jacobian(x: Any, *args: Any, **kw: Any) -> Any:
            nonlocal jacobian_count
            jacobian_count += 1
            value = jac(x, *args, **kw)
            # Genuine finite public residual probes check the Jacobian sign
            # in whatever fixed row organization the solver actually receives.
            # They return no invented numerical factors or solver result.
            step = 2e-6
            directions = np.eye(len(x)) * step
            finite_difference = np.column_stack(
                [
                    (residual(x + v, *args, **kw) - residual(x - v, *args, **kw)) / (2 * step)
                    for v in directions
                ]
            )
            calls.append((np.array(x), np.array(value), finite_difference))
            return value

        return forward_observed_callbacks(
            original, args, kwargs, {"fun": residual, "jac": jacobian}
        )

    with public_observation(optimizer=real_solver):
        result = estimate(api, e, max_nfev=1)
    assert calls, "the contracted public SciPy boundary must execute"
    for x, actual, finite_difference in calls:
        o = observe(e.images, e.orders.values, x, e.carrier)
        assert np.linalg.norm(o.jac + o.k) > 1e-3
        # Equivalent residual row organization is permitted. Compare column Gram
        # and projected directional derivatives rather than forcing row storage.
        assert_allclose(actual.T @ actual, o.jac.T @ o.jac, atol=2e-10, rtol=2e-10)
        assert_allclose(actual, finite_difference, atol=2e-8, rtol=2e-8)
    assert observed.get("method", "trf") == "trf"
    assert observed.get("loss", "linear") == "linear"
    assert observed.get("x_scale", 1) == 1
    assert observed["tr_solver"] == "exact"
    assert observed["ftol"] is None
    assert observed["gtol"] == 1e-9 and observed["xtol"] == 1e-10
    assert observed["max_nfev"] == 1
    bounds = observed.get("bounds", (-np.inf, np.inf))
    assert np.all(np.asarray(bounds[0]) == -np.inf) and np.all(np.asarray(bounds[1]) == np.inf)
    for name in ("callback", "workers", "jac_sparsity"):
        assert observed.get(name) is None
    assert result.nfev >= residual_count and result.njev >= jacobian_count
    assert result.termination == "evaluation_limit"
    assert result.gradient_inf_norm > 1e-9
    assert result.calibration_reality_defect > 0.1
    assert result.normalized_imaginary_rms > 0.01
    check_observer(result, e)


@pytest.mark.parametrize(
    "mode",
    [
        "zero_transfer",
        "invisible_modes",
        "zero_data",
        "even_only",
        "stationary_uninformative",
        "low_design_rank",
    ],
)
def test_availability_and_ambiguity_are_separate(api: Any, mode: str) -> None:
    e = example(1)
    if mode == "zero_transfer":
        e.orders.values.fill(0)
    elif mode == "invisible_modes":
        e.orders.values.fill(0)
        e.orders.values[0, 1, 0, 2] = 1  # Only DC observes the real specimen mean.
    elif mode == "zero_data":
        e.images.fill(0)
    elif mode == "even_only":
        e.kernels[1].fill(0)
        e.orders = record(transfer_from_kernels(e.kernels))
        e.images = spatial_images(e.specimen, e.kernels, e.truth, e.carrier)
        e.initial = e.truth.copy()
        e.initial[[0, 2]] += np.pi  # Legitimate independent pi alternatives.
    elif mode == "stationary_uninformative":
        shape = (1, 1, 1)
        kernels = np.array([[[[1]]], [[[0.2]]], [[[0.1]]]], dtype=np.complex128)
        truth = np.array([-2.5, -1.3, -0.1, 0.9, 2.4])
        e = Example(
            spatial_images(np.ones(shape), kernels, truth, (0, 0)),
            np.zeros(5),
            truth,
            np.ones(shape),
            kernels,
            record(transfer_from_kernels(kernels)),
            (0, 0),
        )
    else:
        e.initial.fill(0.31)
        e.images = spatial_images(e.specimen, e.kernels, e.initial, e.carrier)
    result = estimate(api, e)
    check_observer(result, e)
    if mode in {"zero_transfer", "invisible_modes"}:
        assert result.termination == "nuisance_rank_deficient"
        assert result.nuisance_rank == (0 if mode == "zero_transfer" else 1)
        assert_allclose(result.phases_rad, canonical(e.initial), atol=0, rtol=0)
        if mode == "zero_transfer":
            assert_array_equal(result.specimen_normalized, np.zeros_like(e.specimen))
            assert result.phase_rank == 0
            assert result.gradient_inf_norm == 0
    else:
        assert result.termination == "stationary"
    if mode == "zero_data":
        assert (
            result.relative_residual
            == result.normalized_residual_rms
            == result.gradient_inf_norm
            == 0
        )
        assert result.phase_rank == 0
    if mode in {"stationary_uninformative", "low_design_rank"}:
        assert result.phase_design_rank < 5
    if mode == "stationary_uninformative":
        assert result.relative_residual > 0.01  # Stationary does not mean accurate.
        assert result.phase_rank == 0


@pytest.mark.parametrize(
    "carrier", [(0, 0), (-(10**100) + 1, 10**100 - 1), (np.uint64(2**64 - 1), np.int64(-7))]
)
def test_periodic_carrier_aliasing_keeps_declared_integers(api: Any, carrier: Any) -> None:
    e = example(0)
    e.carrier = (int(carrier[0]), int(carrier[1]))
    reduced = (e.carrier[0] % 3, e.carrier[1] % 4)
    e.images = spatial_images(e.specimen, e.kernels, e.truth, reduced)
    e.initial = e.truth.copy()
    first = estimate(api, e, carrier_bins_yx=list(carrier))
    second = estimate(api, e, carrier_bins_yx=reduced)
    assert first.carrier_bins_yx == e.carrier
    assert all(type(v) is int for v in first.carrier_bins_yx)
    assert_allclose(first.phases_rad, second.phases_rad, atol=2e-12, rtol=0)
    assert_allclose(first.specimen_normalized, second.specimen_normalized, atol=2e-12, rtol=0)
    check_observer(first, e)


@pytest.mark.parametrize("container", [tuple, list], ids=["tuple", "list"])
@pytest.mark.parametrize(
    "shape",
    [(2, 3, 4), (3, 4, 3), (1, 1, 1), (1, 2, 3), (2, 3, 1), (3, 1, 2), (2, 2, 2), (3, 3, 3)],
)
@pytest.mark.parametrize(
    "carrier",
    [
        (0, 0),
        (1, -1),
        (-7, -11),
        (-(10**100) + 1, 10**100 - 1),
        (2**64 - 1, -7),
        (np.int64(-(2**63)), np.int64(2**63 - 1)),
        (np.uint64(2**64 - 1), np.uint64(2**64 - 2)),
        (np.uint64(2**64 - 1), np.int64(-7)),
        (np.int8(-128), np.uint8(255)),
        (np.int16(-32768), np.uint16(65535)),
        (np.int32(-(2**31)), np.uint32(2**32 - 1)),
        (2**53 + 1, -(2**53 + 3)),
    ],
    ids=[
        "zero",
        "small",
        "negative",
        "python_huge",
        "python_mixed_range",
        "numpy_signed",
        "numpy_unsigned",
        "numpy_mixed",
        "numpy_small_width",
        "numpy_16bit",
        "numpy_32bit",
        "binary64_boundary",
    ],
)
def test_integer_carrier_oracles_against_exact_finite_matrices(
    shape: tuple[int, int, int], carrier: Any, container: Any
) -> None:
    # Supplemental shared-oracle proof. Expected indices use Python integers;
    # exact rational turns independently define the finite Fourier matrices.
    coords = list(np.ndindex(shape))
    bins = list(product(*(range(-(length // 2), (length + 1) // 2) for length in shape)))
    size, n = len(coords), 7
    original = (int(carrier[0]), int(carrier[1]))
    declared = container(carrier)
    reduced = (original[0] % shape[1], original[1] % shape[2])

    def root(turns: Fraction) -> complex:
        turns %= 1
        quarter = 4 * turns
        if quarter.denominator == 1:
            return (1, 1j, -1, -1j)[int(quarter)]
        return complex(np.exp(2j * np.pi * float(turns)))

    def row(mode: tuple[int, ...]) -> Any:
        return np.array(
            [
                root(
                    -sum(
                        (
                            Fraction(k * j, length)
                            for k, j, length in zip(mode, position, shape, strict=True)
                        ),
                        Fraction(),
                    )
                )
                for position in coords
            ]
        ) / np.sqrt(size)

    transform = np.array([row(mode) for mode in bins])
    index = {
        tuple(k % length for k, length in zip(mode, shape, strict=True)): i
        for i, mode in enumerate(bins)
    }
    h = np.zeros(shape)
    h.flat[0] = 0.9
    h.flat[-1] += 0.1
    ramp = np.arange(size).reshape(shape) / (size + 1)
    kernels = np.array(
        [h, (0.2 + 0.11j) * h + (0.01 - 0.02j) * ramp, (-0.09 + 0.08j) * h + (0.02 + 0.01j) * ramp],
        dtype=np.complex128,
    )
    values = np.array(
        [(np.sqrt(size) * transform @ kernel.ravel()).reshape(shape) for kernel in kernels],
        dtype=np.complex128,
    )
    phases = 2 * np.pi * np.arange(n) / n - 2.5

    def signed_matrices(transfers: Any) -> dict[int, Any]:
        result = {}
        for m in range(-2, 3):
            matrix = np.empty((size, size), dtype=np.complex128)
            for ki, mode in enumerate(bins):
                source = tuple(
                    (k - m * shift) % length
                    for k, shift, length in zip(mode, (0, *original), shape, strict=True)
                )
                alias = tuple(
                    (k - m * shift) % length
                    for k, shift, length in zip(mode, (0, *reduced), shape, strict=True)
                )
                assert source == alias
                if m >= 0:
                    gain = transfers[m].ravel()[ki]
                else:
                    negative = tuple(-k % length for k, length in zip(mode, shape, strict=True))
                    gain = transfers[-m].ravel()[index[negative]].conjugate()
                matrix[ki] = gain * row(source)
            result[m] = matrix
        return result

    bands = signed_matrices(values)
    specimen = (np.arange(size).reshape(shape) % 5 - 2) / 3 + 0.2
    prediction: Any = sum(
        np.exp(1j * m * phases)[:, None, None] * band for m, band in bands.items()
    )
    expected_images = ((prediction @ specimen.ravel()) @ transform.conj()).reshape(n, *shape)
    assert np.max(np.abs(expected_images.imag)) < 3e-12
    generated = spatial_images(specimen, kernels, phases, declared)
    assert_allclose(generated, expected_images.real, atol=3e-12, rtol=0)
    assert_array_equal(generated, spatial_images(specimen, kernels, phases, reduced))
    assert all(type(value) is int for value in periodic_carrier(declared, shape))

    # Deliberately off-model inputs exercise residual-dependent derivatives,
    # both component scales, real nuisance and the complex T0 diagnostics too.
    values[0].flat[0] += 0.13j
    generated[2].flat[-1] += 0.017
    b = float(np.max(np.abs(generated))) or 1.0
    t = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag)))) or 1.0
    bands = signed_matrices(values / t)
    model: Any = sum(np.exp(1j * m * phases)[:, None, None] * band for m, band in bands.items())
    derivative: Any = sum(
        1j * m * np.exp(1j * m * phases)[:, None, None] * band for m, band in bands.items()
    )
    a = np.concatenate([model.real.reshape(n * size, size), model.imag.reshape(n * size, size)])
    transformed = generated.reshape(n, size) @ transform.T / b
    y = np.concatenate([transformed.real.ravel(), transformed.imag.ravel()])
    ap = []
    for p in range(n):
        masked = np.zeros_like(derivative)
        masked[p] = derivative[p]
        ap.append(
            np.concatenate(
                [masked.real.reshape(n * size, size), masked.imag.reshape(n * size, size)]
            )
        )
    cutoff = np.finfo(float).eps * max(a.shape)
    plus = np.linalg.pinv(a, rtol=cutoff)
    u = plus @ y
    r = y - a @ u
    d = np.column_stack([v @ u for v in ap])
    k = d - a @ (plus @ d)
    jac = -k - np.column_stack([plus.T @ (v.T @ r) for v in ap])
    observed = observe(generated, values, phases, declared)
    assert observed.b == b and observed.t == t
    for actual, expected in [
        (observed.a, a),
        (observed.y, y),
        (observed.u, u),
        (observed.r, r),
        (observed.d, d),
        (observed.k, k),
        (observed.jac, jac),
    ]:
        assert_allclose(actual, expected, atol=3e-12, rtol=0)
    for actual, expected in zip(observed.ap, ap, strict=True):
        assert_allclose(actual, expected, atol=3e-12, rtol=0)
    actual_model = observed.a[: n * size].reshape(n, size, size) + 1j * observed.a[
        n * size :
    ].reshape(n, size, size)
    for m, band in bands.items():
        extracted = np.einsum("p,pij->ij", np.exp(-1j * m * phases), actual_model) / n
        assert_allclose(extracted, band, atol=3e-12, rtol=0)
    singular = np.linalg.svd(a, compute_uv=False)
    phase_s = np.linalg.svd(k, compute_uv=False)
    assert observed.nuisance_rank == int(np.count_nonzero(singular > cutoff * singular[0]))
    assert_allclose(observed.nuisance_s, singular, atol=3e-12, rtol=0)
    assert_allclose(observed.phase_s, phase_s, atol=3e-12, rtol=0)
    # Claim differential rank only well away from a numerical nullspace.
    phase_cutoff = np.finfo(float).eps * max(k.shape) * phase_s[0]
    if phase_s[-1] > 64 * phase_cutoff:
        assert observed.phase_rank == n
    design = np.column_stack(
        [np.ones(n), np.cos(phases), np.sin(phases), np.cos(2 * phases), np.sin(2 * phases)]
    )
    assert observed.design_rank == np.linalg.matrix_rank(design) == 5
    assert observed.relative == pytest.approx(
        np.linalg.norm(r) / np.linalg.norm(y), abs=3e-12, rel=0
    )
    assert observed.rms == pytest.approx(np.linalg.norm(r) / np.sqrt(n * size), abs=3e-12, rel=0)
    assert observed.imaginary == pytest.approx(
        np.linalg.norm((a @ u)[n * size :]) / np.sqrt(n * size), abs=3e-12, rel=0
    )
    assert observed.gradient == pytest.approx(np.max(np.abs(jac.T @ r)), abs=3e-12, rel=0)
    mirrored = (
        np.array(
            [
                values[0]
                .ravel()[index[tuple(-v % length for v, length in zip(mode, shape, strict=True))]]
                .conjugate()
                for mode in bins
            ]
        )
        / t
    )
    assert observed.reality == pytest.approx(
        np.linalg.norm(values[0].ravel() / t - mirrored) / np.sqrt(size), abs=3e-12, rel=0
    )
    expected_allowance = (
        2**20
        * len(y)
        * (size + n + 1)
        * np.finfo(float).eps
        * (1 + np.linalg.norm(y) + np.linalg.norm(u) + np.linalg.norm(d)) ** 2
    )
    assert observed.allowance == pytest.approx(expected_allowance, abs=3e-12, rel=0)


@pytest.mark.parametrize("group", [0, 1])
def test_fixed_gauge_and_coordinate_translation_covariance(api: Any, group: int) -> None:
    e = example(group)
    base = estimate(api, e)
    alpha = 0.37
    shifted_values = e.orders.values.copy()
    shifted_values[1] *= np.exp(-1j * alpha)
    shifted_values[2] *= np.exp(-2j * alpha)
    changed = estimate(
        api, e, order_otf=record(shifted_values), initial_phases_rad=e.initial + alpha
    )
    assert_allclose(
        canonical(changed.phases_rad - base.phases_rad),
        np.full(len(e.initial), alpha),
        atol=2e-7,
        rtol=0,
    )
    assert_allclose(
        changed.specimen_normalized * changed.image_scale / changed.transfer_scale,
        base.specimen_normalized * base.image_scale / base.transfer_scale,
        atol=2e-7,
        rtol=0,
    )
    shift = (1, 0, 1)
    ky, kx = periodic_carrier(e.carrier, e.specimen.shape)
    delta = 2 * np.pi * (ky * shift[1] / e.specimen.shape[1] + kx * shift[2] / e.specimen.shape[2])
    rolled = estimate(
        api,
        e,
        images=np.roll(e.images, shift, axis=(1, 2, 3)),
        initial_phases_rad=e.initial - delta,
    )
    assert_allclose(canonical(rolled.phases_rad - (base.phases_rad - delta)), 0, atol=2e-7, rtol=0)
    assert_allclose(
        rolled.specimen_normalized,
        np.roll(base.specimen_normalized, shift, axis=(0, 1, 2)),
        atol=2e-7,
        rtol=0,
    )


def test_raw_finite_bead_adapter_to_hidden_specimen_inference(api: Any) -> None:
    e, calibrated_orders = calibrated_example(1)
    # Existing calibration output is an input only. Independent kernel DFT is truth.
    assert_allclose(calibrated_orders.values, e.orders.values, atol=2e-12, rtol=0)
    result = estimate(api, e, order_otf=calibrated_orders)
    e.orders = calibrated_orders
    check_observer(result, e)
    assert result.termination == "stationary"
    phase_budget, _ = local_phase_budget(e)
    assert np.linalg.norm(canonical(result.phases_rad - e.truth)) < 1e-4
    assert np.linalg.norm(canonical(result.phases_rad - e.truth)) <= phase_budget


class ArraySubclass(np.ndarray):
    """A prohibited array representation, paired with ordinary-array positives."""


INVALID_ARRAYS = [
    pytest.param(lambda a: a.tolist(), "invalid", id="list"),
    pytest.param(lambda a: a.view(ArraySubclass), "invalid", id="subclass"),
    pytest.param(lambda a: np.ma.array(a), "invalid", id="masked"),
    *[
        pytest.param(lambda a, d=d: a.astype(d), "invalid", id=f"kind-{d}")
        for d in (bool, complex, object, "U8", "datetime64[D]")
    ],
    pytest.param(lambda a: np.zeros((*a.shape, 1)), "invalid", id="rank"),
    pytest.param(lambda a: a[:4], "invalid", id="count"),
    pytest.param(lambda a: np.full(a.shape, np.nan), "nonfinite", id="nan"),
    pytest.param(lambda a: np.full(a.shape, np.inf), "nonfinite", id="positive-infinity"),
    pytest.param(lambda a: np.full(a.shape, -np.inf), "nonfinite", id="negative-infinity"),
]


@pytest.mark.parametrize("field", ["images", "initial_phases_rad"])
@pytest.mark.parametrize("change,prefix", INVALID_ARRAYS)
def test_image_and_phase_grammar(api: Any, field: str, change: Any, prefix: str) -> None:
    e = example(1)
    original = e.images if field == "images" else e.initial
    value = change(original)
    suffix = "images" if field == "images" else "initial_phases"
    changes = {field: value}
    if (
        field == "images"
        and isinstance(value, np.ndarray)
        and value.shape == (4, *e.images.shape[1:])
    ):
        changes["initial_phases_rad"] = e.initial[:4]
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, e, **changes)
    assert exc.value.code == f"{prefix}_volume_phase_estimation_{suffix}"


@pytest.mark.parametrize(
    "shape", [(7, 0, 1, 2), (7, 1, 0, 2), (7, 1, 2, 0), (7,), (7, 1, 2), (7, 1, 1, 2, 1)]
)
def test_image_shape_rejections(api: Any, shape: tuple[int, ...]) -> None:
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, example(1), images=np.zeros(shape))
    assert exc.value.code == "invalid_volume_phase_estimation_images"


@pytest.mark.parametrize("phase_shape", [(7, 1), (6,), (8,), ()])
def test_initial_count_and_shape(api: Any, phase_shape: tuple[int, ...]) -> None:
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, example(1), initial_phases_rad=np.zeros(phase_shape))
    assert exc.value.code == "invalid_volume_phase_estimation_initial_phases"


@pytest.mark.parametrize(
    "dtype",
    [np.int8, np.int64, np.uint64, np.float16, np.float32, np.float64, ">f8", np.longdouble],
)
@pytest.mark.parametrize("layout", ["fortran", "reverse", "readonly"])
def test_permitted_widths_and_layouts_without_phase_design_requirement(
    api: Any, dtype: Any, layout: str
) -> None:
    e = example(1)
    images = np.arange(e.images.size).reshape(e.images.shape).astype(dtype)
    phases = np.arange(7).astype(dtype)
    if layout == "fortran":
        images = np.asfortranarray(images)
    elif layout == "reverse":
        images = images[..., ::-1]
        phases = phases[::-1]
    else:
        images.flags.writeable = phases.flags.writeable = False
    e.orders.values.fill(0)
    snapshots = [(a.tobytes(), a.strides, a.flags.writeable) for a in (images, phases)]
    result = estimate(api, e, images=images, initial_phases_rad=phases)
    assert result.termination == "nuisance_rank_deficient"
    assert_allclose(result.phases_rad, canonical(phases), atol=0, rtol=0)
    assert result.image_scale == (float(np.max(np.abs(images.astype(np.float64)))) or 1.0)
    for a, (content, strides, writeable) in zip((images, phases), snapshots, strict=True):
        assert a.tobytes() == content and a.strides == strides and a.flags.writeable == writeable


@pytest.mark.parametrize("field", ["images", "initial_phases_rad"])
def test_source_finite_conversion_overflow_if_available(api: Any, field: str) -> None:
    # Native capability is explicit; no skip or claim about an unavailable width.
    if np.finfo(np.longdouble).max <= np.finfo(np.float64).max:
        return
    e = example(1)
    shape = e.images.shape if field == "images" else e.initial.shape
    value = np.full(shape, np.longdouble(np.finfo(float).max) * 2, dtype=np.longdouble)
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, e, **{field: value})
    suffix = "images" if field == "images" else "initial_phases"
    assert exc.value.code == f"nonfinite_volume_phase_estimation_{suffix}"


@pytest.mark.parametrize(
    "field,bad",
    [
        ("carrier_bins_yx", (True, 0)),
        ("carrier_bins_yx", (0, 0.0)),
        ("carrier_bins_yx", np.array([0, 1])),
        ("carrier_bins_yx", (0,)),
        ("carrier_bins_yx", (0, 1, 2)),
        ("carrier_bins_yx", "01"),
        *[("max_nfev", v) for v in (0, -1, True, 1.0, "2", np.array(2))],
        *[
            (name, value)
            for name in ("gradient_tolerance", "step_tolerance")
            for value in (
                True,
                0,
                np.finfo(float).eps,
                -1,
                1,
                np.inf,
                np.nan,
                1j,
                "0.1",
                np.array(0.1),
                10**1000,
            )
        ],
        *[("source", value) for value in (None, 1, "", " \t\n")],
    ],
)
def test_carrier_controls_and_source_rejections(api: Any, field: str, bad: Any) -> None:
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, example(1), **{field: bad})
    code = (
        "invalid_otf_source"
        if field == "source"
        else (
            "invalid_volume_phase_estimation_carrier"
            if field == "carrier_bins_yx"
            else "invalid_volume_phase_estimation_controls"
        )
    )
    assert exc.value.code == code


@pytest.mark.parametrize("max_nfev", [np.int64(1), np.uint64(2**64 - 1), 10**100])
def test_positive_control_scalars_and_no_arbitrary_work_cap(api: Any, max_nfev: Any) -> None:
    e = example(1)
    e.images.fill(0)
    result = estimate(
        api,
        e,
        max_nfev=max_nfev,
        gradient_tolerance=np.float32(1e-5),
        step_tolerance=np.float64(0.5),
    )
    assert result.termination == "stationary"


@pytest.mark.parametrize(
    "field,change",
    [
        ("values", lambda v: v.tolist()),
        ("values", lambda v: v.view(ArraySubclass)),
        ("values", lambda v: v.astype(np.complex64)),
        ("values", lambda v: v.real.copy()),
        ("values", lambda v: v[:2]),
        ("values", lambda v: v[..., :0]),
        ("values", lambda v: np.full(v.shape, complex(0, np.inf))),
        ("fz_per_um", lambda v: v.astype(np.float32)),
        ("fy_per_um", lambda v: v.tolist()),
        ("fx_per_um", lambda v: v.view(ArraySubclass)),
        ("fx_per_um", lambda v: v[:-1]),
        ("fx_per_um", lambda v: v[::-1]),
        ("fx_per_um", lambda v: v + 0.01),
        ("fz_per_um", lambda v: np.full(v.shape, np.nan)),
        ("voxel_size_um", lambda v: np.array(v)),
        ("voxel_size_um", lambda v: (0, v[1], v[2])),
        ("voxel_size_um", lambda v: (True, v[1], v[2])),
        ("voxel_size_um", lambda v: (np.inf, v[1], v[2])),
        ("origin_zyx", lambda v: (-1, 0, 0)),
        ("origin_zyx", lambda v: (3, 0, 0)),
        ("origin_zyx", lambda v: (0.0, 0, 0)),
        ("origin_zyx", lambda v: (False, 0, 0)),
        ("source", lambda v: " "),
        ("source", lambda v: None),
    ],
)
def test_every_calibration_field_is_validated(api: Any, field: str, change: Any) -> None:
    e = example(1)
    broken = copy_order_record(e.orders, **{field: change(getattr(e.orders, field))})
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, e, order_otf=broken)
    assert exc.value.code == "invalid_volume_phase_estimation_otf"


def test_otf_instance_and_subclass_getter_semantics(api: Any) -> None:
    e = example(1)
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, e, order_otf=object())
    assert exc.value.code == "invalid_volume_phase_estimation_otf"

    class Missing(simrecon.VolumeOrderOtf):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                raise AttributeError("missing required public values")
            return super().__getattribute__(name)

    class Broken(simrecon.VolumeOrderOtf):
        def __getattribute__(self, name: str) -> Any:
            if name == "source":
                raise RuntimeError("unrelated public getter failure")
            return super().__getattribute__(name)

    class Ordinary(simrecon.VolumeOrderOtf):
        pass

    fields = {name: getattr(e.orders, name) for name in ORDER_FIELDS}
    with pytest.raises(simrecon.SimreconError) as exc:
        estimate(api, e, order_otf=Missing(**fields))
    assert exc.value.code == "invalid_volume_phase_estimation_otf"
    with pytest.raises(RuntimeError, match="unrelated public getter failure"):
        estimate(api, e, order_otf=Broken(**fields))
    e.initial = e.truth.copy()
    result = estimate(api, e, order_otf=Ordinary(**fields))
    check_observer(result, e)


def test_calibration_endian_storage_and_frequency_tolerance_positive(api: Any) -> None:
    e = example(0)
    e.initial = e.truth.copy()
    fields: dict[str, Any] = {}
    for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
        a = getattr(e.orders, name)
        padded = np.empty(
            (*a.shape[:-1], 2 * a.shape[-1]), dtype=">c16" if name == "values" else ">f8"
        )
        padded[..., ::2] = a
        view = padded[..., ::2]
        if name != "values":
            view[...] = np.nextafter(view, np.copysign(np.inf, view))
            view[a == 0] = 0
        view.flags.writeable = False
        fields[name] = view
    alternate = copy_order_record(
        e.orders,
        **fields,
        voxel_size_um=list(e.orders.voxel_size_um),
        origin_zyx=list(e.orders.origin_zyx),
    )
    result = estimate(api, e, order_otf=alternate)
    check_observer(result, e)


@pytest.mark.parametrize("which", ["maximum", "subnormal", "zero", "huge_angles"])
def test_component_scales_extreme_finite_values_and_canonical_angles(api: Any, which: str) -> None:
    shape = (1, 1, 1)
    huge = np.finfo(float).max
    q = np.nextafter(0.0, 1.0)
    initial = np.array([huge, -huge, np.pi, -np.pi, 0.0])
    values = np.zeros((3, *shape), dtype=np.complex128)
    images = np.zeros((5, *shape))
    if which == "maximum":
        values[0].real = huge
        values[0].imag = huge  # A complex-magnitude norm would overflow.
        images.fill(huge)
    elif which == "subnormal":
        values[0].real = q
        images.fill(q)
    elif which == "huge_angles":
        images[:, 0, 0, 0] = [-2, 1, -1, 3, 0]
    e = Example(images, initial, initial, np.zeros(shape), values.copy(), record(values), (0, 0))
    result = estimate(api, e)
    check_observer(result, e)
    assert_allclose(result.phases_rad, canonical(initial), atol=0, rtol=0)
    if which == "maximum":
        assert result.image_scale == result.transfer_scale == huge
        assert_allclose(result.specimen_normalized, 0.5, atol=1e-14, rtol=0)
        assert result.normalized_imaginary_rms == pytest.approx(0.5, abs=1e-14)
        assert result.calibration_reality_defect == 2.0
    elif which == "subnormal":
        assert result.image_scale == result.transfer_scale == q
        assert_allclose(result.specimen_normalized, 1, atol=1e-14, rtol=0)
    elif which == "zero":
        assert result.image_scale == result.transfer_scale == 1.0


@pytest.mark.parametrize(
    "error_type,code",
    [
        (FloatingPointError, "volume_phase_estimation_transform_failure"),
        (OverflowError, "volume_phase_estimation_transform_failure"),
        (RuntimeWarning, "volume_phase_estimation_transform_failure"),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
        (MemoryError, None),
    ],
)
def test_genuine_fft_failure_and_unrelated_exception_propagation(
    request: pytest.FixtureRequest, error_type: Any, code: str | None
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    e = example(1)
    snapshots = [a.tobytes() for a in (e.images, e.initial, e.orders.values)]
    marker = error_type("public FFT failure")

    def failing(original: Any, *args: Any, **kwargs: Any) -> Any:
        if error_type is RuntimeWarning:
            warnings.warn("public FFT failure", RuntimeWarning, stacklevel=1)
            # Genuine bounded transform result if caller incorrectly ignores it.
            return original(*args, **kwargs)
        raise marker

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with (
            public_observation(fft=failing),
            pytest.raises(simrecon.SimreconError if code else error_type) as exc,
        ):
            estimate(api, e)
    if code:
        assert exc.value.code == code
    else:
        assert exc.value is marker
    assert [a.tobytes() for a in (e.images, e.initial, e.orders.values)] == snapshots


@pytest.mark.parametrize(
    "error_type,code",
    [
        (np.linalg.LinAlgError, "volume_phase_estimation_solver_failure"),
        (FloatingPointError, "volume_phase_estimation_solver_failure"),
        (OverflowError, "volume_phase_estimation_solver_failure"),
        (RuntimeWarning, "volume_phase_estimation_solver_failure"),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
        (MemoryError, None),
    ],
)
def test_genuine_optimizer_failure_and_unrelated_propagation(
    request: pytest.FixtureRequest, error_type: Any, code: str | None
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    marker = error_type("public solver failure")

    def failing(original: Any, *args: Any, **kwargs: Any) -> Any:
        if error_type is RuntimeWarning:
            warnings.warn("public solver failure", RuntimeWarning, stacklevel=1)
            return original(*args, **kwargs)
        raise marker

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with (
            public_observation(optimizer=failing),
            pytest.raises(simrecon.SimreconError if code else error_type) as exc,
        ):
            estimate(api, example(1))
    if code:
        assert exc.value.code == code
    else:
        assert exc.value is marker


@pytest.mark.parametrize("failure", [False, True])
def test_input_preservation_and_caller_numerical_warning_policy(api: Any, failure: bool) -> None:
    e = example(1)
    e.initial = e.truth.copy()
    arrays = [
        e.images,
        e.initial,
        e.orders.values,
        e.orders.fz_per_um,
        e.orders.fy_per_um,
        e.orders.fx_per_um,
    ]
    for a in arrays:
        a.flags.writeable = False
    before = [(a.tobytes(), a.strides, a.flags.writeable) for a in arrays]
    with np.errstate(all="raise"), warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        filters = list(warnings.filters)
        mode = np.geterr().copy()
        if failure:
            with pytest.raises(simrecon.SimreconError):
                estimate(api, e, max_nfev=0)
        else:
            estimate(api, e)
        assert np.geterr() == mode
        assert warnings.filters == filters
    for a, (content, strides, writeable) in zip(arrays, before, strict=True):
        assert a.tobytes() == content and a.strides == strides and a.flags.writeable == writeable


def test_unrelated_warning_visible_at_fft_boundary(
    request: pytest.FixtureRequest,
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    e = example(1)
    e.initial = e.truth.copy()

    def warning_fft(original: Any, *args: Any, **kwargs: Any) -> Any:
        warnings.warn("unrelated FFT observer warning", UserWarning, stacklevel=1)
        return original(*args, **kwargs)

    with (
        public_observation(fft=warning_fft),
        pytest.warns(UserWarning, match="unrelated FFT observer warning"),
    ):
        estimate(api, e)


def test_real_step_stagnation_is_not_stationarity(api: Any) -> None:
    e = example(1)
    # A large permitted step tolerance induces an actual positive xtol stop.
    # No fabricated finite OptimizeResult supplies the classification.
    result = estimate(api, e, gradient_tolerance=4 * np.finfo(float).eps, step_tolerance=0.9)
    o = observe(e.images, e.orders.values, result.phases_rad, e.carrier)
    assert o.gradient > 4 * np.finfo(float).eps
    assert result.termination == "stagnated"
    assert result.gradient_inf_norm == pytest.approx(o.gradient, abs=5e-10, rel=0)


def test_joint_exposure_permutation_and_common_scales(api: Any) -> None:
    e = example(1)
    first = estimate(api, e)
    permutation = np.array([3, 0, 6, 1, 5, 2, 4])
    second = estimate(
        api,
        e,
        images=e.images[permutation] * 4,
        initial_phases_rad=e.initial[permutation],
        order_otf=copy_order_record(e.orders, values=e.orders.values * 2),
    )
    assert_allclose(
        canonical(second.phases_rad - first.phases_rad[permutation]), 0, atol=2e-7, rtol=0
    )
    assert_allclose(second.specimen_normalized, first.specimen_normalized, atol=2e-7, rtol=0)
    assert second.image_scale == first.image_scale * 4
    assert second.transfer_scale == first.transfer_scale * 2


def test_huge_initial_phases_drive_nonzero_fundamental_and_second_order(api: Any) -> None:
    e = example(1)
    largest = np.finfo(float).max
    e.initial = np.array([largest, -largest, 1e300, -1e300, np.pi, -np.pi, 0.0])
    e.truth = canonical(e.initial)
    e.images = spatial_images(e.specimen, e.kernels, e.truth, e.carrier)
    result = estimate(api, e)
    assert result.termination == "stationary"
    assert_allclose(result.phases_rad, e.truth, atol=2e-12, rtol=0)
    check_observer(result, e)


def test_deficient_nonzero_design_uses_algebraic_truncated_diagnostics(
    request: pytest.FixtureRequest,
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    shape = (1, 1, 5)
    values = np.zeros((3, *shape), dtype=np.complex128)
    values[:, 0, 0, 2] = [1 + 0.23j, 0.2 + 0.15j, 0.11 - 0.07j]
    initial = np.array([-2.8, -1.3, -0.2, 0.9, 2.4])
    images = np.arange(25, dtype=float).reshape(5, *shape) / 7 - 1
    e = Example(images, initial, initial, np.zeros(shape), values.copy(), record(values), (0, 0))
    o = observe(images, values, canonical(initial), (0, 0))
    assert o.nuisance_rank == 1
    assert np.linalg.norm(o.d) > 0.1
    assert np.linalg.norm(o.jac + o.k) > 0.01

    def forbidden_optimizer(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("a deficient initial point must not run the optimizer")

    with public_observation(optimizer=forbidden_optimizer):
        result = estimate(api, e)
    assert result.termination == "nuisance_rank_deficient"
    assert result.nuisance_rank == 1
    assert_allclose(result.phases_rad, canonical(initial), atol=0, rtol=0)
    check_observer(result, e)


def test_mismatched_fixed_order_gains_are_not_refitted(api: Any) -> None:
    e = example(1)
    e.initial = e.truth.copy()
    e.orders.values[1] *= 1.7 * np.exp(0.2j)
    e.orders.values[2] *= 0.6 * np.exp(-0.3j)
    initial = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    assert initial.rms > 1e-3
    result = estimate(api, e, max_nfev=1)
    assert result.termination == "evaluation_limit"
    assert_allclose(result.phases_rad, canonical(e.initial), atol=0, rtol=0)
    assert result.normalized_residual_rms > 1e-3
    check_observer(result, e)


def test_all_input_snapshots_precede_observation_transform(
    request: pytest.FixtureRequest,
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    e = example(1)
    e.initial = e.truth.copy()
    pristine_images = e.images.copy()
    pristine_initial = e.initial.copy()
    pristine_values = e.orders.values.copy()
    entered = False

    def transform_after_external_change(original: Any, *args: Any, **kwargs: Any) -> Any:
        nonlocal entered
        if not entered:
            entered = True
            e.images.fill(0)
            e.initial.fill(0)
            e.orders.values.fill(0)
            e.orders.fx_per_um.fill(np.nan)
        return original(*args, **kwargs)

    with public_observation(fft=transform_after_external_change):
        result = estimate(api, e)
    assert entered
    # This synchronous public-boundary observer tests the before-numerics
    # snapshot promise. It makes no concurrent-mutation guarantee.
    e.images = pristine_images
    e.initial = pristine_initial
    e.orders = record(pristine_values)
    check_observer(result, e)
    assert_allclose(result.phases_rad, canonical(pristine_initial), atol=2e-12, rtol=0)


def test_extreme_canonical_calibration_grid_avoids_period_overflow(api: Any) -> None:
    shape = (1, 1, 5)
    largest = np.finfo(float).max
    tiny = np.nextafter(0.0, 1.0)
    values = np.zeros((3, *shape), dtype=np.complex128)
    orders = record(values)
    fx = np.array([float(Fraction(k) / 5 / Fraction(float(largest))) for k in range(-2, 3)])
    orders = copy_order_record(orders, voxel_size_um=(largest, tiny, largest), fx_per_um=fx)
    initial = np.arange(5, dtype=float)
    images = np.ones((5, *shape))
    e = Example(images, initial, initial, np.zeros(shape), values.copy(), orders, (0, 0))
    result = estimate(api, e)
    assert result.termination == "nuisance_rank_deficient"
    assert result.nuisance_rank == 0


def test_permitted_normalization_underflow_does_not_reject(api: Any) -> None:
    e = example(1)
    e.orders.values.fill(0)
    e.orders.values[0].real = np.finfo(float).max
    e.orders.values[1].real = np.nextafter(0.0, 1.0)
    e.images.fill(np.finfo(float).max)
    with np.errstate(all="raise"):
        result = estimate(api, e)
    assert result.termination == "stationary"
    assert result.transfer_scale == result.image_scale == np.finfo(float).max
    assert_allclose(result.specimen_normalized, np.ones_like(e.specimen), atol=2e-12, rtol=0)
    assert result.relative_residual < 1e-12


def test_genuine_trial_rank_change_returns_initial_availability(api: Any) -> None:
    # Off-model DC pins the amplitude; the weak Nyquist response tends to zero
    # as the real trust-region trial moves the equal phases from one to zero.
    # Initial rank is far above cutoff, and rank at zero is exactly deficient.
    values = np.zeros((3, 1, 1, 2), dtype=np.complex128)
    values[0, 0, 0, 1], values[1, 0, 0, 1] = 1 + 0.4j, 0.2
    values[0, 0, 0, 0], values[1, 0, 0, 0] = 1e-10, -0.5e-10
    images = np.ones((5, 1, 1, 2))
    initial = np.ones(5)
    e = Example(
        images, initial, initial, np.zeros((1, 1, 2)), values.copy(), record(values), (0, 0)
    )
    first = observe(images, values, initial, (0, 0))
    lost = observe(images, values, np.zeros(5), (0, 0))
    assert first.nuisance_rank == 2 and first.nuisance_s[-1] > 1e-11
    assert lost.nuisance_rank == 1
    result = estimate(api, e)
    assert result.termination == "rank_changed"
    assert_allclose(result.phases_rad, canonical(initial), atol=0, rtol=0)
    # This case is outside the informative arithmetic regime. Its exact Fourier
    # directions decouple. Compare the mean nuisance and fit, not a uniform
    # digit guarantee for its weak unobserved Nyquist coordinate.
    assert np.mean(result.specimen_normalized) == pytest.approx(np.mean(first.u), abs=2e-12)
    assert result.nuisance_rank == first.nuisance_rank
    assert result.normalized_residual_rms == pytest.approx(first.rms, abs=2e-12)
    assert result.gradient_inf_norm == pytest.approx(first.gradient, abs=2e-10)
    assert_allclose(result.nuisance_singular_values, first.nuisance_s, atol=2e-12, rtol=0)
    assert_allclose(result.phase_singular_values, first.phase_s, atol=2e-10, rtol=0)
    assert result.global_ambiguity == "unassessed"
    assert type(result.nfev) is int and result.nfev > 0
    assert type(result.njev) is int and result.njev > 0


def test_proportional_kernel_point_specimen_keeps_ambiguity_unassessed(api: Any) -> None:
    e = example(1)
    h = e.kernels[0].real
    e.kernels = np.array([h, (0.21 + 0.08j) * h, (0.11 - 0.07j) * h])
    e.specimen.fill(0)
    e.specimen[1, 0, 2] = 3
    e.orders = record(transfer_from_kernels(e.kernels))
    e.images = spatial_images(e.specimen, e.kernels, e.truth, e.carrier)
    e.initial = e.truth.copy()
    result = estimate(api, e)
    check_observer(result, e)
    assert result.termination == "stationary"
    assert result.phase_singular_values[-1] < 1e-10
    assert result.global_ambiguity == "unassessed"


def test_weak_nonzero_side_orders_have_no_arbitrary_information_threshold(api: Any) -> None:
    e = example(1)
    e.kernels[1:] *= 1e-8
    e.orders = record(transfer_from_kernels(e.kernels))
    e.images = spatial_images(e.specimen, e.kernels, e.truth, e.carrier)
    e.initial = e.truth.copy()
    o = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    assert o.phase_rank == len(e.initial)
    assert 1e-10 < o.phase_s[-1] < 1e-6
    result = estimate(api, e)
    assert result.termination == "stationary"
    assert result.phase_rank == len(e.initial)
    check_observer(result, e)


@pytest.mark.parametrize(
    "error_type,code",
    [
        (np.linalg.LinAlgError, "volume_phase_estimation_solver_failure"),
        (RuntimeError, None),
        (TypeError, None),
        (ValueError, None),
        (MemoryError, None),
    ],
)
def test_genuine_initial_nuisance_svd_failure_before_optimizer(
    request: pytest.FixtureRequest,
    error_type: Any,
    code: str | None,
) -> None:
    if run_dependency_child(request):
        return
    api = phase_api()
    e = example(1)
    before = [a.tobytes() for a in (e.images, e.initial, e.orders.values)]
    marker = error_type("initial public nuisance SVD failure")
    initial = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    failing_svd = NuisanceSvdFailure(initial.nuisance_s, marker)

    def forbidden_optimizer(original: Any, *args: Any, **kwargs: Any) -> Any:
        pytest.fail("initial nuisance SVD failure must precede optimizer entry")

    with (
        public_observation(svd=failing_svd, optimizer=forbidden_optimizer) as observed,
        pytest.raises(simrecon.SimreconError if code else error_type) as exc,
    ):
        estimate(api, e)
    assert failing_svd.matched_shapes, "no independent initial nuisance decomposition witness"
    assert all(category != "optimizer" for category, _ in observed.events)
    if code:
        assert exc.value.code == code
    else:
        assert exc.value is marker
    assert [a.tobytes() for a in (e.images, e.initial, e.orders.values)] == before


@pytest.mark.parametrize("binding", ["direct", "module"])
@pytest.mark.parametrize(
    "surface",
    [
        "numpy_svd",
        "numpy_svdvals",
        "numpy_lstsq",
        "scipy_svd",
        "scipy_svdvals",
        "scipy_lstsq",
        "scipy_interpolative_svd",
        "scipy_sparse_svds",
        "lapack_gesvd",
        "lapack_gesdd",
        "factory_gesvd",
        "factory_gesdd",
        "fft",
        "optimizer",
    ],
)
def test_public_dependency_bootstrap_admits_binding_and_backend_alternatives(
    request: pytest.FixtureRequest,
    surface: str,
    binding: str,
) -> None:
    # This validates the observer, not scientific product behavior. It remains
    # executable on the missing-API baseline and uses real dependency results.
    if run_dependency_child(request):
        return
    import scipy.linalg
    import scipy.linalg.interpolative
    import scipy.linalg.lapack
    import scipy.optimize
    import scipy.sparse.linalg

    identity = np.eye(2)
    surfaces = {
        "numpy_svd": (np.linalg, "svd", (identity,)),
        "numpy_svdvals": (np.linalg, "svdvals", (identity,)),
        "numpy_lstsq": (np.linalg, "lstsq", (identity, np.ones(2))),
        "scipy_svd": (scipy.linalg, "svd", (identity,)),
        "scipy_svdvals": (scipy.linalg, "svdvals", (identity,)),
        "scipy_lstsq": (scipy.linalg, "lstsq", (identity, np.ones(2))),
        "scipy_interpolative_svd": (scipy.linalg.interpolative, "svd", (identity, 2)),
        "scipy_sparse_svds": (
            scipy.sparse.linalg,
            "svds",
            (np.array([[3.0, 0.0], [0.0, 1.0], [0.2, 0.4], [0.3, -0.2]]),),
        ),
        "lapack_gesvd": (scipy.linalg.lapack, "dgesvd", (identity,)),
        "lapack_gesdd": (scipy.linalg.lapack, "dgesdd", (identity,)),
        "factory_gesvd": (scipy.linalg, "get_lapack_funcs", ("gesvd", (identity,))),
        "factory_gesdd": (scipy.linalg.lapack, "get_lapack_funcs", ("gesdd", (identity,))),
        "fft": (np.fft, "fftn", (np.ones((1, 2, 3)),)),
        "optimizer": (scipy.optimize, "least_squares", (lambda x: x - 1, np.zeros(1))),
    }
    module, name, args = surfaces[surface]
    direct = getattr(module, name)
    kwargs = {"k": 2, "solver": "propack", "rng": 21} if surface == "scipy_sparse_svds" else {}
    if surface.startswith("factory_"):
        # Bind a LAPACK handle before the armed call, just like a direct import.
        direct = direct(*args)
        call = (
            (lambda: direct(identity))
            if binding == "direct"
            else (lambda: getattr(module, name)(*args)(identity))
        )
    else:
        call = (
            (lambda: direct(*args, **kwargs))
            if binding == "direct"
            else (lambda: getattr(module, name)(*args, **kwargs))
        )
    call()  # Normal setup must perform genuine arithmetic without an injection.
    marker = RuntimeError("armed public dependency probe")

    def injected(original: Any, *args: Any, **kwargs: Any) -> Any:
        raise marker

    category = surface if surface in {"fft", "optimizer"} else "svd"
    with (
        public_observation(**{category: injected}) as observed,
        pytest.raises(RuntimeError) as exc,
    ):
        call()
    assert exc.value is marker
    assert observed.events and all(event[0] == category for event in observed.events)
    call()  # Disarming restores ordinary computation for later oracle checks.


@pytest.mark.parametrize("binding", ["direct", "module"])
@pytest.mark.parametrize("backend", ["numpy_svd", "scipy_lstsq", "lapack_factory"])
@pytest.mark.parametrize(
    "organization",
    [
        "full",
        "transpose",
        "column_permuted",
        "orthogonal",
        "qr_scaled",
        "spatial",
        "padded_batch",
        "spectral_block",
    ],
)
def test_nuisance_fault_reaches_past_design_and_decoy_decompositions(
    request: pytest.FixtureRequest,
    organization: str,
    backend: str,
    binding: str,
) -> None:
    # Genuine public dependency executions establish the targeting mechanism;
    # this harness proof is independent of the absent new product API.
    if run_dependency_child(request):
        return
    import scipy.linalg

    e = example(1)
    o = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    a = o.a
    n, size = len(e.initial), e.specimen.size
    c, s = np.cos(canonical(e.initial)), np.sin(canonical(e.initial))
    design = np.column_stack([np.ones(n), c, s, c * c - s * s, (2 * c) * s])
    design_expected = np.linalg.svd(design, compute_uv=False)
    decoy = np.pad(np.eye(size), ((0, len(a) - size), (0, 0)))
    target = a.copy()
    if organization == "transpose":
        target = a.T.copy()
    elif organization == "column_permuted":
        target = a[::-1, ::-1].copy(order="F")
    elif organization == "orthogonal":
        row = np.arange(1, len(a) + 1, dtype=float)
        row /= np.linalg.norm(row)
        column = np.arange(1, size + 1, dtype=float)
        column /= np.linalg.norm(column)
        left = a - 2 * np.outer(row, row @ a)
        target = left - 2 * np.outer(left @ column, column)
    elif organization == "qr_scaled":
        _, triangular = np.linalg.qr(a, mode="reduced")
        target = -7.25 * triangular
    elif organization == "spatial":
        # U* maps Fourier rows into real-compatible spatial observations.
        from volume_phase_estimation_fixture import fourier_matrix

        transform = fourier_matrix(e.specimen.shape)
        complex_a = a[: n * size].reshape(n, size, size) + 1j * a[n * size :].reshape(n, size, size)
        spatial = np.array([transform.conj().T @ row for row in complex_a], dtype=np.complex128)
        assert np.max(np.abs(spatial.imag)) < 1e-13
        target = spatial.real.reshape(n * size, size)
    elif organization == "padded_batch":
        target = np.zeros((2, len(a) + 3, size + 2))
        target[0, :n, :5] = design
        target[1, : len(a), :size] = a
    elif organization == "spectral_block":
        left, _, right = np.linalg.svd(a, full_matrices=False)
        diagonal = left.T @ a @ right.T
        target = 3.5 * diagonal[5:12, 5:12]

    if backend == "numpy_svd":
        module, name = np.linalg, "svd"
    elif backend == "scipy_lstsq":
        module, name = scipy.linalg, "lstsq"
    else:
        module, name = scipy.linalg, "get_lapack_funcs"
    direct = getattr(module, name)

    def decomposition(matrix: Any) -> Any:
        if matrix.ndim > 2 and backend != "numpy_svd":
            return [decomposition(part) for part in matrix]
        function = direct if binding == "direct" else getattr(module, name)
        if backend == "numpy_svd":
            return function(matrix, compute_uv=False)
        if backend == "scipy_lstsq":
            return function(matrix, np.zeros(matrix.shape[0]), lapack_driver="gelsd")[3]
        return function("gesvd", (matrix,))(matrix, compute_uv=0)[1]

    marker = RuntimeError("independently recognized initial nuisance decomposition")
    fault = NuisanceSvdFailure(o.nuisance_s, marker)
    with public_observation(svd=fault):
        # The diagnosed legitimate preceding 7x5 design computation must finish.
        assert_allclose(
            np.sort(decomposition(design)), np.sort(design_expected), atol=2e-13, rtol=0
        )
        # Same shape as A, different spectrum: shape alone cannot target a call.
        assert_allclose(decomposition(decoy), np.ones(size), atol=2e-13, rtol=0)
        assert not fault.matched_shapes
        with pytest.raises(RuntimeError) as exc:
            decomposition(target)
    assert exc.value is marker
    assert fault.passed_shapes and fault.matched_shapes


@pytest.mark.parametrize("binding", ["direct", "module"])
def test_nuisance_fault_recognizes_public_linear_operator_operand(
    request: pytest.FixtureRequest,
    binding: str,
) -> None:
    if run_dependency_child(request):
        return
    import scipy.sparse.linalg

    e = example(1)
    o = observe(e.images, e.orders.values, canonical(e.initial), e.carrier)
    c, s = np.cos(canonical(e.initial)), np.sin(canonical(e.initial))
    design = np.column_stack([np.ones(len(c)), c, s, c * c - s * s, (2 * c) * s])
    design_operator = scipy.sparse.linalg.aslinearoperator(design)
    nuisance_operator = scipy.sparse.linalg.aslinearoperator(o.a)
    direct = scipy.sparse.linalg.svds

    def decomposition(operator: Any) -> Any:
        function = direct if binding == "direct" else scipy.sparse.linalg.svds
        return function(operator, k=2, solver="propack", rng=21)

    marker = MemoryError("recognized public nuisance LinearOperator")
    fault = NuisanceSvdFailure(o.nuisance_s, marker)
    with public_observation(svd=fault):
        _, singular_values, _ = decomposition(design_operator)
        assert np.all(np.isfinite(singular_values)) and np.all(singular_values > 0)
        assert not fault.matched_shapes
        with pytest.raises(MemoryError) as exc:
            decomposition(nuisance_operator)
    assert exc.value is marker
    assert fault.passed_shapes and fault.matched_shapes


@pytest.mark.parametrize("binding", ["direct", "module"])
@pytest.mark.parametrize(
    "call_form",
    ["standard", "jac_positional", "prefix_controls", "all_keywords", "callback_arguments"],
)
def test_scipy_observer_preserves_genuine_call_form_and_controls(
    request: pytest.FixtureRequest,
    call_form: str,
    binding: str,
) -> None:
    # Supplemental postimplementation test-correction regression. The genuine
    # public dependency, not a fabricated solver result, supplies every result.
    if run_dependency_child(request):
        return
    import scipy.optimize

    direct = scipy.optimize.least_squares
    x0 = np.zeros(1)

    def residual(x: Any, offset: float = 1.0, scale: float = 2.0) -> Any:
        return np.array([x[0] - offset, scale * (x[0] - offset)])

    def jacobian(x: Any, offset: float = 1.0, scale: float = 2.0) -> Any:
        return np.array([[1.0], [scale]])

    controls: dict[str, Any] = dict(
        jac=jacobian,
        method="trf",
        bounds=(-np.inf, np.inf),
        loss="linear",
        x_scale=1,
        tr_solver="exact",
        ftol=None,
        gtol=1e-9,
        xtol=1e-10,
        max_nfev=1,
    )
    offset, scale = 1.0, 2.0
    if call_form == "callback_arguments":
        offset, scale = 1.25, 3.0
        controls.update(args=(offset,), kwargs={"scale": scale})
    expected_cost = 0.5 * offset**2 * (1 + scale**2)
    args: tuple[Any, ...] = (residual, x0)
    kwargs = controls.copy()
    if call_form == "jac_positional":
        args = (residual, x0, kwargs.pop("jac"))
    elif call_form == "prefix_controls":
        args = (residual, x0, kwargs.pop("jac"), kwargs.pop("bounds"), kwargs.pop("method"))
    elif call_form == "all_keywords":
        args = ()
        kwargs.update(fun=residual, x0=x0)
    supplied_args = args
    supplied_kwargs = kwargs.copy()

    def solve() -> Any:
        function = direct if binding == "direct" else scipy.optimize.least_squares
        return function(*args, **kwargs)

    baseline = solve()  # Establish that this actual decorated public call works.
    assert baseline.status == 0 and baseline.nfev == baseline.njev == 1
    assert baseline.cost == expected_cost
    residual_calls = 0
    jacobian_calls = 0
    observed: dict[str, Any] = {}

    def observer(original: Any, *incoming: Any, **named: Any) -> Any:
        bound = inspect.signature(original).bind(*incoming, **named)
        bound.apply_defaults()  # Observation only; never replay these containers.
        observed.update(bound.arguments)
        assert len(incoming) == len(args) and set(named) == set(kwargs)

        def real_residual(x: Any, *extra: Any, **kw: Any) -> Any:
            nonlocal residual_calls
            residual_calls += 1
            return bound.arguments["fun"](x, *extra, **kw)

        def real_jacobian(x: Any, *extra: Any, **kw: Any) -> Any:
            nonlocal jacobian_calls
            jacobian_calls += 1
            return bound.arguments["jac"](x, *extra, **kw)

        return forward_observed_callbacks(
            original, incoming, named, {"fun": real_residual, "jac": real_jacobian}
        )

    with public_observation(optimizer=observer) as observation:
        result = solve()
    assert observation.events
    assert result.status == 0 and result.nfev == result.njev == 1
    assert result.cost == expected_cost  # Analytic quadratic; not product-derived truth.
    assert_allclose(result.x, x0, atol=0, rtol=0)
    assert_allclose(result.fun, [-offset, -scale * offset], atol=0, rtol=0)
    assert_allclose(result.jac, [[1], [scale]], atol=0, rtol=0)
    assert residual_calls == result.nfev and jacobian_calls == result.njev
    for name, expected in controls.items():
        assert observed[name] == expected
    assert observed["workers"] is None and observed["callback"] is None
    assert observed["jac_sparsity"] is None
    assert args is supplied_args and kwargs.keys() == supplied_kwargs.keys()
    assert all(kwargs[name] is value for name, value in supplied_kwargs.items())
