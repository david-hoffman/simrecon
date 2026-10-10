"""Exercise pinned reader preparation with controlled external inputs."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "reader_setup", ROOT / "scripts/prepare_imagej_reader.py"
)
assert SPEC is not None and SPEC.loader is not None
reader = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reader
SPEC.loader.exec_module(reader)


def input_for(data: bytes, maximum: int = 100) -> Any:
    return reader.ReaderInput(
        "reader.jar",
        "https://example.invalid/pinned.jar",
        hashlib.sha256(data).hexdigest(),
        maximum,
    )


def test_valid_cache_is_authenticated_without_fetch(tmp_path: Path, monkeypatch) -> None:
    data = b"controlled pinned jar"
    item = input_for(data)
    target = tmp_path / item.name
    target.write_bytes(data)
    monkeypatch.setattr(reader.subprocess, "run", lambda *a, **k: pytest.fail("unexpected network"))
    assert reader.acquire(tmp_path, item) == {
        "path": str(target.resolve()),
        "sha256": item.sha256,
        "size_bytes": len(data),
        "url": item.url,
    }
    target.write_bytes(b"corrupt cache")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        reader.acquire(tmp_path, item)
    assert target.read_bytes() == b"corrupt cache"


def test_missing_input_is_verified_before_publish(tmp_path: Path, monkeypatch) -> None:
    data = b"controlled download"
    item = input_for(data)
    calls = []

    def fetch(argv, **kwargs):
        calls.append((argv, kwargs))
        Path(argv[-1]).write_bytes(data)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(reader.subprocess, "run", fetch)
    identity = reader.acquire(tmp_path, item)
    assert identity["sha256"] == hashlib.sha256(data).hexdigest()
    assert (tmp_path / item.name).read_bytes() == data
    assert list(tmp_path.iterdir()) == [tmp_path / item.name]
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:4] == [
        sys.executable,
        str(ROOT / "scripts/prepare_imagej_reader.py"),
        "--fetch",
        item.name,
    ]
    assert kwargs["timeout"] == 180
    assert kwargs.get("shell", False) is False


@pytest.mark.parametrize("failure", ["checksum", "process", "timeout", "unavailable"])
def test_failed_fetch_preserves_failure_and_cleans_scratch(
    tmp_path: Path, monkeypatch, failure
) -> None:
    item = input_for(b"trusted")

    def fetch(argv, **kwargs):
        Path(argv[-1]).write_bytes(b"untrusted partial download")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        if failure == "unavailable":
            raise OSError("controlled download executable unavailable")
        return subprocess.CompletedProcess(
            argv, int(failure == "process"), "", "controlled fetch error"
        )

    monkeypatch.setattr(reader.subprocess, "run", fetch)
    with pytest.raises((ValueError, TimeoutError, OSError)) as caught:
        reader.acquire(tmp_path, item)
    diagnostic = {
        "checksum": "SHA256 mismatch",
        "process": "controlled fetch error",
        "timeout": "180 seconds",
        "unavailable": "unavailable",
    }[failure]
    assert diagnostic in str(caught.value)
    assert list(tmp_path.iterdir()) == []


class Response(io.BytesIO):
    """Supply HTTP body bytes and optional declared length."""

    def __init__(self, body: bytes, declared: str | None = None):
        super().__init__(body)
        self.headers = {} if declared is None else {"Content-Length": declared}


@pytest.mark.parametrize("declared", [None, "101"])
def test_download_enforces_streamed_and_declared_size(
    tmp_path: Path, monkeypatch, declared
) -> None:
    item = input_for(b"trusted", maximum=100)

    class Opener:
        def open(self, url, *, timeout):
            assert url == item.url
            assert timeout == 15
            return Response(b"x" * 101, declared)

    monkeypatch.setattr(reader.urllib.request, "build_opener", lambda *a: Opener())
    with pytest.raises(ValueError, match="exceeds"):
        reader.download(item, tmp_path / "scratch")


def test_download_rejects_redirects_and_deadline(tmp_path: Path, monkeypatch) -> None:
    assert (
        reader.NoRedirect().redirect_request(None, None, 302, "", None, "https://other.invalid")
        is None
    )
    times = iter([0, 180])
    monkeypatch.setattr(reader.time, "monotonic", lambda: next(times))

    class Opener:
        def open(self, *args, **kwargs):
            return Response(b"trusted")

    monkeypatch.setattr(reader.urllib.request, "build_opener", lambda *a: Opener())
    with pytest.raises(TimeoutError, match="deadline"):
        reader.download(input_for(b"trusted"), tmp_path / "scratch")


@pytest.fixture
def fake_java(tmp_path: Path, monkeypatch) -> Path:
    executable = tmp_path / "java"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import os, sys\n"
        "if '-version' in sys.argv:\n"
        "    version = os.environ.get('TEST_JAVA_VERSION', '21.0.7')\n"
        "    print('java.version = ' + version, file=sys.stderr)\n"
        "    print('java.vendor = Controlled vendor', file=sys.stderr)\n"
        "    print('os.name = Controlled OS', file=sys.stderr)\n"
        "    print('os.arch = controlled_arch', file=sys.stderr)\n"
        "else:\n"
        "    print('simrecon-jdk-source-launcher', end='')\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("SIMRECON_JAVA", str(executable))
    monkeypatch.setattr(reader, "CACHE", tmp_path)
    return executable


def test_java_env_and_path_choice_preserve_identity(fake_java: Path, monkeypatch) -> None:
    identity = reader.java_identity()
    assert identity["executable"] == str(fake_java.resolve())
    assert identity["version"] == "21.0.7"
    assert identity["vendor"] == "Controlled vendor"
    assert identity["platform"] == {"os_name": "Controlled OS", "os_arch": "controlled_arch"}
    assert identity["source_launcher_checked"] is True
    assert not list(fake_java.parent.glob("java-probe-*"))
    monkeypatch.delenv("SIMRECON_JAVA")
    monkeypatch.setenv("PATH", str(fake_java.parent))
    assert reader.java_identity()["executable"] == str(fake_java.resolve())


@pytest.mark.parametrize("version", ["21.0.6", "21.0.7.1", "25"])
def test_wrong_java_version_fails_with_observed_identity(
    fake_java: Path, monkeypatch, version
) -> None:
    monkeypatch.setenv("TEST_JAVA_VERSION", version)
    with pytest.raises(ValueError, match="Require Java 21.0.7") as caught:
        reader.java_identity()
    assert version in str(caught.value)


def test_missing_explicit_java_does_not_fall_back(monkeypatch) -> None:
    monkeypatch.setenv("SIMRECON_JAVA", "/missing/java")
    with pytest.raises(ValueError, match="Java unavailable"):
        reader.java_identity()


@pytest.mark.parametrize("timeout", [False, True])
def test_java_failure_is_bounded_and_diagnostic(fake_java: Path, monkeypatch, timeout) -> None:
    def run(argv, **kwargs):
        assert kwargs["timeout"] == 15
        if timeout:
            raise subprocess.TimeoutExpired(argv, 15)
        return subprocess.CompletedProcess(argv, 1, "", "controlled Java failure")

    monkeypatch.setattr(reader.subprocess, "run", run)
    with pytest.raises(ValueError, match="Java identity failed|Require Java"):
        reader.java_identity()


def test_manifest_reports_exact_jars_and_selected_java(fake_java: Path, monkeypatch) -> None:
    items = (input_for(b"trusted"),)
    monkeypatch.setattr(reader, "INPUTS", items)
    (fake_java.parent / items[0].name).write_bytes(b"trusted")
    manifest = reader.prepare()
    document = json.loads(manifest.read_text())
    assert document["schema"] == "org.simrecon.imagej-reader-inputs"
    assert document["java"]["executable"] == str(fake_java.resolve())
    assert document["jars"][items[0].name]["sha256"] == hashlib.sha256(b"trusted").hexdigest()
    assert document["jars"][items[0].name]["size_bytes"] == 7
    assert "no interoperability result" in document["purpose"]
    (fake_java.parent / items[0].name).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        reader.prepare()
    assert not manifest.exists()


def test_public_cli_missing_java_reports_nonzero_without_traceback(tmp_path: Path) -> None:
    import os

    # Exercise the actual CLI in an isolated layout without touching current reader evidence.
    script = tmp_path / "scripts/prepare_imagej_reader.py"
    script.parent.mkdir()
    shutil.copyfile(ROOT / "scripts/prepare_imagej_reader.py", script)
    result = subprocess.run(
        [sys.executable, str(script)],
        env={**os.environ, "SIMRECON_JAVA": str(tmp_path / "missing")},
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 1
    assert "Java unavailable" in result.stderr
    assert "Traceback" not in result.stderr


def test_download_worker_rejects_unscoped_destination_before_fetch(tmp_path: Path) -> None:
    destination = tmp_path / "preserved.txt"
    destination.write_bytes(b"preserve these bytes")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_imagej_reader.py"),
            "--fetch",
            "bioformats_package.jar",
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 1
    assert "scoped existing temporary cache file" in result.stderr
    assert destination.read_bytes() == b"preserve these bytes"
