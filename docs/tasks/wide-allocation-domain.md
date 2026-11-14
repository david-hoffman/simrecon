# Issue 115: safely extend allocation-byte representation

**Version 1.0.** Sole Current state for this task; Git versions revisions.

## Contract

The owner commissioned issue [115](https://github.com/david-hoffman/simrecon/issues/115)
intake and implementation through high-risk A/B/frozen tests/C/full Ubuntu/D,
then an eventual stacked PR. Start from current main on
`feat/115-wide-allocation-domain`, intake baseline
`b344e41a8b52de76d7cbbf8450319893904c3b8f`. Proposed PR title:
`feat(reconstruction): extend allocation-byte representation safely`.
The coordinator resolves the final stack parent (#112 remains pending); no
parent integration or issue closure is implied by intake.

[Wide allocation domain v1](../contracts/wide-allocation-domain-v1.md) is the
concrete authorized contract, W01–W18. It replaces five byte-only expressions
(eight CE04/CE06 guard obligations) with checked exact native-width byte
arithmetic, retains genuine signed32 element/index/loop constraints and all
native/aggregate/backend/stencil checks, and classifies the target geometry
without allocating it. Existing CE02–07/RM84 scientific/ownership/failure rules
remain. No dtype/precision design, memory-admission cap, full target allocation,
32-bit support, historical executable qualification or 16 GiB fit promise.

Expected results come from the authorized formulas/contract and inherited public
scientific contracts. Error categories remain direct stage errors and workflow/
summary `workflow_representation` at declaration for invalid geometry; operation
causes, MemoryError/interruption and no-partial-result guarantees remain. No
new precedence among simultaneous invalid inputs is specified. Material meaning
is resolved; no further owner decision is needed for this scope.

Boundary inventory includes ordinary small numerical success, independent invalid
declarations, exact byte/count/native boundaries, actual safe/unsafe indices/
stencils, allocation/backend/interruption failure, original-domain compatibility
and documentation. Each contract row includes paired permitted/error evidence.

| Scenario | Decision/outcome | Expected-result source / test review |
| --- | --- | --- |
| W01 | Exact checked wide byte arithmetic | Contract integer invariant; A maps, B recalculates |
| W02 | Five CE04 byte ceilings replaced | Contract bound table; A/B |
| W03 | CE06/workflow/summary byte ceilings replaced | Contract bound table; A/B |
| W04 | Signed dimensions/counts retained | Inherited signed domain; A/B |
| W05 | Signed element/product limits retained | Inherited index math; A/B |
| W06 | Actual index/cutoff/backend constraints retained | Public scientific constraints; A/B, D caller audit |
| W07 | Native dimensions/strides/aggregate extents | Exact intp extent invariant; A/B |
| W08 | Exact zoom/integral extents retained | Inherited zoom contract; A/B |
| W09 | Early rejection before array-sized work | New declaration contract; A/B, D ordering audit |
| W10 | Other invalid declarations retain categories | Inherited errors plus byte admission; A/B |
| W11 | Direct record routes agree where applicable | CE04/CE06 public record contracts; A/B |
| W12 | Workflow/summary agree | CE07/RM84 plus new bound; A/B |
| W13 | Target classified honestly without allocation | Exact target arithmetic; A/B, D docs review |
| W14 | Original numerical behavior preserved | Independent small public controls/inherited tests; A/B/D |
| W15 | Signatures/ownership/debug-summary preserved | Public record/interface contracts; A/B/D |
| W16 | Actual stencil checks preserved | Inherited transfer/address rules; A/B/D |
| W17 | Allocation/backend cause and failure semantics | Inherited operation contracts; A/B/D |
| W18 | Interruption/input preservation/no partial result | Inherited failure contracts; A/B/D |

Inherit PROJECT's approved behavior coverage plus independent risk review;
percentages advisory, no line/statement/branch/combined threshold selected.
Required native statement/branch exact covered/total reporting on Ubuntu 24.04
remains global/per package/per owned file, including never-imported files and
relevant subprocesses. Unsupported metrics/exclusions/skips/missing reports must
be explicit; no gate or measurement migration is commissioned. Relevant risks
are wrap/narrowing, missed byte-only casts, accidental index widening, native
aggregate extents, validation timing, route/error disagreement, failure causes,
unsafe stencils and changed scientific/retention behavior. A maps these risks;
B independently audits omissions; D checks actual implementation beyond green
tests. A bare uncovered branch is not a missing requirement.

Named ownership and transitions:

* Intake owns the new contract, interface excerpt, this task, public/candidate
  packets and separate intake report. No runtime or executable tests in intake.
* Fresh blind A owns `tests/test_wide_allocation_domain.py`, optional
  `tests/wide_allocation_fixture.py` and allocation-obligation corrections only
  in `tests/test_c_known_boundary.py`, `tests/test_c_acquisition_boundary.py`,
  `tests/test_c_workflow_validation.py`, `tests/test_reconstruction_summary.py`.
  Necessary inherited byte-only rejection corrections must be safe before any
  affected inherited file executes. Fresh B reviews exact tests/dependencies;
  coordinator freezes the accepted checkpoint.
* Restricted C owns only the five named source files and eight product-doc files
  enumerated exactly in the candidate packet. All tests/fixtures/snapshots and
  check/discovery/coverage/workflow/skill/policy files are frozen to C.
* Coordinator owns setup/resource windows, parent integration, state/accounting,
  exact full checks, commits, eventual push/PR/CI, presentation and housekeeping.
  Fresh D assesses the exact full-passing candidate and writes report only.

All scientific roles request `gpt-6.1-sol`, high, under current conservative
project guidance; actual attribution/metering unknown unless exposed. Accepted
PR109 policy permits supported fresh no-inheritance tool sessions. Optional
memory/delegation/read-only controls unavailable, shared filesystem/prompt-only
limits disclosed; no delegation by launched roles. Diagnose cause before
corrections/escalation; new meaning returns to intake, invalid tests to A/fresh
B, product defects to C and environment defects to setup.

Exact focused commands/source-free blind harness and Ubuntu container prefix are
in the [public packet](../packets/wide-allocation-domain-public.md); full
`make verify UV=/workspace/.simrecon-tools/uv-env/bin/uv` in the container remains
the exact-candidate gate, all 13 phases and same-run native/report/wheel/audit/M25
obligations intact. No imports/probes/tests/lint/types/install/measurements until
root releases the resource window. No CI-authoritative shortcut. Known failure,
missing required evidence or unmet binding gate blocks submission.

Actual human-set scenario/review/execution/resource limits: **not set**. Missing
counts/tokens/money/time are unknown. Retain every launch, failed attempt,
diagnosis/review/correction cumulatively; no default quota or repeated approval
of this restatement. Completion requires B checkpoint, implementation, exact
Ubuntu full verification and fresh D acceptance; intake is none of those.
Merge/release/issue closure/external messages need separate actual authority.

Coordinator housekeeping uses existing commands at completion: preserve this
active worktree, frozen fixtures, durable docs/reports and required environment/
dependencies. Role-owned disposable scratch/process targets must be named when
created; none created by intake. Check uncommitted work/needed commits before
disposal, preserve uncertain targets and record removed/kept/error facts here.

## Current state

* Status: **WAITING FOR ROOT PARENT FREEZE; B-accepted tests frozen**. High-risk
  A/B/frozen tests/C/full exact Ubuntu/D route. Authorized contract W01–W18,
  scenarios18; equivalent examples/keepers mapped in A/B reports. Actual human
  numeric limits not set; missing metering unknown. Product remains pre-C red.
* Authority: [issue](https://github.com/david-hoffman/simrecon/issues/115) and
  [durable intake launch](../packets/wide-allocation-domain-intake-launch.md).
  Actual A/B public-main base b344e41a8b52de76d7cbbf8450319893904c3b8f;
  B-accepted prepared-test checkpoint 9a423fd608ecf6cdb203283674522b8b88b9e080.
  Root owns integration and requires accepted #112 exact parent before fresh C.
* Frozen99-file manifest
  [tests-checkpoint.sha256](../reports/issue-115/tests-checkpoint.sha256), SHA256
  9fcd3732d4adf47624b13f8aaac1883e30d99ece4cbbaece9cc696d29ff25076.
  Coordinator rechecked every file after B; all match. B accepted exact six
  authored files plus named unchanged dependencies, without claiming an audit
  of every unrelated file. No source changes, C/full gate/D verdict yet.
* Independent evidence: [B1 acceptance](../reports/issue-115/b-review-1.md),
  SHA256 85be60fe77a46aa3b6f089554f600fa8109e0fd6255a8afddff6942b993b08cf;
  [A report](../reports/issue-115/a-tests.md),
  [intake](../reports/issue-115/intake.md),
  [launches/accounting](../reports/issue-115/role-launches.md).
  B independently audited W01–W18/arithmetic/oracles/positive classes/omissions
  and found no actionable test defect. B retained initial product-red evidence
  after inspecting [exact cosmetic delta](../reports/issue-115/behavior-to-prepared.diff)
  and [hash-matching reconstruction evidence](../reports/issue-115/behavior-retention-evidence.md).
  Reconstructed prior text is not an original archived artifact or a new run.
* Checks: root first-attempt pinned Ubuntu preflight passed, supplied environment
  evidence only. A source-free focused pytest exit1:1099passed/19 intended
  obsolete-byte failures/16warnings,128.26s. Final exact six-file Ruff/format/
  canonical uv-run source-free Pyright pass after cosmetic-only preparation;
  no repeated behavioral run was claimed. Four fixed LAPACK messages and the
  conservative stop were retained/routed narrowly without source exposure;
  B found no oracle defect from them, attribution remains unproven.
* Cumulative charges: intake1, A1 plus same-session continuation1, B1 completed
  full affected review1, C0/D0; A semantic corrections0, style rounds2,
  environment/invocation diagnosis1, native-diagnostic stop1, B missing-evidence
  request1 resolved without test change, source exposure0. A check commands10
  (initial4 plus two rounds of3), failed statuses5 including expected product-red.
  Full tokens/costs/elapsed/served attribution unknown;128.26s is only pytest wall.
* Upstream notice: root reports main advanced through merged #106 to
  64a752b4642709c539df2079cc3c906acf4cc7b8; setup/recovery delta, new
  check_dev_environment runtime/check and test, appended role-launch guidance,
  no scientific source/AGENTS/PROJECT/Makefile/lock/dependency changes. This
  worktree is not restacked. Root will integrate #112 onto that main. Preserve
  actual A/B baseline/frozen99 history; after parent integration freeze newly
  inherited tests too and record applicability of unchanged scientific inputs.
* Blocker/next action: **wait for root to integrate accepted #112 and freeze its
  exact parent**, then resume this coordinator and launch fresh restricted C
  with B-accepted tests and exact inherited inputs. No implementation before
  root freeze, no imports/probes/tests/lint/types while another resource window
  owns execution, no installs/full gate/target trial. Known red/missing gate
  blocks submission. Routine continuation needs no new document approval.
* Final evidence pointer prepared before gate: outside tracked candidate bytes
  `/workspace/work/campaign/evidence/115` and coordinator conversation/PR.
  D writes there only after exact full passing Ubuntu verification; no tracked
  state update may mutate the verified head. Root owns eventual push/PR/CI;
  no merge/release/manual issue closure authority.
* Housekeeping: no active A/B-owned process or scratch. Unexecuted coordinator
  scratch bootstrap files and empty `work/issue-115`/`work` removed with existing
  rm/rmdir, no errors. Durable reports/packets, current worktree, frozen tests and
  required shared/environment inputs retained. Active checkout is not disposable.

## PR presentation

Coordinator summary: allocation-byte casts previously rejected otherwise valid
64-bit geometry; the change uses checked native byte arithmetic while retaining
signed element/index and actual addressability constraints. Target validity is
an integer classification, not an allocation/16 GiB claim. A compact bound table
is sufficient; no decorative figure is planned. Appendix retains exact contract/
checkpoint/candidate/base/check/coverage/build/resource provenance and limits.
