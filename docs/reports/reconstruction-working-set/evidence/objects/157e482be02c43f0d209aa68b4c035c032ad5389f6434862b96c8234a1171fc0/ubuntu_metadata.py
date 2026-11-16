"""Fixed ROOT-authorized read-only Ubuntu metadata snippet; SOURCE ONLY.

No process scans, signals, waits, RSS/peak probes or scientific imports.
Future argv: pinned Python, this exact source, ROOT literal request JSON path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time


def path_fact(path):
    try:
        value = Path(path).lstat()
        return {"state": "present", "device": value.st_dev, "inode": value.st_ino}
    except FileNotFoundError:
        return {"state": "absent"}
    except OSError as error:
        return {"state": "unknown", "error": type(error).__name__}


def owned_fact(item, boot_id):
    pid = item["pid"]
    if type(pid) is not int or pid <= 1 or type(item["start_ticks"]) is not int or item["start_ticks"] <= 0:
        raise ValueError("literal exact owned PID/start identity required")
    if item["boot_id"] != boot_id:
        raise ValueError("owned identity from a different/unknown boot")
    base = Path("/proc") / str(pid)
    state = path_fact(base / "stat")
    result = {"expected": item, "stat": state, "fds": {}}
    if state["state"] == "present":
        try:
            tail = (base / "stat").read_text().rsplit(")", 1)[1].split()
            start = int(tail[19])
            result["observed_start_ticks"] = start
            result["identity_state"] = "same_identity" if start == item["start_ticks"] else "reused_ambiguous"
        except (OSError, ValueError, IndexError) as error:
            result["identity_state"] = "unknown"
            result["error"] = type(error).__name__
    else:
        result["identity_state"] = state["state"]
    for fd in item["fds"]:
        if type(fd) is not int or fd < 0:
            raise ValueError("literal exact owned FD required")
        result["fds"][str(fd)] = path_fact(base / "fd" / str(fd))
    return result


def main():
    if len(sys.argv) != 2 or sys.platform != "linux":
        raise ValueError("one ROOT request on pinned Ubuntu required")
    started = time.time_ns()
    request_path = Path(sys.argv[1])
    if request_path.stat().st_size > 1048576:
        raise ValueError("request exceeds fixed bound")
    request = json.loads(request_path.read_text())
    if set(request) != {"disk_paths", "owned_processes"} or len(request["owned_processes"]) > 128 or len(request["disk_paths"]) != 2:
        raise ValueError("fixed request fields/owned identity bound required")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    disks = {}
    for name in request["disk_paths"]:
        value = os.statvfs(name)
        identity = os.stat(name)
        disks[name] = {"device": identity.st_dev, "fsid": value.f_fsid,
                       "fragment_size": value.f_frsize, "free_bytes": value.f_bavail * value.f_frsize,
                       "free_inodes": value.f_favail}
    limits = {}
    for name in ("RLIMIT_AS", "RLIMIT_DATA", "RLIMIT_STACK", "RLIMIT_NOFILE", "RLIMIT_NPROC",
                 "RLIMIT_MEMLOCK", "RLIMIT_CORE", "RLIMIT_FSIZE", "RLIMIT_CPU"):
        limits[name] = list(resource.getrlimit(getattr(resource, name)))
    result = {"protocol": "WS116-fixed-ubuntu-metadata-v1", "observed_at_unix_ns": started,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(), "gid": os.getgid(),
        "executable": str(Path(sys.executable).resolve()), "cwd": os.getcwd(), "boot_id": boot,
        "namespaces": {name: os.readlink("/proc/self/ns/" + name) for name in ("pid", "cgroup")},
        "rlimits": limits, "disks": disks,
        "owned_processes": [owned_fact(item, boot) for item in request["owned_processes"]],
        "environment": {name: os.environ.get(name) for name in
                        ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "outside_campaign_processes": "unknown_not_scanned", "external_ancestors": "unknown_unobservable"}
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
