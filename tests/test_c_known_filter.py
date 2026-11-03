"""CE04 native filter powers, branches and complex quadrature obligations."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from c_known_fixture import blank, compare, known, public, supports, table


@pytest.mark.parametrize("variance,wiener,expected", [(1, 0.5, 0.8), (10, 1, 1 / 11)])
def test_closed_single_term_weight_and_wiener(
    variance: float, wiener: float, expected: float
) -> None:
    b = blank()
    b.quadratures[0, 0, 0, 0, 0, 0] = 1
    b.noise_variance_factors[0, 0] = variance
    result = known(b, table(constant=True), modulation=np.zeros((1, 1)), wiener=wiener)
    assert_allclose(result.filtered_quadratures[0, 0, 0, 0, 0, 0], expected, atol=2e-12, rtol=2e-12)
    assert_allclose(result.image, expected, atol=2e-12, rtol=2e-12)


def test_self_inclusive_other_strict_cutoff_and_self_exclusion() -> None:
    b = blank(shape=(1, 2, 3, 6, 4, 4))
    b.quadratures[:, :, 0, 0, 0, 0] = 1
    b.quadratures[:, :, 0, 0, 0, 2] = 3
    result = known(b, table(constant=True), modulation=np.zeros((2, 1)))
    # At DC the other direction contributes once; at the exact R=1 endpoint
    # only self is included. Unit center transfers, w²=1/4.
    assert_allclose(result.filtered_quadratures[0, :, 0, 0, 0, 0], 4 / 9, atol=2e-12, rtol=2e-12)
    assert_allclose(result.filtered_quadratures[0, :, 0, 0, 0, 2], 12 / 5, atol=2e-12, rtol=2e-12)
    assert_array_equal(result.filtered_quadratures[..., 2, 2], 0)


@pytest.mark.parametrize(
    "dampen,expected", [(False, 4 / 21), (True, 8 / 63)], ids=["undamped", "damped"]
)
def test_other_orders_keep_power_beyond_their_axial_cutoff(dampen: bool, expected: float) -> None:
    b = blank(orders=3, shape=(1, 1, 5, 12, 4, 4))
    # c=[2,4,2]: only order1 itself is traversed at z=3. Every signed
    # overlapping order contributes. Without damping den=5+1/4. With
    # damping, center g=(.5/1)^2+abs(3/2)^3=29/8, so den=4+29/8+1/4=63/8.
    b.quadratures[0, 0, 1, 3, 0, 1] = 1
    b.quadratures[0, 0, 2, 3, 0, 1] = -1j
    result = known(b, table(3, constant=True), dampen_order0=dampen)
    assert_array_equal(result.axial_cutoffs_bins, [2, 4, 2])
    assert_allclose(result.filtered_quadratures[0, 0, 1, 3, 0, 1], expected, atol=2e-12, rtol=2e-12)
    assert_allclose(
        result.filtered_quadratures[0, 0, 2, 3, 0, 1], -1j * expected, atol=2e-12, rtol=2e-12
    )


@pytest.mark.parametrize(
    "orders,nz,expected",
    [
        (2, 2, [0, 0]),
        (3, 3, [0, 0, 0]),
        (2, 6, [1, 1]),
        (3, 12, [2, 4, 2]),
        (4, 12, [2, 4, 4, 2]),
    ],
)
def test_ceil_truncate_clip_order_cutoffs(orders: int, nz: int, expected: list[int]) -> None:
    b = blank(orders, shape=(1, 1, 2 * orders - 1, nz, 2, 4))
    b.quadratures[:] = 1 + 2j
    r = compare(b, table(orders))
    assert_array_equal(r.axial_cutoffs_bins, expected)


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_asymmetric_complex_all_signed_directions_orders_and_variances(layout: str) -> None:
    b = blank(3, shape=(2, 3, 5, 6, 4, 4))
    indices = np.indices(b.quadratures.shape)
    b.quadratures[:] = (1 + sum((j + 1) * a for j, a in enumerate(indices))) / 16
    b.quadratures[:] += 1j * (indices[3] - 2 * indices[4] + indices[2]) / 8
    b.noise_variance_factors[:] = [[1, 2, 4], [3, 1, 2], [2, 5, 1]]
    result = compare(
        b,
        table(3, layout),
        carriers_cyc_um=np.array([[0.125, -0.0625], [-0.25, 0.125], [0, 0.1875]]),
        modulation=np.array([[0.5 + 0.25j, -0.5j], [-1, 0], [0.25j, -0.75]]),
    )
    assert np.any(result.image < 0)
    assert not np.array_equal(result.image[0], result.image[1])


@pytest.mark.parametrize("enabled,radius", [(False, 10), (True, 1), (True, -1), (True, 0)])
def test_suppression_uses_physical_radius_inclusive_outer_condition(
    enabled: bool, radius: float
) -> None:
    b = blank()
    b.quadratures[0, 0, 0, 0, 0, 1] = 1
    result = known(
        b,
        table(constant=True),
        modulation=np.zeros((1, 1)),
        wiener=1,
        suppress_singularities=enabled,
        suppression_radius_bins=radius,
    )
    # Native radius .5 cycles/um and min bin spacing .5 cycles/um.
    s = 0.45 / 1000.45 if enabled and radius >= 1 else 1.0
    assert_allclose(
        result.filtered_quadratures[0, 0, 0, 0, 0, 1], s / (s + 1), atol=2e-12, rtol=2e-12
    )


@pytest.mark.parametrize(
    "suppress,dampen,omit,kz0", list(itertools.product([False, True], repeat=4))
)
def test_order_zero_weight_precedence_and_final_omission(
    suppress: bool, dampen: bool, omit: bool, kz0: bool
) -> None:
    b = blank()
    b.quadratures[:] = 1 + 0.5j
    compare(
        b,
        table(),
        suppress_singularities=suppress,
        dampen_order0=dampen,
        omit_order0=omit,
        omit_kz0=kz0,
        suppression_radius_bins=1,
    )


@pytest.mark.parametrize("nz,taper", [(2, "cosine"), (6, "cosine"), (6, "none")])
def test_taper_uses_shifted_frequency_and_self_axial_bin(nz: int, taper: str) -> None:
    b = blank(shape=(1, 1, 3, nz, 4, 4))
    b.quadratures[:] = 1 - 0.5j
    compare(
        b,
        table(),
        carriers_cyc_um=np.array([[0.1875, -0.125]]),
        output_taper=taper,
        modulation=np.array([[0.5 + 0.75j]]),
    )


def test_complex_conjugation_has_closed_positive_side_amplitude() -> None:
    b = blank()
    b.quadratures[0, 0, 1, 0, 0, 1] = 0.5
    b.quadratures[0, 0, 2, 0, 0, 1] = -0.5j
    samples = np.empty((2, 12, 16), np.complex64)
    samples[0] = 0
    samples[1] = 1 + 1j
    transfer = public("declare_otf")(samples, layout="radial", dkr_cyc_um=0.5, dkz_cyc_um=0.5)
    result = known(b, transfer, modulation=np.array([[0.5 + 0.5j]]))
    # Both signed side orders overlap: 2*|1+i|²*|(.5+.5i)|²+.25=2.25.
    # conj(H)*conj(a)=-i. Fplus=-4i/9; its partner is zero.
    assert_allclose(result.filtered_quadratures[0, 0, 1, 0, 0, 1], -2j / 9, atol=2e-12, rtol=2e-12)
    assert_allclose(result.filtered_quadratures[0, 0, 2, 0, 0, 1], -2 / 9, atol=2e-12, rtol=2e-12)
    assert_allclose(result.image[0, 0, 0], [0, 8 / 9, 0, -8 / 9], atol=2e-12, rtol=2e-12)


def test_filter_precedes_noninteger_relocation_not_quotient_interpolation() -> None:
    b = blank(lateral_zoom=2)
    b.quadratures[0, 0, 1, 0, 0, 1] = 0.5
    b.quadratures[0, 0, 2, 0, 0, 1] = -0.5j
    samples = np.zeros((2, 16, 16), np.complex64)
    samples[1] = 1 + np.arange(16)[:, None] / 4
    transfer = public("declare_otf")(samples, layout="radial", dkr_cyc_um=0.5, dkz_cyc_um=0.5)
    carrier = np.array([[0.25, 0.0]])
    result = compare(b, transfer, carriers_cyc_um=carrier)
    # Native k=.5, K=.75. Self H=1.25; negative overlap q=1 is
    # excluded at R=1. Thus F=1.25/(1.25²+.25)=20/29.
    assert_allclose(result.filtered_quadratures[0, 0, 1, 0, 0, 1], 10 / 29, atol=2e-12, rtol=2e-12)
    x = result.x_um
    expected = 40 / 29 * np.cos(2 * np.pi * (np.arange(8) / 8 + 0.25 * x))
    assert_allclose(result.image[0, 0, 0], expected, atol=2e-12, rtol=2e-12)
    # Explicit interpolation-first comparison at native half-bin endpoints:
    # interpolate H then divide differs from interpolating H/(H²+w²).
    quotient_after = 1.375 / (1.375**2 + 0.25)
    quotient_before = ((1.25 / (1.25**2 + 0.25)) + (1.5 / (1.5**2 + 0.25))) / 2
    assert abs(quotient_after - quotient_before) > 0.001


def test_suppression_on_side_and_unequal_noise_are_not_amplitude_floor() -> None:
    b = blank()
    b.quadratures[:] = 1 + 1j
    b.noise_variance_factors[:] = [0.25, 4]
    compare(
        b,
        table(),
        modulation=np.array([[-0.25 + 0.5j]]),
        suppress_singularities=True,
        suppression_radius_bins=0,
    )


@pytest.mark.parametrize("suppress,omit", list(itertools.product([False, True], repeat=2)))
def test_closed_damping_weights_precede_suppression_and_final_omission(
    suppress: bool, omit: bool
) -> None:
    b = blank()
    b.quadratures[0, 0, 0, 0, 0, 1] = 1
    b.quadratures[0, 0, 0, 1, 0, 1] = 2
    result = known(
        b,
        table(constant=True),
        modulation=np.zeros((1, 1)),
        wiener=1,
        suppress_singularities=suppress,
        dampen_order0=True,
        omit_order0=omit,
    )
    # R=1,c0=1,r=.5: g(z0)=1/4 and g(z1)=5/4. With no side
    # power these give g/(g+1), including when final assembly omits B0.
    assert_allclose(result.filtered_quadratures[0, 0, 0, 0, 0, 1], 1 / 5, rtol=2e-12, atol=2e-12)
    assert_allclose(result.filtered_quadratures[0, 0, 0, 1, 0, 1], 10 / 9, rtol=2e-12, atol=2e-12)
    if omit:
        assert_array_equal(result.image, 0)
    else:
        assert np.max(np.abs(result.image)) > 1


@pytest.mark.parametrize("ny,nx,iy,ix", [(2, 4, 0, 2), (4, 2, 2, 0)])
def test_suppression_outer_radius_uses_smaller_rectangular_bin_spacing(
    ny: int, nx: int, iy: int, ix: int
) -> None:
    b = blank(shape=(1, 1, 3, 6, ny, nx))
    b.quadratures[0, 0, 0, 0, iy, ix] = 1
    r = known(
        b,
        table(constant=True),
        modulation=np.zeros((1, 1)),
        suppress_singularities=True,
        suppression_radius_bins=1,
    )
    # min(dx,dy)=.5 and native r=R=1. Using the larger step wrongly
    # suppresses this sample; its only nonzero eligible power is self.
    assert_allclose(r.filtered_quadratures[0, 0, 0, 0, iy, ix], 0.8, rtol=2e-12, atol=2e-12)


def test_closed_shifted_cosine_taper_multiplies_after_denominator() -> None:
    b = blank()
    b.quadratures[0, 0, 1, 0, 0, 1] = 0.5
    b.quadratures[0, 0, 2, 0, 0, 1] = -0.5j
    values = np.ones((2, 16, 16), np.complex64)
    values[0] = 0
    transfer = public("declare_otf")(values, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.25)
    r = known(b, transfer, carriers_cyc_um=np.array([[0.125, 0]]), output_taper="cosine")
    # K=.625, Rp=1.125; two signed side powers give denominator9/4.
    c = (4 / 9) * math.cos(5 * math.pi / 18)
    assert_allclose(r.filtered_quadratures[0, 0, 1, 0, 0, 1], c / 2, rtol=2e-12, atol=2e-12)
    phase = 2 * np.pi * (np.arange(4) / 4 + 0.125 * ((np.arange(4) - 2) * 0.5))
    assert_allclose(r.image[0, 0, 0], 2 * c * np.cos(phase), rtol=2e-12, atol=2e-12)


@pytest.mark.parametrize("near_endpoint", [False, True], ids=["endpoint", "near-endpoint"])
def test_taper_endpoint_and_near_endpoint_have_bounded_absolute_error(near_endpoint: bool) -> None:
    b = blank()
    delta = 2**-12
    ix = 1 if near_endpoint else 2
    aperture = 0.125 / (1 - delta) if near_endpoint else 0.8
    b.quadratures[0, 0, 0, 0, 0, ix] = 1
    r = known(
        b,
        table(constant=True),
        modulation=np.zeros((1, 1)),
        output_taper="cosine",
        wavelength_nm=500,
        numerical_aperture=aperture,
    )
    # At the endpoint compare mathematical zero with an absolute budget.
    # Inside, r=.5,R=.5/(1-delta): cos(pi*(1-delta)/2)=sin(pi*delta/2).
    # 64 binary64 eps < 1.5e-14 bounds unit-scale argument/arithmetic
    # errors; 2e-14 admits equivalent cosine evaluation without pinning pi.
    expected = 0.8 * math.sin(math.pi * delta / 2) if near_endpoint else 0
    assert_allclose(r.filtered_quadratures[0, 0, 0, 0, 0, ix], expected, rtol=0, atol=2e-14)
    # Literal cosine vs an exact-endpoint conditional remains a D review duty.


def test_public_defaults_select_suppression_and_cosine_taper() -> None:
    b = blank()
    b.quadratures[:] = 1 + 0.5j
    transfer = table()
    explicit = known(b, transfer, suppress_singularities=True, output_taper="cosine")
    default = public("reconstruct_known")(
        b,
        transfer,
        carriers_cyc_um=np.zeros((1, 2)),
        modulation=np.ones((1, 1)),
        wavelength_nm=520,
        numerical_aperture=0.8,
        immersion_index=1.33,
        wiener=0.5,
    )
    assert_array_equal(default.image, explicit.image)
    assert_array_equal(default.filtered_quadratures, explicit.filtered_quadratures)


def test_cutoff_expectation_anchor_is_not_common_cutoff() -> None:
    # This oracle-only check remains runnable before the new public entry exists.
    class Sampling:
        input_shape = (1, 1, 5, 12, 4, 4)
        noise_variance_factors = np.ones((1, 3))
        dz_um = 0.3
        dxy_um = 0.5

    radius, cuts = supports(
        Sampling(), {"wavelength_nm": 520, "numerical_aperture": 0.8, "immersion_index": 1.33}
    )
    assert radius == 1
    assert cuts == [2, 4, 2]
    assert math.trunc(1.3 * 2) == 2
