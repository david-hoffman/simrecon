"""Independent finite bounds for supplemental dark and enormous-field calls."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable
from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Bounds,
    Interval,
    Reference,
    bessel_from_square,
    exact,
    pi_interval,
    sin_cos,
)

DARK_WEIGHT = float.fromhex("0x1.d6cdb882e129ap-5")


def base_arguments() -> dict[str, Any]:
    return {
        "source_e": np.ones((1, 1, 1)),
        "detector_spacing_um_zyx": (1, 1, 1),
        "source_refinement_zyx": (1, 1, 1),
        "carriers_yx_per_um": np.zeros((1, 2)),
        "phases_rad": np.zeros((1, 1)),
        "beam_amplitudes": (1, 0, 0),
        "excitation_um": 0.5,
        "emission_um": 1,
        "refractive_index": 1,
        "detection_na": 1,
        "pupil_order": 1,
        "pixel_subsamples_yx": (1, 1),
    }


def finite_precision_arguments(case: str) -> dict[str, Any]:
    args = base_arguments()
    if case == "dark":
        source = np.full((4, 16, 16), DARK_WEIGHT)
        source[0, 0, 0] = 1
        args.update(
            source_e=source,
            detector_spacing_um_zyx=(1e6, 0.125, 0.125),
            phases_rad=np.array([[math.pi]]),
            beam_amplitudes=(2, 1, 1),
            pupil_order=2,
        )
    else:
        assert case == "huge"
        args.update(
            source_e=np.ones((4, 16, 16)),
            detector_spacing_um_zyx=(1, 1e89, 1e89),
        )
    return args


def outward(value: Interval, digits: int) -> Interval:
    return Interval(
        Interval.rational(Fraction(value.lo), digits).lo,
        Interval.rational(Fraction(value.hi), digits).hi,
        digits,
    )


@cache
def dark_reference(shape: tuple[int, int, int] = (4, 16, 16)) -> Reference:
    """Uniform weight plus one corner excess, exact Q=2 pairwise pupil sum.

    h(r,d)=B(r)+C(r)*cos(omega*d/Dz). Sum the uniform component using
    lateral squared-displacement multiplicities and an axial cosine sum;
    then add the one corner excess. No periodic image or spatial cutoff.
    """
    nz, ny, nx = shape
    weight = exact(DARK_WEIGHT)
    spacing = Fraction(1, 8)
    dz = exact(1e6)
    counts = tuple(
        Counter((y - jy) ** 2 + (x - jx) ** 2 for jy in range(ny) for jx in range(nx))
        for y in range(ny)
        for x in range(nx)
    )

    @cache
    def evaluate(digits: int) -> Bounds:
        working = digits + 20
        pi = pi_interval(working)
        zero = Interval.rational(0, working)
        half = Interval.rational(Fraction(1, 2), working)
        offset = Interval.rational(Fraction(1, 12), working).sqrt()
        low, high = half - offset, half + offset
        difference = (1 - low).sqrt() - (1 - high).sqrt()
        omega = 2 * pi * dz * difference
        cosines = tuple(sin_cos(k * omega)[1] for k in range(nz))

        @cache
        def radial(square_steps: int) -> tuple[Interval, Interval]:
            radius_squared = square_steps * spacing**2
            jm = bessel_from_square(pi.squared() * radius_squared * low)
            jp = bessel_from_square(pi.squared() * radius_squared * high)
            return pi * (jm.squared() + jp.squared()) / 4, pi * jm * jp / 2

        lateral = tuple(
            (
                sum((count * radial(r)[0] for r, count in row.items()), start=zero),
                sum((count * radial(r)[1] for r, count in row.items()), start=zero),
            )
            for row in counts
        )
        unilluminated = []
        for k in range(nz):
            axial_cosine = sum((cosines[abs(j - k)] for j in range(nz)), start=zero)
            for y in range(ny):
                for x in range(nx):
                    bsum, csum = lateral[y * nx + x]
                    bcorner, ccorner = radial(y * y + x * x)
                    unilluminated.append(
                        spacing**2
                        * (
                            weight * (nz * bsum + axial_cosine * csum)
                            + (1 - weight) * (bcorner + cosines[k] * ccorner)
                        )
                    )
        # phi is the exact binary math.pi, not mathematical pi. The stable
        # identity (2+2*cos(phi))^2/6 = (8/3)*sin((phi-pi)/2)^4 avoids cancellation.
        delta = Interval.rational(exact(math.pi), working) - pi
        sine = sin_cos(delta / 2)[0]
        illumination = Fraction(8, 3) * sine.squared().squared()
        values = tuple(outward(u * illumination, digits) for u in unilluminated)
        peak = outward(
            Interval(max(u.lo for u in unilluminated), max(u.hi for u in unilluminated), working),
            digits,
        )
        return values, peak

    return Reference((1, 1, nz, ny, nx), evaluate)


@cache
def huge_reference() -> Reference:
    """Positive matched cells plus a certified bound on every off-axis term.

    DLMF 10.17.1/.3 and 10.17(iii), nu=0, one term in each series, give
    |P| <= 1+9/(128*x^2), |Q| <= 1/(8*x)+225/(3072*x^3).
    For x>=1, 2/3*(1+9/128+1/8+225/3072)^2 < 2; pi>3 implies J0(x)^2<2/x.
    Here x>=sqrt(2)*pi*D>4*D and pi<4, so h<2/D off axis.
    https://dlmf.nist.gov/10.17#iii
    """
    spacing = exact(1e89)
    assert spacing > 1
    bound_sum = 1 + Fraction(9, 128) + Fraction(1, 8) + Fraction(225, 3072)
    assert Fraction(2, 3) * bound_sum**2 < 2

    @cache
    def evaluate(digits: int) -> Bounds:
        base = 4 * pi_interval(digits) * spacing**2
        # 4*(256-1) off-axis source cells, each area*2/D <= 2*D.
        upper = base + 2040 * spacing
        enclosure = Interval(base.lo, upper.hi, digits)
        return (enclosure,) * 1024, enclosure

    return Reference((1, 1, 4, 16, 16), evaluate)


def positive_ldexp_return(
    genuine: Callable[..., Any], value: Any, exponent: Any, *values: Any, **keywords: Any
) -> Any:
    """Explicit public fault: nonpositive exponents stay genuine; positive go inf.

    Respect broadcasting, supplied out storage and where=False preservation.
    Clip only the intentionally corrupted positive exponents before the genuine
    call, avoiding an unrelated overflow warning from the stimulus itself.
    """
    active = np.logical_and(np.greater(exponent, 0), keywords.get("where", True))
    if not np.any(active):
        return genuine(value, exponent, *values, **keywords)
    result = genuine(value, np.minimum(exponent, 0), *values, **keywords)
    if isinstance(result, np.ndarray):
        np.copyto(result, np.inf, where=active)
        return result
    return np.asarray(result).dtype.type(np.inf) if np.any(active) else result
