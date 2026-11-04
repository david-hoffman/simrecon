"""CE06 camera/off traversal, phase policies, sums and immutable diagnostics."""

from dataclasses import FrozenInstanceError
from itertools import product

import numpy as np
import pytest

from c_acquisition_fixture import (
    SOURCE10,
    api,
    assert_mode_trace,
    close,
    events,
    options,
    prepare_expected,
    raw_pattern,
)
from c_acquisition_fixture import (
    numerical_case as numerical_case,
)


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)])
@pytest.mark.parametrize("n", [0, 1, 2])
@pytest.mark.parametrize("edge_width", [0, 1, -1, -2, 4])
def test_raw_camera_off_edge_separation_composition(
    mode: str, z: int, n: int, edge_width: int
) -> None:
    raw = raw_pattern(t=2, d=2, p=4, z=z, y=4, x=6)
    off = None if n == 0 else np.repeat((raw + 3)[..., None, :, :], n, axis=4)
    raw[0, 0, 0, 0, -1, -1] = -1
    if off is not None:
        off[0, 0, 0, 0, 0, -1, -1] = -1
        off[1, 1, 2, -1, -1, 0, 1] = -1  # non-corner -1 is ordinary input
    background = np.arange(24, dtype=float).reshape(4, 6) / 8
    slope = np.ones((4, 6))
    slope[-1, -1] = -2
    slope[0, 0] = 0
    settings = options(
        acquisition_mode=mode,
        norders=2,
        edge_pixels=edge_width,
        background=background,
        flatfield_slope=slope,
        exposure_background=np.arange(raw.size // 24).reshape(raw.shape[:4]) / 16,
        off_exposures=off,
        phases_rad=np.tile([0, np.pi / 2, np.pi, np.pi], (2, 1)),
        lateral_zoom=1.5,
        axial_zoom=2,
    )
    originals = [v.copy() for v in [raw, background, slope] + ([] if off is None else [off])]
    expected = prepare_expected(raw, settings)
    actual = api("prepare_acquisition_bands")(raw, **settings)
    for name, value in expected.items():
        observed = getattr(actual, name)
        if value is None or isinstance(value, tuple):
            assert observed == value
        else:
            close(observed, value)
    for value, before in zip(
        [raw, background, slope] + ([] if off is None else [off]), originals, strict=True
    ):
        np.testing.assert_array_equal(value, before)
    assert actual.reference_sha256 == SOURCE10 and actual.source_revision == "SVN307"
    assert actual.quadratures.flags.writeable and actual.quadratures.flags.owndata
    assert actual.noise_variance_factors.flags.writeable
    assert not actual.frame_sums.flags.writeable
    assert_mode_trace(actual)
    designs = events(actual, "phase-design")
    assert len(designs) == 2 * 2 * z
    for e in designs:
        assert e["policy"] == "supplied"
        close(e["noise_variance_factors"], [1.5, 1.75])


@pytest.mark.parametrize(
    "equalize,equalize_z,equalize_time", list(product([False, True], repeat=3))
)
@pytest.mark.parametrize("n", [1, 2])
def test_all_equalization_policies_use_independent_anchors(
    equalize: bool, equalize_z: bool, equalize_time: bool, n: int
) -> None:
    raw = raw_pattern(t=2, d=2, z=2, y=2, x=4)
    # Negative sums are legitimate and selected zero divisors are separate.
    raw[1, 1] *= -1
    off = np.repeat((raw - 3)[..., None, :, :], n, axis=4)
    settings = options(
        acquisition_mode="3d",
        off_exposures=off,
        equalize=equalize,
        equalize_z=equalize_z,
        equalize_time=equalize_time,
    )
    expected = prepare_expected(raw, settings)
    actual = api("prepare_acquisition_bands")(raw, **settings)
    for name in [
        "quadratures",
        "off_quadratures",
        "equalization_gains",
        "off_equalization_gains",
        "frame_sums",
        "off_frame_sums",
    ]:
        close(getattr(actual, name), expected[name])
    if n == 1:
        np.testing.assert_array_equal(actual.off_equalization_gains, 1)


@pytest.mark.parametrize("which", ["on", "off"])
def test_selected_zero_divisor_rejects_and_disabled_or_n1_remains_valid(which: str) -> None:
    raw = np.ones((1, 1, 3, 1, 2, 4))
    off = np.ones((1, 1, 3, 1, 2, 2, 4))
    (raw if which == "on" else off)[:] = 0
    settings = options(off_exposures=off, equalize=True)
    with pytest.raises(api("AcquisitionModeError"), match="(?i)sum|equaliz|divis"):
        api("prepare_acquisition_bands")(raw, **settings)
    settings["equalize"] = False
    actual = api("prepare_acquisition_bands")(raw, **settings)
    assert np.isfinite(actual.quadratures).all()
    if which == "off":
        settings.update(equalize=True, off_exposures=off[..., :1, :, :])
        actual = api("prepare_acquisition_bands")(raw, **settings)
        np.testing.assert_array_equal(actual.off_frame_sums, 0)
        np.testing.assert_array_equal(actual.off_equalization_gains, 1)


@pytest.mark.parametrize("d", [1, 2, 3])
@pytest.mark.parametrize("policy", ["uniform", "supplied", "steps", "irregular", "reduced"])
def test_phase_policy_matrix_noise_and_raw_nyquist(d: int, policy: str) -> None:
    p = 4 if policy == "reduced" else 3
    raw = raw_pattern(d=d, p=p, y=2, x=4)
    settings = options()
    if policy == "supplied":
        settings["phases_rad"] = np.tile(2 * np.pi * np.arange(p) / p, (d, 1))
    elif policy == "steps":
        settings.update(phase_steps_rad=np.full(d, 0.8), phases_rad=np.zeros((d, p)))
    elif policy in {"irregular", "reduced"}:
        settings["phases_rad"] = np.tile(
            [0, np.pi / 2, np.pi] if p == 3 else [0, np.pi / 2, np.pi, np.pi], (d, 1)
        )
    expected = prepare_expected(raw, settings)
    actual = api("prepare_acquisition_bands")(raw, **settings)
    for name in [
        "quadratures",
        "separation_matrices",
        "noise_variance_factors",
        "phase_angles_rad",
    ]:
        close(getattr(actual, name), expected[name])
    assert actual.phase_policies == expected["phase_policies"]
    if policy == "reduced":
        close(
            actual.noise_variance_factors,
            [[[1.5, 1.75]]] * d if d == 1 else np.tile([1.5, 1.75], (1, d, 1)),
        )
    # Endpoint retains different raw phase slots; a matrix multiplication there is wrong.
    assert np.max(abs(expected["quadratures"][..., -1])) > 0


def test_three_float_steps_limit_is_not_explicit_list_limit() -> None:
    raw = raw_pattern(d=4, y=2, x=4)
    with pytest.raises(api("AcquisitionModeError"), match="(?i)step|three|3|alloc"):
        api("prepare_acquisition_bands")(raw, **options(phase_steps_rad=np.full(4, 0.9)))
    actual = api("prepare_acquisition_bands")(
        raw, **options(phases_rad=np.tile([0, 0.9, 2.1], (4, 1)))
    )
    assert actual.quadratures.shape[1] == 4


def test_record_ownership_frozen_metadata_and_resolved_settings() -> None:
    raw = raw_pattern(y=2, x=4)[..., ::-1]
    raw.flags.writeable = False
    clock = np.arange(6, dtype=float)
    phases = np.arange(6, dtype=float)
    off = np.ones((1, 1, 3, 1, 1, 2, 4), dtype=np.int16)
    settings = options(
        background=np.zeros((2, 4)),
        off_exposures=off,
        header_timestamps=clock,
        header_phases_rad=phases,
        combine_off_orders=np.array([0, -1], dtype=np.int32),
    )
    actual = api("prepare_acquisition_bands")(raw, **settings)
    assert isinstance(actual, api("AcquisitionBands"))
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        actual.acquisition_mode = "3d"
    assert not np.shares_memory(actual.quadratures, raw)
    assert not np.shares_memory(actual.header_timestamps_after, clock)
    np.testing.assert_array_equal(actual.header_timestamps_after, clock)
    s = dict(actual.resolved_settings)
    assert s["background"] == "map" and s["n_off_exposures"] == 1
    assert s["combine_off_orders"] == (0, -1)
    assert tuple(s)[-1] == "n_off_exposures"
    assert s["storage_order"] == "direction-major"
    for name in [
        "quadratures",
        "noise_variance_factors",
        "frame_sums",
        "off_frame_sums",
        "off_quadratures",
        "background_after",
        "slope_after",
        "phase_angles_rad",
        "separation_matrices",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
    ]:
        value = getattr(actual, name)
        assert value.flags.owndata and not np.shares_memory(value, raw)
    assert_mode_trace(actual)


@pytest.mark.parametrize("mode,z", [("2d", 1), ("3d", 3)])
@pytest.mark.parametrize("n", [1, 2])
@pytest.mark.parametrize("selectors", [(1, 1), (0, 1), (1, 0), (-1, 0)])
def test_literal_off_statistics_integer_cells_plus_minus_and_repeated_plane0(
    mode: str, z: int, n: int, selectors: tuple[int, int]
) -> None:
    from c_acquisition_fixture import combine_expected, lift, optics, transform

    raw = raw_pattern(t=2, d=2, z=z, y=4, x=6)
    repeated_side = z > 1 and selectors[1] > 0
    if repeated_side:
        off_frame = np.roll(raw, 1, axis=-1) + np.roll(raw, 2, axis=-2) + 3
    else:
        off_frame = 2 * raw + 1
    off = np.repeat(off_frame[..., None, :, :], n, axis=4)
    # Distinct off data; neither averaging nor per-current-z combination agrees.
    off[..., 0, :, :] += np.arange(24).reshape(4, 6) % 3
    settings = (
        options(
            acquisition_mode=mode,
            dxy_um=0.25,
            off_exposures=off,
            combine_off_orders=np.array(selectors, dtype=np.int32),
        )
        | optics()
    )
    baseline = prepare_expected(raw, settings | {"combine_off_orders": None})
    expected = baseline["quadratures"].copy()
    y, x = 4, 6
    cells = np.array(
        [
            [
                (int(j / (x * 0.25)) ** 2 + int(lift(y)[i] / (y * 0.25)) ** 2) <= 0
                for j in range(x // 2 + 1)
            ]
            for i in range(y)
        ]
    )
    assert 0 < np.count_nonzero(cells) < cells.size
    assert cells[0, 1]  # integer truncated kx=0; physical kx>0 is still inside
    expected_events = []
    for t, d in np.ndindex(2, 2):
        native = (
            transform(expected[t, d], inverse=True, axes=(1,)) / z
            if z > 1
            else expected[t, d].copy()
        )
        offnative = baseline["off_quadratures"][t, d]
        if repeated_side:
            # Each invocation rereads the updated on plane zero and the same
            # separated off plane zero. The observer certifies the divisors.
            for callz in range(z):
                combine_expected(native, offnative, callz, settings, expected_events)
            expected[t, d] = transform(native, axes=(1,))
            continue
        for callz in range(z):
            for m, selector in enumerate(selectors):
                if selector <= 0:
                    continue
                slots = slice(0, 1) if m == 0 else slice(1, 3)
                on = native[slots, 0]
                off0 = offnative[slots, 0]
                on_power, off_power = np.sum(abs(on) ** 2, axis=0), np.sum(abs(off0) ** 2, axis=0)
                no, nf = np.mean(on_power[~cells]), np.mean(off_power[~cells])
                so, sf = np.mean(on_power[cells]) - no, np.mean(off_power[cells]) - nf
                co, cf = max(so, 0), max(sf, 0)
                replaced = co == cf == 0
                if replaced:
                    co = cf = 1
                u, v = np.sqrt(co) / no, np.sqrt(cf) / nf
                a, b = u / (u + v), v / (u + v)
                native[slots, 0] = a * on + (1 if m == 0 else -1) * b * off0
                expected_events.append(
                    dict(
                        call_z=callz,
                        affected_z=0,
                        order=m,
                        cutoff_integer=0,
                        inside_count=int(np.count_nonzero(cells)),
                        outside_count=int(np.count_nonzero(~cells)),
                        on_noise=no,
                        off_noise=nf,
                        on_signal2_before_clip=so,
                        off_signal2_before_clip=sf,
                        both_zero_replaced=replaced,
                        on_scale=u,
                        off_scale=v,
                        denominator=u + v,
                        on_fraction=a,
                        off_fraction=b,
                        quadratures_after=native[slots, 0].copy(),
                    )
                )
        expected[t, d] = transform(native, axes=(1,)) if z > 1 else native
    actual = api("prepare_acquisition_bands")(raw, **settings)
    close(actual.quadratures, expected)
    if repeated_side:
        close(actual.off_quadratures, baseline["off_quadratures"])
    np.testing.assert_array_equal(actual.noise_variance_factors, baseline["noise_variance_factors"])
    observed = events(actual, "off-combination")
    assert len(observed) == len(expected_events)
    for e, want in zip(observed, expected_events, strict=True):
        for name, value in want.items():
            if isinstance(value, (bool, np.bool_)):
                assert type(e[name]) is bool
                assert e[name] is bool(value)
            elif isinstance(value, (int, np.integer)):
                assert type(e[name]) is int
                assert e[name] == value
            else:
                close(e[name], value)


@pytest.mark.parametrize("cause", ["empty-outside", "zero-noise"])
def test_off_statistics_singular_operations_and_skip_positive(cause: str) -> None:
    from c_acquisition_fixture import optics

    raw = np.ones((1, 1, 3, 1, 2, 4)) if cause == "zero-noise" else raw_pattern(y=2, x=4)
    off = raw[..., None, :, :].copy()
    settings = options(
        dxy_um=0.25 if cause == "zero-noise" else 1.0,
        off_exposures=off,
        combine_off_orders=np.array([1, 0], dtype=np.int32),
    ) | optics(numerical_aperture=0.25 if cause == "zero-noise" else 1.0)
    with pytest.raises(api("AcquisitionModeError"), match="(?i)outside|noise|statistic|empty|zero"):
        api("prepare_acquisition_bands")(raw, **settings)
    # Skipped orders do not evaluate even singular statistics or require optics.
    skip = api("prepare_acquisition_bands")(
        raw, **options(combine_off_orders=np.array([0, -1], dtype=np.int32))
    )
    assert not events(skip, "off-combination")


@pytest.mark.parametrize("on_baseline,off_baseline", [(0, 5), (5, 0), (0, 0), (5, 7)])
def test_off_one_zero_both_zero_and_positive_noise_weight_decisions(
    on_baseline: int, off_baseline: int
) -> None:
    from c_acquisition_fixture import optics

    pattern = np.tile([1.0, -1.0, 1.0, -1.0], (2, 1))
    raw = np.broadcast_to(on_baseline + 2 * pattern, (1, 1, 3, 1, 2, 4)).copy()
    off = np.broadcast_to(off_baseline + 4 * pattern, (1, 1, 3, 1, 1, 2, 4)).copy()
    actual = api("prepare_acquisition_bands")(
        raw,
        **(
            options(
                dxy_um=0.25, off_exposures=off, combine_off_orders=np.array([1, 1], dtype=np.int32)
            )
            | optics()
        ),
    )
    e = events(actual, "off-combination")[0]
    no, nf = 4 / 5, 16 / 5
    so, sf = 9 * on_baseline**2 - no, 9 * off_baseline**2 - nf
    close(e["on_noise"], no)
    close(e["off_noise"], nf)
    close(e["on_signal2_before_clip"], so)
    close(e["off_signal2_before_clip"], sf)
    a, b = max(so, 0), max(sf, 0)
    if a == b == 0:
        a = b = 1
    u, v = np.sqrt(a) / no, np.sqrt(b) / nf
    close(e["on_fraction"], u / (u + v))
    close(e["off_fraction"], v / (u + v))
    assert e["both_zero_replaced"] is (on_baseline == off_baseline == 0)
    assert e["inside_count"] == 1 and e["outside_count"] == 5
    side = events(actual, "off-combination")[1]
    assert side["both_zero_replaced"] is True


def test_identical_on_off_side_cancellation_rejects_later_zero_noise() -> None:
    from c_acquisition_fixture import optics

    raw = raw_pattern(z=3, y=4, x=6)
    off = raw[..., None, :, :].copy()
    # First noise values/signals are equal, so fractions=.5,.5 and side
    # subtraction is exact zero. The next literal base-plane0 call must fail.
    with pytest.raises(api("AcquisitionModeError"), match="(?i)noise|zero|statistic"):
        api("prepare_acquisition_bands")(
            raw,
            **(
                options(
                    acquisition_mode="3d",
                    dxy_um=0.25,
                    off_exposures=off,
                    combine_off_orders=np.array([0, 1], dtype=np.int32),
                )
                | optics()
            ),
        )
