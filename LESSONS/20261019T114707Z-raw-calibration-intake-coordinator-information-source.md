# Profile compensation does not supply its carrier label

**Version 1.0**

- ID: 20261019T114707Z-raw-calibration-intake-coordinator-information-source
- Date: 2026-10-19T11:47:07Z
- Task: RAW-CALIBRATION-INTAKE; [task](../docs/tasks/raw-calibration-intake.md)
- Role: nonblind coordinator
- Topic: calibration identifiability
- Status: confirmed conditional algebra
- Observation: For one known finite profile with nonzero candidate shifted spectra and independently free complex side-order responses, changing the integer carrier can be exactly absorbed into a response ratio without changing any raw exposure. This does not prove impossibility under fixed or shared optical structure. A known profile is therefore not, by itself, an independent carrier observation.
- Evidence: [response-ratio derivation and informative alternatives](../docs/reports/raw-calibration-identifiability.md#a-finite-bead-can-fail-to-determine-the-carrier-exactly); known-input [public contract](../docs/contracts/finite-bead-compensation-v1.md#selected-model-and-observable-purpose). Analytical substitution only; no generated-data experiment or physical accuracy measurement.
- Suggested action: Before numerical self-calibration, name the independently measured labels or concrete informative shared optical/probe constraints. Keep hidden evaluator carrier out of initialization and profile compensation settings.
