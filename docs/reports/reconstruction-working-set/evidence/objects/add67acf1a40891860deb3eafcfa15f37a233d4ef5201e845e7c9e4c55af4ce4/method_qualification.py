"""Finite Q0/Q1 plus four small Q2 cases; exact root release is still required.

One case per invocation. No workflow, orphan topology, Q4/Q5 execution,
automatic retry/growth or accepted-method edits occur here.
"""

from __future__ import annotations

import argparse
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
    if grant["case"] in Q2_CASES:
        required.add("docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt")
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
    expected_scope = "WS116-Q2-lifecycle-v1" if args.case in Q2_CASES else "WS116-Q0-Q1-method5-v1"
    require(grant["approved"] is True and grant["scope"] == expected_scope,
            "no exact qualification phase release")
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
    if args.case in Q2_CASES:
        require(identities["docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt"] ==
                inventory["lifecycle_target_sha256"], "Q2 target fixture digest differs from inventory")
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
    if args.case in Q2_CASES:
        require(grant["prerequisites"] == {}, "Q2 uses the one explicit retained-Q1 mapping")
        retained = retained_q1(grant, identities, obs)
        write(out / "retained-Q1-applicability.json", retained)
    else:
        require(set(grant["prerequisites"]) == set(case["requires"]), "prerequisites missing/extra")
        for name, evidence in grant["prerequisites"].items():
            path = Path(evidence["path"])
            require(obs.digest(path) == evidence["sha256"], "prerequisite receipt changed")
            prior = json.loads(path.read_text())
            require(prior["case"] == name and prior["status"] == PASS, "prerequisite incomplete/failed")
            require(prior["source_sha256"] == identities, "prerequisite source identity changed")
            require(prior["exposed_domain"] == grant["resource_domain"]["expected_exposed"],
                    "prerequisite domain changed")
    write(out / "preflight.json", obs.context(ROOT))
    return identities


def retained_q1(grant, current, obs):
    """Retain one exact passed Q1 only for six explicitly unchanged inputs."""
    evidence = grant["retained_method5_Q1"]
    receipt_path = QUAL / "attempts/q1-method5-a1/receipt.json"
    life_path = QUAL / "attempts/q1-method5-a1/normal-lifecycle.json"
    require(Path(evidence["receipt_path"]).resolve() == receipt_path.resolve() and
            evidence["receipt_sha256"] == "23534b9f0298fd2de621a6e2b8b0b7bb993d9ce094d3d716aefdd5b29d7016ce" and
            obs.digest(receipt_path) == evidence["receipt_sha256"], "retained Q1 receipt not exact accepted evidence")
    require(Path(evidence["lifecycle_path"]).resolve() == life_path.resolve() and
            evidence["lifecycle_sha256"] == "b6997727dea0d12fe5d497d335f0f2fb483aa44273e997a5380223f197fe729a" and
            obs.digest(life_path) == evidence["lifecycle_sha256"], "retained Q1 lifecycle bytes changed")
    prior = json.loads(receipt_path.read_text())
    life = json.loads(life_path.read_text())
    require(prior["status"] == PASS and prior["case"] == "Q1-normal" and
            prior["attempt_id"] == "q1-method5-a1", "retained Q1 outcome not successful")
    require(all(prior["source_sha256"][key] == current[key] for key in RETAINED_METHOD_KEYS),
            "accepted method/old fixture/lock changed: retain no Q1 applicability")
    require(life["bootstrap_sha256"] == obs.SESSION_BOOTSTRAP_SHA256 and
            life["terminal"]["wait_status_raw"] == 0 and life["startup_parent_fds_closed"] is True and
            not life.get("cleanup_gap"), "retained bootstrap/normal/ownership evidence incomplete")
    require(prior["exposed_domain"] == grant["resource_domain"]["expected_exposed"],
            "retained Q1 domain no longer corresponds")
    return {"scope":"unchanged method/bootstrap/old normal fixture/lock only; no full new-driver success",
        "receipt_sha256":evidence["receipt_sha256"], "lifecycle_sha256":evidence["lifecycle_sha256"],
        "unchanged_source_sha256":{key:current[key] for key in RETAINED_METHOD_KEYS},
        "prior_driver_sha256":prior["source_sha256"]["docs/reports/reconstruction-working-set/method_qualification.py"],
        "new_driver_sha256":current["docs/reports/reconstruction-working-set/method_qualification.py"],
        "prior_inventory_sha256":prior["source_sha256"]["docs/reports/reconstruction-working-set/qualification/inventory.json"],
        "new_inventory_sha256":current["docs/reports/reconstruction-working-set/qualification/inventory.json"],
        "new_fixture_sha256":current["docs/reports/reconstruction-working-set/qualification/fixtures/lifecycle-target-v1.txt"]}


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
    argv = [sys.executable, "-c", fixture.read_text(), mode, grant["launch_nonce"],
            str(bounds["target_self_exit_seconds"])]
    record = {"case":case_name, "mode":mode, "target_argv":argv,
        "fixture_sha256":obs.digest(fixture), "signals":[], "expected_terminal_signal":expected_signal,
        "scope":"tiny stdlib handling only; no scientific or comparative memory result"}
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
    write(out / "spawn-intent.json", {"observer":obs.process_identity(os.getpid()),
        "target_argv":argv, "fixture_sha256":record["fixture_sha256"], "intent_only":True})
    try:
        with (out / "stdout.json").open("x") as stdout, (out / "stderr.log").open("x") as stderr, (out / "samples.jsonl").open("x") as samples:
            launch = obs.FixedSessionLaunch(argv, os.environ.copy(), grant["launch_nonce"],
                stdout.fileno(), stderr.fileno(), bounds["startup_pipe_bytes"])
            record.update(bootstrap_sha256=obs.SESSION_BOOTSTRAP_SHA256, bootstrap_argv=launch.argv,
                          file_actions=launch.actions, fd_plan=launch.fd_plan)
            write(out / "fixed-route-intent.json", record)
            pid = launch.spawn()
            owner = method.WaitOwner(pid)
            launch.release_parent_writers()
            record["workload_pid"] = pid
            write(out / "owned-child.json", {"identity":obs.process_identity(pid),
                "observer_pid":os.getpid(), "nonce":grant["launch_nonce"], "target_argv":argv})
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
                    require(raw.count(b"\n") == 1 and raw.endswith(b"\n"), "target readiness malformed/multiple")
                    target_ready = json.loads(raw)
                    require(bootstrap is not None and now < readiness_deadline, "target ready without timely bootstrap")
                    require(target_ready.get("role") == "holding-target" and target_ready.get("pid") == pid and
                            target_ready.get("ppid") == os.getpid() and target_ready.get("pgid") == pid and
                            target_ready.get("session_id") == pid and target_ready.get("nonce") == grant["launch_nonce"] and
                            target_ready.get("executable") == grant["python_resolved"] and target_ready.get("mode") == mode,
                            "target identity/session/nonce/mode mismatch")
                    require(type(target_ready.get("term_handler_native")) is int and
                            target_ready["term_handler_native"] == (1 if mode == "ignore-term" else 0) and
                            target_ready.get("self_exit_backstop_seconds") == bounds["target_self_exit_seconds"],
                            "target handler/backstop not observed before control action")
                    record.update(target_ready=target_ready, target_ready_monotonic_ns=time.monotonic_ns())
                    write(out / "target-ready.json", target_ready)
                terminal = owner.collect()
                if terminal is not None:
                    break
                sample = obs.process_sample(pid)
                sample["ancestor_current_bytes"] = {path:obs.read(Path(path) / "memory.current")
                    for path in grant["ancestor_stop_bytes"]}
                sample["child_cgroup"] = obs.read(f"/proc/{pid}/cgroup")
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                if owner.collect() is not None:
                    continue
                require(type(sample.get("VmRSS_bytes")) is int and sample["VmRSS_bytes"] >= 0,
                        "required live-child RSS observation lost")
                require(sample["VmRSS_bytes"] < grant["process_stop_bytes"] and
                        sample["host_available_bytes"] is not None and sample["host_available_bytes"] > grant["host_min_available_bytes"],
                        "process/host safety stop")
                require(sample["child_cgroup"] == obs.read("/proc/self/cgroup") and
                        all(value is not None and int(value) < grant["ancestor_stop_bytes"][path]
                            for path,value in sample["ancestor_current_bytes"].items()), "cgroup safety stop")
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
                    record.update(deadline_decision_monotonic_ns=time.monotonic_ns(), stop_reason="declared_target_deadline")
                    record["signals"].append(owner.send(signal.SIGTERM))
                    term_at = now
                    record["term_requested_monotonic_ns"] = time.monotonic_ns()
                if now >= overall_deadline:
                    record["overall_timeout"] = True
                    if term_at is None:
                        record["signals"].append(owner.send(signal.SIGTERM))
                        term_at = now
                if term_at is not None and kill_at is None and now - term_at >= bounds["term_grace_seconds"]:
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
            error = {"type":type(caught).__name__, "message":"unexpected observer interruption"}
    except BaseException as caught:
        error = {"type":type(caught).__name__, "message":str(caught)}
    finally:
        if owner is None and launch is not None and launch.pid is not None:
            owner = method.WaitOwner(launch.pid)
        method.cleanup(owner, record, bounds["kill_reap_seconds"])
        if launch is not None:
            launch.close()
            (out / "startup-readiness.bin").write_bytes(launch.data)
            record["startup_parent_fds_closed"] = not launch.opened
            record["startup_eof_observed"] = launch.eof
        record.update(error=error, terminal=owner.terminal if owner is not None else None,
                      wait_ownership_lost=owner.wait_lost if owner is not None else None,
                      elapsed_seconds=time.monotonic() - started)
        write(out / "small-lifecycle.json", record)
    require(error is None and "cleanup_gap" not in record and owner is not None and
            owner.terminal is not None and not owner.wait_lost and record.get("startup_parent_fds_closed") is True,
            "lifecycle observation/cleanup failed; unresolved ownership blocks next case")
    require(record.get("control_preconditions_observed") is True and target_ready is not None and
            not record.get("overall_timeout") and record["elapsed_seconds"] < bounds["life_deadline_seconds"],
            "expected control route not reached/collected within bounds")
    terminal = owner.terminal
    require(owner.collect() is terminal and terminal["term_signal"] == expected_signal and
            terminal["signaled"] and not terminal["exited"], "expected reaped signal outcome mismatch")
    if case_name == "Q2-supported-sigint":
        require(cancellation_requested and cancellation_observed and
                any(s["signal"] == signal.SIGKILL and s["delivery"] == "direct_pid_sent" for s in record["signals"]),
                "supported SIGINT did not enter actual owned cleanup")
    else:
        require(any(s["signal"] == signal.SIGTERM and s["delivery"] == "direct_pid_sent" for s in record["signals"]),
                "no actual owned TERM request observed")
        if case_name == "Q2-ignore-term-kill":
            require("no_terminal_after_TERM_grace_monotonic_ns" in record and
                    any(s["signal"] == signal.SIGKILL and s["delivery"] == "direct_pid_sent" for s in record["signals"]),
                    "TERM-ignore grace/KILL route not observed")
        if case_name == "Q2-deadline":
            require(record.get("stop_reason") == "declared_target_deadline" and
                    record["deadline_decision_monotonic_ns"] >= record["target_deadline_monotonic_ns"],
                    "declared deadline decision missing")
    require(terminal["ru_maxrss_native_units"] == "Linux KiB" and
            terminal["kernel_reported_direct_child_high_water_bytes"] == terminal["rusage_native"]["ru_maxrss"] * 1024,
            "kernel terminal units/conversion mismatch")
    return {"lifecycle_file":"small-lifecycle.json", "expected_control_outcome":case_name,
        "terminal":terminal, "scope":"scoped handling pass, not child exit0 or scientific memory proof"}


def main():
    """Run exactly one released readiness case; preserve every failed attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("Q0-context", "Q1-normal", *Q2_CASES), required=True)
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
    out = QUAL / "attempts" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    receipt = {
        "protocol": "WS116-qualification-phase-small-v2",
        "case": args.case,
        "attempt_id": args.attempt_id,
        "status": "qualification_failed",
        "driver_pid": os.getpid(),
        "interpreter": {"version":sys.version, "executable":sys.executable,
                        "resolved":str(Path(sys.executable).resolve())},
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
        if args.case in Q2_CASES:
            require(not any(name == "numpy" or name.startswith("numpy.") or name == "scipy" or name.startswith("scipy.")
                            for name in sys.modules), "Q2 scientific module import forbidden")
            result = small_lifecycle_case(args.case, out, grant, inventory["common_bounds"], obs, method)
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
            "Parent death/spawn-marker gaps, abrupt-loss recovery, Q4/Q5 and science are unqualified. "
            "Receipt excludes its own disk bytes. No retry; unresolved ownership "
            "blocks another case."
        )
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
