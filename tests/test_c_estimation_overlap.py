"""CE05 overlap, regression and exact finite boundary decisions."""

from __future__ import annotations

import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from c_estimation_fixture import (
    OPTICS,
    assert_expected,
    bands_record,
    close,
    controlled_bands,
    dc_bands,
    estimate,
    events,
    expected_estimate,
    overlap,
    rejection,
    transfer_record,
    unit_transfer,
)


@pytest.mark.parametrize("layout", ["radial", "full"])
@pytest.mark.parametrize("carrier", [[0.075, -0.04], [-0.075, 0.04], [0.0, 0.0]])
def test_signed_complex_overlaps_reflection_and_unnormalized_sums(layout, carrier):
    bands = controlled_bands(shape=(4, 3, 4), dz=0.1, orders=4, zoom=(2, 3))
    bands.noise_variance_factors[:] = [[1.0, 2.0, 0.25, 3.0]]
    transfer = transfer_record(5, layout=layout)
    initial = np.array([carrier])
    expected = expected_estimate(bands, transfer, initial, search_carriers=False)
    before = bands.quadratures.copy()
    actual = estimate(bands, transfer, initial, search_carriers=False)
    assert_expected(actual, expected)
    assert_array_equal(bands.quadratures, before)
    assert [b.orders for b in actual.overlaps] == [(0, 1), (0, 2), (0, 3)]
    assert all(e["objective"] is None for e in events(actual, "evaluation"))
    # Non-DC / nonzero means prevent a centered correlation substitution.
    e = events(actual, "evaluation")[0]
    close(e["forward"], e["cross"] / e["SX"])
    close(e["reverse"], e["cross"].conjugate() / e["SY"])
    close(e["correlation"], abs(e["cross"]) / math.sqrt(e["SX"] * e["SY"]))


@pytest.mark.parametrize("dz,na,cutoff", [(1.0, 1.0, 0), (1.0, 0.5, 1), (0.1, 1.0, 1)])
def test_strict_axial_clipping_and_sequential_endpoint_writes(dz, na, cutoff):
    bands = controlled_bands(shape=(2, 1, 4), orders=2, dz=dz)
    samples = np.ones((2, 4, 4), dtype=np.complex128)
    samples[0, :, 3] = 0.5 + 0.25j
    samples[1, :, 3] = 1 + 0.5j
    samples[0, :, 1] = 0.75 - 0.125j
    samples[1, :, 1] = 0.25 + 0.25j
    transfer = transfer_record(2, samples=samples, dkr=1, dkz=1 / (2 * dz))
    initial = np.zeros((1, 2))
    options = dict(search_carriers=False, numerical_aperture=na)
    expected = expected_estimate(bands, transfer, initial, **options)
    actual = estimate(bands, transfer, initial, **options)
    assert actual.axial_cutoff_bins == cutoff
    assert_expected(actual, expected)
    if cutoff == 1:
        # Last visit is +1, not -1: its complex other transfer must survive.
        b = actual.overlaps[0]
        close(
            b.fourier[0, 1, 0, 0],
            bands.quadratures[0, 0, 0, 1, 0, 0]
            * samples[1, 0, 1]
            / math.hypot(abs(samples[0, 0, 1]), abs(samples[1, 0, 1])),
        )


def test_later_failed_endpoint_retains_earlier_successful_write():
    bands = controlled_bands(shape=(2, 1, 4), orders=2)
    samples = np.ones((2, 4, 4), dtype=np.complex128)
    samples[0, :, 1] = 0
    samples[1, :, 3] = 0.5 + 0.25j
    transfer = transfer_record(2, samples=samples, dkr=1, dkz=0.5)
    initial = np.zeros((1, 2))
    options = dict(search_carriers=False, numerical_aperture=0.5)
    expected = expected_estimate(bands, transfer, initial, **options)
    actual = estimate(bands, transfer, initial, **options)
    assert_expected(actual, expected)
    assert actual.overlaps[0].written[0, 1, 0, 0]
    close(
        actual.overlaps[0].fourier[0, 1, 0, 0],
        bands.quadratures[0, 0, 0, 1, 0, 0] * (0.5 + 0.25j) / math.sqrt(1.3125),
    )


@pytest.mark.parametrize("omit", [False, True])
def test_omit_kz0_with_nonzero_axial_energy(omit):
    bands = controlled_bands(shape=(4, 2, 4), orders=2, dz=0.1)
    transfer = transfer_record(2)
    initial = np.array([[0.0625, -0.025]])
    expected = expected_estimate(bands, transfer, initial, search_carriers=False, omit_kz0=omit)
    actual = estimate(bands, transfer, initial, search_carriers=False, omit_kz0=omit)
    assert_expected(actual, expected)
    if omit:
        assert not actual.overlaps[0].written[:, 0].any()
        assert_array_equal(actual.overlaps[0].fourier[:, 0], 0)


@pytest.mark.parametrize("higher", [False, True])
@pytest.mark.parametrize("direction", [-1, 0, 1])
def test_strict_sample_threshold_at_interpolated_equality(higher, direction):
    threshold_value = 0.006 / (5 if higher else 1)
    dxy = 1 / (4 * threshold_value)
    if direction:
        dxy = float(np.nextafter(dxy, math.inf if direction < 0 else 0))
    bands = controlled_bands(shape=(2, 1, 4), orders=2, dxy=dxy)
    samples = np.ones((2, 4, 1), dtype=np.complex128)
    samples[int(higher), :, 0] = [0, 1, 2, 3]
    transfer = transfer_record(2, samples=samples, dkr=1)
    initial = np.zeros((1, 2))
    expected = expected_estimate(bands, transfer, initial, search_carriers=False)
    actual = estimate(bands, transfer, initial, search_carriers=False)
    assert_expected(actual, expected)
    value = (5 if higher else 1) / (4 * dxy)
    if direction == 0:
        assert value == 0.006, "fixture must reach exact binary64 comparison equality"
    assert bool(actual.overlaps[0].written[0, 0, 0, 1]) == (value > 0.006)
    assert bool(actual.overlaps[0].written[1, 0, 0, 1]) == (value > 0.006)


@pytest.mark.parametrize("first_passes", [None, "lower", "higher"])
def test_failed_primary_threshold_short_circuits_unsafe_second_sample(first_passes):
    bands = dc_bands()
    samples = np.zeros((2, 2, 1), dtype=np.complex128)
    if first_passes:
        samples[0 if first_passes == "lower" else 1, 0, 0] = 1
    transfer = transfer_record(2, samples=samples, dkr=0.1)
    # R=.2 admits DC shifted .15, but excludes native Nyquist .5.
    # Second sample at .15 requires an out-of-allocation third radial row.
    rejection(
        bands,
        transfer,
        np.array([[0.15, 0.0]]),
        "(?i)(stencil|interpol|offset|sample|address)" if first_passes else "(?i)(lower|SX|energy)",
        search_carriers=False,
        numerical_aperture=0.05,
    )


@pytest.mark.parametrize("scale", [1.0, 1e-60])
def test_weak_dc_regression_has_no_signal_floor_and_uncentered_correlation(scale):
    bands = dc_bands(gain=-0.25 + 0.125j)
    bands.quadratures *= scale
    actual = estimate(bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False)
    evaluation = events(actual, "evaluation")[0]
    close(evaluation["SX"], 2 * scale**2, atol=0)
    close(evaluation["SY"], 2 * abs(-0.25 + 0.125j) ** 2 * scale**2, atol=0)
    close(evaluation["forward"], -0.25 + 0.125j)
    close(evaluation["reverse"], 1 / (-0.25 + 0.125j))
    close(evaluation["correlation"], 1)
    assert evaluation["objective"] is None


def test_known_large_forward_does_not_evaluate_unused_overflowing_square():
    bands = dc_bands(gain=1)
    bands.quadratures[0, 0, 0, 0, 0, 0] = 1e-100
    bands.quadratures[0, 0, 1, 0, 0, 0] = 1e100
    result = estimate(bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False)
    e = events(result, "evaluation")[0]
    # Four voxels, each overlap constant DC/sqrt(2).
    close(e["SX"], 2e-200, atol=0)
    close(e["SY"], 2e200, atol=0)
    close(e["cross"], 2, atol=0)
    close(e["forward"], 1e200, atol=0)
    close(e["reverse"], 1e-200, atol=0)
    close(e["correlation"], 1)
    assert e["objective"] is None
    assert math.isfinite(abs(e["combined"]))  # No accuracy claim at this conditioning.


def zero_cross_bands():
    """Build pointwise-disjoint known overlaps without a global cross cancellation."""
    bands = bands_record(orders=2, shape=(2, 1, 2))
    bands.quadratures.fill(0)
    bands.quadratures[0, 0, 0, :, 0, :] = [[1, -1], [-1, 1]]
    bands.quadratures[0, 0, 1, :, 0, :] = [[0, 1], [-1, 0]]
    return bands


@pytest.mark.parametrize("fit_all", [True, False])
def test_zero_cross_valid_helper_versus_selected_zero_phase(fit_all):
    bands = zero_cross_bands()
    if not fit_all:
        rejection(
            bands,
            unit_transfer(),
            np.zeros((1, 2)),
            "(?i)(phase|arg|order.?1)",
            search_carriers=False,
            fit_all_phases=False,
            numerical_aperture=0.5,
        )
        return
    actual = estimate(
        bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False, numerical_aperture=0.5
    )
    e = events(actual, "evaluation")[0]
    close(e["SX"], 8)
    close(e["SY"], 4)
    assert e["cross"] == e["forward"] == e["reverse"] == e["combined"] == 0j
    assert e["correlation"] == 0.0
    assert e["objective"] is None
    assert_array_equal(actual.modulation, 0)


def test_zero_forward_positive_floor_fails_at_adjustment():
    bands = zero_cross_bands()
    rejection(
        bands,
        unit_transfer(),
        np.zeros((1, 2)),
        "(?i)(floor|amplitude|division)",
        search_carriers=False,
        amplitude_floors=np.array([0.1]),
        numerical_aperture=0.5,
    )


def test_inclusive_radial_masks_keep_independent_shifted_branches():
    bands = controlled_bands(shape=(3, 1, 4), orders=2)
    transfer = unit_transfer()
    initial = np.array([[0.25, 0]])
    expected = expected_estimate(bands, transfer, initial, search_carriers=False)
    actual = estimate(bands, transfer, initial, search_carriers=False)
    assert_expected(actual, expected)
    # Native +Nyquist .5 minus .25 is admitted; plus .25 is not.
    assert actual.overlaps[0].written[0, 0, 0, 2]
    assert not actual.overlaps[0].written[1, 0, 0, 2]
    # Native -.25 minus .25 hits exactly -.5 and remains included.
    assert actual.overlaps[0].written[0, 0, 0, 3]
    independent = overlap(bands, transfer, initial[0], 1, optics=OPTICS)
    close(actual.overlaps[0].fourier, independent.fourier)


@pytest.mark.parametrize("scale", [1e200, 1e-200])
def test_finite_quadratures_with_undefined_energy_arithmetic_reject(scale):
    bands = dc_bands()
    bands.quadratures *= scale
    rejection(
        bands,
        unit_transfer(),
        np.zeros((1, 2)),
        "(?i)(energy|SX|SY|finite|overflow|underflow|regression)",
        search_carriers=False,
    )


def test_searched_squared_forward_overflow_is_an_actual_objective_error():
    bands = bands_record(shape=(2, 1, 4))
    bands.quadratures.fill(0)
    bands.quadratures[0, 0, 0, 0, 0, 0] = 1e-100
    bands.quadratures[0, 0, 1, 0, 0, 0] = 0.25e-100
    bands.quadratures[0, 0, 3, 0, 0, 1] = 1e100
    # Coarse correlation has tied peaks at +/-1. First peak is +1, k=.125.
    # Remade regression has finite SX~1e-200, SY~1e200 and forward~1e200.
    # Only getmodamp's actually selected square is undefined here.
    rejection(
        bands, unit_transfer(3), np.zeros((1, 2)), "(?i)(objective|forward|square|finite|overflow)"
    )
