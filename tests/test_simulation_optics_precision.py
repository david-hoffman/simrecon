"""Supplemental precision/range evidence; accurate alternatives remain legal."""

from __future__ import annotations

import sys
import warnings
from collections.abc import Callable
from fractions import Fraction
from importlib import import_module
from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from simrecon import SimreconError
from simulation_optics_fixture import compare_reference, exact
from simulation_optics_precision_fixture import precision_case

expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


@pytest.mark.parametrize("case", ["unrepresentable-pupil", "axial-precision", "pupil-precision"])
def test_precision_obstructions_allow_only_range_or_accurate_success(case: str) -> None:
    args, reference = precision_case(case)
    if reference is None:
        # The central of three y-sites is exactly on axis. All terms are
        # nonnegative; I=1 and one output entry imply mu=T. With pi>3,
        # even (1-1e-5)*mu exceeds the largest finite float64.
        lower = exact(1e308) / exact(1e-100) ** 2
        assert lower * Fraction(99999, 100000) > exact(sys.float_info.max)
    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        except SimreconError as error:
            assert error.code == "simulation_optics_range"
        else:
            assert reference is not None, "the exact output is unrepresentable within its allowance"
            assert type(actual) is np.ndarray
            assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
            assert actual.flags.c_contiguous and actual.flags.writeable
            assert np.isfinite(actual).all() and (actual >= 0).all()
            assert not any(np.shares_memory(actual, a) for a in arrays)
            assert actual.shape == reference.shape
            compare_reference(tuple(exact(float(value)) for value in actual.flat), reference)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
