# Pair mixed-member integrity controls with a valid wheel

**Version 1.0**

- ID: 20261012T163533Z-wheel-hash-root-mixed-control-validity
- Date: 2026-10-12T16:35:33.934188+00:00
- Task: [Empirical transfer consumption](../docs/tasks/empirical-transfer-consumption.md)
- Role: coordinator
- Topic: independent fixture validity
- Status: confirmed
- Observation: Two isolated corrupt-member examples in a mixed secure wheel passed on a verifier that still rejected the valid mixed wheel. Passing invalid-input controls alone therefore did not establish correct per-member integrity checking. Fresh review independently checked the exact valid and invalid archives and retained the valid counterpart as mandatory evidence.
- Evidence: Tests-only checkpoint `ce7a3881a95034b0742047211a5dd7f4027d0290`, [public owning suite](../tests/test_verification_wheel_hashes.py), [receipt contract](../docs/contracts/verification-receipt-v1.md), and ignored task evidence `B10-R02-whole-checkpoint-closure.json` in the wheel-hash worktree. The real command-line interface produced 129 passed and seven intended product failures across 136 affected examples on Python 3.13.12/macOS 27.0. The mixed last-member digest and size controls differ from the first member's algorithm; independently verified positives distinguish family refusal from actual member validation.
- Suggested action: Keep valid homogeneous and mixed counterparts alongside isolated corruption controls. Reassess fixture truth independently when repairing compatibility; a negative that passes by rejecting all inputs supplies limited proof.
