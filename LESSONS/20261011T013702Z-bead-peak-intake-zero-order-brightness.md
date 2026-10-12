# Phase-zero brightness differs from zero-order brightness

**Version 1.0**

- ID: 20261011T013702Z-bead-peak-intake-zero-order-brightness
- Date: 2026-10-11T01:37:02.200247+00:00
- Task: [bead peak localization](../docs/tasks/bead-peak-localization.md)
- Role: intake coordinator
- Topic: scientific model terminology
- Status: confirmed
- Observation: The chosen point-bead model gives sum(c0)=B. A phase-zero exposure also includes first and second phase harmonics, so its summed intensity generally differs from B. A report-only written-model check caught and corrected the ambiguous phrase before implementation; the equations and estimator behavior were unchanged.
- Evidence: [selected model](../docs/models/synthetic-3d-acquisition-v1.md), point-bead and signed-phase equations; clarification commit 0c6620f. Local advice/correction accounting is referenced by the task pointer.
- Suggested action: Name zero-order and phase-zero quantities explicitly when documenting calibration scale; verify a proposed brightness identity against the signed phase equation.
