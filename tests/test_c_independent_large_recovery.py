"""CE08 I03-I10: new larger physical D3/axial study through actual workflow.

Execution is authorized only after fresh B accepts this complete frozen
checkpoint. Collection imports no product. The frozen expectation is independent
of every product result. No test-only runtime seam or observer side effect.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from ce08_recovery_large_budget import (
    assert_observer_arrays,
    assert_transfer_observer,
    bounds,
    observer_bounds,
)
from ce08_recovery_large_freeze import assert_recovery, recovery_metrics
from ce08_recovery_large_model import (
    FIXTURE,
    SPEC,
    acquire,
    carriers,
    conventional,
    coordinates,
    physical_response,
    project,
    registration,
    transfer_table,
)

# Filled once from the oracle-only preregistration, before product execution.
SPEC_SHA256 = "49a02fb01bedc4632a11b0f1f6b5d632296f1a5b2faa7f2fe265de7c8f5207aa"
FIXTURE_SHA256 = "3a2cef38a43413cfc29f3159c28f3d0ce6c4c8c431a63b97561319f676d3ae06"


def close(actual: Any, expected: Any, atol: float) -> None:
    np.testing.assert_allclose(actual, expected, rtol=0, atol=atol)


def test_independent_large_d3_axial_recovery_through_workflow() -> None:
    # The only new product call chain; do not execute before fresh complete B.
    from simrecon import declare_otf, reconstruct_workflow

    assert hashlib.sha256(SPEC.read_bytes()).hexdigest() == SPEC_SHA256
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == FIXTURE_SHA256
    p = registration()
    h, k = transfer_table(p), carriers(p)
    with np.load(FIXTURE, allow_pickle=False) as frozen:
        assert_transfer_observer(h, frozen["transfer"])
        observer = observer_bounds(p, h, frozen["raw"])
        assert_observer_arrays(acquire(p, h), frozen, observer)
        close(conventional(frozen["raw"]), frozen["conventional"], observer["conventional_atol"])
        # Reproduce the conditional bound from immutable full oracle arrays;
        # no expensive duplicate full finite reconstruction is needed here.
        builds = []
        for i in range(6):
            builds.append(
                {
                    "spatial": frozen[f"overlap{i}_spatial"],
                    "forward": frozen["modulation"].ravel()[i],
                }
            )
        ref = {
            "bands": frozen["bands"],
            "modulation": frozen["modulation"],
            "filtered": frozen["filtered"],
            "density_image": frozen["expected_density_image"],
            "builds": builds,
        }
        error = bounds(frozen["raw"], h, p, ref)
        power, response = physical_response(p, h)
        assert np.all(abs(power - frozen["mode_power"]) <= observer["mode_power_atol"])
        assert np.all(abs(response - frozen["ideal_response"]) <= observer["ideal_response_atol"])
        assert response.min() > 0.98
        assert frozen["wrong_per_direction_denominator_response"][0] > 2.99
        for row in p["source"]["high_mode_indices"]:
            mode = p["source"]["positive_modes_kxyz_real_imag"][row]
            assert 0.5 < np.hypot(mode[0] / 24, mode[1] / 24) < 0.5 + 2 * (5 / 24)
        assert np.any(frozen["signed_source_bins"][:, 2] != 0)
        assert frozen["raw"].dtype == np.dtype("float32")

        acquisition = {
            "acquisition_mode": "3d",
            **p["sampling"],
            **p["preparation"],
            "norders": 3,
            "flatfield_slope": np.full((24, 24), 2.0),
        }
        # These belong to explicit workflow arguments, not its mapping schema.
        del acquisition["exposure_background"]
        del acquisition["off_exposures"]
        transfer = declare_otf(h, layout="radial", dkr_cyc_um=1 / 24, dkz_cyc_um=1 / 8)
        raw = frozen["raw"].copy()
        untouched = raw.copy()
        actual = reconstruct_workflow(
            raw,
            acquisition=acquisition,
            optics=p["optics"],
            carrier={**p["carrier"], "angles_rad": np.array(p["carrier"]["angles_rad"])},
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
            exposure_background=np.full((1, 3, 5, 8), 3.0),
            calibration=None,
            off_exposures=None,
            header_timestamps=None,
            header_timestamp_unit=None,
            header_phases_rad=None,
            channel_index=None,
            plane_policy="native",
        )
        np.testing.assert_array_equal(raw, untouched)
        assert actual.image.shape == (1, 8, 48, 48)
        assert actual.image.dtype == np.dtype("float64") and not actual.image.flags.writeable
        assert actual.calibration is None and actual.layout is None
        assert actual.bands.input_shape == (1, 3, 5, 8, 24, 24)
        assert actual.bands.input_scale == 1 / 55296
        assert actual.bands.sentinel_frames == ()
        close(actual.bands.noise_variance_factors, np.ones((1, 3, 3)), 0)
        close(actual.bands.equalization_gains, np.ones((1, 3, 5, 8)), 0)
        close(actual.bands.quadratures[0], frozen["bands"], error["bands_atol"])
        close(actual.transfer.samples, h, 0)
        close(actual.initial_carriers_cyc_um, k, error["eta"])
        # Linkage ignores explicit angles; actual estimator carrier uses them.
        linkage = (1 / 2.4) * np.array(
            [(np.cos(d * np.pi / 3), np.sin(d * np.pi / 3)) for d in range(3)]
        )
        close(actual.phase_linkage_carriers_cyc_um, linkage, error["eta"])
        close(actual.parameters.carriers_cyc_um[0], k, error["eta"])
        assert actual.parameters.branches == (("known", "known", "known"),)
        close(actual.parameters.raw_modulation[0], frozen["modulation"], error["modulation_atol"])
        close(actual.parameters.modulation[0], frozen["modulation"], error["modulation_atol"])
        assert len(actual.parameters.overlaps) == 6
        for i, observed in enumerate(actual.parameters.overlaps):
            d, m = i // 2, i % 2 + 1
            assert (
                observed.index == i and observed.time_index == 0 and observed.direction_index == d
            )
            assert observed.purpose == "known" and observed.orders == (0, m)
            close(observed.carrier_cyc_um, k[d], error["eta"])
            for name in ("fourier", "spatial"):
                close(getattr(observed, name), frozen[f"overlap{i}_{name}"], error["overlap_atol"])
            np.testing.assert_array_equal(observed.written, frozen[f"overlap{i}_written"])
        trace = actual.parameters.trace
        assert [event.kind for event in trace] == [
            "evaluation",
            "evaluation",
            "adjustment",
            "adjustment",
        ] * 3
        for d in range(3):
            for m in (1, 2):
                i = 2 * d + m - 1
                event = trace[4 * d + m - 1]
                details = dict(event.details)
                assert event.direction_index == d and event.time_index == 0
                assert details["stage"] == "known" and details["orders"] == (0, m)
                assert details["objective"] is None
                assert details["angle_rad"] is None and details["magnitude_cyc_um"] is None
                assert details["overlap_index"] == i
                for j, key in enumerate(("SX", "SY")):
                    close(
                        details[key],
                        frozen[f"fit{i}_real"][j],
                        error["energies"][i][key + "_error"],
                    )
                close(
                    details["cross"],
                    frozen[f"fit{i}_complex"][0],
                    error["energies"][i]["cross_error"],
                )
                close(details["forward"], frozen["modulation"][d, m - 1], error["modulation_atol"])
                adjust = dict(trace[4 * d + 2 + m - 1].details)
                assert adjust["order"] == m and adjust["floor"] is None
                assert adjust["floor_applied"] is False and adjust["phase_replaced"] is False
                for key in ("raw_forward", "after_floor", "final"):
                    close(adjust[key], frozen["modulation"][d, m - 1], error["modulation_atol"])
        assert len(actual.reconstructions) == 1
        known = actual.reconstructions[0]
        close(known.modulation, actual.parameters.modulation[0], 0)
        close(known.carriers_cyc_um, actual.parameters.carriers_cyc_um[0], 0)
        close(known.filtered_quadratures[0], frozen["filtered"], error["filtered_atol"])
        close(known.axial_cutoffs_bins, [1, 2, 1], 0)
        close(actual.image[0], frozen["expected_workflow_image"], error["workflow_image_atol"])
        close(known.image, actual.image, 0)
        for name, values in zip(("x_um", "y_um", "z_um"), coordinates(True), strict=True):
            close(getattr(actual, name), values, 0)
        close(actual.effective_wiener, [0.002], 0)
        assert actual.intensity_unit == "calibrated-differential-detector-count"
        assert (
            actual.intensity_semantics == "C-scaled-camera-corrected-equalized-phase-reconstruction"
        )
        assert "historical-binary-agreement-unqualified" in actual.limitations
        assert "input-unit-label-not-specimen-mass" in actual.limitations
        density = 3 * actual.image[0]  # fixed analytical conversion, never fit
        close(density, frozen["expected_density_image"], error["density_image_atol"])
        close(project(density, p), frozen["expected_modes"], error["mode_atol"])
        # I03/I07 explicit D discriminator independent of whole-image norm.
        close(np.mean(actual.image), frozen["expected_modes"][0].real / 3, error["mode_atol"] / 3)
        assert abs(np.mean(actual.image) - 0.125) > 0.08
        assert_recovery(
            recovery_metrics(
                density, frozen["conventional_modes"], frozen["truth_modes"], frozen["truth"], p
            ),
            p,
        )
        # No plane selection; assertions cover all8*48*48 signed samples and
        # every declared Fourier coefficient. capture() later exports all.
        assert np.all(np.min(density, axis=(1, 2)) < 0)
        assert np.all(np.max(density, axis=(1, 2)) > 0)
