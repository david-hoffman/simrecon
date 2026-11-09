# Convert admitted NumPy real snapshots with a terminating conversion

**Version 1.0**

- ID: 20261106T191513Z-ce07-coordinator-numpy-real-snapshot-termination
- Date: 2026-11-06T19:15:13.663334+00:00
- Task: [CE07](../docs/tasks/c-equivalence-workflow.md)
- Role: coordinator
- Topic: provenance
- Status: confirmed
- Observation: On the task NumPy2.5.3 arm64 platform, longdouble is8bytes with binary64 format, yet item() retains a NumPy scalar. An otherwise unchanged legal transfer-identity optics value1.0 raised RecursionError. Reviewed public-entry regressions pass after direct ordinary-float snapshot conversion; extended-width input domains remain excluded.
- Evidence: Local durable root `/private/tmp/simrecon-ce07-evidence-20261104`: public/identity-scalar-snapshot-finding-v1.json; B6/final.md; C1-D1-correction-1/c-focused-regression-before-1.log and c-focused-regression-after-1.log. Pre-repair runtime commit4455f668bd470002579cafd145f9e1cc7f312419; existing task Python3.13.12.
- Suggested action: Check actual admitted numeric format and ensure snapshot conversion terminates. Do not assume item() always yields a Python scalar or reject an admitted format by type spelling.
