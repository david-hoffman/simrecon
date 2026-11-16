"""PH118 fixed direct-target SOURCE binding; UNAPPROVED and NEVER EXECUTED.

No launcher, waiter, signal owner, RSS parser or scientific fixture is defined here.
The accompanying copied method7 runner owns that unchanged lifecycle.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE_IDS = (
    "acquisition-64", "acquisition-128", "acquisition-off", "acquisition-drift",
    "known-64", "known-128", "preparation-context-64",
)
METHOD_FILES = ("observer.py", "run_direct_attempt.py", "direct_binding.py", "manifest.json")
ADAPTER = "tests/preparation_harmonic_memory_benchmark.py"
SHARED = "tests/reconstruction_memory_benchmark.py"
PROTOCOL = "docs/packets/issue-118-direct-resource-protocol.md"
DIAGNOSTICS = (
    "scripts/source_free_check.py",
    "scripts/source_free_sitecustomize/sitecustomize.py",
    "scripts/source_free_sitecustomize/pytest_plugin.py",
)


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            value.update(chunk)
    return value.hexdigest()


def manifest():
    return json.loads((HERE / "manifest.json").read_text())


def material_hashes(root):
    """Hash an explicit closed subject list plus every local executable method file.

    No product glob, mutable sibling import or historical116 product map is used.
    The supplied draft has no final subject closure and therefore fails closed.
    """
    root = Path(root).resolve()
    paths = manifest()["subject_material_paths"]
    if not isinstance(paths, list) or not paths or paths != sorted(set(paths)):
        raise ValueError("final explicit sorted subject material closure is unbound")
    required = {ADAPTER, SHARED, PROTOCOL, "uv.lock", *DIAGNOSTICS}
    if not required.issubset(paths) or not any(p.startswith("src/simrecon/") for p in paths):
        raise ValueError("direct/protocol/diagnostic/product closure incomplete")
    result = {}
    for name in paths:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not (root / path).resolve().is_relative_to(root):
            raise ValueError("subject material escapes selected worktree")
        result["subject:" + name] = digest(root / path)
    for name in METHOD_FILES:
        result["method:" + name] = digest(HERE / name)
    return result


def check_release(grant, root):
    """Require future root-owned exact bindings; this source artifact grants none."""
    frozen = manifest()
    if frozen["approved"] is not True or frozen["execution_status"] != "released_exact_case":
        raise ValueError("PH118 direct method is SOURCE ONLY / UNAPPROVED / HOLD")
    timeout = frozen["launch"]["startup_timeout_seconds"]
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("final positive PH118 startup bound remains unbound")
    if grant.get("approved") is not True or grant.get("protocol") != "PH118-direct-grant-v1":
        raise ValueError("unapproved or wrong direct grant")
    subject = grant["subject"]
    required_proofs = (
        "actual_accepted117", "integrated118", "affected_review", "method_qualification",
        "diagnostic_route_qualification", "metadata_git_abort_ownership",
        "exclusive_window", "environment_binding",
    )
    if subject["role"] == "candidate":
        required_proofs += ("parent_case_qualification",)
    for key in required_proofs:
        proof = grant["proofs"][key]
        if not isinstance(proof, dict) or set(proof) != {"path", "sha256"}:
            raise ValueError("unbound reviewed proof: " + key)
        if not re.fullmatch(r"[0-9a-f]{64}", proof["sha256"]) or digest(proof["path"]) != proof["sha256"]:
            raise ValueError("changed reviewed proof: " + key)
    if subject["worktree"] != str(root) or subject["python"] != sys.executable:
        raise ValueError("literal root/interpreter binding differs")
    if subject["role"] not in ("parent", "candidate") or type(subject["dirty"]) is not bool:
        raise ValueError("exact direct subject role/dirty binding required")
    if subject["module_root"] != str(root / "src/simrecon"):
        raise ValueError("fixed selected product module root differs")
    if (subject["revision"], subject["tree"]) != (
        grant["candidate"]["head"], grant["candidate"]["tree"],
    ):
        raise ValueError("target argv and observer subject identities differ")
    if subject["hashes"] != frozen["adapter_hashes"]:
        raise ValueError("adapter/shared/lock bindings differ from frozen manifest")
    if tuple(row["id"] for row in frozen["initial_conditions"]) != CASE_IDS:
        raise ValueError("fixed seven direct condition IDs changed")
    if any(key in grant for key in ("declared_growth_conditions", "growth_separate_admission")):
        raise ValueError("growth dispatch is absent from this fixed direct binding")
    if grant["profile"] is not False or type(grant["repetition"]) is not int:
        raise ValueError("no workflow profiling; integer direct repetition required")
    for name, expected in subject["hashes"].items():
        relative = {"adapter": ADAPTER, "shared_observer": SHARED, "lock": "uv.lock"}[name]
        if digest(root / relative) != expected:
            raise ValueError("changed direct target input: " + name)
    if material_hashes(root) != grant["material_hashes"]:
        raise ValueError("closed direct subject/method material differs")
    # Identity of this environment must be externally frozen/qualified before startup;
    # sitecustomize necessarily executes before this module can inspect its bytes.
    diagnostic = str(root / "scripts/source_free_sitecustomize")
    inherited = subject["diagnostic_environment"]
    previous_path = inherited["inherited_pythonpath"]
    previous_plugins = inherited["inherited_pytest_plugins"]
    if any(value is not None and not isinstance(value, str) for value in (previous_path, previous_plugins)):
        raise ValueError("explicit frozen inherited diagnostic environment required")
    expected_path = diagnostic + (os.pathsep + previous_path if previous_path else "")
    expected_plugins = "pytest_plugin" + ("," + previous_plugins if previous_plugins else "")
    if inherited["PYTHONPATH"] != expected_path or inherited["PYTEST_PLUGINS"] != expected_plugins:
        raise ValueError("diagnostic environment differs from committed prepend/inheritance behavior")
    if os.environ.get("PYTHONPATH") != expected_path or os.environ.get("PYTEST_PLUGINS") != expected_plugins:
        raise ValueError("actual startup diagnostic path/plugin inheritance differs")
    if not isinstance(subject["expected_provenance"], dict) or not isinstance(subject["expected_environment"], dict):
        raise ValueError("final actual provenance/environment records unbound")


def target_argv(grant, spec, root):
    """One direct interpreter/adapter process, never the source_free_check wrapper."""
    subject = grant["subject"]
    values = (
        ("case", spec["id"]), ("role", subject["role"]),
        ("repetition", str(spec["repetition"])), ("worktree", str(root)),
        ("expected-python", sys.executable), ("expected-module-root", subject["module_root"]),
        ("revision", subject["revision"]), ("tree", subject["tree"]),
        ("dirty", "true" if subject["dirty"] else "false"),
        ("adapter-sha256", subject["hashes"]["adapter"]),
        ("shared-observer-sha256", subject["hashes"]["shared_observer"]),
        ("lock-sha256", subject["hashes"]["lock"]),
    )
    return [sys.executable, str(root / ADAPTER), *[part for key, value in values for part in ("--" + key, value)]]


def prepare_spec(grant, spec):
    """External correspondence fields, never injected into adapter scientific JSON."""
    spec["direct_subject"] = grant["subject"]
    spec["expected_material_hashes"] = grant["material_hashes"]
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
    """Check the unchanged direct record, without fabricating WS116-child fields.

    pid links the exclusive inherited stdout descriptor to the exact wait owner.
    PH118-direct-v1 has no child PID/nonce/spec/timestamp fields; it is not an
    independently self-authenticating process receipt. Readiness is pre-exec only.
    """
    from observer import legal_numeric_dtype

    def require(ok, name):
        if not ok:
            raise ValueError("incomplete direct observation: " + name)

    def integer(value):
        return type(value) is int and value >= 0

    def number(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    def sha(value):
        return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None

    subject = spec["direct_subject"]
    require(type(pid) is int and pid > 0, "exact owned direct PID")
    require(record.get("protocol") == "PH118-direct-v1" and record.get("status") == "pass", "direct protocol/status")
    require(
        (record.get("case"), record.get("role"), record.get("repetition"), record.get("entry"))
        == (spec["id"], subject["role"], spec["repetition"], spec["entry"])
        and type(record.get("repetition")) is int,
        "exact direct case/role/repetition/entry",
    )
    provenance = record.get("provenance")
    require(isinstance(provenance, dict) and provenance == subject["expected_provenance"], "complete frozen actual provenance")
    require(
        provenance.get("worktree") == subject["worktree"]
        and provenance.get("interpreter") == subject["python"]
        and provenance.get("revision") == subject["revision"]
        and provenance.get("tree") == subject["tree"]
        and provenance.get("dirty") is subject["dirty"]
        and provenance.get("hashes") == subject["hashes"]
        and provenance.get("product_tracked_clean") is True,
        "selected subject provenance",
    )
    require(
        {key: record.get(key) for key in ("versions", "backend", "scipy_fft_default_workers")}
        == subject["expected_environment"], "pinned package/backend/FFT environment",
    )
    context = record.get("context")
    require(isinstance(context, dict) and context.get("system") == "Linux", "Linux direct context")
    require(context.get("threads") == {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "four startup thread controls")
    require(context.get("pointer_bits") == 64, "64-bit direct context")
    fingerprints = record.get("public_fingerprints")
    require(isinstance(fingerprints, dict) and fingerprints.get("protocol") == "RM84-public-values-v1", "public value protocol")
    require(all(sha(fingerprints.get(key)) for key in ("inputs", "inputs_after", "result")), "public fingerprints")
    require(fingerprints["inputs"] == fingerprints["inputs_after"], "retained callers unchanged")
    for name in ("caller_payload", "result_payload", "union_payload"):
        payload = record.get(name)
        require(isinstance(payload, dict), name)
        require(all(integer(payload.get(key)) for key in ("array_payload_bytes", "unique_backings", "python_metadata_estimate_bytes")), name + " counters")
        require(isinstance(payload.get("metadata_limit"), str) and bool(payload["metadata_limit"]), name + " scope")
        arrays = payload.get("arrays")
        require(isinstance(arrays, list) and bool(arrays), name + " arrays")
        for array in arrays:
            require(
                isinstance(array, dict) and isinstance(array.get("path"), str)
                and isinstance(array.get("shape"), list) and all(integer(n) for n in array["shape"])
                and legal_numeric_dtype(array.get("dtype"), canonical=False)
                and integer(array.get("bytes")), name + " array metadata",
            )
    snapshots, byte_values = record.get("ru_maxrss_native"), record.get("high_water_bytes")
    names = ("pre_target", "target_return", "final_whole_process")
    require(record.get("ru_maxrss_native_units") == "KiB", "Linux snapshot native units")
    require(isinstance(snapshots, dict) and set(snapshots) == set(names), "snapshot names")
    require(isinstance(byte_values, dict) and set(byte_values) == set(names), "snapshot byte names")
    require(all(integer(snapshots[key]) and integer(byte_values[key]) and byte_values[key] == snapshots[key] * 1024 for key in names), "snapshot native/byte conversion")
    require(snapshots[names[0]] <= snapshots[names[1]] <= snapshots[names[2]], "cumulative snapshot order")
    require(number(record.get("elapsed_target_seconds")), "call-only monotonic elapsed seconds")
    for group, keys in (
        ("page_faults", ("before_minor", "before_major", "after_minor", "after_major")),
        ("swaps_native", ("before", "after")), ("block_io_native", ("inblock", "outblock")),
    ):
        values = record.get(group)
        require(isinstance(values, dict) and all(integer(values.get(key)) for key in keys), group)
    witness = record.get("witness")
    require(isinstance(witness, dict) and witness.get("record") == spec["record"], "frozen public record class witness")
    require(record.get("disk_array_bytes") == 0 and isinstance(record.get("limits"), str) and bool(record["limits"]), "no disk arrays / explicit limits")
    # Witness values, numeric correctness and exact paired result matching remain
    # separately reviewed obligations; this structural check supplies no science verdict.


def child_outcome(path, max_bytes, pid, spec):
    """One bounded complete JSON value; logs/multiple records/nonfinite values fail."""
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
        if (record.get("case"), record.get("role"), record.get("repetition")) != (
            spec["id"], spec["direct_subject"]["role"], spec["repetition"],
        ) or type(record.get("repetition")) is not int:
            raise ValueError("direct child condition/subject/repetition mismatch")
        if record.get("status") == "failure":
            if not all(isinstance(record.get(key), str) for key in ("type", "message")):
                raise ValueError("incomplete direct adapter failure record")
            return "direct_adapter_exception", record
        validate_complete_record(record, pid, spec)
        return "finite_observation_pending_qualification", record
    except (ValueError, UnicodeError, OSError, TypeError, KeyError) as error:
        return "malformed_child_record", {"parse_type": type(error).__name__, "message": str(error)}
