"""Independent stored-input oracle; no product implementation imports."""

import math
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt

FloatImage = npt.NDArray[np.float64]
Image = npt.NDArray[Any]


def grid(shape: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    """Canonical signed coordinates, including negative even half-periods."""
    ny, nx = shape
    return tuple(
        (dy, dx)
        for dy in range(-(ny // 2), (ny + 1) // 2)
        for dx in range(-(nx // 2), (nx + 1) // 2)
    )


def score_budget(size: int) -> float:
    return 4096 * size * 2.0**-52


def finite_sum_surface(moving: Image, reference: Image) -> FloatImage:
    """Exact rational differences/squares after the required float64 conversion.

    Only the final square root is rounded: 100 decimal significant digits,
    followed by conversion to float64. No FFT, correlation or product values.
    """
    m = np.array(moving, dtype=np.float64, copy=True)
    r = np.array(reference, dtype=np.float64, copy=True)
    ny, nx = m.shape
    mf = [[Fraction(float(v)) for v in row] for row in m]
    rf = [[Fraction(float(v)) for v in row] for row in r]
    scale = max(abs(v) for image in (mf, rf) for row in image for v in row)
    values: list[float] = []
    with localcontext() as context:
        context.prec = 100
        for dy, dx in grid((ny, nx)):
            if not scale:
                values.append(0.0)
                continue
            energy = sum(
                ((mf[(y + dy) % ny][(x + dx) % nx] - rf[y][x]) / scale) ** 2
                for y in range(ny)
                for x in range(nx)
            ) / (ny * nx)
            assert isinstance(energy, Fraction)
            values.append(float((Decimal(energy.numerator) / Decimal(energy.denominator)).sqrt()))
    return np.array(values, dtype=np.float64).reshape((ny, nx))


def patterned(shape: tuple[int, int]) -> Image:
    """Distinct signed integers, deliberately neither symmetric nor periodic."""
    ny, nx = shape
    return np.array(
        [
            [((17 * y + 11 * x + 7 * y * x + 3 * x * x) % 41) - 19 for x in range(nx)]
            for y in range(ny)
        ],
        dtype=np.int64,
    )


def periodic_motion(reference: Image, shift: tuple[int, int]) -> Image:
    """Construct motion by explicit modular indexing, independent of np.roll."""
    dy, dx = shift
    ny, nx = reference.shape
    return np.array(
        [[reference[(y - dy) % ny, (x - dx) % nx] for x in range(nx)] for y in range(ny)],
        dtype=reference.dtype,
    )


def robust_candidates(surface: FloatImage, tolerance: float) -> tuple[tuple[int, int], ...]:
    """Use oracle classification only where the contract guarantees stability."""
    low = float(np.min(surface))
    differences = [float(v) - low for v in surface.flat]
    error = 2 * score_budget(surface.size)
    # The minimum always qualifies at nonnegative tolerance. Other candidates
    # need a distance > 2 delta from the threshold to assert their membership.
    assert all(d == 0 or abs(d - tolerance) > error for d in differences)
    if differences.count(0.0) > 1:
        assert tolerance > error
    return tuple(
        point
        for point, difference in zip(grid(surface.shape), differences, strict=True)
        if difference <= tolerance
    )


def check_result(
    result: Any,
    moving: Image,
    reference: Image,
    tolerance: Any,
    result_type: type[Any],
    *,
    independent_membership: bool = True,
) -> FloatImage:
    """Check the full oracle and the exact same-call result bookkeeping."""
    assert isinstance(result, result_type)
    surface = result.normalized_rms
    assert type(surface) is np.ndarray
    assert surface.shape == moving.shape
    assert surface.dtype == np.dtype(np.float64)
    assert surface.dtype.isnative
    assert surface.flags.c_contiguous
    assert surface.flags.writeable
    assert np.isfinite(surface).all()
    assert not np.shares_memory(surface, moving)
    assert not np.shares_memory(surface, reference)
    expected = finite_sum_surface(moving, reference)
    error = float(np.max(np.abs(surface - expected)))
    assert error <= score_budget(moving.size), (error, score_budget(moving.size))
    minimum = result.minimum_normalized_rms
    assert type(minimum) is float
    assert math.isfinite(minimum)
    assert minimum == float(np.min(surface))
    converted_tolerance = float(np.asarray(tolerance, dtype=np.float64))
    actual_candidates = tuple(
        point
        for point, value in zip(grid(surface.shape), surface.flat, strict=True)
        if float(value) - minimum <= converted_tolerance
    )
    candidates = result.candidate_displacements_pixels_yx
    assert type(candidates) is tuple
    assert candidates
    assert all(type(pair) is tuple and len(pair) == 2 for pair in candidates)
    assert all(type(v) is int for pair in candidates for v in pair)
    assert candidates == actual_candidates
    if independent_membership:
        assert candidates == robust_candidates(expected, converted_tolerance)
    if len(candidates) == 1:
        assert result.displacement_pixels_yx == candidates[0]
        assert type(result.displacement_pixels_yx) is tuple
        assert all(type(v) is int for v in result.displacement_pixels_yx)
        assert result.failure_code is None
    else:
        assert result.displacement_pixels_yx is None
        assert result.failure_code == "ambiguous_translation"
    return expected
