"""Selected canonical reads without arithmetic on pixel words."""

from typing import BinaryIO

import numpy as np

from ._legacy import check_source
from ._metadata import coordinate, resolved, source_index
from ._model import DataBlock, DatasetInfo, SimreconError


def load_block(handle: BinaryIO, info: DatasetInfo, start: int, stop: int) -> DataBlock:
    data = np.empty((stop - start, *info.stored_shape[1:]), dtype=info.stored_dtype)
    coordinates = tuple(coordinate(info, i) for i in range(start, stop))
    plane_bytes = data[0].nbytes
    word_dtype = np.dtype(f"u{data.dtype.itemsize}")
    source_order = {"little": "<", "big": ">"}[info.byte_order]
    source_dtype = np.dtype(f"{source_order}u{data.dtype.itemsize}")
    for plane, coord in zip(data, coordinates, strict=True):
        handle.seek(1024 + info.extended_header_bytes + source_index(info, coord) * plane_bytes)
        raw = handle.read(plane_bytes)
        if len(raw) != plane_bytes:
            raise SimreconError("source_changed", "Source payload shortened during reading")
        # Convert unsigned words, so float32 NaN payloads never enter float arithmetic.
        plane.view(word_dtype).reshape(-1)[:] = np.frombuffer(raw, dtype=source_dtype)
    return DataBlock(data, info, range(start, stop), coordinates)


def read(info: DatasetInfo, *, plane_start: int, plane_stop: int) -> DataBlock:
    resolved(info)
    if (
        type(plane_start) is not int
        or type(plane_stop) is not int
        or not 0 <= plane_start < plane_stop <= info.stored_shape[0]
    ):
        raise SimreconError("invalid_selection", "Select a nonempty interval within stored planes")
    check_source(info)
    with info.source.open("rb") as handle:
        return load_block(handle, info, plane_start, plane_stop)
