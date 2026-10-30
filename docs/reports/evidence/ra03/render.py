"""Render actual RA03 evaluator arrays without fitting display coordinates or scale."""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.metadata import distributions, version
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize, TwoSlopeNorm
from scripts.reference_alignment_ra03 import fixed_center_views

matplotlib.use("Agg")

RUN = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent
RECORD = json.loads((RUN / "run-record.json").read_text())
assert RECORD["status"] == "complete"
SPACING = tuple(RECORD["detector_spacing_um_zyx"])
ORIGIN = tuple(RECORD["detector_origin_um_zyx"])
CENTER = tuple(RECORD["fixed_center_um_zyx"])
PRODUCTS = ("xy_mip", "xz_mip", "xy_slice", "xz_slice")
ROW_LABELS = (
    "XY maximum projection",
    "XZ maximum projection",
    "XY fixed-center slice",
    "XZ fixed-center slice",
)
LABELS = {
    "paired_generator64_true": "Paired source64, generator",
    "paired_generator32_true": "Paired source32, generator",
    "paired_inverse_true": "Paired source, true illumination",
    "paired_inverse_estimated": "Paired source, estimated illumination",
    "paired_inverse_carrier_only": "Carrier substitution",
    "paired_inverse_phase_only": "Phase substitution",
    "paired_inverse_beam_only": "Beam substitution",
    "original_prediction": "Original fitted prediction",
    "original_fit_reapplied": "Frozen fit, reapplied",
}


def digest(path):
    """Hash a retained regular file for output provenance."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(name):
    """Load the predeclared orientation0 phase0 array without recentering."""
    return np.load(RUN / f"o0-{name}.npy", allow_pickle=False)[0]


def views(array, spacing=SPACING):
    """Use the tested deterministic nearest-plane display boundary."""
    return fixed_center_views(
        array, spacing_um_zyx=spacing, origin_um_zyx=ORIGIN, center_um_zyx=CENTER
    )


def extent(array, spacing, row):
    """Return physical cell-edge extents in micrometres."""
    z, y, x = array.shape
    return [
        ORIGIN[2],
        ORIGIN[2] + x * spacing[2],
        ORIGIN[1 if row % 2 == 0 else 0],
        ORIGIN[1 if row % 2 == 0 else 0] + (y * spacing[1] if row % 2 == 0 else z * spacing[0]),
    ]


def grid(arrays, titles, path, *, spacing=SPACING, differences=False):
    """Preserve four physical products and shared quantitative color scales."""
    all_views = [views(a, spacing) for a in arrays]
    if differences:
        reference_views = all_views[0]
        shown = [{k: v[k] - reference_views[k] for k in PRODUCTS} for v in all_views[1:]]
    else:
        shown = all_views
    columns = len(shown)
    maximum = max(float(np.max(np.abs(v[k]))) for v in shown for k in PRODUCTS)
    norm = (
        TwoSlopeNorm(vmin=-maximum, vcenter=0, vmax=maximum)
        if differences
        else Normalize(
            vmin=min(0.0, min(float(np.min(v[k])) for v in shown for k in PRODUCTS)),
            vmax=maximum,
        )
    )
    ratio = arrays[0].shape[0] * spacing[0] / (arrays[0].shape[1] * spacing[1])
    figure, axes = plt.subplots(
        4,
        columns,
        figsize=(4.2 * columns, 10.8),
        gridspec_kw={"height_ratios": [1, ratio, 1, ratio]},
        layout="constrained",
        squeeze=False,
    )
    for row, key in enumerate(PRODUCTS):
        for column in range(columns):
            axis = axes[row, column]
            image = axis.imshow(
                shown[column][key],
                origin="lower",
                interpolation="nearest",
                extent=extent(arrays[0], spacing, row),
                aspect="equal",
                cmap="RdBu_r" if differences else "magma",
                norm=norm,
            )
            axis.set_xlabel("x (µm)")
            axis.set_ylabel("y (µm)" if row % 2 == 0 else "z (µm)")
            if row == 0:
                axis.set_title(titles[column], fontsize=10)
            if column == 0:
                axis.text(
                    -0.28,
                    0.5,
                    ROW_LABELS[row],
                    rotation=90,
                    transform=axis.transAxes,
                    ha="right",
                    va="center",
                    fontsize=9,
                )
    figure.colorbar(
        image,
        ax=axes,
        label=("Shown-product difference" if differences else "Signal")
        + " (relative signal / detector pixel)",
        shrink=0.75,
    )
    selected = all_views[0]["coordinates_um_zyx"]
    figure.suptitle(
        (
            f"Frozen exposure o0p0; catalogue center {CENTER} µm\n"
            f"Nearest stored planes: z={selected[0]:.5g}, y={selected[1]:.5g} µm; "
            "shared quantitative scale"
        ),
        fontsize=12,
    )
    figure.savefig(OUT / path, dpi=170)
    plt.close(figure)
    return {
        "indices_zyx": list(all_views[0]["indices_zyx"]),
        "coordinates_um_zyx": list(selected),
        "maximum_color_scale": maximum,
        "minimum_color_scale": norm.vmin,
        "scale_units": "relative signal per detector pixel",
        "difference_definition": "difference of shown products" if differences else None,
    }


names = ["fine_reference", "paired_inverse_true", "paired_inverse_estimated", "original_prediction"]
arrays = [load(n) for n in names]
quantitative = grid(
    arrays,
    [
        "Archived fine-generator mean",
        "Paired source, true illumination",
        "Same source, estimated illumination",
        "Original fitted prediction",
    ],
    "forward-four-products.png",
)
difference = grid(
    arrays,
    [
        "Paired true − fine reference",
        "Paired estimated − fine reference",
        "Original fitted − fine reference",
    ],
    "signed-differences.png",
    differences=True,
)

figure, axes = plt.subplots(1, 2, figsize=(13, 3.7), layout="constrained")
z, y, _ = quantitative["indices_zyx"]
x = ORIGIN[2] + (np.arange(arrays[0].shape[2]) + 0.5) * SPACING[2]
for name, array in zip(names, arrays, strict=True):
    profile = array[z, y]
    label = "Archived fine-generator mean" if name == "fine_reference" else LABELS[name]
    axes[0].plot(x, profile, label=label, linewidth=1)
    axes[1].plot(x, profile / np.max(np.abs(profile)), label=label, linewidth=1)
axes[0].set_ylabel("Relative signal / detector pixel")
axes[1].set_ylabel("Shape only: each profile / its own peak")
for axis in axes:
    axis.set_xlabel("x (µm); fixed stored y/z plane")
    axis.grid(alpha=0.2)
axes[0].set_title("Absolute amplitude")
axes[1].set_title("Separately peak normalized; no amplitude evidence")
axes[0].legend(fontsize=8)
figure.savefig(OUT / "fixed-center-profiles.png", dpi=170)
plt.close(figure)

metrics = RECORD["metrics_all15"]
ordered = list(LABELS)
errors = (
    np.array([[row["relative_l2"] for row in metrics[name]["frames"]] for name in ordered]) * 100
)
aggregate = np.array([metrics[name]["aggregate"]["relative_l2"] for name in ordered]) * 100
figure, axes = plt.subplots(
    1, 2, figsize=(16, 5.4), gridspec_kw={"width_ratios": [2.6, 1]}, layout="constrained"
)
image = axes[0].imshow(
    errors,
    aspect="auto",
    cmap="magma",
    vmin=0,
    vmax=max(float(errors.max()), float(aggregate.max())),
)
axes[0].set_xticks(range(15), [f"{o}/{p}" for o in range(3) for p in range(5)])
axes[0].set_yticks(range(len(ordered)), [LABELS[n] for n in ordered])
axes[0].set_xlabel("orientation / phase; every frozen exposure")
axes[0].set_title("Exposure relative norm error (%)")
figure.colorbar(image, ax=axes[0], label="Error / same archived exposure norm (%)", shrink=0.8)
axes[1].barh(range(len(ordered)), aggregate, color="#2b6f94")
axes[1].invert_yaxis()
axes[1].set_yticks([])
axes[1].set_xlabel("Global norm ratio (%)")
axes[1].set_title("One denominator across all15")
for i, value in enumerate(aggregate):
    axes[1].text(value, i, f" {value:.4g}", va="center", fontsize=9)
axes[1].set_xlim(0, max(aggregate) * 1.25)
figure.savefig(OUT / "all-exposure-errors.png", dpi=170)
plt.close(figure)

public = {
    "schema": "simrecon.ra03.public-figure-evidence.v1",
    "frozen_center_um_zyx": list(CENTER),
    "detailed_exposure": [0, 0],
    "detector_spacing_um_zyx": list(SPACING),
    "origin_um_zyx": list(ORIGIN),
    "quantitative_views": quantitative,
    "signed_difference_views": difference,
    "metrics_all15": metrics,
    "conditional_contrasts": RECORD["conditional_contrasts"],
    "arms_by_orientation": [
        {"orientation": row["orientation"], "arms": row["arms"]}
        for row in RECORD["orientation_runs"]
    ],
    "rounding_by_orientation": [row["rounding"] for row in RECORD["orientation_runs"]],
    "source_to_relative": RECORD["source_to_relative"],
    "optics": RECORD["optics"],
    "source_identities": {
        str(Path(k).relative_to(Path.cwd()))
        if Path(k).is_absolute() and Path(k).is_relative_to(Path.cwd())
        else (Path(k).name if Path(k).is_absolute() else k): v
        for k, v in RECORD["source_identities"].items()
    },
    "array_inputs": [
        {k: row[k] for k in ["path", "shape", "dtype", "size_bytes", "sha256"]}
        for row in RECORD["outputs"]
    ],
    "original_inputs": RECORD["inputs"],
    "study_run_record_sha256": digest(RUN / "run-record.json"),
    "study_total_seconds": RECORD["total_seconds"],
    "process_ru_maxrss": RECORD["process_ru_maxrss"],
    "process_ru_maxrss_native_unit": RECORD["process_ru_maxrss_native_unit"],
    "runtime": {k: v for k, v in RECORD["runtime"].items() if k != "executable"},
    "plot_environment": {
        "python": sys.version,
        "matplotlib": version("matplotlib"),
        "numpy": version("numpy"),
        "resolved_distributions": sorted(
            [[d.metadata["Name"], d.version] for d in distributions()]
        ),
    },
    "renderer_sha256": digest(Path(__file__)),
    "figures": [
        {"path": name, "sha256": digest(OUT / name), "size_bytes": (OUT / name).stat().st_size}
        for name in [
            "forward-four-products.png",
            "signed-differences.png",
            "fixed-center-profiles.png",
            "all-exposure-errors.png",
        ]
    ],
    "limits": RECORD["limits"]
    + [
        (
            "Profiles in the right panel are separately shape normalized; "
            "other views retain quantitative scale"
        ),
        (
            "MIP differences subtract corresponding projections, "
            "not project a signed difference volume"
        ),
    ],
}
(OUT / "summary.json").write_text(
    json.dumps(
        public,
        indent=2,
        allow_nan=False,
        default=lambda a: a.item() if isinstance(a, np.generic) else a.tolist(),
    )
    + "\n"
)
Path("artifacts/ra03/plot-environment-final.json").write_text(
    json.dumps(
        {
            "actual_executable_during_render": sys.executable,
            "actual_prefix_during_render": sys.prefix,
            "resolved_distributions": sorted(
                [[d.metadata["Name"], d.version, str(d.locate_file(""))] for d in distributions()]
            ),
            "limit": (
                "Same-process observed environment only; uv may remove its temporary prefix "
                "normally after exit. No later executable custody claim."
            ),
        },
        indent=2,
    )
    + "\n"
)
print(
    json.dumps(
        {
            "figures": [
                "forward-four-products.png",
                "signed-differences.png",
                "fixed-center-profiles.png",
                "all-exposure-errors.png",
            ],
            "summary": str(OUT / "summary.json"),
        }
    )
)
