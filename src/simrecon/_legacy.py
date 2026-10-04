"""Independent, header-only intake for the approved Priism subset."""

import hashlib
import math
import struct
from pathlib import Path

import numpy as np

from ._model import DatasetInfo, SimreconError


def inspect(source: str | Path) -> DatasetInfo:
    source = Path(source)
    stat = source.stat()
    with source.open("rb") as handle:
        header = handle.read(1024)
    if len(header) != 1024:
        raise SimreconError("invalid_header", "The source needs a complete 1024-byte header")
    if struct.unpack_from("<h", header, 96)[0] == -16224:
        endian, byte_order = "<", "little"
    elif struct.unpack_from(">h", header, 96)[0] == -16224:
        endian, byte_order = ">", "big"
    else:
        raise SimreconError("unsupported_format", "The legacy identifier is absent")
    x, y, n, mode = struct.unpack_from(endian + "4i", header)
    extension = struct.unpack_from(endian + "i", header, 92)[0]
    if min(x, y, n) <= 0 or extension < 0:
        raise SimreconError(
            "invalid_header", "Dimensions must be positive and extension nonnegative"
        )
    dtype = {6: np.dtype("uint16"), 2: np.dtype("float32")}.get(mode)
    # Known unsupported MRC modes still have a structural payload size.
    itemsize = {0: 1, 1: 2, 2: 4, 3: 4, 4: 8, 6: 2, 12: 2, 16: 3}.get(mode)
    if stat.st_size < 1024 + extension or (
        itemsize is not None and stat.st_size != 1024 + extension + x * y * n * itemsize
    ):
        raise SimreconError("payload_size", "Source length disagrees with the declared payload")
    spatial = struct.unpack_from(endian + "3f", header, 40)
    metadata = {
        "grid": struct.unpack_from(endian + "3i", header, 28),
        "spatial_fields": tuple(
            finite_value(value, header[40 + i * 4 : 44 + i * 4]) for i, value in enumerate(spatial)
        ),
        "map_axes": struct.unpack_from(endian + "3i", header, 64),
        "time_count": struct.unpack_from(endian + "h", header, 180)[0],
        "image_sequence": struct.unpack_from(endian + "h", header, 182)[0],
        "channel_count": struct.unpack_from(endian + "h", header, 196)[0],
        "wavelength_slots": struct.unpack_from(endian + "5h", header, 198),
        "extension_integer_fields": struct.unpack_from(endian + "h", header, 128)[0],
        "extension_float_fields": struct.unpack_from(endian + "h", header, 130)[0],
    }
    sampling = {
        axis: value if math.isfinite(value) else None
        for axis, value in zip(("x", "y", "z"), spatial, strict=True)
    }
    wavelengths = {str(i): v for i, v in enumerate(metadata["wavelength_slots"]) if v > 0}
    return DatasetInfo(
        source,
        stat.st_size,
        stat.st_mtime_ns,
        hashlib.sha256(header).hexdigest(),
        header,
        (n, y, x),
        mode,
        dtype,
        None,
        byte_order,
        extension,
        metadata,
        ("acquisition_config", "extension_schema") if extension else ("acquisition_config",),
        ("section", "y", "x"),
        (n, y, x),
        None,
        sampling,
        wavelengths,
        (),
    )


def check_source(info: DatasetInfo) -> None:
    stat = info.source.stat()
    with info.source.open("rb") as handle:
        digest = hashlib.sha256(handle.read(1024)).hexdigest()
    if (stat.st_size, stat.st_mtime_ns, digest) != (
        info.source_size,
        info.source_mtime_ns,
        info.header_sha256,
    ):
        raise SimreconError("source_changed", "Source identity changed since inspection")


def finite_value(value: float, raw: bytes) -> object:
    """Retain nonfinite header words without emitting nonstandard JSON numbers."""
    return value if math.isfinite(value) else {"unresolved": "nonfinite", "ieee_bytes": raw.hex()}
