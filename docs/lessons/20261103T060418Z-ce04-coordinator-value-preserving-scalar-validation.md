# Preserve scalar values while checking numerical bounds

**Version 1.0**

- ID: 20261103T060418Z-ce04-coordinator-value-preserving-scalar-validation
- Date: 2026-11-03T06:04:18.167074+00:00
- Task: [CE04](../tasks/c-equivalence-known-parameters.md)
- Role: coordinator
- Topic: scalar numeric validation
- Status: confirmed
- Observation: A valid NumPy float16 Wiener scalar failed while the same Python float succeeded. Blind A3 and fresh B4 confirmed seven scalar positions affected by one overflow family; 39 positive counterparts and the prior 286 cases passed. C extracted NumPy scalar values before absolute-value/comparison arithmetic, retaining the magnitude check before binary64 conversion. This also avoids fixed-width signed-minimum absolute overflow and preserves rejection of exact integers/rationals just outside the float32 bound.
- Evidence: public/float16-scalar-public-finding.md, A3-scalar/report.md, B4/final.md and C1-scalar-correction/report.md through the task's sole evidence pointer. The correction passed 381 focused cases plus 15 public successes and six required rejections. Wider-than-binary64 native floating precision was not dynamically exercised on this host; exact rational controls checked fine boundary distinctions.
- Suggested action: Check permitted scalar kinds as well as arrays. Normalize representation without losing the input value, and validate magnitude before a lossy conversion can round an out-of-domain value onto the boundary.
