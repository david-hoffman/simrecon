# SETUP-DOCTOR: launch and demonstrate delivery doctor

**Version 1.0** Git versions revisions. This record is not technical enforcement.

## Contract

- Slice plan/reference: [setup plan](setup-plan.md). Second sequential setup slice, D1–D5. Prerequisite: completed SETUP-TEST-RUN exact-candidate checks and fresh D review, integrated into the setup branch. The coordinator identifies that integrated revision before A.
- Project/interface references: [approved project](../PROJECT.md), public `uv run --locked delivery doctor [--check]` command invoked from the repository root, and the existing doctor procedure and `DOCTOR-PROMPT.md`. Fresh blind A/B packets exclude implementation and task state revealing implementation.
- Purpose: a thin native doctor command launches one fresh Codex root and propagates observable process results. It does not implement a controller, permission enforcement, retry loop, remote-state query, scientific feature, or package installation.
- R1: Default mode makes one fresh native doctor invocation in write-capable mode. `--check` makes one read-only/report-only invocation. Both preserve child output and successful exit.
- R2: Unsupported syntax exits 2 with a diagnostic before any harness invocation. A child exit 7 returns 7 with diagnostics and no retry. Missing `codex` on PATH exits 127 with an actionable diagnostic and no installation.
- Inputs, outputs, errors, and permissions: the command uses the user's existing Codex authentication. It disables optional memories and delegation, supplies the doctor prompt, and retains child standard output, standard error, and integer exit status. Default mode permits the fresh session's bounded documentation patch but requires owner approval before commit/push/merge. `--check` requests report-only behavior. The helper launches once and never retries or installs tools.
- Expected-result sources: the owner-directed setup, unchanged cases in the earlier read-back, and existing doctor procedure. Exact process arguments, output, file effects, and exit status are the oracles; no numerical tolerance applies.
- Allowed scope and checks: A owns public-interface tests/fixtures and B reviews them. C may edit only `src/simrecon/_delivery.py`; C must not change reviewed tests, fixtures, snapshots, workflow, discovery, coverage settings, skills, or delivery instructions. The coordinator owns the setup script/configuration. Run `make verify`, requiring 100% native measured statements and branches across all new owned instrumentable runtime, including subprocesses and never-imported files. Report unsupported native measurements.
- Preparation/execution budget: remaining time in the single eight-hour setup cap ending October 1, 2026 at 02:29:01 UTC. Shared with SETUP-TEST-RUN: default two A/B review rounds per window and one C repair after initial C. The first slice's actual spending and review history carry forward.

| Scenario ID | Approved input/context and observable success, error, or boundary outcome | Expectation source | Test mapping supplied by A and checked by B |
|---|---|---|---|
| D1 | `delivery doctor`, available harness exits 0: one fresh native doctor invocation in write-capable mode; output and success preserved | Existing specification procedure plus proposed CLI contract | `tests/test_delivery.py::test_doctor_invokes_one_write_capable_native_run` |
| D2 | `delivery doctor --check`, available harness exits 0: one read-only/report-only invocation; output and success preserved | Approved report-only doctor behavior | `tests/test_delivery.py::test_doctor_check_uses_read_only_native_run` |
| D3 | Unsupported flag: exit 2, syntax diagnostic, no harness invocation | Proposed CLI error contract | `tests/test_delivery.py::test_doctor_rejects_unsupported_flag_without_invocation` |
| D4 | Available harness exits 7: return 7, preserve diagnostics, no retry | Proposed process-boundary contract | `tests/test_delivery.py::test_doctor_forwards_native_failure_without_retry` |
| D5 | Harness unavailable on PATH: exit 127, actionable diagnostic, no installation | Proposed environment-error contract | `tests/test_delivery.py::test_doctor_reports_missing_codex_on_path` |

These five scenarios are unchanged from the ten-case read-back. A may substitute a controlled executable at the external Codex boundary to test wrapper behavior. That is not evidence of an actual doctor run. Before repair, the observing role classifies failures as environment/tooling, test defect, product defect, or unresolved requirement. A's mapping goes into this table only after authoring and B review, without changing approved behavior.

After reviewed code, exact-candidate full verification, and fresh D, integrate this slice into the setup branch. The real doctor demonstration then launches a fresh native root from that integrated baseline in a separate clean documentation worktree. It must produce an inspectable specification diff without altering in-flight instructions. Do not commit or push the documentation patch until owner approval. The two slices make one normal setup pull request only after full exact-candidate verification; CI repeats the gate. Owner merge to `main` is a separate action.

## Current state

The sole live status, approval record, role/check evidence, spending metrics, blockers, and next action are in [the setup plan's Current state](setup-plan.md#current-state). This pointer prevents a competing status copy. Final candidate identity and checks belong outside its tracked tree in conversation or the eventual pull request.
