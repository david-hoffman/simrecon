"""Independent finite-source expectations, using declared sites rather than a search.

All distances are exact rational numbers in micrometres.  Conversion of a
Fraction to Python float supplies round-to-nearest/even binary64.  These helpers
never import the product and never discover occupied sites from its output.
"""

from fractions import Fraction
from itertools import product

import numpy as np
from numpy.typing import NDArray

type Site = tuple[int, int, int]
type Shape = tuple[int, int, int]


def exact(value: int | float) -> Fraction:
    """Interpret a normalized binary64 value exactly, not its decimal spelling."""
    return Fraction(value)


def distance_squared(
    site: Site,
    *,
    center: tuple[float, float, float],
    spacing: tuple[float, float, float],
    refinement: Shape,
) -> Fraction:
    """Check one explicitly declared site's public geometric relation."""
    return sum(
        (
            (Fraction(2 * index + 1, 2) * exact(step) / factor - exact(origin)) ** 2
            for index, step, factor, origin in zip(site, spacing, refinement, center, strict=True)
        ),
        Fraction(0),
    )


def verify_declared_sites(
    shape: Shape,
    sites: frozenset[Site],
    *,
    center: tuple[float, float, float],
    radius: float,
    spacing: tuple[float, float, float],
    refinement: Shape,
) -> None:
    """Certify a small hand enumeration, including all excluded lattice sites.

    This bounded exhaustive control is used only on the tiny declared examples;
    it is not a proposed production candidate-selection/search algorithm.
    """
    lattice = product(range(shape[0]), range(shape[1]), range(shape[2]))
    assert sites <= frozenset(lattice)
    for site in product(range(shape[0]), range(shape[1]), range(shape[2])):
        assert (
            distance_squared(site, center=center, spacing=spacing, refinement=refinement)
            <= exact(radius) ** 2
        ) == (site in sites)


def expected_weights(
    shape: Shape, rows: list[tuple[float, frozenset[Site]]]
) -> NDArray[np.float64]:
    """Round exact B/K once, then each exact addition in supplied row order."""
    result = np.zeros(shape, dtype=np.float64)
    for brightness, sites in rows:
        if brightness == 0:
            continue
        assert sites
        weight = float(exact(brightness) / len(sites))
        assert weight > 0
        for site in sites:
            result[site] = float(exact(float(result[site])) + exact(weight))
    return result


CROSS7: frozenset[Site] = frozenset(
    {(1, 1, 1), (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1), (1, 1, 0), (1, 1, 2)}
)
CENTER1: frozenset[Site] = frozenset({(1, 1, 1)})
ANISOTROPIC5: frozenset[Site] = frozenset({(1, 1, 1), (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1)})
OFF_GRID2: frozenset[Site] = frozenset({(0, 1, 1), (1, 1, 1)})
ONLY_SITE: frozenset[Site] = frozenset({(0, 0, 0)})
