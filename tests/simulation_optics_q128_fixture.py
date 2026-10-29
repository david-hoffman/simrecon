"""Certified finite Q128 examples; exact inputs and outward Decimal arithmetic.

Only the explicitly constructed examples below are qualified. The frozen
simulation_optics_fixture supplies interval arithmetic, Machin pi bounds and
Taylor/geometric-tail sin/cos/J0 bounds. No product value supplies truth.
Canonical roots are certified by exact integer signs and degree exhaustion;
floating Newton iterates only propose brackets. See the bound author report
for the complete error argument and the deliberately limited physical domain.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np
from numpy.typing import NDArray

from simulation_optics_fixture import (
    Bounds,
    Interval,
    OracleInconclusive,
    Reference,
    Source,
    bessel_from_square,
    exact,
    pi_interval,
    sin_cos,
)

Rule = tuple[tuple[Interval, Interval], ...]


def legendre_sign(order: int, x: Fraction) -> int:
    """Sign of n! b**n P_n(a/b), using only exact integer operations.

    Multiplying n P_n=(2n-1)x P_(n-1)-(n-1)P_(n-2) gives
    H_n=(2n-1)a H_(n-1)-(n-1)**2 b**2 H_(n-2).
    The removed factor n! b**n is strictly positive.
    """
    a, b = x.numerator, x.denominator
    previous, current = 1, a
    for n in range(2, order + 1):
        previous, current = current, (2 * n - 1) * a * current - (n - 1) ** 2 * b * b * previous
    return (current > 0) - (current < 0)


@cache
def root_brackets(order: int, bits: int) -> tuple[tuple[Fraction, Fraction], ...]:
    """All distinct roots: disjoint exact sign changes exhaust the degree."""
    assert order in (64, 128) and bits >= 200
    positive = []
    for i in range(1, order // 2 + 1):
        seed = math.cos(math.pi * (i - 0.25) / (order + 0.5))
        for _ in range(8):
            previous, current = 1.0, seed
            for n in range(2, order + 1):
                previous, current = current, ((2 * n - 1) * seed * current - (n - 1) * previous) / n
            derivative = order * (previous - seed * current) / (1 - seed * seed)
            seed -= current / derivative
        lo, hi = exact(seed) - Fraction(1, 2**38), exact(seed) + Fraction(1, 2**38)
        left, right = legendre_sign(order, lo), legendre_sign(order, hi)
        if not (0 < lo < hi < 1 and left * right == -1):
            raise OracleInconclusive("Newton proposal failed exact root-bracket certification")
        while hi - lo > Fraction(1, 2**bits):
            middle = (lo + hi) / 2
            sign = legendre_sign(order, middle)
            if sign == 0:
                raise OracleInconclusive("unexpected exact rational Legendre root")
            if sign == left:
                lo = middle
            else:
                hi = middle
        positive.append((lo, hi))
    all_roots = sorted(positive + [(-hi, -lo) for lo, hi in positive])
    assert len(all_roots) == order
    assert all(a[1] < b[0] for a, b in zip(all_roots, all_roots[1:], strict=False))
    # Each interval contains a real root by continuity. A degree-n polynomial
    # cannot have more than n distinct roots. Thus none are missing or repeated.
    return tuple(all_roots)


@cache
def canonical_rule(order: int, digits: int) -> Rule:
    """Enclose transformed Gauss-Legendre weights without renormalization.

    At each root x of P_n, w_[0,1]=(1-x*x)/(n*n*P_(n-1)(x)**2).
    This follows from P'_n=n P_(n-1)/(1-x*x) and the Gauss weight
    2/((1-x*x)*P'_n**2) on [-1,1], then the half-interval transform.
    """
    rule = []
    reflected_weights: dict[tuple[Fraction, Fraction], Interval] = {}
    for lo, hi in root_brackets(order, 4 * digits):
        x = Interval(Interval.rational(lo, digits).lo, Interval.rational(hi, digits).hi, digits)
        key = (lo, hi) if lo > 0 else (-hi, -lo)
        if key not in reflected_weights:
            previous, current = Interval.rational(1, digits), x
            for n in range(2, order):
                previous, current = current, ((2 * n - 1) * x * current - (n - 1) * previous) / n
            # Recurrence parity makes the canonical squared denominator even;
            # the reflected bracket therefore has this same weight enclosure.
            reflected_weights[key] = (1 - x.squared()) / (order * order * current.squared())
        weight = reflected_weights[key]
        node = (1 + x) / 2
        assert 0 < node.lo <= node.hi < 1 and weight.lo > 0
        rule.append((node, weight))
    total = sum((w for _, w in rule), start=Interval.rational(0, digits))
    assert total.lo <= 1 <= total.hi
    return tuple(rule)


def reference_rule(kind: str, digits: int) -> Rule:
    """Canonical Q128 or named oracle-only normalized alternative models."""
    if kind in {"canonical128", "canonical64"}:
        return canonical_rule(128 if kind == "canonical128" else 64, digits)
    if kind == "midpoint128":
        return tuple(
            (
                Interval.rational(Fraction(2 * j + 1, 256), digits),
                Interval.rational(Fraction(1, 128), digits),
            )
            for j in range(128)
        )
    assert kind == "equal-weight128"
    return tuple(
        (u, Interval.rational(Fraction(1, 128), digits)) for u, _ in canonical_rule(128, digits)
    )


@dataclass(frozen=True)
class Geometry:
    """Explicit complete source/focus/pixel domain, independent of product output."""

    sources: tuple[Source, ...]
    focuses: tuple[Fraction, ...]
    sites: tuple[tuple[tuple[Fraction, Fraction], ...], ...]
    lateral_shape: tuple[int, int]
    area: Fraction
    carriers: tuple[tuple[float, float], ...]
    phases: tuple[tuple[float, ...], ...]
    beams: tuple[float, float, float]
    excitation: float
    emission: float
    index: float
    aperture: float

    def reference(self, rule_kind: str = "canonical128") -> Reference:
        """Enclose every output and every unilluminated entry, including tails."""
        shape = (len(self.carriers), len(self.phases[0]), len(self.focuses), *self.lateral_shape)
        assert len(self.sites) == math.prod(self.lateral_shape)
        frequency, nu = (
            exact(self.aperture) / exact(self.emission),
            exact(self.index) / exact(self.emission),
        )
        beta = exact(self.aperture) / exact(self.index)
        k0 = exact(self.index) / exact(self.excitation)
        a0, plus, minus = map(exact, self.beams)
        norm = a0 * a0 + plus * plus + minus * minus

        @cache
        def evaluate(digits: int) -> Bounds:
            # Guard digits counter interval recurrence dependency at degree 128.
            # Actual endpoint widths, not the digit count, certify comparisons.
            working = digits + 80
            rule = reference_rule(rule_kind, working)
            pi, zero = pi_interval(working), Interval.rational(0, working)

            @cache
            def radial(radius_squared: Fraction) -> tuple[Interval, ...]:
                return tuple(
                    bessel_from_square(pi.squared() * (frequency**2 * radius_squared) * u)
                    for u, _ in rule
                )

            @cache
            def axial(d: Fraction) -> tuple[tuple[Interval, Interval], ...]:
                return tuple(
                    sin_cos(2 * pi * (nu * d) * ((1 - beta**2 * u).sqrt() - 1)) for u, _ in rule
                )

            @cache
            def density(radius_squared: Fraction, absolute_d: Fraction) -> Interval:
                # h(r,-d)=h(r,d) by conjugation of this real weighted pupil.
                real, imaginary = zero, zero
                for j0, (sine, cosine), (_, weight) in zip(
                    radial(radius_squared), axial(absolute_d), rule, strict=True
                ):
                    real += weight * j0 * cosine
                    imaginary += weight * j0 * sine
                return pi * frequency**2 * (real.squared() + imaginary.squared())

            @cache
            def illumination(j: int, k: int, o: int, p: int) -> Interval:
                source = self.sources[j]
                qy, qx = map(exact, self.carriers[o])
                kappa = k0 - Interval.rational(k0**2 - qy**2 - qx**2, working).sqrt()
                theta = 2 * pi * ((qy * source.y + qx * source.x) % 1) + exact(self.phases[o][p])
                sy, cy = sin_cos(theta)
                sz, cz = sin_cos(2 * pi * kappa * (source.z - self.focuses[k]))
                return (
                    (a0 * cz + (plus + minus) * cy).squared()
                    + (a0 * sz + (plus - minus) * sy).squared()
                ) / norm

            contributions = tuple(
                tuple(
                    sum(
                        (
                            density((y - s.y) ** 2 + (x - s.x) ** 2, abs(s.z - focus))
                            for y, x in sites
                        ),
                        start=zero,
                    )
                    * (s.electrons * self.area / len(sites))
                    for s in self.sources
                )
                for focus in self.focuses
                for sites in self.sites
            )
            unilluminated = tuple(sum(row, start=zero) for row in contributions)
            targets = tuple(
                sum(
                    (
                        c * illumination(j, k, o, p)
                        for j, c in enumerate(contributions[k * len(self.sites) + pixel])
                    ),
                    start=zero,
                )
                for o in range(len(self.carriers))
                for p in range(len(self.phases[0]))
                for k in range(len(self.focuses))
                for pixel in range(len(self.sites))
            )

            def project(value: Interval) -> Interval:
                return Interval(
                    Interval.rational(Fraction(value.lo), digits).lo,
                    Interval.rational(Fraction(value.hi), digits).hi,
                    digits,
                )

            peak = Interval(
                max(u.lo for u in unilluminated), max(u.hi for u in unilluminated), working
            )
            return tuple(project(t) for t in targets), project(peak)

        return Reference(shape, evaluate)


def optical_arguments() -> dict[str, Any]:
    """Retained binary64 optical constants from the public fixed recipe."""
    return {
        "detector_spacing_um_zyx": (0.125, 0.08, 0.08),
        "source_refinement_zyx": (2, 2, 2),
        "carriers_yx_per_um": np.array([[0.0, 2.459016393442623]]),
        "phases_rad": np.array([[0.0]]),
        "beam_amplitudes": (0.7071067811865476, 0.565685424949238, 0.4242640687119285),
        "excitation_um": 0.488,
        "emission_um": 0.525,
        "refractive_index": 1.515,
        "detection_na": 1.4,
        "pupil_order": 128,
        "pixel_subsamples_yx": (2, 2),
    }


def composition_case() -> tuple[dict[str, Any], dict[str, Any], NDArray[np.float64], Geometry]:
    """Two small finite spheres; exact rational membership and rounded weights."""
    catalogue = np.array([[0.125, 0.08, 0.12, 0.05, 1.0], [0.15625, 0.06, 0.06, 0.03, 2.5]])
    source_args: dict[str, Any] = {
        "catalogue": catalogue,
        "detector_shape_zyx": (2, 2, 3),
        "detector_spacing_um_zyx": (0.125, 0.08, 0.08),
        "source_refinement_zyx": (2, 2, 2),
    }
    dz, dy, dx = map(exact, (0.125, 0.08, 0.08))
    cells = tuple(
        (
            z,
            y,
            x,
            dz * Fraction(2 * z + 1, 4),
            dy * Fraction(2 * y + 1, 4),
            dx * Fraction(2 * x + 1, 4),
        )
        for z in range(4)
        for y in range(4)
        for x in range(6)
    )
    predicted = np.zeros((4, 4, 6))
    for row in catalogue:
        cz, cy, cx, radius, brightness = map(lambda v: exact(float(v)), row)
        occupied = [
            (z, y, x)
            for z, y, x, rz, ry, rx in cells
            if (rz - cz) ** 2 + (ry - cy) ** 2 + (rx - cx) ** 2 <= radius**2
        ]
        assert occupied
        increment = exact(float(brightness / len(occupied)))
        for index in occupied:
            predicted[index] = float(exact(float(predicted[index])) + increment)
    sources = tuple(
        Source(rz, ry, rx, exact(float(predicted[z, y, x])))
        for z, y, x, rz, ry, rx in cells
        if predicted[z, y, x] != 0
    )
    sites = tuple(
        tuple(
            (dy * (y + Fraction(2 * sy + 1, 4)), dx * (x + Fraction(2 * sx + 1, 4)))
            for sy in range(2)
            for sx in range(2)
        )
        for y in range(2)
        for x in range(3)
    )
    args = optical_arguments()
    geometry = Geometry(
        sources,
        (dz / 2, 3 * dz / 2),
        sites,
        (2, 3),
        dy * dx,
        ((0.0, 2.459016393442623),),
        ((0.0,),),
        args["beam_amplitudes"],
        0.488,
        0.525,
        1.515,
        1.4,
    )
    return source_args, args, predicted, geometry


def oscillatory_case() -> tuple[dict[str, Any], Geometry]:
    """Two complete pixels, d=-128 um, beta=1; distinguish finite pupil rules."""
    args = optical_arguments()
    args.update(
        source_e=np.array([[[1.0, 0.0]], [[0.0, 0.0]]]),
        detector_spacing_um_zyx=(512.0, 0.125, 0.25),
        source_refinement_zyx=(2, 1, 1),
        pixel_subsamples_yx=(1, 1),
        carriers_yx_per_um=np.array([[0.125, -0.25]]),
        phases_rad=np.array([[0.2, -1.1]]),
        beam_amplitudes=(4.0, 2.0, 1.0),
        excitation_um=0.5,
        emission_um=1.0,
        refractive_index=1.0,
        detection_na=1.0,
    )
    geometry = Geometry(
        (Source(Fraction(128), Fraction(1, 16), Fraction(1, 8), Fraction(1)),),
        (Fraction(256),),
        (((Fraction(1, 16), Fraction(1, 8)),), ((Fraction(1, 16), Fraction(3, 8)),)),
        (1, 2),
        Fraction(1, 32),
        ((0.125, -0.25),),
        ((0.2, -1.1),),
        (4.0, 2.0, 1.0),
        0.5,
        1.0,
        1.0,
        1.0,
    )
    return args, geometry


def enclosure_width(value: Interval) -> Fraction:
    """Exact width, without ambient Decimal subtraction rounding."""
    return Fraction(value.hi) - Fraction(value.lo)


def qualify_reference(reference: Reference) -> Bounds:
    """Require complete tight mu/T enclosures before product comparisons."""
    targets, peak = reference.evaluate(40)
    assert len(targets) == math.prod(reference.shape)
    assert peak.lo > Decimal(0)
    budget = Fraction(peak.lo) / 10**20
    if max(enclosure_width(v) for v in (*targets, peak)) >= budget:
        raise OracleInconclusive("reference width does not resolve 1e-20*T on its declared example")
    return targets, peak
