"""Blind public MEASUREMENTS-EXPORT-01 tests for approved E1–E3 decisions."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from measurement_fixture_export import LIMIT_BYTES, MEASUREMENTS_PATH, export_measurement
from verification_fixture_tools import PHASES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent
ENV_KEYS = ("SIMRECON_MEASUREMENTS_PATH", "SIMRECON_MEASUREMENTS_RUN_ID")
DEFAULT_REPORT = object()
STALE_ID = "11111111-1111-4111-8111-111111111111"
Repository = tuple[Path, Path]


def run(args: list[str], root: Path, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, capture_output=True, text=True, check=False, **kwargs)


def git(root: Path, *args: str) -> str:
    result = run(["git", *args], root)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def report(units: str = "KiB", baseline: int = 100, peak: int = 107) -> dict[str, Any]:
    # Public arithmetic: 7 KiB = 7168 bytes; 7 native bytes = 7 bytes.
    return {
        "schema": "org.simrecon.measurements",
        "version": 1,
        "run_id": "CURRENT",
        "measurements": {
            "M25": {
                "baseline": baseline,
                "peak": peak,
                "units": units,
                "increment_bytes": (peak - baseline) * (1024 if units == "KiB" else 1),
                "limit_bytes": LIMIT_BYTES,
            }
        },
    }


@pytest.fixture
def repository(tmp_path: Path) -> Repository:
    root = tmp_path / "repo"
    root.mkdir()
    for name in ("src/simrecon/sample.py", "scripts/sample.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"if flag:\n    value = 1\n")
    (root / "scripts/branchless.py").write_bytes(b"value = 1\n")
    (root / "candidate.txt").write_bytes(b"candidate\n")
    (root / ".gitignore").write_text("artifacts/\ndist/\ncalls.jsonl\nmeasurement-calls.jsonl\n")
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "Measurements fixture")
    git(root, "add", ".")
    git(root, "commit", "-qm", "public synthetic candidate")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    shutil.copyfile(
        FIXTURES / "verification_fixture_tools.py", bin_dir / "verification_fixture_tools.py"
    )
    for name in ("make", "uv"):
        target = bin_dir / name
        target.write_text(
            f"#!{sys.executable}\n" + (FIXTURES / "measurements_fixture_commands.py").read_text()
        )
        target.chmod(0o755)
    return root, bin_dir


def invoke(
    repository: Repository,
    *,
    required: bool = True,
    mode: str = "valid",
    value: Any = DEFAULT_REPORT,
    receipt_mode: str = "complete",
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any] | None]:
    root, bin_dir = repository
    env = os.environ.copy()
    # Nested disposable callers must not inherit an enclosing canonical M25 export pair.
    for key in ENV_KEYS:
        env.pop(key, None)
    env["PATH"] = str(bin_dir) + os.pathsep + env["PATH"]
    env["EXPORT_FIXTURE_MODE"] = mode
    env["EXPORT_FIXTURE_REPORT"] = json.dumps(report() if value is DEFAULT_REPORT else value)
    env["RECEIPT_FIXTURE_MODE"] = receipt_mode
    result = run(
        [
            sys.executable,
            str(ROOT / "scripts/verify.py"),
            "--make",
            str(bin_dir / "make"),
            "--uv",
            str(bin_dir / "uv"),
            *(["--measurements-required"] if required else []),
        ],
        root,
        env=env,
    )
    path = root / "artifacts/verification/receipt.json"
    receipt = json.loads(path.read_text()) if path.is_file() else None
    return result, receipt


def observations(root: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in (root / "measurement-calls.jsonl").read_text().splitlines()
    ]


def assert_measurements(receipt: dict[str, Any], root: Path, expected: dict[str, Any]) -> None:
    destination = root / MEASUREMENTS_PATH
    payload = destination.read_bytes()
    actual = json.loads(payload)
    assert actual == {**expected, "run_id": actual["run_id"]}
    assert str(UUID(actual["run_id"])) == actual["run_id"]
    assert receipt["measurements"] == {
        **actual,
        "path": MEASUREMENTS_PATH.as_posix(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


@pytest.mark.parametrize(
    "units,baseline,peak",
    [
        ("KiB", 100, 107),
        ("bytes", 100, 107),
        ("KiB", 0, 0),
        ("bytes", 19, 19),
        ("KiB", 31, 31 + 32768),
        ("bytes", 31, 31 + 33554432),
    ],
)
def test_e1_e3_same_run_exact_report(
    repository: Repository, units: str, baseline: int, peak: int
) -> None:
    root, _ = repository
    expected = report(units, baseline, peak)
    result, receipt = invoke(repository, value=expected)
    assert result.returncode == 0, result.stdout + result.stderr
    assert receipt is not None
    assert receipt["result"] == "passed" and receipt["problems"] == []
    assert [p["name"] for p in receipt["phases"]] == PHASES
    assert all(p["returncode"] == 0 for p in receipt["phases"])
    assert receipt["before"] == receipt["after"]
    assert_measurements(receipt, root, expected)
    calls = observations(root)
    phases = [c for c in calls if any(p in c["args"] for p in PHASES)]
    assert len(phases) == len(PHASES)
    assert sum("tests" in c["args"] for c in phases) == 1
    run_id = receipt["measurements"]["run_id"]
    assert all(c["path"] == MEASUREMENTS_PATH.as_posix() for c in phases)
    assert all(c["run_id"] == run_id for c in phases)
    metadata = [c for c in calls if c not in phases]
    assert metadata
    assert all(c["path"] is None and c["run_id"] is None for c in metadata)


def test_e1_fresh_id_per_invocation(repository: Repository) -> None:
    root, _ = repository
    first, first_receipt = invoke(repository)
    assert first.returncode == 0, first.stderr
    assert first_receipt is not None
    second, second_receipt = invoke(repository)
    assert second.returncode == 0, second.stderr
    assert second_receipt is not None
    assert first_receipt["measurements"]["run_id"] != second_receipt["measurements"]["run_id"]
    assert_measurements(second_receipt, root, report())


def test_e1_legacy_collector_disabled(repository: Repository) -> None:
    root, _ = repository
    destination = root / MEASUREMENTS_PATH
    destination.parent.mkdir(parents=True)
    stale = json.dumps({**report(), "run_id": STALE_ID}).encode()
    destination.write_bytes(stale)
    result, receipt = invoke(repository, required=False)
    assert result.returncode == 0, result.stderr
    assert receipt is not None and receipt["result"] == "passed"
    assert "measurements" in receipt and receipt["measurements"] is None
    assert destination.read_bytes() == stale
    assert all(c["path"] is None and c["run_id"] is None for c in observations(root))


@pytest.mark.parametrize("mode", ["tests-failure", "tests-no-report"])
def test_e2_tests_failure_retains_only_current_valid_evidence(
    repository: Repository, mode: str
) -> None:
    root, _ = repository
    destination = root / MEASUREMENTS_PATH
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps({**report(), "run_id": STALE_ID}))
    result, receipt = invoke(repository, mode=mode)
    assert result.returncode == 37, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert [p["name"] for p in receipt["phases"]] == PHASES[:6]
    assert receipt["phases"][-1]["returncode"] == 37
    suffix = "after measurements" if mode == "tests-failure" else "without measurements"
    assert f"controlled tests failure {suffix}" in result.stdout + result.stderr
    if mode == "tests-failure":
        assert_measurements(receipt, root, report())
        assert receipt["measurements"]["run_id"] != STALE_ID
    else:
        assert receipt["measurements"] is None


def test_e2_before_tests_failure_never_reports_stale(repository: Repository) -> None:
    root, _ = repository
    destination = root / MEASUREMENTS_PATH
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps({**report(), "run_id": STALE_ID}))
    result, receipt = invoke(repository, receipt_mode="command-failure")
    assert result.returncode == 23, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert [p["name"] for p in receipt["phases"]] == PHASES[:3]
    assert receipt["measurements"] is None
    assert "controlled failure diagnostic" in result.stdout + result.stderr


def invalid_reports() -> list[Any]:
    values: list[Any] = [None, [], "object required", 17, True]
    for field, invalid in (
        ("schema", "wrong"),
        ("schema", None),
        ("version", 2),
        ("version", True),
        ("version", 1.0),
        ("run_id", STALE_ID),
        ("run_id", ""),
        ("run_id", 1),
        ("run_id", None),
        ("measurements", []),
        ("measurements", None),
        ("measurements", {}),
        ("measurements", {"M25": []}),
        ("measurements", {"M25": None}),
    ):
        value = report()
        value[field] = invalid
        values.append(value)
    extra = report()
    extra["measurements"]["M26"] = dict(extra["measurements"]["M25"])
    values.append(extra)
    for field in ("schema", "version", "run_id", "measurements"):
        value = report()
        del value[field]
        values.append(value)
    for field in ("baseline", "peak", "units", "increment_bytes", "limit_bytes"):
        value = report()
        del value["measurements"]["M25"][field]
        values.append(value)
    for field in ("baseline", "peak", "increment_bytes", "limit_bytes"):
        original = report()["measurements"]["M25"][field]
        for invalid in (True, float(original), str(original), None, -1):
            value = report()
            value["measurements"]["M25"][field] = invalid
            values.append(value)
    for unit in ("KB", "kib", "Bytes", "MiB", "", None, 1, True):
        value = report()
        value["measurements"]["M25"]["units"] = unit
        values.append(value)
    lower_peak = report()
    lower_peak["measurements"]["M25"].update(baseline=108, peak=107, increment_bytes=0)
    values.append(lower_peak)
    for units, wrong_increment in (("KiB", 7), ("bytes", 7168)):
        value = report(units)
        value["measurements"]["M25"]["increment_bytes"] = wrong_increment
        values.append(value)
    for invalid_limit in (0, LIMIT_BYTES - 1, LIMIT_BYTES + 1):
        value = report()
        value["measurements"]["M25"]["limit_bytes"] = invalid_limit
        values.append(value)
    values += [report("bytes", 0, LIMIT_BYTES + 1), report("KiB", 0, 32769)]
    return values


@pytest.mark.parametrize("value", invalid_reports())
def test_e2_e3_invalid_report_rejected_for_measurements(repository: Repository, value: Any) -> None:
    result, receipt = invoke(repository, value=value)
    assert result.returncode == 1, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert receipt["measurements"] is None
    assert any("measurement" in p.lower() for p in receipt["problems"]), receipt["problems"]
    # Otherwise-complete independent coverage/wheel evidence isolates intended rejection.
    assert [p["name"] for p in receipt["phases"]] == PHASES
    assert all(p["returncode"] == 0 for p in receipt["phases"])
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    assert receipt["artifact"]["version"] == "1.2.0"
    assert receipt["before"] == receipt["after"]


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "malformed",
        "invalid-utf8",
        "duplicate-top",
        "duplicate-record",
        "duplicate-id",
        "changed-id",
        "unavailable",
        "late-report",
    ],
)
def test_e2_missing_malformed_changed_or_late_evidence(repository: Repository, mode: str) -> None:
    root, _ = repository
    if mode == "missing":
        destination = root / MEASUREMENTS_PATH
        destination.parent.mkdir(parents=True)
        destination.write_text(json.dumps({**report(), "run_id": STALE_ID}))
    result, receipt = invoke(repository, mode=mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert receipt["measurements"] is None
    assert any("measurement" in p.lower() for p in receipt["problems"]), receipt["problems"]
    assert all(p["returncode"] == 0 for p in receipt["phases"])


@pytest.mark.parametrize("mode", ["changed-report-same-id", "reformatted-report-same-id"])
def test_e3_later_valid_report_replacement_preserving_run_id_rejected(
    repository: Repository, mode: str
) -> None:
    root, _ = repository
    result, receipt = invoke(repository, mode=mode)
    assert result.returncode == 1, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert any("measurement" in p.lower() for p in receipt["problems"]), receipt["problems"]
    assert [p["name"] for p in receipt["phases"]] == PHASES
    assert all(p["returncode"] == 0 for p in receipt["phases"])
    assert receipt["before"] is not None and receipt["before"]["dirty"] is False
    assert receipt["before"] == receipt["after"]
    assert receipt["coverage"]["global"] == {
        "statements": {"covered": 5, "total": 5},
        "branches": {"covered": 4, "total": 4},
    }
    wheel = root / "dist/simrecon-1.2.0-py3-none-any.whl"
    assert receipt["artifact"] == {
        "path": wheel.relative_to(root).as_posix(),
        "size_bytes": wheel.stat().st_size,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "version": "1.2.0",
    }

    calls = observations(root)
    phases = [c for c in calls if any(p in c["args"] for p in PHASES)]
    assert len(phases) == len(PHASES)
    tests_calls = [c for c in phases if "tests" in c["args"]]
    assert len(tests_calls) == 1
    run_id = tests_calls[0]["run_id"]
    assert str(UUID(run_id)) == run_id
    assert all(c["run_id"] == run_id for c in phases)
    assert all(c["path"] == MEASUREMENTS_PATH.as_posix() for c in phases)

    destination = root / MEASUREMENTS_PATH
    tests_bytes = destination.with_name("tests-phase-measurements.json").read_bytes()
    original = {**report(), "run_id": run_id}
    assert tests_bytes == json.dumps(original).encode()
    final_expected = copy.deepcopy(original)
    if mode == "changed-report-same-id":
        # Independent valid alternative: (211 - 200) KiB * 1024 = 11264 bytes.
        final_expected["measurements"]["M25"] = {
            "baseline": 200,
            "peak": 211,
            "units": "KiB",
            "increment_bytes": 11264,
            "limit_bytes": 33554432,
        }
    final_bytes = destination.read_bytes()
    assert final_bytes == (json.dumps(final_expected, indent=2, sort_keys=True) + "\n").encode()
    assert json.loads(final_bytes) == final_expected
    assert hashlib.sha256(tests_bytes).digest() != hashlib.sha256(final_bytes).digest()
    # Unavailable evidence may be null; any retained diagnostic must match final bytes.
    if receipt["measurements"] is not None:
        assert_measurements(receipt, root, final_expected)


def protected_setup(root: Path, kind: str) -> tuple[Path, bytes]:
    destination = root / MEASUREMENTS_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kind == "tracked":
        destination.write_bytes(b"tracked measurements sentinel\n")
        git(root, "add", "-f", str(MEASUREMENTS_PATH))
        git(root, "commit", "-qm", "tracked destination fixture")
        protected = destination
    else:
        protected = root / ("candidate.txt" if kind == "leaf-tracked" else ".git/config")
        destination.symlink_to(protected)
    return protected, protected.read_bytes()


@pytest.mark.parametrize("kind", ["tracked", "leaf-tracked", "leaf-git"])
@pytest.mark.parametrize("identity_available", [False, True])
def test_e2_helper_protects_destination_before_phases(
    repository: Repository, kind: str, identity_available: bool
) -> None:
    root, _ = repository
    protected, original = protected_setup(root, kind)
    (root / "scripts/branchless.py").unlink()
    if not identity_available:
        (root / ".git/HEAD").unlink()
    result, _ = invoke(repository)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "unrecognized arguments" not in result.stdout + result.stderr
    assert protected.read_bytes() == original
    calls = observations(root) if (root / "measurement-calls.jsonl").exists() else []
    assert not any(any(phase in c["args"] for phase in PHASES) for c in calls)
    assert "measurement" in (result.stdout + result.stderr).lower()


@pytest.fixture
def writer_environment(
    repository: Repository, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, pytest.MonkeyPatch]:
    root, _ = repository
    monkeypatch.chdir(root)
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    return root, monkeypatch


def enable_writer(
    monkeypatch: pytest.MonkeyPatch, destination: str = str(MEASUREMENTS_PATH)
) -> None:
    monkeypatch.setenv(ENV_KEYS[0], destination)
    monkeypatch.setenv(ENV_KEYS[1], STALE_ID)


def native_record() -> dict[str, Any]:
    return {k: v for k, v in report()["measurements"]["M25"].items() if k != "limit_bytes"}


def test_e1_writer_standalone_no_report(
    writer_environment: tuple[Path, pytest.MonkeyPatch],
) -> None:
    root, _ = writer_environment
    export_measurement(native_record())
    assert not (root / "artifacts").exists()


@pytest.mark.parametrize("key", ENV_KEYS)
@pytest.mark.parametrize("value", ["present", ""])
def test_e2_writer_partial_pair_rejected(
    writer_environment: tuple[Path, pytest.MonkeyPatch], key: str, value: str
) -> None:
    root, monkeypatch = writer_environment
    monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="both path and run ID"):
        export_measurement(native_record())
    assert not (root / "artifacts").exists()


def test_e1_writer_exact_same_call_record(
    writer_environment: tuple[Path, pytest.MonkeyPatch],
) -> None:
    root, monkeypatch = writer_environment
    enable_writer(monkeypatch)
    supplied = native_record()
    before = copy.deepcopy(supplied)
    export_measurement(supplied)
    assert supplied == before
    assert json.loads((root / MEASUREMENTS_PATH).read_text()) == {**report(), "run_id": STALE_ID}
    assert git(root, "status", "--porcelain") == ""


@pytest.mark.parametrize("ignored", [False, True])
def test_e2_writer_requires_ignored_approved_path_before_write(
    writer_environment: tuple[Path, pytest.MonkeyPatch], ignored: bool
) -> None:
    root, monkeypatch = writer_environment
    if ignored:
        enable_writer(monkeypatch, "artifacts/verification/other.json")
        expected = "approved artifact path"
    else:
        (root / ".gitignore").write_text("dist/\ncalls.jsonl\nmeasurement-calls.jsonl\n")
        enable_writer(monkeypatch)
        expected = "ignored by Git"
    with pytest.raises(ValueError, match=expected):
        export_measurement(native_record())
    assert not (root / "artifacts").exists()


@pytest.mark.parametrize("kind", ["tracked", "leaf-tracked", "leaf-git"])
def test_e2_writer_preserves_protected_bytes(
    writer_environment: tuple[Path, pytest.MonkeyPatch], kind: str
) -> None:
    root, monkeypatch = writer_environment
    protected, original = protected_setup(root, kind)
    enable_writer(monkeypatch)
    with pytest.raises(ValueError, match="ignored|tracked|Git metadata"):
        export_measurement(native_record())
    assert protected.read_bytes() == original


@pytest.mark.parametrize("caller_failure", ["none", "status", "limit", "units"])
def test_e1_m25_exports_single_invocation_after_assertions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caller_failure: str
) -> None:
    # Call the real existing test with controlled native stdout; never run native M25 here.
    import test_mrc_conversion

    calls: list[list[str]] = []
    exports: list[dict[str, Any]] = []
    measurement = native_record()
    measurement["units"] = "bytes" if sys.platform == "darwin" else "KiB"
    measurement["increment_bytes"] = 7 if sys.platform == "darwin" else 7168
    if caller_failure == "limit":
        measurement["increment_bytes"] = LIMIT_BYTES + 1
    elif caller_failure == "units":
        measurement["units"] = "wrong"

    def controlled_run(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        assert kwargs == {"capture_output": True, "text": True, "check": False}
        return subprocess.CompletedProcess(
            args, 7 if caller_failure == "status" else 0, json.dumps(measurement), ""
        )

    monkeypatch.setattr(test_mrc_conversion.subprocess, "run", controlled_run)
    monkeypatch.setattr(test_mrc_conversion, "export_measurement", exports.append)
    if caller_failure != "none":
        with pytest.raises(AssertionError):
            test_mrc_conversion.test_m25_native_memory(None, tmp_path)
        assert exports == []
    else:
        measurement["units"] = "bytes" if sys.platform == "darwin" else "KiB"
        measurement["increment_bytes"] = 7 if sys.platform == "darwin" else 7168
        test_mrc_conversion.test_m25_native_memory(None, tmp_path)
        assert exports == [measurement]
    assert len(calls) == 1
    assert calls[0] == [sys.executable, str(FIXTURES / "mrc_fixture_memory.py"), str(tmp_path)]


def test_e2_failed_tests_discard_current_invalid_measurements(repository: Repository) -> None:
    invalid = report()
    invalid["measurements"]["M25"]["increment_bytes"] = 7
    result, receipt = invoke(repository, mode="tests-failure", value=invalid)
    assert result.returncode == 37, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert receipt["measurements"] is None
    assert [p["name"] for p in receipt["phases"]] == PHASES[:6]
    assert receipt["phases"][-1]["returncode"] == 37
    assert any("measurement" in p.lower() for p in receipt["problems"])


def test_e2_later_phase_failure_retains_valid_measurements(repository: Repository) -> None:
    root, _ = repository
    result, receipt = invoke(repository, receipt_mode="wheel-build-failure")
    assert result.returncode == 31, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert [p["name"] for p in receipt["phases"]] == PHASES[:11]
    assert receipt["phases"][-1]["returncode"] == 31
    assert_measurements(receipt, root, report())


@pytest.mark.parametrize("protected_area", ["private", "common"])
@pytest.mark.parametrize("writer", [False, True])
def test_e2_linked_worktree_metadata_protected(
    repository: Repository,
    monkeypatch: pytest.MonkeyPatch,
    protected_area: str,
    writer: bool,
) -> None:
    root, bin_dir = repository
    linked = root.parent / "linked"
    git(root, "worktree", "add", "-q", "--detach", str(linked), "HEAD")
    private = Path(git(linked, "rev-parse", "--absolute-git-dir"))
    protected = private / "HEAD" if protected_area == "private" else root / ".git/config"
    original = protected.read_bytes()
    destination = linked / MEASUREMENTS_PATH
    destination.parent.mkdir(parents=True)
    destination.symlink_to(protected)
    if writer:
        monkeypatch.chdir(linked)
        enable_writer(monkeypatch)
        with pytest.raises(ValueError, match="Git metadata"):
            export_measurement(native_record())
    else:
        result, _ = invoke((linked, bin_dir))
        assert result.returncode == 1, result.stdout + result.stderr
        calls_path = linked / "measurement-calls.jsonl"
        calls = observations(linked) if calls_path.exists() else []
        assert not any(any(phase in c["args"] for phase in PHASES) for c in calls)
    assert protected.read_bytes() == original


@pytest.mark.parametrize("writer", [False, True])
def test_e2_ancestor_symlink_cannot_write_git_metadata(
    repository: Repository, monkeypatch: pytest.MonkeyPatch, writer: bool
) -> None:
    root, _ = repository
    metadata = {
        p.relative_to(root / ".git"): p.read_bytes()
        for p in (root / ".git").rglob("*")
        if p.is_file()
    }
    (root / "artifacts").mkdir()
    (root / "artifacts/verification").symlink_to(root / ".git", target_is_directory=True)
    if writer:
        monkeypatch.chdir(root)
        enable_writer(monkeypatch)
        with pytest.raises(ValueError, match="ignored|Git metadata"):
            export_measurement(native_record())
    else:
        result, _ = invoke(repository)
        assert result.returncode == 1, result.stdout + result.stderr
        calls = observations(root) if (root / "measurement-calls.jsonl").exists() else []
        assert not any(any(phase in c["args"] for phase in PHASES) for c in calls)
    after = {
        p.relative_to(root / ".git"): p.read_bytes()
        for p in (root / ".git").rglob("*")
        if p.is_file()
    }
    assert after == metadata


@pytest.mark.parametrize("protected_area", ["tracked", "git", "private", "common"])
def test_e2_successful_earlier_phase_redirect_rejected_before_tests(
    repository: Repository, monkeypatch: pytest.MonkeyPatch, protected_area: str
) -> None:
    root, bin_dir = repository
    original_root = root
    if protected_area in {"private", "common"}:
        root = original_root.parent / "redirect-linked"
        git(original_root, "worktree", "add", "-q", "--detach", str(root), "HEAD")
        private = Path(git(root, "rev-parse", "--absolute-git-dir"))
        protected = (
            private / "HEAD" if protected_area == "private" else original_root / ".git/config"
        )
    else:
        protected = root / ("candidate.txt" if protected_area == "tracked" else ".git/config")
    original = protected.read_bytes()
    candidate_bytes = (root / "candidate.txt").read_bytes()
    monkeypatch.setenv("EXPORT_FIXTURE_REDIRECT_TARGET", str(protected))
    result, receipt = invoke((root, bin_dir), mode="redirect-before-tests")

    # Check preservation first even if verification later fails for another reason.
    assert protected.read_bytes() == original
    assert (root / "candidate.txt").read_bytes() == candidate_bytes
    destination = root / MEASUREMENTS_PATH
    assert destination.is_symlink() and destination.resolve() == protected.resolve()
    calls = observations(root)
    phases = [c for c in calls if any(p in c["args"] for p in PHASES)]
    assert [next(p for p in PHASES if p in c["args"]) for c in phases] == PHASES[:5]
    assert not any("tests" in c["args"] for c in calls)
    assert all(c["path"] == MEASUREMENTS_PATH.as_posix() for c in phases)
    run_id = phases[0]["run_id"]
    assert str(UUID(run_id)) == run_id
    assert all(c["run_id"] == run_id for c in phases)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "controlled successful types phase redirected measurement destination" in (
        result.stdout + result.stderr
    )
    assert receipt is not None and receipt["result"] == "failed"
    assert [p["name"] for p in receipt["phases"]] == PHASES[:5]
    assert all(p["returncode"] == 0 for p in receipt["phases"])
    assert receipt["measurements"] is None
    assert any("measurement" in p.lower() for p in receipt["problems"]), receipt["problems"]
    assert receipt["before"] is not None and receipt["before"]["dirty"] is False
    assert receipt["before"] == receipt["after"]
    assert receipt["coverage"] is None and receipt["artifact"] is None


def test_e2_no_report_without_stale_seed(repository: Repository) -> None:
    result, receipt = invoke(repository, mode="missing")
    assert result.returncode == 1, result.stdout + result.stderr
    assert receipt is not None and receipt["result"] == "failed"
    assert receipt["measurements"] is None
    assert [p["name"] for p in receipt["phases"]] == PHASES
    assert all(p["returncode"] == 0 for p in receipt["phases"])
    assert any("measurement" in p.lower() for p in receipt["problems"])
