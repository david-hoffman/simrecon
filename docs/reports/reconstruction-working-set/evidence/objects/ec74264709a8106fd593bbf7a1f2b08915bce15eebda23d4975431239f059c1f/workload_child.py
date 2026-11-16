"""One WS116 workflow and bounded observations; unexecuted method draft."""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import resource
import struct
import sys
import time

from observer import (SNAPSHOT_SCOPES, THREADS, array_identity, bounded_finite, context,
                      material_hashes, rusage_snapshot, stage_observer)


def execute(spec, root, record):
    if sys.platform != "linux" or struct.calcsize("P") != 8:
        raise ValueError("requires pinned 64-bit Linux interpreter")
    if any(os.environ.get(name) != "1" for name in THREADS):
        raise ValueError("four thread controls must be 1 before startup")
    record["material_hashes_before"] = material_hashes(root)
    if record["material_hashes_before"] != spec["expected_material_hashes"]:
        raise ValueError("material identity differs before imports/generation")
    sys.path.insert(0, str(root / "tests"))
    import numpy as np
    import scipy
    import scipy.fft
    import simrecon
    import reconstruction_summary_fixture as fixture
    # Frozen value protocol streams contiguous buffers without copying, and
    # bounds noncontiguous/endian conversion to 65536 elements per iterator chunk.
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
    record["input_sha256"] = public_value_sha256(case)
    record["input_arrays"] = {"specimen": array_identity(case["specimen"], "specimen"),
                              "transfer": array_identity(case["transfer"].samples, "transfer.samples")}
    # Case owns callers through output observation. No reference workflow exists.
    record["caller_retained"] = retained_payload(case)
    events = []
    observer = stage_observer(events) if spec["profile"] else contextlib.nullcontext()
    entry = simrecon.reconstruct_summary if spec["mode"] == "summary" else simrecon.reconstruct_workflow
    record["phase"] = "workflow_call"
    record["snapshots"] = {}
    with observer:
        record["snapshots"]["pre_call"] = rusage_snapshot(SNAPSHOT_SCOPES["pre_call"])
        start_ns = time.monotonic_ns()
        result = entry(**case)
        end_ns = time.monotonic_ns()
        record["snapshots"]["call_end"] = rusage_snapshot(SNAPSHOT_SCOPES["call_end"])
    record.update(call_start_monotonic_ns=start_ns, call_end_monotonic_ns=end_ns,
                  elapsed_call_seconds=(end_ns - start_ns) / 1e9)
    record["phase"] = "post_call_observation"
    parameters = result if spec["mode"] == "summary" else result.parameters
    common = {key: getattr(result, key) for key in ("image", "x_um", "y_um", "z_um")}
    common.update({key: getattr(parameters, key) for key in (
        "carriers_cyc_um", "modulation", "raw_modulation")})
    finite = all(bounded_finite(value) for value in common.values())
    record.update(output_hashes={key: array_identity(value, key) for key, value in common.items()},
                  common_output_sha256=public_value_sha256(common),
                  public_result_sha256=public_value_sha256(result),
                  branches=parameters.branches, finite_common_fields=finite,
                  result_retained=retained_payload(result), stages=events,
                  context=context(root), python=sys.version, executable=sys.executable,
                  numpy=np.__version__, scipy=scipy.__version__, numpy_backend=np.__config__.CONFIG,
                  scipy_fft_default_workers=scipy.fft.get_workers(),
                  effective_worker_limits="unknown beyond declared environment/default FFT setting",
                  product_module=str(module_path.relative_to(root)))
    record["material_hashes_after"] = material_hashes(root)
    record["material_identity_matches"] = record["material_hashes_before"] == record["material_hashes_after"]
    if not record["material_identity_matches"]:
        record["status"] = "material_identity_failure"
    elif not finite:
        record["status"] = "nonfinite_scientific_failure"
    else:
        record["status"] = "finite_observation_pending_qualification"
    record["phase"] = "observation_complete"
    record["snapshots"]["post_observation"] = rusage_snapshot(SNAPSHOT_SCOPES["post_observation"])
    record["snapshot_limits"] = (
        "Cumulative child high-water snapshots, not isolated stage allocations or complete-child peak. "
        "Parent sole wait4 terminal rusage covers subsequent JSON/teardown; neither scope is numerical-only.")


def main():
    record = {"protocol": "WS116-child-v2", "status": "observation_failure", "phase": "request_read",
              "pid": os.getpid(), "started_monotonic_ns": time.monotonic_ns()}
    try:
        spec = json.loads(Path(sys.argv[1]).read_text())
        root = Path(sys.argv[2]).resolve()
        record["spec"] = spec
        execute(spec, root, record)
    except BaseException as error:
        record.update(status="workflow_exception" if record["phase"] == "workflow_call" else "observation_failure",
                      type=type(error).__name__, message=str(error), error_monotonic_ns=time.monotonic_ns())
    print(json.dumps(record, default=str), flush=True)
    return 0 if record["status"] == "finite_observation_pending_qualification" else 1


if __name__ == "__main__":
    raise SystemExit(main())
