"""Blind public-contract tests for the three supplied axial-profile transfers."""

import warnings
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from typing import Any, Literal

import numpy as np
import pytest

import simrecon
from volume_order_fixture import (
    EPS,
    FIELDS,
    PRECISION,
    Array,
    F,
    Q,
    api,
    assert_frequencies,
    assert_frozen_bindings,
    assert_inputs_preserved,
    assert_values,
    budget,
    call,
    dec,
    direct,
    gains,
    modes,
    normalized_transform_observer,
    preserved_inputs,
    reject,
    root,
    snapshot_inputs,
    state,
    storage,
    unchanged,
)

# Importing api makes its pytest fixture visible; no implementation is inspected.
__all__ = ["api"]

# These algebraic witnesses use M<=24 and component gains<=7, with at
# most a factor-four phasor. This exceeds sums of the independent contractual
# error budgets plus ordinary observer rounding. The direct-sum observer above
# remains bound to the original, tighter per-sample budgets.
RELATION_TOL = float(1024 * 24 * EPS * 16)


def asymmetric() -> tuple[Array, Array]:
    psf = np.array(
        [
            [[1.0, 2.0, 0.0, 4.0], [3.0, 0.0, 7.0, 1.0]],
            [[0.0, 5.0, 2.0, 1.0], [6.0, 2.0, 0.0, 3.0]],
            [[4.0, 1.0, 3.0, 0.0], [0.0, 8.0, 1.0, 2.0]],
        ]
    )
    g = np.array([[2 + 3j, -1 + 0.5j, 0.25 - 2j], [-3 + 1j, 4 - 2j, -2 - 0.75j]])
    return psf, g


def check(
    api: Any,
    psf: Array,
    g: Array,
    origin: tuple[int, int, int] = (0, 0, 0),
    spacing: Any = (0.3, 0.7, 1.1),
) -> Any:
    expected = direct(psf, g, origin)
    with preserved_inputs(psf, g, spacing):
        result = call(api, psf, g, origin_zyx=origin, voxel_size_um=spacing)
    record_type = getattr(simrecon, "VolumeOrderOtf", None)
    assert isinstance(record_type, type)
    assert isinstance(result, record_type)
    assert result.values.shape == (3, *psf.shape)
    assert_values(result.values, expected, gains(g), psf.size)
    assert_frequencies(result, psf.shape, spacing)
    storage(result, psf, g)
    assert result.voxel_size_um == tuple(float(v) for v in spacing)
    assert all(type(v) is float for v in result.voxel_size_um)
    assert result.origin_zyx == origin
    assert all(type(v) is int for v in result.origin_zyx)
    assert result.source == " caller identity "
    return result


@pytest.mark.parametrize("origin", [(0, 0, 0), (2, 1, 3), (1, 0, 2)])
def test_signed_nonseparable_direct_sum(api: Any, origin: tuple[int, int, int]) -> None:
    p, g = asymmetric()
    result = check(api, p, g, origin)
    assert np.min(result.values.real) < -0.1
    assert np.max(np.abs(result.values.imag)) > 0.1
    detection = simrecon.prepare_volume_otf(
        p, voxel_size_um=(0.3, 0.7, 1.1), origin_zyx=origin, source="detection"
    )
    assert np.max(np.abs(result.values[0] - detection.values)) <= float(
        2 * budget(p.size, Decimal(1), True)
    )


def test_constant_gains_zero_dc_and_zero_rows(api: Any) -> None:
    p = np.ones((4, 2, 3))
    g = np.array([[2 + 3j] * 4, [1, -1, 1, -1]], dtype=np.complex128)
    result = check(api, p, g)
    dc = (2, 1, 1)
    assert abs(result.values[(1, *dc)] - (2 + 3j)) < RELATION_TOL
    assert abs(result.values[(2, *dc)]) < RELATION_TOL
    assert np.max(np.abs(result.values[2])) > 0.9  # Zero DC does not mean zero order.
    zero = check(api, p, np.zeros((2, 4), dtype=np.complex128))
    assert np.max(np.abs(zero.values[1:])) < RELATION_TOL
    doubled = check(api, p * 8, g)
    assert np.max(np.abs(result.values - doubled.values)) < RELATION_TOL
    phased = check(api, p, g * np.array([[1j], [-1j]]))
    assert np.max(np.abs(phased.values[1] - 1j * result.values[1])) < RELATION_TOL
    assert np.max(np.abs(phased.values[2] + 1j * result.values[2])) < RELATION_TOL


def test_joint_periodic_translation(api: Any) -> None:
    p, g = asymmetric()
    origin, shift = (2, 0, 1), (2, 1, 3)
    first = check(api, p, g, origin)
    moved = check(
        api,
        np.roll(p, shift, (0, 1, 2)),
        np.roll(g, shift[0], axis=1),
        tuple((o + s) % n for o, s, n in zip(origin, shift, p.shape, strict=True)),
    )
    assert np.max(np.abs(first.values - moved.values)) < RELATION_TOL


def test_axial_exact_phasor_and_cosine_shift(api: Any) -> None:
    p = np.array([[[1.0, 2.0, 4.0]], [[2.0, 0.0, 3.0]], [[7.0, 2.0, 1.0]], [[0.0, 5.0, 2.0]]])
    origin = (3, 0, 1)
    phasor: Any = np.array(
        [complex(*map(float, root(Fraction(-(z - origin[0]), 4)))) for z in range(4)]
    )
    g = np.stack([(2 - 3j) * phasor, phasor.real])
    result = check(api, p, g, origin)
    # kz-l in modular centered indexing, without changing ky/kx.
    assert (
        np.max(np.abs(result.values[1] - (2 - 3j) * np.roll(result.values[0], 1, axis=0)))
        < RELATION_TOL
    )
    cosine = (np.roll(result.values[0], 1, axis=0) + np.roll(result.values[0], -1, axis=0)) / 2
    assert np.max(np.abs(result.values[2] - cosine)) < RELATION_TOL


def test_negative_orders_use_modular_negation(api: Any) -> None:
    p, g = asymmetric()
    positive = check(api, p, g, (2, 1, 3))
    negative = check(api, p, g.conj(), (2, 1, 3))
    for index in product(*(range(n) for n in p.shape)):
        reflected = tuple(
            modes(n).index((-modes(n)[i] + n // 2) % n - n // 2)
            for n, i in zip(p.shape, index, strict=True)
        )
        for m in (1, 2):
            assert (
                abs(negative.values[(m, *index)] - positive.values[(m, *reflected)].conjugate())
                < RELATION_TOL
            )
    assert np.max(np.abs(negative.values[1] - positive.values[1, ::-1, ::-1, ::-1].conj())) > 0.1
    assert np.max(np.abs(positive.values[1] - negative.values[1])) > 0.1


DTYPES = [
    np.dtype(t).newbyteorder(e)
    for t in (
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        np.longdouble,
        np.complex64,
        np.complex128,
        np.clongdouble,
    )
    for e in ("<", ">")
]


@pytest.mark.parametrize("dtype", DTYPES, ids=lambda d: d.str)
def test_permitted_coefficient_widths_and_endian(api: Any, dtype: Any) -> None:
    p = np.array([[[1.0, 3.0]], [[2.0, 5.0]]])
    g = np.array([[2, 7], [3, 1]], dtype=dtype)
    if dtype.kind == "c":
        g += np.array([[3j, -2j], [-1j, 4j]], dtype=dtype)
    check(api, p, g, (1, 0, 1))


@pytest.mark.parametrize("layout", ["fortran", "strided", "reversed", "readonly"])
def test_storage_representations(api: Any, layout: str) -> None:
    p, g = asymmetric()
    pb, gb = p.copy(), g.copy()
    pbytes, gbytes = pb.tobytes(), gb.tobytes()
    if layout == "fortran":
        p, g = np.asfortranarray(p), np.asfortranarray(g)
    elif layout == "strided":
        pb, gb = np.full((3, 2, 8), 91.0), np.full((2, 6), 92 + 4j)
        pb[..., ::2], gb[:, ::2] = p, g
        p, g = pb[..., ::2], gb[:, ::2]
        pbytes, gbytes = pb.tobytes(), gb.tobytes()
    elif layout == "reversed":
        p, g = p[::-1, :, ::-1], g[:, ::-1]
    else:
        p.flags.writeable = g.flags.writeable = False
    check(api, p, g, (2, 1, 3))
    if layout == "strided":
        assert pb.tobytes() == pbytes and gb.tobytes() == gbytes


def test_large_integer_stored_conversion(api: Any) -> None:
    p = np.array([[[2**63 + 1, 2**63 + 4097]], [[2**64 - 1, 1]]], dtype=np.uint64)
    g = np.array([[2**63 + 1, 2**63 + 4097], [2**64 - 1, 0]], dtype=np.uint64)
    check(api, p, g)


class Subarray(np.ndarray):
    pass


@pytest.mark.parametrize(
    "value", [None, [[1, 2], [3, 4]], np.ones((2, 2)).view(Subarray), np.ma.array(np.ones((2, 2)))]
)
def test_coefficient_plain_array_required(api: Any, value: Any) -> None:
    reject(api, "invalid_volume_order_coefficients", np.ones((2, 1, 1)), value)


@pytest.mark.parametrize("dtype", ["?", "O", "U3", "S3", "M8[D]", "m8[D]", [("x", "f8")]])
def test_coefficient_invalid_kind(api: Any, dtype: Any) -> None:
    reject(
        api,
        "invalid_volume_order_coefficients_dtype",
        np.ones((2, 1, 1)),
        np.zeros((2, 2), dtype=dtype),
    )


@pytest.mark.parametrize("shape", [(), (2,), (1, 2), (3, 2), (2, 1), (2, 3), (2, 0), (2, 2, 1)])
def test_coefficient_shape(api: Any, shape: tuple[int, ...]) -> None:
    reject(api, "invalid_volume_order_coefficients_shape", np.ones((2, 1, 1)), np.ones(shape))


@pytest.mark.parametrize(
    "component",
    [
        complex(np.nan, 0),
        complex(np.inf, 0),
        complex(-np.inf, 0),
        complex(0, np.nan),
        complex(0, np.inf),
        complex(0, -np.inf),
    ],
)
def test_coefficient_nonfinite_source(api: Any, component: complex) -> None:
    g = np.ones((2, 2), dtype=np.complex128)
    g[1, 1] = component
    reject(api, "nonfinite_volume_order_coefficients", np.ones((2, 1, 1)), g)


def test_native_wider_coefficients_and_psf(api: Any) -> None:
    # A capability guard is not a skip or emulation. Executed native wider cases
    # are required on platforms where longdouble genuinely offers them.
    wider = np.finfo(np.longdouble)
    if wider.nmant > np.finfo(np.float64).nmant:
        g = np.ones((2, 2), dtype=np.clongdouble)
        g[0, 0] += np.longdouble(2) ** -60
        check(api, np.array([[[1]], [[3]]], dtype=np.longdouble), g)
    if wider.maxexp > np.finfo(np.float64).maxexp:
        too_large = np.longdouble(np.finfo(np.float64).max) * np.longdouble(2)
        for imaginary in (False, True):
            g = np.ones((2, 2), dtype=np.clongdouble)
            if imaginary:
                g.imag[1, 1] = too_large
            else:
                g.real[1, 1] = too_large
            reject(api, "nonfinite_volume_order_coefficients", np.ones((2, 1, 1)), g)
        reject(
            api,
            "nonfinite_psf",
            np.full((2, 1, 1), too_large, dtype=np.longdouble),
            np.ones((2, 2)),
        )
    if wider.minexp < np.finfo(np.float64).minexp:
        tiny = np.longdouble(float.fromhex("0x0.0000000000001p-1022")) / np.longdouble(4)
        g = np.ones((2, 2), dtype=np.clongdouble)
        g.real[0, 0], g.imag[1, 1] = tiny, -tiny
        check(api, np.ones((2, 1, 1)), g)
        p = np.array([[[1]], [[tiny]]], dtype=np.longdouble)
        check(api, p, g)
        p[1, 0, 0] = -tiny
        reject(api, "negative_psf", p, g)
        reject(api, "zero_psf_mass", np.full((2, 1, 1), tiny, dtype=np.longdouble), g)


@pytest.mark.parametrize(
    "psf,code",
    [
        ([[[1]]], "invalid_psf"),
        (np.ones((1, 1, 1)).view(Subarray), "invalid_psf"),
        (np.ones((1, 1, 1), dtype=bool), "invalid_psf_dtype"),
        (np.ones((1, 1, 1), dtype=complex), "invalid_psf_dtype"),
        (np.ones((1, 1)), "invalid_psf_shape"),
        (np.ones((1, 0, 1)), "invalid_psf_shape"),
        (np.array([[[np.nan]]]), "nonfinite_psf"),
        (np.array([[[np.inf]]]), "nonfinite_psf"),
        (np.array([[[-1.0]]]), "negative_psf"),
        (np.array([[[-0.0]]]), "zero_psf_mass"),
    ],
)
def test_inherited_psf_rules(api: Any, psf: Any, code: str) -> None:
    reject(api, code, psf, np.ones((2, 1)))


@pytest.mark.parametrize(
    "keyword,value,code",
    [
        ("voxel_size_um", (1, 2), "invalid_otf_voxel_size"),
        ("voxel_size_um", [True, 1, 1], "invalid_otf_voxel_size"),
        ("voxel_size_um", (1j, 1, 1), "invalid_otf_voxel_size"),
        ("voxel_size_um", (0, 1, 1), "invalid_otf_voxel_size"),
        ("voxel_size_um", (-1, 1, 1), "invalid_otf_voxel_size"),
        ("voxel_size_um", (np.inf, 1, 1), "invalid_otf_voxel_size"),
        ("voxel_size_um", (np.nan, 1, 1), "invalid_otf_voxel_size"),
        ("voxel_size_um", np.ones((1, 3)), "invalid_otf_voxel_size"),
        ("origin_zyx", (0, 0), "invalid_otf_origin"),
        ("origin_zyx", (0.0, 0, 0), "invalid_otf_origin"),
        ("origin_zyx", (False, 0, 0), "invalid_otf_origin"),
        ("origin_zyx", (-1, 0, 0), "invalid_otf_origin"),
        ("origin_zyx", (1, 0, 0), "invalid_otf_origin"),
        ("source", None, "invalid_otf_source"),
        ("source", " \t\n", "invalid_otf_source"),
    ],
)
def test_inherited_metadata_errors(api: Any, keyword: str, value: Any, code: str) -> None:
    reject(api, code, np.ones((1, 1, 1)), np.ones((2, 1)), **{keyword: value})


@pytest.mark.parametrize("container", [tuple, list, np.array])
def test_permitted_metadata_containers(api: Any, container: Any) -> None:
    p = np.array([[[-0.0, 2.0]]])
    spacing = container([np.float32(0.5), np.int64(2), np.float64(3)])
    origin = container([np.int64(0), np.int32(0), np.int64(1)])
    g = np.array([[2], [3 + 4j]])
    with preserved_inputs(p, g, spacing, origin):
        result = call(api, p, g, voxel_size_um=spacing, origin_zyx=origin)
    assert result.voxel_size_um == (0.5, 2.0, 3.0) and result.origin_zyx == (0, 0, 1)
    assert_frequencies(result, p.shape, spacing)


@pytest.mark.parametrize(
    "scale", [np.finfo(np.float64).max, float.fromhex("0x0.0000000000001p-1022"), 1.0]
)
def test_extreme_detection_mass(api: Any, scale: float) -> None:
    p = np.full((2, 2, 3), scale)
    g = np.array([[2 + 3j, -4 + 5j], [0, 7 - 2j]])
    check(api, p, g)


def test_componentwise_maximum_delta_gain(api: Any) -> None:
    maximum = float(F)
    p = np.zeros((3, 2, 4))
    p[2, 1, 3] = maximum
    g = np.full((2, 3), complex(maximum, maximum))
    result = check(api, p, g, (2, 1, 3))
    assert np.isfinite(result.values[1:].real).all()
    assert np.isfinite(result.values[1:].imag).all()
    # check's Decimal complex-error observer enforces the unchanged output
    # budget; finite inward rounding is permitted. Never compute F+iF magnitude.


@pytest.mark.parametrize(
    "case", ["uniform_interior", "nonuniform_interior", "small_outputs_large_gain"]
)
def test_safe_extreme_gains(api: Any, case: str) -> None:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        gain = float(F * Decimal("0.7"))
        assert dec(gain) * (Decimal(2).sqrt() + budget(24, Decimal(1), True)) < F
    p, g = asymmetric()
    if case == "uniform_interior":
        p[:] = float(F)
    if case == "small_outputs_large_gain":
        p[:] = 1
        p[0] = 0
        gain = float(F)
        g[:] = 0
        g[:, 0] = complex(gain, gain)
    else:
        g = np.array([[complex(gain, gain)] * 3, [complex(-gain, gain)] * 3])
    expected = direct(p, g, (2, 1, 3))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        gs = gains(g)
        for index, coordinates in expected.items():
            for component in coordinates:
                assert abs(component) + gs[index[0]] * budget(p.size, Decimal(1), True) <= F
    check(api, p, g, (2, 1, 3))


def test_cancellation_and_subnormal_final_rounding(api: Any) -> None:
    q = float(Q)
    p = np.ones((2, 1, 1))
    g = np.array([[q, 0], [q, -q]], dtype=np.complex128)
    expected = direct(p, g, (0, 0, 0))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        # Finite-precision Decimal sums need not equal the independently
        # evaluated analytic q/2 bit for bit. Observer error is negligible vs q.
        assert abs(expected[(1, 1, 0, 0)][0] - Q / 2) <= Q * Decimal("1e-118")
    check(api, p, g)
    p = np.array([[[1.0, float(Q)]], [[1.0, 0.0]]])
    g = np.array([[1 + 1j, -1 - 1j], [1 - 1j, -1 + 1j]])
    check(api, p, g)


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((1, 1, 1), (float(Q), float(F), 1.0)),
        ((2, 3, 4), (float(F), float(F), float(F))),
        ((3, 1, 2), (1e-308, float(Q), 1e-308)),
    ],
)
def test_representable_extreme_frequency_grids(
    api: Any, shape: tuple[int, ...], spacing: Any
) -> None:
    check(api, np.ones(shape), np.ones((2, shape[0])), spacing=spacing)


@pytest.mark.parametrize(
    "shape,spacing", [((2, 1, 1), (float(Q), 1.0, 1.0)), ((1, 2, 1), (1.0, float(Q), 1.0))]
)
def test_unrepresentable_frequency_grid(api: Any, shape: tuple[int, ...], spacing: Any) -> None:
    reject(
        api,
        "unrepresentable_otf_frequencies",
        np.ones(shape),
        np.ones((2, shape[0])),
        voxel_size_um=spacing,
    )


def test_record_frozen_all_fields_and_independent_calls(api: Any) -> None:
    p, g = asymmetric()
    first, second = check(api, p, g), check(api, p, g)
    storage(first, p, g, second)
    assert_frozen_bindings(first)
    second_before, inputs_before = state(second), snapshot_inputs(p, g)
    for name in FIELDS[:4]:
        before = state(first)
        array = getattr(first, name)
        array.flat[0] = 123
        after = state(first)
        for other, saved, actual in zip(FIELDS, before, after, strict=True):
            if other != name:
                assert actual == saved
        unchanged(second, second_before)
        assert_inputs_preserved(inputs_before)
    # The record must permit direct construction without validation; it need not
    # be a dataclass, expose __dict__, or use a particular exception subclass.
    fields = {name: getattr(second, name) for name in FIELDS}
    fields["source"] = ""
    constructor = getattr(simrecon, "VolumeOrderOtf", None)
    assert callable(constructor)
    record: Any = constructor(**fields)
    assert record.source == ""
    assert record.values.shape == second.values.shape


def test_snapshot_both_inputs_before_transform(api: Any, monkeypatch: Any) -> None:
    p, g = asymmetric()
    expected, gs = direct(p, g, (2, 1, 3)), gains(g)
    original = np.fft.fftn

    def mutate(*args: Any, **kwargs: Any) -> Any:
        p[:] = 0
        g[:] = 999 - 333j
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", mutate)
    result = call(api, p, g, origin_zyx=(2, 1, 3))
    assert_values(result.values, expected, gs, p.size)


@pytest.mark.parametrize("extreme", [False, True])
def test_normalized_transform_seam_and_delta(api: Any, monkeypatch: Any, extreme: bool) -> None:
    p, g = asymmetric()
    if extreme:
        g *= float(F) * 0.15
        p *= float(F) / 8
    origin = (2, 1, 3)
    observe, observed = normalized_transform_observer(p, g, origin, np.fft.fftn)
    monkeypatch.setattr(np.fft, "fftn", observe)
    check(api, p, g, origin)
    assert observed == {0, 1, 2}


@pytest.mark.parametrize(
    "failure",
    [FloatingPointError("controlled"), OverflowError("controlled"), RuntimeWarning("controlled")],
)
def test_handled_transform_exceptions(api: Any, monkeypatch: Any, failure: Exception) -> None:
    p, g = asymmetric()

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise failure

    monkeypatch.setattr(np.fft, "fftn", fail)
    reject(api, "volume_order_transform_failure", p, g)


@pytest.mark.parametrize(
    "component", [complex(np.nan, 0), complex(np.inf, 0), complex(0, np.nan), complex(0, np.inf)]
)
def test_nonfinite_normalized_transform(api: Any, monkeypatch: Any, component: complex) -> None:
    p, g = asymmetric()

    def fail(a: Any, *args: Any, **kwargs: Any) -> Any:
        return np.full(np.shape(a), component, dtype=np.complex128)

    monkeypatch.setattr(np.fft, "fftn", fail)
    reject(api, "volume_order_transform_failure", p, g)


@pytest.mark.parametrize("caller_filter", ["always", "ignore"])
def test_emitted_arithmetic_warning_translation(
    api: Any, monkeypatch: Any, caller_filter: Literal["always", "ignore"]
) -> None:
    p, g = asymmetric()
    original = np.fft.fftn

    def warn(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("controlled arithmetic", RuntimeWarning, stacklevel=1)
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter(caller_filter, RuntimeWarning)
        floating, filters = np.geterr(), list(warnings.filters)
        reject(api, "volume_order_transform_failure", p, g)
        assert np.geterr() == floating and warnings.filters == filters
    assert not any(issubclass(w.category, RuntimeWarning) for w in seen)


@pytest.mark.parametrize(
    "failure",
    [
        MemoryError("controlled"),
        RuntimeError("controlled"),
        TypeError("controlled"),
        ValueError("controlled"),
        UserWarning("controlled"),
    ],
)
def test_unrelated_transform_exceptions_propagate(
    api: Any, monkeypatch: Any, failure: Exception
) -> None:
    p, g = asymmetric()
    floating, filters = np.geterr(), list(warnings.filters)

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise failure

    monkeypatch.setattr(np.fft, "fftn", fail)
    with preserved_inputs(p, g), pytest.raises(type(failure)) as caught:
        call(api, p, g)
    assert caught.value is failure
    assert np.geterr() == floating and warnings.filters == filters


@pytest.mark.parametrize("component", [2 + 0j, 0 + 2j])
@pytest.mark.parametrize("policy", ["ignore", "warn", "raise"])
def test_finite_normalized_rescaling_overflow(
    api: Any, monkeypatch: Any, component: complex, policy: Literal["ignore", "warn", "raise"]
) -> None:
    p = np.ones((2, 1, 1))
    g = np.full((2, 2), float(F), dtype=np.complex128)

    def finite(a: Any, *args: Any, **kwargs: Any) -> Any:
        return np.full(np.shape(a), component, dtype=np.complex128)

    monkeypatch.setattr(np.fft, "fftn", finite)
    with np.errstate(all=policy), warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        before, filters = np.geterr(), list(warnings.filters)
        reject(api, "unrepresentable_volume_order_otf", p, g)
        assert np.geterr() == before and warnings.filters == filters
        assert not any(issubclass(w.category, RuntimeWarning) for w in seen)


@pytest.mark.parametrize("policy", ["ignore", "warn", "raise"])
def test_caller_policy_success_failure_and_unrelated_warnings(
    api: Any, monkeypatch: Any, policy: Literal["ignore", "warn", "raise"]
) -> None:
    old = np.seterr(all=policy)
    try:
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always")
            filters = list(warnings.filters)
            p = np.full((2, 1, 1), float(Q))
            g = np.full((2, 2), complex(float(F) / 2, float(F) / 2))
            check(api, p, g)
            reject(
                api, "nonfinite_volume_order_coefficients", p, np.full((2, 2), complex(np.inf, 0))
            )
            original = np.fft.fftn

            def warn(*args: Any, **kwargs: Any) -> Any:
                warnings.warn("unrelated category retained", UserWarning, stacklevel=1)
                return original(*args, **kwargs)

            monkeypatch.setattr(np.fft, "fftn", warn)
            check(api, p, g)
            assert any(issubclass(w.category, UserWarning) for w in seen)
            assert not any(issubclass(w.category, RuntimeWarning) for w in seen)
            assert np.geterr() == dict.fromkeys(old, policy)
            assert warnings.filters == filters

            def fail(*args: Any, **kwargs: Any) -> Any:
                raise FloatingPointError("controlled")

            monkeypatch.setattr(np.fft, "fftn", fail)
            reject(api, "volume_order_transform_failure", p, g)
            assert np.geterr() == dict.fromkeys(old, policy) and warnings.filters == filters
    finally:
        np.seterr(**old)


def test_python_binding(api: Any) -> None:
    p, g = asymmetric()
    kwargs = dict(axial_coefficients=g, voxel_size_um=(1, 1, 1), origin_zyx=(0, 0, 0), source="s")
    with preserved_inputs(p, g):
        for omitted in kwargs:
            with pytest.raises(TypeError):
                api(p, **{k: v for k, v in kwargs.items() if k != omitted})
        with pytest.raises(TypeError):
            api(p, g, (1, 1, 1), (0, 0, 0), "s")
        with pytest.raises(TypeError):
            api(p, extra=True, **kwargs)


def test_circular_forward_model_and_real_phase_separation(api: Any) -> None:
    p, g = asymmetric()
    origin = (2, 1, 3)
    result = check(api, p, g, origin)
    shape = p.shape
    specimen = np.arange(1, p.size + 1, dtype=float).reshape(shape) / 8
    fields = [np.empty(shape, dtype=np.complex128) for _ in range(3)]
    for m in range(3):
        for r in product(*(range(n) for n in shape)):
            # Caller-known lateral carrier, outside preparation.
            phase = root(Fraction(-m * r[2], shape[2]))
            fields[m][r] = specimen[r] * complex(float(phase[0]), float(phase[1]))
    kernels = [p / p.sum()] + [(p / p.sum()) * g[m, :, None, None] for m in range(2)]
    circular = [np.zeros(shape, dtype=np.complex128) for _ in range(3)]
    for m in range(3):
        for r in product(*(range(n) for n in shape)):
            for t in product(*(range(n) for n in shape)):
                src = tuple(
                    (ri - (ti - oi)) % n for ri, ti, oi, n in zip(r, t, origin, shape, strict=True)
                )
                circular[m][r] += kernels[m][t] * fields[m][src]
    # Independently sum forward and inverse roots. NumPy FFT is never the oracle.
    for m in range(3):
        spectrum = {}
        for k in product(*(modes(n) for n in shape)):
            terms = [
                fields[m][r]
                * complex(
                    *map(
                        float,
                        root(
                            sum(
                                (
                                    Fraction(ki * ri, n)
                                    for ki, ri, n in zip(k, r, shape, strict=True)
                                ),
                                Fraction(0),
                            )
                        ),
                    )
                )
                for r in product(*(range(n) for n in shape))
            ]
            spectrum[k] = sum(terms)
        predicted = np.zeros(shape, dtype=np.complex128)
        for r in product(*(range(n) for n in shape)):
            for index in product(*(range(n) for n in shape)):
                k = tuple(modes(n)[j] for n, j in zip(shape, index, strict=True))
                phase = root(
                    -sum(
                        (Fraction(ki * ri, n) for ki, ri, n in zip(k, r, shape, strict=True)),
                        Fraction(0),
                    )
                )
                predicted[r] += (
                    result.values[(m, *index)] * spectrum[k] * complex(*map(float, phase)) / p.size
                )
        max_u = float(np.max(np.abs(fields[m])))
        spectrum_l1 = sum(abs(v) for v in spectrum.values())
        gain = gains(g)[m]
        # Transform-output error propagated through the inverse direct sum,
        # plus a conservative allowance for finite ordinary-sized observer sums.
        allowance = (
            float(budget(p.size, gain, m == 0)) * spectrum_l1 / p.size
            + 4096 * p.size * float(EPS) * float(gain) * max_u
        )
        assert np.max(np.abs(predicted - circular[m])) <= allowance
    phases = np.arange(7) * 2 * np.pi / 7 + 0.17
    c, s = np.cos(phases), np.sin(phases)
    c2, s2 = c * c - s * s, (2 * c) * s
    images = (
        circular[0].real[None]
        + 2 * c[:, None, None, None] * circular[1].real
        - 2 * s[:, None, None, None] * circular[1].imag
        + 2 * c2[:, None, None, None] * circular[2].real
        - 2 * s2[:, None, None, None] * circular[2].imag
    )
    components = simrecon.separate_volume_phases(images, phases_rad=phases)
    for actual, expected in zip(
        (components.dc, components.c1, components.c2), circular, strict=True
    ):
        # The represented seven equally spaced rows have condition near sqrt(2).
        # 8192*N*eps*B is the inherited coordinate budget. An additional
        # 512*N*eps*B covers forming the rounded real observations above.
        allowance = 8704 * len(phases) * float(EPS) * np.max(np.abs(images), axis=0)
        assert np.all(np.abs(actual.real - expected.real) <= allowance)
        assert np.all(np.abs(actual.imag - expected.imag) <= allowance)


def test_mixed_maximum_and_subnormal_detection_samples(api: Any) -> None:
    p, g = asymmetric()
    p[:] = float(Q)
    p[2, 1, 3] = float(F)
    check(api, p, g, (1, 0, 2))
