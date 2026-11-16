"""Capture read-only outer/Docker resource correspondence for one admission.

This does not grant an experiment or prove anything about unexposed ancestors.
Run only when fresh correspondence evidence is requested. No numerical imports.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def snapshot():
    paths = ["/proc/self/cgroup", "/proc/self/mountinfo", "/proc/meminfo"]
    paths += ["/sys/fs/cgroup/" + name for name in (
        "memory.max", "memory.current", "memory.peak", "memory.events",
        "memory.swap.max", "memory.swap.current")]
    files = {}
    for name in paths:
        try:
            files[name] = Path(name).read_text()
        except OSError as error:
            files[name] = {"error": type(error).__name__, "message": str(error)}
    identities = {}
    for name in ("/sys/fs/cgroup", "/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.current"):
        try:
            stat = os.stat(name)
            identities[name] = {"device": stat.st_dev, "inode": stat.st_ino}
        except OSError as error:
            identities[name] = {"error": type(error).__name__, "message": str(error)}
    try:
        namespace = os.readlink("/proc/self/ns/cgroup")
    except OSError as error:
        namespace = {"error": type(error).__name__, "message": str(error)}
    return {"observed_at_unix_ns": time.time_ns(), "pid": os.getpid(),
            "cgroup_namespace": namespace, "files": files, "file_identities": identities}


if __name__ == "__main__":
    started = time.time_ns()
    outer = snapshot()
    template = ("id={{.Id}} image={{.Image}} memory={{.HostConfig.Memory}} "
                "swap={{.HostConfig.MemorySwap}} cgroupns={{.HostConfig.CgroupnsMode}} "
                "parent={{.HostConfig.CgroupParent}} init_pid={{.State.Pid}}")
    inspect_command = ["docker", "inspect", "--format", template, "simrecon-campaign-ubuntu"]
    inspect = subprocess.run(inspect_command, capture_output=True, text=True, timeout=15)
    # Execute exactly this pure-stdlib snapshot function in the pinned worktree Python.
    function_source = Path(__file__).read_text().split('if __name__ == "__main__":')[0]
    inner_code = function_source + "\nprint(json.dumps(snapshot(), sort_keys=True))\n"
    inner_command = ["docker", "exec", "--user", "1000:1000", "-w", "/workspace/work/issue-116",
                     "simrecon-campaign-ubuntu", ".venv/bin/python", "-c", inner_code]
    inner = subprocess.run(inner_command, capture_output=True, text=True, timeout=15)
    record = {"schema": "campaign-resource-domain-correspondence-v1",
              "started_at_unix_ns": started, "finished_at_unix_ns": time.time_ns(),
              "capture_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "outer": outer,
              "docker_inspect": {"argv": inspect_command, "returncode": inspect.returncode,
                                 "stdout": inspect.stdout, "stderr": inspect.stderr},
              "inner": {"route": inner_command[:-1] + ["<recorded snapshot source>"],
                        "returncode": inner.returncode, "stdout": inner.stdout, "stderr": inner.stderr},
              "external_ancestors": "unknown_unobservable",
              "scope": "asynchronous exposed-machine/container observations; no experiment admission, no host-ancestor absence or workstation certification"}
    directory = Path("/workspace/work/campaign/evidence/116/resource-domain")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (str(started) + ".json")
    data = json.dumps(record, indent=2, sort_keys=True) + "\n"
    with path.open("x") as stream:
        stream.write(data)
    print(json.dumps({"path": str(path), "sha256": hashlib.sha256(data.encode()).hexdigest(),
                      "observed_at_unix_ns": started, "docker_status": inspect.returncode,
                      "inner_status": inner.returncode, "external_ancestors": "unknown_unobservable"}))
    sys.exit(0 if inspect.returncode == inner.returncode == 0 else 1)
