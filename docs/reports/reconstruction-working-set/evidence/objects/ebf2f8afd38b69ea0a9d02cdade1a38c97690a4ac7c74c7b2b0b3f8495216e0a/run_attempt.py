"""External single-attempt WS116 admission/monitor. No retries or growth loop.

DRAFT: not run, parsed or independently reviewed. Requires a coordinator-authored
JSON admission file. A grant is evidence, not an access-control boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
        if not isinstance(grant[key], (int, float)) or grant[key] <= 0:
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
        if threshold <= int(row["memory.current"]) or (row["memory.max"] != "max" and threshold >= int(row["memory.max"])):
            raise ValueError("ancestor threshold does not leave declared current/limit margin")
    available = mem_available()
    if available is None or available <= grant["host_min_available_bytes"]:
        raise ValueError("host available memory does not satisfy admission")
    return {**condition, "profile": grant["profile"], "repetition": grant["repetition"]}, actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    if not args.attempt_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in args.attempt_id):
        raise ValueError("safe unique attempt id required")
    out = HERE / "raw" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)  # Preserve every prior attempt.
    grant = json.loads(args.grant.read_text())
    write(out / "grant.json", grant)
    receipt = {"status": "preflight_started", "grant_sha256": digest(args.grant),
               "observer_pid": os.getpid(), "started_monotonic_ns": time.monotonic_ns()}
    process = None
    try:
        write(out / "preflight.json", context(ROOT))
        spec, identity = admit(grant)
        write(out / "spec.json", spec)
        receipt.update(candidate=identity, material_hashes=material_hashes(ROOT))
        env = os.environ.copy()
        env.update({key: "1" for key in THREADS})
        env["PYTHONPATH"] = str(ROOT / "src")
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        with (out / "stdout.json").open("x") as stdout, (out / "stderr.log").open("x") as stderr, (out / "samples.jsonl").open("x") as samples:
            process = subprocess.Popen([sys.executable, str(HERE / "workload_child.py"), str(out / "spec.json"), str(ROOT)],
                                       cwd=ROOT, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
            receipt["workload_pid"] = process.pid
            receipt["child_cgroup"] = read(f"/proc/{process.pid}/cgroup")
            if receipt["child_cgroup"] != read("/proc/self/cgroup"):
                raise ValueError("workload moved outside observer's admitted cgroup")
            started = time.monotonic()
            stop = None
            while process.poll() is None:
                sample = process_sample(process.pid)
                sample["ancestor_current_bytes"] = {path: read(Path(path) / "memory.current") for path in grant["ancestor_stop_bytes"]}
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                if time.monotonic() - started >= grant["deadline_seconds"]:
                    stop = "deadline"
                elif sample.get("VmRSS_bytes", 0) >= grant["process_stop_bytes"]:
                    stop = "process_current_RSS_threshold"
                elif sample["host_available_bytes"] is None or sample["host_available_bytes"] <= grant["host_min_available_bytes"]:
                    stop = "host_headroom_missing_or_deteriorated"
                elif any(value is None or int(value) >= grant["ancestor_stop_bytes"][path] for path, value in sample["ancestor_current_bytes"].items()):
                    stop = "cgroup_current_threshold_or_unknown"
                if stop:
                    receipt.update(stop_reason=stop, last_sample=sample, signal="SIGTERM")
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=grant["terminate_grace_seconds"])
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        receipt["escalated_signal"] = "SIGKILL"
                        process.wait()
                    break
                time.sleep(grant["sample_interval_seconds"])
            receipt["returncode"] = process.wait()
            receipt["status"] = "stopped" if stop else "child_complete_pending_scientific_review"
    except BaseException as error:
        receipt.update(status="refused_or_failed", type=type(error).__name__, message=str(error))
        if process is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            receipt.update(signal="SIGKILL", returncode=process.returncode)
    finally:
        receipt["finished_monotonic_ns"] = time.monotonic_ns()
        receipt["postflight"] = context(ROOT)
        receipt["observer_ru_maxrss_units"] = "Linux KiB; observer excluded from child RSS"
        receipt["monitor_limits"] = "Sampling can miss short peaks; threshold/time stop may overshoot; monitor cannot guarantee no OOM. No automatic retry."
        receipt["files"] = {p.name: {"logical_bytes": p.stat().st_size,
                                    "allocated_bytes": p.stat().st_blocks * 512} for p in out.iterdir() if p.is_file()}
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == "child_complete_pending_scientific_review" and receipt["returncode"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
