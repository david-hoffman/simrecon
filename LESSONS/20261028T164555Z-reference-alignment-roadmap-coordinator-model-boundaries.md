# Distinguish a study driver from the library's reconstruction model

**Version 1.0**

- ID: 20261028T164555Z-reference-alignment-roadmap-coordinator-model-boundaries
- Date: 2026-10-28T16:45:55.049817+00:00
- Task: [Reference alignment roadmap](../docs/tasks/reference-alignment-roadmap.md)
- Role: coordinator
- Topic: scientific comparison
- Status: confirmed
- Observation: The library already separates and fuses five complex volume orders on a finite periodic integer-carrier model. The full noisy study uses an exterior-zero, pixel-integrated direct operator and a nonnegative source solve. Adding explicit separation is not by itself a missing-physics repair, and passing one model's tests cannot establish equivalence to the other.
- Evidence: [Stage/convention map and normal-equation conditions](../docs/plans/reference-alignment-roadmap.md), source baseline `3b4fe0239823febe9a878d3e838b416319f104bd`; read-only source inspection, no numerical execution or C parity claim.
- Suggested action: Match forward representation, observation metric, constraints and regularization before comparing direct and spectral solutions; retain different-model controls as labeled comparisons.
