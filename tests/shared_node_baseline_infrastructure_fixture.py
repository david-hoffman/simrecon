"""Owned disposable CLI fixtures; no production source is inspected.

Native reports and built wheel below describe this tiny fixture only. They do
not establish production coverage, scientific results, or canonical verification.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
HARNESS = ROOT / "scripts/source_free_check.py"
PINNED = {
    "c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9": 70_000_000,
    "2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20": 10_000_000,
}


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout: float = 58,
) -> subprocess.CompletedProcess[str]:
    """Keep child diagnostics inherited and bound time/output sent to assertions."""
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    assert len(result.stdout) + len(result.stderr) < 100_000, "unbounded fixture output"
    return result


def python(
    args: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return run(
        [str(PYTHON), str(HARNESS), "--timeout", "50", "python", *args],
        cwd=cwd,
        env=env,
    )


def probe(tmp_path: Path, code: str) -> Path:
    path = tmp_path / "owned_probe.py"
    path.write_text(textwrap.dedent(code), encoding="utf-8")
    return path


def authenticated_jars() -> dict[str, Path]:
    found = {digest(path): path for path in (ROOT / "artifacts/imagej-reader").glob("*.jar")}
    assert PINNED.keys() <= found.keys(), "incomplete real pinned-cache capability"
    for identity, maximum in PINNED.items():
        assert found[identity].stat().st_size <= maximum
    return {identity: found[identity] for identity in PINNED}


def reader_layout(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    # Opaque copies are execution inputs, never an expectation source.
    shutil.copyfile(ROOT / "scripts/prepare_imagej_reader.py", scripts / "prepare_imagej_reader.py")
    cache = tmp_path / "artifacts/imagej-reader"
    cache.mkdir(parents=True)
    jars = {}
    for identity, original in authenticated_jars().items():
        target = cache / original.name
        shutil.copyfile(original, target)
        assert digest(target) == identity
        jars[identity] = target
    return cache, jars


def java_environment(*, path_selection: bool = False) -> dict[str, str]:
    env = os.environ.copy()
    selected = env.get("SIMRECON_JAVA")
    assert selected and Path(selected).is_file(), "incomplete real Java capability"
    if path_selection:
        env.pop("SIMRECON_JAVA")
        env["PATH"] = str(Path(selected).parent) + os.pathsep + env.get("PATH", "")
    return env
