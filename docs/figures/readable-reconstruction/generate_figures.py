"""Reproduce conceptual walkthrough SVGs; never runs reconstruction.

Run from any directory with NumPy and Matplotlib installed. Optional PNGs are
reading-size render proofs, not measured microscopy or product output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

BLUE = "#246b9e"
ORANGE = "#b8571a"
GREEN = "#277a59"
INK = "#253447"
COLORS = [INK, BLUE, ORANGE]
HERE = Path(__file__).resolve().parent

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#8c98a5",
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "svg.fonttype": "none",
        "svg.hashsalt": "simrecon-conceptual-walkthrough-v2",
        "savefig.facecolor": "white",
    }
)


def save(fig, name, title, description, preview_dir):
    """Keep text selectable and add an accessible name/description to each SVG."""
    path = HERE / f"{name}.svg"
    fig.savefig(
        path,
        metadata={"Title": title, "Description": description, "Date": None},
    )
    svg = path.read_text()
    svg_start = svg.index("<svg ")
    svg_end = svg.index(">", svg_start)
    svg = (
        svg[:svg_end]
        + ' role="img" aria-labelledby="figure-title figure-description"'
        + svg[svg_end:]
    )
    svg = svg.replace("<title>", '<title id="figure-title">', 1)
    svg = svg.replace(
        "</title>",
        f'</title>\n <desc id="figure-description">{description}</desc>',
        1,
    )
    path.write_text("\n".join(line.rstrip() for line in svg.splitlines()) + "\n")
    if preview_dir is not None:
        preview_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview_dir / f"{name}.png", dpi=100)
    plt.close(fig)


def pipeline(preview_dir):
    """Draw stage dependencies and the explicit transfer branch."""
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.02)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    ax.set_title("One declared channel → signed image", loc="left", pad=14)

    def box(x, y, w, h, text, color=BLUE):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.012",
                linewidth=1.3,
                edgecolor=color,
                facecolor=color + "0d",
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=12)

    def arrow(start, end, **kwargs):
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops={"arrowstyle": "->", "color": INK, "lw": 1.4, **kwargs},
        )

    box(0.04, 0.84, 0.49, 0.11, "Declared specimen exposures\nT × D × P × Z × Y × X", INK)
    box(
        0.04,
        0.62,
        0.49,
        0.14,
        "1  Prepare acquisition bands\ncorrect → edges/equalize → Fourier\nphase "
        "separation → axial Fourier (3D)",
    )
    box(
        0.04, 0.37, 0.49, 0.14, "2  Estimate parameters\ncarrier vectors k and complex modulation a"
    )
    box(
        0.04,
        0.12,
        0.49,
        0.14,
        "3  Reconstruct each time\nnative filtering → Fourier embedding\ninverse sum "
        "+ positive carrier ramp",
    )
    box(0.64, 0.64, 0.32, 0.12, "Explicit complex OTF H\nor separate bead calibration", GREEN)
    box(
        0.64,
        0.12,
        0.32,
        0.14,
        "Known parameters?\nCall reconstruct_known\nto bypass estimation",
        ORANGE,
    )
    arrow((0.285, 0.84), (0.285, 0.76))
    arrow((0.285, 0.62), (0.285, 0.51))
    ax.text(0.30, 0.565, "complex native bands", va="center", fontsize=11)
    arrow((0.285, 0.37), (0.285, 0.26))
    ax.text(0.30, 0.315, "per-time k and a", va="center", fontsize=11)
    arrow((0.64, 0.67), (0.53, 0.46))
    ax.plot([0.68, 0.60, 0.60], [0.64, 0.58, 0.23], color=INK, lw=1.4)
    arrow((0.60, 0.23), (0.53, 0.23))
    arrow((0.64, 0.19), (0.53, 0.19), linestyle="dashed", color=ORANGE)
    ax.plot([0.04, 0.015, 0.015], [0.65, 0.65, 0.19], color=BLUE, lw=1.2)
    arrow((0.015, 0.19), (0.04, 0.19), color=BLUE)
    ax.text(0.285, 0.055, "Signed real output: T × Zout × Yout × Xout", ha="center", fontsize=12)
    save(
        fig,
        "pipeline-overview",
        "Conceptual reconstruction data flow",
        "Arrows show data dependencies, not timing. The workflow resolves the "
        "transfer before preparing specimen bands. Known parameters bypass "
        "estimation. T time, D direction, P phase, Z axial, Y and X lateral samples.",
        preview_dir,
    )


def phase(preview_dir):
    """Plot one analytical phase vector, its separator and retained slots."""
    phases = 2 * np.pi * np.arange(5) / 5
    data = 3 + np.cos(phases) + 0.5 * np.sin(phases)
    rows = np.array([np.ones(5), np.cos(phases), np.sin(phases)])
    values = rows @ data
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.7), gridspec_kw={"width_ratios": [1, 1.25, 0.9]})
    fig.subplots_adjust(left=0.07, right=0.98, top=0.78, bottom=0.20, wspace=0.50)
    fig.suptitle(
        "At one ordinary frequency sample: combine phases, retain three slots", fontsize=13, y=0.96
    )
    ax = axes[0]
    ax.plot(phases, data, "o-", color=INK, lw=1.7)
    ax.set(
        xlabel="Phase φ (rad)",
        ylabel="Input d (a.u.)",
        ylim=(0, 5),
        xticks=[0, np.pi, 2 * np.pi],
        xticklabels=["0", "π", "2π"],
    )
    ax.set_title("Five observations", loc="left")
    ax = axes[1]
    ax.imshow(rows, cmap="RdBu", vmin=-1, vmax=1, aspect="auto")
    for q in range(3):
        for p in range(5):
            ax.text(
                p,
                q,
                f"{rows[q, p]:.2g}",
                ha="center",
                va="center",
                fontsize=10,
                color="white" if abs(rows[q, p]) > 0.65 else INK,
            )
    ax.set(
        xticks=range(5), xlabel="Exposure index p", yticks=range(3), yticklabels=["B₀", "E₁", "O₁"]
    )
    ax.set_title("Multiply by L, then sum", loc="left")
    ax.text(
        0.5,
        -0.31,
        "Blue +1     white 0     red −1",
        transform=ax.transAxes,
        ha="center",
        fontsize=10,
    )
    ax = axes[2]
    ax.bar(range(3), values, color=COLORS, width=0.65)
    for i, value in enumerate(values):
        ax.text(i, value + 0.45, f"{value:g}", ha="center", fontsize=12)
    ax.set(xticks=range(3), xticklabels=["B₀", "E₁", "O₁"], ylabel="Output q (a.u.)", ylim=(0, 18))
    ax.set_title("q = Ld; no 1/P", loc="left")
    save(
        fig,
        "phase-separation",
        "Conceptual unnormalized phase separation",
        "Analytical toy only: P=5, M=2, phi=2pi*p/5, d=3+cos(phi)+0.5sin(phi). Rows "
        "1, cos(phi), sin(phi) produce B0=15, E1=2.5, O1=1.25. a.u. means arbitrary "
        "units. This real-valued toy is not pipeline output; actual quadratures are "
        "complex. The stored x-Nyquist column is excluded.",
        preview_dir,
    )


def relocation(preview_dir):
    """Compare illustrative native and object-coordinate envelopes."""
    # Every breakpoint of the piecewise-linear envelopes; no dense raster needed.
    k = np.array(sorted({-3, 3, *[n * 1.2 + edge for n in (-1, 0, 1) for edge in (-1, 0, 1)]}))

    def profile(q):
        return np.maximum(1 - np.abs(q), 0)

    fig, axes = plt.subplots(2, 1, figsize=(9, 5.1), sharex=True)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.85, bottom=0.23, hspace=0.85)
    fig.suptitle("Separation and relocation answer different questions", fontsize=14, y=0.97)
    for ax in axes:
        ax.set(ylim=(0, 1.18), yticks=[0, 1], ylabel="Toy profile\n(dimensionless)", xlim=(-3, 3))
        ax.axvline(0, color="#adb5bf", lw=0.8)
    axes[0].fill_between(k, profile(k), color=BLUE, alpha=0.20)
    axes[0].plot(k, profile(k), color=BLUE, lw=2)
    axes[0].set_title("Native coordinates: all order envelopes are drawn around k = 0", loc="left")
    axes[0].set_xlabel("Native lateral frequency k (cycles/µm)")
    axes[0].tick_params(labelbottom=True)
    for n, color, style in [(-1, ORANGE, "--"), (0, INK, "-"), (1, BLUE, "-.")]:
        axes[1].plot(
            k, profile(k - n * 1.2), color=color, ls=style, lw=2, label=f"signed order n = {n:+d}"
        )
        axes[1].fill_between(k, profile(k - n * 1.2), color=color, alpha=0.10)
    axes[1].set_title(
        "Object coordinates: K = k + n k₀, with illustrative k₀ = 1.2 cycles/µm", loc="left"
    )
    axes[1].set_xlabel("Object lateral frequency K (cycles/µm)")
    axes[1].legend(
        loc="upper center", bbox_to_anchor=(0.5, -0.63), ncol=3, frameon=False, fontsize=10
    )
    save(
        fig,
        "band-relocation",
        "Conceptual native and relocated frequency support",
        "Toy envelopes max(1-abs(k)/R,0), R=1 cycle per micrometre, carrier=1.2 "
        "cycles per micrometre. Native envelopes coincide; signed object-coordinate "
        "envelopes are centered at -1.2, 0, +1.2. These are illustrative profiles, "
        "not measured OTFs, transfer phases, amplitudes, or recovery evidence.",
        preview_dir,
    )


def overlap(preview_dir):
    """Show other-order sampling coordinates for one fixed object frequency."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 5.1), sharex=True)
    fig.subplots_adjust(left=0.16, right=0.96, top=0.85, bottom=0.20, hspace=1.05)
    fig.suptitle("One object frequency, different native samples", y=0.97, fontsize=14)
    k0, target, radius = 1.2, 0.6, 1.0
    for ax, n, color in zip(axes, [0, 1, -1], [INK, BLUE, ORANGE], strict=True):
        native = target - n * k0
        ax.axvspan(-radius, radius, color=GREEN, alpha=0.11)
        ax.axvline(-radius, color=GREEN, lw=1)
        ax.axvline(radius, color=GREEN, lw=1)
        ax.axhline(0, color="#adb5bf", lw=1)
        ax.plot(native, 0, "o" if abs(native) < radius else "x", color=color, ms=9, mew=2)
        ax.set(ylim=(-0.5, 0.5), yticks=[], xlim=(-2.1, 2.1))
        ax.spines["left"].set_visible(False)
        ax.text(
            -0.04, 0.5, f"n = {n:+d}", ha="right", va="center", transform=ax.transAxes, color=color
        )
        eligibility = (
            "inside: power eligible" if abs(native) < radius else "outside: no overlap power"
        )
        ax.set_title(
            f"q = K − n k₀ = {native:+.1f} cycles/µm   ·   {eligibility}", loc="left", fontsize=12
        )
    axes[-1].set_xlabel("Native lateral coordinate q (cycles/µm)")
    fig.text(
        0.16,
        0.025,
        "Green: |q| < R = 1 cycle/µm     • eligible sample     × outside support",
        fontsize=11,
    )
    save(
        fig,
        "native-overlap",
        "Conceptual overlap denominator coordinates",
        "One-dimensional slice at axial bin zero. Set object frequency K=0.6, carrier"
        " k0=1.2, R=1, all in cycles per micrometre. Other signed orders n=0,+1,-1 "
        "sample q=0.6,-0.6,1.8 respectively; only the first two are radially "
        "eligible. This illustrates other-order eligibility, not the self term, "
        "actual transfer values, or exact boundary behavior.",
        preview_dir,
    )


def assembly(preview_dir):
    """Plot an imposed analytical signed sum with a positive carrier ramp."""
    x = np.linspace(-1, 1, 1001)
    u0 = np.full_like(x, 0.4)
    u1 = 0.3 * np.exp(2j * np.pi * 0.5 * x)
    ramped = 2 * (u1 * np.exp(2j * np.pi * 0.75 * x)).real
    total = u0 + ramped
    fig, axes = plt.subplots(2, 1, figsize=(9, 4.7), sharex=True)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.85, bottom=0.14, hspace=0.6)
    fig.suptitle("Positive carrier ramp + real-part assembly retains the sign", y=0.97, fontsize=14)
    axes[0].plot(x, u0, color=INK, lw=2, label="center Re(u₀) = 0.4")
    axes[0].plot(x, ramped, color=BLUE, lw=2, label="side 2 Re[u₁ exp(+2πik₀x)]")
    axes[0].set(ylim=(-0.8, 1.25), ylabel="Contribution (a.u.)")
    axes[0].legend(loc="upper right", frameon=False, fontsize=10, facecolor="white", framealpha=1)
    axes[0].set_title("Side partner is supplied by 2 Re{…}", loc="left")
    axes[1].plot(x, total, color=GREEN, lw=2.2)
    axes[1].fill_between(x, total, 0, where=total < 0, color=ORANGE, alpha=0.25)
    axes[1].set(
        xlabel="Centered lateral coordinate x (µm)", ylabel="Signed sum I (a.u.)", ylim=(-0.4, 1.2)
    )
    axes[1].set_title("I = 0.4 + 0.6 cos[2π(1.25 cycles/µm)x]", loc="left")
    axes[1].annotate(
        "negative values retained",
        xy=(-0.4, -0.2),
        xytext=(-0.89, 0.48),
        arrowprops={"arrowstyle": "->", "color": ORANGE},
        color=ORANGE,
        fontsize=11,
    )
    for ax in axes:
        ax.axhline(0, color="#adb5bf", lw=0.8, zorder=0)
        ax.set_xlim(-1, 1)
    save(
        fig,
        "signed-assembly",
        "Analytical signed carrier assembly illustration",
        "Continuous analytical functions imposed for illustration: u0=0.4, "
        "u1=0.3exp(2pi*i*0.5*x), carrier k0=0.75 cycles per micrometre, x in "
        "micrometres. The signed sum is 0.4+0.6cos(2pi*1.25*x), spanning -0.2 to 1 "
        "arbitrary unit. These functions are not computed from a prepared dataset or "
        "a finite inverse transform; no physical positivity or recovery claim "
        "follows.",
        preview_dir,
    )


def main():
    """Write the conceptual SVGs and optional normal-width PNG proofs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preview-dir", type=Path, help="also write 900-pixel-wide PNG render proofs"
    )
    args = parser.parse_args()
    for render in [pipeline, phase, relocation, overlap, assembly]:
        render(args.preview_dir)


if __name__ == "__main__":
    main()
