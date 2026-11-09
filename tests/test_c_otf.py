"""CE03 public numerical proofs; independent finite sums, never retained C.

Error budgets were fixed in A3/oracles-before-observation.md before product use.
The dense oracle uses explicit Fourier bases, not a transform implementation.
"""

from dataclasses import FrozenInstanceError
from importlib.util import find_spec
from math import atan, cos, pi, sin
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import simrecon as sr

F64 = NDArray[np.float64]
C128 = NDArray[np.complex128]
EPS = np.finfo(np.float64).eps


def api(name: str) -> Any:
    assert hasattr(sr, name), f"approved public CE03 entry missing: {name}"
    return getattr(sr, name)


def settings(**changes: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dxy_um": 0.25,
        "dz_um": 0.5,
        "linespacing_um": 0.75,
        "wavelength_nm": 520,
        "background_counts": 0.0,
        "compensate_bead": False,
        "fix_axial_axis": False,
    }
    result.update(changes)
    return result


def bead(p: int = 5, n: int = 24, z: int = 5) -> F64:
    """Declare integer detector observations, not a generated optical model."""
    spatial = np.zeros((z, n, n), dtype=np.float64)
    spatial[1, 12, 11] = 100
    spatial[1, 12, 10] = 20
    spatial[1, 12, 12] = 40
    spatial[1, 11, 11] = 30
    spatial[1, 13, 11] = 10
    spatial[0, 12, 11] = 10
    spatial[2, 12, 11] = 30
    amplitudes = np.array([12, 20, 10, 6, 8, 14, 18, 22, 16], dtype=np.float64)[:p]
    return amplitudes[:, None, None, None] * spatial


def edge_matrix(n: int) -> F64:
    """Independent linear form; overlap contributions add to the same row."""
    v = np.zeros(n)
    for index in range(10):
        weight = 1 - sin((index + 0.5) * pi / 20)
        v[index] += weight
        v[n - 1 - index] -= weight
    difference = np.zeros(n)
    difference[-1], difference[0] = 0.5, -0.5
    return np.eye(n) + np.outer(v, difference)


def centered_peak(mean: F64) -> F64:
    """Finite argmax and local polynomial observer, independent of FFT."""
    location = np.unravel_index(int(np.argmax(mean)), mean.shape)
    maximum = float(mean[location])
    if maximum <= 0:
        location, maximum = (0, 0, 0), 0.0
    result = []
    for axis, length in enumerate(mean.shape):
        minus, plus = list(location), list(location)
        minus[axis] = (minus[axis] - 1) % length
        plus[axis] = (plus[axis] + 1) % length
        low, high = float(mean[tuple(minus)]), float(mean[tuple(plus)])
        curvature = high + low - 2 * maximum
        offset = (low - high) / (2 * curvature) if curvature else 0.0
        result.append(location[axis] + (offset if abs(offset) <= 1.5 else 0.0))
    return np.array(result[::-1])


def finite_observer(raw: F64, options: dict[str, Any]) -> dict[str, Any]:
    """Observe contract equations with dense finite bases and real linear maps.

    This oracle has no cleanup/origin implementation: those options have smaller
    analytic mask/regression proofs below. Caller observations are float32 exact.
    """
    p, z, n, _ = raw.shape
    corrected = raw.copy()
    corner = corrected[:, :, -1, -1]
    corner[:] = np.where(corner < 0, corrected[:, :, -1, -2], corner)
    exposure = options.get("exposure_background_counts")
    camera = options.get("background_map")
    if exposure is not None:
        backgrounds, policy = np.asarray(exposure, dtype=float), "exposure"
    elif camera is not None:
        corrected = (corrected - camera) * options["slope_map"]
        backgrounds, policy = np.zeros((z, p)), "maps"
    elif options.get("background_counts") is not None:
        backgrounds = np.full((z, p), options["background_counts"])
        policy = "scalar"
    else:
        indices = np.arange(n)
        border = (indices < 20) | (indices > n - 20)
        backgrounds = corrected[:, :, border, :][:, :, :, border].mean(axis=(-2, -1)).T
        policy = "auto"
    # E=I+D and D annihilates constants. Form endpoint-relative differences
    # before dense multiplication so exact constant-region ties stay exact.
    d = edge_matrix(n) - np.eye(n)
    treated = corrected + np.einsum("ay,pzyx->pzax", d, corrected - corrected[:, :, :1, :])
    treated = treated + np.einsum("bx,pzyx->pzyb", d, treated - treated[:, :, :, :1])
    center = centered_peak(treated.mean(axis=0))
    treated -= backgrounds.T[:, :, None, None]
    phases = 2 * pi * np.arange(p) / p
    rows = [np.ones(p)]
    for m in range(1, (p + 1) // 2):
        rows.extend((np.cos(m * phases), np.sin(m * phases)))
    spatial = np.einsum("sp,pzyx->szyx", np.array(rows) / p, treated)
    qy = np.arange(n)
    qy = np.where(qy <= n // 2, qy, qy - n)
    qz = np.arange(z)
    qz = np.where(qz <= z // 2, qz, qz - z)
    kx = np.arange(n // 2 + 1)
    bx = np.exp(-2j * pi * np.outer(kx, np.arange(n)) / n)
    by = np.exp(-2j * pi * np.outer(qy, np.arange(n)) / n)
    bz = np.exp(-2j * pi * np.outer(qz, np.arange(z)) / z)
    transformed = np.einsum("az,by,cx,szyx->scba", bz, by, bx, spatial, optimize=True)
    phase = np.exp(
        2j
        * pi
        * (
            kx[:, None, None] * center[0] / n
            + qy[None, :, None] * center[1] / n
            + qz[None, None, :] * center[2] / z
        )
    )
    transformed *= phase
    minimum_sphere = 1.0
    if options.get("compensate_bead", False):
        dkr, dkz = 1 / (n * options["dxy_um"]), 1 / (z * options["dz_um"])
        for slot in range(p):
            m = (slot + 1) // 2
            shift = m / (((p - 1) // 2) * options["linespacing_um"])
            theta = options.get("carrier_angle_rad", 0.0)
            rho = np.sqrt(
                (kx[:, None, None] * dkr + shift * cos(theta)) ** 2
                + (qy[None, :, None] * dkr + shift * sin(theta)) ** 2
                + (qz[None, None, :] * dkz) ** 2
            )
            u = pi * options.get("bead_diameter_um", 0.12) * rho
            sphere = np.ones_like(u)
            mask = u != 0
            sphere[mask] = 3 * (np.sin(u[mask]) - u[mask] * np.cos(u[mask])) / u[mask] ** 3
            minimum_sphere = min(minimum_sphere, float(np.min(np.abs(sphere))))
            transformed[slot] /= sphere
    radial = np.zeros((p, n // 2 + 1, z), dtype=np.complex128)
    radius = np.rint(np.hypot(kx[:, None], qy[None, :])).astype(int)
    for r in range(n // 2 + 1):
        selected = radius == r
        if np.any(selected):
            radial[:, r] = transformed[:, selected, :].mean(axis=1)
    # Orthogonal projection onto conjugate axial pairs, including real endpoints.
    partner = (-np.arange(z)) % z
    radial = (radial + radial[:, :, partner].conj()) / 2
    if options.get("fix_axial_axis", False):
        radial[:, 0] = radial[:, 1]
        radial[0, 0, 0] = transformed[0, 0, 0, 0].real
    start = options.get("fix_radial_from", 0)
    if start > 0:
        radial[:, start:, 0] = (radial[:, start:, 1] + radial[:, start:, -1]) / 2
    maxima = np.max(np.abs(radial), axis=(1, 2))
    factors = 1 / (maxima if options.get("rescale_each", False) else np.full(p, maxima[0]))
    radial *= factors[:, None, None]
    combined = [radial[0]]
    angles = []
    for m in range(1, (p + 1) // 2):
        c, s = radial[2 * m - 1 : 2 * m + 1]
        angle = atan(float(np.abs(s).sum() / np.abs(c).sum()))
        cv, sv = c[n // 8, 0].real, s[n // 8, 0].real
        if cv < 0 < sv:
            angle += pi
        elif cv < 0 and sv < 0:
            angle = pi - angle
        elif cv > 0 and sv > 0:
            angle = -angle
        if m == 1 and options.get("forced_pi_shift", False):
            angle = pi - angle
        angles.append(angle)
        combined.append(c * cos(angle) - s * sin(angle))
    combined_array = np.array(combined)
    if options.get("conjugate", False):
        combined_array = combined_array.conj()
    # Forward absolute error, propagated through division, scale, and angle.
    l1 = float(np.abs(treated).sum())
    budget = EPS * (256 * z * n * n + 1024) * max(1.0, l1) / minimum_sphere
    raw_budget = budget
    budget *= float(np.max(factors)) * 64
    angle_condition = 1.0
    for m in range(1, (p + 1) // 2):
        a = float(np.abs(radial[2 * m - 1]).sum())
        b = float(np.abs(radial[2 * m]).sum())
        angle_condition = max(angle_condition, radial[0].size * (a + b) / a**2)
    return {
        "quadratures": radial,
        "samples": combined_array,
        "center": center,
        "backgrounds": backgrounds,
        "phases": phases,
        "factors": factors,
        "angles": np.array(angles),
        "budget": budget,
        "budgets": {
            "quadratures": budget,
            "factors": raw_budget * float(np.max(factors)) ** 2 * 4,
            "angles": budget * angle_condition,
            "phases": EPS * 128 * p,
            "backgrounds": EPS * 256 * n * n * max(1.0, float(np.abs(raw).max())),
        },
        "policy": policy,
    }


def assert_prepared(raw: F64, options: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    expected = finite_observer(raw, options)
    saved = raw.copy()
    actual = api("prepare_bead_otf")(raw, **options)
    for name, key in (
        ("quadratures", "quadratures"),
        ("normalization_factors", "factors"),
        ("quadrature_angles_rad", "angles"),
        ("phase_angles_rad", "phases"),
        ("background_counts", "backgrounds"),
    ):
        np.testing.assert_allclose(
            getattr(actual, name), expected[key], rtol=0, atol=expected["budgets"][key]
        )
    np.testing.assert_allclose(
        actual.transfer.samples, expected["samples"], rtol=0, atol=expected["budget"]
    )
    # Curvatures of these fixtures exceed 1 count; this bounds local-fit error.
    center_bound = EPS * 128 * max(1.0, float(np.abs(raw).max())) * 16
    np.testing.assert_allclose(
        actual.center_pixels_xyz, expected["center"], rtol=0, atol=center_bound
    )
    np.testing.assert_array_equal(raw, saved)
    return actual, expected


def declared(layout: str = "radial", orders: int = 2) -> tuple[Any, C128]:
    shape = (orders, 4, 5) if layout == "radial" else (orders, 3, 4, 4)
    index = np.arange(np.prod(shape)).reshape(shape)
    values = (1 + index**2 + 3 * (index % 7) + 1j * (3 - 2 * index + (index % 5) ** 2)).astype(
        np.complex128
    )
    transfer = api("declare_otf")(values, layout=layout, dkr_cyc_um=0.5, dkz_cyc_um=0.25)
    return transfer, values


def close_sample(actual: Any, expected: Any, values: C128) -> None:
    budget = 256 * EPS * max(1.0, float(np.abs(values).max()))
    np.testing.assert_allclose(actual, expected, rtol=0, atol=budget)


def test_raw_bead_to_prepare_transfer_to_sample_finite_sum() -> None:
    raw = bead()
    actual, expected = assert_prepared(raw, settings())
    # r=1.25, axial table index=1.5, order2: four independently known cells.
    table = expected["samples"][2]
    value = (3 * table[1, 1] + 3 * table[1, 2] + table[2, 1] + table[2, 2]) / 8
    sampled = api("sample_otf")(actual.transfer, 1.25 / 6, 0, 3, dkz_cyc_um=0.2, order=2)
    np.testing.assert_allclose(sampled, value, rtol=0, atol=expected["budget"] * 2)
    assert sampled.shape == () and sampled.dtype == np.complex128
    # Closed-form local parabola: unequal neighbours fix fractional centers.
    np.testing.assert_allclose(
        actual.center_pixels_xyz,
        [11 + 1 / 14, 12 - 1 / 16, 1 + 1 / 16],
        rtol=0,
        atol=EPS * 128 * float(raw.max()) * 16,
    )
    assert np.max(np.abs(expected["quadratures"].imag)) > 1e-5
    assert not np.allclose(
        expected["samples"][1], expected["quadratures"][1] + 1j * expected["quadratures"][2]
    )


@pytest.mark.parametrize("corner", [-7.0, -1.0, -0.25, 0.0, 3.0])
def test_negative_corner_and_nonnegative_preservation(corner: float) -> None:
    raw = bead()
    raw[:, :, -1, -1] = corner
    raw[:, :, -1, -2] = 2
    assert_prepared(raw, settings())


@pytest.mark.parametrize("policy", ["exposure", "maps", "scalar", "auto"])
def test_background_precedence_all_supplied_values_validated(policy: str) -> None:
    raw = bead()
    background = np.full((24, 24), 0.25)
    slope = np.full((24, 24), -0.5)
    options = settings(background_counts=None)
    if policy != "auto":
        options["background_counts"] = 1.25
    if policy in {"exposure", "maps"}:
        options.update(background_map=background, slope_map=slope)
    if policy == "exposure":
        options["exposure_background_counts"] = np.arange(25).reshape(5, 5) / 4 - 3
    actual, expected = assert_prepared(raw, options)
    np.testing.assert_array_equal(actual.background_counts, expected["backgrounds"])
    np.testing.assert_array_equal(background, np.full((24, 24), 0.25))
    np.testing.assert_array_equal(slope, np.full((24, 24), -0.5))
    if policy == "maps":
        # Camera correction leaves boundary/first-maximum neighbours at .125;
        # both edge differences and all three parabolic offsets are exactly0.
        np.testing.assert_array_equal(actual.center_pixels_xyz, [0, 0, 0])
    if policy == "scalar":
        q0 = expected["quadratures"][0]
        assert float(np.max(np.abs(q0))) > 1.1 * abs(q0[0, 0])
    # The vocabulary is not prescribed, but selection must be recorded.
    assert "background_policy" in dict(actual.resolved_settings)


@pytest.mark.parametrize("n", [10, 14, 20, 44])
def test_fixed10_overlap_and_auto_strict_corner_intersection(n: int) -> None:
    raw = np.ones((1, 3, n, n), dtype=np.float64)
    # Peak safely below y=20; distinguish strict high boundary at n-20.
    raw[0, 1, 3, 4] = 5000
    raw[0, 0, 0, :] = np.arange(n) + 2
    raw[0, 2, :, -1] = 5
    if n == 44:
        raw[0, 0, 24, 0] = 200  # y==N-20 excluded
        raw[0, 0, 25, 0] = 70  # y>N-20 included
        raw[0, 0, 0, 22] = 300  # perimeter-only point excluded
    assert_prepared(raw, settings(background_counts=None))


@pytest.mark.parametrize(
    "kind", ["tie", "nonpositive", "zero_curvature", "asymmetric_nonpositive", "negative_fraction"]
)
def test_center_finite_decisions_and_periodic_neighbors(kind: str) -> None:
    raw = np.zeros((1, 3, 24, 24), dtype=np.float64)
    if kind == "tie":
        raw[0, 1, 11, 11] = raw[0, 1, 12, 12] = 10
        center = [11, 11, 1]
    elif kind == "nonpositive":
        raw[:] = -2
        raw[:, :, -1, -1] = 0  # avoid corner substitution changing uniform plane
        center = None
    elif kind == "zero_curvature":
        raw[:] = 2
        center = [0, 0, 0]
    elif kind == "asymmetric_nonpositive":
        raw[:] = -4
        raw[0, 0, 0, 1] = -1
        raw[0, -1, 0, 0] = -20
        center = None
    else:
        raw[0, 0, 11, 11] = 20
        raw[0, -1, 11, 11] = 8
        raw[0, 1, 11, 11] = 2
        center = [11, 11, -0.1]
    actual, _ = assert_prepared(raw, settings(background_counts=3))
    if kind == "zero_curvature":
        np.testing.assert_array_equal(actual.center_pixels_xyz, [0, 0, 0])
    elif center is not None:
        np.testing.assert_allclose(actual.center_pixels_xyz, center, rtol=0, atol=EPS * 4096)


@pytest.mark.parametrize("p", [1, 3, 5, 7, 9])
def test_all_odd_phase_counts_and_lateral_nyquist(p: int) -> None:
    raw = bead(p=p)
    # An exact alternating detector component reaches lateral Nyquist.
    raw[:, 0, 11, 10:14] += np.array([1, -1, 1, -1])
    assert_prepared(raw, settings())


@pytest.mark.parametrize("z", [4, 5])
@pytest.mark.parametrize("theta", [0.0, 0.37])
def test_continuum_sphere_shift_both_quadratures_and_complex_axial_pairs(
    z: int, theta: float
) -> None:
    actual, expected = assert_prepared(
        bead(z=z), settings(compensate_bead=True, bead_diameter_um=0.12, carrier_angle_rad=theta)
    )
    h = actual.quadratures
    np.testing.assert_array_equal(h[:, :, 0].imag, 0)
    np.testing.assert_allclose(h[:, :, 1], h[:, :, -1].conj(), rtol=0, atol=expected["budget"])
    assert np.max(np.abs(h[:, :, 1].imag)) > 1e-6
    if z % 2 == 0:
        np.testing.assert_array_equal(h[:, :, z // 2].imag, 0)


def test_tiny_positive_sphere_has_no_arbitrary_cutoff() -> None:
    raw = bead()
    plain = api("prepare_bead_otf")(raw, **settings())
    tiny = api("prepare_bead_otf")(raw, **settings(compensate_bead=True, bead_diameter_um=2**-40))
    # |1-S| <= u^2/10 + O(u^4); here u<2^-35, below binary64 roundoff.
    bound = EPS * (256 * raw[0].size + 1024) * 16
    np.testing.assert_allclose(tiny.transfer.samples, plain.transfer.samples, rtol=0, atol=bound)


@pytest.mark.parametrize("axial,start", [(True, 0), (False, 2), (True, 2), (True, 40)])
def test_axis_repairs_order_dc_exception_and_large_start_noop(axial: bool, start: int) -> None:
    assert_prepared(bead(), settings(fix_axial_axis=axial, fix_radial_from=start))


@pytest.mark.parametrize(
    "each,forced,conjugate",
    [(False, False, False), (True, False, False), (False, True, False), (True, True, True)],
)
def test_common_or_each_scale_angle_and_first_order_pi_conjugation(
    each: bool, forced: bool, conjugate: bool
) -> None:
    actual, expected = assert_prepared(
        bead(), settings(rescale_each=each, forced_pi_shift=forced, conjugate=conjugate)
    )
    if each:
        np.testing.assert_allclose(
            np.max(np.abs(actual.quadratures), axis=(1, 2)), 1, rtol=0, atol=expected["budget"]
        )
    else:
        np.testing.assert_array_equal(
            actual.normalization_factors, np.repeat(actual.normalization_factors[0], 5)
        )
        assert np.max(np.abs(actual.quadratures[1])) < 0.5


@pytest.mark.parametrize("amplitudes", [[10, 12, 4], [10, 4, 12], [4, 12, 8], [4, 8, 12]])
def test_quadrature_sign_quadrants(amplitudes: list[int]) -> None:
    shape = bead(p=1)[0] / 12
    raw = np.array(amplitudes)[:, None, None, None] * shape
    assert_prepared(raw, settings())


def test_origin_regression_real_axial_sums_only() -> None:
    raw = bead()
    plain = api("prepare_bead_otf")(raw, **settings())
    fixed = api("prepare_bead_otf")(raw, **settings(origin_fit_bins=(2, 4)))
    # Recover pre-scale values through public diagnostic factors. This relation
    # proves repair placement, not absolute Fourier accuracy (composition does).
    before = plain.quadratures / plain.normalization_factors[:, None, None]
    after = fixed.quadratures / fixed.normalization_factors[:, None, None]
    expected = before.copy()
    totals = before[0].real.sum(axis=1)
    mean = (totals[2] + totals[3] + totals[4]) / 3
    slope = (totals[4] - totals[2]) / 2
    expected[0, 0, 0] += -before[0, 0, 0].real + mean - 3 * slope
    expected[0, 1, 0] += -totals[1] + mean - 2 * slope
    bound = EPS * (256 * raw[0].size + 1024) * np.abs(before).sum() * 16
    np.testing.assert_allclose(after, expected, rtol=0, atol=bound)


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_declare_complete_owned_complex_tables_no_normalization(layout: str) -> None:
    transfer, values = declared(layout)
    saved = values.copy()
    assert transfer.layout == layout and transfer.norders == 2
    assert transfer.dkr_cyc_um == 0.5 and transfer.dkz_cyc_um == 0.25
    assert transfer.samples.dtype == np.complex128
    assert transfer.samples.flags.owndata and not transfer.samples.flags.writeable
    np.testing.assert_array_equal(transfer.samples, saved)
    values[:] = 0
    np.testing.assert_array_equal(transfer.samples, saved)
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        transfer.layout = "other"
    with pytest.raises(ValueError):
        transfer.samples.flat[0] = 9


def test_radial_bilinear_imaginary_values_seam_and_one_wrap() -> None:
    transfer, values = declared()
    query = api("sample_otf")
    expected = (3 * values[1, 1, 1] + 3 * values[1, 1, 2] + values[1, 2, 1] + values[1, 2, 2]) / 8
    close_sample(query(transfer, 0.625, 0, 3, dkz_cyc_um=0.125, order=1), expected, values)
    seam = (values[0, 1, 4] + values[0, 1, 0]) / 2
    close_sample(query(transfer, 0.5, 0, -1, dkz_cyc_um=0.125), seam, values)
    close_sample(query(transfer, 0.3, 0.4, 0, dkz_cyc_um=0.25), values[0, 1, 0], values)


def test_radial_safe_flat_aliases_and_zero_weight_vertices() -> None:
    transfer, values = declared()
    query = api("sample_otf")
    flat = values[0].ravel()
    # K=5: -6 adds5 once -> -1, not4; r=1 means flat index4.
    close_sample(query(transfer, 0.5, 0, -6, dkz_cyc_um=0.25), flat[4], values)
    close_sample(query(transfer, 0, 0, 5, dkz_cyc_um=0.25), flat[5], values)
    # The nominal last radial row becomes safe when its axial alias is negative.
    close_sample(query(transfer, 1.5, 0, -11, dkz_cyc_um=0.25), flat[9], values)
    error = api("OtfError")
    for radius, axial in [(1.5, 0), (0, -6), (0, 15)]:
        with pytest.raises(error, match=".+"):
            query(transfer, radius, 0, axial, dkz_cyc_um=0.25)


def test_full_trilinear_both_seams_and_negative_x_reflects_all_axes() -> None:
    transfer, values = declared("full")
    query = api("sample_otf")
    expected = sum(values[1, z, y, x] for z in (2, 0) for y in (3, 0) for x in (1, 2)) / 8
    close_sample(query(transfer, 0.75, 1.75, -1, dkz_cyc_um=0.125, order=1), expected, values)
    reflected = sum(values[0, z, y, x] for z in (2, 0) for y in (3, 0) for x in (1, 2)) / 8
    close_sample(query(transfer, -0.75, 0.25, 1, dkz_cyc_um=0.125), reflected.conjugate(), values)
    # +0 and -0 must both retain original y,z, without conjugation.
    for zero in (0.0, -0.0):
        close_sample(query(transfer, zero, 0.5, 1, dkz_cyc_um=0.25), values[0, 1, 1, 0], values)


def test_full_signed_remainder_safe_alias_and_one_time_wrap() -> None:
    transfer, values = declared("full")
    query = api("sample_otf")
    flat = values[0].ravel()
    # Y=4, y=-6.5 -> add4=-2.5, j=-3, j1=-2 (C signed remainder).
    # z=1 ensures both negative-y stencils are inside the flat allocation.
    expected = (flat[5] + flat[9]) / 2
    close_sample(query(transfer, 0.5, -3.25, 1, dkz_cyc_um=0.25), expected, values)
    # x==X-1 still dereferences x+1, safely aliasing the next row here.
    close_sample(query(transfer, 1.5, 0, 0, dkz_cyc_um=0.25), flat[3], values)
    close_sample(query(transfer, 0, 2.0, 0, dkz_cyc_um=0.25), flat[16], values)
    with pytest.raises(api("OtfError"), match=".+"):
        query(transfer, 1.5, 1.5, 2, dkz_cyc_um=0.25)


def test_full_negative_axial_signed_remainder_and_positive_seam_alias() -> None:
    transfer, values = declared("full")
    flat = values[0].ravel()
    # t=-4.5 adds3 once: l=-2,l1=-1 under C remainder, fraction1/2.
    # x index33 offsets the negative plane indices into the actual allocation.
    expected = (flat[1] + flat[17]) / 2
    close_sample(api("sample_otf")(transfer, 16.5, 0, -9, dkz_cyc_um=0.125), expected, values)
    # Positive t==K is not wrapped; negative y makes all eight offsets safe.
    close_sample(api("sample_otf")(transfer, 0, -3, 3, dkz_cyc_um=0.25), flat[40], values)


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_query_broadcast_order_scalar_empty_and_whole_call_failure(layout: str) -> None:
    transfer, values = declared(layout)
    query = api("sample_otf")
    actual = query(
        transfer,
        np.array([[0], [0.25]]),
        np.array([0, 0.25, 0.5]),
        np.int64(1),
        dkz_cyc_um=0.25,
        order=np.int32(1),
    )
    assert actual.shape == (2, 3) and actual.dtype == np.complex128 and actual.flags.owndata
    for row in range(2):
        for column in range(3):
            scalar = query(transfer, row * 0.25, column * 0.25, 1, dkz_cyc_um=0.25, order=1)
            close_sample(actual[row, column], scalar, values)
    empty = query(transfer, np.empty((0, 1)), np.empty((1, 3)), np.int64(0), dkz_cyc_um=0.25)
    assert empty.shape == (0, 3) and empty.dtype == np.complex128 and empty.flags.owndata
    with pytest.raises(api("OtfError"), match=".+"):
        query(transfer, [0, 1e20], 0, 0, dkz_cyc_um=0.25)


def test_prepared_record_metadata_identity_ownership_and_immutability() -> None:
    raw = bead()
    actual = api("prepare_bead_otf")(raw, **settings())
    assert isinstance(actual, api("PreparedOtf"))
    assert isinstance(actual.transfer, api("OpticalTransfer"))
    assert actual.transfer.samples.shape == (3, 13, 5)
    assert actual.transfer.dkr_cyc_um == 1 / 6
    assert actual.transfer.dkz_cyc_um == 0.4
    assert actual.transfer.source_revision == "SVN307"
    assert actual.transfer.samples.flags.owndata
    assert not actual.transfer.samples.flags.writeable
    assert isinstance(actual.transfer.reference_sha256, tuple)
    hashes = dict(actual.transfer.reference_sha256)
    assert (
        hashes["mainfile.c"] == "b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8"
    )
    assert (
        hashes["small_math_funcs.c"]
        == "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"
    )
    assert hashes["helpers.c"] == "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"
    assert hashes["sirecon.c"] == "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"
    assert hashes["sirecon.h"] == "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"
    assert hashes["Makefile"] == "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"
    assert hashes["usr_local/include/sfftw.h"] == (
        "72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138"
    )
    assert hashes["usr_local/include/srfftw.h"] == (
        "d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a"
    )
    assert hashes["usr_local/include/fftw3.h"] == (
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d"
    )
    expected = {
        "center_pixels_xyz": ((3,), np.float64),
        "background_counts": ((5, 5), np.float64),
        "phase_angles_rad": ((5,), np.float64),
        "quadratures": ((5, 13, 5), np.complex128),
        "normalization_factors": ((5,), np.float64),
        "quadrature_angles_rad": ((2,), np.float64),
    }
    for name, (shape, dtype) in expected.items():
        array = getattr(actual, name)
        assert array.shape == shape and array.dtype == dtype
        assert array.flags.owndata and not array.flags.writeable
        assert not np.shares_memory(array, raw)
    assert isinstance(actual.resolved_settings, tuple)
    resolved = dict(actual.resolved_settings)
    for name, value in settings().items():
        assert resolved[name] == value
    for name in (
        "bead_diameter_um",
        "carrier_angle_rad",
        "cleanup_axial_bins",
        "origin_fit_bins",
        "numerical_aperture",
        "immersion_index",
        "rescale_each",
        "forced_pi_shift",
        "conjugate",
        "fix_radial_from",
        "background_policy",
    ):
        assert name in resolved
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        actual.transfer = None


@pytest.mark.parametrize("l12", [1, 0])
def test_cleanup_literal_masks_radial_cutoff_and_order_dependent_na(l12: int) -> None:
    raw = bead(p=7)
    options = settings(numerical_aperture=0.22)
    baseline = api("prepare_bead_otf")(raw, **options)
    cleaned = api("prepare_bead_otf")(raw, **(options | {"cleanup_axial_bins": (1, l12, 1)}))
    before = baseline.quadratures / baseline.normalization_factors[:, None, None]
    after = cleaned.quadratures / cleaned.normalization_factors[:, None, None]
    expected = before.copy()
    # lambda=.52, dkr=1/6, dkz=.4. For retained r, 0<=e<.08,
    # so j0=h=1. krmax0=.84615 (r5 in); krmax_side=.77846 (r5 out).
    expected[0, 6:] = 0
    expected[0, :6, 1:] = 0
    expected[1:, 5:] = 0
    expected[1:3, :5, 0] = 0  # order1: end=0
    if l12 == 0:
        expected[1:3, :5, 2:4] = 0  # start=1: j2 and partner3; keep j1,j4
    expected[3:, :5, 2:4] = 0  # all orders>=2: start=2, including order3
    bound = EPS * (256 * raw[0].size + 1024) * max(1, np.abs(before).sum()) * 16
    np.testing.assert_allclose(after, expected, rtol=0, atol=bound)

    # Independent seven-observation finite sum after conjugate axial projection:
    # the paired lateral exponentials give cos, with only the axial phase left.
    points = np.array(
        [
            [11, 12, 1, 100],
            [10, 12, 1, 20],
            [12, 12, 1, 40],
            [11, 11, 1, 30],
            [11, 13, 1, 10],
            [11, 12, 0, 10],
            [11, 12, 2, 30],
        ],
        dtype=np.float64,
    )
    center = np.array([11 + 1 / 14, 12 - 1 / 16, 1 + 1 / 16])
    ring = np.array([[0, -2], [0, 2], [1, -2], [1, 2], [2, -1], [2, 0], [2, 1]])
    lateral = np.cos(2 * pi * (ring @ (points[:, :2] - center[:2]).T) / 24).mean(axis=0)
    axial = np.exp(-2j * pi * (points[:, 2, None] - center[2]) * np.array([1, 2, -1]) / 5)
    phase_weight = (
        np.sum(np.array([12, 20, 10, 6, 8, 14, 18]) * np.cos(2 * pi * np.arange(7) / 7)) / 7
    )
    cells = phase_weight * np.sum(points[:, 3, None] * lateral[:, None] * axial, axis=0)
    cell_bound = EPS * (256 * raw[0].size + 1024) * np.abs(raw).sum() * 16
    np.testing.assert_allclose(before[1, 2, [1, 2, 4]], cells, rtol=0, atol=cell_bound)
    np.testing.assert_allclose(after[1, 2, [1, 4]], cells[[0, 2]], rtol=0, atol=cell_bound)
    if l12 == 0:
        np.testing.assert_array_equal(after[1:3, :5, 2:4], 0)
    else:
        # The original permitted empty-upper-loop control retains this cell.
        np.testing.assert_allclose(after[1, 2, 2], cells[1], rtol=0, atol=cell_bound)


def test_cleanup_bypass_ignores_other_bins_and_safe_flat_cross_row_write() -> None:
    raw = bead()
    plain = api("prepare_bead_otf")(raw, **settings())
    bypass = api("prepare_bead_otf")(raw, **settings(cleanup_axial_bins=(0, 2**31 - 1, 2**31 - 1)))
    np.testing.assert_array_equal(plain.transfer.samples, bypass.transfer.samples)
    # Z5,l11=6: r0 h1,end5 writes flat5=(r1,z0). At dz10, r1 e=12.05565,
    # h13,end=-7,start14: neither own-row loop can hide that cross-row write.
    unmasked = api("prepare_bead_otf")(raw, **settings(dz_um=10))
    actual = api("prepare_bead_otf")(raw, **settings(dz_um=10, cleanup_axial_bins=(6, 1, 1)))
    before = unmasked.quadratures / unmasked.normalization_factors[:, None, None]
    after = actual.quadratures / actual.normalization_factors[:, None, None]
    expected = before.copy()
    expected[0, 0, 1:] = 0  # order0 r0 j0=1
    expected[1:3, 0] = 0  # order1 r0 j0..5 and partners
    expected[1:3, 1, 0] = 0  # actual r0,j5 write crosses into row1
    expected[3:, 0, 2:4] = 0  # order2 r0 start=2
    # All r>=1 have no cleanup writes at these declared optics/dz settings.
    bound = EPS * (256 * raw[0].size + 1024) * np.abs(raw).sum() * 16
    np.testing.assert_allclose(after, expected, rtol=0, atol=bound)
    np.testing.assert_array_equal(after[1:3, 1, 0], 0)

    points = np.array(
        [
            [11, 12, 1, 100],
            [10, 12, 1, 20],
            [12, 12, 1, 40],
            [11, 11, 1, 30],
            [11, 13, 1, 10],
            [11, 12, 0, 10],
            [11, 12, 2, 30],
        ],
        dtype=np.float64,
    )
    center = np.array([11 + 1 / 14, 12 - 1 / 16, 1 + 1 / 16])
    ring = np.array([[0, -1], [0, 1], [1, -1], [1, 0], [1, 1]])
    lateral = np.cos(2 * pi * (ring @ (points[:, :2] - center[:2]).T) / 24).mean(axis=0)
    axial = np.exp(-2j * pi * (points[:, 2, None] - center[2]) * np.array([0, 1, -1]) / 5)
    phase_weight = np.sum(np.array([12, 20, 10, 6, 8]) * np.cos(2 * pi * np.arange(5) / 5)) / 5
    cells = phase_weight * np.sum(points[:, 3, None] * lateral[:, None] * axial, axis=0)
    np.testing.assert_allclose(before[1, 1, [0, 1, 4]], cells, rtol=0, atol=bound)
    np.testing.assert_allclose(after[1, 1, [1, 4]], cells[1:], rtol=0, atol=bound)
    assert np.isfinite(actual.transfer.samples).all()
    assert np.max(np.abs(actual.transfer.samples[1])) > 0


def test_zero_sign_angle_fallthrough_with_exact_zero_sine() -> None:
    # Only phase0 is nonzero: sin(m*0) is exactly0, cos(m*0)=1.
    raw = bead()
    raw[1:] = 0
    actual, expected = assert_prepared(raw, settings())
    np.testing.assert_array_equal(actual.quadratures[2::2], 0)
    np.testing.assert_array_equal(actual.quadrature_angles_rad, 0)
    np.testing.assert_allclose(
        actual.transfer.samples[1:], actual.quadratures[1::2], rtol=0, atol=expected["budget"]
    )


def test_public_compatibility_names_remain_and_no_binary_proof_claim() -> None:
    for name in (
        "inspect",
        "read",
        "harmonize",
        "write",
        "declare_acquisition",
        "export_imagej",
        "prepare_bands",
    ):
        assert callable(getattr(sr, name))
    # This is a boundary guard; detailed neutral behavior belongs to its frozen
    # suites. These mathematical tests neither execute C nor prove binary parity.
    assert not hasattr(sr, "reconstruct")
    assert not hasattr(sr, "prepare_otf")
    assert find_spec("simrecon._otf") is None


def test_cleanup_cutoff_equality_is_retained() -> None:
    raw = bead()
    settings_at_boundary = settings(numerical_aperture=0.26)
    plain = api("prepare_bead_otf")(raw, **settings_at_boundary)
    cleaned = api("prepare_bead_otf")(
        raw, **(settings_at_boundary | {"cleanup_axial_bins": (1, 1, 1)})
    )
    before = plain.quadratures / plain.normalization_factors[:, None, None]
    after = cleaned.quadratures / cleaned.normalization_factors[:, None, None]
    # 2*.26/.52 == 1 cycle/um; r6*dkr==1. The strict > cutoff keeps r6,z0.
    assert abs(before[0, 6, 0]) > 1
    bound = EPS * (256 * raw[0].size + 1024) * np.abs(before).sum() * 16
    np.testing.assert_allclose(after[0, 6, 0], before[0, 6, 0], rtol=0, atol=bound)
    np.testing.assert_array_equal(after[0, 7:], 0)


@pytest.mark.parametrize("p", [1, 3, 5, 7, 9])
def test_displaced_single_observation_closed_form_phase_division(p: int) -> None:
    raw = np.zeros((p, 3, 24, 24))
    raw[0, 1, 11, 11] = 9
    actual = api("prepare_bead_otf")(raw, **settings())
    # Delta at an interior pixel: edge is identity, center is exact, negative
    # Fourier phase cancels positive centering. Each C slot is 9/P, each S=0.
    # Thus normalized tables are1 and the inverse maximum is P/9 counts^-1.
    bound = EPS * 512 * raw[0].size
    np.testing.assert_allclose(actual.transfer.samples, 1, rtol=0, atol=bound)
    np.testing.assert_allclose(actual.normalization_factors, p / 9, rtol=0, atol=bound / 9)
    np.testing.assert_array_equal(actual.center_pixels_xyz, [11, 11, 1])
    if p > 1:
        np.testing.assert_array_equal(actual.quadratures[2::2], 0)
        np.testing.assert_array_equal(actual.quadrature_angles_rad, 0)
    sampled = api("sample_otf")(actual.transfer, 0.125, 0, -1, dkz_cyc_um=1 / 6)
    np.testing.assert_allclose(sampled, 1, rtol=0, atol=bound)
