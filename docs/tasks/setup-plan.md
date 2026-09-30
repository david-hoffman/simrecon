# SETUP: install and demonstrate delivery infrastructure

**Version 1.0** Git versions edits. This plan does not approve scientific features.

## Plan, scope, and adoption decisions

The owner approved Python/NumPy/SciPy and an eight-hour setup pass starting September 30, 2026 at 18:29:01 UTC; hard stop October 1 at 02:29:01 UTC. The later repository-configuration request authorizes native GitHub settings. See [project](../PROJECT.md) and [read-only baseline](../setup/BASELINE.md).

Installation: preserve the single specification, reconcile AGENTS, install four skills, record architecture/baseline, archive required references once, establish locked Python checks and ordinary CI, configure GitHub protections, and demonstrate the delivery cycle and doctor. Estimated allocation: inventory/records/tooling 2 hours; reviewed helper/test-infrastructure demonstration 3 hours; exact-candidate verification/fresh D/PR/CI 2 hours; doctor and handoff 1 hour. These allocations share one eight-hour ceiling and are not promises of completion.

Product remediation: none authorized. Legacy build recovery and global legacy coverage would block any small legacy slice; the owner chose a pristine library with the old tree as unshipped study material. New scientific APIs, input conventions, numerical oracles, datasets, performance targets, and porting estimates need subsequent intake. Setup success does not establish scientific readiness.

Documentation/reference work and environment preparation can proceed independently. The runtime demonstration depends on completed infrastructure and approval of the contract below. A then B precede a committed test checkpoint; fresh C follows that checkpoint; full exact-candidate verification precedes fresh D and the normal PR. CI repeats the gate. The real doctor demonstration is a subsequent setup-completion item: after the bootstrap delivery task and its required integration finish, use a separate clean docs worktree, then wait for owner approval of its patch. It is not a pre-PR prerequisite. No dependent slice starts against an unintegrated prerequisite.

## Contract: proposed coherent bootstrap slice

- Slice ID: SETUP-BOOTSTRAP. Baseline: installed infrastructure on `codex/delivery-setup`, identified by its eventual checkpoint; no scientific runtime exists.
- Purpose: a thin native `delivery doctor` invocation and minimal pytest infrastructure that rejects incomplete test runs. No product algorithms, controller, permission enforcement, retry loop, or remote-state query in the helper.
- Public command: `uv run --locked delivery doctor [--check]`, invoked from this repository root. The existing console entry point is `simrecon._delivery:main`.
- Default mode delegates once to a new native Codex root using `review-work` in doctor mode and `DOCTOR-PROMPT.md`. It permits that session's bounded docs-branch patch and requires owner approval before commit/push/merge. `--check` delegates in read-only mode and requests report-only behavior. Optional memories/delegation are disabled. Existing Codex authentication is used; nothing is installed or retried by the helper.
- Child stdout/stderr remain observable. Normal child exit status is returned. Missing `codex` returns 127 with an actionable message. Invalid syntax returns 2 without starting Codex. No numerical calculation or scientific tolerance is involved; process arguments, text, file effects and integer exit status have exact expectations.
- Pytest's complete-suite command must reject skips, expected failures, unexpected passes and empty discovery while retaining their diagnostic reports. A small pytest hook may fill native gaps; it is included in owned-runtime coverage. Ordinary failing tests already fail natively.
- Authorized C files: `src/simrecon/_delivery.py` and `src/simrecon/_pytest_policy.py`. A owns test/fixture files. Coordinator installs the agreed plugin in test configuration before the reviewed checkpoint. CI/configuration is setup work, not ordinary C editing scope.
- Checks: `make verify`; 100% native measured statements and branches for all owned runtime, including these helpers and subprocesses. Subprocess tests may substitute a controlled executable at the external Codex boundary. Such tests establish wrapper behavior only; the actual doctor demonstration must launch a real fresh root and evidence its spec diff.
- Budget: the remaining setup cap; default two A/B rounds and one C repair. A second nonacceptance requires B's diagnosis before another rewrite. Renaming/splitting retains consumed time, reviews and repair allowance.

| Scenario | Input and observable outcome | Expected-result source | A test mapping |
|---|---|---|---|
| D1 | `delivery doctor`, available harness exits 0: one fresh native doctor invocation in write-capable mode; output and success preserved | Existing specification procedure plus proposed CLI contract | Pending A |
| D2 | `delivery doctor --check`, available harness exits 0: one read-only/report-only invocation; output and success preserved | Approved report-only doctor behavior | Pending A |
| D3 | Unsupported flag: exit 2, syntax diagnostic, no harness invocation | Proposed CLI error contract | Pending A |
| D4 | Available harness exits 7: return 7, preserve diagnostics, no retry | Proposed process-boundary contract | Pending A |
| D5 | Harness unavailable on PATH: exit 127, actionable diagnostic, no installation | Proposed environment-error contract | Pending A |
| T1 | Complete discovered suite with one passing test: success | Full verification requirement | Pending A |
| T2 | Empty discovery: nonzero exit with no-tests diagnostic | Native pytest empty-discovery behavior | Pending A |
| T3 | One skipped test: nonzero exit with skip diagnostic | No silently omitted verification | Pending A |
| T4 | One expected-failure test: nonzero exit with expected-failure diagnostic | Known failure blocks submission | Pending A |
| T5 | One unexpectedly passing marked test, even when its marker opts out of strict mode: nonzero exit with diagnostic | Marked exceptions must not hide incomplete verification | Pending A |

This is **10 distinct scenarios**. The default is five; this coherent bootstrap slice needs explicit owner approval as a larger slice. Keeping the verification hook and launcher together makes the first integrated infrastructure candidate subject to the full global gate. Alternatively, the owner may choose two sequential five-scenario slices; neither may claim complete setup until its global verification dependencies are satisfied. No larger scientific slice is implicitly approved.

Initially passing existing-infrastructure tests are valid. Missing new helpers are feature absence; missing dependencies are environment failures. Do not manufacture a product failure or count an import/tooling failure as an intended behavioral failure.

## Current state

- Status: installation authorized and in progress; exact bootstrap contract awaits read-back approval.
- Approvals: Python architecture/eight-hour setup and subsequent GitHub configuration authorized in this conversation. Ten-scenario size exception and contract not yet approved.
- Reviewed checkpoint: none. A/B/C/D: none launched yet. Support/discovery subagents and a native CLI launch probe are not delivery role evidence.
- Candidate and final verification: to be recorded outside the candidate tree in this conversation and eventual PR. No PR exists; no submission permitted while the full gate is incomplete.
- GitHub: native `main` protection applied and read back September 30, 2026. Require PRs; `Verify (ubuntu-24.04)` and `Verify (macos-15)` from native GitHub Actions app ID 15368; current branch required; administrators covered; force pushes/deletion disabled; conversations resolved; zero required human approvals. Read-only default Actions token and inability to approve PRs preserved. [Evidence](../setup/evidence/github/protection-applied.json). No workflow run or observed blocked merge yet. No deliberately failing PR will be submitted to create evidence.
- Baseline: [read-only record](../setup/BASELINE.md). New full verification blocked pending helper/tests. Partial tool loading, lock validation, source lint/type checks and native launch probe do not establish full verification or 100% coverage. The network-enabled dependency audit subsequently passed for 23 packages; the earlier sandbox DNS failure is stale. The 24-package lock validates. Installed pre-commit/pre-push Ruff hooks passed a source-file probe. These partial checks do not replace the full gate.
- Metrics: scenarios=10 proposed / 0 approved; A/B rounds=0/2; C repairs=0/1; setup budget=8 hours total, 24 minutes 45 seconds elapsed / 7 hours 35 minutes 15 seconds remaining as of 18:53:46 UTC, hard stop 02:29:01 UTC; token/dollar spend unavailable. No rename/split resets consumption.
- Blockers before submission: contract approval; fresh role/checkpoint evidence; full local verification. Subsequent completion evidence: CI, observed protections on the normal verified PR, owner integration, and real doctor demonstration. Scientific behavior and full-paper conversion remain separate unresolved work.
- Next: owner contract read-back; meanwhile coordinator completes authorized installation records and reference fidelity checks. After approval, launch fresh A with only Contract/public context, then fresh B; commit the accepted checkpoint before C.
