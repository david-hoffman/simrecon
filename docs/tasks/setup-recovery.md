# DEV105: make setup and task recovery reproducible

**Version 1.0.** Git versions revisions. Sole Current state for issue #105 work.

## Contract and authorization

Human request: `/intake 105`, November 12, 2026. Prepare the concrete contract
and narrow future execution packets for
[fix(dev): Make setup and task recovery reproducible](https://github.com/david-hoffman/simrecon/issues/105).
Use [DEV105 R1–R6/S01–S17](../contracts/setup-recovery-v1.md).
The intake wrote documentation only. The subsequent owner instruction
**“Approved”** authorizes execution of this concrete scope. The coordinator now
assigns the bounded worker packet; sign-in and scientific roles remain outside
this infrastructure task. No second approval of this record is needed.

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
At the intake baseline there was no separate non-installing local readiness
command or portable bootstrap guide. The contract adds those and a recovery procedure using the
existing mechanisms, without amending permissions or delivery policy.

Remote read of #84's original saved task at
`f8042042ff2b6865ecf501e38f11232de5d36fc9` succeeded. That Git object was absent
from the intake checkout; execution recovered it in a separate clone. Do not confuse the
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
- Bounded worker owns new `scripts/check_dev_environment.py`,
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
- Worker/reviewer: `gpt-6.1-sol`, high, conservative current project
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

- **Implementation candidate prepared under “Approved”.** Execution baseline is
  `fdcb0fa76c35a522035b532435f1bc2593eb579f`, tree
  `c8f8d2fdf45007db0912d7dd3619a0010de986d4`, on
  `fix/105-setup-recovery`. The coordinator assigned the existing worker packet.
  Final candidate/check/review status is recorded outside tracked candidate
  bytes in the conversation and local `artifacts/setup-recovery/` evidence;
  the [sanitized report](../reports/setup-recovery.md) retains portable facts.
- Roles: one bounded worker `setup_worker` owns named code/tests/operational docs;
  one operational helper `ubuntu_exercise` performs fresh container setup/repeat
  and recovered-checkpoint preflight. Coordinator owns recovery identity/accounting,
  report, task, full gate and fresh independent review. Helpers do not replace the
  reviewer or any #84 scientific role. Requested worker/helper configuration is
  `gpt-6.1-sol`, high; served attribution, tokens/responses/cost and aggregate
  elapsed/check/owner-wait totals remain unknown. Human limits not set.
- Prerequisites: current Debian host preflight attempt 1 failed on sandbox proxy
  access; same pinned command passed after approved escalation on attempt 2.
  Docker socket probe similarly failed in sandbox and passed after escalation.
  Fresh original #84 clone attempt 1 failed on sandbox proxy connection; attempt 2
  succeeded. Checkpoint, ancestors and six documents recovered with clean state;
  historical ignored logs unavailable. See report/manifest for exact identities.
- Platform evidence: fresh Ubuntu 24.04 first/repeat setup and recovered #84
  preflight passed; final readiness script passed. No macOS 15 executor is
  attached; the coordinator asked whether one is available. Missing platform
  evidence remains a final acceptance/submission blocker. No lowered gate, policy
  amendment or new scientific acceptance is implied. Native sign-in was not probed.
- Intake accounting remains: coordinator plus one read-only helper with inventory
  and continued packet sanity pass; scenarios=17, intake contract correction=1
  (clarified Java launcher proof deferred to preflight). Initial prompt path error,
  two failed CLI issue reads, successful HTML/connector reads, unavailable local
  #84 object, corrected unrelated remote-task lookup and no-index status-wrapper
  correction remain discovery facts. They are not product failures. The first
  intake HTML scratch file was removed and absence confirmed.
- Implementation: 21 new readiness cases plus 11 unchanged preflight cases passed
  twice; lint/format and focused types passed. Three sandbox type-check failures
  and two successful escalated runs are retained. One safe-metadata correction
  and one formatting correction preserve their diagnoses. Ubuntu helper retained
  two input-permission preparation failures and one additional sandbox socket
  denial before successful exercise. See the report for commands and limits.
  Implementation/check/review attempts are cumulative in worker/Ubuntu reports
  and the sanitized report; final gate/review results stay outside
  tracked candidate bytes. Prior #84 charges are preserved in the pinned task and
  later diagnostic comment, without recounting them as new #105 launches.
- Next: preserve missing-platform evidence, prepare clean candidate, run full
  verification and obtain fresh independent review. No push/PR/merge/release or
  external message is authorized. No accepted scientific checkpoint is invented.
- Housekeeping: after all exercise processes completed, removed the stopped
  `simrecon-issue105-ubuntu-exercise` container and confirmed-disposable
  `/workspace/scratch/setup-recovery-105-checkpoint`,
  `/workspace/scratch/setup-recovery-105-ubuntu`, and worker pytest scratch
  `/tmp/pytest-of-agent/pytest-5` / `pytest-6`; filesystem absence confirmed,
  container removal succeeded, no cleanup errors. Recovered clone was clean and
  original commits remain in their source repository. Keep current checkout/
  branches, durable documents/local evidence, shared tools/caches and official
  Ubuntu image (shared-cache ownership uncertain). No #84 Current state was edited.

## PR presentation

If later authorized, explain the reproducible setup and recoverable checkpoint
behavior first. A figure adds little to this procedural change and is omitted.
Use the existing PR template with an appendix for exact identities, fresh/repeated
setup commands, recovery manifest and missing evidence, independent review,
coverage, full verification and separate platform limits. Setup does not establish
scientific acceptance or repair an unreachable executor.
