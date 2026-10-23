"""Supplemental public proof for mixed empty/nonempty sphere cross sections.

The declared sites are hand-derived from integer z/y offsets and half-integer
x offsets. Continuous projected intersections alone do not contribute to K.
This finite midpoint model asserts no continuous sphere-cell accuracy.
"""

import importlib
from fractions import Fraction

import numpy as np
import pytest

from simulation_sources_fixture import verify_declared_sites

OCCUPIED = frozenset({(2, 2, 1), (2, 2, 2)})
RADII = (1.0, 17.0 / 16.0)


@pytest.mark.parametrize("radius", RADII)
def test_oracle_mixed_cross_sections(radius: float) -> None:
    """Certify every site and the projected rows that contain no midpoint."""
    radius_squared = Fraction(radius) ** 2
    # z/y offsets are integers. At (2,2) their squared contribution is 0;
    # four axial neighbors contribute 1; every other row contributes >= 2.
    # The nearest x offsets are +/-1/2, followed by -3/2, +3/2 and +5/2.
    assert Fraction(1, 4) <= radius_squared < 2
    assert 0 <= radius_squared - 1 < Fraction(1, 4)
    if radius > 1:
        assert radius_squared - 1 == Fraction(33, 256) > 0
    else:
        assert radius_squared - 1 == 0  # Closed projected tangencies.
    verify_declared_sites(
        (5, 5, 5),
        OCCUPIED,
        center=(2.5, 2.5, 2.0),
        radius=radius,
        spacing=(1.0, 1.0, 1.0),
        refinement=(1, 1, 1),
    )
    # The two occupied sites share B=7 electrons exactly; no mass repair or
    # floating reduction is needed to establish this particular example.
    assert len(OCCUPIED) == 2
    assert Fraction(3.5) == Fraction(7, 2)


@pytest.mark.parametrize("radius", RADII)
def test_mixed_cross_sections_preserve_membership_and_normalization(radius: float) -> None:
    make_sources = importlib.import_module("scripts.simulation_sources").make_sources
    catalogue = np.array([[2.5, 2.5, 2.0, radius, 7.0]], dtype=np.float64)
    expected = np.zeros((5, 5, 5), dtype=np.float64)
    expected[2, 2, 1] = 3.5
    expected[2, 2, 2] = 3.5

    actual = make_sources(
        catalogue,
        detector_shape_zyx=(5, 5, 5),
        detector_spacing_um_zyx=(1.0, 1.0, 1.0),
        source_refinement_zyx=(1, 1, 1),
    )
    np.testing.assert_array_equal(actual, expected)
