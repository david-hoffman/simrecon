"""Blind public-contract supplements; these do not recreate test-first evidence."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from shared_node_baseline_infrastructure_supplement_fixture import (
    PHASES,
    ROOT,
    attempted_phases,
    digest,
    protected_bytes,
    receipt_at,
    run_public,
    verifier_repo,
    verify,
    write_program,
)


@pytest.mark.parametrize("formatter", ("traceback-exception",))
def test_standard_exception_formatters_suppress_source_and_locals(
    tmp_path: Path, formatter: str
) -> None:
    probe = tmp_path / "formatter.py"
    write_program(
        probe,
        f"""
        import traceback
        def trigger():
            private_local = "A07_LOCAL_SENTINEL"
            raise ValueError("A07 visible value")  # A07_SOURCE_SENTINEL
        try:
            trigger()
        except ValueError as error:
            if {formatter!r} == "format_exception":
                print("".join(traceback.format_exception(error)))
            elif {formatter!r} == "traceback-exception":
                formatted = traceback.TracebackException.from_exception(error, capture_locals=True)
                print("".join(formatted.format()))
            else:
                traceback.print_exception(error)
            assert str(error) == "A07 visible value"
        """,
    )
    result = run_public(tmp_path, str(probe))
    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    assert "ValueError: A07 visible value" in output
    assert str(probe) in output
    assert "line " in output
    assert "A07_SOURCE_SENTINEL" not in output
    assert "A07_LOCAL_SENTINEL" not in output


@pytest.mark.parametrize("structure", ("cause-cycle", "context-cycle", "shared-group"))
def test_finite_exception_graphs_preserve_messages_without_recursion_or_source(
    tmp_path: Path, structure: str
) -> None:
    probe = tmp_path / "graphs.py"
    write_program(
        probe,
        f"""
        import traceback
        first = ValueError("A07 first")
        second = TypeError("A07 second")
        if {structure!r} == "cause-cycle":
            first.__cause__ = second
            second.__cause__ = first
            error = first
        elif {structure!r} == "context-cycle":
            first.__context__ = second
            second.__context__ = first
            error = first
        else:
            error = ExceptionGroup("A07 shared", [first, first, second])
        print("".join(traceback.format_exception(error)))
        print("".join(traceback.TracebackException.from_exception(error).format(chain=False)))
        assert str(first) == "A07 first"
        assert str(second) == "A07 second"
        if {structure!r} == "cause-cycle":
            assert first.__cause__ is second and second.__cause__ is first
        elif {structure!r} == "context-cycle":
            assert first.__context__ is second and second.__context__ is first
        else:
            assert error.exceptions[0] is error.exceptions[1]
        """,
    )
    result = run_public(tmp_path, str(probe), timeout=10)
    assert result.returncode == 0, result.stderr
    assert "ValueError: A07 first" in result.stdout
    assert "TypeError: A07 second" in result.stdout
    assert "RecursionError" not in result.stdout + result.stderr


def test_supported_none_threading_hook_and_exception_formatting(tmp_path: Path) -> None:
    probe = tmp_path / "none_inputs.py"
    write_program(
        probe,
        """
        import threading
        import traceback
        value = threading.ExceptHookArgs((ValueError, None, None, None))
        threading.excepthook(value)
        assert value.exc_type is ValueError
        assert value.exc_value is None
        assert value.exc_traceback is None
        assert value.thread is None
        print("".join(traceback.format_exception(None)))
        print("".join(traceback.format_exception_only(None, None)))
        """,
    )
    result = run_public(tmp_path, str(probe))
    assert result.returncode == 0, result.stderr
    assert "NoneType: None" in result.stdout
    # The public grammar promises accepted None fields, not exact hook prose.


@pytest.mark.parametrize("formatter", ("stack-summary",))
def test_real_standard_stack_locations_omit_source_and_captured_locals(
    tmp_path: Path, formatter: str
) -> None:
    probe = tmp_path / "standard_stacks.py"
    write_program(
        probe,
        f"""
        import sys
        import traceback
        def caller():
            private_local = "A07_STACK_LOCAL_SENTINEL"
            if {formatter!r} == "format-stack":
                return "".join(traceback.format_stack())  # A07_STACK_SOURCE_SENTINEL
            if {formatter!r} == "stack-summary":
                summary = traceback.StackSummary.extract(
                    traceback.walk_stack(sys._getframe()), capture_locals=True)
                return "".join(summary.format())  # A07_STACK_SOURCE_SENTINEL
            try:
                raise LookupError("A07 location error")  # A07_STACK_SOURCE_SENTINEL
            except LookupError as error:
                return "".join(traceback.format_tb(error.__traceback__))
        print(caller())
        """,
    )
    result = run_public(tmp_path, str(probe))
    assert result.returncode == 0, result.stderr
    assert str(probe) in result.stdout
    assert "line " in result.stdout
    assert "caller" in result.stdout
    assert "A07_STACK_SOURCE_SENTINEL" not in result.stdout + result.stderr
    assert "A07_STACK_LOCAL_SENTINEL" not in result.stdout + result.stderr


def test_public_exception_chains_groups_and_syntax_fields_remain_intact(tmp_path: Path) -> None:
    probe = tmp_path / "syntax_chains.py"
    write_program(
        probe,
        """
        import traceback
        import warnings
        syntax = SyntaxError("A07 syntax message", ("A07_syntax.py", 7, 3,
                                                  "A07_SYNTAX_SOURCE_SENTINEL", 7, 8))
        print("".join(traceback.format_exception_only(syntax)))
        assert syntax.filename == "A07_syntax.py"
        assert syntax.lineno == 7 and syntax.offset == 3
        assert syntax.end_lineno == 7 and syntax.end_offset == 8
        assert syntax.text == "A07_SYNTAX_SOURCE_SENTINEL"
        try:
            try:
                raise ValueError("A07 visible cause")  # A07_CHAIN_SOURCE_SENTINEL
            except ValueError as cause:
                raise RuntimeError("A07 visible outer") from cause  # A07_CHAIN_SOURCE_SENTINEL
        except RuntimeError as outer:
            group = ExceptionGroup("A07 visible group", [outer, syntax])
            print("".join(traceback.format_exception(group)))
            assert isinstance(outer.__cause__, ValueError)
        warnings.warn("A07 visible warning", UserWarning)  # A07_WARNING_SOURCE_SENTINEL
        """,
    )
    result = run_public(tmp_path, str(probe))
    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    for message in (
        "SyntaxError: A07 syntax message",
        "A07_syntax.py",
        "line 7",
        "ValueError: A07 visible cause",
        "RuntimeError: A07 visible outer",
        "ExceptionGroup: A07 visible group",
        "UserWarning: A07 visible warning",
    ):
        assert message in output
    for marker in ("SYNTAX", "CHAIN", "WARNING"):
        assert "A07_" + marker + "_SOURCE_SENTINEL" not in output


@pytest.mark.parametrize("exception", ("timeout", "child-status"))
def test_string_command_identity_unavailable_preserves_original_fields(
    tmp_path: Path, exception: str
) -> None:
    probe = tmp_path / "subprocess_fields.py"
    write_program(
        probe,
        f"""
        import subprocess
        import traceback
        command = "A07_COMMAND_ARGUMENT_SENTINEL"
        if {exception!r} == "timeout":
            error = subprocess.TimeoutExpired(
                command, 2.5, output=b"public-output", stderr=b"public-stderr")
            assert error.timeout == 2.5
        else:
            error = subprocess.CalledProcessError(
                23, command, output=b"public-output", stderr=b"public-stderr")
            assert error.returncode == 23
        print(str(error))
        print("".join(traceback.format_exception(error)))
        assert error.cmd == command
        assert error.output == b"public-output"
        assert error.stderr == b"public-stderr"
        """,
    )
    result = run_public(tmp_path, str(probe))
    assert result.returncode == 0, result.stderr
    assert "A07_COMMAND_ARGUMENT_SENTINEL" not in result.stdout + result.stderr
    identity = result.stdout.lower()
    assert any(label in identity for label in ("unavailable", "not recorded", "not available"))
    assert ("2.5" if exception == "timeout" else "23") in result.stdout


@pytest.mark.parametrize("change", ("", "directory-alias", "directory-cycle", "fifo-neighbor"))
def test_verifier_safe_custom_untracked_receipt_and_harmless_neighbors(
    tmp_path: Path, change: str
) -> None:
    repo = tmp_path / "repository"
    make = verifier_repo(repo, change=change)
    protected = protected_bytes(repo)
    receipt_name = "ordinary-receipt.json"
    result = verify(repo, make, receipt=receipt_name, change=change)
    assert result.returncode == 0, result.stderr
    receipt = receipt_at(repo, receipt_name)
    assert receipt["result"] == "passed"
    assert receipt["problems"] == []
    assert receipt_name in receipt["after"]["untracked"]
    assert receipt_name not in receipt["before"]["untracked"]
    actual = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    assert sorted(receipt["after"]["untracked"]) == sorted(
        name for name in actual.stdout.split("\0") if name
    )
    assert receipt["before"]["manifest"] == receipt["after"]["manifest"]
    assert protected_bytes(repo) == protected
    assert attempted_phases(repo) == list(PHASES)
    for phase in receipt["phases"]:
        assert phase["returncode"] == 0
        assert "authentic A07 phase output: " + phase["name"] in (repo / phase["log"]).read_text()
    coverage = receipt["coverage"]
    assert (repo / coverage["reports"]["json"]).is_file()
    assert (repo / coverage["reports"]["html"]).is_file()
    for metrics in coverage["files"].values():
        assert metrics["statements"]["covered"] == metrics["statements"]["total"]
        assert metrics["branches"]["covered"] == metrics["branches"]["total"]
    artifact = receipt["artifact"]
    assert digest(repo / artifact["path"]) == artifact["sha256"]


def test_verifier_failed_phase_custom_receipt_refreshes_identity_without_losing_status(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repository"
    make = verifier_repo(repo, fail="lint")
    protected = protected_bytes(repo)
    receipt_name = "ordinary-failed-receipt.json"
    result = verify(repo, make, receipt=receipt_name, fail="lint")
    assert result.returncode == 23, result.stderr
    receipt = receipt_at(repo, receipt_name)
    assert receipt["result"] == "failed"
    assert receipt_name in receipt["after"]["untracked"]
    assert receipt_name not in receipt["before"]["untracked"]
    actual = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    assert sorted(receipt["after"]["untracked"]) == sorted(
        name for name in actual.stdout.split("\0") if name
    )
    assert attempted_phases(repo) == list(PHASES[:3])
    assert receipt["phases"][-1]["returncode"] == 23
    assert protected_bytes(repo) == protected


def test_standard_runpy_main_is_a_real_script_caller_not_a_new_import_api(
    tmp_path: Path,
) -> None:
    # runpy is a conventional CLI-driver interface. Usage is observable; no
    # promise is asserted about quiet imports, globals or private lifecycle.
    result = run_public(
        tmp_path,
        "-c",
        "import runpy, sys; path = sys.argv[1]; sys.argv = ['verify.py', '--help']; "
        "runpy.run_path(path, run_name='__main__')",
        str(ROOT / "scripts/verify.py"),
    )
    assert result.returncode == 0, result.stderr
    assert "--receipt" in result.stdout
    assert "--measurements-required" in result.stdout
