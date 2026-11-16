"""UNEXECUTED fixed WS116 stage file analysis; no measurement/launch authority.

Stdlib/file-only future aggregation of explicit immutable ROOT-selected records.
No measurement, launch, retry, discovery, plotting, product import or controller.
Requires a new ROOT analysis release AFTER the serial data window is closed.
Separate copy of a075 report cores, with explicit f6-control/8190-stage bindings.
Only seven literal stage recipes; original a075 and initial60 remain unchanged.
No code in this file has been run/imported/compiled/linted/tested.
"""

from __future__ import annotations

import argparse
import csv
import copy
import hashlib
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREPARATION = HERE.parent / "report-source-preparation"
INPUTS = PREPARATION / "inputs"
SCHEMA_INPUTS = PREPARATION / "schema-inputs"
ORIGINAL_SOURCE = PREPARATION / "aggregate_observations.py"
ORIGINAL_SHA = "a0758714c64798a39ded0b1beaf76f8dbbfc24c023d83cc8244172f106235dac"
STAGE_SOURCE = HERE.parent / "growth-profile-binder/source-final-coordinator-frozen/stage_batch_binder.py"
STAGE_SHA = "8190db99ef7fca49659e2979172a111f1c1f325eccef27c991caea06c1a2c4e9"
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


def stage_recipe(table, stage_id, selected):
    """Fixed8190 recipe copy with need/ValueError and strict size type; no import."""
    conditions = copy.deepcopy(table["conditions"])
    conditions.update({entry["condition"]["id"]: copy.deepcopy(entry)
                       for entry in table["growth_proposals"]})
    recipes = []
    if stage_id in ("growth192-summary", "growth256-summary"):
        need(selected is None, "summary growth does not select a largest size")
        size = 192 if stage_id == "growth192-summary" else 256
        for search in (False, True):
            label = "searched" if search else "supplied"
            recipes.append((f"growth{size}-summary-{label}", False, f"g{size}-summary-{label}"))
    elif stage_id in ("largest-full-supplied", "largest-full-searched"):
        need(type(selected) is int and selected in (192, 256), "selected largest full size required")
        label = "supplied" if stage_id == "largest-full-supplied" else "searched"
        recipes.append((f"growth{selected}-full-{label}", False, f"l{selected}-full-{label}"))
    elif stage_id in ("central64-profiles", "largest-profiles", "central-and-largest-profiles"):
        if stage_id == "central64-profiles":
            need(selected is None, "central-only profiles do not select a largest size")
        else:
            need(type(selected) is int and selected in (128, 192, 256), "selected largest profile size required")
        if stage_id != "largest-profiles":
            for mode in ("summary", "full"):
                recipes.append((f"central64-{mode}-searched", True, f"c64-{mode}-searched"))
        if stage_id != "central64-profiles":
            for mode in ("summary", "full"):
                cid = f"frozen128-{mode}-searched" if selected == 128 else f"growth{selected}-{mode}-searched"
                recipes.append((cid, True, f"l{selected}-{mode}-searched"))
    else:
        raise ValueError("unknown fixed stage")
    rows = []
    for cid, profile, suffix in recipes:
        if profile:
            proposal = conditions[cid]["operating_proposal"]
            proposal["deadline_seconds"] *= 2
            proposal["correspondence_maximum_age_seconds"] = proposal["deadline_seconds"] + 120
            proposal["disk_proposal_bytes"] = max(67108864, proposal["deadline_seconds"] * 100 * 8192 + 16777216)
        for repetition in (1, 2, 3):
            aid = f"ws116-gp-{suffix}-r{repetition}-{'p' if profile else 'u'}"
            need(len(aid) <= 64, "fixed nonce extent exceeds existing protocol")
            rows.append({"serial_index": len(rows) + 1, "stage_id": stage_id, "condition_id": cid,
                         "repetition": repetition, "profile": profile, "attempt_id": aid, "launch_nonce": aid})
    return rows, conditions
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


def audit_stage_context(cfg, boundary, table, files):
    """Audit actual8190 stage/admission/closed-history refs, without fresh PID checks."""
    rows, conditions = stage_recipe(table, cfg["stage_id"], cfg["selected_largest_size"])
    need(boundary["stage_id"] == cfg["stage_id"] and
         boundary["stage_admission"] == cfg["stage_admission"] and
         boundary["prior_stage_closures"] == cfg["prior_stage_closures"], "stage boundary linkage differs")
    need(boundary["row"] in rows, "row outside exact fixed stage")
    admission = files.read(cfg["stage_admission"], as_json=True)
    for key, expected in (("stage_id", cfg["stage_id"]), ("selected_largest_size", cfg["selected_largest_size"]),
                          ("candidate", cfg["candidate"]), ("material_hashes", cfg["material_hashes"]),
                          ("method7", cfg["accepted_method7"]), ("environment", cfg["environment"]),
                          ("prior_stage_closures", cfg["prior_stage_closures"]),
                          ("stage_rows", rows), ("table_sha256", TABLE_SHA)):
        need(admission[key] == expected, "actual stage admission differs: " + key)
    need(admission["prerequisites_accepted"] is True and admission["fresh_case_preflight_accepted"] is True,
         "stage prerequisites/preflight not accepted")
    need(admission["operating_proposals"] == {
        row["condition_id"]: conditions[row["condition_id"]]["operating_proposal"] for row in rows},
        "stage/profile operating recipe differs")
    need(0 < len(admission["prior_data_refs"]) <= 32, "prior JSON data refs missing/unbounded")
    for reference in admission["prior_data_refs"]:
        files.read(reference, as_json=True)  # Actual JSON-only binder path, never Markdown.
    if "descriptive_report_applicability_reference" in admission:
        files.read(admission["descriptive_report_applicability_reference"])  # Hash-only prose.
    closures = cfg["prior_stage_closures"]
    need(0 < len(closures) <= 8, "prior closure refs missing/unbounded")
    for reference in closures:
        closure = files.read(reference, as_json=True)
        need(closure["scope"] == "WS116_ROOT_closed_prior_stage" and closure["closed"] is True and
             closure["unresolved_owners"] == [] and closure["historical_identity_facts_retained"] is True,
             "prior stage closure incomplete")
        need(0 < len(closure["terminal_receipts"]) <= 128 and
             0 < len(closure["eligible_boundaries"]) <= 128, "prior closure inventory missing/unbounded")
        for receipt_ref in closure["terminal_receipts"]:
            record = files.read(receipt_ref, as_json=True)
            need(record["terminal"] is not None and record["wait_ownership_lost"] is False,
                 "prior stored terminal ownership incomplete")
        for boundary_ref in closure["eligible_boundaries"]:
            record = files.read(boundary_ref, as_json=True)
            need(record["status"] == "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW", "prior boundary ineligible")
        metadata = files.read(closure["last_post_metadata"], as_json=True)
        need(metadata["protocol"] == "WS116-fixed-ubuntu-metadata-v1" and
             0 < len(metadata["owned_processes"]) <= 128, "stored prior identity metadata missing/unbounded")
        for item in metadata["owned_processes"]:
            expected = item["expected"]
            need(type(expected["pid"]) is int and expected["pid"] > 1 and
                 type(expected["start_ticks"]) is int and expected["start_ticks"] > 0 and
                 isinstance(expected["boot_id"], str) and expected["boot_id"].strip() and
                 isinstance(expected["fds"], list) and all(nonnegative(fd) for fd in expected["fds"]) and
                 item["identity_state"] == "absent" and
                 set(item["fds"]) == {str(fd) for fd in expected["fds"]} and
                 all(value["state"] == "absent" for value in item["fds"].values()),
                 "stored prior identity/FD coverage incomplete")
    needed = {row["attempt_id"] for row in rows if row["profile"] or
              conditions[row["condition_id"]]["condition"]["mode"] == "full"}
    need(set(cfg["matched_unprofiled"]) == needed, "exact stage matched-control refs missing/extra")
    growth_conditions = list({row["condition_id"]: conditions[row["condition_id"]]["condition"]
                              for row in rows if row["condition_id"].startswith("growth")}.values())
    need(cfg["grant_fixed"]["declared_growth_conditions"] == growth_conditions,
         "actual declared growth conditions differ")
    expected_core = {}
    for name, condition in conditions.items():
        expected = condition["expected_output"]
        expected_core[name] = {key: {"shape": expected[key]["shape"], "dtype": "<f8"}
                              for key in ("image", "x_um", "y_um", "z_um", "carriers_cyc_um")}
        for key in ("modulation", "raw_modulation"):
            expected_core[name][key] = {"shape": expected["modulation_and_raw"]["shape"], "dtype": "<c16"}
    need(cfg["expected_core"] == expected_core, "actual28-condition core differs")
    allowed = cfg["allowed_attempt_ids"]
    indices = [next((i for i, row in enumerate(rows) if row["attempt_id"] == name), -1) for name in allowed]
    need(indices and len(allowed) == len(set(allowed)) and -1 not in indices and
         indices == list(range(indices[0], indices[0] + len(indices))) and
         (indices[0] > 0 or indices == [0]) and len(cfg["prior_eligible"]) == indices[0] and
         (indices[0] == 0 or cfg["continuation_authorized"] is True), "actual stage release/prefix differs")
    for prior_ref, row in zip(cfg["prior_eligible"], rows, strict=False):
        record = files.read(prior_ref, as_json=True)
        need(record["row"] == row and record["stage_id"] == cfg["stage_id"] and
             record["candidate"] == cfg["candidate"] and record["material_hashes"] == cfg["material_hashes"] and
             record["stage_admission"] == cfg["stage_admission"] and
             record["prior_stage_closures"] == closures and record["source_sha256"] == STAGE_SHA and
             record["status"] == "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW", "prior prefix linkage differs")


def boundary_for(entry, files, basis, recipe, table):
    """Read the actual eligible boundary and its actual authorized batch config."""
    boundary = files.read(entry["boundary"], as_json=True)
    cfg = files.read(entry["batch_config"], as_json=True)
    need(boundary["status"] == "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW" and
         boundary["row"] == recipe, "actual boundary status/row differs")
    need(boundary["candidate"] == basis["candidate"] and
         boundary["material_hashes"] == basis["material_hashes"], "boundary basis/material mismatch")
    need(boundary["table_sha256"] == TABLE_SHA and
         boundary["config_sha256"] == entry["batch_config"]["sha256"] and
         boundary["source_sha256"] == cfg["binder_sha256"] and
         cfg["binder_sha256"] == (BINDER_SHA if entry["phase"] == "initial" else STAGE_SHA),
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
    is_stage = cfg["binder_sha256"] == STAGE_SHA
    need(ledger["scope"] == ("WS116_current_stage_scientific_observer_workload_processes" if is_stage else
                             "WS116_scientific_observer_workload_processes") and
         ledger["unresolved"] == [] and
         ledger["root_authority_sha256"] == cfg["root_authority"]["sha256"], "owned ledger unresolved")
    if is_stage:
        audit_stage_context(cfg, boundary, table, files)
        need(ledger["stage_id"] == cfg["stage_id"], "CURRENT-STAGE ledger mismatch")
        rows, _ = stage_recipe(table, cfg["stage_id"], cfg["selected_largest_size"])
        stage_ids = {row["attempt_id"] for row in rows}
        need(len(ledger["closed_owned_processes"]) <= 2 * len(rows), "current-stage ledger unbounded")
        for item in ledger["closed_owned_processes"]:
            record = files.read(item["receipt"], as_json=True)
            need(item["attempt_id"] in stage_ids and record["launch"]["nonce"] == item["attempt_id"] and
                 record["terminal"] is not None and record["wait_ownership_lost"] is False and
                 item["identity"]["pid"] in (record["observer_pid"], record["workload_pid"]),
                 "current-stage ledger receipt scope differs")
        ack = cfg["scheduler_ack_expected"]
        need(ack["stage_id"] == cfg["stage_id"] and ack["unresolved_owners"] == [] and
             ack["prior_stage_closures"] == cfg["prior_stage_closures"] and ack["window"] == cfg["window"] and
             ack["campaign_work_suspended"] is True and ack["known_active_numerical_processes"] == [] and
             ack["outside_campaign_actors"] == "unknown_not_scanned", "actual stage scheduler scope differs")
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
         intent["source_sha256"] == cfg["binder_sha256"] and
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
    return {"batch_config": entry["batch_config"], "source_sha256": cfg["binder_sha256"],
        "method7": boundary["method7"], "root_authority": cfg["root_authority"],
        "support": refs, "runner_invocation_unix_ns": invocation,
        "recorded_proof_age_at_invocation_seconds": age_ns / 1e9,
        "recorded_captures": proof_records, "original_proof_maximum_age_seconds": original["maximum_age_seconds"],
        "binder_end_validation_scope": boundary["end_validation_scope"],
        "exact_binder_final_horizon_check_unix_ns": None,
        "stage_id": cfg.get("stage_id"), "stage_admission": cfg.get("stage_admission"),
        "prior_stage_closures": cfg.get("prior_stage_closures", []),
        "end_audit_limit": "actual pinned binder boundary asserts final horizon/window check; exact check time not exported; no analysis-wall freshness or new host observation"}


def audit_record(entry, recipe, plan, basis, files, table):
    """Reuse a075 row audit with explicit initial-control/stage and profile bindings."""
    need(entry["phase"] in {"initial", "stage"} and entry["attempt_id"] == recipe["attempt_id"],
         "wrong selected row")
    boundary, cfg, refs = boundary_for(entry, files, basis, recipe, table)
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
    need(receipt["child_outcome"] == "finite_observation_pending_qualification" and
         receipt["signals"] == [] and receipt["nonterminal_wait_events"] == [] and
         type(receipt["startup_eof_observed"]) is bool, "runner lifecycle/complete verdict differs")
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
    need(cfg["receipt_protocol"] == "WS116-attempt-v3" and cfg["child_protocol"] == "WS116-child-v2",
         "configured accepted protocols differ")
    if cfg["binder_sha256"] == STAGE_SHA:
        need(all(grant[key] == value for key, value in cfg["grant_fixed"].items()),
             "actual stage fixed grant differs")
        if recipe["condition_id"].startswith("growth"):
            need(grant["growth_separate_admission"] is True and grant["smaller_measured_evidence"] == {
                "root_stage_admission": cfg["stage_admission"], "prior_stage_closures": cfg["prior_stage_closures"]},
                "actual growth grant prerequisite binding differs")
    for key in ("condition_id", "repetition", "profile"):
        need(grant[key] == recipe[key], "grant row differs")
    condition = plan["condition"]
    need({key: spec[key] for key in condition} == condition and
         spec["repetition"] == recipe["repetition"] and type(spec["profile"]) is bool and
         spec["profile"] == recipe["profile"], "spec not the exact condition/profile")
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
    need(child["branches"] == plan["expected_output"]["branches"] and
         isinstance(child["stages"], list) and (bool(child["stages"]) if recipe["profile"] else not child["stages"]),
         "branch/profile presence mismatch")
    # Existing qualified runner owns complete stage scalar/order/pair/time validation.
    # Preserve actual event objects; do not add a second scientific stage parser.
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
        "repetition": recipe["repetition"], "profile": recipe["profile"], "phase": entry["phase"],
        "stage_id": cfg.get("stage_id"), "condition": condition,
        "state": "eligible_descriptive_pending_scientific_review",
        "boundary_sha256": entry["boundary"]["sha256"], "receipt_sha256": refs["receipt.json"]["sha256"],
        "raw_files": boundary["raw_files"], "operational_audit": operational, "process_identity": identity,
        "references": entry, "source_sha256": cfg["binder_sha256"],
        "environment_binding": cfg["environment"], "environment_expected": cfg["environment_expected"],
        "method7_reference": cfg["accepted_method7"],
        "matched_unprofiled": cfg.get("matched_unprofiled", {}).get(recipe["attempt_id"]),
        "stages": child["stages"], "startup_eof_observed": receipt["startup_eof_observed"],
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


def audit_selection(entry, table, basis, files):
    """Locate only an exact initial-control or literal8190 recipe, never invent rows."""
    if entry["phase"] == "initial":
        rows, conditions = table["initial_rows"], table["conditions"]
    else:
        need(entry["phase"] == "stage", "unsupported record phase")
        cfg = files.read(entry["batch_config"], as_json=True)
        rows, conditions = stage_recipe(table, cfg["stage_id"], cfg["selected_largest_size"])
    recipe = next((row for row in rows if row["attempt_id"] == entry["attempt_id"]), None)
    need(recipe is not None, "attempt not an exact recipe")
    return audit_record(entry, recipe, conditions[recipe["condition_id"]], basis, files, table)


def reference_key(boundary, config):
    """Match actual bound references by path AND bytes; no projected control data."""
    return (boundary["path"], boundary["sha256"], config["path"], config["sha256"])


def matched_controls(rows, controls):
    """Audit same-repeat exact controls; retain metrics separately, no ratios/subtraction."""
    by_reference = {}
    for control in controls:
        refs = control["references"]
        key = reference_key(refs["boundary"], refs["batch_config"])
        need(key not in by_reference, "duplicate audited control reference")
        need(control["profile"] is False, "control must be unprofiled")
        by_reference[key] = control
    pairs, errors, used = [], [], set()
    for row in rows:
        if not row["profile"] and row["condition"]["mode"] != "full":
            need(row["matched_unprofiled"] is None, "unprofiled summary has unexpected control")
            continue
        try:
            pair = row["matched_unprofiled"]
            key = reference_key(pair["boundary"], pair["config"])
            anchor = by_reference[key]
            left, right = row["condition"], anchor["condition"]
            need(row["repetition"] == anchor["repetition"] and
                 all(left.get(name) == right.get(name) for name in ("shape", "case", "search")) and
                 right["mode"] == (left["mode"] if row["profile"] else "summary"),
                 "paired mode/geometry/case/search/repetition differs")
            for name in ("environment", "environment_binding", "environment_expected", "method7_reference",
                         "input_sha256", "input_arrays", "output_hashes", "common_output_sha256", "branches"):
                need(row[name] == anchor[name], "paired core/source environment differs: " + name)
            if row["profile"]:
                need(row["public_result_sha256"] == anchor["public_result_sha256"],
                     "profile changed its same-mode public graph")
            used.add(key)
            pairs.append({"attempt_id": row["attempt_id"], "control_attempt_id": anchor["attempt_id"],
                "repetition": row["repetition"], "kind": "profile_same_mode" if row["profile"] else "full_summary_common",
                "status": "matched", "profile": row["profile"],
                "observed_metrics": row["metrics"], "unprofiled_control_metrics": anchor["metrics"],
                "control_refs": pair, "profile_events": row["stages"] if row["profile"] else [],
                "limits": "raw scoped metrics kept separate; no perturbation ratio, allocation difference or benefit"})
        except (KeyError, IndexError, TypeError, ValueError, ArithmeticError) as error:
            errors.append({"attempt_id": row["attempt_id"], "state": "matched_control_audit_failure",
                           "error_type": type(error).__name__, "reason": str(error)})
    if used != set(by_reference):
        errors.append({"state": "unused_or_mismatched_control_selection", "references": [
            list(key) for key in set(by_reference) - used]})
    return pairs, errors


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
    need(config["protocol"] == "WS116-fixed-stage-report-v1" and config["root_analysis_approved"] is True and
         config["data_window_closed"] is True and config["analysis_scope"] == "one_fixed_stage",
         "ROOT post-window analysis release absent")
    need(config["source_manifest_sha256"] == SOURCE_MANIFEST and
         config["schema_manifest_sha256"] == SCHEMA_MANIFEST and
         config["original_extractor_sha256"] == ORIGINAL_SHA and config["stage_binder_sha256"] == STAGE_SHA and
         config["table_sha256"] == TABLE_SHA and config["basis_sha256"] == BASIS_SHA,
         "config source/table/basis differs")
    selected, control_selection, excluded = config["stage_selection"], config["control_selection"], config["excluded_records"]
    historical = config["historical_rm84_inventory"]
    need(len(selected) <= 12 and len(control_selection) <= 12 and
         len(selected) + len(control_selection) + len(excluded) + len(historical) <= MAX_RECORDS,
         "finite stage/control/record bound exceeded")
    files = Files([INPUTS, SCHEMA_INPUTS, ORIGINAL_SOURCE.parent, STAGE_SOURCE.parent,
                   *config["allowed_evidence_roots"]])
    files.read({"path": str(ORIGINAL_SOURCE), "sha256": ORIGINAL_SHA})
    files.read({"path": str(STAGE_SOURCE), "sha256": STAGE_SHA})
    pins = files.read(input_ref("source-identities.json", SOURCE_MANIFEST), as_json=True)
    for name, digest in pins["input_sha256"].items():
        files.read(input_ref(name, digest))
    schema_pins = files.read({"path": str(SCHEMA_INPUTS / "source-identities.json"),
                             "sha256": SCHEMA_MANIFEST}, as_json=True)
    for name, digest in schema_pins["source_sha256"].items():
        files.read({"path": str(SCHEMA_INPUTS / name), "sha256": digest})
    table = files.read(input_ref("admission-table.json", TABLE_SHA), as_json=True)
    basis = files.read(input_ref("qualified-method7-source-basis.json", BASIS_SHA), as_json=True)
    # Initial60 remains a separate dataset. Source table status is not runtime authority.
    stage_rows, conditions = stage_recipe(table, config["stage_id"], config["selected_largest_size"])
    recipes = {row["attempt_id"]: row for row in stage_rows}
    need(len({entry["attempt_id"] for entry in selected}) == len(selected) and
         all(entry["phase"] == "stage" and entry["attempt_id"] in recipes for entry in selected),
         "stage selection duplicate/outside recipe")
    need(type(config["allow_partial_selection"]) is bool and
         (len(selected) == len(recipes) or config["allow_partial_selection"] is True),
         "partial data requires explicit ROOT analysis selection")
    out = Path(config["output_root"]).resolve()
    need(not any(out.is_relative_to(root) for root in files.roots) and
         not any(out.is_relative_to(Path(root).resolve()) for root in config["protected_output_roots"]),
         "output would modify source/evidence/worktree")
    out.mkdir(parents=True, exist_ok=False)
    rows, controls, failures, seen_processes = [], [], [], set()
    referenced_evidence_audit_valid = True
    for selection, destination, role in ((selected, rows, "stage"), (control_selection, controls, "unprofiled_control")):
        for entry in selection:
            attempt = entry["attempt_id"]
            try:
                row = audit_selection(entry, table, basis, files)
                if role == "stage":
                    need(row["stage_id"] == config["stage_id"] and
                         row["profile"] == recipes[attempt]["profile"] and
                         row["condition"] == conditions[recipes[attempt]["condition_id"]]["condition"],
                         "analysis row not this exact stage/profile/condition")
                    actual_cfg = files.read(entry["batch_config"], as_json=True)
                    need(actual_cfg["selected_largest_size"] == config["selected_largest_size"],
                         "analysis selected largest differs from actual config")
                else:
                    need(row["profile"] is False, "analysis control is profiled")
                identity = row["process_identity"]
                process_key = (identity["boot_id"], identity["start_ticks"], identity["pid"])
                need(process_key not in seen_processes, "same process identity reused across selected/control rows")
                seen_processes.add(process_key)
                destination.append(row)
            except (KeyError, IndexError, TypeError, ValueError, ArithmeticError, OSError) as error:
                referenced_evidence_audit_valid = False
                failures.append({"attempt_id": attempt, "phase": entry.get("phase"), "role": role,
                                 "state": "excluded_audit_failure", "error_type": type(error).__name__,
                                 "reason": str(error), "references": entry})
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
    active_conditions = {row["condition_id"]: conditions[row["condition_id"]] for row in stage_rows}
    groups = summarize({"conditions": active_conditions}, rows)
    pairs = full_summary_pairs({"conditions": active_conditions}, rows)
    control_pairs, pair_errors = matched_controls(rows, controls)
    if pair_errors:
        referenced_evidence_audit_valid = False
        failures.extend(pair_errors)
    report = {
        "protocol": "WS116-fixed-stage-descriptive-v1", "config_sha256": args.config_sha256,
        "stage_id": config["stage_id"], "selected_largest_size": config["selected_largest_size"],
        "expected_stage_rows": stage_rows, "partial_selection_authorized": config["allow_partial_selection"],
        "candidate": basis["candidate"], "material_hashes": basis["material_hashes"],
        "source_manifest_sha256": SOURCE_MANIFEST, "schema_manifest_sha256": SCHEMA_MANIFEST,
        "original_extractor_sha256": ORIGINAL_SHA, "stage_binder_sha256": STAGE_SHA,
        "table_sha256": TABLE_SHA, "basis_sha256": BASIS_SHA,
        "missing_stage_recipes": missing, "groups": groups, "full_summary_pairs": pairs,
        "matched_control_pairs": control_pairs,
        "fixed_stage_descriptive_complete": len(rows) == len(recipes) and not missing and all(
            group["metrics"] is not None for group in groups) and all(
            pair["status"] == "common_values_match" for pair in pairs) and not pair_errors,
        "final_scientific_acceptance": False,
        "initial60_scope": "original f6 dataset unchanged; only explicit exact controls reread here, never counted as new stage repetitions",
        "referenced_evidence_audit_valid": referenced_evidence_audit_valid,
        "historical_rm84_inventory": historical_records,
        "scope": "kernel terminal/self snapshots distinct; exec retention UNKNOWN; no subtraction, "
                 "aggregate tree peak, isolated workflow allocation or measured contributor ranking",
    }
    report["analysis_success"] = (report["fixed_stage_descriptive_complete"] and
                                  report["referenced_evidence_audit_valid"])
    report["status"] = ("descriptive_complete_audit_valid_pending_scientific_review" if report["analysis_success"]
                        else "descriptive_incomplete_or_reference_audit_failed")
    dump(out / "per-process.json", rows)
    dump(out / "unprofiled-controls.json", controls)
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
    for name in ("per-process.json", "unprofiled-controls.json", "excluded-records.json", "summary.json", "file-audit.json",
                 "three-repeat-summary.csv"):
        with (out / name).open("rb") as stream:
            output_hashes[name] = hashlib.file_digest(stream, "sha256").hexdigest()
    dump(out / "output-identities.json", output_hashes)
    return 0 if report["analysis_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
