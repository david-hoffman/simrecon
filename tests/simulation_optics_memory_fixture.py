"""Public finite geometry for preserving complete optical source accumulation."""

from __future__ import annotations

from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Bounds,
    Interval,
    Reference,
    Source,
    exact,
    finite_images,
    pi_interval,
)

SPACING = (0.625, 0.25, 0.1875)
CARRIERS = ((0.83, -0.61), (-0.47, 0.89))
PHASES = ((0.23, -0.87, 2.4), (-0.53, 1.31, -2.2))


def weight(z: int, y: int, x: int) -> Fraction:
    """Strictly positive, nonseparable integrated electrons, exact in float64."""
    return Fraction(1 + (7 * z + 3 * y + 5 * x + z * y + 2 * y * x + 3 * z * x) % 37, 8)


def arguments() -> dict[str, Any]:
    """Three source subplanes per focus interval; independent pixel sampling."""
    return {
        "source_e": np.array(
            [[[float(weight(z, y, x)) for x in range(6)] for y in range(4)] for z in range(9)]
        ),
        "detector_spacing_um_zyx": SPACING,
        "source_refinement_zyx": (3, 2, 2),
        "carriers_yx_per_um": np.array(CARRIERS),
        "phases_rad": np.array(PHASES),
        "beam_amplitudes": (4.0, 2.0, 1.0),
        "excitation_um": 0.5,
        "emission_um": 0.625,
        "refractive_index": 1.25,
        "detection_na": 0.75,
        "pupil_order": 2,
        "pixel_subsamples_yx": (2, 3),
    }


@cache
def reference() -> Reference:
    """All 216 sites and all pixel sites in exact half-cell coordinates."""
    dz, dy, dx = map(exact, SPACING)
    sources = tuple(
        Source(
            dz * Fraction(2 * z + 1, 6),
            dy * Fraction(2 * y + 1, 4),
            dx * Fraction(2 * x + 1, 4),
            weight(z, y, x),
        )
        for z in range(9)
        for y in range(4)
        for x in range(6)
    )
    sites = tuple(
        tuple(
            (dy * (y + Fraction(2 * sy + 1, 4)), dx * (x + Fraction(2 * sx + 1, 6)))
            for sy in range(2)
            for sx in range(3)
        )
        for y in range(2)
        for x in range(3)
    )
    return finite_images(
        sources,
        (dz / 2, 3 * dz / 2, 5 * dz / 2),
        sites,
        (2, 3),
        dy * dx,
        CARRIERS,
        PHASES,
        beams=(4.0, 2.0, 1.0),
        excitation=0.5,
        emission=0.625,
        index=1.25,
        aperture=0.75,
        order=2,
    )


LARGER_SPACING = (0.625, 0.125, 0.125)
LARGER_FOCUS_INDICES = (0, 6, 12, 18, 24)
LARGER_PIXELS = ((0, 0), (15, 16), (16, 15), (31, 31))


def larger_catalogue() -> tuple[tuple[int, int, int, Fraction], ...]:
    """Three distinct integrated-electron sources on each of fifty planes."""
    return tuple(
        (z, y, x, Fraction(1 + (7 * z + 5 * label) % 23, 4))
        for z in range(50)
        for label, (y, x) in enumerate(
            ((30 + z % 3, 29 + z % 5), (33, 30 + (2 * z) % 4), (29 + z % 2, 34))
        )
    )


def larger_arguments() -> dict[str, Any]:
    """Build a finite 15.625 by 4 by 4 um box without exterior sources."""
    source = np.zeros((50, 64, 64))
    for z, y, x, electrons in larger_catalogue():
        source[z, y, x] = float(electrons)
    return {
        "source_e": source,
        "detector_spacing_um_zyx": LARGER_SPACING,
        "source_refinement_zyx": (2, 2, 2),
        "carriers_yx_per_um": np.array(CARRIERS),
        "phases_rad": np.array(PHASES),
        "beam_amplitudes": (4.0, 2.0, 1.0),
        "excitation_um": 0.5,
        "emission_um": 1.0,
        "refractive_index": 1.25,
        "detection_na": 0.75,
        "pupil_order": 2,
        "pixel_subsamples_yx": (2, 2),
    }


def larger_sources() -> tuple[Source, ...]:
    """Every nonzero source at its original global half-cell coordinate."""
    dz, dy, dx = map(exact, LARGER_SPACING)
    return tuple(
        Source(
            dz * Fraction(2 * z + 1, 4),
            dy * Fraction(2 * y + 1, 4),
            dx * Fraction(2 * x + 1, 4),
            electrons,
        )
        for z, y, x, electrons in larger_catalogue()
    )


def larger_sample_target(sources: tuple[Source, ...]) -> Reference:
    """Exact sampled finite targets; its cropped U maximum is NOT global T."""
    dz, dy, dx = map(exact, LARGER_SPACING)
    sites = tuple(
        tuple(
            (dy * (y + Fraction(2 * sy + 1, 4)), dx * (x + Fraction(2 * sx + 1, 4)))
            for sy in range(2)
            for sx in range(2)
        )
        for y, x in LARGER_PIXELS
    )
    return finite_images(
        sources,
        tuple(dz * Fraction(2 * k + 1, 2) for k in LARGER_FOCUS_INDICES),
        sites,
        (1, len(sites)),  # Packing selected pixels, not the detector shape.
        dy * dx,
        CARRIERS,
        PHASES,
        beams=(4.0, 2.0, 1.0),
        excitation=0.5,
        emission=1.0,
        index=1.25,
        aperture=0.75,
        order=2,
    )


def larger_peak_upper_bound(digits: int) -> Interval:
    """Global T <= area*pi*R^2*total electrons, since |J0| and |A_Q| <= 1."""
    total = sum((row[3] for row in larger_catalogue()), Fraction(0))
    return pi_interval(digits) * (Fraction(9, 1024) * total)


@cache
def larger_necessary_reference() -> Reference:
    """Necessary sampled-entry condition with GLOBAL upper bound, not exact T.

    This may miss errors between 1e-5*T and 1e-5*B, where B>=T. It cannot
    reject a contract-permitted output on accuracy grounds. Existing complete
    image oracles retain the sharper contract allowance and unsampled proof.
    """
    sampled = larger_sample_target(larger_sources())

    @cache
    def evaluate(digits: int) -> Bounds:
        values, _cropped_peak = sampled.evaluate(digits)
        return values, larger_peak_upper_bound(digits)

    return Reference(sampled.shape, evaluate)
