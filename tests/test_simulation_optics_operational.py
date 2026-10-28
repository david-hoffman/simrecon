"""Explicit optional-SciPy fault stimuli and finite precision legal alternatives."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from fractions import Fraction
from importlib import import_module
from typing import Any, cast

import numpy as np
import pytest
from numpy.typing import NDArray
from scipy import special

from simrecon import SimreconError
from simulation_optics_fixture import (
    Reference,
    compare_reference,
    exact,
    on_axis_reference,
    pi_interval,
)
from simulation_optics_operational_fixture import (
    base_arguments,
    dark_reference,
    finite_precision_arguments,
    huge_reference,
    positive_ldexp_return,
)

# Import before injecting. A backend bound earlier may bypass the optional
# patched function; importing under a patch could contaminate later calls.
expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)


class DependencyProbeWarning(UserWarning):
    """Distinct unrelated warning stimulus; never an arithmetic warning."""


def assert_output(actual: NDArray[np.float64], args: dict[str, Any], reference: Reference) -> None:
    assert type(actual) is np.ndarray
    assert actual.dtype == np.dtype("float64") and actual.dtype.isnative
    assert actual.flags.c_contiguous and actual.flags.writeable
    assert np.isfinite(actual).all() and (actual >= 0).all()
    assert not any(
        np.shares_memory(actual, value) for value in args.values() if isinstance(value, np.ndarray)
    )
    assert actual.shape == reference.shape
    compare_reference(tuple(exact(float(value)) for value in actual.flat), reference)


@pytest.mark.parametrize("stimulus", ["memory", "warning", "nonfinite"])
def test_optional_public_scipy_fault_boundary(
    stimulus: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Backend use is optional; observed use binds the corresponding fault rule."""
    args = base_arguments()
    reference = on_axis_reference(
        (1, 1, 1, 1, 1), exact(1), exact(1), aperture=exact(1), emission=exact(1)
    )
    genuine = special.j0
    calls = 0

    def injected(*values: Any, **keywords: Any) -> Any:
        nonlocal calls
        calls += 1
        if stimulus == "memory":
            raise MemoryError("explicit optional dependency stimulus")
        if stimulus == "warning":
            warnings.warn(
                "explicit optional dependency stimulus", DependencyProbeWarning, stacklevel=1
            )
            return genuine(*values, **keywords)
        result = genuine(*values, **keywords)
        if isinstance(result, np.ndarray):
            result.fill(np.nan)
            return result
        return float("nan")

    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    monkeypatch.setattr(special, "j0", injected)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        except MemoryError:
            assert stimulus == "memory" and calls > 0
        except SimreconError as error:
            assert stimulus == "nonfinite" and calls > 0
            assert error.code == "simulation_optics_range"
        else:
            assert stimulus != "memory" or calls == 0
            assert_output(actual, args, reference)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
    if stimulus == "warning" and calls:
        assert any(issubclass(w.category, DependencyProbeWarning) for w in emitted)


def test_native_longdouble_phase_maximum_normalization() -> None:
    """The native wider-real maximum either normalizes finitely or is invalid."""
    args = base_arguments()
    phase = np.full((1, 1), np.finfo(np.longdouble).max, dtype=np.longdouble)
    assert type(phase) is np.ndarray and np.isfinite(phase).all()
    args["phases_rad"] = phase
    settings_before_conversion = np.geterr().copy()
    # This is a genuine test-owned normalization probe, separate from the
    # product call. A casting overflow must not leak a reference warning.
    with np.errstate(over="ignore", invalid="ignore"):
        normalized = phase.astype(np.float64)
    normalizes_finitely = bool(np.isfinite(normalized).all())
    assert np.geterr() == settings_before_conversion
    reference = on_axis_reference(
        (1, 1, 1, 1, 1), exact(1), exact(1), aperture=exact(1), emission=exact(1)
    )
    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            actual = expected_images(**args)
        except SimreconError as error:
            assert not normalizes_finitely
            assert error.code == "invalid_simulation_optics"
        else:
            assert normalizes_finitely
            assert_output(actual, args, reference)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


def test_unrepresentable_subnormal_with_optional_ldexp_nonfinite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact lattice obstruction binds even after an optional check fault."""
    delta = float.fromhex("0x0.0000000000001p-1022")
    args = base_arguments()
    args["source_e"] = np.full((1, 1, 1), delta)
    pi = pi_interval(80)
    # mu=T=pi*delta lies between 3*delta and 4*delta. All finite float64
    # values are integer multiples of delta. Even both bracketing outputs
    # are outside 1e-5*T; every other representable output is farther away.
    assert 3 < Fraction(pi.lo) <= Fraction(pi.hi) < 4
    assert Fraction(pi.lo) - 3 > Fraction(pi.hi) / 100000
    assert 4 - Fraction(pi.hi) > Fraction(pi.hi) / 100000
    genuine = np.ldexp

    def injected(value: Any, exponent: Any, *values: Any, **keywords: Any) -> Any:
        return positive_ldexp_return(genuine, value, exponent, *values, **keywords)

    arrays = [value for value in args.values() if isinstance(value, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    monkeypatch.setattr(np, "ldexp", injected)
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            with pytest.raises(SimreconError) as error:
                expected_images(**args)
            assert error.value.code == "simulation_optics_range"
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]


@pytest.mark.parametrize("case", ["dark", "huge"])
def test_complete_finite_precision_allows_range_or_certified_success(case: str) -> None:
    args = finite_precision_arguments(case)
    reference = dark_reference() if case == "dark" else huge_reference()
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
            assert_output(actual, args, reference)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not [w for w in emitted if issubclass(w.category, RuntimeWarning)]
