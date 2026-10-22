"""Independent stored-input finite sums for the public volume contract."""

from decimal import Decimal, localcontext
from itertools import product

import numpy as np
from numpy.typing import NDArray


def canonical_grid(shape: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    """Enumerate the contract's signed grid, without product output."""
    return tuple(product(*(range(-(n // 2), (n + 1) // 2) for n in shape)))


def stored_surface(moving: NDArray, reference: NDArray) -> NDArray[np.float64]:
    """Evaluate periodic RMS in 100-digit Decimal after float64 conversion.

    Decimal.from_float captures each converted binary64 value exactly. The
    common scale, subtraction, square, mean and root are independent of any
    numerical backend used by the estimator. No raw float64 differences or
    squared energies enter this oracle.
    """
    # Python floats are binary64 on the selected stack. Convert elementwise
    # so the oracle's permitted cast-to-zero does not itself depend on the
    # caller's NumPy underflow handling during a bulk cast.
    indices = tuple(np.ndindex(moving.shape))
    with localcontext() as context:
        context.prec = 100
        md = {i: Decimal.from_float(float(moving[i])) for i in indices}
        rd = {i: Decimal.from_float(float(reference[i])) for i in indices}
        scale = max(abs(v) for v in (*md.values(), *rd.values()))
        if scale == 0:
            return np.zeros(moving.shape, dtype=np.float64)
        scores = []
        for displacement in canonical_grid(moving.shape):
            energy = Decimal(0)
            for index in indices:
                shifted = tuple(
                    (i + d) % n for i, d, n in zip(index, displacement, moving.shape, strict=True)
                )
                difference = md[shifted] / scale - rd[index] / scale
                energy += difference * difference
            scores.append(float((energy / Decimal(moving.size)).sqrt()))
    return np.array(scores, dtype=np.float64).reshape(moving.shape)


def score_allowance(size: int) -> float:
    """Contract allowance plus one binary64 oracle-rounding unit at score 2."""
    return 4096 * size * 2.0**-52 + 2.0**-51


def asymmetric_volume(shape: tuple[int, int, int] = (3, 4, 5)) -> NDArray:
    """Deterministic nonnegative content with a unique, high-contrast marker."""
    values = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    values = (values * values + 3 * values + 7) % 43
    values[0, 0, 0] = 257
    return values
