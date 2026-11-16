"""Fixed file-only scalar collation of ROOT-closed global ordinals 1..78.
No public science, installed package or benchmark import; no observations or inference.
"""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
RAW_MANIFEST = HERE / "closed78-inputs.sha256"
ROSTER = HERE / "closed78-roster.tsv"
SCOPE = "CLOSED78_FILE_SCALARS_PENDING_WHOLE_SCI_NOT_RESULT_ACCEPTANCE"

def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result

def bad_constant(value):
    raise ValueError(f"nonfinite JSON literal {value}")

def parse(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=bad_constant)

def load(path):
    return parse(path.read_text())

def dump(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")

def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)

# This is an actual immutable-completion gate, never a live-progress trigger.
EVIDENCE = HERE.parent
FINAL_INDEX = EVIDENCE / "ROOT-final24-workflow-actual-1/ROOT-result-index.json"
completion_indexes = (
    (FINAL_INDEX, "all24_complete", list(range(55, 79))),
    (EVIDENCE / "ROOT-direct42-actual-1/ROOT-result-index.json", "all42_complete", list(range(13, 55))),
    (EVIDENCE / "ROOT-first-workflow-pair-actual-1/ROOT-result-index.json", "all_two_complete", [1, 2]),
    (EVIDENCE / "ROOT-next-ten-tiny-workflow-actual-1/ROOT-result-index.json", "all_ten_complete", list(range(3, 13))),
)
completion_pins = {}
for index_path, flag, ordinals in completion_indexes:
    index = load(index_path)
    if index.get(flag) is not True or sorted(row["ordinal"] for row in index["results"]) != ordinals:
        raise ValueError(f"immutable completion trigger not satisfied: {index_path}")
    if not all(row.get("terminal0_closed") is True for row in index["results"]):
        raise ValueError(f"failed/incomplete member in completion index: {index_path}")
    completion_pins[str(index_path)] = digest(index_path)

pins = {}
for line in RAW_MANIFEST.read_text().splitlines():
    expected, name = line.split("  ", 1)
    path = Path(name)
    if path in pins:
        raise ValueError(f"duplicate manifest member: {path}")
    if digest(path) != expected:
        raise ValueError(f"changed closed input: {path}")
    pins[path] = expected

def bound(root, name):
    path = root / name
    if path not in pins:
        raise ValueError(f"read outside closed manifest: {path}")
    return path

def sample_projection(path):
    count = 0
    valid = []
    gaps = []
    malformed = []
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            count += 1
            try:
                record = parse(line)
                if not isinstance(record, dict):
                    raise ValueError("sample is not JSON object")
            except (ValueError, TypeError) as error:
                malformed.append({"line": line_number, "error": str(error),
                                  "line_sha256": hashlib.sha256(line.encode()).hexdigest()})
                continue
            value = record.get("VmRSS_bytes")
            if number(value) and value >= 0:
                valid.append(value)
            else:
                gaps.append({"line": line_number, "value": value,
                             "key_present": "VmRSS_bytes" in record,
                             "monotonic_ns": record.get("monotonic_ns"),
                             "process_status_readable": record.get("process_status_readable"),
                             "field_errors": record.get("field_errors")})
    return {"line_count": count, "valid_rss_count": len(valid),
            "missing_or_invalid_rss_count": len(gaps), "malformed_json_count": len(malformed),
            "maximum_valid_VmRSS_bytes": max(valid) if valid else None,
            "gaps": gaps, "malformed": malformed,
            "scope": "discrete samples only; missing/invalid remain explicit, never zero or guaranteed peak"}

def payload(value):
    if not isinstance(value, dict):
        return None
    return {key: value.get(key) for key in (
        "array_payload_bytes", "unique_backings", "python_metadata_estimate_bytes", "metadata_limit")}

records = []
for line in ROSTER.read_text().splitlines():
    ordinal_s, route, role, attempt = line.split("\t")
    ordinal = int(ordinal_s)
    if not 1 <= ordinal <= 78:
        raise ValueError("not closed78 ordinal")
    base = Path("/workspace/work/campaign/evidence/118/resource-method-final-source-preparation/source")
    root = base / route / (f"raw-{role}" if route == "workflow" else "raw") / attempt
    receipt = load(bound(root, "receipt.json"))
    child = load(bound(root, "stdout.json"))
    spec = load(bound(root, "spec.json"))
    grant = load(bound(root, "grant.input"))
    terminal = receipt.get("terminal") or {}
    if receipt.get("status") != "complete_child_observed_pending_scientific_qualification" or terminal.get("returncode") != 0:
        raise ValueError(f"not complete terminal0 closed member: {attempt}")
    native = terminal["rusage_native"]["ru_maxrss"]
    if not number(native) or native < 0 or terminal.get("ru_maxrss_native_units") != "Linux KiB" or terminal.get("ru_maxrss_multiplier_to_bytes") != 1024:
        raise ValueError(f"unsupported native units: {attempt}")
    native_bytes = native * 1024
    if terminal.get("kernel_reported_direct_child_high_water_bytes") != native_bytes:
        raise ValueError(f"native-byte mismatch: {attempt}")
    samples = sample_projection(bound(root, "samples.jsonl"))
    if samples["line_count"] != receipt.get("sample_count"):
        raise ValueError(f"receipt/file sample count mismatch: {attempt}")
    if route == "direct":
        condition = child["case"]
        repetition = child["repetition"]
        if child["role"] != role:
            raise ValueError("direct role mismatch")
        mode, profile = "direct-full", False
        self_bytes = child["high_water_bytes"]
        self_native = child["ru_maxrss_native"]
        call_seconds = child["elapsed_target_seconds"]
        caller = payload(child.get("caller_payload"))
        result = payload(child.get("result_payload"))
        union = payload(child.get("union_payload"))
        fingerprints = child.get("public_fingerprints")
        child_context = {key: child.get(key) for key in ("provenance", "versions", "backend", "scipy_fft_default_workers", "context", "limits")}
        stages = None
    else:
        condition = spec["case"]
        repetition = spec["repetition"]
        mode, profile = spec["mode"], spec["profile"]
        self_bytes = {name: value.get("cumulative_high_water_bytes") for name, value in child["snapshots"].items()}
        self_native = {name: value.get("ru_maxrss_native") for name, value in child["snapshots"].items()}
        call_seconds = child["elapsed_call_seconds"]
        caller = payload(child.get("caller_retained"))
        result = payload(child.get("result_retained"))
        union = None  # Not emitted; do NOT fabricate by summing separate traversals.
        fingerprints = {key: child.get(key) for key in ("input_sha256", "common_output_sha256", "public_result_sha256", "output_hashes", "branches")}
        child_context = {key: child.get(key) for key in ("python", "numpy", "scipy", "numpy_backend", "scipy_fft_default_workers", "effective_worker_limits", "executable", "product_module", "context")}
        stages = child.get("stages")
    if not number(call_seconds) or call_seconds < 0:
        raise ValueError("invalid call time")
    for label, native_value in self_native.items():
        if not number(native_value) or self_bytes[label] != native_value * 1024:
            raise ValueError(f"self native-byte mismatch: {attempt}/{label}")
    start, finish = receipt.get("spawn_start_monotonic_ns"), receipt.get("finished_monotonic_ns")
    # Recorded finish precedes final hashes/postflight/receipt serialization.
    # It is not receipt completion (UNMEASURED) or target-call time.
    collection_seconds = (finish - start) / 1_000_000_000 if number(start) and number(finish) else None
    reaped = terminal.get("reaped_monotonic_ns")
    terminal_collection_seconds = (reaped - start) / 1_000_000_000 if number(start) and number(reaped) else None
    metrics = {"terminal_native_KiB": native, "terminal_direct_child_bytes": native_bytes,
               "target_or_workflow_call_seconds": call_seconds,
               "spawn_to_receipt_finished_seconds": collection_seconds,
               "spawn_to_terminal_collection_seconds": terminal_collection_seconds,
               "sampled_valid_RSS_max_bytes": samples["maximum_valid_VmRSS_bytes"]}
    for label, value in self_bytes.items():
        metrics[f"self_{label}_cumulative_bytes"] = value
    for label, value in (("caller", caller), ("result", result), ("union", union)):
        metrics[f"{label}_array_payload_bytes"] = value.get("array_payload_bytes") if value else None
    expected_head = "2cb73d7a8352d88a16477e5e802852b4948c62cd" if role == "parent" else "75fce7e1ea424127f1b875aaa395d8b3ea29ecaa"
    if receipt["candidate_before"]["head"] != expected_head or receipt.get("material_identity_matches") is not True:
        raise ValueError(f"actual scientific subject/material mismatch: {attempt}")
    records.append({"ordinal": ordinal, "route": route, "role": role, "condition": condition,
        "mode": mode, "profile": profile, "repetition": repetition, "attempt_id": attempt,
        "analysis_scope": SCOPE, "source_files": {name: {"path": str(bound(root, name)), "sha256": pins[bound(root, name)]}
            for name in ("receipt.json", "stdout.json", "samples.jsonl", "spec.json", "grant.input")},
        "metrics": metrics, "self_native_KiB": self_native, "payload": {"caller": caller, "result": result, "union": union,
            "union_scope": "direct emitted union" if route == "direct" else "NOT_EMITTED_UNKNOWN_NOT_SUMMED"},
        "samples": samples, "receipt_rss_terminal_confirmation": receipt.get("rss_terminal_confirmation"),
        "ownership": {key: receipt.get(key) for key in ("workload_pid", "observer_pid", "wait_ownership_lost", "wait_owner", "signals", "startup_parent_fds_closed", "startup_eof_observed", "nonterminal_wait_events", "postflight")},
        "terminal": terminal, "status": receipt["status"], "child_status": child.get("status"),
        "actual_source_identity": {key: receipt.get(key) for key in ("candidate_before", "candidate_after", "candidate_final", "material_identity_matches")},
        "runtime_context": child_context, "runtime_admission": {key: receipt.get(key) for key in ("resource_domain_admission", "limits", "interpreter", "effective_cwd", "child_environment_controls")},
        "grant_source_identity": {key: grant.get(key) for key in ("subject_root", "subject", "candidate", "candidate_identity", "head", "tree")},
        "fingerprints": fingerprints, "witness": child.get("witness"), "stages": stages})

if [record["ordinal"] for record in records] != list(range(1, 79)):
    raise ValueError("roster not exact ordered 1..78")
if len({record["attempt_id"] for record in records}) != 78:
    raise ValueError("duplicate attempt")
by_group = collections.defaultdict(list)
for record in records:
    key = tuple(record[name] for name in ("route", "condition", "mode", "profile", "role"))
    by_group[key].append(record)
summary = []
for key, members in sorted(by_group.items()):
    if sorted(row["repetition"] for row in members) != [1, 2, 3]:
        raise ValueError(f"not exact complete three-repeat group: {key}")
    for metric in sorted(set().union(*(row["metrics"] for row in members))):
        values = [row["metrics"].get(metric) for row in sorted(members, key=lambda row: row["repetition"])]
        valid = all(number(value) for value in values)
        summary.append(dict(zip(("route", "condition", "mode", "profile", "role"), key)) |
                       {"metric": metric, "raw_repetitions_1_2_3": values,
                        "min": min(values) if valid else None, "median": statistics.median(values) if valid else None,
                        "max": max(values) if valid else None,
                        "summary_status": "complete_three_numeric" if valid else "NOT_EMITTED_OR_MISSING_NO_STATISTIC",
                        "attempt_ids": [row["attempt_id"] for row in sorted(members, key=lambda row: row["repetition"])],
                        "scope": SCOPE})

if len(by_group) != 26:
    raise ValueError("not exactly 26 complete route/condition/mode/profile/role groups")
profile_controls = []
for row in records:
    if row["route"] != "workflow" or not row["profile"]:
        continue
    controls = [other for other in records if other["route"] == "workflow" and not other["profile"]
                and all(other[key] == row[key] for key in ("condition", "mode", "role", "repetition"))]
    if len(controls) != 1:
        raise ValueError(f"missing/ambiguous same-role profile control: {row['attempt_id']}")
    control = controls[0]
    profile_controls.append({"profile_attempt": row["attempt_id"], "unprofiled_attempt": control["attempt_id"],
        "profile_ordinal": row["ordinal"], "unprofiled_ordinal": control["ordinal"],
        "same_role_mode_condition_repetition": True, "adds_observations": 0,
        "input_common_public_branches_fingerprints_equal": row["fingerprints"] == control["fingerprints"],
        "profile_metrics": row["metrics"], "unprofiled_metrics": control["metrics"],
        "scope": "actual references; perturbation not isolated by ratio or subtraction"})
if len(profile_controls) != 12:
    raise ValueError("not exactly 12 profiled member references")
common_mode_controls = []
for row in records:
    if row["route"] != "workflow" or row["mode"] != "summary":
        continue
    controls = [other for other in records if other["route"] == "workflow" and other["mode"] == "full"
                and all(other[key] == row[key] for key in ("condition", "profile", "role", "repetition"))]
    if len(controls) != 1:
        raise ValueError(f"missing/ambiguous same-role full-mode reference: {row['attempt_id']}")
    full = controls[0]
    common_mode_controls.append({"summary_attempt": row["attempt_id"], "full_attempt": full["attempt_id"],
        "same_role_case_profile_repetition": True, "adds_observations": 0,
        "common_hash_equal": row["fingerprints"]["common_output_sha256"] == full["fingerprints"]["common_output_sha256"],
        "input_hash_equal": row["fingerprints"]["input_sha256"] == full["fingerprints"]["input_sha256"],
        "branches_equal": row["fingerprints"]["branches"] == full["fingerprints"]["branches"],
        "scope": "common values/branches only; distinct full and summary diagnostic graphs are not equated"})
if len(common_mode_controls) != 18:
    raise ValueError("not exactly 18 existing full/summary common reference pairs")
fingerprint_families = collections.defaultdict(list)
for row in records:
    fingerprint_families[(row["route"], row["condition"], row["mode"], row["profile"])].append(row)
fingerprint_checks = []
for key, members in sorted(fingerprint_families.items()):
    fingerprint_checks.append(dict(zip(("route", "condition", "mode", "profile"), key)) |
        {"attempt_ids": [row["attempt_id"] for row in members],
         "all_six_scientific_fingerprint_projections_equal": all(row["fingerprints"] == members[0]["fingerprints"] for row in members),
         "direct_caller_inputs_unchanged": all(row["fingerprints"].get("inputs") == row["fingerprints"].get("inputs_after") for row in members) if key[0] == "direct" else None,
         "scope": "hash/projection correspondence only, not literal whole-array byte comparison or independent accuracy oracle"})
stage_rows = []
for row in records:
    for event in row["stages"] or []:
        native_value = event["ru_maxrss_native_KiB"]
        if not number(native_value) or native_value < 0:
            raise ValueError("invalid native stage observation")
        stage_rows.append({"attempt_id": row["attempt_id"], "ordinal": row["ordinal"], "role": row["role"],
                           "mode": row["mode"], "profile": row["profile"], "repetition": row["repetition"],
                           **event, "cumulative_stage_high_water_bytes": native_value * 1024})

# Close every actually read raw identity again; no changed input may be silently pooled.
for path, expected in pins.items():
    if digest(path) != expected:
        raise ValueError(f"input changed during scalar collation: {path}")
for index_path, expected in completion_pins.items():
    if digest(Path(index_path)) != expected:
        raise ValueError(f"completion index changed: {index_path}")
if any(name == root or name.startswith(root + ".") for name in sys.modules for root in ("simrecon", "numpy", "scipy", "pytest")):
    raise ValueError("forbidden installed/scientific import")
dump("per-process.json", {"scope": SCOPE, "records": records})
dump("three-repeat-summary.json", {"scope": SCOPE, "groups": summary,
    "limits": "per-role exact condition/mode/profile complete3 only; no paired difference/ratio/pvalue/causal effect or isolated peak"})
dump("profile-control-references.json", {"scope": SCOPE, "references": profile_controls})
dump("shared-mode-common-correspondence.json", {"scope": SCOPE, "references": common_mode_controls})
dump("fingerprint-correspondence.json", {"scope": SCOPE, "checks": fingerprint_checks})
dump("stage-events.json", {"scope": SCOPE, "events": stage_rows,
     "limit": "cumulative associations only; not isolated stage allocation/workspace or unperturbed timing"})
with (HERE / "three-repeat-summary.csv").open("w", newline="") as stream:
    fields = list(summary[0])
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in summary:
        writer.writerow({key: json.dumps(value, allow_nan=False) if isinstance(value, (list, dict)) else value for key, value in row.items()})
metric_fields = sorted(set().union(*(row["metrics"] for row in records)))
with (HERE / "per-process.csv").open("w", newline="") as stream:
    fields = ["ordinal", "route", "condition", "mode", "profile", "role", "repetition", "attempt_id"] + metric_fields + ["sample_gap_count", "sample_malformed_count", "scope"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in records:
        writer.writerow({key: row[key] for key in fields[:8]} | row["metrics"] |
            {"sample_gap_count": row["samples"]["missing_or_invalid_rss_count"],
             "sample_malformed_count": row["samples"]["malformed_json_count"], "scope": SCOPE})
dump("run-metadata.json", {"scope": SCOPE, "python": sys.version, "executable": sys.executable,
    "isolated": sys.flags.isolated, "no_site": sys.flags.no_site, "dont_write_bytecode": sys.dont_write_bytecode,
    "statistics_path": statistics.__file__, "statistics_sha256": digest(Path(statistics.__file__)),
    "script_sha256": digest(Path(__file__)), "raw_manifest_sha256": digest(RAW_MANIFEST), "roster_sha256": digest(ROSTER),
    "record_count": len(records), "complete_condition_mode_profile_role_groups": len(by_group),
    "forbidden_imports_present": False, "input_stability": "all raw identities match before and after",
    "no_workflow_union": True, "no_scientific_calls_or_new_observation": True,
    "immutable_completion_indexes": completion_pins,
    "ownership": "file-only analysis process; creates no subprocess or numerical workload"})
print(json.dumps({"scope": SCOPE, "records": len(records), "groups": len(by_group), "status": "complete_file_scalar_collation"}))
