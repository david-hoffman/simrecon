"""Blind NF02 public-contract tests; expectations never use SIMrecon output."""

from decimal import Decimal, localcontext
from typing import Any, cast

import numpy as np
import numpy.typing as npt
import pytest

import simrecon
from phase_separation_fixture import (
    ORACLE_PRECISION,
    analytic_phantom,
    stored_value_oracle,
)

Array = npt.NDArray[Any]


@pytest.fixture
def api() -> tuple[Any, Any, Any]:
    # Resolve at test execution so absent approved exports yield product-red
    # evidence for every case, instead of silently skipping/empty collection.
    names = ("separate_phases", "PhaseComponents", "SimreconError")
    separate, record, error = (getattr(simrecon, name) for name in names)
    return separate, record, error


def snapshot(images: Array) -> tuple[bytes, tuple[int, ...], str, tuple[int, ...], bool]:
    return images.tobytes(), images.shape, images.dtype.str, images.strides, images.flags.writeable


def tolerance(images: Array) -> Decimal:
    # Decimal conversion is exact, and neither 64*eps*M nor 8*u can underflow.
    with localcontext() as context:
        context.prec = ORACLE_PRECISION
        maximum = max(abs(Decimal.from_float(float(value))) for value in images.flat)
        return 64 * Decimal(2) ** -52 * maximum + 8 * Decimal(2) ** -1074


def assert_component_error(actual: Array, expected: Array, bound: Decimal) -> None:
    assert actual.shape == expected.shape
    assert np.all(np.isfinite(actual)), "nonfinite coefficient violates finite-output contract"
    with localcontext() as context:
        context.prec = ORACLE_PRECISION
        for index in np.ndindex(actual.shape):
            truth = expected[index]
            if not isinstance(truth, Decimal):
                truth = Decimal.from_float(float(truth))
            error = abs(Decimal.from_float(float(actual[index])) - truth)
            assert error <= bound, f"component error {error} exceeds {bound} at {index}"


def assert_result(api: tuple[Any, Any, Any], images: Array, offset: Any) -> Any:
    separate, record, _ = api
    before = snapshot(images)
    try:
        result = separate(images, phase_offset_rad=offset)
    finally:
        assert snapshot(images) == before, "input changed during separation"
    assert isinstance(result, record)
    assert isinstance(result.dc, np.ndarray)
    assert isinstance(result.c1, np.ndarray)
    assert result.dc.shape == result.c1.shape == images.shape[1:]
    assert result.dc.dtype == np.dtype(np.float64) and result.dc.dtype.isnative
    assert result.c1.dtype == np.dtype(np.complex128) and result.c1.dtype.isnative
    for output in (result.dc, result.c1):
        assert output.flags.c_contiguous and output.flags.owndata
        assert not np.shares_memory(output, images)
    assert not np.shares_memory(result.dc, result.c1)
    dc, real, imag = stored_value_oracle(images, float(offset))
    bound = tolerance(images)
    assert_component_error(result.dc, dc, bound)
    c1 = cast(npt.NDArray[np.complex128], result.c1)
    assert_component_error(c1.real, real, bound)
    assert_component_error(c1.imag, imag, bound)
    return result


def assert_rejected(api: tuple[Any, Any, Any], images: Any, offset: Any, code: str) -> None:
    separate, _, error_type = api
    before = snapshot(images) if isinstance(images, np.ndarray) else None
    try:
        with pytest.raises(error_type) as caught:
            separate(images, phase_offset_rad=offset)
    finally:
        if before is not None:
            assert snapshot(images) == before, "input changed during rejection"
    assert isinstance(caught.value, ValueError)
    error = cast(Any, caught.value)
    assert isinstance(error.code, str) and error.code == code
    assert isinstance(error.message, str)


def signed_images() -> Array:
    return np.array(
        [[[14, -3, 0], [1, 9, -12]], [[9, 5, -7], [2, -6, 4]], [[7, -8, 13], [-9, 0, 6]]],
        dtype=np.float64,
    )


@pytest.mark.parametrize("offset", [0.0, np.pi / 6, -0.71, np.pi, -np.pi])
def test_p01_sinusoid_sign_gain_offset_and_spatial_order(api: Any, offset: float) -> None:
    y, x = np.indices((2, 5), dtype=np.float64)
    amplitude = 3 + 2 * y - x
    cosine = 4 - x + y
    sine = 2 + 3 * x - 2 * y
    phases = offset + 2 * np.pi * np.arange(3) / 3
    images = (
        amplitude[None]
        + cosine[None] * np.cos(phases[:, None, None])
        + sine[None] * np.sin(phases[:, None, None])
    )
    result = assert_result(api, images, offset)
    # Analytic identity is a second sign/gain sanity check; stored oracle above
    # remains the precision gate after generation rounding.
    bound = tolerance(images) * Decimal("1.1")
    assert_component_error(result.dc, amplitude, bound)
    assert_component_error(result.c1.real, cosine / 2, bound)
    assert_component_error(result.c1.imag, -sine / 2, bound)


def test_p01_required_keyword_only_offset_preserves_python_binding_errors(api: Any) -> None:
    separate, _, _ = api
    images = signed_images()
    before = snapshot(images)
    with pytest.raises(TypeError):
        separate(images)
    with pytest.raises(TypeError):
        separate(images, 0.0)
    with pytest.raises(TypeError):
        separate(images, phase_offset_rad=0.0, unknown=True)
    assert snapshot(images) == before


@pytest.mark.parametrize("value", [0.0, -0.0, 7.25, -19.5])
@pytest.mark.parametrize("offset", [0.0, -0.83, np.pi])
def test_p02_constant_and_zero(api: Any, value: float, offset: float) -> None:
    images = np.full((3, 2, 4), value, dtype=np.float64)
    result = assert_result(api, images, offset)
    assert_component_error(result.dc, np.full((2, 4), value), tolerance(images))
    assert_component_error(result.c1.real, np.zeros((2, 4)), tolerance(images))
    assert_component_error(result.c1.imag, np.zeros((2, 4)), tolerance(images))


@pytest.mark.parametrize("dtype", ["u2", "f4", "f8"])
@pytest.mark.parametrize("endian", ["<", ">"])
@pytest.mark.parametrize("layout", ["contiguous", "strided", "reversed", "readonly"])
def test_p03_p04_p05_representation_stored_values_and_ownership(
    api: Any, dtype: str, endian: str, layout: str
) -> None:
    values = np.array(
        [
            [[65535, 32768, 1], [42001, 0, 65000]],
            [[32769, 65534, 3], [1001, 40000, 2]],
            [[0, 40003, 65533], [65535, 7, 50001]],
        ],
        dtype=np.float64,
    )
    if dtype != "u2":
        values = values * 0.37 - 10000.123456789
        values[0, 0, 0] = 16777217.25  # float32 quantization is intentional.
    images = values.astype(endian + dtype)
    if layout == "strided":
        backing = np.zeros((3, 4, 6), dtype=images.dtype)
        backing[:, ::2, ::2] = images
        images = backing[:, ::2, ::2]
    elif layout == "reversed":
        images = images[:, ::-1, ::-1]
    elif layout == "readonly":
        images.flags.writeable = False
    result = assert_result(api, images, -0.43)
    before = snapshot(images)
    original_c1 = result.c1.copy()
    result.dc[...] = -981.5
    assert snapshot(images) == before
    assert np.array_equal(result.c1, original_c1)
    original_dc = result.dc.copy()
    result.c1[...] = 17 - 13j
    assert snapshot(images) == before
    assert np.array_equal(result.dc, original_dc)


@pytest.mark.parametrize("shape", [(3, 1, 1), (3, 1, 7), (3, 5, 1)])
def test_p04_p08_singleton_spatial_axes_are_valid(api: Any, shape: tuple[int, ...]) -> None:
    assert_result(api, np.arange(np.prod(shape), dtype=np.float64).reshape(shape), 0.0)


class ArraySubclass(np.ndarray):
    """An array whose extra semantics must never be silently accepted."""


class Coercible:
    """An array-like object outside the plain-ndarray contract."""

    def __array__(self, *args: Any, **kwargs: Any) -> Array:
        """Refuse coercion so invalid-object handling stays observable."""
        raise AssertionError("outside-domain object must not be coerced")


@pytest.mark.parametrize(
    "images",
    [
        None,
        1,
        [[[1.0]]] * 3,
        (((1.0,),),) * 3,
        Coercible(),
        np.zeros((3, 1, 1)).view(ArraySubclass),
        np.ma.array(np.ones((3, 1, 1)), mask=False),
    ],
)
def test_p06_reject_nonplain_objects_without_coercion(api: Any, images: Any) -> None:
    assert_rejected(api, images, 0.0, "invalid_phase_images")


@pytest.mark.parametrize("dtype", ["i2", "i8", "u1", "u4", "bool", "c8", "c16", "O", "f2", "S3"])
def test_p07_reject_unsupported_dtype(api: Any, dtype: str) -> None:
    assert_rejected(api, np.zeros((3, 2, 3), dtype=dtype), 0.0, "invalid_phase_dtype")


@pytest.mark.parametrize(
    "shape",
    [
        (),
        (3,),
        (2, 3),
        (3, 1, 1, 1),
        (1, 2, 3),
        (2, 2, 3),
        (4, 2, 3),
        (0, 2, 3),
        (3, 0, 2),
        (3, 2, 0),
    ],
)
def test_p08_reject_shape(api: Any, shape: tuple[int, ...]) -> None:
    assert_rejected(api, np.zeros(shape, dtype=np.float64), 0.0, "invalid_phase_shape")


@pytest.mark.parametrize("dtype", ["<f4", ">f4", "<f8", ">f8"])
@pytest.mark.parametrize(
    "value,position", [(np.nan, (0, 0, 1)), (np.inf, (1, 1, 0)), (-np.inf, (2, 1, 2))]
)
def test_p09_reject_nonfinite_but_preserve_input(
    api: Any, dtype: str, value: float, position: tuple[int, ...]
) -> None:
    images = signed_images().astype(dtype)
    images[position] = value
    images = images[:, :, ::-1]
    images.flags.writeable = False
    assert_rejected(api, images, 0.0, "nonfinite_phase_images")


@pytest.mark.parametrize(
    "offset",
    [
        True,
        False,
        np.bool_(True),
        1j,
        0j,
        np.complex128(0),
        "0",
        None,
        np.array(0.0),
        np.array([0.0]),
        [0.0],
    ],
)
def test_p10_reject_unsupported_offset_scalar(api: Any, offset: Any) -> None:
    assert_rejected(api, signed_images(), offset, "invalid_phase_offset")


@pytest.mark.parametrize(
    "offset",
    [
        0,
        1,
        -1,
        0.0,
        -0.0,
        np.int8(-1),
        np.uint16(2),
        np.int64(1),
        np.float16(0.5),
        np.float32(-0.75),
        np.float64(0.91),
        np.longdouble("0.33"),
    ],
)
def test_p10_permitted_python_and_numpy_real_scalars(api: Any, offset: Any) -> None:
    assert_result(api, signed_images(), offset)


@pytest.mark.parametrize(
    "offset",
    [
        float("nan"),
        float("inf"),
        -float("inf"),
        np.float32("nan"),
        np.float64("inf"),
        np.longdouble("-inf"),
    ],
)
def test_p11_reject_nonfinite_real_offset(api: Any, offset: Any) -> None:
    assert_rejected(api, signed_images(), offset, "invalid_phase_offset")


@pytest.mark.parametrize(
    "offset",
    [
        np.nextafter(np.pi, np.inf),
        np.nextafter(-np.pi, -np.inf),
        4,
        -4,
        2 * np.pi,
        10**400,
        -(10**400),
    ],
)
def test_p12_reject_outside_principal_interval(api: Any, offset: Any) -> None:
    assert_rejected(api, signed_images(), offset, "invalid_phase_offset")


@pytest.mark.parametrize("offset", [np.pi, -np.pi, np.nextafter(np.pi, 0), np.nextafter(-np.pi, 0)])
def test_p12_principal_interval_endpoints_and_adjacent_inside(api: Any, offset: float) -> None:
    assert_result(api, signed_images(), offset)


@pytest.mark.parametrize("offset", [0.0, 0.37, -np.pi, np.pi])
def test_p13_near_float64_limit_no_intermediate_overflow(api: Any, offset: float) -> None:
    maximum = np.finfo(np.float64).max
    lower = np.nextafter(maximum, 0.0)
    images = np.array(
        [
            [[maximum, -maximum, maximum, maximum, lower, maximum]],
            [[maximum, -maximum, -maximum, maximum, maximum, -maximum]],
            [[maximum, -maximum, maximum, -maximum, lower, -maximum]],
        ],
        dtype=np.float64,
    )
    assert_result(api, images, offset)


@pytest.mark.parametrize("offset", [0.0, 0.61, -np.pi])
def test_p13_subnormal_and_mixed_scale_inputs(api: Any, offset: float) -> None:
    tiny = np.nextafter(0.0, 1.0)
    images = np.array(
        [
            [[tiny, 32 * tiny, -128 * tiny, 0]],
            [[tiny, -16 * tiny, 256 * tiny, tiny]],
            [[tiny, 64 * tiny, -64 * tiny, -tiny]],
        ],
        dtype=np.float64,
    )
    assert_result(api, images, offset)
    # Separate calls prevent the global maximum from hiding tiny-case errors.
    small_normal = np.finfo(np.float64).tiny
    assert_result(api, images / tiny * small_normal, offset)
    assert_result(api, np.array([[[1e300]], [[1e-300]], [[-1e300]]]), offset)


def test_p03_float32_range_and_subnormal_stored_values(api: Any) -> None:
    maximum = np.finfo(np.float32).max
    tiny = np.nextafter(np.float32(0), np.float32(1))
    assert_result(api, np.array([[[maximum]], [[-maximum]], [[maximum]]], dtype=np.float32), 0.31)
    assert_result(api, np.array([[[tiny]], [[-tiny]], [[3 * tiny]]], dtype=np.float32), -0.31)


def test_p14_independent_asymmetric_phantom_and_forward_resynthesis(api: Any) -> None:
    phantom = analytic_phantom()
    result = assert_result(api, phantom.images, phantom.phase_offset_rad)
    bound = tolerance(phantom.images)
    # Compare the persisted expected arrays, allowing their <=0.5-ulp rounding
    # in addition to the exact-oracle bound already checked by assert_result.
    assert_component_error(result.dc, phantom.expected_dc, bound * Decimal("1.01"))
    assert_component_error(result.c1.real, phantom.expected_c1.real, bound * Decimal("1.01"))
    assert_component_error(result.c1.imag, phantom.expected_c1.imag, bound * Decimal("1.01"))
    assert_component_error(phantom.expected_dc, phantom.analytic_dc, bound)
    assert_component_error(phantom.expected_c1.real, phantom.analytic_c1.real, bound)
    assert_component_error(phantom.expected_c1.imag, phantom.analytic_c1.imag, bound)
    assert np.any(phantom.expected_c1.real < 0) and np.any(phantom.expected_c1.real > 0)
    assert np.any(phantom.expected_c1.imag < 0) and np.any(phantom.expected_c1.imag > 0)
    phases = phantom.phase_offset_rad + 2 * np.pi * np.arange(3) / 3
    # Component error propagates through two signed quadratures plus dc:
    # |delta I| <= (1+2*sqrt(2))*bound, plus synthesis float64 roundoff.
    for phase in range(3):
        recovered = result.dc + 2 * np.real(result.c1 * np.exp(1j * phases[phase]))
        assert_component_error(recovered, phantom.images[phase], 5 * bound)
    repeated = analytic_phantom()
    assert phantom.parameters() == repeated.parameters()
    assert phantom.array_identities() == repeated.array_identities()
