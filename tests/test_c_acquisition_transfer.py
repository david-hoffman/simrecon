"""Expanded empirical domains and direct complex128 transfer composition."""

from math import cos, pi, sin, sqrt
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    close,
    edge,
    gamma,
    known_options,
    lift,
    optics,
    options,
    raw_pattern,
    reconstruct_expected,
    sample,
    transform,
)


def bead_options(**changes: Any) -> dict[str, Any]:
    result = dict(
        dxy_um=0.25,
        dz_um=0.7,
        linespacing_um=0.9,
        wavelength_nm=520,
        background_counts=0,
        compensate_bead=False,
        fix_axial_axis=False,
        fix_radial_from=0,
        origin_fit_bins=None,
        cleanup_axial_bins=(0, 0, 0),
    )
    result.update(changes)
    return result


def bead_raw(y: int, x: int, z: int = 1) -> Any:
    raw = np.zeros((3, z, y, x))
    for p, w in enumerate([1, 2, 3]):
        raw[p, z // 2, y // 2, x // 2] = 9 * w
        raw[p, z // 2, y // 2, x // 2 + 2] = w
        # Unequal edge endpoints expose literal Y-based horizontal addressing.
        raw[p, :, 0, 0] = w
        raw[p, :, -1, -1] = 2 * w
    return raw


def bead_expected(raw: Any, settings: dict[str, Any]) -> dict[str, Any]:
    p, z, y, x = raw.shape
    planes = np.array(
        [[edge(raw[phase, h], 10, bead=True) for h in range(z)] for phase in range(p)]
    )
    mean = np.mean(planes, axis=0)
    location = np.unravel_index(np.argmax(mean), mean.shape)
    center = []
    for axis, n in [(2, x), (1, y), (0, z)]:
        v = []
        for offset in [-1, 0, 1]:
            q = list(location)
            q[axis] = (location[axis] + offset) % n
            v.append(mean[tuple(q)])
        c = v[2] + v[0] - 2 * v[1]
        delta = 0 if c == 0 else -(v[2] - v[0]) / (2 * c)
        center.append(location[axis] + (0 if abs(delta) > 1.5 else delta))
    phase = 2 * pi * np.arange(p) / p
    rows = [np.ones(p) / p, np.cos(phase) / p, np.sin(phase) / p]
    separated = np.tensordot(rows, planes, axes=(1, 0))
    transformed = transform(separated, axes=(1, 2, 3))[..., : x // 2 + 1]
    dkr, dkz = 1 / (y * settings["dxy_um"]), 1 / (z * settings["dz_um"])
    radial = np.zeros((p, x // 2 + 1, z), dtype=complex)
    counts = np.zeros(x // 2 + 1)
    for h, i, j in np.ndindex(z, y, x // 2 + 1):
        ramp = np.exp(
            2j * pi * (j * center[0] / x + lift(y)[i] * center[1] / y + lift(z)[h] * center[2] / z)
        )
        r = int(np.rint(np.hypot(j, lift(y)[i])))
        if r >= x // 2 + 1:
            continue
        if h == 0:
            counts[r] += 1
        for slot in range(p):
            value = transformed[slot, h, i, j] * ramp
            if settings["compensate_bead"]:
                order = (slot + 1) // 2
                theta = settings.get("carrier_angle_rad", 0.0)
                rho = sqrt(
                    (j * dkr + order * cos(theta) / settings["linespacing_um"]) ** 2
                    + (lift(y)[i] * dkr + order * sin(theta) / settings["linespacing_um"]) ** 2
                    + (lift(z)[h] * dkz) ** 2
                )
                u = pi * settings.get("bead_diameter_um", 0.12) * rho
                sphere = 1.0 if u == 0 else 3 * (sin(u) - u * cos(u)) / u**3
                value /= sphere
            radial[slot, r, h] += value
    radial /= np.where(counts == 0, 1, counts)[None, :, None]
    radial[:, :, 0] = np.real(radial[:, :, 0])
    for h in range(1, z // 2 + 1):
        v = (radial[:, :, h] + np.conj(radial[:, :, -h])) / 2
        radial[:, :, h], radial[:, :, -h] = v, np.conj(v)
    factors = []
    common = 1 / np.max(abs(radial[0]))
    for slot in range(p):
        scale = 1 / np.max(abs(radial[slot])) if settings.get("rescale_each", False) else common
        factors.append(scale)
        radial[slot] *= scale
    c, s = radial[1], radial[2]
    phi = np.arctan(np.sum(abs(s)) / np.sum(abs(c)))
    cv, sv = c[x // 8, 0].real, s[x // 8, 0].real
    if cv < 0 and sv > 0:
        phi += pi
    elif cv < 0 and sv < 0:
        phi = pi - phi
    elif cv > 0 and sv > 0:
        phi = -phi
    if settings.get("forced_pi_shift", False):
        phi = pi - phi
    combined = np.stack([radial[0], c * cos(phi) - s * sin(phi)])
    if settings.get("conjugate", False):
        combined = np.conj(combined)
    return dict(
        center_pixels_xyz=np.array(center),
        quadratures=radial,
        normalization_factors=np.array(factors),
        samples=combined,
        dkr=dkr,
        dkz=dkz,
    )


@pytest.mark.parametrize(
    "y,x,z",
    [
        (24, 24, 1),
        (22, 24, 3),
        (26, 24, 1),
        (32, 32, 1),
        (10, 8, 1),
        (10, 10, 2),
        (11, 10, 1),
        (12, 10, 1),
    ],
)
@pytest.mark.parametrize("compensate,rescale", [(False, False), (True, False), (False, True)])
def test_rectangular_z1_phase_fft_center_sphere_radial_scale(
    y: int, x: int, z: int, compensate: bool, rescale: bool
) -> None:
    raw = bead_raw(y, x, z)
    raw.flags.writeable = False
    settings = bead_options(
        compensate_bead=compensate,
        rescale_each=rescale,
        carrier_angle_rad=0.37,
        bead_diameter_um=0.08,
    )
    expected = bead_expected(raw, settings)
    actual = api("prepare_bead_otf")(raw, **settings)
    for name in ["center_pixels_xyz", "quadratures", "normalization_factors"]:
        close(
            getattr(actual, name),
            expected[name],
            work=raw.size,
            scale=float(np.sum(abs(raw))),
            condition=16,
        )
    close(actual.transfer.samples, expected["samples"], work=raw.size, scale=16, condition=32)
    assert actual.transfer.samples.shape == (2, x // 2 + 1, z)
    assert actual.transfer.dkr_cyc_um == expected["dkr"]
    assert actual.transfer.dkz_cyc_um == expected["dkz"]
    assert not actual.transfer.samples.flags.writeable


def test_z1_active_radial_repair_fails_but_disabled_and_large_start_are_noops() -> None:
    raw = bead_raw(24, 24)
    good = api("prepare_bead_otf")(raw, **bead_options())
    large = api("prepare_bead_otf")(raw, **bead_options(fix_radial_from=13))
    np.testing.assert_array_equal(good.transfer.samples, large.transfer.samples)
    for start in [1, 12]:
        with pytest.raises(api("OtfError"), match="(?i)radial|repair|alloc|index|bound"):
            api("prepare_bead_otf")(raw, **bead_options(fix_radial_from=start))


def test_rectangular_out_of_allocation_rejects_even_zero_edge_difference() -> None:
    raw = np.zeros((3, 1, 28, 24))
    raw[:, 0, 14, 12] = [10, 20, 30]
    with pytest.raises(api("OtfError"), match="(?i)edge|alloc|bound|address|rectang"):
        api("prepare_bead_otf")(raw, **bead_options())
    # Y=X+2 is in allocation, including real padding writes.
    actual = api("prepare_bead_otf")(bead_raw(26, 24), **bead_options())
    assert np.isfinite(actual.transfer.samples).all()


@pytest.mark.parametrize("dz", [0.0, 0.4])
def test_actual_non_complex64_exact_prepared_transfer_used_without_rebinding(dz: float) -> None:
    raw = np.zeros((3, 1, 32, 32))
    for p, w in enumerate([1, 2, 3]):
        raw[p, 0, 16, 16] = 3 * w
        raw[p, 0, 16, 18] = w
    prepared = api("prepare_bead_otf")(raw, **bead_options())
    table = prepared.transfer
    exact = (17 + 3 * cos(pi / 8)) / 20
    close(table.samples[0, 1, 0], exact, work=32, scale=1)
    quantized = complex(np.complex64(table.samples[0, 1, 0]))
    assert abs(exact - quantized) > 1000 * np.finfo(float).eps
    assert table.dkz_cyc_um == 1 / 0.7
    observed = api("sample_otf")(table, table.dkr_cyc_um, 0, 0, dkz_cyc_um=table.dkz_cyc_um)
    close(observed, exact, work=32, scale=1)
    with pytest.raises(api("OtfError"), match="(?i)represent|complex64|exact|float32"):
        api("declare_otf")(
            table.samples, layout="radial", dkr_cyc_um=table.dkr_cyc_um, dkz_cyc_um=table.dkz_cyc_um
        )
    # Actual raw specimen -> preparation -> known image, then actual fitted factors.
    specimen = raw_pattern(y=4, x=6)
    bands = api("prepare_acquisition_bands")(specimen, **options(dz_um=dz))
    carriers = np.array([[0.04, 0.02]])
    modulation = np.array([[0.3 + 0.1j]])
    expected = reconstruct_expected(bands, table, carriers, modulation, **known_options())
    known = api("reconstruct_known")(
        bands, table, carriers_cyc_um=carriers, modulation=modulation, **known_options()
    )
    close(
        known.image,
        expected["image"],
        work=24,
        scale=float(np.sum(abs(bands.quadratures))),
        condition=64,
    )
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=carriers, search_carriers=False, **optics()
    )
    fitted = api("reconstruct_known")(
        bands,
        table,
        carriers_cyc_um=estimated.carriers_cyc_um[0],
        modulation=estimated.modulation[0],
        **known_options(),
    )
    expected_fit = reconstruct_expected(
        bands, table, estimated.carriers_cyc_um[0], estimated.modulation[0], **known_options()
    )
    close(
        fitted.image,
        expected_fit["image"],
        work=24,
        scale=float(np.sum(abs(bands.quadratures))),
        condition=64,
    )
    # Sampler math independently uses the original table; no dkz=1 requirement.
    close(
        api("sample_otf")(table, 0.1, 0, 0, dkz_cyc_um=table.dkz_cyc_um),
        sample(table, 0.1, 0, 0, table.dkz_cyc_um, 0),
        work=8,
        scale=1,
    )


def test_migrated_original_rectangular_geometry_is_now_positive() -> None:
    raw = np.zeros((5, 5, 24, 22))
    weights = np.array([1.0, 2.0, 4.0, 8.0, 16.0])
    raw[:, 2, 12, 11] = weights
    actual = api("prepare_bead_otf")(raw, **bead_options())
    phase = 2 * pi * np.arange(5) / 5
    expected = (
        np.array([np.ones(5), np.cos(phase), np.sin(phase), np.cos(2 * phase), np.sin(2 * phase)])
        @ weights
        / np.sum(weights)
    )
    close(
        actual.quadratures,
        expected[:, None, None] * np.ones((5, 12, 5)),
        work=5 * 24 * 22,
        scale=16,
        condition=16,
    )
    close(actual.transfer.samples[0], 1, work=5 * 24 * 22, scale=1, condition=16)
    assert actual.transfer.samples.shape == (3, 12, 5)


@pytest.mark.parametrize(
    "y,x,reason",
    [(8, 8, "vertical"), (10, 6, "addition"), (11, 8, "subtraction")],
    ids=["vertical-y8", "padding-add-x6", "last-row-subtract-y11"],
)
def test_adjacent_bead_address_failures_with_zero_edge_differences(
    y: int, x: int, reason: str
) -> None:
    # Each geometry violates a different part of the approved address envelope.
    # A zero difference cannot make an invalid source write safe.
    raw = np.zeros((3, 1, y, x))
    raw[:, 0, y // 2, x // 2] = [1, 2, 3]
    assert reason in {"vertical", "addition", "subtraction"}
    with pytest.raises(api("OtfError"), match=".+"):
        api("prepare_bead_otf")(raw, **bead_options())


def closed_bead_error() -> float:
    """Propagate the explicitly conditional backend model in A2/expectations.md."""
    u = 2.0**-53
    separation_error = 2 * gamma(12) + 64 * u
    fourier_error = 80 * separation_error + gamma(8 * (8 + 10)) * 2
    ramp_error = gamma(8) * 32 + 4 * u
    centered_error = fourier_error + (2 + fourier_error) * ramp_error + gamma(8) * 2
    radial_error = centered_error + gamma(17) * (2 + centered_error)
    scale_error = radial_error / (2 * (2 - radial_error)) + u / (2 - radial_error)
    normalized_error = radial_error / 2 + (2 + radial_error) * scale_error + u * (1 + radial_error)
    c, s = 0.25, sqrt(3) / 12
    sum_error = 5 * normalized_error + gamma(5) * 5 * (c + normalized_error)
    ratio_error = (sum_error * (5 * c + 5 * s)) / (5 * c * (5 * c - sum_error))
    ratio_error += gamma(2) * (5 * s + sum_error) / (5 * c - sum_error)
    # atan <=4u, pi representation <=2u, final subtraction <=4u.
    angle_error = ratio_error + 10 * u
    return (
        2 * normalized_error
        + (c + s + 2 * normalized_error) * (angle_error + 4 * u)
        + gamma(8) * (c + s)
    )


def closed_composition_errors(table_error: float) -> tuple[float, float, float]:
    """Bound the small DC control using product, quotient and reduction errors."""
    u = 2.0**-53
    cells = 8
    a = sqrt(3) / 6
    eh = table_error + gamma(8) * (1 + table_error)
    eb = gamma(8 * (4 + 2)) * 6 + cells * (gamma(12) * 0.75 + 32 * u * 0.75)

    def product(av: float, ae: float, bv: float, be: float) -> float:
        return av * be + bv * ae + ae * be + gamma(8) * (av + ae) * (bv + be)

    def quotient(nv: float, ne: float, dv: float, de: float) -> float:
        assert dv > de  # observer conditioning, never a scientific input gate
        return (ne + nv / dv * de) / (dv - de) + gamma(2) * (nv + ne) / (dv - de)

    def inverse(value: float, error: float) -> float:
        return cells * error + gamma(8 * (4 + 2)) * (value + cells * error)

    d = sqrt(1 + a * a)
    ed2 = product(1, eh, 1, eh) + product(a, eh, a, eh) + u * d * d
    ed = ed2 / (d + sqrt(d * d - ed2)) + u * (d + ed2 / d)
    lower, upper = 6 * a / d, 3 / d
    el = inverse(lower, quotient(6 * a, product(6, eb, a, eh), d, ed))
    eu = inverse(upper, quotient(3, product(3, eb, 1, eh), d, ed))
    sx = cells * lower * lower
    esx = cells * product(lower, el, lower, el) + gamma(cells) * cells * (lower + el) ** 2
    cross = cells * lower * upper
    ecross = cells * product(lower, el, upper, eu)
    ecross += gamma(cells) * cells * (lower + el) * (upper + eu)
    estimate_error = quotient(cross, ecross, sx, esx)
    ecden = product(1, eh, 1, eh) + u * 1.25
    center_error = quotient(6, product(6, eb, 1, eh), 1.25, ecden)
    known_error = inverse(4.8, center_error)
    numerator_error = product(3, eb, a, eh)
    numerator_error = product(3 * a, numerator_error, sqrt(3), estimate_error)
    side_power_error = product(a, eh, a, eh)
    mod_power_error = product(sqrt(3), estimate_error, sqrt(3), estimate_error)
    denominator_error = product(a * a, side_power_error, 3, mod_power_error) + u * 0.5
    side_error = quotient(1.5, numerator_error, 0.5, denominator_error)
    image_error = known_error + 2 * inverse(3, side_error) + gamma(4) * 10.8
    return estimate_error, known_error, image_error


@pytest.mark.parametrize("dz", [0.0, 0.4], ids=["specimen-dz0", "specimen-positive-dz"])
def test_x8_y10_closed_transfer_actual_estimates_and_image(dz: float) -> None:
    # Algebra and allowances are fixed before the first public call.
    a = sqrt(3) / 6
    table_error = closed_bead_error()
    estimate_error, known_error, image_error = closed_composition_errors(table_error)
    assert table_error < abs(a - float(np.float32(a))) / 10
    raw = np.zeros((3, 1, 10, 8))
    raw[:, 0, 5, 4] = [1, 2, 3]
    raw.flags.writeable = False
    prepared = api("prepare_bead_otf")(
        raw,
        **bead_options(
            dxy_um=1.0,
            dz_um=0.5,
            linespacing_um=1.0,
            wavelength_nm=500,
            numerical_aperture=1.0,
            immersion_index=1.0,
        ),
    )
    table = prepared.transfer
    np.testing.assert_array_equal(prepared.center_pixels_xyz, [4, 5, 0])
    np.testing.assert_allclose(
        table.samples,
        np.broadcast_to(np.array([1, a])[:, None, None], (2, 5, 1)),
        rtol=0,
        atol=table_error,
    )
    assert table.dkr_cyc_um == 0.1 and table.dkz_cyc_um == 2.0
    for order, value in enumerate([1, a]):
        observed = api("sample_otf")(table, 0.15, 0, 0, dkz_cyc_um=2.0, order=order)
        np.testing.assert_allclose(observed, value, rtol=0, atol=table_error + gamma(8))
    with pytest.raises(api("OtfError"), match="(?i)represent|complex64|exact|float32"):
        api("declare_otf")(
            table.samples, layout="radial", dkr_cyc_um=table.dkr_cyc_um, dkz_cyc_um=table.dkz_cyc_um
        )
    with pytest.raises(api("OtfError"), match="(?i)stencil|vertex|alloc|bound|index"):
        api("sample_otf")(table, 0.4, 0, 0, dkz_cyc_um=2.0)
    specimen = np.broadcast_to(
        np.array([1, 1, 4])[None, None, :, None, None, None], (1, 1, 3, 1, 2, 4)
    )
    bands = api("prepare_acquisition_bands")(specimen, **options(dxy_um=4.0, dz_um=dz))
    carriers = np.zeros((1, 2))
    settings = known_options(filter_overlaps=False)
    control = api("reconstruct_known")(
        bands, table, carriers_cyc_um=carriers, modulation=np.zeros((1, 1)), **settings
    )
    np.testing.assert_allclose(control.image, 24 / 5, rtol=0, atol=known_error)
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=carriers, search_carriers=False, **optics()
    )
    np.testing.assert_allclose(
        estimated.modulation, -sqrt(3) / 2 - 1.5j, rtol=0, atol=estimate_error
    )
    result = api("reconstruct_known")(
        bands,
        table,
        carriers_cyc_um=estimated.carriers_cyc_um[0],
        modulation=estimated.modulation[0],
        **settings,
    )
    np.testing.assert_allclose(result.image, 54 / 5, rtol=0, atol=image_error)
