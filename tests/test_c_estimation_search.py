"""Independent complete CE05 coarse and literal refinement traces."""

from __future__ import annotations

import cmath
import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from c_estimation_fixture import (
    Build,
    Event,
    Expected,
    assert_expected,
    bands_record,
    close,
    estimate,
    events,
    expected_estimate,
    overlap,
    rejection,
    search_bands,
    tie_bands,
    transfer_record,
    unit_transfer,
)


@pytest.mark.parametrize("seed", [0, 1, 3, 4])
def test_complete_finite_search_trace_both_directions_and_alias_sequence(seed):
    bands = search_bands(seed)
    initial = np.array([[0.06, -0.035]])
    transfer = transfer_record()
    expected = expected_estimate(bands, transfer, initial)
    actual = estimate(bands, transfer, initial)
    assert_expected(actual, expected)
    assert actual.branches == (("searched",),)
    assert [(b.purpose, b.orders) for b in actual.overlaps] == [
        ("coarse", (0, 2)),
        ("refinement", (0, 2)),
        ("later-order", (0, 1)),
    ]
    evaluations = events(actual, "evaluation")
    frozen = [e for e in evaluations if e["stage"] in ("angle", "magnitude", "final")]
    assert all(e["overlap_index"] == 1 for e in frozen)
    assert frozen[0]["remake_overlaps"] is True
    assert all(e["remake_overlaps"] is False for e in frozen[1:])
    for e in evaluations:
        close(e["objective"], abs(e["forward"]) ** 2)
    brackets = events(actual, "bracket")
    angle_stop = next(e for e in brackets if e["stage"] == "angle" and e["branch"] == "stop")
    mag_initial = next(
        e for e in brackets if e["stage"] == "magnitude" and e["branch"] == "initial"
    )
    assert mag_initial["x1"] == angle_stop["x1"]
    assert mag_initial["amp1"] == angle_stop["amp1"]
    # An optimizer that resets the bracket loses this nonzero angle coordinate.
    assert angle_stop["x1"] != 0.0
    coarse = events(actual, "coarse")[0]
    assert abs(coarse["x_offset"]) <= 0.5
    assert abs(coarse["y_offset"]) <= 0.5
    if seed == 1:
        assert coarse["alias_decisions"] == (True, False, True, True)
    if seed in (3, 4):
        assert any(e["branch"] == "negative-swap" and e["stage"] == "angle" for e in brackets)


def zero_objective_case(profile):
    """Build reciprocal-scaled public inputs with safe finite helper arithmetic."""
    assert profile in ("height-one", "coarse-tie")
    bands = bands_record(shape=(2, 1, 4) if profile == "height-one" else (2, 4, 2))
    bands.quadratures.fill(0)
    if profile == "height-one":
        bands.quadratures[0, 0, 0, 0, 0, :] = [2, 0, 1]
        bands.quadratures[0, 0, 1, 0, 0, 0] = 5 / 32
        bands.quadratures[0, 0, 3, 0, 0, 1] = 0.5
        bands.quadratures[0, 0, 4, 0, 0, 1] = 0.5j
        initial = np.array([[-0.05, 0.0]])
    else:
        bands.quadratures[0, 0, 0, 0, 0, :] = [1, -1]
        bands.quadratures[0, 0, 1, 0, 0, 0] = 0.25
        bands.quadratures[0, 0, 3, 0, 1, 0] = 1
        initial = np.zeros((1, 2))
    bands.quadratures[:, :, 0] *= math.ldexp(1.0, 330)
    bands.quadratures[:, :, 1:] *= math.ldexp(1.0, -330)
    return bands, unit_transfer(3), initial


def assert_zero_objective_result(result, profile, fit_all):
    """Check exact decisions and independently scaled, nonzero-energy anchors."""

    def anchored(value, wanted, *, atol=3e-12):
        np.testing.assert_allclose(value, wanted, rtol=3e-11, atol=atol)

    up, down = math.ldexp(1.0, 660), math.ldexp(1.0, -660)
    coarse = events(result, "coarse")[0]
    if profile == "height-one":
        correlation = np.array([[0, 8, 0, 0]], dtype=np.complex128)
        power = np.array([[0, 64, 0, 0]], dtype=np.float64)
        peak, before, after, carrier = (1, 0), [1, 0], [1, 0], [0.125, 0]
        aliases = (False, False, False, False)
        x_neighbors, y_neighbors = [0, 64, 0], [64, 64, 64]
        x_status, y_status, angle0 = "fitted", "zero-curvature", 0.0
        sx, sy, later_sx, later_sy, later_cross = 20, 4, 20, 25 / 256, 5 / 4
        expected_raw1 = 1 / 16

        def cross_at(k):
            return sum(
                h * (-1j) ** j * cmath.exp(4j * math.pi * (j - 2) * k[0])
                for j, h in enumerate((3, 1, 3, 1))
            )
    else:
        correlation = np.zeros((4, 2), dtype=np.complex128)
        correlation[3] = [8, -8]
        power = np.zeros((4, 2))
        power[3] = [64, 64]
        peak, before, after, carrier = (0, 3), [0, 3], [0, -1], [0, -0.125]
        aliases = (False, False, True, False)
        x_neighbors, y_neighbors = [64, 64, 64], [0, 64, 0]
        x_status, y_status, angle0 = "zero-curvature", "fitted", -math.pi / 2
        sx, sy, later_sx, later_sy, later_cross = 8, 8, 16, 1 / 2, 2
        expected_raw1 = 1 / 8

        def cross_at(k):
            return sum(
                (1j) ** y * cmath.exp(4j * math.pi * ((x - 1) * k[0] + (y - 2) * k[1]))
                for y in range(4)
                for x in range(2)
            )

    anchored(coarse["correlation_complex"], correlation)
    anchored(coarse["correlation_power"], power)
    assert coarse["integer_peak_xy"] == peak
    assert coarse["alias_decisions"] == aliases
    anchored(coarse["x_neighbors"], x_neighbors)
    anchored(coarse["y_neighbors"], y_neighbors)
    anchored(coarse["peak_before_alias_xy"], before)
    anchored(coarse["peak_after_alias_xy"], after)
    anchored(coarse["carrier_cyc_um"], carrier)
    anchored([coarse["x_offset"], coarse["y_offset"]], [0, 0])
    assert (coarse["x_offset_status"], coarse["y_offset_status"]) == (x_status, y_status)
    maxima = np.argwhere(coarse["correlation_power"] == np.max(coarse["correlation_power"]))
    assert_array_equal(maxima, [[0, 1]] if profile == "height-one" else [[3, 0], [3, 1]])
    # Height one has floor(Y/2)=0: the two literal comparisons are 0<0 and 0>0.
    if profile == "height-one":
        assert coarse["alias_decisions"][2:] == (False, False)
        assert_array_equal(coarse["y_neighbors"], np.repeat(coarse["correlation_power"][0, 1], 3))

    signature = [
        (e.kind, dict(e.details).get("stage"), dict(e.details).get("branch")) for e in result.trace
    ]
    assert signature == [
        ("coarse", None, None),
        ("evaluation", "angle", None),
        ("evaluation", "angle", None),
        ("bracket", "angle", "initial"),
        ("bracket", "angle", "negative-swap"),
        ("bracket", "angle", "stop"),
        ("parabola", "angle", None),
        ("evaluation", "magnitude", None),
        ("evaluation", "magnitude", None),
        ("bracket", "magnitude", "initial"),
        ("bracket", "magnitude", "negative-swap"),
        ("bracket", "magnitude", "stop"),
        ("parabola", "magnitude", None),
        ("evaluation", "final", None),
        ("evaluation", "later-order", None),
        ("adjustment", None, None),
        ("adjustment", None, None),
    ]
    for event in events(result, "bracket"):
        assert event["x1"] == event["amp1"] == event["amp2"] == event["amp3"] == 0.0
        assert event["strict_improvement"] is False
    parabolas = events(result, "parabola")
    assert [p["status"] for p in parabolas] == [
        "duplicate-coordinate" if profile == "height-one" else "zero-curvature",
        "zero-curvature",
    ]
    assert all(p["result"] == 0.0 for p in parabolas)
    evaluations = events(result, "evaluation")
    expected_stages = ("angle", "angle", "magnitude", "magnitude", "final", "later-order")
    angles = (angle0, angle0 + 0.001, 0.0, 0.0, 0.0, 0.0)
    magnitudes = (0.125, 0.125, 0.125, 0.15, 0.0, 0.0)
    for i, (event, stage, a, m) in enumerate(
        zip(evaluations, expected_stages, angles, magnitudes, strict=True)
    ):
        vector = [m * math.cos(a), m * math.sin(a)]
        later = stage == "later-order"
        sxx, syy, cross = (later_sx, later_sy, later_cross) if later else (sx, sy, cross_at(vector))
        assert event["stage"] == stage and event["orders"] == (0, 1 if later else 2)
        assert event["overlap_index"] == (2 if later else 1)
        assert event["remake_overlaps"] is (i == 0 or later)
        anchored(event["angle_rad"], a)
        anchored(event["magnitude_cyc_um"], m)
        anchored(event["carrier_cyc_um"], vector)
        assert event["SX"] > 0 and event["SY"] > 0 and event["SX"] != event["SY"]
        assert math.isfinite(event["SX"] * event["SY"]) and event["SX"] * event["SY"] > 0
        for key in (
            "SX",
            "SY",
            "cross",
            "forward",
            "reverse",
            "combined",
            "correlation",
            "objective",
        ):
            assert np.isfinite(event[key])
        anchored(event["SX"] * down, sxx)
        anchored(event["SY"] * up, syy)
        anchored(event["cross"], cross)
        anchored(event["forward"] * up, cross / sxx)
        anchored(event["reverse"] * down, complex(cross).conjugate() / syy)
        # SX-SY rounds to SX; atan(t),tan(t/2) differ below binary64 resolution.
        anchored(event["combined"] * up, cross / sxx)
        anchored(event["correlation"], abs(cross) / math.sqrt(sxx * syy))
        assert event["objective"] == 0.0
        assert abs(event["forward"]) ** 2 == 0.0
    assert evaluations[0]["forward"] != 0j and evaluations[-1]["forward"] != 0j
    assert [(b.index, b.purpose, b.orders) for b in result.overlaps] == [
        (0, "coarse", (0, 2)),
        (1, "refinement", (0, 2)),
        (2, "later-order", (0, 1)),
    ]
    assert result.branches == (("searched",),)
    assert_array_equal(result.carriers_cyc_um, 0)
    # Fixed input-derived observation units, never a fitted gain or raw-zero claim.
    raw = result.raw_modulation * up
    np.testing.assert_allclose(raw, [[[expected_raw1, 0]]], rtol=3e-13, atol=3e-13)
    assert raw[0, 0, 0] != 0j
    adjustments = events(result, "adjustment")
    assert [a["order"] for a in adjustments] == [1, 2]
    for i, adjustment in enumerate(adjustments):
        assert adjustment["floor"] is None and adjustment["floor_applied"] is False
        assert adjustment["phase_replaced"] is (not fit_all and i == 1)
        assert adjustment["raw_forward"] == result.raw_modulation[0, 0, i]
        assert adjustment["after_floor"] == adjustment["raw_forward"]
        assert adjustment["final"] == result.modulation[0, 0, i]
    if fit_all:
        assert_array_equal(result.modulation, result.raw_modulation)
    else:
        assert result.modulation[0, 0, 0] == result.raw_modulation[0, 0, 0]
        expected_phase = abs(raw[0, 0, 1]) * cmath.exp(2j * cmath.phase(raw[0, 0, 0]))
        np.testing.assert_allclose(
            result.modulation[0, 0, 1] * up, expected_phase, rtol=3e-13, atol=0
        )


def zero_objective_observation(result, *, check_storage):
    """Express diagnostics in fixed input-derived units without changing decisions."""

    def array(value, dtype, *, exponent=None, pair=False):
        assert value.dtype == dtype
        if check_storage:
            assert value.flags.owndata and not value.flags.writeable
        assert np.isfinite(value).all()
        observed = np.array(value, copy=True)
        if pair:
            observed[0] *= math.ldexp(1.0, -330)
            observed[1] *= math.ldexp(1.0, 330)
        elif exponent is not None:
            observed *= math.ldexp(1.0, exponent)
        observed.flags.writeable = False
        return observed

    if check_storage:
        assert type(result.overlaps) is tuple and type(result.trace) is tuple
    overlaps = []
    for build in result.overlaps:
        overlaps.append(
            Build(
                index=build.index,
                time_index=build.time_index,
                direction_index=build.direction_index,
                purpose=build.purpose,
                orders=build.orders,
                carrier_cyc_um=array(build.carrier_cyc_um, np.float64),
                fourier=array(build.fourier, np.complex128, pair=True),
                spatial=array(build.spatial, np.complex128, pair=True),
                written=array(build.written, np.bool_),
            )
        )
    trace = []
    for event in result.trace:
        if check_storage:
            assert type(event.details) is tuple
        exponents = {}
        if event.kind == "evaluation":
            exponents = {"SX": -660, "SY": 660, "forward": 660, "reverse": -660, "combined": 660}
        elif event.kind == "adjustment":
            exponents = {"raw_forward": 660, "after_floor": 660, "final": 660}
        details = []
        for name, value in event.details:
            if isinstance(value, np.ndarray):
                value = array(value, value.dtype)
            elif name in exponents:
                value *= math.ldexp(1.0, exponents[name])
            details.append((name, value))
        trace.append(
            Event(
                kind=event.kind,
                time_index=event.time_index,
                direction_index=event.direction_index,
                details=tuple(details),
            )
        )
    # Objective and bracket/parabola scores remain the ORIGINAL binary64 zeros.
    # This is an observer representation, not a rescaled input to regression.
    return Expected(
        carriers_cyc_um=array(result.carriers_cyc_um, np.float64),
        raw_modulation=array(result.raw_modulation, np.complex128, exponent=660),
        modulation=array(result.modulation, np.complex128, exponent=660),
        branches=result.branches,
        overlaps=overlaps,
        trace=trace,
        coordinate_budget=0.0,
    )


@pytest.mark.parametrize("profile", ["height-one", "coarse-tie"])
@pytest.mark.parametrize("fit_all", [True, False])
def test_exact_ties_first_maximum_duplicate_coordinate_and_zero_curvature(profile, fit_all):
    bands, transfer, initial = zero_objective_case(profile)
    quadratures, noise = bands.quadratures.copy(), bands.noise_variance_factors.copy()
    samples, initial_before = transfer.samples.copy(), initial.copy()
    metadata = (
        bands.input_shape,
        bands.input_scale,
        bands.dxy_um,
        bands.dz_um,
        bands.lateral_zoom,
        bands.axial_zoom,
        bands.source_revision,
        bands.reference_sha256,
    )
    expected = expected_estimate(bands, transfer, initial, fit_all_phases=fit_all)
    actual = estimate(bands, transfer, initial, fit_all_phases=fit_all)
    assert_expected(
        zero_objective_observation(actual, check_storage=True),
        zero_objective_observation(expected, check_storage=False),
    )
    assert_zero_objective_result(actual, profile, fit_all)
    assert_array_equal(bands.quadratures, quadratures)
    assert_array_equal(bands.noise_variance_factors, noise)
    assert_array_equal(transfer.samples, samples)
    assert_array_equal(initial, initial_before)
    assert_array_equal(actual.initial_carriers_cyc_um, initial_before)
    assert metadata == (
        bands.input_shape,
        bands.input_scale,
        bands.dxy_um,
        bands.dz_um,
        bands.lateral_zoom,
        bands.axial_zoom,
        bands.source_revision,
        bands.reference_sha256,
    )


def test_final_order_two_keeps_frozen_pair_and_other_orders_remake_ascending():
    bands = search_bands(0, orders=5)
    initial = np.array([[0.06, -0.035]])
    transfer = transfer_record(6)
    expected = expected_estimate(bands, transfer, initial)
    actual = estimate(bands, transfer, initial)
    assert_expected(actual, expected)
    assert [(b.purpose, b.orders) for b in actual.overlaps] == [
        ("coarse", (0, 2)),
        ("refinement", (0, 2)),
        ("later-order", (0, 1)),
        ("later-order", (0, 3)),
        ("later-order", (0, 4)),
    ]
    final = next(e for e in events(actual, "evaluation") if e["stage"] == "final")
    close(actual.raw_modulation[0, 0, 1], final["forward"])
    remade = overlap(bands, transfer, expected.carriers_cyc_um[0, 0], 2)
    # This fixture distinguishes frozen final evaluation from a final remake.
    assert np.max(np.abs(remade.fourier - expected.overlaps[1].fourier)) > 1e-3


@pytest.mark.parametrize("reuse", [True, False])
def test_time_policy_refits_amplitude_and_search_all_restarts_declared_initial(reuse):
    bands = search_bands(0, times=2)
    initial = np.array([[0.06, -0.035]])
    transfer = transfer_record()
    expected = expected_estimate(bands, transfer, initial, use_time0_carriers=reuse)
    actual = estimate(bands, transfer, initial, **({} if reuse else {"use_time0_carriers": False}))
    assert_expected(actual, expected)
    assert actual.branches == (("searched",), ("time0-reused" if reuse else "searched",))
    assert not np.allclose(expected.raw_modulation[0], expected.raw_modulation[1])
    if reuse:
        assert_array_equal(actual.carriers_cyc_um[0], actual.carriers_cyc_um[1])
        assert len(events(actual, "coarse")) == 1
        assert [b.orders for b in actual.overlaps if b.time_index == 1] == [(0, 1), (0, 2)]
        known = [e for e in actual.trace if e.time_index == 1 and e.kind == "evaluation"]
        assert all(dict(e.details)["objective"] is None for e in known)
    else:
        assert not events(actual, "reuse")
        coarse_builds = [b for b in actual.overlaps if b.purpose == "coarse"]
        assert len(coarse_builds) == 2
        for b in coarse_builds:
            assert_array_equal(b.carrier_cyc_um, initial[0])


def test_zero_coarse_polar_error_is_earlier_than_empty_regression():
    bands = tie_bands()
    bands.quadratures.fill(0)
    rejection(
        bands,
        unit_transfer(3),
        np.zeros((1, 2)),
        "(?i)(polar|atan2|coarse.*zero|zero.*coarse|angle)",
    )


def test_omitted_zero_plane_search_has_earliest_coarse_polar_error():
    bands = tie_bands()
    rejection(
        bands,
        unit_transfer(3),
        np.zeros((1, 2)),
        "(?i)(polar|atan2|coarse.*zero|zero.*coarse|angle)",
        omit_kz0=True,
    )


def test_resolved_fundamental_guess_is_not_divided_by_highest_order():
    bands = search_bands(2)
    # Historical D=1, O=3 guess for linespacing 5um is 1/(5*2)=.1 cyc/um.
    initial = np.array([[1 / (5 * 2), 0]])
    transfer = transfer_record()
    expected = expected_estimate(bands, transfer, initial)
    actual = estimate(bands, transfer, initial)
    assert_expected(actual, expected)
    assert_array_equal(actual.initial_carriers_cyc_um, initial)
    assert_array_equal(actual.overlaps[0].carrier_cyc_um, initial[0])
    coarse = events(actual, "coarse")[0]
    close(coarse["carrier_cyc_um"], coarse["peak_after_alias_xy"] / [4, 3] / 2)
    starts = [e for e in events(actual, "evaluation") if e["stage"] == "angle"]
    close(starts[1]["angle_rad"] - starts[0]["angle_rad"], 0.001)
    mags = [e for e in events(actual, "evaluation") if e["stage"] == "magnitude"]
    close(mags[1]["magnitude_cyc_um"] - mags[0]["magnitude_cyc_um"], 0.025)
    assert math.isfinite(abs(actual.raw_modulation[0, 0, 1]))


def assert_nonzero_stale_tie_result(result):
    """Check the X2 E18 fixture against tightly bounded algebraic anchors."""

    # Derivation: A1-correction-2/conditioning.md. No accumulated generic parabola
    # allowance is used: equal active ordinates force the coordinate midpoint.
    def anchored(value, expected, *, atol=3e-14):
        np.testing.assert_allclose(value, expected, rtol=3e-13, atol=atol)

    m0, dm, fitted = 5 / 4, 1 / 8, 21 / 16
    active = 1 / 256
    q = 4 * math.pi * 0.2 * m0 * math.sin(0.001)
    cross_plus = (math.cos(2 * q) + 2 * math.cos(q) + 1 - 1j * math.sin(2 * q)) / 4
    carried = abs(cross_plus) ** 2 / 256
    assert 0 < carried < active

    signature = []
    for event in result.trace:
        details = dict(event.details)
        assert (event.time_index, event.direction_index) == (0, 0)
        signature.append((event.kind, details.get("stage"), details.get("branch")))
    assert signature == [
        ("coarse", None, None),
        ("evaluation", "angle", None),
        ("evaluation", "angle", None),
        ("bracket", "angle", "initial"),
        ("bracket", "angle", "negative-swap"),
        ("evaluation", "angle", None),
        ("bracket", "angle", "shift"),
        ("bracket", "angle", "stop"),
        ("parabola", "angle", None),
        ("evaluation", "magnitude", None),
        ("evaluation", "magnitude", None),
        ("bracket", "magnitude", "initial"),
        ("bracket", "magnitude", "negative-swap"),
        ("bracket", "magnitude", "stop"),
        ("parabola", "magnitude", None),
        ("evaluation", "final", None),
        ("evaluation", "later-order", None),
        ("adjustment", None, None),
        ("adjustment", None, None),
    ]
    coarse = events(result, "coarse")[0]
    correlation = np.zeros((4, 2), dtype=np.complex128)
    correlation[0] = [1, -4 / math.sqrt(10)]
    power = np.zeros((4, 2))
    power[0] = [1, 8 / 5]
    anchored(coarse["correlation_complex"], correlation)
    anchored(coarse["correlation_power"], power)
    assert coarse["integer_peak_xy"] == (1, 0)
    anchored(coarse["x_neighbors"], [1, 8 / 5, 1])
    anchored(coarse["y_neighbors"], [0, 8 / 5, 0])
    anchored(coarse["x_offset"], 0)
    anchored(coarse["y_offset"], 0)
    assert coarse["x_offset_status"] == coarse["y_offset_status"] == "fitted"
    assert coarse["alias_decisions"] == (False, False, False, False)
    anchored(coarse["peak_before_alias_xy"], [1, 0])
    anchored(coarse["peak_after_alias_xy"], [1, 0])
    anchored(coarse["carrier_cyc_um"], [m0, 0])

    assert [(b.purpose, b.orders, b.index) for b in result.overlaps] == [
        ("coarse", (0, 2), 0),
        ("refinement", (0, 2), 1),
        ("later-order", (0, 1), 2),
    ]
    scale = 1 / math.sqrt(2)
    spatial_rows = [
        (np.array([scale - 2 / math.sqrt(5), scale + 2 / math.sqrt(5)]), np.full(2, scale / 8)),
        (np.array([0, 2 * scale]), np.full(2, scale / 8)),
        (np.array([0, 2 * scale]), np.full(2, scale / 4)),
    ]
    for build, rows, k in zip(result.overlaps, spatial_rows, (0.5, m0, fitted), strict=True):
        anchored(build.carrier_cyc_um, [k, 0], atol=3e-11)
        for side in (0, 1):
            anchored(build.spatial[side], np.broadcast_to(rows[side], (2, 4, 2)))

    bracket_states = [
        ("angle", "initial", False, (0, 0, 0, active, 0.001, carried)),
        ("angle", "negative-swap", True, (0, 0, 0.001, carried, 0, active)),
        ("angle", "shift", False, (0.001, carried, 0, active, -0.001, carried)),
        ("angle", "stop", False, (0.001, carried, 0, active, -0.001, carried)),
        ("magnitude", "initial", False, (0.001, carried, m0, active, m0 + dm, active)),
        ("magnitude", "negative-swap", False, (0.001, carried, m0 + dm, active, m0, active)),
        ("magnitude", "stop", False, (0.001, carried, m0 + dm, active, m0, active)),
    ]
    for observed, (stage, branch, improvement, state) in zip(
        events(result, "bracket"), bracket_states, strict=True
    ):
        assert (observed["stage"], observed["branch"]) == (stage, branch)
        assert observed["strict_improvement"] is improvement
        anchored([observed[k] for k in ("x1", "x2", "x3")], state[::2], atol=2e-12)
        anchored([observed[k] for k in ("amp1", "amp2", "amp3")], state[1::2], atol=3e-16)
        if stage == "magnitude":
            assert observed["x1"] == 0.001
            assert 0 < observed["amp1"] < observed["amp2"]
            assert observed["amp2"] == observed["amp3"]
    angle, magnitude = events(result, "parabola")
    assert (angle["stage"], angle["status"]) == ("angle", "fitted")
    assert (magnitude["stage"], magnitude["status"]) == ("magnitude", "fitted")
    anchored(angle["result"], 0, atol=2e-11)
    anchored(magnitude["result"], fitted, atol=2e-12)
    anchored([magnitude[k] for k in ("x1", "x2", "x3")], [0.001, m0 + dm, m0], atol=2e-12)
    anchored([magnitude[k] for k in ("y1", "y2", "y3")], [carried, active, active], atol=3e-16)
    # Distinct coordinates, nonzero carried objective gap: a tie is not zero curvature.
    slope = (active - carried) / (m0 + dm - 0.001)
    curvature = -slope / ((m0 - 0.001) / 2)
    assert curvature < 0 and math.isfinite(curvature)

    expected_evaluations = [
        ("angle", 0.0, m0, True, 1, 1 / 8, 1 + 0j),
        ("angle", 0.001, m0, False, 1, 1 / 8, cross_plus),
        ("angle", -0.001, m0, False, 1, 1 / 8, cross_plus.conjugate()),
        ("magnitude", 0.0, m0, False, 1, 1 / 8, 1 + 0j),
        ("magnitude", 0.0, m0 + dm, False, 1, 1 / 8, 1 + 0j),
        ("final", 0.0, fitted, False, 1, 1 / 8, 1 + 0j),
        ("later-order", 0.0, fitted, True, 2, 1 / 2, 2 + 0j),
    ]
    for observed, (stage, a, m, remake, index, sy, cross) in zip(
        events(result, "evaluation"), expected_evaluations, strict=True
    ):
        assert observed["stage"] == stage
        assert observed["overlap_index"] == index
        assert observed["orders"] == (0, 1 if stage == "later-order" else 2)
        assert observed["remake_overlaps"] is remake
        anchored(observed["angle_rad"], a, atol=2e-11)
        anchored(observed["magnitude_cyc_um"], m, atol=2e-12)
        anchored(observed["SX"], 16)
        anchored(observed["SY"], sy)
        anchored(observed["cross"], cross, atol=1e-9)
        anchored(observed["forward"], cross / 16, atol=2e-11)
        anchored(observed["reverse"], cross.conjugate() / sy, atol=1e-9)
        beta = math.atan(2 * abs(cross) / (16 - sy)) / 2
        combined = math.tan(beta) * cross / abs(cross)
        anchored(observed["combined"], combined, atol=1e-9)
        anchored(observed["correlation"], abs(cross) / math.sqrt(16 * sy), atol=1e-9)
        anchored(observed["objective"], abs(cross / 16) ** 2, atol=3e-16)
        vector = [m * math.cos(a), m * math.sin(a)]
        anchored(observed["carrier_cyc_um"], vector, atol=3e-11)
    assert result.branches == (("searched",),)
    anchored(result.carriers_cyc_um[0, 0, 0], fitted, atol=2e-12)
    anchored(result.carriers_cyc_um[0, 0, 1], 0, atol=3e-11)
    anchored(result.raw_modulation, [[[1 / 8, 1 / 16]]], atol=2e-11)
    anchored(result.modulation, [[[1 / 8, 1 / 16]]], atol=2e-11)
    assert [x["order"] for x in events(result, "adjustment")] == [1, 2]
    for adjustment, factor in zip(events(result, "adjustment"), (1 / 8, 1 / 16), strict=True):
        assert adjustment["floor"] is None
        assert adjustment["floor_applied"] is adjustment["phase_replaced"] is False
        for key in ("raw_forward", "after_floor", "final"):
            anchored(adjustment[key], factor, atol=2e-11)


def test_initial_magnitude_tie_preserves_nonzero_angle_state_and_fits_midpoint():
    bands = bands_record(shape=(2, 4, 2), dxy=0.2)
    bands.quadratures.fill(0)
    for slot, gain in ((0, 1), (1, 1 / 4), (3, 1 / 8)):
        bands.quadratures[0, 0, slot, 0, 0, :] = [gain, -gain]
    samples = np.ones((3, 7, 1))
    samples[2, 3, 0] = 2
    transfer = transfer_record(3, samples=samples, dkr=0.5, dkz=1)
    result = estimate(bands, transfer, np.array([[0.5, 0.0]]))
    assert_nonzero_stale_tie_result(result)


@pytest.mark.parametrize("fit_all", [True, False])
def test_zero_higher_factor_keeps_defined_nonzero_order_one_phase(fit_all):
    bands = bands_record(orders=3, shape=(2, 1, 2))
    bands.quadratures.fill(0)
    pattern = np.array([[1, -1], [-1, 1]])
    gain = 0.25 + 0.125j
    bands.quadratures[0, 0, 0, :, 0, :] = pattern
    bands.quadratures[0, 0, 1, :, 0, :] = gain * pattern
    bands.quadratures[0, 0, 3, :, 0, :] = [[0, 1], [-1, 0]]
    before = bands.quadratures.copy()
    transfer, initial = unit_transfer(3), np.zeros((1, 2))
    options = dict(search_carriers=False, numerical_aperture=0.5, fit_all_phases=fit_all)
    expected = expected_estimate(bands, transfer, initial, **options)
    actual = estimate(bands, transfer, initial, **options)
    assert_expected(actual, expected)
    close(actual.raw_modulation, [[[gain, 0]]])
    close(actual.modulation, [[[gain, 0]]])
    assert actual.raw_modulation[0, 0, 1] == actual.modulation[0, 0, 1] == 0j
    assert actual.raw_modulation[0, 0, 0] != 0j
    first, second = events(actual, "evaluation")
    close([first["SX"], first["SY"]], [8, 5 / 8])
    close(first["cross"], 2 + 1j)
    close(first["forward"], gain)
    close(first["reverse"], 1 / gain)
    close(first["combined"], gain)
    close(first["correlation"], 1)
    close([second["SX"], second["SY"]], [8, 4])
    assert second["cross"] == second["forward"] == second["reverse"] == second["combined"] == 0j
    assert second["correlation"] == 0.0
    assert first["objective"] is second["objective"] is None
    assert [x["phase_replaced"] for x in events(actual, "adjustment")] == [False, not fit_all]
    assert actual.branches == (("known",),)
    assert_array_equal(bands.quadratures, before)
