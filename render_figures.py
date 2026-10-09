"""Render presentation-only PR16 figures from the fixed reviewed comparison data."""
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(HERE / ".mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

DATA = json.loads((HERE / "data/comparison-data.json").read_text())
INPUTS = np.load(HERE / "data/volume-comparison-inputs.npz", allow_pickle=False)
OUTPUTS = np.load(HERE / "data/volume-comparison-outputs.npz", allow_pickle=False)
NAMES = list(DATA["cases"])
LABELS = ["On-model", "Off-model", "Huge phases", "Mixed scales"]
COLORS = ["#2475a8", "#7e57a1", "#148773", "#d07820"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for filename, digest in DATA["source_npz_sha256"].items():
    assert sha(HERE / "data" / filename) == digest
for archive, label in [(INPUTS, "inputs"), (OUTPUTS, "outputs")]:
    assert set(archive.files) == set(DATA[label])
    for name, descriptor in DATA[label].items():
        array = archive[name]
        assert array.dtype.str == descriptor["dtype"]
        assert list(array.shape) == descriptor["shape"]
        assert hashlib.sha256(array.tobytes(order="C")).hexdigest() == descriptor["c_order_bytes_sha256"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.titlesize": 12, "axes.labelsize": 11,
                     "figure.facecolor": "white", "savefig.facecolor": "white",
                     "axes.spines.top": False, "axes.spines.right": False})
metrics = {}
with localcontext() as context:
    context.prec = 120
    for name in NAMES:
        case = DATA["cases"][name]
        actual = OUTPUTS[name + "_actual_coordinates"].reshape(5, -1).T
        errors = [max(abs(Decimal.from_float(float(v)) - Decimal(t))
                      for v, t in zip(row, reference, strict=True))
                  for row, reference in zip(actual, case["expected_decimal_voxel_rows"], strict=True)]
        budgets = [Decimal(x) for x in case["local_budgets_decimal"]]
        ratios = [error / budget for error, budget in zip(errors, budgets, strict=True)]
        assert max(ratios) == Decimal(case["max_error_over_local_budget"])
        assert max(errors) == max(Decimal(x) for x in case["max_coordinate_error"])
        metrics[name] = {"maximum_coordinate_errors_decimal": [str(x) for x in errors],
                         "local_budgets_decimal": [str(x) for x in budgets],
                         "error_over_local_budget_decimal": [str(x) for x in ratios]}

# Signed real-coordinate maps, with one common color range per component across z.
coordinates = OUTPUTS["on_model_actual_coordinates"]
titles = ["DC", "Re(c₁)", "Im(c₁)", "Re(c₂)", "Im(c₂)"]
fig, axes = plt.subplots(2, 5, figsize=(13.5, 6.2), constrained_layout=True)
fig.suptitle("Recovered phase harmonics of an observed volume\n"
             "Synthetic on-model data · 8 unequal known phases · two sampled z planes", fontsize=15)
for j, title in enumerate(titles):
    vmin, vmax = float(coordinates[j].min()), float(coordinates[j].max())
    for z in range(2):
        ax = axes[z, j]
        image = ax.imshow(coordinates[j, z], origin="lower", interpolation="nearest",
                          cmap="viridis", vmin=vmin, vmax=vmax, aspect="equal")
        if z == 0:
            ax.set_title(title, weight="bold")
        ax.set_xticks(range(4)); ax.set_yticks(range(3))
        ax.set_xlabel("x voxel index")
        if j == 0:
            ax.set_ylabel(f"z index {z}\ny voxel index")
        for y, x in np.ndindex(3, 4):
            value = float(coordinates[j, z, y, x])
            ax.text(x, y, f"{value:.2f}", ha="center", va="center", fontsize=10,
                    color="white" if (value-vmin)/(vmax-vmin) < .48 else "#142532")
    bar = fig.colorbar(image, ax=axes[:, j], orientation="horizontal", fraction=.055, pad=.05)
    bar.set_label("Intensity units", fontsize=10)
fig.get_layout_engine().set(rect=(0, .07, 1, .93))
fig.text(.5, .025, "Color limits are shared across z within each column. Values are signed real coordinates.\n"
         "These are observed-volume phase harmonics; no physical 3D specimen reconstruction is shown.",
         ha="center", fontsize=10)
fig.savefig(HERE / "volume-components.png", dpi=180)
plt.close(fig)

# Divide in Decimal before converting ratios. Compute logarithms in Decimal too.
fig, axes = plt.subplots(1, 2, figsize=(13.7, 6.7), gridspec_kw={"width_ratios": [1, 1.25]})
fig.subplots_adjust(left=.07, right=.97, bottom=.25, top=.78, wspace=.65)
fig.suptitle("Numerical error against each voxel's own budget", fontsize=17, y=.985)
fig.text(.5, .87, "Each dot summarizes the maximum error across the five returned real coordinates.\n"
         "Reference values and budgets use the reviewed 120-digit Decimal observer.", ha="center", fontsize=11)
ax = axes[0]
floor = 1e-7
for j, name in enumerate(NAMES):
    ratios = np.array([float(Decimal(x)) for x in metrics[name]["error_over_local_budget_decimal"]])
    nonzero = ratios > 0
    assert np.all(ratios[nonzero] > floor)
    offsets = np.linspace(-.2, .2, len(ratios))
    ax.scatter(j + offsets[nonzero], ratios[nonzero], s=27, color=COLORS[j], alpha=.8)
    ax.scatter(j + offsets[~nonzero], np.full(sum(~nonzero), floor), s=45,
               facecolors="white", edgecolors=COLORS[j], linewidths=1.5)
    ax.text(j, max(ratios)*1.9, f"{max(ratios):.3g}", ha="center", color=COLORS[j], weight="bold")
ax.axhline(1, color="#b53035", linestyle="--", linewidth=1.5)
ax.text(-.35, 1.25, "Allowed maximum = 1", color="#b53035")
ax.set_yscale("log"); ax.set_ylim(floor*.6, 3); ax.set_xlim(-.45, 3.45)
ax.set_xticks(range(4), [f"{label}\n{len(metrics[name]['local_budgets_decimal'])} voxels"
                           for name, label in zip(NAMES, LABELS, strict=True)], fontsize=10)
ax.set_ylabel("Maximum coordinate error / local budget")
ax.set_title("All 80 voxels meet their local budget", pad=18)
ax.grid(axis="y", alpha=.2)
ax.annotate("Exact zero\n(open marker at display floor)", xy=(3.03, floor), xytext=(1.15, 4e-7),
            arrowprops={"arrowstyle": "->", "color": "#55616b"}, fontsize=9)

ax = axes[1]
case = metrics["mixed_scales"]
with localcontext() as context:
    context.prec = 120
    error_values = [Decimal(x) for x in case["maximum_coordinate_errors_decimal"]]
    budget_values = [Decimal(x) for x in case["local_budgets_decimal"]]
    error_logs = [float(x.log10()) if x else -340 for x in error_values]
    budget_logs = [float(x.log10()) for x in budget_values]
rows = np.arange(8)
for row, error, budget in zip(rows, error_logs, budget_logs, strict=True):
    ax.plot([error, budget], [row, row], color="#bcc6cc", linewidth=1)
ax.scatter(error_logs, rows, label="Maximum coordinate error", color="#2475a8", s=40, zorder=3)
ax.scatter(budget_logs, rows, label="Local budget", color="#d07820", marker="s", s=32, zorder=3)
ax.text(-285, 4, "exact 0", va="center", fontsize=9, color="#2475a8")
scale_labels = ["1e−200", "1", "float64 max / 64", "2⁻¹⁰⁷⁴", "0", "2⁻¹⁰²²", "1e100", "1e−100"]
ax.set_yticks(rows, [f"{index}  |  {scale}" for index, scale in zip(np.ndindex(2, 2, 2), scale_labels, strict=True)], fontsize=9)
ax.set_ylim(7.6, -.6); ax.set_xlim(-350, 320)
ax.set_xticks([-320, -200, -100, 0, 100, 200, 300])
ax.set_xlabel("log₁₀(value in intensity units)")
ax.set_ylabel("(z, y, x) voxel  |  input scale", labelpad=10)
ax.set_title("Mixed-scale volume: absolute error and budget", pad=18)
ax.grid(axis="x", alpha=.2)
ax.legend(loc="upper right", fontsize=9, frameon=True, facecolor="white", framealpha=.95)
fig.text(.5, .055, "The bright voxel has error 1.78e292 but uses only 1.95e−5 of its local budget.\n"
         "The subnormal voxel has error 1.08e−324 and the largest budget fraction, 0.0274.\n"
         "Zero error is marked explicitly; its marker at the left edge is not log₁₀(0).", ha="center", fontsize=10)
fig.savefig(HERE / "volume-local-error.png", dpi=180)
plt.close(fig)

# Saved sample values only. Lines join stored samples; no new model curve is generated.
fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.7), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
fig.subplots_adjust(left=.09, right=.97, top=.80, bottom=.18, hspace=.18, wspace=.28)
fig.suptitle("Off-model data: projection residual is distinct from solver error", fontsize=15, y=.985)
fig.text(.5, .875, "Eight unequal known phases. Lines join saved exposure samples.\n"
         "Independent and returned fitted predictions coincide at this display scale.", ha="center", fontsize=11)
exposures = np.arange(8)
for column, index in enumerate([(0, 0, 0), (1, 2, 3)]):
    select = (slice(None),) + index
    observed = INPUTS["off_model_images"][select]
    returned = OUTPUTS["off_model_actual_fit"][select]
    independent = OUTPUTS["off_model_expected_fit"][select]
    ax = axes[0, column]
    ax.plot(exposures, observed, "o", color="#172e3d", label="Observed data", markersize=5)
    ax.plot(exposures, returned, "-", color="#2475a8", label="Returned SVD fit", linewidth=2)
    ax.plot(exposures, independent, "D", markerfacecolor="none", markeredgecolor="#d07820",
            label="Independent fit", markersize=6)
    ax.set_title(f"Voxel {index}", weight="bold")
    ax.set_ylabel("Observed / fitted intensity")
    ax.grid(alpha=.15)
    residual = OUTPUTS["off_model_actual_residual"][select]
    axes[1, column].bar(exposures, residual, color="#2475a8", width=.55)
    axes[1, column].axhline(0, color="#687985", linewidth=.8)
    axes[1, column].set_xlabel("Exposure index (zero-based)")
    axes[1, column].set_ylabel("Data − returned fit\n(intensity units)")
    axes[1, column].set_xticks(exposures)
    axes[1, column].grid(axis="y", alpha=.15)
axes[0, 0].legend(loc="best", fontsize=9, frameon=False)
fig.text(.5, .055, "Maximum independent projection residual across the full volume: 2.9605 intensity units.\n"
         "Maximum returned-fit minus independent-fit error: 1.18e−14 intensity units.\n"
         "Residual bars show off-model mismatch, not numerical solver error.", ha="center", fontsize=10)
fig.savefig(HERE / "volume-off-model-projection.png", dpi=180)
plt.close(fig)

(HERE / "figure-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
files = ["volume-components.png", "volume-local-error.png", "volume-off-model-projection.png",
         "figure-metrics.json", "render_figures.py", "data/comparison-data.json",
         "data/volume-comparison-inputs.npz", "data/volume-comparison-outputs.npz"]
manifest = {"candidate": DATA["candidate"], "source_json_sha256": DATA["source_json_sha256"],
            "environment": {"python": platform.python_version(), "numpy": np.__version__,
                            "matplotlib": matplotlib.__version__},
            "transformations": ["Signed actual coordinate maps at both z indices; shared limits per component",
                                "Maximum of five Decimal coordinate differences per voxel divided by its stored Decimal budget before float conversion",
                                "Decimal logarithms for mixed-scale absolute errors and budgets; explicitly marked exact zero",
                                "Saved off-model observations, predictions and residual samples only"],
            "files": {name: {"sha256": sha(HERE / name), "bytes": (HERE / name).stat().st_size} for name in files}}
(HERE / "figure-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"status": "passed", "max_ratios": {name: max(map(Decimal, item["error_over_local_budget_decimal"])).to_eng_string()
                                                     for name, item in metrics.items()},
                  "pngs": {name: manifest["files"][name] for name in files if name.endswith(".png")}}, indent=2))
