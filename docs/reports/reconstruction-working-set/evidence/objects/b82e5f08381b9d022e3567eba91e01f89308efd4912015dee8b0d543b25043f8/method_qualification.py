"""Finite Q0/Q1 readiness slice; source preparation only until exact root release.

One case per invocation. Q2-Q5 are deferred: no workflow, synthetic science,
orphan topology, automatic retry/growth or accepted-method edits occur here.
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
    require(
        grant["approved"] is True and grant["scope"] == "WS116-Q0-Q1-method5-v1",
        "no exact method5 Q0/Q1 root release",
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
    require(set(grant["prerequisites"]) == set(case["requires"]), "prerequisites missing/extra")
    for name, evidence in grant["prerequisites"].items():
        path = Path(evidence["path"])
        require(obs.digest(path) == evidence["sha256"], "prerequisite receipt changed")
        prior = json.loads(path.read_text())
        require(prior["case"] == name and prior["status"] == PASS, "prerequisite incomplete/failed")
        require(prior["source_sha256"] == identities, "prerequisite source identity changed")
        require(
            prior["exposed_domain"] == grant["resource_domain"]["expected_exposed"],
            "prerequisite domain changed",
        )
    write(out / "preflight.json", obs.context(ROOT))
    return identities


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


def main():
    """Run exactly one released readiness case; preserve every failed attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=("Q0-context", "Q1-normal"), required=True)
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
        "protocol": "WS116-qualification-Q0-Q1-method5-v1",
        "case": args.case,
        "attempt_id": args.attempt_id,
        "status": "qualification_failed",
        "driver_pid": os.getpid(),
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
        result = (
            context_case(out, obs)
            if args.case == "Q0-context"
            else normal_case(out, grant, inventory["common_bounds"], obs, method)
        )
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
            "Parent death/spawn-marker gaps and Q2-Q5 are unqualified. "
            "Receipt excludes its own disk bytes. No retry; unresolved ownership "
            "blocks another case."
        )
        write(out / "receipt.json", receipt)
    return 0 if receipt["status"] == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
