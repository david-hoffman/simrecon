# WS116 narrow static-method review input

Review the unexecuted source method only. This is not scientific report acceptance,
experiment admission, accepted #115 verification, gate readiness or evidence of
runtime capability. The coordinator launches a fresh reviewer sequentially, with
no investigator history. Reviewer owns a separately named report, never repairs
these sources and never delegates. #115 gate has the exclusive resource window:
no Python, probes, imports, lint/types/tests, install, benchmarks, numerical work,
new tool execution or rebase. Read-only shell source/diff inspection is sufficient.

Context: original source draft is Git commit
`701b56d349adaf5e719510a158b51402876f9c30`; original main intake baseline is
`b344e41a8b52de76d7cbbf8450319893904c3b8f`. Accepted #112 → #115 experiment
identity and release are pending coordinator binding. Root supplied contextual
#112/#115 progress; this method revision establishes no new accepted baseline.
There are zero numerical trials; actual model/effort, tokens and cost are unknown.
No earlier artifact, correction or charge is reset.

## Exact review surface

- `run_attempt.py`: admission/material identities, posix_spawn file actions and
  setsid, sole exact-PID wait4 owner, monitor, TERM/KILL/exception cleanup,
  statuses/JSON matching, receipts and disk/self-identity scope.
- `workload_child.py`: one workflow/caller lifetime, pre-call/call-end/
  post-observation high-water snapshots, streamed input/result observations,
  finite/status/identity semantics and JSON boundary.
- `observer.py`: canonical array-byte identity, bounded finite checks/file hashes,
  scalar stage wrapper, RSS/cgroup/host facts and cumulative snapshot semantics.
- `manifest.json`: unchanged 20 initial conditions/three repeats and distinct
  unprofiled/profile-control design; source-only method v2 annotations.
- `README.md`: claimed boundaries/reproduction, prerequisites and required grants.
- This input and the coordinator's `method-refinement-packet.md` provide review
  scope. Contract/task/initial packet are permitted context. Existing frozen
  `tests/reconstruction_memory_benchmark.py` and
  `tests/reconstruction_summary_fixture.py` are read-only lineage references.
  Product source is permitted only where needed to challenge the method.

The coordinator provides exact candidate/diff/file digests outside these tracked
bytes. Do not hash this file into itself or turn the review report into another
Current state.

## Claims to challenge from source

1. The parent uses no Popen workload object and no workload poll/waitpid/aggregate
   wait, so its only workload reaper is `WaitOwner.collect` via
   `os.wait4(exact_pid,WNOHANG)`. It caches terminal usage/status once. Repeated
   calls return cached data, nonterminal notifications remain nonterminal, and
   unexpected ChildProcessError explicitly loses evidence/ownership. Independent
   git subprocesses are provenance work, not workload waits.
2. posix_spawn plus setsid is an intended Linux route, not demonstrated support.
   The parent checks default SIGCHLD and signals the process group only while
   ownership remains valid. TERM grace, KILL-reap and exception cleanup are bounded;
   rare unkillable/unreapable children leave an explicit gap rather than success.
   Such a gap requires coordinator PID/resource resolution before another attempt.
3. Terminal rusage is the direct child's maximum process RSS through exit,
   including JSON/teardown; it excludes external observer memory and is no
   concurrent aggregate or numerical-only measure. No numerical grandchildren
   are commissioned. Parent pre-spawn and named child snapshots disclose relevant
   inherited/pre-exec high-water limitations; no subtraction claims isolation.
4. The child runs one workflow with caller case and one result. It never invokes
   a simultaneous reference/baseline reconstruction. Canonical array identities
   preserve frozen shape/dtype/endian/content meaning without whole-volume
   tobytes copies. Converted/finite scratch is bounded; frozen public-value
   fingerprinting streams buffers. Hash/traversal/provenance work remains part
   of cumulative and terminal memory, outside call-only timing where declared.
5. Admission refusal, spawn/parent observation failure, child observation or
   workflow exception, nonfinite result, signal/timeout/monitor stop, malformed/
   missing/oversized child JSON, identity change and successful finite observation
   are distinguishable. Exit zero is not scientific qualification. Before/after
   source/tool hashes and exact spec/PID checks protect applicability, not an
   engineered security boundary. Raw output survives even when parsing is refused.
6. Unprofiled fresh-process corpus and profiled stage attribution/perturbation
   controls stay separate. Observer stage closure retains scalars, not frames or
   arrays; its import mask is explicit. No automatic retry/growth exists. Any
   future correction updates frozen identities and explicitly revisits affected
   evidence; later #117/#118 refresh before #119/#120 remains required.
7. Receipt inventories hash files before receipt creation, excluding itself.
   Coordinator terminal receipt hash/final logical+allocated disk accounting is
   external, without circular self-hash or mutation of old attempts.

## Concrete questions and remaining runtime work

Identify source defects in lifecycle, exception cleanup, output matching,
canonical endian/strided/empty identity handling or bound claims. Does any status
permit a missing terminal rusage, changed material identity or incomplete record
to masquerade as successful observation? Are all scopes/costs described precisely?
Separate a static defect from a runtime question; no fabricated execution result.

Later explicitly released validation must establish pinned interpreter/platform/
backend identities and actual posix_spawn/setsid/wait4 behavior, normal/signal/
TERM/KILL/timeout/exception and missing/malformed output handling, canonical hash
agreement with frozen meaning across contiguous/strided/endian/empty arrays,
actual sampling gaps, ancestor resolution and observer perturbation. These are
outstanding validation obligations, not permission to run now. Final scientific
qualification/review and full Ubuntu make verify remain separate later gates.

Artifacts are durable report work. This source refinement created no numerical
process, fixture or disposable scratch. A temporary replacement source file was
renamed to `run_attempt.py`; no temporary file is intended to remain. No commit,
push, publication or cleanup of unrelated work is authorized.

## Correction after independent static review 1: fresh delta review

Read-only source review 1 is retained externally at
`/workspace/work/campaign/evidence/116/static-method-review-1.md`, SHA256
`9a4452afddd4e4d53e47f2b4990f0a268bd3f7c3216e60ae54a739ed99b4b81c`.
The coordinator correction packet SHA256 is
`5ea52473b8d472fe0746e7b084c70d45b080eea3c4aae4d8c85d1894c5d47825`.
All six exact reviewed source files were independently hash-verified before any
correction, then preserved by the coordinator in
`/workspace/work/campaign/evidence/116/source-method-v2-review1/`. Original v1 Git
history, v2 bytes, first review, diagnosed corrections and all charges remain;
this is no reset or claim of acceptance. A fresh reviewer assesses the delta.

| Finding | Narrow source correction and claimed invariant | Pending qualification |
| --- | --- | --- |
| F1: missing RSS treated as zero | `observer.process_sample` emits explicit null/unusable field diagnostics; after the terminal-race check, runner stops on missing/noninteger/negative RSS using `required_process_RSS_observation_lost`. Integer zero remains distinguishable. Samples and terminal status survive. | Live-child missing/unusable/zero RSS and exit-race handling, ordinary escalation and raw preservation. |
| F2: null snapshots/omitted success fields accepted | Runner `validate_complete_record` explicitly requires child-v2 snapshot values/units/conversion/scope/time/counters, ordered call timing and derived elapsed, required array/value identities, branch structure, actual environment/resource/retention/stage fields and exact materials. A null snapshot or missing required field raises malformed/incomplete observation; finite structural status is still no scientific qualification. | Original null-snapshot/omitted-field counterexample and representative incomplete/malformed/valid records, without new numerical tolerances. |
| C1: parent SIGTERM bypasses finally | Runner requires default SIGINT, records spawn intent/early owned-child identities, and classifies KeyboardInterrupt as `observer_cancelled` through existing bounded cleanup. README binds one-shot SIGINT and concrete identity-verified coordinator recovery for TERM/abrupt death/marker gaps. Observer disappearance never establishes workload termination. | Supported cancellation, repeated/abrupt interruption, missing/partial marker and cautious recovery; unresolved ownership blocks another trial. |

Review the explicit completeness checks as the known protocol's observation
schema, not a generic validation framework or scientific oracle. Does any null,
missing or unusable required value still permit complete-observation status?
Do F1 checks distinguish zero from unknown after checking the terminal race?
Does cancellation/discovery evidence make owned processes discoverable without
assuming stale PID ownership or recoverable terminal usage after parent death?
Challenge the explicit spawn-to-marker/abrupt-death limitations rather than
claiming a Python handler eliminates them. Inspect normal paths for regressions.

Precision correction: a conversion buffer and a tobytes chunk can coexist;
1 MiB is a per-chunk/buffer parameter, not a total observation-scratch ceiling.
Terminal wait4 max-process scope remains distinct from snapshots and aggregate
process-tree memory. All code and operational paths remain unexecuted. Do not run
the counterexample, helper or qualification cases during this static delta review.

## Narrow correction after static review 2: fresh affected-scope review 3

Review 2 is retained at
`/workspace/work/campaign/evidence/116/static-method-review-2.md`, SHA256
`f339a8853d16a28f1c2682a6ccc23a8c612fc1a24e9e85a0045da855c5dfa5e0`.
Correction packet 2 SHA256 is
`54cb1e0a4ddfeef8c5ccbb8d99c09d6f857afeeaab986d45fda2cc64caba740d`.
The coordinator preserved all six exact reviewed files under
`/workspace/work/campaign/evidence/116/source-method-v2-corrected-review2/` before
this correction. That snapshot, earlier sources, both independent reviews and
all charges remain unchanged. Review 2 found F1 statically satisfactory and C1's
operational disposition sufficient for this narrow source purpose; neither
mechanism was redesigned. All runtime limitations remain.

| Finding | Known-protocol correction | Normal and negative source questions for fresh review |
| --- | --- | --- |
| F2a: unpaired/truncated stage stream, zero/out-of-call timestamps | Runner compares profile events with the exact flat workflow mask: declaration, optional layout, preparation, estimation, each reconstruction time 0..T-1, result; paired ordered edges and applicable indices. Every timestamp is positive/in-call/nondecreasing; cumulative stage high-water is bounded by its surrounding snapshots. | Does the one-event/zero-time example fail? Do missing/extra/unpaired/reordered stages, wrong time coverage/indices and out-of-call times fail? Are ordinary T1/T2/T4 profile streams, optional-layout and unprofiled empty streams retained? |
| F2b: arbitrary required resource/snapshot scope text | Required ancestor current is ASCII nonnegative decimal; max is ASCII nonnegative decimal or `max`. Optional peak/events/swap null/unknown observations remain explicit. Exact named snapshot meanings are shared in observer.SNAPSHOT_SCOPES and used by both child and validator. | Do `unknown` required current/max or wrong scope fail? Do zero/current decimal values, legitimate `max`, optional nulls and the actual emitted scope strings remain valid? |
| F2c: impossible dtype encodings | Small pure-Python legal kind/width/byteorder definition shared by identity helper and validator: byte-independent b1/i1/u1; little-endian i/u2/4/8, f2/4/8/16 and c8/16. Retention permits legal actual big-endian multibyte backings separately. | Do `<f1`, `|b16`, invalid widths and noncanonical multibyte identity byteorders fail? Do legal canonical identities and actual retained big-endian metadata remain supported without importing NumPy in the external parser? |

The child now imports shared scope strings; their emitted text and snapshot
boundaries are unchanged. Canonical hashing algorithms and buffer/lifetime costs,
RSS-loss handling, cancellation/recovery, wait ownership and terminal peak scope
are retained. The schema changes describe legal identity encodings, not a new
precision path, tolerance or scientific oracle. Finite record completeness is
still no branch/output recovery proof or report acceptance.

These source questions are not executed examples. Runtime qualification remains
unreleased: actual spawn/wait/reap, signal/recovery, hash equivalence, complete
record parsing, sampling/perturbation and environment/headroom must be checked
later under an explicit grant. Before any data freeze, reconcile the stage mask,
dtypes and resource interfaces against the accepted integrated parent and refresh
all changed material identities. Later #117/#118 affected-evidence refresh before
#119/#120 reliance remains required. No source review certifies a newer base.
