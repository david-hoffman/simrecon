# Fractional drift needs a new aliasing contract

**Version 1.0**

- ID: 20261008T065133Z-volume-phase-01-coordinator-fractional-alias-boundary
- Date: 2026-10-08T06:51:33.520771+00:00
- Task: VOLUME-PHASE-01; docs/tasks/volume-phase-separation.md
- Role: coordinator
- Topic: finite sampled drift model
- Status: confirmed for the stated counterexample
- Observation: Independent five-pixel finite-sum interpolation at fractional displacement 0.5 pixel agrees with the continuous corrected acquisition for specimen mode 1 and carrier 1, but differs for specimen mode 2 whose product mode 3 wraps to -2. The alias factor is exp(-2*pi*i*0.5)=-1. Integer drift's unconditional finite-grid identity does not extend to fractional motion. This supported choosing known-phase volume separation next; it supplies no fractional feature authority.
- Evidence: Task-local artifacts/roadmap-next-execution/fractional-alias-intake.json, independent NumPy finite-sum observer, Python 3.13.12/NumPy 2.5.3; docs/contracts/integer-drift-correction-v1.md model and current task record. No production output used as truth.
- Suggested action: A future fractional-drift intake must specify interpolation/Nyquist meaning and conditional alias-free physical identity before tests.
