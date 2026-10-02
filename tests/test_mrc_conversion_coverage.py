"""Approved follow-up M27–M44; original M01–M26 helpers remain unchanged."""

from __future__ import annotations

import copy
import importlib
import json
import struct
from pathlib import Path
from typing import Any

import pytest

from mrc_fixture_conversion import config, fixture, output
from mrc_fixture_events import SourceEvent
from test_mrc_conversion import check_block, cli, cli_error, cli_report, error


@pytest.fixture
def api() -> Any:
    return importlib.import_module("simrecon")


def invalid(api: Any, tmp_path: Path, cfg: dict[str, Any]) -> None:
    source = tmp_path / "source.mrc"
    fixture(source, config((), ()))
    original = source.read_bytes()
    info = api.inspect(source)
    before = copy.deepcopy(cfg)
    error(api, "config_invalid", api.harmonize, info, config=cfg)
    assert cfg == before and info.config is None
    assert source.read_bytes() == original


def test_m27_missing_cli_config(tmp_path: Path) -> None:
    source = tmp_path / "source.mrc"
    fixture(source, config((), ()))
    destination = tmp_path / "out.mrc"
    cli_error(cli("convert", str(source), str(destination)), "config_invalid")
    assert not destination.exists()


def bad_json(tmp_path: Path, text: str) -> None:
    source = tmp_path / "source.mrc"
    fixture(source, config((), ()))
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(text)
    destination = tmp_path / "out.mrc"
    cli_error(
        cli("convert", str(source), str(destination), "--config", str(cfg_path)),
        "config_invalid",
    )
    assert not destination.exists()


def test_m28_nonfinite_cli_json(tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"sampling_um": {"x": float("nan")}}
    bad_json(tmp_path, json.dumps(cfg))


def test_m29_cli_array(tmp_path: Path) -> None:
    bad_json(tmp_path, "[]")


def test_m30_unknown_top_field(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["extra"] = 1
    invalid(api, tmp_path, cfg)


def test_m31_scalar_axes(api: Any, tmp_path: Path) -> None:
    cfg = config(("phase",), (1,))
    cfg["plane_axes"] = "phase"
    invalid(api, tmp_path, cfg)


def test_m32_unknown_policy(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["extended_header"] = "unknown"
    invalid(api, tmp_path, cfg)


def test_m33_absent_opaque(api: Any, tmp_path: Path) -> None:
    invalid(api, tmp_path, config((), (), opaque=True))


def test_m34_unknown_override(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"extra": 1}
    invalid(api, tmp_path, cfg)


def test_m35_unknown_sampling_axis(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"sampling_um": {"q": 0.2}}
    invalid(api, tmp_path, cfg)


def test_m36_wavelength_array(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"wavelengths_nm": [488]}
    invalid(api, tmp_path, cfg)


def test_m37_zero_override(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"sampling_um": {"x": 0}}
    invalid(api, tmp_path, cfg)


def test_m38_nonnumeric_channel(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"wavelengths_nm": {"channelA": 488}}
    invalid(api, tmp_path, cfg)


def test_m39_unknown_profile_override(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["spatial_fields"] = "unknown_convention"
    cfg["overrides"] = {"sampling_um": {"x": 0.2, "y": 0.375}}
    source = tmp_path / "source.mrc"
    header = fixture(source, cfg)
    original = source.read_bytes()
    inspected = api.inspect(source)
    before = copy.deepcopy(cfg)
    info = api.harmonize(inspected, config=cfg)
    assert cfg == before and inspected.config is None
    assert info.original_header == header and info.file_metadata == inspected.file_metadata
    assert info.sampling_um == {"x": 0.2, "y": 0.375, "z": None}
    check_block(api, info, cfg, 0, 1)
    destination = tmp_path / "python.mrc"
    report = api.write(destination, info, block_planes=1)
    assert isinstance(report, api.WriteReport) and report.planes_written == 1
    meta = output(destination, cfg, header)
    assert report.provenance == tuple(meta["provenance"])
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))
    cli_report(
        cli("convert", str(source), str(tmp_path / "cli.mrc"), "--config", str(cfg_path)),
        tmp_path / "cli.mrc",
        6,
        1,
        cfg,
        header,
    )
    assert source.read_bytes() == original and cfg == before


def test_m40_underflow(api: Any, tmp_path: Path) -> None:
    cfg = config((), ())
    cfg["overrides"] = {"sampling_um": {"x": 1e-60}}
    source = tmp_path / "source.mrc"
    fixture(source, cfg, x=5)
    info = api.harmonize(api.inspect(source), config=cfg)
    assert struct.pack("<f", 5 * 1e-60 * 10000) == bytes(4)
    error(api, "header_unrepresentable", api.write, tmp_path / "out.mrc", info)


def test_m41_sparse_extension_limit(api: Any, tmp_path: Path) -> None:
    cfg = config((), (), opaque=True)
    source = tmp_path / "sparse.mrc"
    header = bytearray(fixture(source, cfg, x=1, y=1))
    extension_size = 2_147_483_647
    struct.pack_into("<i", header, 92, extension_size)
    with source.open("r+b") as handle:
        handle.write(header)
        handle.seek(1024 + extension_size)
        handle.write(struct.pack("<H", 40000))
    assert source.stat().st_size == 1024 + extension_size + 2
    # A genuine sparse file is an environment prerequisite, not a skipped context.
    assert source.stat().st_blocks * 512 < 1024 * 1024
    inspected = api.inspect(source)
    assert inspected.extended_header_bytes == extension_size
    assert inspected.original_header == bytes(header)
    info = api.harmonize(inspected, config=cfg)
    error(api, "header_unrepresentable", api.write, tmp_path / "out.mrc", info)


def changed(api: Any, fn: Any, event: SourceEvent, *args: Any, **kwargs: Any) -> None:
    caught: Any = None
    try:
        fn(*args, **kwargs)
    except Exception as exc:
        caught = exc
    event.assert_occurred()
    assert isinstance(caught, api.SimreconError), f"incidental failure: {caught!r}"
    assert caught.code == "source_changed" and caught.message


def test_m42_active_read_shortens(
    api: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = config((), ())
    source = tmp_path / "source.mrc"
    fixture(source, cfg)
    info = api.harmonize(api.inspect(source), config=cfg)
    event = SourceEvent(source, "payload")
    event.install(monkeypatch)
    changed(api, api.read, event, info, plane_start=0, plane_stop=1)


def test_m43_extension_copy_shortens(
    api: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = config((), (), opaque=True)
    source = tmp_path / "source.mrc"
    extension = bytes(range(256)) * 8192
    fixture(source, cfg, extension=extension)
    info = api.harmonize(api.inspect(source), config=cfg)
    event = SourceEvent(source, "extension", len(extension))
    event.install(monkeypatch)
    changed(api, api.write, event, tmp_path / "out.mrc", info, block_planes=1)


def test_m44_completion_identity_changes(
    api: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = config((), ())
    source = tmp_path / "source.mrc"
    fixture(source, cfg)
    info = api.harmonize(api.inspect(source), config=cfg)
    event = SourceEvent(source, "completion")
    event.install(monkeypatch)
    changed(api, api.write, event, tmp_path / "out.mrc", info, block_planes=1)
