"""Owned CLI workspaces and filesystem observations for disk lifecycle tests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv/bin/python"
HARNESS = ROOT / "scripts/source_free_check.py"
PAYLOAD = b"small lifecycle payload\x00\xff"


@dataclass(frozen=True)
class ChildRun:
    """A new namespace; records and targets are outside its disposable bases."""

    home: Path
    temporary: Path
    records: Path
    targets: Path

    def record(self, name: str) -> dict[str, Any]:
        return json.loads((self.records / f"{name}.json").read_text())

    def preserved(self) -> dict[str, str]:
        """Compare original bytes, original link text, and resolved link bytes."""
        paths = (
            self.targets / "target.bin",
            self.targets / "directory" / "input.bin",
            self.records / "report-sentinel.json",
            self.records / "coverage-sentinel.bin",
            self.records / "m25-sentinel.bin",
        )
        result = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        link = self.targets / "original-link"
        result["original-link-text"] = os.readlink(link)
        result["original-link-resolution"] = str(link.resolve(strict=True))
        result["original-link-bytes"] = hashlib.sha256(link.read_bytes()).hexdigest()
        return result

    def pytest(self, source: str, *, parallel: bool = False, explicit: bool = False) -> int:
        """Use the real opaque root configuration, without replacing its addopts."""
        test_file = self.home / "test_child.py"
        test_file.write_text(self.prelude() + textwrap.dedent(source))
        command = [
            str(PYTHON),
            str(HARNESS),
            "--timeout",
            "90",
            "pytest",
            "-c",
            str(ROOT / "pyproject.toml"),
            "-q",
            "-n",
            "4" if parallel else "0",
            "--dist",
            "loadgroup",
            "--max-worker-restart",
            "0",
        ]
        if explicit:
            command.extend(("--basetemp", str(self.home / "explicit-unused-base")))
        command.append(str(test_file))
        environment = os.environ.copy()
        for key in (
            "PYTEST_DEBUG_TEMPROOT",
            "PYTEST_ADDOPTS",
            "PYTEST_CURRENT_TEST",
            "PYTEST_XDIST_WORKER",
            "PYTEST_XDIST_WORKER_COUNT",
            "PYTEST_XDIST_TESTRUNUID",
        ):
            environment.pop(key, None)
        environment["TMPDIR"] = str(self.temporary)
        (self.records / "command.json").write_text(json.dumps(command, indent=2))
        before = self.preserved()
        (self.records / "preservation-before.json").write_text(json.dumps(before, indent=2))
        with (
            (self.records / "stdout.txt").open("w") as stdout,
            (self.records / "stderr.txt").open("w") as stderr,
        ):
            completed = subprocess.run(
                command,
                cwd=self.home,
                env=environment,
                stdout=stdout,
                stderr=stderr,
                timeout=105,
                check=False,
            )
        after = self.preserved()
        (self.records / "preservation-after.json").write_text(json.dumps(after, indent=2))
        (self.records / "status.json").write_text(
            json.dumps({"returncode": completed.returncode, "child_closed": True})
        )
        assert after == before, f"External bytes/link changed; records: {self.records}"
        return completed.returncode

    def prelude(self) -> str:
        """Only generated caller code; no dependency implementation is inspected."""
        return textwrap.dedent(
            f"""
            import json
            import os
            from pathlib import Path
            import pytest

            RECORDS = Path({str(self.records)!r})
            TARGETS = Path({str(self.targets)!r})
            PAYLOAD = {PAYLOAD!r}

            def save(name, **fields):
                (RECORDS / (name + '.json')).write_text(json.dumps(fields))

            def observe(name, path, factory, **fields):
                payload = path / 'payload.bin'
                payload.write_bytes(PAYLOAD)
                (path / 'file-link').symlink_to(TARGETS / 'target.bin')
                (path / 'directory-link').symlink_to(
                    TARGETS / 'directory', target_is_directory=True)
                base = factory.getbasetemp()
                controller = base.parent if os.environ.get('PYTEST_XDIST_WORKER') else base
                neighbor = controller.parent / 'distinct-owned-neighbor'
                neighbor.mkdir(exist_ok=True)
                (neighbor / 'keep.bin').write_bytes(PAYLOAD)
                save(name, path=str(path), base=str(base), neighbor=str(neighbor),
                     allocated_bytes=payload.stat().st_blocks * 512, **fields)

            @pytest.fixture(scope='module')
            def module_data(tmp_path_factory):
                path = tmp_path_factory.mktemp('module-data')
                (path / 'factory.bin').write_bytes(PAYLOAD)
                yield path
                assert (path / 'factory.bin').read_bytes() == PAYLOAD
                worker = os.environ.get('PYTEST_XDIST_WORKER', 'master')
                save('module-release-' + worker, path=str(path))

            @pytest.fixture(scope='session')
            def session_data(tmp_path_factory):
                path = tmp_path_factory.mktemp('session-data')
                (path / 'factory.bin').write_bytes(PAYLOAD)
                yield path
                assert (path / 'factory.bin').read_bytes() == PAYLOAD
                worker = os.environ.get('PYTEST_XDIST_WORKER', 'master')
                save('session-release-' + worker, path=str(path))
            """
        )


def make_child_run(parent: Path) -> ChildRun:
    """Make a new private CLI namespace, never reuse a prior basetemp."""
    home = Path(tempfile.mkdtemp(prefix="case-", dir=parent))
    temporary = home / "private-tmp"
    records = home / "records"
    targets = home / "external-targets"
    for path in (temporary, records, targets / "directory"):
        path.mkdir(parents=True)
    (targets / "target.bin").write_bytes(PAYLOAD)
    (targets / "directory" / "input.bin").write_bytes(PAYLOAD)
    (targets / "original-link").symlink_to("target.bin")
    for name in ("report-sentinel.json", "coverage-sentinel.bin", "m25-sentinel.bin"):
        (records / name).write_bytes(b"simulated preservation evidence\x00")
    return ChildRun(home, temporary, records, targets)


@pytest.fixture(name="child_run")
def child_run(tmp_path: Path) -> ChildRun:
    """Keep workspaces in the outer fixture through the end of every consumer."""
    return make_child_run(tmp_path)
