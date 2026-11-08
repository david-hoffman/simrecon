"""Render the accepted paired structured specimen on a common physical plane."""

import argparse
import hashlib
import json
from pathlib import Path

import baseline_inputs
import matplotlib
import numpy as np
from matplotlib.colors import AsinhNorm, Normalize
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter

Z_UM = -0.250
OUTPUT_COUNT_TO_SU = 0.000020
INTENSITY_LINEAR_WIDTH_SU = 0.030
PANEL_NAMES = ("Ground truth", "Conventional", "SIMrecon", "SIMrecon − truth")


def digest(path):
    """Return the file SHA-256 digest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_arm(case, paths, runtime_path):
    """Read and align the signed display planes for one arm."""
    truth_path, conventional_path, receipt_path = paths
    (x, y, z), image, truth, conventional, digests = baseline_inputs.read_baseline(
        case, truth_path, conventional_path, receipt_path, runtime_path
    )

    for axis in (x, y, z):
        if (
            axis.ndim != 1
            or axis.size < 2
            or not np.isfinite(axis).all()
            or not (np.diff(axis) > 0).all()
        ):
            raise ValueError("Expected finite, strictly increasing coordinate vectors.")
    indices = np.flatnonzero(z == Z_UM)
    if indices.size != 1:
        raise ValueError(f"The receipt must contain the exact z = {Z_UM:.3f} µm plane.")
    index = int(indices[0])

    if image.ndim == 4 and image.shape[0] == 1:
        image = image[0]
    expected_shape = (z.size, y.size, x.size)
    if any(volume.shape != expected_shape for volume in (truth, conventional, image)):
        raise ValueError(
            f"Expected truth, comparator, and image shape {expected_shape} in Z × Y × X order."
        )

    reconstruction = image[index] * OUTPUT_COUNT_TO_SU
    planes = (truth[index], conventional[index], reconstruction, reconstruction - truth[index])
    if not all(np.isfinite(plane).all() for plane in planes):
        raise ValueError("Each displayed plane must contain finite signed values.")
    inputs = {
        "truth": {"file": truth_path.name, "sha256": digests["truth.npy"]},
        "conventional": {"file": conventional_path.name, "sha256": digests["conventional.npy"]},
        "signed_workflow_receipt": {
            "file": receipt_path.name,
            "sha256": digests["observations.npz"],
        },
    }
    if runtime_path is None:
        inputs["historical_results"] = {
            "file": "historical-results.json",
            "sha256": digests["historical-results.json"],
        }
    else:
        inputs["runtime_receipt"] = {"file": runtime_path.name, "sha256": digests["runtime.json"]}
    return (x, y, z), index, planes, inputs


def edges(axis):
    """Convert regularly spaced sample centers to outer edges."""
    step = axis[1] - axis[0]
    if not np.allclose(np.diff(axis), step, rtol=1e-10, atol=0):
        raise ValueError("Expected uniformly spaced lateral sample centers.")
    return float(axis[0] - step / 2), float(axis[-1] + step / 2)


def signed_label(value, digits=3):
    """Format a value with an explicit sign away from zero."""
    if value == 0:
        return "0"
    return f"{value:+.{digits}f}".replace("-", "−")


def value_range(planes):
    """Find the joint signed extrema across panels."""
    return [
        min(float(plane.min()) for plane in planes),
        max(float(plane.max()) for plane in planes),
    ]


def render(
    noiseless_paths, noisy_paths, destination, *, noiseless_runtime=None, noisy_runtime=None
):
    """Write the comparison figure and its input and scale provenance."""
    grid, z_index, noiseless, noiseless_inputs = read_arm(
        "clean", noiseless_paths, noiseless_runtime
    )
    noisy_grid, _, noisy, noisy_inputs = read_arm("noisy", noisy_paths, noisy_runtime)
    if not all(np.array_equal(a, b) for a, b in zip(grid, noisy_grid, strict=True)):
        raise ValueError("Both arms must have the same physical grid.")
    if not np.array_equal(noiseless[0], noisy[0]):
        raise ValueError("Both arms must have the same ground-truth plane.")

    x, y, z = grid
    extent = (*edges(x), *edges(y))
    intensity_range = value_range((*noiseless[:3], *noisy[:3]))
    residual_range = value_range((noiseless[3], noisy[3]))
    intensity_limit = max(map(abs, intensity_range))
    residual_limit = max(map(abs, residual_range))
    if not intensity_limit > 0 or not residual_limit > 0:
        raise ValueError("Expected nonzero intensity and residual ranges.")
    intensity_norm = AsinhNorm(
        INTENSITY_LINEAR_WIDTH_SU, vmin=-intensity_limit, vmax=intensity_limit
    )
    residual_norm = Normalize(vmin=-residual_limit, vmax=residual_limit)

    destination.mkdir(parents=True, exist_ok=True)
    png = destination / "structured-pair.png"
    pdf = destination / "structured-pair.pdf"
    metadata = destination / "structured-pair.json"
    if any(path.exists() for path in (png, pdf, metadata)):
        raise FileExistsError("Choose an output directory without existing structured-pair files.")

    with matplotlib.rc_context({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42}):
        fig = Figure(figsize=(10, 6.05))
        axes = fig.subplots(2, 4, sharex=True, sharey=True)
        fig.subplots_adjust(
            left=0.119, right=0.985, bottom=0.224, top=0.891, wspace=0.140, hspace=0.112
        )
        fig.text(
            0.985,
            0.979,
            f"XY plane at z = {signed_label(Z_UM)} µm",
            ha="right",
            va="top",
            fontsize=10,
        )
        for row_index, (row, planes) in enumerate(zip(axes, (noiseless, noisy), strict=True)):
            for column, (ax, plane) in enumerate(zip(row, planes, strict=True)):
                norm = residual_norm if column == 3 else intensity_norm
                artist = ax.imshow(
                    plane,
                    extent=extent,
                    origin="lower",
                    interpolation="nearest",
                    cmap="RdBu_r",
                    norm=norm,
                )
                ax.set_xticks([-4, 0, 4])
                ax.set_yticks([-4, 0, 4])
                ax.xaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
                ax.yaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
                ax.tick_params(
                    length=3, width=0.6, labelsize=9, pad=3, left=column == 0, bottom=row_index == 1
                )
                for spine in ax.spines.values():
                    spine.set_linewidth(0.6)
                    spine.set_color("#777777")
                if row_index == 0:
                    ax.set_title(PANEL_NAMES[column], fontsize=11, pad=6)
                bounds = ax.get_position()
                letter = "abcdefgh"[4 * row_index + column]
                fig.text(
                    bounds.x0,
                    bounds.y1 + 0.004,
                    letter,
                    ha="left",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                )
                if column == 2:
                    intensity_artist = artist
                if column == 3:
                    residual_artist = artist

        for row, label in zip(axes, ("Noiseless", "Paired noisy"), strict=True):
            bounds = row[0].get_position()
            fig.text(
                0.023,
                (bounds.y0 + bounds.y1) / 2,
                label,
                ha="center",
                va="center",
                rotation=90,
                fontsize=11,
                fontweight="bold",
            )
        fig.text(0.070, 0.557, "y (µm)", ha="center", va="center", rotation=90, fontsize=10)
        fig.text(0.552, 0.158, "x (µm)", ha="center", va="center", fontsize=10)

        left = axes[1, 0].get_position().x0
        middle = axes[1, 2].get_position().x1
        residual_box = axes[1, 3].get_position()
        intensity_bar = fig.add_axes((left + 0.067, 0.097, middle - left - 0.134, 0.020))
        residual_bar = fig.add_axes(
            (residual_box.x0 + 0.018, 0.097, residual_box.width - 0.036, 0.020)
        )

        inner_ticks = [value for value in (0.05, 0.30) if value < intensity_limit * 0.65]
        positives = [*inner_ticks, intensity_limit]
        intensity_ticks = [-value for value in reversed(positives)] + [0, *positives]
        for bar_axes, artist, ticks, label in (
            (
                intensity_bar,
                intensity_artist,
                intensity_ticks,
                "Shared signed intensity (SU, asinh scale)",
            ),
            (
                residual_bar,
                residual_artist,
                [-residual_limit, 0, residual_limit],
                "Signed residual (SU)",
            ),
        ):
            bar = fig.colorbar(artist, cax=bar_axes, orientation="horizontal", ticks=ticks)
            bar.set_ticks(
                ticks,
                labels=[signed_label(tick, 2 if abs(tick) in inner_ticks else 3) for tick in ticks],
            )
            bar.minorticks_off()
            bar.outline.set_linewidth(0.6)
            bar.ax.tick_params(labelsize=9, length=3, width=0.6, pad=2)
            bar.set_label(label, fontsize=10, labelpad=3)
        fig.text(
            (residual_box.x0 + residual_box.x1) / 2,
            0.010,
            f"Observed {signed_label(residual_range[0])} to {signed_label(residual_range[1])} SU",
            ha="center",
            va="bottom",
            fontsize=8,
            color="#444444",
        )

        with png.open("xb") as stream:
            fig.savefig(stream, format="png", dpi=200, facecolor="white")
        with pdf.open("xb") as stream:
            fig.savefig(
                stream,
                format="pdf",
                dpi=200,
                facecolor="white",
                metadata={"CreationDate": None, "ModDate": None},
            )

    record = {
        "inputs": {"noiseless": noiseless_inputs, "paired_noisy": noisy_inputs},
        "z_index_zero_based": z_index,
        "z_um": float(z[z_index]),
        "panel_shape_y_x": [y.size, x.size],
        "xy_extent_sample_edges_um": extent,
        "xy_spacing_um": [
            float((x[-1] - x[0]) / (x.size - 1)),
            float((y[-1] - y[0]) / (y.size - 1)),
        ],
        "orientation": "X increases rightward. Y increases upward. Nearest-neighbor display.",
        "gain_su_per_workflow_output_count": OUTPUT_COUNT_TO_SU,
        "intensity_observed_range_su": intensity_range,
        "intensity_color_limits_su": [-intensity_limit, intensity_limit],
        "intensity_asinh_linear_width_su": INTENSITY_LINEAR_WIDTH_SU,
        "residual_definition": "Scaled signed reconstruction minus ground truth.",
        "residual_observed_range_su": residual_range,
        "residual_linear_color_limits_su": [-residual_limit, residual_limit],
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
        "plot_script_sha256": digest(Path(__file__)),
        "baseline_inputs_sha256": digest(Path(baseline_inputs.__file__)),
        "outputs_sha256": {path.name: digest(path) for path in (png, pdf)},
    }
    with metadata.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")


def main():
    """Run the plotting command on the selected saved arrays."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--noiseless",
        required=True,
        nargs=3,
        type=Path,
        metavar=("TRUTH", "CONVENTIONAL", "ARCHIVE"),
    )
    parser.add_argument(
        "--noisy", required=True, nargs=3, type=Path, metavar=("TRUTH", "CONVENTIONAL", "ARCHIVE")
    )
    parser.add_argument(
        "--noiseless-runtime",
        type=Path,
        help="Noiseless runtime receipt. Omit only for the exact historical archive.",
    )
    parser.add_argument(
        "--noisy-runtime",
        type=Path,
        help="Paired noisy runtime receipt. Omit only for the exact historical archive.",
    )
    parser.add_argument("--out-dir", required=True, type=Path)
    options = parser.parse_args()
    render(
        options.noiseless,
        options.noisy,
        options.out_dir,
        noiseless_runtime=options.noiseless_runtime,
        noisy_runtime=options.noisy_runtime,
    )


if __name__ == "__main__":
    main()
