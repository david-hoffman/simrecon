"""Focused preservation checks at the shared optical observer boundary."""

from __future__ import annotations

import warnings
from fractions import Fraction
from typing import Any

import numpy as np
import pytest
from scipy import special

import image_only_calibration_pilot_fixture as reference
from image_only_calibration_pilot_fixture import optical_reference_cache as optical_reference_cache


@pytest.fixture
def optical_inputs() -> dict[str, Any]:
    return dict(
        sites=np.array([[0.03125, 0.015625, 0.03125], [0.09375, 0.0625, 0.046875]]),
        weight=0.5,
        shape=(1, 1, 1),
        carriers=np.array([[0.0, 1.5]]),
        phases=np.array([[0.125, 1.25]]),
        amplitudes=np.array([2.0, 1.0, 0.5]),
        order=1,
    )


def exact(result: reference.OpticalEnclosure) -> tuple[tuple[int, ...], str, bytes, Fraction]:
    assert type(result.radius) is Fraction
    return result.values.shape, result.values.dtype.str, result.values.tobytes(), result.radius


def test_optical_cache_exact_keys_and_owned_results(
    optical_inputs: dict[str, Any], optical_reference_cache: reference.OpticalReferenceCache
) -> None:
    inputs = optical_inputs
    cache = optical_reference_cache
    hits, size = cache.hits, len(cache.entries)
    with warnings.catch_warnings(record=True) as seen:
        expected = exact(reference._optical_enclosure_uncached(**inputs))
        cold = reference.optical_enclosure(**inputs)
        assert (cache.hits, len(cache.entries)) == (hits, size + 1)
        copies: dict[str, Any] = {
            key: value.copy() for key, value in inputs.items() if isinstance(value, np.ndarray)
        }
        snapshots = {
            key: (value.tobytes(), value.strides, value.flags.writeable)
            for key, value in copies.items()
        }
        copies["phases"].flags.writeable = False
        warm = reference.optical_enclosure(**(inputs | copies))
        assert (cache.hits, len(cache.entries)) == (hits + 1, size + 1)
        assert not seen
    assert exact(cold) == exact(warm) == expected
    assert cold is not warm and not np.shares_memory(cold.values, warm.values)
    for result in (cold, warm):
        assert result.values.flags.owndata and result.values.flags.writeable
        result.values.fill(-1)

    sites = inputs["sites"]
    sites[0, 0] += 0.03125
    changed_inputs: tuple[dict[str, Any], ...] = (
        inputs.copy(),
        inputs | copies | {"shape": (1, 2, 1)},
        inputs | copies | {"weight": 0.625},
        inputs | copies | {"carriers": np.array([[0.0, 1.625]])},
        inputs | copies | {"phases": np.array([[0.25, 1.25]])},
        inputs | copies | {"amplitudes": np.array([2.0, 1.0, 0.75])},
        inputs | copies | {"order": 128},
    )
    for offset, changed in enumerate(changed_inputs, start=2):
        target = exact(reference._optical_enclosure_uncached(**changed))
        assert target[:3] != expected[:3]
        assert exact(reference.optical_enclosure(**changed)) == target
        assert (cache.hits, len(cache.entries)) == (hits + 1, size + offset)
    sites[0, 0] = copies["sites"][0, 0]
    assert exact(reference.optical_enclosure(**inputs)) == expected
    assert cache.hits == hits + 2
    for key, (data, strides, writeable) in snapshots.items():
        for array in (inputs[key], copies[key]):
            assert array.tobytes() == data and array.strides == strides
        assert inputs[key].flags.writeable == writeable
        assert copies[key].flags.writeable == (key != "phases")

    signed_zero = inputs["carriers"].copy()
    signed_zero[0, 0] = -0.0
    signed_inputs = inputs | {"carriers": signed_zero}
    size = len(cache.entries)
    assert exact(reference.optical_enclosure(**signed_inputs)) == exact(
        reference._optical_enclosure_uncached(**signed_inputs)
    )
    assert (cache.hits, len(cache.entries)) == (hits + 2, size + 1)


def test_optical_cache_fallback_keeps_representations_and_inconclusive_outcomes(
    optical_inputs: dict[str, Any], optical_reference_cache: reference.OpticalReferenceCache
) -> None:
    inputs = optical_inputs
    cache = optical_reference_cache
    reference.optical_enclosure(**inputs)
    stats = cache.hits, len(cache.entries)
    sites = inputs["sites"]
    strided = np.repeat(sites, 2, axis=1)[:, ::2]
    noncanonical = np.broadcast_to(inputs["carriers"], (1, 2))
    alternatives: tuple[dict[str, Any], ...] = (
        {"sites": strided},
        {"sites": np.asfortranarray(sites)},
        {"sites": sites.astype(sites.dtype.newbyteorder("S"))},
        {"sites": sites.astype(np.float32)},
        {"carriers": noncanonical},
        {"weight": np.float64(0.5)},
        {"weight": Fraction(1, 2)},
    )
    for alternative in alternatives:
        changed = inputs | alternative
        observed = reference.optical_enclosure(**changed)
        assert exact(observed) == exact(reference._optical_enclosure_uncached(**changed))
    assert (cache.hits, len(cache.entries)) == stats

    inconclusive: tuple[tuple[dict[str, Any], str], ...] = (
        ({"weight": -0.0}, "pilot optical observer mass/amplitude domain exceeded"),
        (
            {"phases": np.array([[np.inf, 0.0]])},
            "pilot optical observer finite geometry domain exceeded",
        ),
        (
            {"carriers": np.array([[0.0, 4.0]])},
            "pilot observer received an inadmissible represented carrier",
        ),
    )
    for changed, message in inconclusive:
        for observe in (reference._optical_enclosure_uncached, reference.optical_enclosure):
            with pytest.raises(reference.OracleInconclusive, match=message):
                observe(**(inputs | changed))
    scalar_order: dict[str, Any] = inputs | {"order": np.int64(1)}
    with pytest.raises(TypeError) as original:
        reference._optical_enclosure_uncached(**scalar_order)
    with pytest.raises(TypeError) as observed:
        reference.optical_enclosure(**scalar_order)
    assert str(observed.value) == str(original.value)
    assert (cache.hits, len(cache.entries)) == stats


def test_optical_cache_fallback_preserves_diagnostic_policy(
    optical_inputs: dict[str, Any],
    optical_reference_cache: reference.OpticalReferenceCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = optical_inputs
    cache = optical_reference_cache
    expected = exact(reference._optical_enclosure_uncached(**inputs))
    assert exact(reference.optical_enclosure(**inputs)) == expected
    hits, size = cache.hits, len(cache.entries)
    assert exact(reference.optical_enclosure(**inputs)) == expected
    assert (cache.hits, len(cache.entries)) == (hits + 1, size)
    ordinary = reference._optical_diagnostics()
    assert np.geterrcall() is None

    def assert_fallback() -> None:
        changed = reference._optical_diagnostics()
        callback = np.geterrcall()
        assert not reference._same_optical_diagnostics(changed, ordinary) or callback is not None
        assert exact(reference.optical_enclosure(**inputs)) == exact(
            reference._optical_enclosure_uncached(**inputs)
        )
        assert (cache.hits, len(cache.entries)) == (hits + 1, size)
        assert reference._same_optical_diagnostics(reference._optical_diagnostics(), changed)
        assert np.geterrcall() is callback

    def unexpected(*args: Any) -> None:
        pytest.fail("unexpected reference diagnostic")

    with np.errstate(divide="ignore" if np.geterr()["divide"] == "raise" else "raise"):
        assert_fallback()
    with np.errstate(call=unexpected):
        assert_fallback()
    with warnings.catch_warnings():
        warnings.filterwarnings("error", message="^reference cache policy probe$")
        assert_fallback()
    with monkeypatch.context() as patch:
        patch.setattr(warnings, "defaultaction", "always" if ordinary[2] == "error" else "error")
        assert_fallback()
    with monkeypatch.context() as patch:
        patch.setattr(warnings, "showwarning", unexpected)
        assert_fallback()
    with special.errstate(domain="ignore" if special.geterr()["domain"] == "raise" else "raise"):
        assert_fallback()

    assert reference._same_optical_diagnostics(reference._optical_diagnostics(), ordinary)
    assert np.geterrcall() is None
    assert exact(reference.optical_enclosure(**inputs)) == expected
    assert (cache.hits, len(cache.entries)) == (hits + 2, size)
