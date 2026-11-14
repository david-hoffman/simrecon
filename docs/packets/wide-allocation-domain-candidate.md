# Issue 115 — restricted C / fresh D candidate packet template

**Version 1.0.** Coordinator must instantiate mode, checkpoint and exact candidate
fields before launch. This is nonblind candidate context, forbidden to A/B.
Perform the assigned role directly; no delegation or inherited reviewer history.

## Contract, route and inputs

Worktree `/workspace/work/issue-115`; branch `feat/115-wide-allocation-domain`;
intake baseline `b344e41a8b52de76d7cbbf8450319893904c3b8f`. Issue
[115](https://github.com/david-hoffman/simrecon/issues/115) commissions the
allocation-byte extension through implementation, high-risk review and eventual
stacked PR. `docs/contracts/wide-allocation-domain-v1.md` W01–W18 controls meaning.
Read AGENTS, PROJECT, that contract, the interface excerpt and assigned role
skill (`.agents/skills/implement-work/SKILL.md` C mode or
`.agents/skills/review-work/SKILL.md` D mode). Nonblind supporting evidence:
`docs/reports/issue-115/intake.md`; sole task state
`docs/tasks/wide-allocation-domain.md`. Intake launch evidence is
`docs/packets/wide-allocation-domain-intake-launch.md`; role accounting is
`docs/reports/issue-115/role-launches.md`. These are not blind inputs.

Risk: high-risk scientific representation boundary. Requested C/D
`gpt-6.1-sol`, high, conservative project default; actual attribution and
unavailable metering unknown. Diagnose before escalation; missing semantics
return to intake, test defects to blind A/fresh B, environment defects to setup.
Transport acceptance supplies no scientific qualification.

Accepted PR109 policy `b84b178` / integration `be8e447` permits new fresh tool
sessions with `fork_turns="none"`; no author/implementation inheritance for D.
Optional distinct memory/delegation/read-only controls are unavailable here.
Shared filesystem/permissions plus prompt-only file restrictions are disclosed
limits, not isolation. Coordinator records route/tool arguments, exact packet
digest, session ID, launch timestamp/status and completion artifact digests.
No nested launch, commit, push/restack, PR write, merge/release/issue closure or
external message authority for C/D.

## Required launch fields — fill before dependent work

* Mode/session ID/packet digest: **coordinator pending**.
* Actual integration parent: **coordinator pending**. Intake starts from current
  main; #112 is still pending and final stack parent is not an intake assumption.
* Contract/interface identities: **coordinator records SHA256 at launch**.
* B verdict/report and exact accepted test/fixture/mapping checkpoint with file
  digests: **pending**. C must not begin without it.
* Frozen complete tests/fixtures, including unchanged shared dependency identities:
  **coordinator supplies B-accepted manifest**. All tests/fixtures remain frozen
  to C, not just changed files.
* D exact candidate commit/tree/base, clean tracked state, full Ubuntu passing
  receipt/log/report/build/input identities: **pending**. D acceptance must not
  begin on an unverified or known-failing candidate.
* Separate detailed output report: C `docs/reports/issue-115/c-implementation.md`;
  D `/workspace/work/campaign/evidence/115/d-review-N.md`, cumulative N supplied by coordinator.
  Final assistant messages are separate. D writes outside candidate tracked bytes. Report/check evidence must be captured
  by the coordinator without changing an exact candidate after verification.

## C ownership and frozen restrictions

C may edit only the following runtime files as necessary to meet the contract:

* `src/simrecon/reconstruction/known_parameters.py`
* `src/simrecon/acquisition/layout.py`
* `src/simrecon/acquisition/modes.py`
* `src/simrecon/acquisition/preparation.py`
* `src/simrecon/workflow/config.py`

Use the smallest necessary subset. Preserve interfaces and real callers of the
approved metadata validators; no test-only helper. A byte-only storage cast is
not a reason to retain a signed32 byte ceiling. Preserve genuine element/index/
native/backend constraints, validation timing and operation semantics. No new
runtime module or unrelated interface is authorized without coordinator intake.
Other source may be read for actual caller/failure/ownership context but is not
an edit grant. `workflow/reconstruct.py`, `workflow/result.py` and
`workflow/summary.py` need no ownership merely because their behavior is checked;
diagnose any required expansion through the coordinator.

C also owns product documentation alignment only in:

* `docs/contracts/c-equivalence-known-parameters-v1.md`
* `docs/contracts/c-equivalence-acquisition-modes-v1.md`
* `docs/contracts/c-equivalence-workflow-v1.md`
* `docs/contracts/reconstruction-memory-v1.md`
* `docs/usage/c-known-reconstruction.md`
* `docs/usage/c-acquisition-modes.md`
* `docs/usage/c-workflow.md`
* `docs/usage/reconstruction-summary.md`

Update obsolete byte ceilings/target classification consistently, preserving
historical evidence qualification and scientific equations. The new authorized
contract itself, task state, policy/architecture and packets are coordinator/
intake owned. PROJECT's RM84 “no expansion implied” statement remains a valid
description of RM84; coordinator may separately add the new task reference.

C cannot edit tests, fixtures, snapshots, workflows, dependencies/lock, test
discovery/coverage/affinity, skills, delivery rules, verification infrastructure
or PR templates. Invalid frozen tests go to A/fresh B via sanitized public
requirements/test dependencies. A post-implementation addition is supplemental,
not original test-first evidence. D writes report only; no repair/self-approval.

## Checks, resource hold and evidence

Coordinator supplied isolated preflight success: Ubuntu 24.04, Python 3.13.12,
NumPy 2.5.3, SciPy 1.18.1. Do not turn that statement into C's command evidence.
Pinned uv is `/workspace/.simrecon-tools/uv-env/bin/uv`.
**Execution remains held until root releases the focused/full resource window;
no install/probe/test/lint/type/import/measurement during the hold.** Parent
integration/environment identity must be resolved before final checks.

After release use this container prefix:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-115 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  simrecon-campaign-ubuntu
```

Focused tests append `.venv/bin/python scripts/source_free_check.py --timeout
300 pytest` and
`tests/test_wide_allocation_domain.py tests/test_c_known_boundary.py
tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py
tests/test_reconstruction_summary.py`; verify inherited large-call rejection
assertions have first been safely corrected and accepted by B. Expand to affected
existing CE04/CE06/CE07 numerical/compatibility tests only after a diagnosed
need; full verification covers all preserved obligations. Narrow C quality checks
append `/workspace/.simrecon-tools/uv-env/bin/uv run --locked ruff check <owned
changed .py files>`, `ruff format --check <owned changed .py files>` and
`uv run --locked pyright <owned changed .py files>`. Record actual commands and
their status, do not infer passage from absence of errors in a report.

The full exact-candidate gate appends:

```text
make verify UV=/workspace/.simrecon-tools/uv-env/bin/uv
```

It retains all 13 phases, locked inputs, fixed two-worker policy, strict
no-skips/xfail/error discovery, wheel/runtime/development install/import checks,
audit, JDK/ImageJ interoperability and same-run M25 conversion evidence
`<=33554432` bytes. There is no giant reconstruction allocation test or resource
trial. Ubuntu 24.04 is the sole required platform. Conditional CI-authoritative
mode is unavailable; known failures/missing evidence block submission.

Coverage is approved behavior plus independent risk review, all percentages
advisory, no numerical thresholds selected. Required current native statement/
branch JSON/HTML and exact covered/total globally, per package
(`src/simrecon/`, `scripts/`, `devtools/src/simrecon_devtools/`) and per owned file
include never-imported files and relevant subprocesses. Report unsupported
metrics/exclusions/skips/missing evidence; no manual runtime exclusions or
platform unions. A bare uncovered branch is not a test defect. Classify concrete
omissions/product simplification/new meaning/measurement defects and route them
to their named owners.

D forms its own assessment before current-task implementation lessons. Review
W01–W18, B mapping/oracles, genuine signed versus byte-only distinctions,
original-domain positive cases, early declaration ordering, all byte expressions,
actual native/aggregate extents, failure causes, debug/summary retention and target
claim limits beyond green tests. Require frozen-file compliance and exact passing
candidate/input identities. Changed tracked bytes/environment renew affected
verification and fresh D verdict as appropriate.

## Handoff, accounting and presentation

One Current state lives in `docs/tasks/wide-allocation-domain.md`; coordinator
updates it. Final candidate hash/results stay outside verified tracked bytes.
Report exact owned changed files, frozen identities, focused/full commands and
receipt/input/build/report provenance, verdict/findings and limits. Actual human
limits not set; no default quota. Preserve every launch/diagnosis/failed check/
repair/review cumulatively; attribution/tokens/money/elapsed unknown unless
measured. Do not double-count child totals or overlapping time.

Coordinator owns plain-English PR summary, optional useful figure and technical
appendix with exact provenance. Omit a decorative figure: this change is most
clearly explained with the integer-domain table and a concise statement that
representation validity is not memory admission. Eventual stack parent/push/PR/CI
are coordinator work. No merge/release/issue closure is authorized here.

Coordinator owns completion housekeeping using existing commands. C/D report
only own scratch/processes and known retained dependencies. Preserve durable
`docs/reports/issue-115/`, all frozen fixtures and the active worktree; scratch
disposal targets are identified concretely when actually created, not invented
in advance. No helper/test/review is commissioned solely for cleanup.
