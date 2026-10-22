"""Independent stored-input observers; no production transforms or solver oracle.

Decimal precision includes >100 guard digits after reducing binary64-max angles.
The phase matrix alone uses the contract's explicitly represented NumPy operations.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache, lru_cache
from itertools import product
from typing import Any

import numpy as np
from numpy.typing import NDArray

from simrecon import EmpiricalVolumeResponse

PRECISION = 440
D = Decimal
EPS = D.from_float(float.fromhex("0x1p-52"))
Q = D.from_float(float.fromhex("0x0.0000000000001p-1022"))
FIELDS = (
    "values",
    "fz_per_um",
    "fy_per_um",
    "fx_per_um",
    "voxel_size_um",
    "origin_zyx",
)
Complex = tuple[Decimal, Decimal]
Array = NDArray[Any]


def represented(value: Any) -> Decimal:
    return D.from_float(float(value))


def pair(value: Any) -> Complex:
    if isinstance(value, tuple):
        return value
    return represented(value.real), represented(value.imag)


def add(a: Complex, b: Complex) -> Complex:
    return a[0] + b[0], a[1] + b[1]


def multiply(a: Complex, b: Complex) -> Complex:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def conjugate(a: Complex) -> Complex:
    return a[0], -a[1]


def arctan_inverse(n: int) -> Decimal:
    x = D(1) / n
    term = x
    total = x
    k = 1
    while True:
        term *= -x * x
        revised = total + term / (2 * k + 1)
        if revised == total:
            return total
        total = revised
        k += 1


@lru_cache(maxsize=1)
def pi() -> Decimal:
    with localcontext() as ctx:
        ctx.prec = PRECISION + 20
        return 16 * arctan_inverse(5) - 4 * arctan_inverse(239)


@cache
def root(cycles: Fraction, delta: float = 0.0) -> Complex:
    """exp(i*(2*pi*cycles+converted delta)), exact quarter roots when possible."""
    cycles %= 1
    quarters = cycles * 4
    if delta == 0 and quarters.denominator == 1:
        return ((D(1), D(0)), (D(0), D(1)), (D(-1), D(0)), (D(0), D(-1)))[int(quarters) % 4]
    with localcontext() as ctx:
        ctx.prec = PRECISION
        period = 2 * pi()
        x = period * D(cycles.numerator) / cycles.denominator + represented(delta)
        x %= period
        if x > pi():
            x -= period
        if x < -pi():
            x += period
        xx = x * x
        cosine, sine = D(1), x
        ct, st = cosine, sine
        k = 1
        while True:
            ct *= -xx / ((2 * k - 1) * (2 * k))
            st *= -xx / ((2 * k) * (2 * k + 1))
            nc, ns = cosine + ct, sine + st
            if (nc, ns) == (cosine, sine):
                return nc, ns
            cosine, sine = nc, ns
            k += 1


def modes(size: int) -> tuple[int, ...]:
    return tuple(range(-(size // 2), (size + 1) // 2))


def grid(size: int, spacing: Any) -> Array:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        return np.array(
            [float(D(k) / (size * represented(spacing))) for k in modes(size)],
            dtype=np.float64,
        )


def record(**changes: Any) -> EmpiricalVolumeResponse:
    values = changes.pop("values", None)
    if values is None:
        labels = np.arange(72, dtype=np.float64).reshape(3, 2, 3, 4)
        values = ((labels % 11 - 5) / 8 + 1j * (labels % 7 - 3) / 16).astype(np.complex128)
    shape = values.shape[-3:] if values.ndim >= 3 else (2, 3, 4)
    spacing = changes.pop("voxel_size_um", (0.25, 0.5, 0.125))
    fields: dict[str, Any] = {
        "values": values,
        "fz_per_um": grid(shape[0], 0.25),
        "fy_per_um": grid(shape[1], 0.5),
        "fx_per_um": grid(shape[2], 0.125),
        "voxel_size_um": spacing,
        "origin_zyx": (min(1, shape[0] - 1), min(2, shape[1] - 1), shape[2] - 1),
    }
    fields.update(changes)
    return EmpiricalVolumeResponse(**fields)


def revised(response: Any, **changes: Any) -> EmpiricalVolumeResponse:
    fields = {name: getattr(response, name) for name in FIELDS}
    fields.update(changes)
    return EmpiricalVolumeResponse(**fields)


def rotation(
    response: Any, carrier: Any, offset: Any, delta: Any
) -> dict[tuple[int, ...], Complex]:
    ny, nx = response.values.shape[-2:]
    rho = Fraction(int(carrier[0]) * (int(response.origin_zyx[1]) + int(offset[0])), ny)
    rho += Fraction(int(carrier[1]) * (int(response.origin_zyx[2]) + int(offset[1])), nx)
    # Keep order-two delta multiplication in Decimal, not overflowing binary64.
    with localcontext() as ctx:
        ctx.prec = PRECISION
        fundamental = root(-rho, -float(delta))
        phasors = ((D(1), D(0)), fundamental, multiply(fundamental, fundamental))
        return {
            index: multiply(pair(response.values[index]), phasors[index[0]])
            for index in np.ndindex(response.values.shape)
        }


def assert_rotation(result: Any, response: Any, carrier: Any, offset: Any, delta: Any):
    expected = rotation(response, carrier, offset, delta)
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index, target in expected.items():
            if index[0] == 0:
                continue
            re, im = pair(response.values[index])
            budget = 128 * EPS * (abs(re) + abs(im)) + 16 * Q
            assert_close(result.values[index], target, budget, f"rotation {index}")
    original = np.array(response.values[0], dtype=np.complex128, order="C")
    assert result.values[0].tobytes() == original.tobytes(), "order zero bitwise copy"


def assert_close(value: Any, expected: Complex, budget: Decimal, label: str):
    with localcontext() as ctx:
        ctx.prec = PRECISION
        actual = pair(value)
        error_squared = (actual[0] - expected[0]) ** 2 + (actual[1] - expected[1]) ** 2
        assert error_squared <= budget * budget, (
            f"{label}: squared complex error {error_squared} exceeds budget² {budget * budget}"
        )


def direct_dft(values: Any, origin=(0, 0, 0), normalized=False):
    """Negative-exponent finite sum on native centered modes, no FFT."""
    shape = values.shape
    result: dict[tuple[int, ...], Complex] = {}
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for index in np.ndindex(shape):
            mode = tuple(modes(n)[i] for n, i in zip(shape, index, strict=True))
            total = D(0), D(0)
            for coordinate in np.ndindex(shape):
                phase = sum(
                    (
                        Fraction(k * (x - o), n)
                        for k, x, o, n in zip(mode, coordinate, origin, shape, strict=True)
                    ),
                    Fraction(),
                )
                total = add(total, multiply(pair(values[coordinate]), root(-phase)))
            if normalized:
                count = int(np.prod(shape))
                total = total[0] / count, total[1] / count
            result[index] = total
    return result


def represented_basis(phases: Array) -> Array:
    p = np.asarray(phases, dtype=np.float64)
    c, s = np.cos(p), np.sin(p)
    return np.column_stack((np.ones(p.size), c, s, c * c - s * s, (2 * c) * s))


def exact_separation(images: Array, phases: Array) -> tuple[Array, Array, Array]:
    """High-precision normal equations are an observer, never a product solver."""
    basis = represented_basis(phases)
    shape = images.shape[1:]
    outputs = tuple(np.empty(shape, dtype=object) for _ in range(3))
    with localcontext() as ctx:
        ctx.prec = PRECISION
        h = [[represented(x) for x in row] for row in basis]
        gram = [[sum((row[i] * row[j] for row in h), D(0)) for j in range(5)] for i in range(5)]
        for index in np.ndindex(shape):
            b = [represented(images[(p, *index)]) for p in range(images.shape[0])]
            rhs = [sum((row[i] * y for row, y in zip(h, b, strict=True)), D(0)) for i in range(5)]
            augmented = [row.copy() + [y] for row, y in zip(gram, rhs, strict=True)]
            for column in range(5):
                pivot = max(range(column, 5), key=lambda row: abs(augmented[row][column]))
                augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
                scale = augmented[column][column]
                assert scale != 0, "oracle phase matrix must identify five columns"
                augmented[column] = [x / scale for x in augmented[column]]
                for row in range(5):
                    if row != column:
                        scale = augmented[row][column]
                        augmented[row] = [
                            a - scale * b
                            for a, b in zip(augmented[row], augmented[column], strict=True)
                        ]
            x = [row[-1] for row in augmented]
            outputs[0][index] = (x[0], D(0))
            outputs[1][index] = (x[1] / 2, -x[2] / 2)
            outputs[2][index] = (x[3] / 2, -x[4] / 2)
    return outputs[0], outputs[1], outputs[2]


def exposures(dc: Any, c1: Any, c2: Any, phases: Array) -> Array:
    h = represented_basis(phases)
    coefficients = np.stack((dc.real, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag))
    return np.einsum("pj,jzyx->pzyx", h, coefficients)


def estimator(
    images: Array,
    phases: Array,
    transfers: Array,
    carrier: tuple[int, int],
    gain: float,
    ridge: float,
    mask: Array,
):
    """Independent five-band estimator, modular negation, nonwrapping placement."""
    components = exact_separation(images, phases)
    negative = tuple(np.empty(images.shape[1:], dtype=object) for _ in range(2))
    for index in np.ndindex(images.shape[1:]):
        negative[0][index] = conjugate(pair(components[2][index]))
        negative[1][index] = conjugate(pair(components[1][index]))
    bands = [negative[0], negative[1], *components]
    transforms = [direct_dft(band, normalized=True) for band in bands]
    shape = images.shape[1:]
    out_shape = mask.shape
    output: dict[tuple[int, ...], Complex] = {}
    with localcontext() as ctx:
        ctx.prec = PRECISION
        for out_index in np.ndindex(out_shape):
            qmode = tuple(modes(n)[i] for n, i in zip(out_shape, out_index, strict=True))
            numerator, denominator = (D(0), D(0)), represented(ridge)
            for m in range(-2, 3):
                jmode = (qmode[0], qmode[1] + m * carrier[0], qmode[2] + m * carrier[1])
                if any(k not in modes(n) for k, n in zip(jmode, shape, strict=True)):
                    continue
                jindex = tuple(modes(n).index(k) for k, n in zip(jmode, shape, strict=True))
                if m < 0:
                    neg = tuple(
                        modes(n).index((-k + n // 2) % n - n // 2)
                        for k, n in zip(jmode, shape, strict=True)
                    )
                    transfer = conjugate(pair(transfers[(abs(m), *neg)]))
                else:
                    transfer = pair(transfers[(m, *jindex)])
                t = transfer[0] * represented(gain), transfer[1] * represented(gain)
                numerator = add(numerator, multiply(conjugate(t), transforms[m + 2][jindex]))
                denominator += t[0] ** 2 + t[1] ** 2
            scale = represented(mask[out_index]) / denominator if denominator > 0 else D(0)
            output[out_index] = numerator[0] * scale, numerator[1] * scale
        volume: dict[tuple[int, ...], Complex] = {}
        for coordinate in np.ndindex(out_shape):
            total = D(0), D(0)
            for index, value in output.items():
                phase = sum(
                    (
                        Fraction(modes(n)[i] * x, n)
                        for n, i, x in zip(out_shape, index, coordinate, strict=True)
                    ),
                    Fraction(),
                )
                total = add(total, multiply(value, root(phase)))
            volume[coordinate] = total
    return output, volume


def point_model(shape=(2, 3, 4), bead=(1, 2, 3), brightness=16.0):
    """Asymmetric admissible detection with independent generator truth."""
    count = int(np.prod(shape))
    base = 1 / (8 * 2 ** (count - 1).bit_length())
    h = np.full(shape, base, dtype=np.float64)
    h[0, 0, 0] = 0.75
    remaining = 0.25 - (count - 1) * base
    h[tuple((1 % shape[0], 1 % shape[1], 1 % shape[2]))] += remaining / 2
    h[tuple((0, 1 % shape[1], 2 % shape[2]))] += remaining / 2
    a0, ap, am = 1 + 0j, 0.5 + 0.25j, 0.25 - 0.125j
    power = abs(a0) ** 2 + abs(ap) ** 2 + abs(am) ** 2
    g1 = np.empty(shape[0], dtype=np.complex128)
    for z in range(shape[0]):
        phase = complex(*map(float, root(Fraction(z, shape[0]))))
        g1[z] = (ap * a0.conjugate() * phase.conjugate() + a0 * am.conjugate() * phase) / power
    g2 = ap * am.conjugate() / power
    kernels = (h, h * g1[:, None, None], h * g2)
    # Generator carrier is (1,-1). It enters raw exposures, never calibration.
    bead_phase = root(Fraction(bead[1], shape[1]) - Fraction(bead[2], shape[2]))
    ph = complex(*map(float, bead_phase))
    components = tuple(
        brightness * np.roll(kernel, bead, axis=(0, 1, 2)) * ph**m
        for m, kernel in enumerate(kernels)
    )
    return h, kernels, (components[0], components[1], components[2])


def forward_specimen(kernels: Any, specimen: Array, carrier=(1, -1), gain=1.25):
    shape = specimen.shape
    components = tuple(np.zeros(shape, dtype=np.complex128) for _ in range(3))
    for coordinate in product(*(range(n) for n in shape)):
        ph = complex(
            *map(
                float,
                root(
                    Fraction(carrier[0] * coordinate[1], shape[1])
                    + Fraction(carrier[1] * coordinate[2], shape[2])
                ),
            )
        )
        for m, kernel in enumerate(kernels):
            components[m][:] += (
                gain * specimen[coordinate] * ph**m * np.roll(kernel, coordinate, axis=(0, 1, 2))
            )
    return components[0], components[1], components[2]
