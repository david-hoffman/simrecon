# Test audit and Ubuntu-only verification

**Version 1.0.**

The owner's October 20, 2026 request authorizes applying the upstream OpenClaw
test-audit procedure to reduce redundant tests, favor end-to-end/public-entry
proof, and remove macOS from CI. The owner subsequently set a target of at most
600 seconds for the full suite, then tightened the target to below 300 seconds
on October 21. Measure complete CI time, including setup and evidence transfer,
and report tests, local verification and CI job time separately. The full local
gate has no additional 300-second limit. This is a performance objective, not permission
to stop a diagnostic run at 600 seconds or silently waive a check. No total
execution, review, or spending limit was set. Consult a fresh clean-context
`gpt-6-astra`/ultra advisor for blockers and issues.

On October 21 the owner prioritized reducing fixture disk use and fixing cleanup
before further speed work. The [disk lifecycle contract](../contracts/test-fixture-disk-lifecycle-v1.md)
defines the earlier release of newly created disposable scratch, exact locked
pytest failure semantics, external evidence preservation and repeated-run disk
qualification. Historical cleanup and new-run lifecycle changes remain distinct.

Baseline: PR50, commit `8a0e488b66588d7d943dbf52fc48a276dbb14253`.
Branch: `codex/test-audit-linux-ci`. This worktree owns this task only.

## Contract and ownership

- Inventory the complete suite by production owner, then audit the measured
  high-cost layers and concrete redundancy candidates in focused owner batches.
  Record baseline results and cost, each assessed retain/consolidate/delete
  decision, and the independent obligation and keeper before removing proof.
  Untouched or partially inspected tests remain explicitly outside a focused
  batch's audit claim. Baseline failures are defects to classify, never deletion
  candidates merely because they fail. Continue scoped corrections until the
  requested runtime objective is achieved or a material blocker is established.
- Bounded partition: explicitly authorized Ubuntu-only workflow/platform
  maintenance and demonstrated duplicate/conventional test consolidation, with
  unchanged public behavior and independent expectations. Named maintenance
  ownership: `.github/workflows/verify.yml`, relevant current platform guidance
  in `docs/PROJECT.md`, `docs/operations/verification.md` and `README.md`, and
  test/fixture paths named in the per-lane correction packet. Coordinator owns
  this record, audit report, unique lesson and ignored evidence. A fresh
  independent reviewer assesses preservation and the exact passing candidate.
  The [parallel execution packet](../contracts/test-audit-parallel-execution-v1.md)
  names optional scheduling/dependency/policy-hook maintenance and its separate
  qualification obligations.
- Bounded preservation/environment correction: restore the exact baseline
  `tests/test_reconstruction.py::test_fixture_derivation_and_informative_regime`
  declaration after independent review found its direct reference qualification
  was not redundant. Own only that restoration and
  `tests/test_measurements_export.py::repository`'s local
  `maintenance.auto=false` setup before its first commit. Keep all assertions,
  tolerances, metadata comparisons and runtime behavior unchanged. Qualify the
  23 focused reconstruction rows, existing ancestor-symlink rows and complete
  measurement-export file with isolated inherited maintenance enabled; retain
  native Git trace/config evidence. Fresh review and renewed full gates bind.
- Coordinator owns the separately mapped six equivalent parameter examples in
  `tests/test_measurements_export.py::invalid_reports` and
  `tests/test_verification_evidence_outputs.py::test_p11_phase_link_sweeps_actual_current_html_members`.
  Retain isolated numeric counterparts, both complete symlink write-site
  sweeps, all 20 representative link cases and four native-database cases;
  discovery, observers, assertions, helpers and runtime remain unchanged.
  Keep four outer workers; the 40-case comparison did not establish a useful
  six-worker gain. Retain the slowest 25 pytest durations in normal gate output
  for evidence-guided follow-up. Exact full gate and fresh review still bind.
- Follow-up bounded fixture-startup maintenance is owned by the
  [controlled-command packet](../contracts/test-audit-fixture-startup-v1.md).
  It preserves all four command-fixture modules' cases/assertions and corrects
  only the independent C74 controlled timeout input and matching duration
  expectations. The former containing-module hash is superseded explicitly;
  the separately reviewed reader function and its dependencies remain frozen.
- High-risk fixture lifetime correction uses fresh blind A/B, restricted C and
  fresh D. A owns only new `tests/test_fixture_lifecycle.py` and
  `tests/fixture_lifecycle_fixture.py`; C owns only the named retention key in
  `pyproject.toml`. Keep the existing count of three, local worker grouping,
  strict outcome policy and all prior assertions. Coordinator owns diagnostic
  execution and documentation. Stop the unmanaged profiling launcher that makes
  unique explicit temporary bases without cleanup; use owned isolated numbered
  namespaces and retain required native/report data outside them.
- Scientific/binary oracle redesign or uncertain preservation is separate
  high-risk work: concrete public contract and sanitized preservation obligations,
  fresh blind A/fresh B, frozen tests for C, exact verification and fresh D.
  Discovery agents do not become blind authors/reviewers. No runtime behavior,
  scientific defaults, tolerance, public API or binary representation change is
  authorized by a test-count objective.
- Preserve the complete Ubuntu verification phases, coverage report integrity,
  same-run measurements, wheel/import/audit checks, no-skips policy and inherited
  task-selected 100% native executable-line/branch-destination targets. Removal
  of the macOS CI obligation follows the owner's explicit instruction. Any
  concrete percentage conflict requires diagnosis and an actual owner decision;
  neither the target time nor advisory project defaults silently waive it.
- Keep one primary proof per obligation at the strongest useful boundary.
  Focused tests remain where compositions cannot distinguish the same failure.
  Do not rename thousands of executions as one test or move them out of the
  full suite to manufacture a performance claim.

## Checks and completion

Run cheap pinned environment checks first. Use saved baseline evidence only for
unchanged identities and label environment/timing limits. Obtain current
per-test durations and file results. Apply coherent reviewed keeper plans,
serializing shared helper edits. Run focused owner/sibling checks, lint, types,
format and `git diff --check`, then canonical exact-candidate `make verify`.
Measure full-suite and full-verification wall time independently. Required
Ubuntu CI timing remains unverified until actually observed. Do not equate local
macOS timing with Ubuntu timing. No merge, release or external message is
authorized. Publication follows the existing exact-candidate gate only when
requested or necessary under the authorized delivery scope.

The final independent preservation review includes the final audit sweep and
compares every removed obligation with its keeper. Report count/line changes,
retained contracts, measured before/after cost and limitations.

## Current state

The sole current state, declaration inventories, lane packets, baseline/current
results, advisor reports, review rounds, corrections and cumulative accounting
live in ignored `artifacts/test-audit-ci/CURRENT.md`. Final candidate identities
and results stay outside tracked candidate bytes. Actual serving attribution,
complete metering and monetary cost are unknown unless directly observed.
