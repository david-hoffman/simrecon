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

* Status: **B2 integrated checkpoint accepted/frozen; fresh C pending launch**.
  High-risk A/B/frozen tests/C/full exact Ubuntu/D route; W01–W18, scenarios18.
  Actual human numeric limits not set; missing metering unknown. Product remains
  pre-C red; no C implementation, #115 full gate, D or publication yet.
* Root integrated accepted #112 parent d9a0ba924817772fdb5550c7d055bf31bcf70388,
  tree836abd6603e28ea69c611429443c0684ba2f8441, published as PR121. Root reports
  its full local Ubuntu gate/independent acceptance passed; CI43653094741 was
  in progress at handoff, not claimed passed. #115 integrated checkpoint
  290a4e6a834a3de56f7f49b40939e20be159c7cd/tree
  9aa7945f5915ce81896ee001352d6eea761b3535, rebased own commits67ef000+290a4e6.
  No coordinator push/restack. Parent scientific source/defaults/lock unchanged.
* Historical actual A/B1 base b344e41a8b52de76d7cbbf8450319893904c3b8f,
  accepted test checkpoint9a423fd608ecf6cdb203283674522b8b88b9e080 and previous
  head8f6b17eb332e7587450e97534bc67bb93658fd6e remain preserved under local
  refs/campaign/evidence/115-pre-parent. No relabeling of their runs/verdicts.
* All historical99 frozen files match integrated bytes; new inherited setup
  test makes100. Integrated manifest
  [tests-integrated-checkpoint.sha256](../reports/issue-115/tests-integrated-checkpoint.sha256)
  SHA256 3e4d18a1f9a96ae537eeac12bc126012b1d93c3d4613ed76b72da9b740302528.
  Historical manifest remains unchanged. Wide contract/interface and six own
  test digests unchanged. New parent setup test is accepted inherited input,
  with no active precision/API/default implementation change.
* Fresh B2 `/root/issue_115/b2_115`, requested gpt-6.1-sol/high, fork_turns=none,
  reviews whole named public files under self-contained project/coverage/platform/
  role/test-value facts. PROJECT, mixed-role skills, A/B1 reports, nonblind state,
  runtime/history/coverage/lessons and unlisted links excluded. No sibling
  substantive conclusion supplied. B2 independently accepted W01–W18 and exact
  integrated applicability/added setup-test interaction/retained historical
  evidence; report SHA25667e9ffbe0efa451b458432ddbf8565c7dc305561a33d4d174fb67bca4c599a7f.
  No test correction, integrated execution or source exposure. Its explicit
  caller-wiring/declaration-observer/fault-hook limits remain C/D obligations.
* Historical [B1 report](../reports/issue-115/b-review-1.md) accepted exact six
  scientific test files and affected obligations, with explicit proof limits.
  [A report](../reports/issue-115/a-tests.md) records1099pass/19 valid byte-domain
  red/16warnings,128.26s. Final exact-six-file Ruff/format/uv-run source-free
  Pyright passed after cosmetic changes; B1 inspected the complete hash-anchored
  delta and retained prior-run applicability, without claiming a new run.
  Four fixed LAPACK lines/stop retained, no source/locals exposure, attribution
  unproven. B2 receives sanitized facts/delta only and judges independently.
* Cumulative charges: intake1, A1 plus continuation1, B1 completed full review1,
  B2 completed review1 (two B reviews total), C0/D0. A semantic corrections0, cosmetic rounds2,
  environment/invocation diagnosis1, diagnostic stop1, evidence request1 resolved
  without test change, source exposure0. A check commands10/five nonzero statuses
  including product-red. Model attribution/tokens/costs/overall elapsed unknown;
 128.26s is pytest wall only. [Detailed launches](../reports/issue-115/role-launches.md).
* Next: all100 integrated tests rechecked/frozen after B2; launch fresh restricted
  C on actual parentd9 with named product/docs ownership and execution hold. Current execution hold:
  no imports/probes/tests/lint/types/installations/measurements by B2; root117
  has focused checks. Coordinate C ordinary focused window, no full gate until
  root schedules exact clean candidate. Known red/missing proof blocks submission.
* Final receipt/review/publication pointer remains outside tracked candidate
  bytes `/workspace/work/campaign/evidence/115` and conversation/PR. D writes
  there after exact full passing Ubuntu gate. Root owns push/PR parent121/CI;
  no merge/release/manual closure. Prepare all tracked pointers before final gate.
* Housekeeping: no active own check process/scratch. Earlier unused bootstrap
  files and empty work/issue-115/work removed with existing rm/rmdir, no errors.
  Keep durable reports/packets, active checkout, frozen tests and required inputs.

## PR presentation

Coordinator summary: allocation-byte casts previously rejected otherwise valid
64-bit geometry; the change uses checked native byte arithmetic while retaining
signed element/index and actual addressability constraints. Target validity is
an integer classification, not an allocation/16 GiB claim. A compact bound table
is sufficient; no decorative figure is planned. Appendix retains exact contract/
checkpoint/candidate/base/check/coverage/build/resource provenance and limits.
