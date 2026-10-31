"""Observe and plot the independently declared RA08 finite-field comparison."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import runpy
from pathlib import Path
from typing import Any

import numpy as np


def _arrays(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key].copy() for key in archive.files}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _operator(module: Any, data: dict[str, Any]) -> Any:
    return module.build_finite_field_operator(
        kernel=data["kernel"],
        kernel_origin_zyx=tuple(int(v) for v in data["origin"]),
        illumination=data["illumination"],
        detector_crop_zyx=tuple(tuple(int(v) for v in row) for row in data["crop"]),
        input_taper=data["input_taper"],
        padding_shape_zyx=tuple(int(v) for v in data["padding"]),
        source_spacing_um_zyx=tuple(float(v) for v in data["spacing_um"]),
    )


def prepare_reference(destination: Path) -> None:
    """Reproduce the frozen A reference recipe without importing the solver."""
    destination.mkdir(parents=True, exist_ok=False)
    ref = runpy.run_path(
        str(Path(__file__).resolve().parents[1] / "tests/reference_alignment_ra08_fixture.py")
    )
    root = destination
    checks = ref["selfcheck"]()
    shape = (3, 3, 5)
    kernel = np.array(
        [[[0.1, 0.2, 0.05], [0.15, 0.8, 0.25]], [[0.03, 0.1, 0.04], [0.05, 0.2, 0.08]]]
    )
    origin = (0, 1, 1)
    illumination = np.ones((1, 2, *shape))
    illumination[0, 1] = 0.9 + 0.2 * np.indices(shape)[2] / 4
    crop = ((0, 3), (0, 3), (0, 5))
    source = np.zeros(shape)
    source[0, 0, 0] = 1.0
    source[1, 1, 2] = 0.7
    source[2, 2, 4] = 0.4
    finite = ref["finite_matrix"](kernel, origin, illumination, crop)
    periodic = ref["periodic_matrix"](kernel, origin, illumination)
    weights = np.ones((1, 2, *shape))
    images = (finite @ source.ravel()).reshape(weights.shape)
    alpha = 0.02
    h, b = ref["normal_system"](finite, weights, images, alpha)
    ridge = np.linalg.solve(h, b).reshape(shape)
    ridge_score = ref["score_reference"](finite, weights, ridge, images, alpha)
    periodic_h, periodic_b = ref["normal_system"](periodic, weights, images, alpha)
    periodic_ridge = np.linalg.solve(periodic_h, periodic_b).reshape(shape)
    periodic_score = ref["score_reference"](periodic, weights, periodic_ridge, images, alpha)
    spacing = np.array([0.4, 0.25, 0.15])
    center = (1, 1, 2)
    sections = {
        "section_z_um": np.arange(shape[0]) * spacing[0],
        "section_y_um": np.arange(shape[1]) * spacing[1],
        "section_x_um": np.arange(shape[2]) * spacing[2],
    }
    np.savez(
        root / "originals.npz",
        kernel=kernel,
        origin=origin,
        illumination=illumination,
        source=source,
        crop=crop,
        padding=(4, 4, 7),
        spacing_um=spacing,
        input_taper=weights,
        images=images,
        finite_matrix=finite,
        periodic_matrix=periodic,
        finite_fixed_source_prediction=images,
        periodic_fixed_source_prediction=(periodic @ source.ravel()).reshape(images.shape),
        alpha=alpha,
        ridge_source=ridge,
        periodic_ridge_source=periodic_ridge,
        ridge_gradient=ridge_score["gradient"],
        periodic_ridge_gradient=periodic_score["gradient"],
        ridge_residual=ridge_score["residual_images"],
        periodic_ridge_residual=periodic_score["residual_images"],
        center_zyx=center,
        **sections,
    )
    null_matrix = np.array([[1.0, 1.0]])
    np.savez(
        root / "nullspace.npz",
        matrix=null_matrix,
        source_a=[1.0, 0.0],
        source_b=[0.0, 1.0],
        observed=[1.0],
    )
    coarse = np.arange(5.0)
    fine = np.arange(17.0) / 4
    base = 1 + 0.1 * coarse
    alternate_coarse = base + 0.2 * np.sin(np.pi * coarse)
    alternate_fine = 1 + 0.1 * fine + 0.2 * np.sin(np.pi * fine)
    np.savez(
        root / "discretization.npz",
        coarse_coordinate=coarse,
        source_samples=base,
        alternate_samples=alternate_coarse,
        fine_coordinate=fine,
        interpolated_source=1 + 0.1 * fine,
        alternate_continuous_source=alternate_fine,
    )
    design = {
        "version": 1,
        "stage": "independently derived before any product observation",
        "units": {
            "source": "reference-flat-relative brightness per source voxel",
            "detector": "declared numeric detector signal",
            "coordinates": "micrometres",
            "alpha": "declared numeric gauge",
            "optimality": "gradient units",
        },
        "comparison": (
            "Same fixed source/kernel/illumination/observed finite data, "
            "identical alpha and crop; only exterior-zero versus periodic"
            " matrix changes. Both unconstrained ridge optima are compute"
            "d directly. No fit-centered sections or kernel equalization."
        ),
        "center_zyx": center,
        "section_definition": (
            "z[:,1,2], y[1,:,2], x[1,1,:]; index-zero coordinates times s"
            "pacing; q display at i/q without centering shifts"
        ),
        "objective": "||W(Ax-y)||^2/(2M) + alpha||x||^2/(2P)",
        "expected": {
            "finite_ridge_J": ridge_score["total_objective"],
            "periodic_ridge_J": periodic_score["total_objective"],
            "finite_ridge_rho": ref["optimality"](ridge, ridge_score["gradient"], False),
            "periodic_ridge_rho": ref["optimality"](
                periodic_ridge, periodic_score["gradient"], False
            ),
            "fixed_source_boundary_prediction_max_difference": float(
                np.max(np.abs((finite - periodic) @ source.ravel()))
            ),
            "finite_h_condition_inf": float(np.linalg.cond(h, np.inf)),
        },
        "limits": [
            "No solver trajectory oracle or finite-budget universal convergence claim.",
            (
                "Nonzero ridge source error is estimator bias, distinct from "
                "data residual and stationarity."
            ),
            (
                "nullspace.npz demonstrates equal observations for distinct s"
                "ources at alpha=0; no minimum-norm certificate."
            ),
            (
                "discretization.npz is an analytic sampling ambiguity witness"
                ", not an optical truth or continuum recovery oracle. Interpo"
                "lation does not remove its between-sample discrepancy."
            ),
            (
                "Exterior-zero is a declared model assumption, "
                "not established physical exterior truth."
            ),
            "No observed product output exists in these originals.",
        ],
        "tolerance": (
            "2048*eps*term_count*max(1, reference scale); tiny solution e"
            "rror additionally bounded by ||H^-1||inf times stationarity "
            "threshold, not float32 tolerances"
        ),
    }
    (root / "design.json").write_text(json.dumps(design, indent=2) + "\n")
    (root / "selfcheck.json").write_text(json.dumps(checks, indent=2) + "\n")
    controls = []
    tiny_spec = ref["tiny"]()
    tiny_a = ref["matrix_for"](tiny_spec)
    for source_values in ([1.0, -2.0, 1.0], [1.0, 0.7, 1.3]):
        tiny_y = (tiny_a @ source_values).reshape(tiny_spec["input_taper"].shape)
        for alpha_control in (0.0, 0.2):
            tiny_h, tiny_b = ref["normal_system"](
                tiny_a, tiny_spec["input_taper"], tiny_y, alpha_control
            )
            for constrained in (False, True):
                optimum = ref["exact_minimizer"](tiny_h, tiny_b, constrained)
                scored = ref["score_reference"](
                    tiny_a,
                    tiny_spec["input_taper"],
                    optimum.reshape(1, 1, 3),
                    tiny_y,
                    alpha_control,
                )
                controls.append(
                    {
                        "source_values": source_values,
                        "alpha": alpha_control,
                        "nonnegative": constrained,
                        "images": tiny_y.tolist(),
                        "H": tiny_h.tolist(),
                        "b": tiny_b.tolist(),
                        "optimum": optimum.tolist(),
                        "lambda_min": float(np.linalg.eigvalsh(tiny_h)[0]),
                        "condition_inf": float(np.linalg.cond(tiny_h, np.inf)),
                        "objective": scored["total_objective"],
                        "gradient": scored["gradient"].tolist(),
                        "rho": ref["optimality"](
                            optimum.reshape(1, 1, 3), scored["gradient"], constrained
                        ),
                        "atol": ref["ATOL"],
                        "rtol": ref["RTOL"],
                        "budget": ref["BUDGET"],
                    }
                )
    (root / "tiny-controls.json").write_text(json.dumps(controls, indent=2) + "\n")
    geometry = ref["geometry"]()
    geometry_a = ref["matrix_for"](geometry)
    geometry_x = np.linspace(-1.1, 1.7, 12).reshape(2, 2, 3)
    geometry_detector = np.linspace(0.9, -0.7, 16).reshape(geometry["input_taper"].shape)
    np.savez(
        root / "small-finite-control.npz",
        **geometry,
        matrix=geometry_a,
        source=geometry_x,
        detector=geometry_detector,
        prediction=(geometry_a @ geometry_x.ravel()).reshape(geometry_detector.shape),
        adjoint=(geometry_a.T @ geometry_detector.ravel()).reshape(geometry_x.shape),
    )
    assert np.max(np.abs((finite - periodic) @ source.ravel())) > 0.1
    assert np.max(np.abs(ridge_score["gradient"])) < 1e-14
    assert np.max(np.abs(periodic_score["gradient"])) < 1e-14
    np.testing.assert_allclose(alternate_coarse, base, atol=1e-15, rtol=0)
    print("Independent references and oracle selfchecks saved; no product import.")
    # This second source/detector sum is separate from the fixture matrix helper.
    probe = np.random.default_rng(808).normal(size=images.shape)
    prediction = np.zeros_like(images)
    backprojection = np.zeros_like(source)
    for exposure in np.ndindex(*illumination.shape[:2]):
        for local in np.ndindex(*images.shape[-3:]):
            detector = tuple(crop[axis][0] + local[axis] for axis in range(3))
            total = 0.0
            for point in np.ndindex(*source.shape):
                lag = tuple(detector[axis] - point[axis] + origin[axis] for axis in range(3))
                if all(0 <= lag[axis] < kernel.shape[axis] for axis in range(3)):
                    coefficient = kernel[lag] * illumination[exposure + point]
                    total += coefficient * source[point]
                    backprojection[point] += coefficient * probe[exposure + local]
            prediction[exposure + local] = total
    np.savez(
        root / "crosscheck.npz",
        fixed_source_prediction=prediction,
        adjoint_probe=probe,
        adjoint_expected=backprojection,
        constrained_images=np.array([-1.0, 2.0]).reshape(1, 1, 1, 1, 2),
        constrained_alpha=np.array(0.25),
        constrained_expected=np.array([[[0.0, 1.6]]]),
        unconstrained_expected=np.array([[[-0.8, 1.6]]]),
    )


def observe(reference: Path, crosscheck: Path, destination: Path) -> None:
    """Save actual outputs and independent final objective/stationarity checks."""
    destination.mkdir(parents=True, exist_ok=False)
    data = _arrays(reference / "originals.npz")
    control = _arrays(crosscheck)
    module = importlib.import_module("scripts.finite_field_reconstruction")
    operator = _operator(module, data)
    prediction = module.finite_field_forward(operator, data["source"])
    backprojection = module.finite_field_adjoint(operator, control["adjoint_probe"])
    alpha = float(data["alpha"])
    atol, rtol, budget = 1e-11, 1e-9, 10000
    fit = module.solve_finite_field(
        operator,
        images=data["images"],
        regularization=alpha,
        nonnegative=False,
        max_iterations=budget,
        absolute_tolerance=atol,
        relative_tolerance=rtol,
        output_taper=np.ones(data["source"].shape),
        output_zoom=1,
    )
    matrix, weights = data["finite_matrix"], data["input_taper"].ravel()
    x, y = fit.source.ravel(), data["images"].ravel()
    residual = matrix @ x - y
    gradient = matrix.T @ (weights**2 * residual) / y.size + alpha * x / x.size
    hessian = (matrix.T * weights**2) @ matrix / y.size + np.eye(x.size) * alpha / x.size
    expected_gradient_scale = float(np.max(np.abs(matrix.T @ (weights**2 * y) / y.size)))
    threshold = atol + rtol * expected_gradient_scale
    arithmetic_budget = 2048 * np.finfo(float).eps * matrix.shape[0] * max(1.0, np.max(np.abs(y)))
    source_error_bound = float(np.linalg.norm(np.linalg.inv(hessian), ord=np.inf)) * (
        threshold + arithmetic_budget
    )
    source_error = float(np.max(np.abs(x - data["ridge_source"].ravel())))
    checked_objective = float(
        np.sum((weights * residual) ** 2) / (2 * y.size) + alpha * np.sum(x**2) / (2 * x.size)
    )
    gradient_scale = max(
        float(
            np.max(
                np.abs(matrix).T @ (weights**2 * (np.abs(matrix) @ np.abs(x) + np.abs(y))) / y.size
                + alpha * np.abs(x) / x.size
            )
        ),
        float(np.max(np.abs(matrix).T @ (weights**2 * np.abs(y)) / y.size)),
    )
    gradient_roundoff = 64 * np.finfo(float).eps * (x.size + y.size) * gradient_scale
    checks = {
        "forward_max_error": float(np.max(np.abs(prediction - control["fixed_source_prediction"]))),
        "adjoint_max_error": float(np.max(np.abs(backprojection - control["adjoint_expected"]))),
        "gradient_max_error": float(np.max(np.abs(fit.gradient.ravel() - gradient))),
        "objective_error": abs(fit.total_objective - checked_objective),
        "independent_optimality_residual": float(np.max(np.abs(gradient))),
        "reported_optimality_residual": fit.optimality_residual,
        "stopping_threshold": fit.stopping_threshold,
        "independent_stopping_threshold": threshold,
        "source_error_against_discrete_ridge": source_error,
        "independent_stationarity_source_bound": source_error_bound,
        "arithmetic_allowance": float(arithmetic_budget),
        "independent_gradient_roundoff_allowance": gradient_roundoff,
    }
    for key in ("forward_max_error", "adjoint_max_error", "gradient_max_error", "objective_error"):
        if checks[key] > arithmetic_budget:
            raise AssertionError(f"Independent {key} exceeded predeclared binary64 allowance")
    if not fit.converged or fit.status != "converged":
        raise AssertionError(f"Finite observation stopped without stationarity: {fit.status}")
    if abs(fit.stopping_threshold - threshold) > 64 * np.finfo(float).eps * threshold:
        raise AssertionError("Reported threshold does not match the declared relative rule")
    if abs(fit.optimality_residual - checks["independent_optimality_residual"]) > gradient_roundoff:
        raise AssertionError("Reported stationarity does not match the independent gradient")
    if checks["independent_optimality_residual"] > threshold + gradient_roundoff:
        raise AssertionError("Independent gradient does not support mathematical stopping")
    if source_error > source_error_bound:
        raise AssertionError("Source differs from exact discrete ridge beyond stationarity bound")
    tiny = module.build_finite_field_operator(
        kernel=np.ones((1, 1, 1)),
        kernel_origin_zyx=(0, 0, 0),
        illumination=np.ones((1, 1, 1, 1, 2)),
        detector_crop_zyx=((0, 1), (0, 1), (0, 2)),
        input_taper=np.ones((1, 1, 1, 1, 2)),
        padding_shape_zyx=(1, 1, 2),
        source_spacing_um_zyx=(0.2, 0.1, 0.1),
    )
    constrained: dict[str, Any] = {}
    saved = {
        "fixed_source_prediction": prediction,
        "adjoint_prediction": backprojection,
        "source": fit.source,
        "output": fit.output,
        "predicted_images": fit.predicted_images,
        "residual_images": fit.residual_images,
        "gradient": fit.gradient,
        "objective_history": fit.objective_history,
        "optimality_history": fit.optimality_history,
    }
    stopped = module.solve_finite_field(
        operator,
        images=data["images"],
        regularization=alpha,
        nonnegative=False,
        max_iterations=0,
        absolute_tolerance=atol,
        relative_tolerance=rtol,
        output_taper=np.ones(data["source"].shape),
        output_zoom=1,
    )
    if (
        stopped.converged
        or stopped.status != "iteration_limit"
        or stopped.iterations != 0
        or np.any(stopped.source)
        or stopped.optimality_residual <= stopped.stopping_threshold
    ):
        raise AssertionError(
            "Zero-budget control did not distinguish resource stop from convergence"
        )
    saved["zero_budget_objective_history"] = stopped.objective_history
    saved["zero_budget_optimality_history"] = stopped.optimality_history
    for positive, name in ((False, "unconstrained"), (True, "constrained")):
        example = module.solve_finite_field(
            tiny,
            images=control["constrained_images"],
            regularization=float(control["constrained_alpha"]),
            nonnegative=positive,
            max_iterations=1000,
            absolute_tolerance=1e-12,
            relative_tolerance=1e-10,
            output_taper=np.ones((1, 1, 2)),
            output_zoom=1,
        )
        if (
            not example.converged
            or np.max(np.abs(example.source - control[name + "_expected"])) > 1e-8
        ):
            raise AssertionError(f"Analytic {name} comparison failed")
        constrained[name] = {
            "status": example.status,
            "iterations": example.iterations,
            "source": example.source.tolist(),
            "objective": example.total_objective,
            "optimality_residual": example.optimality_residual,
            "threshold": example.stopping_threshold,
        }
        saved[name + "_source"] = example.source
        saved[name + "_objective_history"] = example.objective_history
        saved[name + "_optimality_history"] = example.optimality_history
    np.savez(destination / "observed.npz", **saved)
    null = _arrays(reference / "nullspace.npz")
    ambiguity = _arrays(reference / "discretization.npz")
    summary = {
        "stage": "actual product observations, after independent original expectations",
        "inputs": {
            str(path): _digest(path)
            for path in (reference / "originals.npz", reference / "design.json", crosscheck)
        },
        "settings": {
            "absolute_tolerance": atol,
            "relative_tolerance": rtol,
            "max_iterations": budget,
        },
        "status": fit.status,
        "iterations": fit.iterations,
        "objective": fit.total_objective,
        "independent_checks": checks,
        "fixed_source_boundary_prediction_max_difference": float(
            np.max(np.abs(prediction - data["periodic_fixed_source_prediction"]))
        ),
        "finite_estimator_source_error_against_known_source": float(
            np.linalg.norm(fit.source - data["source"])
        ),
        "periodic_estimator_source_error_against_same_known_source": float(
            np.linalg.norm(data["periodic_ridge_source"] - data["source"])
        ),
        "nullspace_source_distance": float(np.linalg.norm(null["source_a"] - null["source_b"])),
        "nullspace_prediction_distance": float(
            np.linalg.norm(null["matrix"] @ (null["source_a"] - null["source_b"]))
        ),
        "sampling_ambiguity_between_sample_max_difference": float(
            np.max(
                np.abs(ambiguity["alternate_continuous_source"] - ambiguity["interpolated_source"])
            )
        ),
        "active_constraint_comparison": constrained,
        "zero_budget_control": {
            "status": stopped.status,
            "converged": stopped.converged,
            "iterations": stopped.iterations,
            "objective": stopped.total_objective,
            "optimality_residual": stopped.optimality_residual,
            "threshold": stopped.stopping_threshold,
        },
        "limits": json.loads((reference / "design.json").read_text())["limits"],
    }
    (destination / "observation.json").write_text(json.dumps(summary, indent=2) + "\n")


def render(reference: Path, observation: Path, destination: Path) -> None:
    """Plot stored observations without recomputing the product or references."""
    destination.mkdir(parents=True, exist_ok=False)
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")
    data, actual = _arrays(reference / "originals.npz"), _arrays(observation / "observed.npz")
    summary = json.loads((observation / "observation.json").read_text())
    center = tuple(int(v) for v in data["center_zyx"])
    z, y, _ = center
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "savefig.dpi": 180})
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.3), layout="constrained")
    spacing = data["spacing_um"]
    extent = (
        -spacing[2] / 2,
        (data["source"].shape[2] - 0.5) * spacing[2],
        -spacing[1] / 2,
        (data["source"].shape[1] - 0.5) * spacing[1],
    )
    panels = [
        (
            axes[0, 0],
            data["source"].max(axis=0),
            "Fixed source (maximum over z)",
            "native source brightness",
        ),
        (
            axes[0, 1],
            actual["fixed_source_prediction"][0, 0].max(axis=0),
            "Zero-exterior prediction (maximum over z)",
            "detector signal",
        ),
        (
            axes[0, 2],
            (
                data["periodic_fixed_source_prediction"][0, 0].max(axis=0)
                - actual["fixed_source_prediction"][0, 0].max(axis=0)
            ),
            "Periodic minus finite z-maximum projections",
            "detector signal difference",
        ),
    ]
    for ax, image, title, units in panels:
        signed = ax is axes[0, 2]
        limit = float(np.max(np.abs(image)))
        im = ax.imshow(
            image,
            origin="lower",
            extent=extent,
            cmap="RdBu_r" if signed else "viridis",
            vmin=-limit if signed else 0,
            vmax=limit,
        )
        ax.set(title=title, xlabel="x (µm)", ylabel="y (µm)")
        fig.colorbar(im, ax=ax, label=units, shrink=0.8)
    ax = axes[1, 0]
    for source, label, style in (
        (data["source"], "Known discrete source", "o-"),
        (actual["source"], "Finite-field ridge", "s--"),
        (data["periodic_ridge_source"], "Periodic ridge control", "^:"),
    ):
        ax.plot(data["section_x_um"], source[z, y, :], style, label=label, markersize=4)
    ax.set(
        title=f"Fixed x section: z={z}, y={y}", xlabel="x (µm)", ylabel="native source brightness"
    )
    ax.legend(fontsize=8)
    history = actual["objective_history"]
    ax = axes[1, 1]
    ax.semilogy(np.arange(history.size), history, label="Actual finite solver")
    design = json.loads((reference / "design.json").read_text())
    ax.axhline(
        design["expected"]["finite_ridge_J"], color="black", ls="--", label="Direct finite optimum"
    )
    ax.set(
        title="Declared objective",
        xlabel="Accepted source updates",
        ylabel="J (declared numeric gauge)",
    )
    ax.legend(fontsize=8)
    ax = axes[1, 2]
    rho = actual["optimality_history"]
    ax.semilogy(
        np.arange(rho.size), np.maximum(rho, np.finfo(float).tiny), label="Actual gradient ∞-norm"
    )
    threshold = summary["independent_checks"]["stopping_threshold"]
    ax.axhline(threshold, color="black", ls="--", label="Declared stopping threshold")
    ax.set(
        title=f"Stationarity: {summary['status']}",
        xlabel="Accepted source updates",
        ylabel="Gradient units",
    )
    ax.legend(fontsize=8)
    fig.suptitle("RA08: matched finite boundaries and a measured stopping criterion", fontsize=13)
    for suffix in ("png", "pdf"):
        fig.savefig(destination / f"finite-boundaries.{suffix}")
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2), layout="constrained")
    for axis, ax in enumerate(axes):
        selection: list[Any] = list(center)
        selection[axis] = slice(None)
        index = tuple(selection)
        label = "zyx"[axis]
        for source, name, style in (
            (data["source"], "Known source", "o-"),
            (actual["source"], "Finite ridge", "s--"),
            (data["periodic_ridge_source"], "Periodic control", "^:"),
        ):
            ax.plot(data[f"section_{label}_um"], source[index], style, label=name, markersize=4)
        ax.set(
            title=f"Fixed {label} section",
            xlabel=f"{label} (µm)",
            ylabel="native source brightness",
        )
    axes[-1].legend(fontsize=8)
    fig.suptitle(f"Sections cross fixed index {center}; no fitted recentering")
    for suffix in ("png", "pdf"):
        fig.savefig(destination / f"fixed-sections.{suffix}")
    plt.close(fig)
    (destination / "render.json").write_text(
        json.dumps(
            {
                "reference_sha256": _digest(reference / "originals.npz"),
                "observation_sha256": _digest(observation / "observed.npz"),
                "summary_sha256": _digest(observation / "observation.json"),
                "matplotlib": matplotlib.__version__,
                "figures": {
                    p.name: _digest(p) for p in sorted(destination.glob("*")) if p.is_file()
                },
                "limits": (
                    "Stored observed arrays; per-panel color scales labeled; "
                    "no recentering or physical resolution claim."
                ),
            },
            indent=2,
        )
        + "\n"
    )


def main() -> None:
    """Run one explicitly selected observation or rendering stage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "observe", "render"))
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--crosscheck", type=Path)
    parser.add_argument("--observation", type=Path)
    args = parser.parse_args()
    if args.stage == "prepare":
        prepare_reference(args.destination)
        return
    if args.reference is None:
        parser.error("observe/render require --reference")
    if args.stage == "observe":
        if args.crosscheck is None:
            parser.error("observe requires --crosscheck")
        observe(args.reference, args.crosscheck, args.destination)
    else:
        if args.observation is None:
            parser.error("render requires --observation")
        render(args.reference, args.observation, args.destination)


if __name__ == "__main__":
    main()
