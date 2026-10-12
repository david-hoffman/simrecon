"""Supplemental blind public proof of P11 own-evidence output collisions."""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest

from test_verification_output_protection import (
    ROOT,
    Repository,
    create_repository,
    git,
    metadata,
)
from verification_fixture_tools import PHASES

MEASUREMENT = "artifacts/verification/measurements.json"
COVERAGE_JSON = "artifacts/coverage/coverage.json"
COVERAGE_HTML = "artifacts/coverage/html/index.html"
WHEEL = "dist/simrecon-1.2.0-py3-none-any.whl"
DEFAULT_RECEIPT = "artifacts/verification/receipt.json"
# Only measurement and coverage report paths are prescribed by the contracts.
# Wheel name is chosen by the public fixture. Log leaves are layout examples.
LOG_EXAMPLES = ("artifacts/verification/logs/sync.log", "artifacts/verification/logs/audit.log")
REPORTS = (MEASUREMENT, COVERAGE_JSON, COVERAGE_HTML, WHEEL)
M25 = {
    "baseline": 100,
    "peak": 107,
    "units": "KiB",
    "increment_bytes": 7168,  # (107 - 100) KiB * 1024 B/KiB
    "limit_bytes": 33554432,
}

# These controlled Make executables supply external phase I/O, never the
# verifier's output decision. Observe actual argv/status and independently save
# emitted bytes before verifier persistence. No runtime is imported here.
COMMAND_FIXTURE = r"""
import base64
import contextlib
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from measurements_fixture_commands import main
from verification_fixture_tools import PHASES

root = Path.cwd()
args = sys.argv[1:]
phase = next((arg for arg in args if arg in PHASES), None)
stdout, stderr = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    status = main()
    if phase is not None:
        print(f"{os.environ['EVIDENCE_TOKEN']} stdout {phase}")
        print(f"{os.environ['EVIDENCE_TOKEN']} stderr {phase}", file=sys.stderr)
snapshots = {}
generated = {
    'tests': 'artifacts/verification/measurements.json',
    'coverage-json': 'artifacts/coverage/coverage.json',
    'coverage-html': 'artifacts/coverage/html/index.html',
    'wheel': 'dist/simrecon-1.2.0-py3-none-any.whl',
}
if phase in generated:
    name = generated[phase]
    path = root / name
    if path.is_file():
        payload = path.read_bytes()
        snapshots[name] = base64.b64encode(payload).decode('ascii')
action = json.loads(os.environ.get('EVIDENCE_ACTION', '{}'))
action_observation = None
if phase == action.get('phase'):
    destination, target = root / action['destination'], root / action['target']
    before = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    # A log example may be unused. Never invent its output or require its use.
    applied = target.is_file() or action['kind'] == 'symlink'
    if applied:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.unlink(missing_ok=True)
        if action['kind'] == 'symlink':
            destination.symlink_to(target)
        else:
            destination.hardlink_to(target)
    after = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    action_observation = {
        **action, 'applied': applied, 'before': before, 'after': after,
        'shares_inode': destination.samefile(target) if applied and target.is_file() else None,
    }
observation = {
    'argv': [sys.argv[0], *args], 'phase': phase, 'status': status,
    'stdout': stdout.getvalue(), 'stderr': stderr.getvalue(),
    'measurement_path': os.environ.get('SIMRECON_MEASUREMENTS_PATH'),
    'run_id': os.environ.get('SIMRECON_MEASUREMENTS_RUN_ID'),
    'snapshots': snapshots, 'action': action_observation,
}
with (root / 'evidence-calls.jsonl').open('a') as stream:
    stream.write(json.dumps(observation) + '\n')
print(stdout.getvalue(), end='')
print(stderr.getvalue(), end='', file=sys.stderr)
sys.exit(status)
"""


@dataclass
class Observation:
    """Actual invocation evidence; byte snapshots are collected before assertions."""

    command: list[str]
    status: int
    stdout: str
    stderr: str
    receipt: dict[str, Any] | None
    calls: list[dict[str, Any]]
    files: dict[str, bytes]
    identity: dict[str, Any]
    started: datetime
    finished: datetime
    token: str
    bin_dir: str
    action: dict[str, Any]


@pytest.fixture
def evidence_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repository:
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    repository = create_repository(tmp_path)
    root, bin_dir = repository.root, repository.bin_dir
    ignore = root / ".gitignore"
    ignore.write_text(ignore.read_text() + "measurement-calls.jsonl\nevidence-calls.jsonl\n")
    git(root, "add", ".gitignore")
    git(root, "commit", "-qm", "ignore disposable observation ledgers")
    for name in ("verification_fixture_tools.py", "measurements_fixture_commands.py"):
        shutil.copyfile(ROOT / "tests" / name, bin_dir / name)
    for name in ("make", "uv"):
        executable = bin_dir / name
        executable.write_text(f"#!{sys.executable}\n" + COMMAND_FIXTURE)
        executable.chmod(0o755)
    return repository


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def identity(repository: Repository) -> dict[str, Any]:
    root = repository.root
    return {
        "commit": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "dirty": False,
        "untracked": [],
        # Hash opaque Makefile bytes; do not display or interpret their contents.
        "manifest": {
            name: sha256((root / name).read_bytes()) for name in git(root, "ls-files").splitlines()
        },
    }


def invoke(
    repository: Repository,
    receipt_path: str = DEFAULT_RECEIPT,
    *,
    action: dict[str, Any] | None = None,
    mode: str = "valid",
) -> Observation:
    root, bin_dir = repository.root, repository.bin_dir
    before = identity(repository)
    metadata_before = metadata(repository)
    env = os.environ.copy()
    for key in ("SIMRECON_MEASUREMENTS_PATH", "SIMRECON_MEASUREMENTS_RUN_ID"):
        env.pop(key, None)
    token = str(uuid4())
    env.update(
        PATH=str(bin_dir) + os.pathsep + env["PATH"],
        EXPORT_FIXTURE_MODE=mode,
        EXPORT_FIXTURE_REPORT=json.dumps(
            {
                "schema": "org.simrecon.measurements",
                "version": 1,
                "run_id": "CURRENT",
                "measurements": {"M25": M25},
            }
        ),
        RECEIPT_FIXTURE_MODE="complete",
        EVIDENCE_TOKEN=token,
        EVIDENCE_ACTION=json.dumps(action or {}),
    )
    command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "scripts/source_free_check.py"),
        "--timeout",
        "300",
        "python",
        str(ROOT / "scripts/verify.py"),
        "--make",
        str(bin_dir / "make"),
        "--uv",
        str(bin_dir / "uv"),
        "--measurements-required",
        "--receipt",
        receipt_path,
    ]
    started = datetime.now(UTC)
    result = subprocess.run(
        command, cwd=root, env=env, capture_output=True, text=True, check=False, timeout=300
    )
    finished = datetime.now(UTC)
    calls_path = root / "evidence-calls.jsonl"
    calls = (
        [json.loads(line) for line in calls_path.read_text().splitlines()]
        if calls_path.exists()
        else []
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for directory in (root / "artifacts", root / "dist")
        for path in directory.rglob("*")
        if path.is_file()
    }
    # A rejected collision can leave a report, rather than a receipt, at the
    # requested name. It is not parsed as current verification evidence.
    receipt = None
    if receipt_path in files:
        try:
            candidate = json.loads(files[receipt_path])
        except (ValueError, UnicodeError):
            candidate = None
        if isinstance(candidate, dict) and candidate.get("schema") == "org.simrecon.verification":
            receipt = candidate
    observed = Observation(
        command,
        result.returncode,
        result.stdout,
        result.stderr,
        receipt,
        calls,
        files,
        before,
        started,
        finished,
        token,
        str(bin_dir),
        action or {},
    )
    evidence = os.environ.get("A04_EVIDENCE")
    if evidence:
        matches = (
            [
                item["name"]
                for item in receipt["phases"]
                if item["log"]
                in {receipt_path, (action or {}).get("destination"), (action or {}).get("target")}
            ]
            if receipt
            else None
        )
        record = {
            "command": command,
            "status": result.returncode,
            "started": started.isoformat(),
            "finished": finished.isoformat(),
            "receipt_path": receipt_path,
            "action": action,
            "mode": mode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "calls": calls,
            "receipt": receipt,
            "identity": before,
            "files": {name: base64.b64encode(payload).decode() for name, payload in files.items()},
            "same_invocation_log_matches": matches,
            "metadata_unchanged": metadata(repository) == metadata_before,
            "identity_unchanged": identity(repository) == before,
        }
        with Path(evidence).open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    assert metadata(repository) == metadata_before, "verifier changed Git metadata"
    assert identity(repository) == before, "verifier changed the tracked candidate"
    return observed


def phase_calls(observed: Observation) -> list[dict[str, Any]]:
    return [call for call in observed.calls if call["phase"] is not None]


def generated_bytes(observed: Observation) -> dict[str, bytes]:
    return {
        name: base64.b64decode(encoded)
        for call in phase_calls(observed)
        for name, encoded in call["snapshots"].items()
    }


def assert_measurement(observed: Observation, receipt: dict[str, Any]) -> None:
    value = receipt["measurements"]
    payload = observed.files[value["path"]]
    actual = json.loads(payload)
    calls = phase_calls(observed)
    tests = [call for call in calls if call["phase"] == "tests"]
    assert len(tests) == 1, "no single tests-phase measurement provenance"
    run_id = tests[0]["run_id"]
    assert str(UUID(run_id)) == run_id
    expected = {
        "schema": "org.simrecon.measurements",
        "version": 1,
        "run_id": run_id,
        "measurements": {"M25": M25},
    }
    assert actual == expected, "emitted measurement schema/payload changed"
    assert actual["version"] is not True
    assert value == {**expected, "path": MEASUREMENT, "sha256": sha256(payload)}, (
        "measurement digest/path does not describe final bytes"
    )
    assert payload == generated_bytes(observed)[MEASUREMENT], "tests-phase report replaced"
    assert all(
        call["measurement_path"] == MEASUREMENT and call["run_id"] == run_id for call in calls
    )


def assert_coverage(observed: Observation, receipt: dict[str, Any]) -> None:
    coverage = receipt["coverage"]
    assert coverage["reports"] == {"json": COVERAGE_JSON, "html": COVERAGE_HTML}
    generated = generated_bytes(observed)
    for name in (COVERAGE_JSON, COVERAGE_HTML):
        assert observed.files[name] == generated[name], f"emitted {name} was replaced"
    native = json.loads(observed.files[COVERAGE_JSON])
    assert native["meta"]["branch_coverage"] is True
    expected_files = {}
    for name, lines, branches in (
        ("src/simrecon/sample.py", 2, 2),
        ("scripts/sample.py", 2, 2),
        ("scripts/branchless.py", 1, 0),
    ):
        item = native["files"][name]
        assert item["executed_lines"] == list(range(1, lines + 1))
        assert item["missing_lines"] == item["missing_branches"] == item["excluded_lines"] == []
        assert item["executed_branches"] == ([[1, 2], [1, -1]] if branches else [])
        for key, count in (
            ("covered_lines", lines),
            ("num_statements", lines),
            ("covered_branches", branches),
            ("num_branches", branches),
            ("missing_lines", 0),
            ("missing_branches", 0),
            ("excluded_lines", 0),
        ):
            assert type(item["summary"][key]) is int and item["summary"][key] == count
        expected_files[name] = {
            "statements": {"covered": lines, "total": lines},
            "branches": {"covered": branches, "total": branches},
        }
    assert set(native["files"]) == set(expected_files)
    assert coverage["files"] == expected_files
    assert coverage["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    assert coverage["packages"] == {
        "simrecon": expected_files["src/simrecon/sample.py"],
        "scripts": {
            "statements": {"covered": 3, "total": 3},
            "branches": {"covered": 2, "total": 2},
        },
    }
    assert observed.files[COVERAGE_HTML] == b"<html>controlled coverage</html>"


def assert_wheel(observed: Observation, receipt: dict[str, Any]) -> None:
    payload = observed.files[receipt["artifact"]["path"]]
    assert payload == generated_bytes(observed)[WHEEL], "emitted wheel replaced"
    assert receipt["artifact"] == {
        "path": WHEEL,
        "size_bytes": len(payload),
        "sha256": sha256(payload),
        "version": "1.2.0",
    }
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = "simrecon-1.2.0.dist-info"
        assert (
            archive.read(f"{info}/METADATA")
            == b"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.0\n"
        )
        assert b"Wheel-Version: 1.0\n" in archive.read(f"{info}/WHEEL")
        assert b"Tag: py3-none-any\n" in archive.read(f"{info}/WHEEL")
        rows = list(csv.reader(archive.read(f"{info}/RECORD").decode().splitlines()))
        assert len(rows) == len(archive.namelist())
        assert {row[0] for row in rows} == set(archive.namelist())
        for name, fingerprint, size in rows:
            if name == f"{info}/RECORD":
                assert (fingerprint, size) == ("", "")
            else:
                data = archive.read(name)
                digest = (
                    base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
                )
                assert fingerprint == "sha256=" + digest
                assert int(size) == len(data)


def assert_outcome(observed: Observation) -> None:
    """Permit honest early rejection and layouts that safely avoid a log example."""
    calls = phase_calls(observed)
    names = [call["phase"] for call in calls]
    assert names == PHASES[: len(names)], "phase omission, reorder or retry"
    for call in calls:
        assert call["argv"][0] == observed.bin_dir + "/make"
        assert f"UV={observed.bin_dir}/uv" in call["argv"]
        assert call["stdout"] in observed.stdout + observed.stderr, "phase stdout not forwarded"
        assert call["stderr"] in observed.stdout + observed.stderr, "phase stderr not forwarded"
        if call["action"] is not None:
            assert call["action"]["before"] == call["action"]["after"], "phase itself wrote target"
            if call["action"]["applied"] and call["action"]["before"] is not None:
                assert call["action"]["shares_inode"] is True
    for index, call in enumerate(calls):
        if call["status"]:
            assert index == len(calls) - 1, "continued after real phase failure"
            assert observed.status == call["status"], "original phase status swallowed"
    receipt = observed.receipt
    if observed.status == 0:
        assert receipt is not None and receipt["result"] == "passed"
        assert names == PHASES and all(call["status"] == 0 for call in calls)
        assert receipt["problems"] == []
    else:
        assert observed.status == (calls[-1]["status"] if calls and calls[-1]["status"] else 1)
        assert (observed.stdout + observed.stderr).strip(), "silent rejection"
        if receipt is not None:
            assert receipt["result"] == "failed" and receipt["problems"]
    if receipt is None:
        return
    assert (
        receipt["schema"] == "org.simrecon.verification"
        and type(receipt["version"]) is int
        and receipt["version"] == 1
    )
    assert receipt["context"] == {
        "contract": None,
        "reviewed_tests": None,
        "integration_base": None,
    }
    assert receipt["inputs"] == {}
    assert receipt["before"] == receipt["after"] == observed.identity
    begin, end = (datetime.fromisoformat(receipt[key]) for key in ("started_at", "finished_at"))
    assert observed.started <= begin <= end <= observed.finished
    assert [item["name"] for item in receipt["phases"]] == names
    assert [item["command"] for item in receipt["phases"]] == [call["argv"] for call in calls], (
        "invented phase argv"
    )
    assert [item["returncode"] for item in receipt["phases"]] == [
        call["status"] for call in calls
    ], "invented phase status"
    for item, call in zip(receipt["phases"], calls, strict=True):
        path = Path(item["log"])
        assert not path.is_absolute() and ".." not in path.parts
        # Failed persistence can leave an unavailable log. A current receipt
        # written at a reported log path cannot silently replace emitted output,
        # including when the original phase failure status is kept.
        if observed.status == 0 or item["log"] == observed.command[-1]:
            log = observed.files[item["log"]].decode()
            assert call["stdout"] in log and call["stderr"] in log, (
                "current emitted phase output was replaced"
            )
    if receipt.get("measurements") is not None:
        assert_measurement(observed, receipt)
    if receipt.get("artifact") is not None:
        assert_wheel(observed, receipt)
    if observed.status == 0:
        assert receipt["measurements"] is not None
        assert_coverage(observed, receipt)
        assert receipt["artifact"] is not None


@pytest.mark.parametrize("destination", [*REPORTS, *LOG_EXAMPLES])
def test_p11_receipt_destination_keeps_same_run_evidence(
    evidence_repository: Repository, destination: str
) -> None:
    assert_outcome(invoke(evidence_repository, destination))


@pytest.mark.parametrize("target", [*REPORTS, LOG_EXAMPLES[0]])
@pytest.mark.parametrize("entry", ["receipt", "current-log-example"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_p11_phase_link_cannot_falsify_emitted_evidence(
    evidence_repository: Repository, target: str, entry: str, kind: str
) -> None:
    action = {
        "phase": "audit",
        "destination": DEFAULT_RECEIPT if entry == "receipt" else LOG_EXAMPLES[1],
        "target": target,
        "kind": kind,
    }
    assert_outcome(invoke(evidence_repository, action=action))


@pytest.mark.parametrize(
    "destination,mode", [(MEASUREMENT, "tests-failure"), (LOG_EXAMPLES[0], "tests-failure")]
)
def test_p07_p11_collision_keeps_actual_failure_and_stop(
    evidence_repository: Repository, destination: str, mode: str
) -> None:
    assert_outcome(invoke(evidence_repository, destination, mode=mode))


@pytest.mark.parametrize(
    "destination",
    [
        DEFAULT_RECEIPT,
        "artifacts/verification/logs/custom-receipt.json",
        "artifacts/coverage/custom-receipt.json",
        "dist/custom-receipt.json",
    ],
)
def test_p08_p11_safe_custom_destination_preserves_all_evidence(
    evidence_repository: Repository, destination: str
) -> None:
    observed = invoke(evidence_repository, destination)
    assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)


def test_p07_honest_early_rejection_needs_no_unavailable_phase_evidence(
    evidence_repository: Repository,
) -> None:
    observed = invoke(evidence_repository, "candidate.txt")
    assert observed.status == 1
    assert phase_calls(observed) == []
    assert_outcome(observed)


@pytest.fixture
def observed_success(evidence_repository: Repository) -> Observation:
    observed = invoke(evidence_repository)
    assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("alternative", ["unused-example", "safe-replacement"])
def test_local_observer_allows_safe_layout_alternatives(
    observed_success: Observation, alternative: str
) -> None:
    observed = copy.deepcopy(observed_success)
    assert observed.receipt is not None
    phase = observed.receipt["phases"][-1]
    original = phase["log"]
    payload = observed.files[original]
    if alternative == "unused-example":
        phase["log"] = "artifacts/verification/another-run/audit.log"
        observed.files[phase["log"]] = payload
        observed.files[original] = b"unrelated unused layout example\n"
    # Safe replacement may retain the reported pathname. The observer requires
    # real current output at that pathname, never traversal of a former alias.
    assert_outcome(observed)


@pytest.mark.parametrize(
    "defect",
    [
        "measurement-schema",
        "measurement-digest",
        "coverage-json",
        "coverage-html",
        "wheel-digest",
        "log-replaced",
        "stale-output",
        "retry",
        "argv",
        "phase-status",
        "incomplete-success",
        "identity",
    ],
)
def test_local_observer_rejects_false_evidence(observed_success: Observation, defect: str) -> None:
    observed = copy.deepcopy(observed_success)
    assert observed.receipt is not None
    receipt = observed.receipt
    if defect == "measurement-schema":
        observed.files[MEASUREMENT] = b'{"schema": "org.simrecon.verification"}'
    elif defect == "measurement-digest":
        receipt["measurements"]["sha256"] = "0" * 64
    elif defect in {"coverage-json", "coverage-html"}:
        observed.files[COVERAGE_JSON if defect == "coverage-json" else COVERAGE_HTML] = (
            b"receipt replaced native report"
        )
    elif defect == "wheel-digest":
        receipt["artifact"]["sha256"] = "0" * 64
    elif defect in {"log-replaced", "stale-output"}:
        phase = receipt["phases"][0]
        observed.files[phase["log"]] = (
            b"old invocation stdout/stderr"
            if defect == "stale-output"
            else b'{"schema":"org.simrecon.verification"}'
        )
    elif defect == "retry":
        observed.calls.append(copy.deepcopy(phase_calls(observed)[-1]))
    elif defect == "argv":
        receipt["phases"][0]["command"] = ["invented-make", "sync"]
    elif defect == "phase-status":
        receipt["phases"][0]["returncode"] = 23
    elif defect == "incomplete-success":
        observed.calls = [call for call in observed.calls if call["phase"] not in PHASES[5:]]
    elif defect == "identity":
        receipt["after"]["commit"] = "0" * 40
    with pytest.raises((AssertionError, ValueError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("defect", ["swallowed-status", "continued-after-failure"])
def test_local_failure_observer_rejects_false_status_or_continuation(
    evidence_repository: Repository, defect: str
) -> None:
    observed = invoke(evidence_repository, mode="tests-failure")
    assert observed.status == 37
    assert_outcome(observed)
    if defect == "swallowed-status":
        observed.status = 1
    else:
        next_call = copy.deepcopy(phase_calls(observed)[-1])
        next_call["phase"] = "coverage-combine"
        next_call["status"] = 0
        observed.calls.append(next_call)
    with pytest.raises(AssertionError):
        assert_outcome(observed)
