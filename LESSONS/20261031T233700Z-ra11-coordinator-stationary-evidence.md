# Declared stationary evidence is not a motion detector

**Version 1.0**

- ID: 20261031T233700Z-ra11-coordinator-stationary-evidence
- Date: 2026-10-31T23:37:00.671221+00:00
- Task: RA11, [report](../docs/reports/reference-alignment-ra11-motion-applicability.md)
- Role: coordinator
- Topic: evidence applicability
- Status: confirmed
- Observation: RA10's retained finite control shares one source/operator across phase exposures and applies no motion correction. This supports stationary applicability by construction, rather than detecting stationarity in unknown data. The historical full study uses a prescribed focus stack; describe the same focus-plane grid across exposures, not one fixed focal plane.
- Evidence: [provenance](../docs/reports/evidence/reference-alignment-ra11-stationary.json), unchanged preparation/observation driver and original hash-bound arrays; RA11 reference check at the task pointer.
- Suggested action: Keep illumination phase inference separate from any physical motion claim. Require concrete acquisition mechanism and comparable references before numerical motion work.
