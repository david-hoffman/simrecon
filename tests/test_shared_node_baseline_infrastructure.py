"""Blind public-entry preservation tests for BASELINE-INFRASTRUCTURE-01.

All verifier coverage/wheel assertions are visibly fixture-only. No scientific
measurement, full verification, or accepted A/B checkpoint is claimed here.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from shared_node_baseline_infrastructure_fixture import (
    PINNED,
    PYTHON,
    digest,
    java_environment,
    probe,
    python,
    reader_layout,
    run,
)

SOURCE_MARKER = "OWNED_SOURCE_ONLY_MARKER_6031"
LOCAL_MARKER = "OWNED_LOCAL_ONLY_MARKER_9164"


def output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def assert_source_free(rendered: str) -> None:
    assert SOURCE_MARKER not in rendered, "standard rendering exposed owned source"
    assert LOCAL_MARKER not in rendered, "standard rendering exposed owned local"


def _assert_child_diagnostic(rendered: str, kind: str, executable: str) -> None:
    """Observe the exception diagnostic, allowing preserved paths and layout."""
    category = "TimeoutExpired" if kind == "timeout" else "CalledProcessError"
    match = re.search(rf"(?m)^\s*(?:subprocess\.)?{category}:\s*", rendered)
    assert match is not None, "child exception diagnostic missing"
    diagnostic = rendered[match.end() :]
    if kind == "string_failure":
        assert any(
            word in diagnostic.lower() for word in ["unavailable", "not recorded", "unknown"]
        )
        assert "exit 7" not in diagnostic
        assert executable not in diagnostic
    else:
        assert executable in diagnostic, "actual child executable identity missing"
        # Inspect standalone argument disclosure, not '-c' inside a preserved path.
        message = diagnostic.replace(executable, "<OWNED_EXECUTABLE>")
        assert re.search(r"(?:^|[\s'\"\[,])-c(?:$|[\s'\",\]])", message) is None
    if kind == "timeout":
        duration = re.search(
            r"\b(?:timed\s+out\s+(?:after|in)|timeout\s*(?:of|[:=])?|duration\s*[:=]?)"
            r"\s*(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
            r"(seconds?|secs?|s|milliseconds?|ms)\b",
            diagnostic.replace(executable, "<OWNED_EXECUTABLE>"),
            re.IGNORECASE,
        )
        assert duration is not None, "duration missing from timeout diagnostic"
        scale = 0.001 if duration[2].lower() in {"ms", "millisecond", "milliseconds"} else 1
        assert float(duration[1]) * scale == 1, "timeout diagnostic changed one-second duration"
    else:
        status = re.search(
            r"\b(?:exit\s+(?:status|code)|returncode|status)\s*[:=]?\s*(-?\d+)\b",
            diagnostic.replace(executable, "<OWNED_EXECUTABLE>"),
            re.IGNORECASE,
        )
        assert status is not None, "exit status missing from child exception diagnostic"
        assert int(status[1]) == 7, "child diagnostic changed exit status"


def _decoded_values(value: object) -> list[object]:
    """Reader-only scalar value observer; supplies no nested schema/association."""
    if isinstance(value, dict):
        return [leaf for child in value.values() for leaf in _decoded_values(child)]
    if isinstance(value, list):
        return [leaf for child in value for leaf in _decoded_values(child)]
    return [value]


def _assert_cached_reader_values(data: object, selected: str, jars: dict[str, Path]) -> None:
    assert isinstance(data, dict)
    values = _decoded_values(data)
    assert str(Path(selected).resolve()) in values
    assert "21.0.7" in values
    for identity, path in jars.items():
        assert identity in values
        assert str(path) in values
        assert path.stat().st_size in values
        assert digest(path) == identity


@pytest.mark.parametrize(
    "options",
    [[], ["-B"], ["-W", "always", "-X", "utf8"], ["-Walways", "-Xutf8"]],
)
def test_ordinary_interpreter_options_keep_warning_identity(
    tmp_path: Path, options: list[str]
) -> None:
    path = probe(
        tmp_path,
        f'''
        import warnings
        local = "{LOCAL_MARKER}"
        warnings.warn("VISIBLE_WARNING", UserWarning)  # {SOURCE_MARKER}
        ''',
    )
    result = python([*options, str(path)])
    rendered = output(result)
    assert result.returncode == 0
    assert "UserWarning: VISIBLE_WARNING" in rendered
    assert f"{path}:4" in rendered
    assert_source_free(rendered)


def test_interpreter_version_only() -> None:
    result = python(["-V"])
    assert result.returncode == 0
    assert f"Python {sys.version.split()[0]}" in output(result)


@pytest.mark.parametrize("policy", ["default", "always", "never"])
def test_long_option_value_and_literal_program_arguments(policy: str) -> None:
    result = python(
        [
            "--check-hash-based-pycs",
            policy,
            "-c",
            "import json, sys; print(json.dumps(sys.argv[1:]))",
            "-S",
            "-I",
            "-E",
        ]
    )
    assert result.returncode == 0
    assert json.loads(result.stdout) == ["-S", "-I", "-E"]


@pytest.mark.parametrize("chain", ["implicit", "cause", "suppressed"])
def test_real_exception_chains_and_notes(tmp_path: Path, chain: str) -> None:
    suffix = {"implicit": "", "cause": " from inner", "suppressed": " from None"}[chain]
    path = probe(
        tmp_path,
        f'''
        def fail():
            local = "{LOCAL_MARKER}"
            try:
                raise ValueError("INNER_VISIBLE")  # {SOURCE_MARKER}
            except ValueError as inner:
                outer = RuntimeError("OUTER_VISIBLE")
                outer.add_note("VISIBLE_NOTE")
                raise outer{suffix}
        fail()
        ''',
    )
    result = python([str(path)])
    rendered = output(result)
    assert result.returncode == 1
    assert "RuntimeError: OUTER_VISIBLE" in rendered
    assert "VISIBLE_NOTE" in rendered
    assert str(path) in rendered and "in fail" in rendered
    if chain == "suppressed":
        assert "INNER_VISIBLE" not in rendered
    else:
        assert "ValueError: INNER_VISIBLE" in rendered
        relation = "direct cause" if chain == "cause" else "During handling"
        assert relation in rendered
    assert_source_free(rendered)


@pytest.mark.parametrize(
    "api",
    [
        "format_exception(error)",
        "format_exception(type(error), error, error.__traceback__)",
        "print_exception(error, file=stream)",
        "print_exception(type(error), error, error.__traceback__, file=stream)",
        "print_exception(error)",
        "format_exc()",
        "print_exc(file=stream)",
        "format_tb(error.__traceback__)",
        "print_tb(error.__traceback__, file=stream)",
        "format_stack()",
        "print_stack(file=stream)",
        "format_tb(error.__traceback__, limit=1)",
    ],
)
def test_real_traceback_formatting_callers(tmp_path: Path, api: str) -> None:
    path = probe(
        tmp_path,
        f'''
        import io
        import traceback
        def fail():
            local = "{LOCAL_MARKER}"
            raise ValueError("API_VISIBLE")  # {SOURCE_MARKER}
        try:
            fail()
        except ValueError as error:
            original = (error.args, error.__traceback__, error.__cause__, error.__context__)
            stream = io.StringIO()
            rendered = traceback.{api}  # {SOURCE_MARKER}
            if rendered is not None:
                print("".join(rendered), end="")
            print(stream.getvalue(), end="")
            assert original == (error.args, error.__traceback__, error.__cause__, error.__context__)
            print("FIELDS_UNCHANGED")
        ''',
    )
    result = python([str(path)])
    rendered = output(result)
    assert result.returncode == 0
    assert "FIELDS_UNCHANGED" in rendered
    assert str(path) in rendered and "line " in rendered
    if "exception" in api or "exc(" in api:
        assert "ValueError: API_VISIBLE" in rendered
    assert_source_free(rendered)


@pytest.mark.parametrize("api", ["modern", "legacy", "traceback_exception"])
def test_real_syntax_error_exception_only(tmp_path: Path, api: str) -> None:
    path = probe(
        tmp_path,
        f'''
        import traceback
        invalid = "x = ( # {SOURCE_MARKER}"
        try:
            compile(invalid, "owned_invalid_fixture.py", "exec")
        except SyntaxError as error:
            original = (error.text, error.filename, error.lineno, error.offset, error.args)
            error.add_note("SYNTAX_NOTE_VISIBLE")
            if "{api}" == "modern":
                rendered = traceback.format_exception_only(error)
            elif "{api}" == "legacy":
                rendered = traceback.format_exception_only(type(error), error)
            else:
                te = traceback.TracebackException.from_exception(error)
                rendered = te.format_exception_only()
            print("".join(rendered), end="")
            assert original == (error.text, error.filename, error.lineno, error.offset, error.args)
            print("SYNTAX_FIELDS_UNCHANGED")
        ''',
    )
    result = python([str(path)])
    rendered = output(result)
    assert result.returncode == 0
    assert "SyntaxError" in rendered and "never closed" in rendered
    assert "owned_invalid_fixture.py" in rendered and "line 1" in rendered
    assert "SYNTAX_NOTE_VISIBLE" in rendered
    assert "SYNTAX_FIELDS_UNCHANGED" in rendered
    assert_source_free(rendered)


@pytest.mark.parametrize("exception_only", [False, True])
def test_real_exception_group_with_syntax_child(tmp_path: Path, exception_only: bool) -> None:
    path = probe(
        tmp_path,
        f"""
        import traceback
        errors = []
        try:
            raise ValueError("GROUP_ONE")  # {SOURCE_MARKER}
        except ValueError as error:
            errors.append(error)
        try:
            compile("x = ( # {SOURCE_MARKER}", "owned_group_invalid.py", "exec")
        except SyntaxError as error:
            errors.append(error)
        group = ExceptionGroup("VISIBLE_GROUP", errors)
        if {exception_only!r}:
            print("".join(traceback.TracebackException.from_exception(group).format_exception_only(show_group=True)))
        else:
            print("".join(traceback.format_exception(group)))
        """,
    )
    result = python([str(path)])
    rendered = output(result)
    assert result.returncode == 0
    for value in [
        "ExceptionGroup",
        "VISIBLE_GROUP",
        "ValueError: GROUP_ONE",
        "SyntaxError",
        "owned_group_invalid.py",
    ]:
        assert value in rendered
    if not exception_only:
        assert str(path) in rendered
    assert_source_free(rendered)


@pytest.mark.parametrize("kind", ["list_failure", "string_failure", "timeout"])
def test_real_child_failure_and_timeout_fields(tmp_path: Path, kind: str) -> None:
    location = tmp_path / "owned-compat"
    location.mkdir()
    path = probe(
        location,
        f'''
        import subprocess
        import sys
        import traceback
        from pathlib import Path
        kind = "{kind}"
        if kind == "string_failure":
            command = "exit 7 # {SOURCE_MARKER}"
        elif kind == "timeout":
            child = ("from pathlib import Path; import time; "
                     "Path('started').write_text('yes'); time.sleep(5) # {SOURCE_MARKER}")
            command = [sys.executable, "-c", child]
        else:
            child = "import sys; print('CAPTURED_CHILD_OUTPUT'); sys.exit(7) # {SOURCE_MARKER}"
            command = [sys.executable, "-c", child]
        expected_command = tuple(command) if isinstance(command, list) else command
        try:
            subprocess.run(command, shell=(kind == "string_failure"),
                           check=True, capture_output=True, timeout=1)
            raise AssertionError("expected genuine child failure")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            # List arguments contain immutable strings; tuple snapshots detect
            # in-place changes rather than retaining an alias to error.cmd.
            frozen_command = tuple(error.cmd) if isinstance(error.cmd, list) else error.cmd
            original = (frozen_command, error.output, error.stderr)
            assert frozen_command == expected_command
            if kind == "timeout":
                assert error.timeout == 1
                assert Path('started').read_text() == 'yes'
            else:
                assert error.returncode == 7
                if kind == "list_failure":
                    assert error.output == b'CAPTURED_CHILD_OUTPUT\\n'
            print("".join(traceback.format_exception(error)))
            frozen_after = tuple(error.cmd) if isinstance(error.cmd, list) else error.cmd
            assert original == (frozen_after, error.output, error.stderr)
            if kind == "timeout":
                assert error.timeout == 1
            else:
                assert error.returncode == 7
            print("CHILD_FIELDS_UNCHANGED")
        ''',
    )
    result = python([str(path)], cwd=tmp_path)
    rendered = output(result)
    assert result.returncode == 0
    assert "CHILD_FIELDS_UNCHANGED" in rendered
    assert str(path) in rendered  # Legitimate standard stack location contains '-c'.
    _assert_child_diagnostic(rendered, kind, str(PYTHON))
    assert_source_free(rendered)


def test_real_inherited_child_diagnostics(tmp_path: Path) -> None:
    child = probe(
        tmp_path,
        f"""
        import warnings
        warnings.warn("CHILD_WARNING", UserWarning)  # {SOURCE_MARKER}
        raise RuntimeError("CHILD_ERROR")  # {SOURCE_MARKER}
        """,
    )
    parent = tmp_path / "parent.py"
    parent.write_text(
        "import subprocess, sys\n"
        "result = subprocess.run([sys.executable, sys.argv[1]])\n"
        "sys.exit(result.returncode)\n"
    )
    result = python([str(parent), str(child)])
    rendered = output(result)
    assert result.returncode == 1
    assert "UserWarning: CHILD_WARNING" in rendered
    assert "RuntimeError: CHILD_ERROR" in rendered
    assert str(child) in rendered and "line 4" in rendered
    assert_source_free(rendered)


@pytest.mark.parametrize("path_selection", [False, True])
def test_authentic_cached_reader_with_real_selected_java(
    tmp_path: Path, path_selection: bool
) -> None:
    layout = tmp_path / "owned-reader-café"
    layout.mkdir()
    cache, jars = reader_layout(layout)
    before = {key: digest(value) for key, value in jars.items()}
    (cache / "inputs.json").write_text('{"stale_identity": true}')
    env = java_environment(path_selection=path_selection)
    result = python([str(layout / "scripts/prepare_imagej_reader.py")], cwd=layout, env=env)
    assert result.returncode == 0, "real selected JDK/cache preparation failed"
    manifest = cache / "inputs.json"
    data = json.loads(manifest.read_text())
    assert "stale_identity" not in data
    assert {key: digest(value) for key, value in jars.items()} == before
    selected = os.environ["SIMRECON_JAVA"]
    _assert_cached_reader_values(data, selected, jars)
    # Observer-only stdlib round trips: legitimate JSON escaping must not alter
    # value-presence proof. This changes no producer output or nested schema.
    for ascii_encoding in (True, False):
        encoded = json.dumps(data, ensure_ascii=ascii_encoding).replace("/", r"\/")
        _assert_cached_reader_values(json.loads(encoded), selected, jars)


@pytest.mark.parametrize(
    "failure",
    [
        "missing_java",
        "identity_command_failed",
        "source_launcher_failed",
        "corrupt_cache",
        "oversize_bioformats",
        "oversize_imagej",
    ],
)
def test_reader_failure_removes_stale_identity_without_replacing_cache(
    tmp_path: Path, failure: str
) -> None:
    cache, jars = reader_layout(tmp_path)
    env = java_environment()
    stale = cache / "inputs.json"
    stale.write_text('{"owned_stale": true}')
    if failure == "missing_java":
        env["SIMRECON_JAVA"] = str(tmp_path / "absent_java")
        # A real valid Java on PATH must not rescue missing explicit selection.
        env["PATH"] = (
            str(Path(os.environ["SIMRECON_JAVA"]).parent) + os.pathsep + env.get("PATH", "")
        )
    elif failure == "identity_command_failed":
        env["JDK_JAVA_OPTIONS"] = "--owned-invalid-option"
        # JVM startup output is captured separately and never rendered to A.
        identity = run([env["SIMRECON_JAVA"], "-version"], env=env)
        assert identity.returncode != 0, "real Java identity-failure premise missing"
    elif failure == "source_launcher_failed":
        env["JDK_JAVA_OPTIONS"] = "--limit-modules=java.base"
        identity = run([env["SIMRECON_JAVA"], "-version"], env=env)
        assert identity.returncode == 0 and "21.0.7" in output(identity)
        source = tmp_path / "OwnedRestrictedLaunch.java"
        source.write_text("class OwnedRestrictedLaunch { public static void main(String[] a) {} }")
        launch = run([env["SIMRECON_JAVA"], str(source)], env=env)
        assert launch.returncode != 0, "real Java source-launch failure premise missing"
    elif failure == "corrupt_cache":
        next(iter(jars.values())).write_bytes(b"OWNED_CORRUPT_CACHE")
    else:
        maximum = 70_000_000 if failure == "oversize_bioformats" else 10_000_000
        identity = next(key for key, limit in PINNED.items() if limit == maximum)
        with jars[identity].open("wb") as stream:
            stream.truncate(maximum + 1)
    before = {path.name: (path.stat().st_size, digest(path)) for path in jars.values()}
    result = python([str(tmp_path / "scripts/prepare_imagej_reader.py")], cwd=tmp_path, env=env)
    assert result.returncode != 0
    assert not stale.exists()
    assert {path.name: (path.stat().st_size, digest(path)) for path in jars.values()} == before
