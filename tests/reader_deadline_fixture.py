"""Deadline-only driver and pre-rescue observer; shared callers remain unchanged."""

from __future__ import annotations

import contextlib
import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from shared_node_baseline_public_callers_fixture import ACTIVE, READER, ROOT, record

PARENT_SECONDS = 12
OUTER_SECONDS = 35


def deadline_driver(tmp: Path, timeout_attribute: str) -> Path:
    """Change one approved parent constant; the fetched script stays untouched."""
    driver = tmp / "deadline-parent.py"
    driver.write_text(
        "import importlib.util,sys\n"
        f"sys.argv=[{str(READER)!r}]\n"
        f"spec=importlib.util.spec_from_file_location('deadline_parent',{str(READER)!r})\n"
        "assert spec is not None and spec.loader is not None\n"
        "parent=importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name]=parent\n"
        "spec.loader.exec_module(parent)\n"
        f"assert getattr(parent,{timeout_attribute!r}) == 180\n"
        f"setattr(parent,{timeout_attribute!r},{PARENT_SECONDS})\n"
        "print(parent.prepare())\n"
    )
    return driver


def _process_table() -> dict[int, dict[str, Any]]:
    result = subprocess.run(
        ["ps", "-ww", "-axo", "pid=,ppid=,stat=,args="],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    return {
        int(parts[0]): {
            "parent": int(parts[1]),
            "state": parts[2],
            "command": parts[3],
        }
        for line in result.stdout.splitlines()
        if len(parts := line.split(maxsplit=3)) == 4
    }


def _session(table: dict[int, dict[str, Any]], leader: int) -> set[int]:
    owned = set()
    for pid in table:
        with contextlib.suppress(ProcessLookupError):
            if os.getsid(pid) == leader:
                owned.add(pid)
    return owned


def observe_deadline(
    driver: Path, env: dict[str, str], name: str
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    """Record parent exit and descendants before cleanup can send any signal.

    Invoke through source_free_check.py pytest: the direct Python driver and its
    genuine fetch child inherit that diagnostic environment. No inner harness
    gets an independent opportunity to kill a descendant before our snapshot.
    """
    command = [sys.executable, str(driver)]
    started = time.monotonic()
    observation: dict[str, Any] = {
        "argv": command,
        "outer_bound_s": OUTER_SECONDS,
        "rescue_signals": [],
        "cleanup_complete": False,
        "pre_rescue": None,
    }
    seen: set[int] = set()
    fetch_samples: list[dict[str, Any]] = []
    with (
        (driver.parent / "deadline-stdout.txt").open("w") as stdout,
        (driver.parent / "deadline-stderr.txt").open("w") as stderr,
    ):
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=stdout,
            stderr=stderr,
            text=True,
            start_new_session=True,
        )
        ACTIVE.add(process.pid)
        observation["pid"] = process.pid
        try:
            deadline = started + OUTER_SECONDS
            while process.poll() is None and time.monotonic() < deadline:
                table = _process_table()
                owned = _session(table, process.pid)
                seen.update(owned - {process.pid})
                for pid in owned - {process.pid}:
                    args = shlex.split(table[pid]["command"])
                    if str(READER) in args and "--fetch" in args and name in args:
                        fetch_samples.append({"pid": pid, "at": time.monotonic()})
                time.sleep(0.1)
            status = process.poll()
            observed_at = time.monotonic()
            table = _process_table()
            owned = _session(table, process.pid)
            remaining = (seen & table.keys()) | (owned - {process.pid})
            snapshot = {
                "observed_at": observed_at,
                "duration_s": observed_at - started,
                "outer_timeout": status is None,
                "status": status,
                "fetch_samples": fetch_samples,
                "observed_child_pids": sorted(seen),
                "remaining_child_states": {
                    str(pid): table[pid]["state"] for pid in sorted(remaining)
                },
                "remaining_session_pids": sorted(owned),
                "rescue_signals_before_snapshot": list(observation["rescue_signals"]),
            }
            observation["pre_rescue"] = snapshot
            # This immutable record is written before entering rescue cleanup.
            record("deadline-pre-rescue", snapshot)
        finally:
            # Rescue preserves the cache reservation on failure; it never supplies
            # cancellation evidence. Zombie entries remain evidence until reaped.
            for sig, bound in ((signal.SIGTERM, 3), (signal.SIGKILL, 7)):
                deadline = time.monotonic() + bound
                signalled: set[int] = set()
                while time.monotonic() < deadline:
                    process.poll()
                    table = _process_table()
                    owned = _session(table, process.pid)
                    remaining_seen = seen & table.keys()
                    if not owned and not remaining_seen:
                        process.wait(timeout=1)
                        observation["cleanup_complete"] = True
                        ACTIVE.discard(process.pid)
                        break
                    parents = {table[pid]["parent"] for pid in owned}
                    for pid in owned - parents - signalled:
                        if "Z" in table[pid]["state"]:
                            continue
                        with contextlib.suppress(ProcessLookupError):
                            if os.getsid(pid) == process.pid:
                                os.kill(pid, sig)
                                observation["rescue_signals"].append(
                                    {"pid": pid, "signal": sig.name, "at": time.monotonic()}
                                )
                        signalled.add(pid)
                    time.sleep(0.05)
                if observation["cleanup_complete"]:
                    break
            record("deadline-observer", observation)
            if not observation["cleanup_complete"]:
                raise AssertionError(
                    "Tooling blocker: deadline owned processes remain; cache restore blocked"
                )
    result = subprocess.CompletedProcess(
        command,
        process.returncode,
        (driver.parent / "deadline-stdout.txt").read_text(),
        (driver.parent / "deadline-stderr.txt").read_text(),
    )
    record(
        "deadline-output",
        {"status": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
    )
    return result, observation
