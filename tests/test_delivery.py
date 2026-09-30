"""Public console-entry tests for the approved delivery doctor slice."""

import json
import os
import re
import stat
import subprocess
import sys
import sysconfig
import tomllib
from pathlib import Path

import pytest

DELIVERY = Path(sysconfig.get_path("scripts")) / "delivery"


@pytest.fixture
def caller_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "caller-repo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# Caller repository instructions\n")
    (repo / "existing.txt").write_text("Keep this file unchanged.\n")
    return repo


@pytest.fixture
def codex_harness(tmp_path: Path) -> tuple[dict[str, str], Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "codex-calls.jsonl"
    codex = bin_dir / "codex"
    codex.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "call = {'argv': sys.argv[1:], 'cwd': os.getcwd(), 'stdin': sys.stdin.read()}\n"
        "with Path(os.environ['SIMRECON_TEST_CODEX_LOG']).open('a') as stream:\n"
        "    stream.write(json.dumps(call) + '\\n')\n"
        "print('controlled doctor stdout')\n"
        "print('controlled doctor stderr', file=sys.stderr)\n"
        "sys.exit(int(os.environ['SIMRECON_TEST_CODEX_EXIT']))\n"
    )
    codex.chmod(codex.stat().st_mode | stat.S_IXUSR)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["SIMRECON_TEST_CODEX_LOG"] = str(log)
    env["SIMRECON_TEST_CODEX_EXIT"] = "0"
    return env, log


def run_delivery(*args: str, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(DELIVERY), *args],
        cwd=cwd,
        env=env,
        input="",
        text=True,
        capture_output=True,
        check=False,
    )


def calls_from(log: Path) -> list[dict[str, str | list[str]]]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines()]


def option_values(argv: list[str], *options: str) -> list[str]:
    values = []
    for index, token in enumerate(argv):
        if token in options and index + 1 < len(argv):
            values.append(argv[index + 1])
        for option in options:
            if token.startswith(f"{option}="):
                values.append(token.split("=", 1)[1])
    return values


# Only interpret native options relevant to this public invocation boundary.
VALUE_OPTIONS = {
    "--sandbox",
    "-s",
    "--config",
    "-c",
    "--model",
    "-m",
    "--cd",
    "-C",
    "--disable",
    "--enable",
    "--profile",
    "-p",
    "--output-last-message",
    "-o",
    "--output-schema",
    "--color",
    "--add-dir",
}
FLAG_OPTIONS = {
    "--approve-for-me",
    "--ignore-user-config",
    "--dangerously-bypass-approvals-and-sandbox",
    "--yolo",
    "--skip-git-repo-check",
    "--json",
    "--ephemeral",
    "--full-auto",
}


def native_command_and_prompt(call: dict[str, str | list[str]]) -> tuple[list[str], str]:
    argv = call["argv"]
    assert isinstance(argv, list)
    position = 0
    command = None
    options = []
    prompts = []
    while position < len(argv):
        token = argv[position]
        if token in VALUE_OPTIONS:
            assert position + 1 < len(argv)
            options.extend(argv[position : position + 2])
            position += 2
        elif (
            any(token.startswith(f"{option}=") for option in VALUE_OPTIONS) or token in FLAG_OPTIONS
        ):
            options.append(token)
            position += 1
        elif token == "--":
            assert command == "exec"
            prompts.extend(argv[position + 1 :])
            break
        elif token.startswith("-") and token != "-":
            pytest.fail(f"Unexpected native Codex option: {token}")
        elif command is None:
            command = token
            position += 1
        else:
            prompts.append(token)
            position += 1
    assert command == "exec"
    assert len(prompts) <= 1, "Native exec accepts one prompt argument"
    assert not prompts or prompts[0] not in {"resume", "fork", "review", "help"}
    prompt = prompts[0] if prompts and prompts[0] != "-" else ""
    prompt = f"{prompt} {call['stdin']}".strip()
    return options, prompt


def assert_native_doctor_call(
    call: dict[str, str | list[str]], sandbox: str, caller_repo: Path
) -> str:
    options, prompt = native_command_and_prompt(call)
    assert call["cwd"] == str(caller_repo)
    assert all(
        (caller_repo / value).resolve() == caller_repo.resolve()
        for value in option_values(options, "-C", "--cd")
    )
    modes = option_values(options, "--sandbox", "-s")
    disabled = option_values(options, "--disable")
    enabled = option_values(options, "--enable")
    for config in option_values(options, "--config", "-c"):
        key, separator, value = config.partition("=")
        assert separator, "Native config overrides require key=value"
        key = key.strip()
        try:
            parsed = tomllib.loads(f"value = {value}")["value"]
        except tomllib.TOMLDecodeError:
            parsed = value.strip()
        if key == "sandbox_mode":
            modes.append(parsed)
        elif key in {"features.memories", "features.multi_agent"}:
            assert parsed is False, f"Optional feature enabled: {key}"
            disabled.append(key.removeprefix("features."))
        else:
            # Unknown policy overrides cannot establish a controlled sandbox.
            assert key in {"model", "model_reasoning_effort"}, f"Uncontrolled config: {key}"
    assert "memories" in disabled
    assert "multi_agent" in disabled
    assert not {"memories", "multi_agent"}.intersection(enabled)
    assert "--dangerously-bypass-approvals-and-sandbox" not in options
    assert "--yolo" not in options
    assert "--full-auto" not in options
    assert not option_values(options, "--profile", "-p")
    assert all(mode == sandbox for mode in modes)
    if sandbox == "read-only":
        assert modes, "Report-only requires explicit native read-only mode"
        assert "--approve-for-me" not in options
        assert not option_values(options, "--add-dir")
    else:
        assert modes or "--approve-for-me" in options
    assert "review-work" in prompt
    assert re.search(r"\bdoctor\b", prompt, re.IGNORECASE)
    assert "docs/agentic-software-delivery-v1.0/DOCTOR-PROMPT.md" in prompt
    return prompt


def repository_files(repo: Path) -> dict[str, tuple[int, bytes | str | None]]:
    snapshot = {}
    for path in repo.rglob("*"):
        content = (
            os.readlink(path)
            if path.is_symlink()
            else path.read_bytes()
            if path.is_file()
            else None
        )
        snapshot[str(path.relative_to(repo))] = (path.lstat().st_mode, content)
    return snapshot


def assert_controlled_output(result: subprocess.CompletedProcess[str], status: int) -> None:
    assert result.returncode == status
    assert "controlled doctor stdout" in result.stdout
    assert "controlled doctor stderr" in result.stderr


def test_doctor_invokes_one_write_capable_native_run(
    codex_harness: tuple[dict[str, str], Path],
    caller_repo: Path,
) -> None:
    env, log = codex_harness

    result = run_delivery("doctor", env=env, cwd=caller_repo)

    assert_controlled_output(result, 0)
    calls = calls_from(log)
    assert len(calls) == 1
    assert_native_doctor_call(calls[0], "workspace-write", caller_repo)


def test_doctor_check_uses_read_only_native_run(
    codex_harness: tuple[dict[str, str], Path], caller_repo: Path
) -> None:
    env, log = codex_harness
    before = repository_files(caller_repo)

    result = run_delivery("doctor", "--check", env=env, cwd=caller_repo)

    assert_controlled_output(result, 0)
    calls = calls_from(log)
    assert len(calls) == 1
    prompt = assert_native_doctor_call(calls[0], "read-only", caller_repo)
    assert re.search(r"--check|report.only|read.only", prompt, re.IGNORECASE)
    assert repository_files(caller_repo) == before


def test_doctor_rejects_unsupported_flag_without_invocation(
    codex_harness: tuple[dict[str, str], Path],
    caller_repo: Path,
) -> None:
    env, log = codex_harness

    result = run_delivery("doctor", "--unsupported", env=env, cwd=caller_repo)

    assert result.returncode == 2
    assert "--unsupported" in result.stderr
    assert "usage" in result.stderr.lower() or "unrecognized" in result.stderr.lower()
    assert calls_from(log) == []


def test_doctor_forwards_native_failure_without_retry(
    codex_harness: tuple[dict[str, str], Path],
    caller_repo: Path,
) -> None:
    env, log = codex_harness
    env["SIMRECON_TEST_CODEX_EXIT"] = "7"

    result = run_delivery("doctor", env=env, cwd=caller_repo)

    assert_controlled_output(result, 7)
    calls = calls_from(log)
    assert len(calls) == 1
    assert_native_doctor_call(calls[0], "workspace-write", caller_repo)


def test_doctor_reports_missing_codex_on_path(tmp_path: Path, caller_repo: Path) -> None:
    empty_bin = tmp_path / "empty-bin"
    empty_bin.mkdir()
    env = os.environ.copy()
    env["PATH"] = str(empty_bin)

    result = run_delivery("doctor", env=env, cwd=caller_repo)

    assert result.returncode == 127
    assert "codex" in result.stderr.lower()
    assert "path" in result.stderr.lower()
