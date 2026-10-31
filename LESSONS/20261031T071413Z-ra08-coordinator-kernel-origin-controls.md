# Kernel replacements need a matching declared origin

**Version 1.0**

- ID: 20261031T071413Z-ra08-coordinator-kernel-origin-controls
- Date: 2026-10-31T07:14:13.813169+00:00
- Task: [RA08 finite-field objective](../docs/tasks/reference-alignment-ra08.md)
- Role: coordinator, from restricted C public finding
- Topic: independent fixture geometry
- Status: confirmed
- Observation: Two reviewed declarations replaced a three-point kernel with a singleton but retained origin `(0,0,1)`. The nine intended precision/range cases therefore reached valid input rejection instead of their intended operation. A paired `(0,0,0)` singleton origin was accepted. The blind author later changed only those two local origins; the nine passing observations are supplemental after implementation, with fresh B3 review pending.
- Evidence: [Sanitized finding](../artifacts/ra08/roles/C1/public-finding.md), SHA256 `fa38d04c2d4dfd70ed400e2ee06f8d39de9c5919d3c3b0c4477d733cf021be55`; [preserved accepted checkpoint](../artifacts/ra08/checkpoints/accepted-v2.json); [corrected input checkpoint](../artifacts/ra08/roles/A1-correction-2/checkpoint.json). C preserved all reviewed bytes and routed the defect instead of weakening validation. No numerical product-red was obtained in the original nine cases.
- Suggested action: When a public control replaces kernel support, independently check its declared origin and a paired valid geometry before interpreting a failure as numerical evidence. This records a fixture-design lesson; it adds no feature, test quota or gate authority.
