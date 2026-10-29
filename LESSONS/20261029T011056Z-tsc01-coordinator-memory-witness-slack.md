# A smaller payload must still exceed historical memory slack

**Version 1.0**

- ID: 20261029T011056Z-tsc01-coordinator-memory-witness-slack
- Date: 2026-10-29T01:10:56.004108+00:00
- Task: TSC01
- Role: coordinator observing independent blind B review
- Topic: test-fixture sizing and native memory measurements
- Status: confirmed
- Observation: A 64 MiB payload exceeding a 32 MiB increment limit does not establish sensitivity when the observer subtracts historical resident-memory peaks. If H is the earlier peak, R the current resident memory and A the extra resident payload, the measured increment can be max(0, R + A - H). Historical slack H - R can hide the allocation. This is a test-observation gap; no product allocation defect was observed.
- Evidence: R2 numerical candidate bd43d76769dc71a2f02a0e69c34d5f2b5bfdaf17, tests/mrc_fixture_memory.py; fresh B finding B-RN02-01 in the numerical role's retained R2/B-results/review.md. Review launch/hash/accounting is linked from the sole local artifacts/test-consolidation/current-state.json. The original Linux report supplied an earlier peak of 242140 KiB and zero increment, with current resident memory unmeasured.
- Suggested action: Establish witness applicability before accepting a smaller fixture. A conservative payload larger than the measured historical peak plus the unchanged allowance excludes masking by historical slack alone; independently review its actual process ordering and native-unit conversion. This lesson grants no new scope or approval.
