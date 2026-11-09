"""Oracle-only fixture freeze, executable only through source_free_check.py.

No product import/call, pytest or result selection. Never invoke after product
execution to replace a preregistration. Fresh B must review the new checkpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ce08_recovery_budget import bounds
from ce08_recovery_model import (
    FIXTURE,
    acquire,
    acquisition_bounds,
    conventional,
    expected,
    mode_response,
    project,
    registration,
    transfer_table,
)


def freeze(evidence: Path) -> None:
    p = registration()
    pre_observation = acquisition_bounds(p)
    evidence.mkdir(parents=True, exist_ok=True)
    # Bounds are recorded before observation synthesis, even within this run.
    (evidence / "pre-observation-bounds.json").write_text(
        json.dumps(pre_observation, indent=2) + "\n"
    )
    h = transfer_table(p)
    observations = acquire(p, h)
    reference = expected(p, observations["raw"], h)
    error = bounds(observations["raw"], h, p, reference)
    unquantized = expected(p, observations["unquantized_raw"], h)
    conv = conventional(observations["raw"])
    powers, response = mode_response(p, h)
    truth_modes = project(observations["truth"], p)
    image_modes = project(reference["image"], p)
    ideal_modes = truth_modes * response
    conv_modes = project(conv, p)
    # This check validates the NEW physical diagonal derivation against the
    # complete independent literal procedure before product availability.
    np.testing.assert_allclose(
        project(unquantized["image"], p), ideal_modes, rtol=0, atol=error["mode_atol"]
    )
    np.testing.assert_allclose(
        unquantized["modulation"],
        [complex(*v) for v in p["source"]["side_modulation_pairs"]],
        rtol=0,
        atol=error["modulation_atol"],
    )
    relative = abs(image_modes[1:] - truth_modes[1:]) / abs(truth_modes[1:])
    criteria = p["recovery_criteria"]
    assert np.max(relative) < criteria["all_mode_relative_complex_error_max"]
    assert (
        np.linalg.norm(reference["image"] - observations["truth"])
        / np.linalg.norm(observations["truth"])
        < criteria["global_relative_l2_error_max"]
    )
    assert np.min(reference["image"]) < criteria["signed_min_upper"]
    assert np.max(reference["image"]) > criteria["signed_max_lower"]
    for row in p["source"]["high_mode_indices"]:
        i = row + 1
        fraction = abs(image_modes[i]) / abs(truth_modes[i])
        assert (
            criteria["high_mode_amplitude_fraction_min"]
            < fraction
            < criteria["high_mode_amplitude_fraction_max"]
        )
        assert (
            abs(np.angle(image_modes[i] / truth_modes[i]))
            < criteria["high_mode_phase_error_rad_max"]
        )
        assert (
            abs(conv_modes[i]) / abs(truth_modes[i])
            < criteria["conventional_high_mode_fraction_max"]
        )
        assert (
            abs(conv_modes[i] - truth_modes[i]) / abs(image_modes[i] - truth_modes[i])
            > criteria["high_mode_error_improvement_factor_min"]
        )
    arrays = {
        **observations,
        "transfer": h,
        "bands": reference["bands"],
        "filtered": reference["filtered"],
        "expected_image": reference["image"],
        "modulation": reference["modulation"],
        "conventional": conv,
        "truth_modes": truth_modes,
        "expected_modes": image_modes,
        "conventional_modes": conv_modes,
        "ideal_modes": ideal_modes,
        "ideal_response": response,
        "mode_power": powers,
        "regularization_bias_modes": ideal_modes - truth_modes,
        "taper_bias_modes": np.zeros_like(truth_modes),
        "quantization_image_delta": reference["image"] - unquantized["image"],
        "quantization_mode_delta": image_modes - project(unquantized["image"], p),
        "source_residual": reference["image"] - observations["truth"],
    }
    for m, (build, fitted) in enumerate(
        zip(reference["builds"], reference["fits"], strict=True), 1
    ):
        for key in ("fourier", "spatial", "written"):
            arrays[f"overlap{m}_{key}"] = build[key]
        arrays[f"fit{m}_real"] = np.array([fitted[v] for v in ("SX", "SY", "correlation")])
        arrays[f"fit{m}_complex"] = np.array(
            [fitted[v] for v in ("cross", "forward", "reverse", "combined")]
        )
    np.savez_compressed(FIXTURE, **arrays)
    diagnostics = {
        "pre_observation": pre_observation,
        "numerical_budget": error,
        "mode_power": powers.tolist(),
        "ideal_response": response.tolist(),
        "relative_mode_errors": relative.tolist(),
        "expected_image_min_max": [
            float(np.min(reference["image"])),
            float(np.max(reference["image"])),
        ],
        "relative_image_error": float(
            np.linalg.norm(arrays["source_residual"]) / np.linalg.norm(observations["truth"])
        ),
        "quantization_image_delta_max": float(np.max(abs(arrays["quantization_image_delta"]))),
        "quantization_mode_delta_max": float(np.max(abs(arrays["quantization_mode_delta"]))),
        "actual_raw_quantization_max": float(
            np.max(abs(observations["raw"] - observations["unquantized_raw"]))
        ),
        "raw_min_max": [float(observations["raw"].min()), float(observations["raw"].max())],
        "reference_counts_min": float(observations["reference_corrected_counts"].min()),
        "specimen_counts_min": float(observations["specimen_corrected_counts"].min()),
    }
    (evidence / "oracle-diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    import sys

    freeze(Path(sys.argv[1]))
