"""Fit continuous finite-window overlap with analytically profiled complex gains."""

import itertools
import math
import warnings
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
import numpy.typing as npt
from scipy.optimize import minimize

from ._array_validation import conversion_errors, require_finite
from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from .volume_reconstruction import _calibration, _integer, _real_array, _real_scalar

_Complex = npt.NDArray[np.complex128]
_Real = npt.NDArray[np.float64]
_Bins = npt.NDArray[np.intp]
_Carrier = tuple[float, float]
_RANGE = "unrepresentable_volume_overlap"
_NUMERICAL = "volume_overlap_numerical_failure"
_SEARCH = "invalid_volume_overlap_search"
_CONTROLS = "invalid_volume_overlap_controls"


@dataclass(frozen=True)
class VolumeOverlapCandidate:
    """One local attempt, with finite-step information and unresolved global ambiguity.

    Carriers use y/x cycles per micrometre. Objective secants and residual
    Jacobian singular values use reciprocal carrier units. Gains, normalized
    residuals and objective are dimensionless. Log norms retain the raw
    cross-weighted amplitude scales. Array contents remain mutable.
    """

    initial_carrier_per_um: _Carrier
    carrier_per_um: _Carrier
    gains: tuple[complex | None, ...]
    order_status: tuple[str, ...]
    coherence: tuple[float | None, ...]
    relative_residual: tuple[float | None, ...]
    objective: float
    projected_gradient: float
    stationary: bool
    information_singular_values: _Real
    information_rank: int
    status: str
    search_evaluations: int
    diagnostic_evaluations: int
    budget_exhausted: bool
    diagnostics_continuous: bool
    predictor_log2_norm: tuple[float | None, ...]
    response_log2_norm: tuple[float | None, ...]
    global_ambiguity: str


@dataclass(frozen=True)
class VolumeOverlapFit:
    """Caller-ordered attempts and owned fixed all-box overlap geometry.

    Spacing is z/y/x in micrometres; carrier bounds are y/x cycles per
    micrometre. Source is opaque calibration metadata. Arrays are independent
    mutable snapshots; field bindings are frozen.
    """

    candidates: tuple[VolumeOverlapCandidate, ...]
    overlap_bins: tuple[_Bins, _Bins]
    spacing_um: tuple[float, float, float]
    source: str
    carrier_bounds_per_um: _Real


@dataclass(frozen=True)
class _Order:
    gain: complex | None
    status: str
    coherence: float | None
    relative: float | None
    logx: float | None
    logy: float | None
    residual: _Complex

    @property
    def informative(self) -> bool:
        return self.status in ("fitted", "zero_correlation")


@dataclass(frozen=True)
class _Point:
    orders: tuple[_Order, _Order]
    residual: _Real
    objective: float

    @property
    def informative(self) -> tuple[bool, bool]:
        return self.orders[0].informative, self.orders[1].informative


def _finite(value: Any) -> None:
    require_finite(value, _RANGE, "computed components must be finite")


def _scale(values: _Complex) -> tuple[_Complex, int]:
    """Bound components by binary scaling, retaining even subnormal-only inputs."""
    maximum = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag))))
    exponent = math.frexp(maximum)[1] if maximum else 0
    scaled = np.empty(values.shape, dtype=np.complex128)
    np.ldexp(values.real, -exponent, out=scaled.real)
    np.ldexp(values.imag, -exponent, out=scaled.imag)
    return scaled, exponent


def _fourier(values: _Complex) -> _Complex:
    """Evaluate the normalized finite sum on the native integer grid."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            result = np.fft.fftshift(np.fft.fftn(values, axes=(0, 1, 2), norm="forward"))
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(_NUMERICAL, "finite Fourier evaluation failed") from error
    require_finite(result, _NUMERICAL, "Fourier evaluation returned nonfinite components")
    return result


def _unit_product(left: _Complex, right: _Complex) -> tuple[_Complex, float, int]:
    """Normalize a cross-weighted vector without restoring its raw amplitude."""
    a, ea = _scale(left)
    b, eb = _scale(right)
    product, ep = _scale(a * b)
    length = float(np.sqrt(np.sum(product.real**2 + product.imag**2)))
    _finite(length)
    unit = product if length == 0 else product / length
    _finite(unit)
    return unit, length, ea + eb + ep


def _norm(values: _Complex) -> float:
    """Measure a residual without squaring its unscaled small components."""
    scaled, exponent = _scale(values)
    length = float(np.sqrt(np.sum(scaled.real**2 + scaled.imag**2)))
    try:
        result = math.ldexp(length, exponent)
    except OverflowError as error:
        raise SimreconError(_RANGE, "residual norm overflows") from error
    _finite(result)
    return result


def _gain_component(component: float, nx: float, ny: float, exponent: int) -> float:
    """Restore each gain component after including its correlation factor."""
    mantissa, power = math.frexp(component)
    x, px = math.frexp(nx)
    y, py = math.frexp(ny)
    try:
        value = math.ldexp(mantissa * y / x, exponent + power + py - px)
    except OverflowError as error:
        raise SimreconError(_RANGE, "restored gain component overflows") from error
    _finite(value)
    return value


def _overlap(
    shape: tuple[int, int, int], fields: tuple[Fraction, Fraction], bounds: _Real, order: int
) -> _Bins:
    """Form every native bin inside the translated hull for the entire box."""
    ranges = [range(-(shape[0] // 2), (shape[0] + 1) // 2)]
    for axis, field in enumerate(fields):
        length = shape[axis + 1]
        lower, upper = -(length // 2), (length - 1) // 2
        first = max(lower, math.ceil(lower - order * field * Fraction(float(bounds[0, axis]))))
        last = min(upper, math.floor(upper - order * field * Fraction(float(bounds[1, axis]))))
        ranges.append(range(first, last + 1))
    count = math.prod(len(r) for r in ranges)
    result = np.empty((count, 3), dtype=np.intp)
    for index, q in enumerate(itertools.product(*ranges)):
        result[index] = q
    return result


def _interpolate(values: _Complex, bins: _Bins, shift: tuple[Fraction, Fraction]) -> _Complex:
    """Sample Cartesian complex linear transfer values at exact ideal nodes."""
    choices = []
    for delta in shift:
        lower = math.floor(delta)
        fraction = delta - lower
        choices.append(
            [(lower, 1.0)]
            if not fraction
            else [(lower, float(1 - fraction)), (lower + 1, float(fraction))]
        )
    z, y, x = (bins[:, a] + values.shape[a] // 2 for a in range(3))
    sampled = np.zeros(len(bins), dtype=np.complex128)
    for (dy, wy), (dx, wx) in itertools.product(*choices):
        corner = values[z, y + dy, x + dx]
        weight = wy * wx
        sampled.real += weight * corner.real
        sampled.imag += weight * corner.imag
    _finite(sampled)
    return sampled


def _ramp(shape: tuple[int, int, int], shift: tuple[Fraction, Fraction]) -> _Complex:
    """Reduce exact cycles before evaluating the index-zero demodulation ramp."""
    _, ny, nx = shape
    # Separable bounded phases avoid both large arguments and a spatial-size
    # array of rational objects. Integer cycles are removed before conversion.
    vectors = []
    for length, delta in zip((ny, nx), shift, strict=True):
        angles = np.array([-math.tau * float((delta * n / length) % 1) for n in range(length)])
        vector = np.empty(length, dtype=np.complex128)
        np.cos(angles, out=vector.real)
        np.sin(angles, out=vector.imag)
        vectors.append(vector)
    return vectors[0][:, None] * vectors[1][None, :]


def _regression(x: _Complex, nx: float, ex: int, y: _Complex, ny: float, ey: int) -> _Order:
    """Use the same unit-vector regression for gains and the search residual."""
    r = np.zeros(x.size + 1, dtype=np.complex128)
    logx = math.log2(nx) + ex if nx else None
    logy = math.log2(ny) + ey if ny else None
    if not nx or not ny:
        r[-1] = 1
        status = "zero_predictor" if not nx else "zero_response"
        return _Order(0j if nx else None, status, None, None, logx, logy, r)
    # Separate real products preserve cancellation of equal represented terms;
    # a fused complex multiply/dot can leave a spurious orthogonal component.
    h = complex(
        math.fsum(x.real * y.real + x.imag * y.imag),
        math.fsum(x.real * y.imag - x.imag * y.real),
    )
    _finite(h)
    gain = complex(
        _gain_component(h.real, nx, ny, ey - ex),
        _gain_component(h.imag, nx, ny, ey - ex),
    )
    r[:-1] = y - h * x
    relative = 1.0 if h == 0j else _norm(r)
    coherence = abs(h)
    _finite(r)
    _finite(relative)
    _finite(coherence)
    return _Order(
        gain, "zero_correlation" if h == 0j else "fitted", coherence, relative, logx, logy, r
    )


class _Estimator:
    """Retain fixed geometry and scaled snapshots for one finite objective."""

    def __init__(
        self,
        bands: _Complex,
        transfers: _Complex,
        spacing: tuple[float, float, float],
        bounds: _Real,
    ) -> None:
        self.shape = (bands.shape[1], bands.shape[2], bands.shape[3])
        self.fields = (
            self.shape[1] * Fraction(spacing[1]),
            self.shape[2] * Fraction(spacing[2]),
        )
        self.bands = tuple(_scale(row) for row in bands)
        self.transfers = tuple(_scale(row) for row in transfers)
        self.q = (
            _overlap(self.shape, self.fields, bounds, 1),
            _overlap(self.shape, self.fields, bounds, 2),
        )
        self.dc = _fourier(self.bands[0][0]) if any(len(q) for q in self.q) else None

    def evaluate(self, carrier: _Carrier) -> _Point:
        """Evaluate both positive orders with fixed support and profiled gains."""
        orders = []
        for m, q in enumerate(self.q, 1):
            if not len(q):
                orders.append(
                    _Order(
                        None, "no_overlap", None, None, None, None, np.ones(1, dtype=np.complex128)
                    )
                )
                continue
            assert self.dc is not None
            shift = (
                m * self.fields[0] * Fraction(carrier[0]),
                m * self.fields[1] * Fraction(carrier[1]),
            )
            indices = tuple(q[:, a] + self.shape[a] // 2 for a in range(3))
            # Dm(q+shift) is the finite transform of the spatial band times
            # exp(-2*pi*i*shift.n/K), evaluated at integer q. It is never
            # interpolation of stored FFT coefficients.
            dm = _fourier(self.bands[m][0] * _ramp(self.shape, shift))[indices]
            em = _interpolate(self.transfers[m][0], q, shift)
            x, nx, ex = _unit_product(em, self.dc[indices])
            y, ny, ey = _unit_product(self.transfers[0][0][indices], dm)
            ex += self.transfers[m][1] + self.bands[0][1]
            ey += self.transfers[0][1] + self.bands[m][1]
            orders.append(_regression(x, nx, ex, y, ny, ey))
        residual = np.concatenate(
            [v for order in orders for v in (order.residual.real, order.residual.imag)]
        )
        objective = float(np.dot(residual, residual))
        _finite(objective)
        return _Point((orders[0], orders[1]), residual, objective)


def _neighbor(value: float, bound: float, step: float) -> tuple[float, float]:
    """Return a clipped representable neighbor and its actual positive distance."""
    distance = min(Fraction(step), abs(Fraction(bound) - Fraction(value)))
    sign = 1 if bound > value else -1
    neighbor = float(Fraction(value) + sign * distance)
    try:
        actual = float(abs(Fraction(neighbor) - Fraction(value)))
    except OverflowError:
        actual = math.inf
    return neighbor, actual


def _inputs(
    bands: Any, starts: Any, bounds: Any, step: Any, gtol: object, rtol: object, budget: object
) -> tuple[_Complex, _Real, _Real, _Real, float, float, int]:
    """Snapshot every declared observation and search input before numerics."""
    code = "invalid_volume_overlap_bands"
    if (
        type(bands) is not np.ndarray
        or bands.dtype.kind != "c"
        or bands.dtype.itemsize != 16
        or bands.ndim != 4
        or bands.shape[0] != 3
        or 0 in bands.shape[1:]
    ):
        raise SimreconError(code, "bands must be a plain complex128 (3,Z,Y,X) ndarray")
    require_finite(bands, code, "band components must be finite")
    if np.any(bands[0].imag != 0):
        raise SimreconError(code, "dc must have exactly zero imaginary components")
    with conversion_errors(code, "band conversion failed"):
        observed = bands.astype(np.complex128, order="C", copy=True)
    if type(starts) is not np.ndarray or starts.ndim != 2 or starts.shape[0] < 1:
        raise SimreconError(_SEARCH, "starts must have shape (T>=1,2)")
    seeds = _real_array(starts, (starts.shape[0], 2), _SEARCH, _SEARCH)
    box = _real_array(bounds, (2, 2), _SEARCH, _SEARCH)
    if np.any(box[0] > box[1]) or np.any(seeds < box[0]) or np.any(seeds > box[1]):
        raise SimreconError(_SEARCH, "starts must lie in a closed ordered box")
    steps = _real_array(step, (2,), _CONTROLS, _CONTROLS)
    gradient = _real_scalar(gtol, _CONTROLS)
    rank = _real_scalar(rtol, _CONTROLS)
    limit = _integer(budget, _CONTROLS)
    if np.any(steps <= 0) or gradient < 0 or not 0 < rank < 1 or limit <= 0:
        raise SimreconError(_CONTROLS, "invalid step, tolerance or evaluation budget")
    for a in range(2):
        lo, hi = float(box[0, a]), float(box[1, a])
        if lo == hi:
            continue
        for endpoint, other in ((lo, hi), (hi, lo)):
            _, distance = _neighbor(endpoint, other, float(steps[a]))
            if not math.isfinite(distance) or distance <= 0:
                raise SimreconError(_CONTROLS, "step must move finitely from both endpoints")
    return observed, seeds, box, steps, gradient, rank, limit


class _BudgetStop(Exception):
    """Terminate local search before another uncached objective evaluation."""


class _Attempt:
    """Account search points separately from fixed final diagnostic points."""

    def __init__(self, estimator: _Estimator, seed: _Carrier, budget: int) -> None:
        self.estimator = estimator
        self.budget = budget
        self.cache: dict[_Carrier, _Point] = {}
        self.best = seed
        self.search_evaluations = 0
        self.diagnostic_evaluations = 0
        self.search(seed)

    def search(self, carrier: _Carrier) -> _Point:
        """Retain the first exact objective tie and enforce the caller budget."""
        if carrier in self.cache:
            return self.cache[carrier]
        if self.search_evaluations >= self.budget:
            raise _BudgetStop
        point = self.estimator.evaluate(carrier)
        self.search_evaluations += 1
        if not self.cache or point.objective < self.cache[self.best].objective:
            self.best = carrier
        self.cache[carrier] = point
        return point

    def diagnostic(self, carrier: _Carrier) -> _Point:
        """Count only fresh objective evaluations used for diagnostics."""
        if carrier not in self.cache:
            self.cache[carrier] = self.estimator.evaluate(carrier)
            self.diagnostic_evaluations += 1
        return self.cache[carrier]

    def minimize(self, seed: _Carrier, bounds: _Real) -> None:
        """Run one bounded simplex attempt in dimensionless box coordinates."""
        axes = [a for a in range(2) if bounds[0, a] < bounds[1, a]]
        if not axes or self.search_evaluations == self.budget:
            return
        lower = [Fraction(float(bounds[0, a])) for a in axes]
        widths = [Fraction(float(bounds[1, a])) - lo for a, lo in zip(axes, lower, strict=True)]
        initial = np.array(
            [
                float((Fraction(seed[a]) - lo) / width)
                for a, lo, width in zip(axes, lower, widths, strict=True)
            ]
        )
        simplex = np.tile(initial, (len(axes) + 1, 1))
        for j in range(len(axes)):
            simplex[j + 1, j] += 0.05 if initial[j] <= 0.5 else -0.05

        def objective(coordinates: _Real) -> float:
            require_finite(coordinates, _NUMERICAL, "optimizer returned nonfinite coordinates")
            # The normalized seed maps to its exact supplied value, rather than
            # a second rounded round-trip through dimensionless coordinates.
            carrier = list(seed)
            for j, a in enumerate(axes):
                x = float(coordinates[j])
                if not 0 <= x <= 1:
                    raise SimreconError(_NUMERICAL, "optimizer left its declared bounds")
                carrier[a] = (
                    seed[a] if x == initial[j] else float(lower[j] + Fraction(x) * widths[j])
                )
            return self.search((carrier[0], carrier[1])).objective

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                minimize(
                    objective,
                    initial,
                    method="Nelder-Mead",
                    bounds=[(0.0, 1.0)] * len(axes),
                    options={
                        "initial_simplex": simplex,
                        "maxfev": self.budget + 1,
                        "maxiter": self.budget,
                        "xatol": 1e-9,
                        "fatol": 1e-12,
                    },
                )
        except _BudgetStop:
            pass
        except (FloatingPointError, OverflowError, RuntimeWarning, np.linalg.LinAlgError) as error:
            raise SimreconError(_NUMERICAL, "local optimizer failed numerically") from error


def _diagnostics(
    attempt: _Attempt, bounds: _Real, step: _Real, rank_rtol: float
) -> tuple[float, _Real, int, bool]:
    """Compute clipped objective secants and the profiled real residual Jacobian."""
    carrier = attempt.best
    center = attempt.cache[carrier]
    gradient = 0.0
    continuous = True
    columns = []
    for a in range(2):
        sides = []
        for bound in bounds[:, a]:
            neighbor, distance = _neighbor(carrier[a], float(bound), float(step[a]))
            point = center
            if distance > 0:
                _finite(distance)
                k = list(carrier)
                k[a] = neighbor
                point = attempt.diagnostic((k[0], k[1]))
                continuous &= point.informative == center.informative
                secant = (center.objective - point.objective) / distance
                _finite(secant)
                gradient = max(gradient, secant)
            sides.append((distance, point))
        (dm, minus), (dp, plus) = sides
        scale = max(dm, dp)
        # A scaled denominator also handles a total two-sided displacement
        # larger than binary64 range without manufacturing a zero derivative.
        column = (
            ((plus.residual - minus.residual) / scale) / (dm / scale + dp / scale)
            if scale
            else np.zeros_like(center.residual)
        )
        _finite(column)
        columns.append(column)
    jacobian = np.column_stack(columns)
    maximum = float(np.max(np.abs(jacobian)))
    singular = np.zeros(2, dtype=np.float64)
    if maximum:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                scaled = np.linalg.svd(jacobian / maximum, compute_uv=False)
        except (FloatingPointError, OverflowError, RuntimeWarning, np.linalg.LinAlgError) as error:
            raise SimreconError(_NUMERICAL, "residual Jacobian factorization failed") from error
        require_finite(scaled, _NUMERICAL, "factorization returned nonfinite singular values")
        singular[: len(scaled)] = scaled * maximum
        _finite(singular)
    rank = int(np.count_nonzero(singular > rank_rtol * singular[0])) if singular[0] else 0
    return gradient, singular, rank, continuous


def fit_volume_overlap(
    bands: npt.NDArray[Any],
    *,
    order_otf: VolumeOrderOtf,
    initial_carriers_per_um: npt.NDArray[Any],
    carrier_bounds_per_um: npt.NDArray[Any],
    difference_step_per_um: npt.NDArray[Any],
    gradient_tolerance: object,
    rank_rtol: object,
    max_evaluations: object,
) -> VolumeOverlapFit:
    """Fit one orientation's carriers and relative complex positive-order gains.

    Parameters
    ----------
    bands : numpy.ndarray
        Spatial dc,c1,c2, plain finite complex128 (3,Z,Y,X), with real dc.
    order_otf : VolumeOrderOtf
        Fixed, fully validated complex calibration on the native detector grid.
    initial_carriers_per_um : numpy.ndarray
        Caller-ordered real starts (T,2), y/x cycles per micrometre.
    carrier_bounds_per_um : numpy.ndarray
        Closed search box (2,2), lower row then upper row, same carrier units.
    difference_step_per_um : numpy.ndarray
        Positive y/x secant distances (2,), in cycles per micrometre.
    gradient_tolerance : real scalar
        Nonnegative tolerance on negative feasible objective secants.
    rank_rtol : real scalar
        Strict relative singular-value cutoff between zero and one.
    max_evaluations : integer
        Positive objective evaluation budget for each local attempt.

    Returns
    -------
    VolumeOverlapFit
        Every local attempt and fixed all-box overlap, without winner selection.

    Raises
    ------
    SimreconError
        For invalid input, unrepresentable arithmetic or handled numerical
        dependency failure. Unrelated exceptions and MemoryError propagate.

    Notes
    -----
    A bounded spatial demodulation followed by a normalized Fourier transform
    evaluates the finite observation polynomial. Only the complex transfer is
    linearly interpolated. Both gains are profiled in the shared sum of unit
    residual energies. Unavailable orders contribute marker penalties of one.
    Final secants and residual singular values describe finite local changes;
    they prove neither physical recovery, noise confidence nor global uniqueness.
    """
    with np.errstate(all="ignore"):
        observed, starts, bounds, step, gtol, rtol, budget = _inputs(
            bands,
            initial_carriers_per_um,
            carrier_bounds_per_um,
            difference_step_per_um,
            gradient_tolerance,
            rank_rtol,
            max_evaluations,
        )
        shape = (observed.shape[1], observed.shape[2], observed.shape[3])
        transfers, spacing = _calibration(order_otf, shape)
        source = order_otf.source
        estimator = _Estimator(observed, transfers, spacing, bounds)
        candidates = []
        free = int(np.count_nonzero(bounds[1] > bounds[0]))
        for row in starts:
            seed = (float(row[0]), float(row[1]))
            attempt = _Attempt(estimator, seed, budget)
            attempt.minimize(seed, bounds)
            point = attempt.cache[attempt.best]
            gradient, singular, rank, continuous = _diagnostics(attempt, bounds, step, rtol)
            stationary = bool(continuous and gradient <= gtol)
            exhausted = attempt.search_evaluations >= budget
            status = (
                "unavailable"
                if not any(point.informative)
                else "nonsmooth_diagnostics"
                if not continuous
                else "information_deficient"
                if rank < free
                else "finite_difference_stationary"
                if stationary
                else "evaluation_limit"
                if exhausted
                else "search_stopped"
            )
            candidates.append(
                VolumeOverlapCandidate(
                    seed,
                    attempt.best,
                    tuple(o.gain for o in point.orders),
                    tuple(o.status for o in point.orders),
                    tuple(o.coherence for o in point.orders),
                    tuple(o.relative for o in point.orders),
                    point.objective,
                    gradient,
                    stationary,
                    singular,
                    rank,
                    status,
                    attempt.search_evaluations,
                    attempt.diagnostic_evaluations,
                    exhausted,
                    continuous,
                    tuple(o.logx for o in point.orders),
                    tuple(o.logy for o in point.orders),
                    "unresolved",
                )
            )
    return VolumeOverlapFit(tuple(candidates), estimator.q, spacing, source, bounds)
