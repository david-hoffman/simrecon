"""Fit all volume exposure phases in a fixed complex calibration gauge."""

import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import numpy.typing as npt
from scipy.optimize import least_squares

from ._array_validation import require_finite
from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from .volume_reconstruction import _calibration, _container, _integer, _real_array, _real_scalar

Real = npt.NDArray[np.float64]
Complex = npt.NDArray[np.complex128]
_EPS = np.finfo(np.float64).eps
_SOLVER = "volume_phase_estimation_solver_failure"
_RANGE = "unrepresentable_volume_phase_estimation"


@dataclass(frozen=True)
class VolumePhaseEstimate:
    """Local fit with frozen bindings and independently owned mutable arrays.

    Attributes
    ----------
    phases_rad, phasors, phase_deviations_rad : numpy.ndarray
        Canonical exposure angles, represented phasors and wrapped deviations.
    specimen_normalized : numpy.ndarray
        Real signed nuisance specimen, in normalized observation/transfer units.
    image_scale, transfer_scale : float
        Common positive component scales of observations and transfers.
    relative_residual, normalized_residual_rms : float
        Profile residual norm relative to data and per spatial sample.
    normalized_imaginary_rms, calibration_reality_defect : float
        Imaginary prediction RMS and zero-order conjugate-symmetry defect.
    nuisance_rank, nuisance_singular_values : int, numpy.ndarray
        Numerical nuisance rank and its unregularized singular values.
    phase_rank, phase_singular_values : int, numpy.ndarray
        Rank and singular values of nuisance-projected phase information.
    phase_design_rank : int
        Rank of the separate represented five-column separation design.
    gradient_inf_norm : float
        Infinity norm of the complete profile objective gradient.
    termination : str
        Stationary, evaluation limit, stagnation or nuisance availability status.
    nfev, njev : int
        Observed residual and analytic Jacobian evaluation counts.
    carrier_bins_yx : tuple of int
        Original declared integer carrier, before modular indexing.
    source : str
        Unchanged opaque caller label.
    global_ambiguity : str
        Always unassessed; local stationarity establishes no global uniqueness.
    """

    phases_rad: Real
    phasors: Complex
    phase_deviations_rad: Real
    specimen_normalized: Real
    image_scale: float
    transfer_scale: float
    relative_residual: float
    normalized_residual_rms: float
    normalized_imaginary_rms: float
    calibration_reality_defect: float
    nuisance_rank: int
    nuisance_singular_values: Real
    phase_rank: int
    phase_singular_values: Real
    phase_design_rank: int
    gradient_inf_norm: float
    termination: str
    nfev: int
    njev: int
    carrier_bins_yx: tuple[int, int]
    source: str
    global_ambiguity: str


@contextmanager
def _dependency(code: str) -> Iterator[None]:
    """Isolate arithmetic failures at an actual numerical dependency boundary."""
    try:
        with (
            warnings.catch_warnings(),
            np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"),
        ):
            warnings.simplefilter("error", RuntimeWarning)
            yield
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical dependency failed") from error


def _finite(*values: Any, code: str = _RANGE) -> None:
    """Reject nonfinite computed coordinates without complex magnitude tests."""
    for value in values:
        require_finite(value, code, "nonfinite computed coordinates")


def _canonical(phases: Real) -> Real:
    """Canonicalize represented finite angles without rounded-period reduction."""
    result = np.arctan2(np.sin(phases), np.cos(phases))
    result[result == np.pi] = -np.pi
    return result


def _powers(phases: Real) -> Complex:
    """Construct signed powers in order -2,-1,0,1,2 with rounded squaring."""
    c, s = np.cos(phases), np.sin(phases)
    z = c + 1j * s
    second = (c * c - s * s) + 1j * ((2 * c) * s)
    return np.array([second.conj(), z.conj(), np.ones_like(z), z, second])


def _svd(matrix: Real) -> tuple[Real, Real, Real]:
    """Execute the real SVD and validate the numerical factors."""
    with _dependency(_SOLVER):
        left, singular, right = np.linalg.svd(matrix, full_matrices=False)
    _finite(left, singular, right, code=_SOLVER)
    return left, singular, right


def _rank(singular: Real, shape: tuple[int, int]) -> int:
    """Count singular values strictly above the selected relative cutoff."""
    return int(np.count_nonzero(singular > _EPS * max(shape) * singular[0]))


def _transform(values: Any, axes: tuple[int, ...]) -> Complex:
    """Apply the public unitary negative DFT and check its finite result."""
    code = "volume_phase_estimation_transform_failure"
    with _dependency(code):
        result = np.fft.fftn(values, axes=axes, norm="ortho")
    _finite(result, code=code)
    return result


@dataclass
class _Point:
    """Same-point nuisance fit, residual Jacobian and projected information."""

    specimen: Real
    residual: Real
    jacobian: Real
    information: Real
    singular: Real
    rank: int
    imaginary: Real


class _RankChanged(Exception):
    """Stop an optimizer before accepting an unavailable trial point."""


class _Profile:
    """Dense variable projection with a shared real spatial nuisance vector."""

    def __init__(self, operators: Complex, y: Real, n: int, size: int) -> None:
        self.operators = operators
        self.y = y
        self.n = n
        self.size = size
        self.dimension = operators.shape[-1]
        self.nfev = 0
        self.njev = 0
        self.require_full_rank = False
        self.cached_phases: Real | None = None
        self.cached_point: _Point | None = None

    def point(self, phases: Real) -> _Point:
        """Compute the profiled residual and both analytic derivative terms."""
        if self.cached_phases is not None and np.array_equal(phases, self.cached_phases):
            assert self.cached_point is not None
            return self.cached_point
        _finite(phases, code=_SOLVER)
        powers = _powers(phases)
        model = np.einsum("mp,mkj->pkj", powers, self.operators)
        derivative = np.einsum(
            "mp,mkj->pkj", (1j * np.arange(-2, 3))[:, None] * powers, self.operators
        )
        a = np.concatenate(
            (model.real.reshape(-1, self.dimension), model.imag.reshape(-1, self.dimension))
        )
        _finite(a, derivative)
        left, singular, right = _svd(a)
        rank = _rank(singular, a.shape)
        if self.require_full_rank and rank != self.dimension:
            raise _RankChanged
        plus = (right[:rank].T / singular[:rank]) @ left[:, :rank].T
        specimen = plus @ self.y
        prediction = a @ specimen
        residual = self.y - prediction
        # Each exposure phase changes only its own M complex observation rows.
        d_complex = derivative @ specimen
        d = np.zeros((2 * self.n * self.size, self.n))
        ap_r = np.empty((self.dimension, self.n))
        for p in range(self.n):
            real_rows = slice(p * self.size, (p + 1) * self.size)
            imag_rows = slice((self.n + p) * self.size, (self.n + p + 1) * self.size)
            d[real_rows, p] = d_complex[p].real
            d[imag_rows, p] = d_complex[p].imag
            ap_r[:, p] = (
                derivative[p].real.T @ residual[real_rows]
                + derivative[p].imag.T @ residual[imag_rows]
            )
        information = d - a @ (plus @ d)
        jacobian = -information - plus.T @ ap_r
        _finite(plus, specimen, prediction, residual, d, information, jacobian)
        point = _Point(
            specimen,
            residual,
            jacobian,
            information,
            singular,
            rank,
            prediction[self.n * self.size :],
        )
        self.cached_phases = phases.copy()
        self.cached_point = point
        return point

    def residual(self, phases: Real) -> Real:
        """Count actual residual evaluator entries, including interrupted trials."""
        self.nfev += 1
        return self.point(phases).residual

    def jacobian(self, phases: Real) -> Real:
        """Count actual analytic Jacobian evaluator entries."""
        self.njev += 1
        return self.point(phases).jacobian


def estimate_volume_phases(
    images: npt.NDArray[np.generic],
    *,
    order_otf: VolumeOrderOtf,
    carrier_bins_yx: tuple[int, int],
    initial_phases_rad: npt.NDArray[np.generic],
    max_nfev: int,
    gradient_tolerance: float,
    step_tolerance: float,
    source: str,
) -> VolumePhaseEstimate:
    """Estimate every exposure phase through a fixed-transfer local fit.

    Parameters
    ----------
    images : numpy.ndarray
        Plain finite real array with axes phase/z/y/x and at least five frames.
    order_otf : VolumeOrderOtf
        Full complex positive-order transfers in the fixed calibration gauge.
    carrier_bins_yx : tuple of int
        Declared integer lateral carrier; indexing is periodic on every axis.
    initial_phases_rad : numpy.ndarray
        Plain finite real initial commands, one per exposure, in radians.
    max_nfev : int
        Positive residual evaluation limit passed to SciPy's local solver.
    gradient_tolerance, step_tolerance : float
        Separate binary64 tolerances strictly between machine epsilon and one.
    source : str
        Nonblank opaque provenance label, retained without interpretation.

    Returns
    -------
    VolumePhaseEstimate
        Local phase fit and normalized diagnostics, or explicit nuisance-rank
        unavailability. Arrays are independently owned and mutable.

    Raises
    ------
    SimreconError
        For invalid inputs, handled numerical dependency failures or nonfinite
        computed results. Unrelated exceptions and allocation failures propagate.

    Notes
    -----
    Uses an unregularized real nuisance SVD and an analytic two-term profile
    Jacobian with scipy.optimize.least_squares (TRF). Stationarity is a local
    first-derivative condition, not a physical accuracy or uniqueness guarantee.
    Dense storage and factorization supply no scalable-volume promise. The
    supplied transfers already encode the calibration origin; it is not reapplied.
    """
    with np.errstate(all="ignore"):
        return _estimate(
            images,
            order_otf,
            carrier_bins_yx,
            initial_phases_rad,
            max_nfev,
            gradient_tolerance,
            step_tolerance,
            source,
        )


def _estimate(
    images: Any,
    order_otf: Any,
    carrier: Any,
    initial: Any,
    max_nfev: Any,
    gradient_tolerance: Any,
    step_tolerance: Any,
    source: Any,
    *,
    observable: bool = False,
) -> VolumePhaseEstimate:
    """Snapshot the public boundary, then execute the selected local procedure."""
    image_code = "invalid_volume_phase_estimation_images"
    if (
        type(images) is not np.ndarray
        or images.ndim != 4
        or images.shape[0] < 5
        or 0 in images.shape[1:]
    ):
        raise SimreconError(image_code, "images must have shape (N>=5,z>0,y>0,x>0)")
    values = _real_array(
        images, images.shape, image_code, "nonfinite_volume_phase_estimation_images"
    )
    n, nz, ny, nx = values.shape
    shape = (nz, ny, nx)
    size = nz * ny * nx
    angles = _real_array(
        initial,
        (n,),
        "invalid_volume_phase_estimation_initial_phases",
        "nonfinite_volume_phase_estimation_initial_phases",
    )
    try:
        transfers, _ = _calibration(order_otf, shape)
    except (SimreconError, AttributeError) as error:
        raise SimreconError("invalid_volume_phase_estimation_otf", "invalid calibration") from error
    carrier_code = "invalid_volume_phase_estimation_carrier"
    cy, cx = (_integer(v, carrier_code) for v in _container(carrier, 2, carrier_code))
    controls = "invalid_volume_phase_estimation_controls"
    limit = _integer(max_nfev, controls)
    gtol, xtol = (_real_scalar(v, controls) for v in (gradient_tolerance, step_tolerance))
    if limit < 1 or not (_EPS < gtol < 1 and _EPS < xtol < 1):
        raise SimreconError(controls, "invalid evaluation limit or tolerance")
    if not isinstance(source, str) or not source.strip():
        raise SimreconError("invalid_otf_source", "source must be a nonblank string")
    initial_angles = _canonical(angles)
    b = float(np.max(np.abs(values))) or 1.0
    t = max(float(np.max(np.abs(transfers.real))), float(np.max(np.abs(transfers.imag)))) or 1.0
    normalized = np.empty_like(transfers)
    normalized.real = transfers.real / t
    normalized.imag = transfers.imag / t
    # Work in uncentered Fourier row order; this is an orthogonal permutation
    # of the contract's centered real/imaginary stacking.
    f = np.fft.ifftshift(normalized, axes=(1, 2, 3))
    negative = np.ix_(*[(-np.arange(k)) % k for k in shape])
    signed = [f[2][negative].conj(), f[1][negative].conj(), f[0], f[1], f[2]]
    y_complex = _transform(values / b, (1, 2, 3))
    y = np.concatenate((y_complex.real.ravel(), y_complex.imag.ravel()))
    block_profile = None
    if observable:
        from ._fourier_block_phase import _BlockProfile

        block_profile = _BlockProfile(signed, (cy, cx), shape, y, n)
        profile = block_profile
        dimension = profile.dimension
    else:
        dimension = size
        basis = _transform(np.eye(size).reshape(*shape, size), (0, 1, 2))
        operators = np.array(
            [
                row.reshape(size, 1)
                * np.roll(basis, (m * (cy % ny), m * (cx % nx)), axis=(1, 2)).reshape(
                    size, dimension
                )
                for m, row in zip(range(-2, 3), signed, strict=True)
            ]
        )
        _finite(y, operators)
        profile = _Profile(operators, y, n, size)
    if dimension:
        profile.residual(initial_angles)
        profile.jacobian(initial_angles)
        first = profile.point(initial_angles)
    else:
        first = _Point(
            np.empty(0),
            y.copy(),
            np.zeros((2 * n * size, n)),
            np.zeros((2 * n * size, n)),
            np.empty(0),
            0,
            np.zeros(n * size),
        )
    result_angles, point = initial_angles, first
    if not dimension:
        termination = "no_observable_specimen"
    elif first.rank < dimension:
        termination = "nuisance_rank_deficient"
    else:
        profile.require_full_rank = True
        try:
            with _dependency(_SOLVER):
                # SciPy's inferred annotations omit callable jac and ftol=None.
                solved = cast(Any, least_squares)(
                    profile.residual,
                    initial_angles,
                    jac=profile.jacobian,
                    method="trf",
                    bounds=(-np.inf, np.inf),
                    loss="linear",
                    x_scale=1,
                    tr_solver="exact",
                    ftol=None,
                    gtol=gtol,
                    xtol=xtol,
                    max_nfev=limit,
                )
            if (
                not isinstance(solved.status, (int, np.integer))
                or not 0 <= solved.status <= 4
                or solved.x.shape != (n,)
            ):
                raise SimreconError(_SOLVER, "unusable optimizer result")
            _finite(
                solved.x,
                solved.fun,
                solved.jac,
                solved.grad,
                solved.cost,
                solved.optimality,
                code=_SOLVER,
            )
            result_angles = _canonical(solved.x)
            profile.cached_phases = None
            profile.residual(result_angles)
            profile.jacobian(result_angles)
            point = profile.point(result_angles)
            gradient = float(np.max(np.abs(point.jacobian.T @ point.residual)))
            _finite(gradient)
            termination = (
                "stationary"
                if gradient <= gtol
                else ("evaluation_limit" if solved.status == 0 else "stagnated")
            )
        except _RankChanged:
            result_angles, point = initial_angles, first
            termination = "rank_changed"
    phase_s = _svd(point.information)[1] if dimension else np.zeros(n)
    c, s = np.cos(result_angles), np.sin(result_angles)
    design = np.column_stack((np.ones(n), c, s, c * c - s * s, (2 * c) * s))
    _, design_s, _ = _svd(design)
    residual_norm = np.linalg.norm(point.residual)
    y_norm = np.linalg.norm(y)
    relative = float(residual_norm / y_norm) if np.any(y) else 0.0
    rms = float(residual_norm / np.sqrt(n * size))
    imaginary = float(np.linalg.norm(point.imaginary) / np.sqrt(n * size))
    reality = float(np.linalg.norm(f[0] - f[0][negative].conj()) / np.sqrt(size))
    gradient = float(np.max(np.abs(point.jacobian.T @ point.residual)))
    deviations = _canonical(result_angles - initial_angles)
    phasors = c + 1j * s
    _finite(relative, rms, imaginary, reality, gradient, phasors, deviations)
    specimen = block_profile.lift(point.specimen) if block_profile is not None else point.specimen
    _finite(specimen)
    fields = (
        result_angles.copy(order="C"),
        phasors.copy(order="C"),
        deviations.copy(order="C"),
        np.array(specimen.reshape(shape), dtype=np.float64, order="C", copy=True),
        b,
        t,
        relative,
        rms,
        imaginary,
        reality,
        point.rank,
        point.singular.copy(order="C"),
        _rank(phase_s, point.information.shape),
        phase_s.copy(order="C"),
        _rank(design_s, design.shape),
        gradient,
        termination,
        profile.nfev,
        profile.njev,
        (cy, cx),
        source,
        "unassessed",
    )
    if block_profile is not None:
        from ._observable_volume_phase_estimation import ObservableVolumePhaseEstimate

        return ObservableVolumePhaseEstimate(
            *fields,
            observable_fourier_mask=block_profile.mask.copy(order="C"),
            observable_dimension=dimension,
            unobservable_dimension=size - dimension,
        )
    return VolumePhaseEstimate(*fields)
