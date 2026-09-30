"""Contract checks for the configured pytest run policy."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _run_suite(tmp_path: Path, test_source: str | None) -> subprocess.CompletedProcess[str]:
    suite = tmp_path / "suite"
    suite.mkdir()
    if test_source is not None:
        (suite / "test_case.py").write_text(test_source, encoding="utf-8")

    env = os.environ.copy()
    env["PYTEST_ADDOPTS"] = "--tb=line --show-capture=no"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            str(PROJECT_ROOT / "pyproject.toml"),
            str(suite),
            "--tb=line",
            "--show-capture=no",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _check_result(
    result: subprocess.CompletedProcess[str], *, success: bool, diagnostic: str
) -> None:
    output = result.stdout + result.stderr
    if (result.returncode == 0) != success:
        pytest.fail(f"wrong pytest exit status: {result.returncode}")
    if not re.search(diagnostic, output, flags=re.IGNORECASE):
        pytest.fail(f"missing pytest diagnostic: {diagnostic}")
    if re.search(r"ERROR collecting|ImportError|ModuleNotFoundError|INTERNALERROR", output):
        pytest.fail("pytest encountered a collection, import, or internal error")


def test_complete_passing_suite_succeeds(tmp_path: Path) -> None:
    result = _run_suite(tmp_path, "def test_pass():\n    assert True\n")
    _check_result(result, success=True, diagnostic=r"\b1 passed\b")


def test_empty_discovery_fails(tmp_path: Path) -> None:
    result = _run_suite(tmp_path, None)
    _check_result(result, success=False, diagnostic=r"\bno tests ran\b")


def test_skipped_test_fails(tmp_path: Path) -> None:
    result = _run_suite(
        tmp_path, 'import pytest\n\ndef test_skip():\n    pytest.skip("planned skip")\n'
    )
    _check_result(result, success=False, diagnostic=r"\b1 skipped\b")


def test_expected_failure_fails(tmp_path: Path) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\n\n@pytest.mark.xfail(reason="expected failure")\n'
        "def test_xfail():\n    assert False\n",
    )
    _check_result(result, success=False, diagnostic=r"\b1 xfailed\b")


def test_non_strict_unexpected_pass_fails(tmp_path: Path) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\n\n@pytest.mark.xfail(strict=False, reason="unexpected pass")\n'
        "def test_xpass():\n    assert True\n",
    )
    _check_result(result, success=False, diagnostic=r"\b1 xpassed\b")
