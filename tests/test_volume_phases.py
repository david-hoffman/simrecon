"""Blind public-entry contract tests for VOLUME-PHASE-01 (V01--V10)."""

import warnings
from decimal import Decimal, localcontext
from typing import Any

import numpy as np
import pytest

import simrecon
from volume_phase_fixture import (
    PRECISION,
    UNEQUAL_PHASES,
    condition_upper_bound,
    exact,
    represented_basis,
    spatial_coordinates,
    stored_input_oracle,
    synthesize,
)


@pytest.fixture
def api() -> Any:
    # Missing new APIs are ordinary assertion failures, not collection imports.
    operation = getattr(simrecon, "separate_volume_phases", None)
    assert callable(operation), "missing public separate_volume_phases"
    assert isinstance(getattr(simrecon, "VolumePhaseComponents", None), type), (
        "missing public VolumePhaseComponents"
    )
    return operation


def output_coordinates(result: Any) -> np.ndarray:
    return np.stack((result.dc, result.c1.real, result.c1.imag, result.c2.real, result.c2.imag))


def assert_stored_fit(result: Any, images: np.ndarray, phases: np.ndarray) -> None:
    """Check all five coordinates using non-underflowing Decimal budgets."""
    assert condition_upper_bound(phases) < 10, "fixture outside informative regime"
    arrays = [result.dc, result.c1, result.c2]
    for i, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.shape == images.shape[1:]
        assert array.dtype == np.dtype(np.float64 if i == 0 else np.complex128)
        assert array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        for other in [images, phases, *arrays[:i]]:
            assert not np.shares_memory(array, other)
    expected, budgets = stored_input_oracle(images, phases)
    actual = output_coordinates(result).reshape(5, -1).T
    assert actual.shape == (len(expected), 5)
    assert np.isfinite(actual).all()
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for v, (row, truth, budget) in enumerate(zip(actual, expected, budgets, strict=True)):
            for j, (value, reference) in enumerate(zip(row, truth, strict=True)):
                error = abs(exact(value) - reference)
                assert error <= budget, (v, j, str(error), str(budget))


def array_state(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return (
            value.tobytes(),
            value.shape,
            value.strides,
            value.dtype.str,
            value.flags.writeable,
        )
    return None


def assert_rejected(api: Any, images: Any, phases: Any, code: str) -> None:
    before = (array_state(images), array_state(phases))
    mode = np.geterr().copy()
    error_type = getattr(simrecon, "SimreconError", None)
    assert isinstance(error_type, type)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(error_type) as failure:
            api(images, phases_rad=phases)
    assert failure.value.code == code
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.geterr() == mode
    assert (array_state(images), array_state(phases)) == before


def basic_images(n: int = 8) -> np.ndarray:
    return np.arange(n * 6, dtype=np.float64).reshape(n, 1, 2, 3) - 15


def test_public_exports_binding_and_existing_entry(api: Any) -> None:
    """V01/V10: exports and Python's keyword-only required argument binding."""
    assert callable(getattr(simrecon, "separate_phases", None))
    images = basic_images()
    for arguments, keywords in [
        ((images,), {}),
        ((images, UNEQUAL_PHASES), {}),
        ((), {"phases_rad": UNEQUAL_PHASES}),
        ((images,), {"phases_rad": UNEQUAL_PHASES, "unexpected": 1}),
    ]:
        with pytest.raises(TypeError):
            api(*arguments, **keywords)
    # The sole positional parameter is also usable by its documented name.
    result = api(images=images, phases_rad=UNEQUAL_PHASES)
    assert_stored_fit(result, images, UNEQUAL_PHASES)


def test_frozen_bindings_owned_mutable_native_storage(api: Any) -> None:
    """V01/V08: each result array owns independent mutable storage."""
    phases = UNEQUAL_PHASES.copy()
    images = synthesize(phases, spatial_coordinates())
    before = (array_state(images), array_state(phases))
    first = api(images, phases_rad=phases)
    second = api(images, phases_rad=phases)
    component_type = getattr(simrecon, "VolumePhaseComponents", None)
    assert isinstance(component_type, type)
    assert isinstance(first, component_type)
    public_fields = {
        name
        for name in dir(first)
        if not name.startswith("_") and not callable(getattr(first, name))
    }
    assert public_fields == {"dc", "c1", "c2"}
    arrays = [getattr(result, name) for result in (first, second) for name in ("dc", "c1", "c2")]
    for i, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.shape == (2, 3, 4)
        assert array.dtype == np.dtype(np.float64 if i % 3 == 0 else np.complex128)
        assert array.dtype.isnative
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        for other in [images, phases, *arrays[:i]]:
            assert not np.shares_memory(array, other)
    assert_stored_fit(first, images, phases)
    for name in ("dc", "c1", "c2"):
        original = getattr(first, name)
        for action in ("assign", "delete"):
            try:
                if action == "assign":
                    setattr(first, name, np.zeros((2, 3, 4)))
                else:
                    delattr(first, name)
            except Exception:
                # The contract requires frozen bindings, without specifying
                # an exception class or a dataclass implementation.
                assert getattr(first, name) is original
            else:
                pytest.fail(f"public field {name} permits {action}")
    second_before = [array.copy() for array in arrays[3:]]
    untouched_first = [first.c1.copy(), first.c2.copy()]
    first.dc[...] = -123
    np.testing.assert_array_equal(first.c1, untouched_first[0])
    np.testing.assert_array_equal(first.c2, untouched_first[1])
    for current, saved in zip(arrays[3:], second_before, strict=True):
        np.testing.assert_array_equal(current, saved)
    first.c1[...] = 9 + 11j
    np.testing.assert_array_equal(first.c2, untouched_first[1])
    first.c2[...] = -4j
    assert (array_state(images), array_state(phases)) == before


class ArraySubclass(np.ndarray):
    """A forbidden ndarray subtype, without custom conversion behavior."""


@pytest.mark.parametrize("kind", ["list", "tuple", "none", "scalar", "subclass", "masked"])
def test_image_container_rejections(api: Any, kind: str) -> None:
    images = basic_images()
    cases = {
        "list": images.tolist(),
        "tuple": tuple(images),
        "none": None,
        "scalar": np.float64(1),
        "subclass": images.view(ArraySubclass),
        "masked": np.ma.array(images, mask=False),
    }
    assert_rejected(api, cases[kind], UNEQUAL_PHASES, "invalid_volume_phase_images")


@pytest.mark.parametrize("kind", ["list", "tuple", "none", "scalar", "subclass", "masked"])
def test_phase_container_rejections(api: Any, kind: str) -> None:
    phases = UNEQUAL_PHASES
    cases = {
        "list": phases.tolist(),
        "tuple": tuple(phases),
        "none": None,
        "scalar": np.float64(1),
        "subclass": phases.view(ArraySubclass),
        "masked": np.ma.array(phases, mask=False),
    }
    assert_rejected(api, basic_images(), cases[kind], "invalid_volume_phase_angles")


BAD_DTYPES = [
    np.dtype("bool"),
    np.dtype("complex64"),
    np.dtype("complex128"),
    np.dtype("object"),
    np.dtype("U4"),
    np.dtype("S4"),
    np.dtype([("intensity", "f8")]),
    np.dtype("datetime64[ns]"),
    np.dtype("timedelta64[ns]"),
    np.dtype("V8"),
]


@pytest.mark.parametrize("dtype", BAD_DTYPES, ids=str)
@pytest.mark.parametrize("which", ["images", "phases"])
def test_dtype_rejections(api: Any, dtype: np.dtype, which: str) -> None:
    images, phases = basic_images(), UNEQUAL_PHASES.copy()
    if which == "images":
        images = np.zeros(images.shape, dtype=dtype)
        code = "invalid_volume_phase_dtype"
    else:
        phases = np.zeros(phases.shape, dtype=dtype)
        code = "invalid_volume_phase_angles_dtype"
    assert_rejected(api, images, phases, code)


@pytest.mark.parametrize(
    "shape",
    [
        (),
        (8,),
        (8, 2, 3),
        (8, 1, 2, 3, 1),
        (4, 1, 2, 3),
        (0, 1, 2, 3),
        (8, 0, 2, 3),
        (8, 1, 0, 3),
        (8, 1, 2, 0),
    ],
)
def test_image_shape_rejections(api: Any, shape: tuple[int, ...]) -> None:
    # Match any available exposure count so the case does not also introduce
    # a phase-count error with unspecified simultaneous-error precedence.
    phases = np.resize(UNEQUAL_PHASES, shape[0]) if shape else UNEQUAL_PHASES
    assert_rejected(api, np.zeros(shape), phases, "invalid_volume_phase_shape")


@pytest.mark.parametrize("shape", [(), (8, 1), (1, 8), (8, 1, 1), (7,), (9,), (0,)])
def test_phase_shape_rejections(api: Any, shape: tuple[int, ...]) -> None:
    assert_rejected(api, basic_images(), np.zeros(shape), "invalid_volume_phase_angles_shape")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("which", ["images", "phases"])
def test_nonfinite_source_rejections(api: Any, value: float, which: str) -> None:
    images, phases = basic_images(), UNEQUAL_PHASES.copy()
    if which == "images":
        images[-1, -1, -1, -1] = value
        code = "nonfinite_volume_phase_images"
    else:
        phases[-1] = value
        code = "nonfinite_volume_phase_angles"
    with np.errstate(all="raise"):
        assert_rejected(api, images, phases, code)


GOOD_DTYPES = [
    np.dtype(name).newbyteorder(order)
    for name in ("i1", "i2", "i4", "i8", "u1", "u2", "u4", "u8", "f2", "f4", "f8", "longdouble")
    for order in ("=", ">", "<")
]


@pytest.mark.parametrize("dtype", GOOD_DTYPES, ids=lambda d: d.str)
def test_permitted_image_dtypes_define_converted_problem(api: Any, dtype: np.dtype) -> None:
    # Signed dtypes include negative observations; unsigned cases remain valid.
    images = np.arange(8 * 6).reshape(8, 1, 2, 3)
    if dtype.kind != "u":
        images = images - 19
    images = images.astype(dtype)
    before = array_state(images)
    result = api(images, phases_rad=UNEQUAL_PHASES)
    assert_stored_fit(result, images, UNEQUAL_PHASES)
    assert array_state(images) == before


@pytest.mark.parametrize("dtype", GOOD_DTYPES, ids=lambda d: d.str)
def test_permitted_phase_dtypes_define_converted_problem(api: Any, dtype: np.dtype) -> None:
    phases = np.arange(8, dtype=np.int64)
    if dtype.kind != "u":
        phases -= 3
    phases = phases.astype(dtype)
    images = basic_images()
    before = array_state(phases)
    result = api(images, phases_rad=phases)
    assert_stored_fit(result, images, phases)
    assert array_state(phases) == before


@pytest.mark.parametrize("which", ["images", "phases"])
def test_wider_float_conversion_if_representable_on_platform(api: Any, which: str) -> None:
    """No skip: aliases exercise ordinary conversion; wider formats add overflow."""
    wider = np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp
    if wider:
        with np.errstate(all="ignore"):
            huge = np.longdouble(np.finfo(np.float64).max) * np.longdouble(4)
        assert np.isfinite(huge)
        images, phases = basic_images().astype(np.longdouble), UNEQUAL_PHASES.astype(np.longdouble)
        if which == "images":
            images[0, 0, 0, 0] = huge
            code = "nonfinite_volume_phase_images"
        else:
            phases[0] = huge
            code = "nonfinite_volume_phase_angles"
        with np.errstate(all="raise"):
            assert_rejected(api, images, phases, code)
    else:
        images = basic_images().astype(np.longdouble)
        phases = UNEQUAL_PHASES.astype(np.longdouble)
        assert_stored_fit(api(images, phases_rad=phases), images, phases)


def test_conversion_rounding_and_finite_underflow(api: Any) -> None:
    # Integer information above 2**53 is rounded before defining the problem.
    images = np.full((8, 1, 1, 1), 2**53 + 1, dtype=np.uint64)
    images[3, 0, 0, 0] += np.uint64(4)
    result = api(images, phases_rad=UNEQUAL_PHASES)
    assert_stored_fit(result, images, UNEQUAL_PHASES)
    # A phase is rounded to binary64 too, including integers above 2**53.
    phases = np.array([0, 1, 2, 3, 4, 5, 2**53 + 1, 2**53 + 3], dtype=np.uint64)
    images = basic_images()
    assert_stored_fit(api(images, phases_rad=phases), images, phases)
    # Every platform executes this test; only a genuinely wider exponent range
    # can supply a nonzero source value that underflows on float64 conversion.
    if np.finfo(np.longdouble).minexp < np.finfo(np.float64).minexp:
        with np.errstate(all="ignore"):
            tiny = np.longdouble(float.fromhex("0x0.0000000000001p-1022")) / 4
        assert tiny != 0
        images = np.full((8, 1, 1, 1), tiny, dtype=np.longdouble)
        phases = UNEQUAL_PHASES.astype(np.longdouble)
        phases[0] = tiny
        with np.errstate(all="raise"):
            result = api(images, phases_rad=phases)
        assert_stored_fit(result, images, phases)


@pytest.mark.parametrize("layout", ["fortran", "reversed", "stepped", "readonly"])
def test_valid_storage_layouts_and_preservation(api: Any, layout: str) -> None:
    phases = UNEQUAL_PHASES.copy()
    images = synthesize(phases, spatial_coordinates())
    if layout == "fortran":
        images = np.asfortranarray(images)
    elif layout == "reversed":
        images = images[::-1, ::-1, ::-1, ::-1]
        phases = phases[::-1]
    elif layout == "stepped":
        image_backing = np.full((16, 4, 6, 8), -987.0)
        image_backing[::2, ::2, ::2, ::2] = images
        images = image_backing[::2, ::2, ::2, ::2]
        phase_backing = np.full(16, -987.0)
        phase_backing[::2] = phases
        phases = phase_backing[::2]
    else:
        images.flags.writeable = False
        phases.flags.writeable = False
    # Include storage outside each strided view in the preservation assertion.
    image_owner = images.base if isinstance(images.base, np.ndarray) else images
    phase_owner = phases.base if isinstance(phases.base, np.ndarray) else phases
    before = tuple(array_state(a) for a in (images, phases, image_owner, phase_owner))
    result = api(images, phases_rad=phases)
    assert_stored_fit(result, images, phases)
    assert tuple(array_state(a) for a in (images, phases, image_owner, phase_owner)) == before


def test_overlapping_input_views_are_valid_and_preserved(api: Any) -> None:
    backing = np.arange(8 * 6, dtype=np.float64)
    images = backing.reshape(8, 1, 2, 3)
    phases = backing[::6]
    phases[...] = UNEQUAL_PHASES
    assert np.shares_memory(images, phases)
    before = array_state(backing)
    result = api(images, phases_rad=phases)
    assert_stored_fit(result, images, phases)
    assert array_state(backing) == before
    for output in (result.dc, result.c1, result.c2):
        assert not np.shares_memory(output, backing)


@pytest.mark.parametrize("which", ["images", "phases"])
def test_rejection_preserves_entire_strided_readonly_backing(api: Any, which: str) -> None:
    image_backing = np.full((16, 2, 4, 6), 17.0)
    phase_backing = np.full(16, 17.0)
    images = image_backing[::2, ::2, ::2, ::2]
    phases = phase_backing[::2]
    phases[...] = UNEQUAL_PHASES
    if which == "images":
        images[-1, -1, -1, -1] = np.nan
        code = "nonfinite_volume_phase_images"
    else:
        phases[-1] = np.nan
        code = "nonfinite_volume_phase_angles"
    images.flags.writeable = False
    phases.flags.writeable = False
    before = (array_state(image_backing), array_state(phase_backing))
    assert_rejected(api, images, phases, code)
    assert (array_state(image_backing), array_state(phase_backing)) == before


def test_canonical_sign_factor_and_all_five_coordinates(api: Any) -> None:
    """V04: the documented 10+4c+2s+6c2-8s2 example."""
    phases = np.arange(8, dtype=np.float64) * (np.pi / 4)
    coordinates = np.array([10, 2, -1, 3, 4], dtype=np.float64).reshape(5, 1, 1, 1)
    images = synthesize(phases, coordinates)
    result = api(images, phases_rad=phases)
    assert_stored_fit(result, images, phases)
    # The stored-input oracle also independently bounds the departure from
    # the analytic coefficients; roots of unity are never assumed exact.
    reference, _ = stored_input_oracle(images, phases)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        assert max(
            abs(x - exact(y)) for x, y in zip(reference[0], coordinates[:, 0, 0, 0], strict=True)
        ) < Decimal("1e-14")


@pytest.mark.parametrize("order", range(5))
def test_isolated_coordinates_no_cross_order_leakage(api: Any, order: int) -> None:
    coordinates = np.zeros((5, 2, 3, 4))
    coordinates[order] = spatial_coordinates()[order]
    images = synthesize(UNEQUAL_PHASES, coordinates)
    result = api(images, phases_rad=UNEQUAL_PHASES)
    assert_stored_fit(result, images, UNEQUAL_PHASES)


@pytest.mark.parametrize("magnitude", ["large", "doubled_overflow"])
def test_direct_represented_phasors_for_huge_finite_phases(api: Any, magnitude: str) -> None:
    if magnitude == "large":
        phases = np.array([1e15, -1e16, 1e20, -1e25, 1e50, -1e100, 1e150, -1e200])
    else:
        maximum = np.finfo(np.float64).max
        phases = np.array(
            [
                1e308,
                -1e308,
                maximum,
                -maximum,
                np.nextafter(maximum, 0),
                -np.nextafter(maximum, 0),
                1.1e308,
                -1.3e308,
                1e200,
                -1e150,
                0.2,
                1.7,
                3.8,
                5.2,
            ]
        )
    images = synthesize(phases, spatial_coordinates())
    before = (array_state(images), array_state(phases))
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
        warnings.simplefilter("always")
        result = api(images, phases_rad=phases)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert_stored_fit(result, images, phases)
    assert (array_state(images), array_state(phases)) == before


def test_unequal_off_model_projection_and_joint_permutation(api: Any) -> None:
    """V05: genuine nonzero residual, unweighted fit, dc != sample mean."""
    phases = UNEQUAL_PHASES
    images = synthesize(phases, spatial_coordinates())
    images[1, ...] += 3.25
    images[5, 1, 2, 3] -= 7.5
    expected, _ = stored_input_oracle(images, phases)
    h = represented_basis(phases)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        first = expected[0]
        fitted = [
            exact(row[0]) * first[0]
            + 2 * exact(row[1]) * first[1]
            - 2 * exact(row[2]) * first[2]
            + 2 * exact(row[3]) * first[3]
            - 2 * exact(row[4]) * first[4]
            for row in h
        ]
        residual = [exact(b) - fit for b, fit in zip(images[:, 0, 0, 0], fitted, strict=True)]
        assert max(abs(r) for r in residual) > Decimal("0.1")
        assert abs(
            first[0] - sum((exact(b) for b in images[:, 0, 0, 0]), Decimal(0)) / len(phases)
        ) > Decimal("0.1")
        # Exact normal-equation residual orthogonality is a fixture audit,
        # independent of the returned product coordinates.
        for j in range(5):
            assert abs(
                sum(exact(row[j]) * r for row, r in zip(h, residual, strict=True))
            ) < Decimal("1e-100")
    original = api(images, phases_rad=phases)
    assert_stored_fit(original, images, phases)
    permutation = np.array([5, 0, 7, 2, 4, 1, 6, 3])
    permuted = api(images[permutation], phases_rad=phases[permutation])
    assert_stored_fit(permuted, images[permutation], phases[permutation])
    # Separate oracle checks imply permutation agreement within the sum of
    # the two accuracy budgets; no bitwise backend invariance is required.


@pytest.mark.parametrize("case", ["constant", "four_unique", "five_nominal", "too_clustered"])
@pytest.mark.parametrize("zero_observations", [False, True])
def test_rank_deficient_phase_sets(api: Any, case: str, zero_observations: bool) -> None:
    phases = {
        "constant": np.ones(8),
        "four_unique": np.array([0, 1, 2, 3, 0, 1, 2, 3], dtype=np.float64),
        "five_nominal": np.array([0, 1, 2, 3, 0], dtype=np.float64),
        "too_clustered": np.arange(8, dtype=np.float64) * 1e-12,
    }[case]
    images = basic_images(len(phases))
    if zero_observations:
        images[...] = 0
    assert_rejected(api, images, phases, "rank_deficient_volume_phases")


def test_valid_five_rows_and_repeated_phases(api: Any) -> None:
    five = np.array([0.1, 1.3, 2.5, 3.7, 5.0])
    for phases in (five, five[[0, 1, 2, 3, 4, 1, 1, 3]]):
        images = synthesize(phases, spatial_coordinates((1, 2, 3)))
        assert_stored_fit(api(images, phases_rad=phases), images, phases)


def test_full_rank_cluster_has_no_span_or_condition_rejection(api: Any) -> None:
    phases = np.arange(5, dtype=np.float64) * 0.01
    # Independent condition bound certifies rank well above the contract
    # cutoff, while this deliberately leaves the uniform-accuracy regime.
    bound = condition_upper_bound(phases)
    assert Decimal(10) < bound < Decimal("1e12")
    images = np.full((5, 1, 1, 1), 3.0)
    result = api(images, phases_rad=phases)
    assert output_coordinates(result).shape == (5, 1, 1, 1)
    assert np.isfinite(output_coordinates(result)).all()


@pytest.mark.parametrize("shape", [(1, 1, 1), (1, 3, 2), (2, 1, 3), (3, 2, 1), (2, 3, 4)])
def test_voxel_axes_singletons_and_independence(api: Any, shape: tuple[int, int, int]) -> None:
    images = synthesize(UNEQUAL_PHASES, spatial_coordinates(shape))
    original = api(images, phases_rad=UNEQUAL_PHASES)
    assert original.dc.shape == shape
    assert_stored_fit(original, images, UNEQUAL_PHASES)
    changed = images.copy()
    changed[:, -1, -1, -1] += np.arange(8) - 2
    result = api(changed, phases_rad=UNEQUAL_PHASES)
    assert_stored_fit(result, changed, UNEQUAL_PHASES)
    mask = np.ones(shape, dtype=bool)
    mask[-1, -1, -1] = False
    # Both calls must match their own voxelwise truth. A separate spatial-axis
    # transpose checks axis equivariance without imposing bitwise equality.
    transposed = images.transpose(0, 3, 1, 2)
    assert_stored_fit(api(transposed, phases_rad=UNEQUAL_PHASES), transposed, UNEQUAL_PHASES)
    if mask.any():
        before = output_coordinates(original)[:, mask]
        after = output_coordinates(result)[:, mask]
        _, budgets = stored_input_oracle(images, UNEQUAL_PHASES)
        with localcontext() as ctx:
            ctx.prec = PRECISION
            for row_a, row_b, budget in zip(
                before.T,
                after.T,
                [b for b, m in zip(budgets, mask.flat, strict=True) if m],
                strict=True,
            ):
                for a, b in zip(row_a, row_b, strict=True):
                    assert abs(exact(a) - exact(b)) <= 2 * budget


@pytest.mark.parametrize(
    "scale",
    [
        0.0,
        float.fromhex("0x0.0000000000001p-1022"),
        float.fromhex("0x1p-1022"),
        1e-200,
        1.0,
        1e100,
        np.finfo(np.float64).max / 64,
    ],
    ids=["zero", "subnormal", "min_normal", "small", "unit", "large", "max_safe"],
)
def test_intensity_scaled_accuracy_and_preserved_error_mode(api: Any, scale: float) -> None:
    base = spatial_coordinates((1, 2, 3))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        coordinates = np.array([exact(v) * exact(scale) for v in base.flat], dtype=object).reshape(
            base.shape
        )
    images = synthesize(UNEQUAL_PHASES, coordinates)
    for mode in ("warn", "raise"):
        with warnings.catch_warnings(record=True) as caught, np.errstate(all=mode):
            warnings.simplefilter("always")
            before = np.geterr().copy()
            result = api(images, phases_rad=UNEQUAL_PHASES)
            assert np.geterr() == before
        assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
        assert_stored_fit(result, images, UNEQUAL_PHASES)


@pytest.mark.parametrize("case", ["large_dc", "unhalved_harmonic", "complex_magnitude"])
def test_safely_finite_coordinates_avoid_intermediate_overflow(api: Any, case: str) -> None:
    maximum = exact(np.finfo(np.float64).max)
    coordinates = np.zeros((5, 1, 1, 1), dtype=object)
    coordinates[:] = Decimal(0)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        if case == "large_dc":
            phases = UNEQUAL_PHASES
            coordinates[0, 0, 0, 0] = maximum * Decimal("0.95")
        elif case == "unhalved_harmonic":
            phases = np.array([1, 2, 3, 5, 7], dtype=np.float64) * (np.pi / 4)
            coordinates[1, 0, 0, 0] = maximum * Decimal("0.6")
        else:
            phases = np.array(
                [np.pi / 4 + d for d in (-0.25, 0, 0.25)]
                + [5 * np.pi / 4 + d for d in (-0.25, 0, 0.25)]
            )
            coordinates[1, 0, 0, 0] = maximum * Decimal("0.8")
            coordinates[2, 0, 0, 0] = maximum * Decimal("0.8")
    images = synthesize(phases, coordinates)
    assert np.isfinite(images).all()
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
        warnings.simplefilter("always")
        result = api(images, phases_rad=phases)
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.isfinite(output_coordinates(result)).all()
    if case != "complex_magnitude":
        assert_stored_fit(result, images, phases)
    else:
        # Magnitude exceeds max, each returned coordinate remains safe. This
        # phase set is outside cond<=10: acceptance, not a digit promise.
        reference, _ = stored_input_oracle(images, phases)
        assert reference[0][1] ** 2 + reference[0][2] ** 2 > maximum**2
        assert all(abs(value) < maximum for value in reference[0])


@pytest.mark.parametrize("coordinate", [1, 2, 3, 4])
def test_every_harmonic_coordinate_can_exceed_half_max(api: Any, coordinate: int) -> None:
    """V07: neither unhalved B/C nor scale restoration defines output range."""
    maximum = exact(np.finfo(np.float64).max)
    coordinates = np.full((5, 1, 1, 1), Decimal(0), dtype=object)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        coordinates[coordinate, 0, 0, 0] = maximum * Decimal("-0.6")
    if coordinate in (1, 2):
        phases = np.array([1, 2, 3, 5, 7], dtype=np.float64) * (np.pi / 4)
        if coordinate == 2:
            phases -= np.pi / 2
    else:
        phases = np.pi / 8 + np.arange(8) * (np.pi / 4)
    images = synthesize(phases, coordinates)
    assert np.isfinite(images).all()
    reference, _ = stored_input_oracle(images, phases)
    assert maximum / 2 < abs(reference[0][coordinate]) < maximum
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
        warnings.simplefilter("always")
        before = np.geterr().copy()
        result = api(images, phases_rad=phases)
        assert np.geterr() == before
    assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert_stored_fit(result, images, phases)


@pytest.mark.parametrize("coordinate", range(5))
def test_genuine_final_coordinate_range_rejection(api: Any, coordinate: int) -> None:
    maximum = exact(np.finfo(np.float64).max)
    coordinates = np.full((5, 1, 1, 1), Decimal(0), dtype=object)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        coordinates[coordinate, 0, 0, 0] = 4 * maximum
        offsets = np.array([-0.04, -0.02, 0, 0.02, 0.04])
        if coordinate == 0:
            phases = offsets
            coordinates[3, 0, 0, 0] = -2 * maximum
        elif coordinate == 1:
            phases = np.pi / 2 + offsets
        elif coordinate == 2:
            phases = offsets
        elif coordinate == 3:
            phases = np.pi / 4 + offsets
        else:
            phases = offsets
    images = synthesize(phases, coordinates)
    assert np.isfinite(images).all()
    reference, _ = stored_input_oracle(images, phases)
    assert abs(reference[0][coordinate]) > 2 * maximum
    assert condition_upper_bound(phases) < Decimal("1e12")
    with np.errstate(all="raise"):
        assert_rejected(api, images, phases, "unrepresentable_volume_phase_components")


def test_returned_outputs_are_snapshots_of_both_inputs(api: Any) -> None:
    phases = UNEQUAL_PHASES.copy()
    images = synthesize(phases, spatial_coordinates())
    result = api(images, phases_rad=phases)
    assert_stored_fit(result, images, phases)
    saved = output_coordinates(result).copy()
    images[...] = 0
    phases[...] = 0
    np.testing.assert_array_equal(output_coordinates(result), saved)
