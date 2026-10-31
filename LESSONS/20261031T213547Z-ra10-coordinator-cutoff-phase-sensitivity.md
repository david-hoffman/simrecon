# Retained-source phase sensitivity has a conditional meaning

**Version 1.0**

- ID: 20261031T213547Z-ra10-coordinator-cutoff-phase-sensitivity
- Date: 2026-10-31T21:35:47.820426+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: numerical identifiability
- Status: confirmed
- Observation: Projecting a phase derivative away from retained source singular vectors can differ from projecting away all nonzero source directions and from differentiating a reprofiled residual. RA10 explicitly names its frozen retained-subspace diagnostic and preserves unrestricted-source identifiability limits.
- Evidence: ../docs/contracts/reference-alignment-ra10-v1.md; ../artifacts/ra10/roles/A1/correction-1/derivation.md. The active-cutoff fixture distinguishes the three definitions before product implementation.
- Suggested action: State which nuisance subspace is held fixed; accompany relative rank with absolute sensitivity and scientific information limits.
