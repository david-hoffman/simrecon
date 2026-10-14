# Keep diagnostic test selectors out of inherited pytest options

**Version 1.0**

- ID: 20261014T074058Z-baseline-compatibility-coordinator-pytest-selector-inheritance
- Date: 2026-10-14T07:40:58.293340+00:00
- Task: [BASELINE-COMPATIBILITY-01](../docs/tasks/shared-node-baseline-compatibility.md)
- Role: coordinator, observing restricted C diagnostics
- Topic: subprocess test selection
- Status: confirmed
- Observation: A diagnostic subset selected through PYTEST_ADDOPTS supplied those same file selectors to nested pytest commands. The owned run timed out at 600 s and its partial native coverage remained incomplete. A new collection using explicit pytest arguments passed 4091 selected cases in 82.43 s. This subset was not the canonical full gate.
- Evidence: Incomplete candidate14b28670cf8a9fe591715240a6d7dccb9d22db2c; ignored artifacts/baseline-compatibility-20261013/C01/assessment.private.md and incomplete-native-01/inventory.json preserve the failed and fresh collection evidence. The sole roadmap accounting ledger preserves the timeout and correction charge. Environment: Python3.13.12; subprocess measurement enabled.
- Suggested action: Pass diagnostic selectors as explicit pytest arguments. Preserve the incomplete data separately, use bounded cleanup of the recorded owned process group, and create a fresh collection after diagnosing inherited selector pollution. A subset pass supplies no full-gate or100% claim.
