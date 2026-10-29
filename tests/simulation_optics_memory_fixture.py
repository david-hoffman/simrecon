"""Public finite geometry for preserving complete optical source accumulation."""

from __future__ import annotations

from fractions import Fraction
from functools import cache
from typing import Any

import numpy as np

from simulation_optics_fixture import (
    Reference,
    Source,
    exact,
    finite_images,
)

SPACING = (0.625, 0.25, 0.1875)
CARRIERS = ((0.83, -0.61), (-0.47, 0.89))
PHASES = ((0.23, -0.87, 2.4), (-0.53, 1.31, -2.2))


def weight(z: int, y: int, x: int) -> Fraction:
    """Strictly positive, nonseparable integrated electrons, exact in float64."""
    return Fraction(1 + (7 * z + 3 * y + 5 * x + z * y + 2 * y * x + 3 * z * x) % 37, 8)


def arguments(*, reverse_sides: bool = False) -> dict[str, Any]:
    """Three source subplanes per focus; two equivalent signed-carrier inputs."""
    sign = -1 if reverse_sides else 1
    return {
        "source_e": np.array(
            [[[float(weight(z, y, x)) for x in range(4)] for y in range(2)] for z in range(9)]
        ),
        "detector_spacing_um_zyx": SPACING,
        "source_refinement_zyx": (3, 2, 2),
        "carriers_yx_per_um": sign * np.array(CARRIERS),
        "phases_rad": sign * np.array(PHASES),
        "beam_amplitudes": (4.0, 1.0, 2.0) if reverse_sides else (4.0, 2.0, 1.0),
        "excitation_um": 0.5,
        "emission_um": 0.625,
        "refractive_index": 1.25,
        "detection_na": 0.75,
        "pupil_order": 2,
        "pixel_subsamples_yx": (2, 3),
    }


@cache
def reference() -> Reference:
    """All 72 sites and all pixel sites in exact half-cell coordinates."""
    dz, dy, dx = map(exact, SPACING)
    sources = tuple(
        Source(
            dz * Fraction(2 * z + 1, 6),
            dy * Fraction(2 * y + 1, 4),
            dx * Fraction(2 * x + 1, 4),
            weight(z, y, x),
        )
        for z in range(9)
        for y in range(2)
        for x in range(4)
    )
    sites = tuple(
        tuple(
            (dy * (y + Fraction(2 * sy + 1, 4)), dx * (x + Fraction(2 * sx + 1, 6)))
            for sy in range(2)
            for sx in range(3)
        )
        for y in range(1)
        for x in range(2)
    )
    return finite_images(
        sources,
        (dz / 2, 3 * dz / 2, 5 * dz / 2),
        sites,
        (1, 2),
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
