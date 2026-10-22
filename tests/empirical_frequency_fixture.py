"""Independent rational geometry and Decimal oracle for physical point queries.

No production helpers or production outputs define expectations. Units are cycles/um
for coordinates, um for spacings, and dimensionless complex response values.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from itertools import product
from typing import Any

import numpy as np

import simrecon

Array = np.ndarray[Any, Any]
Q0 = Fraction(1, 2**1074)
EPS = Fraction(1, 2**52)
FMAX = Fraction.from_float(float.fromhex("0x1.fffffffffffffp+1023"))


def rational(value: Any) -> Fraction:
    return Fraction.from_float(float(value))


def ideal_axes(shape: tuple[int, int, int], spacing: Any) -> list[list[Fraction]]:
    return [
        [Fraction(k, n) / rational(d) for k in range(-(n // 2), (n + 1) // 2)]
        for n, d in zip(shape, spacing, strict=True)
    ]


def affine_value(order: int, point: Any) -> tuple[Fraction, Fraction]:
    z, y, x = map(Fraction, point)
    return (
        Fraction(3 + order, 8)
        + z / 2
        - y / 4
        + x / 8
        + z * y / 16
        - y * x / 32
        + z * x / 64
        + z * y * x / 128,
        Fraction(2 - order, 16)
        - z / 8
        + y / 2
        - x / 4
        + z * y / 32
        + y * x / 16
        - z * x / 8
        + z * y * x / 64,
    )


def response(
    shape: tuple[int, int, int] = (3, 4, 5),
    spacing: Any = (0.5, 0.25, 0.125),
    origin: Any = (1, 2, 3),
    values: Array | None = None,
) -> Any:
    axes = ideal_axes(shape, spacing)
    if values is None:
        values = np.empty((3, *shape), dtype=np.complex128)
        for m, iz, iy, ix in product(range(3), *map(range, shape)):
            real, imag = affine_value(m, (axes[0][iz], axes[1][iy], axes[2][ix]))
            values[m, iz, iy, ix] = complex(float(real), float(imag))
    return simrecon.EmpiricalVolumeResponse(
        values=values,
        fz_per_um=np.array([float(v) for v in axes[0]], dtype=np.float64),
        fy_per_um=np.array([float(v) for v in axes[1]], dtype=np.float64),
        fx_per_um=np.array([float(v) for v in axes[2]], dtype=np.float64),
        voxel_size_um=spacing,
        origin_zyx=origin,
    )


def arguments(points: Array | None = None, **changes: Any) -> dict[str, Any]:
    result = {
        "order": 1,
        "frequencies_zyx_per_um": (
            np.array([[0.0, 0.0, 0.0]], dtype=np.float64) if points is None else points
        ),
        "calibration_carrier_bins": (0, 0),
        "coordinate_offset_yx": (0, 0),
        "phase_reference_shift_rad": 0.0,
        "source": " explicit physical pairing ",
    }
    result.update(changes)
    return result


def stencil(record: Any, point: Any, order: int) -> list[tuple[Fraction, complex]]:
    shape = record.values.shape[1:]
    axes = ideal_axes(shape, record.voxel_size_um)
    brackets: list[list[tuple[int, Fraction]]] = []
    for coordinate, nodes in zip(point, axes, strict=True):
        f = rational(coordinate) * (-1 if order < 0 else 1)
        if not nodes[0] <= f <= nodes[-1]:
            raise ValueError("oracle query outside ideal hull")
        if f in nodes:
            brackets.append([(nodes.index(f), Fraction(1))])
        else:
            lo = next(i for i in range(len(nodes) - 1) if nodes[i] < f < nodes[i + 1])
            t = (f - nodes[lo]) / (nodes[lo + 1] - nodes[lo])
            brackets.append([(lo, 1 - t), (lo + 1, t)])
    return [
        (wz * wy * wx, complex(record.values[abs(order), iz, iy, ix]))
        for (iz, wz), (iy, wy), (ix, wx) in product(*brackets)
    ]


def dec(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


@lru_cache(maxsize=1)
def pi_decimal() -> Decimal:
    """Machin's formula, independently computed to 450 decimal digits."""
    with localcontext() as ctx:
        ctx.prec = 460

        def atan_inverse(n: int) -> Decimal:
            x = Decimal(1) / n
            total = term = x
            j = 1
            while True:
                term *= -x * x
                updated = total + term / (2 * j + 1)
                if updated == total:
                    return total
                total = updated
                j += 1

        return +(16 * atan_inverse(5) - 4 * atan_inverse(239))


def sin_cos(angle: Decimal) -> tuple[Decimal, Decimal]:
    with localcontext() as ctx:
        ctx.prec = 440
        tau = 2 * pi_decimal()
        x = angle % tau
        if x > pi_decimal():
            x -= tau
        if x < -pi_decimal():
            x += tau
        sine = sin_term = x
        cosine = cos_term = Decimal(1)
        j = 1
        while True:
            sin_term *= -x * x / ((2 * j) * (2 * j + 1))
            cos_term *= -x * x / ((2 * j - 1) * (2 * j))
            new_sin, new_cos = sine + sin_term, cosine + cos_term
            if new_sin == sine and new_cos == cosine:
                return +sine, +cosine
            sine, cosine = new_sin, new_cos
            j += 1


def oracle(record: Any, point: Any, **kwargs: Any) -> tuple[Decimal, Decimal, Decimal]:
    """Return real, imaginary and the contract modulus allowance, without overflow."""
    order = int(kwargs["order"])
    terms = stencil(record, point, order)
    real = sum((w * rational(v.real) for w, v in terms), Fraction())
    imag = sum((w * rational(v.imag) for w, v in terms), Fraction())
    size = sum(
        (w * (abs(rational(v.real)) + abs(rational(v.imag))) for w, v in terms),
        Fraction(),
    )
    rho = (
        sum(
            (
                Fraction(int(k) * (int(b) + int(o)), n)
                for k, b, o, n in zip(
                    kwargs["calibration_carrier_bins"],
                    record.origin_zyx[1:],
                    kwargs["coordinate_offset_yx"],
                    record.values.shape[2:],
                    strict=True,
                )
            ),
            Fraction(),
        )
        % 1
    )
    with localcontext() as ctx:
        ctx.prec = 440
        r, i = dec(real), dec(imag)
        if order:
            angle = -abs(order) * (
                2 * pi_decimal() * dec(rho)
                + Decimal.from_float(float(kwargs["phase_reference_shift_rad"]))
            )
            sine, cosine = sin_cos(angle)
            r, i = r * cosine - i * sine, r * sine + i * cosine
        if order < 0:
            i = -i
        return +r, +i, dec(1024 * EPS * size + 64 * Q0)


def assert_accuracy(actual: Any, record: Any, points: Array, **kwargs: Any) -> None:
    with localcontext() as ctx:
        ctx.prec = 440
        for value, point in zip(actual, points, strict=True):
            expected_real, expected_imag, budget = oracle(record, point, **kwargs)
            dr = Decimal.from_float(float(value.real)) - expected_real
            di = Decimal.from_float(float(value.imag)) - expected_imag
            error = (dr * dr + di * di).sqrt()
            # Decimal oracle residual is <1e-120 relative even for max-float delta.
            # 440 digits also resolve minimum-subnormal values and their budgets.
            assert error <= budget, (value, expected_real, expected_imag, error, budget)


def component_bits(values: Array) -> Array:
    return np.ascontiguousarray(values, dtype=np.complex128).view(np.uint64).reshape(-1, 2)


def storage_variant(array: Array, kind: str) -> Array:
    if kind == "foreign":
        return array.astype(array.dtype.newbyteorder("S"))
    if kind == "fortran":
        return np.asfortranarray(array)
    if kind == "readonly":
        result = array.copy()
        result.flags.writeable = False
        return result
    if kind == "strided":
        enlarged = np.empty((*array.shape[:-1], array.shape[-1] * 2), dtype=array.dtype)
        enlarged[..., ::2] = array
        return enlarged[..., ::2]
    if kind == "reversed":
        return array[..., ::-1].copy()[..., ::-1]
    raise AssertionError(kind)


def exact_phase_coordinates(images: Array, phases: Array) -> list[list[list[Fraction]]]:
    """Exact least squares on the documented represented five-column matrix."""
    c, s = np.cos(phases), np.sin(phases)
    design = np.column_stack((np.ones(len(phases)), c, s, c * c - s * s, (2 * c) * s))
    h = [[rational(v) for v in row] for row in design]
    normal = [[sum((row[i] * row[j] for row in h), Fraction()) for j in range(5)] for i in range(5)]
    augmented = [normal[i] + [Fraction(i == j) for j in range(5)] for i in range(5)]
    for col in range(5):
        pivot = next(i for i in range(col, 5) if augmented[i][col])
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [x / scale for x in augmented[col]]
        for i in range(5):
            if i != col:
                scale = augmented[i][col]
                augmented[i] = [
                    a - scale * b for a, b in zip(augmented[i], augmented[col], strict=True)
                ]
    inverse = [row[5:] for row in augmented]
    results: list[list[list[Fraction]]] = [[], [], []]
    for voxel in np.ndindex(images.shape[1:]):
        observations = [rational(images[(p, *voxel)]) for p in range(len(phases))]
        rhs = [
            sum((row[j] * b for row, b in zip(h, observations, strict=True)), Fraction())
            for j in range(5)
        ]
        fit = [sum((a * b for a, b in zip(row, rhs, strict=True)), Fraction()) for row in inverse]
        results[0].append([fit[0], Fraction()])
        results[1].append([fit[1] / 2, -fit[2] / 2])
        results[2].append([fit[3] / 2, -fit[4] / 2])
    return results


def raw_bead_case(bead: tuple[int, int, int] = (1, 1, 2)) -> tuple[Array, Array, Any, Decimal]:
    """Independent point-bead generation and represented-fit/direct-DFT oracle.

    Kernel masses sum exactly to one. Equal scalar fields select g1=2*cos/3,
    g2=1/3; axial mode 1, lateral modes (1,1). Camera uses 10 count offset and
    2 count/electron response. No truth is supplied to calibration/sampling.
    """
    shape = (3, 3, 4)
    spacing = (0.5, 0.5, 0.25)
    h = np.zeros(shape)
    for idx, mass in [
        ((0, 0, 0), 0.5),
        ((1, 0, 0), 0.125),
        ((0, 1, 0), 0.125),
        ((2, 2, 3), 0.125),
        ((1, 2, 1), 0.125),
    ]:
        h[idx] = mass
    phases = np.array([0.0, 0.61, 1.72, 2.8, 3.75, 4.9, 5.65])
    harmonics = np.empty((3, *shape), dtype=np.complex128)
    with localcontext() as ctx:
        ctx.prec = 120
        for idx in np.ndindex(shape):
            rho = Fraction(bead[1], shape[1]) + Fraction(bead[2], shape[2])
            for m in (0, 1, 2):
                g = (
                    Fraction(1)
                    if m == 0
                    else (Fraction(2 if idx[0] == 0 else -1, 3) if m == 1 else Fraction(1, 3))
                )
                sine, cosine = sin_cos(2 * pi_decimal() * dec(m * rho))
                amplitude = 128 * rational(h[idx]) * g
                dst = tuple((u + b) % n for u, b, n in zip(idx, bead, shape, strict=True))
                harmonics[(m, *dst)] = complex(
                    float(dec(amplitude) * cosine), float(dec(amplitude) * sine)
                )
    c, s = np.cos(phases), np.sin(phases)
    c2, s2 = c * c - s * s, (2 * c) * s
    exposures = np.array(
        [
            harmonics[0].real
            + 2 * harmonics[1].real * cp
            - 2 * harmonics[1].imag * sp
            + 2 * harmonics[2].real * c2p
            - 2 * harmonics[2].imag * s2p
            for cp, sp, c2p, s2p in zip(c, s, c2, s2, strict=True)
        ]
    )
    raw = 10.0 + 2.0 * exposures
    converted = (raw - 10.0) / 2.0
    coords = exact_phase_coordinates(converted, phases)
    mass = sum((v[0] for v in coords[0]), Fraction())
    assert mass > 0
    voxels = list(np.ndindex(shape))
    observed = max(range(len(voxels)), key=lambda j: coords[0][j][0])
    assert voxels[observed] == bead
    expected = np.empty((3, *shape), dtype=np.complex128)
    with localcontext() as ctx:
        ctx.prec = 120
        for m in range(3):
            for loc in np.ndindex(shape):
                mode = tuple(j - n // 2 for j, n in zip(loc, shape, strict=True))
                rr = ii = Decimal(0)
                for voxel, (real, imag) in zip(voxels, coords[m], strict=True):
                    rho = (
                        sum(
                            (
                                Fraction(k * ((u - b) % n), n)
                                for k, u, b, n in zip(mode, voxel, bead, shape, strict=True)
                            ),
                            Fraction(),
                        )
                        % 1
                    )
                    sine, cosine = sin_cos(-2 * pi_decimal() * dec(rho))
                    rr += dec(real) * cosine - dec(imag) * sine
                    ii += dec(real) * sine + dec(imag) * cosine
                expected[(m, *loc)] = complex(float(rr / dec(mass)), float(ii / dec(mass)))
        expected[0, 1, 1, 2] = 1.0
        # Per-real-coordinate separation budget, propagated through the exact
        # common mass and DFT. Lambda<=2 here; 2*e covers complex coordinate norm.
        e = 8192 * len(phases) * EPS * max(map(rational, abs(converted).flat)) + 8 * Q0
        count = math_product(shape)
        denominator = mass - count * e
        assert denominator > 0
        source_budget = (
            3 * count * e / denominator
            + 512 * count * EPS * 2
            + 16 * count * Q0
            + Fraction(1, 10**15)
        )
        # Peak margin protects origin under all permitted separator errors.
        peaks = sorted((v[0] for v in coords[0]), reverse=True)
        assert peaks[0] - peaks[1] > 2 * e
        return raw[np.newaxis], phases, response(shape, spacing, bead, expected), dec(source_budget)


def math_product(values: Any) -> int:
    result = 1
    for v in values:
        result *= int(v)
    return result
