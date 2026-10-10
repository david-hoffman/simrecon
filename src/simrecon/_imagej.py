"""Stream a file-source acquisition into an all-settings Fiji viewing copy."""

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tifffile

from ._imagej_metadata import UINT64_MAX, copy_metadata, ome_xml, setting_name, validate
from ._legacy import check_source
from ._model import DatasetInfo, SimreconError
from ._pixels import read


@dataclass(frozen=True)
class ImagejSeries:
    """One orientation/phase setting with actual T/C/Z/Y/X dimensions."""

    index: int
    name: str
    orientation_index: int | None
    phase_index: int | None
    shape: tuple[int, int, int, int, int]


@dataclass(frozen=True)
class ImagejWriteReport:
    """Completed viewing-copy export and its metadata/viewer limitations."""

    destination: Path
    series: tuple[ImagejSeries, ...]
    series_count: int
    planes_written: int
    provenance: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]


LIMITATIONS = (
    "Opaque extension content is omitted; only its length and SHA256 are retained. "
    "Keep the original source to recover any opaque bytes. The copy retains the exact main "
    "header and logical/interpreted metadata, but is not a standalone original-metadata archive.",
    "An absent Z axis uses SizeZ=1 without physical Z; viewer depth defaults do not establish "
    "acquired or physical Z. Declared singleton axes remain declared in copy metadata. "
    "No time interval or timestamp is known from this export; viewer time defaults establish "
    "no acquired time for an absent time axis and no measured timing for a declared one.",
    "Orientation and phase labels are zero-based setting ordinals, with absent axes labelled "
    "absent. They assign neither physical orientation angles nor physical phase offsets.",
    "Stored TIFF and raw-reader pixels preserve every source bit after endian normalization. "
    "For float32, JVM float transfer may change NaN payload/signalling details; ImageJ preserves "
    "NaN classification, finite values, signed zero and infinity sign. uint16 remains unsigned.",
    "The tested reader path is Bio-Formats 8.5.0 with ImageJ 1.54p: open all series, Grayscale, "
    "Hyperstack, XYCZT, with concatenation and splitting disabled, yielding separate setting "
    "ImagePlus objects. This does not claim execution of the Fiji graphical interface.",
    "Pixel buffers are bounded by block_planes times one XY plane, with bounded encoding "
    "scratch; opaque hashing uses bounded chunks. TIFF directories and OME metadata grow with "
    "plane/series count. BigTIFF offsets do not guarantee viewer RAM capacity or throughput.",
    "Source size, modification time and main-header digest are checked before access and at "
    "completion. This is not an atomic snapshot and cannot detect every same-size, "
    "same-timestamp concurrent payload edit. A later failure may leave a partial new file; "
    "there is no automatic deletion, atomic publication or crash-durability guarantee.",
)


def export_imagej(
    destination: str | Path, info: DatasetInfo, *, block_planes: int = 1
) -> ImagejWriteReport:
    """Export all illumination settings as scalar uncompressed OME-BigTIFF series.

    Parameters
    ----------
    destination : str or Path
        New destination; existing paths are never replaced.
    info : DatasetInfo
        Harmonized supported Priism file-source descriptor.
    block_planes : int, optional
        Positive upper bound on selected pixel-buffer planes. The writer uses
        one-plane reads to handle arbitrary source and output ordering.

    Returns
    -------
    ImagejWriteReport
        Completed export, setting records, provenance and explicit limitations.
    """
    layout = validate(info, block_planes)
    destination = Path(destination)
    check_source(info)
    metadata = copy_metadata(info, layout)
    description = ome_xml(info, layout, metadata)
    planes = layout.series_count * layout.planes_per_series
    itemsize = 2 if info.pixel_mode == 6 else 4
    # A scalar single-strip page uses far less than 4096 bytes of tags/alignment.
    # Include the complete XML before creation. Valid signed32 source counts and
    # plane bytes keep the pixel product below 2**62; Python integer math cannot wrap.
    upper_size = 16 + len(description) + 1 + planes * (layout.x * layout.y * itemsize + 4096)
    if upper_size > UINT64_MAX:
        raise SimreconError("imagej_unrepresentable", "BigTIFF offsets exceed unsigned64")
    series = []
    with (
        destination.open("xb") as handle,
        tifffile.TiffWriter(handle, bigtiff=True, byteorder="<", ome=False) as writer,
    ):
        for o in range(layout.o):
            for p in range(layout.p):
                index = o * layout.p + p
                orientation = o if "orientation" in info.axes else None
                phase = p if "phase" in info.axes else None
                series.append(
                    ImagejSeries(
                        index, setting_name(orientation, phase), orientation, phase, layout.shape
                    )
                )
                for n in range(layout.planes_per_series):
                    source_plane = layout.source_plane(o, p, n)
                    block = read(info, plane_start=source_plane, plane_stop=source_plane + 1)
                    # Normalize integer words, never floating values (NaN payloads).
                    words = block.data[0].view(np.dtype(f"u{itemsize}"))
                    little_words = words.astype(np.dtype(f"<u{itemsize}"), copy=False)
                    # The bytes iterator uses ordinary file writes, retaining
                    # OS errno on failure instead of NumPy's tofile wrapper.
                    writer.write(
                        iter((little_words.tobytes(),)),
                        shape=(layout.y, layout.x),
                        dtype=np.dtype("<u2" if itemsize == 2 else "<f4"),
                        photometric="minisblack",
                        compression=None,
                        metadata=None,
                        description=description if index == 0 and n == 0 else None,
                        rowsperstrip=layout.y,
                        software="simrecon",
                    )
    check_source(info)
    return ImagejWriteReport(
        destination,
        tuple(series),
        layout.series_count,
        planes,
        copy.deepcopy(info.provenance),
        LIMITATIONS,
    )
