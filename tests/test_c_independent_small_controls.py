"""CE08 phase 1: fixed raw mapping first, then actual finite fit composition.

Product execution is reserved for after independent B checkpoint acceptance.
Every oracle, input, budget and assertion here was authored before product calls.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np

from ce08_error_budget import budgets, gamma, norm
from ce08_finite_math import Array, acquire, geometry, prepare, reconstruct, registration, table
from ce08_finite_search import coarse, estimate, overlap, parabola, regression

# SHA-256 of the accepted archive's C-order little-endian float32 payloads.
RAW_SHA256 = {
    "known-noninteger": "465a09097323adef25f0355257207f0db3a43dc1d692fa023609af7c731606af",
    "known-signed-contrast": "d3f6fd34709449a719691f155aba234a43a2884c0598c41b4d7386cfa92c8a0e",
    "finite-search": "c9e6d5dc09aa985da81255a16c69d383fd1b2bc5c86f224c85fab03da430b28b",
}


def close(actual: Any, expected: Any, error: float) -> None:
    np.testing.assert_allclose(actual, expected, atol=error, rtol=0)


def local_close(actual: Any, expected: Any) -> None:
    """Local arithmetic envelope; no propagated input uncertainty or fitted gain."""
    if expected is None or isinstance(expected, (str, bool, tuple)):
        assert actual == expected
    else:
        magnitude = max(1.0, float(np.max(np.abs(np.asarray(expected)))))
        close(actual, expected, gamma(10000 * 256) * magnitude)


def prepared_product(raw: Array, p: dict[str, Any]) -> Any:
    from simrecon import prepare_bands

    _, y, x, _, _ = geometry(p)
    return prepare_bands(
        raw,
        **p["sampling"],
        norders=3,
        background=7.0,
        flatfield_slope=np.full((y, x), 2.0),
        exposure_background=np.full((1, 1, 5, 4), 3.0),
        phases_rad=None,
        edge_pixels=0,
        equalize=False,
        equalize_z=False,
        equalize_time=False,
    )


def known_product(bands: Any, transfer: Any, p: dict[str, Any], k: Array, a: Array) -> Any:
    from simrecon import reconstruct_known

    return reconstruct_known(
        bands,
        transfer,
        carriers_cyc_um=k[None],
        modulation=a[None],
        **p["optics"],
        **p["filtering"],
    )


def check_known(
    bands: Any,
    transfer: Any,
    p: dict[str, Any],
    raw: Array,
    expected_bands: Array,
    k: Array,
    a: Array,
) -> Any:
    h = table(p)
    bound = budgets(raw, expected_bands, h, p)
    expected_filtered, expected_image = reconstruct(expected_bands, h, p, k, a)
    actual = known_product(bands, transfer, p, k, a)
    close(actual.filtered_quadratures[0, 0], expected_filtered, bound["filtered_atol"])
    close(actual.image[0], expected_image, bound["known_image_atol"])
    close(actual.x_um, (np.arange(16) - 8) / 2, 0)
    close(actual.y_um, (np.arange(16) - 8) / 2, 0)
    close(actual.z_um, np.arange(4) - 2, 0)
    return actual


def check_local_trace(
    actual: Any, input_bands: Array, h: Array, p: dict[str, Any], expected: dict[str, Any]
) -> None:
    """Prove each coupled source operation, avoiding loose accumulated bounds.

    Public diagnostics are inputs to these local mathematical assertions. They
    never select the acquisition, truth, settings, branch topology or tolerance.
    The separate raw-origin oracle and full independently computed trace remain.
    """
    assert len(actual.overlaps) == len(expected["overlaps"]) == 3
    independent_builds: list[dict[str, Any]] = []
    for observed, reference in zip(actual.overlaps, expected["overlaps"], strict=True):
        assert observed.index == reference["index"]
        assert observed.purpose == reference["purpose"]
        assert observed.orders == reference["orders"]
        assert observed.time_index == observed.direction_index == 0
        independently_built = overlap(
            input_bands,
            h,
            p,
            np.array(observed.carrier_cyc_um),
            observed.orders[1],
            observed.purpose,
            observed.index,
        )
        independent_builds.append(independently_built)
        for name in ("fourier", "spatial"):
            values = independently_built[name]
            local_error = gamma(10000 * 256) * max(1.0, norm(values))
            close(getattr(observed, name), values, local_error)
        np.testing.assert_array_equal(observed.written, independently_built["written"])

    observed_events = actual.trace
    assert len(observed_events) == len(expected["trace"])
    for observed, reference in zip(observed_events, expected["trace"], strict=True):
        assert observed.kind == reference["kind"]
        assert observed.time_index == observed.direction_index == 0
        assert tuple(key for key, _ in observed.details) == tuple(reference["details"])
        d = dict(observed.details)
        for key in (
            "stage",
            "branch",
            "status",
            "orders",
            "overlap_index",
            "remake_overlaps",
            "strict_improvement",
            "order",
            "floor",
            "floor_applied",
            "phase_replaced",
        ):
            if key in reference["details"]:
                assert d[key] == reference["details"][key]

    coarse_trace: list[dict[str, Any]] = []
    initial = np.array(p["controls"][-1]["initial_cyc_um"])
    k0 = coarse(independent_builds[0], initial, p, coarse_trace)
    for key, value in coarse_trace[0]["details"].items():
        local_close(dict(observed_events[0].details)[key], value)
    local_close(actual.overlaps[0].carrier_cyc_um, initial)
    local_close(actual.overlaps[1].carrier_cyc_um, k0)
    local_close(actual.overlaps[2].carrier_cyc_um, actual.carriers_cyc_um[0, 0])
    mag0, angle0 = float(np.linalg.norm(k0)), math.atan2(k0[1], k0[0])
    states: dict[str, dict[str, Any]] = {}
    fitted: dict[str, float] = {}
    evaluations: dict[str, list[dict[str, Any]]] = {}
    directions: dict[str, int] = {}
    steps = {"angle": 0.001, "magnitude": 0.0125}
    starts = {"angle": angle0, "magnitude": mag0}
    final_factors: dict[int, complex] = {}
    for observed in observed_events[1:]:
        d = dict(observed.details)
        stage = d.get("stage")
        if observed.kind in {"evaluation", "bracket", "parabola"}:
            assert isinstance(stage, str)
        else:
            stage = ""
        if observed.kind == "evaluation":
            build = independent_builds[d["overlap_index"]]
            theta, mag = d["angle_rad"], d["magnitude_cyc_um"]
            if stage in {"angle", "magnitude"}:
                probe_index = len(evaluations.get(stage, []))
                if probe_index < 2:
                    candidate = starts[stage] + probe_index * steps[stage]
                else:
                    previous = states[stage]
                    assert previous["branch"] in {"positive", "negative-swap", "shift"}
                    assert previous["strict_improvement"] is True
                    candidate = previous["x3"] + directions[stage] * steps[stage]
                required_theta = candidate if stage == "angle" else fitted["angle"]
                required_mag = mag0 if stage == "angle" else candidate
            else:
                assert stage in {"final", "later-order"}
                required_theta, required_mag = fitted["angle"], fitted["magnitude"]
            local_close(theta, required_theta)
            local_close(mag, required_mag)
            required_k = required_mag * np.array(
                (math.cos(required_theta), math.sin(required_theta))
            )
            local_close(d["carrier_cyc_um"], required_k)
            # Refit at the required candidate, not a freely reported probe.
            # Bracket amp2/amp3 below consume this evaluation's checked objective.
            fitted_diagnostics = regression(build, required_k, p, True)
            for key, value in fitted_diagnostics.items():
                local_close(d[key], value)
            if stage in {"final", "later-order"}:
                final_factors[build["orders"][1]] = d["forward"]
            evaluations.setdefault(stage, []).append(d)
        elif observed.kind == "bracket":
            step = steps[stage]
            start = starts[stage]
            branch = d["branch"]
            if branch == "initial":
                previous = states.get("angle", {}) if stage == "magnitude" else {}
                local_close(d["x1"], previous.get("x1", 0.0))
                local_close(d["amp1"], previous.get("amp1", 0.0))
                local_close(d["x2"], start)
                local_close(d["x3"], start + step)
                local_close(d["amp2"], evaluations[stage][0]["objective"])
                local_close(d["amp3"], evaluations[stage][1]["objective"])
            else:
                previous = states[stage]
                if branch == "positive":
                    assert previous["amp3"] > previous["amp2"]
                    directions[stage] = 1
                    for key in ("x1", "amp1", "x2", "amp2", "x3", "amp3"):
                        local_close(d[key], previous[key])
                elif branch == "negative-swap":
                    assert previous["amp3"] <= previous["amp2"]
                    directions[stage] = -1
                    for key in ("x1", "amp1"):
                        local_close(d[key], previous[key])
                    for first, second in (("x2", "x3"), ("amp2", "amp3")):
                        local_close(d[first], previous[second])
                        local_close(d[second], previous[first])
                elif branch == "shift":
                    assert previous["amp3"] > previous["amp2"]
                    local_close(d["x1"], previous["x2"])
                    local_close(d["amp1"], previous["amp2"])
                    local_close(d["x2"], previous["x3"])
                    local_close(d["amp2"], previous["amp3"])
                    local_close(d["x3"], previous["x3"] + directions[stage] * step)
                    local_close(d["amp3"], evaluations[stage][-1]["objective"])
                elif branch == "stop":
                    assert previous["amp3"] <= previous["amp2"]
                    for key in ("x1", "amp1", "x2", "amp2", "x3", "amp3"):
                        local_close(d[key], previous[key])
            assert d["strict_improvement"] is bool(d["amp3"] > d["amp2"])
            states[stage] = d
        elif observed.kind == "parabola":
            state = states[stage]
            points: list[float] = []
            for i in (1, 2, 3):
                local_close(d[f"x{i}"], state[f"x{i}"])
                local_close(d[f"y{i}"], state[f"amp{i}"])
                points.extend((d[f"x{i}"], d[f"y{i}"]))
            local_trace: list[dict[str, Any]] = []
            value = parabola(points, stage, local_trace)
            local_close(d["result"], value)
            assert d["status"] == local_trace[0]["details"]["status"]
            fitted[stage] = value
        elif observed.kind == "adjustment":
            order = d["order"]
            for key in ("raw_forward", "after_floor", "final"):
                local_close(d[key], final_factors[order])
            local_close(actual.raw_modulation[0, 0, order - 1], final_factors[order])
            local_close(actual.modulation[0, 0, order - 1], final_factors[order])
    final_k = fitted["magnitude"] * np.array((math.cos(fitted["angle"]), math.sin(fitted["angle"])))
    local_close(actual.carriers_cyc_um[0, 0], final_k)


def test_independent_small_controls_known_before_finite_nuisance() -> None:
    from simrecon import declare_otf, estimate_parameters

    p = registration()
    h = table(p)
    transfer = declare_otf(h, layout="radial", dkr_cyc_um=0.125, dkz_cyc_um=0.25)
    a = np.array([complex(*v) for v in p["source"]["side_modulation_pairs"]])
    for control in p["controls"]:
        name = control["name"]
        raw = np.asarray(acquire(p, control)["raw"])
        assert raw.shape == tuple(p["shape_TDPZYX"]) and raw.dtype == np.dtype("float32")
        assert (
            hashlib.sha256(raw.astype("<f4", copy=False).tobytes()).hexdigest() == RAW_SHA256[name]
        )
        expected_bands = prepare(raw, p)
        bands = prepared_product(raw, p)
        bound = budgets(raw, expected_bands, h, p)
        close(bands.quadratures[0, 0], expected_bands, bound["bands_atol"])
        fixed = check_known(
            bands, transfer, p, raw, expected_bands, np.array(control["carrier_cyc_um"]), a
        )
        if name == "known-signed-contrast":
            assert np.min(fixed.image) < 0 < np.max(fixed.image)
        if not control["search"]:
            continue
        # All fixed mappings above have passed before the first product
        # nuisance call. Expectations here still start at independent raw.
        expected = estimate(expected_bands, h, p, np.array(control["initial_cyc_um"]))
        complete = budgets(raw, expected_bands, h, p, expected)
        actual = estimate_parameters(
            bands,
            transfer,
            initial_carriers_cyc_um=np.array([control["initial_cyc_um"]]),
            **p["optics"],
            **p["estimation"],
        )
        assert actual.branches == (("searched",),)
        close(actual.carriers_cyc_um[0, 0], expected["carrier"], complete["carrier_atol"])
        close(actual.modulation[0, 0], expected["modulation"], complete["modulation_atol"])
        check_local_trace(actual, bands.quadratures[0, 0], h, p, expected)
        # The actual estimate is the public input to reconstruct_known.
        # This conditional operator assertion supplements the independent
        # raw-to-finite-result reference; it never refits truth or gain.
        consumed_k, consumed_a = actual.carriers_cyc_um[0, 0], actual.modulation[0, 0]
        check_known(bands, transfer, p, raw, expected_bands, consumed_k, consumed_a)
