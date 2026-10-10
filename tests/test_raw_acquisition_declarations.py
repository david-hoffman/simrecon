"""Blind A02 public-contract tests; no implementation-derived expectations."""

import builtins
import copy
import itertools
import math
import os
import struct
import warnings
from collections import UserDict
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import simrecon
from simrecon import SimreconError, harmonize, inspect, read

CANONICAL = ("time", "channel", "orientation", "phase", "z", "y", "x")
SIM_AXES = ("orientation", "phase", "y", "x")
COUNTS = {"time": 2, "channel": 3, "orientation": 2, "phase": 4, "z": 2, "y": 2, "x": 3}


def public_declaration() -> Any:
    """Resolve the required public callable at runtime, never at collection."""
    operation = getattr(simrecon, "declare_acquisition", None)
    assert callable(operation), "Missing callable simrecon.declare_acquisition export"
    return operation


def declare_acquisition(*args, **kwargs) -> Any:
    return public_declaration()(*args, **kwargs)


def test_public_exports():
    public_declaration()
    record_type = getattr(simrecon, "RawAcquisition", None)
    assert isinstance(record_type, type), "Missing simrecon.RawAcquisition record type export"


def config_for(axes: Any = SIM_AXES, kind: Any = "specimen_sim", **fields: Any) -> dict[str, Any]:
    return {"version": 1, "acquisition_kind": kind, "axes": list(axes), **fields}


def labeled_samples(axes, counts=None, dtype="int32"):
    """Decimal coordinate digits supply identities independently of array layout."""
    sizes = COUNTS if counts is None else {**COUNTS, **counts}
    data = np.empty(tuple(sizes[a] for a in axes), dtype=dtype)
    for index in np.ndindex(data.shape):
        labels = dict(zip(axes, index, strict=True))
        value = sum(labels.get(axis, 0) * 10**i for i, axis in enumerate(CANONICAL))
        data[index] = value
    return data


def sample_bytes(data, index):
    # A one-element slice reads storage without converting a floating scalar.
    return data[tuple(slice(i, i + 1) for i in index)].tobytes(order="C")


def input_identity(value):
    """Observe owned input values without ambiguous array/NaN equality."""
    if type(value) in (dict, UserDict):
        return (
            type(value),
            tuple((input_identity(k), input_identity(v)) for k, v in value.items()),
        )
    if type(value) in (list, tuple):
        return (type(value), tuple(input_identity(v) for v in value))
    if type(value) is float:
        return (float, struct.pack("=d", value))
    if type(value) is np.ndarray:
        return (np.ndarray, value.shape, value.strides, value.dtype.str, value.tobytes())
    if type(value) in (str, bytes, bool, int, type(None)):
        return (type(value), value)
    # Rejected opaque objects have no supported observation protocol.
    return (type(value), id(value))


def assert_coordinate_identity(result, source, axes):
    expected_axes = tuple(a for a in CANONICAL if a in axes)
    assert type(result.axes) is tuple
    assert type(result.source_axes) is tuple
    assert type(result.source_shape) is tuple
    assert result.axes == expected_axes
    assert result.source_axes == tuple(axes)
    assert result.source_shape == source.shape
    assert type(result.data) is np.ndarray
    assert result.data.flags.c_contiguous
    assert result.data.flags.writeable
    assert result.data.dtype == source.dtype
    assert result.data.dtype.str == source.dtype.str
    sizes = dict(zip(axes, source.shape, strict=True))
    assert result.data.shape == tuple(sizes[a] for a in expected_axes)
    for canonical_index in np.ndindex(result.data.shape):
        labels = dict(zip(expected_axes, canonical_index, strict=True))
        source_index = tuple(labels[a] for a in axes)
        assert sample_bytes(result.data, canonical_index) == sample_bytes(source, source_index)
    assert not np.shares_memory(result.data, source)


def assert_error(code, data, config, metadata=None):
    original_bytes = data.tobytes() if type(data) is np.ndarray else None
    config_before = input_identity(config)
    metadata_before = input_identity(metadata)
    with pytest.raises(SimreconError) as caught:
        declare_acquisition(data, config=config, original_metadata=metadata)
    allowed_codes = (code,) if isinstance(code, str) else code
    assert caught.value.code in allowed_codes
    if original_bytes is not None:
        assert data.tobytes() == original_bytes
    assert input_identity(config) == config_before
    assert input_identity(metadata) == metadata_before


# Public layouts: kinds, prefix orders, omissions and legitimate count alternatives.
@pytest.mark.parametrize("kind", ["specimen_sim", "sim_beads"])
@pytest.mark.parametrize("prefix", list(itertools.permutations(CANONICAL[:5])))
def test_all_sim_axis_orders(kind, prefix):
    axes = (*prefix, "y", "x")
    data = labeled_samples(axes)
    cfg = config_for(axes, kind)
    before = copy.deepcopy(cfg)
    result = declare_acquisition(data, config=cfg)
    record_type = getattr(simrecon, "RawAcquisition", None)
    assert isinstance(record_type, type)
    assert issubclass(type(result), record_type)
    assert result.acquisition_kind == kind
    assert_coordinate_identity(result, data, axes)
    assert cfg == before


PSF_PREFIXES = [p for n in range(4) for p in itertools.permutations(("time", "channel", "z"), n)]


@pytest.mark.parametrize("prefix", PSF_PREFIXES)
def test_detection_psf_all_permitted_prefixes(prefix):
    axes = (*prefix, "y", "x")
    data = labeled_samples(axes)
    result = declare_acquisition(data, config=config_for(axes, "detection_psf"))
    assert result.acquisition_kind == "detection_psf"
    assert_coordinate_identity(result, data, axes)


@pytest.mark.parametrize(
    "optional",
    [subset for n in range(4) for subset in itertools.combinations(("time", "channel", "z"), n)],
)
def test_optional_sim_axes_are_not_inserted_or_reinterpreted(optional):
    axes = (*optional, *SIM_AXES)
    data = labeled_samples(axes, {a: 1 for a in optional})
    result = declare_acquisition(data, config=config_for(axes))
    assert_coordinate_identity(result, data, axes)
    assert set(result.axes) == set(axes)


@pytest.mark.parametrize("kind", ["specimen_sim", "sim_beads"])
@pytest.mark.parametrize("orientation,phase", [(1, 1), (1, 2), (2, 1), (2, 5), (4, 7)])
@pytest.mark.parametrize("z", [False, True])
def test_small_large_and_nonidentifying_counts(kind, orientation, phase, z):
    axes = ("orientation", "z", "phase", "y", "x") if z else SIM_AXES
    data = labeled_samples(axes, {"orientation": orientation, "phase": phase, "z": 1})
    group_axes = tuple(a for a in axes if a not in ("z", "y", "x"))
    commands = np.full(tuple(data.shape[axes.index(a)] for a in group_axes), -9.25).tolist()
    result = declare_acquisition(data, config=config_for(axes, kind, nominal_phases_rad=commands))
    assert_coordinate_identity(result, data, axes)
    assert ("z" in result.axes) is z
    assert result.nominal_phase_axes == ("orientation", "phase")
    assert np.all(result.nominal_phases_rad == -9.25)


# RA05-RA07: storage bytes, arbitrary memory layout, independent owned buffers.
BIT_DTYPES = [
    f"{order}{kind}{width}" for order in ("<", ">") for kind in ("i", "u") for width in (1, 2, 4, 8)
]
BIT_DTYPES += [
    f"{order}f{width}"
    for order in ("<", ">")
    for width in (2, 4, 8, np.dtype(np.longdouble).itemsize)
]


@pytest.mark.parametrize("dtype", sorted(set(BIT_DTYPES)))
def test_exact_sample_storage_including_wider_float_padding(dtype):
    dt = np.dtype(dtype)
    shape = (4, 2, 2, 3)
    # Every byte, including any extended-float padding, has an independently
    # supplied identity. No floating evaluation is needed or permitted here.
    storage = bytearray((37 * i + 11) % 256 for i in range(math.prod(shape) * dt.itemsize))
    data = np.ndarray(shape, dtype=dt, buffer=storage)
    axes = ("phase", "orientation", "y", "x")
    before = bytes(storage)
    result = declare_acquisition(data, config=config_for(axes))
    assert_coordinate_identity(result, data, axes)
    assert bytes(storage) == before
    result.data.view(np.uint8).flat[0] ^= 1
    assert bytes(storage) == before


@pytest.mark.parametrize("order", ["<", ">"])
@pytest.mark.parametrize(
    "width,bits",
    [
        (2, [0x0000, 0x8000, 0x7C00, 0xFC00, 0x7E21, 0x7C01, 0x0001, 0xBC00]),
        (4, [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC12345, 0x7F800001, 1, 0xBF800000]),
        (
            8,
            [
                0,
                0x8000000000000000,
                0x7FF0000000000000,
                0xFFF0000000000000,
                0x7FF8123456789ABC,
                0x7FF0000000000001,
                1,
                0xBFF0000000000000,
            ],
        ),
    ],
)
def test_float_special_values_are_samples_not_metadata(order, width, bits):
    byte_order = "little" if order == "<" else "big"
    raw = b"".join(v.to_bytes(width, byte_order) for v in bits)
    data = np.ndarray((2, 2, 1, 2), dtype=f"{order}f{width}", buffer=raw)
    before = np.geterr()
    with np.errstate(all="raise"):
        mode = np.geterr()
        result = declare_acquisition(data, config=config_for())
        assert np.geterr() == mode
    assert np.geterr() == before
    assert_coordinate_identity(result, data, SIM_AXES)


@pytest.mark.parametrize("layout", ["fortran", "stride", "reverse", "readonly"])
def test_input_memory_layout_and_caller_preservation(layout):
    axes = ("z", "orientation", "phase", "y", "x")
    data = labeled_samples(axes)
    if layout == "fortran":
        data = np.asfortranarray(data)
    elif layout == "stride":
        data = data[..., ::2]
    elif layout == "reverse":
        data = data[::-1, ..., ::-1]
    else:
        data.flags.writeable = False
    before, strides, writable = data.tobytes(), data.strides, data.flags.writeable
    result = declare_acquisition(data, config=config_for(axes))
    assert_coordinate_identity(result, data, axes)
    assert data.tobytes() == before
    assert data.strides == strides
    assert data.flags.writeable == writable


def test_owned_samples_survive_input_mutation():
    data = labeled_samples(SIM_AXES)
    result = declare_acquisition(data, config=config_for())
    saved = result.data.tobytes()
    data.fill(-123)
    assert result.data.tobytes() == saved


def test_declaration_needs_no_file_opening(monkeypatch):
    data, cfg = labeled_samples(SIM_AXES), config_for()

    def forbidden_open(*args, **kwargs):
        pytest.fail("Pure declaration attempted file I/O")

    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", forbidden_open)
        patch.setattr(os, "open", forbidden_open)
        patch.setattr(Path, "open", forbidden_open)
        result = declare_acquisition(data, config=cfg)
    assert_coordinate_identity(result, data, SIM_AXES)


# RA08-RA13: missing values, explicit units, sparse channels and nominal commands.
@pytest.mark.parametrize(
    "field_value", [{}, {"sampling_um": None, "wavelengths_nm": None, "nominal_phases_rad": None}]
)
def test_unknown_metadata_remains_unknown(field_value):
    metadata = {"sampling_um": {"x": 123}, "nominal_phases_rad": [1], "wavelengths_nm": {"0": 600}}
    result = declare_acquisition(
        labeled_samples(SIM_AXES), config=config_for(**field_value), original_metadata=metadata
    )
    assert type(result.sampling_um) is dict
    assert type(result.wavelengths_nm) is dict
    assert type(result.nominal_phase_axes) is tuple
    assert result.sampling_um == {"x": None, "y": None, "z": None}
    assert result.wavelengths_nm == {}
    assert result.nominal_phases_rad is None
    assert result.nominal_phase_axes == ()
    assert result.intensity_unit is None
    assert result.acquisition_id is None
    assert result.calibration_id is None


@pytest.mark.parametrize("sampling", [{"x": 1}, {"y": 0.0975, "x": None}, {"z": None}, {}])
def test_sampling_is_sparse_and_explicit_micrometres(sampling):
    result = declare_acquisition(labeled_samples(SIM_AXES), config=config_for(sampling_um=sampling))
    expected = {"x": None, "y": None, "z": None, **sampling}
    assert result.sampling_um == expected
    for value in result.sampling_um.values():
        assert value is None or type(value) is float


def test_declared_z_may_have_unknown_or_explicit_sampling():
    axes = ("z", *SIM_AXES)
    data = labeled_samples(axes)
    for sampling in ({"z": None}, {"x": 1, "y": 2, "z": 3}):
        result = declare_acquisition(data, config=config_for(axes, sampling_um=sampling))
        assert result.sampling_um == {"x": None, "y": None, "z": None, **sampling}


@pytest.mark.parametrize("channel", [False, True])
def test_wavelengths_are_sparse_generic_binary64_values(channel):
    axes = ("channel", *SIM_AXES) if channel else SIM_AXES
    wavelengths = {"0": 488, "2": 640.25} if channel else {"0": 488}
    result = declare_acquisition(
        labeled_samples(axes), config=config_for(axes, wavelengths_nm=wavelengths)
    )
    assert result.wavelengths_nm == {k: float(v) for k, v in wavelengths.items()}
    assert all(type(v) is float for v in result.wavelengths_nm.values())


def test_smallest_positive_binary64_and_one_rounding():
    smallest = float.fromhex("0x0.0000000000001p-1022")
    integer = 2**53 + 1
    result = declare_acquisition(
        labeled_samples(SIM_AXES),
        config=config_for(
            sampling_um={"x": smallest, "y": integer},
            wavelengths_nm={"0": integer},
            nominal_phases_rad=[[integer] * 4] * 2,
        ),
    )
    assert result.sampling_um == {"x": smallest, "y": float(2**53), "z": None}
    assert result.wavelengths_nm == {"0": float(2**53)}
    assert np.all(result.nominal_phases_rad == float(2**53))


@pytest.mark.parametrize(
    "prefix", list(itertools.permutations(("time", "channel", "orientation", "phase")))
)
def test_nominal_command_named_coordinates_and_no_modulo(prefix):
    axes = (*prefix[:2], "z", *prefix[2:], "y", "x")
    group_shape = tuple(COUNTS[a] for a in prefix)
    commands = np.empty(group_shape, dtype=np.float64)
    expected = {}
    for index in np.ndindex(group_shape):
        labels = dict(zip(prefix, index, strict=True))
        value = -20.5 + sum(labels[a] * 10**i for i, a in enumerate(CANONICAL[:4]))
        commands[index] = value
        expected[tuple(labels[a] for a in CANONICAL[:4])] = struct.pack("=d", value)
    supplied = commands.tolist()
    result = declare_acquisition(
        labeled_samples(axes), config=config_for(axes, nominal_phases_rad=supplied)
    )
    assert result.nominal_phase_axes == CANONICAL[:4]
    assert result.nominal_phases_rad.dtype == np.dtype("float64")
    assert result.nominal_phases_rad.flags.c_contiguous
    assert result.nominal_phases_rad.shape == tuple(COUNTS[a] for a in CANONICAL[:4])
    for index, bits in expected.items():
        assert sample_bytes(result.nominal_phases_rad, index) == bits
    saved = result.nominal_phases_rad.tobytes()
    supplied[0][0][0][0] = 99
    assert result.nominal_phases_rad.tobytes() == saved


def test_nominal_tuple_commands_keep_signed_zero_and_negative_angles():
    commands = ((-0.0, 0.0, -19.0, 25.0),) * 2
    result = declare_acquisition(
        labeled_samples(SIM_AXES), config=config_for(nominal_phases_rad=commands)
    )
    assert result.nominal_phase_axes == ("orientation", "phase")
    assert result.nominal_phases_rad.tobytes() == b"".join(
        struct.pack("=d", v) for row in commands for v in row
    )
    assert result.original_config["nominal_phases_rad"] == commands


@pytest.mark.parametrize(
    "optional",
    [subset for n in range(3) for subset in itertools.combinations(("time", "channel"), n)],
)
def test_commands_retain_only_declared_group_dimensions(optional):
    axes = ("phase", *optional, "orientation", "y", "x")
    group_axes = axes[:-2]
    group_shape = tuple(COUNTS[a] for a in group_axes)
    commands = np.empty(group_shape, dtype=np.float64)
    expected = {}
    canonical_groups = tuple(a for a in CANONICAL[:4] if a in axes)
    for index in np.ndindex(group_shape):
        labels = dict(zip(group_axes, index, strict=True))
        value = -0.25 + sum(labels.get(a, 0) * 10**i for i, a in enumerate(CANONICAL[:4]))
        commands[index] = value
        expected[tuple(labels[a] for a in canonical_groups)] = struct.pack("=d", value)
    result = declare_acquisition(
        labeled_samples(axes), config=config_for(axes, nominal_phases_rad=commands.tolist())
    )
    assert result.nominal_phase_axes == canonical_groups
    assert result.nominal_phases_rad.shape == tuple(COUNTS[a] for a in canonical_groups)
    assert type(result.nominal_phases_rad) is np.ndarray
    for index, bits in expected.items():
        assert sample_bytes(result.nominal_phases_rad, index) == bits


@pytest.mark.parametrize("kind", ["specimen_sim", "detection_psf", "sim_beads"])
@pytest.mark.parametrize("text", ["detector counts", " photoelectrons ", "   ", "opaque-μ-ID"])
def test_opaque_units_and_ids_preserve_text(kind, text):
    axes = ("y", "x") if kind == "detection_psf" else SIM_AXES
    result = declare_acquisition(
        labeled_samples(axes),
        config=config_for(
            axes,
            kind,
            intensity_unit=text,
            acquisition_id=text,
            calibration_id=text,
        ),
    )
    assert (result.intensity_unit, result.acquisition_id, result.calibration_id) == (
        text,
        text,
        text,
    )


# RA14-RA17: recursive snapshots, replacement and deterministic raw provenance.
def test_supported_mapping_roots_and_opaque_metadata_snapshots():
    cfg = UserDict(config_for(sampling_um={"x": 1}))
    metadata: UserDict[str, Any] = UserDict(
        {
            "nested": [{"tuple": (b"\x00\xff", True, None, -5, math.inf, math.nan)}],
            "commands_unknown": [None],
        }
    )
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg, original_metadata=metadata)
    assert type(result.original_metadata["nested"]) is list
    values = result.original_metadata["nested"][0]["tuple"]
    assert type(values) is tuple
    assert values[:5] == (b"\x00\xff", True, None, -5, math.inf)
    assert math.isnan(values[5])
    metadata["nested"][0]["tuple"] = ()
    cfg["sampling_um"]["x"] = 99
    assert result.original_metadata["nested"][0]["tuple"] == values
    assert result.original_config["sampling_um"]["x"] == 1
    assert result.sampling_um["x"] == 1.0


def test_nested_snapshot_mutation_is_independent_in_both_directions():
    cfg = config_for(
        sampling_um={"x": 1},
        wavelengths_nm={"0": 520},
        nominal_phases_rad=[[0, 1, 2, 3], [4, 5, 6, 7]],
    )
    metadata = {"nested": [{"values": [1, (b"header", None)]}], "nonfinite": -math.inf}
    cfg_before, metadata_before = input_identity(cfg), input_identity(metadata)
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg, original_metadata=metadata)
    assert input_identity(cfg) == cfg_before
    assert input_identity(metadata) == metadata_before
    result.original_metadata["nested"][0]["values"].append(2)
    assert input_identity(metadata) == metadata_before
    metadata["nested"][0]["values"][0] = 9
    assert result.original_metadata["nested"][0]["values"][0] == 1
    result.wavelengths_nm["0"] = 600.0
    result.nominal_phases_rad.fill(99)
    assert input_identity(cfg) == cfg_before
    assert result.original_config["wavelengths_nm"] == {"0": 520}
    assert result.original_config["nominal_phases_rad"] == [[0, 1, 2, 3], [4, 5, 6, 7]]
    commands_entry = next(e for e in result.provenance if e["field"] == "nominal_phases_rad")
    commands_entry["new"][0][0] = 42
    assert result.original_config["nominal_phases_rad"][0][0] == 0
    assert cfg["nominal_phases_rad"][0][0] == 0


@pytest.mark.parametrize("metadata", [None, {}])
def test_original_metadata_defaults_to_empty_owned_dict(metadata):
    result = declare_acquisition(
        labeled_samples(SIM_AXES), config=config_for(), original_metadata=metadata
    )
    assert result.original_metadata == {}
    if metadata is not None:
        result.original_metadata["new"] = 1
        assert metadata == {}


def test_provenance_raw_values_order_and_independence():
    cfg = config_for(
        sampling_um={"x": 1, "y": 2},
        wavelengths_nm={"0": 488},
        nominal_phases_rad=[[0, 1, 2, 3], [4, 5, 6, 7]],
        intensity_unit="counts",
        overrides={"sampling_um": {"x": 3}, "wavelengths_nm": {"0": 488}, "calibration_id": None},
    )
    before = copy.deepcopy(cfg)
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg)
    expected = [
        {"field": name, "old": None, "new": copy.deepcopy(before[name]), "source": "config"}
        for name in sorted(set(before) - {"version", "overrides"})
    ] + [
        {
            "field": name,
            "old": copy.deepcopy(before.get(name)),
            "new": copy.deepcopy(value),
            "source": "override",
        }
        for name, value in sorted(before["overrides"].items())
    ]
    assert type(result.provenance) is tuple
    assert result.provenance == tuple(expected)
    assert result.original_config == before
    assert cfg == before
    assert result.sampling_um == {"x": 3.0, "y": None, "z": None}
    # Mutate each returned snapshot independently; record mutability is allowed.
    initial = next(
        e for e in result.provenance if e["field"] == "sampling_um" and e["source"] == "config"
    )
    override = next(
        e for e in result.provenance if e["field"] == "sampling_um" and e["source"] == "override"
    )
    initial["new"]["x"] = 77
    assert override["old"]["x"] == 1
    assert result.original_config["sampling_um"]["x"] == 1
    override["new"]["x"] = 88
    assert result.original_config["overrides"]["sampling_um"]["x"] == 3
    result.sampling_um["x"] = 90
    result.original_config["axes"].append("changed")
    assert next(e for e in result.provenance if e["field"] == "axes")["new"] == list(SIM_AXES)
    assert cfg == before


@pytest.mark.parametrize(
    "field,original,replacement,expected",
    [
        ("sampling_um", {"x": -1, "z": math.inf}, {"y": 2}, {"x": None, "y": 2.0, "z": None}),
        ("wavelengths_nm", {"bad": -1}, {"0": 510}, {"0": 510.0}),
        ("nominal_phases_rad", [[math.nan]], None, None),
        ("intensity_unit", 3, "counts", "counts"),
        ("acquisition_id", "", "new-id", "new-id"),
        ("calibration_id", False, None, None),
    ],
)
def test_invalid_original_field_can_be_replaced(field, original, replacement, expected):
    cfg = config_for(**{field: original}, overrides={field: replacement})
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg)
    assert getattr(result, field) == expected
    assert result.original_config[field] == original
    override = next(e for e in result.provenance if e["source"] == "override")
    assert override["field"] == field
    assert override["old"] == original
    assert override["new"] == replacement


def test_whole_field_command_and_string_overrides():
    replacement = [[-1, -2, -3, -4], [5, 6, 7, 8]]
    cfg = config_for(
        nominal_phases_rad=[[0] * 4] * 2,
        intensity_unit="old",
        acquisition_id="old",
        calibration_id="old",
        overrides={
            "nominal_phases_rad": replacement,
            "intensity_unit": None,
            "acquisition_id": "new",
            "calibration_id": "new",
        },
    )
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg)
    assert result.nominal_phases_rad.tolist() == replacement
    assert result.intensity_unit is None
    assert result.acquisition_id == result.calibration_id == "new"


@pytest.mark.parametrize("explicit_original", [False, True])
def test_none_overrides_are_recorded_even_when_equal_or_originally_absent(explicit_original):
    fields = (
        "sampling_um",
        "wavelengths_nm",
        "nominal_phases_rad",
        "intensity_unit",
        "acquisition_id",
        "calibration_id",
    )
    original = dict.fromkeys(fields) if explicit_original else {}
    cfg = config_for(**original, overrides=dict.fromkeys(fields))
    result = declare_acquisition(labeled_samples(SIM_AXES), config=cfg)
    overrides = tuple(e for e in result.provenance if e["source"] == "override")
    assert overrides == tuple(
        {"field": field, "old": None, "new": None, "source": "override"} for field in sorted(fields)
    )
    initial_fields = tuple(e["field"] for e in result.provenance if e["source"] == "config")
    assert initial_fields == tuple(sorted({"axes", "acquisition_kind", *original}))
    assert result.original_config == cfg
    assert result.sampling_um == {"x": None, "y": None, "z": None}
    assert result.wavelengths_nm == {}
    assert result.nominal_phases_rad is None
    assert result.nominal_phase_axes == ()
    assert result.intensity_unit is result.acquisition_id is result.calibration_id is None


# RA18-RA26: independently isolated invalid inputs and stable codes.
class ArraySubclass(np.ndarray):
    """A genuine ndarray subclass outside the supported plain-array domain."""


@pytest.mark.parametrize(
    "data", [[[1, 2]], np.ma.array([[1, 2]]), np.zeros((2, 3)).view(ArraySubclass), None]
)
def test_reject_nonplain_sample_arrays(data):
    assert_error("invalid_acquisition_data", data, config_for(("y", "x"), "detection_psf"))


@pytest.mark.parametrize(
    "dtype",
    ["bool", "complex64", "object", "U2", "S2", "datetime64[D]", "timedelta64[D]", [("v", "i4")]],
)
def test_reject_sample_dtype(dtype):
    assert_error(
        "invalid_acquisition_dtype",
        np.zeros((2, 3), dtype=dtype),
        config_for(("y", "x"), "detection_psf"),
    )


@pytest.mark.parametrize(
    "data,axes", [(np.zeros((0, 3)), ["y", "x"]), (np.zeros((2, 3)), ["z", "y", "x"])]
)
def test_reject_nonpositive_or_rank_mismatched_shape(data, axes):
    assert_error("invalid_acquisition_shape", data, config_for(axes, "detection_psf"))


@pytest.mark.parametrize(
    "axes", [None, ("y", "x"), ["x", "y"], ["y", "y"], ["z", "x"], ["y", "exposure"], [1, "x"]]
)
def test_reject_invalid_axis_declarations(axes):
    cfg = config_for(("y", "x"), "detection_psf")
    cfg["axes"] = axes
    assert_error("invalid_acquisition_axes", np.zeros((2, 3)), cfg)


@pytest.mark.parametrize("extra", ["switch_off", "I2M", "section", "exposure"])
def test_reject_extra_exposure_axes(extra):
    assert_error(
        "invalid_acquisition_axes",
        np.zeros((2, 2, 3)),
        config_for([extra, "y", "x"], "detection_psf"),
    )


@pytest.mark.parametrize(
    "kind,axes",
    [
        ("unknown", SIM_AXES),
        (None, SIM_AXES),
        (3, SIM_AXES),
        ("specimen_sim", ("y", "x")),
        ("sim_beads", ("orientation", "y", "x")),
        ("specimen_sim", ("phase", "y", "x")),
        ("detection_psf", ("orientation", "y", "x")),
        ("detection_psf", ("phase", "y", "x")),
    ],
)
def test_reject_unknown_or_incompatible_kind(kind, axes):
    assert_error("invalid_acquisition_kind", labeled_samples(axes), config_for(axes, kind))


@pytest.mark.parametrize(
    "cfg",
    [
        None,
        [],
        {},
        {"version": 1, "axes": list(SIM_AXES)},
        {"version": 1, "acquisition_kind": "specimen_sim"},
        config_for(version=True),
        config_for(version=1.0),
        config_for(version=2),
        config_for(unknown=None),
        config_for(overrides=None),
        config_for(overrides=[]),
        config_for(overrides={"version": 1}),
        config_for(overrides={"axes": list(SIM_AXES)}),
        config_for(overrides={"acquisition_kind": "specimen_sim"}),
        config_for(overrides={"extra": 1}),
        config_for(overrides={1: None}),
        config_for(sampling_um={"x": b"1"}, overrides={"sampling_um": {"x": 1}}),
    ],
)
def test_reject_config_schema(cfg):
    assert_error("invalid_acquisition_config", labeled_samples(SIM_AXES), cfg)


@pytest.mark.parametrize("field", ["intensity_unit", "acquisition_id", "calibration_id"])
@pytest.mark.parametrize("bad", ["", 1, False, [], b"id"])
def test_reject_invalid_optional_strings(field, bad):
    assert_error(
        "invalid_acquisition_config", labeled_samples(SIM_AXES), config_for(**{field: bad})
    )


@pytest.mark.parametrize(
    "value", [True, False, -1, 0, -0.0, math.inf, -math.inf, math.nan, 10**1000, "1", []]
)
def test_reject_sampling_value(value):
    assert_error(
        "invalid_acquisition_sampling",
        labeled_samples(SIM_AXES),
        config_for(sampling_um={"x": value}),
    )


@pytest.mark.parametrize("sampling", [[], {"extra": 1}, {"z": 1}, {1: 1}])
def test_reject_sampling_schema_or_absent_z_contradiction(sampling):
    code = (
        ("invalid_acquisition_config", "invalid_acquisition_sampling")
        if isinstance(sampling, dict) and 1 in sampling
        else "invalid_acquisition_sampling"
    )
    assert_error(code, labeled_samples(SIM_AXES), config_for(sampling_um=sampling))


@pytest.mark.parametrize(
    "wavelengths",
    [
        [],
        {"00": 488},
        {"+0": 488},
        {"-1": 488},
        {" 0": 488},
        {"0.0": 488},
        {"٠": 488},
        {0: 488},
        {"1": 488},
        {"999999999999999999999999": 488},
    ],
)
def test_reject_wavelength_schema_and_unindexed_key_bounds(wavelengths):
    code = (
        ("invalid_acquisition_config", "invalid_acquisition_wavelengths")
        if isinstance(wavelengths, dict) and 0 in wavelengths
        else "invalid_acquisition_wavelengths"
    )
    assert_error(
        code,
        labeled_samples(SIM_AXES),
        config_for(wavelengths_nm=wavelengths),
    )


@pytest.mark.parametrize("value", [True, 0, -1, math.inf, math.nan, 10**1000, "488", None])
def test_reject_wavelength_value(value):
    assert_error(
        "invalid_acquisition_wavelengths",
        labeled_samples(SIM_AXES),
        config_for(wavelengths_nm={"0": value}),
    )


def test_reject_channel_index_equal_to_count():
    axes = ("channel", *SIM_AXES)
    assert_error(
        "invalid_acquisition_wavelengths",
        labeled_samples(axes),
        config_for(axes, wavelengths_nm={"3": 488}),
    )


@pytest.mark.parametrize(
    "commands",
    [
        0,
        [],
        [0, 1, 2, 3],
        [[0, 1], [2]],
        [[0] * 4],
        [[[0] * 4] * 2],
        np.zeros((2, 4)),
        [[None] * 4] * 2,
    ],
)
def test_reject_partial_ragged_broadcast_or_nonbuiltin_commands(commands):
    # A NumPy tensor violates both the whole-config domain and the effective
    # command type. Their simultaneous-error precedence is unspecified.
    if type(commands) is np.ndarray:
        assert_error(
            ("invalid_acquisition_config", "invalid_acquisition_phase_commands"),
            labeled_samples(SIM_AXES),
            config_for(nominal_phases_rad=commands),
        )
    else:
        assert_error(
            "invalid_acquisition_phase_commands",
            labeled_samples(SIM_AXES),
            config_for(nominal_phases_rad=commands),
        )


@pytest.mark.parametrize("value", [True, math.inf, -math.inf, math.nan, 10**1000, "0", None])
def test_reject_command_numeric_leaves(value):
    commands = [[0, 1, 2, value], [0, 1, 2, 3]]
    assert_error(
        "invalid_acquisition_phase_commands",
        labeled_samples(SIM_AXES),
        config_for(nominal_phases_rad=commands),
    )


def test_reject_missing_nominal_time_channel_group_dimensions():
    axes = ("time", "channel", *SIM_AXES)
    assert_error(
        "invalid_acquisition_phase_commands",
        labeled_samples(axes),
        config_for(axes, nominal_phases_rad=[[0] * 4] * 2),
    )


def test_detection_psf_rejects_even_empty_commands():
    axes = ("y", "x")
    assert_error(
        "invalid_acquisition_phase_commands",
        labeled_samples(axes),
        config_for(axes, "detection_psf", nominal_phases_rad=[]),
    )


@pytest.mark.parametrize(
    "metadata",
    [
        [],
        {1: "x"},
        {"nested": {1: "x"}},
        {"array": np.zeros(1)},
        {"custom": object()},
        {"set": {1}},
    ],
)
def test_reject_unsupported_original_metadata(metadata):
    assert_error("invalid_acquisition_metadata", labeled_samples(SIM_AXES), config_for(), metadata)


@pytest.mark.parametrize(
    "field,bad,code",
    [
        ("sampling_um", {"x": 0}, "invalid_acquisition_sampling"),
        ("wavelengths_nm", {"0": 0}, "invalid_acquisition_wavelengths"),
        ("nominal_phases_rad", [[0]], "invalid_acquisition_phase_commands"),
        ("intensity_unit", "", "invalid_acquisition_config"),
        ("acquisition_id", "", "invalid_acquisition_config"),
        ("calibration_id", False, "invalid_acquisition_config"),
    ],
)
def test_invalid_effective_override_is_rejected(field, bad, code):
    assert_error(code, labeled_samples(SIM_AXES), config_for(overrides={field: bad}))


# Binding, handled metadata range errors and NumPy mode preservation.
def test_normal_python_argument_binding_errors():
    operation = public_declaration()
    data = labeled_samples(SIM_AXES)
    with pytest.raises(TypeError):
        operation(data)
    with pytest.raises(TypeError):
        operation(data, config_for())
    with pytest.raises(TypeError):
        operation(data, config=config_for(), extra=True)
    with pytest.raises(TypeError):
        operation(data, config_for(), {})


@pytest.mark.parametrize(
    "field,code",
    [
        ("sampling_um", "invalid_acquisition_sampling"),
        ("wavelengths_nm", "invalid_acquisition_wavelengths"),
        ("nominal_phases_rad", "invalid_acquisition_phase_commands"),
    ],
)
def test_metadata_range_rejections_preserve_error_mode_without_runtime_warning(field, code):
    huge = 10**1000
    value = (
        {"x": huge}
        if field == "sampling_um"
        else {"0": huge}
        if field == "wavelengths_nm"
        else [[huge] * 4] * 2
    )
    data, cfg = labeled_samples(SIM_AXES), config_for(**{field: value})
    original_mode = np.geterr()
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        mode = np.geterr()
        assert_error(code, data, cfg)
        assert np.geterr() == mode
    assert np.geterr() == original_mode
    assert not any(issubclass(w.category, RuntimeWarning) for w in emitted)


def test_success_preserves_mixed_numpy_error_modes():
    data, cfg = (
        labeled_samples(SIM_AXES),
        config_for(sampling_um={"x": 0.125}, nominal_phases_rad=[[0, 1, 2, 3], [4, 5, 6, 7]]),
    )
    before = np.geterr()
    with np.errstate(divide="raise", over="ignore", under="warn", invalid="print"):
        mode = np.geterr()
        result = declare_acquisition(data, config=cfg)
        assert np.geterr() == mode
    assert np.geterr() == before
    assert_coordinate_identity(result, data, SIM_AXES)


# RA30: synthetic MRC -> public inspect/harmonize/read -> explicit declaration.
@pytest.mark.parametrize("byte_order", ["<", ">"])
@pytest.mark.parametrize("pixel_mode", [6, 2])
@pytest.mark.parametrize(
    "axes", [("z", "orientation", "phase", "y", "x"), ("orientation", "z", "phase", "y", "x")]
)
def test_public_mrc_composition_and_independent_coordinate_labels(
    tmp_path, byte_order, pixel_mode, axes
):
    sizes = {"z": 2, "orientation": 2, "phase": 3, "y": 2, "x": 5}
    header = bytearray(1024)
    for offset, value in [
        (0, 5),
        (4, 2),
        (8, 12),
        (12, pixel_mode),
        (28, 5),
        (32, 2),
        (36, 2),
        (64, 1),
        (68, 2),
        (72, 3),
        (92, 0),
    ]:
        struct.pack_into(byte_order + "i", header, offset, value)
    for offset, value in [(40, 0.125), (44, 0.25), (48, 0.5)]:
        struct.pack_into(byte_order + "f", header, offset, value)
    for offset, value in [(96, -16224), (180, 1), (182, 0), (196, 1), (198, 520)]:
        struct.pack_into(byte_order + "h", header, offset, value)
    expected = {}
    payload = bytearray()
    for source_index in itertools.product(*(range(sizes[a]) for a in axes)):
        labels = dict(zip(axes, source_index, strict=True))
        value = (
            40000
            + labels["z"] * 1000
            + labels["orientation"] * 100
            + labels["phase"] * 10
            + labels["y"] * 5
            + labels["x"]
        )
        if pixel_mode == 6:
            source_bytes = struct.pack(byte_order + "H", value)
            native_bytes = struct.pack("=H", value)
        else:
            # Coordinate ordinal selects explicit IEEE-754 storage patterns.
            # No float assignment or comparison touches NaN payloads.
            ordinal = (
                ((labels["z"] * 2 + labels["orientation"]) * 3 + labels["phase"]) * 2 + labels["y"]
            ) * 5 + labels["x"]
            patterns = (0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC12345, 0x7F800001)
            bits = patterns[ordinal] if ordinal < len(patterns) else 0x3F800000 + ordinal * 271
            source_bytes = struct.pack(byte_order + "I", bits)
            native_bytes = struct.pack("=I", bits)
        expected[tuple(labels[a] for a in ("orientation", "phase", "z", "y", "x"))] = native_bytes
        payload.extend(source_bytes)
    path = tmp_path / "asymmetric.mrc"
    original_file = bytes(header) + bytes(payload)
    path.write_bytes(original_file)
    info = harmonize(
        inspect(path),
        config={
            "version": 1,
            "data_kind": "spatial_image",
            "plane_axes": list(axes[:-2]),
            "plane_shape": [2, 2, 3],
            "spatial_fields": "direct_um",
            "extended_header": "none",
        },
    )
    block = read(info, plane_start=0, plane_stop=12)
    cfg = config_for(
        info.axes, sampling_um=dict(info.sampling_um), wavelengths_nm=dict(info.wavelengths_nm)
    )
    metadata = {
        "header": info.original_header,
        "file": dict(info.file_metadata),
        "provenance": info.provenance,
    }
    source = block.data.reshape(info.shape)
    result = declare_acquisition(source, config=cfg, original_metadata=metadata)
    assert result.axes == ("orientation", "phase", "z", "y", "x")
    for index, native_bytes in expected.items():
        assert sample_bytes(result.data, index) == native_bytes
    assert_coordinate_identity(result, source, info.axes)
    assert result.original_metadata["header"] == bytes(header)
    assert result.sampling_um == {"x": 0.125, "y": 0.25, "z": 0.5}
    assert result.wavelengths_nm == dict(info.wavelengths_nm)
    assert result.wavelengths_nm == {"0": 520.0}
    assert result.nominal_phases_rad is None
    assert result.acquisition_kind == "specimen_sim"
    assert path.read_bytes() == original_file
    saved = result.data.tobytes()
    source.fill(0)
    assert result.data.tobytes() == saved
