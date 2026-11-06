# Distinguish payload reads from public directory metadata

**Version 1.0**

- ID: 20261106T202111Z-ce07-coordinator-public-directory-metadata-scope
- Date: 2026-11-06T20:21:11.374770+00:00
- Task: [CE07](../docs/tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: review process
- Status: confirmed
- Observation: B7 withheld acceptance after listing a pure-public test directory excluded by its literal packet scope; no implementation or excluded narrative payload was read. Fresh B8 independently accepted the unchanged checkpoint with the same file-payload allowlist and explicit public-directory metadata permission. Both reviews remain charged.
- Evidence: CE07 local durable evidence through the task pointer: B7/final.md; B8/packet.md and final.md; execution-accounting.json. Task Python3.13.12/NumPy2.5.3; pre-repair runtime f60507506511775fcda03a96840caf97d850e2c4.
- Suggested action: State file-payload boundaries and necessary ancestor/public-directory metadata permissions separately. Keep implementation and private narratives excluded; obtain fresh required review after a declared process violation.
