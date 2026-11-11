# Standard real kinds need explicit dtype checks before range comparison

**Version 1.0**

- ID: 20261103T185730Z-ce05-coordinator-standard-real-kinds
- Date: 2026-11-03T18:57:30.071421+00:00
- Task: [CE05 carrier/modulation](../tasks/c-equivalence-carrier-modulation.md)
- Role: coordinator, confirming restricted C's evidence-linked handoff
- Topic: NumPy numeric input validation
- Status: confirmed on the recorded environment
- Observation: On macOS arm64 with NumPy 2.5.3, comparing a valid float16 array containing 0.5 directly against a Python float32-maximum bound raises FloatingPointError when overflow errors are enabled, because scalar promotion casts the bound into float16. Widening the validated array to binary64 before the comparison avoids that overflow. On this environment, longdouble and float64 both have an 8-byte itemsize and display as float64, but have distinct dtype characters g and d. Kind/itemsize checks alone therefore admit a kind excluded by the approved standard-real-array domain.
- Evidence: The task-local `C1/focused-1.log` has two float16-positive failures and two extended-kind-negative failures; `C1/focused-2.log` and `C1/focused-4.log` pass after the implementation correction. The coordinator independently reproduced both properties in `numpy-kind-verification.json`, with overflow errors enabled. The task pointer locates retained evidence. These are observations of this environment, not a claim about all NumPy versions or platforms.
- Suggested action: For the same declared standard-real domain, check its exact allowed dtypes before widening to binary64 for magnitude comparisons. Verify dtype identity separately from representation size on each required platform. This observation grants no new interface or edit authority.
