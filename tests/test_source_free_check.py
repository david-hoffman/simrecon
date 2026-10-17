"""Prove diagnostic locations, messages and statuses survive source suppression."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/source_free_check.py"


def execute(
    mode: str, *arguments: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HARNESS), "--timeout", "30", mode, *arguments],
        cwd=cwd,
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


@pytest.mark.parametrize("flag", ["-I", "-S", "-E", "-ES", "-IS"])
def test_environment_disabling_flags_fail_explicitly(flag: str) -> None:
    result = execute("python", flag, "-c", "print('should not run')")
    assert result.returncode == 1
    assert "disable the inherited diagnostic environment" in result.stderr
    assert "should not run" not in result.stdout


@pytest.mark.parametrize("mode", ["command", "module", "script"])
def test_literal_disabling_flags_after_program_boundary_are_preserved(
    tmp_path: Path, mode: str
) -> None:
    source = "import sys; print('PROGRAM_ARGUMENTS', sys.argv[1:])"
    program = tmp_path / "literal_arguments.py"
    program.write_text(source + "\n")
    arguments = (
        ["-c", source]
        if mode == "command"
        else ["-m", "literal_arguments"]
        if mode == "module"
        else [str(program)]
    )
    result = subprocess.run(
        [sys.executable, str(HARNESS), "python", *arguments, "-I", "-S", "-E"],
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "PROGRAM_ARGUMENTS ['-I', '-S', '-E']" in result.stdout


def test_interpreter_option_values_and_attached_command_preserve_program_arguments() -> None:
    result = execute(
        "python",
        "-W",
        "ignore",
        "-X",
        "utf8",
        "--check-hash-based-pycs",
        "default",
        "-cimport sys; print('ATTACHED_ARGUMENTS', sys.argv[1:])",
        "-S",
    )
    assert result.returncode == 0, result.stderr
    assert "ATTACHED_ARGUMENTS ['-S']" in result.stdout


def subprocess_statement(kind: str) -> str:
    inner = (
        "import time; time.sleep(2) # SOURCE_ONLY_NESTED_TIMEOUT_11"
        if kind == "timeout"
        else "raise SystemExit(7) # SOURCE_ONLY_NESTED_CALLED_11"
    )
    option = "timeout=0.05" if kind == "timeout" else "check=True"
    return f"subprocess.run([sys.executable, '-c', {inner!r}], {option})"


def assert_subprocess_diagnostics(output: str, kind: str) -> None:
    assert sys.executable in output
    assert "SOURCE_ONLY_" not in output
    assert "time.sleep" not in output
    assert "raise SystemExit" not in output
    if kind == "timeout":
        assert "TimeoutExpired" in output
        assert "0.05 seconds" in output
    else:
        assert "CalledProcessError" in output
        assert "exit status 7" in output


def assert_pytest_failure_identity(output: str, source: Path, cwd: Path) -> None:
    for line in output.splitlines():
        if not line.startswith("FAILED "):
            continue
        nodeid = line.removeprefix("FAILED ")
        filename, separator, test_name = nodeid.partition("::")
        test_name = test_name.split(" - ", 1)[0]
        if (
            separator
            and test_name == "test_subprocess_failure"
            and (cwd / filename).resolve() == source.resolve()
        ):
            return
    raise AssertionError(f"No pytest failure identity resolves to {source}")


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("directory", ["inputs", "inputs - legitimate"])
@pytest.mark.parametrize("summary", ["", " - CalledProcessError"])
def test_pytest_failure_identity_accepts_full_relative_and_absolute_paths(
    tmp_path: Path, absolute: bool, directory: str, summary: str
) -> None:
    source = tmp_path / directory / "test_nested.py"
    cwd = tmp_path / "invocation"
    filename = str(source) if absolute else os.path.relpath(source, cwd)
    output = f"FAILED {filename}::test_subprocess_failure{summary}\n"
    assert_pytest_failure_identity(output, source, cwd)


@pytest.mark.parametrize("absolute", [False, True])
@pytest.mark.parametrize("directory", ["inputs", "inputs - legitimate"])
def test_pytest_failure_identity_rejects_a_different_path_with_the_same_basename(
    tmp_path: Path, absolute: bool, directory: str
) -> None:
    source = tmp_path / directory / "test_nested.py"
    wrong_source = tmp_path / "other" / source.name
    cwd = tmp_path / "invocation"
    filename = str(wrong_source) if absolute else os.path.relpath(wrong_source, cwd)
    output = f"FAILED {filename}::test_subprocess_failure\n"
    with pytest.raises(AssertionError, match="No pytest failure identity resolves to"):
        assert_pytest_failure_identity(output, source, cwd)


@pytest.mark.parametrize("layout", ["source-parent", "sibling-directory"])
@pytest.mark.parametrize("directory", ["inputs", "inputs - legitimate"])
def test_pytest_subprocess_failure_preserves_source_identity_across_cwd_layouts(
    tmp_path: Path, layout: str, directory: str
) -> None:
    source = tmp_path / directory / "test_nested.py"
    source.parent.mkdir()
    cwd = source.parent if layout == "source-parent" else tmp_path / "invocation" / "nested"
    cwd.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "import subprocess, sys\n"
        "def test_subprocess_failure():\n"
        f"    {subprocess_statement('called')}\n"
    )
    result = execute("pytest", "-q", str(source), cwd=cwd)
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert_subprocess_diagnostics(output, "called")
    assert_pytest_failure_identity(output, source, cwd)
    assert "1 failed" in output


@pytest.mark.parametrize("kind", ["timeout", "called"])
@pytest.mark.parametrize("mode", ["direct", "print-exc", "exception-only", "snapshot"])
def test_nested_subprocess_exception_renderers_suppress_inline_source(
    tmp_path: Path, kind: str, mode: str
) -> None:
    statement = subprocess_statement(kind)
    source = tmp_path / "nested_exception.py"
    header = "import subprocess, sys, traceback\n"
    if mode == "direct":
        source.write_text(header + statement + "\n")
    else:
        renderer = {
            "print-exc": "traceback.print_exc()",
            "exception-only": "print(''.join(traceback.format_exception_only(error)))",
            "snapshot": (
                "print(''.join(traceback.TracebackException.from_exception("
                "error, capture_locals=True).format()))"
            ),
        }[mode]
        source.write_text(
            header + "try:\n    " + statement + "\nexcept Exception as error:\n"
            "    assert error.cmd[1] == '-c'\n"
            "    assert 'SOURCE_ONLY_' in error.cmd[2]\n"
            "    assert getattr(error, 'returncode', 7) == 7\n"
            "    assert getattr(error, 'timeout', 0.05) == 0.05\n"
            f"    {renderer}\n"
        )
    result = execute("python", str(source))
    assert result.returncode == (1 if mode == "direct" else 0)
    output = result.stdout + result.stderr
    assert_subprocess_diagnostics(output, kind)
    if mode != "exception-only":
        assert f'File "{source}", line' in output


@pytest.mark.parametrize("mode", ["chain", "group", "thread", "pytest"])
def test_nested_subprocess_errors_share_safe_chain_group_thread_and_pytest_diagnostics(
    tmp_path: Path, mode: str
) -> None:
    header = "import subprocess, sys, threading\n"
    timeout = subprocess_statement("timeout")
    called = subprocess_statement("called")
    if mode == "chain":
        body = (
            f"try:\n    {timeout}\nexcept subprocess.TimeoutExpired as first:\n"
            f"    try:\n        {called}\n"
            "    except subprocess.CalledProcessError as second:\n"
            "        raise second from first\n"
        )
    elif mode == "group":
        body = (
            "errors = []\n"
            f"try:\n    {timeout}\nexcept subprocess.TimeoutExpired as error:\n"
            "    errors.append(error)\n"
            f"try:\n    {called}\nexcept subprocess.CalledProcessError as error:\n"
            "    errors.append(error)\n"
            "raise ExceptionGroup('GROUP_MESSAGE_11', errors)\n"
        )
    elif mode == "thread":
        body = (
            f"def failure():\n    {called}\n"
            "thread = threading.Thread(target=failure)\nthread.start()\nthread.join()\n"
        )
    else:
        body = f"def test_subprocess_failure():\n    {called}\n"
    source = tmp_path / ("test_nested.py" if mode == "pytest" else "nested_shared.py")
    source.write_text(header + body)
    result = (
        execute("pytest", "-q", str(source)) if mode == "pytest" else execute("python", str(source))
    )
    assert result.returncode == (0 if mode == "thread" else 1)
    output = result.stdout + result.stderr
    assert_subprocess_diagnostics(output, "called")
    if mode == "pytest":
        assert_pytest_failure_identity(output, source, Path.cwd())
    else:
        assert str(source) in output
    if mode in ("chain", "group"):
        assert_subprocess_diagnostics(output, "timeout")
    if mode == "chain":
        assert "direct cause" in output
    if mode == "group":
        assert "GROUP_MESSAGE_11" in output
    if mode == "pytest":
        assert "1 failed" in output


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


@pytest.mark.parametrize("entry", ["module", "initial_conftest", "nested_conftest"])
@pytest.mark.parametrize("failure", ["syntax", "import"])
def test_pytest_collection_errors_preserve_diagnostics_without_source(
    tmp_path: Path, entry: str, failure: str
) -> None:
    directory = tmp_path / "nested" if entry == "nested_conftest" else tmp_path
    directory.mkdir(exist_ok=True)
    source = directory / ("test_collection.py" if entry == "module" else "conftest.py")
    if failure == "syntax":
        source.write_text("if SOURCE_ONLY_COLLECTION_SYNTAX\n")
        expected = ["SyntaxError: expected ':'", f'File "{source}", line 1']
    else:
        source.write_text(
            "try:\n"
            "    raise ValueError('COLLECTION_CAUSE') # SOURCE_ONLY_COLLECTION_CAUSE\n"
            "except ValueError as error:\n"
            "    raise ImportError('COLLECTION_IMPORT') from error "
            "# SOURCE_ONLY_COLLECTION_IMPORT\n"
        )
        expected = [
            "ValueError: COLLECTION_CAUSE",
            "ImportError: COLLECTION_IMPORT",
            "direct cause",
            f'File "{source}", line 2',
            f'File "{source}", line 4',
        ]
    if entry != "module":
        (directory / "test_inert.py").write_text("def test_inert():\n    pass\n")
    result = execute("pytest", "-q", str(tmp_path), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == (4 if entry == "initial_conftest" else 2), output
    for diagnostic in expected:
        assert diagnostic in output
    assert "SOURCE_ONLY_" not in output
    assert "importlib.import_module(" not in output
    assert "return _bootstrap." not in output
    assert "mod = import_path(" not in output


@pytest.mark.parametrize("explicit_cause", [False, True])
def test_pytest_collection_runtime_chain_preserves_diagnostics_without_source(
    tmp_path: Path, explicit_cause: bool
) -> None:
    source = tmp_path / "test_chain.py"
    suffix = " from error" if explicit_cause else ""
    source.write_text(
        "try:\n"
        "    raise ValueError('COLLECTION_RUNTIME_CAUSE') # SOURCE_ONLY_RUNTIME_CAUSE\n"
        "except ValueError as error:\n"
        f"    raise RuntimeError('COLLECTION_RUNTIME_OUTER'){suffix} "
        "# SOURCE_ONLY_RUNTIME_OUTER\n"
    )
    result = execute("pytest", "-q", str(source), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "ValueError: COLLECTION_RUNTIME_CAUSE" in output
    assert "RuntimeError: COLLECTION_RUNTIME_OUTER" in output
    assert ("direct cause" if explicit_cause else "During handling") in output
    assert f'File "{source}", line 2' in output
    assert f'File "{source}", line 4' in output
    assert "SOURCE_ONLY_" not in output


def test_pytest_setup_import_failure_preserves_status_and_location(tmp_path: Path) -> None:
    source = tmp_path / "test_setup.py"
    source.write_text(
        "def setup_module():\n"
        "    raise ImportError('SETUP_IMPORT_MESSAGE') # SOURCE_ONLY_SETUP_IMPORT\n"
        "def test_inert():\n"
        "    pass\n"
    )
    result = execute("pytest", "-q", str(source), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "ImportError: SETUP_IMPORT_MESSAGE" in output
    assert f"{source.name}::test_inert" in output
    assert "1 error" in output
    assert "SOURCE_ONLY_" not in output


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_pytest_information_options_survive_broken_initial_conftest(
    tmp_path: Path, option: str
) -> None:
    (tmp_path / "conftest.py").write_text(
        "raise ImportError('BROKEN_CONFTEST') # SOURCE_ONLY_INFORMATION_CONFTEST\n"
    )
    result = execute("pytest", option, str(tmp_path), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert ("usage:" if option == "--help" else "pytest ") in output
    assert "SOURCE_ONLY_" not in output


def test_python_pytest_inherits_collection_renderer_and_preserves_existing_plugins(
    tmp_path: Path,
) -> None:
    (tmp_path / "existing_plugin.py").write_text(
        "def pytest_sessionfinish():\n    print('EXISTING_PLUGIN_ACTIVE SOURCE_ONLY_USER_OUTPUT')\n"
    )
    source = tmp_path / "test_import.py"
    source.write_text("raise ImportError('INHERITED_IMPORT') # SOURCE_ONLY_IMPORT_CODE\n")
    result = subprocess.run(
        [sys.executable, str(HARNESS), "python", "-m", "pytest", "-q", str(source)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path), "PYTEST_PLUGINS": "existing_plugin"},
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "ImportError: INHERITED_IMPORT" in output
    assert f'File "{source}", line 1' in output
    assert "EXISTING_PLUGIN_ACTIVE SOURCE_ONLY_USER_OUTPUT" in output
    assert "SOURCE_ONLY_IMPORT_CODE" not in output


def test_pytest_collection_import_mismatch_retains_its_specific_diagnostic(tmp_path: Path) -> None:
    for name in ("first", "second"):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "test_duplicate.py").write_text("def test_inert():\n    pass\n")
    result = execute("pytest", "-q", str(tmp_path), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "import file mismatch" in output
    assert "ImportPathMismatchError" in output
    assert str(tmp_path / "first" / "test_duplicate.py") in output
    assert str(tmp_path / "second" / "test_duplicate.py") in output
    assert "unique basename" in output
    assert "importlib.import_module(" not in output


@pytest.mark.parametrize("cause", ["syntax", "import"])
def test_pytest_caller_collecterror_retains_message_category_and_cause(
    tmp_path: Path, cause: str
) -> None:
    source = tmp_path / "test_custom.py"
    source.write_text("def test_inert():\n    pass\n")
    statement = (
        'compile("if SOURCE_ONLY_CALLER_INPUT\\n", "caller-input.txt", "exec")'
        if cause == "syntax"
        else "raise ImportError('CALLER_IMPORT_CAUSE') # SOURCE_ONLY_CALLER_IMPORT"
    )
    conftest = tmp_path / "conftest.py"
    conftest.write_text(
        "import pytest\n"
        "class DiagnosticCollector(pytest.Module):\n"
        "    def collect(self):\n"
        "        try:\n"
        f"            {statement}\n"
        "        except (SyntaxError, ImportError) as error:\n"
        "            raise self.CollectError('CALLER_CONTEXT: invalid configuration') from error\n"
        "@pytest.hookimpl(tryfirst=True)\n"
        "def pytest_pycollect_makemodule(module_path, parent):\n"
        "    return DiagnosticCollector.from_parent(parent, path=module_path)\n"
    )
    result = execute("pytest", "-q", str(source), cwd=tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode == 2, output
    assert "CollectError: CALLER_CONTEXT: invalid configuration" in output
    assert f'File "{conftest}", line 7' in output
    assert "direct cause" in output
    if cause == "syntax":
        assert "SyntaxError: expected ':'" in output
        assert 'File "caller-input.txt", line 1' in output
    else:
        assert "ImportError: CALLER_IMPORT_CAUSE" in output
        assert f'File "{conftest}", line 5' in output
    assert "SOURCE_ONLY_" not in output
