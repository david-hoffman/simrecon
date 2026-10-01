"""Independent offset, mixed-radix and IEEE-word oracles for M01–M26."""

from __future__ import annotations

import itertools
import json
import struct
from pathlib import Path
from typing import Any, cast

import h5py
import mrcfile
import numpy as np

ORDER = ("time", "channel", "orientation", "phase", "z")
LABEL = b"SIMrecon stack; axial scale unknown; see HDF5 metadata"


def config(
    axes: tuple[str, ...] = ("orientation", "phase"),
    shape: tuple[int, ...] = (3, 3),
    *,
    opaque: bool = False,
) -> dict[str, Any]:
    return dict(
        version=1,
        data_kind="spatial_image",
        plane_axes=list(axes),
        plane_shape=list(shape),
        spatial_fields="direct_um",
        extended_header="opaque" if opaque else "none",
        overrides={},
    )


def coordinates(cfg: dict[str, Any], canonical: bool = True) -> list[dict[str, int]]:
    axes = cfg["plane_axes"]
    sizes = dict(zip(axes, cfg["plane_shape"], strict=True))
    names = [a for a in ORDER if a in axes] if canonical else axes
    return [
        dict(zip(names, c, strict=True))
        for c in itertools.product(*(range(sizes[a]) for a in names))
    ]


def plane(c: dict[str, int], y: int, x: int, mode: int) -> np.ndarray:
    base = sum(c.get(a, 0) * w for a, w in zip(ORDER, (4096, 2048, 512, 64, 16), strict=True))
    values = 40000 + base + np.arange(y)[:, None] * x + np.arange(x)[None, :]
    return values.astype(np.uint16) if mode == 6 else (-values / 8).astype(np.float32)


def fixture(
    path: Path,
    cfg: dict[str, Any],
    *,
    endian: str = "<",
    mode: int = 6,
    y: int = 3,
    x: int = 5,
    extension: bytes = b"",
    words: list[int] | None = None,
    sampling: tuple[float, float, float] = (0.0975, 0.125, 0.75),
) -> bytes:
    header = bytearray(1024)

    def pack(offset: int, fmt: str, *values: int | float) -> None:
        struct.pack_into(endian + fmt, header, offset, *values)

    n = len(coordinates(cfg, False))
    pack(0, "4i", x, y, n, mode)
    pack(28, "3i", x, y, n)
    pack(40, "3f", *sampling)
    pack(64, "3i", 1, 2, 3)
    pack(92, "i", len(extension))
    pack(96, "h", -16224)
    pack(128, "2h", 0, 32)  # stale record fields must not invent an extension
    pack(180, "2h", 1, 7)
    pack(196, "6h", 1, 488, 0, 0, 0, 0)
    header[300:317] = b"original sentinel"
    with path.open("wb") as f:
        f.write(header)
        f.write(extension)
        for c in coordinates(cfg, False):
            if words is not None:
                f.write(struct.pack(endian + str(len(words)) + "I", *words))
            else:
                data = plane(c, y, x, mode)
                f.write(data.astype(endian + ("u2" if mode == 6 else "f4")).tobytes())
    return bytes(header)


def bits(data: np.ndarray) -> bytes:
    return data.astype("<u2" if data.dtype.kind == "u" else "<f4").tobytes()


def provenance_change(entries: Any, field: str, old: Any, new: Any, source: str) -> None:
    """Accept leaf or grouped records while requiring the actual change."""
    parent, _, leaf = field.rpartition(".")
    assert any(
        v["source"] == source
        and (
            (v["field"] in (field, leaf) and v.get("old") == old and v["new"] == new)
            or (
                v["field"] == parent
                and isinstance(v.get("old"), dict)
                and isinstance(v["new"], dict)
                and v["old"].get(leaf) == old
                and v["new"].get(leaf) == new
            )
        )
        for v in entries
    ), f"missing provenance: {field} {old!r} -> {new!r} from {source}"


def expected_changes(entries: Any, cfg: dict[str, Any], original: bytes) -> None:
    endian = "<" if original[96:98] == struct.pack("<h", -16224) else ">"
    for axis, offset in (("time", 180), ("channel", 196)):
        if axis in cfg["plane_axes"]:
            old = struct.unpack_from(endian + "h", original, offset)[0]
            new = cfg["plane_shape"][cfg["plane_axes"].index(axis)]
            if old != new:
                # Both header-count and logical-axis naming identify this change.
                aliases = (f"file_metadata.{axis}_count", f"plane_shape.{axis}")
                matched = False
                for field in aliases:
                    try:
                        provenance_change(entries, field, old, new, "config")
                    except AssertionError:
                        continue
                    matched = True
                assert matched, f"missing {axis} config provenance {old} -> {new}"
    for parent, values in cfg["overrides"].items():
        for leaf, new in values.items():
            if parent == "sampling_um":
                old = struct.unpack_from(
                    endian + "f", original, 40 + 4 * ("x", "y", "z").index(leaf)
                )[0]
            else:
                old = struct.unpack_from(endian + "h", original, 198 + 2 * int(leaf))[0]
            provenance_change(entries, f"{parent}.{leaf}", old, new, "override")


def output(
    path: Path,
    cfg: dict[str, Any],
    original: bytes,
    extension: bytes = b"",
    *,
    words: list[int] | None = None,
) -> dict[str, Any]:
    raw = path.read_bytes()
    h = raw[:1024]
    x, y, n, mode = struct.unpack_from("<4i", h)
    assert (x, y, n, mode) == (
        *struct.unpack_from(
            ("<" if original[96:98] == struct.pack("<h", -16224) else ">") + "2i", original
        ),
        len(coordinates(cfg)),
        struct.unpack_from(
            ("<" if original[96:98] == struct.pack("<h", -16224) else ">") + "i", original, 12
        )[0],
    )
    expected_header = bytearray(1024)

    def put(offset: int, fmt: str, *v: int | float) -> None:
        struct.pack_into("<" + fmt, expected_header, offset, *v)

    put(0, "4i", x, y, n, mode)
    put(28, "3i", x, y, 1)
    put(52, "3f", 90, 90, 90)
    put(64, "3i", 1, 2, 3)
    put(76, "3f", 0, -1, -2)
    put(216, "f", -1)
    put(220, "i", 1)
    expected_header[104:108] = b"HDF5"
    put(108, "i", 20141)
    expected_header[208:216] = b"MAP DD\x00\x00"
    expected_header[224 : 224 + len(LABEL)] = LABEL
    ext_size = struct.unpack_from("<i", h, 92)[0]
    assert ext_size > 0 and ext_size % 4 == 0
    put(92, "i", ext_size)
    byte_order = "<" if original[96:98] == struct.pack("<h", -16224) else ">"
    sampling = dict(
        zip(("x", "y", "z"), struct.unpack_from(byte_order + "3f", original, 40), strict=True)
    )
    sampling.update(cfg["overrides"].get("sampling_um", {}))
    put(40, "2f", x * sampling["x"] * 10000, y * sampling["y"] * 10000)
    assert h == expected_header
    image = raw[1024 : 1024 + ext_size]
    assert image.startswith(b"\x89HDF\r\n\x1a\n")
    extracted = path.with_suffix(".h5")
    extracted.write_bytes(image)
    with h5py.File(extracted, "r") as f:
        assert list(f.keys()) == ["simrecon"]
        assert set(cast(h5py.Group, f["simrecon"]).keys()) == {
            "metadata_json",
            "original_header",
            "original_extended_header",
        }
        names: list[str] = []
        f.visititems(
            lambda name, obj: names.append(name) if isinstance(obj, h5py.Dataset) else None
        )
        assert sorted(names) == [
            "simrecon/metadata_json",
            "simrecon/original_extended_header",
            "simrecon/original_header",
        ]
        for name in names:
            d = f[name]
            assert isinstance(d, h5py.Dataset)
            assert d.ndim == 1 and d.dtype == np.dtype("uint8")
            if d.is_virtual:
                assert all(v.file_name in (".", b".") for v in d.virtual_sources())
            assert d.external is None and d.compression is None
            assert not d.shuffle and not d.fletcher32 and d.scaleoffset is None
            assert isinstance(f.get(name, getlink=True), h5py.HardLink)
        assert bytes(cast(h5py.Dataset, f["simrecon/original_header"])[:]) == original
        assert bytes(cast(h5py.Dataset, f["simrecon/original_extended_header"])[:]) == extension
        encoded = bytes(cast(h5py.Dataset, f["simrecon/metadata_json"])[:])
    meta = json.loads(encoded, parse_constant=lambda v: (_ for _ in ()).throw(AssertionError(v)))
    assert (
        encoded
        == json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )
    axes = [a for a in ORDER if a in cfg["plane_axes"]]
    sizes = dict(zip(cfg["plane_axes"], cfg["plane_shape"], strict=True))
    assert set(meta) == {
        "schema",
        "version",
        "data_kind",
        "logical_axes",
        "logical_shape",
        "source_layout",
        "output_layout",
        "sampling_um",
        "wavelengths_nm",
        "acquisition_config",
        "provenance",
        "main_header_axial_scale",
        "original_extension_schema",
    }
    assert meta["schema"] == "org.simrecon.mrc-metadata" and meta["version"] == 1
    assert meta["data_kind"] == "spatial_image"
    assert meta["logical_axes"] == axes + ["y", "x"]
    assert meta["logical_shape"] == [sizes[a] for a in axes] + [y, x]
    assert meta["source_layout"] == dict(
        plane_axes=cfg["plane_axes"],
        plane_shape=cfg["plane_shape"],
        byte_order="little" if original[96:98] == struct.pack("<h", -16224) else "big",
        pixel_mode=mode,
    )
    assert meta["output_layout"] == dict(
        plane_axes=axes, plane_shape=[sizes[a] for a in axes], section_count=n
    )
    assert meta["acquisition_config"] == cfg
    byte_order = "<" if original[96:98] == struct.pack("<h", -16224) else ">"
    expected_sampling = dict(
        zip(("x", "y", "z"), struct.unpack_from(byte_order + "3f", original, 40), strict=True)
    )
    expected_sampling.update(cfg["overrides"].get("sampling_um", {}))
    if "z" not in axes:
        expected_sampling["z"] = None
    assert meta["sampling_um"] == expected_sampling
    expected_wavelengths = {
        str(i): v
        for i, v in enumerate(struct.unpack_from(byte_order + "5h", original, 198))
        if v > 0
    }
    expected_wavelengths.update(cfg["overrides"].get("wavelengths_nm", {}))
    assert meta["wavelengths_nm"] == expected_wavelengths
    assert meta["main_header_axial_scale"] == "unknown_flattened_stack_zero_angstrom"
    assert meta["original_extension_schema"] == ("opaque" if extension else "none")
    for entry in meta["provenance"]:
        assert {"field", "new", "source"} <= set(entry)
        assert "old" in entry or "unresolved" in entry
        assert entry["source"] in ("config", "override")
    expected_changes(meta["provenance"], cfg, original)
    for i, a in enumerate(("x", "y")):
        actual = struct.unpack_from("<f", h, 40 + i * 4)[0] / (x if a == "x" else y) / 10000
        assert abs(actual / meta["sampling_um"][a] - 1) <= 1e-6
    assert mrcfile.validate(str(path))
    with mrcfile.open(path, permissive=False) as f:
        observed = np.asarray(f.data).reshape(n, y, x)
        for i, c in enumerate(coordinates(cfg)):
            expected = (
                plane(c, y, x, mode)
                if words is None
                else np.array(words, dtype="<u4").view("<f4").reshape(y, x)
            )
            assert bits(observed[i]) == bits(expected)
    return meta
