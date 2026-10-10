"""Blind A expectations for OTF-CALIBRATION K01--K29.

No FFT, stored rounded table, or product output supplies an oracle here.
Converted binary64 samples become exact Fractions before normalization.
Roots of unity use exact quarter-turn identities or 110-digit Decimal Taylor
series after exact rational turn reduction. Machin's identity supplies pi:
pi = 16*atan(1/5) - 4*atan(1/239). Each alternating series stops below
1e-115. For these small grids, fewer than 10,000 rounded operations per bin,
with intermediate root magnitudes below 32, give an error far below the
1e-95 guard. Positive normalized weights sum to one, so root errors do not
amplify with source brightness. This guard is independent of the product's
128*M*2^-52 + 4*M*2^-1074 budget; both terms of that budget remain exact.

Comparisons square exact rational component errors. They never round the
expected complex value or acceptance threshold back to binary64. Frequency
expectations and their 8*eps*abs(f)+q bounds are entirely exact Fractions.
"""

from collections.abc import Iterator
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from typing import Any, Protocol, cast

import numpy as np
import numpy.typing as npt

RealArray = npt.NDArray[Any]
ComplexArray = npt.NDArray[np.complex128]
FloatArray = npt.NDArray[np.float64]
ComplexReference = tuple[Fraction, Fraction]
EPS = Fraction(1, 2**52)
Q = Fraction(1, 2**1074)
ORACLE_GUARD = Fraction(1, 10**95)
PRECISION = 110


class OtfRecord(Protocol):
    """Only contract attributes; no implementation-derived binding."""

    values: ComplexArray
    fy_per_um: FloatArray
    fx_per_um: FloatArray
    pixel_size_um: tuple[float, float]
    origin_yx: tuple[int, int]
    source: str


class PrepareOtf(Protocol):
    """Typed dynamic binding for the specified public preparation call."""

    def __call__(
        self,
        psf: object,
        *,
        pixel_size_um: object,
        origin_yx: object,
        source: object,
    ) -> OtfRecord: ...


class RecordFactory(Protocol):
    """Typed dynamic binding for direct unvalidated public construction."""

    def __call__(
        self,
        *,
        values: object,
        fy_per_um: object,
        fx_per_um: object,
        pixel_size_um: object,
        origin_yx: object,
        source: object,
    ) -> OtfRecord: ...


def modes(length: int) -> tuple[int, ...]:
    return tuple(range(-(length // 2), (length + 1) // 2))


def _decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _atan_inverse(divisor: int) -> Decimal:
    x = Decimal(1) / Decimal(divisor)
    power = x
    total = x
    n = 1
    while True:
        power *= -(x * x)
        term = power / Decimal(2 * n + 1)
        total += term
        if abs(term) < Decimal("1e-115"):
            return total
        n += 1


@cache
def _pi() -> Decimal:
    with localcontext() as context:
        context.prec = PRECISION
        return 16 * _atan_inverse(5) - 4 * _atan_inverse(239)


@cache
def negative_root(turns: Fraction) -> ComplexReference:
    """exp(-2*pi*i*turns), reduced modulo one before approximation."""
    reduced = turns % 1
    exact = {
        Fraction(0): (Fraction(1), Fraction(0)),
        Fraction(1, 4): (Fraction(0), Fraction(-1)),
        Fraction(1, 2): (Fraction(-1), Fraction(0)),
        Fraction(3, 4): (Fraction(0), Fraction(1)),
    }
    if reduced in exact:
        return exact[reduced]
    if reduced > Fraction(1, 2):
        reduced -= 1
    with localcontext() as context:
        context.prec = PRECISION
        angle = -2 * _pi() * _decimal(reduced)
        square = angle * angle
        sine_term, cosine_term = angle, Decimal(1)
        sine, cosine = sine_term, cosine_term
        n = 1
        while True:
            sine_term *= -square / Decimal((2 * n) * (2 * n + 1))
            cosine_term *= -square / Decimal((2 * n - 1) * (2 * n))
            sine += sine_term
            cosine += cosine_term
            if max(abs(sine_term), abs(cosine_term)) < Decimal("1e-115"):
                return Fraction(cosine), Fraction(sine)
            n += 1


def reference_transfer(
    psf: RealArray, origin: tuple[int, int]
) -> tuple[tuple[ComplexReference, ...], ...]:
    """Complete negative-exponential sum for independently converted values."""
    with np.errstate(all="ignore"):
        converted = np.array(psf, dtype=np.float64, copy=True, order="C")
    ny, nx = converted.shape
    samples = [
        (y, x, Fraction.from_float(float(converted[y, x])))
        for y in range(ny)
        for x in range(nx)
        if converted[y, x] != 0
    ]
    mass = sum((value for _, _, value in samples), Fraction(0))
    assert mass > 0, "reference needs positive converted mass"
    normalized = [(y, x, value / mass) for y, x, value in samples]
    rows: list[tuple[ComplexReference, ...]] = []
    for ky in modes(ny):
        row: list[ComplexReference] = []
        for kx in modes(nx):
            real, imag = Fraction(0), Fraction(0)
            for y, x, weight in normalized:
                turns = Fraction(ky * (y - origin[0]), ny) + Fraction(kx * (x - origin[1]), nx)
                root_real, root_imag = negative_root(turns)
                real += weight * root_real
                imag += weight * root_imag
            row.append((real, imag))
        rows.append(tuple(row))
    return tuple(rows)


def transfer_budget(size: int) -> Fraction:
    return 128 * size * EPS + 4 * size * Q


def assert_transfer(
    actual: ComplexArray,
    expected: tuple[tuple[ComplexReference, ...], ...],
) -> None:
    shape = (len(expected), len(expected[0]))
    assert actual.shape == shape, "complete supplied grid must be retained"
    assert bool(np.isfinite(actual).all()), "nonfinite returned transfer"
    budget = transfer_budget(shape[0] * shape[1]) + ORACLE_GUARD
    for y, row in enumerate(expected):
        for x, (real, imag) in enumerate(row):
            returned = complex(actual[y, x])
            dr = Fraction.from_float(returned.real) - real
            di = Fraction.from_float(returned.imag) - imag
            assert dr * dr + di * di <= budget * budget, (
                f"complex absolute accuracy at public bin ({y}, {x})"
            )


def exact_frequency(length: int, spacing: float) -> tuple[Fraction, ...]:
    denominator = length * Fraction.from_float(spacing)
    return tuple(Fraction(k) / denominator for k in modes(length))


def assert_frequency(actual: FloatArray, length: int, spacing: float) -> None:
    assert actual.shape == (length,), "frequency vector shape"
    assert bool(np.isfinite(actual).all()), "frequency vector must be finite"
    expected = exact_frequency(length, spacing)
    for index, exact in enumerate(expected):
        returned = float(actual[index])
        if exact == 0:
            assert returned == 0, "zero mode must be exact zero"
        else:
            assert returned != 0, "nonzero mode must remain nonzero"
        error = abs(Fraction.from_float(returned) - exact)
        assert error <= 8 * EPS * abs(exact) + Q, (
            f"physical frequency accuracy at public index {index}"
        )
    assert all(float(a) < float(b) for a, b in zip(actual, actual[1:], strict=False)), (
        "frequency vectors must be strictly increasing"
    )


def analytic_cases() -> Iterator[tuple[str, RealArray, tuple[int, int]]]:
    delta = np.zeros((3, 5), dtype=np.uint8)
    delta[1, 2] = 7
    yield "delta-odd", delta, (1, 2)
    yield "uniform-even", np.full((4, 6), 5, dtype=np.uint8), (1, 2)
    asymmetric = np.zeros((4, 6), dtype=np.uint8)
    asymmetric[1, 2], asymmetric[2, 2], asymmetric[1, 3] = 3, 1, 4
    yield "asymmetric-even", asymmetric, (1, 2)
    yield "asymmetric-translated", np.roll(asymmetric, (-1, 2), axis=(0, 1)), (0, 4)
    yield (
        "separable-mixed",
        np.array([[1, 0, 1, 0], [2, 0, 2, 0], [1, 0, 1, 0]]),
        (
            1,
            0,
        ),
    )
    yield "singleton", np.array([[7]], dtype=np.uint8), (0, 0)


def permitted_dtypes() -> tuple[tuple[str, np.dtype[Any]], ...]:
    entries: list[tuple[str, np.dtype[Any]]] = []
    for label in ("i1", "i2", "i4", "i8", "u1", "u2", "u4", "u8", "f2", "f4", "f8"):
        for order in ("<", ">"):
            entries.append((order + label, np.dtype(order + label)))
    for order in ("<", ">"):
        entries.append((order + "longdouble", np.dtype(np.longdouble).newbyteorder(order)))
    return tuple(entries)


def wider_source_cases() -> tuple[tuple[str, RealArray, str], ...]:
    """No skip or invented wider capability on binary64-only longdouble."""
    wide = np.finfo(np.longdouble)
    narrow = np.finfo(np.float64)
    if wide.maxexp <= narrow.maxexp and wide.minexp - wide.nmant >= narrow.minexp - narrow.nmant:
        return ()
    cases: list[tuple[str, RealArray, str]] = []
    with np.errstate(all="ignore"):
        if wide.maxexp > narrow.maxexp:
            large = np.longdouble(narrow.max) * np.longdouble(2)
            cases.append(("overflow", np.array([[large, 1]], dtype=np.longdouble), "nonfinite_psf"))
        if wide.minexp - wide.nmant < narrow.minexp - narrow.nmant:
            tiny = np.longdouble(float(Q)) / np.longdouble(4)
            assert tiny > 0 and float(tiny) == 0, "wider underflow fixture capability"
            cases.append(
                ("negative-underflow", np.array([[-tiny, 1]], dtype=np.longdouble), "negative_psf")
            )
            cases.append(
                ("all-underflow", np.array([[tiny, tiny]], dtype=np.longdouble), "zero_psf_mass")
            )
    return tuple(cases)


def as_prepare(binding: object) -> PrepareOtf:
    return cast(PrepareOtf, binding)


def as_factory(binding: object) -> RecordFactory:
    return cast(RecordFactory, binding)
