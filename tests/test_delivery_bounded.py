"""Supplemental public CLI proof for the bounded FIX1 delivery pilot."""

from pathlib import Path

import pytest

import test_verification_receipt as receipt_tools
from verification_fixture_tools import PHASES

repository = receipt_tools.repository


def test_missing_make_retains_first_failure_without_later_phases_or_git_changes(
    repository: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
):
    # Reuse the frozen public fixture; only its disposable executable is removed.
    root, bin_dir = repository
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    expected_state = {
        "commit": receipt_tools.git(root, "rev-parse", "HEAD"),
        "tree": receipt_tools.git(root, "rev-parse", "HEAD^{tree}"),
        "dirty": False,
        "untracked": [],
        "manifest": {
            name: receipt_tools.digest(root / name)
            for name in receipt_tools.git(root, "ls-files").splitlines()
        },
    }
    assert receipt_tools.git(root, "status", "--porcelain") == ""
    metadata_before = {
        path.relative_to(root / ".git"): path.read_bytes()
        for path in (root / ".git").rglob("*")
        if path.is_file()
    }
    missing_make = bin_dir / "make"
    missing_make.unlink()
    assert not missing_make.exists()

    result, receipt = receipt_tools.invoke(repository)

    assert result.returncode == 127, result.stdout + result.stderr
    assert receipt is not None
    assert receipt["result"] == "failed"
    assert receipt["problems"]
    assert [phase["name"] for phase in receipt["phases"]] == [PHASES[0]]
    phase = receipt["phases"][0]
    assert phase["returncode"] == 127
    assert phase["command"][0] == str(missing_make)
    assert PHASES[0] in phase["command"]
    assert f"UV={bin_dir / 'uv'}" in phase["command"]

    log = Path(phase["log"])
    assert not log.is_absolute()
    diagnostic = (root / log).read_text()
    assert diagnostic.strip()
    assert "unavailable" in diagnostic.casefold()
    assert (result.stdout + result.stderr).count(diagnostic) == 1
    # Fixture commands record every non-version invocation independently of receipts.
    assert not (root / "calls.jsonl").exists()
    assert list((root / log.parent).glob("*.log")) == [root / log]

    assert receipt["before"] == expected_state
    assert receipt["after"] == expected_state
    assert receipt_tools.git(root, "status", "--porcelain") == ""
    assert receipt_tools.git(root, "rev-parse", "HEAD") == expected_state["commit"]
    assert receipt_tools.git(root, "rev-parse", "HEAD^{tree}") == expected_state["tree"]
    assert {
        name: receipt_tools.digest(root / name) for name in expected_state["manifest"]
    } == expected_state["manifest"]
    assert {
        path.relative_to(root / ".git"): path.read_bytes()
        for path in (root / ".git").rglob("*")
        if path.is_file()
    } == metadata_before
