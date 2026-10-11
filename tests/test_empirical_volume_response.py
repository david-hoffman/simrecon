"""Blind public-contract tests for empirical bead-referenced response C2."""

import inspect
import warnings
from collections.abc import Callable
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import permutations
from typing import Any, Literal, cast

import numpy as np
import pytest

import simrecon
from empirical_response_fixture import (
    EPS,
    PRECISION,
    Array,
    F,
    Q,
    assert_direct,
    asymmetric,
    dec,
    direct_response,
    dyadic,
    frequencies,
    represented_fit,
)

# Dynamic public lookup keeps the owned quality check independent of the absent
# additive exports. Absence is a collection failure, never a skip or xfail.
EXPORT_NAMES = ("prepare_empirical_volume_response", "EmpiricalVolumeResponse")
prepare = cast(Callable[..., Any], getattr(simrecon, EXPORT_NAMES[0]))
Response = cast(type[Any], getattr(simrecon, EXPORT_NAMES[1]))
SPACING = (0.25, 0.125, 0.5)
MAX = float(np.finfo(np.float64).max)
TINY = float.fromhex("0x0.0000000000001p-1022")


def run(dc: Any, c1: Any = None, c2: Any = None, spacing: Any = SPACING) -> Any:
    if c1 is None:
        c1 = np.zeros_like(dc, dtype=np.complex128)
    if c2 is None:
        c2 = np.zeros_like(dc, dtype=np.complex128)
    return prepare(dc, c1=c1, c2=c2, voxel_size_um=spacing)


def reject(code: str, dc: Any, c1: Any = None, c2: Any = None, spacing: Any = SPACING) -> None:
    supplied = [a for a in (dc, c1, c2, spacing) if type(a) is np.ndarray]
    snapshots = [(a.tobytes(), a.shape, a.strides, a.dtype, a.flags.writeable) for a in supplied]
    with pytest.raises(simrecon.SimreconError) as error:
        run(dc, c1, c2, spacing)
    assert error.value.code == code
    assert snapshots == [
        (a.tobytes(), a.shape, a.strides, a.dtype, a.flags.writeable) for a in supplied
    ]


def checked(dc: Array, c1: Array, c2: Array, spacing: Any = SPACING) -> Any:
    expectation = direct_response(dc, c1, c2)
    result = run(dc, c1, c2, spacing)
    assert_direct(result.values, expectation)
    assert result.origin_zyx == expectation.origin
    assert result.values[(0, *(n // 2 for n in dc.shape))] == 1 + 0j
    return result


def agreement(left: Array, right: Array, budget: Decimal, gain: complex = 1 + 0j) -> None:
    """Supplemental metamorphic check using independently derived budgets."""
    with localcontext() as ctx:
        ctx.prec = PRECISION
        gr, gi = dec(dyadic(gain.real)), dec(dyadic(gain.imag))
        for index in np.ndindex(left.shape):
            lr, li = dec(dyadic(left[index].real)), dec(dyadic(left[index].imag))
            rr, ri = dec(dyadic(right[index].real)), dec(dyadic(right[index].imag))
            dr, di = lr - (rr * gr - ri * gi), li - (rr * gi + ri * gr)
            assert (dr * dr + di * di).sqrt() <= budget + budget * Decimal("1e-80")


def test_public_binding_record_and_native_storage() -> None:
    dc, c1, c2 = asymmetric()
    result = checked(dc, c1, c2)
    assert isinstance(result, Response)
    fields = {"values", "fz_per_um", "fy_per_um", "fx_per_um", "voxel_size_um", "origin_zyx"}
    assert {
        n for n in dir(result) if not n.startswith("_") and not callable(getattr(result, n))
    } == fields
    for field in fields:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, field, getattr(result, field))
    assert type(result.voxel_size_um) is tuple
    assert all(type(v) is float for v in result.voxel_size_um)
    assert type(result.origin_zyx) is tuple
    assert all(type(v) is int for v in result.origin_zyx)
    arrays = [result.values, result.fz_per_um, result.fy_per_um, result.fx_per_um]
    for i, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.dtype == np.dtype(np.complex128 if i == 0 else np.float64)
        assert array.dtype.isnative and array.flags.c_contiguous and array.flags.owndata
        assert array.flags.writeable
        assert all(not np.shares_memory(array, a) for a in (dc, c1, c2, *arrays[:i]))
    kwargs = {name: getattr(result, name) for name in fields}
    kwargs["origin_zyx"] = ("unchecked",)
    assert Response(**kwargs).origin_zyx == ("unchecked",)
    assert inspect.signature(prepare).parameters["dc"].kind in (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    for name in ("c1", "c2", "voxel_size_um"):
        assert inspect.signature(prepare).parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
    for kwargs in ({}, {"c1": c1}, {"c1": c1, "c2": c2}):
        with pytest.raises(TypeError):
            prepare(dc, **kwargs)
    with pytest.raises(TypeError):
        prepare(dc, c1, c2, SPACING)
    with pytest.raises(TypeError):
        prepare(dc, c1=c1, c2=c2, voxel_size_um=SPACING, origin_zyx=(0, 0, 0))
    with pytest.raises(TypeError):
        prepare(c1=c1, c2=c2, voxel_size_um=SPACING)


@pytest.mark.parametrize("shape", [(2, 3, 4), (3, 2, 3), (1, 3, 4), (2, 1, 1), (1, 1, 1)])
def test_asymmetric_signed_complex_direct_sum(shape: tuple[int, int, int]) -> None:
    checked(*asymmetric(shape))


@pytest.mark.parametrize("origin", [(0, 0, 0), (1, 2, 3), (0, 2, 1), (1, 0, 3)])
def test_periodic_joint_roll_and_observed_origin(origin: tuple[int, int, int]) -> None:
    components = asymmetric()
    initial = checked(*components)
    shift = tuple(b - a for a, b in zip(initial.origin_zyx, origin, strict=True))
    moved = tuple(np.roll(a, shift, axis=(0, 1, 2)) for a in components)
    result = checked(*moved)
    assert result.origin_zyx == origin
    # Permit transform roundoff rather than impose bitwise equivalence.
    for order, budget in enumerate(direct_response(*components).budgets):
        agreement(result.values[order], initial.values[order], 2 * budget)


def test_common_relative_gain_zero_dc_and_full_zero_order_shape() -> None:
    dc = np.array([[[2.0, -1.0, 0.5, 0.0]]])
    c1 = np.array([[[1 + 2j, -1 - 2j, 0j, 0j]]])
    c2 = np.zeros_like(c1)
    result = checked(dc, c1, c2)
    assert result.values[1, 0, 0, 2] == 0
    np.testing.assert_array_equal(result.values[2], 0)
    assert result.values[0, 0, 0, 0].real > 1
    assert abs(result.values[0, 0, 0, 1].imag) > 0
    gain = -2 + 3j
    changed = checked(dc, c1 * gain, c2)
    before = direct_response(dc, c1, c2)
    after = direct_response(dc, c1 * gain, c2)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        agreement(
            changed.values[1],
            result.values[1],
            after.budgets[1] + Decimal(13).sqrt() * before.budgets[1],
            gain,
        )
    scaled = checked(dc * 8, c1 * 8, c2 * 8)
    for order, budget in enumerate(before.budgets):
        agreement(scaled.values[order], result.values[order], 2 * budget)


def test_positive_near_tie_and_lower_ties_are_not_isolation_errors() -> None:
    dc = np.array([[[1.0, np.nextafter(1.0, 0.0), -0.25, -0.25]]])
    result = checked(dc, np.zeros_like(dc), np.ones_like(dc))
    assert result.origin_zyx == (0, 0, 0)
    dc = np.array([[[2.0, 1.5, -0.5, -0.5]]])
    assert checked(dc, dc, dc).origin_zyx == (0, 0, 0)


@pytest.mark.parametrize(
    "dc,code",
    [
        ([-1.0, -2.0], "no_positive_bead_peak"),
        ([0.0, -0.0], "no_positive_bead_peak"),
        ([2.0, 2.0], "ambiguous_bead_peak"),
        ([1.0, 0.0, 1.0], "ambiguous_bead_peak"),
        ([2.0, -2.0], "nonpositive_empirical_response_mass"),
        ([2.0, -3.0], "nonpositive_empirical_response_mass"),
    ],
)
def test_peak_and_mass_rejections(dc: list[float], code: str) -> None:
    reject(code, np.array(dc).reshape(1, 1, -1))


def test_conversion_created_peak_tie() -> None:
    dc = np.array([[[2**53, 2**53 + 1]]], dtype=np.uint64)
    reject("ambiguous_bead_peak", dc)


@pytest.mark.parametrize(
    "samples",
    [
        [2**53, 1, -(2**53), 4],
        [2.0**500, -(2.0**499), -(2.0**499), 1],
        [2 * TINY, -TINY],
        [MAX, MAX / 2],
        [TINY],
    ],
)
def test_exact_mass_and_finite_success_without_conditioning_cutoff(samples: list[float]) -> None:
    dc = np.array(samples, dtype=np.float64).reshape(1, 1, -1)
    c1 = dc.astype(np.complex128) * (0.5 + 0.25j)
    c2 = np.zeros_like(c1)
    expected = direct_response(dc, c1, c2)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index in np.ndindex(expected.values.shape):
            for component in expected.values[index]:
                assert abs(component) + expected.budgets[index[0]] < dec(F)
    checked(dc, c1, c2)


def test_overflowing_mass_complex_magnitude_and_product_are_not_rejections() -> None:
    dc = np.array([[[MAX, MAX / 2]]])
    c1 = np.empty(dc.shape, dtype=np.complex128)
    c1.real[:] = MAX
    c1.imag[:] = MAX
    result = checked(dc, c1, np.zeros_like(c1))
    assert result.values[1, 0, 0, 1].real == float(Fraction(4, 3))
    assert result.values[1, 0, 0, 1].imag == float(Fraction(4, 3))


def test_subnormal_mass_and_underflowed_gain_restoration() -> None:
    dc = np.array([[[TINY]]])
    side = np.empty_like(dc, dtype=np.complex128)
    side.real[:] = TINY
    side.imag[:] = TINY
    assert checked(dc, side, np.zeros_like(side)).values[1, 0, 0, 0] == 1 + 1j
    dc = np.zeros((1, 1, 32))
    dc[0, 0, 0] = MAX
    side = np.full(dc.shape, 2.0**-53)
    result = checked(dc, side, -side)
    exact = float(Fraction(32) * dyadic(2.0**-53) / F)
    assert exact > 0
    assert result.values[1, 0, 0, 16].real == exact
    assert result.values[2, 0, 0, 16].real == -exact


def test_componentwise_maximum_boundary_still_attempts_success() -> None:
    dc = np.ones((1, 1, 1))
    side = np.empty(dc.shape, dtype=np.complex128)
    side.real[:] = MAX
    side.imag[:] = -MAX
    result = checked(dc, side, side)
    assert result.values[1, 0, 0, 0].real == MAX
    assert result.values[1, 0, 0, 0].imag == -MAX


@pytest.mark.parametrize("which", [1, 2])
@pytest.mark.parametrize("side", [1 + 0j, 0 + 1j, 1 + 1j])
def test_whole_call_final_component_range_error(side: complex, which: int) -> None:
    dc = np.full((1, 1, 1), TINY)
    parts = [dc, np.zeros_like(dc), np.zeros_like(dc)]
    parts[which] = np.full(dc.shape, side)
    reject("unrepresentable_empirical_response", *parts)


def test_non_dc_final_range_is_checked_for_zero_and_side_orders() -> None:
    reject("unrepresentable_empirical_response", np.array([[[MAX, -MAX, TINY, 0]]]))
    dc = np.array([[[2 * TINY, -TINY]]])
    side = np.array([[[MAX, -MAX]]])
    reject("unrepresentable_empirical_response", dc, side, side)


def test_rational_restoration_retains_signed_underflow() -> None:
    dc = np.array([[[MAX, 0.0, 0.0, 0.0]]])
    side = np.empty_like(dc, dtype=np.complex128)
    side.real[:] = -TINY
    side.imag[:] = TINY
    result = checked(dc, side, side)
    for order in (1, 2):
        value = result.values[order, 0, 0, 2]
        assert value.real == 0 and np.signbit(value.real)
        assert value.imag == 0 and not np.signbit(value.imag)


def test_phase_gauge_and_modular_negative_orders() -> None:
    dc, c1, c2 = asymmetric((2, 3, 4))
    result = checked(dc, c1, c2)
    # alpha=pi/2 gives exact exp(-i*m*alpha), distinguishing sign and order.
    rephased = checked(dc, -1j * c1, -c2)
    budgets = direct_response(dc, c1, c2).budgets
    agreement(rephased.values[1], result.values[1], 2 * budgets[1], -1j)
    agreement(rephased.values[2], result.values[2], 2 * budgets[2], -1 + 0j)
    negative = direct_response(dc, np.conj(c1), np.conj(c2))
    shape = dc.shape
    indexes = [np.array([((-(s - n // 2)) % n + n // 2) % n for s in range(n)]) for n in shape]
    modular = result.values[1:][:, indexes[0]][:, :, indexes[1]][:, :, :, indexes[2]].conj()
    combined = result.values.copy()
    combined[1:] = modular
    assert_direct(combined, negative)
    assert not np.allclose(modular, result.values[1:].conj())
    assert not np.allclose(modular, result.values[1:, ::-1, ::-1, ::-1].conj())
    # Even negative Nyquist bins are their own modular negatives.
    assert indexes[0][0] == 0 and indexes[2][0] == 0


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((2, 3, 4), SPACING),
        ((3, 4, 1), [np.int16(2), np.float32(0.5), np.float64(0.25)]),
        ((1, 1, 1), (TINY, MAX, 1)),
        ((4, 3, 1), (MAX, MAX, TINY)),
        ((2, 1, 1), (2.0**-1024, 1, 1)),
        ((2, 3, 4), np.array([0.25, 0.125, 0.5], dtype=object)),
    ],
)
def test_native_frequency_grammar_accuracy_and_safe_periods(
    shape: tuple[int, int, int], spacing: Any
) -> None:
    result = checked(*asymmetric(shape), spacing=spacing)
    converted = tuple(float(d) for d in spacing)
    assert result.voxel_size_um == converted
    for n, d, returned in zip(
        shape, converted, (result.fz_per_um, result.fy_per_um, result.fx_per_um), strict=True
    ):
        assert returned.shape == (n,)
        assert np.all(np.isfinite(returned))
        assert np.all(returned[1:] > returned[:-1])
        exact = frequencies(n, d)
        for actual, target in zip(returned, exact, strict=True):
            assert abs(dyadic(actual) - target) <= 8 * EPS * abs(target) + Q
            assert (actual == 0) == (target == 0)
        assert returned[n // 2] == 0
        if n > 1:
            assert returned[0] < 0
        if n % 2 == 0:
            assert exact[0] == -Fraction(1, 2) / dyadic(d)


@pytest.mark.parametrize(
    "spacing",
    [
        None,
        1,
        "abc",
        (1, 1),
        (1, 1, 1, 1),
        np.ones((1, 3)),
        range(3),
        {"z": 1, "y": 1, "x": 1},
        (True, 1, 1),
        (np.bool_(True), 1, 1),
        (1 + 0j, 1, 1),
        ("1", 1, 1),
        (0, 1, 1),
        (-1, 1, 1),
        (np.nan, 1, 1),
        (np.inf, 1, 1),
        (10**1000, 1, 1),
    ],
)
def test_invalid_spacing(spacing: Any) -> None:
    reject("invalid_otf_voxel_size", np.ones((1, 1, 1)), spacing=spacing)


@pytest.mark.parametrize("container", ["subclass", "masked"])
def test_spacing_requires_plain_ndarray(container: str) -> None:
    spacing = np.array(SPACING)
    bad = spacing.view(SubArray) if container == "subclass" else np.ma.array(spacing)
    reject("invalid_otf_voxel_size", np.ones((1, 1, 1)), spacing=bad)


@pytest.mark.parametrize("axis", [0, 1, 2])
def test_unrepresentable_final_frequency(axis: int) -> None:
    shape = [1, 1, 1]
    shape[axis] = 2
    dc = np.zeros(tuple(shape))
    dc.flat[0] = 1
    spacing = [1.0, 1.0, 1.0]
    spacing[axis] = TINY
    reject("unrepresentable_otf_frequencies", dc, spacing=spacing)


class SubArray(np.ndarray[Any, Any]):
    """Unsupported ndarray subclass paired with a plain-array positive."""


@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize("form", ["list", "scalar", "subclass", "masked"])
def test_nonarray_and_subclass_components(which: int, form: str) -> None:
    parts: list[Any] = list(asymmetric())
    plain = parts[which]
    bad = {
        "list": plain.tolist(),
        "scalar": 1,
        "subclass": plain.view(SubArray),
        "masked": np.ma.array(plain),
    }[form]
    checked(*parts)
    parts[which] = bad
    reject("invalid_empirical_response_array", *parts)


BAD_DTYPES = [
    np.dtype("?"),
    np.dtype("O"),
    np.dtype("U2"),
    np.dtype("S2"),
    np.dtype([("v", "f8")]),
    np.dtype("datetime64[D]"),
    np.dtype("timedelta64[D]"),
]


@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize("dtype", BAD_DTYPES, ids=str)
def test_rejected_dtype_families(which: int, dtype: np.dtype[Any]) -> None:
    parts: list[Any] = list(asymmetric())
    bad = np.zeros(parts[which].shape, dtype=dtype)
    if dtype.fields is not None:
        bad.flat[0] = (2,)
    else:
        bad.flat[0] = 2
        if dtype.kind in "US":
            bad.flat[1:] = "0"
    parts[which] = bad
    reject("invalid_empirical_response_dtype", *parts)


def test_complex_dc_rejected_but_real_side_orders_are_valid() -> None:
    dc, _, _ = asymmetric()
    checked(dc, dc.astype(np.int16), dc.astype(np.float32))
    reject("invalid_empirical_response_dtype", dc.astype(np.complex128))


@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize(
    "shape", [(), (2, 3), (1, 2, 3, 4), (0, 3, 4), (2, 0, 4), (2, 3, 0), (2, 3, 1)]
)
def test_rank_empty_and_shape_mismatch(which: int, shape: tuple[int, ...]) -> None:
    parts: list[Any] = list(asymmetric())
    bad = np.zeros(shape)
    if bad.size:
        bad.flat[0] = 1
    parts[which] = bad
    reject("invalid_empirical_response_shape", *parts)


@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_source_real_components(which: int, value: float) -> None:
    parts = list(asymmetric())
    parts[which].real.flat[-1] = value
    reject("nonfinite_empirical_response_array", *parts)


@pytest.mark.parametrize("which", [1, 2])
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nonfinite_source_imaginary_components(which: int, value: float) -> None:
    parts = list(asymmetric())
    parts[which].imag.flat[-1] = value
    reject("nonfinite_empirical_response_array", *parts)


# Available native widths are registered, never skipped. NumPy longdouble may
# alias binary64; that capability is separately exported in A's evidence.
REAL_DTYPES = list(
    dict.fromkeys(
        np.dtype(d)
        for d in ("i1", "u1", "i2", "u2", "i4", "u4", "i8", "u8", "f2", "f4", "f8", np.longdouble)
    )
)
SIDE_DTYPES = REAL_DTYPES + list(dict.fromkeys(np.dtype(d) for d in ("c8", "c16", np.clongdouble)))


@pytest.mark.parametrize("dtype", REAL_DTYPES, ids=str)
@pytest.mark.parametrize("byteorder", ["<", ">"])
def test_real_storage_widths_endian_and_conversion(
    dtype: np.dtype[Any], byteorder: Literal["<", ">"]
) -> None:
    dc = np.array([[[2, 1, 0, 0]]], dtype=dtype.newbyteorder(byteorder))
    checked(dc, dc, dc)


@pytest.mark.parametrize("dtype", SIDE_DTYPES, ids=str)
@pytest.mark.parametrize("byteorder", ["<", ">"])
def test_side_storage_widths_endian_and_conversion(
    dtype: np.dtype[Any], byteorder: Literal["<", ">"]
) -> None:
    dc = np.array([[[2.0, 1.0, 0, 0]]])
    side: Array = np.array([[[3, 1, 0, 2]]], dtype=dtype.newbyteorder(byteorder))
    if dtype.kind == "c":
        side.imag[:] = np.array([[[2, -1, 3, -4]]])
    checked(dc, side, side)


@pytest.mark.parametrize("storage", ["fortran", "readonly", "strided", "reversed"])
def test_storage_layout_input_preservation_and_owned_results(storage: str) -> None:
    parts = list(asymmetric())
    if storage == "fortran":
        parts = [np.asfortranarray(a) for a in parts]
    elif storage == "readonly":
        for a in parts:
            a.flags.writeable = False
    elif storage == "strided":
        larger = [np.zeros((2, 3, 8), dtype=a.dtype) for a in parts]
        for backing, a in zip(larger, parts, strict=True):
            backing[:, :, ::2] = a
        parts = [a[:, :, ::2] for a in larger]
    else:
        parts = [a[::-1, :, ::-1] for a in parts]
    before = [a.tobytes() for a in parts]
    result = checked(*parts)
    another = checked(*parts)
    assert before == [a.tobytes() for a in parts]
    for name in ("values", "fz_per_um", "fy_per_um", "fx_per_um"):
        output = getattr(result, name)
        assert not np.shares_memory(output, getattr(another, name))
        output.flat[0] = 17
    assert before == [a.tobytes() for a in parts]
    assert another.values[0, 1, 1, 2] == 1
    bad = parts[0].copy()
    bad.flat[-1] = np.nan
    rejected = [bad, *parts[1:]]
    snapshots = [a.tobytes() for a in rejected]
    reject("nonfinite_empirical_response_array", *rejected)
    assert snapshots == [a.tobytes() for a in rejected]


def test_represented_large_integer_side_values() -> None:
    dc = np.array([[[3, 1]]], dtype=np.uint64)
    side = np.array([[[2**53 + 1, 2**53 + 3]]], dtype=np.uint64)
    checked(dc, side, side)


WIDER_RANGE = np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp
WIDER_PRECISION = np.finfo(np.longdouble).nmant > np.finfo(np.float64).nmant

if WIDER_RANGE:

    @pytest.mark.parametrize("which", [0, 1, 2])
    def test_wider_finite_source_conversion_overflow(which: int) -> None:
        parts: list[Any] = list(asymmetric())
        array = np.array(parts[which], dtype=np.longdouble if which == 0 else np.clongdouble)
        array.real.flat[-1] = np.longdouble(MAX) * np.longdouble(2)
        parts[which] = array
        reject("nonfinite_empirical_response_array", *parts)

    @pytest.mark.parametrize("which", [1, 2])
    def test_wider_finite_imaginary_source_conversion_overflow(which: int) -> None:
        parts: list[Any] = list(asymmetric())
        array: Array = np.array(parts[which], dtype=np.clongdouble)
        parts[which] = array
        checked(*parts)
        array.imag.flat[-1] = np.longdouble(MAX) * np.longdouble(2)
        assert np.all(np.isfinite(array.real)) and np.all(np.isfinite(array.imag))
        assert array.imag.flat[-1] > np.longdouble(MAX)
        reject("nonfinite_empirical_response_array", *parts)

    def test_wider_finite_underflow_defines_converted_problem() -> None:
        dc = np.array([[[1, 0]]], dtype=np.longdouble)
        dc.flat[-1] = np.longdouble(TINY) / np.longdouble(4)
        checked(dc, dc, dc)
        reject("no_positive_bead_peak", np.full((1, 1, 1), dc.flat[-1], dtype=np.longdouble))
        reject("invalid_otf_voxel_size", np.ones((1, 1, 1)), spacing=(dc.flat[-1], 1, 1))


if WIDER_PRECISION:

    def test_wider_precision_conversion_created_tie() -> None:
        dc = np.array([[[1, 1]]], dtype=np.longdouble)
        dc.flat[1] += np.longdouble(2) ** -60
        reject("ambiguous_bead_peak", dc)


def test_scaled_public_fft_inputs_axes_and_pretransform_snapshots(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parts = list(asymmetric())
    frozen = [a.copy() for a in parts]
    expected: list[Array] = []
    direct = direct_response(*frozen)
    origin = direct.origin
    gains: list[Fraction] = []
    norms: list[Fraction] = []
    for a in frozen:
        gain = max(max(abs(float(v.real)), abs(float(v.imag))) for v in a.flat) or 1.0
        gains.append(dyadic(gain))
        norms.append(
            sum((abs(dyadic(v.real)) + abs(dyadic(v.imag)) for v in a.flat), Fraction())
            / dyadic(gain)
        )
        scaled = np.empty(a.shape, dtype=np.complex128)
        for j in np.ndindex(a.shape):
            scaled[j] = complex(
                float(dyadic(a[j].real) / dyadic(gain)), float(dyadic(a[j].imag) / dyadic(gain))
            )
        expected.append(np.roll(scaled, tuple(-b for b in origin), axis=(0, 1, 2)))
    original = np.fft.fftn
    seen: set[int] = set()

    def observe(a: Any, s: Any = None, axes: Any = None, norm: Any = None, out: Any = None) -> Any:
        incoming = np.asarray(a)
        transform_axes = (
            tuple(range(incoming.ndim))
            if axes is None
            else tuple(int(ax) % incoming.ndim for ax in axes)
        )
        assert len(transform_axes) == 3 and len(set(transform_axes)) == 3
        assert norm in (None, "backward")
        if s is not None:
            assert all(
                int(n) in (-1, incoming.shape[ax]) for n, ax in zip(s, transform_axes, strict=True)
            )
        assert incoming.dtype in (np.dtype(np.float64), np.dtype(np.complex128))
        assert incoming.dtype.isnative
        extra = tuple(ax for ax in range(incoming.ndim) if ax not in transform_axes)
        reordered = np.transpose(incoming, (*extra, *transform_axes))
        rows = reordered.reshape((-1, *reordered.shape[-3:]))
        matched_rows: list[tuple[int, tuple[int, ...]]] = []
        for row in rows:
            matches = [
                (i, p)
                for i, target in enumerate(expected)
                for p in permutations(range(3))
                if row.shape == np.transpose(target, p).shape
                and np.array_equal(row, np.transpose(target, p))
            ]
            assert matches, (
                "FFT input must be independently rounded, commonly origin-rolled samples"
            )
            seen.update(i for i, _ in matches)
            matched_rows.append(matches[0])
        # Mutation of all caller components at the first public transform must
        # not influence any later transform, mass, origin or output.
        for component in parts:
            component[:] = 99
        transformed = original(a, s=s, axes=axes, norm=norm, out=out)
        transformed_rows = np.transpose(transformed, (*extra, *transform_axes)).reshape(rows.shape)
        with localcontext() as ctx:
            ctx.prec = PRECISION
            for row, (order, permutation) in zip(transformed_rows, matched_rows, strict=True):
                shifted = np.fft.fftshift(row)
                target = np.transpose(direct.values[order], permutation)
                budget = dec(128 * row.size * EPS * norms[order] + 4 * row.size * Q)
                ratio = dec(direct.mass / gains[order])
                for index in np.ndindex(row.shape):
                    er, ei = target[index]
                    dr = dec(dyadic(shifted[index].real)) - er * ratio
                    di = dec(dyadic(shifted[index].imag)) - ei * ratio
                    assert (dr * dr + di * di).sqrt() <= budget + budget * Decimal("1e-80")
        return transformed

    monkeypatch.setattr(np.fft, "fftn", observe)
    result = run(*parts)
    assert seen == {0, 1, 2}
    assert_direct(result.values, direct_response(*frozen))
    assert result.origin_zyx == origin


def test_single_correctly_rounded_rational_restoration(monkeypatch: pytest.MonkeyPatch) -> None:
    dc = np.array([[[2.0, 1.0]]])
    original = np.fft.fftn
    t_real = float(np.nextafter(0.5, 1.0))
    t_imag = TINY

    def perturb(a: Any, *args: Any, **kwargs: Any) -> Any:
        arguments = inspect.signature(original).bind(a, *args, **kwargs)
        arguments.apply_defaults()
        transformed = original(a, *args, **kwargs).astype(np.complex128)
        axes = arguments.arguments["axes"]
        sizes = arguments.arguments["s"]
        if axes is None:
            count = transformed.ndim if sizes is None else len(sizes)
            spatial_axes = tuple(range(transformed.ndim - count, transformed.ndim))
        else:
            spatial_axes = tuple(int(axis) % transformed.ndim for axis in axes)
        assert len(spatial_axes) == 3 and len(set(spatial_axes)) == 3
        assert sorted(transformed.shape[axis] for axis in spatial_axes) == [1, 1, 2]
        # A valid within-budget perturbation of the sole nonzero frequency;
        # select the length-2 transformed axis, never an untransformed batch.
        axis = next(axis for axis in spatial_axes if transformed.shape[axis] == 2)
        index: list[Any] = [slice(None)] * transformed.ndim
        index[axis] = 1
        transformed[tuple(index)] = complex(t_real, t_imag)
        return transformed

    monkeypatch.setattr(np.fft, "fftn", perturb)
    result = run(dc, dc, dc)
    rational_real = float(dyadic(t_real) * Fraction(2, 3))
    rational_imag = float(dyadic(t_imag) * Fraction(2, 3))
    for order in range(3):
        assert result.values[order, 0, 0, 0].real == rational_real
        assert result.values[order, 0, 0, 0].imag == rational_imag


@pytest.mark.parametrize(
    "failure", [FloatingPointError("fft arithmetic"), OverflowError("fft overflow")]
)
def test_transform_arithmetic_exceptions_translate(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise failure

    monkeypatch.setattr(np.fft, "fftn", fail)
    reject("empirical_response_transform_failure", *asymmetric())


@pytest.mark.parametrize("nonfinite", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("component", ["real", "imag"])
@pytest.mark.parametrize("position", [0, -1])
def test_all_scaled_transform_components_validate_before_dc_identity(
    monkeypatch: pytest.MonkeyPatch, nonfinite: float, component: str, position: int
) -> None:
    original = np.fft.fftn

    def fail(a: Any, *args: Any, **kwargs: Any) -> Any:
        transformed = original(a, *args, **kwargs).astype(np.complex128)
        getattr(transformed, component).flat[position] = nonfinite
        return transformed

    monkeypatch.setattr(np.fft, "fftn", fail)
    reject("empirical_response_transform_failure", *asymmetric())


def test_arithmetic_runtimewarning_translates(monkeypatch: pytest.MonkeyPatch) -> None:
    original = np.fft.fftn

    def warn(a: Any, *args: Any, **kwargs: Any) -> Any:
        warnings.warn("overflow encountered in transform", RuntimeWarning, stacklevel=2)
        return original(a, *args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn)
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        reject("empirical_response_transform_failure", *asymmetric())
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


@pytest.mark.parametrize(
    "failure",
    [
        MemoryError("allocation"),
        RuntimeError("unrelated"),
        TypeError("dependency type"),
        ValueError("dependency value"),
    ],
)
def test_unrelated_and_allocation_transform_exceptions_propagate_identically(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    def fail(*args: Any, **kwargs: Any) -> Any:
        raise failure

    monkeypatch.setattr(np.fft, "fftn", fail)
    before = asymmetric()
    snapshots = [a.tobytes() for a in before]
    with pytest.raises(type(failure)) as error:
        run(*before)
    assert error.value is failure
    assert snapshots == [a.tobytes() for a in before]


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log"])
def test_numpy_error_modes_and_handled_errors_do_not_leak(
    mode: Literal["raise", "warn", "ignore", "call", "print", "log"],
) -> None:
    events: list[Any] = []

    class Log:
        def write(self, text: str) -> None:
            events.append(text)

    old = np.geterr()
    old_callback = np.geterrcall()
    try:
        np.seterrcall(Log() if mode == "log" else lambda *args: events.append(args))
        np.seterr(all=mode)
        selected = np.geterr()
        callback = np.geterrcall()
        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter("always")
            dc = np.array([[[MAX, MAX / 2]]])
            side = np.zeros_like(dc, dtype=np.complex128)
            side.real[:] = MAX
            side.imag[:] = MAX
            run(dc, side, side)
            run(np.array([[[2 * TINY, -TINY]]]))
            reject(
                "unrepresentable_empirical_response", np.full((1, 1, 1), TINY), np.ones((1, 1, 1))
            )
            reject("invalid_otf_voxel_size", np.ones((1, 1, 1)), spacing=(10**1000, 1, 1))
            reject(
                "unrepresentable_otf_frequencies", np.array([[[1.0, 0.0]]]), spacing=(1, 1, TINY)
            )
        assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
        assert not events
        assert np.geterr() == selected
        assert np.geterrcall() is callback
    finally:
        np.seterr(**old)
        np.seterrcall(old_callback)


def test_unrelated_warning_is_not_suppressed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = np.fft.fftn

    def warn(a: Any, *args: Any, **kwargs: Any) -> Any:
        warnings.warn("unrelated public dependency notice", UserWarning, stacklevel=2)
        return original(a, *args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn)
    with pytest.warns(UserWarning, match="unrelated public dependency notice"):
        checked(*asymmetric())


def synthetic(bead: tuple[int, int, int]) -> tuple[Array, Array, Array, Array, Array]:
    """Admissible asymmetric point detection; a0=a+=a-=1, periodic modes."""
    shape = (2, 3, 4)
    h = np.arange(1, 25, dtype=np.float64).reshape(shape)
    # Integer weights sum to 512, so stored h has exact real mass one.
    h[0, 0, 0] = 213
    h /= 512
    brightness = 64.0
    z = np.arange(2).reshape(2, 1, 1)
    # axial integer mode 1: cos(pi*uz) is exactly +/-1 at this grid.
    g1 = (2 / 3) * np.where(z == 0, 1, -1)
    g2 = 1 / 3
    # qy=0, qx=1/(4*dx); bead illumination phase is pi*bx/2.
    gauge = (1 + 0j, 1j, -1 + 0j, -1j)[bead[2]]
    dc = brightness * np.roll(h, bead, axis=(0, 1, 2))
    c1 = brightness * np.roll(h * g1, bead, axis=(0, 1, 2)) * gauge
    c2 = brightness * np.roll(h * g2, bead, axis=(0, 1, 2)) * gauge**2
    phases = 2 * np.pi * np.arange(7) / 7
    c, s = np.cos(phases), np.sin(phases)
    images = np.stack(
        [
            dc
            + 2 * c1.real * cp
            - 2 * c1.imag * sp
            + 2 * c2.real * (cp * cp - sp * sp)
            - 2 * c2.imag * ((2 * cp) * sp)
            for cp, sp in zip(c, s, strict=True)
        ]
    )
    return dc, c1, c2, images, phases


def test_real_declaration_correction_known_phase_response_and_physical_movement() -> None:
    spectra: list[Array] = []
    response_budgets: list[list[Decimal]] = []
    for bead in ((1, 2, 1), (0, 0, 2)):
        truth_dc, truth_c1, truth_c2, exposures, phases = synthetic(bead)
        raw = 10 + 2 * exposures
        commands = phases + np.array([0, 0.2, -0.1, 0.3, -0.2, 0.1, -0.15])
        acquisition = simrecon.declare_acquisition(
            raw[None],
            config={
                "version": 1,
                "acquisition_kind": "sim_beads",
                "axes": ["orientation", "phase", "z", "y", "x"],
                "intensity_unit": "count",
                "sampling_um": {"z": SPACING[0], "y": SPACING[1], "x": SPACING[2]},
                "nominal_phases_rad": [commands.tolist()],
            },
        )
        corrected = simrecon.correct_linear_response(
            acquisition, offset=10, response=2, output_unit="electron"
        )
        # Independent specified binary64 correction, not correction output as oracle.
        corrected_expected = (raw - 10) / 2
        np.testing.assert_array_equal(corrected.data[0], corrected_expected)
        observed = simrecon.separate_volume_phases(corrected.data[0], phases_rad=phases)
        expectation_fit = represented_fit(corrected_expected, phases)
        c, s = np.cos(phases), np.sin(phases)
        h = np.column_stack((np.ones(len(phases)), c, s, c * c - s * s, (2 * c) * s))
        assert np.linalg.cond(h) < 10
        with localcontext() as ctx:
            ctx.prec = PRECISION
            separator_budget = dec(
                8192 * len(phases) * EPS * dyadic(np.max(abs(corrected_expected))) + 8 * Q
            )
            truth_coords = (truth_dc, truth_c1.real, truth_c1.imag, truth_c2.real, truth_c2.imag)
            observed_coords = (
                observed.dc,
                observed.c1.real,
                observed.c1.imag,
                observed.c2.real,
                observed.c2.imag,
            )
            deviations: list[Decimal] = []
            for i, (true, actual) in enumerate(zip(truth_coords, observed_coords, strict=True)):
                largest = Decimal(0)
                for j in np.ndindex(true.shape):
                    fit = expectation_fit[(i, *j)]
                    assert abs(dec(dyadic(actual[j])) - fit) <= separator_budget
                    largest = max(largest, abs(fit - dec(dyadic(true[j]))) + separator_budget)
                deviations.append(largest)
            peak = float(truth_dc[bead])
            second = sorted(truth_dc.flat)[-2]
            assert dec(dyadic(peak) - dyadic(second)) > 2 * deviations[0]
            result = run(observed.dc, observed.c1, observed.c2)
            assert result.origin_zyx == bead
            truth_response = direct_response(truth_dc, truth_c1, truth_c2)
            mass = dec(truth_response.mass)
            size = truth_dc.size
            mass_error = size * deviations[0]
            assert mass_error < mass
            norm_errors = (
                deviations[0],
                deviations[1] + deviations[2],
                deviations[3] + deviations[4],
            )
            primitive_budgets: list[Decimal] = []
            for order, array in enumerate((truth_dc, truth_c1, truth_c2)):
                norm = sum(
                    (abs(dyadic(v.real)) + abs(dyadic(v.imag)) for v in array.flat), Fraction()
                )
                upper_lambda = (dec(norm) + size * norm_errors[order]) / (mass - mass_error)
                primitive_budgets.append(dec(512 * size * EPS) * upper_lambda + dec(16 * size * Q))
            bounds = [Decimal(0)] * 3
            for index in np.ndindex(result.values.shape):
                order = index[0]
                er, ei = truth_response.values[index]
                side_error = (
                    deviations[0]
                    if order == 0
                    else (deviations[2 * order - 1] ** 2 + deviations[2 * order] ** 2).sqrt()
                )
                norm = (er * er + ei * ei).sqrt()
                propagated = (size * side_error + norm * mass_error) / (mass - mass_error)
                bounds[order] = max(bounds[order], propagated + primitive_budgets[order])
                actual = result.values[index]
                error = (
                    (dec(dyadic(actual.real)) - er) ** 2 + (dec(dyadic(actual.imag)) - ei) ** 2
                ).sqrt()
                assert error <= propagated + primitive_budgets[order]
            response_budgets.append(bounds)
        assert acquisition.nominal_phases_rad is not None
        np.testing.assert_array_equal(acquisition.nominal_phases_rad[0], commands)
        wrong = simrecon.separate_volume_phases(corrected.data[0], phases_rad=commands)
        assert np.max(abs(wrong.c1 - observed.c1)) > float(separator_budget) * 100
        spectra.append(result.values)
    # Physical movement changes gauge from i to -1: first order multiplies i,
    # second order multiplies -1. Joint translation alone preserves response.
    for order, gain in enumerate((1 + 0j, 1j, -1 + 0j)):
        agreement(
            spectra[1][order],
            spectra[0][order],
            response_budgets[0][order] + response_budgets[1][order],
            gain,
        )
    assert not np.allclose(spectra[1][1], spectra[0][1])
