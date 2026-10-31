"""Render qualified RA09 presentation copies from frozen saved arrays only.

Only titles and main objective-display axis limits change.
Original drivers, observations, evaluations and rendered figures remain intact.
There is no fitting, simulation, alignment, recentering or candidate selection.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import sys
from pathlib import Path
from typing import Any

import numpy as np

import reference_alignment_ra09_comparison as independent

Array = independent.Array
ROOT = independent.ROOT
SOURCE = ROOT / "artifacts/ra09/figure-preparation"
BASELINE = ROOT / "artifacts/ra09/render-attempt-1"
OUTPUT = ROOT / "artifacts/ra09/report-layout-1"
CALIBRATION = ROOT / "artifacts/ra09/calibration-carrier-figure1"
CASES = ("flat_noiseless", "flat_noise", "finite_mismatch")


def _verify_material(source: Path, evidence: Path) -> dict[str, Any]:
    """Verify original input/output/driver bindings recorded before this work."""
    independent._verify_prepared(source)
    before = independent._read_json(evidence / "before-render.json")
    after = independent._read_json(evidence / "after-render.json")
    expected = {**before["original_files"], **after["new_files"]}
    for name, record in expected.items():
        if independent._hash(ROOT / name) != record["sha256"]:
            raise ValueError(f"Original artifact changed: {name}")
    for name, digest in before["driver_sha256"].items():
        if independent._hash(ROOT / name) != digest:
            raise ValueError(f"Original driver changed: {name}")
    frozen = independent._read_json(source / "observed-freeze.json")
    for name, digest in frozen["files"].items():
        if independent._hash(source / name) != digest:
            raise ValueError(f"Original observed output changed: {name}")
    rendered = independent._read_json(source / "rendered.json")
    for name, digest in rendered["files"].items():
        if independent._hash(source / name) != digest:
            raise ValueError(f"Original rendered output changed: {name}")
    return {
        "original_artifacts_verified": len(expected),
        "original_drivers_verified": before["driver_sha256"],
        "before_render_sha256": independent._hash(evidence / "before-render.json"),
        "after_render_sha256": independent._hash(evidence / "after-render.json"),
        "original_prepared_sha256": independent._hash(source / "prepared.json"),
        "original_observed_freeze_sha256": independent._hash(source / "observed-freeze.json"),
        "original_rendered_manifest_sha256": independent._hash(source / "rendered.json"),
        "original_files": expected,
    }


def _array_identity(array: Array) -> dict[str, Any]:
    return {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "c_order_data_sha256": hashlib.sha256(array.tobytes(order="C")).hexdigest(),
    }


def _phase_support(
    plt: Any, directory: Path, output: Path, case: str, planes: list[int]
) -> dict[str, Any]:
    arrays = independent._load_arrays(directory / "evaluation-arrays.npz")
    support = independent._load_arrays(directory / "expected-arrays.npz")
    metadata = independent._read_json(directory / "search.json")
    spacing = np.asarray(metadata["spacing_um_zyx"])
    phase = arrays["phase_error_rad"]
    nominal = arrays["nominal_carrier_phase_error_rad_order1"]
    refined = arrays["carrier_phase_error_rad_order1"]
    shape = arrays["reference"].shape
    # Identical data and limit expression to the original saved-figure renderer.
    limit = max(float(np.max(abs(phase))), float(np.max(abs(2 * nominal)))) or independent.EPS
    figure, axes = plt.subplots(2, 4, figsize=(16, 7), layout="constrained")
    for row, order in enumerate((1, 2)):
        for column, (image, title) in enumerate(
            (
                (order * nominal[planes[0]], "Nominal carrier slope"),
                (order * refined[planes[0]], "Refined carrier slope"),
                (phase[row, planes[0]], "Refined slope + gain phase"),
            )
        ):
            artist = axes[row, column].imshow(
                image,
                origin="lower",
                extent=(0, shape[2] * spacing[2], 0, shape[1] * spacing[1]),
                aspect="equal",
                interpolation="nearest",
                cmap="coolwarm",
                vmin=-limit,
                vmax=limit,
            )
            axes[row, column].set(title=f"Order {order}\n{title}", xlabel="x (µm)", ylabel="y (µm)")
            figure.colorbar(
                artist, ax=axes[row, column], label="unwrapped phase error (rad)", shrink=0.8
            )
        q = support[f"q{order}"]
        section = q[q[:, 0] == 0]
        axes[row, 3].scatter(
            section[:, 2] / (shape[2] * spacing[2]),
            section[:, 1] / (shape[1] * spacing[1]),
            s=12,
        )
        axes[row, 3].set(
            title=f"Order {order}: fixed Q, qz=0\n{len(q)} total 3D bins",
            xlabel="qx (cycles/µm)",
            ylabel="qy (cycles/µm)",
            aspect="equal",
        )
    figure.suptitle(
        f"RA09 {case}: full fixed XY field; same radian scale; zero axial carrier\n"
        "Index-zero phase; gain phase retained only in the third column; no alignment"
    )
    target = output / f"{case}-phase-and-support.png"
    figure.savefig(target, dpi=170)
    plt.close(figure)
    return {
        "output": target.name,
        "output_sha256": independent._hash(target),
        "original_figure": str((directory / "phase-and-support.png").relative_to(ROOT)),
        "original_figure_sha256": independent._hash(directory / "phase-and-support.png"),
        "source_files": {
            name: independent._hash(directory / name)
            for name in ("evaluation-arrays.npz", "expected-arrays.npz", "search.json")
        },
        "array_binding": {
            "phase_error_rad": _array_identity(phase),
            "nominal_carrier_phase_error_rad_order1": _array_identity(nominal),
            "carrier_phase_error_rad_order1": _array_identity(refined),
            "q1": _array_identity(support["q1"]),
            "q2": _array_identity(support["q2"]),
        },
        "preserved_phase_limits_rad": [-limit, limit],
        "preserved_section_indices_zyx": planes,
        "transformations": (
            "Wrapped/shortened titles only; data, scales, aspect and sample coordinates unchanged."
        ),
    }


def _objective_pairs(plt: Any, directory: Path, output: Path, case: str) -> dict[str, Any]:
    arrays = independent._load_arrays(directory / "objective-landscape.npz")
    metadata = independent._read_json(directory / "search.json")
    observed = independent._read_json(directory / "observed.json")["candidates"][0]
    nominal = np.asarray(metadata["initial_carriers_per_um"][0])
    fitted = np.asarray(observed["carrier_per_um"])
    maximum = float(np.max(arrays["joint_objective"]))
    x, y = arrays["carrier_x_per_um"], arrays["carrier_y_per_um"]
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for ax, key, label in zip(
        axes,
        ("joint_objective", "order2_objective"),
        ("Selected coupled J1 + J2", "J2 only\nSource-observation comparator"),
        strict=True,
    ):
        artist = ax.pcolormesh(x, y, arrays[key], shading="nearest", vmin=0, vmax=maximum)
        ax.plot(nominal[1], nominal[0], "wo", label="nominal metadata")
        ax.plot(fitted[1], fitted[0], "rx", label="joint product fit")
        ax.set(
            title=label,
            xlabel="kx (cycles/µm)",
            ylabel="ky (cycles/µm)",
            xlim=(float(x[0]), float(x[-1])),
            ylim=(float(y[0]), float(y[-1])),
        )
        ax.legend(fontsize=8)
        figure.colorbar(artist, ax=ax, label="dimensionless normalized objective")
    figure.suptitle("Predeclared 9 × 9 box samples; same fixed Q; no measured legacy C parity")
    target = output / f"{case}-objective-order-pairs.png"
    figure.savefig(target, dpi=170)
    plt.close(figure)
    return {
        "output": target.name,
        "output_sha256": independent._hash(target),
        "original_figure": str((directory / "objective-order-pairs.png").relative_to(ROOT)),
        "original_figure_sha256": independent._hash(directory / "objective-order-pairs.png"),
        "source_files": {
            name: independent._hash(directory / name)
            for name in ("objective-landscape.npz", "search.json", "observed.json")
        },
        "array_binding": {key: _array_identity(value) for key, value in arrays.items()},
        "preserved_objective_limits": [0, maximum],
        "display_box_per_um_yx": [[float(y[0]), float(x[0])], [float(y[-1]), float(x[-1])]],
        "axis_endpoints_equal_search_bounds": bool(
            np.array_equal([[y[0], x[0]], [y[-1], x[-1]]], metadata["carrier_bounds_per_um"])
        ),
        "transformations": (
            "Wrapped/shortened comparator title; axes limited to saved extreme sampled "
            "carrier nodes. Data, objective scales, markers and carrier search unchanged."
        ),
    }


def _field_copies(
    plt: Any,
    output: Path,
    reference: Array,
    predictions: list[tuple[str, str, Array, str]],
    spacing: Array,
    planes: list[int],
    source_file: Path,
    reference_field: str,
) -> list[dict[str, Any]]:
    """Wrap field-image titles with original data and exact original shared scales."""
    z, y, _ = planes
    views = (
        ("XY maximum over z", lambda v: np.max(v, axis=0), (2, 1)),
        ("XZ maximum over y", lambda v: np.max(v, axis=1), (2, 0)),
        (f"XY fixed section z={z}", lambda v: v[z], (2, 1)),
        (f"XZ fixed section y={y}", lambda v: v[:, y], (2, 0)),
    )
    low = min(float(reference.min()), *(float(v.min()) for _, _, v, _ in predictions))
    high = max(float(reference.max()), *(float(v.max()) for _, _, v, _ in predictions))
    difference_limit = (
        max(
            float(np.max(abs(view(prediction) - view(reference))))
            for _, view, _ in views
            for _, _, prediction, _ in predictions
        )
        or independent.EPS
    )
    records = []
    for original_name, target_name, prediction, field in predictions:
        original = source_file.parent / original_name
        figure, axes = plt.subplots(4, 3, figsize=(13, 10), layout="constrained")
        for row, (view_label, view, dimensions) in enumerate(views):
            horizontal, vertical = dimensions
            extent = (
                0,
                reference.shape[horizontal] * spacing[horizontal],
                0,
                reference.shape[vertical] * spacing[vertical],
            )
            for column, (title, image) in enumerate(
                (
                    ("Held-out reference", view(reference)),
                    ("Known-source fit prediction", view(prediction)),
                    ("Prediction − reference", view(prediction) - view(reference)),
                )
            ):
                artist = axes[row, column].imshow(
                    image,
                    origin="lower",
                    extent=extent,
                    aspect="equal",
                    interpolation="nearest",
                    cmap="coolwarm" if column == 2 else "viridis",
                    vmin=-difference_limit if column == 2 else low,
                    vmax=difference_limit if column == 2 else high,
                )
                axes[row, column].set(
                    title=f"{view_label}\n{title}",
                    xlabel=f"{'zyx'[horizontal]} (µm)",
                    ylabel=f"{'zyx'[vertical]} (µm)",
                )
                figure.colorbar(
                    artist, ax=axes[row, column], label="relative intensity units", shrink=0.8
                )
        figure.suptitle(
            f"RA09 {target_name.removesuffix('.png')}: held-out phase 0.41 rad\n"
            "Known-source evaluation after output freeze; original quantitative scales"
        )
        target = output / target_name
        figure.savefig(target, dpi=170)
        plt.close(figure)
        records.append(
            {
                "output": target.name,
                "output_sha256": independent._hash(target),
                "original_figure": str(original.relative_to(ROOT)),
                "original_figure_sha256": independent._hash(original),
                "source_files": {
                    str(source_file.relative_to(ROOT)): independent._hash(source_file)
                },
                "array_binding": {
                    reference_field: _array_identity(reference),
                    field: _array_identity(prediction),
                },
                "preserved_intensity_limits": [low, high],
                "preserved_difference_limits": [-difference_limit, difference_limit],
                "preserved_section_indices_zyx": planes,
                "shared_scaling_predictions": [name for _, name, _, _ in predictions],
                "transformations": (
                    "Wrapped row/column titles only; every pixel datum, plane, projection, "
                    "image scale, aspect, colormap and coordinate unchanged. Differences "
                    "remain differences of projections, not maxima of differences."
                ),
            }
        )
    return records


def _calibration_profiles(plt: Any, output: Path) -> dict[str, Any]:
    arrays = independent._load_arrays(CALIBRATION / "full-field-evaluation-arrays.npz")
    metadata = independent._read_json(CALIBRATION / "full-field-evaluation.json")
    spacing = np.asarray(metadata["spacing_um_zyx"])
    z, y, x = metadata["fixed_specimen_section_indices_zyx"]
    cal = arrays["calibration_carrier_phase_error_order1_rad"]
    specimen = arrays["specimen_carrier_phase_error_order1_rad"]
    figure, axes = plt.subplots(1, 3, figsize=(14, 4), layout="constrained")
    for label, phase in (("Short calibration q", cal), ("Frozen specimen q", specimen)):
        axes[0].plot((np.arange(cal.shape[2]) + 0.5) * spacing[2], 2 * phase[z, y], label=label)
        axes[1].plot((np.arange(cal.shape[1]) + 0.5) * spacing[1], 2 * phase[z, :, x], label=label)
    axes[0].set(
        title="Order-two phase\nFixed bead-center x line",
        xlabel="x (µm)",
        ylabel="unwrapped carrier-only error (rad)",
    )
    axes[1].set(
        title="Order-two phase\nFixed bead-center y line",
        xlabel="y (µm)",
        ylabel="unwrapped carrier-only error (rad)",
    )
    for label in ("calibration", "specimen"):
        axes[2].plot(
            (1, 2),
            metadata["metrics"][label]["gain_only_phase_error_rad_by_order"],
            "o-",
            label=label,
        )
    axes[2].set(
        title="Gain-only phase error\nIndex-zero origin",
        xlabel="positive order",
        ylabel="gain-only phase error (rad)",
        xticks=(1, 2),
    )
    for ax in axes:
        ax.legend(fontsize=8)
    target = output / "calibration-phase-profiles-and-gain-phase.png"
    figure.savefig(target, dpi=170)
    plt.close(figure)
    original = CALIBRATION / "phase-profiles-and-gain-phase.png"
    return {
        "output": target.name,
        "output_sha256": independent._hash(target),
        "original_figure": str(original.relative_to(ROOT)),
        "original_figure_sha256": independent._hash(original),
        "source_files": {
            name: independent._hash(CALIBRATION / name)
            for name in ("full-field-evaluation.json", "full-field-evaluation-arrays.npz")
        },
        "array_binding": {
            "calibration_carrier_phase_error_order1_rad": _array_identity(cal),
            "specimen_carrier_phase_error_order1_rad": _array_identity(specimen),
        },
        "preserved_gain_phase_errors_rad": {
            label: metadata["metrics"][label]["gain_only_phase_error_rad_by_order"]
            for label in ("calibration", "specimen")
        },
        "preserved_section_indices_zyx": [z, y, x],
        "transformations": (
            "Wrapped/shortened titles only; all six phase lines, gain points, "
            "scales and coordinates unchanged."
        ),
    }


def render(source: Path, evidence: Path, output: Path) -> None:
    """Create twelve presentation copies and verify every original byte before/after."""
    if (
        (output / "rendered.json").exists()
        or (output / "source-binding-before.json").exists()
        or list(output.glob("*.png"))
    ):
        raise FileExistsError("Presentation outputs exist; no overwrite or automatic retry.")
    binding = _verify_material(source, evidence)
    output.mkdir(parents=True, exist_ok=True)
    independent._write_json(output / "source-binding-before.json", binding)
    plt = importlib.import_module("matplotlib.pyplot")
    catalogue = independent._read_json(source / "catalogue.json")
    figures = []
    for case in CASES:
        directory = source / case
        figures.append(
            _phase_support(plt, directory, output, case, catalogue["section_indices_zyx"])
        )
        figures.append(_objective_pairs(plt, directory, output, case))
        arrays = independent._load_arrays(directory / "evaluation-arrays.npz")
        metadata = independent._read_json(directory / "search.json")
        figures.extend(
            _field_copies(
                plt,
                output,
                arrays["reference"],
                [
                    (
                        "heldout-field.png",
                        f"{case}-heldout-field.png",
                        arrays["prediction"],
                        "prediction",
                    )
                ],
                np.asarray(metadata["spacing_um_zyx"]),
                catalogue["section_indices_zyx"],
                directory / "evaluation-arrays.npz",
                "reference",
            )
        )
    arrays = independent._load_arrays(CALIBRATION / "full-field-evaluation-arrays.npz")
    metadata = independent._read_json(CALIBRATION / "full-field-evaluation.json")
    figures.extend(
        _field_copies(
            plt,
            output,
            arrays["heldout_reference"],
            [
                (
                    f"{label}-q-full-field.png",
                    f"{label}-q-full-field.png",
                    arrays[f"{label}_heldout_prediction"],
                    f"{label}_heldout_prediction",
                )
                for label in ("calibration", "specimen")
            ],
            np.asarray(metadata["spacing_um_zyx"]),
            metadata["fixed_specimen_section_indices_zyx"],
            CALIBRATION / "full-field-evaluation-arrays.npz",
            "heldout_reference",
        )
    )
    figures.append(_calibration_profiles(plt, output))
    after = _verify_material(source, evidence)
    if binding != after:
        raise ValueError("Original material identity changed during presentation rendering.")
    identity = independent._source_identity()
    identity["helper_driver_sha256"] = identity.pop("driver_sha256")
    identity["driver_sha256"] = independent._hash(Path(__file__))
    product_imported = any(
        name == "simrecon" or name.startswith("simrecon.") for name in sys.modules
    )
    if product_imported:
        raise RuntimeError("Presentation-only process unexpectedly imported product code.")
    independent._write_json(
        output / "rendered.json",
        {
            "schema": "simrecon.ra09.presentation-copies.v1",
            "identity": identity,
            "source_material": binding,
            "originals_verified_unchanged_after_render": True,
            "figures": figures,
            "product_imported": False,
            "product_calls": 0,
            "matplotlib": importlib.import_module("matplotlib").__version__,
            "limits": (
                "Presentation copies only. No fits, simulations, candidate selection, "
                "alignment, recentering or changes to scientific inputs/outputs. "
                "Global ambiguity and all original claim limits remain."
            ),
        },
    )
    print(
        "Rendered twelve bound presentation copies; "
        f"{binding['original_artifacts_verified']} originals unchanged."
    )


def main() -> None:
    """Run only the authorized saved-array presentation operation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--baseline-evidence", type=Path, default=BASELINE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    render(args.source, args.baseline_evidence, args.output)


if __name__ == "__main__":
    main()
