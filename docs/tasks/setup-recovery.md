# DEV105: make setup and task recovery reproducible

**Version 1.0.** Git versions revisions. Sole Current state for issue #105 work.

## Contract and authorization

Human request: `/intake 105`, November 12, 2026. Prepare the concrete contract
and narrow future execution packets for
[fix(dev): Make setup and task recovery reproducible](https://github.com/david-hoffman/simrecon/issues/105).
Use [DEV105 R1–R6/S01–S17](../contracts/setup-recovery-v1.md).
This intake writes documentation only; no executable tests, product/infrastructure
implementation, sign-in or scientific role execution is part of this turn.
The packets are dormant future-entry instructions, not launched work or acceptance.
No second approval of a record restating the request is needed.

Baseline: `4dcc50dd70da2f93b4a3360e0a4160144656b35a`, initially clean current
checkout. Intake branch: `docs/105-setup-recovery-intake`; proposed implementation
branch: `fix/105-setup-recovery`; proposed PR title:
`fix(dev): Make setup and task recovery reproducible`. This intake only references
#105; it does not close it. #84 stays a separate scientific task.

## Observed and proposed

The issue and its authorized diagnostic comment report a recovered #84 commit,
missing ignored logs, mismatched PATH tools, a successful explicit pinned preflight,
native sign-in uncertainty and a later offline executor. These are dated reported
observations, not this session's reproduction or a known common root cause.

Local inspection confirms `make preflight` begins with locked setup/reader
preparation, prints uv version without enforcing it, checks exact worktree Python
and import identity, and checks isolated hatchling. Existing reader preparation
checks Java 21.0.7/source-launcher behavior and authenticates jars; it preserves
corrupt input for diagnosis. CI pins uv 0.12.19, Python 3.13.12 and Temurin
21.0.7+6 on Ubuntu 24.04/macOS 15. Codex versions are observations, not pins.
There is no separate non-installing local readiness command or portable bootstrap
guide. The contract proposes those additions and a recovery procedure using the
existing mechanisms, without amending permissions or delivery policy.

Remote read of #84's original saved task at
`f8042042ff2b6865ecf501e38f11232de5d36fc9` succeeded. That Git object is absent
from this local checkout; no recovery exercise has run. Do not confuse the
unrelated historical `simulation-reconstruction-memory.md` task with #84's
`reconstruction-memory-intake.md`. The pinned remote task and later issue comment
remain the recovery expectation sources. They carry their own historical charges;
this task references them without resetting or duplicating their counters.

## Route, ownership and checks

- **Bounded infrastructure**, one worker and fresh independent bounded reviewer.
  Conventional setup/diagnostic reporting reuses existing installation/check
  mechanisms. No security enforcement, new execution permissions, scientific
  oracle, data-loss repair or delivery-policy amendment is authorized. Return
  expanded meaning to intake; proposed policy changes need their own fresh policy
  verdict before activation. This record changes no active policy.
- Future worker owns new `scripts/check_dev_environment.py`,
  `tests/test_dev_environment.py`, `docs/operations/bootstrap.md`,
  `docs/operations/task-recovery.md`, and operational updates to
  `docs/operations/environment.md` and `docs/operations/role-launches.md` strictly
  preserving their existing role/permission/gate rules. Existing
  `tests/test_delivery_preflight.py` may gain meaningful compatibility cases;
  do not remove/weaken its assertions. No Makefile change is needed or authorized.
- Coordinator owns this task/contract/packets, the local execution evidence under
  `artifacts/setup-recovery/`, and a sanitized durable summary at
  `docs/reports/setup-recovery.md`. Reviewers report only. The operational docs
  cannot silently amend templates/AGENTS/skills/specification or enable a new role
  route. No product files, locks, dependency manifests, CI, reader implementation,
  coverage/discovery settings or global environment changes are assigned.
- Future worker/reviewer: `gpt-6.1-sol`, high, conservative current project
  selection; lower-cost calibration remains pending for this responsibility.
  Record actual attribution/settings and missing metering as unknown. Diagnose
  environment, test, implementation and requirement failures separately; concrete
  reasoning limitations justify scoped escalation, not silent model fallback.
- Run cheap interpreter/tool/lock/import prerequisites before dependent work;
  run documented bootstrap twice in fresh supported environments and existing
  `make preflight` with selected pinned tools. Exercise S12–S16 using #84's saved
  checkpoint in a disposable clone, without resuming scientific execution.
  Record supported-platform evidence separately; unavailable platforms remain
  acceptance gaps, not exclusions. Controlled command fixtures do not replace
  actual fresh setup or recovery evidence.
- Focused checks: `uv run --locked python -m pytest tests/test_dev_environment.py
  tests/test_delivery_preflight.py`, named-file Ruff checks and project type checks.
  Readiness output tests use synthetic subprocess tools through its public command
  and actual caller cases; avoid private-state tests or artificial product-red.
  Inherit PROJECT behavior/risk coverage, advisory percentages and mandatory native
  reports. Preserve the full-local gate and all contract R6 obligations.
- Final acceptance requires fresh independent review of the exact fully passing
  candidate and scenario/evidence mapping, plus required platform proof. Prepare
  the sole state pointer before full `make verify`; final identity/results stay
  outside tracked candidate bytes. Missing evidence or known check failures block
  submission, including a draft. No PR/push/issue comment/closure/merge/release
  or publication of raw evidence is authorized by this intake.
- Human scenario/review/repair/time/spend limits: **not set**. Diagnose before
  retries; all failures/repairs/reviews and parent historical charges persist.

## Current state

- **Intake complete; execution not started.** Contract and
  [worker](../packets/setup-recovery-worker.md) /
  [reviewer](../packets/setup-recovery-reviewer.md) packets prepared for future
  assignment. No material decision is missing for this bounded scope. Runtime,
  tests, policy, pins and gates are unchanged. Full setup/recovery/platform proof
  remains future work, not an intake failure or acceptance claim.
- Inputs: issue body and one comment read November 12, 2026 through GitHub
  connector; pinned #84 task and commit read remotely. Current shell is usable;
  managed status reported connected/current with enforced network policy.
  These observations do not qualify local dependencies or native sign-in.
- Discovery failures: initial INTAKE-PROMPT path lookup was corrected; `gh issue
  view` failed once with sandbox socket denial and once with Forbidden after
  approved escalation. Public issue HTML fetch and connector reads succeeded.
  Local `git cat-file` could not find the #84 commit; remote read verified the
  named source. One initial remote task lookup returned an older unrelated task;
  the commit's changed-path inventory resolved the correct filename. These are
  discovery/tooling facts, not product failures or recovered acceptance evidence.
  The first new-file whitespace wrapper mistook Git's no-index difference status
  1 for failure; corrected status handling retained empty whitespace diagnostics.
- Roles/accounting: one intake coordinator, one read-only setup inventory helper
  (`setup_inventory`, inventory plus a continued packet sanity pass); no
  implementation worker, scientific roles or required
  acceptance reviewer launched. Scenarios=17; executable examples/tests not yet
  authored. Intake helper configuration inherited; actual served model/effort,
  per-role tokens/responses/cost and aggregate elapsed/check/owner-wait totals
  unknown. Implementation repairs/review rounds=0. Prior #84 charges remain in
  their pinned sources; not counted as new #105 launches. Limits not set.
  Continued advisory review identified one Java-check boundary ambiguity;
  clarified R2 to defer source-launcher/reader proof explicitly to preflight,
  preserving local version checks and the existing gate. Intake corrections=1;
  this sanity pass is not implementation or policy acceptance review.
- Checks: intake scope, relative links and whitespace only; command outcomes and
  final document identities recorded in the conversation outside these bytes.
  No preflight/full verification, authentication probe or platform recovery was
  run. Next: use the worker packet when implementation is assigned, then a fresh
  reviewer of the exact passing candidate; no public A/B packet is needed for
  this bounded work. #84 retains its own public A/B packets unchanged.
- Housekeeping: retain current checkout/branch, the four intake documents, shared
  tools/caches and unrelated work. The sole task scratch file is
  `/tmp/simrecon-issue-105.html`; removed after extracting source facts, absence
  confirmed, no cleanup error. No task background process or extra worktree was created.
  Future disposable setup/recovery clones must be listed by exact path before
  removal, with process/worktree/needed-commit checks under the existing
  [cleanup workflow](../operations/fixture-cleanup.md). Keep durable evidence
  outside them; retain uncertain targets.

## PR presentation

If later authorized, explain the reproducible setup and recoverable checkpoint
behavior first. A figure adds little to this procedural change and is omitted.
Use the existing PR template with an appendix for exact identities, fresh/repeated
setup commands, recovery manifest and missing evidence, independent review,
coverage, full verification and separate platform limits. Setup does not establish
scientific acceptance or repair an unreachable executor.
