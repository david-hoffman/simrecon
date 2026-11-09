"""Render the accepted finite-bead and synthetic-cell comparisons."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import baseline_inputs
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import AsinhNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

GAIN_SU_PER_COUNT = 0.000020
TITLES = ("Fluorescence truth", "Same-exposure mean", "SIMrecon")
SCORE_KEYS = ("truth", "same_dose_conventional", "reconstruction")
COLORS = ("#202633", "#b04b1f", "#126d8b")
INK = "#202633"
SLATE = "#515a6b"
CENTER = "#697589"
BOX = "#88e5e6"
# From the frozen evaluator scene and profiles. Coordinates are x, y in µm.
PAIRS = (
    ("P14", 0.14, -0.897, -1.658),
    ("P23", 0.23, 1.359, -0.519),
    ("P45", 0.45, 0.658, 1.815),
)
PROFILE_UM = np.arange(-140, 141) * 0.005
BEAD_XLIM = (-3.60, 3.50)
BEAD_YLIM = (-2.80, 3.10)
CELL_XYLIM = (-3.30, 3.30)
CELL_ZLIM = (-1.90, 1.90)
CELL_XY_Z = -0.750
CELL_XZ_Y = 0.440

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10.0,
        "text.color": INK,
        "axes.labelcolor": SLATE,
        "axes.edgecolor": "#a0a7b3",
        "axes.linewidth": 0.6,
        "axes.unicode_minus": True,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "xtick.labelsize": 9.0,
        "ytick.labelsize": 9.0,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "pdf.compression": 9,
    }
)


def _sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _bounds(axis):
    return (float(axis[0] - (axis[1] - axis[0]) / 2), float(axis[-1] + (axis[-1] - axis[-2]) / 2))


def _volume_data(axes, counts, truth, conventional):
    shape = tuple(len(axis) for axis in reversed(axes))
    if counts.shape == (1, *shape):
        counts = counts[0]
    volumes = (truth, conventional, counts * GAIN_SU_PER_COUNT)
    for axis in axes:
        if axis.ndim != 1 or axis.size < 2 or not np.isfinite(axis).all():
            raise ValueError("Expected a finite one-dimensional physical coordinate axis")
        if axis[1] <= axis[0] or not np.allclose(np.diff(axis), axis[1] - axis[0]):
            raise ValueError("Expected a uniformly increasing physical coordinate axis")
    if any(volume.shape != shape or not np.isfinite(volume).all() for volume in volumes):
        raise ValueError(f"Expected finite volumes in Z × Y × X order with shape {shape}")
    return volumes


def _signed_palette(norm):
    # Zero is almost black. Cyan marks negative values and warm hues mark positive values.
    values = np.linspace(0.0, 1.0, 2048)
    zero = float(norm(0))
    positive = np.clip((values - zero) / (1.0 - zero), 0.0, 1.0)
    colors = matplotlib.colormaps["magma"](positive)
    negative = values < zero
    strength = ((zero - values[negative]) / zero)[:, None]
    cyan = np.array([0.20, 0.60, 0.76])
    colors[negative, :3] = colors[negative, :3] * (1.0 - strength) + cyan * strength
    return ListedColormap(colors, name="signed_intensity")


def _plane_image(ax, plane, horizontal, vertical, norm, cmap, xlim, ylim):
    artist = ax.imshow(
        plane,
        extent=(*_bounds(horizontal), *_bounds(vertical)),
        origin="lower",
        aspect="equal",
        interpolation="nearest",
        norm=norm,
        cmap=cmap,
    )
    ax.set(xlim=xlim, ylim=ylim)
    ax.tick_params(length=3, width=0.6, pad=2.5)
    return artist


def _add_panel_title(ax, letter, title=""):
    ax.text(
        0.0,
        1.025,
        letter,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="bottom",
        ha="left",
    )
    if title:
        ax.text(
            0.5,
            1.025,
            title,
            transform=ax.transAxes,
            fontsize=10.6,
            fontweight="normal",
            va="bottom",
            ha="center",
        )


def _scale_number(value, _position):
    return f"{value:g}".replace("-", "−")


def _colorbar(fig, artist, cax, label, ticks, orientation="horizontal"):
    bar = fig.colorbar(
        artist, cax=cax, orientation=orientation, ticks=ticks, format=FuncFormatter(_scale_number)
    )
    bar.set_label(label, fontsize=9, labelpad=4)
    bar.ax.tick_params(length=2.5, width=0.6, pad=2, labelsize=8.5)
    bar.minorticks_off()


def _add_header(fig, title, subtitle):
    fig.text(0.078, 0.961, title, fontsize=19, weight="bold", va="top")
    fig.text(0.078, 0.904, subtitle, fontsize=10.4, color=SLATE, va="top")


def _display_range(plane, x, v, xlim, vlim):
    keep_x = (x >= xlim[0]) & (x <= xlim[1])
    keep_v = (v >= vlim[0]) & (v <= vlim[1])
    displayed = plane[np.ix_(keep_v, keep_x)]
    return [float(displayed.min()), float(displayed.max())]


def _scale_details(norm, ranges):
    lower = min(pair[0] for pair in ranges)
    upper = max(pair[1] for pair in ranges)
    if lower < norm.vmin or upper > norm.vmax:
        raise ValueError(f"Data range [{lower:g}, {upper:g}] exceeds fixed color scale")
    return {
        "color_scale_su": [norm.vmin, norm.vmax],
        "displayed_sample_range_su": [lower, upper],
        "transform": "asinh",
        "linear_width_su": norm.linear_width,
    }


def _bead_figure(axes, volumes, report):
    x, y, _ = axes
    norm = AsinhNorm(linear_width=0.005, vmin=-0.50, vmax=20)
    cmap = _signed_palette(norm)
    fig = plt.figure(figsize=(11.2, 7.1))
    _add_header(
        fig,
        "Finite fluorescent bead phantom",
        "Depth maxima on the same intensity scale, with profiles through three marked pairs",
    )
    grid = fig.add_gridspec(
        2,
        4,
        left=0.078,
        right=0.933,
        top=0.84,
        bottom=0.164,
        width_ratios=(1, 1, 1, 0.053),
        height_ratios=(1.13, 1),
        wspace=0.24,
        hspace=0.45,
    )
    ranges = []
    for col, (volume, title) in enumerate(zip(volumes, TITLES, strict=True)):
        ax = fig.add_subplot(grid[0, col])
        maximum = volume.max(axis=0)
        artist = _plane_image(ax, maximum, x, y, norm, cmap, BEAD_XLIM, BEAD_YLIM)
        ranges.append(_display_range(maximum, x, y, BEAD_XLIM, BEAD_YLIM))
        _add_panel_title(ax, "ABC"[col], title)
        ax.set(xticks=(-3, 0, 3), yticks=(-2, 0, 2), xlabel="x (µm)")
        if col == 0:
            ax.set_ylabel("y (µm)")
        else:
            ax.tick_params(labelleft=False)
        for letter, (_, _, cx, cy) in zip("DEF", PAIRS, strict=True):
            ax.add_patch(
                Rectangle(
                    (cx - 0.34, cy - 0.34),
                    0.68,
                    0.68,
                    linewidth=0.9,
                    edgecolor=BOX,
                    facecolor="none",
                )
            )
            ax.text(
                cx + 0.43, cy + 0.33, letter, color=BOX, weight="bold", fontsize=8.3, va="center"
            )
    _colorbar(
        fig,
        artist,
        fig.add_subplot(grid[0, 3]),
        "Intensity (SU, asinh)",
        (-0.5, 0, 0.02, 0.1, 1, 20),
        orientation="vertical",
    )

    comparison = report["comparison"]
    profiles = {}
    for col, (key, spacing, cx, cy) in enumerate(PAIRS):
        ax = fig.add_subplot(grid[1, col])
        _add_panel_title(ax, "DEF"[col], f"{spacing:.2f} µm truth spacing")
        ax.axhline(0, linewidth=0.75, color="#aab3bf", zorder=0)
        for center in (-spacing / 2, spacing / 2):
            ax.axvline(center, color=CENTER, linestyle=":", linewidth=1.05, zorder=1)
        for score_key, color, linestyle in zip(SCORE_KEYS, COLORS, ("-", "--", "-"), strict=True):
            score = comparison[score_key]["metrics"][key]
            profile = np.asarray(score["profile_su"], dtype=float) - score["baseline_su"]
            if profile.shape != PROFILE_UM.shape or not np.isfinite(profile).all():
                raise ValueError(f"{score_key}/{key} does not contain the frozen profile")
            peak = float(profile.max())
            if peak <= 0:
                raise ValueError(f"{score_key}/{key} has no positive peak for normalization")
            ax.plot(PROFILE_UM, profile / peak, color=color, linestyle=linestyle, linewidth=1.55)
        ax.set(
            xlim=(-0.48, 0.48),
            ylim=(-0.17, 1.06),
            xticks=(-0.4, -0.2, 0, 0.2, 0.4),
            yticks=(-0.1, 0, 0.5, 1),
            xlabel="Distance from pair midpoint (µm)",
        )
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(length=3, width=0.6)
        if col == 0:
            ax.set_ylabel("Baseline-adjusted intensity\n÷ own profile peak")
        else:
            ax.tick_params(labelleft=False)
        profiles[key] = {
            "true_center_separation_um": spacing,
            "box_center_xy_um": [cx, cy],
            "frozen_decision": {
                name: {
                    field: comparison[name]["metrics"][key][field]
                    for field in (
                        "status",
                        "separation_um",
                        "valley_dip_fraction",
                    )
                }
                for name in SCORE_KEYS
            },
        }
    handles = [
        Line2D([], [], color=c, linestyle=style, linewidth=1.55, label=title)
        for c, style, title in zip(COLORS, ("-", "--", "-"), TITLES, strict=True)
    ]
    handles.append(
        Line2D([], [], color=CENTER, linestyle=":", linewidth=1.1, label="True sphere centers")
    )
    fig.legend(
        handles=handles,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.030),
        ncol=4,
        frameon=False,
        fontsize=9.3,
        handlelength=2.7,
    )
    return fig, {
        "projection": "maximum over z of signed intensity, without clipping",
        "projected_xy_limits_um": [BEAD_XLIM, BEAD_YLIM],
        "projection_intensity": _scale_details(norm, ranges),
        "profile_sampling_um": {"start": -0.7, "stop_inclusive": 0.7, "pitch": 0.005},
        "profile_display_limits_um": [-0.48, 0.48],
        "profile_scaling": "subtract frozen baseline, then divide by each trace's own peak",
        "profiles": profiles,
    }


def _sample_index(axis, coordinate):
    matches = np.flatnonzero(np.isclose(axis, coordinate, rtol=0, atol=1e-9))
    if len(matches) != 1:
        raise ValueError(f"Expected the frozen coordinate {coordinate:+.3f} µm on the grid")
    return int(matches[0])


def _cell_figure(axes, volumes):
    x, y, z = axes
    zi = _sample_index(z, CELL_XY_Z)
    yi = _sample_index(y, CELL_XZ_Y)
    residual = volumes[2] - volumes[0]
    norm = AsinhNorm(linear_width=0.025, vmin=-0.10, vmax=2.60)
    error_norm = AsinhNorm(linear_width=0.035, vmin=-0.55, vmax=0.55)
    cmap = _signed_palette(norm)
    fig = plt.figure(figsize=(11.5, 6.5))
    _add_header(
        fig,
        "Synthetic cell interior",
        "XY at z = −0.750 µm (top) and XZ at y = +0.440 µm (bottom)",
    )
    grid = fig.add_gridspec(
        2,
        4,
        left=0.078,
        right=0.973,
        top=0.83,
        bottom=0.22,
        height_ratios=(1, 3.8 / 6.6),
        wspace=0.14,
        hspace=0.28,
    )
    intensity_ranges = []
    residual_ranges = []
    artists = []
    for row in range(2):
        for col, (volume, title) in enumerate(
            zip((*volumes, residual), (*TITLES, "SIMrecon − truth"), strict=True)
        ):
            ax = fig.add_subplot(grid[row, col])
            plane = volume[zi, :, :] if row == 0 else volume[:, yi, :]
            vertical = y if row == 0 else z
            ylim = CELL_XYLIM if row == 0 else CELL_ZLIM
            artist = _plane_image(
                ax,
                plane,
                x,
                vertical,
                error_norm if col == 3 else norm,
                "RdBu_r" if col == 3 else cmap,
                CELL_XYLIM,
                ylim,
            )
            ranges = residual_ranges if col == 3 else intensity_ranges
            ranges.append(_display_range(plane, x, vertical, CELL_XYLIM, ylim))
            _add_panel_title(ax, "ABCDEFGH"[4 * row + col], title if row == 0 else "")
            ax.set_xticks((-3, 0, 3))
            ax.set_yticks((-3, 0, 3) if row == 0 else (-1.5, 0, 1.5))
            if row == 0:
                ax.tick_params(labelbottom=False)
            else:
                ax.set_xlabel("x (µm)", labelpad=2)
            if col == 0:
                label = "y (µm)" if row == 0 else "z (µm)"
                ax.set_ylabel(label, labelpad=2)
            else:
                ax.tick_params(labelleft=False)
            if row == 1:
                artists.append(artist)

    intensity_bar = fig.add_axes([0.138, 0.115, 0.517, 0.022])
    error_bar = fig.add_axes([0.759, 0.115, 0.205, 0.022])
    _colorbar(
        fig,
        artists[2],
        intensity_bar,
        "Shared intensity (SU, asinh)",
        (-0.10, 0, 0.10, 0.5, 1.2, 2.6),
    )
    _colorbar(
        fig, artists[3], error_bar, "Signed residual (SU, asinh)", (-0.55, -0.10, 0, 0.10, 0.55)
    )
    return fig, {
        "xy_z_um": float(z[zi]),
        "xz_y_um": float(y[yi]),
        "xy_limits_um": [CELL_XYLIM, CELL_XYLIM],
        "xz_limits_um": [CELL_XYLIM, CELL_ZLIM],
        "intensity": _scale_details(norm, intensity_ranges),
        "residual": {
            "quantity": "signed reconstruction minus fluorescence truth",
            **_scale_details(error_norm, residual_ranges),
            "displayed_xy_sample_range_su": residual_ranges[0],
            "displayed_xz_sample_range_su": residual_ranges[1],
        },
    }


def main():
    """Load explicit case inputs and write figures with their provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("beads", "cell"))
    parser.add_argument(
        "--observations", type=Path, required=True, help="archive from the 0.020 Wiener run"
    )
    parser.add_argument(
        "--runtime-receipt", type=Path, required=True, help="runtime.json from the same run"
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="new directory to create")
    parser.add_argument(
        "--case-dir", type=Path, help="directory with truth.npy and conventional.npy"
    )
    parser.add_argument("--truth", type=Path)
    parser.add_argument("--conventional", type=Path)
    parser.add_argument(
        "--scores", type=Path, help="matching frozen score JSON; required for beads"
    )
    args = parser.parse_args()
    if args.case_dir is not None:
        if args.truth is not None or args.conventional is not None:
            parser.error("use --case-dir or the explicit --truth and --conventional pair")
        truth = args.case_dir / "truth.npy"
        conventional = args.case_dir / "conventional.npy"
    else:
        if args.truth is None or args.conventional is None:
            parser.error("supply --case-dir or both --truth and --conventional")
        truth, conventional = args.truth, args.conventional
    if args.case == "beads" and args.scores is None:
        parser.error("beads requires --scores")

    try:
        axes, counts, truth_volume, conventional_volume, inputs = baseline_inputs.read_baseline(
            args.case, truth, conventional, args.observations, args.runtime_receipt
        )
        volumes = _volume_data(axes, counts, truth_volume, conventional_volume)
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))
    observation_hash = inputs["observations.npz"]
    report = None
    if args.scores is not None:
        report = json.loads(args.scores.read_text(encoding="utf-8"))
        if report.get("status") != 0 or report.get("receipt_sha256") != observation_hash:
            parser.error("scores must be accepted and match the observation archive digest")
        inputs["scores.json"] = _sha256(args.scores)
    try:
        args.output_dir.mkdir(parents=True)
    except OSError as error:
        parser.error(f"cannot create a fresh output directory: {error}")
    outputs = {ext: args.output_dir / f"{args.case}.{ext}" for ext in ("png", "pdf", "json")}
    if args.case == "beads":
        fig, display = _bead_figure(axes, volumes, report)
    else:
        fig, display = _cell_figure(axes, volumes)
    fig.savefig(outputs["png"], dpi=184, metadata={"Title": f"{args.case} phantom"})
    fig.savefig(
        outputs["pdf"],
        dpi=220,
        metadata={
            "Title": f"{args.case} phantom",
            "CreationDate": None,
        },
    )
    plt.close(fig)
    x, y, z = axes
    record = {
        "case": args.case,
        "units": {"intensity": "simulation source units (SU)", "coordinate": "µm"},
        "wiener": baseline_inputs.BASELINE_WIENER,
        "gain_su_per_reconstruction_count": GAIN_SU_PER_COUNT,
        "axes_zyx_origin_um": [float(axis[0]) for axis in (z, y, x)],
        "axes_zyx_pitch_um": [float((axis[-1] - axis[0]) / (len(axis) - 1)) for axis in (z, y, x)],
        "shape_zyx": list(volumes[0].shape),
        "displayed_sample_range_convention": "sample centers inside the displayed limits",
        "inputs_sha256": inputs,
        "plot_script_sha256": _sha256(Path(__file__)),
        "baseline_inputs_sha256": _sha256(Path(baseline_inputs.__file__)),
        "numpy_version": np.__version__,
        "matplotlib_version": matplotlib.__version__,
        "display": display,
        "figures_sha256": {outputs[ext].name: _sha256(outputs[ext]) for ext in ("png", "pdf")},
    }
    outputs["json"].write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
