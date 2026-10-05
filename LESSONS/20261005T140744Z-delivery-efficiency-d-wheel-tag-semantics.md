# Complete coverage does not establish wheel tag validity

**Version 1.0**

- ID: 20261005T140744Z-delivery-efficiency-d-wheel-tag-semantics
- Date: 2026-10-05T14:07:44Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: D; handoff recorded by documentation maintenance
- Topic: artifact validation
- Status: confirmed
- Observation: The D-reviewed receipt reported complete statement and branch coverage, but D's actual `artifact()` in-memory probe accepted `Tag: definitely-not-a-compatibility-tag` with otherwise valid metadata and recomputed secure RECORD hashes. Nonempty metadata fields and coverage did not establish tag syntax. Agreement with the wheel filename remains a separate validation obligation, inferred from the specifications rather than a separate measured mismatch in this probe.
- Evidence: The [independent D report](../artifacts/delivery-efficiency/roles/d-report.md), finding 2 and coverage table, reviews rejected checkpoint `0823da8315dd48cc9f4a85fc32c70875fc72739e`. D ran `.venv/bin/python -B -c` against the actual `artifact()` function using an in-memory archive substitute on local macOS. The opened [PyPA wheel specification](https://packaging.python.org/en/latest/specifications/binary-distribution-format/#file-name-convention) defines the filename fields and [expanded WHEEL tags](https://packaging.python.org/en/latest/specifications/binary-distribution-format/#file-contents); the opened [compatibility-tag specification](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#overview) defines the three-part tag format.
- Suggested action: Validate compatibility-tag syntax and agreement between expanded metadata tags and filename tags. Route equivalent malformed and mismatched tag cases through authorized fresh A/B review before the bounded C repair and independent D review. This lesson grants no editing scope or repair allowance.
