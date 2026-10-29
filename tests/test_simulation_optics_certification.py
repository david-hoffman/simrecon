"""Complete independently enclosed Q128 public examples, never full O16 allocation."""

from __future__ import annotations

import warnings
from collections.abc import Callable
from fractions import Fraction
from importlib import import_module
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from simulation_optics_fixture import compare_reference, exact
from simulation_optics_q128_fixture import (
    composition_case,
    oscillatory_case,
    qualify_reference,
)

expected_images = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_optics").expected_images,
)
make_sources = cast(
    Callable[..., NDArray[np.float64]],
    import_module("scripts.simulation_sources").make_sources,
)


def observed_call(
    function: Callable[..., NDArray[np.float64]], arguments: dict[str, Any]
) -> NDArray[np.float64]:
    """Observe the real boundary without replacing numerical work or failures."""
    arrays = [v for v in arguments.values() if isinstance(v, np.ndarray)]
    before = [(a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays]
    with warnings.catch_warnings(record=True) as emitted, np.errstate(all="raise"):
        warnings.simplefilter("always")
        settings = np.geterr().copy()
        try:
            result = function(**arguments)
        finally:
            assert np.geterr() == settings
            assert before == [
                (a.tobytes(), a.dtype, a.shape, a.strides, a.flags.writeable) for a in arrays
            ]
    assert not any(issubclass(w.category, RuntimeWarning) for w in emitted)
    assert type(result) is np.ndarray
    assert result.dtype == np.dtype("float64") and result.dtype.isnative
    assert result.flags.c_contiguous and result.flags.writeable
    assert np.isfinite(result).all() and (result >= 0).all()
    assert not any(np.shares_memory(result, value) for value in arrays)
    return result


def test_small_source_catalogue_to_complete_q128_images() -> None:
    """Real two-entry composition; the exact full recipe remains coordinator-owned."""
    source_args, optics_args, predicted, geometry = composition_case()
    reference = geometry.reference()
    qualify_reference(reference)
    generated = observed_call(make_sources, source_args)
    assert generated.shape == predicted.shape == (4, 2, 2)
    assert np.array_equal(generated, predicted)
    optics_args["source_e"] = generated
    actual = observed_call(expected_images, optics_args)
    assert actual.shape == reference.shape == (1, 1, 2, 1, 1)
    compare_reference(tuple(exact(float(v)) for v in actual.flat), reference)


def test_complete_oscillatory_q128_distinguishes_normalized_wrong_rules() -> None:
    """All four outputs have certified truth; normalized mass alone is insufficient.

    Alternatives are oracle-only mathematical models, not injected backends.
    Disjoint 1e-5*T acceptance bands prove sensitivity on this complete example.
    """
    args, geometry = oscillatory_case()
    reference = geometry.reference()
    targets, peak = qualify_reference(reference)
    for kind in ("canonical64", "midpoint128", "equal-weight128"):
        alternative, alternative_peak = qualify_reference(geometry.reference(kind))
        # Sum of both allowances: no single output vector could pass both models.
        combined_allowance = (Fraction(peak.hi) + Fraction(alternative_peak.hi)) / 100000
        separations = [
            max(Fraction(a.lo) - Fraction(b.hi), Fraction(b.lo) - Fraction(a.hi))
            for a, b in zip(targets, alternative, strict=True)
        ]
        assert max(separations) > combined_allowance
    actual = observed_call(expected_images, args)
    assert actual.shape == reference.shape == (1, 2, 1, 1, 2)
    compare_reference(tuple(exact(float(v)) for v in actual.flat), reference)
