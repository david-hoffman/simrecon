# LESSONS-READER-PARENT-01: external-evidence reservation prerequisite

**Version 1.0.** Git versions revisions. Intake for
[issue #100](https://github.com/david-hoffman/simrecon/issues/100), finding
`LESSONS-DOCTOR-01-F002`. This record defines the task and its scoped disposition;
synthetic prerequisite evidence is distinct from full environment qualification.

## Contract

The human instruction is `/intake 100` on November 11, 2026. Complete intake and
prepare narrow execution/review packets for the issue's proposed documentation
remedy. Reuse the approved [project](../PROJECT.md) and [intake procedure](../../.agents/skills/intake/SKILL.md).
No executable tests or product code are part of this intake.

The subsequent human instruction, **“Get a pr up”**, authorizes execution of this
documentation remedy, its isolated demonstration, required checks, commit/push
and pull-request publication. It does not expand fixture/cache ownership or
authorize merge, release, issue closure or unrelated external messages.

The intended outcome is a reproducible manual prerequisite for verification with
external protocol observations. Select explicit parent preparation as the first
remedy. Automatic preparation is deferred: neither the observed failure nor this
intake authorizes changing fixture/cache lifecycle behavior. The issue identifies
an environment prerequisite gap, not a scientific product defect.

Baseline: commit `b05fc782522a81ebd92c10726dac731a26e5a026`, tree
`fc37b2d7da10fc84a8b90682d765020c18c7fca7`, initially clean. Use one task per
worktree. The intake branch is `codex/intake-100-reader-reservation-parent` in the
current checkout. Execution must confirm its actual baseline before reuse.

### Doctor-origin handoff and integration

Preserve the original task ID `LESSONS-READER-PARENT-01`, finding
`LESSONS-DOCTOR-01-F002`, and source observation ID
`20261103T020523Z-ce03-coordinator-external-protocol-lock-parent`. The
[original intake](https://github.com/david-hoffman/simrecon/blob/d48e0e47b315e79a8c8ab33bc81b3f7f235e3c3c/docs/tasks/lessons-reader-reservation-parent.md),
[issue draft](../reports/lessons-doctor-2026-11-11/F002-issue.md),
[doctor probe](../reports/lessons-doctor-2026-11-11/reader-lock-probe.json), and
[prior F002 handling](../lessons/dispositions/20261111T182059Z-lessons-doctor-01-coordinator-b10-tracked.md)
identify the same prerequisite gap. The doctor's original task records its
owner-authorized priority, policy route, synthetic controls, proposed author/
reviewer settings and parent-diagnosis charges. Its source bytes remain in Git;
this record continues its sole correction execution state, not a second task.

Main advanced to `d48e0e47b315e79a8c8ab33bc81b3f7f235e3c3c` (PR #101) during
the first candidate's full verification. It adds that original intake/probe and
lesson-disposition guidance; runtime, tests/fixtures, scripts/devtools, Make,
dependencies and workflows are unchanged. The add/add task-record conflict is
reconciled here, retaining the doctor's provenance/constraints and this session's
authorization, contract, observed evidence and every attempt. The original
suggested reader-environment/PROJECT documentation ownership was proposed, not a
separate human instruction. This intake selects the existing verification
environment procedure plus its verification pointer to place the prerequisite
with its callers and avoid duplicating reader-authentication or PROJECT guidance.
The independently reviewed policy route and preservation/gate conditions remain.

The [new F002 handling record](../lessons/dispositions/20261112T035346Z-reader-parent-100-coordinator-prerequisite-tracked.md)
is scoped only to this candidate and the earlier F002 tracked entry. It leaves
F003 and source-observation confidence untouched. The requested docs and controls
are supplied; integrated-candidate checks/review and human PR integration remain
explicit conditions. Revisit on changed fixture paths/lifecycle, contradictory
environment evidence or altered prerequisite docs; broader qualification and
automatic fixture preparation require their own scope.

### Observed facts and evidence limits

- [Fixture declarations](../../tests/shared_node_baseline_public_callers_fixture.py)
  set `EVIDENCE` to the checkout's
  `artifacts/baseline-compatibility-20261013/A09` and `CACHE` to
  `artifacts/imagej-reader`. `SIMRECON_PROTOCOLS_EVIDENCE` changes only `RUN`,
  which appends `authored-runs/RUN_ID`. The shared lock deliberately stays fixed.
- `ReaderReservation.__init__` creates `RUN`. Its `__enter__` first calls
  `self.lock.mkdir()` without creating parents, before cache inventory or rename.
  Consequently an absent fixed parent with external `RUN` raises
  `FileNotFoundError`; an existing lock remains an exclusive-reservation blocker.
  These are source observations during intake, not newly executed results.
- The [CE03 lesson](../lessons/20261103T020523Z-ce03-coordinator-external-protocol-lock-parent.md)
  records 15 affected failures and 15 unchanged focused passes after preparing
  the empty parent. Its external receipts were not opened in this intake.
- The [existing disposable lifecycle helper](../../tests/test_shared_node_baseline_public_callers.py)
  substitutes `CACHE`, `EVIDENCE` and `RUN`, prepares its own evidence parent, and
  checks restored contents, inode and mode. It does not exercise the absent
  fixed-parent case.
- During the initial intake on `b05fc78`, the original doctor probe and intake
  were absent locally and their default-branch reads returned 404. After PR #101
  reached main, both became available and were opened. The retained doctor probe
  records the same fixture digest and three synthetic conditions: absent parent,
  successful prepared-parent restoration, and existing-lock rejection. This
  supersedes only the earlier availability limit; it is not a new execution or
  proof that unavailable original private receipts were recovered. Doctor charges
  remain linked through [its task](lessons-doctor-first-pass.md), including nine
  delegated launches for that separate parent task; do not double-count them as
  this correction's launches. Complete historical metering remains unknown.

### Requirements and boundary inventory

- **R1 — explicit prerequisite and invocation.** The environment procedure names
  the coordinator/operator as owner of preparing the parent from the intended
  worktree root, before any reservation-using focused tests or full verification
  with external protocol observations. The proposed existing command is
  `mkdir -p artifacts/baseline-compatibility-20261013/A09`. It targets the parent
  only. Explain `SIMRECON_PROTOCOLS_EVIDENCE` with an absolute external directory,
  the appended run subdirectories, and a concrete invocation carrying the same
  override into the intended checks. Ordinary preflight, Python/uv/JDK identity
  and locked setup remain required.
- **R2 — isolated observed demonstration.** On the project Python 3.13.12, use the
  unchanged current `ReaderReservation` with all three globals (`RUN`, `EVIDENCE`,
  `CACHE`) redirected before instantiation to disposable synthetic paths. Keep
  `RUN` outside the synthetic fixed-parent tree. Demonstrate absent-parent errno
  2 before cache movement, then prepare only that parent and demonstrate normal
  entry/unwinding. Retain commands, interpreter/platform, fixture digest, path
  layout, exit statuses and observations in a durable directory outside the
  checkout. This is a diagnostic demonstration, not a new regression suite or
  a reusable executable helper.
- **R3 — preservation and exclusion.** For successful unwinding compare original
  synthetic cache contents/inventory, root inode and mode; establish no leftover
  owned backup or lock. Separately demonstrate rejection of a preexisting
  synthetic lock, preserving its identity/content and the cache. Never use the
  real reader cache or create/remove a live reservation lock in the demonstration.
  Other setup failures remain diagnosed blockers, with their original status;
  do not turn parent preparation into lock removal or cache recovery.
- **R4 — narrow documentation ownership.** The documentation author owns only
  [environment.md](../operations/environment.md), a concise pointer/invocation in
  [verification.md](../operations/verification.md), and disposition/evidence in
  this task. Temporary diagnostic material stays outside tracked source/tests.
  The coordinator also owns the named append-only F002 handling record above,
  reconciled against main's existing disposition format and reviewed independently.
  Runtime, tests/fixtures, workflows, Make targets, dependencies, skills, delivery
  policy, cache data and lock semantics remain outside this remedy's ownership.
- **R5 — gates, evidence and scope.** External protocol observations do not move
  the canonical receipt/log/coverage outputs from their documented checkout
  locations. Preserve the 13 full-verification phases, two-worker grouping,
  report integrity, same-run M25 measurement and supported-platform requirements.
  Distinguish a successful synthetic prerequisite demonstration, a focused check,
  and a passing full exact-candidate gate. A failed gate remains failed. Neither
  issue closure nor this intake constitutes completed qualification.

| Scenario | Distinct outcome | Expectation source | Evidence/review mapping |
| --- | --- | --- | --- |
| S1 | External protocol observations change `RUN`; the shared lock remains under the fixed worktree parent. | R1, fixture declarations | Author documents concrete invocation; reviewer checks paths and environment propagation, including unchanged receipt destinations. |
| S2 | Missing synthetic fixed parent raises `FileNotFoundError`/errno 2 before cache movement. | R2, current `__enter__` | Isolated before-preparation observation with unchanged cache identity/content and no backup/lock. |
| S3 | Preparing only the parent permits reservation entry and normal unwinding. | R1–R3, current lifecycle | Isolated prepared-parent observation; existing-parent preparation is an equivalent idempotence example, not new lock behavior. |
| S4 | Normal unwinding restores the original synthetic cache contents, root inode and mode and leaves no owned backup/lock. | R3, current lifecycle | Before/after inventory and identities; fresh reviewer challenges preservation evidence. |
| S5 | A preexisting synthetic lock rejects entry and is preserved with the untouched cache. | R3, exclusive `mkdir` | Separate existing-lock observation, including lock identity/content and no cache movement. |
| S6 | Parent preparation or another prerequisite failing stops dependent work without deleting locks or repairing caches. | R3, environment procedure | Documented failure handling; no permission/error-injection suite or unrelated recovery claim. |
| S7 | Documentation and scoped disposition preserve all gates and claim only the observed qualification level. | R4–R5, project verification policy | Exact diff, evidence boundaries and independent policy review. |

There are seven distinct scenarios. Coverage-example count is not fixed by intake;
the author records actual demonstrated cases. No numeric scenario or review cap
was set by the human. Invalid path/permissions and operation-time failures keep
their existing meanings; no new API, numerical convention or rejection rule is
introduced. Default evidence placement remains compatible.

### Route, coverage, checks and completion

Use the **policy-documentation route**, with a named documentation author and a
fresh independent policy reviewer, because this remedy changes verification
instructions and the issue expressly requires policy review. It is not a fixture
repair. A report-only diagnostic may use the existing class on synthetic owned
data; any executable fixture/cache lifecycle change returns to separately scoped
intake and the applicable risk route. Data-loss behavior remains high risk.

Inherit [the approved coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance):
behavior coverage with independent risk review; native statement/branch percentages
are advisory, with no selected percentage target. All existing report-integrity,
per-package/per-platform, never-imported/subprocess and full-gate obligations
remain. No runtime/test obligations change, so do not invent product-red tests or
percentage-driven assertions for this documentation task.

Relevant intake checks are source/issue cross-checks, Markdown relative links and
`git diff --check`. Execution adds the isolated demonstration and review of its
preservation evidence. Before opening/reopening a PR, or pushing to an open PR,
the default clean exact-candidate full-local `make verify` gate applies, following
cheap environment preflight. No CI-authoritative exception is selected. Record
final hashes/results outside verified tracked bytes; do not update a verified
candidate merely to write its own hash.

Project model selection calls for `gpt-6.1-sol` at high effort for the future
documentation author/policy reviewer; calibration beyond the recorded narrow
scope remains unmeasured. Record actual attribution and unavailable measurements
as unknown. Escalate only a diagnosed reasoning/tooling limitation or material
outside-scope behavior; do not silently switch route or weaken evidence.

Completion of the remedy requires the named docs, observed S2–S5 evidence,
reviewer acceptance and an evidenced scoped disposition. Intake completion is
separate. PR publication follows the subsequent explicit instruction above;
merge, release, issue closure and unrelated external messages remain unauthorized.

## Narrow execution packets

**Documentation author.** You are the assigned author; work directly without
launching another role. Read AGENTS, the intake skill, this contract, the named
environment/verification/reader-environment documents and the narrowly relevant
current fixture/lifecycle helper. Confirm baseline, interpreter, lock and actual
tool identities before the demonstration. Edit only the R4 documents. Use
temporary material under a task-owned `work/` directory outside the checkout;
retain durable evidence separately outside the checkout. Redirect all fixture
paths before instantiation, and verify that none resolves to real cache/lock
paths. Do not call reader preparation, downloads, `seed`, or subprocess readers
to demonstrate this parent prerequisite. Record the manual-versus-automatic
disposition, checks, changed-file identities, scenario mapping, failures and proof
limits. Hand the exact candidate and evidence to the coordinator for fresh policy
review and applicable submission gates. Maintain this task's sole Current state.

**Fresh policy reviewer.** Start without author conversation/history. You are
already the assigned report-only reviewer; do not repair files or delegate. Use
the review-work skill's policy mode, AGENTS, this contract, the exact documentation
diff, named references and actual demonstration evidence. Independently check
authority, route, ownership, all seven scenarios, the separation of `RUN` and
shared lock, actual external-evidence propagation, source identity, isolation,
contents/inode/mode preservation, existing-lock rejection and unchanged gate/
coverage/accounting rules. Check prerequisite timing and failure handling. Return
ACCEPT or evidenced findings for the exact reviewed scope, and distinguish intake
completeness from remedy activation or PR readiness. Count every review and
correction; missing metering is unknown. Product/test/cache changes or unsupported
qualification claims are out of scope, not documentation shortcuts.

**Coordinator.** Own role transitions, narrow corrections and cumulative
accounting. Retain an unchanged-test baseline rather than creating artificial
test-first evidence. For a future PR, explain the missing-parent trigger and
manual prerequisite in plain English; no figure is needed for this one-directory
relationship. Put candidate/check/evidence identities and limits in the technical
appendix. Preserve the default full-local submission gate and actual external
authority boundaries.

Housekeeping uses [the existing workflow](../operations/fixture-cleanup.md).
Identify exact task-created synthetic directories and close owned processes before
removing them with existing commands. Preserve durable evidence, current checkout,
shared environments and uncertain paths. Do not remove a real lock/cache, create
cleanup software or launch extra tests/review solely for deletion. Record exact
removed/kept/error results here.

## Scoped disposition and observed demonstration

The manual prerequisite is the selected remedy. The unchanged reservation is
sufficient once its parent exists; automatic preparation is not needed to address
this demonstrated case and remains a separately scoped executable change.

The documentation author ran one isolated diagnostic on Python 3.13.12, Linux
x86_64, using the current worktree interpreter and unchanged fixture SHA-256
`eaf31b30080cb1997d27012ecc9ad0689515dc14d17c61f8f3b4c7216a10551f`.
`CACHE` and the fixed `EVIDENCE` parent were synthetic paths under
`/workspace/work/reader-parent-100/synthetic/`; `RUN` was separately redirected
under `/workspace/shared/reader-parent-100/protocol-observations/` before any
reservation was instantiated. No real cache or live lock was used by the
diagnostic.

| Diagnostic condition | Observed result |
| --- | --- |
| Fixed synthetic parent absent | `FileNotFoundError`, errno 2; external `RUN` exists; cache inventory/root inode/mode unchanged; no backup or lock created. |
| Existing parent preparation repeated | Two `mkdir -p` calls exited 0; the empty parent's inode/mode/inventory stayed unchanged. |
| Prepared-parent reservation and normal unwinding | Entered successfully; original cache contents/inventory, root inode and mode restored; owned backup/lock absent afterward. |
| Preexisting synthetic lock | `FileExistsError`, errno 17; lock identity/mode/sentinel content and cache identity/content unchanged; no backup created. |

Durable evidence is outside the checkout at
`/workspace/shared/reader-parent-100/`: `diagnostic.py`,
`diagnostic-commands.sh`, `diagnostic-execution.log`,
`diagnostic-exit-status.txt` (0), `diagnostic-result.json` (PASS) and run-bound
protocol observations. The exact script SHA-256 is
`7fc39ef5ada288f66604642031f68d54899f241cab24a0424659a6dbec128c42`.
These are new observations, distinct from the subsequently available original
doctor probe. Normal local unwinding only was demonstrated: no crash recovery,
concurrent-reservation, permissions, interoperability or cross-platform
qualification claim follows. Full verification is a separate gate.

## Current state

- **Status:** documentation candidate integrated with main PR #101 under “Get a
  pr up.” Isolated diagnostic PASS; fresh policy review found no preliminary
  issues before integration and now assesses the reconciled task/disposition.
  Final review,
  exact-candidate full gate and submission outcomes are recorded outside these
  frozen tracked bytes in `/workspace/shared/reader-parent-100/completion.json`
  and the resulting PR/conversation. This pre-verification pointer does not claim
  those pending results have passed.
- **Authorization/limits:** `/intake 100`, followed by “Get a pr up”; seven scenarios;
  four diagnostic conditions; no human-set execution,
  review, correction or spending limits. Original doctor records became available
  with PR #101; its separate parent-task charges remain linked and are not reset
  or double-counted here. Complete historical metering remains unknown.
- **Baseline/ownership:** initial baseline above; integration base is now
  `d48e0e47b315e79a8c8ab33bc81b3f7f235e3c3c`. Author's two operational docs are
  unchanged by integration; coordinator owns this reconciled task, the new scoped
  F002 handling record, checks and PR. Runtime/tests/fixtures/lock semantics/gates
  are unchanged; every unrelated main file is retained exactly.
- **Evidence:** issue #100 and its empty comment list opened through GitHub;
  default-branch task/probe reads returned 404. Local fixture, lifecycle helper,
  CE03 lesson and relevant project/operational documents inspected. One independent
  read-only scope advisor confirmed paths and ownership. New synthetic evidence
  and its limitations are recorded in the disposition above. The initial 404s
  remain historical facts; the now-available original task/probe/disposition were
  opened without a rerun or retrospective invention. Original private receipts
  were not recovered. Prior canonical gate outputs were preserved in
  external `preexisting-gate-evidence.tar.gz` before any new full run.
- **Checks/review:** intake received fresh independent ACCEPT and passing link/
  whitespace checks. Execution preflight PASS with uv 0.12.19, current-worktree
  Python 3.13.12/imports, authenticated reader setup and isolated hatchling 1.32.4;
  log `preflight.log` in the external evidence directory. A cheap pre-gate locked
  audit passed for 29 packages (`audit-precheck.log`); it replaces no full phase.
  Documentation-candidate hashes, final review and full gate results will remain
  outside verified tracked bytes in conversation/PR and durable external evidence.
  Author checks passed: 12 local target occurrences, five shell-block syntax
  checks and whitespace. Fresh remedy reviewer independently matched document
  hashes, detailed diagnostic inventories, journals and retained synthetic state,
  found no preliminary issues, and independently checked the first full receipt.
  The first candidate passed all 13 phases and 3,100 tests with 47 warnings; its
  unchanged 1,175-file manifest, reports, inputs, measurements and wheels are
  retained outside the checkout in `full-gate-evidence.tar.gz` and
  `pre-integration-completion.json`. That result is not presented as the changed
  integration candidate's gate. New full evidence will use `integrated-` names,
  preserving the first run. Fixture, dependency and environment inputs relevant
  to the synthetic demonstration are unchanged, so its observed cases are retained
  for reviewer applicability assessment without rerunning them.
  No runtime/test/fixture/infrastructure change is present; inherited test bytes
  remain the baseline's bytes, with no invented new test-review checkpoint.
- **Accounting:** one coordinator, one report-only scope-advisor launch and one
  fresh policy-review launch; one completed review, zero review corrections.
  Intake reviewer requested `gpt-6.1-sol`/high per project guidance. Execution adds
  one documentation-author launch at requested `gpt-6.1-sol`/high, one successful
  diagnostic, one preflight and one audit precheck, plus one fresh remedy-policy
  reviewer at requested `gpt-6.1-sol`/high. Remedy review has one preliminary pass,
  zero reviewer-requested corrections; its final verdict is pending. One full
  local gate passed; a second is required for the changed integrated candidate.
  One coordinator integration correction reconciles the diagnosed add/add task
  conflict; one stale patch-context rejection changed no files. No product/test
  defect, author retry or diagnostic rerun is hidden. Initial
  absent-file/search-path diagnostics and unavailable
  remote reads are retained as discovery limits, not product failures. Actual
  served model/effort, tokens, cost and complete elapsed/check-time metering are
  unknown. No known exposure to a required blind role; no blind role was needed.
- **Next action:** finish independent integration-scope assessment, commit the
  resolved candidate, run the complete local gate with
  external protocol observations, deliver its exact identity/evidence for the
  reviewer's final verdict, then push/open the PR. Follow the external completion
  pointer for final results; do not edit verified bytes to record their own hash.
  No material owner decision is unresolved for the manual documentation route.
- **Housekeeping:** after reviewer inspection and author process-closure evidence,
  coordinator removed the exact disposable `/workspace/work/reader-parent-100/`
  directory with existing commands and confirmed it absent (status 0). This
  included only task-created script/check copies and synthetic fixtures/lock.
  Durable external scripts/results/journals, current checkout, real reader cache,
  shared tools/environments and ignored shared bytecode were retained. No command
  errors, worktree removal, live-lock deletion or cache cleanup occurred.
