"""Supplemental finite source/pixel-coordinate accuracy, including legal range."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from importlib import import_module
from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from simrecon import SimreconError
from simulation_optics_coordinate_fixture import (
    EMISSION,
    REFINEMENT,
    arguments,
    coordinate_reference,
)
from simulation_optics_fixture import compare_reference, exact

expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


@pytest.mark.parametrize(
    "refinement,emission", [(4, 1.0), (REFINEMENT, EMISSION)], ids=["nearby", "fine-coordinate"]
)
def test_independent_source_and_pixel_coordinates(refinement: int, emission: float) -> None:
    args = arguments(refinement, emission)
    reference = coordinate_reference(refinement, emission)
    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        except SimreconError as error:
            # The diagnosed fine-coordinate case permits a concrete precision
            # refusal. The ordinary nearby control requires accurate success.
            assert refinement == REFINEMENT and emission == EMISSION
            assert error.code == "simulation_optics_range"
        else:
            assert type(actual) is np.ndarray
            assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
            assert actual.flags.c_contiguous and actual.flags.writeable
            assert np.isfinite(actual).all() and (actual >= 0).all()
            assert not any(np.shares_memory(actual, value) for value in arrays)
            assert actual.shape == reference.shape
            compare_reference(tuple(exact(float(value)) for value in actual.flat), reference)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
