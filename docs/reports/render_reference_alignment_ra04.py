"""Render observed RA04 corrections against independent reviewed fixture controls."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import resource
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests"))
import simrecon as sr  # noqa: E402
from reference_alignment_ra04_fixture import (  # noqa: E402
    declared_example,
    estimated_example,
    reconstruction_control,
)

OUTPUT = ROOT / "docs/reports/figures"
EVIDENCE = ROOT / "docs/reports/evidence/ra04"


def digest(path: str) -> str:
    """Identify an actual input without publishing local absolute paths."""
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def montage(data: np.ndarray) -> np.ndarray:
    """Display each orientation/phase tile in canonical order along columns."""
    return np.hstack([data[o, p] for o in range(data.shape[0]) for p in range(data.shape[1])])


def save(figure: Any, name: str) -> None:
    """Save one numerical figure with its complete visible labels."""
    figure.savefig(OUTPUT / name, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close(figure)


def declared_figure() -> dict[str, Any]:
    """Observe full-map correction with exact dyadic supplied controls."""
    example = declared_example(maps=True)
    pair = sr.correct_alignment_pair(example.specimen, bead=example.bead, **example.arguments)
    assert pair.status == "corrected" and pair.specimen is not None and pair.bead is not None
    result = pair.specimen.data
    error = result - example.specimen_signal
    figure, axes = plt.subplots(2, 2, figsize=(12.5, 6), layout="constrained")
    values = [
        (example.specimen.data, "Raw specimen", "detector count", "viridis", None),
        (
            example.specimen_signal,
            "Independent supplied signal",
            "common signal unit",
            "coolwarm",
            4.5,
        ),
        (
            result,
            "After baseline, response and exposure correction",
            "common signal unit",
            "coolwarm",
            4.5,
        ),
        (error, "Observed minus independent signal", "common signal unit", "coolwarm", 1e-14),
    ]
    for axis, (data, title, unit, cmap, bound) in zip(axes.flat, values, strict=True):
        limits = {} if bound is None else {"vmin": -bound, "vmax": bound}
        artist = axis.imshow(montage(data), aspect="auto", cmap=cmap, **limits)
        axis.set(
            title=title,
            xlabel="Canonical orientation/phase tiles (3 columns each)",
            ylabel="y pixel",
        )
        axis.set_yticks([0, 1])
        figure.colorbar(artist, ax=axis, label=unit, shrink=0.85)
    figure.suptitle(
        "RA04: distinct full-shape baselines, responses and exposures preserve signed signal"
    )
    save(figure, "ra04-declared-correction.png")
    return {
        "specimen_shape": list(result.shape),
        "bead_shape": list(pair.bead.data.shape),
        "specimen_max_absolute_error": float(np.max(np.abs(error))),
        "bead_max_absolute_error": float(np.max(np.abs(pair.bead.data - example.bead_signal))),
        "negative_output_samples": int(np.count_nonzero(result < 0)),
        "operation_order": list(pair.specimen.provenance["operations"]),
        "units": "synthetic common signal unit",
        "limits": (
            "Exact dyadic finite controls; labels declare rather than "
            "authenticate physical calibration."
        ),
    }


def estimated_figure() -> dict[str, Any]:
    """Compare supplied gauge with two explicitly finite estimated gauges."""
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.7), layout="constrained")
    rows = []
    snapshot_variances = None
    expected_variances = None
    for flat_mean, color in ((20, "#1565c0"), (21, "#d84315")):
        example, groups, expected = estimated_example(flat_mean=flat_mean)
        camera = sr.estimate_scalar_camera(
            groups[0],
            blank_counts=groups[1],
            flat_counts=groups[2],
            source=f"RA04 finite controls flat mean {flat_mean}",
        )
        pair = sr.correct_alignment_pair(
            example.specimen,
            bead=example.bead,
            camera_estimate=camera,
            **example.arguments,
        )
        assert pair.status == "corrected" and pair.specimen is not None
        assert pair.camera_estimate is not None
        known = sr.correct_alignment_pair(
            example.specimen,
            bead=example.bead,
            mode="declared",
            output_unit="reference_flat_relative",
            gauge_source="independent dM=8 control",
            specimen_offset=12,
            specimen_response=8,
            bead_offset=12,
            bead_response=8,
            specimen_exposure_factor=1,
            bead_exposure_factor=1,
            reference_sum_equalization="disabled",
        )
        assert known.specimen is not None
        x = example.specimen_signal.ravel()
        known_output = known.specimen.data.ravel()
        y = pair.specimen.data.ravel()
        expected_y = 8 * example.specimen_signal.ravel() / expected["contrast"]
        axes[0].plot(
            x, y, "o-", color=color, label=f"Observed dM = {camera.contrast_counts:g} counts"
        )
        rows.append(
            {
                "flat_group_mean_counts": flat_mean,
                "observed_blank_counts": float(camera.means_counts[1]),
                "observed_contrast_counts": camera.contrast_counts,
                "declared_reference_contrast_counts": 8,
                "known_output": known_output.tolist(),
                "independent_declared_signal": x.tolist(),
                "known_max_error_to_independent_signal": (float(np.max(np.abs(known_output - x)))),
                "estimated_output": y.tolist(),
                "independent_finite_gauge_output": expected_y.tolist(),
                "max_absolute_error_to_finite_gauge": float(np.max(np.abs(y - expected_y))),
                "max_absolute_difference_from_declared_gauge": float(np.max(np.abs(y - x))),
                "camera_variances_counts2": camera.variances_counts2.tolist(),
                "retained_variances_counts2": pair.camera_estimate.variances_counts2.tolist(),
                "empirical_frame_mean_se_counts": (
                    pair.camera_estimate.empirical_mean_se_counts.tolist()
                ),
                "optional_gain_counts_per_e": pair.camera_estimate.gain_counts_per_e,
                "limits": (
                    "Deterministic finite moments, not random sampling "
                    "or real-instrument calibration."
                ),
            }
        )
        if flat_mean == 20:
            snapshot_variances = pair.camera_estimate.variances_counts2
            expected_variances = expected["variances"]
    axes[0].plot([-1, 2], [-1, 2], "k--", alpha=0.5, label="Same declared dM = 8 gauge")
    axes[0].set(
        xlabel="Supplied dM=8 gauge (flat-relative unit)",
        ylabel="Estimated output (its own flat-relative unit)",
        title="One shared estimated gauge; changing its flat changes scale",
    )
    axes[0].legend(fontsize=8)
    positions = np.arange(3)
    axes[1].bar(
        positions - 0.18,
        expected_variances,
        width=0.36,
        color="#90a4ae",
        label="Independent finite moment",
    )
    axes[1].bar(
        positions + 0.18,
        snapshot_variances,
        width=0.36,
        color="#00897b",
        label="Retained camera snapshot",
    )
    axes[1].set(
        xticks=positions,
        xticklabels=["Dark", "Blank", "Flat"],
        ylabel="Original detector-count²",
        title="Mean blank subtraction retains variance evidence",
    )
    axes[1].legend(fontsize=8)
    save(figure, "ra04-estimated-gauge.png")
    return {
        "cases": rows,
        "units": (
            "Each estimated curve uses its explicitly different observed reference-flat gauge."
        ),
    }


def reconstruction_figure() -> dict[str, Any]:
    """Observe sparse phase totals and the fixed-window linear estimator."""
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.7), layout="constrained")
    rows = []
    phase_totals = None
    for point in (False, True):
        for scale in (1.0, 2.0):
            example, arguments, expected_spectrum, expected_image = reconstruction_control(
                point=point, scale=scale
            )
            pair = sr.correct_alignment_pair(
                example.specimen, bead=example.bead, **example.arguments
            )
            assert pair.specimen is not None
            result = sr.reconstruct(pair.specimen.data, **arguments)
            ny, nx = pair.specimen.data.shape[-2:]
            rows.append(
                {
                    "control": "point selected coefficients" if point else "signed constant",
                    "source_scale": scale,
                    "DC_real": float(result.spectrum[ny, nx].real),
                    "expected_DC_real": float(expected_spectrum[ny, nx].real),
                    "max_spectrum_absolute_error": float(
                        np.max(np.abs(result.spectrum - expected_spectrum))
                    ),
                    "max_image_absolute_error": float(
                        np.max(np.abs(result.image - expected_image))
                    ),
                    "max_imaginary_image": float(np.max(np.abs(result.image.imag))),
                    "fixed_ridge": arguments["regularization"],
                    "expected_amplitude_shrinkage": 0.9,
                }
            )
            if point and scale == 1:
                phase_totals = pair.specimen.data.sum(axis=(-2, -1)).ravel()
                axes[0].bar(
                    np.arange(4),
                    phase_totals,
                    color="#1565c0",
                    label="Corrected measured phase sum",
                )
                axes[0].axhline(
                    float(np.mean(phase_totals)),
                    color="#d84315",
                    linestyle="--",
                    label="Counterfactual: equalize every sum to its mean",
                )
                x = np.arange(2 * nx) * 0.5
                axes[1].plot(
                    x,
                    expected_image[0].real,
                    "k-",
                    linewidth=2.5,
                    label="Independent fixed-window estimator",
                )
                axes[1].plot(
                    x,
                    result.image[0].real,
                    "o",
                    color="#00897b",
                    label="Reconstruction after correction",
                )
    axes[0].set(
        xticks=np.arange(4),
        xticklabels=["0", "π/2", "π", "3π/2"],
        xlabel="Illumination phase (radian)",
        ylabel="Phase sum (common signal unit)",
        title="A sparse object's legitimate signal total changes with phase",
    )
    axes[0].set_ylim(0, float(np.max(phase_totals)) * 1.35)
    axes[0].legend(fontsize=8, loc="upper right")
    axes[1].set(
        xlabel="x (µm); fixed 5 µm field, 0.5 µm output sampling",
        ylabel="Reconstructed signed intensity (common signal unit)",
        title="Point input: three lateral coefficients, fixed ridge; no peak claim",
    )
    axes[1].legend(fontsize=8)
    save(figure, "ra04-reconstruction-and-sums.png")
    return {
        "cases": rows,
        "point_phase_sums": phase_totals.tolist(),
        "reference_sum_equalization": "disabled; requested per_frame_sum is unavailable",
        "limits": (
            "Fixed finite periodic grid/transfer/mask/ridge. The plotted curve "
            "is the defined estimator, not a recovered point shape or a resolution claim."
        ),
    }


def frozen_observations_figure() -> dict[str, Any]:
    """Apply the adapter to all frozen original specimen and held-out bead frames."""
    folder = ROOT / "artifacts/ra04/original-observations"
    manifest_bytes = (folder / "complete.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    assert manifest_sha == "1aeae458173155d0609020d25b299e087e16ffa6e31453f744e8b048584ebd5c"
    original_hashes = {}
    for item in manifest["files"]:
        path = folder / item["path"]
        original_hashes[item["path"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert original_hashes[item["path"]] == item["sha256"]
    camera = sr.estimate_scalar_camera(
        np.load(folder / "camera_dark.npy", allow_pickle=False),
        blank_counts=np.load(folder / "camera_blank.npy", allow_pickle=False),
        flat_counts=np.load(folder / "camera_flat.npy", allow_pickle=False),
        source=f"original PR53 observation manifest {manifest_sha}",
    )
    geometry = manifest["geometry"]
    specimen_raw = np.empty((3, 5, *geometry["specimen_shape_zyx"]), dtype=np.float64)
    for orientation in range(3):
        for phase in range(5):
            specimen_raw[orientation, phase] = np.load(
                folder / f"specimen_o{orientation}_p{phase}.npy",
                allow_pickle=False,
            )
    bead_raw = np.load(folder / "calibration_heldout.npy", allow_pickle=False)

    def declare(data: np.ndarray, kind: str, label: str, spacing: list[float]) -> Any:
        return sr.declare_acquisition(
            data,
            config={
                "version": 1,
                "axes": ["orientation", "phase", "z", "y", "x"],
                "acquisition_kind": kind,
                "intensity_unit": "detector count",
                "calibration_id": label,
                "sampling_um": dict(zip(("z", "y", "x"), spacing, strict=True)),
            },
            original_metadata={
                "observation_manifest_sha256": manifest_sha,
                "observation_manifest": manifest,
                "condition": "original frozen paired stationary-camera acquisition",
            },
        )

    specimen = declare(
        specimen_raw,
        "specimen_sim",
        "original specimen provenance",
        geometry["specimen_spacing_um_zyx"],
    )
    bead = declare(
        bead_raw,
        "sim_beads",
        "original held-out bead provenance",
        geometry["calibration_spacing_um_zyx"],
    )
    pair = sr.correct_alignment_pair(
        specimen,
        bead=bead,
        mode="estimated",
        camera_estimate=camera,
        output_unit="reference_flat_relative",
        gauge_source="one original paired scalar estimate",
        specimen_exposure_factor=1,
        bead_exposure_factor=1,
        reference_sum_equalization="disabled",
    )
    assert pair.status == "corrected" and pair.specimen is not None and pair.bead is not None
    assert pair.camera_estimate is not None
    rows = []
    prepared = []
    retained = ROOT / "artifacts/ra04/frozen-pair" / digest("src/simrecon/_alignment_camera.py")
    retained.mkdir(parents=True, exist_ok=True)
    for label, raw, corrected, spacing in (
        ("Specimen", specimen_raw, pair.specimen, geometry["specimen_spacing_um_zyx"]),
        ("Held-out bead", bead_raw, pair.bead, geometry["calibration_spacing_um_zyx"]),
    ):
        largest_error = 0.0
        for orientation in range(3):
            for phase in range(5):
                independent = (
                    raw[orientation, phase] - float(camera.means_counts[1])
                ) / camera.contrast_counts
                largest_error = max(
                    largest_error,
                    float(np.max(np.abs(corrected.data[orientation, phase] - independent))),
                )
        path = retained / (
            "specimen-corrected.npy" if label == "Specimen" else "bead-corrected.npy"
        )
        if path.exists():
            assert np.array_equal(np.load(path, allow_pickle=False), corrected.data)
        else:
            with path.open("xb") as destination:
                np.save(destination, corrected.data, allow_pickle=False)
        rows.append(
            {
                "member": label,
                "shape": list(raw.shape),
                "exposures": 15,
                "max_absolute_difference_from_explicit_affine_composition": largest_error,
                "negative_corrected_samples": int(np.count_nonzero(corrected.data < 0)),
                "corrected_minimum": float(np.min(corrected.data)),
                "corrected_maximum": float(np.max(corrected.data)),
                "retained_output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "retained_output_bytes": path.stat().st_size,
                "declared_source_calibration_id": corrected.source_metadata["calibration_id"],
            }
        )
        selected_raw, selected_corrected = raw[0, 0], corrected.data[0, 0]
        prepared.append((label, selected_raw, selected_corrected, spacing))
    raw_min = min(float(np.min(r[1])) for r in prepared)
    raw_max = max(float(np.max(r[1])) for r in prepared)
    corrected_min = (raw_min - float(camera.means_counts[1])) / camera.contrast_counts
    corrected_max = (raw_max - float(camera.means_counts[1])) / camera.contrast_counts
    figure, axes = plt.subplots(2, 4, figsize=(14.5, 7.7), layout="constrained")
    raw_artist = corrected_artist = None
    for row, (label, raw, corrected, spacing) in enumerate(prepared):
        nz, ny, nx = raw.shape
        dz, dy, dx = spacing
        for column, (data, projection, is_corrected) in enumerate(
            (
                (raw, "XY", False),
                (corrected, "XY", True),
                (raw, "XZ", False),
                (corrected, "XZ", True),
            )
        ):
            plane = np.max(data, axis=0 if projection == "XY" else 1)
            extent = (0, nx * dx, 0, ny * dy if projection == "XY" else nz * dz)
            limits = (corrected_min, corrected_max) if is_corrected else (raw_min, raw_max)
            artist = axes[row, column].imshow(
                plane,
                origin="lower",
                extent=extent,
                aspect="equal",
                cmap="viridis",
                vmin=limits[0],
                vmax=limits[1],
            )
            axes[row, column].set(
                title=f"{label} {projection}: {'corrected' if is_corrected else 'raw'}",
                xlabel="local x (µm)",
                ylabel="local y (µm)" if projection == "XY" else "local z (µm)",
            )
            if is_corrected:
                corrected_artist = artist
            else:
                raw_artist = artist
    figure.colorbar(
        raw_artist,
        ax=axes[:, [0, 2]].ravel().tolist(),
        label="Original detector count",
        shrink=0.75,
    )
    figure.colorbar(
        corrected_artist,
        ax=axes[:, [1, 3]].ravel().tolist(),
        label="Reference-flat-relative unit",
        shrink=0.75,
    )
    figure.suptitle("Original PR53 orientation 1 / exposure 1: one shared camera gauge, no refit")
    save(figure, "ra04-original-frozen-camera.png")
    for item in manifest["files"]:
        assert (
            hashlib.sha256((folder / item["path"]).read_bytes()).hexdigest()
            == original_hashes[item["path"]]
        )
    return {
        "observation_manifest_sha256": manifest_sha,
        "original_arrays_sha256": original_hashes,
        "members": rows,
        "camera_blank_counts": float(camera.means_counts[1]),
        "camera_contrast_counts": camera.contrast_counts,
        "retained_camera_variances_counts2": pair.camera_estimate.variances_counts2.tolist(),
        "retained_camera_empirical_mean_se_counts": (
            pair.camera_estimate.empirical_mean_se_counts.tolist()
        ),
        "optional_gain_counts_per_e": pair.camera_estimate.gain_counts_per_e,
        "camera_information_codes": list(pair.camera_estimate.information_codes),
        "projection": (
            "XY=max over z; XZ=max over y; physical aspect retained; "
            "coordinates local to each recorded volume"
        ),
        "shared_affine_display_raw_count_limits": [raw_min, raw_max],
        "shared_affine_display_relative_limits": [corrected_min, corrected_max],
        "limits": (
            "Original frozen bytes; no new simulation/fit/settings/seeds. "
            "Gauge equivalence only, not recovered source, resolution, noise removal "
            "or instrument calibration. MIPs conceal depth and negative samples; "
            "numerical counters cover full arrays."
        ),
    }


def main() -> None:
    """Write reproducible numerical figures and public/private provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--small-only",
        action="store_true",
        help="Render three public fixture controls without the original archive",
    )
    arguments = parser.parse_args()
    assert Path(sr.__file__).resolve() == ROOT / "src/simrecon/__init__.py"
    assert platform.python_version() == "3.13.12"
    for package, expected in (("numpy", "2.5.3"), ("scipy", "1.18.1"), ("matplotlib", "3.10.7")):
        assert importlib.metadata.version(package) == expected
    OUTPUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    inputs = [
        "docs/contracts/reference-alignment-ra04-v1.md",
        "tests/test_reference_alignment_ra04.py",
        "tests/reference_alignment_ra04_fixture.py",
        "src/simrecon/_alignment_camera.py",
        "src/simrecon/__init__.py",
        "src/simrecon/_linear_response.py",
        "src/simrecon/_scalar_camera_calibration.py",
        "src/simrecon/_acquisition.py",
        "uv.lock",
        "docs/reports/render_reference_alignment_ra04.py",
    ]
    summary = {
        "schema": "RA04-numerical-controls-v1",
        "inputs_sha256": {path: digest(path) for path in inputs},
        "declared": declared_figure(),
        "estimated": estimated_figure(),
        "reconstruction": reconstruction_figure(),
        "original_frozen_observations": (
            None if arguments.small_only else frozen_observations_figure()
        ),
        "versions": {
            package: importlib.metadata.version(package)
            for package in ("numpy", "scipy", "h5py", "matplotlib")
        },
    }
    assert {path: digest(path) for path in inputs} == summary["inputs_sha256"]
    (EVIDENCE / ("summary-small.json" if arguments.small_only else "summary.json")).write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    private = {
        "python": sys.executable,
        "version": sys.version,
        "platform": platform.platform(),
        "simrecon": sr.__file__,
        "peak_ru_maxrss_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "ru_maxrss_units": "B" if sys.platform == "darwin" else "KiB",
        "installed_distributions": {
            d.metadata["Name"]: d.version for d in importlib.metadata.distributions()
        },
        "inputs_sha256": summary["inputs_sha256"],
        "limits": (
            "Renderer-process peak only, not a product memory guarantee; "
            "no sampling uncertainty or instrument calibration claim."
        ),
    }
    (ROOT / "artifacts/ra04/checks/renderer-environment.json").write_text(
        json.dumps(private, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "figures": 3 if arguments.small_only else 4,
                "declared_max_error": summary["declared"]["specimen_max_absolute_error"],
                "reconstruction_cases": len(summary["reconstruction"]["cases"]),
            }
        )
    )


if __name__ == "__main__":
    main()
