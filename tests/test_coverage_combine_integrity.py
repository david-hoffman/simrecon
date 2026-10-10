"""Native coverage integrity through the public Makefile phase."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest
from coverage import CoverageData
from coverage.exceptions import DataError

ROOT = Path(__file__).resolve().parents[1]


def _write_shard(base: Path, source: Path, suffix: str, arcs: set[tuple[int, int]]) -> Path:
    data = CoverageData(basename=str(base), suffix=suffix)
    data.add_arcs({str(source): arcs})
    data.write()
    shard = Path(data.data_filename())
    observed = CoverageData(basename=str(shard))
    observed.read()
    assert set(observed.arcs(str(source)) or []) == arcs
    return shard


def _combine(base: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    make = shutil.which("make")
    uv = os.environ.get("UV") or shutil.which("uv")
    assert make is not None, "the verification phase requires make"
    assert uv is not None, "the verification phase requires uv"
    environment = os.environ.copy()
    environment["COVERAGE_FILE"] = str(base)
    environment["UV_CACHE_DIR"] = str(tmp_path / "uv-cache")
    environment["UV_NO_SYNC"] = "1"
    return subprocess.run(
        [make, "--no-print-directory", "coverage-combine", f"UV={uv}"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_valid_native_shards_combine(tmp_path: Path) -> None:
    source = tmp_path / "measured.py"
    source.write_text("first = 1\nsecond = 2\n", encoding="utf-8")
    base = tmp_path / ".coverage"
    _write_shard(base, source, "first", {(1, 2)})
    _write_shard(base, source, "second", {(2, -1)})

    result = _combine(base, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    combined = CoverageData(basename=str(base))
    combined.read()
    assert combined.measured_files() == {str(source)}
    assert set(combined.arcs(str(source)) or []) == {(1, 2), (2, -1)}


def test_mixed_readable_and_malformed_shards_fail(tmp_path: Path) -> None:
    source = tmp_path / "measured.py"
    source.write_text("first = 1\nsecond = 2\n", encoding="utf-8")
    base = tmp_path / ".coverage"
    _write_shard(base, source, "readable", {(1, 2)})
    malformed = _write_shard(base, source, "malformed", {(2, -1)})
    original = malformed.read_bytes()
    assert len(original) > 8192
    truncated = original[:8192]
    malformed.write_bytes(truncated)
    with pytest.raises(DataError):
        CoverageData(basename=str(malformed)).read()

    result = _combine(base, tmp_path)

    assert result.returncode != 0, result.stdout + result.stderr
    assert malformed.read_bytes() == truncated
