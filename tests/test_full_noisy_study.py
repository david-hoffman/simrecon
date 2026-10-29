"""Public CLI proof for full noisy study; see fixture's pre-authorship ledger.

No missing-driver bypass: before implementation these CLI tests are unavailable
evidence, not product-red. Independent observer/dependency controls may pass.
"""

from __future__ import annotations

import copy
import itertools
import json
import math
import os
import resource
import shutil
import signal
import subprocess
import sys
import time
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from full_noisy_study_fixture import (
    COMMAND_LEDGER,
    COMPARISONS,
    LIMITATIONS,
    NOMINAL,
    OBS_NAMES,
    PRED_NAMES,
    PRIVATE_NAMES,
    RAW_NAMES,
    SETTINGS,
    D,
    acquisition,
    check_available_metric,
    check_metric,
    check_normalized_beam_errors,
    cli,
    close_scalar,
    dec,
    descriptor,
    encoded,
    evaluate_args,
    exact_source,
    expect,
    finite_mean_prediction_references,
    in_process_cli,
    infer_args,
    keys,
    load_json,
    metric_reference,
    observation_bundle,
    paired_axial_reference,
    physical_pi,
    plan,
    read_npy,
    reseal,
    save_declared_order_npy,
    save_npy,
    sha,
    snapshot,
    source_free_environment,
    transferred,
    wrap_reference,
    write_json,
)

# Public record field names copied from adopted contracts, never runtime source.
FIELDS = {
    "ScalarCameraEstimate": (
        "means_counts variances_counts2 frame_means_counts frame_variances_counts2 "
        "empirical_mean_se_counts contrast_counts gain_counts_per_e information_codes "
        "source"
    ),
    "PilotCandidate": (
        "centers_um_zyx brightness_relative carriers_yx_per_um phases_rad "
        "beam_amplitudes occupied_counts stored_unit_masses_e"
    ),
    "BeadCalibrationScore": (
        "stage pupil_order coordinates candidate objective outcome failure_code"
    ),
    "BeadCalibrationAttempt": (
        "sweep_index coordinate_index sign base_score_index trial_coordinates "
        "coordinate_changed parameter_changed outcome infeasibility_reason score_index "
        "selected information_codes failure_code"
    ),
    "BeadCoordinateEvidence": (
        "coordinate_index attempt_count scored_count distinct_coordinate_scored_count "
        "distinct_parameter_scored_count selected_count information_codes"
    ),
    "BeadCalibrationCounts": (
        "planned_poll_attempts attempted_polls scored_polls infeasible_polls "
        "numerical_incomplete_polls completed_pairs completed_sweeps score_attempts "
        "successful_scores"
    ),
    "BeadCalibrationResult": (
        "status stage message failure_code detector_shape_zyx origin_um_zyx "
        "scipy_version camera_source blank_counts contrast_counts sweep_scales "
        "initialization_notes initial_candidate initial_coordinates best_candidate "
        "best_coordinates best_score_index incumbent_score_index frozen_candidate "
        "frozen_coordinates objective_trace poll_attempts coordinate_evidence "
        "unprobed_coordinates counts training_objectives_q128_q256_q512 "
        "heldout_prediction heldout_residual_mean heldout_residual_rms"
    ),
    "SpecimenScore": (
        "candidate_id data_objective penalty_objective total_objective residual_mean residual_rms"
    ),
    "SpecimenGradientSummary": "candidate_id max_abs",
    "SpecimenFitAttempt": (
        "candidate_id iteration trial from_candidate_id gradient_candidate_id step "
        "projected_gradient_max_abs outcome score gradient_state gradient"
    ),
    "SpecimenFitCall": "call_index operation purpose candidate_id orientation outcome failure_code",
    "SpecimenFitCounts": (
        "cache_attempted cache_completed cache_failed forward_attempted "
        "forward_completed forward_failed adjoint_attempted adjoint_completed "
        "adjoint_failed score_attempts scores_completed gradient_attempts "
        "gradients_completed seed_attempts seeds_completed iterations_started "
        "trials_attempted trials_accepted trials_rejected trials_unrepresentable "
        "trials_stagnated best_updates"
    ),
    "SpecimenFitResult": (
        "status stage stop_reason message failure_code failure_component "
        "detector_shape_zyx source_shape_zyx detector_spacing_um_zyx "
        "source_spacing_um_zyx specimen_origin_um_zyx excitation_um emission_um "
        "refractive_index detection_na pixel_samples_yx pupil_order regularization "
        "max_iterations max_backtracking_trials camera_means_counts blank_counts "
        "contrast_counts camera_source carriers_yx_per_um phases_at_specimen_origin_rad"
        " beam_amplitudes illumination_source source_relative initial_score best_score "
        "last_complete_gradient seed_step attempt_trace call_trace counts"
    ),
}


def public_record(value: Any) -> Any:
    """Observe only documented fields of named public returned records."""
    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, np.ndarray):
        return value.tolist()
    if type(value) is tuple:
        return [public_record(item) for item in value]
    name = type(value).__name__
    assert name in FIELDS
    result = {}
    for field in FIELDS[name].split():
        item = getattr(value, field)
        if item is not None and field in ("heldout_prediction", "source_relative"):
            result[field] = {
                "file": "bead_heldout_prediction.npy"
                if field == "heldout_prediction"
                else "specimen_source_relative.npy"
            }
        else:
            result[field] = public_record(item)
    return result


def check_runtime(value: dict[str, Any]) -> None:
    keys(
        value,
        (
            "python_version numpy_version scipy_version simrecon_version platform byteorder"
            " driver_sha256"
        ),
    )
    for name in (
        "python_version",
        "numpy_version",
        "scipy_version",
        "simrecon_version",
        "platform",
    ):
        assert value[name] is None or (type(value[name]) is str and value[name].strip())
    assert type(value["python_version"]) is str and value["python_version"].strip()
    assert type(value["platform"]) is str and value["platform"].strip()
    assert value["byteorder"] in ("little", "big")
    digest = value["driver_sha256"]
    assert type(digest) is str and len(digest) == 64 and set(digest) <= set("0123456789abcdef")


def check_descriptors(root: Path, items: list[dict[str, Any]], names: list[str]) -> None:
    assert [item["path"] for item in items] == names
    for item in items:
        assert item == descriptor(root, item["path"])
        if item["path"].endswith(".npy"):
            array = read_npy(root, item)
            assert item["dtype"] == (
                "<f4" if item["path"] == "specimen_source_relative.npy" else "<f8"
            )
            if "source" in item["path"] or "expected_signal" in item["path"]:
                assert np.all(array >= 0)


def check_estimates(root: Path) -> dict[str, Any]:
    result = load_json(root / "estimates.json", canonical=True)
    keys(
        result,
        (
            "format_version observation_manifest_sha256 algorithm_settings runtime "
            "fit_status fit_stage message failure_code camera_estimate bead_calibration "
            "specimen_fit transferred_phases_at_specimen_origin_rad"
        ),
    )
    assert result["format_version"] == "full_noisy_study_estimates_v1"
    assert result["message"].strip()
    check_runtime(result["runtime"])
    keys(
        result["algorithm_settings"],
        "sweep_scales regularization max_iterations max_backtracking_trials pupil_order",
    )
    return result


def check_freeze(root: Path, *, complete: bool) -> dict[str, Any]:
    freeze = load_json(root / "freeze.json", canonical=True)
    keys(
        freeze,
        (
            "format_version status stage message failure_code observation_manifest_sha256 "
            "files prediction_call_counts"
        ),
    )
    assert freeze["format_version"] == "full_noisy_study_freeze_v1"
    assert freeze["message"].strip()
    names = [item["path"] for item in freeze["files"]]
    assert names[0] == "estimates.json"
    check_descriptors(root, freeze["files"], names)
    keys(
        freeze["prediction_call_counts"],
        (
            "cache_attempted cache_completed cache_failed forward_attempted "
            "forward_completed forward_failed"
        ),
    )
    if complete:
        assert freeze["status"] == "completed_finite_fit" and freeze["stage"] == "complete"
        assert freeze["failure_code"] is None
        assert names == [
            "estimates.json",
            "bead_heldout_prediction.npy",
            "specimen_source_relative.npy",
            *PRED_NAMES,
        ]
        assert freeze["prediction_call_counts"] == dict(
            zip(
                [
                    "cache_attempted",
                    "cache_completed",
                    "cache_failed",
                    "forward_attempted",
                    "forward_completed",
                    "forward_failed",
                ],
                (1, 1, 0, 3, 3, 0),
                strict=True,
            )
        )
    else:
        assert freeze["status"] == "unavailable"
    return freeze


def check_evaluation(
    root: Path, observations: Path, inference: Path, truth: Path
) -> dict[str, Any]:
    report = load_json(root / "evaluation.json", canonical=True)
    keys(
        report,
        (
            "format_version status message runtime observation_manifest_sha256 "
            "inference_freeze_sha256 private_truth_manifest_sha256 inference_status "
            "inference_stage inference_failure_code camera_comparison source_metrics "
            "signal_prediction_metrics corrected_mean_prediction_metrics "
            "observed_residual_mean observed_residual_rms bead_permutation_comparisons "
            "illumination_gauge_comparisons unavailable_comparisons limitations"
        ),
    )
    assert report["format_version"] == "full_noisy_study_evaluation_v1"
    assert report["message"].strip() and report["limitations"] == LIMITATIONS
    check_runtime(report["runtime"])
    marker = load_json(root / "complete.json", canonical=True)
    keys(
        marker,
        (
            "format_version status observation_manifest_sha256 inference_freeze_sha256 "
            "private_truth_manifest_sha256 files"
        ),
    )
    assert marker["format_version"] == "full_noisy_study_evaluation_complete_v1"
    assert type(marker["files"]) is dict  # adopted schema note, NOT a list
    assert marker["files"] == descriptor(root, "evaluation.json")
    for name, path in (
        ("observation_manifest_sha256", observations / "complete.json"),
        ("inference_freeze_sha256", inference / "freeze.json"),
        ("private_truth_manifest_sha256", truth / "complete.json"),
    ):
        assert report[name] == marker[name] == sha(path)
    assert marker["status"] == report["status"]
    return report


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Only the real CLI can supply completed records used by later controls."""
    root = tmp_path_factory.mktemp("full-noisy-A-public-complete")
    return run_public_pipeline(root, plan())


def run_public_pipeline(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    """Obtain every successful workflow artifact from the real separate-process CLI."""
    plan_path = root / "public-plan.json"
    # Reader must accept noncanonical whitespace/order while hashing original bytes.
    plan_path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    run, inference, evaluation = root / "generated", root / "inference", root / "evaluation"
    expect(cli("generate", "--plan", str(plan_path), "--out", str(run)), 0)
    observations, truth = run / "observations", run / "private_truth"
    generated = snapshot(run)
    inferred = cli(*infer_args(observations, inference))
    if inferred.returncode != 0:
        state = load_json(inference / "estimates.json")
        bead = state["bead_calibration"]
        raise AssertionError(
            {
                "returncode": inferred.returncode,
                "stage": state["fit_stage"],
                "contrast": state["camera_estimate"]["contrast_counts"],
                "bead_status": None if bead is None else bead["status"],
                "bead_stage": None if bead is None else bead["stage"],
            }
        )
    expect(inferred, 0)
    frozen = snapshot(inference)
    expect(cli(*evaluate_args(observations, inference, truth, evaluation)), 0)
    assert snapshot(run) == generated and snapshot(inference) == frozen
    assert json.loads(plan_path.read_text()) == value
    return dict(
        root=root,
        plan=value,
        plan_path=plan_path,
        run=run,
        observations=observations,
        truth=truth,
        inference=inference,
        evaluation=evaluation,
    )


def test_generation_protocol_and_independent_source_reference(
    pipeline: dict[str, Any],
) -> None:
    run, obs, truth, value = (pipeline[k] for k in ("run", "observations", "truth", "plan"))
    manifest = load_json(obs / "complete.json", canonical=True)
    keys(manifest, "format_version geometry acquisition_model nominal_phase_commands_rad files")
    assert manifest["format_version"] == "full_noisy_study_observations_v1"
    assert manifest["geometry"] == value["geometry"]
    assert manifest["acquisition_model"] == acquisition()
    assert manifest["nominal_phase_commands_rad"] == NOMINAL
    check_descriptors(obs, manifest["files"], OBS_NAMES)
    assert set(p.name for p in obs.iterdir()) == {*OBS_NAMES, "complete.json"}
    seal = load_json(truth / "complete.json", canonical=True)
    keys(seal, "format_version observation_manifest_sha256 files")
    assert seal["format_version"] == "full_noisy_study_truth_v1"
    assert seal["observation_manifest_sha256"] == sha(obs / "complete.json")
    check_descriptors(truth, seal["files"], PRIVATE_NAMES)
    assert set(p.name for p in truth.iterdir()) == {*PRIVATE_NAMES, "complete.json"}
    marker = load_json(run / "generation.complete.json", canonical=True)
    keys(marker, "format_version status observation_manifest_sha256 private_truth_manifest_sha256")
    assert marker == {
        "format_version": "full_noisy_study_generation_v1",
        "status": "generated",
        "observation_manifest_sha256": sha(obs / "complete.json"),
        "private_truth_manifest_sha256": sha(truth / "complete.json"),
    }
    assert set(p.name for p in run.iterdir()) == {
        "observations",
        "private_truth",
        "generation.complete.json",
    }
    assert load_json(truth / "plan.json", canonical=True) == value
    summary = load_json(truth / "generation_summary.json", canonical=True)
    keys(
        summary,
        (
            "format_version runtime plan_input_sha256 "
            "specimen_phases_at_specimen_origin_rad source_model source_mass"
        ),
    )
    assert summary["format_version"] == "full_noisy_study_truth_v1"
    assert summary["plan_input_sha256"] == sha(pipeline["plan_path"])
    assert summary["source_model"] == "closed_midpoint_total_normalized_catalogue_order"
    check_runtime(summary["runtime"])
    keys(summary["source_mass"], "bead specimen")
    for name, refinement in (("bead", (8, 8, 8)), ("specimen", (2, 2, 2))):
        prefix = "calibration" if name == "bead" else "specimen"
        expected = exact_source(
            value[f"{name}_catalogue"],
            value["geometry"][f"{prefix}_shape_zyx"],
            value["geometry"][f"{prefix}_spacing_um_zyx"],
            refinement,
        )
        stored = np.load(truth / f"{name}_source_e.npy", allow_pickle=False)
        np.testing.assert_array_equal(stored, expected)
        mass = summary["source_mass"][name]
        keys(
            mass,
            "catalogue_total_e stored_total_e difference_e relative_difference unavailable_fields",
        )
        with localcontext() as ctx:
            ctx.prec = 100
            target = sum((dec(row[4]) for row in value[f"{name}_catalogue"]), Decimal(0))
            total = sum((dec(x) for x in expected.flat), Decimal(0))
            close_scalar(mass["catalogue_total_e"], float(target))
            close_scalar(mass["stored_total_e"], float(total))
            close_scalar(mass["difference_e"], float(total - target), scale=float(target))
            close_scalar(mass["relative_difference"], float((total - target) / target), scale=1.0)
        assert mass["unavailable_fields"] == []
    expected_phases = transferred(
        value["illumination"]["phases_at_calibration_origin_rad"],
        value["illumination"]["carriers_yx_per_um"],
        value["geometry"]["calibration_origin_um_zyx"],
        value["geometry"]["specimen_origin_um_zyx"],
    )
    np.testing.assert_allclose(
        summary["specimen_phases_at_specimen_origin_rad"],
        expected_phases,
        rtol=0,
        atol=64 * np.finfo(float).eps,
    )


def test_generation_real_scientific_call_composition(pipeline: dict[str, Any]) -> None:
    from scripts.simulation_camera import sample_camera
    from scripts.simulation_optics import expected_images

    value, truth, obs = (pipeline[k] for k in ("plan", "truth", "observations"))
    geometry, camera, illumination = (value[k] for k in ("geometry", "camera", "illumination"))
    camera_kw = {
        name: camera[name] for name in ("read_noise_e", "gain_counts_per_e", "offset_counts")
    }
    optics = dict(
        excitation_um=0.488,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=value["generator_pupil_order"],
        pixel_subsamples_yx=(2, 2),
    )
    # Accepted public operations establish wiring/seed chunk relations ONLY.
    # Their own mathematical accuracy is not inferred from self-comparison.
    for group in ("dark", "blank", "flat"):
        signal = np.full(
            tuple(geometry["camera_shape_yx"]), camera["flat_signal_e"] if group == "flat" else 0.0
        )
        expected = np.stack(
            [
                sample_camera(
                    signal,
                    background_e=0.0 if group == "dark" else camera["background_e"],
                    seed=seed,
                    shot_noise=True,
                    **camera_kw,
                )
                for seed in value["seeds"][f"camera_{group}"]
            ]
        )
        np.testing.assert_array_equal(
            np.load(obs / f"camera_{group}.npy", allow_pickle=False), expected
        )
    bead = np.load(truth / "bead_source_e.npy", allow_pickle=False)
    q = np.asarray(illumination["carriers_yx_per_um"], dtype=np.float64)
    phases = np.asarray(illumination["phases_at_calibration_origin_rad"], dtype=np.float64)
    beam = tuple(float(x) for x in illumination["beam_amplitudes"])
    central = expected_images(
        bead,
        detector_spacing_um_zyx=D,
        source_refinement_zyx=(8, 8, 8),
        carriers_yx_per_um=np.zeros((1, 2)),
        phases_rad=np.zeros((1, 1)),
        beam_amplitudes=(1.0, 0.0, 0.0),
        **optics,
    )[0, 0]
    training = expected_images(
        bead,
        detector_spacing_um_zyx=D,
        source_refinement_zyx=(8, 8, 8),
        carriers_yx_per_um=q,
        phases_rad=phases,
        beam_amplitudes=beam,
        **optics,
    )
    for label, mean, seed_values in (
        ("central", central, value["seeds"]["calibration_central"]),
        ("training", training, value["seeds"]["calibration_training"]),
        ("heldout", training[:, :5], value["seeds"]["calibration_heldout"]),
    ):
        np.testing.assert_array_equal(
            np.load(truth / f"calibration_{label}_expected_signal_e.npy", allow_pickle=False), mean
        )
        sampled = (
            sample_camera(
                mean,
                seed=seed_values,
                background_e=camera["background_e"],
                shot_noise=True,
                **camera_kw,
            )
            if label == "central"
            else np.stack(
                [
                    np.stack(
                        [
                            sample_camera(
                                mean[o, p],
                                seed=seed_values[o][p],
                                background_e=camera["background_e"],
                                shot_noise=True,
                                **camera_kw,
                            )
                            for p in range(mean.shape[1])
                        ]
                    )
                    for o in range(3)
                ]
            )
        )
        np.testing.assert_array_equal(
            np.load(obs / f"calibration_{label}.npy", allow_pickle=False), sampled
        )
    source = np.load(truth / "specimen_source_e.npy", allow_pickle=False)
    # Physical transfer has its independent assertion above. For this procedural
    # composition relation consume the actual represented stored phase values;
    # a legitimate reduction may differ from the observer by ordinary roundoff.
    psi = np.asarray(
        load_json(truth / "generation_summary.json")["specimen_phases_at_specimen_origin_rad"],
        dtype=np.float64,
    )
    for o in range(3):
        means = expected_images(
            source,
            detector_spacing_um_zyx=tuple(geometry["specimen_spacing_um_zyx"]),
            source_refinement_zyx=(2, 2, 2),
            carriers_yx_per_um=q[o : o + 1],
            phases_rad=psi[o : o + 1],
            beam_amplitudes=beam,
            **optics,
        )[0]
        for p in range(5):
            np.testing.assert_array_equal(
                np.load(truth / f"specimen_o{o}_p{p}_expected_signal_e.npy", allow_pickle=False),
                means[p],
            )
            sampled = sample_camera(
                means[p],
                background_e=camera["background_e"],
                seed=value["seeds"]["specimen"][o][p],
                shot_noise=True,
                **camera_kw,
            )
            np.testing.assert_array_equal(
                np.load(obs / f"specimen_o{o}_p{p}.npy", allow_pickle=False), sampled
            )


def independent_camera_moments(groups: list[Any], camera: dict[str, Any]) -> dict[str, Any]:
    keys(camera, FIELDS["ScalarCameraEstimate"])
    with localcontext() as ctx:
        ctx.prec = 1000
        pixels = groups[0][0].size
        assert all(frame.size == pixels for group in groups for frame in group)
        ell = (pixels - 1).bit_length() + max((len(group) - 1).bit_length() for group in groups) + 8
        scale = max(abs(dec(x)) for group in groups for x in group.flat)
        eps, q0 = Decimal(2) ** -52, Decimal(2) ** -1074
        mean_bound = 256 * ell * eps * scale + 16 * ell * q0
        var_bound = 4096 * ell * eps * scale * scale + 128 * ell * q0
        group_means, group_variances = [], []
        for g, array in enumerate(groups):
            means, variances = [], []
            for t, frame in enumerate(array):
                samples = [dec(x) for x in frame.flat]
                mean = sum(samples, Decimal(0)) / len(samples)
                variance = sum(((x - mean) * (x - mean) for x in samples), Decimal(0)) / (
                    len(samples) - 1
                )
                means.append(mean)
                variances.append(variance)
                assert abs(dec(camera["frame_means_counts"][g][t]) - mean) <= mean_bound
                assert abs(dec(camera["frame_variances_counts2"][g][t]) - variance) <= var_bound
                if variance == 0:
                    assert camera["frame_variances_counts2"][g][t] == 0
            group_means.append(sum(means, Decimal(0)) / len(means))
            group_variances.append(sum(variances, Decimal(0)) / len(variances))
            assert abs(dec(camera["means_counts"][g]) - group_means[-1]) <= mean_bound
            assert abs(dec(camera["variances_counts2"][g]) - group_variances[-1]) <= var_bound
            if group_variances[-1] == 0:
                assert camera["variances_counts2"][g] == 0
            frame_means = [dec(v) for v in camera["frame_means_counts"][g]]
            se = (
                sum(
                    (
                        (v - dec(camera["means_counts"][g])) * (v - dec(camera["means_counts"][g]))
                        for v in frame_means
                    ),
                    Decimal(0),
                )
                / (len(frame_means) * (len(frame_means) - 1))
            ).sqrt()
            assert abs(dec(camera["empirical_mean_se_counts"][g]) - se) <= mean_bound
            if scale == 0:
                assert camera["means_counts"][g] == 0 and camera["empirical_mean_se_counts"][g] == 0
                assert all(v == 0 for v in camera["frame_means_counts"][g])
        assert camera["contrast_counts"] == camera["means_counts"][2] - camera["means_counts"][1]
        return {
            "means": group_means,
            "variances": group_variances,
            "A": scale,
            "ell": ell,
            "mean_bound": mean_bound,
            "variance_bound": var_bound,
        }


def test_pipeline_complete47_paired_gauge_actual_specimen_and_freeze(
    pipeline: dict[str, Any],
) -> None:
    from scripts.image_only_bead_calibration import fit_bead_calibration
    from scripts.image_only_specimen_fit import fit_specimen
    from scripts.simulation_inverse_operator import build_kernel_cache, forward

    from simrecon import estimate_scalar_camera

    obs, inference, value = (pipeline[k] for k in ("observations", "inference", "plan"))
    geometry = value["geometry"]
    estimate = check_estimates(inference)
    freeze = check_freeze(inference, complete=True)
    assert estimate["algorithm_settings"] == SETTINGS
    assert estimate["fit_status"] == "completed_finite_fit" and estimate["fit_stage"] == "complete"
    assert estimate["failure_code"] is None
    assert (
        estimate["observation_manifest_sha256"]
        == freeze["observation_manifest_sha256"]
        == sha(obs / "complete.json")
    )
    groups = [
        np.load(obs / f"camera_{name}.npy", allow_pickle=False)
        for name in ("dark", "blank", "flat")
    ]
    independent_camera_moments(groups, estimate["camera_estimate"])
    source_label = f"full_noisy_study:{sha(obs / 'complete.json')}"
    camera = estimate_scalar_camera(
        groups[0], blank_counts=groups[1], flat_counts=groups[2], source=source_label + ":camera"
    )
    assert estimate["camera_estimate"] == public_record(camera)
    bead = fit_bead_calibration(
        np.load(obs / "calibration_central.npy", allow_pickle=False),
        structured_counts=np.load(obs / "calibration_training.npy", allow_pickle=False),
        heldout_counts=np.load(obs / "calibration_heldout.npy", allow_pickle=False),
        camera_estimate=camera,
        origin_um_zyx=tuple(geometry["calibration_origin_um_zyx"]),
        sweep_scales=tuple(SETTINGS["sweep_scales"]),
    )
    assert bead.status == "completed_finite_fit"
    assert estimate["bead_calibration"] == public_record(bead)
    record = estimate["bead_calibration"]
    polls = record["poll_attempts"]
    assert [(a["sweep_index"], a["coordinate_index"], a["sign"]) for a in polls] == list(
        itertools.product(range(len(SETTINGS["sweep_scales"])), range(47), (-1, 1))
    )
    assert (
        record["counts"]["planned_poll_attempts"]
        == record["counts"]["attempted_polls"]
        == 94 * len(SETTINGS["sweep_scales"])
    )
    assert record["counts"]["completed_pairs"] == 47 * len(SETTINGS["sweep_scales"])
    assert record["counts"]["completed_sweeps"] == len(SETTINGS["sweep_scales"])
    assert [s["pupil_order"] for s in record["objective_trace"][-2:]] == [256, 512]
    assert record["unprobed_coordinates"] == [
        e["coordinate_index"]
        for e in record["coordinate_evidence"]
        if e["distinct_parameter_scored_count"] == 0
    ]
    np.testing.assert_array_equal(
        np.load(inference / "bead_heldout_prediction.npy", allow_pickle=False),
        bead.heldout_prediction,
    )
    candidate = record["frozen_candidate"]
    psi = transferred(
        candidate["phases_rad"],
        candidate["carriers_yx_per_um"],
        geometry["calibration_origin_um_zyx"],
        geometry["specimen_origin_um_zyx"],
    )
    np.testing.assert_allclose(
        estimate["transferred_phases_at_specimen_origin_rad"],
        psi,
        rtol=0,
        atol=128 * np.finfo(float).eps,
    )
    actual_psi = np.asarray(estimate["transferred_phases_at_specimen_origin_rad"], dtype=np.float64)
    raw = np.stack(
        [
            np.stack(
                [np.load(obs / f"specimen_o{o}_p{p}.npy", allow_pickle=False) for p in range(5)]
            )
            for o in range(3)
        ]
    )
    specimen = fit_specimen(
        raw,
        camera_estimate=camera,
        carriers_yx_per_um=np.asarray(candidate["carriers_yx_per_um"], dtype=np.float64),
        phases_at_specimen_origin_rad=actual_psi,
        beam_amplitudes=np.asarray(candidate["beam_amplitudes"], dtype=np.float64),
        illumination_source=source_label + ":bead_finite47",
        detector_spacing_um_zyx=tuple(geometry["specimen_spacing_um_zyx"]),
        specimen_origin_um_zyx=tuple(geometry["specimen_origin_um_zyx"]),
        **{
            k: SETTINGS[k]
            for k in ("regularization", "max_iterations", "max_backtracking_trials", "pupil_order")
        },
    )
    assert specimen.status == "completed_finite_fit"
    assert estimate["specimen_fit"] == public_record(specimen)
    source = np.load(inference / "specimen_source_relative.npy", allow_pickle=False)
    np.testing.assert_array_equal(source, specimen.source_relative)
    nz, ny, nx = geometry["specimen_shape_zyx"]
    assert tuple(source.shape) == (nz, 2 * ny, 2 * nx) and source.dtype == np.dtype("<f4")
    assert specimen.detector_spacing_um_zyx == tuple(geometry["specimen_spacing_um_zyx"])
    assert specimen.source_spacing_um_zyx == tuple(
        float(v) if i == 0 else float(v) / 2
        for i, v in enumerate(geometry["specimen_spacing_um_zyx"])
    )
    kernel = build_kernel_cache(
        source_shape_zyx=specimen.source_shape_zyx,
        source_spacing_um_zyx=specimen.source_spacing_um_zyx,
        emission_um=0.525,
        refractive_index=1.515,
        detection_na=1.4,
        pupil_order=SETTINGS["pupil_order"],
    )
    for o in range(3):
        predicted = forward(
            source,
            kernel_cache=kernel,
            carrier_yx_per_um=np.asarray(candidate["carriers_yx_per_um"][o], dtype=np.float64),
            phases_rad=np.asarray(actual_psi[o], dtype=np.float64),
            beam_amplitudes=tuple(float(v) for v in candidate["beam_amplitudes"]),
            excitation_um=0.488,
        )
        for p in range(5):
            np.testing.assert_array_equal(
                np.load(inference / f"prediction_o{o}_p{p}.npy", allow_pickle=False), predicted[p]
            )


def test_metrics_independent_full_arrays_permutations_and_global_gauges(
    pipeline: dict[str, Any],
) -> None:
    obs, inference, truth, value = (
        pipeline[k] for k in ("observations", "inference", "truth", "plan")
    )
    report = check_evaluation(pipeline["evaluation"], obs, inference, truth)
    estimates = check_estimates(inference)
    assert report["status"] in ("evaluated", "evaluated_with_unavailable_metrics")
    assert (
        report["inference_status"] == "completed_finite_fit"
        and report["inference_stage"] == "complete"
    )
    assert report["inference_failure_code"] is None
    camera, true = estimates["camera_estimate"], value["camera"]
    d, b = camera["contrast_counts"], camera["means_counts"][1]
    with localcontext() as ctx:
        ctx.prec = 100
        a = dec(true["gain_counts_per_e"]) / dec(d)
        geometry = value["geometry"]
        src = exact_source(
            value["specimen_catalogue"],
            geometry["specimen_shape_zyx"],
            geometry["specimen_spacing_um_zyx"],
            (2, 2, 2),
        )
        np.testing.assert_array_equal(
            np.load(truth / "specimen_source_e.npy", allow_pickle=False), src
        )
        reference = paired_axial_reference(src, true["gain_counts_per_e"], d)
        fitted = np.load(inference / "specimen_source_relative.npy", allow_pickle=False)
        check_metric(report["source_metrics"], fitted, reference)
        prediction, signal, corrected, observed = [], [], [], []
        means, rms = np.empty((3, 5)), np.empty((3, 5))
        for o, p in itertools.product(range(3), range(5)):
            pred = np.load(inference / f"prediction_o{o}_p{p}.npy", allow_pickle=False)
            mu = np.load(truth / f"specimen_o{o}_p{p}_expected_signal_e.npy", allow_pickle=False)
            raw = np.load(obs / f"specimen_o{o}_p{p}.npy", allow_pickle=False)
            prediction.extend(pred.flat)
            signal.extend(float(a * dec(x)) for x in mu.flat)
            corrected.extend(
                float(
                    (
                        dec(true["offset_counts"])
                        + dec(true["gain_counts_per_e"]) * (dec(x) + dec(true["background_e"]))
                        - dec(b)
                    )
                    / dec(d)
                )
                for x in mu.flat
            )
            residual = [
                dec(x) - (dec(y) - dec(b)) / dec(d)
                for x, y in zip(pred.flat, raw.flat, strict=True)
            ]
            means[o, p] = float(sum(residual) / len(residual))
            rms[o, p] = float((sum((x * x for x in residual), Decimal(0)) / len(residual)).sqrt())
            observed.extend(residual)
        check_metric(report["signal_prediction_metrics"], prediction, signal)
        check_metric(report["corrected_mean_prediction_metrics"], prediction, corrected)
        np.testing.assert_allclose(
            report["observed_residual_mean"],
            means,
            rtol=256 * np.finfo(float).eps,
            atol=256 * np.finfo(float).eps * max(abs(float(x)) for x in observed),
        )
        np.testing.assert_allclose(
            report["observed_residual_rms"], rms, rtol=256 * np.finfo(float).eps, atol=0
        )
        comparison = report["camera_comparison"]
        keys(
            comparison,
            "means_error_counts contrast_error_counts gain_error_counts_per_e unavailable_fields",
        )
        targets = [
            dec(true["offset_counts"]),
            dec(true["offset_counts"]) + dec(true["gain_counts_per_e"]) * dec(true["background_e"]),
            dec(true["offset_counts"])
            + dec(true["gain_counts_per_e"])
            * (dec(true["background_e"]) + dec(true["flat_signal_e"])),
        ]
        for index, target in enumerate(targets):
            close_scalar(
                comparison["means_error_counts"][index],
                float(dec(camera["means_counts"][index]) - target),
                scale=float(abs(target)),
            )
        close_scalar(
            comparison["contrast_error_counts"],
            float(dec(d) - dec(true["gain_counts_per_e"]) * dec(true["flat_signal_e"])),
            scale=d,
        )
        gain = camera["gain_counts_per_e"]
        close_scalar(
            comparison["gain_error_counts_per_e"],
            None if gain is None else gain - true["gain_counts_per_e"],
            scale=true["gain_counts_per_e"],
        )
        candidate = estimates["bead_calibration"]["frozen_candidate"]
        permutations = report["bead_permutation_comparisons"]
        assert [entry["permutation"] for entry in permutations] == [
            list(p) for p in itertools.permutations(range(3))
        ]
        for entry in permutations:
            keys(entry, "permutation center_error_um_zyx brightness_error_relative")
            for i, j in enumerate(entry["permutation"]):
                for axis in range(3):
                    close_scalar(
                        entry["center_error_um_zyx"][i][axis],
                        candidate["centers_um_zyx"][i][axis] - value["bead_catalogue"][j][axis],
                        scale=2.0,
                    )
                close_scalar(
                    entry["brightness_error_relative"][i],
                    float(
                        dec(candidate["brightness_relative"][i])
                        - a * dec(value["bead_catalogue"][j][4])
                    ),
                    scale=float(a * dec(value["bead_catalogue"][j][4])),
                )
        gauges = report["illumination_gauge_comparisons"]
        assert [entry["gauge"] for entry in gauges] == ["as_stored", "global_side_exchange"]
        true_i = value["illumination"]
        true_beam = [dec(x) for x in true_i["beam_amplitudes"]]
        true_norm = sum((x * x for x in true_beam), Decimal(0)).sqrt()
        for entry, sign in zip(gauges, (1, -1), strict=True):
            keys(
                entry,
                (
                    "gauge carrier_error_yx_per_um phase_error_rad wrapped_phase_error_rad "
                    "normalized_beam_error"
                ),
            )
            beam = [dec(x) for x in candidate["beam_amplitudes"]]
            if sign == -1:
                beam = [beam[0], beam[2], beam[1]]
            norm = sum((x * x for x in beam), Decimal(0)).sqrt()
            for i in range(3):
                close_scalar(
                    entry["normalized_beam_error"][i],
                    float(beam[i] / norm - true_beam[i] / true_norm),
                    scale=1.0,
                )
                for j in range(2):
                    close_scalar(
                        entry["carrier_error_yx_per_um"][i][j],
                        sign * candidate["carriers_yx_per_um"][i][j]
                        - true_i["carriers_yx_per_um"][i][j],
                        scale=4.0,
                    )
                for p in range(9):
                    error = (
                        sign * candidate["phases_rad"][i][p]
                        - true_i["phases_at_calibration_origin_rad"][i][p]
                    )
                    close_scalar(entry["phase_error_rad"][i][p], error, scale=16.0)
                    # Complete represented subtraction, then physical-period wrap.
                    with localcontext() as phase_ctx:
                        phase_ctx.prec = 440
                        difference = sign * dec(candidate["phases_rad"][i][p]) - dec(
                            true_i["phases_at_calibration_origin_rad"][i][p]
                        )
                        period = 2 * physical_pi()
                        turns = ((difference + physical_pi()) / period).to_integral_value(
                            rounding="ROUND_FLOOR"
                        )
                        expected = float(difference - turns * period)
                    close_scalar(
                        entry["wrapped_phase_error_rad"][i][p],
                        -math.pi if expected >= math.pi else expected,
                        scale=16.0,
                    )


def test_real_noisy_sealed_unavailable_is_not_completed(tmp_path: Path) -> None:
    # Positive photon flat + strictly positive represented Gaussian read noise.
    # Zero beads and subnormal read noise / ~500 contrast correct to exact zero;
    # the real initializer must report missing positive peaks, not invent a fit.
    value = plan(unavailable=True)
    plan_path, run = tmp_path / "public-zero-beads.json", tmp_path / "generated"
    write_json(plan_path, value)
    expect(cli("generate", "--plan", str(plan_path), "--out", str(run)), 0)
    obs, truth = run / "observations", run / "private_truth"
    before = snapshot(run)
    inference, evaluation = tmp_path / "unavailable", tmp_path / "assessment"
    expect(cli(*infer_args(obs, inference)), 3)
    estimates = check_estimates(inference)
    freeze = check_freeze(inference, complete=False)
    assert estimates["fit_status"] == "unavailable" and estimates["fit_stage"] == "bead"
    assert estimates["camera_estimate"]["contrast_counts"] > 0
    assert estimates["bead_calibration"]["status"] == "initialization_failed"
    assert estimates["specimen_fit"] is None
    assert estimates["transferred_phases_at_specimen_origin_rad"] is None
    assert freeze["stage"] == "bead" and freeze["failure_code"] is None
    assert [x["path"] for x in freeze["files"]] == ["estimates.json"]
    assert all(v == 0 for v in freeze["prediction_call_counts"].values())
    frozen = snapshot(inference)
    expect(cli(*evaluate_args(obs, inference, truth, evaluation)), 3)
    report = check_evaluation(evaluation, obs, inference, truth)
    assert report["status"] == "reported_unavailable"
    assert report["inference_status"] == "unavailable" and report["inference_stage"] == "bead"
    assert report["inference_failure_code"] is None
    assert all(report[field] is None for field in COMPARISONS)
    assert {tuple(sorted(item.items())) for item in report["unavailable_comparisons"]} == {
        tuple(sorted({"field": field, "reason": "inference_unavailable"}.items()))
        for field in COMPARISONS
    }
    assert snapshot(run) == before and snapshot(inference) == frozen
    mass = load_json(truth / "generation_summary.json")["source_mass"]
    for name in ("bead", "specimen"):
        assert mass[name] == {
            "catalogue_total_e": 0.0,
            "stored_total_e": 0.0,
            "difference_e": 0.0,
            "relative_difference": None,
            "unavailable_fields": [{"field": "relative_difference", "reason": "zero_reference"}],
        }


@pytest.mark.parametrize(
    "case,stage,code,camera_present,bead_present",
    [
        ("zero", "camera_normalization", None, True, False),
        ("negative", "camera_normalization", None, True, False),
        ("gain_missing", "bead", None, True, True),
        ("range", "camera", "scalar_camera_calibration_range", False, False),
    ],
)
def test_camera_boundaries_honest_records(
    tmp_path: Path,
    case: str,
    stage: str,
    code: str | None,
    camera_present: bool,
    bead_present: bool,
) -> None:
    obs = observation_bundle(tmp_path / "observations", camera_case=case)
    before = snapshot(obs)
    out = tmp_path / "inference"
    settings = {**SETTINGS, "sweep_scales": [2.0, 0.25, 2.0]}
    expect(cli(*infer_args(obs, out, settings)), 3)
    estimates, freeze = check_estimates(out), check_freeze(out, complete=False)
    assert estimates["fit_stage"] == freeze["stage"] == stage
    assert estimates["failure_code"] == freeze["failure_code"] == code
    assert (estimates["camera_estimate"] is not None) == camera_present
    assert (estimates["bead_calibration"] is not None) == bead_present
    assert estimates["specimen_fit"] is None
    assert estimates["algorithm_settings"] == settings
    assert all(count == 0 for count in freeze["prediction_call_counts"].values())
    if case == "gain_missing":
        assert estimates["camera_estimate"]["gain_counts_per_e"] is None
        assert estimates["camera_estimate"]["contrast_counts"] == 1.0
        assert estimates["bead_calibration"]["status"] == "initialization_failed"
        assert estimates["bead_calibration"]["sweep_scales"] == [2.0, 0.25, 2.0]
    assert snapshot(obs) == before


@pytest.mark.parametrize("source_free_parent", [False, True])
@pytest.mark.parametrize("nested", [False, True])
def test_cli_child_diagnostics_without_parent_preconditions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_free_parent: bool, nested: bool
) -> None:
    """Qualify harness plumbing, without supplying a product decision or result."""
    site = str(Path(__file__).resolve().parents[1] / "scripts/source_free_sitecustomize")
    inherited_path = str(tmp_path / "inherited-import-path")
    monkeypatch.setenv(
        "PYTHONPATH", site + os.pathsep + inherited_path if source_free_parent else inherited_path
    )
    inherited_plugin = "h1_inherited_plugin"
    monkeypatch.setenv(
        "PYTEST_PLUGINS",
        "pytest_plugin," + inherited_plugin if source_free_parent else inherited_plugin,
    )
    before = os.environ.copy()
    env = source_free_environment()
    assert os.environ == before
    assert all(
        env[key] == value
        for key, value in before.items()
        if key not in ("PYTHONPATH", "PYTEST_PLUGINS")
    )
    assert env["PYTHONPATH"].split(os.pathsep) == [site, inherited_path]
    assert env["PYTEST_PLUGINS"].split(",") == ["pytest_plugin", inherited_plugin]
    filename = str(Path(__file__).resolve())
    failure = (
        "try:\n raise ValueError('h1 cause')\n"
        "except ValueError as error:\n raise RuntimeError('h1 outer') from error\n"
    )
    code = (
        "import sys, warnings\n"
        "assert sys.excepthook.__module__ == 'sitecustomize'\n"
        "assert warnings.formatwarning.__module__ == 'sitecustomize'\n"
        f"warnings.warn_explicit('h1 warning', UserWarning, {filename!r}, 1)\n"
        f"exec(compile({failure!r}, {filename!r}, 'exec'))\n"
    )
    if nested:
        code = (
            "import subprocess, sys\n"
            f"result = subprocess.run([sys.executable, '-c', {code!r}], check=False)\n"
            "raise SystemExit(result.returncode)\n"
        )
    argv = [sys.executable, "-c", code]
    receipt: dict[str, Any] = {
        "argv": argv,
        "timeout_s": 30,
        "diagnostic_qualification": True,
        "source_free_parent": source_free_parent,
        "nested": nested,
    }
    COMMAND_LEDGER.append(receipt)
    result = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=30, check=False)
    receipt.update(
        status=result.returncode, stdout=result.stdout, stderr=result.stderr, process_closed=True
    )
    assert result.returncode == 1 and result.stdout == ""
    assert f"{filename}:1: UserWarning: h1 warning" in result.stderr
    assert f'File "{filename}", line 2' in result.stderr
    assert f'File "{filename}", line 4' in result.stderr
    assert "ValueError: h1 cause" in result.stderr
    assert "direct cause of the following exception" in result.stderr
    assert "RuntimeError: h1 outer" in result.stderr
    assert "Public CLI proof for full noisy study" not in result.stderr
    assert "evidence, not product-red" not in result.stderr


@pytest.mark.parametrize("command", ["generate", "infer", "evaluate", "root"])
def test_cli_help(command: str) -> None:
    expect(cli(*([] if command == "root" else [command]), "--help"), 0)


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("all",),
        ("resume",),
        ("cleanup",),
        ("generate",),
        ("infer",),
        ("evaluate",),
        ("generate", "--plan"),
        ("infer", "--sweep-scales"),
        ("evaluate", "--private-truth"),
        ("generate", "--plan", "x", "--out", "y", "--plan", "z"),
        ("generate", "--plan", "x", "--out", "y", "--out", "z"),
        ("generate", "--plan", "x", "--out", "y", "--overwrite"),
        ("generate", "--plan", "x", "--out", "y", "extra"),
        ("generate", "--plan", "x", "--out", "y", "--plugin", "x"),
    ],
)
def test_cli_grammar(args: tuple[str, ...]) -> None:
    expect(in_process_cli(*args), 2)


def set_at(value: Any, path: tuple[Any, ...], replacement: Any) -> None:
    for part in path[:-1]:
        value = value[part]
    value[path[-1]] = replacement


PLAN_BAD = [
    (("format_version",), "full_noisy_study_plan_v1.2"),
    (("geometry", "camera_shape_yx"), [1, 1]),
    (("geometry", "camera_shape_yx"), [True, 8]),
    (("geometry", "camera_shape_yx"), [8.0, 8]),
    (("geometry", "camera_shape_yx"), [8]),
    (("geometry", "calibration_shape_zyx"), [0, 2, 24]),
    (("geometry", "calibration_shape_zyx"), [1, 1, 24]),
    (("geometry", "specimen_shape_zyx"), [1, -1, 2]),
    (("geometry", "calibration_spacing_um_zyx"), [0.125, 0.081, 0.080]),
    (("geometry", "specimen_spacing_um_zyx"), [0.0, 0.08, 0.08]),
    (("geometry", "specimen_origin_um_zyx"), [0.0, 1.0]),
    (("geometry", "specimen_origin_um_zyx"), [0.0, False, 0.0]),
    (("camera", "background_e"), -1.0),
    (("camera", "read_noise_e"), 0.0),
    (("camera", "gain_counts_per_e"), -1.0),
    (("camera", "flat_signal_e"), 0.0),
    (("camera", "offset_counts"), True),
    (("camera", "offset_counts"), "0"),
    (("camera", "background_e"), None),
    (("camera", "offset_counts"), 10**400),
    (("generator_pupil_order",), 0),
    (("generator_pupil_order",), True),
    (("generator_pupil_order",), 2.0),
    (("illumination", "carriers_yx_per_um"), [[0.0, 0.0]]),
    (("illumination", "carriers_yx_per_um", 0), [4.0, 0.0]),
    (("illumination", "phases_at_calibration_origin_rad", 1), [0.0] * 5),
    (("illumination", "beam_amplitudes"), [0.0, 0.0, 0.0]),
    (("illumination", "beam_amplitudes"), [1.0, -1.0, 0.0]),
    (("bead_catalogue",), []),
    (("bead_catalogue", 0, 3), 0.051),
    (("bead_catalogue", 0, 0), 0.01),
    (("bead_catalogue", 0, 4), -1.0),
    (("bead_catalogue", 1), [0.0625, 0.08, 0.16, 0.05, 1.0]),
    (("specimen_catalogue",), [0.0, 0.0, 0.0, 0.05, 0.0]),
    (("specimen_catalogue", 0, 3), 0.0),
    (("specimen_catalogue", 0, 2), 2.0),
    (("seeds", "camera_dark"), [1] * 8),
    (("seeds", "camera_dark", 0), -1),
    (("seeds", "camera_dark", 0), True),
    (("seeds", "camera_dark", 0), 1.0),
    (("seeds", "calibration_training"), [[1] * 8] * 3),
    (("seeds", "calibration_heldout"), [[1] * 5] * 2),
    (("seeds", "specimen"), [[1] * 9] * 3),
]


@pytest.mark.parametrize("path,replacement", PLAN_BAD)
def test_plan_rejections_before_claim(
    tmp_path: Path, path: tuple[Any, ...], replacement: Any
) -> None:
    value = plan()
    set_at(value, path, replacement)
    input_path, out = tmp_path / "bad.json", tmp_path / "out"
    write_json(input_path, value)
    before = snapshot(tmp_path)
    expect(in_process_cli("generate", "--plan", str(input_path), "--out", str(out)), 2)
    assert snapshot(tmp_path) == before and not out.exists()


@pytest.mark.parametrize("level", [(), ("geometry",), ("camera",), ("illumination",), ("seeds",)])
@pytest.mark.parametrize("defect", ["unknown", "missing", "duplicate"])
def test_plan_exact_keys_at_every_object(
    tmp_path: Path, level: tuple[str, ...], defect: str
) -> None:
    value = plan()
    target = value
    for name in level:
        target = target[name]
    first = next(iter(target))
    if defect == "unknown":
        target["unapproved"] = 1
    elif defect == "missing":
        del target[first]
    raw = encoded(value)
    if defect == "duplicate":
        token = json.dumps(first).encode() + b":"
        raw = raw.replace(token, token + b"null," + token, 1)
    input_path, out = tmp_path / "bad.json", tmp_path / "out"
    input_path.write_bytes(raw)
    expect(in_process_cli("generate", "--plan", str(input_path), "--out", str(out)), 2)
    assert input_path.read_bytes() == raw and not out.exists()


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b"null",
        b"{} {}",
        b"{",
        b"\xff",
        *[
            encoded(plan()).replace(b'"background_e":0.1', b'"background_e":' + token)
            for token in (b"NaN", b"Infinity", b"-Infinity", b"1e9999")
        ],
    ],
)
def test_strict_plan_json(tmp_path: Path, raw: bytes) -> None:
    input_path, out = tmp_path / "bad.json", tmp_path / "out"
    input_path.write_bytes(raw)
    expect(in_process_cli("generate", "--plan", str(input_path), "--out", str(out)), 2)
    assert input_path.read_bytes() == raw and not out.exists()


@pytest.mark.parametrize(
    "flag,text",
    [
        ("--sweep-scales", "[]"),
        ("--sweep-scales", "[0]"),
        ("--sweep-scales", "[-1]"),
        ("--sweep-scales", "[true]"),
        ("--sweep-scales", "[null]"),
        ("--sweep-scales", "[NaN]"),
        ("--sweep-scales", "[1e999]"),
        ("--sweep-scales", "1"),
        ("--sweep-scales", "[1] trailing"),
        ("--regularization", "0"),
        ("--regularization", "nan"),
        ("--regularization", "inf"),
        ("--regularization", "1e9999"),
        ("--regularization", "-1"),
        ("--max-iterations", "0"),
        ("--max-iterations", "1.0"),
        ("--max-backtracking-trials", "-1"),
        ("--pupil-order", "true"),
        ("--pupil-order", "0"),
    ],
)
def test_algorithm_settings_syntax(tmp_path: Path, flag: str, text: str) -> None:
    # Invalid settings must be diagnosed without needing a scientific input.
    args = infer_args(tmp_path / "not-present", tmp_path / "out")
    args[args.index(flag) + 1] = text
    expect(in_process_cli(*args), 2)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("command", ["infer", "evaluate"])
def test_each_required_flag_duplicate_unknown_and_positionals(tmp_path: Path, command: str) -> None:
    args = (
        infer_args(tmp_path / "obs", tmp_path / "out")
        if command == "infer"
        else evaluate_args(tmp_path / "obs", tmp_path / "inf", tmp_path / "truth", tmp_path / "out")
    )
    for index in range(1, len(args), 2):
        expect(in_process_cli(*(args[:index] + args[index + 2 :])), 2)
        expect(in_process_cli(*(args + args[index : index + 2])), 2)
    for extra in (["extra"], ["--unknown", "1"], ["--overwrite"], ["--plan", "secret"]):
        expect(in_process_cli(*(args + extra)), 2)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("case", ["huge_phase", "overflowing_origin_difference", "endpoint"])
def test_phase_cases_physical_period_and_safe_complete_expression(
    tmp_path: Path, case: str
) -> None:
    value = plan(unavailable=True)
    geometry, illumination = value["geometry"], value["illumination"]
    illumination["beam_amplitudes"] = [1.0, 0.0, 0.0]
    if case == "huge_phase":
        illumination["phases_at_calibration_origin_rad"] = [
            [1e300 + o for _ in range(9)] for o in range(3)
        ]
        illumination["carriers_yx_per_um"] = [[0.0, 0.0]] * 3
    elif case == "overflowing_origin_difference":
        geometry["calibration_origin_um_zyx"] = [0.0, -1e308, 1e308]
        geometry["specimen_origin_um_zyx"] = [0.0, 1e308, -1e308]
        illumination["carriers_yx_per_um"] = [
            [2.0**-1000, 0.0],
            [0.0, 2.0**-1000],
            [2.0**-1001, 2.0**-1002],
        ]
    else:
        illumination["phases_at_calibration_origin_rad"] = [
            [math.pi, -math.pi, 0.0, -0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
        ] * 3
        illumination["carriers_yx_per_um"] = [[0.0, 0.0]] * 3
    input_path, out = tmp_path / "plan.json", tmp_path / "out"
    write_json(input_path, value)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 0)
    actual = load_json(out / "private_truth/generation_summary.json")[
        "specimen_phases_at_specimen_origin_rad"
    ]
    expected = transferred(
        illumination["phases_at_calibration_origin_rad"],
        illumination["carriers_yx_per_um"],
        geometry["calibration_origin_um_zyx"],
        geometry["specimen_origin_um_zyx"],
    )
    # These cases reduce at most ~2e7 exact turns or one huge phase. Error is
    # measured on the reduced result; a huge input-scaled tolerance is vacuous.
    allowance = 512 * np.finfo(float).eps
    if case == "overflowing_origin_difference":
        # Allow ordinary reduction roundoff on this finite ~2e7-turn control.
        # This still rejects lost/overflowing coordinates by a wide margin.
        with localcontext() as ctx:
            ctx.prec = 440
            turns = max(
                abs(
                    sum(
                        (
                            dec(q[j])
                            * (
                                dec(geometry["specimen_origin_um_zyx"][j + 1])
                                - dec(geometry["calibration_origin_um_zyx"][j + 1])
                            )
                            for j in range(2)
                        ),
                        Decimal(0),
                    )
                )
                for q in illumination["carriers_yx_per_um"]
            )
        allowance = 128 * np.finfo(float).eps * 2 * math.pi * max(1.0, float(turns))
    np.testing.assert_allclose(actual, expected, rtol=0, atol=allowance)
    assert np.all(np.asarray(actual) >= -math.pi) and np.all(np.asarray(actual) < math.pi)
    if case == "endpoint":
        assert actual[0][0] == -math.pi


def test_empty_catalogue_and_large_integer_seed_are_legal(tmp_path: Path) -> None:
    value = plan(unavailable=True, empty=True)
    value["seeds"]["camera_dark"][0] = 10**300
    # Integer real fields and zero/negative carrier/phase/origin are legal.
    value["camera"]["offset_counts"] = -10
    value["illumination"]["beam_amplitudes"] = [0, 2, 0]
    value["illumination"]["carriers_yx_per_um"] = [[0, 0]] * 3
    input_path, out = tmp_path / "plan.json", tmp_path / "out"
    write_json(input_path, value)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 0)
    assert np.all(np.load(out / "private_truth/specimen_source_e.npy", allow_pickle=False) == 0)
    assert load_json(out / "private_truth/plan.json")["specimen_catalogue"] == []


@pytest.mark.parametrize("brightness", [0.0, 1.0])
def test_positive_unoccupied_source_is_range_not_domain_or_fake_success(
    tmp_path: Path, brightness: float
) -> None:
    value = plan(unavailable=True)
    # Radius1nm at the box corner's contained neighborhood misses every 2x site.
    value["specimen_catalogue"] = [[0.002, 0.002, 0.002, 0.001, brightness]]
    input_path, out = tmp_path / "plan.json", tmp_path / "out"
    write_json(input_path, value)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 6 if brightness else 0)
    if brightness:
        assert not (out / "generation.complete.json").exists()
        assert not (out / "observations/complete.json").exists()
    before = snapshot(out)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 5)
    assert snapshot(out) == before


@pytest.fixture(scope="module")
def sealed(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("full-noisy-A-public-sealed")
    obs = observation_bundle(root / "observations")
    inference = root / "inference"
    expect(cli(*infer_args(obs, inference)), 3)
    check_freeze(inference, complete=False)
    return {"root": root, "observations": obs, "inference": inference}


@pytest.mark.parametrize("version", [(1, 0), (2, 0), (3, 0)])
def test_binary_protocol_ordinary_versions_and_noncanonical_json(
    tmp_path: Path, version: tuple[int, int]
) -> None:
    obs = observation_bundle(tmp_path / "obs", version=version, camera_case="negative")
    marker = obs / "complete.json"
    marker.write_text(json.dumps(load_json(marker), indent=3), encoding="utf-8")
    (obs / "not-an-input.json").write_bytes(b"invalid and unrelated")
    before = snapshot(obs)
    out = tmp_path / "out"
    expect(cli(*infer_args(obs, out)), 3)
    assert check_estimates(out)["camera_estimate"]["contrast_counts"] == -1.0
    assert snapshot(obs) == before


@pytest.mark.parametrize(
    "defect",
    [
        "missing_manifest",
        "partial_manifest",
        "wrong_version",
        "extra_key",
        "missing_key",
        "geometry_key",
        "geometry_missing",
        "geometry_bool",
        "geometry_shape",
        "spacing",
        "model_key",
        "model_missing",
        "model_false",
        "model_kind",
        "nominal_commands",
        "descriptor_key",
        "descriptor_missing",
        "descriptor_bool_size",
        "descriptor_shape_kind",
        "descriptor_negative_size",
        "descriptor_hash_upper",
        "descriptor_hash_wrong",
        "absolute_path",
        "parent_path",
        "alternate_separator",
        "extra_file",
        "missing_file",
        "file_order",
        "duplicate_file",
        "json_duplicate_root",
        "json_duplicate_nested",
        "nan_geometry",
        "overflow_geometry",
        "missing_payload",
        "wrong_size",
    ],
)
def test_observation_protocol_rejections(tmp_path: Path, defect: str) -> None:
    obs = observation_bundle(tmp_path / "obs")
    marker = obs / "complete.json"
    value = load_json(marker)
    if defect == "missing_manifest":
        marker.rename(obs / "not_complete.json")
    elif defect == "partial_manifest":
        marker.write_bytes(b'{"format_version":')
    else:
        if defect == "wrong_version":
            value["format_version"] = "full_noisy_study_observations_v2"
        elif defect == "extra_key":
            value["truth"] = "no"
        elif defect == "missing_key":
            del value["files"]
        elif defect == "geometry_key":
            value["geometry"]["truth"] = 0
        elif defect == "geometry_missing":
            del value["geometry"]["specimen_origin_um_zyx"]
        elif defect == "geometry_bool":
            value["geometry"]["camera_shape_yx"][0] = True
        elif defect == "geometry_shape":
            value["geometry"]["specimen_shape_zyx"] = [1, 2]
        elif defect == "spacing":
            value["geometry"]["calibration_spacing_um_zyx"][0] = 0.1
        elif defect == "model_key":
            value["acquisition_model"]["seed"] = 0
        elif defect == "model_missing":
            del value["acquisition_model"]["pupil"]
        elif defect == "model_false":
            value["acquisition_model"]["shot_noise"] = False
        elif defect == "model_kind":
            value["acquisition_model"]["stationary_camera"] = 1
        elif defect == "nominal_commands":
            value["nominal_phase_commands_rad"][0] = 0.01
        elif defect == "descriptor_key":
            value["files"][0]["seed"] = 0
        elif defect == "descriptor_missing":
            del value["files"][0]["sha256"]
        elif defect == "descriptor_bool_size":
            value["files"][0]["size_bytes"] = True
        elif defect == "descriptor_shape_kind":
            value["files"][0]["shape"][0] = 8.0
        elif defect == "descriptor_negative_size":
            value["files"][0]["size_bytes"] = -1
        elif defect == "descriptor_hash_upper":
            value["files"][0]["sha256"] = value["files"][0]["sha256"].upper()
        elif defect == "descriptor_hash_wrong":
            value["files"][0]["sha256"] = "0" * 64
        elif defect == "absolute_path":
            value["files"][0]["path"] = str(obs / "camera_dark.npy")
        elif defect == "parent_path":
            value["files"][0]["path"] = "../obs/camera_dark.npy"
        elif defect == "alternate_separator":
            value["files"][0]["path"] = "obs\\camera_dark.npy"
        elif defect == "extra_file":
            value["files"].append(value["files"][0])
        elif defect == "missing_file":
            value["files"].pop()
        elif defect == "file_order":
            value["files"][0], value["files"][1] = value["files"][1], value["files"][0]
        elif defect == "duplicate_file":
            value["files"][1] = value["files"][0]
        elif defect == "missing_payload":
            (obs / RAW_NAMES[-1]).rename(obs / "moved.npy")
        elif defect == "wrong_size":
            value["files"][0]["size_bytes"] += 1
        raw = encoded(value)
        if defect == "json_duplicate_root":
            raw = raw.replace(b'"files":', b'"files":[],"files":', 1)
        elif defect == "json_duplicate_nested":
            raw = raw.replace(b'"shot_noise":', b'"shot_noise":false,"shot_noise":', 1)
        elif defect == "nan_geometry":
            raw = raw.replace(b'"specimen_origin_um_zyx":[0.5', b'"specimen_origin_um_zyx":[NaN')
        elif defect == "overflow_geometry":
            raw = raw.replace(b'"specimen_origin_um_zyx":[0.5', b'"specimen_origin_um_zyx":[1e9999')
        marker.write_bytes(raw)
    before = snapshot(obs)
    out = tmp_path / "out"
    expect(in_process_cli(*infer_args(obs, out)), 4)
    assert snapshot(obs) == before and not out.exists()


@pytest.mark.parametrize(
    "defect",
    [
        "big_endian",
        "float32",
        "fortran",
        "nan",
        "infinity",
        "wrong_shape",
        "trailing",
        "truncated",
        "header_only",
        "object_header",
        "signed_counts",
    ],
)
def test_binary_protocol_payload_validation(tmp_path: Path, defect: str) -> None:
    obs = observation_bundle(tmp_path / "obs")
    shape = tuple(load_json(obs / "complete.json")["geometry"]["specimen_shape_zyx"])
    path = obs / RAW_NAMES[-1]
    old = path.read_bytes()
    if defect in ("trailing", "truncated", "header_only"):
        path.write_bytes(
            old + old if defect == "trailing" else old[:-1] if defect == "truncated" else old[:128]
        )
        manifest = load_json(obs / "complete.json")
        manifest["files"][-1].update(size_bytes=path.stat().st_size, sha256=sha(path))
        write_json(obs / "complete.json", manifest)
    elif defect == "signed_counts":
        # Raw signed counts are legal: this example must NOT reject.
        values = np.full(shape, -20.0, dtype="<f8")
        path.rename(obs / "original-public-payload.npy")
        save_npy(path, values)
        reseal(obs)
    elif defect == "object_header":
        with path.open("wb") as stream:
            np.lib.format.write_array_header_1_0(
                stream, {"descr": "|O", "fortran_order": False, "shape": shape}
            )
            stream.write(b"\x00" * 32)  # no pickle or executable object payload
        manifest = load_json(obs / "complete.json")
        manifest["files"][-1].update(size_bytes=path.stat().st_size, sha256=sha(path), dtype="|O")
        write_json(obs / "complete.json", manifest)
    else:
        values = np.zeros(
            shape,
            dtype=">f8" if defect == "big_endian" else "<f4" if defect == "float32" else "<f8",
        )
        if defect == "fortran":
            values = np.asfortranarray(values)
        elif defect == "nan":
            values.flat[0] = np.nan
        elif defect == "infinity":
            values.flat[0] = np.inf
        elif defect == "wrong_shape":
            values = np.zeros((1, 2, 1), dtype="<f8")
        path.rename(obs / "original-public-payload.npy")
        if defect == "fortran":
            save_declared_order_npy(path, values, (1, 0), fortran=True)
        else:
            save_npy(path, values)
        reseal(obs)
    before = snapshot(obs)
    out = tmp_path / "out"
    expect(in_process_cli(*infer_args(obs, out)), 3 if defect == "signed_counts" else 4)
    assert snapshot(obs) == before
    if defect != "signed_counts":
        assert not out.exists()


@pytest.mark.parametrize("command", ["generate", "infer", "evaluate"])
@pytest.mark.parametrize(
    "entry", ["directory", "nonempty_directory", "file", "live_symlink", "dangling_symlink"]
)
def test_output_ownership_preserves_every_existing_root(
    tmp_path: Path, command: str, entry: str, pipeline: dict[str, Any]
) -> None:
    out, referent = tmp_path / "existing", tmp_path / "referent"
    referent.write_bytes(b"original referent bytes\x00\xff")
    if entry in ("directory", "nonempty_directory"):
        out.mkdir()
        if entry == "nonempty_directory":
            (out / "original").write_bytes(b"keep nested data")
    elif entry == "file":
        out.write_bytes(b"original root bytes\x00\xff")
    else:
        out.symlink_to(referent if entry == "live_symlink" else tmp_path / "absent")
    before = snapshot(tmp_path)
    if command == "generate":
        args = ["generate", "--plan", str(pipeline["plan_path"]), "--out", str(out)]
    elif command == "infer":
        args = infer_args(pipeline["observations"], out)
    else:
        args = evaluate_args(
            pipeline["observations"], pipeline["inference"], pipeline["truth"], out
        )
    expect(cli(*args), 5)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("command", ["generate", "infer", "evaluate"])
def test_missing_output_parent_never_created(
    tmp_path: Path, command: str, pipeline: dict[str, Any]
) -> None:
    out = tmp_path / "missing" / "child"
    before = snapshot(tmp_path)
    if command == "generate":
        args = ["generate", "--plan", str(pipeline["plan_path"]), "--out", str(out)]
    elif command == "infer":
        args = infer_args(pipeline["observations"], out)
    else:
        args = evaluate_args(
            pipeline["observations"], pipeline["inference"], pipeline["truth"], out
        )
    expect(cli(*args), 5)
    assert snapshot(tmp_path) == before


def test_partial_io_retained_unsealed_and_retry_cannot_repair(tmp_path: Path) -> None:
    input_path, out = tmp_path / "plan.json", tmp_path / "partial"
    value = plan()
    # A legal larger source makes the real NPY write exceed the cap, while
    # leaving room for the installed subprocess instrumentation's native data.
    # The cap is an I/O example, not a scientific or coverage acceptance limit.
    value["geometry"]["calibration_shape_zyx"] = [1, 2, 256]
    file_limit_bytes = 1 << 20
    source_payload_bytes = math.prod(8 * n for n in [1, 2, 256]) * 8
    assert source_payload_bytes > file_limit_bytes
    write_json(input_path, value)
    original = input_path.read_bytes()

    def bounded_file_write() -> None:
        # Real OS file-size failure, no runtime replacement or test-only seam.
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit_bytes, file_limit_bytes))

    expect(
        cli(
            "generate", "--plan", str(input_path), "--out", str(out), preexec_fn=bounded_file_write
        ),
        5,
    )
    assert out.is_dir() and input_path.read_bytes() == original
    assert not (out / "generation.complete.json").exists()
    assert not (out / "observations/complete.json").exists()
    assert not (out / "private_truth/complete.json").exists()
    partial_files = [p for p in out.rglob("*") if p.is_file()]
    assert partial_files and all(p.stat().st_size <= file_limit_bytes for p in partial_files)
    partial_source = out / "private_truth/bead_source_e.npy"
    assert partial_source.is_file() and 0 < partial_source.stat().st_size <= file_limit_bytes
    assert partial_source.stat().st_size < source_payload_bytes
    before = snapshot(out)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 5)
    assert snapshot(out) == before


@pytest.mark.parametrize("link", [False, True])
def test_completion_leaf_created_exclusively_at_real_io_boundary(
    tmp_path: Path, link: bool
) -> None:
    input_path, out = tmp_path / "plan.json", tmp_path / "run"
    write_json(input_path, plan())
    referent = tmp_path / "original-referent"
    referent.write_bytes(b"never truncate or replace this completion entry\n")
    argv = [
        sys.executable,
        "-m",
        "scripts.full_noisy_study",
        "generate",
        "--plan",
        str(input_path),
        "--out",
        str(out),
    ]
    env = source_free_environment()
    receipt: dict[str, Any] = {
        "argv": argv,
        "timeout_s": 300,
        "fault": "external completion leaf conflict",
        "PYTHONPATH": env["PYTHONPATH"],
    }
    COMMAND_LEDGER.append(receipt)
    process = subprocess.Popen(
        argv, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stopped = False
    try:
        deadline = time.monotonic() + 300
        while not out.is_dir() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.001)
        assert out.is_dir() and process.poll() is None, (
            "No live generation window; proof incomplete"
        )
        os.kill(process.pid, signal.SIGSTOP)
        stopped = True
        _, status = os.waitpid(process.pid, os.WUNTRACED)
        assert os.WIFSTOPPED(status), "Process exited before external fault; proof incomplete"
        leaf = out / "generation.complete.json"
        assert not leaf.exists() and not leaf.is_symlink(), (
            "Completion already published; proof incomplete"
        )
        if link:
            leaf.symlink_to(referent)
        else:
            with leaf.open("xb") as stream:
                stream.write(referent.read_bytes())
        original = snapshot(leaf)
        os.kill(process.pid, signal.SIGCONT)
        stopped = False
        stdout, stderr = process.communicate(timeout=300)
        receipt.update(status=process.returncode, stdout=stdout, stderr=stderr, output=str(out))
        assert process.returncode == 5, (process.returncode, stdout, stderr)
        assert snapshot(leaf) == original
        assert referent.read_bytes() == b"never truncate or replace this completion entry\n"
        retained = snapshot(out)
        expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 5)
        assert snapshot(out) == retained
    finally:
        if process.poll() is None:
            if stopped:
                os.kill(process.pid, signal.SIGCONT)
            process.kill()
        final_stdout, final_stderr = process.communicate(timeout=10)
        receipt.setdefault("status", process.returncode)
        receipt.setdefault("stdout", final_stdout)
        receipt.setdefault("stderr", final_stderr)
        receipt["process_closed"] = True


def test_detached_inference_ignores_private_decoys_and_path_names(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    first, second = tmp_path / "first", tmp_path / "seed-truth-gain-999999"
    first.mkdir()
    second.mkdir()
    for root in (first, second):
        shutil.copytree(pipeline["observations"], root / "observations")
    # No root generation marker. Parent/sibling truth/plan/means are invalid
    # decoys, not inputs. All actual observation bytes/settings stay identical.
    for name in ("generation.complete.json", "plan.json", "generation_summary.json"):
        (second / name).write_bytes(b"not JSON; forbidden inference input")
    (second / "private_truth").mkdir()
    (second / "private_truth/complete.json").write_bytes(b"invalid private decoy")
    before_first, before_second = snapshot(first), snapshot(second)
    out_a, out_b = tmp_path / "fit-a", tmp_path / "fit-b"
    expect(cli(*infer_args(first / "observations", out_a)), 0)
    expect(cli(*infer_args(second / "observations", out_b)), 0)
    assert snapshot(out_a) == snapshot(out_b)
    assert snapshot(first) == before_first and snapshot(second) == before_second
    assert snapshot(out_a) == snapshot(pipeline["inference"])


def test_heldout_independence_preserves_every_training_decision(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    obs = tmp_path / "observations"
    shutil.copytree(pipeline["observations"], obs)
    path = obs / "calibration_heldout.npy"
    raw = np.load(path, allow_pickle=False)
    with path.open("wb") as stream:
        np.save(stream, raw + 10.0, allow_pickle=False)
    reseal(obs)
    out = tmp_path / "inference"
    expect(cli(*infer_args(obs, out)), 0)
    original, changed = check_estimates(pipeline["inference"]), check_estimates(out)
    a, b = copy.deepcopy(original["bead_calibration"]), copy.deepcopy(changed["bead_calibration"])
    # Source identities necessarily change with manifest bytes; compare every
    # actual training field while permitting only heldout summaries to change.
    for value in (a, b):
        for name in ("camera_source", "heldout_residual_mean", "heldout_residual_rms"):
            value.pop(name)
    assert a == b
    assert (
        original["bead_calibration"]["heldout_residual_mean"]
        != changed["bead_calibration"]["heldout_residual_mean"]
    )
    for name in ("bead_heldout_prediction.npy", "specimen_source_relative.npy", *PRED_NAMES):
        assert (out / name).read_bytes() == (pipeline["inference"] / name).read_bytes()


@pytest.mark.parametrize(
    "defect",
    [
        "missing_freeze",
        "partial_freeze",
        "freeze_extra",
        "freeze_missing",
        "freeze_version",
        "freeze_identity",
        "freeze_completed_without_predictions",
        "freeze_counts",
        "freeze_unknown_path",
        "freeze_duplicate",
        "estimates_extra",
        "estimates_missing",
        "estimates_version",
        "estimates_identity",
        "settings_extra",
        "settings_invalid",
        "runtime_extra",
        "runtime_hash",
        "camera_extra",
        "camera_missing",
        "camera_shape",
        "camera_nonfinite",
        "camera_bool",
        "payload_tampered",
        "payload_trailing",
        "payload_missing",
    ],
)
def test_evaluation_public_validation_before_private_read(
    tmp_path: Path, sealed: dict[str, Path], defect: str
) -> None:
    inference = tmp_path / "inference"
    shutil.copytree(sealed["inference"], inference)
    marker, estimates_path = inference / "freeze.json", inference / "estimates.json"
    freeze, estimates = load_json(marker), load_json(estimates_path)
    if defect == "missing_freeze":
        marker.rename(inference / "not-freeze.json")
    elif defect == "partial_freeze":
        marker.write_bytes(b"{")
    else:
        if defect == "freeze_extra":
            freeze["extra"] = 0
        elif defect == "freeze_missing":
            del freeze["files"]
        elif defect == "freeze_version":
            freeze["format_version"] = "v2"
        elif defect == "freeze_identity":
            freeze["observation_manifest_sha256"] = "0" * 64
        elif defect == "freeze_completed_without_predictions":
            freeze["status"] = "completed_finite_fit"
        elif defect == "freeze_counts":
            freeze["prediction_call_counts"]["forward_completed"] = 3
        elif defect == "freeze_unknown_path":
            freeze["files"][0]["path"] = "../estimates.json"
        elif defect == "freeze_duplicate":
            freeze["files"].append(freeze["files"][0])
        elif defect == "estimates_extra":
            estimates["true_gain"] = 2.0
        elif defect == "estimates_missing":
            del estimates["camera_estimate"]
        elif defect == "estimates_version":
            estimates["format_version"] = "v2"
        elif defect == "estimates_identity":
            estimates["observation_manifest_sha256"] = "0" * 64
        elif defect == "settings_extra":
            estimates["algorithm_settings"]["unknown"] = 1
        elif defect == "settings_invalid":
            estimates["algorithm_settings"]["regularization"] = 0
        elif defect == "runtime_extra":
            estimates["runtime"]["unknown"] = 1
        elif defect == "runtime_hash":
            estimates["runtime"]["driver_sha256"] = "not-a-hash"
        elif defect == "camera_extra":
            estimates["camera_estimate"]["truth"] = 0
        elif defect == "camera_missing":
            del estimates["camera_estimate"]["variances_counts2"]
        elif defect == "camera_shape":
            estimates["camera_estimate"]["means_counts"] = [0.0, 0.0]
        elif defect == "camera_bool":
            estimates["camera_estimate"]["contrast_counts"] = True
        if defect.startswith(("estimates_", "settings_", "runtime_", "camera_")):
            write_json(estimates_path, estimates)
            if defect == "camera_nonfinite":
                estimates_path.write_bytes(
                    estimates_path.read_bytes().replace(
                        b'"contrast_counts":0.0', b'"contrast_counts":NaN'
                    )
                )
            freeze["files"][0] = descriptor(inference, "estimates.json")
        if defect == "payload_tampered":
            estimates_path.write_bytes(estimates_path.read_bytes() + b" ")
        elif defect == "payload_trailing":
            estimates_path.write_bytes(estimates_path.read_bytes() + b" {}")
            freeze["files"][0] = descriptor(inference, "estimates.json")
        elif defect == "payload_missing":
            estimates_path.rename(inference / "not-estimates.json")
        write_json(marker, freeze)
    # Opening this FIFO blocks. Bad public data must finish without reading it.
    # No filesystem authentication or total stat-observation claim is made.
    truth = tmp_path / "private-truth-trap"
    truth.mkdir()
    os.mkfifo(truth / "complete.json")
    before_inf, before_obs, before_truth = (
        snapshot(inference),
        snapshot(sealed["observations"]),
        snapshot(truth),
    )
    out = tmp_path / "evaluation"
    expect(cli(*evaluate_args(sealed["observations"], inference, truth, out), timeout=30), 4)
    assert snapshot(inference) == before_inf and snapshot(sealed["observations"]) == before_obs
    assert snapshot(truth) == before_truth and not out.exists()


@pytest.mark.parametrize("payload", ["specimen_source_relative.npy", *PRED_NAMES])
def test_every_completed_payload_verified_before_truth(
    tmp_path: Path, pipeline: dict[str, Any], payload: str
) -> None:
    inference = tmp_path / "inference"
    shutil.copytree(pipeline["inference"], inference)
    path = inference / payload
    path.write_bytes(path.read_bytes()[:-1])
    truth = tmp_path / "truth-trap"
    truth.mkdir()
    os.mkfifo(truth / "complete.json")
    before = snapshot(inference)
    out = tmp_path / "evaluation"
    expect(cli(*evaluate_args(pipeline["observations"], inference, truth, out), timeout=30), 4)
    assert snapshot(inference) == before and not out.exists()


@pytest.mark.parametrize(
    "defect",
    [
        "missing_marker",
        "partial_marker",
        "version",
        "unknown",
        "observation_identity",
        "missing_descriptor",
        "descriptor_order",
        "digest",
        "plan_keys",
        "plan_geometry",
        "summary_keys",
        "summary_version",
        "negative_source",
        "nonfinite_mean",
        "source_trailing",
    ],
)
def test_evaluation_private_protocol_rejections(
    tmp_path: Path, pipeline: dict[str, Any], defect: str
) -> None:
    truth = tmp_path / "truth"
    shutil.copytree(pipeline["truth"], truth)
    marker = truth / "complete.json"
    value = load_json(marker)
    if defect == "missing_marker":
        marker.rename(truth / "not-complete.json")
    elif defect == "partial_marker":
        marker.write_bytes(b"{")
    else:
        if defect == "version":
            value["format_version"] = "full_noisy_study_generation_v1"
        elif defect == "unknown":
            value["unknown"] = 1
        elif defect == "observation_identity":
            value["observation_manifest_sha256"] = "0" * 64
        elif defect == "missing_descriptor":
            value["files"].pop()
        elif defect == "descriptor_order":
            value["files"][0], value["files"][1] = value["files"][1], value["files"][0]
        elif defect == "digest":
            value["files"][0]["sha256"] = "0" * 64
        elif defect in ("plan_keys", "plan_geometry", "summary_keys", "summary_version"):
            name = "plan.json" if defect.startswith("plan") else "generation_summary.json"
            content = load_json(truth / name)
            if defect.endswith("keys"):
                content["unknown"] = 1
            elif defect == "plan_geometry":
                content["geometry"]["specimen_origin_um_zyx"][0] += 1.0
            else:
                content["format_version"] = "full_noisy_study_summary_v1"
            write_json(truth / name, content)
            value["files"] = [descriptor(truth, item["path"]) for item in value["files"]]
        elif defect in ("negative_source", "nonfinite_mean", "source_trailing"):
            name = (
                "specimen_source_e.npy"
                if defect != "nonfinite_mean"
                else "specimen_o2_p4_expected_signal_e.npy"
            )
            path = truth / name
            if defect == "source_trailing":
                path.write_bytes(path.read_bytes() + b"trailing")
            else:
                array = np.load(path, allow_pickle=False)
                array.flat[0] = -1.0 if defect == "negative_source" else np.nan
                with path.open("wb") as stream:
                    np.save(stream, array, allow_pickle=False)
            for item in value["files"]:
                if item["path"] == name:
                    item.update(size_bytes=path.stat().st_size, sha256=sha(path))
        write_json(marker, value)
    before = snapshot(truth)
    out = tmp_path / "evaluation"
    expect(
        in_process_cli(*evaluate_args(pipeline["observations"], pipeline["inference"], truth, out)),
        4,
    )
    assert snapshot(truth) == before and not out.exists()


@pytest.mark.parametrize(
    "case",
    [
        "zero_reference",
        "large_paired_source",
        "huge_phases_and_beams",
        "finite_mean_product_overflow",
    ],
)
def test_extreme_evaluation_honest_arithmetic_not_new_physical_acquisition(
    tmp_path: Path, pipeline: dict[str, Any], case: str
) -> None:
    # Content hashes assert identity, not scientific authenticity. Alter only
    # evaluator inputs after a REAL frozen inference. These are explicitly
    # synthetic arithmetic controls, never evidence of acquisition or recovery.
    truth = tmp_path / "arithmetic-truth"
    shutil.copytree(pipeline["truth"], truth)
    value = load_json(truth / "plan.json")
    summary = load_json(truth / "generation_summary.json")
    if case == "huge_phases_and_beams":
        value["illumination"]["phases_at_calibration_origin_rad"] = [
            [(-1 if (o + p) % 2 else 1) * 1e300 for p in range(9)] for o in range(3)
        ]
        component = float.fromhex("0x1.fffffffffffffp+1023")
        value["illumination"]["beam_amplitudes"] = [component] * 3
    elif case == "finite_mean_product_overflow":
        # Evaluator protocol arithmetic only: these private means are deliberately
        # altered after the actual inference freeze, not acquired physical truth.
        assert math.isinf(value["camera"]["gain_counts_per_e"] * 1e308)
        for name in RAW_NAMES:
            path = truth / name.replace(".npy", "_expected_signal_e.npy")
            original = np.load(path, allow_pickle=False)
            with path.open("wb") as stream:
                np.save(stream, np.full(original.shape, 1e308, dtype="<f8"), allow_pickle=False)
    else:
        path = truth / "specimen_source_e.npy"
        source = np.load(path, allow_pickle=False)
        source.fill(0 if case == "zero_reference" else 1.7e308)
        with path.open("wb") as stream:
            np.save(stream, source, allow_pickle=False)
        if case == "zero_reference":
            value["specimen_catalogue"] = []
            summary["source_mass"]["specimen"] = {
                "catalogue_total_e": 0.0,
                "stored_total_e": 0.0,
                "difference_e": 0.0,
                "relative_difference": None,
                "unavailable_fields": [
                    {"field": "relative_difference", "reason": "zero_reference"}
                ],
            }
        else:
            estimates = check_estimates(pipeline["inference"])
            value["camera"]["gain_counts_per_e"] = (
                estimates["camera_estimate"]["contrast_counts"] / 2
            )
            with localcontext() as ctx:
                ctx.prec = 1000
                total = sum((dec(x) for x in source.flat), Decimal(0))
                catalogue = sum((dec(row[4]) for row in value["specimen_catalogue"]), Decimal(0))
                summary["source_mass"]["specimen"] = {
                    "catalogue_total_e": float(catalogue),
                    "stored_total_e": None,
                    "difference_e": None,
                    "relative_difference": float((total - catalogue) / catalogue),
                    "unavailable_fields": [
                        {"field": "stored_total_e", "reason": "unrepresentable"},
                        {"field": "difference_e", "reason": "unrepresentable"},
                    ],
                }
    write_json(truth / "plan.json", value)
    write_json(truth / "generation_summary.json", summary)
    reseal(truth)
    frozen = snapshot(pipeline["inference"])
    out = tmp_path / "evaluation"
    expect(
        in_process_cli(*evaluate_args(pipeline["observations"], pipeline["inference"], truth, out)),
        0,
    )
    report = check_evaluation(out, pipeline["observations"], pipeline["inference"], truth)
    assert snapshot(pipeline["inference"]) == frozen
    if case == "finite_mean_product_overflow":
        camera = check_estimates(pipeline["inference"])["camera_estimate"]
        predictions = np.stack(
            [np.load(pipeline["inference"] / name, allow_pickle=False) for name in PRED_NAMES]
        )
        signal_reference, corrected_reference = finite_mean_prediction_references(
            np.full(predictions.shape, 1e308, dtype=np.float64),
            true_gain=value["camera"]["gain_counts_per_e"],
            true_offset=value["camera"]["offset_counts"],
            true_background=value["camera"]["background_e"],
            estimated_blank=camera["means_counts"][1],
            estimated_contrast=camera["contrast_counts"],
        )
        for field, reference in (
            ("signal_prediction_metrics", signal_reference),
            ("corrected_mean_prediction_metrics", corrected_reference),
        ):
            check_available_metric(report[field], predictions, reference)
            assert report[field]["count"] == predictions.size
            assert not any(item["field"] == field for item in report["unavailable_comparisons"])
    elif case != "huge_phases_and_beams":
        estimated = np.load(
            pipeline["inference"] / "specimen_source_relative.npy", allow_pickle=False
        )
        reference = np.full(estimated.shape, 0.0 if case == "zero_reference" else 1.7e308)
        check_metric(report["source_metrics"], estimated, reference)
        assert report["status"] == "evaluated_with_unavailable_metrics"
        field = "relative_l2" if case == "zero_reference" else "reference_l2"
        assert report["source_metrics"][field] is None
        if case == "large_paired_source":
            assert report["source_metrics"]["error_rms"] is not None
            assert report["source_metrics"]["error_mean"] is not None
            close_scalar(report["source_metrics"]["relative_l2"], 1.0)
    else:
        gauges = report["illumination_gauge_comparisons"]
        assert [g["gauge"] for g in gauges] == ["as_stored", "global_side_exchange"]
        # Numerical normalization despite raw-square or raw-norm overflow.
        assert all(math.isfinite(x) for g in gauges for x in g["normalized_beam_error"])
        candidate = check_estimates(pipeline["inference"])["bead_calibration"]["frozen_candidate"]
        for gauge, sign in zip(gauges, (1, -1), strict=True):
            check_normalized_beam_errors(
                gauge["normalized_beam_error"],
                candidate["beam_amplitudes"],
                value["illumination"]["beam_amplitudes"],
                side_exchange=sign == -1,
            )
            for o, p in itertools.product(range(3), range(9)):
                with localcontext() as ctx:
                    ctx.prec = 440
                    difference = sign * dec(candidate["phases_rad"][o][p]) - dec(
                        value["illumination"]["phases_at_calibration_origin_rad"][o][p]
                    )
                    turns = ((difference + physical_pi()) / (2 * physical_pi())).to_integral_value(
                        rounding="ROUND_FLOOR"
                    )
                    expected = float(difference - turns * 2 * physical_pi())
                close_scalar(gauge["wrapped_phase_error_rad"][o][p], expected, scale=8.0)


def test_prediction_metrics_preserve_tiny_absolute_errors_beside_large_common_signal(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    # Evaluator-only protocol arithmetic after a real completed CLI workflow.
    # These altered means/predictions claim neither acquisition nor recovery.
    inference, truth = tmp_path / "inference", tmp_path / "truth"
    shutil.copytree(pipeline["inference"], inference)
    shutil.copytree(pipeline["truth"], truth)
    estimates = check_estimates(inference)
    camera = estimates["camera_estimate"]
    contrast, blank = camera["contrast_counts"], camera["means_counts"][1]
    assert contrast > 0 and math.isfinite(contrast) and math.isfinite(blank)
    value = load_json(truth / "plan.json")
    value["camera"].update(gain_counts_per_e=contrast, offset_counts=blank, background_e=0.0)
    write_json(truth / "plan.json", value)

    large, tiny = math.ldexp(1.0, 500), math.ldexp(1.0, -600)
    shape = tuple(value["geometry"]["specimen_shape_zyx"])
    assert shape == (2, 1, 2)
    prediction = np.array([large, 0.0, 0.0, 0.0], dtype="<f8").reshape(shape)
    reference = np.array([large, tiny, 0.0, 0.0], dtype="<f8").reshape(shape)
    for prediction_name, raw_name in zip(PRED_NAMES, RAW_NAMES, strict=True):
        for path, array in (
            (inference / prediction_name, prediction),
            (truth / raw_name.replace(".npy", "_expected_signal_e.npy"), reference),
        ):
            with path.open("wb") as stream:
                np.save(stream, array, allow_pickle=False)
    reseal(inference, "freeze.json")
    reseal(truth)
    # Source stays the real nonnegative <f4 fit; no huge source coefficient.
    assert sha(inference / "specimen_source_relative.npy") == sha(
        pipeline["inference"] / "specimen_source_relative.npy"
    )
    check_freeze(inference, complete=True)
    check_descriptors(truth, load_json(truth / "complete.json")["files"], PRIVATE_NAMES)
    inputs = {path: snapshot(path) for path in (pipeline["observations"], inference, truth)}
    out = tmp_path / "evaluation"
    expect(cli(*evaluate_args(pipeline["observations"], inference, truth, out)), 0)
    report = check_evaluation(out, pipeline["observations"], inference, truth)
    assert report["inference_status"] == "completed_finite_fit"
    assert report["status"] in ("evaluated", "evaluated_with_unavailable_metrics")
    for path, before in inputs.items():
        assert snapshot(path) == before

    # Complete exact-real references: d/d*mu = mu and
    # (b + d*(mu+0) - b)/d = mu. Both contain the same small residual.
    # Fifteen four-voxel exposures: N=60, fifteen errors=-tiny.
    assert len(PRED_NAMES) == len(RAW_NAMES) == 15
    count = len(PRED_NAMES) * math.prod(shape)
    with localcontext() as ctx:
        ctx.prec = 1000
        d, b = dec(contrast), dec(blank)
        for mu in reference.flat:
            assert float(d * dec(mu) / d) == mu
            assert float((b + d * (dec(mu) + Decimal(0)) - b) / d) == mu
        error_l2 = (Decimal(15) * dec(tiny) ** 2).sqrt()
        reference_l2 = (Decimal(15) * (dec(large) ** 2 + dec(tiny) ** 2)).sqrt()
        expected = {
            "reference_l2": float(reference_l2),
            "error_l2": float(error_l2),
            "relative_l2": float(error_l2 / reference_l2),
            "error_rms": float((Decimal(15) * dec(tiny) ** 2 / count).sqrt()),
            "error_max_abs": tiny,
            "error_mean": float(-Decimal(15) * dec(tiny) / count),
        }
    assert count == 60
    assert expected["relative_l2"] == 0.0  # 2**-1100 rounds to zero.
    assert expected["error_rms"] == tiny / 2
    assert expected["error_mean"] == -tiny / 4
    for field in ("signal_prediction_metrics", "corrected_mean_prediction_metrics"):
        actual = report[field]
        assert set(actual) == {"count", "unavailable_fields", *expected}
        assert actual["count"] == count and actual["unavailable_fields"] == []
        assert not any(item["field"] == field for item in report["unavailable_comparisons"])
        assert actual["relative_l2"] == 0.0
        for name, wanted in expected.items():
            # Use each statistic's own scale, never the huge common input scale.
            if wanted != 0.0:
                assert actual[name] is not None and actual[name] != 0.0, (field, name, actual)
            close_scalar(actual[name], wanted)


def test_same_seed_same_version_generation_retains_identical_payloads(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    out = tmp_path / "repeat"
    expect(cli("generate", "--plan", str(pipeline["plan_path"]), "--out", str(out)), 0)
    assert snapshot(out) == snapshot(pipeline["run"])


def test_reference_controls_exact_membership_metrics_and_physical_period() -> None:
    # Non-product self-qualification: no assumed RNG result or special-function
    # accuracy margin. Fraction membership includes exact closed spherical ties.
    catalogue = [[0.5, 0.5, 0.5, 0.5, 3.0]]
    actual = exact_source(catalogue, (1, 1, 1), (1.0, 1.0, 1.0), (1, 1, 2))
    np.testing.assert_array_equal(actual, np.full((1, 1, 2), 1.5))
    result = metric_reference([3.0, -4.0], [0.0, 0.0])
    assert result["count"] == 2 and result["error_l2"] == 5.0
    assert result["error_mean"] == -0.5 and result["error_max_abs"] == 4.0
    assert result["reference_l2"] == 0.0 and result["relative_l2"] is None
    assert result["unavailable_fields"] == [{"field": "relative_l2", "reason": "zero_reference"}]
    large = metric_reference([-1.7e308] * 4, [1.7e308] * 4)
    assert large["reference_l2"] is None and large["error_rms"] is None
    assert large["relative_l2"] == 2.0
    stable = metric_reference([0.0] * 16, [1.7e308] * 16)
    assert stable["reference_l2"] is None and stable["error_l2"] is None
    assert stable["error_rms"] == 1.7e308 and stable["error_mean"] == -1.7e308
    assert stable["relative_l2"] == 1.0
    assert float(physical_pi()) == math.pi
    assert wrap_reference(math.pi) == -math.pi
    assert wrap_reference(0.5, (2.0**-1000, 0.0), (0.0, -1e308, 0.0), (0.0, 1e308, 0.0)) != 0.5
    rounded_period = (1e300 + math.pi) % (2 * math.pi) - math.pi
    assert abs(wrap_reference(1e300) - rounded_period) > 0.1


def test_existing_public_camera_control_with_independent_dyadic_oracle() -> None:
    from simrecon import estimate_scalar_camera

    # A small existing-code control is initially passing evidence, not red for
    # this absent driver. It qualifies the independent camera observer and the
    # accepted optional-gain path without requiring a scientific fit or mock.
    groups = [np.tile(np.asarray([[[v, v + 2.0]]]), (8, 1, 1)) for v in (-2.0, 0.0, 4.0)]
    before = [x.copy() for x in groups]
    modes = np.geterr().copy()
    rng = np.random.get_state()
    result = estimate_scalar_camera(
        groups[0], blank_counts=groups[1], flat_counts=groups[2], source="A-public-dyadic"
    )
    observed = public_record(result)
    reference = independent_camera_moments(groups, observed)
    # Exact dyadic reference arithmetic distinguishes K-1 from K. Returned
    # moments retain the contract's allowance; they need not equal the target bits.
    assert reference["means"] == [Decimal(-1), Decimal(1), Decimal(5)]
    assert reference["variances"] == [Decimal(2)] * 3
    assert result.contrast_counts == result.means_counts[2] - result.means_counts[1]
    variance_contrast = float(result.variances_counts2[2]) - float(result.variances_counts2[1])
    if variance_contrast > 0:
        assert result.gain_counts_per_e == variance_contrast / result.contrast_counts
        assert result.information_codes == ()
    else:
        assert result.gain_counts_per_e is None
        assert result.information_codes == ("nonpositive_variance_contrast",)
    # Constant-frame variance is specified to be EXACTLY zero, preserving the
    # real optional-gain path without requiring identical rounded nonzero variances.
    constant = [np.full((8, 1, 2), v, dtype=np.float64) for v in (-2.0, 0.0, 4.0)]
    uninformative = estimate_scalar_camera(
        constant[0],
        blank_counts=constant[1],
        flat_counts=constant[2],
        source="A-public-constant-variance",
    )
    independent_camera_moments(constant, public_record(uninformative))
    assert uninformative.contrast_counts > 0 and uninformative.gain_counts_per_e is None
    assert uninformative.information_codes == ("nonpositive_variance_contrast",)
    assert np.geterr() == modes
    after_rng = np.random.get_state()
    assert rng[0] == after_rng[0] and rng[2:] == after_rng[2:]
    np.testing.assert_array_equal(rng[1], after_rng[1])
    for original, current in zip(before, groups, strict=True):
        np.testing.assert_array_equal(original, current)


RECORD_PATHS = [
    ("camera_estimate",),
    ("bead_calibration",),
    ("bead_calibration", "initial_candidate"),
    ("bead_calibration", "objective_trace", 0),
    ("bead_calibration", "poll_attempts", 0),
    ("bead_calibration", "coordinate_evidence", 0),
    ("bead_calibration", "counts"),
    ("specimen_fit",),
    ("specimen_fit", "initial_score"),
    ("specimen_fit", "last_complete_gradient"),
    ("specimen_fit", "attempt_trace", 0),
    ("specimen_fit", "call_trace", 0),
    ("specimen_fit", "counts"),
]


@pytest.mark.parametrize("path", RECORD_PATHS)
@pytest.mark.parametrize("defect", ["unknown", "missing"])
def test_recursive_public_record_schema_rejection(
    tmp_path: Path, pipeline: dict[str, Any], path: tuple[Any, ...], defect: str
) -> None:
    inference = tmp_path / "inference"
    shutil.copytree(pipeline["inference"], inference)
    estimates = load_json(inference / "estimates.json")
    record = estimates
    for key in path:
        record = record[key]
    assert type(record) is dict, (path, "required small-case record unavailable")
    if defect == "unknown":
        record["unapproved"] = 1
    else:
        del record[next(iter(record))]
    write_json(inference / "estimates.json", estimates)
    reseal(inference, "freeze.json")
    out = tmp_path / "evaluation"
    expect(
        in_process_cli(*evaluate_args(pipeline["observations"], inference, pipeline["truth"], out)),
        4,
    )
    assert not out.exists()


def test_signed_frozen_predictions_remain_valid_protocol_input(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    inference = tmp_path / "inference"
    shutil.copytree(pipeline["inference"], inference)
    name = PRED_NAMES[-1]
    path = inference / name
    array = np.load(path, allow_pickle=False)
    array.fill(-1.25)
    with path.open("wb") as stream:
        np.save(stream, array, allow_pickle=False)
    reseal(inference, "freeze.json")
    out = tmp_path / "evaluation"
    # Byte identity is not authenticity; the evaluator reports signed error.
    expect(cli(*evaluate_args(pipeline["observations"], inference, pipeline["truth"], out)), 0)
    report = check_evaluation(out, pipeline["observations"], inference, pipeline["truth"])
    raw = np.load(pipeline["observations"] / RAW_NAMES[-1], allow_pickle=False)
    camera = check_estimates(inference)["camera_estimate"]
    with localcontext() as ctx:
        ctx.prec = 100
        residuals = [
            dec(-1.25) - (dec(x) - dec(camera["means_counts"][1])) / dec(camera["contrast_counts"])
            for x in raw.flat
        ]
        close_scalar(
            report["observed_residual_mean"][2][4],
            float(sum(residuals, Decimal(0)) / len(residuals)),
            scale=2.0,
        )


def test_tangent_beads_and_minimal_camera_are_legal(tmp_path: Path) -> None:
    value = plan(unavailable=True)
    value["geometry"]["camera_shape_yx"] = [1, 2]
    for row, x in zip(value["bead_catalogue"], (0.0625, 0.1625, 0.2625), strict=True):
        row[2] = x
    with localcontext() as ctx:
        ctx.prec = 100
        assert dec(0.1625) - dec(0.0625) == 2 * dec(0.050)
        assert dec(0.2625) - dec(0.1625) == 2 * dec(0.050)
    input_path, out = tmp_path / "plan.json", tmp_path / "generated"
    write_json(input_path, value)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 0)
    assert np.load(out / "observations/camera_dark.npy", allow_pickle=False).shape == (8, 1, 2)


def test_camera_generation_range_is_unsealed_and_preserved(tmp_path: Path) -> None:
    value = plan(unavailable=True)
    value["camera"]["flat_signal_e"] = 1e300  # finite but outside Poisson integer draw range
    input_path, out = tmp_path / "plan.json", tmp_path / "generated"
    write_json(input_path, value)
    result = cli("generate", "--plan", str(input_path), "--out", str(out))
    expect(result, 6)
    assert not (out / "generation.complete.json").exists()
    assert not (out / "observations/complete.json").exists()
    before = snapshot(out)
    expect(cli("generate", "--plan", str(input_path), "--out", str(out)), 5)
    assert snapshot(out) == before


@pytest.mark.parametrize(
    "defect",
    [
        "source_f8",
        "source_negative",
        "source_fortran",
        "source_reference",
        "prediction_nonfinite",
        "bead_reference",
    ],
)
def test_frozen_payload_domains_and_references(
    tmp_path: Path, pipeline: dict[str, Any], defect: str
) -> None:
    inference = tmp_path / "inference"
    shutil.copytree(pipeline["inference"], inference)
    if defect.endswith("reference"):
        estimates = load_json(inference / "estimates.json")
        record, field = (
            ("specimen_fit", "source_relative")
            if defect == "source_reference"
            else ("bead_calibration", "heldout_prediction")
        )
        estimates[record][field] = {"file": "../undeclared.npy"}
        write_json(inference / "estimates.json", estimates)
    else:
        path = inference / (
            PRED_NAMES[0] if defect == "prediction_nonfinite" else "specimen_source_relative.npy"
        )
        array = np.load(path, allow_pickle=False)
        if defect == "source_f8":
            array = array.astype("<f8")
        elif defect == "source_negative":
            array.flat[0] = -1.0
        elif defect == "source_fortran":
            array = np.asfortranarray(array)
        else:
            array.flat[0] = np.nan
        with path.open("wb") as stream:
            np.save(stream, array, allow_pickle=False)
    reseal(inference, "freeze.json")
    out = tmp_path / "evaluation"
    expect(
        in_process_cli(*evaluate_args(pipeline["observations"], inference, pipeline["truth"], out)),
        4,
    )
    assert not out.exists()


def test_real_bead_range_retains_actual_incomplete_record(tmp_path: Path) -> None:
    from scripts.image_only_bead_calibration import fit_bead_calibration

    from simrecon import estimate_scalar_camera

    obs = observation_bundle(tmp_path / "obs", camera_case="gain_missing")
    central = np.zeros((1, 2, 15), dtype="<f8")
    central[0, 0, [0, 7, 14]] = 100.0
    training = np.full((3, 9, 1, 2, 15), 1e308, dtype="<f8")
    manifest = load_json(obs / "complete.json")
    manifest["geometry"]["calibration_shape_zyx"] = [1, 2, 15]
    write_json(obs / "complete.json", manifest)
    with (obs / "calibration_heldout.npy").open("wb") as stream:
        np.save(stream, np.zeros((3, 5, 1, 2, 15), dtype="<f8"), allow_pickle=False)
    for name, array in (
        ("calibration_central.npy", central),
        ("calibration_training.npy", training),
    ):
        with (obs / name).open("wb") as stream:
            np.save(stream, array, allow_pickle=False)
    reseal(obs)
    out = tmp_path / "inference"
    expect(cli(*infer_args(obs, out)), 3)
    result, freeze = check_estimates(out), check_freeze(out, complete=False)
    assert result["fit_stage"] == freeze["stage"] == "bead"
    groups = [
        np.load(obs / f"camera_{n}.npy", allow_pickle=False) for n in ("dark", "blank", "flat")
    ]
    camera = estimate_scalar_camera(
        groups[0],
        blank_counts=groups[1],
        flat_counts=groups[2],
        source=f"full_noisy_study:{sha(obs / 'complete.json')}:camera",
    )
    direct = fit_bead_calibration(
        central,
        structured_counts=training,
        heldout_counts=np.load(obs / "calibration_heldout.npy", allow_pickle=False),
        camera_estimate=camera,
        origin_um_zyx=tuple(plan()["geometry"]["calibration_origin_um_zyx"]),
        sweep_scales=tuple(SETTINGS["sweep_scales"]),
    )
    # The complete squared-residual objective cannot fit float64. This is a
    # real required numerical obstruction, not a fabricated failed fitter.
    assert direct.status == "numerical_incomplete"
    assert result["bead_calibration"] == public_record(direct)
    assert result["failure_code"] == freeze["failure_code"] == direct.failure_code
    assert result["specimen_fit"] is None
    assert all(value == 0 for value in freeze["prediction_call_counts"].values())


def test_real_specimen_range_retains_bead_and_no_fabricated_source(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    obs = tmp_path / "observations"
    shutil.copytree(pipeline["observations"], obs)
    path = obs / RAW_NAMES[-1]
    array = np.full((2, 1, 2), 1e308, dtype="<f8")
    with path.open("wb") as stream:
        np.save(stream, array, allow_pickle=False)
    reseal(obs)
    out = tmp_path / "inference"
    expect(cli(*infer_args(obs, out)), 3)
    estimates, freeze = check_estimates(out), check_freeze(out, complete=False)
    assert estimates["fit_stage"] == freeze["stage"] == "specimen"
    assert estimates["bead_calibration"]["status"] == "completed_finite_fit"
    specimen = estimates["specimen_fit"]
    keys(specimen, FIELDS["SpecimenFitResult"])
    assert specimen["status"] == "numerical_incomplete"
    assert (
        specimen["stage"] == "initial_score" and specimen["failure_component"] == "data_objective"
    )
    assert (
        specimen["failure_code"]
        == estimates["failure_code"]
        == freeze["failure_code"]
        == "image_only_specimen_fit_range"
    )
    assert (
        specimen["source_relative"] is None
        and specimen["initial_score"] is None
        and specimen["best_score"] is None
    )
    assert [item["path"] for item in freeze["files"]] == [
        "estimates.json",
        "bead_heldout_prediction.npy",
    ]
    assert all(value == 0 for value in freeze["prediction_call_counts"].values())


def test_asymmetric_pairing_reference_and_geometry_are_distinguishing() -> None:
    value = plan()
    geometry = value["geometry"]
    seeds = value["seeds"]
    streams = [
        *seeds["camera_dark"],
        *seeds["camera_blank"],
        *seeds["camera_flat"],
        seeds["calibration_central"],
        *(seed for row in seeds["calibration_training"] for seed in row),
        *(seed for row in seeds["calibration_heldout"] for seed in row),
        *(seed for row in seeds["specimen"] for seed in row),
    ]
    assert streams == list(range(10000, 10082))  # Original fixed streams; no seed search.
    assert geometry["calibration_spacing_um_zyx"] == list(D)
    assert geometry["specimen_spacing_um_zyx"] == [0.25, 0.1, 0.12] != list(D)
    source = exact_source(
        value["specimen_catalogue"],
        geometry["specimen_shape_zyx"],
        geometry["specimen_spacing_um_zyx"],
        (2, 2, 2),
    )
    assert source.shape == (4, 2, 4)
    # Exact squared distances admit four sites in plane 0 and four in
    # plane 2. The intervening planes are outside both closed spheres.
    assert [np.count_nonzero(plane) for plane in source] == [4, 0, 4, 0]
    first_weight, second_weight = 700.0 / 4, 1300.0 / 4
    np.testing.assert_array_equal(np.unique(source[0][source[0] > 0]), [first_weight])
    np.testing.assert_array_equal(np.unique(source[2][source[2] > 0]), [second_weight])
    reference = paired_axial_reference(source, 2.0, 4.0)
    assert reference.shape == (2, 2, 4)
    for k, y, x in np.ndindex(reference.shape):
        # gain/contrast=1/2; this dyadic scale permits an exact rational target.
        from fractions import Fraction

        expected = float(
            (Fraction(float(source[2 * k, y, x])) + Fraction(float(source[2 * k + 1, y, x]))) / 2
        )
        assert reference[k, y, x] == expected
    assert not np.array_equal(reference, source[::2])  # doubling first fine plane
    assert not np.array_equal(reference, np.stack((reference[0], reference[0])))
    assert not np.array_equal(reference, reference[::-1])  # swapped coarse pairs
    assert not np.array_equal(reference, 0.5 * (source[:2] + source[2:]))  # split-half pairing


@pytest.mark.parametrize("target", ["group_mean", "small_frame_mean", "group_variance"])
@pytest.mark.parametrize("outside", [False, True])
def test_camera_observer_accepts_contract_allowance_and_rejects_excess(
    target: str, outside: bool
) -> None:
    # Synthetic observer qualification ONLY. No fake estimate enters production
    # or supplies a successful scientific fit/pipeline decision.
    groups = [np.tile(np.asarray([[[v, v + 2.0]]]), (8, 1, 1)) for v in (-2.0, 0.0, 4.0)]
    camera: dict[str, Any] = dict(
        means_counts=[-1.0, 1.0, 5.0],
        variances_counts2=[2.0, 2.0, 2.0],
        frame_means_counts=[[-1.0] * 8, [1.0] * 8, [5.0] * 8],
        frame_variances_counts2=[[2.0] * 8 for _ in range(3)],
        empirical_mean_se_counts=[0.0, 0.0, 0.0],
        contrast_counts=4.0,
        gain_counts_per_e=None,
        information_codes=["nonpositive_variance_contrast"],
        source="A-observer-only-dyadic",
    )
    reference = independent_camera_moments(groups, camera)
    assert reference["A"] == 6 and reference["ell"] == 12
    assert float(reference["mean_bound"]) == 4.092726157978177e-12
    if target == "group_mean":
        camera["means_counts"][2] = float(
            dec(5) + (2 * reference["mean_bound"] if outside else Decimal("1e-12"))
        )
    elif target == "small_frame_mean":
        camera["frame_means_counts"][0][0] = float(
            dec(-1) + (2 * reference["mean_bound"] if outside else Decimal("2e-12"))
        )
    else:
        camera["variances_counts2"][2] = float(
            dec(2) + (2 * reference["variance_bound"] if outside else Decimal("1e-10"))
        )
    camera["contrast_counts"] = camera["means_counts"][2] - camera["means_counts"][1]
    dvar = camera["variances_counts2"][2] - camera["variances_counts2"][1]
    camera["gain_counts_per_e"] = dvar / camera["contrast_counts"] if dvar > 0 else None
    camera["information_codes"] = [] if dvar > 0 else ["nonpositive_variance_contrast"]
    with localcontext() as ctx:
        ctx.prec = 1000
        for g in range(3):
            group_mean = dec(camera["means_counts"][g])
            differences = [dec(x) - group_mean for x in camera["frame_means_counts"][g]]
            camera["empirical_mean_se_counts"][g] = float(
                (sum((x * x for x in differences), Decimal(0)) / 56).sqrt()
            )
    if outside:
        with pytest.raises(AssertionError):
            independent_camera_moments(groups, camera)
    else:
        independent_camera_moments(groups, camera)


@pytest.mark.parametrize("version", [(1, 0), (2, 0), (3, 0)])
@pytest.mark.parametrize("fortran", [False, True])
def test_header_observer_distinguishes_declared_order_from_loaded_strides(
    tmp_path: Path, version: tuple[int, int], fortran: bool
) -> None:
    values = np.asarray([[[1.0, -2.0]]], dtype="<f8")
    path = tmp_path / "single-axis.npy"
    save_declared_order_npy(path, values, version, fortran=fortran)
    loaded = np.load(path, allow_pickle=False)
    assert loaded.flags.c_contiguous and loaded.flags.f_contiguous
    item = descriptor(tmp_path, path.name)
    if fortran:
        with pytest.raises(AssertionError):
            read_npy(tmp_path, item)
    else:
        np.testing.assert_array_equal(read_npy(tmp_path, item), values)


@pytest.mark.parametrize("fortran", [False, True])
def test_v3_header_order_through_actual_cli_with_dual_contiguous_payload(
    tmp_path: Path, fortran: bool
) -> None:
    obs = observation_bundle(tmp_path / "obs", version=(3, 0))
    manifest = load_json(obs / "complete.json")
    manifest["geometry"]["specimen_shape_zyx"] = [1, 1, 2]
    for name in RAW_NAMES:
        path = obs / name
        path.rename(obs / (name + ".original"))
        save_declared_order_npy(
            path,
            np.zeros((1, 1, 2), dtype="<f8"),
            (3, 0),
            fortran=fortran if name == RAW_NAMES[-1] else False,
        )
    write_json(obs / "complete.json", manifest)
    reseal(obs)
    assert np.load(obs / RAW_NAMES[-1], allow_pickle=False).flags.c_contiguous
    before = snapshot(obs)
    out = tmp_path / "inference"
    expect(cli(*infer_args(obs, out)), 4 if fortran else 3)
    assert snapshot(obs) == before
    if fortran:
        assert not out.exists()
    else:
        check_freeze(out, complete=False)


# Exact-key negative examples: each targets an inherited dimension/domain or an
# explicitly authoritative retained-record relation. Every base fit is REAL.
INNER_RECORD_MUTATIONS = [
    ("estimates", ("bead_calibration", "initial_coordinates"), lambda old, root: old[:-1]),
    (
        "estimates",
        ("bead_calibration", "frozen_candidate", "carriers_yx_per_um", 0),
        lambda old, root: old[:1],
    ),
    (
        "estimates",
        ("bead_calibration", "frozen_candidate", "brightness_relative", 0),
        lambda old, root: -1.0,
    ),
    (
        "estimates",
        ("bead_calibration", "frozen_candidate", "carriers_yx_per_um", 0),
        lambda old, root: [10.0, 0.0],
    ),
    ("estimates", ("bead_calibration", "heldout_residual_mean", 0), lambda old, root: old[:-1]),
    ("estimates", ("bead_calibration", "heldout_residual_rms", 0, 0), lambda old, root: -1.0),
    ("estimates", ("bead_calibration", "objective_trace", 0, "objective"), lambda old, root: -1.0),
    (
        "estimates",
        ("bead_calibration", "poll_attempts", 0, "coordinate_index"),
        lambda old, root: 47,
    ),
    (
        "estimates",
        ("bead_calibration", "poll_attempts", 0, "trial_coordinates"),
        lambda old, root: old[:-1],
    ),
    ("estimates", ("bead_calibration", "counts", "attempted_polls"), lambda old, root: old + 1),
    (
        "estimates",
        ("bead_calibration", "coordinate_evidence", 0, "attempt_count"),
        lambda old, root: old + 1,
    ),
    (
        "estimates",
        ("bead_calibration", "unprobed_coordinates"),
        lambda old, root: sorted(set(old) ^ {0}),
    ),
    (
        "estimates",
        ("bead_calibration", "best_score_index"),
        lambda old, root: len(root["bead_calibration"]["objective_trace"]),
    ),
    ("estimates", ("bead_calibration", "camera_source"), lambda old, root: old + ":mismatched"),
    ("estimates", ("bead_calibration", "contrast_counts"), lambda old, root: old * 2),
    ("estimates", ("bead_calibration", "status"), lambda old, root: "initialization_failed"),
    ("estimates", ("specimen_fit", "source_shape_zyx"), lambda old, root: old[:-1]),
    ("estimates", ("specimen_fit", "source_shape_zyx", 0), lambda old, root: old + 1),
    (
        "estimates",
        ("specimen_fit", "best_score", "candidate_id"),
        lambda old, root: 1 + max(a["candidate_id"] for a in root["specimen_fit"]["attempt_trace"]),
    ),
    ("estimates", ("specimen_fit", "best_score", "residual_mean", 0), lambda old, root: old[:-1]),
    ("estimates", ("specimen_fit", "best_score", "total_objective"), lambda old, root: -1.0),
    ("estimates", ("specimen_fit", "counts", "best_updates"), lambda old, root: old + 1),
    ("estimates", ("specimen_fit", "counts", "forward_completed"), lambda old, root: old + 1),
    ("estimates", ("specimen_fit", "counts", "cache_attempted"), lambda old, root: True),
    ("estimates", ("specimen_fit", "call_trace", 0, "call_index"), lambda old, root: 0),
    (
        "estimates",
        ("specimen_fit", "call_trace", 0, "failure_code"),
        lambda old, root: "simulation_inverse_operator_range",
    ),
    (
        "estimates",
        ("specimen_fit", "attempt_trace", 0, "score", "candidate_id"),
        lambda old, root: 1,
    ),
    ("estimates", ("specimen_fit", "camera_source"), lambda old, root: old + ":mismatched"),
    ("estimates", ("specimen_fit", "illumination_source"), lambda old, root: old + ":mismatched"),
    ("estimates", ("specimen_fit", "phases_at_specimen_origin_rad", 0), lambda old, root: old[:-1]),
    ("estimates", ("specimen_fit", "source_spacing_um_zyx", 1), lambda old, root: -old),
    ("estimates", ("specimen_fit", "regularization"), lambda old, root: 0.0),
    ("estimates", ("specimen_fit", "max_iterations"), lambda old, root: old + 1),
    ("estimates", ("specimen_fit", "status"), lambda old, root: "normalization_unavailable"),
    ("estimates", ("fit_status",), lambda old, root: "unavailable"),
    ("estimates", ("fit_stage",), lambda old, root: "bead"),
    ("freeze", ("prediction_call_counts", "forward_completed"), lambda old, root: 2),
]


def object_keys(value: Any, path: tuple[Any, ...] = ()) -> dict[tuple[Any, ...], set[str]]:
    """Observe object key sets independently of malformed inner numeric values."""
    result = {}
    if isinstance(value, dict):
        result[path] = set(value)
        for key, item in value.items():
            result.update(object_keys(item, (*path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.update(object_keys(item, (*path, index)))
    return result


@pytest.mark.parametrize(
    "document,path,change",
    INNER_RECORD_MUTATIONS,
    ids=[
        f"{n:02d}-{doc}-{'-'.join(map(str, path))}"
        for n, (doc, path, _) in enumerate(INNER_RECORD_MUTATIONS)
    ],
)
def test_inner_record_consistency_before_private_read(
    tmp_path: Path, pipeline: dict[str, Any], document: str, path: tuple[Any, ...], change: Any
) -> None:
    original = snapshot(pipeline["inference"])
    inference = tmp_path / "inference"
    shutil.copytree(pipeline["inference"], inference)
    documents = {
        "estimates": load_json(inference / "estimates.json"),
        "freeze": load_json(inference / "freeze.json"),
    }
    before_keys = object_keys(documents)
    root = documents[document]
    container = root
    for key in path[:-1]:
        container = container[key]
    container[path[-1]] = change(container[path[-1]], root)
    assert object_keys(documents) == before_keys
    write_json(inference / "estimates.json", documents["estimates"])
    documents["freeze"]["files"] = [
        descriptor(inference, item["path"]) for item in documents["freeze"]["files"]
    ]
    write_json(inference / "freeze.json", documents["freeze"])
    before = snapshot(inference)
    truth = tmp_path / "private-read-trap"
    truth.mkdir()
    os.mkfifo(truth / "complete.json")
    truth_before = snapshot(truth)
    out = tmp_path / "evaluation"
    expect(cli(*evaluate_args(pipeline["observations"], inference, truth, out), timeout=30), 4)
    assert not out.exists() and snapshot(inference) == before
    assert snapshot(pipeline["inference"]) == original and snapshot(truth) == truth_before


def test_completed_unprobed_records_are_legitimate_evaluator_input(
    tmp_path: Path, pipeline: dict[str, Any]
) -> None:
    settings = {**SETTINGS, "sweep_scales": [float.fromhex("0x0.0000000000001p-1022")]}
    inference, out = tmp_path / "inference", tmp_path / "evaluation"
    expect(cli(*infer_args(pipeline["observations"], inference, settings)), 0)
    estimates = check_estimates(inference)
    assert estimates["bead_calibration"]["status"] == "completed_finite_fit"
    assert estimates["bead_calibration"]["unprobed_coordinates"] == list(range(47))
    expect(cli(*evaluate_args(pipeline["observations"], inference, pipeline["truth"], out)), 0)
    report = check_evaluation(out, pipeline["observations"], inference, pipeline["truth"])
    assert report["status"] in ("evaluated", "evaluated_with_unavailable_metrics")


@pytest.mark.parametrize("side_exchange", [False, True])
@pytest.mark.parametrize("nearby_roundoff", [False, True])
@pytest.mark.parametrize(
    "true_component",
    [1e308, float.fromhex("0x1.fffffffffffffp+1023")],
    ids=["raw-square-overflow", "raw-norm-overflow"],
)
def test_extreme_beam_observer_accepts_independent_normalization(
    side_exchange: bool, nearby_roundoff: bool, true_component: float
) -> None:
    # Observer qualification only: exact specified algebra, not fitted numbers
    # borrowed from a product/reviewer and not a fabricated scientific outcome.
    fitted, true = [4.0, 2.0, 1.0], [true_component] * 3
    ordered = [4.0, 1.0, 2.0] if side_exchange else fitted
    expected = [v / math.sqrt(21.0) - 1 / math.sqrt(3.0) for v in ordered]
    if nearby_roundoff:
        expected = [float(v + 8 * np.finfo(float).eps) for v in expected]
    check_normalized_beam_errors(expected, fitted, true, side_exchange=side_exchange)


@pytest.mark.parametrize("side_exchange", [False, True])
@pytest.mark.parametrize("component", [0, 1, 2])
@pytest.mark.parametrize(
    "true_component",
    [1e308, float.fromhex("0x1.fffffffffffffp+1023")],
    ids=["raw-square-overflow", "raw-norm-overflow"],
)
def test_extreme_beam_observer_rejects_each_finite_wrong_component(
    side_exchange: bool, component: int, true_component: float
) -> None:
    fitted, true = [4.0, 2.0, 1.0], [true_component] * 3
    ordered = [4.0, 1.0, 2.0] if side_exchange else fitted
    wrong = [v / math.sqrt(21.0) - 1 / math.sqrt(3.0) for v in ordered]
    # Pure arithmetic counterexamples, never production/fitter substitutions:
    # raw squares overflow at1e308; an unscaled hypot overflows at maximum finite.
    bad_norm = math.sqrt(sum(v * v for v in true)) if true_component == 1e308 else math.hypot(*true)
    assert math.isinf(bad_norm)
    wrong[component] = ordered[component] / math.sqrt(21.0) - true[component] / bad_norm
    assert all(math.isfinite(v) for v in wrong)
    with pytest.raises(AssertionError):
        check_normalized_beam_errors(wrong, fitted, true, side_exchange=side_exchange)


@pytest.mark.parametrize("reference_kind", ["signal", "corrected_mean"])
@pytest.mark.parametrize("outcome", ["available", "null", "unrepresentable", "finite_zero"])
def test_finite_mean_metric_reference_and_observer_qualification(
    reference_kind: str, outcome: str
) -> None:
    # Pure arithmetic/observer qualification. These arrays are not a fitted
    # source, camera estimate or fabricated successful scientific CLI result.
    means, prediction = np.full(60, 1e308, dtype=np.float64), np.zeros(60, dtype=np.float64)
    assert math.isinf(2.0 * 1e308)
    signal, corrected = finite_mean_prediction_references(
        means,
        true_gain=2.0,
        true_offset=-7.0,
        true_background=0.1,
        estimated_blank=-6.5,
        estimated_contrast=1024.0,
    )
    reference = signal if reference_kind == "signal" else corrected
    # Exact dyadic division is an independent finite expression; the bounded
    # affine terms are far below a float64 ulp here and do not change rounding.
    scalar = 1e308 / 512.0
    np.testing.assert_array_equal(reference, np.full(60, scalar, dtype=np.float64))
    norm = scalar * math.sqrt(60.0)
    assert math.isfinite(norm)
    summary: Any = dict(
        count=60,
        reference_l2=norm,
        error_l2=norm,
        relative_l2=1.0,
        error_rms=scalar,
        error_max_abs=scalar,
        error_mean=-scalar,
        unavailable_fields=[],
    )
    if outcome == "null":
        summary = None
    elif outcome == "unrepresentable":
        summary["reference_l2"] = None
        summary["unavailable_fields"] = [{"field": "reference_l2", "reason": "unrepresentable"}]
    elif outcome == "finite_zero":
        for name in (
            "reference_l2",
            "error_l2",
            "relative_l2",
            "error_rms",
            "error_max_abs",
            "error_mean",
        ):
            summary[name] = 0.0
        assert all(math.isfinite(summary[name]) for name in summary if name != "unavailable_fields")
    if outcome == "available":
        check_available_metric(summary, prediction, reference)
    else:
        with pytest.raises(AssertionError):
            check_available_metric(summary, prediction, reference)
