"""UNEXECUTED WS116 report support; source preparation is not analysis authority.

Stdlib/file-only future aggregation of explicit immutable ROOT-selected records.
No measurement, launch, retry, discovery, plotting, product import or controller.
Requires a new ROOT analysis release AFTER the serial data window is closed.
Consumes the frozen f6 binder's actual boundary/config schema directly.
Source reconciliation is documented in report-plan.md; no code has been run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "inputs"
SCHEMA_INPUTS = HERE / "schema-inputs"
SOURCE_MANIFEST = "49db118fc930f6c86c8f24201fb9de001a7d3b47aac9fdc7670143c59f922a72"
SCHEMA_MANIFEST = "1350a5cfacb72e4a7d18b9947b002a56a6178bef45cd6b399a87bc66a5b3395d"
BINDER_SHA = "f6b89920979c0f73a5860190a7d14735c2b63d7b27d6482c02465f3c649d1d24"
CAPTURE_SHA = "47215ee63496e2043e0f5668c1d2d433351ca6067550f11f469f257ccccda68f"
TABLE_SHA = "0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d"
BASIS_SHA = "bcfbb0352618325a4363952ed2f58bd2fe0660d730b0d6138093bdbc8a22303c"
OLD_FAILED_SHA = "ea1132b9b6d5705768c3efaecb5e02d4d332de9e3186317d1809fb8558f1fee5"
MAX_RECORDS = 256
MAX_REFERENCES = 8192
MAX_JSON = 8 * 1024 * 1024
MAX_ARTIFACT = 4 * 1024**3
MAX_HASH_BYTES = 64 * 1024**3
CHUNK = 1024 * 1024
SNAPSHOT_SCOPES = {
    "pre_call": "after input hashes/retention, before call timestamp",
    "call_end": "after call/end timestamp, before result observations",
    "post_observation": (
        "after context/hash/retention/finite/identity observations, "
        "before JSON serialization and teardown"
    ),
}
METRICS = (
    "terminal_native_KiB", "terminal_kernel_bytes", "call_seconds",
    "spawn_to_terminal_collection_seconds", "target_start_to_last_snapshot_seconds",
    "pre_call_cumulative_self_bytes", "call_end_cumulative_self_bytes",
    "post_observation_cumulative_self_bytes",
)


def need(ok, message):
    """Reject an audit/selection mismatch without changing or repairing evidence."""
    if not ok:
        raise ValueError(message)


def object_without_duplicates(pairs):
    """Do not silently accept ambiguous duplicate JSON fields."""
    result = {}
    for key, value in pairs:
        need(key not in result, "duplicate JSON field: " + key)
        result[key] = value
    return result


def decode(payload):
    """Reject nonstandard NaN/Infinity JSON constants as malformed metadata."""
    def invalid(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(payload, object_pairs_hook=object_without_duplicates, parse_constant=invalid)


def sha_text(value):
    """Validate a declared lowercase SHA256 fingerprint."""
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def nonnegative(value):
    """Keep bool and missing/native unknown values distinct from integers."""
    return type(value) is int and value >= 0


def finite_seconds(value):
    """Require an actual finite nonnegative timing observation."""
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


class Files:
    """Bound explicit file reads/hashes; never glob or sample a live process."""

    def __init__(self, roots):
        self.roots = tuple(Path(root).resolve() for root in roots)
        self.remaining = MAX_HASH_BYTES
        self.operations = 0
        self.audit = []

    def read(self, reference, *, as_json=False):
        """Hash one named immutable artifact and optionally parse bounded JSON."""
        self.operations += 1
        need(self.operations <= MAX_REFERENCES, "explicit file-reference bound exceeded")
        need(set(reference) == {"path", "sha256"} and sha_text(reference["sha256"]), "bad file reference")
        path = Path(reference["path"]).resolve()
        need(any(path.is_relative_to(root) for root in self.roots), "file outside explicit roots")
        before = path.stat()
        limit = MAX_JSON if as_json else MAX_ARTIFACT
        need(path.is_file() and before.st_size <= limit, "file missing/nonregular/over bound")
        digest = hashlib.sha256()
        pieces = [] if as_json else None
        read_bytes = 0
        with path.open("rb") as stream:
            while block := stream.read(CHUNK):
                read_bytes += len(block)
                self.remaining -= len(block)
                need(read_bytes <= limit and self.remaining >= 0, "declared file/hash budget exceeded")
                digest.update(block)
                if pieces is not None:
                    pieces.append(block)
        after = path.stat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
             "artifact changed during read")
        need(digest.hexdigest() == reference["sha256"], "artifact SHA256 differs")
        self.audit.append({
            **reference, "logical_bytes": after.st_size,
            "allocated_bytes": after.st_blocks * 512,
        })
        return decode(b"".join(pieces)) if pieces is not None else None


def input_ref(name, digest):
    """Address only an exact frozen source input, not an active worktree."""
    return {"path": str(INPUTS / name), "sha256": digest}


def boundary_for(entry, files, basis, recipe):
    """Read the actual eligible boundary and its actual authorized batch config."""
    boundary = files.read(entry["boundary"], as_json=True)
    cfg = files.read(entry["batch_config"], as_json=True)
    need(boundary["status"] == "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW" and
         boundary["row"] == recipe, "actual boundary status/row differs")
    need(boundary["candidate"] == basis["candidate"] and
         boundary["material_hashes"] == basis["material_hashes"], "boundary basis/material mismatch")
    need(boundary["table_sha256"] == TABLE_SHA and
         boundary["config_sha256"] == entry["batch_config"]["sha256"] and
         boundary["source_sha256"] == cfg["binder_sha256"] == BINDER_SHA,
         "actual config/source/table binding differs")
    need(cfg["authorized"] is True and cfg["candidate"] == basis["candidate"] and
         cfg["material_hashes"] == basis["material_hashes"] and
         recipe["attempt_id"] in cfg["allowed_attempt_ids"], "actual batch release/basis differs")
    need(boundary["method7"] == cfg["accepted_method7"], "actual method7 reference differs")
    method7 = files.read(cfg["accepted_method7"], as_json=True)
    need(method7 == cfg["method7_expected"] and method7["candidate"] == basis["candidate"] and
         method7["suitable"] is True and method7["qualified"] is True and
         method7["runner_end_domain_check"] is False and
         method7["source_basis"]["sha256"] == BASIS_SHA,
         "actual qualified method7/basis differs")
    need(files.read(method7["source_basis"], as_json=True) == basis, "method7 source basis bytes differ")
    files.read(method7["review_report"])
    for key, expected in (("root_authority", "authority_expected"),
                          ("environment", "environment_expected"),
                          ("scheduler_ack", "scheduler_ack_expected")):
        need(cfg[expected] is not None and files.read(cfg[key], as_json=True) == cfg[expected],
             "actual config support differs: " + key)
    ledger = files.read(cfg["owned_ledger"], as_json=True)
    need(ledger["scope"] == "WS116_scientific_observer_workload_processes" and
         ledger["unresolved"] == [] and
         ledger["root_authority_sha256"] == cfg["root_authority"]["sha256"], "owned ledger unresolved")
    files.read(cfg["metadata_source"])
    end_scope = ("binder original-proof hash/horizon + fresh end domain/context/margins/events; "
                 "runner receipt does not perform this check")
    need(boundary["end_validation_scope"] == end_scope, "binder end-validation scope differs")
    raw = Path(boundary["raw_path"]).resolve()
    need(raw == (Path(cfg["root"]) / "docs/reports/reconstruction-working-set/raw" /
                 recipe["attempt_id"]).resolve(), "actual raw path/attempt differs")
    need(0 < len(boundary["raw_files"]) <= 32, "actual raw inventory unbounded/empty")
    refs = {}
    for name, metadata in boundary["raw_files"].items():
        need(Path(name).name == name and name not in {"", ".", ".."} and
             sha_text(metadata["sha256"]) and nonnegative(metadata["logical_bytes"]) and
             nonnegative(metadata["allocated_bytes"]), "malformed raw inventory")
        refs[name] = {"path": str(raw / name), "sha256": metadata["sha256"]}
    return boundary, cfg, refs


def audit_operational(entry, boundary, cfg, grant, files):
    """Audit pinned recorded support; never apply current wall-clock freshness."""
    required = {"intent.json", "grant.json", "observer-exit.json", "raw-files.json"}
    required |= {phase + suffix for phase in ("pre", "post") for suffix in (
        "-capture-command.json", "-metadata.json", "-metadata-request.json",
        "-metadata-intent.json", "-metadata-command.json",
    )}
    refs = entry["support"]
    need(required <= set(refs) and len(refs) <= 24, "actual row support missing/unbounded")
    directory = Path(entry["boundary"]["path"]).resolve().parent
    need(directory == (Path(cfg["external_batch_directory"]) / boundary["row"]["attempt_id"]).resolve(),
         "actual boundary directory differs")
    records = {}
    for name, reference in refs.items():
        need(Path(name).name == name and Path(reference["path"]).resolve() == directory / name,
             "actual supporting file/name differs")
        records[name] = files.read(reference, as_json=name in required)
    need(records["grant.json"] == grant and
         refs["grant.json"]["sha256"] == boundary["raw_files"]["grant.input"]["sha256"],
         "actual external/raw grant differs")
    need(records["raw-files.json"] == boundary["raw_files"], "external raw inventory differs")
    intent, observed = records["intent.json"], records["observer-exit.json"]
    need(intent["row"] == boundary["row"] and intent["config_sha256"] == boundary["config_sha256"] and
         intent["source_sha256"] == BINDER_SHA and
         intent["grant_sha256"] == refs["grant.json"]["sha256"], "actual invocation intent differs")
    need(observed["returncode"] == 0 and observed["overdue"] is False and observed["wait_gaps"] == [],
         "observer/proxy exit not eligible")
    invocation = observed["runner_invocation_unix_ns"]
    window = cfg["window"]
    need(nonnegative(invocation) and window["starts_unix_ns"] <= invocation < window["ends_unix_ns"],
         "recorded invocation outside actual window")
    need(intent["time_unix_ns"] <= invocation and grant["root_release_at_unix_ns"] <= invocation and
         grant["exclusive_window"] == cfg["grant_fixed"]["exclusive_window"] and
         grant["exclusive_window"]["released"] is True and
         grant["exclusive_window"]["evidence_sha256"] == cfg["root_authority"]["sha256"],
         "actual grant/authority/invocation binding differs")
    proof_records = {}
    for phase in ("pre", "post"):
        command = records[phase + "-capture-command.json"]
        need(command["returncode"] == 0, "recorded capture failed")
        pointer = decode(command["stdout"])
        reference = {"path": pointer["path"], "sha256": pointer["sha256"]}
        proof = files.read(reference, as_json=True)
        need(proof["schema"] == "campaign-resource-domain-correspondence-v1" and
             proof["capture_source_sha256"] == CAPTURE_SHA and
             proof["external_ancestors"] == "unknown_unobservable" and
             proof["docker_inspect"]["returncode"] == proof["inner"]["returncode"] == 0 and
             proof["docker_inspect"]["stdout"] == cfg["docker_inspect_stdout"],
             "recorded correspondence identity differs")
        inner = decode(proof["inner"]["stdout"])
        need(proof["outer"]["file_identities"] == inner["file_identities"],
             "recorded inner/outer objects differ")
        for name, view in (("outer", proof["outer"]), ("inner", inner)):
            mapping = cfg["mapping"][name]
            need(view["cgroup_namespace"] == mapping["cgroup_namespace"] and
                 view["file_identities"] == mapping["file_identities"] and
                 all(view["files"][path] == value for path, value in mapping["fixed_files"].items()),
                 "recorded exposed mapping differs")
            need(nonnegative(view["observed_at_unix_ns"]), "recorded view timestamp invalid")
        stamp = proof["started_at_unix_ns"]
        need(nonnegative(stamp) and window["starts_unix_ns"] <= stamp < window["ends_unix_ns"],
             "recorded capture outside window")
        metadata = records[phase + "-metadata.json"]
        request_ref = refs[phase + "-metadata-request.json"]
        metadata_intent = records[phase + "-metadata-intent.json"]
        metadata_command = records[phase + "-metadata-command.json"]
        need(metadata_command["returncode"] == 0 and decode(metadata_command["stdout"]) == metadata and
             metadata["protocol"] == "WS116-fixed-ubuntu-metadata-v1" and
             metadata["source_sha256"] == cfg["metadata_source"]["sha256"] and
             metadata["request_sha256"] == request_ref["sha256"] and
             metadata_intent["source"] == cfg["metadata_source"] and
             metadata_intent["request_sha256"] == request_ref["sha256"], "recorded metadata linkage differs")
        for key in ("uid", "gid", "executable", "cwd", "boot_id", "namespaces", "rlimits"):
            need(metadata[key] == cfg["metadata_expected"][key], "recorded metadata differs: " + key)
        request = records[phase + "-metadata-request.json"]
        need(len(metadata["owned_processes"]) == len(request["owned_processes"]) and
             all(item["expected"] == expected and item["identity_state"] == "absent" and
                 set(item["fds"]) == {str(fd) for fd in expected["fds"]} and
                 all(fact["state"] == "absent" for fact in item["fds"].values())
                 for item, expected in zip(metadata["owned_processes"], request["owned_processes"], strict=True)),
             "recorded owned PID/FD disposition unresolved")
        need(metadata["outside_campaign_processes"] == "unknown_not_scanned" and
             nonnegative(metadata["observed_at_unix_ns"]), "metadata scope/time invalid")
        proof_records[phase] = {"proof": reference, "started_at_unix_ns": stamp,
            "outer_observed_at_unix_ns": proof["outer"]["observed_at_unix_ns"],
            "inner_observed_at_unix_ns": inner["observed_at_unix_ns"],
            "metadata_observed_at_unix_ns": metadata["observed_at_unix_ns"]}
    original = grant["resource_domain"]["correspondence_evidence"]
    pre = proof_records["pre"]
    need({key: intent["proof"][key] for key in ("path", "sha256")} == pre["proof"] and
         {key: original[key] for key in ("path", "sha256")} == pre["proof"] and
         original["observed_at_unix_ns"] == pre["started_at_unix_ns"], "original proof binding differs")
    age_ns = invocation - pre["started_at_unix_ns"]
    need(0 <= age_ns <= 5000000000 and
         observed["proof_age_at_invocation_seconds"] == age_ns / 1e9 and
         0 <= invocation - pre["metadata_observed_at_unix_ns"] <= cfg["metadata_max_age_seconds"] * 1e9,
         "recorded invocation proof/metadata ages invalid")
    need(proof_records["post"]["started_at_unix_ns"] >= invocation,
         "post capture precedes invocation")
    # f6 checks the original horizon after fresh post context. Its boundary has
    # no exact final-check timestamp. Do not fabricate one from a capture time.
    return {"batch_config": entry["batch_config"], "source_sha256": BINDER_SHA,
        "method7": boundary["method7"], "root_authority": cfg["root_authority"],
        "support": refs, "runner_invocation_unix_ns": invocation,
        "recorded_proof_age_at_invocation_seconds": age_ns / 1e9,
        "recorded_captures": proof_records, "original_proof_maximum_age_seconds": original["maximum_age_seconds"],
        "binder_end_validation_scope": boundary["end_validation_scope"],
        "exact_binder_final_horizon_check_unix_ns": None,
        "end_audit_limit": "accepted f6 boundary asserts final horizon/window check; exact check time not exported; no analysis-wall freshness or new host observation"}


def audit_initial(entry, recipe, plan, basis, files):
    """Cross-check one completed initial row; retain only compact observations."""
    need(entry["phase"] == "initial" and entry["attempt_id"] == recipe["attempt_id"], "wrong selected row")
    boundary, cfg, refs = boundary_for(entry, files, basis, recipe)
    need(refs["receipt.json"]["sha256"] != OLD_FAILED_SHA, "old failed trial cannot be primary")
    need({"receipt.json", "stdout.json", "spec.json", "grant.input", "owned-child.json"} <= set(refs),
         "required raw files omitted")
    receipt = files.read(refs["receipt.json"], as_json=True)
    need(files.audit[-1]["logical_bytes"] == boundary["raw_files"]["receipt.json"]["logical_bytes"],
         "receipt logical size differs")
    inventory = receipt["files_before_receipt"]
    need(set(refs) == set(inventory) | {"receipt.json"}, "raw inventory differs or receipt self-hash invented")
    loaded = {}
    for name, metadata in inventory.items():
        need(Path(name).name == name and metadata["sha256"] == refs[name]["sha256"], "raw fingerprint differs")
        loaded[name] = files.read(refs[name], as_json=name in {
            "stdout.json", "spec.json", "grant.input", "owned-child.json",
        })
        need(files.audit[-1]["logical_bytes"] == boundary["raw_files"][name]["logical_bytes"] ==
             metadata["logical_bytes"], "raw logical size differs")
    child, spec, grant, marker = (loaded[name] for name in (
        "stdout.json", "spec.json", "grant.input", "owned-child.json",
    ))
    operational = audit_operational(entry, boundary, cfg, grant, files)
    need(boundary["fingerprints"] == {key: child[key] for key in (
        "input_sha256", "common_output_sha256", "public_result_sha256", "branches")},
        "actual boundary fingerprints differ")
    for key, expected in cfg["environment_expected"]["software"].items():
        need(child[key] == expected, "child/software binding differs: " + key)
    need(receipt["protocol"] == "WS116-attempt-v3" and receipt["status"] ==
         "complete_child_observed_pending_scientific_qualification", "runner incomplete/failed")
    need(marker["attempt_id"] == recipe["attempt_id"], "owned marker attempt differs")
    for key in ("stop_reason", "cleanup_gap", "postflight_gap", "error_type"):
        need(not receipt.get(key), "runner failure/gap: " + key)
    need(receipt["wait_ownership_lost"] is False and receipt["startup_parent_fds_closed"] is True,
         "ownership/FD evidence incomplete")
    for key in ("candidate_before", "candidate_after", "candidate_final"):
        need(receipt[key] == basis["candidate"], "candidate changed")
    for key in ("material_hashes_before", "material_hashes_after", "material_hashes_final"):
        need(receipt[key] == basis["material_hashes"], "receipt material map changed")
    need(grant["candidate"] == basis["candidate"] and grant["material_hashes"] == basis["material_hashes"],
         "grant material/candidate mismatch")
    need(grant["numerical_release"] is True and grant["accepted_112_then_115"] is True,
         "runtime grant absent")
    need(grant["resource_domain"]["expected_exposed"] == cfg["expected_exposed"] and
         grant["attempt_id"] == recipe["attempt_id"], "actual grant domain/attempt differs")
    for key in ("condition_id", "repetition", "profile"):
        need(grant[key] == recipe[key], "grant row differs")
    condition = plan["condition"]
    need({key: spec[key] for key in condition} == condition and
         spec["repetition"] == recipe["repetition"] and spec["profile"] is False,
         "spec not the exact unprofiled condition")
    need(spec["expected_material_hashes"] == basis["material_hashes"] and child["spec"] == spec,
         "child spec/material mismatch")
    need(child["protocol"] == "WS116-child-v2" and child["status"] ==
         "finite_observation_pending_qualification" and child["finite_common_fields"] is True and
         child["material_identity_matches"] is True and receipt["material_identity_matches"] is True,
         "child not complete finite/identity observation")
    need(child["material_hashes_before"] == basis["material_hashes"] and
         child["material_hashes_after"] == basis["material_hashes"], "child material map changed")
    need(receipt["child_record_sha256"] == refs["stdout.json"]["sha256"], "child fingerprint mismatch")
    need(receipt["grant_sha256"] == refs["grant.input"]["sha256"] and
         marker["grant_sha256"] == refs["grant.input"]["sha256"] and
         marker["spec_sha256"] == refs["spec.json"]["sha256"], "marker/grant/spec mismatch")
    pid = receipt["workload_pid"]
    terminal = receipt["terminal"]
    need(child["pid"] == terminal["pid"] == marker["workload_pid"] == pid, "exact child PID mismatch")
    need(grant["launch_nonce"] == recipe["launch_nonce"] == spec["launch"]["nonce"] and
         receipt["launch"] == spec["launch"] and
         spec["launch"]["bootstrap_sha256"] == basis["bootstrap_sha256"], "launch/source binding differs")
    ready = receipt["session_ready"]
    need(ready["nonce"] == grant["launch_nonce"] and
         ready["pid"] == ready["pgid"] == ready["session_id"] == pid and
         ready["ppid"] == marker["observer_pid"] == receipt["observer_pid"], "session/lineage mismatch")
    need(spec["expected_exposed_domain"] == grant["resource_domain"]["expected_exposed"],
         "admitted exposed domain mismatch")
    identity = marker["child_identity"]
    need(identity["pid"] == pid and isinstance(identity["boot_id"], str) and identity["boot_id"] and
         nonnegative(identity["start_ticks"]), "fresh process identity unavailable")
    need(terminal["wait_status_raw"] == 0 and terminal["returncode"] == 0 and
         terminal["exited"] is True and terminal["signaled"] is False, "not normal exit0")
    native = terminal["rusage_native"]["ru_maxrss"]
    need(nonnegative(native) and terminal["ru_maxrss_native_units"] == "Linux KiB" and
         terminal["ru_maxrss_multiplier_to_bytes"] == 1024 and
         terminal["kernel_reported_direct_child_high_water_bytes"] == native * 1024, "terminal native units")
    need(child["branches"] == plan["expected_output"]["branches"] and child["stages"] == [],
         "branch/profile mismatch")
    expected_outputs = {
        name: (plan["expected_output"]["modulation_and_raw"] if name in {"modulation", "raw_modulation"}
               else plan["expected_output"][name])
        for name in ("image", "x_um", "y_um", "z_um", "carriers_cyc_um", "modulation", "raw_modulation")
    }
    for name, expected in expected_outputs.items():
        item = child["output_hashes"][name]
        need(item[0] == name and item[1] == expected["shape"] and
             item[2] == ("<c16" if expected["dtype"] == "complex128" else "<f8") and sha_text(item[3]),
             "output identity shape/dtype/hash mismatch")
    for name, expected_name, shape, dtype in (
        ("specimen", "specimen", plan["fixture"]["raw_shape_TDPZYX"], "<f4"),
        ("transfer", "transfer.samples", plan["fixture"]["transfer_shape"], "<c16"),
    ):
        item = child["input_arrays"][name]
        need(item[0] == expected_name and item[1] == shape and item[2] == dtype and sha_text(item[3]),
             "input array identity mismatch")
    for key in ("input_sha256", "common_output_sha256", "public_result_sha256"):
        need(sha_text(child[key]), "missing value fingerprint")
    snapshots = child["snapshots"]
    need(set(snapshots) == set(SNAPSHOT_SCOPES), "snapshot names differ")
    for name, scope in SNAPSHOT_SCOPES.items():
        item = snapshots[name]
        need(item["scope"] == scope and nonnegative(item["ru_maxrss_native"]) and
             item["ru_maxrss_native_units"] == "Linux KiB" and
             item["cumulative_high_water_bytes"] == item["ru_maxrss_native"] * 1024,
             "snapshot native/scope mismatch")
    call = child["elapsed_call_seconds"]
    wall = (terminal["reaped_monotonic_ns"] - receipt["spawn_start_monotonic_ns"]) / 1e9
    target = (snapshots["post_observation"]["monotonic_ns"] - child["started_monotonic_ns"]) / 1e9
    need(all(finite_seconds(value) for value in (call, wall, target)), "invalid timing")
    need(call == (child["call_end_monotonic_ns"] - child["call_start_monotonic_ns"]) / 1e9,
         "call timing derivation mismatch")
    environment = {
        key: child[key] for key in ("python", "executable", "numpy", "scipy", "numpy_backend",
                                   "scipy_fft_default_workers", "product_module", "effective_worker_limits")
    }
    environment.update({key: child["context"][key] for key in (
        "host_id_sha256", "system", "kernel", "machine", "threads", "allocator", "rlimits",
    )})
    environment["exposed_domain"] = spec["expected_exposed_domain"]
    metrics = dict(zip(METRICS, (
        native, native * 1024, call, wall, target,
        *(snapshots[name]["cumulative_high_water_bytes"] for name in SNAPSHOT_SCOPES),
    ), strict=True))
    return {
        "attempt_id": recipe["attempt_id"], "condition_id": recipe["condition_id"],
        "repetition": recipe["repetition"], "profile": False, "phase": "initial",
        "state": "eligible_descriptive_pending_scientific_review",
        "boundary_sha256": entry["boundary"]["sha256"], "receipt_sha256": refs["receipt.json"]["sha256"],
        "raw_files": boundary["raw_files"], "operational_audit": operational, "process_identity": identity,
        "environment": environment, "metrics": metrics, "terminal": terminal, "snapshots": snapshots,
        "rss_terminal_confirmation": receipt.get("rss_terminal_confirmation"),
        "initial_resource_domain": receipt["resource_domain_admission"],
        "observer_snapshot_separate_from_child": receipt.get("observer_self_snapshot"),
        "branches": child["branches"], "input_sha256": child["input_sha256"],
        "input_arrays": child["input_arrays"], "output_hashes": child["output_hashes"],
        "common_output_sha256": child["common_output_sha256"],
        "public_result_sha256": child["public_result_sha256"],
        "retained": {name: child[name] for name in ("caller_retained", "result_retained")},
        "observed_retained_dtype_labels": sorted({array["dtype"] for name in (
            "caller_retained", "result_retained") for array in child[name]["arrays"]}),
    }


def summarize(table, rows):
    """Use exactly three audited distinct processes; never use a partial median."""
    groups = []
    for condition_id in table["conditions"]:
        members = [row for row in rows if row.get("condition_id") == condition_id and
                   row.get("state") == "eligible_descriptive_pending_scientific_review"]
        reasons = []
        if sorted(row["repetition"] for row in members) != [1, 2, 3]:
            reasons.append("missing/invalid/duplicate repetition")
        if len(members) == 3:
            for key in ("environment", "input_sha256", "input_arrays", "branches", "output_hashes",
                        "common_output_sha256", "public_result_sha256"):
                if any(row[key] != members[0][key] for row in members[1:]):
                    reasons.append("repeat mismatch: " + key)
            process_keys = {(row["process_identity"]["boot_id"], row["process_identity"]["start_ticks"],
                             row["process_identity"]["pid"]) for row in members}
            if len(process_keys) != 3:
                reasons.append("not three distinct process identities")
        metrics = None if reasons else {
            key: {"min": min(row["metrics"][key] for row in members),
                  "median": statistics.median(row["metrics"][key] for row in members),
                  "max": max(row["metrics"][key] for row in members)}
            for key in METRICS
        }
        groups.append({"condition_id": condition_id, "eligible_repetitions": sorted(
            row["repetition"] for row in members), "status": "incomplete_or_mismatched" if reasons else
            "three_repeat_descriptive_only", "reasons": reasons, "metrics": metrics})
    return groups


def full_summary_pairs(table, rows):
    """Compare only matched full/summary shape/case/search/repetition/environment."""
    pairs = []
    conditions = table["conditions"]
    for full_id, plan in conditions.items():
        full = plan["condition"]
        if full["mode"] != "full":
            continue
        for summary_id, other in conditions.items():
            summary = other["condition"]
            if summary["mode"] != "summary" or any(full.get(key) != summary.get(key)
                                                 for key in ("shape", "case", "search")):
                continue
            for repetition in (1, 2, 3):
                a = next((row for row in rows if row.get("condition_id") == full_id and
                          row.get("repetition") == repetition and row.get("metrics")), None)
                b = next((row for row in rows if row.get("condition_id") == summary_id and
                          row.get("repetition") == repetition and row.get("metrics")), None)
                keys = ("environment", "input_sha256", "input_arrays", "branches",
                        "output_hashes", "common_output_sha256")
                mismatches = ["missing eligible pair"] if a is None or b is None else [
                    key for key in keys if a[key] != b[key]]
                pairs.append({"full": full_id, "summary": summary_id, "repetition": repetition,
                              "status": "unavailable_or_mismatched" if mismatches else "common_values_match",
                              "mismatches": mismatches,
                              "public_result_fingerprints": "structurally different modes; not compared"})
    return pairs


def dump(path, value):
    """Write derived analysis separately, never mutate source observations."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def audit_excluded(entry, files):
    """Keep excluded evidence errors distinct from declared historical absence."""
    need(entry["phase"] in {"failed", "refused", "profile", "growth", "historical"} and
         isinstance(entry["reason"], str) and entry["reason"], "unclassified excluded record")
    availability = entry["availability"]
    need(availability in {"available", "unknown", "unavailable"}, "unknown availability label")
    evidence = entry.get("evidence", [])
    if availability != "available":
        need(entry["phase"] == "historical" and evidence == [],
             "declared historical absence must not invent evidence pointers")
        return {**entry, "state": "declared_historical_unknown_or_unavailable", "evidence_errors": []}
    need(0 < len(evidence) <= 32, "available excluded evidence missing/unbounded")
    errors = []
    for reference in evidence:
        try:
            files.read(reference)
        except (KeyError, IndexError, TypeError, ValueError, ArithmeticError, OSError) as error:
            errors.append({"reference": reference, "error_type": type(error).__name__, "reason": str(error)})
    return {**entry, "state": "excluded_never_pooled", "evidence_errors": errors}


def main():
    """Run only after a ROOT-frozen analysis config explicitly closes the data window."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    args = parser.parse_args()
    need(sha_text(args.config_sha256), "explicit ROOT config fingerprint required")
    with args.config.open("rb") as stream:
        payload = stream.read(2 * 1024 * 1024 + 1)
    need(len(payload) <= 2 * 1024 * 1024 and hashlib.sha256(payload).hexdigest() ==
         args.config_sha256, "config size/fingerprint mismatch")
    config = decode(payload)
    need(config["protocol"] == "WS116-report-config-v1" and config["root_analysis_approved"] is True and
         config["data_window_closed"] is True and config["analysis_scope"] == "initial60",
         "ROOT post-window analysis release absent")
    need(config["source_manifest_sha256"] == SOURCE_MANIFEST and
         config["schema_manifest_sha256"] == SCHEMA_MANIFEST and
         config["table_sha256"] == TABLE_SHA and config["basis_sha256"] == BASIS_SHA,
         "config source/table/basis differs")
    selected, excluded = config["initial_selection"], config["excluded_records"]
    historical = config["historical_rm84_inventory"]
    need(len(selected) + len(excluded) + len(historical) <= MAX_RECORDS, "finite record bound exceeded")
    files = Files([INPUTS, SCHEMA_INPUTS, *config["allowed_evidence_roots"]])
    pins = files.read(input_ref("source-identities.json", SOURCE_MANIFEST), as_json=True)
    for name, digest in pins["input_sha256"].items():
        files.read(input_ref(name, digest))
    schema_pins = files.read({"path": str(SCHEMA_INPUTS / "source-identities.json"),
                             "sha256": SCHEMA_MANIFEST}, as_json=True)
    for name, digest in schema_pins["source_sha256"].items():
        files.read({"path": str(SCHEMA_INPUTS / name), "sha256": digest})
    table = files.read(input_ref("admission-table.json", TABLE_SHA), as_json=True)
    basis = files.read(input_ref("qualified-method7-source-basis.json", BASIS_SHA), as_json=True)
    # UNADMITTED is immutable historical recipe status, not runtime permission.
    recipes = {row["attempt_id"]: row for row in table["initial_rows"]}
    need(len(recipes) == 60 and len({entry["attempt_id"] for entry in selected}) == len(selected),
         "initial recipe/selection cardinality mismatch")
    out = Path(config["output_root"]).resolve()
    need(not any(out.is_relative_to(root) for root in files.roots) and
         not any(out.is_relative_to(Path(root).resolve()) for root in config["protected_output_roots"]),
         "output would modify source/evidence/worktree")
    out.mkdir(parents=True, exist_ok=False)
    rows, failures, seen_processes = [], [], set()
    referenced_evidence_audit_valid = True
    for entry in selected:
        attempt = entry["attempt_id"]
        try:
            need(attempt in recipes, "attempt not an initial recipe")
            recipe = recipes[attempt]
            row = audit_initial(entry, recipe, table["conditions"][recipe["condition_id"]], basis, files)
            identity = row["process_identity"]
            process_key = (identity["boot_id"], identity["start_ticks"], identity["pid"])
            need(process_key not in seen_processes, "same process identity reused across selected rows")
            seen_processes.add(process_key)
            rows.append(row)
        except (KeyError, IndexError, TypeError, ValueError, ArithmeticError, OSError) as error:
            referenced_evidence_audit_valid = False
            failures.append({"attempt_id": attempt, "phase": "initial", "state": "excluded_audit_failure",
                             "error_type": type(error).__name__, "reason": str(error), "references": entry})
    present = {entry["attempt_id"] for entry in selected}
    missing = [row for key, row in recipes.items() if key not in present]
    for entry in excluded:
        record = audit_excluded(entry, files)
        referenced_evidence_audit_valid &= not record["evidence_errors"]
        failures.append(record)
    historical_records = []
    for entry in historical:
        need(entry["phase"] == "historical", "RM84 inventory must be historical")
        record = audit_excluded(entry, files)
        referenced_evidence_audit_valid &= not record["evidence_errors"]
        historical_records.append(record)
    groups = summarize(table, rows)
    pairs = full_summary_pairs(table, rows)
    report = {
        "protocol": "WS116-initial60-descriptive-v1", "config_sha256": args.config_sha256,
        "candidate": basis["candidate"], "material_hashes": basis["material_hashes"],
        "source_manifest_sha256": SOURCE_MANIFEST, "schema_manifest_sha256": SCHEMA_MANIFEST,
        "table_sha256": TABLE_SHA, "basis_sha256": BASIS_SHA,
        "missing_initial_recipes": missing, "groups": groups, "full_summary_pairs": pairs,
        "initial60_descriptive_complete": len(rows) == 60 and not missing and all(
            group["metrics"] is not None for group in groups) and all(
            pair["status"] == "common_values_match" for pair in pairs),
        "final_scientific_acceptance": False, "profiles_growth": "separate, excluded; no permission inferred",
        "referenced_evidence_audit_valid": referenced_evidence_audit_valid,
        "historical_rm84_inventory": historical_records,
        "scope": "kernel terminal/self snapshots distinct; exec retention UNKNOWN; no subtraction, "
                 "aggregate tree peak, isolated workflow allocation or measured contributor ranking",
    }
    report["analysis_success"] = (report["initial60_descriptive_complete"] and
                                  report["referenced_evidence_audit_valid"])
    report["status"] = ("descriptive_complete_audit_valid_pending_scientific_review" if report["analysis_success"]
                        else "descriptive_incomplete_or_reference_audit_failed")
    dump(out / "per-process.json", rows)
    dump(out / "excluded-records.json", failures)
    dump(out / "summary.json", report)
    dump(out / "file-audit.json", files.audit)
    with (out / "three-repeat-summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("condition_id", "status", "eligible_repetitions", *(
            key + "_" + stat for key in METRICS for stat in ("min", "median", "max"))))
        for group in groups:
            writer.writerow((group["condition_id"], group["status"], json.dumps(group["eligible_repetitions"]),
                             *(group["metrics"][key][stat] if group["metrics"] is not None else ""
                               for key in METRICS for stat in ("min", "median", "max"))))
    # Own output fingerprint list intentionally excludes its own bytes.
    output_hashes = {}
    for name in ("per-process.json", "excluded-records.json", "summary.json", "file-audit.json",
                 "three-repeat-summary.csv"):
        with (out / name).open("rb") as stream:
            output_hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    dump(out / "output-identities.json", output_hashes)
    return 0 if report["analysis_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
