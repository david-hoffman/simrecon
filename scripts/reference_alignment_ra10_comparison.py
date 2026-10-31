"""Prepare independent finite RA10 observations, freeze fits, then render evidence.

Preparation does not import the product. Observation freezes every candidate
before loading evaluator truth. Rendering never reruns inference.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHAPE = (3, 4, 5)
SPACING = (0.25, 0.5, 0.5)
ORIGIN = (1, 1, 1)
CROP = ((0, 3), (0, 4), (0, 5))
CARRIER = np.array((0.28 / 2.0, 0.42 / 2.5))
CATALOGUE = (
    ((0.375, 1.15, 1.55), (0.22, 0.48, 0.45), 1.0),
    ((0.26, 0.55, 0.65), (0.18, 0.32, 0.33), 0.65),
    ((0.51, 1.55, 0.50), (0.15, 0.26, 0.28), 0.45),
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _arrays(path: Path) -> dict[str, Any]:
    with np.load(path, allow_pickle=False) as stored:
        return {name: stored[name].copy() for name in stored.files}


def _matrix(kernels: Any, phases: Any) -> Any:
    """Assemble the raw finite real matrix by explicit detector/source sums."""
    sites = list(np.ndindex(SHAPE))
    result = np.zeros((len(phases), len(sites), len(sites)))
    for j, detector in enumerate(sites):
        for q, source in enumerate(sites):
            lag = tuple(detector[a] - source[a] + ORIGIN[a] for a in range(3))
            if any(v < 0 or v >= kernels.shape[a + 1] for a, v in enumerate(lag)):
                continue
            theta = (
                2
                * np.pi
                * (CARRIER[0] * source[1] * SPACING[1] + CARRIER[1] * source[2] * SPACING[2])
            )
            k0, k1, k2 = kernels[(slice(None), *lag)]
            for p, phase in enumerate(phases):
                z = np.exp(1j * (theta + phase))
                result[p, j, q] = k0.real + 2 * (k1 * z + k2 * z * z).real
    return result


def _profile(kernels: Any, phases: Any, images: Any, covariance: Any, mask: Any) -> Any:
    """Recompute the complete whitened truncated-source objective independently."""
    a = _matrix(kernels, phases)[:, mask.ravel(), :]
    n, d, p = a.shape
    chol = np.linalg.cholesky(covariance)
    b = np.linalg.solve(chol, a.reshape(n, -1)).reshape(n * d, p)
    y = np.linalg.solve(chol, images.reshape(n, -1)[:, mask.ravel()]).ravel()
    u, singular, vh = np.linalg.svd(b, full_matrices=False)
    keep = singular > 1e-10 * singular[0]
    source = (vh[keep].T / singular[keep]) @ (u[:, keep].T @ y)
    residual = b @ source - y
    return float(residual @ residual / (2 * n * d)), source


def prepare(directory: Path) -> None:
    """Seal inputs and a separate evaluator catalogue without product imports."""
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError("Preparation requires an empty output directory")
    coordinates = (np.indices(SHAPE).astype(float) + 0.5) * np.array(SPACING)[:, None, None, None]
    source = np.zeros(SHAPE)
    for center, sigma, amplitude in CATALOGUE:
        delta = (coordinates - np.array(center)[:, None, None, None]) / np.array(sigma)[
            :, None, None, None
        ]
        source += amplitude * np.exp(-0.5 * np.sum(delta * delta, axis=0))
    kernels = np.zeros((3, 3, 3, 3), dtype=complex)
    kernels[0, 1, 1, 1] = 0.70
    kernels[0, 1, 1, 0] = 0.11
    kernels[0, 1, 0, 1] = 0.09
    kernels[0, 0, 1, 1] = 0.06
    kernels[0, 2, 1, 1] = 0.04
    kernels[1, 1, 1, 1] = 0.30 * np.exp(0.22j)
    kernels[1, 1, 1, 2] = 0.06 * np.exp(-0.31j)
    kernels[1, 2, 1, 1] = 0.03 * np.exp(0.14j)
    kernels[2, 1, 1, 1] = 0.12 * np.exp(-0.31j)
    kernels[2, 1, 2, 1] = 0.035 * np.exp(0.17j)
    commands = 2 * np.pi * np.arange(7) / 7
    independent = commands + 0.17 + np.array((0, 0.07, -0.05, 0.09, -0.04, -0.03, 0.06))
    common = commands + 0.17
    mask = np.ones(SHAPE, dtype=bool)
    mask[:, 1::2, 1::2] = False
    covariance = 0.002**2 * (np.eye(7) + 0.08 * np.ones((7, 7)))
    clean = (_matrix(kernels, independent) @ source.ravel()).reshape((7, *SHAPE))
    common_images = (_matrix(kernels, common) @ source.ravel()).reshape((7, *SHAPE))
    mismatch_kernels = kernels.copy()
    mismatch_kernels[1] *= np.exp(0.05j)
    mismatch_kernels[2] *= np.exp(-0.07j)
    mismatch = (_matrix(mismatch_kernels, independent) @ source.ravel()).reshape((7, *SHAPE))
    white_noise = np.random.default_rng(2026103111).normal(size=(7, int(np.prod(SHAPE))))
    noise = (np.linalg.cholesky(covariance) @ white_noise).reshape(clean.shape)
    weak_kernels = kernels.copy()
    weak_kernels[1:] *= 1e-3
    weak = (_matrix(weak_kernels, independent) @ source.ravel()).reshape((7, *SHAPE))
    zero_kernels = kernels.copy()
    zero_kernels[1:] = 0
    zero = (_matrix(zero_kernels, independent) @ source.ravel()).reshape((7, *SHAPE))
    halfturn_kernels = kernels.copy()
    halfturn_kernels[1] = 0
    halfturn = (_matrix(halfturn_kernels, commands) @ source.ravel()).reshape((7, *SHAPE))
    five_phases = 2 * np.pi * np.arange(5) / 5
    five_images = (_matrix(kernels, five_phases) @ source.ravel()).reshape(5, -1)

    def design(phases: Any) -> Any:
        return np.column_stack(
            (
                np.ones(len(phases)),
                np.cos(phases),
                np.sin(phases),
                np.cos(2 * phases),
                np.sin(2 * phases),
            )
        )

    # This free coefficient fit is an explicit ambiguity demonstration, not RA10 inference.
    alternative5 = design(2 * five_phases)
    five_prediction = alternative5 @ np.linalg.solve(alternative5, five_images)
    alternative7 = design(2 * commands)
    seven_prediction = (
        alternative7 @ np.linalg.lstsq(alternative7, common_images.reshape(7, -1), rcond=1e-10)[0]
    )
    _json(
        directory / "free-band-ambiguity.json",
        {
            "five_frame_alternative_max_absolute_residual": float(
                np.max(np.abs(five_prediction - five_images))
            ),
            "seven_frame_doubled_command_relative_residual": float(
                np.linalg.norm(seven_prediction - common_images.reshape(7, -1))
                / np.linalg.norm(common_images)
            ),
            "limit": (
                "Unrestricted coefficient images; alternative order relabelling can fit five "
                "frames. "
                "Redundancy rejects this chosen alternative only, not all aliases."
            ),
        },
    )
    np.savez(
        directory / "inputs.npz",
        kernels=kernels,
        commands=commands,
        supplied_monitor_phases=independent,
        mask=mask,
        covariance=covariance,
        independent_clean=clean,
        independent_noise=clean + noise,
        common_clean=common_images,
        independent_mismatch=mismatch,
        weak=weak,
        weak_kernels=weak_kernels,
        zero=zero,
        zero_kernels=zero_kernels,
        halfturn=halfturn,
        halfturn_kernels=halfturn_kernels,
    )
    np.savez(
        directory / "evaluation-only.npz",
        source=source,
        actual=independent,
        common=common,
        mismatch_generation_kernels=mismatch_kernels,
    )
    (directory / "driver-preparation.py").write_bytes(Path(__file__).read_bytes())
    # Nearest stored display center; first index wins an exact tie.
    sections = tuple(
        int(np.argmin(np.abs((np.arange(SHAPE[a]) + 0.5) * SPACING[a] - CATALOGUE[0][0][a])))
        for a in range(3)
    )
    _json(
        directory / "preparation.json",
        {
            "schema": "ra10-independent-finite-inputs-v1",
            "shape_zyx": SHAPE,
            "spacing_um_zyx": SPACING,
            "carrier_per_um_yx": CARRIER.tolist(),
            "kernel_origin_zyx": ORIGIN,
            "crop": CROP,
            "catalogue": CATALOGUE,
            "section_zyx": sections,
            "phase_origin": "source index zero; display centers are half a cell later",
            "starts": "zero offsets from nominal commands; no evaluator source supplied",
            "inferred_offset_bounds_rad": [-0.4, 0.4],
            "halfturn_starts_rad": [0, float(np.pi)],
            "halfturn_bounds_rad": [0, float(np.pi)],
            "difference_step_rad": 1e-4,
            "gradient_tolerance": 1e-9,
            "max_evaluations": 256,
            "source_rtol": 1e-10,
            "phase_rank_rtol": 1e-6,
            "noise_base_standard_deviation": 0.002,
            "noise_covariance": "4e-6*(I+0.08*ones); identical to supplied weighting covariance",
            "noise_seed": 2026103111,
            "mismatch": (
                "Data use first/second kernels times exp(0.05i)/exp(-0.07i); inference "
                "keeps the original kernels. No common gauge rotation matches both. "
                "No recovery goal applies to this deliberately miscalibrated case."
            ),
            "conditional_clean_phase_goal_rad": 0.03,
            "goal_scope": "independent-clean informative nominal-start control only",
            "input_sha256": _hash(directory / "inputs.npz"),
            "evaluation_sha256": _hash(directory / "evaluation-only.npz"),
            "benchmark_sha256": _hash(ROOT / "docs/benchmarks/reference-alignment-v1.json"),
            "driver_sha256": _hash(Path(__file__)),
        },
    )


def observe(directory: Path, authorization: str) -> None:
    """Freeze all public outputs before reading truth for independent evaluation."""
    if authorization != "RA10 coordinator authorizes these sealed observations":
        raise ValueError("Explicit observation authorization required")
    if (directory / "observed-freeze.json").exists():
        raise ValueError("Refusing to replace frozen observations")
    meta = json.loads((directory / "preparation.json").read_text())
    if _hash(directory / "inputs.npz") != meta["input_sha256"]:
        raise ValueError("Sealed input identity changed")
    arrays = _arrays(directory / "inputs.npz")
    product = importlib.import_module("simrecon")
    plans = (
        ("known", "independent_clean", "kernels", "known"),
        ("common-control", "common_clean", "kernels", "common"),
        ("common-on-independent", "independent_clean", "kernels", "common"),
        ("independent-clean", "independent_clean", "kernels", "independent"),
        ("common-noise", "independent_noise", "kernels", "common"),
        ("independent-noise", "independent_noise", "kernels", "independent"),
        ("independent-mismatch", "independent_mismatch", "kernels", "independent"),
        ("weak", "weak", "weak_kernels", "independent"),
        ("zero-side", "zero", "zero_kernels", "independent"),
        ("halfturn", "halfturn", "halfturn_kernels", "independent"),
    )
    results: dict[str, Any] = {}
    saves: dict[str, Any] = {}
    for name, data_key, kernel_key, mode in plans:
        q = 0 if mode == "known" else (1 if mode == "common" else 7)
        starts = np.zeros((1, q))
        bounds = np.tile(np.array((-0.4, 0.4))[:, None], (1, q))
        if name == "halfturn":
            starts = np.stack((np.zeros(q), np.full(q, np.pi)))
            bounds = np.stack((np.zeros(q), np.full(q, np.pi)))
        result = product.fit_exposure_phases(
            arrays[data_key],
            order_kernels=arrays[kernel_key],
            kernel_origin_zyx=ORIGIN,
            source_shape_zyx=SHAPE,
            detector_crop_zyx=CROP,
            source_spacing_um_zyx=SPACING,
            carrier_per_um_yx=CARRIER.copy(),
            exposure_covariance=arrays["covariance"],
            fit_mask=arrays["mask"],
            phases_rad=arrays["supplied_monitor_phases"] if mode == "known" else arrays["commands"],
            mode=mode,
            initial_offsets_rad=starts,
            offset_bounds_rad=bounds,
            difference_step_rad=np.full(q, 1e-4),
            source_rtol=1e-10,
            phase_rank_rtol=1e-6,
            gradient_tolerance=1e-9,
            max_evaluations=256,
        )
        rows = []
        for index, candidate in enumerate(result.candidates):
            row: dict[str, Any] = {}
            for field in candidate.__dataclass_fields__:
                value = getattr(candidate, field)
                if isinstance(value, np.ndarray):
                    saves[f"{name}__{index}__{field}"] = value
                    row[field] = {"saved_array": f"{name}__{index}__{field}"}
                else:
                    row[field] = value
            rows.append(row)
        results[name] = {"mode": mode, "data_key": data_key, "kernel_key": kernel_key, "rows": rows}
    np.savez(directory / "observed-arrays.npz", **saves)
    _json(directory / "observed-scalars.json", results)
    runtime = {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": importlib.import_module("scipy").__version__,
        "source_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_status": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "implementation_sha256": _hash(ROOT / "src/simrecon/exposure_phase.py"),
        "driver_sha256": _hash(Path(__file__)),
        "material_sha256": {
            name: _hash(ROOT / name)
            for name in (
                "src/simrecon/__init__.py",
                "docs/contracts/reference-alignment-ra10-v1.md",
                "uv.lock",
                "pyproject.toml",
                ".python-version",
            )
        },
    }
    freeze = {
        "inputs_sha256": _hash(directory / "inputs.npz"),
        "preparation_sha256": _hash(directory / "preparation.json"),
        "observed_arrays_sha256": _hash(directory / "observed-arrays.npz"),
        "observed_scalars_sha256": _hash(directory / "observed-scalars.json"),
        "runtime": runtime,
        "evaluation_input_sha256_predeclared": meta["evaluation_sha256"],
        "evaluation_truth_loaded_before_this_freeze": False,
    }
    _json(directory / "observed-freeze.json", freeze)
    if _hash(directory / "evaluation-only.npz") != meta["evaluation_sha256"]:
        raise ValueError("Sealed evaluator identity changed; frozen observations retained")
    truth = _arrays(directory / "evaluation-only.npz")
    evaluations = {}
    for name, info in results.items():
        rows = []
        for index, row in enumerate(info["rows"]):
            phases = saves[f"{name}__{index}__phases_rad"]
            profiled_objective, source = _profile(
                arrays[info["kernel_key"]],
                phases,
                arrays[info["data_key"]],
                arrays["covariance"],
                arrays["mask"],
            )
            product_source = saves[f"{name}__{index}__source"]
            prediction = saves[f"{name}__{index}__predicted_images"]
            raw_forward = (
                _matrix(arrays[info["kernel_key"]], phases) @ product_source.ravel()
            ).reshape((7, *SHAPE))
            reference = arrays[info["data_key"]]
            held = ~arrays["mask"]
            whitened = np.linalg.solve(
                np.linalg.cholesky(arrays["covariance"]),
                (raw_forward - reference)[:, arrays["mask"]],
            )
            objective = float(np.sum(whitened * whitened) / (2 * whitened.size))
            actual = truth["common"] if name == "common-control" else truth["actual"]
            if name == "halfturn":
                actual = arrays["commands"]
            error = np.angle(np.exp(1j * (phases - actual)))
            rows.append(
                {
                    "objective_independent": objective,
                    "profiled_objective_independent": profiled_objective,
                    "objective_absolute_difference": abs(objective - row["objective"]),
                    "source_max_absolute_difference": float(
                        np.max(np.abs(source.reshape(SHAPE) - product_source))
                    ),
                    "prediction_max_absolute_difference": float(
                        np.max(np.abs(raw_forward - prediction))
                    ),
                    "residual_max_absolute_difference": float(
                        np.max(
                            np.abs(
                                saves[f"{name}__{index}__residual_images"]
                                - (prediction - reference)
                            )
                        )
                    ),
                    "heldout_relative_error": float(
                        np.linalg.norm((prediction - reference)[:, held])
                        / np.linalg.norm(reference[:, held])
                    ),
                    "full_relative_error": float(
                        np.linalg.norm(prediction - reference) / np.linalg.norm(reference)
                    ),
                    "max_wrapped_phase_error_rad": float(np.max(np.abs(error))),
                    "phase_goal_applies": name == "independent-clean",
                    "phase_goal_passed": bool(np.max(np.abs(error)) <= 0.03)
                    if name == "independent-clean"
                    else None,
                }
            )
        evaluations[name] = rows
    _json(
        directory / "evaluation.json",
        {
            "observation_freeze_sha256": _hash(directory / "observed-freeze.json"),
            "evaluation_input_sha256": _hash(directory / "evaluation-only.npz"),
            "results": evaluations,
            "limits": (
                "Conditional synthetic finite model; masked pixels, not unseen independent "
                "phase labels; no physical uniqueness or real-data claim"
            ),
        },
    )


def render(directory: Path, output: Path) -> None:
    """Render fixed planes/scales and phase/prediction comparisons from saved fits."""
    matplotlib = importlib.import_module("matplotlib")
    matplotlib.use("Agg")
    plt = importlib.import_module("matplotlib.pyplot")

    meta = json.loads((directory / "preparation.json").read_text())
    freeze = json.loads((directory / "observed-freeze.json").read_text())
    evaluation = json.loads((directory / "evaluation.json").read_text())
    expected = {
        "inputs.npz": freeze["inputs_sha256"],
        "preparation.json": freeze["preparation_sha256"],
        "observed-arrays.npz": freeze["observed_arrays_sha256"],
        "observed-scalars.json": freeze["observed_scalars_sha256"],
        "evaluation-only.npz": meta["evaluation_sha256"],
        "observed-freeze.json": evaluation["observation_freeze_sha256"],
    }
    if any(_hash(directory / name) != digest for name, digest in expected.items()):
        raise ValueError("Saved observation/evaluation identity changed; rendering stopped")
    if (
        meta["input_sha256"] != freeze["inputs_sha256"]
        or evaluation["evaluation_input_sha256"] != meta["evaluation_sha256"]
    ):
        raise ValueError("Preparation/freeze/evaluation associations differ")
    output.mkdir(parents=True, exist_ok=True)
    arrays = _arrays(directory / "inputs.npz")
    truth = _arrays(directory / "evaluation-only.npz")
    fitted = _arrays(directory / "observed-arrays.npz")
    scalar = json.loads((directory / "observed-scalars.json").read_text())
    figures = []

    def save(fig: Any, name: str) -> None:
        fig.savefig(output / name, dpi=180, bbox_inches="tight")
        plt.close(fig)
        figures.append({"name": name, "sha256": _hash(output / name)})

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    frame = np.arange(7)
    for ax, name in zip(axes[0], ("independent-clean", "independent-noise"), strict=True):
        ax.axhline(0, color="0.5", linestyle=":", label="Commands (zero offset)")
        ax.plot(frame, truth["actual"] - arrays["commands"], "ko-", label="Actual minus command")
        for other, label in (
            ("known", "Supplied known phases"),
            ("common-on-independent" if name.endswith("clean") else "common-noise", "Common fit"),
            (name, "Independent fit"),
        ):
            ax.plot(
                frame, fitted[f"{other}__0__phases_rad"] - arrays["commands"], ".-", label=label
            )
        if name.endswith("clean"):
            ax.plot(
                frame,
                fitted["independent-mismatch__0__phases_rad"] - arrays["commands"],
                ".--",
                label="Miscalibrated kernels",
            )
        ax.set(title=name, xlabel="Exposure index", ylabel="Offset in fixed gauge (rad)")
        ax.legend(fontsize=8)
    ax = axes[1, 0]
    names = (
        "known",
        "common-control",
        "common-on-independent",
        "independent-clean",
        "common-noise",
        "independent-noise",
        "independent-mismatch",
        "weak",
        "zero-side",
    )
    ax.bar(
        np.arange(len(names)),
        [evaluation["results"][n][0]["heldout_relative_error"] for n in names],
    )
    ax.set(xticks=np.arange(len(names)), xticklabels=names, ylabel="Held-out relative image error")
    ax.tick_params(axis="x", rotation=65)
    ax = axes[1, 1]
    for name in (
        "independent-clean",
        "independent-noise",
        "independent-mismatch",
        "weak",
        "zero-side",
    ):
        values = fitted[f"{name}__0__phase_singular_values"]
        ax.plot(np.arange(len(values)), values, ".-", label=name)
    ax.set_yscale("symlog", linthresh=1e-9)
    ax.set(
        xlabel="Singular-value index",
        ylabel="Cutoff-conditional tangent sensitivity",
    )
    ax.legend(fontsize=8)
    fig.suptitle("RA10: phases, disjoint-pixel predictions and conditional local information")
    save(fig, "phase-and-information.png")

    field_names = (
        "known",
        "common-on-independent",
        "independent-clean",
        "independent-noise",
        "independent-mismatch",
    )
    z, y, _ = meta["section_zyx"]

    def views(a: Any) -> Any:
        return a.max(axis=0), a.max(axis=1), a[z], a[:, y, :]

    field_arrays = [fitted[f"{name}__0__predicted_images"][0] for name in field_names]
    field_arrays += [arrays[scalar[name]["data_key"]][0] for name in field_names]
    vmin = min(float(np.min(a)) for a in field_arrays)
    vmax = max(float(np.max(a)) for a in field_arrays)
    delta = max(
        1e-14,
        *(
            float(np.max(np.abs(p - o)))
            for name in field_names
            for p, o in zip(
                views(fitted[f"{name}__0__predicted_images"][0]),
                views(arrays[scalar[name]["data_key"]][0]),
                strict=True,
            )
        ),
    )
    for name in field_names:
        predicted = fitted[f"{name}__0__predicted_images"][0]
        observed = arrays[scalar[name]["data_key"]][0]
        pred_views, obs_views = views(predicted), views(observed)
        fig, axes = plt.subplots(3, 4, figsize=(12, 8), constrained_layout=True)
        diffs = [p - o for p, o in zip(pred_views, obs_views, strict=True)]
        for j, label in enumerate(
            ("XY max over z", "XZ max over y", "Fixed XY section", "Fixed XZ section")
        ):
            extent = (
                0,
                SHAPE[2] * SPACING[2],
                0,
                SHAPE[1 if j % 2 == 0 else 0] * SPACING[1 if j % 2 == 0 else 0],
            )
            for row, image, title in (
                (0, obs_views[j], "Observed"),
                (1, pred_views[j], "Predicted"),
                (2, diffs[j], "Prediction − data"),
            ):
                ax = axes[row, j]
                im = ax.imshow(
                    image,
                    origin="lower",
                    extent=extent,
                    aspect="equal",
                    cmap="coolwarm" if row == 2 else "viridis",
                    vmin=-delta if row == 2 else vmin,
                    vmax=delta if row == 2 else vmax,
                )
                ax.set(
                    title=f"{title}\n{label}",
                    xlabel="x (µm)",
                    ylabel="y (µm)" if j % 2 == 0 else "z (µm)",
                )
                fig.colorbar(im, ax=ax, shrink=0.65, label="Signal (relative units)")
        fig.suptitle(f"{name}: full field and predeclared catalogue-center sections; exposure 0")
        save(fig, f"{name}-field.png")

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), constrained_layout=True)
    z, y, _ = meta["section_zyx"]
    for name in ("known", "common-on-independent", "independent-clean", "independent-noise"):
        profile = fitted[f"{name}__0__predicted_images"][0, z, y]
        axes[0].plot((np.arange(SHAPE[2]) + 0.5) * SPACING[2], profile, ".-", label=name)
        axes[1].plot(
            (np.arange(SHAPE[2]) + 0.5) * SPACING[2],
            profile / max(float(np.max(np.abs(profile))), 1e-300),
            ".-",
            label=name,
        )
    reference = arrays["independent_clean"][0, z, y]
    axes[0].plot(
        (np.arange(SHAPE[2]) + 0.5) * SPACING[2], reference, "k--", label="Clean reference"
    )
    axes[0].set(
        title="Fixed center line: quantitative signal",
        xlabel="x (µm)",
        ylabel="Signal (relative units)",
    )
    axes[1].set(
        title="Separately peak-normalized: shape only",
        xlabel="x (µm)",
        ylabel="Independent max-absolute normalization",
    )
    axes[0].legend(fontsize=7)
    for name in (
        "common-on-independent",
        "independent-clean",
        "independent-noise",
        "independent-mismatch",
    ):
        residual = fitted[f"{name}__0__residual_images"]
        axes[2].plot(
            np.arange(7),
            np.sqrt(np.mean(residual[:, ~arrays["mask"]] ** 2, axis=1)),
            ".-",
            label=name,
        )
    axes[2].set(
        title="Disjoint held-out pixels",
        xlabel="Exposure index",
        ylabel="Raw residual RMS (relative units)",
    )
    axes[2].legend(fontsize=7)
    save(fig, "profiles-and-heldout-residuals.png")
    _json(
        output / "measurements.json",
        {
            "preparation_sha256": _hash(directory / "preparation.json"),
            "observed_freeze_sha256": _hash(directory / "observed-freeze.json"),
            "evaluation": evaluation,
            "figures": figures,
            "render_python": sys.version,
            "render_numpy": np.__version__,
            "render_matplotlib": matplotlib.__version__,
            "render_driver_sha256": _hash(Path(__file__)),
        },
    )


def main() -> None:
    """Dispatch explicit preparation, observation or saved-output rendering."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "observe", "render"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--authorization", default="")
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.directory)
    elif args.mode == "observe":
        observe(args.directory, args.authorization)
    elif args.output is None:
        parser.error("render requires --output")
    else:
        render(args.directory, args.output)


if __name__ == "__main__":
    main()
