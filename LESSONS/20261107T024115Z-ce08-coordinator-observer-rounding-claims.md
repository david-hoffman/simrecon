# Separate observer precision from frozen numerical input

**Version 1.0**

- ID: 20261107T024115Z-ce08-coordinator-observer-rounding-claims
- Date: 2026-11-07T02:41:15Z
- Task: [CE08](../docs/tasks/c-equivalence-independent-acceptance.md)
- Role: coordinator
- Topic: independent numerical observers
- Status: confirmed
- Observation: A legitimate real-trigonometric evaluation of the larger continuous source differed from the frozen binary64 source by at most 3.10862447e-15, rejecting an exact-regeneration assertion despite unchanged mathematics. A separate float32 midpoint check did not establish unique raw rounding. Supplemental bounded binary64 observer comparisons and closed quantization-cell intervals resolved these claims without changing the frozen raw/expected arrays, physical criteria or product numerical bounds. Two larger samples remain unresolved for unique rounding; the revised proof makes no such guarantee.
- Evidence: Durable task evidence `roles/B4-report.md`, `roles/A3-correction-1-report.md`, `roles/A4-correction-1-report.md`, `roles/B5-report.md` under the task evidence pointer. B5 accepted complete checkpoint SHA-256 `1e789c4c939df33d30155a8282c78432ee9fcf06aa9674817468afef5550221c` before the unchanged source-free ordered matched/larger proof passed. [Public observed evidence](../docs/reports/data/ce08-independent-acceptance.json) records the unchanged acquisitions and results.
- Suggested action: Derive observer error separately from product tolerance. Prove a midpoint margin before asserting exact regeneration, or state quantization-cell consistency without claiming unique rounding. Preserve frozen numerical product inputs and charge physical observer uncertainty inside the preregistered budget.
