"""Independent actual between/within drift estimators and correction ordering."""

from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import (
    api,
    as_disc,
    assert_mode_trace,
    between_expected,
    certified_pi,
    close,
    correlate,
    correlation_budget,
    correlation_field,
    edge,
    events,
    gamma,
    lift,
    optics,
    options,
    prepare_expected,
    raw_pattern,
    transform,
)
from c_acquisition_fixture import (
    numerical_case as numerical_case,
)


def drift_images(*, d: int = 2, z: int = 3, t: int = 1) -> Any:
    raw = np.zeros((t, d, 3, z, 10, 10))
    for time, direction, phase, h in np.ndindex(t, d, 3, z):
        # Integer asymmetric pattern, independently translated with array rolls.
        plane = np.zeros((10, 10))
        plane[3, 4] = 32 + 4 * phase
        plane[6, 2] = 5 + time
        plane[4, 7] = 9 + h
        raw[time, direction, phase, h] = np.roll(plane, (direction, -direction), axis=(0, 1))
    return raw


def compare_correlation(actual: dict[str, Any], expected: dict[str, Any], bound: float) -> None:
    power = np.asarray(expected["absolute_correlation"])
    maximum = float(np.max(power))
    if maximum > 0:
        ordered = np.sort(power.reshape(-1))
        assert ordered[-1] - ordered[-2] > 2 * bound, "independent peak margin unresolved"
    for name in ["cross_spectrum", "correlation", "absolute_correlation"]:
        np.testing.assert_allclose(actual[name], np.asarray(expected[name]), rtol=0, atol=bound)
    assert actual["integer_peak_xyz"] == expected["integer_peak_xyz"]
    assert actual["offset_status_xyz"] == expected["offset_status_xyz"]
    error = []
    for values in expected["neighbors_xyz"]:
        slope = (values[2] - values[0]) / 2
        curvature = values[2] + values[0] - 2 * values[1]
        if curvature == 0:
            error.append(0.0)
        else:
            assert abs(curvature) > 4 * bound
            # Each neighbor may move by bound, so slope moves by at most
            # bound and curvature by 4*bound. Enclose this quotient too.
            uncertainty = (bound * abs(curvature) + abs(slope) * 4 * bound) / (
                abs(curvature) * (abs(curvature) - 4 * bound)
            )
            error.append(
                float(
                    np.nextafter(float(np.asarray(uncertainty)) + float(uncertainty.error), np.inf)
                )
            )
    np.testing.assert_allclose(
        actual["neighbors_xyz"], np.asarray(expected["neighbors_xyz"]), rtol=0, atol=bound
    )
    offset_bound = max(error)
    for name in ["offsets_xyz", "wrapped_displacement_xyz"]:
        value = expected[name]
        # The independent fit also propagates rounding in the quotient and
        # in adding the integer peak and applying the resolved wrap.
        allowance = max(offset_bound, float(np.max(value.error)))
        if name == "wrapped_displacement_xyz":
            scale = float(np.max(abs(np.asarray(value)))) + max(
                expected["absolute_correlation"].shape
            )
            allowance += gamma(2) * (scale + allowance)
        allowance = float(np.nextafter(allowance, np.inf))
        assert np.isfinite(allowance)
        np.testing.assert_allclose(actual[name], np.asarray(value), rtol=0, atol=allowance)


@pytest.mark.parametrize("z", [1, 4, 6])
@pytest.mark.parametrize("hpf", [-0.2, 0.0, 0.3])
@pytest.mark.parametrize("n", [0, 1, 3])
def test_actual_between_prepass_middle_first_off_fourth_root_and_correction(
    z: int, hpf: float, n: int
) -> None:
    raw = drift_images(z=z)
    off = None if n == 0 else np.repeat((raw + 1)[..., None, :, :], n, axis=4)
    if off is not None and n > 1:
        off[..., 1:, :, :] += 100  # prepass first off ONLY; normal loader sums all
    mode = "2d" if z == 1 else "3d"
    settings = options(
        acquisition_mode=mode,
        drift_between=True,
        drift_filter_fraction=hpf,
        background=2.0,
        flatfield_slope=np.full((10, 10), 3.0),
        exposure_background=np.full(raw.shape[:4], 0.25),
        off_exposures=off,
    ) | optics(numerical_aperture=0.4)
    expected = between_expected(
        raw[0],
        background=2.0,
        off=None if off is None else off[0],
        highpass=hpf,
        **optics(numerical_aperture=0.4),
    )
    actual = api("prepare_acquisition_bands")(raw, **settings)
    built = events(actual, "between-build")
    assert len(built) == 1
    for name in ["subz", "first_z", "unused_axial_cutoff"]:
        assert built[0][name] == expected[name]
    for name in ["centers", "fourier", "optical_radial_cutoff"]:
        close(built[0][name], expected[name])
    assert built[0]["optical_radial_cutoff"] > 0.5  # deliberately unclamped
    correlations = events(actual, "drift-correlation")
    for d, e in enumerate(correlations, 1):
        assert e["scope"] == "between" and e["exponent"] == 0.25 and e["moving_index"] == d
        bound = correlation_budget(expected["centers"][0], expected["centers"][d], 0.25)
        compare_correlation(e, expected["correlations"][d - 1], bound)
    ordinary = prepare_expected(raw, settings | {"drift_between": False})
    correction = events(actual, "between-correction")
    assert len(correction) == 1
    for d in [0, 1]:
        displacement = actual.between_displacements_pixels[0, d]
        zz, yy, xx = np.meshgrid(lift(z), lift(10), np.arange(6), indexing="ij")
        phase = np.exp(
            2j
            * certified_pi()
            * (displacement[0] * xx / 10 + displacement[1] * yy / 10 + displacement[2] * zz / z)
        )
        # Relation checks application of measured estimate, not its accuracy;
        # independent raw correlation above supplies the accuracy evidence.
        close(
            actual.quadratures[0, d],
            ordinary["quadratures"][0, d] * phase,
            proof=actual.quadratures,
        )
    close(actual.off_quadratures, ordinary["off_quadratures"]) if n else None
    assert_mode_trace(actual)


def test_all_zero_correlation_keeps_initialized_center_and_no_phase_invention() -> None:
    raw = np.zeros((1, 2, 3, 1, 10, 10))
    actual = api("prepare_acquisition_bands")(raw, **(options(drift_between=True) | optics()))
    e = events(actual, "drift-correlation")[0]
    assert e["integer_peak_xyz"] == (5, 5, 0)
    np.testing.assert_array_equal(e["wrapped_displacement_xyz"], [5, 5, 0])
    assert e["offset_status_xyz"] == ("zero-curvature", "zero-curvature", "not-fitted")
    np.testing.assert_array_equal(e["cross_spectrum"], 0)
    np.testing.assert_array_equal(e["correlation"], 0)
    np.testing.assert_array_equal(e["absolute_correlation"], 0)


def test_absolute_negative_peak_first_strict_tie_and_positive_half_wrap() -> None:
    raw = np.zeros((1, 2, 3, 1, 10, 10))
    # One periodic alternating raw mode survives fixed10 edges as a finite
    # periodic pattern. Negative moving data forces negative correlation peaks.
    plane = np.tile([1.0, -1.0] * 5, (10, 1))
    raw[:, 0, :, 0] = plane
    raw[:, 1, :, 0] = -plane
    # Repair the three selected -1 sentinels before accumulating the
    # prepass, without touching either the raw input or a camera map.
    selected = raw[0, :, :, 0].copy()
    sentinel = selected[..., -1, -1] == -1
    assert np.count_nonzero(sentinel) == 3
    selected[..., -1, -1][sentinel] = selected[..., -1, -2][sentinel]
    # The field is independently certified. First-maximum selection below
    # is a relation on the returned field because the peak gap is unresolved.
    centers = [edge(np.sum(as_disc(planes) / 300, axis=0), 10)[None] for planes in selected]
    expected = correlation_field(*centers, exponent=0.25, pitch=1.0, rd=2 / 0.52, highpass=0.0)
    actual = api("prepare_acquisition_bands")(
        raw, **(options(drift_between=True) | optics(numerical_aperture=1.0))
    )
    e = events(actual, "drift-correlation")[0]
    assert np.min(e["correlation"]) < 0
    bound = correlation_budget(centers[0], centers[1], 0.25)
    for name in ["correlation", "absolute_correlation"]:
        np.testing.assert_allclose(e[name], np.asarray(expected[name]), rtol=0, atol=bound)
    np.testing.assert_array_equal(e["absolute_correlation"], abs(e["correlation"]))
    peak_value = np.max(e["absolute_correlation"])
    assert e["integer_peak_xyz"] == tuple(
        np.unravel_index(np.argmax(e["absolute_correlation"]), e["absolute_correlation"].shape)[
            ::-1
        ]
    )
    assert peak_value > 0
    signed = np.asarray(expected["correlation"])
    assert -np.min(signed) - np.max(signed) > 2 * bound
    assert e["correlation"][e["integer_peak_xyz"][::-1]] < 0


@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
@pytest.mark.parametrize("hpf", [-0.1, 0.4])
def test_within_2d_actual_reference_half_power_and_before_separation(
    storage: str, hpf: float
) -> None:
    raw = drift_images(d=1, z=1)
    raw[0, 0, 1, 0] = np.roll(raw[0, 0, 1, 0], 1, axis=1)
    raw[0, 0, 2, 0] = np.roll(raw[0, 0, 2, 0], -2, axis=0)
    off = np.repeat((raw + 1)[..., None, :, :], 2, axis=4)
    settings = (
        options(
            storage_order=storage,
            off_exposures=off,
            drift_within=True,
            drift_filter_fraction=hpf,
            fit_drift=False,
            adjust_phases=False,
        )
        | optics()
    )
    actual = api("prepare_acquisition_bands")(raw, **settings)
    prepared = prepare_expected(raw, settings)
    alpha = prepared["input_scale"]
    exposures = alpha * (raw[0, 0, :, 0] + np.sum(off[0, 0, :, 0], axis=1))
    reference = exposures[0][None]
    corr = [
        correlate(reference, v[None], exponent=0.5, pitch=1.0, rd=2 * 0.25 / 0.52, highpass=hpf)
        for v in exposures
    ]
    within = [e for e in events(actual, "drift-correlation") if e["scope"] == "within"]
    assert len(within) == 3
    for p, e in enumerate(within):
        assert e["exponent"] == 0.5
        compare_correlation(e, corr[p], correlation_budget(reference, exposures[p][None], 0.5))
    corrections = events(actual, "exposure-correction")
    onfourier = transform(alpha * raw[0, 0, :, 0], axes=(1, 2))[..., :6]
    offfourier = transform(alpha * np.sum(off[0, 0, :, 0], axis=1), axes=(1, 2))[..., :6]
    yy, xx = np.meshgrid(lift(10), np.arange(6), indexing="ij")
    for p, e in enumerate(corrections):
        displacement = actual.exposure_displacements_pixels[0, 0, 0, p]
        ramp = np.exp(2j * certified_pi() * (displacement[0] * xx / 10 + displacement[1] * yy / 10))
        close(e["phase_multiplier"], ramp)
        onfourier[p] *= ramp
        offfourier[p] *= ramp
    left = prepared["separation_matrices"][0, 0, 0]
    onbands, offbands = left @ onfourier.reshape(3, -1), left @ offfourier.reshape(3, -1)
    onbands, offbands = onbands.reshape(3, 10, 6), offbands.reshape(3, 10, 6)
    onbands[:, :, -1], offbands[:, :, -1] = onfourier[:, :, -1], offfourier[:, :, -1]
    close(actual.quadratures[0, 0, :, 0], onbands, proof=actual.quadratures)
    close(actual.off_quadratures[0, 0, :, 0], offbands, proof=actual.off_quadratures)
    assert actual.header_timestamps_after is None
    assert not events(actual, "cubic-fit")
    assert len(events(actual, "between-build")) == (1 if storage == "direction-major" else 0)


def test_fast_d1_between_only_skips_unsafe_prepass_but_is_initialized_zero() -> None:
    raw = raw_pattern(y=1, x=4)
    actual = api("prepare_acquisition_bands")(
        raw, **options(storage_order="z-major", drift_between=True, dz_um=0.0)
    )
    expected = prepare_expected(raw, options(storage_order="z-major"))
    np.testing.assert_array_equal(actual.between_displacements_pixels, 0)
    close(actual.quadratures, expected["quadratures"])
    assert not events(actual, "between-build") and not events(actual, "drift-correlation")


def test_nonzero_constant_tie_zero_curvature_and_independent_positive_half_wrap() -> None:
    # Four phases of one give exact center 1/256 on a 16-by-16 plane.
    # The optical mask selects DC alone: Rd=1/32 < first bin=1/16.
    # The dyadic radix-2 DC sum is 1. Quarter-power of unit cross is 1
    # and the one-coefficient inverse yields exactly one at every cell.
    constant = np.ones((1, 2, 4, 1, 16, 16))
    tie = api("prepare_acquisition_bands")(
        constant,
        **(options(drift_between=True) | optics(wavelength_nm=500, numerical_aperture=1 / 128)),
    )
    event = events(tie, "drift-correlation")[0]
    expected_cross = np.zeros((1, 16, 9), dtype=complex)
    expected_cross[0, 0, 0] = 1
    np.testing.assert_array_equal(event["cross_spectrum"], expected_cross)
    close(event["correlation"], as_disc(np.ones((1, 16, 16))))
    np.testing.assert_array_equal(event["correlation"], 1)
    np.testing.assert_array_equal(event["absolute_correlation"], 1)
    np.testing.assert_array_equal(event["neighbors_xyz"], 1)
    np.testing.assert_array_equal(event["offsets_xyz"], 0)
    assert event["integer_peak_xyz"] == (0, 0, 0)
    assert event["offset_status_xyz"] == ("zero-curvature", "zero-curvature", "not-fitted")
    np.testing.assert_array_equal(event["wrapped_displacement_xyz"], 0)

    # Keep the independent translated impulse on its original grid.
    # The full-spectrum correlation is 100 at x=5 and zero elsewhere.
    raw = np.zeros((1, 2, 3, 1, 10, 10))
    raw[:, 0, :, 0, 4, 2] = 100
    raw[:, 1, :, 0, 4, 7] = 100
    half = api("prepare_acquisition_bands")(
        raw, **(options(drift_between=True) | optics(numerical_aperture=1.0))
    )
    event = events(half, "drift-correlation")[0]
    expected = np.zeros((1, 10, 10))
    expected[0, 0, 5] = 100
    close(event["correlation"], expected)
    assert event["integer_peak_xyz"] == (5, 0, 0)
    close(event["wrapped_displacement_xyz"], [5, 0, 0])
    # The half-wrap equality proof assumes preservation of the equal
    # periodic neighbors of the impulse. Then offset0 and strict >half
    # retain +5. The generic coefficient error bound cannot prove that tie.
    assert event["offset_status_xyz"] == ("fitted", "fitted", "not-fitted")


def test_z6_substack3_nonzero_native_axial_shift_and_full_z_correction() -> None:
    from c_acquisition_fixture import certified_close

    raw = np.zeros((1, 2, 3, 6, 10, 10))
    # Selected source sections1..3: reference at selected0 and moving at1.
    raw[:, 0, :, 1, 4, 4] = 600
    raw[:, 1, :, 2, 4, 4] = 600
    settings = options(acquisition_mode="3d", drift_between=True) | optics(numerical_aperture=1.0)
    expected = between_expected(raw[0], **optics(numerical_aperture=1.0))
    actual = api("prepare_acquisition_bands")(raw, **settings)
    assert events(actual, "between-build")[0]["subz"] == 3
    close(
        actual.between_displacements_pixels[0, 1],
        [0, 0, 1],
        proof=actual.between_displacements_pixels,
    )
    ordinary = prepare_expected(raw, options(acquisition_mode="3d"))
    zz, yy, xx = np.meshgrid(lift(6), lift(10), np.arange(6), indexing="ij")
    truth = ordinary["quadratures"][0, 1] * np.exp(2j * certified_pi() * zz / 6)
    certified_close(actual.quadratures[0, 1], truth)
    assert expected["correlations"][0]["integer_peak_xyz"] == (0, 0, 1)


def test_drift_optical_boundary_is_strict_before_quarter_power() -> None:
    raw = np.zeros((1, 2, 3, 1, 10, 10))
    raw[:, 0, :, 0, 4, 3] = 100
    raw[:, 1, :, 0, 4, 4] = 100
    op = optics(wavelength_nm=500, numerical_aperture=0.125)
    # Rd=2*.125/.5=.5. Native x Nyquist is exactly.5 and must remain0;
    # the x4 bin has radius.4 and a nonzero unit-magnitude cross value.
    expected = between_expected(raw[0], **op)
    actual = api("prepare_acquisition_bands")(raw, **(options(drift_between=True) | op))
    event = events(actual, "drift-correlation")[0]
    assert event["cross_spectrum"][0, 0, 5] == 0j
    close(abs(event["cross_spectrum"][0, 0, 4]), 1.0, proof=event["cross_spectrum"])
    bound = correlation_budget(expected["centers"][0], expected["centers"][1], 0.25)
    compare_correlation(event, expected["correlations"][0], bound)
