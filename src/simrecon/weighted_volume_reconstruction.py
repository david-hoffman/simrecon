"""Covariance-weighted inversion of the declared real volume observation map."""

import warnings
from collections.abc import Callable
from dataclasses import dataclass
from fractions import Fraction
from math import prod, sqrt
from typing import Any

import numpy as np
import numpy.typing as npt

from ._model import SimreconError
from ._volume_order_otf import VolumeOrderOtf
from .volume_reconstruction import (
    _calibration,
    _container,
    _frequencies,
    _integer,
    _real_array,
    _real_scalar,
)

_RANGE = "unrepresentable_weighted_volume_reconstruction"
_SOLVER = "weighted_volume_solver_failure"
_COVARIANCE = "invalid_weighted_volume_covariance"
_SINGULAR = "singular_weighted_volume_covariance"
_OTFS = "invalid_volume_reconstruction_otfs"
_GRID = "unrepresentable_volume_reconstruction_grid"

Real = npt.NDArray[np.float64]
Complex = npt.NDArray[np.complex128]


@dataclass(frozen=True)
class WeightedReconstruction3D:
    """Real inverse and raw-objective diagnostics, followed by a spectral taper.

    Arrays own independent mutable native storage. Bindings are frozen; direct
    construction does not validate. Spatial arrays use z/y/x, frequencies use
    cycles per micrometre, and voxel spacings use micrometres. Separated real
    coordinates are dc, Re c1, Im c1, Re c2, Im c2. Covariance is in squared
    input-intensity units. Predictions and objectives describe the untapered
    estimate; the tapered volume can be complex.
    """

    volume: Complex
    spectrum: Complex
    untapered_volume: Real
    untapered_spectrum: Complex
    separated_coordinates: Real
    separated_covariance: Real
    predicted_images: Real
    residual_images: Real
    data_objective: float
    penalty_objective: float
    information_rank: int
    unknown_count: int
    fz_per_um: Real
    fy_per_um: Real
    fx_per_um: Real
    voxel_size_um: tuple[float, float, float]


@dataclass
class _Inputs:
    observed: Real
    phases: Real
    gains: Real
    carriers: list[tuple[int, int]]
    transfers: list[Complex]
    covariance: Real
    alpha: float
    taper: Real
    output: tuple[int, int, int]
    spacing: tuple[float, float, float]
    frequencies: tuple[Real, Real, Real]


def _snapshot(
    images: Any,
    order_otfs: Any,
    phases_rad: Any,
    carriers_bins: Any,
    gains: Any,
    exposure_covariance: Any,
    regularization: object,
    output_shape_yx: object,
    apodization: Any,
) -> _Inputs:
    """Validate and copy every field before any trigonometry or inverse work."""
    if type(images) is not np.ndarray:
        raise SimreconError("invalid_volume_reconstruction_images", "plain ndarray required")
    if images.dtype.kind not in "iuf":
        raise SimreconError("invalid_volume_reconstruction_dtype", "real dtype required")
    if images.ndim != 5 or images.shape[0] < 1 or images.shape[1] < 5 or 0 in images.shape[2:]:
        raise SimreconError("invalid_volume_reconstruction_shape", "invalid acquisition shape")
    r_count, n, nz, ny, nx = images.shape
    detector = (nz, ny, nx)
    observed = _real_array(
        images,
        images.shape,
        "invalid_volume_reconstruction_dtype",
        "nonfinite_volume_reconstruction_images",
    )
    phases = _real_array(
        phases_rad,
        (r_count, n),
        "invalid_volume_reconstruction_phases",
        "nonfinite_volume_reconstruction_phases",
    )
    gain = _real_array(
        gains,
        (r_count,),
        "invalid_volume_reconstruction_gains",
        "invalid_volume_reconstruction_gain_values",
    )
    if np.any(gain <= 0):
        raise SimreconError("invalid_volume_reconstruction_gain_values", "positive gains required")
    carrier_code = "invalid_volume_reconstruction_carriers"
    if (
        type(carriers_bins) is not np.ndarray
        or carriers_bins.dtype.kind not in "iu"
        or carriers_bins.shape != (r_count, 2)
    ):
        raise SimreconError(carrier_code, "integer ndarray (R,2) required")
    carriers = [(int(y), int(x)) for y, x in carriers_bins.copy()]
    shape_code = "invalid_volume_reconstruction_output_shape"
    ly, lx = (_integer(v, shape_code) for v in _container(output_shape_yx, 2, shape_code))
    if any(v <= 0 or v > np.iinfo(np.intp).max for v in (ly, lx)):
        raise SimreconError(shape_code, "positive native-index dimensions required")
    if ly < ny + 4 * max(abs(y) for y, _ in carriers) or lx < nx + 4 * max(
        abs(x) for _, x in carriers
    ):
        raise SimreconError(shape_code, "output must retain every signed band")
    output = (nz, ly, lx)
    penalty_code = "invalid_volume_reconstruction_regularization"
    alpha = _real_scalar(regularization, penalty_code)
    if alpha < 0:
        raise SimreconError(penalty_code, "nonnegative regularization required")
    mask_code = "invalid_volume_reconstruction_apodization_values"
    taper = _real_array(apodization, output, "invalid_volume_reconstruction_apodization", mask_code)
    if np.any(apodization < 0) or np.any(apodization > 1) or np.any(taper < 0) or np.any(taper > 1):
        raise SimreconError(mask_code, "source and converted taper must lie in [0,1]")
    calibrations = [
        _calibration(record, detector) for record in _container(order_otfs, r_count, _OTFS)
    ]
    spacing = calibrations[0][1]
    if any(d != spacing for _, d in calibrations):
        raise SimreconError(_OTFS, "converted voxel spacings must agree")
    out_spacing = tuple(
        float(Fraction(d) * k / length)
        for d, k, length in zip(spacing, detector, output, strict=True)
    )
    if any(not np.isfinite(d) or d <= 0 for d in out_spacing):
        raise SimreconError(_GRID, "output spacing must be finite and positive")
    fz, fy, fx = (
        _frequencies(length, k, d) for length, k, d in zip(output, detector, spacing, strict=True)
    )
    covariance = _real_array(exposure_covariance, (r_count, n, n), _COVARIANCE, _COVARIANCE)
    return _Inputs(
        observed,
        phases,
        gain,
        carriers,
        [v for v, _ in calibrations],
        covariance,
        alpha,
        taper,
        output,
        (out_spacing[0], out_spacing[1], out_spacing[2]),
        (fz, fy, fx),
    )


def _finite(value: Any, code: str = _RANGE) -> None:
    """Check components rather than a potentially overflowing complex magnitude."""
    if not np.isfinite(value).all():
        raise SimreconError(code, "nonfinite numerical stage")


def _factor(
    operation: Callable[[], Any], code: str = _SOLVER, *, nonfinite_code: str | None = None
) -> Any:
    """Translate failures only around the requested numerical factorization."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            result = operation()
    except (np.linalg.LinAlgError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical factorization failed") from error
    for value in result if isinstance(result, tuple) else (result,):
        _finite(value, nonfinite_code or code)
    return result


def _scaled(values: Real | Complex) -> tuple[Any, int]:
    """Use binary component scaling, including for subnormal-only inputs."""
    maximum = max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag))))
    exponent = int(np.frexp(maximum)[1]) if maximum else 0
    if np.iscomplexobj(values):
        scaled = np.empty(values.shape, dtype=np.complex128)
        scaled.real = np.ldexp(values.real, -exponent)
        scaled.imag = np.ldexp(values.imag, -exponent)
    else:
        scaled = np.ldexp(values, -exponent)
    return scaled, exponent


def _transform(values: Real | Complex, *, inverse: bool = False) -> Complex:
    """Transform safely scaled components, then restore the Fourier-series units."""
    scaled, exponent = _scaled(values)
    code = "volume_reconstruction_transform_failure"
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            if inverse:
                transformed = np.fft.ifftn(np.fft.ifftshift(scaled), norm="forward")
            else:
                transformed = np.fft.fftshift(np.fft.fftn(scaled, norm="forward"))
    except (FloatingPointError, OverflowError, RuntimeWarning) as error:
        raise SimreconError(code, "numerical transform failed") from error
    _finite(transformed, code)
    result = np.empty(values.shape, dtype=np.complex128)
    result.real = np.ldexp(transformed.real, exponent)
    result.imag = np.ldexp(transformed.imag, exponent)
    _finite(result)
    return result


def _apply(matrix: Real, values: Real) -> Real:
    """Apply a real map without an avoidable unscaled observation-sum overflow."""
    scaled, exponent = _scaled(values)
    result = np.ldexp(matrix @ scaled, exponent)
    _finite(result)
    return result


def _phase_design(phases: Real) -> Real:
    """Retain the prerequisite represented basis and its unscaled rank cutoff."""
    c, s = np.cos(phases), np.sin(phases)
    h = np.column_stack((np.ones(phases.size), c, s, c * c - s * s, (2 * c) * s))
    _, singular, _ = _factor(
        lambda: np.linalg.svd(h, full_matrices=False), "volume_phase_solver_failure"
    )
    cutoff = np.finfo(float).eps * max(phases.size, 5) * singular[0]
    if np.count_nonzero(singular > cutoff) < 5:
        raise SimreconError("rank_deficient_volume_phases", "phase rank is below five")
    return h * np.array([1.0, 2.0, -2.0, 2.0, -2.0])


def _whitener(covariance: Real) -> Real:
    """Validate the normalized eigenvalue boundary and factor the full covariance."""
    scale = float(np.max(np.abs(covariance)))
    if scale == 0 or not np.array_equal(covariance, covariance.T):
        raise SimreconError(_SINGULAR, "covariance must be symmetric positive definite")
    normalized = covariance / scale
    eigenvalues = _factor(lambda: np.linalg.eigvalsh(normalized), nonfinite_code=_SINGULAR)
    threshold = np.finfo(float).eps * len(covariance) * eigenvalues[-1]
    if not eigenvalues[0] > threshold > 0:
        raise SimreconError(_SINGULAR, "covariance is not numerically positive definite")
    lower = _factor(lambda: np.linalg.cholesky(normalized))
    whiten = _factor(lambda: np.linalg.solve(lower, np.eye(len(covariance)))) / sqrt(scale)
    _finite(whiten)
    return whiten


def _separate(k: Real, whiten: Real, observed: Real) -> tuple[Real, Real]:
    """Compute GLS with a whitened SVD, retaining every covariance entry."""
    u, singular, vh = _factor(lambda: np.linalg.svd(whiten @ k, full_matrices=False))
    if np.any(singular <= 0):
        raise SimreconError(_SOLVER, "unusable GLS singular values")
    inverse = vh.T / singular
    _finite(inverse)
    covariance = inverse @ inverse.T
    _finite(covariance)
    # Apply to scaled observations before restoring intensity, so large raw
    # observations need not form a large unweighted intermediate fit.
    scaled, exponent = _scaled(observed)
    coordinates = np.ldexp(inverse @ (u.T @ (whiten @ scaled)), exponent)
    _finite(coordinates)
    return coordinates, covariance


def _real_map(inputs: _Inputs, designs: list[Real]) -> Real:
    """Build columns by applying calibrated Fourier optics to real unit sources.

    Real and imaginary parts are taken only after native detector synthesis.
    Thus every negative-band dependency and self-conjugate endpoint is already
    included, without treating signed bands as independent observations.
    """
    r_count, n, nz, ny, nx = inputs.observed.shape
    m, p = nz * ny * nx, prod(inputs.output)
    maps = np.empty((r_count, n * m, p), dtype=np.float64)
    effective = [t * g for t, g in zip(inputs.transfers, inputs.gains, strict=True)]
    for transfer in effective:
        _finite(transfer)
    source = np.zeros(inputs.output, dtype=np.float64)
    for column in range(p):
        source.flat[column] = 1
        spectrum = _transform(source)
        source.flat[column] = 0
        for r, (cy, cx) in enumerate(inputs.carriers):
            coordinates = np.empty((5, m), dtype=np.float64)
            for order in range(3):
                y0 = inputs.output[1] // 2 - ny // 2 - order * cy
                x0 = inputs.output[2] // 2 - nx // 2 - order * cx
                detector_spectrum = effective[r][order] * spectrum[:, y0 : y0 + ny, x0 : x0 + nx]
                _finite(detector_spectrum)
                band = _transform(detector_spectrum, inverse=True).ravel()
                if order == 0:
                    coordinates[0] = band.real
                else:
                    coordinates[2 * order - 1] = band.real
                    coordinates[2 * order] = band.imag
            maps[r, :, column] = (designs[r] @ coordinates).ravel()
    _finite(maps)
    return maps


def _inverse(b: Real, matrix: Real, alpha: float, p: int) -> tuple[Real, int]:
    """Solve in x/sqrt(P) coordinates with the declared cutoff and ridge modes."""
    u, singular, vh = _factor(lambda: np.linalg.svd(matrix, full_matrices=False))
    cutoff = np.finfo(float).eps * max(matrix.shape) * singular[0]
    retained = singular > cutoff
    rank = int(np.count_nonzero(retained))
    factors = np.zeros_like(singular)
    if alpha == 0:
        np.divide(1.0, singular, out=factors, where=retained)
    else:
        # hypot avoids both squaring overflow and a squared-singular underflow
        # that would otherwise lose small, positively regularized modes.
        denominator = np.hypot(singular, sqrt(alpha))
        factors = (singular / denominator) / denominator
    _finite(factors)
    scaled, exponent = _scaled(b)
    x = np.ldexp((vh.T @ (factors * (u.T @ scaled))) * sqrt(p), exponent)
    _finite(x)
    return x, rank


def _squared_norm(values: Real, weight: float = 1.0) -> float:
    """Accumulate a nonnegative diagnostic with component scaling before squares."""
    if weight == 0:
        return 0.0
    scaled, exponent = _scaled(values)
    norm = np.linalg.norm(scaled.ravel()) * sqrt(weight)
    # Restore to a norm before squaring, keeping representable subnormal squares.
    restored = np.ldexp(norm, exponent)
    result = float(restored * restored)
    _finite(result)
    return result


def reconstruct_volume_weighted(
    images: npt.NDArray[Any],
    *,
    order_otfs: tuple[VolumeOrderOtf, ...] | list[VolumeOrderOtf],
    phases_rad: npt.NDArray[Any],
    carriers_bins: npt.NDArray[Any],
    gains: npt.NDArray[Any],
    exposure_covariance: npt.NDArray[Any],
    regularization: object,
    output_shape_yx: object,
    apodization: npt.NDArray[Any],
) -> WeightedReconstruction3D:
    """Minimize the declared covariance-weighted real raw-data objective.

    Images have shape (R,N,z,y,x). Exposure covariance has shape (R,N,N)
    and is declared constant over independent detector voxels. Known phases,
    integer y/x carriers, positive gains and full complex order transfers define
    the real observation map. All keywords are required. Regularization is an
    explicit nonnegative source penalty in inverse squared intensity units.

    Zero regularization selects the numerical minimum-norm inverse; positive
    regularization retains all nonzero singular modes, including those below
    the reported information-rank cutoff. Tapering follows the inverse and
    never changes its raw predictions, residuals or objective diagnostics.

    This implementation uses a dense real observation matrix and stable SVD
    factorizations. It imposes no dimension cap and makes no scalability or
    undeclared-noise optimality promise. Invalid inputs and numerical failures
    raise SimreconError; allocation and unrelated backend exceptions propagate.
    """
    with np.errstate(all="ignore"):
        inputs = _snapshot(
            images,
            order_otfs,
            phases_rad,
            carriers_bins,
            gains,
            exposure_covariance,
            regularization,
            output_shape_yx,
            apodization,
        )
        r_count, n, nz, ny, nx = inputs.observed.shape
        m, p = nz * ny * nx, prod(inputs.output)
        designs = [_phase_design(phases) for phases in inputs.phases]
        whiteners = [_whitener(covariance) for covariance in inputs.covariance]
        coordinates = np.empty((r_count, 5, nz, ny, nx), dtype=np.float64)
        covariances = np.empty((r_count, 5, 5), dtype=np.float64)
        for r in range(r_count):
            z, psi = _separate(designs[r], whiteners[r], inputs.observed[r].reshape(n, m))
            coordinates[r] = z.reshape(5, nz, ny, nx)
            covariances[r] = psi
        maps = _real_map(inputs, designs)
        matrix = np.empty((r_count * n * m, p), dtype=np.float64)
        b = np.empty((r_count, n, m), dtype=np.float64)
        for r in range(r_count):
            whiten = whiteners[r] / sqrt(m)
            block = _apply(whiten, maps[r].reshape(n, m * p)) * sqrt(p)
            matrix[r * n * m : (r + 1) * n * m] = block.reshape(n * m, p)
            b[r] = _apply(whiten, inputs.observed[r].reshape(n, m))
        _finite(matrix)
        x, rank = _inverse(b.ravel(), matrix, inputs.alpha, p)
        predicted = np.empty_like(inputs.observed)
        residual = np.empty_like(inputs.observed)
        weighted_residual = np.empty_like(b)
        for r in range(r_count):
            predicted[r] = _apply(maps[r], x).reshape(n, nz, ny, nx)
            residual[r] = inputs.observed[r] - predicted[r]
            _finite(residual[r])
            weighted_residual[r] = _apply(whiteners[r] / sqrt(m), residual[r].reshape(n, m))
        data_objective = _squared_norm(weighted_residual)
        penalty_objective = _squared_norm(x, inputs.alpha / p)
        untapered = np.array(x.reshape(inputs.output), order="C", copy=True)
        untapered_spectrum = _transform(untapered)
        spectrum = untapered_spectrum * inputs.taper
        _finite(spectrum)
        volume = _transform(spectrum, inverse=True)
    return WeightedReconstruction3D(
        volume,
        spectrum,
        untapered,
        untapered_spectrum,
        coordinates,
        covariances,
        predicted,
        residual,
        data_objective,
        penalty_objective,
        rank,
        p,
        *inputs.frequencies,
        inputs.spacing,
    )
