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
SNAPSHOT_SCOPES = {
    "pre_call": "after input hashes/retention, before call timestamp",
    "call_end": "after call/end timestamp, before result observations",
    "post_observation": "after context/hash/retention/finite/identity observations, before JSON serialization and teardown",
}
ONE_BYTE_DTYPES = frozenset(("|b1", "|i1", "|u1"))
MULTIBYTE_KIND_SIZES = {"i": (2, 4, 8), "u": (2, 4, 8), "f": (2, 4, 8, 16), "c": (8, 16)}


def legal_numeric_dtype(value, *, canonical):
    """Supported dtype.str encodings; canonical identities are little endian.

    Retention metadata preserves actual big-endian backings where present.
    One-byte encodings are byteorder-independent. No NumPy import is needed.
    """
    if not isinstance(value, str):
        return False
    if value in ONE_BYTE_DTYPES:
        return True
    if len(value) < 3 or value[0] not in ("<" if canonical else "<>"):
        return False
    return any(value == value[0] + kind + str(size)
               for kind, sizes in MULTIBYTE_KIND_SIZES.items() for size in sizes)


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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
    values = {"VmRSS_bytes": None}
    errors = {}
    for line in (status or "").splitlines():
        name, _, value = line.partition(":")
        if name in ("VmRSS", "VmHWM", "VmSwap"):
            try:
                parts = value.split()
                if len(parts) != 2 or parts[1] != "kB" or int(parts[0]) < 0:
                    raise ValueError("unusable native process-memory field")
                values[name + "_bytes"] = int(parts[0]) * 1024
            except (ValueError, IndexError) as error:
                values[name + "_bytes"] = None
                errors[name] = str(error)
    return {"monotonic_ns": time.monotonic_ns(), "pid": pid, **values,
            "process_status_readable": status is not None, "field_errors": errors,
            "host_available_bytes": mem_available()}


def process_identity(pid):
    """Read-only recovery marker facts; missing fields never prove process exit."""
    stat = read(f"/proc/{pid}/stat")
    result = {"pid": pid, "observed_monotonic_ns": time.monotonic_ns(),
              "boot_id": read("/proc/sys/kernel/random/boot_id"),
              "start_ticks": None, "ppid": None, "pgid": None, "session_id": None}
    if stat is not None:
        try:
            tail = stat.rsplit(")", 1)[1].split()  # fields 3 onward
            result.update(ppid=int(tail[1]), pgid=int(tail[2]), session_id=int(tail[3]),
                          start_ticks=int(tail[19]))
        except (ValueError, IndexError):
            result["stat_identity_error"] = "unusable process stat"
    try:
        result["executable"] = os.readlink(f"/proc/{pid}/exe")
    except OSError:
        result["executable"] = None
    return result


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


def rusage_snapshot(scope):
    """Scalar cumulative self sample; terminal observation belongs to wait4."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {"scope": scope, "monotonic_ns": time.monotonic_ns(),
            "ru_maxrss_native": usage.ru_maxrss, "ru_maxrss_native_units": "Linux KiB",
            "cumulative_high_water_bytes": int(usage.ru_maxrss) * 1024,
            "ru_minflt": usage.ru_minflt, "ru_majflt": usage.ru_majflt,
            "ru_nswap": usage.ru_nswap, "ru_inblock": usage.ru_inblock,
            "ru_oublock": usage.ru_oublock, "ru_utime_seconds": usage.ru_utime,
            "ru_stime_seconds": usage.ru_stime}


def array_identity(array, name, chunk_bytes=1048576):
    """RM84 array identity values with bounded C-order little-endian streaming.

    No fixture.identity/tobytes of an entire volume. Content digest excludes the
    name/shape/dtype just as frozen fixture.identity does; all four are recorded.
    Conversion buffers and each tobytes chunk are separately <= chunk_bytes
    (for supported <=16-byte numeric items) and can coexist. This parameter is
    not a total-scratch ceiling; metadata/allocator/hash state also consumes memory.
    """
    import numpy as np
    array = np.asarray(array)
    if array.dtype.kind not in "biufc" or array.dtype.itemsize > 16:
        raise ValueError("unsupported identity dtype")
    target = array.dtype.newbyteorder("<")
    if not legal_numeric_dtype(target.str, canonical=True):
        raise ValueError("unsupported canonical numeric dtype encoding")
    hasher = hashlib.sha256()
    if array.size:
        if array.flags.c_contiguous and (array.dtype.byteorder in ("<", "|") or
                                        (array.dtype.isnative and __import__("sys").byteorder == "little")):
            view = memoryview(array).cast("B")
            for offset in range(0, array.nbytes, chunk_bytes):
                hasher.update(view[offset:offset + chunk_bytes])
        else:
            for chunk in np.nditer(array, flags=["external_loop", "buffered", "zerosize_ok"],
                                   op_flags=["readonly"], op_dtypes=[target], order="C",
                                   buffersize=max(1, chunk_bytes // max(1, array.dtype.itemsize))):
                count = max(1, chunk_bytes // max(1, array.dtype.itemsize))
                for offset in range(0, chunk.size, count):
                    hasher.update(chunk[offset:offset + count].tobytes(order="C"))
    return name, tuple(array.shape), target.str, hasher.hexdigest()


def bounded_finite(array, chunk_bytes=1048576):
    """Bound finite-check boolean temporaries; the check still costs memory/time."""
    import numpy as np
    array = np.asarray(array)
    for chunk in np.nditer(array, flags=["external_loop", "buffered", "zerosize_ok"],
                           op_flags=["readonly"], order="C",
                           buffersize=max(1, chunk_bytes // max(1, array.dtype.itemsize))):
        count = max(1, chunk_bytes // max(1, array.dtype.itemsize))
        for offset in range(0, chunk.size, count):
            if not bool(np.isfinite(chunk[offset:offset + count]).all()):
                return False
    return True
