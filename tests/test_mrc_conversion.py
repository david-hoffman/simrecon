"""All 26 approved input contexts, tested through public boundaries."""

from __future__ import annotations

import copy
import hashlib
import importlib
import json
import os
import struct
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from measurement_fixture_export import export_measurement
from mrc_fixture_conversion import (
    bits,
    config,
    coordinates,
    expected_changes,
    fixture,
    output,
    plane,
)


@pytest.fixture
def api() -> Any:
    module = importlib.import_module("simrecon")
    for name in (
        "inspect",
        "harmonize",
        "read",
        "write",
        "DatasetInfo",
        "DataBlock",
        "WriteReport",
        "SimreconError",
    ):
        assert hasattr(module, name), f"public export absent: simrecon.{name}"
    assert issubclass(module.SimreconError, ValueError)
    return module


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["simrecon", *args], capture_output=True, text=True, check=False)


def error(api: Any, code: str, fn: Any, *args: Any, **kwargs: Any) -> str:
    with pytest.raises(api.SimreconError) as caught:
        fn(*args, **kwargs)
    assert caught.value.code == code
    assert isinstance(caught.value.message, str) and caught.value.message
    return caught.value.message


def cli_error(
    result: subprocess.CompletedProcess[str],
    code: str,
    status: int = 2,
    *,
    message: str | None = None,
) -> None:
    assert result.returncode == status
    assert not result.stdout
    value = json.loads(result.stderr)
    assert value["code"] == code and isinstance(value["message"], str)
    assert value["message"]
    if message is not None:
        assert value["message"] == message
    assert "Traceback" not in result.stderr


def cli_inspection(
    result: subprocess.CompletedProcess[str], source: Path, mode: int, n: int, byte_order: str
) -> None:
    assert result.returncode == 0 and result.stderr == ""
    value = json.loads(result.stdout)
    assert value["source"] == str(source)
    assert value["source_size"] == source.stat().st_size
    assert value["source_mtime_ns"] == source.stat().st_mtime_ns
    assert value["header_sha256"] == hashlib.sha256(source.read_bytes()[:1024]).hexdigest()
    assert value["stored_shape"] == [n, 3, 5]
    assert value["axes"] == ["section", "y", "x"]
    assert value["shape"] == [n, 3, 5]
    assert value["pixel_mode"] == mode and value["byte_order"] == byte_order
    assert value["extended_header_bytes"] == 0 and value["config"] is None
    assert value["data_kind"] is None and value["unresolved"]
    assert value["file_metadata"]["time_count"] == 1
    assert value["file_metadata"]["channel_count"] == 1


def cli_report(
    result: subprocess.CompletedProcess[str],
    destination: Path,
    mode: int,
    n: int,
    cfg: dict[str, Any],
    header: bytes,
) -> None:
    assert result.returncode == 0 and result.stderr == ""
    value = json.loads(result.stdout)
    assert value["destination"] == str(destination)
    assert value["stored_shape"] == [n, 3, 5]
    assert value["pixel_mode"] == mode and value["planes_written"] == n
    assert isinstance(value["limitations"], list) and value["limitations"]
    assert all(isinstance(v, str) and v for v in value["limitations"])
    meta = output(destination, cfg, header)
    assert value["provenance"] == meta["provenance"]


def resolved(
    api: Any, tmp_path: Path, cfg: dict[str, Any], **kwargs: Any
) -> tuple[Path, bytes, Any]:
    p = tmp_path / "input.mrc"
    header = fixture(p, cfg, **kwargs)
    info = api.inspect(p)
    before = copy.deepcopy(cfg)
    result = api.harmonize(info, config=cfg)
    assert cfg == before and info.config is None
    assert result.file_metadata == info.file_metadata
    assert result is not info and result.original_header == header
    assert result.config == cfg
    return p, header, result


def check_block(api: Any, info: Any, cfg: dict[str, Any], start: int, stop: int) -> None:
    b = api.read(info, plane_start=start, plane_stop=stop)
    assert isinstance(b, api.DataBlock) and b.info == info
    assert b.plane_indices == range(start, stop)
    assert b.coordinates == tuple(coordinates(cfg)[start:stop])
    assert b.data.flags.owndata and b.data.flags.c_contiguous and b.data.dtype.isnative
    assert b.data.shape == (stop - start, *info.stored_shape[1:])
    assert b.data.dtype == np.dtype("uint16" if info.pixel_mode == 6 else "float32")
    for i, c in enumerate(coordinates(cfg)[start:stop]):
        assert bits(b.data[i]) == bits(
            plane(c, info.stored_shape[1], info.stored_shape[2], info.pixel_mode)
        )


def test_m01_raw(api: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config()
    p = tmp_path / "raw.mrc"
    header = fixture(p, cfg)
    source_digest = hashlib.sha256(p.read_bytes()).hexdigest()
    # Guard all file opens during pure harmonization. Inspect reads are bounded below.
    import builtins

    real_open = builtins.open
    real_path_open = Path.open

    class HeaderOnly:
        def __init__(self, handle: Any) -> None:
            self.handle = handle

        def __enter__(self) -> Any:
            self.handle.__enter__()
            return self

        def __exit__(self, *args: Any) -> Any:
            return self.handle.__exit__(*args)

        def read(self, size: int = -1) -> bytes:
            assert 0 <= size <= 1024 and self.handle.tell() + size <= 1024
            return self.handle.read(size)

        def readinto(self, buffer: Any) -> int:
            assert self.handle.tell() + len(buffer) <= 1024
            return self.handle.readinto(buffer)

        def __getattr__(self, name: str) -> Any:
            return getattr(self.handle, name)

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", lambda *a, **k: HeaderOnly(real_open(*a, **k)))
        m.setattr(Path, "open", lambda *a, **k: HeaderOnly(real_path_open(*a, **k)))
        info = api.inspect(p)
    assert isinstance(info, api.DatasetInfo)
    assert info.source == p and info.source_size == p.stat().st_size
    assert info.source_mtime_ns == p.stat().st_mtime_ns
    assert info.header_sha256 == hashlib.sha256(header).hexdigest()
    assert info.original_header == header and info.stored_shape == (9, 3, 5)
    assert info.axes == ("section", "y", "x") and info.shape == (9, 3, 5)
    assert info.byte_order == "little" and info.pixel_mode == 6
    assert np.dtype(info.stored_dtype) == np.dtype("uint16")
    assert info.extended_header_bytes == 0 and info.config is None
    assert info.file_metadata["extension_float_fields"] == 32
    assert info.file_metadata["extension_integer_fields"] == 0
    assert info.file_metadata["time_count"] == 1
    assert info.file_metadata["channel_count"] == 1
    assert info.file_metadata["image_sequence"] == 7
    assert info.data_kind is None and info.unresolved
    for field in (
        "grid",
        "spatial_fields",
        "map_axes",
        "time_count",
        "image_sequence",
        "channel_count",
        "wavelength_slots",
        "extension_integer_fields",
        "extension_float_fields",
    ):
        assert field in info.file_metadata
    before = copy.deepcopy(cfg)
    with monkeypatch.context() as m:

        def forbidden(*args: Any, **kwargs: Any) -> Any:
            raise AssertionError("harmonize opened a file")

        m.setattr(builtins, "open", forbidden)
        m.setattr(Path, "open", forbidden)
        m.setattr(os, "open", forbidden)
        r = api.harmonize(info, config=cfg)
    assert cfg == before and info.config is None
    assert r.axes == ("orientation", "phase", "y", "x") and r.shape == (3, 3, 3, 5)
    assert r.sampling_um["z"] is None

    # Allow only the header and selected source planes, even when a caller asks
    # for a canonical interval. This rejects a convenience full-stack read.
    class SelectedOnly(HeaderOnly):
        def read(self, size: int = -1) -> bytes:
            start = self.handle.tell()
            assert size >= 0
            assert (start + size <= 1024) or (
                start >= 1024 + 2 * 30 and start + size <= 1024 + 5 * 30
            )
            return self.handle.read(size)

        def readinto(self, buffer: Any) -> int:
            data = self.read(len(buffer))
            buffer[: len(data)] = data
            return len(data)

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", lambda *a, **k: SelectedOnly(real_open(*a, **k)))
        m.setattr(Path, "open", lambda *a, **k: SelectedOnly(real_path_open(*a, **k)))
        check_block(api, r, cfg, 2, 5)
    dest = tmp_path / "out.mrc"
    report = api.write(dest, r, block_planes=2)
    assert isinstance(report, api.WriteReport)
    assert report.destination == dest and report.stored_shape == (9, 3, 5)
    assert report.pixel_mode == 6 and report.planes_written == 9
    assert report.provenance == r.provenance and report.limitations
    output(dest, cfg, header)
    assert hashlib.sha256(p.read_bytes()).hexdigest() == source_digest
    inspected = cli("inspect", str(p))
    cli_inspection(inspected, p, 6, 9, "little")
    cp = tmp_path / "config.json"
    cp.write_text(json.dumps(cfg))
    dest2 = tmp_path / "cli.mrc"
    result = cli("convert", str(p), str(dest2), "--config", str(cp), "--block-planes", "2")
    cli_report(result, dest2, 6, 9, cfg, header)


def test_m02_big_float_2d(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    p, header, info = resolved(api, tmp_path, cfg, endian=">", mode=2)
    assert info.axes == ("y", "x") and info.sampling_um["z"] is None
    assert info.byte_order == "big"
    check_block(api, info, cfg, 0, 1)
    dest = tmp_path / "out.mrc"
    api.write(dest, info)
    output(dest, cfg, header)
    cp = tmp_path / "config.json"
    cp.write_text(json.dumps(cfg))
    cli_inspection(cli("inspect", str(p)), p, 2, 1, "big")
    dest2 = tmp_path / "cli.mrc"
    result = cli("convert", str(p), str(dest2), "--config", str(cp))
    cli_report(result, dest2, 2, 1, cfg, header)


def test_m03_reorder(api: Any, tmp_path: Path) -> None:
    cfg = config(("z", "phase", "time", "orientation", "channel"), (2, 4, 2, 4, 2))
    _, header, info = resolved(api, tmp_path, cfg, endian=">")
    assert info.axes == ("time", "channel", "orientation", "phase", "z", "y", "x")
    assert info.shape == (2, 2, 4, 4, 2, 3, 5)
    check_block(api, info, cfg, 13, 21)
    dest = tmp_path / "out.mrc"
    api.write(dest, info, block_planes=3)
    meta = output(dest, cfg, header)
    assert meta["sampling_um"]["z"] == 0.75
    expected_changes(info.provenance, cfg, header)


def test_m04_ieee_words(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    words = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC01234, 0xFFC05678]
    _, header, info = resolved(api, tmp_path, cfg, mode=2, y=2, x=3, words=words)
    b = api.read(info, plane_start=0, plane_stop=1)
    assert bits(b.data) == struct.pack("<6I", *words)
    dest = tmp_path / "out.mrc"
    api.write(dest, info)
    output(dest, cfg, header, words=words)


def test_m05_overrides(api: Any, tmp_path: Path) -> None:
    cfg = config()
    cfg["overrides"] = {"sampling_um": {"x": 0.2, "y": 0.125}, "wavelengths_nm": {"0": 561}}
    p, header, info = resolved(api, tmp_path, cfg)
    assert info.sampling_um == {"x": 0.2, "y": 0.125, "z": None}
    assert info.wavelengths_nm["0"] == 561
    expected_changes(info.provenance, cfg, header)
    cfg["overrides"]["sampling_um"]["x"] = 99
    assert info.sampling_um["x"] == 0.2 and info.config["overrides"]["sampling_um"]["x"] == 0.2
    saved = copy.deepcopy(dict(info.config))
    dest = tmp_path / "out.mrc"
    api.write(dest, info)
    output(dest, saved, header)
    assert p.read_bytes()[:1024] == header


def test_m06_unresolved(api: Any, tmp_path: Path) -> None:
    cfg = config()
    p = tmp_path / "input.mrc"
    fixture(p, cfg)
    info = api.inspect(p)
    error(api, "config_required", api.read, info, plane_start=0, plane_stop=1)
    dest = tmp_path / "out.mrc"
    error(api, "config_required", api.write, dest, info)
    cp = tmp_path / "config.json"
    cp.write_text("{}")
    message = error(api, "config_required", api.harmonize, info, config={})
    cli_error(
        cli("convert", str(p), str(dest), "--config", str(cp)), "config_required", message=message
    )
    assert not dest.exists()


def test_m07_layout(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    cfg = config(shape=(3, 4))
    cfg["overrides"] = {"sampling_um": {"x": 1}}
    error(api, "layout_mismatch", api.harmonize, api.inspect(p), config=cfg)


def test_m08_opaque(api: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = config(("phase", "orientation"), (3, 3), opaque=True)
    ext = b"\x00opaque\xff" + bytes(range(256)) * 7
    p, header, info = resolved(api, tmp_path, cfg, extension=ext)
    assert info.extended_header_bytes == len(ext)
    # Inspection must not read even one opaque byte.
    import builtins

    real = builtins.open

    class Guard:
        def __init__(self, f: Any) -> None:
            self.f = f

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *a: Any) -> None:
            self.f.close()

        def read(self, n: int = -1) -> bytes:
            assert n >= 0 and self.f.tell() + n <= 1024
            return self.f.read(n)

        def __getattr__(self, name: str) -> Any:
            return getattr(self.f, name)

    with monkeypatch.context() as m:
        m.setattr(builtins, "open", lambda *a, **k: Guard(real(*a, **k)))
        m.setattr(Path, "open", lambda path, *a, **k: Guard(real(path, *a, **k)))
        assert api.inspect(p).extended_header_bytes == len(ext)
    dest = tmp_path / "out.mrc"
    api.write(dest, info, block_planes=1)
    meta = output(dest, cfg, header, ext)
    assert not any(k in meta for k in ("timestamps", "dose", "background"))


def test_m09_schema(api: Any, tmp_path: Path) -> None:
    cfg = config()
    cfg.pop("extended_header")
    p = tmp_path / "input.mrc"
    fixture(p, cfg, extension=b"opaque")
    info = api.inspect(p)
    assert info.unresolved
    error(api, "schema_required", api.harmonize, info, config=cfg)


def test_m10_short_header(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    p.write_bytes(b"\x00" * 1023)
    message = error(api, "invalid_header", api.inspect, p)
    cli_error(cli("inspect", str(p)), "invalid_header", message=message)


def test_m11_short_payload(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("r+b") as f:
        f.truncate(p.stat().st_size - 1)
    message = error(api, "payload_size", api.inspect, p)
    cli_error(cli("inspect", str(p)), "payload_size", message=message)
    cfg = config()
    cfg["overrides"] = {"sampling_um": {"x": 1}}
    cp = tmp_path / "config.json"
    cp.write_text(json.dumps(cfg))
    dest = tmp_path / "out.mrc"
    cli_error(
        cli("convert", str(p), str(dest), "--config", str(cp)), "payload_size", message=message
    )
    assert not dest.exists()


def test_m12_trailer(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("ab") as f:
        f.write(b"extra")
    error(api, "payload_size", api.inspect, p)


def test_m13_mode(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("r+b") as f:
        f.seek(12)
        f.write(struct.pack("<i", 1))
    info = api.inspect(p)
    assert info.pixel_mode == 1 and info.stored_dtype is None
    error(api, "unsupported_mode", api.harmonize, info, config=config())
    error(api, "unsupported_mode", api.read, info, plane_start=0, plane_stop=1)
    error(api, "unsupported_mode", api.write, tmp_path / "out.mrc", info)


def test_m14_mapping(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("r+b") as f:
        f.seek(64)
        f.write(struct.pack("<3i", 2, 1, 3))
    info = api.inspect(p)
    assert tuple(info.file_metadata["map_axes"]) == (2, 1, 3)
    error(api, "unsupported_axes", api.harmonize, info, config=config())


def test_m15_identifier(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("r+b") as f:
        f.seek(96)
        f.write(b"\x00\x00")
    error(api, "unsupported_format", api.inspect, p)


def test_m16_dimension(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    with p.open("r+b") as f:
        f.write(struct.pack("<i", 0))
    error(api, "invalid_header", api.inspect, p)


def test_m17_json(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config())
    cp = tmp_path / "config.json"
    cp.write_text("{")
    dest = tmp_path / "out.mrc"
    cli_error(cli("convert", str(p), str(dest), "--config", str(cp)), "config_invalid")
    assert not dest.exists()


def test_m18_duplicate(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    header = fixture(p, config())
    cfg = config(("phase", "phase"), (3, 3))
    before = copy.deepcopy(cfg)
    error(api, "config_invalid", api.harmonize, api.inspect(p), config=cfg)
    assert cfg == before and p.read_bytes()[:1024] == header


def test_m19_sampling(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "input.mrc"
    fixture(p, config(), sampling=(0, 0.125, 0.75))
    error(api, "sampling_required", api.harmonize, api.inspect(p), config=config())


def test_m20_no_overwrite(api: Any, tmp_path: Path) -> None:
    cfg = config()
    p, _, info = resolved(api, tmp_path, cfg)
    dest = tmp_path / "out.mrc"
    dest.write_bytes(b"keep me")
    cp = tmp_path / "config.json"
    cp.write_text(json.dumps(cfg))
    for target in (dest, p):
        before = target.read_bytes()
        with pytest.raises(FileExistsError):
            api.write(target, info)
        cli_error(cli("convert", str(p), str(target), "--config", str(cp)), "io_error", 1)
        assert target.read_bytes() == before


def test_m21_changed(api: Any, tmp_path: Path) -> None:
    p, header, info = resolved(api, tmp_path, config())
    dest = tmp_path / "out.mrc"

    def rejected() -> None:
        error(api, "source_changed", api.read, info, plane_start=0, plane_stop=1)
        error(api, "source_changed", api.write, dest, info)

    os.utime(p, ns=(info.source_mtime_ns, info.source_mtime_ns + 1_000_000_000))
    rejected()
    os.utime(p, ns=(info.source_mtime_ns, info.source_mtime_ns))
    with p.open("r+b") as f:
        f.seek(300)
        f.write(b"CHANGED")
    os.utime(p, ns=(info.source_mtime_ns, info.source_mtime_ns))
    rejected()
    with p.open("r+b") as f:
        f.write(header)
        f.seek(0, 2)
        f.write(b"size change")
    os.utime(p, ns=(info.source_mtime_ns, info.source_mtime_ns))
    rejected()


def test_m22_selection(api: Any, tmp_path: Path) -> None:
    _, _, info = resolved(api, tmp_path, config())
    error(api, "invalid_selection", api.read, info, plane_start=8, plane_stop=10)


def test_m23_block(api: Any, tmp_path: Path) -> None:
    _, _, info = resolved(api, tmp_path, config())
    dest = tmp_path / "out.mrc"
    error(api, "invalid_block_size", api.write, dest, info, block_planes=0)
    assert not dest.exists()


def test_m24_missing(api: Any, tmp_path: Path) -> None:
    p = tmp_path / "missing.mrc"
    with pytest.raises(FileNotFoundError):
        api.inspect(p)
    cli_error(cli("inspect", str(p)), "io_error", 1)


def test_m26_header_range(api: Any, tmp_path: Path) -> None:
    cfg = config()
    cfg["overrides"] = {"sampling_um": {"x": 1e38}}
    _, _, info = resolved(api, tmp_path, cfg)
    error(api, "header_unrepresentable", api.write, tmp_path / "out.mrc", info)


def test_m25_native_memory(api: Any, tmp_path: Path) -> None:
    import sys

    runner = Path(__file__).with_name("mrc_fixture_memory.py")
    result = subprocess.run(
        [sys.executable, str(runner), str(tmp_path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
    measurement = json.loads(result.stdout)
    assert measurement["increment_bytes"] <= 32 * 1024 * 1024
    assert measurement["units"] == ("bytes" if sys.platform == "darwin" else "KiB")
    export_measurement(measurement)
