"""Blind A tests for RA12's finite predictive handoff, never identification.

Known candidates are diagnostic controls. Only raw observations, estimated
camera values and declared geometry/settings enter the inference calls.
"""

import importlib
import inspect
import math
import random
import warnings
from dataclasses import FrozenInstanceError, replace
from importlib.metadata import version
from itertools import combinations
from typing import Any

import numpy as np
import pytest
from scripts.image_only_specimen_fit import fit_specimen

from image_only_calibration_handoff_fixture import (
    FIELD_ATOL,
    OPTICAL_BUDGET,
    ORIGIN,
    PHASE_ATOL,
    SD,
    SMALL,
    SPEC,
    SPEC_ORIGIN,
    D,
    alternatives,
    audit_kwargs,
    camera,
    candidate,
    exact_occupied,
    feasible,
    field,
    optical,
    physical_shift,
    physical_transfer,
    prediction,
    unit_source,
)

# |A_Q| <= sum(w)=1; each unit source stores K*RN64(1/K) <= 1+eps.
# T <= sum(B)*pixel_area*pi*(NA/lambda_em)^2*(1+eps).
T_BOUND = float(2.7 * D[1] * D[2] * math.pi * (1.4 / 0.525) ** 2 * (1 + np.finfo(float).eps))
CAL_ATOL = OPTICAL_BUDGET * T_BOUND
INFERENCE_SHAPE = (1, 3, 24)
# Cauchy-Schwarz gives 0<=I< =3 for any nonnegative beam triple.
# This permissive finite-control setting deliberately makes no recovery claim.
PERMISSIVE_OPERATOR = 3 + FIELD_ATOL


@pytest.fixture(scope="module")
def api():
    # Feature absence is a failure, not a skip or a semantic product-red claim.
    return importlib.import_module("scripts.image_only_calibration_handoff")


def audit(api, c=None, **changes):
    options = audit_kwargs(calibration_atol=CAL_ATOL)
    options.update(changes)
    return api.audit_calibration_candidate(candidate() if c is None else c, **options)


def assert_array(value, shape):
    assert type(value) is np.ndarray
    assert value.shape == shape
    assert value.dtype == np.dtype("float64") and value.dtype.isnative
    assert value.flags.c_contiguous and value.flags.writeable and value.flags.owndata
    assert np.all(np.isfinite(value))


def assert_same_candidate(actual, expected):
    for name in ("centers_um_zyx", "brightness_relative", "carriers_yx_per_um", "beam_amplitudes"):
        np.testing.assert_allclose(
            getattr(actual, name), getattr(expected, name), rtol=0, atol=2e-14
        )
    # Wrapping is legal; a fitted phase must not be arbitrarily reset.
    np.testing.assert_allclose(
        np.exp(1j * physical_shift(actual.phases_rad, 0)),
        np.exp(1j * physical_shift(expected.phases_rad, 0)),
        rtol=0,
        atol=PHASE_ATOL,
    )


def assert_selected_specimen_illumination(result, origin=ORIGIN, destination=SPEC_ORIGIN):
    """Tie the consumer payload to its selected candidate, allowing beam scale."""
    c, out = result.candidate, result.specimen
    assert c is not None and out is not None
    expected_q = c.carriers_yx_per_um.copy()
    expected_beams = c.beam_amplitudes.copy()
    expected_phases = physical_transfer(c.phases_rad, expected_q, origin, destination)
    np.testing.assert_array_equal(out.carriers_yx_per_um, expected_q)
    assert np.all(out.beam_amplitudes >= 0) and np.max(out.beam_amplitudes) > 0
    # Normalize only for the comparison: common amplitude is a physical gauge.
    np.testing.assert_allclose(
        out.beam_amplitudes / np.max(out.beam_amplitudes),
        expected_beams / np.max(expected_beams),
        rtol=0,
        atol=2e-14,
    )
    np.testing.assert_allclose(
        out.phases_at_specimen_origin_rad, expected_phases, rtol=0, atol=PHASE_ATOL
    )
    payloads = (out.carriers_yx_per_um, out.phases_at_specimen_origin_rad, out.beam_amplitudes)
    records = [c] + [case.candidate for case in result.audit if case.candidate is not None]
    if result.seed_result is not None:
        records.extend([result.seed_result.initial_candidate, result.seed_result.frozen_candidate])
    for value, shape in zip(payloads, ((3, 2), (3, 5), (3,)), strict=True):
        assert_array(value, shape)
        for record in records:
            if record is not None:
                for selected in (
                    record.centers_um_zyx,
                    record.brightness_relative,
                    record.carriers_yx_per_um,
                    record.phases_rad,
                    record.beam_amplitudes,
                    record.stored_unit_masses_e,
                ):
                    assert not np.shares_memory(value, selected)
    for i, value in enumerate(payloads):
        for other in payloads[i + 1 :]:
            assert not np.shares_memory(value, other)
    return expected_q, expected_phases, expected_beams


def assert_claim(result, kind):
    assert result.input_kind == kind
    assert result.global_operator_identification == "unestablished"
    assert result.status in {
        "predictive_estimate",
        "diagnostic_candidate",
        "unavailable",
        "numerical_incomplete",
    }
    assert isinstance(result.message, str) and result.message.strip()
    p = result.provenance
    assert p["model"] == "ra12_clear_pupil_predictive_handoff_v1"
    assert p["global_operator_identification"] == "unestablished"
    assert p["confidence_guarantee"] is None
    assert p["output_unit"] == "reference_flat_relative"
    assert p["pupil_order"] == 128
    assert p["audit_scope"] == "listed_direct_transformations_only"
    assert p["numpy_version"] == np.__version__
    assert p["scipy_version"] == version("scipy")
    limits = str(p["limitations"]).lower()
    for word in ("finite", "global", "confidence", "synthetic", "source", "inverse"):
        assert word in limits
    if result.status in {"unavailable", "numerical_incomplete"}:
        assert result.specimen is None
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.status = "identified"


def test_independent_field_symmetry_and_one_focus_counterexamples():
    """Analytic positive/negative controls validate the evaluator before product."""
    for beams in ((4.0, 2.0, 1.0), (4.0, 1.0, 1.0)):
        c = candidate(beams=beams)
        alts = dict(alternatives(c))
        f = field(c)
        assert f.shape == (3, 5, 5, 4, 6)
        assert np.min(f) >= -FIELD_ATOL and np.max(f) <= 3 + FIELD_ATOL
        np.testing.assert_allclose(f, field(alts["global"]), rtol=0, atol=FIELD_ATOL)
        root = alts["root"]
        assert root is not None
        assert np.max(np.abs(f - field(root))) > 0.05
        # A Z=1 specimen samples d=0 only: odd-axial ambiguity is harmless there.
        np.testing.assert_allclose(
            field(c, shape=(1, 2, 3)), field(root, shape=(1, 2, 3)), rtol=0, atol=FIELD_ATOL
        )
        if beams[1] != beams[2]:
            assert np.max(np.abs(f - field(alts["beam_swap"]))) > 0.05
        else:
            np.testing.assert_array_equal(f, field(alts["beam_swap"]))
    huge = candidate()
    huge.phases_rad[:] = 1e100
    base = physical_shift(huge.phases_rad, 0)
    for index, (_, shifted) in enumerate(alternatives(huge)[-9:]):
        assert shifted is not None
        orientation = index // 3
        phases = physical_shift(shifted.phases_rad, 0)
        # Chord lengths for quarter/half/three-quarter physical turns are
        # sqrt(2), 2, sqrt(2), independent of the enormous initial angle.
        chord = np.abs(np.exp(1j * phases[orientation]) - np.exp(1j * base[orientation]))
        target = (math.sqrt(2), 2.0, math.sqrt(2))[index % 3]
        np.testing.assert_allclose(chord, target, rtol=0, atol=PHASE_ATOL)
        for other in set(range(3)) - {orientation}:
            np.testing.assert_array_equal(phases[other], base[other])
    # These unit-circle identities use only bounded rotations/conjugation.
    # They independently challenge every complete-expression observer branch.
    original_units = np.exp(1j * base)
    for label, alt in alternatives(huge):
        if alt is None:
            continue
        target = original_units.copy()
        parts = label.split(":")
        if label == "global":
            target = np.conj(target)
        elif parts[0] == "carrier":
            orientation, axis, sign = (int(x) for x in parts[1:])
            turns = sign * huge.centers_um_zyx[0, axis + 1] / (SMALL[axis + 1] * D[axis + 1])
            target[orientation] *= np.exp(-2j * math.pi * turns)
        elif parts[0] == "phase_neg":
            orientation, phase = (int(x) for x in parts[1:])
            target[orientation, phase] = np.conj(target[orientation, phase])
        elif parts[0] == "phase_pi":
            orientation, phase = (int(x) for x in parts[1:])
            target[orientation, phase] *= -1
        elif parts[0] == "common":
            target[int(parts[1])] *= np.exp(1j * float(parts[2]))
        np.testing.assert_allclose(
            np.exp(1j * physical_shift(alt.phases_rad, 0)), target, rtol=0, atol=PHASE_ATOL
        )


def test_fixture_closed_membership_and_public_optical_symmetry():
    c = candidate()
    for center in c.centers_um_zyx:
        src = unit_source(center, SMALL)
        sites = exact_occupied(center)
        expected = np.zeros(tuple(8 * n for n in SMALL))
        for site in sites:
            expected[site] = 1 / len(sites)
        np.testing.assert_array_equal(src, expected)
        # Axial source sites occur in exact equal-weight pairs about focus.
        np.testing.assert_array_equal(src, src[::-1])
    central, train = prediction(c)
    assert 0 < np.max(central) <= T_BOUND
    for label in ("global", "beam_swap", "reflection", "root", "root_swap"):
        alt = dict(alternatives(c))[label]
        assert alt is not None
        ac, at = prediction(alt)
        np.testing.assert_allclose(ac, central, rtol=0, atol=CAL_ATOL)
        np.testing.assert_allclose(at, train, rtol=0, atol=CAL_ATOL)


@pytest.mark.parametrize("beams", [(4.0, 2.0, 1.0), (4.0, 1.0, 1.0)])
def test_single_focus_material_alternatives_block_handoff(api, beams):
    c = candidate(beams=beams)
    result = audit(api, c)
    assert_claim(result, "supplied_candidate_diagnostic")
    assert result.status == "unavailable" and result.stage == "audit"
    assert result.audit_complete is True
    assert result.seed_result is None and result.refinement is None
    assert result.training_rms is None and result.heldout_prediction is None
    cases = result.audit
    expected = alternatives(c)
    assert len(cases) == len(expected)
    assert len({x.case_id for x in cases}) == len(cases)
    reference = field(c)
    central, structured = prediction(c)
    for (label, alt), case in zip(expected, cases, strict=True):
        assert isinstance(case.case_id, str) and case.case_id
        if not feasible(alt):
            assert case.outcome == "infeasible", label
            assert case.candidate is None
            assert case.calibration_max_abs_difference is None
            assert case.operator_max_abs_difference is None
            assert case.calibration_equivalent is None and case.material is None
            continue
        assert alt is not None
        assert_same_candidate(case.candidate, alt)
        assert case.outcome != "numerical_incomplete", label
        delta = case.calibration_max_abs_difference
        assert type(delta) is float and math.isfinite(delta) and delta >= 0
        equivalent = delta <= CAL_ATOL
        assert case.calibration_equivalent is equivalent
        if label in {
            "global",
            "beam_swap",
            "reflection",
            "root",
            "root_swap",
            "center:1:2:-1",
            "component:0:0",
            "phase_pi:0:0",
        }:
            ac, at = prediction(alt)
            independent = max(
                float(np.max(np.abs(ac - central))), float(np.max(np.abs(at - structured)))
            )
            assert abs(delta - independent) <= CAL_ATOL
        if equivalent:
            independent = float(np.max(np.abs(field(alt) - reference)))
            assert abs(case.operator_max_abs_difference - independent) <= FIELD_ATOL
            material = independent > 1e-7
            assert case.material is material
            assert case.outcome == ("material_alternative" if material else "equivalent_harmless")
        else:
            assert case.outcome == "calibration_distinct"
            assert case.material is False
    # The first is a harmless global gauge; balanced side swap alone proves
    # nothing about the distinct beam-root material alternative.
    assert cases[0].outcome == "equivalent_harmless"
    assert cases[3].outcome == "material_alternative"
    if beams[1] != beams[2]:
        assert cases[1].outcome == "material_alternative"
    else:
        assert cases[1].outcome == "equivalent_harmless"
    assert any(case.material for case in cases)
    # Audit candidates are real independently retained diagnostic payloads.
    # An unchanged phase array is still a snapshot, never borrowed storage.
    saved_reference = result.candidate.phases_rad.copy()
    saved_other = cases[1].candidate.phases_rad.copy()
    cases[0].candidate.phases_rad[:] = -123.0
    np.testing.assert_array_equal(result.candidate.phases_rad, saved_reference)
    np.testing.assert_array_equal(cases[1].candidate.phases_rad, saved_other)


def test_audit_full_field_uses_declared_geometry_and_threshold_equality(api):
    c = candidate()
    # At one focus beam ambiguity is harmless; at displaced foci it is material.
    one = audit(api, c, specimen_detector_shape_zyx=(1, 2, 3), operator_atol=1e-7)
    assert one.audit[1].outcome == "equivalent_harmless"
    three = audit(api, c)
    value = three.audit[1].operator_max_abs_difference
    assert value > 0.05
    boundary = audit(api, c, operator_atol=value)
    assert boundary.audit[1].outcome == "equivalent_harmless"
    below = audit(api, c, operator_atol=float(np.nextafter(value, 0.0)))
    assert below.audit[1].outcome == "material_alternative"
    # Equality is a computed finite comparison, not a confidence threshold.
    assert boundary.audit[1].calibration_equivalent is True
    assert below.specimen is None


def test_positive_diagnostic_transfer_snapshots_and_real_consumer(api):
    c = candidate()
    cam = camera()
    # The declared permissive operator threshold permits a diagnostic output
    # with unequal beams. The tight control above independently rejects it.
    result = audit(api, c, camera_estimate=cam, operator_atol=PERMISSIVE_OPERATOR)
    assert_claim(result, "supplied_candidate_diagnostic")
    assert result.status == "diagnostic_candidate" and result.stage == "complete"
    assert result.audit_complete and not any(x.material for x in result.audit)
    out = result.specimen
    assert out is not None
    assert out.pupil_order == 128
    assert out.detector_shape_zyx == SPEC
    assert out.detector_spacing_um_zyx == SD
    assert out.source_shape_zyx == (3, 4, 6)
    assert out.source_spacing_um_zyx == (SD[0], SD[1] / 2, SD[2] / 2)
    assert out.specimen_origin_um_zyx == SPEC_ORIGIN
    np.testing.assert_array_equal(result.candidate.carriers_yx_per_um, c.carriers_yx_per_um)
    np.testing.assert_allclose(
        result.candidate.beam_amplitudes / np.max(result.candidate.beam_amplitudes),
        c.beam_amplitudes / np.max(c.beam_amplitudes),
        rtol=0,
        atol=2e-14,
    )
    expected_q, _, expected_beams = assert_selected_specimen_illumination(result)
    expected_phases = physical_transfer(c.phases_rad, c.carriers_yx_per_um, ORIGIN, SPEC_ORIGIN)
    np.testing.assert_allclose(
        out.phases_at_specimen_origin_rad, expected_phases, rtol=0, atol=PHASE_ATOL
    )
    assert result.provenance["phase_transfer"]["application_count"] == 1
    assert result.provenance["source"] == " RA12 supplied diagnostic "
    assert result.provenance["controls"]["training_rms_limit"] is None
    assert result.provenance["controls"]["max_refinement_evaluations"] is None
    # Candidate profile metadata must come from rebuilt geometry, not stale input.
    counts = tuple(len(exact_occupied(x)) for x in c.centers_um_zyx)
    assert result.candidate.occupied_counts == counts
    np.testing.assert_allclose(
        result.candidate.stored_unit_masses_e, [k * (1 / k) for k in counts], rtol=0, atol=1e-14
    )
    arrays = [
        result.candidate.centers_um_zyx,
        result.candidate.brightness_relative,
        result.candidate.carriers_yx_per_um,
        result.candidate.phases_rad,
        result.candidate.beam_amplitudes,
        result.candidate.stored_unit_masses_e,
        out.carriers_yx_per_um,
        out.phases_at_specimen_origin_rad,
        out.beam_amplitudes,
        out.camera_estimate.means_counts,
        result.provenance["camera"]["means_counts"],
    ]
    for i, arr in enumerate(arrays):
        assert_array(arr, arr.shape)
        for other in arrays[i + 1 :]:
            assert not np.shares_memory(arr, other)
        for source in (
            c.centers_um_zyx,
            c.brightness_relative,
            c.carriers_yx_per_um,
            c.phases_rad,
            c.beam_amplitudes,
            cam.means_counts,
        ):
            assert not np.shares_memory(arr, source)
    assert out.camera_estimate.gain_counts_per_e is None
    # Use a nonzero off-center finite specimen on the actual half-cell basis.
    src = np.zeros(out.source_shape_zyx)
    src[0, 1, 4], src[2, 3, 0] = 0.4, 0.8
    means = optical(
        src,
        expected_q,
        expected_phases,
        expected_beams,
        spacing=SD,
        refinement=(1, 2, 2),
    )
    raw = cam.means_counts[1] + cam.contrast_counts * means
    fit = fit_specimen(
        raw,
        camera_estimate=out.camera_estimate,
        carriers_yx_per_um=out.carriers_yx_per_um,
        phases_at_specimen_origin_rad=out.phases_at_specimen_origin_rad,
        beam_amplitudes=out.beam_amplitudes,
        illumination_source=out.illumination_source,
        detector_spacing_um_zyx=out.detector_spacing_um_zyx,
        specimen_origin_um_zyx=out.specimen_origin_um_zyx,
        pupil_order=out.pupil_order,
        regularization=0.01,
        max_iterations=1,
        max_backtracking_trials=8,
    )
    assert fit.status == "completed_finite_fit"
    assert fit.source_shape_zyx == out.source_shape_zyx
    assert fit.best_score is not None and fit.initial_score is not None
    assert fit.source_relative is not None
    assert fit.best_score.total_objective < fit.initial_score.total_objective
    assert np.any(fit.source_relative > 0)
    np.testing.assert_array_equal(
        fit.phases_at_specimen_origin_rad, out.phases_at_specimen_origin_rad
    )
    # Candidate zero has exactly zero prediction and penalty. Its complete
    # public score therefore independently checks one camera correction.
    target_zero_score = math.fsum(float(x) ** 2 for x in means.flat) / (2 * means.size)
    assert abs(fit.initial_score.data_objective - target_zero_score) <= 1e-12
    # Snapshot retention under caller mutation, including camera consumed values.
    saved = tuple(
        a.copy()
        for a in (out.carriers_yx_per_um, out.phases_at_specimen_origin_rad, out.beam_amplitudes)
    )
    c.phases_rad[:] = 99
    c.carriers_yx_per_um[:] = 0
    c.beam_amplitudes[:] = 9
    result.candidate.phases_rad[:] = -42
    result.candidate.carriers_yx_per_um[:] = -0.1
    result.candidate.beam_amplitudes[:] = 3
    cam.means_counts[:] = -99
    for actual, expected in zip(
        (out.carriers_yx_per_um, out.phases_at_specimen_origin_rad, out.beam_amplitudes),
        saved,
        strict=True,
    ):
        np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(out.camera_estimate.means_counts, [-2, 7, 11])


@pytest.mark.parametrize(
    "origin,destination,huge_phase",
    [
        ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), False),
        ((1.0, -1e308, 1e308), (-1.0, 1e308, -1e308), False),
        (ORIGIN, SPEC_ORIGIN, True),
    ],
)
def test_physical_period_complete_origin_difference_and_huge_phase(
    api, origin, destination, huge_phase
):
    c = candidate(beams=(1.0, 0.0, 0.0))
    # Binary-rational q makes enormous coordinate products exactly reducible
    # in cycles even where their unreduced float64 differences overflow.
    c.carriers_yx_per_um[:] = [[0.5, 0.25], [-0.25, 0.5], [1.0, -0.5]]
    if huge_phase:
        c.phases_rad[:] = 1e100
    result = audit(api, c, calibration_origin_um_zyx=origin, specimen_origin_um_zyx=destination)
    assert result.status == "diagnostic_candidate"
    expected = physical_transfer(c.phases_rad, c.carriers_yx_per_um, origin, destination)
    np.testing.assert_allclose(
        result.specimen.phases_at_specimen_origin_rad, expected, rtol=0, atol=PHASE_ATOL
    )
    assert np.all(result.specimen.phases_at_specimen_origin_rad >= -math.pi)
    assert np.all(result.specimen.phases_at_specimen_origin_rad < math.pi)
    if huge_phase:
        # The pi alternative must remain a real pi shift even at huge input.
        shifted = result.audit[42].candidate  # phase_pi orientation 0, exposure 0
        assert shifted is not None
        phase = physical_transfer(shifted.phases_rad, c.carriers_yx_per_um, origin, origin)[0, 0]
        base = physical_transfer(c.phases_rad, c.carriers_yx_per_um, origin, origin)[0, 0]
        assert abs(abs(phase - base) - math.pi) < PHASE_ATOL
        # All nine common shifts must survive huge-input rounding. Compare
        # every exposure, including the four not transferred to the specimen.
        expected_cases = alternatives(c)
        assert len(result.audit) == len(expected_cases)
        for index in range(len(expected_cases) - 9, len(expected_cases)):
            label, expected_candidate = expected_cases[index]
            assert label.startswith("common:") and expected_candidate is not None
            actual = result.audit[index].candidate
            assert actual is not None
            assert_same_candidate(actual, expected_candidate)
            orientation = (index - (len(expected_cases) - 9)) // 3
            actual_phases = physical_shift(actual.phases_rad, 0)
            original = physical_shift(c.phases_rad, 0)
            assert (
                np.max(
                    np.abs(
                        np.exp(1j * actual_phases[orientation]) - np.exp(1j * original[orientation])
                    )
                )
                > 1.0
            )
            for other in set(range(3)) - {orientation}:
                np.testing.assert_allclose(
                    actual_phases[other], original[other], rtol=0, atol=PHASE_ATOL
                )
        # Cover every phase-changing family coherently, including the complete
        # bead-0 anchor subtraction for feasible carrier-frequency alternatives.
        carrier_count = 0
        for (label, expected_candidate), case in zip(expected_cases, result.audit, strict=True):
            changes_phase = label == "global" or label.startswith(
                ("carrier:", "phase_neg:", "phase_pi:", "common:")
            )
            if not changes_phase or not feasible(expected_candidate):
                continue
            assert expected_candidate is not None and case.candidate is not None
            assert_same_candidate(case.candidate, expected_candidate)
            if label.startswith("carrier:"):
                carrier_count += 1
                orientation = int(label.split(":")[1])
                phases = physical_shift(case.candidate.phases_rad, 0)
                original = physical_shift(c.phases_rad, 0)
                assert (
                    np.max(
                        np.abs(
                            np.exp(1j * phases[orientation]) - np.exp(1j * original[orientation])
                        )
                    )
                    > 0.5
                )
                for other in set(range(3)) - {orientation}:
                    np.testing.assert_allclose(
                        phases[other], original[other], rtol=0, atol=PHASE_ATOL
                    )
        assert carrier_count > 0


@pytest.fixture(scope="module")
def raw_control():
    c = candidate(beams=(1.0, 0.0, 0.0), shape=INFERENCE_SHAPE)
    central, structured = prediction(c, INFERENCE_SHAPE)
    cam = camera()
    # Explicit noiseless mathematical acquisition. No means or true parameters
    # are passed separately to the estimator. Fixed signed tail excursions test
    # that the objective includes all pixels and never clips observations.
    raw_c = 7 + 4 * central
    raw_s = 7 + 4 * structured
    raw_s[:, :, 0, 0, 0] = -9.0
    held = 7 + 4 * structured[:, :5]
    return raw_c, raw_s, held, cam


def infer_kwargs(raw_control, **changes):
    central, structured, held, cam = raw_control
    options: dict[str, Any] = dict(
        structured_counts=structured,
        heldout_counts=held,
        camera_estimate=cam,
        calibration_origin_um_zyx=ORIGIN,
        specimen_detector_shape_zyx=(1, 1, 2),
        specimen_detector_spacing_um_zyx=SD,
        specimen_origin_um_zyx=SPEC_ORIGIN,
        sweep_scales=(float(np.nextafter(0.0, 1.0)),),
        max_refinement_evaluations=1,
        # Declared broad control: acceptance is finite predictive plumbing,
        # not accuracy, convergence or scientific operator identification.
        training_rms_limit=1e6,
        calibration_atol=CAL_ATOL,
        operator_atol=PERMISSIVE_OPERATOR,
        source="RA12 observation control",
    )
    options.update(changes)
    return central, options


def training_loss_expectation(c, central, structured, cam):
    """Compute one candidate's full loss and its own optical/reduction bounds."""
    pc, ps = prediction(c, central.shape)
    yc = (central - cam.means_counts[1]) / cam.contrast_counts
    ys = (structured - cam.means_counts[1]) / cam.contrast_counts
    rc, rs = pc - yc, ps - ys
    m = central.size * 28
    target = (
        math.fsum(float(x) ** 2 for x in rc.flat) + math.fsum(float(x) ** 2 for x in rs.flat)
    ) / (2 * m)
    maxr = max(float(np.max(np.abs(rc))), float(np.max(np.abs(rs))))
    peak_bound = (
        math.fsum(float(b) for b in c.brightness_relative)
        * D[1]
        * D[2]
        * math.pi
        * (1.4 / 0.525) ** 2
        * (1 + np.finfo(float).eps)
    )
    e = OPTICAL_BUDGET * peak_bound
    optical_error = e * maxr + e**2 / 2
    # Bound both reduction paths conservatively without assuming pairwise sums:
    # M residual squares/additions per path, plus correction/scaling/division.
    # eps rather than eps/2 is conservative; the finite controls have n*eps<1.
    n = 2 * m + 32
    neps = n * np.finfo(float).eps
    assert neps < 1
    reduction_error = neps / (1 - neps) * (maxr + e) ** 2 / 2
    reduction_error += n * float.fromhex("0x0.0000000000001p-1022")
    return target, optical_error, reduction_error


def check_refinement(result, central, structured, cam, *, evaluation_limit=1):
    r = result.refinement
    assert r is not None and isinstance(r.message, str) and r.message
    scored = [x for x in r.trace if x.outcome == "scored"]
    assert scored and r.objective_evaluations == len(r.trace)
    assert r.successful_evaluations == len(scored)
    assert r.infeasible_evaluations == sum(x.outcome == "infeasible" for x in r.trace)
    assert [x.evaluation_index for x in r.trace] == list(
        range(r.trace[0].evaluation_index, r.trace[0].evaluation_index + len(r.trace))
    )
    best = min(scored, key=lambda x: x.objective)
    assert r.best_objective == best.objective
    assert r.best_evaluation_index == best.evaluation_index
    assert r.initial_objective == scored[0].objective
    assert r.best_objective <= r.initial_objective
    for item in r.trace:
        assert item.outcome in {"scored", "infeasible", "numerical_incomplete"}
        if item.outcome == "scored":
            assert (
                type(item.objective) is float
                and item.objective >= 0
                and math.isfinite(item.objective)
            )
        else:
            assert item.objective is None
        with pytest.raises((FrozenInstanceError, AttributeError)):
            item.objective = -1
    assert r.nfev is None or type(r.nfev) is int
    assert r.njev is None or type(r.njev) is int
    assert r.nfev is None or 0 < r.nfev <= evaluation_limit
    # Independently recompute full signed loss for the returned candidate,
    # including central and every one of the 27 complete structured images.
    target, selected_optical, selected_reduction = training_loss_expectation(
        result.candidate, central, structured, cam
    )
    assert abs(r.best_objective - target) <= selected_optical + selected_reduction
    assert abs(result.training_rms - math.sqrt(2 * r.best_objective)) <= 1e-12
    np.testing.assert_array_equal(
        result.candidate.centers_um_zyx, result.seed_result.frozen_candidate.centers_um_zyx
    )
    # Q256/Q512 remain seed diagnostics. The new first score must independently
    # rescore that frozen seed at Q128 against the same complete training data.
    initial_target, seed_optical, seed_reduction = training_loss_expectation(
        result.seed_result.frozen_candidate, central, structured, cam
    )
    assert abs(r.initial_objective - initial_target) <= seed_optical + seed_reduction


def candidate_matches(actual, expected):
    """Match physical payloads without imposing API spelling or phase wrapping."""
    if actual is None or expected is None:
        return actual is expected
    try:
        assert_same_candidate(actual, expected)
    except AssertionError:
        return False
    return True


def check_inference_audit(result, options, shape):
    """Verify direct inventory plus both seed comparisons at the raw boundary."""
    expected = alternatives(result.candidate, shape)
    cases = result.audit
    assert result.audit_complete is True
    assert len(cases) == len(expected) + 2
    assert all(isinstance(case.case_id, str) and case.case_id for case in cases)
    assert len({case.case_id for case in cases}) == len(cases)
    seeds = (result.seed_result.initial_candidate, result.seed_result.frozen_candidate)
    assert all(seed is not None for seed in seeds)
    # Seed cases have no prescribed location/ID spelling. Remove a pair only
    # if its physical payloads match the two retained seeds and the remaining
    # direct cases match the complete prescribed order, including infeasibility.
    eligible = [
        i
        for i, case in enumerate(cases)
        if any(candidate_matches(case.candidate, seed) for seed in seeds)
    ]
    selected_pair = None
    for pair in combinations(eligible, 2):
        payloads = [cases[i].candidate for i in pair]
        if not any(
            all(candidate_matches(payloads[j], order[j]) for j in range(2))
            for order in (seeds, seeds[::-1])
        ):
            continue
        direct = [case for i, case in enumerate(cases) if i not in pair]
        if all(
            candidate_matches(case.candidate, alt if feasible(alt, shape) else None)
            for case, (_, alt) in zip(direct, expected, strict=True)
        ):
            selected_pair = pair
            break
    assert selected_pair is not None
    reference = field(
        result.candidate,
        shape=options["specimen_detector_shape_zyx"],
        spacing=options["specimen_detector_spacing_um_zyx"],
        origin=options["calibration_origin_um_zyx"],
        destination=options["specimen_origin_um_zyx"],
    )
    for case_index, case in enumerate(cases):
        assert case.outcome != "numerical_incomplete"
        if case.candidate is None:
            assert case.outcome == "infeasible"
            assert case.calibration_equivalent is None and case.material is None
            continue
        delta = case.calibration_max_abs_difference
        assert type(delta) is float and math.isfinite(delta) and delta >= 0
        equivalent = delta <= options["calibration_atol"]
        assert case.calibration_equivalent is equivalent
        if not equivalent:
            assert case.outcome == "calibration_distinct" and case.material is False
            continue
        observed = case.operator_max_abs_difference
        assert type(observed) is float and math.isfinite(observed) and observed >= 0
        material = observed > options["operator_atol"]
        assert case.material is material
        assert case.outcome == ("material_alternative" if material else "equivalent_harmless")
        # Independent whole-field values for both seed comparisons. Direct
        # transform physics already has the stronger diagnostic test above.
        if case_index in selected_pair:
            independent = float(
                np.max(
                    np.abs(
                        field(
                            case.candidate,
                            shape=options["specimen_detector_shape_zyx"],
                            spacing=options["specimen_detector_spacing_um_zyx"],
                            origin=options["calibration_origin_um_zyx"],
                            destination=options["specimen_origin_um_zyx"],
                        )
                        - reference
                    )
                )
            )
            assert abs(observed - independent) <= FIELD_ATOL
    pc, ps = prediction(result.candidate, shape)
    for i in selected_pair:
        sc, ss = prediction(cases[i].candidate, shape)
        delta = max(float(np.max(np.abs(sc - pc))), float(np.max(np.abs(ss - ps))))
        # Two independent response assemblies; candidate brightness sets T.
        mass = max(
            float(np.sum(c.brightness_relative)) for c in (result.candidate, cases[i].candidate)
        )
        error = OPTICAL_BUDGET * mass * D[1] * D[2] * math.pi * (1.4 / 0.525) ** 2
        assert abs(cases[i].calibration_max_abs_difference - delta) <= error + 1e-12
    if any(case.material is True for case in cases):
        assert result.status == "unavailable" and result.stage == "audit"
        assert result.specimen is None


def assert_same_audit(actual, expected):
    assert len(actual) == len(expected)
    for a, b in zip(actual, expected, strict=True):
        for name in (
            "case_id",
            "outcome",
            "calibration_max_abs_difference",
            "operator_max_abs_difference",
            "calibration_equivalent",
            "material",
            "reason",
            "failure_code",
        ):
            assert getattr(a, name) == getattr(b, name)
        assert candidate_matches(a.candidate, b.candidate)


def test_nontrivial_continuous_refinement_beyond_seed_reporting(api, raw_control):
    central, options = infer_kwargs(raw_control, max_refinement_evaluations=3)
    result = api.infer_calibration_handoff(central, **options)
    assert result.status == "predictive_estimate"
    assert_selected_specimen_illumination(result)
    check_refinement(
        result,
        central,
        options["structured_counts"],
        options["camera_estimate"],
        evaluation_limit=3,
    )
    r = result.refinement
    assert r is not None
    assert type(r.status) is int and isinstance(r.message, str) and r.message
    assert type(r.nfev) is int and 0 < r.nfev <= 3
    assert type(r.njev) is int and r.njev > 0
    assert r.successful_evaluations > 1
    assert len([entry for entry in r.trace[1:] if entry.outcome == "scored"]) > 0
    check_inference_audit(result, options, central.shape)


def test_observation_only_material_audit_blocks_and_ignores_heldout(api, raw_control):
    central, options = infer_kwargs(
        raw_control,
        calibration_atol=1e6,
        operator_atol=1e-7,
        specimen_detector_shape_zyx=(3, 1, 2),
    )
    result = api.infer_calibration_handoff(central, **options)
    assert_claim(result, "observations_only")
    check_refinement(result, central, options["structured_counts"], options["camera_estimate"])
    check_inference_audit(result, options, central.shape)
    # A broad calibration comparison is deliberate: test the material blocking
    # decision without imposing parameter recovery or exact calibration symmetry.
    shifted = alternatives(result.candidate, central.shape)[-9][1]
    assert shifted is not None
    geometry = dict(
        shape=options["specimen_detector_shape_zyx"],
        spacing=SD,
        origin=ORIGIN,
        destination=SPEC_ORIGIN,
    )
    delta = float(np.max(np.abs(field(shifted, **geometry) - field(result.candidate, **geometry))))
    assert delta > 0.05
    witnesses = [case for case in result.audit if candidate_matches(case.candidate, shifted)]
    assert witnesses
    for case in witnesses:
        # Independently bound the complete calibration delta, rather than
        # assuming the permissive tolerance makes every possible image equivalent.
        pc, ps = prediction(result.candidate, central.shape)
        ac, ass = prediction(shifted, central.shape)
        cal_delta = max(float(np.max(np.abs(ac - pc))), float(np.max(np.abs(ass - ps))))
        assert cal_delta + CAL_ATOL < options["calibration_atol"]
        assert case.calibration_equivalent is True
        assert abs(case.operator_max_abs_difference - delta) <= FIELD_ATOL
        assert case.material is True and case.outcome == "material_alternative"
    assert result.status == "unavailable" and result.stage == "audit"
    assert result.specimen is None
    changed = api.infer_calibration_handoff(
        central, **{**options, "heldout_counts": options["heldout_counts"] + 2}
    )
    assert_same_candidate(changed.candidate, result.candidate)
    assert changed.refinement == result.refinement
    assert changed.training_rms == result.training_rms
    assert_same_audit(changed.audit, result.audit)
    assert (changed.status, changed.stage, changed.reason_code, changed.audit_complete) == (
        result.status,
        result.stage,
        result.reason_code,
        result.audit_complete,
    )
    assert changed.provenance["controls"] == result.provenance["controls"]
    assert changed.specimen is None


def test_observation_only_finite_refinement_and_heldout_independence(api, raw_control):
    central, options = infer_kwargs(raw_control)
    result = api.infer_calibration_handoff(central, **options)
    assert_claim(result, "observations_only")
    assert result.status == "predictive_estimate" and result.stage == "complete"
    assert result.audit_complete and result.specimen is not None
    assert result.seed_result is not None
    check_refinement(result, central, options["structured_counts"], options["camera_estimate"])
    check_inference_audit(result, options, central.shape)
    expected_q, expected_phases, expected_beams = assert_selected_specimen_illumination(result)
    np.testing.assert_allclose(
        result.specimen.phases_at_specimen_origin_rad,
        physical_transfer(
            result.candidate.phases_rad, result.candidate.carriers_yx_per_um, ORIGIN, SPEC_ORIGIN
        ),
        rtol=0,
        atol=PHASE_ATOL,
    )
    assert result.provenance["phase_transfer"]["application_count"] == 1
    assert_array(result.heldout_prediction, (3, 5, *INFERENCE_SHAPE))
    pc, ps = prediction(result.candidate, INFERENCE_SHAPE)
    np.testing.assert_allclose(result.heldout_prediction, ps[:, :5], rtol=0, atol=CAL_ATOL)
    residual = result.heldout_prediction - (options["heldout_counts"] - 7) / 4
    np.testing.assert_allclose(
        result.heldout_residual_mean, np.mean(residual, axis=(2, 3, 4)), rtol=1e-12, atol=1e-12
    )
    np.testing.assert_allclose(
        result.heldout_residual_rms,
        np.sqrt(np.mean(residual**2, axis=(2, 3, 4))),
        rtol=1e-12,
        atol=1e-12,
    )
    changed = api.infer_calibration_handoff(
        central, **{**options, "heldout_counts": options["heldout_counts"] + 2}
    )
    assert_same_candidate(changed.candidate, result.candidate)
    assert changed.refinement == result.refinement
    assert changed.training_rms == result.training_rms
    assert (changed.status, changed.stage, changed.reason_code, changed.audit_complete) == (
        result.status,
        result.stage,
        result.reason_code,
        result.audit_complete,
    )
    assert_same_audit(changed.audit, result.audit)
    assert changed.provenance["controls"] == result.provenance["controls"]
    assert_selected_specimen_illumination(changed)
    np.testing.assert_array_equal(changed.heldout_prediction, result.heldout_prediction)
    np.testing.assert_allclose(
        changed.heldout_residual_mean, result.heldout_residual_mean - 0.5, rtol=0, atol=1e-12
    )
    np.testing.assert_array_equal(
        changed.specimen.phases_at_specimen_origin_rad,
        result.specimen.phases_at_specimen_origin_rad,
    )
    # Training-limit rejection is a finite declared decision, not a new search.
    rejected = api.infer_calibration_handoff(central, **{**options, "training_rms_limit": 0.0})
    assert rejected.status == "unavailable" and rejected.reason_code == "training_misfit"
    assert rejected.specimen is None
    assert rejected.refinement == result.refinement
    at_limit = api.infer_calibration_handoff(
        central, **{**options, "training_rms_limit": result.training_rms}
    )
    assert at_limit.status == "predictive_estimate"
    assert at_limit.training_rms == result.training_rms
    # Actual inference-to-consumer composition. Evaluator-only acquisition
    # choices are used only AFTER the inferred candidate/predictions freeze.
    out = result.specimen
    truth = candidate(beams=(1.0, 0.0, 0.0), shape=INFERENCE_SHAPE)
    true_phases = physical_transfer(truth.phases_rad, truth.carriers_yx_per_um, ORIGIN, SPEC_ORIGIN)
    source_e = np.zeros(out.source_shape_zyx)
    source_e[0, 0, 2], source_e[0, 1, 0] = 0.6, 0.3
    means = optical(
        source_e,
        truth.carriers_yx_per_um,
        true_phases,
        truth.beam_amplitudes,
        spacing=SD,
        refinement=(1, 2, 2),
    )
    fitted = fit_specimen(
        7 + 4 * means,
        camera_estimate=out.camera_estimate,
        carriers_yx_per_um=out.carriers_yx_per_um,
        phases_at_specimen_origin_rad=out.phases_at_specimen_origin_rad,
        beam_amplitudes=out.beam_amplitudes,
        illumination_source=out.illumination_source,
        detector_spacing_um_zyx=out.detector_spacing_um_zyx,
        specimen_origin_um_zyx=out.specimen_origin_um_zyx,
        pupil_order=out.pupil_order,
        regularization=0.01,
        max_iterations=1,
        max_backtracking_trials=8,
    )
    assert fitted.status == "completed_finite_fit"
    assert fitted.source_relative is not None
    assert fitted.best_score is not None and fitted.initial_score is not None
    assert fitted.best_score.total_objective < fitted.initial_score.total_objective
    # Independently generate unit-electron basis responses, then scale those
    # dimensionless responses by the fitted relative coefficients. Do not
    # relabel relative brightness as electron-valued source input.
    evaluated = np.zeros_like(means)
    for index in np.ndindex(out.source_shape_zyx):
        unit_e = np.zeros(out.source_shape_zyx)
        unit_e[index] = 1.0
        evaluated += float(fitted.source_relative[index]) * optical(
            unit_e,
            expected_q,
            expected_phases,
            expected_beams,
            spacing=SD,
            refinement=(1, 2, 2),
        )
    residual_rms = math.sqrt(
        math.fsum(float(x) ** 2 for x in (evaluated - means).flat) / means.size
    )
    prediction_rms = math.sqrt(math.fsum(float(x) ** 2 for x in evaluated.flat) / means.size)
    peak_bound = (
        math.fsum(float(x) for x in fitted.source_relative.flat)
        * SD[1]
        * SD[2]
        * math.pi
        * (1.4 / 0.525) ** 2
    )
    # Inverse builder/application bound (2e-4+1e-8) plus optical assembly,
    # separate from source-basis error, residual rounding and optimizer error.
    error_rms = (2e-4 + 1e-8) * prediction_rms + OPTICAL_BUDGET * peak_bound
    objective_error = error_rms * residual_rms + error_rms**2 / 2 + 1e-12
    assert abs(fitted.best_score.data_objective - residual_rms**2 / 2) <= objective_error
    saved = tuple(
        a.copy()
        for a in (out.carriers_yx_per_um, out.phases_at_specimen_origin_rad, out.beam_amplitudes)
    )
    result.candidate.carriers_yx_per_um[:] = 0
    result.candidate.phases_rad[:] = 99
    result.candidate.beam_amplitudes[:] = 3
    for actual, expected in zip(
        (out.carriers_yx_per_um, out.phases_at_specimen_origin_rad, out.beam_amplitudes),
        saved,
        strict=True,
    ):
        np.testing.assert_array_equal(actual, expected)


def test_late_heldout_range_retains_frozen_training_and_refinement(api, raw_control):
    central, structured, _, cam = raw_control
    # A valid quarter-count contrast makes the required held-out correction
    # unrepresentable, while ordinary training stays finite and informative.
    cam = replace(cam, contrast_counts=0.25)
    corrected_c, corrected_s = (central - 7) / 4, (structured - 7) / 4
    central = 7 + 0.25 * corrected_c
    structured = 7 + 0.25 * corrected_s
    huge = np.full((3, 5, *INFERENCE_SHAPE), 1e308)
    _, opts = infer_kwargs((central, structured, huge, cam))
    result = api.infer_calibration_handoff(central, **opts)
    assert_claim(result, "observations_only")
    assert result.status == "numerical_incomplete" and result.stage == "heldout"
    assert result.failure_code is not None
    assert result.candidate is not None and result.refinement is not None
    assert result.seed_result.frozen_candidate is not None
    assert all(x is not None for x in result.seed_result.training_objectives_q128_q256_q512)
    assert result.heldout_residual_mean is None and result.heldout_residual_rms is None
    assert result.specimen is None


def test_early_seed_range_is_numerical_incomplete_without_fabricated_training(api):
    shape = (1, 2, 2)
    raw = (
        np.full(shape, 9.0),
        np.full((3, 9, *shape), 9.0),
        np.full((3, 5, *shape), 9.0),
        replace(camera(), contrast_counts=float.fromhex("0x0.0000000000001p-1022")),
    )
    central, options = infer_kwargs(raw)
    # (9-7)/2**-1074 = 2**1075, beyond float64, despite valid finite inputs.
    with np.errstate(all="raise"):
        policy = np.geterr().copy()
        result = api.infer_calibration_handoff(central, **options)
        assert np.geterr() == policy
    assert_claim(result, "observations_only")
    assert result.status == "numerical_incomplete" and result.stage == "seed"
    assert result.failure_code == "image_only_bead_calibration_range"
    seed = result.seed_result
    assert seed is not None
    assert seed.status == "numerical_incomplete" and seed.stage == "normalization"
    assert seed.failure_code == result.failure_code
    assert seed.initial_candidate is None and seed.frozen_candidate is None
    assert seed.training_objectives_q128_q256_q512 == (None, None, None)
    assert result.candidate is None and result.refinement is None and result.specimen is None
    assert result.training_rms is None and result.heldout_prediction is None
    assert result.heldout_residual_mean is None and result.heldout_residual_rms is None


@pytest.mark.parametrize("contrast,central_value", [(0.0, 7.0), (-1.0, -4.0), (4.0, 7.0)])
def test_normalization_and_initialization_unavailable(api, contrast, central_value):
    shape = (1, 2, 2)
    raw = (
        np.full(shape, central_value),
        np.full((3, 9, *shape), 7.0),
        np.full((3, 5, *shape), 7.0),
        replace(camera(), contrast_counts=contrast),
    )
    central, options = infer_kwargs(raw)
    result = api.infer_calibration_handoff(central, **options)
    assert_claim(result, "observations_only")
    assert result.status == "unavailable" and result.stage == "seed"
    assert result.candidate is None and result.refinement is None and result.specimen is None
    assert result.failure_code is None


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("specimen_detector_shape_zyx", [1, 2, 3]),
        ("specimen_detector_shape_zyx", (True, 2, 3)),
        ("specimen_detector_shape_zyx", (1, 0, 3)),
        ("specimen_detector_shape_zyx", (np.int64(1), 2, 3)),
        ("specimen_detector_spacing_um_zyx", (1.0, 0.0, 1.0)),
        ("specimen_detector_spacing_um_zyx", (1.0, np.float64(1), 1.0)),
        ("specimen_detector_spacing_um_zyx", (1.0, float("inf"), 1.0)),
        ("specimen_origin_um_zyx", (1, True, 3)),
        ("calibration_origin_um_zyx", (1, 2, float("nan"))),
        ("calibration_atol", 0.0),
        ("calibration_atol", True),
        ("calibration_atol", np.float64(0.1)),
        ("operator_atol", -1),
        ("operator_atol", 10**400),
        ("source", "  "),
        ("source", None),
    ],
)
def test_new_metadata_validates_before_unavailable(api, field_name, value):
    opts = audit_kwargs(camera_estimate=replace(camera(), contrast_counts=0.0))
    opts[field_name] = value
    with pytest.raises(Exception) as error:
        api.audit_calibration_candidate(candidate(), **opts)
    assert getattr(error.value, "code", None) == "invalid_calibration_handoff"


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("max_refinement_evaluations", 0),
        ("max_refinement_evaluations", True),
        ("max_refinement_evaluations", 1.0),
        ("training_rms_limit", -1),
        ("training_rms_limit", float("inf")),
        ("training_rms_limit", np.float64(1)),
        ("sweep_scales", ()),
        ("sweep_scales", (0.0,)),
        ("structured_counts", np.zeros((3, 8, 1, 2, 2))),
        ("heldout_counts", np.full((3, 5, 1, 2, 2), float("nan"))),
    ],
)
def test_inference_validation_precedes_normalization(api, field_name, value):
    raw = (
        np.zeros((1, 2, 2)),
        np.zeros((3, 9, 1, 2, 2)),
        np.zeros((3, 5, 1, 2, 2)),
        replace(camera(), contrast_counts=0.0),
    )
    central, options = infer_kwargs(raw)
    options[field_name] = value
    with pytest.raises(Exception) as error:
        api.infer_calibration_handoff(central, **options)
    assert getattr(error.value, "code", None) in {
        "invalid_calibration_handoff",
        "invalid_image_only_bead_calibration",
    }


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("centers_um_zyx", np.zeros((2, 3))),
        ("centers_um_zyx", np.array([[0.0625, 0.12, 0.08]] * 3)),
        (
            "centers_um_zyx",
            np.array([[0.01, 0.12, 0.08], [0.0625, 0.12, 0.28], [0.0625, 0.12, 0.48]]),
        ),
        ("brightness_relative", np.array([-1.0, 1.0, 1.0])),
        ("carriers_yx_per_um", np.full((3, 2), 4.0)),
        ("phases_rad", np.zeros((3, 9), dtype=complex)),
        ("beam_amplitudes", np.zeros(3)),
        ("beam_amplitudes", np.array([1.0, -1.0, 0.0])),
        ("beam_amplitudes", np.array([1.0, float("nan"), 0.0])),
    ],
)
def test_candidate_direct_construction_authenticates_nothing(api, field_name, value):
    c = replace(candidate(), **{field_name: value})
    with pytest.raises(Exception) as error:
        audit(api, c)
    assert getattr(error.value, "code", None) == "invalid_calibration_handoff"


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("means_counts", np.zeros(2)),
        ("means_counts", np.zeros(3, dtype=">f8")),
        ("contrast_counts", True),
        ("source", "\t"),
    ],
)
def test_camera_consumed_fields_are_validated(api, field_name, value):
    cam = replace(camera(), **{field_name: value})
    with pytest.raises(Exception) as error:
        audit(api, camera_estimate=cam)
    assert getattr(error.value, "code", None) in {
        "invalid_calibration_handoff",
        "invalid_image_only_bead_calibration",
    }


@pytest.mark.parametrize("layout", ["endian", "fortran", "strided", "readonly", "integer"])
def test_legal_representations_preserved_and_unconsumed_camera_opaque(api, layout):
    c = candidate(beams=(1.0, 0.0, 0.0))
    original = c.phases_rad.copy()
    arrays = {}
    for name in (
        "centers_um_zyx",
        "brightness_relative",
        "carriers_yx_per_um",
        "phases_rad",
        "beam_amplitudes",
    ):
        a = getattr(c, name)
        if layout == "endian":
            a = a.astype(">f8")
        elif layout == "fortran":
            a = np.asfortranarray(a)
        elif layout == "strided":
            storage = np.zeros((*a.shape, 2))
            storage[..., 0] = a
            a = storage[..., 0]
        elif layout == "readonly":
            a = a.copy()
            a.flags.writeable = False
        elif layout == "integer" and name == "beam_amplitudes":
            a = a.astype(np.int64)
        arrays[name] = a
    c = replace(c, **arrays)
    cam = replace(
        camera(), variances_counts2=object(), gain_counts_per_e=object(), information_codes=object()
    )
    before = {name: (a.copy(), a.strides, a.flags.writeable) for name, a in arrays.items()}
    old_errors, old_filters = np.geterr(), list(warnings.filters)
    state, py_state = np.random.get_state(), random.getstate()
    result = audit(api, c, camera_estimate=cam)
    assert result.status == "diagnostic_candidate"
    np.testing.assert_allclose(result.candidate.phases_rad, original, rtol=0, atol=PHASE_ATOL)
    assert result.specimen.camera_estimate.variances_counts2 is cam.variances_counts2
    assert result.specimen.camera_estimate.gain_counts_per_e is cam.gain_counts_per_e
    for name, (data, strides, writeable) in before.items():
        np.testing.assert_array_equal(getattr(c, name), data)
        assert getattr(c, name).strides == strides and getattr(c, name).flags.writeable == writeable
    assert np.geterr() == old_errors and warnings.filters == old_filters
    now = np.random.get_state()
    assert state[0] == now[0] and state[2:] == now[2:]
    np.testing.assert_array_equal(state[1], now[1])
    assert random.getstate() == py_state


@pytest.mark.parametrize("layout", ["endian", "fortran", "strided", "readonly", "integer"])
def test_raw_signed_representation_and_caller_policy_on_information_return(api, layout):
    raw = []
    for shape in ((1, 2, 2), (3, 9, 1, 2, 2), (3, 5, 1, 2, 2)):
        a = np.full(shape, -3.0)
        if layout == "endian":
            a = a.astype(">f8")
        elif layout == "fortran":
            a = np.asfortranarray(a)
        elif layout == "strided":
            a = np.broadcast_to(a[..., :1], shape)
        elif layout == "readonly":
            a.flags.writeable = False
        elif layout == "integer":
            a = a.astype("int64")
        raw.append(a)
    central, options = infer_kwargs((*raw, camera()))
    before = [(a.copy(), a.strides, a.flags.writeable) for a in raw]
    with np.errstate(all="raise"):
        policy = np.geterr()
        result = api.infer_calibration_handoff(central, **options)
        assert np.geterr() == policy
        with pytest.raises(Exception) as error:
            api.infer_calibration_handoff(central, **{**options, "operator_atol": 0.0})
        assert getattr(error.value, "code", None) == "invalid_calibration_handoff"
        assert np.geterr() == policy
    assert result.status == "unavailable" and result.candidate is None
    for a, (copy, strides, writeable) in zip(raw, before, strict=True):
        np.testing.assert_array_equal(a, copy)
        assert a.strides == strides and a.flags.writeable == writeable


def test_concrete_range_obstructions_are_not_invalid_input(api):
    c = candidate(beams=(1.0, 0.0, 0.0))
    # A strictly positive detector spacing is valid input even when its
    # required half-spacing is not representable as a positive float64.
    result = audit(
        api,
        c,
        specimen_detector_spacing_um_zyx=(0.21, float(np.nextafter(0.0, 1.0)), 0.11),
    )
    assert result.status == "numerical_incomplete"
    assert result.failure_code == "calibration_handoff_range"
    assert result.specimen is None


def test_binding_and_absence_of_true_parameter_inputs(api):
    infer_params = inspect.signature(api.infer_calibration_handoff).parameters
    expected = {
        "central_counts",
        "structured_counts",
        "heldout_counts",
        "camera_estimate",
        "calibration_origin_um_zyx",
        "specimen_detector_shape_zyx",
        "specimen_detector_spacing_um_zyx",
        "specimen_origin_um_zyx",
        "sweep_scales",
        "max_refinement_evaluations",
        "training_rms_limit",
        "calibration_atol",
        "operator_atol",
        "source",
    }
    assert set(infer_params) == expected
    for name, param in infer_params.items():
        assert param.default is inspect.Parameter.empty
        if name != "central_counts":
            assert param.kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        api.infer_calibration_handoff(np.zeros((1, 2, 2)), true_phases=np.zeros((3, 9)))
    with pytest.raises(TypeError):
        api.audit_calibration_candidate(candidate(), SMALL)
    with pytest.raises(TypeError):
        api.audit_calibration_candidate(candidate())


def test_multifocus_reflection_is_scored_and_invalid_root_is_infeasible(api):
    c = candidate()
    shape = (2, 3, 7)
    result = audit(api, c, calibration_shape_zyx=shape)
    reflected = alternatives(c, shape)[2][1]
    assert reflected is not None
    central, structured = prediction(c, shape)
    ac, at = prediction(reflected, shape)
    expected = max(float(np.max(np.abs(ac - central))), float(np.max(np.abs(at - structured))))
    assert expected > 10 * CAL_ATOL
    case = result.audit[2]
    assert case.outcome == "calibration_distinct"
    assert abs(case.calibration_max_abs_difference - expected) <= CAL_ATOL
    balanced = audit(api, candidate(beams=(1.0, 1.0, 1.0)))
    for case in balanced.audit[3:5]:
        assert case.outcome == "infeasible"
        assert case.candidate is None and case.failure_code is None
        assert case.material is None and case.calibration_equivalent is None


def test_computed_calibration_threshold_and_common_beam_scale(api):
    c = candidate()
    original = audit(api, c)
    index = 42  # first individual addition of pi
    delta = original.audit[index].calibration_max_abs_difference
    assert delta > CAL_ATOL
    equal = audit(api, c, calibration_atol=delta)
    assert equal.audit[index].calibration_equivalent is True
    below = audit(api, c, calibration_atol=float(np.nextafter(delta, 0.0)))
    assert below.audit[index].calibration_equivalent is False
    # Common amplitudes are a gauge; no physical gain, intensity alignment or
    # independent normalization of central/side orders is needed.
    scaled = audit(api, replace(c, beam_amplitudes=c.beam_amplitudes * 8))
    assert scaled.status == original.status
    for first, second in zip(original.audit, scaled.audit, strict=True):
        assert first.outcome == second.outcome
        if first.calibration_max_abs_difference is not None:
            assert (
                abs(first.calibration_max_abs_difference - second.calibration_max_abs_difference)
                <= CAL_ATOL
            )
        if first.operator_max_abs_difference is not None:
            assert (
                abs(first.operator_max_abs_difference - second.operator_max_abs_difference)
                <= FIELD_ATOL
            )


def test_zero_brightness_zero_carrier_duplicate_phases_are_legitimate(api):
    c = candidate(beams=(1.0, 0.0, 0.0), zero=True)
    c.carriers_yx_per_um[:] = 0
    c.phases_rad[:] = 0.73
    result = audit(api, c)
    assert result.status == "diagnostic_candidate"
    assert result.audit_complete
    for case in result.audit:
        assert case.outcome in {"infeasible", "equivalent_harmless"}
        if case.outcome == "equivalent_harmless":
            assert case.calibration_max_abs_difference == 0
            assert case.operator_max_abs_difference <= FIELD_ATOL


class ArraySubclass(np.ndarray):
    """Provide an explicitly rejected representation, never a product seam."""


@pytest.mark.parametrize(
    "value",
    [
        np.zeros((1, 2, 2), dtype=bool),
        np.zeros((1, 2, 2), dtype=complex),
        np.zeros((1, 2, 2), dtype=object),
        np.zeros((1, 2, 2)).view(ArraySubclass),
        np.zeros((1, 1, 2)),
        np.full((1, 2, 2), float("inf")),
        [[[0.0, 0.0], [0.0, 0.0]]],
    ],
)
def test_raw_invalid_representations_reject_before_information_outcome(api, value):
    raw = (
        value,
        np.zeros((3, 9, 1, 2, 2)),
        np.zeros((3, 5, 1, 2, 2)),
        replace(camera(), contrast_counts=0.0),
    )
    central, options = infer_kwargs(raw)
    with pytest.raises(Exception) as error:
        api.infer_calibration_handoff(central, **options)
    assert getattr(error.value, "code", None) in {
        "invalid_calibration_handoff",
        "invalid_image_only_bead_calibration",
    }


@pytest.mark.parametrize(
    "value",
    [
        np.zeros((3, 9), dtype=bool),
        np.zeros((3, 9), dtype=object),
        np.zeros((3, 9)).view(ArraySubclass),
        np.full((3, 9), float("inf")),
    ],
)
def test_candidate_rejected_array_grammar(api, value):
    with pytest.raises(Exception) as error:
        audit(api, replace(candidate(), phases_rad=value))
    assert getattr(error.value, "code", None) == "invalid_calibration_handoff"


def test_uint64_conversion_rounding_and_origin_tuple_subclass_are_legal(api):
    class Origin(tuple):
        pass

    shape = (1, 2, 2)
    value = 2**53 + 1  # rounds to 2**53; finite rounding is permitted.
    raw = (
        np.full(shape, value, dtype="uint64"),
        np.full((3, 9, *shape), value, dtype="uint64"),
        np.full((3, 5, *shape), value, dtype="uint64"),
        replace(camera(), contrast_counts=0.0),
    )
    central, options = infer_kwargs(raw, calibration_origin_um_zyx=Origin((-2, 0, 3)))
    result = api.infer_calibration_handoff(central, **options)
    assert result.status == "unavailable"
    assert result.failure_code is None


def test_longdouble_raw_values_follow_available_native_range(api):
    shape = (1, 2, 2)
    wider = np.finfo(np.longdouble).maxexp > np.finfo(float).maxexp
    raw = (
        np.full(shape, np.finfo(np.longdouble).max, dtype=np.longdouble),
        np.zeros((3, 9, *shape)),
        np.zeros((3, 5, *shape)),
        replace(camera(), contrast_counts=0.0),
    )
    central, options = infer_kwargs(raw)
    if wider:
        # A native wider exponent supplies the original-finite/conversion-
        # nonfinite rejection control. Its absence cannot supply that proof.
        with pytest.raises(Exception) as error:
            api.infer_calibration_handoff(central, **options)
        assert getattr(error.value, "code", None) in {
            "invalid_calibration_handoff",
            "invalid_image_only_bead_calibration",
        }
    else:
        # Native longdouble may alias float64. Its finite maximum is legal;
        # validation precedes nonpositive-contrast informational unavailability.
        result = api.infer_calibration_handoff(central, **options)
        assert result.status == "unavailable" and result.stage == "seed"
        assert result.failure_code is None
    invalid = np.full(shape, float("inf"), dtype=np.longdouble)
    with pytest.raises(Exception) as error:
        api.infer_calibration_handoff(invalid, **options)
    assert getattr(error.value, "code", None) in {
        "invalid_calibration_handoff",
        "invalid_image_only_bead_calibration",
    }
