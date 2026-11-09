# Native resumed-session token counters are cumulative

**Version 1.0**

- ID: 20261104T045108Z-ce06-coordinator-native-usage-counter
- Date: 2026-11-04T04:51:08.666383+00:00
- Task: [CE06 acquisition modes](../docs/tasks/c-equivalence-acquisition-modes.md)
- Role: coordinator
- Topic: observed native metering semantics
- Status: confirmed for the recorded CLI events; billing/model identity unqualified
- Observation: B1's completion after its public study reported 1,660,443 input tokens. Its later first full-review completion reported 6,818,218. The latter exactly matched native total_token_usage, not last_token_usage. Adding both would double-count 1,660,443. Cached inputs and reasoning outputs are subsets of input and output respectively.
- Evidence: Durable CE06 usage-semantics-receipt.json, SHA256 f1c2f56322fd5e28a6387979513ce08bd9b219189da627a24e487f07d1fb079b. It preserves token_count metadata only from B1 and B2, compares each emitted completion with total_token_usage, and checks total=input+output. No conversation/source/private-reasoning content was printed. Actual served identity, billing and unavailable failed-response/root/advisory measurements remain unknown.
- Suggested action: Use the newest observed cumulative token total once per native session. Retain every invocation's elapsed time, command status, failure and review charge separately. Verify semantics if the CLI changes; a resume erases no history and unknown metering is not zero.
