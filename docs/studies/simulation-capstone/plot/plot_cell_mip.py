"""Render the baseline synthetic cell as three matched XY depth projections."""

import argparse
import json
from pathlib import Path

import baseline_inputs
import matplotlib
import numpy as np
import plot_phantoms as phantoms
from matplotlib.colors import AsinhNorm
from matplotlib.figure import Figure

STEM = "cell-xy-mip"


def _figure(axes, volumes):
    x, y, z = axes
    xy = phantoms.CELL_XYLIM
    maxima = [volume.max(axis=0) for volume in volumes]
    norm = AsinhNorm(linear_width=0.025, vmin=-0.10, vmax=2.60)
    cmap = phantoms._signed_palette(norm)
    ranges = [phantoms._display_range(plane, x, y, xy, xy) for plane in maxima]
    scale = phantoms._scale_details(norm, ranges)

    fig = Figure(figsize=(10.7, 3.75))
    fig.text(0.075, 0.955, "Synthetic cell interior", fontsize=19, weight="bold", va="top")
    z_range = f"{z[0]:+.3f} to {z[-1]:+.3f} µm".replace("-", "−")
    fig.text(
        0.075,
        0.875,
        f"XY maximum-intensity projections over all {z.size} z planes ({z_range})",
        fontsize=10.4,
        color=phantoms.SLATE,
        va="top",
    )
    grid = fig.add_gridspec(
        1,
        4,
        left=0.075,
        right=0.891,
        top=0.753,
        bottom=0.140,
        width_ratios=(1, 1, 1, 0.054),
        wspace=0.19,
    )
    for col, (plane, title) in enumerate(zip(maxima, phantoms.TITLES, strict=True)):
        ax = fig.add_subplot(grid[0, col])
        artist = phantoms._plane_image(ax, plane, x, y, norm, cmap, xy, xy)
        phantoms._add_panel_title(ax, "ABC"[col], title)
        ax.set(xticks=(-3, 0, 3), yticks=(-3, 0, 3), xlabel="x (µm)")
        if col == 0:
            ax.set_ylabel("y (µm)")
        else:
            ax.tick_params(labelleft=False)
    phantoms._colorbar(
        fig,
        artist,
        fig.add_subplot(grid[0, 3]),
        "Shared intensity (SU, asinh)",
        (-0.10, 0, 0.10, 0.5, 1.2, 2.6),
        orientation="vertical",
    )
    return fig, {
        "projection": "maximum over all z sample centers of signed intensity, without clipping",
        "projected_z_sample_centers_um": [float(z[0]), float(z[-1])],
        "projected_xy_limits_um": [xy, xy],
        "displayed_sample_range_convention": "sample centers inside the displayed limits",
        "projection_intensity": scale,
        "panel_ranges_su": dict(zip(phantoms.SCORE_KEYS, ranges, strict=True)),
    }


def main():
    """Verify the exact baseline inputs and write the projection and its provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--runtime-receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    try:
        axes, counts, truth, conventional, inputs = baseline_inputs.read_baseline(
            "cell",
            args.case_dir / "truth.npy",
            args.case_dir / "conventional.npy",
            args.observations,
            args.runtime_receipt,
        )
        volumes = phantoms._volume_data(axes, counts, truth, conventional)
        fig, display = _figure(axes, volumes)
        args.output_dir.mkdir(parents=True)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    png = args.output_dir / f"{STEM}.png"
    pdf = args.output_dir / f"{STEM}.pdf"
    metadata = args.output_dir / f"{STEM}.json"
    title = "Synthetic cell XY maximum-intensity projections"
    fig.savefig(png, dpi=184, metadata={"Title": title})
    fig.savefig(pdf, dpi=220, metadata={"Title": title, "CreationDate": None})
    zyx = axes[::-1]
    record = {
        "case": "cell",
        "units": {"intensity": "simulation source units (SU)", "coordinate": "µm"},
        "wiener": baseline_inputs.BASELINE_WIENER,
        "gain_su_per_reconstruction_count": phantoms.GAIN_SU_PER_COUNT,
        "axes_zyx_origin_um": [float(axis[0]) for axis in zyx],
        "axes_zyx_pitch_um": [float((axis[-1] - axis[0]) / (len(axis) - 1)) for axis in zyx],
        "shape_zyx": list(truth.shape),
        "inputs_sha256": inputs,
        "plot_script_sha256": phantoms._sha256(Path(__file__)),
        "plot_phantoms_sha256": phantoms._sha256(Path(phantoms.__file__)),
        "baseline_inputs_sha256": phantoms._sha256(Path(baseline_inputs.__file__)),
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
        "display": display,
        "figures_sha256": {path.name: phantoms._sha256(path) for path in (png, pdf)},
    }
    metadata.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
