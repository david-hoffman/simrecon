"""Oracle-only new preregistration freeze; never invokes product or pytest."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ce08_recovery_large_budget import bounds, gamma
from ce08_recovery_large_model import (
    FIXTURE,
    acquire,
    acquisition_bounds,
    carriers,
    conventional,
    expected,
    physical_response,
    project,
    registration,
    sample,
    source_modes,
    transfer_table,
    wave,
)


def recovery_metrics(
    image: Any, conventional_modes: Any, truth_modes: Any, truth: Any, p: Any
) -> dict[str, Any]:
    coeff = project(image, p)
    relative = abs(coeff - truth_modes) / abs(truth_modes)
    highs = np.array(p["source"]["high_mode_indices"]) + 1
    fractions = abs(coeff[highs] / truth_modes[highs])
    phases = abs(np.angle(coeff[highs] / truth_modes[highs]))
    conv = abs(conventional_modes[highs] / truth_modes[highs])
    improvements = abs(conventional_modes[highs] - truth_modes[highs]) / abs(
        coeff[highs] - truth_modes[highs]
    )
    return {
        "relative_complex_mode_errors": relative.tolist(),
        "high_mode_amplitude_fractions": fractions.tolist(),
        "high_mode_phase_errors_rad": phases.tolist(),
        "conventional_high_mode_fractions": conv.tolist(),
        "high_mode_error_improvements": improvements.tolist(),
        "global_relative_l2_error": float(np.linalg.norm(image - truth) / np.linalg.norm(truth)),
        "image_min": float(image.min()),
        "image_max": float(image.max()),
    }


def assert_recovery(metrics: dict[str, Any], p: dict[str, Any]) -> None:
    c = p["recovery_criteria"]
    assert max(metrics["relative_complex_mode_errors"]) <= c["all_mode_relative_complex_error_max"]
    assert min(metrics["high_mode_amplitude_fractions"]) >= c["high_mode_amplitude_fraction_min"]
    assert max(metrics["high_mode_amplitude_fractions"]) <= c["high_mode_amplitude_fraction_max"]
    assert max(metrics["high_mode_phase_errors_rad"]) <= c["high_mode_phase_error_rad_max"]
    assert (
        max(metrics["conventional_high_mode_fractions"]) <= c["conventional_high_mode_fraction_max"]
    )
    assert (
        min(metrics["high_mode_error_improvements"]) >= c["high_mode_error_improvement_factor_min"]
    )
    assert metrics["global_relative_l2_error"] <= c["global_relative_l2_error_max"]
    assert metrics["image_min"] < c["signed_min_upper"]
    assert metrics["image_max"] > c["signed_max_lower"]


def freeze(evidence: Path) -> None:
    evidence.mkdir(parents=True, exist_ok=True)
    p = registration()
    pre = acquisition_bounds(p)
    (evidence / "pre-observation-bounds.json").write_text(json.dumps(pre, indent=2) + "\n")
    h = transfer_table(p)
    data = acquire(p, h)
    ref = expected(p, data["raw"], h)
    error = bounds(data["raw"], h, p, ref)
    unquantized = expected(p, data["unquantized_raw"], h)
    conv = conventional(data["raw"])
    power, response = physical_response(p, h)
    tm = project(data["truth"], p)
    em = project(ref["density_image"], p)
    cm = project(conv, p)
    im = tm * response
    # Independent continuous signal-response derivation challenged against
    # complete literal traversal before product. No fitted/rescaled oracle.
    np.testing.assert_allclose(
        project(unquantized["density_image"], p), im, rtol=0, atol=error["mode_atol"]
    )
    illumination_a = np.tile([complex(*v) for v in p["source"]["side_modulation_pairs"]], (3, 1))
    np.testing.assert_allclose(
        unquantized["modulation"], illumination_a, rtol=0, atol=error["modulation_atol"]
    )
    keys = [(0, 0, 0), *(tuple(row[:3]) for row in p["source"]["positive_modes_kxyz_real_imag"])]
    response_map = dict(zip(keys, response, strict=True))
    for key, value in list(response_map.items()):
        response_map[tuple(-j for j in key)] = value
    ideal_image = np.real(
        sum(
            c * response_map[k] * wave((k[0] / 24, k[1] / 24, k[2] / 8), True)
            for k, c in source_modes(p)
        )
    )
    np.testing.assert_allclose(
        unquantized["density_image"], ideal_image, rtol=0, atol=error["density_image_atol"]
    )
    # Public source-origin and all-signed-direction inventory, no product.
    inventory, by_direction = [], np.zeros((len(keys), 3))
    for i, key in enumerate(keys):
        for d, k0 in enumerate(carriers(p)):
            for order in range(-2, 3):
                q = np.array((key[0] / 24, key[1] / 24)) - order * k0
                eligible = np.linalg.norm(q) < 0.5
                hh = sample(h, abs(order), float(q[0]), float(q[1]), key[2]) if eligible else 0j
                aa = 1 + 0j if order == 0 else illumination_a[d, abs(order) - 1]
                term = abs(aa * hh) ** 2
                by_direction[i, d] += term
                inventory.append(
                    [i, d, order, q[0], q[1], key[2], hh.real, hh.imag, term, int(eligible)]
                )
    # Regrouping15 nonnegative powers into3 sums of5 incurs at most the
    # sum of both gamma bounds; this is not the physical/product tolerance.
    np.testing.assert_allclose(
        by_direction.sum(axis=1), power, rtol=0, atol=2 * gamma(30) * max(power)
    )
    per_direction_wrong_response = np.sum(by_direction / (by_direction + 0.002**2), axis=1)
    assert per_direction_wrong_response[0] - response[0] > 1.9
    assert np.max(abs(ref["modulation"] - illumination_a)) > 5 * error["modulation_atol"]
    # Every sampled threshold value at both possible overlap requests. Table
    # queries here are oracle-only diagnostics, not extra product requirements.
    threshold_margins = []
    for k0 in carriers(p):
        for order in (1, 2):
            for iy in range(-11, 13):
                for ix in range(-11, 13):
                    q = np.array((ix / 24, iy / 24))
                    if np.linalg.norm(q) > 0.5:
                        continue
                    for shift in (-order * k0, order * k0):
                        other = q + shift
                        if np.linalg.norm(other) > 0.5:
                            continue
                        for iz in (-1, 0, 1):
                            for qq in (q, other):
                                for factor in (1, 5):
                                    threshold_margins.append(
                                        abs(
                                            factor
                                            * abs(sample(h, order, float(qq[0]), float(qq[1]), iz))
                                            - 0.006
                                        )
                                    )
    signal_margins = [0.5 - math.hypot(row[3], row[4]) for row in inventory if row[8] > 1e-20]
    arrays = {
        **data,
        "transfer": h,
        "bands": ref["bands"],
        "filtered": ref["filtered"],
        "modulation": ref["modulation"],
        "expected_workflow_image": ref["image"],
        "expected_density_image": ref["density_image"],
        "conventional": conv,
        "truth_modes": tm,
        "expected_modes": em,
        "conventional_modes": cm,
        "ideal_modes": im,
        "ideal_response": response,
        "mode_power": power,
        "regularization_bias_modes": im - tm,
        "taper_bias_modes": np.zeros_like(tm),
        "quantization_image_delta": ref["density_image"] - unquantized["density_image"],
        "quantization_mode_delta": em - project(unquantized["density_image"], p),
        "source_residual": ref["density_image"] - data["truth"],
        "conventional_residual": conv - data["truth"],
        "ideal_density_image": ideal_image,
        "mode_power_by_direction": by_direction,
        "signed_direction_order_inventory": np.array(inventory),
        "wrong_per_direction_denominator_response": per_direction_wrong_response,
        "signed_source_bins": np.array([k for k, _ in source_modes(p)]),
        "signed_truth_coefficients": np.array([c for _, c in source_modes(p)]),
        "signed_expected_coefficients": np.array(
            [
                np.mean(
                    ref["density_image"] * np.conj(wave((k[0] / 24, k[1] / 24, k[2] / 8), True))
                )
                for k, _ in source_modes(p)
            ]
        ),
    }
    for i, build in enumerate(ref["builds"]):
        for name in ("fourier", "spatial", "written"):
            arrays[f"overlap{i}_{name}"] = build[name]
        arrays[f"fit{i}_real"] = np.array([build[name] for name in ("SX", "SY", "correlation")])
        arrays[f"fit{i}_complex"] = np.array(
            [build[name] for name in ("cross", "forward", "reverse", "combined")]
        )
    # Preserve oracle arrays even if the preregistered physical goal fails.
    np.savez_compressed(FIXTURE, **arrays)
    metrics = recovery_metrics(ref["density_image"], cm, tm, data["truth"], p)
    diagnostics = {
        "pre_observation": pre,
        "budget": error,
        "carriers_cyc_um": carriers(p).tolist(),
        "power": power.tolist(),
        "response": response.tolist(),
        "physical_criteria": metrics,
        "quantization_image_delta_max": float(abs(arrays["quantization_image_delta"]).max()),
        "quantization_mode_delta_max": float(abs(arrays["quantization_mode_delta"]).max()),
        "raw_quantization_max": float(abs(data["raw"] - data["unquantized_raw"]).max()),
        "raw_min_max": [float(data["raw"].min()), float(data["raw"].max())],
        "reference_corrected_counts_min": float(data["reference_corrected_counts"].min()),
        "specimen_corrected_counts_min": float(data["specimen_corrected_counts"].min()),
        "unconverted_workflow_dc": float(np.mean(ref["image"])),
        "density_dc": float(np.mean(ref["density_image"])),
        "conventional_dc": float(np.mean(conv)),
        "continuum_total_signed_mass_density_unit": 576.0,
        "output_quadrature_signed_mass_density_unit": float(data["truth"].sum() * 0.25),
        "minimum_overlap_threshold_distance": float(min(threshold_margins)),
        "minimum_signal_bearing_support_margin_cyc_um": float(min(signal_margins)),
        "wrong_per_direction_denominator_dc_response": float(per_direction_wrong_response[0]),
        "fitted_modulation_minus_illumination_max": float(
            np.max(abs(ref["modulation"] - illumination_a))
        ),
        "unquantized_diagonal_full_image_discrepancy_max": float(
            abs(unquantized["density_image"] - ideal_image).max()
        ),
    }
    (evidence / "oracle-diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    assert_recovery(metrics, p)


if __name__ == "__main__":
    import sys

    freeze(Path(sys.argv[1]))
