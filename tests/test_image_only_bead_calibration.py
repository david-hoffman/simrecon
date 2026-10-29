"""Blind A public-boundary tests for image-only-bead-calibration-v1.

The complete obligation inventory, keeper families and explicit proof limits
precede executable definitions in image_only_bead_calibration_fixture.py.
Source-free runner is required. Missing module/operation is unavailable evidence,
not product-red; no skip, fallback implementation or decision mock is supplied.
"""

from __future__ import annotations

import importlib
import itertools
import math
import random
import warnings
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from image_only_bead_calibration_fixture import (
    AXIAL_SHAPE,
    EPS,
    FIELDS,
    RANGE_SHAPE,
    SHAPE,
    SMALLEST,
    D,
    arguments,
    assert_finite_score,
    assert_independent,
    assert_initial_brightness,
    assert_ledger,
    assert_same,
    camera,
    finite_predictions,
    improving_pair_arguments,
    improving_pair_qualification,
    inward_upper,
    observations,
    output_arrays,
    poll_range_arguments,
    poll_range_qualification,
)
from simrecon import ScalarCameraEstimate, SimreconError, estimate_scalar_camera

bead = importlib.import_module("scripts.image_only_bead_calibration")
pilot = importlib.import_module("scripts.image_only_calibration_pilot")
fit = bead.fit_bead_calibration


class ArraySubclass(np.ndarray):
    """Represent an explicitly forbidden raw array subclass."""


class TupleSubclass(tuple):
    """Distinguish the accepted origin and forbidden scale containers."""


class IntSubclass(int):
    """Represent a forbidden numeric subclass."""


class FloatSubclass(float):
    """Represent a forbidden numeric subclass."""


class StringSubclass(str):
    """Represent an accepted opaque source value."""


class CameraSubclass(ScalarCameraEstimate):
    """Represent a permitted camera record subclass."""


def unavailable_inputs(**changes: Any) -> dict[str, Any]:
    values = arguments(camera_estimate=camera(contrast_counts=0.0))
    values.update(changes)
    return values


@pytest.mark.parametrize(
    "missing",
    (
        "central_counts",
        "structured_counts",
        "heldout_counts",
        "camera_estimate",
        "origin_um_zyx",
        "sweep_scales",
    ),
)
def test_binding_all_arguments_required(missing: str) -> None:
    values = arguments()
    del values[missing]
    with pytest.raises(TypeError):
        fit(**values)


@pytest.mark.parametrize("unknown", ("truth",))
def test_binding_no_truth_optimizer_or_extra_inputs(unknown: str) -> None:
    with pytest.raises(TypeError):
        fit(**arguments(), **{unknown: None})


def test_binding_only_central_may_be_positional() -> None:
    values = arguments()
    central = values.pop("central_counts")
    with pytest.raises(TypeError):
        fit(central, values.pop("structured_counts"), **values)


ARRAY_NAMES = ("central_counts", "structured_counts", "heldout_counts")
INVALID_ARRAY_FORMS = (
    "list",
    "bool",
    "complex",
    "object",
    "string",
    "subclass",
    "masked",
    "nan",
    "posinf",
    "neginf",
    "rank",
    "wrong_shape",
    "empty",
)


@pytest.mark.parametrize(
    "name,form",
    [
        *(
            (name, form)
            for name in ARRAY_NAMES
            for form in INVALID_ARRAY_FORMS
            if form not in ("posinf", "neginf")
        ),
        ("central_counts", "posinf"),
        ("central_counts", "neginf"),
    ],
)
def test_invalid_raw_arrays_before_unavailable(name: str, form: str) -> None:
    values = unavailable_inputs()
    array = values[name]
    if form == "list":
        invalid = array.tolist()
    elif form in ("bool", "complex", "object", "string"):
        invalid = array.astype(
            {"bool": bool, "complex": complex, "object": object, "string": str}[form]
        )
    elif form == "subclass":
        invalid = array.view(ArraySubclass)
    elif form == "masked":
        invalid = np.ma.array(array)
    elif form in ("nan", "posinf", "neginf"):
        invalid = array.copy()
        invalid.flat[-1] = {"nan": np.nan, "posinf": np.inf, "neginf": -np.inf}[form]
    elif form == "rank":
        invalid = array.reshape(-1)
    elif form == "empty":
        invalid = array[..., :0]
    else:
        invalid = array[..., :-1]
        if name == "central_counts":
            values["structured_counts"] = values["structured_counts"][..., :-1]
            values["heldout_counts"] = values["heldout_counts"][..., :-1]
            # Keep shape agreement but violate the central rank requirement.
            invalid = invalid[None, ...]
    values[name] = invalid
    with pytest.raises(SimreconError) as error:
        fit(**values)
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("shape", ((0, 2, 2), (1, 1, 2), (1, 2, 1)))
def test_invalid_physical_box_even_before_normalization(shape: tuple[int, int, int]) -> None:
    values = unavailable_inputs(
        central_counts=np.zeros(shape),
        structured_counts=np.zeros((3, 9, *shape)),
        heldout_counts=np.zeros((3, 5, *shape)),
    )
    with pytest.raises(SimreconError) as error:
        fit(**values)
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize(
    "name,leading",
    (
        ("structured_counts", (2, 9)),
        ("structured_counts", (3, 8)),
        ("heldout_counts", (2, 5)),
        ("heldout_counts", (3, 6)),
    ),
)
def test_invalid_orientation_command_dimensions(name: str, leading: tuple[int, int]) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(**{name: np.zeros((*leading, *SHAPE))}))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("name", ARRAY_NAMES)
def test_finite_original_values_follow_platform_conversion_range(name: str) -> None:
    # On platforms with no wider floating format this case does not exist.
    # This is a reported representation limit, not a skip or a product refusal.
    if np.finfo(np.longdouble).max > np.finfo(np.float64).max:
        values = unavailable_inputs()
        invalid = values[name].astype(np.longdouble)
        invalid.flat[-1] = np.finfo(np.longdouble).max
        assert np.isfinite(invalid).all()
        values[name] = invalid
        with pytest.raises(SimreconError) as error:
            fit(**values)
        assert error.value.code == "invalid_image_only_bead_calibration"
    else:
        assert np.finfo(np.longdouble).max == np.finfo(np.float64).max
        values = unavailable_inputs()
        values[name] = np.full(values[name].shape, np.finfo(np.longdouble).max, dtype=np.longdouble)
        result = fit(**values)
        assert result.status == "normalization_unavailable"


BAD_SCALARS = (
    True,
    np.int64(1),
    np.float64(1),
    IntSubclass(1),
    FloatSubclass(1),
    complex(1),
    "1",
    None,
    math.inf,
    -math.inf,
    math.nan,
    10**400,
)


@pytest.mark.parametrize("bad", BAD_SCALARS)
def test_invalid_contrast_scalar(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(camera_estimate=camera(contrast_counts=bad)))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("bad", BAD_SCALARS)
def test_invalid_origin_member(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(origin_um_zyx=(0, bad, 0)))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("bad", (*BAD_SCALARS, 0, -0.0, -1))
def test_invalid_scale_member_before_unavailable(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(sweep_scales=(1.0, bad)))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("bad", ([], [1.0], (), TupleSubclass((1.0,)), np.array([1.0]), 1.0, None))
def test_invalid_scales_container(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(sweep_scales=bad))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("bad", ([0, 0, 0], (0, 0), (0, 0, 0, 0), np.zeros(3), None))
def test_invalid_origin_container(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(origin_um_zyx=bad))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize(
    "field,bad",
    (
        ("means_counts", [0.0, 1.0, 2.0]),
        ("means_counts", np.zeros(2)),
        ("means_counts", np.zeros((1, 3))),
        ("means_counts", np.zeros(3, dtype=np.float32)),
        ("means_counts", np.zeros(3, dtype=np.int64)),
        ("means_counts", np.zeros(3, dtype=bool)),
        ("means_counts", np.zeros(3, dtype=complex)),
        ("means_counts", np.zeros(3, dtype=object)),
        ("means_counts", np.zeros(3, dtype=str)),
        ("means_counts", np.zeros(3, dtype=">f8")),
        ("means_counts", np.zeros(3).view(ArraySubclass)),
        ("means_counts", np.ma.array(np.zeros(3))),
        ("means_counts", np.array([0.0, np.inf, 1.0])),
        ("means_counts", np.array([np.nan, 0.0, 1.0])),
        ("means_counts", np.array([0.0, 0.0, -np.inf])),
        ("source", ""),
        ("source", " \t\n"),
        ("source", 1),
        ("source", None),
    ),
)
def test_invalid_consumed_camera_fields(field: str, bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(camera_estimate=camera(contrast_counts=0, **{field: bad})))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize("bad", (None, {}, object()))
def test_invalid_camera_type(bad: Any) -> None:
    with pytest.raises(SimreconError) as error:
        fit(**unavailable_inputs(camera_estimate=bad))
    assert error.value.code == "invalid_image_only_bead_calibration"


@pytest.mark.parametrize(
    "layout",
    (
        "signed_int",
        "unsigned_int",
        "float32",
        "big_endian",
        "fortran",
        "reversed",
        "strided",
        "readonly",
        "rounding",
        "finite_underflow",
    ),
)
def test_positive_raw_representations(layout: str) -> None:
    values = unavailable_inputs()
    for name in ARRAY_NAMES:
        array = values[name]
        if layout in ("signed_int", "unsigned_int", "float32", "big_endian"):
            array = array.astype(
                {
                    "signed_int": np.int64,
                    "unsigned_int": np.uint64,
                    "float32": np.float32,
                    "big_endian": ">f8",
                }[layout]
            )
        elif layout == "fortran":
            array = np.asfortranarray(array)
        elif layout == "reversed":
            array = array[..., ::-1]
        elif layout == "strided":
            padded = np.empty((*array.shape[:-1], array.shape[-1] * 2))
            padded[..., ::2] = array
            array = padded[..., ::2]
        elif layout == "readonly":
            array.flags.writeable = False
        elif layout == "rounding":
            array = np.full(array.shape, 2**53 + 1, dtype=np.uint64)
        else:
            array = np.full(array.shape, np.finfo(np.longdouble).tiny, dtype=np.longdouble)
        values[name] = array
    result = fit(**values)
    assert result.status == "normalization_unavailable"
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_positive_minimum_box_and_extreme_normalized_metadata() -> None:
    shape = (1, 2, 2)
    means = np.array([99.0, 0.0, 2.0, 0.0, -99.0, 0.0])[::2]
    means.flags.writeable = False
    estimate = camera(
        means_counts=means,
        contrast_counts=-1,
        source=StringSubclass("  opaque  "),
        gain_counts_per_e=object(),
        information_codes=object(),
    )
    estimate = CameraSubclass(
        **{
            name: getattr(estimate, name)
            for name in (
                "means_counts",
                "variances_counts2",
                "frame_means_counts",
                "frame_variances_counts2",
                "empirical_mean_se_counts",
                "contrast_counts",
                "gain_counts_per_e",
                "information_codes",
                "source",
            )
        }
    )
    result = fit(
        np.zeros(shape),
        structured_counts=np.zeros((3, 9, *shape)),
        heldout_counts=np.zeros((3, 5, *shape)),
        camera_estimate=estimate,
        origin_um_zyx=TupleSubclass((10**300, -0.0, -(10**300))),
        sweep_scales=(SMALLEST, 1e308, 1, 2, 2, 0.5),
    )
    assert result.status == "normalization_unavailable"
    assert result.origin_um_zyx == (float(10**300), -0.0, float(-(10**300)))
    assert result.camera_source == "  opaque  " and type(result.camera_source) is str
    assert result.blank_counts == 2.0 and result.contrast_counts == -1.0
    assert result.sweep_scales == (SMALLEST, 1e308, 1.0, 2.0, 2.0, 0.5)
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.mark.parametrize("contrast", (0, -2))
def test_unavailable_has_exact_absence_and_zero_ledgers(contrast: int | float) -> None:
    result = fit(
        **unavailable_inputs(
            camera_estimate=camera(contrast_counts=contrast), sweep_scales=(1, 2, 1)
        )
    )
    assert result.status == "normalization_unavailable" and result.stage == "normalization"
    assert result.initialization_notes is None
    assert result.training_objectives_q128_q256_q512 == (None, None, None)
    assert result.unprobed_coordinates == tuple(range(47))
    assert result.counts.planned_poll_attempts == 282
    for evidence in result.coordinate_evidence:
        assert evidence.information_codes == ()
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.mark.parametrize("kind", ("all_zero", "negative", "one_peak", "zero_window"))
def test_information_failure_is_not_range_or_fabricated_candidate(kind: str) -> None:
    shape = (9, 2, 2) if kind == "zero_window" else SHAPE
    y = np.zeros(shape)
    if kind == "negative":
        y.fill(-1)
    elif kind == "one_peak":
        y[0, 0, 7] = 1
    elif kind == "zero_window":
        # Gaussian tail outside the <=0.5um suppression ball has a z-clipped
        # centroid window containing no positive unsmoothed sample.
        y[4, 0, 0] = 1
    result = fit(
        5 + 2 * y,
        structured_counts=np.zeros((3, 9, *shape)),
        heldout_counts=np.zeros((3, 5, *shape)),
        camera_estimate=camera(),
        origin_um_zyx=(0, 0, 0),
        sweep_scales=(1,),
    )
    assert result.status == "initialization_failed" and result.stage == "initialization"
    assert result.initialization_notes is None
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.fixture(scope="module")
def subnormal_result() -> Any:
    return fit(**arguments())


@pytest.fixture(scope="module")
def moving_result() -> Any:
    return fit(**arguments(shape=AXIAL_SHAPE, sweep_scales=(0.5,)))


@pytest.fixture(scope="module")
def mixed_schedule_result() -> Any:
    return fit(**arguments(sweep_scales=(SMALLEST, 1e308, SMALLEST)))


def test_initialization_full_47_state_units_and_fixed_nominal_settings(
    subnormal_result: Any,
) -> None:
    result = subnormal_result
    assert result.status == "completed_finite_fit"
    expected_centers = np.array(
        [[0.0625, 0.05, 0.05], [0.0625, 0.05, 0.60], [0.0625, 0.05, inward_upper(15, D[2])]]
    )
    # Detector center products/centroid arithmetic may round, but the clamp
    # must use the EXACT inward upper bound. No pixel-coordinate round trip.
    np.testing.assert_allclose(
        result.initial_coordinates[:9].reshape(3, 3), expected_centers, rtol=32 * EPS, atol=0
    )
    assert result.initial_coordinates[8] == inward_upper(15, D[2])
    np.testing.assert_array_equal(result.initial_coordinates[9:12], np.ones(3))
    np.testing.assert_allclose(
        result.initial_coordinates[12:14],
        [math.acos(1 / math.sqrt(3)) / (math.pi / 2), 0.5],
        rtol=32 * EPS,
    )
    np.testing.assert_array_equal(result.initial_coordinates[[14, 16, 18]], np.full(3, 1.2 / 1.515))
    np.testing.assert_array_equal(result.initial_coordinates[[15, 17, 19]], [0, 1 / 3, 2 / 3])
    np.testing.assert_array_equal(
        result.initial_coordinates[20:].reshape(3, 9),
        np.tile([0, 1 / 5, 2 / 5, 3 / 5, 4 / 5, 1 / 10, 3 / 10, 7 / 10, 9 / 10], (3, 1)),
    )
    import scipy

    assert (
        type(result.initialization_notes) is str
        and scipy.__version__ in result.initialization_notes
    )
    # Independently expected accounting is 3 clipped windows, 0 overlaps,
    # 5 clamps. The contract supplies no machine-readable notes grammar;
    # imposing decimal tokens here would reject legitimate prose. Content
    # accounting remains a manual public-result review obligation for B/D.
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_initialization_tie_lexicographic_edges_and_inward_clamp() -> None:
    c, s, h = observations(edge=True, tie=True)
    result = fit(**arguments(central_counts=c, structured_counts=s, heldout_counts=h))
    assert result.status == "completed_finite_fit"
    expected_x = [0.05, 7.5 * D[2], inward_upper(15, D[2])]
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx[:, 2], expected_x, rtol=32 * EPS
    )
    assert result.initial_candidate.centers_um_zyx[0, 2] == 0.05
    assert result.initial_candidate.centers_um_zyx[-1, 2] == inward_upper(15, D[2])
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_initialization_smooths_signed_data_and_uses_unsmoothed_positive_centroid() -> None:
    central, structured, heldout = observations(shape=RANGE_SHAPE)
    y = (central - 5) / 2
    y[0, 0, 2] = -8
    # The negative neighbor moves the smoothed first-object maximum to x=0
    # and below both other peaks. Clipping before smoothing reverses this
    # order. Its unsmoothed centroid still uses the positive x=1 pixel only.
    result = fit(
        **arguments(
            shape=RANGE_SHAPE,
            central_counts=5 + 2 * y,
            structured_counts=structured,
            heldout_counts=heldout,
        )
    )
    assert result.status == "completed_finite_fit"
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx[:, 2],
        [0.68, inward_upper(16, D[2]), 0.12],
        rtol=32 * EPS,
    )
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_initialization_weighted_physical_centroid_without_pixel_round_trip() -> None:
    central, structured, heldout = observations(shape=RANGE_SHAPE)
    y = (central - 5) / 2
    y[0, 1, 8], y[1, 0, 8] = 1.0, 0.25
    # Positive window weights 6,1,1/4; all other window samples are negative.
    expected = [(7 * 0.0625 + 0.25 * 0.1875) / 7.25, (6.25 * 0.04 + 1 * 0.12) / 7.25, 8.5 * D[2]]
    result = fit(
        **arguments(
            shape=RANGE_SHAPE,
            central_counts=5 + 2 * y,
            structured_counts=structured,
            heldout_counts=heldout,
        )
    )
    assert result.status == "completed_finite_fit"
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx[1], expected, rtol=64 * EPS, atol=0
    )
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_initialization_exact_suppression_boundary_and_nonlocal_peak_window() -> None:
    shape = (9, 2, 16)
    y = np.zeros(shape)
    y[0, 0, 0], y[4, 0, 0], y[4, 0, 4], y[8, 0, 15] = 16, 8, 0.5, 4
    # The sample (4,0,0) is exactly 0.5 um from the first peak and must be
    # suppressed. (4,0,1) is just outside that ball and wins next, despite
    # not being a local maximum. Its +/-3 x window includes the x=4 sample;
    # the incorrectly retained x=0 peak's window would exclude that sample.
    # This moves the positive centroid above the 0.05 um lower clamp.
    result = fit(
        **arguments(
            central_counts=5 + 2 * y,
            structured_counts=np.full((3, 9, *shape), 1e200),
            heldout_counts=np.zeros((3, 5, *shape)),
        )
    )
    # Stop at the prescribed initial loss overflow after initialization. This
    # isolates the initializer without a fake predictor or a search seam.
    assert result.status == "numerical_incomplete" and result.stage == "initial"
    expected = np.array(
        [
            [0.0625, 0.05, 0.05],
            [0.5625, 0.05, (8 * 0.04 + 0.5 * 0.36) / 8.5],
            [1.0625, 0.05, inward_upper(16, D[2])],
        ]
    )
    np.testing.assert_allclose(
        result.initial_candidate.centers_um_zyx, expected, rtol=64 * EPS, atol=0
    )
    assert result.initialization_notes is not None
    # Manual notes accounting: 3 clipped windows, 1 overlapping window pair
    # (the inclusive z=2 plane), 5 clamped coordinates. Prose is unspecified.
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.mark.parametrize("layout", ("big_endian", "fortran", "strided", "readonly", "float32"))
def test_positive_layouts_normalize_to_same_actual_observations(
    layout: str, subnormal_result: Any
) -> None:
    values = arguments()
    for name in ARRAY_NAMES:
        original = values[name]
        if layout == "big_endian":
            values[name] = original.astype(">f8")
        elif layout == "fortran":
            values[name] = np.asfortranarray(original)
        elif layout == "strided":
            padded = np.empty((*original.shape[:-1], original.shape[-1] * 2))
            padded[..., ::2] = original
            values[name] = padded[..., ::2]
        elif layout == "readonly":
            original.flags.writeable = False
        else:
            values[name] = original.astype(np.float32)
        np.testing.assert_array_equal(values[name], original)
    result = fit(**values)
    assert_same(result, subnormal_result)
    for array in output_arrays(result):
        assert all(not np.shares_memory(array, values[name]) for name in ARRAY_NAMES)


def test_relative_count_gauge_and_unconsumed_camera_fields(subnormal_result: Any) -> None:
    values = arguments()
    for name in ARRAY_NAMES:
        values[name] = 2 * values[name] - 16
    values["camera_estimate"] = camera(
        means_counts=np.array([-999.0, -6.0, 123.0]),
        contrast_counts=4,
        gain_counts_per_e=1e300,
        information_codes=("arbitrary",),
    )
    result = fit(**values)
    for name in FIELDS["BeadCalibrationResult"]:
        if name not in ("blank_counts", "contrast_counts"):
            assert_same(getattr(result, name), getattr(subnormal_result, name))
    assert result.blank_counts == -6.0 and result.contrast_counts == 4.0


def test_real_image_derived_camera_record_composes_without_physical_gain(
    subnormal_result: Any,
) -> None:
    estimate = estimate_scalar_camera(
        np.full((2, 1, 2), -7.0),
        blank_counts=np.full((2, 1, 2), 5.0),
        flat_counts=np.full((2, 1, 2), 7.0),
        source="opaque estimated camera",
    )
    assert estimate.gain_counts_per_e is None and estimate.contrast_counts == 2
    result = fit(**arguments(camera_estimate=estimate))
    assert_same(result, subnormal_result)


def test_subnormal_scale_scores_unchanged_trials_and_reports_unprobed(
    subnormal_result: Any,
) -> None:
    result = subnormal_result
    assert result.status == "completed_finite_fit"
    assert len(result.poll_attempts) == 94 and len(result.objective_trace) == 97
    assert result.unprobed_coordinates == tuple(range(47))
    for attempt in result.poll_attempts:
        assert attempt.outcome == "scored"
        assert attempt.coordinate_changed is attempt.parameter_changed is False
        assert "unchanged_coordinate" in attempt.information_codes
        assert "unchanged_parameter" in attempt.information_codes
        if attempt.coordinate_index < 9:
            assert "occupancy_equivalent_center" in attempt.information_codes
    # Different valid reductions of unchanged images can differ in their
    # last bits. Selection and equality codes follow reported scores in the
    # ledger audit; numerical accuracy is a separate finite-equation check.
    np.testing.assert_array_equal(result.initial_coordinates, result.frozen_coordinates)
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_schedule_all_coordinates_strict_pair_decisions_and_fixed_scales(
    moving_result: Any,
) -> None:
    assert moving_result.status == "completed_finite_fit"
    assert len(moving_result.poll_attempts) == 94
    assert {a.coordinate_index for a in moving_result.poll_attempts} == set(range(47))
    assert any(
        a.coordinate_changed and a.parameter_changed
        for a in moving_result.poll_attempts
        if a.outcome == "scored"
    )
    assert any(
        a.outcome == "infeasible" and a.infeasibility_reason == "center_geometry"
        for a in moving_result.poll_attempts
    )
    assert_ledger(moving_result, bead, pilot.PilotCandidate)


def test_schedule_order_repeats_huge_legal_scale_no_clamp_or_early_stop(
    mixed_schedule_result: Any,
) -> None:
    result = mixed_schedule_result
    assert result.status == "completed_finite_fit"
    assert result.sweep_scales == (SMALLEST, 1e308, SMALLEST)
    assert result.counts.attempted_polls == 282 and result.counts.completed_sweeps == 3
    for attempt in result.poll_attempts[94:188]:
        assert attempt.outcome == "infeasible"
        assert attempt.infeasibility_reason == (
            "center_geometry" if attempt.coordinate_index < 9 else "coordinate_bounds"
        )
    np.testing.assert_array_equal(result.initial_coordinates, result.frozen_coordinates)
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_zero_brightness_is_a_legal_fit_and_information_codes_stay_literal() -> None:
    values = arguments(sweep_scales=(10.0, 0.5))
    values["structured_counts"] = np.full((3, 9, *SHAPE), 5 - 2 * 1024.0)
    result = fit(**values)
    assert result.status == "completed_finite_fit"
    # The negative training observations are retained. At the brightness
    # pairs, initial beams/carriers/phases remain fixed. The five equally
    # spaced commands give summed illumination 5 per orientation at every
    # source/focus, so their 15*1024 cross term dominates the central Y<=8
    # term. Decreasing each B to zero strictly improves this finite case.
    np.testing.assert_array_equal(result.frozen_candidate.brightness_relative, np.zeros(3))
    witnessed_centers = witnessed_other = 0
    for attempt in result.poll_attempts[94:]:
        if attempt.outcome != "scored":
            continue
        if attempt.coordinate_index < 9:
            assert "zero_brightness_center" in attempt.information_codes
            witnessed_centers += 1
        if attempt.coordinate_index < 9 or attempt.coordinate_index >= 12:
            assert "zero_total_brightness" in attempt.information_codes
            witnessed_other += 1
    assert witnessed_centers > 0 and witnessed_other > 0
    np.testing.assert_array_equal(result.heldout_prediction, np.zeros((3, 5, *SHAPE)))
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.mark.parametrize(
    "target", ("gamma_zero", "gamma_one", "eta_zero", "eta_one", "rho_zero", "rho_one")
)
def test_endpoints_exact_beam_zeros_and_coordinate_parameter_distinction(target: str) -> None:
    gamma = math.acos(1 / math.sqrt(3)) / (math.pi / 2)
    if target.startswith("gamma"):
        index, scale = 12, (gamma if target.endswith("zero") else 1 - gamma) / 0.05
    elif target.startswith("eta"):
        index, scale = 13, 10.0
    else:
        index, scale = 14, ((1.2 / 1.515) if target.endswith("zero") else 1 - 1.2 / 1.515) / 0.01
    result = fit(**arguments(sweep_scales=(scale,)))
    assert result.status == "completed_finite_fit"
    attempts = [a for a in result.poll_attempts if a.coordinate_index == index]
    sign = -1 if target.endswith("zero") else 1
    trial = next(a for a in attempts if a.sign == sign)
    # The exact normalized endpoint is checked before any claim about beams.
    assert trial.trial_coordinates[index] == (0 if sign == -1 else 1)
    assert trial.outcome == "scored"
    if trial.outcome == "scored":
        candidate = result.objective_trace[trial.score_index].candidate
        if target == "gamma_zero":
            np.testing.assert_array_equal(candidate.beam_amplitudes[1:], [0, 0])
        elif target == "gamma_one":
            assert candidate.beam_amplitudes[0] == 0
        elif target == "eta_zero":
            assert candidate.beam_amplitudes[2] == 0
        elif target == "eta_one":
            assert candidate.beam_amplitudes[1] == 0
        elif target == "rho_zero":
            np.testing.assert_array_equal(candidate.carriers_yx_per_um[0], [0, 0])
        elif target == "rho_one":
            # Coordinate 14 precedes angle 15. This represented vector is
            # exact, and Fraction proves it lies strictly inside the domain.
            assert trial.trial_coordinates[15] == 0
            k0 = 1.515 / 0.488
            assert Fraction(k0) < Fraction(1.515) / Fraction(0.488)
            np.testing.assert_array_equal(candidate.carriers_yx_per_um[0], [0, k0])
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_finite_equation_initializer_brightness_and_initial_complete_signed_loss(
    subnormal_result: Any,
) -> None:
    # Not a recovery assertion: independently validate the actual represented
    # candidate against the adopted finite optical/source equation.
    assert_initial_brightness(subnormal_result.initial_candidate, np.array([8.0, 6.0, 4.0]), SHAPE)
    assert_finite_score(subnormal_result.objective_trace[0], arguments())
    assert_finite_score(subnormal_result.objective_trace[1], arguments())


def test_finite_equation_changed_profiles_illumination_and_full_training_loss(
    moving_result: Any,
) -> None:
    # Separate gamma and eta: eta creates unequal side beams, needed to
    # distinguish the source-minus-focus axial sign. Separate carrier radius
    # and angle as well. Center polls require newly occupied source profiles.
    from image_only_calibration_pilot_fixture import unit_sites

    families = (
        (0, 3, 6),  # Axial source movement requires the separate two-plane scene.
        (1, 2, 4, 5, 7, 8),
        range(9, 12),
        range(12, 13),
        range(13, 14),
        range(14, 15),
        range(15, 16),
        range(20, 47),
    )
    for family in families:
        attempt = next(
            a
            for a in moving_result.poll_attempts
            if a.coordinate_index in family
            and a.outcome == "scored"
            and a.parameter_changed
            and (
                a.coordinate_index >= 9 or "occupancy_equivalent_center" not in a.information_codes
            )
        )
        if attempt.coordinate_index < 9:
            b = attempt.coordinate_index // 3
            base = moving_result.objective_trace[attempt.base_score_index].candidate
            trial = moving_result.objective_trace[attempt.score_index].candidate
            assert base.brightness_relative[b] > 0 and trial.brightness_relative[b] > 0
            old_sites = unit_sites(tuple(base.centers_um_zyx[b]), AXIAL_SHAPE)[0]
            new_sites = unit_sites(tuple(trial.centers_um_zyx[b]), AXIAL_SHAPE)[0]
            assert set(map(tuple, old_sites)) != set(map(tuple, new_sites))
        assert_finite_score(
            moving_result.objective_trace[attempt.score_index], arguments(shape=AXIAL_SHAPE)
        )
    assert_finite_score(
        moving_result.objective_trace[moving_result.incumbent_score_index],
        arguments(shape=AXIAL_SHAPE),
    )


def test_finite_equation_exact_frozen_rescores_and_first_five_prediction(
    moving_result: Any,
) -> None:
    import image_only_calibration_pilot_fixture as reference

    result = moving_result
    for score in result.objective_trace[-2:]:
        assert_finite_score(score, arguments(shape=AXIAL_SHAPE))
    _, structured, bound = finite_predictions(result.frozen_candidate, AXIAL_SHAPE, 512)
    reference.assert_prediction_close(result.heldout_prediction, structured[:, :5], bound)


def test_residuals_signed_mean_and_rms_from_complete_frozen_prediction(
    subnormal_result: Any,
) -> None:
    inputs, result = arguments(), subnormal_result
    heldout = (inputs["heldout_counts"] - 5) / 2
    residual = heldout - result.heldout_prediction
    mean = np.empty((3, 5))
    rms = np.empty((3, 5))
    for o, p in itertools.product(range(3), range(5)):
        values = [float(v) for v in residual[o, p].flat]
        mean[o, p] = math.fsum(values) / len(values)
        rms[o, p] = math.sqrt(math.fsum(v * v for v in values) / len(values))
    # 64 pixels, fewer than 8M+64 elementary operations, eps bound inflated
    # for both observer and product reductions. No optical error is added:
    # this obligation is explicitly relative to the returned prediction.
    allowance = (8 * math.prod(SHAPE) + 64) * EPS * np.max(np.abs(residual)) * 8
    np.testing.assert_allclose(result.heldout_residual_mean, mean, atol=allowance, rtol=0)
    np.testing.assert_allclose(result.heldout_residual_rms, rms, atol=allowance, rtol=0)


@pytest.mark.parametrize("moving", (False, True))
def test_origin_and_heldout_only_change_allowed_metadata_summaries(
    moving: bool,
    subnormal_result: Any,
    moving_result: Any,
) -> None:
    baseline = moving_result if moving else subnormal_result
    shape = AXIAL_SHAPE if moving else SHAPE
    values = arguments(shape=shape, sweep_scales=(0.5,) if moving else (SMALLEST,))
    values["heldout_counts"] = values["heldout_counts"] + 4
    values["origin_um_zyx"] = (1e300, -1e300, 123.5)
    changed = fit(**values)
    assert changed.status == "completed_finite_fit"
    for name in FIELDS["BeadCalibrationResult"]:
        if name not in ("origin_um_zyx", "heldout_residual_mean", "heldout_residual_rms"):
            assert_same(getattr(changed, name), getattr(baseline, name))
    heldout = (arguments(shape=shape)["heldout_counts"] - 5) / 2
    residual_scale = max(
        float(np.max(np.abs(heldout - baseline.heldout_prediction))),
        float(np.max(np.abs(heldout + 2 - changed.heldout_prediction))),
    )
    # Bound both float64 mean reductions and their subtraction. This tests
    # the contract's shift relation, not a predetermined search trajectory.
    allowance = (8 * math.prod(shape) + 64) * EPS * residual_scale * 16
    np.testing.assert_allclose(
        changed.heldout_residual_mean - baseline.heldout_residual_mean,
        np.full((3, 5), 2.0),
        rtol=0,
        atol=allowance,
    )
    assert_ledger(changed, bead, pilot.PilotCandidate)
    assert_independent(changed, baseline)


def test_records_frozen_public_types_and_independent_writable_snapshots(
    moving_result: Any, subnormal_result: Any
) -> None:
    result = moving_result
    assert_ledger(result, bead, pilot.PilotCandidate)
    assert_independent(result)
    representatives = (
        result,
        result.counts,
        result.coordinate_evidence[0],
        result.objective_trace[0],
        result.poll_attempts[0],
        result.initial_candidate,
    )
    for record in representatives:
        field = FIELDS[type(record).__name__][0]
        with pytest.raises((AttributeError, TypeError)):
            setattr(record, field, getattr(record, field))
    # Actual mutation of one caller-visible array must leave every other
    # snapshot and later call unaffected. Use a separate result, not fixtures.
    fresh = fit(**arguments())
    arrays = output_arrays(fresh)
    copies = [a.copy() for a in arrays]
    arrays[0].flat[0] += 1
    for array, saved in zip(arrays[1:], copies[1:], strict=True):
        np.testing.assert_array_equal(array, saved)
    again = fit(**arguments())
    assert_same(again, subnormal_result)
    assert_independent(again, subnormal_result, fresh)


def test_initial_range_keeps_constructed_candidate_but_no_success_or_polls() -> None:
    values = arguments()
    values["structured_counts"] = np.full((3, 9, *SHAPE), 1e200)
    result = fit(**values)
    # Direct float64 residual squares are prescribed for the objective.
    assert result.status == "numerical_incomplete" and result.stage == "initial"
    assert result.failure_code == "image_only_bead_calibration_range"
    assert result.initial_candidate is not None and result.initial_coordinates is not None
    assert result.best_candidate is None and result.best_score_index is None
    assert result.incumbent_score_index is None and result.poll_attempts == ()
    assert (
        len(result.objective_trace) == 1
        and result.objective_trace[0].outcome == "numerical_incomplete"
    )
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_poll_range_stops_immediately_and_retains_unresolved_partial_pair() -> None:
    proof = poll_range_qualification()
    assert proof["initial_upper_ratio"] < 1 < proof["square_lower_ratio"]
    result = fit(**poll_range_arguments())
    assert result.status == "numerical_incomplete" and result.stage == "poll"
    assert result.failure_code == "image_only_bead_calibration_range"
    assert result.initial_candidate is not None and result.initialization_notes is not None
    for row, expected in zip(
        result.initial_candidate.centers_um_zyx, proof["centers"], strict=True
    ):
        assert all(
            abs(Fraction(float(a)) - Fraction(float(b))) <= proof["center_error"]
            for a, b in zip(row, expected, strict=True)
        )
    for brightness, (lo, hi) in zip(
        result.initial_candidate.brightness_relative, proof["brightness_intervals"], strict=True
    ):
        assert lo <= Fraction(float(brightness)) / Fraction(2e151) <= hi
    np.testing.assert_array_equal(result.initial_coordinates[9:12], np.ones(3))
    rho = 1.2 / 1.515
    gamma = math.acos(1 / math.sqrt(3)) / (math.pi / 2)
    tail = np.array(
        [
            1,
            1,
            1,
            gamma,
            0.5,
            rho,
            0,
            rho,
            1 / 3,
            rho,
            2 / 3,
            *np.tile([0, 0.2, 0.4, 0.6, 0.8, 0.1, 0.3, 0.7, 0.9], 3),
        ]
    )
    np.testing.assert_array_equal(np.delete(result.initial_coordinates[9:], 3), np.delete(tail, 3))
    np.testing.assert_allclose(result.initial_coordinates[12], gamma, rtol=32 * EPS, atol=0)
    assert result.best_score_index == result.incumbent_score_index == 0
    assert_same(result.best_candidate, result.initial_candidate)
    assert_same(result.best_coordinates, result.initial_coordinates)
    assert len(result.objective_trace) == 2
    assert result.objective_trace[0].stage == "initial"
    assert result.objective_trace[0].outcome == "scored"
    lo, hi = proof["initial_objective_scaled_interval"]
    assert lo <= Fraction(result.objective_trace[0].objective) / Fraction(2e151) ** 2 <= hi
    failed = result.objective_trace[1]
    assert failed.stage == "poll" and failed.pupil_order == 128
    assert failed.outcome == "numerical_incomplete"
    assert failed.candidate is failed.objective is None
    assert failed.failure_code == "image_only_bead_calibration_range"
    assert len(result.poll_attempts) == 20
    for ordinal, attempt in enumerate(result.poll_attempts):
        assert attempt.sweep_index == 0 and attempt.coordinate_index == ordinal // 2
        assert attempt.sign == (-1, 1)[ordinal % 2] and attempt.base_score_index == 0
        assert attempt.selected is (False if ordinal < 18 else None)
        if ordinal < 19:
            assert attempt.outcome == "infeasible" and attempt.score_index is None
            assert attempt.infeasibility_reason == (
                "center_geometry" if ordinal < 18 else "coordinate_bounds"
            )
        else:
            assert attempt.outcome == "numerical_incomplete" and attempt.score_index == 1
            assert attempt.infeasibility_reason is None
            assert attempt.failure_code == "image_only_bead_calibration_range"
        assert attempt.parameter_changed is None and attempt.information_codes == ()
    negative, positive = result.poll_attempts[-2:]
    assert negative.trial_coordinates[9] == -89 and positive.trial_coordinates[9] == 91
    assert_same(failed.coordinates, positive.trial_coordinates)
    expected_counts = (94, 20, 0, 19, 1, 9, 0, 2, 1)
    for name, expected_count in zip(FIELDS["BeadCalibrationCounts"], expected_counts, strict=True):
        assert getattr(result.counts, name) == expected_count
    assert result.unprobed_coordinates == tuple(range(47))
    assert result.frozen_candidate is result.frozen_coordinates is None
    assert (
        result.heldout_prediction
        is result.heldout_residual_mean
        is result.heldout_residual_rms
        is None
    )
    assert result.training_objectives_q128_q256_q512 == (
        result.objective_trace[0].objective,
        None,
        None,
    )
    assert_ledger(result, bead, pilot.PilotCandidate)
    assert_independent(result)


def test_improving_poll_is_best_but_not_incumbent_when_positive_trial_fails() -> None:
    proof = improving_pair_qualification()
    initial_lo, initial_hi = proof["initial_sumsq_ratio"]
    negative_lo, negative_hi = proof["negative_sumsq_ratio"]
    assert 0 < negative_lo <= negative_hi < initial_lo <= initial_hi < 1
    assert proof["positive_square_lower_ratio"] > 1
    values = improving_pair_arguments()
    callers = [values[name] for name in ARRAY_NAMES] + [values["camera_estimate"].means_counts]
    saved = [(a.copy(), a.dtype, a.strides, a.flags.writeable) for a in callers]
    python_random, numpy_random = random.getstate(), np.random.get_state()
    with np.errstate(all="raise"), warnings.catch_warnings():
        warnings.simplefilter("error")
        policy, filters = np.geterr().copy(), list(warnings.filters)
        result = fit(**values)
        assert np.geterr() == policy and warnings.filters == filters
    assert random.getstate() == python_random
    after = np.random.get_state()
    assert after[0] == numpy_random[0] and after[2:] == numpy_random[2:]
    np.testing.assert_array_equal(after[1], numpy_random[1])
    assert result.status == "numerical_incomplete" and result.stage == "poll"
    assert result.failure_code == "image_only_bead_calibration_range"
    assert len(result.objective_trace) == 3 and len(result.poll_attempts) == 2
    initial, negative, failed = result.objective_trace
    assert [s.stage for s in result.objective_trace] == ["initial", "poll", "poll"]
    assert [s.pupil_order for s in result.objective_trace] == [128, 128, 128]
    assert initial.outcome == negative.outcome == "scored"
    assert failed.outcome == "numerical_incomplete"
    assert initial.failure_code is negative.failure_code is None
    assert failed.candidate is failed.objective is None
    assert failed.failure_code == "image_only_bead_calibration_range"
    # Compare each computed score to independent finite-equation bounds;
    # ordering then uses those ACTUAL reported scores without a tolerance.
    maximum = Fraction(float(np.finfo(np.float64).max))
    divisor = 2 * 28 * math.prod(RANGE_SHAPE)
    for score, bounds in (
        (initial, (initial_lo, initial_hi)),
        (negative, (negative_lo, negative_hi)),
    ):
        ratio = Fraction(score.objective) * divisor / maximum
        assert bounds[0] <= ratio <= bounds[1]
    assert negative.objective < initial.objective
    assert result.best_score_index == 1 and result.incumbent_score_index == 0
    assert_same(result.initial_candidate, initial.candidate)
    assert_same(result.initial_coordinates, initial.coordinates)
    assert_same(result.best_candidate, negative.candidate)
    assert_same(result.best_coordinates, negative.coordinates)
    for b, (row, expected) in enumerate(
        zip(
            initial.candidate.centers_um_zyx,
            proof["centers"][0],
            strict=True,
        )
    ):
        assert all(
            abs(Fraction(float(a)) - Fraction(float(e))) <= proof["center_error"]
            for a, e in zip(row, expected, strict=True)
        )
        lo, hi = proof["brightness_intervals"][b]
        assert (
            lo <= Fraction(float(initial.candidate.brightness_relative[b])) / Fraction(1e146) <= hi
        )
    tail = proof["initial_tail"]
    np.testing.assert_array_equal(np.delete(initial.coordinates[9:], 3), np.delete(tail, 3))
    np.testing.assert_allclose(initial.coordinates[12], tail[3], rtol=32 * EPS, atol=0)
    for position, attempt in enumerate(result.poll_attempts):
        assert attempt.sweep_index == attempt.coordinate_index == attempt.base_score_index == 0
        assert attempt.sign == (-1, 1)[position]
        assert attempt.score_index == position + 1 and attempt.selected is None
        assert attempt.coordinate_changed is True and attempt.infeasibility_reason is None
        expected = initial.coordinates.copy()
        expected[0] += attempt.sign * float((D[0] / 8) * 0.5)
        np.testing.assert_array_equal(attempt.trial_coordinates, expected)
        assert_same(result.objective_trace[position + 1].coordinates, attempt.trial_coordinates)
    assert result.poll_attempts[0].outcome == "scored"
    assert result.poll_attempts[0].parameter_changed is True
    assert result.poll_attempts[0].failure_code is None
    assert result.poll_attempts[1].outcome == "numerical_incomplete"
    assert result.poll_attempts[1].parameter_changed is None
    assert result.poll_attempts[1].failure_code == "image_only_bead_calibration_range"
    assert result.poll_attempts[1].information_codes == ()
    for row, expected in zip(negative.candidate.centers_um_zyx, proof["centers"][1], strict=True):
        assert all(
            abs(Fraction(float(a)) - Fraction(float(e))) <= proof["trial_center_error"]
            for a, e in zip(row, expected, strict=True)
        )
    np.testing.assert_array_equal(
        negative.candidate.brightness_relative, initial.candidate.brightness_relative
    )
    expected_counts = (94, 2, 1, 0, 1, 0, 0, 3, 2)
    for name, count in zip(FIELDS["BeadCalibrationCounts"], expected_counts, strict=True):
        assert getattr(result.counts, name) == count
    assert result.unprobed_coordinates == tuple(range(1, 47))
    assert result.training_objectives_q128_q256_q512 == (negative.objective, None, None)
    assert result.initialization_notes is not None
    assert result.frozen_candidate is result.frozen_coordinates is None
    assert (
        result.heldout_prediction
        is result.heldout_residual_mean
        is result.heldout_residual_rms
        is None
    )
    assert_ledger(result, bead, pilot.PilotCandidate)
    assert_independent(result)
    arrays = output_arrays(result)
    copies = [a.copy() for a in arrays]
    for output in arrays:
        assert all(not np.shares_memory(output, caller) for caller in callers)
    # The independent best-state snapshot stays writable despite frozen
    # record bindings. Mutating it cannot alter initial/trace/caller arrays.
    result.best_coordinates[0] += 1
    for array, contents in zip(arrays, copies, strict=True):
        if array is not result.best_coordinates:
            np.testing.assert_array_equal(array, contents)
    for caller, (contents, dtype, strides, writable) in zip(callers, saved, strict=True):
        np.testing.assert_array_equal(caller, contents)
        assert caller.dtype == dtype and caller.strides == strides
        assert caller.flags.writeable == writable


def test_normalization_range_before_candidate_formation() -> None:
    values = arguments(
        camera_estimate=camera(means_counts=np.array([0.0, -1e308, 0.0]), contrast_counts=SMALLEST)
    )
    values["central_counts"] = np.full(SHAPE, 1e308)
    result = fit(**values)
    assert result.status == "numerical_incomplete" and result.stage == "normalization"
    assert result.failure_code == "image_only_bead_calibration_range"
    assert result.initialization_notes is None
    assert_ledger(result, bead, pilot.PilotCandidate)


def test_late_range_retains_complete_prediction_both_summaries_absent() -> None:
    y = np.zeros(SHAPE)
    for x, height in zip((0, 7, 14), (8, 6, 4), strict=True):
        y[0, 0, x] = height
    values = arguments(
        central_counts=SMALLEST * y,
        structured_counts=np.zeros((3, 9, *SHAPE)),
        heldout_counts=np.ones((3, 5, *SHAPE)),
        camera_estimate=camera(means_counts=np.zeros(3), contrast_counts=SMALLEST),
    )
    result = fit(**values)
    assert result.status == "numerical_incomplete" and result.stage == "heldout_residual"
    assert result.failure_code == "image_only_bead_calibration_range"
    assert result.frozen_candidate is not None and result.heldout_prediction is not None
    assert result.heldout_residual_mean is result.heldout_residual_rms is None
    assert all(v is not None for v in result.training_objectives_q128_q256_q512)
    # Contrast underflow is legal. Only the late required correction is
    # unrepresentable: 1 / 2**-1074 > maxfloat. Earlier fitting is independent.
    values["heldout_counts"] = np.zeros((3, 5, *SHAPE))
    successful = fit(**values)
    assert successful.status == "completed_finite_fit"
    for name in (
        "initial_candidate",
        "best_candidate",
        "frozen_candidate",
        "objective_trace",
        "poll_attempts",
        "coordinate_evidence",
        "counts",
        "heldout_prediction",
        "training_objectives_q128_q256_q512",
    ):
        assert_same(getattr(result, name), getattr(successful, name))
    assert_ledger(result, bead, pilot.PilotCandidate)


@pytest.mark.parametrize("outcome", ("success", "invalid", "unavailable", "range", "poll_range"))
def test_preservation_inputs_random_numpy_and_warning_policy(outcome: str) -> None:
    values = poll_range_arguments() if outcome == "poll_range" else arguments()
    if outcome == "invalid":
        values["heldout_counts"] = values["heldout_counts"].astype(bool)
    elif outcome == "unavailable":
        values["camera_estimate"] = camera(contrast_counts=0)
    elif outcome == "range":
        values["structured_counts"].fill(1e200)
    arrays = [values[name] for name in ARRAY_NAMES] + [values["camera_estimate"].means_counts]
    snapshots = [(a.copy(), a.strides, a.flags.writeable, a.dtype) for a in arrays]
    python_random, numpy_random = random.getstate(), np.random.get_state()
    with np.errstate(all="raise"), warnings.catch_warnings():
        warnings.simplefilter("error")
        policy, filters = np.geterr().copy(), list(warnings.filters)
        if outcome == "invalid":
            with pytest.raises(SimreconError) as error:
                fit(**values)
            assert error.value.code == "invalid_image_only_bead_calibration"
        else:
            result = fit(**values)
            assert (
                result.status
                == {
                    "success": "completed_finite_fit",
                    "unavailable": "normalization_unavailable",
                    "range": "numerical_incomplete",
                    "poll_range": "numerical_incomplete",
                }[outcome]
            )
            for output in output_arrays(result):
                assert all(not np.shares_memory(output, source) for source in arrays)
        assert np.geterr() == policy and warnings.filters == filters
    assert random.getstate() == python_random
    after = np.random.get_state()
    assert after[0] == numpy_random[0] and after[2:] == numpy_random[2:]
    np.testing.assert_array_equal(after[1], numpy_random[1])
    for array, (contents, strides, writable, dtype) in zip(arrays, snapshots, strict=True):
        np.testing.assert_array_equal(array, contents)
        assert (
            array.strides == strides and array.flags.writeable == writable and array.dtype == dtype
        )
