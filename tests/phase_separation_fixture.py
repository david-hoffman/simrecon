"""Blind A: stored-value rational oracle and unequal-phase analytic fixture.

No product solve is used. All least-squares algebra and certificate checks use
exact Fractions; square-root enclosures use integer arithmetic (192 bits).
Normal equations here are exact oracle algebra, never a shipped solver.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from math import isqrt
from typing import Any

import numpy as np
from numpy.typing import NDArray

Array = NDArray[Any]
Vector = list[F]
Matrix = list[Vector]
EPS = F(1, 2**52)
Q_HALF = F(1, 2**1075)
PHASES = (-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81)


class OracleUnresolved(RuntimeError):
    """No supplied sufficient certificate succeeded; this is not product-red."""


def rational(value: Any) -> F:
    return F.from_float(float(value))


def dot(a: Vector, b: Vector) -> F:
    return sum((x * y for x, y in zip(a, b, strict=True)), F(0))


def norm2(a: Vector) -> F:
    return dot(a, a)


def mv(a: Matrix, x: Vector) -> Vector:
    return [dot(row, x) for row in a]


def transpose(a: Matrix) -> Matrix:
    return [list(col) for col in zip(*a, strict=True)]


def gram(a: Matrix) -> Matrix:
    cols = transpose(a)
    return [[dot(x, y) for y in cols] for x in cols]


def inverse(a: Matrix) -> Matrix:
    n = len(a)
    work = [row.copy() + [F(i == j) for j in range(n)] for i, row in enumerate(a)]
    for j in range(n):
        pivot = work[j][j]
        assert pivot != 0, "oracle requires nonsingular exact represented Gram matrix"
        work[j] = [v / pivot for v in work[j]]
        for i in range(n):
            if i != j:
                factor = work[i][j]
                work[i] = [x - factor * y for x, y in zip(work[i], work[j], strict=True)]
    return [row[n:] for row in work]


def determinant3(a: Matrix) -> F:
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def positive_definite(a: Matrix) -> bool:
    return a[0][0] > 0 and a[0][0] * a[1][1] - a[0][1] * a[1][0] > 0 and determinant3(a) > 0


def sqrt_interval(value: F) -> tuple[F, F]:
    """Exact enclosing endpoints; no overflow or zeroed subnormal allowance."""
    assert value >= 0
    if value == 0:
        return F(0), F(0)
    exponent = (value.numerator.bit_length() - value.denominator.bit_length()) // 2
    scale = F(2) ** (192 - exponent)
    scaled = value * scale * scale
    root = isqrt(scaled.numerator // scaled.denominator)
    return F(root) / scale, F(root + 1) / scale


def spectral2_interval(g: Matrix) -> tuple[F, F]:
    """Enclose lambda_max(G) by exact Sylvester tests, not a numeric eigensolve."""
    low = max(g[i][i] for i in range(3))
    high = sum((g[i][i] for i in range(3)), F(0))
    for _ in range(128):
        mid = (low + high) / 2
        shift = [[F(i == j) * mid - g[i][j] for j in range(3)] for i in range(3)]
        if positive_definite(shift):
            high = mid
        else:
            low = mid
    return low, high


@dataclass
class RationalFit:
    """Represent an exact stored-matrix fit and sufficient backward witnesses."""

    k: Matrix
    inv: Matrix
    a2_low: F
    a2_high: F
    s2_low: F

    @classmethod
    def from_phases(cls, phases: Array) -> RationalFit:
        h = represented_h(phases)
        k = [[rational(row[0]), 2 * rational(row[1]), -2 * rational(row[2])] for row in h]
        return cls.from_k(k)

    @classmethod
    def from_k(cls, k: Matrix) -> RationalFit:
        g = gram(k)
        assert positive_definite(g), "exact represented matrix is not full rank"
        inv = inverse(g)
        low, high = spectral2_interval(g)
        # trace(G^-1) >= 1/lambda_min(G): rigorous lower singular bound.
        s2 = 1 / sum((inv[i][i] for i in range(3)), F(0))
        return cls(k, inv, low, high, s2)

    def expected(self, b: Vector) -> Vector:
        return mv(self.inv, mv(transpose(self.k), b))

    def residual(self, b: Vector, z: Vector) -> Vector:
        return [v - w for v, w in zip(b, mv(self.k, z), strict=True)]

    def forward_bound(self, b: Vector, star: Vector) -> F | None:
        eta = 128 * max(len(self.k), 3) * EPS
        alpha = eta * sqrt_interval(self.a2_high)[1]
        s = sqrt_interval(self.s2_low)[0]
        if alpha >= s:
            return None
        beta = eta * sqrt_interval(norm2(b))[1]
        r = self.residual(b, star)
        return (
            (beta + alpha * sqrt_interval(norm2(star))[1]) / (s - alpha)
            + alpha * sqrt_interval(norm2(r))[1] / (s - alpha) ** 2
            + sqrt_interval(F(3))[1] * Q_HALF
        )

    def _valid(self, b: Vector, z: Vector, e: Matrix, f: Vector) -> bool:
        eta = 128 * max(len(self.k), 3) * EPS
        # Frobenius is a conservative upper bound for spectral E. Exact lower
        # endpoint for ||K|| makes this a sufficient, never optimistic, check.
        if sum((norm2(row) for row in e), F(0)) > eta**2 * self.a2_low:
            return False
        if norm2(f) > eta**2 * norm2(b):
            return False
        changed = [
            [x + y for x, y in zip(r, s, strict=True)] for r, s in zip(self.k, e, strict=True)
        ]
        if not positive_definite(gram(changed)):
            return False
        residual = self.residual_with(changed, [x + y for x, y in zip(b, f, strict=True)], z)
        # Exact full-rank normal equations are sufficient for unique minimizer.
        return all(v == 0 for v in mv(transpose(changed), residual))

    @staticmethod
    def residual_with(k: Matrix, b: Vector, z: Vector) -> Vector:
        return [x - y for x, y in zip(b, mv(k, z), strict=True)]

    def certify(self, b: Vector, returned: Vector) -> str:
        star = self.expected(b)
        # Exact final quantization d, independently bounded by q/2 per lane.
        d = [max(-Q_HALF, min(Q_HALF, x - y)) for x, y in zip(returned, star, strict=True)]
        z = [x - y for x, y in zip(returned, d, strict=True)]
        delta = [x - y for x, y in zip(z, star, strict=True)]
        u = mv(self.k, delta)
        zero_e = [[F(0)] * 3 for _ in self.k]
        if self._valid(b, z, zero_e, u):
            return "rhs-only"
        zz = norm2(z)
        if zz:
            # Split u between E*z=-t*u and f=(1-t)*u. Every candidate has
            # residual r_star and E columns in col(K), so orthogonality is exact.
            unorm = sqrt_interval(norm2(u))[1]
            bnorm = sqrt_interval(norm2(b))[0]
            eta = 128 * max(len(self.k), 3) * EPS
            needed = max(F(0), 1 - eta * bnorm / unorm) if unorm else F(0)
            for t in (F(1), needed):
                e = [[-t * v * w / zz for w in z] for v in u]
                f = [(1 - t) * v for v in u]
                if self._valid(b, z, e, f):
                    return "column-space/split"
        r = self.residual(b, z)
        rr = norm2(r)
        if rr:
            # Residual projection construction: E=-r*(K.T*r).T/||r||^2,
            # f=E*z. Residual remains r and (K+E).T*r=0 exactly.
            g = mv(transpose(self.k), r)
            e = [[-v * w / rr for w in g] for v in r]
            if self._valid(b, z, e, mv(e, z)):
                return "residual-projection"
        if rr and zz:
            # E-only alternative: v=t*r, t=(b.T*r)/||r||^2. Then
            # v.T*(b-v)=0. Satisfy E*z=w=b-v-K*z and E.T*v=-K.T*v.
            t = dot(b, r) / rr
            v = [t * x for x in r]
            vv = norm2(v)
            if vv:
                w = [x - y for x, y in zip(r, v, strict=True)]
                g = [-x for x in mv(transpose(self.k), v)]
                correction = [x - y * dot(v, w) / zz for x, y in zip(g, z, strict=True)]
                e = [
                    [wi * zj / zz + vi * cj / vv for zj, cj in zip(z, correction, strict=True)]
                    for wi, vi in zip(w, v, strict=True)
                ]
                if self._valid(b, z, e, [F(0)] * len(b)):
                    return "rescaled-residual"
        bound = self.forward_bound(b, star)
        if (
            bound is not None
            and norm2([x - y for x, y in zip(returned, star, strict=True)]) > bound**2
        ):
            raise AssertionError(
                "V01/V03/V20: violates necessary finite forward consequence of backward policy"
            )
        if not norm2(b) and any(returned):
            raise AssertionError("V02: zero observations require zero returned float64 lanes")
        raise OracleUnresolved(
            "no sufficient full-rank certificate; alternatives need independent review, "
            "not product-red"
        )


def represented_h(phases: Array) -> Array:
    with np.errstate(all="ignore"):
        p = phases.astype(np.float64)
        return np.column_stack((np.ones(p.size), np.cos(p), np.sin(p)))


def expected_arrays(images: Array, phases: Array) -> tuple[Array, Array, Array]:
    """Compute dc, c1 and all fitted-minus-input residuals for stored values."""
    with np.errstate(all="ignore"):
        values = images.astype(np.float64)
    fit = RationalFit.from_phases(phases)
    shape = values.shape[1:]
    dc = np.empty(shape, dtype=np.float64)
    c1 = np.empty(shape, dtype=np.complex128)
    residuals = np.empty(values.shape, dtype=np.float64)
    for index in np.ndindex(shape):
        b = [rational(v) for v in values[(slice(None), *index)]]
        z = fit.expected(b)
        dc[index] = float(z[0])
        c1[index] = complex(float(z[1]), float(z[2]))
        residuals[(slice(None), *index)] = [-float(v) for v in fit.residual(b, z)]
    return dc, c1, residuals


@dataclass
class AnalyticFixture:
    """Hold all independent numeric panels for the later real comparison."""

    phases_rad: Array
    images: Array
    h: Array
    generating_dc: Array
    generating_c1: Array
    expected_dc: Array
    expected_c1: Array
    expected_residuals: Array


def analytic_fixture(shape: tuple[int, int] = (9, 14)) -> AnalyticFixture:
    """Signed, asymmetric, nonsquare phantom; N=7 unequal well-spaced phases.

    Coordinates x,y each span [-1,1]. All intensities use arbitrary common
    input intensity units. The stored rounded problem defines expectations.
    C can render these fields and its actual public output; no fake output.
    """
    y, x = np.meshgrid(np.linspace(-1, 1, shape[0]), np.linspace(-1, 1, shape[1]), indexing="ij")
    dc = 1.2 + 0.4 * x - 0.7 * y + 1.8 * np.exp(-((x - 0.31) ** 2 / 0.09 + (y + 0.22) ** 2 / 0.21))
    real = -0.9 + 0.65 * x + 0.31 * np.sin(2.1 * y + 0.3)
    imag = 0.6 - 0.47 * y + 0.8 * np.exp(-((x + 0.42) ** 2 / 0.16 + (y - 0.37) ** 2 / 0.07))
    c1 = real + 1j * imag
    phases = np.array(PHASES, dtype=np.float64)
    h = represented_h(phases)
    images = dc[None] + 2 * real[None] * h[:, 1, None, None] - 2 * imag[None] * h[:, 2, None, None]
    expected_dc, expected_c1, residuals = expected_arrays(images, phases)
    return AnalyticFixture(phases, images, h, dc, c1, expected_dc, expected_c1, residuals)
