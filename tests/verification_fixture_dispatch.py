"""Small POSIX external fixture dispatch and lossless actual-argument records.

Inert commands use the shell. Dynamic measurements, native APIs and late
filesystem actions keep ordinary qualified Python startup and instrumentation.
These records observe executed commands; they never predict a phase ledger.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


def append_record(path: Path, fields: list[str]) -> None:
    with path.open("ab") as stream:
        stream.write(b"\0".join(os.fsencode(item) for item in [str(len(fields)), *fields]) + b"\0")


def read_records(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    parts = path.read_bytes().split(b"\0")
    assert parts.pop() == b"", "incomplete actual-argument record"
    result = []
    index = 0
    while index < len(parts):
        count = int(parts[index])
        assert count >= 0 and index + count < len(parts), "incomplete actual-argument record"
        result.append([os.fsdecode(value) for value in parts[index + 1 : index + count + 1]])
        index += count + 1
    return result


def read_calls(path: Path) -> list[list[str]]:
    if not path.exists():
        return []
    if b"\0" in path.read_bytes():
        return read_records(path)
    return [json.loads(line) for line in path.read_text().splitlines()]


def read_measurements(path: Path) -> list[dict[str, Any]]:
    return [
        {"path": fields[0] or None, "run_id": fields[1] or None, "args": fields[2:]}
        for fields in read_records(path)
    ]


def read_evidence_calls(path: Path) -> list[dict[str, Any]]:
    result = []
    for fields in read_records(path):
        if fields[0] == "json":
            result.append(json.loads(fields[1]))
            continue
        _, phase, stdout, stderr, measurement, run_id, *argv = fields
        result.append(
            dict(
                argv=argv,
                phase=phase or None,
                status=0,
                stdout=stdout,
                stderr=stderr,
                measurement_path=measurement or None,
                run_id=run_id or None,
                snapshots={},
                action=None,
                retained_logs={},
                blocked_log=None,
                wheel_members={},
            )
        )
    return result


def install_dispatch(
    target: Path,
    python_body: str,
    *,
    profile: str = "receipt",
    dynamic_phases: tuple[str, ...] = (),
) -> None:
    """Install an actual external command with a narrowly selected Python fallback."""
    driver = target.with_name(target.name + "-dynamic.py")
    quote = shlex.quote
    fallback = f'exec {quote(sys.executable)} {quote(str(driver))} "$@"'
    # Keep argv[0] equal to the selected command, including in the Python fallback.
    driver.write_text(
        "import sys\nsys.argv[0] = " + repr(str(target)) + "\n" + python_body,
        encoding="utf-8",
    )
    shell = """#!/bin/sh
set -eu
export RECEIPT_TRACE_FORMAT=nul
record() { destination=$1; shift; printf '%s\\000' "$#" "$@" >> "$destination"; }
phase=''
for arg do
    case "$arg" in
    sync|coverage-clean|lint|format|types|tests|coverage-combine|coverage-json|coverage-html|\
coverage-report|wheel|wheel-import|audit) phase=$arg; break;;
    esac
done
"""
    if dynamic_phases:
        shell += 'case "$phase" in ' + "|".join(dynamic_phases) + ") " + fallback + ";; esac\n"
    if profile in {"receipt", "measurement", "output", "hash"}:
        # Some keepers seed stale outputs by executing a command directly,
        # before invoke() prepares immutable templates. Preserve that caller.
        shell += (
            'if [ -z "${RECEIPT_FIXTURE_INPUTS:-}" ]; then\n'
            '    case "$phase" in coverage-json|wheel) ' + fallback + ";; esac\nfi\n"
        )
        if profile == "measurement":
            shell += f'case "$phase" in tests|audit) {fallback};; esac\n'
            shell += (
                'if [ "$phase" = types ] && '
                '[ "${EXPORT_FIXTURE_MODE:-}" = redirect-before-tests ]; then\n'
                + fallback
                + "\nfi\n"
            )
        if profile == "output":
            shell += (
                'if [ -n "$phase" ] && [ "$phase" = "${OUTPUT_PROTECTION_PHASE:-}" ]; then\n'
                + fallback
                + "\nfi\n"
            )
        if profile == "hash":
            shell += f'if [ "$phase" = wheel ]; then {fallback}; fi\n'
        shell += f"""case "$phase:${{RECEIPT_FIXTURE_MODE:-complete}}" in
tests:tracked-change|tests:commit-change|tests:input-change|audit:unavailable-final-identity)
    {fallback};;
esac
"""
        if profile == "measurement":
            shell += (
                'record measurement-calls.jsonl "${SIMRECON_MEASUREMENTS_PATH:-}" '
                '"${SIMRECON_MEASUREMENTS_RUN_ID:-}" "$@"\n'
            )
        shell += """if [ "$#" = 1 ] && [ "$1" = --version ]; then
    printf 'fixture tool 1.0\\n'; exit 0
fi
record calls.jsonl "$@"
"""
        if target.name == "uv":
            shell += """tool=''
for arg do case "$arg" in ruff|pyright|coverage|pytest) tool=$arg;; esac; done
last=''; for arg do last=$arg; done
if [ -n "$tool" ] && [ "$last" = --version ]; then
    printf '%s fixture 1.0\\n' "$tool"
else
    printf 'controlled uv command\\n'
fi
exit 0
"""
        shell += """printf 'controlled phase %s\\n' "$phase"
mode=${RECEIPT_FIXTURE_MODE:-complete}
if [ "$phase:$mode" = lint:command-failure ]; then
    printf 'controlled failure diagnostic\\n' >&2; exit 23
fi
case "$phase" in
coverage-clean) rm -rf artifacts/coverage dist;;
coverage-json)
    if [ "$mode" != missing-json ]; then
        mkdir -p artifacts/coverage
        source="$RECEIPT_FIXTURE_INPUTS/artifacts/coverage/coverage.json"
        cp "$source" artifacts/coverage/coverage.json
        if [ "$mode" = partial-json-failure ]; then
            printf 'controlled partial JSON failure\\n' >&2; exit 29
        fi
    fi;;
coverage-html)
    if [ "$mode" != missing-html ]; then
        mkdir -p artifacts/coverage/html
        printf '<html>controlled coverage</html>' > artifacts/coverage/html/index.html
    fi;;
wheel)
    if [ "$mode" != missing-wheel ]; then
        mkdir -p dist
        for source in "$RECEIPT_FIXTURE_INPUTS"/dist/*.whl; do cp "$source" dist/; done
    fi
    if [ "$mode" = wheel-build-failure ]; then
        printf 'controlled wheel build failure\\n' >&2; exit 31
    fi;;
esac
"""
    elif profile == "evidence":
        shell += """if [ -z "$phase" ]; then
    if [ "$#" = 1 ] && [ "$1" = --version ]; then printf 'fixture tool 1.0\\n'; exit 0; fi
"""
        shell += fallback + "\nfi\n"
        # Only inert phases are handled here. Reports/actions keep Python observers.
        shell += (
            'case "$phase" in tests|coverage-json|coverage-html|wheel|audit) '
            + fallback
            + ";; esac\n"
        )
        shell += (
            'if [ "${EVIDENCE_NATIVE:-0}" = 1 ] && [ "$phase" = coverage-combine ]; then\n'
            + fallback
            + "\nfi\n"
        )
        shell += """record calls.jsonl "$@"
path=${SIMRECON_MEASUREMENTS_PATH:-}
run_id=${SIMRECON_MEASUREMENTS_RUN_ID:-}
record measurement-calls.jsonl "$path" "$run_id" "$@"
stdout=$(printf 'controlled phase %s\\n%s stdout %s' "$phase" "$EVIDENCE_TOKEN" "$phase")
stderr=$(printf '%s stderr %s' "$EVIDENCE_TOKEN" "$phase")
if [ "$phase" = coverage-clean ]; then rm -rf artifacts/coverage dist; fi
record evidence-calls.jsonl fast "$phase" "$stdout
" "$stderr
" "${SIMRECON_MEASUREMENTS_PATH:-}" "${SIMRECON_MEASUREMENTS_RUN_ID:-}" "$0" "$@"
printf '%s\\n' "$stdout"
printf '%s\\n' "$stderr" >&2
"""
    else:
        raise ValueError(profile)
    target.write_text(shell, encoding="utf-8")
    target.chmod(0o755)


def install_native_dispatch(
    target: Path,
    driver: Path,
    *,
    dynamic_phases: tuple[str, ...],
    external: bool = False,
) -> None:
    """Keep native/stateful commands live; emit only inert phase text in shell."""
    fallback = f'exec {shlex.quote(sys.executable)} {shlex.quote(str(driver))} "$@"'
    shell = """#!/bin/sh
set -eu
record() { destination=$1; shift; printf '%s\\000' "$#" "$@" >> "$destination"; }
for arg do
    if [ "$arg" = --version ]; then
"""
    shell += (
        "        printf '"
        + ("A13 disposable phase driver 1" if external else "A08 fixture make 1")
        + "\\n'; exit 0\n    fi\ndone\nphase=''\n"
    )
    shell += """for arg do
    case "$arg" in -*|*=*) continue;; *) phase=$arg; break;; esac
done
"""
    shell += 'case "$phase" in ' + "|".join(dynamic_phases) + ") " + fallback + ";; esac\n"
    if external:
        shell += """record "$A13_OBSERVATIONS/trace.argv" "$phase" "$@"
printf '%s:%s\\n' "$A13_NONCE" "$phase" > "$A13_OBSERVATIONS/$phase.txt"
if [ "$A15_OUTPUT_STREAM" = stderr ]; then
    cat "$A13_OBSERVATIONS/$phase.txt" >&2
else
    cat "$A13_OBSERVATIONS/$phase.txt"
fi
"""
    else:
        shell += """record phase-trace.argv "$phase" "$@"
printf 'A08 actual disposable phase %s\\n' "$phase"
"""
    target.write_text(shell, encoding="utf-8")
    target.chmod(0o700)
