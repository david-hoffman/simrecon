"""Render frozen RA02 arrays; no reconstruction or oracle evaluation.

Use an isolated matplotlib3.10.7/numpy2.5.3 environment. Input arrays were
exported separately with the locked project environment and reviewed fixture.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.colors import TwoSlopeNorm


def plane(values, axis, coordinate, spacing):
    """Select the nearest declared-coordinate sample, first on ties."""
    centers = np.arange(values.shape[axis]) * spacing[axis]
    # argmin chooses the first index on a represented equal-distance tie.
    index = int(np.argmin(np.abs(centers - coordinate)))
    return np.take(values, index, axis=axis), index, float(centers[index])


def extent(shape, spacing, vertical):
    """Return half-sample display edges in physical micrometres."""
    h, w = shape
    return [
        -spacing[2] / 2,
        (w - 0.5) * spacing[2],
        -spacing[vertical] / 2,
        (h - 0.5) * spacing[vertical],
    ]


def main():
    """Render the frozen numerical arrays without running the inverse."""
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arrays", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    a = np.load(args.arrays, allow_pickle=False)
    raw = a["images"][0, 0]
    expected, actual = a["expected_volume"], a["actual_volume"]
    native_spacing = a["input_spacing_um"]
    spacing = native_spacing * np.array(raw.shape) / np.array(actual.shape)
    center = a["transfer_origin_zyx"] * native_spacing
    # The coordinate is declared by the input transfer origin before outputs.
    # This algebraic control has no bead catalogue or fitted point center.
    arrays = [raw.real, expected.real, actual.real]
    spacings = [native_spacing, spacing, spacing]
    projections = []
    selected = []
    for value, step in zip(arrays, spacings, strict=True):
        xy, zi, zc = plane(value, 0, center[0], step)
        xz, yi, yc = plane(value, 1, center[1], step)
        projections.append([value.max(axis=0), value.max(axis=1), xy, xz])
        selected.append((zi, zc, yi, yc))
    limit = max(float(np.max(np.abs(x))) for value in projections for x in value)
    norm = TwoSlopeNorm(vcenter=0, vmin=-limit, vmax=limit)
    differences = [projections[2][i] - projections[1][i] for i in range(4)]
    diff_limit = max(float(np.max(np.abs(x))) for x in differences)
    diff_limit = max(diff_limit, np.finfo(float).tiny)
    diff_norm = TwoSlopeNorm(vcenter=0, vmin=-diff_limit, vmax=diff_limit)
    fig, axes = plt.subplots(4, 4, figsize=(14, 8.5), constrained_layout=True)
    names = [
        "Raw: orientation 1, phase 1",
        "Independent estimator",
        "Public fusion",
        "Fusion minus expected",
    ]
    rows = [
        "XY maximum over z",
        "XZ maximum over y",
        "XY fixed-coordinate slice",
        "XZ fixed-coordinate slice",
    ]
    for row in range(4):
        vertical = 1 if row % 2 == 0 else 0
        for col in range(4):
            ax = axes[row, col]
            value = projections[col][row] if col < 3 else differences[row]
            step = spacings[col] if col < 3 else spacing
            ax.imshow(
                value,
                origin="lower",
                extent=extent(value.shape, step, vertical),
                cmap="RdBu_r",
                norm=norm if col < 3 else diff_norm,
                interpolation="nearest",
                aspect="equal",
            )
            ax.set_xlabel("x (µm)")
            ax.set_ylabel(
                (rows[row] + "\n" if col == 0 else "") + ("y" if vertical == 1 else "z") + " (µm)"
            )
            if row == 0:
                ax.set_title(names[col], fontsize=10)
    fig.colorbar(
        axes[0, 0].images[0],
        ax=axes[:, :3],
        shrink=0.65,
        label="Signed real intensity (arbitrary input units)",
    )
    fig.colorbar(
        axes[0, 3].images[0],
        ax=axes[:, 3],
        shrink=0.65,
        label="Signed difference (same units; separate arithmetic scale)",
    )
    zplanes = ", ".join(f"{s[1]:g}" for s in selected)
    yplanes = ", ".join(f"{s[3]:g}" for s in selected)
    fig.suptitle(
        "RA02: declared complex estimator on a tiny periodic control\n"
        f"Target coordinate z={center[0]:g}, y={center[1]:g} µm; "
        f"nearest planes z=[{zplanes}], y=[{yplanes}] µm",
        fontsize=12,
    )
    args.output.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output / "volume-comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    # Frequency placement is geometric and fixed before observing intensities.
    # Show the qz=0 plane for orientation 1; no selected peak/slice.
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
    ny, nx = raw.shape[1:]
    fy = np.arange(-(ny // 2), (ny + 1) // 2)
    fx = np.arange(-(nx // 2), (nx + 1) // 2)
    length = native_spacing * np.array(raw.shape)
    carrier = a["carriers_yx_bins"][0]
    colors = plt.cm.viridis(np.linspace(0.05, 0.95, 5))
    for i, m in enumerate(range(-2, 3)):
        xx, yy = np.meshgrid(fx - m * carrier[1], fy - m * carrier[0])
        axes[0].scatter(
            xx / length[2],
            yy / length[1],
            s=24,
            facecolors="none",
            edgecolors=[colors[i]],
            marker=["o", "s", "D", "^", "v"][i],
            label=f"m={m:+d}",
        )
    axes[0].set(
        xlabel="Object qx (cycles/µm)",
        ylabel="Object qy (cycles/µm)",
        title="Declared placement q = j − m × carrier",
    )
    axes[0].set_aspect("equal")
    axes[0].legend(
        fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.10), ncol=5, frameon=False
    )
    axes[0].set_title("Declared placement q = j − m × carrier", pad=38)
    axes[0].grid(alpha=0.2)
    zi = int(a["centered_dc_index"][0])
    expected_s, actual_s = a["expected_spectrum"][zi], a["actual_spectrum"][zi]
    spectral_limit = max(
        float(np.max(np.abs(expected_s.real))),
        float(np.max(np.abs(actual_s.real))),
        float(np.max(np.abs(expected_s.imag))),
        float(np.max(np.abs(actual_s.imag))),
    )
    snorm = TwoSlopeNorm(vcenter=0, vmin=-spectral_limit, vmax=spectral_limit)
    fyout, fxout = a["fy_per_um"], a["fx_per_um"]
    de_y = 1 / length[1]
    de_x = 1 / length[2]
    se = [fxout[0] - de_x / 2, fxout[-1] + de_x / 2, fyout[0] - de_y / 2, fyout[-1] + de_y / 2]
    for ax, value, title in zip(
        axes[1:],
        [actual_s.real, actual_s.imag],
        ["Actual output spectrum: real", "Actual output spectrum: imaginary"],
        strict=True,
    ):
        sim = ax.imshow(
            value,
            origin="lower",
            extent=se,
            cmap="RdBu_r",
            norm=snorm,
            aspect="equal",
            interpolation="nearest",
        )
        ax.set(xlabel="qx (cycles/µm)", ylabel="qy (cycles/µm)", title=title)
    fig.colorbar(
        sim, ax=axes[1:], shrink=0.75, label="Fourier-series amplitude (input intensity units)"
    )
    max_error = float(np.max(np.abs(a["signed_spectrum_difference"])))
    fig.suptitle(
        "Fixed axial frequency qz = 0 cycles/µm; "
        f"full-spectrum max |actual − expected| = {max_error:.3g}"
    )
    fig.savefig(args.output / "frequency-placement.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    print("Rendered frozen arrays; no product or independent oracle called.")


if __name__ == "__main__":
    main()
