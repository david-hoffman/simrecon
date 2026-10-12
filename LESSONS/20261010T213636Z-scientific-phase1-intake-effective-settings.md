# Reference help and calibration output do not establish effective settings

**Version 1.0**

- ID: 20261010T213636Z-scientific-phase1-intake-effective-settings
- Date: 2026-10-10T21:36:36Z
- Task: [SCIENTIFIC-PHASE1-20261010](../docs/tasks/scientific-phase1-intake.md)
- Role: intake coordinator, with fresh source advice
- Topic: target provenance
- Status: confirmed
- Observation: inspected reconstruction help advertises five phases and background 515, while assignments select three phases and zero background. Empirical calibration emits radial OTFs by default, but reconstruction defaults to nonradial interpretation. These textual facts do not identify the settings used for an owner's reference output.
- Evidence: [acquisition matrix](../docs/plans/scientific-phase1-acquisition.md#provenance-traps-and-sampling-check), hashed `helpers.c:73,103,511,545,558` and `mainfile.c:1009–1035`; read-only source inspection on October 10, 2026. No reference program was executed.
- Suggested action: obtain effective command/configuration/build provenance before selecting a compatibility mode; retain source help/default discrepancies as provenance questions, not instrument facts or automatically adopted Python defaults.
