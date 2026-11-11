# Hash canonical numerical storage through a byte view

**Version 1.0**

- ID: 20261106T202111Z-ce07-coordinator-native-numerical-buffer-identity
- Date: 2026-11-06T20:21:11.374770+00:00
- Task: [CE07](../tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: provenance
- Status: confirmed
- Observation: Admitted native g/G arrays with standard binary64 components had the same normalized dtype strings and bytes as ordinary d/D arrays, but direct Python numeric-buffer export raised ValueError. A byte view of already normalized storage preserved the required input hashes and passed all four public cases without an extra payload copy.
- Evidence: CE07 local durable evidence through the task pointer: support/complex-snapshot-public-symptom-2.json; B8/final.md; C1-D1-correction-2/c-focused-regression-before-1.log and c-focused-regression-after-boundary-1.log; c-implementation-handoff.md. Task Python3.13.12/NumPy2.5.3; pre-repair runtime f60507506511775fcda03a96840caf97d850e2c4.
- Suggested action: Treat canonical byte identity and Python numeric-buffer format support as separate concerns. Preserve checked original storage and use a byte representation for hashing.
