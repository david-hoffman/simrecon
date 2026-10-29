"""Small disposable public pytest inputs and file-backed runner observations."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS = ("-n", "2", "--dist=loadgroup", "--max-worker-restart=0")

OBSERVER = """\
import json
import os
from pathlib import Path
import pytest

HERE = Path(__file__).parent

def record(kind, **values):
    with (HERE / ("observed-" + str(os.getpid()) + ".jsonl")).open("a") as stream:
        stream.write(json.dumps(dict(kind=kind, pid=os.getpid(), **values)) + "\\n")

def pytest_collection_finish(session):
    record("collection", worker=getattr(session.config, "workerinput", {}).get("workerid"),
           nodes=[item.nodeid for item in session.items],
           groups=[[mark.args[0] for mark in item.iter_markers("xdist_group")]
                   for item in session.items])

def pytest_runtest_logreport(report):
    record("report", node=report.nodeid, when=report.when, outcome=report.outcome,
           wasxfail=getattr(report, "wasxfail", None))

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    record("finish", worker=getattr(session.config, "workerinput", {}).get("workerid"),
           reporter=terminal is not None, status=int(session.exitstatus),
           stats={} if terminal is None else {key: len(value)
                                             for key, value in terminal.stats.items()},
           processes=session.config.getoption("numprocesses", default=None))
"""


def suite(root: Path, files: dict[str, str], *, conftest: str = "") -> Path:
    """Create fresh mutable inputs with the project's actual strict policy plugin."""
    root.mkdir(parents=True)
    (root / "pytest.ini").write_text(
        "[pytest]\naddopts = --strict-config --strict-markers -ra -p simrecon._pytest_policy\n"
        "strict_xfail = true\n",
        encoding="utf-8",
    )
    (root / "conftest.py").write_text(OBSERVER + conftest, encoding="utf-8")
    for relative, source in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return root


def run(
    root: Path,
    *,
    workers: bool = True,
    arguments: tuple[str, ...] = (),
    timeout: int = 40,
    environment: dict[str, str] | None = None,
    prefix: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    """Launch one bounded public runner and retain original streams and argv."""
    argv = [
        sys.executable,
        str(ROOT / "scripts/source_free_check.py"),
        "--timeout",
        str(timeout),
        "pytest" if not prefix else "python",
        *prefix,
        "-q",
        "-c",
        str(root / "pytest.ini"),
        str(root / "tests"),
        *(FLAGS if workers else ()),
        *arguments,
    ]
    env = os.environ.copy() | (environment or {})
    result = subprocess.run(
        argv, cwd=root, env=env, capture_output=True, text=True, timeout=timeout + 10
    )
    (root / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (root / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    (root / "invocation.json").write_text(
        json.dumps(
            {
                "argv": argv,
                "cwd": str(root),
                "status": result.returncode,
                "environment": {
                    key: value
                    for key, value in env.items()
                    if key.startswith(("COVERAGE_", "PYTEST_"))
                    or key in ("PATH", "PYTHONPATH", "UV")
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return result


def observations(root: Path) -> list[dict]:
    """Read only our own JSON observations, never native coverage formats."""
    return [
        json.loads(line)
        for path in sorted(root.glob("observed-*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
