"""Public RB117 inputs, finite 2D oracle and exact retention observers.

Only public constructors/entries are called. No implementation state is read.
The independent observer bounds are declared before any product execution.
"""

from __future__ import annotations

import cmath
import dataclasses
import hashlib
import math
import struct
from types import SimpleNamespace
from typing import Any

import numpy as np

from c_estimation_fixture import (
    ATOL,
    OPTICS,
    RTOL,
    Build,
    Event,
    Expected,
    bracket_event,
    finite_transform,
    known_image_sum,
    lift,
    parabola,
    table_sample,
    transfer_record,
)


def workflow_case(
    mode: str,
    orders: int,
    *,
    times: int = 1,
    directions: int = 1,
    layout: str = "radial",
    reuse: bool = True,
    search: bool = True,
    dz: float = 1.0,
    adjustments: bool = False,
    low_bin: bool = False,
    odd_phase: bool = False,
) -> tuple[Any, dict[str, Any]]:
    """Freeze dyadic count inputs without selecting from observed results."""
    shape = (times, directions, 2 * orders - 1, 1 if mode == "2d" else 3, 3, 8 if low_bin else 4)
    raw = np.random.default_rng(7).integers(1, 17, shape).astype(np.float64)
    if low_bin:
        phases = shape[2]
        spatial = np.array([2, 1, -1, -1, 0, -1, -1, 1], dtype=np.float64)
        for t in range(times):
            for p in range(phases):
                coefficient = phases * int(p == 0) - 1
                raw[t, :, p] = 64 + (t + 1) * (p + 1) / 8 + (1 + t / 4) * coefficient * spatial
                if odd_phase:
                    sine = np.array([0, 1, 1, 1, 0, -1, -1, -1], dtype=np.float64)
                    raw[t, :, p] += 0.5 * (int(p == 1) - int(p == 0)) * sine
    samples = None if mode == "3d" else _plane_samples(orders + 1, layout)
    if low_bin:
        table_shape = (
            (orders + 1, 12, 1 if mode == "2d" else 8)
            if layout == "radial"
            else (orders + 1, 1 if mode == "2d" else 8, 12, 12)
        )
        samples = np.ones(table_shape)
    transfer = transfer_record(
        orders + 1,
        layout=layout,
        samples=samples,
    )
    settings: dict[str, Any] = dict(
        acquisition=dict(
            acquisition_mode=mode,
            dxy_um=1.0,
            dz_um=dz,
            norders=orders,
            background=0.0,
            lateral_zoom=1.0,
            axial_zoom=1,
            phase_policy="uniform",
            edge_pixels=0,
            equalize=False,
        ),
        optics=OPTICS.copy(),
        carrier=dict(
            linespacing_um=10.0,
            angles_rad=np.linspace(-0.4, 0.2, directions),
            search_carriers=search,
            use_time0_carriers=reuse,
            amplitude_floors=np.full(orders - 1, 0.75) if adjustments else None,
            fit_all_phases=not adjustments,
        ),
        filtering=dict(wiener=0.5, suppress_singularities=False, output_taper="none"),
        specimen_identity=dict(id="rb117-specimen", intensity_unit="detector-counts"),
        transfer=transfer,
        transfer_identity=dict(
            id="rb117-transfer", intensity_unit="dimensionless-transfer", optics=OPTICS.copy()
        ),
    )
    return raw, settings


def _plane_samples(orders: int, layout: str) -> Any:
    shape = (orders, 12, 1) if layout == "radial" else (orders, 1, 12, 12)
    samples = np.empty(shape, dtype=np.complex128)
    for index in np.ndindex(shape):
        b, *coordinates = index
        samples[index] = (8 + b + sum(coordinates)) / 16 + 1j * (
            1 + 2 * b + sum((j + 1) * v for j, v in enumerate(coordinates))
        ) / 32
    return samples


def initial_vectors(raw: Any, settings: dict[str, Any]) -> Any:
    count = raw.shape[1]
    carrier = settings["carrier"]
    divisor = 1 if settings["acquisition"]["acquisition_mode"] == "2d" else raw.shape[2] // 2
    magnitude = 1 / (carrier["linespacing_um"] * divisor)
    return np.array(
        [[magnitude * math.cos(a), magnitude * math.sin(a)] for a in carrier["angles_rad"]]
    ).reshape(count, 2)


def finite_bands(raw: Any, settings: dict[str, Any]) -> Any:
    """CE02/06 uniform finite sums, including the untouched Nyquist slots."""
    nt, nd, phases, nz, ny, nx = raw.shape
    orders = settings["acquisition"]["norders"]
    slots = 2 * orders - 1
    alpha = 1 / (nx * ny * nz * nd)
    quadratures = np.empty((nt, nd, slots, nz, ny, nx // 2 + 1), dtype=np.complex128)
    for t in range(nt):
        for d in range(nd):
            frames = np.stack(
                [
                    np.stack([finite_transform(raw[t, d, p, z] * alpha, -1) for z in range(nz)])
                    for p in range(phases)
                ]
            )
            separated = np.empty((slots, nz, ny, nx // 2 + 1), dtype=np.complex128)
            for q in range(slots):
                weights = [
                    1.0
                    if q == 0
                    else (math.cos if q % 2 else math.sin)(
                        ((q + 1) // 2) * 2 * math.pi * p / phases
                    )
                    for p in range(phases)
                ]
                separated[q] = sum(
                    weights[p] * frames[p, :, :, : nx // 2 + 1] for p in range(phases)
                )
                separated[q, :, :, nx // 2] = frames[q, :, :, nx // 2]
                # The axial transform acts after separation; Z1 is the 2D identity.
                for y in range(ny):
                    for x in range(nx // 2 + 1):
                        quadratures[t, d, q, :, y, x] = finite_transform(separated[q, :, y, x], -1)
    return SimpleNamespace(
        input_shape=raw.shape,
        quadratures=quadratures,
        noise_variance_factors=np.ones((nd, orders)),
        input_scale=alpha,
        dxy_um=1.0,
        dz_um=settings["acquisition"]["dz_um"],
        lateral_zoom=1,
        axial_zoom=1,
    )


def plane_build(
    bands: Any,
    transfer: Any,
    k: Any,
    pair: tuple[int, int],
    t: int,
    d: int,
    purpose: str,
    index: int,
) -> Build:
    """Enumerate true2D general-pair masks, complex weights and reflected slots."""
    _, _, _, _, ny, nx = bands.input_shape
    a, b = pair
    fourier = np.zeros((2, 1, ny, nx), dtype=np.complex128)
    written = np.zeros(fourier.shape, dtype=np.bool_)
    delta = (b - a) * np.asarray(k)
    for y in range(ny):
        for x in range(nx):
            qx, qy = lift(x, nx) / nx, lift(y, ny) / ny
            if math.hypot(qx, qy) > 0.5:
                continue
            for side in (0, 1):
                sx, sy = qx + (1 if side else -1) * delta[0], qy + (1 if side else -1) * delta[1]
                if math.hypot(sx, sy) > 0.5:
                    continue
                own, other = (b, a) if side else (a, b)
                first = table_sample(transfer, qx, qy, 0, transfer.dkz_cyc_um, own)
                if abs(first) <= 0.006:
                    continue
                second = table_sample(transfer, sx, sy, 0, transfer.dkz_cyc_um, other)
                if abs(second) <= 0.006:
                    continue
                yy, xx = ((-y) % ny, nx - x) if x > nx // 2 else (y, x)
                slot = 0 if own == 0 else 2 * own - 1
                even = complex(bands.quadratures[t, d, slot, 0, yy, xx])
                odd = complex(bands.quadratures[t, d, slot + 1, 0, yy, xx]) if own else 0j
                if x > nx // 2:
                    even, odd = even.conjugate(), odd.conjugate()
                fourier[side, 0, y, x] = (
                    (even + 1j * odd) * second / math.hypot(abs(first), abs(second))
                )
                written[side, 0, y, x] = True
    spatial = np.stack([finite_transform(fourier[side], +1) for side in (0, 1)])
    return Build(index, t, d, purpose, pair, np.array(k), fourier, spatial, written)


def plane_regression(build: Build, k: Any, objective: bool) -> dict[str, Any]:
    _, _, ny, nx = build.spatial.shape
    lower, higher, cross = [], [], []
    for y in range(ny):
        for x in range(nx):
            u = complex(build.spatial[0, 0, y, x])
            v = complex(build.spatial[1, 0, y, x]) * cmath.exp(
                2j
                * math.pi
                * (build.orders[1] - build.orders[0])
                * ((x - nx // 2) * k[0] + (y - ny // 2) * k[1])
            )
            lower.append(abs(u) ** 2)
            higher.append(abs(v) ** 2)
            cross.append(u.conjugate() * v)
    sx, sy = math.fsum(lower), math.fsum(higher)
    c = complex(math.fsum(v.real for v in cross), math.fsum(v.imag for v in cross))
    assert sx > 0 and sy > 0 and sx != sy, "independent fixture is outside regression domain"
    beta = math.atan(2 * abs(c) / (sx - sy)) / 2
    if beta < 0:
        beta += math.pi / 2
    forward = c / sx
    return dict(
        SX=sx,
        SY=sy,
        cross=c,
        forward=forward,
        reverse=c.conjugate() / sy,
        combined=math.tan(beta) * cmath.exp(1j * cmath.phase(c)) if c else 0j,
        correlation=math.sqrt(abs(c) ** 2 / (sx * sy)),
        objective=abs(forward) ** 2 if objective else None,
    )


def expected_plane(bands: Any, transfer: Any, initial: Any, **options: Any) -> Expected:
    """Literal CE05 finite search with CE06 pair01/adjacent/product substitutions."""
    nt, nd, _, _, ny, nx = bands.input_shape
    orders = bands.noise_variance_factors.shape[1]
    raw = np.empty((nt, nd, orders - 1), dtype=np.complex128)
    answer = Expected(np.empty((nt, nd, 2)), raw, np.empty_like(raw), ())
    branches = []
    for t in range(nt):
        row = []
        for d in range(nd):

            def event(kind: str, *, t: int = t, d: int = d, **details: Any) -> None:
                answer.trace.append(Event(kind, t, d, tuple(details.items())))

            def build(
                k: Any, pair: tuple[int, int], purpose: str, *, t: int = t, d: int = d
            ) -> Build:
                value = plane_build(bands, transfer, k, pair, t, d, purpose, len(answer.overlaps))
                answer.overlaps.append(value)
                return value

            def evaluate(
                value: Build,
                stage: str,
                k: Any,
                angle: Any,
                magnitude: Any,
                remake: bool,
                *,
                t: int = t,
                d: int = d,
                publish: Any = event,
            ) -> float:
                fit = plane_regression(value, k, stage != "known")
                publish(
                    "evaluation",
                    stage=stage,
                    orders=value.orders,
                    overlap_index=value.index,
                    remake_overlaps=remake,
                    angle_rad=angle,
                    magnitude_cyc_um=magnitude,
                    carrier_cyc_um=np.array(k),
                    **fit,
                )
                raw[t, d, value.orders[1] - 1] = fit["forward"]
                return fit["objective"] if stage != "known" else 0.0

            reused = bool(t and options["use_time0_carriers"] and options["search_carriers"])
            if not options["search_carriers"] or reused:
                row.append("time0-reused" if reused else "known")
                k = answer.carriers_cyc_um[0, d].copy() if reused else initial[d].copy()
                if reused:
                    event("reuse", source_time=0, carrier_cyc_um=k.copy())
                for b in range(1, orders):
                    evaluate(build(k, (0, b), "known"), "known", k, None, None, True)
            else:
                row.append("searched")
                coarse = build(initial[d], (0, 1), "coarse")
                corr = finite_transform(coarse.spatial[0, 0] * coarse.spatial[1, 0].conj(), -1)
                power = np.abs(corr) ** 2
                iy, ix = np.unravel_index(int(np.argmax(power)), power.shape)
                xn = np.array([power[iy, (ix + q) % nx] for q in (-1, 0, 1)])
                yn = np.array([power[(iy + q) % ny, ix] for q in (-1, 0, 1)])

                def offset(values: Any) -> tuple[float, str]:
                    minus, center, plus = map(float, values)
                    curvature = plus + minus - 2 * center
                    if curvature == 0:
                        return 0.0, "zero-curvature"
                    value = -(plus - minus) / (2 * curvature)
                    return (0.0, "outside-range") if abs(value) > 1.5 else (value, "fitted")

                xo, xs = offset(xn)
                yo, ys = offset(yn)
                peak = np.array([float(ix) + xo, float(iy) + yo])
                before, decisions = peak.copy(), []
                for axis, sign in ((0, -1), (0, 1), (1, -1), (1, 1)):
                    size = (nx, ny)[axis]
                    decision = (
                        bool(initial[d, axis] / size < peak[axis] - size // 2)
                        if sign < 0
                        else bool(initial[d, axis] / size > peak[axis] + size // 2)
                    )
                    decisions.append(decision)
                    if decision:
                        peak[axis] += sign * size
                k = peak / [nx, ny]
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
                assert np.any(k), "independent fixture reaches zero coarse polar conversion"
                mag0, angle = math.hypot(*k), math.atan2(k[1], k[0])
                frozen = build(k, (0, 1), "refinement")
                x1, amp1 = 0.0, 0.0
                magnitude = mag0
                for stage, start, step in (
                    ("angle", angle, 0.001),
                    ("magnitude", mag0, 0.1 / max(nx, ny)),
                ):

                    def probe(
                        coordinate: float,
                        remake: bool = False,
                        *,
                        stage: str = stage,
                        mag0: float = mag0,
                        angle: float = angle,
                        frozen: Build = frozen,
                    ) -> float:
                        a, m = (coordinate, mag0) if stage == "angle" else (angle, coordinate)
                        vector = np.array([m * math.cos(a), m * math.sin(a)])
                        return evaluate(frozen, stage, vector, float(a), float(m), remake)

                    x2, x3 = float(start), float(start + step)
                    amp2, amp3 = probe(x2, stage == "angle"), probe(x3)
                    bracket_event(
                        event, stage, "initial", bool(amp3 > amp2), (x1, amp1, x2, amp2, x3, amp3)
                    )
                    if amp3 > amp2:
                        candidate, increment = x3, step
                        branch = "positive"
                    else:
                        candidate, increment = float(start), -step
                        x2, x3, amp2, amp3 = x3, x2, amp3, amp2
                        branch = "negative-swap"
                    bracket_event(
                        event, stage, branch, bool(amp3 > amp2), (x1, amp1, x2, amp2, x3, amp3)
                    )
                    while amp3 > amp2:
                        x1, amp1, x2, amp2 = x2, amp2, x3, amp3
                        candidate += increment
                        x3, amp3 = candidate, probe(candidate)
                        bracket_event(
                            event, stage, "shift", bool(amp3 > amp2), (x1, amp1, x2, amp2, x3, amp3)
                        )
                    bracket_event(event, stage, "stop", False, (x1, amp1, x2, amp2, x3, amp3))
                    result, status, budget = parabola((x1, amp1, x2, amp2, x3, amp3))
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
                for b in range(2, orders):
                    evaluate(
                        build(k, (b - 1, b), "later-order"),
                        "later-order",
                        k,
                        angle,
                        magnitude,
                        True,
                    )
            answer.carriers_cyc_um[t, d] = k
            cumulative = raw[t, d].copy()
            for b in range(2, orders):
                cumulative[b - 1] *= cumulative[b - 2]
                event(
                    "cumulative-product",
                    order=b,
                    direct_forward=complex(raw[t, d, b - 1]),
                    previous_cumulative=complex(cumulative[b - 2]),
                    product=complex(cumulative[b - 1]),
                )
            floors = options["amplitude_floors"]
            after = cumulative.copy()
            applied = []
            for b in range(1, orders):
                use = floors is not None and abs(after[b - 1]) < floors[b - 1]
                applied.append(bool(use))
                if use:
                    assert floors is not None
                    assert after[b - 1] != 0
                    after[b - 1] *= floors[b - 1] / abs(after[b - 1])
            if not options["fit_all_phases"]:
                assert after[0] != 0
            phi = cmath.phase(after[0])
            for b in range(1, orders):
                replace = not options["fit_all_phases"] and b >= 2
                final = abs(after[b - 1]) * cmath.exp(1j * b * phi) if replace else after[b - 1]
                answer.modulation[t, d, b - 1] = final
                event(
                    "adjustment",
                    order=b,
                    raw_forward=complex(cumulative[b - 1]),
                    floor=None if floors is None else float(floors[b - 1]),
                    floor_applied=applied[b - 1],
                    after_floor=complex(after[b - 1]),
                    phase_replaced=replace,
                    final=complex(final),
                )
        branches.append(tuple(row))
    answer.branches = tuple(branches)
    return answer


def exact(actual: Any, expected: Any) -> None:
    """Same-environment parity includes scalar/array signed-zero bits and types."""
    assert type(actual) is type(expected)
    if isinstance(expected, np.ndarray):
        assert actual.shape == expected.shape and actual.dtype == expected.dtype
        assert actual.tobytes(order="C") == expected.tobytes(order="C")
    elif isinstance(expected, float):
        assert struct.pack("!d", actual) == struct.pack("!d", expected)
    elif isinstance(expected, complex):
        exact(actual.real, expected.real)
        exact(actual.imag, expected.imag)
    elif isinstance(expected, tuple):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected, strict=True):
            exact(a, e)
    elif dataclasses.is_dataclass(expected):
        for field in dataclasses.fields(expected):
            exact(getattr(actual, field.name), getattr(expected, field.name))
    else:
        assert actual == expected


def compact_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return compact_value(value.tolist())
    if isinstance(value, list | tuple):
        return tuple(compact_value(v) for v in value)
    return value


def assert_capture_projection(summary: Any, full: Any) -> None:
    parameters = full.parameters
    assert len(summary.overlap_builds) == len(parameters.overlaps)
    for index, (descriptor, build) in enumerate(
        zip(summary.overlap_builds, parameters.overlaps, strict=True)
    ):
        for name in ("index", "time_index", "direction_index", "purpose", "orders"):
            exact(getattr(descriptor, name), getattr(build, name))
        assert descriptor.index == index
        exact(descriptor.carrier_cyc_um, compact_value(build.carrier_cyc_um))
        assert not hasattr(descriptor, "spatial") and not hasattr(descriptor, "fourier")
    assert len(summary.search_trace) == len(parameters.trace)
    for compact, complete in zip(summary.search_trace, parameters.trace, strict=True):
        for name in ("kind", "time_index", "direction_index"):
            exact(getattr(compact, name), getattr(complete, name))
        expected = tuple(
            (key, compact_value(value))
            for key, value in complete.details
            if complete.kind != "coarse" or key not in ("correlation_complex", "correlation_power")
        )
        exact(compact.details, expected)
        for key, value in compact.details:
            if key == "overlap_index":
                assert 0 <= value < len(summary.overlap_builds)
    for name in (
        "image",
        "x_um",
        "y_um",
        "z_um",
        "initial_carriers_cyc_um",
        "phase_linkage_carriers_cyc_um",
        "effective_wiener",
        "input_identities",
        "trace",
        "source_revision",
        "reference_sha256",
        "limitations",
        "intensity_unit",
        "intensity_semantics",
    ):
        exact(getattr(summary, name), getattr(full, name))
    for name in ("carriers_cyc_um", "raw_modulation", "modulation", "branches"):
        exact(getattr(summary, name), getattr(parameters, name))
    for name in ("samples",):
        identity = dict(summary.transfer)[name]
        array = getattr(full.transfer, name)
        canonical = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
        assert identity.name == "transfer.samples"
        assert identity.shape == array.shape and identity.dtype == canonical.dtype.str
        assert identity.sha256 == hashlib.sha256(canonical.tobytes()).hexdigest()


def public_arrays(value: Any) -> list[Any]:
    """Traverse declared public value fields only; no claim about hidden owners."""
    if isinstance(value, np.ndarray):
        return [value]
    if isinstance(value, tuple):
        return [array for item in value for array in public_arrays(item)]
    if dataclasses.is_dataclass(value):
        return [
            array
            for field in dataclasses.fields(value)
            for array in public_arrays(getattr(value, field.name))
        ]
    return []


def independent_images(bands: Any, transfer: Any, expected: Expected) -> list[Any]:
    images = []
    for t in range(bands.input_shape[0]):
        sliced = SimpleNamespace(**vars(bands))
        sliced.input_shape = (1, *bands.input_shape[1:])
        sliced.quadratures = bands.quadratures[t : t + 1]
        # All sampled axial indices are zero in Z1, so positive surrogate pitch
        # evaluates the identical finite filter equations for accepted dz=0.
        if sliced.dz_um == 0:
            sliced.dz_um = 1.0
        images.append(
            known_image_sum(sliced, transfer, expected.carriers_cyc_um[t], expected.modulation[t])
        )
    return images


def assert_image_oracle(actual: Any, images: list[Any], expected: Expected) -> None:
    wanted = np.concatenate(images, axis=0)
    scale = max(1.0, float(np.max(np.abs(wanted))))
    # At V<=72, Q<=9, D<=3: finite transforms/dots/positive Wiener=.5
    # quotients have <4096 elementary operations per output contribution.
    # gamma_4096 < 4.6e-13; inherited 3e-11 envelope exceeds 64*gamma_4096.
    # Parameter-coordinate phase sensitivity is propagated separately, never
    # used for compact/full parity or scalar/discrete comparisons.
    allowance = ATOL + 128 * math.pi * scale * expected.coordinate_budget
    np.testing.assert_allclose(actual, wanted, rtol=RTOL, atol=allowance)
