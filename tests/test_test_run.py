"""Contract checks for the configured serial and distributed pytest run policy."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(params=[0, 4], ids=["serial", "four-workers"])
def workers(request: pytest.FixtureRequest) -> int:
    return int(request.param)


def _run_suite(
    tmp_path: Path,
    test_source: str | None,
    workers: int,
    *,
    conftest_source: str | None = None,
) -> subprocess.CompletedProcess[str]:
    suite = tmp_path / "suite"
    suite.mkdir()
    if test_source is not None:
        (suite / "test_case.py").write_text(test_source, encoding="utf-8")
    if conftest_source is not None:
        (suite / "conftest.py").write_text(conftest_source, encoding="utf-8")

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
            "-n",
            str(workers),
            "--dist=loadgroup",
            "--max-worker-restart=0",
            "--tb=line",
            "--show-capture=no",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def _check_result(
    result: subprocess.CompletedProcess[str],
    *,
    status: int,
    diagnostic: str,
    collection_error: bool = False,
) -> None:
    output = result.stdout + result.stderr
    if result.returncode != status:
        pytest.fail(f"wrong pytest exit status: {result.returncode}; expected {status}")
    if not re.search(diagnostic, output, flags=re.IGNORECASE):
        pytest.fail(f"missing pytest diagnostic: {diagnostic}")
    if re.search(r"ImportError|ModuleNotFoundError|INTERNALERROR", output):
        pytest.fail("pytest encountered an import or internal error")
    if not collection_error and re.search(r"ERROR collecting", output):
        pytest.fail("pytest encountered an unintended collection error")


def test_complete_passing_suite_succeeds(tmp_path: Path, workers: int) -> None:
    result = _run_suite(tmp_path, "def test_pass():\n    assert True\n", workers)
    _check_result(result, status=0, diagnostic=r"\b1 passed\b")


def test_empty_discovery_fails(tmp_path: Path, workers: int) -> None:
    result = _run_suite(tmp_path, None, workers)
    _check_result(result, status=5, diagnostic=r"\bno tests ran\b")


def test_skipped_test_fails(tmp_path: Path, workers: int) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\n\ndef test_skip():\n    pytest.skip("planned skip")\n',
        workers,
    )
    _check_result(result, status=1, diagnostic=r"\b1 skipped\b")


def test_collection_skip_fails(tmp_path: Path, workers: int) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\npytest.skip("planned collection skip", allow_module_level=True)\n',
        workers,
    )
    _check_result(result, status=1, diagnostic=r"\b1 skipped\b")


def test_expected_failure_fails(tmp_path: Path, workers: int) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\n\n@pytest.mark.xfail(reason="expected failure")\n'
        "def test_xfail():\n    assert False\n",
        workers,
    )
    _check_result(result, status=1, diagnostic=r"\b1 xfailed\b")


def test_non_strict_unexpected_pass_fails(tmp_path: Path, workers: int) -> None:
    result = _run_suite(
        tmp_path,
        'import pytest\n\n@pytest.mark.xfail(strict=False, reason="unexpected pass")\n'
        "def test_xpass():\n    assert True\n",
        workers,
    )
    _check_result(result, status=1, diagnostic=r"\b1 xpassed\b")


def test_native_failure_keeps_failure_status(tmp_path: Path, workers: int) -> None:
    result = _run_suite(
        tmp_path, 'def test_failure():\n    assert False, "POLICY_NATIVE_SENTINEL"\n', workers
    )
    _check_result(result, status=1, diagnostic=r"\b1 failed\b")
    assert "POLICY_NATIVE_SENTINEL" in result.stdout + result.stderr


def test_collection_error_keeps_failure_status(tmp_path: Path, workers: int) -> None:
    result = _run_suite(tmp_path, 'raise RuntimeError("POLICY_COLLECTION_SENTINEL")\n', workers)
    _check_result(
        result,
        status=2 if workers == 0 else 1,
        diagnostic=r"\b1 error\b" if workers == 0 else r"\b[1-9]\d* errors?\b",
        collection_error=True,
    )
    assert re.search(r"ERROR collecting .*suite[/\\]test_case\.py", result.stdout + result.stderr)
    assert "RuntimeError: POLICY_COLLECTION_SENTINEL" in result.stdout + result.stderr


def test_serial_child_inside_worker_still_rejects_skip(tmp_path: Path) -> None:
    source = (
        "import os, re, subprocess, sys\n"
        "from xdist import is_xdist_worker\n\n"
        "def test_nested(request, tmp_path):\n"
        "    assert is_xdist_worker(request)\n"
        "    assert os.environ['PYTEST_XDIST_WORKER'].startswith('gw')\n"
        "    suite = tmp_path / 'nested'\n"
        "    suite.mkdir()\n"
        "    (suite / 'test_nested_skip.py').write_text(\n"
        "        'import pytest\\ndef test_skip():\\n    pytest.skip(\"nested skip\")\\n')\n"
        "    command = [sys.executable, '-m', 'pytest', '-c',\n"
        f"               {str(PROJECT_ROOT / 'pyproject.toml')!r}, str(suite), '-n', '0',\n"
        "               '--max-worker-restart=0', '--tb=line', '--show-capture=no']\n"
        "    result = subprocess.run(command, capture_output=True, text=True, timeout=30)\n"
        "    output = result.stdout + result.stderr\n"
        "    assert result.returncode == 1, (result.returncode, output)\n"
        "    assert re.search(r'\\b1 skipped\\b', output)\n"
        "    assert not re.search(\n"
        "        r'ERROR collecting|ImportError|ModuleNotFoundError|INTERNALERROR', output)\n"
    )
    result = _run_suite(tmp_path, source, 4)
    _check_result(result, status=0, diagnostic=r"\b1 passed\b")


def test_worker_crash_fails_without_replacement(tmp_path: Path) -> None:
    lifecycle = tmp_path / "worker-lifecycle.jsonl"
    crash = tmp_path / "worker-crash.json"
    conftest = (
        "import json\nfrom pathlib import Path\n\n"
        "def record(event, worker, error=None):\n"
        f"    with Path({str(lifecycle)!r}).open('a') as stream:\n"
        "        stream.write(json.dumps({'event': event, 'worker': worker, "
        "'error': error})+'\\n')\n\n"
        "def pytest_xdist_newgateway(gateway):\n"
        "    record('created', gateway.id)\n\n"
        "def pytest_testnodedown(node, error):\n"
        "    record('down', node.gateway.id, str(error) if error is not None else None)\n"
    )
    source = (
        "import json, os\nfrom pathlib import Path\n"
        "from xdist import get_xdist_worker_id\n\n"
        "def test_crash(request):\n"
        f"    Path({str(crash)!r}).write_text(json.dumps(\n"
        "        {'worker': get_xdist_worker_id(request), 'pid': os.getpid()}))\n"
        "    os._exit(17)\n"
    )
    result = _run_suite(tmp_path, source, 4, conftest_source=conftest)
    (tmp_path / "worker-crash.stdout").write_text(result.stdout, encoding="utf-8")
    (tmp_path / "worker-crash.stderr").write_text(result.stderr, encoding="utf-8")
    (tmp_path / "worker-crash-command.json").write_text(
        json.dumps({"command": result.args, "status": result.returncode}), encoding="utf-8"
    )
    _check_result(result, status=1, diagnostic=r"\b1 failed\b")
    output = result.stdout + result.stderr
    crashed = set(re.findall(r"worker (gw\d+) crashed and worker restarting disabled", output))
    events = [json.loads(line) for line in lifecycle.read_text().splitlines()]
    created = [event["worker"] for event in events if event["event"] == "created"]
    down = [event for event in events if event["event"] == "down"]
    failed = [event for event in down if event["error"] is not None]
    executed = json.loads(crash.read_text())
    assert sorted(created) == ["gw0", "gw1", "gw2", "gw3"]
    assert sorted(event["worker"] for event in down) == sorted(created)
    assert len(failed) == 1
    assert crashed == {failed[0]["worker"]} == {executed["worker"]}
    assert isinstance(executed["pid"], int) and executed["pid"] > 0
