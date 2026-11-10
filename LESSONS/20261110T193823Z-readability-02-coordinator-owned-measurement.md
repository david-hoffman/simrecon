# Relocating tooling requires receipt inventory updates

**Version 1.0**

- ID: 20261110T193823Z-readability-02-coordinator-owned-measurement
- Date: 2026-11-10T19:38:23.182362+00:00
- Task: [Task 02](../docs/tasks/readability-stack.md#task-02-contract-and-evidence-pointer)
- Role: coordinator
- Topic: development packaging and measurement
- Status: confirmed
- Observation: Coverage source configuration and verification receipt package/root
  enumeration are separate inputs. Moving the doctor and pytest policy required
  updating both to retain per-file and per-package development measurements.
  Editable checkout imports alone do not establish product-only installation.
- Evidence: `scripts/verify.py` owned-root enumeration; the Task 02 native
  never-imported/omitted-development-source regressions; installed wheel checks in
  `tests/test_installed_wheels.py`. Exact candidate/full-run evidence is retained
  with the stacked PR and ignored `artifacts/readability-02/` evidence.
- Suggested action: For future package moves, inventory string-based plugin and
  console consumers, owned measurement roots and installed artifacts together.
  Preserve the sole product artifact path and test from temporary caller contexts.
