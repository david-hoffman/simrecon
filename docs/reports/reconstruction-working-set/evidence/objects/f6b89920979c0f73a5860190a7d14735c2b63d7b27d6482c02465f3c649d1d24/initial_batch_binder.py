"""ROOT-owned fixed WS116 initial-row binder; SOURCE ONLY, not activated.

No scientific imports, native accounting, workload waits/signals, retries or growth.
Existing runner owns completeness validation and its exact direct-child wait4.
This file has deliberately NOT been executed or tested in the source-only lane.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

TABLE_SHA = "0058ccffffd86448c613351319a7b892e813d123014ab0205cf5b69c85a4b49d"
EMPTY_SHA = hashlib.sha256(b"").hexdigest()
MATERIAL_NAMES = ('src/simrecon/__init__.py', 'src/simrecon/acquisition/__init__.py', 'src/simrecon/acquisition/declarations.py', 'src/simrecon/acquisition/drift.py', 'src/simrecon/acquisition/layout.py', 'src/simrecon/acquisition/modes.py', 'src/simrecon/acquisition/preparation.py', 'src/simrecon/cli.py', 'src/simrecon/io/__init__.py', 'src/simrecon/io/imagej.py', 'src/simrecon/io/imagej_metadata.py', 'src/simrecon/io/metadata.py', 'src/simrecon/io/mrc_writer.py', 'src/simrecon/io/pixels.py', 'src/simrecon/io/priism.py', 'src/simrecon/models.py', 'src/simrecon/optical_transfer.py', 'src/simrecon/reconstruction/__init__.py', 'src/simrecon/reconstruction/known_parameters.py', 'src/simrecon/reconstruction/parameter_estimation.py', 'src/simrecon/workflow/__init__.py', 'src/simrecon/workflow/adapters.py', 'src/simrecon/workflow/config.py', 'src/simrecon/workflow/identity.py', 'src/simrecon/workflow/reconstruct.py', 'src/simrecon/workflow/result.py', 'src/simrecon/workflow/summary.py', 'src/simrecon/workflow/transfer.py', 'uv.lock', 'tests/reconstruction_summary_fixture.py', 'tests/reconstruction_memory_benchmark.py', 'docs/reports/reconstruction-working-set/manifest.json', 'docs/reports/reconstruction-working-set/observer.py', 'docs/reports/reconstruction-working-set/run_attempt.py', 'docs/reports/reconstruction-working-set/workload_child.py')
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")
CAPTURE_SHA = "47215ee63496e2043e0f5668c1d2d433351ca6067550f11f469f257ccccda68f"
COMPLETE = "complete_child_observed_pending_scientific_qualification"
CONFIG_KEYS = {"authorized", "binder_sha256", "table_path", "root", "git", "docker", "outer_python",
    "capture_helper", "container", "inner_python", "python_resolved", "candidate", "material_hashes",
    "tool_hashes", "accepted_method7", "method7_expected", "environment", "environment_expected",
    "root_authority", "authority_expected", "window", "mapping", "expected_exposed",
    "docker_inspect_stdout", "metadata_source", "metadata_expected", "metadata_max_age_seconds",
    "scheduler_ack", "scheduler_ack_expected", "owned_ledger", "expected_core",
    "grant_fixed", "conditional_rationale", "receipt_protocol", "child_protocol", "allowed_attempt_ids",
    "continuation_authorized", "prior_eligible", "external_batch_directory"}


class Hold(Exception):
    pass


def require(ok, reason):
    if not ok:
        raise Hold(reason)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1048576):
            h.update(block)
    return h.hexdigest()


def load(path, maximum=4194304):
    require(Path(path).stat().st_size <= maximum, "JSON exceeds fixed parse bound")
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def pinned(ref):
    require(type(ref) is dict and set(ref) == {"path", "sha256"}, "missing exact file reference")
    require(sha(ref["path"]) == ref["sha256"], "pinned file bytes changed: " + ref["path"])
    return load(ref["path"])


def age(timestamp, limit):
    require(type(timestamp) is int and 0 <= time.time_ns() - timestamp <= limit * 1000000000,
            "missing/future/stale context timestamp")


def window(cfg):
    w = cfg["window"]
    require(w["starts_unix_ns"] <= time.time_ns() < w["ends_unix_ns"], "ROOT window inactive")
    require(pinned(cfg["root_authority"]) == cfg["authority_expected"], "ROOT authority differs")


def source(cfg):
    require(sha(cfg["loaded_path"]) == cfg["loaded_sha256"] and sha(__file__) == cfg["binder_sha256"] and
            sha(cfg["table_path"]) == TABLE_SHA, "config/binder/table changed during batch")
    root = Path(cfg["root"])
    require(cfg["root"] == "/workspace/work/issue-116" and cfg["container"] == "simrecon-campaign-ubuntu" and cfg["inner_python"] == ".venv/bin/python",
            "existing capture helper fixed worktree/container mismatch")
    actual = {}
    for key, args in (("head", ["rev-parse", "HEAD"]), ("tree", ["rev-parse", "HEAD^{tree}"])):
        actual[key] = subprocess.check_output([cfg["git"], *args], cwd=root, text=True).strip()
    actual["tracked_diff_sha256"] = hashlib.sha256(subprocess.check_output(
        [cfg["git"], "diff", "--binary", "HEAD"], cwd=root)).hexdigest()
    require(actual == cfg["candidate"] and actual["tracked_diff_sha256"] == EMPTY_SHA,
            "candidate changed or tracked state dirty")
    require(set(cfg["material_hashes"]) == set(MATERIAL_NAMES), "exact35 material basis required")
    for name, expected in cfg["material_hashes"].items():
        path = root / name
        require(path.resolve().is_relative_to(root.resolve()) and sha(path) == expected,
                "material identity changed: " + name)
    require({cfg[key] for key in ("git", "docker", "outer_python", "capture_helper", "python_resolved")}
            <= set(cfg["tool_hashes"]), "missing tool/executable hash")
    require(str((root / cfg["inner_python"]).resolve()) == cfg["python_resolved"], "inner interpreter path changed")
    for path, expected in cfg["tool_hashes"].items():
        require(sha(path) == expected, "tool/environment executable changed: " + path)
    require(pinned(cfg["accepted_method7"]) == cfg["method7_expected"], "accepted method7 ambiguity")
    require(cfg["method7_expected"]["suitable"] is True and
            cfg["method7_expected"]["qualified"] is True, "method7 not suitable/qualified")
    require(pinned(cfg["environment"]) == cfg["environment_expected"], "environment binding changed")
    require(sha(cfg["metadata_source"]["path"]) == cfg["metadata_source"]["sha256"],
            "complementary source identity changed")


def scheduler(cfg):
    ack = pinned(cfg["scheduler_ack"])
    require(ack == cfg["scheduler_ack_expected"] and ack["window"] == cfg["window"] and
            ack["campaign_work_suspended"] is True and ack["known_active_numerical_processes"] == [] and
            ack["outside_campaign_actors"] == "unknown_not_scanned", "ROOT scheduler suspension ACK unknown/changed")
    require(cfg["window"]["starts_unix_ns"] - 5000000000 <= ack["observed_at_unix_ns"] <= time.time_ns(),
            "ROOT scheduler ACK not fresh for this window")
    return ack


def owned_markers(raw):
    receipt = load(raw / "receipt.json")
    markers = [load(raw / "spawn-intent.json")["observer_identity"],
               load(raw / "owned-child.json")["child_identity"]]
    require([item["pid"] for item in markers] == [receipt["observer_pid"], receipt["workload_pid"]],
            "owned marker/receipt identity mismatch")
    return [{"pid": item["pid"], "start_ticks": item["start_ticks"], "boot_id": item["boot_id"],
             "fds": sorted(set(receipt["startup_fd_plan"].values()))} for item in markers]


def metadata(cfg, row, phase, out, proposal, extra_owned=()):
    """One fixed complementary inner-namespace stdlib snippet; no process scans."""
    require(sha(cfg["metadata_source"]["path"]) == cfg["metadata_source"]["sha256"],
            "complementary metadata source changed")
    ledger = pinned(cfg["owned_ledger"])
    require(ledger["scope"] == "WS116_scientific_observer_workload_processes" and ledger["unresolved"] == [] and
            ledger["root_authority_sha256"] == cfg["root_authority"]["sha256"],
            "ROOT known-owned ledger incomplete/unknown")
    owned = []
    for item in ledger["closed_owned_processes"]:
        receipt = pinned(item["receipt"])
        require(receipt["terminal"] is not None and receipt["wait_ownership_lost"] is False and
                item["identity"]["pid"] in (receipt["observer_pid"], receipt["workload_pid"]),
                "prior owned receipt/identity unresolved")
        owned.append(item["identity"])
    owned += cfg["prior_owned"] + list(extra_owned)
    # Deduplicate literal identities while retaining every exact FD path.
    merged = {}
    for item in owned:
        key = (item["pid"], item["start_ticks"], item["boot_id"])
        if key in merged:
            merged[key]["fds"] = sorted(set(merged[key]["fds"] + item["fds"]))
        else:
            merged[key] = dict(item)
    require(set(cfg["metadata_expected"]["disk_identity"]) == {cfg["root"], cfg["external_batch_directory"]},
            "both raw-worktree and external progress filesystems require actual disk facts")
    request = {"disk_paths": list(cfg["metadata_expected"]["disk_identity"]),
               "owned_processes": list(merged.values())}
    request_path = out / (phase + "-metadata-request.json")
    save(request_path, request)
    command = [cfg["docker"], "exec", "--user", "1000:1000", "-w", cfg["root"]]
    for name in THREADS:
        command += ["-e", name + "=1"]
    command += [cfg["container"], cfg["inner_python"], cfg["metadata_source"]["path"], str(request_path)]
    save(out / (phase + "-metadata-intent.json"), {"argv": command,
         "source": cfg["metadata_source"], "request_sha256": sha(request_path),
         "environment": {name: "1" for name in THREADS}})
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    save(out / (phase + "-metadata-command.json"), {"returncode": result.returncode,
         "stdout": result.stdout, "stderr": result.stderr})
    require(result.returncode == 0, "complementary metadata incomplete")
    value = json.loads(result.stdout)
    require(value["protocol"] == "WS116-fixed-ubuntu-metadata-v1" and
            value["source_sha256"] == cfg["metadata_source"]["sha256"] and
            value["request_sha256"] == sha(request_path), "complementary source/request mismatch")
    expected = cfg["metadata_expected"]
    require(set(expected) == {"uid", "gid", "executable", "cwd", "boot_id", "namespaces", "rlimits", "disk_identity"},
            "missing metadata physical expectations")
    for key in ("uid", "gid", "executable", "cwd", "boot_id", "namespaces", "rlimits"):
        require(value[key] == expected[key] and value[key] is not None, "Ubuntu metadata changed: " + key)
    require(value["uid"] == value["gid"] == 1000 and value["executable"] == cfg["python_resolved"] and
            value["namespaces"]["cgroup"] == cfg["expected_exposed"]["namespace"] and
            value["environment"] == {name: "1" for name in THREADS}, "UID/executable/namespace/environment unknown")
    require(set(value["disks"]) == set(expected["disk_identity"]), "disk path set differs")
    for path, disk in value["disks"].items():
        require({key: disk[key] for key in ("device", "fsid", "fragment_size")} == expected["disk_identity"][path] and
                disk["free_bytes"] >= proposal["disk_proposal_bytes"] and disk["free_inodes"] > 0,
                "Ubuntu disk identity/headroom unknown")
    require(len(value["owned_processes"]) == len(request["owned_processes"]), "owned identity postcheck omitted")
    for observed, item in zip(value["owned_processes"], request["owned_processes"]):
        require(observed["expected"] == item and observed["identity_state"] == "absent" and
                all(fact["state"] == "absent" for fact in observed["fds"].values()) and
                set(observed["fds"]) == {str(fd) for fd in item["fds"]},
                "exact owned PID/start/FD remains live/reused/ambiguous")
    require(value["outside_campaign_processes"] == "unknown_not_scanned", "global absence invented")
    require(type(cfg["metadata_max_age_seconds"]) in (int, float) and 0 < cfg["metadata_max_age_seconds"] <= 60,
            "ROOT complementary age predicate unavailable")
    age(value["observed_at_unix_ns"], cfg["metadata_max_age_seconds"])
    save(out / (phase + "-metadata.json"), value)
    return value


def context(cfg, row, phase, out, proposal):
    """Run ONLY the existing pinned capture helper; no new probe implementation."""
    require(sha(cfg["capture_helper"]) == CAPTURE_SHA, "capture helper changed")
    result = subprocess.run([cfg["outer_python"], cfg["capture_helper"]],
                            capture_output=True, text=True, check=False)
    save(out / (phase + "-capture-command.json"), {"returncode": result.returncode,
         "stdout": result.stdout, "stderr": result.stderr})
    require(result.returncode == 0, "existing capture helper failed")
    pointer = json.loads(result.stdout)
    proof = pinned({"path": pointer["path"], "sha256": pointer["sha256"]})
    require(proof["capture_source_sha256"] == CAPTURE_SHA and proof["schema"] ==
            "campaign-resource-domain-correspondence-v1", "capture protocol changed")
    require(proof["external_ancestors"] == "unknown_unobservable", "external ancestors unknown")
    require(proof["docker_inspect"]["returncode"] == proof["inner"]["returncode"] == 0,
            "Docker/inner context incomplete")
    require(proof["docker_inspect"]["stdout"] == cfg["docker_inspect_stdout"],
            "container/image/init PID/config identity changed")
    inner = json.loads(proof["inner"]["stdout"])
    require(proof["outer"]["file_identities"] == inner["file_identities"],
            "outer/inner exposed resource objects differ")
    for name, view in (("outer", proof["outer"]), ("inner", inner)):
        expected = cfg["mapping"][name]
        require(view["cgroup_namespace"] == expected["cgroup_namespace"] and
                view["file_identities"] == expected["file_identities"], "resource object mapping changed")
        for path, text in expected["fixed_files"].items():
            require(view["files"][path] == text, "membership/mount/limit changed: " + path)
        f = view["files"]
        require(set(cfg["expected_exposed"]["visible_memory_max"]) == {"/sys/fs/cgroup"},
                "helper cannot prove additional ancestors: HOLD for ROOT correspondence")
        current, maximum = int(f["/sys/fs/cgroup/memory.current"]), int(f["/sys/fs/cgroup/memory.max"])
        stop = proposal["proposed_each_visible_ancestor_stop_bytes"]
        require(current + proposal["process_stop_bytes"] + proposal["reserve_bytes"] <= stop < maximum,
                "ancestor current/process/reserve/limit margin fails")
        events = dict(line.split() for line in f["/sys/fs/cgroup/memory.events"].splitlines())
        require(events == cfg["mapping"][name]["events_exact"], "memory event delta/unknown")
        require(int(f["/sys/fs/cgroup/memory.swap.current"]) == cfg["mapping"][name]["swap_current_bytes"] == 0,
                "swap present/changed")
        mem = dict(line.split(":", 1) for line in f["/proc/meminfo"].splitlines())
        require(mem["MemAvailable"].strip().endswith("kB"), "host units unknown")
        available = int(mem["MemAvailable"].split()[0]) * 1024
        require(available > max(proposal["host_min_available_bytes"],
                                proposal["process_stop_bytes"] + proposal["reserve_bytes"]),
                "host/process/reserve headroom fails")
        age(view["observed_at_unix_ns"], 5)
    age(proof["started_at_unix_ns"], 5)
    return pointer, proof


def inventory(raw, maximum_bytes):
    """Bounded known per-attempt directory only; never process/global scans."""
    require(raw.is_dir() and not raw.is_symlink(), "raw directory missing/aliased")
    paths = list(raw.iterdir())
    require(len(paths) <= 32, "unexpected raw file count")
    require(sum(path.lstat().st_size for path in paths) <= maximum_bytes, "raw hash byte budget exceeded")
    result = {}
    for path in paths:
        require(path.is_file() and not path.is_symlink(), "unexpected raw entry")
        stat = path.stat()
        result[path.name] = {"sha256": sha(path), "logical_bytes": stat.st_size,
                             "allocated_bytes": stat.st_blocks * 512}
    return result


def eligible(cfg, row, condition, raw, grant_sha):
    """Check existing protocol's result and a small declared core, no new science parser."""
    r = load(raw / "receipt.json")
    child = load(raw / "stdout.json")
    require(r["protocol"] == cfg["receipt_protocol"] and child["protocol"] == cfg["child_protocol"],
            "latebound accepted protocol mismatch")
    require(r["status"] == COMPLETE and r["child_outcome"] == "finite_observation_pending_qualification",
            "runner completeness/child status ineligible")
    require(not any(k in r for k in ("stop_reason", "cleanup_gap", "postflight_gap", "error_type")),
            "runner stop/cleanup/postflight failure")
    require(r["signals"] == [] and r["startup_parent_fds_closed"] is True and
            type(r["startup_eof_observed"]) is bool and r["wait_ownership_lost"] is False and
            r["nonterminal_wait_events"] == [], "lifecycle/FD/native ownership gap")
    terminal = r["terminal"]
    require(terminal["pid"] == r["workload_pid"] and terminal["exited"] is True and
            terminal["signaled"] is False and terminal["returncode"] == terminal["exit_code"] == 0,
            "child finite exit0 native receipt missing")
    require(terminal["ru_maxrss_native_units"] == "Linux KiB" and
            terminal["ru_maxrss_multiplier_to_bytes"] == 1024 and
            type(terminal["rusage_native"]["ru_maxrss"]) is int and
            terminal["kernel_reported_direct_child_high_water_bytes"] ==
            terminal["rusage_native"]["ru_maxrss"] * 1024,
            "existing native receipt inconsistent; no new accounting")
    require(r["grant_sha256"] == grant_sha and r["child_record_sha256"] == sha(raw / "stdout.json"),
            "grant/child receipt fingerprint mismatch")
    for key in ("candidate_before", "candidate_after", "candidate_final"):
        require(r[key] == cfg["candidate"], "receipt source basis changed")
    for key in ("material_hashes_before", "material_hashes_after", "material_hashes_final"):
        require(r[key] == cfg["material_hashes"], "receipt materials changed")
    require(r["material_identity_matches"] is True and child["material_identity_matches"] is True and
            child["finite_common_fields"] is True and child["status"] ==
            "finite_observation_pending_qualification", "child finite/material completion absent")
    require(child["pid"] == r["workload_pid"] and child["spec"]["launch"]["nonce"] == row["launch_nonce"],
            "child identity/nonce mismatch")
    for key in ("condition_id",):
        require(row[key] == condition["condition"]["id"], "wrong condition")
    for key in ("repetition", "profile"):
        require(child["spec"][key] == row[key], "wrong repetition/profile")
    for key in ("shape", "mode", "search"):
        require(child["spec"][key] == condition["condition"][key], "wrong declared shape/mode/search")
    require(child["branches"] == condition["expected_output"]["branches"], "wrong preserved branch")
    require(child["spec"].get("case") == condition["condition"].get("case"), "wrong fixture case")
    for key, expected in cfg["expected_core"][row["condition_id"]].items():
        identity = child["output_hashes"][key]
        require(identity[:3] == [key, expected["shape"], expected["dtype"]], "wrong core dtype/geometry")
    require(r["interpreter"]["resolved"] == cfg["python_resolved"] and
            r["launch"]["nonce"] == row["launch_nonce"] and
            r["session_ready"]["pid"] == r["workload_pid"], "interpreter/session mismatch")
    return {key: child[key] for key in ("input_sha256", "common_output_sha256", "public_result_sha256", "branches")}


def compare(row, condition, hashes, previous):
    for prior_row, prior_condition, prior_hashes in previous:
        left, right = condition["condition"], prior_condition["condition"]
        if left["id"] == right["id"]:
            require(hashes == prior_hashes, "identical repeat fingerprints differ")
        elif (left["shape"], left.get("case"), left["search"]) == (
                right["shape"], right.get("case"), right["search"]) and left["mode"] != right["mode"]:
            require(all(hashes[key] == prior_hashes[key] for key in
                        ("input_sha256", "common_output_sha256", "branches")),
                    "matched full/summary core differs")


def run(cfg, row, condition, directory, previous):
    proposal = condition["operating_proposal"]
    raw = Path(cfg["root"]) / "docs/reports/reconstruction-working-set/raw" / row["attempt_id"]
    require(not raw.exists(), "attempt-ID collision, never reuse/overwrite")
    out = directory / row["attempt_id"]
    out.mkdir()
    window(cfg)
    require(time.time_ns() + (proposal["deadline_seconds"] + 120) * 1000000000 <
            cfg["window"]["ends_unix_ns"], "remaining ROOT window insufficient")
    source(cfg)
    require(set(cfg["grant_fixed"]) == {"numerical_release", "accepted_112_then_115",
            "campaign_ownership_resolved", "exclusive_window", "declared_growth_conditions",
            "no_automatic_retry_or_growth"}, "unknown fixed grant field")
    require(cfg["grant_fixed"]["declared_growth_conditions"] == [] and
            cfg["grant_fixed"]["campaign_ownership_resolved"] is True and
            cfg["grant_fixed"]["no_automatic_retry_or_growth"] is True,
            "growth/ownership/fixed grant invalid")
    require(cfg["grant_fixed"]["exclusive_window"] == {"released": True,
            "evidence": cfg["root_authority"]["path"],
            "evidence_sha256": cfg["root_authority"]["sha256"],
            "scope": "WS116 exact frozen initial-row release"}, "grant window authority differs")
    require(cfg["grant_fixed"]["numerical_release"] is True and
            cfg["grant_fixed"]["accepted_112_then_115"] is True, "ROOT numerical dependency/release absent")
    scheduler(cfg)
    physical = metadata(cfg, row, "pre", out, proposal)
    # Complementary context/static checks precede the LAST fresh correspondence capture.
    source(cfg)
    proof_ptr, proof = context(cfg, row, "pre", out, proposal)
    grant = dict(cfg["grant_fixed"])
    grant.update(candidate=cfg["candidate"], material_hashes=cfg["material_hashes"],
                 python_resolved=cfg["python_resolved"], condition_id=row["condition_id"],
                 repetition=row["repetition"], profile=False, launch_nonce=row["launch_nonce"],
                 attempt_id=row["attempt_id"], root_release_at_unix_ns=time.time_ns())
    for key in ("deadline_seconds", "process_stop_bytes", "host_min_available_bytes", "terminate_grace_seconds",
                "kill_reap_seconds", "max_child_record_bytes", "sample_interval_seconds",
                "startup_timeout_seconds", "startup_pipe_bytes"):
        grant[key] = proposal[key]
    grant["ancestor_stop_bytes"] = {"/sys/fs/cgroup": proposal["proposed_each_visible_ancestor_stop_bytes"]}
    grant["representation_preflight"] = {"accepted": True, "evidence": {
        "table_sha256": TABLE_SHA, "condition_id": row["condition_id"],
        "root_authority": cfg["root_authority"], "source_runtime_checks_preserved": True}}
    grant["headroom_evidence"] = {"proof": proof_ptr, "physical": physical,
                                  "operating_proposal": proposal, "status": "ROOT frozen conditional design"}
    grant["resource_domain"] = {"scope": "WS116-exposed-domain-conditional-v1",
        "external_ancestors": "unknown_unobservable", "conditional_rationale": cfg["conditional_rationale"],
        "expected_exposed": cfg["expected_exposed"], "correspondence_evidence": {
            "path": proof_ptr["path"], "sha256": proof_ptr["sha256"],
            "observed_at_unix_ns": proof["started_at_unix_ns"],
            "maximum_age_seconds": proposal["deadline_seconds"] + 120},
        **{key: proposal[key] for key in ("predicted_child_peak_bytes", "native_allocator_allowance_bytes", "reserve_bytes")}}
    grant_path = out / "grant.json"
    save(grant_path, grant)
    command = [cfg["docker"], "exec", "--user", "1000:1000", "-w", cfg["root"]]
    for name in THREADS:
        command += ["-e", name + "=1"]
    command += [cfg["container"], cfg["inner_python"],
                cfg["root"] + "/docs/reports/reconstruction-working-set/run_attempt.py",
                "--grant", str(grant_path), "--attempt-id", row["attempt_id"]]
    save(out / "intent.json", {"command": command, "row": row, "config_sha256": cfg["loaded_sha256"],
         "proof": proof_ptr, "grant_sha256": sha(grant_path), "source_sha256": sha(__file__),
         "time_unix_ns": time.time_ns(), "scope": "one synchronous existing runner; no retry"})
    # Binding/record writing must finish before <=5s freshness decision. No automatic recapture.
    window(cfg)
    scheduler(cfg)
    age(physical["observed_at_unix_ns"], cfg["metadata_max_age_seconds"])
    age(proof["started_at_unix_ns"], 5)
    require(sha(proof_ptr["path"]) == proof_ptr["sha256"], "proof changed before invocation")
    with (out / "observer.stdout.log").open("x") as stdout, (out / "observer.stderr.log").open("x") as stderr:
        # <=5s applies to existing-runner invocation, NOT a real-time workload spawn promise.
        invocation_unix_ns = time.time_ns()
        require(0 <= invocation_unix_ns - proof["started_at_unix_ns"] <= 5000000000,
                "last correspondence capture older than5s at runner invocation")
        require(invocation_unix_ns + (proposal["deadline_seconds"] + 120) * 1000000000 <
                cfg["window"]["ends_unix_ns"], "window insufficient at runner invocation")
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        # Ordinary wait owns only Docker exec proxy, NEVER workload PID/wait4.
        # Remain attached to this invocation through any overdue period; never kill it.
        started = time.monotonic()
        wait_gaps = []
        overdue = False
        while True:
            try:
                if process.poll() is not None:
                    code = process.wait()
                    break
                elapsed = time.monotonic() - started
                overdue = overdue or elapsed > proposal["deadline_seconds"] + 120
                print(json.dumps({"attempt_id": row["attempt_id"], "elapsed_seconds": elapsed,
                      "status": "OVERDUE_OWNED_HOLD" if overdue or wait_gaps
                      else "WAITING_OWNED_OBSERVER", "proxy_pid": process.pid}), flush=True)
                time.sleep(5)
            except BaseException as error:
                # Even cancellation/heartbeat loss stops progression, never abandons proxy.
                if len(wait_gaps) < 8:
                    wait_gaps.append({"type": type(error).__name__, "reason": str(error)})
                try:
                    time.sleep(1)
                except BaseException:
                    pass
    save(out / "observer-exit.json", {"returncode": code, "proxy_pid": process.pid, "overdue": overdue, "wait_gaps": wait_gaps,
         "runner_invocation_unix_ns": invocation_unix_ns,
         "proof_age_at_invocation_seconds": (invocation_unix_ns - proof["started_at_unix_ns"]) / 1000000000})
    raw_files = inventory(raw, proposal["disk_proposal_bytes"])
    save(out / "raw-files.json", raw_files)
    require(code == 0 and not overdue and not wait_gaps,
            "runner/proxy nonzero, overdue or wait interruption: ROOT diagnosis required")
    hashes = eligible(cfg, row, condition, raw, sha(grant_path))
    compare(row, condition, hashes, previous)
    # End validation is THIS frozen ROOT operational boundary, not the runner receipt.
    metadata(cfg, row, "post", out, proposal, owned_markers(raw))
    source(cfg)
    scheduler(cfg)
    context(cfg, row, "post", out, proposal)
    window(cfg)
    age(proof["started_at_unix_ns"], proposal["deadline_seconds"] + 120)
    require(sha(proof_ptr["path"]) == proof_ptr["sha256"], "original admission proof changed at end")
    boundary = {"status": "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW", "row": row,
        "candidate": cfg["candidate"], "material_hashes": cfg["material_hashes"], "table_sha256": TABLE_SHA,
        "method7": cfg["accepted_method7"], "raw_path": str(raw), "raw_files": raw_files,
        "fingerprints": hashes, "config_sha256": cfg["loaded_sha256"], "source_sha256": sha(__file__),
        "end_validation_scope": "binder original-proof hash/horizon + fresh end domain/context/margins/events; runner receipt does not perform this check"}
    save(out / "eligible-boundary.json", boundary)
    return hashes


def main():
    require(len(sys.argv) == 3, "use exact ROOT config path and approved config SHA256")
    require(sha(sys.argv[1]) == sys.argv[2], "config hash mismatch")
    cfg = load(sys.argv[1])
    require(set(cfg) == CONFIG_KEYS, "unknown/missing ROOT config field")
    require(cfg["authorized"] is True, "template/not ROOT authorized: HOLD")
    require(sha(__file__) == cfg["binder_sha256"], "binder source not ROOT frozen")
    require(sha(cfg["table_path"]) == TABLE_SHA, "approved initial table changed")
    table = load(cfg["table_path"])
    cfg["loaded_sha256"] = sys.argv[2]
    cfg["loaded_path"] = sys.argv[1]
    expected_core = {}
    for name, condition in table["conditions"].items():
        expected = condition["expected_output"]
        expected_core[name] = {key: {"shape": expected[key]["shape"], "dtype": "<f8"}
                              for key in ("image", "x_um", "y_um", "z_um", "carriers_cyc_um")}
        for key in ("modulation", "raw_modulation"):
            expected_core[name][key] = {"shape": expected["modulation_and_raw"]["shape"], "dtype": "<c16"}
    require(cfg["expected_core"] == expected_core, "ROOT declared core differs from exact table")
    rows = table["initial_rows"]
    allowed = cfg["allowed_attempt_ids"]
    require(allowed and len(allowed) == len(set(allowed)), "empty/duplicate row release")
    indices = [next((i for i, row in enumerate(rows) if row["attempt_id"] == name), -1) for name in allowed]
    require(-1 not in indices and indices == list(range(indices[0], indices[0] + len(indices))),
            "unknown/out-of-order/skipped rows")
    require(all(rows[i]["profile"] is False for i in indices), "profile/growth unadmitted")
    require(indices[0] > 0 or indices == [0], "initial release may name ONLY new row1")
    require(len(cfg["prior_eligible"]) == indices[0], "missing closed prior prefix/root continuation")
    require(indices[0] == 0 or cfg["continuation_authorized"] is True, "ROOT continuation absent")
    previous = []
    cfg["prior_owned"] = []
    source(cfg)
    window(cfg)
    for index, ref in enumerate(cfg["prior_eligible"]):
        boundary = pinned(ref)
        row = rows[index]
        require(boundary["status"] == "ELIGIBLE_PENDING_ROOT_SCIENTIFIC_REVIEW" and
                boundary["row"] == row and boundary["candidate"] == cfg["candidate"] and
                boundary["material_hashes"] == cfg["material_hashes"] and
                boundary["table_sha256"] == TABLE_SHA and boundary["method7"] == cfg["accepted_method7"] and
                boundary["source_sha256"] == cfg["binder_sha256"], "prior eligible exact-basis mismatch")
        condition = table["conditions"][row["condition_id"]]
        require(inventory(Path(boundary["raw_path"]), condition["operating_proposal"]["disk_proposal_bytes"]) ==
                boundary["raw_files"], "prior receipt/raw fingerprint changed")
        old_grant_sha = boundary["raw_files"]["grant.input"]["sha256"]
        hashes = eligible(cfg, row, condition, Path(boundary["raw_path"]), old_grant_sha)
        require(hashes == boundary["fingerprints"], "prior fingerprint disagreement")
        previous.append((row, condition, hashes))
        cfg["prior_owned"] += owned_markers(Path(boundary["raw_path"]))
    directory = Path(cfg["external_batch_directory"])
    require(not directory.resolve().is_relative_to(Path(cfg["root"]).resolve()), "progress must be external")
    directory.mkdir(exist_ok=False)
    try:
        for index in indices:
            row = rows[index]
            condition = table["conditions"][row["condition_id"]]
            hashes = run(cfg, row, condition, directory, previous)
            previous.append((row, condition, hashes))
            cfg["prior_owned"] += owned_markers(Path(cfg["root"]) / "docs/reports/reconstruction-working-set/raw" / row["attempt_id"])
        save(directory / "queue-boundary.json", {"status": "FIXED_RELEASE_COMPLETE_HOLD",
             "completed_ids": allowed, "remaining": "unreleased; ROOT owns continuation"})
    except BaseException as error:
        save(directory / "HOLD.json", {"status": "HOLD_WHOLE_QUEUE", "type": type(error).__name__,
             "reason": str(error), "completed_eligible_ids": [v[0]["attempt_id"] for v in previous],
             "ownership": "No signals/scans/automatic retry; any pending observer remains ROOT-owned"})
        raise


if __name__ == "__main__":
    main()
