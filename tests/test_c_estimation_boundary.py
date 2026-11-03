"""CE05 caller domains, selected failures, adjustments and immutable records."""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np
import pytest
from numpy.testing import assert_array_equal

import simrecon
from c_estimation_fixture import (
    PUBLIC,
    SOURCES,
    assert_expected,
    bands_record,
    close,
    controlled_bands,
    dc_bands,
    estimate,
    events,
    expected_estimate,
    rejection,
    transfer_record,
    unit_transfer,
)


@pytest.mark.parametrize("floors", [None, [0.125, 0.5, 1.0], [0.25, 0.5, 0.75]])
@pytest.mark.parametrize("fit_all", [True, False])
def test_floor_below_equal_above_then_phase_from_order_one(floors, fit_all):
    bands = dc_bands(gain=0.25j, orders=4)
    initial = np.zeros((1, 2))
    values = None if floors is None else np.array(floors)
    options = dict(search_carriers=False, amplitude_floors=values, fit_all_phases=fit_all)
    expected = expected_estimate(bands, unit_transfer(4), initial, **options)
    actual = estimate(bands, unit_transfer(4), initial, **options)
    assert_expected(actual, expected)
    close(actual.raw_modulation[0, 0], [0.25j, 0.5j, 0.75j])
    adjustments = events(actual, "adjustment")
    assert [a["order"] for a in adjustments] == [1, 2, 3]
    if floors == [0.125, 0.5, 1.0]:
        assert [a["floor_applied"] for a in adjustments] == [False, False, True]
    if not fit_all:
        close(actual.modulation[0, 0, 1], -abs(expected.modulation[0, 0, 1]))
        close(actual.modulation[0, 0, 2], -1j * abs(expected.modulation[0, 0, 2]))
    else:
        assert all(not a["phase_replaced"] for a in adjustments)


@pytest.mark.parametrize(
    "bad,pattern",
    [
        ("lower", "(?i)(lower|SX|energy)"),
        ("higher", "(?i)(higher|SY|energy)"),
        ("equal", "(?i)(equal|combined|singular)"),
        ("later-order", "(?i)(higher|SY|energy)"),
        ("later-time", "(?i)(higher|SY|energy)"),
    ],
)
def test_absent_equal_and_late_failures_reject_whole_call_without_mutation(bad, pattern):
    bands = dc_bands(orders=3, times=2)
    if bad == "lower":
        bands.quadratures[:, :, 0] = 0
    elif bad == "higher":
        bands.quadratures[:, :, 1:3] = 0
    elif bad == "equal":
        bands.quadratures[:, :, 1] = bands.quadratures[:, :, 0]
        bands.quadratures[:, :, 2] = 0
    elif bad == "later-order":
        bands.quadratures[:, :, 3:] = 0
    else:
        bands.quadratures[1, :, 1:] = 0
    rejection(bands, unit_transfer(3), np.zeros((1, 2)), pattern, search_carriers=False)


def test_omit_clipped_zero_cutoff_known_fit_fails_at_energy_not_stencil():
    bands = dc_bands()
    # R=1 table is unsafe even at DC; omitting the sole z plane skips all requests.
    transfer = transfer_record(2, samples=np.ones((2, 1, 1)))
    rejection(
        bands,
        transfer,
        np.zeros((1, 2)),
        "(?i)(lower|SX|energy)",
        search_carriers=False,
        omit_kz0=True,
    )


@pytest.mark.parametrize("reuse", [False, True])
def test_known_path_ignores_time0_policy_and_uses_unequal_direction_vectors(reuse):
    bands = controlled_bands(times=2, directions=3, orders=2)
    initial = np.array([[0.0, 0.0], [0.05, -0.02], [-0.09, 0.04]])
    transfer = transfer_record(2)
    expected = expected_estimate(
        bands, transfer, initial, search_carriers=False, use_time0_carriers=reuse
    )
    actual = estimate(bands, transfer, initial, search_carriers=False, use_time0_carriers=reuse)
    assert_expected(actual, expected)
    assert actual.branches == (("known",) * 3,) * 2
    assert not events(actual, "reuse")


@pytest.mark.parametrize("dtype", [np.int16, np.uint32, np.float16, np.float32, np.float64])
def test_standard_real_kinds_strided_readonly_carriers_and_noise_are_valid(dtype):
    bands = controlled_bands(orders=2)
    # Used arrays are copied; no requirement to be contiguous or writable.
    original = bands.quadratures.copy()
    buffer = np.zeros((*original.shape[:-1], original.shape[-1] * 2), dtype=np.complex128)
    buffer[..., ::2] = original
    quadratures = buffer[..., ::2]
    quadratures.flags.writeable = False
    noise = np.array([[2.0, 3.0, 7.0, 8.0]])[:, ::2]
    noise.flags.writeable = False
    bands = dataclasses.replace(bands, quadratures=quadratures, noise_variance_factors=noise)
    backing = np.zeros((1, 4), dtype=dtype)
    initial = backing[:, ::2]
    initial.flags.writeable = False
    transfer = unit_transfer()
    expected = expected_estimate(bands, transfer, initial, search_carriers=False)
    actual = estimate(bands, transfer, initial, search_carriers=False)
    assert_expected(actual, expected)
    assert_array_equal(quadratures, original)
    assert not np.shares_memory(actual.initial_carriers_cyc_um, initial)


@pytest.mark.parametrize("search", [False, True])
def test_two_orders_are_allowed_only_when_not_searching(search):
    bands = dc_bands()
    if search:
        rejection(bands, unit_transfer(), np.zeros((1, 2)), "(?i)(order|search)")
    else:
        actual = estimate(
            bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False, fit_all_phases=False
        )
        close(actual.modulation, [[[0.25 + 0.125j]]])


@pytest.mark.parametrize("orders,floors", [(25, True), (26, False), (26, True)])
def test_floor_allocation_limit_does_not_impose_a_floor_disabled_order_cap(orders, floors):
    bands = dc_bands(orders=orders, gain=1 / 128)
    options = dict(
        search_carriers=False, amplitude_floors=np.full(orders - 1, 1 / 16) if floors else None
    )
    if orders == 26 and floors:
        rejection(bands, unit_transfer(orders), np.zeros((1, 2)), "(?i)(floor|25|order)", **options)
    else:
        actual = estimate(bands, unit_transfer(orders), np.zeros((1, 2)), **options)
        expected = expected_estimate(bands, unit_transfer(orders), np.zeros((1, 2)), **options)
        assert_expected(actual, expected)


@pytest.mark.parametrize(
    "name,value",
    [
        ("wavelength_nm", True),
        ("wavelength_nm", 500.0),
        ("wavelength_nm", 0),
        ("wavelength_nm", 32768),
        ("wavelength_nm", np.array(500)),
        ("numerical_aperture", True),
        ("numerical_aperture", 0),
        ("numerical_aperture", -0.1),
        ("numerical_aperture", 1.1),
        ("numerical_aperture", float("nan")),
        ("numerical_aperture", float("inf")),
        ("numerical_aperture", 1 + 0j),
        ("numerical_aperture", np.array(1.0)),
        ("immersion_index", True),
        ("immersion_index", 0.999),
        ("immersion_index", 2.001),
        ("immersion_index", float("nan")),
        ("immersion_index", float("inf")),
        ("search_carriers", 0),
        ("search_carriers", np.bool_(False)),
        ("use_time0_carriers", 1),
        ("fit_all_phases", None),
        ("omit_kz0", "false"),
    ],
)
def test_invalid_optics_and_flag_domains(name, value):
    options = dict(search_carriers=False) | {name: value}
    rejection(
        dc_bands(),
        unit_transfer(),
        np.zeros((1, 2)),
        f"(?i)({name}|wavelength|aperture|immersion|boolean|flag)",
        **options,
    )


@pytest.mark.parametrize("wavelength,na,immersion", [(np.int32(1), 1.0, 1.0), (32767, 2.0, 2.0)])
def test_optical_integer_and_closed_endpoints(wavelength, na, immersion):
    bands = dc_bands()
    actual = estimate(
        bands,
        unit_transfer(),
        np.zeros((1, 2)),
        search_carriers=False,
        wavelength_nm=wavelength,
        numerical_aperture=na,
        immersion_index=immersion,
    )
    close(actual.raw_modulation, [[[0.25 + 0.125j]]])


@pytest.mark.parametrize(
    "value",
    [
        [[0.0, 0.0]],
        np.zeros(2),
        np.zeros((2, 2)),
        np.zeros((1, 1)),
        np.zeros((1, 2), dtype=bool),
        np.zeros((1, 2), dtype=complex),
        np.array([["0", "0"]]),
        np.array([[0, 0]], dtype=object),
        np.array([[np.nan, 0]]),
        np.array([[0, np.inf]]),
        np.array([[1e40, 0]]),
        np.zeros((1, 2), dtype=np.longdouble),
    ],
)
def test_invalid_carrier_kind_shape_finiteness_and_float32_magnitude(value):
    rejection(dc_bands(), unit_transfer(), value, "(?i)(carrier|initial)", search_carriers=False)


@pytest.mark.parametrize(
    "value",
    [
        [0.1],
        np.array(0.1),
        np.array([0.1, 0.2]),
        np.array([0.0]),
        np.array([-0.1]),
        np.array([np.nan]),
        np.array([np.inf]),
        np.array([1e40]),
        np.array([True]),
        np.array([0.1j]),
        np.array(["0.1"]),
        np.array([0.1], dtype=object),
        np.array([0.1], dtype=np.longdouble),
    ],
)
def test_invalid_floor_kind_shape_positive_finite_and_representation(value):
    rejection(
        dc_bands(),
        unit_transfer(),
        np.zeros((1, 2)),
        "(?i)(floor|amplitude)",
        search_carriers=False,
        amplitude_floors=value,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("input_shape", (1, 1, 3, 1, 1, 2)),
        ("input_shape", (1, 1, 3, 2, 1, 3)),
        ("input_shape", (0, 1, 3, 2, 1, 2)),
        ("input_shape", (1, 1, 2, 2, 1, 2)),
        ("input_shape", (1, 1, 3, 2, 1)),
        ("input_shape", (True, 1, 3, 2, 1, 2)),
        ("input_scale", 2.0),
        ("input_scale", 0),
        ("input_scale", float("nan")),
        ("dxy_um", 0),
        ("dz_um", -1),
        ("dxy_um", True),
        ("dz_um", float("inf")),
        ("lateral_zoom", 0),
        ("axial_zoom", 1.5),
        ("lateral_zoom", True),
        ("source_revision", "SVN306"),
        ("reference_sha256", ()),
        ("quadratures", np.zeros((1, 1, 3, 2, 1, 2), dtype=np.complex64)),
        ("quadratures", np.zeros((1, 1, 2, 2, 1, 2), dtype=np.complex128)),
        ("quadratures", np.full((1, 1, 3, 2, 1, 2), np.nan, dtype=np.complex128)),
        ("noise_variance_factors", np.ones((1, 2), dtype=np.float32)),
        ("noise_variance_factors", np.zeros((1, 2))),
        ("noise_variance_factors", np.full((1, 2), np.inf)),
        ("noise_variance_factors", np.ones((2, 2))),
    ],
)
def test_invalid_used_prepared_record_fields(field, value):
    bands = dataclasses.replace(dc_bands(), **{field: value})
    rejection(
        bands,
        unit_transfer(),
        np.zeros((1, 2)),
        "(?i)(band|shape|scale|sampling|dxy|dz|zoom|source|reference|quadrature|noise|variance|finite)",
        search_carriers=False,
    )


def test_actual_record_types_required_and_unused_preparation_diagnostics_not_replayed():
    transfer = unit_transfer()
    rejection(object(), transfer, np.zeros((1, 2)), "(?i)(band|Prepared)", search_carriers=False)
    rejection(
        dc_bands(), object(), np.zeros((1, 2)), "(?i)(transfer|Optical)", search_carriers=False
    )
    bands = dc_bands()
    bands.frame_sums.fill(np.nan)
    bands.equalization_gains.fill(-7)
    bands.separation_matrices.fill(np.nan)
    actual = estimate(bands, transfer, np.zeros((1, 2)), search_carriers=False)
    close(actual.modulation, [[[0.25 + 0.125j]]])


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_revision", "SVN306"),
        ("reference_sha256", ()),
        ("layout", "other"),
        ("dkr_cyc_um", 0),
        ("dkz_cyc_um", float("nan")),
        ("norders", 1),
        ("samples", np.ones((2, 2, 1), dtype=np.complex64)),
        ("samples", np.full((2, 2, 1), np.inf, dtype=np.complex128)),
    ],
)
def test_invalid_used_transfer_metadata_or_complete_samples(field, value):
    transfer = dataclasses.replace(unit_transfer(), **{field: value})
    rejection(
        dc_bands(),
        transfer,
        np.zeros((1, 2)),
        "(?i)(transfer|OTF|source|reference|layout|increment|dkr|dkz|order|sample|finite)",
        search_carriers=False,
    )


def test_unsafe_required_zero_weight_vertex_is_not_zero_filled():
    transfer = transfer_record(2, samples=np.ones((2, 1, 1)))
    rejection(
        dc_bands(),
        transfer,
        np.zeros((1, 2)),
        "(?i)(stencil|interpol|offset|sample|address)",
        search_carriers=False,
    )


@pytest.mark.parametrize("kind", ["cutoff", "dxy", "dz", "native-product", "dimension"])
def test_source_integer_and_derived_frequency_representation_rejects_before_work(kind):
    bands = dc_bands()
    if kind == "cutoff":
        bands = dataclasses.replace(bands, dz_um=1e10)
    elif kind == "dxy":
        bands = dataclasses.replace(bands, dxy_um=float(np.nextafter(0.0, 1.0)))
    elif kind == "dz":
        bands = dataclasses.replace(bands, dz_um=float(np.nextafter(0.0, 1.0)))
    else:
        nx, ny, nz = (2**31, 1, 2) if kind == "dimension" else (2**30, 2, 2)
        shape = (1, 1, 3, nz, ny, nx // 2 + 1)
        view = np.lib.stride_tricks.as_strided(
            np.zeros(1, dtype=np.complex128), shape=shape, strides=(0,) * 6, writeable=False
        )
        bands = dataclasses.replace(
            bands,
            quadratures=view,
            input_shape=(1, 1, 3, nz, ny, nx),
            input_scale=1 / (nx * ny * nz),
        )
    rejection(
        bands,
        unit_transfer(),
        np.zeros((1, 2)),
        "(?i)(represent|integer|32|cutoff|frequen|finite|overflow|sampling|dxy|dz|size|extent|address)",
        search_carriers=False,
    )


def test_signature_errors():
    function = PUBLIC.estimate_parameters
    with pytest.raises(TypeError):
        function(dc_bands(), unit_transfer())
    with pytest.raises(TypeError):
        estimate(dc_bands(), unit_transfer(), np.zeros((1, 2)), recalcarrays=True)


def test_retired_scientific_public_names_remain_absent():
    for name in ("reconstruct", "reconstruct_volume", "prepare_otf"):
        assert not hasattr(simrecon, name)


def test_owned_immutable_outputs_ordered_schema_and_source_metadata():
    bands = controlled_bands(orders=2)
    transfer = unit_transfer()
    initial = np.zeros((1, 2))
    actual = estimate(bands, transfer, initial, search_carriers=False)
    assert isinstance(actual, PUBLIC.EstimatedParameters)
    assert actual.source_revision == "SVN307"
    assert actual.reference_sha256 == SOURCES
    assert type(actual.axial_cutoff_bins) is int
    assert type(actual.radial_cutoff_cyc_um) is float
    assert actual.radial_cutoff_cyc_um == 0.5
    assert type(actual.branches) is tuple and type(actual.branches[0]) is tuple
    assert type(actual.overlaps) is tuple and type(actual.trace) is tuple
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
        actual.source_revision = "changed"
    settings = dict(actual.resolved_settings)
    assert tuple(settings) == (
        "wavelength_nm",
        "numerical_aperture",
        "immersion_index",
        "search_carriers",
        "use_time0_carriers",
        "amplitude_floors",
        "fit_all_phases",
        "omit_kz0",
        "dxy_um",
        "dz_um",
        "lateral_zoom",
        "axial_zoom",
        "input_scale",
    )
    assert settings == dict(
        wavelength_nm=500,
        numerical_aperture=1.0,
        immersion_index=1.0,
        search_carriers=False,
        use_time0_carriers=True,
        amplitude_floors=None,
        fit_all_phases=True,
        omit_kz0=False,
        dxy_um=1.0,
        dz_um=1.0,
        lateral_zoom=1,
        axial_zoom=1,
        input_scale=bands.input_scale,
    )
    output_arrays: list[Any] = []
    for name, dtype in (
        ("carriers_cyc_um", np.float64),
        ("initial_carriers_cyc_um", np.float64),
        ("modulation", np.complex128),
        ("raw_modulation", np.complex128),
    ):
        value = getattr(actual, name)
        assert value.dtype == dtype
        output_arrays.append(value)
    for build in actual.overlaps:
        for name in ("index", "time_index", "direction_index"):
            assert type(getattr(build, name)) is int and getattr(build, name) >= 0
        assert type(build.orders) is tuple and all(type(i) is int for i in build.orders)
        assert build.fourier.dtype == build.spatial.dtype == np.complex128
        assert build.written.dtype == np.bool_
        output_arrays.extend([build.carrier_cyc_um, build.fourier, build.spatial, build.written])
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
            build.index = 5
    for event in actual.trace:
        assert type(event.time_index) is int and type(event.direction_index) is int
        assert type(event.details) is tuple
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
            event.kind = "changed"
        for _, value in event.details:
            if isinstance(value, np.ndarray):
                output_arrays.append(value)
            elif isinstance(value, (np.generic, list, dict)):
                pytest.fail(
                    "diagnostic scalars/sequences must use the declared immutable Python types"
                )
    for i, value in enumerate(output_arrays):
        assert value.flags.owndata and not value.flags.writeable
        assert not np.shares_memory(value, bands.quadratures)
        assert not np.shares_memory(value, transfer.samples)
        assert not np.shares_memory(value, initial)
        for other in output_arrays[:i]:
            assert not np.shares_memory(value, other)
    snapshot = actual.raw_modulation.copy()
    bands.quadratures.fill(123)
    initial.fill(99)
    assert_array_equal(actual.raw_modulation, snapshot)
    assert math.isfinite(abs(snapshot).max())


@pytest.mark.parametrize("dtype", [np.int16, np.float16, np.float32, np.float64])
def test_valid_readonly_strided_floor_kinds_are_copied_and_resolved(dtype):
    bands = dc_bands()
    # Integral positive floor 1 and dyadic floating floor .5 are both legal.
    buffer = np.array([1 if np.issubdtype(dtype, np.integer) else 0.5, 7], dtype=dtype)
    floors = buffer[::2]
    floors.flags.writeable = False
    actual = estimate(
        bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False, amplitude_floors=floors
    )
    magnitude = float(floors[0])
    close(abs(actual.modulation[0, 0, 0]), magnitude)
    assert dict(actual.resolved_settings)["amplitude_floors"] == (magnitude,)
    buffer[0] = 2
    assert dict(actual.resolved_settings)["amplitude_floors"] == (magnitude,)


def test_finite_positive_noise_has_no_float32_magnitude_cap_or_estimator_weight():
    bands = dc_bands()
    bands.noise_variance_factors[:] = [[1e-300, 1e300]]
    actual = estimate(bands, unit_transfer(), np.zeros((1, 2)), search_carriers=False)
    close(actual.raw_modulation, [[[0.25 + 0.125j]]])
    close(events(actual, "evaluation")[0]["SX"], 2)


def test_one_order_is_not_a_known_fit_domain():
    rejection(
        bands_record(orders=1, shape=(2, 1, 2)),
        unit_transfer(1),
        np.zeros((1, 2)),
        "(?i)(order|band)",
        search_carriers=False,
    )
