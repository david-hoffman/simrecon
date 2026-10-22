"""Blind A01 public-contract tests for Cartesian empirical transfer interpolation."""

from __future__ import annotations

import math
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
from typing import Any

import numpy as np
import pytest

import simrecon as sr
from empirical_trilinear_fixture import (
    EPS,
    FMAX,
    FREQUENCY_FIELDS,
    PRECISION,
    QUANTUM,
    affine_value,
    assert_budget,
    asymmetric_values,
    coordinates,
    decimal,
    direct_dft,
    frequency_arrays,
    multiply,
    oracle,
    phase_images,
    phasor,
    pi,
    sampled_affine,
    signed_estimator,
    smooth_samples,
    specimen_example,
    stencil,
)


def public_export(name: str) -> Any:
    return getattr(sr, name)


@pytest.fixture(scope="session")
def api() -> Any:
    # Missing new API is a baseline capability gap, never a skip or product-red.
    return public_export("adapt_empirical_volume_response_trilinear")


def response(
    shape: tuple[int, ...] = (3, 4, 5),
    spacing: Any = (0.5, 0.75, 1.25),
    *,
    values: Any = None,
    origin: Any = (1, 2, 3),
) -> Any:
    axes = frequency_arrays(shape, spacing)
    return sr.EmpiricalVolumeResponse(
        values=asymmetric_values(shape) if values is None else values,
        fz_per_um=axes[0],
        fy_per_um=axes[1],
        fx_per_um=axes[2],
        voxel_size_um=spacing,
        origin_zyx=origin,
    )


def declarations(**updates: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "target_shape_zyx": (3, 3, 3),
        "target_voxel_size_um": (1.0, 1.5, 2.5),
        "calibration_carrier_bins": (2, -5),
        "specimen_carrier_bins": (3, -6),
        "coordinate_offset_yx": (-1, 4),
        "phase_reference_shift_rad": 0.375,
        "source": "  calibration / specimen: caller declaration\n",
    }
    result.update(updates)
    return result


def identity(**updates: Any) -> dict[str, Any]:
    return declarations(
        **{
            "calibration_carrier_bins": (0, 0),
            "specimen_carrier_bins": (0, 0),
            "coordinate_offset_yx": (0, 0),
            "phase_reference_shift_rad": 0.0,
            **updates,
        }
    )


def changed(record: Any, **updates: Any) -> Any:
    fields = response_fields(record)
    fields.update(updates)
    return sr.EmpiricalVolumeResponse(**fields)


def response_fields(record: Any) -> dict[str, Any]:
    return {
        name: getattr(record, name)
        for name in ("values", *FREQUENCY_FIELDS, "voxel_size_um", "origin_zyx")
    }


def expect_code(api: Any, record: Any, code: str, kwargs: Any = None) -> None:
    with pytest.raises(sr.SimreconError) as caught:
        api(record, **(identity() if kwargs is None else kwargs))
    assert caught.value.code == code


def arrays(record: Any) -> list[Any]:
    return [record.values, *(getattr(record, field) for field in FREQUENCY_FIELDS)]


def assert_input_unchanged(record: Any, before: Any) -> None:
    for array, (contents, strides, writable, dtype) in zip(arrays(record), before, strict=True):
        assert array.tobytes() == contents
        assert array.strides == strides
        assert array.flags.writeable == writable
        assert array.dtype == dtype


def snapshot(record: Any) -> Any:
    return [(a.tobytes(), a.strides, a.flags.writeable, a.dtype) for a in arrays(record)]


def test_oracle_self_geometry_and_exact_tensor_cancellation() -> None:
    assert stencil([Fraction(-1), Fraction(0), Fraction(1)], Fraction(1, 4)) == [
        (1, Fraction(3, 4)),
        (2, Fraction(1, 4)),
    ]
    record = response((3, 3, 3), (1.0, 1.0, 1.0), origin=(0, 0, 0))
    record.values[:] = 0
    record.values[0, 1:, 1:, 1:] = np.array(
        [[[1, -1], [-1, 1]], [[-1, 1], [1, -1]]], dtype=np.complex128
    )
    expected = oracle(record, identity(target_voxel_size_um=(2.0, 2.0, 2.0)))
    assert expected[(0, 2, 2, 2)][:2] == (Decimal(0), Decimal(0))
    assert expected[(0, 2, 2, 2)][2] > 0
    assert coordinates(3, 0.1)[2] == Fraction(1, 3) / Fraction.from_float(0.1)


def test_oracle_self_pi_roots_and_huge_angle_reduction() -> None:
    with localcontext() as context:
        context.prec = PRECISION
        assert str(pi()).startswith("3.14159265358979323846264338327950288419716939937510")
        c, s = phasor(Fraction(1, 4))
        assert abs(c) < Decimal("1e-790")
        assert abs(s - 1) < Decimal("1e-790")
        c, s = phasor(angle=float(np.finfo(np.float64).max))
        # Independent binary64 libm cross-check; product is never consulted.
        assert abs(c - Decimal.from_float(math.cos(float(np.finfo(np.float64).max)))) < Decimal(
            "2e-16"
        )
        assert abs(s - Decimal.from_float(math.sin(float(np.finfo(np.float64).max)))) < Decimal(
            "2e-16"
        )
        assert abs(c * c + s * s - 1) < Decimal("1e-790")
        second = multiply((c, s), (c, s))
        assert abs(second[0] ** 2 + second[1] ** 2 - 1) < Decimal("1e-790")


def test_oracle_self_direct_sum_roundtrip_and_multiaffine() -> None:
    stored = np.array([[[1 + 2j, -3 + 4j, 5 - 6j]]], dtype=np.complex128)
    coefficients = direct_dft(stored) / stored.size
    np.testing.assert_allclose(direct_dft(coefficients, inverse=True), stored, rtol=0, atol=2e-15)
    record = response(
        (3, 3, 3), (1.0, 1.0, 1.0), values=sampled_affine((3, 3, 3), (1.0,) * 3), origin=(0, 0, 0)
    )
    expected = oracle(record, identity(target_voxel_size_um=(2.0,) * 3))
    # The stored samples are rounded; account for <=1 ulp of source conversion.
    for m, z, y, x in np.ndindex((3, 3, 3, 3)):
        target = affine_value(m, *[coordinates(3, 2.0)[i] for i in (z, y, x)])
        re, im, _ = expected[(m, z, y, x)]
        assert abs(complex(float(re), float(im)) - target) < 2e-16


def test_public_binding_exports_and_direct_record(api: Any) -> None:
    wrapper = public_export("TrilinearVolumeTransfer")
    marker = object()
    constructed = wrapper(orders=marker, provenance={"opaque": 1})
    assert constructed.orders is marker
    assert constructed.provenance == {"opaque": 1}
    constructed.provenance["opaque"] = 2
    assert constructed.provenance == {"opaque": 2}
    for name in ("orders", "provenance"):
        with pytest.raises((AttributeError, TypeError)):
            setattr(constructed, name, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(constructed, name)
    record = response()
    kwargs = declarations()
    for key in kwargs:
        remaining = dict(kwargs)
        del remaining[key]
        with pytest.raises(TypeError):
            api(record, **remaining)
    with pytest.raises(TypeError):
        api(record, kwargs["target_shape_zyx"], **kwargs)
    with pytest.raises(TypeError):
        api(record, **kwargs, unexpected=True)
    with pytest.raises(TypeError):
        api(**kwargs)


def test_asymmetric_full_cartesian_interpolation_and_gauge(api: Any) -> None:
    record = response()
    kwargs = declarations()
    actual = api(record, **kwargs)
    assert isinstance(actual, public_export("TrilinearVolumeTransfer"))
    assert isinstance(actual.orders, sr.VolumeOrderOtf)
    assert actual.orders.values.shape == (3, 3, 3, 3)
    assert_budget(actual.orders.values, oracle(record, kwargs))
    assert actual.orders.origin_zyx == (0, 0, 0)
    assert actual.orders.voxel_size_um == kwargs["target_voxel_size_um"]
    assert actual.orders.source == kwargs["source"]
    assert np.any(actual.orders.values.real < 0)
    assert np.any(actual.orders.values.imag != 0)


def test_multiaffine_exactness_and_separate_smooth_approximation(api: Any) -> None:
    shape = (3, 5, 5)
    spacing = (0.5, 0.25, 0.5)
    record = response(shape, spacing, values=sampled_affine(shape, spacing), origin=(0, 0, 0))
    kwargs = identity(target_voxel_size_um=(1.0, 1.25, 2.5))
    actual = api(record, **kwargs)
    expected_affine = oracle(record, kwargs)
    assert_budget(actual.orders.values, expected_affine)
    source_rounding = max(
        math.ulp(float(v.real)) + math.ulp(float(v.imag)) for v in record.values.flat
    )
    for m, z, y, x in np.ndindex(actual.orders.values.shape):
        point = [
            coordinates(3, d)[i]
            for d, i in zip(kwargs["target_voxel_size_um"], (z, y, x), strict=True)
        ]
        truth = affine_value(m, *point)
        allowance = float(expected_affine[(m, z, y, x)][2])
        allowance += source_rounding + math.ulp(truth.real) + math.ulp(truth.imag)
        assert abs(actual.orders.values[m, z, y, x] - truth) <= allowance
    # H=(1+i)*(z^2+2y^2+3x^2)/16. The sum of h_a^2 sup|H_aa|/8
    # bounds its interpolation error, independently of the arithmetic budget.
    axes = [coordinates(n, d) for n, d in zip(shape, spacing, strict=True)]
    smooth = np.empty((3, *shape), dtype=np.complex128)
    for m, z, y, x in np.ndindex(smooth.shape):
        v = (axes[0][z] ** 2 + 2 * axes[1][y] ** 2 + 3 * axes[2][x] ** 2) / 16
        smooth[m, z, y, x] = complex(float(v), float(v))
    record = changed(record, values=smooth)
    expected = oracle(record, kwargs)
    actual = api(record, **kwargs).orders.values
    assert_budget(actual, expected)
    approximation_errors = []
    h2 = [
        float(Fraction(1, n) / Fraction.from_float(d)) ** 2
        for n, d in zip(shape, spacing, strict=True)
    ]
    approximation_bound = (
        math.sqrt(2) * sum(c * h for c, h in zip((2 / 16, 4 / 16, 6 / 16), h2, strict=True)) / 8
    )
    for index, (re, im, _) in expected.items():
        _, z, y, x = index
        point = [
            coordinates(3, d)[i]
            for d, i in zip(kwargs["target_voxel_size_um"], (z, y, x), strict=True)
        ]
        truth = complex(1, 1) * float((point[0] ** 2 + 2 * point[1] ** 2 + 3 * point[2] ** 2) / 16)
        approximation_errors.append(abs(complex(float(re), float(im)) - truth))
    assert 0 < max(approximation_errors) <= approximation_bound


def test_tolerated_frequency_metadata_never_controls_weights_nodes_or_output(api: Any) -> None:
    record = response((3, 3, 3), (0.1, 0.3, 0.7), origin=(0, 0, 0))
    perturbed = []
    for a in arrays(record)[1:]:
        b = a.copy()
        b[len(b) // 2] = -0.0
        for _ in range(4):
            b[0] = np.nextafter(b[0], -np.inf)
            b[-1] = np.nextafter(b[-1], np.inf)
        perturbed.append(b)
    record = changed(record, **dict(zip(FREQUENCY_FIELDS, perturbed, strict=True)))
    kwargs = identity(target_voxel_size_um=record.voxel_size_um)
    actual = api(record, **kwargs).orders
    assert actual.values.tobytes() == record.values.tobytes()
    for got, wanted in zip(
        arrays(actual)[1:], frequency_arrays((3, 3, 3), record.voxel_size_um), strict=True
    ):
        assert got.tobytes() == wanted.tobytes()
    kwargs = identity(target_voxel_size_um=(0.2, 0.6, 1.4))
    assert_budget(api(record, **kwargs).orders.values, oracle(record, kwargs))


@pytest.mark.parametrize(
    "source_shape,target_shape",
    [((3, 3, 3), (3, 3, 3)), ((1, 3, 5), (1, 3, 5)), ((6, 6, 6), (3, 3, 3))],
)
@pytest.mark.parametrize("negative_zero", [False, True])
def test_closed_nodes_singletons_even_source_and_bit_copy(
    api: Any, source_shape: Any, target_shape: Any, negative_zero: bool
) -> None:
    record = response(source_shape, (1.0,) * 3, origin=(0, 0, 0))
    record.values.real.flat[0] = -0.0
    record.values.imag.flat[1] = -0.0
    record.values[2, ...] = complex(float(np.finfo(float).max), float(np.finfo(float).max))
    target_spacing = tuple(Fraction(n, s) for n, s in zip(source_shape, target_shape, strict=True))
    kwargs = identity(
        target_shape_zyx=target_shape,
        target_voxel_size_um=tuple(float(d) for d in target_spacing),
        phase_reference_shift_rad=-0.0 if negative_zero else 0.0,
    )
    actual = api(record, **kwargs).orders.values
    for out_index in np.ndindex(target_shape):
        source_index = tuple(
            i - t // 2 + n // 2
            for i, t, n in zip(out_index, target_shape, source_shape, strict=True)
        )
        assert (
            actual[(slice(None), *out_index)].tobytes()
            == record.values[(slice(None), *source_index)].tobytes()
        )


def test_order_zero_node_copy_with_nonidentity_side_rotation(api: Any) -> None:
    record = response((3, 3, 3), (1.0,) * 3, origin=(0, 1, 2))
    record.values[0] = complex(float(np.finfo(float).max), float(np.finfo(float).max))
    kwargs = identity(target_voxel_size_um=(1.0,) * 3, phase_reference_shift_rad=0.7)
    actual = api(record, **kwargs)
    assert actual.orders.values[0].tobytes() == record.values[0].tobytes()
    # F0 is exempt from sufficient-success inequality at this exact boundary.
    assert_budget(actual.orders.values, oracle(record, kwargs), sufficient=False)


def test_integral_nonzero_huge_carrier_identity_copies_all_component_bits(api: Any) -> None:
    record = response((3, 3, 3), (1.0,) * 3, origin=(0, 1, 2))
    record.values.real.flat[0] = -0.0
    record.values.imag.flat[1] = -0.0
    record.values[2] = complex(float(np.finfo(float).max), float(np.finfo(float).max))
    carrier = (3 * (2**300 + 1), -3 * (2**400 + 7))
    kwargs = identity(
        target_voxel_size_um=(1.0,) * 3,
        calibration_carrier_bins=carrier,
        specimen_carrier_bins=carrier,
        coordinate_offset_yx=(2**500 + 1, -(2**600)),
        phase_reference_shift_rad=-0.0,
    )
    assert api(record, **kwargs).orders.values.tobytes() == record.values.tobytes()


@pytest.mark.parametrize("spacing", [0.1, 0.7, 0.17, 1e-100, 1e100])
def test_target_frequency_components_are_correctly_rounded_exact_rationals(
    api: Any, spacing: float
) -> None:
    record = response((3, 3, 3), (spacing,) * 3, origin=(0, 0, 0))
    kwargs = identity(target_voxel_size_um=(spacing,) * 3)
    result = api(record, **kwargs).orders
    for actual, expected in zip(
        arrays(result)[1:], frequency_arrays((3, 3, 3), (spacing,) * 3), strict=True
    ):
        assert actual.tobytes() == expected.tobytes()


def test_subnormal_source_coordinate_allowance_includes_quantum(api: Any) -> None:
    spacing = float(np.finfo(float).max)
    record = response((3, 3, 3), (spacing,) * 3, origin=(0, 0, 0))
    vector = record.fx_per_um.copy()
    vector[0] = np.nextafter(vector[0], -np.inf)
    exact = coordinates(3, spacing)[0]
    tolerance = 8 * EPS * abs(exact) + QUANTUM
    assert abs(Fraction.from_float(float(vector[0])) - exact) <= tolerance
    record = changed(record, fx_per_um=vector)
    kwargs = identity(target_voxel_size_um=(spacing,) * 3)
    assert api(record, **kwargs).orders.values.tobytes() == record.values.tobytes()
    for _ in range(4):
        vector[0] = np.nextafter(vector[0], -np.inf)
    assert abs(Fraction.from_float(float(vector[0])) - exact) > tolerance
    expect_code(api, record, "invalid_empirical_transfer_response", kwargs)


@pytest.mark.parametrize("shape", [(2, 3, 3), (3, 4, 3), (3, 3, 2)])
def test_even_target_rejects_without_zero_support_bypass(api: Any, shape: Any) -> None:
    record = response()
    record.values[:] = 0
    expect_code(
        api,
        record,
        "unsupported_empirical_interpolation_target_nyquist",
        identity(target_shape_zyx=shape),
    )


@pytest.mark.parametrize("axis", [0, 1, 2])
def test_strict_closed_hull_and_singleton_coverage(api: Any, axis: int) -> None:
    record = response((3, 3, 3), (1.0,) * 3, origin=(0, 0, 0))
    record.values[:] = 0
    spacing = [1.0, 1.0, 1.0]
    spacing[axis] = np.nextafter(1.0, 0.0)
    expect_code(
        api,
        record,
        "incomplete_empirical_transfer_coverage",
        identity(target_voxel_size_um=spacing),
    )
    shape = [3, 3, 3]
    shape[axis] = 1
    singleton = response(tuple(shape), (1.0,) * 3, origin=(0, 0, 0))
    expect_code(api, singleton, "incomplete_empirical_transfer_coverage", identity())
    kwargs = identity(
        target_shape_zyx=shape, target_voxel_size_um=(float(np.finfo(float).max),) * 3
    )
    assert_budget(api(singleton, **kwargs).orders.values, oracle(singleton, kwargs))


@pytest.mark.parametrize("which", ["calibration_carrier_bins", "specimen_carrier_bins"])
@pytest.mark.parametrize("axis", [0, 1])
def test_carrier_equality_is_exact_and_nonwrapping(api: Any, which: str, axis: int) -> None:
    kwargs = declarations()
    values = list(kwargs[which])
    values[axis] += 1
    kwargs[which] = values
    expect_code(api, response(), "mismatched_empirical_transfer_carrier", kwargs)
    # Equal rounded ratios are not equal physical rationals.
    huge = 2**200
    kwargs = identity(
        calibration_carrier_bins=(huge, 0),
        specimen_carrier_bins=(huge + 1, 0),
        target_voxel_size_um=(0.5, 1.0, 1.25),
    )
    expect_code(api, response(), "mismatched_empirical_transfer_carrier", kwargs)


@pytest.mark.parametrize("carrier", [0, -(2**300 + 7), 2**300 + 11, np.uint64(2**64 - 1)])
def test_huge_exact_carriers_offsets_and_reduced_gauge(api: Any, carrier: Any) -> None:
    record = response((3, 3, 3), (1.0,) * 3, origin=(2, 1, 2))
    kwargs = identity(
        target_voxel_size_um=(2.0,) * 3,
        calibration_carrier_bins=[carrier, -int(carrier)],
        specimen_carrier_bins=[2 * int(carrier), -2 * int(carrier)],
        coordinate_offset_yx=[2**400 + 1, -(2**400) + 4],
        phase_reference_shift_rad=-0.3,
    )
    actual = api(record, **kwargs)
    assert_budget(actual.orders.values, oracle(record, kwargs))
    assert actual.provenance["calibration_carrier_bins"] == (int(carrier), -int(carrier))
    assert all(type(k) is int for k in actual.provenance["coordinate_offset_yx"])


def test_storage_roll_offset_equivalence_and_physical_bead_phase(api: Any) -> None:
    record = response((3, 5, 5), (1.0,) * 3, origin=(0, 1, 2))
    kwargs = identity(
        target_voxel_size_um=(2.0, 2.5, 2.5),
        calibration_carrier_bins=(2, -2),
        specimen_carrier_bins=(3, -3),
        coordinate_offset_yx=(4, -3),
        phase_reference_shift_rad=0.4,
    )
    expected = oracle(record, kwargs)
    assert_budget(api(record, **kwargs).orders.values, expected)
    # A joint storage roll leaves the centered E unchanged and changes observed origin.
    rolled = changed(record, origin_zyx=(0, 2, 1))
    rolled_kwargs = {**kwargs, "coordinate_offset_yx": (3, -2)}
    assert_budget(api(rolled, **rolled_kwargs).orders.values, expected)
    moved_values = record.values.copy()
    with localcontext() as context:
        context.prec = PRECISION
        for m in (1, 2):
            c, s = phasor(Fraction(m * 4, 5))  # kc dot physical displacement (1,-1).
            moved_values[m] *= complex(float(c), float(s))
    moved = changed(rolled, values=moved_values)
    actual = api(moved, **kwargs).orders.values
    moved_expected = oracle(moved, kwargs)
    assert_budget(actual, moved_expected)
    rounding_bound = 16 * float(EPS) * float(np.max(abs(record.values)))
    for index, (re, im, _) in expected.items():
        moved_re, moved_im, _ = moved_expected[index]
        assert abs(complex(float(moved_re - re), float(moved_im - im))) <= rounding_bound
    uncompensated = api(rolled, **kwargs).orders.values
    assert_budget(uncompensated, oracle(rolled, kwargs))
    assert (
        max(
            abs(uncompensated[index] - complex(float(re), float(im)))
            for index, (re, im, _) in expected.items()
            if index[0] > 0
        )
        > 0.1
    )


@pytest.mark.parametrize("dc", [0j, -2 + 3j, 4 - 5j])
def test_arbitrary_nonhermitian_zero_dc_cancellation_and_zero_stencils(
    api: Any, dc: complex
) -> None:
    record = response((3, 3, 3), (1.0,) * 3, origin=(0, 0, 0))
    record.values[0, 1, 1, 1] = dc
    record.values[1] = 0
    record.values[2] = 0
    record.values[2, 1:, 1:, 1:] = np.array([[[1j, -1j], [-1j, 1j]], [[-1j, 1j], [1j, -1j]]])
    kwargs = identity(target_voxel_size_um=(2.0,) * 3, phase_reference_shift_rad=0.2)
    actual = api(record, **kwargs).orders.values
    expected = oracle(record, kwargs)
    assert_budget(actual, expected)
    assert actual[0, 1, 1, 1] == dc
    assert np.count_nonzero(actual[1]) == 0
    assert abs(actual[2, 2, 2, 2]) <= float(expected[(2, 2, 2, 2)][2])


class ArraySubclass(np.ndarray[Any, Any]):
    """Supply a deliberately unsupported array subclass."""


class TupleSubclass(tuple[Any, ...]):
    """Supply a deliberately unsupported tuple subclass."""


class ListSubclass(list[Any]):
    """Supply a deliberately unsupported list subclass."""


@pytest.mark.parametrize("bad", [None, [], np.zeros((3, 3, 4, 5)), "response"])
def test_response_type_rejects(api: Any, bad: Any) -> None:
    expect_code(api, bad, "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "case",
    [
        "list",
        "subclass",
        "masked",
        "real",
        "narrow",
        "wide",
        "bool",
        "object",
        "rank",
        "orders",
        "empty",
        "nan",
        "inf_real",
        "inf_imag",
    ],
)
def test_entire_source_values_validation_including_unused_samples(api: Any, case: str) -> None:
    record = response()
    values: Any = record.values.copy()
    if case == "list":
        values = values.tolist()
    elif case == "subclass":
        values = values.view(ArraySubclass)
    elif case == "masked":
        values = np.ma.array(values)
    elif case in ("real", "narrow", "wide", "bool", "object"):
        dtype = {
            "real": np.float64,
            "narrow": np.complex64,
            "wide": np.clongdouble,
            "bool": np.bool_,
            "object": object,
        }[case]
        # clongdouble may equal complex128 on a platform; use a definite wrong width then.
        if case == "wide" and np.dtype(dtype).itemsize == 16:
            dtype = np.complex64
        values = np.zeros(record.values.shape, dtype=dtype)
    elif case == "rank":
        values = values[0]
    elif case == "orders":
        values = values[:2]
    elif case == "empty":
        values = values[:, :0]
    else:
        values[2, 0, 0, 0] = {
            "nan": complex(np.nan, 0),
            "inf_real": complex(np.inf, 0),
            "inf_imag": complex(0, -np.inf),
        }[case]
    expect_code(
        api,
        changed(record, values=values),
        "invalid_empirical_transfer_response",
        identity(target_shape_zyx=(1, 1, 1)),
    )


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize(
    "case",
    [
        "list",
        "subclass",
        "masked",
        "narrow",
        "integer",
        "rank",
        "length",
        "nan",
        "inf",
        "reverse",
        "duplicate",
        "dc",
        "off_dc_zero",
        "far",
    ],
)
def test_all_source_frequency_fields_validation(api: Any, axis: int, case: str) -> None:
    record = response()
    field = FREQUENCY_FIELDS[axis]
    value: Any = getattr(record, field).copy()
    if case == "list":
        value = value.tolist()
    elif case == "subclass":
        value = value.view(ArraySubclass)
    elif case == "masked":
        value = np.ma.array(value)
    elif case in ("narrow", "integer"):
        value = value.astype(np.float32 if case == "narrow" else np.int64)
    elif case == "rank":
        value = value[None]
    elif case == "length":
        value = value[:-1]
    elif case == "reverse":
        value = value[::-1]
    elif case == "duplicate":
        value[0] = value[1]
    elif case == "dc":
        value[len(value) // 2] = float(QUANTUM)
    elif case == "off_dc_zero":
        value[0] = 0
    elif case == "far":
        value[0] *= 1 + 32 * float(EPS)
    else:
        value[0] = np.nan if case == "nan" else np.inf
    expect_code(
        api,
        changed(record, **{field: value}),
        "invalid_empirical_transfer_response",
        identity(target_shape_zyx=(1, 1, 1)),
    )


BAD_TRIPLES: list[Any] = [
    None,
    np.array([1, 1, 1]),
    TupleSubclass((1, 1, 1)),
    ListSubclass([1, 1, 1]),
    (1, 1),
    (1, 1, 1, 1),
    (True, 1, 1),
    (np.bool_(True), 1, 1),
    (1 + 0j, 1, 1),
    ("1", 1, 1),
    (Fraction(1), 1, 1),
]
BAD_SPACINGS: list[Any] = [
    *BAD_TRIPLES,
    (0, 1, 1),
    (-1, 1, 1),
    (np.nan, 1, 1),
    (np.inf, 1, 1),
    (10**400, 1, 1),
    (np.longdouble(0.0), 1, 1),
]
BAD_ORIGINS: list[Any] = [*BAD_TRIPLES, (1.0, 1, 1), (-1, 1, 1), (3, 1, 1), (2**100, 1, 1)]


@pytest.mark.parametrize("bad", BAD_SPACINGS)
def test_source_spacing_grammar_and_conversion(api: Any, bad: Any) -> None:
    expect_code(api, changed(response(), voxel_size_um=bad), "invalid_empirical_transfer_response")


@pytest.mark.parametrize("bad", BAD_ORIGINS)
def test_source_origin_grammar_and_bounds(api: Any, bad: Any) -> None:
    expect_code(api, changed(response(), origin_zyx=bad), "invalid_empirical_transfer_response")


@pytest.mark.parametrize("field", ["values", *FREQUENCY_FIELDS, "voxel_size_um", "origin_zyx"])
def test_missing_source_attributes_and_unrelated_getter_failure(api: Any, field: str) -> None:
    base = response()

    class Missing(sr.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == field:
                raise AttributeError("missing public response field")
            return super().__getattribute__(name)

    class Broken(sr.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == field:
                raise RuntimeError("unrelated public getter failure")
            return super().__getattribute__(name)

    fields = response_fields(base)
    expect_code(api, Missing(**fields), "invalid_empirical_transfer_response")
    with pytest.raises(RuntimeError, match="unrelated public getter failure"):
        api(Broken(**fields), **identity())


@pytest.mark.parametrize(
    "bad", [*BAD_TRIPLES, (1.0, 3, 3), (0, 3, 3), (-1, 3, 3), (np.iinfo(np.intp).max + 1, 3, 3)]
)
def test_target_shape_grammar_and_extent(api: Any, bad: Any) -> None:
    expect_code(
        api, response(), "invalid_empirical_transfer_target_shape", identity(target_shape_zyx=bad)
    )


@pytest.mark.parametrize("bad", BAD_SPACINGS)
def test_target_spacing_grammar_and_conversion(api: Any, bad: Any) -> None:
    expect_code(
        api,
        response(),
        "invalid_empirical_transfer_target_voxel_size",
        identity(target_voxel_size_um=bad),
    )


def tolerance_admitted_extreme_source() -> Any:
    spacing = float.fromhex("0x0.1555555555555p-1022")
    maximum = float(np.finfo(np.float64).max)
    # The ideal z endpoints exceed Fmax. Finite stored endpoints still satisfy
    # the source metadata allowance; do not round the ideal source coordinates.
    return sr.EmpiricalVolumeResponse(
        values=asymmetric_values((3, 1, 1)),
        fz_per_um=np.array([-maximum, 0.0, maximum], dtype=np.float64),
        fy_per_um=np.array([0.0], dtype=np.float64),
        fx_per_um=np.array([0.0], dtype=np.float64),
        voxel_size_um=(spacing, 1.0, 1.0),
        origin_zyx=(0, 0, 0),
    )


def test_oracle_self_tolerance_admitted_source_and_isolated_target_range() -> None:
    record = tolerance_admitted_extreme_source()
    ideal = coordinates(3, record.voxel_size_um[0])
    # Beyond the round-to-nearest overflow midpoint, not merely above Fmax.
    assert ideal[2] > FMAX + 2**970
    assert abs(FMAX - ideal[2]) <= 8 * EPS * abs(ideal[2]) + QUANTUM
    for axis, field in enumerate(FREQUENCY_FIELDS):
        nodes = coordinates(record.values.shape[axis + 1], record.voxel_size_um[axis])
        for stored, exact in zip(getattr(record, field), nodes, strict=True):
            assert abs(Fraction.from_float(float(stored)) - exact) <= 8 * EPS * abs(exact) + QUANTUM
    for factor in (1, 2):
        target = coordinates(3, factor * record.voxel_size_um[0])
        assert ideal[0] <= target[0] <= target[-1] <= ideal[-1]
    finite = coordinates(3, 2 * record.voxel_size_um[0])
    assert 0 < finite[2] < FMAX
    assert math.isfinite(float(finite[2]))


def test_target_unrepresentable_frequency_error(api: Any) -> None:
    record = tolerance_admitted_extreme_source()
    expect_code(
        api,
        record,
        "unrepresentable_otf_frequencies",
        identity(target_shape_zyx=(3, 1, 1), target_voxel_size_um=record.voxel_size_um),
    )


def test_tolerance_admitted_extreme_source_with_finite_target(api: Any) -> None:
    record = tolerance_admitted_extreme_source()
    target_spacing = (2 * record.voxel_size_um[0], 1.0, 1.0)
    kwargs = identity(target_shape_zyx=(3, 1, 1), target_voxel_size_um=target_spacing)
    actual = api(record, **kwargs).orders
    assert_budget(actual.values, oracle(record, kwargs))
    for axis, field in enumerate(FREQUENCY_FIELDS):
        expected = np.array(
            [float(f) for f in coordinates(actual.values.shape[axis + 1], target_spacing[axis])],
            dtype=np.float64,
        )
        assert getattr(actual, field).tobytes() == expected.tobytes()
    assert actual.origin_zyx == (0, 0, 0)


@pytest.mark.parametrize("spacing", [float(np.finfo(float).max), 1e308])
def test_final_rn64_frequencies_survive_period_overflow(api: Any, spacing: float) -> None:
    record = response((3, 3, 3), (spacing,) * 3, origin=(0, 0, 0))
    kwargs = identity(target_voxel_size_um=(spacing,) * 3)
    actual = api(record, **kwargs).orders
    assert actual.values.tobytes() == record.values.tobytes()
    for got, wanted in zip(
        arrays(actual)[1:], frequency_arrays((3, 3, 3), (spacing,) * 3), strict=True
    ):
        assert got.tobytes() == wanted.tobytes()
        assert got[0] < 0 < got[2]
        assert not np.signbit(got[1])


@pytest.mark.parametrize("spacing", [float(QUANTUM), float(np.finfo(float).max)])
def test_singleton_accepts_every_positive_represented_spacing(api: Any, spacing: float) -> None:
    record = response(
        (1, 1, 1), [np.float64(spacing), spacing, spacing], origin=[np.int64(0), np.uint64(0), 0]
    )
    kwargs = identity(
        target_shape_zyx=[np.int64(1), np.uint64(1), 1],
        target_voxel_size_um=[spacing, np.float64(spacing), spacing],
        phase_reference_shift_rad=np.float64(-0.0),
    )
    actual = api(record, **kwargs)
    assert actual.orders.values.tobytes() == record.values.tobytes()
    assert all(type(d) is float for d in actual.orders.voxel_size_um)
    assert all(type(n) is int for n in actual.provenance["source_origin_zyx"])
    assert math.copysign(1, actual.provenance["phase_reference_shift_rad"]) == -1


BAD_PAIRS: list[Any] = [
    None,
    np.array([0, 0]),
    TupleSubclass((0, 0)),
    ListSubclass([0, 0]),
    (0,),
    (0, 0, 0),
    (True, 0),
    (np.bool_(False), 0),
    (1.0, 0),
    (1 + 0j, 0),
    ("1", 0),
    (Fraction(1), 0),
]


@pytest.mark.parametrize(
    "field,code",
    [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("specimen_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset"),
    ],
)
@pytest.mark.parametrize("bad", BAD_PAIRS)
def test_exact_pair_grammar(api: Any, field: str, code: str, bad: Any) -> None:
    expect_code(api, response(), code, identity(**{field: bad}))


@pytest.mark.parametrize(
    "bad",
    [
        True,
        np.bool_(False),
        1j,
        "0",
        [],
        np.array(0.0),
        Fraction(1),
        Decimal(1),
        np.nan,
        np.inf,
        -np.inf,
        10**400,
    ],
)
def test_phase_grammar_finiteness_and_conversion(api: Any, bad: Any) -> None:
    expect_code(
        api,
        response(),
        "invalid_empirical_transfer_phase_shift",
        identity(phase_reference_shift_rad=bad),
    )


@pytest.mark.parametrize(
    "angle",
    [
        -0.0,
        0,
        float(QUANTUM),
        -0.7,
        np.float32(0.2),
        float(np.finfo(float).max),
        -float(np.finfo(float).max),
        np.longdouble(0.0),
    ],
)
def test_phase_permitted_extremes_without_doubled_angle_overflow(api: Any, angle: Any) -> None:
    record = response()
    kwargs = declarations(phase_reference_shift_rad=angle)
    actual = api(record, **kwargs)
    assert_budget(actual.orders.values, oracle(record, kwargs))
    assert type(actual.provenance["phase_reference_shift_rad"]) is float
    assert actual.provenance["phase_reference_shift_rad"] == float(angle)


@pytest.mark.parametrize("bad", [None, 1, "", "  \t\n", b"source"])
def test_source_label_rejects(api: Any, bad: Any) -> None:
    expect_code(api, response(), "invalid_otf_source", identity(source=bad))


@pytest.mark.parametrize(
    "layout", ["native", "fortran", "reversed", "strided", "big_endian", "readonly"]
)
def test_storage_snapshots_ownership_and_frozen_wrapper(api: Any, layout: str) -> None:
    record = response()
    transformed = []
    for a in arrays(record):
        if layout == "fortran":
            b = np.asfortranarray(a)
        elif layout == "reversed":
            # Preserve canonical frequency values while supplying negative strides.
            b = np.flip(np.flip(a).copy())
        elif layout == "strided":
            backing = np.empty((*a.shape[:-1], 2 * a.shape[-1]), dtype=a.dtype)
            b = backing[..., ::2]
            b[:] = a
        elif layout == "big_endian":
            b = a.astype(a.dtype.newbyteorder(">"))
        else:
            b = a.copy()
        if layout == "readonly":
            b.flags.writeable = False
        transformed.append(b)
    record = changed(record, **dict(zip(("values", *FREQUENCY_FIELDS), transformed, strict=True)))

    class OrdinarySubclass(sr.EmpiricalVolumeResponse):
        pass

    record = OrdinarySubclass(**response_fields(record))
    before = snapshot(record)
    spacing = [1, np.float64(1.5), 2.5]
    offset = [np.int64(-1), 4]
    kwargs = declarations(
        target_shape_zyx=[np.int64(3), np.uint64(3), 3],
        target_voxel_size_um=spacing,
        coordinate_offset_yx=offset,
    )
    actual = api(record, **kwargs)
    again = api(record, **kwargs)
    assert_budget(actual.orders.values, oracle(record, kwargs))
    expected_provenance = {
        "sampling": "complex_cartesian_trilinear_v1",
        "source_shape_zyx": (3, 4, 5),
        "source_voxel_size_um": (0.5, 0.75, 1.25),
        "source_origin_zyx": (1, 2, 3),
        "calibration_carrier_bins": (2, -5),
        "specimen_carrier_bins": (3, -6),
        "coordinate_offset_yx": (-1, 4),
        "phase_reference_shift_rad": 0.375,
    }
    assert type(actual.provenance) is dict
    assert actual.provenance == expected_provenance
    assert actual.provenance is not again.provenance
    output_arrays = arrays(actual.orders)
    all_outputs = output_arrays + arrays(again.orders)
    for a in all_outputs:
        assert type(a) is np.ndarray
        assert a.flags.owndata and a.flags.c_contiguous and a.flags.writeable
        assert a.dtype.isnative
        assert a.dtype == (np.dtype(np.complex128) if a.ndim == 4 else np.dtype(np.float64))
        assert all(not np.shares_memory(a, b) for b in arrays(record))
    for a, b in combinations(all_outputs, 2):
        assert not np.shares_memory(a, b)
    for field in ("orders", "provenance"):
        with pytest.raises((AttributeError, TypeError)):
            setattr(actual, field, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(actual, field)
    spacing[0] = 9
    offset[0] = 999
    assert actual.provenance == expected_provenance
    actual.provenance["source_origin_zyx"] = (0, 0, 0)
    assert again.provenance == expected_provenance
    for a in output_arrays:
        a.flat[0] = 123
    assert_input_unchanged(record, before)
    expect_code(api, record, "invalid_otf_source", declarations(source=""))
    assert_input_unchanged(record, before)


def test_extreme_weighted_contribution_survives_standalone_weight_underflow(api: Any) -> None:
    # Source nodes +/-1/(3*q) are not representable, so use a large but valid
    # source frequency ~1e307 and a tiny target ~1e-309. The positive weight
    # is ~1e-616, but weight*Fmax ~1e-308 is far above 64*q.
    source_spacing = 1e-308
    target_spacing = 1e308
    values = np.zeros((3, 1, 1, 3), dtype=np.complex128)
    values[:, 0, 0, 2] = complex(float(np.finfo(float).max) / 4, -float(np.finfo(float).max) / 8)
    record = response((1, 1, 3), (1.0, 1.0, source_spacing), values=values, origin=(0, 0, 0))
    kwargs = identity(target_shape_zyx=(1, 1, 3), target_voxel_size_um=(1.0, 1.0, target_spacing))
    expected = oracle(record, kwargs)
    assert float(Fraction.from_float(source_spacing) / Fraction.from_float(target_spacing)) == 0
    with localcontext() as context:
        context.prec = PRECISION
        assert abs(expected[(0, 0, 0, 2)][0]) > 10**10 * expected[(0, 0, 0, 2)][2]
    actual = api(record, **kwargs).orders.values
    assert_budget(actual, expected)
    assert np.count_nonzero(actual[:, 0, 0, 0]) == 0


def test_safe_finite_cancellation_and_rotation_avoid_intermediate_overflow(api: Any) -> None:
    f = float(np.finfo(float).max)
    record = response((1, 1, 3), (1.0, 1.0, 1.0), origin=(0, 0, 0))
    record.values[:] = 0
    record.values[:, 0, 0, 1] = complex(0.6 * f, 0.6 * f)
    record.values[:, 0, 0, 2] = complex(-0.6 * f, -0.6 * f)
    kwargs = identity(
        target_shape_zyx=(1, 1, 3),
        target_voxel_size_um=(1.0, 1.0, 2.0),
        phase_reference_shift_rad=0.2,
    )
    assert_budget(api(record, **kwargs).orders.values, oracle(record, kwargs))


def weighted_extreme_corner_case() -> tuple[Any, dict[str, Any]]:
    record = response((1, 1, 3), (1.0, 1.0, 1.0), origin=(0, 0, 0))
    record.values[:] = 0
    maximum = float(np.finfo(np.float64).max)
    record.values[1:, 0, 0, 0] = complex(maximum, maximum)
    record.values[1:, 0, 0, 2] = complex(maximum, maximum)
    kwargs = identity(
        target_shape_zyx=(1, 1, 3),
        target_voxel_size_um=(1.0, 1.0, 2.0),
        phase_reference_shift_rad=math.pi / 4,
    )
    return record, kwargs


def test_oracle_self_weighted_corner_success_margin_despite_corner_overflow() -> None:
    record, kwargs = weighted_extreme_corner_case()
    expected = oracle(record, kwargs)
    with localcontext() as context:
        context.prec = PRECISION
        maximum = decimal(FMAX)
        c, s = phasor(angle=-float(kwargs["phase_reference_shift_rad"]))
        corner_real = maximum * (c - s)
        assert corner_real > Decimal("1.4") * maximum
        first = (corner_real / 2, maximum * (c + s) / 2)
        second = (
            maximum * (c * c - s * s - 2 * c * s) / 2,
            maximum * (c * c - s * s + 2 * c * s) / 2,
        )
        allowance = decimal(1024 * EPS * FMAX + 64 * QUANTUM)
        observer_rounding = maximum * Decimal("1e-780")
        for order, components in ((1, first), (2, second)):
            for x in (0, 2):
                re, im, delta = expected[(order, 0, 0, x)]
                assert abs(re - components[0]) <= observer_rounding
                assert abs(im - components[1]) <= observer_rounding
                assert delta == allowance
        margin = min(
            maximum - abs(component) - delta
            for re, im, delta in expected.values()
            for component in (re, im)
        )
        assert margin > Decimal("0.29") * maximum


def test_safe_weighted_rotation_when_unweighted_corner_would_overflow(api: Any) -> None:
    record, kwargs = weighted_extreme_corner_case()
    expected = oracle(record, kwargs)
    actual = api(record, **kwargs).orders.values
    assert_budget(actual, expected)
    assert np.count_nonzero(actual[0]) == 0


def test_tensor_weight_product_underflow_keeps_representable_contribution(api: Any) -> None:
    values = np.zeros((3, 1, 3, 3), dtype=np.complex128)
    values[:, 0, 2, 2] = complex(float(np.finfo(float).max) / 4, 0)
    record = response((1, 3, 3), (1.0, 1e-100, 1e-100), values=values, origin=(0, 0, 0))
    kwargs = identity(target_shape_zyx=(1, 3, 3), target_voxel_size_um=(1.0, 1e100, 1e100))
    expected = oracle(record, kwargs)
    with localcontext() as context:
        context.prec = PRECISION
        assert abs(expected[(0, 0, 2, 2)][0]) > 10**10 * expected[(0, 0, 2, 2)][2]
    assert_budget(api(record, **kwargs).orders.values, expected)


def test_final_rotation_component_overflow_rejects_whole_call(api: Any) -> None:
    record = response((1, 1, 1), (1.0,) * 3, origin=(0, 0, 0))
    record.values[:] = 0
    record.values[1, 0, 0, 0] = complex(float(np.finfo(float).max), float(np.finfo(float).max))
    kwargs = identity(target_shape_zyx=(1, 1, 1), phase_reference_shift_rad=math.pi / 4)
    before = snapshot(record)
    expect_code(api, record, "unrepresentable_empirical_interpolation", kwargs)
    assert_input_unchanged(record, before)


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log"])
def test_caller_arithmetic_and_warning_modes_preserved(api: Any, mode: Any) -> None:
    class Sink:
        def write(self, message: str) -> None:
            raise AssertionError("handled arithmetic reached caller log")

        def __call__(self, error: str, flag: int) -> None:
            raise AssertionError("handled arithmetic reached caller callback")

    old_mode = np.geterr()
    old_callback = np.geterrcall()
    try:
        np.seterrcall(Sink())
        np.seterr(all=mode)
        before_mode = np.geterr()
        before_callback = np.geterrcall()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            filters = list(warnings.filters)
            record = response((1, 1, 1), (1.0,) * 3, origin=(0, 0, 0))
            record.values[:] = complex(float(QUANTUM), -float(QUANTUM))
            kwargs = identity(target_shape_zyx=(1, 1, 1), phase_reference_shift_rad=0.3)
            actual = api(record, **kwargs)
            assert_budget(actual.orders.values, oracle(record, kwargs))
            expect_code(
                api,
                record,
                "invalid_empirical_transfer_phase_shift",
                {**kwargs, "phase_reference_shift_rad": 10**400},
            )
            record.values[1] = complex(float(np.finfo(float).max), float(np.finfo(float).max))
            expect_code(
                api,
                record,
                "unrepresentable_empirical_interpolation",
                {**kwargs, "phase_reference_shift_rad": math.pi / 4},
            )
            assert warnings.filters == filters
            assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
        assert np.geterr() == before_mode
        assert np.geterrcall() is before_callback
    finally:
        np.seterr(**old_mode)
        np.seterrcall(old_callback)


@pytest.mark.parametrize(
    "exception",
    [
        MemoryError("allocation-like getter failure"),
        TypeError("unrelated getter failure"),
        ValueError("unrelated getter failure"),
        OverflowError("unrelated getter failure"),
    ],
)
def test_unrelated_and_allocation_getter_exceptions_propagate(
    api: Any, exception: Exception
) -> None:
    class Broken(sr.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                raise exception
            return super().__getattribute__(name)

    base = response()
    record = Broken(**response_fields(base))
    with pytest.raises(type(exception)) as caught:
        api(record, **identity())
    assert caught.value is exception


def test_unrelated_getter_warning_is_preserved(api: Any) -> None:
    class Warns(sr.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                warnings.warn("public getter warning", UserWarning, stacklevel=2)
            return super().__getattribute__(name)

    base = response()
    record = Warns(**response_fields(base))
    with pytest.warns(UserWarning, match="public getter warning"):
        api(record, **identity())


@pytest.fixture(scope="module")
def raw_calibration() -> Any:
    shape = (1, 5, 5)
    bead = (0, 1, 2)
    alpha_c = -0.2
    actual_phases = np.array([-0.4, 0.2, 1.0, 1.9, 2.8, 4.0, 5.2])
    h = np.zeros(shape, dtype=np.float64)
    h[0, 0, 0] = 0.75
    h[0, 1, 0] = 0.125
    h[0, 0, 1] = 0.125
    centered = np.roll(h, bead, axis=(0, 1, 2))
    bands = np.empty((3, *shape), dtype=np.complex128)
    g = (1 + 0j, (2 + 1j) / 16, (-1 + 2j) / 32)
    for m in range(3):
        c, s = phasor(Fraction(m * 2, 5))
        bands[m] = 32 * centered * g[m] * complex(float(c), float(s))
    signal = phase_images(bands, actual_phases)
    raw = (11 + 2 * signal)[None]
    acquisition = sr.declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "count",
            # Commands deliberately differ from both actual phase schedules.
            "nominal_phases_rad": [[0.0] * len(actual_phases)],
        },
    )
    calibrated = sr.calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=11,
        response=2,
        output_unit="electron",
        phases_rad=actual_phases + alpha_c,
        voxel_size_um=(1.0, 1.0, 1.0),
    )
    expected = smooth_samples(shape, (1.0,) * 3, alpha_c)
    for m in (1, 2):
        c, s = phasor(Fraction(m * 2, 5))
        expected[m] *= complex(float(c), float(s))
    bmax = float(np.max(abs(signal)))
    # The separator informative budget plus forward-generation/correction rounding.
    e = (8192 * len(actual_phases) + 128) * float(EPS) * bmax
    # Two real coordinates bound a complex side error by 2e. Common mass is 32;
    # the peak margin is 20, far greater than 2e. |E|<=1, Lambda<=1.5.
    mass_error = h.size * e
    budget = (2 * h.size * e + mass_error) / (32 - mass_error)
    budget += 512 * h.size * float(EPS) * 1.5
    assert 2 * e < 20 and mass_error < 32
    return calibrated, expected, budget, alpha_c


def test_public_raw_bead_prerequisite_and_independent_input_expectations(
    raw_calibration: Any,
) -> None:
    calibrated, expected, budget, _ = raw_calibration
    assert calibrated.response.origin_zyx == (0, 1, 2)
    assert calibrated.response.values.shape == expected.shape
    assert np.max(abs(calibrated.response.values - expected)) <= budget
    assert calibrated.provenance["phases_rad"]["source"] == "supplied_actual"
    assert calibrated.provenance["bead_compensation"] == "identity"


def test_existing_same_grid_adapter_keeps_even_grid_and_observed_origin() -> None:
    record = response((2, 2, 2), (1.0,) * 3, origin=(1, 1, 1))
    actual = sr.adapt_empirical_volume_response(
        record,
        carrier_bins=(0, 0),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source="existing even-grid common-grid declaration",
    )
    assert actual.values.tobytes() == record.values.tobytes()
    assert actual.origin_zyx == (1, 1, 1)


def test_permitted_numpy_scalar_metadata_preserves_converted_meaning(api: Any) -> None:
    spacing = [np.uint64(1), np.int16(2), np.float32(0.5)]
    record = response((3, 3, 3), spacing, origin=[np.uint64(0), np.int16(1), np.int64(2)])
    kwargs = identity(
        target_shape_zyx=[np.uint64(3), np.int16(3), np.int64(3)],
        target_voxel_size_um=[np.float32(1), np.longdouble(2), np.float64(0.5)],
        calibration_carrier_bins=[np.int16(0), np.uint64(0)],
        specimen_carrier_bins=[np.uint64(0), np.int64(0)],
        coordinate_offset_yx=[np.int16(-1), np.uint64(2**64 - 1)],
        phase_reference_shift_rad=np.uint64(2**64 - 1),
    )
    actual = api(record, **kwargs)
    assert_budget(actual.orders.values, oracle(record, kwargs))
    assert actual.provenance["phase_reference_shift_rad"] == float(np.uint64(2**64 - 1))
    assert actual.provenance["source_voxel_size_um"] == (1.0, 2.0, 0.5)


def test_oracle_self_specimen_forward_and_ridge_bias_accounting() -> None:
    example = specimen_example()
    expected = signed_estimator(example, example["physical"])
    truth = example["truth"]
    assert np.max(abs(expected - truth)) > 0.01  # Declared ridge bias, not numerical error.
    assert np.max(abs(expected[truth == 0])) < 1e-15
    assert 0 < expected[0, 7, 1].real < 1
    assert np.max(abs(example["images"])) < 3


def test_oracle_self_contract_example_margins_and_held_out_error() -> None:
    record = response()
    kwargs = declarations()
    for axis in range(3):
        source_nodes = coordinates(record.values.shape[axis + 1], record.voxel_size_um[axis])
        target_nodes = coordinates(
            kwargs["target_shape_zyx"][axis], kwargs["target_voxel_size_um"][axis]
        )
        assert source_nodes[0] <= target_nodes[0] <= target_nodes[-1] <= source_nodes[-1]
    for axis in (0, 1):
        kc = Fraction(kwargs["calibration_carrier_bins"][axis], record.values.shape[axis + 2])
        kc /= Fraction.from_float(record.voxel_size_um[axis + 1])
        ks = Fraction(kwargs["specimen_carrier_bins"][axis], kwargs["target_shape_zyx"][axis + 1])
        ks /= Fraction.from_float(kwargs["target_voxel_size_um"][axis + 1])
        assert kc == ks
    example = specimen_example()
    # Use phase zero and origin zero to isolate geometric approximation here.
    source = response(
        (1, 5, 5), (1.0,) * 3, values=smooth_samples((1, 5, 5), (1.0,) * 3), origin=(0, 0, 0)
    )
    expected = oracle(
        source,
        identity(target_shape_zyx=example["target"], target_voxel_size_um=example["spacing"]),
    )
    interpolated = np.empty((3, *example["target"]), dtype=np.complex128)
    for index, (re, im, _) in expected.items():
        interpolated[index] = complex(float(re), float(im))
    physical = smooth_samples(example["target"], example["spacing"])
    assert 0.001 < np.max(abs(interpolated - physical)) < 0.2
    # Apply the independently declared specimen reference gauge to both orders.
    for m in (1, 2):
        c, s = phasor(angle=-m * example["alpha_s"])
        interpolated[m] *= complex(float(c), float(s))
    result = signed_estimator(example, interpolated)
    physical_result = signed_estimator(example, example["physical"])
    assert np.max(abs(result - physical_result)) > 1e-4


def test_raw_bead_adapter_specimen_reconstruction_with_separate_model_error(
    api: Any, raw_calibration: Any
) -> None:
    calibrated, source_expected, calibration_budget, alpha_c = raw_calibration
    example = specimen_example()
    kwargs = identity(
        target_shape_zyx=example["target"],
        target_voxel_size_um=example["spacing"],
        calibration_carrier_bins=(2, 0),
        specimen_carrier_bins=(3, 0),
        phase_reference_shift_rad=example["alpha_s"] - alpha_c,
        source="declared three-site continuous comparison; point bead; known phases",
    )
    ideal_source = response((1, 5, 5), (1.0,) * 3, values=source_expected, origin=(0, 1, 2))
    expected = oracle(ideal_source, kwargs)
    ideal_interpolated = np.empty((3, *example["target"]), dtype=np.complex128)
    for index, (re, im, _) in expected.items():
        ideal_interpolated[index] = complex(float(re), float(im))
    actual = api(calibrated.response, **kwargs)
    arithmetic_budget = max(float(value[2]) for value in expected.values())
    transfer_budget = calibration_budget + 2 * arithmetic_budget
    assert np.max(abs(actual.orders.values - ideal_interpolated)) <= transfer_budget
    held_out_error = float(np.max(abs(ideal_interpolated - example["physical"])))
    assert 0.001 < held_out_error < 0.2
    # This is approximation of a separately declared continuous Fourier polynomial.
    # It is deliberately not called exact continuous physical recovery.
    expected_spectrum = signed_estimator(example, ideal_interpolated)
    physical_spectrum = signed_estimator(example, example["physical"])
    assert np.max(abs(expected_spectrum - physical_spectrum)) > 1e-4
    assert np.max(abs(physical_spectrum - example["truth"])) > 0.01
    reconstruction = sr.reconstruct_volume(
        example["images"],
        order_otfs=[actual.orders],
        phases_rad=example["phases"][None],
        carriers_bins=np.array([[3, 0]], dtype=np.int64),
        gains=np.array([example["gain"]]),
        regularization=example["penalty"],
        output_shape_yx=example["output"][1:],
        apodization=np.ones(example["output"]),
    )
    n = len(example["phases"])
    detector_sites = math.prod(example["target"])
    output_sites = math.prod(example["output"])
    bmax = float(np.max(abs(example["images"])))
    separator_error = 8192 * n * float(EPS) * bmax
    beta_s = 65536 * 5 * (n + detector_sites) * float(EPS) * bmax
    # For |E|<=1, gain=1.5, lambda=.25, |D|<=1.5 and <=5 terms:
    # |dQ/dE| <= 6120, |dQ/dD| <=30. Round up for both complex coordinates.
    # This includes calibration propagation and adapter rounding, separately from
    # held-out interpolation error and the explicitly retained ridge bias.
    spectrum_budget = 8192 * transfer_budget + 64 * separator_error + beta_s
    assert spectrum_budget < 1e-4
    np.testing.assert_allclose(
        reconstruction.spectrum, expected_spectrum, rtol=0, atol=spectrum_budget
    )
    expected_volume = direct_dft(expected_spectrum, inverse=True)
    volume_budget = output_sites * spectrum_budget + 16384 * 5 * output_sites * float(EPS) * bmax
    np.testing.assert_allclose(reconstruction.volume, expected_volume, rtol=0, atol=volume_budget)
    assert actual.orders.origin_zyx == (0, 0, 0)
