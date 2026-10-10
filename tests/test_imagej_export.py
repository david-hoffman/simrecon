"""Blind public-contract tests for IMAGEJ-EXPORT-01; see independent fixture formulas."""

from __future__ import annotations

import base64
import copy
import errno
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
import tracemalloc
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterator, Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import tifffile

import simrecon
from imagej_export_fixture import (
    CANONICAL,
    NS,
    Acquisition,
    assert_values,
    decode_raw,
    exact_json_dumps,
    finite_json,
    json_with_exact_numbers,
    observe,
    persist_observation,
    persist_report_observation,
    scale_close,
    sha256,
    sparse_extension_source,
    values_equal,
)

Q = "{" + NS + "}"
PUBLIC: Any = simrecon
PROFILE = {
    "open_all_series": True,
    "quiet": True,
    "windowless": True,
    "group_files": False,
    "ungroup_files": True,
    "must_group": False,
    "concatenate": False,
    "split_c": False,
    "split_z": False,
    "split_t": False,
    "crop": False,
    "ranges": False,
    "swap": False,
    "autoscale": False,
    "updater": False,
    "virtual": False,
    "stitch_tiles": False,
    "force_thumbnails": False,
    "show_metadata": False,
    "show_ome_xml": False,
    "show_rois": False,
    "pattern_ids": False,
    "color_mode": "Grayscale",
    "stack_format": "Hyperstack",
    "stack_order": "XYCZT",
    "location": "Local machine",
    "headless": "true",
}


@pytest.fixture
def api() -> Callable[..., Any]:
    candidate = getattr(simrecon, "export_imagej", None)
    assert callable(candidate), "IMAGEJ-EXPORT-01 requires public simrecon.export_imagej"
    return candidate


def input_info(
    tmp_path: Path, spec: Acquisition, *, sparse: bool = False
) -> tuple[Path, Any, dict[str, Any]]:
    source = tmp_path / "independent.priism"
    spec.write(source, sparse=sparse)
    config = spec.config()
    return source, simrecon.harmonize(simrecon.inspect(source), config=config), config


def planes(spec: Acquisition) -> Iterator[tuple[int, int, int, int, int, int, int]]:
    """(series,o,p,n,t,c,z); output C fastest, then Z, then T."""
    count_c, count_z = spec.count("channel"), spec.count("z")
    for o in range(spec.count("orientation")):
        for p in range(spec.count("phase")):
            s = o * spec.count("phase") + p
            for t in range(spec.count("time")):
                for z in range(count_z):
                    for c in range(count_c):
                        yield s, o, p, c + count_c * (z + count_z * t), t, c, z


def assert_limitations_representation(report: Any) -> None:
    """Only the public tuple/string representation is machine-verifiable here.

    No count, order, wording or per-string facts are prescribed. Successful
    reports are captured below; independent D must review whole-text truth,
    completeness, conditionals and actual emitting paths against A04's matrix.
    Passing this assertion is never semantic acceptance of disclosures.
    """
    assert isinstance(report.limitations, tuple) and all(
        isinstance(s, str) for s in report.limitations
    )


def assert_report(report: Any, destination: Path, spec: Acquisition, info: Any) -> None:
    assert isinstance(report, PUBLIC.ImagejWriteReport)
    assert isinstance(report.destination, Path) and report.destination == destination
    assert type(report.series_count) is int and type(report.planes_written) is int
    assert_values(report.series_count, spec.series_count)
    assert_values(report.planes_written, spec.sections)
    assert isinstance(report.series, tuple) and len(report.series) == spec.series_count
    for s, series in enumerate(report.series):
        o, p = divmod(s, spec.count("phase"))
        assert isinstance(series, PUBLIC.ImagejSeries) and type(series.index) is int
        assert_values(series.index, s)
        assert_values(series.name, spec.name(o, p))
        for actual, expected in (
            (series.orientation_index, o if "orientation" in spec.plane_axes else None),
            (series.phase_index, p if "phase" in spec.plane_axes else None),
        ):
            assert actual is None or type(actual) is int
            assert_values(actual, expected)
        assert isinstance(series.shape, tuple) and all(type(count) is int for count in series.shape)
        assert_values(series.shape, spec.series_shape)
    assert isinstance(report.provenance, tuple)
    assert_values(report.provenance, info.provenance)


def assert_descriptor_preserved(actual: Any, expected: Any) -> None:
    # Named public fields, never implementation dictionaries/source/introspection.
    fields = (
        "source",
        "source_size",
        "source_mtime_ns",
        "header_sha256",
        "original_header",
        "stored_shape",
        "pixel_mode",
        "stored_dtype",
        "data_kind",
        "byte_order",
        "extended_header_bytes",
        "file_metadata",
        "unresolved",
        "axes",
        "shape",
        "config",
        "sampling_um",
        "wavelengths_nm",
        "provenance",
    )
    for name in fields:
        assert_values(getattr(actual, name), getattr(expected, name))


def project_metadata(xml: ET.Element, images: list[ET.Element]) -> tuple[dict[str, Any], str]:
    annotations = {
        node.attrib["ID"]: node
        for node in xml.findall(f"{Q}StructuredAnnotations/{Q}MapAnnotation")
    }
    values = []
    for image in images:
        matching = [
            annotations[ref.attrib["ID"]]
            for ref in image.findall(Q + "AnnotationRef")
            if ref.attrib["ID"] in annotations
            and annotations[ref.attrib["ID"]].get("Namespace") == "org.simrecon.imagej-copy"
        ]
        assert len(matching) == 1
        entries = matching[0].findall(f"{Q}Value/{Q}M")
        assert len(entries) == 1 and entries[0].get("K") == "metadata_json"
        value = entries[0].text
        assert value is not None and not value.startswith("\ufeff")
        values.append(value)
    assert values and len(set(values)) == 1

    def sorted_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in pairs]
        assert keys == sorted(keys) and len(keys) == len(set(keys)), "JSON keys/order"
        return dict(pairs)

    # Validate compact syntax without re-encoding numbers or string escapes.
    # json.loads validates tokens; this scan rejects whitespace only outside
    # strings. Sorted decoded object keys and duplicates are checked at every level.
    in_string = escaped = False
    for character in values[0]:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        else:
            assert character not in " \t\r\n", "JSON must use compact separators"
    metadata = json_with_exact_numbers(
        values[0],
        object_pairs_hook=sorted_object,
    )
    assert isinstance(metadata, dict)
    return metadata, values[0]


def assert_metadata(
    metadata: Mapping[str, Any], source: Path, spec: Acquisition, info: Any
) -> None:
    expected = {
        "schema": "org.simrecon.imagej-copy",
        "version": 1,
        "data_kind": "spatial_image",
        "logical_axes": [axis for axis in CANONICAL if axis in spec.plane_axes] + ["y", "x"],
        "logical_shape": [spec.count(axis) for axis in CANONICAL if axis in spec.plane_axes]
        + [spec.y, spec.x],
        "source_layout": {
            "plane_axes": list(spec.plane_axes),
            "plane_shape": list(spec.plane_shape),
            "byte_order": spec.byte_order,
            "pixel_mode": spec.mode,
        },
        "stored_shape": [spec.sections, spec.y, spec.x],
        "sampling_um": finite_json(info.sampling_um),
        "wavelengths_nm": finite_json(info.wavelengths_nm),
        "acquisition_config": finite_json(info.config),
        "file_metadata": finite_json(info.file_metadata),
        "unresolved": finite_json(info.unresolved),
        "provenance": finite_json(info.provenance),
        "source_identity": {
            "source_name": source.name,
            "source_size": source.stat().st_size,
            "source_mtime_ns": source.stat().st_mtime_ns,
            "header_sha256": hashlib.sha256(spec.header()).hexdigest(),
        },
        "original_header_base64": base64.b64encode(spec.header()).decode("ascii"),
        "original_extension": {
            "schema": "opaque" if spec.extension else "none",
            "bytes": len(spec.extension),
            "sha256": hashlib.sha256(spec.extension).hexdigest(),
            "content_retained": False,
        },
        "series_layout": {
            "series_order": "orientation_phase",
            "plane_order": "XYCZT",
            "series_count": spec.series_count,
            "per_series_shape": list(spec.series_shape),
            "orientation_count": spec.count("orientation"),
            "phase_count": spec.count("phase"),
            **{
                axis + "_present": axis in spec.plane_axes
                for axis in ("orientation", "phase", "z", "channel", "time")
            },
        },
    }
    assert_values(metadata, expected)
    assert metadata["original_extension"]["content_retained"] is False
    assert all(
        type(metadata["series_layout"][axis + "_present"]) is bool
        for axis in ("orientation", "phase", "z", "channel", "time")
    )
    for shape in (
        metadata["logical_shape"],
        metadata["stored_shape"],
        metadata["source_layout"]["plane_shape"],
        metadata["series_layout"]["per_series_shape"],
    ):
        assert all(
            isinstance(count, (int, float, Decimal))
            and not isinstance(count, bool)
            and count > 0
            and count == int(count)
            for count in shape
        )
    assert base64.b64decode(metadata["original_header_base64"], validate=True) == spec.header()
    assert str(source.resolve()) not in exact_json_dumps(metadata)


def assert_carrier(output: Path, source: Path, spec: Acquisition, info: Any) -> dict[str, Any]:
    sampling = spec.resolved_sampling()
    with output.open("rb") as stream:
        assert stream.read(8) == b"II\x2b\x00\x08\x00\x00\x00"
    with tifffile.TiffFile(output) as tif:
        assert tif.is_bigtiff and tif.byteorder == "<"
        assert len(tif.pages) == spec.sections
        first_page = tif.pages[0]
        assert isinstance(first_page, tifffile.TiffPage)
        description = first_page.description
        assert description is not None
        description_tag = first_page.tags["ImageDescription"]
        with output.open("rb") as stream:
            stream.seek(description_tag.valueoffset)
            encoded_description = stream.read(description_tag.count).rstrip(b"\x00")
        assert encoded_description.decode("utf-8") == description
        xml = ET.fromstring(description)
        assert xml.tag == Q + "OME"
        assert not xml.findall(".//" + Q + "BinaryOnly")
        assert not xml.findall(".//" + Q + "BinData")
        images = xml.findall(Q + "Image")
        assert len(images) == spec.series_count
        metadata, _ = project_metadata(xml, images)
        assert_metadata(metadata, source, spec, info)
        per_series = spec.count("channel") * spec.count("z") * spec.count("time")
        observed_maps: list[tuple[int, int, int, int, int]] = []
        for s, image in enumerate(images):
            o, p = divmod(s, spec.count("phase"))
            assert image.get("Name") == spec.name(o, p)
            pixels = image.find(Q + "Pixels")
            assert pixels is not None
            assert pixels.get("DimensionOrder") == "XYCZT"
            assert pixels.get("Type") == ("uint16" if spec.mode == 6 else "float")
            assert pixels.get("BigEndian", "false").lower() in ("false", "0")
            for axis, expected in zip(
                "XYCZT",
                (spec.x, spec.y, spec.count("channel"), spec.count("z"), spec.count("time")),
                strict=True,
            ):
                assert int(pixels.attrib["Size" + axis]) == expected
            for axis in "XY":
                assert pixels.get("PhysicalSize" + axis + "Unit") == "µm"
                expected_scale = sampling[axis.lower()]
                assert expected_scale is not None
                # Original XML must round-trip the supplied binary64 exactly.
                # Reader/unit-conversion tolerance belongs only to assert_observer.
                assert float(pixels.attrib["PhysicalSize" + axis]) == expected_scale, (
                    "carrier scale decimal does not round-trip supplied binary64"
                )
            if "z" in spec.plane_axes:
                assert pixels.get("PhysicalSizeZUnit") == "µm"
                expected_z = sampling["z"]
                assert expected_z is not None
                assert float(pixels.attrib["PhysicalSizeZ"]) == expected_z, (
                    "carrier scale decimal does not round-trip supplied binary64"
                )
            else:
                assert "PhysicalSizeZ" not in pixels.attrib
            assert "TimeIncrement" not in pixels.attrib and "TimeIncrementUnit" not in pixels.attrib
            assert image.find(Q + "AcquisitionDate") is None
            channels = pixels.findall(Q + "Channel")
            assert len(channels) == spec.count("channel")
            for c, channel in enumerate(channels):
                assert channel.get("Name") == f"channel={c}"
                assert int(channel.attrib["SamplesPerPixel"]) == 1
                assert not any(
                    key in channel.attrib
                    for key in ("ExcitationWavelength", "EmissionWavelength", "Color")
                )
            for plane in pixels.findall(Q + "Plane"):
                assert not any(
                    key in plane.attrib
                    for key in ("PositionX", "PositionY", "PositionZ", "DeltaT", "ExposureTime")
                )
            tiff_data = pixels.findall(Q + "TiffData")
            assert tiff_data, "explicit plane mappings required"
            for mapping in tiff_data:
                first_ifd = int(mapping.get("IFD", "0"))
                z0, c0, t0 = (int(mapping.get("First" + axis, "0")) for axis in "ZCT")
                # Bounds must precede flattening: FirstC=C would otherwise alias
                # FirstC=0,FirstZ=1, and FirstZ=Z would alias FirstZ=0,FirstT=1.
                for axis, coordinate in (("z", z0), ("channel", c0), ("time", t0)):
                    assert 0 <= coordinate < spec.count(axis), (
                        f"TiffData starting {axis} coordinate is out of bounds"
                    )
                start = c0 + spec.count("channel") * (z0 + spec.count("z") * t0)
                default_count = 1 if "IFD" in mapping.attrib else len(tif.pages)
                count = int(mapping.get("PlaneCount", str(default_count)))
                assert count > 0
                for offset in range(count):
                    n = start + offset
                    assert 0 <= n < per_series
                    t, remainder = divmod(n, spec.count("z") * spec.count("channel"))
                    z, c = divmod(remainder, spec.count("channel"))
                    observed_maps.append((s, first_ifd + offset, t, c, z))
                for uuid in mapping.findall(Q + "UUID"):
                    # The OME schema permits self references such as './copy.tif'.
                    # Resolve spelling without permitting an external pixel file.
                    referenced_file = output.parent / uuid.get("FileName", output.name)
                    assert referenced_file.resolve() == output.resolve(), (
                        "TiffData references external pixels"
                    )
        expected_maps = [(s, s * per_series + n, t, c, z) for s, _, _, n, t, c, z in planes(spec)]
        assert sorted(observed_maps) == sorted(expected_maps)
        for s, o, p, n, t, c, z in planes(spec):
            page = tif.pages[s * per_series + n]
            assert isinstance(page, tifffile.TiffPage)
            assert page.shape == (spec.y, spec.x)
            assert page.samplesperpixel == 1 and page.compression == 1
            assert page.predictor == 1
            assert page.bitspersample == spec.itemsize * 8
            assert page.sampleformat == (1 if spec.mode == 6 else 3)
            assert not page.subifds
            assert not page.is_reduced
            assert page.asarray().tobytes() == spec.plane_bytes(o=o, p=p, t=t, c=c, z=z)
            # Independently inspect uncompressed strip bytes, including NaN payloads.
            with output.open("rb") as stream:
                chunks = []
                for offset, count in zip(page.dataoffsets, page.databytecounts, strict=True):
                    stream.seek(offset)
                    chunks.append(stream.read(count))
            if not page.is_tiled:
                assert b"".join(chunks) == spec.plane_bytes(o=o, p=p, t=t, c=c, z=z)
        return metadata


def assert_observer(record: Mapping[str, Any], output: Path, spec: Acquisition, info: Any) -> None:
    sampling = spec.resolved_sampling()
    assert record["startup_only"] is False
    assert_values(record["profile"], PROFILE)
    assert record["carrier_schema_valid"] is True
    assert record["used_files"] == [output.name]
    raw, imageplus = record["raw_series"], record["imageplus"]
    assert len(raw) == len(imageplus) == spec.series_count
    dimensions = [spec.x, spec.y, spec.count("channel"), spec.count("z"), spec.count("time")]
    count = spec.count("channel") * spec.count("z") * spec.count("time")
    raw_xml = ET.fromstring(record["raw_ome_xml"])
    assert raw_xml.tag == Q + "OME"
    carrier_xml = ET.fromstring(record["carrier_ome_xml"])
    metadata, _ = project_metadata(carrier_xml, carrier_xml.findall(Q + "Image"))
    assert_values(metadata["logical_shape"], list(info.shape))
    for s, (r, im) in enumerate(zip(raw, imageplus, strict=True)):
        o, p = divmod(s, spec.count("phase"))
        assert_values(r["index"], s)
        assert_values(im["series_property"], s)
        assert r["name"] == spec.name(o, p)
        title = output.name if spec.series_count == 1 else output.name + " - " + spec.name(o, p)
        # Controlled ASCII names are short and do not trigger upstream suppression/truncation.
        assert im["title"] == title
        assert_values(r["dimensions_xyczt"], dimensions)
        assert_values(im["dimensions_xyczt"], dimensions)
        assert r["order"] == "XYCZT" and r["little_endian"] is True and r["rgb"] is False
        assert_values(r["resolution_count"], 1)
        assert_values(r["image_count"], count)
        assert_values(im["stack_size"], count)
        assert r["pixel_type"] == ("uint16" if spec.mode == 6 else "float")
        assert_values(im["bit_depth"], spec.itemsize * 8)
        assert im["open_as_hyperstack"] is True
        if 2 <= spec.count("channel") <= 7:
            assert_values(im["composite_mode"], 3)  # pinned ImageJ GRAYSCALE
        assert_values(
            r["channels"],
            [
                {"name": f"channel={c}", "samples_per_pixel": 1}
                for c in range(spec.count("channel"))
            ],
        )
        for axis in "xy":
            expected_scale = sampling[axis]
            assert expected_scale is not None
            scale_close(r["physical_um"][axis], expected_scale)
            scale_close(im["calibration"][axis], expected_scale)
        assert im["calibration"]["unit"] in ("µm", "um", "micron", "micrometer", "micrometre")
        if "z" in spec.plane_axes:
            expected_z = sampling["z"]
            assert expected_z is not None
            scale_close(r["physical_um"]["z"], expected_z)
            scale_close(im["calibration"]["z"], expected_z)
        else:
            assert r["physical_um"]["z"] is None
            assert_values(im["calibration"]["z"], 1)  # viewer default; JSON says absent
        assert_values(im["calibration"]["frame_interval"], 0)
        # Viewer default origin has no contractual signed-zero preservation.
        origin = im["calibration"]["origin"]
        assert isinstance(origin, list) and len(origin) == 3
        assert all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0 for v in origin
        )
        assert im["calibration"]["density_calibrated"] is False
        # Record the actual importer XML, but do not require arbitrary annotations
        # to become an ImagePlus property or survive the importer's metadata copy.
        # The file's original OME annotation above provides independent recovery.
        if im["ome_xml"]:
            assert ET.fromstring(im["ome_xml"]).tag == Q + "OME"
    for s, o, p, n, t, c, z in planes(spec):
        rplane, iplane = raw[s]["planes"][n], imageplus[s]["planes"][n]
        assert_values(rplane["n"], n)
        assert_values(rplane["zct"], [z, c, t])
        assert_values(iplane["zct"], [z, c, t])
        assert_values(iplane["stack_index"], n + 1)
        expected = spec.plane_bytes(o=o, p=p, t=t, c=c, z=z)
        assert decode_raw(rplane) == expected
        words = list(
            struct.unpack("<" + ("H" if spec.mode == 6 else "I") * (spec.x * spec.y), expected)
        )
        assert iplane["primitive"] == ("short[]" if spec.mode == 6 else "float[]")
        assert len(iplane["words"]) == len(words)
        for observed, word in zip(iplane["words"], words, strict=True):
            assert type(observed) is int  # observer emits primitive integer bit words
            if spec.mode == 2 and word & 0x7F800000 == 0x7F800000 and word & 0x007FFFFF:
                assert observed & 0x7F800000 == 0x7F800000 and observed & 0x007FFFFF
            else:
                assert observed == word  # finite, zeros and infinities retain exact primitive bits


def test_owned_observer_startup(tmp_path: Path) -> None:
    record = observe(None, tmp_path / "startup")
    assert record["startup_only"] is True
    assert_values(record["profile"], PROFILE)
    assert "raw_series" not in record and "imageplus" not in record


FULL = [
    Acquisition(mode=mode, byte_order=endian) for mode in (6, 2) for endian in ("little", "big")
]
AXES = [
    Acquisition(plane_axes=(), plane_shape=(), extension=b""),
    Acquisition(plane_axes=("phase",), plane_shape=(4,), extension=b""),
    Acquisition(plane_axes=("orientation",), plane_shape=(5,)),
    Acquisition(
        plane_axes=("z", "phase", "time", "channel", "orientation"), plane_shape=(1, 1, 1, 1, 1)
    ),
    Acquisition(
        plane_axes=("z", "channel", "phase", "orientation", "time"), plane_shape=(4, 2, 3, 2, 3)
    ),
    Acquisition(plane_axes=("phase", "orientation"), plane_shape=(5, 2)),
]


@pytest.mark.parametrize(
    "spec",
    FULL + AXES,
    ids=[
        "u16-le",
        "u16-be",
        "f32-le",
        "f32-be",
        "all-absent",
        "phase-only",
        "orientation-only",
        "all-singleton",
        "unequal-czt",
        "five-phases",
    ],
)
def test_every_setting_file_raw_and_imageplus(
    tmp_path: Path, api: Callable[..., Any], spec: Acquisition
) -> None:
    source, info, config = input_info(tmp_path, spec)
    config_before, descriptor_before = copy.deepcopy(config), copy.deepcopy(info)
    source_before = sha256(source), source.stat().st_mtime_ns
    destination = tmp_path / "copy.ome.tif"
    report = api(destination, info, block_planes=2)
    assert_report(report, destination, spec, info)
    assert isinstance(report, PUBLIC.ImagejWriteReport)
    assert report.destination == destination and isinstance(report.destination, Path)
    assert report.series_count == spec.series_count and report.planes_written == spec.sections
    assert type(report.series_count) is int and type(report.planes_written) is int
    assert isinstance(report.series, tuple) and len(report.series) == spec.series_count
    for s, series in enumerate(report.series):
        o, p = divmod(s, spec.count("phase"))
        assert isinstance(series, PUBLIC.ImagejSeries)
        assert type(series.index) is int
        assert series.index == s and series.name == spec.name(o, p)
        assert series.orientation_index == (o if "orientation" in spec.plane_axes else None)
        assert series.phase_index == (p if "phase" in spec.plane_axes else None)
        assert series.shape == spec.series_shape and isinstance(series.shape, tuple)
        assert all(type(count) is int for count in series.shape)
        for index in (series.orientation_index, series.phase_index):
            assert index is None or type(index) is int
    assert_values(report.provenance, info.provenance)
    assert isinstance(report.provenance, tuple)
    assert_limitations_representation(report)
    persist_report_observation(
        report,
        source,
        destination,
        config,
        spec,
        info,
        f"every-setting-mode{spec.mode}-{spec.byte_order}-"
        f"axes{'_'.join(spec.plane_axes) or 'absent'}",
    )
    assert_carrier(destination, source, spec, info)
    record = observe(destination, tmp_path / "reader")
    assert_observer(record, destination, spec, info)
    persist_observation(
        record,
        source,
        destination,
        config,
        f"mode{spec.mode}-{spec.byte_order}-axes{'_'.join(spec.plane_axes) or 'absent'}",
    )
    assert_values(config, config_before)
    assert_descriptor_preserved(info, descriptor_before)
    assert (sha256(source), source.stat().st_mtime_ns) == source_before
    # The original still serves the established public read boundary.
    block = simrecon.read(info, plane_start=0, plane_stop=1)
    assert block.data.tobytes() == spec.plane_bytes(o=0, p=0, t=0, c=0, z=0)


@pytest.mark.parametrize("endian", ["little", "big"])
def test_overrides_and_nonfinite_source_words_are_retained(
    tmp_path: Path, api: Callable[..., Any], endian: str
) -> None:
    # Both are valid source files with positive explicit resolved sampling.
    # Exact decoded binary32 source words and copied old/new provenance retain
    # zero signs independently of the JSON numeral spelling.
    for label, source_words in (
        ("nonfinite", (0x7FC12345, 0x7F800000, 0xFF800000)),
        ("signed-zero", (0x80000000, 0x00000000, 0x80000000)),
    ):
        spec = Acquisition(
            byte_order=endian,
            spatial_words=source_words,
            overrides={
                "sampling_um": {"x": math.nextafter(0.1, 1.0), "y": 0.2, "z": 0.625},
                "wavelengths_nm": {"0": 488.0, "1": 599.125},
            },
        )
        case = tmp_path / label
        case.mkdir()
        source, info, config = input_info(case, spec)
        output = case / "metadata.ome.tif"
        report = api(output, info)
        assert_report(report, output, spec, info)
        metadata = assert_carrier(output, source, spec, info)
        words = metadata["file_metadata"]["spatial_fields"]
        prefix = "<" if endian == "little" else ">"
        # Derive decoded spatial-field values from independently packed source words.
        expected_words = []
        for word in source_words:
            encoded = struct.pack(prefix + "I", word)
            decoded = struct.unpack(prefix + "f", encoded)[0]
            expected_words.append(
                decoded
                if math.isfinite(decoded)
                else {"unresolved": "nonfinite", "ieee_bytes": encoded.hex()}
            )
        assert_values(words, expected_words)
        assert_values(info.file_metadata["spatial_fields"], expected_words)
        assert_values(metadata["sampling_um"], spec.resolved_sampling())
        assert any(change["source"] == "override" for change in metadata["provenance"])
        assert_limitations_representation(report)
        persist_report_observation(
            report, source, output, config, spec, info, f"source-words-{label}-{endian}"
        )
        record = observe(output, case / "reader")
        assert_observer(record, output, spec, info)
        persist_observation(record, source, output, config, f"{label}-header-{endian}")


def test_equal_override_and_block_partition_are_preserved(
    tmp_path: Path, api: Callable[..., Any]
) -> None:
    # An equal override is still provenance, and block partition does not change meaning.
    equal = struct.unpack("<f", struct.pack("<f", 0.0975))[0]
    spec = Acquisition(overrides={"sampling_um": {"x": equal}, "wavelengths_nm": {"0": 488.0}})
    source, info, config = input_info(tmp_path, spec)
    assert any(
        entry["source"] == "override" and values_equal(entry["old"], entry["new"])
        for entry in info.provenance
    )
    for block in (1, 7, spec.sections + 1):
        output = tmp_path / f"block-{block}.ome.tif"
        report = api(str(output), info, block_planes=block)
        assert_report(report, output, spec, info)
        assert report.destination == output
        assert_limitations_representation(report)
        persist_report_observation(report, source, output, config, spec, info, f"block-{block}")
        assert_carrier(output, source, spec, info)
        assert_values(report.provenance, info.provenance)


def reject(api: Callable[..., Any], destination: Path, info: Any, code: str, **kwargs: Any) -> None:
    with pytest.raises(simrecon.SimreconError) as error:
        api(destination, info, **kwargs)
    assert error.value.code == code and isinstance(error.value.message, str)
    assert not destination.exists()


@pytest.mark.parametrize("block", [0, -1, True, False, 1.0, "1", None])
def test_invalid_blocks_before_creation(
    tmp_path: Path, api: Callable[..., Any], block: Any
) -> None:
    _, info, _ = input_info(tmp_path, Acquisition())
    reject(api, tmp_path / "invalid.ome.tif", info, "invalid_block_size", block_planes=block)


@pytest.mark.parametrize(
    "kind,code",
    [
        ("unharmonized", "config_required"),
        ("mode", "unsupported_mode"),
        ("axes", "unsupported_axes"),
    ],
)
def test_single_invalid_source_before_creation(
    tmp_path: Path, api: Callable[..., Any], kind: str, code: str
) -> None:
    spec = (
        Acquisition(mode=0)
        if kind == "mode"
        else Acquisition(map_axes=(2, 1, 3))
        if kind == "axes"
        else Acquisition()
    )
    source = tmp_path / "invalid.priism"
    spec.write(source)
    inspected = simrecon.inspect(source)
    # Unsupported inspectable sources have otherwise settled config. Harmonize may
    # itself reject the mode/mapping; that existing boundary remains authoritative.
    if kind == "unharmonized":
        reject(api, tmp_path / "invalid.ome.tif", inspected, code)
    else:
        try:
            info = simrecon.harmonize(inspected, config=spec.config())
        except simrecon.SimreconError as error:
            assert error.code == code
            assert not (tmp_path / "invalid.ome.tif").exists()
        else:
            reject(api, tmp_path / "invalid.ome.tif", info, code)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
@pytest.mark.parametrize("value", [1e-50, 2.0**-150, 1e39])
def test_scale_float32_underflow_overflow(
    tmp_path: Path, api: Callable[..., Any], value: float, axis: str
) -> None:
    spec = Acquisition(overrides={"sampling_um": {axis: value}})
    _, info, _ = input_info(tmp_path, spec)
    reject(api, tmp_path / "invalid.ome.tif", info, "imagej_unrepresentable")


@pytest.mark.parametrize("axis", ["x", "y", "z"])
@pytest.mark.parametrize(
    "value", [2.0**-149, float.fromhex("0x1.fffffep+127"), math.nextafter(0.125, 1.0)]
)
def test_scale_positive_float32_limits_and_binary64_precision(
    tmp_path: Path, api: Callable[..., Any], value: float, axis: str
) -> None:
    spec = Acquisition(
        plane_axes=("z",),
        plane_shape=(1,),
        extension=b"",
        overrides={"sampling_um": {axis: value}},
    )
    source, info, config = input_info(tmp_path, spec)
    output = tmp_path / "scale.ome.tif"
    report = api(output, info)
    assert_report(report, output, spec, info)
    assert_limitations_representation(report)
    persist_report_observation(report, source, output, config, spec, info, f"scale-{axis}")
    assert_carrier(output, source, spec, info)
    record = observe(output, tmp_path / "reader")
    assert_observer(record, output, spec, info)
    persist_observation(record, source, output, config, "representable-scale")


def test_sparse_plane_byte_index_bound_before_payload_access(
    tmp_path: Path, api: Callable[..., Any]
) -> None:
    # int32 X is valid; one uint16 row is 2**31 bytes, one above signed32 max.
    spec = Acquisition(plane_axes=(), plane_shape=(), x=1 << 30, y=1, extension=b"")
    _, info, _ = input_info(tmp_path, spec, sparse=True)
    assert info.source_size == 1024 + (1 << 31)
    assert info.source.stat().st_blocks * 512 < 1024 * 1024
    reject(api, tmp_path / "invalid.ome.tif", info, "imagej_unrepresentable")


@pytest.mark.parametrize("change", ["size", "mtime", "header"])
def test_source_changed_before_export(tmp_path: Path, api: Callable[..., Any], change: str) -> None:
    source, info, _ = input_info(tmp_path, Acquisition())
    before = source.stat()
    if change == "size":
        with source.open("ab") as stream:
            stream.write(b"x")
    elif change == "mtime":
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
    else:
        with source.open("r+b") as stream:
            stream.seek(300)
            stream.write(b"\xfe")
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    reject(api, tmp_path / "changed.ome.tif", info, "source_changed")


@pytest.mark.parametrize("destination_kind", ["existing", "source", "symlink", "directory"])
def test_exclusive_destination_preserves_existing_bytes(
    tmp_path: Path, api: Callable[..., Any], destination_kind: str
) -> None:
    source, info, _ = input_info(tmp_path, Acquisition())
    before = sha256(source), source.stat().st_mtime_ns
    destination = tmp_path / "occupied.ome.tif"
    sentinel = b"preserve this existing file\x00\xff"
    if destination_kind == "source":
        destination = source
    elif destination_kind == "directory":
        destination.mkdir()
    elif destination_kind == "symlink":
        target = tmp_path / "user-owned-target.bin"
        target.write_bytes(sentinel)
        destination.symlink_to(target)
    else:
        destination.write_bytes(sentinel)

    # Reads can change atime; only observe writer-relevant mtime and object
    # identity. lstat preserves the symlink itself; stat observes its target.
    def identity(path: Path, *, follow: bool) -> tuple[int, int, int]:
        state = path.stat() if follow else path.lstat()
        return state.st_dev, state.st_ino, state.st_mtime_ns

    occupied_before = identity(destination, follow=False), identity(destination, follow=True)
    with pytest.raises(OSError):
        api(destination, info)
    assert (sha256(source), source.stat().st_mtime_ns) == before
    assert (
        identity(destination, follow=False),
        identity(destination, follow=True),
    ) == occupied_before
    if destination_kind == "directory":
        assert destination.is_dir() and not list(destination.iterdir())
    elif destination_kind != "source":
        assert destination.read_bytes() == sentinel
        if destination_kind == "symlink":
            assert destination.is_symlink()


def test_missing_parent_ordinary_io_error(tmp_path: Path, api: Callable[..., Any]) -> None:
    _, info, _ = input_info(tmp_path, Acquisition())
    with pytest.raises(FileNotFoundError):
        api(tmp_path / "missing" / "copy.ome.tif", info)


def cli(
    source: Path, destination: Path, config: Path, *extra: str
) -> subprocess.CompletedProcess[str]:
    executable = Path(sys.executable).parent / "simrecon"
    result = subprocess.run(
        [
            str(executable),
            "export-imagej",
            str(source),
            str(destination),
            "--config",
            str(config),
            *extra,
        ],
        capture_output=True,
        timeout=180,
    )
    # Decode the captured UTF-8 bytes directly. Text mode normalizes legal JSON
    # whitespace line endings before the original stdout evidence is recorded.
    return subprocess.CompletedProcess(
        result.args,
        result.returncode,
        result.stdout.decode("utf-8"),
        result.stderr.decode("utf-8"),
    )


def test_cli_success_matches_library_report_and_actual_reader(
    tmp_path: Path, api: Callable[..., Any]
) -> None:
    spec = Acquisition(
        plane_axes=("phase", "orientation"),
        plane_shape=(3, 2),
        byte_order="big",
        overrides={"sampling_um": {"x": math.nextafter(0.1, 1.0)}},
    )
    source = tmp_path / "independent.priism"
    spec.write(source)
    # A real source identity beyond binary64's consecutive-integer precision;
    # acquire DatasetInfo only after setting and observing the filesystem value.
    os.utime(source, ns=(1 << 60, 1 << 60))
    assert source.stat().st_mtime_ns == 1 << 60
    config = spec.config()
    info = simrecon.harmonize(simrecon.inspect(source), config=config)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    output = tmp_path / "cli.ome.tif"
    result = cli(source, output, config_path, "--block-planes", "2")
    assert result.returncode == 0 and result.stderr == ""
    report = json_with_exact_numbers(result.stdout)
    assert set(report) == {
        "destination",
        "series",
        "series_count",
        "planes_written",
        "provenance",
        "limitations",
    }
    assert_values(report["destination"], str(output))
    assert_values(report["series_count"], 6)
    assert_values(report["planes_written"], 6)
    expected_series = [
        {
            "index": o * 3 + p,
            "name": spec.name(o, p),
            "orientation_index": o,
            "phase_index": p,
            "shape": list(spec.series_shape),
        }
        for o in range(2)
        for p in range(3)
    ]
    assert_values(report["series"], expected_series)
    assert_values(report["provenance"], finite_json(info.provenance))
    other = api(tmp_path / "library.ome.tif", info, block_planes=2)
    assert_report(other, tmp_path / "library.ome.tif", spec, info)
    assert_limitations_representation(other)
    assert isinstance(report["limitations"], list) and all(
        isinstance(text, str) for text in report["limitations"]
    )
    persist_report_observation(
        other,
        source,
        tmp_path / "library.ome.tif",
        config,
        spec,
        info,
        "cli-success-and-library",
        cli_report=report,
        cli_stdout=result.stdout,
    )
    assert_values(report["limitations"], list(other.limitations))
    assert_carrier(output, source, spec, info)
    record = observe(output, tmp_path / "reader")
    assert_observer(record, output, spec, info)
    persist_observation(record, source, output, config, "cli-success")


@pytest.mark.parametrize(
    "invalid,code,status",
    [
        ("config", "config_invalid", 2),
        ("layout", "layout_mismatch", 2),
        ("schema", "schema_required", 2),
        ("payload", "payload_size", 2),
        ("block", "invalid_block_size", 2),
        ("scale", "imagej_unrepresentable", 2),
        ("existing", "io_error", 1),
        ("missing-parent", "io_error", 1),
    ],
)
def test_cli_error_json_no_success_or_source_traceback(
    tmp_path: Path, invalid: str, code: str, status: int
) -> None:
    spec = Acquisition()
    source = tmp_path / "cli.priism"
    spec.write(source)
    config = spec.config()
    config_path = tmp_path / "config.json"
    output = tmp_path / "error.ome.tif"
    extra: tuple[str, ...] = ()
    if invalid == "layout":
        config["plane_shape"] = [1] * len(spec.plane_shape)
    elif invalid == "schema":
        config.pop("extended_header")
    elif invalid == "payload":
        with source.open("r+b") as stream:
            stream.truncate(source.stat().st_size - 1)
    elif invalid == "block":
        extra = ("--block-planes", "0")
    elif invalid == "scale":
        config["overrides"] = {"sampling_um": {"x": 1e39}}
    elif invalid == "existing":
        output.write_bytes(b"existing sentinel")
    elif invalid == "missing-parent":
        output = tmp_path / "missing" / "error.ome.tif"
    config_path.write_text("{" if invalid == "config" else json.dumps(config))
    source_before = sha256(source), source.stat().st_mtime_ns
    occupied_before = None
    if invalid == "existing":
        state = output.stat()
        occupied_before = state.st_dev, state.st_ino, state.st_mtime_ns
    result = cli(source, output, config_path, *extra)
    assert result.returncode == status, f"CLI status={result.returncode}; expected={status}"
    assert result.stdout == ""
    error = json.loads(result.stderr)
    assert error["code"] == code, f"CLI code={error['code']}; expected={code}"
    assert isinstance(error["message"], str)
    assert "Traceback" not in result.stderr
    assert (sha256(source), source.stat().st_mtime_ns) == source_before
    if invalid == "existing":
        assert output.read_bytes() == b"existing sentinel"
        state = output.stat()
        assert (state.st_dev, state.st_ino, state.st_mtime_ns) == occupied_before
    else:
        assert not output.exists()


def test_source_change_during_real_export_never_returns_success(
    tmp_path: Path, api: Callable[..., Any]
) -> None:
    import threading
    import time

    spec = Acquisition(plane_axes=("z",), plane_shape=(384,), x=512, y=512, extension=b"")
    source, info, _ = input_info(tmp_path, spec, sparse=True)
    output = tmp_path / "changing.ome.tif"
    changed, stop = threading.Event(), threading.Event()
    actor_errors: list[BaseException] = []

    def actor() -> None:
        try:
            deadline = time.monotonic() + 60
            while not stop.is_set() and time.monotonic() < deadline:
                if output.exists() and output.stat().st_size >= 8 * 1024 * 1024:
                    stat = source.stat()
                    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
                    changed.set()
                    return
                stop.wait(0.001)
        except BaseException as error:
            actor_errors.append(error)

    thread = threading.Thread(target=actor, name="owned-source-change", daemon=False)
    thread.start()
    try:
        with pytest.raises(simrecon.SimreconError) as error:
            api(output, info, block_planes=1)
        assert error.value.code == "source_changed"
    finally:
        stop.set()
        thread.join(timeout=5)
    assert not thread.is_alive() and not actor_errors
    assert changed.is_set(), "source-change actor did not exercise the public race"
    # Partial newly created output is permitted; this is no atomic snapshot claim.


def test_real_operation_time_write_failure(tmp_path: Path, api: Callable[..., Any]) -> None:
    # Both required platforms implement POSIX RLIMIT_FSIZE. Limit only the child,
    # ignore SIGXFSZ so a real write returns EFBIG rather than killing pytest.
    # Restore the prior limit after observation so native subprocess coverage can save.
    spec = Acquisition(plane_axes=("z",), plane_shape=(8,), x=64, y=64, extension=b"")
    source, _, config = input_info(tmp_path, spec)
    original = sha256(source), source.stat().st_mtime_ns
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    output = tmp_path / "limited.ome.tif"
    probe = tmp_path / "owned_write_limit.py"
    probe.write_text(
        "import errno, json, pathlib, resource, signal, simrecon, sys\n"
        "source, config_path, output = map(pathlib.Path, sys.argv[1:])\n"
        "info = simrecon.harmonize(simrecon.inspect(source), "
        "config=json.loads(config_path.read_text()))\n"
        "signal.signal(signal.SIGXFSZ, signal.SIG_IGN)\n"
        "original_soft, original_hard = resource.getrlimit(resource.RLIMIT_FSIZE)\n"
        "try:\n"
        "    resource.setrlimit(resource.RLIMIT_FSIZE, (8192, original_hard))\n"
        "    try:\n"
        "        simrecon.export_imagej(output, info)\n"
        "    except OSError as error:\n"
        "        print(json.dumps({'error_errno': error.errno, 'success': False}))\n"
        "    else:\n"
        "        raise AssertionError('operation-time write failure returned success')\n"
        "finally:\n"
        "    resource.setrlimit(resource.RLIMIT_FSIZE, (original_soft, original_hard))\n"
    )
    result = subprocess.run(
        [sys.executable, str(probe), str(source), str(config_path), str(output)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert_values(
        json_with_exact_numbers(result.stdout), {"error_errno": errno.EFBIG, "success": False}
    )
    assert (sha256(source), source.stat().st_mtime_ns) == original
    assert output.exists() and output.stat().st_size <= 8192


@pytest.mark.parametrize("block_planes", [1, 3])
def test_pixel_memory_and_opaque_hash_are_bounded(
    tmp_path: Path, api: Callable[..., Any], block_planes: int
) -> None:
    import numpy as np

    # 192 MiB source pixels; 128 MiB opaque extension. Total pixels grow by 24x.
    # The bound deliberately permits growing TIFF/XML metadata (~384 planes),
    # interpreter overhead and several bounded encoding buffers. It is measured
    # Python/NumPy allocation, not an assertion about constant total RSS.
    tracemalloc.start()
    calibration_array = np.empty((512, 512), dtype=np.uint16)
    measured, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert measured >= calibration_array.nbytes, "resource observer missed NumPy pixel storage"
    del calibration_array
    peaks = []
    mapped_sizes: list[int] = []
    active: dict[str, Any] = {}

    def audit_mmap(event: str, arguments: tuple[Any, ...]) -> None:
        if event != "mmap.__new__" or not active:
            return
        fileno, length = arguments[:2]
        stat = os.fstat(fileno) if fileno >= 0 else None
        if stat is not None and (stat.st_dev, stat.st_ino) == active["identity"]:
            actual_length = length or stat.st_size
            mapped_sizes.append(actual_length)
            assert actual_length <= active["max_bytes"], "whole source mapping exceeds pixel bound"

    # The native audit event also sees previously imported constructor aliases.
    # Hooks cannot be removed, so this owned observer becomes inert in finally.
    sys.addaudithook(audit_mmap)
    for count in (16, 384):
        case = tmp_path / f"planes-{count}"
        case.mkdir()
        spec = Acquisition(
            plane_axes=("z",),
            plane_shape=(count,),
            x=512,
            y=512,
            extension=b"",
        )
        source = case / "independent.priism"
        extension_hash = sparse_extension_source(source, spec, 128 * 1024 * 1024)
        config = spec.config()
        config["extended_header"] = "opaque"
        info = simrecon.harmonize(simrecon.inspect(source), config=config)
        source_identity = source.stat().st_dev, source.stat().st_ino

        active.update(
            identity=source_identity,
            max_bytes=8 * block_planes * spec.x * spec.y * spec.itemsize,
        )
        tracemalloc.start()
        try:
            report = api(case / "bounded.ome.tif", info, block_planes=block_planes)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            active.clear()
            tracemalloc.stop()
        assert_report(report, case / "bounded.ome.tif", spec, info)
        assert report.planes_written == count
        assert_limitations_representation(report)
        persist_report_observation(
            report,
            source,
            case / "bounded.ome.tif",
            config,
            spec,
            info,
            f"resource-planes{count}-block{block_planes}",
        )
        # 64 MiB excludes the 192 MiB whole-pixel allocation while allowing
        # plane-dependent carrier metadata, extension hashing and normal scratch.
        assert peak < 64 * 1024 * 1024
        peaks.append(peak)
        with tifffile.TiffFile(case / "bounded.ome.tif") as tif:
            assert len(tif.pages) == count
            first_page = tif.pages[0]
            assert isinstance(first_page, tifffile.TiffPage)
            xml = ET.fromstring(first_page.description)
            metadata, _ = project_metadata(xml, xml.findall(Q + "Image"))
            assert metadata["original_extension"]["sha256"] == extension_hash.hex()
            assert metadata["original_extension"]["content_retained"] is False
        # mmap requests may be absent or per-block; neither requires an invented
        # implementation call count or forbids a bounded legitimate alternative.
    assert peaks[1] - peaks[0] < 32 * 1024 * 1024
    assert all(length <= 8 * block_planes * 512 * 512 * 2 for length in mapped_sizes)
