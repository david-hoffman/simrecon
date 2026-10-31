"""Blind public-contract RA08 tests. Expectations precede product observation."""

from __future__ import annotations

import dataclasses
import importlib
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

from reference_alignment_ra08_fixture import (
    ATOL,
    BUDGET,
    EPS,
    RTOL,
    arithmetic_tolerance,
    display_reference,
    exact_minimizer,
    geometry,
    matrix_for,
    normal_system,
    optimality,
    periodic_matrix,
    score_reference,
    tiny,
)


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Any:
    # Missing public module is legitimate baseline red, not a static type error.
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    return importlib.import_module("scripts.finite_field_reconstruction")


def close(actual: Any, expected: Any, *, terms: int = 256) -> None:
    np.testing.assert_allclose(
        actual, expected, atol=arithmetic_tolerance(expected, terms=terms), rtol=0
    )


def array_contract(value: Any, shape: tuple[int, ...], *, writable: bool = True) -> None:
    assert type(value) is np.ndarray
    assert value.shape == shape
    assert value.dtype == np.dtype("float64") and value.dtype.isnative
    assert value.flags.c_contiguous and value.flags.owndata
    assert bool(value.flags.writeable) is writable
    assert np.all(np.isfinite(value))


def no_alias(arrays: list[NDArray[Any]]) -> None:
    for i, x in enumerate(arrays):
        for y in arrays[i + 1 :]:
            assert not np.shares_memory(x, y)


def expect_error(code: str, call: Any) -> None:
    with pytest.raises(Exception) as caught:
        call()
    assert type(caught.value).__name__ == "SimreconError"
    assert getattr(caught.value, "code", None) == code


def solve(api: Any, op: Any, y: Any, **changes: Any) -> Any:
    args = dict(
        images=y,
        regularization=0.2,
        nonnegative=False,
        max_iterations=BUDGET,
        absolute_tolerance=ATOL,
        relative_tolerance=RTOL,
        output_taper=np.ones(op.illumination.shape[2:]),
        output_zoom=1,
    )
    args.update(changes)
    return api.solve_finite_field(op, **args)


def gradient_roundoff_budget(
    matrix: NDArray[Any],
    spec: dict[str, Any],
    x: NDArray[Any],
    y: NDArray[Any],
    alpha: float,
) -> float:
    """Bound control-scale cancellation error using absolute finite-sum operands."""
    # gamma_n scales with the operands before cancellation, not with ||g|| or
    # an arbitrary unit floor. The factor 32 allows both evaluations' products,
    # reductions and stable FFT roundoff for the small declared workspaces.
    workspace_depth = sum((size - 1).bit_length() for size in spec["padding_shape_zyx"])
    operations = 32 * (x.size + y.size + workspace_depth + 8)
    gamma = operations * EPS / (1 - operations * EPS)
    abs_x = np.abs(x.ravel())
    residual_scale = np.abs(matrix) @ abs_x + np.abs(y.ravel())
    gradient_scale = (
        np.abs(matrix).T @ (spec["input_taper"].ravel() ** 2 * residual_scale) / y.size
        + alpha * abs_x / x.size
    )
    return float(gamma * np.max(gradient_scale))


def threshold_roundoff_budget(atol: float, rtol: float, rho0: float, rho0_error: float) -> float:
    """Propagate initial-gradient error and scalar multiply/add rounding."""
    return abs(rtol) * rho0_error + 8 * EPS * (abs(atol) + abs(rtol * rho0))


def check_fit(
    fit: Any,
    spec: dict[str, Any],
    y: NDArray[Any],
    alpha: float,
    nonnegative: bool,
    *,
    budget: int = BUDGET,
    atol: float = ATOL,
    rtol: float = RTOL,
) -> None:
    a = matrix_for(spec)
    expected = score_reference(a, spec["input_taper"], fit.source, y, alpha)
    initial = score_reference(a, spec["input_taper"], np.zeros_like(fit.source), y, alpha)
    rho = optimality(fit.source, expected["gradient"], nonnegative)
    rho0 = optimality(np.zeros_like(fit.source), initial["gradient"], nonnegative)
    threshold = atol + rtol * rho0
    gradient_error = gradient_roundoff_budget(a, spec, fit.source, y, alpha)
    initial_gradient_error = gradient_roundoff_budget(a, spec, np.zeros_like(fit.source), y, alpha)
    threshold_error = threshold_roundoff_budget(atol, rtol, rho0, initial_gradient_error)
    for key, value in expected.items():
        if key == "gradient":
            np.testing.assert_allclose(fit.gradient, value, atol=gradient_error, rtol=0)
        else:
            close(getattr(fit, key), value)
    for field in (
        "data_objective",
        "penalty_objective",
        "total_objective",
        "optimality_residual",
        "stopping_threshold",
    ):
        assert type(getattr(fit, field)) is float
        assert np.isfinite(getattr(fit, field))
    assert type(fit.iterations) is int and 0 <= fit.iterations <= budget
    assert type(fit.converged) is bool and type(fit.nonnegative) is bool
    assert fit.nonnegative is nonnegative
    assert fit.regularization == alpha
    assert fit.status in {"converged", "iteration_limit", "stagnation"}
    assert fit.converged is (fit.status == "converged")
    # Infinity norm and fixed-source KKT projection do not amplify gradient
    # error. Threshold arithmetic has its own much smaller units/scale budget.
    assert fit.converged is (fit.optimality_residual <= fit.stopping_threshold)
    np.testing.assert_allclose(fit.optimality_residual, rho, atol=gradient_error, rtol=0)
    np.testing.assert_allclose(fit.stopping_threshold, threshold, atol=threshold_error, rtol=0)
    if fit.converged:
        assert rho <= threshold + gradient_error + threshold_error
    if nonnegative:
        assert np.all(fit.source >= 0)
    arrays = []
    for field, shape in (
        ("source", spec["illumination"].shape[2:]),
        ("predicted_images", y.shape),
        ("residual_images", y.shape),
        ("gradient", spec["illumination"].shape[2:]),
        ("output", fit.output.shape),
        ("objective_history", (fit.iterations + 1,)),
        ("optimality_history", (fit.iterations + 1,)),
    ):
        value = getattr(fit, field)
        array_contract(value, shape)
        arrays.append(value)
    no_alias(arrays + [y, spec["kernel"], spec["illumination"], spec["input_taper"]])
    close(fit.objective_history[0], initial["total_objective"])
    close(fit.objective_history[-1], expected["total_objective"])
    np.testing.assert_allclose(fit.optimality_history[0], rho0, atol=initial_gradient_error, rtol=0)
    np.testing.assert_allclose(fit.optimality_history[-1], rho, atol=gradient_error, rtol=0)
    assert np.all(fit.optimality_history >= 0)


def test_finite_sum_real_adjoint_crop_origin_and_padding(api: Any) -> None:
    spec = geometry()
    a = matrix_for(spec)
    x = np.linspace(-1.1, 1.7, 12).reshape(2, 2, 3)
    detector = np.linspace(0.9, -0.7, 16).reshape(spec["input_taper"].shape)
    op = api.build_finite_field_operator(**spec)
    prediction = api.finite_field_forward(op, x)
    adjoint = api.finite_field_adjoint(op, detector)
    close(prediction, (a @ x.ravel()).reshape(detector.shape))
    close(adjoint, (a.T @ detector.ravel()).reshape(x.shape))
    close(np.vdot(prediction, detector), np.vdot(x, adjoint))
    array_contract(prediction, detector.shape)
    array_contract(adjoint, x.shape)
    padded = dict(spec, padding_shape_zyx=(7, 6, 11))
    op2 = api.build_finite_field_operator(**padded)
    close(api.finite_field_forward(op2, x), prediction)
    close(api.finite_field_adjoint(op2, detector), adjoint)
    different_spacing = api.build_finite_field_operator(
        **dict(spec, source_spacing_um_zyx=(2, 3, 4))
    )
    close(api.finite_field_forward(different_spacing, x), prediction)
    # W is absent from both operators: changing it cannot change A or A.T.
    unweighted = api.build_finite_field_operator(**dict(spec, input_taper=np.ones_like(detector)))
    close(api.finite_field_forward(unweighted, x), prediction)
    close(api.finite_field_adjoint(unweighted, detector), adjoint)
    # Crop selects detector rows, preserving emitters outside that crop.
    outside = np.zeros_like(x)
    outside[0, 1, 2] = 1
    close(api.finite_field_forward(op, outside), a[:, 5].reshape(detector.shape))
    assert np.max(np.abs(a[:, 5])) > 0.1


@pytest.mark.parametrize("emitter", [(0, 0, 0), (1, 1, 2), (2, 2, 4)])
def test_corner_interior_fixed_source_periodic_control(
    api: Any, emitter: tuple[int, int, int]
) -> None:
    spec: dict[str, Any] = dict(
        kernel=np.array([[[0.2, 1.0, 0.5]]]),
        kernel_origin_zyx=(0, 0, 1),
        illumination=np.ones((1, 1, 3, 3, 5)),
        detector_crop_zyx=((0, 3), (0, 3), (0, 5)),
        input_taper=np.ones((1, 1, 3, 3, 5)),
        padding_shape_zyx=(3, 3, 7),
        source_spacing_um_zyx=(1, 1, 1),
    )
    x = np.zeros((3, 3, 5))
    x[emitter] = 1.3
    a = matrix_for(spec)
    periodic = periodic_matrix(spec["kernel"], spec["kernel_origin_zyx"], spec["illumination"])
    predicted = api.finite_field_forward(api.build_finite_field_operator(**spec), x)
    close(predicted, (a @ x.ravel()).reshape(spec["input_taper"].shape))
    difference = np.max(np.abs((a - periodic) @ x.ravel()))
    assert (difference > 0.1) if emitter[2] in (0, 4) else (difference == 0)


def test_score_residual_weights_normalization_scaling_and_gradient(api: Any) -> None:
    spec = geometry()
    a = matrix_for(spec)
    x = np.linspace(-0.91, 1.13, 12).reshape(2, 2, 3)
    y = np.linspace(1.3, -0.8, 16).reshape(spec["input_taper"].shape)
    op = api.build_finite_field_operator(**spec)
    score = api.finite_field_score(op, x, images=y, regularization=0.37)
    expected = score_reference(a, spec["input_taper"], x, y, 0.37)
    for name, value in expected.items():
        close(getattr(score, name), value)
    for name in ("data_objective", "penalty_objective", "total_objective"):
        assert type(getattr(score, name)) is float
    for name, shape in (
        ("predicted_images", y.shape),
        ("residual_images", y.shape),
        ("gradient", x.shape),
    ):
        array_contract(getattr(score, name), shape)
    no_alias([score.predicted_images, score.residual_images, score.gradient, x, y])
    # Gradient by an independent centered directional derivative of the quadratic.
    direction = np.linspace(0.4, -0.3, 12).reshape(x.shape)
    step = EPS ** (1 / 3)
    plus = api.finite_field_score(op, x + step * direction, images=y, regularization=0.37)
    minus = api.finite_field_score(op, x - step * direction, images=y, regularization=0.37)
    derivative = (plus.total_objective - minus.total_objective) / (2 * step)
    bound = 64 * EPS / step * max(1, abs(expected["total_objective"]))
    assert abs(derivative - np.sum(expected["gradient"] * direction)) <= bound
    # A zero-weight datum is still reported; M still includes that datum.
    changed_y = y.copy()
    changed_y.ravel()[0] += 11
    changed = api.finite_field_score(op, x, images=changed_y, regularization=0.37)
    close(changed.total_objective, score.total_objective)
    close(changed.gradient, score.gradient)
    close(changed.residual_images.ravel()[0], score.residual_images.ravel()[0] - 11)
    for kernel_scale, illumination_scale in ((2.0, 1.0), (1.0, -1.5)):
        scaled = api.build_finite_field_operator(
            **dict(
                spec,
                kernel=spec["kernel"] * kernel_scale,
                illumination=spec["illumination"] * illumination_scale,
            )
        )
        close(
            api.finite_field_forward(scaled, x),
            score.predicted_images * kernel_scale * illumination_scale,
        )
    close(api.finite_field_forward(op, x * 2), score.predicted_images * 2)


@pytest.mark.parametrize("alpha", [0.0, 0.2])
@pytest.mark.parametrize("nonnegative", [False, True])
@pytest.mark.parametrize("source_values", [(1.0, -2.0, 1.0), (1.0, 0.7, 1.3)])
def test_tiny_exact_estimators_and_stationarity(
    api: Any, alpha: float, nonnegative: bool, source_values: tuple[float, ...]
) -> None:
    spec = tiny()
    a = matrix_for(spec)
    y = (a @ np.asarray(source_values)).reshape(spec["input_taper"].shape)
    h, b = normal_system(a, spec["input_taper"], y, alpha)
    expected = exact_minimizer(h, b, nonnegative)
    op = api.build_finite_field_operator(**spec)
    fit = solve(api, op, y, regularization=alpha, nonnegative=nonnegative)
    check_fit(fit, spec, y, alpha, nonnegative)
    assert fit.converged, (
        "Tiny well-conditioned control must meet the criterion within the chosen budget"
    )
    # SPD strong convexity gives ||x-x*||inf <= ||H^-1||inf*rho,
    # also for the constrained variational inequality, via lambda_min in 2-norm.
    threshold = ATOL + RTOL * float(np.max(np.abs(b)))
    error_bound = np.sqrt(b.size) * threshold / float(np.linalg.eigvalsh(h)[0])
    np.testing.assert_allclose(
        fit.source.ravel(), expected, rtol=0, atol=2 * error_bound + arithmetic_tolerance(expected)
    )
    if source_values[1] < 0 and nonnegative:
        assert expected[1] == 0 and np.all(fit.source >= 0)
        assert not np.allclose(expected, np.linalg.solve(h, b), rtol=0, atol=0.01)
    close(fit.output, fit.source)
    close(fit.output_spacing_um_zyx, spec["source_spacing_um_zyx"])


@pytest.mark.parametrize("nonnegative", [False, True])
@pytest.mark.parametrize("budget", [0, 1])
def test_resource_stop_and_initial_criterion_have_distinct_meaning(
    api: Any, nonnegative: bool, budget: int
) -> None:
    spec = tiny()
    a = matrix_for(spec)
    y = (a @ np.array([1.0, -2.0, 1.0])).reshape(spec["input_taper"].shape)
    op = api.build_finite_field_operator(**spec)
    fit = solve(api, op, y, nonnegative=nonnegative, max_iterations=budget)
    check_fit(fit, spec, y, 0.2, nonnegative, budget=budget)
    if budget == 0:
        np.testing.assert_array_equal(fit.source, 0)
        assert fit.status == "iteration_limit" and not fit.converged
    # With a loose declared threshold, x=0 must converge before the budget stop.
    initial = solve(
        api,
        op,
        y,
        nonnegative=nonnegative,
        max_iterations=0,
        absolute_tolerance=10.0,
        relative_tolerance=0.0,
    )
    check_fit(initial, spec, y, 0.2, nonnegative, budget=0, atol=10.0, rtol=0.0)
    assert initial.status == "converged" and initial.iterations == 0
    np.testing.assert_array_equal(initial.source, 0)


@pytest.mark.parametrize("nonnegative", [False, True])
@pytest.mark.parametrize("relative_tolerance", [0.5, 1.0])
def test_relative_only_initial_stopping_uses_projected_residual(
    api: Any, nonnegative: bool, relative_tolerance: float
) -> None:
    spec: dict[str, Any] = dict(
        kernel=np.ones((1, 1, 1)),
        kernel_origin_zyx=(0, 0, 0),
        illumination=np.ones((1, 1, 1, 1, 3)),
        detector_crop_zyx=((0, 1), (0, 1), (0, 3)),
        input_taper=np.ones((1, 1, 1, 1, 3)),
        padding_shape_zyx=(1, 1, 3),
        source_spacing_um_zyx=(1.0, 1.0, 1.0),
    )
    # A=I, M=3: g(0)=[2,-0.5,0]. Thus rho0 is 2 unconstrained
    # and 0.5 constrained. Using the unprojected norm would falsely converge
    # the constrained rtol=0.5 case even with zero accepted updates.
    y = np.array([-6.0, 1.5, 0.0]).reshape(1, 1, 1, 1, 3)
    op = api.build_finite_field_operator(**spec)
    fit = solve(
        api,
        op,
        y,
        regularization=0.0,
        nonnegative=nonnegative,
        max_iterations=0,
        absolute_tolerance=0.0,
        relative_tolerance=relative_tolerance,
    )
    check_fit(fit, spec, y, 0.0, nonnegative, budget=0, atol=0.0, rtol=relative_tolerance)
    assert fit.iterations == 0
    np.testing.assert_array_equal(fit.source, 0)
    assert fit.converged is (relative_tolerance == 1.0)
    assert fit.status == ("converged" if relative_tolerance == 1.0 else "iteration_limit")


@pytest.mark.parametrize("zero_kind", ["kernel", "illumination", "input_taper", "images"])
@pytest.mark.parametrize("nonnegative", [False, True])
def test_valid_zero_maps_and_zero_data(api: Any, zero_kind: str, nonnegative: bool) -> None:
    spec = tiny()
    y = np.ones(spec["input_taper"].shape)
    if zero_kind == "images":
        y[:] = 0
    else:
        spec[zero_kind] = np.zeros_like(spec[zero_kind])
    op = api.build_finite_field_operator(**spec)
    fit = solve(api, op, y, regularization=0.0, nonnegative=nonnegative, max_iterations=0)
    check_fit(fit, spec, y, 0.0, nonnegative, budget=0)
    assert fit.converged and fit.iterations == 0
    np.testing.assert_array_equal(fit.source, 0)
    close(fit.total_objective, float(np.sum((spec["input_taper"] * y) ** 2) / (2 * y.size)))


def test_rank_deficiency_accepts_stationarity_without_minimum_norm_or_source_certificate(
    api: Any,
) -> None:
    spec: dict[str, Any] = dict(
        kernel=np.ones((1, 1, 2)),
        kernel_origin_zyx=(0, 0, 0),
        illumination=np.ones((1, 1, 1, 1, 2)),
        detector_crop_zyx=((0, 1), (0, 1), (1, 2)),
        input_taper=np.ones((1, 1, 1, 1, 1)),
        padding_shape_zyx=(1, 1, 3),
        source_spacing_um_zyx=(1, 1, 1),
    )
    op = api.build_finite_field_operator(**spec)
    y = np.ones((1, 1, 1, 1, 1))
    for nonnegative in (False, True):
        fit = solve(api, op, y, regularization=0.0, nonnegative=nonnegative)
        check_fit(fit, spec, y, 0.0, nonnegative)
        assert fit.converged
        close(np.sum(fit.source), 1.0, terms=4096)
        # No assertion on a particular source split or minimum norm.


def test_display_taper_zoom_spacing_and_fixed_origin_are_output_only(api: Any) -> None:
    shape = (2, 2, 3)
    spec: dict[str, Any] = dict(
        kernel=np.ones((1, 1, 1)),
        kernel_origin_zyx=(0, 0, 0),
        illumination=np.ones((1, 1, *shape)),
        detector_crop_zyx=((0, 2), (0, 2), (0, 3)),
        input_taper=np.ones((1, 1, *shape)),
        padding_shape_zyx=shape,
        source_spacing_um_zyx=(0.4, 0.3, 0.2),
    )
    op = api.build_finite_field_operator(**spec)
    y = 0.2 + np.arange(12).reshape(1, 1, *shape) / 10
    taper = np.linspace(0, 1, 12).reshape(shape)
    base = solve(api, op, y, regularization=0.0)
    tapered = solve(api, op, y, regularization=0.0, output_taper=taper)
    close(tapered.output, tapered.source * taper)
    shown = solve(api, op, y, regularization=0.0, output_taper=taper, output_zoom=3)
    check_fit(shown, spec, y, 0.0, False)
    assert shown.converged
    close(shown.source, base.source)
    close(shown.output, display_reference(shown.source, taper, 3))
    close(shown.output[::3, ::3, ::3], shown.source * taper)
    close(shown.output_spacing_um_zyx, np.asarray(spec["source_spacing_um_zyx"]) / 3)
    for field in (
        "predicted_images",
        "residual_images",
        "gradient",
        "objective_history",
        "optimality_history",
    ):
        close(getattr(shown, field), getattr(base, field))
    close(shown.total_objective, base.total_objective)
    no_alias([shown.source, shown.output, taper, y, base.source, base.output])
    # Singleton axes stay singleton; zoom does not duplicate endpoints.
    small = api.build_finite_field_operator(**tiny())
    one = solve(api, small, np.ones(small.input_taper.shape), output_zoom=2)
    assert one.output.shape == (1, 1, 5)
    close(one.output, display_reference(one.source, np.ones_like(one.source), 2))


def test_records_own_arrays_and_preserve_callers_and_ambient_state(api: Any) -> None:
    spec = geometry()
    snapshots = {key: value.copy() for key, value in spec.items() if type(value) is np.ndarray}
    flags = {key: value.flags.writeable for key, value in spec.items() if type(value) is np.ndarray}
    errors = np.geterr().copy()
    filters = list(warnings.filters)
    op = api.build_finite_field_operator(**spec)
    assert isinstance(op, api.FiniteFieldOperator)
    for name in ("kernel", "illumination", "input_taper"):
        array_contract(getattr(op, name), spec[name].shape, writable=False)
        assert not np.shares_memory(getattr(op, name), spec[name])
    for name in (
        "kernel_origin_zyx",
        "detector_crop_zyx",
        "padding_shape_zyx",
        "source_spacing_um_zyx",
    ):
        assert type(getattr(op, name)) is tuple
        assert getattr(op, name) == spec[name]
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        op.kernel = np.zeros_like(op.kernel)
    x = np.linspace(-1, 1, 12).reshape(2, 2, 3)
    y = np.ones(op.input_taper.shape)
    x.setflags(write=False)
    y.setflags(write=False)
    s1 = api.finite_field_score(op, x, images=y, regularization=0.1)
    s2 = api.finite_field_score(op, x, images=y, regularization=0.1)
    assert isinstance(s1, api.FiniteFieldScore)
    f1 = solve(api, op, y, max_iterations=0)
    f2 = solve(api, op, y, max_iterations=0)
    assert isinstance(f1, api.FiniteFieldFit)
    for record, field in ((s1, "total_objective"), (f1, "source")):
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            setattr(record, field, None)
    returned = [
        s1.predicted_images,
        s1.residual_images,
        s1.gradient,
        s2.predicted_images,
        s2.residual_images,
        s2.gradient,
    ]
    returned += [
        getattr(f, n)
        for f in (f1, f2)
        for n in (
            "source",
            "output",
            "predicted_images",
            "residual_images",
            "gradient",
            "objective_history",
            "optimality_history",
        )
    ]
    no_alias(returned + [x, y, op.kernel, op.illumination, op.input_taper])
    before = api.finite_field_forward(op, x)
    spec["kernel"][:] = 0
    close(api.finite_field_forward(op, x), before)
    spec["kernel"][:] = snapshots["kernel"]
    for key, value in snapshots.items():
        np.testing.assert_array_equal(spec[key], value)
        assert spec[key].flags.writeable == flags[key]
    assert not x.flags.writeable and not y.flags.writeable
    assert np.geterr() == errors and warnings.filters == filters


@pytest.mark.parametrize(
    "dtype",
    ["i1", "u1", "i2", "u2", "i4", "u4", "i8", "u8", "f2", "f4", "f8", ">f8", ">i4", np.longdouble],
)
@pytest.mark.parametrize("layout", ["C", "F", "negative", "readonly"])
def test_permitted_array_widths_endians_layouts(api: Any, dtype: Any, layout: str) -> None:
    def convert(value: Any) -> NDArray[Any]:
        arr = np.array(value, dtype=dtype, order="F" if layout == "F" else "C")
        if layout == "negative":
            arr = arr[..., ::-1]
        if layout == "readonly":
            arr.setflags(write=False)
        return arr

    spec = tiny()
    # Integral controls keep all unsigned/half-width inputs legitimate.
    spec["kernel"] = convert([[[1, 1, 0]]])
    spec["illumination"] = convert(np.ones((2, 1, 1, 1, 3)))
    spec["input_taper"] = convert(np.ones((2, 1, 1, 1, 3)))
    x = convert([[[1, 2, 3]]])
    y = convert(np.arange(6).reshape(2, 1, 1, 1, 3))
    a = matrix_for(spec)
    op = api.build_finite_field_operator(**spec)
    close(api.finite_field_forward(op, x), (a @ x.ravel()).reshape(y.shape))
    close(api.finite_field_adjoint(op, y), (a.T @ y.ravel()).reshape(x.shape))
    score = api.finite_field_score(op, x, images=y, regularization=0)
    for key, value in score_reference(
        a, spec["input_taper"], x.astype(float), y.astype(float), 0
    ).items():
        close(getattr(score, key), value)
    fit = solve(api, op, y, max_iterations=0, output_taper=convert(np.ones((1, 1, 3))))
    check_fit(fit, spec, y, 0.2, False, budget=0)


def test_binary64_source_and_gradient_are_not_rounded_to_float32(api: Any) -> None:
    spec = tiny()
    spec["kernel"] = np.ones((1, 1, 1))
    spec["kernel_origin_zyx"] = (0, 0, 0)
    spec["illumination"] = np.ones((1, 1, 1, 1, 3))
    spec["input_taper"] = np.ones((1, 1, 1, 1, 3))
    y = np.array([1 + 2**-29, 1 - 2**-30, 1 + 2**-31]).reshape(1, 1, 1, 1, 3)
    op = api.build_finite_field_operator(**spec)
    x = y.reshape(1, 1, 3).copy()
    score = api.finite_field_score(op, x, images=y * 0.3, regularization=0.1)
    expected = score_reference(matrix_for(spec), spec["input_taper"], x, y * 0.3, 0.1)
    close(score.gradient, expected["gradient"], terms=3)
    fit = solve(api, op, y, regularization=0.0, absolute_tolerance=1e-14, relative_tolerance=0.0)
    assert fit.converged
    np.testing.assert_allclose(fit.source, x, atol=2e-13, rtol=0)


class ArraySubclass(np.ndarray[Any, Any]):
    """A non-plain array explicitly excluded by the input contract."""


def invalid_array(kind: str, shape: tuple[int, ...]) -> Any:
    values = np.ones(shape)
    if kind == "list":
        return values.tolist()
    if kind == "subclass":
        return values.view(ArraySubclass)
    if kind == "masked":
        return np.ma.array(values, mask=False)
    if kind == "shape":
        return values.reshape(-1)
    if kind == "empty":
        return np.empty((*shape[:-1], 0))
    if kind in {"nan", "inf"}:
        values.flat[0] = float(kind)
        return values
    return values.astype({"bool": bool, "complex": complex, "object": object, "string": "U1"}[kind])


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "shape",
        "empty",
        "nan",
        "inf",
        "bool",
        "complex",
        "object",
        "string",
    ],
)
@pytest.mark.parametrize(
    "boundary",
    [
        "kernel",
        "illumination",
        "input_taper",
        "source",
        "detector",
        "images_score",
        "images_fit",
        "output_taper",
    ],
)
def test_array_grammar_at_real_boundaries(api: Any, kind: str, boundary: str) -> None:
    spec = tiny()
    op = api.build_finite_field_operator(**spec)
    x = np.ones((1, 1, 3))
    y = np.ones(spec["input_taper"].shape)
    if boundary in {"kernel", "illumination", "input_taper"}:
        spec[boundary] = invalid_array(kind, spec[boundary].shape)

        def call():
            return api.build_finite_field_operator(**spec)
    elif boundary == "source":
        bad = invalid_array(kind, x.shape)

        def call():
            return api.finite_field_forward(op, bad)
    elif boundary == "detector":
        bad = invalid_array(kind, y.shape)

        def call():
            return api.finite_field_adjoint(op, bad)
    elif boundary == "images_score":
        bad = invalid_array(kind, y.shape)

        def call():
            return api.finite_field_score(op, x, images=bad, regularization=0)
    elif boundary == "images_fit":
        bad = invalid_array(kind, y.shape)

        def call():
            return solve(api, op, bad, max_iterations=0)
    else:
        bad = invalid_array(kind, x.shape)

        def call():
            return solve(api, op, y, output_taper=bad, max_iterations=0)

    expect_error("invalid_finite_field_input", call)


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "shape",
        "empty",
        "nan",
        "inf",
        "bool",
        "complex",
        "object",
        "string",
    ],
)
def test_score_source_has_its_own_array_boundary(api: Any, kind: str) -> None:
    spec = tiny()
    op = api.build_finite_field_operator(**spec)
    expect_error(
        "invalid_finite_field_input",
        lambda: api.finite_field_score(
            op,
            invalid_array(kind, (1, 1, 3)),
            images=np.ones(spec["input_taper"].shape),
            regularization=0,
        ),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("kernel_origin_zyx", [0, 0, 1]),
        ("kernel_origin_zyx", (0, 1)),
        ("kernel_origin_zyx", (0, False, 1)),
        ("kernel_origin_zyx", (0, 0, np.int64(1))),
        ("kernel_origin_zyx", (0, 0, -1)),
        ("kernel_origin_zyx", (0, 0, 3)),
        ("kernel_origin_zyx", (0, 0, 1.0)),
        ("detector_crop_zyx", [(0, 1), (0, 1), (0, 3)]),
        ("detector_crop_zyx", ((0, 1), (0, 1), [0, 3])),
        ("detector_crop_zyx", ((0, 1), (0, 1), (0, 0))),
        ("detector_crop_zyx", ((0, 1), (0, 1), (2, 1))),
        ("detector_crop_zyx", ((0, 1), (0, 1), (-1, 2))),
        ("detector_crop_zyx", ((0, 1), (0, 1), (0, 4))),
        ("detector_crop_zyx", ((0, 1), (0, 1), (False, 3))),
        ("detector_crop_zyx", ((0, 1), (0, 1), (0, np.int64(3)))),
        ("detector_crop_zyx", ((0, 1), (0, 1))),
        ("padding_shape_zyx", [1, 1, 5]),
        ("padding_shape_zyx", (1, 1)),
        ("padding_shape_zyx", (1, 1, 4)),
        ("padding_shape_zyx", (1, 0, 5)),
        ("padding_shape_zyx", (1, 1, False)),
        ("padding_shape_zyx", (1, 1, 5.0)),
        ("padding_shape_zyx", (1, 1, np.int64(5))),
        ("source_spacing_um_zyx", [0.5, 0.3, 0.2]),
        ("source_spacing_um_zyx", (0.5, 0.3)),
        ("source_spacing_um_zyx", (0.5, 0.3, 0)),
        ("source_spacing_um_zyx", (0.5, 0.3, -1)),
        ("source_spacing_um_zyx", (0.5, 0.3, float("inf"))),
        ("source_spacing_um_zyx", (0.5, 0.3, float("nan"))),
        ("source_spacing_um_zyx", (0.5, 0.3, True)),
        ("source_spacing_um_zyx", (0.5, 0.3, "0.2")),
        ("source_spacing_um_zyx", (0.5, 0.3, np.int64(1))),
    ],
)
def test_geometry_rejection_boundaries(api: Any, field: str, value: Any) -> None:
    expect_error(
        "invalid_finite_field_input",
        lambda: api.build_finite_field_operator(**dict(tiny(), **{field: value})),
    )


@pytest.mark.parametrize("boundary", ["input_taper", "output_taper"])
@pytest.mark.parametrize("value", [-EPS, 1 + EPS])
def test_taper_closed_interval(api: Any, boundary: str, value: float) -> None:
    spec = tiny()
    if boundary == "input_taper":
        spec[boundary].flat[0] = value

        def call():
            return api.build_finite_field_operator(**spec)
    else:
        op = api.build_finite_field_operator(**spec)
        taper = np.ones((1, 1, 3))
        taper.flat[0] = value

        def call():
            return solve(
                api, op, np.ones(spec["input_taper"].shape), output_taper=taper, max_iterations=0
            )

    expect_error("invalid_finite_field_input", call)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("regularization", -EPS),
        ("regularization", True),
        ("regularization", float("nan")),
        ("regularization", float("inf")),
        ("regularization", "0"),
        ("regularization", np.int64(1)),
        ("absolute_tolerance", -EPS),
        ("absolute_tolerance", True),
        ("absolute_tolerance", float("inf")),
        ("absolute_tolerance", float("nan")),
        ("absolute_tolerance", "0"),
        ("absolute_tolerance", np.int64(1)),
        ("relative_tolerance", -EPS),
        ("relative_tolerance", True),
        ("relative_tolerance", float("inf")),
        ("relative_tolerance", float("nan")),
        ("relative_tolerance", "0"),
        ("relative_tolerance", np.int64(1)),
        ("nonnegative", 0),
        ("nonnegative", np.bool_(True)),
        ("nonnegative", "false"),
        ("max_iterations", -1),
        ("max_iterations", True),
        ("max_iterations", 1.0),
        ("max_iterations", np.int64(1)),
        ("output_zoom", 0),
        ("output_zoom", -1),
        ("output_zoom", True),
        ("output_zoom", 2.0),
        ("output_zoom", np.int64(2)),
    ],
)
def test_solver_scalar_grammar(api: Any, field: str, value: Any) -> None:
    spec = tiny()
    op = api.build_finite_field_operator(**spec)
    expect_error(
        "invalid_finite_field_input",
        lambda: solve(api, op, np.ones(spec["input_taper"].shape), **{field: value}),
    )


@pytest.mark.parametrize("alpha", [-EPS, True, float("nan"), float("inf"), "0", np.int64(1)])
def test_score_regularization_grammar(api: Any, alpha: Any) -> None:
    spec = tiny()
    op = api.build_finite_field_operator(**spec)
    expect_error(
        "invalid_finite_field_input",
        lambda: api.finite_field_score(
            op, np.ones((1, 1, 3)), images=np.ones(spec["input_taper"].shape), regularization=alpha
        ),
    )


def test_positive_scalar_and_geometry_endpoints(api: Any) -> None:
    spec = tiny()
    spec["kernel"] = np.zeros((1, 1, 3))
    spec["kernel_origin_zyx"] = (0, 0, 2)
    spec["source_spacing_um_zyx"] = (1, 2, 3)
    spec["input_taper"].ravel()[::2] = 0
    op = api.build_finite_field_operator(**spec)
    y = -np.ones(spec["input_taper"].shape)
    # Huge finite iteration budget is not an arbitrary practical-size rejection.
    for atol, rtol in ((1, 0), (0, 1)):
        fit = solve(
            api,
            op,
            y,
            regularization=0,
            absolute_tolerance=atol,
            relative_tolerance=rtol,
            max_iterations=sys.maxsize + 1,
            output_taper=np.zeros((1, 1, 3)),
        )
        assert fit.converged and fit.iterations == 0
        close(fit.output, np.zeros((1, 1, 3)))
    expect_error(
        "invalid_finite_field_input",
        lambda: solve(api, op, y, absolute_tolerance=0, relative_tolerance=0),
    )
    # Insufficient padding remains invalid for an exact-zero kernel.
    expect_error(
        "invalid_finite_field_input",
        lambda: api.build_finite_field_operator(**dict(spec, padding_shape_zyx=(1, 1, 4))),
    )


def test_moderate_regime_is_not_an_input_cap(api: Any) -> None:
    spec = tiny()
    spec["source_spacing_um_zyx"] = (0.005, 12.0, 1.0)
    spec["kernel"] *= 3
    spec["illumination"] *= 2
    x = np.array([[[-1.1, 0.4, 2.3]]])
    y = np.linspace(-21, 25, 6).reshape(spec["input_taper"].shape)
    op = api.build_finite_field_operator(**spec)
    score = api.finite_field_score(op, x, images=y, regularization=3.5)
    expected = score_reference(matrix_for(spec), spec["input_taper"], x, y, 3.5)
    for name, value in expected.items():
        close(getattr(score, name), value)


@pytest.mark.parametrize(
    "operation",
    ["forward", "adjoint", "score_data", "score_gradient", "solve", "padding", "zoom", "spacing"],
)
def test_arithmetic_range_is_source_free_and_preserves_state(api: Any, operation: str) -> None:
    spec = tiny()
    spec["kernel"] = np.ones((1, 1, 1))
    spec["kernel_origin_zyx"] = (0, 0, 0)
    spec["illumination"] = np.ones((1, 1, 1, 1, 3))
    spec["input_taper"] = np.ones((1, 1, 1, 1, 3))
    x = np.ones((1, 1, 3))
    y = np.ones((1, 1, 1, 1, 3))
    huge = np.finfo(float).max
    if operation in {"forward", "adjoint", "score_gradient"}:
        spec["kernel"] *= huge
    if operation == "forward":
        x *= 2
    if operation == "adjoint":
        y *= 2
    if operation == "score_gradient":
        x *= 0
        # J=8, while each required gradient is -4*max_float/3: genuinely
        # unrepresentable regardless of normalization/evaluation order.
        y *= 4
    if operation in {"score_data", "solve"}:
        y *= huge
    op = api.build_finite_field_operator(**spec)
    if operation == "forward":

        def call():
            return api.finite_field_forward(op, x)
    elif operation == "adjoint":

        def call():
            return api.finite_field_adjoint(op, y)
    elif operation.startswith("score"):

        def call():
            return api.finite_field_score(op, x, images=y, regularization=0)
    elif operation == "solve":

        def call():
            return solve(api, op, y, max_iterations=0)
    elif operation == "padding":

        def call():
            return api.build_finite_field_operator(
                **dict(spec, padding_shape_zyx=(1, 1, sys.maxsize + 1))
            )
    elif operation == "zoom":

        def call():
            return solve(api, op, y, max_iterations=0, output_zoom=sys.maxsize)
    else:
        spec["source_spacing_um_zyx"] = (1.0, 1.0, float(np.nextafter(0.0, 1.0)))
        op = api.build_finite_field_operator(**spec)

        def call():
            return solve(api, op, y, max_iterations=0, output_zoom=2)

    before_x, before_y = x.copy(), y.copy()
    x.setflags(write=False)
    y.setflags(write=False)
    prior_mode = np.geterr().copy()
    prior_filters = list(warnings.filters)
    try:
        # Errors must still be translated at the responsible arithmetic stage
        # under a caller's stricter mode, with no emitted RuntimeWarning.
        np.seterr(all="raise")
        strict_mode = np.geterr().copy()
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            inside_filters = list(warnings.filters)
            expect_error("finite_field_range", call)
            assert np.geterr() == strict_mode
            assert warnings.filters == inside_filters
            assert not any(issubclass(item.category, RuntimeWarning) for item in recorded)
        assert warnings.filters == prior_filters
    finally:
        np.seterr(**prior_mode)
    np.testing.assert_array_equal(x, before_x)
    np.testing.assert_array_equal(y, before_y)
    assert not x.flags.writeable and not y.flags.writeable
