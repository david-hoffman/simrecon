# SP112: qualify a single-precision reconstruction proposal

**Version 1.0.** Git versions revisions. This is the sole Current state for #112.

## Contract

- Authority: [issue #112](https://github.com/david-hoffman/simrecon/issues/112),
  supplied to this session at `/workspace/work/campaign/issue-112.md`; the
  [coordinator packet](../packets/precision-112/intake-author.md) requests this intake,
  scientific study/proposal, fresh review, verification and eventual PR.
- Outcome: a reviewed evidence-backed proposal and finite downstream plan,
  [SP112 contract](../contracts/single-precision-study-v1.md). No runtime change,
  default migration, whole-workflow conversion, merge, release or issue closure.
- Branch `docs/112-single-precision-contract`; public-main baseline
  `b344e41a8b52de76d7cbbf8450319893904c3b8f` for actual trials; intended
  final integration base is public main
  `64a752b4642709c539df2079cc3c906acf4cc7b8` after root-owned fast-forward.
  Proposed PR title:
  `docs(precision): propose a qualified single-precision reconstruction path`.
  Issue coordinator prepares local commits; campaign root alone integrates, pushes and opens the PR.
- Scientific expectation sources: active CE02–CE07 mathematical contracts and
  RM84 compatibility boundary linked from the contract. Legacy experiments and
  double/single agreement supply no independent oracle or feature authority.
- Inputs/outputs: deterministic finite analytic band/phase/transfer witnesses,
  documented dtype/kernel probes and fresh-process measurements; output is
  proposed scientific decisions, methods, actual raw evidence and limitations.
  No hidden product tests, fabricated product-red evidence or runtime exports.
- R1: independently justified error/decision/failure methods distinguish source
  conversion, reference uncertainty and candidate execution error.
- R2: explicitly propose storage/compute/reduction/result dtypes, opt-in selection,
  initial modes, failure and compatibility; identify unresolved scientific choices.
- R3: independently constructible PreparedBands32 record/fixture proposal and
  exact first downstream #113 scope, without relying on preparation completion.
- R4: bounded reproducible actual numerical/dtype/memory/time observations, with
  pinned platform/inputs/versions and honest unsupported/unmeasured limits.
- R5: separately intakeable workflow-facing CE06 preparation, estimation,
  transfer and summary stages; CE02 alone establishes no workflow memory saving.
- R6: fresh independent scientific assessment before study acceptance; later
  runtime work has separate high-risk intake and frozen A/B/C/D checkpoints.
- Risk: scientific numerical design remains high risk. This task delivers a
  report-only proposal, not a runtime/test checkpoint. A nonblind study author
  and fresh independent scientific reviewer are the applicable study roles;
  they inspect public equations and existing interfaces, challenge oracles and
  proposal scope, and supply no runtime readiness verdict. Manufacturing red
  tests or calling a pre-gate proposal assessment “D” would misrepresent the
  work. Later product implementation requires fresh blind A, fresh blind B,
  restricted C and fresh D. The final exact-candidate readiness assessment and
  submission gate remain coordinator-owned and distinct from scientific review.
- Ownership: intake author edits only this task, the SP112 contract and
  `docs/packets/precision-112/{study-author,scientific-review}.md`, plus its
  local detailed report `work/precision-112/intake-report.md`. Study author may
  subsequently edit the proposed contract and named durable report directory
  `docs/reports/single-precision-study/` (reproducible report-only scripts, raw
  JSON and scientific report); scratch only `work/precision-112/`. No runtime,
  product tests/fixtures, dependencies, gates, workflows or policy edits. Fresh
  reviewer writes its own report only and does not repair its review target.
  Issue coordinator owns this task, packets and role ledger; the execution
  supplement narrows any broader draft author ownership.
- Inherited coverage: [PROJECT](../PROJECT.md#coverage-policy-and-adoption-provenance)
  selects behavior coverage and independent risk review; percentages advisory.
  Full gate still requires native statement/branch reports globally, per package
  and file on Ubuntu 24.04, never-imported files/subprocesses, current JSON/HTML,
  and same-run M25 evidence. No selected percentage target is invented.
  Report-only scripts are study artifacts, not shipped/runtime source or test
  helpers; full configured checks remain unchanged.
- Checks: before grant only static reads, link/schema/ledger inspection and
  `git diff --check`. After coordinator preflight/resource grant, locked study
  commands in the study packet with bounded failures logged. Root runs exact
  candidate `make verify` through its pinned shared Ubuntu route, with clean
  tracked start and unchanged inputs, before PR. No CI-authoritative waiver.
- Models: requested fresh tool route `gpt-6.1-sol` / high for intake, study and
  scientific review; conservative scientific choice, general quality calibration
  unmeasured. Actual serving attribution and usage/cost are unknown unless host
  provides them. Escalate only after diagnosed concrete reasoning limitation;
  missing scientific meaning returns to intake, environment failure to root.
- Limits: no human numeric execution, review, memory, timing or accuracy budget
  set. 16 GiB is a workstation feasibility objective, not a process ceiling.
  Coordinator resource scheduling and finite experiment design bind. Missing
  measurements are unknown, not zero. Three fresh repetitions are study design,
  not a human limit. Largest planned spatial sample is Y64 X64 until amended.
- Completion: complete all issue checkboxes with observed evidence or explicitly
  restrict the scientifically supported proposal and document material gaps;
  independent scientific acceptance, final exact candidate checks/review, then
  coordinator PR. Proposal acceptance activates no runtime behavior.
- Housekeeping: root preserves tracked contract/packets/durable reports, current
  checkout, shared pinned environment and active work. Intake created no scratch
  process or numerical fixture. Its local report/packet are coordinator inputs;
  keep until incorporated, then root may remove confirmed disposable scratch
  under existing section 9.1 procedure. No cleanup helper or separate full run.

The 22 scenarios below count distinct study decisions. M01–M20 in the contract
are 20 finite matrix rows with explicitly listed equivalent variants; no full
Cartesian product or claim that 20 executions suffice. Total generated concrete
examples/run count is unknown until the study author freezes the manifest.

| ID | Distinct observable obligation / boundary | Source | Coverage examples / evidence and review |
| --- | --- | --- | --- |
| S01 | Existing double APIs/defaults/summary-full compatibility preserved | Issue, RM84 | Static diff and double controls; reviewer checks no activation |
| S02 | Genuine low-precision bulk storage/compute distinct from final downcast | Issue | Dtype table, M01/M19; distinguish prototypes from future runtime |
| S03 | Original input representation and input-conversion error distinguished | Issue / section 2 | M05/M14; frozen x0/x32 and independent references |
| S04 | FFT interface, normalization, transitions and workspace limits characterized | Issue | M01, pinned NumPy/SciPy; no unsupported internal claim |
| S05 | Binary64 accumulation/solve/coordinate policies explicit | Issue | M04/M07/M08; table and measured promotions |
| S06 | Signed image, scale and cancellation acceptance independently justified | CE04 | M02/M03/M06; absolute and signal-scale error bounds |
| S07 | Carrier and modulation error separated from image/physical accuracy | CE05 | M08/M10/M16; units, complex error and zero-phase caveat |
| S08 | Normalization/range/underflow/overflow decisions explicit | CE02–05 | M05/M18; finite normal assumptions and subnormal contributions |
| S09 | Phase conditioning distinguishes residual from forward error | CE02/06 | M07; analytic small solve, rank/rounding boundaries |
| S10 | Energy helper permitted-zero and singular cases distinguished | CE05 | M08/M09; unequal positive/C=0 versus equal/zero energies |
| S11 | Frozen-overlap search and inherited magnitude state preserved | CE05 | M10/M12; actual constructible witness or qualification gap |
| S12 | Strict maxima/ties/brackets have margins and unresolved classification | CE05 | M11/M12; exact tie rule and interval comparisons |
| S13 | Complex transfer interpolation and actual unsafe stencils qualified | CE03 | M13; radial/full, zero-weight vertices, boundaries |
| S14 | Empirical c128 values retain source precision and record conversion | CE03/07 | M14; c64-exact versus nonexact source values |
| S15 | New independently constructible band schema validates all its fields | Issue | Section 4; M02/M18, direct construction revalidation |
| S16 | Legacy schemas, ownership and parameter precision retained | CE02/04/06 | Old rejection preserved, read-only/strided constructor positives |
| S17 | Supported initial mode and separately scoped exclusions explicit | Issue | #113 stationary 3D; M15/M17 characterize future boundaries |
| S18 | Finite/representation/operation failures and no partial result explicit | CE02–07 | M18; paired valid declarations, no arbitrary floor/cap |
| S19 | Bounded reproducible actual error/dtype/RSS/time evidence | Issue | M01–M20 manifest, raw runs, versions and unmeasured labels |
| S20 | Shared-host resource limits and 16 GiB objective honestly interpreted | Issue | Headroom preflight, M19/M20 scaling; no extrapolated guarantee |
| S21 | Concrete downstream CE06/estimation/transfer/summary contracts | Issue | Section 5 dependencies and separate high-risk route |
| S22 | Fresh independent scientific acceptance precedes proposal acceptance | Issue | Exact artifact digest and report; final gate separate |

## Current state

- Status: scientifically accepted study/proposal, with explicit bounded limits;
  exact-candidate canonical gate and fresh final readiness review remain pending.
  Runtime/defaults are unchanged; no single runtime or product checkpoint is qualified.
- Baselines: actual trials b344e41a8b52de76d7cbbf8450319893904c3b8f;
  intended final public integration base64a752b4642709c539df2079cc3c906acf4cc7b8.
  Root integrated the disjoint eleven-file setup/recovery delta after write hold;
  independent scientific review verified unchanged numerical material applicability.
- Final evidence pointer (prepared before verification): campaign root records
  exact candidate/tree/base, canonical receipt, final independent verdict and
  publication evidence outside tracked bytes at
  `/workspace/work/campaign/evidence/112/`. No post-gate tracked self-hash edit.
- Roles: fresh intake `/root/issue_112/intake_author`, fresh investigator
  `/root/issue_112/study_author`, fresh scientist
  `/root/issue_112/scientific_reviewer_1`. Requested Sol/high, fork_turns=none,
  no nested delegation; serving attribution and unavailable memory/read-only
  controls remain unknown/unavailable as disclosed in the
  [role ledger](../reports/single-precision-study/role-ledger.md).
- Scientific verdict: [review1](../reports/single-precision-study/scientific-review-1.md)
  accepts all six #112 study criteria with bounded scientific limitations;
  exact reviewed proposal candidate and hashes are in that report. No blocking
  proposal correction. It is no final D/readiness or runtime acceptance.
- Evidence: [report](../reports/single-precision-study/report.md),
  [acceptance method](../reports/single-precision-study/acceptance-method.md),
  frozen manifests/scripts/raw attempts and derived ledgers. Artifact SHA,
  raw/TSV/RSS reconciliation, independent scalar bounds and staged whitespace
  checks passed; full-gate/coverage/build/M25 results remain pending root receipt.
- Metrics:22 scenarios,20 matrix rows,16 kernel declarations; study198 Docker
  invocations =184 workload attempts (168 completed,16 diagnosed study failures)
  +1 missing-script launch +5 freezes +7 environment/admission +1 backend probe.
  Interrupted launcher137 and original unattempted repetition stay separate.
  Preliminary scientist ran2 bounded reconciliation processes, no resource replay.
  Author launches2, scientific reviews1, no review-target repair; all methodology,
  fixture/observer corrections and exposure/accounting are retained in linked ledgers.
  Human numeric caps: not set. Token/cache/response/cost and complete elapsed/
  owner-wait measurements: unknown, never zero-filled or double-counted.
- Limits binding downstream intake: general FFT envelopes/literal CE04 branches,
  nonunit transfer rounding witnesses, new-record/runtime failures and actual
  allocation lifecycle; single search, CE06 workflow, physical recovery and
  workstation readiness remain unqualified. #113 can start independent intake
  from the accepted constructible record and methods; this activates no behavior.
- Next action: campaign root runs canonical full Ubuntu `make verify` on the
  clean final candidate. After a passing exact receipt, issue coordinator launches
  a fresh report-only final readiness reviewer writing outside tracked bytes.
  Root alone pushes/opens PR; no merge/release/issue closure is authorized.
- Housekeeping: removed confirmed disposable report `__pycache__`, investigator
  scratch directory and duplicate local intake/packet/check scratch after durable
  copies/check results were preserved; existing commands exited0 and absence was
  confirmed. No owned live/stopped numerical workload remains. Kept current
  checkout/commits, tracked evidence, shared environment/caches and
  `work/precision-112/pr-draft.md` as root's active PR input. No cleanup errors.

## PR presentation (coordinator)

Lead with the proposed useful opt-in bulk-precision path, independently declared
first-slice bands and finite downstream plan. The identified resource table and
explicit prototype limits convey the comparison; no figure is needed. Keep
versions, scientific/gate/review identities, coverage/M25/build proof, complete
attempt accounting and unresolved limits in the technical appendix. Coordinator
prepared `work/precision-112/pr-draft.md`; root fills exact final proof after gate.
