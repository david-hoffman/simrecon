"""RA07 independent stored-input observer; no product imports or FFT oracle.

Phase fits use 80-digit Decimal elimination on the represented binary64 basis.
Spatial transforms use explicit bounded-angle finite sums. Geometry uses Fraction.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass
class Case:
    """Hold independent stored input arrays and declared physical metadata."""

    images: FloatArray
    phases: FloatArray
    gains: FloatArray
    carriers: FloatArray
    transfers: tuple[ComplexArray, ...]
    spacing: tuple[float, float, float]
    output_yx: tuple[int, int]
    taper: FloatArray
    penalty: float

    @property
    def native(self) -> tuple[int, int, int]:
        return tuple(self.images.shape[2:])  # type: ignore[return-value]

    @property
    def output(self) -> tuple[int, int, int]:
        return (self.native[0], *self.output_yx)

    @property
    def shifts(self) -> tuple[tuple[Fraction, Fraction], ...]:
        return tuple(
            tuple(
                self.native[a + 1]
                * Fraction.from_float(self.spacing[a + 1])
                * Fraction.from_float(float(row[a]))
                for a in range(2)
            )
            for row in self.carriers
        )  # type: ignore[return-value]


def bins(size: int) -> tuple[int, ...]:
    return tuple(range(-(size // 2), (size + 1) // 2))


def modes(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(itertools.product(*(bins(k) for k in shape)))


def samples(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(itertools.product(*(range(k) for k in shape)))


def phasor(cycles: Fraction) -> complex:
    """Bound exact rational cycles before conversion to a float angle."""
    angle = math.tau * float(cycles % 1)
    return complex(math.cos(angle), math.sin(angle))


def csum(values: list[complex]) -> complex:
    return complex(math.fsum(v.real for v in values), math.fsum(v.imag for v in values))


def basis(phases: FloatArray) -> FloatArray:
    c, s = np.cos(phases), np.sin(phases)
    return np.column_stack((np.ones_like(c), c, s, c * c - s * s, (2 * c) * s))


def fit(images: FloatArray, phases: FloatArray) -> tuple[ComplexArray, ...]:
    """Independent high-precision normal equations, never a production solver."""
    h = basis(phases)
    with localcontext() as ctx:
        ctx.prec = 80
        hd = [[Decimal.from_float(float(v)) for v in row] for row in h]
        gram = [
            [sum((row[i] * row[j] for row in hd), Decimal(0)) for j in range(5)] for i in range(5)
        ]
        answer = np.empty((5, math.prod(images.shape[1:])), dtype=np.float64)
        for pixel, data in enumerate(images.reshape(len(phases), -1).T):
            bd = [Decimal.from_float(float(v)) for v in data]
            rhs = [
                sum((row[i] * v for row, v in zip(hd, bd, strict=True)), Decimal(0))
                for i in range(5)
            ]
            aug = [gram[i].copy() + [rhs[i]] for i in range(5)]
            for col in range(5):
                pivot = max(range(col, 5), key=lambda i: abs(aug[i][col]))
                aug[col], aug[pivot] = aug[pivot], aug[col]
                scale = aug[col][col]
                if not scale:
                    raise ValueError("oracle requires full rank")
                aug[col] = [v / scale for v in aug[col]]
                for row in range(5):
                    if row != col:
                        scale = aug[row][col]
                        aug[row] = [a - scale * b for a, b in zip(aug[row], aug[col], strict=True)]
            answer[:, pixel] = [float(row[-1]) for row in aug]
    fields = answer.reshape(5, *images.shape[1:])
    return (
        fields[0].astype(np.complex128),
        (fields[1] - 1j * fields[2]) / 2,
        (fields[3] - 1j * fields[4]) / 2,
    )


def transform(data: ComplexArray, *, forward: bool) -> ComplexArray:
    shape = data.shape
    coords = samples(shape) if forward else modes(shape)
    destinations = modes(shape) if forward else samples(shape)
    sign, normalization = (-1, data.size) if forward else (1, 1)
    values = data.ravel()
    result = [
        csum(
            [
                complex(v)
                * phasor(
                    sign
                    * sum(
                        (Fraction(a * b, k) for a, b, k in zip(q, n, shape, strict=True)),
                        Fraction(),
                    )
                )
                for v, n in zip(values, coords, strict=True)
            ]
        )
        / normalization
        for q in destinations
    ]
    return np.array(result, dtype=np.complex128).reshape(shape)


def signed_transfer(values: ComplexArray, order: int) -> ComplexArray:
    if order >= 0:
        return values[order].copy()
    positive = values[-order]
    result = np.empty(positive.shape, dtype=np.complex128)
    for index, j in zip(np.ndindex(positive.shape), modes(positive.shape), strict=True):
        reflected = tuple(((-v + k // 2) % k) for v, k in zip(j, positive.shape, strict=True))
        result[index] = positive[reflected].conjugate()
    return result


def interpolate(values: ComplexArray, point: tuple[Fraction, ...]) -> complex | None:
    axes: list[list[tuple[int, Fraction]]] = []
    for v, k in zip(point, values.shape, strict=True):
        low, high = bins(k)[0], bins(k)[-1]
        if v < low or v > high:
            return None
        floor = v.numerator // v.denominator
        if v == floor:
            axes.append([(floor + k // 2, Fraction(1))])
        else:
            axes.append([(floor + k // 2, floor + 1 - v), (floor + 1 + k // 2, v - floor)])
    return csum(
        [
            complex(values[tuple(i for i, _ in corners)]) * float(math.prod(w for _, w in corners))
            for corners in itertools.product(*axes)
        ]
    )


def weights(case: Case) -> tuple[list[tuple[int, int, ComplexArray]], float]:
    rows = [
        (r, m, signed_transfer(e, m)) for r, e in enumerate(case.transfers) for m in range(-2, 3)
    ]
    result: list[tuple[int, int, ComplexArray]] = []
    positive_denominators: list[float] = []
    for r, m, er in rows:
        w = np.zeros(case.native, dtype=np.complex128)
        for index, j in zip(np.ndindex(case.native), modes(case.native), strict=True):
            a = (
                Fraction(j[0]),
                Fraction(j[1]) - m * case.shifts[r][0],
                Fraction(j[2]) - m * case.shifts[r][1],
            )
            contributions = []
            for s, ell, es in rows:
                query = (a[0], a[1] + ell * case.shifts[s][0], a[2] + ell * case.shifts[s][1])
                value = interpolate(es, query)
                if value is not None:
                    t = float(case.gains[s]) * value
                    contributions.append(t.real * t.real + t.imag * t.imag)
            denominator = math.fsum(contributions) + case.penalty
            if denominator:
                positive_denominators.append(denominator)
                w[index] = (float(case.gains[r]) * er[index]).conjugate() / denominator
        result.append((r, m, w))
    return result, min(positive_denominators, default=math.inf)


def oracle(case: Case) -> tuple[ComplexArray, ComplexArray]:
    fits = [fit(b, p) for b, p in zip(case.images, case.phases, strict=True)]
    filtered, _ = weights(case)
    output_samples = samples(case.output)
    native_modes = modes(case.native)
    bands = []
    for r, m, w in filtered:
        spatial = fits[r][abs(m)]
        if m < 0:
            spatial = spatial.conjugate()
        coefficients = (transform(spatial, forward=True) * w).ravel()
        band = [
            csum(
                [
                    complex(v)
                    * phasor(
                        sum(
                            (
                                Fraction(jj * nn, kk)
                                for jj, nn, kk in zip(j, n, case.output, strict=True)
                            ),
                            Fraction(),
                        )
                    )
                    for j, v in zip(native_modes, coefficients, strict=True)
                ]
            )
            * phasor(
                -m
                * (
                    case.shifts[r][0] * Fraction(n[1], case.output[1])
                    + case.shifts[r][1] * Fraction(n[2], case.output[2])
                )
            )
            for n in output_samples
        ]
        bands.append(band)
    u = np.array([csum(list(v)) for v in zip(*bands, strict=True)], dtype=np.complex128).reshape(
        case.output
    )
    spectrum = transform(u, forward=True) * case.taper
    return spectrum, transform(spectrum, forward=False)


def dense_relocation(case: Case, r: int, order: int) -> ComplexArray:
    """Independent finite L matrix: output DFT times shifted native synthesis."""
    native, out = modes(case.native), modes(case.output)
    ns = samples(case.output)
    cy, cx = case.shifts[r]
    return np.array(
        [
            [
                csum(
                    [
                        phasor(
                            Fraction((j[0] - q[0]) * n[0], case.output[0])
                            + (j[1] - q[1] - order * cy) * Fraction(n[1], case.output[1])
                            + (j[2] - q[2] - order * cx) * Fraction(n[2], case.output[2])
                        )
                        for n in ns
                    ]
                )
                / len(ns)
                for j in native
            ]
            for q in out
        ],
        dtype=np.complex128,
    )


def allowance(case: Case) -> tuple[float, float]:
    """Derive absolute intensity budgets from inputs before product output.

    Separator: inherited 8192*N*eps*B per real coordinate. Convex transfer
    interpolation cannot enlarge component maxima. 128*J*eps*tmax**2 bounds
    weighted-square/interpolation accumulation. Quotient sensitivity is
    deltaD*tmax/dmin + Dmax*deltaH*tmax/dmin**2. Native synthesis sums J*M
    terms; normalized output DFT preserves this absolute bound. Final positive
    synthesis contributes P times the spectrum budget. Extra 64*eps term per
    elementary complex operation covers independent float observer sums.
    """
    eps = np.finfo(np.float64).eps
    r, n = case.images.shape[:2]
    j, m, p = 5 * r, math.prod(case.native), math.prod(case.output)
    b = float(np.max(np.abs(case.images)))
    kappa = max(float(np.linalg.cond(basis(row))) for row in case.phases)
    tmax = max(
        float(g) * float(np.max(np.abs(e.real) + np.abs(e.imag)))
        for g, e in zip(case.gains, case.transfers, strict=True)
    )
    _, dmin = weights(case)
    if not math.isfinite(dmin):
        return (0.0, 0.0)
    derror = 2 * 8192 * n * eps * b + 64 * m * eps * kappa * b
    dmax = 4 * kappa * b
    herror = 128 * j * eps * tmax**2
    werror = derror * tmax / dmin + dmax * tmax * herror / dmin**2 + 64 * eps * dmax * tmax / dmin
    synthesis = j * m * werror + 64 * eps * j * m * (m + p) * dmax * tmax / dmin
    spectrum = synthesis + 64 * p * eps * j * m * dmax * tmax / dmin
    volume = p * spectrum + 64 * p * eps * j * m * dmax * tmax / dmin
    return spectrum + 1e-300, volume + 1e-300


def make_case(
    native: tuple[int, int, int] = (2, 2, 3),
    *,
    orientations: int = 2,
    output_yx: tuple[int, int] = (4, 5),
    off_model: bool = True,
) -> Case:
    phases = np.array([0.07, 0.81, 1.92, 2.73, 3.64, 4.61, 5.59])
    phase_rows = np.array([phases + r * 0.13 for r in range(orientations)])
    ns = np.array(samples(native), dtype=np.float64)
    images = []
    transfers = []
    for r in range(orientations):
        z, y, x = ns.T
        coefficients = np.array(
            [
                1.2 + 0.1 * z - 0.07 * y + 0.03 * x,
                0.36 + 0.02 * x - 0.04 * y,
                -0.27 + 0.06 * z + 0.01 * x,
                -0.22 + 0.05 * y - 0.02 * x,
                0.31 + 0.02 * z + 0.04 * y,
            ]
        )
        data = basis(phase_rows[r]) @ coefficients
        if off_model:
            data += (0.023 * np.arange(7) ** 2)[:, None] * (1 + 0.03 * x)[None, :]
        images.append(data.reshape(7, *native))
        grid = np.arange(3 * math.prod(native), dtype=np.float64).reshape(3, *native)
        transfers.append(
            (0.31 + 0.004 * grid + 0.03 * r + 1j * (-0.21 + 0.007 * grid - 0.02 * r)).astype(
                np.complex128
            )
        )
    spacing = (0.75, 0.5, 1.25)
    # Nominal shifts; divided physical carriers can round. The oracle retains
    # the exact converted rational products. Keep away from a ceil boundary.
    shifts = [(0.375, -0.3125), (-0.25, 0.4375)]
    carriers = np.array(
        [
            [shifts[r][0] / (native[1] * spacing[1]), shifts[r][1] / (native[2] * spacing[2])]
            for r in range(orientations)
        ]
    )
    taper = np.linspace(0.2, 1.0, native[0] * math.prod(output_yx)).reshape(native[0], *output_yx)
    return Case(
        np.array(images),
        phase_rows,
        np.array([0.75, 1.5][:orientations]),
        carriers,
        tuple(transfers),
        spacing,
        output_yx,
        taper,
        0.1875,
    )


def five_phase_case() -> Case:
    """Select five stored exposures without changing the original fixtures."""
    case = make_case((1, 1, 1), orientations=1, output_yx=(3, 3))
    case.images = case.images[:, :5].copy()
    case.phases = case.phases[:, :5].copy()
    return case


def analytic_case() -> tuple[Case, complex]:
    case = make_case((1, 1, 1), orientations=1, output_yx=(3, 3), off_model=False)
    case.carriers = np.array([[-0.75, 0.25]])  # bin shifts (-3/8,+5/16)
    case.gains[:] = 1
    case.taper[:] = 1
    case.penalty = 0.25
    a, t = complex(0.375, -0.21875), complex(0.5, 0.25)
    case.transfers[0][:] = 0
    case.transfers[0][2] = t
    coordinates = np.array([0.0, 0.0, 0.0, 2 * a.real, -2 * a.imag])
    case.images[0] = (basis(case.phases[0]) @ coordinates).reshape(7, 1, 1, 1)
    return case, a * t.conjugate() / (abs(t) ** 2 + case.penalty)


def analytic_volume(case: Case, amplitude: complex, *, sign: int = -1) -> ComplexArray:
    cy, cx = case.shifts[0]
    return np.array(
        [
            2
            * (
                amplitude
                * phasor(
                    sign
                    * 2
                    * (cy * Fraction(n[1], case.output[1]) + cx * Fraction(n[2], case.output[2]))
                )
            ).real
            for n in samples(case.output)
        ],
        dtype=np.complex128,
    ).reshape(case.output)
