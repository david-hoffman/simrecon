# Restore public module identities after fixture reloads

**Version 1.0**

- ID: 20261029T040816Z-tsc01-coordinator-public-module-fixture-isolation
- Date: 2026-10-29T04:08:16.065103+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator, recording independently reviewed A/B evidence
- Topic: test fixture isolation
- Status: confirmed
- Observation: Reload-based public optimizer injection replaced exported class identities that another suite had imported at collection. The pre-repair proposal's combined suites had 281 passes and 22 exact-type failures; a frozen-baseline four-case order reproducer had three passes and one failure. Restoring the original module namespace in fixture teardown preserved patch-before-reload injection and all exact-type assertions. Both four-case orders and the required complete pilot-then-bead shared-process closure then passed in fresh A and B checks. This was a fixture isolation defect, not product-red evidence.
- Evidence: R3-C candidate e8f87b5a0554b1c8c92449528fe01af99d272e6a; A2 and B each observed 303 complete-suite passes. The ignored artifacts/test-consolidation/R3-accepted-checkpoints.json binds original role evidence and B review SHA-256 868fa7a526999510e2f2e67919e73a7648e206e582386431ed1bb7289cf15fef. The closure is 'pytest -q tests/test_image_only_calibration_pilot.py tests/test_image_only_bead_calibration.py' through the source-free wrapper, using the qualified Python 3.13.12 environment. Supplemental observer failures and their corrected confirmation remain separate in B's accounting.
- Suggested action: Give reload-based dependency injection a fixture-owned lifetime and restore exported identities in finally. Check both a small order reproducer and the complete affected suites in their required shared-process order. Preserve legitimate direct and module-qualified dependency imports and the original exact-type assertions; do not substitute reordered or separate runs for isolation proof. This lesson grants no new scope or gate exception.
