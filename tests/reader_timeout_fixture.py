"""Caller-side real-timeout qualification; no runtime source inspection."""

from __future__ import annotations

import hashlib
import json
import os
import runpy
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


def process_table(run: Any = subprocess.run) -> dict[int, dict[str, Any]]:
    result = run(
        ["/bin/ps", "-axo", "pid=,ppid=,stat=,lstart=,comm="],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    table = {}
    for line in result.stdout.splitlines():
        fields = line.split(maxsplit=8)
        if len(fields) == 9:
            pid, parent, state = fields[:3]
            table[int(pid)] = {
                "pid": int(pid),
                "parent": int(parent),
                "state": state,
                "start": " ".join(fields[3:8]),
                "executable": fields[8],
            }
    return table


def destination(command: Any, cache: Path, protected: set[str]) -> Path | None:
    """Qualify a current scoped output, independently of timeout/argument order."""
    if not isinstance(command, (list, tuple)):
        return None
    matches = []
    for argument in command:
        if not isinstance(argument, (str, os.PathLike)):
            continue
        # Never parse or display inline source. Only absolute path arguments qualify.
        text = os.fspath(argument)
        if not text.startswith(str(cache) + os.sep):
            continue
        path = Path(text)
        if (
            path.parent == cache
            and path.name not in protected
            and path.name.endswith(".download")
            and path.is_file()
            and not path.is_symlink()
        ):
            matches.append(path)
    return matches[0] if len(matches) == 1 else None


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def qualified_live_child(initial: dict[str, Any], current: dict[str, Any]) -> bool:
    """Qualify progress only with original executable display and live identity."""
    if any(current[key] != initial[key] for key in ("pid", "start", "parent")):
        raise AssertionError("known download PID identity changed")
    # ps executable display can change during exit even before its state says Z.
    # Such a row remains present, but supplies no further live/progress proof.
    return "Z" not in current["state"] and current["executable"] == initial["executable"]


def run_reader(
    reader: Path,
    cache: Path,
    authentic: Path,
    events: Path,
    protected: set[str],
    effective: float | None,
) -> None:
    """Run the actual reader with only the selected real run timeout adapted."""
    real_run = subprocess.run
    lock = threading.Lock()

    def emit(kind: str, **fields: Any) -> None:
        with lock, events.open("a") as stream:
            stream.write(json.dumps({"event": kind, "at": time.monotonic(), **fields}) + "\n")

    def adapted(*args: Any, **kwargs: Any) -> Any:
        command = args[0] if args else kwargs.get("args")
        selected = destination(command, cache, protected)
        forwarded = dict(kwargs)
        original = kwargs.get("timeout")
        if selected is not None and effective is not None:
            forwarded["timeout"] = effective
        assert all(forwarded[key] is value for key, value in kwargs.items() if key != "timeout")
        if selected is None or effective is None:
            assert forwarded == kwargs
        metadata = {
            "selected": selected is not None,
            "configured_timeout": original,
            "effective_timeout": forwarded.get("timeout"),
            "executable": os.fspath(command[0]) if isinstance(command, (list, tuple)) else None,
            "argv_count": len(command) if isinstance(command, (list, tuple)) else None,
            "argv_sha256": hashlib.sha256(repr(command).encode()).hexdigest(),
            "kwargs_keys": sorted(kwargs),
            "other_kwargs_same_objects": True,
            "driver_pid": os.getpid(),
        }
        emit("call", **metadata)
        stop = threading.Event()
        observer_errors = []

        def observe() -> None:
            try:
                payload = authentic.read_bytes()
                last_size = 0
                identity = None
                while not stop.is_set():
                    table = process_table(real_run)
                    candidates = [
                        row
                        for row in table.values()
                        if row["parent"] == os.getpid() and Path(row["executable"]).name != "ps"
                    ]
                    live = False
                    if identity is None:
                        if len(candidates) > 1:
                            raise AssertionError("ambiguous initial download child identity")
                        if len(candidates) == 1:
                            row = candidates[0]
                            assert "Z" not in row["state"], "initial download child is zombie"
                            identity = dict(row)
                            emit("initial-child", **identity)
                    if identity is not None:
                        row = table.get(identity["pid"])
                        if row is not None:
                            # comm legitimately becomes <defunct> on exit. Record all
                            # fields before validating, including a failed transition.
                            emit("child-state", initial=identity, current=row)
                            live = qualified_live_child(identity, row)
                            if live:
                                emit("live-child", **row)
                        else:
                            emit(
                                "known-child-absent",
                                pid=identity["pid"],
                                other_direct_children=candidates,
                            )
                    if selected is not None and selected.exists() and live:
                        received = selected.read_bytes()
                        if len(received) > last_size:
                            assert received == payload[: len(received)]
                            assert 0 < len(received) < len(payload)
                            emit(
                                "received",
                                bytes=len(received),
                                sha256=hashlib.sha256(received).hexdigest(),
                                child=dict(identity) if identity else None,
                            )
                            last_size = len(received)
                    stop.wait(0.1)
            except BaseException as error:
                observer_errors.append(type(error).__name__ + ": " + str(error))

        thread = None
        if selected is not None and effective is not None:
            thread = threading.Thread(target=observe)
            thread.start()
        started = time.monotonic()
        try:
            result = real_run(*args, **forwarded)
            emit("returned", **metadata, status=result.returncode)
            return result
        except subprocess.TimeoutExpired as error:
            emit(
                "native-timeout",
                **metadata,
                category=type(error).__name__,
                exception_timeout=error.timeout,
                elapsed_s=time.monotonic() - started,
            )
            try:
                raise
            except subprocess.TimeoutExpired as same:
                assert same is error
                emit("same-exception-reraised", identity_equal=True)
                raise
        finally:
            stop.set()
            if thread is not None:
                thread.join(timeout=6)
                emit("observer-finished", stopped=not thread.is_alive(), errors=observer_errors)
                assert not thread.is_alive()

    subprocess.run = adapted
    sys.argv = [str(reader)]
    try:
        runpy.run_path(str(reader), run_name="__main__")
    finally:
        emit("application-finished")
        subprocess.run = real_run


def driver(
    path: Path,
    reader: Path,
    cache: Path,
    authentic: Path,
    protected: set[str],
    effective: float | None,
) -> Path:
    events = path.with_suffix(".jsonl")
    path.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(Path(__file__).parent)!r})\n"
        "from pathlib import Path\n"
        "from reader_timeout_fixture import run_reader\n"
        f"run_reader(Path({str(reader)!r}), Path({str(cache)!r}), "
        f"Path({str(authentic)!r}), Path({str(events)!r}), {protected!r}, {effective!r})\n"
    )
    return events


def before_rescue(events: Path, cache: Path, name: str, other: str) -> dict[str, Any]:
    """Read-only same-invocation state before the harness can signal anything."""
    observed = read_events(events)
    identities = {row["pid"]: row for row in observed if row["event"] == "live-child"}
    table = process_table()
    return {
        "at": time.monotonic(),
        "events": observed,
        "known_children": identities,
        "remaining_known_children": {pid: table[pid] for pid in identities if pid in table},
        "target_exists": (cache / name).exists(),
        "manifest_exists": (cache / "inputs.json").exists(),
        "other_sha256": hashlib.sha256((cache / other).read_bytes()).hexdigest(),
        "entries": sorted(path.name for path in cache.iterdir()),
        "limit": (
            "Strict PID absence; zombies/reused PID count present. "
            "Start stamp has second resolution; no kernel birth handle."
        ),
    }
