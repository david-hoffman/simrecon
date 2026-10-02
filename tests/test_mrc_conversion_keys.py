"""M45/M46: two key spellings, each exercised through Python and CLI.

Independent fixture oracle: documented little-endian mode 6 offsets, one
channel plane, 3 rows by 5 columns; pixel(row, column) = 40000 + 5*row + column.
The accepted test-side fixture/oracles are reused without changes. Modern
header/container checks below retain their independent byte expectations,
but wavelength expectations use logical channel 0 rather than raw spelling.
No pixel or byte tolerance. Only header-derived lateral scale uses rtol 1e-6.
"""

from __future__ import annotations

import copy
import importlib
import json
import struct
import subprocess
from pathlib import Path
from typing import Any, cast

import h5py
import mrcfile
import numpy as np

from mrc_fixture_conversion import LABEL, ORDER, bits, config, coordinates, fixture, plane


def channel_override(entries: Any) -> None:
    """Require unambiguous logical-channel old/new/source provenance."""
    assert any(
        entry.get("source") == "override"
        and (
            entry.get("field") in ("wavelengths_nm.0", "0")
            and entry.get("old") == 488
            and entry.get("new") == 561
            or entry.get("field") == "wavelengths_nm"
            and isinstance(entry.get("old"), dict)
            and isinstance(entry.get("new"), dict)
            and entry["old"].get("0") == 488
            and entry["new"].get("0") == 561
        )
        for entry in entries
    ), "missing logical channel 0 provenance: 488 -> 561 from override"


def key_output(
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
    assert encoded in (
        json.dumps(meta, sort_keys=True, separators=(",", ":"), ensure_ascii=ascii_only).encode()
        for ascii_only in (False, True)
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
    # Both approved spellings identify the sole logical channel 0.
    expected_wavelengths["0"] = 561
    assert meta["wavelengths_nm"] == expected_wavelengths
    assert meta["main_header_axial_scale"] == "unknown_flattened_stack_zero_angstrom"
    assert meta["original_extension_schema"] == ("opaque" if extension else "none")
    for entry in meta["provenance"]:
        assert {"field", "new", "source"} <= set(entry)
        assert "old" in entry or "unresolved" in entry
        assert entry["source"] in ("config", "override")
    channel_override(meta["provenance"])
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


def key_context(tmp_path: Path, key: str, *, cli_boundary: bool) -> None:
    cfg = config(("channel",), (1,))
    cfg["overrides"] = {"wavelengths_nm": {key: 561}}
    before = copy.deepcopy(cfg)
    source = tmp_path / "source.mrc"
    header = fixture(source, cfg)
    original = source.read_bytes()
    # Check the independent synthetic fixture before invoking any product entry.
    assert struct.unpack_from("<4i", header) == (5, 3, 1, 6)
    assert struct.unpack_from("<h", header, 198) == (488,)
    pixels = struct.pack("<15H", *range(40000, 40015))
    assert original == header + pixels
    destination = tmp_path / "output.mrc"
    if cli_boundary:
        cfg_path = tmp_path / "config.json"
        cfg_path.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run(
            [
                "simrecon",
                "convert",
                str(source),
                str(destination),
                "--config",
                str(cfg_path),
                "--block-planes",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert not result.stderr
        report = json.loads(result.stdout)
        assert report["destination"] == str(destination)
        assert report["stored_shape"] == [1, 3, 5]
        assert report["pixel_mode"] == 6 and report["planes_written"] == 1
        assert report["limitations"]
        channel_override(report["provenance"])
        assert json.loads(cfg_path.read_text(encoding="utf-8")) == before
    else:
        api: Any = importlib.import_module("simrecon")
        inspected = api.inspect(source)
        assert isinstance(inspected, api.DatasetInfo)
        assert inspected.original_header == header and inspected.config is None
        assert inspected.stored_shape == (1, 3, 5)
        assert inspected.file_metadata["channel_count"] == 1
        assert tuple(inspected.file_metadata["wavelength_slots"]) == (488, 0, 0, 0, 0)
        info = api.harmonize(inspected, config=cfg)
        assert isinstance(info, api.DatasetInfo) and info is not inspected
        assert info.axes == ("channel", "y", "x") and info.shape == (1, 3, 5)
        assert info.wavelengths_nm == {"0": 561}
        assert info.config == before and info.original_header == header
        assert info.file_metadata == inspected.file_metadata
        assert info.sampling_um == {
            "x": struct.unpack_from("<f", header, 40)[0],
            "y": 0.125,
            "z": None,
        }
        channel_override(info.provenance)
        block = api.read(info, plane_start=0, plane_stop=1)
        assert isinstance(block, api.DataBlock) and block.info == info
        assert block.plane_indices == range(0, 1)
        assert block.coordinates == ({"channel": 0},)
        assert block.data.shape == (1, 3, 5) and block.data.dtype == np.dtype("uint16")
        assert block.data.flags.owndata and block.data.flags.c_contiguous
        assert block.data.dtype.isnative and bits(block.data) == pixels
        report = api.write(destination, info, block_planes=1)
        assert isinstance(report, api.WriteReport)
        assert report.destination == destination and report.stored_shape == (1, 3, 5)
        assert report.pixel_mode == 6 and report.planes_written == 1
        assert report.provenance == info.provenance and report.limitations
    meta = key_output(destination, before, header)
    assert meta["wavelengths_nm"] == {"0": 561}
    assert meta["acquisition_config"]["overrides"]["wavelengths_nm"] == {key: 561}
    assert cfg == before and source.read_bytes() == original


def test_m45_ascii_key_python(tmp_path: Path) -> None:
    key_context(tmp_path, "00", cli_boundary=False)


def test_m45_ascii_key_cli(tmp_path: Path) -> None:
    key_context(tmp_path, "00", cli_boundary=True)


def test_m46_arabic_indic_key_python(tmp_path: Path) -> None:
    key_context(tmp_path, "\u0660", cli_boundary=False)


def test_m46_arabic_indic_key_cli(tmp_path: Path) -> None:
    key_context(tmp_path, "\u0660", cli_boundary=True)
