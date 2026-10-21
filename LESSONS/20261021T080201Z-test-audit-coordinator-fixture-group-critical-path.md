# Fewer fixture captures can lengthen the critical path

**Version 1.0**

- ID: 20261021T080201Z-test-audit-coordinator-fixture-group-critical-path
- Date: 2026-10-21T08:02:01Z
- Task: [Test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: parallel fixture scheduling
- Status: confirmed
- Observation: A fixed source/candidate/candidate/source cohort ran all 40 reference-export cases with four workers. Grouping consumers by the two module-fixture selectors reduced captures from eight to two and aggregate child CPU time by 46.10%, but increased mean wall time from 7.356050 s to 7.884740 s. The reconstruction group created a roughly 5-second single-worker tail. All cases passed and exact observed owned native execution sets matched. The candidate was rejected; this cohort does not establish its effect in the complete suite.
- Evidence: `artifacts/test-audit-ci/five-minute-reference-grouping/REPORT.md`, run `7311684d-ce4c-40f4-9e1c-3ada5f708231`, four timing receipts, actual capture/Popen/worker attribution and `native-comparison.json`. No tracked grouping change was adopted. Fresh clean Astra independently diagnosed the serialization from those records.
- Suggested action: Measure wall time and the longest worker path before adopting fixture affinity for a runtime goal. Lower capture counts or CPU use alone establish no faster gate. Preserve a negative experiment rather than repeating it without a new mechanism.

