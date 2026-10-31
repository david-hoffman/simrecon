"""Discrete exterior-zero reconstruction with explicit geometry and stopping.

This development mode consumes a supplied sampled kernel and illumination. It
does not infer the specimen exterior, optical parameters, or physical resolution.
"""

from __future__ import annotations

import math
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from simrecon import SimreconError

Array = NDArray[np.float64]
Triple = tuple[int, int, int]
Crop = tuple[tuple[int, int], tuple[int, int], tuple[int, int]]


@dataclass(frozen=True)
class FiniteFieldOperator:
    """Bind copied read-only model arrays and fixed z/y/x geometry."""

    kernel: Array
    kernel_origin_zyx: Triple
    illumination: Array
    detector_crop_zyx: Crop
    input_taper: Array
    padding_shape_zyx: Triple
    source_spacing_um_zyx: tuple[float, float, float]


@dataclass(frozen=True)
class FiniteFieldScore:
    """Bind unweighted predictions/residuals and the declared objective/gradient."""

    predicted_images: Array
    residual_images: Array
    gradient: Array
    data_objective: float
    penalty_objective: float
    total_objective: float


@dataclass(frozen=True)
class FiniteFieldFit:
    """Bind the accepted iterate, display output, and actual stopping evidence."""

    source: Array
    output: Array
    output_spacing_um_zyx: tuple[float, float, float]
    predicted_images: Array
    residual_images: Array
    gradient: Array
    data_objective: float
    penalty_objective: float
    total_objective: float
    objective_history: Array
    optimality_history: Array
    optimality_residual: float
    stopping_threshold: float
    iterations: int
    status: str
    converged: bool
    nonnegative: bool
    regularization: float


def _invalid(message: str) -> SimreconError:
    return SimreconError("invalid_finite_field_input", message)


def _range(message: str) -> SimreconError:
    return SimreconError("finite_field_range", message)


@contextmanager
def _arithmetic(stage: str) -> Iterator[None]:
    # Local error mode suppresses no unrelated warnings and restores caller state.
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        try:
            yield
        except (FloatingPointError, OverflowError) as exc:
            raise _range(f"Unrepresentable arithmetic during {stage}") from exc


def _addressable(shape: tuple[int, ...]) -> None:
    if any(s > sys.maxsize for s in shape) or math.prod(shape) > sys.maxsize // 8:
        raise _range("Required float64 array is not addressable")


def _array(value: object, name: str, ndim: int, shape: tuple[int, ...] | None = None) -> Array:
    if type(value) is not np.ndarray:
        raise _invalid(f"{name} must be a plain real ndarray")
    arr = cast(NDArray[Any], value)
    if arr.dtype.kind not in "iuf" or arr.ndim != ndim or any(s == 0 for s in arr.shape):
        raise _invalid(f"{name} has invalid dtype or dimensions")
    if shape is not None and arr.shape != shape:
        raise _invalid(f"{name} has incorrect shape")
    if not np.all(np.isfinite(arr)):
        raise _invalid(f"{name} must be finite")
    _addressable(arr.shape)
    with _arithmetic(f"{name} conversion"):
        result = np.array(arr, dtype=np.float64, order="C", copy=True)
    _finite(result)
    return result


def _finite(value: Array | float) -> None:
    if not np.all(np.isfinite(value)):
        raise _range("Required result is not finite float64")


def _tuple(value: object, length: int, name: str) -> tuple[Any, ...]:
    if type(value) is not tuple or len(value) != length:
        raise _invalid(f"{name} must be a tuple of length {length}")
    return value


def _integer(value: object, name: str, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise _invalid(f"{name} must be a Python integer >= {minimum}")
    return value


def _scalar(value: object, name: str) -> float:
    if type(value) not in (int, float):
        raise _invalid(f"{name} must be a nonnegative Python numeric scalar")
    try:
        result = float(cast(int | float, value))
    except OverflowError as exc:
        raise _range(f"{name} is not representable in float64") from exc
    if not math.isfinite(result) or result < 0:
        raise _invalid(f"{name} must be finite and nonnegative")
    return result


def _taper(value: object, name: str, shape: tuple[int, ...]) -> Array:
    result = _array(value, name, len(shape), shape)
    if np.any(result < 0) or np.any(result > 1):
        raise _invalid(f"{name} must lie in [0, 1]")
    return result


def build_finite_field_operator(
    *,
    kernel: object,
    kernel_origin_zyx: object,
    illumination: object,
    detector_crop_zyx: object,
    input_taper: object,
    padding_shape_zyx: object,
    source_spacing_um_zyx: object,
) -> FiniteFieldOperator:
    """Validate and copy a fixed exterior-zero finite convolution model.

    Padding must accommodate full linear convolution. The finite-sum backend
    evaluates only intersecting source/detector slices, so no padded array or
    dense optical matrix is needed. Extra padding cannot affect this map.
    Kernel brightness, origin and source spacing are used exactly as declared.
    """
    k = _array(kernel, "kernel", 3)
    light = _array(illumination, "illumination", 5)
    origin = tuple(
        _integer(v, "kernel origin", 0) for v in _tuple(kernel_origin_zyx, 3, "kernel_origin_zyx")
    )
    if any(o >= s for o, s in zip(origin, k.shape, strict=True)):
        raise _invalid("Kernel origin lies outside kernel")
    crop = tuple(
        tuple(_integer(v, "crop index", 0) for v in _tuple(pair, 2, "crop pair"))
        for pair in _tuple(detector_crop_zyx, 3, "detector_crop_zyx")
    )
    if any(not 0 <= a < b <= s for (a, b), s in zip(crop, light.shape[2:], strict=True)):
        raise _invalid("Crop must select a nonempty part of the fixed source box")
    padding = tuple(
        _integer(v, "padding dimension", 1)
        for v in _tuple(padding_shape_zyx, 3, "padding_shape_zyx")
    )
    if any(p < s + t - 1 for p, s, t in zip(padding, light.shape[2:], k.shape, strict=True)):
        raise _invalid("Padding is too small for full linear convolution")
    _addressable(padding)
    spacing = tuple(
        _scalar(v, "source spacing")
        for v in _tuple(source_spacing_um_zyx, 3, "source_spacing_um_zyx")
    )
    if any(v == 0 for v in spacing):
        raise _invalid("Source spacing must be positive")
    weights = _taper(input_taper, "input_taper", (*light.shape[:2], *(b - a for a, b in crop)))
    for array in (k, light, weights):
        array.setflags(write=False)
    return FiniteFieldOperator(
        k,
        cast(Triple, origin),
        light,
        cast(Crop, crop),
        weights,
        cast(Triple, padding),
        cast(tuple[float, float, float], spacing),
    )


def _overlaps(
    operator: FiniteFieldOperator,
) -> Iterator[tuple[float, tuple[slice, ...], tuple[slice, ...]]]:
    """Yield source and crop-local detector slices for each supported kernel lag."""
    for index in np.ndindex(operator.kernel.shape):
        coefficient = float(operator.kernel[index])
        if coefficient == 0:
            continue
        source_slices = []
        detector_slices = []
        for k, o, size, (start, stop) in zip(
            index,
            operator.kernel_origin_zyx,
            operator.illumination.shape[2:],
            operator.detector_crop_zyx,
            strict=True,
        ):
            lag = k - o
            lo, hi = max(start, lag), min(stop, size + lag)
            if lo >= hi:
                break
            source_slices.append(slice(lo - lag, hi - lag))
            detector_slices.append(slice(lo - start, hi - start))
        else:
            yield coefficient, tuple(source_slices), tuple(detector_slices)


def _forward(operator: FiniteFieldOperator, source: Array) -> Array:
    result = np.zeros(operator.input_taper.shape, dtype=np.float64)
    with _arithmetic("finite forward sum"):
        for coefficient, src, det in _overlaps(operator):
            index = (slice(None), slice(None), *src)
            result[(slice(None), slice(None), *det)] += (
                operator.illumination[index] * source[src] * coefficient
            )
    _finite(result)
    return result


def _adjoint(operator: FiniteFieldOperator, detector: Array) -> Array:
    result = np.zeros(operator.illumination.shape[2:], dtype=np.float64)
    with _arithmetic("finite adjoint sum"):
        for coefficient, src, det in _overlaps(operator):
            contribution = (
                detector[(slice(None), slice(None), *det)]
                * coefficient
                * operator.illumination[(slice(None), slice(None), *src)]
            )
            result[src] += np.sum(contribution, axis=(0, 1))
    _finite(result)
    return result


def finite_field_forward(operator: FiniteFieldOperator, source: object) -> Array:
    """Return the unweighted real finite convolution on the fixed detector crop."""
    x = _array(source, "source", 3, operator.illumination.shape[2:])
    return _forward(operator, x)


def finite_field_adjoint(operator: FiniteFieldOperator, detector: object) -> Array:
    """Return the real transpose with detector rows at their original coordinates."""
    y = _array(detector, "detector", 5, operator.input_taper.shape)
    return _adjoint(operator, y)


def _score(operator: FiniteFieldOperator, x: Array, y: Array, alpha: float) -> FiniteFieldScore:
    predicted = _forward(operator, x)
    with _arithmetic("objective and residual weighting"):
        residual = predicted - y
        weighted = operator.input_taper * residual
        normalized = weighted / math.sqrt(2 * y.size)
        data = float(np.sum(normalized * normalized))
        penalized = (x * math.sqrt(alpha)) / math.sqrt(2 * x.size)
        penalty = float(np.sum(penalized * penalized))
        # Divide before backprojection: its normalized result can be representable
        # even when the unnormalized transpose sum would overflow.
        adjoint_input = (weighted / y.size) * operator.input_taper
    gradient = _adjoint(operator, adjoint_input)
    with _arithmetic("ridge gradient"):
        gradient += (x / x.size) * alpha
        total = data + penalty
    for value in (residual, gradient, data, penalty, total):
        _finite(value)
    return FiniteFieldScore(predicted, residual, gradient, data, penalty, total)


def finite_field_score(
    operator: FiniteFieldOperator,
    source: object,
    *,
    images: object,
    regularization: object,
) -> FiniteFieldScore:
    """Evaluate the float64 residual-weighted ridge objective and its gradient."""
    x = _array(source, "source", 3, operator.illumination.shape[2:])
    y = _array(images, "images", 5, operator.input_taper.shape)
    alpha = _scalar(regularization, "regularization")
    return _score(operator, x, y, alpha)


def _stationarity(x: Array, gradient: Array, nonnegative: bool) -> tuple[Array, float]:
    k = np.where(x > 0, gradient, np.minimum(gradient, 0)) if nonnegative else gradient.copy()
    return k, float(np.max(np.abs(k)))


def _step(
    operator: FiniteFieldOperator,
    x: Array,
    score: FiniteFieldScore,
    k: Array,
    rho: float,
    alpha: float,
    nonnegative: bool,
) -> Array:
    """Minimize the quadratic along a normalized feasible steepest direction."""
    with _arithmetic("steepest direction"):
        direction = -k / rho
    mapped = _forward(operator, direction)
    with _arithmetic("directional curvature"):
        weighted = operator.input_taper * mapped / math.sqrt(mapped.size)
        ridge = direction * (math.sqrt(alpha) / math.sqrt(x.size))
        curvature = float(np.sum(weighted * weighted) + np.sum(ridge * ridge))
        slope = -float(np.sum(score.gradient * direction))
    _finite(curvature)
    _finite(slope)
    if curvature <= 0 or slope <= 0:
        raise SimreconError("finite_field_solver_failure", "No positive descent curvature")
    with _arithmetic("source update"):
        length = slope / curvature
        _finite(length)
        candidate = x + length * direction
        if nonnegative:
            crossing = candidate < 0
            if np.any(crossing):
                # Only crossing entries are divided; their ratios are <= length.
                length = float(np.min(x[crossing] / -direction[crossing]))
                candidate = x + length * direction
                # Enforce the limiting boundary exactly, avoiding a tiny positive
                # roundoff residue that would prevent active-set identification.
                limiting = crossing & (x == -length * direction)
                candidate[limiting] = 0
            candidate = np.maximum(candidate, 0)
    _finite(candidate)
    return candidate


def _display(x: Array, taper: Array, zoom: int) -> Array:
    with _arithmetic("display taper and interpolation"):
        result = x * taper
        # Separable interpolation uses only convex adjacent samples, with fixed
        # endpoints. Singleton axes never grow and no periodic extension occurs.
        if zoom != 1:
            for axis, size in enumerate(x.shape):
                if size == 1:
                    continue
                locations = np.arange(zoom * (size - 1) + 1, dtype=np.float64) / zoom
                lo = np.floor(locations).astype(np.intp)
                hi = np.minimum(lo + 1, size - 1)
                fraction = locations - lo
                shape = [1] * 3
                shape[axis] = locations.size
                fraction = fraction.reshape(shape)
                result = (
                    np.take(result, lo, axis=axis) * (1 - fraction)
                    + np.take(result, hi, axis=axis) * fraction
                )
    _finite(result)
    return np.array(result, dtype=np.float64, order="C", copy=True)


def solve_finite_field(
    operator: FiniteFieldOperator,
    *,
    images: object,
    regularization: object,
    nonnegative: object,
    max_iterations: object,
    absolute_tolerance: object,
    relative_tolerance: object,
    output_taper: object,
    output_zoom: object,
) -> FiniteFieldFit:
    """Solve from zero, stopping only on the declared infinity-norm criterion.

    Feasible steepest descent uses exact quadratic line minimization, clipped at
    the first nonnegativity boundary. Each accepted update is rescored through
    the original finite map. A fixed point above threshold is stagnation; budget
    exhaustion is an iteration limit. Neither establishes convergence.
    Display interpolation and taper never enter this optimization.
    """
    y = _array(images, "images", 5, operator.input_taper.shape)
    alpha = _scalar(regularization, "regularization")
    if type(nonnegative) is not bool:
        raise _invalid("nonnegative must be a Python bool")
    budget = _integer(max_iterations, "max_iterations", 0)
    atol = _scalar(absolute_tolerance, "absolute_tolerance")
    rtol = _scalar(relative_tolerance, "relative_tolerance")
    if atol == 0 and rtol == 0:
        raise _invalid("At least one tolerance must be positive")
    zoom = _integer(output_zoom, "output_zoom", 1)
    shape = operator.illumination.shape[2:]
    taper = _taper(output_taper, "output_taper", shape)
    _addressable(tuple(zoom * (s - 1) + 1 for s in shape))
    with _arithmetic("output spacing"):
        spacing = tuple(s / zoom for s in operator.source_spacing_um_zyx)
    if any(s == 0 or not math.isfinite(s) for s in spacing):
        raise _range("Output spacing is not representable and positive")
    x = np.zeros(shape, dtype=np.float64)
    score = _score(operator, x, y, alpha)
    k, rho = _stationarity(x, score.gradient, nonnegative)
    with _arithmetic("stopping threshold"):
        threshold = atol + rtol * rho
    _finite(threshold)
    objectives = [score.total_objective]
    optimalities = [rho]
    iterations = 0
    while True:
        if rho <= threshold:
            status = "converged"
            break
        if iterations >= budget:
            status = "iteration_limit"
            break
        candidate = _step(operator, x, score, k, rho, alpha, nonnegative)
        if np.array_equal(candidate, x):
            status = "stagnation"
            break
        x = candidate
        score = _score(operator, x, y, alpha)
        k, rho = _stationarity(x, score.gradient, nonnegative)
        iterations += 1
        objectives.append(score.total_objective)
        optimalities.append(rho)
    return FiniteFieldFit(
        source=np.array(x, dtype=np.float64, order="C", copy=True),
        output=_display(x, taper, zoom),
        output_spacing_um_zyx=cast(tuple[float, float, float], spacing),
        predicted_images=score.predicted_images,
        residual_images=score.residual_images,
        gradient=score.gradient,
        data_objective=score.data_objective,
        penalty_objective=score.penalty_objective,
        total_objective=score.total_objective,
        objective_history=np.array(objectives, dtype=np.float64),
        optimality_history=np.array(optimalities, dtype=np.float64),
        optimality_residual=rho,
        stopping_threshold=threshold,
        iterations=iterations,
        status=status,
        converged=status == "converged",
        nonnegative=nonnegative,
        regularization=alpha,
    )
