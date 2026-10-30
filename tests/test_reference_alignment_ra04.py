"""Blind RA04 public-boundary tests; expectations come from approved equations."""

from __future__ import annotations

import copy
import warnings
from contextlib import contextmanager
from decimal import Decimal, localcontext
from typing import Any, Literal

import numpy as np
import pytest

import simrecon as sr
from reference_alignment_ra04_fixture import (
    PairExample,
    acquisition,
    carrier_point,
    declared_example,
    estimated_example,
    reconstruction_control,
)

RAW_FIELDS = (
    "data",
    "axes",
    "source_axes",
    "source_shape",
    "acquisition_kind",
    "sampling_um",
    "wavelengths_nm",
    "nominal_phases_rad",
    "nominal_phase_axes",
    "intensity_unit",
    "acquisition_id",
    "calibration_id",
    "original_config",
    "original_metadata",
    "provenance",
)
CAMERA_FIELDS = (
    "means_counts",
    "variances_counts2",
    "frame_means_counts",
    "frame_variances_counts2",
    "empirical_mean_se_counts",
    "contrast_counts",
    "gain_counts_per_e",
    "information_codes",
    "source",
)
PAIR_FIELDS = (
    "status",
    "information_codes",
    "mode",
    "output_unit",
    "gauge_source",
    "reference_sum_equalization",
    "specimen_exposure_factor",
    "bead_exposure_factor",
)
FRAME_FIELDS = ("data", "axes", "input_unit", "output_unit", "source_metadata", "provenance")


def record(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(value, field) for field in fields}


def pair_tree(value: Any) -> dict[str, Any]:
    result = record(value, PAIR_FIELDS)
    for name in ("specimen", "bead"):
        member = getattr(value, name)
        result[name] = None if member is None else record(member, FRAME_FIELDS)
    estimate = value.camera_estimate
    result["camera_estimate"] = None if estimate is None else record(estimate, CAMERA_FIELDS)
    return result


def same(actual: Any, expected: Any) -> None:
    """Exact public value observer; does not inspect product internals."""
    assert type(actual) is type(expected)
    if isinstance(expected, np.ndarray):
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        assert actual.tobytes() == expected.tobytes()
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            same(actual[key], expected[key])
    elif isinstance(expected, (tuple, list)):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected, strict=True):
            same(a, b)
    else:
        assert actual == expected


def mutable_nodes(tree: Any) -> list[Any]:
    nodes: list[Any] = []
    if isinstance(tree, (np.ndarray, dict, list)):
        nodes.append(tree)
    if isinstance(tree, dict):
        for child in tree.values():
            nodes.extend(mutable_nodes(child))
    elif isinstance(tree, (tuple, list)):
        for child in tree:
            nodes.extend(mutable_nodes(child))
    return nodes


def independent(*trees: Any) -> None:
    nodes = [node for tree in trees for node in mutable_nodes(tree)]
    assert len({id(node) for node in nodes}) == len(nodes)
    arrays = [node for node in nodes if isinstance(node, np.ndarray)]
    for i, array in enumerate(arrays):
        for other in arrays[i + 1 :]:
            assert not np.shares_memory(array, other)


def correct(example: PairExample, **changes: Any) -> Any:
    arguments = example.arguments | changes
    specimen = arguments.pop("specimen", example.specimen)
    bead = arguments.pop("bead", example.bead)
    # A local public lookup permits independent existing-interface controls to run
    # before this additive API exists. No product source/type discovery occurs.
    return public_export("correct_alignment_pair")(specimen, bead=bead, **arguments)


def public_export(name: str) -> Any:
    return getattr(sr, name)


@contextmanager
def error(code: str):
    with pytest.raises(sr.SimreconError) as caught:
        yield
    assert caught.value.code == code


def estimate_case(**options: Any) -> tuple[PairExample, Any, dict[str, Any]]:
    example, groups, truth = estimated_example(**options)
    estimate = sr.estimate_scalar_camera(
        groups[0], blank_counts=groups[1], flat_counts=groups[2], source=" retained camera source "
    )
    return example, estimate, truth


def test_public_exports_and_binding() -> None:
    example = declared_example()
    result = correct(example)
    assert isinstance(result, public_export("AlignmentCameraPair"))
    assert isinstance(result.specimen, public_export("AlignmentCameraFrames"))
    operation = public_export("correct_alignment_pair")
    for key in (
        "mode",
        "output_unit",
        "gauge_source",
        "reference_sum_equalization",
        "specimen_exposure_factor",
        "bead_exposure_factor",
    ):
        args = example.arguments.copy()
        del args[key]
        with pytest.raises(TypeError):
            operation(example.specimen, bead=example.bead, **args)
    with pytest.raises(TypeError):
        operation(example.specimen, example.bead, **example.arguments)
    with pytest.raises(TypeError):
        operation(example.specimen, bead=example.bead, unknown=True, **example.arguments)
    with pytest.raises(TypeError):
        operation(example.specimen, **example.arguments)


@pytest.mark.parametrize("maps", [False, True])
def test_declared_common_gauge_exact(maps: bool) -> None:
    example = declared_example(maps=maps)
    result = correct(example)
    assert result.status == "corrected"
    assert result.information_codes == ()
    assert result.camera_estimate is None
    for name in ("mode", "output_unit", "gauge_source", "reference_sum_equalization"):
        assert getattr(result, name) == example.arguments[name]
    for name in ("specimen", "bead"):
        frame = getattr(result, name)
        np.testing.assert_array_equal(frame.data, getattr(example, name + "_signal"))
        assert type(frame.data) is np.ndarray
        assert frame.data.dtype == np.dtype("float64")
        assert frame.data.flags.c_contiguous and frame.data.flags.owndata
        assert frame.axes == getattr(example, name).axes
        assert frame.input_unit == "detector count"
        assert frame.output_unit == " shared signal "


@pytest.mark.parametrize(
    "offset_map,response_map", [(False, False), (True, False), (False, True), (True, True)]
)
def test_each_member_scalar_map_combinations(offset_map: bool, response_map: bool) -> None:
    example = declared_example()
    changes = {}
    for name in ("specimen", "bead"):
        shape = getattr(example, name).data.shape
        for kind, mapped in (("offset", offset_map), ("response", response_map)):
            key = name + "_" + kind
            if mapped:
                changes[key] = np.full(shape, example.arguments[key], dtype=">f8")
                changes[key].flags.writeable = False
    result = correct(example, **changes)
    np.testing.assert_array_equal(result.specimen.data, example.specimen_signal)
    np.testing.assert_array_equal(result.bead.data, example.bead_signal)


def test_full_canonical_coordinates_and_source_metadata() -> None:
    # Source z,phase,time,orientation,channel,y,x -> canonical time,channel,orientation,phase,z,y,x.
    axes = ("z", "phase", "time", "orientation", "channel", "y", "x")
    signal = np.arange(96, dtype=np.float64).reshape(2, 2, 2, 1, 2, 2, 3) / 4 - 9
    canonical = np.transpose(signal, (2, 4, 3, 1, 0, 5, 6)).copy()
    offset = np.arange(96, dtype=np.int16).reshape(canonical.shape) - 15
    response = np.where(np.indices(canonical.shape)[1] == 0, 0.5, 2.0)
    exposure = np.where(np.indices(canonical.shape)[0] == 0, 4.0, 0.25)
    raw_canonical = offset + response * exposure * canonical
    raw_source = np.transpose(raw_canonical, (4, 3, 0, 2, 1, 5, 6))
    raw = acquisition(raw_source, axes=axes)
    example = declared_example()
    result = correct(
        example,
        specimen=raw,
        specimen_offset=offset,
        specimen_response=response,
        specimen_exposure_factor=exposure,
    )
    np.testing.assert_array_equal(result.specimen.data, canonical)
    expected_metadata = record(raw, RAW_FIELDS)
    del expected_metadata["data"]
    same(result.specimen.source_metadata, expected_metadata)


@pytest.mark.parametrize(
    "raw,offset,response,exposure,expected,negative_zero",
    [
        (1.0, 0.0, 2.0**1023, 2.0, 2.0**-1024, False),
        (1.0, 0.0, 2.0**-1022, 2.0**1023, 0.5, False),
        (-float.fromhex("0x0.0000000000001p-1022"), 0.0, 1.0, 2.0, -0.0, True),
        (
            float.fromhex("0x0.0000000000001p-1022"),
            0.0,
            float.fromhex("0x0.0000000000001p-1022"),
            1.0,
            1.0,
            False,
        ),
        (-8.0, -4.0, 2.0, 0.5, -4.0, False),
        (0.0, 0.0, 1.0, float.fromhex("0x0.0000000000001p-1022"), 0.0, False),
        (
            float.fromhex("0x0.0000000000001p-1022"),
            0.0,
            1.0,
            float.fromhex("0x0.0000000000001p-1022"),
            1.0,
            False,
        ),
        (
            -float.fromhex("0x0.0000000000001p-1022"),
            0.0,
            2.0,
            float.fromhex("0x0.0000000000001p-1022"),
            -0.0,
            True,
        ),
    ],
)
def test_sequential_extremes_and_signed_underflow(
    raw: float,
    offset: float,
    response: float,
    exposure: float,
    expected: float,
    negative_zero: bool,
) -> None:
    example = declared_example()
    result = correct(
        example,
        specimen=acquisition(np.full((1, 1, 1, 1), raw)),
        specimen_offset=offset,
        specimen_response=response,
        specimen_exposure_factor=exposure,
    )
    assert result.specimen.data.item() == expected
    assert bool(np.signbit(result.specimen.data.item())) == (expected < 0 or negative_zero)


def test_sequential_rounding_not_product_denominator() -> None:
    # Exact represented numbers; Fraction gives independent correctly rounded stages.
    from fractions import Fraction

    c = float.fromhex("0x1.0000000000001p+0")
    r = float.fromhex("0x1.8000000000000p+0")
    t = float.fromhex("0x1.8000000000000p+0")
    expected = float(Fraction(float(Fraction(c) / Fraction(r))) / Fraction(t))
    example = declared_example()
    result = correct(
        example,
        specimen=acquisition(np.full((1, 1, 1, 1), c)),
        specimen_offset=0,
        specimen_response=r,
        specimen_exposure_factor=t,
    )
    assert result.specimen.data.item() == expected


@pytest.mark.parametrize("flat_spread", [2.0, 1.0, 0.5])
def test_estimated_gauge_independent_of_physical_gain(flat_spread: float) -> None:
    example, estimate, truth = estimate_case(flat_spread=flat_spread)
    result = correct(example, camera_estimate=estimate)
    assert result.status == "corrected" and result.information_codes == ()
    assert result.output_unit == "reference_flat_relative"
    # Independent mean-moment budget propagated through (C-MB)/dM, dM=8.
    # ell=ceil(log2(4))+ceil(log2(3))+8=12; A<=28.
    mean_budget = 256 * 12 * np.finfo(float).eps * 28
    for name in ("specimen", "bead"):
        signal = getattr(example, name + "_signal")
        bound = mean_budget * (1 + 2 * np.max(np.abs(signal))) / (8 - 2 * mean_budget)
        bound += 8 * np.finfo(float).eps * max(1.0, float(np.max(np.abs(signal))))
        np.testing.assert_allclose(getattr(result, name).data, signal, rtol=0, atol=bound)
    if flat_spread <= 1:
        assert result.camera_estimate.gain_counts_per_e is None
        assert "nonpositive_variance_contrast" in result.camera_estimate.information_codes
    else:
        # Propagate the finite variance/mean budgets through dV/dM (20/8).
        assert result.camera_estimate.gain_counts_per_e == pytest.approx(2.5, rel=0, abs=3e-9)
    same(record(result.camera_estimate, CAMERA_FIELDS), record(estimate, CAMERA_FIELDS))
    assert truth["contrast"] == 8


@pytest.mark.parametrize("flat_mean", [12, 8])
def test_nonpositive_contrast_complete_unavailable(flat_mean: int) -> None:
    example, estimate, _ = estimate_case(flat_mean=flat_mean)
    result = correct(example, camera_estimate=estimate)
    assert result.status == "unavailable"
    assert result.information_codes == ("nonpositive_flat_contrast",)
    assert result.specimen is None and result.bead is None
    same(record(result.camera_estimate, CAMERA_FIELDS), record(estimate, CAMERA_FIELDS))


@pytest.mark.parametrize("member", ["specimen", "bead"])
@pytest.mark.parametrize("factor", [0.5, 2.0, float.fromhex("0x1.0000000000001p+0")])
def test_estimated_changed_exposure_unavailable(member: str, factor: float) -> None:
    example, estimate, _ = estimate_case()
    factors = np.ones(getattr(example, member).data.shape)
    factors.flat[-1] = factor
    result = correct(example, camera_estimate=estimate, **{member + "_exposure_factor": factors})
    assert result.status == "unavailable"
    assert result.information_codes == ("estimated_exposure_unavailable",)
    assert result.specimen is None and result.bead is None
    np.testing.assert_array_equal(getattr(result, member + "_exposure_factor"), factors)


def test_all_unavailable_codes_order_and_snapshots() -> None:
    example, estimate, _ = estimate_case(flat_mean=8)
    result = correct(
        example,
        camera_estimate=estimate,
        reference_sum_equalization="per_frame_sum",
        specimen_exposure_factor=2,
    )
    assert result.status == "unavailable"
    assert result.information_codes == (
        "reference_sum_equalization_unavailable",
        "estimated_exposure_unavailable",
        "nonpositive_flat_contrast",
    )
    assert result.specimen is None and result.bead is None
    assert result.mode == "estimated" and result.specimen_exposure_factor == 2.0
    same(record(result.camera_estimate, CAMERA_FIELDS), record(estimate, CAMERA_FIELDS))


def test_phase_dependent_point_sums_not_equalized() -> None:
    images, _, totals = carrier_point()
    example = declared_example()
    raw = acquisition(3 + 4 * images)
    result = correct(
        example, specimen=raw, specimen_offset=3, specimen_response=2, specimen_exposure_factor=2
    )
    # Raw forward rounding plus two exact power-of-two divisions: <=2 eps*max(raw).
    bound = 2 * np.finfo(float).eps * float(np.max(np.abs(raw.data)))
    np.testing.assert_allclose(result.specimen.data.sum(axis=(-2, -1)), totals, rtol=0, atol=bound)
    assert np.ptp(totals) > 1
    unavailable = correct(example, reference_sum_equalization="per_frame_sum")
    assert unavailable.status == "unavailable"
    assert unavailable.information_codes == ("reference_sum_equalization_unavailable",)
    assert unavailable.specimen is None and unavailable.bead is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("mode", "unknown"),
        ("mode", None),
        ("mode", 1),
        ("output_unit", ""),
        ("output_unit", " \t"),
        ("output_unit", None),
        ("output_unit", 1),
        ("gauge_source", ""),
        ("gauge_source", "\n"),
        ("gauge_source", None),
        ("gauge_source", 1),
        ("reference_sum_equalization", "unknown"),
        ("reference_sum_equalization", None),
        ("camera_estimate", object()),
    ],
)
def test_invalid_selectors_strings_declared_union(key: str, value: Any) -> None:
    with error("invalid_alignment_camera"):
        correct(declared_example(), **{key: value})


@pytest.mark.parametrize(
    "key", ["specimen_offset", "specimen_response", "bead_offset", "bead_response"]
)
def test_declared_coefficients_required(key: str) -> None:
    with error("invalid_alignment_camera"):
        correct(declared_example(), **{key: None})


@pytest.mark.parametrize(
    "key", ["specimen_offset", "specimen_response", "bead_offset", "bead_response"]
)
def test_estimated_rejects_supplied_coefficients(key: str) -> None:
    example, estimate, _ = estimate_case()
    with error("invalid_alignment_camera"):
        correct(example, camera_estimate=estimate, **{key: 1})


@pytest.mark.parametrize("estimate", [None, object(), {"contrast_counts": 8.0}])
def test_estimated_requires_real_estimate(estimate: Any) -> None:
    example, _, _ = estimated_example()
    with error("invalid_alignment_camera"):
        correct(example, camera_estimate=estimate)


@pytest.mark.parametrize(
    "unit", ["photons", "reference_flat_relative ", " reference_flat_relative"]
)
def test_estimated_unit_exact(unit: str) -> None:
    example, estimate, _ = estimate_case()
    with error("invalid_alignment_camera"):
        correct(example, camera_estimate=estimate, output_unit=unit)


@pytest.mark.parametrize("member", ["specimen", "bead"])
@pytest.mark.parametrize("wrong", [None, object(), "swapped", "psf", "linear", "pair", "frames"])
def test_wrong_acquisition_kinds_and_double_correction(member: str, wrong: Any) -> None:
    example = declared_example()
    value = wrong
    if wrong == "swapped":
        value = example.bead if member == "specimen" else example.specimen
    elif wrong == "psf":
        value = acquisition(np.ones((1, 2)), "detection_psf", axes=("y", "x"))
    elif wrong == "linear":
        value = sr.correct_linear_response(
            getattr(example, member), offset=0, response=1, output_unit="signal"
        )
    elif wrong in ("pair", "frames"):
        previous = correct(example)
        value = previous if wrong == "pair" else getattr(previous, member)
    with error("invalid_alignment_camera"):
        correct(example, **{member: value})


@pytest.mark.parametrize("member", ["specimen", "bead"])
@pytest.mark.parametrize(
    "mode,unit",
    [
        ("declared", None),
        ("estimated", None),
        ("estimated", "different count"),
        ("estimated", "detector count "),
        ("estimated", " "),
    ],
)
def test_input_count_unit_mismatch_or_unknown_rejected(
    mode: str, member: str, unit: str | None
) -> None:
    example = declared_example()
    estimate: Any = None
    if mode == "estimated":
        example, estimate, _ = estimate_case()
    raw = getattr(example, member)
    replacement = acquisition(raw.data, raw.acquisition_kind, unit=unit)
    with error("invalid_alignment_camera"):
        correct(example, camera_estimate=estimate, **{member: replacement})


@pytest.mark.parametrize("unit", ["", False, 1, [], {}])
def test_input_unit_malformed_rejected_at_raw_declaration(unit: Any) -> None:
    # These cannot be resolved labels on a valid public RawAcquisition. Exercise
    # its real producer instead of inventing a manually corrupted adapter input.
    with error("invalid_acquisition_config"):
        acquisition(np.ones((1, 1, 1, 1)), unit=unit)


@pytest.mark.parametrize("estimated", [False, True])
def test_both_unknown_units_rejected_and_opaque_whitespace_allowed(estimated: bool) -> None:
    example = declared_example()
    estimate: Any = None
    if estimated:
        example, estimate, _ = estimate_case()
    with error("invalid_alignment_camera"):
        correct(
            example,
            camera_estimate=estimate,
            specimen=acquisition(example.specimen.data, unit=None),
            bead=acquisition(example.bead.data, "sim_beads", unit=None),
        )
    specimen = acquisition(example.specimen.data, unit=" \t")
    bead = acquisition(example.bead.data, "sim_beads", unit=" \t")
    result = correct(example, camera_estimate=estimate, specimen=specimen, bead=bead)
    assert result.status == "corrected" and result.information_codes == ()
    for name, raw in (("specimen", specimen), ("bead", bead)):
        frame = getattr(result, name)
        assert frame.input_unit == " \t"
        assert frame.provenance["linear_response"]["input_unit"] == " \t"
        same(frame.source_metadata, record(raw, RAW_FIELDS[1:]))


@pytest.mark.parametrize("maps", [False, True])
@pytest.mark.parametrize(
    "specimen_unit,bead_unit",
    [
        ("detector count", "different count"),
        ("detector count", "detector count "),
        (" \t", "opaque bead label"),
    ],
)
def test_declared_distinct_input_units_common_output(
    maps: bool, specimen_unit: str, bead_unit: str
) -> None:
    # C_j[U_j] = O_j[U_j] + r_j[U_j/Ucommon] * t_j * X_j[Ucommon].
    # The frozen dyadic controls provide distinct responses and exact truth;
    # relabeling a member changes no represented coefficient or inverse stage.
    example = declared_example(maps=maps)
    specimen = acquisition(example.specimen.data, unit=specimen_unit)
    bead = acquisition(example.bead.data, "sim_beads", unit=bead_unit)
    result = correct(example, specimen=specimen, bead=bead)
    assert result.status == "corrected" and result.information_codes == ()
    assert result.output_unit == example.arguments["output_unit"]
    for name, raw in (("specimen", specimen), ("bead", bead)):
        frame = getattr(result, name)
        np.testing.assert_array_equal(frame.data, getattr(example, name + "_signal"))
        assert frame.input_unit == raw.intensity_unit
        assert frame.output_unit == example.arguments["output_unit"]
        assert frame.provenance["linear_response"]["input_unit"] == raw.intensity_unit
        assert frame.provenance["linear_response"]["output_unit"] == frame.output_unit
        same(frame.source_metadata, record(raw, RAW_FIELDS[1:]))


@pytest.mark.parametrize("estimated", [False, True])
@pytest.mark.parametrize(
    "sid,bid",
    [
        ("one", "two"),
        ("one", "one "),
        (None, "one"),
        ("one", None),
        (None, None),
        ("one", "one"),
        (" \t", " \t"),
        (" \t", "one"),
    ],
)
def test_calibration_ids_unknown_or_conflicting(
    sid: str | None, bid: str | None, estimated: bool
) -> None:
    example = declared_example()
    estimate: Any = None
    if estimated:
        example, estimate, _ = estimate_case()
    changes = {
        "specimen": acquisition(example.specimen.data, calibration_id=sid),
        "bead": acquisition(example.bead.data, "sim_beads", calibration_id=bid),
    }
    result = correct(example, camera_estimate=estimate, **changes)
    assert result.status == "corrected" and result.information_codes == ()
    assert result.specimen.source_metadata["calibration_id"] == sid
    assert result.bead.source_metadata["calibration_id"] == bid
    for name, raw in changes.items():
        same(getattr(result, name).source_metadata, record(raw, RAW_FIELDS[1:]))


class ArraySubclass(np.ndarray):
    """Unsupported caller representation, with no custom decisions."""


BAD_FORMS = [
    True,
    np.float64(1),
    np.int64(1),
    [1],
    (1,),
    object(),
    1 + 0j,
    np.array(1),
    np.array([1.0]).view(ArraySubclass),
    np.ma.array([1.0]),
]
BAD_DTYPES = [
    "bool",
    "complex128",
    "object",
    "U1",
    "S1",
    "datetime64[D]",
    "timedelta64[D]",
    [("v", "f8")],
]


@pytest.mark.parametrize("value", BAD_FORMS)
@pytest.mark.parametrize("member", ["specimen", "bead"])
def test_exposure_unsupported_forms(member: str, value: Any) -> None:
    with error("invalid_alignment_exposure"):
        correct(declared_example(), **{member + "_exposure_factor": value})


@pytest.mark.parametrize("dtype", BAD_DTYPES)
def test_exposure_unsupported_dtypes(dtype: Any) -> None:
    example = declared_example()
    value = np.ones(example.specimen.data.shape, dtype=dtype)
    with error("invalid_alignment_exposure"):
        correct(example, specimen_exposure_factor=value)


@pytest.mark.parametrize("shape", [(2, 3), (1, 1, 1, 1), (3, 2, 2, 3)])
@pytest.mark.parametrize(
    "key", ["specimen_exposure_factor", "specimen_offset", "specimen_response"]
)
def test_no_broadcast_or_coordinate_inference(key: str, shape: tuple[int, ...]) -> None:
    code = (
        "invalid_alignment_exposure" if key.endswith("factor") else "invalid_linear_response_shape"
    )
    with error(code):
        correct(declared_example(), **{key: np.ones(shape)})


@pytest.mark.parametrize(
    "value", [0, -0.0, -1.0, float("nan"), float("inf"), -float("inf"), 10**400]
)
@pytest.mark.parametrize("array", [False, True])
def test_exposure_invalid_values(value: Any, array: bool) -> None:
    example = declared_example()
    factor = np.full(example.specimen.data.shape, value) if array else value
    with error("invalid_alignment_exposure"):
        correct(example, specimen_exposure_factor=factor)


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize("value", BAD_FORMS + [float("nan"), float("inf"), 10**400])
def test_primitive_coefficient_domain_codes(field: str, value: Any) -> None:
    example = declared_example()
    # Isolate unsupported representation from shape: simultaneous-error precedence
    # is unspecified, so subclass/masked examples use the correct full shape.
    if isinstance(value, np.ma.MaskedArray):
        value = np.ma.array(np.ones(example.specimen.data.shape))
    elif isinstance(value, ArraySubclass):
        value = np.ones(example.specimen.data.shape).view(ArraySubclass)
    code = (
        "invalid_linear_response_shape"
        if isinstance(value, np.ndarray) and type(value) is np.ndarray
        else "invalid_linear_response_" + field
    )
    if isinstance(value, np.ndarray) and value.dtype.kind not in "iuf":
        code = "invalid_linear_response_" + field
    with error(code):
        correct(example, **{"specimen_" + field: value})


@pytest.mark.parametrize("dtype", BAD_DTYPES)
@pytest.mark.parametrize("field", ["offset", "response"])
def test_primitive_coefficient_dtype_codes(dtype: Any, field: str) -> None:
    example = declared_example()
    with error("invalid_linear_response_" + field):
        correct(example, **{"bead_" + field: np.ones(example.bead.data.shape, dtype=dtype)})


@pytest.mark.parametrize("response", [0, -0.0, -1])
def test_nonpositive_declared_response_invalid(response: float) -> None:
    with error("invalid_linear_response_response"):
        correct(declared_example(), bead_response=response)


@pytest.mark.parametrize("pixel", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("unavailable", [False, True])
def test_nonfinite_raw_is_domain_error_even_when_unavailable(
    pixel: float, unavailable: bool
) -> None:
    example = declared_example()
    raw = acquisition(np.full((1, 1, 1, 1), pixel), "sim_beads")
    with error("invalid_linear_response_data"):
        correct(
            example,
            bead=raw,
            reference_sum_equalization="per_frame_sum" if unavailable else "disabled",
        )


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("bead_response", 0, "invalid_linear_response_response"),
        ("specimen_offset", float("nan"), "invalid_linear_response_offset"),
        ("specimen_exposure_factor", 0, "invalid_alignment_exposure"),
    ],
)
def test_unavailable_still_validates_domains(field: str, value: Any, code: str) -> None:
    with error(code):
        correct(declared_example(), reference_sum_equalization="per_frame_sum", **{field: value})


@pytest.mark.parametrize("stage", ["subtract", "linear_divide", "exposure_divide"])
@pytest.mark.parametrize("member", ["specimen", "bead"])
def test_range_stages_and_unavailable_does_not_execute_arithmetic(stage: str, member: str) -> None:
    example = declared_example()
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    offset = -maximum if stage == "subtract" else 0
    response = 0.5 if stage == "linear_divide" else 2 if stage == "subtract" else 1
    exposure = 0.5 if stage == "exposure_divide" else 2
    changes = {
        member: acquisition(
            np.full((1, 1, 1, 1), maximum), "specimen_sim" if member == "specimen" else "sim_beads"
        ),
        member + "_offset": offset,
        member + "_response": response,
        member + "_exposure_factor": exposure,
    }
    code = "alignment_camera_range" if stage == "exposure_divide" else "linear_response_range"
    with error(code):
        correct(example, **changes)
    result = correct(example, reference_sum_equalization="per_frame_sum", **changes)
    assert result.status == "unavailable" and result.specimen is None and result.bead is None


def test_estimated_unavailable_does_not_execute_linear_range() -> None:
    example, estimate, _ = estimate_case(flat_mean=12)
    maximum = float.fromhex("0x1.fffffffffffffp+1023")
    raw = acquisition(np.full((1, 1, 1, 1), -maximum))
    result = correct(example, camera_estimate=estimate, specimen=raw)
    assert result.status == "unavailable" and result.specimen is None and result.bead is None


def test_original_to_float64_conversion_domains_and_rounding() -> None:
    example = declared_example()
    raw = acquisition(np.array([2**53 + 1, 2**53 + 3], dtype=">i8").reshape(1, 1, 1, 2))
    result = correct(
        example, specimen=raw, specimen_offset=0, specimen_response=1, specimen_exposure_factor=1
    )
    np.testing.assert_array_equal(result.specimen.data.ravel(), [float(2**53), float(2**53 + 4)])
    if np.finfo(np.longdouble).maxexp > np.finfo(float).maxexp:
        huge = np.full((1, 1, 1, 1), np.longdouble(2) ** 1024, dtype=np.longdouble)
        with error("invalid_linear_response_data"):
            correct(example, specimen=acquisition(huge))
        with error("invalid_alignment_exposure"):
            correct(
                example,
                specimen_exposure_factor=np.full(
                    example.specimen.data.shape, huge.item(), dtype=np.longdouble
                ),
            )
        tiny = np.longdouble(2) ** -1075
        with error("invalid_alignment_exposure"):
            correct(
                example,
                specimen_exposure_factor=np.full(
                    example.specimen.data.shape, tiny, dtype=np.longdouble
                ),
            )


@pytest.mark.parametrize("estimated", [False, True])
def test_exact_provenance_and_independent_storage(estimated: bool) -> None:
    example = declared_example(maps=True)
    estimate: Any = None
    if estimated:
        example, estimate, _ = estimate_case(flat_spread=0.5)
    inputs = {
        "specimen": record(example.specimen, RAW_FIELDS),
        "bead": record(example.bead, RAW_FIELDS),
        "arguments": example.arguments,
        "estimate": None if estimate is None else record(estimate, CAMERA_FIELDS),
    }
    before = copy.deepcopy(inputs)
    result = correct(example, camera_estimate=estimate)
    another = correct(example, camera_estimate=estimate)
    same(inputs, before)
    for name in ("specimen", "bead"):
        raw = getattr(example, name)
        frame = getattr(result, name)
        factor = example.arguments[name + "_exposure_factor"]
        normalized = getattr(result, name + "_exposure_factor")
        if isinstance(factor, np.ndarray):
            assert type(normalized) is np.ndarray
            assert normalized.dtype == np.dtype("float64") and normalized.flags.c_contiguous
            np.testing.assert_array_equal(normalized, factor)
        else:
            assert type(normalized) in (float, np.float64)
            assert normalized == float(factor)
        offset = (
            float(estimate.means_counts[1])
            if estimate is not None
            else example.arguments[name + "_offset"]
        )
        response = (
            estimate.contrast_counts
            if estimate is not None
            else example.arguments[name + "_response"]
        )
        linear = sr.correct_linear_response(
            raw, offset=offset, response=response, output_unit=result.output_unit
        )
        provenance = frame.provenance
        assert set(provenance) == {
            "model",
            "equation",
            "gauge_source",
            "coefficient_origin",
            "camera_source",
            "linear_response",
            "operations",
            "exposure_factor",
        }
        assert provenance["model"] == "alignment_camera_v1"
        assert provenance["equation"] == "raw=offset+response*exposure_factor*signal"
        assert provenance["gauge_source"] == example.arguments["gauge_source"]
        assert provenance["coefficient_origin"] == example.arguments["mode"]
        assert provenance["camera_source"] == (estimate.source if estimate is not None else None)
        assert provenance["operations"] == ("subtract_offset", "divide_response", "divide_exposure")
        assert set(provenance["exposure_factor"]) == {"supplied", "applied"}
        same(provenance["exposure_factor"]["supplied"], factor)
        applied_factor = provenance["exposure_factor"]["applied"]
        if isinstance(normalized, np.ndarray):
            same(applied_factor, normalized)
        else:
            assert type(applied_factor) in (float, np.float64)
            assert applied_factor == normalized
        same(provenance["linear_response"], linear.provenance)
        same(frame.source_metadata, linear.source_metadata)
        assert provenance["linear_response"]["equation"] == "raw=offset+response*signal"
    independent(inputs, pair_tree(result), pair_tree(another))
    with pytest.raises(AttributeError):
        result.status = "changed"
    with pytest.raises(AttributeError):
        result.specimen.data = np.zeros(1)
    result.specimen.data.fill(99)
    result.specimen.source_metadata["original_metadata"]["opaque"].append("mutated")
    result.specimen.provenance["exposure_factor"]["applied"] = 99
    if estimated:
        result.camera_estimate.variances_counts2.fill(-99)
    same(inputs, before)
    np.testing.assert_array_equal(
        another.specimen.data, correct(example, camera_estimate=estimate).specimen.data
    )


def test_unavailable_snapshot_ownership() -> None:
    example, estimate, _ = estimate_case(flat_mean=8)
    before = copy.deepcopy(record(estimate, CAMERA_FIELDS))
    result = correct(example, camera_estimate=estimate, reference_sum_equalization="per_frame_sum")
    another = correct(example, camera_estimate=estimate, reference_sum_equalization="per_frame_sum")
    independent(
        record(estimate, CAMERA_FIELDS), example.arguments, pair_tree(result), pair_tree(another)
    )
    result.camera_estimate.frame_means_counts[0].fill(99)
    result.bead_exposure_factor.fill(7)
    same(record(estimate, CAMERA_FIELDS), before)
    assert np.all(example.arguments["bead_exposure_factor"] == 1)
    same(record(another.camera_estimate, CAMERA_FIELDS), before)


@pytest.mark.parametrize("outcome", ["corrected", "unavailable", "domain", "range", "underflow"])
def test_inputs_error_modes_and_warning_filters_preserved(outcome: str) -> None:
    example = declared_example(maps=True)
    changes: dict[str, Any] = {}
    expected_code = None
    if outcome == "unavailable":
        changes["reference_sum_equalization"] = "per_frame_sum"
    elif outcome == "domain":
        changes["specimen_exposure_factor"] = 0
        expected_code = "invalid_alignment_exposure"
    elif outcome in ("range", "underflow"):
        raw_value = (
            np.finfo(float).max if outcome == "range" else -float.fromhex("0x0.0000000000001p-1022")
        )
        changes = {
            "specimen": acquisition(np.full((1, 1, 1, 1), raw_value)),
            "specimen_offset": 0,
            "specimen_response": 1,
            "specimen_exposure_factor": 0.5 if outcome == "range" else 2,
        }
        expected_code = "alignment_camera_range" if outcome == "range" else None
    inputs = {
        "specimen": record(example.specimen, RAW_FIELDS),
        "bead": record(example.bead, RAW_FIELDS),
        "arguments": example.arguments,
        "changes": changes,
    }
    before = copy.deepcopy(inputs)
    with warnings.catch_warnings(record=True) as caught, np.errstate(all="raise"):
        warnings.simplefilter("always")
        filters = list(warnings.filters)
        modes, callback = np.geterr().copy(), np.geterrcall()
        if expected_code:
            with error(expected_code):
                correct(example, **changes)
        else:
            correct(example, **changes)
        assert np.geterr() == modes and np.geterrcall() is callback
        assert warnings.filters == filters
        assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
        warnings.warn("caller unrelated warning", UserWarning, stacklevel=1)
        assert caught[-1].category is UserWarning
    same(inputs, before)


@pytest.mark.parametrize("point", [False, True])
@pytest.mark.parametrize("scale", [0.25, 1.0, 2.0])
def test_signed_constant_and_point_fixed_reconstruction(point: bool, scale: float) -> None:
    example, args, expected_spectrum, expected_image = reconstruction_control(
        point=point, scale=scale
    )
    corrected = correct(example)
    result = sr.reconstruct(corrected.specimen.data, **args)
    # Approved coordinate budget, with R=1,N=4,a=1; then modulus <=sqrt(2)*budget.
    ny, nx = example.specimen_signal.shape[-2:]
    budget = (
        8192
        * 4
        * (4 * ny * nx)
        * np.finfo(float).eps
        * float(np.max(np.abs(example.specimen_signal)))
    )
    # Raw affine rounding adds <=2 eps*max(raw)/4 per input; <=64 amplification
    # covers the well-conditioned four-phase fit, unit transfer and lambda=1/8.
    budget += 64 * np.finfo(float).eps * float(np.max(np.abs(example.specimen.data)))
    tolerance = np.sqrt(2.0) * budget
    np.testing.assert_allclose(result.spectrum, expected_spectrum, rtol=0, atol=tolerance)
    np.testing.assert_allclose(result.image, expected_image, rtol=0, atol=tolerance)
    assert result.pixel_size_um == (0.5, 0.5)
    if point:
        # Same 3*5 µm² field: integral = amplitude * input pixel area * 9/10.
        assert (result.image.sum() * 0.25) == pytest.approx(
            2 * scale * 0.9, rel=0, abs=15 * tolerance
        )
        assert result.spectrum[ny, nx] == pytest.approx(2 * scale * 0.9 / 15, rel=0, abs=tolerance)
    else:
        assert np.max(result.image.real) < 0


# Independent existing-interface controls must remain runnable before adapter addition.
@pytest.mark.parametrize("maps", [False, True])
def test_existing_linear_interface_control(maps: bool) -> None:
    example = declared_example(maps=maps)
    for name in ("specimen", "bead"):
        result = sr.correct_linear_response(
            getattr(example, name),
            offset=example.arguments[name + "_offset"],
            response=example.arguments[name + "_response"],
            output_unit="explicit intermediate",
        )
        expected = getattr(example, name + "_signal") * example.arguments[name + "_exposure_factor"]
        np.testing.assert_array_equal(result.data, expected)


@pytest.mark.parametrize(
    "flat_mean,flat_spread", [(20, 2.0), (20, 1.0), (20, 0.5), (12, 2.0), (8, 0.5)]
)
def test_existing_scalar_finite_moment_control(flat_mean: int, flat_spread: float) -> None:
    _, estimate, truth = estimate_case(flat_mean=flat_mean, flat_spread=flat_spread)
    # Public finite-moment bounds: K=4,T=3,ell=12,A<=28.
    mean_budget = 256 * 12 * np.finfo(float).eps * 28
    variance_budget = 4096 * 12 * np.finfo(float).eps * 28**2
    for field, expected, tolerance in (
        ("means_counts", truth["means"], mean_budget),
        ("variances_counts2", truth["variances"], variance_budget),
    ):
        np.testing.assert_allclose(getattr(estimate, field), expected, rtol=0, atol=tolerance)
    for group in range(3):
        np.testing.assert_allclose(
            estimate.frame_means_counts[group],
            truth["frame_means"][group],
            rtol=0,
            atol=mean_budget,
        )
        np.testing.assert_allclose(
            estimate.frame_variances_counts2[group],
            truth["frame_variances"][group],
            rtol=0,
            atol=variance_budget,
        )
        # Repeatability is relational in returned means; their accuracy is
        # independently checked above against source moments, not this target.
        with localcontext() as context:
            context.prec = 90
            frame_means = [
                Decimal.from_float(float(value)) for value in estimate.frame_means_counts[group]
            ]
            group_mean = Decimal.from_float(float(estimate.means_counts[group]))
            count = len(frame_means)
            squared = sum(((value - group_mean) ** 2 for value in frame_means), Decimal(0))
            target = (squared / Decimal(count * (count - 1))).sqrt()
            reported = Decimal.from_float(float(estimate.empirical_mean_se_counts[group]))
            assert reported.is_finite() and reported >= 0
            assert abs(reported - target) <= Decimal.from_float(mean_budget)
    assert estimate.contrast_counts == pytest.approx(truth["contrast"], rel=0, abs=2 * mean_budget)


@pytest.mark.parametrize("point", [False, True])
def test_existing_fixed_reconstruction_control(point: bool) -> None:
    example, args, spectrum, image = reconstruction_control(point=point)
    assert (
        (
            example.specimen.sampling_um["y"],
            example.specimen.sampling_um["x"],
        )
        == args["otf"].pixel_size_um
        == (1.0, 1.0)
    )
    result = sr.reconstruct(example.specimen_signal, **args)
    assert result.pixel_size_um == (0.5, 0.5)
    ny, nx = example.specimen_signal.shape[-2:]
    budget = (
        np.sqrt(2.0)
        * 8192
        * 4
        * (4 * ny * nx)
        * np.finfo(float).eps
        * float(np.max(np.abs(example.specimen_signal)))
    )
    np.testing.assert_allclose(result.spectrum, spectrum, rtol=0, atol=budget)
    np.testing.assert_allclose(result.image, image, rtol=0, atol=budget)


def test_independent_point_total_control() -> None:
    images, _, totals = carrier_point()
    np.testing.assert_allclose(
        images.sum(axis=(-2, -1)), totals, rtol=0, atol=16 * np.finfo(float).eps
    )
    assert np.ptp(totals) > 1


@pytest.mark.parametrize("dtype", ["i2", "u1", ">f4", ">f8"])
def test_exposure_storage_normalization_without_caller_mutation(dtype: str) -> None:
    example = declared_example()
    # Slice an extra trailing coordinate: full canonical shape, noncontiguous storage.
    backing = np.empty(example.specimen.data.shape + (2,), dtype=dtype)
    factors = backing[..., 0]
    factors[...] = 2
    factors.flags.writeable = False
    before = factors.tobytes()
    result = correct(example, specimen_exposure_factor=factors)
    np.testing.assert_array_equal(result.specimen.data, example.specimen_signal)
    normalized = result.specimen_exposure_factor
    assert type(normalized) is np.ndarray
    assert normalized.dtype == np.dtype("float64")
    assert normalized.flags.c_contiguous and normalized.flags.owndata
    assert not np.shares_memory(normalized, factors)
    assert factors.tobytes() == before and not factors.flags.writeable
    provenance = result.specimen.provenance["exposure_factor"]
    same(provenance["supplied"], factors)
    same(provenance["applied"], normalized)


def test_shared_caller_maps_are_independently_snapshotted() -> None:
    example = declared_example()
    shared = np.ones((1, 1, 1, 2))
    raw = np.array([[[[-1.0, 3.0]]]])
    changes: dict[str, Any] = {"specimen": acquisition(raw), "bead": acquisition(raw, "sim_beads")}
    for member in ("specimen", "bead"):
        for coefficient in ("offset", "response", "exposure_factor"):
            changes[member + "_" + coefficient] = shared
    result = correct(example, **changes)
    independent(pair_tree(result))
    for node in mutable_nodes(pair_tree(result)):
        if isinstance(node, np.ndarray):
            assert not np.shares_memory(node, shared)
    shared.fill(99)
    np.testing.assert_array_equal(result.specimen.data, raw - 1)
    np.testing.assert_array_equal(result.bead.data, raw - 1)


def test_estimated_negative_background_and_noise_statistics_retained() -> None:
    example, estimate, _ = estimate_case(dark_mean=16, flat_spread=0.5)
    assert estimate.means_counts[1] - estimate.means_counts[0] < 0
    assert estimate.variances_counts2[2] - estimate.variances_counts2[1] < 0
    result = correct(example, camera_estimate=estimate)
    assert result.status == "corrected" and result.information_codes == ()
    assert result.camera_estimate.information_codes == (
        "nonpositive_variance_contrast",
        "negative_background_estimate",
    )
    same(record(result.camera_estimate, CAMERA_FIELDS), record(estimate, CAMERA_FIELDS))
    assert result.camera_estimate.variances_counts2[1] > 6
    assert np.all(result.camera_estimate.empirical_mean_se_counts > 1)
    assert result.output_unit == "reference_flat_relative"
    assert result.specimen.provenance["linear_response"]["offset"]["applied"] == 12


def test_declared_rejects_real_estimator_record_union() -> None:
    _, estimate, _ = estimate_case()
    with error("invalid_alignment_camera"):
        correct(declared_example(), camera_estimate=estimate)


@pytest.mark.parametrize("value", [None, False, np.array([[[[0.0]]]])])
def test_estimated_unavailable_still_validates_exposure_domain(value: Any) -> None:
    example, estimate, _ = estimate_case(flat_mean=8)
    with error("invalid_alignment_exposure"):
        correct(example, camera_estimate=estimate, specimen_exposure_factor=value)


@pytest.mark.parametrize("outcome", ["corrected", "unavailable", "rejected"])
def test_estimated_inputs_and_caller_policy_preserved(outcome: str) -> None:
    example, estimate, _ = estimate_case(flat_spread=0.5)
    inputs = {
        "specimen": record(example.specimen, RAW_FIELDS),
        "bead": record(example.bead, RAW_FIELDS),
        "arguments": example.arguments,
        "estimate": record(estimate, CAMERA_FIELDS),
    }
    before = copy.deepcopy(inputs)
    factor = 1 if outcome == "corrected" else 2 if outcome == "unavailable" else 0
    with np.errstate(all="raise"), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        modes = np.geterr().copy()
        filters = list(warnings.filters)
        if outcome == "rejected":
            with error("invalid_alignment_exposure"):
                correct(example, camera_estimate=estimate, specimen_exposure_factor=factor)
        else:
            result = correct(example, camera_estimate=estimate, specimen_exposure_factor=factor)
            assert result.status == outcome
        assert np.geterr() == modes and warnings.filters == filters
        assert not caught
    same(inputs, before)


def test_sequential_rounding_fixture_is_distinguishing() -> None:
    """Prove the chosen non-dyadic division control differs by one binary64 ULP."""
    from fractions import Fraction

    c = Fraction(float.fromhex("0x1.0000000000001p+0"))
    r = Fraction(3, 2)
    sequential = float(Fraction(float(c / r)) / r)
    combined = float(c / (r * r))
    assert sequential != combined
    assert abs(sequential - combined) == np.spacing(combined)


@pytest.mark.parametrize("member", ["specimen", "bead"])
def test_identity_correction_is_explicit_not_inferred(member: str) -> None:
    example = declared_example()
    raw = getattr(example, member)
    result = correct(
        example, **{member + "_offset": 0, member + "_response": 1, member + "_exposure_factor": 1}
    )
    np.testing.assert_array_equal(getattr(result, member).data, raw.data.astype(np.float64))
    assert getattr(result, member).provenance["exposure_factor"]["supplied"] == 1


@pytest.mark.parametrize("field", ["offset", "response"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_full_shape_coefficients_rejected(field: str, value: float) -> None:
    example = declared_example()
    coefficient = np.ones(example.bead.data.shape)
    coefficient.flat[-1] = value
    with error("invalid_linear_response_" + field):
        correct(example, **{"bead_" + field: coefficient})


@pytest.mark.parametrize("mode", ["call", "log", "print", "warn", "ignore"])
@pytest.mark.parametrize("outcome", ["corrected", "unavailable", "range", "underflow"])
def test_nondefault_numpy_modes_and_callback_preserved(
    mode: Literal["call", "log", "print", "warn", "ignore"], outcome: str
) -> None:
    class ArithmeticObserver:
        def __init__(self) -> None:
            self.events: list[Any] = []

        def __call__(self, *args: Any) -> None:
            self.events.append(args)

        def write(self, message: str) -> None:
            self.events.append(message)

    example = declared_example()
    observer = ArithmeticObserver()
    changes: dict[str, Any] = {}
    if outcome == "unavailable":
        changes["reference_sum_equalization"] = "per_frame_sum"
    elif outcome in ("range", "underflow"):
        pixel = (
            float.fromhex("0x1.fffffffffffffp+1023")
            if outcome == "range"
            else -float.fromhex("0x0.0000000000001p-1022")
        )
        changes = {
            "specimen": acquisition(np.full((1, 1, 1, 1), pixel)),
            "specimen_offset": 0,
            "specimen_response": 1,
            "specimen_exposure_factor": 0.5 if outcome == "range" else 2,
        }
    previous_callback = np.geterrcall()
    try:
        np.seterrcall(observer)
        with np.errstate(all=mode), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            modes = np.geterr().copy()
            if outcome == "range":
                with error("alignment_camera_range"):
                    correct(example, **changes)
            else:
                correct(example, **changes)
            assert np.geterr() == modes and np.geterrcall() is observer
            assert not observer.events
            assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
    finally:
        np.seterrcall(previous_callback)


@pytest.mark.parametrize("reason", ["contrast", "exposure"])
def test_estimated_unavailable_validates_raw_pixels(reason: str) -> None:
    example, estimate, _ = estimate_case(flat_mean=8 if reason == "contrast" else 20)
    raw = acquisition(np.full((1, 1, 1, 1), float("nan")))
    with error("invalid_linear_response_data"):
        correct(
            example,
            camera_estimate=estimate,
            specimen=raw,
            specimen_exposure_factor=1 if reason == "contrast" else 2,
        )
