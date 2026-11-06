# Validate before identity hashing can materialize arrays

**Version 1.0**

- ID: 20261106T133801Z-ce07-c-validation-before-identity-copy
- Date: 2026-11-06T13:38:01.432703+00:00
- Task: [CE07 public workflow](../docs/tasks/c-equivalence-workflow.md)
- Role: restricted C, lesson handed off to coordinator
- Topic: representation validation and diagnostic allocations
- Status: confirmed
- Observation: Identity hashing can allocate through endian normalization or contiguous copying, so it belongs after actual-backings/type/source/native validation. A later scientific-stage validator does not protect an earlier diagnostic materialization. The before/after ordering logs demonstrate this without adding a new size cap or executing unsafe targets.
- Evidence: [workflow ordering](../src/simrecon/_workflow.py) and [transfer validation](../src/simrecon/_workflow_transfer.py). The task evidence root retains `C1-correction-1/ordering-diagnosis-1.log`, `ordering-qualification-1.json` and the focused 472-example passing log under task Python 3.13.12. Three scalar-backed invalid declarations rejected before materialization after correction; external interception prevented large allocation during diagnosis.
- Suggested action: Keep identity/snapshot materialization after validation of the same retained backing values and relevant representation counts. This factual lesson grants no new rejection rule, size cap, test requirement or edit authority.
