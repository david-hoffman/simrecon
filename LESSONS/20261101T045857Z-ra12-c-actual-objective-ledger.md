# Track actual residual entries separately from optimizer counts

**Version 1.0**

- ID: 20261101T045857Z-ra12-c-actual-objective-ledger
- Date: 2026-11-01T04:58:57.080942+00:00
- Task: [RA12](../docs/tasks/reference-alignment-ra12.md)
- Role: restricted implementation C; verbatim observation handed off to coordinator
- Topic: nonlinear least-squares accounting
- Status: confirmed
- Observation: "Keep the optimizer's declared evaluation count separate from the actual residual-entry ledger: finite-difference evaluations can contain the best actually evaluated physical candidate even when the declared function-evaluation limit is one."
- Evidence: the [public refinement contract](../docs/contracts/reference-alignment-ra12-v1.md) and [independent accepted tests](../tests/test_image_only_calibration_handoff.py); C1's retained local report records all 84 handoff instances passing with 1,140 existing cases on Python 3.13.12 / SciPy 1.18.1. The focused command and exact hashes are in the local task evidence, not an independent full-gate verdict.
- Suggested action: retain an explicit score ledger and select only actually scored finite candidates when implementing the same declared best-evaluated-point behavior.
