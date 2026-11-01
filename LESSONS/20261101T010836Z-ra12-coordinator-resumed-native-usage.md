# Resumed native usage was cumulative in the observed CLI

**Version 1.0**

- ID: 20261101T010836Z-ra12-coordinator-resumed-native-usage
- Date: 2026-11-01T01:08:36.352111+00:00
- Task: [RA12](../docs/tasks/reference-alignment-ra12.md)
- Role: coordinator
- Topic: native resource accounting
- Status: confirmed for the observed root and CLI version
- Observation: With Codex CLI 0.166.0-alpha.5.1, the resumed `turn.completed` usage matched the original producer's `total_token_usage`, including the first invocation. The initial root snapshot was 556,167 total tokens; the final resumed snapshot was 759,003; the verified resume increment was 202,836. Adding both snapshots would double-count the initial invocation. This observation does not establish other clients' counter semantics.
- Evidence: Local `artifacts/ra12/advice/native-token-counter-producer-extract-1.json`, SHA-256 `641b2340ed1e7617898afa9834877959061bb26b54d1319780c64b734d4bf74f`, retains token-counter metadata only. `artifacts/ra12/accounting-correction-1.json` preserves the diagnosed overcount and correction. No conversation or reasoning content is extracted into this lesson.
- Suggested action: For this observed CLI, count the measured root once at its final cumulative snapshot, or sum verified increments. Recheck changed versions or evidence. Preserve failed launches and unavailable metering separately.
