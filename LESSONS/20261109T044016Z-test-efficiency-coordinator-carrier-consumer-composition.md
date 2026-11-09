# Keep representation checks at every consuming boundary

**Version 1.0**

- ID: 20261109T044016Z-test-efficiency-coordinator-carrier-consumer-composition
- Date: 2026-11-09T04:40:16.879110+00:00
- Task: [Test efficiency audit](../docs/tasks/test-efficiency-audit.md)
- Role: coordinator
- Topic: test consolidation
- Status: confirmed
- Observation: Splitting 192 carrier-representation cases into extraction checks and 34 reduced numerical cases lost proof that both numerical consumers accepted the original representations. Correct integer reduction alone did not establish correct composition through either consumer. The correction retains every original consumer call while sharing the 34 immutable independent expected results.
- Evidence: Baseline `8f6b35ceda362944f00de44acbf7098989f157e4`, [current finite-matrix tests](../tests/test_volume_phase_estimation.py), and the public-test-only review/correction records referenced by the task's sole evidence pointer. The corrected focused selection passed 226 cases under Python 3.13.12. A supplemental test-helper probe independently exposed a mixed-integer rounding error at each consumer: converting `2**64 - 1` through binary64 changes its residue modulo 4 from 3 to 0. No product mutation or product-red claim follows.
- Suggested action: Share pure expected calculations across equivalent represented problems. Preserve each declared input class at every consumer whose conversion behavior the original test observes; direct helper checks do not substitute for that composition.
