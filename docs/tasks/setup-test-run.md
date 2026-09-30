# SETUP-TEST-RUN: reject incomplete pytest runs

**Version 1.0** Git versions revisions. This record is not technical enforcement.

## Contract

- Slice plan/reference: [setup plan](setup-plan.md). First of two sequential setup slices, T1–T5. Intended baseline is authorized minimal Python test infrastructure on `codex/delivery-setup`; the coordinator identifies its revision before A.
- Project/interface references: [approved project](../PROJECT.md), public `make verify` command, complete-suite `python -m pytest -p simrecon._pytest_policy` invocation, and public process results. The canonical `make verify` selects the plugin through pytest options. Fresh blind A/B packets exclude implementation and task state revealing implementation.
- Purpose: a complete discovered suite succeeds; empty discovery, skips, expected failures, and unexpected passes fail with diagnostics. This is setup verification behavior, not a scientific feature.
- R1: A complete discovered suite containing one passing test returns success.
- R2: Empty discovery, one skipped test, one expected-failure test, and one unexpectedly passing marked test each return nonzero with the corresponding diagnostic. R2 applies even if the unexpected-pass marker opts out of strict mode.
- Inputs, outputs, errors, and permissions: invoke the complete suite through the public project test command from the repository root. Observe integer exit status and retained pytest diagnostics. Normal failing tests already fail natively. No numerical tolerance applies.
- Expected-result sources: the owner-directed setup and unchanged cases in the earlier read-back, full-verification requirement in [AGENTS](../../AGENTS.md), and the project command. Exact process status class and diagnostic category are the oracles; no scientific calculation is involved.
- Allowed scope and checks: A owns tests and fixtures; B reviews A's tests. The coordinator may install minimal infrastructure before A. C may edit only `src/simrecon/_pytest_policy.py` if reviewed tests show an actual gap, and must not alter reviewed tests, fixtures, snapshots, workflow, discovery, coverage settings, skills, or delivery instructions. C may find existing behavior sufficient and make no code change. Run `make verify`, requiring 100% native measured statements and branches across all new owned instrumentable runtime, including subprocesses and never-imported files. Report unsupported native measurements.
- Preparation/execution budget: part of the single eight-hour setup cap ending October 1, 2026 at 02:29:01 UTC. Shared with SETUP-DOCTOR: default two A/B review rounds per window and one C repair after initial C. Prior spending is retained.

| Scenario ID | Approved input/context and observable success, error, or boundary outcome | Expectation source | Test mapping supplied by A and checked by B |
|---|---|---|---|
| T1 | Complete discovered suite with one passing test: success | Full verification requirement | `tests/test_test_run.py::test_complete_passing_suite_succeeds` |
| T2 | Empty discovery: nonzero exit with no-tests diagnostic | Native pytest empty-discovery behavior | `tests/test_test_run.py::test_empty_discovery_fails` |
| T3 | One skipped test: nonzero exit with skip diagnostic | No silently omitted verification | `tests/test_test_run.py::test_skipped_test_fails` |
| T4 | One expected-failure test: nonzero exit with expected-failure diagnostic | Known failure blocks submission | `tests/test_test_run.py::test_expected_failure_fails` |
| T5 | One unexpectedly passing marked test, even when its marker opts out of strict mode: nonzero exit with diagnostic | Marked exceptions must not hide incomplete verification | `tests/test_test_run.py::test_non_strict_unexpected_pass_fails` |

These five scenarios are unchanged from the ten-case read-back. Initially passing existing-infrastructure tests are valid. Before repair, the observing role classifies failures as environment/tooling, test defect, product defect, or unresolved requirement. Import/tooling failure is not intended product-red evidence. A's mapping goes into this table only after authoring and B review, without changing approved behavior.

Completion requires an accepted A/B checkpoint, fresh C evaluation, passing exact-candidate full verification, fresh D review, and integration into the setup branch. The dependent doctor slice starts only from that integrated baseline. No pull request submission is permitted with a known full-gate failure.

## Current state

The sole live status, approval record, role/check evidence, spending metrics, blockers, and next action are in [the setup plan's Current state](setup-plan.md#current-state). This pointer prevents a competing status copy. Final candidate identity and checks belong outside its tracked tree in conversation or the eventual pull request.
