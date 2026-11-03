"""Independent small finite sums for the accepted CE05 public contract.

No production numerical helper is an oracle. The only production calls below
construct public CE02/CE03 inputs or invoke the public estimator under test.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

import simrecon

PUBLIC: Any = simrecon

RTOL = 3e-11
ATOL = 3e-12
OPTICS: dict[str, Any] = dict(wavelength_nm=500, numerical_aperture=1.0, immersion_index=1.0)
SOURCES = (
    ("sirecon.c", "3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567"),
    ("small_math_funcs.c", "a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e"),
    ("helpers.c", "b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206"),
    ("sirecon.h", "f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629"),
    ("Makefile", "1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4"),
    (
        "usr_local/include/fftw3.h",
        "8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d",
    ),
)


def bands_record(
    *,
    times: int = 1,
    directions: int = 1,
    orders: int = 3,
    shape: tuple[int, int, int] = (3, 3, 4),
    dxy: float = 1.0,
    dz: float = 1.0,
    zoom: tuple[int, int] = (1, 1),
    raw: Any = None,
) -> Any:
    """Construct actual CE02 records; writable quadratures are caller data."""
    phases = 2 * orders - 1
    if raw is None:
        raw = np.ones((times, directions, phases, *shape), dtype=np.float64)
    return simrecon.prepare_bands(
        raw,
        dxy_um=dxy,
        dz_um=dz,
        norders=orders,
        background=0,
        lateral_zoom=zoom[0],
        axial_zoom=zoom[1],
        edge_pixels=0,
        equalize=False,
    )


def transfer_record(
    orders: int = 3,
    *,
    layout: str = "radial",
    samples: Any = None,
    dkr: float = 0.25,
    dkz: float = 1.0,
) -> Any:
    """Declare complete, exactly complex64-representable independent tables."""
    if samples is None:
        shape = (orders, 12, 8) if layout == "radial" else (orders, 8, 12, 12)
        samples = np.empty(shape, dtype=np.complex128)
        for idx in np.ndindex(shape):
            order, *coords = idx
            samples[idx] = (8 + order + sum(coords)) / 16 + 1j * (
                1 + 2 * order + sum((i + 1) * v for i, v in enumerate(coords))
            ) / 32
    return simrecon.declare_otf(samples, layout=layout, dkr_cyc_um=dkr, dkz_cyc_um=dkz)


def controlled_bands(**kwargs: Any) -> Any:
    """Use deterministic unequal complex quadratures, including endpoints."""
    bands = bands_record(**kwargs)
    for idx in np.ndindex(bands.quadratures.shape):
        t, d, q, z, y, x = idx
        bands.quadratures[idx] = (3 + 2 * t + d + 3 * z - y + x) / (8 * (q + 1)) + 1j * (
            2 + t - d + z + 2 * y - 3 * x
        ) / (16 * (q + 1))
    return bands


def estimate(bands: Any, transfer: Any, initial: Any, **settings: Any) -> Any:
    """Call only the declared public boundary, preserving absence as absence."""
    options = OPTICS | settings
    return PUBLIC.estimate_parameters(
        bands,
        transfer,
        initial_carriers_cyc_um=initial,
        **options,
    )


def rejection(bands: Any, transfer: Any, initial: Any, match: str, **settings: Any) -> None:
    """Require the public subtype and informative field/operation text."""
    cls = PUBLIC.ParameterEstimationError
    assert issubclass(cls, simrecon.SimreconError)
    observed = bands.quadratures if hasattr(bands, "quadratures") else None
    if observed is not None and all(stride == 0 for stride in observed.strides):
        # Oversized representation probes alias one scalar. Observe that exact
        # underlying storage without allocating or traversing their logical shape.
        observed = observed[(slice(0, 1),) * observed.ndim]
    before = observed.copy() if observed is not None else None
    with pytest.raises(cls, match=match):
        estimate(bands, transfer, initial, **settings)
    if before is not None:
        assert_array_equal(observed, before)


def lift(index: int, size: int) -> int:
    """Label the even Nyquist positive."""
    return index if index <= size // 2 else index - size


def finite_transform(values: Any, sign: int) -> Any:
    """Direct full exponential sum, without any Fourier library transform."""
    shape = values.shape
    answer = np.empty(shape, dtype=np.complex128)
    addresses = tuple(np.ndindex(shape))
    for out in addresses:
        terms = [complex(values[src]) * root_phase(src, out, shape, sign) for src in addresses]
        answer[out] = complex(math.fsum(v.real for v in terms), math.fsum(v.imag for v in terms))
    return answer


def root_phase(src: Any, out: Any, shape: Any, sign: int) -> complex:
    """Evaluate exact quarter-turn roots algebraically; others by exponentials."""
    quarter_turns = sum(4 * a * b / n for a, b, n in zip(src, out, shape, strict=True))
    if quarter_turns.is_integer():
        return (1j) ** (sign * int(quarter_turns) % 4)
    return cmath.exp(sign * 0.5j * math.pi * quarter_turns)


def table_sample(transfer: Any, x: float, y: float, z: int, dzf: float, order: int) -> complex:
    """Independent scalar interpolation, with literal flat vertex safety."""
    tab = transfer.samples[order]
    flat = tab.ravel()
    axial = z * (dzf / transfer.dkz_cyc_um)
    if transfer.layout == "radial":
        radial = math.hypot(x, y) / transfer.dkr_cyc_um
        if axial < 0:
            axial += tab.shape[1]
        i, j = math.floor(radial), math.floor(axial)
        a, b = radial - i, axial - j
        j1 = 0 if j == tab.shape[1] - 1 else j + 1
        offsets = (
            i * tab.shape[1] + j,
            i * tab.shape[1] + j1,
            (i + 1) * tab.shape[1] + j,
            (i + 1) * tab.shape[1] + j1,
        )
        if min(offsets) < 0 or max(offsets) >= flat.size:
            raise ValueError("oracle unsafe stencil")
        p, q, r, s = (complex(flat[k]) for k in offsets)
        return (1 - a) * ((1 - b) * p + b * q) + a * ((1 - b) * r + b * s)
    u, v = x / transfer.dkr_cyc_um, y / transfer.dkr_cyc_um
    reflected = u < 0
    if reflected:
        u, v, axial = -u, -v, -axial
    nz, ny, nx = tab.shape
    if v < 0:
        v += ny
    if axial < 0:
        axial += nz
    ix, iy, iz = math.floor(u), math.floor(v), math.floor(axial)
    a, b, c = u - ix, v - iy, axial - iz
    result = 0j
    for zz, wz in ((iz, 1 - c), ((iz + 1) % nz, c)):
        for yy, wy in ((iy, 1 - b), ((iy + 1) % ny, b)):
            for xx, wx in ((ix, 1 - a), (ix + 1, a)):
                offset = zz * ny * nx + yy * nx + xx
                if not 0 <= offset < flat.size:
                    raise ValueError("oracle unsafe stencil")
                result += complex(flat[offset]) * wx * wy * wz
    return result.conjugate() if reflected else result


def cutoffs(bands: Any, optics: dict[str, Any]) -> tuple[float, int]:
    """Independent optical cutoff, including strict-greater CE05 clipping."""
    z = bands.input_shape[3]
    wavelength = optics["wavelength_nm"] / 1000
    theta = math.asin(optics["numerical_aperture"] / optics["immersion_index"])
    radius = min(2 * optics["numerical_aperture"] / wavelength, 1 / (2 * bands.dxy_um))
    cutoff = math.ceil(
        (1 - math.cos(theta)) / (wavelength / optics["immersion_index"]) * z * bands.dz_um
    )
    if cutoff > z // 2:
        cutoff = max(z // 2 - 1, 0)
    return radius, cutoff


@dataclass
class Build:
    """Independent expected overlap capture."""

    index: int
    time_index: int
    direction_index: int
    purpose: str
    orders: tuple[int, int]
    carrier_cyc_um: Any
    fourier: Any
    spatial: Any
    written: Any


@dataclass
class Event:
    """Ordered public trace expectation."""

    kind: str
    time_index: int
    direction_index: int
    details: tuple[tuple[str, Any], ...]


@dataclass
class Expected:
    """Independent result and propagated coordinate roundoff allowance."""

    carriers_cyc_um: Any
    raw_modulation: Any
    modulation: Any
    branches: tuple[tuple[str, ...], ...]
    overlaps: list[Build] = field(default_factory=list)
    trace: list[Event] = field(default_factory=list)
    coordinate_budget: float = 0.0


def overlap(
    bands: Any,
    transfer: Any,
    carrier: Any,
    order: int,
    *,
    t: int = 0,
    d: int = 0,
    purpose: str = "known",
    index: int = 0,
    omit: bool = False,
    optics: dict[str, Any] | None = None,
) -> Build:
    """Enumerate independent masks, sample short circuits and sequential writes."""
    optics = OPTICS if optics is None else optics
    nz, ny, nx = bands.input_shape[3:]
    radius, cutoff = cutoffs(bands, optics)
    fourier = np.zeros((2, nz, ny, nx), dtype=np.complex128)
    written = np.zeros(fourier.shape, dtype=np.bool_)
    delta = order * np.asarray(carrier)
    for iy in range(ny):
        for ix in range(nx):
            x, y = lift(ix, nx) / (nx * bands.dxy_um), lift(iy, ny) / (ny * bands.dxy_um)
            if math.hypot(x, y) > radius:
                continue
            for side in (0, 1):
                shifted_x = x + (1 if side else -1) * delta[0]
                shifted_y = y + (1 if side else -1) * delta[1]
                if math.hypot(shifted_x, shifted_y) > radius:
                    continue
                for z in range(-cutoff, cutoff + 1):
                    if omit and z == 0:
                        continue
                    dzf = 1 / (nz * bands.dz_um)
                    first_order, second_order = (order, 0) if side else (0, order)
                    first = table_sample(transfer, x, y, z, dzf, first_order)
                    if (5 if side else 1) * abs(first) <= 0.006:
                        continue
                    second = table_sample(transfer, shifted_x, shifted_y, z, dzf, second_order)
                    if (1 if side else 5) * abs(second) <= 0.006:
                        continue
                    zz, yy, xx = z % nz, iy, ix
                    reflected = ix > nx // 2
                    if reflected:
                        zz, yy, xx = (-z) % nz, (-iy) % ny, nx - ix
                    slot = 2 * order - 1 if side else 0
                    even = complex(bands.quadratures[t, d, slot, zz, yy, xx])
                    odd = complex(bands.quadratures[t, d, slot + 1, zz, yy, xx]) if side else 0j
                    if reflected:
                        even, odd = even.conjugate(), odd.conjugate()
                    band = even + 1j * odd if side else even
                    fourier[side, z % nz, iy, ix] = (
                        band * second / math.hypot(abs(first), abs(second))
                    )
                    written[side, z % nz, iy, ix] = True
    spatial = np.stack([finite_transform(fourier[i], +1) for i in (0, 1)])
    return Build(index, t, d, purpose, (0, order), np.array(carrier), fourier, spatial, written)


def regression(build: Build, carrier: Any, dxy: float, objective: bool) -> dict[str, Any]:
    """Independent complex dot products, with no unused square on known fits."""
    _, nz, ny, nx = build.spatial.shape
    terms_x, terms_y, terms_c = [], [], []
    for z, y, x in np.ndindex((nz, ny, nx)):
        a = complex(build.spatial[0, z, y, x])
        b = complex(build.spatial[1, z, y, x]) * cmath.exp(
            2j
            * math.pi
            * build.orders[1]
            * dxy
            * ((x - nx // 2) * carrier[0] + (y - ny // 2) * carrier[1])
        )
        terms_x.append(abs(a) ** 2)
        terms_y.append(abs(b) ** 2)
        terms_c.append(a.conjugate() * b)
    sx, sy = math.fsum(terms_x), math.fsum(terms_y)
    cross = complex(math.fsum(v.real for v in terms_c), math.fsum(v.imag for v in terms_c))
    if sx <= 0 or sy <= 0 or sx == sy:
        raise ValueError("oracle undefined energy regression")
    forward, reverse = cross / sx, cross.conjugate() / sy
    beta = 0.5 * math.atan(2 * abs(cross) / (sx - sy))
    if beta < 0:
        beta += math.pi / 2
    combined = math.tan(beta) * cmath.exp(1j * cmath.phase(cross)) if cross else 0j
    return dict(
        SX=sx,
        SY=sy,
        cross=cross,
        forward=forward,
        reverse=reverse,
        combined=combined,
        correlation=math.sqrt(abs(cross) ** 2 / (sx * sy)),
        objective=abs(forward) ** 2 if objective else None,
    )


def parabola(points: tuple[float, ...]) -> tuple[float, str, float]:
    """Divided differences plus conservative input-error propagation."""
    x1, y1, x2, y2, x3, y3 = points
    if len({x1, x2, x3}) < 3:
        return 0.0, "duplicate-coordinate", 0.0
    b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
    s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
    curvature = (s2 - s1) / (b2 - b1)
    if curvature == 0:
        return 0.0, "zero-curvature", 0.0
    ey = RTOL * max(abs(y1), abs(y2), abs(y3)) + ATOL
    es1, es2 = 2 * ey / abs(x2 - x1), 2 * ey / abs(x3 - x2)
    ec = (es1 + es2) / abs(b2 - b1)
    bound = 16 * (es2 / abs(curvature) + abs(s2) * ec / curvature**2)
    return b2 - s2 / curvature, "fitted", bound


def probe_value(
    evaluate: Any,
    build: Build,
    stage: str,
    coordinate: float,
    initial_magnitude: float,
    fixed_angle: float,
    remake: bool = False,
) -> float:
    """Evaluate a literal candidate with explicit, noncaptured stage inputs."""
    angle, magnitude = (
        (coordinate, initial_magnitude) if stage == "angle" else (fixed_angle, coordinate)
    )
    vector = np.array([magnitude * math.cos(angle), magnitude * math.sin(angle)])
    return evaluate(build, stage, vector, float(angle), float(magnitude), remake)


def bracket_event(
    publish: Any, stage: str, branch: str, improvement: bool, points: tuple[float, ...]
) -> None:
    """Capture the complete bracket state after a specified mutation."""
    x1, y1, x2, y2, x3, y3 = points
    publish(
        "bracket",
        stage=stage,
        branch=branch,
        x1=x1,
        amp1=y1,
        x2=x2,
        amp2=y2,
        x3=x3,
        amp3=y3,
        strict_improvement=improvement,
    )


def expected_estimate(bands: Any, transfer: Any, initial: Any, **options: Any) -> Expected:
    """Full independent finite search/known path through contract equations."""
    settings: dict[str, Any] = (
        dict(
            search_carriers=True,
            use_time0_carriers=True,
            amplitude_floors=None,
            fit_all_phases=True,
            omit_kz0=False,
        )
        | options
    )
    optics = OPTICS | {k: settings[k] for k in OPTICS if k in settings}
    nt, nd, _, nz, ny, nx = bands.input_shape
    orders = bands.noise_variance_factors.shape[1]
    raw = np.empty((nt, nd, orders - 1), dtype=np.complex128)
    carriers = np.empty((nt, nd, 2), dtype=np.float64)
    answer = Expected(carriers, raw, np.empty_like(raw), ())
    branches: list[tuple[str, ...]] = []
    for t in range(nt):
        row: list[str] = []
        for d in range(nd):

            def event(kind: str, *, t: int = t, d: int = d, **details: Any) -> None:
                answer.trace.append(Event(kind, t, d, tuple(details.items())))

            def build_at(k: Any, b: int, purpose: str, *, t: int = t, d: int = d) -> Build:
                result = overlap(
                    bands,
                    transfer,
                    k,
                    b,
                    t=t,
                    d=d,
                    purpose=purpose,
                    index=len(answer.overlaps),
                    omit=settings["omit_kz0"],
                    optics=optics,
                )
                answer.overlaps.append(result)
                return result

            def evaluate(
                build: Build,
                stage: str,
                k: Any,
                angle: Any,
                mag: Any,
                remake: bool,
                *,
                t: int = t,
                d: int = d,
                publish: Any = event,
            ) -> float:
                values = regression(build, k, bands.dxy_um, stage != "known")
                publish(
                    "evaluation",
                    stage=stage,
                    orders=build.orders,
                    overlap_index=build.index,
                    remake_overlaps=remake,
                    angle_rad=angle,
                    magnitude_cyc_um=mag,
                    carrier_cyc_um=np.array(k),
                    **values,
                )
                raw[t, d, build.orders[1] - 1] = values["forward"]
                return values["objective"] if stage != "known" else 0.0

            if not settings["search_carriers"] or (t and settings["use_time0_carriers"]):
                reused = settings["search_carriers"] and t > 0
                k = carriers[0, d].copy() if reused else np.array(initial[d], dtype=float)
                row.append("time0-reused" if reused else "known")
                if reused:
                    event("reuse", source_time=0, carrier_cyc_um=k.copy())
                for b in range(1, orders):
                    evaluate(build_at(k, b, "known"), "known", k, None, None, True)
            else:
                row.append("searched")
                coarse = build_at(initial[d], 2, "coarse")
                v = np.sum(coarse.spatial[0] * coarse.spatial[1].conj(), axis=0)
                corr = finite_transform(v, -1)
                power = np.abs(corr) ** 2
                iy, ix = np.unravel_index(int(np.argmax(power)), power.shape)
                xn = np.array([power[iy, (ix + q) % nx] for q in (-1, 0, 1)])
                yn = np.array([power[(iy + q) % ny, ix] for q in (-1, 0, 1)])

                def offset(neighbors: Any) -> tuple[float, str]:
                    minus, center, plus = map(float, neighbors)
                    curvature = plus + minus - 2 * center
                    if curvature == 0:
                        return 0.0, "zero-curvature"
                    value = -(plus - minus) / (2 * curvature)
                    return (0.0, "outside-range") if abs(value) > 1.5 else (value, "fitted")

                xo, xs = offset(xn)
                yo, ys = offset(yn)
                peak = np.array([float(ix) + xo, float(iy) + yo])
                before = peak.copy()
                decisions: list[bool] = []
                for axis, sign in ((0, -1), (0, 1), (1, -1), (1, 1)):
                    size = (nx, ny)[axis]
                    step = 1 / (size * bands.dxy_um)
                    decision = (
                        bool(initial[d, axis] * step < peak[axis] - size // 2)
                        if sign < 0
                        else bool(initial[d, axis] * step > peak[axis] + size // 2)
                    )
                    decisions.append(decision)
                    if decision:
                        peak[axis] += sign * size
                k = peak / np.array([nx, ny]) / bands.dxy_um / 2
                event(
                    "coarse",
                    overlap_index=coarse.index,
                    correlation_complex=corr,
                    correlation_power=power,
                    integer_peak_xy=(int(ix), int(iy)),
                    x_neighbors=xn,
                    y_neighbors=yn,
                    x_offset=xo,
                    y_offset=yo,
                    x_offset_status=xs,
                    y_offset_status=ys,
                    peak_before_alias_xy=before,
                    alias_decisions=tuple(decisions),
                    peak_after_alias_xy=peak.copy(),
                    carrier_cyc_um=k.copy(),
                )
                if not np.any(k):
                    raise ValueError("oracle zero coarse polar conversion")
                mag0, angle0 = math.hypot(*k), math.atan2(k[1], k[0])
                frozen = build_at(k, 2, "refinement")
                x1: float = 0.0
                amp1: float = 0.0
                angle: float = angle0
                magnitude: float = mag0
                for stage, start, step in (
                    ("angle", angle0, 0.001),
                    ("magnitude", mag0, 0.1 / (max(nx, ny) * bands.dxy_um)),
                ):
                    x2, x3 = float(start), float(start + step)
                    amp2: float = probe_value(
                        evaluate, frozen, stage, x2, mag0, angle, stage == "angle"
                    )
                    amp3: float = probe_value(evaluate, frozen, stage, x3, mag0, angle)

                    bracket_event(
                        event, stage, "initial", bool(amp3 > amp2), (x1, amp1, x2, amp2, x3, amp3)
                    )
                    if amp3 > amp2:
                        candidate, increment = x3, step
                        bracket_event(
                            event, stage, "positive", True, (x1, amp1, x2, amp2, x3, amp3)
                        )
                    else:
                        candidate, increment = float(start), -step
                        amp2, amp3, x2, x3 = amp3, amp2, x3, x2
                        bracket_event(
                            event,
                            stage,
                            "negative-swap",
                            bool(amp3 > amp2),
                            (x1, amp1, x2, amp2, x3, amp3),
                        )
                    while amp3 > amp2:
                        amp1, x1, amp2, x2 = amp2, x2, amp3, x3
                        candidate += increment
                        x3, amp3 = (
                            candidate,
                            probe_value(evaluate, frozen, stage, candidate, mag0, angle),
                        )
                        bracket_event(
                            event, stage, "shift", bool(amp3 > amp2), (x1, amp1, x2, amp2, x3, amp3)
                        )
                    bracket_event(event, stage, "stop", False, (x1, amp1, x2, amp2, x3, amp3))
                    points = (x1, amp1, x2, amp2, x3, amp3)
                    result, status, budget = parabola(points)
                    answer.coordinate_budget += budget
                    event(
                        "parabola",
                        stage=stage,
                        x1=x1,
                        y1=amp1,
                        x2=x2,
                        y2=amp2,
                        x3=x3,
                        y3=amp3,
                        result=result,
                        status=status,
                    )
                    if stage == "angle":
                        angle = result
                    else:
                        magnitude = result
                k = np.array([magnitude * math.cos(angle), magnitude * math.sin(angle)])
                evaluate(frozen, "final", k, angle, magnitude, False)
                for b in range(1, orders):
                    if b != 2:
                        evaluate(
                            build_at(k, b, "later-order"), "later-order", k, angle, magnitude, True
                        )
            carriers[t, d] = k
            floors = settings["amplitude_floors"]
            after = raw[t, d].copy()
            applied: list[bool] = []
            for b in range(1, orders):
                use_floor = floors is not None and abs(after[b - 1]) < floors[b - 1]
                applied.append(bool(use_floor))
                if use_floor:
                    assert floors is not None
                    if after[b - 1] == 0:
                        raise ValueError("oracle zero floor division")
                    after[b - 1] *= floors[b - 1] / abs(after[b - 1])
            if not settings["fit_all_phases"] and after[0] == 0:
                raise ValueError("oracle zero selected base phase")
            phi = cmath.phase(after[0])
            for b in range(1, orders):
                replace_phase = not settings["fit_all_phases"] and b >= 2
                final = (
                    abs(after[b - 1]) * cmath.exp(1j * b * phi) if replace_phase else after[b - 1]
                )
                answer.modulation[t, d, b - 1] = final
                event(
                    "adjustment",
                    order=b,
                    raw_forward=complex(raw[t, d, b - 1]),
                    floor=None if floors is None else float(floors[b - 1]),
                    floor_applied=applied[b - 1],
                    after_floor=complex(after[b - 1]),
                    phase_replaced=replace_phase,
                    final=complex(final),
                )
        branches.append(tuple(row))
    answer.branches = tuple(branches)
    return answer


def events(result: Any, kind: str) -> list[dict[str, Any]]:
    """Read public diagnostic records without inspecting production internals."""
    return [dict(e.details) for e in result.trace if e.kind == kind]


def close(actual: Any, expected: Any, *, atol: float = ATOL) -> None:
    """Use a preregistered scale-aware binary64 comparison."""
    assert_allclose(actual, expected, rtol=RTOL, atol=atol)


def assert_expected(actual: Any, expected: Expected) -> None:
    """Compare ordered decisions, all captured arrays and every numeric trace field."""
    budget = expected.coordinate_budget
    # Phase sensitivity <= 2*pi*m*dxy*(X+Y) times coordinate uncertainty.
    sensitivity = 1 + max(
        (b.orders[1] * sum(b.fourier.shape[2:]) for b in expected.overlaps), default=0
    )
    allowance = ATOL + 16 * math.pi * sensitivity * budget
    close(actual.carriers_cyc_um, expected.carriers_cyc_um, atol=ATOL + 4 * budget)
    close(actual.raw_modulation, expected.raw_modulation, atol=allowance)
    close(actual.modulation, expected.modulation, atol=allowance)
    assert actual.branches == expected.branches
    assert len(actual.overlaps) == len(expected.overlaps)
    for a, e in zip(actual.overlaps, expected.overlaps, strict=True):
        for name in ("index", "time_index", "direction_index", "purpose", "orders"):
            assert getattr(a, name) == getattr(e, name)
        close(a.carrier_cyc_um, e.carrier_cyc_um, atol=ATOL + 4 * budget)
        for name in ("fourier", "spatial"):
            close(
                getattr(a, name),
                getattr(e, name),
                atol=allowance if e.purpose == "later-order" or e.time_index > 0 else ATOL,
            )
        assert_array_equal(a.written, e.written)
    assert len(actual.trace) == len(expected.trace)
    stage_budget = 0.0
    active_location = (-1, -1)
    for a, e in zip(actual.trace, expected.trace, strict=True):
        if active_location != (e.time_index, e.direction_index):
            active_location = (e.time_index, e.direction_index)
            stage_budget = budget if e.time_index > 0 else 0.0
        trace_allowance = ATOL + 16 * math.pi * sensitivity * stage_budget
        own_budget = 0.0
        if e.kind == "parabola":
            d = dict(e.details)
            _, _, own_budget = parabola(tuple(d[k] for k in ("x1", "y1", "x2", "y2", "x3", "y3")))
            trace_allowance += own_budget
        assert (a.kind, a.time_index, a.direction_index) == (
            e.kind,
            e.time_index,
            e.direction_index,
        )
        assert tuple(k for k, _ in a.details) == tuple(k for k, _ in e.details)
        for (name, value), (_, wanted) in zip(a.details, e.details, strict=True):
            if wanted is None or isinstance(wanted, (str, bool, int, tuple)):
                if wanted is not None:
                    assert type(value) is type(wanted)
                assert value == wanted, (a.kind, name)
            elif isinstance(wanted, np.ndarray):
                scale = max(1.0, float(np.max(np.abs(wanted))))
                assert value.dtype == wanted.dtype and value.shape == wanted.shape
                assert value.flags.owndata and not value.flags.writeable
                close(value, wanted, atol=trace_allowance * scale)
            else:
                assert type(value) is (complex if np.iscomplexobj(wanted) else float)
                assert np.isfinite(value)
                close(value, wanted, atol=trace_allowance * max(1.0, abs(wanted)))
        if e.kind == "parabola":
            stage_budget += own_budget


def dc_bands(
    *, gain: complex = 0.25 + 0.125j, orders: int = 2, times: int = 1, directions: int = 1
) -> Any:
    """Algebraic DC overlaps with exact scale-independent unequal energies."""
    bands = bands_record(times=times, directions=directions, orders=orders, shape=(2, 1, 2))
    bands.quadratures.fill(0)
    bands.quadratures[:, :, 0, 0, 0, 0] = 1
    for t in range(times):
        for d in range(directions):
            for b in range(1, orders):
                bands.quadratures[t, d, 2 * b - 1, 0, 0, 0] = gain * (b + t + d)
    return bands


def unit_transfer(orders: int = 2) -> Any:
    """Two radial samples and one axial sample suffice for the small DC domain."""
    return transfer_record(orders, samples=np.ones((orders, 2, 1)), dkr=1, dkz=1)


def search_bands(seed: int = 0, *, times: int = 1, orders: int = 3) -> Any:
    """Seed-fixed dyadic caller quadratures chosen using only finite oracle paths."""
    bands = bands_record(times=times, orders=orders, shape=(3, 3, 4))
    rng = np.random.default_rng(seed)
    bands.quadratures[:] = (
        rng.integers(-8, 9, bands.quadratures.shape)
        + 1j * rng.integers(-8, 9, bands.quadratures.shape)
    ) / 16
    bands.quadratures[:, :, 0] *= 3
    return bands


def tie_bands() -> Any:
    """Make a coarse peak, then disjoint spatial supports at refinement."""
    bands = bands_record(shape=(2, 1, 4))
    bands.quadratures.fill(0)
    bands.quadratures[0, 0, 0, 0, 0, :] = 1
    bands.quadratures[0, 0, 1, 0, 0, 0] = 0.25
    bands.quadratures[0, 0, 3, 0, 0, 1] = -0.5j
    return bands


def known_image_sum(
    bands: Any, transfer: Any, carriers: Any, modulation: Any, *, wiener: float = 0.5
) -> Any:
    """Independent CE04 no-taper/no-suppression finite filter and assembly.

    This consumes independently predicted CE05 parameters. No reconstruction
    product helper or forward image generator participates in the expectation.
    """
    nt, nd, _, nz, ny, nx = bands.input_shape
    orders = bands.noise_variance_factors.shape[1]
    radius = min(4.0, 1 / (2 * bands.dxy_um))
    le = 0.5
    c0 = math.ceil((1 - math.cos(math.asin(1.0))) / le * nz * bands.dz_um)
    cuts = [c0] + [math.trunc((1 + 1 / 0.88) * c0)] * (orders - 2) + [math.trunc(1.3 * c0)]
    cuts = [max(nz // 2 - 1, 0) if c >= nz // 2 else c for c in cuts]
    filtered = bands.quadratures.copy()
    for t in range(nt):
        for d in range(nd):
            for m in range(orders):
                full = np.zeros((nz, ny, nx), dtype=np.complex128)
                for y in range(-(ny // 2 - 1), ny // 2 + 1) if ny >= 2 else ():
                    for x in range(-(nx // 2 - 1), nx // 2 + 1):
                        if m == 0 and x < 0:
                            continue
                        reflected = x < 0
                        yy, xx = ((-y) % ny, -x) if reflected else (y % ny, x)
                        slot = 0 if m == 0 else 2 * m - 1
                        slots = [slot] if m == 0 else [slot, slot + 1]
                        kx, ky = x / (nx * bands.dxy_um), y / (ny * bands.dxy_um)
                        for z in range(-cuts[m], cuts[m] + 1):
                            if math.hypot(kx, ky) > radius:
                                for s in slots:
                                    filtered[t, d, s, z % nz, yy, xx] = 0
                                continue
                            dzf = 1 / (nz * bands.dz_um)
                            h1 = table_sample(transfer, kx, ky, z, dzf, m)
                            a = 1 if m == 0 else modulation[d, m - 1]
                            weight = 1 / bands.noise_variance_factors[d, m]
                            denominator = abs(h1) ** 2 * abs(a) ** 2 * weight
                            for e in range(nd):
                                for signed in range(-(orders - 1), orders):
                                    if (e, signed) == (d, m):
                                        continue
                                    qx = kx + m * carriers[d, 0] - signed * carriers[e, 0]
                                    qy = ky + m * carriers[d, 1] - signed * carriers[e, 1]
                                    if math.hypot(qx, qy) < radius:
                                        h2 = table_sample(transfer, qx, qy, z, dzf, abs(signed))
                                        aa = 1 if signed == 0 else modulation[e, abs(signed) - 1]
                                        denominator += (
                                            abs(h2) ** 2
                                            * abs(aa) ** 2
                                            / bands.noise_variance_factors[e, abs(signed)]
                                        )
                            scale = (
                                weight
                                * h1.conjugate()
                                * complex(a).conjugate()
                                / (denominator + wiener**2)
                            )
                            zz = (-z) % nz if reflected else z % nz
                            even = complex(filtered[t, d, slot, zz, yy, xx])
                            odd = complex(filtered[t, d, slot + 1, zz, yy, xx]) if m else 0j
                            if reflected:
                                even, odd = even.conjugate(), odd.conjugate()
                            if m:
                                full[z % nz, y % ny, x % nx] = (even + 1j * odd) * scale
                            else:
                                filtered[t, d, 0, zz, yy, xx] = even * scale
                        for z in range(cuts[m] + 1, nz - cuts[m]):
                            for s in slots:
                                filtered[t, d, s, z, yy, xx] = 0
                if m:
                    for y in range(-(ny // 2 - 1), ny // 2 + 1) if ny >= 2 else ():
                        for x in range(nx // 2 + 1):
                            for z in range(-cuts[m], cuts[m] + 1):
                                p = full[z % nz, y % ny, x]
                                n = full[(-z) % nz, (-y) % ny, (-x) % nx].conjugate()
                                filtered[t, d, 2 * m - 1, z % nz, y % ny, x] = (p + n) / 2
                                filtered[t, d, 2 * m, z % nz, y % ny, x] = (p - n) / (2j)
    az, ly = bands.axial_zoom, bands.lateral_zoom
    outshape = (az * nz, ly * ny, ly * nx)
    image = np.zeros((nt, *outshape), dtype=np.float64)
    for t in range(nt):
        for d in range(nd):
            for m in range(orders):
                coefficients = np.zeros(outshape, dtype=np.complex128)
                for z, y, x in np.ndindex((nz, ny, nx)):
                    qx, qy, qz = lift(x, nx), lift(y, ny), lift(z, nz)
                    zz, yy, xx = z, y, x
                    reflected = qx < 0
                    if reflected:
                        zz, yy, xx = (-z) % nz, (-y) % ny, -qx
                    slot = 0 if m == 0 else 2 * m - 1
                    e = complex(filtered[t, d, slot, zz, yy, xx])
                    o = complex(filtered[t, d, slot + 1, zz, yy, xx]) if m else 0j
                    if reflected:
                        e, o = e.conjugate(), o.conjugate()
                    coefficients[qz % outshape[0], qy % outshape[1], qx % outshape[2]] = (
                        e + 1j * o if m else e
                    )
                spatial = finite_transform(coefficients, +1)
                for z, y, x in np.ndindex(outshape):
                    phase = (
                        2j
                        * math.pi
                        * m
                        * (
                            carriers[d, 0] * (x - outshape[2] // 2) * bands.dxy_um / ly
                            + carriers[d, 1] * (y - outshape[1] // 2) * bands.dxy_um / ly
                        )
                    )
                    image[t, z, y, x] += (2 if m else 1) * (
                        spatial[z, y, x] * cmath.exp(phase)
                    ).real
    return image
