"""Supplemental exact-input closed forms for extreme finite optical phases."""

from __future__ import annotations

from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Bounds,
    Interval,
    OracleInconclusive,
    Reference,
    exact,
    pi_interval,
    sin_cos,
)


def project(value: Interval, digits: int) -> Interval:
    """Project endpoint rationals outward, with no assumed rounding allowance."""
    return Interval(
        Interval.rational(Fraction(value.lo), digits).lo,
        Interval.rational(Fraction(value.hi), digits).hi,
        digits,
    )


def resolved_cosine(angle: Interval, requested: int) -> Interval:
    """Certify phase resolution before integer-turn reduction and Taylor sums."""
    if Fraction(angle.hi) - Fraction(angle.lo) >= Fraction(1, 10 ** (requested + 10)):
        raise OracleInconclusive("precision-reference phase enclosure is unresolved")
    return sin_cos(angle)[1]


@cache
def axial_precision_reference() -> Reference:
    """Q=1 on-axis detection, integer lateral cycles, two axial focuses."""
    excitation, q, dz = exact(1e-308), exact(5e307), exact(1e308)
    assert (q / 2).denominator == 1
    k0 = 1 / excitation
    assert q <= k0

    @cache
    def evaluate(digits: int) -> Bounds:
        # Phase magnitude is below 1e617; +700 leaves over 80 guard digits.
        # Soundness is still supplied by intervals and the phase-width check.
        working = digits + 700
        pi = pi_interval(working)
        kappa = Interval.rational(k0, working) - Interval.rational(k0**2 - q**2, working).sqrt()
        cosine = resolved_cosine(2 * pi * kappa * dz, digits)
        values = (project(3 * pi, digits), project(pi * (5 + 4 * cosine) / 3, digits))
        return values, project(pi, digits)

    return Reference((1, 1, 2, 1, 1), evaluate)


@cache
def pupil_precision_reference() -> Reference:
    """Two equal pupil phasors at the exact displacement -float(1e20)/4."""
    d = -exact(1e20) / 4

    @cache
    def evaluate(digits: int) -> Bounds:
        # Phase magnitude is below 1e21; +40 gives over 19 guard digits.
        working = digits + 40
        pi = pi_interval(working)
        half = Interval.rational(Fraction(1, 2), working)
        offset = Interval.rational(Fraction(1, 12), working).sqrt()
        difference = (half + offset).sqrt() - (half - offset).sqrt()
        cosine = resolved_cosine(2 * pi * d * difference, digits)
        target = project(pi * (1 + cosine) / 2, digits)
        return (target,), target

    return Reference((1, 1, 1, 1, 1), evaluate)


def precision_case(case: str) -> tuple[dict[str, Any], Reference | None]:
    """Public arguments; None marks only an independently unrepresentable output."""
    args: dict[str, Any] = {
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
    if case == "unrepresentable-pupil":
        args.update(
            detector_spacing_um_zyx=(1, 1e308, 1),
            emission_um=1e-100,
            pixel_subsamples_yx=(3, 1),
        )
        return args, None
    if case == "axial-precision":
        args.update(
            source_e=np.array([[[1.0]], [[0.0]]]),
            detector_spacing_um_zyx=(1e308, 1, 1),
            carriers_yx_per_um=np.array([[0.0, 5e307]]),
            beam_amplitudes=(1, 1, 1),
            excitation_um=1e-308,
        )
        return args, axial_precision_reference()
    assert case == "pupil-precision"
    args.update(
        source_e=np.array([[[1.0]], [[0.0]]]),
        detector_spacing_um_zyx=(1e20, 1, 1),
        source_refinement_zyx=(2, 1, 1),
        pupil_order=2,
    )
    return args, pupil_precision_reference()
