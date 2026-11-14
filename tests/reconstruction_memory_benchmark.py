"""Single fresh-process RM84 experiment; orchestration is external and source-free.

Run through scripts/source_free_check.py. Set all thread controls before process
startup; this CLI rejects missing controls. One invocation is exactly one call.
No disk arrays, numerical children, export or implicit growth are performed.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import platform
import resource
import struct
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

THREAD_CONTROLS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def public_value_sha256(value: Any) -> str:
    """Fingerprint all declared public values, preserving types, order and float bits.

    Record class names and storage aliasing are deliberately absent: compact
    record classes need not have fixed names, and ownership has separate tests.
    Array bytes use C order and little endian with bounded conversion buffers.
    This supplements independent scientific expectations; it is not an oracle.
    """
    import numpy as np

    digest = hashlib.sha256()
    active: set[int] = set()

    def token(kind: str, content: bytes) -> None:
        digest.update(kind.encode("ascii") + b":" + str(len(content)).encode("ascii") + b":")
        digest.update(content)

    def visit(item: Any) -> None:
        if item is None:
            token("none", b"")
        elif type(item) is bool:
            token("bool", b"1" if item else b"0")
        elif type(item) is int:
            token("int", str(item).encode("ascii"))
        elif type(item) is float:
            token("float64", struct.pack("<d", item))
        elif type(item) is complex:
            token("complex128", struct.pack("<dd", item.real, item.imag))
        elif type(item) is str:
            token("str", item.encode("utf-8"))
        elif type(item) is bytes:
            token("bytes", item)
        elif isinstance(item, (np.ndarray, np.generic)):
            array = np.asarray(item)
            if array.dtype.kind not in "biufc":
                raise ValueError("unsupported public numeric value dtype")
            token("ndarray" if isinstance(item, np.ndarray) else "numpy-scalar", b"")
            visit(array.shape)
            visit(array.dtype.newbyteorder("<").str)
            token("array-bytes", str(array.nbytes).encode("ascii"))
            if not array.nbytes:
                return
            if array.flags.c_contiguous and (
                array.dtype.byteorder in ("<", "|")
                or (array.dtype.isnative and sys.byteorder == "little")
            ):
                digest.update(memoryview(array).cast("B"))
                return
            for chunk in np.nditer(
                array,
                flags=["external_loop", "buffered", "zerosize_ok"],
                op_flags=["readonly"],
                op_dtypes=[array.dtype.newbyteorder("<")],
                order="C",
                buffersize=65536,
            ):
                digest.update(np.asarray(chunk).tobytes())
        else:
            if id(item) in active:
                raise ValueError("cyclic public value")
            active.add(id(item))
            try:
                if dataclasses.is_dataclass(item) and not isinstance(item, type):
                    fields = dataclasses.fields(item)
                    token("record", str(len(fields)).encode("ascii"))
                    for field in fields:
                        visit(field.name)
                        visit(getattr(item, field.name))
                elif isinstance(item, Mapping):
                    token("mapping", str(len(item)).encode("ascii"))
                    for key, child in item.items():
                        visit(key)
                        visit(child)
                elif isinstance(item, (tuple, list)):
                    token(
                        "tuple" if isinstance(item, tuple) else "list",
                        str(len(item)).encode("ascii"),
                    )
                    for child in item:
                        visit(child)
                else:
                    raise ValueError("unsupported public value object")
            finally:
                active.remove(id(item))

    token("protocol", b"RM84-public-values-v1")
    visit(value)
    return digest.hexdigest()


def rss_bytes(native: int, system: str) -> int:
    """Convert ru_maxrss using its documented Linux/macOS native units."""
    if system == "Linux":
        return native * 1024
    if system == "Darwin":
        return native
    raise ValueError(f"unsupported ru_maxrss units on {system}")


def retained_payload(value: Any) -> dict[str, Any]:
    """Count reachable NumPy backing allocations once, even disjoint strided views.

    Python metadata is an estimate from sys.getsizeof excluding array buffers;
    allocator overhead and external/backend workspaces are not attributed.
    """
    import numpy as np

    seen: set[int] = set()
    backing: dict[int, int] = {}
    arrays: list[dict[str, Any]] = []
    metadata = 0

    def visit(item: Any, path: str) -> None:
        nonlocal metadata
        if id(item) in seen:
            return
        seen.add(id(item))
        if isinstance(item, np.ndarray):
            base = item
            while isinstance(base.base, np.ndarray):
                base = base.base
            if base.base is not None:
                # A foreign owner can hide a larger allocation. Do not mislabel
                # the visible view's bytes as a complete retained-payload count.
                raise ValueError("unsupported external array backing owner")
            backing[id(base)] = base.nbytes
            metadata += max(0, sys.getsizeof(item) - (item.nbytes if item.flags.owndata else 0))
            arrays.append(
                dict(path=path, shape=item.shape, dtype=item.dtype.str, bytes=item.nbytes)
            )
        else:
            metadata += sys.getsizeof(item)
            if dataclasses.is_dataclass(item) and not isinstance(item, type):
                for field in dataclasses.fields(item):
                    visit(getattr(item, field.name), f"{path}.{field.name}")
                # Instance caches/extra attributes also keep allocations alive.
                for key, child in getattr(item, "__dict__", {}).items():
                    visit(child, f"{path}.{key}")
                for cls in type(item).__mro__:
                    slots = getattr(cls, "__slots__", ())
                    slots = (slots,) if isinstance(slots, str) else slots
                    for key in slots:
                        if key not in {"__dict__", "__weakref__"} and hasattr(item, key):
                            visit(getattr(item, key), f"{path}.{key}")
            elif isinstance(item, Mapping):
                for key, child in item.items():
                    visit(key, f"{path}.key")
                    visit(child, f"{path}.{key}")
            elif isinstance(item, (tuple, list)):
                for index, child in enumerate(item):
                    visit(child, f"{path}.{index}")
            elif item is not None and not isinstance(
                item, (str, bytes, int, float, complex, bool, np.generic)
            ):
                raise ValueError("unsupported retained value object")

    visit(value, "result")
    return dict(
        array_payload_bytes=sum(backing.values()),
        unique_backings=len(backing),
        arrays=arrays,
        python_metadata_estimate_bytes=metadata,
        metadata_limit=(
            "sys.getsizeof excludes allocator overhead and untraversed foreign objects"
        ),
    )


def read_system_file(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def host_context() -> dict[str, Any]:
    """Expose bounded OS resource facts, never private path contents or source."""
    return dict(
        system=platform.system(),
        release=platform.release(),
        machine=platform.machine(),
        python=sys.version,
        host_id_sha256=hashlib.sha256(platform.node().encode()).hexdigest(),
        pointer_bits=8 * __import__("struct").calcsize("P"),
        meminfo=read_system_file("/proc/meminfo"),
        cgroup_memory_max=read_system_file("/sys/fs/cgroup/memory.max"),
        cgroup_memory_current=read_system_file("/sys/fs/cgroup/memory.current"),
        cgroup_swap_max=read_system_file("/sys/fs/cgroup/memory.swap.max"),
        cgroup_swap_current=read_system_file("/sys/fs/cgroup/memory.swap.current"),
        allocator={key: os.environ.get(key) for key in ("PYTHONMALLOC", "MALLOC_ARENA_MAX")},
        threads={key: os.environ.get(key) for key in THREAD_CONTROLS},
        unsupported_controls=(
            "environment requests reported; per-library effective worker count unknown"
        ),
        swap_attribution="unknown",
        backend_workspace_bytes="unknown",
    )


def execute(args: argparse.Namespace) -> dict[str, Any]:
    """Generate, hash, retain callers, execute once and report raw observations."""
    for key in THREAD_CONTROLS:
        if os.environ.get(key) != "1":
            raise ValueError(f"{key}=1 must be set before process startup")
    import numpy as np
    import scipy
    import scipy.fft

    import simrecon
    from reconstruction_summary_fixture import RESOURCE_SHAPES, identity, scenario, workload

    if args.case == "primary":
        shape = tuple(args.shape)
        if shape not in RESOURCE_SHAPES:
            raise ValueError("primary shape is outside frozen experiment inventory")
        case = workload(shape, search=args.search)
    else:
        case = scenario(args.case)
    context = host_context()
    before = resource.getrusage(resource.RUSAGE_SELF)
    hashes = dict(
        specimen=identity(case["specimen"], "specimen"),
        transfer=identity(case["transfer"].samples, "transfer.samples"),
    )
    # Hashing is included in whole-process accounting and precedes the call baseline.
    baseline = resource.getrusage(resource.RUSAGE_SELF)
    started = time.monotonic()
    entry = getattr(
        simrecon, "reconstruct_summary" if args.mode == "summary" else "reconstruct_workflow"
    )
    result = entry(**case)
    elapsed = time.monotonic() - started
    payload = retained_payload(result)
    result_hashes = {
        name: identity(getattr(result, name), name) for name in ("image", "x_um", "y_um", "z_um")
    }
    parameters = result if args.mode == "summary" else result.parameters
    result_hashes.update(
        {
            name: identity(getattr(parameters, name), name)
            for name in ("carriers_cyc_um", "modulation", "raw_modulation")
        }
    )
    public_fingerprint = public_value_sha256(result)
    # Include result hashing and the observer in the final whole-process high-water.
    after = resource.getrusage(resource.RUSAGE_SELF)
    return dict(
        protocol="RM84-v1",
        label=args.label,
        repetition=args.repetition,
        mode=args.mode,
        case=args.case,
        search=args.search,
        input_hashes=hashes,
        output_hashes=result_hashes,
        public_value_fingerprint=dict(protocol="RM84-public-values-v1", sha256=public_fingerprint),
        branches=parameters.branches,
        elapsed_call_seconds=elapsed,
        baseline_ru_maxrss_native=baseline.ru_maxrss,
        peak_ru_maxrss_native=after.ru_maxrss,
        native_ru_maxrss_units="KiB" if platform.system() == "Linux" else "bytes",
        baseline_high_water_bytes=rss_bytes(baseline.ru_maxrss, platform.system()),
        whole_process_peak_bytes=rss_bytes(after.ru_maxrss, platform.system()),
        page_faults=dict(
            before_minor=before.ru_minflt,
            before_major=before.ru_majflt,
            after_minor=after.ru_minflt,
            after_major=after.ru_majflt,
        ),
        swaps_native=dict(before=before.ru_nswap, after=after.ru_nswap),
        block_io_native=dict(inblock=after.ru_inblock, oublock=after.ru_oublock),
        disk_array_bytes=0,
        fixture_disk_bytes=Path(__file__).stat().st_size,
        fixture_disk_allocated_bytes=getattr(Path(__file__).stat(), "st_blocks", 0) * 512,
        disk_use_limit=(
            "CLI creates no files; redirected logs/artifacts must be measured externally"
        ),
        revision=args.revision,
        tree=args.tree,
        dirty=args.dirty,
        fixture_sha256=hashlib.sha256(
            Path(__file__).with_name("reconstruction_summary_fixture.py").read_bytes()
        ).hexdigest(),
        benchmark_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        lock_sha256=hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
        numpy_version=np.__version__,
        scipy_version=scipy.__version__,
        numpy_backend=np.__config__.CONFIG,
        scipy_fft_default_workers=scipy.fft.get_workers(),
        context=context,
        retained=payload,
        limits=(
            "Peak includes imports, inputs, hashing and numerical workspaces; "
            "no peak-minus-baseline attribution. Python metadata estimate is incomplete."
        ),
    )


def main() -> int:
    """Require explicit provenance; emit failures as data and keep nonzero status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("full", "summary"), required=True)
    parser.add_argument(
        "--case",
        choices=("primary", "signed", "2d", "between", "within", "off1", "off2"),
        default="primary",
    )
    parser.add_argument("--shape", nargs=5, type=int, default=(1, 3, 8, 32, 32))
    parser.add_argument("--search", action="store_true")
    parser.add_argument("--label", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--tree", required=True)
    parser.add_argument("--dirty", choices=("true", "false"), required=True)
    parser.add_argument("--repetition", choices=(1, 2, 3), type=int, required=True)
    args = parser.parse_args()
    try:
        record = execute(args)
    except BaseException as error:
        print(
            json.dumps(
                dict(
                    status="failure",
                    type=type(error).__name__,
                    message=str(error),
                    label=args.label,
                    repetition=args.repetition,
                    mode=args.mode,
                )
            )
        )
        return 1
    print(json.dumps(dict(status="pass", **record), default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
