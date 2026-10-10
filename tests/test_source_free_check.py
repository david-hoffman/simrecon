"""Prove diagnostic locations, messages and statuses survive source suppression."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/source_free_check.py"


def execute(mode: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HARNESS), "--timeout", "30", mode, *arguments],
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )


def test_python_warning_and_exception_preserve_diagnostics_without_source(tmp_path: Path) -> None:
    source = tmp_path / "direct.py"
    source.write_text(
        "import warnings\n"
        "warnings.warn('WARNING_MESSAGE_01', UserWarning)  # SOURCE_ONLY_WARNING_01\n"
        "raise RuntimeError('EXCEPTION_MESSAGE_01')  # SOURCE_ONLY_EXCEPTION_01\n"
    )
    result = execute("python", str(source))
    assert result.returncode == 1
    assert f"{source}:2: UserWarning: WARNING_MESSAGE_01" in result.stderr
    assert f'File "{source}", line 3' in result.stderr
    assert "RuntimeError: EXCEPTION_MESSAGE_01" in result.stderr
    assert "SOURCE_ONLY_" not in result.stdout + result.stderr


def test_python_subprocess_inherits_source_free_diagnostics(tmp_path: Path) -> None:
    child = tmp_path / "child.py"
    child.write_text(
        "import warnings\n"
        "warnings.warn('CHILD_WARNING_02', DeprecationWarning) # SOURCE_ONLY_CHILD_WARNING_02\n"
        "raise ValueError('CHILD_EXCEPTION_02') # SOURCE_ONLY_CHILD_EXCEPTION_02\n"
    )
    parent = tmp_path / "parent.py"
    parent.write_text(
        "import subprocess, sys\n"
        f"result = subprocess.run([sys.executable, {str(child)!r}])\n"
        "print('CHILD_STATUS', result.returncode)\n"
        "sys.exit(result.returncode)\n"
    )
    result = execute("python", str(parent))
    assert result.returncode == 1
    assert "CHILD_STATUS 1" in result.stdout
    assert f"{child}:2: DeprecationWarning: CHILD_WARNING_02" in result.stderr
    assert f'File "{child}", line 3' in result.stderr
    assert "ValueError: CHILD_EXCEPTION_02" in result.stderr
    assert "SOURCE_ONLY_" not in result.stdout + result.stderr


def test_pytest_failure_and_warning_retain_identity_without_source(tmp_path: Path) -> None:
    source = tmp_path / "test_failure.py"
    source.write_text(
        "import warnings\n"
        "def test_diagnostic():\n"
        "    warnings.warn('PYTEST_WARNING_03', UserWarning) # SOURCE_ONLY_PYTEST_WARNING_03\n"
        "    assert False # SOURCE_ONLY_PYTEST_FAILURE_03\n"
    )
    result = execute("pytest", "-q", "--tb=long", "--showlocals", str(source))
    assert result.returncode == 1
    output = result.stdout + result.stderr
    assert f"{source}:4: AssertionError" in output
    assert f"{source}:3: UserWarning: PYTEST_WARNING_03" in output
    assert "1 failed" in output
    assert "SOURCE_ONLY_" not in output


def test_syntax_error_and_exception_chain_do_not_render_source(tmp_path: Path) -> None:
    syntax = tmp_path / "syntax.py"
    syntax.write_text("if SOURCE_ONLY_SYNTAX_04\n")
    result = execute("python", str(syntax))
    assert result.returncode == 1
    assert "SyntaxError: expected ':'" in result.stderr
    assert str(syntax) in result.stderr
    assert "SOURCE_ONLY_" not in result.stderr
    chain = tmp_path / "chain.py"
    chain.write_text(
        "try:\n"
        "    raise ValueError('CAUSE_MESSAGE_04') # SOURCE_ONLY_CAUSE_04\n"
        "except ValueError as error:\n"
        "    raise RuntimeError('OUTER_MESSAGE_04') from error # SOURCE_ONLY_OUTER_04\n"
    )
    result = execute("python", str(chain))
    assert result.returncode == 1
    assert "ValueError: CAUSE_MESSAGE_04" in result.stderr
    assert "RuntimeError: OUTER_MESSAGE_04" in result.stderr
    assert "direct cause" in result.stderr
    assert "SOURCE_ONLY_" not in result.stderr


@pytest.mark.parametrize("flag", ["-I", "-S", "-E"])
def test_environment_disabling_flags_fail_explicitly(flag: str) -> None:
    result = execute("python", flag, "-c", "print('should not run')")
    assert result.returncode == 1
    assert "disable the inherited diagnostic environment" in result.stderr
    assert "should not run" not in result.stdout


def test_timeout_preserves_failure_status() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--timeout",
            "0.1",
            "python",
            "-c",
            "import time; time.sleep(10) # SOURCE_ONLY_TIMEOUT_06",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 1
    assert "TimeoutExpired" in result.stderr
    assert "0.1 seconds" in result.stderr
    assert sys.executable in result.stderr
    assert "python" in result.stderr
    assert "SOURCE_ONLY_" not in result.stdout + result.stderr
    assert "time.sleep" not in result.stdout + result.stderr


@pytest.mark.parametrize("method", ["print_tb", "format_tb", "print_stack", "format_stack"])
def test_standard_traceback_and_stack_rendering_preserve_locations_without_source(
    tmp_path: Path, method: str
) -> None:
    source = tmp_path / "standard_frames.py"
    if method.endswith("tb"):
        call = (
            "traceback.print_tb(error.__traceback__)"
            if method == "print_tb"
            else "print(''.join(traceback.format_tb(error.__traceback__)))"
        )
        source.write_text(
            "import traceback\n"
            "try:\n"
            "    raise ValueError('FRAME_MESSAGE_07') # SOURCE_ONLY_FRAME_07\n"
            "except ValueError as error:\n"
            f"    {call}\n"
            "    print(type(error).__name__, str(error))\n"
        )
        expected_line = 3
    else:
        call = (
            "traceback.print_stack()"
            if method == "print_stack"
            else "print(''.join(traceback.format_stack()))"
        )
        source.write_text(f"import traceback\n{call} # SOURCE_ONLY_STACK_07\n")
        expected_line = 2
    result = execute("python", str(source))
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert f'File "{source}", line {expected_line}' in output
    assert "SOURCE_ONLY_" not in output
    if method.endswith("tb"):
        assert "ValueError FRAME_MESSAGE_07" in output


@pytest.mark.parametrize("legacy", [False, True])
def test_standard_exception_only_syntax_error_retains_diagnostics_without_source(
    tmp_path: Path, legacy: bool
) -> None:
    source = tmp_path / "exception_only.py"
    arguments = "type(error), error" if legacy else "error"
    source.write_text(
        "import traceback\n"
        "error = SyntaxError('SYNTAX_MESSAGE_08', "
        "('syntax-location.py', 7, 4, 'if SOURCE_ONLY_EXCEPTION_ONLY_08'))\n"
        f"print(''.join(traceback.format_exception_only({arguments})))\n"
    )
    result = execute("python", str(source))
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert 'File "syntax-location.py", line 7' in output
    assert "SyntaxError: SYNTAX_MESSAGE_08" in output
    assert "SOURCE_ONLY_" not in output


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf"])
def test_nonpositive_or_nonfinite_timeout_fails_before_command(timeout: str) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--timeout",
            timeout,
            "python",
            "-c",
            "print('should not run')",
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 2
    assert "--timeout must be finite and positive" in result.stderr
    assert "should not run" not in result.stdout


def test_standard_caught_traceback_and_pytest_thread_warning_are_source_free(
    tmp_path: Path,
) -> None:
    source = tmp_path / "caught.py"
    source.write_text(
        "import traceback\n"
        "try:\n"
        "    raise ValueError('CAUGHT_MESSAGE_05') # SOURCE_ONLY_CAUGHT_05\n"
        "except ValueError:\n"
        "    traceback.print_exc()\n"
    )
    result = execute("python", str(source))
    assert result.returncode == 0
    assert "ValueError: CAUGHT_MESSAGE_05" in result.stderr
    assert f'File "{source}", line 3' in result.stderr
    assert "SOURCE_ONLY_" not in result.stderr
    source = tmp_path / "test_thread.py"
    source.write_text(
        "import threading\n"
        "def failure():\n"
        "    raise ValueError('THREAD_MESSAGE_05') # SOURCE_ONLY_THREAD_05\n"
        "def test_thread():\n"
        "    thread = threading.Thread(target=failure)\n"
        "    thread.start()\n"
        "    thread.join()\n"
    )
    result = execute("pytest", "-q", str(source))
    output = result.stdout + result.stderr
    assert result.returncode == 0
    assert "PytestUnhandledThreadExceptionWarning" in output
    assert "ValueError: THREAD_MESSAGE_05" in output
    assert str(source) in output
    assert "SOURCE_ONLY_" not in output


def test_existing_pythonpath_remains_available(tmp_path: Path) -> None:
    (tmp_path / "controlled_module.py").write_text("value = 'PYTHONPATH_PRESERVED'\n")
    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "python",
            "-c",
            "import controlled_module; print(controlled_module.value)",
        ],
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0
    assert "PYTHONPATH_PRESERVED" in result.stdout
