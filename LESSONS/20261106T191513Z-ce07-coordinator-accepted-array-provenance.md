# Preserve original identities for accepted array storage

**Version 1.0**

- ID: 20261106T191513Z-ce07-coordinator-accepted-array-provenance
- Date: 2026-11-06T19:15:13.663334+00:00
- Task: [CE07](../docs/tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: provenance
- Status: confirmed
- Observation: A genuine ndarray subclass in an accepted transfer produced a finite workflow result but omitted its required original input identity. Fresh blind tests independently froze original bytes and exposed direct and nested omissions; the scoped repair preserves those identities without changing the scientific stages.
- Evidence: Local durable root `/private/tmp/simrecon-ce07-evidence-20261104`: D1/final.md; A1-correction-9/revised-original-identities-1.log; B6/final.md; C1-D1-correction-1/c-focused-regression-before-1.log and c-focused-regression-after-1.log. Pre-repair runtime commit4455f668bd470002579cafd145f9e1cc7f312419; existing task Python3.13.12.
- Suggested action: Audit original-input provenance over the same admitted backing types as scientific consumption. Keep original and consumed identities separate.
