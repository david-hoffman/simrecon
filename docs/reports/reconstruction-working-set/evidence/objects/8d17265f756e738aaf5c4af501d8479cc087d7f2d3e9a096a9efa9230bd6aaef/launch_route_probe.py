"""One selected tiny launch-route probe; source-only until exact coordinator release.

No setsid spawn attribute, fork/fallback matrix, numerical import or workflow.
The original failed Q1 attempt and its unknown terminal usage remain untouched.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
ROOT = REPORT.parents[2]

BOOTSTRAP = r"""import json
import os
import sys

fd = int(sys.argv[1])
nonce = sys.argv[2]
os.setsid()
message = json.dumps({"role":"bootstrap", "pid":os.getpid(), "ppid":os.getppid(),
    "pgid":os.getpgrp(), "session_id":os.getsid(0), "nonce":nonce,
    "executable":os.readlink("/proc/self/exe")}).encode() + b"\n"
if len(message) > 512:
    raise RuntimeError("bootstrap readiness exceeds frozen bound")
if os.write(fd, message) != len(message):
    raise RuntimeError("incomplete bootstrap readiness write")
os.close(fd)
os.execve(sys.argv[3], [sys.argv[3], "-c", sys.argv[4], nonce], os.environ.copy())
"""
TARGET = r"""import json
import os
import sys

print(json.dumps({"role":"target", "pid":os.getpid(), "ppid":os.getppid(),
    "pgid":os.getpgrp(), "session_id":os.getsid(0), "nonce":sys.argv[1],
    "executable":os.readlink("/proc/self/exe"),
    "cgroup_namespace":os.readlink("/proc/self/ns/cgroup")}), flush=True)
raise SystemExit(0)
"""


def require(value, message):
    """Reject missing/changed evidence and stop without selecting another route."""
    if not value:
        raise RuntimeError(message)


def write(path, value):
    """Write durable probe metadata; no field is a scientific result."""
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def direct_signal(owner, signum):
    """Signal only an exact still-owned unreaped PID, never its process group."""
    if owner.collect() is not None:
        return {"signal":signum, "delivery":"already_terminal"}
    require(not owner.wait_lost, "wait ownership lost; signal forbidden")
    try:
        os.kill(owner.pid, signum)
        return {"signal":signum, "delivery":"direct_pid_sent",
                "monotonic_ns":time.monotonic_ns()}
    except ProcessLookupError:
        return {"signal":signum, "delivery":"absent_race"}


def direct_cleanup(owner, record, bounds):
    """Bound exact-PID TERM/KILL/reap; missing terminal usage remains explicit."""
    if owner is None or owner.terminal is not None:
        return
    try:
        record["signals"].append(direct_signal(owner, signal.SIGTERM))
        until = time.monotonic() + bounds["term_grace_seconds"]
        while owner.collect() is None and time.monotonic() < until:
            time.sleep(bounds["poll_seconds"])
        if owner.terminal is None:
            record["signals"].append(direct_signal(owner, signal.SIGKILL))
            until = time.monotonic() + bounds["kill_reap_seconds"]
            while owner.collect() is None and time.monotonic() < until:
                time.sleep(bounds["poll_seconds"])
        if owner.terminal is None:
            record["cleanup_gap"] = "owned PID has no terminal wait4 after cleanup bound; block all further work"
    except BaseException as error:
        record["cleanup_gap"] = {"type":type(error).__name__, "message":str(error),
                                 "meaning":"ownership/terminal usage unresolved; block further work"}


def identities(grant, obs):
    """Check frozen source/fixture bytes without importing product code."""
    required = {
        "docs/reports/reconstruction-working-set/qualification/launch_route_probe.py",
        "docs/reports/reconstruction-working-set/qualification/launch-route-inventory.json",
        "docs/reports/reconstruction-working-set/observer.py",
        "docs/reports/reconstruction-working-set/run_attempt.py",
        "uv.lock",
    }
    require(required <= set(grant["source_sha256"]), "mandatory probe identity missing")
    found = {}
    for name in grant["source_sha256"]:
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), "probe identity outside worktree")
        found[name] = obs.digest(path)
    require(found == grant["source_sha256"], "frozen probe input changed")
    return found


def admit(args, grant, inventory, obs, method):
    """Require the one inspected route, fresh proof and conservative exposed margins."""
    require(grant["approved"] is True and grant["scope"] == "WS116-selected-launch-route-v1",
            "selected route is not released")
    require(grant["attempt_id"] == args.attempt_id, "attempt/grant mismatch")
    require(method.git("rev-parse", "HEAD") == grant["candidate_head"], "candidate HEAD changed")
    require(str(Path(sys.executable).resolve()) == grant["python_resolved"], "unpinned Python")
    require(grant["ownership_resolved"] is True, "prior ownership unresolved")
    require(grant["bounds"] == inventory["bounds"], "probe bounds differ from freeze")
    require(all(os.environ.get(key) == "1" for key in obs.THREADS), "startup thread controls missing")
    require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL, "SIGCHLD ownership unavailable")
    require(signal.getsignal(signal.SIGINT) is signal.default_int_handler, "default SIGINT handler required")
    require(isinstance(grant["nonce"], str) and 0 < len(grant["nonce"].encode()) <= 64,
            "nonce exceeds frozen readiness bound")
    require(hashlib.sha256(BOOTSTRAP.encode()).hexdigest() == inventory["bootstrap_sha256"] and
            hashlib.sha256(TARGET.encode()).hexdigest() == inventory["target_sha256"], "body digest mismatch")
    found = identities(grant, obs)
    cg = obs.cgroup_ancestors()
    require("error" not in cg, "missing observable domain")
    bounds = inventory["bounds"]
    for key in ("process_stop_bytes", "host_min_available_bytes"):
        require(grant[key] == bounds[key], "probe stop differs from frozen setting")
    for key in ("predicted_child_peak_bytes", "native_allocator_allowance_bytes", "reserve_bytes"):
        require(grant["resource_domain"][key] == bounds[key], "probe allowance/reserve changed")
    require(set(grant["ancestor_stop_bytes"]) == {row["path"] for row in cg["visible_ancestors"]},
            "visible ancestor stop missing/extra")
    for row in cg["visible_ancestors"]:
        stop = grant["ancestor_stop_bytes"][row["path"]]
        require(type(stop) is int and stop > int(row["memory.current"]), "invalid ancestor stop")
        require(row["memory.max"] == "max" or stop < int(row["memory.max"]), "ancestor stop leaves no margin")
    method.exposed_domain_admission(grant, cg)
    available = obs.mem_available()
    require(available is not None and available > grant["host_min_available_bytes"], "host headroom lost/unknown")
    return found


def handshake(value, role, pid, nonce, executable):
    """Match actual bootstrap/target PID, parent, session, nonce and executable."""
    require(isinstance(value, dict) and value.get("role") == role and value.get("pid") == pid and
            value.get("ppid") == os.getpid() and value.get("pgid") == pid and
            value.get("session_id") == pid and value.get("nonce") == nonce and
            value.get("executable") == executable, "same-PID/session/nonce handshake mismatch")


def run_probe(out, grant, inventory, obs, method, record):
    """Use plain spawn, same-PID setsid/readiness/exec and one exact wait owner."""
    bounds = inventory["bounds"]
    owner = None
    opened = set()
    data = bytearray()
    eof = False
    ready = None
    started = time.monotonic()
    deadline = started + bounds["overall_readiness_seconds"]
    def close_owned(fd):
        if fd in opened:
            os.close(fd)
            opened.remove(fd)
    def reserve(fd):
        copied = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 64)
        opened.add(copied)
        return copied
    write(out / "intent.json", {"observer":obs.process_identity(os.getpid()),
        "nonce":grant["nonce"], "route":"plain-posix-spawn/same-pid-setsid/execve",
        "bootstrap_sha256":inventory["bootstrap_sha256"], "target_sha256":inventory["target_sha256"]})
    try:
        with (out / "stdout.json").open("x") as stdout, (out / "stderr.log").open("x") as stderr, (out / "samples.jsonl").open("x") as samples:
            raw_read, raw_write = os.pipe2(os.O_CLOEXEC)
            opened.update((raw_read, raw_write))
            read_fd, write_fd = reserve(raw_read), reserve(raw_write)
            close_owned(raw_read)
            close_owned(raw_write)
            out_src, err_src = reserve(stdout.fileno()), reserve(stderr.fileno())
            ready_dst = reserve(write_fd)
            os.set_blocking(read_fd, False)
            argv = [sys.executable, "-c", BOOTSTRAP, str(ready_dst), grant["nonce"], sys.executable, TARGET]
            actions = [(os.POSIX_SPAWN_OPEN, 0, "/dev/null", os.O_RDONLY, 0),
                       (os.POSIX_SPAWN_DUP2, out_src, 1), (os.POSIX_SPAWN_DUP2, err_src, 2),
                       (os.POSIX_SPAWN_DUP2, write_fd, ready_dst),
                       (os.POSIX_SPAWN_CLOSE, read_fd), (os.POSIX_SPAWN_CLOSE, write_fd),
                       (os.POSIX_SPAWN_CLOSE, out_src), (os.POSIX_SPAWN_CLOSE, err_src)]
            record.update(argv=argv, file_actions=actions,
                fd_plan={"read":read_fd,"write_source":write_fd,"ready_destination":ready_dst,
                         "stdout_source":out_src,"stderr_source":err_src}, phase="spawn")
            write(out / "spawn-intent.json", {"argv":argv,"file_actions":actions,
                "fd_plan":record["fd_plan"],"nonce":grant["nonce"],"intent_only":True})
            # No setsid/setpgroup spawn attribute and no alternative route.
            pid = os.posix_spawn(sys.executable, argv, os.environ.copy(), file_actions=actions)
            owner = method.WaitOwner(pid)
            record.update(workload_pid=pid, phase="readiness-and-exit")
            write(out / "owned-child.json", {"pid":pid,"identity":obs.process_identity(pid),
                "observer_pid":os.getpid(),"nonce":grant["nonce"],"argv":argv})
            for fd in (write_fd, ready_dst, out_src, err_src):
                close_owned(fd)
            while True:
                terminal = owner.collect()
                # Drain buffered bytes even after terminal exit; EOF/readiness race
                # must not discard a valid message written before exec/exit.
                for _ in range(8):
                    if eof:
                        break
                    try:
                        chunk = os.read(read_fd, 256)
                    except BlockingIOError:
                        break
                    if not chunk:
                        eof = True
                        break
                    data.extend(chunk)
                    (out / "readiness.bin").write_bytes(data)
                    require(len(data) <= bounds["pipe_bytes"], "readiness byte bound exceeded")
                if ready is None and b"\n" in data:
                    require(data.count(b"\n") == 1 and data.endswith(b"\n"), "malformed/multiple readiness records")
                    ready = json.loads(data.decode())
                    handshake(ready, "bootstrap", pid, grant["nonce"], grant["python_resolved"])
                    record["bootstrap_ready"] = ready
                    write(out / "bootstrap-ready.json", ready)
                if eof and ready is None:
                    raise RuntimeError("readiness EOF without valid bootstrap record")
                terminal = owner.collect()
                if terminal is not None and ready is not None:
                    break
                require(time.monotonic() < deadline, "overall/readiness deadline")
                if terminal is None:
                    sample = obs.process_sample(pid)
                    sample["ancestor_current_bytes"] = {path:obs.read(Path(path) / "memory.current")
                        for path in grant["ancestor_stop_bytes"]}
                    sample["child_cgroup"] = obs.read(f"/proc/{pid}/cgroup")
                    samples.write(json.dumps(sample) + "\n")
                    samples.flush()
                    if owner.collect() is None:
                        require(type(sample.get("VmRSS_bytes")) is int and sample["VmRSS_bytes"] >= 0,
                                "required process RSS lost")
                        require(sample["VmRSS_bytes"] < grant["process_stop_bytes"], "process RSS stop")
                        require(sample["host_available_bytes"] is not None and
                            sample["host_available_bytes"] > grant["host_min_available_bytes"], "host headroom stop")
                        require(sample["child_cgroup"] == obs.read("/proc/self/cgroup"), "child cgroup lost/moved")
                        require(all(value is not None and int(value) < grant["ancestor_stop_bytes"][path]
                            for path,value in sample["ancestor_current_bytes"].items()), "ancestor current stop")
                time.sleep(bounds["poll_seconds"])
            require(time.monotonic() <= deadline, "probe overall deadline exceeded")
            require(terminal["returncode"] == 0 and owner.collect() is terminal, "normal/cached exact wait4 missing")
            path = out / "stdout.json"
            require(0 < path.stat().st_size <= bounds["target_record_bytes"], "target output missing/oversized")
            target = json.loads(path.read_text())
            handshake(target, "target", pid, grant["nonce"], grant["python_resolved"])
            require(target["cgroup_namespace"] == grant["resource_domain"]["expected_exposed"]["namespace"],
                    "target namespace differs from mapped exposed domain")
            require(terminal["ru_maxrss_native_units"] == "Linux KiB" and
                    terminal["complete_child_peak_bytes"] == terminal["rusage_native"]["ru_maxrss"] * 1024,
                    "terminal native units/conversion mismatch")
            record.update(target_handshake=target, phase="route_observed")
    finally:
        direct_cleanup(owner, record, bounds)
        record["terminal"] = owner.terminal if owner is not None else None
        record["wait_ownership_lost"] = owner.wait_lost if owner is not None else None
        record["elapsed_seconds"] = time.monotonic() - started
        (out / "readiness.bin").write_bytes(data)
        for fd in tuple(opened):
            close_owned(fd)
        write(out / "route-details.json", record)
    require("cleanup_gap" not in record and owner is not None and owner.terminal is not None and not owner.wait_lost,
            "unresolved owned PID/terminal usage; block further work")


def main():
    """Run one exactly frozen probe after release; never retry or alter old evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    require(args.attempt_id and all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                                  for c in args.attempt_id), "safe unique attempt ID required")
    out = HERE / "launch-route-attempts" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    record = {"protocol":"WS116-selected-launch-route-v1", "status":"probe_failed", "phase":"admission",
        "attempt_id":args.attempt_id,"observer_pid":os.getpid(),"driver_argv":sys.argv,"signals":[],
        "started_monotonic_ns":time.monotonic_ns(),"not_scientific_memory_evidence":True}
    obs = None
    try:
        (out / "grant.input").write_bytes(args.grant.read_bytes())
        grant = json.loads((out / "grant.input").read_text())
        inventory = json.loads((HERE / "launch-route-inventory.json").read_text())
        sys.path.insert(0, str(REPORT))
        import observer as obs
        import run_attempt as method
        require(not any(name == "simrecon" or name.startswith("simrecon.") or name == "numpy" or
                        name.startswith("numpy.") or name == "scipy" or name.startswith("scipy.")
                        for name in sys.modules), "forbidden scientific/product import")
        found = admit(args, grant, inventory, obs, method)
        record.update(source_sha256=found, grant_sha256=obs.digest(out / "grant.input"),
                      observer_identity=obs.process_identity(os.getpid()),resource_domain=grant["resource_domain"])
        write(out / "preflight.json", obs.context(ROOT))
        run_probe(out, grant, inventory, obs, method, record)
        method.exposed_domain_admission(grant, obs.cgroup_ancestors())
        require(identities(grant, obs) == found, "probe material identity changed")
        record["status"] = "selected_tiny_route_observed_only"
    except BaseException as error:
        record.update(error_type=type(error).__name__,error_message=str(error))
    finally:
        record["finished_monotonic_ns"] = time.monotonic_ns()
        if obs is not None:
            try:
                record["postflight"] = obs.context(ROOT)
            except BaseException as error:
                record.update(status="probe_failed",postflight_error=str(error))
        record["files_before_receipt"] = {path.name:{"logical_bytes":path.stat().st_size,
            "allocated_bytes":path.stat().st_blocks * 512} for path in out.iterdir() if path.is_file()}
        record["limits"] = ("Terminal wait4 is kernel-reported direct-child usage through final exit. "
            "Inherited/pre-exec/exec-transition high-water retention remains unresolved; same PID does not "
            "guarantee every bootstrap/startup peak survives exec. No subtraction/aggregate/benefit claim. "
            "A tiny route is not a scientific-method qualification. "
            "PID1 is not a general reaper; parent-death/spawn-to-owner gaps remain; no deliberate orphan test. "
            "Receipt excludes its own disk bytes. Failure stops; no fallback route or retry.")
        write(out / "receipt.json", record)
    return 0 if record["status"] == "selected_tiny_route_observed_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
