"""Plot accepted tiny finite-model controls without changing their numerical values."""

import hashlib
import json
import sys
from importlib.metadata import distributions, version
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "tiny-controls.json").read_text())
CONTROL = DATA["controls"]
FOCUS = np.asarray(CONTROL["refinement"]["geometry"]["focus_centers_um"])
FIGURE, AXES = plt.subplots(1, 3, figsize=(14.2, 4.1), layout="constrained", sharey=True)


def values(record, name):
    """Read the serialized scalar detector stack in its unchanged order."""
    return np.asarray(record[name]["values"]).ravel()


def compare(axis, actual, expected, label, color):
    """Show application output as a line and independent finite target as crosses."""
    axis.plot(FOCUS, actual, color=color, label=label, linewidth=1.8)
    axis.plot(FOCUS, expected, color=color, marker="x", linestyle="none", markersize=7)


point = CONTROL["point_sign"]
compare(
    AXES[0],
    values(point, "actual"),
    values(point, "expected"),
    "Generator / physical target",
    "#c15b21",
)
compare(
    AXES[0],
    values(point, "inverse_actual"),
    values(point, "inverse_expected"),
    "Inverse / represented target",
    "#256c94",
)
AXES[0].set_title("Displaced point; unequal side beams")
for row, color in zip(
    CONTROL["refinement"]["source_rows"], ("#c15b21", "#256c94", "#628543"), strict=True
):
    compare(
        AXES[1],
        values(row, "actual"),
        values(row, "expected"),
        f"Source refinement {row['source_refinement']}",
        color,
    )
AXES[1].set_title("Same sphere; pixels=2, pupil Q=2")
for row, color in zip(
    CONTROL["refinement"]["pixel_rows"], ("#c15b21", "#256c94", "#628543"), strict=True
):
    compare(
        AXES[2],
        values(row, "actual"),
        values(row, "expected"),
        f"Pixel midpoint count {row['pixels']}",
        color,
    )
AXES[2].set_title("Same source refinement=2, pupil Q=2")
for axis in AXES:
    axis.set_xlabel("Focus z (µm); fixed source center z=0.75 µm")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
AXES[0].set_ylabel("Expected detector signal (electrons)")
FIGURE.suptitle(
    (
        "Tiny finite-model controls: lines are actual outputs; "
        "crosses are independent targets\n"
        "Source/pixel changes are discretization sensitivity, not resolution"
    ),
    fontsize=11,
)
FIGURE.savefig(ROOT / "tiny-control-comparisons.png", dpi=180)
plt.close(FIGURE)
metadata = {
    "python": sys.version,
    "actual_executable_during_render": sys.executable,
    "actual_prefix_during_render": sys.prefix,
    "numpy": version("numpy"),
    "matplotlib": version("matplotlib"),
    "distributions": sorted(
        [[d.metadata["Name"], d.version, str(d.locate_file(""))] for d in distributions()]
    ),
    "input_sha256": hashlib.sha256((ROOT / "tiny-controls.json").read_bytes()).hexdigest(),
    "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "figure_sha256": hashlib.sha256(
        (ROOT / "tiny-control-comparisons.png").read_bytes()
    ).hexdigest(),
    "limit": (
        "Observed in this render process; uv may remove temporary environment prefix "
        "normally after exit; no later executable-custody claim"
    ),
}
Path("artifacts/ra03/tiny-plot-environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(
    json.dumps(
        {"figure": str(ROOT / "tiny-control-comparisons.png"), "sha256": metadata["figure_sha256"]}
    )
)
