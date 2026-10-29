"""Independent RA02 finite sums, Decimal least squares, and public controls.

Axes are z/y/x (or y/x), origin index zero; spacings are micrometres,
frequencies cycles/micrometre, phases radians. No product helper is an oracle.
Run through source_free_check.py python with --output artifacts/ra02/A/figure.npz
for actual arrays; rendering belongs to the coordinator.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from itertools import product
from math import prod
from typing import Any

import numpy as np
from numpy.typing import NDArray

from simrecon import Otf2D, VolumeOrderOtf, reconstruct_volume

Real = NDArray[np.float64]
Complex = NDArray[np.complex128]
Array = NDArray[Any]
EPS = 2.0**-52
PI = Decimal("3.14159265358979323846264338327950288419716939937510582097494459230781640628620899")


def dec(value: Any) -> Decimal:
    """Exact binary64-to-decimal conversion, not decimal string rounding."""
    return Decimal.from_float(float(value))


def bins(n: int) -> range:
    return range(-(n // 2), (n + 1) // 2)


def modes(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(product(*(bins(n) for n in shape)))


@cache
def root(turn: Fraction) -> tuple[Decimal, Decimal]:
    """70-digit rational-turn root; only a final binary64 conversion rounds."""
    with localcontext() as ctx:
        ctx.prec = 80
        turn = (turn + Fraction(1, 2)) % 1 - Fraction(1, 2)
        x = 2 * PI * Decimal(turn.numerator) / Decimal(turn.denominator)
        c, s, ct, st = Decimal(1), x, Decimal(1), x
        for k in range(1, 101):
            ct *= -x * x / Decimal((2 * k - 1) * (2 * k))
            st *= -x * x / Decimal((2 * k) * (2 * k + 1))
            c += ct
            s += st
        return +c, +s


def wave(
    mode: tuple[int, ...], point: tuple[int, ...], shape: tuple[int, ...]
) -> tuple[Decimal, Decimal]:
    return root(
        sum((Fraction(k * x, n) for k, x, n in zip(mode, point, shape, strict=True)), Fraction())
    )


def finite_sum(values: Array, *, synthesis: bool = False) -> Complex:
    """Direct finite DFT/series synthesis with 70-digit accumulation; no FFT."""
    shape = values.shape
    locations = list(np.ndindex(shape))
    signed = modes(shape)
    out = np.empty(shape, dtype=np.complex128)
    converted = [(dec(v.real), dec(v.imag)) for v in values.ravel().astype(np.complex128)]
    with localcontext() as ctx:
        ctx.prec = 70
        for index, target in enumerate(locations if synthesis else signed):
            re, im = Decimal(0), Decimal(0)
            for (vr, vi), source in zip(converted, signed if synthesis else locations, strict=True):
                cr, si = wave(source, target, shape) if synthesis else wave(target, source, shape)
                if not synthesis:
                    si = -si
                re += vr * cr - vi * si
                im += vr * si + vi * cr
            divisor = 1 if synthesis else values.size
            out.flat[index] = complex(float(re / divisor), float(im / divisor))
    return out


def decimal_solve(matrix: Array, rhs: Array) -> Real:
    """Pivoted Gaussian elimination in 70-digit arithmetic, multiple RHS."""
    a = np.asarray(matrix, dtype=np.float64)
    b = np.asarray(rhs, dtype=np.float64)
    vector = b.ndim == 1
    if vector:
        b = b[:, None]
    with localcontext() as ctx:
        ctx.prec = 70
        rows = [[dec(v) for v in row] + [dec(v) for v in br] for row, br in zip(a, b, strict=True)]
        n, nrhs = a.shape[0], b.shape[1]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(rows[r][col]))
            rows[col], rows[pivot] = rows[pivot], rows[col]
            scale = rows[col][col]
            assert scale != 0
            rows[col] = [v / scale for v in rows[col]]
            for r in range(n):
                if r != col:
                    factor = rows[r][col]
                    rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col], strict=True)]
        result = np.array([[float(v) for v in row[n : n + nrhs]] for row in rows])
    return result[:, 0] if vector else result


def phase_matrix(phases: Real, harmonic: int) -> Real:
    c, s = np.cos(phases), np.sin(phases)
    columns = [np.ones(phases.size), 2 * c, -2 * s]
    if harmonic == 2:
        columns += [2 * (c * c - s * s), -2 * ((2 * c) * s)]
    return np.column_stack(columns)


def least_squares(k: Real, data: Real) -> Real:
    """Exact represented normal products and solve to 70 digits, then round."""
    n = k.shape[1]
    b = data.reshape(k.shape[0], -1)
    with localcontext() as ctx:
        ctx.prec = 70
        kd = [[dec(v) for v in row] for row in k]
        bd = [[dec(v) for v in row] for row in b]
        gram = [
            [sum((row[i] * row[j] for row in kd), Decimal(0)) for j in range(n)] for i in range(n)
        ]
        rhs = [
            [
                sum((row[i] * br[j] for row, br in zip(kd, bd, strict=True)), Decimal(0))
                for j in range(b.shape[1])
            ]
            for i in range(n)
        ]
        rows = [g + r for g, r in zip(gram, rhs, strict=True)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda r: abs(rows[r][col]))
            rows[col], rows[pivot] = rows[pivot], rows[col]
            scale = rows[col][col]
            assert scale != 0
            rows[col] = [v / scale for v in rows[col]]
            for r in range(n):
                if r != col:
                    factor = rows[r][col]
                    rows[r] = [x - factor * y for x, y in zip(rows[r], rows[col], strict=True)]
        result = np.array([[float(v) for v in row[n:]] for row in rows])
    return result.reshape((n, *data.shape[1:]))


def coordinates(components: Any, harmonic: int) -> Real:
    fields = [components.dc, components.c1.real, components.c1.imag]
    if harmonic == 2:
        fields += [components.c2.real, components.c2.imag]
    return np.stack(fields)


def bands(z: Real) -> list[Complex]:
    return [z[0].astype(np.complex128)] + [z[i] + 1j * z[i + 1] for i in range(1, z.shape[0], 2)]


def negative_index(index: tuple[int, ...], shape: tuple[int, ...]) -> tuple[int, ...]:
    return tuple((-(i - n // 2) + n // 2) % n for i, n in zip(index, shape, strict=True))


def frequency(n: int, spacing: float) -> Real:
    with localcontext() as ctx:
        ctx.prec = 70
        return np.array([float(Decimal(k) / Decimal(n) / dec(spacing)) for k in bins(n)])


def order_record(
    values: Complex, spacing: tuple[float, float, float], origin: tuple[int, int, int] = (0, 0, 0)
) -> VolumeOrderOtf:
    axes = [frequency(n, d) for n, d in zip(values.shape[1:], spacing, strict=True)]
    return VolumeOrderOtf(
        values=values,
        fz_per_um=axes[0],
        fy_per_um=axes[1],
        fx_per_um=axes[2],
        voxel_size_um=spacing,
        origin_zyx=origin,
        source="RA02 independent algebraic transfer",
    )


def otf_record(values: Complex, spacing: tuple[float, float]) -> Otf2D:
    return Otf2D(
        values=values,
        fy_per_um=frequency(values.shape[0], spacing[0]),
        fx_per_um=frequency(values.shape[1], spacing[1]),
        pixel_size_um=spacing,
        origin_yx=(0, 1),
        source="RA02 Hermitian finite kernel",
    )


def volume_oracle(
    images: Real,
    phases: Real,
    transfers: list[Complex],
    carriers: Array,
    gains: Real,
    penalty: float,
    mask: Real,
) -> tuple[Complex, Complex, Real]:
    """Stored-input LS followed by literal independent finite sums/Decimal fusion."""
    detector_shape = images.shape[2:]
    output_shape = mask.shape
    u = [[Decimal(0), Decimal(0)] for _ in range(mask.size)]
    v = [Decimal(0) for _ in range(mask.size)]
    out_lookup = {q: i for i, q in enumerate(modes(output_shape))}
    with localcontext() as ctx:
        ctx.prec = 70
        for data, phi, transfer, carrier, gain in zip(
            images, phases, transfers, carriers, gains, strict=True
        ):
            z = least_squares(phase_matrix(phi, 2), data)
            spatial = bands(z)
            d = {m: finite_sum(spatial[m]) for m in range(3)}
            d[-1], d[-2] = finite_sum(np.conj(spatial[1])), finite_sum(np.conj(spatial[2]))
            for index, j in zip(np.ndindex(detector_shape), modes(detector_shape), strict=True):
                for m in range(-2, 3):
                    q = (j[0], j[1] - m * int(carrier[0]), j[2] - m * int(carrier[1]))
                    oi = out_lookup[q]
                    e = (
                        transfer[(m, *index)]
                        if m >= 0
                        else np.conj(transfer[(-m, *negative_index(index, detector_shape))])
                    )
                    tr, ti = dec(gain) * dec(e.real), dec(gain) * dec(e.imag)
                    dr, di = dec(d[m][index].real), dec(d[m][index].imag)
                    u[oi][0] += tr * dr + ti * di
                    u[oi][1] += tr * di - ti * dr
                    v[oi] += tr * tr + ti * ti
        spectrum = np.zeros(output_shape, dtype=np.complex128)
        for i, (ur, ui) in enumerate(u):
            denominator = v[i] + dec(penalty)
            if denominator:
                amplitude = dec(mask.flat[i])
                spectrum.flat[i] = complex(
                    float(amplitude * ur / denominator), float(amplitude * ui / denominator)
                )
    return (
        spectrum,
        finite_sum(spectrum, synthesis=True),
        np.array([float(x) for x in v]).reshape(output_shape),
    )


def oracle_2d(
    images: Real,
    phases: Real,
    h: Complex,
    shifts: Array,
    modulation: Real,
    brightness: Real,
    penalty: float,
    mask: Real,
) -> tuple[Complex, Complex, Real]:
    """Integer-shift 2D own-estimator oracle, with closed canonical endpoints."""
    shape = images.shape[2:]
    detector = {q: i for i, q in enumerate(modes(shape))}
    u = np.zeros(mask.shape, dtype=np.complex128)
    v = np.zeros(mask.shape)
    # DFT/phase truth comes from high precision; small weighted reductions below
    # have explicit observer allowance, separate from product accuracy budgets.
    for data, phi, shift, mod, gain in zip(
        images, phases, shifts, modulation, brightness, strict=True
    ):
        dc, c1 = bands(least_squares(phase_matrix(phi, 1), data))
        transforms = [finite_sum(dc), finite_sum(c1), finite_sum(np.conj(c1))]
        for oi, q in enumerate(modes(mask.shape)):
            for m, d in zip((0, 1, -1), transforms, strict=True):
                j = tuple(k + m * int(c) for k, c in zip(q, shift, strict=True))
                if j in detector:
                    di = detector[j]
                    t = gain * h.flat[di] * (1 if m == 0 else mod / 2)
                    u.flat[oi] += np.conj(t) * d.flat[di]
                    v.flat[oi] += t.real * t.real + t.imag * t.imag
    spectrum = np.zeros(mask.shape, dtype=np.complex128)
    nonzero = v + penalty > 0
    spectrum[nonzero] = mask[nonzero] * u[nonzero] / (v[nonzero] + penalty)
    return spectrum, finite_sum(spectrum, synthesis=True), v


def fusion_budget(
    images: Real,
    phases: Real,
    denominator: Real,
    output_shape: tuple[int, ...],
    *,
    volume: bool,
    gains: Real,
    penalty: float,
) -> dict[str, float | int]:
    """Pre-call informative-regime checks and separate normative/observer bounds."""
    r, n = images.shape[:2]
    m, p = prod(images.shape[2:]), prod(output_shape)
    scale = float(np.max(np.abs(images)))
    condition = max(float(np.linalg.cond(phase_matrix(phi, 2 if volume else 1))) for phi in phases)
    positive = denominator[denominator > 0]
    margin = float(np.min(positive))
    assert condition <= 10 and margin > 0
    assert np.all((gains >= 0.5) & (gains <= 2))
    with localcontext() as ctx:
        ctx.prec = 70
        epsilon, tiny, b = Decimal(2) ** -52, Decimal(2) ** -1074, dec(scale)
        if volume:
            j = 5 * r
            assert margin >= 0.25 and penalty <= 1
            assert Decimal(65536 * j * (n + m + p)) * epsilon <= Decimal(2) ** -10
            assert Decimal(64 * j * p) * max(b, tiny) <= dec(np.finfo(float).max)
            bs = Decimal(65536 * j * (n + m)) * epsilon * b + Decimal(256 * j * (n + m)) * tiny
            bv = p * bs + Decimal(16384 * j * p) * epsilon * b + 64 * p * tiny
        else:
            assert margin >= 1e-6 * max(1.0, float(np.max(denominator)), penalty)
            bs = Decimal(8192 * r * n * p) * epsilon * b / dec(np.min(gains)) + 8 * p * tiny
            bv = bs
        observer = (
            128 * EPS * (n + m + p) * max(1.0, scale) * max(1.0, condition) / min(1.0, margin)
        )
        observer_volume = observer * p if volume else observer
        assert observer < float(bs) / 8 and observer_volume < float(bv) / 8
        return dict(
            N=n,
            M=m,
            P=p,
            B=scale,
            condition=condition,
            denominator_margin=margin,
            spectrum_bound=float(bs),
            spatial_bound=float(bv),
            observer_spectrum=observer,
            observer_spatial=observer_volume,
        )


def asymmetric_volume_control() -> dict[str, Any]:
    shape, outshape = (3, 2, 5), (3, 6, 9)
    phases = np.array([[-0.4, 0.5, 1.8, 3.0, 4.5, 5.7], [0.1, 0.9, 2.2, 3.4, 4.6, 5.9]])
    carriers = np.array([[1, -1], [-1, 1]])
    gains = np.array([0.75, 1.5])
    spacing = (0.7, 0.4, 0.25)
    origin = (1, 1, 2)
    images, transfers = [], []
    for r, phi in enumerate(phases):
        points = np.indices(shape)
        z = np.stack(
            [
                1 + points[0] / 8 - points[2] / 6,
                (points[1] - 0.5) / 3,
                (points[2] - 2) / 7,
                (points[0] - 1) / 5,
                (points[2] + points[1] - 2) / 9,
            ]
        )
        raw = np.einsum("pk,kzyx->pzyx", phase_matrix(phi, 2), z)
        raw += (np.arange(phi.size) ** 2)[:, None, None, None] * 0.003 * (r + 1)
        images.append(raw)
        e = np.empty((3, *shape), dtype=np.complex128)
        for oi in range(3):
            for index, j in zip(np.ndindex(shape), modes(shape), strict=True):
                cr, si = wave(j, origin, shape)
                phase = complex(float(cr), float(-si))
                e[(oi, *index)] = phase * complex(
                    (3 + oi + r + index[0]) / 12, (index[1] + 2 * index[2] - 3 - oi) / 24
                )
        assert np.max(np.abs(e.real)) <= 1 and np.max(np.abs(e.imag)) <= 1
        transfers.append(e)
    mask = (0.25 + 0.75 * np.arange(prod(outshape)) / (prod(outshape) - 1)).reshape(outshape)
    mask[0, 1, 2] = 0
    return dict(
        images=np.array(images),
        phases=phases,
        transfers=transfers,
        carriers=carriers,
        gains=gains,
        penalty=0.5,
        mask=mask,
        spacing=spacing,
        origin=origin,
    )


def call_volume(control: dict[str, Any]) -> Any:
    return reconstruct_volume(
        control["images"],
        order_otfs=[
            order_record(e, control["spacing"], control.get("origin", (0, 0, 0)))
            for e in control["transfers"]
        ],
        phases_rad=control["phases"],
        carriers_bins=control["carriers"],
        gains=control["gains"],
        regularization=control["penalty"],
        output_shape_yx=control["mask"].shape[1:],
        apodization=control["mask"],
    )


def observe_volume(control: dict[str, Any]) -> dict[str, Any]:
    expected, spatial, v = volume_oracle(
        control["images"],
        control["phases"],
        control["transfers"],
        control["carriers"],
        control["gains"],
        control["penalty"],
        control["mask"],
    )
    budget = fusion_budget(
        control["images"],
        control["phases"],
        v + control["penalty"],
        control["mask"].shape,
        volume=True,
        gains=control["gains"],
        penalty=control["penalty"],
    )
    actual = call_volume(control)
    return dict(
        control=control,
        expected_spectrum=expected,
        expected_spatial=spatial,
        actual_spectrum=actual.spectrum,
        actual_spatial=actual.volume,
        signed_spectrum_difference=actual.spectrum - expected,
        signed_spatial_difference=actual.volume - spatial,
        axes=(actual.fz_per_um, actual.fy_per_um, actual.fx_per_um),
        budget=budget,
    )


def real_basis(shape: tuple[int, ...], representatives: list[tuple[int, ...]]) -> Real:
    """DC then unnormalized cosine/sine pairs; no duplicate conjugates."""
    columns = [np.ones(prod(shape))]
    for q in representatives:
        roots = [wave(q, p, shape) for p in np.ndindex(shape)]
        columns.extend(
            [np.array([float(cr) for cr, _ in roots]), np.array([float(si) for _, si in roots])]
        )
    return np.column_stack(columns)


def convolution_matrix(
    detector_shape: tuple[int, ...],
    phases: Real,
    transfers: list[Complex],
    carrier: tuple[int, ...],
    gain: float,
    representatives: list[tuple[int, ...]],
) -> tuple[Real, Real]:
    """Real raw forward map assembled by spatial circular convolution.

    Transfer inverse sums give kernels. Carrier multiplies source BEFORE each
    convolution. No product separation/fusion/FFT is called here.
    """
    source = real_basis(detector_shape, representatives)
    locations = list(np.ndindex(detector_shape))
    harmonic = len(transfers) - 1
    k = phase_matrix(phases, harmonic)
    kernels = [finite_sum(e, synthesis=True) / prod(detector_shape) for e in transfers]
    band_maps = []
    for m, kernel in enumerate(kernels):
        result = np.zeros_like(source, dtype=np.complex128)
        for xi, x in enumerate(locations):
            for ui, u in enumerate(locations):
                displacement = tuple(
                    (xx - uu) % n for xx, uu, n in zip(x, u, detector_shape, strict=True)
                )
                cr, si = wave(tuple(m * c for c in carrier), u, detector_shape)
                result[xi] += kernel[displacement] * complex(float(cr), float(si)) * source[ui]
        band_maps.append(result * gain)
    assert np.max(np.abs(band_maps[0].imag)) < 1e-12
    coordinates_map = [band_maps[0].real]
    for c in band_maps[1:]:
        coordinates_map += [c.real, c.imag]
    raw_map = np.einsum("pk,kud->pud", k, np.array(coordinates_map)).reshape(
        phases.size * prod(detector_shape), -1
    )
    return raw_map, np.array(coordinates_map)


def matched_control(*, volume: bool) -> dict[str, Any]:
    if volume:
        shape, outshape = (3, 1, 7), (3, 1, 11)
        reps = [(0, 0, 1), (1, 0, -1), (1, 0, 0), (1, 0, 1)]
        phi = np.array([-0.3, 0.8, 2.0, 3.4, 5.0])
        support = {(z, 0, x) for z in (-1, 0, 1) for x in (-1, 0, 1)}
        transfer = np.zeros((3, *shape), dtype=np.complex128)
        for index, j in zip(np.ndindex(shape), modes(shape), strict=True):
            for m in range(3):
                if (j[0], 0, j[2] - m) in support:
                    transfer[(m, *index)] = (
                        0.75 if m == 0 else complex(0.5 + m / 16, (j[0] + j[2]) / 32)
                    )
        carrier, gain = (0, 0, 1), 1.25
        transfers = list(transfer)
        public_transfer = transfer
    else:
        shape, outshape = (1, 7), (2, 14)
        reps = [(0, 1)]
        phi = np.array([-0.2, 1.7, 4.1])
        h = np.zeros(shape, dtype=np.complex128)
        for i, j in enumerate(modes(shape)):
            if abs(j[1]) <= 2:
                cr, si = wave(j, (0, 1), shape)
                h.flat[i] = (1 if j[1] == 0 else 0.75) * complex(float(cr), float(-si))
        transfers = [h, 0.375 * h]
        public_transfer = h
        carrier, gain = (0, 1), 1.25
    a, band_map = convolution_matrix(shape, phi, transfers, carrier, gain, reps)
    basis = real_basis(outshape, reps)
    k = phase_matrix(phi, 2 if volume else 1)
    inverse = decimal_solve(k, np.eye(k.shape[0]))
    g = np.diag([1.0] + [2.0] * (k.shape[1] - 1))
    w = inverse.T @ g @ inverse
    metric = np.kron(w, np.eye(prod(shape))) / prod(shape)
    gram = basis.T @ basis / prod(outshape)
    theta = np.array([1.0, -0.4, 0.3, 0.2, -0.25, 0.15, 0.1, -0.2, 0.35][: basis.shape[1]])
    raw = (a @ theta).reshape((phi.size, *shape))
    # A deterministic raw residual makes this an inverse comparison beyond
    # merely reproducing the original source coordinates.
    raw += (0.015 * np.arange(phi.size) / phi.size).reshape((phi.size, *((1,) * len(shape))))
    penalty = 0.25
    normal = a.T @ metric @ a + penalty * gram
    rhs = a.T @ metric @ raw.ravel()
    solution = decimal_solve(normal, rhs)
    tolerance = (
        4096
        * EPS
        * (raw.size + basis.shape[1] + basis.shape[0]) ** 2
        * max(
            1.0,
            float(np.linalg.norm(a)),
            float(np.linalg.norm(raw)),
            float(np.linalg.norm(solution)),
        )
        * max(1.0, float(np.linalg.cond(normal)))
    )
    assert tolerance < 1e-5
    return dict(
        shape=shape,
        outshape=outshape,
        representatives=reps,
        phases=phi,
        transfer=public_transfer,
        gain=gain,
        carrier=carrier,
        images=raw,
        basis=basis,
        band_map=band_map,
        a=a,
        metric=metric,
        w=w,
        gram=gram,
        normal=normal,
        solution=solution,
        penalty=penalty,
        tolerance=tolerance,
    )


def figure_arrays() -> dict[str, Array]:
    """Actual tested signed arrays and physical coordinates; no rendering.

    spectrum arrays are centered z/y/x, zero at shape//2; volume origin is
    spatial index (0,0,0). Inputs: R,N,z,y,x. Spacing in micrometres. Signed
    differences are actual minus expected, retaining both complex components.
    """
    observation = observe_volume(asymmetric_volume_control())
    c = observation["control"]
    return dict(
        images=c["images"],
        phases_rad=c["phases"],
        carriers_yx_bins=c["carriers"],
        gains=c["gains"],
        transfers=np.array(c["transfers"]),
        mask=c["mask"],
        regularization=np.array(c["penalty"]),
        input_spacing_um=np.array(c["spacing"]),
        transfer_origin_zyx=np.array(c["origin"]),
        expected_spectrum=observation["expected_spectrum"],
        actual_spectrum=observation["actual_spectrum"],
        expected_volume=observation["expected_spatial"],
        actual_volume=observation["actual_spatial"],
        signed_spectrum_difference=observation["signed_spectrum_difference"],
        signed_volume_difference=observation["signed_spatial_difference"],
        fz_per_um=observation["axes"][0],
        fy_per_um=observation["axes"][1],
        fx_per_um=observation["axes"][2],
        centered_dc_index=np.array(c["mask"].shape) // 2,
        spatial_origin_index=np.zeros(3, dtype=np.int64),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    np.savez(args.output, allow_pickle=False, **figure_arrays())
    print("RA02 figure arrays written; signed differences retain complex values")
