# Source-free diagnostic and probe channels: resolved

**Version 1.0**

- Record kind: disposition
- ID: 20261111T182059Z-lessons-doctor-01-coordinator-b05-resolved
- Date: 2026-11-11T18:20:59.467994+00:00
- Task / deciding role: [LESSONS-DOCTOR-01](../../tasks/lessons-doctor-first-pass.md), coordinator after independent policy acceptance.
- Lesson IDs: the exact IDs in the per-lesson decisions below; each appears once in this record.
- Finding IDs / scope: per-lesson mapping below. Grouping is a semantic view, not proof of a common defect or blanket resolution.
- State: resolved
- Completion conditions: per-lesson conditions below; tracked does not mean resolved.
- Basis / evidence: baseline b05fc782522a81ebd92c10726dac731a26e5a026; current repository inspection and the explicitly named retained checks/isolated probes. No full product verification was run for this report. Missing historical/private artifacts and platform limits remain explicit.
- Work links: per-lesson links below, or none because no current correction is commissioned for that scope.
- Relationships: no earlier disposition exists at this cutoff; these records supersede none. Related observations and narrow observation corrections remain intact. No automatic duplicate resolution is inferred.
- Revisit: per-lesson triggers/owner below. New conflicting evidence requires a new explicitly scoped disposition.

## 20261010T004950Z-imagej-setup-root-exception-command-text

- Lesson: [original observation](../20261010T004950Z-imagej-setup-root-exception-command-text.md)
- Finding IDs / scope: none; no actionable finding established; Standard nested subprocess.TimeoutExpired and subprocess.CalledProcessError messages through the existing standard traceback renderers
- Basis / evidence: Checked the present targeted renderer/oracle and its direct positive/negative cases. SHA256 values of all three current harness files and tests/test_source_free_check.py exactly match the before manifest in the retained 2026-11-09 edcf53b5d5c0f494c388944d3cfda5c04b9fda97 receipt; its tests phase returned 0 and the linked same-run log records 3087 passed. This resolves the specific standard channel/path incident, not custom messages, all pytest channels, arbitrary source printing or future changed helper bytes. The resolved scope expressly excludes unraisable/__del__ rendering and implies no verdict for sys.unraisablehook.
- Evidence pointers: `docs/lessons/20261010T004950Z-imagej-setup-root-exception-command-text.md`; `tests/test_source_free_check.py:245`; `scripts/source_free_check.py`; `scripts/source_free_sitecustomize/sitecustomize.py`; `scripts/source_free_sitecustomize/pytest_plugin.py`; `artifacts/verification/receipt.json`; `artifacts/verification/logs/tests.log:121`
- Completion conditions: Current exact-byte harness/tests demonstrate argument/source suppression while preserving executable and duration/status for the standard direct, traceback, chain, group, thread and pytest examples.
- Work links: none; scoped knowledge/decision only, evidence retained below
- Revisit: Revisit if these material harness/test inputs change or a new source-bearing diagnostic channel is observed. Owner: Coordinator of the next applicable authorized task.

## 20261010T192003Z-stack-maintenance-coordinator-pytest-source-identity

- Lesson: [original observation](../20261010T192003Z-stack-maintenance-coordinator-pytest-source-identity.md)
- Finding IDs / scope: none; no actionable finding established; Pytest test failure file identity resolved against its actual invocation directory
- Basis / evidence: Checked the present targeted renderer/oracle and its direct positive/negative cases. SHA256 values of all three current harness files and tests/test_source_free_check.py exactly match the before manifest in the retained 2026-11-09 edcf53b5d5c0f494c388944d3cfda5c04b9fda97 receipt; its tests phase returned 0 and the linked same-run log records 3087 passed. This resolves the specific standard channel/path incident, not custom messages, all pytest channels, arbitrary source printing or future changed helper bytes. The resolved scope expressly excludes unraisable/__del__ rendering and implies no verdict for sys.unraisablehook.
- Evidence pointers: `docs/lessons/20261010T192003Z-stack-maintenance-coordinator-pytest-source-identity.md`; `tests/test_source_free_check.py:180`; `scripts/source_free_check.py`; `scripts/source_free_sitecustomize/sitecustomize.py`; `scripts/source_free_sitecustomize/pytest_plugin.py`; `artifacts/verification/receipt.json`; `artifacts/verification/logs/tests.log:121`
- Completion conditions: Current exact-byte path observer/tests accept correct relative/absolute full paths from both invocation layouts and reject a different directory with the same basename.
- Work links: none; scoped knowledge/decision only, evidence retained below
- Revisit: Revisit if these material harness/test inputs change or a new source-bearing diagnostic channel is observed. Owner: Coordinator of the next applicable authorized task.

## 20261010T232710Z-raw-acquisition-declarations-coordinator-pytest-collection-diagnostics

- Lesson: [original observation](../20261010T232710Z-raw-acquisition-declarations-coordinator-pytest-collection-diagnostics.md)
- Finding IDs / scope: none; no actionable finding established; Pytest module/conftest import and syntax collection diagnostics handled by the current installed plugin
- Basis / evidence: Checked the present targeted renderer/oracle and its direct positive/negative cases. SHA256 values of all three current harness files and tests/test_source_free_check.py exactly match the before manifest in the retained 2026-11-09 edcf53b5d5c0f494c388944d3cfda5c04b9fda97 receipt; its tests phase returned 0 and the linked same-run log records 3087 passed. This resolves the specific standard channel/path incident, not custom messages, all pytest channels, arbitrary source printing or future changed helper bytes. The resolved scope expressly excludes unraisable/__del__ rendering and implies no verdict for sys.unraisablehook.
- Evidence pointers: `docs/lessons/20261010T232710Z-raw-acquisition-declarations-coordinator-pytest-collection-diagnostics.md`; `tests/test_source_free_check.py:454`; `scripts/source_free_check.py`; `scripts/source_free_sitecustomize/sitecustomize.py`; `scripts/source_free_sitecustomize/pytest_plugin.py`; `artifacts/verification/receipt.json`; `artifacts/verification/logs/tests.log:121`
- Completion conditions: Current exact-byte plugin/tests exercise module, initial/nested conftest, import/syntax, runtime chain, setup import, import mismatch and caller CollectError cases while preserving diagnostics/status and suppressing ordinary source snippets.
- Work links: none; scoped knowledge/decision only, evidence retained below
- Revisit: Revisit if these material harness/test inputs change or a new source-bearing diagnostic channel is observed. Owner: Coordinator of the next applicable authorized task.
