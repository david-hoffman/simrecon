"""Blind public-contract tests for explicit signed physical-frequency sampling.

Scenario inventory: docs/contracts/empirical-frequency-sampling-v1.md Q01-Q20.
The fixture uses exact rational brackets and an independent Decimal gauge oracle.
"""

from __future__ import annotations

import dataclasses
import math
import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any, Literal

import numpy as np
import pytest

import simrecon
from empirical_frequency_fixture import (
    FMAX,
    Q0,
    affine_value,
    arguments,
    assert_accuracy,
    component_bits,
    dec,
    ideal_axes,
    oracle,
    pi_decimal,
    rational,
    response,
    sin_cos,
    stencil,
    storage_variant,
)

Array = np.ndarray[Any, Any]


@pytest.fixture(scope="session")
def api() -> Any:
    # Missing exports are baseline setup evidence, not scientific product-red.
    assert hasattr(simrecon, "EmpiricalFrequencySamples"), "new record API absent"
    return getattr(simrecon, "sample_empirical_volume_transfer", None)


def reject(api: Any, code: str, record: Any | None = None, **changes: Any) -> None:
    if record is None:
        record = response()
    with pytest.raises(simrecon.SimreconError) as caught:
        api(record, **arguments(**changes))
    assert caught.value.code == code


def test_independent_oracle_known_values_and_precision() -> None:
    """Hand-solvable nodes, convexity, conjugation and quarter turn audit oracle."""
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (0, 0, 0))
    p = np.array([[-0.25, -0.5, -0.75]], dtype=np.float64)
    terms = stencil(r, p[0], 0)
    assert len(terms) == 8
    assert sum(w for w, _ in terms) == 1
    assert all(w > 0 for w, _ in terms)
    expected = affine_value(0, map(rational, p[0]))
    a, b, _ = oracle(r, p[0], **arguments(p, order=0))
    assert (a, b) == tuple(Decimal(v.numerator) / Decimal(v.denominator) for v in expected)
    r.values[1] = complex(2, 3)
    kw = arguments(order=1, calibration_carrier_bins=(1, 0), coordinate_offset_yx=(1, 0))
    a, b, _ = oracle(r, [0, 0, 0], **kw)
    assert abs(a + 2) < Decimal("1e-420")
    assert abs(b + 3) < Decimal("1e-420")
    sine, cosine = sin_cos(pi_decimal() / 2)
    # Division above uses the caller's 28-digit Decimal context.
    assert abs(sine - 1) < Decimal("1e-26")
    assert abs(cosine) < Decimal("1e-26")
    assert str(pi_decimal()).startswith("3.14159265358979323846264338327950288419716939937510")
    with localcontext() as ctx:
        ctx.prec = 440
        assert abs(dec(Q0) - Decimal.from_float(float(Q0))) < dec(Q0) * Decimal("1e-439")


def test_public_bindings_record_and_direct_construction(api: Any) -> None:
    r = response()
    kw = arguments()
    result = api(r, **kw)
    cls = getattr(simrecon, "EmpiricalFrequencySamples", None)
    assert cls is not None
    names = ("values", "frequencies_zyx_per_um", "order", "source", "provenance")
    assert type(result) is cls
    assert tuple(f.name for f in dataclasses.fields(result)) == names
    assert type(result.order) is int
    assert result.order == 1
    assert type(result.source) is str and result.source == kw["source"]
    assert type(result.provenance) is dict
    assert result.values.shape == (1,)
    assert result.frequencies_zyx_per_um.shape == (1, 3)
    for name in names:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, None)
        with pytest.raises((AttributeError, TypeError)):
            delattr(result, name)
    # Direct record construction deliberately supplies no validation/deep freeze.
    direct = cls(
        values="unvalidated", frequencies_zyx_per_um=None, order=99, source=None, provenance=[]
    )
    assert direct.values == "unvalidated"
    for name in kw:
        incomplete = dict(kw)
        del incomplete[name]
        with pytest.raises(TypeError):
            api(r, **incomplete)
    with pytest.raises(TypeError):
        api(r, *kw.values())
    with pytest.raises(TypeError):
        api(r, **kw, specimen_carrier_bins=(0, 0))


@pytest.mark.parametrize("order", [-2, -1, 0, 1, 2, np.int8(-2), np.int64(1), np.uint64(2)])
def test_signed_integer_orders(api: Any, order: Any) -> None:
    r = response()
    p = np.array([[0.125, -0.25, 0.5], [-0.25, 0.25, -0.75]])
    kw = arguments(
        p,
        order=order,
        calibration_carrier_bins=(2, -3),
        coordinate_offset_yx=(-1, 2),
        phase_reference_shift_rad=0.37,
    )
    result = api(r, **kw)
    assert type(result.order) is int and result.order == int(order)
    assert_accuracy(result.values, r, p, **kw)


@pytest.mark.parametrize(
    "order",
    [True, np.bool_(False), 1.0, np.float64(-1), 1j, "1", None, np.array(1), -3, 3, 10**100],
)
def test_invalid_order(api: Any, order: Any) -> None:
    reject(api, "invalid_empirical_transfer_order", order=order)


@pytest.mark.parametrize("kind", ["foreign", "fortran", "readonly", "strided", "reversed"])
def test_query_and_source_layouts_snapshot_bits(api: Any, kind: str) -> None:
    base = response()
    r = dataclasses.replace(
        base,
        **{
            field: storage_variant(getattr(base, field), kind)
            for field in ("values", "fz_per_um", "fy_per_um", "fx_per_um")
        },
    )
    p = storage_variant(
        np.array([[0.0, -0.0, 0.0], [0.125, -0.25, 0.5], [0.0, -0.0, 0.0], [-0.0, 0.0, -0.0]]), kind
    )
    observed = [
        (a, a.tobytes(), a.strides, a.flags.writeable)
        for a in (p, r.values, r.fz_per_um, r.fy_per_um, r.fx_per_um)
    ]
    result = api(r, **arguments(p))
    assert_accuracy(result.values, r, p, **arguments(p))
    np.testing.assert_array_equal(
        result.frequencies_zyx_per_um.view(np.uint64), p.astype(np.float64).view(np.uint64)
    )
    assert component_bits(result.values)[0].tolist() == component_bits(result.values)[2].tolist()
    for a, data, strides, writeable in observed:
        assert (a.tobytes(), a.strides, a.flags.writeable) == (data, strides, writeable)


class ArraySubclass(np.ndarray[Any, Any]):
    """Deliberately excluded ndarray subclass."""


@pytest.mark.parametrize(
    "points",
    [
        [[0.0, 0.0, 0.0]],
        np.zeros((1, 3), dtype=np.float32),
        np.zeros((1, 3), dtype=np.int64),
        np.zeros((1, 3), dtype=np.complex128),
        np.zeros((1, 3), dtype=object),
        np.zeros((1, 3), dtype=bool),
        np.zeros(3),
        np.zeros((1, 1, 3)),
        np.zeros((1, 2)),
        np.zeros((1, 4)),
        np.empty((0, 3)),
        np.array([[0.0, np.nan, 0.0]]),
        np.array([[0.0, 0.0, np.inf]]),
        np.array([[-np.inf, 0.0, 0.0]]),
        np.zeros((1, 3)).view(ArraySubclass),
        np.ma.array(np.zeros((1, 3)), mask=False),
    ],
)
def test_invalid_queries(api: Any, points: Any) -> None:
    reject(api, "invalid_empirical_transfer_frequencies", frequencies_zyx_per_um=points)


def test_anisotropic_complex_tensor_multiaffine_and_duplicate_points(api: Any) -> None:
    # Each source coordinate is dyadic: independent affine formula is exact here.
    r = response((4, 4, 4), (0.5, 1.0, 2.0), (1, 2, 3))
    p = np.array(
        [
            [-0.875, -0.4375, -0.21875],
            [0.125, 0.0625, 0.03125],
            [-0.3125, 0.1875, -0.09375],
            [0.125, 0.0625, 0.03125],
        ]
    )
    for order in (0, 1, 2):
        kw = arguments(p, order=order)
        actual = api(r, **kw).values
        assert_accuracy(actual, r, p, **kw)
        with localcontext() as ctx:
            ctx.prec = 440
            for point in p:
                expected = affine_value(order, map(rational, point))
                ir, ii, _ = oracle(r, point, **kw)
                assert (ir, ii) == tuple(map(dec, expected))
    # All cross terms and both components are nonzero; magnitude/phase blending,
    # nearest nodes, axis permutations, a second centering and volume factors differ.


def test_exact_geometry_not_tolerated_source_metadata(api: Any) -> None:
    r = response((1, 1, 3), (1.0, 1.0, 1.0), (0, 0, 0))
    p = np.array([[0.0, 0.0, float(Fraction(1, 3))]])  # rounded inward
    r.values[:] = 0
    r.values[1, 0, 0, 1] = 1e100
    r.values[1, 0, 0, 2] = 0
    # Perturb metadata inward but within its independent validation allowance.
    r.fx_per_um[2] = np.nextafter(r.fx_per_um[2], 0.0)
    kw = arguments(p)
    assert rational(p[0, 2]) < Fraction(1, 3)
    result = api(r, **kw)
    assert_accuracy(result.values, r, p, **kw)
    assert result.values[0].real > 1e82  # snapping to endpoint would return zero


def test_rounded_ideal_endpoint_outside_rejects_without_tolerance(api: Any) -> None:
    r = response((1, 1, 5), (1.0, 1.0, 1.0), (0, 0, 0))
    upper = float(Fraction(2, 5))
    assert rational(upper) > Fraction(2, 5)
    reject(
        api,
        "incomplete_empirical_transfer_coverage",
        r,
        frequencies_zyx_per_um=np.array([[0.0, 0.0, upper]]),
    )
    inside = np.nextafter(upper, 0.0)
    p = np.array([[0.0, 0.0, inside]])
    assert_accuracy(api(r, **arguments(p)).values, r, p, **arguments(p))
    # Metadata itself remains valid even though it rounds outside the ideal hull.


@pytest.mark.parametrize("order", [0, 1, 2, -1, -2])
def test_exact_nodes_component_bits_and_closed_endpoints(api: Any, order: int) -> None:
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (1, 1, 1))
    fmax = float(FMAX)
    v = np.empty((2, 2, 2), dtype=np.complex128)
    v.real.flat[:] = [-0.0, 0.0, fmax, -fmax, 7.0, -3.0, 0.0, -0.0]
    v.imag.flat[:] = [0.0, -0.0, fmax, -fmax, -0.0, 0.0, -2.0, 4.0]
    r.values[abs(order)] = v
    p = np.array(list(np.ndindex(2, 2, 2)), dtype=np.float64) - 1
    if order < 0:
        p = -p
    kw = arguments(
        p,
        order=order,
        calibration_carrier_bins=(2, -2),
        coordinate_offset_yx=(10**90, 10**90),
        phase_reference_shift_rad=-0.0,
    )
    result = api(r, **kw)
    expected_bits = component_bits(v.ravel()).copy()
    if order < 0:
        expected_bits[:, 1] ^= np.uint64(1 << 63)
    np.testing.assert_array_equal(component_bits(result.values), expected_bits)


def test_order_zero_node_ignores_nonidentity_gauge(api: Any) -> None:
    r = response((1, 1, 1), (1.0, 1.0, 1.0), (0, 0, 0))
    r.values[0, 0, 0, 0] = complex(-0.0, -0.0)
    result = api(
        r,
        **arguments(
            order=0, phase_reference_shift_rad=1e308, calibration_carrier_bins=(10**800, -(10**900))
        ),
    )
    np.testing.assert_array_equal(
        component_bits(result.values), component_bits(r.values[0].ravel())
    )


def test_zero_stencil_and_exact_cancellation_are_data(api: Any) -> None:
    r = response((1, 1, 2), (1.0, 1.0, 0.5), (0, 0, 0))
    r.values[:] = 0
    p = np.array([[0.0, 0.0, -0.5]])
    for order in range(-2, 3):
        # Negative order's reflected hull is [0,1].
        points = -p if order < 0 else p
        assert (
            api(r, **arguments(points, order=order, phase_reference_shift_rad=0.7)).values[0] == 0
        )
    r.values[0, 0, 0] = [complex(4, -8), complex(-4, 8)]
    kw = arguments(p, order=0)
    assert_accuracy(api(r, **kw).values, r, p, **kw)


def test_physical_reflection_all_axes_not_same_frequency_or_reversal(api: Any) -> None:
    r = response((4, 4, 4), (0.5, 1.0, 2.0), (1, 2, 3))
    p = np.array([[0.125, -0.1875, 0.0625], [-0.25, 0.125, -0.125]])
    for m in (1, 2):
        kw = arguments(
            p,
            order=-m,
            calibration_carrier_bins=(1, -3),
            coordinate_offset_yx=(2, 1),
            phase_reference_shift_rad=-0.41,
        )
        negative = api(r, **kw).values
        assert_accuracy(negative, r, p, **kw)
        positive_kw = kw | {"order": m, "frequencies_zyx_per_um": -p}
        positive = api(r, **positive_kw).values
        assert_accuracy(positive, r, -p, **positive_kw)


@pytest.mark.parametrize("axis", [0, 1, 2])
def test_even_physical_nyquist_domain_and_whole_call(api: Any, axis: int) -> None:
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (0, 0, 0))
    p = np.zeros((2, 3))
    p[1, axis] = 1.0
    reject(api, "incomplete_empirical_transfer_coverage", r, frequencies_zyx_per_um=p)
    kw = arguments(p, order=-1)
    assert_accuracy(api(r, **kw).values, r, p, **kw)
    # Conversely the stored negative endpoint is outside the negative-row domain.
    reject(api, "incomplete_empirical_transfer_coverage", r, order=-1, frequencies_zyx_per_um=-p)


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("direction", [-1, 1])
def test_singleton_only_zero_no_support_or_zero_bypass(api: Any, axis: int, direction: int) -> None:
    r = response((1, 1, 1), (1.0, 1.0, 1.0), (0, 0, 0))
    r.values[:] = 0
    p = np.zeros((2, 3))
    p[1, axis] = direction * float(Q0)
    reject(api, "incomplete_empirical_transfer_coverage", r, order=0, frequencies_zyx_per_um=p)


def test_gauge_source_samples_offsets_and_shift_sign(api: Any) -> None:
    r = response((3, 4, 5), (0.5, 0.25, 0.125), (1, 2, 3))
    p = np.array([[0.125, -0.25, 0.75], [-0.5, 0.125, -1.25]])
    for m in (-2, -1, 1, 2):
        kw = arguments(
            p,
            order=m,
            calibration_carrier_bins=(1, -2),
            coordinate_offset_yx=(3, -1),
            phase_reference_shift_rad=0.37,
        )
        assert_accuracy(api(r, **kw).values, r, p, **kw)
    # Changing storage origin together with the opposite sample offset preserves
    # common coordinates. A second centering/frequency phase would break this.
    moved = dataclasses.replace(r, origin_zyx=(0, 1, 4))
    kw = arguments(p, order=2, calibration_carrier_bins=(1, -2), coordinate_offset_yx=(3, -1))
    a = api(r, **kw).values
    moved_kw = kw | {"coordinate_offset_yx": (4, -2)}
    b = api(moved, **moved_kw).values
    assert_accuracy(a, r, p, **kw)
    assert_accuracy(b, moved, p, **moved_kw)
    for point in p:
        assert oracle(r, point, **kw) == oracle(moved, point, **moved_kw)


@pytest.mark.parametrize(
    "delta", [0.0, -0.0, float(Q0), -float(Q0), 1e308, -1e308, np.float32(0.125), np.int64(2)]
)
def test_finite_phase_extremes_huge_exact_declarations(api: Any, delta: Any) -> None:
    r = response()
    p = np.array([[0.125, -0.25, 0.5]])
    for m in (1, 2, -2):
        kw = arguments(
            p,
            order=m,
            calibration_carrier_bins=(10**600 + 1, -(10**500) - 3),
            coordinate_offset_yx=(10**700 + 2, -(10**400)),
            phase_reference_shift_rad=delta,
        )
        result = api(r, **kw)
        assert_accuracy(result.values, r, p, **kw)
        assert type(result.provenance["phase_reference_shift_rad"]) is float
        assert math.copysign(1.0, result.provenance["phase_reference_shift_rad"]) == math.copysign(
            1.0, float(delta)
        )


@pytest.mark.parametrize(
    "field,code",
    [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset"),
    ],
)
@pytest.mark.parametrize(
    "bad",
    [
        None,
        (1,),
        (1, 2, 3),
        np.array([1, 2]),
        "12",
        (True, 0),
        (np.bool_(True), 0),
        (1.0, 0),
        (1j, 0),
    ],
)
def test_integer_pair_grammar(api: Any, field: str, code: str, bad: Any) -> None:
    reject(api, code, **{field: bad})


class PairSubclass(list[Any]):
    """Deliberately excluded list subclass."""


def test_exact_builtin_pair_containers_and_allowed_unsigned(api: Any) -> None:
    for field, code in [
        ("calibration_carrier_bins", "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", "invalid_empirical_transfer_coordinate_offset"),
    ]:
        reject(api, code, **{field: PairSubclass([1, 2])})
    r = response()
    kw = arguments(
        calibration_carrier_bins=[np.uint64(2**64 - 1), np.int8(-1)],
        coordinate_offset_yx=[0, 10**400],
    )
    result = api(r, **kw)
    assert_accuracy(result.values, r, kw["frequencies_zyx_per_um"], **kw)
    for field in ("calibration_carrier_bins", "coordinate_offset_yx"):
        assert type(result.provenance[field]) is tuple
        assert all(type(v) is int for v in result.provenance[field])
        assert result.provenance[field] == tuple(map(int, kw[field]))


@pytest.mark.parametrize(
    "bad",
    [
        True,
        np.bool_(False),
        1j,
        "0",
        None,
        np.array(0.0),
        float("nan"),
        float("inf"),
        -float("inf"),
        10**1000,
    ],
)
def test_phase_grammar_and_conversion(api: Any, bad: Any) -> None:
    reject(api, "invalid_empirical_transfer_phase_shift", phase_reference_shift_rad=bad)


@pytest.mark.parametrize("bad", [None, "", " \t\n", 3])
def test_source_label_grammar(api: Any, bad: Any) -> None:
    reject(api, "invalid_otf_source", source=bad)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("values", []),
        ("values", np.zeros((3, 1, 1, 1), dtype=np.complex64)),
        ("values", np.zeros((3, 1, 1, 1), dtype=np.float64)),
        ("values", np.zeros((2, 1, 1, 1), dtype=np.complex128)),
        ("values", np.zeros((3, 1, 1), dtype=np.complex128)),
        ("values", np.zeros((3, 0, 1, 1), dtype=np.complex128)),
        ("values", np.zeros((3, 1, 1, 1), dtype=np.complex128).view(ArraySubclass)),
        ("values", np.ma.array(np.zeros((3, 1, 1, 1), dtype=np.complex128))),
        ("fz_per_um", [0.0]),
        ("fy_per_um", np.array([0.0], dtype=np.float32)),
        ("fx_per_um", np.array([0], dtype=np.int64)),
        ("fx_per_um", np.array([[0.0]])),
        ("fy_per_um", np.array([0.0, 1.0])),
        ("fz_per_um", np.array([0.0]).view(ArraySubclass)),
        ("fy_per_um", np.ma.array([0.0])),
        ("fx_per_um", np.array([float("nan")])),
        ("fz_per_um", np.array([float("inf")])),
        ("fy_per_um", np.array([float(Q0)])),
        ("voxel_size_um", np.ones(3)),
        ("voxel_size_um", (1.0, 1.0)),
        ("voxel_size_um", PairSubclass([1.0, 1.0, 1.0])),
        ("voxel_size_um", (True, 1.0, 1.0)),
        ("voxel_size_um", (1j, 1.0, 1.0)),
        ("voxel_size_um", (0.0, 1.0, 1.0)),
        ("voxel_size_um", (-1.0, 1.0, 1.0)),
        ("voxel_size_um", (float("nan"), 1.0, 1.0)),
        ("voxel_size_um", (float("inf"), 1.0, 1.0)),
        ("voxel_size_um", (10**1000, 1.0, 1.0)),
        ("origin_zyx", np.zeros(3, dtype=int)),
        ("origin_zyx", (0, 0)),
        ("origin_zyx", PairSubclass([0, 0, 0])),
        ("origin_zyx", (True, 0, 0)),
        ("origin_zyx", (0.0, 0, 0)),
        ("origin_zyx", (-1, 0, 0)),
        ("origin_zyx", (0, 1, 0)),
        ("origin_zyx", (0, 0, 10**500)),
    ],
)
def test_full_response_representation(api: Any, field: str, bad: Any) -> None:
    r = response((1, 1, 1), (1.0, 1.0, 1.0), (0, 0, 0))
    reject(
        api, "invalid_empirical_transfer_response", dataclasses.replace(r, **{field: bad}), order=0
    )


@pytest.mark.parametrize("bad", [None, {}, np.zeros((3, 1, 1, 1))])
def test_response_requires_public_record(api: Any, bad: Any) -> None:
    reject(api, "invalid_empirical_transfer_response", bad if bad is not None else False)


@pytest.mark.parametrize("component", ["real", "imag"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_unused_response_row_and_source_sample_still_validated(
    api: Any, component: str, bad: float
) -> None:
    r = response()
    getattr(r.values, component)[2, -1, -1, -1] = bad
    # Only zero-row DC requested; unused +2 corner must still reject.
    reject(api, "invalid_empirical_transfer_response", r, order=0)


@pytest.mark.parametrize("axis", ["fz_per_um", "fy_per_um", "fx_per_um"])
def test_source_coordinate_order_dc_offdc_and_tolerance(api: Any, axis: str) -> None:
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (0, 0, 0))
    valid = getattr(r, axis).copy()
    for _ in range(8):
        valid[0] = np.nextafter(valid[0], -np.inf)
    accepted = dataclasses.replace(r, **{axis: valid})
    p = np.array([[-0.5, -0.5, -0.5]])
    assert_accuracy(api(accepted, **arguments(p)).values, accepted, p, **arguments(p))
    outside = valid.copy()
    outside[0] = np.nextafter(outside[0], -np.inf)
    for bad in [
        outside,
        np.array([0.0, 0.0]),
        np.array([1.0, 0.0]),
        np.array([-1.0, float(Q0)]),
        np.array([-1.0, -0.25]),
        np.array([-1.0, np.inf]),
    ]:
        reject(api, "invalid_empirical_transfer_response", dataclasses.replace(r, **{axis: bad}))


def test_source_spacing_extremes_and_converted_metadata(api: Any) -> None:
    # N*d overflows in binary64, but each final canonical frequency is finite.
    r = response(
        (2, 1, 1), [float(FMAX), np.float64(float(Q0)), np.int64(2)], [np.uint8(1), 0, np.int64(0)]
    )
    p = np.array([[0.0, 0.0, 0.0], [-float(Q0), 0.0, 0.0]])
    result = api(r, **arguments(p))
    assert_accuracy(result.values, r, p, **arguments(p))
    assert result.provenance["source_voxel_size_um"] == (float(FMAX), float(Q0), 2.0)
    assert all(type(v) is float for v in result.provenance["source_voxel_size_um"])
    assert result.provenance["source_origin_zyx"] == (1, 0, 0)
    assert all(type(v) is int for v in result.provenance["source_origin_zyx"])
    # Singleton axes have no nonzero-frequency representability restriction.
    s = response((1, 1, 1), (float(Q0), float(FMAX), 1.0), (0, 0, 0))
    assert_accuracy(api(s, **arguments()).values, s, np.zeros((1, 3)), **arguments())


class OrdinaryResponse(simrecon.EmpiricalVolumeResponse):
    """Permitted ordinary public record subclass."""


class MissingFieldResponse(simrecon.EmpiricalVolumeResponse):
    """Exercise a missing required public field through its ordinary getter."""

    def __getattribute__(self, name: str) -> Any:
        """Raise AttributeError for the selected public field."""
        if name == "fx_per_um":
            raise AttributeError("missing public frequency field")
        return super().__getattribute__(name)


@pytest.mark.parametrize(
    "failure",
    [
        MemoryError("allocation sentinel"),
        RuntimeError("unrelated getter"),
        ZeroDivisionError("unrelated arithmetic"),
        TypeError("getter type failure outside conversion"),
        ValueError("getter value failure outside conversion"),
        OverflowError("getter range failure outside conversion"),
    ],
)
def test_public_getter_failures_propagate_unmodified(api: Any, failure: Exception) -> None:
    class GetterResponse(simrecon.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                raise failure
            return super().__getattribute__(name)

    r = response()
    broken = GetterResponse(**{f.name: getattr(r, f.name) for f in dataclasses.fields(r)})
    with pytest.raises(type(failure)) as caught:
        api(broken, **arguments())
    assert caught.value is failure


def test_ordinary_response_subclasses_and_missing_field(api: Any) -> None:
    r = response()
    fields = {f.name: getattr(r, f.name) for f in dataclasses.fields(r)}
    sub = OrdinaryResponse(**fields)
    assert_accuracy(api(sub, **arguments()).values, sub, np.zeros((1, 3)), **arguments())
    reject(api, "invalid_empirical_transfer_response", MissingFieldResponse(**fields))


@pytest.mark.parametrize("failure_type", [TypeError, ValueError, OverflowError])
def test_expected_conversion_errors_translate_at_each_boundary(
    api: Any, failure_type: type[Exception]
) -> None:
    class BadFloat(float):
        def __float__(self) -> float:
            raise failure_type("numeric conversion sentinel")

    class BadInt(int):
        def __int__(self) -> int:
            raise failure_type("integer conversion sentinel")

    for name, value, code in [
        ("order", BadInt(1), "invalid_empirical_transfer_order"),
        ("calibration_carrier_bins", (BadInt(1), 0), "invalid_empirical_transfer_carrier"),
        ("coordinate_offset_yx", (0, BadInt(1)), "invalid_empirical_transfer_coordinate_offset"),
        ("phase_reference_shift_rad", BadFloat(0.1), "invalid_empirical_transfer_phase_shift"),
    ]:
        reject(api, code, **{name: value})
    r = response()
    for name, value in [
        ("voxel_size_um", (BadFloat(1), 1.0, 1.0)),
        ("origin_zyx", (BadInt(0), 0, 0)),
    ]:
        reject(api, "invalid_empirical_transfer_response", dataclasses.replace(r, **{name: value}))


@pytest.mark.parametrize(
    "failure", [MemoryError("conversion allocation"), RuntimeError("conversion unrelated")]
)
def test_unrelated_numeric_conversion_exceptions_propagate(api: Any, failure: Exception) -> None:
    class BadFloat(float):
        def __float__(self) -> float:
            raise failure

    with pytest.raises(type(failure)) as caught:
        api(response(), **arguments(phase_reference_shift_rad=BadFloat(1.0)))
    assert caught.value is failure


def test_wide_phase_conversion_underflow_when_available(api: Any) -> None:
    # Native longdouble may equal binary64. No capability skip or new precision
    # requirement: the converted value is authoritative on either platform.
    with np.errstate(all="ignore"):
        phase = np.longdouble("-1e-400")
    result = api(response(), **arguments(phase_reference_shift_rad=phase))
    assert result.provenance["phase_reference_shift_rad"] == 0.0
    assert math.copysign(1.0, result.provenance["phase_reference_shift_rad"]) == -1.0


def test_owned_arrays_provenance_and_input_preservation_on_both_paths(api: Any) -> None:
    spacing = [0.5, 0.25, 0.125]
    origin = [1, 2, 3]
    carrier = [1, -2]
    offset = [-1, 3]
    r = response(spacing=spacing, origin=origin)
    p = np.array([[0.0, -0.0, 0.0], [0.25, -0.25, 0.5], [0.0, -0.0, 0.0]])
    kw = arguments(
        p,
        order=np.int8(-2),
        calibration_carrier_bins=carrier,
        coordinate_offset_yx=offset,
        phase_reference_shift_rad=-0.0,
    )
    inputs = [r.values, r.fz_per_um, r.fy_per_um, r.fx_per_um, p]
    before = [(a.tobytes(), a.strides, a.flags.writeable) for a in inputs]
    first, second = api(r, **kw), api(r, **kw)
    for result in (first, second):
        assert type(result.values) is np.ndarray
        assert type(result.frequencies_zyx_per_um) is np.ndarray
        assert result.values.dtype == np.dtype(np.complex128)
        assert result.frequencies_zyx_per_um.dtype == np.dtype(np.float64)
        for a in (result.values, result.frequencies_zyx_per_um):
            assert a.flags.owndata and a.flags.c_contiguous and a.flags.writeable
            assert all(not np.shares_memory(a, b) for b in inputs)
        assert not np.shares_memory(result.values, result.frequencies_zyx_per_um)
        assert result.provenance == {
            "sampling": "complex_cartesian_trilinear_points_v1",
            "source_shape_zyx": (3, 4, 5),
            "source_voxel_size_um": (0.5, 0.25, 0.125),
            "source_origin_zyx": (1, 2, 3),
            "calibration_carrier_bins": (1, -2),
            "coordinate_offset_yx": (-1, 3),
            "phase_reference_shift_rad": -0.0,
        }
        assert math.copysign(1.0, result.provenance["phase_reference_shift_rad"]) == -1.0
        assert all(type(v) is int for v in result.provenance["source_shape_zyx"])
    assert first.provenance is not second.provenance
    for a in (first.values, first.frequencies_zyx_per_um):
        for b in (second.values, second.frequencies_zyx_per_um):
            assert not np.shares_memory(a, b)
    for a, old in zip(inputs, before, strict=True):
        assert (a.tobytes(), a.strides, a.flags.writeable) == old
    first.values[:] = 99
    first.frequencies_zyx_per_um[:] = 42
    first.provenance["sampling"] = "caller mutation"
    r.values[:] = -77
    p[:] = -99
    carrier[:] = [7, 8]
    offset[:] = [10, 11]
    spacing[:] = [2.0, 2.0, 2.0]
    origin[:] = [0, 0, 0]
    assert second.provenance["calibration_carrier_bins"] == (1, -2)
    assert second.provenance["coordinate_offset_yx"] == (-1, 3)
    assert second.provenance["source_voxel_size_um"] == (0.5, 0.25, 0.125)
    assert second.provenance["source_origin_zyx"] == (1, 2, 3)
    assert second.provenance["sampling"] == "complex_cartesian_trilinear_points_v1"
    assert not np.all(second.values == 99)
    assert second.frequencies_zyx_per_um[0, 1] == 0
    # Rejection also preserves layout, content, flags and metadata.
    r = response()
    p = np.array([[0.0, 0.0, 0.0], [100.0, 0.0, 0.0]])
    r.values.flags.writeable = False
    old = (r.values.tobytes(), p.tobytes(), r.values.strides, r.values.flags.writeable)
    reject(api, "incomplete_empirical_transfer_coverage", r, frequencies_zyx_per_um=p)
    assert (r.values.tobytes(), p.tobytes(), r.values.strides, r.values.flags.writeable) == old


@pytest.mark.parametrize("kind", ["cancelling", "rotated", "tiny_weight", "subnormal"])
def test_component_safe_arithmetic_sufficient_success(api: Any, kind: str) -> None:
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (0, 0, 0))
    r.values[:] = 0
    p = np.array([[-0.5, -0.5, -0.5]])
    delta = 0.0
    if kind == "cancelling":
        r.values[1, 0] = complex(float(FMAX), float(FMAX))
        r.values[1, 1] = complex(-float(FMAX), -float(FMAX))
    elif kind == "rotated":
        big = float(FMAX) * 0.9
        r.values[1, 0] = complex(big, big)
        r.values[1, 1] = complex(big, -big)
        delta = math.pi / 4
    elif kind == "tiny_weight":
        r.values[1, 0, 0, 0] = float.fromhex("0x1p+1023")
        p[:] = -float.fromhex("0x1p-540")
    else:
        r.values[1] = complex(float(Q0), -float(Q0))
    kw = arguments(p, phase_reference_shift_rad=delta)
    er, ei, budget = oracle(r, p[0], **kw)
    with localcontext() as ctx:
        ctx.prec = 440
        assert abs(er) + budget < dec(FMAX)
        assert abs(ei) + budget < dec(FMAX)
    actual = api(r, **kw).values
    assert np.isfinite(actual.real).all() and np.isfinite(actual.imag).all()
    assert_accuracy(actual, r, p, **kw)
    if kind == "tiny_weight":
        assert actual[0].real != 0  # standalone three-axis weight underflows


def test_final_component_range_rejects_entire_call(api: Any) -> None:
    r = response((1, 1, 2), (1.0, 1.0, 0.5), (0, 0, 0))
    big = float(FMAX) * 0.9
    r.values[1, 0, 0] = [0.0, complex(big, big)]
    p = np.array([[0.0, 0.0, -1.0], [0.0, 0.0, 0.0]])
    kw = arguments(p, phase_reference_shift_rad=-math.pi / 4)
    er, _, _ = oracle(r, p[1], **kw)
    with localcontext() as ctx:
        ctx.prec = 440
        assert er > dec(FMAX) * Decimal("1.2")
    reject(api, "unrepresentable_empirical_interpolation", r, **kw)


@pytest.mark.parametrize("mode", ["raise", "warn"])
def test_caller_arithmetic_warning_policy_preserved(
    api: Any, mode: Literal["raise", "warn"]
) -> None:
    r = response((2, 2, 2), (0.5, 0.5, 0.5), (0, 0, 0))
    r.values[:] = 0
    r.values[1, 0, 0, 0] = float.fromhex("0x1p+1023")
    p = np.full((1, 3), -float.fromhex("0x1p-540"))
    with np.errstate(all=mode), warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("error", RuntimeWarning)
        state, filters = np.geterr().copy(), list(warnings.filters)
        kw = arguments(p, phase_reference_shift_rad=1e308)
        assert_accuracy(api(r, **kw).values, r, p, **kw)
        reject(api, "invalid_empirical_transfer_phase_shift", r, phase_reference_shift_rad=10**1000)
        reject(
            api, "incomplete_empirical_transfer_coverage", r, frequencies_zyx_per_um=np.ones((1, 3))
        )
        big = float(FMAX) * 0.9
        r.values[1] = complex(big, big)
        reject(
            api,
            "unrepresentable_empirical_interpolation",
            r,
            phase_reference_shift_rad=-math.pi / 4,
        )
        assert np.geterr() == state
        assert warnings.filters == filters
        assert not captured


def test_unrelated_warning_category_is_not_suppressed(api: Any) -> None:
    class WarningResponse(simrecon.EmpiricalVolumeResponse):
        def __getattribute__(self, name: str) -> Any:
            if name == "values":
                warnings.warn("public getter warning sentinel", UserWarning, stacklevel=2)
            return super().__getattribute__(name)

    r = response()
    noisy = WarningResponse(**{f.name: getattr(r, f.name) for f in dataclasses.fields(r)})
    with pytest.warns(UserWarning, match="public getter warning sentinel"):
        result = api(noisy, **arguments())
    assert_accuracy(result.values, r, np.zeros((1, 3)), **arguments())


def test_held_out_smooth_model_error_separate_from_arithmetic(api: Any) -> None:
    r = response((4, 4, 4), (0.5, 1.0, 2.0), (0, 0, 0))
    axes = ideal_axes((4, 4, 4), r.voxel_size_um)

    def smooth(point: Any) -> tuple[Fraction, Fraction]:
        z, y, x = map(Fraction, point)
        return 1 + z * z + 2 * y * y + 3 * x * x, -2 * z * z + y * y / 2 - x * x / 4

    for idx in np.ndindex(4, 4, 4):
        value = smooth(axes[a][j] for a, j in enumerate(idx))
        r.values[(0, *idx)] = complex(*map(float, value))
    p = np.array([[-0.875, -0.3125, -0.21875], [-0.25, 0.125, 0.0625], [0.375, -0.125, -0.03125]])
    kw = arguments(p, order=0)
    actual = api(r, **kw).values
    assert_accuracy(actual, r, p, **kw)
    with localcontext() as ctx:
        ctx.prec = 100
        # sum h_a^2*|H_aa|/8; H_aa = 2*(a_real+i*a_imag).
        coeff = [(1, -2), (2, Fraction(1, 2)), (3, Fraction(-1, 4))]
        cell_bound = sum(
            (
                dec((nodes[1] - nodes[0]) ** 2)
                * (dec(Fraction(a)) ** 2 + dec(Fraction(b)) ** 2).sqrt()
                / 4
                for nodes, (a, b) in zip(axes, coeff, strict=True)
            ),
            Decimal(0),
        )
        for value, point in zip(actual, p, strict=True):
            hr, hi = map(dec, smooth(map(rational, point)))
            ir, ii, arithmetic_budget = oracle(r, point, **kw)
            model_error = ((ir - hr) ** 2 + (ii - hi) ** 2).sqrt()
            observed_error = (
                (Decimal.from_float(float(value.real)) - hr) ** 2
                + (Decimal.from_float(float(value.imag)) - hi) ** 2
            ).sqrt()
            assert Decimal("0.001") < model_error <= cell_bound
            assert observed_error <= cell_bound + arithmetic_budget
    # This is a declared mathematical comparison; it makes no optical claim.


@pytest.mark.parametrize("order", [-2, -1, 1, 2])
def test_explicit_overlap_object_and_detector_coordinates(api: Any, order: int) -> None:
    r = response((4, 4, 4), (0.5, 1.0, 2.0), (1, 2, 3))
    f = np.array([[0.0, -0.0625, 0.0], [-0.125, 0.0, -0.03125], [0.125, 0.0625, 0.0]])
    q = np.array([0.0, 0.0625, 0.03125])
    detector = f + order * q
    zero_kw = arguments(
        f,
        order=0,
        calibration_carrier_bins=(1, -2),
        coordinate_offset_yx=(-1, 2),
        phase_reference_shift_rad=0.31,
    )
    side_kw = zero_kw | {"order": order, "frequencies_zyx_per_um": detector}
    zero = api(r, **zero_kw)
    side = api(r, **side_kw)
    assert_accuracy(zero.values, r, f, **zero_kw)
    assert_accuracy(side.values, r, detector, **side_kw)
    np.testing.assert_array_equal(side.frequencies_zyx_per_um, detector)
    # Generate observations from independent interpolants, not sampler outputs.
    e0 = np.array([complex(float(a), float(b)) for a, b, _ in (oracle(r, p, **zero_kw) for p in f)])
    em = np.array(
        [complex(float(a), float(b)) for a, b, _ in (oracle(r, p, **side_kw) for p in detector)]
    )
    spectrum = np.array([1.0 + 0.5j, -0.75 + 0.25j, 0.5 - 1.0j])
    gain = complex(0.7, -0.4)
    d0 = e0 * spectrum
    dm = gain * em * spectrum
    x = side.values * d0
    y = zero.values * dm
    fitted = np.vdot(x, y) / np.vdot(x, x)
    assert abs(fitted - gain) < 2e-11
    # q intentionally differs from calibration carrier/(Nc*dc): that equality
    # has no meaning here. Detector observations were supplied at these points;
    # the sampler performs no observation interpolation or estimator fitting.


def test_raw_point_bead_to_signed_queries_with_independent_budget(api: Any) -> None:
    from empirical_frequency_fixture import raw_bead_case

    raw, phases, expected, source_budget = raw_bead_case()
    acquisition = simrecon.declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "z", "y", "x"],
            "intensity_unit": "count",
            # Commands deliberately carry no actual-phase information.
            "nominal_phases_rad": [[0.0] * len(phases)],
            "sampling_um": {"z": 1.0, "y": 1.0, "x": 1.0},
        },
    )
    calibrated = simrecon.calibrate_raw_point_bead(
        acquisition,
        group={"orientation": 0},
        offset=10.0,
        response=2.0,
        output_unit="electron",
        phases_rad=phases,
        voxel_size_um=expected.voxel_size_um,
    )
    assert calibrated.response.origin_zyx == (1, 1, 2)
    p = np.array([[0.125, -0.25, 0.125], [-0.25, 0.125, -0.375], [0.125, -0.25, 0.125]])
    with localcontext() as ctx:
        ctx.prec = 120
        for order in (-2, -1, 0, 1, 2):
            kw = arguments(
                p,
                order=order,
                calibration_carrier_bins=(1, 1),
                coordinate_offset_yx=(0, 0),
                phase_reference_shift_rad=0.23,
                source="known synthetic point bead; external physical pairing",
            )
            sampled = api(calibrated.response, **kw)
            # Independent expected source is exact represented-phase LS followed
            # by direct Fourier sums; interpolation convexity carries its budget.
            for value, point in zip(sampled.values, p, strict=True):
                er, ei, arithmetic_budget = oracle(expected, point, **kw)
                dr = Decimal.from_float(float(value.real)) - er
                di = Decimal.from_float(float(value.imag)) - ei
                assert (dr * dr + di * di).sqrt() <= source_budget + arithmetic_budget
    assert sampled.source == "known synthetic point bead; external physical pairing"


def test_joint_storage_roll_vs_physical_bead_move_gauge(api: Any) -> None:
    # Small public prepare-response composition uniquely reaches already-centered
    # data and the observed bead gauge without repeating raw validation tests.
    shape = (3, 4, 4)
    h = np.zeros(shape)
    h[0, 0, 0], h[1, 0, 1], h[2, 1, 0] = 0.5, 0.25, 0.25
    spacing = (0.5, 0.25, 0.5)
    carrier = (1, -1)
    b = (1, 1, 2)
    moved_b = (2, 2, 1)

    def components(bead: tuple[int, int, int]) -> tuple[Array, Array, Array]:
        dc = 128 * np.roll(h, bead, axis=(0, 1, 2))
        rho = sum(
            (Fraction(k * j, n) for k, j, n in zip(carrier, bead[1:], shape[1:], strict=True)),
            Fraction(),
        )
        sides = []
        with localcontext() as ctx:
            ctx.prec = 100
            for m, scale in ((1, Fraction(1, 4)), (2, Fraction(1, 8))):
                sine, cosine = sin_cos(2 * pi_decimal() * dec(m * rho))
                sides.append(dc * complex(float(dec(scale) * cosine), float(dec(scale) * sine)))
        return dc, sides[0], sides[1]

    def prepare(arrays: tuple[Array, ...]) -> Any:
        dc, c1, c2 = arrays
        return simrecon.prepare_empirical_volume_response(dc, c1=c1, c2=c2, voxel_size_um=spacing)

    arrays = components(b)
    base = prepare(arrays)
    shift = (1, 1, 0)
    rolled = prepare(tuple(np.roll(a, shift, axis=(0, 1, 2)) for a in arrays))
    physically_moved = prepare(components(moved_b))
    p = np.array([[0.125, -0.25, 0.125], [-0.25, 0.25, -0.125]])
    for order in (-2, -1, 1, 2):
        kw = arguments(p, order=order, calibration_carrier_bins=carrier)
        a = api(base, **kw).values
        # Storage translation did not change the underlying illumination phase;
        # subtract the translation from its common-coordinate sample declaration.
        rolled_kw = kw | {"coordinate_offset_yx": (-shift[1], -shift[2])}
        b_values = api(rolled, **rolled_kw).values
        c_values = api(physically_moved, **kw).values
        np.testing.assert_allclose(b_values, a, rtol=0.0, atol=2e-11)
        np.testing.assert_allclose(c_values, a, rtol=0.0, atol=2e-11)
        # Applying a physical-move declaration to merely rolled data is different.
        incorrect = api(rolled, **kw).values
        assert np.max(np.abs(incorrect - a)) > 0.01
