# Repeated integer extraction retains its named error boundary

**Version 1.0**

- ID: 20261018T080433Z-phase-carrier-scan-coordinator-integer-conversion-boundary
- Date: 2026-10-18T08:04:33.830643+00:00
- Task: 01a14db7-46d7-7e80-a3d6-a84240864ec4; [task pointer](../docs/tasks/phase-carrier-scan.md)
- Role: coordinator
- Topic: public conversion errors
- Status: confirmed
- Observation: A valid nonboolean integer subtype with underlying origin zero can permit an earlier conversion and raise on a later conversion. The carrier-scan working draft let TypeError, ValueError and OverflowError escape raw after the earlier success. Immediate expected-error controls and MemoryError/RuntimeError propagation controls passed. This is one named validation-boundary defect family, not evidence of numerical model failure.
- Evidence: Frozen supplemental regression in tests/test_phase_carrier_scan.py at checkpoint 985c8d318dae8bd4457d41094c31a37722d4b91e; local A01/resume04/pytest01.log records 3 failed, 7 passed, 87 deselected. The [public contract](../docs/contracts/phase-carrier-scan-v1.md) defines complete validation and narrow expected-error translation. Existing tests and fixture were preserved byte for byte.
- Suggested action: Keep expected conversion-error translation valid at every extraction that can actually raise. Preserve allocation and unrelated exceptions. Exact integer extraction that bypasses a caller hook, or execution that never reaches its failing invocation, remains a legitimate alternative; do not make conversion counts part of the public contract.
