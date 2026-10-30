"""Render retained RA05 observations with shared complex-response scales.

Use the isolated plotting environment. This program reads an existing scientific
observation directory and creates a new render directory without regeneration.
"""

import argparse
import hashlib
import json
import platform
import sys
import time
from fractions import Fraction
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")


def sha256(path):
    """Fingerprint a complete local file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extent(x, y):
    """Convert uniformly sampled center coordinates to image-edge coordinates."""
    dx, dy = x[1] - x[0], y[1] - y[0]
    return x[0] - dx / 2, x[-1] + dx / 2, y[0] - dy / 2, y[-1] + dy / 2


def complex_planes(data, metadata, destination):
    """Show all orders on one signed scale with phases and independent errors."""
    values = data["returned_response"]
    truth = data["expected_response"]
    plane = int(np.where(data["fz_per_um"] == 0)[0][0])
    observed, expected = values[:, plane], truth[:, plane]
    error = np.abs(observed - expected)
    signed_limit = float(max(np.max(abs(observed.real)), np.max(abs(observed.imag))))
    error_limit = float(np.max(error)) or 1.0
    bounds = extent(data["fx_per_um"], data["fy_per_um"])
    fig, axes = plt.subplots(
        3, 4, figsize=(13.5, 8), sharex=True, sharey=True, layout="constrained"
    )
    for order in range(3):
        panels = (
            (observed[order].real, "RdBu_r", -signed_limit, signed_limit),
            (observed[order].imag, "RdBu_r", -signed_limit, signed_limit),
            (np.angle(observed[order]), "twilight", -np.pi, np.pi),
            (error[order], "magma", 0, error_limit),
        )
        for column, (array, cmap, lower, upper) in enumerate(panels):
            image = axes[order, column].imshow(
                array,
                origin="lower",
                extent=bounds,
                cmap=cmap,
                vmin=lower,
                vmax=upper,
                interpolation="nearest",
                aspect="equal",
            )
            if column == 0:
                signed_image = image
            elif column == 2:
                phase_image = image
            elif column == 3:
                error_image = image
        axes[order, 0].set_ylabel(f"Order {order}\nf_y [cycles/µm]")
    for axis, title in zip(
        axes[0],
        ("Real part", "Imaginary part", "Phase [rad]", "Absolute complex error"),
        strict=True,
    ):
        axis.set_title(title)
    for axis in axes[-1]:
        axis.set_xlabel("f_x [cycles/µm]")
    fig.colorbar(signed_image, ax=axes[:, :2].ravel().tolist(), shrink=0.8, label="Transfer [1]")
    fig.colorbar(phase_image, ax=axes[:, 2].tolist(), shrink=0.8, label="Phase [rad]")
    bar = fig.colorbar(error_image, ax=axes[:, 3].tolist(), shrink=0.8, label="Error [1]")
    bar.formatter.set_powerlimits((0, 0))
    bar.update_ticks()
    fig.suptitle(
        "Complex calibration order planes at f_z = 0\n"
        "One common dc normalization; bead and calibration-phase gauge retained",
        fontsize=14,
    )
    fig.savefig(destination / "complex-orders.png", dpi=180)
    plt.close(fig)


def bead_anchor(data, metadata, destination):
    """Compare raw and compensated dc with the independently declared anchor."""
    mass_record = metadata["dc_mass"]
    mass = float(Fraction(mass_record["numerator"], mass_record["denominator"]))
    anchor = tuple(metadata["origin_zyx"])
    peak = tuple(
        int(x)
        for x in np.unravel_index(
            np.argmax(data["returned_components"][0].real), data["returned_components"][0].shape
        )
    )
    spacing = metadata["calibration_record"]["response"]["voxel_size_um"]
    z = anchor[0]
    arrays = (
        data["returned_components"][0].real / mass,
        data["compensated_dc_returned"],
        data["h_at_anchor"],
    )
    panels = [array[z] for array in arrays]
    lower, upper = min(float(p.min()) for p in panels), max(float(p.max()) for p in panels)
    ny, nx = panels[0].shape
    bounds = (
        -spacing[2] / 2,
        (nx - 0.5) * spacing[2],
        -spacing[1] / 2,
        (ny - 0.5) * spacing[1],
    )
    fig, axes = plt.subplots(
        1, 3, figsize=(12, 4.1), sharex=True, sharey=True, layout="constrained"
    )
    titles = (
        "Observed dc / original mass",
        "After native profile division",
        "Independent h at bead anchor",
    )
    for axis, panel, title in zip(axes, panels, titles, strict=True):
        image = axis.imshow(
            panel,
            origin="lower",
            extent=bounds,
            cmap="viridis",
            vmin=lower,
            vmax=upper,
            interpolation="nearest",
            aspect="equal",
        )
        axis.scatter(
            anchor[2] * spacing[2],
            anchor[1] * spacing[1],
            marker="+",
            color="black",
            s=130,
            linewidths=2,
            label="Independent bead anchor",
        )
        axis.set_title(title)
        axis.set_xlabel("x [µm]")
    axes[0].set_ylabel("y [µm]")
    axes[0].scatter(
        peak[2] * spacing[2],
        peak[1] * spacing[1],
        marker="D",
        facecolors="none",
        edgecolors="black",
        s=90,
        linewidths=1.8,
        label="Observed raw dc peak",
    )
    fig.colorbar(image, ax=axes.tolist(), shrink=0.8, label="Normalized per-site weight [1]")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, frameon=False)
    fig.suptitle(
        f"Profile compensation precedes centering: z = {z * spacing[0]:g} µm\n"
        f"Raw peak {peak}; compensated anchor {anchor}",
        fontsize=13,
    )
    fig.savefig(destination / "bead-compensation.png", dpi=180)
    plt.close(fig)


def signed_sampling(data, metadata, destination):
    """Show all signed rows on a distinct declared specimen frequency grid."""
    expected = data["dense_sample_expected"]
    returned = data["sample_returned"]
    limit = 1.06 * float(
        max(
            np.max(abs(expected.real)),
            np.max(abs(expected.imag)),
            np.max(abs(returned.real)),
            np.max(abs(returned.imag)),
        )
    )
    fig, axes = plt.subplots(
        5, 2, figsize=(10.5, 10), sharex=True, sharey=True, layout="constrained"
    )
    for row, order in enumerate(data["orders"]):
        for column, part in enumerate(("real", "imag")):
            axis = axes[row, column]
            axis.axhline(0, color="0.8", linewidth=0.6)
            axis.plot(
                data["dense_query_points"][:, 2],
                getattr(expected[row], part),
                color="#17658d",
                linewidth=1.8,
                label="Independent complex interpolant",
            )
            axis.scatter(
                data["query_points"][row, :, 2],
                getattr(returned[row], part),
                color="#d56922",
                s=27,
                marker="o",
                label="Returned specimen-grid query",
            )
            axis.set_ylim(-limit, limit)
            axis.grid(axis="x", alpha=0.15)
        axes[row, 0].set_ylabel(f"Order {int(order):+d}\nTransfer [1]")
    axes[0, 0].set_title("Real part")
    axes[0, 1].set_title("Imaginary part")
    for axis in axes[-1]:
        axis.set_xlabel("Detector f_x [cycles/µm]; f_y = f_z = 0")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, frameon=False)
    fig.suptitle(
        "Signed complex sampling on a distinct specimen grid\n"
        "Shared vertical scale; explicit object frequencies f = detector − m q",
        fontsize=14,
    )
    fig.savefig(destination / "signed-sampling.png", dpi=180)
    plt.close(fig)


def main():
    """Render one retained numerical cohort into a new directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source, destination = args.observations.resolve(), args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    started = time.time()
    inputs = {name: sha256(source / name) for name in ("observation.json", "observations.npz")}
    metadata = json.loads((source / "observation.json").read_text())
    with np.load(source / "observations.npz") as archive:
        data = {key: archive[key].copy() for key in archive.files}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    complex_planes(data, metadata, destination)
    bead_anchor(data, metadata, destination)
    signed_sampling(data, metadata, destination)
    after = {name: sha256(source / name) for name in inputs}
    if inputs != after:
        raise ValueError("retained scientific input changed during rendering")
    record = {
        "argv": sys.argv,
        "started_unix_s": started,
        "completed_unix_s": time.time(),
        "python": sys.executable,
        "python_version": platform.python_version(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "renderer_sha256": sha256(Path(__file__).resolve()),
        "source_inputs_before": inputs,
        "source_inputs_after": after,
        "annotation_qualification": {
            "raw_dc_peak_recorded_by_original_measurement": metadata["raw_dc_peak_zyx"],
            "raw_dc_peak_zyx_derived_from_retained_dc": [
                int(x)
                for x in np.unravel_index(
                    np.argmax(data["returned_components"][0].real),
                    data["returned_components"][0].shape,
                )
            ],
            "method": "Use retained spatial dc shape, excluding the phase axis of exposure data.",
            "original_measurement_metadata_changed": False,
        },
        "images": {
            p.name: {"sha256": sha256(p), "size_bytes": p.stat().st_size}
            for p in sorted(destination.glob("*.png"))
        },
        "limits": "Retained values only; no scientific regeneration, masking or per-order scaling.",
    }
    (destination / "render-manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record["images"], indent=2))


if __name__ == "__main__":
    main()
