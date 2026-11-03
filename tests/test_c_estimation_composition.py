"""Real public CE02/CE03 -> CE05 -> per-time CE04 composition."""

from __future__ import annotations

import cmath
import dataclasses
import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import simrecon
from c_estimation_fixture import (
    OPTICS,
    assert_expected,
    bands_record,
    close,
    estimate,
    expected_estimate,
    known_image_sum,
    unit_transfer,
)


def one_time(bands, time):
    """Use the specified public value-record slicing, preserving alpha."""
    return dataclasses.replace(
        bands,
        quadratures=bands.quadratures[time : time + 1].copy(),
        input_shape=(1, *bands.input_shape[1:]),
        frame_sums=bands.frame_sums[time : time + 1].copy(),
        equalization_gains=bands.equalization_gains[time : time + 1].copy(),
        sentinel_frames=tuple((0, d, z, p) for t, d, z, p in bands.sentinel_frames if t == time),
    )


@pytest.mark.parametrize("phase_policy", [True, False])
def test_raw_three_direction_profile_uses_estimates_in_actual_filtered_image(phase_policy):
    raw = np.empty((2, 3, 5, 4, 2, 4), dtype=np.float64)
    profiles = np.array([[2, 3, 5, 7, 11], [3, 8, 4, 12, 6]])
    for t in range(2):
        for d in range(3):
            for p in range(5):
                raw[t, d, p] = profiles[t, p] + d * (p + 1)
    bands = bands_record(raw=raw, directions=3, times=2, shape=(4, 2, 4))
    transfer = unit_transfer(3)
    initial = np.zeros((3, 2))
    floors = np.array([0.4, 0.3])
    options = dict(search_carriers=False, amplitude_floors=floors, fit_all_phases=phase_policy)
    expected = expected_estimate(bands, transfer, initial, **options)
    # A second algebraic oracle starts at raw counts, independent of observed bands.
    bzero = np.empty((2, 3))
    side = np.empty((2, 3, 2), dtype=np.complex128)
    fitted = np.empty_like(side)
    for t in range(2):
        for d in range(3):
            values = [float(profiles[t, p] + d * (p + 1)) for p in range(5)]
            bzero[t, d] = sum(values) / 3  # spatial volume cancels alpha; D=3 remains.
            for m in (1, 2):
                side[t, d, m - 1] = (
                    sum(v * cmath.exp(2j * math.pi * m * p / 5) for p, v in enumerate(values)) / 3
                )
                a = side[t, d, m - 1] / bzero[t, d]
                fitted[t, d, m - 1] = a * max(1.0, floors[m - 1] / abs(a))
            if not phase_policy:
                fitted[t, d, 1] = abs(fitted[t, d, 1]) * cmath.exp(
                    2j * cmath.phase(fitted[t, d, 0])
                )
    close(expected.modulation, fitted)
    actual = estimate(bands, transfer, initial, **options)
    assert_expected(actual, expected)
    snapshots = bands.quadratures.copy()
    images = []
    for t in range(2):
        sliced = one_time(bands, t)
        assert sliced.input_scale == bands.input_scale
        reconstruction = simrecon.reconstruct_known(
            sliced,
            transfer,
            carriers_cyc_um=actual.carriers_cyc_um[t],
            modulation=actual.modulation[t],
            **OPTICS,
            wiener=0.5,
            suppress_singularities=False,
            output_taper="none",
        )
        denominator = 0.25 + sum(1 + 2 * np.sum(np.abs(fitted[t, d]) ** 2) for d in range(3))
        numerator = sum(
            bzero[t, d]
            + 2 * sum((fitted[t, d, m].conjugate() * side[t, d, m]).real for m in range(2))
            for d in range(3)
        )
        close(reconstruction.image, np.full((1, 4, 2, 4), numerator / denominator))
        assert_array_equal(reconstruction.modulation, actual.modulation[t])
        close(reconstruction.image, known_image_sum(sliced, transfer, initial, fitted[t]))
        images.append(reconstruction.image[0])
    assert np.max(np.abs(images[0] - images[1])) > 0.1
    assert_array_equal(bands.quadratures, snapshots)


@pytest.mark.parametrize("reuse", [True, False])
def test_raw_finite_search_per_time_estimates_compose_without_gain_or_registration(reuse):
    rng = np.random.default_rng(7)
    raw = rng.integers(1, 17, (2, 1, 5, 3, 3, 4)).astype(np.float64)
    bands = bands_record(raw=raw, times=2)
    transfer = unit_transfer(3)
    initial = np.array([[0.05, -0.025]])
    expected = expected_estimate(bands, transfer, initial, use_time0_carriers=reuse)
    expected_images = [
        known_image_sum(
            one_time(bands, t), transfer, expected.carriers_cyc_um[t], expected.modulation[t]
        )
        for t in range(2)
    ]
    actual = estimate(bands, transfer, initial, use_time0_carriers=reuse)
    assert_expected(actual, expected)
    for t in range(2):
        result = simrecon.reconstruct_known(
            one_time(bands, t),
            transfer,
            carriers_cyc_um=actual.carriers_cyc_um[t],
            modulation=actual.modulation[t],
            **OPTICS,
            wiener=0.5,
            suppress_singularities=False,
            output_taper="none",
        )
        # Propagate the independently bounded CE05 parameter uncertainty into the
        # small, positive-denominator CE04 quotient and centered phase sum.
        scale = max(1.0, float(np.max(np.abs(expected_images[t]))))
        allowance = 3e-12 + 128 * math.pi * scale * expected.coordinate_budget
        close(result.image, expected_images[t], atol=allowance)
        assert_array_equal(result.carriers_cyc_um, actual.carriers_cyc_um[t])
        assert_array_equal(result.modulation, actual.modulation[t])
