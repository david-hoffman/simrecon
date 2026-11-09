"""CE08 matched physical recovery against an on-demand independent observer."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from ce08_error_budget import gamma
from ce08_recovery_budget import (
    assert_float32_rounding,
    assert_transfer_regeneration,
    bounds,
    physical_observer_bounds,
)
from ce08_recovery_model import (
    acquire,
    conventional,
    coordinates,
    expected,
    mode_response,
    project,
    registration,
    transfer_table,
)

# SHA-256 of the accepted archive's C-order little-endian inputs and stacked masks.
RAW_SHA256 = "714ed10a0a9fce2a7010dc267dd9cfe18e93ea0d72d0e7521e969ae7b4aa25b3"
TRANSFER_SHA256 = "c506f4073a721f1cba92a57ed0f2f266142f51764a8e5ee02efbfa8517543079"
OVERLAP_WRITTEN_SHA256 = "18a75c7e4f86fe2e5058a364507bb439f4d871a3bc123c652392a5aafca712d6"


def close(actual: Any, reference: Any, error: float) -> None:
    np.testing.assert_allclose(actual, reference, rtol=0, atol=error)


def assert_recovery(
    actual: Any, conventional_modes: Any, truth_modes: Any, truth: Any, p: dict[str, Any]
) -> None:
    criteria = p["recovery_criteria"]
    coefficients = project(actual, p)
    errors = abs(coefficients[1:] - truth_modes[1:]) / abs(truth_modes[1:])
    assert np.max(errors) <= criteria["all_mode_relative_complex_error_max"]
    for row in p["source"]["high_mode_indices"]:
        index = row + 1
        fraction = abs(coefficients[index]) / abs(truth_modes[index])
        assert (
            criteria["high_mode_amplitude_fraction_min"]
            <= fraction
            <= criteria["high_mode_amplitude_fraction_max"]
        )
        assert (
            abs(np.angle(coefficients[index] / truth_modes[index]))
            <= criteria["high_mode_phase_error_rad_max"]
        )
        conventional_error = abs(conventional_modes[index] - truth_modes[index])
        actual_error = abs(coefficients[index] - truth_modes[index])
        assert (
            conventional_error >= criteria["high_mode_error_improvement_factor_min"] * actual_error
        )
        assert abs(conventional_modes[index]) <= criteria[
            "conventional_high_mode_fraction_max"
        ] * abs(truth_modes[index])
    assert np.linalg.norm(actual - truth) <= criteria[
        "global_relative_l2_error_max"
    ] * np.linalg.norm(truth)
    # Signed image requirement is separate from mathematical equivalence.
    assert np.min(actual) < criteria["signed_min_upper"]
    assert np.max(actual) > criteria["signed_max_lower"]


def test_independent_matched_physical_recovery_through_workflow() -> None:
    # This is the ONLY product call chain in the new checkpoint. Invocation
    # waits for fresh B. No product import occurs at module import/freeze time.
    from simrecon import declare_otf, reconstruct_workflow

    p = registration()
    h = transfer_table(p)
    assert_transfer_regeneration(h, p)
    assert hashlib.sha256(h.astype("<c16", copy=False).tobytes()).hexdigest() == TRANSFER_SHA256
    data = acquire(p, h)
    assert data["raw"].shape == tuple(p["shape_TDPZYX"])
    assert hashlib.sha256(data["raw"].astype("<f4", copy=False).tobytes()).hexdigest() == RAW_SHA256
    observer = physical_observer_bounds(p, h)
    assert_float32_rounding(data["raw"], data["unquantized_raw"], observer["unquantized_raw"])
    reference = expected(p, data["raw"], h)
    written = np.stack([build["written"] for build in reference["builds"]])
    assert hashlib.sha256(written.tobytes()).hexdigest() == OVERLAP_WRITTEN_SHA256
    error = bounds(data["raw"], h, p, reference)
    truth_modes = project(data["truth"], p)
    image_modes = project(reference["image"], p)
    conventional_modes = project(conventional(data["raw"]), p)
    _, response = mode_response(p, h)
    assert np.all(response > 0.98)
    # Physical frequency support is independent of the output grid pitch.
    for row in p["source"]["high_mode_indices"]:
        kx, ky, *_ = p["source"]["positive_modes_kxyz_real_imag"][row]
        radius = np.hypot(kx / 8, ky / 8)
        assert 0.5 < radius < 0.75
        assert np.hypot((kx - 2) / 8, ky / 8) < 0.5

    acquisition = {
        "acquisition_mode": "3d",
        **p["sampling"],
        "norders": 3,
        "background": 7.0,
        "flatfield_slope": np.full((8, 8), 2.0),
        "phase_policy": "uniform",
        "phases_rad": None,
        "phase_steps_rad": None,
        "edge_pixels": 0,
        "equalize": False,
        "equalize_z": False,
        "equalize_time": False,
        "storage_order": "direction-major",
        "combine_off_orders": None,
        "drift_between": False,
        "drift_within": False,
        "fit_drift": False,
        "adjust_phases": False,
        "drift_filter_fraction": 0.0,
    }
    transfer = declare_otf(h, layout="radial", dkr_cyc_um=0.125, dkz_cyc_um=0.25)
    raw = data["raw"].copy()
    untouched = raw.copy()
    actual = reconstruct_workflow(
        raw,
        acquisition=acquisition,
        optics=p["optics"],
        carrier=p["carrier"],
        filtering=p["filtering"],
        transfer=transfer,
        specimen_identity={
            "id": p["version"],
            "intensity_unit": "calibrated-differential-detector-count",
        },
        transfer_identity={
            "id": p["version"] + "-matched-transfer",
            "intensity_unit": "dimensionless-transfer",
            "optics": p["optics"],
        },
        exposure_background=np.full((1, 1, 5, 4), 3.0),
        calibration=None,
        off_exposures=None,
        header_timestamps=None,
        header_timestamp_unit=None,
        header_phases_rad=None,
        channel_index=None,
        plane_policy="native",
    )
    np.testing.assert_array_equal(raw, untouched)
    assert actual.image.shape == (1, 4, 16, 16)
    assert actual.image.dtype == np.dtype("float64")
    assert not actual.image.flags.writeable
    assert actual.calibration is None and actual.layout is None
    assert actual.bands.input_shape == (1, 1, 5, 4, 8, 8)
    assert actual.bands.input_scale == 1 / 1024
    assert actual.bands.sentinel_frames == ()
    close(actual.bands.noise_variance_factors, np.ones((1, 1, 3)), 0)
    close(actual.bands.equalization_gains, np.ones((1, 1, 5, 4)), 0)
    close(actual.bands.quadratures[0, 0], reference["bands"], error["bands_atol"])
    close(actual.transfer.samples, h, 0)
    close(actual.initial_carriers_cyc_um, [[0.125, 0]], 0)
    close(actual.phase_linkage_carriers_cyc_um, [[0.25, 0]], 0)
    close(actual.parameters.carriers_cyc_um, [[[0.125, 0]]], 0)
    assert actual.parameters.branches == (("known",),)
    close(
        actual.parameters.raw_modulation[0, 0],
        reference["modulation"],
        error["modulation_atol"],
    )
    close(actual.parameters.modulation[0, 0], reference["modulation"], error["modulation_atol"])
    assert len(actual.parameters.overlaps) == 2
    for m, observed in enumerate(actual.parameters.overlaps, 1):
        assert observed.index == m - 1
        assert observed.time_index == observed.direction_index == 0
        assert observed.purpose == "known" and observed.orders == (0, m)
        close(observed.carrier_cyc_um, [0.125, 0], 0)
        build = reference["builds"][m - 1]
        for key in ("fourier", "spatial"):
            close(getattr(observed, key), build[key], error["overlap_atol"])
        np.testing.assert_array_equal(observed.written, build["written"])
    assert [event.kind for event in actual.parameters.trace] == [
        "evaluation",
        "evaluation",
        "adjustment",
        "adjustment",
    ]
    for m, event in enumerate(actual.parameters.trace[:2], 1):
        details = dict(event.details)
        assert details["stage"] == "known" and details["orders"] == (0, m)
        assert details["objective"] is None
        assert details["angle_rad"] is None and details["magnitude_cyc_um"] is None
        assert details["overlap_index"] == m - 1
        fitted = reference["fits"][m - 1]
        energy = error["energies"][m - 1]
        for key in ("SX", "SY", "cross"):
            close(details[key], fitted[key], energy[key + "_error"])
        close(details["forward"], fitted["forward"], error["modulation_atol"])
    for m, event in enumerate(actual.parameters.trace[2:], 1):
        details = dict(event.details)
        assert details["order"] == m and details["floor"] is None
        assert details["floor_applied"] is False and details["phase_replaced"] is False
        for key in ("raw_forward", "after_floor", "final"):
            close(details[key], reference["modulation"][m - 1], error["modulation_atol"])
    assert len(actual.reconstructions) == 1
    known = actual.reconstructions[0]
    close(known.modulation, actual.parameters.modulation[0], 0)
    close(known.carriers_cyc_um, actual.parameters.carriers_cyc_um[0], 0)
    close(known.filtered_quadratures[0, 0], reference["filtered"], error["filtered_atol"])
    close(actual.image[0], reference["image"], error["image_atol"])
    close(known.image, actual.image, 0)
    for name, values in zip(("x_um", "y_um", "z_um"), coordinates(True), strict=True):
        close(getattr(actual, name), values, 0)
    close(actual.effective_wiener, [0.002], 0)
    assert [event.kind for event in actual.trace] == [
        "declaration",
        "layout",
        "transfer",
        "preparation",
        "estimation",
        "reconstruction",
        "result",
    ]
    assert actual.intensity_unit == "calibrated-differential-detector-count"
    assert actual.intensity_semantics == "C-scaled-camera-corrected-equalized-phase-reconstruction"
    assert "historical-binary-agreement-unqualified" in actual.limitations
    assert "input-unit-label-not-specimen-mass" in actual.limitations
    close(project(actual.image[0], p), image_modes, error["mode_atol"])
    # Extra DC assertion constrains normalization independently of full-L2
    # recovery. No mode/plane is dropped and no fitted rescale is allowed.
    close(np.mean(actual.image), image_modes[0].real, error["mode_atol"])
    assert_recovery(actual.image[0], conventional_modes, truth_modes, data["truth"], p)
    # The independent signed residual/mode arrays and explicit capture()
    # provide later presentation. No writes or runtime seam are added here.
    assert gamma(256) < error["mode_atol"] < 0.001
