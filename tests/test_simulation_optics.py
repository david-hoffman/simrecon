"""NS02 blind A: real public caller, analytic controls and explicit finite sums."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable
from decimal import Decimal, localcontext
from fractions import Fraction
from importlib import import_module
from typing import Any, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from simrecon import SimreconError
from simulation_optics_fixture import (
    Interval,
    Reference,
    Source,
    compare_reference,
    decimal_pi,
    direct_factors,
    exact,
    finite_images,
    huge_geometry_reference,
    on_axis_reference,
    pi_interval,
    sin_cos,
)

# Deliberate real import at collection: missing public module must fail honestly.
expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


def inputs() -> dict[str, Any]:
    return {
        "source_e": np.array([[[7.0]]]),
        "detector_spacing_um_zyx": (0.7, 0.3, 0.4),
        "source_refinement_zyx": (1, 1, 1),
        "carriers_yx_per_um": np.array([[0.0, 0.0]]),
        "phases_rad": np.array([[0.0]]),
        "beam_amplitudes": (1.0, 0.0, 0.0),
        "excitation_um": 0.5,
        "emission_um": 0.6,
        "refractive_index": 1.25,
        "detection_na": 0.8,
        "pupil_order": 2,
        "pixel_subsamples_yx": (1, 1),
    }


def snapshot(arguments: dict[str, Any]) -> list[tuple[Any, ...]]:
    return [
        (value, value.tobytes(), value.dtype, value.shape, value.strides, value.flags.writeable)
        for value in arguments.values()
        if isinstance(value, np.ndarray)
    ]


def assert_preserved(before: list[tuple[Any, ...]]) -> None:
    for value, contents, dtype, shape, strides, writable in before:
        assert value.tobytes() == contents
        assert value.dtype == dtype
        assert value.shape == shape
        assert value.strides == strides
        assert value.flags.writeable == writable


def call(arguments: dict[str, Any]) -> NDArray[np.float64]:
    before = snapshot(arguments)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            result = expected_images(**arguments)
        finally:
            assert np.geterr() == settings
            assert_preserved(before)
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
    assert type(result) is np.ndarray
    assert result.dtype == np.dtype("float64") and result.dtype.isnative
    assert result.flags.c_contiguous and result.flags.writeable
    assert np.isfinite(result).all()
    assert (result >= 0).all()
    for value in arguments.values():
        if isinstance(value, np.ndarray):
            assert not np.shares_memory(result, value)
    return result


def assert_finite_target(
    actual: NDArray[np.float64],
    reference: Reference,
    *,
    subtract: tuple[NDArray[np.float64], ...] = (),
    multiplier: int = 1,
) -> None:
    assert actual.shape == reference.shape
    assert all(value.shape == actual.shape for value in subtract)
    # Returned arrays are observations only. Subtraction is exact rational
    # arithmetic for the supplemental three-call superposition relation.
    observations = tuple(
        exact(float(value)) - sum((exact(float(a.flat[i])) for a in subtract), Fraction(0))
        for i, value in enumerate(actual.flat)
    )
    compare_reference(observations, reference, multiplier=multiplier)


def assert_scaled_scalar_target(
    actual: NDArray[np.float64],
    target: Decimal,
    peak: Decimal,
    *,
    unit: float,
    uncertainty: Decimal = Decimal(0),
) -> None:
    """Compare in exact input units, retaining a conservative oracle error."""
    assert actual.shape == (1, 1, 1, 1, 1)
    with localcontext() as context:
        context.prec = 100
        observed = Decimal.from_float(float(actual.item())) / Decimal.from_float(unit)
        assert abs(observed - target) + uncertainty <= Decimal("1e-5") * peak


@pytest.mark.parametrize("dz,order", [(0.01, 1), (3.7, 2), (0.6, 3), (0.8, 7)])
def test_zero_and_on_axis_peak_have_electron_area_units(dz: float, order: int) -> None:
    args = inputs()
    args.update(detector_spacing_um_zyx=(dz, 0.3, 0.4), pupil_order=order)
    reference = on_axis_reference((1, 1, 1, 1, 1), exact(7), exact(0.3) * exact(0.4))
    assert_finite_target(call(args), reference)
    args["source_e"] = np.zeros((2, 2, 3))
    args["phases_rad"] = np.array([[0.0, math.pi, -31.0]])
    zero = call(args)
    assert zero.shape == (1, 3, 2, 2, 3)
    assert np.count_nonzero(zero) == 0


@pytest.mark.parametrize(
    "beams",
    [
        (4.0, 2.0, 1.0),
        (0.0, 2.0, 1.0),
        (0.0, 0.0, 3.0),
        (0.0, 3.0, 0.0),
        (0.0, 1.0, 1.0),
        (4.0, 2.0, 2.0),
    ],
)
def test_direct_squared_field_phases_and_amplitude_normalization(
    beams: tuple[float, float, float],
) -> None:
    args = inputs()
    phases = (0.0, math.pi / 2, math.pi, -math.pi / 2, 2 * math.pi, 0.0)
    args.update(beam_amplitudes=beams, phases_rad=np.array([phases]))
    # At q=d=0: Re(E)=a0+(plus+minus)cos(phi), Im(E)=(plus-minus)sin(phi).
    reference = on_axis_reference(
        (1, len(phases), 1, 1, 1),
        exact(7),
        exact(0.3) * exact(0.4),
        factors=direct_factors(phases, beams),
    )
    assert_finite_target(call(args), reference)
    args["beam_amplitudes"] = tuple(11 * a for a in beams)
    assert_finite_target(call(args), reference)


def test_unequal_sides_resolve_source_minus_focus_sign() -> None:
    args = inputs()
    # n/lambda_ex=1 and |q|=sqrt(7)/4 => kappa=1/4 cycles/um.
    # Source z=1.5; focuses 0.5,1.5,2.5 => d=+1,0,-1 um.
    q = math.sqrt(7) / 4
    phase = math.pi / 2 - 2 * math.pi * q * 0.15
    args.update(
        source_e=np.array([[[0.0]], [[7.0]], [[0.0]]]),
        source_refinement_zyx=(1, 1, 1),
        detector_spacing_um_zyx=(1.0, 0.3, 0.4),
        excitation_um=1.25,
        carriers_yx_per_um=np.array([[q, 0.0]]),
        phases_rad=np.array([[phase]]),
        beam_amplitudes=(4.0, 2.0, 1.0),
        pupil_order=1,
    )

    # Idealized sign factors are 25/21,17/21,9/21. Enclose the exact
    # normalized q/phase and exact source y=D_y/2 rather than those rounded factors.
    def factors(digits: int) -> tuple[Interval, ...]:
        pi = pi_interval(digits)
        kappa = 1 - Interval.rational(1 - exact(q) ** 2, digits).sqrt()
        sy, cy = sin_cos(2 * pi * (exact(q) * exact(0.3) / 2) + exact(phase))
        result = []
        for d in (1, 0, -1):
            sz, cz = sin_cos(2 * pi * kappa * d)
            result.append(((4 * cz + 3 * cy).squared() + (4 * sz + sy).squared()) / 21)
        return tuple(result)

    reference = on_axis_reference(
        (1, 1, 3, 1, 1),
        exact(7),
        exact(0.3) * exact(0.4),
        factors=factors,
    )
    assert_finite_target(call(args), reference)


@pytest.mark.parametrize("order", [1, 2, 3])
def test_explicit_edge_sources_signed_carriers_defocus_and_refinements(order: int) -> None:
    args = inputs()
    source = np.zeros((4, 3, 4))
    source[0, 0, 0], source[3, 2, 3], source[1, 1, 2] = 7.0, 2.5, 0.125
    carriers = ((0.37, -0.23), (-0.11, 0.41), (0.0, 0.0))
    phases = (
        (0.2, -1.1, 7.4, 0.0, math.pi),
        (-0.7, 0.3, 0.3, -8.2, 1.7),
        (math.pi, 0.0, -2.0, 3.0, 4.0),
    )
    args.update(
        source_e=source,
        detector_spacing_um_zyx=(0.8, 0.3, 0.4),
        source_refinement_zyx=(2, 1, 2),
        pixel_subsamples_yx=(2, 1),
        carriers_yx_per_um=np.array(carriers),
        phases_rad=np.array(phases),
        beam_amplitudes=(4.0, 2.0, 1.0),
        pupil_order=order,
    )
    dz, dy, dx = map(exact, (0.8, 0.3, 0.4))
    reference = finite_images(
        (
            Source(dz / 4, dy / 2, dx / 4, exact(7)),
            Source(7 * dz / 4, 5 * dy / 2, 7 * dx / 4, exact(2.5)),
            Source(3 * dz / 4, 3 * dy / 2, 5 * dx / 4, exact(0.125)),
        ),
        (dz / 2, 3 * dz / 2),
        (
            ((dy / 4, dx / 2), (3 * dy / 4, dx / 2)),
            ((dy / 4, 3 * dx / 2), (3 * dy / 4, 3 * dx / 2)),
            ((5 * dy / 4, dx / 2), (7 * dy / 4, dx / 2)),
            ((5 * dy / 4, 3 * dx / 2), (7 * dy / 4, 3 * dx / 2)),
            ((9 * dy / 4, dx / 2), (11 * dy / 4, dx / 2)),
            ((9 * dy / 4, 3 * dx / 2), (11 * dy / 4, 3 * dx / 2)),
        ),
        (3, 2),
        dy * dx,
        carriers,
        phases,
        order=order,
    )
    actual = call(args)
    assert_finite_target(actual, reference)
    assert np.array_equal(actual, call(args))
    actual.fill(-123)
    assert_finite_target(call(args), reference)


@pytest.mark.parametrize("subsamples", [(1, 1), (2, 3), (3, 2)])
def test_pixel_midpoints_and_area(subsamples: tuple[int, int]) -> None:
    args = inputs()
    py, px = subsamples
    args.update(pixel_subsamples_yx=subsamples, pupil_order=1)
    # Q=1 has a single pupil phasor: h(r,d)=pi R² J0(2pi R r/sqrt(2))².
    dz, dy, dx = map(exact, (0.7, 0.3, 0.4))
    sites = tuple(
        (dy * Fraction(2 * j + 1, 2 * py), dx * Fraction(2 * i + 1, 2 * px))
        for j in range(py)
        for i in range(px)
    )
    reference = finite_images(
        (Source(dz / 2, dy / 2, dx / 2, exact(7)),),
        (dz / 2,),
        (sites,),
        (1, 1),
        dy * dx,
        ((0.0, 0.0),),
        ((0.0,),),
        beams=(1.0, 0.0, 0.0),
        order=1,
    )
    assert_finite_target(call(args), reference)


def test_source_weights_superpose_without_voxel_volume() -> None:
    args = inputs()
    args.update(
        source_e=np.array([[[2.0, 5.0]]]),
        source_refinement_zyx=(1, 1, 2),
        pupil_order=1,
        beam_amplitudes=(4.0, 2.0, 1.0),
        carriers_yx_per_um=np.array([[0.0, 0.31]]),
        phases_rad=np.array([[0.7]]),
    )
    dz, dy, dx = map(exact, (0.7, 0.3, 0.4))
    reference = finite_images(
        (Source(dz / 2, dy / 2, dx / 4, exact(2)), Source(dz / 2, dy / 2, 3 * dx / 4, exact(5))),
        (dz / 2,),
        (((dy / 2, dx / 2),),),
        (1, 1),
        dy * dx,
        ((0.0, 0.31),),
        ((0.7,),),
        order=1,
    )
    combined = call(args)
    assert_finite_target(combined, reference)
    args["source_e"] = np.array([[[2.0, 0.0]]])
    left = call(args)
    args["source_e"] = np.array([[[0.0, 5.0]]])
    right = call(args)
    assert_finite_target(
        combined,
        reference.zero_target(),
        subtract=(left, right),
        multiplier=3,
    )


def test_dark_exposure_uses_unilluminated_peak_allowance() -> None:
    args = inputs()
    phases = (math.pi, math.pi + 1e-4, math.pi + 1e-2, 0.0)
    args.update(
        source_e=np.array([[[1e9]]]),
        beam_amplitudes=(2.0, 1.0, 1.0),
        phases_rad=np.array([phases]),
    )
    reference = on_axis_reference(
        (1, 4, 1, 1, 1),
        exact(1e9),
        exact(0.3) * exact(0.4),
        factors=direct_factors(phases, (2, 1, 1)),
    )
    assert_finite_target(call(args), reference)


def test_refinement_in_all_axes_uses_half_cell_source_positions() -> None:
    args = inputs()
    source = np.zeros((2, 2, 3))
    source[1, 1, 2] = 7
    args.update(
        source_e=source,
        source_refinement_zyx=(2, 2, 3),
        pixel_subsamples_yx=(1, 2),
        carriers_yx_per_um=np.array([[-0.37, 0.23]]),
        phases_rad=np.array([[-0.8, 0.1]]),
        beam_amplitudes=(4, 2, 1),
    )
    dz, dy, dx = map(exact, (0.7, 0.3, 0.4))
    reference = finite_images(
        (Source(3 * dz / 4, 3 * dy / 4, 5 * dx / 6, exact(7)),),
        (dz / 2,),
        (((dy / 2, dx / 4), (dy / 2, 3 * dx / 4)),),
        (1, 1),
        dy * dx,
        ((-0.37, 0.23),),
        ((-0.8, 0.1),),
    )
    assert_finite_target(call(args), reference)


def test_builtin_integer_coefficients_and_large_finite_phase() -> None:
    args = inputs()
    args.update(
        detector_spacing_um_zyx=(1, 1, 1),
        beam_amplitudes=(0, 3, 0),
        excitation_um=1,
        emission_um=1,
        refractive_index=1,
        detection_na=1,
        phases_rad=np.array([[1e308, -1e308, 0.0]]),
    )
    # A sole side beam has unit intensity at every finite phase; d=r=0.
    reference = on_axis_reference(
        (1, 3, 1, 1, 1),
        exact(7),
        exact(1),
        aperture=exact(1),
        emission=exact(1),
    )
    assert_finite_target(call(args), reference)
    args.update(
        carriers_yx_per_um=np.array([[0, 2**53]]),
        excitation_um=2.0**-54,
    )
    # Both the enormous carrier phase and input phase are irrelevant to one beam.
    assert_finite_target(call(args), reference)


@pytest.mark.parametrize(
    "variant", ["integer", "unsigned", "float32", "endian", "strided", "fortran", "readonly"]
)
def test_permitted_array_representations(variant: str) -> None:
    args = inputs()
    args.update(
        source_e=np.arange(1.0, 9.0).reshape(2, 2, 2),
        carriers_yx_per_um=np.array([[1.0, 1.0], [0.0, 2.0]]),
        phases_rad=np.array([[0.0, 1.0], [1.0, 0.0]]),
        beam_amplitudes=(4.0, 2.0, 1.0),
    )
    for key in ("source_e", "carriers_yx_per_um", "phases_rad"):
        array = args[key]
        if variant in {"integer", "unsigned", "float32", "endian"}:
            array = array.astype(
                {"integer": "i2", "unsigned": "u8", "float32": "f4", "endian": ">f8"}[variant]
            )
        elif variant == "strided":
            storage = np.repeat(array[..., ::-1], 2, axis=-1)
            array = storage[..., ::-2]
        elif variant == "fortran":
            array = np.asfortranarray(array)
        else:
            array.flags.writeable = False
        args[key] = array
    dz, dy, dx = map(exact, (0.7, 0.3, 0.4))
    reference = finite_images(
        (
            Source(dz / 2, dy / 2, dx / 2, exact(1)),
            Source(dz / 2, dy / 2, 3 * dx / 2, exact(2)),
            Source(dz / 2, 3 * dy / 2, dx / 2, exact(3)),
            Source(dz / 2, 3 * dy / 2, 3 * dx / 2, exact(4)),
            Source(3 * dz / 2, dy / 2, dx / 2, exact(5)),
            Source(3 * dz / 2, dy / 2, 3 * dx / 2, exact(6)),
            Source(3 * dz / 2, 3 * dy / 2, dx / 2, exact(7)),
            Source(3 * dz / 2, 3 * dy / 2, 3 * dx / 2, exact(8)),
        ),
        (dz / 2, 3 * dz / 2),
        (
            ((dy / 2, dx / 2),),
            ((dy / 2, 3 * dx / 2),),
            ((3 * dy / 2, dx / 2),),
            ((3 * dy / 2, 3 * dx / 2),),
        ),
        (2, 2),
        dy * dx,
        ((1.0, 1.0), (0.0, 2.0)),
        ((0.0, 1.0), (1.0, 0.0)),
    )
    assert_finite_target(call(args), reference)


def test_float64_input_rounding_is_permitted() -> None:
    args = inputs()
    args["source_e"] = np.array([[[2**53 + 1]]], dtype=np.uint64)
    reference = on_axis_reference(
        (1, 1, 1, 1, 1),
        exact(float(2**53 + 1)),
        exact(0.3) * exact(0.4),
    )
    assert_finite_target(call(args), reference)


def test_subnormal_nonzero_output_satisfies_the_same_bound() -> None:
    args = inputs()
    smallest = math.ulp(0.0)
    args.update(
        source_e=np.array([[[smallest]]]),
        detector_spacing_um_zyx=(1, 1, 1),
        emission_um=2.0**-20,
        detection_na=1,
        refractive_index=1,
        pupil_order=1,
    )
    # At r=d=0, mu=T=pi*2**40*delta. Rounding error is <=delta/2,
    # less than 1.5e-13*T, although the successful output is subnormal.
    with localcontext() as context:
        context.prec = 100
        peak = decimal_pi() * 2**40
        assert_scaled_scalar_target(
            call(args), peak, peak, unit=smallest, uncertainty=Decimal("1e-75")
        )


def test_dark_underflow_to_zero_respects_unilluminated_bound() -> None:
    args = inputs()
    smallest = math.ulp(0.0)
    phase = math.pi / 2
    args.update(
        source_e=np.array([[[smallest]]]),
        detector_spacing_um_zyx=(1, 1, 1),
        emission_um=1,
        detection_na=1,
        refractive_index=1,
        pupil_order=1,
        beam_amplitudes=(0, 1, 1),
        phases_rad=np.array([[phase]]),
    )
    # The input phase is the exact binary float, not mathematical pi/2.
    # I=2*cos(phase)**2 <= 2*abs(phase-pi/2)**2. Only zero is in range.
    with localcontext() as context:
        context.prec = 100
        pi = decimal_pi()
        offset = abs(Decimal.from_float(phase) - pi / 2) + Decimal("1e-90")
        upper = 2 * offset**2 * pi + Decimal("1e-90")
        assert_scaled_scalar_target(call(args), Decimal(0), pi, unit=smallest, uncertainty=upper)


def test_large_integer_turn_carriers_preserve_exact_phase_target() -> None:
    args = inputs()
    phases = (0.0, 0.25, math.pi / 2)
    args.update(
        source_e=np.ones((1, 1, 1)),
        detector_spacing_um_zyx=(1, 1, 1),
        carriers_yx_per_um=np.array([[0, 2**53], [2**52, -(2**52)], [-(2**53), 0]]),
        phases_rad=np.array([phases, phases, phases]),
        excitation_um=2.0**-54,
        emission_um=1,
        detection_na=1,
        refractive_index=1,
        beam_amplitudes=(1, 1, 1),
        pupil_order=1,
    )
    # Exact source y=x=1/2: the dot products are integer cycles +2**52,0,-2**52.
    # d=0; reducing those cycles first leaves exactly the normalized input phase.
    reference = on_axis_reference(
        (3, 3, 1, 1, 1),
        exact(1),
        exact(1),
        aperture=exact(1),
        emission=exact(1),
        factors=direct_factors(phases * 3, (1, 1, 1)),
    )
    assert_finite_target(call(args), reference)


def test_carrier_and_aperture_closed_upper_boundaries() -> None:
    args = inputs()
    args.update(
        carriers_yx_per_um=np.array([[0.0, 2.5], [1.5, 2.0]]),
        phases_rad=np.array([[0.0, 0.5], [-0.3, 0.9]]),
        detection_na=1.25,
        beam_amplitudes=(4.0, 2.0, 1.0),
        pupil_order=3,
    )
    dz, dy, dx = map(exact, (0.7, 0.3, 0.4))
    reference = finite_images(
        (Source(dz / 2, dy / 2, dx / 2, exact(7)),),
        (dz / 2,),
        (((dy / 2, dx / 2),),),
        (1, 1),
        dy * dx,
        ((0.0, 2.5), (1.5, 2.0)),
        ((0.0, 0.5), (-0.3, 0.9)),
        aperture=1.25,
        order=3,
    )
    assert_finite_target(call(args), reference)


class ArraySubclass(np.ndarray):
    """Excluded array type, despite otherwise valid contents."""


class FloatSubclass(float):
    """Excluded coefficient type, despite a finite positive value."""


class IntSubclass(int):
    """Excluded count type, despite a positive integer value."""


INVALID: list[tuple[str, Any]] = [
    ("source_e", np.ones((1, 1))),
    ("source_e", np.zeros((0, 1, 1))),
    ("source_e", np.array([[[-1.0]]])),
    ("source_e", [[[1.0]]]),
    ("source_e", np.ones((1, 1, 1)).view(ArraySubclass)),
    ("carriers_yx_per_um", np.zeros((1, 3))),
    ("carriers_yx_per_um", np.zeros((0, 2))),
    ("phases_rad", np.zeros((1, 0))),
    ("phases_rad", np.zeros((2, 1))),
    ("phases_rad", np.zeros(1)),
    ("carriers_yx_per_um", np.array([[2.5, 1e-3]])),
    ("detection_na", 1.250001),
    ("pupil_order", 0),
    ("pupil_order", True),
    ("pupil_order", 1.0),
    ("pupil_order", np.int64(2)),
    ("pupil_order", IntSubclass(2)),
    ("source_refinement_zyx", (2, 1, 1)),
    ("source_refinement_zyx", (1, 0, 1)),
    ("source_refinement_zyx", (1, -1, 1)),
    ("source_refinement_zyx", (1, True, 1)),
    ("source_refinement_zyx", (1, 1.0, 1)),
    ("source_refinement_zyx", [1, 1, 1]),
    ("source_refinement_zyx", (1, 1)),
    ("pixel_subsamples_yx", (1, 0)),
    ("pixel_subsamples_yx", (True, 1)),
    ("pixel_subsamples_yx", (1.0, 1)),
    ("pixel_subsamples_yx", [1, 1]),
    ("pixel_subsamples_yx", (1, 1, 1)),
    ("detector_spacing_um_zyx", [0.7, 0.3, 0.4]),
    ("detector_spacing_um_zyx", (0.7, 0.3)),
    ("detector_spacing_um_zyx", (0.7, 0.0, 0.4)),
    ("detector_spacing_um_zyx", (0.7, -0.3, 0.4)),
    ("detector_spacing_um_zyx", (0.7, True, 0.4)),
    ("detector_spacing_um_zyx", (0.7, np.float64(0.3), 0.4)),
    ("beam_amplitudes", (0, 0, 0)),
    ("beam_amplitudes", (-1, 2, 1)),
    ("beam_amplitudes", [1, 0, 0]),
    ("beam_amplitudes", (1, 0)),
    ("beam_amplitudes", (True, 0, 0)),
    ("beam_amplitudes", (FloatSubclass(1), 0, 0)),
]
for array_key, shape in (
    ("source_e", (1, 1, 1)),
    ("carriers_yx_per_um", (1, 2)),
    ("phases_rad", (1, 1)),
):
    for dtype in ("bool", "complex128", "object", "U1"):
        INVALID.append((array_key, np.ones(shape).astype(dtype)))
    for nonfinite in (float("nan"), float("inf"), -float("inf")):
        INVALID.append((array_key, np.full(shape, nonfinite)))
    if array_key != "source_e":
        INVALID.extend(
            [
                (array_key, np.zeros(shape).tolist()),
                (array_key, np.zeros(shape).view(ArraySubclass)),
            ]
        )
for coefficient in ("excitation_um", "emission_um", "refractive_index", "detection_na"):
    for invalid in (
        0,
        -1,
        True,
        np.float64(1),
        FloatSubclass(1),
        float("nan"),
        float("inf"),
        10**400,
    ):
        INVALID.append((coefficient, invalid))
for coefficient in ("detector_spacing_um_zyx", "beam_amplitudes"):
    for invalid in (float("nan"), float("inf"), 10**400):
        INVALID.append((coefficient, (1, invalid, 1)))


@pytest.mark.parametrize("key,value", INVALID)
def test_invalid_domains_preserve_inputs_and_error_settings(key: str, value: Any) -> None:
    args = inputs()
    args[key] = value
    before = snapshot(args)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        with pytest.raises(SimreconError) as error:
            expected_images(**args)
        assert error.value.code == "invalid_simulation_optics"
        assert np.geterr() == settings
    assert_preserved(before)
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


@pytest.mark.parametrize(
    "changes,allow_accurate_success",
    [
        ({"source_e": np.ones((3, 1, 1)), "detector_spacing_um_zyx": (1e308, 0.3, 0.4)}, True),
        ({"emission_um": 1e-320}, False),
        ({"source_e": np.full((1, 1, 1), 1e308), "emission_um": 0.01}, False),
    ],
)
def test_range_obstructions_preserve_inputs_and_error_settings(
    changes: dict[str, Any], allow_accurate_success: bool
) -> None:
    args = inputs()
    args.update(changes)
    before = snapshot(args)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            result = expected_images(**args)
        except SimreconError as error:
            assert error.code == "simulation_optics_range"
        else:
            # Geometry beyond float64 is an identifiable representation obstacle,
            # but a higher-precision evaluator may instead return an accurate image.
            assert allow_accurate_success
            assert type(result) is np.ndarray
            assert result.dtype == np.dtype("float64") and result.dtype.isnative
            assert result.flags.c_contiguous and result.flags.writeable
            assert np.isfinite(result).all() and (result >= 0).all()
            for value in args.values():
                if isinstance(value, np.ndarray):
                    assert not np.shares_memory(result, value)
            assert_finite_target(result, huge_geometry_reference())
        finally:
            assert np.geterr() == settings
            assert_preserved(before)
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


@pytest.mark.parametrize("weight_units", [1, 16])
def test_finite_subnormal_quantization_obstruction_has_range_error(weight_units: int) -> None:
    args = inputs()
    args.update(
        source_e=np.array([[[weight_units * math.ulp(0.0)]]]),
        detector_spacing_um_zyx=(1, 1, 1),
        emission_um=1,
        detection_na=1,
        refractive_index=1,
        pupil_order=1,
    )
    # mu=T=weight_units*pi*delta. Every float in this range is an integer*delta.
    # Even the two bracketing floats fail: this is an obstruction, not a size cap.
    with localcontext() as context:
        context.prec = 100
        peak = weight_units * decimal_pi()
        lower = Decimal(int(peak))
        distance = min(peak - lower, lower + 1 - peak)
        assert distance - Decimal("1e-88") > Decimal("1e-5") * peak
    before = snapshot(args)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        with pytest.raises(SimreconError) as error:
            expected_images(**args)
        assert error.value.code == "simulation_optics_range"
        assert np.geterr() == settings
    assert_preserved(before)
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


def test_python_argument_binding_remains_type_error() -> None:
    args = inputs()
    del args["emission_um"]
    with pytest.raises(TypeError):
        expected_images(**args)
    args = inputs()
    args["unknown_argument"] = 1
    with pytest.raises(TypeError):
        expected_images(**args)
    args = inputs()
    with pytest.raises(TypeError):
        expected_images(args.pop("source_e"), args.pop("detector_spacing_um_zyx"), **args)
