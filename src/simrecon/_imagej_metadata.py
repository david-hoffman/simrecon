"""OME carrier layout and recoverable, source-referenced copy metadata."""

import base64
import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from ._metadata import ORDER, resolved
from ._model import DatasetInfo, SimreconError

OME_NS = "http://www.openmicroscopy.org/Schemas/OME/2016-06"
COPY_NS = "org.simrecon.imagej-copy"
INT32_MAX = 2**31 - 1
UINT64_MAX = 2**64 - 1


@dataclass(frozen=True)
class Layout:
    """Factored acquisition counts, with absent carrier axes of size one."""

    t: int
    c: int
    o: int
    p: int
    z: int
    y: int
    x: int

    @property
    def shape(self) -> tuple[int, int, int, int, int]:
        return self.t, self.c, self.z, self.y, self.x

    @property
    def series_count(self) -> int:
        return self.o * self.p

    @property
    def planes_per_series(self) -> int:
        return self.t * self.z * self.c

    def source_plane(self, o: int, p: int, n: int) -> int:
        """Map a C-fastest output plane to the public canonical read index."""
        t, remainder = divmod(n, self.c * self.z)
        z, c = divmod(remainder, self.c)
        return (((t * self.c + c) * self.o + o) * self.p + p) * self.z + z


def validate(info: DatasetInfo, block_planes: int) -> Layout:
    """Reject unsupported descriptors and carrier limits before file creation."""
    resolved(info)
    if type(block_planes) is not int or block_planes <= 0:
        raise SimreconError("invalid_block_size", "block_planes must be a positive integer")
    canonical = tuple(a for a in ORDER if a in info.axes) + ("y", "x")
    if info.data_kind != "spatial_image" or info.unresolved or info.axes != canonical:
        raise SimreconError("unsupported_axes", "A harmonized spatial-image layout is required")
    sizes = dict(zip(info.axes, info.shape, strict=True))
    layout = Layout(*(sizes.get(a, 1) for a in (*ORDER, "y", "x")))
    # Source dimensions/sections are signed32. Factored setting and plane counts
    # cannot exceed their source section product; check the carrier explicitly.
    counts = (*layout.shape, layout.series_count, layout.planes_per_series)
    if any(not 0 < n <= INT32_MAX for n in counts):
        raise SimreconError("imagej_unrepresentable", "OME counts must fit positive signed32")
    itemsize = 2 if info.pixel_mode == 6 else 4
    if layout.x * layout.y * itemsize > INT32_MAX:
        raise SimreconError("imagej_unrepresentable", "XY plane bytes exceed Java indexing")
    for axis in ("x", "y", "z") if "z" in info.axes else ("x", "y"):
        value = info.sampling_um[axis]
        try:
            rounded = struct.unpack("<f", struct.pack("<f", value))[0]  # type: ignore[arg-type]
        except (OverflowError, struct.error):
            rounded = math.inf
        if not math.isfinite(rounded) or rounded <= 0:
            raise SimreconError(
                "imagej_unrepresentable", "OME physical sizes must round to positive finite float32"
            )
    return layout


def copy_metadata(info: DatasetInfo, layout: Layout) -> str:
    """Copy public metadata and hash opaque bytes in bounded chunks."""
    digest = hashlib.sha256()
    with info.source.open("rb") as handle:
        handle.seek(1024)
        remaining = info.extended_header_bytes
        while remaining:
            chunk = handle.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise SimreconError("source_changed", "Source extension shortened during hashing")
            digest.update(chunk)
            remaining -= len(chunk)
    assert info.config is not None
    metadata: dict[str, Any] = {
        "schema": COPY_NS,
        "version": 1,
        "data_kind": info.data_kind,
        "logical_axes": info.axes,
        "logical_shape": info.shape,
        "source_layout": {
            "plane_axes": info.config["plane_axes"],
            "plane_shape": info.config["plane_shape"],
            "byte_order": info.byte_order,
            "pixel_mode": info.pixel_mode,
        },
        "stored_shape": info.stored_shape,
        "sampling_um": info.sampling_um,
        "wavelengths_nm": info.wavelengths_nm,
        "acquisition_config": info.config,
        "file_metadata": info.file_metadata,
        "unresolved": info.unresolved,
        "provenance": info.provenance,
        "source_identity": {
            "source_name": info.source.name,
            "source_size": info.source_size,
            "source_mtime_ns": info.source_mtime_ns,
            "header_sha256": info.header_sha256,
        },
        "original_header_base64": base64.b64encode(info.original_header).decode("ascii"),
        "original_extension": {
            "schema": "opaque" if info.extended_header_bytes else "none",
            "bytes": info.extended_header_bytes,
            "sha256": digest.hexdigest(),
            "content_retained": False,
        },
        "series_layout": {
            "series_order": "orientation_phase",
            "plane_order": "XYCZT",
            "series_count": layout.series_count,
            "per_series_shape": layout.shape,
            "orientation_count": layout.o,
            "phase_count": layout.p,
            **{
                a + "_present": a in info.axes
                for a in ("orientation", "phase", "z", "channel", "time")
            },
        },
    }
    return json.dumps(metadata, allow_nan=False, sort_keys=True, separators=(",", ":"))


def setting_name(o: int | None, p: int | None) -> str:
    """Name ordinals without assigning physical angles or phase offsets."""
    return (
        f"orientation={o if o is not None else 'absent'}; phase={p if p is not None else 'absent'}"
    )


def ome_xml(info: DatasetInfo, layout: Layout, metadata: str) -> bytes:
    """Build explicit OME2016-06 mappings for every single-file image plane."""
    root = ET.Element("OME", {"xmlns": OME_NS})
    for o in range(layout.o):
        for p in range(layout.p):
            s = o * layout.p + p
            image = ET.SubElement(
                root,
                "Image",
                ID=f"Image:{s}",
                Name=setting_name(
                    o if "orientation" in info.axes else None,
                    p if "phase" in info.axes else None,
                ),
            )
            attributes = {
                "ID": f"Pixels:{s}",
                "DimensionOrder": "XYCZT",
                "Type": "uint16" if info.pixel_mode == 6 else "float",
                "BigEndian": "false",
                **{f"Size{a}": str(n) for a, n in zip("TCZYX", layout.shape, strict=True)},
            }
            for axis in ("x", "y", "z") if "z" in info.axes else ("x", "y"):
                attributes["PhysicalSize" + axis.upper()] = repr(info.sampling_um[axis])
                attributes["PhysicalSize" + axis.upper() + "Unit"] = "µm"
            pixels = ET.SubElement(image, "Pixels", attributes)
            for c in range(layout.c):
                ET.SubElement(
                    pixels,
                    "Channel",
                    ID=f"Channel:{s}:{c}",
                    Name=f"channel={c}",
                    SamplesPerPixel="1",
                )
            for n in range(layout.planes_per_series):
                t, remainder = divmod(n, layout.c * layout.z)
                z, c = divmod(remainder, layout.c)
                ET.SubElement(
                    pixels,
                    "TiffData",
                    IFD=str(s * layout.planes_per_series + n),
                    FirstZ=str(z),
                    FirstC=str(c),
                    FirstT=str(t),
                    PlaneCount="1",
                )
            ET.SubElement(image, "AnnotationRef", ID="Annotation:0")
    annotations = ET.SubElement(root, "StructuredAnnotations")
    annotation = ET.SubElement(annotations, "MapAnnotation", ID="Annotation:0", Namespace=COPY_NS)
    value = ET.SubElement(annotation, "Value")
    ET.SubElement(value, "M", K="metadata_json").text = metadata
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
