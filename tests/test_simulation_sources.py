"""Blind public-contract tests for total-normalized finite midpoint spheres.

This suite asserts the finite model, not continuous sphere-cell integration.
Stored mass need not equal exact input brightness.  Source refinement changes
the midpoint model; it supplies no optical/pixel or continuum error bound.
"""

import importlib
import random
import warnings
from collections.abc import Callable
from fractions import Fraction
from itertools import product
from typing import Any

import numpy as np
import pytest

from simulation_sources_fixture import (
    ANISOTROPIC5,
    CENTER1,
    CROSS7,
    OFF_GRID2,
    ONLY_SITE,
    distance_squared,
    exact,
    expected_weights,
    verify_declared_sites,
)

INVALID = "invalid_simulation_source"
RANGE = "simulation_source_range"
DEFAULTS: dict[str, Any] = {
    "detector_shape_zyx": (1, 1, 1),
    "detector_spacing_um_zyx": (2.0, 2.0, 2.0),
    "source_refinement_zyx": (1, 1, 1),
}


@pytest.fixture
def make_sources() -> Callable[..., Any]:
    # The real production import is deliberately required.  Missing runtime is
    # unavailable execution, never a fake callable, skip, or manufactured red.
    return importlib.import_module("scripts.simulation_sources").make_sources


def call(make_sources: Callable[..., Any], catalogue: Any, **changes: Any) -> Any:
    return make_sources(catalogue, **(DEFAULTS | changes))


def assert_array(actual: Any, expected: Any) -> None:
    assert type(actual) is np.ndarray
    assert actual.dtype == np.dtype(np.float64)
    assert actual.dtype.isnative
    assert actual.shape == expected.shape
    assert actual.flags.c_contiguous
    assert actual.flags.writeable
    assert np.isfinite(actual).all()
    assert (actual >= 0).all()
    np.testing.assert_array_equal(actual, expected)
    # Equality alone would accept negative zero; the contract initializes +0.
    assert not np.signbit(actual[actual == 0]).any()


def assert_code(operation: Callable[[], Any], code: str) -> Exception:
    with pytest.raises(Exception) as captured:
        operation()
    error = captured.value
    assert any(base.__name__ == "SimreconError" for base in type(error).__mro__)
    assert getattr(error, "code", None) == code
    return error


def sphere(brightness: float = 1.0) -> Any:
    return np.array([[1.0, 1.0, 1.0, 1.0, brightness]])


def test_oracle_closed_ties_and_strict_neighbors() -> None:
    """S02: certify all 27 sites without consulting production."""
    for radius, sites in [
        (1.0, CROSS7),
        (float(np.nextafter(1.0, 0.0)), CENTER1),
        (float(np.nextafter(1.0, 2.0)), CROSS7),
    ]:
        verify_declared_sites(
            (3, 3, 3),
            sites,
            center=(1.5, 1.5, 1.5),
            radius=radius,
            spacing=(1.0, 1.0, 1.0),
            refinement=(1, 1, 1),
        )
    assert (
        distance_squared(
            (0, 1, 1),
            center=(1.5, 1.5, 1.5),
            spacing=(1.0, 1.0, 1.0),
            refinement=(1, 1, 1),
        )
        == 1
    )
    assert (0, 0, 1) not in CROSS7  # A cube would falsely include this site.


def test_oracle_anisotropic_and_off_grid_sets() -> None:
    for center, radius, sites in [
        ((1.5, 1.5, 2.25), 1.0, ANISOTROPIC5),
        ((1.25, 1.5, 2.25), 0.75, OFF_GRID2),
    ]:
        verify_declared_sites(
            (4, 3, 4),
            sites,
            center=center,
            radius=radius,
            spacing=(2.0, 1.0, 3.0),
            refinement=(2, 1, 2),
        )


def test_oracle_multiaxis_tie_and_lost_square_distinction() -> None:
    """Exact sums distinguish a 3-4-5 tie and a sub-ulp squared increment."""
    verify_declared_sites(
        (2, 2, 3),
        frozenset({(0, 0, 1), (0, 1, 1)}),
        center=(0.875, 1.0, 1.5),
        radius=0.625,
        spacing=(1.0, 1.0, 1.0),
        refinement=(1, 1, 1),
    )
    assert Fraction(3, 8) ** 2 + Fraction(1, 2) ** 2 == Fraction(5, 8) ** 2
    center_y = float(np.nextafter(1.5, 2.0))
    verify_declared_sites(
        (3, 3, 3),
        frozenset({(1, 1, 1), (1, 2, 1)}),
        center=(1.5, center_y, 1.5),
        radius=1.0,
        spacing=(1.0, 1.0, 1.0),
        refinement=(1, 1, 1),
    )
    assert 1 + (exact(center_y) - Fraction(3, 2)) ** 2 > 1
    assert 1.0 + (center_y - 1.5) ** 2 == 1.0


def test_oracle_rounding_controls_and_nonconservation() -> None:
    weight = float(Fraction(1, 7))
    assert weight.hex() == "0x1.2492492492492p-3"
    expected = expected_weights((3, 3, 3), [(1.0, CROSS7)])
    assert sum(map(exact, map(float, expected.flat))) == Fraction(1) - Fraction(1, 2**54)
    large = float(2**53)
    ordered = expected_weights((1, 1, 1), [(large, ONLY_SITE), (1.0, ONLY_SITE), (1.0, ONLY_SITE)])
    reverse = expected_weights((1, 1, 1), [(1.0, ONLY_SITE), (1.0, ONLY_SITE), (large, ONLY_SITE)])
    assert ordered.item() == large
    assert reverse.item() == large + 2
    assert exact(ordered.item()) != exact(large) + 2
    tiny = float.fromhex("0x0.0000000000001p-1022")
    assert float(exact(tiny) / 2) == 0  # Exact halfway tie rounds to even zero.
    assert float(3 * exact(tiny) / 2) == 2 * tiny


@pytest.mark.parametrize("zero_rows", [False, True])
def test_empty_and_zero_rows(make_sources: Callable[..., Any], zero_rows: bool) -> None:
    catalogue = np.array([[0.25, 0.25, 0.25, 0.125, -0.0]]) if zero_rows else np.empty((0, 5))
    # The zero row has no occupied site. It must still succeed.
    result = call(make_sources, catalogue)
    assert_array(result, np.zeros((1, 1, 1)))


@pytest.mark.parametrize(
    "dtype", [np.int16, np.uint64, np.float16, np.float32, np.float64, np.longdouble, ">f8", ">i4"]
)
def test_permitted_dtypes(make_sources: Callable[..., Any], dtype: Any) -> None:
    catalogue = np.array([[1, 1, 1, 1, 7]], dtype=dtype)
    original = catalogue.tobytes()
    result = call(make_sources, catalogue)
    assert_array(result, np.full((1, 1, 1), 7.0))
    assert catalogue.tobytes() == original
    assert not np.shares_memory(result, catalogue)


@pytest.mark.parametrize("layout", ["fortran", "strided", "reversed", "readonly"])
def test_permitted_layouts(make_sources: Callable[..., Any], layout: str) -> None:
    rows = np.array([[1, 1, 1, 1, 2], [1, 1, 1, 1, 3]], dtype=np.float64)
    if layout == "fortran":
        rows = np.asfortranarray(rows)
    elif layout == "strided":
        backing = np.zeros((4, 10))
        backing[::2, ::2] = rows
        rows = backing[::2, ::2]
    elif layout == "reversed":
        rows = rows[::-1]
    else:
        rows.flags.writeable = False
    before = rows.tobytes()
    metadata = (rows.shape, rows.strides, rows.dtype, rows.flags.writeable)
    result = call(make_sources, rows)
    assert_array(result, np.full((1, 1, 1), 5.0))
    assert rows.tobytes() == before
    assert (rows.shape, rows.strides, rows.dtype, rows.flags.writeable) == metadata
    assert not np.shares_memory(result, rows)
    result[0, 0, 0] = 41
    assert rows.tobytes() == before


def test_integer_conversion_rounding_is_permitted(make_sources: Callable[..., Any]) -> None:
    catalogue = np.array([[1, 1, 1, 1, 2**53 + 1]], dtype=np.uint64)
    assert_array(call(make_sources, catalogue), np.full((1, 1, 1), float(2**53)))


@pytest.mark.parametrize(
    "radius,sites",
    [
        (1.0, CROSS7),
        (float(np.nextafter(1.0, 0.0)), CENTER1),
        (float(np.nextafter(1.0, 2.0)), CROSS7),
    ],
)
def test_closed_boundary_and_strict_neighbors(
    make_sources: Callable[..., Any], radius: float, sites: Any
) -> None:
    result = call(
        make_sources,
        np.array([[1.5, 1.5, 1.5, radius, 1.0]]),
        detector_shape_zyx=(3, 3, 3),
        detector_spacing_um_zyx=(1.0, 1.0, 1.0),
    )
    assert_array(result, expected_weights((3, 3, 3), [(1.0, sites)]))


@pytest.mark.parametrize(
    "center,radius,sites",
    [((1.5, 1.5, 2.25), 1.0, ANISOTROPIC5), ((1.25, 1.5, 2.25), 0.75, OFF_GRID2)],
)
def test_anisotropic_physical_coordinates(
    make_sources: Callable[..., Any], center: Any, radius: float, sites: Any
) -> None:
    result = call(
        make_sources,
        np.array([[*center, radius, 11.0]]),
        detector_shape_zyx=(2, 3, 2),
        detector_spacing_um_zyx=(2.0, 1.0, 3.0),
        source_refinement_zyx=(2, 1, 2),
    )
    assert_array(result, expected_weights((4, 3, 4), [(11.0, sites)]))


def test_half_cell_and_independent_refinements(make_sources: Callable[..., Any]) -> None:
    sites = frozenset(product(range(1), range(2), range(4)))
    verify_declared_sites(
        (1, 2, 4),
        sites,
        center=(1.0, 1.0, 1.0),
        radius=1.0,
        spacing=(2.0, 2.0, 2.0),
        refinement=(1, 2, 4),
    )
    result = call(make_sources, sphere(8.0), source_refinement_zyx=(1, 2, 4))
    assert_array(result, np.ones((1, 2, 4)))


def test_nonbinary_refinement_and_thirds(make_sources: Callable[..., Any]) -> None:
    sites = frozenset({(0, 0, 0), (1, 0, 0), (2, 0, 0)})
    verify_declared_sites(
        (3, 1, 1),
        sites,
        center=(1.0, 1.0, 1.0),
        radius=1.0,
        spacing=(2.0, 2.0, 2.0),
        refinement=(3, 1, 1),
    )
    result = call(make_sources, sphere(), source_refinement_zyx=(3, 1, 1))
    assert_array(result, expected_weights((3, 1, 1), [(1.0, sites)]))


def test_exact_multiaxis_boundary(make_sources: Callable[..., Any]) -> None:
    sites = frozenset({(0, 0, 1), (0, 1, 1)})
    rows = np.array([[0.875, 1.0, 1.5, 0.625, 13.0]])
    result = call(
        make_sources,
        rows,
        detector_shape_zyx=(2, 2, 3),
        detector_spacing_um_zyx=(1.0, 1.0, 1.0),
    )
    assert_array(result, expected_weights((2, 2, 3), [(13.0, sites)]))


def test_exact_membership_preserves_tiny_squared_difference(
    make_sources: Callable[..., Any],
) -> None:
    rows = np.array([[1.5, float(np.nextafter(1.5, 2.0)), 1.5, 1.0, 2.0]])
    result = call(
        make_sources,
        rows,
        detector_shape_zyx=(3, 3, 3),
        detector_spacing_um_zyx=(1.0, 1.0, 1.0),
    )
    assert_array(result, expected_weights((3, 3, 3), [(2.0, frozenset({(1, 1, 1), (1, 2, 1)}))]))


@pytest.mark.parametrize(
    "brightnesses",
    [(2.0, 3.0, 7.0), (float(2**53), 1.0, 1.0), (1.0, 1.0, float(2**53)), (float(2**53 + 2), 1.0)],
)
def test_duplicate_rows_and_prescribed_addition_order(
    make_sources: Callable[..., Any], brightnesses: tuple[float, ...]
) -> None:
    rows = np.concatenate([sphere(value) for value in brightnesses])
    expected = expected_weights((1, 1, 1), [(value, ONLY_SITE) for value in brightnesses])
    assert_array(call(make_sources, rows), expected)


def test_partial_overlap_is_additive(make_sources: Callable[..., Any]) -> None:
    # Shifted radius-one crosses overlap at exactly two sites.
    first = frozenset({(0, 1, 1), (1, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1), (1, 1, 0), (1, 1, 2)})
    second = frozenset(
        {(1, 1, 1), (2, 1, 1), (3, 1, 1), (2, 0, 1), (2, 2, 1), (2, 1, 0), (2, 1, 2)}
    )
    for center, sites in [((1.5, 1.5, 1.5), first), ((2.5, 1.5, 1.5), second)]:
        verify_declared_sites(
            (4, 3, 3),
            sites,
            center=center,
            radius=1.0,
            spacing=(1.0, 1.0, 1.0),
            refinement=(1, 1, 1),
        )
    rows = np.array([[1.5, 1.5, 1.5, 1.0, 1.0], [2.5, 1.5, 1.5, 1.0, 2.0]])
    result = call(
        make_sources, rows, detector_shape_zyx=(4, 3, 3), detector_spacing_um_zyx=(1.0, 1.0, 1.0)
    )
    assert_array(result, expected_weights((4, 3, 3), [(1.0, first), (2.0, second)]))


@pytest.mark.parametrize("radius", [0.25, float(np.nextafter(0.25, 0.0))])
def test_near_edge_and_face_tangency(make_sources: Callable[..., Any], radius: float) -> None:
    # The radius supplies a strict neighbor that survives float normalization.
    rows = np.array([[0.25, 0.25, 0.25, radius, 9.0]])
    result = call(make_sources, rows, detector_spacing_um_zyx=(0.5, 0.5, 0.5))
    assert_array(result, np.full((1, 1, 1), 9.0))


def test_positive_empty_membership_is_range(make_sources: Callable[..., Any]) -> None:
    rows = np.array([[0.25, 0.25, 0.25, 0.125, 1.0]])
    assert_code(lambda: call(make_sources, rows), RANGE)


@pytest.mark.parametrize(
    "brightness,raises",
    [
        (float.fromhex("0x0.0000000000001p-1022"), True),
        (float.fromhex("0x0.0000000000003p-1022"), False),
    ],
)
def test_quotient_to_zero_and_nonzero_subnormal(
    make_sources: Callable[..., Any], brightness: float, raises: bool
) -> None:
    rows = np.array([[1.25, 1.5, 2.25, 0.75, brightness]])
    kwargs = dict(
        detector_shape_zyx=(2, 3, 2),
        detector_spacing_um_zyx=(2.0, 1.0, 3.0),
        source_refinement_zyx=(2, 1, 2),
    )
    if raises:
        assert_code(lambda: call(make_sources, rows, **kwargs), RANGE)
    else:
        assert_array(
            call(make_sources, rows, **kwargs),
            expected_weights((4, 3, 4), [(brightness, OFF_GRID2)]),
        )


def test_large_finite_weights_and_overlap_overflow(make_sources: Callable[..., Any]) -> None:
    largest = float(np.finfo(np.float64).max)
    assert_array(call(make_sources, sphere(largest)), np.full((1, 1, 1), largest))
    assert_array(
        call(make_sources, np.concatenate([sphere(largest / 2), sphere(largest / 2)])),
        np.full((1, 1, 1), largest),
    )
    rows = np.concatenate([sphere(largest), sphere(largest)])
    before = rows.tobytes()
    assert_code(lambda: call(make_sources, rows), RANGE)
    assert rows.tobytes() == before


@pytest.mark.parametrize(
    "scale", [float(2**1023), float.fromhex("0x1p-1022"), float.fromhex("0x0.0000000000001p-1022")]
)
def test_extreme_exact_geometry_with_tiny_output(
    make_sources: Callable[..., Any], scale: float
) -> None:
    # Eight sites at (D/2 or 3D/2)^3 around c=(D,D,D), radius D.
    # Each distance^2 = 3D^2/4 < D^2; exact box side 2D. For minsubnormal
    # D the half sites aren't float64 numbers. For huge D box and squares
    # overflow float64. Neither prevents this eight-element output.
    assert Fraction(3, 4) < 1
    rows = np.array([[scale, scale, scale, scale, 8.0]])
    result = call(
        make_sources,
        rows,
        detector_shape_zyx=(2, 2, 2),
        detector_spacing_um_zyx=(scale, scale, scale),
    )
    assert_array(result, np.ones((2, 2, 2)))


def test_exact_box_product_rejects_rounded_tangent(make_sources: Callable[..., Any]) -> None:
    step = 1.0 / 3.0
    assert 3 * exact(step) < 1
    assert 3 * step == 1.0
    assert_code(
        lambda: call(
            make_sources,
            np.array([[0.5, 0.5, 0.5, 0.5, 0.0]]),
            detector_shape_zyx=(3, 3, 3),
            detector_spacing_um_zyx=(step, step, step),
        ),
        INVALID,
    )


@pytest.mark.parametrize(
    "shape,refinement",
    [
        ((2**100, 1, 1), (1, 1, 1)),
        ((1, 1, 1), (2**100, 1, 1)),
        ((2**32, 2**32, 1), (1, 1, 1)),
        ((2**61, 1, 1), (1, 1, 1)),
    ],
)
def test_unrepresentable_shape_or_storage(
    make_sources: Callable[..., Any], shape: Any, refinement: Any
) -> None:
    # Every request exceeds signed 64-bit ndarray dimension/storage addressing.
    # No merely expensive representable allocation is requested.
    assert_code(
        lambda: call(
            make_sources,
            np.empty((0, 5)),
            detector_shape_zyx=shape,
            source_refinement_zyx=refinement,
        ),
        RANGE,
    )


class IntegerSubclass(int):
    """Non-plain integer rejected by the public count and spacing domains."""


class FloatSubclass(float):
    """Non-plain float rejected by the public spacing domain."""


class ArraySubclass(np.ndarray):
    """Non-plain ndarray rejected by the public catalogue domain."""


@pytest.mark.parametrize(
    "catalogue",
    [
        [],
        [[1, 1, 1, 1, 1]],
        np.zeros(5),
        np.zeros((1, 4)),
        np.zeros((0, 6)),
        np.zeros((1, 1, 5)),
        np.ones((1, 5), dtype=bool),
        np.ones((1, 5), dtype=complex),
        np.ones((1, 5), dtype=object),
        np.full((1, 5), "1"),
        np.zeros((1, 5), dtype="datetime64[D]"),
        np.ones((1, 5)).view(ArraySubclass),
        np.ma.array([[1, 1, 1, 1, 1]], mask=False),
    ],
)
def test_invalid_catalogue_forms(make_sources: Callable[..., Any], catalogue: Any) -> None:
    assert_code(lambda: call(make_sources, catalogue), INVALID)


@pytest.mark.parametrize("column", range(5))
@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_original_nonfinite_values(
    make_sources: Callable[..., Any], column: int, value: float
) -> None:
    rows = sphere()
    rows[0, column] = value
    before = rows.tobytes()
    assert_code(lambda: call(make_sources, rows), INVALID)
    assert rows.tobytes() == before


@pytest.mark.parametrize("keyword", ["detector_shape_zyx", "source_refinement_zyx"])
@pytest.mark.parametrize(
    "bad",
    [
        (1, 1),
        (1, 1, 1, 1),
        [1, 1, 1],
        (True, 1, 1),
        (np.int64(1), 1, 1),
        (IntegerSubclass(1), 1, 1),
        (1.0, 1, 1),
        (0, 1, 1),
        (-1, 1, 1),
        None,
    ],
)
def test_invalid_count_domains(make_sources: Callable[..., Any], keyword: str, bad: Any) -> None:
    assert_code(lambda: call(make_sources, sphere(), **{keyword: bad}), INVALID)


@pytest.mark.parametrize(
    "bad",
    [
        (1, 1),
        (1, 1, 1, 1),
        [2, 2, 2],
        (True, 2, 2),
        (np.float64(2), 2, 2),
        (np.int64(2), 2, 2),
        (FloatSubclass(2), 2, 2),
        (IntegerSubclass(2), 2, 2),
        (0.0, 2, 2),
        (-0.0, 2, 2),
        (-1.0, 2, 2),
        (np.nan, 2, 2),
        (np.inf, 2, 2),
        (2**2000, 2, 2),
        None,
    ],
)
def test_invalid_spacing_domains(make_sources: Callable[..., Any], bad: Any) -> None:
    assert_code(lambda: call(make_sources, sphere(), detector_spacing_um_zyx=bad), INVALID)


def test_plain_integer_spacing_is_valid(make_sources: Callable[..., Any]) -> None:
    assert_array(
        call(make_sources, sphere(), detector_spacing_um_zyx=(2, 2, 2)), np.ones((1, 1, 1))
    )


@pytest.mark.parametrize(
    "radius,brightness",
    [(0.0, 1.0), (-0.0, 1.0), (-1.0, 1.0), (0.0, 0.0), (-1.0, 0.0), (1.0, -1.0)],
)
def test_invalid_radius_or_brightness(
    make_sources: Callable[..., Any], radius: float, brightness: float
) -> None:
    rows = np.array([[1.0, 1.0, 1.0, radius, brightness]])
    assert_code(lambda: call(make_sources, rows), INVALID)


@pytest.mark.parametrize("axis", range(3))
@pytest.mark.parametrize(
    "center", [float(np.nextafter(1.0, 0.0)), float(np.nextafter(1.0, 2.0)), -2.0, 4.0]
)
@pytest.mark.parametrize("brightness", [0.0, 1.0])
def test_exterior_sphere_rejected_without_input_changes(
    make_sources: Callable[..., Any], axis: int, center: float, brightness: float
) -> None:
    rows = sphere(brightness)
    rows[0, axis] = center
    before = rows.tobytes()
    assert_code(lambda: call(make_sources, rows), INVALID)
    assert rows.tobytes() == before


def test_all_rows_are_validated_even_after_zero(make_sources: Callable[..., Any]) -> None:
    rows = np.concatenate([sphere(0.0), sphere(0.0)])
    rows[1, 3] = 0
    assert_code(lambda: call(make_sources, rows), INVALID)


def test_native_wider_real_normalization_if_available(make_sources: Callable[..., Any]) -> None:
    # Platform conditional execution, never a skip or fabricated conversion
    # failure. On equal-range native formats only permitted acceptance is tested.
    rows = np.array([[1, 1, 1, 1, 1]], dtype=np.longdouble)
    assert_array(call(make_sources, rows), np.ones((1, 1, 1)))
    if np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp:
        rows[0, 4] = np.finfo(np.longdouble).max
        assert np.isfinite(rows[0, 4])
        assert_code(lambda: call(make_sources, rows), INVALID)


def test_ordinary_argument_binding(make_sources: Callable[..., Any]) -> None:
    with pytest.raises(TypeError):
        make_sources()
    for missing in DEFAULTS:
        arguments = {key: value for key, value in DEFAULTS.items() if key != missing}
        with pytest.raises(TypeError):
            make_sources(sphere(), **arguments)
    with pytest.raises(TypeError):
        make_sources(sphere(), **DEFAULTS, unknown=True)
    with pytest.raises(TypeError):
        make_sources(sphere(), (1, 1, 1), (2, 2, 2), (1, 1, 1))


@pytest.mark.parametrize(
    "case",
    [
        "success",
        "underflow",
        "subnormal",
        "overflow",
        "invalid",
        "normalization",
        "large_geometry",
        "tiny_geometry",
    ],
)
def test_numpy_policy_and_expected_arithmetic_warnings(
    make_sources: Callable[..., Any], case: str
) -> None:
    rows = sphere()
    kwargs: dict[str, Any] = {}
    code = None
    if case in {"underflow", "subnormal"}:
        brightness = float.fromhex("0x0.0000000000001p-1022") * (1 if case == "underflow" else 3)
        rows = np.array([[1.25, 1.5, 2.25, 0.75, brightness]])
        kwargs = dict(
            detector_shape_zyx=(2, 3, 2),
            detector_spacing_um_zyx=(2.0, 1.0, 3.0),
            source_refinement_zyx=(2, 1, 2),
        )
        code = RANGE if case == "underflow" else None
    elif case == "overflow":
        rows = np.concatenate([sphere(float(np.finfo(np.float64).max))] * 2)
        code = RANGE
    elif case == "invalid":
        rows[0, 3] = -1
        code = INVALID
    elif case == "normalization":
        kwargs = dict(detector_spacing_um_zyx=(2**2000, 2, 2))
        code = INVALID
    elif case in {"large_geometry", "tiny_geometry"}:
        scale = (
            float(2**1023) if case == "large_geometry" else float.fromhex("0x0.0000000000001p-1022")
        )
        rows = np.array([[scale, scale, scale, scale, 8.0]])
        kwargs = dict(detector_shape_zyx=(2, 2, 2), detector_spacing_um_zyx=(scale, scale, scale))
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        before = np.geterr().copy()
        if code:
            assert_code(lambda: call(make_sources, rows, **kwargs), code)
        else:
            result = call(make_sources, rows, **kwargs)
            assert np.isfinite(result).all()
        assert np.geterr() == before
    assert not [item for item in seen if issubclass(item.category, RuntimeWarning)]


@pytest.mark.parametrize(
    "fault",
    [
        MemoryError("source allocation sentinel"),
        ValueError("unrelated numerical sentinel"),
        RuntimeError("unrelated dependency sentinel"),
    ],
)
def test_public_allocation_faults_propagate_if_used(
    make_sources: Callable[..., Any], monkeypatch: Any, fault: Exception
) -> None:
    # Optional stimulus at the public NumPy boundary. An alternate backend may
    # avoid np.zeros entirely; then the ordinary exact result must still pass.
    original = np.zeros
    called = False

    def fail(*args: Any, **kwargs: Any) -> Any:
        nonlocal called
        called = True
        raise fault

    observed = None
    result = None
    with monkeypatch.context() as context:
        context.setattr(np, "zeros", fail)
        try:
            result = call(make_sources, sphere())
        except Exception as error:
            observed = error
    assert np.zeros is original
    if called:
        assert observed is fault
    else:
        assert observed is None
        assert_array(result, np.ones((1, 1, 1)))


def test_unrelated_public_dependency_warning_remains_visible(
    make_sources: Callable[..., Any], monkeypatch: Any
) -> None:
    original = np.zeros
    called = False

    def warn_then_allocate(*args: Any, **kwargs: Any) -> Any:
        nonlocal called
        called = True
        warnings.warn("unrelated source dependency warning", UserWarning, stacklevel=2)
        return original(*args, **kwargs)

    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        with monkeypatch.context() as context:
            context.setattr(np, "zeros", warn_then_allocate)
            result = call(make_sources, sphere())
    assert_array(result, np.ones((1, 1, 1)))
    if called:
        assert any(
            item.category is UserWarning
            and str(item.message) == "unrelated source dependency warning"
            for item in seen
        )


def test_repeatability_independence_and_global_rng_state(make_sources: Callable[..., Any]) -> None:
    rows = sphere(7.0)
    before = rows.tobytes()
    numpy_state = np.random.get_state()
    python_state = random.getstate()
    first = call(make_sources, rows)
    second = call(make_sources, rows)
    after_numpy = np.random.get_state()
    assert numpy_state[0] == after_numpy[0]
    np.testing.assert_array_equal(numpy_state[1], after_numpy[1])
    assert numpy_state[2:] == after_numpy[2:]
    assert random.getstate() == python_state
    assert rows.tobytes() == before
    assert_array(first, np.full((1, 1, 1), 7.0))
    assert_array(second, first)
    assert not np.shares_memory(first, second)
    first[0, 0, 0] = 0
    assert second.item() == 7.0
