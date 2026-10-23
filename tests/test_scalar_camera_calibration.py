"""NS03-C blind A1 tests from scalar-camera-calibration-v1 only.

Behavior inventory (equivalent parameter values are coverage examples):
S01 finite frame/group moments, K-1, signed counts and empirical standard error;
S02 constants/zeros, all information decisions and returned-point arithmetic;
S03 accepted storage/conversion, unequal frame counts and minimum geometry;
S04 input/source/binding rejection, range versus invalid and caller preservation;
S05 exact result boundary, frozen bindings, independent mutable storage/purity;
S06 numerical envelope, frame/pixel permutations and positive affine count units;
S07 real declaration/correction composition even without physical gain.

Every assertion exercises a real public boundary. Rational observers and small
literal controls distinguish plausible wrong grouping/divisors independently.
No test-only production seam or simulator/RNG oracle is introduced. Allocation
and unrelated injected failures have no safe portable public trigger here.
"""

import warnings
from itertools import combinations
from typing import Any, Literal

import numpy as np
import pytest

from scalar_camera_calibration_fixture import (
    allowances,
    assert_decisions,
    assert_near_exact,
    assert_statistics,
    literal_se,
    small_groups,
)
from simrecon import (
    ScalarCameraEstimate,
    SimreconError,
    correct_linear_response,
    declare_acquisition,
    estimate_scalar_camera,
)

SOURCE = " primary camera: ensemble D/B/F; estimated "
INVALID = "invalid_scalar_camera_calibration"
RANGE = "scalar_camera_calibration_range"
ErrorMode = Literal["raise", "warn", "ignore", "call", "print", "log"]


def estimate(groups: tuple[Any, ...], *, source: Any = SOURCE) -> Any:
    saved = [
        (group, snapshot(group))
        for group in groups
        if type(group) is np.ndarray and group.dtype.kind in "iuf"
    ]
    try:
        return estimate_scalar_camera(
            groups[0], blank_counts=groups[1], flat_counts=groups[2], source=source
        )
    finally:
        for group, before in saved:
            assert_unchanged(group, before)


def arrays(result: Any) -> list[np.ndarray]:
    return [
        result.means_counts,
        result.variances_counts2,
        *result.frame_means_counts,
        *result.frame_variances_counts2,
        result.empirical_mean_se_counts,
    ]


def assert_unchanged(group: np.ndarray, saved: tuple[Any, ...]) -> None:
    values, strides, writable, dtype, raw_bytes = saved
    np.testing.assert_array_equal(group, values)
    assert group.strides == strides
    assert group.flags.writeable == writable
    assert group.dtype == dtype
    assert group.tobytes() == raw_bytes


def snapshot(group: np.ndarray) -> tuple[Any, ...]:
    return group.copy(), group.strides, group.flags.writeable, group.dtype, group.tobytes()


def test_small_literal_moments_distinguish_frame_pooling_and_divisors() -> None:
    groups = small_groups()
    result = estimate(groups)
    assert isinstance(result, ScalarCameraEstimate)
    # D means [-2,4], B means [3,5,7], F means [6,8].
    # Frame squared residual sums: 8,8,32; K-1=2, hence V=[4,4,16].
    # Group means [1,5,7]; contrasts dM=2, dV=12; gain=6 counts/e.
    mean_bound, variance_bound = allowances(groups)
    assert_near_exact(result.means_counts, [1, 5, 7], mean_bound)
    assert_near_exact(result.variances_counts2, [4, 4, 16], variance_bound)
    np.testing.assert_allclose(
        result.empirical_mean_se_counts, literal_se(), rtol=0, atol=float(4 * mean_bound)
    )
    assert result.information_codes == ()
    assert result.source == SOURCE
    assert_statistics(result, groups)
    assert_decisions(result)


@pytest.mark.parametrize(
    ("levels", "codes"),
    [
        ((0, 0, 0), ("nonpositive_flat_contrast", "nonpositive_variance_contrast")),
        ((-5, -2, 3), ("nonpositive_variance_contrast",)),
        (
            (3, 2, 1),
            (
                "nonpositive_flat_contrast",
                "nonpositive_variance_contrast",
                "negative_background_estimate",
            ),
        ),
        ((3, 2, 4), ("nonpositive_variance_contrast", "negative_background_estimate")),
    ],
)
def test_constant_signed_zero_data_are_information_not_errors(
    levels: tuple[int, ...], codes: tuple[str, ...]
) -> None:
    groups = tuple(np.full((2, 1, 2), level, dtype=np.float64) for level in levels)
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_near_exact(result.means_counts, levels, allowances(groups)[0])
    for value in [result.variances_counts2, *result.frame_variances_counts2]:
        assert np.all(value == 0)
    assert result.information_codes == codes
    assert result.gain_counts_per_e is None
    assert_decisions(result)
    if levels == (0, 0, 0):
        for output in arrays(result):
            assert np.all(output == 0)


@pytest.mark.parametrize("flat_mean", [-3.0, 0.0, 3.0])
@pytest.mark.parametrize("flat_spread", [0.5, 1.0, 2.0])
def test_mean_and_variance_contrast_signs_are_independent(
    flat_mean: float, flat_spread: float
) -> None:
    # Blank mean 0 and variance 2. Flat variance 2*spread**2.
    dark = np.full((2, 1, 2), 1.0)
    blank = np.tile([-1.0, 1.0], (2, 1, 1))
    flat = np.tile([flat_mean - flat_spread, flat_mean + flat_spread], (2, 1, 1))
    groups = dark, blank, flat
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)
    if flat_mean != 0 and flat_spread != 1:
        assert (result.gain_counts_per_e is not None) == (flat_mean > 0 and flat_spread > 1)
    assert result.information_codes[-1] == "negative_background_estimate"


@pytest.mark.parametrize("scale", [1.0, 2.0**-520, 2.0**20])
def test_no_stationarity_screening_trimming_masking_or_frame_normalization(
    scale: float,
) -> None:
    # Deliberate frame drift and an isolated bright pixel remain finite data.
    groups = (
        np.array([[[0, 0, 0], [0, 0, 0]], [[100, 100, 100], [100, 100, 100]]]) * scale,
        np.array([[[1, 1, 1], [1, 1, 1]], [[3, 3, 3], [3, 3, 3]]]) * scale,
        np.array([[[1, 1, 1], [1, 1, 101]], [[5, 5, 5], [5, 5, 5]]]) * scale,
    )
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)
    assert result.frame_variances_counts2[0][0] == 0
    assert result.frame_variances_counts2[0][1] == 0


@pytest.mark.parametrize(
    "dtype",
    ["i1", "i2", "i4", "i8", "u1", "u2", "u4", "u8", "f2", "f4", "f8", ">i4", ">f8", np.longdouble],
)
def test_numeric_widths_endianness_and_conversion(dtype: Any) -> None:
    base = np.array([[[0, 2, 4]], [[6, 8, 10]]])
    groups = tuple((base + shift).astype(dtype) for shift in (0, 2, 6))
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)


@pytest.mark.parametrize("layout", ["strided", "fortran", "readonly", "reversed"])
def test_supported_layouts_preserve_values_flags_and_strides(layout: str) -> None:
    groups = []
    for base in small_groups():
        if layout == "strided":
            backing = np.empty((base.shape[0], 2, 6))
            group = backing[:, ::2, ::2]
            group[:] = base
        elif layout == "fortran":
            group = np.asfortranarray(base)
        elif layout == "reversed":
            group = base[:, :, ::-1]
        else:
            group = base.copy()
            group.flags.writeable = False
        groups.append(group)
    saved = [snapshot(group) for group in groups]
    result = estimate(tuple(groups))
    assert_statistics(result, tuple(groups))
    for group, before in zip(groups, saved, strict=True):
        assert_unchanged(group, before)


@pytest.mark.parametrize("shape", [(2, 1, 2), (3, 2, 1), (2, 2, 3)])
def test_minimum_and_nonsquare_geometry_with_unequal_frame_counts(
    shape: tuple[int, int, int],
) -> None:
    groups = tuple(
        np.arange((shape[0] + index) * shape[1] * shape[2], dtype=np.float64).reshape(
            shape[0] + index, shape[1], shape[2]
        )
        for index in range(3)
    )
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)


@pytest.mark.parametrize(
    "kind", ["rounded_uint64", "wide_fraction", "finite_underflow", "signed_zero"]
)
def test_conversion_defines_statistics_including_rounding_and_underflow(kind: str) -> None:
    if kind == "rounded_uint64":
        # 2**53+1 normalizes to 2**53; an exact original-integer oracle is wrong.
        base = np.array([[[2**53, 2**53 + 1]], [[2**53 + 4, 2**53 + 5]]], dtype=np.uint64)
    elif kind == "wide_fraction":
        base = np.array([[[1, 2]], [[3, 4]]], dtype=np.longdouble)
        base += np.longdouble(2) ** -60
    elif kind == "finite_underflow":
        # On binary64-longdouble platforms this is already zero; still valid.
        with np.errstate(all="ignore"):
            tiny = np.longdouble(2) ** -1075
        base = np.full((2, 1, 2), tiny, dtype=np.longdouble)
    else:
        base = np.array([[[-0.0, 0.0]], [[0.0, -0.0]]])
    groups = base, base.copy(), base.copy()
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)
    if kind == "rounded_uint64":
        # Both pixels in each normalized frame coincide exactly.
        for values in result.frame_variances_counts2:
            assert np.all(values == 0)


@pytest.mark.parametrize("source", ["camera", " \t camera \n", " 0 "])
def test_source_is_an_unchanged_opaque_nonblank_label(source: str) -> None:
    assert estimate(small_groups(), source=source).source == source


@pytest.mark.parametrize("source", [None, "", " ", "\t\n", 1, True, b"camera", ["camera"]])
def test_invalid_source_domain(source: Any) -> None:
    groups = small_groups()
    saved = [snapshot(group) for group in groups]
    with pytest.raises(SimreconError) as caught:
        estimate(groups, source=source)
    assert caught.value.code == INVALID
    for group, before in zip(groups, saved, strict=True):
        assert_unchanged(group, before)


class ArraySubclass(np.ndarray):
    """A non-plain ndarray rejected at the public input boundary."""


def invalid_groups() -> list[Any]:
    legal = np.ones((2, 1, 2))
    return [
        None,
        1.0,
        legal.tolist(),
        np.array(1),
        np.ones((2, 2)),
        np.ones((2, 1, 1, 2)),
        np.ones((1, 1, 2)),
        np.ones((0, 1, 2)),
        np.ones((2, 0, 2)),
        np.ones((2, 1, 0)),
        np.ones((2, 1, 1)),
        legal.view(ArraySubclass),
        np.ma.array(legal),
        legal.astype(bool),
        legal.astype(complex),
        legal.astype(object),
        legal.astype("U2"),
        legal.astype("S2"),
        np.zeros((2, 1, 2), dtype="V8"),
        np.zeros((2, 1, 2), dtype=[("counts", "f8")]),
        np.zeros((2, 1, 2), dtype="datetime64[D]"),
        np.zeros((2, 1, 2), dtype="timedelta64[D]"),
    ]


@pytest.mark.parametrize("bad", invalid_groups())
@pytest.mark.parametrize("index", [0, 1, 2])
def test_array_type_dtype_rank_frame_and_pixel_rejections(bad: Any, index: int) -> None:
    groups = list(small_groups())
    groups[index] = bad
    with pytest.raises(SimreconError) as caught:
        estimate(tuple(groups))
    assert caught.value.code == INVALID


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("shape", [(2, 2, 3), (2, 3, 1), (2, 1, 2)])
def test_detector_dimensions_must_match_not_just_total_pixel_count(
    index: int, shape: tuple[int, ...]
) -> None:
    groups = list(small_groups())
    groups[index] = np.ones(shape)
    with pytest.raises(SimreconError) as caught:
        estimate(tuple(groups))
    assert caught.value.code == INVALID


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("index", [0, 1, 2])
def test_original_nonfinite_samples_are_invalid_and_inputs_preserved(
    value: float, index: int
) -> None:
    groups = small_groups()
    groups[index][0, 0, 0] = value
    saved = [snapshot(group) for group in groups]
    with pytest.raises(SimreconError) as caught:
        estimate(groups)
    assert caught.value.code == INVALID
    for group, before in zip(groups, saved, strict=True):
        assert_unchanged(group, before)


def test_wider_finite_sample_outside_binary64_is_invalid_where_representable() -> None:
    # No skip/platform union: extended range is conditional on actual dtype support.
    wider = np.longdouble(np.finfo(np.longdouble).max)
    if wider > np.longdouble(np.finfo(np.float64).max):
        groups = tuple(np.full((2, 1, 2), wider, dtype=np.longdouble) for _ in range(3))
        with pytest.raises(SimreconError) as caught:
            estimate(groups)
        assert caught.value.code == INVALID
    else:
        # A platform with no wider exponent still tests its widest valid storage.
        groups = tuple(np.full((2, 1, 2), 32, dtype=np.longdouble) for _ in range(3))
        assert_statistics(estimate(groups), groups)


@pytest.mark.parametrize("case", ["variance", "mean_contrast", "background_difference"])
@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log"])
def test_required_nonfinite_stages_are_range_not_invalid_and_preserve_modes(
    case: str, mode: ErrorMode
) -> None:
    maximum = float(np.finfo(np.float64).max)
    if case == "variance":
        groups = tuple(np.tile([-1e200, 1e200], (2, 1, 1)) for _ in range(3))
    elif case == "mean_contrast":
        groups = tuple(np.full((2, 1, 2), v) for v in (0.0, -maximum, maximum))
    else:
        groups = tuple(np.full((2, 1, 2), v) for v in (-maximum, maximum, maximum))
    saved = [snapshot(group) for group in groups]
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with np.errstate(all=mode):
            before = np.geterr().copy()
            callback = np.geterrcall()
            with pytest.raises(SimreconError) as caught:
                estimate(groups)
            assert caught.value.code == RANGE
            assert np.geterr() == before
            assert np.geterrcall() is callback
    assert not [w for w in caught_warnings if issubclass(w.category, RuntimeWarning)]
    for group, before_group in zip(groups, saved, strict=True):
        assert_unchanged(group, before_group)


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log"])
def test_success_underflow_and_invalid_input_preserve_error_and_warning_policy(
    mode: ErrorMode,
) -> None:
    groups = tuple(np.full((2, 1, 2), -0.0) for _ in range(3))
    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with np.errstate(all=mode):
            before = np.geterr().copy()
            callback = np.geterrcall()
            filters = list(warnings.filters)
            result = estimate(groups)
            assert_statistics(result, groups)
            small = tuple(np.tile([-(2.0**-540), 2.0**-540], (2, 1, 1)) for _ in range(3))
            assert_statistics(estimate(small), small)
            bad = list(groups)
            bad[1] = np.full((2, 1, 2), np.inf)
            with pytest.raises(SimreconError) as caught:
                estimate(tuple(bad))
            assert caught.value.code == INVALID
            assert np.geterr() == before
            assert np.geterrcall() is callback
            assert warnings.filters == filters
            warnings.warn("unrelated warning remains visible", UserWarning, stacklevel=1)
    assert [w.category for w in caught_warnings] == [UserWarning]


def test_return_schema_shapes_frozen_bindings_writable_arrays_and_independent_storage() -> None:
    groups = small_groups()
    saved = [snapshot(group) for group in groups]
    result = estimate(groups)
    repeated = estimate(groups)
    assert isinstance(result, ScalarCameraEstimate)
    assert result.source == SOURCE
    assert len(result.frame_means_counts) == len(result.frame_variances_counts2) == 3
    expected_shapes = [(3,), (3,), (2,), (3,), (2,), (2,), (3,), (2,), (3,)]
    outputs = arrays(result)
    for output, shape in zip(outputs, expected_shapes, strict=True):
        assert type(output) is np.ndarray
        assert output.dtype == np.dtype(np.float64)
        assert output.dtype.isnative
        assert output.shape == shape
        assert output.flags.c_contiguous and output.flags.writeable
    for left, right in combinations(outputs + arrays(repeated) + list(groups), 2):
        assert not np.shares_memory(left, right)
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
    ):
        with pytest.raises(AttributeError):
            setattr(result, name, getattr(result, name))
    for first, second in zip(outputs, arrays(repeated), strict=True):
        np.testing.assert_array_equal(first, second)
    for output in outputs:
        output[:] = 12345
    assert_statistics(repeated, groups)
    for group, before in zip(groups, saved, strict=True):
        assert_unchanged(group, before)
    groups[0][:] = -777
    assert_near_exact(repeated.means_counts, [1, 5, 7], allowances(small_groups())[0])


def test_aliasing_between_input_groups_does_not_alias_any_output() -> None:
    base = np.arange(18, dtype=np.float64).reshape(3, 2, 3)
    groups = base, base[::-1], base[:, :, ::-1]
    result = estimate(groups)
    assert_statistics(result, groups)
    for output in arrays(result):
        assert not np.shares_memory(output, base)


def test_pure_statistic_does_not_consume_or_reseed_global_random_state() -> None:
    before = np.random.get_state()
    estimate(small_groups())
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


@pytest.mark.parametrize("scale,shift", [(2.0, -17.0), (0.25, 100.0), (1024.0, 0.0)])
def test_positive_affine_count_relabeling(scale: float, shift: float) -> None:
    groups = small_groups()
    original = estimate(groups)
    changed_groups = tuple(scale * group + shift for group in groups)
    changed = estimate(changed_groups)
    assert_statistics(changed, changed_groups)
    assert_decisions(changed)
    # Each side has an independent exact-moment proof above/below. Compare
    # the relation with both error budgets, allowing backend reduction choices.
    assert_statistics(original, groups)
    old_mean_bound, old_variance_bound = allowances(groups)
    new_mean_bound, new_variance_bound = allowances(changed_groups)
    mean_budget = float(new_mean_bound + scale * old_mean_bound)
    variance_budget = float(new_variance_bound + scale**2 * old_variance_bound)
    np.testing.assert_allclose(
        changed.means_counts, scale * original.means_counts + shift, rtol=0, atol=2 * mean_budget
    )
    np.testing.assert_allclose(
        changed.variances_counts2,
        scale**2 * original.variances_counts2,
        rtol=0,
        atol=2 * variance_budget,
    )
    assert abs(changed.contrast_counts - scale * original.contrast_counts) <= 4 * mean_budget
    assert changed.information_codes == original.information_codes
    raw = np.array([-3.0, 5.0, 7.0, 13.0])
    y = (raw - original.means_counts[1]) / original.contrast_counts
    transformed_y = (scale * raw + shift - changed.means_counts[1]) / changed.contrast_counts
    np.testing.assert_allclose(transformed_y, y, rtol=0, atol=64 * mean_budget / scale)


def test_frame_and_pixel_permutations_reorder_diagnostics_only() -> None:
    groups = small_groups()
    original = estimate(groups)
    changed_groups = tuple(group[::-1, :, [2, 0, 1]] for group in groups)
    changed = estimate(changed_groups)
    assert_statistics(changed, changed_groups)
    mean_bound, variance_bound = allowances(groups)
    np.testing.assert_allclose(
        changed.means_counts, original.means_counts, rtol=0, atol=float(2 * mean_bound)
    )
    np.testing.assert_allclose(
        changed.variances_counts2,
        original.variances_counts2,
        rtol=0,
        atol=float(2 * variance_bound),
    )
    # Permuted diagnostics are each checked against exact rational targets by
    # assert_statistics; empirical SE uses each call's own returned points.
    for index in range(3):
        np.testing.assert_allclose(
            changed.frame_means_counts[index],
            original.frame_means_counts[index][::-1],
            rtol=0,
            atol=float(2 * mean_bound),
        )
        np.testing.assert_allclose(
            changed.frame_variances_counts2[index],
            original.frame_variances_counts2[index][::-1],
            rtol=0,
            atol=float(2 * variance_bound),
        )
    assert_decisions(changed)


@pytest.mark.parametrize("scale", [2.0**-400, 1.0, 2.0**30])
def test_exact_observer_bounds_non_dyadic_means_and_cancellation(scale: float) -> None:
    base = np.array(
        [[[1, -1, 2, -2, 3]], [[7, 11, -13, 17, -19]], [[2, 3, 5, 7, 11]]], dtype=np.float64
    )
    groups = tuple((base * scale + shift * scale) for shift in (0, 3, 10))
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)


@pytest.mark.parametrize("case", ["overflow_candidate", "underflow_candidate"])
def test_optional_gain_quotient_uses_returned_points_without_range_failure(case: str) -> None:
    # Extreme finite targets offer an optional quotient-over/underflow opportunity.
    # The numerical allowance does not force tiny returned contrast signs; retain
    # legitimate unavailable alternatives instead of requiring a reduction order.
    if case == "overflow_candidate":
        tiny = 2.0**-1018
        flat = np.tile([-32.0, 32.0, tiny, tiny], (2, 1, 1))
        zero = np.zeros((2, 1, 4))
    else:
        flat = np.array([[[2.0**500, 2.0**500]], [[-(2.0**-530), 2.0**-530]]])
        zero = np.zeros((2, 1, 2))
    groups = zero, zero.copy(), flat
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)


@pytest.mark.parametrize("variance_mode", ["positive", "zero", "negative"])
def test_real_relative_correction_uses_blank_not_dark_with_unavailable_gain(
    variance_mode: str,
) -> None:
    dark = np.full((2, 1, 2), -4.0)
    blank = np.tile([2.0, 6.0], (2, 1, 1))  # mean 4, variance 8
    spreads = {"positive": 4.0, "zero": 2.0, "negative": 1.0}
    spread = spreads[variance_mode]
    flat = np.tile([12.0 - spread, 12.0 + spread], (2, 1, 1))
    groups = dark, blank, flat
    result = estimate(groups)
    assert_statistics(result, groups)
    assert_decisions(result)
    if variance_mode != "zero":
        assert (result.gain_counts_per_e is not None) == (variance_mode == "positive")
    raw = np.array([[-4.0, 4.0, 12.0], [20.0, 0.0, 8.0]])
    acquisition = declare_acquisition(
        raw,
        config={
            "version": 1,
            "acquisition_kind": "detection_psf",
            "axes": ["y", "x"],
            "intensity_unit": "counts",
        },
    )
    corrected = correct_linear_response(
        acquisition,
        offset=float(result.means_counts[1]),
        response=result.contrast_counts,
        output_unit="reference_flat_relative",
    )
    mean_bound = float(allowances(groups)[0])
    correction_bound = 8 * mean_bound / (8 - 4 * mean_bound) + 128 * np.finfo(float).eps
    np.testing.assert_allclose(
        corrected.data, [[-1, 0, 1], [2, -0.5, 0.5]], rtol=0, atol=correction_bound
    )
    assert corrected.input_unit == "counts"
    assert corrected.output_unit == "reference_flat_relative"
    assert corrected.provenance["offset"]["source"] == "supplied"
    assert corrected.provenance["offset"]["applied"] == float(result.means_counts[1])
    assert corrected.provenance["response"]["applied"] == result.contrast_counts
    np.testing.assert_array_equal(acquisition.data, raw)
    # Corrected pixels remain variable: subtracting a mean does not remove noise.
    normalized_blank = (blank - result.means_counts[1]) / result.contrast_counts
    np.testing.assert_allclose(normalized_blank[0], [[-0.25, 0.25]], rtol=0, atol=correction_bound)


@pytest.mark.parametrize(
    "case",
    ["missing_blank", "missing_flat", "missing_source", "positional_keyword", "truth_gain", "seed"],
)
def test_python_binding_rejects_missing_keywords_positional_keywords_and_truth(case: str) -> None:
    dark, blank, flat = small_groups()
    kwargs: dict[str, Any] = {"blank_counts": blank, "flat_counts": flat, "source": SOURCE}
    with pytest.raises(TypeError):
        if case.startswith("missing_"):
            del kwargs[
                {
                    "missing_blank": "blank_counts",
                    "missing_flat": "flat_counts",
                    "missing_source": "source",
                }[case]
            ]
            estimate_scalar_camera(dark, **kwargs)
        elif case == "positional_keyword":
            callable_api: Any = estimate_scalar_camera
            callable_api(dark, blank, flat, SOURCE)
        else:
            kwargs[{"truth_gain": "gain_counts_per_e", "seed": "seed"}[case]] = 1
            estimate_scalar_camera(dark, **kwargs)
