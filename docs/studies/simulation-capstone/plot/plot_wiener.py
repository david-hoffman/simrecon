"""Plot the registered, measured SIMrecon Wiener sweep."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import AsinhNorm, ListedColormap
from matplotlib.ticker import MaxNLocator, NullLocator

WIENERS = (0.002, 0.002 * math.sqrt(10), 0.020, 0.020 * math.sqrt(10), 0.200)
WIENER_LABELS = ("0.002", "0.006325", "0.020", "0.063246", "0.200")
PANEL_WIENERS = (0.002, 0.020, 0.200)
REFERENCE_WIENER = 0.020
GAIN_SU_PER_COUNT = 0.000020
CELL_Z_UM = -0.750
XY_LIMITS_UM = (-3.30, 3.30)
AXES = tuple(
    (np.arange(size) - size // 2) * pitch for size, pitch in ((256, 0.04), (256, 0.04), (32, 0.125))
)
SHAPE = (32, 256, 256)
# Exact corrected-cell independent inputs, pinned by the sweep witness.
CELL_INPUT_SHA256 = {
    "cell_truth": "9d2441dfd1652fc02f72b380000c75d0fd31b116440b740b697234ce38e4f0ac",
    "cell_conventional": "87bcb9ab2870348a5913f22b5bdb6438f6176d0b2132f079490e6a621da92524",
}
INK = "#202633"
SLATE = "#515a6b"
TEAL = "#126d8b"
RUST = "#a3441c"
GRID = "#e0e4e9"
REF = "#697589"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "text.color": INK,
        "axes.labelcolor": SLATE,
        "axes.edgecolor": "#a0a7b3",
        "axes.linewidth": 0.6,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "pdf.compression": 9,
    }
)


def _file_digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _input_receipt(path):
    return {"name": path.name, "sha256": _file_digest(path)}


def _signed_volume(array):
    if (
        array.shape != SHAPE
        or array.dtype.newbyteorder("<") != np.dtype("<f8")
        or not np.isfinite(array).all()
    ):
        raise ValueError(f"Expected a finite binary64 signed volume with Z,Y,X shape {SHAPE}")
    return array


def _read_rows(path):
    aggregate = json.loads(path.read_text(encoding="utf-8"))
    rows = {}
    for row in aggregate["rows"]:
        key = (row["case"], row["wiener"])
        if key in rows or row["effective_wiener"] != row["wiener"]:
            raise ValueError(f"Duplicate or inconsistent sweep row {key}")
        rows[key] = row
    expected = {(case, w) for case in ("cell", "beads") for w in WIENERS}
    if rows.keys() != expected:
        raise ValueError("Expected exactly ten sweep rows at the registered logarithmic values")
    return rows


def _load_observation(path, row, zi):
    with np.load(path, allow_pickle=False) as observed:
        for key, expected in zip(("x_um", "y_um", "z_um"), AXES, strict=True):
            actual = observed[key]
            if actual.dtype.newbyteorder("<") != np.dtype("<f8") or not np.array_equal(
                actual, expected
            ):
                raise ValueError(f"Unexpected physical coordinate {key} for {path.name}")
        counts = observed["image"]
    if counts.shape == (1, *SHAPE):
        counts = counts[0]
    counts = np.ascontiguousarray(_signed_volume(counts), dtype="<f8")
    identity = [
        list(counts.shape),
        counts.dtype.str,
        hashlib.sha256(memoryview(counts).cast("B")).hexdigest(),
    ]
    if row["signed_image_counts_identity"] != identity:
        raise ValueError(f"Observation does not match the measured row at w={row['wiener']:.3f}")
    return counts[zi] * GAIN_SU_PER_COUNT


def _read_inputs(args, rows):
    paths = {"cell_truth": args.cell_truth, "cell_conventional": args.cell_conventional}
    receipts = {role: _input_receipt(path) for role, path in paths.items()}
    for role, expected in CELL_INPUT_SHA256.items():
        if receipts[role]["sha256"] != expected:
            raise ValueError(f"{role} does not match the exact corrected-cell comparator pin")
    receipts["metrics"] = _input_receipt(args.metrics)
    receipts["cell_observations"] = {}
    truth, conventional = (
        _signed_volume(np.load(path, allow_pickle=False, mmap_mode="r")) for path in paths.values()
    )
    z = AXES[2]
    zi = int(np.flatnonzero(z == CELL_Z_UM).item())
    intensity = max(float(np.abs(truth).max()), float(np.abs(conventional).max()))
    residual = float(np.abs(conventional - truth).max())
    if min(intensity, residual) <= 0 or not math.isfinite(intensity + residual):
        raise ValueError("Invalid fixed display extents")
    images = [truth[zi], conventional[zi]]
    for w, path in zip(PANEL_WIENERS, args.cell_observations, strict=True):
        images.append(_load_observation(path, rows["cell", w], zi))
        receipts["cell_observations"][f"{w:.3f}"] = _input_receipt(path)
    return images, intensity, residual, receipts


def _signed_palette():
    values = np.linspace(0, 1, 2048)
    colors = matplotlib.colormaps["magma"](np.clip(2 * values - 1, 0, 1))
    negative = values < 0.5
    strength = (1 - 2 * values[negative])[:, None]
    cyan = np.array([0.20, 0.60, 0.76])
    colors[negative, :3] = colors[negative, :3] * (1 - strength) + cyan * strength
    return ListedColormap(colors, name="signed_intensity")


def _text_number(value, precision=3):
    return f"{value:.{precision}g}".replace("-", "−")


def _panel_title(ax, letter, title, y=1.025):
    ax.text(0, y, letter, transform=ax.transAxes, fontsize=11.5, weight="bold", va="bottom")
    ax.text(0.5, y, title, transform=ax.transAxes, fontsize=10.2, ha="center", va="bottom")


def _sample_details(plane, limit):
    x, y, _ = AXES
    lower, upper = XY_LIMITS_UM
    # Count pixels that intersect the visible crop, including partially displayed edge pixels.
    half_pitch = 0.020
    in_x = (x + half_pitch > lower) & (x - half_pitch < upper)
    in_y = (y + half_pitch > lower) & (y - half_pitch < upper)
    cropped = plane[np.ix_(in_y, in_x)]
    return {
        "crop_sample_range_su": [float(cropped.min()), float(cropped.max())],
        "crop_clipped_samples": int(np.count_nonzero(np.abs(cropped) > limit)),
        "full_plane_clipped_samples": int(np.count_nonzero(np.abs(plane) > limit)),
    }


def _image_panel(fig, position, plane, norm, cmap, letter, title, ticks_x, ticks_y):
    ax = fig.add_axes(position)
    x, y, _ = AXES
    extent = (x[0] - 0.020, x[-1] + 0.020, y[0] - 0.020, y[-1] + 0.020)
    ax.imshow(
        plane,
        extent=extent,
        origin="lower",
        interpolation="nearest",
        aspect="equal",
        norm=norm,
        cmap=cmap,
    )
    ax.set(xlim=XY_LIMITS_UM, ylim=XY_LIMITS_UM, xticks=(-3, 0, 3), yticks=(-3, 0, 3))
    ax.tick_params(length=3, width=0.6, pad=2.5, labelbottom=ticks_x, labelleft=ticks_y)
    if ticks_y:
        ax.set_ylabel("y (µm)", labelpad=2)
    _panel_title(ax, letter, title)
    details = _sample_details(plane, norm.vmax)
    clipped = details["crop_clipped_samples"]
    if clipped:
        ax.text(
            0.97,
            0.04,
            f"{clipped:,} clipped",
            transform=ax.transAxes,
            color="white",
            ha="right",
            va="bottom",
            fontsize=7.5,
            bbox={"facecolor": INK, "edgecolor": "none", "alpha": 0.87, "pad": 2.0},
        )
    return details


def _image_bands(fig, images, intensity, residual, rows):
    image_norm = AsinhNorm(linear_width=0.025, vmin=-intensity, vmax=intensity)
    residual_norm = AsinhNorm(linear_width=0.035, vmin=-residual, vmax=residual)
    cmap = _signed_palette()
    x_start = (0.067, 0.245, 0.423, 0.601, 0.779)
    width = 0.160
    height = width * fig.get_figwidth() / fig.get_figheight()
    top_titles = ("Fluorescence truth", "Same-exposure mean", "w = 0.002", "w = 0.020", "w = 0.200")
    residual_titles = ("Mean − truth", "0.002 − truth", "0.020 − truth", "0.200 − truth")
    ids = ("truth", "same_exposure", *(f"w_{w:.3f}" for w in PANEL_WIENERS))
    details = {"signed_su": {}, "residual_su": {}}
    for index, (key, image, title) in enumerate(zip(ids, images, top_titles, strict=True)):
        details["signed_su"][key] = _image_panel(
            fig,
            [x_start[index], 0.680, width, height],
            image,
            image_norm,
            cmap,
            "ABCDE"[index],
            title,
            index == 0,
            index == 0,
        )
    for index, (key, image, title) in enumerate(
        zip(ids[1:], images[1:], residual_titles, strict=True), start=1
    ):
        details["residual_su"][key] = _image_panel(
            fig,
            [x_start[index], 0.418, width, height],
            image - images[0],
            residual_norm,
            "RdBu_r",
            "FGHI"[index - 1],
            title,
            True,
            index == 1,
        )
    fig.text(
        0.592, 0.386, "x (µm)  •  Common 6.6 × 6.6 µm crop", ha="center", fontsize=9, color=SLATE
    )
    for y, label, norm, palette in (
        (0.575, "Signed intensity (SU)", image_norm, cmap),
        (0.486, "Image − truth (SU)", residual_norm, "RdBu_r"),
    ):
        fig.text(0.067, y + 0.020, label, fontsize=9.3, weight="bold")
        cax = fig.add_axes([0.067, y, 0.129, 0.011])
        ticks = (norm.vmin, 0, norm.vmax)
        bar = fig.colorbar(
            ScalarMappable(norm=norm, cmap=palette),
            cax=cax,
            orientation="horizontal",
            ticks=ticks,
        )
        bar.ax.set_xticklabels([_text_number(value) for value in ticks])
        bar.ax.tick_params(length=2.5, width=0.6, pad=2, labelsize=8.5)
        bar.minorticks_off()
    fig.text(
        0.067,
        0.426,
        "Asinh color scales\nBadges count clipped\nsamples in the crop.",
        fontsize=8.3,
        color=SLATE,
        linespacing=1.4,
    )
    for w in PANEL_WIENERS:
        clipping = rows["cell", w].get("panel_clipping_counts")
        if clipping is None:
            continue
        for scale in details:
            observed = details[scale][f"w_{w:.3f}"]["full_plane_clipped_samples"]
            if clipping[scale][f"xy_z={CELL_Z_UM:.3f}"] != observed:
                raise ValueError(f"Measured clipping count does not match observation at w={w:.3f}")
    return {
        "xy_z_um": CELL_Z_UM,
        "xy_limits_um": [XY_LIMITS_UM, XY_LIMITS_UM],
        "normalization": "asinh",
        "signed_su": {"limits": [-intensity, intensity], "linear_width": 0.025},
        "residual_su": {"limits": [-residual, residual], "linear_width": 0.035},
        "panels": details,
    }


def _read_series(rows):
    errors = [rows["cell", w]["metrics"]["cell"]["low_band"]["relative_error"] for w in WIENERS]
    if any(not math.isfinite(error) or error < 0 for error in errors):
        raise ValueError("Expected finite nonnegative cell low-band relative errors")
    pairs = [rows["beads", w]["metrics"]["beads"]["P14"] for w in WIENERS]
    for pair in pairs:
        status = pair["status"]
        drop = pair["valley_dip_fraction"]
        spacing = pair["separation_um"]
        if pair["truth_separation_um"] != 0.14 or status not in ("resolved", "unresolved"):
            raise ValueError("Expected the registered 0.14 µm bead pair and valid status")
        if drop is not None and (not math.isfinite(drop) or drop < 0):
            raise ValueError("Invalid signed P14 valley drop")
        if status == "resolved":
            if (
                drop is None
                or drop < 0.15
                or spacing is None
                or not math.isfinite(spacing)
                or spacing + 1e-12 < 0.10
                or pair["reason"] is not None
            ):
                raise ValueError("Resolved P14 result contradicts the registered pair rule")
        elif spacing is not None or not pair["reason"]:
            raise ValueError("Unresolved P14 result needs null spacing and a reason")
    return errors, pairs


def _chart_axis(fig, position, letter, title, y_label, tick_labels):
    ax = fig.add_axes(position)
    ax.set(xscale="log", xlim=(0.00135, 0.295), ylabel=y_label)
    ax.set_xticks(WIENERS, tick_labels)
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.grid(axis="y", color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.axvline(REFERENCE_WIENER, color=REF, linewidth=1.05, linestyle=(0, (2, 2)), zorder=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=3, width=0.6, pad=3)
    _panel_title(ax, letter, title, y=1.04)
    return ax


def _metric_panels(fig, errors, pairs):
    positions = ([0.083, 0.137, 0.373, 0.185], [0.561, 0.137, 0.372, 0.185])
    cell = _chart_axis(
        fig,
        positions[0],
        "J",
        "Cell conditioned low band",
        "Relative RMS error (%)",
        WIENER_LABELS,
    )
    cell_percent = np.asarray(errors) * 100
    upper = max(float(cell_percent.max()), 1e-6)
    cell.set_ylim(0, upper * 1.24)
    cell.plot(WIENERS, cell_percent, color=TEAL, marker="o", linewidth=1.35, markersize=5)
    for w, value in zip(WIENERS, cell_percent, strict=True):
        cell.annotate(
            f"{_text_number(value)}%",
            (w, value),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=TEAL,
            fontsize=8.5,
        )

    labels = [
        f"{label}\n{pair['separation_um']:.3f} µm"
        if pair["status"] == "resolved"
        else f"{label}\nunresolved"
        for label, pair in zip(WIENER_LABELS, pairs, strict=True)
    ]
    beads = _chart_axis(
        fig,
        positions[1],
        "K",
        "Beads · P14 (0.14 µm truth)",
        "Signed valley drop (%)",
        labels,
    )
    values = [
        np.nan if pair["valley_dip_fraction"] is None else 100 * pair["valley_dip_fraction"]
        for pair in pairs
    ]
    max_drop = max([15, *(value for value in values if math.isfinite(value))])
    missing = any(not math.isfinite(value) for value in values)
    missing_y = -0.11 * max_drop
    beads.set_ylim(-0.20 * max_drop if missing else 0, 1.26 * max_drop)
    beads.yaxis.set_major_locator(MaxNLocator(nbins=4))
    beads.set_yticks([tick for tick in beads.get_yticks() if 0 <= tick <= 1.26 * max_drop])
    beads.axhline(15, color=RUST, linewidth=0.9, linestyle=(0, (5, 3)), alpha=0.72, zorder=1)
    beads.plot(WIENERS, values, linewidth=1.15, color=RUST, alpha=0.7)
    for w, value, pair in zip(WIENERS, values, pairs, strict=True):
        if not math.isfinite(value):
            beads.plot(w, missing_y, marker="x", markersize=6, color=RUST, linestyle="none")
            continue
        beads.plot(
            w,
            value,
            marker="o",
            markersize=5.5,
            markeredgecolor=RUST,
            linestyle="none",
            markerfacecolor=RUST if pair["status"] == "resolved" else "white",
        )
        beads.annotate(
            f"{_text_number(value)}%",
            (w, value),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=RUST,
            fontsize=8.5,
        )
    fig.text(0.267, 0.095, "Wiener parameter w (log scale)", ha="center", fontsize=9.4, color=SLATE)
    fig.text(
        0.746,
        0.077,
        "Wiener parameter w (log scale) and measured peak spacing",
        ha="center",
        fontsize=9.4,
        color=SLATE,
    )
    guide = "Dashed line = 15% valley criterion   ·   Open circle = unresolved"
    if missing:
        guide += "   ·   × = fewer than two eligible maxima"
    fig.text(0.067, 0.042, guide, fontsize=8.6, color=SLATE)
    fig.text(
        0.067,
        0.023,
        "Dotted vertical line marks the 0.020 reference. One simulated noise draw per specimen.",
        fontsize=8.6,
        color=SLATE,
    )


def _caption(pairs):
    states = ", ".join(
        f"{label} ({pair['separation_um']:.3f} µm)"
        if pair["status"] == "resolved"
        else f"{label} (unresolved)"
        for label, pair in zip(WIENER_LABELS, pairs, strict=True)
    )
    missing_note = (
        "A missing valley drop has no percentage and is marked ×. "
        if any(pair["valley_dip_fraction"] is None for pair in pairs)
        else ""
    )
    return (
        "**Wiener sweep on the noisy finite-bead and corrected-cell simulations.** "
        "A–E show fluorescence truth, the mean of the same 15 exposures, and three "
        "registered reconstructions at z = −0.750 µm. F–I subtract the matched truth "
        "from the mean and each reconstruction. Both color scales are signed, centered at zero "
        "and use inverse hyperbolic sine mapping. Badges count clipped samples in the "
        "displayed crop. SU denotes simulation source units. "
        "J shows the root-mean-square (RMS) error relative to truth within the conditioned "
        "cell low band. K shows the baseline-subtracted valley drop as a fraction of the weaker "
        "peak for bead pair P14. Both horizontal axes show the public Wiener parameter w, "
        "with adjacent values separated by a factor of √10. The filter adds w² to the denominator, "
        "so this contribution increases tenfold at each step. "
        "The 15% drop criterion is one part of the frozen pair rule. "
        "The rule also requires two eligible maxima of at least 0.005 SU, at least 0.10 µm apart, "
        f"in ordered truth neighborhoods. P14 at each Wiener value was {states}. "
        f"{missing_note}"
        "The dotted vertical line marks the 0.020 reference. "
        "Each specimen has one noisy realization.\n"
    )


def main(argv=None):
    """Render measured rows and write the figure and its evidence sidecar."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metrics", type=Path, required=True, help="Measured JSON aggregate at the exact log grid"
    )
    parser.add_argument(
        "--cell-truth", type=Path, required=True, help="Pinned corrected-cell truth NPY"
    )
    parser.add_argument(
        "--cell-conventional", type=Path, required=True, help="Pinned same-exposure mean NPY"
    )
    parser.add_argument(
        "--cell-observations",
        type=Path,
        required=True,
        nargs=3,
        metavar=("W_0.002", "W_0.020", "W_0.200"),
        help="Signed-count observation NPZs in the registered order",
    )
    parser.add_argument("--output-dir", type=Path, required=True, help="Fresh directory to create")
    args = parser.parse_args(argv)
    if args.output_dir.exists():
        parser.error("Output directory must be fresh")
    try:
        rows = _read_rows(args.metrics)
        errors, pairs = _read_series(rows)
        images, intensity, residual, receipts = _read_inputs(args, rows)
        fig = plt.figure(figsize=(12, 9.3))
        fig.text(
            0.067,
            0.966,
            "Wiener sweep on two synthetic specimens",
            fontsize=19,
            weight="bold",
            va="top",
        )
        fig.text(
            0.067,
            0.931,
            "Corrected cell interior at z = −0.750 µm  •  "
            "Same raw exposures and fitted factors across each sweep",
            color=SLATE,
            fontsize=10.4,
            va="top",
        )
        display = _image_bands(fig, images, intensity, residual, rows)
        _metric_panels(fig, errors, pairs)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))

    args.output_dir.mkdir()
    png = args.output_dir / "wiener.png"
    pdf = args.output_dir / "wiener.pdf"
    caption_path = args.output_dir / "wiener-caption.md"
    fig.savefig(png, dpi=170)
    fig.savefig(pdf, dpi=170, metadata={"CreationDate": None})
    plt.close(fig)
    caption_path.write_text(_caption(pairs), encoding="utf-8")
    sidecar = {
        "inputs": receipts,
        "renderer": _input_receipt(Path(__file__)),
        "outputs": {path.name: _file_digest(path) for path in (png, pdf, caption_path)},
        "reconstruction_gain_su_per_count": GAIN_SU_PER_COUNT,
        "display": display,
        "wieners": WIENERS,
        "panel_wieners": PANEL_WIENERS,
        "reference_wiener": REFERENCE_WIENER,
        "cell_low_band_relative_rms_error": errors,
        "p14": pairs,
        "plot_versions": {"matplotlib": matplotlib.__version__, "numpy": np.__version__},
    }
    (args.output_dir / "wiener.json").write_text(
        json.dumps(sidecar, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
