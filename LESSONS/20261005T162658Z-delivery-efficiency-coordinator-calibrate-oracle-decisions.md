# Calibrate oracle decisions before reducing model capability

**Version 1.0**

- ID: 20261005T162658Z-delivery-efficiency-coordinator-calibrate-oracle-decisions
- Date: 2026-10-05T16:26:58Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: model selection and oracle validity
- Status: confirmed for the recorded synthetic trial; broader model-quality inference is unproved
- Observation: On the same twelve public synthetic decision groups, requested Luna/medium correctly decided nine groups but falsely accepted a normalized-key rejection oracle, supplied an unapproved unit convention, and missed binary representation errors. Requested Sol/high correctly decided all twelve groups. A separate already-classified mechanical reference edit using Luna/medium passed its deterministic diff/link checks. These observations support different task-family qualifications; they do not establish general model rankings, quality equivalence, escaped-defect rates or numerical savings.
- Evidence: [fixed public cases, expected decisions and measured results](../docs/operations/calibration-results.md), including delivered-packet SHA-256, requested configurations and available native usage; [model-selection scope](../docs/operations/model-selection.md). Native CLI 0.160.0, two fresh read-only sessions, no live implementation in calibration. Closed expected decisions were prepared by a fresh designer before calls. Root scored the returned public decisions. Detailed ignored terminal evidence is retained under artifacts/delivery-efficiency/rollout/; no transcripts or private reasoning are committed.
- Suggested action: Select capability by the hardest expected-value or acceptance decision. Qualify the cheaper configuration only for already-classified mechanical work with deterministic checks. Keep scientific/binary/custom-oracle test authors and reviewers on the conservative qualified configuration with independent gates. Recalibrate changed configurations or unrepresented task families within an approved allowance; a model swap does not resolve missing requirements or renew retries.
