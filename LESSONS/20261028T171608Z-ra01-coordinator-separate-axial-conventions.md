# Unequal beams expose an axial convention boundary

**Version 1.0**

- ID: 20261028T171608Z-ra01-coordinator-separate-axial-conventions
- Date: 2026-10-28T17:16:08.121690+00:00
- Task: [RA01](../docs/tasks/RA01.md)
- Role: coordinator
- Topic: scientific comparison intake
- Status: confirmed
- Observation: The periodic synthetic acquisition contract writes focus-minus-source displacement, while the finite optics and inverse contracts write source-minus-focus with a positive central-field exponent. Identical unequal side labels therefore need a derived mapping before physical equivalence is claimed. This static contract distinction establishes no runtime defect.
- Evidence: [Periodic model](../docs/models/synthetic-3d-acquisition-v1.md#illumination-and-axial-scan), [finite optics](../docs/contracts/simulation-optics-v1.md#illumination-and-detection-equations), [RA01 convention dictionary](../docs/reports/reference-alignment-benchmark.md#convention-dictionary), baseline 8f6b35ceda362944f00de44acbf7098989f157e4; read-only capability advisor inspection. No numerical run.
- Suggested action: Use explicit asymmetric axial controls and complete sign/beam/transfer mapping in the authorized comparison steps; do not silently amend either model.
