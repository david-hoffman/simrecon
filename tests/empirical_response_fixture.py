"""Independent dyadic/direct-sum observers; no SIMrecon imports or FFT oracle."""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from typing import Any

import numpy as np

Array = np.ndarray[Any, Any]
PRECISION = 120
PI = Decimal(
    "3.141592653589793238462643383279502884197169399375105820974944592307816406"
    "286208998628034825342117067982148086513282306647093844609550582231725359"
)
EPS = Fraction(1, 2**52)
Q = Fraction(1, 2**1074)
F = Fraction.from_float(float(np.finfo(np.float64).max))


def dyadic(value: Any) -> Fraction:
    return Fraction.from_float(float(value))


def dec(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def root(turns: Fraction) -> tuple[Decimal, Decimal]:
    """Negative-exponent unit root, exact for quadrant roots."""
    turns %= 1
    exact = {
        Fraction(0): (Decimal(1), Decimal(0)),
        Fraction(1, 4): (Decimal(0), Decimal(-1)),
        Fraction(1, 2): (Decimal(-1), Decimal(0)),
        Fraction(3, 4): (Decimal(0), Decimal(1)),
    }
    if turns in exact:
        return exact[turns]
    if turns > Fraction(1, 2):
        turns -= 1
    x = -2 * PI * dec(turns)
    square = x * x
    cosine = term_c = Decimal(1)
    sine = term_s = x
    for n in range(1, 250):
        term_c *= -square / Decimal((2 * n - 1) * (2 * n))
        term_s *= -square / Decimal((2 * n) * (2 * n + 1))
        cosine += term_c
        sine += term_s
        if abs(term_c) + abs(term_s) < Decimal("1e-125"):
            break
    return cosine, sine


@dataclass(frozen=True)
class DirectResponse:
    """Independent centered spectrum, exact mass and acceptance budgets."""

    # Each object-array item is (Decimal real, Decimal imaginary).
    values: Array
    budgets: tuple[Decimal, Decimal, Decimal]
    mass: Fraction
    origin: tuple[int, int, int]


def direct_response(dc: Array, c1: Array, c2: Array) -> DirectResponse:
    """Sum stored binary64 samples at signed modes, with exact converted mass."""
    a0 = np.array(dc, dtype=np.float64)
    sides = [np.array(c, dtype=np.complex128) for c in (c1, c2)]
    shape = tuple(int(n) for n in a0.shape)
    coordinates = list(product(*(range(n) for n in shape)))
    origin = tuple(int(i) for i in np.unravel_index(np.argmax(a0), shape))
    assert len(origin) == 3
    origin3 = (origin[0], origin[1], origin[2])
    mass = sum((dyadic(a0[j]) for j in coordinates), Fraction())
    assert mass > 0
    out = np.empty((3, *shape), dtype=object)
    budgets: list[Decimal] = []
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for m, array in enumerate([a0, *sides]):
            samples = {j: (dyadic(array[j].real), dyadic(array[j].imag)) for j in coordinates}
            norm = sum((abs(r) + abs(i) for r, i in samples.values()), Fraction())
            budgets.append(
                dec(512 * len(coordinates) * EPS * norm / mass + 16 * len(coordinates) * Q)
            )
            for shifted in coordinates:
                modes = tuple(s - n // 2 for s, n in zip(shifted, shape, strict=True))
                real = Decimal(0)
                imag = Decimal(0)
                for j, (r, i) in samples.items():
                    turns = sum(
                        (
                            Fraction(k * ((p - b) % n), n)
                            for k, p, b, n in zip(modes, j, origin3, shape, strict=True)
                        ),
                        Fraction(),
                    )
                    cosine, sine = root(turns)
                    real += dec(r / mass) * cosine - dec(i / mass) * sine
                    imag += dec(r / mass) * sine + dec(i / mass) * cosine
                out[(m, *shifted)] = (real, imag)
    return DirectResponse(out, (budgets[0], budgets[1], budgets[2]), mass, origin3)


def assert_direct(actual: Array, expected: DirectResponse) -> None:
    assert actual.shape == expected.values.shape
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index in np.ndindex(actual.shape):
            er, ei = expected.values[index]
            dr = dec(dyadic(actual[index].real)) - er
            di = dec(dyadic(actual[index].imag)) - ei
            error = (dr * dr + di * di).sqrt()
            # Observer uncertainty is at least 100 decimal digits below the
            # project's ordinary eps budget. Exact roots have no trig error.
            observer = max(abs(er), abs(ei), Decimal(1)) * Decimal("1e-110")
            # Do not weaken a q-scale project budget with a unit-scale floor.
            observer = min(observer, expected.budgets[index[0]] * Decimal("1e-80"))
            assert error <= expected.budgets[index[0]] + observer, (
                index,
                error,
                expected.budgets[index[0]],
            )


def asymmetric(shape: tuple[int, int, int] = (2, 3, 4)) -> tuple[Array, Array, Array]:
    j = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    dc = (j % 5 - 2) / 8
    dc[-1, 0, -1] = 8
    c1 = (j - 7) / 16 + 1j * ((j * 3 % 11) - 5) / 8
    c2 = ((j * 7 % 13) - 6) / 4 + 1j * (j - 12) / 32
    return dc, c1, c2


def frequencies(n: int, spacing: float) -> list[Fraction]:
    return [Fraction(k, n) / dyadic(spacing) for k in range(-(n // 2), (n + 1) // 2)]


def represented_fit(images: Array, phases: Array) -> Array:
    """120-digit independent normal-equation observer on represented K.

    Only small well-conditioned fixtures use this observer. Production's SVD
    implementation and empirical response are never called here.
    """
    c, s = np.cos(phases), np.sin(phases)
    k = np.column_stack(
        (np.ones(len(phases)), 2 * c, -2 * s, 2 * (c * c - s * s), -2 * ((2 * c) * s))
    )
    result = np.empty((5, *images.shape[1:]), dtype=object)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        kd = [[dec(dyadic(v)) for v in row] for row in k]
        gram = [
            [sum((row[i] * row[j] for row in kd), Decimal()) for j in range(5)] for i in range(5)
        ]
        for xyz in np.ndindex(images.shape[1:]):
            b = [dec(dyadic(images[(p, *xyz)])) for p in range(len(phases))]
            rhs = [
                sum((row[i] * v for row, v in zip(kd, b, strict=True)), Decimal()) for i in range(5)
            ]
            matrix = [row.copy() + [v] for row, v in zip(gram, rhs, strict=True)]
            for col in range(5):
                pivot = max(range(col, 5), key=lambda r: abs(matrix[r][col]))
                matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
                divisor = matrix[col][col]
                assert divisor != 0
                matrix[col] = [v / divisor for v in matrix[col]]
                for row in range(5):
                    if row == col:
                        continue
                    factor = matrix[row][col]
                    matrix[row] = [
                        v - factor * w for v, w in zip(matrix[row], matrix[col], strict=True)
                    ]
            for i in range(5):
                result[(i, *xyz)] = matrix[i][-1]
    return result
