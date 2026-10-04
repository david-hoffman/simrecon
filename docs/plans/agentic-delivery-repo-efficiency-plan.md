# Plan: improve delivery efficiency in SIMrecon

**Version 1.0. Proposed October 3, 2026.** This is a plan, not an approved change to delivery rules. Writing it does not authorize implementation, publication, or additional repairs on an existing task.

## Recommendation

First reduce repeated reading, handoff writing, environment recovery, and verification bookkeeping within the current rules. Then adopt a lighter delivery route for routine maintenance and bounded fixes, after approving the corresponding [specification changes](agentic-delivery-spec-efficiency-plan.md).

Keep four independent roles for work where incorrect expectations or implementation could invalidate scientific results, corrupt files, lose data, or expand execution permissions. Keep the current 100% measured statement and branch coverage requirement for owned runtime. The intended savings come from doing less repeated coordination, not reporting less evidence.

## Baseline and scope

Implementation handoff: branch `codex/delivery-efficiency` now starts at merged main `b365b461e878ded267cc98adf55651c93cf66d38` in `/Users/davidhoffman/.codex/worktrees/delivery-efficiency/simrecon`. That baseline includes the converter and NumPy docstring linting. The earlier checkout observations below are historical evidence; implementation does not need to integrate or repeat those tasks.

Two checkouts contain different stages of the same repository:

| Checkout inspected | Revision | Relevant state |
|---|---|---|
| Workspace `/Users/davidhoffman/Documents/GitHub/simrecon` | `c2a3e78d2cf4160e99c7ec416b85ce0d7e8202fb`, branch `codex/delivery-setup` | Installed delivery scaffold, four role skills, doctor wrapper, hooks, full verification and CI. No converter in this checkout. |
| Conversion worktree `/Users/davidhoffman/.codex/worktrees/540f/simrecon` | `aa17fe5bce9b90c427e4d4856b3d31229b57cca1` | Completed converter plus the separate NumPy docstring-lint configuration follow-up. The converter's verified completion revision was `be5a5379a4232f62d0411da28a51dd1d6102984d`. |

The plans are saved in the workspace checkout. They do not integrate either branch. Implementation must name its intended baseline and preserve independently completed work; it must not replay the lint task or assume the converter has already entered the workspace branch.

The installed sources are [AGENTS.md](../../AGENTS.md), [PROJECT.md](../PROJECT.md), the four skills under `.agents/skills/`, [Makefile](../../Makefile), [pyproject.toml](../../pyproject.toml), [hooks](../../.pre-commit-config.yaml), [CI](../../.github/workflows/verify.yml), and the [doctor wrapper](../../src/simrecon/_delivery.py). The canonical command remains `make verify UV=/Users/davidhoffman/.local/bin/uv` on this workstation.

## Evidence and limits

- The converter needed 26, then 44, then 46 approved scenarios and three A/B windows. Initial tests passed while coverage was incomplete. Later independent review found a contract restriction that passing coverage had missed. See the [task history](/Users/davidhoffman/.codex/worktrees/540f/simrecon/docs/tasks/architecture-intake.md:56), [initial coverage report](/Users/davidhoffman/.codex/worktrees/540f/simrecon/artifacts/mrc-conversion/roles/c-initial-report.md:9), and [D finding](/Users/davidhoffman/.codex/worktrees/540f/simrecon/artifacts/mrc-conversion/roles/d-report.txt:3).
- Test review caught four real oracle/assertion defects. Independent review is useful; its cost should be reserved for the work that needs it. [B findings](/Users/davidhoffman/.codex/worktrees/540f/simrecon/artifacts/mrc-conversion/roles/b-round1-report.txt:1).
- Repair verification repeated after sandbox DNS failures during the wheel build. Native memory measurements also ran separately after the canonical suite exercised them. [C2 evidence](/Users/davidhoffman/.codex/worktrees/540f/simrecon/artifacts/mrc-conversion/roles/c-keys-report.md:9).
- An ambiguous packet caused a reviewer to launch another reviewer, requiring termination and a fresh launch. [Tooling incident](/Users/davidhoffman/.codex/worktrees/540f/simrecon/artifacts/mrc-conversion/roles/d-keys-launch-attempt1-tooling.json:3).
- Coordinator accounting through conversion completion contains 191 model responses, 20,103,480 input tokens, 19,453,184 cached input tokens, and 164,107 output tokens. Thus uncached input was `20,103,480 - 19,453,184 = 650,296`; cached input was about 96.8%. These counters include repeated context processing, not that many unique words or an equivalent dollar charge. Complete separate-role costs are unavailable. [Local usage record](/Users/davidhoffman/.codex/sessions/2026/10/01/rollout-2026-10-01T07-45-45-01a0f7ed-b340-7bc1-92e5-35af975d4ad4.jsonl:1592).

These local links identify existing evidence; they are not portable CI inputs. Do not copy session transcripts or owner data into Git. No measured savings percentage is available, and a substantial converter is not a fair timing baseline for a small lint change.

## 1. Shorten the operational path

**Priority: first. Policy dependency: none for using existing narrow-input rules.**

- Reconcile `docs/PROJECT.md` on the chosen integration baseline. Keep current architecture, environment, supported commands, and public-contract links easy to find. Move superseded interviews, installation deadlines, and old launch observations behind historical links. Do not reinterpret pending scientific work as approved.
- Keep shared instructions in `AGENTS.md`; keep role differences in the four skills. Replace duplicate explanations with links. Do not add a second live workflow or require routine workers to read the entire specification.
- Prepare short public-input packets for A/B and separate candidate packets for C/D. A/B must not receive the Current state section, implementation history, implementation-derived coverage locations, or coordinator conversation. A coverage gap must be translated into an already approved public behavior or returned to intake.
- Reports should state verdict, findings, changed scope, commands/results, and evidence pointers. Reference unchanged scenario mappings and environment records rather than repeating them. Retain one Current state section, not one per report.
- At a substantial phase boundary, use a fresh coordinator with a compact handoff if the existing context is dominated by completed work. Preserve approvals, spending, blockers, and evidence. This does not refresh allowances or justify frequent session churn.

**Acceptance:** a fresh worker can identify its permitted inputs and exact commands without a broad document sweep. A/B packet inspection finds no implementation-bearing input. Current policy remains intact. Instruction edits use the authorized documentation-maintenance procedure; shortening prose is not permission to remove a gate.

## 2. Make verification produce reusable evidence

**Priority: second. Policy dependency: approved infrastructure maintenance; exact-candidate submission rules stay intact.**

Propose a cheap `make check` for synchronized-environment lint, formatting and types. Keep `make verify` as the full locked dependency, test/coverage, build/import and audit gate. Share Make prerequisites so the two commands cannot drift; a cheap pass must never be presented as full verification.

Prepare task pointers and intended documentation before the final candidate commit. Run full verification once for that candidate, and let D inspect its applicable evidence. A source, test, fixture, dependency, check, environment or baseline change invalidates affected evidence. Until a narrower rule is explicitly adopted, a changed candidate still receives the required exact-candidate full run before submission.

Have the full command emit one ordinary JSON receipt alongside logs in ignored `artifacts/`. Record:

- Candidate identity and clean/dirty state; approved contract and reviewed-test revision where applicable.
- Commands, exit statuses, environment/platform, and source/test/fixture/lock/check fingerprints.
- Exact statement and branch numerators/denominators, scope, missing/excluded items and report paths.
- Native memory or other task-required measurements already collected by the tests, so a second run is not needed solely to obtain numbers.

The receipt is evidence by convention, not a signed certificate, evidence database, or substitute for reading failures. Missing required reports fail verification. D should not automatically repeat a successful full run whose inputs remain applicable.

Resolve dependency-cache and network prerequisites once through authorized setup. Document a known-working environment for each role; put cheap environment checks before expensive work. Preserve failed attempts. Do not add silent retries, unconditional sandbox elevation, or offline success claims for a check that requires network access.

**Files likely affected:** `Makefile`, `docs/PROJECT.md`, CI artifact paths if needed, a small verification helper if necessary, and its public-entry tests. New Python helpers remain owned runtime with 100% statement/branch measurement. Make and YAML receive command-path evidence, not invented Python coverage.

**Acceptance:** a successful full run produces its receipt without follow-up measurement runs; a failed check or missing report cannot produce a passing receipt. Changed inputs invalidate reuse. The existing supported CI matrix continues to run full verification.

## 3. Standardize role launch only where it removes demonstrated work

**Priority: third, optional after the first two improvements. Policy dependency: approved tooling task.**

Use one documented, tested native launch path. If commands and reusable packets suffice, add no runtime wrapper. If a helper is justified, keep it small: one explicit role, one packet, one worktree, one native process, one report destination. It must not schedule subsequent roles, choose repairs, create approval, or retry automatically.

Make “you are this role; do not launch another role” explicit. Use supported memory/delegation controls. Validate packet paths and the working directory, preserve native failure status, and keep model/environment selection in project configuration. Avoid a special orchestrator agent whose only job is to spawn the actual worker.

Provide tested source-free warning/traceback rendering for blind probes. Keep exception categories/messages, locations and failure status. Test it with disposable failures and warnings, including subprocess output; disclose unsupported channels. Do not claim these prompts or formatting helpers create engineered filesystem isolation.

**Acceptance:** one launch creates exactly one native role; failures return without retries. A/B diagnostic probes expose no source snippets. A live bounded launch complements controlled tests. Any new helper receives full owned-runtime coverage and independent review of its execution permissions.

## 4. Adopt lighter routes only after the policy decision

**Priority: after specification approval.**

| Route | Proposed SIMrecon use | Review |
|---|---|---|
| Routine maintenance | Prose, formatting, approved lint settings or dependency maintenance with no product behavior change | One worker; fresh independent review mandatory when dependencies, workflows, checks, or authority change. |
| Bounded existing behavior | A local non-scientific defect with settled expected behavior and a narrow impact | One worker writes regression tests and repair; one fresh reviewer reviews both. |
| Independent scientific/high-risk delivery | Numerical expectations, acquisition axes/units, pixel encoding, binary formats, data-loss prevention, or execution authority | Fresh blind A, blind B, C, and D; reviewed tests remain frozen for C. |

Choose by impact and unresolved expectations, not lines changed or task name. A prose-only edit in a scientific module can be routine; a three-line endian repair is high risk. A policy/gate change cannot lower its own review requirements by calling itself mechanical.

Before adoption, update the approved specification, then synchronize `AGENTS.md`, skills and package templates/prompts. Do not give a future light-route worker today's C restrictions and expect it to author tests; the permitted ownership must be explicit. Preserve current in-flight tasks and their consumed budgets/repair allowances. The separate lint task is not retroactively reclassified.

The specification plan also proposes accepting a complete explicit owner request as authorization for the first two routes, and allowing A/C authors to continue their own correction sessions within unchanged scope. Reviewers remain fresh and independent; a blind A exposed to implementation cannot continue blind work. These exceptions need policy approval before installation here. They do not permit a repair allowance to reset.

## 5. Prevent late acceptance work

For independent tasks, intake and B should check a compact matrix of normal operation, invalid input, representational limits, operation-time failure, external compatibility and public documentation. Start from public requirements, not anticipated private implementation branches. Some coverage gaps will still appear; handle them honestly.

The specification plan distinguishes new behavior from additional test examples of accepted behavior. Adopt that distinction here after approval. Changed high-risk tests still need independent A/B review, but corrections can focus on the changed tests and shared oracle/fixture impact instead of reproducing the entire prior review.

Public API documentation must enter acceptance before C. The lint follow-up has already enabled Ruff's NumPy-convention `D` rules in the conversion worktree; preserve that work rather than install a competing linter. Lint does not prove that units, shapes, errors or memory promises are accurate, nor automatically document every exported object defined in a private module. D must check those semantics against the contract.

## Rollout, measurement and owner decisions

1. Approve the specification decisions separately from tooling scope. Name the integration baseline; do not merge branches as a side effect of this plan.
2. Apply the short-document/packet cleanup using the current rules. Review the affected instruction diff and synchronize required templates.
3. Implement verification/environment improvements as a bounded maintenance task. Add launch tooling only if repeated launch or diagnostic work still warrants it.
4. After policy adoption, pilot the routine and bounded routes on three genuinely small tasks. Exercise the independent route on one representative task or existing synthetic case. Do not rerun the completed owner-data conversion merely for a process benchmark.
5. Compare active elapsed seconds, owner-wait seconds, model responses, cached/uncached input, output tokens, launches, review rounds and rework. Use native counters once per session; avoid double-counting cumulative observations and child usage. Mark unavailable counters unknown. Dollars require verified pricing and complete usage.

The pilot target is at most one worker plus one reviewer for a small task, with no repeated interview after a complete authorized request. Savings are a measurement goal, not a promised percentage. Keep the route only if correct outcomes, required review and checks remain intact; rework, source exposure or missed obligations trigger reassessment.

Owner decisions still needed for execution: the three-route policy and its approval boundary; whether to build receipt/launch helpers or initially use documented commands; the integration baseline; and a bounded maintenance budget. This plan lowers no threshold, renews no consumed allowance, and authorizes no push, PR, merge or release.
