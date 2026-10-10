# Name the numerical dependency before blind failure tests

**Version 1.0**

- ID: 20261009T031912Z-volume-otf-01-root-public-failure-seam
- Date: 2026-10-09T03:19:12.373844+00:00
- Task: [VOLUME-OTF-01](../docs/tasks/volume-otf-preparation.md)
- Role: coordinator
- Topic: public-contract testability
- Status: confirmed
- Observation: The initial contract specified numerical transform-failure outcomes without naming a production dependency. Blind A correctly left controlled fault injection pending rather than imposing an implementation seam. Intake then named NumPy's public fftn boundary before independent test review; the mathematical DFT and existing error outcomes stayed the same.
- Evidence: [Numerical boundary](../docs/contracts/volume-otf-preparation-v1.md#numerical-range-and-failure-boundaries), contract clarification commit d32ddacb39331e52d12088656352204eaeba94ba, and the task-local initial A report/continuation referenced by the task pointer. The initial report explicitly records the untested U25 gap and no implementation exposure.
- Suggested action: When a contract promises controlled dependency-failure behavior, settle an observable production boundary before blind authoring, or explicitly record the fault-injection limit. This lesson approves no additional backend or policy change.
