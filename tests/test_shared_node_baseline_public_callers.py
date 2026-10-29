"""A09 corrected supplemental public callers; no new scientific oracle."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

import shared_node_baseline_public_callers_fixture as callers_fixture
from shared_node_baseline_public_callers_fixture import (
    CACHE,
    DECLARATIONS,
    GENERATOR,
    HARNESS,
    PHASES,
    READER,
    Transport,
    VerificationFixture,
    assert_identity,
    digest,
    inventory,
    invoke,
    java_wrapper,
    python,
    reader,
    record,
    reserved,
    selected_java,
)


def test_actual_reader_cached_identity_and_standard_loading(tmp_path: Path) -> None:
    """C71/C72: authentic bytes, selected executable and real downstream command."""
    driver = tmp_path / "reader-preflight.py"
    driver.write_text(
        "import runpy,sys\n"
        f"sys.argv=[{str(READER)!r}]\n"
        "try:\n"
        f"    runpy.run_path({str(READER)!r},run_name='A08_operational_preflight')\n"
        "except SystemExit as error:\n"
        "    if error.code not in (None,0): raise\n"
        f"sys.argv=[{str(READER)!r}]\n"
        f"runpy.run_path({str(READER)!r},run_name='__main__')\n"
    )
    with reserved() as cache:
        cache.seed()
        authentic = {name: digest(CACHE / name) for name in DECLARATIONS}
        result = reader(driver=driver)
        assert result.returncode == 0
        assert_identity(selected_java(), tmp_path)
        assert {name: digest(CACHE / name) for name in DECLARATIONS} == authentic


def test_actual_reader_path_selected_java(tmp_path: Path) -> None:
    """The documented fallback PATH selection accepts a working source launcher."""
    wrapper = java_wrapper(tmp_path, "valid")
    (tmp_path / "java").symlink_to(wrapper)
    env = dict(os.environ)
    env.pop("SIMRECON_JAVA", None)
    env["PATH"] = str(tmp_path) + os.pathsep + env.get("PATH", "")
    with reserved() as cache:
        cache.seed()
        result = reader(env)
        assert result.returncode == 0
        assert_identity("java", tmp_path, env)


@pytest.mark.parametrize(
    "variant",
    [
        "absent",
        "failure",
        "wrong-version",
        "missing-vendor",
        "missing-platform",
        "launcher-failure",
    ],
)
def test_actual_reader_selected_java_rejection(tmp_path: Path, variant: str) -> None:
    """C72: identity omissions and launcher failures cannot produce current evidence."""
    env = dict(os.environ)
    env["SIMRECON_JAVA"] = str(
        tmp_path / "missing-java" if variant == "absent" else java_wrapper(tmp_path, variant)
    )
    with reserved() as cache:
        cache.seed()
        hashes = {name: digest(CACHE / name) for name in DECLARATIONS}
        result = reader(env)
        assert result.returncode != 0
        assert not (CACHE / "inputs.json").exists()
        assert {name: digest(CACHE / name) for name in DECLARATIONS} == hashes


@pytest.mark.parametrize("variant", ["corrupt", "oversized"])
def test_actual_reader_invalid_cached_jar_preserved(variant: str) -> None:
    """C71: invalid cached bytes remain diagnostic input rather than silent replacement."""
    with reserved() as cache:
        cache.seed()
        path = CACHE / "ij-1.54p.jar"
        if variant == "corrupt":
            path.write_bytes(b"A08-independent-corrupt-cache")
        else:
            with path.open("wb") as stream:
                stream.truncate(DECLARATIONS[path.name]["maximum_bytes"] + 1)
        before = digest(path)
        other = digest(CACHE / "bioformats_package.jar")
        result = reader()
        assert result.returncode != 0
        assert digest(path) == before
        assert digest(CACHE / "bioformats_package.jar") == other
        assert not (CACHE / "inputs.json").exists()


@pytest.mark.parametrize(
    "name,mode",
    [
        ("ij-1.54p.jar", mode)
        for mode in (
            "length",
            "eof",
            "redirect",
            "advertised-oversize",
            "actual-oversize",
            "socket-timeout",
            "digest",
        )
    ]
    + [("bioformats_package.jar", "length")],
)
def test_transport_actual_reader_authenticated_download(
    tmp_path: Path, name: str, mode: str
) -> None:
    """Genuine TLS/client I/O: authenticated positives and independently invalid bytes."""
    other_name = next(item for item in DECLARATIONS if item != name)
    with reserved() as cache:
        cache.seed(omit=name)
        other = digest(CACHE / other_name)
        temporary = tmp_path / "download-temporary"
        temporary.mkdir()
        with Transport(tmp_path, cache.backup / name, mode) as transport:
            started = time.monotonic()
            result = reader(transport.environment() | {"TMPDIR": str(temporary)}, timeout=70)
            elapsed = time.monotonic() - started
            requests = [
                event["request"] for event in transport.events if event["event"] == "request"
            ]
            assert requests and all(request.startswith("GET ") for request in requests), (
                "Tooling nonwitness: transport GET not reached"
            )
            if mode == "socket-timeout":
                assert 14 <= elapsed < 40, "Tooling nonwitness: earlier failure than socket bound"
        if mode in {"length", "eof"}:
            assert result.returncode == 0
            assert_identity(
                selected_java(), tmp_path, observed_urls={name: transport.observed_url()}
            )
            assert digest(CACHE / name) == DECLARATIONS[name]["sha256"]
            assert {path.name for path in CACHE.iterdir()} == {"inputs.json", *DECLARATIONS}
        else:
            assert result.returncode != 0
            assert not (CACHE / name).exists()
            assert not (CACHE / "inputs.json").exists()
            assert {path.name for path in CACHE.iterdir()} == {other_name}
        assert digest(CACHE / other_name) == other
        assert list(temporary.iterdir()) == [], "scoped temporary download leaked"


def test_parent_deadline_actual_reader_slow_active_transport(tmp_path: Path) -> None:
    """A real >180 s transfer with activity every 5 s distinguishes parent deadline."""
    name = "ij-1.54p.jar"
    with reserved() as cache:
        cache.seed(omit=name)
        other = digest(CACHE / "bioformats_package.jar")
        with Transport(tmp_path, cache.backup / name, "parent-deadline") as transport:
            start = time.monotonic()
            observation: dict[str, object] = {}
            result = reader(transport.environment(), timeout=225, observation=observation)
            elapsed = time.monotonic() - start
            activity = [event["at_s"] for event in transport.events if event["event"] == "bytes"]
            witness = bool(activity) and elapsed >= 175 and activity[-1] - activity[0] >= 170
            record(
                "deadline-classification",
                {
                    "witness": witness,
                    "duration_s": elapsed,
                    "status": result.returncode,
                    "activity_s": activity,
                    "scheduled_transfer_s": 5
                    * ((DECLARATIONS[name]["size_bytes"] + 65535) // 65536),
                    "outer_bound_s": 225,
                    "socket_bound_s": 15,
                    "subprocess": observation,
                },
            )
            assert witness, (
                "Tooling nonwitness: earlier failure did not exercise the parent deadline"
            )
            assert all(
                0 < right - left < 15 for left, right in zip(activity, activity[1:], strict=False)
            )
            assert 175 <= elapsed < 210
            assert result.returncode != 0
            cleanup = observation["child_cleanup"]
            assert isinstance(cleanup, dict) and cleanup["observed_child_pids"]
            assert not cleanup["remaining_child_states"]
        assert not (CACHE / name).exists()
        assert not (CACHE / "inputs.json").exists()
        assert {path.name for path in CACHE.iterdir()} == {"bioformats_package.jar"}
        assert digest(CACHE / "bioformats_package.jar") == other


@pytest.mark.parametrize("relationship", ["cause", "context", "shared-group"])
def test_source_free_uncaught_finite_exception_relationships(
    tmp_path: Path, relationship: str
) -> None:
    """C73: lawful cyclic/shared exceptions terminate without source or locals."""
    script = tmp_path / "uncaught-public-exception.py"
    if relationship == "cause":
        body = "first.__cause__=second\nsecond.__cause__=first\nraise first from second"
        expected = ["ValueError: A08-first", "RuntimeError: A08-second"]
    elif relationship == "context":
        body = "first.__context__=second\nsecond.__context__=first\nraise first"
        expected = ["ValueError: A08-first", "RuntimeError: A08-second"]
    else:
        body = (
            "raise ExceptionGroup('A08-group',"
            "[first,ExceptionGroup('A08-subgroup',[first,second])])"
        )
        expected = [
            "ExceptionGroup: A08-group",
            "ValueError: A08-first",
            "RuntimeError: A08-second",
        ]
    script.write_text(
        "first=ValueError('A08-first')\nsecond=RuntimeError('A08-second')\n"
        "local_marker='A08_LOCAL_SECRET'\n" + body + " # A08_SOURCE_SECRET\n"
    )
    result = python(script, timeout=20)
    assert result.returncode != 0
    for message in expected:
        assert message in result.stderr
    assert str(script) in result.stderr
    for channel in (result.stdout, result.stderr):
        assert "A08_SOURCE_SECRET" not in channel
        assert "A08_LOCAL_SECRET" not in channel


def assert_passed_native_receipt(
    fixture: VerificationFixture, document: dict[str, object] | None
) -> None:
    """Independent exact sums over Coverage.py's top-level contributions, once."""
    assert document is not None and document["result"] == "passed"
    native = json.loads((fixture.root / "artifacts/coverage/coverage.json").read_text())
    for key in (
        "num_statements",
        "covered_lines",
        "missing_lines",
        "excluded_lines",
        "num_branches",
        "covered_branches",
        "missing_branches",
        "num_partial_branches",
    ):
        assert native["totals"][key] == sum(
            item["summary"][key] for item in native["files"].values()
        )
    assert "external.py" in native["files"]
    assert native["files"]["external.py"]["summary"]["excluded_lines"] > 0
    coverage = document["coverage"]
    assert isinstance(coverage, dict)
    expected_files = {"src/simrecon/owned.py", "scripts/owned.py"}
    assert set(coverage["files"]) == expected_files
    for file in expected_files:
        emitted = native["files"][file]["summary"]
        assert coverage["files"][file] == {
            "statements": {"covered": emitted["covered_lines"], "total": emitted["num_statements"]},
            "branches": {"covered": emitted["covered_branches"], "total": emitted["num_branches"]},
        }
    for metric in ("statements", "branches"):
        for count in ("covered", "total"):
            assert coverage["global"][metric][count] == sum(
                coverage["files"][name][metric][count] for name in expected_files
            )
    for package, file in (("simrecon", "src/simrecon/owned.py"), ("scripts", "scripts/owned.py")):
        assert coverage["packages"][package] == coverage["files"][file]
    assert (fixture.root / ".coverage").stat().st_size > 0
    assert (fixture.root / "artifacts/coverage/html/index.html").is_file()
    wheel = fixture.root / "dist/simrecon-0.1.0-py3-none-any.whl"
    artifact = document["artifact"]
    assert isinstance(artifact, dict)
    assert artifact["sha256"] == digest(wheel)
    assert artifact["size_bytes"] == wheel.stat().st_size
    assert artifact["version"] == "0.1.0"


def test_verifier_genuine_native_extra_file_and_standard_loading(tmp_path: Path) -> None:
    """C76/C77/C81/P08: external contributions are counted once, not discarded."""
    fixture = VerificationFixture(tmp_path)
    result, document = fixture.run(receipt="artifacts/custom-safe/receipt.json", load=True)
    assert result.returncode == 0
    assert_passed_native_receipt(fixture, document)
    assert document is not None
    phases = document["phases"]
    assert isinstance(phases, list)
    assert [phase["name"] for phase in phases] == PHASES
    for phase in phases:
        assert phase["returncode"] == 0
        assert phase["command"][0] == str(fixture.make)
        assert phase["name"] in phase["command"]
        assert "UV=" + sys.executable in phase["command"]
        assert (
            "A08 actual disposable phase " + phase["name"]
            in (fixture.root / phase["log"]).read_text()
        )


@pytest.mark.parametrize(
    "scope,field,value",
    [("totals", "missing_lines", False), ("file", "num_partial_branches", 0.0)],
)
def test_verifier_rejects_invalid_native_count_types(
    tmp_path: Path, scope: str, field: str, value: object
) -> None:
    """C77: authentic emitted complete reports with one invalid native integer."""
    fixture = VerificationFixture(tmp_path)
    fixture.configure({"native_change": {"scope": scope, "field": field, "value": value}})
    result, document = fixture.run()
    assert result.returncode == 1
    assert document is None or document["result"] == "failed"


def test_verifier_rejects_inconsistent_native_top_level_total(tmp_path: Path) -> None:
    fixture = VerificationFixture(tmp_path)
    fixture.configure(
        {"native_change": {"scope": "totals", "field": "num_statements", "increment": True}}
    )
    result, document = fixture.run()
    assert result.returncode == 1
    assert document is None or document["result"] == "failed"


@pytest.mark.parametrize(
    "output",
    [
        "control-marker.txt",
        ".git/config",
        "missing-tracked.txt",
        "artifacts/receipt-hardlink.json",
    ],
)
def test_verifier_initial_protected_output_preserved(tmp_path: Path, output: str) -> None:
    """P01/P06/P09: tracked/Git, missing tracked and hardlink identity protection."""
    fixture = VerificationFixture(tmp_path)
    marker = fixture.root / "control-marker.txt"
    before = marker.read_bytes()
    git_config = (fixture.root / ".git/config").read_bytes()
    if output == "missing-tracked.txt":
        # A tracked path remains protected even when its bytes are absent.
        output = "control-marker.txt"
        marker.unlink()
    elif output == "artifacts/receipt-hardlink.json":
        (fixture.root / "artifacts").mkdir()
        (fixture.root / output).hardlink_to(marker)
    initially_present = marker.exists()
    result, document = fixture.run(receipt=output)
    if output == "artifacts/receipt-hardlink.json" and result.returncode == 0:
        assert_passed_native_receipt(fixture, document)
        assert (fixture.root / output).stat().st_ino != marker.stat().st_ino
    else:
        assert result.returncode != 0
        assert document is None or document.get("result") != "passed"
    if initially_present:
        assert marker.is_file()
        assert marker.read_bytes() == before
    else:
        assert not marker.exists() and not marker.is_symlink()
    assert (fixture.root / ".git/config").read_bytes() == git_config


@pytest.mark.parametrize("mode", ["mkdir", "late-open"])
@pytest.mark.parametrize("fail", [False, True])
def test_verifier_public_audit_output_observer_preserves_protected_bytes(
    tmp_path: Path, mode: str, fail: bool
) -> None:
    """P02/P04/P10: observer witness is explicit; safe atomic replacement is lawful."""
    fixture = VerificationFixture(tmp_path)
    if fail:
        fixture.configure({"fail_phase": "lint", "status": 23})
    marker = (fixture.root / "control-marker.txt").read_bytes()
    config = (fixture.root / ".git/config").read_bytes()
    git_before = inventory(fixture.root / ".git")
    result, document = fixture.run(receipt="artifacts/observer-output/receipt.json", observer=mode)
    observation = json.loads((fixture.root / "observer.json").read_text())
    record(
        "audit-classification",
        {
            "mode": mode,
            "observation": observation,
            "classification": "witness" if observation["witness"] else "lawful-backend-nonwitness",
            "status": result.returncode,
        },
    )
    assert (fixture.root / "control-marker.txt").read_bytes() == marker
    assert (fixture.root / ".git/config").read_bytes() == config
    git_after = inventory(fixture.root / ".git")
    # Content, mode and additions matter; timestamps and directory sizes do not.
    assert {
        name: {key: item[key] for key in ("directory", "mode", "sha256")}
        for name, item in git_after.items()
    } == {
        name: {key: item[key] for key in ("directory", "mode", "sha256")}
        for name, item in git_before.items()
    }
    if fail:
        assert result.returncode == 23
        assert document is None or document["result"] != "passed"
        trace = [
            json.loads(line)["phase"]
            for line in (fixture.root / "phase-trace.jsonl").read_text().splitlines()
        ]
        assert trace == PHASES[:3]
        if document is not None:
            assert [phase["name"] for phase in document["phases"]] == PHASES[:3]
            assert document["phases"][-1]["returncode"] == 23
    elif result.returncode == 0:
        assert_passed_native_receipt(fixture, document)
    else:
        assert document is None or document["result"] != "passed"


@pytest.mark.parametrize("failure", ["child-status", "child-timeout"])
@pytest.mark.parametrize("representation", ["argv-path", "direct-path"])
def test_source_free_live_path_subprocess_fields(
    tmp_path: Path, failure: str, representation: str
) -> None:
    """C74: real public Path executable, original fields and argument-free rendering."""
    ready = tmp_path / "child-ready"
    child = tmp_path / "child.py"
    child.write_text(
        "import pathlib,threading,sys\nprint('A08-child-output',flush=True)\n"
        "print('A08-child-error',file=sys.stderr,flush=True)\n"
        + (
            f"pathlib.Path({str(ready)!r}).touch()\nthreading.Event().wait()\n"
            if failure == "child-timeout"
            else "sys.exit(23)\n"
        )
    )
    if representation == "direct-path":
        executable = tmp_path / "owned-child"
        executable.write_text(f"#!{sys.executable}\n" + child.read_text())
        executable.chmod(0o700)
        command = "executable"
    else:
        executable = Path(sys.executable)
        command = f"[executable, {str(child)!r}, 'A08_ARG_SECRET']"
    if failure == "child-timeout":
        # Start the timeout after both streams are flushed, not during interpreter startup.
        invocation = (
            "    with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,\n"
            "                          text=True) as process:\n"
            "        try:\n"
            "            deadline=time.monotonic()+10\n"
            "            while not ready.is_file() and time.monotonic()<deadline:\n"
            "                assert process.poll() is None, 'Tooling nonwitness: child exited'\n"
            "                time.sleep(0.01)\n"
            "            assert ready.is_file(), 'Tooling nonwitness: child did not become ready'\n"
            "            process.communicate(timeout=0.15)\n"
            "        finally:\n"
            "            if process.poll() is None: process.kill()\n"
            "            process.communicate(timeout=5)\n"
        )
    else:
        invocation = (
            "    subprocess.run(command,check=True,capture_output=True,text=True,timeout=6)\n"
        )
    script = tmp_path / "path-caller.py"
    script.write_text(
        "import json,pathlib,subprocess,time\n"
        f"ready=pathlib.Path({str(ready)!r})\n"
        f"executable=pathlib.Path({str(executable)!r})\ncommand={command}\n"
        "try:\n"
        + invocation
        + "except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as error:\n"
        "    assert error.cmd == command\n"
        "    assert error.stdout in ('A08-child-output\\n',b'A08-child-output\\n')\n"
        "    assert error.stderr in ('A08-child-error\\n',b'A08-child-error\\n')\n"
        "    if isinstance(error,subprocess.TimeoutExpired): assert error.timeout == 0.15\n"
        "    else: assert error.returncode == 23\n"
        "    print(json.dumps({'fields_preserved':True}),flush=True)\n"
        "    raise # A08_SOURCE_SECRET\n"
    )
    result = python(script, timeout=20)
    assert result.returncode != 0
    assert json.loads(result.stdout)["fields_preserved"] is True
    assert (
        "TimeoutExpired" if failure == "child-timeout" else "CalledProcessError"
    ) in result.stderr
    assert ("0.15" if failure == "child-timeout" else "23") in result.stderr
    if representation == "argv-path":
        assert str(executable) in result.stderr
    assert "A08_ARG_SECRET" not in result.stderr
    assert "A08_SOURCE_SECRET" not in result.stderr


def test_source_free_standard_loading_then_real_command(tmp_path: Path) -> None:
    """No quiet-import assumption: load with valid argv, then observe real failure."""
    child = tmp_path / "load-command.py"
    child.write_text("raise ValueError('A08-loaded-command') # A08_SOURCE_SECRET\n")
    driver = tmp_path / "load-preflight.py"
    driver.write_text(
        "import runpy,sys\n"
        f"sys.argv=[{str(HARNESS)!r},'python',{str(child)!r}]\n"
        "try:\n"
        f"    runpy.run_path({str(HARNESS)!r},run_name='A08_operational_preflight')\n"
        "except SystemExit:\n"
        "    pass\n"
        f"sys.argv=[{str(HARNESS)!r},'python',{str(child)!r}]\n"
        f"runpy.run_path({str(HARNESS)!r},run_name='__main__')\n"
    )
    result = python(driver, timeout=30)
    assert result.returncode != 0
    assert "ValueError: A08-loaded-command" in result.stderr
    assert str(child) in result.stderr
    assert "A08_SOURCE_SECRET" not in result.stderr


@pytest.mark.parametrize("selector", ["otf", "reconstruction"])
def test_actual_generator_bounded_loading_and_caller_lifecycle(
    tmp_path: Path, selector: str
) -> None:
    """C83/C86: operational loading observation plus real selector/file consumption.

    No complete scientific fields, historical digests, quiet import or library API
    expectation follows. Non-main rejection is lawful when the real CLI succeeds.
    """
    with tempfile.TemporaryDirectory(prefix="A09-generator-", dir=tmp_path) as name:
        directory = Path(name)
        loader = directory / "loader.py"
        loading_observation = directory / "loading.json"
        loader.write_text(
            "import json,pathlib,runpy,sys\n"
            f"sys.argv=[{str(GENERATOR)!r},{selector!r}]\n"
            "observation={'operation':'non-main runpy loading','completed':False}\n"
            "try:\n"
            f"    runpy.run_path({str(GENERATOR)!r},run_name='A09_operational_observation')\n"
            "    observation['completed']=True\n"
            "except BaseException as error:\n"
            "    observation['category']=type(error).__name__\n"
            "    observation['message']=str(error)\n"
            "    if isinstance(error,SystemExit): observation['status']=error.code\n"
            "finally:\n"
            f"    pathlib.Path({str(loading_observation)!r}).write_text(json.dumps(observation))\n"
        )
        try:
            loading = python(
                loader, cwd=directory, timeout=90, kind="generator-non-main-observation"
            )
            loading_status = loading.returncode
        except AssertionError as error:
            if str(error) != "Tooling nonwitness: supported outer wait expired":
                raise
            loading_status = None
        # Loading is observational. Even a bounded timeout is not a product-red CLI claim.
        observation = (
            json.loads(loading_observation.read_text())
            if loading_observation.exists()
            else {"operation": "non-main runpy loading", "bounded_completion": False}
        )
        output = directory / "caller-output.json"
        caller = directory / "documented-caller.py"
        caller.write_text(
            "import json,pathlib,subprocess,sys\n"
            f"output=pathlib.Path({str(output)!r})\n"
            "with output.open('w') as stream:\n"
            f"    result=subprocess.run([{sys.executable!r},{str(HARNESS)!r},'--timeout','90',"
            f"'python',{str(GENERATOR)!r},{selector!r}],stdout=stream,stderr=subprocess.PIPE,"
            "text=True,timeout=95)\n"
            "sys.stderr.write(result.stderr)\n"
            "if result.returncode: sys.exit(result.returncode)\n"
            # json.load consumes exactly one document and rejects trailing non-whitespace.
            "with output.open() as stream: document=json.load(stream)\n"
            "print(json.dumps({'consumed':True,'exists_during_context':output.is_file()}))\n"
        )
        output.write_text("")  # The caller owns this destination before CLI execution.
        entries_before_cli = inventory(directory)
        cli = python(caller, cwd=directory, timeout=105, kind="actual-generator-documented-caller")
        record(
            "generator-loading-classification",
            {
                "selector": selector,
                "loading": observation,
                "loading_status": loading_status,
                "cli_status": cli.returncode,
                "classification": (
                    "CLI-success; loading observation only"
                    if cli.returncode == 0
                    else "CLI-failure; dependency/environment or product diagnosis required"
                ),
            },
        )
        assert cli.returncode == 0
        assert json.loads(cli.stdout) == {"consumed": True, "exists_during_context": True}
        # A caller-side parse independently consumes the whole returned document too.
        json.loads(output.read_text())
        entries_after_cli = inventory(directory)
        record(
            "generator-caller-lifecycle",
            {
                "selector": selector,
                "output_sha256": digest(output),
                "generator_sha256": digest(GENERATOR),
                "consumed_inside_context": True,
                "owned_entries": sorted(path.name for path in directory.iterdir()),
                "before_cli": entries_before_cli,
                "after_cli": entries_after_cli,
                "limit": "Owned location inventory only; no global or transient-write guarantee",
            },
        )
        assert set(entries_after_cli) == set(entries_before_cli)
        for entry in entries_before_cli:
            if entry != "caller-output.json":
                for field in ("directory", "mode", "sha256"):
                    assert entries_after_cli[entry][field] == entries_before_cli[entry][field]
    assert not directory.exists()
    record("generator-context-cleanup", {"selector": selector, "removed": not directory.exists()})


def test_owned_invoke_exception_cleanup_before_cache_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture-only witness: ordinary helper interruption releases no active child."""
    import subprocess

    marker = tmp_path / "child-started.json"
    script = tmp_path / "owned-sleeping-child.py"
    script.write_text(
        "import json,os,pathlib,time\n"
        f"pathlib.Path({str(marker)!r}).write_text(json.dumps({{'pid':os.getpid()}}))\n"
        "time.sleep(30)\n"
    )
    ordinary_communicate = subprocess.Popen.communicate
    interrupted = False

    def interrupt_once(process: subprocess.Popen[str], *args: Any, **kwargs: Any) -> Any:
        nonlocal interrupted
        if not interrupted:
            deadline = time.monotonic() + 10
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            assert marker.exists(), "Tooling nonwitness: child did not start"
            interrupted = True
            raise RuntimeError("A09-owned-fixture-interruption")
        return ordinary_communicate(process, *args, **kwargs)

    original = inventory(CACHE)
    inode = CACHE.stat().st_ino
    with reserved() as cache:
        cache.seed()
        with monkeypatch.context() as patch:
            patch.setattr(subprocess.Popen, "communicate", interrupt_once)
            with pytest.raises(RuntimeError, match="A09-owned-fixture-interruption"):
                invoke(
                    [sys.executable, HARNESS, "--timeout", "40", "python", script],
                    timeout=45,
                    kind="owned-fixture-interruption",
                )
        pid = json.loads(marker.read_text())["pid"]
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    assert interrupted and inventory(CACHE) == original and CACHE.stat().st_ino == inode


def _lifecycle_states(pids: list[int]) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["ps", "-p", ",".join(map(str, pids)), "-o", "pid=,ppid=,pgid=,stat="],
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert result.returncode in (0, 1)
    states = []
    for line in result.stdout.splitlines():
        pid, parent, group, state = line.split()
        states.append(
            {
                "pid": int(pid),
                "ppid": int(parent),
                "pgid": int(group),
                "state": state,
                "session": os.getsid(int(pid)),
            }
        )
    return states


@contextlib.contextmanager
def _disposable_lifecycle_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[callers_fixture.ReaderReservation]:
    cache_path = tmp_path / "owned-cache"
    cache_path.mkdir()
    marker = cache_path / "preserved.bin"
    marker.write_bytes(b"A02-independent-owned-cache\x00\xff")
    marker.chmod(0o640)
    cache_path.chmod(0o750)
    before = inventory(cache_path)
    inode, mode = cache_path.stat().st_ino, cache_path.stat().st_mode
    evidence = tmp_path / "owned-evidence"
    evidence.mkdir()
    with monkeypatch.context() as patch:
        patch.setattr(callers_fixture, "CACHE", cache_path)
        patch.setattr(callers_fixture, "EVIDENCE", evidence)
        patch.setattr(callers_fixture, "RUN", evidence / "run")
        with callers_fixture.ReaderReservation() as reservation:
            yield reservation
        assert inventory(cache_path) == before
        assert cache_path.stat().st_ino == inode and cache_path.stat().st_mode == mode
        assert not reservation.backup.exists() and not reservation.lock.exists()


class _OwnedLifecycle:
    """Real owned processes, independent observations and bounded emergency rescue."""

    def __init__(self, directory: Path, separate: bool, mode: str, status: int = 0) -> None:
        self.directory = directory
        directory.mkdir()
        self.separate = separate
        self.mode = mode
        self.failure = RuntimeError("A02-supplemental-original-interruption")
        self.roots: list[subprocess.Popen[str]] = []
        self.child_pid: int | None = None
        self.observation_failed = False
        self.observer_denials: list[dict[str, str]] = []
        self.first = True
        self.stop = directory / "stop-child"
        self.parent_identity = directory / "parent.json"
        self.child_identity = directory / "child.json"
        self.parent = directory / "parent.py"
        child = directory / "child.py"
        child.write_text(
            "import json,os,pathlib,sys,time\n"
            "print('A02-child-out',flush=True)\n"
            "print('A02-child-err',file=sys.stderr,flush=True)\n"
            f"identity=pathlib.Path({str(self.child_identity)!r})\n"
            "temporary=identity.with_suffix('.tmp')\n"
            "temporary.write_text(json.dumps(dict(pid=os.getpid(),ppid=os.getppid(),"
            "pgid=os.getpgrp(),session=os.getsid(0))))\n"
            "temporary.replace(identity)\n"
            f"stop=pathlib.Path({str(self.stop)!r})\n"
            f"deadline=time.monotonic()+{1 if mode == 'complete' else 20}\n"
            "while time.monotonic()<deadline and not stop.exists(): time.sleep(0.02)\n"
            f"sys.exit({status})\n"
        )
        self.parent.write_text(
            "import json,os,pathlib,subprocess,sys\n"
            "print('A02-parent-out',flush=True)\n"
            "print('A02-parent-err',file=sys.stderr,flush=True)\n"
            f"child=subprocess.Popen([sys.executable,{str(child)!r}]"
            + (",process_group=0" if separate else "")
            + ")\ntry:\n"
            f"    identity=pathlib.Path({str(self.parent_identity)!r})\n"
            "    temporary=identity.with_suffix('.tmp')\n"
            "    temporary.write_text(json.dumps(dict(pid=os.getpid(),child=child.pid,"
            "pgid=os.getpgrp(),session=os.getsid(0))))\n"
            "    temporary.replace(identity)\n"
            "    status=child.wait(timeout=24)\n"
            "finally:\n"
            f"    pathlib.Path({str(self.stop)!r}).touch()\n"
            "    if child.poll() is None:\n"
            "        child.terminate()\n"
            "        try: child.wait(timeout=2)\n"
            "        except subprocess.TimeoutExpired:\n"
            "            child.kill()\n"
            "            child.wait(timeout=2)\n"
            "sys.exit(status)\n"
        )
        self.unrelated_stop = directory / "stop-unrelated"
        unrelated_script = directory / "unrelated.py"
        unrelated_script.write_text(
            "import pathlib,time\n"
            f"stop=pathlib.Path({str(self.unrelated_stop)!r})\n"
            "deadline=time.monotonic()+30\n"
            "while time.monotonic()<deadline and not stop.exists(): time.sleep(0.02)\n"
        )
        self.unrelated = subprocess.Popen(
            [sys.executable, unrelated_script],
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.native_init = subprocess.Popen.__init__
        self.native_communicate = subprocess.Popen.communicate
        self.native_run = subprocess.run

    def install(self, patch: pytest.MonkeyPatch) -> None:
        def capture(process: Any, args: Any, *more: Any, **kwargs: Any) -> None:
            self.native_init(process, args, *more, **kwargs)
            if args == [sys.executable, str(self.parent)]:
                self.roots.append(process)
                record("A02-root-identity", {"pid": process.pid})

        def communicate(process: Any, *args: Any, **kwargs: Any) -> Any:
            if self.roots and process is self.roots[0] and self.first:
                self.first = False
                deadline = time.monotonic() + 5
                while not (self.parent_identity.exists() and self.child_identity.exists()):
                    assert time.monotonic() < deadline, (
                        "Tooling nonwitness: identity markers absent"
                    )
                    time.sleep(0.02)
                parent = json.loads(self.parent_identity.read_text())
                self.child_pid = int(parent["child"])
                record("A02-child-identity", {"parent": parent, "child_pid": self.child_pid})
                child = json.loads(self.child_identity.read_text())
                assert child["pid"] == self.child_pid and child["ppid"] == process.pid
                assert parent["session"] == child["session"] == process.pid
                assert (parent["pgid"] != child["pgid"]) == self.separate
                states = _lifecycle_states([process.pid, self.child_pid, self.unrelated.pid])
                record("A02-before-process-states", {"states": states})
                assert {entry["pid"] for entry in states} == {
                    process.pid,
                    self.child_pid,
                    self.unrelated.pid,
                }
                assert os.getsid(self.unrelated.pid) != process.pid
                if self.mode in {"interrupt", "observation-failure"}:
                    self.observation_failed = self.mode == "observation-failure"
                    raise self.failure
            return self.native_communicate(process, *args, **kwargs)

        def run(args: Any, *more: Any, **kwargs: Any) -> Any:
            if self.observation_failed and _lifecycle_process_query(args, kwargs.get("executable")):
                denial = {
                    "category": "PermissionError",
                    "executable": str(
                        kwargs.get("executable")
                        or (args[0] if isinstance(args, (list, tuple)) else args)
                    ),
                }
                self.observer_denials.append(denial)
                record("A02-observer-denied", denial)
                raise PermissionError("A02-injected-public-process-observation-denied")
            return self.native_run(args, *more, **kwargs)

        patch.setattr(subprocess.Popen, "__init__", capture)
        patch.setattr(subprocess.Popen, "communicate", communicate)
        patch.setattr(subprocess, "run", run)

    def assert_stopped(self) -> None:
        assert self.child_pid is not None
        with pytest.raises(ProcessLookupError):
            os.kill(self.child_pid, 0)
        with pytest.raises(ProcessLookupError):
            os.kill(self.roots[0].pid, 0)
        assert self.roots[0].pid not in callers_fixture.ACTIVE
        assert self.unrelated.poll() is None
        os.kill(self.unrelated.pid, 0)
        states = _lifecycle_states([self.unrelated.pid])
        assert len(states) == 1 and "Z" not in states[0]["state"]
        record("A02-after-process-states", {"unrelated": states, "strict_owned_absence": True})

    def rescue(self) -> None:
        # No ps dependency and no remembered-child PID signal. Recovery is separate
        # from the fixture's outcome; ACTIVE changes only after actual proof.
        self.stop.touch()
        self.unrelated_stop.touch()
        rescue_errors: list[Exception] = []
        try:
            for process in [*self.roots, self.unrelated]:
                try:
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=2)
                    stdout, stderr = self.native_communicate(process, timeout=1)
                    record(
                        "A02-rescue-native",
                        {
                            "pid": process.pid,
                            "status": process.returncode,
                            "stdout": stdout,
                            "stderr": stderr,
                        },
                    )
                except Exception as error:
                    rescue_errors.append(error)
        finally:
            if self.child_pid is None and self.parent_identity.exists():
                self.child_pid = int(json.loads(self.parent_identity.read_text())["child"])
            if self.child_pid is not None:
                deadline = time.monotonic() + 22
                while time.monotonic() < deadline:
                    try:
                        os.kill(self.child_pid, 0)
                    except ProcessLookupError:
                        break
                    time.sleep(0.02)
                with pytest.raises(ProcessLookupError):
                    os.kill(self.child_pid, 0)
                for process in self.roots:
                    assert process.returncode is not None
                    with pytest.raises(ProcessLookupError):
                        os.kill(process.pid, 0)
                    # Only release this test's guard after independent disappearance.
                    callers_fixture.ACTIVE.discard(process.pid)
            elif self.roots:
                raise AssertionError("Tooling blocker: rescue lacks owned child identity")
        if rescue_errors:
            raise ExceptionGroup("A02 bounded rescue incomplete", rescue_errors)


@contextlib.contextmanager
def _owned_lifecycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, separate: bool, mode: str, status: int = 0
) -> Iterator[_OwnedLifecycle]:
    lifecycle = _OwnedLifecycle(tmp_path / "processes", separate, mode, status)
    try:
        with monkeypatch.context() as patch:
            lifecycle.install(patch)
            yield lifecycle
    finally:
        lifecycle.rescue()


@pytest.mark.parametrize("status", [0, 23])
def test_owned_session_native_status_streams_and_disposable_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """L01/L02: independent native streams/status and cache inode/bytes preservation."""
    with (
        _disposable_lifecycle_cache(tmp_path, monkeypatch),
        _owned_lifecycle(
            tmp_path, monkeypatch, separate=False, mode="complete", status=status
        ) as life,
    ):
        observation: dict[str, Any] = {}
        result = invoke([sys.executable, life.parent], timeout=6, observation=observation)
        assert result.returncode == status
        assert result.stdout == "A02-parent-out\nA02-child-out\n"
        assert result.stderr == "A02-parent-err\nA02-child-err\n"
        assert observation["status"] == status and observation["outer_timeout"] is False
        life.assert_stopped()


@pytest.mark.parametrize("separate", [False, True])
def test_owned_session_interruption_and_unrelated_process_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, separate: bool
) -> None:
    """L03/L06: real session-owned descendants disappear before disposable restoration."""
    with (
        _disposable_lifecycle_cache(tmp_path, monkeypatch),
        _owned_lifecycle(tmp_path, monkeypatch, separate=separate, mode="interrupt") as life,
    ):
        with pytest.raises(RuntimeError) as caught:
            invoke([sys.executable, life.parent], timeout=6)
        assert caught.value is life.failure
        life.assert_stopped()


@pytest.mark.parametrize("separate", [False, True])
def test_owned_session_actual_outer_timeout_before_disposable_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, separate: bool
) -> None:
    """L04: actual wait expiration remains nonwitness failure after strict cleanup."""
    with (
        _disposable_lifecycle_cache(tmp_path, monkeypatch),
        _owned_lifecycle(tmp_path, monkeypatch, separate=separate, mode="timeout") as life,
    ):
        with pytest.raises(
            AssertionError, match="^Tooling nonwitness: supported outer wait expired$"
        ):
            invoke([sys.executable, life.parent], timeout=0.15)
        life.assert_stopped()
        observations = list((callers_fixture.RUN / "observations").glob("command-*.json"))
        assert len(observations) == 1
        assert json.loads(observations[0].read_text())["outer_timeout"] is True


def _lifecycle_process_query(args: Any, executable: Any = None) -> bool:
    """Select public ps calls independently of executable path or query options."""
    command = executable
    if command is None:
        command = args[0] if isinstance(args, (list, tuple)) and args else args
    return (
        isinstance(command, (str, bytes, os.PathLike)) and Path(os.fsdecode(command)).name == "ps"
    )


def _lifecycle_cleanup_snapshot(life: _OwnedLifecycle) -> dict[str, Any]:
    """Observe actual post-cleanup state through an independent public observer."""
    assert life.child_pid is not None and life.roots
    pids = {"parent": life.roots[0].pid, "child": life.child_pid, "unrelated": life.unrelated.pid}
    # The saved public run function belongs to the test's external observer. It
    # does not supply state to invoke or disable its injected observation fault.
    observed = life.native_run(
        ["ps", "-p", ",".join(map(str, pids.values())), "-o", "pid=,ppid=,pgid=,stat="],
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert observed.returncode in (0, 1)
    states = []
    for line in observed.stdout.splitlines():
        pid, parent, group, state = line.split()
        states.append({"pid": int(pid), "ppid": int(parent), "pgid": int(group), "state": state})
    present = {}
    for name, pid in pids.items():
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            present[name] = False
        else:
            present[name] = True
    snapshot = {
        "pids": pids,
        "present": present,
        "states": states,
        "observer_status": observed.returncode,
        "active": sorted(callers_fixture.ACTIVE),
        "injected_denials": list(life.observer_denials),
    }
    record("A02-independent-cleanup-snapshot", snapshot)
    assert present["unrelated"] and life.unrelated.poll() is None
    assert os.getsid(life.unrelated.pid) != life.roots[0].pid
    assert any(entry["pid"] == life.unrelated.pid and "Z" not in entry["state"] for entry in states)
    return snapshot


def test_owned_session_unproven_cleanup_retains_guard_and_disposable_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """L05: refuse unproven cleanup; permit independently proved safe cleanup."""
    with _disposable_lifecycle_cache(tmp_path, monkeypatch) as reservation:
        before = inventory(reservation.backup)
        inode, mode = reservation.backup.stat().st_ino, reservation.backup.stat().st_mode
        fixture_inode = callers_fixture.CACHE.stat().st_ino
        with _owned_lifecycle(
            tmp_path, monkeypatch, separate=True, mode="observation-failure"
        ) as life:
            with pytest.raises(RuntimeError) as caught:
                invoke([sys.executable, life.parent], timeout=6)
            assert caught.value is life.failure
            snapshot = _lifecycle_cleanup_snapshot(life)
            remaining = [name for name in ("parent", "child") if snapshot["present"][name]]
            unproven = bool(remaining) or life.roots[0].pid in callers_fixture.ACTIVE
            if unproven:
                # One surviving owned process is enough; neither PID is required
                # to survive when a lawful stronger strategy can prove cleanup.
                assert life.roots[0].pid in callers_fixture.ACTIVE
                with pytest.raises(
                    AssertionError, match="owned process cleanup incomplete; backup retained"
                ):
                    reservation.__exit__()
                assert reservation.lock.is_dir()
                assert (
                    json.loads(reservation.journal.read_text())["stage"]
                    == "BLOCKED-owned-processes-active"
                )
            else:
                for name in ("parent", "child"):
                    with pytest.raises(ProcessLookupError):
                        os.kill(snapshot["pids"][name], 0)
                assert life.roots[0].pid not in callers_fixture.ACTIVE
            assert inventory(reservation.backup) == before
            assert reservation.backup.stat().st_ino == inode
            assert reservation.backup.stat().st_mode == mode
            assert callers_fixture.CACHE.stat().st_ino == fixture_inode
            record(
                "A02-L05-outcome",
                {
                    "refusal_witness": unproven,
                    "remaining_owned": remaining,
                    "strict_owned_absence": not remaining,
                    "injected_denials": list(life.observer_denials),
                    "backup_inventory": inventory(reservation.backup),
                    "backup_inode": inode,
                    "backup_mode": mode,
                    "reserved_inode": fixture_inode,
                    "proof_gap": None
                    if unproven
                    else (
                        "Safe cleanup accepted; no L05 refusal witness in this run; "
                        "route lawful additional proof."
                    ),
                },
            )


def test_owned_session_start_failure_preserves_disposable_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Native launch rejection creates no false active ownership or cache loss."""
    before_active = set(callers_fixture.ACTIVE)
    with _disposable_lifecycle_cache(tmp_path, monkeypatch):
        with pytest.raises(FileNotFoundError):
            invoke([tmp_path / "missing-owned-executable"], timeout=1)
        assert before_active == callers_fixture.ACTIVE
