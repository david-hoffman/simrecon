"""Exercise artifact separation through the real installed-wheel verification command."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def wheel_repository(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str]:
    """Build both distributions into their separate caller-owned output locations."""
    root = tmp_path_factory.mktemp("separate-installed-wheels")
    uv = os.environ.get("UV") or shutil.which("uv")
    assert uv is not None
    for name in ("pyproject.toml", "uv.lock", "devtools/pyproject.toml"):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    for project, output in (
        (ROOT, root / "dist"),
        (ROOT / "devtools", root / "artifacts/devtools/dist"),
    ):
        result = subprocess.run(
            [uv, "build", "--offline", "--wheel", str(project), "--out-dir", str(output)],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert len(list(output.glob("*.whl"))) == 1
    return root, uv


def test_installed_product_and_devtools_are_independent(wheel_repository: tuple[Path, str]) -> None:
    """Public artifact imports and real console callers prove the packaging boundary."""
    root, uv = wheel_repository
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_installed_wheels.py"), "--uv", uv],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "installed product: 36 exports, console CLI, runtime-only environment" in result.stdout
    assert "installed devtools: doctor caller and strict pytest" in result.stdout
    assert result.stdout.count("sha256=") == 2


def test_installed_check_rejects_harness_code_in_product(
    wheel_repository: tuple[Path, str], tmp_path: Path
) -> None:
    """A leaked utility is rejected before installation, even beside a valid product."""
    root, uv = wheel_repository
    contaminated = tmp_path / "repository"
    shutil.copytree(root / "dist", contaminated / "dist")
    shutil.copytree(root / "artifacts", contaminated / "artifacts")
    wheel = next((contaminated / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("simrecon/_delivery.py", "raise RuntimeError('leaked utility')\n")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_installed_wheels.py"), "--uv", uv],
        cwd=contaminated,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2
    assert "product wheel contains repository development utilities" in result.stderr
