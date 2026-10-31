"""Independent RA08 finite-sum oracles. No product imports or observations.

All coordinates are integer z/y/x. Matrix rows follow C-order detector layout;
columns follow C-order source layout. Arithmetic bounds are fixed pre-observation.
"""

from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]
EPS = np.finfo(np.float64).eps
# <=256 terms; 2048 eps per term allows finite sums/FFT roundoff at these scales.
# This is far below a float32 ulp for the nonbinary controls used in the suite.
ROUND_FACTOR = 2048.0
ATOL = 2e-10  # gradient units; chosen before observing a solver
RTOL = 2e-11
BUDGET = 4000  # tiny, well-conditioned controls only, not a universal guarantee


def finite_matrix(
    kernel: Array,
    origin: tuple[int, int, int],
    illumination: Array,
    crop: tuple[tuple[int, int], tuple[int, int], tuple[int, int]],
) -> Array:
    """Enumerate the declared finite sum directly, without FFT/convolution APIs."""
    shape = illumination.shape[2:]
    detectors = list(itertools.product(*(range(a, b) for a, b in crop)))
    matrix = np.zeros(
        (illumination.shape[0] * illumination.shape[1] * len(detectors), math.prod(shape))
    )
    row = 0
    for r, n in np.ndindex(illumination.shape[:2]):
        for d in detectors:
            for col, s in enumerate(np.ndindex(shape)):
                lag = tuple(d[i] - s[i] + origin[i] for i in range(3))
                if all(0 <= lag[i] < kernel.shape[i] for i in range(3)):
                    matrix[row, col] = kernel[lag] * illumination[(r, n, *s)]
            row += 1
    return matrix


def periodic_matrix(kernel: Array, origin: tuple[int, int, int], illumination: Array) -> Array:
    """Sum wrapped lags for the matched fixed-source periodic control."""
    shape = illumination.shape[2:]
    matrix = np.zeros(
        (illumination.shape[0] * illumination.shape[1] * math.prod(shape), math.prod(shape))
    )
    for r, n in np.ndindex(illumination.shape[:2]):
        for row, d in enumerate(np.ndindex(shape)):
            offset = (r * illumination.shape[1] + n) * int(np.prod(shape))
            for k in np.ndindex(kernel.shape):
                s = tuple((d[i] - k[i] + origin[i]) % shape[i] for i in range(3))
                matrix[offset + row, np.ravel_multi_index(s, shape)] += (
                    kernel[k] * illumination[(r, n, *s)]
                )
    return matrix


def geometry() -> dict[str, Any]:
    kernel = np.array(
        [[[0.13, 0.72, -0.21], [0.41, -0.17, 0.23]], [[-0.11, 0.31, 0.19], [0.07, 0.53, -0.29]]]
    )
    illumination = (np.arange(48, dtype=np.float64).reshape(2, 2, 2, 2, 3) % 11 - 3) / 5
    return dict(
        kernel=kernel,
        kernel_origin_zyx=(0, 1, 1),
        illumination=illumination,
        detector_crop_zyx=((0, 2), (1, 2), (0, 2)),
        input_taper=np.linspace(0, 1, 16).reshape(2, 2, 2, 1, 2),
        padding_shape_zyx=(3, 3, 5),
        source_spacing_um_zyx=(0.37, 0.21, 0.13),
    )


def tiny() -> dict[str, Any]:
    return dict(
        kernel=np.array([[[0.25, 1.0, 0.5]]]),
        kernel_origin_zyx=(0, 0, 1),
        illumination=np.array([[[[[1.0, 1.5, 0.75]]]], [[[[0.5, -1.0, 1.25]]]]]),
        detector_crop_zyx=((0, 1), (0, 1), (0, 3)),
        input_taper=np.array([[[[[1.0, 0.5, 0.75]]]], [[[[0.25, 1.0, 0.0]]]]]),
        padding_shape_zyx=(1, 1, 5),
        source_spacing_um_zyx=(0.5, 0.3, 0.2),
    )


def matrix_for(spec: dict[str, Any]) -> Array:
    return finite_matrix(
        spec["kernel"], spec["kernel_origin_zyx"], spec["illumination"], spec["detector_crop_zyx"]
    )


def score_reference(
    matrix: Array, weights: Array, x: Array, y: Array, alpha: float
) -> dict[str, Any]:
    flat = x.ravel()
    residual = matrix @ flat - y.ravel()
    weighted = weights.ravel() * residual
    data = float(weighted @ weighted / (2 * y.size))
    penalty = float(alpha * (flat @ flat) / (2 * x.size))
    return dict(
        predicted_images=(matrix @ flat).reshape(y.shape),
        residual_images=residual.reshape(y.shape),
        gradient=(
            (matrix.T @ (weights.ravel() ** 2 * residual)) / y.size + alpha * flat / x.size
        ).reshape(x.shape),
        data_objective=data,
        penalty_objective=penalty,
        total_objective=data + penalty,
    )


def normal_system(matrix: Array, weights: Array, y: Array, alpha: float) -> tuple[Array, Array]:
    w2 = weights.ravel() ** 2
    h = (
        matrix.T @ (w2[:, None] * matrix) / y.size
        + alpha * np.eye(matrix.shape[1]) / matrix.shape[1]
    )
    b = matrix.T @ (w2 * y.ravel()) / y.size
    return h, b


def exact_minimizer(h: Array, b: Array, nonnegative: bool) -> Array:
    """Enumerate all active sets for tiny SPD controls, no iterative oracle."""
    if not nonnegative:
        return np.linalg.solve(h, b)
    for flags in itertools.product((False, True), repeat=b.size):
        free = np.array(flags)
        x = np.zeros_like(b)
        if np.any(free):
            x[free] = np.linalg.solve(h[np.ix_(free, free)], b[free])
        g = h @ x - b
        if np.all(x[free] > 0) and np.all(g[~free] >= -64 * EPS):
            return x
    raise AssertionError("Independent active-set enumeration found no KKT point")


def optimality(x: Array, gradient: Array, nonnegative: bool) -> float:
    k = np.where(x > 0, gradient, np.minimum(gradient, 0)) if nonnegative else gradient
    return float(np.max(np.abs(k)))


def display_reference(x: Array, taper: Array, zoom: int) -> Array:
    """Tensor linear interpolation, explicitly evaluating up to eight corners."""
    src = x * taper
    out = np.zeros(tuple(zoom * (s - 1) + 1 for s in x.shape))
    for d in np.ndindex(out.shape):
        coords = tuple(v / zoom for v in d)
        lo = tuple(int(np.floor(v)) for v in coords)
        frac = tuple(coords[i] - lo[i] for i in range(3))
        for bits in itertools.product((0, 1), repeat=3):
            idx = tuple(min(lo[i] + bits[i], x.shape[i] - 1) for i in range(3))
            weight = np.prod([frac[i] if bits[i] else 1 - frac[i] for i in range(3)])
            out[d] += weight * src[idx]
    return out


def arithmetic_tolerance(*values: Any, terms: int = 256) -> float:
    scale = max(1.0, *(float(np.max(np.abs(v))) for v in values))
    return ROUND_FACTOR * EPS * terms * scale


def selfcheck() -> dict[str, Any]:
    """Own-oracle checks only. Analytic hand control and two-sided identities."""
    k = np.array([[[2.0, 3.0]]])
    a = finite_matrix(k, (0, 0, 0), np.ones((1, 1, 1, 1, 3)), ((0, 1), (0, 1), (0, 3)))
    np.testing.assert_array_equal(a, [[2, 0, 0], [3, 2, 0], [0, 3, 2]])
    spec = tiny()
    a = matrix_for(spec)
    y = (a @ np.array([1.0, -2.0, 1.0])).reshape(spec["input_taper"].shape)
    h, b = normal_system(a, spec["input_taper"], y, 0.2)
    results = {}
    for constrained in (False, True):
        x = exact_minimizer(h, b, constrained)
        g = h @ x - b
        assert optimality(x, g, constrained) < 256 * EPS
        results[str(constrained)] = x.tolist()
    assert np.any(np.asarray(results["False"]) < 0)
    assert np.any(np.asarray(results["True"]) == 0)
    # Linear tensor ramps have exact interpolation and no endpoint extension.
    ramp = np.arange(8, dtype=np.float64).reshape(2, 2, 2)
    zoomed = display_reference(ramp, np.ones_like(ramp), 2)
    zz, yy, xx = np.indices((3, 3, 3))
    np.testing.assert_array_equal(zoomed, 2 * zz + yy + xx / 2)
    return {
        "hand_triangular_matrix": [[2, 0, 0], [3, 2, 0], [0, 3, 2]],
        "tiny_matrix": a.tolist(),
        "tiny_condition_inf": float(np.linalg.cond(h, np.inf)),
        "minimizers": results,
        "epsilon": EPS,
        "arithmetic_base_tolerance": arithmetic_tolerance(1.0),
        "checks": "hand triangular matrix; SPD/KKT; exact trilinear ramp",
    }
