"""LINRESP-01 blind A tests: public inputs, independent numerical expectations."""

from __future__ import annotations

import copy
import importlib
import math
import warnings
from typing import Any, Literal

import numpy as np
import pytest

from linear_response_fixture import (
    SOURCE_FIELDS,
    acquisition,
    decimal_phase_coordinates,
    mutable_arrays,
    phase_design,
    public_api,
    rounded_signal,
    same_value,
    source_snapshot,
)

Array = np.ndarray[Any, Any]
ErrorMode = Literal["raise", "warn", "call", "print", "log", "ignore"]
MAX = float.fromhex("0x1.fffffffffffffp+1023")
TINY = float.fromhex("0x0.0000000000001p-1022")


@pytest.fixture
def api() -> Any:
    return public_api()


def correction(api: Any, record: Any, offset: Any = 0, response: Any = 1) -> Any:
    return api.correct_linear_response(
        record, offset=offset, response=response, output_unit="electron"
    )


def rejected(api: Any, record: Any, code: str, **kwargs: Any) -> None:
    arguments = {"offset": 0, "response": 1, "output_unit": "electron"}
    arguments.update(kwargs)
    before = source_snapshot(record) if isinstance(record, api.RawAcquisition) else None
    pixels = record.data.tobytes() if before is not None else None
    array_bytes = {
        key: value.tobytes() for key, value in arguments.items() if isinstance(value, np.ndarray)
    }
    with warnings.catch_warnings(record=True) as observed:
        warnings.simplefilter("always")
        with pytest.raises(api.SimreconError) as caught:
            api.correct_linear_response(record, **arguments)
    assert caught.value.code == code
    assert not [warning for warning in observed if issubclass(warning.category, RuntimeWarning)]
    if before is not None:
        assert record.data.tobytes() == pixels
        same_value(source_snapshot(record), before)
    for key, value in array_bytes.items():
        assert arguments[key].tobytes() == value


def assert_owned_native(array: Any, shape: tuple[int, ...]) -> None:
    assert type(array) is np.ndarray
    assert array.shape == shape
    assert array.dtype == np.dtype(np.float64)
    assert array.dtype.isnative
    assert array.flags.c_contiguous
    assert array.flags.owndata
    assert array.flags.writeable


def test_scalar_count_electron_model_and_public_result(api: Any) -> None:
    record = acquisition(np.array([[110, 6, 10], [-2, 12, 14]], dtype=np.int16))
    result = correction(api, record, offset=10, response=2)
    assert isinstance(result, api.LinearResponseCorrection)
    assert_owned_native(result.data, (2, 3))
    np.testing.assert_array_equal(result.data, [[50, -2, 0], [-6, 1, 2]])
    assert result.axes == ("y", "x")
    assert result.input_unit == "count"
    assert result.output_unit == "electron"
    assert result.data[0, 0] != 110 / 2 - 10  # Wrong-order control gives 45.
    np.testing.assert_array_equal(10 + 2 * result.data, record.data)


@pytest.mark.parametrize(
    "offset_map,response_map", [(False, False), (True, False), (False, True), (True, True)]
)
def test_four_scalar_map_combinations(api: Any, offset_map: bool, response_map: bool) -> None:
    signal = np.array([[-5, 0, 7], [11, -13, 17]], dtype=np.int64)
    offset = np.array([[3, -4, 5], [-6, 7, -8]], dtype=np.int16) if offset_map else -4
    response = np.array([[1, 2, 4], [8, 2, 1]], dtype=np.uint16) if response_map else 2
    raw = offset + response * signal
    result = correction(api, acquisition(raw), offset, response)
    np.testing.assert_array_equal(result.data, signal)


@pytest.mark.parametrize(
    "kind,axes,shape",
    [
        ("detection_psf", ("y", "x"), (2, 3)),
        ("detection_psf", ("z", "y", "x"), (1, 2, 3)),
        ("detection_psf", ("channel", "time", "z", "y", "x"), (2, 3, 1, 2, 3)),
        ("specimen_sim", ("orientation", "phase", "y", "x"), (1, 2, 2, 3)),
        ("sim_beads", ("phase", "orientation", "z", "y", "x"), (3, 2, 1, 2, 3)),
        (
            "specimen_sim",
            ("z", "phase", "time", "orientation", "channel", "y", "x"),
            (2, 3, 2, 2, 3, 2, 4),
        ),
    ],
)
def test_all_profiles_and_canonical_full_maps(
    api: Any, kind: str, axes: tuple[str, ...], shape: tuple[int, ...]
) -> None:
    weights = {
        "time": 4096,
        "channel": 1024,
        "orientation": 256,
        "phase": 64,
        "z": 16,
        "y": 4,
        "x": 1,
    }
    source = np.empty(shape, dtype=np.int64)
    for index in np.ndindex(shape):
        source[index] = (
            sum(weights[name] * coordinate for name, coordinate in zip(axes, index, strict=True))
            - 5
        )
    record = acquisition(source, axes=axes, kind=kind)
    canonical = tuple(name for name in weights if name in axes)
    canonical_shape = tuple(shape[axes.index(name)] for name in canonical)
    expected = np.empty(canonical_shape, dtype=np.float64)
    off = np.empty(canonical_shape, dtype=np.int32)
    gain = np.empty(canonical_shape, dtype=np.float64)
    for index in np.ndindex(canonical_shape):
        named = dict(zip(canonical, index, strict=True))
        raw = sum(weights[name] * named[name] for name in canonical) - 5
        off[index] = 2 * named["y"] - named["x"]
        gain[index] = 2 ** (named.get("orientation", 0) + named.get("z", 0))
        expected[index] = (raw - int(off[index])) / float(gain[index])
    result = correction(api, record, off, gain)
    assert result.axes == canonical
    assert_owned_native(result.data, canonical_shape)
    np.testing.assert_array_equal(result.data, expected)
    same_value(result.source_metadata, source_snapshot(record))


@pytest.mark.parametrize(
    "dtype",
    ["i1", "u1", "<i2", ">i2", "<u4", ">u4", "<i8", ">u8", "<f2", ">f4", ">f8", np.longdouble],
)
@pytest.mark.parametrize("storage", ["c", "fortran", "strided-readonly"])
def test_supported_raw_widths_byteorders_and_storage(api: Any, dtype: Any, storage: str) -> None:
    base = np.array([[1, 2, 3], [4, 5, 6]], dtype=dtype)
    if storage == "fortran":
        base = np.asfortranarray(base)
    elif storage == "strided-readonly":
        wide = np.zeros((2, 6), dtype=dtype)
        wide[:, ::2] = base
        base = wide[:, ::2]
        base.setflags(write=False)
    record = acquisition(base)
    # The public factory canonicalizes layout. Read-only flags remain a permitted
    # correction input; do not replace R1 data with a non-owned/corrupted buffer.
    if storage == "strided-readonly":
        record.data.setflags(write=False)
    before = record.data.tobytes()
    result = correction(api, record)
    assert_owned_native(result.data, (2, 3))
    np.testing.assert_array_equal(result.data, [[1, 2, 3], [4, 5, 6]])
    assert record.data.tobytes() == before
    assert not np.shares_memory(result.data, record.data)
    assert not np.shares_memory(result.data, base)


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize("dtype", ["i1", "u1", ">i2", ">u8", "f2", ">f4", ">f8", np.longdouble])
@pytest.mark.parametrize("storage", ["fortran", "strided-readonly"])
def test_coefficient_storage_supplied_and_applied(
    api: Any, field: str, dtype: Any, storage: str
) -> None:
    values = np.array([[1, 2, 4], [8, 2, 1]], dtype=dtype)
    if storage == "fortran":
        supplied = np.asfortranarray(values)
    else:
        wide = np.zeros((2, 6), dtype=dtype)
        wide[:, ::2] = values
        supplied = wide[:, ::2]
        supplied.setflags(write=False)
    original_bytes = supplied.tobytes()
    record = acquisition(np.array([[12, 14, 16], [18, 20, 22]], dtype=np.int16))
    kwargs = {"offset": 0, "response": 1, field: supplied}
    result = correction(api, record, **kwargs)
    np.testing.assert_array_equal(
        result.data, rounded_signal(record.data, kwargs["offset"], kwargs["response"])
    )
    entry = result.provenance[field]
    assert entry.keys() == {"source", "supplied", "applied"}
    assert entry["source"] == "supplied"
    same_value(entry["supplied"], values)
    assert entry["supplied"].flags.owndata and entry["supplied"].flags.c_contiguous
    assert_owned_native(entry["applied"], values.shape)
    np.testing.assert_array_equal(entry["applied"], [[1, 2, 4], [8, 2, 1]])
    assert supplied.tobytes() == original_bytes
    for array in (entry["supplied"], entry["applied"], result.data):
        assert not np.shares_memory(array, supplied)


@pytest.mark.parametrize(
    "field,value",
    [
        ("offset", 2**53 + 1),
        ("response", 2**53 + 1),
        ("offset", -0.0),
        ("response", 2.0),
        ("offset", -(2**100)),
        ("response", 2**100),
    ],
)
def test_scalar_supplied_type_and_binary64_applied(api: Any, field: str, value: Any) -> None:
    record = acquisition(np.array([[3.0, 8.0]]))
    kwargs = {"offset": 0, "response": 1, field: value}
    result = correction(api, record, **kwargs)
    entry = result.provenance[field]
    assert entry.keys() == {"source", "supplied", "applied"}
    assert entry["source"] == "supplied"
    same_value(entry["supplied"], value)
    same_value(entry["applied"], float(value))
    np.testing.assert_array_equal(
        result.data, rounded_signal(record.data, kwargs["offset"], kwargs["response"])
    )


def test_explicit_identity_integer_rounding_and_sequential_rounding(api: Any) -> None:
    integers = np.array([[2**53 + 1, 2**53 + 3, -(2**53 + 1)]], dtype=np.int64)
    result = correction(api, acquisition(integers))
    np.testing.assert_array_equal(result.data, [[float(2**53), float(2**53 + 4), -float(2**53)]])
    # 2**53 - (-1) rounds back to 2**53 before division; fused exact result differs.
    record = acquisition(np.array([[float(2**53)]]))
    result = correction(api, record, offset=-1, response=3)
    expected = rounded_signal(record.data, -1, 3)
    np.testing.assert_array_equal(result.data, expected)
    from fractions import Fraction

    fused = float(Fraction(2**53 + 1, 3))
    assert result.data[0, 0] != fused


def test_nonexact_rounding_observer_distinguishes_wrong_arithmetic(api: Any) -> None:
    record = acquisition(np.array([[0.1, -7.3, 1.0], [1e100, -1e-100, math.pi]]))
    offset = np.array([[0.03, 0.2, -0.1], [1e99, 1e-101, -math.e]])
    response = np.array([[0.7, 3.1, 0.3], [11.0, 1.3, 0.9]])
    result = correction(api, record, offset, response)
    np.testing.assert_array_equal(result.data, rounded_signal(record.data, offset, response))


@pytest.mark.parametrize("value", [None, 3, [], {}, np.array([[1.0]])])
def test_nonrecord_rejection(api: Any, value: Any) -> None:
    rejected(api, value, "invalid_linear_response_acquisition")


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nonfinite_raw_is_not_rejected_by_r1_but_is_by_correction(api: Any, value: float) -> None:
    record = acquisition(np.array([[1.0, value]]))
    assert not np.isfinite(record.data[0, 1])
    rejected(api, record, "invalid_linear_response_data")


class CoefficientSubclass(np.ndarray[Any, Any]):
    """A forbidden subclass supplied only as a public invalid argument."""


def unsupported_coefficients() -> list[Any]:
    return [
        None,
        True,
        [1, 2],
        (1, 2),
        "1",
        1 + 0j,
        np.int64(1),
        np.float64(1),
        np.float32(1),
        np.array([[1, 1]], dtype=np.int16).view(CoefficientSubclass),
        np.ma.array([[1, 1]], mask=False),
        np.array([[True, False]]),
        np.array([[1 + 0j, 1 + 0j]]),
        np.array([[1, 1]], dtype=object),
        np.array([["1", "1"]]),
        np.array([[b"1", b"1"]]),
        np.zeros((1, 2), dtype=[("v", "f8")]),
        np.zeros((1, 2), dtype="datetime64[ns]"),
        np.zeros((1, 2), dtype="timedelta64[ns]"),
    ]


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize("index", range(19))
def test_unsupported_coefficient_forms_and_dtype_families(api: Any, field: str, index: int) -> None:
    rejected(
        api,
        acquisition(np.array([[1, 2]])),
        f"invalid_linear_response_{field}",
        **{field: unsupported_coefficients()[index]},
    )


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize(
    "shape", [(), (3,), (2, 3), (1, 1, 2, 3), (2, 1, 2, 3), (3, 2, 2, 3), (2, 3, 3, 2)]
)
def test_no_array_broadcast_or_coordinate_inference(
    api: Any, field: str, shape: tuple[int, ...]
) -> None:
    record = acquisition(
        np.ones((2, 3, 2, 3)), axes=("orientation", "phase", "y", "x"), kind="specimen_sim"
    )
    rejected(api, record, "invalid_linear_response_shape", **{field: np.ones(shape)})


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize(
    "value",
    [math.nan, math.inf, -math.inf, 10**400],
    ids=["nan", "positive-infinity", "negative-infinity", "huge-int"],
)
def test_coefficient_nonfinite_and_scalar_conversion_overflow(
    api: Any, field: str, value: Any
) -> None:
    rejected(
        api,
        acquisition(np.array([[1.0, 2.0]])),
        f"invalid_linear_response_{field}",
        **{field: value},
    )


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_array_nonfinite_coefficients_reject_entire_call(
    api: Any, field: str, value: float
) -> None:
    rejected(
        api,
        acquisition(np.array([[1.0, 2.0]])),
        f"invalid_linear_response_{field}",
        **{field: np.array([[1.0, value]])},
    )


@pytest.mark.parametrize("value", [-1, 0, -0.0, -TINY])
@pytest.mark.parametrize("is_array", [False, True])
def test_response_requires_strict_normalized_positivity(
    api: Any, value: Any, is_array: bool
) -> None:
    supplied = np.array([[1.0, value]]) if is_array else value
    rejected(
        api,
        acquisition(np.array([[1.0, 2.0]])),
        "invalid_linear_response_response",
        response=supplied,
    )


@pytest.mark.parametrize("offset", [-7, 0, -0.0, 11])
def test_finite_signed_offsets_and_signed_output(api: Any, offset: Any) -> None:
    record = acquisition(np.array([[-8.0, 0.0, 12.0]]))
    np.testing.assert_array_equal(
        correction(api, record, offset, 2).data,
        [[(-8 - offset) / 2, -offset / 2, (12 - offset) / 2]],
    )


def test_missing_input_label(api: Any) -> None:
    rejected(api, acquisition(np.array([[1.0]]), unit=None), "invalid_linear_response_unit")


@pytest.mark.parametrize("output_unit", [None, "", True, 5, [], b"electron"])
def test_invalid_output_labels(api: Any, output_unit: Any) -> None:
    rejected(
        api, acquisition(np.array([[1.0]])), "invalid_linear_response_unit", output_unit=output_unit
    )


@pytest.mark.parametrize(
    "input_unit,output_unit",
    [("count", "count"), ("count", "electron"), ("  ", "\t "), (" ADU / s ", " arbitrary label ")],
)
def test_opaque_units_preserved_without_conversion(
    api: Any, input_unit: str, output_unit: str
) -> None:
    record = acquisition(np.array([[110]]), unit=input_unit)
    result = api.correct_linear_response(record, offset=10, response=2, output_unit=output_unit)
    assert result.input_unit == input_unit and result.output_unit == output_unit
    assert result.provenance["input_unit"] == input_unit
    assert result.provenance["output_unit"] == output_unit
    np.testing.assert_array_equal(result.data, [[50]])


# Wider-native evidence is registered only where the required storage exists.
# Absence is a reported capability limitation, not a skip or a passing test.
if np.finfo(np.longdouble).maxexp > np.finfo(np.float64).maxexp:

    @pytest.mark.parametrize("which", ["raw", "offset", "response"])
    def test_wider_float_conversion_to_infinity(api: Any, which: str) -> None:
        wide = np.array([[np.longdouble(MAX) * np.longdouble(2)]], dtype=np.longdouble)
        record = acquisition(wide if which == "raw" else np.array([[1.0]]))
        code = (
            "invalid_linear_response_data" if which == "raw" else f"invalid_linear_response_{which}"
        )
        kwargs = {} if which == "raw" else {which: wide}
        rejected(api, record, code, **kwargs)


if np.finfo(np.longdouble).nmant > np.finfo(np.float64).nmant:

    def test_wider_float_precision_normalized_before_arithmetic(api: Any) -> None:
        raw = np.array([[np.longdouble(2**53) + np.longdouble(1)]])
        result = correction(api, acquisition(raw), offset=2**53, response=1)
        np.testing.assert_array_equal(result.data, [[0.0]])


# tiny/4 is exactly 2**-1076; include wider native subnormal ranges as well.
if np.finfo(np.longdouble).minexp - np.finfo(np.longdouble).nmant <= -1076:

    def test_wider_float_conversion_underflow(api: Any) -> None:
        tiny = np.array([[np.longdouble(TINY) / np.longdouble(4)]])
        np.testing.assert_array_equal(correction(api, acquisition(tiny)).data, [[0.0]])
        record = acquisition(np.array([[1.0]]))
        np.testing.assert_array_equal(correction(api, record, offset=tiny).data, [[1.0]])
        rejected(api, record, "invalid_linear_response_response", response=tiny)


@pytest.mark.parametrize("negative", [False, True])
def test_subtraction_overflow_even_when_exact_quotient_would_fit(api: Any, negative: bool) -> None:
    value = -MAX if negative else MAX
    record = acquisition(np.array([[0.0, value]]))
    rejected(api, record, "linear_response_range", offset=-value, response=2)


@pytest.mark.parametrize("value", [1.0, -1.0])
def test_quotient_overflow_with_finite_numerator(api: Any, value: float) -> None:
    rejected(api, acquisition(np.array([[0.0, value]])), "linear_response_range", response=TINY)


def test_subnormal_response_subnormal_result_and_negative_underflow(api: Any) -> None:
    record = acquisition(np.array([[TINY, -TINY, 0.0, -0.0]]))
    np.testing.assert_array_equal(
        correction(api, record, response=TINY).data, [[1.0, -1.0, 0.0, -0.0]]
    )
    result = correction(api, record, response=2)
    np.testing.assert_array_equal(result.data, [[0.0, -0.0, 0.0, -0.0]])
    np.testing.assert_array_equal(np.signbit(result.data), [[False, True, False, True]])
    np.testing.assert_array_equal(
        correction(api, acquisition(np.array([[2 * TINY, -2 * TINY]])), response=2).data,
        [[TINY, -TINY]],
    )
    offsets = np.array([[-0.0, 0.0]], dtype=">f8")
    result = correction(api, acquisition(np.array([[1.0, -1.0]])), offset=offsets)
    np.testing.assert_array_equal(
        np.signbit(result.provenance["offset"]["supplied"]), [[True, False]]
    )
    np.testing.assert_array_equal(
        np.signbit(result.provenance["offset"]["applied"]), [[True, False]]
    )


@pytest.mark.parametrize("mode", ["raise", "warn", "call", "print", "log", "ignore"])
@pytest.mark.parametrize(
    "case",
    [
        "success-underflow",
        "range",
        "quotient-range",
        "invalid-data",
        "invalid-offset",
        "invalid-response",
    ],
)
def test_numpy_modes_restored_and_no_arithmetic_diagnostics(
    api: Any, mode: ErrorMode, case: str, capsys: Any
) -> None:
    events: list[Any] = []

    class Observer:
        def __call__(self, *args: Any) -> None:
            events.append(args)

        def write(self, message: str) -> None:
            events.append(message)

    observer = Observer()
    old_callback = np.geterrcall()
    np.seterrcall(observer)
    try:
        with np.errstate(divide=mode, over=mode, under=mode, invalid=mode):
            before = np.geterr().copy()
            with warnings.catch_warnings(record=True) as observed:
                warnings.simplefilter("always")
                if case == "success-underflow":
                    result = correction(api, acquisition(np.array([[-TINY]])), response=2)
                    assert result.data[0, 0] == 0 and np.signbit(result.data[0, 0])
                elif case == "range":
                    rejected(
                        api, acquisition(np.array([[MAX]])), "linear_response_range", offset=-MAX
                    )
                elif case == "quotient-range":
                    rejected(
                        api, acquisition(np.array([[1.0]])), "linear_response_range", response=TINY
                    )
                elif case == "invalid-data":
                    rejected(
                        api, acquisition(np.array([[math.inf]])), "invalid_linear_response_data"
                    )
                elif case == "invalid-offset":
                    rejected(
                        api,
                        acquisition(np.array([[1.0]])),
                        "invalid_linear_response_offset",
                        offset=10**400,
                    )
                else:
                    rejected(
                        api,
                        acquisition(np.array([[1.0]])),
                        "invalid_linear_response_response",
                        response=0,
                    )
            assert np.geterr() == before
            assert np.geterrcall() is observer
            assert not [w for w in observed if issubclass(w.category, RuntimeWarning)]
            assert not events
            captured = capsys.readouterr()
            assert not captured.out and not captured.err
    finally:
        np.seterrcall(old_callback)


def rich_record() -> Any:
    source = np.arange(48, dtype=">i2").reshape((2, 3, 2, 2, 2))
    commands = [
        [
            [100 * channel + 10 * orientation + phase for phase in range(2)]
            for orientation in range(3)
        ]
        for channel in range(2)
    ]
    # Command tensor follows channel/orientation/phase; z is a spatial axis.
    config = {
        "sampling_um": {"x": 0.1, "y": 0.2},
        "wavelengths_nm": {"0": 488, "1": 640},
        "nominal_phases_rad": commands,
        "acquisition_id": "acq-opaque",
        "calibration_id": "cal-opaque",
        "overrides": {"intensity_unit": " count ", "sampling_um": {"x": 0.4, "y": None}},
    }
    return acquisition(
        source,
        axes=("channel", "orientation", "phase", "y", "x"),
        kind="sim_beads",
        config_extra=config,
        metadata={
            "header": b"\x00\xffopaque",
            "nested": [1, (True, None, b"x"), {"nan": math.nan, "inf": math.inf}],
            "flags": {"saturated": True, "bad_pixel": [0, 1]},
        },
    )


def test_all_source_metadata_provenance_schema_and_independence(api: Any) -> None:
    record = rich_record()
    original = source_snapshot(record)
    pixels = record.data.tobytes()
    offset = np.full(record.data.shape, -2, dtype=">i2")
    response = np.full(record.data.shape, 2, dtype=">f4")
    result = correction(api, record, offset, response)
    another = correction(api, record, offset, response)
    assert type(result.source_metadata) is dict
    assert result.source_metadata.keys() == set(SOURCE_FIELDS)
    assert "data" not in result.source_metadata
    same_value(result.source_metadata, original)
    assert result.provenance.keys() == {
        "model",
        "equation",
        "input_unit",
        "output_unit",
        "offset",
        "response",
    }
    assert result.provenance["model"] == "linear_response_v1"
    assert result.provenance["equation"] == "raw=offset+response*signal"
    assert result.provenance["input_unit"] == " count "
    assert result.provenance["output_unit"] == "electron"
    for name, supplied in (("offset", offset), ("response", response)):
        entry = result.provenance[name]
        assert entry.keys() == {"source", "supplied", "applied"}
        assert entry["source"] == "supplied"
        same_value(entry["supplied"], supplied)
        assert_owned_native(entry["applied"], record.data.shape)
    assert not np.shares_memory(result.data, another.data)
    caller_arrays = [
        record.data,
        offset,
        response,
        *mutable_arrays(original),
        *mutable_arrays(source_snapshot(record)),
    ]
    # Compare directly to real caller nominal-command storage as well as the snapshots.
    caller_arrays += mutable_arrays({name: getattr(record, name) for name in SOURCE_FIELDS})
    returned_arrays = [
        result.data,
        *mutable_arrays(result.source_metadata),
        *mutable_arrays(result.provenance),
    ]
    for array in returned_arrays:
        assert all(not np.shares_memory(array, caller) for caller in caller_arrays)
        assert all(
            not np.shares_memory(array, other)
            for other in [
                another.data,
                *mutable_arrays(another.source_metadata),
                *mutable_arrays(another.provenance),
            ]
        )
    result.data.fill(-999)
    result.source_metadata["sampling_um"]["x"] = 999
    result.source_metadata["original_metadata"]["nested"][2]["nan"] = 999
    result.source_metadata["original_config"]["overrides"]["sampling_um"]["x"] = 999
    result.source_metadata["provenance"][0]["new"] = "changed"
    result.source_metadata["nominal_phases_rad"].fill(999)
    result.provenance["offset"]["supplied"].fill(999)
    result.provenance["response"]["applied"].fill(999)
    assert record.data.tobytes() == pixels
    same_value(source_snapshot(record), original)
    same_value(another.source_metadata, original)
    assert np.all(offset == -2) and np.all(response == 2)
    frozen_result = copy.deepcopy(another.source_metadata)
    frozen_provenance = copy.deepcopy(another.provenance)
    frozen_data = another.data.copy()
    record.data.fill(99)
    record.original_metadata["nested"].append("caller changed")
    record.original_config["overrides"]["sampling_um"]["x"] = 88
    record.nominal_phases_rad.fill(-77)
    offset.fill(66)
    response.fill(55)
    same_value(another.source_metadata, frozen_result)
    same_value(another.provenance, frozen_provenance)
    np.testing.assert_array_equal(another.data, frozen_data)


@pytest.mark.parametrize("failure", ["invalid-response", "quotient-range"])
def test_rich_metadata_and_maps_preserved_on_rejection(api: Any, failure: str) -> None:
    record = rich_record()
    offset = np.full(record.data.shape, -2.0, dtype=">f8")
    response = np.full(record.data.shape, TINY if failure == "quotient-range" else 2.0)
    if failure == "invalid-response":
        response.flat[-1] = 0.0
    code = (
        "invalid_linear_response_response"
        if failure == "invalid-response"
        else "linear_response_range"
    )
    rejected(api, record, code, offset=offset, response=response)


def test_dtype_extrema_and_opaque_flags_do_not_trigger_saturation_repair(api: Any) -> None:
    record = acquisition(
        np.array([[0, 255]], dtype=np.uint8),
        metadata={"saturated": True, "bad_pixels": [1], "exposure_ms": 200},
    )
    result = correction(api, record, offset=10, response=1)
    np.testing.assert_array_equal(result.data, [[-10, 245]])
    same_value(result.source_metadata["original_metadata"], record.original_metadata)


@pytest.mark.parametrize(
    "variant", ["offset", "response", "output_unit", "all", "unknown", "positional"]
)
def test_python_binding_errors(api: Any, variant: str) -> None:
    record = acquisition(np.array([[1.0]]))
    arguments: dict[str, Any] = {"offset": 0, "response": 1, "output_unit": "count"}
    if variant in arguments:
        del arguments[variant]
    elif variant == "all":
        arguments = {}
    elif variant == "unknown":
        arguments["exposure"] = 1
    with pytest.raises(TypeError):
        if variant == "positional":
            api.correct_linear_response(record, 0, 1, "count")
        else:
            api.correct_linear_response(record, **arguments)


def composition_inputs() -> tuple[Any, Array, Array, Array, Array, Array, Array]:
    phases = np.array([0.1, 0.8, 1.7, 2.5, 3.6, 4.4, 5.8])
    design = phase_design(phases)
    assert np.linalg.cond(design) < 10  # Confirms the contract's accuracy regime.
    shape = (2, 7, 2, 3, 4)  # orientation, phase, z, y, x
    signal = np.empty(shape)
    off = np.empty(shape)
    gain = np.empty(shape)
    intended = np.empty((2, 5, 2, 3, 4))
    for orientation, z, y, x in np.ndindex((2, 2, 3, 4)):
        coordinates = (
            20 + 8 * orientation + 4 * z + 2 * y + x,
            1 + x / 4,
            -2 - y / 4,
            3 + z / 2,
            4 + orientation / 2,
        )
        intended[orientation, :, z, y, x] = coordinates
        dc, a, b, c, d = coordinates
        for p in range(7):
            row = design[p]
            signal[orientation, p, z, y, x] = (
                dc + 2 * a * row[1] - 2 * b * row[2] + 2 * c * row[3] - 2 * d * row[4]
            )
            off[orientation, p, z, y, x] = 1 + 2 * orientation + 4 * p + 8 * z + y + x
            gain[orientation, p, z, y, x] = 2 ** ((orientation + p + z + y + x) % 3)
    raw = off + gain * signal
    # Deliberately noncanonical source z/orientation/phase/y/x layout.
    source = np.empty((2, 2, 7, 3, 4))
    for z, orientation, p, y, x in np.ndindex(source.shape):
        source[z, orientation, p, y, x] = raw[orientation, p, z, y, x]
    record = acquisition(
        source,
        axes=("z", "orientation", "phase", "y", "x"),
        kind="specimen_sim",
        config_extra={"nominal_phases_rad": [[0.0] * 7 for _ in range(2)]},
    )
    independent = rounded_signal(raw, off, gain)
    return record, off, gain, independent, design, phases, intended


def assert_phase_fit(
    module: Any, data: Array, independent: Array, design: Array, phases: Array, intended: Array
) -> None:
    for orientation in range(2):
        # Explicit true phases chosen by the caller, not the all-zero commands.
        components = module.separate_volume_phases(data[orientation], phases_rad=phases)
        expected = decimal_phase_coordinates(design, independent[orientation])
        actual = np.stack(
            (
                components.dc,
                components.c1.real,
                components.c1.imag,
                components.c2.real,
                components.c2.imag,
            )
        )
        budget = (
            8192 * phases.size * 2**-52 * np.max(np.abs(independent[orientation]), axis=0)
            + 8 * TINY
        )
        assert np.all(np.abs(actual - expected) <= budget)
        # Stored forward-rounding error bounds the difference from selected coefficients.
        k = design * np.array([1, 2, -2, 2, -2])
        with np.errstate(all="ignore"):
            smallest = float(np.linalg.svd(k, compute_uv=False)[-1])
        # Decimal computes the residual against exact represented K, not a rounded fit.
        from decimal import Decimal, localcontext

        with localcontext() as context:
            context.prec = 100
            for index in np.ndindex((2, 3, 4)):
                selected = intended[(orientation, slice(None), *index)]
                residual_max = Decimal(0)
                for p in range(7):
                    exact = sum(
                        (
                            Decimal.from_float(float(k[p, j]))
                            * Decimal.from_float(float(selected[j]))
                            for j in range(5)
                        ),
                        Decimal(0),
                    )
                    residual_max = max(
                        residual_max,
                        abs(
                            Decimal.from_float(float(independent[(orientation, p, *index)])) - exact
                        ),
                    )
                # Factor 2 allows computed singular-value and final observer rounding.
                forward_budget = 2 * math.sqrt(7) * float(residual_max) / smallest + 2**-51 * float(
                    np.max(np.abs(selected))
                )
                assert np.all(np.abs(expected[(slice(None), *index)] - selected) <= forward_budget)


def test_asymmetric_full_map_then_actual_known_phase_separation(api: Any) -> None:
    record, off, gain, independent, design, phases, intended = composition_inputs()
    result = correction(api, record, off, gain)
    np.testing.assert_array_equal(result.data, independent)
    same_value(result.source_metadata["nominal_phases_rad"], np.zeros((2, 7)))
    assert_phase_fit(api, result.data, independent, design, phases, intended)


def test_public_prerequisites_and_composition_oracle() -> None:
    """Initially passing fixture evidence; does not stand in for L24 correction."""
    module = importlib.import_module("simrecon")
    record = rich_record()
    assert record.axes == ("channel", "orientation", "phase", "y", "x")
    assert record.intensity_unit == " count "
    assert record.nominal_phases_rad.shape == (2, 3, 2)
    record, off, gain, independent, design, phases, intended = composition_inputs()
    assert record.axes == ("orientation", "phase", "z", "y", "x")
    np.testing.assert_array_equal(independent, rounded_signal(record.data, off, gain))
    assert_phase_fit(module, independent, independent, design, phases, intended)


def test_array_coefficient_precision_is_normalized_once(api: Any) -> None:
    record = acquisition(np.array([[2**53 + 1, 2**53 + 3]], dtype=np.int64))
    offset = np.array([[2**53, 2**53 + 1]], dtype=">i8")
    response = np.array([[2**53 + 1, 2**53 + 3]], dtype=">u8")
    result = correction(api, record, offset, response)
    np.testing.assert_array_equal(result.data, [[0.0, 4.0 / float(2**53 + 4)]])
    same_value(result.provenance["offset"]["supplied"], offset)
    same_value(result.provenance["response"]["supplied"], response)
    np.testing.assert_array_equal(
        result.provenance["offset"]["applied"], [[float(2**53), float(2**53)]]
    )
    np.testing.assert_array_equal(
        result.provenance["response"]["applied"], [[float(2**53), float(2**53 + 4)]]
    )


def test_safe_finite_extremes_and_uint64_max_are_accepted(api: Any) -> None:
    record = acquisition(np.array([[MAX, -MAX, 1.0]]))
    result = correction(api, record, response=MAX)
    np.testing.assert_array_equal(result.data, rounded_signal(record.data, 0, MAX))
    np.testing.assert_array_equal(
        correction(api, acquisition(np.array([[MAX]])), offset=MAX).data, [[0.0]]
    )
    integers = np.array([[2**64 - 1]], dtype=">u8")
    np.testing.assert_array_equal(correction(api, acquisition(integers)).data, [[float(2**64)]])


def test_independent_arithmetic_observer_self_check() -> None:
    np.testing.assert_array_equal(rounded_signal(np.array([[110, -2]]), 10, 2), [[50, -6]])
    np.testing.assert_array_equal(
        rounded_signal(np.array([[float(2**53)]]), -1, 3), [[float(2**53) / 3]]
    )


def test_decimal_observer_self_check() -> None:
    # Explicit integer rows make this independent observer check exact.
    design = np.array(
        [[1, 1, 0, 1, 0], [1, 0, 1, -1, 0], [1, -1, 0, 1, 0], [1, 0, -1, -1, 0], [1, 0, 0, 0, 1]],
        dtype=np.float64,
    )
    coordinates = np.array([10, 2, -1, 3, 4], dtype=np.float64)
    pixels = (design * np.array([1, 2, -2, 2, -2])) @ coordinates
    result = decimal_phase_coordinates(design, pixels.reshape((5, 1, 1, 1)))
    np.testing.assert_array_equal(result[:, 0, 0, 0], coordinates)
