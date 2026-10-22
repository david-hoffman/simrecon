"""Certified exact-coordinate finite sums; no product or SciPy output oracle."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext
from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Bounds,
    Interval,
    OracleInconclusive,
    Reference,
    bessel_from_square,
    exact,
    pi_interval,
    sin_cos,
)

REFINEMENT = 79980
EMISSION = float.fromhex("0x1.7dd61e9aba872p-33")


def arguments(refinement: int, emission: float) -> dict[str, Any]:
    source = np.zeros((1, refinement, 1))
    source[0, -1, 0] = 1
    return {
        "source_e": source,
        "detector_spacing_um_zyx": (1, 1, 1),
        "source_refinement_zyx": (1, refinement, 1),
        "carriers_yx_per_um": np.zeros((1, 2)),
        "phases_rad": np.zeros((1, 1)),
        "beam_amplitudes": (1, 0, 0),
        "excitation_um": 0.5,
        "emission_um": emission,
        "refractive_index": 1,
        "detection_na": 1,
        "pupil_order": 1,
        "pixel_subsamples_yx": (refinement - 1, 1),
    }


def asymptotic_square(x: Interval) -> Interval:
    """DLMF 10.17.1/.3/(iii), nu=0, one term per P/Q series, x>=1.

    P=1+rhoP, |rhoP|<=9/(128*x^2).
    Q=-1/(8*x)+rhoQ, |rhoQ|<=225/(3072*x^3).
    https://dlmf.nist.gov/10.17
    """
    if x.lo < 1:
        raise OracleInconclusive("asymptotic reference requires x>=1")
    digits = x.digits
    one = Interval.rational(1, digits)
    pi = pi_interval(digits)
    ep = (Interval.rational(Fraction(9, 128), digits) / x.squared()).hi
    eq = (Interval.rational(Fraction(225, 3072), digits) / (x.squared() * x)).hi
    p = one.padded(ep)
    q = (-one / (8 * x)).padded(eq)
    sine, cosine = sin_cos(x - pi / 4)
    return 2 * (cosine * p - sine * q).squared() / (pi * x)


def squared_bessel(x: Interval) -> Interval:
    if x.hi <= 16:
        return bessel_from_square(x.squared() / 4).squared()
    return asymptotic_square(x)


def reciprocal_sums(
    refinement: int, start: int, stop: int, digits: int
) -> tuple[Interval, Interval]:
    """Enclose both complete finite sums of 1/d and 1/d^2, d=1+2*f*m."""
    ends = []
    for rounding in (ROUND_FLOOR, ROUND_CEILING):
        with localcontext() as context:
            context.prec = digits
            context.rounding = rounding
            first, second = Decimal(0), Decimal(0)
            for m in range(start, stop):
                denominator = 1 + 2 * refinement * m
                first += Decimal(1) / Decimal(denominator)
                second += Decimal(1) / Decimal(denominator * denominator)
            ends.append((first, second))
    return (
        Interval(ends[0][0], ends[1][0], digits),
        Interval(ends[0][1], ends[1][1], digits),
    )


def tail_enclosure(refinement: int, start: int, stop: int, x0: Interval) -> Interval:
    """Bound every remaining squared Bessel term, without treating it as zero.

    For x>=1, |J0(x)^2-(1+sin(2*x))/(pi*x)|<=1/x^2.
    The finite geometric partial sums of exp(2i*x_m) have modulus
    <=1/abs(sin(step)). Summation by parts with decreasing 1/x_m
    bounds the entire weighted oscillatory sum by 1/(abs(sin(step))*x_start).
    The nonoscillatory and squared-error sums are evaluated completely.
    """
    digits = x0.digits
    zero = Interval.rational(0, digits)
    if start == stop:
        return zero
    pi = pi_interval(digits)
    x_start = (1 + 2 * refinement * start) * x0
    if x_start.lo < 1:
        raise OracleInconclusive("tail reference requires all x>=1")
    sine = sin_cos(2 * refinement * x0)[0].absolute()
    if sine.lo <= 0:
        raise OracleInconclusive("oscillatory tail step cannot be separated from a full turn")
    first, second = reciprocal_sums(refinement, start, stop, digits)
    mean = first / (pi * x0)
    oscillation = Interval.rational(1, digits) / (pi * sine * x_start)
    remainder = second / x0.squared()
    enclosed = mean.padded((oscillation + remainder).hi)
    return Interval(max(Decimal(0), enclosed.lo), enclosed.hi, digits)


@cache
def certificate(refinement: int, emission: float, digits: int, prefix: int) -> Interval:
    """Exact geometry, directly enclosed prefix, certified complete tail."""
    pixels = refinement - 1
    assert refinement >= 2 and 1 <= prefix <= pixels
    working = digits + 20
    pi = pi_interval(working)
    wavelength = exact(emission)
    x0 = Interval.rational(2, working).sqrt() * pi / (2 * refinement * pixels * wavelength)
    total = sum(
        (squared_bessel((1 + 2 * refinement * m) * x0) for m in range(prefix)),
        start=Interval.rational(0, working),
    )
    total += tail_enclosure(refinement, prefix, pixels, x0)
    target = pi * total / (pixels * wavelength**2)
    return Interval(
        Interval.rational(Fraction(target.lo), digits).lo,
        Interval.rational(Fraction(target.hi), digits).hi,
        digits,
    )


@cache
def coordinate_reference(refinement: int, emission: float) -> Reference:
    @cache
    def evaluate(digits: int) -> Bounds:
        prefix = min(refinement - 1, 64 * max(1, digits // 40))
        bound = certificate(refinement, emission, digits, prefix)
        if digits > 40:
            previous = evaluate(digits // 2)[0][0]
            bound = Interval(max(bound.lo, previous.lo), min(bound.hi, previous.hi), digits)
            if bound.lo > bound.hi:
                raise OracleInconclusive("independent finite certificates have empty intersection")
        # Central-only illumination and one output entry give T=mu exactly.
        return (bound,), bound

    return Reference((1, 1, 1, 1, 1), evaluate)
