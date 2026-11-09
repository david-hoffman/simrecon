"""Render the signed cell close-pair section and its fixed lateral profile."""

import argparse
import json
from pathlib import Path

import baseline_inputs
import check_cell_detail as detail
import matplotlib
import numpy as np
import plot_phantoms as phantoms
from matplotlib.colors import AsinhNorm, Normalize
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

MID_X_UM, Y_UM, Z_UM = 0.56, -0.04, 0.50
CROP_RADIUS_SAMPLES = 8
OBSERVED_LINEAR_WIDTH_SU = 0.12
COLORS = (phantoms.COLORS[1], phantoms.COLORS[2], phantoms.INK)


def _figure(offset_nm, planes, profiles, sim_score, crop_start):
    separation_nm = sim_score["spacing_um"] * 1000
    dip_percent = sim_score["dip_fraction"] * 100
    extent = (*phantoms._bounds(offset_nm), *phantoms._bounds(offset_nm))
    truth_max = float(np.ceil(planes[0].max()))
    observed_low = min(0, float(min(plane.min() for plane in planes[1:])))
    observed_high = float(max(plane.max() for plane in planes[1:]))
    norms = (
        Normalize(0, truth_max),
        AsinhNorm(OBSERVED_LINEAR_WIDTH_SU, vmin=observed_low, vmax=observed_high),
    )

    fig = Figure(figsize=(7.5, 5.75))
    fig.text(0.105, 0.946, "A close pair in the synthetic cell", size=19, weight="bold")
    fig.text(
        0.105,
        0.906,
        "160 nm emitter spacing · XY section at z = +0.50 µm",
        size=10.5,
        color=phantoms.SLATE,
    )
    grid = fig.add_gridspec(
        4,
        3,
        left=0.106,
        right=0.962,
        top=0.850,
        bottom=0.104,
        height_ratios=(1.04, 0.065, 0.26, 0.92),
        hspace=0.30,
        wspace=0.18,
    )
    for col, (plane, title) in enumerate(
        zip(planes, ("Truth", "Exposure mean", "SIMrecon"), strict=True)
    ):
        ax = fig.add_subplot(grid[0, col])
        artist = ax.imshow(
            plane,
            origin="lower",
            interpolation="nearest",
            extent=extent,
            cmap="gray",
            norm=norms[0 if col == 0 else 1],
        )
        phantoms._add_panel_title(ax, "ABC"[col], title)
        ax.set(xticks=[], yticks=[])
        ax.plot([-337, -309], [0, 0], color=phantoms.SLATE, linewidth=1.5, clip_on=False)
        ax.plot([309, 337], [0, 0], color=phantoms.SLATE, linewidth=1.5, clip_on=False)
        if col == 0:
            ax.plot([-280, -80], [-260, -260], color="white", linewidth=2, solid_capstyle="butt")
            ax.text(-180, -230, "200 nm", color="white", size=8.5, ha="center")
            bar = fig.colorbar(artist, cax=fig.add_subplot(grid[1, 0]), orientation="horizontal")
            bar.locator = MaxNLocator(nbins=4)
            bar.update_ticks()
            bar.set_label("Truth intensity (SU)", size=9)
        elif col == 2:
            bar = fig.colorbar(artist, cax=fig.add_subplot(grid[1, 1:]), orientation="horizontal")
            ticks = [
                tick
                for tick in (-0.25, -0.08, 0.0, 0.08, 0.25, 1.0, 3.0)
                if observed_low <= tick <= observed_high
            ]
            bar.set_ticks(ticks, labels=[f"{tick:g}".replace("-", "−") for tick in ticks])
            bar.minorticks_off()
            bar.set_label("Shared signed intensity (SU, asinh)", size=9)

    ax = fig.add_subplot(grid[3, :])
    ax.axhline(0, linewidth=0.65, color="#b9c0ca")
    for center in (-80, 80):
        ax.axvline(center, linewidth=0.9, linestyle="--", color="#a9b2bf")
    for profile, color, label, linestyle in zip(
        profiles,
        COLORS,
        ("Exposure average", "SIMrecon", "Original single punctum (SIMrecon)"),
        ("-", "-", ":"),
        strict=True,
    ):
        ax.plot(
            offset_nm,
            profile,
            color=color,
            marker="o",
            markersize=3.2,
            linewidth=1.5,
            linestyle=linestyle,
            label=label,
        )
    peak_indices = [peak["x_index"] - crop_start for peak in sim_score["peaks"]]
    ax.scatter(
        offset_nm[peak_indices],
        profiles[1][peak_indices],
        facecolors="white",
        edgecolors=COLORS[1],
        linewidth=1.3,
        s=37,
        zorder=4,
    )
    valley_index = sim_score["valley"]["x_index"] - crop_start
    ax.scatter(
        offset_nm[valley_index],
        profiles[1][valley_index],
        marker="D",
        color=COLORS[1],
        s=22,
        zorder=4,
    )
    ax.set(
        xlim=(-335, 335),
        xticks=(-320, -240, -160, -80, 0, 80, 160, 240, 320),
        xlabel="Lateral offset from pair midpoint (nm)",
        ylabel="Signed intensity (SU)",
    )
    ax.spines[["top", "right"]].set_visible(False)
    inset = ax.inset_axes([0.055, 0.57, 0.20, 0.38])
    inset.plot(offset_nm, profiles[0], color=COLORS[0], linewidth=1.15, marker="o", markersize=2.2)
    inset.set(xlim=(-160, 160), xticks=(-160, 0, 160), title="Exposure average (zoom)")
    inset.set_ylabel("SU", fontsize=7, labelpad=2)
    inset.yaxis.set_major_locator(MaxNLocator(nbins=3))
    inset.tick_params(labelsize=7, length=2, pad=1.5)
    inset.title.set_fontsize(7.5)
    inset.spines[["top", "right"]].set_visible(False)
    ax.text(
        0.0,
        1.075,
        "D   Lateral profile",
        transform=ax.transAxes,
        va="bottom",
        size=11.5,
        weight="bold",
    )
    ax.text(
        1.0,
        1.075,
        f"SIMrecon: {separation_nm:.0f} nm between peaks, {dip_percent:.1f}% dip",
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        size=9.5,
        color=COLORS[1],
    )
    ax.legend(
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.185),
        frameon=False,
        fontsize=8.6,
        columnspacing=1.1,
        handlelength=1.8,
    )
    return fig, {
        "truth_linear_limits_su": [0, truth_max],
        "shared_observed_asinh_limits_su": [observed_low, observed_high],
        "shared_observed_asinh_linear_width_su": OBSERVED_LINEAR_WIDTH_SU,
    }


def main():
    """Render the measured four-arm comparison after checking the full study receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("detail-input", "detail-output", "base-input", "base-output", "figure-output"):
        parser.add_argument(field.replace("-", "_"), type=Path)
    args = parser.parse_args()

    try:
        receipt = detail.study_receipt(
            args.detail_input, args.detail_output, args.base_input, args.base_output
        )
        if receipt["status"] != "pass":
            raise ValueError("cell-detail study did not pass the fixed comparison")
        base_axes, base_counts, _, _, base_inputs = _read_case(
            "cell", args.base_input, args.base_output
        )
        axes, counts, truth, conventional, detail_inputs = _read_case(
            "cell-detail", args.detail_input, args.detail_output
        )
        _check_rendered_inputs(receipt, detail_inputs, base_inputs)
        if any(not np.array_equal(a, b) for a, b in zip(axes, base_axes, strict=True)):
            raise ValueError("control and pair coordinates differ")
        z, y, x = detail.Z_INDEX, detail.Y_INDEX, detail.MIDPOINT_INDEX
        radius = CROP_RADIUS_SAMPLES
        rows, cols = slice(y - radius, y + radius + 1), slice(x - radius, x + radius + 1)
        offset_nm = (np.arange(cols.start, cols.stop) - x) * detail.PITCH_NM
        planes = (
            truth[z, rows, cols],
            conventional[z, rows, cols],
            counts[z, rows, cols] * detail.SU_PER_COUNT,
        )
        profiles = (
            conventional[z, y, cols],
            counts[z, y, cols] * detail.SU_PER_COUNT,
            base_counts[z, y, cols] * detail.SU_PER_COUNT,
        )
        fig, scales = _figure(
            offset_nm, planes, profiles, receipt["arms"]["detail_sim"], cols.start
        )
        args.figure_output.mkdir(parents=True)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))

    destination = args.figure_output / "cell-close-pair"
    title = "A close pair in the synthetic cell"
    png, pdf = destination.with_suffix(".png"), destination.with_suffix(".pdf")
    fig.savefig(png, dpi=220, metadata={"Title": title})
    fig.savefig(pdf, dpi=300, metadata={"Title": title, "CreationDate": None})
    metadata = {
        "case": "cell-detail",
        "control": "cell",
        "wiener": detail.WIENER,
        "model_rayleigh_point_pair_um": 0.61 * 0.525 / 1.40,
        "true_lateral_fwhm_um": 2 * np.sqrt(2 * np.log(2)) * 0.0275,
        "source_center_separation_um": 0.16,
        "section": {
            "x_center_um": MID_X_UM,
            "y_center_um": Y_UM,
            "z_um": Z_UM,
            "crop_radius_samples": radius,
            "native_pitch_nm": detail.PITCH_NM,
            "image_interpolation": "nearest pixel",
            "image_intensity": scales,
            "exposure_average_profile_zoom_x_limits_nm": [-160, 160],
        },
        "measurement": receipt,
        "rendered_inputs_sha256": {"cell-detail": detail_inputs, "cell": base_inputs},
        "sources_sha256": {
            Path(module.__file__).name: phantoms._sha256(Path(module.__file__))
            for module in (baseline_inputs, detail, phantoms)
        }
        | {Path(__file__).name: phantoms._sha256(Path(__file__))},
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
        "figures_sha256": {path.name: phantoms._sha256(path) for path in (png, pdf)},
    }
    destination.with_suffix(".json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _read_case(case, input_dir, output_dir):
    return baseline_inputs.read_baseline(
        case,
        input_dir / "truth.npy",
        input_dir / "conventional.npy",
        output_dir / "w-0.020.npz",
        output_dir / "runtime.json",
    )


def _check_rendered_inputs(receipt, detail_inputs, base_inputs):
    for arm, data, label in (
        ("truth", detail_inputs, "truth.npy"),
        ("same_exposure", detail_inputs, "conventional.npy"),
        ("detail_sim", detail_inputs, "observations.npz"),
        ("base_sim", base_inputs, "observations.npz"),
    ):
        if receipt["arms"][arm]["identity"]["sha256"] != data[label]:
            raise ValueError(f"{arm}: verified and rendered files differ")


if __name__ == "__main__":
    main()
