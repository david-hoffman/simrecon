"""Blind public-contract tests for raw point-bead calibration, P01--P24."""

from __future__ import annotations

import warnings
from collections import UserDict
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from inspect import Parameter, signature
from itertools import combinations
from types import SimpleNamespace
from typing import Any, Literal

import numpy as np
import pytest
from numpy.typing import NDArray

import simrecon
from raw_point_bead_fixture import (
    ACTUAL,
    CANONICAL,
    EPS,
    SPACING,
    assert_observation,
    converted_correction,
    fit_stored,
    forward_images,
    observe,
    physical_images,
    represented_matrix,
    root,
)
from simrecon import (
    EmpiricalVolumeResponse,
    RawAcquisition,
    SimreconError,
    VolumePhaseComponents,
    correct_linear_response,
    declare_acquisition,
    prepare_empirical_volume_response,
    separate_volume_phases,
)

Array = NDArray[Any]


@pytest.fixture
def calibrate() -> Any:
    name = "calibrate_raw_point_bead"
    assert hasattr(simrecon, name), "Required public calibration export is absent"
    return getattr(simrecon, name)


def declare(
    images: Array,
    *,
    axes: tuple[str, ...] = ("orientation", "phase", "z", "y", "x"),
    nominal: bool = False,
    unit: Any = " count ",
    sampling: Any = None,
) -> RawAcquisition:
    raw = images[None] if images.ndim == 4 else images
    config: dict[str, Any] = {
        "version": 1,
        "acquisition_kind": "sim_beads",
        "axes": list(axes),
        "intensity_unit": unit,
        "acquisition_id": "raw-example",
        "calibration_id": "opaque-pairing",
        "sampling_um": sampling,
        "wavelengths_nm": {"0": 532},
    }
    if nominal:
        command_axes = [a for a in axes if a not in ("z", "y", "x")]
        command_shape = tuple(raw.shape[axes.index(a)] for a in command_axes)
        config["nominal_phases_rad"] = np.full(command_shape, 0.125).tolist()
    return declare_acquisition(
        raw,
        config=config,
        original_metadata={
            "header": b"opaque\x00",
            "flags": ["bad-pixel", "saturated"],
            "nested": (None, {"uninterpreted": float("inf")}),
        },
    )


def arguments(**changes: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "group": {"orientation": 0},
        "offset": 0,
        "response": 1,
        "output_unit": " electron ",
        "phases_rad": ACTUAL.copy(),
        "voxel_size_um": SPACING,
    }
    values.update(changes)
    return values


def equal_tree(actual: Any, expected: Any) -> None:
    assert type(actual) is type(expected)
    if isinstance(actual, np.ndarray):
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        # Numeric snapshots promise signed values, dtype and byte order, but not
        # the padding bytes of wider floating representations.
        np.testing.assert_array_equal(actual, expected)
        if actual.dtype.kind == "f":
            np.testing.assert_array_equal(np.signbit(actual), np.signbit(expected))
        elif actual.dtype.kind == "c":
            np.testing.assert_array_equal(
                np.signbit(np.real(actual)), np.signbit(np.real(expected))
            )
            np.testing.assert_array_equal(
                np.signbit(np.imag(actual)), np.signbit(np.imag(expected))
            )
    elif isinstance(actual, dict):
        assert actual.keys() == expected.keys()
        for key in actual:
            equal_tree(actual[key], expected[key])
    elif isinstance(actual, (tuple, list)):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            equal_tree(a, b)
    elif isinstance(actual, float) and np.isnan(actual):
        assert np.isnan(expected)
    else:
        assert actual == expected
        if isinstance(actual, float) and actual == 0:
            assert np.signbit(actual) == np.signbit(expected)


def mutable_leaves(value: Any) -> list[Any]:
    if isinstance(value, np.ndarray):
        return [value]
    if isinstance(value, dict):
        return [value] + [leaf for v in value.values() for leaf in mutable_leaves(v)]
    if isinstance(value, (tuple, list)):
        return ([value] if isinstance(value, list) else []) + [
            leaf for v in value for leaf in mutable_leaves(v)
        ]
    return []


def independent(output: Any, caller: Any) -> None:
    for a in mutable_leaves(output):
        for b in mutable_leaves(caller):
            assert a is not b
            if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
                assert not np.shares_memory(a, b)


def record_snapshot(acquisition: RawAcquisition) -> dict[str, Any]:
    return {f.name: deepcopy(getattr(acquisition, f.name)) for f in fields(acquisition)}


def result_arrays(result: Any) -> list[Array]:
    return [
        result.components.dc,
        result.components.c1,
        result.components.c2,
        result.response.values,
        result.response.fz_per_um,
        result.response.fy_per_um,
        result.response.fx_per_um,
    ]


def assert_code(calibrate: Any, acquisition: Any, code: str, **changes: Any) -> None:
    kwargs = arguments(**changes)
    before = deepcopy(kwargs)
    source = record_snapshot(acquisition) if isinstance(acquisition, RawAcquisition) else None
    source_bytes = acquisition.data.tobytes() if isinstance(acquisition, RawAcquisition) else None
    with pytest.raises(SimreconError) as caught:
        calibrate(acquisition, **kwargs)
    assert caught.value.code == code
    equal_tree(kwargs, before)
    if source is not None:
        equal_tree(record_snapshot(acquisition), source)
        assert acquisition.data.tobytes() == source_bytes


def test_independent_observer_self_checks_and_existing_public_composition() -> None:
    """Supplementary initially-passing evidence, never the sole composition oracle."""
    from fractions import Fraction

    cosine, sine = root(Fraction(1, 4))
    assert abs(cosine) < Decimal("1e-100")
    assert abs(sine + 1) < Decimal("1e-100")
    dc = np.array([[[10.0, 1.0], [2.0, 3.0]]])
    c1 = np.full(dc.shape, 2 - 1j)
    c2 = np.full(dc.shape, 3 + 4j)
    images = forward_images(dc, c1=c1, c2=c2)
    coordinates, error = fit_stored(images, ACTUAL)
    for row, expected in zip(
        coordinates, (dc, np.real(c1), np.imag(c1), np.real(c2), np.imag(c2)), strict=True
    ):
        np.testing.assert_allclose(
            np.array([float(v) for v in row]), expected.ravel(), atol=float(error), rtol=0
        )
    acquisition = declare(10 + 2 * images, nominal=True)
    correction = correct_linear_response(acquisition, offset=10, response=2, output_unit="electron")
    components = separate_volume_phases(correction.data[0], phases_rad=ACTUAL)
    response = prepare_empirical_volume_response(
        components.dc, c1=components.c1, c2=components.c2, voxel_size_um=SPACING
    )

    result = SimpleNamespace(components=components, response=response)
    assert_observation(
        result, observe(converted_correction(acquisition.data[0], 10, 2), ACTUAL, SPACING)
    )


def test_public_exports_binding_and_frozen_exact_records(calibrate: Any) -> None:
    record_name = "PointBeadCalibration"
    assert hasattr(simrecon, record_name)
    acquisition = declare(physical_images(ACTUAL))
    kwargs = arguments()
    result = calibrate(acquisition, **kwargs)
    assert type(result) is getattr(simrecon, record_name)
    assert [f.name for f in fields(result)] == ["components", "response", "provenance"]
    assert type(result.components) is VolumePhaseComponents
    assert {f.name for f in fields(result.components)} == {"dc", "c1", "c2"}
    assert type(result.response) is EmpiricalVolumeResponse
    assert {f.name for f in fields(result.response)} == {
        "values",
        "fz_per_um",
        "fy_per_um",
        "fx_per_um",
        "voxel_size_um",
        "origin_zyx",
    }
    assert type(result.provenance) is dict
    for record, field in (
        (result, "components"),
        (result.components, "dc"),
        (result.response, "values"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(record, field, getattr(record, field))
    for key in kwargs:
        parameter = signature(calibrate).parameters[key]
        assert parameter.kind is Parameter.KEYWORD_ONLY
        assert parameter.default is Parameter.empty
        omitted = kwargs.copy()
        omitted.pop(key)
        with pytest.raises(TypeError):
            calibrate(acquisition, **omitted)
    with pytest.raises(TypeError):
        calibrate(acquisition, kwargs["group"], **{k: v for k, v in kwargs.items() if k != "group"})
    for forbidden in ("origin", "bead", "kernel", "carrier", "brightness", "transfer", "unknown"):
        with pytest.raises(TypeError):
            calibrate(acquisition, **kwargs, **{forbidden: None})


@pytest.mark.parametrize(
    "offset_map,response_map", [(False, False), (True, False), (False, True), (True, True)]
)
@pytest.mark.parametrize(
    "layout", [CANONICAL, ("z", "phase", "orientation", "channel", "time", "y", "x")]
)
def test_full_acquisition_correction_selection_and_independent_all_bin_oracle(
    calibrate: Any, offset_map: bool, response_map: bool, layout: tuple[str, ...]
) -> None:
    signals = np.empty((2, 2, 2, len(ACTUAL), 2, 3, 4))
    for t in range(2):
        for c in range(2):
            for o in range(2):
                signals[t, c, o] = physical_images(
                    ACTUAL, brightness=80 + 16 * t + 8 * c, orientation=o
                )
                signals[t, c, o, :, 0, 1, 2] += np.arange(len(ACTUAL)) ** 2 / 64
    index = np.arange(signals.size).reshape(signals.shape)
    offset = (7 + (index % 11) / 8).astype(">f8") if offset_map else 7
    response = (1.5 + (index % 7) / 4).astype(">f8") if response_map else 2
    raw = offset + response * signals
    source = np.transpose(raw, tuple(CANONICAL.index(a) for a in layout))
    acquisition = declare(source, axes=layout, nominal=True, sampling={"z": 9, "y": 8, "x": 7})
    group = {"orientation": 1, "time": 1, "channel": 0}
    result = calibrate(acquisition, **arguments(group=group, offset=offset, response=response))
    corrected = converted_correction(raw, offset, response)[1, 0, 1]
    oracle = observe(corrected, ACTUAL, SPACING)
    assert_observation(result, oracle)
    assert np.max(np.abs(result.components.dc - corrected.mean(axis=0))) > 0.1
    assert np.max(np.abs(result.response.values[1].imag)) > 0.01
    assert np.max(np.abs(result.response.values[2].imag)) > 0.01
    assert not np.allclose(result.response.values[1], np.conj(result.response.values[1]))
    assert result.response.voxel_size_um == SPACING
    equal_tree(result.provenance["group"], group)
    if offset_map and layout != CANONICAL:
        assert acquisition.source_shape != acquisition.data.shape
        assert_code(
            calibrate,
            acquisition,
            "invalid_linear_response_shape",
            group=group,
            offset=np.transpose(offset, tuple(CANONICAL.index(a) for a in layout)),
            response=response,
        )


@pytest.mark.parametrize(
    "group",
    [
        {},
        {"orientation": 0, "channel": 0},
        {"orientation": 0, "time": 0},
        {"orientation": 0, "unknown": 0},
        UserDict({"orientation": 0}),
        [("orientation", 0)],
        None,
        {0: 0},
        {"Orientation": 0},
    ],
)
def test_group_exact_plain_dict_and_keys(calibrate: Any, group: Any) -> None:
    assert_code(
        calibrate, declare(physical_images(ACTUAL)), "invalid_point_bead_group", group=group
    )


class IntSubclass(int):
    """Unsupported selector scalar representation."""

    pass


class DictSubclass(dict[str, int]):
    """Unsupported selector container representation."""

    pass


@pytest.mark.parametrize("index", [-1, 1, True, False, np.int64(0), IntSubclass(0), 0.0, "0", None])
def test_group_plain_int_nonbool_nonnegative_in_range(calibrate: Any, index: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_point_bead_group",
        group={"orientation": index},
    )


def test_group_dict_subclass_rejected(calibrate: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_point_bead_group",
        group=DictSubclass(orientation=0),
    )


def test_present_singleton_group_axes_required_and_extrema_distinct(calibrate: Any) -> None:
    raw = np.stack([physical_images(ACTUAL, orientation=o) for o in range(2)])[None, None]
    acquisition = declare(raw, axes=CANONICAL)
    group = {"time": 0, "channel": 0, "orientation": 1}
    result = calibrate(acquisition, **arguments(group=group))
    assert_observation(result, observe(raw[0, 0, 1], ACTUAL, SPACING))
    other = calibrate(acquisition, **arguments(group={**group, "orientation": 0}))
    assert np.max(np.abs(result.response.values - other.response.values)) > 0.01
    for key in group:
        assert_code(
            calibrate,
            acquisition,
            "invalid_point_bead_group",
            group={k: v for k, v in group.items() if k != key},
        )
    assert_code(calibrate, acquisition, "invalid_point_bead_group", group={**group, "time": 1})
    assert_code(
        calibrate, acquisition, "invalid_point_bead_group", group={**group, "orientation": 2}
    )


@pytest.mark.parametrize("optional_axis", ["time", "channel"])
@pytest.mark.parametrize("count", [1, 2])
def test_independently_optional_group_profiles(
    calibrate: Any, optional_axis: str, count: int
) -> None:
    axes = (optional_axis, "orientation", "phase", "z", "y", "x")
    signals = np.array(
        [
            [
                physical_images(ACTUAL, brightness=64 + 64 * index, orientation=orientation)
                for orientation in range(2)
            ]
            for index in range(count)
        ]
    )
    # Optional-axis brightness differs in components even when response
    # normalization cancels it. Orientation also changes complex side orders.
    raw = 10 + 2 * signals
    acquisition = declare(raw, axes=axes, nominal=True)
    group = {optional_axis: count - 1, "orientation": 1}
    result = calibrate(acquisition, **arguments(group=group, offset=10, response=2))
    selected = converted_correction(raw, 10, 2)[count - 1, 1]
    selected_oracle = observe(selected, ACTUAL, SPACING)
    assert_observation(result, selected_oracle)
    equal_tree(result.provenance["group"], group)
    other_group = {optional_axis: 0, "orientation": 0}
    other = calibrate(acquisition, **arguments(group=other_group, offset=10, response=2))
    other_oracle = observe(converted_correction(raw, 10, 2)[0, 0], ACTUAL, SPACING)
    assert_observation(other, other_oracle)
    assert np.max(np.abs(result.response.values - other.response.values)) > 0.01
    if count == 2:
        assert np.max(np.abs(result.components.dc - other.components.dc)) > 1
    for key in group:
        assert_code(
            calibrate,
            acquisition,
            "invalid_point_bead_group",
            group={k: v for k, v in group.items() if k != key},
        )
    absent_axis = "channel" if optional_axis == "time" else "time"
    assert_code(calibrate, acquisition, "invalid_point_bead_group", group={**group, absent_axis: 0})
    assert_code(
        calibrate, acquisition, "invalid_point_bead_group", group={**group, optional_axis: count}
    )


@pytest.mark.parametrize("value", [None, {}, np.ones((1, 7, 1, 1, 1)), "acquisition"])
def test_nonrecord_acquisition_rejected(calibrate: Any, value: Any) -> None:
    assert_code(calibrate, value, "invalid_point_bead_acquisition")


@pytest.mark.parametrize("kind", ["specimen_sim", "detection_psf"])
def test_other_valid_kinds_rejected(calibrate: Any, kind: str) -> None:
    axes = ["orientation", "phase", "z", "y", "x"] if kind == "specimen_sim" else ["z", "y", "x"]
    data = physical_images(ACTUAL)[None] if kind == "specimen_sim" else np.ones((2, 3, 4))
    acquisition = declare_acquisition(
        data,
        config={"version": 1, "acquisition_kind": kind, "axes": axes, "intensity_unit": "count"},
    )
    assert_code(calibrate, acquisition, "invalid_point_bead_kind")


def test_missing_explicit_z_rejected(calibrate: Any) -> None:
    acquisition = declare_acquisition(
        np.ones((1, 7, 2, 3)),
        config={
            "version": 1,
            "acquisition_kind": "sim_beads",
            "axes": ["orientation", "phase", "y", "x"],
            "intensity_unit": " count ",
        },
    )
    assert acquisition.axes == ("orientation", "phase", "y", "x")
    assert acquisition.data.shape == (1, 7, 2, 3)
    assert_code(calibrate, acquisition, "invalid_point_bead_axes")


@pytest.mark.parametrize("shape", [(1, 1, 1), (1, 3, 4), (2, 3, 4), (3, 2, 3)])
def test_explicit_singleton_and_odd_even_nonsquare_grids(
    calibrate: Any, shape: tuple[int, int, int]
) -> None:
    images = physical_images(ACTUAL, shape=shape, bead=(shape[0] - 1, shape[1] - 1, shape[2] - 1))
    result = calibrate(declare(images), **arguments())
    assert_observation(result, observe(images, ACTUAL, SPACING))


@pytest.mark.parametrize(
    "case,code",
    [
        ("raw_nan", "invalid_linear_response_data"),
        ("raw_inf", "invalid_linear_response_data"),
        ("offset_nan", "invalid_linear_response_offset"),
        ("response_zero", "invalid_linear_response_response"),
        ("response_inf", "invalid_linear_response_response"),
        ("subtract_range", "linear_response_range"),
        ("divide_range", "linear_response_range"),
    ],
)
def test_nonselected_correction_failures_still_reject_and_selected_only_is_valid(
    calibrate: Any, case: str, code: str
) -> None:
    raw = np.stack((physical_images(ACTUAL), physical_images(ACTUAL)))
    offset = np.zeros(raw.shape)
    response = np.ones(raw.shape)
    bad = (1, 0, 0, 0, 0)
    if case == "raw_nan":
        raw[bad] = np.nan
    elif case == "raw_inf":
        raw[bad] = np.inf
    elif case == "offset_nan":
        offset[bad] = np.nan
    elif case == "response_zero":
        response[bad] = 0
    elif case == "response_inf":
        response[bad] = np.inf
    elif case == "subtract_range":
        raw[bad], offset[bad], response[bad] = np.finfo(float).max, -np.finfo(float).max, 2
    else:
        raw[bad], response[bad] = 1, np.nextafter(0.0, 1.0)
    acquisition = declare(raw)
    assert_code(calibrate, acquisition, code, offset=offset, response=response)
    selected = declare(raw[:1])
    result = calibrate(selected, **arguments(offset=offset[:1], response=response[:1]))
    assert_observation(
        result, observe(converted_correction(raw[0], offset[0], response[0]), ACTUAL, SPACING)
    )


@pytest.mark.parametrize("name", ["offset", "response"])
@pytest.mark.parametrize(
    "value",
    [
        True,
        np.float64(1),
        [1],
        1 + 0j,
        pytest.param(lambda shape: np.ones(shape, dtype=bool), id="bool-map"),
        pytest.param(lambda shape: np.ones(shape, dtype=object), id="object-map"),
        pytest.param(lambda shape: np.ones(shape, dtype=complex), id="complex-map"),
        pytest.param(lambda shape: np.ma.array(np.ones(shape), mask=False), id="masked-map"),
        float("nan"),
        float("inf"),
        10**400,
    ],
)
def test_coefficient_representation_and_conversion_errors(
    calibrate: Any, name: str, value: Any
) -> None:
    acquisition = declare(physical_images(ACTUAL))
    # Match the public canonical shape so only representation/conversion is
    # invalid. Simultaneous shape/dtype error precedence is unspecified.
    if callable(value):
        value = value(acquisition.data.shape)
    # Masked-array equality can hide both mask changes and underlying values.
    # Save plain independent observations before invoking the public operation.
    masked_before = (
        (np.ma.getmaskarray(value).copy(), np.ma.getdata(value).copy())
        if isinstance(value, np.ma.MaskedArray)
        else None
    )
    assert_code(
        calibrate,
        acquisition,
        f"invalid_linear_response_{name}",
        **{name: value},
    )
    if masked_before is not None:
        np.testing.assert_array_equal(np.ma.getmaskarray(value), masked_before[0])
        np.testing.assert_array_equal(np.ma.getdata(value), masked_before[1])


@pytest.mark.parametrize("name", ["offset", "response"])
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(1, id="builtin-int"),
        pytest.param(1.0, id="builtin-float"),
        pytest.param(np.dtype("i1"), id="signed-map"),
        pytest.param(np.dtype(">u2"), id="unsigned-map"),
        pytest.param(np.dtype(">f4"), id="float-map"),
        pytest.param(np.dtype(np.longdouble), id="longdouble-map"),
    ],
)
def test_supported_coefficient_representation_controls(
    calibrate: Any, name: str, value: Any
) -> None:
    images = physical_images(ACTUAL)
    acquisition = declare(images)
    if isinstance(value, np.dtype):
        value = np.ones(acquisition.data.shape, dtype=value)
    kwargs = arguments(**{name: value})
    source_before, kwargs_before = record_snapshot(acquisition), deepcopy(kwargs)
    source_bytes = acquisition.data.tobytes()
    result = calibrate(acquisition, **kwargs)
    # Every supported representation supplies exactly one. The stored-input
    # expectation is independent of product output and all-bin assertions
    # also prove that later calibration stages accept this control.
    corrected = converted_correction(images, 1 if name == "offset" else 0, 1)
    assert_observation(result, observe(corrected, ACTUAL, SPACING))
    equal_tree(record_snapshot(acquisition), source_before)
    assert acquisition.data.tobytes() == source_bytes
    equal_tree(kwargs, kwargs_before)


@pytest.mark.parametrize("name", ["offset", "response"])
@pytest.mark.parametrize("shape", [(), (3, 4), (1, 7, 1, 1, 1), (7, 2, 3, 4)])
def test_coefficient_full_canonical_shape_no_broadcast(
    calibrate: Any, name: str, shape: tuple[int, ...]
) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_linear_response_shape",
        **{name: np.ones(shape)},
    )


@pytest.mark.parametrize("response", [0, -0.0, -1, -np.nextafter(0.0, 1.0)])
def test_nonpositive_response_rejected(calibrate: Any, response: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_linear_response_response",
        response=response,
    )


@pytest.mark.parametrize("unit", [None, "", 3, True])
def test_output_unit_required(calibrate: Any, unit: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_linear_response_unit",
        output_unit=unit,
    )


def test_input_unit_required(calibrate: Any) -> None:
    acquisition = declare(physical_images(ACTUAL), unit=None)
    assert_code(calibrate, acquisition, "invalid_linear_response_unit")


@pytest.mark.parametrize(
    "phases,code",
    [
        ([0.0] * 7, "invalid_volume_phase_angles"),
        (np.ma.array(ACTUAL), "invalid_volume_phase_angles"),
        (np.ones(7, dtype=bool), "invalid_volume_phase_angles_dtype"),
        (ACTUAL.astype(complex), "invalid_volume_phase_angles_dtype"),
        (ACTUAL.astype(object), "invalid_volume_phase_angles_dtype"),
        (np.ones(7, dtype="U1"), "invalid_volume_phase_angles_dtype"),
        (np.array(0.0), "invalid_volume_phase_angles_shape"),
        (ACTUAL[:, None], "invalid_volume_phase_angles_shape"),
        (ACTUAL[:5], "invalid_volume_phase_angles_shape"),
        (np.array([np.nan, *ACTUAL[1:]]), "nonfinite_volume_phase_angles"),
        (np.array([np.inf, *ACTUAL[1:]]), "nonfinite_volume_phase_angles"),
        (np.zeros(7), "rank_deficient_volume_phases"),
        (np.array([0, 1, 0, 1, 0, 1, 0]), "rank_deficient_volume_phases"),
    ],
)
def test_actual_phase_rejections_propagate(calibrate: Any, phases: Any, code: str) -> None:
    assert_code(calibrate, declare(physical_images(ACTUAL)), code, phases_rad=phases)


def test_too_few_exposures_propagates_shape_error(calibrate: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL[:4])),
        "invalid_volume_phase_shape",
        phases_rad=ACTUAL[:4],
    )


def test_five_exposure_full_rank_minimum_with_independent_expectations(calibrate: Any) -> None:
    phases = np.arange(5, dtype=np.float64) * (2 * np.pi / 5)
    images = physical_images(phases)
    acquisition = declare(10 + 2 * images, nominal=True)
    result = calibrate(acquisition, **arguments(offset=10, response=2, phases_rad=phases))
    corrected = converted_correction(acquisition.data[0], 10, 2)
    assert_observation(result, observe(corrected, phases, SPACING))
    equal_tree(result.provenance["phases_rad"]["supplied"], phases)
    equal_tree(result.provenance["phases_rad"]["applied"], phases)


@pytest.mark.parametrize(
    "phases",
    [
        ACTUAL,
        np.concatenate((ACTUAL, ACTUAL[:2])),
        np.arange(7, dtype=">i8"),
        np.array([1e308, -1e308, 2e307, -2e307, 3e307, -3e307, 4e307]),
    ],
)
def test_repeated_unequal_integer_endian_and_huge_actual_phases(
    calibrate: Any, phases: Array
) -> None:
    dc = np.array([[[12.0, 1.0], [-0.25, 2.0]]])
    c1 = np.array([[[0.5 + 0.2j, -0.3 + 0.1j], [0.25 - 0.125j, 0.5j]]])
    images = forward_images(dc, phases=phases, c1=c1, c2=2j * c1)
    padded = np.empty(2 * len(phases), dtype=phases.dtype)
    padded[::2] = phases
    supplied = padded[::2]
    supplied.flags.writeable = False
    result = calibrate(declare(images, nominal=True), **arguments(phases_rad=supplied))
    assert_observation(result, observe(images, supplied, SPACING))
    phase_record = result.provenance["phases_rad"]
    equal_tree(phase_record["supplied"], np.array(supplied, order="C"))
    equal_tree(phase_record["applied"], np.array(supplied, dtype=np.float64, order="C"))


def test_nominal_commands_absent_or_unidentifiable_never_substitute_actual(calibrate: Any) -> None:
    images = physical_images(ACTUAL)
    a = calibrate(declare(images), **arguments())
    b = calibrate(declare(images, nominal=True), **arguments())
    assert_observation(a, observe(images, ACTUAL, SPACING))
    for av, bv in zip(result_arrays(a), result_arrays(b), strict=True):
        np.testing.assert_array_equal(av, bv)
    wrong_phases = ACTUAL + np.array([0.0, 0.11, -0.2, 0.3, -0.09, 0.13, -0.25])
    wrong = calibrate(declare(images, nominal=True), **arguments(phases_rad=wrong_phases))
    assert np.max(np.abs(wrong.response.values - a.response.values)) > 0.005


def test_weak_but_full_rank_phases_have_no_condition_cutoff(calibrate: Any) -> None:
    phases = np.linspace(0, 0.02, 7)
    h = represented_matrix(phases)
    singular = np.linalg.svd(h, compute_uv=False)
    assert np.all(singular > float(EPS) * len(phases) * singular[0])
    assert np.linalg.cond(h) > 10
    images = np.broadcast_to(np.array([[[8.0, 1.0]]]), (7, 1, 1, 2)).copy()
    result = calibrate(declare(images), **arguments(phases_rad=phases))
    assert np.all(np.isfinite(result.response.values))
    assert result.response.origin_zyx == (0, 0, 0)


@pytest.mark.parametrize("spacing", [(np.float32(0.31), np.int64(1), 2), [0.31, 0.17, 0.09]])
def test_spacing_container_scalars_and_independent_source_sampling(
    calibrate: Any, spacing: Any
) -> None:
    images = physical_images(ACTUAL)
    a = calibrate(declare(images, sampling=None), **arguments(voxel_size_um=spacing))
    b = calibrate(
        declare(images, sampling={"z": 3, "y": 2, "x": 1}), **arguments(voxel_size_um=spacing)
    )
    assert_observation(a, observe(images, ACTUAL, spacing))
    for av, bv in zip(result_arrays(a), result_arrays(b), strict=True):
        np.testing.assert_array_equal(av, bv)
    record = b.provenance["voxel_size_um"]
    assert record["source"] == "supplied"
    equal_tree(record["supplied"], spacing)
    assert record["applied"] == tuple(float(v) for v in spacing) == b.response.voxel_size_um
    assert b.provenance["source_metadata"]["sampling_um"] == {"z": 3.0, "y": 2.0, "x": 1.0}


def ndarray_spacing(dtype: Any, storage: str) -> tuple[Array, Array]:
    """Permitted scalar examples; object storage is not a dtype rejection rule."""
    if np.dtype(dtype).kind == "O":
        values = [np.float32(0.31), np.int64(2), 0.09]
    elif np.dtype(dtype) == np.dtype("u8"):
        values = [2**53 + 1, 2**53 + 3, 2**53 + 5]
    elif np.dtype(dtype).kind in "iu":
        values = [1, 2, 3]
    else:
        values = [0.31, 0.17, 0.09]
    if storage == "contiguous":
        backing = np.array(values, dtype=dtype)
        return backing, backing
    backing = np.full(6, 7, dtype=dtype)
    if storage == "strided":
        spacing = backing[::2]
    else:
        assert storage == "reversed-readonly"
        spacing = backing[4::-2]
    spacing[:] = values
    if storage == "reversed-readonly":
        spacing.flags.writeable = False
    return spacing, backing


@pytest.mark.parametrize("dtype", ["i1", ">i2", "u8", "f2", ">f4", ">f8", np.longdouble, object])
@pytest.mark.parametrize("storage", ["contiguous", "strided", "reversed-readonly"])
def test_ndarray_spacing_numeric_provenance_ownership_and_preservation(
    calibrate: Any, dtype: Any, storage: str
) -> None:
    spacing, backing = ndarray_spacing(dtype, storage)
    spacing_before, backing_before = spacing.copy(), backing.copy()
    layout_before = (spacing.strides, spacing.flags.writeable, backing.flags.writeable)
    applied = tuple(float(value) for value in spacing_before)
    images = physical_images(ACTUAL)
    raw = 10 + 2 * images
    acquisitions = [
        declare(raw, sampling=None),
        declare(raw, sampling={"z": 3, "y": 2, "x": 1}),
    ]
    sources_before = [record_snapshot(acquisition) for acquisition in acquisitions]
    kwargs = arguments(offset=10, response=2, voxel_size_um=spacing)
    kwargs_before = deepcopy(kwargs)
    results = [calibrate(acquisition, **kwargs) for acquisition in acquisitions]
    # Stored correction, represented fit and every signed bin are independent
    # expectations. Frequencies use the converted spacing, never source sampling.
    oracle = observe(converted_correction(raw, 10, 2), ACTUAL, spacing_before)
    for result, source in zip(results, sources_before, strict=True):
        assert_observation(result, oracle)
        equal_tree(result.provenance["source_metadata"]["sampling_um"], source["sampling_um"])
        record = result.provenance["voxel_size_um"]
        assert type(record) is dict
        assert set(record) == {"source", "supplied", "applied"}
        assert record["source"] == "supplied"
        supplied = record["supplied"]
        equal_tree(supplied, spacing_before)
        assert supplied.dtype.str == spacing.dtype.str
        assert supplied.shape == (3,)
        assert supplied.flags.c_contiguous and supplied.flags.owndata
        assert type(record["applied"]) is tuple
        assert all(type(value) is float for value in record["applied"])
        assert record["applied"] == applied == result.response.voxel_size_um
        independent(
            [result.provenance, result_arrays(result)],
            [kwargs, backing, *[acquisition.data for acquisition in acquisitions]],
        )
        for array in result_arrays(result):
            assert not np.shares_memory(supplied, array)
    independent(
        [results[0].provenance, result_arrays(results[0])],
        [results[1].provenance, result_arrays(results[1])],
    )
    equal_tree(kwargs, kwargs_before)
    equal_tree(spacing, spacing_before)
    equal_tree(backing, backing_before)
    assert (spacing.strides, spacing.flags.writeable, backing.flags.writeable) == layout_before
    for acquisition, source in zip(acquisitions, sources_before, strict=True):
        equal_tree(record_snapshot(acquisition), source)

    saved_second = deepcopy([results[1].provenance, result_arrays(results[1])])
    results[0].provenance["voxel_size_um"]["supplied"][0] = 8
    equal_tree(spacing, spacing_before)
    equal_tree(backing, backing_before)
    equal_tree([results[1].provenance, result_arrays(results[1])], saved_second)
    saved_first = deepcopy([results[0].provenance, result_arrays(results[0])])
    # Mutate writable backing even when the supplied view is read-only.
    backing[:] = 9
    equal_tree([results[0].provenance, result_arrays(results[0])], saved_first)
    equal_tree([results[1].provenance, result_arrays(results[1])], saved_second)


@pytest.mark.parametrize("failure", ["phase-rank", "frequency-range"])
def test_ndarray_spacing_preserved_on_inherited_rejection(calibrate: Any, failure: str) -> None:
    spacing, backing = ndarray_spacing(">f8", "reversed-readonly")
    changes: dict[str, Any] = {}
    if failure == "phase-rank":
        changes["phases_rad"] = np.zeros(len(ACTUAL))
        code = "rank_deficient_volume_phases"
    else:
        backing[4] = np.nextafter(0.0, 1.0)
        code = "unrepresentable_otf_frequencies"
    spacing_before, backing_before = spacing.copy(), backing.copy()
    layout_before = (spacing.strides, spacing.flags.writeable, backing.flags.writeable)
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        code,
        voxel_size_um=spacing,
        **changes,
    )
    equal_tree(spacing, spacing_before)
    equal_tree(backing, backing_before)
    assert (spacing.strides, spacing.flags.writeable, backing.flags.writeable) == layout_before


def invalid_ndarray_spacing(case: str) -> tuple[Array, Array]:
    """Unsupported container/shape/leaves, each with visible caller backing."""
    dtype = np.float64 if case in ("zero", "negative", "nan", "inf") else object
    backing = np.full(8, 7, dtype=dtype)
    spacing = backing[4::-2]
    spacing[:] = [0.31, 0.17, 0.09]
    if case == "scalar":
        spacing = backing[4:5].reshape(())
    elif case == "matrix":
        spacing = spacing.reshape(1, 3)
    elif case == "empty":
        spacing = backing[:0]
    elif case == "short":
        spacing = spacing[:2]
    elif case == "long":
        spacing = backing[::2]
    elif case == "subclass":
        spacing = spacing.view(ArraySubclass)
    elif case == "masked":
        spacing = np.ma.array(spacing, mask=[False, True, False], copy=False)
    else:
        leaves: dict[str, Any] = {
            "bool": True,
            "numpy-bool": np.bool_(True),
            "string": "0.31",
            "bytes": b"0.31",
            "complex": 0.31 + 0j,
            "none": None,
            "list": [0.31],
            "zero": 0,
            "negative": -1,
            "nan": np.nan,
            "inf": np.inf,
            "huge-int": 10**400,
        }
        spacing[0] = leaves[case]
    spacing.flags.writeable = False
    return spacing, backing


@pytest.mark.parametrize(
    "case",
    [
        "scalar",
        "matrix",
        "empty",
        "short",
        "long",
        "subclass",
        "masked",
        "bool",
        "numpy-bool",
        "string",
        "bytes",
        "complex",
        "none",
        "list",
        "zero",
        "negative",
        "nan",
        "inf",
        "huge-int",
    ],
)
def test_ndarray_spacing_boundaries_and_rejection_preservation(calibrate: Any, case: str) -> None:
    spacing, backing = invalid_ndarray_spacing(case)
    spacing_before, backing_before = deepcopy(spacing), deepcopy(backing)
    mask_before = np.ma.getmaskarray(spacing).copy()
    layout_before = (spacing.strides, spacing.flags.writeable, backing.flags.writeable)
    assert_code(
        calibrate, declare(physical_images(ACTUAL)), "invalid_otf_voxel_size", voxel_size_um=spacing
    )
    equal_tree(spacing, spacing_before)
    equal_tree(backing, backing_before)
    np.testing.assert_array_equal(np.ma.getmaskarray(spacing), mask_before)
    assert (spacing.strides, spacing.flags.writeable, backing.flags.writeable) == layout_before


@pytest.mark.parametrize(
    "spacing",
    [
        None,
        "123",
        [],
        (1, 2),
        (1, 2, 3, 4),
        (True, 1, 1),
        (0, 1, 1),
        (-1, 1, 1),
        (np.nan, 1, 1),
        (np.inf, 1, 1),
        (1j, 1, 1),
        (10**400, 1, 1),
        ("1", 1, 1),
    ],
)
def test_spacing_rejections(calibrate: Any, spacing: Any) -> None:
    assert_code(
        calibrate, declare(physical_images(ACTUAL)), "invalid_otf_voxel_size", voxel_size_um=spacing
    )


@pytest.mark.parametrize(
    "spacing", [(np.nextafter(0.0, 1.0), 1, 1), (1, 1, np.nextafter(0.0, 1.0))]
)
def test_unrepresentable_frequency_rejection(calibrate: Any, spacing: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "unrepresentable_otf_frequencies",
        voxel_size_um=spacing,
    )


def test_extreme_spacing_without_period_overflow_and_singleton_minimum(calibrate: Any) -> None:
    images = physical_images(ACTUAL, shape=(1, 2, 3), bead=(0, 1, 2))
    spacing = (np.nextafter(0.0, 1.0), np.finfo(float).max, np.finfo(float).max)
    result = calibrate(declare(images), **arguments(voxel_size_um=spacing))
    assert_observation(result, observe(images, ACTUAL, spacing))


@pytest.mark.parametrize(
    "dc,code",
    [
        (np.array([[[-1.0, -2.0]]]), "no_positive_bead_peak"),
        (np.zeros((1, 1, 2)), "no_positive_bead_peak"),
        (np.array([[[2.0, 2.0]]]), "ambiguous_bead_peak"),
        (np.array([[[2.0, -3.0]]]), "nonpositive_empirical_response_mass"),
        (np.array([[[2.0, -2.0]]]), "nonpositive_empirical_response_mass"),
    ],
)
def test_observed_peak_and_exact_mass_rejections(calibrate: Any, dc: Array, code: str) -> None:
    assert_code(calibrate, declare(np.repeat(dc[None], len(ACTUAL), axis=0)), code)


@pytest.mark.parametrize(
    "dc", [np.array([[[9.0, 3.0, 3.0]]]), np.array([[[2.0, -1.0]]]), np.array([[[8.0, -7.0, 2.0]]])]
)
def test_signed_dc_secondary_peaks_and_common_mass_with_zero_sides(
    calibrate: Any, dc: Array
) -> None:
    images = np.repeat(dc[None], len(ACTUAL), axis=0)
    result = calibrate(declare(images), **arguments())
    assert_observation(result, observe(images, ACTUAL, SPACING))
    if np.min(dc) < 0:
        assert np.max(np.abs(result.response.values[0])) > 1


def test_exact_mass_cancellation_and_overflowing_total_are_not_extra_cutoffs(
    calibrate: Any,
) -> None:
    # Repeating observations have identical fitted columns. Choose exactly represented
    # cancellation with a comfortable positive residual, rather than an ambiguous q mass.
    for dc in (
        np.array([[[2.0**30, -(2.0**30) + 1, 2.0]]]),
        np.array(
            [[[np.finfo(float).max * 0.75, np.finfo(float).max / 2, np.finfo(float).max / 2]]]
        ),
    ):
        images = np.repeat(dc[None], len(ACTUAL), axis=0)
        result = calibrate(declare(images), **arguments())
        assert result.response.origin_zyx == (0, 0, 0)
        assert np.all(np.isfinite(result.response.values))
        assert_observation(result, observe(images, ACTUAL, SPACING))


def test_phase_origin_joint_roll_and_physical_bead_gauges(calibrate: Any) -> None:
    images = physical_images(ACTUAL)
    base = calibrate(declare(images), **arguments())
    base_oracle = observe(images, ACTUAL, SPACING)
    assert_observation(base, base_oracle)
    roll = (1, -1, 2)
    rolled_images = np.roll(images, roll, axis=(1, 2, 3))
    rolled = calibrate(declare(rolled_images), **arguments())
    rolled_oracle = observe(rolled_images, ACTUAL, SPACING)
    assert_observation(rolled, rolled_oracle)
    assert np.all(
        np.abs(rolled.response.values - base.response.values)
        <= (rolled_oracle.budgets + base_oracle.budgets)
    )
    alpha = 0.37
    shifted = calibrate(declare(images), **arguments(phases_rad=ACTUAL + alpha))
    shifted_oracle = observe(images, ACTUAL + alpha, SPACING)
    assert_observation(shifted, shifted_oracle)
    for order in range(3):
        factor = np.exp(-1j * order * alpha)
        # Both independent fit/response budgets plus a conservative allowance for
        # the represented phase-shift/generator algebra on these small angles.
        budget = shifted_oracle.budgets[order] + base_oracle.budgets[order]
        budget += 32 * float(EPS) * (1 + np.abs(base_oracle.values[order]))
        assert np.all(
            np.abs(shifted_oracle.values[order] - base_oracle.values[order] * factor) <= budget
        )
        assert np.all(
            np.abs(shifted.response.values[order] - base.response.values[order] * factor) <= budget
        )
    moved_images = physical_images(ACTUAL, bead=(1, 2, 0))
    moved = calibrate(declare(moved_images), **arguments())
    moved_oracle = observe(moved_images, ACTUAL, SPACING)
    assert_observation(moved, moved_oracle)
    theta = -2 * np.pi * 3 / 4
    for order in range(3):
        factor = np.exp(1j * order * theta)
        budget = moved_oracle.budgets[order] + base_oracle.budgets[order]
        budget += 32 * float(EPS) * (1 + np.abs(base_oracle.values[order]))
        assert np.all(
            np.abs(moved_oracle.values[order] - base_oracle.values[order] * factor) <= budget
        )
        assert np.all(
            np.abs(moved.response.values[order] - base.response.values[order] * factor) <= budget
        )
    assert np.max(np.abs(moved.response.values[1] - base.response.values[1])) > 0.01


def test_exact_provenance_source_snapshots_storage_and_caller_preservation(calibrate: Any) -> None:
    images = physical_images(ACTUAL)
    raw = (11 + 2 * images)[None].astype(">f8")
    acquisition = declare(raw, nominal=True, sampling={"z": 1, "y": 2, "x": 3})
    offset = np.full(raw.shape, -0.0, dtype=">f4")
    response = np.full(raw.shape, 2, dtype=">u2")
    phases = ACTUAL.astype(">f8")
    spacing = [np.float32(0.31), np.int64(1), 2]
    group = {"orientation": 0}
    kwargs = arguments(
        group=group, offset=offset, response=response, phases_rad=phases, voxel_size_um=spacing
    )
    source_before, kwargs_before = record_snapshot(acquisition), deepcopy(kwargs)
    source_bytes = acquisition.data.tobytes()
    result = calibrate(acquisition, **kwargs)
    second = calibrate(acquisition, **kwargs)
    equal_tree(record_snapshot(acquisition), source_before)
    assert acquisition.data.tobytes() == source_bytes
    equal_tree(kwargs, kwargs_before)
    p = result.provenance
    assert set(p) == {
        "model",
        "group",
        "source_metadata",
        "linear_response",
        "phases_rad",
        "voxel_size_um",
        "bead_compensation",
        "response_gauge",
    }
    assert p["model"] == "point_bead_identity_v1"
    assert p["bead_compensation"] == "identity"
    assert p["response_gauge"] == "observed_dc_peak_with_supplied_phase_origin"
    equal_tree(p["group"], group)
    source_expected = {k: v for k, v in source_before.items() if k != "data"}
    equal_tree(p["source_metadata"], source_expected)
    linear = p["linear_response"]
    assert set(linear) == {"model", "equation", "input_unit", "output_unit", "offset", "response"}
    assert linear["model"] == "linear_response_v1"
    assert linear["equation"] == "raw=offset+response*signal"
    assert linear["input_unit"] == " count "
    assert linear["output_unit"] == " electron "
    for name, supplied in (("offset", offset), ("response", response)):
        assert set(linear[name]) == {"source", "supplied", "applied"}
        assert linear[name]["source"] == "supplied"
        equal_tree(linear[name]["supplied"], supplied)
        equal_tree(linear[name]["applied"], supplied.astype(np.float64))
    assert set(p["phases_rad"]) == {"source", "supplied", "applied"}
    assert p["phases_rad"]["source"] == "supplied_actual"
    equal_tree(p["phases_rad"]["supplied"], phases)
    equal_tree(p["phases_rad"]["applied"], phases.astype(np.float64))
    assert not np.shares_memory(p["phases_rad"]["supplied"], p["phases_rad"]["applied"])
    for snapshot in mutable_leaves(p):
        if isinstance(snapshot, np.ndarray):
            assert type(snapshot) is np.ndarray
            assert snapshot.flags.c_contiguous
            assert snapshot.flags.owndata
    assert set(p["voxel_size_um"]) == {"source", "supplied", "applied"}
    equal_tree(p["voxel_size_um"]["supplied"], spacing)
    assert p["voxel_size_um"]["source"] == "supplied"
    assert p["voxel_size_um"]["applied"] == tuple(float(v) for v in spacing)
    arrays = result_arrays(result)
    for index, array in enumerate(arrays):
        assert type(array) is np.ndarray
        assert array.flags.c_contiguous and array.flags.owndata and array.flags.writeable
        assert array.dtype == np.dtype(np.float64 if index in (0, 4, 5, 6) else np.complex128)
    for a, b in combinations(arrays, 2):
        assert not np.shares_memory(a, b)
    independent(
        [p, arrays], [kwargs, {f.name: getattr(acquisition, f.name) for f in fields(acquisition)}]
    )
    independent([p, arrays], [second.provenance, result_arrays(second), acquisition.data, kwargs])
    saved = deepcopy([second.provenance, result_arrays(second)])
    result.components.dc.flat[0] = -99
    result.response.values.flat[0] = 42j
    p["group"]["orientation"] = 8
    p["source_metadata"]["original_metadata"]["flags"].append("new")
    p["phases_rad"]["supplied"][0] = 99
    p["voxel_size_um"]["supplied"][0] = 88
    equal_tree([second.provenance, result_arrays(second)], saved)
    equal_tree(record_snapshot(acquisition), source_before)
    assert acquisition.data.tobytes() == source_bytes
    equal_tree(kwargs, kwargs_before)


@pytest.mark.parametrize(
    "dtype", ["i1", "u1", ">i2", ">u4", "i8", "u8", "f2", ">f4", ">f8", np.longdouble]
)
def test_raw_width_endian_readonly_strided_and_scalar_provenance(
    calibrate: Any, dtype: Any
) -> None:
    dc = np.array([[[12, 1], [0, 2]]], dtype=dtype)
    images = np.repeat(dc[None], len(ACTUAL), axis=0)
    backing = np.empty((*images.shape[:-1], images.shape[-1] * 2), dtype=images.dtype)
    backing[..., ::2] = images
    raw = backing[..., ::2]
    raw.flags.writeable = False
    acquisition = declare(raw)
    result = calibrate(acquisition, **arguments(offset=-2, response=2.0, output_unit=" count "))
    assert_observation(result, observe(converted_correction(images, -2, 2.0), ACTUAL, SPACING))
    for name, supplied, applied in (("offset", -2, -2.0), ("response", 2.0, 2.0)):
        equal_tree(result.provenance["linear_response"][name]["supplied"], supplied)
        equal_tree(result.provenance["linear_response"][name]["applied"], applied)


def test_subnormal_response_and_signed_underflow_no_floor_or_clipping(calibrate: Any) -> None:
    tiny = float(np.nextafter(0.0, 1.0))
    dc = np.array([[[16, -1, 2]]], dtype=np.float64)
    raw = np.repeat((dc * tiny)[None], len(ACTUAL), axis=0)
    result = calibrate(declare(raw), **arguments(response=tiny))
    assert_observation(result, observe(converted_correction(raw, 0, tiny), ACTUAL, SPACING))
    assert result.components.dc[0, 0, 1] < 0
    # Full-array correction accepts a nonselected negative quotient underflow to -0.
    groups = np.stack((physical_images(ACTUAL), physical_images(ACTUAL)))
    groups[1, 0, 0, 0, 0] = -tiny
    response = np.ones(groups.shape)
    response[1, 0, 0, 0, 0] = 2
    result = calibrate(declare(groups), **arguments(response=response))
    assert_observation(result, observe(groups[0], ACTUAL, SPACING))


@pytest.mark.parametrize("mode", ["raise", "warn", "ignore", "call", "print", "log"])
def test_numpy_error_modes_preserved_on_success_and_handled_failure(
    calibrate: Any, mode: Literal["raise", "warn", "ignore", "call", "print", "log"]
) -> None:
    old = np.geterr()
    with np.errstate(all=mode), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        before = np.geterr().copy()
        calibrate(declare(physical_images(ACTUAL)), **arguments())
        raw = np.stack((physical_images(ACTUAL), physical_images(ACTUAL)))
        raw[1, 0, 0, 0, 0] = np.finfo(float).max
        offset = np.zeros(raw.shape)
        offset[1, 0, 0, 0, 0] = -np.finfo(float).max
        assert_code(calibrate, declare(raw), "linear_response_range", offset=offset, response=2)
        assert np.geterr() == before
        assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    assert np.geterr() == old


@pytest.mark.parametrize(
    "failure,code",
    [
        (FloatingPointError("public FFT"), "empirical_response_transform_failure"),
        (OverflowError("public FFT"), "empirical_response_transform_failure"),
        ("warning", "empirical_response_transform_failure"),
        ("nonfinite", "empirical_response_transform_failure"),
        (MemoryError("public FFT"), None),
        (RuntimeError("public FFT"), None),
        (TypeError("public FFT"), None),
        (ValueError("public FFT"), None),
    ],
)
def test_public_fft_failure_boundary_translation_and_propagation(
    calibrate: Any, monkeypatch: pytest.MonkeyPatch, failure: Any, code: str | None
) -> None:
    original = np.fft.fftn
    acquisition = declare(physical_images(ACTUAL))
    before = record_snapshot(acquisition)
    error_mode = np.geterr().copy()

    def injected(*args: Any, **kwargs: Any) -> Any:
        if failure == "warning":
            warnings.warn("public FFT arithmetic", RuntimeWarning, stacklevel=2)
            return original(*args, **kwargs)
        if failure == "nonfinite":
            output = original(*args, **kwargs)
            output[...] = np.nan
            return output
        raise failure

    monkeypatch.setattr(np.fft, "fftn", injected)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        if code is None:
            with pytest.raises(type(failure)) as raised:
                calibrate(acquisition, **arguments())
            assert raised.value is failure
        else:
            assert_code(calibrate, acquisition, code)
        assert not any(issubclass(w.category, RuntimeWarning) for w in caught)
    equal_tree(record_snapshot(acquisition), before)
    assert np.geterr() == error_mode


def test_unrelated_fft_warning_remains_visible(
    calibrate: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = np.fft.fftn

    def warn(*args: Any, **kwargs: Any) -> Any:
        warnings.warn("public unrelated warning", UserWarning, stacklevel=2)
        return original(*args, **kwargs)

    monkeypatch.setattr(np.fft, "fftn", warn)
    with pytest.warns(UserWarning, match="public unrelated warning"):
        calibrate(declare(physical_images(ACTUAL)), **arguments())


def test_integer_conversion_rounding_and_finite_raw_extrema_are_preserved(calibrate: Any) -> None:
    dc = np.array([[[2**64 - 1, 2**53 + 1, 0]]], dtype=np.uint64)
    images = np.repeat(dc[None], len(ACTUAL), axis=0)
    acquisition = declare(images)
    before = acquisition.data.tobytes()
    result = calibrate(acquisition, **arguments(offset=2**53 + 1, response=2**60))
    corrected = converted_correction(images, 2**53 + 1, 2**60)
    assert_observation(result, observe(corrected, ACTUAL, SPACING))
    assert acquisition.data.tobytes() == before
    assert result.components.dc[0, 0, 2] < 0
    assert result.provenance["linear_response"]["offset"]["supplied"] == 2**53 + 1
    assert result.provenance["linear_response"]["offset"]["applied"] == float(2**53 + 1)
    assert result.provenance["source_metadata"]["original_metadata"]["flags"] == [
        "bad-pixel",
        "saturated",
    ]


def test_strided_readonly_full_coefficients_keep_supplied_and_applied_snapshots(
    calibrate: Any,
) -> None:
    images = physical_images(ACTUAL)
    shape = (1, *images.shape)
    backing_offset = np.full((*shape[:-1], shape[-1] * 2), -3, dtype=">i2")
    backing_response = np.full((*shape[:-1], shape[-1] * 2), 2, dtype=">f4")
    offset, response = backing_offset[..., ::2], backing_response[..., ::2]
    offset.flags.writeable = False
    response.flags.writeable = False
    raw = offset + response * images[None]
    result = calibrate(declare(raw), **arguments(offset=offset, response=response))
    assert_observation(
        result, observe(converted_correction(raw[0], offset[0], response[0]), ACTUAL, SPACING)
    )
    for name, source in (("offset", offset), ("response", response)):
        record = result.provenance["linear_response"][name]
        equal_tree(record["supplied"], np.array(source, order="C"))
        equal_tree(record["applied"], np.array(source, dtype=np.float64, order="C"))
        assert record["supplied"].flags.c_contiguous
        assert record["applied"].flags.c_contiguous
        assert not np.shares_memory(record["supplied"], source)
        assert not np.shares_memory(record["applied"], source)


@pytest.mark.parametrize(
    "dtype", ["i1", "u1", ">i2", ">u4", "i8", "u8", "f2", ">f4", ">f8", np.longdouble]
)
def test_actual_phase_widths_and_converted_value_meaning(calibrate: Any, dtype: Any) -> None:
    phases = np.arange(7).astype(dtype)
    dc = np.array([[[11.0, 1.0], [-0.5, 2.0]]])
    c1 = np.array([[[0.5 + 0.25j, 0.1j], [0.25, -0.125j]]])
    images = forward_images(dc, phases=phases, c1=c1, c2=(1 + 0.5j) * c1)
    result = calibrate(declare(images), **arguments(phases_rad=phases))
    assert_observation(result, observe(images, phases, SPACING))
    equal_tree(result.provenance["phases_rad"]["supplied"], phases)
    equal_tree(result.provenance["phases_rad"]["applied"], phases.astype(np.float64))


def test_effective_overrides_and_complete_original_declarations_survive(calibrate: Any) -> None:
    images = physical_images(ACTUAL)
    config = {
        "version": 1,
        "acquisition_kind": "sim_beads",
        "axes": ["orientation", "phase", "z", "y", "x"],
        "intensity_unit": "original unit",
        "sampling_um": {"x": -1},
        "nominal_phases_rad": None,
        "overrides": {
            "intensity_unit": "count",
            "sampling_um": {"x": 3, "y": 2, "z": 1},
            "nominal_phases_rad": [[0.125] * len(ACTUAL)],
            "acquisition_id": "overridden-id",
            "calibration_id": "opaque-id",
        },
    }
    metadata = {"bytes": b"opaque\xff", "nested": [{"unused": float("nan")}], "tuple": (1, None)}
    acquisition = declare_acquisition(images[None], config=config, original_metadata=metadata)
    source_before = record_snapshot(acquisition)
    result = calibrate(acquisition, **arguments())
    assert_observation(result, observe(images, ACTUAL, SPACING))
    equal_tree(
        result.provenance["source_metadata"],
        {k: v for k, v in source_before.items() if k != "data"},
    )
    assert result.provenance["linear_response"]["input_unit"] == "count"
    assert result.provenance["source_metadata"]["original_config"]["sampling_um"] == {"x": -1}
    assert result.provenance["source_metadata"]["sampling_um"] == {"x": 3.0, "y": 2.0, "z": 1.0}
    preserved = deepcopy(result.provenance)
    acquisition.original_metadata["nested"].append("caller change")
    assert acquisition.nominal_phases_rad is not None
    acquisition.nominal_phases_rad[0, 0] = 99
    acquisition.data.flat[0] = -1
    config["overrides"]["sampling_um"]["x"] = 9
    metadata["nested"].append("source change")
    equal_tree(result.provenance, preserved)


def test_subnormal_corrected_dc_is_not_clipped_or_subject_to_epsilon_floor(calibrate: Any) -> None:
    tiny = np.nextafter(0.0, 1.0)
    dc = np.array([[[1024 * tiny, -16 * tiny, 64 * tiny]]])
    images = np.repeat(dc[None], len(ACTUAL), axis=0)
    result = calibrate(declare(images), **arguments())
    assert_observation(result, observe(images, ACTUAL, SPACING))
    assert result.components.dc[0, 0, 1] < 0


class ArraySubclass(np.ndarray[Any, Any]):
    """Unsupported subclass for plain-array public argument grammar."""


@pytest.mark.parametrize("name", ["offset", "response"])
def test_coefficient_ndarray_subclass_rejected(calibrate: Any, name: str) -> None:
    acquisition = declare(physical_images(ACTUAL))
    coefficient = np.ones(acquisition.data.shape).view(ArraySubclass)
    assert_code(calibrate, acquisition, f"invalid_linear_response_{name}", **{name: coefficient})


def test_actual_phase_ndarray_subclass_rejected(calibrate: Any) -> None:
    assert_code(
        calibrate,
        declare(physical_images(ACTUAL)),
        "invalid_volume_phase_angles",
        phases_rad=ACTUAL.view(ArraySubclass),
    )


def test_valid_pixel_changes_preserving_declared_record_invariants_supported(
    calibrate: Any,
) -> None:
    acquisition = declare(physical_images(ACTUAL), nominal=True)
    replacement = physical_images(ACTUAL, bead=(0, 1, 1), brightness=64)
    acquisition.data[0] = replacement
    result = calibrate(acquisition, **arguments(offset=-0.0))
    assert_observation(result, observe(converted_correction(replacement, -0.0, 1), ACTUAL, SPACING))
    snapshot = result.provenance["linear_response"]["offset"]
    assert type(snapshot["supplied"]) is float
    assert type(snapshot["applied"]) is float
    assert np.signbit(snapshot["supplied"])
    assert np.signbit(snapshot["applied"])


def test_joint_phase_exposure_permutation_preserves_fit(calibrate: Any) -> None:
    images = physical_images(ACTUAL)
    images[:, 0, 1, 2] += np.arange(len(ACTUAL)) ** 2 / 32
    permutation = np.array([5, 1, 6, 0, 3, 2, 4])
    permuted_images, permuted_phases = images[permutation], ACTUAL[permutation]
    base = calibrate(declare(images), **arguments())
    permuted = calibrate(declare(permuted_images), **arguments(phases_rad=permuted_phases))
    base_oracle = observe(images, ACTUAL, SPACING)
    permuted_oracle = observe(permuted_images, permuted_phases, SPACING)
    assert_observation(base, base_oracle)
    assert_observation(permuted, permuted_oracle)
    assert np.all(
        np.abs(base.response.values - permuted.response.values)
        <= (base_oracle.budgets + permuted_oracle.budgets)
    )
