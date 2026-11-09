"""Pre-product component/norm envelopes for the small CE08 controls.

The stable-transform model is explicit, conservative and conditional. It is
not an assertion about historical C/libm rounding. Scientific decisions are
checked against their own error intervals, never given a numerical tolerance.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from ce08_finite_math import Array, geometry, read_band, sample


def gamma(n: int) -> float:
    u = 2.0**-53
    return n * u / (1 - n * u)


def norm(value: Array) -> float:
    return float(np.linalg.norm(value.ravel()))


def interval_op(
    a: tuple[float, float], b: tuple[float, float], operation: str
) -> tuple[float, float]:
    if operation == "+":
        values = [a[0] + b[0], a[1] + b[1]]
    elif operation == "-":
        values = [a[0] - b[1], a[1] - b[0]]
    elif operation == "*":
        values = [x * y for x in a for y in b]
    else:
        assert b[0] * b[1] > 0, "unresolved parabola divisor in error propagation"
        values = [x / y for x in a for y in b]
    return math.nextafter(min(values), -math.inf), math.nextafter(max(values), math.inf)


def parabola_error(details: dict[str, Any], ex: float, ey: float) -> float:
    def interval(key: str, error: float) -> tuple[float, float]:
        value = details[key]
        return value - error, value + error

    x1, x2, x3 = (interval(key, ex) for key in ("x1", "x2", "x3"))
    y1, y2, y3 = (interval(key, ey) for key in ("y1", "y2", "y3"))
    b1 = interval_op(interval_op(x1, x2, "+"), (2.0, 2.0), "/")
    b2 = interval_op(interval_op(x2, x3, "+"), (2.0, 2.0), "/")
    s1 = interval_op(interval_op(y2, y1, "-"), interval_op(x2, x1, "-"), "/")
    s2 = interval_op(interval_op(y3, y2, "-"), interval_op(x3, x2, "-"), "/")
    curvature = interval_op(interval_op(s2, s1, "-"), interval_op(b2, b1, "-"), "/")
    result = interval_op(b2, interval_op(s2, curvature, "/"), "-")
    return max(abs(result[0] - details["result"]), abs(result[1] - details["result"]))


def budgets(
    raw: Array, bands: Array, h: Array, p: dict[str, Any], estimated: dict[str, Any] | None = None
) -> dict[str, Any]:
    z, y, x, _, _ = geometry(p)
    n = z * y * x
    eta = gamma(64 * n * math.ceil(math.log2(2 * n)) + 32 * n)
    alpha = 1 / (4 * n)
    corrected = alpha * 2 * (raw.astype(float) - 10)
    # Unnormalized DFT has Euclidean operator norm sqrt(N); five bounded
    # separation rows have abs(row)<=1. Include both observer and FFT envelope.
    eb = eta * 5 * math.sqrt(n) * norm(corrected)
    result: dict[str, Any] = {
        "eta": eta,
        "bands_l2": eb,
        "bands_atol": eb,
        "filtered_atol": 8 * eb / (0.35**2),
        "known_image_atol": 40 * math.sqrt(n) * eb / (0.35**2),
    }
    if estimated is None:
        return result
    builds = estimated["overlaps"]

    def overlap_error(build: dict[str, Any], ek: float) -> tuple[float, float]:
        norms = [norm(v) for v in build["spatial"]]
        order = build["orders"][1]
        # Only successful branches contribute. Scalar radial table slopes bound
        # |dH/dr|<=2.1 on the entire used stencil. Native first H is fixed;
        # the shifted H changes by <=2.1*order*|delta_k|.
        minimum = math.inf
        for side, iz, iy, ix in np.argwhere(build["written"]):
            q = np.array((signed_index(ix, x) / x, signed_index(iy, y) / y))
            other = q + (-1 if side == 0 else 1) * order * build["carrier_cyc_um"]
            first = sample(
                h, 0 if side == 0 else order, float(q[0]), float(q[1]), signed_index(iz, z)
            )
            second = sample(
                h, order if side == 0 else 0, float(other[0]), float(other[1]), signed_index(iz, z)
            )
            minimum = min(minimum, math.hypot(abs(first), abs(second)))
        full_band = np.array(
            [
                read_band(
                    bands, order, signed_index(iz, z), signed_index(iy, y), signed_index(ix, x)
                )
                for iz, iy, ix in np.ndindex((z, y, x))
            ]
        )
        movement = 2 * 2.1 * order * ek / minimum * max(norm(bands[0]), norm(full_band))
        return tuple(
            math.sqrt(n) * (math.sqrt(2) * eb + movement) + (eta + gamma(200)) * v for v in norms
        )  # type: ignore[return-value]

    def fit_error(
        build: dict[str, Any], errors: tuple[float, float], ek: float
    ) -> dict[str, float]:
        nx, ny = (norm(v) for v in build["spatial"])
        ex, ey = errors
        ey += ny * 2 * math.pi * build["orders"][1] * math.hypot(x // 2, y // 2) * ek
        esx = 2 * nx * ex + ex**2 + gamma(8 * n) * nx**2
        esy = 2 * ny * ey + ey**2 + gamma(8 * n) * ny**2
        ec = nx * ey + ny * ex + ex * ey + gamma(16 * n) * nx * ny
        assert nx**2 > esx and ny**2 > esy
        # |cross|<=nx*ny, a norm bound rather than observed favorable phase.
        ef = (ec + (ny / nx) * esx) / (nx**2 - esx)
        er = (ec + (nx / ny) * esy) / (ny**2 - esy)
        return {
            "SX": esx,
            "SY": esy,
            "cross": ec,
            "forward": ef,
            "reverse": er,
            "objective": 2 * (ny / nx) * ef + ef**2,
            "combined": 10 * (ef + er),
            "correlation": 10 * (ef + er),
        }

    ex, ey = overlap_error(builds[0], 0)
    nx, ny = (norm(v) for v in builds[0]["spatial"])
    ec = nx * ey + ny * ex + ex * ey + eta * nx * ny
    coarse = estimated["trace"][0]["details"]
    epower = 2 * abs(coarse["correlation_complex"]) * ec + ec**2
    offsets: list[float] = []
    peak = coarse["integer_peak_xy"]
    for axis in (0, 1):
        values = coarse["x_neighbors" if axis == 0 else "y_neighbors"]
        indices = [
            ((peak[1], (peak[0] + d) % x) if axis == 0 else ((peak[1] + d) % y, peak[0]))
            for d in (-1, 0, 1)
        ]
        errors = [float(epower[idx]) for idx in indices]
        slope = float((values[2] - values[0]) / 2)
        curvature = float(values[2] + values[0] - 2 * values[1])
        es = (errors[0] + errors[2]) / 2
        ecurv = errors[0] + errors[2] + 2 * errors[1]
        assert abs(curvature) > ecurv
        offsets.append(
            (es * abs(curvature) + abs(slope) * ecurv) / (abs(curvature) * (abs(curvature) - ecurv))
        )
    ek0 = math.hypot(offsets[0] / (2 * x), offsets[1] / (2 * y))
    mags = [
        e["details"]["magnitude_cyc_um"] for e in estimated["trace"] if e["kind"] == "evaluation"
    ]
    mag0 = mags[0]
    ea0 = ek0 / (mag0 - ek0)
    frozen_error = overlap_error(builds[1], ek0)
    angle_fit = fit_error(builds[1], frozen_error, ek0 + mag0 * ea0)
    parabolas = [e["details"] for e in estimated["trace"] if e["kind"] == "parabola"]
    ea = parabola_error(parabolas[0], ea0, angle_fit["objective"])
    magnitude_fit = fit_error(builds[1], frozen_error, ek0 + max(mags) * ea)
    em = parabola_error(parabolas[1], ek0, magnitude_fit["objective"])
    ek = em + max(mags) * ea
    final_fit = fit_error(builds[1], frozen_error, ek)
    later_error = overlap_error(builds[2], ek)
    later_fit = fit_error(builds[2], later_error, ek)
    result.update(
        {
            "coarse_complex_atol": ec,
            "coarse_power_atol": float(np.max(epower)),
            "overlap_initial_atol": max(ex, ey),
            "overlap_refinement_atol": max(frozen_error),
            "overlap_later_atol": max(later_error),
            "coarse_carrier_atol": ek0,
            "angle_atol": ea,
            "magnitude_atol": em,
            "carrier_atol": ek,
            "angle_fit": angle_fit,
            "magnitude_fit": magnitude_fit,
            "final_fit": final_fit,
            "later_fit": later_fit,
            "modulation_atol": max(final_fit["forward"], later_fit["forward"]),
        }
    )
    return result


def signed_index(index: Any, length: int) -> int:
    value = int(index)
    return value if value <= length // 2 else value - length
