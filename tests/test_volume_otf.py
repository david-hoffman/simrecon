"""Blind public-contract tests for VOLUME-OTF-01; no product FFT oracle."""

from __future__ import annotations

import importlib
import io
import itertools
import math
import os
import subprocess
import sys
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from typing import Any, Literal, cast

import numpy as np
import pytest

# More than 100 correct decimal digits; all reference arithmetic uses 100 digits.
PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406"
    "286208998628034825342117067982148086513282306647"
)
EPS = Decimal.from_float(2**-52)
Q = Decimal.from_float(float.fromhex("0x0.0000000000001p-1022"))
MAX = float.fromhex("0x1.fffffffffffffp+1023")
ARRAY_FIELDS = ("values", "fz_per_um", "fy_per_um", "fx_per_um")
FIELDS = (*ARRAY_FIELDS, "voxel_size_um", "origin_zyx", "source")


def modes(length: int) -> range:
    return range(-(length // 2), (length + 1) // 2)


@cache
def root(turns: Fraction) -> tuple[Decimal, Decimal]:
    """Negative exponential using reduced rational angle and Decimal Taylor sums."""
    turns %= 1
    if turns > Fraction(1, 2):
        turns -= 1
    with localcontext() as ctx:
        ctx.prec = 100
        angle = -2 * PI * Decimal(turns.numerator) / Decimal(turns.denominator)
        real = term_r = Decimal(1)
        imag = term_i = angle
        for n in range(1, 180):
            term_r *= -(angle * angle) / Decimal((2 * n - 1) * (2 * n))
            term_i *= -(angle * angle) / Decimal((2 * n) * (2 * n + 1))
            real += term_r
            imag += term_i
            if max(abs(term_r), abs(term_i)) < Decimal("1e-98"):
                break
        else:
            raise AssertionError("reference Taylor series did not converge")
        return +real, +imag


def reference(psf: Any, origin: tuple[int, ...]) -> Any:
    """Exact float64 sample values, independent high-precision normalized sum."""
    with localcontext() as ctx:
        ctx.prec = 100
        weighted = [
            (index, Decimal.from_float(float(psf[index])))
            for index in np.ndindex(psf.shape)
            if psf[index] != 0
        ]
        total = sum((weight for _, weight in weighted), Decimal(0))
        expected = {}
        for index, k in zip(
            np.ndindex(psf.shape),
            itertools.product(*(modes(n) for n in psf.shape)),
            strict=True,
        ):
            real = imag = Decimal(0)
            for position, weight in weighted:
                turns = sum(
                    (
                        Fraction(ki * (p - o), n)
                        for ki, p, o, n in zip(k, position, origin, psf.shape, strict=True)
                    ),
                    Fraction(0),
                )
                cosine, sine = root(turns)
                real += weight / total * cosine
                imag += weight / total * sine
            expected[index] = (real, imag)
        return expected


def assert_transfer(values: Any, expected: Any, size: int) -> None:
    with localcontext() as ctx:
        ctx.prec = 100
        budget = 128 * size * EPS + 4 * size * Q
        assert np.isfinite(values).all()
        for index, (real, imag) in expected.items():
            actual = values[index]
            dr = Decimal.from_float(float(actual.real)) - real
            di = Decimal.from_float(float(actual.imag)) - imag
            assert (dr * dr + di * di).sqrt() <= budget, f"DFT mismatch at {index}"


def assert_frequencies(result: Any, shape: Any, spacings: Any) -> None:
    with localcontext() as ctx:
        ctx.prec = 100
        for name, n, spacing in zip(ARRAY_FIELDS[1:], shape, spacings, strict=True):
            observed = getattr(result, name)
            assert observed.shape == (n,)
            assert np.isfinite(observed).all()
            assert all(
                float(a) < float(b) for a, b in zip(observed[:-1], observed[1:], strict=True)
            )
            d = Decimal.from_float(float(spacing))
            for actual, k in zip(observed, modes(n), strict=True):
                if k == 0:
                    assert actual == 0
                else:
                    exact = Decimal(k) / (n * d)
                    error = abs(Decimal.from_float(float(actual)) - exact)
                    assert actual != 0
                    assert error <= 8 * EPS * abs(exact) + Q


def asymmetric() -> Any:
    psf = np.zeros((3, 4, 2), dtype=np.float64)
    for position, mass in [
        ((0, 0, 0), 3),
        ((1, 0, 0), 1),
        ((0, 1, 0), 4),
        ((0, 0, 1), 2),
        ((2, 3, 1), 5),
    ]:
        psf[position] = mass
    return psf


def check_independent_oracles() -> None:
    """Separate analytical checks; executable without importing simrecon."""
    with localcontext() as ctx:
        ctx.prec = 100
        assert abs(root(Fraction(1, 4))[0]) < Decimal("1e-95")
        assert abs(root(Fraction(1, 4))[1] + 1) < Decimal("1e-95")
        assert abs(root(Fraction(1, 3))[0] + Decimal("0.5")) < Decimal("1e-95")
        assert abs(root(Fraction(1, 3))[1] + Decimal(3).sqrt() / 2) < Decimal("1e-95")
        expected = reference(asymmetric(), (0, 0, 0))
        # k=(1,1,-1): [3+e^(-2pi*i/3)-4i-2+5e^(pi*i/6)]/15.
        real, imag = expected[(2, 3, 0)]
        assert abs(real - (Decimal("0.5") + 5 * Decimal(3).sqrt() / 2) / 15) < Decimal("1e-94")
        assert abs(imag - (-Decimal(3).sqrt() / 2 - Decimal("1.5")) / 15) < Decimal("1e-94")
        for shape in [(1, 1, 1), (2, 3, 4)]:
            delta = np.zeros(shape)
            delta[(0, 0, 0)] = 1
            assert_transfer(np.ones(shape, dtype=complex), reference(delta, (0, 0, 0)), delta.size)
            constant = np.ones(shape)
            ideal = np.zeros(shape, dtype=complex)
            ideal[tuple(n // 2 for n in shape)] = 1
            assert_transfer(ideal, reference(constant, (0, 0, 0)), constant.size)
        # Exact stored values independently cross-check integer conversion at ties.
        assert float(2**53 + 1) == float(2**53)
        assert float(2**53 + 3) == float(2**53 + 4)
        assert float(2**64 - 1) == float(2**64)
        # All-subnormal ratio and all-max cancellation do not use a float sum.
        for source in [np.array([Q, 3 * Q], dtype=float).reshape(1, 1, 2), np.full((1, 1, 2), MAX)]:
            values = reference(source, (0, 0, 0))
            target = Decimal("-0.5") if source[0, 0, 0] != MAX else Decimal(0)
            assert abs(values[(0, 0, 0)][0] - target) < Decimal("1e-95")
        print(
            "independent Decimal roots, asymmetric analytical bin, delta, constant, "
            "stored ties, range: PASS"
        )


@pytest.fixture(scope="module")
def api() -> Any:
    # Public import at setup keeps collection useful before the feature exists.
    simrecon = importlib.import_module("simrecon")

    return simrecon.prepare_volume_otf, simrecon.Otf3D, simrecon.SimreconError


def prepare(api: Any, psf: Any, **changes: Any) -> Any:
    kwargs = {
        "voxel_size_um": (0.7, 1.25, 2.5),
        "origin_zyx": (0, 0, 0),
        "source": " A calibration \n",
    }
    kwargs.update(changes)
    return api[0](psf, **kwargs)


def assert_error(api: Any, code: str | tuple[str, ...], psf: Any, **kwargs: Any) -> None:
    before = psf.copy() if isinstance(psf, np.ndarray) else None
    raw_before = psf.tobytes() if isinstance(psf, np.ndarray) else None
    with pytest.raises(api[2]) as caught:
        prepare(api, psf, **kwargs)
    error = caught.value
    assert isinstance(error, ValueError)
    public_error = cast(Any, error)
    allowed = (code,) if isinstance(code, str) else code
    assert public_error.code in allowed
    assert isinstance(public_error.code, str)
    assert isinstance(public_error.message, str)
    if before is not None:
        np.testing.assert_array_equal(psf, before)
        assert psf.dtype == before.dtype
        assert psf.tobytes() == raw_before


def test_oracle_analytical_selfcheck() -> None:
    check_independent_oracles()


@pytest.mark.parametrize("origin", [(0, 0, 0), (2, 1, 1), (1, 3, 0)])
def test_full_signed_asymmetric_dft_and_physical_grid(api: Any, origin: Any) -> None:
    psf = asymmetric()
    result = prepare(api, psf, origin_zyx=origin)
    assert result.values.shape == psf.shape
    assert_transfer(result.values, reference(psf, origin), psf.size)
    assert_frequencies(result, psf.shape, (0.7, 1.25, 2.5))
    assert np.min(result.values.real) < -0.1
    assert np.max(np.abs(result.values.imag)) > 0.1
    assert abs(result.values[1, 2, 1] - 1) <= float(128 * psf.size * EPS)
    # Modular negative modes, including self-conjugate even Nyquist endpoints.
    for index in np.ndindex(psf.shape):
        k = tuple(index[a] - psf.shape[a] // 2 for a in range(3))
        opposite = tuple(((-k[a]) + psf.shape[a] // 2) % psf.shape[a] for a in range(3))
        assert abs(result.values[index] - result.values[opposite].conjugate()) <= float(
            256 * psf.size * EPS
        )


@pytest.mark.parametrize("shift", [(1, 2, 1), (-1, -3, 0)])
def test_joint_periodic_translation_and_exact_gain(api: Any, shift: Any) -> None:
    psf = asymmetric()
    origin = (2, 1, 1)
    baseline = prepare(api, psf, origin_zyx=origin)
    translated = np.roll(psf, shift, axis=(0, 1, 2))
    moved_origin = tuple((o + s) % n for o, s, n in zip(origin, shift, psf.shape, strict=True))
    for samples, declared in [(translated, moved_origin), (psf * 8, origin)]:
        observed = prepare(api, samples, origin_zyx=declared)
        expected = reference(psf, origin)
        assert_transfer(observed.values, expected, psf.size)
        assert_transfer(baseline.values, expected, psf.size)


@pytest.mark.parametrize("shape", [(1, 1, 1), (1, 3, 4), (3, 1, 2), (2, 4, 1), (2, 3, 5)])
@pytest.mark.parametrize("kind", ["delta-at-origin", "delta-away", "constant"])
def test_delta_constant_singletons_full_grid(api: Any, shape: Any, kind: str) -> None:
    origin = tuple(n - 1 for n in shape)
    psf = np.ones(shape) if kind == "constant" else np.zeros(shape)
    if kind != "constant":
        psf[origin if kind == "delta-at-origin" else (0, 0, 0)] = 7
    result = prepare(api, psf, origin_zyx=origin)
    assert_transfer(result.values, reference(psf, origin), psf.size)
    assert_frequencies(result, shape, (0.7, 1.25, 2.5))
    assert result.values.shape == shape


REAL_DTYPES = sorted(
    {np.dtype(code).str for code in np.typecodes["AllInteger"] + np.typecodes["Float"]}
)


@pytest.mark.parametrize("dtype", REAL_DTYPES)
@pytest.mark.parametrize("order", ["<", ">"])
def test_all_available_real_widths_and_endian(
    api: Any, dtype: str, order: Literal["<", ">"]
) -> None:
    psf = np.array([0, 1, 2, 3, 7, 11, 13, 17], dtype=np.dtype(dtype).newbyteorder(order)).reshape(
        2, 2, 2
    )
    result = prepare(api, psf, origin_zyx=(1, 0, 1))
    assert_transfer(result.values, reference(psf, (1, 0, 1)), psf.size)


@pytest.mark.parametrize(
    "dtype, numbers",
    [
        (np.int64, [2**53 + 1, 2**53 + 3, 2**63 - 1, 1]),
        (np.uint64, [2**53 + 1, 2**53 + 3, 2**64 - 1, 1]),
        (np.longdouble, ["1.000000000000000111", "0.000000000000000001", "2", "3"]),
    ],
)
def test_converted_sample_problem(api: Any, dtype: Any, numbers: Any) -> None:
    psf = np.array(numbers, dtype=dtype).reshape(1, 2, 2)
    result = prepare(api, psf, origin_zyx=(0, 1, 0))
    assert_transfer(result.values, reference(psf, (0, 1, 0)), psf.size)


@pytest.mark.parametrize("layout", ["strided", "reversed", "readonly", "fortran"])
def test_ownership_mutability_snapshots_and_frozen_bindings(api: Any, layout: str) -> None:
    owner = np.arange(1, 193, dtype=float).reshape(6, 8, 4)
    psf = owner[::2, ::2, ::2]
    if layout == "reversed":
        psf = psf[::-1, ::-1, ::-1]
    elif layout == "readonly":
        psf.flags.writeable = False
    elif layout == "fortran":
        psf = np.asfortranarray(psf)
    spacing = np.array([0.7, 1.25, 2.5])
    origin = np.array([2, 1, 1], dtype=np.int32)
    before = psf.copy()
    owner_before = owner.copy()
    first = prepare(api, psf, voxel_size_um=spacing, origin_zyx=origin)
    second = prepare(api, psf, voxel_size_um=spacing, origin_zyx=origin)
    assert isinstance(first, api[1])
    assert {
        name
        for name in dir(first)
        if not name.startswith("_") and not callable(getattr(first, name))
    } == set(FIELDS)
    assert first.source == " A calibration \n"
    assert first.voxel_size_um == (0.7, 1.25, 2.5)
    assert all(type(v) is float for v in first.voxel_size_um)
    assert first.origin_zyx == (2, 1, 1)
    assert all(type(v) is int for v in first.origin_zyx)
    outputs = [getattr(first, name) for name in ARRAY_FIELDS]
    other_outputs = [getattr(second, name) for name in ARRAY_FIELDS]
    for i, array in enumerate(outputs):
        assert isinstance(array, np.ndarray)
        assert array.dtype == np.dtype(np.complex128 if i == 0 else np.float64)
        assert array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        for inp in (psf, owner, spacing, origin):
            assert not np.shares_memory(array, inp)
        for other in outputs[i + 1 :] + other_outputs:
            assert not np.shares_memory(array, other)
    assert_transfer(first.values, reference(psf, (2, 1, 1)), psf.size)
    np.testing.assert_array_equal(psf, before)
    np.testing.assert_array_equal(owner, owner_before)
    np.testing.assert_array_equal(spacing, [0.7, 1.25, 2.5])
    np.testing.assert_array_equal(origin, [2, 1, 1])
    frozen_snapshot = [array.copy() for array in other_outputs]
    for name in FIELDS:
        original = getattr(first, name)
        if name in ARRAY_FIELDS:
            replacement = np.array(original, copy=True)
        elif name == "voxel_size_um":
            replacement = tuple(2 * value for value in original)
        elif name == "origin_zyx":
            replacement = (0, 0, 0)
        else:
            replacement = original + " alternate binding"
        assert replacement is not original
        try:
            setattr(first, name, replacement)
        except BaseException:
            assert getattr(first, name) is original
        assert getattr(first, name) is original
    for i, array in enumerate(outputs):
        unaffected = [a.copy() for a in outputs]
        array.flat[0] = 99 + (1j if i == 0 else 0)
        for j, other in enumerate(outputs):
            if i != j:
                np.testing.assert_array_equal(other, unaffected[j])
    for other, snapshot in zip(other_outputs, frozen_snapshot, strict=True):
        np.testing.assert_array_equal(other, snapshot)
    np.testing.assert_array_equal(psf, before)
    spacing[:] = 9
    origin[:] = 0
    owner[:] = 0
    assert second.voxel_size_um == (0.7, 1.25, 2.5)
    assert second.origin_zyx == (2, 1, 1)
    for other, snapshot in zip(other_outputs, frozen_snapshot, strict=True):
        np.testing.assert_array_equal(other, snapshot)


def test_direct_record_construction_does_not_validate(api: Any) -> None:
    markers = {name: object() for name in FIELDS}
    record = api[1](**markers)
    for name, value in markers.items():
        assert getattr(record, name) is value


class ArraySubclass(np.ndarray):
    """Disallowed ndarray subclass used only as a public input."""


@pytest.mark.parametrize("psf", [None, 1, [[[1]]], (1,), np.ones((1, 1, 1)).view(ArraySubclass)])
def test_reject_nonplain_array(api: Any, psf: Any) -> None:
    assert_error(api, "invalid_psf", psf)


@pytest.mark.parametrize(
    "dtype",
    [bool, complex, object, "U2", "S2", "datetime64[D]", "timedelta64[D]", "V8", [("value", "f8")]],
)
def test_reject_nonreal_dtype(api: Any, dtype: Any) -> None:
    psf = np.zeros((1, 1, 1), dtype=dtype)
    assert_error(api, "invalid_psf_dtype", psf)


@pytest.mark.parametrize("shape", [(), (2,), (2, 2), (1, 2, 2, 2), (0, 2, 2), (2, 0, 2), (2, 2, 0)])
def test_reject_rank_and_empty_axes(api: Any, shape: Any) -> None:
    # An empty axis also has no legal origin; simultaneous-error precedence is unspecified.
    code = ("invalid_psf_shape", "invalid_otf_origin") if 0 in shape else "invalid_psf_shape"
    assert_error(api, code, np.ones(shape))


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.longdouble])
def test_reject_nonfinite_source(api: Any, value: Any, dtype: Any) -> None:
    # -infinity violates both source finiteness and nonnegativity; no precedence is specified.
    code = ("nonfinite_psf", "negative_psf") if value == -np.inf else "nonfinite_psf"
    assert_error(api, code, np.array([1, value], dtype=dtype).reshape(1, 1, 2))


@pytest.mark.parametrize("value", [-1, -float(Q), -1e-20])
def test_reject_negative_source(api: Any, value: Any) -> None:
    assert_error(api, "negative_psf", np.array([1, value]).reshape(1, 1, 2))


@pytest.mark.parametrize("dtype", [np.int8, np.int64, np.float16, np.float64])
def test_negative_signed_kinds(api: Any, dtype: Any) -> None:
    assert_error(api, "negative_psf", np.array([-1, 1], dtype=dtype).reshape(1, 1, 2))


def test_signed_zero_is_nonnegative(api: Any) -> None:
    psf = np.array([-0.0, 0.0, 1.0]).reshape(1, 1, 3)
    before = psf.tobytes()
    assert_transfer(prepare(api, psf).values, reference(psf, (0, 0, 0)), psf.size)
    assert psf.tobytes() == before


@pytest.mark.parametrize("dtype", [np.int64, np.uint64, np.float64])
def test_zero_converted_mass(api: Any, dtype: Any) -> None:
    assert_error(api, "zero_psf_mass", np.zeros((2, 1, 3), dtype=dtype))


WIDER_RANGE = np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp
WIDER_UNDERFLOW = np.finfo(np.longdouble).minexp < np.finfo(np.float64).minexp


if WIDER_RANGE or WIDER_UNDERFLOW:

    @pytest.mark.parametrize(
        "case",
        (["overflow"] if WIDER_RANGE else [])
        + (["negative-underflow", "zero-underflow", "mixed-underflow"] if WIDER_UNDERFLOW else []),
    )
    def test_wider_float_conversion_boundaries(api: Any, case: str) -> None:
        tiny = np.longdouble("1e-4000")
        if case == "overflow":
            psf = np.array([1, np.finfo(np.longdouble).max], dtype=np.longdouble).reshape(1, 1, 2)
            assert_error(api, "nonfinite_psf", psf)
        elif case == "negative-underflow":
            assert_error(
                api, "negative_psf", np.array([1, -tiny], dtype=np.longdouble).reshape(1, 1, 2)
            )
        elif case == "zero-underflow":
            assert_error(api, "zero_psf_mass", np.full((1, 1, 2), tiny, dtype=np.longdouble))
        else:
            psf = np.array([tiny, 1], dtype=np.longdouble).reshape(1, 1, 2)
            assert_transfer(prepare(api, psf).values, reference(psf, (0, 0, 0)), psf.size)


BAD_TRIPLES = [
    None,
    1,
    "123",
    {0: 1, 1: 1, 2: 1},
    {1, 2, 3},
    (1, 1),
    (1, 1, 1, 1),
    np.ones((1, 3)),
    np.ones((3, 1)),
    np.ones(3).view(ArraySubclass),
]


@pytest.mark.parametrize("triple", BAD_TRIPLES)
@pytest.mark.parametrize(
    "field,code",
    [("voxel_size_um", "invalid_otf_voxel_size"), ("origin_zyx", "invalid_otf_origin")],
)
def test_reject_malformed_triples(api: Any, triple: Any, field: str, code: str) -> None:
    assert_error(api, code, np.ones((2, 2, 2)), **{field: triple})


@pytest.mark.parametrize(
    "bad", [True, np.bool_(False), 1j, "1", None, Decimal(1), Fraction(1), np.array(1.0)]
)
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_reject_nonreal_spacing_scalars(api: Any, bad: Any, axis: int) -> None:
    spacing = [1, 1, 1]
    spacing[axis] = bad
    assert_error(api, "invalid_otf_voxel_size", np.ones((2, 2, 2)), voxel_size_um=spacing)


@pytest.mark.parametrize("bad", [0, -1, -0.0, np.nan, np.inf, -np.inf, 10**400])
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_reject_nonpositive_nonfinite_spacing(api: Any, bad: Any, axis: int) -> None:
    spacing = [1, 1, 1]
    spacing[axis] = bad
    assert_error(api, "invalid_otf_voxel_size", np.ones((2, 2, 2)), voxel_size_um=spacing)


if WIDER_RANGE or WIDER_UNDERFLOW:

    @pytest.mark.parametrize(
        "case", (["overflow"] if WIDER_RANGE else []) + (["underflow"] if WIDER_UNDERFLOW else [])
    )
    def test_reject_wider_spacing_conversion(api: Any, case: str) -> None:
        bad = np.finfo(np.longdouble).max if case == "overflow" else np.longdouble("1e-4000")
        assert_error(api, "invalid_otf_voxel_size", np.ones((1, 1, 1)), voxel_size_um=(bad, 1, 1))


@pytest.mark.parametrize("container", [tuple, list, np.array])
@pytest.mark.parametrize(
    "spacing",
    [
        (np.int16(1), np.uint64(2), np.float32(3)),
        (np.float16(0.5), np.float64(1.25), np.longdouble(2)),
    ],
)
def test_permitted_triples_and_scalars(api: Any, container: Any, spacing: Any) -> None:
    # Object ndarray preserves heterogeneous permitted scalar kinds.
    supplied_spacing = (
        np.array(spacing, dtype=object) if container is np.array else container(spacing)
    )
    origin = container((np.int64(1), np.uint32(2), np.int16(3)))
    psf = np.ones((2, 3, 4))
    result = prepare(api, psf, voxel_size_um=supplied_spacing, origin_zyx=origin)
    assert result.voxel_size_um == tuple(float(v) for v in spacing)
    assert result.origin_zyx == (1, 2, 3)
    assert_frequencies(result, psf.shape, spacing)


@pytest.mark.parametrize(
    "bad", [True, np.bool_(False), 1.0, np.float32(1), 1j, "1", None, np.array(1), Fraction(1)]
)
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_reject_noninteger_origin(api: Any, bad: Any, axis: int) -> None:
    origin = [0, 0, 0]
    origin[axis] = bad
    assert_error(api, "invalid_otf_origin", np.ones((2, 3, 4)), origin_zyx=origin)


@pytest.mark.parametrize("axis,n", [(0, 2), (1, 3), (2, 4)])
@pytest.mark.parametrize("side", ["negative", "end", "huge"])
def test_reject_out_of_bounds_origin(api: Any, axis: int, n: int, side: str) -> None:
    origin = [0, 0, 0]
    origin[axis] = {"negative": -1, "end": n, "huge": 10**100}[side]
    assert_error(api, "invalid_otf_origin", np.ones((2, 3, 4)), origin_zyx=origin)


@pytest.mark.parametrize("origin", list(itertools.product(range(2), range(3), range(2))))
def test_all_legal_origin_indices(api: Any, origin: Any) -> None:
    psf = np.arange(1, 13).reshape(2, 3, 2)
    assert_transfer(prepare(api, psf, origin_zyx=origin).values, reference(psf, origin), psf.size)


@pytest.mark.parametrize("source", [None, 1, b"source", "", " \n\t", "\u2003\u00a0"])
def test_reject_source_label(api: Any, source: Any) -> None:
    assert_error(api, "invalid_otf_source", np.ones((1, 1, 1)), source=source)


@pytest.mark.parametrize("source", [" source \n", "\u2003identity\u00a0", "x", "\x00"])
def test_source_text_is_opaque_and_unchanged(api: Any, source: str) -> None:
    assert prepare(api, np.ones((1, 1, 1)), source=source).source == source


RANGE_CASES = [
    np.full((2, 3, 2), MAX),
    np.full((2, 3, 2), float(Q)),
    np.array([float(Q), 3 * float(Q)]).reshape(1, 1, 2),
    np.array([MAX, float(Q), MAX, 0]).reshape(1, 2, 2),
    np.array([1, float(Q), 0, 0]).reshape(1, 2, 2),
    np.array([1, 1 + 2**-52, 1, 1 - 2**-52, 2**-48, 0, 0, 0]).reshape(2, 2, 2),
]


@pytest.mark.parametrize("psf", RANGE_CASES)
def test_extreme_mass_and_cancellation_budget(api: Any, psf: Any) -> None:
    result = prepare(api, psf)
    assert_transfer(result.values, reference(psf, (0, 0, 0)), psf.size)


@pytest.mark.parametrize(
    "shape,spacing",
    [
        ((2, 3, 4), (MAX, MAX, MAX)),
        ((1, 1, 1), (float(Q), MAX, float(Q))),
        ((1, 3, 2), (float(Q), MAX, 0.5)),
        ((3, 1, 2), (0.5, float(Q), MAX)),
        ((2, 3, 1), (MAX, 0.5, float(Q))),
        ((2, 3, 4), (float.fromhex("0x1p-1022"), 1, 2)),
        ((2, 3, 4), (float.fromhex("0x1p-1024"), 1, 1)),
        ((2, 3, 4), (1, float.fromhex("0x1p-1024"), 1)),
        ((2, 3, 4), (1, 1, float.fromhex("0x1p-1024"))),
    ],
)
def test_representable_extreme_frequency_formula(api: Any, shape: Any, spacing: Any) -> None:
    result = prepare(api, np.ones(shape), voxel_size_um=spacing)
    assert_frequencies(result, shape, spacing)
    assert_transfer(result.values, reference(np.ones(shape), (0, 0, 0)), math.prod(shape))


@pytest.mark.parametrize("axis", [0, 1, 2])
@pytest.mark.parametrize("spacing", [float(Q)])
def test_reject_unrepresentable_final_frequencies(api: Any, axis: int, spacing: float) -> None:
    sizes: list[Any] = [1, 1, 1]
    sizes[axis] = spacing
    assert_error(api, "unrepresentable_otf_frequencies", np.ones((2, 3, 4)), voxel_size_um=sizes)


@pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
def test_preserve_floating_policy_and_no_arithmetic_warnings(
    api: Any, mode: Literal["ignore", "warn", "raise", "call", "print", "log"], capfd: Any
) -> None:
    class ErrorLog:
        def __init__(self) -> None:
            self.messages: list[str] = []

        def write(self, message: str) -> None:
            self.messages.append(message)

    prior = np.geterr()
    prior_handler = np.geterrcall()
    log = ErrorLog()
    callbacks = []
    handler = (lambda *args: callbacks.append(args)) if mode == "call" else log
    try:
        np.seterrcall(handler)
        np.seterr(all=mode)
        expected_policy = np.geterr().copy()
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", RuntimeWarning)
            for psf in RANGE_CASES[:4]:
                prepare(api, psf)
                assert np.geterr() == expected_policy
                assert np.geterrcall() is handler
            prepare(api, np.ones((2, 3, 4)), voxel_size_um=(MAX, MAX, MAX))
            assert_error(
                api,
                "unrepresentable_otf_frequencies",
                np.ones((2, 2, 2)),
                voxel_size_um=(float(Q), 1, 1),
            )
            assert_error(api, "negative_psf", np.array([-float(Q), 1]).reshape(1, 1, 2))
            assert np.geterr() == expected_policy
            assert np.geterrcall() is handler
        assert not [warning for warning in seen if issubclass(warning.category, RuntimeWarning)]
        assert not callbacks
        assert not log.messages
        captured = capfd.readouterr()
        assert "Warning:" not in captured.out + captured.err
    finally:
        np.seterr(**prior)
        np.seterrcall(prior_handler)


@pytest.mark.parametrize(
    "case",
    [
        "missing-psf",
        "missing-spacing",
        "missing-origin",
        "missing-source",
        "positional-keywords",
        "extra",
    ],
)
def test_ordinary_python_binding(api: Any, case: str) -> None:
    psf = np.ones((1, 1, 1))
    args = [psf]
    kwargs = {"voxel_size_um": (1, 1, 1), "origin_zyx": (0, 0, 0), "source": "s"}
    if case == "missing-psf":
        args = []
    elif case.startswith("missing-"):
        kwargs.pop(
            {
                "missing-spacing": "voxel_size_um",
                "missing-origin": "origin_zyx",
                "missing-source": "source",
            }[case]
        )
    elif case == "positional-keywords":
        args += list(kwargs.values())
        kwargs = {}
    else:
        kwargs["extra"] = True
    with pytest.raises(TypeError) as caught:
        api[0](*args, **kwargs)
    assert not isinstance(caught.value, api[2])


@pytest.mark.parametrize("dtype", REAL_DTYPES)
def test_all_available_real_spacing_scalar_widths(api: Any, dtype: str) -> None:
    scalar = np.dtype(dtype).type(2)
    result = prepare(api, np.ones((2, 3, 4)), voxel_size_um=(scalar, scalar, scalar))
    assert result.voxel_size_um == (2.0, 2.0, 2.0)
    assert_frequencies(result, (2, 3, 4), (2, 2, 2))


@pytest.mark.parametrize(
    "dtype", sorted({np.dtype(code).str for code in np.typecodes["AllInteger"]})
)
def test_all_available_integer_origin_scalar_widths(api: Any, dtype: str) -> None:
    scalar = np.dtype(dtype).type(1)
    result = prepare(api, asymmetric(), origin_zyx=(scalar, scalar, scalar))
    assert result.origin_zyx == (1, 1, 1)
    assert_transfer(result.values, reference(asymmetric(), (1, 1, 1)), 24)


def test_preparation_performs_no_file_access(api: Any, monkeypatch: Any) -> None:
    # Public file-entry seams, restricted to the preparation call after import.
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("preparation attempted file access")

    with monkeypatch.context() as patch:
        patch.setattr("builtins.open", forbidden)
        patch.setattr(io, "open", forbidden)
        patch.setattr(os, "open", forbidden)
        result = prepare(api, asymmetric())
    assert_transfer(result.values, reference(asymmetric(), (0, 0, 0)), 24)


def test_standalone_public_usage_signed_exact_root_comparison(api: Any) -> None:
    # A fresh ordinary Python caller, with source-free diagnostics before imports.
    script = r"""
import sys
import warnings

def fail(kind, value, tb):
    print(f"{kind.__name__}: {value}", file=sys.stderr)
    while tb is not None:
        print(f"{tb.tb_frame.f_code.co_filename}:{tb.tb_lineno}: "
              f"{tb.tb_frame.f_code.co_name}", file=sys.stderr)
        tb = tb.tb_next

warnings.formatwarning = lambda message, category, filename, lineno, file=None, line=None: (
    f"{filename}:{lineno}: {category.__name__}: {message}\n")
sys.excepthook = fail
try:
    import itertools
    import numpy as np
    from simrecon import Otf3D, prepare_volume_otf
    psf = np.zeros((2, 2, 2))
    psf[0, 0, 0], psf[1, 1, 1] = 1, 3
    result = prepare_volume_otf(psf, voxel_size_um=(0.5, 1, 2),
                                origin_zyx=(0, 0, 0), source="standalone")
    assert isinstance(result, Otf3D)
    worst = 0.0
    for index, k in zip(np.ndindex(psf.shape), itertools.product((-1, 0), repeat=3),
                        strict=True):
        expected = (1 + 3 * (-1)**sum(k)) / 4
        error = abs(result.values[index] - expected)
        worst = max(worst, float(error))
        assert error <= 128 * 8 * 2**-52
    assert result.voxel_size_um == (0.5, 1.0, 2.0)
    print(f"signed full-volume maximum absolute error={worst:.17g}; "
          f"budget={128 * 8 * 2**-52:.17g}; dimensionless")
except Exception:
    fail(*sys.exc_info())
    sys.exit(1)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30, check=False
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "signed full-volume maximum absolute error=" in completed.stdout
    assert not completed.stderr


@pytest.mark.parametrize("layout", ["strided", "reversed", "readonly"])
def test_permitted_array_triples_preserved(api: Any, layout: str) -> None:
    spacing_owner = np.array([0.7, 9, 1.25, 9, 2.5, 9])
    origin_owner = np.array([0, 99, 1, 99, 1, 99], dtype=np.int64)
    spacing = spacing_owner[::2]
    origin = origin_owner[::2]
    if layout == "reversed":
        spacing = spacing[::-1]
        origin = origin[::-1]
    elif layout == "readonly":
        spacing.flags.writeable = False
        origin.flags.writeable = False
    spacing_before, origin_before = spacing_owner.copy(), origin_owner.copy()
    result = prepare(api, asymmetric(), voxel_size_um=spacing, origin_zyx=origin)
    assert result.voxel_size_um == tuple(float(v) for v in spacing)
    assert result.origin_zyx == tuple(int(v) for v in origin)
    assert_frequencies(result, (3, 4, 2), spacing)
    assert_transfer(result.values, reference(asymmetric(), tuple(int(v) for v in origin)), 24)
    np.testing.assert_array_equal(spacing_owner, spacing_before)
    np.testing.assert_array_equal(origin_owner, origin_before)


@pytest.mark.parametrize("case", ["negative", "nonfinite", "zero", "spacing"])
def test_rejection_preserves_readonly_reversed_input_and_owner(api: Any, case: str) -> None:
    owner = np.ones((4, 6, 4))
    psf = owner[::-2, ::-2, ::-2]
    kwargs = {}
    if case == "negative":
        psf[0, 0, 0] = -float(Q)
        code = "negative_psf"
    elif case == "nonfinite":
        psf[0, 0, 0] = np.nan
        code = "nonfinite_psf"
    elif case == "zero":
        psf[:] = 0
        code = "zero_psf_mass"
    else:
        kwargs = {"voxel_size_um": (1, 0, 1)}
        code = "invalid_otf_voxel_size"
    raw_before = owner.tobytes()
    psf.flags.writeable = False
    assert_error(api, code, psf, **kwargs)
    assert owner.tobytes() == raw_before
    assert not psf.flags.writeable


def transform_failure_inputs() -> Any:
    owner = asymmetric()
    psf = owner[::-1, ::-1, ::-1]
    psf.flags.writeable = False
    spacing_owner = np.array([0.7, 99, 1.25, 99, 2.5, 99])
    origin_owner = np.array([2, 99, 1, 99, 1, 99], dtype=np.int64)
    spacing = spacing_owner[::2]
    origin = origin_owner[::2]
    kwargs = {"voxel_size_um": spacing, "origin_zyx": origin, "source": " fault identity \n"}
    snapshots = [
        (array, array.shape, array.strides, array.dtype, array.flags.writeable, array.tobytes())
        for array in (owner, psf, spacing_owner, spacing, origin_owner, origin)
    ]
    return psf, kwargs, snapshots


def assert_transform_inputs_preserved(snapshots: Any) -> None:
    for array, shape, strides, dtype, writeable, raw in snapshots:
        assert array.shape == shape
        assert array.strides == strides
        assert array.dtype == dtype
        assert array.flags.writeable == writeable
        assert array.tobytes() == raw


@contextmanager
def transform_caller_policy(mode: Any, warning_action: Any) -> Iterator[None]:
    class Observer:
        def __init__(self) -> None:
            self.calls: list[Any] = []
            self.messages: list[str] = []

        def __call__(self, *args: Any) -> None:
            self.calls.append(args)

        def write(self, message: str) -> None:
            self.messages.append(message)

    previous_policy, previous_handler = np.geterr(), np.geterrcall()
    observer = Observer()
    try:
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter(warning_action, RuntimeWarning)
            before_filters = list(warnings.filters)
            before_show, before_format = warnings.showwarning, warnings.formatwarning
            np.seterrcall(observer)
            np.seterr(all=mode)
            expected_policy = np.geterr().copy()
            yield
            assert np.geterr() == expected_policy
            assert np.geterrcall() is observer
            assert warnings.filters == before_filters
            assert warnings.showwarning is before_show
            assert warnings.formatwarning is before_format
            assert not [item for item in seen if issubclass(item.category, RuntimeWarning)]
            assert not observer.calls
            assert not observer.messages
    finally:
        np.seterr(**previous_policy)
        np.seterrcall(previous_handler)


def transform_fault(original: Any, fault: Any) -> Any:
    calls: list[bool] = []

    def injected(a: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append(True)
        if isinstance(fault, BaseException):
            raise fault
        if fault == "emitted-runtime-warning":
            warnings.warn(
                "overflow encountered in numerical transform", RuntimeWarning, stacklevel=2
            )
            # If warning handling is absent, return a valid ordinary dependency result.
            # The real FFT supplies the dependency response, never an expected-value oracle.
            return original(a, *args, **kwargs)
        result = original(a, *args, **kwargs)
        part, kind = fault.split(":")
        nonfinite = {"nan": math.nan, "+inf": math.inf, "-inf": -math.inf}[kind]
        value = result.flat[-1]
        result.flat[-1] = (
            complex(nonfinite, float(value.imag))
            if part == "real"
            else complex(float(value.real), nonfinite)
        )
        return result

    return injected, calls


HANDLED_TRANSFORM_CASES = [
    "floating-point-error",
    "overflow-error",
    "raised-runtime-warning",
    "emitted-runtime-warning",
    "real:nan",
    "real:+inf",
    "real:-inf",
    "imag:nan",
    "imag:+inf",
    "imag:-inf",
]
ERROR_MODES = ["ignore", "warn", "raise", "call", "print", "log"]
WARNING_ACTIONS = ["always", "error", "ignore"]


@pytest.mark.parametrize("case", HANDLED_TRANSFORM_CASES)
@pytest.mark.parametrize("mode", ERROR_MODES)
@pytest.mark.parametrize("warning_action", WARNING_ACTIONS)
def test_transform_arithmetic_and_nonfinite_failure_is_whole_call_rejection(
    api: Any, monkeypatch: Any, capfd: Any, case: str, mode: str, warning_action: str
) -> None:
    psf, kwargs, snapshots = transform_failure_inputs()
    exception_types = {
        "floating-point-error": FloatingPointError,
        "overflow-error": OverflowError,
        "raised-runtime-warning": RuntimeWarning,
    }
    fault = (
        exception_types[case]("overflow in numerical transform")
        if case in exception_types
        else case
    )
    injected, calls = transform_fault(np.fft.fftn, fault)
    monkeypatch.setattr(np.fft, "fftn", injected)
    with transform_caller_policy(mode, warning_action):
        assert_error(api, "otf_transform_failure", psf, **kwargs)
        assert calls, "the approved transform seam was not reached"
        assert_transform_inputs_preserved(snapshots)
    captured = capfd.readouterr()
    assert "Warning:" not in captured.out + captured.err


@pytest.mark.parametrize("exception_type", [MemoryError, RuntimeError, TypeError, ValueError])
@pytest.mark.parametrize("mode", ERROR_MODES)
@pytest.mark.parametrize("warning_action", WARNING_ACTIONS)
def test_transform_memory_and_unrelated_exceptions_propagate(
    api: Any, monkeypatch: Any, capfd: Any, exception_type: Any, mode: str, warning_action: str
) -> None:
    psf, kwargs, snapshots = transform_failure_inputs()
    fault = exception_type("injected transform dependency failure")
    injected, calls = transform_fault(np.fft.fftn, fault)
    monkeypatch.setattr(np.fft, "fftn", injected)
    with transform_caller_policy(mode, warning_action):
        with pytest.raises(exception_type) as caught:
            prepare(api, psf, **kwargs)
        assert caught.value is fault
        assert calls, "the approved transform seam was not reached"
        assert_transform_inputs_preserved(snapshots)
    captured = capfd.readouterr()
    assert "Warning:" not in captured.out + captured.err


def assert_normalized_transform_call(
    psf: Any, origin: Any, samples: Any, sizes: Any, axes: Any, norm: Any
) -> None:
    with localcontext() as ctx:
        ctx.prec = 100
        total = sum((Decimal.from_float(float(v)) for v in psf.flat), Decimal(0))
        assert samples.shape == psf.shape
        assert samples.dtype in (np.dtype(np.float64), np.dtype(np.complex128))
        assert np.all(samples.imag == 0)
        assert norm in (None, "backward")
        selected_axes = tuple(range(3)) if axes is None else tuple(axes)
        assert len(selected_axes) == 3
        assert set(axis % 3 for axis in selected_axes) == {0, 1, 2}
        if sizes is not None:
            assert len(sizes) == 3
            assert all(
                size in (None, -1, psf.shape[axis % 3])
                for size, axis in zip(sizes, selected_axes, strict=True)
            )
        for position in np.ndindex(psf.shape):
            source_position = tuple(
                (p + o) % n for p, o, n in zip(position, origin, psf.shape, strict=True)
            )
            exact = Decimal.from_float(float(psf[source_position])) / total
            assert (
                abs(Decimal.from_float(float(samples[position].real)) - exact)
                <= 128 * psf.size * EPS
            )


def test_public_transform_seam_receives_normalized_origin_shifted_full_volume(
    api: Any, monkeypatch: Any
) -> None:
    original = np.fft.fftn
    psf, kwargs, snapshots = transform_failure_inputs()
    origin = tuple(int(v) for v in kwargs["origin_zyx"])
    captured = []

    def observe(a: Any, s: Any = None, axes: Any = None, norm: Any = None, out: Any = None) -> Any:
        captured.append((np.array(a, copy=True), s, axes, norm))
        return original(a, s=s, axes=axes, norm=norm, out=out)

    monkeypatch.setattr(np.fft, "fftn", observe)
    result = prepare(api, psf, **kwargs)
    assert captured, "the approved public transform boundary was not called"
    for samples, sizes, axes, norm in captured:
        assert_normalized_transform_call(psf, origin, samples, sizes, axes, norm)
    assert_transfer(result.values, reference(psf, origin), psf.size)
    assert_frequencies(result, psf.shape, kwargs["voxel_size_um"])
    assert_transform_inputs_preserved(snapshots)


# q/4 = 2**-1076 must be natively representable before constructing the wider source.
if np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076:

    def wider_partial_underflow_source() -> Any:
        with np.errstate(under="ignore"):
            quarter_q = np.ldexp(np.longdouble(1), -1076)
            psf = np.array([quarter_q, 3 * quarter_q], dtype=np.longdouble).reshape(1, 1, 2)
        psf.flags.writeable = False
        return psf

    def test_wider_partial_underflow_stored_samples_are_normalized(api: Any) -> None:
        psf = wider_partial_underflow_source()
        before = (psf.tobytes(), psf.shape, psf.strides, psf.dtype, psf.flags.writeable)
        # Converted samples are (0,q): modes (-1,0) give 0-1 and 0+1.
        expected = {
            (0, 0, 0): (Decimal(-1), Decimal(0)),
            (0, 0, 1): (Decimal(1), Decimal(0)),
        }
        result = prepare(api, psf, origin_zyx=(0, 0, 0))
        assert result.values.shape == (1, 1, 2)
        assert_transfer(result.values, expected, 2)
        assert (psf.tobytes(), psf.shape, psf.strides, psf.dtype, psf.flags.writeable) == before

    def test_wider_partial_underflow_stored_problem_selfcheck() -> None:
        psf = wider_partial_underflow_source()
        before = (psf.tobytes(), psf.shape, psf.strides, psf.dtype, psf.flags.writeable)
        assert np.isfinite(psf).all() and (psf > 0).all()
        assert psf[0, 0, 1] == 3 * psf[0, 0, 0]
        assert 4 * psf[0, 0, 0] == np.longdouble(float(Q))
        with np.errstate(under="ignore"):
            stored = psf.astype(np.float64)
        assert stored.dtype == np.dtype(np.float64) and stored.dtype.isnative
        assert tuple(stored.flat) == (0.0, float(Q))
        assert tuple(float(value) for value in psf.flat) == (0.0, float(Q))
        expected = reference(psf, (0, 0, 0))
        signed_analytic = np.array([-1, 1], dtype=np.complex128).reshape(1, 1, 2)
        assert_transfer(signed_analytic, expected, 2)
        assert (psf.tobytes(), psf.shape, psf.strides, psf.dtype, psf.flags.writeable) == before
        print(
            "native wider partial-underflow self-check: source=(q/4,3q/4); "
            "stored=(0,q); signed H=(-1,1): PASS"
        )


@contextmanager
def wider_conversion_policy_guard(
    mode: Literal["ignore", "warn", "raise", "call", "print", "log"], capfd: Any
) -> Iterator[None]:
    """Observe a real call, including NumPy's direct file-descriptor warning path."""
    prior = np.geterr()
    prior_handler = np.geterrcall()
    callbacks: list[Any] = []
    log = io.StringIO()
    handler = (lambda *args: callbacks.append(args)) if mode == "call" else log
    capfd.readouterr()
    try:
        np.seterrcall(handler)
        np.seterr(all=mode)
        expected_policy = np.geterr().copy()
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", RuntimeWarning)
            expected_filters = cast(Any, warnings.filters).copy()
            yield
            assert np.geterr() == expected_policy
            assert np.geterrcall() is handler
            assert warnings.filters == expected_filters
        assert not [item for item in seen if issubclass(item.category, RuntimeWarning)]
        assert not callbacks
        assert log.getvalue() == ""
        captured = capfd.readouterr()
        assert "Warning:" not in captured.out + captured.err
    finally:
        np.seterr(**prior)
        np.seterrcall(prior_handler)
    assert np.geterr() == prior
    assert np.geterrcall() is prior_handler


if np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
    def test_wider_partial_underflow_preserves_caller_policy(
        api: Any, mode: Literal["ignore", "warn", "raise", "call", "print", "log"], capfd: Any
    ) -> None:
        psf = wider_partial_underflow_source()
        spacing = np.array([0.7, 1.25, 2.5])
        spacing.flags.writeable = False
        inputs = (psf, spacing)
        before = [
            (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
            for array in inputs
        ]
        expected = {
            (0, 0, 0): (Decimal(-1), Decimal(0)),
            (0, 0, 1): (Decimal(1), Decimal(0)),
        }
        with wider_conversion_policy_guard(mode, capfd):
            result = prepare(api, psf, voxel_size_um=spacing, origin_zyx=(0, 0, 0))
            assert result.values.shape == (1, 1, 2)
            assert_transfer(result.values, expected, 2)
            assert_frequencies(result, psf.shape, spacing)
            assert [
                (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
                for array in inputs
            ] == before

    def test_native_wider_conversion_policy_selfcheck(capsys: Any) -> None:
        """Observe actual dependency casts; prescribe no product conversion algorithm."""
        import json

        prior = np.geterr()
        prior_handler = np.geterrcall()
        psf = wider_partial_underflow_source()
        before = (psf.tobytes(), psf.shape, psf.strides, psf.dtype, psf.flags.writeable)
        observations: list[dict[str, Any]] = []
        stored_problem = None
        try:
            for mode in ("ignore", "warn", "raise"):
                np.seterr(all=mode)
                expected_policy = np.geterr().copy()
                converted = None
                failure = None
                with warnings.catch_warnings(record=True) as seen:
                    warnings.simplefilter("always", RuntimeWarning)
                    expected_filters = cast(Any, warnings.filters).copy()
                    try:
                        converted = psf.astype(np.float64)
                    except FloatingPointError as error:
                        assert mode == "raise"
                        failure = str(error)
                    assert warnings.filters == expected_filters
                assert np.geterr() == expected_policy
                assert np.geterrcall() is prior_handler
                arithmetic = [item for item in seen if issubclass(item.category, RuntimeWarning)]
                assert not arithmetic or mode == "warn"
                if converted is not None:
                    assert converted.dtype == np.dtype(np.float64) and converted.dtype.isnative
                    assert tuple(converted.flat) == (0.0, float(Q))
                    if mode == "ignore":
                        stored_problem = converted
                else:
                    assert mode == "raise" and failure is not None
                observations.append(
                    {
                        "mode": mode,
                        "outcome": "FloatingPointError" if failure is not None else "converted",
                        "exception_message": failure,
                        "stored_samples_q_units": [0, 1] if converted is not None else None,
                        "warnings": [
                            {
                                "category": item.category.__name__,
                                "message": str(item.message),
                                "filename": item.filename,
                                "line": item.lineno,
                            }
                            for item in seen
                        ],
                    }
                )
                assert (
                    psf.tobytes(),
                    psf.shape,
                    psf.strides,
                    psf.dtype,
                    psf.flags.writeable,
                ) == before
            assert stored_problem is not None
            with np.errstate(all="ignore"):
                exact = reference(stored_problem, (0, 0, 0))
                signed = np.array([-1, 1], dtype=np.complex128).reshape(1, 1, 2)
                assert_transfer(signed, exact, 2)
        finally:
            np.seterr(**prior)
            np.seterrcall(prior_handler)
        assert np.geterr() == prior
        assert np.geterrcall() is prior_handler
        mechanism_observed = bool(observations[1]["warnings"]) and (
            observations[2]["outcome"] == "FloatingPointError"
        )
        # A silent backend is recorded honestly; B decides mechanism evidence adequacy.
        with capsys.disabled():
            print(
                "native wider conversion-policy self-check: "
                + json.dumps(
                    {
                        "dtype": str(psf.dtype),
                        "numpy_version": np.__version__,
                        "longdouble_minexp": int(np.finfo(np.longdouble).minexp),
                        "longdouble_nmant": int(np.finfo(np.longdouble).nmant),
                        "source_q_units": ["1/4", "3/4"],
                        "signed_H": [-1, 1],
                        "warn_raise_mechanism_observed": mechanism_observed,
                        "observations": observations,
                        "caller_policy_handler_and_input_restored": True,
                    },
                    sort_keys=True,
                )
            )


if WIDER_RANGE or np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
    @pytest.mark.parametrize(
        "case",
        (["psf-overflow", "spacing-overflow"] if WIDER_RANGE else [])
        + (
            ["psf-zero-underflow", "psf-negative-underflow", "spacing-underflow"]
            if np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076
            else []
        ),
    )
    def test_wider_invalid_conversions_preserve_caller_policy(
        api: Any,
        mode: Literal["ignore", "warn", "raise", "call", "print", "log"],
        case: str,
        capfd: Any,
    ) -> None:
        with np.errstate(all="ignore"):
            psf = np.ones((1, 1, 2))
            spacing = np.ones(3, dtype=np.longdouble)
            if case.endswith("overflow"):
                bad = np.finfo(np.longdouble).max
            else:
                bad = wider_partial_underflow_source()[0, 0, 0]
            if case == "psf-overflow":
                psf = np.array([1, bad], dtype=np.longdouble).reshape(1, 1, 2)
                code = "nonfinite_psf"
            elif case == "psf-zero-underflow":
                psf = np.full((1, 1, 2), bad, dtype=np.longdouble)
                code = "zero_psf_mass"
            elif case == "psf-negative-underflow":
                # Source is genuinely negative despite conversion to negative zero.
                psf = np.array([1, -bad], dtype=np.longdouble).reshape(1, 1, 2)
                code = "negative_psf"
            else:
                spacing[0] = bad
                code = "invalid_otf_voxel_size"
        psf.flags.writeable = False
        spacing.flags.writeable = False
        inputs = (psf, spacing)
        before = [
            (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
            for array in inputs
        ]
        with wider_conversion_policy_guard(mode, capfd):
            assert_error(api, code, psf, voxel_size_um=spacing, origin_zyx=(0, 0, 0))
            assert [
                (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
                for array in inputs
            ] == before


if np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076:

    @pytest.mark.parametrize("mode", ["ignore", "warn", "raise", "call", "print", "log"])
    @pytest.mark.parametrize("axis", [0, 1, 2])
    def test_wider_positive_subnormal_spacing_preserves_caller_policy(
        api: Any,
        mode: Literal["ignore", "warn", "raise", "call", "print", "log"],
        axis: int,
        capfd: Any,
    ) -> None:
        shape = [2, 2, 2]
        shape[axis] = 1
        psf = np.array([5.0, 1.0, 2.0, 3.0]).reshape(shape)
        with np.errstate(all="ignore"):
            spacing = np.array([0.5, 1.0, 2.0], dtype=np.longdouble)
            spacing[axis] = 3 * np.ldexp(np.longdouble(1), -1076)
        origin = np.array([n - 1 for n in shape], dtype=np.int64)
        inputs = (psf, spacing, origin)
        for array in inputs:
            array.flags.writeable = False
        before = [
            (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
            for array in inputs
        ]
        expected_spacing = [0.5, 1.0, 2.0]
        # The unique nearest float64 value to 3q/4 is q, never zero.
        expected_spacing[axis] = float(Q)
        expected_origin = tuple(n - 1 for n in shape)
        expected = reference(psf, expected_origin)
        source = " positive wider spacing \n"
        with wider_conversion_policy_guard(mode, capfd):
            result = prepare(api, psf, voxel_size_um=spacing, origin_zyx=origin, source=source)
            assert isinstance(result, api[1])
            assert result.voxel_size_um == tuple(expected_spacing)
            assert all(type(value) is float for value in result.voxel_size_um)
            assert result.origin_zyx == expected_origin
            assert all(type(value) is int for value in result.origin_zyx)
            assert result.source == source
            assert result.values.shape == tuple(shape)
            assert_transfer(result.values, expected, psf.size)
            assert_frequencies(result, shape, expected_spacing)
            outputs = [getattr(result, name) for name in ARRAY_FIELDS]
            for index, array in enumerate(outputs):
                assert isinstance(array, np.ndarray)
                assert array.dtype == np.dtype(np.complex128 if index == 0 else np.float64)
                assert array.dtype.isnative
                assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
                for other in (*inputs, *outputs[index + 1 :]):
                    assert not np.shares_memory(array, other)
            assert [
                (array.tobytes(), array.shape, array.strides, array.dtype, array.flags.writeable)
                for array in inputs
            ] == before
