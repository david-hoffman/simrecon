"""Real raw/layout/camera/metadata -> bands -> actual estimates -> known image."""

from copy import copy
from math import pi
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    close,
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


def independent_factors(bands: Any, table: Any, carriers: Any, **op: Any) -> Any:
    tcount, dcount, _, _, _, _ = bands.input_shape
    o = bands.noise_variance_factors.shape[-1]
    result = np.empty((tcount, dcount, o - 1), dtype=complex)
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
    scale = float(np.sum(abs(independent.quadratures)))
    work = int(np.prod(independent.input_shape[-3:]))
    close(control.image, control_truth["image"], work=work, scale=scale, condition=256)
    estimated = api("estimate_parameters")(
        bands, table, initial_carriers_cyc_um=carriers, search_carriers=False, **op
    )
    close(estimated.modulation, factors, work=work, scale=8, condition=256)
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
        close(actual.image, expected["image"], work=work, scale=scale, condition=512)


@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
@pytest.mark.parametrize("d,z", [(2, 2), (1, 3), (3, 1)])
def test_literal_reinterpret_unique_exposure_labels_and_real_composition(
    storage: str, d: int, z: int
) -> None:
    raw = raw_pattern(t=2, d=d, z=z, y=4, x=6)
    for t, di, p, h in np.ndindex(raw.shape[:4]):
        raw[t, di, p, h] += 1000 * t + 100 * di + 10 * h + p
    off = np.repeat((raw + 5)[..., None, :, :], 2, axis=4).astype(np.int16)
    extra = np.arange(2 * d * 3 * z, dtype=float).reshape(2, d, 3, z) / 8
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
        close(
            getattr(bands, field),
            truth[field],
            work=raw.size,
            scale=float(np.sum(abs(raw))),
            condition=16,
        )
    composition(bands, independent, transfer(), np.tile([0.05, 0.02], (d, 1)))


@pytest.mark.parametrize("layout", ["radial", "full"])
def test_raw_on_off_camera_linked_phase_actual_estimator_final_signed_image(layout: str) -> None:
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
    expected_phase = phase[::2] + 2 * pi * np.cos(theta) / spacing * np.array(shifts)
    left, noise = matrix(expected_phase, 2, "drift")
    alpha = 1 / (100 * 1.5**2 * 2)
    on = transform(2 * alpha * (raw[0, 0, :, 0] - 2), axes=(1, 2))[..., :6]
    offsum = transform(2 * alpha * (off[0, 0, :, 0, 0] - 2), axes=(1, 2))[..., :6]
    yy, xx = np.meshgrid(lift(10), np.arange(6), indexing="ij")
    for p in range(4):
        ramp = np.exp(2j * pi * shifts[p] * xx / 10)
        on[p] *= ramp
        offsum[p] *= ramp
    separated = (left @ on.reshape(4, -1)).reshape(3, 10, 6)
    oseparated = (left @ offsum.reshape(4, -1)).reshape(3, 10, 6)
    separated[:, :, -1], oseparated[:, :, -1] = on[:3, :, -1], offsum[:3, :, -1]
    independent = copy(bands)
    object.__setattr__(independent, "quadratures", separated[None, None, :, None])
    object.__setattr__(independent, "noise_variance_factors", noise[None, None])
    close(
        bands.exposure_displacements_pixels[0, 0, 0, :, 0], shifts, work=100, scale=2, condition=128
    )
    close(bands.phase_angles_rad[0, 0, 0], expected_phase, work=100, scale=8, condition=128)
    close(
        bands.quadratures,
        independent.quadratures,
        work=100,
        scale=float(np.sum(abs(raw))),
        condition=256,
    )
    close(
        bands.off_quadratures[0, 0, :, 0],
        oseparated,
        work=100,
        scale=float(np.sum(abs(raw))),
        condition=256,
    )
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
    expected = np.empty_like(bands.quadratures)
    noise = np.empty_like(bands.noise_variance_factors)
    dx = (prefix - 10).reshape(4, 2, 3) ** 3 - measured[:, None, None]
    yy, xx = np.meshgrid(lift(10), np.arange(41), indexing="ij")
    for d in range(4):
        for z in range(2):
            on = transform(2 * raw[0, d, :, z] / 6400, axes=(1, 2))[..., :41]
            for p in range(3):
                on[p] *= np.exp(2j * pi * dx[d, z, p] * xx / 80)
            phase = (
                2 * pi * np.arange(3) / 3 + 2 * pi * np.cos(theta - d * pi / 4) / spacing * dx[d, z]
            )
            left, nv = matrix(phase, 2, "drift")
            section = (left @ on.reshape(3, -1)).reshape(3, 10, 41)
            section[:, :, -1] = on[:, :, -1]
            expected[0, d, :, z] = section
            if z == 1:
                noise[0, d] = nv
        expected[0, d] = transform(expected[0, d], axes=(1,))
        if between and d > 0:
            expected[0, d] *= np.exp(2j * pi * measured[d] * xx / 80)[None, None]
    independent = copy(bands)
    object.__setattr__(independent, "quadratures", expected)
    object.__setattr__(independent, "noise_variance_factors", noise)
    close(bands.quadratures, expected, work=1600, scale=float(np.sum(abs(raw))), condition=512)
    composition(
        bands,
        independent,
        transfer(k=2, complex_values=True),
        np.array([[0.03, 0.02], [0.02, -0.03], [-0.04, 0.01], [0.01, 0.04]]),
    )
