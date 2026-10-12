"""Supplemental blind public proof of P11 own-evidence output collisions."""

from __future__ import annotations

import base64
import copy
import csv
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib.metadata import version
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
from importlib.metadata import version
from pathlib import Path
from measurements_fixture_commands import main
from verification_fixture_tools import PHASES

root = Path.cwd()
args = sys.argv[1:]
phase = next((arg for arg in args if arg in PHASES), None)
# Observe already persisted output before the next external command. Discovery
# uses actual current streams, including directory aliases, not log leaf names.
previous = root / 'evidence-calls.jsonl'
prior_calls = ([json.loads(line) for line in previous.read_text().splitlines()]
               if previous.exists() else [])
retained_logs = {}
visited = set()
for directory, dirs, names in os.walk(root / 'artifacts', followlinks=True):
    resolved = str(Path(directory).resolve())
    if resolved in visited:
        dirs[:] = []
        continue
    visited.add(resolved)
    for name in sorted(names):
        path = Path(directory) / name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for call in prior_calls:
            if (call['phase'] and call['stdout'].encode() in payload
                    and call['stderr'].encode() in payload):
                retained_logs.setdefault(call['phase'], {
                    'path': str(path.relative_to(root)),
                    'payload': base64.b64encode(payload).decode('ascii'),
                })
stdout, stderr = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    queried_tool = next((name for name in ('ruff', 'pyright', 'coverage', 'pytest')
                         if name in args), None)
    if Path(sys.argv[0]).name == 'uv' and queried_tool and args[-1:] == ['--version']:
        # Truthful controlled metadata, from this executable's actual environment.
        print(f'{queried_tool} {version(queried_tool)}')
        status = 0
    else:
        status = main()
    if phase == os.environ.get('EVIDENCE_FAILURE_PHASE'):
        status = 37
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
if phase is not None and phase == action.get('phase'):
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
        if action['kind'] == 'directory-alias':
            destination.symlink_to(target.parent, target_is_directory=True)
        elif action['kind'] == 'symlink':
            destination.symlink_to(target)
        else:
            destination.hardlink_to(target)
    after = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
    action_observation = {
        **action, 'applied': applied, 'before': before, 'after': after,
        'shares_inode': ((destination / target.name if action['kind'] == 'directory-alias'
                          else destination).samefile(target)
                         if applied and target.is_file() else None),
    }
if phase == 'audit' and os.environ.get('EVIDENCE_AUDIT_FAILURE') == '1':
    status = 37
blocked_log = None
if phase == 'audit' and os.environ.get('EVIDENCE_BLOCK_LOG'):
    blocked_log = os.environ['EVIDENCE_BLOCK_LOG']
    path = root / blocked_log
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()
observation = {
    'argv': [sys.argv[0], *args], 'phase': phase, 'status': status,
    'stdout': stdout.getvalue(), 'stderr': stderr.getvalue(),
    'measurement_path': os.environ.get('SIMRECON_MEASUREMENTS_PATH'),
    'run_id': os.environ.get('SIMRECON_MEASUREMENTS_RUN_ID'),
    'snapshots': snapshots, 'action': action_observation,
    'retained_logs': retained_logs, 'blocked_log': blocked_log,
    'wheel_members': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in (root / 'dist').glob('*.whl')}
                     if phase == 'wheel' else {},
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
    report_anchors: tuple[str, ...]
    expected_environment: dict[str, Any]
    retained_logs: dict[str, dict[str, str]]
    blocked_logs: tuple[str, ...]
    coverage_profile: str


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
    failure_phase: str | None = None,
    receipt_mode: str = "complete",
    block_log: str = "",
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
        RECEIPT_FIXTURE_MODE=receipt_mode,
        EVIDENCE_TOKEN=token,
        EVIDENCE_ACTION=json.dumps(action or {}),
        EVIDENCE_NATIVE=str(int(native)),
        EVIDENCE_ARCS=json.dumps(NATIVE_ARCS),
        EVIDENCE_DATA_FILE=data_file,
        EVIDENCE_AUDIT_FAILURE=str(int(audit_failure)),
        EVIDENCE_FAILURE_PHASE=failure_phase or "",
        EVIDENCE_BLOCK_LOG=block_log,
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
    if receipt is not None:
        # Path.rglob does not traverse directory symlinks. Observe the actual
        # reported current log paths, including ignored external aliases;
        # never infer log membership from a directory/layout example.
        for item in receipt["phases"]:
            name = item["log"]
            path = root / name
            if path.is_file():
                files[name] = path.read_bytes()
    retained_logs = {}
    for call in calls:
        for phase, anchor in call["retained_logs"].items():
            retained_logs.setdefault(phase, anchor)
            path = root / anchor["path"]
            if path.is_file():
                files[anchor["path"]] = path.read_bytes()
    for call in calls:
        if call["phase"] is not None:
            for name, payload in files.items():
                if call["stdout"].encode() in payload and call["stderr"].encode() in payload:
                    retained_logs.setdefault(
                        call["phase"],
                        {"path": name, "payload": base64.b64encode(payload).decode()},
                    )
    blocked_logs = tuple(
        call["blocked_log"]
        for call in calls
        if call["blocked_log"] and (root / call["blocked_log"]).is_dir()
    )
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
        report_anchors(calls),
        {
            "platform": platform.platform(),
            "python_executable": str(Path(sys.executable).resolve()),
            "python_version": sys.version.split()[0],
            "make_version": "fixture tool 1.0",
            "uv_version": "fixture tool 1.0",
            "git_executable": str(Path(shutil.which("git", path=env["PATH"]) or "").resolve()),
            "git_version": git(root, "--version"),
            "tools": {name: version(name) for name in ("ruff", "pyright", "coverage", "pytest")},
        },
        retained_logs,
        blocked_logs,
        "complete" if native else receipt_mode,
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
            "failure_phase": failure_phase,
            "receipt_mode": receipt_mode,
            "token": token,
            "report_anchors": list(observed.report_anchors),
            "native_anchors": list(observed.native_anchors),
            "expected_environment": observed.expected_environment,
            "wheel_emissions": [
                {
                    "phase": call["phase"],
                    "container_sha256": sha256(base64.b64decode(call["snapshots"][WHEEL])),
                    **wheel_observation(base64.b64decode(call["snapshots"][WHEEL])),
                }
                for call in calls
                if WHEEL in call["snapshots"]
            ],
            "retained_logs": {
                phase: {
                    "path": anchor["path"],
                    "sha256": sha256(base64.b64decode(anchor["payload"])),
                    "size_bytes": len(base64.b64decode(anchor["payload"])),
                }
                for phase, anchor in retained_logs.items()
            },
            "blocked_logs": list(blocked_logs),
            "action_requested": action,
            "calls": [
                {
                    **call,
                    "retained_logs": {
                        phase: {
                            "path": anchor["path"],
                            "sha256": sha256(base64.b64decode(anchor["payload"])),
                            "size_bytes": len(base64.b64decode(anchor["payload"])),
                        }
                        for phase, anchor in call["retained_logs"].items()
                    },
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
            "native_database_reported_log_phases": [
                item["name"]
                for item in receipt["phases"]
                if any(
                    event["database"]
                    and (root / item["log"]).resolve() == (root / event["database"]).resolve()
                    for event in emissions
                )
            ]
            if receipt
            else None,
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


def report_anchors(calls: list[dict[str, Any]]) -> tuple[str, ...]:
    """Anchor actual pre-persistence snapshots independently of receipt inclusion."""
    return tuple(
        sha256(
            json.dumps(
                {
                    "phase": call["phase"],
                    "run_id": call["run_id"],
                    "snapshots": call["snapshots"],
                    "wheel_members": call["wheel_members"],
                },
                sort_keys=True,
            ).encode()
        )
        for call in calls
        if call["phase"] is not None and call["snapshots"]
    )


def generated_bytes(observed: Observation) -> dict[str, bytes]:
    return {
        name: base64.b64decode(encoded)
        for call in phase_calls(observed)
        for name, encoded in call["snapshots"].items()
    }


def expected_measurement(observed: Observation) -> dict[str, Any] | None:
    tests = [call for call in phase_calls(observed) if call["phase"] == "tests"]
    if not tests or MEASUREMENT not in generated_bytes(observed):
        return None
    assert len(tests) == 1, "no single tests-phase measurement provenance"
    run_id = tests[0]["run_id"]
    assert str(UUID(run_id)) == run_id
    expected = {
        "schema": "org.simrecon.measurements",
        "version": 1,
        "run_id": run_id,
        "measurements": {"M25": M25},
    }
    try:
        actual = json.loads(generated_bytes(observed)[MEASUREMENT], object_pairs_hook=unique_keys)
    except (ValueError, UnicodeError):
        return None
    if actual != expected or type(actual["version"]) is not int:
        return None
    return expected


def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate evidence key")
        result[key] = value
    return result


def valid_emitted_reports(observed: Observation) -> dict[str, bytes]:
    """Independent fixture validity; invalid/unavailable emission is no diagnostic."""
    valid = {}
    for name, payload in generated_bytes(observed).items():
        try:
            if name == MEASUREMENT:
                assert expected_measurement(observed) is not None
            elif name == COVERAGE_JSON:
                coverage_expectation(observed, payload)
            elif name == COVERAGE_HTML:
                if observed.native_emissions:
                    html = observed.native_emissions[-1]
                    assert html["phase"] == "coverage-html"
                    assert payload == base64.b64decode(html["members"][name])
                    assert observed.token.encode() in payload
                else:
                    assert payload == b"<html>controlled coverage</html>"
            elif name == WHEEL:
                assert_wheel_container(payload)
            else:
                raise AssertionError("unrecognized fixture emission")
        except (AssertionError, ValueError, KeyError, TypeError, UnicodeError, zipfile.BadZipFile):
            continue
        valid[name] = payload
    return valid


def assert_emitted_reports(observed: Observation) -> None:
    """Own writes preserve actual valid current emission, even without a receipt.

    Synthetic fixture snapshots prove preservation, not production measurement.
    Invalid M25 emission is unavailable diagnostic evidence, never valid success.
    """
    assert report_anchors(observed.calls) == observed.report_anchors, (
        "report emission anchor changed"
    )
    for name, payload in valid_emitted_reports(observed).items():
        assert observed.files.get(name) == payload, (
            f"current emitted evidence lost/replaced: {name}"
        )


def assert_measurement(observed: Observation, receipt: dict[str, Any]) -> None:
    value = receipt["measurements"]
    payload = observed.files[value["path"]]
    actual = json.loads(payload)
    calls = phase_calls(observed)
    tests = [call for call in calls if call["phase"] == "tests"]
    assert len(tests) == 1, "no single tests-phase measurement provenance"
    run_id = tests[0]["run_id"]
    assert str(UUID(run_id)) == run_id
    expected = expected_measurement(observed)
    assert expected is not None, "no valid current emitted measurements"
    assert actual == expected, "emitted measurement schema/payload changed"
    assert actual["version"] is not True
    assert value == {**expected, "path": MEASUREMENT, "sha256": sha256(payload)}, (
        "measurement digest/path does not describe final bytes"
    )
    assert payload == generated_bytes(observed)[MEASUREMENT], "tests-phase report replaced"
    assert all(
        call["measurement_path"] == MEASUREMENT and call["run_id"] == run_id for call in calls
    )


def coverage_expectation(observed: Observation, payload: bytes) -> dict[str, Any]:
    """Exact independent inputs, including approved partial/zero native profiles."""
    native = json.loads(payload, object_pairs_hook=unique_keys)
    assert native["meta"]["branch_coverage"] is True
    profile = observed.coverage_profile
    line_counts, branch_counts = {
        "partial-coverage": ((2, 2, 1), (1, 1, 0)),
        "partial-json-failure": ((2, 2, 1), (1, 1, 0)),
        "partial-statements": ((2, 2, 0), (2, 2, 0)),
        "partial-combined": ((1, 1, 1), (1, 1, 0)),
        "zero-coverage": ((0, 0, 0), (0, 0, 0)),
    }.get(profile, ((2, 2, 1), (2, 2, 0)))
    expected_files = {}
    counter_keys = (
        "covered_lines",
        "num_statements",
        "missing_lines",
        "excluded_lines",
        "covered_branches",
        "num_branches",
        "missing_branches",
        "num_partial_branches",
    )
    for index, (name, lines, branches) in enumerate(
        (
            ("src/simrecon/sample.py", 2, 2),
            ("scripts/sample.py", 2, 2),
            ("scripts/branchless.py", 1, 0),
        )
    ):
        item = native["files"][name]
        covered_lines, covered_branches = line_counts[index], branch_counts[index]
        assert item["executed_lines"] == list(range(1, covered_lines + 1))
        assert item["missing_lines"] == list(range(covered_lines + 1, lines + 1))
        assert item["excluded_lines"] == []
        destinations = [[1, 2], [1, -1]] if branches else []
        if profile == "partial-combined" and branches:
            destinations.reverse()
        executed, missing = destinations[:covered_branches], destinations[covered_branches:]
        assert sorted(item["executed_branches"]) == sorted(executed)
        assert sorted(item["missing_branches"]) == sorted(missing)
        partial = len({arc[0] for arc in missing} & set(item["executed_lines"]))
        for key, count in (
            ("covered_lines", covered_lines),
            ("num_statements", lines),
            ("covered_branches", covered_branches),
            ("num_branches", branches),
            ("missing_lines", lines - covered_lines),
            ("missing_branches", branches - covered_branches),
            ("excluded_lines", 0),
            ("num_partial_branches", partial),
        ):
            assert type(item["summary"][key]) is int and item["summary"][key] == count
        expected_files[name] = {
            "statements": {"covered": covered_lines, "total": lines},
            "branches": {"covered": covered_branches, "total": branches},
        }
    assert set(native["files"]) == set(expected_files)
    for key in counter_keys:
        assert type(native["totals"][key]) is int
        assert native["totals"][key] == sum(
            item["summary"][key] for item in native["files"].values()
        )
    return expected_files


def assert_coverage(observed: Observation, receipt: dict[str, Any]) -> None:
    coverage = receipt["coverage"]
    assert coverage["reports"] == {"json": COVERAGE_JSON, "html": COVERAGE_HTML}
    generated = generated_bytes(observed)
    assert COVERAGE_JSON in generated, "no current coverage JSON emission"
    for name in (COVERAGE_JSON, COVERAGE_HTML):
        if name in generated:
            assert observed.files[name] == generated[name], f"emitted {name} was replaced"
    expected_files = coverage_expectation(observed, observed.files[COVERAGE_JSON])
    assert coverage["files"] == expected_files

    def aggregate(names: list[str]) -> dict[str, Any]:
        return {
            metric: {
                count: sum(expected_files[name][metric][count] for name in names)
                for count in ("covered", "total")
            }
            for metric in ("statements", "branches")
        }

    assert coverage["global"] == aggregate(list(expected_files))
    assert coverage["packages"] == {
        "simrecon": expected_files["src/simrecon/sample.py"],
        "scripts": aggregate(["scripts/sample.py", "scripts/branchless.py"]),
    }
    if not observed.native_emissions and COVERAGE_HTML in generated:
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
    expected_phases = [
        "tests",
        "coverage-combine",
        "coverage-json",
        "coverage-html",
    ]
    assert events and [event["phase"] for event in events] == expected_phases[: len(events)], (
        "incomplete native generation"
    )
    calls = {call["phase"]: call for call in phase_calls(observed)}
    assert [event["phase"] for event in events] == [
        call["phase"] for call in phase_calls(observed) if call["phase"] in expected_phases
    ], "actual native phase emission omitted"
    for event in events:
        assert event["token"] == observed.token, "stale native generation"
        assert event["status"] == calls[event["phase"]]["status"]
    expected_operations = [
        "CoverageData.add_arcs/write",
        "Coverage.combine/save",
        "Coverage.json_report",
        "Coverage.html_report",
    ]
    assert [event["operation"] for event in events] == expected_operations[: len(events)]
    if len(events) == 1:
        # A tests-phase shard is an input, not a claimed retained current DB.
        return
    shard, combined = events[:2]
    assert shard["shards"] and set(shard["shards"]) == set(combined["shards"])
    for name, before in shard["shards"].items():
        assert before["exists"] is True
        assert combined["shards"][name] == {"sha256": before["sha256"], "exists": False}
    current = events[-1]
    database = current["database"]
    assert database and all(event["database"] == database for event in events[1:])
    expected = base64.b64decode(current["database_payload"])
    assert_native_container(expected, NATIVE_ARCS)
    final = observed.files.get(database)
    assert final is not None and sha256(final) == sha256(expected), (
        "current native database replaced"
    )
    assert final == expected, "complete native container changed"
    assert_native_container(final, NATIVE_ARCS)
    if current["phase"] != "coverage-html":
        return
    html = current
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
    wheel_calls = [call for call in phase_calls(observed) if call["phase"] == "wheel"]
    assert len(wheel_calls) == 1 and set(wheel_calls[0]["wheel_members"]) == {WHEEL}, (
        "no sole current emitted wheel"
    )
    payload = observed.files[receipt["artifact"]["path"]]
    assert payload == generated_bytes(observed)[WHEEL], "emitted wheel replaced"
    assert receipt["artifact"] == {
        "path": WHEEL,
        "size_bytes": len(payload),
        "sha256": sha256(payload),
        "version": "1.2.0",
    }
    assert_wheel_container(payload)


def assert_wheel_container(payload: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        info = "simrecon-1.2.0.dist-info"
        names = archive.namelist()
        assert len(names) == len(set(names)), "ambiguous duplicate archive member"
        assert [name for name in names if name.endswith(".dist-info/METADATA")] == [
            f"{info}/METADATA"
        ], "no sole distribution metadata"
        assert (
            archive.read(f"{info}/METADATA")
            == b"Metadata-Version: 2.1\nName: simrecon\nVersion: 1.2.0\n"
        )
        wheel_fields = archive.read(f"{info}/WHEEL").decode().splitlines()
        assert [line for line in wheel_fields if line.startswith("Wheel-Version:")] == [
            "Wheel-Version: 1.0"
        ]
        # This fixture's emitted filename establishes its independent tag set.
        assert {line for line in wheel_fields if line.startswith("Tag:")} == {"Tag: py3-none-any"}
        rows = list(csv.reader(archive.read(f"{info}/RECORD").decode().splitlines()))
        assert len(rows) == len(names)
        assert {row[0] for row in rows} == set(names)
        for name, fingerprint, size in rows:
            if name == f"{info}/RECORD":
                assert (fingerprint, size) == ("", "")
            else:
                data = archive.read(name)
                algorithm, separator, encoded = fingerprint.partition("=")
                assert separator and algorithm and encoded, "malformed member hash"
                member_hash = hashlib.new(algorithm, data)
                # Admit supported secure fixed-size member hashes by strength,
                # not a fixture-only algorithm whitelist. MD5/SHA1 and their
                # concatenation remain weak regardless of digest byte length.
                assert member_hash.name not in {"md5", "sha1", "md5-sha1"}, "weak member hash"
                assert member_hash.digest_size >= hashlib.sha256().digest_size, (
                    "member hash below SHA256 strength"
                )
                digest = base64.urlsafe_b64encode(member_hash.digest()).rstrip(b"=").decode()
                assert encoded == digest, "member digest does not describe actual bytes"
                assert int(size) == len(data)


def wheel_observation(payload: bytes) -> dict[str, Any]:
    """Export actual pre-persistence archive observation without member source bytes."""
    operation = "zipfile.ZipFile/read;csv.reader"
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            members = [
                {
                    "name": item.filename,
                    "sha256": sha256(archive.read(item)),
                    "size_bytes": len(archive.read(item)),
                }
                for item in archive.infolist()
            ]
            records = {
                item.filename: list(csv.reader(archive.read(item).decode().splitlines()))
                for item in archive.infolist()
                if item.filename.endswith(".dist-info/RECORD")
            }
    except (zipfile.BadZipFile, ValueError, UnicodeError) as error:
        return {
            "operation": operation,
            "available": False,
            "error_category": type(error).__name__,
            "message": str(error),
        }
    return {"operation": operation, "available": True, "members": members, "records": records}


def unavailable_current_log(observed: Observation, call: dict[str, Any], name: str) -> bool:
    """Independent obstruction of uncreated final-phase persistence, not lost logs."""
    if (
        observed.status == 0
        or call is not phase_calls(observed)[-1]
        or call["phase"] in observed.retained_logs
    ):
        return False
    if name in observed.blocked_logs and call["blocked_log"] == name:
        return True
    # Honest rejection can leave protected current evidence at the log path.
    # It is not a previously retained log for this phase. Bind obstruction to
    # independently emitted bytes and actual phase-created alias/inode facts.
    protected = valid_emitted_reports(observed)
    for event in observed.native_emissions:
        if event["database"]:
            protected[event["database"]] = base64.b64decode(event["database_payload"])
        protected.update(
            {name: base64.b64decode(value) for name, value in event["members"].items()}
        )
    protected.update(
        {
            anchor["path"]: base64.b64decode(anchor["payload"])
            for anchor in observed.retained_logs.values()
        }
    )
    payload = observed.files.get(name)
    if name in protected and payload == protected[name]:
        return True
    action = call["action"]
    return bool(
        action
        and action["destination"] == name
        and action["applied"]
        and action["shares_inode"] is True
        and action["target"] in protected
        and action["before"] == action["after"] == sha256(protected[action["target"]])
        and payload == protected[action["target"]]
    )


def assert_retained_logs(observed: Observation) -> None:
    """Actual retained output binds even failed or receipt-unavailable outcomes."""
    calls = phase_calls(observed)
    for call in calls:
        anchor = observed.retained_logs.get(call["phase"])
        if anchor is not None:
            payload = base64.b64decode(anchor["payload"])
            assert call["stdout"].encode() in payload and call["stderr"].encode() in payload
            assert observed.files.get(anchor["path"]) == payload, (
                "previously retained current phase log lost/replaced"
            )
    if observed.receipt is not None:
        for item, call in zip(observed.receipt["phases"], calls, strict=True):
            payload = observed.files.get(item["log"])
            if unavailable_current_log(observed, call, item["log"]):
                continue
            if payload is not None:
                assert call["stdout"].encode() in payload and call["stderr"].encode() in payload, (
                    "current emitted phase output was replaced"
                )
            else:
                # Independent phase-created directory proves unavailable
                # persistence. A failed status or problem string alone does not.
                raise AssertionError(
                    "reported current phase log unavailable without persistence evidence"
                )


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
    # Preservation follows actual emission, not receipt presence or inclusion.
    assert_emitted_reports(observed)
    assert_retained_logs(observed)
    if receipt is None:
        if observed.native_emissions:
            assert_native_evidence(observed)
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
    environment = receipt["environment"]
    expected_environment = observed.expected_environment
    assert environment["platform"] == expected_environment["platform"]
    assert (
        str(Path(environment["python"]["executable"]).resolve())
        == (expected_environment["python_executable"])
    )
    assert expected_environment["python_version"] in environment["python"]["version"]
    for name in ("make", "uv"):
        assert environment[name]["executable"] == observed.bin_dir + "/" + name
        assert environment[name]["version"] in {expected_environment[name + "_version"], "1.0"}
    assert (
        str(Path(environment["git"]["executable"]).resolve())
        == (expected_environment["git_executable"])
    )
    assert environment["git"]["version"] == expected_environment["git_version"]
    assert set(environment["tools"]) == set(expected_environment["tools"])
    for name, value in environment["tools"].items():
        if value is not None:
            independent_version = expected_environment["tools"][name]
            assert value in {independent_version, f"{name} {independent_version}"}, (
                "untruthful check-tool version"
            )
        elif any(call["phase"] == "sync" and call["status"] == 0 for call in calls):
            pytest.fail("available controlled check-tool version missing")
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
    for item in receipt["phases"]:
        phase_begin, phase_end = (
            datetime.fromisoformat(item[key]) for key in ("started_at", "finished_at")
        )
        for stamp in (phase_begin, phase_end):
            offset = stamp.utcoffset()
            assert offset is not None and offset.total_seconds() == 0
        assert begin <= phase_begin <= phase_end <= end, "phase timestamps outside current receipt"
        path = Path(item["log"])
        assert not path.is_absolute() and ".." not in path.parts
    if expected_measurement(observed) is not None:
        assert receipt.get("measurements") is not None, "valid current measurements omitted"
    if receipt.get("measurements") is not None:
        assert_measurement(observed, receipt)
    generated = valid_emitted_reports(observed)
    if COVERAGE_JSON in generated:
        assert receipt.get("coverage") is not None, "valid current coverage diagnostics omitted"
    if receipt.get("coverage") is not None:
        assert_coverage(observed, receipt)
    wheel_calls = [call for call in calls if call["phase"] == "wheel"]
    if WHEEL in generated and len(wheel_calls) == 1 and len(wheel_calls[0]["wheel_members"]) == 1:
        assert receipt.get("artifact") is not None, "valid current wheel diagnostics omitted"
    if receipt.get("artifact") is not None:
        assert_wheel(observed, receipt)
    if observed.status == 0:
        assert set(REPORTS) <= set(generated), "missing complete current report emission"
        assert receipt["measurements"] is not None
        assert receipt["artifact"] is not None
    if observed.native_emissions:
        assert_native_evidence(observed)


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
        observed.retained_logs[phase["name"]]["path"] = phase["log"]
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
        observed.retained_logs[phase["name"]]["path"] = phase["log"]
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


def prepare_native_directory(repository: Repository, name: str, alias: bool) -> None:
    """Ignored public layout; external storage belongs only to this disposable fixture."""
    directory = repository.root / name
    directory.parent.mkdir(parents=True, exist_ok=True)
    if alias:
        external = repository.root.parent / "owned-native-storage"
        external.mkdir()
        directory.symlink_to(external, target_is_directory=True)
        assert directory.resolve() == external.resolve()
    else:
        directory.mkdir()
    assert git(repository.root, "check-ignore", name) == name


@pytest.mark.parametrize("alias", [False, True], ids=["ordinary", "directory-alias"])
@pytest.mark.parametrize("collision", [False, True], ids=["neighbor", "collision"])
def test_p11_directory_receipt_preserves_current_native_evidence(
    evidence_repository: Repository, alias: bool, collision: bool
) -> None:
    directory = "artifacts/native-output"
    prepare_native_directory(evidence_repository, directory, alias)
    data_file = directory + "/current.data"
    destination = data_file if collision else directory + "/receipt.json"
    observed = invoke(evidence_repository, destination, native=True, data_file=data_file)
    if not collision:
        assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)


@pytest.mark.parametrize("alias", [False, True], ids=["ordinary", "directory-alias"])
@pytest.mark.parametrize("leaf", ["audit.log", "unused-native.data"])
def test_p11_directory_log_example_preserves_current_native_evidence(
    evidence_repository: Repository, alias: bool, leaf: str
) -> None:
    # The leaf is only a layout example. assert_outcome binds actually reported
    # current log output, and independently preserves the actual emitted DB.
    # A different log layout can pass; no leaf recurrence or alias ban follows.
    directory = "artifacts/verification/logs"
    prepare_native_directory(evidence_repository, directory, alias)
    observed = invoke(evidence_repository, native=True, data_file=directory + "/" + leaf)
    if leaf == "unused-native.data":
        assert observed.status == 0, observed.stdout + observed.stderr
    assert_outcome(observed)


@pytest.mark.parametrize("entry", ["receipt", "current-log-example"])
def test_p07_directory_alias_keeps_native_evidence_and_actual_failure(
    evidence_repository: Repository, entry: str
) -> None:
    directory = "artifacts/native-output" if entry == "receipt" else "artifacts/verification/logs"
    prepare_native_directory(evidence_repository, directory, True)
    data_file = directory + ("/current.data" if entry == "receipt" else "/audit.log")
    destination = data_file if entry == "receipt" else DEFAULT_RECEIPT
    observed = invoke(
        evidence_repository, destination, native=True, data_file=data_file, audit_failure=True
    )
    # Honest early rejection may precede audit. If audit ran, the common oracle
    # requires its genuine status 37, no continuation and all retained evidence.
    assert_outcome(observed)


def test_p04_p11_phase_created_directory_receipt_alias(
    evidence_repository: Repository,
) -> None:
    prepare_native_directory(evidence_repository, "artifacts/native-output", True)
    action = {
        "phase": "audit",
        "destination": "artifacts/new-alias",
        "selector": "database",
        "kind": "directory-alias",
    }
    observed = invoke(
        evidence_repository,
        "artifacts/new-alias/current.data",
        action=action,
        native=True,
        data_file="artifacts/native-output/current.data",
    )
    assert_outcome(observed)


def test_p10_finite_cyclic_receipt_alias_rejects_honestly(
    evidence_repository: Repository,
) -> None:
    root = evidence_repository.root
    (root / "artifacts").mkdir(exist_ok=True)
    (root / "artifacts/cycle-a").symlink_to("cycle-b", target_is_directory=True)
    (root / "artifacts/cycle-b").symlink_to("cycle-a", target_is_directory=True)
    observed = invoke(evidence_repository, "artifacts/cycle-a/receipt.json", native=True)
    assert observed.status == 1
    assert_outcome(observed)


@pytest.mark.parametrize("order", ["stdout-first", "stderr-first"])
def test_local_log_observer_allows_both_stream_orders(
    observed_success: Observation, order: str
) -> None:
    observed = copy.deepcopy(observed_success)
    assert observed.receipt is not None
    for item, call in zip(observed.receipt["phases"], phase_calls(observed), strict=True):
        streams = [call["stdout"], call["stderr"]]
        if order == "stderr-first":
            streams.reverse()
        observed.files[item["log"]] = "".join(streams).encode()
        observed.retained_logs[item["name"]]["payload"] = base64.b64encode(
            observed.files[item["log"]]
        ).decode()
    assert_outcome(observed)


@pytest.mark.parametrize("defect", ["version-missing", "version-invented", "unemitted-version"])
def test_local_metadata_observer_rejects_untruthful_versions(
    observed_success: Observation, defect: str
) -> None:
    observed = copy.deepcopy(observed_success)
    assert observed.receipt is not None
    if defect == "version-missing":
        observed.receipt["environment"]["tools"]["coverage"] = None
    elif defect == "version-invented":
        observed.receipt["environment"]["tools"]["coverage"] = "invented coverage version"
    else:
        # Self-consistent query output cannot justify fabricated metadata.
        observed.receipt["environment"]["tools"]["coverage"] = "coverage 0.0.fabricated"
        for call in observed.calls:
            if "coverage" in call["argv"] and call["phase"] is None:
                call["stdout"] = "coverage 0.0.fabricated\n"
    with pytest.raises((AssertionError, pytest.fail.Exception)):
        assert_outcome(observed)


@pytest.mark.parametrize("form", ["display", "distribution"])
def test_local_metadata_observer_allows_truth_without_query_records(
    observed_success: Observation, form: str
) -> None:
    observed = copy.deepcopy(observed_success)
    assert observed.receipt is not None
    observed.calls = [call for call in observed.calls if call["phase"] is not None]
    if form == "distribution":
        observed.receipt["environment"]["tools"] = observed.expected_environment["tools"].copy()
        for name in ("make", "uv"):
            observed.receipt["environment"][name]["version"] = "1.0"
    assert_outcome(observed)


@pytest.fixture
def observed_tests_failure(evidence_repository: Repository) -> Observation:
    observed = invoke(evidence_repository, mode="tests-failure")
    assert observed.status == 37
    assert_outcome(observed)
    return observed


@pytest.fixture
def observed_late_failure(evidence_repository: Repository) -> Observation:
    observed = invoke(evidence_repository, audit_failure=True)
    assert observed.status == 37
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("receipt_available", [False, True])
def test_local_failed_measurement_observer_allows_current_diagnostics(
    observed_tests_failure: Observation, receipt_available: bool
) -> None:
    observed = copy.deepcopy(observed_tests_failure)
    if not receipt_available:
        observed.receipt = None
        observed.files.pop(DEFAULT_RECEIPT)
    assert_outcome(observed)


@pytest.mark.parametrize("defect", ["deleted", "replaced", "omitted", "suppressed-anchor"])
@pytest.mark.parametrize("receipt_available", [False, True])
def test_local_failed_measurement_observer_rejects_lost_valid_evidence(
    observed_tests_failure: Observation, defect: str, receipt_available: bool
) -> None:
    observed = copy.deepcopy(observed_tests_failure)
    if defect == "deleted":
        del observed.files[MEASUREMENT]
    elif defect == "replaced":
        observed.files[MEASUREMENT] = b"not current M25 evidence"
    elif defect == "suppressed-anchor":
        phase_calls(observed)[-1]["snapshots"].pop(MEASUREMENT)
    else:
        assert observed.receipt is not None
        observed.receipt["measurements"] = None
    if not receipt_available:
        observed.receipt = None
        # Omission of an unavailable receipt alone is legitimate. Combine it
        # with loss of emitted bytes to exercise the original no-receipt hole.
        if defect == "omitted":
            del observed.files[MEASUREMENT]
    with pytest.raises((AssertionError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("alternative", ["ordinary", "no-receipt", "failed-log-persistence"])
def test_local_late_failure_observer_allows_preserved_evidence(
    observed_late_failure: Observation,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    alternative: str,
) -> None:
    observed = copy.deepcopy(observed_late_failure)
    if alternative == "no-receipt":
        observed.receipt = None
        observed.files.pop(DEFAULT_RECEIPT)
    elif alternative == "failed-log-persistence":
        # A separate owned public invocation creates a real directory blocker
        # before persistence. The example may be unused by another valid layout.
        repository = prepare_evidence_repository(tmp_path / "blocked", monkeypatch)
        observed = invoke(repository, audit_failure=True, block_log=LOG_EXAMPLES[-1])
        assert observed.status == 37
    assert_outcome(observed)


@pytest.mark.parametrize("target", [COVERAGE_JSON, COVERAGE_HTML, WHEEL])
@pytest.mark.parametrize("defect", ["deleted", "replaced", "omitted", "no-receipt"])
def test_local_late_failure_observer_rejects_lost_valid_reports(
    observed_late_failure: Observation, target: str, defect: str
) -> None:
    observed = copy.deepcopy(observed_late_failure)
    if defect == "replaced":
        observed.files[target] = b"replaced actual emitted evidence"
    elif defect == "omitted":
        assert observed.receipt is not None
        observed.receipt["artifact" if target == WHEEL else "coverage"] = None
    else:
        del observed.files[target]
        if defect == "no-receipt":
            observed.receipt = None
    with pytest.raises((AssertionError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("phase", ["coverage-json", "wheel"])
def test_p07_valid_phase_emission_survives_its_genuine_failure(
    evidence_repository: Repository, phase: str
) -> None:
    observed = invoke(evidence_repository, failure_phase=phase, native=True)
    assert observed.status == 37
    assert phase_calls(observed)[-1]["phase"] == phase
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
@pytest.mark.parametrize("target", ["database", "html-member"])
def test_local_native_failure_observer_rejects_loss_without_receipt_dependency(
    evidence_repository: Repository, receipt_available: bool, target: str
) -> None:
    observed = invoke(evidence_repository, native=True, audit_failure=True)
    assert observed.status == 37
    assert_outcome(observed)
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)
    html = observed.native_emissions[-1]
    name = (
        html["database"]
        if target == "database"
        else next(name for name in html["members"] if name != COVERAGE_HTML)
    )
    del observed.files[name]
    with pytest.raises((AssertionError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("phase", ["coverage-combine", "coverage-json"])
def test_local_partial_native_failure_observer_rejects_lost_container(
    evidence_repository: Repository, phase: str
) -> None:
    observed = invoke(evidence_repository, native=True, failure_phase=phase)
    assert observed.status == 37
    assert_outcome(observed)
    observed.receipt = None
    assert_outcome(observed)
    del observed.files[observed.native_emissions[-1]["database"]]
    with pytest.raises(AssertionError):
        assert_outcome(observed)


@pytest.mark.parametrize("mode", ["tests-no-report", "malformed", "duplicate-top"])
def test_local_failed_measurement_observer_allows_absent_or_invalid_emission(
    evidence_repository: Repository, mode: str
) -> None:
    observed = invoke(evidence_repository, mode=mode)
    assert observed.status != 0
    assert expected_measurement(observed) is None
    assert_outcome(observed)
    observed.files.pop(MEASUREMENT, None)
    assert_outcome(observed)
    observed.receipt = None
    assert_outcome(observed)


@pytest.mark.parametrize(
    "mode",
    [
        "missing-json",
        "missing-html",
        "missing-wheel",
        "malformed-coverage",
        "invalid-wheel",
        "multiple-wheels",
    ],
)
def test_local_failure_observer_allows_unavailable_or_invalid_report_evidence(
    evidence_repository: Repository, mode: str
) -> None:
    observed = invoke(evidence_repository, receipt_mode=mode)
    assert observed.status == 1
    assert_outcome(observed)
    # Only valid actually emitted fixture evidence is retained. Invalid bytes
    # and unrun/missing phases cannot fabricate available diagnostics.
    for name in set(generated_bytes(observed)) - set(valid_emitted_reports(observed)):
        observed.files.pop(name, None)
    assert_outcome(observed)
    observed.receipt = None
    assert_outcome(observed)


@pytest.fixture(params=["tests", "audit"])
def current_log_failure(
    evidence_repository: Repository, request: pytest.FixtureRequest
) -> Observation:
    observed = invoke(evidence_repository, failure_phase=request.param)
    assert observed.status == 37
    assert phase_calls(observed)[-1]["phase"] == request.param
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("receipt_available", [False, True])
@pytest.mark.parametrize("order", ["stdout-first", "stderr-first"])
def test_local_failed_log_observer_allows_current_output_and_layouts(
    current_log_failure: Observation, receipt_available: bool, order: str
) -> None:
    observed = copy.deepcopy(current_log_failure)
    assert observed.receipt is not None
    for item, call in zip(observed.receipt["phases"], phase_calls(observed), strict=True):
        # Model another actual legitimate emission/layout: neither stream order
        # nor the public example leaves define the preservation contract.
        streams = [call["stdout"], call["stderr"]]
        if order == "stderr-first":
            streams.reverse()
        payload = "".join(streams).encode()
        old = item["log"]
        item["log"] = f"artifacts/alternate-logs/current-{call['phase']}.txt"
        observed.files[item["log"]] = payload
        observed.files[old] = b"unused layout example"
        observed.retained_logs[call["phase"]] = {
            "path": item["log"],
            "payload": base64.b64encode(payload).decode(),
        }
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
@pytest.mark.parametrize("defect", ["deleted", "replaced"])
def test_local_failed_log_observer_rejects_loss_of_earlier_retention(
    current_log_failure: Observation, receipt_available: bool, defect: str
) -> None:
    observed = copy.deepcopy(current_log_failure)
    anchor = observed.retained_logs["sync"]
    # Retention was already observed by a later real external phase command.
    assert any("sync" in call["retained_logs"] for call in observed.calls)
    if defect == "deleted":
        del observed.files[anchor["path"]]
    else:
        observed.files[anchor["path"]] = b"forged old output"
    if not receipt_available:
        observed.receipt = None
    with pytest.raises(AssertionError):
        assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
def test_local_failed_log_observer_allows_genuine_unavailable_persistence(
    evidence_repository: Repository, receipt_available: bool
) -> None:
    observed = invoke(evidence_repository, audit_failure=True, block_log=LOG_EXAMPLES[-1])
    assert observed.status == 37
    assert observed.blocked_logs == (LOG_EXAMPLES[-1],)
    assert_outcome(observed)
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


PARTIAL_PROFILES = ["partial-coverage", "partial-statements", "partial-combined", "zero-coverage"]


@pytest.fixture(params=[*PARTIAL_PROFILES, "partial-json-failure"])
def current_partial_failure(
    evidence_repository: Repository, request: pytest.FixtureRequest
) -> Observation:
    phase = None if request.param == "partial-json-failure" else "coverage-json"
    observed = invoke(evidence_repository, receipt_mode=request.param, failure_phase=phase)
    assert observed.status == (29 if phase is None else 37)
    assert COVERAGE_JSON in valid_emitted_reports(observed)
    assert COVERAGE_HTML not in generated_bytes(observed)
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("receipt_available", [False, True])
def test_local_partial_coverage_observer_allows_current_failed_diagnostics(
    current_partial_failure: Observation, receipt_available: bool
) -> None:
    observed = copy.deepcopy(current_partial_failure)
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
@pytest.mark.parametrize("defect", ["deleted", "replaced", "omitted"])
def test_local_partial_coverage_observer_rejects_lost_current_diagnostics(
    current_partial_failure: Observation, receipt_available: bool, defect: str
) -> None:
    observed = copy.deepcopy(current_partial_failure)
    assert observed.receipt is not None
    if defect == "replaced":
        observed.files[COVERAGE_JSON] = b"{}"
    elif defect == "omitted" and receipt_available:
        observed.receipt["coverage"] = None
    else:
        del observed.files[COVERAGE_JSON]
    if not receipt_available:
        observed.receipt = None
    with pytest.raises((AssertionError, KeyError)):
        assert_outcome(observed)


@pytest.mark.parametrize("profile", PARTIAL_PROFILES)
def test_p07_advisory_profiles_preserve_exact_current_counts(
    evidence_repository: Repository, profile: str
) -> None:
    observed = invoke(evidence_repository, receipt_mode=profile)
    assert observed.status == 0
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
def test_p07_partial_json_status29_retains_current_report_without_html(
    evidence_repository: Repository, receipt_available: bool
) -> None:
    observed = invoke(evidence_repository, receipt_mode="partial-json-failure")
    assert observed.status == 29
    assert phase_calls(observed)[-1]["phase"] == "coverage-json"
    assert COVERAGE_JSON in valid_emitted_reports(observed)
    assert COVERAGE_HTML not in generated_bytes(observed)
    assert_outcome(observed)
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


@pytest.fixture(params=["wheel", "audit"])
def current_stronger_wheel_failure(
    evidence_repository: Repository, request: pytest.FixtureRequest
) -> Observation:
    observed = invoke(evidence_repository, receipt_mode="sha512-wheel", failure_phase=request.param)
    assert observed.status == 37
    assert phase_calls(observed)[-1]["phase"] == request.param
    assert WHEEL in valid_emitted_reports(observed)
    wheel = wheel_observation(generated_bytes(observed)[WHEEL])
    assert wheel["available"] is True
    assert {
        row[1].split("=")[0] for rows in wheel["records"].values() for row in rows if row[1]
    } == {"sha512"}
    assert_outcome(observed)
    return observed


@pytest.mark.parametrize("receipt_available", [False, True])
def test_local_stronger_wheel_observer_allows_failed_current_diagnostics(
    current_stronger_wheel_failure: Observation, receipt_available: bool
) -> None:
    observed = copy.deepcopy(current_stronger_wheel_failure)
    assert observed.receipt is not None
    assert_wheel(observed, observed.receipt)
    # The outer transport identity is still actual archive SHA256, independent
    # of stronger RECORD member hashes. No receipt creates no new diagnostic.
    assert observed.receipt["artifact"]["sha256"] == sha256(generated_bytes(observed)[WHEEL])
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
@pytest.mark.parametrize("defect", ["deleted", "replaced", "omitted"])
def test_local_stronger_wheel_observer_rejects_lost_valid_current_evidence(
    current_stronger_wheel_failure: Observation, receipt_available: bool, defect: str
) -> None:
    observed = copy.deepcopy(current_stronger_wheel_failure)
    assert observed.receipt is not None
    if defect == "replaced":
        observed.files[WHEEL] = b"replaced current stronger-hash archive"
    elif defect == "omitted" and receipt_available:
        observed.receipt["artifact"] = None
    else:
        # Receipt absence cannot excuse losing actual valid emitted wheel bytes.
        del observed.files[WHEEL]
    if not receipt_available:
        observed.receipt = None
    with pytest.raises((AssertionError, KeyError)):
        assert_outcome(observed)


def test_p08_stronger_record_hash_keeps_success_evidence(evidence_repository: Repository) -> None:
    observed = invoke(evidence_repository, receipt_mode="sha512-wheel")
    assert observed.status == 0
    assert_outcome(observed)


@pytest.mark.parametrize("receipt_available", [False, True])
def test_p07_wheel_build_status31_keeps_valid_current_artifact(
    evidence_repository: Repository, receipt_available: bool
) -> None:
    observed = invoke(evidence_repository, receipt_mode="wheel-build-failure")
    assert observed.status == 31
    assert phase_calls(observed)[-1]["phase"] == "wheel"
    assert WHEEL in valid_emitted_reports(observed)
    assert_outcome(observed)
    if not receipt_available:
        observed.receipt = None
    assert_outcome(observed)


def record_fixture_wheel(payload: bytes, algorithm: str, defect: str = "") -> bytes:
    """Standalone archive-input control; never a verifier persistence decision.

    Rebuild the actual public fixture's archive using standard ZIP/CSV/hash
    primitives. Authentic fixture/control bytes prove bounded validity only,
    not production build provenance or actual isolated import/installability.
    """
    info = "simrecon-1.2.0.dist-info"
    record = f"{info}/RECORD"
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = {name: archive.read(name) for name in archive.namelist() if name != record}
    if defect == "missing-metadata":
        del members[f"{info}/METADATA"]
    elif defect == "multiple-metadata":
        members["simrecon_extra-1.2.0.dist-info/METADATA"] = members[f"{info}/METADATA"]
    elif defect == "invalid-wheel-format":
        members[f"{info}/WHEEL"] = members[f"{info}/WHEEL"].replace(b"1.0", b"invalid")
    elif defect == "mismatched-tag":
        members[f"{info}/WHEEL"] += b"Tag: py3-none-other\n"
    rows = []
    for name, data in members.items():
        encoded = base64.urlsafe_b64encode(hashlib.new(algorithm, data).digest()).rstrip(b"=")
        fingerprint = algorithm + "=" + encoded.decode()
        if defect == "digest":
            fingerprint = algorithm + "=" + "A" * len(encoded)
        elif defect == "unknown-algorithm":
            fingerprint = "unknown-member-hash=" + encoded.decode()
        elif defect == "malformed-hash":
            fingerprint = encoded.decode()
        if defect != "missing-member" or name != "simrecon/__init__.py":
            rows.append([name, fingerprint, str(len(data) + (1 if defect == "size" else 0))])
    if defect == "duplicate-record":
        rows.append(rows[0])
    rows.append([record, "sha512=AAAA" if defect == "hashed-self" else "", ""])
    text = io.StringIO()
    csv.writer(text, lineterminator="\n").writerows(rows)
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
        if defect == "duplicate-member":
            archive.writestr("simrecon/__init__.py", members["simrecon/__init__.py"])
        archive.writestr(record, text.getvalue())
    return result.getvalue()


@pytest.mark.parametrize(
    "algorithm", ["sha256", "sha384", "sha512", "sha3_256", "sha3_512", "blake2b", "blake2s"]
)
def test_local_wheel_observer_accepts_secure_record_algorithms(
    observed_success: Observation, algorithm: str
) -> None:
    payload = record_fixture_wheel(generated_bytes(observed_success)[WHEEL], algorithm)
    assert_wheel_container(payload)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        rows = list(
            csv.reader(archive.read("simrecon-1.2.0.dist-info/RECORD").decode().splitlines())
        )
        assert {row[1].split("=")[0] for row in rows if row[1]} == {algorithm}


@pytest.mark.parametrize(
    "defect",
    [
        "digest",
        "size",
        "weak-sha1",
        "weak-md5",
        "below-sha256",
        "unknown-algorithm",
        "malformed-hash",
        "missing-member",
        "duplicate-record",
        "hashed-self",
        "duplicate-member",
        "missing-metadata",
        "multiple-metadata",
        "invalid-wheel-format",
        "mismatched-tag",
    ],
)
def test_local_wheel_observer_rejects_invalid_record_and_archive_evidence(
    observed_success: Observation, defect: str
) -> None:
    algorithm = {"weak-sha1": "sha1", "weak-md5": "md5", "below-sha256": "sha224"}.get(
        defect, "sha512"
    )
    if defect == "duplicate-member":
        with pytest.warns(UserWarning):
            payload = record_fixture_wheel(
                generated_bytes(observed_success)[WHEEL], algorithm, defect
            )
    else:
        payload = record_fixture_wheel(generated_bytes(observed_success)[WHEEL], algorithm, defect)
    with pytest.raises((AssertionError, ValueError, KeyError)):
        assert_wheel_container(payload)
    observed = copy.deepcopy(observed_success)
    wheel = next(call for call in phase_calls(observed) if call["phase"] == "wheel")
    wheel["snapshots"][WHEEL] = base64.b64encode(payload).decode()
    assert WHEEL not in valid_emitted_reports(observed)


@pytest.mark.parametrize(
    "mode",
    [
        "weak-wheel-hash",
        "record-hash-mismatch",
        "record-size-mismatch",
        "incomplete-record",
        "invalid-record-self",
        "duplicate-member",
        "multiple-metadata",
    ],
)
def test_p07_invalid_wheel_profiles_keep_honest_unavailable_diagnostics(
    evidence_repository: Repository, mode: str
) -> None:
    observed = invoke(evidence_repository, receipt_mode=mode)
    assert observed.status == 1
    assert observed.receipt is not None and observed.receipt["artifact"] is None
    assert WHEEL not in valid_emitted_reports(observed)
    assert_outcome(observed)
    observed.files.pop(WHEEL)
    assert_outcome(observed)
    observed.receipt = None
    assert_outcome(observed)
