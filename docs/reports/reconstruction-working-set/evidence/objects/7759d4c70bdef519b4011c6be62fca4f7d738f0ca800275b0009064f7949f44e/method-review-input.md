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
