"""Independent RA09 observations, exact geometry and direct-sum regression.

No product fit is called here. Carrier products and support use rational
arithmetic on represented inputs. Trigonometric arguments are reduced before
conversion to binary64. All arithmetic allowances are fixed before observation.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

import numpy as np
from numpy.typing import NDArray

ComplexArray = NDArray[np.complex128]
RealArray = NDArray[np.float64]
IntArray = NDArray[np.intp]
EPS = 2.0**-52
# <=125 direct-sum terms, <=2*125 regression coordinates. This allowance is
# 2^16*M*eps divided by a declared bounded-operand nonzero norm floor 1/16.
# The chosen controls check that floor independently; no output selects it.
NORM_FLOOR = 1.0 / 16.0
VALUE_ATOL = 65536 * 125 * EPS / NORM_FLOOR
DIAGNOSTIC_ATOL = 8 * VALUE_ATOL / (1.0 / 1024.0)
RECOVERY_PHASE_ATOL = 0.04  # radians, field-wide; solver control, not a theorem
RECOVERY_GAIN_ATOL = 0.02


def bins(length: int) -> range:
    return range(-(length // 2), (length + 1) // 2)


def rational(value: float) -> Fraction:
    return Fraction.from_float(float(value))


def overlap(
    shape: tuple[int, int, int], spacing: tuple[float, float, float], bounds: RealArray, order: int
) -> IntArray:
    """Exact all-box membership; native lexicographic bins, no tolerance."""
    result = []
    for q in itertools.product(*(bins(k) for k in shape)):
        good = True
        for a in (1, 2):
            extent = order * shape[a] * rational(spacing[a])
            lo = q[a] + extent * rational(bounds[0, a - 1])
            hi = q[a] + extent * rational(bounds[1, a - 1])
            good &= lo >= -(shape[a] // 2) and hi <= (shape[a] - 1) // 2
        if good:
            result.append(q)
    return np.asarray(result, dtype=np.intp).reshape(-1, 3)


def shifted(
    q: NDArray[np.intp],
    shape: tuple[int, int, int],
    spacing: tuple[float, float, float],
    carrier: tuple[float, float],
    order: int,
) -> tuple[Fraction, Fraction, Fraction]:
    return (
        Fraction(int(q[0])),
        Fraction(int(q[1])) + order * shape[1] * rational(spacing[1]) * rational(carrier[0]),
        Fraction(int(q[2])) + order * shape[2] * rational(spacing[2]) * rational(carrier[1]),
    )


def finite_sum(values: ComplexArray, t: tuple[Fraction, Fraction, Fraction]) -> complex:
    """Sum the normalized negative-exponent finite transform independently."""
    terms = []
    for n in np.ndindex(values.shape):
        turns = sum((t[a] * n[a] / values.shape[a] for a in range(3)), Fraction()) % 1
        angle = -math.tau * float(turns)
        terms.append(complex(values[n]) * complex(math.cos(angle), math.sin(angle)))
    return complex(math.fsum(z.real for z in terms), math.fsum(z.imag for z in terms)) / values.size


def interpolate(values: ComplexArray, t: tuple[Fraction, Fraction, Fraction]) -> complex:
    """Tensor-product Cartesian linear weights on exact native bin nodes."""
    choices = []
    for a, x in enumerate(t):
        lower = math.floor(x)
        weight = x - lower
        if not weight:
            choices.append([(lower + values.shape[a] // 2, 1.0)])
        else:
            choices.append(
                [
                    (lower + values.shape[a] // 2, float(1 - weight)),
                    (lower + 1 + values.shape[a] // 2, float(weight)),
                ]
            )
    terms = []
    for corner in itertools.product(*choices):
        index = tuple(p[0] for p in corner)
        terms.append(complex(values[index]) * math.prod(p[1] for p in corner))
    return complex(math.fsum(z.real for z in terms), math.fsum(z.imag for z in terms))


def component_scale(values: ComplexArray) -> float:
    return max(float(np.max(np.abs(values.real))), float(np.max(np.abs(values.imag)))) or 1.0


def stable_norm(values: ComplexArray) -> float:
    return math.hypot(*(float(x) for z in values for x in (z.real, z.imag)))


@dataclass(frozen=True)
class Point:
    """Store independent normalized regression coordinates and raw norm scales."""

    objective: float
    gains: tuple[complex | None, ...]
    statuses: tuple[str, ...]
    coherence: tuple[float | None, ...]
    relative: tuple[float | None, ...]
    logx: tuple[float | None, ...]
    logy: tuple[float | None, ...]
    residual: RealArray
    informative: tuple[bool, ...]
    scaled_norms: tuple[tuple[float, float], ...]


def evaluate(
    bands: ComplexArray, cal: Any, bounds: RealArray, carrier: tuple[float, float]
) -> Point:
    shape = tuple(bands.shape[1:])
    assert len(shape) == 3
    shape3 = (shape[0], shape[1], shape[2])
    scales = [component_scale(row) for row in bands]
    rows = [row / scale for row, scale in zip(bands, scales, strict=True)]
    ts = [component_scale(row) for row in cal.values]
    transfers = [row / scale for row, scale in zip(cal.values, ts, strict=True)]
    gains, statuses, coherence, relative, logx, logy, augmented, norms = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for m in (1, 2):
        qs = overlap(shape3, cal.voxel_size_um, bounds, m)
        xx, yy = [], []
        for q in qs:
            t = shifted(q, shape3, cal.voxel_size_um, carrier, m)
            qt = tuple(Fraction(int(v)) for v in q)
            assert len(qt) == 3
            xx.append(interpolate(transfers[m], t) * finite_sum(rows[0], (qt[0], qt[1], qt[2])))
            idx = tuple(int(q[a]) + shape3[a] // 2 for a in range(3))
            yy.append(complex(transfers[0][idx]) * finite_sum(rows[m], t))
        x, y = np.asarray(xx, dtype=np.complex128), np.asarray(yy, dtype=np.complex128)
        nx, ny = stable_norm(x), stable_norm(y)
        norms.append((nx, ny))
        logx.append(math.log2(nx) + math.log2(scales[0]) + math.log2(ts[m]) if nx else None)
        logy.append(math.log2(ny) + math.log2(scales[m]) + math.log2(ts[0]) if ny else None)
        r = np.zeros(len(qs) + 1, dtype=np.complex128)
        if not len(qs) or not nx or not ny:
            status = (
                "no_overlap" if not len(qs) else "zero_predictor" if not nx else "zero_response"
            )
            gains.append(0j if status == "zero_response" else None)
            coherence.append(None)
            relative.append(None)
            r[-1] = 1
        else:
            u, v = x / nx, y / ny
            products = u.conj() * v
            h = complex(math.fsum(z.real for z in products), math.fsum(z.imag for z in products))
            assert logx[-1] is not None and logy[-1] is not None
            logratio = logy[-1] - logx[-1]
            integer = math.floor(logratio)
            fractional = 2.0 ** (logratio - integer)
            gains.append(
                complex(
                    math.ldexp(h.real * fractional, integer),
                    math.ldexp(h.imag * fractional, integer),
                )
            )
            coherence.append(abs(h))
            r[:-1] = v - h * u
            relative.append(stable_norm(r))
            status = "zero_correlation" if h == 0 else "fitted"
        statuses.append(status)
        augmented.extend(r.real)
        augmented.extend(r.imag)
    residual = np.asarray(augmented, dtype=np.float64)
    return Point(
        float(np.dot(residual, residual)),
        tuple(gains),
        tuple(statuses),
        tuple(coherence),
        tuple(relative),
        tuple(logx),
        tuple(logy),
        residual,
        tuple(s in ("fitted", "zero_correlation") for s in statuses),
        tuple(norms),
    )


def diagnostics(
    bands: ComplexArray,
    cal: Any,
    bounds: RealArray,
    carrier: tuple[float, float],
    step: RealArray,
    rtol: float,
) -> dict[str, Any]:
    center = evaluate(bands, cal, bounds, carrier)
    columns = []
    gradient = 0.0
    continuous = True
    count = 0
    for a in range(2):
        points = []
        for sign in (-1, 1):
            available = carrier[a] - bounds[0, a] if sign < 0 else bounds[1, a] - carrier[a]
            distance = min(float(step[a]), float(available))
            if distance <= 0:
                points.append((0.0, center))
                continue
            k = list(carrier)
            k[a] += sign * distance
            point = evaluate(bands, cal, bounds, (k[0], k[1]))
            points.append((distance, point))
            count += 1
            continuous &= point.informative == center.informative
            gradient = max(gradient, (center.objective - point.objective) / distance)
        (dm, minus), (dp, plus) = points
        columns.append(
            (plus.residual - minus.residual) / (dm + dp)
            if dm + dp
            else np.zeros_like(center.residual)
        )
    jacobian = np.column_stack(columns)
    singular = np.linalg.svd(jacobian, compute_uv=False)
    rank = int(np.count_nonzero(singular > rtol * singular[0])) if singular[0] else 0
    return {
        "gradient": gradient,
        "singular": singular,
        "rank": rank,
        "continuous": continuous,
        "directions": count,
    }


def calibration(
    values: ComplexArray,
    spacing: tuple[float, float, float] = (0.75, 0.5, 1.25),
    origin: tuple[int, int, int] = (0, 0, 0),
) -> Any:
    import simrecon

    frequencies = [
        np.asarray(
            [float(Fraction(k) / (length * rational(d))) for k in bins(length)], dtype=np.float64
        )
        for length, d in zip(values.shape[1:], spacing, strict=True)
    ]
    return simrecon.VolumeOrderOtf(
        values,
        frequencies[0],
        frequencies[1],
        frequencies[2],
        spacing,
        origin,
        "RA09 independent opaque calibration",
    )


def arbitrary_case(shape: tuple[int, int, int] = (3, 4, 5)) -> tuple[ComplexArray, Any]:
    z, y, x = np.indices(shape)
    dc = 1 + 0.19 * z - 0.13 * y + 0.07 * x + 0.11 * ((x + y) % 2)
    bands = np.asarray(
        [
            dc,
            (0.4 + 0.07 * z + 0.11 * x) + 1j * (0.2 * y - 0.13 * x),
            (-0.3 + 0.17 * y - 0.09 * z) + 1j * (0.15 + 0.12 * x * y),
        ],
        dtype=np.complex128,
    )
    values = np.asarray(
        [
            (0.7 + 0.03 * z + 0.02 * x) + 1j * (0.11 * y - 0.05 * x),
            (0.5 + 0.07 * y + 0.02 * x * x) + 1j * (0.23 + 0.03 * z - 0.04 * x),
            (-0.4 + 0.06 * x - 0.02 * z) + 1j * (0.6 + 0.02 * x * y),
        ],
        dtype=np.complex128,
    )
    return bands, calibration(values)


def replace_calibration(cal: Any, **changes: Any) -> Any:
    """Construct a changed public record without assuming its implementation."""
    import simrecon

    fields = {
        name: getattr(cal, name)
        for name in (
            "values",
            "fz_per_um",
            "fy_per_um",
            "fx_per_um",
            "voxel_size_um",
            "origin_zyx",
            "source",
        )
    }
    fields.update(changes)
    return simrecon.VolumeOrderOtf(**fields)


@dataclass(frozen=True)
class RecoveryControl:
    """Hold fixed acquisition metadata, independent truth and held-out inputs."""

    bands: ComplexArray
    calibration: Any
    starts: RealArray
    bounds: RealArray
    step: RealArray
    truth: tuple[float, float]
    gains: tuple[complex, complex]
    specimen: RealArray
    heldout_specimen: RealArray


def recovery_control(noise: bool = False) -> RecoveryControl:
    """Declare a smooth basin with starts from nominal acquisition metadata."""
    shape = (3, 5, 5)
    z, y, x = np.indices(shape)
    specimen = (1.3 + 0.2 * np.cos(0.7 * z + 0.9 * y) + 0.3 * np.sin(0.4 * x + 0.3 * y)).astype(
        np.float64
    )
    heldout = (0.9 + 0.17 * z + 0.08 * y + 0.03 * x * x).astype(np.float64)
    spacing = (0.75, 0.5, 1.25)
    # Acquisition nominal bins (0.25,-0.25); declared search half-width .2 bins.
    starts = np.array([[0.25 / 2.5, -0.25 / 6.25]])
    bounds = np.array([[0.05 / 2.5, -0.45 / 6.25], [0.45 / 2.5, -0.05 / 6.25]])
    truth = (0.29 / 2.5, -0.21 / 6.25)
    gains = (0.65 + 0.3j, -0.4 + 0.55j)
    transfers = (0.8 + 0.1j, -0.6 + 0.25j)
    bands = np.empty((3, *shape), dtype=np.complex128)
    bands[0] = specimen
    for m in (1, 2):
        ramp = np.exp(2j * np.pi * m * (truth[0] * spacing[1] * y + truth[1] * spacing[2] * x))
        bands[m] = gains[m - 1] * transfers[m - 1] * specimen * ramp
        if noise:
            bands[m] += 0.002 * (np.sin(1.7 * x + 0.3 * z) + 1j * np.cos(0.9 * y - 0.2 * x))
    values = np.ones_like(bands)
    values[1], values[2] = transfers
    return RecoveryControl(
        bands,
        calibration(values, spacing),
        starts,
        bounds,
        np.array([1 / 1024, 1 / 1024]),
        truth,
        gains,
        specimen,
        heldout,
    )


def field_prediction(
    control: RecoveryControl,
    carrier: tuple[float, float],
    gains: tuple[complex, complex],
    heldout: bool = False,
) -> ComplexArray:
    specimen = control.heldout_specimen if heldout else control.specimen
    _, y, x = np.indices(specimen.shape)
    return np.asarray(
        [
            gains[m - 1]
            * control.calibration.values[m, 0, 0, 0]
            * specimen
            * np.exp(
                2j
                * np.pi
                * m
                * (
                    carrier[0] * control.calibration.voxel_size_um[1] * y
                    + carrier[1] * control.calibration.voxel_size_um[2] * x
                )
            )
            for m in (1, 2)
        ],
        dtype=np.complex128,
    )


def nonconstant_transfer_control() -> tuple[ComplexArray, Any, RealArray, tuple[float, float]]:
    """Generate a finite circular response that need not satisfy shifted fitting."""
    control = recovery_control()
    bands = control.bands.copy()
    values = control.calibration.values.copy()
    _, y, x = np.indices(control.specimen.shape)
    shape = control.specimen.shape
    qs = list(itertools.product(*(bins(k) for k in shape)))
    for m in (1, 2):
        modulation = np.exp(
            2j
            * np.pi
            * m
            * (
                control.truth[0] * control.calibration.voxel_size_um[1] * y
                + control.truth[1] * control.calibration.voxel_size_um[2] * x
            )
        )
        varying = values[m] * (0.65 + 0.09 * y + 0.04 * x * x)
        values[m] = varying
        modulated = np.asarray(control.specimen * modulation, dtype=np.complex128)
        coefficients = [
            finite_sum(modulated, (Fraction(q[0]), Fraction(q[1]), Fraction(q[2])))
            * varying[tuple(q[a] + shape[a] // 2 for a in range(3))]
            for q in qs
        ]
        for n in np.ndindex(shape):
            terms = [
                coefficient * np.exp(2j * np.pi * sum(q[a] * n[a] / shape[a] for a in range(3)))
                for q, coefficient in zip(qs, coefficients, strict=True)
            ]
            bands[m][n] = control.gains[m - 1] * complex(
                math.fsum(z.real for z in terms), math.fsum(z.imag for z in terms)
            )
    cal = replace_calibration(control.calibration, values=values)
    return bands, cal, np.array([control.truth, control.truth]), control.truth
