"""WS116 analysis-only observer. Source draft, never executed during preparation."""
from __future__ import annotations

import contextlib
import hashlib
import importlib
import os
from pathlib import Path
import platform
import resource
import time

THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def material_hashes(root):
    paths = sorted((root / "src/simrecon").rglob("*.py"))
    paths += [root / "uv.lock", root / "tests/reconstruction_summary_fixture.py",
              root / "tests/reconstruction_memory_benchmark.py"]
    report = root / "docs/reports/reconstruction-working-set"
    paths += [report / name for name in ("manifest.json", "observer.py", "run_attempt.py", "workload_child.py")]
    return {str(p.relative_to(root)): digest(p) for p in paths}


def cgroup_ancestors():
    """Resolve v2 membership against mountinfo, then include every visible ancestor.

    Unsupported v1, namespace path mismatch or inaccessible files fail admission.
    Visible mount root may hide host ancestors: external scheduling must resolve
    that uncertainty; the function does not infer unlimited headroom from it.
    """
    membership = read("/proc/self/cgroup")
    mounts = read("/proc/self/mountinfo")
    if membership is None or mounts is None:
        return {"error": "cgroup membership/mountinfo unavailable"}
    group = next((line[3:] for line in membership.splitlines() if line.startswith("0::")), None)
    if group is None:
        return {"error": "v2 membership unavailable; v1 requires an explicit observer revision"}
    for line in mounts.splitlines():
        left, right = line.split(" - ", 1)
        if right.split()[0] != "cgroup2":
            continue
        fields = left.split()
        # Decode mountinfo's defined path escapes, without shell interpretation.
        decode = lambda s: s.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")
        mount_root, mount = Path(decode(fields[3])), Path(decode(fields[4]))
        try:
            relative = Path(group).relative_to(mount_root)
        except ValueError:
            continue
        if ".." in relative.parts:
            continue
        current = mount / relative
        rows = []
        while True:
            rows.append({"path": str(current), **{key: read(current / key) for key in (
                "memory.max", "memory.current", "memory.peak", "memory.events",
                "memory.swap.max", "memory.swap.current")}})
            if current == mount:
                break
            current = current.parent
        return {"membership": group, "mount_root": str(mount_root), "mount": str(mount),
                "visible_ancestors": rows, "hidden_ancestors": "unknown until coordinator resolves host/namespace limits"}
    return {"error": "effective cgroup mount could not be resolved"}


def mem_available():
    for line in (read("/proc/meminfo") or "").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return None


def context(root):
    disk = os.statvfs(root)
    return {"system": platform.system(), "kernel": platform.release(), "machine": platform.machine(),
            "host_id_sha256": hashlib.sha256(platform.node().encode()).hexdigest(),
            "pid": os.getpid(), "meminfo": read("/proc/meminfo"), "cgroup": cgroup_ancestors(),
            "rlimits": {key: resource.getrlimit(getattr(resource, key)) for key in (
                "RLIMIT_AS", "RLIMIT_DATA", "RLIMIT_RSS", "RLIMIT_CPU", "RLIMIT_FSIZE", "RLIMIT_NOFILE")},
            "disk_available_bytes": disk.f_bavail * disk.f_frsize,
            "threads": {key: os.environ.get(key) for key in THREADS},
            "allocator": {key: os.environ.get(key) for key in ("PYTHONMALLOC", "MALLOC_ARENA_MAX")}}


def process_sample(pid):
    status = read(f"/proc/{pid}/status")
    values = {}
    for line in (status or "").splitlines():
        name, _, value = line.partition(":")
        if name in ("VmRSS", "VmHWM", "VmSwap"):
            values[name + "_bytes"] = int(value.split()[0]) * 1024
    return {"monotonic_ns": time.monotonic_ns(), "pid": pid, **values,
            "host_available_bytes": mem_available()}


@contextlib.contextmanager
def stage_observer(events):
    """Patch only the workflow's imported context manager; record scalar events.

    No frame/locals inspection and no array references. Stage high-water is
    cumulative. Timestamp clock is shared Linux monotonic with external samples.
    Context-manager allocation/timing can perturb the experiment.
    """
    module = importlib.import_module("simrecon.workflow.reconstruct")
    original = module.workflow_stage

    @contextlib.contextmanager
    def wrapped(stage, **kwargs):
        def record(edge):
            events.append({"stage": stage, "time_index": kwargs.get("time_index"), "edge": edge,
                           "monotonic_ns": time.monotonic_ns(),
                           "ru_maxrss_native_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        record("enter")
        try:
            with original(stage, **kwargs):
                yield
        finally:
            record("exit")
    module.workflow_stage = wrapped
    try:
        yield
    finally:
        module.workflow_stage = original
