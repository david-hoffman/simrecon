"""Supplemental after implementation began; initial B3 proofs remain frozen."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from importlib import import_module
from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from simulation_optics_aggregate_fixture import (
    aggregate_reference,
    arguments,
    refinement_arguments,
    refinement_reference,
)
from simulation_optics_fixture import compare_reference, exact

expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


@pytest.mark.parametrize("reverse_sides", [False, True], ids=["direct", "reversed-sides"])
def test_dense_asymmetric_volume_matches_complete_finite_sum(reverse_sides: bool) -> None:
    """Every output entry has the unchanged absolute allowance from independent U.

    Negating both q and phi and exchanging a+ with a- leaves the complex field
    unchanged. Both legal inputs must satisfy the same independent target; no
    comparison between two product outputs supplies numerical truth.
    """
    args = arguments(reverse_sides=reverse_sides)
    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
    assert type(actual) is np.ndarray
    assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
    assert actual.flags.c_contiguous and actual.flags.writeable
    assert np.isfinite(actual).all() and (actual >= 0).all()
    assert not any(np.shares_memory(actual, a) for a in arrays)
    reference = aggregate_reference()
    assert actual.shape == reference.shape == (2, 3, 2, 2, 3)
    compare_reference(tuple(exact(float(value)) for value in actual.flat), reference)


@pytest.mark.parametrize(
    "beams",
    [(4.0, 2.0, 1.0), (1.0, 0.0, 0.0), (0.0, 2.0, 1.0), (2.0, 1.0, 0.0)],
    ids=["unequal", "central-only", "sides-only", "central-one-side"],
)
def test_complete_independent_refinements_and_beam_positives(
    beams: tuple[float, float, float],
) -> None:
    """The same full finite geometry must retain each remaining beam harmonic."""
    args = refinement_arguments(beams)
    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
    assert type(actual) is np.ndarray
    assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
    assert actual.flags.c_contiguous and actual.flags.writeable
    assert np.isfinite(actual).all() and (actual >= 0).all()
    assert not any(np.shares_memory(actual, a) for a in arrays)
    reference = refinement_reference(beams)
    assert actual.shape == reference.shape == (2, 3, 3, 5, 10)
    compare_reference(tuple(exact(float(value)) for value in actual.flat), reference)
