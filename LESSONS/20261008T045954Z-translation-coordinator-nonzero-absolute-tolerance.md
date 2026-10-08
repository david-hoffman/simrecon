# Absolute ambiguity checks need a nonzero minimum example

**Version 1.0**

- ID: 20261008T045954Z-translation-coordinator-nonzero-absolute-tolerance
- Date: 2026-10-08T04:59:54.626862+00:00
- Task: [TRANSLATION-01](../docs/tasks/translation-estimation.md)
- Role: coordinator observing blind B1/B2 evidence
- Topic: numerical test design
- Status: confirmed
- Observation: An absolute-only score-minus-minimum rule can be under-tested when all close-boundary examples have zero minimum. Fresh B1 demonstrated that an added relative allowance passed those success examples. A nonzero-minimum, well-separated fixture distinguishes the wrong candidate set without relying on roundoff boundaries.
- Evidence: B2 accepted test checkpoint 9c5fe7eb5156b1f1ef5c8938a52c8c6babe608f1; tests/test_translation.py test_t06_nonzero_minimum_has_no_relative_allowance; [contract T06](../docs/contracts/translation-estimation-v1.md). Independent rational/Decimal scores have nearest positive-tolerance boundary about 8.29e-8 away, versus 2delta about 5.46e-12. Detailed source-free B1/B2 reports remain in task-local ignored evidence. This was a test gap before product implementation, not a claimed existing product defect.
- Suggested action: When a public policy specifies absolute-only tolerance around a computed minimum, include a nonzero-minimum example with independently justified separation and check the complete candidate set.
