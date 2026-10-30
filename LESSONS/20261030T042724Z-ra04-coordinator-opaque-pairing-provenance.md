# Opaque labels do not authenticate paired camera calibration

**Version 1.0**

- ID: 20261030T042724Z-ra04-coordinator-opaque-pairing-provenance
- Date: 2026-10-30T04:27:24.394844+00:00
- Task: RA04, docs/tasks/reference-alignment-ra04.md
- Role: coordinator, observing preimplementation contract/test review
- Topic: unit/provenance contract
- Status: confirmed within the cited public contracts and controls
- Observation: The first RA04 draft overinterpreted raw-unit/calibration-ID equality. Public algebra and fresh B2 review support separate declared responses converting different raw units into one common output unit; calibration IDs remain opaque provenance. Equal estimated-mode count labels express the caller applicability assertion and establish no physical calibration.
- Evidence: docs/contracts/reference-alignment-ra04-v1.md R12/R22/R23; docs/reports/evidence/ra04/B2-review.md. Original revision1 and mathematical advice are retained locally in artifacts/ra04/intake and artifacts/ra04/advisor.
- Suggested action: Use the explicit response-unit relation and the approved metadata meaning when composing corrections. Preserve opaque IDs and label assertions without inventing compatibility checks. This observation grants no new edit authority.
