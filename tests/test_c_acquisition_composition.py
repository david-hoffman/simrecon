"""Real raw/layout/camera/metadata -> bands -> actual estimates -> known image."""

from copy import copy
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    certified_pi,
    close,
    disc_empty,
    known_options,
    lift,
    matrix,
    one_time,
    optics,
    options,
    overlaps,
    prepare_expected,
    raw_pattern,
    reconstruct_expected,
    regression,
    transfer,
    transform,
)
from c_acquisition_fixture import (
    numerical_case as numerical_case,
)


def independent_factors(bands: Any, table: Any, carriers: Any, **op: Any) -> Any:
    tcount, dcount, _, _, _, _ = bands.input_shape
    o = bands.noise_variance_factors.shape[-1]
    result = disc_empty((tcount, dcount, o - 1), dtype=complex)
    for t, d in np.ndindex(tcount, dcount):
        for b in range(1, o):
            overlap = overlaps(bands, table, carriers[d], (0, b), t, d, **op)
            result[t, d, b - 1] = regression(overlap["spatial"], carriers[d], (0, b), bands.dxy_um)[
                "forward"
            ]
        if bands.acquisition_mode == "2d":
            result[t, d] = np.cumprod(result[t, d])
    return result


def composition(
    bands: Any, independent: Any, table: Any, carriers: Any, *, op: dict[str, Any] | None = None
) -> None:
    op = optics() if op is None else op
    factors = independent_factors(independent, table, carriers, **op)
    # Known controls FIRST, with independent factors fixed before observation.
    fixed = np.full((carriers.shape[0], factors.shape[-1]), 0.3 + 0.1j)
    control = api("reconstruct_known")(
        bands, table, carriers_cyc_um=carriers, modulation=fixed, **(known_options() | op)
    )
    control_truth = reconstruct_expected(
        independent, table, carriers, fixed, **(known_options() | op)
    )
    close(control.image, control_truth["image"])
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=carriers, search_carriers=False, **op
    )
    close(estimated.modulation, factors)
    np.testing.assert_array_equal(
        estimated.carriers_cyc_um, np.broadcast_to(carriers, estimated.carriers_cyc_um.shape)
    )
    for t in range(bands.input_shape[0]):
        actual = api("reconstruct_known")(
            one_time(bands, t),
            table,
            carriers_cyc_um=estimated.carriers_cyc_um[t],
            modulation=estimated.modulation[t],
            **(known_options() | op),
        )
        expected = reconstruct_expected(
            one_time(independent, t), table, carriers, factors[t], **(known_options() | op)
        )
        close(actual.image, expected["image"])


@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
@pytest.mark.parametrize("d,z", [(2, 2), (1, 3), (3, 1)])
def test_literal_reinterpret_unique_exposure_labels_and_real_composition(
    storage: str, d: int, z: int
) -> None:
    raw = raw_pattern(t=2, d=d, z=z, y=4, x=6)
    for t, di, p, h in np.ndindex(raw.shape[:4]):
        raw[t, di, p, h] += 1000 * t + 100 * di + 10 * h + p
    off = np.repeat((raw + 5)[..., None, :, :], 2, axis=4).astype(np.int16)
    extra = np.arange(2 * d * 3 * z, dtype=np.float32).reshape(2, d, 3, z) / np.float32(8)
    before = [v.copy() for v in [raw, off, extra]]
    helper = api("reinterpret_2d_planes")(
        raw, storage_order=storage, off_exposures=off, exposure_background=extra
    )
    expected = np.empty((2 * z, d, 3, 1, 4, 6))
    expected_off = np.empty((2 * z, d, 3, 1, 2, 4, 6), dtype=np.int16)
    expected_extra = np.empty((2 * z, d, 3, 1))
    source = np.empty((z, d, 2), dtype=np.int64)
    for q, di in np.ndindex(z, d):
        oldd, oldz = (di, q) if storage == "z-major" else divmod(q * d + di, z)
        source[q, di] = oldd, oldz
        for t in range(2):
            expected[t * z + q, di, :, 0] = raw[t, oldd, :, oldz]
            expected_off[t * z + q, di, :, 0] = off[t, oldd, :, oldz]
            expected_extra[t * z + q, di, :, 0] = extra[t, oldd, :, oldz]
    for observed, want in [
        (helper.images, expected),
        (helper.off_exposures, expected_off),
        (helper.exposure_background, expected_extra),
        (helper.source_direction_z, source),
    ]:
        np.testing.assert_array_equal(observed, want)
        assert observed.flags.owndata and not observed.flags.writeable
    for a, b in zip([raw, off, extra], before, strict=True):
        np.testing.assert_array_equal(a, b)
    assert helper.original_shape == raw.shape and helper.storage_order == storage
    assert helper.images.dtype == raw.dtype and helper.off_exposures.dtype == off.dtype
    assert extra.dtype == np.float32 and helper.exposure_background.dtype == np.float64
    if storage == "direction-major" and d == z == 2:
        np.testing.assert_array_equal(source, [[[0, 0], [0, 1]], [[1, 0], [1, 1]]])
        assert not np.array_equal(helper.images[0, 1, :, 0], raw[0, 1, :, 0])
    settings = options(
        storage_order=storage,
        off_exposures=helper.off_exposures,
        exposure_background=helper.exposure_background,
        equalize=True,
        equalize_time=True,
    )
    bands = api("prepare_acquisition_bands")(helper.images, **settings)
    truth = prepare_expected(expected, settings)
    independent = copy(bands)
    for field in ["quadratures", "noise_variance_factors"]:
        object.__setattr__(independent, field, truth[field])
        close(getattr(bands, field), truth[field])
    composition(bands, independent, transfer(), np.tile([0.05, 0.02], (d, 1)))


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("pitch", [1.0, 0.5])
def test_raw_on_off_camera_linked_phase_actual_estimator_final_signed_image(
    layout: str, pitch: float
) -> None:
    raw = np.zeros((1, 1, 4, 1, 10, 10))
    seed = np.zeros((10, 10))
    seed[3, 4] = 32
    seed[6, 2] = 7
    seed[4, 7] = 11
    shifts = [0, 1, -1, 2]
    for p in range(4):
        raw[0, 0, p, 0] = 2 + (p + 1) * np.roll(seed, shifts[p], axis=1)
    off = (2 * raw - 2)[..., None, :, :]
    phase = np.array([0.0, 9.0, 0.8, 10.0, 2.4, 11.0, 4.2, 12.0])
    clock = np.arange(8, dtype=float) + 10
    theta, spacing = 0.7, 5.0
    settings = options(
        dxy_um=pitch,
        off_exposures=off,
        background=2.0,
        flatfield_slope=np.full((10, 10), 2.0),
        header_timestamps=clock,
        header_phases_rad=phase,
        drift_within=True,
        adjust_phases=True,
        phase_start_angle_rad=theta,
        linespacing_um=spacing,
        lateral_zoom=1.5,
        axial_zoom=2,
    ) | optics(numerical_aperture=0.4)
    bands = api("prepare_acquisition_bands")(raw, **settings)
    # Analytic integer translations: all Fourier magnitudes are common up to
    # positive exposure amplitudes; autocorrelation peaks at the stated shift.
    expected_phase = phase[::2] + 2 * certified_pi() * pitch * np.cos(theta) / spacing * np.array(
        shifts
    )
    left, noise = matrix(expected_phase, 2, "drift")
    alpha = 1 / (100 * 1.5**2 * 2)
    on = transform(2 * alpha * (raw[0, 0, :, 0] - 2), axes=(1, 2))[..., :6]
    offsum = transform(2 * alpha * (off[0, 0, :, 0, 0] - 2), axes=(1, 2))[..., :6]
    yy, xx = np.meshgrid(lift(10), np.arange(6), indexing="ij")
    for p in range(4):
        ramp = np.exp(2j * certified_pi() * shifts[p] * xx / 10)
        on[p] *= ramp
        offsum[p] *= ramp
    separated = (left @ on.reshape(4, -1)).reshape(3, 10, 6)
    oseparated = (left @ offsum.reshape(4, -1)).reshape(3, 10, 6)
    separated[:, :, -1], oseparated[:, :, -1] = on[:3, :, -1], offsum[:3, :, -1]
    independent = copy(bands)
    object.__setattr__(independent, "quadratures", separated[None, None, :, None])
    object.__setattr__(independent, "noise_variance_factors", noise[None, None])
    close(
        bands.exposure_displacements_pixels[0, 0, 0, :, 0],
        shifts,
        proof=bands.exposure_displacements_pixels,
    )
    close(bands.phase_angles_rad[0, 0, 0], expected_phase, proof=bands.phase_angles_rad)
    close(bands.quadratures, independent.quadratures)
    close(bands.off_quadratures[0, 0, :, 0], oseparated, proof=bands.off_quadratures)
    composition(
        bands,
        independent,
        transfer(layout=layout, complex_values=True),
        np.array([[0.07, 0.03]]),
        op=optics(numerical_aperture=0.4),
    )


def test_useful_ordinary_d3_p5_o3_raw_estimate_known_compatibility() -> None:
    raw = raw_pattern(t=2, d=3, p=5, z=3, y=4, x=6)
    settings = options(acquisition_mode="3d", norders=3)
    bands = api("prepare_acquisition_bands")(raw, **settings)
    truth = prepare_expected(raw, settings)
    independent = copy(bands)
    for field in ["quadratures", "noise_variance_factors"]:
        object.__setattr__(independent, field, truth[field])
    composition(
        bands,
        independent,
        transfer(3, k=3, complex_values=True),
        np.array([[0.07, 0.02], [-0.03, 0.08], [0.04, -0.06]]),
    )


@pytest.mark.parametrize("between", [False, True])
def test_actual_3d_within_cubic_measured_between_sequence_to_estimate_and_image(
    between: bool,
) -> None:
    raw = np.zeros((1, 4, 3, 2, 10, 80))
    measured = np.array([0.0, 1.0, 8.0, 27.0])
    for d, p, z in np.ndindex(4, 3, 2):
        raw[0, d, p, z, 5, 20 + int(measured[d])] = 64
    off = raw[..., None, :, :].copy()
    prefix = np.array([10 + d + (p - 3) / 10 for d in range(4) for p in range(6)])
    clock = np.r_[prefix, np.arange(24) + 100.0]
    phases = np.arange(48, dtype=float) / 3
    theta, spacing = 0.37, 100.0
    settings = (
        options(
            acquisition_mode="3d",
            off_exposures=off,
            flatfield_slope=np.full((10, 80), 2.0),
            drift_within=True,
            drift_between=between,
            adjust_phases=True,
            header_timestamps=clock,
            header_phases_rad=phases,
            phase_start_angle_rad=theta,
            linespacing_um=spacing,
            negative_angle_step=True,
        )
        | optics()
    )
    bands = api("prepare_acquisition_bands")(raw, **settings)
    expected = disc_empty(bands.quadratures.shape, dtype=complex)
    noise = disc_empty(bands.noise_variance_factors.shape)
    dx = (prefix - 10).reshape(4, 2, 3) ** 3 - measured[:, None, None]
    yy, xx = np.meshgrid(lift(10), np.arange(41), indexing="ij")
    for d in range(4):
        for z in range(2):
            on = transform(2 * raw[0, d, :, z] / 6400, axes=(1, 2))[..., :41]
            for p in range(3):
                on[p] *= np.exp(2j * certified_pi() * dx[d, z, p] * xx / 80)
            phase = (
                2 * certified_pi() * np.arange(3) / 3
                + 2 * certified_pi() * np.cos(theta - d * certified_pi() / 4) / spacing * dx[d, z]
            )
            left, nv = matrix(phase, 2, "drift")
            section = (left @ on.reshape(3, -1)).reshape(3, 10, 41)
            section[:, :, -1] = on[:, :, -1]
            expected[0, d, :, z] = section
            if z == 1:
                noise[0, d] = nv
        expected[0, d] = transform(expected[0, d], axes=(1,))
        if between and d > 0:
            expected[0, d] *= np.exp(2j * certified_pi() * measured[d] * xx / 80)[None, None]
    independent = copy(bands)
    object.__setattr__(independent, "quadratures", expected)
    object.__setattr__(independent, "noise_variance_factors", noise)
    close(bands.quadratures, expected)
    composition(
        bands,
        independent,
        transfer(k=2, complex_values=True),
        np.array([[0.03, 0.02], [0.02, -0.03], [-0.04, 0.01], [0.01, 0.04]]),
    )


def test_new_record_ordinary_3d_search_pair02_divisor2_to_actual_image() -> None:
    from types import SimpleNamespace

    from c_acquisition_fixture import as_disc, certified_close, parameter_model

    raw = raw_pattern(t=2, d=3, p=5, z=3, y=4, x=6)
    prep = options(acquisition_mode="3d", norders=3)
    bands = api("prepare_acquisition_bands")(raw, **prep)
    expected = prepare_expected(raw, prep)
    independent = SimpleNamespace(
        **expected,
        input_shape=raw.shape,
        acquisition_mode="3d",
        dxy_um=1.0,
        dz_um=0.5,
        lateral_zoom=1.0,
        axial_zoom=1,
    )
    table = transfer(3, k=3, complex_values=True)
    initial = np.tile([0.15, 0.05], (3, 1))
    fixed = np.full((3, 2), 0.3 + 0.1j)
    control = api("reconstruct_known")(
        bands, table, carriers_cyc_um=initial, modulation=fixed, **known_options()
    )
    certified_close(
        control.image,
        reconstruct_expected(
            independent, table, as_disc(initial), as_disc(fixed), **known_options()
        )["image"],
    )
    truth = parameter_model(independent, table, initial_carriers_cyc_um=initial, **optics())
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=initial, **optics()
    )
    certified_close(estimated.carriers_cyc_um, truth.carriers_cyc_um)
    certified_close(estimated.modulation, truth.modulation)
    assert [build.orders for build in estimated.overlaps if build.purpose == "coarse"] == [
        (0, 2)
    ] * 3
    for t in range(2):
        actual = api("reconstruct_known")(
            one_time(bands, t),
            table,
            carriers_cyc_um=estimated.carriers_cyc_um[t],
            modulation=estimated.modulation[t],
            **known_options(),
        )
        model = copy(independent)
        model.input_shape = (1, *raw.shape[1:])
        model.quadratures = independent.quadratures[t : t + 1]
        model.noise_variance_factors = independent.noise_variance_factors[t : t + 1]
        certified_close(
            actual.image,
            reconstruct_expected(
                model, table, truth.carriers_cyc_um[t], truth.modulation[t], **known_options()
            )["image"],
        )


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)])
def test_selected_off_combination_c4_into_actual_fit_and_image(mode: str, z: int) -> None:
    from c_acquisition_fixture import events

    raw = raw_pattern(d=2, z=z, y=10, x=10)
    off = (np.roll(raw, 1, axis=-1) + np.roll(raw, 2, axis=-2) + 3)[..., None, :, :].copy()
    prep = options(
        acquisition_mode=mode,
        dxy_um=0.1,
        off_exposures=off,
        combine_off_orders=np.array([1, 1], dtype=np.int32),
    ) | optics(wavelength_nm=500, numerical_aperture=1.0)
    truth = prepare_expected(raw, prep)
    bands = api("prepare_acquisition_bands")(raw, **prep)
    for event in events(bands, "off-combination"):
        assert event["cutoff_integer"] == 4
        assert event["inside_count"] == 29 and event["outside_count"] == 31
    independent = copy(bands)
    for key in ["quadratures", "noise_variance_factors"]:
        object.__setattr__(independent, key, truth[key])
        close(getattr(bands, key), truth[key])
    # dxy.1 makes the native grid ten times wider; table spacing1 keeps all
    # actually requested vertices interior without changing its raw values.
    samples = np.ones((2, 32, z), dtype=complex)
    table = api("declare_otf")(samples, layout="radial", dkr_cyc_um=1.0, dkz_cyc_um=2.0)
    composition(
        bands,
        independent,
        table,
        np.array([[0.3, 0.1], [-0.2, 0.25]]),
        op=optics(wavelength_nm=500, numerical_aperture=1.0),
    )


@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
def test_literal_helper_effective_time0_search_reuse_refits_modulation(storage: str) -> None:
    from types import SimpleNamespace

    from c_acquisition_fixture import certified_close, parameter_model

    raw = raw_pattern(t=1, d=2, p=3, z=2, y=4, x=6)
    helper = api("reinterpret_2d_planes")(raw, storage_order=storage)
    expected_images = np.empty((2, 2, 3, 1, 4, 6))
    for q, di in np.ndindex(2, 2):
        old_d, old_z = (di, q) if storage == "z-major" else divmod(q * 2 + di, 2)
        expected_images[q, di, :, 0] = raw[0, old_d, :, old_z]
    np.testing.assert_array_equal(helper.images, expected_images)
    prep = options(storage_order=storage)
    bands = api("prepare_acquisition_bands")(helper.images, **prep)
    truth = prepare_expected(expected_images, prep)
    independent = SimpleNamespace(
        **truth,
        input_shape=helper.images.shape,
        acquisition_mode="2d",
        dxy_um=1.0,
        dz_um=0.5,
        lateral_zoom=1.0,
        axial_zoom=1,
    )
    table = transfer()
    initial = np.tile([0.15, 0.05], (2, 1))
    # Known control precedes the actual search/reuse composition.
    composition(bands, independent, table, initial)
    expected = parameter_model(independent, table, initial_carriers_cyc_um=initial, **optics())
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=initial, **optics()
    )
    assert estimated.branches == (("searched", "searched"), ("time0-reused", "time0-reused"))
    np.testing.assert_array_equal(estimated.carriers_cyc_um[0], estimated.carriers_cyc_um[1])
    certified_close(estimated.carriers_cyc_um, expected.carriers_cyc_um)
    certified_close(estimated.modulation, expected.modulation)
    assert np.max(abs(np.asarray(expected.modulation[1] - expected.modulation[0]))) > np.max(
        (expected.modulation[1] - expected.modulation[0]).error
    )
    for t in range(2):
        image = api("reconstruct_known")(
            one_time(bands, t),
            table,
            carriers_cyc_um=estimated.carriers_cyc_um[t],
            modulation=estimated.modulation[t],
            **known_options(),
        )
        model = copy(independent)
        model.input_shape = (1, *helper.images.shape[1:])
        model.quadratures = independent.quadratures[t : t + 1]
        model.noise_variance_factors = independent.noise_variance_factors[t : t + 1]
        certified_close(
            image.image,
            reconstruct_expected(
                model, table, expected.carriers_cyc_um[t], expected.modulation[t], **known_options()
            )["image"],
        )
