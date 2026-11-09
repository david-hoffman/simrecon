"""Supplemental public preservation; fresh B must assess this checkpoint."""

import base64
import hashlib
import json
import os
import warnings
import xml.etree.ElementTree as ET
from typing import cast

import numpy as np
import pytest
import tifffile

from shared_node_baseline_public_failures_fixture import (
    observe_operation_time_shortening,
    write_priism,
)
from simrecon import export_imagej, harmonize, inspect, read


@pytest.fixture
def caller_state():
    """Check preservation of caller arithmetic and warning settings."""
    mode = np.geterr()
    filters = warnings.filters[:]
    yield
    assert np.geterr() == mode
    assert warnings.filters == filters


def test_genuine_opaque_priism_mutation_free_export_twin(tmp_path, caller_state):
    source = tmp_path / "valid.priism"
    header, pixels, config, extension_digest = write_priism(source)
    source_bytes = source.read_bytes()
    source_stat = source.stat()
    original_config = json.dumps(config, sort_keys=True)
    info = harmonize(inspect(source), config=config)
    assert info.original_header == header
    assert info.source_size == 1024 + 4096 + pixels.nbytes
    assert info.extended_header_bytes == 4096
    assert info.header_sha256 == hashlib.sha256(header).hexdigest()
    block = read(info, plane_start=0, plane_stop=1)
    assert np.array_equal(block.data, pixels)
    destination = tmp_path / "valid.ome.tif"
    report = export_imagej(destination, info, block_planes=1)
    assert report.series_count == 1 and report.planes_written == 1
    assert report.series[0].name == "orientation=absent; phase=absent"
    assert report.series[0].shape == (1, 1, 1, 2, 3)
    with tifffile.TiffFile(destination) as output:
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
        "bytes": 4096,
        "sha256": extension_digest,
        "content_retained": False,
    }
    assert source.read_bytes() == source_bytes
    assert source.stat().st_size == source_stat.st_size
    assert source.stat().st_mtime_ns == source_stat.st_mtime_ns
    assert info.original_header == header
    assert json.dumps(config, sort_keys=True) == original_config


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
