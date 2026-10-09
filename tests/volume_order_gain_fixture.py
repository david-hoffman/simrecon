"""Independent represented-data and finite-sum observers for volume-order gain.

No product numerical routine supplies an expected value. Least squares uses
exact rational arithmetic on native represented phase entries and stored data.
Fourier roots, regression, norms and budgets use 80-digit Decimal arithmetic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
from typing import Any

import numpy as np

Array = np.ndarray[Any, Any]
Mode = tuple[int, int, int]
PI = Decimal(
    "3.1415926535897932384626433832795028841971693993751058209749445923078164062862"
    "089986280348253421170679"
)
EPS = Decimal.from_float(2.0**-52)
QUANTUM = Decimal.from_float(math.ldexp(1.0, -1074))


def dec(value: Any) -> Decimal:
    return Decimal.from_float(float(value))


@dataclass(frozen=True)
class Z:
    """Complex observer value with independent Decimal components."""

    real: Decimal
    imag: Decimal = Decimal(0)

    def __add__(self, other: Z) -> Z:
        """Add independent real and imaginary components."""
        return Z(self.real + other.real, self.imag + other.imag)

    def __sub__(self, other: Z) -> Z:
        """Subtract independent real and imaginary components."""
        return Z(self.real - other.real, self.imag - other.imag)

    def __mul__(self, other: Z) -> Z:
        """Multiply using Decimal component arithmetic."""
        return Z(
            self.real * other.real - self.imag * other.imag,
            self.real * other.imag + self.imag * other.real,
        )

    def scale(self, factor: Decimal) -> Z:
        return Z(self.real * factor, self.imag * factor)

    def conj(self) -> Z:
        return Z(self.real, -self.imag)

    def square(self) -> Decimal:
        return self.real * self.real + self.imag * self.imag

    def modulus(self) -> Decimal:
        return self.square().sqrt()

    def native(self) -> complex:
        return complex(float(self.real), float(self.imag))


def z(value: Any) -> Z:
    return Z(dec(np.real(value)), dec(np.imag(value)))


def root(turns: Fraction) -> Z:
    """Evaluate exp(2*pi*i*turns), with exact quarter-turn roots."""
    turns %= 1
    quarter = turns * 4
    if quarter.denominator == 1:
        return (
            Z(Decimal(1)),
            Z(Decimal(0), Decimal(1)),
            Z(Decimal(-1)),
            Z(Decimal(0), Decimal(-1)),
        )[int(quarter) % 4]
    if turns > Fraction(1, 2):
        turns -= 1
    angle = 2 * PI * Decimal(turns.numerator) / Decimal(turns.denominator)
    a2 = angle * angle
    cosine = ct = Decimal(1)
    sine = st = angle
    for k in range(1, 160):
        ct *= -a2 / Decimal((2 * k - 1) * 2 * k)
        st *= -a2 / Decimal(2 * k * (2 * k + 1))
        cosine += ct
        sine += st
        if max(abs(ct), abs(st)) < Decimal("1e-90"):
            break
    return Z(cosine, sine)


def bins(size: int) -> range:
    return range(-(size // 2), (size + 1) // 2)


def modes(shape: tuple[int, int, int]) -> list[Mode]:
    return [(a, b, c) for a, b, c in product(bins(shape[0]), bins(shape[1]), bins(shape[2]))]


def index(mode: Mode, shape: tuple[int, int, int]) -> Mode:
    return tuple(q + k // 2 for q, k in zip(mode, shape, strict=True))  # type: ignore[return-value]


def negate(mode: Mode, shape: tuple[int, int, int]) -> Mode:
    return tuple((-q + k // 2) % k - k // 2 for q, k in zip(mode, shape, strict=True))  # type: ignore[return-value]


def phase_matrix(steps: Array) -> Array:
    phi = np.array(steps, dtype=np.float64, copy=True)
    c, s = np.cos(phi), np.sin(phi)
    return np.column_stack((np.ones(phi.size), c, s, c * c - s * s, (2 * c) * s))


def rational_inverse(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    n = len(matrix)
    rows = [list(row) + [Fraction(i == j) for j in range(n)] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = next(i for i in range(col, n) if rows[i][col])
        rows[col], rows[pivot] = rows[pivot], rows[col]
        divisor = rows[col][col]
        rows[col] = [v / divisor for v in rows[col]]
        for i in range(n):
            if i != col:
                factor = rows[i][col]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[col], strict=True)]
    return [row[n:] for row in rows]


def fraction_decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def separated_exact(images: Array, steps: Array) -> tuple[list[Z], list[Z], list[Z], Decimal]:
    """Exact rational LS, rounded only when converted to the Decimal observer."""
    h = [[Fraction(float(v)) for v in row] for row in phase_matrix(steps)]
    gram = [[sum((row[i] * row[j] for row in h), Fraction()) for j in range(5)] for i in range(5)]
    inv = rational_inverse(gram)
    weights = [
        [sum((inv[i][j] * row[j] for j in range(5)), Fraction()) for row in h] for i in range(5)
    ]
    flat = np.array(images, dtype=np.float64, copy=True).reshape(len(h), -1)
    bands: tuple[list[Z], list[Z], list[Z]] = ([], [], [])
    for voxel in range(flat.shape[1]):
        b = [Fraction(float(v)) for v in flat[:, voxel]]
        coordinates = [
            sum((w * v for w, v in zip(row, b, strict=True)), Fraction()) for row in weights
        ]
        bands[0].append(Z(fraction_decimal(coordinates[0])))
        bands[1].append(
            Z(fraction_decimal(coordinates[1] / 2), fraction_decimal(-coordinates[2] / 2))
        )
        bands[2].append(
            Z(fraction_decimal(coordinates[3] / 2), fraction_decimal(-coordinates[4] / 2))
        )
    # cond_2(H) <= sqrt(trace(H.T H)*trace((H.T H)^-1)).
    condition_bound = (
        fraction_decimal(sum((gram[i][i] for i in range(5)), Fraction()))
        * fraction_decimal(sum((inv[i][i] for i in range(5)), Fraction()))
    ).sqrt()
    return *bands, condition_bound


def finite_dft(band: list[Z], shape: tuple[int, int, int]) -> dict[Mode, Z]:
    coordinates = list(product(*(range(k) for k in shape)))
    result: dict[Mode, Z] = {}
    for q in modes(shape):
        value = Z(Decimal(0))
        for r, amplitude in zip(coordinates, band, strict=True):
            turns = -sum(
                (Fraction(a * b, k) for a, b, k in zip(q, r, shape, strict=True)), Fraction()
            )
            value += amplitude * root(turns)
        result[q] = value.scale(Decimal(1) / Decimal(math.prod(shape)))
    return result


def norm(vector: list[Z]) -> Decimal:
    return sum((v.square() for v in vector), Decimal(0)).sqrt()


@dataclass(frozen=True)
class Oracle:
    """Stored-input regression and independently certified regime evidence."""

    gain: Z
    residual: Decimal
    coherence: Decimal
    count: int
    nx: Decimal
    ny: Decimal
    a0: Decimal
    am: Decimal
    brightness: Decimal
    condition_bound: Decimal
    delta: Decimal

    def informative(self) -> bool:
        return (
            self.condition_bound <= 10
            and self.a0 > 0
            and self.am > 0
            and self.nx >= self.am * self.brightness / 8
            and self.ny >= self.a0 * self.brightness / 8
            and self.coherence >= Decimal("0.25")
            and Decimal("0.0001") <= self.gain.modulus() <= 10
            and self.delta <= Decimal(2) ** -10
        )


def observe(
    images: Array, steps: Array, values: Array, carrier: tuple[int, int], order: int
) -> Oracle:
    with localcontext() as ctx:
        ctx.prec = 80
        shape = tuple(int(k) for k in images.shape[1:])
        assert len(shape) == 3
        shape3: tuple[int, int, int] = (shape[0], shape[1], shape[2])
        dc, c1, c2, condition = separated_exact(images, steps)
        d0 = finite_dft(dc, shape3)
        dm = finite_dft((c1, c2)[order - 1], shape3)
        window = set(modes(shape3))
        pairs = [
            (q, (q[0], q[1] + order * carrier[0], q[2] + order * carrier[1])) for q in modes(shape3)
        ]
        pairs = [(q, j) for q, j in pairs if j in window]
        x, y = [], []
        a0 = am = Decimal(0)
        for q, j in pairs:
            e0, em = z(values[(0, *index(q, shape3))]), z(values[(order, *index(j, shape3))])
            a0 = max(a0, abs(e0.real), abs(e0.imag))
            am = max(am, abs(em.real), abs(em.imag))
            x.append(em * d0[q])
            y.append(e0 * dm[j])
        nx, ny = norm(x), norm(y)
        if nx == 0:
            raise ValueError("observer predictor is zero")
        if ny == 0:
            gain, residual, coherence = Z(Decimal(0)), Decimal(0), Decimal(0)
        else:
            u, v = [a.scale(1 / nx) for a in x], [a.scale(1 / ny) for a in y]
            correlation = sum((a.conj() * b for a, b in zip(u, v, strict=True)), Z(Decimal(0)))
            gain = correlation.scale(ny / nx)
            coherence = correlation.modulus()
            residual = norm([b - correlation * a for a, b in zip(u, v, strict=True)])
        brightness = max(abs(dec(v)) for v in np.array(images, dtype=np.float64).flat)
        delta = Decimal(65536 * len(steps) * math.prod(shape3)) * EPS
        return Oracle(
            gain, residual, coherence, len(pairs), nx, ny, a0, am, brightness, condition, delta
        )


def synthesize(spectrum: dict[Mode, complex], shape: tuple[int, int, int]) -> Array:
    """Finite positive-exponent sum; no FFT or product helper."""
    result = np.zeros(shape, dtype=np.complex128)
    for r in product(*(range(k) for k in shape)):
        terms = []
        for q, amplitude in spectrum.items():
            angle = 2 * math.pi * sum(a * b / k for a, b, k in zip(q, r, shape, strict=True))
            terms.append(amplitude * complex(math.cos(angle), math.sin(angle)))
        result[r] = complex(math.fsum(a.real for a in terms), math.fsum(a.imag for a in terms))
    return result


def exposures(dc: Array, c1: Array, c2: Array, steps: Array) -> Array:
    h = phase_matrix(steps)
    coords = np.stack((dc.real, 2 * c1.real, -2 * c1.imag, 2 * c2.real, -2 * c2.imag))
    return (h @ coords.reshape(5, -1)).reshape((len(steps), *dc.shape))


def steps_default() -> Array:
    return np.array([0.07, 0.81, 1.93, 2.87, 3.72, 4.81, 5.69], dtype=np.float64)


def fields(shape: tuple[int, int, int], values: Array | None = None) -> dict[str, Any]:
    spacing = (0.7, 0.9, 1.1)
    if values is None:
        values = np.empty((3, *shape), dtype=np.complex128)
        for m, q in product(range(3), modes(shape)):
            values[(m, *index(q, shape))] = complex(
                0.58 + 0.023 * q[0] + 0.019 * q[1] + 0.031 * q[2] + 0.07 * m,
                0.11 * m + 0.037 * q[2] - 0.017 * q[1],
            )
    return dict(
        values=values,
        fz_per_um=np.array([k / (shape[0] * spacing[0]) for k in bins(shape[0])]),
        fy_per_um=np.array([k / (shape[1] * spacing[1]) for k in bins(shape[1])]),
        fx_per_um=np.array([k / (shape[2] * spacing[2]) for k in bins(shape[2])]),
        voxel_size_um=spacing,
        origin_zyx=(shape[0] - 1, 0, shape[2] - 1),
        source="  opaque A2 calibration; unverified  ",
    )


def arbitrary_case(
    shape: tuple[int, int, int] = (2, 3, 4), steps: Array | None = None
) -> tuple[Array, Array, dict[str, Any]]:
    if steps is None:
        steps = steps_default()
    r = np.arange(math.prod(shape), dtype=np.float64).reshape(shape)
    dc = 1.4 + 0.025 * r + 0.3 * np.cos(0.7 * r)
    c1 = 0.8 + 0.02 * r + 1j * (0.22 + 0.015 * r)
    c2 = -1.0 + 0.01 * r + 1j * (0.7 + 0.01 * r)
    images = exposures(dc, c1, c2, steps)
    if len(steps) > 5:
        images += 0.03 * np.sin(np.arange(len(steps))[:, None, None, None] * 1.7 + r)
    return images, steps, fields(shape)


def constant_case(
    dc: float = 1, c1: complex = 0.3 + 0.2j, shape: tuple[int, int, int] = (1, 1, 1)
) -> tuple[Array, Array, dict[str, Any]]:
    steps = steps_default()
    images = exposures(np.full(shape, dc), np.full(shape, c1), np.zeros(shape), steps)
    return images, steps, fields(shape, np.ones((3, *shape), dtype=np.complex128))


def alias_free_case() -> tuple[
    Array, Array, dict[str, Any], dict[Mode, complex], tuple[complex, complex]
]:
    """Generate extended signed specimen support with no wrapped lateral band."""
    shape = (2, 4, 8)
    specimen: dict[Mode, complex] = {
        (0, 0, 0): 1.4,
        (0, 1, 1): 0.12 + 0.08j,
        (0, -1, -1): 0.12 - 0.08j,
        (-1, -2, 0): 0.09,
    }
    values = np.empty((3, *shape), dtype=np.complex128)
    for q in modes(shape):
        values[(0, *index(q, shape))] = 0.63 + 0.03 * math.cos(sum(q))
        values[(1, *index(q, shape))] = 0.47 + 0.01 * q[1] + 1j * (0.12 + 0.013 * q[2])
        values[(2, *index(q, shape))] = 0.55 - 0.014 * q[2] + 1j * (-0.18 + 0.02 * q[0])
    gains = (0.8 + 0.35j, -0.45 + 0.7j)
    spectra: list[dict[Mode, complex]] = [{}, {}, {}]
    for m in range(3):
        for q, amplitude in specimen.items():
            j = (q[0], q[1], q[2] + m)
            assert j in set(modes(shape))
            spectra[m][j] = (
                values[(m, *index(j, shape))] * amplitude * (1 if m == 0 else gains[m - 1])
            )
    bands = [synthesize(s, shape) for s in spectra]
    assert np.max(np.abs(bands[0].imag)) < 1e-14
    steps = steps_default()
    return (
        exposures(bands[0].real, bands[1], bands[2], steps),
        steps,
        fields(shape, values),
        specimen,
        gains,
    )


def reconstruction_observer(
    images: Array, steps: Array, values: Array, output: tuple[int, int, int], ridge: float
) -> tuple[Array, Array]:
    """Finite-sum recombination, including modular conjugate negative transfers."""
    with localcontext() as ctx:
        ctx.prec = 80
        shape: tuple[int, int, int] = tuple(images.shape[1:])  # type: ignore[assignment]
        dc, c1, c2, _ = separated_exact(images, steps)
        bands = {
            0: finite_dft(dc, shape),
            1: finite_dft(c1, shape),
            2: finite_dft(c2, shape),
            -1: finite_dft([a.conj() for a in c1], shape),
            -2: finite_dft([a.conj() for a in c2], shape),
        }
        spectrum = np.zeros(output, dtype=np.complex128)
        out_modes = set(modes(output))
        for q in out_modes:
            numerator, denominator = Z(Decimal(0)), dec(ridge)
            for m in range(-2, 3):
                j = (q[0], q[1], q[2] + m)
                if j not in bands[m]:
                    continue
                if m < 0:
                    transfer = z(values[(-m, *index(negate(j, shape), shape))]).conj()
                else:
                    transfer = z(values[(m, *index(j, shape))])
                numerator += transfer.conj() * bands[m][j]
                denominator += transfer.square()
            if denominator:
                spectrum[index(q, output)] = numerator.scale(1 / denominator).native()
        volume = synthesize({q: complex(spectrum[index(q, output)]) for q in out_modes}, output)
        return spectrum, volume
