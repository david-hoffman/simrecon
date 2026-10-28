"""Blind public-contract tests for the finite inverse operator.

The fixture's direct cosine DFT, finite pupil, squared-field illumination and
explicit real transpose supply independent truth. No product call supplies an
expected result. Each test group names a distinct observable risk in its name.
"""

from __future__ import annotations

import importlib
import inspect
import math
import sys
import traceback
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import numpy as np
import pytest

from simrecon import SimreconError
from simulation_inverse_operator_fixture import (
    apply_reference,
    kernel_from_spectra,
    light_bound,
    null_support_spectra,
    operator_matrix,
    padding_only_spectra,
    physical_kernel,
    pixel_matrix,
    row_column_norms,
    signed_spectra,
    spectra_from_plane,
)

operator = importlib.import_module("scripts.simulation_inverse_operator")

FIELDS = (
    "lateral_spectra",
    "source_shape_zyx",
    "source_spacing_um_zyx",
    "emission_um",
    "refractive_index",
    "detection_na",
    "pupil_order",
)
SHAPE = (3, 2, 4)
SPACING = (0.23, 0.17, 0.11)
INVALID = "invalid_simulation_inverse_operator"
RANGE = "simulation_inverse_operator_range"


@contextmanager
def observe_arithmetic_ownership(
    unrelated_errors: tuple[Exception, ...] = (),
) -> Iterator[list[warnings.WarningMessage]]:
    """Collect evidence; neither wording nor attribution proves causality.

    Only qualification controls may supply an exact exception instance issued
    at an entered public dependency boundary. Unknown exceptions block scientific
    classification. Assertions about values/state keep their original meaning.
    """
    with warnings.catch_warnings(record=True) as caught:
        try:
            yield caught
        except Exception as error:
            if any(error is sentinel for sentinel in unrelated_errors):
                traceback.print_exception(error)
                print("QUALIFIED_UNRELATED_EXCEPTION", type(error).__name__, str(error))
                raise
            if isinstance(error, AssertionError):
                raise
            traceback.print_exception(error)
            pytest.fail(
                "OBSERVER_INCONCLUSIVE: public exception ownership is unqualified; "
                f"{type(error).__name__}: {error}",
                pytrace=False,
            )
        finally:
            for warning in caught:
                print(
                    warnings.formatwarning(
                        warning.message, warning.category, warning.filename, warning.lineno
                    ),
                    end="",
                )


def assert_arithmetic_ownership_resolved(
    caught: list[warnings.WarningMessage], unrelated_warnings: tuple[Warning, ...] = ()
) -> None:
    """Block unknown RuntimeWarnings without claiming success or product-red.

    Exact identity qualifies only test-issued dependency sentinels. No phrase,
    filename, stacklevel or warning count constitutes an ownership certificate.
    """
    unresolved = []
    for warning in caught:
        if any(warning.message is sentinel for sentinel in unrelated_warnings):
            print("QUALIFIED_UNRELATED_WARNING", warning.category.__name__, str(warning.message))
        elif issubclass(warning.category, RuntimeWarning):
            unresolved.append(warning)
    if unresolved:
        pytest.fail(
            "OBSERVER_INCONCLUSIVE: RuntimeWarning ownership is unqualified; "
            "retain category/message/location and route causal diagnosis",
            pytrace=False,
        )


def cache_fields(shape: tuple[int, int, int] = SHAPE) -> dict[str, Any]:
    """Construct public record arguments without relying on builder fidelity."""
    return dict(
        lateral_spectra=signed_spectra(shape),
        source_shape_zyx=shape,
        source_spacing_um_zyx=SPACING,
        emission_um=0.61,
        refractive_index=1.33,
        detection_na=0.9,
        pupil_order=3,
    )


def make_cache(**changes: Any) -> Any:
    fields = cache_fields()
    fields.update(changes)
    return operator.InverseKernelCache(**fields)


def builder_fields(**changes: Any) -> dict[str, Any]:
    fields = cache_fields()
    del fields["lateral_spectra"]
    fields.update(changes)
    return fields


def settings(**changes: Any) -> dict[str, Any]:
    result = dict(
        carrier_yx_per_um=np.array([-0.73, 0.41]),
        phases_rad=np.array([0.21, 1.37, -0.82]),
        beam_amplitudes=(0.7, 1.2, 0.25),
        excitation_um=0.48,
    )
    result.update(changes)
    return result


def operand(operation: str, shape: tuple[int, int, int] = SHAPE, phases: int = 3) -> Any:
    target = shape if operation == "forward" else (phases, shape[0], shape[1] // 2, shape[2] // 2)
    return ((np.arange(math.prod(target)) % 11 - 5) / 3).astype(np.float32).reshape(target)


def run(operation: str, data: Any, cache: Any = None, **changes: Any) -> Any:
    return getattr(operator, operation)(
        data, kernel_cache=make_cache() if cache is None else cache, **settings(**changes)
    )


def assert_storage(value: Any, shape: tuple[int, ...], dtype: Any) -> None:
    assert type(value) is np.ndarray
    assert value.shape == shape
    assert value.dtype == np.dtype(dtype) and value.dtype.isnative
    assert value.flags.owndata and value.flags.writeable and value.flags.c_contiguous
    assert np.all(np.isfinite(value))


@contextmanager
def unchanged_policy_and_random(*arrays: Any) -> Any:
    """Observe preservation without installing a replacement production seam."""
    before = [a.copy() for a in arrays]
    policy, filters = np.geterr().copy(), list(warnings.filters)
    state = np.random.get_state()
    try:
        yield
    finally:
        assert np.geterr() == policy
        assert warnings.filters == filters
        after = np.random.get_state()
        assert state[0] == after[0]
        np.testing.assert_array_equal(state[1], after[1])
        assert state[2:] == after[2:]
        for original, saved in zip(arrays, before, strict=True):
            np.testing.assert_array_equal(original, saved)


def assert_contract_error(
    code: str, operation: str, function: Any, *args: Any, field: str | None = None, **kwargs: Any
) -> None:
    with pytest.raises(SimreconError) as caught:
        function(*args, **kwargs)
    error = caught.value
    assert isinstance(error, SimreconError)
    assert getattr(error, "code", None) == code
    message = getattr(error, "message", None)
    assert isinstance(message, str) and message.strip()
    text = " ".join(message.casefold().split()).strip(" .:;!?")
    assert any(character.isalpha() for character in text)
    # Reject clear placeholders, not unfamiliar descriptions or field synonyms.
    assert text not in {
        "error",
        "invalid",
        "invalid input",
        "failure",
        "failed",
        "unknown error",
        "an error occurred",
        "something went wrong",
        "unidentified problem",
    }
    # Free-form prose cannot be classified by a vocabulary whitelist. Every
    # diagnostic below requires manual assessment of operation OR field context
    # during behavior/risk review; passing these generic checks does not certify
    # that assessment. Keep the complete message and triggering context visible.
    print(f"DIAGNOSTIC_CONTEXT_REVIEW operation={operation!r} field={field!r} message={message!r}")


def reference(cache: Any, options: dict[str, Any]) -> tuple[Any, float, float]:
    shape, spacing = cache.source_shape_zyx, cache.source_spacing_um_zyx
    kernel = kernel_from_spectra(cache.lateral_spectra, shape)
    matrix = operator_matrix(
        kernel,
        shape,
        spacing,
        options["carrier_yx_per_um"],
        options["phases_rad"],
        options["beam_amplitudes"],
        options["excitation_um"],
        cache.refractive_index,
    )
    cr, cc = row_column_norms(pixel_matrix(kernel, shape, spacing, absolute=True))
    bound = light_bound(options["beam_amplitudes"])
    return matrix, bound * cr, len(options["phases_rad"]) * bound * cc


def assert_fidelity(actual: Any, expected: Any, scale: float) -> None:
    assert np.all(np.isfinite(actual))
    if scale == 0:
        np.testing.assert_array_equal(actual.ravel(), expected.ravel())
    else:
        # 5e-13 scale is an observer allowance, not an absolute signal floor.
        error = max(
            abs(float(a) - float(b)) for a, b in zip(actual.ravel(), expected.ravel(), strict=True)
        )
        assert error <= (1e-4 + 5e-13) * scale, (error, scale)


@pytest.mark.parametrize(
    ("shape", "spacing", "order"),
    [
        ((1, 2, 2), (0.2, 0.13, 0.09), 1),
        ((2, 2, 4), (0.31, 0.08, 0.15), 2),
        ((3, 4, 2), (0.17, 0.11, 0.07), 5),
        ((1, 2, 2), (0.2, 0.13, 0.09), 37),
    ],
)
def test_builder_complete_pupil_geometry_and_separate_absolute_error_budget(
    shape: Any,
    spacing: Any,
    order: int,
) -> None:
    fields = builder_fields(
        source_shape_zyx=shape, source_spacing_um_zyx=spacing, pupil_order=order
    )
    with unchanged_policy_and_random():
        cache = operator.build_kernel_cache(**fields)
    assert isinstance(cache, operator.InverseKernelCache)
    assert_storage(cache.lateral_spectra, (shape[0], 2 * shape[1], shape[2] + 1), np.float32)
    for name, expected in fields.items():
        assert getattr(cache, name) == expected
    spectra = cache.lateral_spectra
    np.testing.assert_array_equal(
        spectra, spectra[:, (-np.arange(2 * shape[1])) % (2 * shape[1]), :]
    )
    represented = kernel_from_spectra(spectra, shape)
    physical = physical_kernel(
        shape,
        spacing,
        fields["emission_um"],
        fields["refractive_index"],
        fields["detection_na"],
        order,
    )
    # Absolute errors precede summation; a signed four-point cancellation cannot pass.
    error = pixel_matrix(represented - physical, shape, spacing, absolute=True)
    base = pixel_matrix(physical, shape, spacing)
    er, ec = row_column_norms(error)
    br, bc = row_column_norms(base)
    assert br > 0 and bc > 0
    assert er <= (1e-4 + 5e-13) * br
    assert ec <= (1e-4 + 5e-13) * bc


def test_builder_record_normalization_frozen_bindings_and_call_independence() -> None:
    arguments = builder_fields(
        source_shape_zyx=(1, 2, 2),
        source_spacing_um_zyx=(1, 1, 1),
        emission_um=1,
        refractive_index=1,
        detection_na=1,
        pupil_order=1,
    )
    first = operator.build_kernel_cache(**arguments)
    second = operator.build_kernel_cache(**arguments)
    assert {
        name
        for name in dir(first)
        if not name.startswith("_") and not callable(getattr(first, name))
    } == set(FIELDS)
    assert type(first.source_shape_zyx) is tuple
    assert all(type(x) is int for x in first.source_shape_zyx)
    assert type(first.source_spacing_um_zyx) is tuple
    assert all(type(x) is float for x in first.source_spacing_um_zyx)
    assert all(
        type(getattr(first, name)) is float
        for name in ("emission_um", "refractive_index", "detection_na")
    )
    assert type(first.pupil_order) is int
    for field in FIELDS:
        with pytest.raises((AttributeError, TypeError)):
            setattr(first, field, getattr(first, field))
    assert not np.shares_memory(first.lateral_spectra, second.lateral_spectra)
    # Fidelity permits different rounding and unused-lag choices across calls;
    # ownership does not add a coefficientwise reproducibility requirement.
    physical = physical_kernel((1, 2, 2), (1.0, 1.0, 1.0), 1.0, 1.0, 1.0, 1)
    norms = row_column_norms(pixel_matrix(physical, (1, 2, 2), (1.0, 1.0, 1.0)))
    for cache in (first, second):
        assert_storage(cache.lateral_spectra, (1, 4, 3), np.float32)
        represented = kernel_from_spectra(cache.lateral_spectra, (1, 2, 2))
        errors = row_column_norms(
            pixel_matrix(represented - physical, (1, 2, 2), (1.0, 1.0, 1.0), absolute=True)
        )
        assert all(
            error <= (1e-4 + 5e-13) * norm for error, norm in zip(errors, norms, strict=True)
        )
    saved = second.lateral_spectra.copy()
    first.lateral_spectra[:] = 0  # Contents, unlike the field binding, remain mutable.
    np.testing.assert_array_equal(second.lateral_spectra, saved)


@pytest.mark.parametrize("shape", [(1, 2, 4), (2, 4, 2), (3, 2, 4)])
def test_signed_direct_payload_forward_and_real_adjoint_values(shape: Any) -> None:
    cache = operator.InverseKernelCache(**cache_fields(shape))
    options = settings()
    matrix, forward_norm, adjoint_norm = reference(cache, options)
    x, y = operand("forward", shape), operand("adjoint", shape)
    with unchanged_policy_and_random(
        x, y, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
    ):
        ax = operator.forward(x, kernel_cache=cache, **options)
        aty = operator.adjoint(y, kernel_cache=cache, **options)
    assert_storage(ax, y.shape, np.float64)
    assert_storage(aty, x.shape, np.float64)
    assert_fidelity(ax, apply_reference(matrix, x), forward_norm * float(np.max(np.abs(x))))
    assert_fidelity(
        aty, apply_reference(matrix, y, transpose=True), adjoint_norm * float(np.max(np.abs(y)))
    )
    # Supplemental duality uses a bound derived from both per-output error budgets.
    lhs = math.fsum(float(a) * float(b) for a, b in zip(ax.ravel(), y.ravel(), strict=True))
    rhs = math.fsum(float(a) * float(b) for a, b in zip(x.ravel(), aty.ravel(), strict=True))
    bound = forward_norm * float(np.max(np.abs(x))) * math.fsum(map(abs, map(float, y.ravel())))
    bound += adjoint_norm * float(np.max(np.abs(y))) * math.fsum(map(abs, map(float, x.ravel())))
    assert abs(lhs - rhs) <= (1e-4 + 5e-13) * bound


@pytest.mark.parametrize("shape", [(2, 2, 2), (3, 2, 4)])
def test_nonzero_finite_map_accepts_coordinated_unused_lateral_padding(shape: Any) -> None:
    # Each addition is exact float32 here. The added inverse is supported only
    # on y=Ny OR x=Nx. The original signed finite map and its G scales survive.
    base = operator.InverseKernelCache(**cache_fields(shape))
    payload = base.lateral_spectra + padding_only_spectra(shape, 256.0)
    cache = operator.InverseKernelCache(**(cache_fields(shape) | {"lateral_spectra": payload}))
    options = settings()
    matrix, f_norm, j_norm = reference(base, options)
    padded_matrix, padded_f, padded_j = reference(cache, options)
    np.testing.assert_array_equal(padded_matrix, matrix)
    assert (padded_f, padded_j) == (f_norm, j_norm)
    assert np.max(np.abs(payload - base.lateral_spectra)) == 256
    matrix.flags.writeable = False
    for operation in ("forward", "adjoint"):
        call_payload = payload.copy()
        call_cache = operator.InverseKernelCache(
            **(cache_fields(shape) | {"lateral_spectra": call_payload})
        )
        options, data = settings(), operand(operation, shape)
        with unchanged_policy_and_random(data, call_payload):
            result = getattr(operator, operation)(data, kernel_cache=call_cache, **options)
        expected_shape = (
            (3, shape[0], shape[1] // 2, shape[2] // 2) if operation == "forward" else shape
        )
        assert_storage(result, expected_shape, np.float64)
        assert_fidelity(
            result,
            apply_reference(matrix, data, transpose=operation == "adjoint"),
            (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
        )


def test_all_source_detector_edges_corners_and_interior_basis_columns() -> None:
    # A dense basis sweep asserts every finite interaction, including opposite corners.
    shape = (2, 2, 4)
    cache = operator.InverseKernelCache(**cache_fields(shape))
    options = settings(phases_rad=np.array([-0.4, 0.9]))
    matrix, f_norm, j_norm = reference(cache, options)
    matrix.flags.writeable = False
    for operation in ("forward", "adjoint"):
        cache = operator.InverseKernelCache(**cache_fields(shape))
        options = settings(phases_rad=np.array([-0.4, 0.9]))
        data_shape = shape if operation == "forward" else (2, 2, 1, 2)
        for index in range(math.prod(data_shape)):
            data = np.zeros(data_shape, dtype=np.float32)
            data.flat[index] = -1 if index % 2 else 1
            result = getattr(operator, operation)(data, kernel_cache=cache, **options)
            expected = apply_reference(matrix, data, transpose=operation == "adjoint")
            assert_fidelity(result, expected, f_norm if operation == "forward" else j_norm)


@pytest.mark.parametrize(
    ("carrier", "phases", "amplitudes"),
    [
        ([0.0, 0.0], [0.7], (0.7, 1.2, 0.25)),
        ([-0.73, 0.41], [0.2, 0.2, -2.1], (0.7, 1.2, 0.25)),
        ([0.73, -0.41], [-0.8, 0.3], (1.0, 0.0, 0.0)),
        ([0.73, -0.41], [-0.8, 0.3], (0.0, 1.0, 0.0)),
        ([0.73, -0.41], [-0.8, 0.3], (0.0, 0.0, 1.0)),
        ([0.73, -0.41], [-0.8, 0.3], (0.0, 0.4, 1.3)),
        ([0.73, -0.41], [-0.8, 0.3], (0.4, 0.0, 1.3)),
        ([0.73, -0.41], [-0.8, 0.3], (0.4, 1.3, 0.0)),
        ([2.0, 0.0], [0.2, 1.1], (0.7, 1.2, 0.25)),  # Exact grazing q=n/lambda.
    ],
)
def test_continuous_signed_carriers_harmonics_unequal_sides_and_rank_free_positives(
    carrier: Any,
    phases: Any,
    amplitudes: Any,
) -> None:
    cache = make_cache(refractive_index=1.0)
    options = settings(
        carrier_yx_per_um=np.array(carrier),
        phases_rad=np.array(phases),
        beam_amplitudes=amplitudes,
        excitation_um=0.5,
    )
    matrix, f_norm, j_norm = reference(cache, options)
    x, y = operand("forward"), operand("adjoint", phases=len(phases))
    assert_fidelity(
        operator.forward(x, kernel_cache=cache, **options),
        apply_reference(matrix, x),
        f_norm * float(np.max(np.abs(x))),
    )
    assert_fidelity(
        operator.adjoint(y, kernel_cache=cache, **options),
        apply_reference(matrix, y, transpose=True),
        j_norm * float(np.max(np.abs(y))),
    )


def test_builder_to_application_physical_bound_is_sum_of_two_separate_budgets() -> None:
    shape = (2, 2, 4)
    fields = builder_fields(source_shape_zyx=shape, pupil_order=2)
    cache = operator.build_kernel_cache(**fields)
    options = settings()
    physical = physical_kernel(shape, SPACING, 0.61, 1.33, 0.9, 2)
    matrix = operator_matrix(
        physical,
        shape,
        SPACING,
        options["carrier_yx_per_um"],
        options["phases_rad"],
        options["beam_amplitudes"],
        0.48,
        1.33,
    )
    cr, cc = row_column_norms(pixel_matrix(physical, shape, SPACING))
    l_bound = light_bound(options["beam_amplitudes"])
    x, y = operand("forward", shape), operand("adjoint", shape)
    for operation, data, scale in [("forward", x, cr * l_bound), ("adjoint", y, 3 * cc * l_bound)]:
        result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        expected = apply_reference(matrix, data, transpose=operation == "adjoint")
        error = float(np.max(np.abs(result.ravel() - expected)))
        assert error <= (2e-4 + 1e-8 + 1e-12) * scale * float(np.max(np.abs(data)))


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("zero_kind", ["operand", "kernel", "both"])
def test_zero_scale_is_exact_zero_after_validation(operation: str, zero_kind: str) -> None:
    cache = make_cache()
    data = operand(operation)
    if zero_kind in ("operand", "both"):
        data[:] = 0
    if zero_kind in ("kernel", "both"):
        cache.lateral_spectra[:] = 0
    result = run(operation, data, cache)
    assert_storage(result, (3, 3, 1, 2) if operation == "forward" else SHAPE, np.float64)
    np.testing.assert_array_equal(result, np.zeros_like(result))


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("layout", ["big_endian", "strided", "fortran", "read_only"])
def test_float32_operand_and_cache_layouts_are_semantic_not_rejection_rules(
    operation: str,
    layout: str,
) -> None:
    def variant(array: Any) -> Any:
        if layout == "big_endian":
            return array.astype(">f4")
        if layout == "fortran":
            return np.asfortranarray(array)
        if layout == "read_only":
            result = array.copy()
            result.flags.writeable = False
            return result
        storage = np.empty((*array.shape, 2), dtype=np.float32)
        storage[..., 0] = array
        return storage[..., 0]

    original = make_cache()
    cache = make_cache(lateral_spectra=variant(original.lateral_spectra))
    data = variant(operand(operation))
    matrix, f_norm, j_norm = reference(cache, settings())
    with unchanged_policy_and_random(data, cache.lateral_spectra):
        result = run(operation, data, cache)
    expected_shape = (3, 3, 1, 2) if operation == "forward" else SHAPE
    assert_storage(result, expected_shape, np.float64)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_outputs_own_storage_and_do_not_alias_inputs_cache_or_other_calls(operation: str) -> None:
    cache, data = make_cache(), operand(operation)
    first, second = run(operation, data, cache), run(operation, data, cache)
    matrix, f_norm, j_norm = reference(cache, settings())
    expected = apply_reference(matrix, data, transpose=operation == "adjoint")
    scale = (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data)))
    for result in (first, second):
        assert_storage(result, (3, 3, 1, 2) if operation == "forward" else SHAPE, np.float64)
        assert_fidelity(result, expected, scale)
    saved = second.copy()
    assert not np.shares_memory(first, second)
    assert not np.shares_memory(first, data)
    assert not np.shares_memory(first, cache.lateral_spectra)
    first[:] = 123
    data[:] = 0
    cache.lateral_spectra[:] = 0
    np.testing.assert_array_equal(second, saved)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "magnitude",
    [
        float(np.finfo(np.float32).smallest_subnormal),
        float(np.finfo(np.float32).tiny),
        1e-30,
        1e30,
        float(np.finfo(np.float32).max),
    ],
)
def test_tiny_and_large_float32_operands_keep_max_absolute_scaled_accuracy(
    operation: str,
    magnitude: float,
) -> None:
    cache = make_cache()
    data = np.sign(operand(operation)).astype(np.float32) * np.float32(magnitude)
    matrix, f_norm, j_norm = reference(cache, settings())
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, cache.lateral_spectra):
                result = run(operation, data, cache)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * magnitude,
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "kernel_magnitude",
    [float(np.finfo(np.float32).smallest_subnormal), float(np.finfo(np.float32).max)],
)
def test_extreme_represented_cache_is_not_a_hidden_conditioning_gate(
    operation: str,
    kernel_magnitude: float,
) -> None:
    # A constant spectrum represents a lateral delta. No ill-conditioned inference occurs.
    cache = make_cache(lateral_spectra=np.full((3, 4, 5), kernel_magnitude, dtype=np.float32))
    data = operand(operation)
    matrix, f_norm, j_norm = reference(cache, settings())
    result = run(operation, data, cache)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "extreme",
    ["amplitudes_large", "amplitudes_tiny", "phase", "turns", "axial_phase", "carrier_norm"],
)
def test_huge_reducible_or_safely_normalized_settings_remain_valid(
    operation: str,
    extreme: str,
) -> None:
    changes: dict[str, Any] = {}
    options = settings()
    if extreme == "amplitudes_large":
        options["beam_amplitudes"] = (1e308, 7e307, 2e307)
    elif extreme == "amplitudes_tiny":
        options["beam_amplitudes"] = (1e-300, 7e-301, 2e-301)
    elif extreme == "phase":
        options["phases_rad"] = np.array([1e308, -1e200, float(2**80)])
    elif extreme == "turns":
        changes["source_spacing_um_zyx"] = (0.23, 1e200, 1e-200)
        # Area remains finite while the lateral turn product overflows raw float64.
        changes["refractive_index"] = 1e200
        options["carrier_yx_per_um"] = np.array([1e200, -1e199])
    elif extreme == "axial_phase":
        changes["source_spacing_um_zyx"] = (1e308, 0.17, 0.11)
    else:
        changes["refractive_index"] = 1e200
        options["carrier_yx_per_um"] = np.array([-1e200, 1e200])
    cache = make_cache(**changes)
    matrix, f_norm, j_norm = reference(cache, options)
    data = operand(operation)
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, cache.lateral_spectra):
                result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


@pytest.mark.parametrize("value", [1e-300, 1e308])
def test_builder_safe_ratio_evaluation_does_not_reject_raw_square_overflow(value: float) -> None:
    fields = builder_fields(
        source_shape_zyx=(1, 2, 2),
        emission_um=value,
        refractive_index=value,
        detection_na=value,
        pupil_order=1,
    )
    cache = operator.build_kernel_cache(**fields)
    physical = physical_kernel((1, 2, 2), SPACING, 1.0, 1.0, 1.0, 1)
    represented = kernel_from_spectra(cache.lateral_spectra, (1, 2, 2))
    error = pixel_matrix(represented - physical, (1, 2, 2), SPACING, absolute=True)
    base = pixel_matrix(physical, (1, 2, 2), SPACING)
    for actual, scale in zip(row_column_norms(error), row_column_norms(base), strict=True):
        assert actual <= (1e-4 + 5e-13) * scale


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_cache_subclass_and_integer_phase_carrier_settings_are_permitted(operation: str) -> None:
    class Child(operator.InverseKernelCache):
        pass

    cache = Child(**cache_fields())
    options = settings(
        carrier_yx_per_um=np.array([0, 1], dtype=np.int16),
        phases_rad=np.array([0, 1, 2], dtype=np.uint64),
    )
    data = operand(operation)
    matrix, f_norm, j_norm = reference(cache, options)
    result = getattr(operator, operation)(data, kernel_cache=cache, **options)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_direct_cache_and_beam_settings_accept_plain_builtin_integer_scalars(
    operation: str,
) -> None:
    cache = make_cache(
        source_spacing_um_zyx=(1, 1, 1),
        emission_um=1,
        refractive_index=2,
        detection_na=1,
    )
    options = settings(beam_amplitudes=(1, 2, 0), excitation_um=1)
    data = operand(operation)
    matrix, f_norm, j_norm = reference(cache, options)
    with unchanged_policy_and_random(
        data, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
    ):
        result = getattr(operator, operation)(data, kernel_cache=cache, **options)
    assert_storage(result, (3, 3, 1, 2) if operation == "forward" else SHAPE, np.float64)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


class ArrayChild(np.ndarray):
    """A prohibited ndarray subclass, without custom numerical behavior."""


class FloatChild(float):
    """A prohibited scalar subclass."""


class IntChild(int):
    """A prohibited scalar subclass."""


class TupleChild(tuple):
    """A prohibited tuple subclass, without custom element behavior."""


BAD_METADATA = [
    ("source_shape_zyx", [3, 2, 4]),
    ("source_shape_zyx", TupleChild((3, 2, 4))),
    ("source_shape_zyx", (3, 2)),
    ("source_shape_zyx", (True, 2, 4)),
    ("source_shape_zyx", (np.int64(3), 2, 4)),
    ("source_shape_zyx", (IntChild(3), 2, 4)),
    ("source_shape_zyx", (3.0, 2, 4)),
    ("source_shape_zyx", (0, 2, 4)),
    ("source_shape_zyx", (-1, 2, 4)),
    ("source_shape_zyx", (3, 3, 4)),
    ("source_shape_zyx", (3, 2, 1)),
    ("source_spacing_um_zyx", [0.23, 0.17, 0.11]),
    ("source_spacing_um_zyx", TupleChild((0.23, 0.17, 0.11))),
    ("source_spacing_um_zyx", (0.23, 0.17)),
    ("source_spacing_um_zyx", (0.0, 0.17, 0.11)),
    ("source_spacing_um_zyx", (-1.0, 0.17, 0.11)),
    ("source_spacing_um_zyx", (float("inf"), 0.17, 0.11)),
    ("source_spacing_um_zyx", (0.23, float("nan"), 0.11)),
    ("source_spacing_um_zyx", (True, 0.17, 0.11)),
    ("source_spacing_um_zyx", (np.float64(0.23), 0.17, 0.11)),
    ("source_spacing_um_zyx", (FloatChild(0.23), 0.17, 0.11)),
    ("source_spacing_um_zyx", (np.int64(1), 0.17, 0.11)),
    ("source_spacing_um_zyx", (IntChild(1), 0.17, 0.11)),
    ("source_spacing_um_zyx", (10**400, 0.17, 0.11)),
    ("emission_um", 0),
    ("emission_um", -0.5),
    ("emission_um", float("nan")),
    ("emission_um", float("inf")),
    ("emission_um", True),
    ("emission_um", "0.61"),
    ("emission_um", np.float64(0.61)),
    ("emission_um", FloatChild(0.61)),
    ("emission_um", np.int64(1)),
    ("emission_um", IntChild(1)),
    ("emission_um", 10**400),
    ("refractive_index", 0),
    ("refractive_index", -1),
    ("refractive_index", float("nan")),
    ("refractive_index", float("inf")),
    ("detection_na", 0),
    ("detection_na", -0.1),
    ("detection_na", 1.34),
    ("detection_na", float("nan")),
    ("detection_na", float("inf")),
    ("pupil_order", 0),
    ("pupil_order", -1),
    ("pupil_order", True),
    ("pupil_order", 2.0),
    ("pupil_order", np.int64(3)),
    ("pupil_order", IntChild(3)),
]
BAD_METADATA += [
    (field, value)
    for field in ("refractive_index", "detection_na")
    for value in (True, "1", np.float64(1), FloatChild(1), np.int64(1), IntChild(1), 10**400)
]


@pytest.mark.parametrize(("field", "value"), BAD_METADATA)
def test_builder_rejects_only_contractual_metadata_grammar_and_domain(
    field: str, value: Any
) -> None:
    with unchanged_policy_and_random():
        assert_contract_error(
            INVALID,
            "build",
            operator.build_kernel_cache,
            field=field,
            **builder_fields(**{field: value}),
        )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(("field", "value"), BAD_METADATA)
def test_every_direct_cache_metadata_field_is_validated_even_for_zero_input(
    operation: str,
    field: str,
    value: Any,
) -> None:
    # Direct construction itself must not validate or authenticate fields.
    cache = make_cache(**{field: value})
    data = np.zeros_like(operand(operation))
    with unchanged_policy_and_random(data):
        assert_contract_error(
            INVALID,
            operation,
            getattr(operator, operation),
            data,
            kernel_cache=cache,
            field=field,
            **settings(beam_amplitudes=(0.0, 1.0, 0.0)),
        )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "bad_kind",
    [
        "float64",
        "float16",
        "int32",
        "bool",
        "complex64",
        "object",
        "structured",
        "subclass",
        "list",
        "shape",
        "empty",
        "nan",
        "positive_inf",
        "negative_inf",
    ],
)
def test_operands_reject_wrong_representations_and_nonfinite_components(
    operation: str,
    bad_kind: str,
) -> None:
    data = operand(operation)
    if bad_kind in ("float64", "float16", "int32", "bool", "complex64", "object"):
        data = data.astype(bad_kind)
    elif bad_kind == "structured":
        data = np.zeros(data.shape, dtype=[("v", "f4")])
    elif bad_kind == "subclass":
        data = data.view(ArrayChild)
    elif bad_kind == "list":
        data = data.tolist()
    elif bad_kind == "shape":
        data = data.reshape(-1)
    elif bad_kind == "empty":
        data = data[:0]
    else:
        data.flat[0] = {"nan": np.nan, "positive_inf": np.inf, "negative_inf": -np.inf}[bad_kind]
    assert_contract_error(
        INVALID,
        operation,
        getattr(operator, operation),
        data,
        kernel_cache=make_cache(),
        field="source_e" if operation == "forward" else "detector_values",
        **settings(),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    "bad_kind",
    [
        "float64",
        "float16",
        "int32",
        "bool",
        "complex64",
        "object",
        "subclass",
        "list",
        "shape",
        "nan",
        "inf",
        "asymmetric_y",
    ],
)
def test_cache_payload_rejects_width_shape_nonfinite_and_exact_y_asymmetry(
    operation: str,
    bad_kind: str,
) -> None:
    payload = signed_spectra(SHAPE)
    if bad_kind in ("float64", "float16", "int32", "bool", "complex64", "object"):
        payload = payload.astype(bad_kind)
    elif bad_kind == "subclass":
        payload = payload.view(ArrayChild)
    elif bad_kind == "list":
        payload = payload.tolist()
    elif bad_kind == "shape":
        payload = payload[..., :-1]
    elif bad_kind == "asymmetric_y":
        payload[0, 1, 0] = np.nextafter(payload[0, 1, 0], np.float32(np.inf))
    else:
        payload[0, 0, 0] = np.nan if bad_kind == "nan" else np.inf
    cache = make_cache(lateral_spectra=payload)
    assert_contract_error(
        INVALID,
        operation,
        getattr(operator, operation),
        np.zeros_like(operand(operation)),
        kernel_cache=cache,
        field="lateral_spectra",
        **settings(),
    )


BAD_SETTINGS = [
    ("carrier_yx_per_um", [0.0, 0.0]),
    ("carrier_yx_per_um", np.array([True, False])),
    ("carrier_yx_per_um", np.array([0.0j, 0.0j])),
    ("carrier_yx_per_um", np.array([0, 0], dtype=object)),
    ("carrier_yx_per_um", np.array([0.0, 0.0]).view(ArrayChild)),
    ("carrier_yx_per_um", np.array([0.0])),
    ("carrier_yx_per_um", np.array([[0.0, 0.0]])),
    ("carrier_yx_per_um", np.array([np.nan, 0.0])),
    ("carrier_yx_per_um", np.array([0.0, np.inf])),
    ("carrier_yx_per_um", np.array([3.0, 0.0])),
    ("phases_rad", [0.0, 1.0, 2.0]),
    ("phases_rad", np.array([], dtype=float)),
    ("phases_rad", np.array([True, False, True])),
    ("phases_rad", np.array([0j, 1j, 2j])),
    ("phases_rad", np.array([0, 1, 2], dtype=object)),
    ("phases_rad", np.array([0.0, 1.0, 2.0]).view(ArrayChild)),
    ("phases_rad", np.array([[0.0, 1.0, 2.0]])),
    ("phases_rad", np.array([0.0, np.nan, 2.0])),
    ("phases_rad", np.array([0.0, np.inf, 2.0])),
    ("beam_amplitudes", [1.0, 1.0, 1.0]),
    ("beam_amplitudes", TupleChild((1.0, 1.0, 1.0))),
    ("beam_amplitudes", (1.0, 1.0)),
    ("beam_amplitudes", (0.0, 0.0, 0.0)),
    ("beam_amplitudes", (-0.1, 1.0, 0.0)),
    ("beam_amplitudes", (float("inf"), 1.0, 0.0)),
    ("beam_amplitudes", (float("nan"), 1.0, 0.0)),
    ("beam_amplitudes", (True, 1.0, 0.0)),
    ("beam_amplitudes", (np.float64(1), 1.0, 0.0)),
    ("beam_amplitudes", (FloatChild(1), 1.0, 0.0)),
    ("beam_amplitudes", (np.int64(1), 1.0, 0.0)),
    ("beam_amplitudes", (IntChild(1), 1.0, 0.0)),
    ("beam_amplitudes", (10**400, 1.0, 0.0)),
    ("excitation_um", 0),
    ("excitation_um", -0.5),
    ("excitation_um", float("nan")),
    ("excitation_um", float("inf")),
    ("excitation_um", True),
    ("excitation_um", np.float64(0.5)),
    ("excitation_um", FloatChild(0.5)),
    ("excitation_um", "0.5"),
    ("excitation_um", 10**400),
]


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(("field", "value"), BAD_SETTINGS)
def test_settings_are_validated_before_zero_shortcuts(
    operation: str, field: str, value: Any
) -> None:
    cache = make_cache(lateral_spectra=np.zeros((3, 4, 5), dtype=np.float32))
    data = np.zeros_like(operand(operation))
    assert_contract_error(
        INVALID,
        operation,
        getattr(operator, operation),
        data,
        kernel_cache=cache,
        field=field,
        **settings(**{field: value}),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("cache", [object(), {}, None, 3])
def test_consumers_require_cache_record_instance(operation: str, cache: Any) -> None:
    assert_contract_error(
        INVALID,
        operation,
        getattr(operator, operation),
        operand(operation),
        kernel_cache=cache,
        field="kernel_cache",
        **settings(),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_phase_count_and_operand_shape_must_agree_without_silent_prediction_downcast(
    operation: str,
) -> None:
    cache = make_cache()
    if operation == "adjoint":
        assert_contract_error(
            INVALID,
            operation,
            operator.adjoint,
            operand(operation),
            kernel_cache=cache,
            field="detector_values / phases_rad",
            **settings(phases_rad=np.array([0.2])),
        )
    else:
        # A prediction is deliberately float64. Passing it as data requires caller rounding.
        prediction = operator.forward(operand("forward"), kernel_cache=cache, **settings())
        assert_contract_error(
            INVALID,
            "adjoint",
            operator.adjoint,
            prediction,
            kernel_cache=cache,
            field="detector_values",
            **settings(),
        )
        rounded = prediction.astype(np.float32)
        matrix, _, j_norm = reference(cache, settings())
        result = operator.adjoint(rounded, kernel_cache=cache, **settings())
        assert_fidelity(
            result,
            apply_reference(matrix, rounded, transpose=True),
            j_norm * float(np.max(np.abs(rounded))),
        )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_required_settings_keyword_binding_and_no_hidden_backend_interface(operation: str) -> None:
    function, data, cache = getattr(operator, operation), operand(operation), make_cache()
    options = dict(kernel_cache=cache, **settings())
    for missing in options:
        selected = {k: v for k, v in options.items() if k != missing}
        with pytest.raises(TypeError):
            function(data, **selected)
    with pytest.raises(TypeError):
        function(data, cache, **settings())
    with pytest.raises(TypeError):
        function(data, **options, backend="caller_chosen")
    signature = inspect.signature(function)
    assert set(list(signature.parameters)[1:]) == set(options)
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY for p in list(signature.parameters.values())[1:]
    )


def test_builder_required_keyword_binding() -> None:
    fields = builder_fields()
    for missing in fields:
        with pytest.raises(TypeError):
            operator.build_kernel_cache(**{k: v for k, v in fields.items() if k != missing})
    with pytest.raises(TypeError):
        operator.build_kernel_cache(*fields.values())
    with pytest.raises(TypeError):
        operator.build_kernel_cache(**fields, backend="caller_chosen")


@pytest.mark.parametrize(
    "changes",
    [
        {"source_shape_zyx": (sys.maxsize, 2, 2)},
        {"emission_um": 1e30, "detection_na": 1.0},
        {"emission_um": 1e-30, "detection_na": 1.0},
    ],
)
def test_concrete_address_space_or_float32_cache_obstruction_reports_range(changes: Any) -> None:
    # On this 4x4 grid every exact inverse value is a multiple of 2**-153
    # and at most float32 max in magnitude, regardless of unused lateral lags.
    # With M=4 sources and Q1, B_Q <= 4*M*area*peak. A required on-axis
    # error therefore already exceeds the full row budget for either peak.
    with unchanged_policy_and_random():
        assert_contract_error(
            RANGE,
            "build",
            operator.build_kernel_cache,
            field=(
                "source_shape_zyx"
                if "source_shape_zyx" in changes
                else "lateral_spectra / emission_um / detection_na"
            ),
            **builder_fields(source_shape_zyx=(1, 2, 2)) | changes,
        )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_unrepresentable_owned_output_is_range_without_warning_or_policy_leak(
    operation: str,
) -> None:
    # Every queried kernel value is 1.0. Pixel area is 1e308 (representable),
    # but four same-sign terms and nonzero data require >float64 output.
    shape = (1, 2, 2)
    plane = np.ones((1, 4, 4), dtype=np.float64)
    cache = operator.InverseKernelCache(
        **(
            cache_fields(shape)
            | {
                "lateral_spectra": spectra_from_plane(plane, shape),
                "source_spacing_um_zyx": (1.0, 1e154, 1e154),
            }
        )
    )
    data_shape = shape if operation == "forward" else (1, 1, 1, 1)
    data = np.full(data_shape, 100.0, dtype=np.float32)
    options = settings(
        carrier_yx_per_um=np.zeros(2), phases_rad=np.zeros(1), beam_amplitudes=(1.0, 0.0, 0.0)
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, cache.lateral_spectra):
                assert_contract_error(
                    RANGE,
                    operation,
                    getattr(operator, operation),
                    data,
                    kernel_cache=cache,
                    field=f"{operation} output",
                    **options,
                )
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_failure_preserves_inputs_random_state_and_caller_warning_policy(operation: str) -> None:
    data = operand(operation)
    data.flat[1] = np.nan
    cache = make_cache()
    options = settings()
    old_policy = np.seterr(all="raise")
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("error")
            with unchanged_policy_and_random(
                data, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
            ):
                assert_contract_error(
                    INVALID,
                    operation,
                    getattr(operator, operation),
                    data,
                    kernel_cache=cache,
                    field="source_e" if operation == "forward" else "detector_values",
                    **options,
                )
        assert not caught
    finally:
        np.seterr(**old_policy)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(("step", "strength"), [(1e-180, 1e30), (1e180, 1e-30)])
def test_safe_pixel_kernel_operand_product_survives_raw_area_underflow_or_overflow(
    operation: str,
    step: float,
    strength: float,
) -> None:
    from decimal import localcontext

    from simulation_inverse_operator_fixture import decimal

    shape = (1, 2, 2)
    # The exact inverse DFT of a constant spectrum is a lateral delta.
    coefficient = np.float32(strength)
    cache = operator.InverseKernelCache(
        **(
            cache_fields(shape)
            | {
                "lateral_spectra": np.full((1, 4, 3), coefficient, dtype=np.float32),
                "source_spacing_um_zyx": (1.0, step, step),
            }
        )
    )
    data_shape = shape if operation == "forward" else (1, 1, 1, 1)
    data = np.full(data_shape, coefficient, dtype=np.float32)
    with localcontext() as context:
        context.prec = 100
        expected_value = decimal(step) ** 2 * decimal(coefficient) ** 2
        if operation == "forward":
            expected_value *= 4
        expected = float(expected_value)
    assert math.isfinite(expected) and expected != 0
    options = settings(
        carrier_yx_per_um=np.zeros(2), phases_rad=np.zeros(1), beam_amplitudes=(1.0, 0.0, 0.0)
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, cache.lateral_spectra):
                result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    np.testing.assert_allclose(result, expected, rtol=1e-4 + 5e-13, atol=0)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_exact_real_carrier_domain_rejects_norm_rounding_onto_grazing_boundary(
    operation: str,
) -> None:
    cache = make_cache(refractive_index=1.0)
    # sqrt(2**2 + tiny**2) > 2 in exact real arithmetic, although hypot rounds to 2.
    carrier = np.array([2.0, np.finfo(np.float64).smallest_subnormal])
    assert_contract_error(
        INVALID,
        operation,
        getattr(operator, operation),
        operand(operation),
        kernel_cache=cache,
        field="carrier_yx_per_um",
        **settings(excitation_um=0.5, carrier_yx_per_um=carrier),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize(
    ("dtype", "example"),
    [
        (np.float16, "small integers"),
        (np.float32, "small integers"),
        (np.float64, "small integers"),
        (np.longdouble, "small integers"),
        (np.int8, "small integers"),
        (np.uint64, "small integers"),
        (np.dtype("f8").newbyteorder("S"), "continuous signed float"),
        (np.dtype("i2").newbyteorder("S"), "signed integers"),
        (np.dtype("u4").newbyteorder("S"), "small integers"),
    ],
)
def test_plain_real_setting_widths_and_noncontiguous_read_only_arrays_are_valid(
    operation: str,
    dtype: Any,
    example: str,
) -> None:
    if example == "continuous signed float":
        phase_values, carrier_backwards = [0.21, 1.37, -0.82], [0.41, -0.73]
    elif example == "signed integers":
        phase_values, carrier_backwards = [-2, 0, 3], [1, -1]
    else:
        phase_values, carrier_backwards = [0, 1, 2], [0, 1]
    phase_storage = np.array([[phase, 0] for phase in phase_values], dtype=dtype)
    phases = phase_storage[:, 0]
    phases.flags.writeable = False
    carrier = np.array(carrier_backwards, dtype=dtype)[::-1]
    carrier.flags.writeable = False
    options = settings(carrier_yx_per_um=carrier, phases_rad=phases)
    cache, data = make_cache(), operand(operation)
    matrix, f_norm, j_norm = reference(cache, options)
    with unchanged_policy_and_random(data, cache.lateral_spectra, phases, carrier):
        result = getattr(operator, operation)(data, kernel_cache=cache, **options)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("field", ["phases_rad", "carrier_yx_per_um"])
def test_longdouble_original_and_normalized_finiteness_without_platform_skip(
    operation: str,
    field: str,
) -> None:
    maximum = np.finfo(np.longdouble).max
    extended = maximum > np.longdouble(np.finfo(np.float64).max)
    if field == "carrier_yx_per_um" and extended:
        maximum = np.longdouble(np.finfo(np.float64).max) * np.longdouble(1.5)
    values = np.array([maximum] if field == "phases_rad" else [maximum, 0], dtype=np.longdouble)
    cache = make_cache()
    options = settings(**{field: values})
    if field == "carrier_yx_per_um":
        # q is max or 1.5*max, within n/lambda=2*max as exact reals.
        # Only normalization overflows on extended-width platforms.
        cache = make_cache(refractive_index=float(np.finfo(np.float64).max))
        options["excitation_um"] = 0.5
    data = operand(operation, phases=1 if field == "phases_rad" else 3)
    if values[0] > np.longdouble(np.finfo(np.float64).max):
        assert_contract_error(
            INVALID,
            operation,
            getattr(operator, operation),
            data,
            kernel_cache=cache,
            field=field,
            **options,
        )
    else:
        # Platforms whose longdouble equals float64 still accept their finite maximum.
        matrix, f_norm, j_norm = reference(cache, options)
        result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        assert_fidelity(
            result,
            apply_reference(matrix, data, transpose=operation == "adjoint"),
            (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
        )


def assert_dependency_bypass_result(
    result: Any, operation: str, cache: Any, data: Any, options: dict[str, Any]
) -> None:
    """Check independently correct work when no wrapped dependency was entered."""
    if operation == "build":
        assert isinstance(result, operator.InverseKernelCache)
        for field, expected in builder_fields(pupil_order=2).items():
            assert getattr(result, field) == expected
        assert_storage(result.lateral_spectra, (3, 4, 5), np.float32)
        np.testing.assert_array_equal(
            result.lateral_spectra, result.lateral_spectra[:, [0, 3, 2, 1], :]
        )
        physical = physical_kernel(SHAPE, SPACING, 0.61, 1.33, 0.9, 2)
        represented = kernel_from_spectra(result.lateral_spectra, SHAPE)
        errors = row_column_norms(
            pixel_matrix(represented - physical, SHAPE, SPACING, absolute=True)
        )
        scales = row_column_norms(pixel_matrix(physical, SHAPE, SPACING))
        assert all(
            error <= (1e-4 + 5e-13) * scale for error, scale in zip(errors, scales, strict=True)
        )
    else:
        matrix, f_norm, j_norm = reference(cache, options)
        shape = (
            (len(options["phases_rad"]), SHAPE[0], SHAPE[1] // 2, SHAPE[2] // 2)
            if operation == "forward"
            else SHAPE
        )
        assert_storage(result, shape, np.float64)
        assert_fidelity(
            result,
            apply_reference(matrix, data, transpose=operation == "adjoint"),
            (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
        )


@pytest.mark.parametrize("operation", ["build", "forward", "adjoint"])
@pytest.mark.parametrize("error_class", [MemoryError, RuntimeError, TypeError, ValueError])
def test_unrelated_public_numerical_dependency_exception_is_not_relabelled(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    error_class: type[Exception],
) -> None:
    # These are real public dependency boundaries, not product internals. No call
    # is required: direct sums, other backends and analytic builders remain valid.
    cache, data, options = (
        make_cache(),
        operand("forward" if operation == "build" else operation),
        settings(),
    )
    sentinel = error_class("unrelated public numerical dependency failure")
    entered = False

    def fail(*args: Any, **kwargs: Any) -> Any:
        nonlocal entered
        entered = True
        raise sentinel

    for module_name in ("numpy.fft", "scipy.fft"):
        module = importlib.import_module(module_name)
        for name in (
            "fft",
            "ifft",
            "rfft",
            "irfft",
            "fft2",
            "ifft2",
            "rfft2",
            "irfft2",
            "fftn",
            "ifftn",
            "rfftn",
            "irfftn",
            "hfft",
            "ihfft",
        ):
            monkeypatch.setattr(module, name, fail)
    monkeypatch.setattr(importlib.import_module("scipy.special"), "j0", fail)
    monkeypatch.setattr(importlib.import_module("scipy.special"), "roots_legendre", fail)
    monkeypatch.setattr(np.polynomial.legendre, "leggauss", fail)
    with unchanged_policy_and_random(
        data, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
    ):
        try:
            if operation == "build":
                result = operator.build_kernel_cache(**builder_fields(pupil_order=2))
            else:
                result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        except BaseException as error:
            assert entered
            assert error is sentinel  # Not merely an equal message or another ValueError.
        else:
            assert not entered, "A dependency sentinel was swallowed before a returned result"
            assert_dependency_bypass_result(result, operation, cache, data, options)


@pytest.mark.parametrize("operation", ["build", "forward", "adjoint"])
def test_public_calls_do_not_persist_work_files_in_caller_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    operation: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    if operation == "build":
        operator.build_kernel_cache(**builder_fields(source_shape_zyx=(1, 2, 2)))
    else:
        run(operation, operand(operation))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("operation", ["build", "forward", "adjoint"])
@pytest.mark.parametrize("warning_class", [UserWarning, RuntimeWarning])
def test_unrelated_dependency_warning_propagates_without_replacing_caller_policy(
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
    warning_class: type[Warning],
) -> None:
    sentinel = warning_class("unrelated public numerical dependency warning")
    entered = False
    cache, data, options = (
        make_cache(),
        operand("forward" if operation == "build" else operation),
        settings(),
    )

    def warn_then_call(original: Any) -> Any:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            nonlocal entered
            entered = True
            warnings.warn(sentinel, stacklevel=2)
            return original(*args, **kwargs)

        return wrapped

    for module_name in ("numpy.fft", "scipy.fft"):
        module = importlib.import_module(module_name)
        for name in (
            "fft",
            "ifft",
            "rfft",
            "irfft",
            "fft2",
            "ifft2",
            "rfft2",
            "irfft2",
            "fftn",
            "ifftn",
            "rfftn",
            "irfftn",
            "hfft",
            "ihfft",
        ):
            monkeypatch.setattr(module, name, warn_then_call(getattr(module, name)))
    special = importlib.import_module("scipy.special")
    for name in ("j0", "roots_legendre"):
        monkeypatch.setattr(special, name, warn_then_call(getattr(special, name)))
    monkeypatch.setattr(
        np.polynomial.legendre, "leggauss", warn_then_call(np.polynomial.legendre.leggauss)
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("error", warning_class)
        with unchanged_policy_and_random(
            data, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
        ):
            try:
                if operation == "build":
                    result = operator.build_kernel_cache(**builder_fields(pupil_order=2))
                else:
                    result = getattr(operator, operation)(data, kernel_cache=cache, **options)
            except BaseException as error:
                assert entered
                assert error is sentinel
            else:
                assert not entered, "An entered dependency warning did not follow caller policy"
                assert_dependency_bypass_result(result, operation, cache, data, options)
    # No required call, backend, warning count or production injection export.
    assert not caught


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_nonzero_target_below_float64_resolution_is_concrete_precision_range(
    operation: str,
) -> None:
    from decimal import localcontext

    from simulation_inverse_operator_fixture import decimal

    shape = (1, 2, 2)
    coefficient = np.finfo(np.float32).smallest_subnormal
    cache = operator.InverseKernelCache(
        **(
            cache_fields(shape)
            | {
                "lateral_spectra": np.full((1, 4, 3), coefficient, dtype=np.float32),
                "source_spacing_um_zyx": (1.0, 1e-160, 1e-164),
            }
        )
    )
    data_shape = shape if operation == "forward" else (1, 1, 1, 1)
    data = np.full(data_shape, coefficient, dtype=np.float32)
    with localcontext() as context:
        context.prec = 100
        exact = decimal(1e-160) * decimal(1e-164) * decimal(coefficient) ** 2
        if operation == "forward":
            exact *= 4
        assert 0 < exact < decimal(np.finfo(np.float64).smallest_subnormal) / 2
    options = settings(
        carrier_yx_per_um=np.zeros(2), phases_rad=np.zeros(1), beam_amplitudes=(1.0, 0.0, 0.0)
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, cache.lateral_spectra):
                assert_contract_error(
                    RANGE,
                    operation,
                    getattr(operator, operation),
                    data,
                    kernel_cache=cache,
                    field=f"{operation} output",
                    **options,
                )
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)


@pytest.mark.parametrize("shape", [(1, 2, 4), (2, 4, 2), (3, 2, 4), (2, 2, 4)])
@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_nonzero_payload_supported_only_on_unused_lags_has_exact_zero_finite_map(
    shape: Any,
    operation: str,
) -> None:
    # Analytic separability proves every required lag zero, hence exact G=0.
    # A floating inverse-DFT cancellation residue is never truth or a scale here.
    cache = operator.InverseKernelCache(
        **(
            cache_fields(shape)
            | {
                "lateral_spectra": null_support_spectra(shape),
            }
        )
    )
    data = operand(operation, shape)
    assert np.any(cache.lateral_spectra != 0) and np.any(data != 0)
    with unchanged_policy_and_random(data, cache.lateral_spectra):
        result = run(operation, data, cache)
    target_shape = (3, shape[0], shape[1] // 2, shape[2] // 2) if operation == "forward" else shape
    assert_storage(result, target_shape, np.float64)
    np.testing.assert_array_equal(result, np.zeros(target_shape, dtype=np.float64))


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
@pytest.mark.parametrize("byte_order", ["native", "non_native"])
def test_finite_uint64_phase_normalization_defines_observably_rounded_float64_problem(
    operation: str,
    byte_order: str,
) -> None:
    from decimal import Decimal

    from simulation_inverse_operator_fixture import decimal, reduced_cis

    # The original integer differs from the normalized phase by exactly one radian.
    dtype = np.dtype("u8").newbyteorder("S" if byte_order == "non_native" else "=")
    storage = np.array([2**63 + 1, 0], dtype=dtype)
    phases = storage[::2]
    phases.flags.writeable = False
    assert int(phases[0]) - int(float(phases[0])) == 1
    cache = make_cache()
    options = settings(
        carrier_yx_per_um=np.zeros(2), phases_rad=phases, beam_amplitudes=(1.0, 1.0, 0.0)
    )
    data = np.ones(SHAPE if operation == "forward" else (1, 3, 1, 2), dtype=np.float32)
    matrix, f_norm, j_norm = reference(cache, options)
    expected = apply_reference(matrix, data, transpose=operation == "adjoint")
    normalized_light = 1 + reduced_cis(decimal(phases[0])).real
    original_light = 1 + reduced_cis(Decimal(int(phases[0]))).real
    base = pixel_matrix(kernel_from_spectra(cache.lateral_spectra, SHAPE), SHAPE, SPACING)
    wrong = apply_reference(base * original_light, data, transpose=operation == "adjoint")
    scale = f_norm if operation == "forward" else j_norm
    np.testing.assert_allclose(matrix, base * normalized_light, atol=0, rtol=2e-15)
    assert float(np.max(np.abs(expected - wrong))) > 4 * (1e-4 + 5e-13) * scale
    with unchanged_policy_and_random(data, phases, cache.lateral_spectra):
        result = getattr(operator, operation)(data, kernel_cache=cache, **options)
    assert_fidelity(result, expected, scale)


@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_finite_longdouble_setting_underflow_on_normalization_remains_permitted(
    operation: str,
) -> None:
    # Extended longdouble can normalize to zero; on float64-width platforms this
    # remains a finite tiny positive. Both define the normalized float64 problem.
    tiny = np.finfo(np.longdouble).smallest_subnormal
    phases = np.array([tiny], dtype=np.longdouble)
    carrier = np.array([tiny, 0], dtype=np.longdouble)
    options = settings(phases_rad=phases, carrier_yx_per_um=carrier)
    cache, data = make_cache(), operand(operation, phases=1)
    matrix, f_norm, j_norm = reference(cache, options)
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(data, phases, carrier, cache.lateral_spectra):
                result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert_fidelity(
        result,
        apply_reference(matrix, data, transpose=operation == "adjoint"),
        (f_norm if operation == "forward" else j_norm) * float(np.max(np.abs(data))),
    )


# Retained postimplementation supplements. This new A starts from a null
# checkpoint; no historical acceptance or test-first claim is promoted here.
@pytest.mark.parametrize("operation", ["forward", "adjoint"])
def test_supplemental_representable_float64_subnormal_outputs_succeed(operation: str) -> None:
    from fractions import Fraction

    shape = (1, 2, 2)
    step = math.ldexp(1.0, -520)
    cache = operator.InverseKernelCache(
        **(
            cache_fields(shape)
            | {
                "lateral_spectra": np.ones((1, 4, 3), dtype=np.float32),
                "source_spacing_um_zyx": (1.0, step, step),
            }
        )
    )
    data_shape = shape if operation == "forward" else (1, 1, 1, 1)
    data = np.ones(data_shape, dtype=np.float32)
    options = settings(
        carrier_yx_per_um=np.zeros(2), phases_rad=np.zeros(1), beam_amplitudes=(1.0, 0.0, 0.0)
    )
    # Constant half-spectrum 1 is a unit lateral delta. Each source belongs
    # to this pixel: forward sums four areas; the real adjoint deposits one.
    exponent = -1038 if operation == "forward" else -1040
    exact = Fraction(1, 2 ** (-exponent))
    expected = math.ldexp(1.0, exponent)
    assert Fraction.from_float(expected) == exact
    assert 0 < expected < sys.float_info.min
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random(
                data, cache.lateral_spectra, options["carrier_yx_per_um"], options["phases_rad"]
            ):
                result = getattr(operator, operation)(data, kernel_cache=cache, **options)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    target_shape = (1, 1, 1, 1) if operation == "forward" else shape
    assert_storage(result, target_shape, np.float64)
    assert not np.shares_memory(result, data)
    assert not np.shares_memory(result, cache.lateral_spectra)
    # Exact rational comparison avoids underflow/rounding in 1e-4*subnormal.
    # Here the contract scale equals the positive target for both directions.
    for value in result.ravel():
        assert abs(Fraction.from_float(float(value)) - exact) <= exact / 10000


@pytest.mark.parametrize("emission", [1e200, 1e-200])
def test_supplemental_builder_peak_outside_float64_has_proven_cache_obstruction(
    emission: float,
) -> None:
    # Q1 on-axis peak is pi/emission**2. For the 4x4 lateral transform,
    # exact float32-cache inverse values lie on 2**-153 multiples and have
    # magnitude <= float32 max. The independent proof is retained with this
    # supplement: neither the ~1e-400 nor the ~1e400 peak can meet the budget.
    arguments = builder_fields(
        source_shape_zyx=(1, 2, 2),
        source_spacing_um_zyx=(1.0, 0.125, 0.25),
        emission_um=emission,
        refractive_index=1.0,
        detection_na=1.0,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                assert_contract_error(
                    RANGE,
                    "build",
                    operator.build_kernel_cache,
                    field="lateral_spectra / emission_um",
                    **arguments,
                )
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)


@pytest.mark.parametrize("na_exponent", [-64, -68])
def test_supplemental_physical_cache_near_float32_lower_range_meets_both_budgets(
    na_exponent: int,
) -> None:
    shape, spacing = (3, 2, 4), (0.375, 0.125, 0.25)
    na = math.ldexp(1.0, na_exponent)
    arguments = builder_fields(
        source_shape_zyx=shape,
        source_spacing_um_zyx=spacing,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=na,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                cache = operator.build_kernel_cache(**arguments)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert isinstance(cache, operator.InverseKernelCache)
    assert_storage(cache.lateral_spectra, (3, 4, 5), np.float32)
    for field, expected in arguments.items():
        assert getattr(cache, field) == expected
    np.testing.assert_array_equal(cache.lateral_spectra, cache.lateral_spectra[:, [0, 3, 2, 1], :])
    # Division by this exact binary power is exact on these float32 values.
    # Compare H_C/NA**2 with H_Q/NA**2; E and B norms scale identically.
    scale = math.ldexp(1.0, 2 * na_exponent)
    represented = kernel_from_spectra(cache.lateral_spectra.astype(np.float64) / scale, shape)
    physical = physical_kernel(shape, spacing, 1.0, 1.0, na, 1) / scale
    errors = row_column_norms(pixel_matrix(represented - physical, shape, spacing, absolute=True))
    norms = row_column_norms(pixel_matrix(physical, shape, spacing))
    assert min(norms) > 0
    for error, norm in zip(errors, norms, strict=True):
        assert error <= (1e-4 + 5e-13) * norm


def supplemental_axial_delta_reference(
    source: Any,
    residual: Any,
    spacing: tuple[float, float, float],
    weights: Any,
    carrier: Any,
    phases: Any,
    amplitudes: tuple[float, float, float],
    excitation: float,
    index: float,
) -> tuple[Any, Any, float, float]:
    """Sum finite axial lags, integrate pixels and independently lift real residuals.

    The represented spectrum is constant laterally, hence has an exact lateral
    delta. Only same-site lateral interactions survive. This observer allocates
    two output volumes and uses scalar sums; it never forms an optical matrix.
    """
    nz, ny, nx = source.shape
    dz, dy, dx = spacing
    area = dy * dx
    qy, qx = map(float, carrier)
    k0 = index / excitation
    q2 = math.fsum((qy * qy, qx * qx))
    kappa = q2 / (k0 + math.sqrt(k0 * k0 - q2))
    a0, plus, minus = amplitudes
    beam_norm = math.fsum(a * a for a in amplitudes)

    def light(p: int, focus: int, jz: int, y: int, x: int) -> float:
        theta = 2 * math.pi * math.fsum((qy * (y + 0.5) * dy, qx * (x + 0.5) * dx))
        lateral = theta + float(phases[p])
        axial = 2 * math.pi * kappa * (jz - focus) * dz
        field = a0 + plus * complex(math.cos(lateral - axial), math.sin(lateral - axial))
        field += minus * complex(math.cos(-lateral - axial), math.sin(-lateral - axial))
        return abs(field) ** 2 / beam_norm

    forward_values = np.empty(residual.shape, dtype=np.float64)
    for p, focus, py, px in np.ndindex(residual.shape):
        points = []
        for sy in range(2):
            for sx in range(2):
                y, x = 2 * py + sy, 2 * px + sx
                points.append(
                    math.fsum(
                        float(weights[abs(focus - jz)])
                        * light(p, focus, jz, y, x)
                        * float(source[jz, y, x])
                        for jz in range(nz)
                    )
                )
        forward_values[p, focus, py, px] = area * math.fsum(points)
    adjoint_values = np.empty(source.shape, dtype=np.float64)
    for jz, y, x in np.ndindex(source.shape):
        # Repeated-pixel deposit: every fine site receives its enclosing pixel
        # residual once per focus and phase, times ONE area, before axial summation.
        adjoint_values[jz, y, x] = area * math.fsum(
            float(weights[abs(focus - jz)])
            * light(p, focus, jz, y, x)
            * float(residual[p, focus, y // 2, x // 2])
            for p in range(len(phases))
            for focus in range(nz)
        )
    axial_norm = max(
        math.fsum(abs(float(weights[abs(focus - jz)])) for jz in range(nz)) for focus in range(nz)
    )
    return forward_values, adjoint_values, 4 * area * axial_norm, area * axial_norm


def test_supplemental_moderate_nonsquare_signed_axial_delta_composition() -> None:
    shape, spacing = (3, 32, 64), (0.19, 0.08, 0.11)
    weights = np.array([0.75, -0.5, 0.125], dtype=np.float32)
    payload = np.empty((3, 64, 65), dtype=np.float32)
    for lag in range(3):
        payload[lag] = weights[lag]
    fields = cache_fields(shape) | {"source_spacing_um_zyx": spacing}
    z, y, x = np.indices(shape)
    source = ((7 * z + 3 * y - 5 * x) % 29 - 14).astype(np.float32) / np.float32(8)
    source[0, 0, 0], source[-1, -1, -1], source[1, 16, 31] = 1.75, -2.5, 3.125
    p, z, y, x = np.indices((3, 3, 16, 32))
    residual = ((11 * p - 5 * z + 7 * y + 3 * x) % 37 - 18).astype(np.float32) / np.float32(16)
    residual[0, 0, 0, 0], residual[-1, -1, -1, -1] = 1.875, -2.25
    options = settings()
    expected_forward, expected_adjoint, cr, cc = supplemental_axial_delta_reference(
        source,
        residual,
        spacing,
        weights,
        options["carrier_yx_per_um"],
        options["phases_rad"],
        options["beam_amplitudes"],
        options["excitation_um"],
        fields["refractive_index"],
    )
    expected_forward.flags.writeable = expected_adjoint.flags.writeable = False
    for operation in ("forward", "adjoint"):
        call_source, call_residual, call_payload = source.copy(), residual.copy(), payload.copy()
        cache = operator.InverseKernelCache(**(fields | {"lateral_spectra": call_payload}))
        options = settings()
        data = call_source if operation == "forward" else call_residual
        expected = expected_forward if operation == "forward" else expected_adjoint
        scale = light_bound(options["beam_amplitudes"]) * (cr if operation == "forward" else 3 * cc)
        scale *= float(np.max(np.abs(data)))
        old_policy = np.seterr(all="raise")
        try:
            with observe_arithmetic_ownership() as caught:
                warnings.simplefilter("always")
                with unchanged_policy_and_random(
                    call_source,
                    call_residual,
                    call_payload,
                    options["carrier_yx_per_um"],
                    options["phases_rad"],
                ):
                    result = getattr(operator, operation)(data, kernel_cache=cache, **options)
            assert_arithmetic_ownership_resolved(caught)
        finally:
            np.seterr(**old_policy)
        assert_storage(result, expected.shape, np.float64)
        assert not np.shares_memory(result, data) and not np.shares_memory(result, call_payload)
        assert_fidelity(result, expected, scale)


def test_supplemental_physical_cache_feasible_near_float32_quantization_limit() -> None:
    # Retained positive: a DC-only witness has required value round(32*peak)/32
    # in float32. Oracle qualification below proves its margin independently.
    # Neither that payload nor its nonzero unused lags are required results.
    shape, spacing = (3, 2, 4), (0.375, 0.125, 0.25)
    na = math.ldexp(1.0, -71)
    arguments = builder_fields(
        source_shape_zyx=shape,
        source_spacing_um_zyx=spacing,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=na,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                cache = operator.build_kernel_cache(**arguments)
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert isinstance(cache, operator.InverseKernelCache)
    assert_storage(cache.lateral_spectra, (3, 4, 5), np.float32)
    for field, expected in arguments.items():
        assert getattr(cache, field) == expected
    np.testing.assert_array_equal(cache.lateral_spectra, cache.lateral_spectra[:, [0, 3, 2, 1], :])
    # Exact binary rescaling keeps the observer normal, and rescales E/B equally.
    # Absolute POINT errors precede the four-sample pixel sum. Unused Ny/Nx
    # inverse-lag values are never queried or constrained by this comparison.
    scale = math.ldexp(1.0, -142)
    represented = kernel_from_spectra(cache.lateral_spectra.astype(np.float64) / scale, shape)
    physical = physical_kernel(shape, spacing, 1.0, 1.0, na, 1) / scale
    errors = row_column_norms(pixel_matrix(represented - physical, shape, spacing, absolute=True))
    norms = row_column_norms(pixel_matrix(physical, shape, spacing))
    assert min(norms) > 0
    for error, norm in zip(errors, norms, strict=True):
        assert error <= (1e-4 + 5e-13) * norm, (error, norm)


@pytest.mark.parametrize("nominal_peak_quanta", [1500.49, 402.123])
def test_supplemental_multi_axial_near_quantum_physical_cache_fidelity(
    nominal_peak_quanta: float,
) -> None:
    # Nominal peak only selects a binary64 NA; physical truth uses that actual
    # represented NA. Independent DC feasibility does not prescribe any payload.
    shape, spacing = (2, 2, 2), (0.375, 0.125, 0.25)
    na = math.sqrt(nominal_peak_quanta / math.pi) * math.ldexp(1.0, -74) * math.sqrt(0.5)
    arguments = builder_fields(
        source_shape_zyx=shape,
        source_spacing_um_zyx=spacing,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=na,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                try:
                    cache = operator.build_kernel_cache(**arguments)
                except SimreconError as error:
                    print(
                        "UNEXPECTED_PUBLIC_BUILDER_REFUSAL",
                        nominal_peak_quanta,
                        na.hex(),
                        error.code,
                        error.message,
                    )
                    raise
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert isinstance(cache, operator.InverseKernelCache)
    assert_storage(cache.lateral_spectra, (2, 4, 3), np.float32)
    for field, expected in arguments.items():
        assert getattr(cache, field) == expected
    np.testing.assert_array_equal(cache.lateral_spectra, cache.lateral_spectra[:, [0, 3, 2, 1], :])
    # Scale by delta=2**-149 before the DFT and E comparison. This rescales both
    # budgets equally and avoids observer underflow. Unused lags are unconstrained.
    scale = math.ldexp(1.0, -149)
    represented = kernel_from_spectra(cache.lateral_spectra.astype(np.float64) / scale, shape)
    physical = physical_kernel(shape, spacing, 1.0, 1.0, na, 1) / scale
    errors = row_column_norms(pixel_matrix(represented - physical, shape, spacing, absolute=True))
    norms = row_column_norms(pixel_matrix(physical, shape, spacing))
    assert min(norms) > 0
    for error, norm in zip(errors, norms, strict=True):
        assert error <= (1e-4 + 5e-13) * norm, (nominal_peak_quanta, na.hex(), error, norm)


def test_supplemental_finite_quantum_cache_feasible_with_actual_rounding_margin() -> None:
    # Retained positive. The generic delta/32 rounding bound is too loose here;
    # oracle qualification uses the actual metadata and its faithful DC witness.
    # That independent witness is NOT a required builder payload or strategy.
    shape, spacing = (2, 2, 2), (0.375, 0.125, 0.25)
    na = math.sqrt(300.49 / math.pi) * math.ldexp(1.0, -74) * math.sqrt(0.5)
    arguments = builder_fields(
        source_shape_zyx=shape,
        source_spacing_um_zyx=spacing,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=na,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                try:
                    cache = operator.build_kernel_cache(**arguments)
                except SimreconError as error:
                    print("UNEXPECTED_FINITE_QUANTUM_REFUSAL", na.hex(), error.code, error.message)
                    raise
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
    assert isinstance(cache, operator.InverseKernelCache)
    assert_storage(cache.lateral_spectra, (2, 4, 3), np.float32)
    for field, expected in arguments.items():
        assert getattr(cache, field) == expected
    np.testing.assert_array_equal(cache.lateral_spectra, cache.lateral_spectra[:, [0, 3, 2, 1], :])
    # Scale BOTH sides by delta before inverse DFT and pointwise absolute error.
    # No absolute floor or constraint on unused spatial lags is introduced.
    scale = math.ldexp(1.0, -149)
    represented = kernel_from_spectra(cache.lateral_spectra.astype(np.float64) / scale, shape)
    physical = physical_kernel(shape, spacing, 1.0, 1.0, na, 1) / scale
    errors = row_column_norms(pixel_matrix(represented - physical, shape, spacing, absolute=True))
    norms = row_column_norms(pixel_matrix(physical, shape, spacing))
    assert min(norms) > 0
    for error, norm in zip(errors, norms, strict=True):
        assert error <= (1e-4 + 5e-13) * norm, (na.hex(), error, norm)


def test_supplemental_finite_normal_pupil_peak_below_cache_precision_lattice() -> None:
    # The physical peak is NORMAL binary64, not an underflow obstruction.
    # Every exact real 4x4 inverse-DFT sample lies in (2**-149/16)*Z.
    # All required lags reach a retained pixel. Nonzero samples violate the row
    # budget; all-zero required samples give E=B. No float32 payload can qualify.
    na = math.sqrt(1e-10 / math.pi) * math.ldexp(1.0, -74) * math.sqrt(0.5)
    arguments = builder_fields(
        source_shape_zyx=(2, 2, 2),
        source_spacing_um_zyx=(0.375, 0.125, 0.25),
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=na,
        pupil_order=1,
    )
    old_policy = np.seterr(all="raise")
    try:
        with observe_arithmetic_ownership() as caught:
            warnings.simplefilter("always")
            with unchanged_policy_and_random():
                assert_contract_error(
                    RANGE,
                    "build_kernel_cache",
                    operator.build_kernel_cache,
                    field="lateral_spectra physical-cache precision",
                    **arguments,
                )
        assert_arithmetic_ownership_resolved(caught)
    finally:
        np.seterr(**old_policy)
