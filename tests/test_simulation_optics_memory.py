"""Blind memory-preservation examples through the complete public operator."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from importlib import import_module
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from simulation_optics_fixture import compare_reference, exact
from simulation_optics_memory_fixture import (
    LARGER_FOCUS_INDICES,
    LARGER_PIXELS,
    arguments,
    larger_arguments,
    larger_necessary_reference,
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
    actual = call(arguments())
    target = reference()
    assert actual.shape == target.shape == (2, 3, 3, 2, 3)
    compare_reference(tuple(exact(float(value)) for value in actual.flat), target)


def test_returned_image_survives_later_different_source_call() -> None:
    """Reducing temporary storage must not reuse a caller's earlier output."""
    args = arguments()
    first = call(args)
    before = first.tobytes()
    # Integrated weights scale the finite equation linearly. Distinct calls
    # still own their outputs independently, even at identical output shape.
    args["source_e"] = 2 * args["source_e"]
    second = call(args)
    assert first.tobytes() == before
    assert not np.shares_memory(first, second)
    second.fill(0)
    assert first.tobytes() == before


def test_larger_axial_catalogue_satisfies_complete_source_necessary_bound() -> None:
    """Sample fixed entries with every source and a proved global T upper bound.

    Supplemental after implementation: this is a necessary accuracy condition,
    not certification of the sharper 1e-5*T bound over the full output image.
    """
    target = larger_necessary_reference()
    actual = call(larger_arguments())
    assert actual.shape == (2, 3, 25, 32, 32)
    observations = tuple(
        exact(float(actual[o, p, k, y, x]))
        for o in range(2)
        for p in range(3)
        for k in LARGER_FOCUS_INDICES
        for y, x in LARGER_PIXELS
    )
    compare_reference(observations, target)
