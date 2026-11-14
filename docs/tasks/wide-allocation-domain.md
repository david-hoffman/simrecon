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

* Status: **fresh blind B pending launch**; high-risk route, default full-local exact-candidate gate.
  Concrete contract and packets settled; A prepared six test files and final quality checks pass; independent B pending; all scientific acceptance pending.
* Authority: original issue and explicit user-commissioned sequence recorded in
  [durable intake launch](../packets/wide-allocation-domain-intake-launch.md).
  Numeric human limits not set. No unresolved material meaning.
* Baseline: `b344e41a8b52de76d7cbbf8450319893904c3b8f`; parent stack unresolved
  by coordinator; no B checkpoint/frozen manifest/C candidate/D verdict yet.
* Scope metrics: scenarios=18, equivalent examples not yet enumerated by A.
  Models/launches/accounting in
  [role-launch evidence](../reports/issue-115/role-launches.md). Intake launch 1;
  coordinator read-only preparation precedes it. A/B/C/D not yet launched in
  this intake record. Full/delta reviews, repairs, tokens/cost/elapsed and actual
  served model are unknown unless coordinator evidence supplies them; no
  invented zero measurement.
* Checks: intake used only read-only shell/git inspection plus authorized docs
  writes. No install/import/test/lint/type/measurement run. Coordinator supplied
  successful isolated Ubuntu preflight. Root granted A/B focused-only resource
  window after #112 confirmed no active numerical process; A checks in progress. No product-red claim; initially passing tests remain
  valid and scientific baseline is unmeasured by intake.
* Correction routing: inherited assertions requiring byte-only rejection need
  A's approved expectation correction and fresh B review; signed/index/native/
  stencil rejections remain. No tests changed during intake. No bare coverage
  finding or new metric threshold is asserted.
* Evidence: [intake report](../reports/issue-115/intake.md) and authored artifact
  digests in the intake final message. Final candidate/check results will live
  outside verified tracked bytes under `/workspace/work/campaign/evidence/115`
  and in coordinator conversation/PR evidence. D writes its final verdict there;
  no tracked state update may mutate the passing candidate.
* Blocker/next action: root resource scheduling blocks execution only. Coordinator
  classified A evidence and completed preparation. Next launch fresh blind B
  report-only while #112 owns numerical resources; parent #112 still
  blocks C/final integration and full verification scheduling. No extra
  document-approval checkpoint is required.
* Housekeeping: intake created no scratch files or long-lived processes; durable
  deliverables retained. Coordinator retains active worktree/environment and
  handles any separately created scratch.

## PR presentation

Coordinator summary: allocation-byte casts previously rejected otherwise valid
64-bit geometry; the change uses checked native byte arithmetic while retaining
signed element/index and actual addressability constraints. Target validity is
an integer classification, not an allocation/16 GiB claim. A compact bound table
is sufficient; no decorative figure is planned. Appendix retains exact contract/
checkpoint/candidate/base/check/coverage/build/resource provenance and limits.
