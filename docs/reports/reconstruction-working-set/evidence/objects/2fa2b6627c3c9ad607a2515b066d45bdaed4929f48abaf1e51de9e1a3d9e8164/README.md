# WS116 source-only experiment preparation

These are **unexecuted analysis drafts**, initially prepared at provisional public-main
`b344e41a8b52de76d7cbbf8450319893904c3b8f`. They provide no measured working set,
successful qualification, experiment admission, ranking, independent acceptance
or passing check claim. The [task](../../tasks/reconstruction-working-set.md)
owns Current state; this report does not create another status store. #112 holds
the numerical window, and accepted #115 plus coordinator release are prerequisites.

Files: [fixed corpus](manifest.json), [liveness calculations](analysis/liveness-draft.md),
[one-attempt runner](run_attempt.py), [child](workload_child.py),
[observer](observer.py), [handoff hypotheses](handoffs/source-hypotheses.md).
`raw/` will retain every attempt, grant, preflight, sample stream, output/error and
receipt. It is currently empty. No Python, imports, lint, types, tests, numerical
experiment, benchmark, install or full verification was executed in preparation.
The runner is not yet parsed, validated or reviewed and must not be treated as a
ready experiment tool until the later released session diagnoses it. Source-only
method revision v2 adds complete-child wait ownership, bounded array identities,
explicit snapshot/status scopes and a separate static-method review input. The
original draft is preserved in Git at `701b56d349adaf5e719510a158b51402876f9c30`;
no prior attempt, charge or correction is reset. This method refinement remains
on that source-preparation baseline; root's reports about #112/#115 do not bind
an accepted experiment baseline or release numerical work.

## Fixed workload and generator meaning

The initial manifest declares 20 mode/search conditions, each with three fresh
process repetitions (60 unprofiled calls). It is not a Cartesian product. Separate
profile controls use central searched full/summary and the eventual exact largest
safe searched full/summary conditions, three each. If full growth is refused,
retain that refusal and use the largest separately admitted matched full case;
never silently change the intended comparison. Freeze this manifest/tooling
revision before execution. Source-preparation `not_run` fields are historical
annotations: later attempt outcomes belong only in raw receipts and derived tables,
not in edits to a material manifest between repeats. Any material correction
requires a new version identity and an explicit affected-evidence decision.

The child reuses frozen `tests/reconstruction_summary_fixture.py` directly and
RM84 hashing/retention helpers from `tests/reconstruction_memory_benchmark.py`.
It extends no frozen allowlist. At specifically admitted 192/256 lateral sizes it
calls the same workload generator with only Y/X changed; initial and witness shapes
remain exact. Optics are wavelength 500 nm, NA=1, immersion=1. The object is
`30+3cos(2π(x/X+y/Y))+2sin(2π(2x/X-y/Y))+cos(2π(z/Z+3x/X))`
`+0.75cos(2π(3y/Y+x/X))`. Illumination has fundamental amplitude `0.31+t/64`,
second harmonic `0.13+t/128`, spatial phase `2π(x cosθ+y sinθ)/8`,
`θ=dπ/D`, phase step `2πp/5`, second-harmonic phase offset 0.3; detector counts
include `d/4+t/8` and round into float32. Transfer uses exact dyadic asymmetric
complex samples `1+m/16+r/128+i(m+r+a)/256`, radial `(O,64,K)` with
`K=16` for 3d and 1 for native 2d, frequency increments 0.125 cycles/µm.
Full constants/declarations and identity semantics remain in the frozen file.
Supplied conditions fit modulation with known initial carriers; searched T0 uses
search and T>0 uses time0 carrier reuse while fitting current-time modulation.
Expected branches are `known`, or T0 `searched` and later `time0-reused`.

Witnesses are frozen `scenario` definitions, not fitted from results:
`2d` uses `(T,D,Z,Y,X)=(2,2,1,12,16)`;
`off1/off2` use `(2,3,4,16,16)`, calibrated camera/maps/equalization, 1 or 2
raw off exposures `raw/8`, dxy=0.1 µm and positive combine selectors;
`between` uses `(2,3,4,12,12)` with direction-major between drift;
`within` uses `(2,4,4,12,12)` with fitted within drift, adjusted phases and
explicit timestamps/header phases. Actual hashes, branch/finite qualification
and current-baseline applicability are pending. Hashes do not prove physical
recovery or replace inherited scientific expectations.

## Later reproduction and admission

The coordinator must first pin the accepted #112 → #115 base, 64-bit Ubuntu
worktree `.venv`, dependency/import health and numerical window. Reread changed
source/dtype/domain policy, fix diagnosed draft-tool defects within report scope,
and independently review instrumentation before relying on measurements. No
product/tests/fixtures/gates/lock/RM84 evidence edits are commissioned.

For each single attempt the coordinator supplies one JSON grant. Required fields:

- `numerical_release: true`, `accepted_112_then_115: true`, `condition_id`,
  `repetition` (1–3), `profile` (boolean), and exact `python_resolved` path.
- `candidate`: exact `head`, `tree` and SHA256 `tracked_diff_sha256` of raw
  `git diff --binary HEAD` stdout; `material_hashes`: path→SHA256 mapping from
  `observer.material_hashes(root)`, covering all product Python sources, lock,
  frozen fixture/benchmark and manifest/tooling. Untracked output paths do not
  enter candidate comparison. Untracked relevant source/tooling bytes do enter
  material hashes. Raw grant/preflight files therefore cannot invalidate every
  subsequent match merely by existing.
- `representation_preflight: {accepted:true,evidence:...}` with actual accepted
  signed32/unsigned32/native-intp products, output extents and transfer stencils
  calculated without allocating a proposed volume; accepted representation is
  separate from allocation safety.
- `headroom_evidence`: smaller measured envelopes, conservative co-live estimate,
  native/allocator allowance, host/caller/observer reserve and budget rationale;
  `hidden_ancestors_resolved:true` only with effective host/namespace ancestor
  resolution evidence. Root cgroup files alone are insufficient. A missing or
  unsupported cgroup interface is a refusal requiring a declared observer revision.
- Positive `deadline_seconds`, `process_stop_bytes`, `host_min_available_bytes`,
  `terminate_grace_seconds`, `kill_reap_seconds`, and integer
  `max_child_record_bytes`; `sample_interval_seconds:0.01`; and
  `ancestor_stop_bytes` mapping **every visible ancestor absolute path** to a
  conservative current-memory threshold strictly between current and finite max
  where a finite max exists. No numbers are supplied by this draft because actual
  admitted headroom is unknown.
- For growth only: explicit `declared_growth_conditions`,
  `growth_separate_admission:true` and `smaller_measured_evidence`; only primary
  `(1,3,8,192,192)` then `(1,3,8,256,256)` are supported by this draft. Summary
  supplied precedes searched. Full comparisons require their own admission.
  The coordinator enforces ordering/evidence; this is no automated scheduler.

Example later command, **not executed and not currently authorized**:

```sh
.venv/bin/python docs/reports/reconstruction-working-set/run_attempt.py \
  --grant /absolute/coordinator-approved-grant.json \
  --attempt-id central64-summary-searched-unprofiled-r1
```

No batch CLI, implicit growth or retry exists. One invocation launches one child,
sets all four declared thread controls to 1 before startup, captures stdout/stderr,
records preflight and samples, and stops the owned process group on a deadline,
process RSS threshold, ancestor current-memory threshold or host-headroom loss.
Every attempt directory is new; reuse is refused. A stopped/failed attempt needs
classification/diagnosis before another grant. No deliberate OOM or swap rescue.
The external monitor can race or overshoot and cannot guarantee zero OOM risk.
The source uses `os.posix_spawn(..., setsid=True)` to avoid creating a `Popen`
object with destructor or signal-helper reaping paths. The only workload wait
owner calls `os.wait4(exact_pid, WNOHANG)` and caches one terminal status/rusage.
There is no `Popen.poll/wait/communicate/send_signal`, aggregate wait or numerical
grandchild. Signals use `os.killpg` after checking cached/terminal ownership.
Default SIGCHLD is required; unexpected auto-reaping loses terminal evidence and
does not authorize signaling an unowned/reused PID. TERM grace and KILL-reap periods
are bounded, including exception cleanup. A still-unreaped kernel task is an
explicit cleanup gap requiring coordinator resolution before another attempt.
An inaccessible post-exit /proc sample is not a fabricated stop: terminal wait
collection is checked again after sampling. Exact spawn/setsid/wait4/units and
signal behavior remain runtime validation questions; no capability probe ran.
No experiment may overlap campaign numerical work, installation or verification.

## Measurement meanings and review

The parent records Linux wait4 terminal native `ru_maxrss` in KiB and multiplies
by 1024 for `terminal.complete_child_peak_bytes`. This describes the awaited
direct child through exit, including JSON serialization and teardown. It is a
maximum resident process size, not a sum of concurrent child/thread/observer
memory, numerical-only allocation, or a guarantee of a new workstation envelope.
No numerical grandchildren are commissioned. Inherited/pre-exec high-water and
kernel/libc accounting limits remain explicit qualification questions; never
subtract the parent or baseline to invent an isolated numerical peak.

Child `snapshots.pre_call`, `snapshots.call_end` and
`snapshots.post_observation` retain native values, converted cumulative bytes,
monotonic timestamps and scope. They include work through their query only.
Post-observation covers hashing/finite/retention/context/identity collection,
but excludes subsequent JSON/teardown, covered separately by terminal wait4.
Sampled RSS/HWM and these cumulative snapshots are distinct observations.
Call time brackets only the workflow invocation; profiled brackets include stage
observer work inside the call. Never subtract pre-call high-water and call it
isolated workflow memory. Page faults/swap/block-I/O are context, not allocation
ownership. Parent observer memory/CPU is outside child RSS but consumes headroom.
Receipt disk counts/hashes cover files existing before receipt serialization and
exclude its own bytes. Post-run directory disk accounting remains a separate required
collection, using both logical and allocated bytes without mutating old evidence.

Array identities preserve frozen RM84 name/shape/little-endian dtype/content
meaning while streaming C-order bytes in bounded chunks; the child never calls
the frozen fixture's whole-array `identity(...tobytes())`. Contiguous arrays use
zero-copy memoryview chunks; conversion and finite-check scratch are bounded by
1 MiB chunks. The frozen `public_value_sha256` uses direct memoryview content
without a contiguous copy or buffered 65536-element conversion for noncontiguous/
endian data; those protocol meanings remain unchanged. It hashes declarations,
caller input and one result, never launches a baseline/reference workflow. Hashing,
finite checks, retained-array metadata and provenance still consume memory/time
and contribute to the corresponding snapshots and complete-child high-water.

Receipts separate `admission_refused`, `spawn_failure`, `observation_failure`,
`timeout_stopped`, `monitor_stopped`, `child_signaled`, missing/malformed/oversized
child records, nonfinite outcomes, workflow exceptions, identity changes and
nonzero child exits. A well-formed finite child plus exit zero, terminal rusage
and matched before/after material identities yields only
`complete_child_observed_pending_scientific_qualification`. Exit status is raw
process evidence; it never establishes searched/witness meaning or report
acceptance. Raw wait status, decoded normal exit/signal and actual-time context
are retained. JSON/spec/PID and required success snapshots are checked; invalid
stdout is preserved without treating a guessed value as a missing measurement.
Grant bytes survive admission failure. Identity capture before admission, before
spawn and after observation binds source/tooling bytes without self-hashing the
receipt or silently editing the frozen manifest. Runtime failure classifications
remain pending diagnosis by their named owners.

Profile runs patch only `simrecon.workflow.reconstruct`'s imported
`workflow_stage` context manager: declaration, optional layout, preparation,
estimation, each time reconstruction, result. They do **not** instrument every
independent import of that context manager (for example transfer contexts), nor
individual hidden FFT/ufunc allocations. Observer closure retains scalar stage,
time index, timestamp and cumulative high-water dictionaries only, no frames,
locals or arrays. External 10 ms `/proc` RSS samples and ancestor/host samples
provide association, miss short peaks, and add monitor overhead. Effective sample
gaps/counts must be derived from actual timestamps; requested cadence is no claim
of guaranteed 10 ms sampling. Stage enter/exit high-water is cumulative; sampled
stage maxima and source-calculated payload are different quantities.

Match unprofiled/profiled inputs, common output hashes and branch tuples per
condition before any attribution claim; report call-time/RSS medians and ranges,
all three repeats, observer cost and unresolved perturbation. Public full/summary
fingerprints differ structurally; compare `common_output_sha256` and declared
output/parameter fields between entry modes. Reject observer-altered outputs or
branches, preserve the failed observation, and commission a corrected observer.
The child checks common numeric fields for finiteness; reviewer must assess branch
and witness meaning, not accept exit status as scientific qualification. Result
retention counts unique NumPy roots; metadata remains an incomplete estimate.

## Evidence gaps and later refresh

Original `artifacts/rm84/` is absent in this worktree (read-only inventory during
preparation); no tracked RM84 artifact paths were returned by `git ls-files`.
Frozen source definitions are present. Historical raw repeats/receipts are therefore
not available here and are neither regenerated nor inferred. The absent path
inventory command returned status 2; this is missing evidence, not a numerical
failure. Preserve any originals later supplied with their original candidate/input
meaning. No largest demonstrated case or measured next-size boundary exists yet.

W01: manifest and source identity plan prepared, actual receipts pending.
W02: provisional calculated liveness prepared, observed attribution pending.
W03/W04: finite contrasts and witnesses declared, all executions/qualification pending.
W05: scalar stage observer and separate control plan drafted, perturbation unknown.
W06: explicit per-attempt preflight/stop design, no case admitted.
W07: current dtype payload arithmetic separated from precision predictions.
W08: hypotheses only; measured ranking and individual final handoffs pending.
W09: fresh scientific review, full Ubuntu `make verify` and exact-candidate final
acceptance are coordinator-owned future gates, with no pass claimed.

Later accepted #117/#118 changes require a narrow affected-family liveness,
contrast and observer-control refresh plus fresh independent review before
#119/#120 design relies on those claims. Preserve this baseline's evidence;
never silently relabel it. Source-only artifacts are durable report work. No
scratch fixtures, numerical child process or other persistent owned process was
created in this stage; read-only shell commands have completed. No commit/push/
publication. Actual model/effort, tokens, cost, CPU/wall usage and host accounting
are unknown except where the coordinator/host records them. No human numeric cap
is set; the three-repeat design is not such a cap.
