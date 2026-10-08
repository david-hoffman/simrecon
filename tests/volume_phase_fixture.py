"""Independent stored-input observer for the volume-phase public contract.

Decimal normal equations are an observer only, never a product solver. Inputs
and represented trigonometric entries are exact binary64 values lifted to
120 decimal digits. Scaling avoids both subnormal budgets and huge squares.
"""

from decimal import Decimal, localcontext

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
PRECISION = 120
# Construct in a sufficiently wide context, rather than the default 28 digits.
with localcontext() as _context:
    _context.prec = PRECISION
    EPSILON = Decimal(2) ** -52
    MIN_SUBNORMAL = Decimal(2) ** -1074


def exact(value: float | np.floating) -> Decimal:
    """Lift a stored native float, without a decimal-string approximation."""
    return Decimal.from_float(float(value))


def represented_basis(phases: np.ndarray) -> FloatArray:
    phi = np.array(phases, dtype=np.float64, copy=True)
    c = np.cos(phi)
    s = np.sin(phi)
    return np.column_stack((np.ones(phi.size), c, s, c * c - s * s, (2 * c) * s))


def solve_decimal(matrix: list[list[Decimal]], rhs: list[Decimal]) -> list[Decimal]:
    """Small, partial-pivoted elimination independent of numerical libraries."""
    a = [row.copy() + [value] for row, value in zip(matrix, rhs, strict=True)]
    n = len(rhs)
    for j in range(n):
        pivot = max(range(j, n), key=lambda k: abs(a[k][j]))
        if not a[pivot][j]:
            raise ValueError("observer matrix is singular")
        a[j], a[pivot] = a[pivot], a[j]
        divisor = a[j][j]
        a[j] = [value / divisor for value in a[j]]
        for k in range(n):
            if k != j:
                factor = a[k][j]
                a[k] = [x - factor * y for x, y in zip(a[k], a[j], strict=True)]
    return [row[-1] for row in a]


def decimal_system(
    phases: np.ndarray,
) -> tuple[list[list[Decimal]], list[list[Decimal]]]:
    h = [[exact(value) for value in row] for row in represented_basis(phases)]
    gram = [[sum((row[i] * row[j] for row in h), Decimal(0)) for j in range(5)] for i in range(5)]
    return h, gram


def condition_upper_bound(phases: np.ndarray) -> Decimal:
    """cond_2(H) <= sqrt(||H' H||_inf * ||(H' H)^-1||_inf).

    Both matrices are symmetric, so the infinity norm bounds the spectral
    norm. This checks the informative regime without a library SVD oracle.
    """
    with localcontext() as ctx:
        ctx.prec = PRECISION
        _, gram = decimal_system(phases)
        columns = [solve_decimal(gram, [Decimal(int(i == j)) for i in range(5)]) for j in range(5)]
        norm = max(sum((abs(x) for x in row), Decimal(0)) for row in gram)
        inverse_norm = max(
            sum((abs(columns[j][i]) for j in range(5)), Decimal(0)) for i in range(5)
        )
        return (norm * inverse_norm).sqrt()


def stored_input_oracle(
    images: np.ndarray, phases: np.ndarray
) -> tuple[list[list[Decimal]], list[Decimal]]:
    """Five output coordinates and the contract's intensity-unit budgets.

    Each voxel is normalized by its exact max |b| before the 5x5 solve.
    The output conversion from (A,B1,C1,B2,C2) is (A,B1/2,-C1/2,B2/2,-C2/2).
    No production solver, result, or float64 normal equation is used.
    """
    converted = np.array(images, dtype=np.float64, copy=True)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        h, gram = decimal_system(phases)
        answers: list[list[Decimal]] = []
        budgets: list[Decimal] = []
        divisors = [Decimal(1), Decimal(2), Decimal(-2), Decimal(2), Decimal(-2)]
        for values in converted.reshape(converted.shape[0], -1).T:
            b = [exact(value) for value in values]
            scale = max(abs(value) for value in b)
            if scale:
                normalized = [value / scale for value in b]
                rhs = [
                    sum(
                        (row[j] * value for row, value in zip(h, normalized, strict=True)),
                        Decimal(0),
                    )
                    for j in range(5)
                ]
                fitted = solve_decimal(gram, rhs)
                answers.append(
                    [
                        value * scale / divisor
                        for value, divisor in zip(fitted, divisors, strict=True)
                    ]
                )
            else:
                answers.append([Decimal(0)] * 5)
            budgets.append(8192 * len(h) * EPSILON * scale + 8 * MIN_SUBNORMAL)
        return answers, budgets


def synthesize(phases: np.ndarray, coordinates: np.ndarray) -> FloatArray:
    """Round each exact represented-model observation once to binary64.

    Coordinates use public order (dc, c1.real, c1.imag, c2.real, c2.imag).
    Object arrays of Decimals allow testing unrepresentable true outputs
    while keeping every stored observation finite.
    """
    shape = coordinates.shape[1:]
    flat = coordinates.reshape(5, -1)
    result = np.empty((len(phases), flat.shape[1]), dtype=np.float64)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        h, _ = decimal_system(phases)
        for p, row in enumerate(h):
            for v in range(flat.shape[1]):
                z = [value if isinstance(value, Decimal) else exact(value) for value in flat[:, v]]
                value = row[0] * z[0]
                value += 2 * row[1] * z[1] - 2 * row[2] * z[2]
                value += 2 * row[3] * z[3] - 2 * row[4] * z[4]
                result[p, v] = float(value)
    return result.reshape((len(phases), *shape))


def spatial_coordinates(shape: tuple[int, int, int] = (2, 3, 4)) -> FloatArray:
    """Distinct signed coefficients on each spatial axis and each order."""
    z, y, x = np.indices(shape, dtype=np.float64)
    return np.array(
        [
            10 + z / 8 + y / 4 + x / 2,
            2 + z / 4 - y / 8 + x / 16,
            -1 + z / 8 + y / 4 - x / 16,
            3 - z / 8 + y / 16 + x / 4,
            4 + z / 4 - y / 16 - x / 8,
        ]
    )


UNEQUAL_PHASES = np.array([-0.2, 0.43, 1.21, 2.04, 2.9, 3.63, 4.57, 5.38])
