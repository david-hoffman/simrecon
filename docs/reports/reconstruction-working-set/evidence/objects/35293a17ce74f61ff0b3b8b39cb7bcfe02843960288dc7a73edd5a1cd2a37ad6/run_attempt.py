"""External single-attempt WS116 admission/monitor. No retries or growth loop.

DRAFT: not run, parsed or independently reviewed. Requires a coordinator-authored
JSON admission file. A grant is evidence, not an access-control boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from observer import (THREADS, cgroup_ancestors, context, digest, material_hashes,
                      mem_available, process_sample, read)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write(path, record):
    path.write_text(json.dumps(record, indent=2, default=str) + "\n")


def admit(grant):
    if grant["numerical_release"] is not True or grant["accepted_112_then_115"] is not True:
        raise ValueError("accepted dependency and exact numerical release required")
    if not grant["representation_preflight"]["accepted"] or not grant["representation_preflight"]["evidence"]:
        raise ValueError("accepted integer/domain/actual-stencil preflight missing")
    if not grant["headroom_evidence"] or not grant["hidden_ancestors_resolved"]:
        raise ValueError("conservative headroom/native allowance or ancestor resolution missing")
    for key in ("deadline_seconds", "process_stop_bytes", "host_min_available_bytes", "terminate_grace_seconds"):
        if type(grant[key]) not in (int, float) or not math.isfinite(grant[key]) or grant[key] <= 0:
            raise ValueError("positive explicit safety setting required: " + key)
    if grant["sample_interval_seconds"] != 0.01:
        raise ValueError("observer interval differs from manifest; revise manifest before execution")
    if str(Path(sys.executable).resolve()) != grant["python_resolved"]:
        raise ValueError("interpreter differs from pinned grant")
    actual = {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
              "tracked_diff_sha256": hashlib.sha256(subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=ROOT)).hexdigest()}
    if actual != grant["candidate"] or material_hashes(ROOT) != grant["material_hashes"]:
        raise ValueError("candidate or material input identities changed")
    manifest = json.loads((HERE / "manifest.json").read_text())
    candidates = manifest["initial_conditions"] + grant.get("declared_growth_conditions", [])
    condition = next(row for row in candidates if row["id"] == grant["condition_id"])
    if condition not in manifest["initial_conditions"]:
        if (not grant.get("growth_separate_admission") or not grant.get("smaller_measured_evidence")
                or "case" in condition or condition["shape"] not in ([1, 3, 8, 192, 192], [1, 3, 8, 256, 256])):
            raise ValueError("growth needs declared 192 or 256 shape, smaller evidence and separate admission")
    if grant["repetition"] not in manifest["repetitions"] or type(grant["profile"]) is not bool:
        raise ValueError("undeclared repetition/profile")
    cg = cgroup_ancestors()
    if "error" in cg:
        raise ValueError(cg["error"])
    rows = cg["visible_ancestors"]
    if set(grant["ancestor_stop_bytes"]) != {row["path"] for row in rows}:
        raise ValueError("every visible effective ancestor needs explicit threshold")
    for row in rows:
        if row["memory.current"] is None or row["memory.max"] is None:
            raise ValueError("ancestor current/max unknown")
        threshold = grant["ancestor_stop_bytes"][row["path"]]
        if type(threshold) is not int or threshold <= 0:
            raise ValueError("ancestor threshold must be positive integer bytes")
        if threshold <= int(row["memory.current"]) or (row["memory.max"] != "max" and threshold >= int(row["memory.max"])):
            raise ValueError("ancestor threshold does not leave declared current/limit margin")
    available = mem_available()
    if available is None or available <= grant["host_min_available_bytes"]:
        raise ValueError("host available memory does not satisfy admission")
    return {**condition, "profile": grant["profile"], "repetition": grant["repetition"]}, actual


class WaitOwner:
    """Only this object calls wait4 for this exact PID; no Popen object exists."""
    def __init__(self, pid):
        self.pid = pid
        self.terminal = None
        self.wait_lost = False
        self.nonterminal_wait_events = []

    def collect(self):
        if self.terminal is not None:
            return self.terminal
        if self.wait_lost:
            raise RuntimeError("wait ownership lost; terminal usage unavailable")
        try:
            pid, status, usage = os.wait4(self.pid, os.WNOHANG)
        except InterruptedError:
            return None
        except ChildProcessError:
            self.wait_lost = True
            raise RuntimeError("child reaped elsewhere or auto-reaped; never infer peak")
        if pid == 0:
            return None
        if not (os.WIFEXITED(status) or os.WIFSIGNALED(status)):
            self.nonterminal_wait_events.append({"wait_status_raw": status, "pid": pid,
                "observed_monotonic_ns": time.monotonic_ns(),
                "stopped": os.WIFSTOPPED(status),
                "stop_signal": os.WSTOPSIG(status) if os.WIFSTOPPED(status) else None})
            return None  # A traced/stopped notification is not complete-child usage.
        self.terminal = {
            "pid": pid, "wait_status_raw": status, "returncode": os.waitstatus_to_exitcode(status),
            "exited": os.WIFEXITED(status), "signaled": os.WIFSIGNALED(status),
            "exit_code": os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
            "term_signal": os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
            "core_dumped": os.WCOREDUMP(status) if hasattr(os, "WCOREDUMP") else None,
            "reaped_monotonic_ns": time.monotonic_ns(),
            "rusage_native": {key: getattr(usage, key) for key in dir(usage) if key.startswith("ru_")},
            "ru_maxrss_native_units": "Linux KiB", "ru_maxrss_multiplier_to_bytes": 1024,
            "complete_child_peak_bytes": int(usage.ru_maxrss) * 1024,
            "scope": "wait4 exact direct child through exit, including JSON/teardown; maximum resident process size, not concurrent aggregate or numerical-only memory"}
        return self.terminal

    def send(self, signum):
        # An unreaped direct child cannot have its PID recycled. Always collect
        # first; if another reaper invalidated ownership, do not signal a reused PID.
        if self.collect() is not None:
            return {"signal": signum, "delivery": "already_terminal"}
        try:
            os.killpg(self.pid, signum)
            return {"signal": signum, "delivery": "sent", "monotonic_ns": time.monotonic_ns()}
        except ProcessLookupError:
            return {"signal": signum, "delivery": "group_absent_race", "monotonic_ns": time.monotonic_ns()}


def candidate_identity():
    return {"head": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"),
            "tracked_diff_sha256": hashlib.sha256(subprocess.check_output(
                ["git", "diff", "--binary", "HEAD"], cwd=ROOT)).hexdigest()}


def cleanup(owner, receipt, seconds):
    """Best-effort bounded kill/reap; an unreapable kernel task is an explicit gap."""
    if owner is None or owner.terminal is not None:
        return
    try:
        receipt.setdefault("signals", []).append(owner.send(signal.SIGKILL))
        until = time.monotonic() + seconds
        while owner.collect() is None and time.monotonic() < until:
            time.sleep(0.01)
        if owner.terminal is None:
            receipt["cleanup_gap"] = "SIGKILL requested but terminal wait4 unavailable by cleanup deadline; coordinator must resolve owned PID before another attempt"
    except BaseException as error:
        receipt["cleanup_gap"] = {"type": type(error).__name__, "message": str(error),
                                  "meaning": "wait/signal ownership unresolved; do not start another attempt"}


def child_outcome(path, max_bytes, pid, spec):
    if not path.exists() or path.stat().st_size == 0:
        return "missing_child_record", None
    if path.stat().st_size > max_bytes:
        return "child_record_exceeds_admitted_parse_bound", None
    try:
        record = json.loads(path.read_text())
        if not isinstance(record, dict) or record.get("protocol") != "WS116-child-v2":
            raise ValueError("wrong protocol/object")
        if record.get("pid") != pid or record.get("spec") != spec:
            raise ValueError("child PID/spec does not match admitted process")
        if record.get("status") == "finite_observation_pending_qualification":
            if record.get("finite_common_fields") is not True or record.get("material_identity_matches") is not True:
                raise ValueError("finite/identity fields contradict success status")
            if set(record.get("snapshots", {})) != {"pre_call", "call_end", "post_observation"}:
                raise ValueError("required cumulative snapshots missing")
            if (record.get("material_hashes_before") != spec["expected_material_hashes"] or
                    record.get("material_hashes_after") != spec["expected_material_hashes"]):
                raise ValueError("child material hashes do not match admitted bytes")
        if record.get("status") not in {"finite_observation_pending_qualification", "material_identity_failure",
                "nonfinite_scientific_failure", "workflow_exception", "observation_failure"}:
            raise ValueError("unknown child outcome status")
        return record.get("status", "malformed_child_record"), record
    except (ValueError, UnicodeError, OSError) as error:
        return "malformed_child_record", {"parse_type": type(error).__name__, "message": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    if not args.attempt_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.attempt_id):
        raise ValueError("safe unique attempt id required")
    out = HERE / "raw" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    receipt = {"protocol": "WS116-attempt-v2", "status": "admission_started", "phase": "admission",
               "observer_pid": os.getpid(), "started_monotonic_ns": time.monotonic_ns(), "signals": []}
    owner = None
    grant = {}
    spec = None
    try:
        # Preserve exact grant bytes even if JSON/admission is invalid.
        import shutil
        shutil.copyfile(args.grant, out / "grant.input")
        receipt["grant_sha256"] = digest(out / "grant.input")
        grant = json.loads((out / "grant.input").read_text())
        write(out / "preflight.json", context(ROOT))
        if sys.platform != "linux" or not hasattr(os, "wait4") or not hasattr(os, "posix_spawn"):
            raise ValueError("Linux stdlib wait4/posix_spawn route unavailable")
        if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise ValueError("default SIGCHLD required; no handler/auto-reaper allowed")
        for key in ("kill_reap_seconds", "max_child_record_bytes"):
            if type(grant[key]) not in (int, float) or not math.isfinite(grant[key]) or grant[key] <= 0:
                raise ValueError("positive explicit method safety setting required: " + key)
        if type(grant["max_child_record_bytes"]) is not int:
            raise ValueError("child JSON parse bound must be integer bytes")
        receipt["candidate_pre_admission"] = candidate_identity()
        receipt["material_hashes_pre_admission"] = material_hashes(ROOT)
        spec, identity = admit(grant)
        hashes_before = material_hashes(ROOT)
        spec["expected_material_hashes"] = hashes_before
        write(out / "spec.json", spec)
        receipt.update(candidate_before=identity, material_hashes_before=hashes_before,
                       wait_owner="single os.wait4(exact_pid,WNOHANG), no waitpid/Popen/aggregate waits",
                       spawn_route="os.posix_spawn executable with setsid=True; runtime support not assumed",
                       interpreter={"executable": sys.executable, "resolved": str(Path(sys.executable).resolve()),
                                    "version": sys.version},
                       sigchld_handler="SIG_DFL", effective_cwd=str(ROOT))
        env = os.environ.copy()
        env.update({key: "1" for key in THREADS})
        env["PYTHONPATH"] = str(ROOT / "src")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        receipt["child_environment_controls"] = {key: env.get(key) for key in (*THREADS, "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONMALLOC", "MALLOC_ARENA_MAX")}
        receipt["phase"] = "spawn"
        # chdir is parent-only before spawn, avoiding preexec_fn or another child.
        os.chdir(ROOT)
        with (out / "stdout.json").open("x") as stdout, (out / "stderr.log").open("x") as stderr, (out / "samples.jsonl").open("x") as samples:
            receipt["observer_pre_spawn_snapshot"] = __import__("observer").rusage_snapshot("parent before posix_spawn; not subtracted from child peak")
            receipt["spawn_start_monotonic_ns"] = time.monotonic_ns()
            pid = os.posix_spawn(sys.executable,
                [sys.executable, str(HERE / "workload_child.py"), str(out / "spec.json"), str(ROOT)], env,
                file_actions=[(os.POSIX_SPAWN_OPEN, 0, "/dev/null", os.O_RDONLY, 0),
                              (os.POSIX_SPAWN_DUP2, stdout.fileno(), 1),
                              (os.POSIX_SPAWN_DUP2, stderr.fileno(), 2)], setsid=True)
            owner = WaitOwner(pid)
            receipt.update(workload_pid=pid, phase="observation", spawn_return_monotonic_ns=time.monotonic_ns())
            deadline = receipt["spawn_start_monotonic_ns"] / 1e9 + grant["deadline_seconds"]
            term_at = None
            kill_at = None
            count = 0
            while owner.collect() is None:
                sample = process_sample(pid)
                sample["child_cgroup"] = read(f"/proc/{pid}/cgroup")
                sample["ancestor_current_bytes"] = {path: read(Path(path) / "memory.current") for path in grant["ancestor_stop_bytes"]}
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                count += 1
                if owner.collect() is not None:
                    break  # Exit raced /proc observation; do not invent a stop.
                now = time.monotonic()
                stop = None
                if sample["child_cgroup"] != read("/proc/self/cgroup"):
                    stop = "child_cgroup_missing_or_moved"
                elif now >= deadline:
                    stop = "timeout"
                elif sample.get("VmRSS_bytes", 0) >= grant["process_stop_bytes"]:
                    stop = "process_current_RSS_threshold"
                elif sample["host_available_bytes"] is None or sample["host_available_bytes"] <= grant["host_min_available_bytes"]:
                    stop = "host_headroom_missing_or_deteriorated"
                elif any(value is None or int(value) >= grant["ancestor_stop_bytes"][path] for path, value in sample["ancestor_current_bytes"].items()):
                    stop = "cgroup_current_threshold_or_unknown"
                if stop and term_at is None:
                    receipt.update(stop_reason=stop, last_sample=sample)
                    receipt["signals"].append(owner.send(signal.SIGTERM))
                    term_at = now
                if term_at is not None and kill_at is None and now - term_at >= grant["terminate_grace_seconds"]:
                    receipt["signals"].append(owner.send(signal.SIGKILL))
                    kill_at = now
                if kill_at is not None and now - kill_at >= grant["kill_reap_seconds"]:
                    raise TimeoutError("terminal wait4 missing after KILL reap deadline")
                time.sleep(grant["sample_interval_seconds"])
            receipt["sample_count"] = count
        receipt["terminal"] = owner.terminal
        outcome, child_record = child_outcome(out / "stdout.json", grant["max_child_record_bytes"], owner.pid, spec)
        receipt["child_outcome"] = outcome
        receipt["child_record_sha256"] = digest(out / "stdout.json")
        receipt["candidate_after"] = candidate_identity()
        receipt["material_hashes_after"] = material_hashes(ROOT)
        identity_matches = (receipt["candidate_after"] == receipt["candidate_before"] and
                            receipt["material_hashes_after"] == receipt["material_hashes_before"])
        receipt["material_identity_matches"] = identity_matches
        if "stop_reason" in receipt:
            receipt["status"] = "timeout_stopped" if receipt["stop_reason"] == "timeout" else "monitor_stopped"
        elif owner.terminal["signaled"]:
            receipt["status"] = "child_signaled"
        elif outcome in ("missing_child_record", "malformed_child_record", "child_record_exceeds_admitted_parse_bound"):
            receipt["status"] = outcome
            receipt["child_parse_diagnostic"] = child_record
        elif not identity_matches or outcome == "material_identity_failure":
            receipt["status"] = "material_identity_failure"
        elif outcome == "nonfinite_scientific_failure":
            receipt["status"] = "nonfinite_scientific_failure"
        elif outcome == "workflow_exception":
            receipt["status"] = "workflow_exception_unclassified"
        elif outcome == "observation_failure":
            receipt["status"] = "child_observation_failure"
        elif owner.terminal["returncode"] != 0:
            receipt["status"] = "child_nonzero_exit"
        elif outcome != "finite_observation_pending_qualification":
            receipt["status"] = "child_observation_failure"
        else:
            receipt["status"] = "complete_child_observed_pending_scientific_qualification"
    except BaseException as error:
        receipt.update(status={"admission": "admission_refused", "spawn": "spawn_failure"}.get(
            receipt["phase"], "observation_failure"), error_type=type(error).__name__, error_message=str(error))
    finally:
        cleanup(owner, receipt, grant.get("kill_reap_seconds", 1) if isinstance(grant, dict) else 1)
        if owner is not None:
            receipt["terminal"] = owner.terminal
            receipt["wait_ownership_lost"] = owner.wait_lost
            receipt["nonterminal_wait_events"] = owner.nonterminal_wait_events
        receipt["finished_monotonic_ns"] = time.monotonic_ns()
        try:
            receipt["candidate_final"] = candidate_identity()
            receipt["material_hashes_final"] = material_hashes(ROOT)
            if "candidate_before" in receipt and (receipt["candidate_final"] != receipt["candidate_before"] or
                    receipt["material_hashes_final"] != receipt["material_hashes_before"]):
                receipt["material_identity_matches"] = False
                if receipt["status"] == "complete_child_observed_pending_scientific_qualification":
                    receipt["status"] = "material_identity_failure"
            receipt["postflight"] = context(ROOT)
            receipt["observer_self_snapshot"] = __import__("observer").rusage_snapshot("parent after child/cleanup, excludes receipt serialization")
            receipt["files_before_receipt"] = {p.name: {"sha256": digest(p), "logical_bytes": p.stat().st_size,
                "allocated_bytes": p.stat().st_blocks * 512} for p in out.iterdir() if p.is_file()}
        except BaseException as error:
            receipt["postflight_gap"] = {"type": type(error).__name__, "message": str(error)}
            if receipt["status"] == "complete_child_observed_pending_scientific_qualification":
                receipt["status"] = "complete_child_observation_incomplete"
        receipt["limits"] = (
            "wait4 peak is a maximum process RSS, not parent+child aggregate or numerical-only allocation. "
            "No numerical grandchildren commissioned. Inherited/pre-exec high-water, native allocator/FFT "
            "semantics and spawn support require actual runtime qualification. Sampling/stops can overshoot. "
            "File inventory excludes receipt itself; coordinator collects final disk sizes/hash externally. No retry.")
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == "complete_child_observed_pending_scientific_qualification" and "cleanup_gap" not in receipt else 1


if __name__ == "__main__":
    raise SystemExit(main())
