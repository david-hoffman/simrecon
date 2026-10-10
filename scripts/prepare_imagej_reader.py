"""Authenticate pinned development-only reader inputs and Java identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOCKET_TIMEOUT_SECONDS = 15
FETCH_TIMEOUT_SECONDS = 180
JAVA_TIMEOUT_SECONDS = 15
JAVA_VERSION = "21.0.7"
ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "artifacts" / "imagej-reader"


@dataclass(frozen=True)
class ReaderInput:
    """Identify one immutable upstream development input."""

    name: str
    url: str
    sha256: str
    maximum_bytes: int


INPUTS = (
    ReaderInput(
        "bioformats_package.jar",
        "https://downloads.openmicroscopy.org/bio-formats/8.5.0/artifacts/bioformats_package.jar",
        "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9",
        70_000_000,
    ),
    ReaderInput(
        "ij-1.54p.jar",
        "https://sites.imagej.net/Fiji/jars/ij-1.54p.jar-20250219110715",
        "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20",
        10_000_000,
    ),
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject redirects instead of requesting an unpinned URL."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str):
        """Leave redirect responses as explicit HTTP failures."""
        return None


def authenticate(path: Path, item: ReaderInput) -> dict[str, Any]:
    """Check bounded file bytes before reporting their provenance."""
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            size += len(chunk)
            if size > item.maximum_bytes:
                raise ValueError(f"{item.name}: exceeds {item.maximum_bytes} bytes")
            digest.update(chunk)
    actual = digest.hexdigest()
    if actual != item.sha256:
        raise ValueError(f"{item.name}: SHA256 mismatch: expected {item.sha256}, observed {actual}")
    return {"path": str(path.resolve()), "sha256": actual, "size_bytes": size, "url": item.url}


def download(item: ReaderInput, temporary: Path) -> None:
    """Stream one URL with socket, byte and cooperative deadline bounds."""
    deadline = time.monotonic() + FETCH_TIMEOUT_SECONDS
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(item.url, timeout=SOCKET_TIMEOUT_SECONDS) as response:
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > item.maximum_bytes:
            raise ValueError(f"{item.name}: declared size exceeds {item.maximum_bytes} bytes")
        size = 0
        with temporary.open("wb") as stream:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"{item.name}: download deadline exceeded")
                chunk = response.read(min(65536, item.maximum_bytes - size + 1))
                if not chunk:
                    break
                size += len(chunk)
                if size > item.maximum_bytes:
                    raise ValueError(f"{item.name}: exceeds {item.maximum_bytes} bytes")
                stream.write(chunk)


def acquire(cache: Path, item: ReaderInput) -> dict[str, Any]:
    """Authenticate cache or publish only an authenticated bounded download."""
    target = cache / item.name
    if target.exists():
        return authenticate(target, item)
    descriptor, name = tempfile.mkstemp(prefix=f".{item.name}-", suffix=".download", dir=cache)
    os.close(descriptor)
    temporary = Path(name)
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--fetch", item.name, str(temporary)],
            capture_output=True,
            text=True,
            timeout=FETCH_TIMEOUT_SECONDS,
            check=False,
        )
        if result.returncode:
            raise ValueError(f"{item.name}: download failed ({result.returncode}): {result.stderr}")
        authenticate(temporary, item)
        temporary.replace(target)
        return authenticate(target, item)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(
            f"{item.name}: download exceeded {FETCH_TIMEOUT_SECONDS} seconds"
        ) from error
    finally:
        temporary.unlink(missing_ok=True)


def java_identity() -> dict[str, Any]:
    """Require the selected working JDK and retain reported properties."""
    selected = os.environ.get("SIMRECON_JAVA")
    executable = shutil.which(selected if selected is not None else "java")
    if executable is None:
        raise ValueError("Java unavailable: set SIMRECON_JAVA or put Java 21.0.7 on PATH")
    executable = str(Path(executable).resolve())
    try:
        result = subprocess.run(
            [executable, "-XshowSettings:properties", "-version"],
            capture_output=True,
            text=True,
            timeout=JAVA_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError(f"Java identity failed for {executable}: {error}") from error
    output = result.stdout + result.stderr
    properties = dict(re.findall(r"^\s*([\w.]+)\s*=\s*(.*?)\s*$", output, re.MULTILINE))
    if result.returncode or properties.get("java.version") != JAVA_VERSION:
        raise ValueError(
            f"Require Java {JAVA_VERSION}; status {result.returncode}, "
            f"observed {properties.get('java.version', 'unknown')}: {output}"
        )
    if not properties.get("java.vendor") or not properties.get("os.name"):
        raise ValueError("Java identity omitted vendor or platform")
    # A version string alone does not prove that this executable has the JDK source launcher.
    with tempfile.TemporaryDirectory(prefix="java-probe-", dir=CACHE) as directory:
        source = Path(directory) / "ReaderSetupProbe.java"
        source.write_text(
            "class ReaderSetupProbe { public static void main(String[] args) { "
            'System.out.print("simrecon-jdk-source-launcher"); } }\n'
        )
        try:
            probe = subprocess.run(
                [executable, str(source)],
                capture_output=True,
                text=True,
                timeout=JAVA_TIMEOUT_SECONDS,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ValueError(f"Java source launcher failed: {error}") from error
        if probe.returncode or probe.stdout != "simrecon-jdk-source-launcher":
            raise ValueError(f"Java source launcher failed ({probe.returncode}): {probe.stderr}")
    return {
        "executable": executable,
        "version": properties["java.version"],
        "vendor": properties["java.vendor"],
        "platform": {"os_name": properties["os.name"], "os_arch": properties.get("os.arch")},
        "version_output": output,
        "source_launcher_checked": True,
    }


def prepare() -> Path:
    """Publish a current identity manifest after all inputs pass."""
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = CACHE / "inputs.json"
    # A failed preparation must not leave a previous successful-looking identity.
    manifest.unlink(missing_ok=True)
    java = java_identity()
    jars = {item.name: acquire(CACHE, item) for item in INPUTS}
    document = {
        "schema": "org.simrecon.imagej-reader-inputs",
        "version": 1,
        "jars": jars,
        "java": java,
        "host_platform": platform.platform(),
        "purpose": "development reader inputs; no interoperability result or verification receipt",
    }
    manifest.write_text(json.dumps(document, indent=2) + "\n")
    return manifest


def main() -> int:
    """Run preparation or the parent-bounded internal download worker."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", nargs=2, metavar=("INPUT_NAME", "TEMPORARY_PATH"))
    arguments = parser.parse_args()
    try:
        if arguments.fetch:
            name, temporary = arguments.fetch
            item = next(item for item in INPUTS if item.name == name)
            destination = Path(temporary)
            if (
                destination.parent.resolve() != CACHE.resolve()
                or not destination.name.startswith(f".{item.name}-")
                or not destination.name.endswith(".download")
                or destination.is_symlink()
                or not destination.is_file()
            ):
                raise ValueError(
                    "Download worker requires its scoped existing temporary cache file"
                )
            download(item, destination)
        else:
            print(prepare())
    except (OSError, ValueError, TimeoutError, StopIteration) as error:
        print(f"Reader preparation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
