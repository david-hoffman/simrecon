"""RA13 observation-only integration obligations W1--W10.

No implementation source, internal seams, private truth inputs, or optimizer mocks.
The permissive positive asserts finite composition, never recovery/convergence.
"""

import importlib
import math
import random
import warnings
from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import Any

import numpy as np
import pytest

from raw_sim_workflow_fixture import (
    ARRAY_NAMES,
    CAL_D,
    CAL_ORIGIN,
    CAL_SHAPE,
    CONTROL_NAMES,
    SPEC_D,
    SPEC_ORIGIN,
    SPEC_SHAPE,
    composition,
    direct_specimen,
    explicit_fit,
    finite_inputs,
    logical_sha256,
    physical_transfer,
    unavailable_inputs,
)
from simrecon import SimreconError


@pytest.fixture(scope="module")
def workflow():
    # A real missing module is absence evidence; no stub/skip/xfail substitutes.
    return importlib.import_module("scripts.raw_sim_workflow").reconstruct_raw_sim


@pytest.fixture(scope="module")
def noiseless():
    return finite_inputs()


@pytest.fixture(scope="module")
def positive(workflow, noiseless):
    before = snapshots(noiseless)
    result = workflow(**noiseless)
    assert snapshots(noiseless) == before
    return result


def same_public_record(left: Any, right: Any) -> None:
    """Composition oracle only: recursively compare public returned bindings."""
    assert type(left) is type(right)
    if isinstance(left, np.ndarray):
        assert left.shape == right.shape and left.dtype == right.dtype
        np.testing.assert_allclose(left, right, rtol=1e-10, atol=1e-12)
    elif is_dataclass(left) and not isinstance(left, type):
        for field in fields(left):
            same_public_record(getattr(left, field.name), getattr(right, field.name))
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            same_public_record(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            same_public_record(a, b)
    elif isinstance(left, float):
        assert left == pytest.approx(right, rel=1e-10, abs=1e-12)
    else:
        assert left == right


def assert_handoff_stop(result, expected) -> None:
    assert result.stage == "handoff"
    for name in ("status", "reason_code", "failure_code", "message"):
        assert getattr(result, name) == getattr(expected, name)
    same_public_record(result.handoff, expected)
    assert result.camera_estimate is not None
    assert result.specimen_fit is None


def assert_initial_score(fit, raw, blank=7.0, contrast=4.0) -> None:
    """Exact zero-source expectation from supplied counts, using fsum reductions."""
    observed = (raw - blank) / contrast
    flat = [float(y) for y in observed.flat]
    expected = math.fsum(y * y for y in flat) / (2 * len(flat))
    score = fit.initial_score
    # At most a few dozen float64 operations/reductions per tiny observation.
    # 64 eps is conservative for this small, ordinary-magnitude exact control.
    tol = 64 * np.finfo(np.float64).eps
    assert score.data_objective == pytest.approx(expected, rel=tol, abs=tol * expected)
    assert score.penalty_objective == 0
    for o, p in np.ndindex(3, 5):
        values = [float(y) for y in observed[o, p].flat]
        mean = -math.fsum(values) / len(values)
        rms = math.sqrt(math.fsum(y * y for y in values) / len(values))
        assert score.residual_mean[o][p] == pytest.approx(mean, rel=tol, abs=tol * abs(mean))
        assert score.residual_rms[o][p] == pytest.approx(rms, rel=tol, abs=tol * rms)


def test_w1_real_noiseless_composition_and_independent_initial_score(positive, noiseless):
    camera, handoff, fit = composition(noiseless)
    assert handoff.status == "predictive_estimate"  # Fixture adequacy, not identification.
    assert positive.status == "completed_finite_fit" and positive.stage == "complete"
    assert positive.reason_code is None and positive.failure_code is None
    assert positive.message.strip()
    same_public_record(positive.camera_estimate, camera)
    same_public_record(positive.handoff, handoff)
    same_public_record(positive.specimen_fit, fit)
    assert positive.camera_estimate.gain_counts_per_e is None  # Not a normalization gate.
    np.testing.assert_array_equal(positive.camera_estimate.means_counts, [-2, 7, 11])
    assert positive.camera_estimate.contrast_counts == 4
    assert_initial_score(positive.specimen_fit, noiseless["specimen_counts"])


def test_w1_independent_finite_prediction_and_score(positive, noiseless):
    """Independent equation check at returned x; no comparison to hidden true x."""
    assert_finite_score(positive.specimen_fit, noiseless)


def assert_finite_score(fit, inputs):
    """Compare a real fit to the independent finite equation and its own budget."""
    x = fit.source_relative
    expected = direct_specimen(
        x, fit.carriers_yx_per_um, fit.phases_at_specimen_origin_rad, fit.beam_amplitudes
    )
    observed = (inputs["specimen_counts"] - 7) / 4
    residual = expected - observed
    # Contract physical forward max error: (2t+t²)*L*C_r(B_Q)*max(abs(x)).
    # Direct central-only ones response is the nonnegative physical row sum.
    row_sum = direct_specimen(np.ones(x.shape), np.zeros((3, 2)), np.zeros((3, 5)), (1, 0, 0))
    beams = fit.beam_amplitudes
    illumination_bound = float(np.sum(beams)) ** 2 / float(np.sum(beams**2))
    scale = illumination_bound * float(np.max(row_sum)) * float(np.max(x))
    # Separate observer arithmetic allowance; no source-grid/recovery allowance.
    error = (2e-4 + 1e-8 + 1e-10) * scale
    rms = math.sqrt(math.fsum(float(v) ** 2 for v in residual.flat) / residual.size)
    data = rms * rms / 2
    assert abs(fit.best_score.data_objective - data) <= rms * error + error**2 / 2 + 1e-14
    penalty = inputs["regularization"] * math.fsum(float(v) ** 2 for v in x.flat) / (2 * x.size)
    assert fit.best_score.penalty_objective == pytest.approx(penalty, rel=64 * np.finfo(float).eps)
    for o, p in np.ndindex(3, 5):
        mean = math.fsum(float(v) for v in residual[o, p].flat) / residual[o, p].size
        rms = math.sqrt(math.fsum(float(v) ** 2 for v in residual[o, p].flat) / residual[o, p].size)
        assert abs(fit.best_score.residual_mean[o][p] - mean) <= error + 1e-13
        assert abs(fit.best_score.residual_rms[o][p] - rms) <= error + 1e-13


def test_w2_nonzero_origin_first_five_once_only(positive):
    h, fit = positive.handoff, positive.specimen_fit
    expected = physical_transfer(
        h.candidate.phases_rad, h.candidate.carriers_yx_per_um, CAL_ORIGIN, SPEC_ORIGIN
    )
    np.testing.assert_allclose(
        h.specimen.phases_at_specimen_origin_rad, expected, rtol=0, atol=2e-12
    )
    np.testing.assert_array_equal(
        fit.phases_at_specimen_origin_rad, h.specimen.phases_at_specimen_origin_rad
    )
    np.testing.assert_array_equal(fit.carriers_yx_per_um, h.specimen.carriers_yx_per_um)
    np.testing.assert_array_equal(fit.beam_amplitudes, h.specimen.beam_amplitudes)
    twice = physical_transfer(
        np.pad(expected, ((0, 0), (0, 4))), h.candidate.carriers_yx_per_um, CAL_ORIGIN, SPEC_ORIGIN
    )
    assert np.max(np.abs(np.exp(1j * twice) - np.exp(1j * expected))) > 0.1
    assert fit.pupil_order == 128
    assert fit.source_shape_zyx == (2, 4, 6)
    assert fit.source_spacing_um_zyx == (SPEC_D[0], SPEC_D[1] / 2, SPEC_D[2] / 2)
    assert h.provenance["phase_transfer"]["application_count"] == 1


def test_w2_multifocus_unequal_sides_reach_real_consumer(workflow):
    from image_only_calibration_handoff_fixture import candidate, prediction

    inputs = finite_inputs()
    truth = candidate(shape=(3, 3, 24))
    central, structured = prediction(truth, (3, 3, 24))
    inputs.update(
        central_counts=7 + 4 * central,
        structured_counts=7 + 4 * structured,
        heldout_counts=7 + 4 * structured[:, :5],
        max_refinement_evaluations=6,
    )
    result = workflow(**inputs)
    assert result.handoff.status == "predictive_estimate"
    descriptor = result.handoff.specimen
    # This verifies a discriminating control, never equality to generator beams.
    assert descriptor.beam_amplitudes[1] != descriptor.beam_amplitudes[2]
    np.testing.assert_array_equal(result.specimen_fit.beam_amplitudes, descriptor.beam_amplitudes)
    same_public_record(result.specimen_fit, explicit_fit(inputs, descriptor))


@pytest.mark.parametrize("contrast", [0.0, -4.0])
def test_w3_nonpositive_contrast_preserves_real_unavailable(workflow, contrast):
    inputs = unavailable_inputs()
    inputs["flat_counts"] = np.full((2, 2, 2), 7 + contrast)
    _, expected, _ = composition(inputs)
    result = workflow(**inputs)
    assert expected.status == "unavailable"
    assert_handoff_stop(result, expected)


@pytest.mark.parametrize(
    "case", ["initialization", "training_misfit", "training_range", "heldout_range"]
)
def test_w3_real_handoff_outcomes_and_retained_candidates(workflow, noiseless, case):
    inputs = dict(noiseless)
    if case == "initialization":
        inputs["central_counts"] = np.full(CAL_SHAPE, 6.0)
    elif case == "training_misfit":
        inputs["training_rms_limit"] = 0
    elif case == "training_range":
        inputs["structured_counts"] = np.full((3, 9, *CAL_SHAPE), np.finfo(float).max)
    else:
        inputs["heldout_counts"] = np.full((3, 5, *CAL_SHAPE), np.finfo(float).max)
    _, handoff, _ = composition(inputs)
    assert handoff.status in {"unavailable", "numerical_incomplete"}
    result = workflow(**inputs)
    assert_handoff_stop(result, handoff)
    if case == "training_misfit":
        assert handoff.reason_code == "training_misfit" and handoff.candidate is not None
    if case == "heldout_range":
        assert handoff.candidate is not None


@pytest.mark.parametrize(
    "strict", [True, False], ids=["fixed-misfit", "noise-does-not-forbid-execution"]
)
def test_w3_w10_fixed_noisy_diagnostic_follows_actual_outcome(workflow, strict):
    inputs = finite_inputs(noisy=True, strict_diagnostic=strict)
    camera, handoff, fit = composition(inputs)
    result = workflow(**inputs)
    same_public_record(result.camera_estimate, camera)
    same_public_record(result.handoff, handoff)
    assert handoff.input_kind == "observations_only"
    assert handoff.global_operator_identification == "unestablished"
    if strict:
        assert handoff.status == "unavailable" and handoff.reason_code == "training_misfit"
    if handoff.status == "predictive_estimate":
        assert fit is not None
        same_public_record(result.specimen_fit, fit)
        assert result.status == fit.status  # Noise adds no wrapper execution gate.
    else:
        assert_handoff_stop(result, handoff)


def camera_range_inputs():
    inputs = unavailable_inputs()
    inputs["dark_counts"] = np.array([np.finfo(float).max, -np.finfo(float).max] * 4).reshape(
        2, 2, 2
    )
    return inputs


def test_w4_real_camera_arithmetic_range(workflow):
    from simrecon import estimate_scalar_camera

    inputs = camera_range_inputs()
    with pytest.raises(SimreconError) as captured:
        estimate_scalar_camera(
            inputs["dark_counts"],
            blank_counts=inputs["blank_counts"],
            flat_counts=inputs["flat_counts"],
            source=inputs["source"],
        )
    assert captured.value.code == "scalar_camera_calibration_range"
    result = workflow(**inputs)
    assert result.status == "numerical_incomplete" and result.stage == "camera"
    assert result.reason_code is None
    assert result.failure_code == captured.value.code
    assert result.message == str(captured.value)
    assert result.camera_estimate is result.handoff is result.specimen_fit is None
    assert set(result.provenance["inputs"]) == set(ARRAY_NAMES)


class ArraySubclass(np.ndarray):
    """Rejected array representation."""

    pass


class TupleSubclass(tuple):
    """Inherited calibration origin accepts this; strict specimen metadata does not."""

    pass


class FloatSubclass(float):
    """Rejected scalar representation."""

    pass


class IntSubclass(int):
    """Rejected count representation."""

    pass


class StringSubclass(str):
    """Rejected label representation."""

    pass


# One representative per distinct grammar/boundary risk; no Cartesian expansion.
INVALID = [
    ("specimen_counts", None),
    ("specimen_counts", np.zeros((3, 5, 1, 1, 1), dtype=np.float32)),
    ("specimen_counts", np.zeros((3, 5, 1, 1, 1), dtype=">f8" if np.little_endian else "<f8")),
    ("specimen_counts", np.zeros((3, 5, 1, 1, 1)).view(ArraySubclass)),
    ("specimen_counts", np.zeros((3, 5, 1, 1))),
    ("specimen_counts", np.zeros((3, 4, 1, 1, 1))),
    ("specimen_counts", np.zeros((3, 5, 0, 1, 1))),
    ("specimen_counts", np.full((3, 5, 1, 1, 1), np.nan)),
    ("dark_counts", [[[0, 1]], [[2, 3]]]),
    ("blank_counts", np.zeros((2, 2, 2), dtype=bool)),
    ("flat_counts", np.zeros((2, 2, 2), dtype=complex)),
    ("dark_counts", np.zeros((2, 2, 2), dtype=object)),
    ("dark_counts", np.zeros((2, 2, 2)).view(ArraySubclass)),
    ("dark_counts", np.zeros((1, 2, 2))),
    ("dark_counts", np.zeros((2, 1, 1))),
    ("blank_counts", np.zeros((2, 2, 3))),
    ("flat_counts", np.full((2, 2, 2), np.inf)),
    ("central_counts", np.zeros((1, 1, 2))),  # 0.080 um side is too small.
    ("central_counts", np.zeros((1, 2, 2), dtype=bool)),
    ("structured_counts", np.zeros((3, 8, 1, 2, 2))),
    ("heldout_counts", np.zeros((3, 5, 1, 2, 3))),
    ("heldout_counts", np.full((3, 5, 1, 2, 2), np.nan)),
    ("calibration_id", " "),
    ("specimen_calibration_id", "different acquisition"),
    ("source", StringSubclass("label")),
    ("source", "\t"),
    ("calibration_origin_um_zyx", [0, 0, 0]),
    ("calibration_origin_um_zyx", (0, True, 0)),
    ("specimen_origin_um_zyx", TupleSubclass((0, 0, 0))),
    ("specimen_origin_um_zyx", (0, np.float64(1), 0)),
    ("specimen_origin_um_zyx", (0, 0, float("inf"))),
    ("specimen_detector_spacing_um_zyx", (1, 0, 1)),
    ("specimen_detector_spacing_um_zyx", (1, -1, 1)),
    ("specimen_detector_spacing_um_zyx", (1, FloatSubclass(1), 1)),
    ("sweep_scales", ()),
    ("sweep_scales", TupleSubclass((1,))),
    ("sweep_scales", (True,)),
    ("sweep_scales", (0,)),
    ("sweep_scales", (float("nan"),)),
    ("max_refinement_evaluations", True),
    ("max_iterations", 0),
    ("max_backtracking_trials", IntSubclass(1)),
    ("training_rms_limit", -1),
    ("training_rms_limit", FloatSubclass(1)),
    ("calibration_atol", 0),
    ("operator_atol", float("inf")),
    ("regularization", 0),
    ("regularization", 10**400),
]
# Finite original values outside float64 range exist only on wider-float hosts.
# Add supported representation examples, rather than a vacuous native-width test.
if np.finfo(np.longdouble).max > np.finfo(np.float64).max:
    for _name, _shape in (("flat_counts", (2, 2, 2)), ("heldout_counts", (3, 5, 1, 2, 2))):
        INVALID.append((_name, np.full(_shape, np.finfo(np.longdouble).max, dtype=np.longdouble)))


@pytest.mark.parametrize(
    ("name", "value"), INVALID, ids=[f"{n}-{i}" for i, (n, _) in enumerate(INVALID)]
)
def test_w5_complete_validation_before_camera_range(workflow, name, value):
    inputs = camera_range_inputs()
    inputs[name] = value
    with pytest.raises(SimreconError) as captured:
        workflow(**inputs)
    assert captured.value.code == "invalid_raw_sim_workflow"
    message = str(captured.value)
    if name == "specimen_calibration_id":
        assert "calibration_id" in message
    else:
        assert name in message


def snapshots(inputs):
    return {
        name: (
            array.tobytes(order="A"),
            array.dtype,
            array.shape,
            array.strides,
            array.flags.num,
        )
        for name in ARRAY_NAMES
        for array in [inputs[name]]
    }


@pytest.mark.parametrize("layout", ["fortran", "reverse", "stride", "readonly", "zero_stride"])
def test_w6_w8_legal_layouts_original_bytes_and_state(workflow, layout):
    inputs = unavailable_inputs()
    for name in ARRAY_NAMES:
        a = inputs[name]
        if name == "specimen_counts":
            a.flat[0] = -0.0  # Provenance distinguishes negative zero.
        elif name in {"dark_counts", "central_counts"}:
            a = a.astype(">f4")  # Non-native widths/endian legal outside specimen.
        elif name in {"flat_counts", "structured_counts"}:
            a = a.astype("<i2")
        elif name == "heldout_counts":
            a = a.astype("u2")
        if layout == "fortran":
            a = np.asfortranarray(a)
        elif layout == "reverse":
            a = a[..., ::-1]
        elif layout == "stride":
            b = np.empty((*a.shape[:-1], a.shape[-1] * 2), dtype=a.dtype)
            b[..., ::2] = a
            a = b[..., ::2]
        elif layout == "readonly":
            a.setflags(write=False)
        else:
            a = np.broadcast_to(a[..., :1], a.shape)
        inputs[name] = a
    inputs["calibration_origin_um_zyx"] = TupleSubclass(CAL_ORIGIN)
    inputs["sweep_scales"] = (2, 0.5, 2)  # Legal order and duplicates.
    before = snapshots(inputs)
    state = np.geterr().copy(), list(warnings.filters), random.getstate(), np.random.get_state()
    result = workflow(**inputs)
    assert result.status == "unavailable" and result.stage == "handoff"
    assert snapshots(inputs) == before
    assert np.geterr() == state[0] and warnings.filters == state[1]
    assert random.getstate() == state[2]
    after_rng = np.random.get_state()
    assert after_rng[0] == state[3][0] and after_rng[2:] == state[3][2:]
    np.testing.assert_array_equal(after_rng[1], state[3][1])
    assert_input_provenance(result.provenance, inputs)
    assert result.provenance["controls"]["sweep_scales"] == (2.0, 0.5, 2.0)


def assert_input_provenance(provenance, inputs):
    assert provenance["schema"] == "ra13.raw_sim_workflow.v1"
    assert set(provenance["inputs"]) == set(ARRAY_NAMES)
    for name in ARRAY_NAMES:
        a = inputs[name]
        entry = provenance["inputs"][name]
        assert type(entry["shape"]) is tuple and entry["shape"] == a.shape
        assert entry["dtype"] == a.dtype.str
        assert entry["nbytes"] == a.size * a.itemsize
        assert entry["sha256"] == logical_sha256(a)
        axes = (
            "frame,y,x"
            if name in ARRAY_NAMES[1:4]
            else "z,y,x"
            if name == "central_counts"
            else "orientation,phase,z,y,x"
        )
        actual_axes = entry["axes"]
        assert actual_axes == axes or actual_axes == tuple(axes.split(","))


def test_w6_finite_conversion_rounding_and_large_legal_controls(workflow):
    inputs = unavailable_inputs()
    for name in ARRAY_NAMES[1:]:
        inputs[name] = np.full(inputs[name].shape, 2**53 + 1, dtype=np.uint64)
    inputs.update(
        max_iterations=10**100,
        max_backtracking_trials=10**100,
        max_refinement_evaluations=10**100,
        training_rms_limit=0,
    )
    result = workflow(**inputs)
    assert result.status == "unavailable" and result.stage == "handoff"
    assert result.camera_estimate.contrast_counts == 0
    np.testing.assert_array_equal(result.camera_estimate.means_counts, float(2**53))
    assert_input_provenance(result.provenance, inputs)
    assert result.provenance["controls"]["max_iterations"] == 10**100


def test_w8_original_representation_not_physical_equivalence(workflow):
    inputs = unavailable_inputs()
    inputs["specimen_counts"].flat[0] = 0.0
    changed = dict(inputs)
    changed["specimen_counts"] = inputs["specimen_counts"].copy()
    changed["specimen_counts"].flat[0] = -0.0
    positive_zero = workflow(**inputs)
    negative_zero = workflow(**changed)
    assert (
        positive_zero.provenance["inputs"]["specimen_counts"]["sha256"]
        != negative_zero.provenance["inputs"]["specimen_counts"]["sha256"]
    )
    endian_changed = dict(inputs)
    endian_changed["central_counts"] = inputs["central_counts"].astype(
        ">f8" if np.little_endian else "<f8"
    )
    other = workflow(**endian_changed)
    assert (
        positive_zero.provenance["inputs"]["central_counts"]["sha256"]
        != other.provenance["inputs"]["central_counts"]["sha256"]
    )
    assert positive_zero.status == other.status == "unavailable"


@pytest.mark.parametrize(
    "case", ["partial_gradient", "initial_score", "derived_spacing", "zero_direction"]
)
def test_w7_real_specimen_and_geometry_outcomes(workflow, noiseless, case):
    inputs = dict(noiseless)
    if case == "partial_gradient":
        inputs["specimen_counts"] = np.full((3, 5, *SPEC_SHAPE), 4e40)
    elif case == "initial_score":
        inputs["specimen_counts"] = np.full((3, 5, *SPEC_SHAPE), 4e200)
    elif case == "derived_spacing":
        inputs["specimen_detector_spacing_um_zyx"] = (
            0.21,
            float.fromhex("0x0.0000000000001p-1022"),
            0.11,
        )
    else:
        inputs["specimen_counts"] = np.full((3, 5, *SPEC_SHAPE), 7.0)
    _, h, f = composition(inputs)
    result = workflow(**inputs)
    if h.status != "predictive_estimate":
        assert case == "derived_spacing"
        assert h.status == "numerical_incomplete"
        assert_handoff_stop(result, h)
        return
    assert f is not None
    same_public_record(result.specimen_fit, f)
    if case == "zero_direction":
        assert result.status == "completed_finite_fit"
        assert f.stop_reason == "no_projected_direction"
        np.testing.assert_array_equal(f.source_relative, 0)
    else:
        assert result.status == "numerical_incomplete" and result.stage == "specimen"
        assert result.reason_code == f.stop_reason
        assert result.failure_code == f.failure_code and result.message == f.message
        if case == "partial_gradient":
            assert f.stage == "initial_gradient"
            assert f.source_relative is not None and f.best_score is not None
            np.testing.assert_array_equal(f.source_relative, 0)
        else:
            assert f.stage == "initial_score" and f.source_relative is f.best_score is None


def test_w7_limits_are_preserved_as_finite_not_convergence(positive):
    fit = positive.specimen_fit
    assert fit.status == "completed_finite_fit" and fit.stop_reason == "iteration_limit"
    assert fit.max_iterations == 1 and fit.max_backtracking_trials == 4
    assert fit.counts.trials_accepted == 1 and fit.counts.best_updates == 2
    assert fit.attempt_trace[-1].gradient_state == "not_needed"
    assert fit.best_score.total_objective < fit.initial_score.total_objective
    assert fit.source_relative.dtype == np.dtype("float32")
    assert np.all(np.isfinite(fit.source_relative)) and np.all(fit.source_relative >= 0)
    # Presence matters: zero is a valid finite evaluation-limit diagnostic.
    assert positive.handoff.refinement.status is not None
    assert positive.handoff.refinement.nfev is not None


def metadata_leaves(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from metadata_leaves(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from metadata_leaves(item)
    else:
        yield value


def contains_metadata(value, expected):
    if isinstance(value, dict):
        return any(contains_metadata(v, expected) for v in value.values())
    if isinstance(value, (tuple, list)):
        return tuple(value) == expected or any(contains_metadata(v, expected) for v in value)
    return False


def test_w8_complete_provenance_and_frozen_result(workflow, positive, noiseless):
    p = positive.provenance
    assert_input_provenance(p, noiseless)
    assert p["source"] == noiseless["source"]
    assert p["calibration_id"] == p["specimen_calibration_id"] == noiseless["calibration_id"]
    for name in CONTROL_NAMES:
        assert p["controls"][name] == noiseless[name]
    # Nested descriptive key spelling is not prescribed. Assert the named values.
    geometry = list(metadata_leaves(p["geometry"]))
    for expected in (CAL_ORIGIN, SPEC_ORIGIN, CAL_D, SPEC_D, SPEC_SHAPE, (2, 4, 6)):
        assert contains_metadata(p["geometry"], expected), (expected, geometry)
    for name in ("units", "model", "versions", "limits"):
        assert p[name]
    model_values = list(metadata_leaves(p["model"]))
    model_text = str(p["model"]).lower()
    for value in (0.488, 0.525, 1.515, 1.4, 128):
        assert value in model_values or str(value) in model_text
    assert "ra12" in model_text and "specimen" in model_text
    unit_text = str(p["units"]).lower()
    assert all(word in unit_text for word in ("counts", "integrated", "relative"))
    limit_text = str(p["limits"]).lower()
    assert all(
        word in limit_text
        for word in (
            "finite",
            "global",
            "converg",
            "confidence",
            "instrument",
            "resolution",
            "recovery",
        )
    )
    import platform

    import scipy

    versions = set(str(v) for v in metadata_leaves(p["versions"]))
    assert {platform.python_version(), np.__version__, scipy.__version__} <= versions
    assert not any(isinstance(v, np.ndarray) for v in metadata_leaves(p))
    assert {
        name
        for name in dir(positive)
        if not name.startswith("_") and not callable(getattr(positive, name))
    } == {
        "status",
        "stage",
        "reason_code",
        "failure_code",
        "message",
        "camera_estimate",
        "handoff",
        "specimen_fit",
        "provenance",
    }
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        positive.status = "recovered"
    other = workflow(**noiseless)
    p["inputs"]["specimen_counts"]["sha256"] = "caller changed metadata"
    assert other.provenance["inputs"]["specimen_counts"]["sha256"] == logical_sha256(
        noiseless["specimen_counts"]
    )
    # Restore shared fixture metadata so test order cannot influence observations.
    p["inputs"]["specimen_counts"]["sha256"] = logical_sha256(noiseless["specimen_counts"])


@pytest.mark.parametrize(
    "forbidden",
    [
        "true_camera",
        "true_phases",
        "specimen_source",
        "noiseless_mean",
        "support_mask",
        "optimizer_callback",
        "transfer_array",
        "fallback",
    ],
)
def test_w9_truth_and_tuning_keywords_are_not_public(workflow, forbidden):
    with pytest.raises(TypeError):
        workflow(**unavailable_inputs(), **{forbidden: None})


def test_w9_all_keywords_required_and_only_specimen_positional(workflow):
    import inspect

    inputs = unavailable_inputs()
    parameters = inspect.signature(workflow).parameters
    assert set(parameters) == set(inputs)
    assert all(p.default is inspect.Parameter.empty for p in parameters.values())
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY
        for name, p in parameters.items()
        if name != "specimen_counts"
    )
    for name in inputs:
        missing = dict(inputs)
        del missing[name]
        with pytest.raises(TypeError):
            workflow(**missing)
    with pytest.raises(TypeError):
        workflow(inputs["specimen_counts"], inputs["dark_counts"])
    keyword_inputs = dict(inputs)
    raw = keyword_inputs.pop("specimen_counts")
    assert workflow(raw, **keyword_inputs).status == "unavailable"


def test_w9_exception_preserves_inputs_and_policies(workflow):
    inputs = camera_range_inputs()
    inputs["regularization"] = 0
    before = snapshots(inputs)
    with np.errstate(all="raise"), warnings.catch_warnings():
        warnings.simplefilter("error")
        error_policy = np.geterr().copy()
        warning_policy = list(warnings.filters)
        with pytest.raises(SimreconError) as captured:
            workflow(**inputs)
        assert captured.value.code == "invalid_raw_sim_workflow"
        assert snapshots(inputs) == before
        assert np.geterr() == error_policy and warnings.filters == warning_policy


def test_fixture_hash_observer_preserves_endian_signed_zero_and_layout():
    import hashlib

    a = np.array([[[0.0, -0.0], [1.0, -2.0]]], dtype=">f8")
    assert (
        logical_sha256(a)
        == hashlib.sha256(
            bytes.fromhex("000000000000000080000000000000003ff0000000000000c000000000000000")
        ).hexdigest()
    )
    assert logical_sha256(a) == logical_sha256(np.asfortranarray(a))
    assert logical_sha256(a) != logical_sha256(a.astype("<f8"))
    b = a.copy()
    b[0, 0, 1] = 0
    assert logical_sha256(a) != logical_sha256(b)
