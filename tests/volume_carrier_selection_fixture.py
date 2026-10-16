"""Independent stored-input observer; never imports selector or scanner internals."""

from __future__ import annotations

import itertools
from collections.abc import Iterable
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np

from simrecon import EmpiricalVolumeResponse

PI = Decimal(
    "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
)
Pair = tuple[Decimal, Decimal]


def dsum(values: Iterable[Decimal]) -> Decimal:
    return sum(values, Decimal(0))


def dec(value: Any) -> Decimal:
    f = Fraction(value)
    return Decimal(f.numerator) / Decimal(f.denominator)


def add(a: Pair, b: Pair) -> Pair:
    return a[0] + b[0], a[1] + b[1]


def mul(a: Pair, b: Pair) -> Pair:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def conj(a: Pair) -> Pair:
    return a[0], -a[1]


def norm2(a: Pair) -> Decimal:
    return a[0] ** 2 + a[1] ** 2


def unit(angle: Decimal) -> Pair:
    """90-digit Taylor observer; bounded argument, no production trig/FFT."""
    angle %= 2 * PI
    c = ct = Decimal(1)
    s = st = angle
    for k in range(1, 180):
        ct *= -(angle * angle) / ((2 * k - 1) * (2 * k))
        st *= -(angle * angle) / ((2 * k) * (2 * k + 1))
        c += ct
        s += st
    return c, s


def phase_matrix(phases: Any) -> Any:
    c, s = np.cos(phases), np.sin(phases)
    return np.column_stack((np.ones(len(phases)), c, s, c * c - s * s, (2 * c) * s))


def response(shape: tuple[int, int, int] = (4, 4, 8)) -> Any:
    spacing = (0.5, 0.25, 0.125)
    axes = [
        np.array([float(Fraction(k, n) / Fraction(d)) for k in range(-(n // 2), (n + 1) // 2)])
        for n, d in zip(shape, spacing, strict=True)
    ]
    z, y, x = np.meshgrid(*axes, indexing="ij")
    values = np.empty((3, *shape), dtype=np.complex128)
    values[0] = 1 + z / 8 + y * x / 16 + 1j * (1 / 8 + x / 8 - z * y / 16)
    values[1] = 3 / 4 + y / 16 + z * x / 32 + 1j * (1 / 4 - z / 16 + y * x / 32)
    values[2] = 5 / 4 - x / 16 + z * y / 32 + 1j * (-1 / 8 + y / 8 + z * x / 32)
    return EmpiricalVolumeResponse(
        values, axes[0], axes[1], axes[2], spacing, (1 % shape[0], 1 % shape[1], 2 % shape[2])
    )


def case(order: int = 1) -> tuple[Any, dict[str, Any]]:
    phases = np.array([-0.29, 0.51, 1.41, 2.36, 3.15, 4.40, 5.73])
    z, y, x = np.indices((2, 3, 4))
    dc = 3 + z / 4 - y / 8 + x / 16 + z * x / 32
    c1 = (1 + x / 4 - y / 8) + 1j * (y / 4 - z / 8 + x / 16)
    c2 = (-1 / 2 + z / 8 + y / 16) + 1j * (3 / 4 - x / 8 + z * y / 16)
    h = phase_matrix(phases)
    coordinates = np.stack((dc, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag))
    images = np.einsum("pj,jzyx->pzyx", h, coordinates)
    # A true overdetermined, off-model residual, not an exact hidden-parameter fit.
    images[2, 1, 1, 2] += 0.03125
    return images, {
        "response": response(),
        "voxel_size_um": (1.0, 2.0, 4.0),
        "phase_steps_rad": phases,
        "candidate_carriers_yx": [(0, 0), (0, 1), (-1, 0)],
        "order": order,
        "calibration_carrier_bins": (1, -2),
        "coordinate_offset_yx": (2, -1),
        "phase_reference_shift_rad": 0.37,
        "source": "  independent stored-input pairing; opaque  ",
    }


def simple_case() -> tuple[Any, dict[str, Any]]:
    images, args = case()
    args.update(
        calibration_carrier_bins=(0, 0), coordinate_offset_yx=(0, 0), phase_reference_shift_rad=0.0
    )
    args["response"].values[:] = 1 + 0j
    return images, args


def solve_coordinates(images: Any, phases: Any) -> list[list[Decimal]]:
    """Independent 90-digit normal-equation observer on *stored* H and b."""
    h = [[dec(float(v)) for v in row] for row in phase_matrix(phases)]
    b = [[dec(float(v)) for v in row] for row in images.reshape(len(phases), -1)]
    nvox = len(b[0])
    augmented: list[list[Decimal]] = [
        [dsum(h[p][i] * h[p][j] for p in range(len(h))) for j in range(5)]
        + [dsum(h[p][i] * b[p][v] for p in range(len(h))) for v in range(nvox)]
        for i in range(5)
    ]
    for i in range(5):
        pivot = max(range(i, 5), key=lambda k: abs(augmented[k][i]))
        augmented[i], augmented[pivot] = augmented[pivot], augmented[i]
        scale = augmented[i][i]
        augmented[i] = [v / scale for v in augmented[i]]
        for k in range(5):
            if k != i:
                factor = augmented[k][i]
                augmented[k] = [
                    a - factor * b for a, b in zip(augmented[k], augmented[i], strict=True)
                ]
    return [row[5:] for row in augmented]


def transfer(
    args: dict[str, Any], m: int, bins: tuple[int, ...], shape: Any
) -> tuple[Pair, Decimal]:
    r = args["response"]
    stencils = []
    for p, n, d, nc, dc in zip(
        bins, shape, args["voxel_size_um"], r.values.shape[1:], r.voxel_size_um, strict=True
    ):
        query = Fraction(float(Fraction(p, n) / Fraction(d)))
        pos = query * nc * Fraction(dc) + nc // 2
        low = pos.numerator // pos.denominator
        t = pos - low
        stencils.append([(low, 1 - t)] if t == 0 else [(low, 1 - t), (low + 1, t)])
    value = (Decimal(0), Decimal(0))
    envelope = Decimal(0)
    for stencil in itertools.product(*stencils):
        index = tuple(i for i, _ in stencil)
        weight = dec(stencil[0][1] * stencil[1][1] * stencil[2][1])
        v = complex(r.values[(m, *index)])
        value = add(value, (weight * dec(v.real), weight * dec(v.imag)))
        envelope += weight * (abs(dec(v.real)) + abs(dec(v.imag)))
    if m:
        rho = (
            sum(
                Fraction(k * (origin + offset), n)
                for k, origin, offset, n in zip(
                    args["calibration_carrier_bins"],
                    r.origin_zyx[1:],
                    args["coordinate_offset_yx"],
                    r.values.shape[2:],
                    strict=True,
                )
            )
            % 1
        )
        angle = -m * (2 * PI * dec(rho) + dec(args["phase_reference_shift_rad"]))
        value = mul(value, unit(angle))
    return value, envelope


def independent_rows(
    images: Any, args: dict[str, Any], precision: int = 90
) -> list[dict[str, Any]]:
    with localcontext() as ctx:
        ctx.prec = precision
        shape = images.shape[1:]
        sites = list(itertools.product(*(range(n) for n in shape)))
        bins = list(itertools.product(*(range(-(n // 2), (n + 1) // 2) for n in shape)))
        coordinates = solve_coordinates(images, args["phase_steps_rad"])
        m = args["order"]
        bands = [
            [(v, Decimal(0)) for v in coordinates[0]],
            [
                (a / 2, -b / 2)
                for a, b in zip(coordinates[2 * m - 1], coordinates[2 * m], strict=True)
            ],
        ]
        spectra = []
        for band in bands:
            spectrum = {}
            for p in bins:
                total = (Decimal(0), Decimal(0))
                for site, coefficient in zip(sites, band, strict=True):
                    angle = (
                        -2
                        * PI
                        * dsum(
                            dec(Fraction(k * r, n)) for k, r, n in zip(p, site, shape, strict=True)
                        )
                    )
                    total = add(total, mul(coefficient, unit(angle)))
                spectrum[p] = (total[0] / len(sites), total[1] / len(sites))
            spectra.append(spectrum)
        eps, q0 = Decimal(2) ** -52, Decimal(2) ** -1074
        big_b = max(abs(dec(float(v))) for v in images.flat)
        alpha = 8192 * len(images) * eps * big_b + 8 * q0
        d = 2 * alpha + 4096 * len(sites) * eps * (10 * big_b + 2 * alpha) + 64 * q0
        result = []
        for ky, kx in args["candidate_carriers_yx"]:
            data = []
            for p in bins:
                j = (p[0], p[1] + m * ky, p[2] + m * kx)
                if j not in spectra[1]:
                    continue
                f0, l0 = transfer(args, 0, p, shape)
                fm, lm = transfer(args, m, j, shape)
                data.append(
                    (
                        spectra[0][p],
                        spectra[1][j],
                        f0,
                        fm,
                        1024 * eps * l0 + 64 * q0,
                        1024 * eps * lm + 64 * q0,
                    )
                )
            x = [mul(fm, dc) for dc, _, _, fm, _, _ in data]
            y = [mul(f0, cm) for _, cm, f0, _, _, _ in data]
            xn = dsum(norm2(v) for v in x).sqrt()
            yn = dsum(norm2(v) for v in y).sqrt()
            cross = (Decimal(0), Decimal(0))
            for a, b in zip(x, y, strict=True):
                cross = add(cross, mul(conj(a), b))
            beta = (cross[0] / xn**2, cross[1] / xn**2)
            c = (cross[0] / (xn * yn), cross[1] / (xn * yn))
            residual = dsum(
                norm2(add((b[0] / yn, b[1] / yn), mul((-c[0], -c[1]), (a[0] / xn, a[1] / xn))))
                for a, b in zip(x, y, strict=True)
            ).sqrt()
            sx = max(norm2(fm).sqrt() + em for _, _, _, fm, _, em in data) * max(
                norm2(dc).sqrt() + d for dc, _, _, _, _, _ in data
            )
            sy = max(norm2(f0).sqrt() + e0 for _, _, f0, _, e0, _ in data) * max(
                norm2(cm).sqrt() + d for _, cm, _, _, _, _ in data
            )
            nu = 64 * eps + 64 * q0
            ex = dsum(
                (norm2(fm).sqrt() * d + norm2(dc).sqrt() * em + d * em + nu * sx) ** 2
                for dc, _, _, fm, _, em in data
            ).sqrt()
            ey = dsum(
                (norm2(f0).sqrt() * d + norm2(cm).sqrt() * e0 + d * e0 + nu * sy) ** 2
                for _, cm, f0, _, e0, _ in data
            ).sqrt()
            a, b = ex / xn, ey / yn
            h = a + b
            gamma = 4096 * len(data) * eps + 128 * q0
            coherence = norm2(c).sqrt()
            assert h + gamma <= Decimal(1) / 64
            gain_error = (yn / xn) * (h * (2 * (1 + b) + coherence) + (1 + b) * gamma) / (
                1 - a
            ) + 8 * q0
            result.append(
                {
                    "gain": complex(float(beta[0]), float(beta[1])),
                    "relative_residual": float(residual),
                    "coherence": float(coherence),
                    "overlap_count": len(data),
                    "gain_budget": float(gain_error),
                    "residual_budget": float(4 * h + gamma),
                    "coherence_budget": float(2 * h + gamma),
                }
            )
        return result


def matched_case() -> tuple[Any, dict[str, Any]]:
    images, args = simple_case()
    images = np.concatenate((images, images[:, :, :1]), axis=2)
    shape = images.shape[1:]
    spacing = args["voxel_size_um"]
    axes = [
        np.array([float(Fraction(p, n) / Fraction(d)) for p in range(-(n // 2), (n + 1) // 2)])
        for n, d in zip(shape, spacing, strict=True)
    ]
    args["response"] = EmpiricalVolumeResponse(
        np.ones((3, *shape), dtype=complex), axes[0], axes[1], axes[2], spacing, (0, 0, 0)
    )
    return images, args


def singleton_gain_case(
    zero_transfer: complex, side_transfer: complex = 1 + 0j
) -> tuple[Any, dict[str, Any]]:
    _, args = simple_case()
    h = phase_matrix(args["phase_steps_rad"])
    images = (h @ np.array([1.0, 6.0, -8.0, 0.0, 0.0]))[:, None, None, None]
    values = np.array([zero_transfer, side_transfer, 1 + 0j], dtype=np.complex128).reshape(
        3, 1, 1, 1
    )
    args.update(
        response=EmpiricalVolumeResponse(
            values, np.array([0.0]), np.array([0.0]), np.array([0.0]), (1.0, 1.0, 1.0), (0, 0, 0)
        ),
        candidate_carriers_yx=[(0, 0)],
    )
    return images, args
