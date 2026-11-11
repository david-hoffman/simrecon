# LESSONS-UNRAISABLE-01: preserve unraisable diagnostics without source lines

**Version 1.0.** Git versions revisions. This record is not technical enforcement.

## Contract

- Human instruction: `/intake 99`, received November 11, 2026. Prepare the concrete
  correction contract and execution packets for
  [issue #99](https://github.com/david-hoffman/simrecon/issues/99), finding
  `LESSONS-DOCTOR-01-F001`. This intake writes documentation, not executable tests
  or runtime code. It requires no second approval of this record. The saved worker
  and reviewer packets are dormant future-entry instructions; this request does
  not launch or perform the correction.
- Baseline: `b05fc782522a81ebd92c10726dac731a26e5a026`, initially clean tracked
  checkout. One coherent correction; no scientific or architectural dependency.
- Purpose: restore the existing source-free diagnostic promise of
  [role launches](../operations/role-launches.md) for Python unraisable exceptions
  through `scripts/source_free_check.py` and its inherited Python environment.
- Non-goals: scientific changes, general content redaction, engineered access
  controls, new execution permissions, arbitrary application output filtering,
  replacement of caller-installed hooks, dependency changes, policy changes,
  global diagnostic certification, or disposition of other doctor findings.

### Observed, expected and unverified

Issue #99 reports a public-launcher reproduction at the baseline on Linux with
Python 3.13.12 and separately 3.12.14: a synthetic exception in `__del__` prints
the original `raise` line and its source-only comment. The type, message and
location survive, and the interpreter exits 0. That successful process status
does not establish that source was suppressed. This intake did not rerun the
probe and makes no claim of actual product-source exposure in a blind session.

Read-only inspection confirms that the current diagnostic installation handles
ordinary exceptions, warnings, threads and traceback formatting but does not
replace `sys.unraisablehook`. That is a leading cause, not a mandated patch or
proof that it is the only relevant path. Pytest can intercept unraisable events;
the public behavior, rather than the identity of an installed hook, is the oracle.

The issue cites this task filename and
`docs/reports/lessons-doctor-2026-11-11/cohort-1-probe.json`. Neither file existed
in the local baseline; authenticated GitHub default-branch contents reads also
returned 404 on November 11, 2026. This document is newly created, not a recovered
historical intake. The original probe artifact, its exact helper hashes and prior
doctor accounting remain unavailable. The issue's reported observations retain
their stated limits; this intake does not substitute fresh passing evidence.

### Requirements

- **R1 — source omission:** a reportable unraisable exception arising in a
  synthetic Python program through the public launcher produces useful
  diagnostics without automatically retrieved source snippets, comments or
  local-variable dumps. Cover explicit finalization and normal interpreter
  shutdown on the supported project interpreter.
- **R2 — retained meaning:** retain the exception type/category, authored message
  and available traceback filename/line. Formatting, indentation and the exact
  diagnostic header are not fixed. An arbitrary object's representation is not
  a required identity field and may be omitted. Preserve authored exception and
  warning messages; this is not a promise to redact arbitrary message contents.
- **R3 — status and inheritance:** retain native process outcomes, including 0
  for an otherwise successful process with an unraisable event and an explicitly
  chosen nonzero exit status. An ordinary Python subprocess inheriting the
  launcher's environment receives the same source omission and useful
  diagnostics. Do not fabricate failure or hide an actual child failure.
- **R4 — warning compatibility:** retain the paired working ResourceWarning
  case, including category, message and location under explicit warning filters.
  Preserve normal filters and warning promotion. A warning raised as an exception
  during finalization follows native unraisable/status behavior.
- **R5 — pytest compatibility:** qualify unraisable events under the launcher's
  pytest mode and Python mode invoking pytest. Preserve the locked pytest
  warning/error policy, test identity, counts and exit status under explicit
  warning settings; do not swallow a warning or force every event to fail.
- **R6 — preservation and disposition:** existing source-free warning, exception,
  syntax, chain/group, thread, standard traceback, subprocess, startup/collection,
  timeout and interpreter-option behavior remains intact. Record exact scoped
  evidence and limits; resolving #99 resolves no other diagnostic claim.

### Boundary and scenario inventory

Expected results come from the issue's correction request, the existing
source-free launch contract, and the supported interpreter/locked pytest's
native diagnostic and status semantics. Synthetic source-only and local-only
markers must be distinct from deliberately retained messages. Tests must observe
the public launcher and real child processes; a directly invoked hook alone is
insufficient.

| ID | Distinct decision and observable outcome | Equivalent coverage examples / expectation source | Evidence owner |
|---|---|---|---|
| S1 | Explicit finalization reports type, message and traceback location without source/comment/local rendering | Synthetic `__del__` exception with unique message and source-only/local-only markers; R1/R2 | Worker; fresh reviewer audits observer |
| S2 | Normal interpreter shutdown retains the same diagnostic fields and source omission | A synthetic finalizer whose event is actually reported by native Python; no guarantee to finalize every object; R1/R2 | Worker; reviewer checks deterministic fixture |
| S3 | Ordinary inherited Python child receives source-free diagnostics and retains its native status | Real `subprocess` child, actual inherited environment, parent observes/propagates status; R3 | Worker; reviewer audits inheritance |
| S4 | Unraisable reporting does not invent or erase process failure | Native successful exit 0 and explicit nonzero exit, such as 7; ordinary uncaught failure remains a failure; R3 | Worker; reviewer checks positive and failure cases |
| S5 | Working ResourceWarning stays useful and source-free under its selected warning filter | Explicitly emitted warning and relevant resource-finalization warning with explicit filters; R4 | Worker; reviewer checks original positive case |
| S6 | Warning promotion during finalization preserves its exception meaning and native status | ResourceWarning promoted to an error during finalization; R2/R4 | Worker; reviewer audits filter/status oracle |
| S7 | Pytest interception remains source-free without changing selected warning/error outcomes | Public pytest mode and Python mode invoking locked pytest; warning and warning-as-error settings; R5 | Worker; reviewer checks real pytest path |
| S8 | Existing diagnostic and launch decisions remain unchanged | Existing source-free regression suite, including accepted option rejections and permitted literal arguments; R6 | Worker; reviewer audits preservation |

Invalid inputs inherit existing launcher rules; this task adds no rejection rule.
Representation limits: only available traceback locations can be retained;
arbitrary object/message text is not a universal secrecy boundary. Operation-time
failures retain existing timeout, launch-error and child-error behavior. Supported
qualification is project Python 3.13.12 with locked dependencies; the reported
3.12.14 observation is historical reproduction evidence, not a new support target.
CI still requires Ubuntu 24.04 and macOS 15. The worker maps concrete examples to
requirements/scenarios; example and test counts are not scenario limits.

### Route, ownership and checks

- **Route: bounded infrastructure correction.** The requested presentation/status
  behavior is settled, with no new permissions, security guarantee, scientific
  meaning, binary representation or data-loss behavior. Prompted role blindness
  is not an engineered access control. Do not lower a newly discovered uncertain
  or expanded boundary to fit this route; route material new meaning to intake.
- Bounded worker owns `scripts/source_free_sitecustomize/sitecustomize.py`,
  `tests/test_source_free_check.py` and its synthetic temporary fixtures.
  `scripts/source_free_sitecustomize/pytest_plugin.py` and
  `scripts/source_free_check.py` are permitted only for a diagnosed necessary
  repair of R1–R6; explain any such change. The worker owns the correction report
  at `docs/reports/lessons-unraisable-diagnostics.md` and updates this sole Current
  state. No other runtime, tests, dependencies, workflows, coverage, discovery,
  skills, policy or scientific files are authorized.
- Fresh bounded reviewer independently assesses meaningful tests, observer/oracle
  validity, omitted outcomes, permitted positive cases, exact passing correction
  and preserved gates. The reviewer reports only and never repairs its target.
  No blind A/B or restricted C role is commissioned for this bounded route.
- Planned worker/reviewer configuration: `gpt-6.1-sol`, high, per
  [model selection](../operations/model-selection.md). This is the conservative
  provisional choice, not a quality guarantee. Record actual served settings and
  unavailable metering as unknown. Diagnose concrete reasoning limitations before
  escalation; missing semantics return to intake, tooling failures to setup.
- Coverage inherits [PROJECT](../PROJECT.md#coverage-policy-and-adoption-provenance):
  approved behavior coverage with independent risk review; no percentage target
  selected. Native statement/branch measurement, exact integer counts, global/
  package/never-imported/subprocess scope, current JSON/HTML and report integrity
  remain mandatory. Other instrumented metrics are unsupported, not invented.
- Before dependent execution, check supported Python/uv, per-worktree locked
  environment, imports and `make preflight`. Then run focused lint/format/types
  and `uv run --locked python -m pytest tests/test_source_free_check.py`.
  Reproduce the approved defect before repair where available; retain initially
  passing cases and classify failures. Neither exit 0 nor marker absence alone
  proves useful source-free diagnostics.
- Submission gate: clean, unchanged exact candidate passing `make verify`, all
  13 phases, native reports, both wheel checks, audit and same-run M25 evidence
  with the unchanged 33,554,432-byte limit. Record actual uv/Java paths and
  environment. CI repeats full configured platforms. Conditional CI-authoritative
  mode is not enabled. Known failures or missing required evidence block even a
  draft PR. No full verification or PR submission is part of this intake.
- Completion of the correction requires fresh independent acceptance of the exact
  passing candidate plus the scoped report. A later correction role entry uses
  the [worker](../packets/lessons-unraisable-worker.md) and
  [reviewer](../packets/lessons-unraisable-reviewer.md) packets; their existence is
  not execution or acceptance evidence. No merge, release, issue closure or
  external-message authority is supplied by `/intake 99`.
- Actual human-set scenario/review/repair/time/spending limits: **not set**.
  Preserve historical attempts; unavailable prior counts/costs remain unknown.

## Current state

- **Status:** intake complete; bounded correction not started; no runtime or test
  change, product-red checkpoint, passing correction or acceptance claimed.
- Human instruction and constraints: `/intake 99`; no unresolved material contract
  question. Baseline is the commit above. Final intake commit/tree and check results
  belong in the conversation, outside the tracked candidate bytes.
- Workspace: existing `/workspace/simrecon`, branch
  `intake/99-unraisable-diagnostics`; baseline runtime/tests preserved.
- Evidence: issue body and empty comments read November 11, 2026; cited task/probe
  absent locally and default-branch reads returned 404. Existing code/tests were
  inspected nonblind. The missing historical probe/accounting is an evidence
  limitation, not a new owner decision or a reason to claim fresh reproduction.
- Roles: one coordinator intake author and one read-only discovery helper,
  `intake_diagnostic_inventory`; helper inspected the diagnostic owner boundary and
  supplied scenario/routing advice, then a continued report-only packet sanity
  check. It performed no tests, edits, launches or acceptance review. Its optional
  `gh` issue reread returned Forbidden; the coordinator's connector issue read
  succeeded. Neither session is eligible to be the fresh correction
  reviewer. No native correction worker or required reviewer launched in intake.
- Capability observations: existing baseline interpreter reports Python 3.13.12;
  current default PATH uv reports 0.13.5, while PROJECT pins 0.12.19. Direct checks
  confirm shared `/workspace/.simrecon-tools/uv-env/bin/uv` is 0.12.19 and
  `/workspace/.simrecon-tools/jdk-21.0.7+6/bin/java` is Temurin 21.0.7+6. The
  existing activation file selects these tools and shared caches. Execution must
  select them and refresh locked preflight; old setup logs do not prove current
  candidate readiness. No dependency installation or full test run attempted in
  intake.
- Risk disposition: S1–S8 require public-entry behavior evidence; misleading
  observer parsing, suppressed diagnostics, pytest interception, child inheritance,
  shutdown timing, warning filters and changed status are the concrete risks.
  No percentage-only finding commissions additional tests.
- Accounting: scenarios=8; concrete example/test count pending worker mapping.
  Intake helper launches=1, continued discovery turns=1; correction-worker
  launches=0 and required review verdicts=0 in this intake only. Prior doctor
  attempts and metering unknown.
  Coordinator actual model/effort unknown; helper requested `gpt-6.1-sol`/high,
  actual served attribution unknown. Per-role responses/tokens/cached tokens,
  verified monetary cost and complete elapsed/check/owner-wait totals unknown.
  No historical counters are reset. Actual human-set limits: not set.
- Next action when correction work is requested: use the bounded worker packet,
  qualify tools/environment, map and reproduce the approved behavior, then
  repair within ownership and obtain fresh exact-candidate review. The defective
  launcher remains unqualified for unraisable events until correction acceptance;
  do not claim blind-role readiness from this intake.
- Housekeeping: no task probe, fixture or process was created. The temporary
  `/workspace/work/intake-99` worktree was used to draft documents before the
  shared setup note selecting the existing cloud checkout was read. The documents
  were transferred to the existing checkout and the clean temporary worktree
  removed with `git worktree remove`. Keep the current checkout, intake branch,
  durable documents and shared tool caches. Removed paths:
  `/workspace/work/intake-99`; cleanup errors: none.
  At correction completion close owned writers and use existing filesystem/Git
  commands on exact disposable temporary-fixture paths and unused task worktrees,
  preserving needed commits, evidence and uncertain targets under
  [the cleanup workflow](../operations/fixture-cleanup.md).

## PR presentation

Coordinator summary: destructor exceptions can reveal source lines even when a
process exits successfully. The correction retains the useful diagnostic and
native status while omitting automatically rendered source. No figure is useful
for this textual behavior change. A later PR uses the established template with
plain-English behavior first and a collapsible technical appendix for exact
identities, baseline/final checks, independent review, coverage, measurements,
platform limits and the scoped disposition. No PR is opened by this intake.
