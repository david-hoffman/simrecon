# Near-zero expected residual does not fix an exact policy decision

**Version 1.0**

- ID: 20261008T035131Z-carrier-selection-coordinator-near-zero-residual
- Date: 2026-10-08T03:51:31.985912+00:00
- Task: [CARRIER-SELECT-01](../docs/tasks/carrier-selection.md)
- Role: coordinator
- Topic: numerical oracle and exact threshold policy
- Status: confirmed
- Observation: Fresh blind B1 rejected a test at authored checkpoint 5d697ac4ad1885f90b0a2f9604f3fc2bfc9ddce9 that required no_acceptable_carrier for a model-consistent fit at a tiny positive residual threshold. Its independent stored-input residual was about 4.1744e-16, below the approved 3.1832e-10 accuracy budget. A permitted computed residual can be zero, so the contract's inclusive threshold does not justify a fixed rejection. This was a test overconstraint, not an observed product defect.
- Evidence: [Selection contract](../docs/contracts/carrier-selection-v1.md), S02/S10; test_error_mode_and_warning_preservation at the authored checkpoint; task-local artifacts/carrier-selection-execution/B-final.txt records the independent derivation and verdict. Narrow correction returns to blind A and fresh B, preserving the existing fixture and shared observer.
- Suggested action: For exact scalar gates over approximate numerical outputs, independently verify numerical accuracy, then check eligibility against the same call's actual returned diagnostics. Do not infer a strictly positive computed residual from a mathematical or independently computed value beneath the permitted error budget.
