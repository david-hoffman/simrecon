"""Exercise readiness through its command boundary without setup or service calls."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_dev_environment.py"


@pytest.fixture
def local_checkout(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    root = tmp_path / "checkout café"
    root.mkdir()
    tools = tmp_path / "tools with spaces"
    tools.mkdir()
    environment = {
        **os.environ,
        "PATH": str(tools),
        "UV": str(tools / "uv"),
        "SIMRECON_JAVA": str(tools / "java"),
        "DEV105_CALLS": str(tmp_path / "calls.jsonl"),
        "DEV105_ROOT": str(root),
        "DEV105_FAILURE": "",
    }
    source = """\
import json
import os
from pathlib import Path
import sys
import time

tool = Path(sys.argv[0]).name
args = sys.argv[1:]
with Path(os.environ['DEV105_CALLS']).open('a') as calls:
    calls.write(json.dumps([tool, args]) + '\\n')
failure = os.environ['DEV105_FAILURE']
root = Path(os.environ['DEV105_ROOT'])
if tool == 'uv':
    assert args == ['--version'], 'readiness attempted setup'
    if failure == 'timeout':
        time.sleep(3)
    if failure == 'nonzero':
        print('synthetic local failure', file=sys.stderr)
        sys.exit(9)
    print('uv 0.1.0' if failure == 'uv-version' else 'uv 0.12.19')
elif tool == 'java':
    assert args == ['-XshowSettings:properties', '-version']
    print('java.version = ' + ('17.0.1' if failure == 'java-version' else '21.0.7'))
    print('java.vendor = permitted alternative vendor')
    print('java.runtime.version = 21.0.7+6-test')
    print('user.home = SYNTHETIC_PRIVATE_HOME_DO_NOT_ECHO')
    print('custom.secret = SYNTHETIC_SECRET_PROPERTY_DO_NOT_ECHO')
elif tool == 'make':
    assert args == ['--version'], 'readiness attempted Make setup target'
    print('GNU Make 4.3')
elif tool == 'git':
    if args == ['--version']:
        print('git version 2.39.0')
    elif args == ['rev-parse', '--show-toplevel']:
        print(root)
    elif args == ['rev-parse', 'HEAD', 'HEAD^{tree}']:
        print('a' * 40 + '\\n' + 'b' * 40)
    elif args == ['rev-parse', '--abbrev-ref', 'HEAD']:
        print('fix/105-setup-recovery')
    elif args == ['status', '--porcelain', '--untracked-files=no']:
        pass
    else:
        sys.exit('unexpected git command')
elif tool == 'python':
    assert args[:3] == ['-I', '-B', '-c']
    assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'
    result = dict(executable=str(root / '.venv/bin/python'), version='3.13.12',
                  prefix=str(root / '.venv'), imports={})
    for name in ('simrecon', 'numpy', 'h5py'):
        result['imports'][name] = dict(version='test',
                                      path=str(root / 'src' / name / '__init__.py'))
    if failure == 'python-version':
        result['version'] = '3.12.0'
    if failure == 'prefix':
        result['prefix'] = str(root.parent / 'foreign/.venv')
    if failure == 'import':
        result['imports']['simrecon']['path'] = str(root.parent / 'foreign/simrecon.py')
    if failure == 'dependencies':
        result['error'] = 'ModuleNotFoundError'
    print(json.dumps(result))
else:
    sys.exit('unexpected tool')
"""
    for path in [
        *(tools / name for name in ("git", "make", "uv", "java")),
        root / ".venv/bin/python",
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"#!{sys.executable}\n" + source, encoding="utf-8")
        path.chmod(0o755)
    (root / "caller-data").write_text("preserve me", encoding="utf-8")
    return root, environment


def run_check(
    checkout: tuple[Path, dict[str, str]], *args: str, failure: str = ""
) -> subprocess.CompletedProcess[str]:
    root, environment = checkout
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *args],
        cwd=root,
        env={**environment, "DEV105_FAILURE": failure},
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


def test_ready_reports_identities_limits_and_only_local_probes(
    local_checkout: tuple[Path, dict[str, str]],
) -> None:
    root, environment = local_checkout
    before = {str(path): path.read_bytes() for path in root.rglob("*") if path.is_file()}
    result = run_check(local_checkout)
    assert result.returncode == 0, result.stdout + result.stderr
    for expected in (
        "LOCAL READY (deferred checks remain required)",
        "OS=",
        "architecture=",
        "HEAD/tree:",
        "expected=0.12.19 observed=0.12.19",
        "expected=3.13.12 observed=3.13.12",
        "java.vendor = permitted alternative vendor",
        "java.runtime.version = 21.0.7+6-test",
        "DEFERRED: JDK source-launcher and authenticated reader inputs",
        "NOT CHECKED: connectivity, native stored login, completed sign-in and role capability",
    ):
        assert expected in result.stdout
    assert str(root / "src/simrecon/__init__.py") in result.stdout
    assert "SYNTHETIC_PRIVATE_HOME_DO_NOT_ECHO" not in result.stdout
    assert "SYNTHETIC_SECRET_PROPERTY_DO_NOT_ECHO" not in result.stdout
    assert {str(path): path.read_bytes() for path in root.rglob("*") if path.is_file()} == before
    calls = [
        json.loads(line) for line in Path(environment["DEV105_CALLS"]).read_text().splitlines()
    ]
    assert [tool for tool, _ in calls] == [
        "git",
        "git",
        "git",
        "git",
        "git",
        "make",
        "uv",
        "java",
        "python",
    ]


@pytest.mark.parametrize(
    ("failure", "diagnostic"),
    [
        ("uv-version", "uv: wrong version"),
        ("java-version", "Java: wrong version"),
        ("python-version", "worktree Python: wrong version"),
        ("prefix", "wrong worktree"),
        ("import", "wrong worktree/import"),
        ("dependencies", "uninitialized dependencies"),
        ("nonzero", "nonzero command: status=9"),
        ("timeout", "uv: timeout: exceeded 0.2 seconds"),
    ],
)
def test_unhealthy_local_prerequisites_fail_distinctly(
    local_checkout: tuple[Path, dict[str, str]], failure: str, diagnostic: str
) -> None:
    args = ("--timeout", "0.2") if failure == "timeout" else ()
    result = run_check(local_checkout, *args, failure=failure)
    assert result.returncode == 1, result.stdout + result.stderr
    assert diagnostic in result.stdout
    assert "synthetic local failure" not in result.stdout + result.stderr
    assert "next:" in result.stdout and "LOCAL NOT READY" in result.stdout


@pytest.mark.parametrize("tool", ["git", "make", "uv", "java", "python"])
def test_missing_tool_names_setup_action(
    local_checkout: tuple[Path, dict[str, str]], tool: str
) -> None:
    root, environment = local_checkout
    path = root / ".venv/bin/python" if tool == "python" else Path(environment["PATH"]) / tool
    path.unlink()
    result = run_check(local_checkout)
    assert result.returncode == 1
    assert (
        "missing executable" in result.stdout
        and str(path if tool != "git" and tool != "make" else tool) in result.stdout
    )
    assert "bootstrap.md" in result.stdout


def test_permission_failure_stays_failure(local_checkout: tuple[Path, dict[str, str]]) -> None:
    Path(local_checkout[1]["UV"]).chmod(0o644)
    result = run_check(local_checkout)
    assert result.returncode == 1
    assert "uv: permission failure:" in result.stdout


def test_explicit_paths_override_wrong_environment_tools(
    local_checkout: tuple[Path, dict[str, str]],
) -> None:
    root, environment = local_checkout
    correct_uv, correct_java = environment["UV"], environment["SIMRECON_JAVA"]
    environment.update(UV=str(root / "absent uv"), SIMRECON_JAVA=str(root / "absent java"))
    result = run_check(local_checkout, "--uv", correct_uv, "--java", correct_java)
    assert result.returncode == 0, result.stdout + result.stderr
    environment.pop("UV")
    environment.pop("SIMRECON_JAVA")
    result = run_check(local_checkout)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_unbounded_or_invalid_timeout_rejected(
    local_checkout: tuple[Path, dict[str, str]], timeout: str
) -> None:
    result = run_check(local_checkout, "--timeout", timeout)
    assert result.returncode == 2
    assert "finite and positive" in result.stderr


def test_real_worktree_readiness() -> None:
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert str(ROOT / "src/simrecon/__init__.py") in result.stdout
    assert "LOCAL READY (deferred checks remain required)" in result.stdout
