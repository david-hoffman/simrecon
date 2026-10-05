"""Blind public CLI tests for verification receipt contract V1–V5."""

import base64
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from verification_fixture_tools import PHASES, TAG_WHEELS

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
        "inconsistent-native-destinations",
        "conflicting-metadata",
        "invalid-wheel-format",
        "incomplete-record",
        "invalid-record-self",
        "record-hash-mismatch",
        "record-size-mismatch",
        "weak-wheel-hash",
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


@pytest.mark.parametrize(
    "mode,status,last",
    [
        ("partial-json-failure", 29, "coverage-json"),
        ("wheel-build-failure", 31, "wheel"),
    ],
)
def test_v2_same_run_evidence_survives_phase_failure(repository, mode, status, last):
    root, bin_dir = repository
    # Seed complete evidence; coverage-clean must remove it before this run.
    for phase in ("coverage-json", "coverage-html", "wheel"):
        seeded = run([str(bin_dir / "make"), phase], root)
        assert seeded.returncode == 0
    result, receipt = invoke(repository, mode)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == status
    assert [p["name"] for p in receipt["phases"]] == PHASES[: PHASES.index(last) + 1]
    assert receipt["phases"][-1]["returncode"] == status
    if mode == "partial-json-failure":
        assert not (root / "artifacts/coverage/html/index.html").exists()
        assert receipt["coverage"] is not None, json.dumps(receipt["problems"])
        assert receipt["coverage"]["global"] == {
            "statements": {"covered": 5, "total": 5},
            "branches": {"covered": 2, "total": 4},
        }
        assert receipt["coverage"]["files"]["src/simrecon/sample.py"]["branches"] == {
            "covered": 1,
            "total": 2,
        }
    else:
        wheel = root / "dist/simrecon-1.2.0-py3-none-any.whl"
        assert receipt["artifact"] is not None, json.dumps(receipt["problems"])
        assert receipt["artifact"] == {
            "path": str(wheel.relative_to(root)),
            "size_bytes": wheel.stat().st_size,
            "sha256": digest(wheel),
            "version": "1.2.0",
        }


def test_v3_stronger_record_hash_is_valid(repository):
    result, receipt = invoke(repository, "sha512-wheel")
    assert receipt is not None
    assert result.returncode == 0, json.dumps(receipt["problems"])
    assert receipt["result"] == "passed"
    assert receipt["artifact"]["version"] == "1.2.0"
    assert "wheel-import" in [p["name"] for p in receipt["phases"]]


@pytest.mark.parametrize("identity_available", [False, True])
@pytest.mark.parametrize("destination", ["candidate.txt", ".git/config"])
def test_v4_output_protection_with_missing_tracked_file(
    repository, destination, identity_available
):
    root, _ = repository
    protected = root / destination
    original = protected.read_bytes()
    (root / "scripts/branchless.py").unlink()
    if not identity_available:
        (root / ".git/HEAD").unlink()
    result, _ = invoke(repository, extra=("--receipt", destination))
    assert result.returncode != 0
    assert protected.read_bytes() == original, f"protected output overwritten: {destination}"
    assert not (root / "scripts/branchless.py").exists()


def test_v4_unavailable_final_identity_fails(repository):
    result, receipt = invoke(repository, "unavailable-final-identity")
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 1
    assert receipt["after"] is None or receipt["after"]["commit"] is None


def test_v4_output_directory_symlink_cannot_write_git_metadata(repository):
    root, _ = repository
    metadata = {
        p.relative_to(root / ".git"): p.read_bytes()
        for p in (root / ".git").rglob("*")
        if p.is_file()
    }
    (root / "scripts/branchless.py").unlink()
    (root / "artifacts").mkdir()
    (root / "artifacts/verification").symlink_to(root / ".git", target_is_directory=True)
    result, _ = invoke(repository)
    assert result.returncode != 0
    after = {
        p.relative_to(root / ".git"): p.read_bytes()
        for p in (root / ".git").rglob("*")
        if p.is_file()
    }
    assert after == metadata, sorted(
        str(name) for name in set(after) | set(metadata) if after.get(name) != metadata.get(name)
    )


@pytest.mark.parametrize("identity_available", [False, True])
def test_v4_tracked_phase_logs_preserved_with_missing_file(repository, identity_available):
    root, _ = repository
    result, receipt = invoke(repository)
    assert result.returncode == 0
    assert receipt is not None
    # Use public receipt paths only to select destinations. Sentinel bytes are
    # independently chosen; product output supplies no expected content.
    names = [phase["log"] for phase in receipt["phases"]]
    sentinel = b"tracked log destination must survive\n"
    for name in names:
        (root / name).write_bytes(sentinel)
        git(root, "add", "-f", name)
    git(root, "commit", "-qm", "tracked output protection fixture")
    (root / "scripts/branchless.py").unlink()
    if not identity_available:
        (root / ".git/HEAD").unlink()
    result, _ = invoke(repository)
    assert result.returncode != 0
    for name in names:
        assert (root / name).read_bytes() == sentinel, f"tracked phase log overwritten: {name}"


@pytest.fixture
def linked_repository(repository, tmp_path, monkeypatch):
    """Create a disposable linked worktree with independently located metadata."""
    root, bin_dir = repository
    linked = tmp_path / "linked"
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    git(root, "worktree", "add", "-q", "-b", "receipt-linked", str(linked))
    private_git = Path(git(linked, "rev-parse", "--absolute-git-dir"))
    common_git = (linked / git(linked, "rev-parse", "--git-common-dir")).resolve()
    assert private_git != common_git
    assert common_git == root / ".git"
    assert (linked / ".git").is_file()
    return (linked, bin_dir), common_git


def test_v4_linked_worktree_shared_config_preserved(linked_repository):
    repository, common_git = linked_repository
    root, _ = repository
    config = common_git / "config"
    original_config = config.read_bytes()
    before_state = {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "status": git(root, "status", "--porcelain"),
        "refs": git(root, "show-ref"),
        "worktrees": git(root, "worktree", "list", "--porcelain"),
    }
    metadata = {
        p.relative_to(common_git): p.read_bytes() for p in common_git.rglob("*") if p.is_file()
    }
    git_pointer = (root / ".git").read_bytes()
    result, _ = invoke(repository, extra=("--receipt", str(config)))
    after_metadata = {
        p.relative_to(common_git): p.read_bytes() for p in common_git.rglob("*") if p.is_file()
    }
    assert config.read_bytes() == original_config, "shared Git config overwritten"
    assert result.returncode != 0
    assert after_metadata == metadata, "shared or per-worktree Git metadata changed"
    assert (root / ".git").read_bytes() == git_pointer
    assert {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "status": git(root, "status", "--porcelain"),
        "refs": git(root, "show-ref"),
        "worktrees": git(root, "worktree", "list", "--porcelain"),
    } == before_state


def test_v1_linked_worktree_normal_receipt_succeeds(linked_repository):
    repository, _ = linked_repository
    root, _ = repository
    expected_state = {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "dirty": False,
        "untracked": [],
        "manifest": {name: digest(root / name) for name in git(root, "ls-files").splitlines()},
    }
    assert git(root, "status", "--porcelain") == ""
    result, receipt = invoke(repository)
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    assert receipt["before"] == expected_state
    assert receipt["after"] == expected_state
    assert [phase["name"] for phase in receipt["phases"]] == PHASES
    assert all(phase["returncode"] == 0 for phase in receipt["phases"])
    assert git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize("mode", ["missing-metadata", "multiple-metadata", "duplicate-member"])
def test_v3_malformed_sole_wheel_metadata_or_archive(repository, mode):
    root, _ = repository
    result, receipt = invoke(repository, mode)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 1
    assert receipt["artifact"] is None
    assert [phase["name"] for phase in receipt["phases"]] == PHASES
    assert all(phase["returncode"] == 0 for phase in receipt["phases"])
    assert receipt["before"] == receipt["after"]
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    wheels = list((root / "dist").glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        assert len(metadata_names) == (
            0 if mode == "missing-metadata" else 2 if mode == "multiple-metadata" else 1
        )
        assert names.count("simrecon/__init__.py") == (2 if mode == "duplicate-member" else 1)


@pytest.mark.parametrize("phase", ["sync", "audit"])
@pytest.mark.parametrize(
    "target_kind", ["tracked", "ordinary-config", "common-config", "private-head"]
)
def test_v1_phase_log_symlink_protects_target(repository, linked_repository, phase, target_kind):
    ordinary_root, _ = repository
    linked, common_git = linked_repository
    selected = linked if target_kind in {"common-config", "private-head"} else repository
    root, _ = selected
    targets = {
        "tracked": ordinary_root / "candidate.txt",
        "ordinary-config": ordinary_root / ".git/config",
        "common-config": common_git / "config",
        "private-head": Path(git(root, "rev-parse", "--absolute-git-dir")) / "HEAD",
    }
    target = targets[target_kind].resolve(strict=True)
    original = target.read_bytes()
    result, receipt = invoke(selected)
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    leaf = root / next(item["log"] for item in receipt["phases"] if item["name"] == phase)
    leaf.unlink()
    leaf.symlink_to(target)
    assert leaf.is_symlink()
    assert leaf.resolve(strict=True) == target
    assert leaf.read_bytes() == original
    assert git(root, "check-ignore", str(leaf.relative_to(root))) == str(leaf.relative_to(root))
    assert git(root, "status", "--porcelain") == ""
    result, receipt = invoke(selected)
    # Check bytes first: an eventual failed identity check cannot excuse damage.
    assert target.read_bytes() == original, f"protected {target_kind} overwritten by {phase} log"
    assert result.returncode != 0
    if receipt is not None:
        failed(result, receipt)


def assert_tag_wheel_fixture(root, mode):
    """Independently verify sole fixture tags and every RECORD hash and size."""
    suffix, tags = TAG_WHEELS[mode]
    wheels = list((root / "dist").glob("*.whl"))
    assert [wheel.name for wheel in wheels] == [f"simrecon-1.2.0-{suffix}.whl"]
    info = "simrecon-1.2.0.dist-info"
    with zipfile.ZipFile(wheels[0]) as archive:
        wheel_text = archive.read(f"{info}/WHEEL").decode("ascii")
        assert (
            tuple(
                line.removeprefix("Tag: ")
                for line in wheel_text.splitlines()
                if line.startswith("Tag: ")
            )
            == tags
        )
        rows = list(csv.reader(archive.read(f"{info}/RECORD").decode("ascii").splitlines()))
        assert {row[0] for row in rows} == set(archive.namelist())
        assert len(rows) == len(archive.namelist())
        for name, fingerprint, size in rows:
            if name == f"{info}/RECORD":
                assert (fingerprint, size) == ("", "")
            else:
                data = archive.read(name)
                expected = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
                assert fingerprint == f"sha256={expected.decode('ascii')}"
                assert int(size) == len(data)


@pytest.mark.parametrize(
    "mode",
    [
        "tag-missing-component",
        "tag-extra-component",
        "tag-empty-python",
        "tag-empty-abi",
        "tag-empty-platform",
        "tag-python-mismatch",
        "tag-abi-mismatch",
        "tag-platform-mismatch",
        "tag-incomplete-expansion",
        "tag-extra-expansion",
    ],
)
def test_v3_declared_wheel_tags_rejected(repository, mode):
    result, receipt = invoke(repository, mode)
    assert_tag_wheel_fixture(repository[0], mode)
    assert receipt is not None
    failed(result, receipt)
    assert result.returncode == 1
    assert receipt["artifact"] is None
    assert [item["name"] for item in receipt["phases"]] == PHASES
    assert all(item["returncode"] == 0 for item in receipt["phases"])
    assert receipt["before"] == receipt["after"]


@pytest.mark.parametrize("mode", ["tag-valid-compressed", "tag-valid-build-platform"])
def test_v1_declared_wheel_tags_accepted(repository, mode):
    root, _ = repository
    result, receipt = invoke(repository, mode)
    assert_tag_wheel_fixture(root, mode)
    assert result.returncode == 0, result.stderr
    assert receipt is not None
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    wheels = list((root / "dist").glob("*.whl"))
    assert len(wheels) == 1
    assert receipt["artifact"] == {
        "path": str(wheels[0].relative_to(root)),
        "size_bytes": wheels[0].stat().st_size,
        "sha256": digest(wheels[0]),
        "version": "1.2.0",
    }
    assert [item["name"] for item in receipt["phases"]] == PHASES
