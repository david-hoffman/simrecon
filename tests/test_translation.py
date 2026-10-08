"""TRANSLATION-01 blind public-entry contract tests (T01--T10)."""

import warnings
from dataclasses import FrozenInstanceError
from typing import Any, Literal

import numpy as np
import pytest

import simrecon
from translation_fixture import (
    check_result,
    finite_sum_surface,
    grid,
    patterned,
    periodic_motion,
    score_budget,
)


@pytest.fixture
def api() -> Any:
    # Do not import absent names during collection: fail at the public boundary.
    function = getattr(simrecon, "estimate_translation", None)
    assert callable(function), "public estimate_translation export is required"
    return function


@pytest.fixture
def result_type() -> Any:
    result = getattr(simrecon, "TranslationEstimate", None)
    assert isinstance(result, type), "public TranslationEstimate export is required"
    return result


def assert_error(api: Any, code: str, moving: Any, reference: Any, tolerance: Any) -> None:
    error_type = getattr(simrecon, "SimreconError", None)
    assert isinstance(error_type, type), "public SimreconError is required"
    before = snapshots(moving, reference, tolerance)
    old_mode = np.geterr().copy()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        with pytest.raises(error_type) as caught:
            api(moving, reference=reference, ambiguity_tolerance=tolerance)
    assert caught.value.code == code
    assert np.geterr() == old_mode
    assert not any(issubclass(w.category, RuntimeWarning) for w in recorded)
    assert_preserved(before)


def snapshots(*values: Any) -> list[tuple[Any, bytes, Any]]:
    saved: list[tuple[Any, bytes, Any]] = []
    for value in values:
        if isinstance(value, np.ndarray):
            saved.append(
                (
                    value,
                    value.tobytes(order="A"),
                    (value.dtype, value.shape, value.strides, value.flags.writeable),
                )
            )
            if isinstance(value, np.ma.MaskedArray) and isinstance(value.mask, np.ndarray):
                mask = value.mask
                saved.append(
                    (
                        mask,
                        mask.tobytes(order="A"),
                        (mask.dtype, mask.shape, mask.strides, mask.flags.writeable),
                    )
                )
    return saved


def assert_preserved(saved: list[tuple[Any, bytes, Any]]) -> None:
    for value, data, metadata in saved:
        assert (value.dtype, value.shape, value.strides, value.flags.writeable) == metadata
        assert value.tobytes(order="A") == data


def evaluate(
    api: Any,
    result_type: Any,
    moving: Any,
    reference: Any,
    tolerance: Any = 0.001,
    *,
    independent_membership: bool = True,
) -> Any:
    before = snapshots(moving, reference, tolerance)
    old_mode = np.geterr().copy()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        result = api(moving, reference=reference, ambiguity_tolerance=tolerance)
    assert not any(issubclass(w.category, RuntimeWarning) for w in recorded)
    assert np.geterr() == old_mode
    # Verify the oracle inputs before deriving expectations. A product mutation
    # must not change the data that define the independent expected surface.
    assert_preserved(before)
    check_result(
        result,
        moving,
        reference,
        tolerance,
        result_type,
        independent_membership=independent_membership,
    )
    return result


def test_t01_exports_frozen_bindings_and_mutable_surface(api: Any, result_type: Any) -> None:
    reference = patterned((3, 4))
    result = evaluate(api, result_type, reference.copy(), reference)
    replacements = {
        "normalized_rms": np.zeros((3, 4)),
        "minimum_normalized_rms": 7.0,
        "candidate_displacements_pixels_yx": ((7, 7),),
        "displacement_pixels_yx": (7, 7),
        "failure_code": "replacement",
    }
    for name, value in replacements.items():
        with pytest.raises((FrozenInstanceError, AttributeError)):
            setattr(result, name, value)
        with pytest.raises((FrozenInstanceError, AttributeError)):
            delattr(result, name)
    result.normalized_rms[0, 0] = 9.0
    assert result.normalized_rms[0, 0] == 9.0


@pytest.mark.parametrize(
    "binding",
    [
        "no-moving",
        "no-reference",
        "no-tolerance",
        "positional-reference",
        "positional-tolerance",
        "extra",
    ],
)
def test_t01_required_keyword_binding(api: Any, binding: str) -> None:
    image = patterned((2, 3))
    with pytest.raises(TypeError):
        if binding == "no-moving":
            api(reference=image, ambiguity_tolerance=0)
        elif binding == "no-reference":
            api(image, ambiguity_tolerance=0)
        elif binding == "no-tolerance":
            api(image, reference=image)
        elif binding == "positional-reference":
            api(image, image, ambiguity_tolerance=0)
        elif binding == "positional-tolerance":
            api(image, image, 0)
        else:
            api(image, reference=image, ambiguity_tolerance=0, extra=True)


@pytest.mark.parametrize(
    "dtype",
    [
        "i1",
        "u1",
        "i2",
        "u2",
        "i4",
        "u4",
        "i8",
        "u8",
        "f2",
        "f4",
        "f8",
        "longdouble",
        ">i2",
        ">u4",
        ">f4",
        ">f8",
        "<f8",
    ],
)
@pytest.mark.parametrize("side", ["moving", "reference"])
def test_t02_real_dtype_and_endian_classes(
    api: Any, result_type: Any, dtype: str, side: str
) -> None:
    image = np.array([[0, 3, 1], [7, 2, 5]], dtype=dtype)
    shifted = periodic_motion(image, (1, -1))
    moving = shifted if side == "moving" else shifted.astype(np.float64)
    reference = image.astype(np.float64) if side == "moving" else image
    evaluate(api, result_type, moving, reference)


@pytest.mark.parametrize(
    "layout", ["fortran", "transpose", "negative-stride", "strided", "read-only", "overlap"]
)
def test_t02_layout_and_backing_storage_preserved(api: Any, result_type: Any, layout: str) -> None:
    backing = patterned((6, 8)).astype(np.float64)
    if layout == "fortran":
        backing = np.asfortranarray(backing)
        image = backing
    elif layout == "transpose":
        image = backing.T
    elif layout == "negative-stride":
        image = backing[::-1, ::-1]
    elif layout == "strided":
        image = backing[::2, ::2]
    elif layout == "read-only":
        backing.flags.writeable = False
        image = backing
    else:
        image = backing[:, :4]
    reference = backing[:, 2:6] if layout == "overlap" else image.copy()
    before = backing.tobytes(order="A")
    image_flags, reference_flags = image.flags.writeable, reference.flags.writeable
    evaluate(api, result_type, image, reference)
    assert backing.tobytes(order="A") == before
    assert image.flags.writeable == image_flags
    assert reference.flags.writeable == reference_flags


class ImageSubclass(np.ndarray[Any, Any]):
    """A prohibited ndarray subclass, with no special hooks."""


def invalid_image(kind: str) -> Any:
    if kind == "list":
        return [[1.0, 2.0]]
    if kind == "tuple":
        return ((1.0, 2.0),)
    if kind == "scalar":
        return 1.0
    if kind == "none":
        return None
    if kind == "subclass":
        return np.ones((2, 3)).view(ImageSubclass)
    if kind == "masked":
        return np.ma.array(np.ones((2, 3)), mask=False)
    if kind == "bool":
        return np.ones((2, 3), dtype=bool)
    if kind == "complex":
        return np.ones((2, 3), dtype=np.complex128)
    if kind == "object":
        return np.ones((2, 3), dtype=object)
    if kind == "string":
        return np.full((2, 3), "1")
    if kind == "bytes":
        return np.full((2, 3), b"1")
    if kind == "structured":
        return np.zeros((2, 3), dtype=[("value", "f8")])
    if kind == "datetime":
        return np.zeros((2, 3), dtype="datetime64[ns]")
    if kind == "timedelta":
        return np.zeros((2, 3), dtype="timedelta64[ns]")
    if kind == "void":
        return np.zeros((2, 3), dtype="V8")
    if kind == "rank0":
        return np.array(1.0)
    if kind == "rank1":
        return np.ones(6)
    if kind == "rank3":
        return np.ones((1, 2, 3))
    if kind == "empty-y":
        return np.zeros((0, 3))
    if kind == "empty-x":
        return np.zeros((2, 0))
    if kind == "empty-both":
        return np.zeros((0, 0))
    image = np.ones((2, 3))
    image[1, 2] = {"nan": np.nan, "positive-inf": np.inf, "negative-inf": -np.inf}[kind]
    return image


@pytest.mark.parametrize(
    "kind",
    [
        "list",
        "tuple",
        "scalar",
        "none",
        "subclass",
        "masked",
        "bool",
        "complex",
        "object",
        "string",
        "bytes",
        "structured",
        "datetime",
        "timedelta",
        "void",
        "rank0",
        "rank1",
        "rank3",
        "empty-y",
        "empty-x",
        "empty-both",
        "nan",
        "positive-inf",
        "negative-inf",
    ],
)
@pytest.mark.parametrize("side", ["moving", "reference"])
def test_t02_invalid_images(api: Any, kind: str, side: str) -> None:
    valid = patterned((2, 3))
    invalid = invalid_image(kind)
    moving, reference = (invalid, valid) if side == "moving" else (valid, invalid)
    before = valid.tobytes()
    invalid_bytes = invalid.tobytes() if isinstance(invalid, np.ndarray) else None
    assert_error(api, "invalid_translation_images", moving, reference, 0)
    assert valid.tobytes() == before
    if isinstance(invalid, np.ndarray):
        assert invalid.tobytes() == invalid_bytes


@pytest.mark.parametrize("shape", [(1, 1), (1, 5), (6, 1), (3, 5), (4, 6)])
def test_t03_every_canonical_shift(api: Any, result_type: Any, shape: tuple[int, int]) -> None:
    reference = patterned(shape)
    for shift in grid(shape):
        moving = periodic_motion(reference, shift)
        result = evaluate(api, result_type, moving, reference)
        assert result.displacement_pixels_yx == shift
        aligned = np.roll(moving, tuple(-v for v in shift), axis=(0, 1))
        np.testing.assert_array_equal(aligned, reference)


@pytest.mark.parametrize("shape", [(3, 2), (1, 6), (2, 4)])
def test_t03_incompatible_valid_shapes(api: Any, shape: tuple[int, int]) -> None:
    moving, reference = patterned((2, 3)), patterned(shape)
    old_m, old_r = moving.tobytes(), reference.tobytes()
    assert_error(api, "incompatible_translation_shape", moving, reference, 0)
    assert (moving.tobytes(), reference.tobytes()) == (old_m, old_r)


@pytest.mark.parametrize(
    "tolerance",
    [
        0,
        -0.0,
        0.001,
        2,
        3.0,
        np.int8(0),
        np.uint64(3),
        np.float16(0.001),
        np.float32(0.001),
        np.float64(0.001),
        np.longdouble("0.001"),
        np.array(0, dtype=">i8"),
        np.array(0.001, dtype=">f8"),
        np.array(2, dtype="u2"),
        np.array(0.001, dtype=np.longdouble),
        np.nextafter(0.0, 1.0),
        2**1000,
        np.finfo(np.float64).max,
        np.uint64(2**64 - 1),
        np.array(-0.0),
    ],
)
def test_t04_permitted_tolerances(api: Any, result_type: Any, tolerance: Any) -> None:
    reference = patterned((2, 3))
    moving = periodic_motion(reference, (-1, 1))
    result = evaluate(api, result_type, moving, reference, tolerance)
    if float(tolerance) >= 2:
        assert result.candidate_displacements_pixels_yx == grid(reference.shape)


def invalid_tolerance(kind: str) -> Any:
    values: dict[str, Any] = {
        "negative-int": -1,
        "negative-float": -0.01,
        "negative-array": np.array(-0.01),
        "bool": True,
        "numpy-bool": np.bool_(False),
        "bool-array": np.array(False),
        "complex": 1 + 0j,
        "complex-array": np.array(0j),
        "object-array": np.array(0, dtype=object),
        "string": "0.1",
        "string-array": np.array("0.1"),
        "list": [0.1],
        "tuple": (0.1,),
        "rank1": np.array([0.1]),
        "rank2": np.array([[0.1]]),
        "empty": np.array([]),
        "subclass": np.array(0.1).view(ImageSubclass),
        "masked": np.ma.array(0.1, mask=False),
        "none": None,
        "nan": float("nan"),
        "positive-inf": float("inf"),
        "negative-inf": float("-inf"),
        "array-nan": np.array(float("nan")),
        "huge-python-int": 10**1000,
    }
    return values[kind]


@pytest.mark.parametrize(
    "kind",
    [
        "negative-int",
        "negative-float",
        "negative-array",
        "bool",
        "numpy-bool",
        "bool-array",
        "complex",
        "complex-array",
        "object-array",
        "string",
        "string-array",
        "list",
        "tuple",
        "rank1",
        "rank2",
        "empty",
        "subclass",
        "masked",
        "none",
        "nan",
        "positive-inf",
        "negative-inf",
        "array-nan",
        "huge-python-int",
    ],
)
def test_t04_rejected_tolerances(api: Any, kind: str) -> None:
    image = patterned((2, 3))
    before = image.tobytes()
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        assert_error(api, "invalid_translation_tolerance", image, image, invalid_tolerance(kind))
    assert not any(issubclass(w.category, RuntimeWarning) for w in recorded)
    assert image.tobytes() == before


@pytest.mark.parametrize("values", ["wide-conversion", "tiny-conversion", "rounding"])
def test_t02_t04_extended_source_conversion(api: Any, result_type: Any, values: str) -> None:
    wide = np.finfo(np.longdouble)
    double = np.finfo(np.float64)
    if values == "wide-conversion":
        # Platform capability branches are actual dtype limits, never skips.
        if wide.max > np.longdouble(double.max):
            large = np.longdouble(double.max) * np.longdouble(2)
            assert np.isfinite(large)
            for side in ("moving", "reference"):
                image = np.array([[large, 1]], dtype=np.longdouble)
                other = np.ones((1, 2))
                m, r = (image, other) if side == "moving" else (other, image)
                before = image.tobytes()
                with warnings.catch_warnings(record=True) as recorded:
                    warnings.simplefilter("always")
                    assert_error(api, "invalid_translation_images", m, r, 0)
                assert not any(issubclass(w.category, RuntimeWarning) for w in recorded)
                assert image.tobytes() == before
            for tolerance in (large, np.array(large)):
                assert_error(api, "invalid_translation_tolerance", other, other, tolerance)
        else:
            image = np.array([[wide.max]], dtype=np.longdouble)
            evaluate(api, result_type, image, image, np.longdouble(0))
    elif values == "tiny-conversion":
        tiny = np.nextafter(np.longdouble(0), np.longdouble(1))
        # Only assert underflow rules if the source type can represent them.
        if wide.smallest_subnormal < np.longdouble(double.smallest_subnormal):
            assert tiny > 0 and float(tiny) == 0
            image = np.array([[tiny, -tiny]], dtype=np.longdouble)
            evaluate(api, result_type, image, np.zeros((1, 2)), tiny, independent_membership=False)
            evaluate(api, result_type, image, image, np.array(tiny), independent_membership=False)
            for tolerance in (-tiny, np.array(-tiny)):
                assert_error(api, "invalid_translation_tolerance", image, image, tolerance)
        else:
            image = np.array([[tiny, -tiny]], dtype=np.longdouble)
            evaluate(api, result_type, image, image)
    else:
        image = np.array([[2**53 + 1, 2**53 + 5, 2**53 + 9]], dtype=np.uint64)
        reference = np.array([[2**53, 2**53 + 4, 2**53 + 8]], dtype=np.float64)
        evaluate(api, result_type, image, reference, independent_membership=False)
        if wide.nmant > double.nmant:
            source = np.array(
                [[np.longdouble(1) + np.longdouble(2) ** -60, -1]], dtype=np.longdouble
            )
            evaluate(
                api, result_type, source, np.array([[1.0, -1.0]]), independent_membership=False
            )


@pytest.mark.parametrize(
    "case", ["off-model", "gain", "offset", "negative-gain", "border", "unequal-energy"]
)
def test_t05_t07_fixed_objective_off_model(api: Any, result_type: Any, case: str) -> None:
    reference = np.array([[3.0, -2.0, 0.0], [7.0, 1.0, -4.0]])
    if case == "off-model":
        moving = np.array([[-1.0, 4.0, 2.0], [0.0, -3.0, 5.0]])
    elif case == "gain":
        moving = 2 * periodic_motion(reference, (-1, 1))
    elif case == "offset":
        moving = periodic_motion(reference, (0, -1)) + 20
    elif case == "negative-gain":
        moving = -periodic_motion(reference, (-1, 0))
    elif case == "border":
        reference = np.array([[10.0, 0.0, 1.0, 0.0, 0.0]])
        moving = np.array([[0.0, 2.0, 0.0, 0.0, 10.0]])
    else:
        moving = np.array([[100.0, 0.0, 0.0], [0.0, 0.0, -0.01]])
    result = evaluate(api, result_type, moving, reference)
    assert result.minimum_normalized_rms > score_budget(reference.size)


@pytest.mark.parametrize("scale", [2.0**900, 2.0**-900, -8.0])
def test_t05_common_exact_scaling(api: Any, result_type: Any, scale: float) -> None:
    reference = np.array([[0.125, -0.25, 0.5], [1.0, -0.75, 0.0]])
    moving = np.array([[0.75, 0.0, -0.125], [-0.5, 0.25, 1.0]])
    original = evaluate(api, result_type, moving, reference)
    scaled = evaluate(api, result_type, moving * scale, reference * scale)
    difference = np.max(np.abs(original.normalized_rms - scaled.normalized_rms))
    assert difference <= 2 * score_budget(reference.size)


@pytest.mark.parametrize(
    "case",
    [
        "zeros",
        "equal-constant",
        "unequal-constant",
        "opposite-constant",
        "repeated-x",
        "repeated-y",
        "repeated-both",
    ],
)
def test_t06_t07_no_information_rejection_or_first_winner(
    api: Any, result_type: Any, case: str
) -> None:
    if case == "zeros":
        reference, moving = np.zeros((3, 4)), np.zeros((3, 4))
    elif case == "equal-constant":
        reference, moving = np.full((2, 3), -3.0), np.full((2, 3), -3.0)
    elif case == "unequal-constant":
        reference, moving = np.full((2, 3), 2.0), np.full((2, 3), 5.0)
    elif case == "opposite-constant":
        reference, moving = np.ones((2, 3)), -np.ones((2, 3))
    elif case == "repeated-x":
        reference = np.array([[1, 2, 1, 2], [7, -1, 7, -1]])
        moving = periodic_motion(reference, (-1, 1))
    elif case == "repeated-y":
        reference = np.array([[1, 2, 7], [1, 2, 7], [1, 2, 7]])
        moving = periodic_motion(reference, (1, -1))
    else:
        reference = np.tile(np.array([[1, 2], [7, -1]]), (2, 3))
        moving = periodic_motion(reference, (1, 1))
    result = evaluate(api, result_type, moving, reference)
    assert result.failure_code == "ambiguous_translation"
    assert result.displacement_pixels_yx is None


@pytest.mark.parametrize("pair", [(0.0, 0.0), (1.0, -1.0), (7.0, 2.0)])
def test_t03_t07_singleton_always_unique(
    api: Any, result_type: Any, pair: tuple[float, float]
) -> None:
    moving, reference = (np.array([[v]]) for v in pair)
    result = evaluate(api, result_type, moving, reference, 0)
    assert result.displacement_pixels_yx == (0, 0)
    assert result.candidate_displacements_pixels_yx == ((0, 0),)


def test_t06_inclusive_same_call_subtraction_and_no_hidden_epsilon(
    api: Any, result_type: Any
) -> None:
    # Dy has one candidate; dx=-1 is worse by exactly 1 for every valid score
    # at the analytic objective. Membership is always checked against *this*
    # call's returned values, even if backend rounding varies between calls.
    reference = np.array([[1.0, 0.0]])
    moving = reference.copy()
    for tolerance in (np.nextafter(1.0, 0.0), 1.0, np.nextafter(1.0, 2.0)):
        evaluate(api, result_type, moving, reference, tolerance, independent_membership=False)
    initial = api(moving, reference=reference, ambiguity_tolerance=0)
    differences = initial.normalized_rms - initial.minimum_normalized_rms
    boundary = float(np.max(differences))
    for tolerance in (np.nextafter(boundary, 0.0), boundary, np.nextafter(boundary, np.inf)):
        evaluate(api, result_type, moving, reference, tolerance, independent_membership=False)


@pytest.mark.parametrize(
    "tolerance,expected_candidates",
    [(0.0, ((0, 0),)), (2.5e-7, ((0, 0), (0, 1)))],
)
def test_t06_nonzero_minimum_has_no_relative_allowance(
    api: Any,
    result_type: Any,
    tolerance: float,
    expected_candidates: tuple[tuple[int, int], ...],
) -> None:
    reference = np.array([[1.0, 0.0, 0.0]])
    moving = np.array([[1001.0, 1000.5, 1000.0]])
    # B=1001, P=3. Canonical squared-score numerators are 3001002.25,
    # 3001000.25, 3001001.25, all divided by 3006003. The minimum is
    # nonzero, so an unintended relative allowance can admit wrong shifts.
    # At tolerance 2.5e-7, the closest boundary is >8.29e-8 away, versus
    # 2 delta <5.46e-12. Zero tolerance also has a separated sole minimum.
    result = evaluate(api, result_type, moving, reference, tolerance)
    assert result.minimum_normalized_rms > 0.99
    assert result.candidate_displacements_pixels_yx == expected_candidates
    if len(expected_candidates) == 1:
        assert result.displacement_pixels_yx == (0, 0)
        assert result.failure_code is None
    else:
        assert result.displacement_pixels_yx is None
        assert result.failure_code == "ambiguous_translation"


def test_t06_exact_computed_ties_zero_tolerance(api: Any, result_type: Any) -> None:
    for moving, reference in (
        (np.zeros((2, 3)), np.zeros((2, 3))),
        (np.ones((2, 3)), np.ones((2, 3))),
        (np.array([[1, 2, 1, 2]]), np.array([[2, 1, 2, 1]])),
    ):
        evaluate(api, result_type, moving, reference, 0, independent_membership=False)


@pytest.mark.parametrize(
    "case",
    [
        "max-opposite",
        "max-mixed",
        "subnormal",
        "subnormal-mixed",
        "near-perfect",
        "uint64-max",
        "int64-min",
    ],
)
@pytest.mark.parametrize("mode", ["warn", "raise", "ignore"])
def test_t08_t09_stability_and_error_mode(
    api: Any, result_type: Any, case: str, mode: Literal["warn", "raise", "ignore"]
) -> None:
    maximum = np.finfo(np.float64).max
    tiny = np.nextafter(0.0, 1.0)
    if case == "max-opposite":
        reference = np.array([[maximum, -maximum, maximum / 2]])
        moving = -reference
    elif case == "max-mixed":
        reference = np.array([[maximum, 0.0], [tiny, -maximum]])
        moving = np.array([[-maximum, tiny], [0.0, maximum]])
    elif case == "subnormal":
        reference = np.array([[tiny, 2 * tiny, -4 * tiny]])
        moving = periodic_motion(reference, (0, -1))
    elif case == "subnormal-mixed":
        reference = np.array([[tiny, 0.0, 1.0], [-tiny, -0.25, 0.0]])
        moving = np.array([[0.0, tiny, 0.75], [-tiny, -0.5, 0.0]])
    elif case == "near-perfect":
        reference = np.array([[0.5, -1.0, 0.25], [0.0, 0.75, -0.5]])
        moving = periodic_motion(reference, (-1, 1))
        moving[0, 0] += 2.0**-27
    elif case == "uint64-max":
        reference = np.array([[2**64 - 1, 0, 2**63]], dtype=np.uint64)
        moving = periodic_motion(reference, (0, 1))
    else:
        reference = np.array([[-(2**63), 0, 2**62]], dtype=np.int64)
        moving = periodic_motion(reference, (0, -1))
    saved = np.seterr(all=mode)
    try:
        result = evaluate(api, result_type, moving, reference)
        assert np.geterr() == dict.fromkeys(saved, mode)
        if case == "near-perfect":
            # Exact stored perturbation: one changed pixel, B=1, P=6.
            analytic = 2.0**-27 / np.sqrt(6.0)
            assert analytic > 100 * score_budget(reference.size)
            assert abs(result.minimum_normalized_rms - analytic) <= score_budget(reference.size)
            assert result.minimum_normalized_rms > 0
    finally:
        np.seterr(**saved)


def test_t09_output_does_not_alias_other_calls_or_future_inputs(api: Any, result_type: Any) -> None:
    reference = patterned((3, 4)).astype(np.float64)
    moving = periodic_motion(reference, (1, -1))
    original_m, original_r = moving.copy(), reference.copy()
    first = evaluate(api, result_type, moving, reference)
    second = evaluate(api, result_type, moving, reference)
    assert not np.shares_memory(first.normalized_rms, second.normalized_rms)
    retained = first.normalized_rms.copy()
    moving.fill(999)
    reference.fill(-999)
    np.testing.assert_array_equal(first.normalized_rms, retained)
    check_result(first, original_m, original_r, 0.001, result_type)
    first.normalized_rms.fill(99)
    check_result(second, original_m, original_r, 0.001, result_type)


def test_t04_t09_validation_precedes_numerical_evaluation(api: Any) -> None:
    # Even this valid, arithmetic-sensitive input must reject negative tolerance.
    maximum = np.finfo(np.float64).max
    moving = np.array([[maximum, -maximum]])
    reference = -moving
    before = moving.tobytes(), reference.tobytes()
    saved = np.seterr(all="raise")
    try:
        assert_error(api, "invalid_translation_tolerance", moving, reference, -1)
        assert np.geterr() == dict.fromkeys(saved, "raise")
    finally:
        np.seterr(**saved)
    assert (moving.tobytes(), reference.tobytes()) == before


def test_t10_executed_known_shift_ambiguity_and_off_model_usage(api: Any, result_type: Any) -> None:
    reference = patterned((3, 5))
    moving = periodic_motion(reference, (1, -2))
    known = evaluate(api, result_type, moving, reference)
    assert known.displacement_pixels_yx == (1, -2)
    np.testing.assert_array_equal(np.roll(moving, (-1, 2), axis=(0, 1)), reference)
    ambiguous = evaluate(api, result_type, moving, reference, 3)
    assert ambiguous.displacement_pixels_yx is None
    changed = moving.astype(np.float64) + 7.0
    off_model = evaluate(api, result_type, changed, reference)
    oracle = finite_sum_surface(changed, reference)
    assert np.min(oracle) > 0.1
    assert off_model.minimum_normalized_rms > 0.1


def test_t03_modest_nonstandard_size_has_no_information_cap(api: Any, result_type: Any) -> None:
    reference = patterned((2, 33))
    moving = periodic_motion(reference, (-1, -16))
    result = evaluate(api, result_type, moving, reference)
    assert result.displacement_pixels_yx == (-1, -16)


def test_t09_mixed_error_mode_and_handler_preserved(api: Any, result_type: Any) -> None:
    calls: list[tuple[str, int]] = []

    def on_error(message: str, flag: int) -> None:
        calls.append((message, flag))

    reference = np.array([[np.finfo(np.float64).max, 0, -np.finfo(np.float64).max]])
    moving = periodic_motion(reference, (0, 1))
    previous_handler = np.seterrcall(on_error)
    previous_mode = np.seterr(divide="call", over="raise", under="warn", invalid="ignore")
    active_mode = np.geterr().copy()
    try:
        evaluate(api, result_type, moving, reference)
        assert np.geterr() == active_mode
        assert np.geterrcall() is on_error
        assert calls == []
    finally:
        np.seterr(**previous_mode)
        np.seterrcall(previous_handler)
