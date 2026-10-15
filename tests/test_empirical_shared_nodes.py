"""Blind A tests for FEATURE R01-R14 and SN01-SN92.

Scenario obligations and non-executable scope limits are mapped in A01/evidence/REPORT.md.
"""

from __future__ import annotations

import dataclasses
import importlib
import math
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any, Literal

import numpy as np
import pytest

from empirical_shared_node_fixture import (
    assert_rotation,
    component_bits,
    decimal_components,
    discrete_forward,
    empirical_expected,
    estimator,
    indices,
    kernel,
    modes,
    negation,
    phase_basis,
    physical_bead,
    physical_specimen,
    polynomial_transfer,
    response,
    rotated,
    selected,
)

api = importlib.import_module("simrecon")
EPS = 2.0**-52
FMAX = np.finfo(np.float64).max
Q = float.fromhex("0x0.0000000000001p-1022")


def declarations(record: Any, **changes: Any) -> dict[str, Any]:
    result = dict(
        target_shape_zyx=record.values.shape[1:],
        target_voxel_size_um=record.voxel_size_um,
        calibration_carrier_bins=(0, 0),
        specimen_carrier_bins=(0, 0),
        coordinate_offset_yx=(0, 0),
        phase_reference_shift_rad=0.0,
        source=" paired calibration / specimen ; opaque ",
    )
    result.update(changes)
    return result


def adapt(record: Any, **changes: Any) -> Any:
    function = api.adapt_empirical_volume_response_shared_nodes
    return function(record, **declarations(record, **changes))


def reject(record: Any, code: str, **changes: Any) -> None:
    kwargs = declarations(
        response(api), target_shape_zyx=(1, 1, 1), target_voxel_size_um=(1.0,) * 3
    )
    kwargs.update(changes)
    with pytest.raises(api.SimreconError) as error:
        api.adapt_empirical_volume_response_shared_nodes(record, **kwargs)
    assert error.value.code == code


def snapshot(record: Any) -> tuple[Any, ...]:
    arrays = (record.values, record.fz_per_um, record.fy_per_um, record.fx_per_um)
    return tuple((a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays)


def reconstruction_budget(
    images: np.ndarray, phases: np.ndarray, output: Any
) -> tuple[float, float]:
    """VR's informative absolute intensity-unit budgets, rounded upward."""
    assert np.linalg.cond(phase_basis(phases)) < 3
    with localcontext() as ctx:
        ctx.prec = 70
        j, n, m, p = 5, len(phases), math.prod(images.shape[1:]), math.prod(output)
        eps, q = Decimal(2) ** -52, Decimal(2) ** -1074
        b = Decimal.from_float(float(np.max(abs(images))))
        assert 65536 * j * (n + m + p) * eps <= Decimal(2) ** -10
        assert 64 * j * p * max(b, q) <= Decimal.from_float(FMAX)
        beta_s = 65536 * j * (n + m) * eps * b + 256 * j * (n + m) * q
        beta_v = p * beta_s + 16384 * j * p * eps * b + 64 * p * q
        return float(np.nextafter(float(beta_s), math.inf)), float(
            np.nextafter(float(beta_v), math.inf)
        )


def test_public_exports_and_binding() -> None:
    assert hasattr(api, "SharedNodeVolumeTransfer")
    function = api.adapt_empirical_volume_response_shared_nodes
    record = response(api)
    kwargs = declarations(record)
    assert isinstance(function(record, **kwargs), api.SharedNodeVolumeTransfer)
    for key in kwargs:
        missing = kwargs.copy()
        del missing[key]
        with pytest.raises(TypeError):
            function(record, **missing)
    with pytest.raises(TypeError):
        function(record, **kwargs, unknown=1)
    for key in kwargs:
        positional = kwargs.copy()
        value = positional.pop(key)
        with pytest.raises(TypeError):
            function(record, value, **positional)


@pytest.mark.parametrize(
    ("nc", "dc", "ns", "ds"),
    [
        ((9, 15, 21), (0.5, 0.25, 0.125), (3, 5, 7), (1.5, 0.75, 0.375)),
        ((4, 4, 4), (0.75, 0.75, 0.75), (3, 3, 3), (1.0, 1.0, 1.0)),
        ((12, 12, 12), (0.5, 0.25, 0.125), (4, 4, 4), (0.5, 0.25, 0.125)),
        ((15, 21, 27), (0.25, 0.125, 0.0625), (3, 3, 3), (0.625, 0.4375, 0.28125)),
        ((1, 5, 7), (Q, 0.25, 0.125), (1, 3, 3), (FMAX, 5 / 12, 7 / 24)),
        ((1, 9, 15), (Q, 0.25, 0.125), (1, 3, 5), (FMAX, 0.75, 0.375)),
    ],
)
def test_exact_geometry_and_cartesian_lookup(nc: Any, dc: Any, ns: Any, ds: Any) -> None:
    # Last case's non-dyadic spacing intentionally is not an exact rational match.
    record = response(api, nc, dc)
    for vector in (record.fz_per_um, record.fy_per_um, record.fx_per_um):
        vector[len(vector) // 2] = -0.0
        for i in range(len(vector)):
            if i != len(vector) // 2:
                vector[i] = np.nextafter(vector[i], math.copysign(math.inf, vector[i]))
    try:
        maps = tuple(indices(c, d, s, t) for c, d, s, t in zip(nc, dc, ns, ds, strict=True))
    except ValueError:
        reject(
            record,
            "incomplete_empirical_transfer_coverage",
            target_shape_zyx=ns,
            target_voxel_size_um=ds,
        )
        return
    assert all(len(set(axis)) == len(axis) for axis in maps)
    for c, s, axis in zip(nc, ns, maps, strict=True):
        for j, i in zip(modes(s), axis, strict=True):
            pneg = axis[negation(s, j) + s // 2] - c // 2
            assert pneg == negation(c, i - c // 2)
    result = adapt(record, target_shape_zyx=ns, target_voxel_size_um=ds)
    np.testing.assert_array_equal(
        component_bits(result.orders.values), component_bits(selected(record, ns, ds))
    )
    assert result.provenance["source_indices_zyx"] == maps
    for field, axis_map, n, spacing in zip(
        ("fz_per_um", "fy_per_um", "fx_per_um"),
        maps,
        ns,
        ds,
        strict=True,
    ):
        actual = getattr(result.orders, field)
        np.testing.assert_array_equal(
            component_bits(actual), component_bits(getattr(record, field)[list(axis_map)])
        )
        for value, mode in zip(actual, modes(n), strict=True):
            ideal = Fraction(mode, n) / Fraction(float(spacing))
            budget = 8 * Fraction(1, 2**52) * abs(ideal) + Fraction(1, 2**1074)
            assert abs(Fraction(float(value)) - ideal) <= budget


@pytest.mark.parametrize("axis", range(3))
@pytest.mark.parametrize("zero", [False, True])
def test_missing_nodes_and_noncommuting_nodes(axis: int, zero: bool) -> None:
    record = response(api, (9, 9, 9), (1.0, 1.0, 1.0))
    if zero:
        record.values[:] = 0
    shape = [3, 3, 3]
    spacing = [3.0, 3.0, 3.0]
    shape[axis] = 4
    spacing[axis] = 9 / 4  # Equal period, complete lookup, incompatible fixed Nyquist.
    reject(
        record,
        "incompatible_empirical_transfer_negation",
        target_shape_zyx=shape,
        target_voxel_size_um=spacing,
    )
    shape[axis] = 5
    spacing[axis] = 1.0  # 9/5 is not an integer map.
    reject(
        record,
        "incomplete_empirical_transfer_coverage",
        target_shape_zyx=shape,
        target_voxel_size_um=spacing,
    )


def test_rounded_coordinates_never_define_equality() -> None:
    record = response(api, (1, 1, 3), (1.0, 1.0, FMAX / 4))
    # Nearly equal rounded frequencies do not establish equal exact periods.
    ds = (1.0, 1.0, np.nextafter(record.voxel_size_um[2], math.inf))
    reject(
        record,
        "incomplete_empirical_transfer_coverage",
        target_shape_zyx=(1, 1, 3),
        target_voxel_size_um=ds,
    )
    near = response(api)
    near.fx_per_um[0] = np.nextafter(near.fx_per_um[0], -math.inf)
    near.fx_per_um[3] = -0.0
    result = adapt(near)
    np.testing.assert_array_equal(
        component_bits(result.orders.fx_per_um), component_bits(near.fx_per_um)
    )


@pytest.mark.parametrize("spacing", [Q, FMAX, 1.0, np.float32(0.125)])
def test_singletons_and_extreme_coordinate_copy(spacing: Any) -> None:
    record = response(api, (1, 1, 1), (FMAX, Q, 1.0))
    record.fz_per_um[0] = record.fy_per_um[0] = record.fx_per_um[0] = -0.0
    result = adapt(record, target_voxel_size_um=[spacing, spacing, spacing])
    for array in (result.orders.fz_per_um, result.orders.fy_per_um, result.orders.fx_per_um):
        assert np.signbit(array[0])
    assert result.orders.voxel_size_um == (float(spacing),) * 3


def test_overflowing_period_and_extreme_finite_frequencies() -> None:
    for spacing in (FMAX, float.fromhex("0x1p-1022")):
        record = response(api, (9, 9, 9), (spacing,) * 3)
        for array in (record.fz_per_um, record.fy_per_um, record.fx_per_um):
            array[4] = -0.0
            array[1] = np.nextafter(array[1], -math.inf)
            array[7] = np.nextafter(array[7], math.inf)
        result = adapt(record, target_shape_zyx=(3, 3, 3))
        for field in ("fz_per_um", "fy_per_um", "fx_per_um"):
            np.testing.assert_array_equal(
                component_bits(getattr(result.orders, field)),
                component_bits(getattr(record, field)[[1, 4, 7]]),
            )


@pytest.mark.parametrize("axis", [0, 1])
def test_carriers_physical_not_modular(axis: int) -> None:
    record = response(api, (9, 9, 9), (0.25,) * 3)
    huge = 2**160 + 17
    source_carrier = [0, 0]
    target_carrier = [0, 0]
    source_carrier[axis] = 3 * huge
    target_carrier[axis] = huge
    kwargs: dict[str, Any] = dict(
        target_shape_zyx=(3, 3, 3),
        target_voxel_size_um=(0.25,) * 3,
        calibration_carrier_bins=source_carrier,
        specimen_carrier_bins=target_carrier,
        coordinate_offset_yx=(-(2**200), 2**180 + 1),
        phase_reference_shift_rad=-0.375,
    )
    result = adapt(record, **kwargs)
    rho = sum(
        (
            Fraction(k * (b + o), n)
            for k, b, o, n in zip(
                source_carrier,
                record.origin_zyx[1:],
                kwargs["coordinate_offset_yx"],
                record.values.shape[2:],
                strict=True,
            )
        ),
        Fraction(),
    )
    assert_rotation(result.orders.values, selected(record, (3, 3, 3), (0.25,) * 3), rho, -0.375)
    target_carrier[axis] += 3  # Identical target gauge modulo a period; unequal physical carrier.
    record.values[1:] = 0
    reject(record, "mismatched_empirical_transfer_carrier", **kwargs)


@pytest.mark.parametrize("delta", [-0.375, FMAX, -FMAX, Q, -Q, -0.0])
def test_signed_complex_rotation_exact_modular_and_large_phase(delta: float) -> None:
    record = response(api, (1, 3, 5), (0.5, 0.25, 0.125))
    carriers = (-(2**230) + 9, 2**260 + 3)
    offsets = (2**310 + 1, -(2**290) + 2)
    rho = sum(
        (
            Fraction(k * (b + o), n)
            for k, b, o, n in zip(carriers, record.origin_zyx[1:], offsets, (3, 5), strict=True)
        ),
        Fraction(),
    )
    result = adapt(
        record,
        calibration_carrier_bins=carriers,
        specimen_carrier_bins=carriers,
        coordinate_offset_yx=offsets,
        phase_reference_shift_rad=delta,
    )
    assert_rotation(result.orders.values, record.values, rho, delta)
    np.testing.assert_array_equal(
        component_bits(result.orders.values[0]), component_bits(record.values[0])
    )


@pytest.mark.parametrize("delta", [0.0, -0.0])
def test_identity_components_zero_dc_and_extrema(delta: float) -> None:
    record = response(api, (1, 1, 3))
    record.values.real[:] = np.array([-0.0, FMAX, Q])
    record.values.imag[:] = np.array([0.0, FMAX, -Q])
    record.values[0, 0, 0, 1] = 0j  # Zero DC remains legitimate.
    result = adapt(
        record,
        calibration_carrier_bins=(0, 3),
        specimen_carrier_bins=(0, 3),
        coordinate_offset_yx=(0, 2**200),
        phase_reference_shift_rad=delta,
    )
    np.testing.assert_array_equal(
        component_bits(result.orders.values), component_bits(record.values)
    )


def test_zero_rows_and_no_hidden_normalization() -> None:
    record = response(api)
    record.values[2] = 0
    result = adapt(
        record,
        calibration_carrier_bins=(2, -1),
        specimen_carrier_bins=(2, -1),
        coordinate_offset_yx=(-9, 14),
        phase_reference_shift_rad=0.25,
    )
    rho = Fraction(2 * (4 - 9), 5) - Fraction(6 + 14, 7)
    assert_rotation(result.orders.values, record.values, rho, 0.25)
    assert np.all(result.orders.values[2] == 0)
    assert result.orders.values[0, 1, 2, 3] == record.values[0, 1, 2, 3]


def test_safe_extreme_rotation_and_selected_only_range() -> None:
    record = response(api, (3, 3, 3), (1.0,) * 3)
    record.values[:] = 0
    record.values[1:, 0, 0, 0] = complex(FMAX, FMAX)  # Unselected, rotating would overflow.
    record.values[1:, 1, 1, 1] = complex(FMAX / 4, FMAX / 4)
    kwargs = dict(
        target_shape_zyx=(1, 1, 1),
        target_voxel_size_um=(Q, FMAX, 0.1),
        phase_reference_shift_rad=math.pi / 4,
    )
    before = snapshot(record)
    result = adapt(record, **kwargs)
    expected = selected(record, (1, 1, 1), kwargs["target_voxel_size_um"])
    assert_rotation(result.orders.values, expected, Fraction(), math.pi / 4)
    with localcontext() as ctx:
        ctx.prec = 420
        for m in (1, 2):
            re, im, bound = rotated(expected[m, 0, 0, 0], m, Fraction(), math.pi / 4)
            assert max(abs(re), abs(im)) + bound < Decimal.from_float(FMAX)
    assert snapshot(record) == before
    record.values[1, 1, 1, 1] = complex(FMAX, FMAX)
    before_rejection = snapshot(record)
    reject(record, "unrepresentable_empirical_transfer", **kwargs)
    assert snapshot(record) == before_rejection
    record.values[1, 1, 1, 1] = complex(FMAX, 0)
    # The strict sufficient inequality fails at identity. Acceptance is still mandatory identity.
    adapt(record, **(kwargs | {"phase_reference_shift_rad": 0.0}))


def test_all_source_fields_validated_before_selection() -> None:
    base = response(api, (3, 3, 3), (1.0,) * 3)
    changes: list[dict[str, Any]] = []
    values = base.values.copy()
    values[2, 0, 0, 0] = complex(math.nan, 0)
    changes.append(dict(values=values))
    frequency = base.fx_per_um.copy()
    frequency[0] = math.inf
    changes.extend(
        [dict(fx_per_um=frequency), dict(origin_zyx=(3, 0, 0)), dict(voxel_size_um=(0, 1, 1))]
    )
    for change in changes:
        record = dataclasses.replace(base, **change)
        before = snapshot(record)
        reject(record, "invalid_empirical_transfer_response", target_shape_zyx=(1, 1, 1))
        assert snapshot(record) == before


class ArraySubclass(np.ndarray):
    """Unsupported ndarray-derived representation."""


class TupleSubclass(tuple):
    """Unsupported derived metadata container."""


class FloatConversion(int):
    """A real scalar that raises at its ordinary float-conversion boundary."""

    outcome: Any = ValueError("conversion marker")

    def __float__(self) -> float:
        """Raise a configured conversion or unrelated exception."""
        raise self.outcome


class WarningFloat(float):
    """A permitted real scalar with an unrelated warning on conversion."""

    def __float__(self) -> float:
        """Return zero while making warning preservation observable."""
        warnings.warn("unrelated declaration warning", UserWarning, stacklevel=2)
        return 0.0


def test_record_type_subclass_and_direct_algebraic_domain() -> None:
    base = response(api)
    reject(dataclasses.asdict(base), "invalid_empirical_transfer_response")

    class Derived(api.EmpiricalVolumeResponse):
        pass

    record = Derived(**{f.name: getattr(base, f.name) for f in dataclasses.fields(base)})
    record.values[:] = 0
    record.values[1, 0, 1, 2] = -2 + 3j  # Non-Hermitian, zero DC, no physical assertion.
    np.testing.assert_array_equal(adapt(record).orders.values, record.values)


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "real",
        "complex64",
        "bool",
        "rank",
        "orders",
        "empty",
        "nan",
        "imag_inf",
    ],
)
def test_source_value_rejections(kind: str) -> None:
    base = response(api)
    values: Any = base.values.copy()
    if kind == "list":
        values = values.tolist()
    elif kind == "subclass":
        values = values.view(ArraySubclass)
    elif kind == "masked":
        values = np.ma.array(values)
    elif kind in ("real", "complex64", "bool"):
        values = values.real.astype(
            {"real": np.float64, "complex64": np.complex64, "bool": np.bool_}[kind]
        )
    elif kind == "rank":
        values = values[0]
    elif kind == "orders":
        values = values[:2]
    elif kind == "empty":
        values = values[:, :0]
    elif kind == "nan":
        values.real[2, 0, 0, 0] = math.nan
    else:
        values.imag[2, 0, 0, 0] = math.inf
    reject(dataclasses.replace(base, values=values), "invalid_empirical_transfer_response")


@pytest.mark.parametrize("field", ["fz_per_um", "fy_per_um", "fx_per_um"])
@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "float32",
        "complex",
        "rank",
        "length",
        "nan",
        "inf",
        "reverse",
        "repeat",
        "off_dc_zero",
        "dc_nonzero",
        "budget",
    ],
)
def test_source_coordinate_rejections(field: str, kind: str) -> None:
    base = response(api)
    v: Any = getattr(base, field).copy()
    if kind == "list":
        v = v.tolist()
    elif kind == "subclass":
        v = v.view(ArraySubclass)
    elif kind == "masked":
        v = np.ma.array(v)
    elif kind in ("float32", "complex"):
        v = v.astype(np.float32 if kind == "float32" else np.complex128)
    elif kind == "rank":
        v = v[None]
    elif kind == "length":
        v = v[:-1]
    elif kind == "nan":
        v[0] = math.nan
    elif kind == "inf":
        v[-1] = math.inf
    elif kind == "reverse":
        v = v[::-1]
    elif kind == "repeat":
        v[0] = v[1]
    elif kind == "off_dc_zero":
        v[0] = 0
    elif kind == "dc_nonzero":
        v[len(v) // 2] = Q
    else:
        v[0] *= 1 + 64 * EPS
    reject(dataclasses.replace(base, **{field: v}), "invalid_empirical_transfer_response")


@pytest.mark.parametrize("field", ["voxel_size_um", "origin_zyx"])
@pytest.mark.parametrize(
    "kind",
    [
        "array",
        "tuple_subclass",
        "short",
        "long",
        "bool",
        "complex",
        "string",
        "nonfinite",
        "negative",
        "zero_or_edge",
        "float_origin",
        "conversion_overflow",
    ],
)
def test_source_metadata_rejections(field: str, kind: str) -> None:
    base = response(api)
    v: Any = list(getattr(base, field))
    if kind == "array":
        v = np.array(v)
    elif kind == "tuple_subclass":
        v = TupleSubclass(v)
    elif kind == "short":
        v = v[:2]
    elif kind == "long":
        v.append(1)
    else:
        v[0] = {
            "bool": True,
            "complex": 1 + 0j,
            "string": "1",
            "nonfinite": math.inf,
            "negative": -1,
            "zero_or_edge": 0 if field == "voxel_size_um" else 3,
            "float_origin": 1.0 if field == "origin_zyx" else math.nan,
            "conversion_overflow": 10**1000,
        }[kind]
    reject(dataclasses.replace(base, **{field: v}), "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "field,code",
    [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("specimen_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset"),
        ("target_shape_zyx", "invalid_empirical_transfer_target_shape"),
        ("target_voxel_size_um", "invalid_empirical_transfer_target_voxel_size"),
    ],
)
@pytest.mark.parametrize(
    "kind",
    ["array", "tuple_subclass", "short", "long", "bool", "complex", "string", "nested", "scalar"],
)
def test_declaration_container_and_scalar_grammar(field: str, code: str, kind: str) -> None:
    base = response(api)
    v: Any = list(declarations(base)[field])
    if kind == "array":
        v = np.array(v)
    elif kind == "tuple_subclass":
        v = TupleSubclass(v)
    elif kind == "short":
        v.pop()
    elif kind == "long":
        v.append(1)
    elif kind == "scalar":
        v = 1
    else:
        v[0] = {"bool": np.bool_(False), "complex": 1 + 0j, "string": "1", "nested": [1]}[kind]
    reject(base, code, **{field: v})


@pytest.mark.parametrize(
    "field,code",
    [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("specimen_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset"),
        ("target_shape_zyx", "invalid_empirical_transfer_target_shape"),
    ],
)
def test_integer_declarations_never_coerce_float(field: str, code: str) -> None:
    base = response(api)
    v = list(declarations(base)[field])
    v[0] = 1.0
    reject(base, code, **{field: v})


@pytest.mark.parametrize("bad", [0, -1, np.iinfo(np.intp).max + 1])
def test_target_extent_native_limits(bad: int) -> None:
    reject(response(api), "invalid_empirical_transfer_target_shape", target_shape_zyx=(bad, 5, 7))


@pytest.mark.parametrize(
    "bad",
    [False, np.bool_(True), 1j, "0", [0], np.array(0), math.nan, math.inf, -math.inf, 10**1000],
)
def test_phase_rejections(bad: Any) -> None:
    reject(response(api), "invalid_empirical_transfer_phase_shift", phase_reference_shift_rad=bad)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf, -math.inf, 10**1000])
def test_target_spacing_rejections(bad: Any) -> None:
    reject(
        response(api),
        "invalid_empirical_transfer_target_voxel_size",
        target_voxel_size_um=(bad, 0.25, 0.125),
    )


@pytest.mark.parametrize("bad", [None, "", " \t\n", 1, b"pair"])
def test_source_label_rejections(bad: Any) -> None:
    reject(response(api), "invalid_otf_source", source=bad)


def test_positive_numpy_scalars_lists_unsigned_and_underflow() -> None:
    record = response(api, (1, 1, 1), (1.0,) * 3, (0, 0, 0))
    record = dataclasses.replace(
        record,
        voxel_size_um=[np.int64(1), np.float32(1), np.float64(1)],
        origin_zyx=[np.uint64(0), np.int32(0), 0],
    )
    for delta in (np.int64(-2), np.float32(0.25), np.float64(-0.0)):
        result = adapt(
            record,
            target_shape_zyx=[np.int32(1), np.uint64(1), 1],
            target_voxel_size_um=[np.int64(1), np.float32(1), np.float64(1)],
            calibration_carrier_bins=[np.uint64(2**64 - 1), np.int64(-3)],
            specimen_carrier_bins=[2**64 - 1, -3],
            coordinate_offset_yx=[np.int64(-7), 2**200],
            phase_reference_shift_rad=delta,
        )
        assert result.orders.voxel_size_um == (1.0, 1.0, 1.0)
        assert all(type(x) is int for x in result.provenance["calibration_carrier_bins"])
    # Available wider floating types may underflow only when actually wider on this platform.
    # Q itself is always a valid converted subnormal and never a rejection floor.
    adapt(record, phase_reference_shift_rad=Q, target_voxel_size_um=(Q,) * 3)


@pytest.mark.parametrize(
    "layout", ["readonly", "strided", "reversed", "fortran", "opposite_endian"]
)
def test_layouts_preservation_and_output_ownership(layout: str) -> None:
    base = response(api)
    fields: dict[str, Any] = {}
    for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
        a = getattr(base, name)
        if layout == "readonly":
            a = a.copy()
            a.flags.writeable = False
        elif layout == "fortran":
            a = np.asfortranarray(a)
        elif layout == "opposite_endian":
            a = a.astype(a.dtype.newbyteorder("S"))
        else:
            shape = list(a.shape)
            shape[-1] *= 2
            backing = np.empty(shape, dtype=a.dtype)
            a = backing[..., ::-2] if layout == "reversed" else backing[..., ::2]
            a[...] = getattr(base, name)
        fields[name] = a
    record = dataclasses.replace(base, **fields)
    before = snapshot(record)
    first, second = adapt(record), adapt(record)
    assert snapshot(record) == before
    outputs = [
        first.orders.values,
        first.orders.fz_per_um,
        first.orders.fy_per_um,
        first.orders.fx_per_um,
    ]
    inputs = list(fields.values())
    for i, array in enumerate(outputs):
        assert array.dtype == (np.dtype(np.complex128) if i == 0 else np.dtype(np.float64))
        assert (
            array.dtype.isnative
            and array.flags.c_contiguous
            and array.flags.owndata
            and array.flags.writeable
        )
        for other in (
            inputs
            + outputs[:i]
            + [
                second.orders.values,
                second.orders.fz_per_um,
                second.orders.fy_per_um,
                second.orders.fx_per_um,
            ]
        ):
            assert not np.shares_memory(array, other)
    np.testing.assert_array_equal(
        component_bits(first.orders.values), component_bits(record.values)
    )
    first.orders.values[:] = 17
    first.orders.fx_per_um[:] = 0
    assert snapshot(record) == before
    reject(record, "mismatched_empirical_transfer_carrier", calibration_carrier_bins=(0, 1))
    assert snapshot(record) == before


def test_output_schema_provenance_snapshots_and_frozen_bindings() -> None:
    record = response(api, (9, 15, 21), (0.5, 0.25, 0.125))
    shape = [3, 5, 7]
    spacing = [1.5, 0.75, 0.375]
    carrier = [np.uint64(2), np.int64(-3)]
    offset = [np.int64(-23), 2**200]
    kwargs = dict(
        target_shape_zyx=shape,
        target_voxel_size_um=spacing,
        calibration_carrier_bins=carrier,
        specimen_carrier_bins=carrier,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=-0.0,
        source="  physical pairing is caller-assumed; not parsed  ",
    )
    result = adapt(record, **kwargs)
    second = adapt(record, **kwargs)
    assert {f.name for f in dataclasses.fields(result)} == {"orders", "provenance"}
    assert {f.name for f in dataclasses.fields(result.orders)} == {
        "values",
        "fz_per_um",
        "fy_per_um",
        "fx_per_um",
        "voxel_size_um",
        "origin_zyx",
        "source",
    }
    assert result.orders.values.shape == (3, 3, 5, 7)
    assert result.orders.origin_zyx == (0, 0, 0)
    assert result.orders.voxel_size_um == tuple(spacing)
    assert all(type(x) is float for x in result.orders.voxel_size_um)
    assert all(type(x) is int for x in result.orders.origin_zyx)
    assert result.orders.source == kwargs["source"]
    expected = dict(
        sampling="exact_shared_native_nodes_v1",
        source_shape_zyx=(9, 15, 21),
        source_voxel_size_um=(0.5, 0.25, 0.125),
        source_origin_zyx=(8, 14, 20),
        source_indices_zyx=tuple(
            indices(c, d, s, t)
            for c, d, s, t in zip((9, 15, 21), record.voxel_size_um, shape, spacing, strict=True)
        ),
        calibration_carrier_bins=(2, -3),
        specimen_carrier_bins=(2, -3),
        coordinate_offset_yx=(-23, 2**200),
        phase_reference_shift_rad=-0.0,
    )
    assert type(result.provenance) is dict
    assert result.provenance == expected
    assert math.copysign(1, result.provenance["phase_reference_shift_rad"]) == -1
    for key in expected:
        if key not in ("sampling", "phase_reference_shift_rad"):
            assert type(result.provenance[key]) is tuple
    for key in (
        "source_shape_zyx",
        "source_origin_zyx",
        "calibration_carrier_bins",
        "specimen_carrier_bins",
        "coordinate_offset_yx",
    ):
        assert all(type(x) is int for x in result.provenance[key])
    assert all(type(x) is float for x in result.provenance["source_voxel_size_um"])
    assert type(result.provenance["phase_reference_shift_rad"]) is float
    assert all(
        type(axis) is tuple and all(type(i) is int for i in axis)
        for axis in result.provenance["source_indices_zyx"]
    )
    shape[0] = 1
    spacing[0] = 8
    carrier[0] = 99
    offset[0] = 77
    record.values[:] = 42
    assert result.provenance == expected
    result.provenance["extra"] = 1
    assert "extra" not in second.provenance
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        result.orders = second.orders
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        del result.provenance
    wrapper = api.SharedNodeVolumeTransfer(orders="opaque", provenance={})
    assert wrapper.orders == "opaque"  # Direct construction adds no validation.


@pytest.mark.parametrize("failure", [TypeError, ValueError, OverflowError])
@pytest.mark.parametrize(
    "field,code",
    [
        ("phase_reference_shift_rad", "invalid_empirical_transfer_phase_shift"),
        ("target_voxel_size_um", "invalid_empirical_transfer_target_voxel_size"),
        ("source_spacing", "invalid_empirical_transfer_response"),
    ],
)
def test_expected_conversion_translation(failure: type[Exception], field: str, code: str) -> None:
    record = response(api)
    value = FloatConversion(1)
    value.outcome = failure("conversion marker")
    if field == "source_spacing":
        reject(dataclasses.replace(record, voxel_size_um=(value, 0.25, 0.125)), code)
    else:
        reject(
            record,
            code,
            **{field: value if field == "phase_reference_shift_rad" else (value, 0.25, 0.125)},
        )


@pytest.mark.parametrize("failure", [MemoryError, RuntimeError, LookupError])
def test_unrelated_conversion_exceptions_propagate_without_dependency_seam(
    failure: type[Exception],
) -> None:
    value = FloatConversion(1)
    value.outcome = failure("unrelated conversion marker")
    with pytest.raises(failure, match="unrelated conversion marker") as error:
        adapt(response(api), phase_reference_shift_rad=value)
    assert error.value is value.outcome


@pytest.mark.parametrize("policy", ["raise", "warn", "ignore"])
def test_arithmetic_policy_and_unrelated_warnings(
    policy: Literal["raise", "warn", "ignore"],
) -> None:
    record = response(api, (1, 1, 1), (1.0,) * 3)
    record.values[:] = complex(FMAX / 4, FMAX / 4)
    with np.errstate(all=policy), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        old_filters = list(warnings.filters)
        old_mode = np.geterr().copy()
        adapt(record, phase_reference_shift_rad=FMAX, target_voxel_size_um=(Q, FMAX, 1.0))
        reject(record, "invalid_empirical_transfer_phase_shift", phase_reference_shift_rad=10**1000)
        record.values[1] = complex(FMAX, FMAX)
        reject(record, "unrepresentable_empirical_transfer", phase_reference_shift_rad=math.pi / 4)
        adapt(record, phase_reference_shift_rad=WarningFloat(0))
        assert np.geterr() == old_mode
        assert warnings.filters == old_filters
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert any(
        issubclass(w.category, UserWarning) and str(w.message) == "unrelated declaration warning"
        for w in caught
    )


def test_validation_geometry_and_carrier_precede_range() -> None:
    record = response(api, (9, 9, 9), (1.0,) * 3)
    record.values[1:] = complex(FMAX, FMAX)
    reject(
        record,
        "incomplete_empirical_transfer_coverage",
        target_shape_zyx=(5, 5, 5),
        phase_reference_shift_rad=math.pi / 4,
    )
    reject(
        record,
        "incompatible_empirical_transfer_negation",
        target_shape_zyx=(4, 4, 4),
        target_voxel_size_um=(2.25,) * 3,
        phase_reference_shift_rad=math.pi / 4,
    )
    reject(
        record,
        "mismatched_empirical_transfer_carrier",
        calibration_carrier_bins=(1, 0),
        phase_reference_shift_rad=math.pi / 4,
    )


def test_existing_same_grid_adapter_compatibility() -> None:
    record = response(api)
    old = api.adapt_empirical_volume_response(
        record,
        carrier_bins=(-2, 3),
        coordinate_offset_yx=(7, -9),
        phase_reference_shift_rad=-0.375,
        source="pair",
    )
    new = adapt(
        record,
        calibration_carrier_bins=(-2, 3),
        specimen_carrier_bins=(-2, 3),
        coordinate_offset_yx=(7, -9),
        phase_reference_shift_rad=-0.375,
        source="pair",
    ).orders
    # Equality is by mathematical budgets, not identical backend organization.
    rho = Fraction(-2 * (4 + 7), 5) + Fraction(3 * (6 - 9), 7)
    assert_rotation(old.values, record.values, rho, -0.375)
    assert_rotation(new.values, record.values, rho, -0.375)
    assert old.origin_zyx == record.origin_zyx and new.origin_zyx == (0, 0, 0)


def test_reconstruction_range_remains_separate_from_adapter_acceptance() -> None:
    record = response(api, (1, 1, 1), (1.0,) * 3)
    record.values[:] = FMAX
    adapted = adapt(record)
    phases = np.array([2 * math.pi * p / 5 for p in range(5)])
    with pytest.raises(api.SimreconError) as error:
        api.reconstruct_volume(
            np.zeros((1, 5, 1, 1, 1)),
            order_otfs=(adapted.orders,),
            phases_rad=phases[None],
            carriers_bins=np.array([[0, 0]]),
            gains=np.array([2.0]),
            regularization=0.25,
            output_shape_yx=(1, 1),
            apodization=np.zeros((1, 1, 1)),
        )
    assert error.value.code == "unrepresentable_volume_reconstruction"


def test_even_shared_nyquist_preserves_complex_lift() -> None:
    record = response(api, (1, 1, 12), (0.5,) * 3)
    record.values[:] = 0
    record.values[0] = 1
    adapted = adapt(record, target_shape_zyx=(1, 1, 4))
    phases = np.array([2 * math.pi * p / 5 for p in range(5)])
    images = np.broadcast_to((-1.0) ** np.arange(4), (5, 1, 1, 4)).copy()
    actual = api.reconstruct_volume(
        images[None],
        order_otfs=(adapted.orders,),
        phases_rad=phases[None],
        carriers_bins=np.array([[0, 0]]),
        gains=np.array([1.0]),
        regularization=0.0,
        output_shape_yx=(1, 8),
        apodization=np.ones((1, 1, 8)),
    )
    expected = np.exp(-2j * np.pi * 2 * np.arange(8) / 8)[None, None]
    _, beta_v = reconstruction_budget(images, phases, (1, 1, 8))
    np.testing.assert_allclose(actual.volume, expected, rtol=0, atol=beta_v)
    assert np.max(abs(actual.volume.imag)) > 0.9


@pytest.mark.parametrize(
    "nc,ns,spacing,carrier_c,carrier_s",
    [
        ((3, 5, 7), (3, 5, 7), (0.5, 0.25, 0.125), (0, 1), (0, 1)),
        ((3, 12, 24), (3, 4, 8), (0.5, 0.25, 0.125), (0, 3), (0, 1)),
        ((1, 9, 15), (1, 3, 5), (0.5, 0.25, 0.125), (0, 3), (0, 1)),
    ],
)
def test_reconstruction_independent_stored_estimator(
    nc: Any, ns: Any, spacing: Any, carrier_c: Any, carrier_s: Any
) -> None:
    record = response(api, nc, spacing)
    record.values[:] /= max(1, np.max(abs(record.values.real)) * 4)
    result = adapt(
        record,
        target_shape_zyx=ns,
        calibration_carrier_bins=carrier_c,
        specimen_carrier_bins=carrier_s,
        coordinate_offset_yx=(4, -7),
        phase_reference_shift_rad=-0.375,
    )
    phases = np.array([0.0, 0.9, 2.1, 3.5, 5.2])
    grid = np.indices(ns)
    dc = 1 + np.cos(2 * np.pi * grid[-1] / ns[-1]) / 8
    c1 = (grid[0] + 1j * (grid[1] + 1)) / 64
    c2 = (grid[2] - 2j) / 128
    basis = phase_basis(phases)
    images = np.array(
        [
            dc
            + 2 * c1.real * row[1]
            - 2 * c1.imag * row[2]
            + 2 * c2.real * row[3]
            - 2 * c2.imag * row[4]
            for row in basis
        ]
    )
    output = (ns[0], ns[1] + 4 * abs(carrier_s[0]), ns[2] + 4 * abs(carrier_s[1]))
    mask = np.ones(output)
    mask[..., 0] = 0.25
    gain = 1.5
    wanted_spectrum, wanted_volume = estimator(
        images, phases, result.orders.values, carrier_s, gain, 0.25, mask
    )
    actual = api.reconstruct_volume(
        images[None],
        order_otfs=(result.orders,),
        phases_rad=phases[None],
        carriers_bins=np.array([carrier_s]),
        gains=np.array([gain]),
        regularization=0.25,
        output_shape_yx=output[1:],
        apodization=mask,
    )
    beta_s, beta_v = reconstruction_budget(images, phases, output)
    np.testing.assert_allclose(actual.spectrum, wanted_spectrum, rtol=0, atol=beta_s)
    np.testing.assert_allclose(actual.volume, wanted_volume, rtol=0, atol=beta_v)
    with pytest.raises(api.SimreconError) as error:
        api.reconstruct_volume(
            images[None],
            order_otfs=(result.orders,),
            phases_rad=phases[None],
            carriers_bins=np.array([carrier_s]),
            gains=np.array([gain]),
            regularization=0.25,
            output_shape_yx=(1, 1),
            apodization=np.ones((ns[0], 1, 1)),
        )
    assert error.value.code == "invalid_volume_reconstruction_output_shape"


def declare_raw(images: np.ndarray, phases: np.ndarray, kind: str) -> Any:
    commands = phases + np.array([0.03, -0.02, 0.05, -0.04, 0.01])
    return api.declare_acquisition(
        (10 + 2 * images)[None],
        config=dict(
            version=1,
            acquisition_kind=kind,
            axes=["orientation", "phase", "z", "y", "x"],
            intensity_unit="counts",
            nominal_phases_rad=[commands.tolist()],
        ),
    )


@pytest.mark.parametrize(
    "bead,brightness,roll,alpha_c,alpha_s,gain",
    [
        ((10, 13, 16), 600.0, (0, 0, 0), 0.25, -0.125, 1.0),
        ((3, 5, 7), 1200.0, (2, -3, 4), -0.375, 0.5, 1.5),
    ],
)
def test_different_grid_raw_physical_composition(
    bead: Any, brightness: float, roll: Any, alpha_c: float, alpha_s: float, gain: float
) -> None:
    nc, ns = (21, 27, 33), (7, 9, 11)
    dc, ds = (0.125, 0.0625, 0.03125), (0.375, 0.1875, 0.09375)
    physical_phases = np.array([2 * math.pi * p / 5 for p in range(5)])
    calibration_phases = physical_phases.copy()
    if brightness != 600:
        calibration_phases += np.array([0.0, 0.04, -0.02, 0.05, -0.03])
    offset = (2, -3)
    calibration_signal = physical_bead(nc, bead, brightness, offset, calibration_phases)
    calibration_signal = np.roll(calibration_signal, roll, axis=(1, 2, 3))
    acquisition = declare_raw(calibration_signal, calibration_phases, "sim_beads")
    calibrated = api.calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=10,
        response=2,
        output_unit="electrons",
        phases_rad=calibration_phases + alpha_c,
        voxel_size_um=dc,
    )
    observed = tuple((b + t) % n for b, t, n in zip(bead, roll, nc, strict=True))
    assert calibrated.response.origin_zyx == observed
    stored_calibration = (acquisition.data[0].astype(np.float64) - 10) / 2
    separation_bound = 8192 * 5 * EPS * float(np.max(abs(stored_calibration))) + 8 * Q
    with localcontext() as ctx:
        ctx.prec = 70
        independent_components = decimal_components(
            stored_calibration, calibration_phases + alpha_c
        )
        convert = np.vectorize(lambda z: z.native(), otypes=[np.complex128])
        for actual_component, expected_component in zip(
            (calibrated.components.dc, calibrated.components.c1, calibrated.components.c2),
            independent_components,
            strict=True,
        ):
            wanted = convert(expected_component)
            np.testing.assert_allclose(
                actual_component.real, wanted.real, rtol=0, atol=separation_bound
            )
            np.testing.assert_allclose(
                actual_component.imag, wanted.imag, rtol=0, atol=separation_bound
            )
    stored_empirical, empirical_allowances = empirical_expected(
        (calibrated.components.dc, calibrated.components.c1, calibrated.components.c2),
        observed,
        ns,
    )
    picked = selected(calibrated.response, ns, ds)
    for order in range(3):
        np.testing.assert_allclose(
            picked[order], stored_empirical[order], rtol=0, atol=empirical_allowances[order]
        )
    corrected_offset = (offset[0] - roll[1], offset[1] - roll[2])
    transfer = adapt(
        calibrated.response,
        target_shape_zyx=ns,
        target_voxel_size_um=ds,
        calibration_carrier_bins=(0, 1),
        specimen_carrier_bins=(0, 1),
        coordinate_offset_yx=corrected_offset,
        phase_reference_shift_rad=alpha_s - alpha_c,
    )
    rho = Fraction(observed[2] + corrected_offset[1], nc[2])
    assert_rotation(transfer.orders.values, picked, rho, alpha_s - alpha_c)
    analytic = polynomial_transfer(ns, alpha_s)
    # RPC propagation: separator error per coordinate, peak/mass stability, EVR, ETC.
    m = math.prod(nc)
    bmax = float(np.max(calibration_signal))
    separation = 8192 * 5 * EPS * bmax + 8 * Q
    assert m * separation < brightness
    h = kernel(nc)
    peak_margin = brightness * (h.flat[0] - np.partition(h.ravel(), -2)[-2])
    assert peak_margin > 2 * separation
    empirical = 512 * m * EPS * 2 + 16 * m * Q
    composite = (
        (m * separation * 2 + m * separation) / (brightness - m * separation)
        + empirical
        + 256 * EPS
    )
    # Camera rounding/generator trig is much smaller than this inherited conservative budget.
    assert composite < 1e-4
    np.testing.assert_allclose(transfer.orders.values, analytic, rtol=0, atol=composite)
    specimen_signal, specimen = physical_specimen(ns, physical_phases)
    specimen_acquisition = declare_raw(gain * specimen_signal, physical_phases, "specimen_sim")
    corrected = api.correct_linear_response(
        specimen_acquisition, offset=10, response=2, output_unit="electrons"
    )
    images = corrected.data[0]
    phases = physical_phases + alpha_s
    mask = np.ones((7, 9, 15))
    expected_s, expected_v = estimator(
        images, phases, transfer.orders.values, (0, 1), gain, 0.25, mask
    )
    actual = api.reconstruct_volume(
        images[None],
        order_otfs=(transfer.orders,),
        phases_rad=phases[None],
        carriers_bins=np.array([[0, 1]]),
        gains=np.array([gain]),
        regularization=0.25,
        output_shape_yx=(9, 15),
        apodization=mask,
    )
    beta_s, beta_v = reconstruction_budget(images, phases, mask.shape)
    assert beta_s < 1e-6 and beta_v < 1e-3
    np.testing.assert_allclose(actual.spectrum, expected_s, rtol=0, atol=beta_s)
    np.testing.assert_allclose(actual.volume, expected_v, rtol=0, atol=beta_v)
    # Generator truth lives on the preserved-FOV output grid. Ridge causes genuine bias.
    out_grid = np.indices(mask.shape)
    unrounded_truth = 1 + sum(np.cos(2 * np.pi * out_grid[a] / mask.shape[a]) for a in range(3)) / 8
    ridge_bias = float(np.max(abs(expected_v - unrounded_truth)))
    assert ridge_bias > 0.1
    assert np.min(specimen) >= 0.625 - 4 * EPS
    # Deliberately unequal specimen kernel: same geometry still accepts the declared pair.
    unequal_signal, _ = physical_specimen(ns, physical_phases, unequal=True)
    unequal_images = ((10 + 2 * gain * unequal_signal) - 10) / 2
    unequal_s, unequal_v = estimator(
        unequal_images, phases, transfer.orders.values, (0, 1), gain, 0.25, mask
    )
    paired = api.reconstruct_volume(
        unequal_images[None],
        order_otfs=(transfer.orders,),
        phases_rad=phases[None],
        carriers_bins=np.array([[0, 1]]),
        gains=np.array([gain]),
        regularization=0.25,
        output_shape_yx=(9, 15),
        apodization=mask,
    )
    unequal_beta_s, unequal_beta_v = reconstruction_budget(unequal_images, phases, mask.shape)
    np.testing.assert_allclose(paired.spectrum, unequal_s, rtol=0, atol=unequal_beta_s)
    np.testing.assert_allclose(paired.volume, unequal_v, rtol=0, atol=unequal_beta_v)
    assert np.max(abs(unequal_v - expected_v)) > 1e-4


@pytest.mark.parametrize("nc_x,ns_x,kc,ks", [(12, 4, 0, 0), (24, 8, 3, 1)])
def test_even_subset_physical_shared_displacements(nc_x: int, ns_x: int, kc: int, ks: int) -> None:
    nc, ns = (3, 3, nc_x), (3, 3, ns_x)
    spacing = (0.5, 0.25, 0.125)
    phases = np.array([2 * math.pi * p / 5 for p in range(5)])
    hc, hs = np.zeros(nc), np.zeros(ns)
    hc[0, 0, :2] = hs[0, 0, :2] = (0.75, 0.25)
    bead = np.zeros(nc)
    bead[1, 1, nc_x - 3] = 600
    raw_bead = declare_raw(discrete_forward(bead, hc, kc, phases), phases, "sim_beads")
    calibrated = api.calibrate_raw_point_bead(
        raw_bead,
        group={"orientation": 0},
        offset=10,
        response=2,
        output_unit="electrons",
        phases_rad=phases + 0.25,
        voxel_size_um=spacing,
    )
    adapted = adapt(
        calibrated.response,
        target_shape_zyx=ns,
        target_voxel_size_um=spacing,
        calibration_carrier_bins=(0, kc),
        specimen_carrier_bins=(0, ks),
        phase_reference_shift_rad=-0.375,
    )
    expected = np.empty((3, *ns), complex)
    for index in np.ndindex(ns):
        kx = index[2] - ns_x // 2
        base = 0.75 + 0.25 * np.exp(-2j * np.pi * kx / ns_x)
        expected[(0, *index)] = base
        expected[(1, *index)] = base * (2 / 3) * np.exp(0.125j)
        expected[(2, *index)] = base / 3 * np.exp(0.25j)
    # RPC/EVR propagation for these small, nonnegative, well-conditioned examples.
    count = math.prod(nc)
    sep = 8192 * 5 * EPS * float(np.max(raw_bead.data))
    calibration_bound = 3 * count * sep / (600 - count * sep) + 1024 * count * EPS
    np.testing.assert_allclose(adapted.orders.values, expected, rtol=0, atol=calibration_bound)
    x = np.indices(ns)[2]
    specimen = 1 + np.cos(2 * np.pi * x / ns_x) / 8
    images = discrete_forward(specimen, hs, ks, phases)
    specimen_raw = declare_raw(images, phases, "specimen_sim")
    corrected = api.correct_linear_response(
        specimen_raw, offset=10, response=2, output_unit="electrons"
    )
    images = corrected.data[0]
    output = (3, 3, ns_x + 4 * ks)
    mask = np.ones(output)
    wanted_s, wanted_v = estimator(
        images, phases - 0.125, adapted.orders.values, (0, ks), 1.0, 0.25, mask
    )
    actual = api.reconstruct_volume(
        images[None],
        order_otfs=(adapted.orders,),
        phases_rad=(phases - 0.125)[None],
        carriers_bins=np.array([[0, ks]]),
        gains=np.array([1.0]),
        regularization=0.25,
        output_shape_yx=output[1:],
        apodization=mask,
    )
    beta_s, beta_v = reconstruction_budget(images, phases - 0.125, output)
    np.testing.assert_allclose(actual.spectrum, wanted_s, rtol=0, atol=beta_s)
    np.testing.assert_allclose(actual.volume, wanted_v, rtol=0, atol=beta_v)


def test_roll_compensation_and_physical_movement_are_distinct() -> None:
    shape = (3, 5, 7)
    base = response(api, shape, origin=(1, 2, 3))
    roll = (1, 1, 2)
    carrier, offset = (1, -2), (4, -3)
    rolled = dataclasses.replace(
        base,
        origin_zyx=tuple((b + t) % n for b, t, n in zip(base.origin_zyx, roll, shape, strict=True)),
    )
    a = adapt(
        base,
        calibration_carrier_bins=carrier,
        specimen_carrier_bins=carrier,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=0.25,
    )
    b = adapt(
        rolled,
        calibration_carrier_bins=carrier,
        specimen_carrier_bins=carrier,
        coordinate_offset_yx=(offset[0] - roll[1], offset[1] - roll[2]),
        phase_reference_shift_rad=0.25,
    )
    lmax = float(np.max(abs(base.values.real) + abs(base.values.imag)))
    np.testing.assert_allclose(
        a.orders.values, b.orders.values, rtol=0, atol=256 * EPS * lmax + 32 * Q
    )
    uncompensated = adapt(
        rolled,
        calibration_carrier_bins=carrier,
        specimen_carrier_bins=carrier,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=0.25,
    )
    assert np.max(abs(uncompensated.orders.values[1:] - a.orders.values[1:])) > 0.1
    # A physical bead move at fixed illumination origin changes raw intensities.
    phases = np.array([2 * math.pi * p / 5 for p in range(5)])
    raw = physical_bead(shape, (1, 2, 3), 600, offset, phases)
    moved = physical_bead(shape, (1, 3, 5), 600, offset, phases)
    assert np.max(abs(moved - np.roll(raw, (1, 2), axis=(2, 3)))) > 0.1
