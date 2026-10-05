"""Blind public CLI tests for verification receipt contract V1–V5."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from verification_fixture_tools import PHASES

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).with_name("verification_fixture_tools.py")


def run(args, cwd, **kwargs):
    """Execute a public command while preserving coverage and diagnostics."""
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False, **kwargs)


def git(root, *args):
    result = run(["git", *args], root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("src/simrecon/sample.py", "scripts/sample.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"if flag:\n    value = 1\n")
    (root / "scripts/branchless.py").write_bytes(b"value = 1\n")
    (root / "candidate.txt").write_bytes(b"candidate\n")
    shutil.copyfile(ROOT / "Makefile", root / "Makefile")
    (root / ".gitignore").write_text("artifacts/\ndist/\ncalls.jsonl\n")
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Receipt fixture")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture candidate")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("make", "uv"):
        target = bin_dir / name
        target.write_text(f"#!{sys.executable}\n" + TOOLS.read_text())
        target.chmod(0o755)
    return root, bin_dir


def invoke(repository, mode="complete", extra=(), interpreter=None, receipt_path=None):
    root, bin_dir = repository
    env = os.environ.copy()
    env["RECEIPT_FIXTURE_MODE"] = mode
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    result = run(
        [
            interpreter or sys.executable,
            str(ROOT / "scripts/verify.py"),
            "--make",
            str(bin_dir / "make"),
            "--uv",
            str(bin_dir / "uv"),
            *extra,
        ],
        root,
        env=env,
    )
    path = root / (receipt_path or "artifacts/verification/receipt.json")
    receipt = json.loads(path.read_text()) if path.exists() else None
    return result, receipt


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failed(result, receipt):
    assert result.returncode != 0
    assert receipt is not None
    assert receipt["result"] == "failed"
    assert receipt["problems"]


@pytest.mark.parametrize("custom", [False, True])
def test_v1_complete_receipt(repository, custom):
    root, bin_dir = repository
    expected_manifest = {name: digest(root / name) for name in git(root, "ls-files").splitlines()}
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", "HEAD^{tree}")
    destination = "artifacts/custom/receipt.json" if custom else None
    result, receipt = invoke(
        repository,
        extra=("--receipt", destination) if custom else (),
        receipt_path=destination,
    )
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    assert receipt["schema"] == "org.simrecon.verification"
    assert receipt["version"] == 1
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    assert receipt["context"] == dict(contract=None, reviewed_tests=None, integration_base=None)
    assert receipt["inputs"] == {}
    for state in (receipt["before"], receipt["after"]):
        assert state["commit"] == commit
        assert state["tree"] == tree
        assert state["dirty"] is False
        assert state["manifest"] == expected_manifest
        assert state["untracked"] == []
    assert [phase["name"] for phase in receipt["phases"]] == PHASES
    for phase in receipt["phases"]:
        assert phase["returncode"] == 0
        assert phase["name"] in phase["command"]
        assert f"UV={bin_dir / 'uv'}" in phase["command"]
        log = Path(phase["log"])
        assert not log.is_absolute()
        assert f"controlled phase {phase['name']}" in (root / log).read_text()
        for key in ("started_at", "finished_at"):
            offset = datetime.fromisoformat(phase[key].replace("Z", "+00:00")).utcoffset()
            assert offset is not None
            assert offset.total_seconds() == 0
    for key in ("started_at", "finished_at"):
        offset = datetime.fromisoformat(receipt[key].replace("Z", "+00:00")).utcoffset()
        assert offset is not None
        assert offset.total_seconds() == 0
    metrics = {"statements": {"covered": 2, "total": 2}, "branches": {"covered": 2, "total": 2}}
    coverage = receipt["coverage"]
    assert coverage["files"] == {
        "src/simrecon/sample.py": metrics,
        "scripts/sample.py": metrics,
        "scripts/branchless.py": {
            "statements": {"covered": 1, "total": 1},
            "branches": {"covered": 0, "total": 0},
        },
    }
    assert coverage["packages"] == {
        "simrecon": metrics,
        "scripts": {
            "statements": {"covered": 3, "total": 3},
            "branches": {"covered": 2, "total": 2},
        },
    }
    assert coverage["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    assert coverage["reports"] == {
        "json": "artifacts/coverage/coverage.json",
        "html": "artifacts/coverage/html/index.html",
    }
    wheel = root / "dist/simrecon-1.2.0-py3-none-any.whl"
    assert receipt["artifact"] == {
        "path": str(wheel.relative_to(root)),
        "size_bytes": wheel.stat().st_size,
        "sha256": digest(wheel),
        "version": "1.2.0",
    }
    environment = receipt["environment"]
    assert Path(environment["python"]["executable"]).resolve() == Path(sys.executable).resolve()
    assert environment["python"]["version"]
    assert environment["platform"]
    for name in ("make", "uv", "git"):
        assert environment[name]["executable"]
        assert environment[name]["version"]
    assert set(environment["tools"]) == {"ruff", "pyright", "coverage", "pytest"}


def test_v1_real_make_check(repository):
    root, bin_dir = repository
    result = run(
        ["/usr/bin/make", "-f", str(ROOT / "Makefile"), "check", f"UV={bin_dir / 'uv'}"], root
    )
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert calls == [
        ["sync", "--locked", "--all-groups"],
        ["run", "--locked", "ruff", "check", "src", "tests", "scripts"],
        ["run", "--locked", "ruff", "format", "--check", "src", "tests", "scripts"],
        ["run", "--locked", "pyright"],
    ]

    (root / "calls.jsonl").unlink()
    for phase in ("sync", "lint", "format", "types"):
        shared = run(["/usr/bin/make", phase, f"UV={bin_dir / 'uv'}"], root)
        assert shared.returncode == 0, shared.stderr
    shared_calls = [json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()]
    assert shared_calls == calls


def test_v2_command_failure(repository):
    result, receipt = invoke(repository, "command-failure")
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 23
    assert [phase["name"] for phase in receipt["phases"]] == PHASES[:3]
    assert receipt["phases"][-1]["returncode"] == 23
    assert "controlled failure diagnostic" in result.stdout + result.stderr
    assert receipt["before"] == receipt["after"]


def test_v2_missing_executable(repository):
    root, bin_dir = repository
    (bin_dir / "make").unlink()
    result, receipt = invoke(repository)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 127
    assert git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    "mode",
    [
        "missing-json",
        "missing-html",
        "missing-owned",
        "partial-coverage",
        "excluded-coverage",
        "malformed-coverage",
        "no-native-branches",
        "missing-native-numerator",
        "missing-native-destinations",
        "missing-wheel",
        "multiple-wheels",
        "invalid-wheel",
    ],
)
def test_v3_incomplete_evidence(repository, mode):
    root, bin_dir = repository
    if mode in {"missing-json", "missing-html", "missing-wheel"}:
        env = os.environ.copy()
        env["RECEIPT_FIXTURE_MODE"] = "complete"
        for phase in ("coverage-json", "coverage-html", "wheel"):
            seeded = run([str(bin_dir / "make"), phase], root, env=env)
            assert seeded.returncode == 0, seeded.stderr
        assert (root / "artifacts/coverage/coverage.json").is_file()
        assert (root / "artifacts/coverage/html/index.html").is_file()
        assert (root / "dist/simrecon-1.2.0-py3-none-any.whl").is_file()
    result, receipt = invoke(repository, mode)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 1


@pytest.mark.parametrize("mode", ["dirty-start", "tracked-change", "commit-change"])
def test_v4_candidate_changes(repository, mode):
    root, _ = repository
    if mode == "dirty-start":
        (root / "candidate.txt").write_bytes(b"dirty\n")
    before_commit = git(root, "rev-parse", "HEAD")
    before_tree = git(root, "rev-parse", "HEAD^{tree}")
    result, receipt = invoke(repository, mode)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 1
    after_commit = git(root, "rev-parse", "HEAD")
    after_tree = git(root, "rev-parse", "HEAD^{tree}")
    assert receipt["before"]["commit"] == before_commit
    assert receipt["before"]["tree"] == before_tree
    assert receipt["after"]["commit"] == after_commit
    assert receipt["after"]["tree"] == after_tree
    if mode == "commit-change":
        assert after_commit != before_commit
        assert after_tree != before_tree
    if mode == "dirty-start":
        assert receipt["before"]["dirty"] is True
    else:
        assert (
            receipt["before"]["manifest"]["candidate.txt"]
            == hashlib.sha256(b"candidate\n").hexdigest()
        )
        assert (
            receipt["after"]["manifest"]["candidate.txt"]
            == hashlib.sha256(
                b"new commit\n" if mode == "commit-change" else b"changed\n"
            ).hexdigest()
        )


def test_v5_context_and_private_input(repository, tmp_path):
    root, _ = repository
    (root / "unrelated-local.txt").write_bytes(b"unapproved local bytes")
    private = tmp_path / "private-owner-data.bin"
    payload = b"private bytes must never appear in receipt\x00"
    private.write_bytes(payload)
    result, receipt = invoke(
        repository,
        extra=(
            "--contract",
            "VRC-01",
            "--reviewed-tests",
            "review-label",
            "--base",
            "base-label",
            "--input",
            f"approved={private}",
        ),
    )
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    assert receipt["context"] == {
        "contract": "VRC-01",
        "reviewed_tests": "review-label",
        "integration_base": "base-label",
    }
    fingerprint = {"size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    for state in (receipt["before"], receipt["after"]):
        assert state["untracked"] == ["unrelated-local.txt"]
        assert "unrelated-local.txt" not in state["manifest"]
    assert "unapproved local bytes" not in json.dumps(receipt)
    assert receipt["inputs"] == {"approved": {"before": fingerprint, "after": fingerprint}}
    assert str(private) not in json.dumps(receipt)
    assert "private bytes" not in json.dumps(receipt)


@pytest.mark.parametrize("kind", ["duplicate", "unnamed", "directory", "missing", "changed"])
def test_v5_invalid_inputs(repository, tmp_path, monkeypatch, kind):
    private = tmp_path / "private-input.bin"
    private.write_bytes(b"original input")
    extra = ["--input", f"approved={private}"]
    if kind == "duplicate":
        extra += ["--input", f"approved={private}"]
    elif kind == "unnamed":
        extra = ["--input", f"={private}"]
    elif kind == "directory":
        extra = ["--input", f"approved={tmp_path}"]
    elif kind == "missing":
        private.unlink()
    monkeypatch.setenv("RECEIPT_PRIVATE_INPUT", str(private))
    result, receipt = invoke(repository, "input-change" if kind == "changed" else "complete", extra)
    assert result.returncode in (1, 2)
    assert "can't open file" not in result.stderr
    if receipt is None:
        assert result.returncode == 2
        assert "error:" in result.stderr
    if receipt is not None:
        assert receipt is not None
        failed(result, receipt)
        assert str(private) not in json.dumps(receipt)
        assert "original input" not in json.dumps(receipt)
    if kind == "changed":
        assert result.returncode == 1
        assert receipt is not None
        failed(result, receipt)
        assert receipt["inputs"]["approved"]["before"] == {
            "size_bytes": 14,
            "sha256": hashlib.sha256(b"original input").hexdigest(),
        }
        assert receipt["inputs"]["approved"]["after"] == {
            "size_bytes": 13,
            "sha256": hashlib.sha256(b"changed input").hexdigest(),
        }


def test_v1_native_system_python_entry(repository):
    result, receipt = invoke(repository, interpreter="/usr/bin/python3")
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    assert receipt["result"] == "passed"
    native_version = run(["/usr/bin/python3", "--version"], repository[0])
    assert native_version.returncode == 0
    assert native_version.stdout.strip().split()[-1] in receipt["environment"]["python"]["version"]


def test_v4_forbidden_tracked_receipt(repository):
    root, _ = repository
    original = (root / "candidate.txt").read_bytes()
    result, _ = invoke(repository, extra=("--receipt", "candidate.txt"))
    assert result.returncode != 0
    assert "can't open file" not in result.stderr
    assert (root / "candidate.txt").read_bytes() == original
    assert git(root, "status", "--porcelain") == ""


def test_v5_malformed_input_syntax(repository):
    result, receipt = invoke(repository, extra=("--input", "missing-equals"))
    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "can't open file" not in result.stderr
    if receipt is not None:
        assert receipt is not None
        failed(result, receipt)
