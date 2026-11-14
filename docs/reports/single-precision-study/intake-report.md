# SP112 intake author report

Fresh role `/root/issue_112/intake_author` completed the assigned intake packet
with SHA-256 `e6c6a8c038bebd9e3239d6998c342c835c8aecdc573a628523690364d58782f7`.
Worktree `/workspace/work/issue-112`, branch `docs/112-single-precision-contract`,
observed HEAD `b344e41a8b52de76d7cbbf8450319893904c3b8f`. No commit was made.

## Delivered artifacts

- `docs/contracts/single-precision-study-v1.md`: proposed dtype policy,
  independent numerical methods, finite representative matrix, bounded
  measurement protocol, independently constructible first-slice record/fixtures,
  separately intakeable implementation stages and issue-checkbox mapping.
- `docs/tasks/single-precision-study.md`: sole Current state, concrete request,
  R1–R6, 22 distinct scenarios, named ownership, study-versus-runtime route,
  inherited coverage/gates, accounting/resource/housekeeping and next role.
- `docs/packets/precision-112/study-author.md`: candidate-template-derived
  nonblind report-only study author, explicit files/resource prerequisites and
  evidence requirements. Root freezes exact launch digest/candidate.
- `docs/packets/precision-112/scientific-review.md`: candidate-template-derived
  fresh independent report-only scientific assessment. Proposal review is
  explicitly distinct from pre-gate D/readiness and subsequent runtime A/B/C/D.

Scientific statements are proposals, not activated product behavior. Actual
measurements, qualification decisions, independent scientific acceptance, full
verification and PR remain subsequent coordinator-managed work. No manufactured
red tests or arbitrary tolerance/budget was introduced.

## Main decisions / scientific boundaries

The proposed initial profile uses float32/complex64 bulk frames/bands/FFT/filter
storage; binary64 coordinates/scalars/phase solves/noise and promoted energy/cross
reductions; binary64 image accumulation and float32 returned image. Transfer
sources remain complex128; conversion of bounded consumed blocks is explicit.
Actual backend dtype behavior and undocumented workspace remain evidence gaps.

Numerical methods distinguish `F(x0)`, `F(x32)`, double evaluation error and
candidate execution error. Tiny independent sparse Fourier/direct-DFT and scalar
interpolation oracles carry reference uncertainty separately; condition-scaled
absolute error handles signed cancellation. Discrete maxima/brackets/stencils
require interval margins and exact ties preserve literal CE rules. Unknown or
undefined reference/branch behavior cannot be called passing. Physical recovery
and workstation feasibility are not inferred from kernel observations.

The new proposed `declare_prepared_bands32` / `PreparedBands32` schema is narrow,
independently constructible, all-field validated and independently owned. It has
complex64 quadratures and float64 `(T,D,O)` noise, computed CE scale, exact
mapping/profile metadata and bounded immutable caller provenance. No old stage
dataclass is reused/downcasted; no phase/camera/history fields are fabricated.
Existing double-only schemas/validation remain unchanged. Independent fixtures
specify band coefficients directly, not by calling production preparation.

Coordinator clarified authoritative #113 expects opt-in `reconstruct_known`
selection. The proposal now uses future
`reconstruct_known(..., precision="single-mixed-v1")`, preserving omitted/default
double calls; no separate `reconstruct_known32` entry remains. #112 changes no API.
#113 initially targets stationary known-parameter 3D, with CE02 direct preparation,
workflow-facing CE06 preparation, CE05 estimation, transfer/calibration handling
and workflow/summary integration as separate later intakes.

## Counts, unresolved decisions and next action

Scenarios=22. Representative matrix rows=20 with explicit equivalent variants;
concrete generated examples/execution count unknown until investigator freezes
manifest. No Cartesian-product promise. M12 actual search witness and M17 full
CE06 stateful witnesses require constructibility qualification; missing evidence
must restrict the proposal rather than create a helper-only proof. FFT/backend
error envelopes, supported precision-sensitive mode subset, exact implementation
signature/settings/error category and application-level accuracy remain for
evidence/review/later intake as described. No human numeric error/memory/time/
execution/review budget was set.

Root reported pinned Ubuntu preflight passed and granted the next investigator
an exclusive numerical window. Intake used no numerical resource under it.
Root can now launch the study author with the four artifact identities and its
supplemental execution packet; later launch a fresh scientific reviewer against
the completed exact proposal/evidence. Runtime requires separate high-risk
fresh blind A/B, restricted C and fresh D, never reuse study review as readiness.

## Commands, evidence and scope

All executed shell commands returned exit 0 except the four no-index difference
checks described below; no tests, imports,
benchmarks, experiments, installations or runtime probes were executed.

- Read assigned packet using `cat`; confirmed SHA-256 with `sha256sum`.
- Read root AGENTS, PROJECT, intake skill/prompt, TASK/CANDIDATE templates,
  role-launch and model-selection instructions. Some broad combined reads were
  tool-output-truncated; subsequently opened relevant PROJECT sections and narrow
  active contract/source sections to recover needed interface detail.
- Used `rg --files` and narrow `rg -n` / `sed` static reads for precision/memory
  contracts and current preparation/modes, known-parameter, parameter-estimation,
  optical-transfer and workflow interfaces. No legacy source/archive was read.
- Observed `git status --short`, branch and HEAD. At start existing untracked
  `docs/packets/precision-112/`, `docs/reports/single-precision-study/`, `work/`
  were present. Did not inspect unrelated coordinator evidence in those paths.
- `git diff --check` exit 0 (tracked-only scope acknowledged for new files).
  Ran `git diff --no-index --check -- /dev/null <file>` separately on each of
  the four new docs to inspect actual untracked content; each returned exit 1
  because the new file differs from /dev/null, with no whitespace diagnostics.
- `wc -l`: contract 341, task 169, study-author packet 88, scientific-review
  packet 81 at handoff. SHA-256 identities were printed outside tracked bytes.
  No runtime/tests/fixtures/dependency/workflow/gate/policy files were edited.
- No full gate, coverage, wheel, native resource or scientific acceptance result
  is claimed. Those statuses remain pending in the task.

## Process / cumulative accounting / housekeeping

This intake author launch=1; initial draft=1; coordinator-requested interface
correction=1 (separate-entry proposal corrected to #113 opt-in keyword); review
verdicts=0, scientific experiments=0, installs=0, author-spawned children=0.
The task records no self-initiated diagnosed scientific repair; this coordinator
scope correction is retained here rather than erasing its draft history.
Requested configuration Sol/high per packet; actual serving attribution,
responses/input/cached/output/reasoning tokens, money and wall/owner-wait/check
times unknown. Root retains prior campaign and tool-launch charges cumulatively;
this report does not reset or duplicate those counters.

No conversation inheritance or delegation was used. Optional memory-disable/
per-role read-only controls were unavailable; filesystem/permissions shared and
allowlists are prompt restrictions. No forbidden-source exposure observed.
No owned running process, numerical fixture or temporary script exists. Only
this report and four named docs were created/edited. Keep this report/assigned
packet until root integrates the handoff; keep tracked deliverables, durable
study evidence and shared environment. Root owns eventual confirmed-disposable
cleanup and final removed/kept/error record in the task.
