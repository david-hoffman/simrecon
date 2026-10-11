"""Blind contract tests for empirical-transfer-consumption-v1, C01--C20.

An absent public adapter is collection/setup evidence, never product-red.
All numerical expectations come from the independent owned observer fixture.
"""

from __future__ import annotations

import warnings
from decimal import localcontext
from fractions import Fraction
from itertools import combinations
from typing import Any

import numpy as np
import pytest

import simrecon as public
from empirical_transfer_fixture import (
    EPS,
    FIELDS,
    PRECISION,
    D,
    Q,
    assert_close,
    assert_rotation,
    direct_dft,
    estimator,
    exact_separation,
    exposures,
    forward_specimen,
    grid,
    multiply,
    pair,
    point_model,
    record,
    represented,
    represented_basis,
    revised,
    root,
    rotation,
)

# Resolve only the public export. No private imports or implementation inspection.
ADAPTER_EXPORT = "adapt_empirical_volume_response"
adapt: Any = getattr(public, ADAPTER_EXPORT)
SOURCE = "  caller pairing: signed response / no physical certificate  "
DEFAULT = {
    "carrier_bins": (1, -1),
    "coordinate_offset_yx": (0, 0),
    "phase_reference_shift_rad": 0.375,
    "source": SOURCE,
}


def invoke(response=None, **changes):
    options = DEFAULT | changes
    return adapt(record() if response is None else response, **options)


def snapshots(response):
    return (
        {
            name: (
                item.tobytes(),
                item.dtype.str,
                item.shape,
                item.strides,
                item.flags.writeable,
            )
            for name in FIELDS
            if isinstance(item := getattr(response, name), np.ndarray)
        },
        tuple(repr(getattr(response, name)) for name in FIELDS),
    )


def reject(response, code, **changes):
    before = snapshots(response) if isinstance(response, public.EmpiricalVolumeResponse) else None
    with pytest.raises(public.SimreconError) as caught:
        invoke(response, **changes)
    assert caught.value.code == code, f"expected {code}; received {caught.value.code}"
    if before is not None:
        assert snapshots(response) == before, (
            "rejection must preserve all input arrays and metadata"
        )


def test_C01_public_record_binding_and_explicit_declarations():
    response = record()
    out = invoke(response)
    assert isinstance(out, public.VolumeOrderOtf), "existing VolumeOrderOtf result required"
    assert {
        name for name in dir(out) if not name.startswith("_") and not callable(getattr(out, name))
    } == set(FIELDS) | {"source"}, "seven public record fields"
    assert out.source == SOURCE
    assert out.origin_zyx == response.origin_zyx
    for name in (*FIELDS, "source"):
        with pytest.raises((AttributeError, TypeError)):
            setattr(out, name, getattr(out, name))
        with pytest.raises((AttributeError, TypeError)):
            delattr(out, name)
    for missing in DEFAULT:
        options = {name: value for name, value in DEFAULT.items() if name != missing}
        with pytest.raises(TypeError):
            adapt(response, **options)
    with pytest.raises(TypeError):
        adapt(**DEFAULT)
    with pytest.raises(TypeError):
        adapt(response, (1, 2), **DEFAULT)
    with pytest.raises(TypeError):
        adapt(response, **DEFAULT, truth_bead=(1, 2, 3))


@pytest.mark.parametrize(
    ("carrier", "offset", "delta"),
    [
        ((1, -1), (0, 0), 0.375),
        ((-2, 3), (-7, 5), -1.125),
        ((0, 0), (19, -11), 0.5),
        ((1, 1), (0, 1), 0.0),
        ((3, 4), (0, 0), -0.0),
        ((1, 0), (0, 0), 0.0),
        ((0, 1), (0, 0), 0.0),
    ],
)
def test_C02_C04_signed_complex_exact_carrier_rotation(carrier, offset, delta):
    response = record()
    before = snapshots(response)
    result = invoke(
        response, carrier_bins=carrier, coordinate_offset_yx=offset, phase_reference_shift_rad=delta
    )
    assert_rotation(result, response, carrier, offset, delta)
    assert snapshots(response) == before


@pytest.mark.parametrize(
    "carrier,offset",
    [
        ((0, 0), (0, 0)),
        ((3, 4), (0, 0)),
        ((1, -1), (1, 1)),
        ((3 * (2**2048 + 1), 4 * (2**2048 - 1)), (2**1200, -(2**1200))),
    ],
)
@pytest.mark.parametrize("delta", [0.0, -0.0])
def test_C03_identity_copies_signed_zeros_and_nonunit_dc(carrier, offset, delta):
    response = record()
    response.values.real.flat[::4] = -0.0
    response.values.imag.flat[::5] = -0.0
    response.values[0, 1, 1, 2] = -7.25 + 3.5j
    result = invoke(
        response, carrier_bins=carrier, coordinate_offset_yx=offset, phase_reference_shift_rad=delta
    )
    assert result.values.tobytes() == response.values.tobytes(), (
        "exact integral-cycle identity copy"
    )


def test_C04_zero_side_rows_and_zero_nonunit_dc_are_valid():
    response = record()
    response.values[1:] = 0
    response.values[0, 1, 1, 2] = 0
    result = invoke(response)
    assert np.count_nonzero(result.values[1:]) == 0, "zero side transfers must stay exactly zero"
    assert result.values[0].tobytes() == response.values[0].tobytes()


@pytest.mark.parametrize("field", ["carrier_bins", "coordinate_offset_yx"])
@pytest.mark.parametrize(
    "bad",
    [
        None,
        1,
        (),
        (1,),
        (1, 2, 3),
        np.array([1, 2]),
        (1.0, 2),
        (True, 2),
        (np.bool_(False), 2),
        (1 + 0j, 2),
        (np.array(1), 2),
        ("1", 2),
    ],
)
def test_C12_C13_integer_declaration_rejections(field, bad):
    code = (
        "invalid_empirical_transfer_carrier"
        if field == "carrier_bins"
        else "invalid_empirical_transfer_coordinate_offset"
    )
    reject(record(), code, **{field: bad})


class ListSubclass(list):
    """Distinguish exact built-in list containers from subclass containers."""


class TupleSubclass(tuple):
    """Distinguish exact built-in tuple containers from subclass containers."""


@pytest.mark.parametrize("field", ["carrier_bins", "coordinate_offset_yx"])
@pytest.mark.parametrize("container", [ListSubclass([1, 2]), TupleSubclass((1, 2))])
def test_C12_C13_exact_builtin_containers(field, container):
    code = (
        "invalid_empirical_transfer_carrier"
        if field == "carrier_bins"
        else "invalid_empirical_transfer_coordinate_offset"
    )
    reject(record(), code, **{field: container})


@pytest.mark.parametrize(
    "carrier,offset",
    [
        ([np.int8(-1), np.uint8(2)], [np.int32(3), np.int64(-7)]),
        ((np.uint64(2**64 - 1), np.uint64(2**63 + 11)), (np.uint64(2**64 - 3), -(2**90))),
        ((2**1200 + 1, -(2**1300) + 7), (-(2**1100) + 3, 2**1400 + 9)),
        ((3 * (2**1024 + 1) + 1, 4 * (2**1080 + 1) - 1), (3 * 2**1025, -4 * 2**1090)),
        ((0, 0), [2**2048, -(2**2048)]),
    ],
)
def test_C12_C13_exact_huge_signed_unsigned_and_periodic_inputs(carrier, offset):
    response = record()
    result = invoke(response, carrier_bins=carrier, coordinate_offset_yx=offset)
    assert_rotation(result, response, carrier, offset, DEFAULT["phase_reference_shift_rad"])


@pytest.mark.parametrize(
    "bad",
    [
        None,
        True,
        np.bool_(False),
        1 + 0j,
        "0",
        [0],
        np.array(0.0),
        D("0"),
        Fraction(1, 2),
        float("inf"),
        float("-inf"),
        float("nan"),
        2**2000,
    ],
)
def test_C14_phase_scalar_conversion_and_finiteness_rejections(bad):
    reject(record(), "invalid_empirical_transfer_phase_shift", phase_reference_shift_rad=bad)


@pytest.mark.parametrize(
    "delta",
    [
        0,
        -3,
        np.int64(-7),
        np.uint64(2**64 - 1),
        np.float16(0.5),
        np.float32(-0.25),
        np.float64(-0.0),
        np.longdouble(0.625),
        float.fromhex("0x1p-1074"),
        -float.fromhex("0x1p-1074"),
        np.finfo(np.float64).max,
        -np.finfo(np.float64).max,
        2**1000,
    ],
)
def test_C14_huge_finite_subnormal_and_all_scalar_families(delta):
    response = record()
    result = invoke(response, phase_reference_shift_rad=delta)
    assert_rotation(result, response, DEFAULT["carrier_bins"], (0, 0), delta)


@pytest.mark.parametrize("bad", [None, "", " \t\n", 3, b"label"])
def test_C15_nonblank_source_rejected(bad):
    reject(record(), "invalid_otf_source", source=bad)


@pytest.mark.parametrize(
    "source", [" calibration ", "anything opaque; not a verified identifier", "µm / signed Δ"]
)
def test_C15_source_is_opaque_and_unchanged(source):
    assert invoke(record(), source=source).source == source


class ArraySubclass(np.ndarray):
    """An ndarray subclass is outside the plain-array contract."""


@pytest.mark.parametrize("bad", [object(), {}, np.zeros((3, 2, 3, 4))])
def test_C09_nonrecord_rejected(bad):
    reject(bad, "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "bool",
        "real",
        "c64",
        "rank",
        "orders",
        "empty",
        "real_nan",
        "imag_inf",
    ]
    + (["wide"] if np.dtype(np.clongdouble).itemsize > 16 else []),
)
def test_C08_C09_all_value_representation_decisions(kind):
    response = record()
    values: Any = response.values.copy()
    if kind == "list":
        values = values.tolist()
    elif kind == "subclass":
        values = values.view(ArraySubclass)
    elif kind == "masked":
        values = np.ma.array(values)
    elif kind in ("bool", "real", "c64", "wide"):
        target = np.dtype(
            {"bool": np.bool_, "real": np.float64, "c64": np.complex64, "wide": np.clongdouble}[
                kind
            ]
        )
        values = np.zeros(values.shape, dtype=target)
    elif kind == "rank":
        values = values[0]
    elif kind == "orders":
        values = values[:2]
    elif kind == "empty":
        values = values[:, :0]
    elif kind == "real_nan":
        values.real[0, 0, 0, 0] = np.nan
    elif kind == "imag_inf":
        values.imag[2, 1, 2, 3] = np.inf
    reject(
        revised(response, values=values), "invalid_empirical_transfer_response", carrier_bins=(0, 0)
    )


@pytest.mark.parametrize("field", ["fz_per_um", "fy_per_um", "fx_per_um"])
@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "subclass",
        "masked",
        "f32",
        "int",
        "complex",
        "rank",
        "length",
        "nan",
        "inf",
        "reverse",
        "repeat",
        "dc",
        "off_dc_zero",
        "outside_budget",
    ],
)
def test_C10_every_frequency_field_fully_validated(field, kind):
    response = record()
    vector: Any = getattr(response, field).copy()
    if kind == "list":
        vector = vector.tolist()
    elif kind == "subclass":
        vector = vector.view(ArraySubclass)
    elif kind == "masked":
        vector = np.ma.array(vector)
    elif kind in ("f32", "int", "complex"):
        vector = vector.astype({"f32": "f4", "int": "i8", "complex": "c16"}[kind])
    elif kind == "rank":
        vector = vector[None]
    elif kind == "length":
        vector = vector[:-1]
    elif kind in ("nan", "inf"):
        vector[0] = np.nan if kind == "nan" else np.inf
    elif kind == "reverse":
        vector = vector[::-1]
    elif kind == "repeat":
        vector[1] = vector[0]
    elif kind == "dc":
        vector[len(vector) // 2] = np.nextafter(0.0, 1.0)
    elif kind == "off_dc_zero":
        vector[0] = 0
    elif kind == "outside_budget":
        for _ in range(64):
            vector[0] = np.nextafter(vector[0], -np.inf)
    response.values[1:] = 0
    reject(
        revised(response, **{field: vector}),
        "invalid_empirical_transfer_response",
        carrier_bins=(0, 0),
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        np.array([1.0, 1.0, 1.0]),
        ListSubclass([1, 1, 1]),
        (1, 1),
        (1, 1, 1, 1),
        (True, 1, 1),
        (np.bool_(False), 1, 1),
        (1 + 0j, 1, 1),
        ("1", 1, 1),
        (0, 1, 1),
        (-1, 1, 1),
        (np.nan, 1, 1),
        (np.inf, 1, 1),
        (2**2000, 1, 1),
    ],
)
def test_C11_spacing_grammar_and_conversion_rejections(bad):
    reject(revised(record(), voxel_size_um=bad), "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "bad",
    [
        None,
        np.array([0, 0, 0]),
        TupleSubclass((0, 0, 0)),
        (0, 0),
        (0, 0, 0, 0),
        (False, 0, 0),
        (np.bool_(True), 0, 0),
        (0.0, 0, 0),
        (0 + 0j, 0, 0),
        (-1, 0, 0),
        (2, 0, 0),
        (0, 3, 0),
        (0, 0, 4),
        (0, 0, 2**1024),
    ],
)
def test_C11_origin_grammar_and_bounds_rejections(bad):
    reject(revised(record(), origin_zyx=bad), "invalid_empirical_transfer_response")


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((1, 1, 1), (float.fromhex("0x1p-1074"), np.finfo(np.float64).max, 1.0)),
        ((1, 1, 1), (np.int64(2), np.uint64(2**64 - 1), np.longdouble(0.125))),
        ((3, 4, 1), (np.finfo(np.float64).max, np.finfo(np.float64).max, 0.5)),
        ((3, 2, 4), (0.25, 0.5, 0.125)),
        ((2, 3, 4), (float.fromhex("0x1p-1022"), 2.0, 1.0)),
    ],
)
def test_C08_C10_C11_extreme_grids_and_algebraic_positives(shape, spacing):
    vectors = [grid(n, d) for n, d in zip(shape, spacing, strict=True)]
    response = record(
        values=np.full((3, *shape), -0.25 + 0.5j),
        voxel_size_um=list(spacing),
        origin_zyx=[np.int16(0), np.uint64(0), 0],
        **dict(zip(FIELDS[1:4], vectors, strict=True)),
    )
    result = invoke(response)
    assert_rotation(result, response, (1, -1), (0, 0), 0.375)
    assert all(type(x) is float for x in result.voxel_size_um)
    assert all(type(x) is int for x in result.origin_zyx)
    for name in FIELDS[1:4]:
        assert getattr(result, name).tobytes() == getattr(response, name).tobytes()


def test_C10_permitted_frequency_rounding_is_copied_without_recomputation():
    response = record()
    for name in FIELDS[1:4]:
        vector = getattr(response, name)
        for _ in range(7):
            vector[0] = np.nextafter(vector[0], -np.inf)
        vector[len(vector) // 2] = -0.0
    result = invoke(response)
    for name in FIELDS[1:4]:
        assert getattr(result, name).tobytes() == getattr(response, name).tobytes(), (
            "accepted measured frequencies copied exactly"
        )


class ResponseSubclass(public.EmpiricalVolumeResponse):
    """Ordinary frozen response subclasses remain permitted inputs."""


def test_C08_response_subclass_and_scalar_families_are_valid():
    r = record()
    response = ResponseSubclass(**{name: getattr(r, name) for name in FIELDS})
    response = revised(
        response, voxel_size_um=[np.float32(0.25), np.float16(0.5), np.float64(0.125)]
    )
    invoke(ResponseSubclass(**{name: getattr(response, name) for name in FIELDS}))


@pytest.mark.parametrize("layout", ["fortran", "reversed", "strided", "readonly", "big_endian"])
def test_C16_storage_snapshots_ownership_and_call_independence(layout):
    response = record()
    arrays = {name: getattr(response, name) for name in FIELDS[:4]}
    converted = {}
    for name, array in arrays.items():
        if layout == "fortran":
            new = np.asfortranarray(array)
        elif layout == "reversed":
            new = array[::-1].copy()[::-1]
        elif layout == "strided":
            storage = np.empty((*array.shape[:-1], 2 * array.shape[-1]), dtype=array.dtype)
            storage[..., ::2] = array
            new = storage[..., ::2]
        elif layout == "readonly":
            new = array.copy()
            new.flags.writeable = False
        else:
            new = array.astype(array.dtype.newbyteorder(">"))
        converted[name] = new
    response = revised(response, **converted)
    before = snapshots(response)
    first, second = invoke(response), invoke(response)
    assert_rotation(first, response, (1, -1), (0, 0), 0.375)
    outputs = [getattr(call, name) for call in (first, second) for name in FIELDS[:4]]
    for i, output in enumerate(outputs):
        assert type(output) is np.ndarray
        assert output.flags.c_contiguous and output.flags.owndata and output.flags.writeable
        assert output.dtype == np.dtype("c16" if i % 4 == 0 else "f8") and output.dtype.isnative
        assert all(not np.shares_memory(output, original) for original in converted.values())
    for a, b in combinations(outputs, 2):
        assert not np.shares_memory(a, b), "output arrays and calls own separate storage"
    assert snapshots(response) == before
    first.values[:] = 99
    first.fx_per_um[:] = 99
    assert snapshots(response) == before
    assert_rotation(second, response, (1, -1), (0, 0), 0.375)
    reject(response, "invalid_empirical_transfer_phase_shift", phase_reference_shift_rad=np.inf)


@pytest.mark.parametrize(
    "value",
    [
        complex(0.6 * np.finfo(np.float64).max, 0.6 * np.finfo(np.float64).max),
        complex(float.fromhex("0x1p-1074"), -float.fromhex("0x1p-1074")),
        complex(1e-280, -2e-280),
        complex(-1.5, 2.25),
    ],
)
def test_C17_safe_success_extreme_cancellation_and_subnormal_budgets(value):
    # rho=1/8: one cancellation component, one near-max but safely finite component.
    response = record(values=np.full((3, 1, 1, 8), value), origin_zyx=(0, 0, 1))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        maximum = represented(np.finfo(np.float64).max)
        expected = rotation(response, (0, 1), (0, 0), 0.0)
        for index, target in expected.items():
            if index[0] > 0:
                re, im = pair(response.values[index])
                bound = 128 * EPS * (abs(re) + abs(im)) + 16 * Q
                assert all(abs(component) + bound < maximum for component in target), (
                    "fixture satisfies mandatory safe-success margin"
                )
    result = invoke(response, carrier_bins=(0, 1), phase_reference_shift_rad=0.0)
    assert_rotation(result, response, (0, 1), (0, 0), 0.0)


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log", "mixed"])
def test_C18_caller_modes_preserved_for_identity_underflow_and_rejection(mode):
    class Logger:
        def write(self, message):
            raise AssertionError(f"handled arithmetic must not log: {message}")

    def callback(*args):
        raise AssertionError(f"handled arithmetic must not call: {args}")

    previous, old_callback = np.geterr(), np.geterrcall()
    try:
        np.seterrcall(Logger() if mode == "log" else callback)
        if mode == "mixed":
            np.seterr(divide="raise", over="ignore", under="call", invalid="warn")
        else:
            np.seterr(all=mode)
        desired = np.geterr()
        expected_callback = np.geterrcall()
        filters = list(warnings.filters)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            inside_filters = list(warnings.filters)
            maximum = np.finfo(np.float64).max
            identity = record(
                values=np.full((3, 1, 1, 1), complex(maximum, maximum)), origin_zyx=(0, 0, 0)
            )
            result = invoke(identity, carrier_bins=(0, 0), phase_reference_shift_rad=-0.0)
            assert result.values.tobytes() == identity.values.tobytes(), (
                "overflowing complex magnitude is no rejection at identity"
            )
            tiny = record(
                values=np.full((3, 1, 1, 1), complex(float.fromhex("0x1p-1074"), 0)),
                origin_zyx=(0, 0, 0),
            )
            assert_rotation(invoke(tiny, phase_reference_shift_rad=0.7), tiny, (1, -1), (0, 0), 0.7)
            overflow = record(
                values=np.ones((3, 1, 1, 8), dtype=np.complex128), origin_zyx=(0, 0, 1)
            )
            overflow.values[1, 0, 0, 7] = complex(0.8 * maximum, 0.8 * maximum)
            reject(
                overflow,
                "unrepresentable_empirical_transfer",
                carrier_bins=(0, 1),
                phase_reference_shift_rad=0.0,
            )
            reject(
                record(),
                "invalid_empirical_transfer_phase_shift",
                phase_reference_shift_rad=2**2000,
            )
            assert np.geterr() == desired
            assert np.geterrcall() is expected_callback
            assert warnings.filters == inside_filters
            warnings.warn("unrelated observer warning", UserWarning, stacklevel=2)
            assert len(caught) == 1 and caught[0].category is UserWarning, (
                "handled arithmetic emits no RuntimeWarning; unrelated warning remains"
            )
            assert np.geterrcall() is expected_callback
        assert warnings.filters == filters
    finally:
        np.seterr(**previous)
        np.seterrcall(old_callback)


def test_C19_adapter_uses_no_spatial_transform_or_supplied_psf(monkeypatch):
    def prohibited(*args, **kwargs):
        raise AssertionError("adapter must not transform or reinterpret response as a supplied PSF")

    monkeypatch.setattr(np.fft, "fftn", prohibited)
    monkeypatch.setattr(np.fft, "ifftn", prohibited)
    monkeypatch.setattr(public, "prepare_volume_order_otfs", prohibited)
    response = record()
    assert_rotation(invoke(response), response, (1, -1), (0, 0), 0.375)


def check_selected_gauge(
    orders, response, corrected, cal_phases, kernels, alpha_s, delta, offset=(0, 0)
):
    """Triangle bound separates rounded stored-estimator and generator-model truth."""
    shape = corrected.shape[1:]
    exact = exact_separation(corrected, cal_phases)
    assert np.linalg.cond(represented_basis(cal_phases)) <= 10
    with localcontext() as ctx:
        ctx.prec = PRECISION
        count = int(np.prod(shape))
        bmax = represented(np.max(np.abs(corrected)))
        e = 8192 * len(cal_phases) * EPS * bmax + 8 * Q
        dc_values = [exact[0][index][0] for index in np.ndindex(shape)]
        mass = sum(dc_values, D(0))
        assert mass > count * e, "stable positive common-mass margin"
        ranked = sorted(dc_values, reverse=True)
        assert ranked[0] - ranked[1] > 2 * e, "stable unique peak margin"
        transforms = [direct_dft(array, origin=response.origin_zyx) for array in exact]
        kernel_dfts = [direct_dft(kernel) for kernel in kernels]
        rho = Fraction(response.origin_zyx[1] + offset[0], shape[1]) - Fraction(
            response.origin_zyx[2] + offset[1], shape[2]
        )
        fundamental = root(-rho, -delta)
        specimen_phase = root(Fraction(), -alpha_s)
        adapter_phases = ((D(1), D(0)), fundamental, multiply(fundamental, fundamental))
        physical_phases = ((D(1), D(0)), specimen_phase, multiply(specimen_phase, specimen_phase))
        budgets = {}
        for m in range(3):
            l1 = sum(
                (abs(exact[m][index][0]) + abs(exact[m][index][1]) for index in np.ndindex(shape)),
                D(0),
            )
            lam = l1 / mass
            primitive = (
                512 * count * EPS * ((l1 + 2 * count * e) / (mass - count * e)) + 16 * count * Q
            )
            for index, value in transforms[m].items():
                target = value[0] / mass, value[1] / mass
                # Two real side coordinates: complex error <=sqrt(2)*e <=2*e.
                propagated = (2 * count * e + lam * count * e) / (mass - count * e) + primitive
                assert_close(
                    response.values[(m, *index)], target, propagated, f"stored bead E{m}/{index}"
                )
                stored_f = multiply(target, adapter_phases[m])
                model_f = multiply(kernel_dfts[m][index], physical_phases[m])
                model_gap = abs(stored_f[0] - model_f[0]) + abs(stored_f[1] - model_f[1])
                re, im = pair(response.values[(m, *index)])
                adapter_budget = 128 * EPS * (abs(re) + abs(im)) + 16 * Q if m else D(0)
                budget = model_gap + propagated + adapter_budget
                budgets[(m, *index)] = budget
                assert_close(
                    orders.values[(m, *index)], model_f, budget, f"selected model gauge {m}/{index}"
                )
        return budgets


@pytest.mark.parametrize(
    "shape,bead,roll,alpha_c,alpha_s",
    [((2, 3, 4), (1, 2, 3), (1, 1, 2), 0.3, -0.4), ((3, 3, 3), (2, 0, 1), (2, 2, 1), -0.2, 0.6)],
)
def test_C05_C06_C20_raw_bead_movement_storage_roll_and_phase_gauge(
    shape, bead, roll, alpha_c, alpha_s
):
    phases = np.array([0.0, 0.73, 1.81, 2.54, 3.48, 4.31, 5.47])
    cal_phases = phases + alpha_c
    h, kernels, components = point_model(shape, bead)
    raw_signal = exposures(*components, phases)
    raw = 4.0 + 2.0 * raw_signal
    acquisition = public.declare_acquisition(
        raw[None],
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "counts",
            "nominal_phases_rad": [[0.0] * len(phases)],
        },
    )
    calibrated = public.calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=4.0,
        response=2.0,
        output_unit="electrons",
        phases_rad=cal_phases,
        voxel_size_um=(0.25, 0.5, 0.125),
    )
    assert calibrated.response.origin_zyx == bead, (
        "observation-derived origin under selected peak gauge"
    )
    corrected = (raw - 4.0) / 2.0
    count = int(np.prod(shape))
    delta = alpha_s - alpha_c
    orders = invoke(calibrated.response, phase_reference_shift_rad=delta)
    assert_rotation(orders, calibrated.response, (1, -1), (0, 0), delta)
    # Generator comparison is a separate physical gauge control, never calibration input.
    baseline_budgets = check_selected_gauge(
        orders, calibrated.response, corrected, cal_phases, kernels, alpha_s, delta
    )
    rolled = public.declare_acquisition(
        np.roll(raw, roll, axis=(1, 2, 3))[None],
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "counts",
        },
    )
    rolled_cal = public.calibrate_raw_point_bead(
        rolled,
        group={"orientation": 0},
        offset=4.0,
        response=2.0,
        output_unit="electrons",
        phases_rad=cal_phases,
        voxel_size_um=(0.25, 0.5, 0.125),
    )
    rolled_orders = invoke(
        rolled_cal.response,
        coordinate_offset_yx=(-roll[1], -roll[2]),
        phase_reference_shift_rad=delta,
    )
    assert_rotation(rolled_orders, rolled_cal.response, (1, -1), (-roll[1], -roll[2]), delta)
    rolled_budgets = check_selected_gauge(
        rolled_orders,
        rolled_cal.response,
        np.roll(corrected, roll, axis=(1, 2, 3)),
        cal_phases,
        kernels,
        alpha_s,
        delta,
        (-roll[1], -roll[2]),
    )
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index in np.ndindex(orders.values.shape):
            assert_close(
                rolled_orders.values[index],
                pair(orders.values[index]),
                baseline_budgets[index] + rolled_budgets[index],
                f"storage roll/offset {index}",
            )
    moved_bead = tuple((b + t) % n for b, t, n in zip(bead, roll, shape, strict=True))
    _, _, moved_components = point_model(shape, moved_bead)
    moved_raw = 4.0 + 2.0 * exposures(*moved_components, phases)
    moved_acq = public.declare_acquisition(
        moved_raw[None],
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "counts",
        },
    )
    moved_cal = public.calibrate_raw_point_bead(
        moved_acq,
        group={"orientation": 0},
        offset=4.0,
        response=2.0,
        output_unit="electrons",
        phases_rad=cal_phases,
        voxel_size_um=(0.25, 0.5, 0.125),
    )
    moved_orders = invoke(moved_cal.response, phase_reference_shift_rad=delta)
    assert_rotation(moved_orders, moved_cal.response, (1, -1), (0, 0), delta)
    moved_budgets = check_selected_gauge(
        moved_orders,
        moved_cal.response,
        (moved_raw - 4.0) / 2.0,
        cal_phases,
        kernels,
        alpha_s,
        delta,
    )
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index in np.ndindex(orders.values.shape):
            assert_close(
                moved_orders.values[index],
                pair(orders.values[index]),
                baseline_budgets[index] + moved_budgets[index],
                f"physical bead compensation {index}",
            )
        observed_gap = represented(
            np.max(np.abs(moved_cal.response.values[1:] - calibrated.response.values[1:]))
        )
        assert observed_gap > 2 * max(baseline_budgets.values()), (
            "movement control exceeds inherited numerical uncertainty"
        )
    specimen = np.arange(count, dtype=np.float64).reshape(shape) / count + 0.25
    specimen_components = forward_specimen(kernels, specimen)
    specimen_phases = np.array([0.1, 0.91, 1.62, 2.88, 3.66, 4.74, 5.81])
    images = exposures(*specimen_components, specimen_phases)
    compare_reconstruction(images, specimen_phases + alpha_s, orders, (1, -1), 1.25, 0.25)
    # h and specimen are generator truth. Extended-grid object recovery is not asserted.
    assert h[0, 0, 0] == 0.75


def compare_reconstruction(images, phases, orders, carrier, gain, ridge, require_complex=False):
    shape = images.shape[1:]
    output = (shape[1] + 4 * abs(carrier[0]), shape[2] + 4 * abs(carrier[1]))
    mask = np.ones((shape[0], *output), dtype=np.float64)
    mask[..., ::2] = 0.625
    mask[:, 0, :] = 0
    result = public.reconstruct_volume(
        images[None],
        order_otfs=[orders],
        phases_rad=phases[None],
        carriers_bins=np.array([carrier], dtype=np.int64),
        gains=np.array([gain]),
        regularization=ridge,
        output_shape_yx=output,
        apodization=mask,
    )
    exact_spectrum, exact_volume = estimator(
        images, phases, orders.values, carrier, gain, ridge, mask
    )
    with localcontext() as ctx:
        ctx.prec = PRECISION
        n, m, p = len(phases), int(np.prod(shape)), int(np.prod(mask.shape))
        b = represented(np.max(np.abs(images)))
        assert np.linalg.cond(represented_basis(phases)) <= 10
        assert np.max(np.abs(orders.values.real)) <= 1 and np.max(np.abs(orders.values.imag)) <= 1
        assert ridge >= 0.25 and ridge <= 1
        assert 65536 * 5 * (n + m + p) * EPS <= D(2) ** -10
        assert 64 * 5 * p * max(b, Q) <= represented(np.finfo(np.float64).max)
        beta_s = 65536 * 5 * (n + m) * EPS * b + 256 * 5 * (n + m) * Q
        beta_v = p * beta_s + 16384 * 5 * p * EPS * b + 64 * p * Q
        if require_complex:
            assert any(abs(value[1]) > beta_v for value in exact_volume.values()), (
                "independent fixture imaginary component exceeds the inherited volume budget"
            )
        for index in np.ndindex(mask.shape):
            assert_close(
                result.spectrum[index],
                exact_spectrum[index],
                beta_s,
                f"stored estimator spectrum {index}",
            )
            assert_close(
                result.volume[index],
                exact_volume[index],
                beta_v,
                f"stored estimator volume {index}",
            )
    return result


@pytest.mark.parametrize("zero_sides", [False, True])
def test_C07_direct_signed_transfer_modular_negative_orders_gain_and_complex_nyquist(zero_sides):
    response = record(values=record().values / 2)
    if zero_sides:
        response.values[1:] = 0
    orders = invoke(response)
    assert_rotation(orders, response, (1, -1), (0, 0), 0.375)
    labels = np.arange(24, dtype=np.float64).reshape(2, 3, 4)
    dc = 0.25 + (labels % 5) / 8
    c1 = (labels % 3 - 1) / 16 + 1j * (labels % 4 - 2) / 32
    c2 = (labels % 7 - 3) / 32 + 1j * (labels % 5 - 2) / 16
    phases = np.array([0.0, 0.7, 1.9, 2.8, 3.9, 4.6, 5.5])
    images = exposures(dc, c1, c2, phases)
    # N>5 off-model data must retain the represented projection, not generator coefficients.
    images[0, 1, 2, 3] += 0.0625
    compare_reconstruction(images, phases, orders, (1, -1), 0.75, 0.5, require_complex=True)
