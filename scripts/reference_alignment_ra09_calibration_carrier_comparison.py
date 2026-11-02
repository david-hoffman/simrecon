"""Compare short-field and specimen carrier fits using the same RA09 operation.

This is a new known-response synthetic control. It does not execute a historical
pupil/bead fitter or establish a full calibration handoff or legacy C parity.
Preparation uses only independent helpers. Observation fits calibration data
alone, seals outputs, then reads truth and the already-frozen specimen result.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from typing import Any

import numpy as np

import reference_alignment_ra09_comparison as independent

Array = independent.Array
ROOT = independent.ROOT
DEFAULT_OUTPUT = ROOT / "artifacts/ra09/calibration-carrier-figure1"
SPECIMEN_OUTPUT = ROOT / "artifacts/ra09/figure-preparation"
CONTRACT = independent.CONTRACT
FIELDS = (
    "initial_carrier_per_um",
    "carrier_per_um",
    "gains",
    "order_status",
    "coherence",
    "relative_residual",
    "objective",
    "projected_gradient",
    "stationary",
    "information_singular_values",
    "information_rank",
    "status",
    "search_evaluations",
    "diagnostic_evaluations",
    "budget_exhausted",
    "diagnostics_continuous",
    "predictor_log2_norm",
    "response_log2_norm",
    "global_ambiguity",
)


def _identity() -> dict[str, Any]:
    original = independent._source_identity()
    return {
        **original,
        "helper_driver_sha256": original["driver_sha256"],
        "driver_sha256": independent._hash(Path(__file__)),
        "contract_sha256": independent._hash(ROOT / CONTRACT),
    }


def prepare(output: Path) -> None:
    """Freeze the predeclared noisy short-field data and independent expectations."""
    if (output / "prepared.json").exists():
        raise FileExistsError("Prepared control is immutable; select a separate declared run.")
    design_path = output / "design.json"
    design = independent._read_json(design_path)
    if independent._hash(Path(independent.__file__)) != design["original_helper_script_sha256"]:
        raise ValueError("Original independent helper changed; do not silently update its pin.")
    shape = tuple(design["calibration_shape_zyx"])
    spacing = np.asarray(design["spacing_um_zyx"])
    position = (independent._coordinates(shape) + 0.5) * spacing
    displacement = (position - np.asarray(design["bead_center_display_um_zyx"])) / np.asarray(
        design["bead_sigma_um_zyx"]
    )
    specimen = (
        design["bead_amplitude_relative"] * np.exp(-0.5 * np.sum(displacement**2, axis=1))
        + design["pedestal_relative"]
    ).reshape(shape)
    lengths = np.asarray(design["full_specimen_shape_zyx"])[1:] * spacing[1:]
    carrier = np.asarray(design["evaluation_only_true_full_specimen_bins_yx"]) / lengths
    gains = np.asarray(
        [
            amplitude * np.exp(1j * phase)
            for amplitude, phase in (
                design["evaluation_only_g1_amplitude_phase_rad"],
                design["evaluation_only_g2_amplitude_phase_rad"],
            )
        ]
    )
    kernels = np.zeros((3, 3, 3, 3), dtype=np.complex128)
    kernels[:, 1, 1, 1] = [
        design["transfer_E0"],
        design["transfer_E1_amplitude_phase_rad"][0]
        * np.exp(1j * design["transfer_E1_amplitude_phase_rad"][1]),
        design["transfer_E2_amplitude_phase_rad"][0]
        * np.exp(1j * design["transfer_E2_amplitude_phase_rad"][1]),
    ]
    clean = independent._model_bands(specimen, spacing, carrier, gains, kernels)
    noise = np.random.default_rng(design["noise_seed"]).normal(
        0, design["noise_sd_relative"], clean.shape + (2,)
    )
    bands = clean + noise[..., 0] + 1j * noise[..., 1]
    bands[0] = bands[0].real
    transfer = independent._kernel_transfer(kernels, shape)
    starts = np.asarray(design["nominal_full_specimen_bins_yx"])[None, :] / lengths
    bounds = np.asarray(design["bounds_full_specimen_bins_yx"]) / lengths
    controls = design["controls"]
    metadata = {
        "shape_zyx": shape,
        "spacing_um_zyx": spacing,
        "origin_zyx": [0, 0, 0],
        "source": "RA09 new short-field known-response calibration control",
        "initial_carriers_per_um": starts,
        "carrier_bounds_per_um": bounds,
        "difference_step_per_um": np.asarray(controls["difference_step_full_specimen_bins_yx"])
        / lengths,
        "gradient_tolerance": controls["gradient_tolerance"],
        "rank_rtol": controls["rank_rtol"],
        "max_evaluations": controls["max_evaluations"],
        "initialization": (
            "same physical acquisition metadata as original specimen; no truth initialization"
        ),
        "noise": {
            "model": design["noise_model"],
            "sd_relative": design["noise_sd_relative"],
            "seed": design["noise_seed"],
        },
        "coordinate_frames": {
            "phase": "n*spacing, index-zero origin; no half-cell phase correction",
            "display": "(n+0.5)*spacing",
            "display_minus_phase_um_zyx": design["display_minus_phase_origin_um_zyx"],
        },
    }
    support = tuple(independent._overlap(shape, spacing, bounds, m) for m in (1, 2))
    q = (support[0], support[1])
    nominal = independent._profile(bands, transfer, spacing, starts[0], q)
    generation = independent._profile(bands, transfer, spacing, carrier, q)
    noiseless = independent._profile(clean, transfer, spacing, carrier, q)
    allowance = independent._condition_and_allowances(bands, transfer, spacing, carrier, q)
    landscape = independent._landscape(bands, transfer, spacing, bounds, q)
    np.savez(output / "observations.npz", bands=bands, transfer=transfer)
    independent._write_json(output / "search.json", metadata)
    np.savez(
        output / "evaluation-truth.npz",
        specimen=specimen,
        carrier=carrier,
        gains=gains,
        kernels=kernels,
        clean_bands=clean,
    )
    np.savez(
        output / "expected-arrays.npz",
        q1=q[0],
        q2=q[1],
        x1=nominal["orders"][0]["x"],
        y1=nominal["orders"][0]["y"],
        x2=nominal["orders"][1]["x"],
        y2=nominal["orders"][1]["y"],
    )
    np.savez(
        output / "objective-landscape.npz",
        carrier_y_per_um=landscape["carrier_y_per_um"],
        carrier_x_per_um=landscape["carrier_x_per_um"],
        joint_objective=landscape["joint_objective"],
        order2_objective=landscape["order2_objective"],
    )
    independent._write_json(
        output / "expected.json",
        {
            "at_nominal": independent._summary(nominal),
            "at_generation_carrier": independent._summary(generation),
            "noiseless_at_generation_carrier": independent._summary(noiseless),
            "allowances": allowance,
            "fixed_overlap_counts": [len(s) for s in q],
            "method": "independent direct finite sums and normalized complex regression",
            "recovery_guarantee": None,
            "limits": (
                "This is one fixed noisy extended-bead control. No ordering of calibration "
                "versus specimen accuracy is promised. A low short-field residual or local "
                "rank does not establish full-field phase accuracy, a noise likelihood, "
                "global uniqueness, historical fitter behavior or legacy C parity."
            ),
        },
    )
    files = (
        "design.json",
        "observations.npz",
        "search.json",
        "evaluation-truth.npz",
        "expected-arrays.npz",
        "objective-landscape.npz",
        "expected.json",
    )
    independent._write_json(
        output / "prepared.json",
        {
            "schema": "simrecon.ra09.short-calibration-prepared.v1",
            "identity": _identity(),
            "files": {name: independent._hash(output / name) for name in files},
            "original_specimen_prepared_sha256": design["original_prepared_manifest_sha256"],
            "product_calls": 0,
            "human_numeric_limits": "not set",
            "truth_boundary": (
                "Observe checks only observations/search and hash-only provenance before "
                "calibration fit; calibration output is sealed before parsing specimen q, "
                "evaluation truth, design or expectations."
            ),
        },
    )
    print(f"Prepared and sealed {len(files)} short-calibration control files at {output}")


def _verify(output: Path, *, observations_only: bool = False) -> dict[str, Any]:
    prepared = independent._read_json(output / "prepared.json")
    if independent._hash(Path(__file__)) != prepared["identity"]["driver_sha256"]:
        raise ValueError("Companion driver changed after preparation.")
    if (
        independent._hash(Path(independent.__file__))
        != prepared["identity"]["helper_driver_sha256"]
    ):
        raise ValueError("Original independent helper changed after preparation.")
    if independent._hash(ROOT / CONTRACT) != prepared["identity"]["contract_sha256"]:
        raise ValueError("Public contract changed after preparation.")
    for name, digest in prepared["files"].items():
        if observations_only and name not in {"observations.npz", "search.json"}:
            continue
        if independent._hash(output / name) != digest:
            raise ValueError(f"Prepared artifact changed: {name}")
    return prepared


def _envelope(output: Path, specimen: Path, path: Path) -> dict[str, Any]:
    """Verify the coordinator's hash binding without inspecting implementation."""
    envelope = independent._read_json(path)
    if envelope["schema"] != "simrecon.ra09.shared-implementation.v1":
        raise ValueError("Unsupported shared-implementation envelope schema.")
    prepared = _verify(output, observations_only=True)
    hashes = envelope["source_hashes_at_specimen_observation"]
    if hashes != envelope["source_hashes_at_calibration_observation"]:
        raise ValueError("Coordinator must bind both observations to identical C sources.")
    if envelope["same_runtime_environment_attested"] is not True:
        raise ValueError("Coordinator must qualify the shared observation environment.")
    for name in ("src/simrecon/volume_overlap.py", "src/simrecon/__init__.py"):
        digest = hashes[name]
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError(f"Invalid coordinator source hash: {name}")
    required = {
        "contract_sha256": independent._hash(ROOT / CONTRACT),
        "calibration_prepared_sha256": independent._hash(output / "prepared.json"),
        "specimen_prepared_sha256": independent._hash(specimen / "prepared.json"),
        "specimen_observed_freeze_sha256": independent._hash(specimen / "observed-freeze.json"),
        "specimen_observed_json_sha256": independent._hash(specimen / "flat_noise/observed.json"),
    }
    for name, digest in required.items():
        if envelope[name] != digest:
            raise ValueError(f"Coordinator envelope mismatch: {name}")
    if required["specimen_prepared_sha256"] != prepared["original_specimen_prepared_sha256"]:
        raise ValueError("Specimen preparation differs from the originally sealed run.")
    original = independent._read_json(specimen / "observed-freeze.json")
    if original["identity"]["sources"][CONTRACT] != required["contract_sha256"]:
        raise ValueError("Specimen and calibration contracts differ.")
    if original["files"]["flat_noise/observed.json"] != required["specimen_observed_json_sha256"]:
        raise ValueError("Specimen result is not part of its original frozen output.")
    return envelope


def observe(output: Path, specimen: Path, authorization: str, envelope_path: Path) -> None:
    """Fit only calibration observations, freeze outputs, then compare saved q."""
    if not authorization.strip():
        raise ValueError("A nonempty coordinator observation authorization is required.")
    if (output / "observed-freeze.json").exists():
        raise FileExistsError("Calibration output is frozen; do not rerun or overwrite it.")
    envelope = _envelope(output, specimen, envelope_path)
    metadata = independent._read_json(output / "search.json")
    arrays = independent._load_arrays(output / "observations.npz")
    shape = tuple(metadata["shape_zyx"])
    spacing = np.asarray(metadata["spacing_um_zyx"])
    grids = [independent._bins(n) / (n * d) for n, d in zip(shape, spacing, strict=True)]
    product = importlib.import_module("simrecon")
    calibration = product.VolumeOrderOtf(
        values=arrays["transfer"],
        fz_per_um=grids[0],
        fy_per_um=grids[1],
        fx_per_um=grids[2],
        voxel_size_um=tuple(spacing),
        origin_zyx=tuple(metadata["origin_zyx"]),
        source=metadata["source"],
    )
    result = product.fit_volume_overlap(
        arrays["bands"],
        order_otf=calibration,
        initial_carriers_per_um=np.asarray(metadata["initial_carriers_per_um"]),
        carrier_bounds_per_um=np.asarray(metadata["carrier_bounds_per_um"]),
        difference_step_per_um=np.asarray(metadata["difference_step_per_um"]),
        gradient_tolerance=metadata["gradient_tolerance"],
        rank_rtol=metadata["rank_rtol"],
        max_evaluations=metadata["max_evaluations"],
    )
    independent._write_json(
        output / "observed.json",
        {
            "candidates": [
                {field: getattr(c, field) for field in FIELDS} for c in result.candidates
            ],
            "spacing_um": result.spacing_um,
            "source": result.source,
            "carrier_bounds_per_um": result.carrier_bounds_per_um,
        },
    )
    np.savez(output / "observed-arrays.npz", q1=result.overlap_bins[0], q2=result.overlap_bins[1])
    independent._write_json(output / "coordinator-envelope.json", envelope)
    independent._write_json(
        output / "observed-freeze.json",
        {
            "authorization": authorization,
            "identity": _identity(),
            "prepared_sha256": independent._hash(output / "prepared.json"),
            "coordinator_envelope_sha256": independent._hash(output / "coordinator-envelope.json"),
            "files": {
                name: independent._hash(output / name)
                for name in ("observed.json", "observed-arrays.npz", "coordinator-envelope.json")
            },
            "truth_or_specimen_carrier_parsed_before_freeze": False,
            "implementation_binding": (
                "Coordinator qualifies identical C source hashes and environment for both "
                "frozen observations. Companion checks this envelope; it does not read C source."
            ),
        },
    )
    # First parsing of specimen candidates and all evaluation truth occurs here.
    _evaluate(output, specimen)
    print(f"Observed calibration once; sealed output and compared frozen specimen at {output}")


def _evaluate(output: Path, specimen_output: Path) -> None:
    _verify(output)
    independent._verify_prepared(specimen_output)
    metadata = independent._read_json(output / "search.json")
    expected = independent._read_json(output / "expected.json")
    truth = independent._load_arrays(output / "evaluation-truth.npz")
    arrays = independent._load_arrays(output / "observations.npz")
    saved = independent._load_arrays(output / "expected-arrays.npz")
    observed_support = independent._load_arrays(output / "observed-arrays.npz")
    observed = independent._read_json(output / "observed.json")["candidates"][0]
    specimen = independent._read_json(specimen_output / "flat_noise/observed.json")["candidates"][0]
    full_truth = independent._load_arrays(specimen_output / "flat_noise/evaluation-truth.npz")
    full_metadata = independent._read_json(specimen_output / "flat_noise/search.json")
    catalogue = independent._read_json(specimen_output / "catalogue.json")
    if not np.array_equal(truth["carrier"], full_truth["carrier"]):
        raise ValueError("The predeclared controls must share physical generation carrier.")
    if not np.array_equal(truth["gains"], full_truth["gains"]):
        raise ValueError("The predeclared controls must share relative gain gauge.")
    spacing = np.asarray(metadata["spacing_um_zyx"])
    carrier = np.asarray(observed["carrier_per_um"])
    q = (saved["q1"], saved["q2"])
    profile = independent._profile(arrays["bands"], arrays["transfer"], spacing, carrier, q)
    independent._write_json(
        output / "calibration-evaluation.json",
        {
            "independent_at_retained_point": independent._summary(profile),
            "objective_absolute_difference": abs(observed["objective"] - profile["objective"]),
            "objective_within_predeclared_allowance": abs(
                observed["objective"] - profile["objective"]
            )
            <= expected["allowances"]["arithmetic_objective_absolute_allowance"],
            "overlap_equal": all(
                np.array_equal(saved[k], observed_support[k]) for k in ("q1", "q2")
            ),
            "diagnostics": observed,
            "limits": expected["limits"],
        },
    )
    full_shape = full_truth["specimen"].shape
    phase_coordinates = independent._coordinates(full_shape) * spacing
    values: dict[str, Array] = {}
    metrics = {}
    for label, candidate in (("calibration", observed), ("specimen", specimen)):
        fitted = np.asarray(candidate["carrier_per_um"])
        gains = np.asarray([independent._complex(g) for g in candidate["gains"]])
        phase = (2 * np.pi * phase_coordinates[:, 1:] @ (fitted - truth["carrier"])).reshape(
            full_shape
        )
        values[f"{label}_carrier_phase_error_order1_rad"] = phase
        predictions = independent._model_bands(
            full_truth["specimen"], spacing, fitted, gains, full_truth["kernels"]
        )
        values[f"{label}_heldout_prediction"] = independent._exposure(
            predictions, full_metadata["heldout_phase_rad"]
        )
        metrics[label] = {
            "carrier_per_um_yx": fitted,
            "carrier_error_in_full_specimen_bins_yx": (fitted - truth["carrier"])
            * np.asarray(full_shape)[1:]
            * spacing[1:],
            "max_carrier_only_phase_error_rad_by_order": [
                float(np.max(abs(phase))) * m for m in (1, 2)
            ],
            "gain_only_phase_error_rad_by_order": np.angle(gains / truth["gains"]),
            "gain_amplitude_ratio_by_order": abs(gains / truth["gains"]),
            "local_fit_objective": candidate["objective"],
            "local_fit_status": candidate["status"],
            "local_fit_information_rank": candidate["information_rank"],
            "global_ambiguity": candidate["global_ambiguity"],
        }
    reference = independent._exposure(full_truth["clean_bands"], full_metadata["heldout_phase_rad"])
    reference += full_truth["heldout_noise"]
    values["heldout_reference"] = reference
    for label in ("calibration", "specimen"):
        difference = values[f"{label}_heldout_prediction"] - reference
        values[f"{label}_heldout_signed_difference"] = difference
        metrics[label]["relative_full_field_heldout_l2"] = float(
            np.linalg.norm(difference) / np.linalg.norm(reference)
        )
    np.savez(
        output / "full-field-evaluation-arrays.npz",
        calibration_carrier_phase_error_order1_rad=values[
            "calibration_carrier_phase_error_order1_rad"
        ],
        specimen_carrier_phase_error_order1_rad=values["specimen_carrier_phase_error_order1_rad"],
        calibration_heldout_prediction=values["calibration_heldout_prediction"],
        specimen_heldout_prediction=values["specimen_heldout_prediction"],
        heldout_reference=reference,
        calibration_heldout_signed_difference=values["calibration_heldout_signed_difference"],
        specimen_heldout_signed_difference=values["specimen_heldout_signed_difference"],
        calibration_x1=profile["orders"][0]["x"],
        calibration_y1=profile["orders"][0]["y"],
        calibration_x2=profile["orders"][1]["x"],
        calibration_y2=profile["orders"][1]["y"],
    )
    independent._write_json(
        output / "full-field-evaluation.json",
        {
            "metrics": metrics,
            "fixed_specimen_section_indices_zyx": catalogue["section_indices_zyx"],
            "full_specimen_shape_zyx": full_shape,
            "spacing_um_zyx": spacing,
            "coordinate_frames": metadata["coordinate_frames"],
            "no_post_fit_alignment": True,
            "winner_selection": None,
            "comparison": (
                "One new short-calibration control versus the already frozen full-specimen "
                "flat_noise candidate. Same public operation, fixed calibration gauge and "
                "coordinator-qualified C identity. No specimen refit or candidate selection."
            ),
            "limits": expected["limits"],
        },
    )
    names = (
        "calibration-evaluation.json",
        "full-field-evaluation.json",
        "full-field-evaluation-arrays.npz",
    )
    independent._write_json(
        output / "evaluation-freeze.json",
        {
            "observed_freeze_sha256": independent._hash(output / "observed-freeze.json"),
            "files": {name: independent._hash(output / name) for name in names},
        },
    )


def _field_figure(
    plt: Any, output: Path, arrays: dict[str, Array], metadata: dict[str, Any]
) -> None:
    reference = arrays["heldout_reference"]
    spacing = np.asarray(metadata["spacing_um_zyx"])
    z, y, _ = metadata["fixed_specimen_section_indices_zyx"]
    views = (
        ("XY maximum over z", lambda v: np.max(v, axis=0), (2, 1)),
        ("XZ maximum over y", lambda v: np.max(v, axis=1), (2, 0)),
        (f"XY fixed section z={z}", lambda v: v[z], (2, 1)),
        (f"XZ fixed section y={y}", lambda v: v[:, y], (2, 0)),
    )
    low = min(
        float(reference.min()),
        *(float(arrays[f"{s}_heldout_prediction"].min()) for s in ("calibration", "specimen")),
    )
    high = max(
        float(reference.max()),
        *(float(arrays[f"{s}_heldout_prediction"].max()) for s in ("calibration", "specimen")),
    )
    limit = (
        max(
            float(np.max(abs(view(arrays[f"{s}_heldout_prediction"]) - view(reference))))
            for _, view, _ in views
            for s in ("calibration", "specimen")
        )
        or independent.EPS
    )
    for label in ("calibration", "specimen"):
        figure, axes = plt.subplots(4, 3, figsize=(13, 10), layout="constrained")
        prediction = arrays[f"{label}_heldout_prediction"]
        for row, (view_label, view, dimensions) in enumerate(views):
            horizontal, vertical = dimensions
            extent = (
                0,
                reference.shape[horizontal] * spacing[horizontal],
                0,
                reference.shape[vertical] * spacing[vertical],
            )
            for column, (title, image) in enumerate(
                (
                    ("Held-out reference", view(reference)),
                    (f"{label} q/g prediction", view(prediction)),
                    ("Prediction − reference", view(prediction) - view(reference)),
                )
            ):
                artist = axes[row, column].imshow(
                    image,
                    origin="lower",
                    extent=extent,
                    aspect="equal",
                    interpolation="nearest",
                    cmap="coolwarm" if column == 2 else "viridis",
                    vmin=-limit if column == 2 else low,
                    vmax=limit if column == 2 else high,
                )
                axes[row, column].set(
                    title=f"{view_label}: {title}",
                    xlabel=f"{'zyx'[horizontal]} (µm)",
                    ylabel=f"{'zyx'[vertical]} (µm)",
                )
                figure.colorbar(
                    artist, ax=axes[row, column], label="relative intensity units", shrink=0.8
                )
        figure.suptitle(
            "Known-source held-out prediction after both fits freeze; "
            "shared scales across both fit panels"
        )
        figure.savefig(output / f"{label}-q-full-field.png", dpi=170)
        plt.close(figure)


def render(output: Path) -> None:
    """Render actual sealed calibration/specimen comparisons with lazy plotting."""
    _verify(output)
    for marker in ("observed-freeze.json", "evaluation-freeze.json"):
        frozen = independent._read_json(output / marker)
        for name, digest in frozen["files"].items():
            if independent._hash(output / name) != digest:
                raise ValueError(f"Frozen comparison output changed: {name}")
    plt = importlib.import_module("matplotlib.pyplot")
    arrays = independent._load_arrays(output / "full-field-evaluation-arrays.npz")
    metadata = independent._read_json(output / "full-field-evaluation.json")
    _field_figure(plt, output, arrays, metadata)
    spacing = np.asarray(metadata["spacing_um_zyx"])
    z, y, x = metadata["fixed_specimen_section_indices_zyx"]
    cal = arrays["calibration_carrier_phase_error_order1_rad"]
    full = arrays["specimen_carrier_phase_error_order1_rad"]
    limit = (
        2 * max(float(np.max(abs(cal))), float(np.max(abs(full))), float(np.max(abs(cal - full))))
        or independent.EPS
    )
    figure, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    for row, order in enumerate((1, 2)):
        for column, (label, phase) in enumerate(
            (
                ("Short calibration q", cal),
                ("Frozen specimen q", full),
                ("Calibration − specimen", cal - full),
            )
        ):
            artist = axes[row, column].imshow(
                order * phase[z],
                origin="lower",
                extent=(0, cal.shape[2] * spacing[2], 0, cal.shape[1] * spacing[1]),
                aspect="equal",
                interpolation="nearest",
                cmap="coolwarm",
                vmin=-limit,
                vmax=limit,
            )
            axes[row, column].set(title=f"Order {order}: {label}", xlabel="x (µm)", ylabel="y (µm)")
            figure.colorbar(
                artist,
                ax=axes[row, column],
                label="unwrapped carrier-only phase error (rad)",
                shrink=0.8,
            )
    figure.suptitle(
        "Full specimen field; index-zero phase; zero axial carrier; gain phase excluded"
    )
    figure.savefig(output / "calibration-vs-specimen-phase-maps.png", dpi=170)
    plt.close(figure)
    figure, axes = plt.subplots(1, 3, figsize=(14, 4), layout="constrained")
    for label, phase in (("Short calibration q", cal), ("Frozen specimen q", full)):
        axes[0].plot((np.arange(cal.shape[2]) + 0.5) * spacing[2], 2 * phase[z, y], label=label)
        axes[1].plot((np.arange(cal.shape[1]) + 0.5) * spacing[1], 2 * phase[z, :, x], label=label)
    axes[0].set(
        title="Order-two phase: fixed bead-center x line",
        xlabel="x (µm)",
        ylabel="unwrapped carrier-only error (rad)",
    )
    axes[1].set(
        title="Order-two phase: fixed bead-center y line",
        xlabel="y (µm)",
        ylabel="unwrapped carrier-only error (rad)",
    )
    for label in ("calibration", "specimen"):
        axes[2].plot(
            (1, 2),
            metadata["metrics"][label]["gain_only_phase_error_rad_by_order"],
            "o-",
            label=label,
        )
    axes[2].set(
        title="Relative gain/common phase at index-zero origin",
        xlabel="positive order",
        ylabel="gain-only phase error (rad)",
        xticks=(1, 2),
    )
    for ax in axes:
        ax.legend(fontsize=8)
    figure.savefig(output / "phase-profiles-and-gain-phase.png", dpi=170)
    plt.close(figure)
    observed = independent._read_json(output / "observed.json")["candidates"][0]
    landscape = independent._load_arrays(output / "objective-landscape.npz")
    support = independent._load_arrays(output / "expected-arrays.npz")
    search = independent._read_json(output / "search.json")
    figure, axes = plt.subplots(1, 3, figsize=(14, 4), layout="constrained")
    artist = axes[0].pcolormesh(
        landscape["carrier_x_per_um"],
        landscape["carrier_y_per_um"],
        landscape["joint_objective"],
        shading="nearest",
    )
    fit = np.asarray(observed["carrier_per_um"])
    nominal = np.asarray(search["initial_carriers_per_um"][0])
    axes[0].plot(fit[1], fit[0], "rx", label="retained calibration fit")
    axes[0].plot(nominal[1], nominal[0], "wo", label="nominal metadata")
    axes[0].set(
        title=f"Short-field J; retained J={observed['objective']:.4g}",
        xlabel="kx (cycles/µm)",
        ylabel="ky (cycles/µm)",
    )
    figure.colorbar(artist, ax=axes[0], label="dimensionless normalized objective")
    cal_shape = np.asarray(search["shape_zyx"])
    for order in (1, 2):
        q = support[f"q{order}"]
        section = q[q[:, 0] == 0]
        axes[1].scatter(
            section[:, 2] / (cal_shape[2] * spacing[2]),
            section[:, 1] / (cal_shape[1] * spacing[1]),
            s=20,
            marker="o" if order == 1 else "x",
            label=f"order {order}, {len(q)} total Q bins",
        )
        gain = independent._complex(observed["gains"][order - 1])
        axes[2].plot(
            abs(arrays[f"calibration_y{order}"] - gain * arrays[f"calibration_x{order}"]),
            label=f"order {order}",
        )
    axes[1].set(
        title="Calibration fixed Q, qz=0",
        xlabel="qx (cycles/µm)",
        ylabel="qy (cycles/µm)",
        aspect="equal",
    )
    axes[2].set(
        title="Calibration cross-weighted residual",
        xlabel="lexicographic Q sample",
        ylabel="absolute complex residual",
    )
    for ax in axes:
        ax.legend(fontsize=8)
    figure.suptitle(
        f"New known-response calibration control: {observed['status']}; "
        f"rank {observed['information_rank']}; no uniqueness claim"
    )
    figure.savefig(output / "calibration-objective-support-residual.png", dpi=170)
    plt.close(figure)
    files = sorted(output.glob("*.png"))
    independent._write_json(
        output / "rendered.json",
        {
            "identity": _identity(),
            "files": {p.name: independent._hash(p) for p in files},
            "matplotlib": importlib.import_module("matplotlib").__version__,
            "evaluation_freeze_sha256": independent._hash(output / "evaluation-freeze.json"),
            "limits": metadata["limits"],
        },
    )
    print(f"Rendered {len(files)} sealed short-calibration comparison figures at {output}")


def main() -> None:
    """Run an explicit stage without permitting implicit observation or refit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "observe", "render"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--specimen-output", type=Path, default=SPECIMEN_OUTPUT)
    parser.add_argument("--authorization", default="")
    parser.add_argument("--coordinator-envelope", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.output)
    elif args.mode == "render":
        render(args.output)
    else:
        if args.coordinator_envelope is None:
            parser.error("observe requires --coordinator-envelope and --authorization")
        observe(args.output, args.specimen_output, args.authorization, args.coordinator_envelope)


if __name__ == "__main__":
    main()
