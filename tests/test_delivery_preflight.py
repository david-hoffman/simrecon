"""Exercise the public Make preflight with controlled prerequisite environments."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def controlled_uv(tmp_path: Path) -> tuple[Path, Path, Path]:
    isolated = tmp_path / "isolated"
    venv.EnvBuilder(with_pip=False, symlinks=True).create(isolated)
    isolated_python = isolated / "bin/python"
    site = Path(
        subprocess.check_output(
            [str(isolated_python), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
            text=True,
            timeout=30,
        ).strip()
    )
    (site / "hatchling").mkdir()
    (site / "hatchling/__init__.py").write_text("", encoding="utf-8")
    metadata = site / "hatchling-1.32.4.dist-info"
    metadata.mkdir()
    (metadata / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: hatchling\nVersion: 1.32.4\n", encoding="utf-8"
    )
    wrapper = tmp_path / "controlled_uv.py"
    wrapper.write_text(
        textwrap.dedent(
            """\
            import json
            import os
            from pathlib import Path
            import subprocess
            import sys

            args = sys.argv[1:]
            with Path(os.environ['ENV1_CALLS']).open('a') as stream:
                stream.write(json.dumps(args) + '\\n')
            failure = os.environ['ENV1_FAILURE']
            if args == ['sync', '--locked', '--all-groups']:
                if failure == 'sync':
                    sys.exit('controlled locked sync failure')
                sys.exit(0)
            if args == [
                'run', '--locked', '--no-sync', 'python', 'scripts/prepare_imagej_reader.py'
            ]:
                if failure == 'reader':
                    sys.exit('controlled reader preparation failure')
                print('preflight: reader inputs authenticated (controlled fixture)')
                sys.exit(0)
            if args == ['--version']:
                print('uv controlled test executable')
                sys.exit(0)
            if args[:5] == ['run', '--locked', '--no-sync', 'python', '-c']:
                prefix = {
                    'import': "import sys; sys.modules['numpy'] = None; ",
                    'interpreter': "import sys; sys.version_info = (3, 12, 0); ",
                    'environment': "import sys; sys.prefix = '/wrong/worktree'; ",
                    'package-path': "import simrecon; simrecon.__file__ = '/wrong/simrecon.py'; ",
                }.get(failure, '')
                sys.exit(subprocess.call([sys.executable, '-c', prefix + args[5]]))
            if args[:6] == ['run', '--no-project', '--with', 'hatchling==1.32.4', 'python', '-c']:
                if failure == 'isolated-creation':
                    sys.exit('controlled isolated environment creation failure')
                prefix = {
                    'hatchling-import': "import sys; sys.modules['hatchling'] = None; ",
                    'hatchling-version': (
                        "import importlib.metadata; "
                        "importlib.metadata.version = lambda name: '0.0'; "
                    ),
                    'not-isolated': (
                        "import sys; from pathlib import Path; "
                        "sys.prefix = str(Path.cwd() / '.venv'); "
                    ),
                }.get(failure, '')
                command = [os.environ['ENV1_ISOLATED_PYTHON'], '-c', prefix + args[6]]
                sys.exit(subprocess.call(command))
            sys.exit('unexpected uv command: ' + repr(args))
            """
        ),
        encoding="utf-8",
    )
    return wrapper, tmp_path / "calls.jsonl", isolated_python


def _git_state() -> tuple[str, str]:
    status, diff = (
        subprocess.check_output(["git", *args], cwd=ROOT, text=True, timeout=30)
        for args in (("status", "--porcelain"), ("diff", "--binary"))
    )
    return status, diff


def _preflight(
    controlled_uv: tuple[Path, Path, Path], failure: str
) -> tuple[subprocess.CompletedProcess[str], list[list[str]]]:
    wrapper, calls, isolated_python = controlled_uv
    before = _git_state()
    result = subprocess.run(
        ["make", "--no-print-directory", "preflight", f"UV={sys.executable} {wrapper}"],
        cwd=ROOT,
        env={
            **os.environ,
            "ENV1_CALLS": str(calls),
            "ENV1_FAILURE": failure,
            "ENV1_ISOLATED_PYTHON": str(isolated_python),
        },
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert _git_state() == before
    return result, [json.loads(line) for line in calls.read_text().splitlines()]


def _assert_order(calls: list[list[str]], count: int) -> None:
    expected = [
        ["sync", "--locked", "--all-groups"],
        ["run", "--locked", "--no-sync", "python", "scripts/prepare_imagej_reader.py"],
        ["--version"],
        ["run", "--locked", "--no-sync", "python", "-c"],
        ["run", "--no-project", "--with", "hatchling==1.32.4", "python", "-c"],
    ]
    assert len(calls) == count
    for actual, prefix in zip(calls, expected, strict=False):
        assert actual[: len(prefix)] == prefix
        assert len(actual) == len(prefix) + (1 if prefix[-1] == "-c" else 0)


def test_preflight_success_reports_actual_identity_and_order(
    controlled_uv: tuple[Path, Path, Path],
) -> None:
    result, calls = _preflight(controlled_uv, "")
    assert result.returncode == 0, result.stdout + result.stderr
    _assert_order(calls, 5)
    # Inspect emitted health output, rather than Make's echoed Python command.
    lines = result.stdout.splitlines()
    assert "preflight: reader inputs authenticated (controlled fixture)" in lines
    assert any(line.startswith("preflight: python ") and sys.executable in line for line in lines)
    imports = next(line for line in lines if line.startswith("preflight: imports "))
    for name in ("simrecon", "numpy", "h5py"):
        assert name in imports
    assert str(ROOT / "src/simrecon/__init__.py") in imports
    isolated_python = controlled_uv[2]
    assert any(
        line.startswith("preflight: isolated python ") and str(isolated_python) in line
        for line in lines
    )
    assert any(line.startswith("preflight: hatchling 1.32.4 ") for line in lines)


@pytest.mark.parametrize(
    ("failure", "count", "diagnostic"),
    [
        ("sync", 1, "controlled locked sync failure"),
        ("reader", 2, "controlled reader preparation failure"),
        ("import", 4, "import of numpy halted"),
        ("interpreter", 4, "expected Python 3.13.12"),
        ("environment", 4, "expected current-worktree .venv"),
        ("package-path", 4, "simrecon import is outside current-worktree"),
    ],
)
def test_preflight_sync_or_health_failure_stops_without_retry(
    controlled_uv: tuple[Path, Path, Path], failure: str, count: int, diagnostic: str
) -> None:
    result, calls = _preflight(controlled_uv, failure)
    assert result.returncode != 0
    assert diagnostic in result.stderr
    _assert_order(calls, count)
    assert not any(
        line.startswith("preflight: isolated python ") for line in result.stdout.splitlines()
    )


@pytest.mark.parametrize(
    ("failure", "diagnostic"),
    [
        ("isolated-creation", "controlled isolated environment creation failure"),
        ("hatchling-import", "import of hatchling halted"),
        ("hatchling-version", "expected hatchling 1.32.4"),
        ("not-isolated", "build dependency environment is not isolated"),
    ],
)
def test_preflight_isolated_prerequisite_failure_is_reported_without_retry(
    controlled_uv: tuple[Path, Path, Path], failure: str, diagnostic: str
) -> None:
    result, calls = _preflight(controlled_uv, failure)
    assert result.returncode != 0
    assert diagnostic in result.stderr
    _assert_order(calls, 5)
