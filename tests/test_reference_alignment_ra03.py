"""Blind public-contract tests for RA03; no implementation inspection.

R17/R18 are full-study coordinator obligations. The small fixture controls below
are executable protocol inputs, not substitutes for the fifteen-exposure study.
"""

import copy
import importlib
import math
import warnings
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from reference_alignment_ra03_fixture import (
    OBSERVER_REL,
    TRUE_BEAMS,
    arm_settings,
    bessel0,
    cache_matrices,
    illumination,
    kernel_application_control,
    large_phase_control,
    large_phase_phasor,
    make_cache,
    orientation_case,
    pairing_control,
    physical_images,
    point_sign_control,
    pupil,
    refinement_controls,
    signed_cache_control,
    transfer,
)


def api():
    # Local import: existing-interface controls remain collectable without RA03.
    return importlib.import_module("scripts.reference_alignment_ra03")


def evaluate(case):
    return api().evaluate_orientation(**case)


def assert_values(actual, expected, allowance):
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.shape == expected.shape
    assert np.isfinite(actual).all()
    assert float(np.max(np.abs(actual - expected))) <= allowance


def assert_owned(array, dtype, shape):
    assert type(array) is np.ndarray
    assert array.dtype == np.dtype(dtype)
    assert array.dtype.isnative
    assert array.shape == shape
    assert array.flags.owndata and array.flags.writeable


def expected_metrics(reference, prediction):
    """Small, safely scaled hand-observed data only; no product metric helper."""
    ref = [float(v) for v in np.asarray(reference).flat]
    delta = [float(v) - r for v, r in zip(np.asarray(prediction).flat, ref, strict=True)]
    ref_norm, error = math.hypot(*ref), math.hypot(*delta)
    return dict(
        count=len(ref),
        error_l2=error,
        reference_l2=ref_norm,
        relative_l2=None if ref_norm == 0 else error / ref_norm,
        max_abs=max(map(abs, delta)),
        mean_difference=math.fsum(delta) / len(delta),
        rms_difference=error / math.sqrt(len(delta)),
    )


def assert_metric_row(actual, expected):
    assert actual["count"] == expected["count"]
    for key, value in expected.items():
        if value is None:
            assert actual[key] is None
        elif key != "count":
            assert actual[key] == pytest.approx(value, rel=OBSERVER_REL, abs=0)


def test_oracle_analytic_peak_and_unequal_side_sign():
    # Independent analytic anchors: J0(0)=1, one-node pupil modulus=1 at r=0.
    assert bessel0(0) == 1
    for order in (1, 2, 3):
        assert pupil(0, 0, pupil_order=order) == pytest.approx(math.pi / 4, rel=OBSERVER_REL)
    for d in (-0.5, 0.0, 0.5):
        assert pupil(0, d, pupil_order=1) == pytest.approx(math.pi / 4, rel=OBSERVER_REL)
    # kappa=1/2 algebraically, theta=pi/2. Fields (0,5) and (0,-3).
    q = np.array([math.sqrt(3) / 2, 0.0])
    assert illumination(0, 0, 0.5, q, math.pi / 2, TRUE_BEAMS) == pytest.approx(
        25 / 21, rel=OBSERVER_REL
    )
    assert illumination(0, 0, -0.5, q, math.pi / 2, TRUE_BEAMS) == pytest.approx(
        9 / 21, rel=OBSERVER_REL
    )
    # A nonzero 5*2^-154 value is below half the smallest float32
    # subnormal (2^-150), so nearest-even conversion must lose it.
    stages = pairing_control()
    assert stages["paired64"][2, 0, 1] == 5 * 2**-154
    assert stages["paired32"][2, 0, 1] == 0
    assert np.count_nonzero((stages["paired64"] != 0) & (stages["paired32"] == 0)) == 1
    assert (
        stages["represented32_total"] - stages["exact_gauged_total"]
        == stages["pair_sum_change"] * Fraction(5, 4)
        + stages["gauge_sum_change"]
        + stages["cast32_sum_change"]
    )


def test_r01_r02_r09_pairing_rounding_and_archived_values():
    case = orientation_case()
    result = evaluate(case)
    assert {"arrays", "sources", "arms", "metrics", "rounding"} <= result.keys()
    paired64 = (case["fine_source_e"][0::2] + case["fine_source_e"][1::2]) * 1.25
    paired32 = paired64.astype(np.float32)
    stages = pairing_control()
    np.testing.assert_array_equal(stages["paired64"], paired64)
    np.testing.assert_array_equal(stages["paired32"], paired32)
    np.testing.assert_array_equal(result["sources"]["paired64"], paired64)
    np.testing.assert_array_equal(result["sources"]["paired32"], paired32)
    np.testing.assert_array_equal(
        result["arrays"]["fine_reference"], case["reference_signal_e"] * 1.25
    )
    np.testing.assert_array_equal(
        result["arrays"]["original_prediction"], case["original_prediction_relative"]
    )
    delta = paired32.astype(np.float64) - paired64
    ledger = result["rounding"]
    wanted = expected_metrics(paired64, paired32)
    for key in ("relative_l2", "max_abs"):
        assert ledger[key] == pytest.approx(wanted[key], rel=OBSERVER_REL, abs=0)
    assert ledger["sum_change"] == pytest.approx(math.fsum(delta.flat), rel=OBSERVER_REL, abs=0)
    assert ledger["nonzero_lost"] == int(np.count_nonzero((paired64 != 0) & (paired32 == 0))) == 1
    assert ledger["changed_coefficients"] == int(np.count_nonzero(paired32 != paired64))


def test_r03_paired_generators_have_independent_finite_targets():
    case = orientation_case()
    result = evaluate(case)
    paired = (case["fine_source_e"][0::2] + case["fine_source_e"][1::2]) * 1.25
    phases = transfer(
        case["true_carrier_yx_per_um"],
        case["true_phases_at_calibration_origin_rad"],
        case["calibration_origin_um_zyx"],
        case["specimen_origin_um_zyx"],
    )
    for name, source in (
        ("paired_generator64_true", paired),
        ("paired_generator32_true", paired.astype(np.float32).astype(np.float64)),
    ):
        expected, u = physical_images(
            source,
            spacing=case["detector_spacing_um_zyx"],
            refinement=(1, 2, 2),
            q=case["true_carrier_yx_per_um"],
            phases=phases,
            beams=case["true_beam_amplitudes"],
        )
        scale = float(u.max())
        assert_values(result["arrays"][name], expected, (1e-5 + OBSERVER_REL) * scale)


def test_r04_to_r09_all_arms_gauge_kappa_order_and_original_reapplication():
    case = orientation_case()
    result = evaluate(case)
    paired = ((case["fine_source_e"][0::2] + case["fine_source_e"][1::2]) * 1.25).astype(np.float32)
    cache = make_cache()
    b, _, _, _ = cache_matrices(cache)
    cr = float(np.max(np.sum(b, axis=1)))
    for name, (q, calphases, beams) in arm_settings(case).items():
        phases = transfer(
            q, calphases, case["calibration_origin_um_zyx"], case["specimen_origin_um_zyx"]
        )
        source = case["original_source_relative"] if name == "original_fit_reapplied" else paired
        expected, _ = physical_images(
            source,
            spacing=case["detector_spacing_um_zyx"],
            refinement=(1, 2, 2),
            q=q,
            phases=phases,
            beams=beams,
        )
        lscale = sum(beams) ** 2 / sum(a * a for a in beams)
        scale = lscale * cr * float(np.max(np.abs(source)))
        # Any faithful builder representation is legitimate. This is the joint
        # physical-to-cache plus application bound, not isolated cache rounding.
        assert_values(result["arrays"][name], expected, (2e-4 + 1e-8 + OBSERVER_REL) * scale)
        manifest = result["arms"][name]
        np.testing.assert_array_equal(manifest["carrier_yx_per_um"], q)
        np.testing.assert_array_equal(manifest["phases_at_calibration_origin_rad"], calphases)
        phase_error = np.asarray(manifest["phases_at_specimen_origin_rad"]) - phases
        # Equivalent wrapping is allowed; no imposed wrap interval.
        assert_values(np.sin(phase_error / 2), np.zeros(len(phases)), OBSERVER_REL)
        np.testing.assert_array_equal(manifest["beam_amplitudes"], beams)
        assert isinstance(manifest["source"], str) and manifest["source"].strip()
        assert isinstance(manifest["interpretation"], str) and manifest["interpretation"].strip()
    # This chosen intervention actually changes the axial illumination, so an
    # accidentally unused arm setting cannot pass as an indistinguishable input.
    assert not np.array_equal(
        result["arrays"]["paired_inverse_true"], result["arrays"]["paired_inverse_carrier_only"]
    )


def test_r03_to_r09_anisotropic_spacing_and_changed_optics():
    case = orientation_case()
    spacing = (0.5, 0.75, 1.25)
    optics = dict(
        excitation_um=0.9, emission_um=0.8, refractive_index=1.2, detection_na=0.7, pupil_order=3
    )
    case.update(detector_spacing_um_zyx=spacing, **optics)
    paired64 = (case["fine_source_e"][0::2] + case["fine_source_e"][1::2]) * case[
        "source_to_relative"
    ]
    paired32 = paired64.astype(np.float32)
    targets = {}
    true_q = case["true_carrier_yx_per_um"]
    true_phases = transfer(
        true_q,
        case["true_phases_at_calibration_origin_rad"],
        case["calibration_origin_um_zyx"],
        case["specimen_origin_um_zyx"],
    )
    for name, source in (
        ("paired_generator64_true", paired64),
        ("paired_generator32_true", paired32.astype(np.float64)),
    ):
        expected, unilluminated = physical_images(
            source,
            spacing=spacing,
            refinement=(1, 2, 2),
            q=true_q,
            phases=true_phases,
            beams=case["true_beam_amplitudes"],
            optics=optics,
        )
        targets[name] = (expected, (1e-5 + OBSERVER_REL) * float(unilluminated.max()))
    # B_Q is nonnegative. Its row sums equal the unilluminated finite
    # image of an all-ones source: no product cache supplies this scale.
    _, row_sums = physical_images(
        np.ones(paired64.shape, dtype=np.float64),
        spacing=spacing,
        refinement=(1, 2, 2),
        q=np.zeros(2),
        phases=np.zeros(1),
        beams=(1.0, 0.0, 0.0),
        optics=optics,
    )
    cr = float(row_sums.max())
    for name, (q, calibration_phases, beams) in arm_settings(case).items():
        source = case["original_source_relative"] if name == "original_fit_reapplied" else paired32
        phases = transfer(
            q, calibration_phases, case["calibration_origin_um_zyx"], case["specimen_origin_um_zyx"]
        )
        expected, _ = physical_images(
            source,
            spacing=spacing,
            refinement=(1, 2, 2),
            q=q,
            phases=phases,
            beams=beams,
            optics=optics,
        )
        lscale = sum(beams) ** 2 / sum(a * a for a in beams)
        scale = lscale * cr * float(np.max(np.abs(source)))
        targets[name] = (expected, (2e-4 + 1e-8 + OBSERVER_REL) * scale)
    # Compute every independent target and budget before observing the evaluator.
    # These inverse targets use the joint physical/cache/application allowance.
    result = evaluate(case)
    for name, (expected, allowance) in targets.items():
        assert_values(result["arrays"][name], expected, allowance)


def test_r10_evaluator_metrics_cover_every_arm_with_same_archived_denominator():
    result = evaluate(orientation_case())
    reference = result["arrays"]["fine_reference"]
    names = set(result["arrays"]) - {"fine_reference"}
    assert names == {
        "paired_generator64_true",
        "paired_generator32_true",
        "paired_inverse_true",
        "paired_inverse_estimated",
        "paired_inverse_carrier_only",
        "paired_inverse_phase_only",
        "paired_inverse_beam_only",
        "original_prediction",
        "original_fit_reapplied",
    }
    assert set(result["metrics"]) == names
    for name in names:
        metric = result["metrics"][name]
        prediction = result["arrays"][name]
        assert_metric_row(metric["aggregate"], expected_metrics(reference, prediction))
        assert len(metric["frames"]) == 3
        for p, row in enumerate(metric["frames"]):
            assert (row["orientation"], row["phase"]) == (0, p)
            assert_metric_row(row, expected_metrics(reference[p], prediction[p]))


@pytest.mark.parametrize("rank", [4, 5])
def test_r10_metrics_global_norms_signed_differences_and_zero_reference(rank):
    reference = np.array([0, 0, 3, 4, 0, 12, 5, 0], dtype=np.int64).reshape(2, 2, 1, 1, 2)
    if rank == 4:
        reference = reference.reshape(4, 1, 1, 2)
    prediction = reference.astype(np.float64) + np.array([0, 0, -3, -4, 0, 12, -10, 0]).reshape(
        reference.shape
    )
    result = api().summarize_errors(
        reference, {"signed": prediction, "zero": np.zeros_like(prediction)}
    )
    for name, pred in (("signed", prediction), ("zero", np.zeros_like(prediction))):
        rows = result[name]["frames"]
        assert len(rows) == 4
        for i, row in enumerate(rows):
            o, p = divmod(i, 2) if rank == 5 else (0, i)
            assert (row["orientation"], row["phase"]) == (o, p)
            assert_metric_row(
                row, expected_metrics(reference.reshape(4, 2)[i], pred.reshape(4, 2)[i])
            )
        assert_metric_row(result[name]["aggregate"], expected_metrics(reference, pred))
    assert result["signed"]["frames"][0]["relative_l2"] is None
    # The global ratio is sqrt(269)/sqrt(194), distinct from averaging finite frame ratios.
    assert result["signed"]["aggregate"]["relative_l2"] == pytest.approx(
        math.sqrt(269 / 194), rel=OBSERVER_REL
    )


def test_r11_metrics_layout_positives_no_mutation_and_zero_aggregate():
    reference = np.arange(8, dtype=">f8").reshape(1, 2, 2, 2)[..., ::-1]
    reference.flags.writeable = False
    prediction = np.asfortranarray(-reference)
    before = reference.copy(), prediction.copy()
    result = api().summarize_errors(reference, {"negative": prediction})
    assert_metric_row(result["negative"]["aggregate"], expected_metrics(reference, prediction))
    np.testing.assert_array_equal(reference, before[0])
    np.testing.assert_array_equal(prediction, before[1])
    zeros = np.zeros((1, 1, 1, 1))
    result = api().summarize_errors(zeros, {"zero": zeros.copy(), "nonzero": zeros + 2})
    for name in ("zero", "nonzero"):
        assert result[name]["aggregate"]["relative_l2"] is None
    assert result["zero"]["aggregate"]["error_l2"] == 0
    assert result["nonzero"]["aggregate"]["mean_difference"] == 2


@pytest.mark.parametrize(
    "variant",
    [
        "rank",
        "empty_axis",
        "bool",
        "complex",
        "object",
        "list",
        "subclass",
        "nan",
        "prediction_shape",
        "empty_dict",
        "empty_name",
        "bad_name",
        "mapping",
        "overflow",
    ],
)
def test_r11_metrics_reject_invalid_domain_and_nonfinite_reductions(variant):
    reference = np.ones((1, 1, 1, 2))
    predictions: Any = {"arm": reference.copy()}
    if variant == "rank":
        reference = np.ones((1, 2))
    elif variant == "empty_axis":
        reference = np.ones((1, 1, 0, 2))
    elif variant in ("bool", "complex", "object"):
        reference = reference.astype({"bool": bool, "complex": complex, "object": object}[variant])
    elif variant == "list":
        reference = reference.tolist()
    elif variant == "subclass":
        reference = reference.view(type("ArraySubclass", (np.ndarray,), {}))
    elif variant == "nan":
        predictions["arm"][0, 0, 0, 0] = np.nan
    elif variant == "prediction_shape":
        predictions["arm"] = np.ones((1, 1, 1, 1))
    elif variant == "empty_dict":
        predictions = {}
    elif variant == "empty_name":
        predictions = {"": reference}
    elif variant == "bad_name":
        predictions = {1: reference}
    elif variant == "mapping":
        predictions = [("arm", reference)]
    elif variant == "overflow":
        reference.fill(np.finfo(np.float64).max)
        predictions["arm"] = -reference
    with pytest.raises(ValueError):
        api().summarize_errors(reference, predictions)


def test_r12_fixed_half_cell_views_physical_tie_and_independence():
    # All negative: an implicit zero initial value would corrupt the MIPs.
    volume = -np.arange(1, 25, dtype=np.float64).reshape(3, 2, 4)
    before = volume.copy()
    result = api().fixed_center_views(
        volume,
        spacing_um_zyx=(0.5, 2.0, 0.25),
        origin_um_zyx=(-1.0, 3.0, -0.5),
        center_um_zyx=(-0.5, 5.0, 0.5),
    )
    assert tuple(result["indices_zyx"]) == (0, 0, 3)
    np.testing.assert_array_equal(result["coordinates_um_zyx"], (-0.75, 4.0, 0.375))
    expected = dict(
        xy_mip=volume.max(axis=0),
        xz_mip=volume.max(axis=1),
        xy_slice=volume[0],
        xz_slice=volume[:, 0],
    )
    arrays = []
    for name, truth in expected.items():
        actual = result[name]
        assert_owned(actual, np.float64, truth.shape)
        np.testing.assert_array_equal(actual, truth)
        assert not np.shares_memory(actual, volume)
        for other in arrays:
            assert not np.shares_memory(actual, other)
        arrays.append(actual)
    np.testing.assert_array_equal(volume, before)


@pytest.mark.parametrize(
    "center,indices", [((0.0, 0.0, 0.0), (0, 0, 0)), ((2.0, 2.0, 2.0), (1, 1, 1))]
)
def test_r12_field_faces_are_valid(center, indices):
    result = api().fixed_center_views(
        np.zeros((2, 2, 2)),
        spacing_um_zyx=(1.0, 1.0, 1.0),
        origin_um_zyx=(0.0, 0.0, 0.0),
        center_um_zyx=center,
    )
    assert tuple(result["indices_zyx"]) == indices


@pytest.mark.parametrize(
    "variant", ["outside", "spacing", "origin", "center", "rank", "dtype", "nonfinite"]
)
def test_r12_views_reject_invalid_inputs(variant):
    kwargs: dict[str, Any] = dict(
        spacing_um_zyx=(1.0, 1.0, 1.0), origin_um_zyx=(0.0, 0.0, 0.0), center_um_zyx=(0.5, 0.5, 0.5)
    )
    volume = np.ones((2, 2, 2))
    if variant == "outside":
        kwargs["center_um_zyx"] = (2.01, 0.5, 0.5)
    elif variant == "spacing":
        kwargs["spacing_um_zyx"] = (0.0, 1.0, 1.0)
    elif variant in ("origin", "center"):
        kwargs[f"{variant}_um_zyx"] = (np.inf, 0.0, 0.0)
    elif variant == "rank":
        volume = np.ones((2, 2))
    elif variant == "dtype":
        volume = volume.astype(bool)
    elif variant == "nonfinite":
        volume[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        api().fixed_center_views(volume, **kwargs)


def test_r13_point_above_and_below_focus_with_unequal_sides():
    control = point_sign_control()
    tscale = float(control["unilluminated"].max())
    assert_values(control["actual"], control["expected"], (1e-5 + OBSERVER_REL) * tscale)
    _, g, _, _ = cache_matrices(control["cache"])
    scale = sum(TRUE_BEAMS) ** 2 / sum(a * a for a in TRUE_BEAMS) * float(g.sum(axis=1).max())
    assert_values(
        control["inverse_actual"], control["inverse_expected"], (1e-4 + OBSERVER_REL) * scale
    )
    # Q1 has no axial envelope loss, so this is an analytic sign discriminator.
    assert control["expected"][0, 0, 0, 0] / control["expected"][0, 2, 0, 0] == pytest.approx(
        25 / 9, rel=OBSERVER_REL
    )


def test_r14_physical_kernel_and_represented_application_separate_bounds():
    control = kernel_application_control()
    b, g, e = (control[k] for k in ("physical_matrix", "absolute_matrix", "error_matrix"))
    for axis in (0, 1):
        bound = (1e-4 + OBSERVER_REL) * float(b.sum(axis=axis).max())
        assert float(e.sum(axis=axis).max()) <= bound
    beams = control["beams"]
    scale = (
        sum(beams) ** 2
        / sum(a * a for a in beams)
        * float(g.sum(axis=1).max())
        * float(np.abs(control["source"]).max())
    )
    assert_values(control["actual"], control["expected"], (1e-4 + OBSERVER_REL) * scale)


def test_r14_signed_cache_is_an_algebraic_target_not_authenticated_pupil():
    control = signed_cache_control()
    assert_values(control["interpreted"], control["expected"], OBSERVER_REL)
    assert_values(
        control["actual"], control["expected"], (1e-4 + OBSERVER_REL) * control["application_scale"]
    )
    assert control["actual"][0, 1, 0, 0] < 0


def test_r15_same_sphere_source_refinement_and_separate_pixel_counts():
    controls = refinement_controls()
    assert [r["source_refinement"] for r in controls["source_rows"]] == [1, 2, 4]
    assert [r["pixels"] for r in controls["pixel_rows"]] == [1, 2, 4]
    for row in controls["source_rows"]:
        np.testing.assert_array_equal(row["source_actual"], row["source_expected"])
        assert row["occupied_count"] > 0
        assert row["pixels"] == 2 and row["pupil_order"] == 2
    for row in controls["pixel_rows"]:
        assert row["source_refinement"] == 2 and row["pupil_order"] == 2
    for row in controls["source_rows"] + controls["pixel_rows"]:
        scale = float(row["unilluminated"].max())
        assert_values(row["actual"], row["expected"], (1e-5 + OBSERVER_REL) * scale)
    # No monotonic-convergence or continuum-resolution assertion is selected.


def test_r16_ownership_layout_signed_original_and_preserved_state():
    case = orientation_case()
    array_keys = [key for key, value in case.items() if isinstance(value, np.ndarray)]
    for key in array_keys:
        case[key] = np.asfortranarray(case[key].astype(case[key].dtype.newbyteorder(">")))
        case[key].flags.writeable = False
    before = {key: case[key].copy() for key in array_keys}
    random_before = np.random.get_state()
    old_policy = np.seterr(all="raise")
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            result = evaluate(case)
        assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
        assert np.geterr() == dict.fromkeys(("divide", "over", "under", "invalid"), "raise")
    finally:
        np.seterr(**old_policy)
    random_after = np.random.get_state()
    assert random_before[0] == random_after[0]
    np.testing.assert_array_equal(random_before[1], random_after[1])
    assert random_before[2:] == random_after[2:]
    outputs = []
    for value in result["arrays"].values():
        assert_owned(value, np.float64, (3, 3, 1, 1))
        outputs.append(value)
    for key, dtype in (("paired64", np.float64), ("paired32", np.float32)):
        assert_owned(result["sources"][key], dtype, (3, 2, 2))
        outputs.append(result["sources"][key])
    for i, output in enumerate(outputs):
        for other in outputs[:i] + [case[key] for key in array_keys]:
            assert not np.shares_memory(output, other)
    for key in array_keys:
        np.testing.assert_array_equal(case[key], before[key])
    # A later result must have independent storage, without prescribing caching.
    again = evaluate(case)
    for key, value in result["arrays"].items():
        np.testing.assert_array_equal(value, again["arrays"][key])
        assert not np.shares_memory(value, again["arrays"][key])


def test_r16_zero_source_one_phase_zero_carrier_and_one_beam():
    case = orientation_case()
    case["fine_source_e"].fill(0)
    case["original_source_relative"].fill(0)
    case["reference_signal_e"] = np.zeros((1, 3, 1, 1))
    case["original_prediction_relative"] = np.zeros((1, 3, 1, 1))
    for side in ("true", "estimated"):
        case[f"{side}_carrier_yx_per_um"] = np.zeros(2)
        case[f"{side}_phases_at_calibration_origin_rad"] = np.array([0.0])
        case[f"{side}_beam_amplitudes"] = (0.0, 1.0, 0.0)
    result = evaluate(case)
    for array in result["arrays"].values():
        np.testing.assert_array_equal(array, np.zeros((1, 3, 1, 1)))
    assert result["rounding"]["relative_l2"] is None
    for metric in result["metrics"].values():
        assert metric["aggregate"]["relative_l2"] is None


@pytest.mark.parametrize(
    "field,variant",
    [
        ("fine_source_e", "float32"),
        ("fine_source_e", "shape"),
        ("fine_source_e", "negative"),
        ("reference_signal_e", "float32"),
        ("reference_signal_e", "negative"),
        ("reference_signal_e", "shape"),
        ("original_source_relative", "float64"),
        ("original_source_relative", "shape"),
        ("original_prediction_relative", "float32"),
        ("original_prediction_relative", "shape"),
        ("fine_source_e", "subclass"),
        ("original_prediction_relative", "nonfinite"),
        ("source_to_relative", "zero"),
        ("source_to_relative", "nonfinite"),
        ("calibration_origin_um_zyx", "shape"),
        ("specimen_origin_um_zyx", "nonfinite"),
        ("true_phases_at_calibration_origin_rad", "shape"),
        ("estimated_carrier_yx_per_um", "shape"),
    ],
)
def test_r16_evaluator_specific_invalid_inputs_identify_input(field, variant):
    case = orientation_case()
    if variant in ("float32", "float64"):
        case[field] = case[field].astype(variant)
    elif variant == "negative":
        case[field].flat[0] = -1
    elif variant == "shape":
        if isinstance(case[field], np.ndarray):
            case[field] = case[field][:-1]
        else:
            case[field] = (0.0, 0.0)
    elif variant == "subclass":
        case[field] = case[field].view(type("ArraySubclass", (np.ndarray,), {}))
    elif variant == "nonfinite":
        if isinstance(case[field], np.ndarray):
            case[field].flat[0] = np.inf
        elif isinstance(case[field], tuple):
            case[field] = (0.0, np.inf, 0.0)
        else:
            case[field] = np.inf
    elif variant == "zero":
        case[field] = 0.0
    before = copy.deepcopy(case)
    with pytest.raises(ValueError) as caught:
        evaluate(case)
    message = str(caught.value).lower().replace("_", " ")
    aliases = {
        "fine_source_e": [("fine", "source")],
        "reference_signal_e": [("reference",)],
        "original_source_relative": [("original", "source")],
        "original_prediction_relative": [("original", "prediction")],
        "source_to_relative": [("source", "relative"), ("scale",)],
        "calibration_origin_um_zyx": [("calibration", "origin")],
        "specimen_origin_um_zyx": [("specimen", "origin")],
        "true_phases_at_calibration_origin_rad": [("phase",)],
        "estimated_carrier_yx_per_um": [("estimated", "carrier")],
    }
    accepted_aliases = aliases[field]
    if variant == "shape" and isinstance(before[field], np.ndarray):
        # Removing axis zero changes P for the reference/prediction/phase
        # cases, and Nz for the original source. Permit only those linked
        # participants. The odd fine-source axis and short carrier are
        # intrinsically malformed, independent of every other input's shape.
        shape_aliases = {
            "reference_signal_e": [("reference",), ("original", "prediction"), ("phase",)],
            "original_source_relative": [
                ("original", "source"),
                ("fine", "source"),
                ("reference",),
                ("original", "prediction"),
            ],
            "original_prediction_relative": [
                ("original", "prediction"),
                ("reference",),
                ("phase",),
            ],
            "true_phases_at_calibration_origin_rad": [
                ("phase",),
                ("reference",),
                ("original", "prediction"),
            ],
        }
        if field in shape_aliases:
            accepted_aliases = shape_aliases[field]
    assert any(all(word in message for word in words) for words in accepted_aliases)
    for key, value in before.items():
        if isinstance(value, np.ndarray):
            np.testing.assert_array_equal(case[key], value)


def test_r16_nonfinite_derived_pairing_rejects_and_preserves_policy():
    case = orientation_case()
    case["fine_source_e"][0:2, 0, 0] = np.finfo(np.float64).max
    before = case["fine_source_e"].copy()
    policy = np.geterr()
    with pytest.raises(ValueError):
        evaluate(case)
    assert np.geterr() == policy
    np.testing.assert_array_equal(case["fine_source_e"], before)


def test_r16_existing_delegated_optical_domain_exception_is_preserved():
    api()  # Keep feature absence distinct from a delegated-operation assertion.
    case = orientation_case()
    case["detection_na"] = 2.0  # NA > refractive index, invalid in both contracts.
    with pytest.raises(Exception) as caught:
        evaluate(case)
    assert type(caught.value).__name__ == "SimreconError"
    # Either public delegated boundary may validate first; no order is imposed.
    assert getattr(caught.value, "code", None) in {
        "invalid_simulation_optics",
        "invalid_simulation_inverse_operator",
    }


def test_r16_ordinary_binding_errors():
    module = api()
    with pytest.raises(TypeError):
        module.evaluate_orientation()
    with pytest.raises(TypeError):
        module.evaluate_orientation(**orientation_case(), unknown_argument=True)
    with pytest.raises(TypeError):
        module.summarize_errors()
    with pytest.raises(TypeError):
        module.fixed_center_views(np.zeros((1, 1, 1)), unknown_argument=True)


@pytest.mark.parametrize("displaced", [False, True], ids=["equal_origin_q0", "shifted_origin_qx"])
def test_supplement_r03_to_r09_r16_large_phase_and_origin_transfer(displaced):
    # POST-IMPLEMENTATION SUPPLEMENT to the B2 checkpoint, not initial blind-red
    # evidence. Keep the accepted bounded-phase observers unchanged.
    control = large_phase_control(displaced)
    result = evaluate(control["case"])
    failures = []
    for name in (
        "paired_generator64_true",
        "paired_generator32_true",
        "paired_inverse_true",
        "paired_inverse_estimated",
        "paired_inverse_carrier_only",
        "paired_inverse_phase_only",
        "paired_inverse_beam_only",
    ):
        actual = result["arrays"][name]
        assert actual.shape == control["expected"].shape
        assert np.isfinite(actual).all()
        allowance = (
            control["generator_allowance_e"]
            if name.startswith("paired_generator")
            else control["inverse_allowance_e"]
        )
        error = float(np.max(np.abs(actual - control["expected"])))
        if error > allowance:
            failures.append(f"{name}: max error {error:.17g} exceeds allowance {allowance:.17g}")
    np.testing.assert_array_equal(
        result["arrays"]["original_fit_reapplied"], np.zeros((1, 1, 1, 1))
    )
    for name in (
        "paired_inverse_true",
        "paired_inverse_estimated",
        "paired_inverse_carrier_only",
        "paired_inverse_phase_only",
        "paired_inverse_beam_only",
        "original_fit_reapplied",
    ):
        manifest = result["arms"][name]
        for key, expected_pair in (
            ("phases_at_calibration_origin_rad", control["calibration_phasor"]),
            ("phases_at_specimen_origin_rad", control["specimen_phasor"]),
        ):
            observed = np.asarray(manifest[key], dtype=np.float64)
            assert observed.shape == (1,) and np.isfinite(observed).all()
            observed_pair = large_phase_phasor(observed[0])
            error = max(abs(a - b) for a, b in zip(observed_pair, expected_pair, strict=True))
            if error > control["manifest_allowance"]:
                failures.append(f"{name}.{key}: phasor error {error:.17g}")
    assert not failures, "\n".join(failures)
