"""Fixed-calibration phase inference for an exterior-zero shared real source."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares

from ._model import SimreconError

type Real = NDArray[np.float64]
type Complex = NDArray[np.complex128]
type Mask = NDArray[np.bool_]

_INPUT = "invalid_exposure_phase_input"
_RANGE = "exposure_phase_range"
_NUMERICAL = "exposure_phase_numerical_failure"


@dataclass(frozen=True)
class ExposurePhaseCandidate:
    """One caller start, its best visited fit and independent local diagnostics.

    Phase information freezes the retained source subspace. It is neither
    unrestricted-source identifiability nor a truncated-profile derivative.
    Arrays are independently owned mutable snapshots; bindings are frozen.
    """

    initial_offsets_rad: Real
    offsets_rad: Real
    phases_rad: Real
    common_offset_rad: float | None
    independent_deviations_rad: Real
    source: Real
    predicted_images: Real
    residual_images: Real
    objective: float
    source_singular_values: Real
    source_rank: int
    phase_singular_values: Real
    phase_rank: int
    free_parameter_count: int
    information_status: str
    projected_gradient: float
    diagnostics_continuous: bool
    stationary: bool
    search_status: str
    search_evaluations: int
    diagnostic_evaluations: int
    global_ambiguity: str


@dataclass(frozen=True)
class ExposurePhaseFit:
    """Fixed gauge and caller-ordered candidates, without a selected winner."""

    mode: str
    input_phases_rad: Real
    carrier_per_um_yx: tuple[float, float]
    source_spacing_um_zyx: tuple[float, float, float]
    fit_mask: Mask
    candidates: tuple[ExposurePhaseCandidate, ...]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SimreconError(_INPUT, message)


def _finite(*values: Any, code: str = _RANGE) -> None:
    if any(not np.all(np.isfinite(value)) for value in values):
        raise SimreconError(code, "nonfinite numerical result")


@contextmanager
def _arithmetic(code: str = _RANGE) -> Iterator[None]:
    # Do not intercept warnings or unrelated exceptions from dependencies.
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            yield
    except (FloatingPointError, OverflowError) as error:
        raise SimreconError(code, "unrepresentable numerical arithmetic") from error


@contextmanager
def _numerical() -> Iterator[None]:
    try:
        with _arithmetic(_NUMERICAL):
            yield
    except np.linalg.LinAlgError as error:
        raise SimreconError(_NUMERICAL, "numerical dependency failed") from error


def _real(value: Any, name: str) -> Real:
    _require(type(value) is np.ndarray and value.dtype.kind in "iuf", f"invalid {name}")
    _require(bool(np.all(np.isfinite(value))), f"nonfinite {name}")
    with _arithmetic():
        try:
            # Explicit storage also handles platforms where longdouble has
            # binary64 representation but a distinct unsupported linalg type.
            result = np.empty(value.shape, dtype=np.float64, order="C")
            np.copyto(result, value, casting="unsafe")
        except (TypeError, ValueError) as error:
            raise SimreconError(_INPUT, f"cannot convert {name}") from error
    _finite(result)
    return result


def _scalar(value: Any, name: str, *, rank: bool = False) -> float:
    _require(
        isinstance(value, (int, float, np.integer, np.floating))
        and not isinstance(value, (bool, np.bool_)),
        f"invalid {name}",
    )
    _require(bool(np.isfinite(value)) if not isinstance(value, int) else True, f"invalid {name}")
    with _arithmetic():
        result = float(value)
    _finite(result)
    _require(0 < result < 1 if rank else result >= 0, f"invalid {name}")
    return result


def _integer_triple(value: Any, name: str) -> tuple[int, int, int]:
    _require(
        type(value) is tuple and len(value) == 3 and all(type(v) is int for v in value),
        f"invalid {name}",
    )
    return value


def _snapshot(value: Any) -> Real:
    return np.array(value, dtype=np.float64, order="C", copy=True)


def _svd(matrix: Real) -> tuple[Real, Real, Real]:
    with _numerical():
        u, singular, vh = np.linalg.svd(matrix, full_matrices=False)
    _finite(u, singular, vh, code=_NUMERICAL)
    return u, singular, vh


def _whiten(cholesky: Real, values: Real) -> Real:
    with _numerical():
        result = np.linalg.solve(cholesky, values)
    _finite(result)
    return result


def _geometry(
    kernels: Complex,
    origin: tuple[int, int, int],
    shape: tuple[int, int, int],
    crop: tuple[tuple[int, int], ...],
    spacing: tuple[float, float, float],
    carrier: Real,
) -> tuple[Complex, Real]:
    """Build only the three finite detector/source displacement operators."""
    try:
        indices = np.indices(shape).reshape(3, -1).T
        detector_shape = tuple(b - a for a, b in crop)
        detectors = np.indices(detector_shape).reshape(3, -1).T
        detectors += np.array([a for a, _ in crop])
        operators = np.zeros((3, len(detectors), len(indices)), dtype=np.complex128)
    except (ValueError, OverflowError) as error:
        raise SimreconError(_RANGE, "unrepresentable model workspace") from error
    coordinates = indices * np.array(spacing)
    _finite(coordinates)
    theta = 2 * np.pi * (carrier[0] * coordinates[:, 1] + carrier[1] * coordinates[:, 2])
    _finite(theta)
    for row, detector in enumerate(detectors):
        displacement = detector - indices + np.array(origin)
        valid = np.all((displacement >= 0) & (displacement < np.array(kernels.shape[1:])), axis=1)
        z, y, x = displacement[valid].T
        operators[:, row, valid] = kernels[:, z, y, x]
    return operators, theta


@dataclass
class _Point:
    phases: Real
    source: Real
    prediction: Real
    residual: Real
    objective: float
    singular: Real
    retained: Real
    rank: int
    weighted_residual: Real
    raw_derivative: Real


class _Profile:
    def __init__(
        self,
        operators: Complex,
        theta: Real,
        images: Real,
        labels: Real,
        mode: str,
        mask: Mask,
        cholesky: Real,
        source_rtol: float,
    ) -> None:
        self.operators = operators
        self.theta = theta
        self.images = images.reshape(len(labels), -1)
        self.labels = labels
        self.mode = mode
        self.mask = mask.reshape(-1)
        self.cholesky = cholesky
        self.source_rtol = source_rtol
        self.n = len(labels)
        self.voxels = operators.shape[2]
        self.m = self.n * int(np.count_nonzero(mask))
        self.data = (
            _whiten(cholesky, self.images[:, self.mask]).reshape(-1) if self.m else np.zeros(0)
        )

    def point(self, offsets: Real) -> _Point:
        phases = self.labels.copy() if self.mode == "known" else self.labels + offsets
        _finite(phases)
        model = np.empty((self.n, self.images.shape[1], self.voxels))
        # Reduce the represented full angle before doubling or exponentiation.
        angles = self.theta[None, :] + phases[:, None]
        _finite(angles)
        angles = np.remainder(angles, 2 * np.pi)
        first = np.cos(angles) + 1j * np.sin(angles)
        second = first * first
        for p in range(self.n):
            model[p] = (
                self.operators[0].real
                + 2 * (self.operators[1] * first[p]).real
                + 2 * (self.operators[2] * second[p]).real
            )
        _finite(model)
        if self.m:
            training = model[:, self.mask, :].reshape(self.n, -1)
            b_matrix = _whiten(self.cholesky, training).reshape(self.m, self.voxels)
            u, singular, vh = _svd(b_matrix)
            keep = singular > self.source_rtol * singular[0]
            retained = u[:, keep]
            rank = int(np.count_nonzero(keep))
            source = vh[keep].T @ ((retained.T @ self.data) / singular[keep])
        else:
            singular = np.zeros(0)
            retained = np.zeros((0, 0))
            rank = 0
            source = np.zeros(self.voxels)
        prediction = model @ source
        residual = prediction - self.images
        weighted = (
            _whiten(self.cholesky, residual[:, self.mask]).reshape(-1) if self.m else np.zeros(0)
        )
        objective = float((weighted @ weighted) / (2 * self.m)) if self.m else 0.0
        raw_derivative = np.empty_like(prediction)
        for p in range(self.n):
            raw_derivative[p] = (
                -2
                * ((self.operators[1] * first[p] + 2 * self.operators[2] * second[p]) @ source).imag
            )
        _finite(source, prediction, residual, weighted, objective, raw_derivative)
        return _Point(
            phases,
            source,
            prediction,
            residual,
            objective,
            singular,
            retained,
            rank,
            weighted,
            raw_derivative,
        )

    def sensitivity(self, point: _Point, axes: NDArray[np.intp], rtol: float) -> tuple[Real, int]:
        free = len(axes)
        if not self.m or not free:
            return np.zeros(free), 0
        directions = np.zeros((self.n, self.images.shape[1], free))
        for j, axis in enumerate(axes):
            if self.mode == "common":
                directions[:, :, j] = point.raw_derivative
            else:
                directions[axis, :, j] = point.raw_derivative[axis]
        d = _whiten(self.cholesky, directions[:, self.mask, :].reshape(self.n, -1))
        d = d.reshape(self.m, free)
        tangent = (d - point.retained @ (point.retained.T @ d)) / np.sqrt(self.m)
        _finite(tangent)
        _, singular, _ = _svd(tangent)
        singular = np.pad(singular, (0, free - len(singular)))
        rank = int(np.count_nonzero(singular > rtol * singular[0]))
        return singular, rank


class _EvaluationLimit(Exception):
    """End one local attempt while preserving its first best visited point."""


class _Search:
    def __init__(self, profile: _Profile, seed: Real, axes: NDArray[np.intp], budget: int) -> None:
        self.profile = profile
        self.seed = seed
        self.axes = axes
        self.budget = budget
        self.count = 0
        self.best_offsets = seed.copy()
        self.best: _Point | None = None
        self.cached_offsets: Real | None = None
        self.cached: _Point | None = None

    def evaluate(self, free_offsets: Real) -> Real:
        offsets = self.seed.copy()
        offsets[self.axes] = free_offsets
        if self.cached_offsets is not None and np.array_equal(offsets, self.cached_offsets):
            assert self.cached is not None
            return self.cached.weighted_residual
        if self.count == self.budget:
            raise _EvaluationLimit
        # Keep callback model/objective arithmetic in the range-error stage,
        # even when the caller is inside the optimizer dependency boundary.
        with _arithmetic():
            point = self.profile.point(offsets)
        self.count += 1
        self.cached_offsets, self.cached = offsets.copy(), point
        if self.best is None or point.objective < self.best.objective:
            self.best_offsets, self.best = offsets.copy(), point
        return point.weighted_residual


def _candidate(
    profile: _Profile,
    seed: Real,
    bounds: Real,
    steps: Real,
    source_shape: tuple[int, int, int],
    image_shape: tuple[int, ...],
    phase_rtol: float,
    gtol: float,
    budget: int,
) -> ExposurePhaseCandidate:
    axes = np.flatnonzero(bounds[0] < bounds[1])
    free = len(axes)
    search = _Search(profile, seed, axes, budget)
    search.evaluate(seed[axes])
    if free and budget > 1 and profile.m:
        try:
            with _numerical():
                least_squares(
                    search.evaluate,
                    seed[axes],
                    bounds=(bounds[0, axes], bounds[1, axes]),
                    ftol=1e-12,
                    xtol=1e-12,
                    gtol=1e-12,
                    max_nfev=budget,
                )
        except _EvaluationLimit:
            pass
    point = search.best
    assert point is not None
    offsets = search.best_offsets
    gradient, continuous, diagnostic_count = 0.0, True, 0
    for axis in axes:
        for direction, boundary in ((-1, bounds[0, axis]), (1, bounds[1, axis])):
            distance = direction * (boundary - offsets[axis])
            step = min(float(steps[axis]), float(distance))
            if step <= 0:
                continue
            neighbor = offsets.copy()
            neighbor[axis] += direction * step
            displaced = float(abs(neighbor[axis] - offsets[axis]))
            if displaced == 0:
                continue
            observed = profile.point(neighbor)
            diagnostic_count += 1
            gradient = max(gradient, float((point.objective - observed.objective) / displaced))
            continuous = continuous and point.rank == observed.rank
    _finite(gradient)
    stationary = continuous and gradient <= gtol
    phase_singular, phase_rank = profile.sensitivity(point, axes, phase_rtol)
    known = profile.mode == "known"
    status = (
        "known"
        if known
        else "fixed"
        if not free
        else "stationary"
        if stationary
        else "evaluation_limit"
        if search.count == budget
        else "stopped"
    )
    information = (
        "known"
        if known
        else "no_training_data"
        if not profile.m
        else "no_free_parameters"
        if not free
        else "full_local_rank"
        if phase_rank == free
        else "rank_deficient"
    )
    deviations = offsets - offsets[0] if profile.mode == "independent" else np.zeros(profile.n)
    _finite(deviations)
    return ExposurePhaseCandidate(
        initial_offsets_rad=_snapshot(seed),
        offsets_rad=_snapshot(offsets),
        phases_rad=_snapshot(point.phases),
        common_offset_rad=None if known else float(offsets[0]),
        independent_deviations_rad=_snapshot(deviations),
        source=_snapshot(point.source.reshape(source_shape)),
        predicted_images=_snapshot(point.prediction.reshape(image_shape)),
        residual_images=_snapshot(point.residual.reshape(image_shape)),
        objective=point.objective,
        source_singular_values=_snapshot(point.singular),
        source_rank=point.rank,
        phase_singular_values=_snapshot(phase_singular),
        phase_rank=phase_rank,
        free_parameter_count=free,
        information_status=information,
        projected_gradient=gradient,
        diagnostics_continuous=continuous,
        stationary=stationary,
        search_status=status,
        search_evaluations=search.count,
        diagnostic_evaluations=diagnostic_count,
        global_ambiguity="not_inferred" if known else "unresolved",
    )


def fit_exposure_phases(
    images: Any,
    *,
    order_kernels: Any,
    kernel_origin_zyx: Any,
    source_shape_zyx: Any,
    detector_crop_zyx: Any,
    source_spacing_um_zyx: Any,
    carrier_per_um_yx: Any,
    exposure_covariance: Any,
    fit_mask: Any,
    phases_rad: Any,
    mode: Any,
    initial_offsets_rad: Any,
    offset_bounds_rad: Any,
    difference_step_rad: Any,
    source_rtol: Any,
    phase_rank_rtol: Any,
    gradient_tolerance: Any,
    max_evaluations: Any,
) -> ExposurePhaseFit:
    """Profile a finite shared source and locally fit supplied phase offsets.

    Geometry, kernels, covariance and the common spatial training mask are fixed.
    Phases are unwrapped radians in the supplied index-zero calibration gauge;
    spacing is in micrometres and carrier in cycles per micrometre. All starts
    and aliases remain visible. Local diagnostics establish no global uniqueness.
    """
    _require(type(mode) is str and mode in ("known", "common", "independent"), "invalid mode")
    data = _real(images, "images")
    _require(data.ndim == 4 and all(v > 0 for v in data.shape), "invalid images shape")
    n = data.shape[0]
    shape = _integer_triple(source_shape_zyx, "source shape")
    _require(all(v > 0 for v in shape), "invalid source shape")
    origin = _integer_triple(kernel_origin_zyx, "kernel origin")
    _require(
        type(order_kernels) is np.ndarray
        and order_kernels.dtype.kind == "c"
        and order_kernels.dtype.itemsize == 16
        and order_kernels.ndim == 4
        and order_kernels.shape[0] == 3
        and all(v > 0 for v in order_kernels.shape[1:]),
        "invalid order kernels",
    )
    _require(bool(np.all(np.isfinite(order_kernels))), "nonfinite order kernels")
    _require(bool(np.all(order_kernels[0].imag == 0)), "zero order must be real")
    kernels = np.array(order_kernels, dtype=np.complex128, order="C", copy=True)
    _require(
        all(0 <= o < k for o, k in zip(origin, kernels.shape[1:], strict=True)), "invalid origin"
    )
    crop = detector_crop_zyx
    _require(
        type(crop) is tuple
        and len(crop) == 3
        and all(type(v) is tuple and len(v) == 2 and all(type(i) is int for i in v) for v in crop),
        "invalid crop",
    )
    crop = cast(tuple[tuple[int, int], ...], crop)
    _require(all(0 <= a < b <= s for (a, b), s in zip(crop, shape, strict=True)), "invalid crop")
    _require(tuple(b - a for a, b in crop) == data.shape[1:], "crop/image shape mismatch")
    _require(
        type(source_spacing_um_zyx) is tuple
        and len(source_spacing_um_zyx) == 3
        and all(type(v) in (int, float) for v in source_spacing_um_zyx),
        "invalid spacing",
    )
    spacing = cast(
        tuple[float, float, float], tuple(_scalar(v, "spacing") for v in source_spacing_um_zyx)
    )
    _require(all(v > 0 for v in spacing), "invalid spacing")
    carrier = _real(carrier_per_um_yx, "carrier")
    labels = _real(phases_rad, "phases")
    covariance = _real(exposure_covariance, "covariance")
    _require(carrier.shape == (2,) and labels.shape == (n,), "invalid carrier or phases shape")
    _require(covariance.shape == (n, n), "invalid covariance shape")
    _require(bool(np.array_equal(covariance, covariance.T)), "asymmetric covariance")
    try:
        with _arithmetic():
            cholesky = np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as error:
        raise SimreconError(_INPUT, "covariance is not numerically positive definite") from error
    _finite(cholesky)
    _require(bool(np.all(np.diag(cholesky) > 0)), "invalid covariance factor")
    _require(
        type(fit_mask) is np.ndarray
        and fit_mask.dtype == np.dtype(bool)
        and fit_mask.shape == data.shape[1:],
        "invalid fit mask",
    )
    mask = fit_mask.copy(order="C")
    q = 0 if mode == "known" else 1 if mode == "common" else n
    starts = _real(initial_offsets_rad, "starts")
    bounds = _real(offset_bounds_rad, "bounds")
    steps = _real(difference_step_rad, "steps")
    _require(starts.ndim == 2 and starts.shape[0] >= 1 and starts.shape[1] == q, "invalid starts")
    _require(mode != "known" or starts.shape[0] == 1, "known mode requires one start")
    _require(bounds.shape == (2, q) and steps.shape == (q,), "invalid bounds or steps shape")
    _require(bool(np.all(bounds[0] <= bounds[1])), "reversed bounds")
    _require(bool(np.all((starts >= bounds[0]) & (starts <= bounds[1]))), "start outside bounds")
    _require(bool(np.all(steps > 0)), "nonpositive steps")
    axes = bounds[0] < bounds[1]
    # Overflow here only means the supplied step reaches past a finite endpoint.
    with np.errstate(over="ignore", invalid="raise", under="ignore"):
        forward = np.minimum(bounds[0, axes] + steps[axes], bounds[1, axes])
        backward = np.maximum(bounds[1, axes] - steps[axes], bounds[0, axes])
    _require(
        bool(np.all(forward > bounds[0, axes]) and np.all(backward < bounds[1, axes])),
        "unrepresentable endpoint step",
    )
    source_cutoff = _scalar(source_rtol, "source rtol", rank=True)
    phase_cutoff = _scalar(phase_rank_rtol, "phase rtol", rank=True)
    gtol = _scalar(gradient_tolerance, "gradient tolerance")
    _require(
        isinstance(max_evaluations, (int, np.integer))
        and not isinstance(max_evaluations, (bool, np.bool_))
        and bool(max_evaluations > 0),
        "invalid evaluation budget",
    )
    with _arithmetic():
        operators, theta = _geometry(kernels, origin, shape, crop, spacing, carrier)
        profile = _Profile(operators, theta, data, labels, mode, mask, cholesky, source_cutoff)
        candidates = tuple(
            _candidate(
                profile,
                seed,
                bounds,
                steps,
                shape,
                data.shape,
                phase_cutoff,
                gtol,
                int(max_evaluations),
            )
            for seed in starts
        )
    return ExposurePhaseFit(
        mode=mode,
        input_phases_rad=_snapshot(labels),
        carrier_per_um_yx=(float(carrier[0]), float(carrier[1])),
        source_spacing_um_zyx=(spacing[0], spacing[1], spacing[2]),
        fit_mask=mask.copy(order="C"),
        candidates=candidates,
    )
