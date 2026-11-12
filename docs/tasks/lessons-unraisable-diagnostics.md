# LESSONS-UNRAISABLE-01: preserve source-free unraisable diagnostics

**Version 1.0** Git versions revisions.

## Contract

- Origin: owner-authorized LESSONS-DOCTOR-01 triage and prioritized intake; stable finding LESSONS-DOCTOR-01-F001. [Issue draft and completion conditions](../reports/lessons-doctor-2026-11-11/F001-issue.md); [observed reproduction](../reports/lessons-doctor-2026-11-11/cohort-1-probe.json).
- Objective: the existing public source-free launcher omits source snippets/comments/locals for unraisable exceptions, including inherited supported Python children, while retaining exception category/type, message, file/line location and native exit status. Direct warnings and existing exception/pytest diagnostic channels retain their established behavior. No scientific runtime behavior, general output filtering or claim of an engineered security sandbox.
- Baseline: `b05fc782522a81ebd92c10726dac731a26e5a026`, Linux project Python 3.13.12; isolated reproduction also observed on 3.12.14. The captured zero process exit is native unraisable behavior, not a successful no-exposure result. No product source was used in the probes.
- Route: bounded infrastructure correction for settled diagnostic formatting; proposed worker ownership `scripts/source_free_sitecustomize/sitecustomize.py`, `tests/test_source_free_check.py`, and directly affected documentation. Keep launcher/pytest-plugin unchanged unless diagnosed scope explicitly requires them. A fresh independent bounded reviewer assesses oracle, retained diagnostics, inherited channels and exact passing candidate. If the fix needs new execution/security authority, a changed observer contract or unresolved meaning, return to intake/high-risk routing before those changes.
- Expectation sources: root AGENTS, `docs/operations/role-launches.md`, `docs/operations/imagej-reader-environment.md` and the current launcher contract. Existing lesson text is nonblind diagnosis evidence only; no raw report enters blind A/B packets if routing changes.
- Scenarios: synthetic destructor exception omits source-only marker but retains semantic diagnostics; supported inherited child has the same protection; direct ResourceWarning still works; existing exception/warning/pytest channels remain valid; native status and failure categories are preserved. Error-message text intentionally containing arbitrary strings is not blanket-redacted merely because it resembles source.
- Checks: meaningful public-entry regression reproducing the actual omission, existing diagnostic tests, full `make verify` on the exact candidate, fresh independent review. Project coverage policy is inherited unchanged; no fabricated red test or coverage-target change.
- Authority and ownership: this task records intake only. A correction worker has not been launched and implementation is not represented as completed or underway. Coordinator owns this record/publication, and any later commissioning names the worker/reviewer under the existing route. No merge/release authority follows.
- Limits/accounting: no human-set numeric limits; requested future worker/reviewer model `gpt-6.1-sol`, high; unavailable actual attribution/tokens/cost unknown. Diagnosis/review spending remains in the parent doctor task and must not be reset or double-counted.

## Current state

- Status: recorded; intake complete, correction not started. Priority: first actionable finding from the doctor pass.
- Confirmed observation: source-only marker appears in unraisable traceback on project interpreter. Raw evidence and exact helper hashes are in the linked receipt. Cause hypothesis: default `sys.unraisablehook` bypasses the currently installed Python traceback replacements.
- Required next action: commission the named bounded correction and independent review using this contract. Preserve all unrelated channels and return unresolved behavior to intake.
- Issue link: [#99](https://github.com/david-hoffman/simrecon/issues/99), published and read back open with the exact reviewed body. This section remains the sole correction execution state.
