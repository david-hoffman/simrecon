# Keep immutable source bindings for each check

**Version 1.0**

- ID: 20261029T140143Z-TSC01-coordinator-bind-check-inputs-before-start
- Date: 2026-10-29T14:01:43.208842Z
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator, recording verified author/reviewer observations
- Topic: check provenance
- Status: confirmed
- Observation: The first delivery review could not bind earlier check inputs to the committed files from the supplied packet. An earlier inventory had been overwritten. A retained during-run manifest plus a bounded recorded-write inference supported the behavioral result; separate exact-final quality checks resolved the remaining gap. No pre-run digest was invented.
- Evidence: R6 protocols B1 finding B-E1, the original 032 manifest digest, the coordinator-final-quality receipt and fresh B2 acceptance are bound by the accepted checkpoint map. Local checkpoint pointer: `artifacts/test-consolidation/R6-accepted-checkpoints.json`; exact source evidence is indexed locally in `artifacts/test-consolidation/R6-lessons-evidence.json`.
- Suggested action: Capture named material inputs in unique records before and after a check. Keep earlier records across formatting and commit hooks; a final-only hash list does not establish what an earlier command read. This lesson grants no additional edit, gate or execution authority.
