"""Blind public-boundary proof for VOLUME-REFERENCE-TRANSLATION V01–V19.

V20's executed scientific observations and usage custody belong to C/D.
The independent oracle is in volume_translation_estimation_fixture.py.
"""

import warnings
from itertools import product
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import simrecon
from simrecon import SimreconError, TranslationEstimate, estimate_translation
from volume_translation_estimation_fixture import (
    asymmetric_volume,
    canonical_grid,
    score_allowance,
    stored_surface,
)

# Resolve the declared public names at runtime so preparation can type-check
# before the additive API exists. Missing exports still fail public collection.
VolumeTranslationEstimate, estimate_volume_translation = (
    getattr(simrecon, name) for name in ("VolumeTranslationEstimate", "estimate_volume_translation")
)


def assert_surface(moving: NDArray, reference: NDArray, tolerance: Any = 0.0):
    """Check independent accuracy and the separate same-call decision rule."""
    original = moving.tobytes(), reference.tobytes()
    result = estimate_volume_translation(moving, reference=reference, ambiguity_tolerance=tolerance)
    assert (moving.tobytes(), reference.tobytes()) == original
    expected = stored_surface(moving, reference)
    np.testing.assert_allclose(
        result.normalized_rms,
        expected,
        rtol=0,
        atol=score_allowance(moving.size),
    )
    assert_result(result, moving.shape, float(tolerance))
    return result


def assert_result(result, shape: tuple[int, ...], tolerance: float):
    """Observe selection only; this helper supplies no numerical truth."""
    assert type(result) is VolumeTranslationEstimate
    scores = result.normalized_rms
    assert type(scores) is np.ndarray
    assert scores.shape == shape
    assert scores.dtype == np.dtype(np.float64)
    assert scores.dtype.isnative
    assert scores.flags.c_contiguous
    assert scores.flags.writeable
    assert np.isfinite(scores).all()
    assert type(result.minimum_normalized_rms) is float
    assert result.minimum_normalized_rms == float(np.min(scores))
    expected = tuple(
        displacement
        for displacement, score in zip(canonical_grid(shape), scores.flat, strict=True)
        if float(score) - result.minimum_normalized_rms <= tolerance
    )
    candidates = result.candidate_displacements_voxels_zyx
    assert type(candidates) is tuple
    assert candidates == expected
    assert candidates
    for displacement in candidates:
        assert type(displacement) is tuple
        assert len(displacement) == 3
        assert all(type(value) is int for value in displacement)
    if len(expected) == 1:
        assert type(result.displacement_voxels_zyx) is tuple
        assert all(type(value) is int for value in result.displacement_voxels_zyx)
        assert result.displacement_voxels_zyx == expected[0]
        assert result.failure_code is None
    else:
        assert result.displacement_voxels_zyx is None
        assert type(result.failure_code) is str
        assert result.failure_code == "ambiguous_volume_translation"


def assert_error(code: str, moving, reference, tolerance: Any = 0.0):
    """Require the public error code, without constraining prose/precedence."""
    with pytest.raises(SimreconError) as caught:
        estimate_volume_translation(moving, reference=reference, ambiguity_tolerance=tolerance)
    assert caught.value.code == code


def test_public_binding_requires_only_moving_positional_and_both_keywords():
    volume = np.ones((1, 2, 3))
    with pytest.raises(TypeError):
        estimate_volume_translation(volume)
    with pytest.raises(TypeError):
        estimate_volume_translation(volume, reference=volume)
    with pytest.raises(TypeError):
        estimate_volume_translation(volume, ambiguity_tolerance=0.0)
    with pytest.raises(TypeError):
        estimate_volume_translation(reference=volume, ambiguity_tolerance=0.0)
    with pytest.raises(TypeError):
        estimate_volume_translation(volume, volume, 0.0)
    with pytest.raises(TypeError):
        estimate_volume_translation(volume, volume, ambiguity_tolerance=0.0)
    result = estimate_volume_translation(volume, reference=volume, ambiguity_tolerance=0.0)
    assert_result(result, volume.shape, 0.0)


def test_exact_frozen_fields_direct_construction_and_mutable_score_storage():
    names = (
        "normalized_rms",
        "minimum_normalized_rms",
        "candidate_displacements_voxels_zyx",
        "displacement_voxels_zyx",
        "failure_code",
    )
    result = assert_surface(np.array([[[3.0]]]), np.array([[[-2.0]]]))
    public_values = {
        name
        for name in dir(result)
        if not name.startswith("_") and not callable(getattr(result, name))
    }
    assert public_values == set(names)
    for name in names:
        with pytest.raises((AttributeError, TypeError)):
            setattr(result, name, getattr(result, name))
    result.normalized_rms[0, 0, 0] = 123.0
    assert result.normalized_rms[0, 0, 0] == 123.0
    # Construction itself has no estimator validation obligation.
    constructed = VolumeTranslationEstimate(
        normalized_rms=np.array([[[np.nan]]]),
        minimum_normalized_rms=-1.0,
        candidate_displacements_voxels_zyx=(),
        displacement_voxels_zyx=None,
        failure_code="caller-value",
    )
    assert constructed.minimum_normalized_rms == -1.0


@pytest.mark.parametrize(
    "dtype",
    [
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        np.longdouble,
        ">i4",
        "<i4",
        ">u8",
        "<u8",
        ">f8",
        "<f8",
        ">f4",
        ">f2",
        np.dtype(np.longdouble).newbyteorder(">"),
    ],
)
def test_real_dtype_and_endian_examples(dtype):
    reference = np.array([[[1, 4, 2], [7, 3, 6]], [[2, 9, 5], [8, 1, 3]]], dtype=dtype)
    moving = np.roll(reference, (1, -1, 1), axis=(0, 1, 2))
    assert_surface(moving, reference)


@pytest.mark.parametrize("layout", ["fortran", "strided", "reversed", "readonly"])
def test_layout_signed_and_mixed_dtype_examples(layout):
    reference = asymmetric_volume((2, 3, 4)) - 50
    moving = np.roll(reference, (1, 1, -1), axis=(0, 1, 2)).astype(np.float32)
    if layout == "fortran":
        reference, moving = np.asfortranarray(reference), np.asfortranarray(moving)
    elif layout == "strided":
        rbase, mbase = np.zeros((4, 6, 8)), np.zeros((4, 6, 8), dtype=np.float32)
        rbase[::2, ::2, ::2], mbase[::2, ::2, ::2] = reference, moving
        reference, moving = rbase[::2, ::2, ::2], mbase[::2, ::2, ::2]
    elif layout == "reversed":
        reference, moving = reference[::-1, :, ::-1], moving[::-1, :, ::-1]
    else:
        reference.flags.writeable = False
        moving.flags.writeable = False
    assert_surface(moving, reference)


class ArraySubclass(np.ndarray):
    """A real ndarray subclass, explicitly outside the contract."""


@pytest.mark.parametrize(
    "invalid",
    [
        None,
        3,
        np.float64(1.0),
        [[[1.0]]],
        (1, 2),
        np.ones((1, 2, 3), dtype=bool),
        np.ones((1, 2, 3), dtype=complex),
        np.ones((1, 2, 3), dtype=object),
        np.full((1, 2, 3), "a"),
        np.full((1, 2, 3), b"a"),
        np.zeros((1, 2, 3), dtype=[("value", "f8")]),
        np.zeros((1, 2, 3), dtype="datetime64[D]"),
        np.zeros((1, 2, 3), dtype="timedelta64[D]"),
        np.ones((1, 2, 3)).view(ArraySubclass),
        np.ma.array(np.ones((1, 2, 3))),
        np.array(1.0),
        np.ones(3),
        np.ones((2, 3)),
        np.ones((1, 1, 2, 3)),
        np.empty((0, 2, 3)),
        np.empty((2, 0, 3)),
        np.empty((2, 3, 0)),
    ],
)
@pytest.mark.parametrize("side", ["moving", "reference"])
def test_invalid_image_grammar(invalid, side):
    valid = np.ones((1, 2, 3))
    pair = (invalid, valid) if side == "moving" else (valid, invalid)
    assert_error("invalid_volume_translation_images", *pair)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("side", ["moving", "reference"])
def test_nonfinite_source_images_rejected_without_mutation(value, side):
    invalid, valid = np.ones((2, 2, 3)), np.ones((2, 2, 3))
    invalid[1, 1, 2] = value
    before = invalid.tobytes(), valid.tobytes()
    pair = (invalid, valid) if side == "moving" else (valid, invalid)
    assert_error("invalid_volume_translation_images", *pair)
    assert (invalid.tobytes(), valid.tobytes()) == before


def test_unequal_otherwise_valid_shapes_have_distinct_error():
    assert_error("incompatible_volume_translation_shape", np.ones((2, 3, 4)), np.ones((3, 2, 4)))


@pytest.mark.parametrize("shape", [(1, 1, 1), (1, 3, 4), (3, 1, 2), (2, 3, 1), (3, 3, 3)])
def test_singleton_odd_and_even_axes_are_valid(shape):
    reference = asymmetric_volume(shape)
    assert_surface(np.roll(reference, 1, axis=0), reference)


@pytest.mark.parametrize(
    "tolerance",
    [
        0,
        -0.0,
        0.001,
        2,
        5.0,
        np.int64(0),
        np.uint64(2),
        np.float16(0.5),
        np.float32(0.25),
        np.float64(0.1),
        np.longdouble(0.125),
        np.array(0),
        np.array(-0.0),
        np.array(0.25, dtype=">f8"),
        np.array(2, dtype=">u8"),
        np.nextafter(0.0, 1.0),
    ],
)
def test_permitted_tolerance_grammar_and_ranges(tolerance):
    reference = asymmetric_volume((2, 2, 3))
    assert_surface(reference, reference, tolerance)


@pytest.mark.parametrize(
    "tolerance",
    [
        True,
        np.bool_(False),
        1j,
        None,
        "0",
        [0],
        (0,),
        {},
        np.array([0.0]),
        np.ones((1, 1)),
        np.array(True),
        np.array(0j),
        np.array(0, dtype=object),
        np.array("0"),
        np.array(b"0"),
        np.array(0.0).view(ArraySubclass),
        np.ma.array(np.array(0.0)),
        np.array(0, dtype="datetime64[D]"),
        np.array(0, dtype="timedelta64[D]"),
        -1,
        -0.001,
        np.int64(-1),
        np.array(-0.25),
        np.nan,
        np.inf,
        -np.inf,
        np.array(np.nan),
        np.array(np.inf),
        10**1000,
    ],
)
def test_invalid_tolerance_grammar_and_ranges(tolerance):
    # Finite extremes would overflow an unscaled numerical evaluation. A bad
    # tolerance must still reach validation, even with strict caller modes.
    reference = np.full((1, 2, 3), np.finfo(np.float64).max)
    with np.errstate(all="raise"):
        before = np.geterr()
        assert_error("invalid_volume_translation_tolerance", -reference, reference, tolerance)
        assert np.geterr() == before


def test_extended_range_inputs_and_tolerances_without_platform_skips():
    info = np.finfo(np.longdouble)
    double = np.finfo(np.float64)
    reference = np.array([[[1.0, 2.0, 4.0]]])
    # On platforms with binary64 longdouble, the wider-only cases are absent,
    # rather than fabricated or skipped. Ordinary longdouble remains tested.
    if info.max > np.longdouble(double.max):
        overflow = np.longdouble(double.max) * np.longdouble(2)
        for side in (0, 1):
            pair = [reference, reference]
            pair[side] = np.full(reference.shape, overflow, dtype=np.longdouble)
            with warnings.catch_warnings():
                warnings.simplefilter("error", RuntimeWarning)
                assert_error("invalid_volume_translation_images", *pair)
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            assert_error("invalid_volume_translation_tolerance", reference, reference, overflow)
            assert_error(
                "invalid_volume_translation_tolerance", reference, reference, np.array(overflow)
            )
    tiny = np.longdouble(double.smallest_subnormal) / np.longdouble(4)
    if tiny > 0:
        assert float(tiny) == 0.0
        with np.errstate(all="raise"):
            assert_surface(np.full(reference.shape, tiny), np.zeros(reference.shape))
            assert_surface(reference, reference, tiny)
            assert_surface(reference, reference, np.array(tiny))
            for negative in (-tiny, np.array(-tiny)):
                assert_error("invalid_volume_translation_tolerance", reference, reference, negative)
    rounded = np.array([[[2**53 + 1, 2**53 + 7, 2**53 + 13]]], dtype=np.uint64)
    assert_surface(np.roll(rounded, 1, axis=2), rounded)


def test_independent_full_surface_off_model_common_scale_all_voxels():
    reference = np.array([[[1, -2, 3], [4, 0, -5]], [[6, 3, -1], [2, 9, -4]]], dtype=float)
    moving = np.array([[[8, 1, -7], [2, 3, 6]], [[-3, 4, 1], [5, -2, 11]]], dtype=float)
    assert_surface(moving, reference)
    assert_surface(2 * moving + 7, reference)
    assert_surface(np.roll(reference, (1, -1, 1), axis=(0, 1, 2)) * 3 + 2, reference)


@pytest.mark.parametrize("shift", [(1, -1, 2), (-1, 1, -2), (0, -2, 0), (1, 0, 0)])
def test_content_displacement_sign_axis_order_half_period_and_alignment(shift):
    reference = asymmetric_volume()
    moving = np.roll(reference, shift, axis=(0, 1, 2))
    result = assert_surface(moving, reference)
    canonical = tuple(
        (s + n // 2) % n - n // 2 for s, n in zip(shift, reference.shape, strict=True)
    )
    assert result.displacement_voxels_zyx == canonical
    np.testing.assert_array_equal(
        np.roll(moving, tuple(-d for d in canonical), axis=(0, 1, 2)), reference
    )
    truth = stored_surface(moving, reference).ravel()
    ordered = np.sort(truth)
    assert ordered[1] - ordered[0] > 100 * score_allowance(reference.size)


def test_even_half_period_on_every_axis_and_ordered_complete_grid():
    reference = asymmetric_volume((2, 4, 6))
    moving = np.roll(reference, (1, 2, 3), axis=(0, 1, 2))
    assert assert_surface(moving, reference).displacement_voxels_zyx == (-1, -2, -3)
    result = assert_surface(moving, reference, 2.0)
    expected = tuple(product(range(-1, 1), range(-2, 2), range(-3, 3)))
    assert result.candidate_displacements_voxels_zyx == expected


def test_inclusive_same_call_boundary_and_next_float_neighbors():
    reference = asymmetric_volume((2, 3, 4))
    moving = np.roll(reference, (1, -1, 1), axis=(0, 1, 2))
    seed = assert_surface(moving, reference)
    gaps = seed.normalized_rms - seed.minimum_normalized_rms
    boundary = float(np.sort(gaps.ravel())[1])
    assert boundary > 100 * score_allowance(reference.size)
    # Scores may vary within allowance on another call. Only an actual
    # same-call equality asserts inclusion; every call checks the exact rule.
    for tolerance in (np.nextafter(boundary, 0), boundary, np.nextafter(boundary, np.inf)):
        result = assert_surface(moving, reference, tolerance)
        actual_gaps = result.normalized_rms - result.minimum_normalized_rms
        qualifying = actual_gaps <= tolerance
        assert len(result.candidate_displacements_voxels_zyx) == int(qualifying.sum())
    # The analytic wrong-shift score is 1. Classification still uses the
    # returned score; an accelerated method can differ within its allowance.
    reference = np.array([[[0.0, 1.0]]])
    for tolerance in (0.0, np.nextafter(1.0, 0), 1.0, np.nextafter(1.0, np.inf)):
        assert_surface(reference, reference, tolerance)


@pytest.mark.parametrize("constants", [(0.0, 0.0), (4.0, 4.0), (3.0, -2.0)])
def test_constant_volumes_do_not_prefer_a_tie_or_reject_information(constants):
    moving, reference = (np.full((2, 3, 4), v) for v in constants)
    # Only B=0 promises exact zeros. For other mathematical ties, allow
    # twice the per-score numerical error before requiring every candidate.
    tolerance = 0.0 if constants == (0.0, 0.0) else 4 * score_allowance(moving.size)
    result = assert_surface(moving, reference, tolerance)
    assert result.candidate_displacements_voxels_zyx == canonical_grid(moving.shape)
    if constants == (0.0, 0.0):
        np.testing.assert_array_equal(result.normalized_rms, np.zeros(moving.shape))


def test_repeated_pattern_keeps_distinct_axial_candidates():
    reference = np.tile(np.array([[[0.0, 1.0], [3.0, 7.0]]]), (4, 1, 1))
    moving = np.roll(reference, (1, 1, -1), axis=(0, 1, 2))
    result = assert_surface(moving, reference, 4 * score_allowance(reference.size))
    assert result.candidate_displacements_voxels_zyx == tuple((z, -1, -1) for z in range(-2, 2))


@pytest.mark.parametrize(
    "pair", [(0.0, 0.0), (2.0, -3.0), (np.finfo(float).max, -np.finfo(float).max)]
)
def test_one_voxel_always_has_one_candidate_even_with_bad_fit(pair):
    result = assert_surface(np.array([[[pair[0]]]]), np.array([[[pair[1]]]]), 10.0)
    assert result.displacement_voxels_zyx == (0, 0, 0)
    assert result.failure_code is None


@pytest.mark.parametrize("scale", [2.0**-1000, 1.0, 2.0**1000])
def test_exact_power_of_two_scaling_preserves_stored_ratios(scale):
    reference = np.array([[[1.0, -2.0, 3.0], [4.0, 0.0, 7.0]]])
    moving = np.array([[[2.0, 5.0, -1.0], [3.0, -4.0, 6.0]]])
    # Each scaled value remains normal and the ratios are exactly unchanged.
    expected = stored_surface(moving, reference)
    result = assert_surface(moving * scale, reference * scale)
    np.testing.assert_allclose(
        result.normalized_rms, expected, rtol=0, atol=score_allowance(reference.size)
    )


def test_stable_extremes_subnormals_mixed_scale_and_near_alignment():
    maximum = np.finfo(np.float64).max
    subnormal = np.finfo(np.float64).smallest_subnormal
    cases = [
        (np.array([[[maximum, -maximum, maximum / 2]]]), np.array([[[-maximum, maximum, 0.0]]])),
        (
            np.array([[[subnormal, 2 * subnormal, 4 * subnormal]]]),
            np.array([[[2 * subnormal, -subnormal, subnormal]]]),
        ),
        (np.array([[[maximum, subnormal, 0.0]]]), np.array([[[subnormal, maximum, -subnormal]]])),
    ]
    reference = 1.0 + np.arange(24, dtype=float).reshape(2, 3, 4) / 32
    moving = np.roll(reference, (1, -1, 1), axis=(0, 1, 2)).copy()
    moving[0, 1, 2] += 2.0**-20
    cases.append((moving, reference))
    for moving, reference in cases:
        before = moving.tobytes(), reference.tobytes()
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            with np.errstate(all="raise"):
                mode = np.geterr()
                assert_surface(moving, reference)
                assert np.geterr() == mode
        assert (moving.tobytes(), reference.tobytes()) == before


def test_outputs_own_snapshots_do_not_alias_inputs_or_another_call():
    base = asymmetric_volume((4, 3, 5))
    reference, moving = base[:2], base[2:]
    before = base.tobytes()
    first = assert_surface(moving, reference)
    second = assert_surface(moving, reference)
    assert first is not second
    assert base.tobytes() == before
    for output in (first.normalized_rms, second.normalized_rms):
        assert not np.shares_memory(output, base)
    assert not np.shares_memory(first.normalized_rms, second.normalized_rms)
    first_bytes, second_bytes = first.normalized_rms.tobytes(), second.normalized_rms.tobytes()
    base[:] = -99
    assert first.normalized_rms.tobytes() == first_bytes
    assert second.normalized_rms.tobytes() == second_bytes
    first.normalized_rms[:] = 42
    assert second.normalized_rms.tobytes() == second_bytes
    assert np.all(base == -99)


def test_failure_preserves_shared_strided_readonly_storage_and_error_mode():
    base = asymmetric_volume((4, 3, 5))
    moving, reference = base[::2, :, ::-1], base[1::2, :, ::-1]
    moving.flags.writeable = False
    reference.flags.writeable = False
    before = base.tobytes()
    with np.errstate(divide="raise", over="warn", under="ignore", invalid="raise"):
        mode = np.geterr()
        assert_error("invalid_volume_translation_tolerance", moving, reference, -1)
        assert np.geterr() == mode
        assert_error("incompatible_volume_translation_shape", moving, reference[:, :, :2])
        assert np.geterr() == mode
    assert base.tobytes() == before
    assert not moving.flags.writeable and not reference.flags.writeable


def test_existing_two_dimensional_public_contract_stays_separate():
    reference = np.array([[0.0, 1.0, 4.0], [2.0, 8.0, 3.0]])
    moving = np.roll(reference, (1, -1), axis=(0, 1))
    result = estimate_translation(moving, reference=reference, ambiguity_tolerance=0.0)
    assert type(result) is TranslationEstimate
    assert result.displacement_pixels_yx == (-1, -1)
    np.testing.assert_allclose(
        result.normalized_rms,
        stored_surface(moving, reference),
        rtol=0,
        atol=score_allowance(reference.size),
    )
    assert result.failure_code is None
    with pytest.raises(SimreconError) as caught:
        estimate_translation(
            moving[:, :, None], reference=reference[:, :, None], ambiguity_tolerance=0.0
        )
    assert caught.value.code == "invalid_translation_images"
