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
import tempfile
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
NATIVE_ARCS = {
    "src/simrecon/sample.py": [(-1, 1), (1, 2), (1, -1), (2, -1)],
    "scripts/sample.py": [(-1, 1), (1, 2), (1, -1), (2, -1)],
    "scripts/branchless.py": [(-1, 1), (1, -1)],
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
    native = os.environ.get('EVIDENCE_NATIVE') == '1'
    if native and phase in ('tests', 'coverage-combine', 'coverage-json', 'coverage-html'):
        # Genuine public native APIs over independently declared synthetic arcs.
        # No scientific test, product import, actual build or canonical gate.
        from coverage import Coverage, CoverageData
        token = os.environ['EVIDENCE_TOKEN']
        arcs = json.loads(os.environ['EVIDENCE_ARCS'])
        data_file = root / os.environ['EVIDENCE_DATA_FILE']
        data_file.parent.mkdir(parents=True, exist_ok=True)
        shard_dir = root / 'artifacts/native-shards'
        shard_dir.mkdir(parents=True, exist_ok=True)
        cov = Coverage(data_file=str(data_file), config_file=False, branch=True)
        cov.set_option('run:relative_files', True)
        event = {'token': token, 'phase': phase, 'operation': None, 'members': {},
                 'database': None, 'shards': {}, 'status': status}
        if phase == 'tests':
            shard = CoverageData(basename=str(shard_dir / data_file.name), suffix=token)
            shard.add_arcs({name: [tuple(arc) for arc in values] for name, values in arcs.items()})
            shard.write()
            event['operation'] = 'CoverageData.add_arcs/write'
            event['shards'][str(Path(shard.data_filename()).relative_to(root))] = {
                'sha256': hashlib.sha256(Path(shard.data_filename()).read_bytes()).hexdigest(),
                'exists': True,
            }
            # Authentic but unused stale data is not the retained current DB.
            stale = CoverageData(basename=str(root / '.coverage.unused'))
            stale.add_arcs({'unused.py': [(-1, 1), (1, -1)]})
            stale.write()
        elif phase == 'coverage-combine':
            inputs = list(shard_dir.iterdir())
            event['shards'] = {str(path.relative_to(root)): {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            } for path in inputs if path.is_file()}
            cov.combine(data_paths=[str(shard_dir)], strict=True, keep=False)
            cov.save()
            for name in event['shards']:
                event['shards'][name]['exists'] = (root / name).exists()
            event['operation'] = 'Coverage.combine/save'
        else:
            cov.load()
            if phase == 'coverage-json':
                cov.json_report(outfile='artifacts/coverage/coverage.json')
                event['operation'] = 'Coverage.json_report'
            else:
                import shutil
                report = root / 'artifacts/coverage/html'
                # Discover only this actual emission, never stale directory members.
                shutil.rmtree(report, ignore_errors=True)
                cov.html_report(directory=str(report), title=f'Public fixture {token}')
                event['operation'] = 'Coverage.html_report'
                event['members'] = {
                    str(path.relative_to(root)): base64.b64encode(path.read_bytes()).decode('ascii')
                    for path in report.rglob('*') if path.is_file()
                }
        if phase != 'tests':
            current = Path(cov.get_data().data_filename())
            event['database'] = str(current.relative_to(root))
            event['database_payload'] = base64.b64encode(current.read_bytes()).decode('ascii')
        with (root / 'native-emissions.jsonl').open('a') as stream:
            stream.write(json.dumps(event) + '\n')
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
    if action.get('selector'):
        lines = (root / 'native-emissions.jsonl').read_text().splitlines()
        events = [json.loads(line) for line in lines]
        current = next(item for item in reversed(events) if item['phase'] == 'coverage-html')
        members = sorted(current['members'])
        action['target'] = (current['database'] if action['selector'] == 'database'
                            else members[action['member_index']])
        action['generation_token'] = current['token']
        action['discovered_members'] = members
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
if phase == 'audit' and os.environ.get('EVIDENCE_AUDIT_FAILURE') == '1':
    status = 37
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
    native_emissions: list[dict[str, Any]]
    native_anchors: tuple[str, ...]


def prepare_evidence_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repository:
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "0")
    repository = create_repository(tmp_path)
    root, bin_dir = repository.root, repository.bin_dir
    ignore = root / ".gitignore"
    ignore.write_text(
        ignore.read_text()
        + "measurement-calls.jsonl\nevidence-calls.jsonl\nnative-emissions.jsonl\n.coverage*\n"
    )
    git(root, "add", ".gitignore")
    git(root, "commit", "-qm", "ignore disposable observation ledgers")
    for name in ("verification_fixture_tools.py", "measurements_fixture_commands.py"):
        shutil.copyfile(ROOT / "tests" / name, bin_dir / name)
    for name in ("make", "uv"):
        executable = bin_dir / name
        executable.write_text(f"#!{sys.executable}\n" + COMMAND_FIXTURE)
        executable.chmod(0o755)
    return repository


@pytest.fixture
def evidence_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repository:
    return prepare_evidence_repository(tmp_path, monkeypatch)


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
    native: bool = False,
    data_file: str = ".coverage",
    audit_failure: bool = False,
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
        EVIDENCE_NATIVE=str(int(native)),
        EVIDENCE_ARCS=json.dumps(NATIVE_ARCS),
        EVIDENCE_DATA_FILE=data_file,
        EVIDENCE_AUDIT_FAILURE=str(int(audit_failure)),
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
    emissions_path = root / "native-emissions.jsonl"
    emissions = (
        [json.loads(line) for line in emissions_path.read_text().splitlines()]
        if emissions_path.exists()
        else []
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for directory in (root / "artifacts", root / "dist")
        for path in directory.rglob("*")
        if path.is_file()
    }
    # Current DB discovery comes from public data_filename at actual emission.
    # Include requested/stale root outputs without treating them as current data.
    extra_names = {receipt_path, ".coverage.unused"}
    extra_names.update(event["database"] for event in emissions if event["database"])
    for name in extra_names:
        path = root / name
        if path.is_file():
            files[name] = path.read_bytes()
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
        emissions,
        tuple(sha256(json.dumps(event, sort_keys=True).encode()) for event in emissions),
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
    evidence = os.environ.get("A05_EVIDENCE")
    if evidence:
        # Public sanitized hashes only: no generated HTML/source bytes exported.
        record = {
            "test": os.environ.get("PYTEST_CURRENT_TEST"),
            "command": command,
            "status": result.returncode,
            "started": started.isoformat(),
            "finished": finished.isoformat(),
            "timed_out": False,
            "receipt_path": receipt_path,
            "mode": mode,
            "native": native,
            "token": token,
            "action_requested": action,
            "calls": [
                {
                    **call,
                    "snapshots": {
                        name: {
                            "sha256": sha256(base64.b64decode(value)),
                            "size_bytes": len(base64.b64decode(value)),
                        }
                        for name, value in call["snapshots"].items()
                    },
                }
                for call in calls
            ],
            "emissions": [
                {
                    **{
                        key: value
                        for key, value in event.items()
                        if key not in {"members", "database_payload"}
                    },
                    "members": {
                        name: {
                            "sha256": sha256(base64.b64decode(value)),
                            "size_bytes": len(base64.b64decode(value)),
                        }
                        for name, value in event["members"].items()
                    },
                    "database_sha256": sha256(base64.b64decode(event["database_payload"]))
                    if event.get("database_payload")
                    else None,
                }
                for event in emissions
            ],
            "receipt": receipt,
            "files": {
                name: {"sha256": sha256(payload), "size_bytes": len(payload)}
                for name, payload in files.items()
            },
            "identity": before,
            "metadata_unchanged": True,
            "identity_unchanged": True,
        }
        with Path(evidence).open("a") as stream:
            stream.write(json.dumps(record) + "\n")
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
        expected_branches = [[1, 2], [1, -1]] if branches else []
        assert item["executed_branches"] == (
            sorted(expected_branches) if observed.native_emissions else expected_branches
        )
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
    if observed.native_emissions:
        assert_native_evidence(observed)
    else:
        assert observed.files[COVERAGE_HTML] == b"<html>controlled coverage</html>"


def assert_native_container(payload: bytes, expected_arcs: dict[str, Any]) -> None:
    """Read the entire authentic container through its public native API."""
    from coverage import CoverageData

    with tempfile.TemporaryDirectory(prefix="a05-native-observer-") as directory:
        path = Path(directory) / "observed.data"
        path.write_bytes(payload)
        data = CoverageData(basename=str(path))
        data.read()
        assert data.has_arcs(), "native branch instrumentation unavailable"
        assert data.measured_files() == set(expected_arcs), "native owned-file membership changed"
        assert data.measured_contexts() == {""}, "unexpected native context"
        for name, arcs in expected_arcs.items():
            assert sorted(data.arcs(name) or []) == sorted(arcs), "synthetic native arcs changed"


def assert_native_evidence(observed: Observation) -> None:
    """Complete actual emission, bound to genuine phases of this invocation.

    Arcs/counts/M25 and source content are synthetic. Public report/container
    APIs are genuine. This does not measure production or rerun native export.
    """
    events = observed.native_emissions
    assert tuple(sha256(json.dumps(event, sort_keys=True).encode()) for event in events) == (
        observed.native_anchors
    ), "native emission anchor changed"
    assert [event["phase"] for event in events] == [
        "tests",
        "coverage-combine",
        "coverage-json",
        "coverage-html",
    ], "incomplete native generation"
    calls = {call["phase"]: call for call in phase_calls(observed)}
    for event in events:
        assert event["token"] == observed.token, "stale native generation"
        assert event["status"] == calls[event["phase"]]["status"] == 0
    assert [event["operation"] for event in events] == [
        "CoverageData.add_arcs/write",
        "Coverage.combine/save",
        "Coverage.json_report",
        "Coverage.html_report",
    ]
    shard, combined, _, html = events
    assert shard["shards"] and set(shard["shards"]) == set(combined["shards"])
    for name, before in shard["shards"].items():
        assert before["exists"] is True
        assert combined["shards"][name] == {"sha256": before["sha256"], "exists": False}
    database = html["database"]
    assert database and all(event["database"] == database for event in events[1:])
    expected = base64.b64decode(html["database_payload"])
    assert_native_container(expected, NATIVE_ARCS)
    final = observed.files.get(database)
    assert final is not None and sha256(final) == sha256(expected), (
        "current native database replaced"
    )
    assert final == expected, "complete native container changed"
    assert_native_container(final, NATIVE_ARCS)
    members = {name: base64.b64decode(value) for name, value in html["members"].items()}
    assert COVERAGE_HTML in members and len(members) > 1, "no complete public HTML emission"
    assert observed.token.encode() in members[COVERAGE_HTML], "HTML index from another invocation"
    assert members[COVERAGE_HTML] == generated_bytes(observed)[COVERAGE_HTML]
    for name, payload in members.items():
        assert observed.files.get(name) == payload, f"current HTML member replaced: {name}"
        assert sha256(observed.files[name]) == sha256(payload)
    # A path class alone is no membership/currentness proof. Bind link targets
    # to actual generation, and never require every historical file to survive.
    for call in phase_calls(observed):
        action = call["action"]
        if action and action.get("selector"):
            assert action["generation_token"] == observed.token
            assert action["discovered_members"] == sorted(members)
            target = (
                database
                if action["selector"] == "database"
                else sorted(members)[action["member_index"]]
            )
            assert action["target"] == target
            assert action["before"] == sha256(expected if target == database else members[target])


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
            action = call["action"]
            if action.get("selector"):
                html = next(
                    event
                    for event in observed.native_emissions
                    if event["phase"] == "coverage-html"
                )
                members = sorted(html["members"])
                assert action["generation_token"] == html["token"] == observed.token
                assert action["discovered_members"] == members
                target = (
                    html["database"]
                    if action["selector"] == "database"
                    else members[action["member_index"]]
                )
                assert action["target"] == target
                payload = base64.b64decode(
                    html["database_payload"]
                    if target == html["database"]
                    else html["members"][target]
                )
                assert action["before"] == sha256(payload)
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
    # A genuine late command failure does not authorize own persistence to
    # destroy the complete native evidence already emitted by this invocation.
    # Honest early rejection can have no HTML emission and needs no such proof.
    if observed.native_emissions and observed.native_emissions[-1]["phase"] == "coverage-html":
        assert_native_evidence(observed)
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
    for stamp in (begin, end):
        offset = stamp.utcoffset()
        assert offset is not None and offset.total_seconds() == 0
    assert observed.started <= begin <= end <= observed.finished
    assert [item["name"] for item in receipt["phases"]] == names
    assert [item["command"] for item in receipt["phases"]] == [call["argv"] for call in calls], (
        "invented phase argv"
    )
    assert [item["returncode"] for item in receipt["phases"]] == [
        call["status"] for call in calls
    ], "invented phase status"
    for item, call in zip(receipt["phases"], calls, strict=True):
        phase_begin, phase_end = (
            datetime.fromisoformat(item[key]) for key in ("started_at", "finished_at")
        )
        for stamp in (phase_begin, phase_end):
            offset = stamp.utcoffset()
            assert offset is not None and offset.total_seconds() == 0
        assert begin <= phase_begin <= phase_end <= end, "phase timestamps outside current receipt"
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
        "receipt-non-utc",
        "phase-non-utc",
        "phase-time-outside-receipt",
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
    elif defect == "receipt-non-utc":
        receipt["started_at"] = (
            datetime.fromisoformat(receipt["started_at"]).isoformat().replace("+00:00", "+01:00")
        )
    elif defect == "phase-non-utc":
        phase = receipt["phases"][0]
        phase["started_at"] = (
            datetime.fromisoformat(phase["started_at"]).isoformat().replace("+00:00", "+01:00")
        )
    elif defect == "phase-time-outside-receipt":
        receipt["phases"][0]["started_at"] = observed.finished.isoformat()
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


def test_p11_receipt_at_current_native_database(evidence_repository: Repository) -> None:
    # The name is fixture configuration, not a required production backend/name.
    assert_outcome(invoke(evidence_repository, ".coverage", native=True))


@pytest.mark.parametrize("entry", ["receipt", "current-log-example"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_p11_phase_link_at_current_native_database(
    evidence_repository: Repository, entry: str, kind: str
) -> None:
    action = {
        "phase": "audit",
        "destination": DEFAULT_RECEIPT if entry == "receipt" else LOG_EXAMPLES[1],
        "selector": "database",
        "kind": kind,
    }
    assert_outcome(invoke(evidence_repository, action=action, native=True))


@pytest.mark.parametrize("entry", ["receipt", "current-log-example"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_p11_phase_link_sweeps_actual_current_html_members(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str, kind: str
) -> None:
    # Each target is selected from THAT invocation's public HTML emission.
    # The first safe emission only starts a finite member sweep; no filename,
    # private source map, fixed member count or cross-run leaf recurrence binds.
    safe = prepare_evidence_repository(tmp_path / "discovery", monkeypatch)
    baseline = invoke(safe, native=True)
    assert baseline.status == 0, baseline.stdout + baseline.stderr
    assert_outcome(baseline)
    members = baseline.native_emissions[-1]["members"]
    index = 0
    failures = []
    while index < len(members):
        repository = prepare_evidence_repository(tmp_path / f"member-{index}", monkeypatch)
        action = {
            "phase": "audit",
            "destination": DEFAULT_RECEIPT if entry == "receipt" else LOG_EXAMPLES[1],
            "selector": "html-member",
            "member_index": index,
            "kind": kind,
        }
        observed = invoke(repository, action=action, native=True)
        try:
            assert_outcome(observed)
        except AssertionError as error:
            failures.append({"member_index": index, "failure": str(error)})
        # Initial honest rejection may have no emission or phase link. Do not
        # invent report members or claim that a challenged log was actually used.
        html = [event for event in observed.native_emissions if event["phase"] == "coverage-html"]
        if html:
            members = html[-1]["members"]
        index += 1
    assert not failures, f"current HTML member preservation failures: {failures}"


@pytest.mark.parametrize(
    "destination,data_file",
    [
        (DEFAULT_RECEIPT, ".coverage"),
        (".coverage.receipt.json", ".coverage"),
        (".coverage.unused", ".coverage"),
        ("artifacts/coverage/html/custom-receipt.json", ".coverage"),
        ("artifacts/native/custom-receipt.json", "artifacts/native/custom.data"),
    ],
)
def test_p08_native_safe_neighbors_unused_stale_and_alternate_layout(
    evidence_repository: Repository, destination: str, data_file: str
) -> None:
    observed = invoke(evidence_repository, destination, native=True, data_file=data_file)
    assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)
    # Public combine consumed its inputs. They are not final retained current DBs.
    for name in observed.native_emissions[1]["shards"]:
        assert name not in observed.files


@pytest.mark.parametrize("entry", ["ordinary", "receipt-database", "log-database"])
def test_p07_native_current_evidence_keeps_genuine_failure_status_and_stop(
    evidence_repository: Repository, entry: str
) -> None:
    action = (
        {
            "phase": "audit",
            "destination": LOG_EXAMPLES[1],
            "selector": "database",
            "kind": "hardlink",
        }
        if entry == "log-database"
        else None
    )
    receipt_path = ".coverage" if entry == "receipt-database" else DEFAULT_RECEIPT
    observed = invoke(
        evidence_repository, receipt_path, action=action, native=True, audit_failure=True
    )
    assert_outcome(observed)
    if entry == "ordinary":
        assert observed.status == 37
        assert_native_evidence(observed)


@pytest.fixture
def native_success(evidence_repository: Repository) -> Observation:
    observed = invoke(evidence_repository, native=True)
    assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("alternative", ["unused-stale", "safe-replacement", "unused-log-layout"])
def test_local_native_observer_allows_legitimate_alternatives(
    native_success: Observation, alternative: str
) -> None:
    observed = copy.deepcopy(native_success)
    assert observed.receipt is not None
    if alternative == "unused-stale":
        observed.files[".coverage.unused"] = b"unused old artifact may be replaced"
        observed.files["artifacts/coverage/html/unrelated-unused.txt"] = b"not emitted by this run"
    elif alternative == "safe-replacement":
        # Equal independently emitted bytes are valid after a safe replacement.
        html = observed.native_emissions[-1]
        for name in [html["database"], *html["members"]]:
            observed.files[name] = bytes(bytearray(observed.files[name]))
    else:
        phase = observed.receipt["phases"][-1]
        original = phase["log"]
        phase["log"] = "artifacts/verification/unused-layout/current-audit.log"
        observed.files[phase["log"]] = observed.files[original]
        observed.files[original] = b"unused prior layout example"
    assert_outcome(observed)


@pytest.mark.parametrize(
    "defect",
    [
        "database-replaced",
        "database-self-consistent-wrong-arcs",
        "database-missing",
        "database-stale-generation",
        "html-member-replaced",
        "html-member-missing",
        "html-self-consistent-substitution",
        "html-membership-shrink",
        "html-stale-generation",
        "native-operation",
        "native-status",
        "consumed-shard-current",
    ],
)
def test_local_native_observer_rejects_forged_stale_or_incomplete_evidence(
    native_success: Observation, defect: str
) -> None:
    observed = copy.deepcopy(native_success)
    html = observed.native_emissions[-1]
    database = html["database"]
    members = html["members"]
    auxiliary = next(name for name in sorted(members) if name != COVERAGE_HTML)
    if defect == "database-replaced":
        observed.files[database] = b'{"schema":"org.simrecon.verification"}'
    elif defect == "database-self-consistent-wrong-arcs":
        from coverage import CoverageData

        with tempfile.TemporaryDirectory(prefix="a05-wrong-arcs-") as directory:
            path = Path(directory) / "wrong.data"
            data = CoverageData(basename=str(path))
            data.add_arcs({name: [(-1, 1), (1, -1)] for name in NATIVE_ARCS})
            data.write()
            wrong = path.read_bytes()
        observed.files[database] = wrong
        # Even a self-consistent authentic container cannot supply independent arcs.
        for event in observed.native_emissions[1:]:
            event["database_payload"] = base64.b64encode(wrong).decode()
        observed.native_anchors = tuple(
            sha256(json.dumps(event, sort_keys=True).encode())
            for event in observed.native_emissions
        )
    elif defect == "database-missing":
        del observed.files[database]
    elif defect in {"database-stale-generation", "html-stale-generation"}:
        event = observed.native_emissions[1] if defect.startswith("database") else html
        event["token"] = "11111111-1111-4111-8111-111111111111"
        observed.native_anchors = tuple(
            sha256(json.dumps(event, sort_keys=True).encode())
            for event in observed.native_emissions
        )
    elif defect == "html-member-replaced":
        observed.files[auxiliary] = b"receipt replaced actual emitted member"
    elif defect == "html-member-missing":
        del observed.files[auxiliary]
    elif defect == "html-self-consistent-substitution":
        wrong = b"self-consistent stale/substituted HTML " + observed.token.encode()
        for name in members:
            observed.files[name] = wrong
        for call in phase_calls(observed):
            if call["phase"] == "coverage-html":
                call["snapshots"][COVERAGE_HTML] = base64.b64encode(wrong).decode()
        # Independent genuine emission anchors remain; matching index/call bytes
        # and a current token alone do not establish complete actual HTML output.
    elif defect == "html-membership-shrink":
        del members[auxiliary]
        del observed.files[auxiliary]
    elif defect == "native-operation":
        html["operation"] = "fabricated public emission"
    elif defect == "native-status":
        html["status"] = 23
    else:
        html["database"] = next(iter(observed.native_emissions[0]["shards"]))
    with pytest.raises((AssertionError, ValueError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("defect", ["database-replaced", "html-member-replaced"])
def test_local_native_failure_observer_rejects_replaced_current_evidence(
    evidence_repository: Repository, defect: str
) -> None:
    observed = invoke(evidence_repository, native=True, audit_failure=True)
    assert observed.status == 37
    assert_outcome(observed)
    html = observed.native_emissions[-1]
    target = (
        html["database"]
        if defect == "database-replaced"
        else next(name for name in sorted(html["members"]) if name != COVERAGE_HTML)
    )
    observed.files[target] = b"own persistence replaced current native evidence on failure"
    with pytest.raises(AssertionError):
        assert_outcome(observed)
