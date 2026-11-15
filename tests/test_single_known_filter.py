"""Literal traversal and independently rounded native-coefficient expectations.

These compare filtered diagnostics, so no FFT error allowance enters them.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

import simrecon as sr
from single_known_fixture import (
    PROFILE,
    add,
    arrays,
    call,
    conjugate,
    cosine_scale_from_program,
    cq,
    declare,
    empirical_quotients_from_program,
    empirical_scale_from_program,
    hypot_transfer_program,
    multiply,
    owned,
    recombine,
    rn32,
    rn64,
    rotate,
    rounding_margin32,
    snapshot,
    sqrt_small_interval,
    to_complex,
    transfer,
    unit_scale,
)
from test_single_known_boundary import rejected


def test_per_time_direction_and_order_noise_and_ordered_overlap() -> None:
    q, v = arrays(t=2, d=2, o=3)
    q[:, :, 0, 0, 0, 0] = 1
    q[:, :, 1, 0, 0, 0] = 1
    q[:, :, 3, 0, 0, 0] = 1
    v[...] = [[[1, 2, 4], [3, 5, 7]], [[2, 3, 5], [7, 11, 13]]]
    result = call(declare(q, v))
    for t in range(2):
        for d in range(2):
            for m, slot in ((0, 0), (1, 1), (2, 3)):
                gs = [[rn64(1 / Fraction(int(v[t, e, n]))) for n in range(3)] for e in range(2)]
                denominator = gs[d][m]
                # Independent sum of the prescribed signed scalar powers.
                for e in range(2):
                    for n in (-2, -1, 0, 1, 2):
                        if (e, n) != (d, m):
                            denominator = rn64(denominator + gs[e][abs(n)])
                denominator = rn64(denominator + Fraction(1, 4))
                expected = rn32(rn64(gs[d][m] / denominator))
                assert result.filtered_quadratures[t, d, slot, 0, 0, 0] == float(expected)
    assert (
        result.filtered_quadratures[0, 0, 0, 0, 0, 0]
        != result.filtered_quadratures[1, 0, 0, 0, 0, 0]
    )


def test_inclusive_self_strict_other_and_positive_zero_writes() -> None:
    q, v = arrays()
    q[...] = complex(-1.0, -0.0)
    bands = declare(q, v)
    result = call(bands)
    interior = unit_scale((Fraction(1), Fraction(1)), 0)
    edge = unit_scale((Fraction(1), Fraction(1)), 0, boundary=True)
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 0].real == -float(interior)
    # r=R=1/2 exactly, self is included, every other q=R is excluded.
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 2].real == -float(edge)
    outside = result.filtered_quadratures[0, 0, :, 0, 1, 1:]
    assert outside.tobytes() == bytes(outside.nbytes)
    axial = result.filtered_quadratures[0, 0, :, 1]
    assert axial.tobytes() == bytes(axial.nbytes)


@pytest.mark.parametrize("modulation", [1 + 0j, 1j, -1 + 0j, 3 + 4j, 0j])
def test_nonunit_complex_transfer_complete_scale_and_actual_partner(modulation: complex) -> None:
    q, v = arrays()
    e = complex(1 + 2**-23, -0.75)
    o = complex(-0.5, 0.25)
    q[0, 0, 0, 0, 0, 1] = e
    q[0, 0, 1, 0, 0, 1] = e
    q[0, 0, 2, 0, 0, 1] = o
    result = call(declare(q, v), transfer(value=3 + 4j), modulation=np.array([[modulation]]))
    # |H|=5 and the selected |a| values0/1/5 are exactly representable.
    a2 = Fraction(modulation.real) ** 2 + Fraction(modulation.imag) ** 2
    denominator = 25 + 50 * a2 + Fraction(1, 4)
    base = (rn64(Fraction(3) / denominator), rn64(Fraction(-4) / denominator))
    scale64 = multiply(base, conjugate(cq(modulation)), bits=53)
    scale = (rn32(scale64[0]), rn32(scale64[1]))
    center = multiply(cq(e), (rn32(base[0]), rn32(base[1])))
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 1] == to_complex(center)
    positive = multiply(add(cq(e), rotate(cq(o))), scale)
    opposite = multiply(add(conjugate(cq(e)), rotate(conjugate(cq(o)))), scale)
    expected_e, expected_o = recombine(positive, conjugate(opposite))
    assert result.filtered_quadratures[0, 0, 1, 0, 0, 1] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 2, 0, 0, 1] == to_complex(expected_o)
    # The oracle formed both opposite coefficients from declared E/O; it never
    # supplies a partner to the candidate or reads a private transform buffer.
    if modulation:
        assert conjugate(opposite) != conjugate(positive)


def test_direction_major_order_is_visible_at_a_consumed_scale_rounding_boundary() -> None:
    q, v = arrays(d=2)
    q[0, 0, 0, 0, 0, 0] = 1
    v[...] = [[[2**54, 2**54], [1, 2**26]]]
    result = call(declare(q, v), wiener=2**-25)
    # Start with self2^-54; e0 sides add two more2^-54. e1 signed -1
    # adds2^-26 before e1 order0 adds1. The three tiny terms then round
    # upward to2^-52. Remaining side and w² give the denominator below.
    denominator = 1 + Fraction(1, 2**25) + Fraction(1, 2**50) + Fraction(1, 2**52)
    expected = rn32(rn64(Fraction(1, 2**54) / denominator))
    assert expected == Fraction(1, 2**54) * (1 - Fraction(1, 2**24))
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 0] == float(expected)
    # Moving the large power first loses the three tiny terms and lands
    # exactly on the RN32 midpoint, whose even result is2^-54 instead.
    reordered = rn32(rn64(Fraction(1, 2**54) / (denominator - Fraction(1, 2**52))))
    assert reordered == Fraction(1, 2**54) and reordered != expected


def test_other_power_has_no_own_axial_cutoff() -> None:
    q, v = arrays(o=3, z=20)
    q[0, 0, 1, 2, 0, 1] = 1
    result = call(declare(q, v, dz_um=0.1), numerical_aperture=0.5)
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [1, 2, 1])
    # Self m1,z2 is inside its cutoff2; zero and highest order have cutoff1.
    # All five signed powers still contribute, giving5+1/4, not2+1/4.
    expected = rn32(rn64(Fraction(4, 21)))
    assert result.filtered_quadratures[0, 0, 1, 2, 0, 1] == float(expected)


def test_omit_kz0_changes_only_center_z0_weight_and_overlap_power() -> None:
    q, v = arrays(z=6)
    for z in (0, 1):
        q[0, 0, 0, z, 0, 1] = 1
        q[0, 0, 1, z, 0, 1] = 1
    result = call(declare(q, v), numerical_aperture=0.5, omit_kz0=True)
    full = float(rn32(rn64(Fraction(4, 13))))
    side_z0 = float(rn32(rn64(Fraction(4, 9))))
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 1] == 0
    assert result.filtered_quadratures[0, 0, 0, 1, 0, 1] == full
    assert result.filtered_quadratures[0, 0, 1, 0, 0, 1] == side_z0
    assert result.filtered_quadratures[0, 0, 1, 1, 0, 1] == full
    omitted = call(declare(q, v), numerical_aperture=0.5, omit_order0=True)
    assert omitted.filtered_quadratures[0, 0, 0, 1, 0, 1] == 0


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_affine_complex_transfer_interpolation_remains_c128(layout: str) -> None:
    q, v = arrays()
    q[0, 0, 0, 0, 0, 1] = 1
    if layout == "radial":
        source = np.empty((2, 8, 8), dtype=np.complex128)
        for r in range(8):
            source[:, r, :] = (r + 1) * (3 + 4j)
    else:
        # Xh=1 intentionally exercises safe flat cross-row x aliases.
        source = np.empty((2, 3, 3, 1), dtype=np.complex128)
        for k in range(3):
            for y in range(3):
                source[:, k, y, 0] = (1 + 3 * k + y) * (3 + 4j)
    otf = sr.declare_otf(source, layout=layout, dkr_cyc_um=1.0, dkz_cyc_um=1.0)
    before = snapshot(otf.samples)
    result = call(declare(q, v), otf)
    # At kx=1/4, ky=kz=0 both layouts interpolate H=(5/4)*(3+4i).
    # Its exact hypot is25/4 and norm squared625/16. The consumed scale is
    # (15/4-5i)/(3*625/16+1/4)=(60-80i)/1879.
    expected = complex(
        float(rn32(rn64(Fraction(60, 1879)))), float(rn32(rn64(Fraction(-80, 1879))))
    )
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 1] == expected
    assert snapshot(otf.samples) == before


def test_nonunit_transfer_is_sampled_natively_before_carrier_relocation() -> None:
    q, v = arrays()
    q[0, 0, 1, 0, 0, 1] = 1
    source = np.empty((2, 8, 8), dtype=np.complex128)
    for r in range(8):
        source[:, r, :] = (r + 1) * (3 + 4j)
    otf = sr.declare_otf(source, layout="radial", dkr_cyc_um=1.0, dkz_cyc_um=1.0)
    result = call(declare(q, v), otf, carriers_cyc_um=np.array([[0.25, 0.0]]))
    # Positive self native x1/4 has shifted object x1/2. Its other q values
    # are1/2 and3/4: strict support excludes both. Denominator625/16+1/4.
    positive = (rn32(rn64(Fraction(60, 629))), rn32(rn64(Fraction(-80, 629))))
    # Opposite native x-1/4 has shifted object0. Other q1/4 and0 contribute
    # 625/16 and25, in addition to its own625/16 and the Wiener1/4.
    opposite = (rn32(rn64(Fraction(30, 827))), rn32(rn64(Fraction(-40, 827))))
    expected_e, expected_o = recombine(positive, conjugate(opposite))
    assert result.filtered_quadratures[0, 0, 1, 0, 0, 1] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 2, 0, 0, 1] == to_complex(expected_o)
    # Sampling self at relocated1/2 would instead use H=(3/2)*(3+4i),
    # with scale(9-12i)/113; it is a different finite-procedure oracle.
    relocated = (rn32(rn64(Fraction(9, 113))), rn32(rn64(Fraction(-12, 113))))
    assert positive != relocated


def test_empirical_style_non_c64_exact_original_transfer_is_valid_and_preserved() -> None:
    bands = declare()
    otf = transfer(value=1 + 0.5j, empirical_delta=2**-30)
    assert otf.samples[0, 0, 0].real == 1 + 2**-30
    before = snapshot(otf.samples)
    result = call(bands, otf)
    assert result.precision_profile == PROFILE
    assert snapshot(otf.samples) == before
    # This is domain/source-retention evidence. Accuracy for this nonexact
    # hypot/interpolation witness awaits its explicit scalar enclosure.


def test_empirical_source_rounding_boundary_has_independent_conditional_scalar_enclosure(
    record_property: Any,
) -> None:
    # G3 applicability remains source/binary/primitive/RNE correspondence, not
    # a guessed ULP allowance. The supplied moderate program is outward-evaluated.
    delta = Fraction(1, 2**30)
    a = rn64(1 + Fraction(1, 5 * 2**23)) - Fraction(1, 2**38)
    expected = empirical_scale_from_program(delta, a)
    early_table_rounding = empirical_scale_from_program(Fraction(0), a)
    h = hypot_transfer_program(delta)
    h_reference = sqrt_small_interval((1 + delta) ** 2 + Fraction(1, 4))
    quotient = empirical_quotients_from_program(delta, a)
    margins = [
        rounding_margin32(component, represented)
        for component, represented in zip(quotient, expected, strict=True)
    ]
    reference = (1 + delta) / (
        ((1 + delta) ** 2 + Fraction(1, 4)) * (1 + 2 * a * a) + Fraction(1, 4)
    )
    exact_with_library = tuple(
        (1 + delta) / (endpoint * endpoint * (1 + 2 * a * a) + Fraction(1, 4)) for endpoint in h
    )
    library_scale = min(exact_with_library), max(exact_with_library)
    library_bound = max(abs(endpoint - reference) for endpoint in library_scale)
    scalar_bound = max(
        abs(quotient[0][0] - library_scale[1]), abs(quotient[0][1] - library_scale[0])
    )
    conversion_bound = max(abs(expected[0] - endpoint) for endpoint in quotient[0])
    assert expected[0] == Fraction(1, 4) - Fraction(1, 2**26)
    assert early_table_rounding[0] == Fraction(1, 4)
    q, v = arrays()
    q[0, 0, 0, 0, 0, 0] = 1
    otf = transfer(value=1 + 0.5j, empirical_delta=float(delta))
    before = snapshot(otf.samples)
    result = call(declare(q, v), otf, modulation=np.array([[float(a)]], dtype=np.float64))
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 0] == to_complex(expected)
    assert snapshot(otf.samples) == before
    assert np.all(result.image == float(expected[0]))
    absolute_error = abs(expected[0] - reference)
    assert absolute_error <= library_bound + scalar_bound + conversion_bound
    record_property(
        "sp113_empirical_dc_enclosure",
        {
            "source_hypot_lower": str(h[0]),
            "source_hypot_upper": str(h[1]),
            "hypot_library_error_lower": str(h[0] - h_reference[1]),
            "hypot_library_error_upper": str(h[1] - h_reference[0]),
            "input_representation_error": "0",
            "source_c64_conversion": "not performed",
            "interpolation_error": "0 (exact node)",
            "library_image_bound": str(library_bound),
            "scalar_image_bound": str(scalar_bound),
            "consumed_scale_image_bound": str(conversion_bound),
            "minimum_consumed_bin_margin": str(min(margins)),
            "local_error": "0",
            "fft_error": "0 (DC)",
            "f64_accumulation_error": "0",
            "final_rounding_error": "0",
            "reference_width": "0",
            "max_absolute_error": str(absolute_error),
            "rms_error": str(absolute_error),
            "interval_distance": str(absolute_error),
            "far_endpoint_upper_bound": str(absolute_error),
            "signed_minimum": str(expected[0]),
            "signed_maximum": str(expected[0]),
            "signal_scale": "1",
            "cancellation_condition": "1",
            "error_over_signal_scale": str(absolute_error),
            "qualification": (
                "conditional; actual hypot/sqrt/scalar/FFT source/binary/RNE "
                "correspondence remains separate"
            ),
        },
    )


@pytest.mark.parametrize("z,na,cutoff", [(2, 1.0, 0), (6, 1.0, 2)])
def test_cosine_uses_shifted_object_origin_and_zero_cutoff_lateral_fallback(
    z: int, na: float, cutoff: int
) -> None:
    q, v = arrays(z=z)
    # Positive harmonic1 and independently zero negative harmonic at native x1/4.
    q[0, 0, 1, 0, 0, 1] = 0.5
    q[0, 0, 2, 0, 0, 1] = -0.5j
    s = unit_scale((Fraction(1), Fraction(1)), 1)
    expected_e, expected_o = recombine((s, Fraction(0)), (Fraction(0), Fraction(0)))
    result = call(
        declare(q, v),
        numerical_aperture=na,
        carriers_cyc_um=np.array([[-0.25, 0.0]]),
        output_taper="cosine",
    )
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [cutoff, cutoff])
    # Kxy=0,z0 gives rho0 and exact cos0=1. Using native radius instead of
    # shifted object radius gives rho1/3. At cutoff0 division by Zp is invalid;
    # the required lateral fallback still has the independently known rho0.
    assert result.filtered_quadratures[0, 0, 1, 0, 0, 1] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 2, 0, 0, 1] == to_complex(expected_o)


def test_cosine_ellipse_uses_c1_and_rho1_is_not_hard_zero() -> None:
    # Conditional G3 point proof uses the actual source expressions/table boxes;
    # no generic libm error promise or measured discrepancy sets an allowance.
    half_scale = cosine_scale_from_program(
        (rn64(Fraction(4, 21)), Fraction(0)),
        Fraction(1, 4),
    )
    edge_scale = cosine_scale_from_program(
        (rn64(Fraction(4, 5)), Fraction(0)),
        Fraction(1, 2),
    )
    q, v = arrays(o=3, z=20)
    q[0, 0, 3, 4, 0, 1], q[0, 0, 4, 4, 0, 1] = 0.5, -0.5j
    result = call(
        declare(q, v, dz_um=0.1),
        numerical_aperture=1.0,
        carriers_cyc_um=np.array([[-0.125, 0.0]]),
        output_taper="cosine",
    )
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [4, 8, 5])
    # Highest m2,z4 uses Zp=c[1]=8, not its own c[2]=5. Shifted Kxy0
    # makes rho1/2 and query PI64/4. The reflected negative harmonic is0.
    expected_e, expected_o = recombine(half_scale, (Fraction(0), Fraction(0)))
    assert result.filtered_quadratures[0, 0, 3, 4, 0, 1] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 4, 4, 0, 1] == to_complex(expected_o)
    boundary_q, boundary_v = arrays()
    boundary_q[0, 0, 0, 0, 0, 2] = 1
    boundary = call(declare(boundary_q, boundary_v), output_taper="cosine")
    assert edge_scale[0] > 0
    assert boundary.filtered_quadratures[0, 0, 0, 0, 0, 2] == to_complex(edge_scale)


def test_cosine_radius_above_one_clips_to_actual_pi64_half_point() -> None:
    edge_scale = cosine_scale_from_program(
        (rn64(Fraction(4, 5)), Fraction(0)),
        Fraction(1, 2),
    )
    q, v = arrays(o=3, z=20)
    q[0, 0, 3, 4, 0, 2] = 1
    result = call(
        declare(q, v, dz_um=0.1),
        numerical_aperture=1.0,
        carriers_cyc_um=np.array([[0.125, 0.0]]),
        output_taper="cosine",
    )
    # Native r=R1/2 is included. Shifted rabs=Rp3/4 and z/Zp=4/8 give
    # rho²=5/4>1 with a certified margin; other q>=5/8 are all excluded.
    # p is finite edge_scale, while the independently declared opposite z-4
    # coefficient at self-paired lateral Nyquist is0.
    expected_e, expected_o = recombine(edge_scale, (Fraction(0), Fraction(0)))
    assert result.filtered_quadratures[0, 0, 3, 4, 0, 2] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 4, 4, 0, 2] == to_complex(expected_o)


def test_odd_y_literal_untouched_and_partial_reflected_zero_rows() -> None:
    q, v = arrays(z=4, y=5, x=6)
    q[...] = complex(-2.0, -0.0)
    q[0, 0, 1, 0, 3, 0] = complex(-0.0, -0.0)
    before = q.copy()
    result = call(declare(q, v))
    filtered = result.filtered_quadratures
    # VY={-1,0,1,2}: row3 represents the omitted y=-2.
    assert filtered[0, 0, 0, :, 3].tobytes() == before[0, 0, 0, :, 3].tobytes()
    for slot in (1, 2):
        for x in (0, 3):
            assert filtered[0, 0, slot, :, 3, x].tobytes() == before[0, 0, slot, :, 3, x].tobytes()
        for z in (0, 1, 3):
            assert filtered[0, 0, slot, z, 3, 1].tobytes() == before[0, 0, slot, z, 3, 1].tobytes()
        assert filtered[0, 0, slot, 2, 3, 1].tobytes() == bytes(8)
        # Reflected x=-2,y=2 lies strictly outside R: every axial cell zero.
        assert filtered[0, 0, slot, :, 3, 2].tobytes() == bytes(4 * 8)


def test_y1_has_empty_filter_and_recombination_even_with_singular_damping_request() -> None:
    q, v = arrays(y=1, x=2)
    q[0, 0, 0, 0, 0, 0] = complex(-0.0, -0.0)
    q[0, 0, 1, 1, 0, 1] = -2 + 3j
    q[0, 0, 2, 0, 0, 1] = 1 - 4j
    bands = declare(q, v)
    result = call(bands, transfer(radial=1, axial=1), dampen_order0=True)
    assert result.filtered_quadratures.tobytes() == q.tobytes()
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [0, 0])


def test_damping_precedes_omission_then_omit_kz0_overrides() -> None:
    q, v = arrays(z=6)
    q[0, 0, 0, 0, 0, 1] = 1
    bands = declare(q, v)
    result = call(bands, numerical_aperture=0.5, dampen_order0=True, omit_order0=True)
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [2, 2])
    # r/R=1/2,z=0 gives g0=1/4, denominator1/4+2+1/4=5/2.
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 1] == float(rn32(rn64(Fraction(1, 10))))
    assert np.all(result.image == 0)  # Side data zero; final center omission holds.
    overridden = call(
        bands, numerical_aperture=0.5, dampen_order0=True, omit_order0=True, omit_kz0=True
    )
    assert overridden.filtered_quadratures[0, 0, 0, 0, 0, 1] == 0
    for flags in (
        {},
        {"omit_order0": True},
        {"omit_kz0": True},
        {"omit_order0": True, "omit_kz0": True},
    ):
        rejected(lambda flags=flags: call(dampen_order0=True, **flags), (PROFILE, "damp", "cutoff"))


def test_order_specific_cutoff_ceil_truncation_and_independent_clip() -> None:
    q, v = arrays(o=3, z=20)
    bands = declare(q, v, dz_um=0.1)
    result = call(bands, numerical_aperture=0.5)
    # c0=ceil((2-sqrt(3))*2)=1, intermediate trunc(1+1/.88)=2,
    # highest trunc1.3=1. None clips at floor20/2.
    np.testing.assert_array_equal(result.axial_cutoffs_bins, [1, 2, 1])
    q2, v2 = arrays(z=20)
    np.testing.assert_array_equal(
        call(declare(q2, v2, dz_um=0.1), numerical_aperture=0.5).axial_cutoffs_bins, [1, 1]
    )
    np.testing.assert_array_equal(call().axial_cutoffs_bins, [0, 0])


def test_suppression_physical_radius_signed_bypass_and_inclusive_condition() -> None:
    q, v = arrays()
    q[0, 0, 0, 0, 0, 1] = 1
    bands = declare(q, v)
    bypass = call(bands, suppress_singularities=True, suppression_radius_bins=-1.0)
    off = call(bands, suppress_singularities=False)
    assert bypass.filtered_quadratures.tobytes() == off.filtered_quadratures.tobytes()
    # dx=1/4,dy=1/2. Radius_bins1 makes sr=1/4; x1 is exactly included.
    result = call(bands, suppress_singularities=True, suppression_radius_bins=1.0)
    r2 = Fraction(1, 16)
    inner = rn64(r2 + Fraction(0.2))
    g = rn64(1 / rn64(1 + rn64(Fraction(1000) / inner)))
    denominator = rn64(rn64(rn64(g + g) + g) + Fraction(1, 4))
    expected = rn32(rn64(g / denominator))
    assert result.filtered_quadratures[0, 0, 0, 0, 0, 1] == float(expected)
    assert expected != unit_scale((Fraction(1), Fraction(1)), 0)


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_zero_weight_actual_stencil_failure_retains_cause_and_inputs(layout: str) -> None:
    bands = declare()
    otf = (
        transfer(radial=1, axial=1)
        if layout == "radial"
        else sr.declare_otf(
            np.ones((2, 1, 1, 1), dtype=np.complex128),
            layout="full",
            dkr_cyc_um=1.0,
            dkz_cyc_um=1.0,
        )
    )
    before = snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples)
    error = rejected(
        lambda: call(bands, otf, modulation=np.zeros((1, 1)), omit_order0=True),
        (PROFILE, "stencil", "transfer", "otf"),
    )
    assert isinstance(error.__cause__, sr.OtfError)
    assert snapshot(bands.quadratures, bands.noise_variance_factors, otf.samples) == before
    # Same zero data/modulation is permitted with a safe complete stencil.
    assert np.all(
        call(bands, transfer(layout=layout), modulation=np.zeros((1, 1)), omit_order0=True).image
        == 0
    )


def test_one_time_axial_wrapping_rejects_an_actual_unsafe_request() -> None:
    q, v = arrays(z=6)
    bands = declare(q, v)
    otf = replace(transfer(), dkz_cyc_um=0.01)
    before = snapshot(bands.quadratures, otf.samples)
    error = rejected(
        lambda: call(bands, otf, numerical_aperture=0.5), (PROFILE, "stencil", "transfer", "otf")
    )
    assert isinstance(error.__cause__, sr.OtfError)
    assert snapshot(bands.quadratures, otf.samples) == before


def test_actual_self_sample_precedes_evaluated_singular_damping() -> None:
    # At the first visited origin c0=0. Both an unsafe stencil and damping
    # singularity exist; the self sample must fail first and retain OtfError.
    error = rejected(
        lambda: call(otf=transfer(radial=1, axial=1), dampen_order0=True),
        (PROFILE, "stencil", "transfer", "otf"),
    )
    assert isinstance(error.__cause__, sr.OtfError)
    rejected(lambda: call(dampen_order0=True), (PROFILE, "damp", "cutoff"))


def test_actual_eligible_other_sample_precedes_its_overflowing_damping_weight() -> None:
    q, v = arrays(o=3, z=20, y=2, x=2)
    v[0, 0, 0] = 2**-1023
    bands = declare(q, v, dxy_um=0.5, dz_um=0.25)
    native_dkz = rn64(Fraction(1, 5))
    table_dkz = rn64(native_dkz / Fraction(29, 8))
    ratio = rn64(native_dkz / table_dkz)
    assert Fraction(18, 5) < ratio < Fraction(73, 20)
    carriers = np.array([[-0.25, 0.0]])
    modulation = np.ones((1, 2), dtype=np.complex128)

    def source(width: int) -> Any:
        samples = np.ones((3, 16, 1, width), dtype=np.complex128)
        samples[0] = 0
        otf = sr.declare_otf(samples, layout="full", dkr_cyc_um=0.25, dkz_cyc_um=float(table_dkz))
        empirical = np.array(otf.samples, copy=True)
        empirical[0] = 2**-1000
        return replace(otf, samples=owned(empirical))

    unsafe, safe = source(2), source(3)
    before = snapshot(
        bands.quadratures, bands.noise_variance_factors, unsafe.samples, carriers, modulation
    )
    options = dict(
        wavelength_nm=4000,
        numerical_aperture=1.0,
        wiener=1.0,
        dampen_order0=True,
        carriers_cyc_um=carriers,
        modulation=modulation,
    )
    error = rejected(
        lambda: call(bands, unsafe, **options), (PROFILE, "transfer", "stencil", "otf")
    )
    assert isinstance(error.__cause__, sr.OtfError)
    assert (
        snapshot(
            bands.quadratures, bands.noise_variance_factors, unsafe.samples, carriers, modulation
        )
        == before
    )
    # c=[2,4,2]. All earlier center queries |z|<=2 have axial vertices below
    # plane15 and finite damping. First m1 self(x0,z-4) is safe at t~1.5.
    # Other n=-2,-1 are excluded (q>=R); n0 is eligible at qx-1/4.
    # Full negative-x reflection makes t~14.5, includes plane15, and Xh2's
    # last lateral vertex aliases flat32 outside its32-element allocation.
    # Only after that sample would g0=2^1023*(1/4+8) overflow.
    weight_error = rejected(
        lambda: call(bands, safe, **options),
        (PROFILE, "weight", "damp", "power", "finite", "overflow"),
    )
    assert not isinstance(weight_error.__cause__, sr.OtfError)
    v[...] = 1
    positive = call(declare(q, v, dxy_um=0.5, dz_um=0.25), safe, **options)
    np.testing.assert_array_equal(positive.axial_cutoffs_bins, [2, 4, 2])
    assert np.all(positive.image == 0)


def test_full_negative_x_reflects_axial_and_lateral_coordinates_and_conjugates() -> None:
    q, v = arrays(z=6, y=4)
    e, o = 1 + 2j, 3 - 1j
    q[0, 0, 1, 1, 1, 1] = e
    q[0, 0, 2, 1, 1, 1] = o
    source = np.empty((2, 8, 8, 8), dtype=np.complex128)
    for z in range(8):
        for y in range(8):
            for x in range(8):
                source[:, z, y, x] = (1 + 3 * z + y + x) * (3 + 4j)
    otf = sr.declare_otf(source, layout="full", dkr_cyc_um=1.0, dkz_cyc_um=1 / 6)
    result = call(declare(q, v), otf, numerical_aperture=0.5)
    # Positive query is (1/4,1/4,1): H=(9/2)*(3+4i). The reflected
    # negative query must return its conjugate, including both y and z flips.
    scale = (rn32(rn64(Fraction(27, 3038))), rn32(rn64(Fraction(-18, 1519))))
    positive = multiply(add(cq(e), rotate(cq(o))), scale)
    opposite = multiply(add(conjugate(cq(e)), rotate(conjugate(cq(o)))), conjugate(scale))
    expected_e, expected_o = recombine(positive, conjugate(opposite))
    assert result.filtered_quadratures[0, 0, 1, 1, 1, 1] == to_complex(expected_e)
    assert result.filtered_quadratures[0, 0, 2, 1, 1, 1] == to_complex(expected_o)


def test_invalid_complete_extra_order_cannot_hide_behind_no_signal() -> None:
    otf = transfer(orders=3)
    bad = np.array(otf.samples, copy=True)
    bad[2, -1, -1] = complex(np.inf, 0)
    rejected(lambda: call(otf=replace(otf, samples=owned(bad))), ("transfer", "otf", "finite"))
