# Measure the value of test-reference caches

**Version 1.0**

- ID: 20261109T045205Z-test-efficiency-coordinator-measure-cache-value
- Date: 2026-11-09T04:52:05.884383+00:00
- Task: [Test efficiency audit](../docs/tasks/test-efficiency-audit.md)
- Role: coordinator
- Topic: test maintenance and performance
- Status: confirmed
- Observation: A phase-oracle cache passed independent correctness review after consumer-composition and mutable-array-header repairs. One focused comparison measured the original 192 cases at 3.03 s and the revised 226 cases at about 1.08 s. The coordinator retired this optimization because that small local saving did not justify its added serialization machinery. This records the final disposition of the attempt described in [the carrier-consumer lesson](20261109T044016Z-test-efficiency-coordinator-carrier-consumer-composition.md); that lesson's composition finding remains valid.
- Evidence: The task evidence pointer retains the original source-free cost log, B3 review, exact original-source restoration and all earlier attempts. Python 3.13.12 on macOS arm64; other work ran concurrently. This is one local focused comparison, not a controlled benchmark or whole-suite speed claim.
- Suggested action: Profile before adding reference-cache abstractions. Prefer consolidating expensive repeated acquisitions; retain a simpler original test when the observed saving is too small to justify the new maintenance burden. This creates no numerical quota or universal timing threshold.
