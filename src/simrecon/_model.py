"""Value records shared by the conversion interfaces."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


class SimreconError(ValueError):
    """An expected conversion failure with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class DatasetInfo:
    source: Path
    source_size: int
    source_mtime_ns: int
    header_sha256: str
    original_header: bytes
    stored_shape: tuple[int, int, int]
    pixel_mode: int
    stored_dtype: np.dtype | None
    data_kind: str | None
    byte_order: str
    extended_header_bytes: int
    file_metadata: dict[str, Any]
    unresolved: tuple[str, ...]
    axes: tuple[str, ...]
    shape: tuple[int, ...]
    config: dict[str, Any] | None
    sampling_um: dict[str, float | None]
    wavelengths_nm: dict[str, float]
    provenance: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class DataBlock:
    data: np.ndarray
    info: DatasetInfo
    plane_indices: range
    coordinates: tuple[dict[str, int], ...]


@dataclass(frozen=True)
class WriteReport:
    destination: Path
    stored_shape: tuple[int, int, int]
    pixel_mode: int
    planes_written: int
    provenance: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]
