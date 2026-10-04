"""Bounded MRC2014 writer with a self-contained HDF5 metadata image."""

import json
import math
import shutil
import struct
import tempfile
from pathlib import Path
from typing import Any, cast

import h5py
import numpy as np

from ._legacy import check_source
from ._metadata import resolved
from ._model import DatasetInfo, SimreconError, WriteReport
from ._pixels import load_block

CHUNK = 1024 * 1024
LABEL = b"SIMrecon stack; axial scale unknown; see HDF5 metadata"
LIMITATIONS = (
    "Generic readers see a flattened stack with unknown axial scale.",
    "Named acquisition axes require the embedded HDF5 metadata; ImageJ integration is deferred.",
)


def metadata(info: DatasetInfo) -> dict[str, Any]:
    return {
        "schema": "org.simrecon.mrc-metadata",
        "version": 1,
        "data_kind": info.data_kind,
        "logical_axes": info.axes,
        "logical_shape": info.shape,
        "source_layout": {
            "plane_axes": cast(dict[str, Any], info.config)["plane_axes"],
            "plane_shape": cast(dict[str, Any], info.config)["plane_shape"],
            "byte_order": info.byte_order,
            "pixel_mode": info.pixel_mode,
        },
        "output_layout": {
            "plane_axes": info.axes[:-2],
            "plane_shape": info.shape[:-2],
            "section_count": info.stored_shape[0],
        },
        "sampling_um": info.sampling_um,
        "wavelengths_nm": info.wavelengths_nm,
        "acquisition_config": info.config,
        "provenance": info.provenance,
        "main_header_axial_scale": "unknown_flattened_stack_zero_angstrom",
        "original_extension_schema": "opaque" if info.extended_header_bytes else "none",
    }


def header(info: DatasetInfo, extension_size: int) -> bytes:
    n, y, x = info.stored_shape
    lengths = [
        size * cast(float, info.sampling_um[axis]) * 10000 for size, axis in ((x, "x"), (y, "y"))
    ]
    if any(v <= 0 or v > float(np.finfo(np.float32).max) or not math.isfinite(v) for v in lengths):
        raise SimreconError(
            "header_unrepresentable", "Lateral cell lengths must fit positive finite float32"
        )
    packed = struct.pack("<2f", *lengths)
    if any(v <= 0 for v in struct.unpack("<2f", packed)):
        raise SimreconError("header_unrepresentable", "Lateral cell lengths underflow float32")
    if extension_size > 2**31 - 1:
        raise SimreconError(
            "header_unrepresentable", "HDF5 extension exceeds signed 32-bit storage"
        )
    result = bytearray(1024)
    struct.pack_into("<4i", result, 0, x, y, n, info.pixel_mode)
    struct.pack_into("<3i", result, 28, x, y, 1)
    result[40:48] = packed
    struct.pack_into("<3f", result, 52, 90, 90, 90)
    struct.pack_into("<3i", result, 64, 1, 2, 3)
    struct.pack_into("<3f", result, 76, 0, -1, -2)
    struct.pack_into("<i", result, 92, extension_size)
    result[104:108] = b"HDF5"
    struct.pack_into("<i", result, 108, 20141)
    result[208:216] = b"MAP DD\x00\x00"
    struct.pack_into("<f", result, 216, -1)
    struct.pack_into("<i", result, 220, 1)
    result[224 : 224 + len(LABEL)] = LABEL
    return bytes(result)


def stage_metadata(path: Path, info: DatasetInfo) -> int:
    encoded = json.dumps(
        metadata(info), allow_nan=False, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    with h5py.File(path, "w") as container, info.source.open("rb") as source:
        group = container.create_group("simrecon")
        group.create_dataset("metadata_json", data=np.frombuffer(encoded, dtype=np.uint8))
        group.create_dataset(
            "original_header", data=np.frombuffer(info.original_header, dtype=np.uint8)
        )
        extension = group.create_dataset(
            "original_extended_header", (info.extended_header_bytes,), dtype="u1"
        )
        source.seek(1024)
        for start in range(0, info.extended_header_bytes, CHUNK):
            size = min(CHUNK, info.extended_header_bytes - start)
            raw = source.read(size)
            if len(raw) != size:
                raise SimreconError("source_changed", "Source extension shortened during reading")
            extension[start : start + size] = np.frombuffer(raw, dtype=np.uint8)
    return path.stat().st_size


def write(destination: str | Path, info: DatasetInfo, *, block_planes: int = 1) -> WriteReport:
    resolved(info)
    if type(block_planes) is not int or block_planes <= 0:
        raise SimreconError("invalid_block_size", "Block plane count must be a positive integer")
    check_source(info)
    destination = Path(destination)
    # Exclusive creation is the no-overwrite guarantee, including source-as-destination.
    with (
        destination.open("xb") as output,
        tempfile.TemporaryDirectory(prefix="simrecon-") as scratch,
    ):
        staged = Path(scratch) / "metadata.h5"
        size = stage_metadata(staged, info)
        padded = (size + 3) // 4 * 4
        output.write(header(info, padded))
        with staged.open("rb") as extension:
            shutil.copyfileobj(extension, output, CHUNK)
        output.write(b"\x00" * (padded - size))
        with info.source.open("rb") as source:
            for start in range(0, info.stored_shape[0], block_planes):
                block = load_block(
                    source, info, start, min(start + block_planes, info.stored_shape[0])
                )
                words = block.data.view(np.dtype(f"u{block.data.dtype.itemsize}"))
                encoded = words.astype(words.dtype.newbyteorder("<"), copy=False)
                output.write(memoryview(encoded).cast("B"))
    check_source(info)
    return WriteReport(
        destination,
        info.stored_shape,
        info.pixel_mode,
        info.stored_shape[0],
        info.provenance,
        LIMITATIONS,
    )
