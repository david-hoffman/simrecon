"""Blind public-entry proof of verification-owned output safety after phases."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from verification_fixture_tools import PHASES

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = Path("artifacts/verification/receipt.json")
MARKER = b"candidate must survive verification output persistence\x00\n"


def run(args: list[str], root: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=root, capture_output=True, text=True, check=False, timeout=300, **kwargs
    )


def git(root: Path, *args: str) -> str:
    result = run(["git", *args], root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


@dataclass(frozen=True)
class Repository:
    """Locate disposable candidate files, commands and authentic Git metadata."""

    root: Path
    bin_dir: Path
    common_git: Path
    private_git: Path


def create_repository(directory: Path, linked: bool = False) -> Repository:
    root = directory / "repo"
    root.mkdir(parents=True)
    for name in ("src/simrecon/sample.py", "scripts/sample.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"if flag:\n    value = 1\n")
    (root / "scripts/branchless.py").write_bytes(b"value = 1\n")
    (root / "candidate.txt").write_bytes(MARKER)
    # Copy the check entry opaquely; never inspect runtime/check source bytes.
    shutil.copyfile(ROOT / "Makefile", root / "Makefile")
    (root / ".gitignore").write_text(
        "artifacts/\ndist/\ncalls.jsonl\nactions.jsonl\n", encoding="utf-8"
    )
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Output protection fixture")
    git(root, "add", ".")
    git(root, "commit", "-qm", "disposable candidate")
    common_git = root / ".git"
    if linked:
        linked_root = directory / "linked"
        git(root, "worktree", "add", "-q", "-b", "output-fixture", str(linked_root))
        root = linked_root
    private_git = Path(git(root, "rev-parse", "--absolute-git-dir"))
    bin_dir = directory / "bin"
    bin_dir.mkdir()
    shutil.copyfile(
        ROOT / "tests/verification_fixture_tools.py", bin_dir / "verification_fixture_tools.py"
    )
    for name in ("make", "uv"):
        command = bin_dir / name
        command.write_text(
            f"#!{sys.executable}\n"
            + Path(__file__).with_name("verification_output_fixture.py").read_text(),
            encoding="utf-8",
        )
        command.chmod(0o755)
    return Repository(root, bin_dir, common_git, private_git)


@pytest.fixture(autouse=True)
def no_optional_git_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")


@pytest.fixture
def repository(tmp_path: Path) -> Repository:
    return create_repository(tmp_path)


def invoke(
    repository: Repository,
    action: dict[str, Any] | None = None,
    receipt_path: Path = RECEIPT,
    extra: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["OUTPUT_PROTECTION_ACTION"] = json.dumps(action or {})
    env["RECEIPT_FIXTURE_MODE"] = "complete"
    env["PATH"] = str(repository.bin_dir) + os.pathsep + env["PATH"]
    args = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/source_free_check.py"),
        "--timeout",
        "300",
        "python",
        str(ROOT / "scripts/verify.py"),
        "--make",
        str(repository.bin_dir / "make"),
        "--uv",
        str(repository.bin_dir / "uv"),
        "--receipt",
        str(receipt_path),
        *extra,
    ]
    result = run(args, repository.root, env=env)
    evidence = os.environ.get("OUTPUT_PROTECTION_EVIDENCE")
    if evidence:
        # Test-side command ledger only. No product seam or altered diagnostics.
        record = {
            "command": [arg.replace(str(repository.bin_dir), "<fixture-bin>") for arg in args],
            "status": result.returncode,
            "action": action,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "calls": calls(repository),
            "actions": action_observations(repository),
        }
        target = repository.root / action["target"] if action and action.get("target") else None
        record["target_after"] = (
            hashlib.sha256(target.read_bytes()).hexdigest() if target and target.is_file() else None
        )
        try:
            observed_receipt = load_receipt(repository, receipt_path)
        except (ValueError, OSError):
            observed_receipt = None
        record["receipt_phases"] = observed_receipt["phases"] if observed_receipt else None
        record["receipt_result"] = observed_receipt["result"] if observed_receipt else None
        record["challenged_log_phases"] = (
            [
                item["name"]
                for item in observed_receipt["phases"]
                if action and Path(item["log"]) == Path(action["destination"])
            ]
            if observed_receipt
            else None
        )
        with Path(evidence).open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
    return result


def load_receipt(repository: Repository, path: Path = RECEIPT) -> dict[str, Any] | None:
    destination = repository.root / path
    # An unsafe alias is observed via target bytes, never parsed as receipt JSON.
    if destination.is_symlink() or not destination.is_file():
        return None
    protected = [repository.root / name for name in ("candidate.txt", "scripts/branchless.py")]
    protected.extend(path for path in repository.common_git.rglob("*") if path.is_file())
    if (repository.root / ".git").is_file():
        protected.append(repository.root / ".git")
    if any(path.exists() and destination.samefile(path) for path in protected):
        return None
    return json.loads(destination.read_text(encoding="utf-8"))


def calls(repository: Repository) -> list[list[str]]:
    path = repository.root / "calls.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def metadata(repository: Repository) -> dict[Path, bytes]:
    snapshot = {
        path.relative_to(repository.common_git): path.read_bytes()
        for path in repository.common_git.rglob("*")
        if path.is_file()
    }
    if (repository.root / ".git").is_file():
        snapshot[Path("__linked_root_git_pointer__")] = (repository.root / ".git").read_bytes()
    return snapshot


def tracked_markers(repository: Repository) -> dict[str, bytes]:
    # Only independently authored fixture files, never opaque Makefile/runtime bytes.
    return {
        name: (repository.root / name).read_bytes()
        for name in ("candidate.txt", "scripts/branchless.py")
        if (repository.root / name).exists()
    }


def assert_trace(repository: Repository, receipt: dict[str, Any] | None) -> list[str]:
    # Public environment metadata may query uv separately from phase commands.
    # Keep the full executable ledger; compare phase-bearing calls to receipts.
    trace = [command for command in calls(repository) if any(arg in PHASES for arg in command)]
    phases = [next(arg for arg in command if arg in PHASES) for command in trace]
    assert phases == PHASES[: len(phases)], "phase reordering, retry or invented command"
    if receipt is not None:
        assert [item["name"] for item in receipt["phases"]] == phases
        assert [item["command"][1:] for item in receipt["phases"]] == trace
        assert all(
            item["command"][0] == str(repository.bin_dir / "make") for item in receipt["phases"]
        )
    return phases


def action_observations(repository: Repository) -> list[dict[str, Any]]:
    path = repository.root / "actions.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def assert_action(repository: Repository, phase: str, kind: str) -> None:
    actions = action_observations(repository)
    assert len(actions) == 1
    assert actions[0]["phase"] == phase
    assert actions[0]["kind"] == kind
    assert actions[0]["before"] == actions[0]["after"], "phase itself changed protected bytes"
    if kind == "hardlink":
        assert actions[0]["shares_target_inode"] is True


def assert_safe_outcome(
    repository: Repository,
    result: subprocess.CompletedProcess[str],
    receipt: dict[str, Any] | None,
    phase: str,
    kind: str,
    status: int = 0,
) -> list[str]:
    """Allow unused challenges, safe replacement and valid early rejection."""
    phases = assert_trace(repository, receipt)
    if action_observations(repository):
        assert_action(repository, phase, kind)
        assert phase in phases
        if status:
            assert result.returncode == status
            assert phases[-1] == phase
            if receipt is not None:
                assert receipt["phases"][-1]["returncode"] == status
    else:
        assert phase not in phases
        assert_rejected(result, receipt)
    if result.returncode == 0:
        assert receipt is not None and receipt["result"] == "passed"
        assert receipt["problems"] == []
        assert phases == PHASES
        assert all(item["returncode"] == 0 for item in receipt["phases"])
        assert receipt["before"] == receipt["after"]
    else:
        assert_rejected(result, receipt)
    return phases


def assert_rejected(
    result: subprocess.CompletedProcess[str], receipt: dict[str, Any] | None
) -> None:
    assert result.returncode != 0, result.stdout + result.stderr
    if receipt is not None:
        assert receipt["result"] == "failed"
        assert receipt["problems"]


@pytest.fixture(scope="module")
def log_candidates(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    # Publicly observed examples only. No name is required to recur in another
    # invocation; unused aliases and safe replacement satisfy the safety oracle.
    # The tested invocation's receipt alone supplies any actual leaf match.
    repository = create_repository(tmp_path_factory.mktemp("output-public-examples"))
    result = invoke(repository)
    receipt = load_receipt(repository)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "passed"
    assert assert_trace(repository, receipt) == PHASES
    return {item["name"]: Path(item["log"]) for item in receipt["phases"]}


@pytest.mark.parametrize("linked,custom", [(False, False), (False, True), (True, False)])
def test_p08_ordinary_outputs_preserve_identity_and_public_evidence(
    tmp_path: Path, linked: bool, custom: bool
) -> None:
    repository = create_repository(tmp_path, linked)
    before_metadata = metadata(repository)
    before_markers = tracked_markers(repository)
    commit = git(repository.root, "rev-parse", "HEAD")
    tree = git(repository.root, "rev-parse", "HEAD^{tree}")
    approved = tmp_path / "approved-input.bin"
    approved.write_bytes(b"private fixture input\x00")
    path = Path("artifacts/custom/evidence.json") if custom else RECEIPT
    result = invoke(repository, receipt_path=path, extra=("--input", f"approved={approved}"))
    receipt = load_receipt(repository, path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt is not None
    assert receipt["schema"] == "org.simrecon.verification" and receipt["version"] == 1
    assert receipt["result"] == "passed" and receipt["problems"] == []
    assert receipt["before"] == receipt["after"]
    assert receipt["before"]["commit"] == commit and receipt["before"]["tree"] == tree
    assert receipt["before"]["dirty"] is False
    assert receipt["before"]["manifest"]["candidate.txt"] == hashlib.sha256(MARKER).hexdigest()
    fingerprint = {"size_bytes": 22, "sha256": hashlib.sha256(approved.read_bytes()).hexdigest()}
    assert receipt["inputs"] == {"approved": {"before": fingerprint, "after": fingerprint}}
    assert str(approved) not in json.dumps(receipt)
    assert "private fixture input" not in json.dumps(receipt)
    assert assert_trace(repository, receipt) == PHASES
    for phase in receipt["phases"]:
        assert phase["returncode"] == 0
        assert f"UV={repository.bin_dir / 'uv'}" in phase["command"]
        assert f"controlled phase {phase['name']}" in (repository.root / phase["log"]).read_text()
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    wheel = repository.root / receipt["artifact"]["path"]
    assert receipt["artifact"]["sha256"] == hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata
    assert git(repository.root, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    "target_kind,phase,status,kind",
    [
        (target, phase, status, kind)
        for target, phase, status in [
            ("tracked", "types", 0),
            ("tracked", "audit", 0),
            ("tracked", "types", 23),
            ("missing-tracked", "types", 0),
            ("ordinary-config", "types", 0),
            ("common-config", "audit", 0),
            ("private-head", "types", 0),
            ("git-pointer", "types", 0),
        ]
        for kind in ("alias", "hardlink")
        if target != "missing-tracked" or kind == "alias"
    ],
)
def test_p02_phase_receipt_alias_preserves_protected_bytes(
    tmp_path: Path, target_kind: str, phase: str, status: int, kind: str
) -> None:
    repository = create_repository(
        tmp_path, target_kind in {"common-config", "private-head", "git-pointer"}
    )
    targets = {
        "tracked": repository.root / "candidate.txt",
        "missing-tracked": repository.root / "candidate.txt",
        "ordinary-config": repository.common_git / "config",
        "common-config": repository.common_git / "config",
        "private-head": repository.private_git / "HEAD",
        "git-pointer": repository.root / ".git",
    }
    target = targets[target_kind]
    before_markers = tracked_markers(repository)
    before_metadata = metadata(repository)
    action: dict[str, Any] = {
        "phase": phase,
        "kind": kind,
        "destination": str(RECEIPT),
        "target": str(target),
        "status": status,
    }
    if target_kind == "missing-tracked":
        action["identity_loss"] = "candidate.txt"
    result = invoke(repository, action)
    removed = target_kind == "missing-tracked" and bool(action_observations(repository))
    if removed:
        del before_markers["candidate.txt"]
    assert tracked_markers(repository) == before_markers, "receipt overwrote tracked bytes"
    assert metadata(repository) == before_metadata, "receipt altered Git metadata"
    if removed:
        assert not target.exists(), "receipt recreated a missing tracked file"
    receipt = load_receipt(repository)
    assert_safe_outcome(repository, result, receipt, phase, kind, status)
    if target_kind == "missing-tracked":
        assert_rejected(result, receipt)


@pytest.mark.parametrize(
    "target_kind,phase,status",
    [
        ("tracked", "sync", 0),
        ("tracked", "audit", 0),
        ("tracked", "sync", 23),
        ("common-config", "sync", 0),
        ("private-head", "audit", 0),
        ("git-pointer", "sync", 0),
    ],
)
@pytest.mark.parametrize("kind", ["alias", "hardlink"])
def test_p03_current_log_alias_preserves_bytes_and_original_failure(
    tmp_path: Path,
    log_candidates: dict[str, Path],
    target_kind: str,
    phase: str,
    status: int,
    kind: str,
) -> None:
    repository = create_repository(tmp_path, target_kind != "tracked")
    target = (
        repository.root / "candidate.txt"
        if target_kind == "tracked"
        else repository.common_git / "config"
        if target_kind == "common-config"
        else repository.root / ".git"
        if target_kind == "git-pointer"
        else repository.private_git / "HEAD"
    )
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    result = invoke(
        repository,
        {
            "phase": phase,
            "kind": kind,
            "destination": str(log_candidates[phase]),
            "target": str(target),
            "status": status,
        },
    )
    assert tracked_markers(repository) == before_markers, "current log overwrote tracked bytes"
    assert metadata(repository) == before_metadata, "current log altered Git metadata"
    receipt = load_receipt(repository)
    assert_safe_outcome(repository, result, receipt, phase, kind, status)


@pytest.mark.parametrize("target_kind", ["tracked", "common-config", "private-head", "git-pointer"])
@pytest.mark.parametrize("kind", ["alias", "hardlink"])
def test_p04_future_log_alias_is_revalidated(
    tmp_path: Path, log_candidates: dict[str, Path], target_kind: str, kind: str
) -> None:
    repository = create_repository(tmp_path, target_kind != "tracked")
    target = (
        repository.root / "candidate.txt"
        if target_kind == "tracked"
        else repository.common_git / "config"
        if target_kind == "common-config"
        else repository.root / ".git"
        if target_kind == "git-pointer"
        else repository.private_git / "HEAD"
    )
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    result = invoke(
        repository,
        {
            "phase": "sync",
            "kind": kind,
            "destination": str(log_candidates["types"]),
            "target": str(target),
        },
    )
    assert tracked_markers(repository) == before_markers, "future log overwrote tracked bytes"
    assert metadata(repository) == before_metadata, "future log altered Git metadata"
    receipt = load_receipt(repository)
    assert_safe_outcome(repository, result, receipt, "sync", kind)


@pytest.mark.parametrize("ancestor", [False, True])
@pytest.mark.parametrize("linked", [False, True])
def test_p04_output_directory_or_ancestor_redirect_preserves_all_git_metadata(
    tmp_path: Path, ancestor: bool, linked: bool
) -> None:
    repository = create_repository(tmp_path, linked)
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    destination = "artifacts" if ancestor else "artifacts/verification"
    result = invoke(
        repository,
        {
            "phase": "audit",
            "kind": "directory-alias",
            "destination": destination,
            "target": str(repository.common_git),
            "saved": "saved-output" if ancestor else "artifacts/saved-output",
        },
    )
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata, "redirected ancestor created/changed Git bytes"
    receipt = load_receipt(repository)
    assert_safe_outcome(repository, result, receipt, "audit", "directory-alias")


@pytest.mark.parametrize("entry", ["receipt", "current-log"])
@pytest.mark.parametrize("identity", ["missing-file", "unavailable-head", "dirty-start"])
@pytest.mark.parametrize("kind", ["alias", "hardlink"])
def test_p06_incomplete_or_dirty_identity_does_not_authorize_later_protected_write(
    tmp_path: Path, log_candidates: dict[str, Path], entry: str, identity: str, kind: str
) -> None:
    repository = create_repository(tmp_path, linked=True)
    if identity == "dirty-start":
        (repository.root / "candidate.txt").write_bytes(MARKER + b"dirty fixture\n")
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    destination = RECEIPT if entry == "receipt" else log_candidates["audit"]
    action: dict[str, Any] = {
        "phase": "audit",
        "kind": kind,
        "destination": str(destination),
        "target": str(repository.common_git / "config"),
    }
    if identity == "missing-file":
        action["identity_loss"] = "scripts/branchless.py"
    elif identity == "unavailable-head":
        action["identity_loss"] = str(repository.private_git / "HEAD")
    result = invoke(repository, action)
    if action_observations(repository) and identity == "missing-file":
        del before_markers["scripts/branchless.py"]
    elif action_observations(repository) and identity == "unavailable-head":
        del before_metadata[(repository.private_git / "HEAD").relative_to(repository.common_git)]
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata, "identity failure excused protected write"
    receipt = load_receipt(repository)
    assert_rejected(result, receipt)
    phases = assert_safe_outcome(repository, result, receipt, "audit", kind)
    if identity == "dirty-start" and not (repository.root / "actions.jsonl").exists():
        # Rejecting a dirty start before executing the action is a legitimate
        # alternative. The contract does not require unsafe phases to execute.
        assert receipt is not None and receipt["before"]["dirty"] is True
        assert "audit" not in phases


@pytest.mark.parametrize("entry", ["receipt", "current-log", "future-log"])
def test_p08_phase_replaced_ignored_regular_output_remains_valid(
    repository: Repository, log_candidates: dict[str, Path], entry: str
) -> None:
    destination = (
        RECEIPT
        if entry == "receipt"
        else log_candidates["types"]
        if entry == "current-log"
        else log_candidates["audit"]
    )
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    result = invoke(
        repository, {"phase": "types", "kind": "regular", "destination": str(destination)}
    )
    receipt = load_receipt(repository)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "passed"
    assert receipt["before"] == receipt["after"]
    assert assert_trace(repository, receipt) == PHASES
    assert_action(repository, "types", "regular")
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata


@pytest.mark.parametrize("entry,status", [("receipt", 0), ("current-log", 0), ("current-log", 23)])
def test_p10_local_output_failure_is_honest_and_preserves_protected_bytes(
    repository: Repository, log_candidates: dict[str, Path], entry: str, status: int
) -> None:
    destination = RECEIPT if entry == "receipt" else log_candidates["types"]
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    result = invoke(
        repository,
        {
            "phase": "types",
            "kind": "unwritable-directory",
            "destination": str(destination),
            "status": status,
        },
    )
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata
    receipt = load_receipt(repository)
    assert_safe_outcome(repository, result, receipt, "types", "unwritable-directory", status)
    if entry == "receipt":
        assert_rejected(result, receipt)


@pytest.mark.parametrize("missing", [False, True])
def test_p07_original_command_failure_or_missing_command_keeps_status_and_safe_evidence(
    repository: Repository, missing: bool
) -> None:
    before_markers, before_metadata = tracked_markers(repository), metadata(repository)
    if missing:
        (repository.bin_dir / "make").unlink()
        result = invoke(repository)
    else:
        result = invoke(
            repository,
            {"phase": "types", "kind": "regular", "destination": str(RECEIPT), "status": 23},
        )
    receipt = load_receipt(repository)
    assert result.returncode == (127 if missing else 23), result.stdout + result.stderr
    assert receipt is not None
    assert_rejected(result, receipt)
    expected = ["sync"] if missing else PHASES[: PHASES.index("types") + 1]
    assert [item["name"] for item in receipt["phases"]] == expected
    assert receipt["phases"][-1]["returncode"] == result.returncode
    if missing:
        assert not [call for call in calls(repository) if any(arg in PHASES for arg in call)]
        assert receipt["phases"][-1]["command"][0] == str(repository.bin_dir / "make")
        assert "sync" in receipt["phases"][-1]["command"]
        assert f"UV={repository.bin_dir / 'uv'}" in receipt["phases"][-1]["command"]
    else:
        assert assert_trace(repository, receipt) == expected
        assert_action(repository, "types", "regular")
    log = repository.root / receipt["phases"][-1]["log"]
    assert log.is_file() and log.stat().st_size > 0
    assert receipt["before"] == receipt["after"]
    assert tracked_markers(repository) == before_markers
    assert metadata(repository) == before_metadata
