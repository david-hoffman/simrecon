"""Independent stored-input arithmetic for the public carrier-scan contract.

No production estimator, sampler, separator or FFT supplies an expectation.
The observer uses exact rational five-column least squares and 160-digit
Decimal complex finite sums. Normal equations are an exact rational observer,
not the required floating-point production solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache, lru_cache
from itertools import product
from typing import Any

import numpy as np

D = Decimal
PRECISION = 160
EPS = D.from_float(float.fromhex("0x1p-52"))
Q0 = D.from_float(float.fromhex("0x0.0000000000001p-1022"))
FMAX = D.from_float(float(np.finfo(np.float64).max))
ZERO = D(0)


def dec(value: Any) -> Decimal:
    if isinstance(value, Fraction):
        return D(value.numerator) / D(value.denominator)
    if isinstance(value, (float, np.floating)):
        return D.from_float(float(value))
    return D(value)


@dataclass(frozen=True)
class Z:
    """A Decimal complex value with component-safe observer arithmetic."""

    re: Decimal = D(0)
    im: Decimal = D(0)

    def __add__(self, other: Z) -> Z:
        """Add represented components."""
        return Z(self.re + other.re, self.im + other.im)

    def __sub__(self, other: Z) -> Z:
        """Subtract represented components."""
        return Z(self.re - other.re, self.im - other.im)

    def __mul__(self, other: Z) -> Z:
        """Multiply without binary64 intermediate limits."""
        return Z(
            self.re * other.re - self.im * other.im,
            self.re * other.im + self.im * other.re,
        )

    def scale(self, factor: Decimal) -> Z:
        return Z(self.re * factor, self.im * factor)

    def conj(self) -> Z:
        return Z(self.re, -self.im)

    def norm(self) -> Decimal:
        return (self.re * self.re + self.im * self.im).sqrt()


def z(value: Any) -> Z:
    number = complex(value)
    return Z(dec(number.real), dec(number.imag))


def total(values: Any) -> Z:
    result = Z()
    for value in values:
        result = result + value
    return result


def norm(values: Any) -> Decimal:
    return sum((v.re * v.re + v.im * v.im for v in values), D(0)).sqrt()


@lru_cache(maxsize=1)
def pi() -> Decimal:
    # Gauss-Legendre, quadratic convergence; 12 iterations exceed 480 digits.
    with localcontext() as ctx:
        ctx.prec = 480
        a, b, t, p = D(1), D(1) / D(2).sqrt(), D(1) / 4, D(1)
        for _ in range(12):
            next_a = (a + b) / 2
            b = (a * b).sqrt()
            t -= p * (a - next_a) ** 2
            a = next_a
            p *= 2
        return (a + b) ** 2 / (4 * t)


def cis(angle: Decimal) -> Z:
    # Argument reduction needs 480 digits for a finite binary64 angle near 1e308.
    with localcontext() as ctx:
        ctx.prec = 480
        angle %= 2 * pi()
        if angle > pi():
            angle -= 2 * pi()
        if angle < -pi():
            angle += 2 * pi()
        with localcontext() as inner:
            inner.prec = PRECISION + 20
            angle = +angle
            cosine, sine = D(1), angle
            tc, ts = D(1), angle
            n = 1
            while True:
                tc *= -(angle * angle) / ((2 * n - 1) * (2 * n))
                ts *= -(angle * angle) / ((2 * n) * (2 * n + 1))
                cosine += tc
                sine += ts
                if max(abs(tc), abs(ts)) < D("1e-170"):
                    return Z(cosine, sine)
                n += 1


@cache
def root(cycles: Fraction) -> Z:
    with localcontext() as ctx:
        ctx.prec = 480
        return cis(-2 * pi() * dec(cycles % 1))


def bins(size: int) -> range:
    return range(-(size // 2), (size + 1) // 2)


def frequency(index: int, size: int, spacing: float) -> Fraction:
    # The float conversion performs RN64 of this exact rational, separately.
    return Fraction.from_float(float(Fraction(index, size) / Fraction(float(spacing))))


def phase_matrix(phases: np.ndarray) -> np.ndarray:
    p = np.asarray(phases, dtype=np.float64)
    c, s = np.cos(p), np.sin(p)
    return np.column_stack((np.ones(p.size), c, s, c * c - s * s, (2 * c) * s))


def observations(shape: tuple[int, int, int], phases: np.ndarray) -> np.ndarray:
    """Asymmetric signed, off-model observations; all five columns are excited."""
    grid = np.arange(np.prod(shape), dtype=np.float64).reshape(shape)
    coefficients = np.stack(
        (
            2 + grid / 16,
            np.sin(grid + 0.2),
            np.cos(grid * 0.7),
            0.3 + grid / 41,
            np.sin(grid * 1.1) / 2,
        )
    )
    data = (phase_matrix(phases) @ coefficients.reshape(5, -1)).reshape((phases.size, *shape))
    # Not a sixth phase harmonic assumed to be orthogonal: LS must project it.
    data += np.arange(phases.size)[:, None, None, None] ** 2 * (grid + 1) / 701
    return data


def solve_exact(images: np.ndarray, phases: np.ndarray) -> list[list[Fraction]]:
    h = [[Fraction(float(v)) for v in row] for row in phase_matrix(phases)]
    b = np.asarray(images, dtype=np.float64).reshape(len(h), -1)
    width = b.shape[1]
    augmented = [
        [sum((row[i] * row[j] for row in h), Fraction()) for j in range(5)]
        + [
            sum((row[i] * Fraction(float(b[n, j])) for n, row in enumerate(h)), Fraction())
            for j in range(width)
        ]
        for i in range(5)
    ]
    for col in range(5):
        pivot = next(i for i in range(col, 5) if augmented[i][col])
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        divisor = augmented[col][col]
        augmented[col] = [v / divisor for v in augmented[col]]
        for row in range(5):
            if row != col:
                factor = augmented[row][col]
                augmented[row] = [
                    a - factor * b for a, b in zip(augmented[row], augmented[col], strict=True)
                ]
    return [row[5:] for row in augmented]


def bands(images: np.ndarray, phases: np.ndarray, order: int) -> tuple[list[Z], list[Z]]:
    solution = solve_exact(images, phases)
    return (
        [Z(dec(v)) for v in solution[0]],
        [
            Z(dec(a) / 2, -dec(b) / 2)
            for a, b in zip(solution[2 * order - 1], solution[2 * order], strict=True)
        ],
    )


def phase_condition_upper_bound(phases: np.ndarray) -> Decimal:
    """Prove cond2(H)<=||H||F*||H+||F with exact rational operands."""
    h = phase_matrix(phases)
    h_norm_squared = sum((Fraction(float(v)) ** 2 for v in h.flat), Fraction())
    inverse = solve_exact(np.eye(len(phases)), phases)
    inverse_norm_squared = sum((v * v for row in inverse for v in row), Fraction())
    return dec(h_norm_squared * inverse_norm_squared).sqrt()


def finite_dft(values: list[Z], mode: tuple[int, ...], shape: tuple[int, ...]) -> Z:
    return total(
        value
        * root(
            sum((Fraction(k * r, n) for k, r, n in zip(mode, site, shape, strict=True)), Fraction())
        )
        for site, value in zip(product(*(range(n) for n in shape)), values, strict=True)
    ).scale(D(1) / int(np.prod(shape)))


def stencil(point: tuple[Fraction, ...], shape: tuple[int, ...], spacing: Any) -> Any:
    axes = []
    for query, size, step in zip(point, shape, spacing, strict=True):
        # Exact source index, relative to the first canonical source node.
        index = query * size * Fraction(float(step)) + size // 2
        if index < 0 or index > size - 1:
            return None
        low = index.numerator // index.denominator
        t = index - low
        axes.append([(low, Fraction(1))] if not t else [(low, 1 - t), (low + 1, t)])
    return [
        (tuple(entry[0] for entry in corner), corner[0][1] * corner[1][1] * corner[2][1])
        for corner in product(*axes)
    ]


def transfer(
    response: Any, order: int, point: tuple[Fraction, ...], carrier: Any, offset: Any, delta: float
) -> Any:
    corners = stencil(point, response.values.shape[1:], response.voxel_size_um)
    if corners is None:
        return None
    value, envelope = Z(), D(0)
    for site, weight in corners:
        sample = z(response.values[(order, *site)])
        value += sample.scale(dec(weight))
        envelope += dec(weight) * (abs(sample.re) + abs(sample.im))
    rho = (
        sum(
            (
                Fraction(int(k) * (int(origin) + int(shift)), int(size))
                for k, origin, shift, size in zip(
                    carrier, response.origin_zyx[1:], offset, response.values.shape[2:], strict=True
                )
            ),
            Fraction(),
        )
        % 1
    )
    if order:
        with localcontext() as ctx:
            ctx.prec = 480
            rotation = cis(-order * (2 * pi() * dec(rho) + dec(float(delta))))
        value *= rotation
    return value, 1024 * EPS * envelope + 64 * Q0


@dataclass(frozen=True)
class Expected:
    """Independent target and conditional project error allocations."""

    count: int
    gain: Z
    residual: Decimal
    coherence: Decimal
    gain_bound: Decimal
    residual_bound: Decimal
    coherence_bound: Decimal
    informative: bool
    success_margin: bool
    h: Decimal
    stencil_ratio: Decimal
    condition_upper_bound: Decimal


def expected(
    images: np.ndarray,
    phases: np.ndarray,
    response: Any,
    spacing: Any,
    carrier: tuple[int, int],
    order: int,
    calibration: Any = (0, 0),
    offset: Any = (0, 0),
    delta: float = 0.0,
    source_error: Decimal = ZERO,
) -> Expected | None:
    with localcontext() as ctx:
        ctx.prec = PRECISION
        shape = images.shape[1:]
        modes = list(product(*(bins(n) for n in shape)))
        dc, cm = bands(images, phases, order)
        x, y, targets = [], [], []
        for p in modes:
            j = (p[0], p[1] + order * carrier[0], p[2] + order * carrier[1])
            if not all(k in bins(n) for k, n in zip(j, shape, strict=True)):
                continue
            fp = tuple(frequency(k, n, d) for k, n, d in zip(p, shape, spacing, strict=True))
            fj = tuple(frequency(k, n, d) for k, n, d in zip(j, shape, spacing, strict=True))
            t0 = transfer(response, 0, fp, calibration, offset, delta)
            tm = transfer(response, order, fj, calibration, offset, delta)
            if t0 is None or tm is None:
                return None
            f0, e0 = t0
            fm, em = tm
            # Composition only: a proved upstream complex source error passes
            # through convex interpolation/gauge with unit norm. The actual
            # source envelope can exceed this reference envelope by <=2*error.
            e0 += (1 + 2048 * EPS) * source_error
            em += (1 + 2048 * EPS) * source_error
            d0, dm = finite_dft(dc, p, shape), finite_dft(cm, j, shape)
            x.append(fm * d0)
            y.append(f0 * dm)
            targets.append((d0, dm, f0, fm, e0, em))
        xn, yn = norm(x), norm(y)
        if not x or not xn or not yn:
            raise ValueError("Use exact analytic tests for information-zero outcomes")
        u, v = [a.scale(1 / xn) for a in x], [b.scale(1 / yn) for b in y]
        correlation = total(a.conj() * b for a, b in zip(u, v, strict=True))
        gain = correlation.scale(yn / xn)
        residual = norm([b - correlation * a for a, b in zip(u, v, strict=True)])
        bmax = max(abs(dec(float(v))) for v in images.flat)
        alpha = 8192 * images.shape[0] * EPS * bmax + 8 * Q0
        error_d = 2 * alpha + 4096 * int(np.prod(shape)) * EPS * (10 * bmax + 2 * alpha) + 64 * Q0
        sx = max(fm.norm() + em for _, _, _, fm, _, em in targets) * max(
            d0.norm() + error_d for d0, *_ in targets
        )
        sy = max(f0.norm() + e0 for _, _, f0, _, e0, _ in targets) * max(
            dm.norm() + error_d for _, dm, *_ in targets
        )
        nu = 64 * EPS + 64 * Q0
        ex = sum(
            (
                (fm.norm() * error_d + d0.norm() * em + error_d * em + nu * sx) ** 2
                for d0, _, _, fm, _, em in targets
            ),
            D(0),
        ).sqrt()
        ey = sum(
            (
                (f0.norm() * error_d + dm.norm() * e0 + error_d * e0 + nu * sy) ** 2
                for _, dm, f0, _, e0, _ in targets
            ),
            D(0),
        ).sqrt()
        a, b = ex / xn, ey / yn
        h = a + b
        gamma = 4096 * len(x) * EPS + 128 * Q0
        condition_upper = phase_condition_upper_bound(phases)
        informative = condition_upper <= 10 and h + gamma <= D(1) / 64
        if a >= 1:
            # No informative guarantee: callers must not use these as tolerances.
            gain_bound = D("Infinity")
        else:
            gain_bound = (yn / xn) * (h * (2 * (1 + b) + correlation.norm()) + (1 + b) * gamma) / (
                1 - a
            ) + 8 * Q0
        coord_margin = all(
            abs(dec(coordinate)) + alpha < FMAX
            for row in solve_exact(images, phases)
            for coordinate in row
        )
        transfer_margin = all(
            max(abs(f0.re), abs(f0.im)) + e0 < FMAX and max(abs(fm.re), abs(fm.im)) + em < FMAX
            for _, _, f0, fm, e0, em in targets
        )
        success = (
            coord_margin and transfer_margin and max(abs(gain.re), abs(gain.im)) + gain_bound < FMAX
        )
        ratios = [
            e / max(f.norm(), Q0)
            for _, _, f0, fm, e0, em in targets
            for f, e in ((f0, e0), (fm, em))
            if f.norm() > 0
        ]
        return Expected(
            len(x),
            gain,
            residual,
            correlation.norm(),
            gain_bound,
            4 * h + gamma,
            2 * h + gamma,
            informative,
            success,
            h,
            max(ratios),
            condition_upper,
        )
