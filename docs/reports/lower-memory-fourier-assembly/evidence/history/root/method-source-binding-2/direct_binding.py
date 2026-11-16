"""FA120 fixed 27-row SOURCE binding; never an execution grant.

The copied current118 runner owns launch/wait/guards/RSS/status unchanged.
No numerical content loader, monitor, reaper, registry or scientific fixture.
The frozen d2d6 child has no CLI: math-interface-proposal/ is a separate,
unapplied amendment for its owner. Actual amended child identity is UNBOUND.
"""

# ROOT source binding: execution still requires independent review and exact-case grant.

import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONDITIONS = ("Ksmall", "Kmedium", "K2D")
VARIANT_ORDER = {
    1: ("baseline", "candidate", "retained-control"),
    2: ("candidate", "retained-control", "baseline"),
    3: ("retained-control", "baseline", "candidate"),
}
CASE_IDS = tuple(
    condition + "-r" + str(repetition) + "-" + variant
    for condition in CONDITIONS
    for repetition in (1, 2, 3)
    for variant in VARIANT_ORDER[repetition]
)
METHOD_FILES = ("observer.py", "run_direct_attempt.py", "direct_binding.py", "manifest.json")
FIXTURE_FILES = ("filtered.npy", "carriers.npy", "x_um.npy", "y_um.npy", "grid.json")
FIXTURE = "tests/reconstruction_summary_fixture.py"
DIAGNOSTICS = (
    "scripts/source_free_check.py",
    "scripts/source_free_sitecustomize/sitecustomize.py",
    "scripts/source_free_sitecustomize/pytest_plugin.py",
)
ROW_CONFIG_KEYS = {
    "condition", "variant", "repetition", "actual119_parent", "candidate",
    "environment", "grant", "fixture_root", "fixture_file_hashes", "output_image_path",
}
PAYLOAD_KEYS = {
    "status", "condition", "variant", "repetition", "pid", "ppid",
    "actual119_parent", "candidate", "environment", "grant", "fixture_directory",
    "fixture_file_hashes", "fixture_loading_started_ns", "fixture_loading_ended_ns",
    "fixture_loading_seconds", "input_identities_before", "input_identities_after",
    "output_identity", "output_complete_little_endian_bytes_path", "output_shape",
    "output_dtype", "output_strides", "output_owns_data", "output_writeable",
    "native_high_water_units", "native_high_water_multiplier_to_bytes",
    "pre_call_high_water_native", "call_end_high_water_native",
    "post_observation_high_water_native", "pre_call_snapshot_ns", "kernel_started_ns",
    "kernel_ended_ns", "call_end_snapshot_ns", "post_observation_snapshot_ns",
    "kernel_seconds", "terminal_direct_child_usage", "sampled_current_rss", "limits",
}


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            value.update(chunk)
    return value.hexdigest()


def manifest():
    return json.loads((HERE / "manifest.json").read_text())


def material_hashes(root):
    """Closed product/method/math/config/five-file/provenance paths only."""
    root = Path(root).resolve()
    frozen = manifest()
    paths = frozen["subject_material_paths"]
    if not isinstance(paths, list) or not paths or paths != sorted(set(paths)):
        raise ValueError("final explicit sorted subject material closure is unbound")
    required = {FIXTURE, "uv.lock", *DIAGNOSTICS}
    if not required.issubset(paths) or not any(p.startswith("src/simrecon/") for p in paths):
        raise ValueError("FA120 subject/diagnostic/product closure incomplete")
    result = {}
    for name in paths:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not (root / path).resolve().is_relative_to(root):
            raise ValueError("subject material escapes selected worktree")
        result["subject:" + name] = digest(root / path)
    for name in METHOD_FILES:
        result["method:" + name] = digest(HERE / name)
    # Explicit math files; no mutable sibling import or command registry.
    for name in ("child", "writer", "witnesses", "closed_manifest"):
        entry = frozen["math_materials"][name]
        if digest(entry["path"]) != entry["sha256"]:
            raise ValueError("changed bound math material: " + name)
        result["math:" + name] = entry["sha256"]
    for condition in CONDITIONS:
        fixture = frozen["fixtures"][condition]
        if set(fixture["files"]) != set(FIXTURE_FILES):
            raise ValueError("exactly five measured fixture files required")
        for name in FIXTURE_FILES:
            path = Path(fixture["directory"]) / name
            value = digest(path)
            if value != fixture["files"][name]:
                raise ValueError("changed qualified five-file fixture")
            result["fixture:" + condition + ":" + name] = value
        for name in ("public_image", "provenance"):
            entry = fixture[name]
            value = digest(entry["path"])
            if value != entry["sha256"]:
                raise ValueError("changed separate public reference/provenance")
            result["reference:" + condition + ":" + name] = value
    for row in frozen["initial_conditions"]:
        entry = row["config"]
        value = digest(entry["path"])
        if value != entry["sha256"]:
            raise ValueError("changed fixed row config")
        result["config:" + row["id"]] = value
    return result


def check_release(grant, root):
    """Future ROOT bindings only; current source unconditionally holds above."""
    frozen = manifest()
    if frozen["approved"] is not True or frozen["execution_status"] != "released_exact_case":
        raise ValueError("FA120 SOURCE ONLY / HOLD")
    if frozen["numerical_release"] is not True or grant.get("approved") is not True:
        raise ValueError("no FA120 numerical/exact-case approval")
    if grant.get("protocol") != "FA120-direct-grant-v1" or grant["window"] != "W120":
        raise ValueError("FA120 exact grant and literal W120 required")
    if grant["window"] != frozen["planned_window"]:
        raise ValueError("planned exclusive window differs")
    timeout = frozen["launch"]["startup_timeout_seconds"]
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("final positive startup bound remains unbound")
    subject = grant["subject"]
    selected = frozen["subject"]
    if str(root) != selected["root"] or root.resolve() != root:
        raise ValueError("actual119-integrated120 root differs")
    if grant["candidate"] != selected["identity"]:
        raise ValueError("actual120 candidate head/tree/patch differs")
    if subject["actual119_parent"] != frozen["actual119_parent"]:
        raise ValueError("actual119 parent differs")
    for key in (
        "actual119_reconciliation", "affected118_scientific_disposition",
        "fresh_method_source_review", "fresh_scientific_source_review",
        "finite_method_qualification", "public_fixture_qualification",
        "diagnostic_route_qualification", "metadata_git_abort_ownership",
        "exclusive_window", "environment_binding", "individual_admission",
    ):
        proof = grant["proofs"][key]
        if not isinstance(proof, dict) or set(proof) != {"path", "sha256"}:
            raise ValueError("unbound reviewed proof: " + key)
        if not re.fullmatch(r"[0-9a-f]{64}", proof["sha256"]) or digest(proof["path"]) != proof["sha256"]:
            raise ValueError("changed reviewed proof: " + key)
    if subject["worktree"] != str(root) or subject["python"] != sys.executable:
        raise ValueError("literal root/interpreter differs")
    if subject["python"] != selected["python"] or subject["module_root"] != str(root / "src/simrecon"):
        raise ValueError("fixed selected product origin differs")
    if subject["dirty"] is not False or subject["module_root"] != selected["module_root"]:
        raise ValueError("actual clean product/material binding required")
    if (subject["revision"], subject["tree"]) != (grant["candidate"]["head"], grant["candidate"]["tree"]):
        raise ValueError("target and observer subject identities differ")
    if tuple(row["id"] for row in frozen["initial_conditions"]) != CASE_IDS:
        raise ValueError("exact 27 IDs/rotated order changed")
    rows = frozen["initial_conditions"]
    if len({row["output_image_path"] for row in rows}) != 27 or len({row["config"]["path"] for row in rows}) != 27:
        raise ValueError("27 distinct ROOT-bound output/config paths required")
    if not Path(frozen["attempt_output_root"]).is_absolute():
        raise ValueError("actual attempt output root remains unbound")
    if any(key in grant for key in ("declared_growth_conditions", "growth_separate_admission")):
        raise ValueError("growth dispatch absent")
    row = next(row for row in frozen["initial_conditions"] if row["id"] == grant["condition_id"])
    if grant["profile"] is not False or type(grant["repetition"]) is not int or grant["repetition"] != row["repetition"]:
        raise ValueError("one fixed unprofiled row/repetition required")
    config_entry = row["config"]
    if grant["row_config"] != config_entry or digest(config_entry["path"]) != config_entry["sha256"]:
        raise ValueError("exact future mathowner row config differs")
    with Path(config_entry["path"]).open("rb") as stream:
        config = json.load(stream, object_pairs_hook=_object, parse_constant=_constant)
    _finite_json(config)
    if set(config) != ROW_CONFIG_KEYS:
        raise ValueError("fixed FA120 config fields differ")
    if type(config["repetition"]) is not int or (config["condition"], config["variant"], config["repetition"]) != (row["condition"], row["variant"], row["repetition"]):
        raise ValueError("fixed config row differs")
    fixture = frozen["fixtures"][row["condition"]]
    if str(Path(config["fixture_root"]) / row["condition"]) != fixture["directory"]:
        raise ValueError("qualified condition fixture directory differs")
    if config["fixture_file_hashes"] != fixture["files"]:
        raise ValueError("qualified five-file identities differ")
    if config["output_image_path"] != row["output_image_path"]:
        raise ValueError("unique complete raw output artifact path differs")
    expected_image = Path(frozen["attempt_output_root"]) / grant["attempt_id"] / "output-image.le.bin"
    if Path(config["output_image_path"]) != expected_image:
        raise ValueError("raw output image must share this exact attempt evidence directory")
    for key in ("actual119_parent", "candidate", "environment", "grant"):
        if config[key] != subject["expected_child_fields"][key]:
            raise ValueError("fixed child provenance differs: " + key)
    if config["actual119_parent"] != frozen["actual119_parent"] or config["candidate"] != grant["candidate"]:
        raise ValueError("config parent/candidate provenance differs")
    if config["grant"] != grant["grant_id"]:
        raise ValueError("noncircular ROOT grant ID differs; receipt separately hashes grant bytes")
    if Path(config["output_image_path"]).exists():
        raise ValueError("unique output image path already exists")
    if material_hashes(root) != grant["material_hashes"]:
        raise ValueError("closed FA120 subject/method/fixture material differs")
    # Preserve current118 diagnostic prepend/inheritance; no -I/-S/-E route.
    diagnostic = str(root / "scripts/source_free_sitecustomize")
    inherited = subject["diagnostic_environment"]
    previous_path = inherited["inherited_pythonpath"]
    previous_plugins = inherited["inherited_pytest_plugins"]
    if any(value is not None and not isinstance(value, str) for value in (previous_path, previous_plugins)):
        raise ValueError("explicit frozen inherited diagnostic environment required")
    expected_path = diagnostic + (os.pathsep + previous_path if previous_path else "")
    expected_plugins = "pytest_plugin" + ("," + previous_plugins if previous_plugins else "")
    if inherited["PYTHONPATH"] != expected_path or inherited["PYTEST_PLUGINS"] != expected_plugins:
        raise ValueError("diagnostic prepend/inheritance differs")
    if os.environ.get("PYTHONPATH") != expected_path or os.environ.get("PYTEST_PLUGINS") != expected_plugins:
        raise ValueError("actual startup diagnostic path/plugin differs")


def target_argv(grant, spec, root):
    """Exactly one future amended child CLI; current d2d6 cannot accept it."""
    return [sys.executable, manifest()["math_materials"]["child"]["path"], "--fa120-config", spec["config"]["path"]]


def prepare_spec(grant, spec):
    """External correspondence/provenance, never injected scientific values."""
    spec["direct_subject"] = grant["subject"]
    spec["expected_material_hashes"] = grant["material_hashes"]
    spec["expected_observer_pid"] = os.getpid()
    spec["fixture_binding"] = manifest()["fixtures"][spec["condition"]]
    return spec


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("nonfinite JSON constant")


def _finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite JSON numeric value")
    if isinstance(value, dict):
        for item in value.values():
            _finite_json(item)
    elif isinstance(value, list):
        for item in value:
            _finite_json(item)


def validate_complete_record(record, pid, spec):
    """Fixed math payload metadata only; never parse NPY/image content here."""
    def require(ok, name):
        if not ok:
            raise ValueError("incomplete FA120 observation: " + name)

    def integer(value):
        return type(value) is int and value >= 0

    def number(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    def array_identity(value, name):
        # reconstruction_summary_fixture.identity's tuple becomes a JSON LIST:
        # [name, [shape...], canonical dtype.str, canonical complete-byte SHA256].
        dtype = "<c16" if name == "filtered" else "<f8"
        return (
            isinstance(value, list) and len(value) == 4 and value[0] == name
            and isinstance(value[1], list)
            and all(type(size) is int and size >= 0 for size in value[1])
            and value[2] == dtype and isinstance(value[3], str)
            and re.fullmatch(r"[0-9a-f]{64}", value[3]) is not None
        )

    require(set(record) == PAYLOAD_KEYS, "exact frozen child payload fields")
    require(type(pid) is int and pid > 0 and record["pid"] == pid and type(record["pid"]) is int, "exact owned child PID")
    require(record["ppid"] == spec["expected_observer_pid"] and type(record["ppid"]) is int, "actual observer PPID")
    require(record["status"] == "OBSERVATION_ONLY_NOT_ACCEPTANCE", "observation status")
    require((record["condition"], record["variant"], record["repetition"]) == (spec["condition"], spec["variant"], spec["repetition"]) and type(record["repetition"]) is int, "exact finite row")
    subject = spec["direct_subject"]
    for key in ("actual119_parent", "candidate", "environment", "grant"):
        require(record[key] == subject["expected_child_fields"][key], "bound child provenance " + key)
    fixture = spec["fixture_binding"]
    require(record["fixture_directory"] == fixture["directory"] and record["fixture_file_hashes"] == fixture["files"], "exact qualified five fixture files")
    before, after = record["input_identities_before"], record["input_identities_after"]
    require(isinstance(before, dict) and isinstance(after, dict) and set(before) == set(after) == {"filtered", "carriers", "x_um", "y_um"}, "four kernel callers before/after")
    require(all(array_identity(values[name], name) for values in (before, after) for name in ("filtered", "carriers", "x_um", "y_um")), "four-field JSON-list caller identities before/after")
    require(before == after == fixture["expected_loaded_input_identities"], "fixed unchanged loaded caller identities")
    output_identity = record["output_identity"]
    require(array_identity(output_identity, "image") and output_identity == fixture["expected_output_identity"], "four-field JSON-list public image identity; separate full byte comparison still required")
    require(output_identity[1] == spec["output_shape"] and output_identity[2] == "<f8", "canonical output identity shape/dtype")
    require(record["output_complete_little_endian_bytes_path"] == spec["output_image_path"], "complete raw little-endian image path")
    require(record["output_shape"] == spec["output_shape"] and record["output_dtype"] == "<f8" and record["output_strides"] == spec["output_strides"], "output shape/dtype/strides")
    require(record["output_owns_data"] is True and record["output_writeable"] is True, "kernel output flags")
    image = Path(spec["output_image_path"])
    require(image.is_file() and image.stat().st_size == spec["output_bytes"], "complete archived raw image byte count")
    require(digest(image) == output_identity[3], "complete raw artifact digest matches declared canonical output identity")
    require(record["native_high_water_units"] == "Linux KiB" and record["native_high_water_multiplier_to_bytes"] == 1024, "Linux native cumulative units")
    highs = [record[name] for name in ("pre_call_high_water_native", "call_end_high_water_native", "post_observation_high_water_native")]
    require(all(integer(value) for value in highs) and highs == sorted(highs), "cumulative high-water order; no subtraction")
    stamps = [record[name] for name in ("fixture_loading_started_ns", "fixture_loading_ended_ns", "pre_call_snapshot_ns", "kernel_started_ns", "kernel_ended_ns", "call_end_snapshot_ns", "post_observation_snapshot_ns")]
    require(all(type(value) is int and value > 0 for value in stamps) and stamps == sorted(stamps), "actual monotonic child timestamps")
    require(number(record["fixture_loading_seconds"]) and record["fixture_loading_seconds"] == (stamps[1] - stamps[0]) / 1_000_000_000, "separate fixture load duration")
    require(number(record["kernel_seconds"]) and record["kernel_seconds"] == (stamps[4] - stamps[3]) / 1_000_000_000, "one assembly call duration")
    require(record["terminal_direct_child_usage"] == "EXTERNAL_EXISTING_WAIT_OWNER_REQUIRED", "external terminal ownership placeholder")
    require(record["sampled_current_rss"] == "EXTERNAL_EXISTING_OBSERVER_REQUIRED", "external sampled RSS placeholder")
    require(isinstance(record["limits"], str) and bool(record["limits"]), "explicit observation limits")
    # Metadata/hash equality is no scientific verdict or complete byte comparison.


def child_outcome(path, max_bytes, pid, spec):
    """Inherited bounded strict JSON core; fixed FA120 record correspondence."""
    if not path.exists() or path.stat().st_size == 0:
        return "missing_child_record", None
    if path.stat().st_size > max_bytes:
        return "child_record_exceeds_admitted_parse_bound", None
    try:
        with path.open("rb") as stream:
            raw = stream.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return "child_record_exceeds_admitted_parse_bound", None
        record = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant)
        _finite_json(record)
        if not isinstance(record, dict):
            raise ValueError("direct child record must be one JSON object")
        validate_complete_record(record, pid, spec)
        return "finite_observation_pending_qualification", record
    except (ValueError, UnicodeError, OSError, TypeError, KeyError) as error:
        return "malformed_child_record", {"parse_type": type(error).__name__, "message": str(error)}
