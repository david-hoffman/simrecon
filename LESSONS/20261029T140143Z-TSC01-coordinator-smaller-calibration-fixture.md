# Qualify smaller fixtures through their real workflow

**Version 1.0**

- ID: 20261029T140143Z-TSC01-coordinator-smaller-calibration-fixture
- Date: 2026-10-29T14:01:43.208842Z
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator, recording verified author/reviewer observations
- Topic: fixture size
- Status: confirmed
- Observation: A complete 16-column calibration proposal failed the genuine initializer with unavailable separated positive centroids. A 20-column proposal restored the original 0.72 micrometre bead spacing and passed the workflow keepers with the original random seeds. Nonoverlapping source spheres alone did not establish usable finite-image initialization.
- Evidence: R6 study A cmd-014 and cmd-019; the final cmd-040 closure and fresh B geometry assessment are bound by the accepted checkpoint map. Local checkpoint pointer: `artifacts/test-consolidation/R6-accepted-checkpoints.json`; exact source evidence is indexed locally in `artifacts/test-consolidation/R6-lessons-evidence.json`.
- Suggested action: Qualify a smaller complete fixture against its strongest public workflow keepers. Keep the random seeds and outcome assertions fixed; preserve an unsuitable proposal as a failed fixture attempt rather than product-red evidence. This lesson grants no additional edit, gate or execution authority.
