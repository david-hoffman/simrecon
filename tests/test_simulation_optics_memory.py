"""Blind memory-preservation examples through the complete public operator."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from simulation_optics_aggregate_fixture import large_arguments, large_reference
from simulation_optics_fixture import compare_reference, exact
from simulation_optics_memory_fixture import (
    arguments,
    reference,
)

expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


def call(args: dict[str, Any]) -> NDArray[np.float64]:
    """Observe the public output and preserve all caller-owned array state."""
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
    assert not any(np.shares_memory(actual, value) for value in arrays)
    return actual


def test_nonseparable_sources_preserve_defocus_across_three_focus_planes() -> None:
    """Require every source in a bright Q2 volume with unequal beam amplitudes."""
    args = arguments()
    actual = call(args)
    target = reference()
    assert actual.shape == target.shape == (2, 3, 3, 1, 2)
    compare_reference(tuple(exact(float(value)) for value in actual.flat), target)
    before = actual.tobytes()
    # Identical complete inputs prove deterministic evaluation and independent storage.
    second = call(args)
    assert np.array_equal(actual, second)
    assert actual.tobytes() == before
    assert not np.shares_memory(actual, second)
    second.fill(0)
    assert actual.tobytes() == before


def test_larger_axial_catalogue_satisfies_complete_source_necessary_bound() -> None:
    """Every output includes all 17 source planes and the exact global T."""
    target = large_reference()
    args = large_arguments()
    source = args["source_e"]
    assert source.shape == (17, 2, 2) and np.all(source > 0)
    assert np.unique(source[-1]).size > 1
    actual = call(args)
    assert actual.shape == target.shape == (2, 3, 17, 1, 1)
    compare_reference(tuple(exact(float(value)) for value in actual.flat), target)
