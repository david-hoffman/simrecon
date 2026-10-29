# Separate historical notes from blind fixture-reading inputs

**Version 1.0**

- ID: 20261029T061430Z-tsc01-coordinator-blind-fixture-reading-views
- Date: 2026-10-29T06:14:30.445905+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: test-review input boundaries
- Status: confirmed
- Observation: Two study fixture modules contained earlier role/check narratives in docstrings or comments. The first author stopped before tests or edits. A fresh author and reviewer used line-preserving reading copies with those narratives omitted; the remaining non-docstring abstract syntax trees matched the originals. All runtime imports used the byte-identical original modules. Both fresh roles passed the complete 648-test focused closure.
- Evidence: The original [full-study fixture](../tests/full_noisy_study_fixture.py) and [specimen fixture](../tests/image_only_specimen_fit_fixture.py) retain SHA-256 identities `34f3cb5106a2a3feb2e84012fdcd592df6d5026999b759c9d21d19e2b8fa213e` and `a9b14eedd03408975236216b5644f27d8c255b930550a377ed5a5ef1a8c51097`. Local R4-study-A2 ownership, safe-view manifest, original stop report and fresh A2/B source-free check receipts are retained through the sole Current state. The accepted study source checkpoint is `adf964c29c34087dbdc1735997e0365aa8723bcb`; no full-gate or performance result follows from the focused checks.
- Suggested action: Inspect proposed blind inputs for historical narrative before launch. Where a reading view is necessary, bind original and view hashes and verify the remaining code, preserve original line positions, and execute only the original module. Exposure requires role routing; hiding the text afterward does not restore the exposed role's blindness.
