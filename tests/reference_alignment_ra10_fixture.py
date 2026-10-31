"""Independent RA10 finite-sum fixtures and public-contract numerical oracles.

No simrecon imports. Units are micrometres, radians and raw signal units.
The caller design precedes synthetic truth; no truth-selected seed or mask.
"""

from dataclasses import dataclass
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

type Real = NDArray[np.float64]
type Arguments = dict[str, Any]

# Scientific/optimization accuracy targets, separate from arithmetic allowances.
# Fixed before correction probes or product observations; no truth-based tuning.
RECOVERY_PHASE_ATOL_RAD = 0.002
RECOVERY_HELDOUT_ATOL = 0.01


@dataclass
class Case:
    """Public caller design and independently specified evaluator truth."""

    arguments: Arguments
    source: Real
    actual_phases: Real


@dataclass
class Oracle:
    """Profiled finite model values and their predeclared roundoff allowance."""

    source: Real
    prediction: Real
    residual: Real
    objective: float
    source_singular: Real
    source_rank: int
    phase_singular: Real
    phase_rank: int
    free: int
    allowance: float


def finite_matrix(arguments: Arguments, phases: Real) -> Real:
    """Literal exterior-zero sum: crop affects detector, never source position."""
    shape = arguments["source_shape_zyx"]
    kernels = np.asarray(arguments["order_kernels"], dtype=np.complex128)
    origin = arguments["kernel_origin_zyx"]
    spacing = tuple(float(value) for value in arguments["source_spacing_um_zyx"])
    carrier = np.asarray(arguments["carrier_per_um_yx"], dtype=np.float64)
    crop = arguments["detector_crop_zyx"]
    detectors = list(product(*(range(a, b) for a, b in crop)))
    sources = list(product(*(range(size) for size in shape)))
    matrix = np.zeros((len(phases), len(detectors), len(sources)))
    for p, phase in enumerate(phases):
        for j, detector in enumerate(detectors):
            for q, source in enumerate(sources):
                displacement = tuple(
                    detector[axis] - source[axis] + origin[axis] for axis in range(3)
                )
                if not all(0 <= displacement[axis] < kernels.shape[axis + 1] for axis in range(3)):
                    continue
                angle = float(
                    2
                    * np.pi
                    * (carrier[0] * source[1] * spacing[1] + carrier[1] * source[2] * spacing[2])
                    + phase
                )
                k0, k1, k2 = kernels[(slice(None), *displacement)]
                matrix[p, j, q] = (
                    k0.real
                    + 2 * (k1 * np.exp(1j * angle)).real
                    + 2 * (k2 * np.exp(2j * angle)).real
                )
    return matrix


def finite_prediction(arguments: Arguments, phases: Real, source: Real) -> Real:
    # Explicit accumulation also checks matrix-vector ordering independently.
    matrix = finite_matrix(arguments, phases)
    prediction = np.zeros(matrix.shape[:2])
    for p in range(matrix.shape[0]):
        for d in range(matrix.shape[1]):
            prediction[p, d] = sum(
                float(matrix[p, d, s]) * float(source.flat[s]) for s in range(matrix.shape[2])
            )
    return prediction.reshape(arguments["images"].shape)


def phase_derivative(arguments: Arguments, phases: Real, source: Real) -> Real:
    """Differentiate the raw finite sum while holding fitted source fixed."""
    kernels = np.asarray(arguments["order_kernels"], dtype=np.complex128)
    origin = arguments["kernel_origin_zyx"]
    spacing = tuple(float(value) for value in arguments["source_spacing_um_zyx"])
    carrier = np.asarray(arguments["carrier_per_um_yx"], dtype=np.float64)
    crop = arguments["detector_crop_zyx"]
    detectors = list(product(*(range(a, b) for a, b in crop)))
    sources = list(product(*(range(size) for size in source.shape)))
    derivative = np.zeros((len(phases), len(detectors)))
    for p, phase in enumerate(phases):
        for j, detector in enumerate(detectors):
            for s in sources:
                displacement = tuple(detector[axis] - s[axis] + origin[axis] for axis in range(3))
                if not all(0 <= displacement[axis] < kernels.shape[axis + 1] for axis in range(3)):
                    continue
                theta = (
                    2 * np.pi * (carrier[0] * s[1] * spacing[1] + carrier[1] * s[2] * spacing[2])
                )
                k1 = kernels[(1, *displacement)]
                k2 = kernels[(2, *displacement)]
                derivative[p, j] += float(source[s]) * float(
                    -2
                    * (
                        k1 * np.exp(1j * (theta + phase)) + 2 * k2 * np.exp(2j * (theta + phase))
                    ).imag
                )
    return derivative


def phases_for(arguments: Arguments, offsets: Real) -> Real:
    labels = np.asarray(arguments["phases_rad"], dtype=np.float64)
    if arguments["mode"] == "known":
        return labels.copy()
    return labels + offsets


def oracle(arguments: Arguments, offsets: Real) -> Oracle:
    phases = phases_for(arguments, offsets)
    matrix = finite_matrix(arguments, phases)
    mask = arguments["fit_mask"].reshape(-1)
    n, _, voxels = matrix.shape
    m = n * int(np.count_nonzero(mask))
    bounds = arguments["offset_bounds_rad"]
    axes = np.flatnonzero(bounds[0] < bounds[1])
    if m == 0:
        source = np.zeros(arguments["source_shape_zyx"])
        prediction = finite_prediction(arguments, phases, source)
        return Oracle(
            source,
            prediction,
            prediction - arguments["images"],
            0.0,
            np.zeros(0),
            0,
            np.zeros(len(axes)),
            0,
            len(axes),
            2e-11,
        )
    covariance = np.asarray(arguments["exposure_covariance"], dtype=np.float64)
    images = np.asarray(arguments["images"], dtype=np.float64)
    cholesky = np.linalg.cholesky(covariance)
    # Solving with exposure as first axis whitens each detector vector.
    training = matrix[:, mask, :]
    b_matrix = np.linalg.solve(cholesky, training.reshape(n, -1)).reshape(
        n * int(mask.sum()), voxels
    )
    b = np.linalg.solve(cholesky, images.reshape(n, -1)[:, mask]).reshape(-1)
    u, singular, vh = np.linalg.svd(b_matrix, full_matrices=False)
    keep = singular > arguments["source_rtol"] * singular[0]
    rank = int(np.count_nonzero(keep))
    retained = u[:, keep]
    source = np.zeros(voxels)
    if rank:
        source = vh[keep].T @ ((retained.T @ b) / singular[keep])
    source = source.reshape(arguments["source_shape_zyx"])
    prediction = finite_prediction(arguments, phases, source)
    residual = prediction - images
    # Raw C^-1 quadratic form is independent of optimizer loss/whitened cache.
    raw_training = residual.reshape(n, -1)[:, mask]
    objective = float(np.sum(raw_training * np.linalg.solve(covariance, raw_training)) / (2 * m))
    raw_derivative = phase_derivative(arguments, phases, source)
    directions = np.zeros((n, matrix.shape[1], len(axes)))
    for j, axis in enumerate(axes):
        if arguments["mode"] == "common":
            directions[:, :, j] = raw_derivative
        else:
            directions[axis, :, j] = raw_derivative[axis]
    if len(axes):
        d = np.linalg.solve(cholesky, directions[:, mask, :].reshape(n, -1))
        d = d.reshape(m, len(axes))
        tangent = (d - retained @ (retained.T @ d)) / np.sqrt(m)
        phase_singular = np.linalg.svd(tangent, compute_uv=False)
        phase_singular = np.pad(phase_singular, (0, len(axes) - len(phase_singular)))
        phase_rank = int(
            np.count_nonzero(phase_singular > arguments["phase_rank_rtol"] * phase_singular[0])
        )
    else:
        phase_singular = np.zeros(0)
        phase_rank = 0
    condition = float(singular[0] / singular[keep][-1]) if rank else 1.0
    allowance = max(
        2e-11,
        512 * np.finfo(np.float64).eps * max(b_matrix.shape) * condition**2,
    )
    assert allowance < 1e-5, "Oracle fixture is too ill-conditioned for its budget"
    if singular[0] > 0:
        relative = singular / singular[0]
        margin = np.abs(relative - arguments["source_rtol"])
        # Oracle precision applicability, not a product input restriction.
        # Structural nulls may be safely discarded outside the sufficient
        # moderate-regime margin. Preserve the stronger check elsewhere.
        null_roundoff = 512 * np.finfo(np.float64).eps * max(b_matrix.shape)
        resolved_null = (relative <= null_roundoff) & (
            arguments["source_rtol"] - relative > 8 * null_roundoff
        )
        assert np.all((margin >= 1e-8) | resolved_null), (
            "Oracle fixture has an unresolved source cutoff"
        )
    return Oracle(
        source,
        prediction,
        residual,
        objective,
        singular,
        rank,
        phase_singular,
        phase_rank,
        len(axes),
        allowance,
    )


def secant_oracle(
    arguments: Arguments, offsets: Real, center: Oracle
) -> tuple[float, bool, int, float]:
    metric = 0.0
    continuous = True
    evaluations = 0
    error = 0.0
    for axis in range(len(offsets)):
        for direction, boundary in (
            (-1, arguments["offset_bounds_rad"][0, axis]),
            (1, arguments["offset_bounds_rad"][1, axis]),
        ):
            distance = float(direction * (boundary - offsets[axis]))
            step = min(float(arguments["difference_step_rad"][axis]), distance)
            if step <= 0:
                continue
            neighbor = offsets.copy()
            neighbor[axis] += direction * step
            displaced = float(abs(neighbor[axis] - offsets[axis]))
            if displaced == 0:
                continue
            observed = oracle(arguments, neighbor)
            metric = max(metric, (center.objective - observed.objective) / displaced)
            continuous = continuous and center.source_rank == observed.source_rank
            evaluations += 1
            error = max(
                error,
                (
                    center.allowance * max(1.0, abs(center.objective))
                    + observed.allowance * max(1.0, abs(observed.objective))
                )
                / displaced,
            )
    return metric, continuous, evaluations, error


def make_case(mode: str = "known", n: int = 7) -> Case:
    """Caller design is fixed independently from actual phases and specimen."""
    rng = np.random.default_rng(92841)
    kernels = rng.uniform(-0.28, 0.28, (3, 2, 3, 4)).astype(np.complex128)
    kernels[1:] += 1j * rng.uniform(-0.23, 0.23, (2, 2, 3, 4))
    labels = np.array([0.21, 1.02, 2.31, 3.09, 4.44, 5.18, 6.13])[:n]
    covariance_seed = np.eye(n) + 0.11 * np.tril(np.ones((n, n)), -1)
    q = 0 if mode == "known" else 1 if mode == "common" else n
    starts = np.zeros((1, q)) if q == 0 else np.array([0.0, 0.15, -0.15])[:, None] * np.ones((1, q))
    arguments: Arguments = {
        "images": np.zeros((n, 2, 2, 2)),
        "order_kernels": kernels,
        "kernel_origin_zyx": (0, 1, 2),
        "source_shape_zyx": (2, 2, 3),
        "detector_crop_zyx": ((0, 2), (0, 2), (1, 3)),
        "source_spacing_um_zyx": (0.75, 1.25, 0.5),
        "carrier_per_um_yx": np.array([-0.173, 0.237]),
        "exposure_covariance": covariance_seed @ covariance_seed.T,
        "fit_mask": np.array([[[True, True], [False, True]], [[True, False], [True, True]]]),
        "phases_rad": labels,
        "mode": mode,
        "initial_offsets_rad": starts,
        "offset_bounds_rad": np.array([-0.6 * np.ones(q), 0.6 * np.ones(q)]),
        "difference_step_rad": np.full(q, 0.002),
        "source_rtol": 1e-10,
        "phase_rank_rtol": 1e-7,
        "gradient_tolerance": 2e-7,
        "max_evaluations": 128,
    }
    # Independent evaluator inputs. These do not change any caller controls.
    source = np.array(
        [
            [[0.9, -0.4, 0.2], [0.6, -0.8, 0.35]],
            [[-0.3, 0.7, 0.5], [0.25, -0.15, 1.1]],
        ]
    )
    truth = np.array([0.27, -0.23, 0.19, 0.42, -0.36, 0.14, -0.09])[:n]
    actual = labels + (0.31 if mode == "common" else truth)
    if mode == "known":
        # Known monitor metadata is an actual observation, not commanded truth.
        arguments["phases_rad"] = actual.copy()
    arguments["images"] = finite_prediction(arguments, actual, source)
    return Case(arguments, source, actual)


def reimage(case: Case) -> None:
    case.arguments["images"] = finite_prediction(case.arguments, case.actual_phases, case.source)


def band_matrix(phases: Real) -> Real:
    return np.column_stack(
        (
            np.ones(len(phases)),
            np.cos(phases),
            np.sin(phases),
            np.cos(2 * phases),
            np.sin(2 * phases),
        )
    )


def make_recovery_case(mode: str) -> Case:
    """Use command start 0 for the predeclared, conditional positive outcome."""
    case = make_case(mode)
    # Preserve calibration, geometry, source, mask, bounds and all caller starts.
    # These constants do not depend on the independently generated actual phase.
    case.arguments["max_evaluations"] = 256
    case.arguments["difference_step_rad"][:] = 0.0001
    case.arguments["gradient_tolerance"] = 1e-8
    return case


def whitened_profile_residual(arguments: Arguments, offsets: Real) -> Real:
    """Evaluate the selected source profile, not the frozen-subspace tangent."""
    profile = oracle(arguments, offsets)
    n = len(arguments["phases_rad"])
    residual = profile.residual.reshape(n, -1)[:, arguments["fit_mask"].reshape(-1)]
    covariance = np.asarray(arguments["exposure_covariance"], dtype=np.float64)
    return np.linalg.solve(np.linalg.cholesky(covariance), residual).reshape(-1)


def cutoff_sensitivity_controls(
    arguments: Arguments, offsets: Real
) -> tuple[float, float, float, float]:
    """Common-mode negative controls: all-source projection and profile slopes.

    These quantities are deliberately different from the contracted diagnostic.
    The two profile slopes use h and h/2 to expose difference truncation error.
    """
    profile = oracle(arguments, offsets)
    phases = phases_for(arguments, offsets)
    n = len(phases)
    mask = arguments["fit_mask"].reshape(-1)
    m = n * int(mask.sum())
    cholesky = np.linalg.cholesky(np.asarray(arguments["exposure_covariance"], dtype=np.float64))
    raw_matrix = finite_matrix(arguments, phases)[:, mask, :]
    b = np.linalg.solve(cholesky, raw_matrix.reshape(n, -1)).reshape(m, -1)
    # All source columns are nonzero independent directions in this fixture.
    assert np.linalg.matrix_rank(b) == b.shape[1]
    full_basis = np.linalg.qr(b, mode="reduced")[0]
    raw_derivative = phase_derivative(arguments, phases, profile.source)[:, mask]
    d = np.linalg.solve(cholesky, raw_derivative).reshape(-1)
    all_source = float(np.linalg.norm(d - full_basis @ (full_basis.T @ d)) / np.sqrt(m))
    profile_norms = []
    for step in (1e-4, 5e-5):
        slope = (
            whitened_profile_residual(arguments, offsets + step)
            - whitened_profile_residual(arguments, offsets - step)
        ) / (2 * step)
        profile_norms.append(float(np.linalg.norm(slope) / np.sqrt(m)))
    cutoff_margin = float(
        np.min(
            np.abs(profile.source_singular / profile.source_singular[0] - arguments["source_rtol"])
        )
    )
    return all_source, profile_norms[0], profile_norms[1], cutoff_margin
