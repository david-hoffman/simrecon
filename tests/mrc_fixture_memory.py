"""Fresh-process M25 native RSS and independent all-plane verification."""

from __future__ import annotations

import importlib
import json
import linecache
import resource
import struct
import sys
import traceback
import warnings
from pathlib import Path
from typing import Any, cast

linecache.getline = lambda *args, **kwargs: ""


def showwarning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: object = None,
    line: str | None = None,
) -> None:
    print(f"{filename}:{lineno}: {category.__name__}: {message}", file=sys.stderr)


warnings.showwarning = showwarning


def main() -> None:
    import h5py
    import numpy as np

    simrecon: Any = importlib.import_module("simrecon")

    directory = Path(sys.argv[1])
    source = directory / "large.mrc"
    dest = directory / "large-output.mrc"
    # Warm the independent dependencies before the after-import high-water baseline.
    with h5py.File(directory / "warm.h5", "w") as f:
        f.create_dataset("warm", data=np.arange(8))
    baseline = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert sys.platform == "darwin" or sys.platform.startswith("linux")
    units = "bytes" if sys.platform == "darwin" else "KiB"
    native_byte_unit = 1 if units == "bytes" else 1024
    baseline_bytes = baseline * native_byte_unit
    limit_bytes = 32 * 1024 * 1024
    plane_bytes = 1024 * 256 * 2
    # H is historical, not current RSS. A fully resident payload A implies
    # peak >= A, so A > H + L forces peak - H > L even if current RSS is zero.
    # Choose the smallest whole-plane witness supported by that conservative bound.
    planes = (baseline_bytes + limit_bytes) // plane_bytes + 1
    payload_bytes = planes * plane_bytes
    assert 0 < planes <= 2**31 - 1, "M25 witness does not fit the native MRC section field"
    assert baseline_bytes >= 0
    assert payload_bytes > baseline_bytes + limit_bytes, "M25 memory witness is inapplicable"
    assert (planes - 1) * plane_bytes <= baseline_bytes + limit_bytes
    print(
        "M25 witness: "
        + json.dumps(
            dict(
                baseline_bytes=baseline_bytes,
                plane_bytes=plane_bytes,
                planes=planes,
                payload_bytes=payload_bytes,
                limit_bytes=limit_bytes,
                whole_payload_min_increment_bytes=payload_bytes - baseline_bytes,
            )
        ),
        file=sys.stderr,
        flush=True,
    )
    cfg = dict(
        version=1,
        data_kind="spatial_image",
        plane_axes=["time"],
        plane_shape=[planes],
        spatial_fields="direct_um",
        extended_header="opaque",
        overrides={},
    )
    extension_size = 64 * 1024 * 1024
    header = bytearray(1024)
    struct.pack_into("<4i", header, 0, 1024, 256, planes, 6)
    struct.pack_into("<3i", header, 28, 1024, 256, planes)
    struct.pack_into("<3f", header, 40, 0.125, 0.25, 0.5)
    struct.pack_into("<3i", header, 64, 1, 2, 3)
    struct.pack_into("<i", header, 92, extension_size)
    struct.pack_into("<h", header, 96, -16224)
    struct.pack_into("<h", header, 180, 1)
    struct.pack_into("<h", header, 196, 1)
    chunk = bytes(range(256)) * 4096
    ramp = np.arange(256 * 1024, dtype=np.uint32).reshape(256, 1024)
    with source.open("wb") as f:
        f.write(header)
        for _ in range(extension_size // len(chunk)):
            f.write(chunk)
        for i in range(planes):
            f.write(((ramp + i * 37) % 65536).astype("<u2").tobytes())
    info = simrecon.harmonize(simrecon.inspect(source), config=cfg)
    report = simrecon.write(dest, info, block_planes=1)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    increment_bytes = (peak - baseline) * native_byte_unit
    print(
        json.dumps(
            dict(baseline=baseline, peak=peak, units=units, increment_bytes=increment_bytes)
        ),
        flush=True,
    )
    assert increment_bytes <= limit_bytes
    assert report.planes_written == planes
    with dest.open("rb") as f:
        modern = f.read(1024)
        n = struct.unpack_from("<i", modern, 92)[0]
        assert struct.unpack_from("<4i", modern) == (1024, 256, planes, 6)
        with (directory / "extension.h5").open("wb") as extracted:
            left = n
            while left:
                block = f.read(min(left, 1024 * 1024))
                assert block
                extracted.write(block)
                left -= len(block)
        for i in range(planes):
            expected = ((ramp + i * 37) % 65536).astype("<u2").tobytes()
            assert f.read(len(expected)) == expected, f"plane {i}"
        assert f.read(1) == b""
    with h5py.File(directory / "extension.h5", "r") as f:
        for name in ("metadata_json", "original_header", "original_extended_header"):
            dataset = f[f"simrecon/{name}"]
            assert isinstance(dataset, h5py.Dataset)
            if dataset.is_virtual:
                assert all(v.file_name in (".", b".") for v in dataset.virtual_sources())
            assert dataset.external is None and dataset.compression is None
            assert not dataset.shuffle and not dataset.fletcher32 and dataset.scaleoffset is None
            assert isinstance(f.get(f"simrecon/{name}", getlink=True), h5py.HardLink)
        assert bytes(cast(h5py.Dataset, f["simrecon/original_header"])[:]) == header
        d = cast(h5py.Dataset, f["simrecon/original_extended_header"])
        assert d.shape == (extension_size,)
        for start in range(0, extension_size, len(chunk)):
            assert bytes(d[start : start + len(chunk)]) == chunk
        meta = json.loads(bytes(cast(h5py.Dataset, f["simrecon/metadata_json"])[:]))
        assert meta["source_layout"]["plane_shape"] == [planes]
        assert meta["output_layout"]["section_count"] == planes
        assert meta["original_extension_schema"] == "opaque"


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        for frame in traceback.extract_tb(exc.__traceback__):
            print(f"{frame.filename}:{frame.lineno}: {frame.name}", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
