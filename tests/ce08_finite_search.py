"""CE08 independent finite nuisance decisions from public CE05 equations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ce08_finite_math import CD, LD, TAU, Array, finite_sum, geometry, read_band, sample, signed


def overlap(
    bands: Array, h: Array, p: dict[str, Any], k: Array, order: int, purpose: str, index: int
) -> dict[str, Any]:
    z, y, x, radius, cutoff = geometry(p)
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    f = np.zeros((2, z, y, x), dtype=CD)
    written = np.zeros(f.shape, dtype=bool)
    for iy, ix in np.ndindex((y, x)):
        q = np.array((signed(ix, x) / x, signed(iy, y) / y))
        if np.linalg.norm(q) > radius:
            continue
        for side, offset in ((0, -order * k), (1, order * k)):
            other = q + offset
            if np.linalg.norm(other) > radius:
                continue
            for iz in range(-cutoff, cutoff + 1):
                first = sample(h, 0 if side == 0 else order, float(q[0]), float(q[1]), iz)
                if abs(first) * (1 if side == 0 else 5) <= 0.006:
                    continue
                second = sample(h, order if side == 0 else 0, float(other[0]), float(other[1]), iz)
                if abs(second) * (5 if side == 0 else 1) <= 0.006:
                    continue
                value = read_band(
                    bands, 0 if side == 0 else order, iz, signed(iy, y), signed(ix, x)
                )
                f[side, iz % z, iy, ix] = value * second / math.hypot(abs(first), abs(second))
                written[side, iz % z, iy, ix] = True
    return {
        "index": index,
        "time_index": 0,
        "direction_index": 0,
        "purpose": purpose,
        "orders": (0, order),
        "carrier_cyc_um": k.copy(),
        "fourier": f,
        "spatial": np.stack([finite_sum(v, +1) for v in f]),
        "written": written,
    }


def regression(
    build: dict[str, Any], k: Array, p: dict[str, Any], objective: bool
) -> dict[str, Any]:
    z, y, x, _, _ = geometry(p)
    yy, xx = np.indices((y, x), dtype=LD)
    ramp = np.exp(CD(1j) * TAU * build["orders"][1] * ((xx - x // 2) * k[0] + (yy - y // 2) * k[1]))
    lower = build["spatial"][0]
    higher = build["spatial"][1] * ramp
    sx = float(np.sum(abs(lower) ** 2, dtype=LD))
    sy = float(np.sum(abs(higher) ** 2, dtype=LD))
    cross = complex(np.sum(np.conj(lower) * higher, dtype=CD))
    assert sx > 0 and sy > 0 and sx != sy
    forward, reverse = cross / sx, np.conj(cross) / sy
    beta = 0.5 * math.atan(2 * abs(cross) / (sx - sy))
    if beta < 0:
        beta += math.pi / 2
    combined = 0j if cross == 0 else math.tan(beta) * cross / abs(cross)
    return {
        "SX": sx,
        "SY": sy,
        "cross": cross,
        "forward": forward,
        "reverse": complex(reverse),
        "combined": combined,
        "correlation": math.sqrt(abs(cross) ** 2 / (sx * sy)),
        "objective": abs(forward) ** 2 if objective else None,
    }


def event(trace: list[dict[str, Any]], kind: str, **details: Any) -> None:
    trace.append({"kind": kind, "time_index": 0, "direction_index": 0, "details": details})


def coarse(
    build: dict[str, Any], initial: Array, p: dict[str, Any], trace: list[dict[str, Any]]
) -> Array:
    _, y, x, _, _ = geometry(p)
    v = np.sum(build["spatial"][0] * np.conj(build["spatial"][1]), axis=0)
    corr = finite_sum(v, -1)
    power = abs(corr) ** 2
    # np.argmax is first row-major. This is equivalent to the strict scan for
    # this finite nonnegative map, not an independent local-maximum heuristic.
    iy, ix = np.unravel_index(int(np.argmax(power)), power.shape)
    neighbors: list[Array] = []
    offsets: list[float] = []
    statuses: list[str] = []
    for vals in (
        power[iy, [(ix - 1) % x, ix, (ix + 1) % x]],
        power[[(iy - 1) % y, iy, (iy + 1) % y], ix],
    ):
        minus, center, plus = (float(v) for v in vals)
        curvature = plus + minus - 2 * center
        offset = 0.0 if curvature == 0 else -(plus - minus) / (2 * curvature)
        status = "zero-curvature" if curvature == 0 else "fitted"
        if abs(offset) > 1.5:
            offset, status = 0.0, "outside-range"
        neighbors.append(vals)
        offsets.append(offset)
        statuses.append(status)
    peak = np.array((ix + offsets[0], iy + offsets[1]))
    before = peak.copy()
    decisions: list[bool] = []
    for axis, size in ((0, x), (1, y)):
        subtract = bool(initial[axis] / size < peak[axis] - size // 2)
        if subtract:
            peak[axis] -= size
        decisions.append(subtract)
        add = bool(initial[axis] / size > peak[axis] + size // 2)
        if add:
            peak[axis] += size
        decisions.append(add)
    k = peak / np.array((2 * x, 2 * y))
    event(
        trace,
        "coarse",
        overlap_index=build["index"],
        correlation_complex=corr,
        correlation_power=power,
        integer_peak_xy=(int(ix), int(iy)),
        x_neighbors=neighbors[0],
        y_neighbors=neighbors[1],
        x_offset=offsets[0],
        y_offset=offsets[1],
        x_offset_status=statuses[0],
        y_offset_status=statuses[1],
        peak_before_alias_xy=before,
        alias_decisions=tuple(decisions),
        peak_after_alias_xy=peak,
        carrier_cyc_um=k,
    )
    return k


def parabola(points: list[float], stage: str, trace: list[dict[str, Any]]) -> float:
    x1, y1, x2, y2, x3, y3 = points
    status = "duplicate-coordinate"
    result = 0.0
    if len({x1, x2, x3}) == 3:
        b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
        s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
        curvature = (s2 - s1) / (b2 - b1)
        status = "zero-curvature" if curvature == 0 else "fitted"
        if curvature != 0:
            result = b2 - s2 / curvature
    event(
        trace,
        "parabola",
        stage=stage,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        x3=x3,
        y3=y3,
        result=result,
        status=status,
    )
    return result


def estimate(bands: Array, h: Array, p: dict[str, Any], initial: Array) -> dict[str, Any]:
    """Full one-time/one-direction search; no optimizer and no product calls."""
    trace: list[dict[str, Any]] = []
    builds = [overlap(bands, h, p, initial, 2, "coarse", 0)]
    k0 = coarse(builds[0], initial, p, trace)
    assert np.linalg.norm(k0) != 0
    mag0 = float(np.linalg.norm(k0))
    angle0 = math.atan2(k0[1], k0[0])
    builds.append(overlap(bands, h, p, k0, 2, "refinement", 1))
    raw = np.zeros(2, dtype=np.complex128)

    def evaluate(
        stage: str, angle: float, magnitude: float, build: dict[str, Any], remake: bool
    ) -> float:
        k = magnitude * np.array((math.cos(angle), math.sin(angle)))
        fit = regression(build, k, p, True)
        event(
            trace,
            "evaluation",
            stage=stage,
            orders=build["orders"],
            overlap_index=build["index"],
            remake_overlaps=remake,
            angle_rad=angle,
            magnitude_cyc_um=magnitude,
            carrier_cyc_um=k,
            **fit,
        )
        if stage in {"final", "later-order"}:
            raw[build["orders"][1] - 1] = fit["forward"]
        return fit["objective"]

    stale = [0.0, 0.0]

    def refine(stage: str, start: float, step: float, fixed: float) -> float:
        def objective(value: float, remake: bool = False) -> float:
            angle, mag = (value, fixed) if stage == "angle" else (fixed, value)
            return evaluate(stage, angle, mag, builds[1], remake)

        x1, amp1 = stale
        x2, x3 = start, start + step
        amp2 = objective(x2, stage == "angle")
        amp3 = objective(x3)

        def bracket(branch: str) -> None:
            event(
                trace,
                "bracket",
                stage=stage,
                branch=branch,
                x1=x1,
                amp1=amp1,
                x2=x2,
                amp2=amp2,
                x3=x3,
                amp3=amp3,
                strict_improvement=bool(amp3 > amp2),
            )

        bracket("initial")
        if amp3 > amp2:
            candidate, direction = start + step, step
            bracket("positive")
        else:
            candidate, direction = start, -step
            x2, x3, amp2, amp3 = x3, x2, amp3, amp2
            bracket("negative-swap")
        while amp3 > amp2:
            x1, amp1, x2, amp2 = x2, amp2, x3, amp3
            candidate += direction
            x3, amp3 = candidate, objective(candidate)
            bracket("shift")
        bracket("stop")
        stale[:] = [x1, amp1]
        return parabola([x1, amp1, x2, amp2, x3, amp3], stage, trace)

    angle = refine("angle", angle0, 0.001, mag0)
    mag = refine("magnitude", mag0, 0.1 / 8, angle)
    evaluate("final", angle, mag, builds[1], False)
    carrier = mag * np.array((math.cos(angle), math.sin(angle)))
    builds.append(overlap(bands, h, p, carrier, 1, "later-order", 2))
    evaluate("later-order", angle, mag, builds[2], True)
    for m in (1, 2):
        event(
            trace,
            "adjustment",
            order=m,
            raw_forward=complex(raw[m - 1]),
            floor=None,
            floor_applied=False,
            after_floor=complex(raw[m - 1]),
            phase_replaced=False,
            final=complex(raw[m - 1]),
        )
    return {"carrier": carrier, "modulation": raw, "overlaps": builds, "trace": trace}
