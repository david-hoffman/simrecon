"""CE01 R01/R02/R03: real public absence, neutral use and isolated wheel closure."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest

from c_equivalence_retirement_fixture import (
    RETIRED_MODULES,
    RETIRED_SCRIPTS,
    neutral_io,
    observe_boundary,
    retired_members,
)

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/source_free_check.py"


def checked(argv: list[str], *, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Inherited source-free child diagnostics; bounded waits and honest status."""
    result = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    assert result.returncode == 0, (
        f"command status={result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    return result


def test_source_retired_public_attributes_absent() -> None:
    observed = observe_boundary()
    assert not observed["missing_neutral"], observed["missing_neutral"]
    assert not observed["retired_attributes"], observed["retired_attributes"]


def test_source_retired_modules_unavailable() -> None:
    observed = observe_boundary()
    assert not observed["importable_retired_modules"], observed["importable_retired_modules"]


def test_source_retired_code_paths_absent() -> None:
    paths = [ROOT / "src" / (name.replace(".", "/") + ".py") for name in RETIRED_MODULES]
    paths.extend(ROOT / name for name in RETIRED_SCRIPTS)
    present = [str(path.relative_to(ROOT)) for path in paths if path.exists()]
    assert not present, present


def test_source_neutral_public_io(tmp_path: Path) -> None:
    assert neutral_io(tmp_path / "neutral") == {
        "source": str(tmp_path / "neutral/input.priism"),
        "planes": 1,
        "samples": 6,
    }


@pytest.mark.parametrize(
    "member",
    [
        "docs/simrecon/_otf.md",
        "simrecon/_otf.txt",
        "x.dist-info/licenses/simrecon/_otf.txt",
        "docs/simrecon/_otf.py",
        "x.dist-info/licenses/simrecon/_otf.py",
        "simrecon/_otf.py.txt",
        "simrecon/_otf.so.txt",
        "simrecon/__pycache__/_otf.cpython-313.pyc.txt",
        "simrecon/_otf_notes.py",
        "simrecon/_otf_extra/__init__.py",
        "x.data/purelib/simrecon/_otf.md",
        "x.data/platlib/simrecon/_otf.txt",
        "x.data/data/simrecon/_otf.py",
        "x.data/scripts/simulation_sources.txt",
        "docs/scripts/simulation_sources.py",
        "x.dist-info/licenses/scripts/simulation_sources.py",
        "scripts/simulation_sources.py.md",
    ],
)
def test_wheel_member_oracle_allows_nonexecuting_evidence(member: str) -> None:
    """R01/R04: text and non-import-root evidence do not prove an active module."""
    assert retired_members([member]) == []


@pytest.mark.parametrize(
    "member",
    [
        "simrecon/_otf.py",
        "simrecon/_otf.pyc",
        "simrecon/__pycache__/_otf.cpython-313.pyc",
        "simrecon/__pycache__/_otf.cpython-313.opt-1.pyc",
        "simrecon/_otf.so",
        "simrecon/_otf.abi3.so",
        "simrecon/_otf.cpython-313-x86_64-linux-gnu.so",
        "simrecon/_otf.cpython-313-darwin.so",
        "simrecon/_otf.pyd",
        "simrecon/_otf.cp313-win_amd64.pyd",
        "simrecon/_otf/__init__.py",
        "simrecon/_otf/",
        "simrecon/_otf/namespace-evidence.txt",
        "x.data/purelib/simrecon/_otf.py",
        "x.data/platlib/simrecon/_otf.abi3.so",
        "x.data/purelib/simrecon/_otf/namespace-evidence.txt",
        "x.data/platlib/simrecon/__pycache__/_otf.cpython-313.pyc",
        "scripts/simulation_sources.py",
        "simulation_sources.py",
        "x.data/purelib/scripts/simulation_sources.py",
        "x.data/scripts/simulation_sources.py",
        "x.data/scripts/simulation_sources",
        "x.data/scripts/simulation_sources.pyc",
    ],
)
def test_wheel_member_oracle_rejects_retired_executable_paths(member: str) -> None:
    """R01/R03: importable packages, namespace paths and shipped code stay banned."""
    assert retired_members([member]) == [member]


def test_wheel_member_oracle_keeps_only_forbidden_members() -> None:
    """A permitted evidence neighbor cannot suppress the executable violation."""
    forbidden = "x.data/purelib/simrecon/_otf.py"
    assert retired_members(
        ["simrecon/_otf.txt", forbidden, "x.dist-info/licenses/simrecon/_otf.txt"]
    ) == [forbidden]


@pytest.fixture(scope="module")
def installed_wheel(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """Build with the project's pinned uv backend, then install without dependencies."""
    directory = tmp_path_factory.mktemp("ce01-wheel")
    uv = os.environ.get("UV") or shutil.which("uv")
    assert uv is not None, "locked uv wheel builder is required"
    built = directory / "dist"
    checked([uv, "build", "--offline", "--wheel", "--out-dir", str(built)], cwd=ROOT)
    wheels = list(built.glob("*.whl"))
    assert len(wheels) == 1
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        members = archive.namelist()
    installed = directory / "installed"
    checked(
        [
            uv,
            "pip",
            "install",
            "--offline",
            "--no-deps",
            "--no-index",
            "--python",
            sys.executable,
            "--target",
            str(installed),
            str(wheel),
        ],
        cwd=directory,
    )
    probe = directory / "public-caller.py"
    shutil.copyfile(ROOT / "tests/c_equivalence_retirement_fixture.py", probe)
    result = checked(
        [
            sys.executable,
            str(HARNESS),
            "--timeout",
            "60",
            "python",
            str(probe),
            str(installed),
            str(ROOT),
            str(directory / "neutral"),
        ],
        cwd=directory,
    )
    return {
        "members": members,
        "observed": json.loads(result.stdout),
        "installed": installed,
        "probe": probe,
        "directory": directory,
    }


def test_installed_wheel_retired_members_absent(installed_wheel: dict[str, Any]) -> None:
    assert not retired_members(installed_wheel["members"])


def test_installed_wheel_retired_attributes_absent(installed_wheel: dict[str, Any]) -> None:
    observed = installed_wheel["observed"]
    assert not observed["missing_neutral"], observed["missing_neutral"]
    assert not observed["retired_attributes"], observed["retired_attributes"]


def test_installed_wheel_retired_modules_unavailable(installed_wheel: dict[str, Any]) -> None:
    observed = installed_wheel["observed"]
    assert not observed["importable_retired_modules"], observed["importable_retired_modules"]


def test_installed_wheel_neutral_io_and_cli(installed_wheel: dict[str, Any]) -> None:
    assert installed_wheel["observed"]["neutral_io"]["samples"] == 6
    directory = installed_wheel["directory"]
    prefix = [
        sys.executable,
        str(HARNESS),
        "--timeout",
        "60",
        "python",
        str(installed_wheel["probe"]),
        str(installed_wheel["installed"]),
        str(ROOT),
        "--cli",
    ]
    source = directory / "neutral/input.priism"
    inspected = checked([*prefix, "inspect", str(source)], cwd=directory)
    assert json.loads(inspected.stdout)["stored_shape"] == [1, 2, 3]
    for command, name in (("convert", "cli.mrc"), ("export-imagej", "cli.ome.tif")):
        result = checked(
            [
                *prefix,
                command,
                str(source),
                str(directory / name),
                "--config",
                str(directory / "neutral/config.json"),
            ],
            cwd=directory,
        )
        assert json.loads(result.stdout)["planes_written"] == 1
