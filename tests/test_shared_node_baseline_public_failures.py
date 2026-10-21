"""Supplemental public preservation; fresh B must assess this checkpoint."""

import base64
import hashlib
import json
import math
import os
import warnings
import xml.etree.ElementTree as ET
from typing import cast

import numpy as np
import pytest
import tifffile

from shared_node_baseline_public_failures_fixture import (
    illumination_case,
    illumination_expected_gain,
    observe_operation_time_shortening,
    translation_scores,
    write_priism,
)
from simrecon import (
    IlluminationEstimate,
    SimreconError,
    estimate_illumination,
    estimate_translation,
    export_imagej,
    harmonize,
    inspect,
    read,
    scan_carriers,
)


class OrdinaryFloat(float):
    """Accept a float subclass with inherited numeric protocols."""


class ConvertingFloat(float):
    """Record an ordinary float conversion and supply its caller-owned value."""

    converted: float
    events: list[str]

    def __new__(cls, source, converted):
        result = super().__new__(cls, source)
        result.converted = converted
        result.events = []
        return result

    def __float__(self):
        """Return the supplied built-in float without a dependency seam."""
        self.events.append("float")
        return self.converted


class OrdinaryInteger(int):
    """Accept an integer subclass with inherited numeric protocols."""


class RaisingInteger(int):
    """Raise a caller-owned exception from ordinary integer conversion."""

    error: SimreconError
    events: list[str]

    def __new__(cls, value, error):
        result = super().__new__(cls, value)
        result.error = error
        result.events = []
        return result

    def __int__(self):
        """Record actual invocation before raising the same exception."""
        self.events.append("int")
        raise self.error


class OrdinaryLabel(str):
    """Accept a string subclass with inherited string protocols."""


class RaisingLabel(str):
    """Raise a caller-owned exception from an ordinary string operation."""

    error: SimreconError
    events: list[str]

    def __new__(cls, value, error):
        result = super().__new__(cls, value)
        result.error = error
        result.events = []
        return result

    def strip(self, *args, **kwargs):
        self.events.append("strip")
        raise self.error


@pytest.fixture
def caller_state():
    """Check preservation of caller arithmetic and warning settings."""
    mode = np.geterr()
    filters = warnings.filters[:]
    yield
    assert np.geterr() == mode
    assert warnings.filters == filters


def snapshot_arrays(arrays):
    return [(array.dtype, array.shape, array.strides, array.tobytes()) for array in arrays]


def assert_translation(result, moving, reference, tolerance):
    expected = translation_scores(moving, reference)
    delta = 4096 * moving.size * 2**-52
    assert np.max(np.abs(result.normalized_rms - expected)) <= delta
    ny, nx = moving.shape
    minimum = float(result.normalized_rms.min())
    candidates = tuple(
        (dy, dx)
        for iy, dy in enumerate(range(-(ny // 2), (ny + 1) // 2))
        for ix, dx in enumerate(range(-(nx // 2), (nx + 1) // 2))
        if float(result.normalized_rms[iy, ix]) - minimum <= tolerance
    )
    assert result.minimum_normalized_rms == minimum
    assert result.candidate_displacements_pixels_yx == candidates
    assert result.displacement_pixels_yx == (candidates[0] if len(candidates) == 1 else None)
    assert result.failure_code == (None if len(candidates) == 1 else "ambiguous_translation")


@pytest.mark.parametrize("tolerance", [0.0, -0.0, 0.125, 2.0])
def test_ordinary_float_subclass_translation_positive(tolerance, caller_state):
    reference = np.array([[0.0, 1.0, 3.0], [2.0, 7.0, 4.0]])
    moving = np.roll(reference, (1, -1), axis=(0, 1))
    saved = snapshot_arrays([moving, reference])
    result = estimate_translation(
        moving, reference=reference, ambiguity_tolerance=OrdinaryFloat(tolerance)
    )
    assert_translation(result, moving, reference, tolerance)
    assert snapshot_arrays([moving, reference]) == saved


@pytest.mark.parametrize("converted", [float("nan"), float("inf"), -1.0])
def test_used_float_conversion_must_remain_finite_nonnegative(
    converted, caller_state, record_property
):
    reference = np.array([[0.0, 1.0, 3.0], [2.0, 7.0, 4.0]])
    moving = np.roll(reference, (1, -1), axis=(0, 1))
    saved = snapshot_arrays([moving, reference])
    tolerance = ConvertingFloat(0.125, converted)
    caught = None
    result = None
    try:
        result = estimate_translation(moving, reference=reference, ambiguity_tolerance=tolerance)
    except SimreconError as error:
        caught = error
    exercised = bool(tolerance.events)
    record_property("float_callback_exercised", exercised)
    if exercised:
        assert caught is not None
        assert caught.code == "invalid_translation_tolerance"
    else:
        # A lawful conversion may use the stored built-in scalar directly.
        assert caught is None
        assert_translation(result, moving, reference, 0.125)
    assert float.__float__(tolerance) == 0.125
    assert tolerance.converted is converted
    assert snapshot_arrays([moving, reference]) == saved


@pytest.mark.parametrize("converted", [0.0, -0.0, 0.125, 2.0])
def test_finite_nonnegative_float_conversion_positive(converted, caller_state, record_property):
    reference = np.array([[0.0, 1.0, 3.0], [2.0, 7.0, 4.0]])
    moving = np.roll(reference, (1, -1), axis=(0, 1))
    saved = snapshot_arrays([moving, reference])
    tolerance = ConvertingFloat(0.125, converted)
    result = estimate_translation(moving, reference=reference, ambiguity_tolerance=tolerance)
    exercised = bool(tolerance.events)
    record_property("positive_float_callback_exercised", exercised)
    assert_translation(result, moving, reference, converted if exercised else 0.125)
    assert float.__float__(tolerance) == 0.125
    assert tolerance.converted is converted
    assert snapshot_arrays([moving, reference]) == saved


@pytest.mark.parametrize("source", [-1.0, -float.fromhex("0x0.0000000000001p-1022")])
def test_negative_source_tolerance_cannot_become_accepted_zero(source, caller_state):
    image = np.array([[3.0]])
    saved = snapshot_arrays([image])
    tolerance = ConvertingFloat(source, -0.0)
    with pytest.raises(SimreconError) as caught:
        estimate_translation(image, reference=image, ambiguity_tolerance=tolerance)
    assert caught.value.code == "invalid_translation_tolerance"
    assert float.__float__(tolerance) == source
    assert snapshot_arrays([image]) == saved


@pytest.mark.parametrize("source", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_source_tolerance_cannot_become_accepted_finite(
    source, caller_state, record_property
):
    image = np.array([[3.0]])
    saved = snapshot_arrays([image])
    tolerance = ConvertingFloat(source, 0.125)
    with pytest.raises(SimreconError) as caught:
        estimate_translation(image, reference=image, ambiguity_tolerance=tolerance)
    assert caught.value.code == "invalid_translation_tolerance"
    record_property("nonfinite_source_float_callback_exercised", bool(tolerance.events))
    stored = float.__float__(tolerance)
    if math.isnan(source):
        assert math.isnan(stored)
    else:
        assert stored == source
    assert tolerance.converted == 0.125
    assert snapshot_arrays([image]) == saved


def assert_illumination(result, source):
    # The four quadrature columns have condition sqrt(2). H=1 and k=0
    # give Dplus/D0=(1+0.5j)/4. All information energies exceed B/8.
    images, steps, _ = illumination_case(source)
    expected_gain = illumination_expected_gain(images, steps)
    assert abs(expected_gain - complex(0.25, 0.125)) <= 64 * 2**-52
    actual_gain = (
        0.5
        * result.modulation
        * complex(math.cos(result.phase_offset_rad), math.sin(result.phase_offset_rad))
    )
    delta = 8192 * 4 * 3 * 2**-52
    assert abs(actual_gain - expected_gain) <= delta
    assert abs(result.relative_residual) <= delta
    assert result.overlap_count == 3
    assert result.source == source
    theta = math.atan2(expected_gain.imag, expected_gain.real)
    expected = np.arctan2(
        np.sin(steps) * math.cos(theta) + np.cos(steps) * math.sin(theta),
        np.cos(steps) * math.cos(theta) - np.sin(steps) * math.sin(theta),
    )
    assert np.max(np.abs(np.exp(1j * result.phases_rad) - np.exp(1j * expected))) <= 4 * delta
    assert result.phases_rad.dtype == np.dtype("float64")
    assert result.phases_rad.flags.c_contiguous


def case_arrays(images, steps, otf):
    return [images, steps, otf.values, otf.fy_per_um, otf.fx_per_um]


@pytest.mark.parametrize("container", ["list", "tuple", "object_array"])
def test_ordinary_integer_subclass_scan_positive_and_named_local_outcomes(container, caller_state):
    source = OrdinaryLabel("  unit transfer  ")
    images, steps, otf = illumination_case(source)
    rows = [
        (OrdinaryInteger(0), OrdinaryInteger(0)),
        (OrdinaryInteger(0), OrdinaryInteger(3)),
        (OrdinaryInteger(0), OrdinaryInteger(0)),
    ]
    candidates = rows if container == "list" else tuple(rows)
    if container == "object_array":
        candidates = np.array(rows, dtype=object)
    arrays = case_arrays(images, steps, otf)
    if container == "object_array":
        arrays.append(candidates)
    saved = snapshot_arrays(arrays)
    results = scan_carriers(
        images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=candidates
    )
    assert tuple(result.carrier_bins_yx for result in results) == ((0, 0), (0, 3), (0, 0))
    assert tuple(result.failure_code for result in results) == (
        None,
        "no_illumination_overlap",
        None,
    )
    assert results[1].estimate is None
    for index in (0, 2):
        assert_illumination(results[index].estimate, source)
        assert not np.shares_memory(
            cast(IlluminationEstimate, results[index].estimate).phases_rad, steps
        )
    assert not np.shares_memory(
        cast(IlluminationEstimate, results[0].estimate).phases_rad,
        cast(IlluminationEstimate, results[2].estimate).phases_rad,
    )
    assert snapshot_arrays(arrays) == saved


def test_zero_observations_scan_returns_named_local_information_failures(caller_state):
    images, steps, otf = illumination_case(OrdinaryLabel("unit transfer"))
    images.fill(0.0)
    candidates = [
        (OrdinaryInteger(0), OrdinaryInteger(0)),
        (OrdinaryInteger(0), OrdinaryInteger(1)),
        (OrdinaryInteger(0), OrdinaryInteger(3)),
        (OrdinaryInteger(0), OrdinaryInteger(0)),
    ]
    arrays = case_arrays(images, steps, otf)
    saved = snapshot_arrays(arrays)
    results = scan_carriers(
        images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=candidates
    )
    # Zero observations have an exact zero least-squares solution. Their
    # transforms contain only zero summands, unlike cancellation of nonzero
    # modes. Nonempty overlap therefore has zero predictor/response energy.
    assert tuple(result.carrier_bins_yx for result in results) == ((0, 0), (0, 1), (0, 3), (0, 0))
    assert tuple(result.failure_code for result in results) == (
        "unidentifiable_illumination",
        "unidentifiable_illumination",
        "no_illumination_overlap",
        "unidentifiable_illumination",
    )
    assert all(result.estimate is None for result in results)
    assert snapshot_arrays(arrays) == saved


@pytest.mark.parametrize("container", ["list", "object_array"])
def test_used_integer_protocol_preserves_original_caller_exception(
    container, caller_state, record_property
):
    images, steps, otf = illumination_case(OrdinaryLabel("unit transfer"))
    error = SimreconError("caller_coordinate_failure", "owned coordinate conversion failure")
    coordinate = RaisingInteger(0, error)
    candidates = [(coordinate, OrdinaryInteger(0))]
    arrays = case_arrays(images, steps, otf)
    if container == "object_array":
        candidates = np.array(candidates, dtype=object)
        arrays.append(candidates)
    saved = snapshot_arrays(arrays)
    caught = None
    results = None
    try:
        results = scan_carriers(
            images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=candidates
        )
    except SimreconError as observed:
        caught = observed
    exercised = bool(coordinate.events)
    record_property("integer_callback_exercised", exercised)
    if exercised:
        assert caught is error
        assert caught is not None
        assert caught.code == "caller_coordinate_failure"
        assert results is None
    else:
        assert caught is None
        assert results is not None
        assert len(results) == 1
        assert results[0].carrier_bins_yx == (0, 0)
        assert results[0].failure_code is None
        assert_illumination(results[0].estimate, otf.source)
    assert coordinate.error is error
    assert int.__int__(coordinate) == 0
    assert snapshot_arrays(arrays) == saved


def test_ordinary_string_subclass_direct_otf_positive(caller_state):
    source = OrdinaryLabel("  unit transfer  ")
    images, steps, otf = illumination_case(source)
    arrays = case_arrays(images, steps, otf)
    saved = snapshot_arrays(arrays)
    result = estimate_illumination(images, otf=otf, phase_steps_rad=steps, carrier_bins_yx=(0, 0))
    assert_illumination(result, source)
    assert snapshot_arrays(arrays) == saved


@pytest.mark.parametrize("operation", ["illumination", "scan"])
def test_used_label_protocol_preserves_original_caller_exception(
    operation, caller_state, record_property
):
    error = SimreconError("caller_label_failure", "owned label operation failure")
    source = RaisingLabel("unit transfer", error)
    images, steps, otf = illumination_case(source)
    arrays = case_arrays(images, steps, otf)
    saved = snapshot_arrays(arrays)
    caught = None
    result = None
    try:
        if operation == "illumination":
            result = estimate_illumination(
                images, otf=otf, phase_steps_rad=steps, carrier_bins_yx=(0, 0)
            )
        else:
            results = scan_carriers(
                images, otf=otf, phase_steps_rad=steps, candidate_carriers_bins_yx=[(0, 0)]
            )
            assert len(results) == 1
            assert results[0].failure_code is None
            result = results[0].estimate
    except SimreconError as observed:
        caught = observed
    exercised = bool(source.events)
    record_property("label_callback_exercised", exercised)
    if exercised:
        assert caught is error
        assert caught is not None
        assert caught.code == "caller_label_failure"
        assert result is None
    else:
        assert caught is None
        assert_illumination(result, source)
    assert source.error is error
    assert source == "unit transfer"
    assert otf.source is source
    assert snapshot_arrays(arrays) == saved


def test_genuine_operation_time_shortening_reports_source_changed(
    tmp_path, caller_state, record_property
):
    source = tmp_path / "operation.priism"
    extension_bytes = 4 * 1024 * 1024
    header, pixels, config, extension_digest = write_priism(source, extension_bytes=extension_bytes)
    original_bytes = source.read_bytes()
    original_stat = source.stat()
    original_config = json.dumps(config, sort_keys=True)
    info = harmonize(inspect(source), config=config)
    assert info.original_header == header
    assert info.header_sha256 == hashlib.sha256(header).hexdigest()
    assert info.source_size == 1024 + extension_bytes + pixels.nbytes
    assert info.source_mtime_ns == original_stat.st_mtime_ns
    assert info.extended_header_bytes == extension_bytes
    assert np.array_equal(read(info, plane_start=0, plane_stop=1).data, pixels)

    positive = tmp_path / "positive.ome.tif"
    report = export_imagej(positive, info, block_planes=1)
    assert report.series_count == 1 and report.planes_written == 1
    with tifffile.TiffFile(positive) as output:
        assert output.is_bigtiff
        assert len(output.pages) == 1
        assert np.array_equal(output.pages[0].asarray(), pixels[0])
        root = ET.fromstring(cast(str, output.ome_metadata))
        namespace = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
        entries = root.findall(".//ome:MapAnnotation/ome:Value/ome:M", namespace)
        metadata = json.loads(
            cast(str, next(entry.text for entry in entries if entry.get("K") == "metadata_json"))
        )
    assert base64.b64decode(metadata["original_header_base64"]) == header
    assert metadata["original_extension"] == {
        "schema": "opaque",
        "bytes": extension_bytes,
        "sha256": extension_digest,
        "content_retained": False,
    }
    assert source.read_bytes() == original_bytes
    assert source.stat().st_size == original_stat.st_size
    assert source.stat().st_mtime_ns == original_stat.st_mtime_ns
    positive_digest = hashlib.sha256(positive.read_bytes()).hexdigest()

    destination = tmp_path / "intervened.ome.tif"
    shortened_size = 1024 + extension_bytes // 2
    observation = observe_operation_time_shortening(
        info, destination, shortened_size=shortened_size
    )
    record_property("operation_time_source_change", json.dumps(observation, sort_keys=True))
    mutation = observation["mutation"]
    operation = observation["operation"]
    if (
        mutation is None
        or operation is None
        or observation["incomplete_reason"] is not None
        or observation["child_exitcode"] != 0
    ):
        pytest.fail(
            "Diagnostic capability gap: no complete witnessed operation-time mutation; "
            "this is neither product-red nor a source-change test pass"
        )
    assert (
        operation["operation_start_ns"]
        < observation["audit_event_ns"]
        <= mutation["start_ns"]
        < mutation["end_ns"]
        < operation["operation_end_ns"]
    )
    assert mutation["actor_pid"] == os.getpid()
    assert mutation["actor_pid"] != observation["child_pid"]
    assert mutation["size_before"] == info.source_size
    assert mutation["size_after"] == shortened_size
    assert mutation["mtime_before_ns"] == info.source_mtime_ns
    assert mutation["mtime_after_ns"] == source.stat().st_mtime_ns
    assert mutation["header_sha256_before"] == info.header_sha256
    assert mutation["header_sha256_after"] == info.header_sha256
    assert source.read_bytes() == original_bytes[:shortened_size]
    assert operation["outcome"]["success"] is False
    assert operation["outcome"]["domain_error"] is True
    assert operation["outcome"]["code"] == "source_changed"
    # A partial newly created destination may remain. Its absence is also legal.
    # The audit event establishes no successful private extension-read stage.
    assert hashlib.sha256(positive.read_bytes()).hexdigest() == positive_digest
    assert info.original_header == header
    assert info.source_size == original_stat.st_size
    assert info.source_mtime_ns == original_stat.st_mtime_ns
    assert json.dumps(config, sort_keys=True) == original_config


class RaisingFloat(float):
    """Always raise the caller's exception when ordinary conversion is used."""

    error: SimreconError
    events: list[str]

    def __new__(cls, value, error):
        result = super().__new__(cls, value)
        result.error = error
        result.events = []
        return result

    def __float__(self):
        """Record invocation and always raise the unchanged caller exception."""
        self.events.append("float")
        raise self.error


def test_used_float_protocol_preserves_original_caller_exception(caller_state, record_property):
    reference = np.array([[0.0, 1.0, 3.0], [2.0, 7.0, 4.0]])
    moving = np.roll(reference, (1, -1), axis=(0, 1))
    saved = snapshot_arrays([moving, reference])
    stored_tolerance = 0.125
    positive = estimate_translation(
        moving, reference=reference, ambiguity_tolerance=OrdinaryFloat(stored_tolerance)
    )
    assert_translation(positive, moving, reference, stored_tolerance)
    assert snapshot_arrays([moving, reference]) == saved
    record_property("float_exception_positive_control", "independent objective passed")

    error = SimreconError("caller_tolerance_failure", "owned tolerance conversion failure")
    tolerance = RaisingFloat(stored_tolerance, error)
    caught = None
    result = None
    try:
        result = estimate_translation(moving, reference=reference, ambiguity_tolerance=tolerance)
    except SimreconError as observed:
        caught = observed
    exercised = bool(tolerance.events)
    record_property("float_exception_callback_exercised", exercised)
    if exercised:
        assert caught is error
        assert caught is not None
        assert caught.code == "caller_tolerance_failure"
        assert result is None
        record_property("float_exception_path_evidence", "original object and code propagated")
    else:
        # Reading the inherited scalar is lawful; it leaves exception propagation unproved.
        assert caught is None
        assert_translation(result, moving, reference, stored_tolerance)
        record_property(
            "float_exception_path_evidence", "qualified positive; exception path unproved"
        )
    assert float.__float__(tolerance) == stored_tolerance
    assert tolerance.error is error
    assert error.code == "caller_tolerance_failure"
    assert snapshot_arrays([moving, reference]) == saved
