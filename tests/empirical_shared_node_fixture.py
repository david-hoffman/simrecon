"""Independent exact geometry, decimal arithmetic and finite physical generators.

No product implementation or existing test helper is used here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from itertools import product
from typing import Any, cast

import numpy as np


@lru_cache
def pi(precision: int = 420) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = precision + 16

        def atan_inverse(n: int) -> Decimal:
            x = Decimal(1) / n
            power = x
            total = x
            for k in range(1, precision * 2):
                power *= -x * x
                term = power / (2 * k + 1)
                total += term
                if abs(term) < Decimal(10) ** (-precision - 8):
                    break
            return total

        return +(16 * atan_inverse(5) - 4 * atan_inverse(239))


def sincos(angle: Decimal) -> tuple[Decimal, Decimal]:
    """Mathematical trig, reduced using precision far beyond binary64 inputs."""
    tau = 2 * pi()
    x = angle % tau
    if x > pi():
        x -= tau
    if x < -pi():
        x += tau
    sine = term_s = x
    cosine = term_c = Decimal(1)
    for k in range(1, 1800):
        term_s *= -x * x / ((2 * k) * (2 * k + 1))
        term_c *= -x * x / ((2 * k - 1) * (2 * k))
        sine += term_s
        cosine += term_c
        if max(abs(term_s), abs(term_c)) < Decimal(10) ** (-410):
            break
    return sine, cosine


def modes(n: int) -> tuple[int, ...]:
    return tuple(range(-(n // 2), (n + 1) // 2))


def indices(nc: int, dc: float, ns: int, ds: float) -> tuple[int, ...]:
    ratio = nc * Fraction(float(dc)) / (ns * Fraction(float(ds)))
    result = tuple(Fraction(j) * ratio for j in modes(ns))
    if any(i.denominator != 1 or int(i) not in modes(nc) for i in result):
        raise ValueError("missing exact node")
    return tuple(int(i) + nc // 2 for i in result)


def negation(n: int, k: int) -> int:
    return (-k + n // 2) % n - n // 2


def coordinates(n: int, spacing: float) -> np.ndarray:
    return np.array([float(Fraction(k, n) / Fraction(float(spacing))) for k in modes(n)])


def response(
    api: Any,
    shape: tuple[int, ...] = (3, 5, 7),
    spacing: tuple[float, ...] = (0.5, 0.25, 0.125),
    origin: tuple[int, int, int] | None = None,
) -> Any:
    count = 3 * math.prod(shape)
    t = np.arange(count, dtype=np.float64).reshape((3, *shape))
    values = (t - count / 3) / 32 + 1j * ((t % 11) - 4) / 16
    return api.EmpiricalVolumeResponse(
        values=values,
        fz_per_um=coordinates(shape[0], spacing[0]),
        fy_per_um=coordinates(shape[1], spacing[1]),
        fx_per_um=coordinates(shape[2], spacing[2]),
        voxel_size_um=spacing,
        origin_zyx=origin or tuple(n - 1 for n in shape),
    )


def selected(record: Any, shape: tuple[int, int, int], spacing: Any) -> np.ndarray:
    maps = tuple(
        indices(nc, dc, ns, ds)
        for nc, dc, ns, ds in zip(
            record.values.shape[1:], record.voxel_size_um, shape, spacing, strict=True
        )
    )
    return record.values[np.ix_(range(3), *maps)]


def rotated(
    value: complex, order: int, rho: Fraction, delta: float
) -> tuple[Decimal, Decimal, Decimal]:
    with localcontext() as ctx:
        ctx.prec = 420
        reduced = rho % 1
        angle = -order * (
            2 * pi() * Decimal(reduced.numerator) / Decimal(reduced.denominator)
            + Decimal.from_float(float(delta))
        )
        sine, cosine = sincos(angle)
        real = Decimal.from_float(float(value.real))
        imag = Decimal.from_float(float(value.imag))
        budget = 128 * Decimal(2) ** -52 * (abs(real) + abs(imag))
        budget += 16 * Decimal(2) ** -1074
        return real * cosine - imag * sine, real * sine + imag * cosine, budget


def assert_rotation(actual: np.ndarray, expected: np.ndarray, rho: Fraction, delta: float) -> None:
    for order in (1, 2):
        for index in np.ndindex(expected.shape[1:]):
            value = actual[(order, *index)]
            re, im, budget = rotated(expected[(order, *index)], order, rho, delta)
            with localcontext() as ctx:
                ctx.prec = 420
                error2 = (Decimal.from_float(float(value.real)) - re) ** 2
                error2 += (Decimal.from_float(float(value.imag)) - im) ** 2
                assert error2 <= budget**2


def component_bits(array: np.ndarray) -> np.ndarray:
    dtype = np.complex128 if array.dtype.kind == "c" else np.float64
    return np.array(array, dtype=dtype, order="C").view(np.uint64)


def phase_basis(phases: np.ndarray) -> np.ndarray:
    c = np.cos(phases)
    s = np.sin(phases)
    return np.column_stack((np.ones(len(phases)), c, s, c * c - s * s, (2 * c) * s))


@dataclass(frozen=True)
class Z:
    """Small decimal complex number for an independent stored-input estimator."""

    re: Decimal = Decimal(0)
    im: Decimal = Decimal(0)

    def __add__(self, other: Z) -> Z:
        """Add real and imaginary components."""
        return Z(self.re + other.re, self.im + other.im)

    def __sub__(self, other: Z) -> Z:
        """Subtract real and imaginary components."""
        return Z(self.re - other.re, self.im - other.im)

    def __mul__(self, other: Z) -> Z:
        """Multiply without binary floating intermediates."""
        return Z(self.re * other.re - self.im * other.im, self.re * other.im + self.im * other.re)

    def scale(self, value: Decimal) -> Z:
        return Z(self.re * value, self.im * value)

    def conj(self) -> Z:
        return Z(self.re, -self.im)

    @classmethod
    def stored(cls, value: complex | float) -> Z:
        return cls(Decimal.from_float(float(value.real)), Decimal.from_float(float(value.imag)))

    def native(self) -> complex:
        return complex(float(self.re), float(self.im))


@lru_cache
def roots(n: int, positive: bool = False) -> tuple[Z, ...]:
    result = []
    with localcontext() as ctx:
        ctx.prec = 420
        for k in range(n):
            s, c = sincos((1 if positive else -1) * 2 * pi() * k / n)
            result.append(Z(c, s))
    return tuple(result)


def decimal_dft(values: np.ndarray, *, inverse: bool = False) -> np.ndarray:
    """Separable direct sums, without using a production FFT or reconstruction."""
    work = np.empty(values.shape, dtype=object)
    for index in np.ndindex(values.shape):
        v: Any = values[index]
        work[index] = v if isinstance(v, Z) else Z.stored(v)
    for axis, n in enumerate(values.shape):
        out = np.empty_like(work)
        roots_n = roots(n, inverse)
        for rest in np.ndindex(*(values.shape[a] for a in range(3) if a != axis)):
            for k in range(n):
                total = Z()
                for j in range(n):
                    idx = list(rest)
                    idx.insert(axis, j)
                    total = total + work[tuple(idx)] * roots_n[(k * j) % n]
                idx = list(rest)
                idx.insert(axis, k)
                out[tuple(idx)] = total
        work = out
    return work


def decimal_components(images: np.ndarray, phases: np.ndarray) -> list[np.ndarray]:
    """Exact represented five-exposure linear solve, with 70 decimal digits."""
    basis = phase_basis(phases)
    matrix = [[Decimal.from_float(float(x)) for x in row] for row in basis]
    inverse = [[Decimal(int(i == j)) for j in range(5)] for i in range(5)]
    for col in range(5):
        pivot = max(range(col, 5), key=lambda i: abs(matrix[i][col]))
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        inverse[col], inverse[pivot] = inverse[pivot], inverse[col]
        divisor = matrix[col][col]
        matrix[col] = [x / divisor for x in matrix[col]]
        inverse[col] = [x / divisor for x in inverse[col]]
        for row in range(5):
            if row != col:
                factor = matrix[row][col]
                matrix[row] = [
                    x - factor * y for x, y in zip(matrix[row], matrix[col], strict=True)
                ]
                inverse[row] = [
                    x - factor * y for x, y in zip(inverse[row], inverse[col], strict=True)
                ]
    components = [np.empty(images.shape[1:], dtype=object) for _ in range(3)]
    for index in np.ndindex(images.shape[1:]):
        b = [Decimal.from_float(float(images[(p, *index)])) for p in range(5)]
        v = [sum((a * x for a, x in zip(row, b, strict=True)), Decimal(0)) for row in inverse]
        components[0][index] = Z(v[0])
        components[1][index] = Z(v[1] / 2, -v[2] / 2)
        components[2][index] = Z(v[3] / 2, -v[4] / 2)
    return components


def empirical_expected(
    components: tuple[np.ndarray, np.ndarray, np.ndarray],
    origin: tuple[int, ...],
    target_shape: tuple[int, ...],
) -> tuple[np.ndarray, tuple[float, ...]]:
    """Direct selected-mode DFT of exact stored components and exact dc mass.

    This oracle uses public separated inputs, not an empirical or adapter output.
    It is separate from the generator-model comparison and separator error.
    """
    with localcontext() as ctx:
        ctx.prec = 70
        mass = sum((Decimal.from_float(float(x)) for x in components[0].flat), Decimal())
        size = math.prod(components[0].shape)
        expected = np.empty((3, *target_shape), complex)
        allowances = []
        for m, values in enumerate(components):
            work = np.empty(values.shape, object)
            total = Decimal()
            for index in np.ndindex(values.shape):
                scalar: Any = values[index]
                value = Z.stored(scalar)
                total += abs(value.re) + abs(value.im)
                work[index] = value
            work = np.roll(work, tuple(-b for b in origin), axis=(0, 1, 2))
            for axis, n in enumerate(values.shape):
                out_shape = list(work.shape)
                out_shape[axis] = target_shape[axis]
                out = np.empty(out_shape, object)
                axis_roots = roots(n)
                for rest in np.ndindex(*(work.shape[a] for a in range(3) if a != axis)):
                    for ki, k in enumerate(modes(target_shape[axis])):
                        result = Z()
                        for j in range(n):
                            idx = list(rest)
                            idx.insert(axis, j)
                            result = result + work[tuple(idx)] * axis_roots[(k * j) % n]
                        idx = list(rest)
                        idx.insert(axis, ki)
                        out[tuple(idx)] = result
                work = out
            for index in np.ndindex(target_shape):
                value = cast(Z, work[index]).scale(1 / mass)
                expected[(m, *index)] = value.native()
            bound = 512 * size * Decimal(2) ** -52 * total / mass
            bound += 16 * size * Decimal(2) ** -1074
            allowances.append(float(bound))
        expected[(0, *(n // 2 for n in target_shape))] = 1 + 0j
        return expected, tuple(allowances)


def estimator(
    images: np.ndarray,
    phases: np.ndarray,
    transfers: np.ndarray,
    carrier: tuple[int, int],
    gain: float,
    ridge: float,
    mask: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """VR equations on stored inputs; decimal solve, direct DFT and synthesis."""
    with localcontext() as ctx:
        ctx.prec = 70
        shape = images.shape[1:]
        count = Decimal(math.prod(shape))
        components = decimal_components(images, phases)
        bands = {m: decimal_dft(components[m]) for m in (0, 1, 2)}
        bands[-1] = decimal_dft(np.vectorize(lambda z: z.conj(), otypes=[object])(components[1]))
        bands[-2] = decimal_dft(np.vectorize(lambda z: z.conj(), otypes=[object])(components[2]))
        output = mask.shape
        spectrum = np.empty(output, dtype=object)
        for oi in np.ndindex(output):
            q = tuple(i - n // 2 for i, n in zip(oi, output, strict=True))
            numerator = Z()
            denominator = Decimal.from_float(ridge)
            for m in (-2, -1, 0, 1, 2):
                j = (q[0], q[1] + m * carrier[0], q[2] + m * carrier[1])
                if not all(k in modes(n) for k, n in zip(j, shape, strict=True)):
                    continue
                ti = tuple(k + n // 2 for k, n in zip(j, shape, strict=True))
                if m < 0:
                    ni = tuple(negation(n, k) + n // 2 for k, n in zip(j, shape, strict=True))
                    transfer = Z.stored(transfers[(-m, *ni)]).conj()
                else:
                    transfer = Z.stored(transfers[(m, *ti)])
                t = transfer.scale(Decimal.from_float(gain))
                bi = tuple(k % n for k, n in zip(j, shape, strict=True))
                d = cast(Z, bands[m][bi]).scale(1 / count)
                numerator = numerator + t.conj() * d
                denominator += t.re * t.re + t.im * t.im
            spectrum[oi] = (
                numerator.scale(Decimal.from_float(float(mask[oi])) / denominator)
                if denominator
                else Z()
            )
        unshifted = np.roll(spectrum, tuple(-(n // 2) for n in output), axis=(0, 1, 2))
        volume = decimal_dft(unshifted, inverse=True)
        convert = np.vectorize(lambda z: z.native(), otypes=[np.complex128])
        return convert(spectrum), convert(volume)


def kernel(shape: tuple[int, int, int], *, unequal: bool = False) -> np.ndarray:
    """Finite polynomial with positive samples, unit mass and unique zero peak."""
    result = np.ones(shape)
    for axis, n in enumerate(shape):
        theta = 2 * np.pi * np.arange(n) / n
        a = 0.375 if unequal and axis == 2 else 0.25
        factor = 1 + a * np.cos(theta) + np.sin(theta) * (1 - np.cos(theta)) / 16
        view = [1, 1, 1]
        view[axis] = n
        result *= factor.reshape(view) / n
    return result


def physical_bead(
    shape: tuple[int, int, int],
    bead: tuple[int, int, int],
    brightness: float,
    offset: tuple[int, int],
    phases: np.ndarray,
) -> np.ndarray:
    h = kernel(shape)
    displacement = np.indices(shape)
    dz = (displacement[0] - bead[0]) % shape[0]
    hy = (displacement[1] - bead[1]) % shape[1]
    hx = (displacement[2] - bead[2]) % shape[2]
    h_shift = h[dz, hy, hx]
    theta = 2 * np.pi * (bead[2] + offset[1]) / shape[2]
    field_z = np.exp(2j * np.pi * dz / shape[0])
    return np.array(
        [
            brightness
            * h_shift
            * abs(field_z + np.exp(1j * (theta + p)) + np.exp(-1j * (theta + p))) ** 2
            / 3
            for p in phases
        ]
    )


def physical_specimen(
    shape: tuple[int, int, int], phases: np.ndarray, *, unequal: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Raw signal from emitting-site squared fields, without seeding transfers."""
    grid = np.indices(shape)
    specimen = np.asarray(1 + sum(np.cos(2 * np.pi * grid[a] / shape[a]) for a in range(3)) / 8)
    h = kernel(shape, unequal=unequal)
    images = np.zeros((len(phases), *shape))
    for site in product(*(range(n) for n in shape)):
        delta = tuple((grid[a] - site[a]) % shape[a] for a in range(3))
        shifted = h[delta]
        field_z = np.exp(2j * np.pi * delta[0] / shape[0])
        theta = 2 * np.pi * site[2] / shape[2]
        for p, phi in enumerate(phases):
            intensity = (
                abs(field_z + np.exp(1j * (theta + phi)) + np.exp(-1j * (theta + phi))) ** 2 / 3
            )
            images[p] += specimen[site] * shifted * intensity
    return images, specimen


def polynomial_transfer(shape: tuple[int, int, int], alpha: float = 0.0) -> np.ndarray:
    """Analytic Fourier coefficients of h*g_m, independent of raw calibration."""
    # sin(theta)*(1-cos(theta))/16 = sin(theta)/16 - sin(2theta)/32.
    coefficients = {0: 1 + 0j, 1: 1 / 8 - 1j / 32, -1: 1 / 8 + 1j / 32, 2: 1j / 64, -2: -1j / 64}
    result = np.zeros((3, *shape), dtype=np.complex128)
    for index in np.ndindex(shape):
        z, y, x = (i - n // 2 for i, n in zip(index, shape, strict=True))
        lateral = coefficients.get(y, 0) * coefficients.get(x, 0)
        hz = coefficients.get(z, 0)
        result[(0, *index)] = hz * lateral
        result[(1, *index)] = (
            (coefficients.get(z - 1, 0) + coefficients.get(z + 1, 0))
            * lateral
            * np.exp(-1j * alpha)
            / 3
        )
        result[(2, *index)] = hz * lateral * np.exp(-2j * alpha) / 3
    return result


def discrete_forward(
    specimen: np.ndarray, h: np.ndarray, carrier_x: int, phases: np.ndarray
) -> np.ndarray:
    """Direct emitting-site squared-field sums for sparse even-subset kernels."""
    shape = specimen.shape
    grid = np.indices(shape)
    result = np.zeros((len(phases), *shape))
    for site in np.ndindex(shape):
        if specimen[site] == 0:
            continue
        displacement = tuple((grid[a] - site[a]) % shape[a] for a in range(3))
        shifted = h[displacement]
        field = np.exp(2j * np.pi * displacement[0] / shape[0])
        theta = 2 * np.pi * carrier_x * site[2] / shape[2]
        for p, phi in enumerate(phases):
            result[p] += (
                specimen[site]
                * shifted
                * abs(field + np.exp(1j * (theta + phi)) + np.exp(-1j * (theta + phi))) ** 2
                / 3
            )
    return result
