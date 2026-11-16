"""WS116 analysis-only observer. Source draft, never executed during preparation."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import importlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
SNAPSHOT_SCOPES = {
    "pre_call": "after input hashes/retention, before call timestamp",
    "call_end": "after call/end timestamp, before result observations",
    "post_observation": (
        "after context/hash/retention/finite/identity observations, "
        "before JSON serialization and teardown"
    ),
}
ONE_BYTE_DTYPES = frozenset(("|b1", "|i1", "|u1"))
MULTIBYTE_KIND_SIZES = {"i": (2, 4, 8), "u": (2, 4, 8), "f": (2, 4, 8, 16), "c": (8, 16)}
SESSION_BOOTSTRAP = r"""import json
import os
import sys

fd = int(sys.argv[1])
nonce = sys.argv[2]
stage = "arguments"
try:
    target = json.loads(sys.argv[3])
    stage = "setsid"
    os.setsid()
    stage = "readiness"
    message = json.dumps({"role":"bootstrap", "pid":os.getpid(), "ppid":os.getppid(),
        "pgid":os.getpgrp(), "session_id":os.getsid(0), "nonce":nonce,
        "executable":os.readlink("/proc/self/exe")}).encode() + b"\n"
    if len(message) > 512 or os.write(fd, message) != len(message):
        raise RuntimeError("invalid/incomplete bounded readiness write")
    os.close(fd)
    fd = -1
    stage = "exec"
    os.execve(target[0], target, os.environ.copy())
except BaseException as error:
    if fd >= 0:
        os.close(fd)
    detail = {"stage":stage, "type":type(error).__name__, "message":str(error)[:160]}
    os.write(2, ("WS116_BOOTSTRAP_ERROR " + json.dumps(detail) + "\n").encode())
    raise SystemExit(125 if stage == "exec" else 124)
"""
SESSION_BOOTSTRAP_SHA256 = hashlib.sha256(SESSION_BOOTSTRAP.encode()).hexdigest()


class StartupError(RuntimeError):
    """Fixed-route preparation/readiness failure, separate from numerical failure."""


class FixedSessionLaunch:
    """One plain-spawn/same-PID setsid/readiness/exec route; never reaps or signals.

    Caller creates one exact-PID wait owner immediately after spawn returns and
    uses direct-PID cleanup throughout the declared no-descendant workload.
    """

    def __init__(self, target_argv, env, nonce, stdout_fd, stderr_fd, pipe_bytes=1024):
        self.target_argv = list(target_argv)
        self.env = env
        self.nonce = nonce
        self.pipe_bytes = pipe_bytes
        self.pid = None
        self.ready = None
        self.eof = False
        self.data = bytearray()
        self.opened = set()
        self.fd_plan = {}
        if (
            not self.target_argv
            or self.target_argv[0] != sys.executable
            or not isinstance(nonce, str)
            or not 0 < len(nonce) <= 64
            or any(
                c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for c in nonce
            )
            or pipe_bytes != 1024
        ):
            raise StartupError("fixed pinned argv/nonce/readiness bound invalid")
        try:
            raw_read, raw_write = os.pipe2(os.O_CLOEXEC)
            self.opened.update((raw_read, raw_write))
            self.read_fd, write_fd = self._reserve(raw_read), self._reserve(raw_write)
            self._close(raw_read)
            self._close(raw_write)
            out_src, err_src = self._reserve(stdout_fd), self._reserve(stderr_fd)
            ready_dst = self._reserve(write_fd)
            self.parent_writers = (write_fd, ready_dst, out_src, err_src)
            os.set_blocking(self.read_fd, False)
            self.argv = [
                sys.executable,
                "-c",
                SESSION_BOOTSTRAP,
                str(ready_dst),
                nonce,
                json.dumps(self.target_argv),
            ]
            self.actions = [
                (os.POSIX_SPAWN_OPEN, 0, "/dev/null", os.O_RDONLY, 0),
                (os.POSIX_SPAWN_DUP2, out_src, 1),
                (os.POSIX_SPAWN_DUP2, err_src, 2),
                (os.POSIX_SPAWN_DUP2, write_fd, ready_dst),
                (os.POSIX_SPAWN_CLOSE, self.read_fd),
                (os.POSIX_SPAWN_CLOSE, write_fd),
                (os.POSIX_SPAWN_CLOSE, out_src),
                (os.POSIX_SPAWN_CLOSE, err_src),
            ]
            self.fd_plan = {
                "read": self.read_fd,
                "write_source": write_fd,
                "ready_destination": ready_dst,
                "stdout_source": out_src,
                "stderr_source": err_src,
            }
        except BaseException:
            self.close()
            raise

    def _reserve(self, fd):
        copied = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 64)
        self.opened.add(copied)
        return copied

    def _close(self, fd):
        if fd in self.opened:
            os.close(fd)
            self.opened.remove(fd)

    def spawn(self):
        """Return one kernel PID; there is no unsupported setsid spawn attribute."""
        self.pid = os.posix_spawn(sys.executable, self.argv, self.env, file_actions=self.actions)
        return self.pid

    def release_parent_writers(self):
        """Close aliases only after the caller has constructed its exact wait owner."""
        for fd in self.parent_writers:
            self._close(fd)

    def drain(self):
        """Drain bounded bytes even after cached terminal exit; validate one message."""
        if self.ready is not None:
            return self.ready
        for _ in range(8):
            if self.eof:
                break
            try:
                chunk = os.read(self.read_fd, 256)
            except BlockingIOError:
                break
            if not chunk:
                self.eof = True
                break
            if len(self.data) + len(chunk) > self.pipe_bytes:
                raise StartupError("readiness byte bound exceeded")
            self.data.extend(chunk)
        if b"\n" in self.data:
            if self.data.count(b"\n") != 1 or not self.data.endswith(b"\n"):
                raise StartupError("malformed/multiple readiness messages")
            try:
                value = json.loads(self.data.decode())
            except (ValueError, UnicodeError) as error:
                raise StartupError("malformed readiness JSON") from error
            if (
                not isinstance(value, dict)
                or value.get("role") != "bootstrap"
                or value.get("pid") != self.pid
                or value.get("ppid") != os.getpid()
                or value.get("pgid") != self.pid
                or value.get("session_id") != self.pid
                or value.get("nonce") != self.nonce
                or value.get("executable") != str(Path(sys.executable).resolve())
            ):
                raise StartupError("unverified same-PID/session/nonce readiness")
            self.ready = value
            self.close()
        elif self.eof:
            raise StartupError("readiness EOF without a valid message")
        return self.ready

    def close(self):
        """Close retained parent descriptors; no process ownership action occurs."""
        for fd in tuple(self.opened):
            self._close(fd)


def bootstrap_failure(path):
    """Read only a bounded fixed bootstrap-error prefix after child termination."""
    try:
        with Path(path).open("rb") as stream:
            first = stream.read(4096).split(b"\n", 1)[0]
        prefix = b"WS116_BOOTSTRAP_ERROR "
        if first.startswith(prefix):
            value = json.loads(first[len(prefix) :])
            if isinstance(value, dict) and value.get("stage") in (
                "arguments",
                "setsid",
                "readiness",
                "exec",
            ):
                return value
    except (OSError, ValueError, UnicodeError):
        pass
    return None


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
    return any(
        value == value[0] + kind + str(size)
        for kind, sizes in MULTIBYTE_KIND_SIZES.items()
        for size in sizes
    )


def read(path):
    """Read optional OS text; inaccessible files remain unknown."""
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def digest(path):
    """Hash file bytes with bounded reads."""
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def material_hashes(root):
    """Identify the declared product, fixture, dependency and method source bytes."""
    if root not in (Path("/workspace/work/issue-116"), Path("/workspace/work/issue-117")) or (
        root.resolve() != root
    ):
        raise ValueError("product root differs from fixed RB117 revision mapping")
    paths = sorted((root / "src/simrecon").rglob("*.py"))
    paths += [
        root / "uv.lock",
        root / "tests/reconstruction_summary_fixture.py",
        root / "tests/reconstruction_memory_benchmark.py",
    ]
    material = {str(p.relative_to(root)): digest(p) for p in paths}
    report = Path(__file__).resolve().parent
    if report != Path("/workspace/work/campaign/evidence/117/resource-method-source"):
        raise ValueError("method source differs from fixed RB117 external tooling directory")
    material.update(
        {
            "external_method:" + str(report / name): digest(report / name)
            for name in (
                "manifest.json",
                "observer.py",
                "run_attempt.py",
                "workload_child.py",
                "method_qualification.py",
            )
        }
    )
    return material


def cgroup_ancestors():
    """Resolve v2 membership against mountinfo, then include every visible ancestor.

    Unsupported v1, namespace path mismatch or inaccessible files fail admission.
    The visible mount root may hide external ancestors. Conditional admission
    records that uncertainty; the function never infers absent/unlimited parents.
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
        def decode(value):
            return (
                value.replace("\\040", " ")
                .replace("\\011", "\t")
                .replace("\\012", "\n")
                .replace("\\134", "\\")
            )

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
            rows.append(
                {
                    "path": str(current),
                    **{
                        key: read(current / key)
                        for key in (
                            "memory.max",
                            "memory.current",
                            "memory.peak",
                            "memory.events",
                            "memory.swap.max",
                            "memory.swap.current",
                        )
                    },
                }
            )
            if current == mount:
                break
            current = current.parent
        try:
            namespace = os.readlink("/proc/self/ns/cgroup")
        except OSError:
            namespace = None
        return {
            "membership": group,
            "mount_root": str(mount_root),
            "mount": str(mount),
            "namespace": namespace,
            "visible_ancestors": rows,
            "hidden_ancestors": (
                "unknown: ancestors outside the exposed domain are unobserved; "
                "no absence or unlimited claim"
            ),
        }
    return {"error": "effective cgroup mount could not be resolved"}


def mem_available():
    """Read exposed MemAvailable bytes, preserving a missing observation."""
    for line in (read("/proc/meminfo") or "").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) * 1024
    return None


def context(root):
    """Collect actual-time OS, resource and requested thread-control facts."""
    disk = os.statvfs(root)
    return {
        "system": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "host_id_sha256": hashlib.sha256(platform.node().encode()).hexdigest(),
        "pid": os.getpid(),
        "meminfo": read("/proc/meminfo"),
        "cgroup": cgroup_ancestors(),
        "rlimits": {
            key: resource.getrlimit(getattr(resource, key))
            for key in (
                "RLIMIT_AS",
                "RLIMIT_DATA",
                "RLIMIT_RSS",
                "RLIMIT_CPU",
                "RLIMIT_FSIZE",
                "RLIMIT_NOFILE",
            )
        },
        "disk_available_bytes": disk.f_bavail * disk.f_frsize,
        "threads": {key: os.environ.get(key) for key in THREADS},
        "allocator": {key: os.environ.get(key) for key in ("PYTHONMALLOC", "MALLOC_ARENA_MAX")},
    }


def process_sample(pid):
    """Sample child RSS and explicit missing/unusable observation diagnostics."""
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
    return {
        "monotonic_ns": time.monotonic_ns(),
        "pid": pid,
        **values,
        "process_status_readable": status is not None,
        "field_errors": errors,
        "host_available_bytes": mem_available(),
    }


def process_identity(pid):
    """Read-only recovery marker facts; missing fields never prove process exit."""
    stat = read(f"/proc/{pid}/stat")
    result = {
        "pid": pid,
        "observed_monotonic_ns": time.monotonic_ns(),
        "boot_id": read("/proc/sys/kernel/random/boot_id"),
        "start_ticks": None,
        "ppid": None,
        "pgid": None,
        "session_id": None,
    }
    if stat is not None:
        try:
            tail = stat.rsplit(")", 1)[1].split()  # fields 3 onward
            result.update(
                ppid=int(tail[1]),
                pgid=int(tail[2]),
                session_id=int(tail[3]),
                start_ticks=int(tail[19]),
            )
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
            events.append(
                {
                    "stage": stage,
                    "time_index": kwargs.get("time_index"),
                    "edge": edge,
                    "monotonic_ns": time.monotonic_ns(),
                    "ru_maxrss_native_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                }
            )

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
    return {
        "scope": scope,
        "monotonic_ns": time.monotonic_ns(),
        "ru_maxrss_native": usage.ru_maxrss,
        "ru_maxrss_native_units": "Linux KiB",
        "cumulative_high_water_bytes": int(usage.ru_maxrss) * 1024,
        "ru_minflt": usage.ru_minflt,
        "ru_majflt": usage.ru_majflt,
        "ru_nswap": usage.ru_nswap,
        "ru_inblock": usage.ru_inblock,
        "ru_oublock": usage.ru_oublock,
        "ru_utime_seconds": usage.ru_utime,
        "ru_stime_seconds": usage.ru_stime,
    }


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
        if array.flags.c_contiguous and (
            array.dtype.byteorder in ("<", "|")
            or (array.dtype.isnative and __import__("sys").byteorder == "little")
        ):
            view = memoryview(array).cast("B")
            for offset in range(0, array.nbytes, chunk_bytes):
                hasher.update(view[offset : offset + chunk_bytes])
        else:
            for chunk in np.nditer(
                array,
                flags=["external_loop", "buffered", "zerosize_ok"],
                op_flags=["readonly"],
                op_dtypes=[target],
                order="C",
                buffersize=max(1, chunk_bytes // max(1, array.dtype.itemsize)),
            ):
                count = max(1, chunk_bytes // max(1, array.dtype.itemsize))
                for offset in range(0, chunk.size, count):
                    hasher.update(chunk[offset : offset + count].tobytes(order="C"))
    return name, tuple(array.shape), target.str, hasher.hexdigest()


def bounded_finite(array, chunk_bytes=1048576):
    """Bound finite-check boolean temporaries; the check still costs memory/time."""
    import numpy as np

    array = np.asarray(array)
    for chunk in np.nditer(
        array,
        flags=["external_loop", "buffered", "zerosize_ok"],
        op_flags=["readonly"],
        order="C",
        buffersize=max(1, chunk_bytes // max(1, array.dtype.itemsize)),
    ):
        count = max(1, chunk_bytes // max(1, array.dtype.itemsize))
        for offset in range(0, chunk.size, count):
            if not bool(np.isfinite(chunk[offset : offset + count]).all()):
                return False
    return True
