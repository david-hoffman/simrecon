"""Exactly one WS116 workflow; invoked only by admitted external runner."""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import resource
import struct
import sys
import time

from observer import THREADS, context, stage_observer


def execute(spec, root):
    if sys.platform != "linux" or struct.calcsize("P") != 8:
        raise ValueError("requires pinned 64-bit Linux interpreter")
    if any(os.environ.get(name) != "1" for name in THREADS):
        raise ValueError("four thread controls must be 1 before startup")
    # Frozen RM84 helpers are read-only and imported from this exact worktree.
    sys.path.insert(0, str(root / "tests"))
    import numpy as np
    import scipy
    import scipy.fft
    import simrecon
    import reconstruction_summary_fixture as fixture
    from reconstruction_memory_benchmark import public_value_sha256, retained_payload

    module_path = Path(simrecon.__file__).resolve()
    if not module_path.is_relative_to((root / "src/simrecon").resolve()):
        raise ValueError("product import is not the declared worktree")
    case = (fixture.scenario(spec["case"]) if "case" in spec else
            fixture.workload(tuple(spec["shape"]), search=spec["search"]))
    if tuple(case["specimen"].shape[i] for i in (0, 1, 3, 4, 5)) != tuple(spec["shape"]):
        raise ValueError("fixture shape differs from frozen condition")
    if case["carrier"]["search_carriers"] != spec["search"]:
        raise ValueError("fixture search differs from frozen condition")
    input_fingerprint = public_value_sha256(case)
    # These caller references remain alive through final result observation.
    caller_payload = retained_payload(case)
    events = []
    observer = stage_observer(events) if spec["profile"] else contextlib.nullcontext()
    entry = simrecon.reconstruct_summary if spec["mode"] == "summary" else simrecon.reconstruct_workflow
    before = resource.getrusage(resource.RUSAGE_SELF)
    with observer:
        baseline = resource.getrusage(resource.RUSAGE_SELF)
        start_ns = time.monotonic_ns()
        result = entry(**case)
        end_ns = time.monotonic_ns()
    parameters = result if spec["mode"] == "summary" else result.parameters
    common = {key: getattr(result, key) for key in ("image", "x_um", "y_um", "z_um")}
    common.update({key: getattr(parameters, key) for key in (
        "carriers_cyc_um", "modulation", "raw_modulation")})
    finite = all(bool(np.isfinite(value).all()) for value in common.values())
    # Result traversal/hashing occurs after call timing, before final high-water.
    output_hashes = {key: fixture.identity(value, key) for key, value in common.items()}
    common_fingerprint = public_value_sha256(common)
    public_fingerprint = public_value_sha256(result)
    retained = retained_payload(result)
    after = resource.getrusage(resource.RUSAGE_SELF)
    return {"status": "pass" if finite else "nonfinite_scientific_failure", "spec": spec,
            "input_sha256": input_fingerprint, "output_hashes": output_hashes,
            "common_output_sha256": common_fingerprint, "public_result_sha256": public_fingerprint,
            "branches": parameters.branches, "finite_common_fields": finite,
            "call_start_monotonic_ns": start_ns, "call_end_monotonic_ns": end_ns,
            "elapsed_call_seconds": (end_ns - start_ns) / 1e9,
            "precall_high_water_native": baseline.ru_maxrss,
            "whole_process_high_water_native": after.ru_maxrss,
            "ru_maxrss_units": "Linux KiB", "ru_maxrss_multiplier_to_bytes": 1024,
            "whole_process_peak_bytes": int(after.ru_maxrss) * 1024,
            "precall_high_water_bytes": int(baseline.ru_maxrss) * 1024,
            "page_faults": {"before_minor": before.ru_minflt, "after_minor": after.ru_minflt,
                            "before_major": before.ru_majflt, "after_major": after.ru_majflt},
            "swaps_native": [before.ru_nswap, after.ru_nswap],
            "block_io_native": [after.ru_inblock, after.ru_oublock],
            "caller_retained": caller_payload, "result_retained": retained,
            "stages": events, "context": context(root), "python": sys.version,
            "executable": sys.executable, "numpy": np.__version__, "scipy": scipy.__version__,
            "numpy_backend": np.__config__.CONFIG, "scipy_fft_default_workers": scipy.fft.get_workers(),
            "effective_worker_limits": "unknown beyond reported controls/default worker setting",
            "product_module": str(module_path.relative_to(root)),
            "limits": "RSS includes imports/generator/input and output hashes/call/result traversal; no isolated peak by subtraction. Native workspace/allocator/shared pages unattributed."}


def main():
    spec = json.loads(Path(sys.argv[1]).read_text())
    root = Path(sys.argv[2]).resolve()
    try:
        record = execute(spec, root)
    except BaseException as error:
        record = {"status": "failure", "spec": spec, "type": type(error).__name__,
                  "message": str(error), "monotonic_ns": time.monotonic_ns()}
    print(json.dumps(record, default=str), flush=True)
    return 0 if record["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
