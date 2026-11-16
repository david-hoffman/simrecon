"""PH118 external fixed-direct SOURCE binding of accepted116 method7.

UNAPPROVED / UNRELEASED / NEVER EXECUTED. No retries, growth or workflow dispatch.
Original method7 launch/wait/guard/RSS logic is unchanged in this external copy.
A future root-authored exact-case grant is evidence, not access control.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

_SOURCE_DIR = Path(__file__).resolve().parent
for _name, _expected in {
    "observer.py": "384b4f1a95ad135136c60b9bb750437fe72e5bbb1a94fc21bd7cc1ae14ff6c9e",
    "direct_binding.py": "7822b13257761fb535867b197eacd836e15607ff0a64754d0b2adc62bc4a1c87",
}.items():
    if hashlib.sha256((_SOURCE_DIR / _name).read_bytes()).hexdigest() != _expected:
        raise ValueError("fixed external method import source identity changed: " + _name)
sys.path.insert(0, str(_SOURCE_DIR))

import direct_binding
from direct_binding import child_outcome, material_hashes

from observer import (
    SESSION_BOOTSTRAP_SHA256,
    THREADS,
    FixedSessionLaunch,
    StartupError,
    bootstrap_failure,
    cgroup_ancestors,
    context,
    digest,
    mem_available,
    process_identity,
    process_sample,
    read,
)

for _name in ("observer", "direct_binding"):
    if Path(sys.modules[_name].__file__).resolve() != _SOURCE_DIR / (_name + ".py"):
        raise ValueError("external method import resolved outside frozen source directory")

HERE = Path(__file__).resolve().parent
ROOT = None  # Required literal --subject-root; no prospective117/118 default.
RSS_TERMINAL_CONFIRM_SECONDS = 0.05


def git(*args):
    """Read exact Git provenance without changing the worktree."""
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write(path, record):
    """Write one JSON evidence record without circular self-identification."""
    path.write_text(json.dumps(record, indent=2, default=str) + "\n")


def exposed_domain_admission(grant, cg):
    """Conditional admission in a mapped exposed domain, with external risk open."""
    domain = grant["resource_domain"]
    if (
        domain["scope"] != "WS116-exposed-domain-conditional-v1"
        or domain["external_ancestors"] != "unknown_unobservable"
        or not isinstance(domain["conditional_rationale"], str)
        or not domain["conditional_rationale"].strip()
    ):
        raise ValueError(
            "explicit exposed-domain conditional rationale/unknown external ancestors required"
        )
    if "hidden_ancestors_resolved" in grant:
        raise ValueError("obsolete hidden-host certainty flag is not a conditional-admission field")
    evidence = domain["correspondence_evidence"]
    observed = evidence["observed_at_unix_ns"]
    age_limit = evidence["maximum_age_seconds"]
    now = time.time_ns()
    if (
        type(observed) is not int
        or observed <= 0
        or observed > now
        or type(age_limit) not in (int, float)
        or not math.isfinite(age_limit)
        or age_limit <= 0
        or now - observed > age_limit * 1e9
    ):
        raise ValueError("actual-time domain correspondence evidence missing/stale")
    if digest(evidence["path"]) != evidence["sha256"]:
        raise ValueError("domain correspondence evidence bytes changed")
    if not isinstance(cg.get("namespace"), str) or not cg["namespace"]:
        raise ValueError("observable cgroup namespace identity unavailable")
    actual = {key: cg[key] for key in ("membership", "mount_root", "mount", "namespace")}
    actual["visible_memory_max"] = {
        row["path"]: row["memory.max"] for row in cg["visible_ancestors"]
    }
    if domain["expected_exposed"] != actual:
        raise ValueError("actual exposed membership/namespace/limits differ from mapped domain")
    for key in ("predicted_child_peak_bytes", "native_allocator_allowance_bytes", "reserve_bytes"):
        if type(domain[key]) is not int or domain[key] <= 0:
            raise ValueError("positive quantified conditional headroom component required: " + key)
    if (
        domain["predicted_child_peak_bytes"] + domain["native_allocator_allowance_bytes"]
        > grant["process_stop_bytes"]
    ):
        raise ValueError(
            "predicted child payload/envelope plus native allowance exceeds process stop"
        )
    finite = []
    for row in cg["visible_ancestors"]:
        current, maximum = row["memory.current"], row["memory.max"]

        def decimal(value):
            return isinstance(value, str) and re.fullmatch(r"[0-9]+", value) is not None

        if not decimal(current) or not (maximum == "max" or decimal(maximum)):
            raise ValueError("required exposed current/limit observations unusable")
        if maximum != "max":
            finite.append(int(maximum))
        if (
            int(current) + grant["process_stop_bytes"] + domain["reserve_bytes"]
            > grant["ancestor_stop_bytes"][row["path"]]
        ):
            raise ValueError("exposed current plus process stop and reserve exceeds ancestor stop")
    if not finite:
        raise ValueError("no finite observable exposed-domain memory bound")


def admit(grant):
    """Validate exact-case release, applicability and conditional resource admission."""
    if grant["numerical_release"] is not True or grant["accepted_112_then_115"] is not True:
        raise ValueError("accepted dependency and exact numerical release required")
    if (
        not grant["representation_preflight"]["accepted"]
        or not grant["representation_preflight"]["evidence"]
    ):
        raise ValueError("accepted integer/domain/actual-stencil preflight missing")
    if not grant["headroom_evidence"]:
        raise ValueError("conservative case-specific headroom evidence missing")
    for key in (
        "deadline_seconds",
        "process_stop_bytes",
        "host_min_available_bytes",
        "terminate_grace_seconds",
    ):
        if type(grant[key]) not in (int, float) or not math.isfinite(grant[key]) or grant[key] <= 0:
            raise ValueError("positive explicit safety setting required: " + key)
    if grant["sample_interval_seconds"] != 0.01:
        raise ValueError(
            "observer interval differs from manifest; revise manifest before execution"
        )
    if str(Path(sys.executable).resolve()) != grant["python_resolved"]:
        raise ValueError("interpreter differs from pinned grant")
    actual = {
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "tracked_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=ROOT)
        ).hexdigest(),
    }
    if actual != grant["candidate"] or material_hashes(ROOT) != grant["material_hashes"]:
        raise ValueError("candidate or material input identities changed")
    manifest = json.loads((HERE / "manifest.json").read_text())
    if (
        manifest["launch"]["bootstrap_sha256"] != SESSION_BOOTSTRAP_SHA256
        or grant["startup_timeout_seconds"] != manifest["launch"]["startup_timeout_seconds"]
        or type(grant["startup_pipe_bytes"]) is not int
        or grant["startup_pipe_bytes"] != manifest["launch"]["startup_pipe_bytes"]
    ):
        raise ValueError("fixed bootstrap identity/startup bounds differ from manifest")
    nonce = grant["launch_nonce"]
    if (
        not isinstance(nonce, str)
        or not 0 < len(nonce) <= 64
        or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for c in nonce
        )
    ):
        raise ValueError("bounded fixed-route nonce required")
    candidates = manifest["initial_conditions"]
    condition = next(row for row in candidates if row["id"] == grant["condition_id"])
    if grant["repetition"] not in manifest["repetitions"] or grant["profile"] is not False:
        raise ValueError("undeclared direct repetition or workflow profile requested")
    cg = cgroup_ancestors()
    if "error" in cg:
        raise ValueError(cg["error"])
    rows = cg["visible_ancestors"]
    if set(grant["ancestor_stop_bytes"]) != {row["path"] for row in rows}:
        raise ValueError("every visible effective ancestor needs explicit threshold")
    for row in rows:
        if row["memory.current"] is None or row["memory.max"] is None:
            raise ValueError("ancestor current/max unknown")
        threshold = grant["ancestor_stop_bytes"][row["path"]]
        if type(threshold) is not int or threshold <= 0:
            raise ValueError("ancestor threshold must be positive integer bytes")
        if threshold <= int(row["memory.current"]) or (
            row["memory.max"] != "max" and threshold >= int(row["memory.max"])
        ):
            raise ValueError("ancestor threshold does not leave declared current/limit margin")
    exposed_domain_admission(grant, cg)
    available = mem_available()
    if available is None or available <= grant["host_min_available_bytes"]:
        raise ValueError("host available memory does not satisfy admission")
    return {**condition, "profile": grant["profile"], "repetition": grant["repetition"]}, actual


class WaitOwner:
    """Only this object calls wait4 for this exact PID; no Popen object exists."""

    def __init__(self, pid):
        self.pid = pid
        self.terminal = None
        self.wait_lost = False
        self.nonterminal_wait_events = []

    def collect(self):
        """Collect exact-PID terminal usage once, retaining nonterminal notifications."""
        if self.terminal is not None:
            return self.terminal
        if self.wait_lost:
            raise RuntimeError("wait ownership lost; terminal usage unavailable")
        try:
            pid, status, usage = os.wait4(self.pid, os.WNOHANG)
        except InterruptedError:
            return None
        except ChildProcessError as error:
            self.wait_lost = True
            raise RuntimeError("child reaped elsewhere or auto-reaped; never infer peak") from error
        if pid == 0:
            return None
        if not (os.WIFEXITED(status) or os.WIFSIGNALED(status)):
            self.nonterminal_wait_events.append(
                {
                    "wait_status_raw": status,
                    "pid": pid,
                    "observed_monotonic_ns": time.monotonic_ns(),
                    "stopped": os.WIFSTOPPED(status),
                    "stop_signal": os.WSTOPSIG(status) if os.WIFSTOPPED(status) else None,
                }
            )
            return None  # A traced/stopped notification is not complete-child usage.
        self.terminal = {
            "pid": pid,
            "wait_status_raw": status,
            "returncode": os.waitstatus_to_exitcode(status),
            "exited": os.WIFEXITED(status),
            "signaled": os.WIFSIGNALED(status),
            "exit_code": os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
            "term_signal": os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
            "core_dumped": os.WCOREDUMP(status) if hasattr(os, "WCOREDUMP") else None,
            "reaped_monotonic_ns": time.monotonic_ns(),
            "rusage_native": {
                key: getattr(usage, key) for key in dir(usage) if key.startswith("ru_")
            },
            "ru_maxrss_native_units": "Linux KiB",
            "ru_maxrss_multiplier_to_bytes": 1024,
            "kernel_reported_direct_child_high_water_bytes": int(usage.ru_maxrss) * 1024,
            "scope": (
                "kernel-reported direct-child usage through final exit; inherited/pre-exec/"
                "exec-transition high-water retention unresolved; same PID does not guarantee "
                "every bootstrap/startup peak survives exec; no subtraction/aggregate/benefit claim"
            ),
        }
        return self.terminal

    def send(self, signum):
        """Signal only the still-owned direct PID, before or after session readiness."""
        # An unreaped direct child cannot have its PID recycled. Always collect
        # first; if another reaper invalidated ownership, do not signal a reused PID.
        if self.collect() is not None:
            return {"signal": signum, "delivery": "already_terminal"}
        try:
            os.kill(self.pid, signum)
            return {
                "signal": signum,
                "delivery": "direct_pid_sent",
                "monotonic_ns": time.monotonic_ns(),
            }
        except ProcessLookupError:
            return {
                "signal": signum,
                "delivery": "direct_pid_absent_race",
                "monotonic_ns": time.monotonic_ns(),
            }


def candidate_identity():
    """Capture HEAD, tree and tracked-patch identities separately from raw outputs."""
    return {
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "tracked_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "--binary", "HEAD"], cwd=ROOT)
        ).hexdigest(),
    }


def cleanup(owner, receipt, seconds):
    """Best-effort bounded kill/reap; an unreapable kernel task is an explicit gap."""
    if owner is None or owner.terminal is not None:
        return
    try:
        receipt.setdefault("signals", []).append(owner.send(signal.SIGKILL))
        until = time.monotonic() + seconds
        while owner.collect() is None and time.monotonic() < until:
            time.sleep(0.01)
        if owner.terminal is None:
            receipt["cleanup_gap"] = (
                "SIGKILL requested but terminal wait4 unavailable by cleanup deadline; "
                "coordinator must resolve owned PID before another attempt"
            )
    except BaseException as error:
        receipt["cleanup_gap"] = {
            "type": type(error).__name__,
            "message": str(error),
            "meaning": "wait/signal ownership unresolved; do not start another attempt",
        }


def independent_monitor_stop(sample, grant, now, deadline, startup_deadline, ready, parent_cgroup):
    """Keep non-RSS-absence guards active, before accepting a terminal confirmation."""
    if sample["child_cgroup"] != parent_cgroup:
        return "child_cgroup_missing_or_moved"
    if not ready and now >= startup_deadline:
        return "startup_readiness_timeout"
    if now >= deadline:
        return "timeout"
    rss = sample.get("VmRSS_bytes")
    if type(rss) is int and rss >= grant["process_stop_bytes"]:
        return "process_current_RSS_threshold"
    if (
        sample["host_available_bytes"] is None
        or sample["host_available_bytes"] <= grant["host_min_available_bytes"]
    ):
        return "host_headroom_missing_or_deteriorated"
    if any(
        value is None or int(value) >= grant["ancestor_stop_bytes"][path]
        for path, value in sample["ancestor_current_bytes"].items()
    ):
        return "cgroup_current_threshold_or_unknown"
    return None


def monitor_sample_decision(
    owner,
    sample,
    grant,
    receipt,
    *,
    deadline,
    startup_deadline,
    ready,
    parent_cgroup,
    clock=time.monotonic,
):
    """Confirm a missing/invalid RSS gap for at most 50ms; never quietly resume."""
    now = clock()
    rss = sample.get("VmRSS_bytes")
    unusable = type(rss) is not int or rss < 0
    gap = receipt.get("rss_terminal_confirmation")
    sample_ns = sample.get("monotonic_ns")
    stamp_error = None
    if unusable or gap is not None:
        if type(sample_ns) is not int or sample_ns <= 0:
            stamp_error = "missing, noninteger or nonpositive actual sample timestamp"
        elif sample_ns > math.ceil(now * 1e9):
            stamp_error = "actual sample timestamp is after helper entry"
        elif (
            gap is not None
            and gap["origin_monotonic_ns"] is not None
            and sample_ns < gap["origin_monotonic_ns"]
        ):
            stamp_error = "actual sample timestamp predates immutable gap origin"
    if unusable and gap is None:
        origin = sample_ns if stamp_error is None else None
        gap = {
            "bound_seconds": RSS_TERMINAL_CONFIRM_SECONDS,
            "origin_monotonic_ns": origin,
            "deadline_monotonic_ns": origin + 50_000_000 if origin is not None else None,
            "first_helper_entry_monotonic": now,
            "first_sample": dict(sample),
            "observations": [],
            "outcome": "pending",
            "meaning": "required RSS observation gap; cause unknown, not RSS=0 or proof of exit",
        }
        receipt["rss_terminal_confirmation"] = gap
    if gap is not None and stamp_error is not None:
        gap.setdefault("timestamp_errors", []).append(
            {
                "sample_monotonic_ns": sample_ns,
                "helper_entry_monotonic": now,
                "error": stamp_error,
            }
        )
        gap["sample_timestamp_invalid"] = True
        if gap["outcome"] == "pending":
            gap["outcome"] = "invalid_sample_timestamp"
    stop = independent_monitor_stop(
        sample, grant, now, deadline, startup_deadline, ready, parent_cgroup
    )
    if stop is not None:
        receipt.setdefault("stop_reason", stop)
        receipt.setdefault("last_sample", sample)
    if gap is not None:
        gap["last_sample"] = sample
    try:
        terminal = owner.collect()
    except BaseException as error:
        if gap is not None:
            if gap["outcome"] == "pending":
                gap["outcome"] = "ownership_lost_or_collection_interrupted"
            gap["collection_error"] = {"type": type(error).__name__, "message": str(error)}
        raise
    observed = clock()
    terminal_ns = terminal["reaped_monotonic_ns"] if terminal is not None else None
    # Collection itself may cross a deadline. Independent stops keep precedence.
    stop = stop or independent_monitor_stop(
        sample, grant, observed, deadline, startup_deadline, ready, parent_cgroup
    )
    if gap is not None:
        gap["observations"].append(
            {
                "monotonic": observed,
                "helper_entry_monotonic": now,
                "sample_monotonic_ns": sample_ns,
                "RSS_present": not unusable,
                "VmRSS_bytes": rss,
                "terminal_observed": terminal is not None,
                "terminal_collected_monotonic_ns": terminal_ns,
                "independent_stop": stop,
            }
        )
        if stop is not None:
            gap.setdefault("independent_stop", stop)
        if gap["outcome"] == "pending":
            if (
                terminal_ns is not None
                and gap["origin_monotonic_ns"] <= terminal_ns <= gap["deadline_monotonic_ns"]
            ):
                gap.update(
                    outcome="terminal_confirmed_with_visible_sampling_gap",
                    terminal_collected_monotonic_ns=terminal_ns,
                    confirmation_decision_monotonic=observed,
                )
            elif math.ceil(observed * 1e9) >= gap["deadline_monotonic_ns"]:
                gap.update(outcome="strict_required_RSS_failure", bound_reached_monotonic=observed)
        if gap["outcome"] == "strict_required_RSS_failure" or gap.get("sample_timestamp_invalid"):
            stop = stop or "required_process_RSS_observation_lost"
    if stop is not None:
        receipt.setdefault("stop_reason", stop)
        receipt.setdefault("last_sample", sample)
    return stop


def stopped_status(reason):
    """Classify the latched monitor cause without replacing it with a later event."""
    return (
        "startup_timeout_stopped"
        if reason == "startup_readiness_timeout"
        else "timeout_stopped"
        if reason == "timeout"
        else "monitor_stopped"
    )


def observe_session_readiness(receipt, ready, startup_deadline, *, clock=time.monotonic):
    """Preserve earliest stop and separately record an actual late readiness event."""
    observed = clock()
    if observed >= startup_deadline:
        prior = receipt.get("stop_reason")
        receipt.setdefault("stop_reason", "startup_readiness_timeout")
        receipt["late_session_readiness"] = {
            "observed_monotonic": observed,
            "startup_deadline_monotonic": startup_deadline,
            "prior_stop_reason": prior,
            "primary_stop_reason": receipt["stop_reason"],
            "readiness": dict(ready),
        }
        raise StartupError("session readiness arrived after startup deadline")


def observer_exception_status(receipt, error):
    """Keep an earlier stop primary when a subsequent readiness error unwinds main."""
    if isinstance(error, KeyboardInterrupt):
        return "observer_cancelled"
    if isinstance(error, StartupError) and "stop_reason" in receipt:
        return stopped_status(receipt["stop_reason"])
    if receipt.get("stop_reason") == "startup_readiness_timeout":
        return "startup_timeout_stopped"
    return {
        "admission": "admission_refused",
        "startup_prepare": "startup_fd_prepare_failure",
        "startup_readiness": "startup_readiness_failure",
        "spawn": "spawn_failure",
    }.get(receipt["phase"], "observation_failure")


def observed_child_status(receipt, terminal, outcome, identity_matches, boot_error):
    """Apply the existing final status precedence after actual child parsing."""
    if boot_error is not None:
        return "bootstrap_" + boot_error["stage"] + "_failure"
    if "stop_reason" in receipt:
        return stopped_status(receipt["stop_reason"])
    if terminal["signaled"]:
        return "child_signaled"
    if outcome in {
        "missing_child_record",
        "malformed_child_record",
        "child_record_exceeds_admitted_parse_bound",
    }:
        return outcome
    if not identity_matches or outcome == "material_identity_failure":
        return "material_identity_failure"
    if outcome == "nonfinite_scientific_failure":
        return "nonfinite_scientific_failure"
    if outcome == "direct_adapter_exception":
        return "direct_adapter_exception_unclassified"
    if outcome == "observation_failure":
        return "child_observation_failure"
    if terminal["returncode"] != 0:
        return "child_nonzero_exit"
    if outcome != "finite_observation_pending_qualification":
        return "child_observation_failure"
    return "complete_child_observed_pending_scientific_qualification"


def main():
    """Run one admitted child, preserve every outcome and never retry automatically."""
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", type=Path, required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--subject-root", type=Path, required=True)
    args = parser.parse_args()
    ROOT = args.subject_root.resolve()
    if not args.attempt_id or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for c in args.attempt_id
    ):
        raise ValueError("safe unique attempt id required")
    out = HERE / "raw" / args.attempt_id
    out.mkdir(parents=True, exist_ok=False)
    receipt = {
        "protocol": "PH118-direct-attempt-SOURCE-v1",
        "status": "admission_started",
        "phase": "admission",
        "observer_pid": os.getpid(),
        "started_monotonic_ns": time.monotonic_ns(),
        "signals": [],
    }
    owner = None
    launch = None
    grant = {}
    spec = None
    try:
        # Preserve exact grant bytes even if JSON/admission is invalid.
        import shutil

        shutil.copyfile(args.grant, out / "grant.input")
        receipt["grant_sha256"] = digest(out / "grant.input")
        grant = json.loads((out / "grant.input").read_text())
        direct_binding.check_release(grant, ROOT)
        write(out / "preflight.json", context(ROOT))
        if sys.platform != "linux" or not hasattr(os, "wait4") or not hasattr(os, "posix_spawn"):
            raise ValueError("Linux stdlib wait4/posix_spawn route unavailable")
        if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise ValueError("default SIGCHLD required; no handler/auto-reaper allowed")
        if signal.getsignal(signal.SIGINT) is not signal.default_int_handler:
            raise ValueError(
                "default Python SIGINT handler required for supported one-shot cancellation"
            )
        for key in ("kill_reap_seconds", "max_child_record_bytes"):
            if (
                type(grant[key]) not in (int, float)
                or not math.isfinite(grant[key])
                or grant[key] <= 0
            ):
                raise ValueError("positive explicit method safety setting required: " + key)
        if type(grant["max_child_record_bytes"]) is not int:
            raise ValueError("child JSON parse bound must be integer bytes")
        receipt["candidate_pre_admission"] = candidate_identity()
        receipt["material_hashes_pre_admission"] = material_hashes(ROOT)
        spec, identity = admit(grant)
        direct_binding.prepare_spec(grant, spec)
        hashes_before = material_hashes(ROOT)
        spec["expected_material_hashes"] = hashes_before
        spec["expected_exposed_domain"] = grant["resource_domain"]["expected_exposed"]
        target_argv = direct_binding.target_argv(grant, spec, ROOT)
        spec["launch"] = {
            "route": "plain-spawn/same-pid-setsid/execve",
            "bootstrap_sha256": SESSION_BOOTSTRAP_SHA256,
            "nonce": grant["launch_nonce"],
            "startup_timeout_seconds": grant["startup_timeout_seconds"],
            "startup_pipe_bytes": grant["startup_pipe_bytes"],
            "target_argv": target_argv,
        }
        write(out / "spec.json", spec)
        receipt.update(
            candidate_before=identity,
            material_hashes_before=hashes_before,
            resource_domain_admission=grant["resource_domain"],
            wait_owner="single os.wait4(exact_pid,WNOHANG), no waitpid/Popen/aggregate waits",
            spawn_route="plain posix_spawn; fixed same-PID setsid/readiness/execve bootstrap",
            launch=spec["launch"],
            interpreter={
                "executable": sys.executable,
                "resolved": str(Path(sys.executable).resolve()),
                "version": sys.version,
            },
            sigchld_handler="SIG_DFL",
            effective_cwd=str(ROOT),
            direct_record_binding={
                "protocol": "PH118-direct-v1",
                "stdout": "exclusive redirected FD of exact owned bootstrap/exec PID",
                "self_pid_nonce_spec": "absent in unchanged adapter; not fabricated",
                "metadata_git_abort_ownership": "future reviewed proof required; no current qualification",
                "self_snapshot_scope": "pre_target/target_return/final_whole_process; last is before JSON/teardown",
            },
        )
        env = os.environ.copy()
        env.update({key: "1" for key in THREADS})
        # Preserve the qualified source-free environment; do not replace it with src.
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        receipt["child_environment_controls"] = {
            key: env.get(key)
            for key in (
                *THREADS,
                "PYTHONPATH",
                "PYTHONDONTWRITEBYTECODE",
                "PYTHONMALLOC",
                "MALLOC_ARENA_MAX",
            )
        }
        receipt["phase"] = "startup_prepare"
        # chdir is parent-only before spawn, avoiding preexec_fn or another child.
        os.chdir(ROOT)
        with (
            (out / "stdout.json").open("x") as stdout,
            (out / "stderr.log").open("x") as stderr,
            (out / "samples.jsonl").open("x") as samples,
        ):
            receipt["observer_pre_spawn_snapshot"] = __import__("observer").rusage_snapshot(
                "parent before posix_spawn; not subtracted from child peak"
            )
            launch = FixedSessionLaunch(
                target_argv,
                env,
                grant["launch_nonce"],
                stdout.fileno(),
                stderr.fileno(),
                grant["startup_pipe_bytes"],
            )
            write(
                out / "spawn-intent.json",
                {
                    "attempt_id": args.attempt_id,
                    "observer_identity": process_identity(os.getpid()),
                    "target_argv": target_argv,
                    "bootstrap_argv": launch.argv,
                    "file_actions": launch.actions,
                    "fd_plan": launch.fd_plan,
                    "bootstrap_sha256": SESSION_BOOTSTRAP_SHA256,
                    "spec_sha256": digest(out / "spec.json"),
                    "grant_sha256": receipt["grant_sha256"],
                    "scope": (
                        "intent only, not proof whether spawn occurred; "
                        "coordinator resolves any marker gap"
                    ),
                },
            )
            receipt["spawn_start_monotonic_ns"] = time.monotonic_ns()
            receipt["phase"] = "spawn"
            pid = launch.spawn()
            owner = WaitOwner(pid)
            launch.release_parent_writers()
            write(
                out / "owned-child.json",
                {
                    "attempt_id": args.attempt_id,
                    "observer_pid": os.getpid(),
                    "workload_pid": pid,
                    "child_identity": process_identity(pid),
                    "session_status": "unverified until bounded readiness",
                    "target_argv": target_argv,
                    "bootstrap_argv": launch.argv,
                    "spec_sha256": digest(out / "spec.json"),
                    "grant_sha256": receipt["grant_sha256"],
                    "scope": (
                        "owned child marker, not terminal receipt; "
                        "missing identity fields require coordinator discovery"
                    ),
                },
            )
            receipt.update(
                workload_pid=pid,
                phase="startup_readiness",
                spawn_return_monotonic_ns=time.monotonic_ns(),
            )
            deadline = receipt["spawn_start_monotonic_ns"] / 1e9 + grant["deadline_seconds"]
            startup_deadline = (
                receipt["spawn_start_monotonic_ns"] / 1e9 + grant["startup_timeout_seconds"]
            )
            term_at = None
            kill_at = None
            count = 0
            while True:
                terminal = owner.collect()
                if launch.ready is None:
                    ready = launch.drain()  # Drain buffered readiness even after cached exit.
                    if ready is not None:
                        observe_session_readiness(receipt, ready, startup_deadline)
                        write(out / "session-ready.json", ready)
                        receipt["session_ready"] = ready
                        receipt["phase"] = "observation"
                if terminal is not None:
                    if launch.ready is None:
                        raise StartupError("terminal exit without verified session readiness")
                    gap = receipt.get("rss_terminal_confirmation")
                    if gap is not None:
                        # No post-terminal /proc RSS/cgroup value is invented. Keep
                        # the last actual child sample, label fresh host/ancestor
                        # observations separately and check all decision guards.
                        guard_sample = dict(gap["last_sample"])
                        guard_sample["host_available_bytes"] = mem_available()
                        guard_sample["ancestor_current_bytes"] = {
                            path: read(Path(path) / "memory.current")
                            for path in grant["ancestor_stop_bytes"]
                        }
                        gap["cached_terminal_guard_refresh"] = {
                            "monotonic_ns": time.monotonic_ns(),
                            "child_fields": (
                                "last actual sample, not a new post-terminal observation"
                            ),
                            "host_available_bytes": guard_sample["host_available_bytes"],
                            "ancestor_current_bytes": guard_sample["ancestor_current_bytes"],
                        }
                        stop = monitor_sample_decision(
                            owner,
                            guard_sample,
                            grant,
                            receipt,
                            deadline=deadline,
                            startup_deadline=startup_deadline,
                            ready=launch.ready is not None,
                            parent_cgroup=read("/proc/self/cgroup"),
                        )
                        if stop is not None:
                            receipt.setdefault("stop_reason", stop)
                            receipt.setdefault("last_sample", gap["last_sample"])
                    if time.monotonic() >= deadline:
                        receipt.setdefault("stop_reason", "timeout")
                        receipt["deadline_observed_after_exit"] = True
                    break
                sample = process_sample(pid)
                sample["child_cgroup"] = read(f"/proc/{pid}/cgroup")
                sample["ancestor_current_bytes"] = {
                    path: read(Path(path) / "memory.current")
                    for path in grant["ancestor_stop_bytes"]
                }
                samples.write(json.dumps(sample) + "\n")
                samples.flush()
                count += 1
                stop = monitor_sample_decision(
                    owner,
                    sample,
                    grant,
                    receipt,
                    deadline=deadline,
                    startup_deadline=startup_deadline,
                    ready=launch.ready is not None,
                    parent_cgroup=read("/proc/self/cgroup"),
                )
                now = time.monotonic()
                if stop and term_at is None:
                    receipt.setdefault("stop_reason", stop)
                    receipt["last_sample"] = sample
                    receipt["signals"].append(owner.send(signal.SIGTERM))
                    term_at = now
                if owner.terminal is not None:
                    continue  # Drain readiness and finalise any visible gap at loop top.
                if (
                    term_at is not None
                    and kill_at is None
                    and now - term_at >= grant["terminate_grace_seconds"]
                ):
                    receipt["signals"].append(owner.send(signal.SIGKILL))
                    kill_at = now
                if kill_at is not None and now - kill_at >= grant["kill_reap_seconds"]:
                    raise TimeoutError("terminal wait4 missing after KILL reap deadline")
                time.sleep(grant["sample_interval_seconds"])
            receipt["sample_count"] = count
        receipt["terminal"] = owner.terminal
        outcome, child_record = child_outcome(
            out / "stdout.json", grant["max_child_record_bytes"], owner.pid, spec
        )
        receipt["child_outcome"] = outcome
        receipt["child_record_sha256"] = digest(out / "stdout.json")
        receipt["candidate_after"] = candidate_identity()
        receipt["material_hashes_after"] = material_hashes(ROOT)
        identity_matches = (
            receipt["candidate_after"] == receipt["candidate_before"]
            and receipt["material_hashes_after"] == receipt["material_hashes_before"]
        )
        receipt["material_identity_matches"] = identity_matches
        boot_error = bootstrap_failure(out / "stderr.log")
        if boot_error is not None:
            receipt["bootstrap_error"] = boot_error
        receipt["status"] = observed_child_status(
            receipt, owner.terminal, outcome, identity_matches, boot_error
        )
        if receipt["status"] in (
            "missing_child_record",
            "malformed_child_record",
            "child_record_exceeds_admitted_parse_bound",
        ):
            receipt["child_parse_diagnostic"] = child_record
    except BaseException as error:
        status = observer_exception_status(receipt, error)
        receipt.update(status=status, error_type=type(error).__name__, error_message=str(error))
    finally:
        if owner is None and launch is not None and launch.pid is not None:
            owner = WaitOwner(
                launch.pid
            )  # First owner after a returned-PID interruption, not a second reaper.
            receipt["returned_pid_cleanup_owner_created"] = True
        cleanup(owner, receipt, grant.get("kill_reap_seconds", 1) if isinstance(grant, dict) else 1)
        if launch is not None:
            launch.close()
            (out / "startup-readiness.bin").write_bytes(launch.data)
            receipt["startup_fd_plan"] = launch.fd_plan
            receipt["startup_eof_observed"] = launch.eof
            receipt["startup_parent_fds_closed"] = not launch.opened
            boot_error = bootstrap_failure(out / "stderr.log")
            if boot_error is not None:
                receipt["bootstrap_error"] = boot_error
                if receipt["status"] == "startup_readiness_failure":
                    receipt["status"] = "bootstrap_" + boot_error["stage"] + "_failure"
        if owner is not None:
            receipt["terminal"] = owner.terminal
            receipt["wait_ownership_lost"] = owner.wait_lost
            receipt["nonterminal_wait_events"] = owner.nonterminal_wait_events
        receipt["finished_monotonic_ns"] = time.monotonic_ns()
        try:
            receipt["candidate_final"] = candidate_identity()
            receipt["material_hashes_final"] = material_hashes(ROOT)
            if "candidate_before" in receipt and (
                receipt["candidate_final"] != receipt["candidate_before"]
                or receipt["material_hashes_final"] != receipt["material_hashes_before"]
            ):
                receipt["material_identity_matches"] = False
                if receipt["status"] == "complete_child_observed_pending_scientific_qualification":
                    receipt["status"] = "material_identity_failure"
            receipt["postflight"] = context(ROOT)
            receipt["observer_self_snapshot"] = __import__("observer").rusage_snapshot(
                "parent after child/cleanup, excludes receipt serialization"
            )
            receipt["files_before_receipt"] = {
                p.name: {
                    "sha256": digest(p),
                    "logical_bytes": p.stat().st_size,
                    "allocated_bytes": p.stat().st_blocks * 512,
                }
                for p in out.iterdir()
                if p.is_file()
            }
        except BaseException as error:
            receipt["postflight_gap"] = {"type": type(error).__name__, "message": str(error)}
            if receipt["status"] == "complete_child_observed_pending_scientific_qualification":
                receipt["status"] = "complete_child_observation_incomplete"
        receipt["limits"] = (
            "Terminal wait4 is kernel-reported direct-child usage through final exit. "
            "Inherited/pre-exec/exec-transition high-water retention remains unresolved; same PID "
            "does not guarantee every bootstrap/startup peak survives exec. No subtraction/"
            "aggregate/benefit claim. Target self snapshots are separate; "
            "no numerical descendants. Direct-PID cleanup only. PID1 is not a general reaper; "
            "abrupt-parent/spawn-marker gaps "
            "remain. Sampling/stops can overshoot. "
            "File inventory excludes receipt itself; coordinator collects final disk sizes/hash "
            "externally. No retry."
        )
        write(out / "receipt.json", receipt)
    return (
        0
        if receipt["status"] == "complete_child_observed_pending_scientific_qualification"
        and "cleanup_gap" not in receipt
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
