"""Finite Q0/Q1, four Q2 cases, bounded Q4 parser and Q5 tiny-hash slices.

One case per exact root release. No workflow, orphan topology,
automatic retry/growth or accepted-method edits occur here.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QUAL = HERE / "qualification"
PASS = "case_pass_scoped_only"
Q2_CASES = ("Q2-default-term", "Q2-ignore-term-kill", "Q2-deadline", "Q2-supported-sigint")
Q4_CASE = "Q4-parser"
Q5_CASE = "Q5-tinyhash"
M6_CASE = "method6-rss-controls"
Q2_EVIDENCE = (
    (
        "q2-default-term-a1",
        "04adceb4b0362c55902889d01738beb582850655604dfe478ef8a2c27edba68f",
        "3db07d01c27eebb4b7ff5698f1b13be00da4e973f11544d4069fa7175050d0ed",
        15,
    ),
    (
        "q2-ignore-term-kill-a1",
        "14945d428577e75365b5c3202d31c265577520a5ee8e8018c84d60b868a1bc8d",
        "770881e6f83e0e8bdd03f12154724dcdb76d21898690ecb85a70bba2bb8a2396",
        9,
    ),
    (
        "q2-deadline-a1",
        "ab9589156df4668b0109317776a52a314b131a35ed541be86bb9ccd5cede0733",
        "5d44e75d98d30cde5eeb5fef59829e7d440c734e6146ceb673d175149d06140c",
        15,
    ),
    (
        "q2-supported-sigint-a1",
        "6d8d320f5649c1440f53811623a820e28363a8b0d400894fb1bfac1135d9b946",
        "91d9219f68482219ed385fb2b57b397c407067cfaae86279e181736d593d8c63",
        9,
    ),
)
RETAINED_METHOD_KEYS = (
    "docs/reports/reconstruction-working-set/observer.py",
    "docs/reports/reconstruction-working-set/run_attempt.py",
    "docs/reports/reconstruction-working-set/workload_child.py",
    "docs/reports/reconstruction-working-set/manifest.json",
    "docs/reports/reconstruction-working-set/qualification/fixtures/stdlib-child.txt",
    "uv.lock",
)


def require(condition, message):
    """Stop on a prerequisite/outcome mismatch; missing evidence is never success."""
    if not condition:
        raise RuntimeError(message)


def write(path, value):
    """Preserve qualification metadata without claiming scientific observations."""
    path.write_text(json.dumps(value, indent=2, default=str) + "\n")


def no_product():
    """Check that no product module has been imported in this narrow slice."""
    require(
        not any(name == "simrecon" or name.startswith("simrecon.") for name in sys.modules),
        "forbidden product module import",
    )


def source_identities(grant, obs):
    """Bind coordinator-frozen method, driver, lock and finite fixture bytes."""
    required = {
        "docs/reports/reconstruction-working-set/method_qualification.py",
        "docs/reports/reconstruction-working-set/observer.py",
        "docs/reports/reconstruction-working-set/run_attempt.py",
        "docs/reports/reconstruction-working-set/workload_child.py",
        "docs/reports/reconstruction-working-set/manifest.json",
        "docs/reports/reconstruction-working-set/qualification/inventory.json",
        "docs/reports/reconstruction-working-set/qualification/fixtures/stdlib-child.txt",
        "uv.lock",
    }
    if grant["case"] in (*Q2_CASES, Q4_CASE, Q5_CASE):
        required.add(
            "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt"
        )
    if grant["case"] in (Q4_CASE, Q5_CASE):
        required.add(
            "docs/reports/reconstruction-working-set/qualification/fixtures/parser-vectors-v1.json"
        )
    if grant["case"] in (Q5_CASE, M6_CASE):
        required.update(
            {
                "docs/reports/reconstruction-working-set/qualification/fixtures/tiny-hash-vectors-v1.json",
                "tests/reconstruction_summary_fixture.py",
                "tests/reconstruction_memory_benchmark.py",
            }
        )
    if grant["case"] == M6_CASE:
        required.update(
            {
                "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt",
                "docs/reports/reconstruction-working-set/qualification/fixtures/parser-vectors-v1.json",
                "docs/reports/reconstruction-working-set/qualification/fixtures/method6-rss-controls-v1.json",
            }
        )
    require(required <= set(grant["source_sha256"]), "mandatory frozen material identity missing")
    actual = {}
    for name in grant["source_sha256"]:
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), "source identity outside named worktree")
        actual[name] = obs.digest(path)
    require(actual == grant["source_sha256"], "source/fixture identity changed")
    return actual


def admission(args, grant, inventory, obs, method, out):
    """Require exact release, fresh correspondence and conservative case margins."""
    require(args.case != M6_CASE, "method6 uses only its isolated pure entry path")
    expected_scope = (
        "WS116-Q5-tinyhash-v1"
        if args.case == Q5_CASE
        else "WS116-Q4-parser-v1"
        if args.case == Q4_CASE
        else "WS116-Q2-lifecycle-v1"
        if args.case in Q2_CASES
        else "WS116-Q0-Q1-method5-v1"
    )
    require(
        grant["approved"] is True and grant["scope"] == expected_scope,
        "no exact qualification phase release",
    )
    require(
        grant["case"] == args.case and grant["attempt_id"] == args.attempt_id,
        "grant/case/attempt mismatch",
    )
    require(method.git("rev-parse", "HEAD") == grant["candidate_head"], "candidate HEAD changed")
    require(str(Path(sys.executable).resolve()) == grant["python_resolved"], "unpinned interpreter")
    require(
        all(os.environ.get(name) == "1" for name in obs.THREADS),
        "thread controls absent before startup",
    )
    require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL, "SIGCHLD ownership unavailable")
    require(
        signal.getsignal(signal.SIGINT) is signal.default_int_handler,
        "default SIGINT handler required",
    )
    require(
        grant["campaign_ownership_resolved"] is True,
        "unresolved previous process/resource ownership",
    )
    require(grant["bounds"] == inventory["common_bounds"], "bounds differ from frozen inventory")
    require(
        inventory["bootstrap_sha256"] == obs.SESSION_BOOTSTRAP_SHA256,
        "integrated bootstrap identity differs from qualification inventory",
    )
    identities = source_identities(grant, obs)
    if args.case in (*Q2_CASES, Q4_CASE, Q5_CASE):
        require(
            identities[
                "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt"
            ]
            == inventory["lifecycle_target_sha256"],
            "Q2 target fixture digest differs from inventory",
        )
    if args.case in (Q4_CASE, Q5_CASE):
        phase = "q4" if args.case == Q4_CASE else "q5"
        require(grant["phase_bounds"] == inventory[phase + "_bounds"], "phase bounds differ")
        require(
            identities[
                "docs/reports/reconstruction-working-set/qualification/fixtures/parser-vectors-v1.json"
            ]
            == inventory["q4_fixture_sha256"],
            "Q4 scalar fixture differs",
        )
    if args.case == Q5_CASE:
        require(
            identities[
                "docs/reports/reconstruction-working-set/qualification/fixtures/tiny-hash-vectors-v1.json"
            ]
            == inventory["q5_fixture_sha256"],
            "Q5 tiny fixture differs",
        )
    case = next(row for row in inventory["cases"] if row["id"] == args.case)
    cg = obs.cgroup_ancestors()
    require("error" not in cg, "observable cgroup resolution unavailable")
    bounds = inventory["common_bounds"]
    for key in ("process_stop_bytes", "host_min_available_bytes"):
        require(grant[key] == bounds[key], "grant stop setting differs from inventory")
    for key in ("predicted_child_peak_bytes", "native_allocator_allowance_bytes", "reserve_bytes"):
        require(
            grant["resource_domain"][key] == bounds[key],
            "grant allowance/reserve differs from inventory",
        )
    require(
        set(grant["ancestor_stop_bytes"]) == {row["path"] for row in cg["visible_ancestors"]},
        "visible ancestor stop missing/extra",
    )
    for row in cg["visible_ancestors"]:
        stop = grant["ancestor_stop_bytes"][row["path"]]
        require(type(stop) is int and stop > int(row["memory.current"]), "unusable ancestor stop")
        require(
            row["memory.max"] == "max" or stop < int(row["memory.max"]),
            "ancestor stop leaves no finite-limit margin",
        )
    method.exposed_domain_admission(grant, cg)
    available = obs.mem_available()
    require(
        available is not None and available > grant["host_min_available_bytes"],
        "host headroom missing/insufficient",
    )
    if args.case in (*Q2_CASES, Q4_CASE, Q5_CASE):
        require(grant["prerequisites"] == {}, "Q2 uses the one explicit retained-Q1 mapping")
        retained = retained_q1(grant, identities, obs)
        write(out / "retained-Q1-applicability.json", retained)
        if args.case in (Q4_CASE, Q5_CASE):
            write(out / "retained-Q2-applicability.json", retained_q2(identities, obs))
        if args.case == Q5_CASE:
            write(out / "retained-Q4-applicability.json", retained_q4(identities, obs))
    else:
        require(set(grant["prerequisites"]) == set(case["requires"]), "prerequisites missing/extra")
        for name, evidence in grant["prerequisites"].items():
            path = Path(evidence["path"])
            require(obs.digest(path) == evidence["sha256"], "prerequisite receipt changed")
            prior = json.loads(path.read_text())
            require(
                prior["case"] == name and prior["status"] == PASS, "prerequisite incomplete/failed"
            )
            require(prior["source_sha256"] == identities, "prerequisite source identity changed")
            require(
                prior["exposed_domain"] == grant["resource_domain"]["expected_exposed"],
                "prerequisite domain changed",
            )
    write(out / "preflight.json", obs.context(ROOT))
    return identities


def retained_q1(grant, current, obs):
    """Retain one exact passed Q1 only for six explicitly unchanged inputs."""
    evidence = grant["retained_method5_Q1"]
    receipt_path = QUAL / "attempts/q1-method5-a1/receipt.json"
    life_path = QUAL / "attempts/q1-method5-a1/normal-lifecycle.json"
    require(
        Path(evidence["receipt_path"]).resolve() == receipt_path.resolve()
        and evidence["receipt_sha256"]
        == "23534b9f0298fd2de621a6e2b8b0b7bb993d9ce094d3d716aefdd5b29d7016ce"
        and obs.digest(receipt_path) == evidence["receipt_sha256"],
        "retained Q1 receipt not exact accepted evidence",
    )
    require(
        Path(evidence["lifecycle_path"]).resolve() == life_path.resolve()
        and evidence["lifecycle_sha256"]
        == "b6997727dea0d12fe5d497d335f0f2fb483aa44273e997a5380223f197fe729a"
        and obs.digest(life_path) == evidence["lifecycle_sha256"],
        "retained Q1 lifecycle bytes changed",
    )
    prior = json.loads(receipt_path.read_text())
    life = json.loads(life_path.read_text())
    require(
        prior["status"] == PASS
        and prior["case"] == "Q1-normal"
        and prior["attempt_id"] == "q1-method5-a1",
        "retained Q1 outcome not successful",
    )
    require(
        all(prior["source_sha256"][key] == current[key] for key in RETAINED_METHOD_KEYS),
        "accepted method/old fixture/lock changed: retain no Q1 applicability",
    )
    require(
        life["bootstrap_sha256"] == obs.SESSION_BOOTSTRAP_SHA256
        and life["terminal"]["wait_status_raw"] == 0
        and life["startup_parent_fds_closed"] is True
        and not life.get("cleanup_gap"),
        "retained bootstrap/normal/ownership evidence incomplete",
    )
    require(
        prior["exposed_domain"] == grant["resource_domain"]["expected_exposed"],
        "retained Q1 domain no longer corresponds",
    )
    return {
        "scope": (
            "unchanged method/bootstrap/old normal fixture/lock only; no full new-driver success"
        ),
        "receipt_sha256": evidence["receipt_sha256"],
        "lifecycle_sha256": evidence["lifecycle_sha256"],
        "unchanged_source_sha256": {key: current[key] for key in RETAINED_METHOD_KEYS},
        "prior_driver_sha256": prior["source_sha256"][
            "docs/reports/reconstruction-working-set/method_qualification.py"
        ],
        "new_driver_sha256": current[
            "docs/reports/reconstruction-working-set/method_qualification.py"
        ],
        "prior_inventory_sha256": prior["source_sha256"][
            "docs/reports/reconstruction-working-set/qualification/inventory.json"
        ],
        "new_inventory_sha256": current[
            "docs/reports/reconstruction-working-set/qualification/inventory.json"
        ],
        "new_fixture_sha256": current[
            "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt"
        ],
    }


def retained_q2(current, obs):
    """Retain the four exact Q2 results only for their unchanged method inputs."""
    rows = []
    keys = (
        *RETAINED_METHOD_KEYS,
        "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt",
    )
    for attempt, receipt_sha, lifecycle_sha, expected_signal in Q2_EVIDENCE:
        directory = QUAL / "attempts" / attempt
        require(
            obs.digest(directory / "receipt.json") == receipt_sha
            and obs.digest(directory / "small-lifecycle.json") == lifecycle_sha,
            "exact retained Q2 evidence changed",
        )
        prior = json.loads((directory / "receipt.json").read_text())
        life = json.loads((directory / "small-lifecycle.json").read_text())
        require(
            prior["status"] == PASS
            and prior["attempt_id"] == attempt
            and all(prior["source_sha256"][key] == current[key] for key in keys),
            "retained Q2 outcome/input mapping differs",
        )
        require(
            life["terminal"]["term_signal"] == expected_signal
            and life["startup_parent_fds_closed"] is True
            and life["wait_ownership_lost"] is False
            and life["error"] is None
            and not life.get("cleanup_gap"),
            "retained Q2 ownership evidence incomplete",
        )
        rows.append(
            {
                "attempt_id": attempt,
                "receipt_sha256": receipt_sha,
                "lifecycle_sha256": lifecycle_sha,
                "prior_driver_sha256": prior["source_sha256"][
                    "docs/reports/reconstruction-working-set/method_qualification.py"
                ],
            }
        )
    return {
        "scope": "four exact Q2 results for unchanged method/bootstrap/fixtures/lock only; "
        "no relabelled new-driver pass",
        "evidence": rows,
        "unchanged_source_sha256": {key: current[key] for key in keys},
        "current_driver_sha256": current[
            "docs/reports/reconstruction-working-set/method_qualification.py"
        ],
        "current_inventory_sha256": current[
            "docs/reports/reconstruction-working-set/qualification/inventory.json"
        ],
    }


def local_safety(grant, obs):
    """Apply released current-process and exposed-domain stops between tiny vectors."""
    sample = obs.process_sample(os.getpid())
    require(
        type(sample.get("VmRSS_bytes")) is int
        and sample["VmRSS_bytes"] < grant["process_stop_bytes"]
        and sample["host_available_bytes"] is not None
        and sample["host_available_bytes"] > grant["host_min_available_bytes"],
        "qualification current-process/host stop",
    )
    require(
        all(
            (value := obs.read(Path(path) / "memory.current")) is not None and int(value) < stop
            for path, stop in grant["ancestor_stop_bytes"].items()
        ),
        "qualification exposed-domain stop",
    )


def parser_case(out, grant, bounds, obs, method):
    """Observe accepted Q4 interfaces on the exact finite scalar fixture inventory."""
    fixture = QUAL / "fixtures/parser-vectors-v1.json"
    require(fixture.stat().st_size <= bounds["fixture_bytes"], "Q4 fixture exceeds bound")
    data = json.loads(fixture.read_text())
    vectors = data["vectors"]
    require(
        len(vectors) == bounds["vector_count"]
        and len({row["id"] for row in vectors}) == len(vectors),
        "Q4 vector inventory differs",
    )
    directory = out / "vectors"
    directory.mkdir()
    started = time.monotonic()
    total_bytes = 0
    completed = 0
    with (out / "parser-results.jsonl").open("x") as results:
        for vector in vectors:
            require(time.monotonic() - started < bounds["wall_seconds"], "Q4 soft deadline")
            local_safety(grant, obs)
            row = {
                "id": vector["id"],
                "interface": vector["interface"],
                "expected": vector["expected"],
                "synthetic_not_measurement": True,
            }
            path = directory / (vector["id"] + ".json")
            if vector["interface"] == "child_outcome":
                record = json.loads(json.dumps(data["base_record"]))
                profile = vector.get("profile_stream")
                if profile is not None:
                    stream = data["profile_streams"][profile]
                    record["spec"]["shape"][0] = stream["times"]
                    record["spec"]["profile"] = True
                    record["branches"] = [["known"] for _ in range(stream["times"])]
                    record["stages"] = json.loads(json.dumps(stream["events"]))
                expected_spec = json.loads(json.dumps(record["spec"]))
                for change in vector.get("changes", []):
                    parent = record
                    for component in change["path"][:-1]:
                        parent = parent[component]
                    key = change["path"][-1]
                    if change["op"] == "delete":
                        del parent[key]
                    else:
                        require(change["op"] == "set", "unknown Q4 fixture operation")
                        parent[key] = change["value"]
                if "direct_expected" in vector:
                    direct = "accepted"
                    try:
                        method.validate_complete_record(
                            record, data["synthetic_pid"], expected_spec
                        )
                    except ValueError as error:
                        direct = "refused"
                        row["direct_diagnostic"] = str(error)
                    row["direct_observed"] = direct
                    row["direct_expectation_matches"] = direct == vector["direct_expected"]
                mode = vector.get("file_mode", "record")
                if mode == "record":
                    payload = json.dumps(record, allow_nan=False).encode()
                elif mode == "missing":
                    payload = None
                elif mode == "oversized":
                    payload = b"x" * (bounds["record_bytes"] + 1)
                else:
                    payload = {
                        "empty": b"",
                        "truncated": b'{"protocol":',
                        "invalid_utf8": b"\xff",
                        "array_object": b"[]",
                    }[mode]
                require(
                    payload is None
                    or len(payload) <= bounds["record_bytes"] + (1 if mode == "oversized" else 0),
                    "Q4 emitted record exceeds bound",
                )
                if payload is not None:
                    path.write_bytes(payload)
                    total_bytes += len(payload)
                observed, diagnostic = method.child_outcome(
                    path, bounds["record_bytes"], data["synthetic_pid"], expected_spec
                )
                row.update(
                    observed=observed,
                    protocol_refusal=observed
                    in {
                        "missing_child_record",
                        "malformed_child_record",
                        "child_record_exceeds_admitted_parse_bound",
                    },
                )
                if observed == "malformed_child_record":
                    row["parse_diagnostic"] = diagnostic
            elif vector["interface"] == "bootstrap_failure":
                payload = vector["text"].encode()
                require(len(payload) <= bounds["bootstrap_fixture_bytes"], "Q4 bootstrap bound")
                path.write_bytes(payload)
                total_bytes += len(payload)
                value = obs.bootstrap_failure(path)
                row["observed"] = value.get("stage") if value is not None else None
            else:
                require(vector["interface"] == "legal_numeric_dtype", "unknown Q4 interface")
                row["observed"] = obs.legal_numeric_dtype(
                    vector["dtype"], canonical=vector["canonical"]
                )
            require(total_bytes <= bounds["total_fixture_output_bytes"], "Q4 total file bound")
            row["expectation_matches"] = row["observed"] == row["expected"] and row.get(
                "direct_expectation_matches", True
            )
            results.write(json.dumps(row) + "\n")
            results.flush()
            require(
                row["expectation_matches"], "Q4 qualification expectation failed: " + vector["id"]
            )
            completed += 1
    return {
        "results_file": "parser-results.jsonl",
        "vectors_completed": completed,
        "fixture_output_bytes": total_bytes,
        "spawned_children": 0,
        "scope": "finite synthetic parser expectations only; protocol refusal may be expected; "
        "no science, native wait-status classifier or full main status ladder executed",
    }


def retained_q4(current, obs):
    """Keep the one exact Q4 result only for unchanged method and scalar fixtures."""
    directory = QUAL / "attempts/q4-parser-a1"
    receipt_sha = "9e58d30b4cdfa97249fb3ed17fe15757d03477c52473933c9bd9dc76b1a1d7aa"
    rows_sha = "b4075111d60219184356bc235e7f81d0a6ccbb8c4ac1b4d9e5ffe243d0a4228a"
    require(
        obs.digest(directory / "receipt.json") == receipt_sha
        and obs.digest(directory / "parser-results.jsonl") == rows_sha,
        "retained exact Q4 evidence changed",
    )
    prior = json.loads((directory / "receipt.json").read_text())
    keys = (
        *RETAINED_METHOD_KEYS,
        "docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt",
        "docs/reports/reconstruction-working-set/qualification/fixtures/parser-vectors-v1.json",
    )
    require(
        prior["status"] == PASS
        and prior["case"] == Q4_CASE
        and prior["attempt_id"] == "q4-parser-a1"
        and prior["result"]["vectors_completed"] == 151
        and all(prior["source_sha256"][key] == current[key] for key in keys),
        "retained Q4 outcome/unchanged-input mapping differs",
    )
    return {
        "receipt_sha256": receipt_sha,
        "rows_sha256": rows_sha,
        "scope": "exact Q4 parser result only for unchanged methods/fixtures/lock; "
        "new driver/inventory/Q5/helper inputs are independently bound, not prior passes",
        "unchanged_source_sha256": {key: current[key] for key in keys},
        "prior_driver_sha256": prior["source_sha256"][
            "docs/reports/reconstruction-working-set/method_qualification.py"
        ],
        "current_driver_sha256": current[
            "docs/reports/reconstruction-working-set/method_qualification.py"
        ],
    }


def tiny_hash_vector(vector, chunks, bounds, obs, np, fixture, public_hash, diagnostic_path):
    """Release all tiny arrays at return; retain only scalar identities and observations."""
    raw = bytes.fromhex(vector["backing_hex"])
    canonical = bytes.fromhex(vector["expected_canonical_hex"])
    require(
        len(raw) <= bounds["max_backing_bytes"] and len(canonical) <= bounds["max_array_bytes"],
        "Q5 literal byte allocation bound",
    )
    backing = np.frombuffer(raw, dtype=vector["dtype"]).reshape(vector["backing_shape"])
    mode = vector["mode"]
    if mode == "fortran":
        value = np.array(backing, order="F", copy=True)
    elif mode == "positive_stride":
        value = backing[::2]
    elif mode == "negative_stride":
        value = backing[::-1]
    elif mode == "numpy_scalar":
        value = backing[()]
    else:
        require(mode == "direct", "unknown Q5 finite fixture mode")
        value = backing
    array = np.asarray(value)
    require(
        array.size <= bounds["max_elements"]
        and array.nbytes <= bounds["max_array_bytes"]
        and tuple(array.shape) == tuple(vector["expected_shape"]),
        "Q5 shape/element/byte bound",
    )
    if "expected_c_contiguous" in vector:
        require(
            bool(array.flags.c_contiguous) == vector["expected_c_contiguous"]
            and bool(array.flags.f_contiguous) == vector["expected_f_contiguous"],
            "Q5 intended F-only layout missing",
        )
    if "expected_stride_sign" in vector:
        require(
            (1 if array.strides[0] > 0 else -1) == vector["expected_stride_sign"]
            and abs(array.strides[0]) > 0,
            "Q5 intended stride missing",
        )
        if mode == "positive_stride":
            require(array.strides[0] > array.dtype.itemsize, "positive stride is not spaced")
    expected = (
        vector["name"],
        tuple(vector["expected_shape"]),
        vector["expected_dtype"],
        hashlib.sha256(canonical).hexdigest(),
    )
    frozen = fixture.identity(value, vector["name"])
    diagnostic = {
        "id": vector["id"],
        "expected_identity": expected,
        "frozen_identity": frozen,
        "expected_finite": vector["expected_finite"],
        "observations": [],
    }

    def save():
        encoded = json.dumps(diagnostic) + "\n"
        require(len(encoded.encode()) <= bounds["result_row_bytes"], "Q5 diagnostic row bound")
        diagnostic_path.write_text(encoded)

    save()
    require(frozen == expected, "frozen RM84 identity differs from literal canonical bytes")
    observations = diagnostic["observations"]
    for chunk_bytes in chunks:
        require(16 <= chunk_bytes <= bounds["max_chunk_bytes"], "Q5 chunk control outside bound")
        observed = obs.array_identity(value, vector["name"], chunk_bytes=chunk_bytes)
        finite = obs.bounded_finite(value, chunk_bytes=chunk_bytes)
        observations.append(
            {"chunk_bytes": chunk_bytes, "observed_identity": observed, "observed_finite": finite}
        )
        save()
        require(
            observed == expected and observed == frozen and finite is vector["expected_finite"],
            "Q5 identity/finite expectation mismatch",
        )
    golden = np.frombuffer(canonical, dtype=vector["expected_dtype"]).reshape(
        vector["expected_shape"]
    )
    golden_value = golden[()] if mode == "numpy_scalar" else golden
    actual_public, expected_public = public_hash(value), public_hash(golden_value)
    diagnostic.update(
        public_value_sha256=actual_public, literal_reference_public_sha256=expected_public
    )
    save()
    require(
        actual_public == expected_public, "frozen public-value canonical/layout comparison differs"
    )
    return {
        "id": vector["id"],
        "expected_identity": expected,
        "frozen_identity": frozen,
        "observations": observations,
        "expected_finite": vector["expected_finite"],
        "public_value_sha256": actual_public,
        "literal_reference_public_sha256": expected_public,
        "shape": list(array.shape),
        "dtype": array.dtype.str,
        "strides": list(array.strides),
        "c_contiguous": bool(array.flags.c_contiguous),
        "f_contiguous": bool(array.flags.f_contiguous),
        "elements": int(array.size),
        "array_bytes": int(array.nbytes),
        "source_backing_bytes": len(raw),
        "canonical_reference_bytes": len(canonical),
        "expectation_matches": True,
    }


def tiny_hash_case(out, grant, bounds, obs):
    """Use only NumPy and two pinned frozen RM84 helpers on 33 tiny declared vectors."""
    import numpy as np

    sys.path.insert(0, str(ROOT / "tests"))
    import reconstruction_memory_benchmark as benchmark
    import reconstruction_summary_fixture as fixture

    no_product()
    require(
        not any(name == "scipy" or name.startswith("scipy.") for name in sys.modules),
        "Q5 SciPy import forbidden",
    )
    require(
        np.__version__ == "2.5.3"
        and Path(fixture.__file__).resolve() == ROOT / "tests/reconstruction_summary_fixture.py"
        and Path(benchmark.__file__).resolve() == ROOT / "tests/reconstruction_memory_benchmark.py",
        "Q5 NumPy/frozen-helper resolution differs",
    )
    path = QUAL / "fixtures/tiny-hash-vectors-v1.json"
    require(path.stat().st_size <= bounds["fixture_bytes"], "Q5 fixture exceeds bound")
    data = json.loads(path.read_text())
    require(
        len(data["vectors"]) == bounds["vector_count"]
        and len(data["public_relations"]) == bounds["public_relation_count"]
        and data["chunk_bytes"] == bounds["chunk_bytes"],
        "Q5 finite inventory differs",
    )
    public_hashes = {}
    started = time.monotonic()
    directory = out / "tiny-vectors"
    directory.mkdir()
    with (out / "tiny-hash-results.jsonl").open("x") as results:
        for vector in data["vectors"]:
            require(time.monotonic() - started < bounds["wall_seconds"], "Q5 soft deadline")
            local_safety(grant, obs)
            row = tiny_hash_vector(
                vector,
                data["chunk_bytes"],
                bounds,
                obs,
                np,
                fixture,
                benchmark.public_value_sha256,
                directory / (vector["id"] + ".json"),
            )
            public_hashes[vector["id"]] = row["public_value_sha256"]
            encoded = json.dumps(row) + "\n"
            require(len(encoded.encode()) <= bounds["result_row_bytes"], "Q5 result row bound")
            results.write(encoded)
            results.flush()
            require(results.tell() <= bounds["results_file_bytes"], "Q5 result file bound")
    relations = []
    for relation in data["public_relations"]:
        observed = public_hashes[relation["left"]] == public_hashes[relation["right"]]
        row = {
            **relation,
            "observed_public_hash_equal": observed,
            "expectation_matches": observed is relation["public_hash_equal"],
        }
        relations.append(row)
        write(out / "public-relations.json", relations)
        require(row["expectation_matches"], "Q5 public fingerprint relation differs")
    no_product()
    require(
        not any(name == "scipy" or name.startswith("scipy.") for name in sys.modules),
        "Q5 scientific import scope expanded",
    )
    return {
        "results_file": "tiny-hash-results.jsonl",
        "vectors_completed": len(public_hashes),
        "public_relations_completed": len(relations),
        "chunks": data["chunk_bytes"],
        "numpy": np.__version__,
        "workload_children": 0,
        "administrative_subprocess": "existing admission git rev-parse only, no numerical child",
        "scope": "tiny canonical/value/finite semantics only; reference copies disclosed, "
        "no workflow/reference pair, peak benefit or exec-transition retention proof",
    }


def method6_prior_scope(grant, current, obs):
    """Retain only named unchanged function/input scopes, never whole old receipts."""
    old_path = Path(grant["legacy_runner_source"]["path"])
    require(
        old_path
        == Path("/workspace/work/campaign/evidence/116/source-before-method6/run_attempt.py")
        and grant["legacy_runner_source"]["sha256"]
        == "1e554fdadffdfc54cbc14758e072224db5cd278f1e7b7e91b813c11c65b5fd61"
        and obs.digest(old_path) == grant["legacy_runner_source"]["sha256"],
        "preserved method5 runner source differs",
    )
    functions = ("WaitOwner", "cleanup", "child_outcome", "validate_complete_record")
    texts = []
    for path in (old_path, HERE / "run_attempt.py"):
        require(path.stat().st_size <= 131072, "method6 retained source parse bound")
        source = path.read_text()
        nodes = ast.parse(source).body
        texts.append(
            {
                node.name: ast.get_source_segment(source, node)
                for node in nodes
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in functions
            }
        )
    require(
        set(texts[0]) == set(functions) and texts[0] == texts[1],
        "named retained function bytes changed; stop applicability reuse",
    )
    evidence = [
        ("q1-method5-a1", "23534b9f0298fd2de621a6e2b8b0b7bb993d9ce094d3d716aefdd5b29d7016ce"),
        *((attempt, receipt_sha) for attempt, receipt_sha, _, _ in Q2_EVIDENCE),
        ("q4-parser-a1", "9e58d30b4cdfa97249fb3ed17fe15757d03477c52473933c9bd9dc76b1a1d7aa"),
        ("q5-tinyhash-a1", "164ecf085b44b51bbc26a01fba523ab7e1ca388e2d8074e94fdf19297e7bcb3d"),
    ]
    unchanged_keys = tuple(
        key
        for key in current
        if key
        not in {
            "docs/reports/reconstruction-working-set/run_attempt.py",
            "docs/reports/reconstruction-working-set/method_qualification.py",
            "docs/reports/reconstruction-working-set/qualification/inventory.json",
            "docs/reports/reconstruction-working-set/qualification/fixtures/method6-rss-controls-v1.json",
        }
    )
    rows = []
    for attempt, receipt_sha in evidence:
        path = QUAL / "attempts" / attempt / "receipt.json"
        require(obs.digest(path) == receipt_sha, "historical qualified receipt changed")
        prior = json.loads(path.read_text())
        require(
            prior["status"] == PASS and prior["attempt_id"] == attempt,
            "historical scoped result differs",
        )
        keys = [key for key in unchanged_keys if key in prior["source_sha256"]]
        require(
            all(prior["source_sha256"][key] == current[key] for key in keys),
            "historical unchanged input subset differs",
        )
        rows.append(
            {
                "attempt_id": attempt,
                "receipt_sha256": receipt_sha,
                "full_source_receipt_reuse": False,
                "unchanged_input_sha256": {key: current[key] for key in keys},
            }
        )
    return {
        "scope": "Q1/Q2 WaitOwner+cleanup/fixed observer launch only; Q4 unchanged parser/"
        "observer dtype/bootstrap helpers only; Q5 observer array/finite and frozen "
        "value protocols only. New monitor, main integration and extracted final status "
        "have no prior full-source pass.",
        "unchanged_runner_function_sha256": {
            name: hashlib.sha256(texts[1][name].encode()).hexdigest() for name in functions
        },
        "evidence": rows,
    }


class Method6ControlOwner:
    """Finite fake collection source; no wait, signal, child or native usage exists."""

    def __init__(self, terminal_kind):
        self.terminal_kind = terminal_kind
        self.action = "none"
        self.terminal = None
        self.wait_lost = False
        self.nonterminal_wait_events = []
        self.collect_calls = 0
        self.collected_at_ns = 0

    def collect(self):
        """Supply one declared fake event, caching a declared terminal like the real owner."""
        self.collect_calls += 1
        if self.terminal is not None:
            return self.terminal
        if self.action == "wait_loss":
            self.wait_lost = True
            raise RuntimeError("synthetic exact-owner wait loss")
        if self.action == "interrupt":
            raise KeyboardInterrupt("synthetic collection interrupt")
        if self.action == "nonterminal":
            self.nonterminal_wait_events.append({"synthetic_notification": True})
        if self.action == "terminal":
            kind = self.terminal_kind
            self.terminal = {
                "pid": 7141,
                "reaped_monotonic_ns": self.collected_at_ns,
                "returncode": -9 if kind == "signal" else 3 if kind == "nonzero" else 0,
                "signaled": kind == "signal",
                "synthetic_not_native": True,
            }
        return self.terminal


def method6_controls(out, grant, bounds, obs, method):
    """Exercise the actual new decision and final-status helpers with finite synthetic inputs."""
    path = QUAL / "fixtures/method6-rss-controls-v1.json"
    require(path.stat().st_size <= bounds["fixture_bytes"], "method6 fixture bound")
    data = json.loads(path.read_text())
    require(
        len(data["vectors"]) == bounds["vector_count"]
        and len({row["id"] for row in data["vectors"]}) == bounds["vector_count"],
        "method6 exact vector inventory differs",
    )
    parser_path = QUAL / "fixtures/parser-vectors-v1.json"
    require(
        parser_path.stat().st_size <= bounds["parser_fixture_bytes"], "old parser fixture bound"
    )
    parser_fixture = json.loads(parser_path.read_text())
    directory = out / "method6-vectors"
    directory.mkdir()
    started = time.monotonic()
    with (out / "method6-results.jsonl").open("x") as results:
        for vector in data["vectors"]:
            require(
                time.monotonic() - started < bounds["wall_seconds"], "method6 control soft deadline"
            )
            owner = Method6ControlOwner(vector.get("terminal_kind", "normal"))
            receipt = {}
            exception = None
            row = {
                "id": vector["id"],
                "expected": vector["expected"],
                "steps": [],
                "synthetic_not_process_or_native_observation": True,
            }
            diagnostic_path = directory / (vector["id"] + ".json")
            require(len(vector["steps"]) <= bounds["steps_per_vector"], "method6 step bound")
            for step in vector["steps"]:
                sample = json.loads(json.dumps(data["base_sample"]))
                sample.update(step.get("sample", {}))
                if step.get("remove_RSS"):
                    del sample["VmRSS_bytes"]
                if step.get("remove_sample_timestamp"):
                    del sample["monotonic_ns"]
                owner.action = step["owner"]
                owner.collected_at_ns = step.get("terminal_monotonic_ns", 0)
                ticks = iter((step["before"], step["after"]))
                stop = None
                try:
                    stop = method.monitor_sample_decision(
                        owner,
                        sample,
                        data["synthetic_grant"],
                        receipt,
                        deadline=vector.get("deadline", 1.0),
                        startup_deadline=vector.get("startup_deadline", 0.5),
                        ready=vector.get("ready", True),
                        parent_cgroup="0::/",
                        clock=lambda ticks=ticks: next(ticks),
                    )
                except (RuntimeError, KeyboardInterrupt) as error:
                    exception = type(error).__name__
                row["steps"].append(
                    {
                        "before": step["before"],
                        "after": step["after"],
                        "sample": sample,
                        "returned_stop": stop,
                        "exception": exception,
                        "receipt": json.loads(json.dumps(receipt)),
                    }
                )
                encoded = json.dumps(row) + "\n"
                require(
                    len(encoded.encode()) <= bounds["diagnostic_bytes"], "method6 diagnostic bound"
                )
                diagnostic_path.write_text(encoded)
                if exception is not None:
                    break
            outcome, parsed = None, None
            status = None
            readiness_failed = False
            if "readiness" in vector and exception is None:
                event = vector["readiness"]
                try:
                    method.observe_session_readiness(
                        receipt,
                        event["value"],
                        event["deadline"],
                        clock=lambda event=event: event["observed"],
                    )
                except method.StartupError as error:
                    exception = type(error).__name__
                    readiness_failed = True
                    status = method.observer_exception_status(receipt, error)
            if owner.terminal is not None:
                record = json.loads(json.dumps(parser_fixture["base_record"]))
                spec = json.loads(json.dumps(record["spec"]))
                child = vector.get("child", "finite")
                child_path = directory / (vector["id"] + "-child.json")
                if child == "malformed":
                    child_path.write_text("{")
                elif child == "oversized":
                    child_path.write_bytes(b"x" * (bounds["record_bytes"] + 1))
                elif child != "missing":
                    if child != "finite":
                        record["status"] = child
                    encoded = json.dumps(record)
                    require(
                        len(encoded.encode()) <= bounds["record_bytes"],
                        "method6 child record bound",
                    )
                    child_path.write_text(encoded)
                outcome, parsed = method.child_outcome(
                    child_path, bounds["record_bytes"], 7141, spec
                )
                boot_error = None
                if "bootstrap_stage" in vector:
                    boot_path = directory / (vector["id"] + "-bootstrap.txt")
                    boot_path.write_text(
                        "WS116_BOOTSTRAP_ERROR " + json.dumps({"stage": vector["bootstrap_stage"]})
                    )
                    boot_error = obs.bootstrap_failure(boot_path)
                if not readiness_failed:
                    status = method.observed_child_status(
                        receipt,
                        owner.terminal,
                        outcome,
                        vector.get("identity_matches", True),
                        boot_error,
                    )
            observed = {
                "gap_outcome": receipt.get("rss_terminal_confirmation", {}).get("outcome"),
                "stop_reason": receipt.get("stop_reason"),
                "exception": exception,
                "terminal_present": owner.terminal is not None,
                "status": status,
                "wait_ownership_lost": owner.wait_lost,
                "nonterminal_notifications": len(owner.nonterminal_wait_events),
                "gap_origin_monotonic_ns": receipt.get("rss_terminal_confirmation", {}).get(
                    "origin_monotonic_ns"
                ),
                "gap_deadline_monotonic_ns": receipt.get("rss_terminal_confirmation", {}).get(
                    "deadline_monotonic_ns"
                ),
                "late_readiness": receipt.get("late_session_readiness"),
            }
            row.update(
                observed=observed,
                child_outcome=outcome,
                parse_diagnostic=parsed if outcome == "malformed_child_record" else None,
                collect_calls=owner.collect_calls,
                native_wait_calls=0,
                signals_sent=0,
                expectation_matches=observed == vector["expected"],
            )
            encoded = json.dumps(row) + "\n"
            require(
                len(encoded.encode()) <= bounds["diagnostic_bytes"],
                "method6 final diagnostic bound",
            )
            diagnostic_path.write_text(encoded)
            results.write(encoded)
            results.flush()
            require(results.tell() <= bounds["results_file_bytes"], "method6 results file bound")
            require(
                row["expectation_matches"],
                "method6 qualification expectation differs: " + vector["id"],
            )
    return {
        "results_file": "method6-results.jsonl",
        "vectors_completed": len(data["vectors"]),
        "confirmation_seconds": method.RSS_TERMINAL_CONFIRM_SECONDS,
        "workload_children": 0,
        "scope": "deterministic fake owner/clock/sample + actual decision/status/parser only; "
        "no live exit-race reproduction, kernel wait4/TERM proof or scientific result",
    }


def pure_method6(args):
    """Run only file-bound fake controls; no generic admission or live OS observations."""
    import resource
    import subprocess

    blocked = []

    def deny(*_args, **_kwargs):
        blocked.append("forbidden process/signal/wait/resource API")
        raise RuntimeError(blocked[-1])

    def audit(event, arguments):
        forbidden = event in {
            "os.fork",
            "os.forkpty",
            "os.posix_spawn",
            "os.system",
            "os.exec",
            "os.kill",
            "os.killpg",
            "subprocess.Popen",
            "signal.pthread_kill",
            "signal.raise_signal",
        }
        if event == "import":
            forbidden = arguments[0].split(".", 1)[0] in {"numpy", "scipy", "simrecon", "ctypes"}
        if event == "open" and isinstance(arguments[0], (str, bytes)):
            name = os.fsdecode(arguments[0])
            forbidden = name.startswith(("/proc/", "/sys/"))
        if forbidden:
            blocked.append("forbidden audited effect: " + event)
            raise RuntimeError(blocked[-1])

    sys.addaudithook(audit)
    # Wait functions have no guaranteed audit event. Deny the concrete APIs in
    # this dedicated process as well; do not restore them and run another case.
    for name in (
        "fork",
        "forkpty",
        "posix_spawn",
        "posix_spawnp",
        "system",
        "kill",
        "killpg",
        "wait",
        "waitpid",
        "wait3",
        "wait4",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
    ):
        if hasattr(os, name):
            setattr(os, name, deny)
    for name in ("signal", "raise_signal", "pthread_kill", "alarm", "setitimer"):
        if hasattr(signal, name):
            setattr(signal, name, deny)
    for name in ("getrusage", "getrlimit", "setrlimit", "prlimit"):
        if hasattr(resource, name):
            setattr(resource, name, deny)
    subprocess.Popen = deny
    if hasattr(subprocess, "_fork_exec"):
        subprocess._fork_exec = deny

    out = QUAL / "attempts" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    receipt = {
        "protocol": "WS116-method6-pure-controls-v1",
        "case": args.case,
        "attempt_id": args.attempt_id,
        "status": "qualification_failed",
        "driver_pid": os.getpid(),
        "argv": sys.argv,
        "started_monotonic_ns": time.monotonic_ns(),
        "physical_resource_admission": "not performed or claimed",
        "not_scientific_evidence": True,
    }
    try:
        require(
            sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            "pure method6 command requires -I -S -B",
        )
        require(
            not any(
                name.split(".", 1)[0] in {"numpy", "scipy", "simrecon", "ctypes"}
                for name in sys.modules
            ),
            "forbidden module already loaded",
        )
        with args.grant.open("rb") as stream:
            payload = stream.read(65537)
        require(len(payload) <= 65536, "pure grant file exceeds64KiB")
        (out / "grant.input").write_bytes(payload)
        grant = json.loads(payload)
        require(
            grant["approved"] is True
            and grant["pure_stdlib_controls_only"] is True
            and grant["numerical_release"] is False
            and grant["scope"] == receipt["protocol"]
            and grant["case"] == M6_CASE
            and grant["attempt_id"] == args.attempt_id,
            "no exact pure-stdlib control release",
        )
        require(
            str(Path(sys.executable).resolve()) == grant["python_resolved"],
            "pure control interpreter differs from pinned source grant",
        )

        def file_digest(path):
            with Path(path).open("rb") as stream:
                return hashlib.file_digest(stream, "sha256").hexdigest()

        require(
            len(grant["source_sha256"]) == 14
            and {
                "docs/reports/reconstruction-working-set/observer.py",
                "docs/reports/reconstruction-working-set/run_attempt.py",
                "docs/reports/reconstruction-working-set/method_qualification.py",
                "docs/reports/reconstruction-working-set/qualification/inventory.json",
            }
            <= set(grant["source_sha256"]),
            "pure fourteen-input map incomplete",
        )
        for name, digest in grant["source_sha256"].items():
            path = (ROOT / name).resolve()
            require(
                path.is_relative_to(ROOT) and file_digest(path) == digest,
                "pure source input identity differs: " + name,
            )
        require(
            "observer" not in sys.modules and "run_attempt" not in sys.modules,
            "report module unexpectedly preloaded",
        )
        sys.path.insert(0, str(HERE))
        import observer as obs
        import run_attempt as method

        require(
            Path(obs.__file__).resolve() == HERE / "observer.py"
            and Path(method.__file__).resolve() == HERE / "run_attempt.py",
            "pure report imports resolve outside frozen files",
        )
        # Fail immediately if a future edit reaches a generic live-observation
        # helper. All effect attempts remain fatal even if a negative control
        # happens to catch their RuntimeError.
        for module in (obs, method):
            for name in ("context", "process_sample", "cgroup_ancestors", "mem_available"):
                if hasattr(module, name):
                    setattr(module, name, deny)
        method.git = deny
        obs.rusage_snapshot = deny
        identities = source_identities(grant, obs)
        inventory_path = QUAL / "inventory.json"
        require(inventory_path.stat().st_size <= 32768, "pure inventory exceeds32KiB")
        inventory = json.loads(inventory_path.read_text())
        bounds = inventory["method6_bounds"]
        require(
            grant["phase_bounds"] == bounds
            and bounds["confirmation_seconds"] == method.RSS_TERMINAL_CONFIRM_SECONDS
            and identities[
                "docs/reports/reconstruction-working-set/qualification/fixtures/method6-rss-controls-v1.json"
            ]
            == inventory["method6_fixture_sha256"],
            "pure finite bound/fixture mismatch",
        )
        receipt.update(
            source_sha256=identities,
            grant_sha256=file_digest(out / "grant.input"),
            interpreter=str(Path(sys.executable).resolve()),
            isolation_flags={
                "isolated": sys.flags.isolated,
                "no_site": sys.flags.no_site,
                "dont_write_bytecode": sys.dont_write_bytecode,
            },
        )
        write(
            out / "prior-function-applicability.json", method6_prior_scope(grant, identities, obs)
        )
        started = time.monotonic()
        result = method6_controls(out, grant, bounds, obs, method)
        require(time.monotonic() - started < bounds["wall_seconds"], "pure controls soft deadline")
        require(
            source_identities(grant, obs) == identities and not blocked,
            "pure control source/effect condition changed",
        )
        require(
            not any(
                name.split(".", 1)[0] in {"numpy", "scipy", "simrecon", "ctypes"}
                for name in sys.modules
            ),
            "pure import scope expanded",
        )
        receipt.update(result=result, status=PASS)
    except BaseException as error:
        receipt.update(error_type=type(error).__name__, error_message=str(error))
    finally:
        receipt.update(
            finished_monotonic_ns=time.monotonic_ns(),
            blocked_effects=blocked,
            limits="Pure synthetic semantics only; no process/native/resource/science "
            "qualification. In-process denial is not an OS security sandbox. "
            "Fresh affected method6 review + new clean basis/root window/per-case "
            "release still required before any workflow retry.",
        )
        if blocked:
            receipt["status"] = "qualification_failed"
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == PASS else 1


def context_case(out, obs):
    """Observe actual pinned environment/backend facts without a numerical operation."""
    import numpy as np
    import scipy
    import scipy.fft

    no_product()
    facts = {
        "python": sys.version,
        "executable": sys.executable,
        "resolved_executable": str(Path(sys.executable).resolve()),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "numpy_backend": np.__config__.CONFIG,
        "scipy_fft_default_workers": scipy.fft.get_workers(),
        "context": obs.context(ROOT),
        "scientific_operations": "none",
        "effective_worker_limits": "unknown beyond requested controls/default FFT setting",
    }
    write(out / "environment.json", facts)
    return {
        "environment_file": "environment.json",
        "scope": "environment facts only, no workload result",
    }


def normal_case(out, grant, bounds, obs, method):
    """Qualify the integrated fixed bootstrap using one tiny stdlib-only target."""
    require(
        sys.platform == "linux" and hasattr(os, "posix_spawn") and hasattr(os, "wait4"),
        "Linux spawn/wait4 route unavailable",
    )
    fixture = QUAL / "fixtures/stdlib-child.txt"
    argv = [sys.executable, "-c", fixture.read_text(), "normal"]
    record = {
        "argv": argv,
        "body_sha256": obs.digest(fixture),
        "signals": [],
        "scope": "tiny direct stdlib child; not a scientific memory envelope",
    }
    owner = None
    launch = None
    started = time.monotonic()
    deadline = started + bounds["life_deadline_seconds"]
    term_at = None
    kill_at = None
    write(
        out / "spawn-intent.json",
        {
            "observer": obs.process_identity(os.getpid()),
            "argv": argv,
            "body_sha256": record["body_sha256"],
            "intent_only": True,
        },
    )
    try:
        with (
            (out / "stdout.json").open("x") as stdout,
            (out / "stderr.log").open("x") as stderr,
            (out / "samples.jsonl").open("x") as samples,
        ):
            launch = obs.FixedSessionLaunch(
                argv,
                os.environ.copy(),
                grant["launch_nonce"],
                stdout.fileno(),
                stderr.fileno(),
                bounds["startup_pipe_bytes"],
            )
            record.update(
                bootstrap_sha256=obs.SESSION_BOOTSTRAP_SHA256,
                bootstrap_argv=launch.argv,
                file_actions=launch.actions,
                fd_plan=launch.fd_plan,
            )
            write(out / "fixed-route-intent.json", record)
            pid = launch.spawn()
            owner = method.WaitOwner(pid)
            launch.release_parent_writers()
            record["workload_pid"] = pid
            write(
                out / "owned-child.json",
                {"workload": obs.process_identity(pid), "observer_pid": os.getpid(), "argv": argv},
            )
            while True:
                terminal = owner.collect()
                ready = launch.drain()
                if ready is not None and "session_ready" not in record:
                    require(
                        time.monotonic() < started + bounds["startup_timeout_seconds"],
                        "integrated readiness arrived late",
                    )
                    record["session_ready"] = ready
                    write(out / "session-ready.json", ready)
                if terminal is not None:
                    require(ready is not None, "terminal exit without integrated readiness")
                    break
                now = time.monotonic()
                sample = obs.process_sample(pid)
                sample["ancestor_current_bytes"] = {
                    path: obs.read(Path(path) / "memory.current")
                    for path in grant["ancestor_stop_bytes"]
                }
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                if owner.collect() is not None:
                    continue
                rss = sample.get("VmRSS_bytes")
                require(type(rss) is int and rss >= 0, "required live-child RSS observation lost")
                require(rss < grant["process_stop_bytes"], "qualification process RSS stop")
                require(
                    sample["host_available_bytes"] is not None
                    and sample["host_available_bytes"] > grant["host_min_available_bytes"],
                    "qualification host stop",
                )
                require(
                    all(
                        value is not None and int(value) < grant["ancestor_stop_bytes"][path]
                        for path, value in sample["ancestor_current_bytes"].items()
                    ),
                    "qualification ancestor stop",
                )
                if now >= deadline and term_at is None:
                    record["stop_reason"] = "normal-case timeout"
                    record["signals"].append(owner.send(signal.SIGTERM))
                    term_at = now
                if (
                    term_at is not None
                    and kill_at is None
                    and now - term_at >= bounds["term_grace_seconds"]
                ):
                    record["signals"].append(owner.send(signal.SIGKILL))
                    kill_at = now
                if kill_at is not None and now - kill_at >= bounds["kill_reap_seconds"]:
                    raise TimeoutError("terminal wait4 missing after KILL deadline")
                time.sleep(bounds["sample_seconds"])
        terminal = owner.terminal
        require(time.monotonic() < deadline, "normal target exited after readiness-case deadline")
        require(
            terminal is not None and owner.collect() is terminal,
            "missing/uncached terminal outcome",
        )
        require(
            "stop_reason" not in record and terminal["returncode"] == 0, "normal exit not observed"
        )
        path = out / "stdout.json"
        require(
            0 < path.stat().st_size <= bounds["max_record_bytes"],
            "missing/oversized child handshake",
        )
        ready = json.loads(path.read_text())
        require(
            ready["ready"] is True
            and ready["pid"] == pid
            and ready["ppid"] == os.getpid()
            and ready["pgid"] == pid
            and ready["session_id"] == pid
            and ready["mode"] == "normal",
            "normal/session handshake mismatch",
        )
        require(
            terminal["ru_maxrss_native_units"] == "Linux KiB"
            and terminal["kernel_reported_direct_child_high_water_bytes"]
            == terminal["rusage_native"]["ru_maxrss"] * 1024,
            "terminal native high-water conversion mismatch",
        )
        record["handshake"] = ready
    finally:
        if owner is None and launch is not None and launch.pid is not None:
            owner = method.WaitOwner(launch.pid)
        method.cleanup(owner, record, bounds["kill_reap_seconds"])
        if launch is not None:
            launch.close()
            (out / "startup-readiness.bin").write_bytes(launch.data)
            record["startup_parent_fds_closed"] = not launch.opened
        record["terminal"] = owner.terminal if owner is not None else None
        record["elapsed_seconds"] = time.monotonic() - started
        write(out / "normal-lifecycle.json", record)
    require(
        "cleanup_gap" not in record and owner is not None and not owner.wait_lost,
        "cleanup/ownership unresolved; block any further case",
    )
    return {
        "lifecycle_file": "normal-lifecycle.json",
        "terminal": owner.terminal,
        "scope": "normal direct-child capability only; signal/recovery paths unqualified",
    }


def small_lifecycle_case(case_name, out, grant, bounds, obs, method):
    """Run one of four declared target-ready lifecycle cases; never kill the observer."""
    mode = "ignore-term" if case_name == "Q2-ignore-term-kill" else "default"
    expected_signal = 9 if case_name in ("Q2-ignore-term-kill", "Q2-supported-sigint") else 15
    fixture = QUAL / "fixtures/lifecycle-target-v1.txt"
    argv = [
        sys.executable,
        "-c",
        fixture.read_text(),
        mode,
        grant["launch_nonce"],
        str(bounds["target_self_exit_seconds"]),
    ]
    record = {
        "case": case_name,
        "mode": mode,
        "target_argv": argv,
        "fixture_sha256": obs.digest(fixture),
        "signals": [],
        "expected_terminal_signal": expected_signal,
        "scope": "tiny stdlib handling only; no scientific or comparative memory result",
    }
    owner = None
    launch = None
    error = None
    cancellation_requested = False
    cancellation_observed = False
    target_ready = None
    acted = False
    term_at = None
    kill_at = None
    target_deadline = None
    started = time.monotonic()
    overall_deadline = started + bounds["life_deadline_seconds"]
    readiness_deadline = started + bounds["startup_timeout_seconds"]
    write(
        out / "spawn-intent.json",
        {
            "observer": obs.process_identity(os.getpid()),
            "target_argv": argv,
            "fixture_sha256": record["fixture_sha256"],
            "intent_only": True,
        },
    )
    try:
        with (
            (out / "stdout.json").open("x") as stdout,
            (out / "stderr.log").open("x") as stderr,
            (out / "samples.jsonl").open("x") as samples,
        ):
            launch = obs.FixedSessionLaunch(
                argv,
                os.environ.copy(),
                grant["launch_nonce"],
                stdout.fileno(),
                stderr.fileno(),
                bounds["startup_pipe_bytes"],
            )
            record.update(
                bootstrap_sha256=obs.SESSION_BOOTSTRAP_SHA256,
                bootstrap_argv=launch.argv,
                file_actions=launch.actions,
                fd_plan=launch.fd_plan,
            )
            write(out / "fixed-route-intent.json", record)
            pid = launch.spawn()
            owner = method.WaitOwner(pid)
            launch.release_parent_writers()
            record["workload_pid"] = pid
            write(
                out / "owned-child.json",
                {
                    "identity": obs.process_identity(pid),
                    "observer_pid": os.getpid(),
                    "nonce": grant["launch_nonce"],
                    "target_argv": argv,
                },
            )
            while True:
                terminal = owner.collect()
                bootstrap = launch.drain()  # Drain even after terminal was cached.
                now = time.monotonic()
                if bootstrap is not None and "bootstrap_ready" not in record:
                    require(now < readiness_deadline, "bootstrap readiness arrived late")
                    record["bootstrap_ready"] = bootstrap
                    write(out / "session-ready.json", bootstrap)
                with (out / "stdout.json").open("rb") as stream:
                    raw = stream.read(bounds["target_ready_bytes"] + 1)
                require(len(raw) <= bounds["target_ready_bytes"], "target readiness exceeds bound")
                if target_ready is None and b"\n" in raw:
                    require(
                        raw.count(b"\n") == 1 and raw.endswith(b"\n"),
                        "target readiness malformed/multiple",
                    )
                    target_ready = json.loads(raw)
                    require(
                        bootstrap is not None and now < readiness_deadline,
                        "target ready without timely bootstrap",
                    )
                    require(
                        target_ready.get("role") == "holding-target"
                        and target_ready.get("pid") == pid
                        and target_ready.get("ppid") == os.getpid()
                        and target_ready.get("pgid") == pid
                        and target_ready.get("session_id") == pid
                        and target_ready.get("nonce") == grant["launch_nonce"]
                        and target_ready.get("executable") == grant["python_resolved"]
                        and target_ready.get("mode") == mode,
                        "target identity/session/nonce/mode mismatch",
                    )
                    require(
                        type(target_ready.get("term_handler_native")) is int
                        and target_ready["term_handler_native"]
                        == (1 if mode == "ignore-term" else 0)
                        and target_ready.get("self_exit_backstop_seconds")
                        == bounds["target_self_exit_seconds"],
                        "target handler/backstop not observed before control action",
                    )
                    record.update(
                        target_ready=target_ready, target_ready_monotonic_ns=time.monotonic_ns()
                    )
                    write(out / "target-ready.json", target_ready)
                terminal = owner.collect()
                if terminal is not None:
                    break
                sample = obs.process_sample(pid)
                sample["ancestor_current_bytes"] = {
                    path: obs.read(Path(path) / "memory.current")
                    for path in grant["ancestor_stop_bytes"]
                }
                sample["child_cgroup"] = obs.read(f"/proc/{pid}/cgroup")
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                if owner.collect() is not None:
                    continue
                require(
                    type(sample.get("VmRSS_bytes")) is int and sample["VmRSS_bytes"] >= 0,
                    "required live-child RSS observation lost",
                )
                require(
                    sample["VmRSS_bytes"] < grant["process_stop_bytes"]
                    and sample["host_available_bytes"] is not None
                    and sample["host_available_bytes"] > grant["host_min_available_bytes"],
                    "process/host safety stop",
                )
                require(
                    sample["child_cgroup"] == obs.read("/proc/self/cgroup")
                    and all(
                        value is not None and int(value) < grant["ancestor_stop_bytes"][path]
                        for path, value in sample["ancestor_current_bytes"].items()
                    ),
                    "cgroup safety stop",
                )
                now = time.monotonic()
                if target_ready is not None and not acted:
                    acted = True
                    record["control_preconditions_observed"] = True
                    if case_name == "Q2-supported-sigint":
                        cancellation_requested = True
                        record["supported_sigint_requested_monotonic_ns"] = time.monotonic_ns()
                        os.kill(os.getpid(), signal.SIGINT)
                    elif case_name == "Q2-deadline":
                        target_deadline = now + bounds["deadline_after_target_ready_seconds"]
                        record["target_deadline_monotonic_ns"] = int(target_deadline * 1e9)
                    else:
                        record["signals"].append(owner.send(signal.SIGTERM))
                        term_at = now
                        record["term_requested_monotonic_ns"] = time.monotonic_ns()
                if target_ready is None and now >= readiness_deadline:
                    raise TimeoutError("bootstrap/target readiness deadline")
                if target_deadline is not None and now >= target_deadline and term_at is None:
                    record.update(
                        deadline_decision_monotonic_ns=time.monotonic_ns(),
                        stop_reason="declared_target_deadline",
                    )
                    record["signals"].append(owner.send(signal.SIGTERM))
                    term_at = now
                    record["term_requested_monotonic_ns"] = time.monotonic_ns()
                if now >= overall_deadline:
                    record["overall_timeout"] = True
                    if term_at is None:
                        record["signals"].append(owner.send(signal.SIGTERM))
                        term_at = now
                if (
                    term_at is not None
                    and kill_at is None
                    and now - term_at >= bounds["term_grace_seconds"]
                ):
                    if owner.collect() is not None:
                        continue
                    record["no_terminal_after_TERM_grace_monotonic_ns"] = time.monotonic_ns()
                    record["signals"].append(owner.send(signal.SIGKILL))
                    kill_at = now
                if kill_at is not None and now - kill_at >= bounds["kill_reap_seconds"]:
                    raise TimeoutError("terminal missing after KILL/reap bound")
                time.sleep(bounds["sample_seconds"])
    except KeyboardInterrupt as caught:
        if cancellation_requested:
            cancellation_observed = True
            record["cancellation_disposition"] = "expected_one_shot_SIGINT_entered_finally_cleanup"
        else:
            error = {"type": type(caught).__name__, "message": "unexpected observer interruption"}
    except BaseException as caught:
        error = {"type": type(caught).__name__, "message": str(caught)}
    finally:
        if owner is None and launch is not None and launch.pid is not None:
            owner = method.WaitOwner(launch.pid)
        method.cleanup(owner, record, bounds["kill_reap_seconds"])
        if launch is not None:
            launch.close()
            (out / "startup-readiness.bin").write_bytes(launch.data)
            record["startup_parent_fds_closed"] = not launch.opened
            record["startup_eof_observed"] = launch.eof
        record.update(
            error=error,
            terminal=owner.terminal if owner is not None else None,
            wait_ownership_lost=owner.wait_lost if owner is not None else None,
            elapsed_seconds=time.monotonic() - started,
        )
        write(out / "small-lifecycle.json", record)
    require(
        error is None
        and "cleanup_gap" not in record
        and owner is not None
        and owner.terminal is not None
        and not owner.wait_lost
        and record.get("startup_parent_fds_closed") is True,
        "lifecycle observation/cleanup failed; unresolved ownership blocks next case",
    )
    require(
        record.get("control_preconditions_observed") is True
        and target_ready is not None
        and not record.get("overall_timeout")
        and record["elapsed_seconds"] < bounds["life_deadline_seconds"],
        "expected control route not reached/collected within bounds",
    )
    terminal = owner.terminal
    require(
        owner.collect() is terminal
        and terminal["term_signal"] == expected_signal
        and terminal["signaled"]
        and not terminal["exited"],
        "expected reaped signal outcome mismatch",
    )
    if case_name == "Q2-supported-sigint":
        require(
            cancellation_requested
            and cancellation_observed
            and any(
                s["signal"] == signal.SIGKILL and s["delivery"] == "direct_pid_sent"
                for s in record["signals"]
            ),
            "supported SIGINT did not enter actual owned cleanup",
        )
    else:
        require(
            any(
                s["signal"] == signal.SIGTERM and s["delivery"] == "direct_pid_sent"
                for s in record["signals"]
            ),
            "no actual owned TERM request observed",
        )
        if case_name == "Q2-ignore-term-kill":
            require(
                "no_terminal_after_TERM_grace_monotonic_ns" in record
                and any(
                    s["signal"] == signal.SIGKILL and s["delivery"] == "direct_pid_sent"
                    for s in record["signals"]
                ),
                "TERM-ignore grace/KILL route not observed",
            )
        if case_name == "Q2-deadline":
            require(
                record.get("stop_reason") == "declared_target_deadline"
                and record["deadline_decision_monotonic_ns"]
                >= record["target_deadline_monotonic_ns"],
                "declared deadline decision missing",
            )
    require(
        terminal["ru_maxrss_native_units"] == "Linux KiB"
        and terminal["kernel_reported_direct_child_high_water_bytes"]
        == terminal["rusage_native"]["ru_maxrss"] * 1024,
        "kernel terminal units/conversion mismatch",
    )
    return {
        "lifecycle_file": "small-lifecycle.json",
        "expected_control_outcome": case_name,
        "terminal": terminal,
        "scope": "scoped handling pass, not child exit0 or scientific memory proof",
    }


def main():
    """Run exactly one released readiness case; preserve every failed attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=("Q0-context", "Q1-normal", *Q2_CASES, Q4_CASE, Q5_CASE, M6_CASE),
        required=True,
    )
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    args = parser.parse_args()
    require(
        args.attempt_id
        and all(
            c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in args.attempt_id
        ),
        "safe unique attempt id required",
    )
    if args.case == M6_CASE:
        return pure_method6(args)
    out = QUAL / "attempts" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    receipt = {
        "protocol": "WS116-qualification-phase-small-v2",
        "case": args.case,
        "attempt_id": args.attempt_id,
        "status": "qualification_failed",
        "driver_pid": os.getpid(),
        "interpreter": {
            "version": sys.version,
            "executable": sys.executable,
            "resolved": str(Path(sys.executable).resolve()),
        },
        "argv": sys.argv,
        "started_monotonic_ns": time.monotonic_ns(),
        "not_scientific_evidence": True,
    }
    obs = None
    try:
        (out / "grant.input").write_bytes(args.grant.read_bytes())
        grant = json.loads((out / "grant.input").read_text())
        inventory = json.loads((QUAL / "inventory.json").read_text())
        sys.path.insert(0, str(HERE))
        import observer as obs
        import run_attempt as method

        no_product()
        receipt["grant_sha256"] = obs.digest(out / "grant.input")
        identities = admission(args, grant, inventory, obs, method, out)
        receipt.update(
            source_sha256=identities,
            exposed_domain=grant["resource_domain"]["expected_exposed"],
            driver_identity=obs.process_identity(os.getpid()),
            resource_domain=grant["resource_domain"],
        )
        deadline = time.monotonic() + inventory["common_bounds"]["soft_deadline_seconds"]
        if args.case in (*Q2_CASES, Q4_CASE):
            require(
                not any(
                    name == "numpy"
                    or name.startswith("numpy.")
                    or name == "scipy"
                    or name.startswith("scipy.")
                    for name in sys.modules
                ),
                "Q2 scientific module import forbidden",
            )
            if args.case == Q4_CASE:
                result = parser_case(out, grant, inventory["q4_bounds"], obs, method)
            else:
                result = small_lifecycle_case(
                    args.case, out, grant, inventory["common_bounds"], obs, method
                )
        elif args.case == Q5_CASE:
            result = tiny_hash_case(out, grant, inventory["q5_bounds"], obs)
        elif args.case == "Q0-context":
            result = context_case(out, obs)
        else:
            result = normal_case(out, grant, inventory["common_bounds"], obs, method)
        require(time.monotonic() <= deadline, "readiness case exceeded soft deadline")
        no_product()
        method.exposed_domain_admission(grant, obs.cgroup_ancestors())
        require(
            source_identities(grant, obs) == identities,
            "material inputs changed during readiness case",
        )
        receipt.update(result=result, status=PASS)
    except BaseException as error:
        receipt.update(error_type=type(error).__name__, error_message=str(error))
    finally:
        receipt["finished_monotonic_ns"] = time.monotonic_ns()
        if obs is not None:
            try:
                receipt["postflight"] = obs.context(ROOT)
            except BaseException as error:
                receipt.update(status="qualification_failed", postflight_error=str(error))
        receipt["files_before_receipt"] = {
            path.name: {
                "logical_bytes": path.stat().st_size,
                "allocated_bytes": path.stat().st_blocks * 512,
            }
            for path in out.iterdir()
            if path.is_file()
        }
        receipt["limits"] = (
            "No product workflow, aggregate-tree peak or comparative scientific memory envelope. "
            "Terminal wait4 is kernel-reported direct-child usage through final exit. "
            "Inherited/pre-exec/exec-transition high-water retention remains unresolved; "
            "same PID does not guarantee every "
            "bootstrap/startup peak survives exec. No subtraction/aggregate/benefit claim. "
            "Parent death/spawn-marker gaps, abrupt-loss recovery and science are unqualified. "
            "Q4, when selected, covers only its exact synthetic interfaces/vector expectations. "
            "Q5, when selected, covers tiny value identity/finite checks only, never peak benefit. "
            "Receipt excludes its own disk bytes. No retry; unresolved ownership "
            "blocks another case."
        )
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
