"""Render actual profile/control observations; no new statistic or numerical experiment."""

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
points = HERE / "largest256-profile-control-points.csv"
provenance = json.loads((HERE / "figure-input-provenance.json").read_text())
assert hashlib.sha256(points.read_bytes()).hexdigest() == provenance["csv_sha256"]
with points.open(newline="") as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == 12

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey="row")
groups = [("no", "Unprofiled", "#3568A8", "o", -0.055),
          ("yes", "Profiled", "#C76A24", "s", 0.055)]
for column, mode in enumerate(("summary", "full")):
    for profiled, label, color, marker, offset in groups:
        selected = sorted(
            (row for row in rows if row["mode"] == mode and row["profiled"] == profiled),
            key=lambda row: int(row["repetition"]),
        )
        assert [int(row["repetition"]) for row in selected] == [1, 2, 3]
        x = [int(row["repetition"]) + offset for row in selected]
        axes[0, column].scatter(
            x, [int(row["terminal_kernel_bytes"]) / 1048576 for row in selected],
            label=label, color=color, marker=marker, s=60, zorder=3,
        )
        axes[1, column].scatter(
            x, [float(row["call_seconds"]) for row in selected],
            color=color, marker=marker, s=60, zorder=3,
        )
    axes[0, column].set_title("Summary" if mode == "summary" else "Full diagnostics")
    axes[1, column].set_xlabel("Repetition (separate fresh process)")
    for axis in axes[:, column]:
        axis.set_xticks([1, 2, 3])
        axis.set_xlim(0.65, 3.35)
        axis.set_ylim(bottom=0)
        axis.grid(axis="y", color="#e1e5e9", linewidth=0.8)
axes[0, 0].set_ylabel("Terminal process high-water (MiB)")
axes[1, 0].set_ylabel("Workflow call duration (s)")
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.suptitle("Largest completed searched workload: T1 / D3 / 8 × 256 × 256", y=0.99)
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.945),
           ncol=2, frameon=False)
fig.text(
    0.03, 0.025,
    "Three fresh processes per group; physical/cache context is uncontrolled.\n"
    "Points show process high-water and call time, not isolated allocation or causal profiling cost.",
    fontsize=9,
)
fig.tight_layout(rect=(0.01, 0.09, 0.99, 0.88))
for suffix in ("png", "svg"):
    fig.savefig(HERE / ("largest256-profile-controls." + suffix), dpi=180, facecolor="white")
plt.close(fig)
print(json.dumps({"matplotlib": matplotlib.__version__, "rows": len(rows),
                  "source_csv_sha256": provenance["csv_sha256"],
                  "scope": "Presentation only; no aggregation or reconstruction"}))

