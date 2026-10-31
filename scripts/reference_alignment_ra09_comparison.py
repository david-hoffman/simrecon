"""Prepare, observe and render the scoped RA09 finite-overlap comparison.

Preparation imports no product code. Saved acquisition metadata excludes truth.
Observation saves and seals every product output before loading evaluation truth.
Figures concern a declared small synthetic model, never a reconstruction claim.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import itertools
import json
import platform
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/ra09/figure-preparation"
CONTRACT = "docs/contracts/reference-alignment-ra09-v1.md"
BENCHMARK = "docs/benchmarks/reference-alignment-v1.json"
CASES = ("finite_objective", "flat_noiseless", "flat_noise", "finite_mismatch")
EPS = np.finfo(np.float64).eps


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(_json_value(value), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, (tuple, list)):
        return [_json_value(v) for v in value]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, np.generic):
        return _json_value(value.item())
    return value


def _complex(value: Any) -> complex:
    return complex(value["real"], value["imag"])


def _load_arrays(path: Path) -> dict[str, Array]:
    with np.load(path, allow_pickle=False) as stored:
        return {key: stored[key].copy() for key in stored.files}


def _bins(length: int) -> Array:
    return np.arange(-(length // 2), (length + 1) // 2, dtype=np.int64)


def _coordinates(shape: tuple[int, ...]) -> Array:
    return np.indices(shape, dtype=np.float64).reshape(3, -1).T


def _finite_dft(values: Array, targets: Array) -> Array:
    """Evaluate a normalized negative-sign finite sum without an FFT.

    The target can be noninteger. Blocking limits the observer's temporary size;
    it changes neither the finite window nor the index-zero origin.
    """
    shape = np.asarray(values.shape, dtype=np.float64)
    coordinates = _coordinates(values.shape)
    flat = values.reshape(-1)
    result = np.empty(len(targets), dtype=np.complex128)
    for first in range(0, len(targets), 64):
        target = targets[first : first + 64]
        phase = (target / shape) @ coordinates.T
        result[first : first + len(target)] = np.exp(-2j * np.pi * phase) @ flat / values.size
    return result


def _overlap(shape: tuple[int, ...], spacing: Array, bounds: Array, order: int) -> Array:
    """Select the fixed all-box support with exact represented-real products."""
    axes: list[list[int]] = []
    for axis, length in enumerate(shape):
        native = _bins(length).tolist()
        if axis == 0:
            axes.append(native)
            continue
        extent = Fraction(length) * Fraction.from_float(float(spacing[axis]))
        lower = order * extent * Fraction.from_float(float(bounds[0, axis - 1]))
        upper = order * extent * Fraction.from_float(float(bounds[1, axis - 1]))
        axes.append([q for q in native if native[0] <= q + lower and q + upper <= native[-1]])
    return np.asarray(list(itertools.product(*axes)), dtype=np.int64).reshape(-1, 3)


def _interpolate(values: Array, targets: Array) -> Array:
    """Interpolate transfer components on ideal native bin nodes."""
    shape = np.asarray(values.shape, dtype=np.int64)
    location = targets + shape // 2
    lo = np.floor(location).astype(np.int64)
    hi = np.minimum(lo + 1, shape - 1)
    fraction = location - lo
    result = np.zeros(len(targets), dtype=np.complex128)
    for corner in itertools.product((0, 1), repeat=3):
        index = np.where(corner, hi, lo)
        weight = np.prod(np.where(corner, fraction, 1 - fraction), axis=1)
        result += weight * values[tuple(index.T)]
    return result


def _profile(
    bands: Array, transfer: Array, spacing: Array, carrier: Array, support: tuple[Array, Array]
) -> dict[str, Any]:
    """Calculate the contract's coupled normalized regression independently."""
    scale = np.asarray(bands.shape[1:]) * spacing
    residuals: list[Array] = []
    orders: list[dict[str, Any]] = []
    for order, q in enumerate(support, start=1):
        if len(q) == 0:
            raise ValueError("The declared figure controls require nonempty overlap.")
        shifted = q.astype(np.float64) + np.r_[0.0, order * scale[1:] * carrier]
        d0 = _finite_dft(bands[0], q)
        dm = _finite_dft(bands[order], shifted)
        x = _interpolate(transfer[order], shifted) * d0
        y = transfer[0][tuple((q + np.asarray(bands.shape[1:]) // 2).T)] * dm
        nx, ny = float(np.linalg.norm(x)), float(np.linalg.norm(y))
        if nx == 0 or ny == 0:
            raise ValueError("The declared figure controls require informative norms.")
        u, v = x / nx, y / ny
        h = np.vdot(u, v)
        residual = v - h * u
        residuals.append(np.r_[residual.real, 0.0, residual.imag, 0.0])
        orders.append(
            {
                "gain": complex((ny / nx) * h),
                "coherence": float(abs(h)),
                "relative_residual": float(np.linalg.norm(residual)),
                "objective": float(np.vdot(residual, residual).real),
                "predictor_norm": nx,
                "response_norm": ny,
                "x": x,
                "y": y,
            }
        )
    return {
        "objective": sum(o["objective"] for o in orders),
        "orders": orders,
        "residual": np.concatenate(residuals),
    }


def _summary(profile: dict[str, Any]) -> dict[str, Any]:
    return _json_value(
        {
            "objective": profile["objective"],
            "orders": [
                {k: v for k, v in order.items() if k not in {"x", "y"}}
                for order in profile["orders"]
            ],
        }
    )


def _ramp(shape: tuple[int, ...], spacing: Array, carrier: Array, order: int) -> Array:
    coordinates = _coordinates(shape)
    phase = coordinates[:, 1:] @ (spacing[1:] * carrier)
    return np.exp(2j * np.pi * order * phase).reshape(shape)


def _convolve_zero(values: Array, kernel: Array) -> Array:
    """Apply the declared 3x3x3 kernel with zero exterior and same-size crop."""
    result = np.zeros(values.shape, dtype=np.complex128)
    for index in itertools.product(range(3), repeat=3):
        offset = np.asarray(index) - 1
        destination = tuple(
            slice(max(0, int(d)), min(n, n + int(d)))
            for d, n in zip(offset, values.shape, strict=True)
        )
        source = tuple(
            slice(max(0, -int(d)), min(n, n - int(d)))
            for d, n in zip(offset, values.shape, strict=True)
        )
        result[destination] += kernel[index] * values[source]
    return result


def _kernel_transfer(kernels: Array, shape: tuple[int, ...]) -> Array:
    q = np.asarray(list(itertools.product(*(_bins(n) for n in shape))))
    offset = _coordinates((3, 3, 3)) - 1
    phase = (q / np.asarray(shape)) @ offset.T
    matrix = np.exp(-2j * np.pi * phase)
    return np.asarray([matrix @ k.reshape(-1) for k in kernels]).reshape(3, *shape)


def _model_bands(
    specimen: Array, spacing: Array, carrier: Array, gains: Array, kernels: Array
) -> Array:
    rows = [np.real(_convolve_zero(specimen, kernels[0])).astype(np.complex128)]
    for order in (1, 2):
        rows.append(
            gains[order - 1]
            * _convolve_zero(
                specimen * _ramp(specimen.shape, spacing, carrier, order), kernels[order]
            )
        )
    return np.asarray(rows, dtype=np.complex128)


def _exposure(bands: Array, phase: float) -> Array:
    return bands[0].real + 2 * np.real(
        bands[1] * np.exp(1j * phase) + bands[2] * np.exp(2j * phase)
    )


def _metadata(shape: tuple[int, ...], spacing: Array, fixed: bool) -> dict[str, Any]:
    lengths = np.asarray(shape)[1:] * spacing[1:]
    if fixed:
        nominal = np.array([0.125, -0.125])
        bounds = np.stack([nominal, nominal])
    else:
        nominal = np.array([0.20, 0.50]) / lengths
        bounds = np.array([[0.10, 0.20], [0.50, 0.65]]) / lengths
    return {
        "shape_zyx": list(shape),
        "spacing_um_zyx": spacing.tolist(),
        "origin_zyx": [0, 0, 0],
        "source": "RA09 declared finite synthetic calibration; no measured instrument claim",
        "initial_carriers_per_um": [nominal.tolist()],
        "carrier_bounds_per_um": bounds.tolist(),
        "difference_step_per_um": (np.array([1e-4, 1e-4]) / lengths).tolist(),
        "gradient_tolerance": 1e-8,
        "rank_rtol": 1e-6,
        "max_evaluations": 256,
        "initialization": (
            "nominal acquisition bins (0.20,0.50), independently declared before fitting"
            if not fixed
            else "fixed arithmetic-control comparison point; not a recovery start"
        ),
    }


def _make_scene(shape: tuple[int, ...], spacing: Array, catalogue: list[dict[str, Any]]) -> Array:
    position = (_coordinates(shape) + 0.5) * spacing
    specimen = np.full(np.prod(shape), 0.015, dtype=np.float64)
    for bead in catalogue:
        displacement = (position - bead["center_um_zyx"]) / bead["sigma_um_zyx"]
        specimen += bead["amplitude_relative"] * np.exp(-0.5 * np.sum(displacement**2, axis=1))
    return specimen.reshape(shape)


def _condition_and_allowances(
    bands: Array, transfer: Array, spacing: Array, truth: Array, support: tuple[Array, Array]
) -> dict[str, Any]:
    """Predeclare finite arithmetic and a local informative phase-recovery goal.

    A normalized direct-sum component allowance is 64*M*eps*B. Multiplication
    and transfer interpolation allowances enter before vector normalization.
    The factors below deliberately exceed first-order perturbation constants.
    The phase goal is conditional on remaining in the declared local basin;
    no optimization, global uniqueness or noise guarantee follows.
    """
    lengths = np.asarray(bands.shape[1:])[1:] * spacing[1:]
    center = _profile(bands, transfer, spacing, truth, support)
    delta_bin = 1e-3
    columns = []
    minimum_norm = min(min(o["predictor_norm"], o["response_norm"]) for o in center["orders"])
    for axis in range(2):
        step = np.zeros(2)
        step[axis] = delta_bin / lengths[axis]
        plus = _profile(bands, transfer, spacing, truth + step, support)
        minus = _profile(bands, transfer, spacing, truth - step, support)
        columns.append((plus["residual"] - minus["residual"]) / (2 * delta_bin))
        minimum_norm = min(
            minimum_norm,
            *(
                min(o["predictor_norm"], o["response_norm"])
                for p in (plus, minus)
                for o in p["orders"]
            ),
        )
    singular = np.linalg.svd(np.stack(columns, axis=1), compute_uv=False)
    component_bound = 64 * bands[0].size * EPS * float(np.max(np.abs(bands)))
    transfer_bound = max(1.0, float(np.max(np.abs(transfer))))
    norm_bound = np.sqrt(max(map(len, support))) * component_bound * transfer_bound * 4
    normalized_bound = 16 * norm_bound / minimum_norm
    arithmetic_allowance = 16 * normalized_bound + 128 * EPS
    phase_goal = 0.03
    bin_goal = phase_goal / (4 * np.pi * np.sqrt(2))
    residual_goal = float(singular[-1]) * bin_goal / 4
    return {
        "arithmetic_objective_absolute_allowance": float(arithmetic_allowance),
        "arithmetic_gain_absolute_allowance": float(normalized_bound * 8),
        "arithmetic_basis": (
            "64*M*eps*B direct-sum component bound; propagated products, norms "
            "and normalization; conservative factors 4,16,16"
        ),
        "minimum_stencil_operand_norm": minimum_norm,
        "direct_sum_component_allowance": component_bound,
        "local_singular_values_per_detector_bin": singular.tolist(),
        "conditioning_stencil_halfwidth_bins": delta_bin,
        "local_phase_goal_rad_order2_full_field": phase_goal,
        "local_carrier_goal_l2_detector_bins": bin_goal,
        "local_objective_goal": residual_goal**2,
        "local_regime_halfwidth_bins": 0.10,
        "local_goal_basis": (
            "order-2 phase <=4*pi*sqrt(2)*||delta carrier bins||; target residual "
            "<=s_min*bin_goal/4; local finite-secant information only"
        ),
        "limits": (
            "The recovery goal is a predeclared conditional figure control, not a public "
            "uniform error theorem or optimizer guarantee. Noise and mismatch have no "
            "recovery allowance."
        ),
    }


def _source_identity() -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    paths = (CONTRACT, BENCHMARK, "docs/plans/reference-alignment-roadmap.md", "uv.lock")
    return {
        "git_head": completed.stdout.strip(),
        "driver_sha256": _hash(Path(__file__)),
        "sources": {path: _hash(ROOT / path) for path in paths},
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
    }


def _landscape(
    bands: Array, transfer: Array, spacing: Array, bounds: Array, support: tuple[Array, Array]
) -> dict[str, Array]:
    """Sample the declared box identically for coupled and order-two objectives."""
    axes = [np.linspace(bounds[0, a], bounds[1, a], 9) for a in range(2)]
    joint = np.empty((9, 9))
    second = np.empty((9, 9))
    for iy, ky in enumerate(axes[0]):
        for ix, kx in enumerate(axes[1]):
            profile = _profile(bands, transfer, spacing, np.array([ky, kx]), support)
            joint[iy, ix] = profile["objective"]
            second[iy, ix] = profile["orders"][1]["objective"]
    return {
        "carrier_y_per_um": axes[0],
        "carrier_x_per_um": axes[1],
        "joint_objective": joint,
        "order2_objective": second,
    }


def prepare(output: Path) -> None:
    """Save observations, independent expectations and truth before product calls."""
    if (output / "prepared.json").exists():
        raise FileExistsError(
            "Prepared inputs are immutable; select a new explicit output directory."
        )
    output.mkdir(parents=True, exist_ok=True)
    benchmark = _read_json(ROOT / BENCHMARK)
    bead = benchmark["figures"]["plane_choices"]["specimen_o0_p0"]
    catalogue = [
        {
            "center_um_zyx": bead["nominal_bead_center_local_um_zyx"],
            "sigma_um_zyx": [0.18, 0.50, 0.50],
            "amplitude_relative": 1.0,
        },
        {
            "center_um_zyx": [0.35, 1.60, 1.65],
            "sigma_um_zyx": [0.15, 0.60, 0.40],
            "amplitude_relative": 0.7,
        },
        {
            "center_um_zyx": [0.90, 2.60, 5.00],
            "sigma_um_zyx": [0.16, 0.40, 0.55],
            "amplitude_relative": 0.5,
        },
    ]
    spacing = np.array([0.25, 0.5, 0.5])
    shape = (5, 11, 13)
    specimen = _make_scene(shape, spacing, catalogue)
    planes = [
        int(np.argmin(abs((np.arange(n) + 0.5) * d - center)))
        for n, d, center in zip(shape, spacing, catalogue[0]["center_um_zyx"], strict=True)
    ]
    _write_json(
        output / "catalogue.json",
        {
            "catalogue": catalogue,
            "shape_zyx": shape,
            "spacing_um_zyx": spacing.tolist(),
            "section_indices_zyx": planes,
            "actual_section_centers_um_zyx": ((np.asarray(planes) + 0.5) * spacing).tolist(),
            "selection": (
                "first declared catalogue row; nearest stored sample center; first index "
                "on ties; full field; no fitted recentering"
            ),
            "benchmark_mapping": {
                "source": BENCHMARK,
                "field": "figures.plane_choices.specimen_o0_p0.nominal_bead_center_local_um_zyx",
                "copied_center_um_zyx": catalogue[0]["center_um_zyx"],
                "limits": (
                    "Only the first bead center is reused. Dimensions, spacing, smooth "
                    "Gaussian profiles and other objects define a new small synthetic scene."
                ),
            },
        },
    )
    true_carrier = np.array([0.28, 0.42]) / (np.asarray(shape)[1:] * spacing[1:])
    gains = np.array([0.5 * np.exp(0.22j), 0.25 * np.exp(-0.31j)])
    flat = np.zeros((3, 3, 3, 3), dtype=np.complex128)
    flat[:, 1, 1, 1] = [1, 0.72 * np.exp(0.13j), 0.43 * np.exp(-0.21j)]
    offset = _coordinates((3, 3, 3)) - 1
    kernel = np.exp(-np.sum(offset**2 * np.array([0.6, 1.0, 0.8]), axis=1))
    kernel /= kernel.sum()
    varying = np.asarray(
        [
            kernel,
            kernel * (0.72 * np.exp(0.13j + 0.18j * offset[:, 0])),
            kernel * (0.43 * np.exp(-0.21j - 0.24j * offset[:, 0])),
        ]
    ).reshape(3, 3, 3, 3)
    heldout_phase = 0.41
    prepared_files: list[Path] = [output / "catalogue.json"]
    for name in CASES:
        tiny = name == "finite_objective"
        this_shape = (3, 5, 5) if tiny else shape
        this_spacing = np.array([0.5, 0.5, 0.5]) if tiny else spacing
        this_specimen = (
            _make_scene(
                this_shape,
                this_spacing,
                [
                    {
                        "center_um_zyx": [0.7, 1.1, 1.4],
                        "sigma_um_zyx": [0.35, 0.45, 0.40],
                        "amplitude_relative": 1.0,
                    }
                ],
            )
            if tiny
            else specimen
        )
        kernels = varying if name in {"finite_objective", "finite_mismatch"} else flat
        carrier = np.array([0.08, -0.06]) if tiny else true_carrier
        clean_bands = _model_bands(this_specimen, this_spacing, carrier, gains, kernels)
        bands = clean_bands.copy()
        heldout_noise = np.zeros(this_shape, dtype=np.float64)
        if name == "flat_noise":
            noise = np.random.default_rng(2026103108).normal(0, 0.002, bands.shape + (2,))
            bands += noise[..., 0] + 1j * noise[..., 1]
            bands[0] = bands[0].real
            heldout_noise = np.random.default_rng(2026103109).normal(0, 0.002, this_shape)
        transfer = _kernel_transfer(kernels, this_shape)
        metadata = _metadata(this_shape, this_spacing, tiny)
        metadata["case"] = name
        metadata["noise"] = (
            {
                "model": (
                    "independent additive Gaussian real/imaginary separated-band "
                    "components; dc real only"
                ),
                "sd_relative": 0.002,
                "band_seed": 2026103108,
                "heldout_seed": 2026103109,
            }
            if name == "flat_noise"
            else None
        )
        metadata["heldout_phase_rad"] = heldout_phase
        q = tuple(
            _overlap(this_shape, this_spacing, np.asarray(metadata["carrier_bounds_per_um"]), m)
            for m in (1, 2)
        )
        support = (q[0], q[1])
        start = np.asarray(metadata["initial_carriers_per_um"][0])
        at_start = _profile(bands, transfer, this_spacing, start, support)
        at_truth = _profile(bands, transfer, this_spacing, carrier, support)
        integer = np.rint(start * np.asarray(this_shape)[1:] * this_spacing[1:])
        integer_carrier = integer / (np.asarray(this_shape)[1:] * this_spacing[1:])
        baseline = _profile(bands, transfer, this_spacing, integer_carrier, support)
        allowance = _condition_and_allowances(bands, transfer, this_spacing, carrier, support)
        directory = output / name
        directory.mkdir(exist_ok=True)
        if not tiny:
            landscape = _landscape(
                bands,
                transfer,
                this_spacing,
                np.asarray(metadata["carrier_bounds_per_um"]),
                support,
            )
            np.savez(
                directory / "objective-landscape.npz",
                carrier_y_per_um=landscape["carrier_y_per_um"],
                carrier_x_per_um=landscape["carrier_x_per_um"],
                joint_objective=landscape["joint_objective"],
                order2_objective=landscape["order2_objective"],
            )
        np.savez(directory / "observations.npz", bands=bands, transfer=transfer)
        _write_json(directory / "search.json", metadata)
        np.savez(
            directory / "evaluation-truth.npz",
            specimen=this_specimen,
            carrier=carrier,
            gains=gains,
            kernels=kernels,
            clean_bands=clean_bands,
            heldout_noise=heldout_noise,
        )
        expectations = {
            "case": name,
            "method": (
                "direct normalized finite sums plus independent complex regression; "
                "transfer Cartesian linear interpolation on ideal nodes"
            ),
            "fixed_overlap_counts": [len(s) for s in support],
            "at_nominal": _summary(at_start),
            "at_generation_carrier_evaluation_only": _summary(at_truth),
            "integer_baseline_same_fixed_Q": {
                "carrier_bins_yx": integer.tolist(),
                "carrier_per_um_yx": integer_carrier.tolist(),
                "profile": _summary(baseline),
                "limits": (
                    "Integer nonwrapping gain regression restricted to the identical Q; "
                    "not the larger complete overlap of a separate fixed-integer box."
                ),
            },
            "allowances": allowance,
            "identifiable_exact_model": name == "flat_noiseless",
            "order_pair_comparison": (
                "Predeclared 9x9 metadata-box grid: joint J1+J2 versus J2 alone on "
                "identical Q2. This aligns with the roadmap's source observation that "
                "ordinary reference 3D fitting principally uses 0-to-2 overlap; no "
                "legacy execution or measured C parity. Grid minima are sampled values, "
                "not continuous or global optimization certificates."
            ),
            "limits": (
                "No full raw estimation, specimen reconstruction, continuum recovery, "
                "global uniqueness or legacy C execution. Nonconstant transfer uses "
                "zero-exterior convolution/crop and is deliberately outside the exact "
                "phase-ramped flat-transfer identity."
            ),
        }
        _write_json(directory / "expected.json", expectations)
        np.savez(
            directory / "expected-arrays.npz",
            q1=support[0],
            q2=support[1],
            x1=at_start["orders"][0]["x"],
            y1=at_start["orders"][0]["y"],
            x2=at_start["orders"][1]["x"],
            y2=at_start["orders"][1]["y"],
        )
        prepared_files.extend(sorted(directory.iterdir()))
    _write_json(
        output / "prepared.json",
        {
            "schema": "simrecon.ra09.figure-preparation.v1",
            "identity": _source_identity(),
            "files": {str(path.relative_to(output)): _hash(path) for path in prepared_files},
            "product_calls": 0,
            "truth_boundary": (
                "observe reads only observations/search until all product outputs and "
                "observed-freeze.json have been saved; evaluation then reads truth/expectations"
            ),
            "scene_selection": (
                "declared catalogue, dimensions, seeds, slice rule and heldout phase "
                "fixed before product observation"
            ),
            "human_numeric_limits": "not set",
        },
    )
    print(f"Prepared and sealed {len(prepared_files)} files at {output}")


def _verify_prepared(output: Path, *, observations_only: bool = False) -> dict[str, Any]:
    prepared = _read_json(output / "prepared.json")
    for name, digest in prepared["files"].items():
        if observations_only and Path(name).name not in {"observations.npz", "search.json"}:
            continue
        if _hash(output / name) != digest:
            raise ValueError(f"Prepared artifact changed: {name}")
    if _hash(Path(__file__)) != prepared["identity"]["driver_sha256"]:
        raise ValueError("Driver changed after preparation; use a new explicit preparation output.")
    return prepared


def observe(output: Path, authorization: str) -> None:
    """Call the public operation, seal outputs, then evaluate against saved truth."""
    _verify_prepared(output, observations_only=True)
    if (output / "observed-freeze.json").exists():
        raise FileExistsError(
            "Observed outputs are immutable; retain this run and use a new preparation."
        )
    if not authorization.strip():
        raise ValueError("Observation needs the coordinator's recorded authorization reference.")
    product = importlib.import_module("simrecon")
    output_files = []
    for name in CASES:
        directory = output / name
        metadata = _read_json(directory / "search.json")
        arrays = _load_arrays(directory / "observations.npz")
        shape = tuple(metadata["shape_zyx"])
        spacing = np.asarray(metadata["spacing_um_zyx"])
        grids = [_bins(n).astype(np.float64) / (n * d) for n, d in zip(shape, spacing, strict=True)]
        calibration = product.VolumeOrderOtf(
            values=arrays["transfer"],
            fz_per_um=grids[0],
            fy_per_um=grids[1],
            fx_per_um=grids[2],
            voxel_size_um=tuple(spacing),
            origin_zyx=tuple(metadata["origin_zyx"]),
            source=metadata["source"],
        )
        result = product.fit_volume_overlap(
            arrays["bands"],
            order_otf=calibration,
            initial_carriers_per_um=np.asarray(metadata["initial_carriers_per_um"]),
            carrier_bounds_per_um=np.asarray(metadata["carrier_bounds_per_um"]),
            difference_step_per_um=np.asarray(metadata["difference_step_per_um"]),
            gradient_tolerance=metadata["gradient_tolerance"],
            rank_rtol=metadata["rank_rtol"],
            max_evaluations=metadata["max_evaluations"],
        )
        candidates = []
        fields = (
            "initial_carrier_per_um",
            "carrier_per_um",
            "gains",
            "order_status",
            "coherence",
            "relative_residual",
            "objective",
            "projected_gradient",
            "stationary",
            "information_singular_values",
            "information_rank",
            "status",
            "search_evaluations",
            "diagnostic_evaluations",
            "budget_exhausted",
            "diagnostics_continuous",
            "predictor_log2_norm",
            "response_log2_norm",
            "global_ambiguity",
        )
        for candidate in result.candidates:
            candidates.append({field: _json_value(getattr(candidate, field)) for field in fields})
        observed = {
            "candidates": candidates,
            "spacing_um": _json_value(result.spacing_um),
            "source": result.source,
            "carrier_bounds_per_um": _json_value(result.carrier_bounds_per_um),
        }
        _write_json(directory / "observed.json", observed)
        np.savez(
            directory / "observed-arrays.npz", q1=result.overlap_bins[0], q2=result.overlap_bins[1]
        )
        output_files.extend((directory / "observed.json", directory / "observed-arrays.npz"))
    _write_json(
        output / "observed-freeze.json",
        {
            "authorization": authorization,
            "identity": _source_identity(),
            "prepared_sha256": _hash(output / "prepared.json"),
            "files": {str(path.relative_to(output)): _hash(path) for path in output_files},
            "truth_loaded_before_output_freeze": False,
        },
    )
    # This is the first evaluation-truth read in observation mode.
    _evaluate(output)
    print(f"Observed, sealed and evaluated {len(CASES)} cases at {output}")


def _evaluate(output: Path) -> None:
    for name in CASES:
        directory = output / name
        metadata = _read_json(directory / "search.json")
        expected = _read_json(directory / "expected.json")
        arrays = _load_arrays(directory / "observations.npz")
        truth = _load_arrays(directory / "evaluation-truth.npz")
        saved = _load_arrays(directory / "expected-arrays.npz")
        observed_support = _load_arrays(directory / "observed-arrays.npz")
        observed = _read_json(directory / "observed.json")
        candidate = observed["candidates"][0]
        spacing = np.asarray(metadata["spacing_um_zyx"])
        carrier = np.asarray(candidate["carrier_per_um"])
        support = (saved["q1"], saved["q2"])
        profile = _profile(arrays["bands"], arrays["transfer"], spacing, carrier, support)
        gains = np.asarray([_complex(g) for g in candidate["gains"]])
        prediction_bands = _model_bands(
            truth["specimen"], spacing, carrier, gains, truth["kernels"]
        )
        prediction = _exposure(prediction_bands, metadata["heldout_phase_rad"])
        reference = _exposure(truth["clean_bands"], metadata["heldout_phase_rad"])
        reference += truth["heldout_noise"]
        position = _coordinates(reference.shape) * spacing
        carrier_phase = (2 * np.pi * position[:, 1:] @ (carrier - truth["carrier"])).reshape(
            reference.shape
        )
        nominal = np.asarray(metadata["initial_carriers_per_um"][0])
        nominal_carrier_phase = (
            2 * np.pi * position[:, 1:] @ (nominal - truth["carrier"])
        ).reshape(reference.shape)
        phase_error = np.asarray(
            [
                order * carrier_phase + np.angle(gains[order - 1] / truth["gains"][order - 1])
                for order in (1, 2)
            ]
        )
        integer = np.asarray(expected["integer_baseline_same_fixed_Q"]["carrier_per_um_yx"])
        integer_profile = _profile(arrays["bands"], arrays["transfer"], spacing, integer, support)
        integer_gains = np.asarray([o["gain"] for o in integer_profile["orders"]])
        baseline_prediction = _exposure(
            _model_bands(truth["specimen"], spacing, integer, integer_gains, truth["kernels"]),
            metadata["heldout_phase_rad"],
        )
        np.savez(
            directory / "evaluation-arrays.npz",
            reference=reference,
            prediction=prediction,
            integer_prediction=baseline_prediction,
            signed_difference=prediction - reference,
            carrier_phase_error_rad_order1=carrier_phase,
            nominal_carrier_phase_error_rad_order1=nominal_carrier_phase,
            phase_error_rad=phase_error,
            x1=profile["orders"][0]["x"],
            y1=profile["orders"][0]["y"],
            x2=profile["orders"][1]["x"],
            y2=profile["orders"][1]["y"],
        )
        objective_error = abs(candidate["objective"] - profile["objective"])
        gain_error = [abs(g - p["gain"]) for g, p in zip(gains, profile["orders"], strict=True)]
        allowance = expected["allowances"]
        _write_json(
            directory / "evaluation.json",
            {
                "independent_at_observed": _summary(profile),
                "objective_absolute_difference": objective_error,
                "objective_within_predeclared_arithmetic_allowance": objective_error
                <= allowance["arithmetic_objective_absolute_allowance"],
                "gain_absolute_differences": gain_error,
                "gains_within_predeclared_arithmetic_allowance": max(gain_error)
                <= allowance["arithmetic_gain_absolute_allowance"],
                "overlap_equal": all(
                    np.array_equal(saved[k], observed_support[k]) for k in ("q1", "q2")
                ),
                "carrier_error_detector_bins_yx": (
                    (carrier - truth["carrier"]) * np.asarray(reference.shape)[1:] * spacing[1:]
                ).tolist(),
                "relative_heldout_l2": float(
                    np.linalg.norm(prediction - reference) / np.linalg.norm(reference)
                ),
                "integer_relative_heldout_l2": float(
                    np.linalg.norm(baseline_prediction - reference) / np.linalg.norm(reference)
                ),
                "carrier_only_max_order2_phase_error_rad": float(np.max(abs(2 * carrier_phase))),
                "nominal_carrier_only_max_order2_phase_error_rad": float(
                    np.max(abs(2 * nominal_carrier_phase))
                ),
                "gain_only_phase_error_rad_by_order": np.angle(gains / truth["gains"]).tolist(),
                "gain_amplitude_ratio_by_order": abs(gains / truth["gains"]).tolist(),
                "gain_and_carrier_max_phase_error_rad_by_order": np.max(
                    abs(phase_error), axis=(1, 2, 3)
                ).tolist(),
                "conditional_noiseless_phase_goal_met": bool(
                    np.max(abs(2 * carrier_phase))
                    <= allowance["local_phase_goal_rad_order2_full_field"]
                )
                if expected["identifiable_exact_model"]
                else None,
                "limits": expected["limits"],
            },
        )


def render(output: Path) -> None:
    """Render sealed numerical observations with an externally retained plot env."""
    _verify_prepared(output)
    freeze = _read_json(output / "observed-freeze.json")
    for name, digest in freeze["files"].items():
        if _hash(output / name) != digest:
            raise ValueError(f"Observed artifact changed: {name}")
    plt = importlib.import_module("matplotlib.pyplot")
    catalogue = _read_json(output / "catalogue.json")
    planes = catalogue["section_indices_zyx"]
    for name in CASES[1:]:
        directory = output / name
        arrays = _load_arrays(directory / "evaluation-arrays.npz")
        saved = _load_arrays(directory / "expected-arrays.npz")
        metadata = _read_json(directory / "search.json")
        spacing = np.asarray(metadata["spacing_um_zyx"])
        reference, prediction = arrays["reference"], arrays["prediction"]
        figure, axes = plt.subplots(4, 3, figsize=(13, 10), layout="constrained")
        views = (
            ("XY maximum over z", lambda v: np.max(v, axis=0), (2, 1)),
            ("XZ maximum over y", lambda v: np.max(v, axis=1), (2, 0)),
            (f"XY section z index {planes[0]}", lambda v: v[planes[0]], (2, 1)),
            (f"XZ section y index {planes[1]}", lambda v: v[:, planes[1]], (2, 0)),
        )
        vmin, vmax = (
            min(float(reference.min()), float(prediction.min())),
            max(float(reference.max()), float(prediction.max())),
        )
        differences = [view(prediction) - view(reference) for _, view, _ in views]
        difference_limit = max(float(np.max(abs(d))) for d in differences) or EPS
        for row, (label, view, dimensions) in enumerate(views):
            horizontal, vertical = dimensions
            extent = (
                0,
                reference.shape[horizontal] * spacing[horizontal],
                0,
                reference.shape[vertical] * spacing[vertical],
            )
            images = (view(reference), view(prediction), differences[row])
            for column, (title, image) in enumerate(
                zip(
                    ("Held-out reference", "Fit prediction", "Prediction − reference"),
                    images,
                    strict=True,
                )
            ):
                ax = axes[row, column]
                artist = ax.imshow(
                    image,
                    origin="lower",
                    extent=extent,
                    aspect="equal",
                    interpolation="nearest",
                    cmap="coolwarm" if column == 2 else "viridis",
                    vmin=-difference_limit if column == 2 else vmin,
                    vmax=difference_limit if column == 2 else vmax,
                )
                ax.set(
                    title=f"{label}: {title}",
                    xlabel=f"{'zyx'[horizontal]} (µm)",
                    ylabel=f"{'zyx'[vertical]} (µm)",
                )
                figure.colorbar(artist, ax=ax, label="relative intensity units", shrink=0.8)
        figure.suptitle(
            f"RA09 {name}: held-out phase {metadata['heldout_phase_rad']} rad; "
            "known specimen used only after fit freeze"
        )
        figure.savefig(directory / "heldout-field.png", dpi=170)
        plt.close(figure)
        figure, axes = plt.subplots(2, 4, figsize=(16, 7), layout="constrained")
        phase = arrays["phase_error_rad"]
        nominal_phase = arrays["nominal_carrier_phase_error_rad_order1"]
        refined_phase = arrays["carrier_phase_error_rad_order1"]
        phase_limit = max(float(np.max(abs(phase))), float(np.max(abs(2 * nominal_phase)))) or EPS
        for row, order in enumerate((1, 2)):
            for column, (image, label) in enumerate(
                (
                    (order * nominal_phase[planes[0]], "Nominal carrier slope only"),
                    (order * refined_phase[planes[0]], "Refined carrier slope only"),
                    (phase[row, planes[0]], "Refined slope + relative gain phase"),
                )
            ):
                ax = axes[row, column]
                artist = ax.imshow(
                    image,
                    origin="lower",
                    extent=(
                        0,
                        reference.shape[2] * spacing[2],
                        0,
                        reference.shape[1] * spacing[1],
                    ),
                    aspect="equal",
                    interpolation="nearest",
                    cmap="coolwarm",
                    vmin=-phase_limit,
                    vmax=phase_limit,
                )
                ax.set(
                    title=f"Order {order}: {label}",
                    xlabel="x (µm)",
                    ylabel="y (µm)",
                )
                figure.colorbar(artist, ax=ax, label="unwrapped phase error (rad)", shrink=0.8)
            q = saved[f"q{order}"]
            ax = axes[row, 3]
            sample = q[q[:, 0] == 0]
            ax.scatter(
                sample[:, 2] / (reference.shape[2] * spacing[2]),
                sample[:, 1] / (reference.shape[1] * spacing[1]),
                s=12,
            )
            ax.set(
                title=f"Order {order}: fixed Q, qz=0 ({len(q)} 3D bins)",
                xlabel="qx (cycles/µm)",
                ylabel="qy (cycles/µm)",
                aspect="equal",
            )
        figure.suptitle(
            f"RA09 {name}: full XY field (zero axial carrier); "
            "same phase scale; gain phase reported separately in evaluation.json"
        )
        figure.savefig(directory / "phase-and-support.png", dpi=170)
        plt.close(figure)
        figure, axes = plt.subplots(1, 3, figsize=(13, 3.8), layout="constrained")
        x = (np.arange(reference.shape[2]) + 0.5) * spacing[2]
        z, y, _ = planes
        for label, volume in (
            ("Reference", reference),
            ("Fit", prediction),
            ("Integer same Q", arrays["integer_prediction"]),
        ):
            line = volume[z, y]
            axes[0].plot(x, line, label=label)
            axes[1].plot(x, line / np.max(abs(line)), label=label)
        axes[0].set(
            title="Fixed catalogue-center x profile",
            xlabel="x (µm)",
            ylabel="relative intensity units",
        )
        axes[1].set(
            title="Separately peak-normalized profiles: shape only",
            xlabel="x (µm)",
            ylabel="each line / its own maximum absolute value",
        )
        for order in (1, 2):
            xp, yp = arrays[f"x{order}"], arrays[f"y{order}"]
            gain = _read_json(directory / "observed.json")["candidates"][0]["gains"][order - 1]
            axes[2].plot(abs(yp - _complex(gain) * xp), label=f"order {order}")
        axes[2].set(
            title="Cross-weighted overlap residual",
            xlabel="lexicographic fixed-Q sample",
            ylabel="absolute complex residual",
        )
        for ax in axes:
            ax.legend(fontsize=8)
        figure.savefig(directory / "profiles-and-overlap.png", dpi=170)
        plt.close(figure)
        landscape = _load_arrays(directory / "objective-landscape.npz")
        observed = _read_json(directory / "observed.json")["candidates"][0]
        figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
        nominal = np.asarray(metadata["initial_carriers_per_um"][0])
        fitted = np.asarray(observed["carrier_per_um"])
        maximum = float(np.max(landscape["joint_objective"]))
        for ax, key, label in zip(
            axes,
            ("joint_objective", "order2_objective"),
            ("Selected coupled J1 + J2", "Source-observation comparator: J2 only"),
            strict=True,
        ):
            artist = ax.pcolormesh(
                landscape["carrier_x_per_um"],
                landscape["carrier_y_per_um"],
                landscape[key],
                shading="nearest",
                vmin=0,
                vmax=maximum,
            )
            ax.plot(nominal[1], nominal[0], "wo", label="nominal metadata")
            ax.plot(fitted[1], fitted[0], "rx", label="joint product fit")
            ax.set(title=label, xlabel="kx (cycles/µm)", ylabel="ky (cycles/µm)")
            ax.legend(fontsize=8)
            figure.colorbar(artist, ax=ax, label="dimensionless normalized objective")
        figure.suptitle("Predeclared 9 × 9 box samples; same fixed Q; no measured legacy C parity")
        figure.savefig(directory / "objective-order-pairs.png", dpi=170)
        plt.close(figure)
    files = sorted(output.glob("*/*.png"))
    _write_json(
        output / "rendered.json",
        {
            "identity": _source_identity(),
            "observed_freeze_sha256": _hash(output / "observed-freeze.json"),
            "files": {str(p.relative_to(output)): _hash(p) for p in files},
            "matplotlib": importlib.import_module("matplotlib").__version__,
            "limits": (
                "Maximum-projection differences are differences of projections. Sections "
                "use predeclared catalogue planes. Only separately labelled profiles are "
                "shape normalized. Known-source prediction is evaluation, not specimen "
                "reconstruction."
            ),
        },
    )
    print(f"Rendered {len(files)} figures at {output}")


def main() -> None:
    """Run one explicit stage; observation requires a coordinator reference."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "observe", "render"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--authorization",
        default="",
        help="coordinator authorization evidence reference, required for observe",
    )
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.output)
    elif args.mode == "observe":
        observe(args.output, args.authorization)
    else:
        render(args.output)


if __name__ == "__main__":
    main()
