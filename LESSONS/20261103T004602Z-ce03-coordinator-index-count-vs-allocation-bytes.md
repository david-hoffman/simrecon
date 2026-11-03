# Separate source index counts from native allocation bytes

**Version 1.0**

- ID: 20261103T004602Z-ce03-coordinator-index-count-vs-allocation-bytes
- Date: 2026-11-03T00:46:02.497286+00:00
- Task: [CE03](../docs/tasks/c-equivalence-optical-transfer.md)
- Role: coordinator
- Topic: source representation limits
- Status: confirmed
- Observation: The selected source allocates phases and transfer orders separately. Its signed32 element/index products precede size_t byte multiplication. For N=16384,Z=2, the padded per-phase count is 536,936,448 elements, while float32 allocation bytes are 2,147,745,792. The source index products fit despite exceeding a signed32 byte count. A draft universal 2^31-byte/aggregate-element cap was corrected before C; source review also identified empty native output shapes whose nominal nbytes=0 hides an unrepresentable target dtype extent.
- Evidence: [Final source-representation contract](../docs/contracts/c-equivalence-optical-transfer-v1.md); source-review-3-representation and its accepting delta via the [task evidence pointer](../docs/tasks/c-equivalence-optical-transfer.md). Bounded integer/zero-data probes in the own Python3.13.12/NumPy2.5.3 environment; no large payload or retained C execution. Historical effective FFT ABI remains unqualified.
- Suggested action: Audit actual operand types, evaluation order and per-allocation counts. Validate owned Python dtype/shape/native extent separately from source signed-index arithmetic and actual memory availability. No new physical-memory promise, policy change or process budget follows.
