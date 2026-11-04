"""Actual cubic controls, alias/header mutation, and linked phase origin/sign."""

from math import pi
from typing import Any

import numpy as np
import pytest

from c_acquisition_fixture import api, close, events, matrix, optics, options
from c_acquisition_fixture import numerical_case as numerical_case


def impulses(*, mode: str, t: int = 1) -> tuple[Any, Any]:
    # 80 pixels keeps cubic displacements 0,1,8,27 within the positive half.
    d, p, z = (1, 4, 1) if mode == "2d" else (4, 3, 2)
    raw = np.zeros((t, d, p, z, 10, 80))
    for time, direction, phase, h in np.ndindex(t, d, p, z):
        displacement = [0, 1, 8, 27][phase if mode == "2d" else direction]
        raw[time, direction, phase, h, 5, 20 + displacement] = 64
    return raw, np.repeat(raw[..., None, :, :], 1, axis=4)


@pytest.mark.parametrize("origin", [0.0, 10.0])
@pytest.mark.parametrize("storage", ["direction-major", "z-major"])
def test_fitted_2d_cubic_exact_control_alias_mutation_and_first_off_phase(
    origin: float, storage: str
) -> None:
    raw, off = impulses(mode="2d", t=2)
    clock = np.arange(16, dtype=float) + 100
    clock[[1, 3, 5, 7]] = origin + np.arange(4)
    phases = np.arange(16, dtype=float) / 11
    phases[[0, 2, 4, 6]] = [0.0, 0.7, 2.9, 4.1]
    before_clock, before_phases = clock.copy(), phases.copy()
    theta, spacing = 0.2, 100.0
    actual = api("prepare_acquisition_bands")(
        raw,
        **(
            options(
                storage_order=storage,
                off_exposures=off,
                drift_within=True,
                fit_drift=True,
                adjust_phases=True,
                header_timestamps=clock,
                header_phases_rad=phases,
                phase_steps_rad=np.array([0.0]),
                phases_rad=np.zeros((1, 4)),
                phase_start_angle_rad=theta,
                linespacing_um=spacing,
            )
            | optics()
        ),
    )
    fits = events(actual, "cubic-fit")
    assert len(fits) == 2
    for fit in fits:
        assert type(fit["scope"]) is str
        close(fit["matrix"], [[1, 1, 1], [2, 4, 8], [3, 9, 27]])
        close(fit["coefficients"], [[0, 0], [0, 0], [1, 0]])
        close(fit["evaluation_timestamps_after"], [0, 1, 2, 3])
        close(fit["sample_timestamps_after"], [0, 1, 2, 3])
        close(fit["evaluated_xy"], [[0, 0], [1, 0], [8, 0], [27, 0]])
    expected_displacement = np.array([[0, 0], [1, 0], [8, 0], [27, 0]])
    close(actual.exposure_displacements_pixels, np.tile(expected_displacement, (2, 1, 1, 1, 1)))
    expected_phases = (
        phases[[0, 2, 4, 6]] + 2 * pi * np.cos(theta) / spacing * expected_displacement[:, 0]
    )
    close(actual.phase_angles_rad, np.tile(expected_phases, (2, 1, 1, 1)))
    left, noise = matrix(expected_phases, 2, "drift")
    close(actual.separation_matrices, np.tile(left, (2, 1, 1, 1, 1)))
    close(actual.noise_variance_factors, np.tile(noise, (2, 1, 1)))
    assert actual.phase_policies == ((("drift",),), (("drift",),))
    np.testing.assert_array_equal(actual.header_timestamps_after, before_clock)
    np.testing.assert_array_equal(clock, before_clock)
    np.testing.assert_array_equal(phases, before_phases)
    assert len(events(actual, "exposure-correction")) == 8


@pytest.mark.parametrize("both", [False, True])
def test_ordinary_3d_cubic_distinct_vectors_global_prefix_reused_at_later_time(both: bool) -> None:
    raw, off = impulses(mode="3d", t=2)
    # Samples use d*Z*P+floor(Z*P/2), deliberately IGNORING off stride.
    prefix = np.array([10 + d + (p - 3) / 10 for d in range(4) for p in range(6)])
    clock = np.r_[prefix, np.arange(72, dtype=float) + 100]
    phases = np.arange(96, dtype=float) / 3
    original = clock.copy()
    theta, spacing = 0.37, 100.0
    actual = api("prepare_acquisition_bands")(
        raw,
        **(
            options(
                acquisition_mode="3d",
                off_exposures=off,
                drift_within=True,
                drift_between=both,
                adjust_phases=True,
                fit_drift=False,
                header_timestamps=clock,
                header_phases_rad=phases,
                phase_start_angle_rad=theta,
                linespacing_um=spacing,
                negative_angle_step=True,
            )
            | optics()
        ),
    )
    fits = events(actual, "cubic-fit")
    assert len(fits) == 2
    measured = np.array([0.0, 1.0, 8.0, 27.0])
    eta = prefix - 10
    expected = eta**3
    for t, fit in enumerate(fits):
        assert type(fit["scope"]) is str
        close(fit["sample_displacements_xy"], np.c_[measured, np.zeros(4)])
        close(fit["coefficients"], [[0, 0], [0, 0], [1, 0]])
        close(fit["evaluation_timestamps_after"], eta)
        # First sample retains tau0 (10 at t0, 0 after prefix mutation at t1).
        close(fit["sample_timestamps_after"], [10 if t == 0 else 0, 1, 2, 3])
    correction = expected.reshape(4, 2, 3) - measured[:, None, None]
    close(
        actual.exposure_displacements_pixels[..., 0],
        np.tile(correction, (2, 1, 1, 1)),
        proof=actual.exposure_displacements_pixels,
    )
    close(
        actual.exposure_displacements_pixels[..., 1], 0, proof=actual.exposure_displacements_pixels
    )
    for d in range(4):
        expected_phase = (
            2 * pi * np.arange(3) / 3
            + 2 * pi * np.cos(theta - d * pi / 4) / spacing * correction[d]
        )
        close(
            actual.phase_angles_rad[:, d],
            np.tile(expected_phase, (2, 1, 1)),
            proof=actual.phase_angles_rad,
        )
        _, last_noise = matrix(expected_phase[-1], 2, "drift")
        close(
            actual.noise_variance_factors[:, d],
            np.tile(last_noise, (2, 1)),
            proof=actual.noise_variance_factors,
        )
    np.testing.assert_array_equal(actual.header_timestamps_after[24:], original[24:])
    close(actual.header_timestamps_after[:24], eta, proof=actual.header_timestamps_after)
    np.testing.assert_array_equal(clock, original)
    assert len(events(actual, "between-correction")) == (6 if both else 0)


@pytest.mark.parametrize(
    "kind", ["flag-off", "no-phase", "no-clock", "short", "singular", "power-underflow"]
)
def test_fitted_metadata_prerequisites_and_cubic_failures(kind: str) -> None:
    raw, off = impulses(mode="2d")
    clock = np.arange(8, dtype=float)
    phase = np.arange(8) * pi / 4
    settings = (
        options(
            off_exposures=off,
            drift_within=True,
            fit_drift=True,
            adjust_phases=True,
            header_timestamps=clock,
            header_phases_rad=phase,
            linespacing_um=100.0,
        )
        | optics()
    )
    if kind == "flag-off":
        settings["adjust_phases"] = False
    elif kind == "no-phase":
        settings["header_phases_rad"] = None
    elif kind == "no-clock":
        settings["header_timestamps"] = None
    elif kind == "short":
        raw, off = raw[:, :, :3], off[:, :, :3]
        settings.update(off_exposures=off, header_timestamps=clock[:6], header_phases_rad=phase[:6])
    elif kind == "singular":
        settings["header_timestamps"] = np.ones(8)
    else:
        settings["header_timestamps"] = np.arange(8) * 2.0**-1070
    reason = "(?i)phase|timestamp|metadata|fit|cubic|rank|alloc|power"
    if kind in {"singular", "power-underflow"}:
        # Underflow zeros the higher design columns, so the selected solve
        # may identify the cause directly as a singular matrix.
        reason += "|singular matrix"
    with pytest.raises(api("AcquisitionModeError"), match=reason):
        api("prepare_acquisition_bands")(raw, **settings)


def test_overdetermined_cubic_orthogonal_residual_and_duplicate_time_positive() -> None:
    for times, shifts in [
        ([0, 1, 2, 3, 4], [0, -3, 14, 23, 65]),
        ([0, 1, 2, 3, 3], [0, 1, 8, 27, 27]),
    ]:
        # For times1..4, (-4,6,-4,1) is orthogonal to each t,t²,t³
        # column. The unweighted fit therefore retains exactly c=(0,0,1).
        raw = np.zeros((1, 1, 5, 1, 10, 160))
        for p, shift in enumerate(shifts):
            raw[0, 0, p, 0, 5, 20 + shift] = 64
        off = raw[..., None, :, :].copy()
        clock = np.repeat(np.array(times, dtype=float) + 10, 2)
        phases = np.repeat(2 * pi * np.arange(5) / 5, 2)
        actual = api("prepare_acquisition_bands")(
            raw,
            **(
                options(
                    storage_order="z-major",
                    drift_within=True,
                    fit_drift=True,
                    adjust_phases=True,
                    off_exposures=off,
                    header_timestamps=clock,
                    header_phases_rad=phases,
                    linespacing_um=100.0,
                )
                | optics()
            ),
        )
        fit = events(actual, "cubic-fit")[0]
        close(fit["coefficients"], [[0, 0], [0, 0], [1, 0]])
        close(fit["evaluated_xy"][:, 0], np.array(times) ** 3)


def test_3d_overdetermined_fit_subtracts_measured_not_fitted_midpoints() -> None:
    # At times1..4 the residual(-4,6,-4,1) is orthogonal to all three
    # cubic columns. The fitted curve is t**3 but measured samples differ.
    shifts = np.array([0, -3, 14, 23, 65])
    raw = np.zeros((1, 5, 3, 2, 10, 160))
    for d in range(5):
        raw[0, d, :, :, 5, 20 + shifts[d]] = 64
    off = raw[..., None, :, :].copy()
    prefix = np.array([10 + d + (p - 3) / 10 for d in range(5) for p in range(6)])
    clock = np.r_[prefix, np.arange(30) + 100.0]
    phases = np.arange(60, dtype=float) / 3
    result = api("prepare_acquisition_bands")(
        raw,
        **(
            options(
                acquisition_mode="3d",
                off_exposures=off,
                drift_within=True,
                adjust_phases=True,
                header_timestamps=clock,
                header_phases_rad=phases,
                linespacing_um=100.0,
            )
            | optics()
        ),
    )
    fit = events(result, "cubic-fit")[0]
    close(fit["coefficients"], [[0, 0], [0, 0], [1, 0]])
    close(fit["sample_displacements_xy"][:, 0], shifts, proof=fit["sample_displacements_xy"])
    expected = (prefix - 10).reshape(5, 2, 3) ** 3 - shifts[:, None, None]
    close(
        result.exposure_displacements_pixels[0, ..., 0],
        expected,
        proof=result.exposure_displacements_pixels,
    )
    assert np.max(abs(shifts - np.arange(5) ** 3)) == 6
