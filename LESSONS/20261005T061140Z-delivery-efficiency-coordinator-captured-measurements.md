# Internally captured measurements are absent from phase logs

**Version 1.0**

- ID: 20261005T061140Z-delivery-efficiency-coordinator-captured-measurements
- Date: 2026-10-05T06:11:40Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: verification evidence
- Status: confirmed
- Observation: The existing M25 parent test parses captured subprocess JSON but emits none of its baseline, peak or increment values on success. Saving the canonical phase output cannot recover those fields automatically.
- Evidence: [test_mrc_conversion.py](../tests/test_mrc_conversion.py), `test_m25_native_memory`; [mrc_fixture_memory.py](../tests/mrc_fixture_memory.py), JSON output; unchanged from preparation commit `e00ae80f6b5043d97b6e953d71c70f20ffaccd5b`. Static inspection on this workstation established the output path; no retrieval rerun was made.
- Suggested action: Say logs retain emitted output only. If a later task needs the numerical fields, authorize a reviewed same-run export before verification rather than rerun scientific tests solely to retrieve them.
