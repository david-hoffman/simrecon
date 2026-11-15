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

* Status: **C complete; clean candidate preparation for root full gate, then D**.
  Authorized W01–W18/high-risk A/B/frozen tests/C/full exact Ubuntu/D route.
  This tracked state is the prepared pointer: final exact candidate/receipt/D/
  publication evidence lives outside tracked bytes under
  `/workspace/work/campaign/evidence/115` and in root conversation/PR. No tracked
  edit may record a passing head's own hash or mutate it after exact verification.
* Frozen parent: accepted #112 d9a0ba924817772fdb5550c7d055bf31bcf70388,
  tree836abd6603e28ea69c611429443c0684ba2f8441, PR121. Root reports full local
  gate/independent acceptance and exact CI test merge/tree passed. This is
  parent evidence, not a #115 full-gate or D result. Root owns stack/push/PR/CI.
* Historical actual A/B1 base/checkpoint b344e41/9a423fd and old8f6b17 lineage
  remain preserved in refs/campaign/evidence/115-pre-parent. Root integrated
  own commits onto parentd9, producing290a4e6/tree9aa7945. Fresh B2 accepted
  that integrated checkpoint without corrections, independently retained prior
  cosmetic-delta evidence, and assessed inherited setup-test interaction.
  [B2 report](../reports/issue-115/b-review-2.md) SHA256
  67e9ffbe0efa451b458432ddbf8565c7dc305561a33d4d174fb67bca4c599a7f.
* Frozen100-file [manifest](../reports/issue-115/tests-integrated-checkpoint.sha256)
  SHA2563e4d18a1f9a96ae537eeac12bc126012b1d93c3d4613ed76b72da9b740302528;
  all match after C. Historical99 manifest unchanged; added inherited setup test
  is the sole test-set integration delta. C edited no tests/fixtures/config/
  check policy/dependencies/infrastructure. No hidden source/private ancestry.
* Fresh C `/root/issue_115/c_115` began clean43ebeb4/tree89d8de2 on parentd9.
  Changed only known_parameters.py and acquisition/layout.py plus eight named
  product contracts/usages. Five historical byte expressions/eight guards are
  dominated by retained checked actual-width native extents; signed element/
  index/loop checks and original scientific computation/failure/ownership/
  debug-summary semantics remain. Coordinator separately added PROJECT's
  contract/task reference and owns this state/accounting/presentation.
* [C implementation report](../reports/issue-115/c-implementation.md) SHA256
  f1a16d344f3eb8a390bd351b89631656b12f2e7fbc19b4425eb436ba0aac90c1
  records real-caller/ordering/aggregate/failure inspection and exact source
  hashes. Direct known ifftn is an imported alias; the accepted later SciPy
  monkeypatch can take its positive fallback. No universal backend hook-hit
  claim; the actual call remains in the unchanged operation wrapper. D must
  independently assess these concrete proof limits and actual implementation.
* C focused checks: all1118 passed/16warnings in131.23s; changed-source Ruff,
  format and locked Pyright all exit0. No runtime edit followed these checks,
  no corrective code round. Four exact historical DLASCL parameter-4 lines
  recurred, no new native diagnostic; originating case remains unlocalized,
  with no blanket harmlessness/backend qualification claim. No target allocation,
  installation, memory benchmark or full gate run by C. Window released; no
  active own check/background process/scratch. Diff/frozen100 checks pass.
* Historical A evidence remains1099passed/19 valid byte-domain reds/16warnings,
 128.26s, before implementation and cosmetic-only preparation. Final exact A
  Ruff/format/uv-run source-free Pyright pass; independent B1/B2 inspected the
  complete reconstructed/hash-matching cosmetic delta. Historical results are
  not relabeled as integrated reruns. Source/locals exposure0.
* Cumulative charges: intake1; A1 plus continuation1; B1 and B2 completed two
  independent affected reviews; C1; D0. Semantic test corrections0, cosmetic
  rounds2, environment/invocation diagnosis1, diagnostic stop1, missing-evidence
  request1 resolved without test change. A check commands10/five nonzero statuses
  including intended product-red; C four scientific/quality commands all0,
  three administrative path-navigation misses corrected and disclosed. Full
  tokens/cost/overall elapsed/served attribution unknown; pytest walls above
  are individual checks. Actual human numeric limits not set; no default cap.
  [Cumulative launch detail](../reports/issue-115/role-launches.md).
* Next: root schedules canonical full Ubuntu make verify on exact clean committed
  candidate, all13 phases and required same-run coverage/wheel/import/audit/M25
  evidence. Then fresh independent D writes outside tracked candidate bytes.
  Known failed/missing gate evidence blocks submission; focused pass is no full
  gate. No CI-authoritative shortcut, huge allocation or resource trial. Root
  publishes only after exact full pass plus D, stacked on PR121; no merge/release/
  manual closure authority.
* Housekeeping: removed earlier unused coordinator bootstrap and empty scratch
  directories with rm/rmdir, no errors. C/B created no scratch or background
  process. Keep active checkout, frozen tests, durable reports/packets and pinned
  environments/shared dependencies. No custom cleanup helper or extra gate.

## PR presentation

Coordinator summary: allocation-byte casts previously rejected otherwise valid
64-bit geometry; the change uses checked native byte arithmetic while retaining
signed element/index and actual addressability constraints. Target validity is
an integer classification, not an allocation/16 GiB claim. A compact bound table
is sufficient; no decorative figure is planned. Appendix retains exact contract/
checkpoint/candidate/base/check/coverage/build/resource provenance and limits.
