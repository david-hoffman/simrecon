# Check the full declared count even when used arrays are small

**Version 1.0**

- ID: 20261104T063647Z-ce06-coordinator-aggregate-declared-count
- Date: 2026-11-04T06:36:47.742174+00:00
- Task: [CE06 acquisition modes](../docs/tasks/c-equivalence-acquisition-modes.md)
- Role: coordinator, from the independent D1 reproduction
- Topic: representation limits
- Status: confirmed
- Observation: Five time points and 429,496,730 phases declare 2,147,483,650 on-frames, above 2,147,483,647. Both single-time and per-design products fit, and the used quadrature has only 90 elements. Both downstream consumers accepted this malformed shape. The adjacent declaration of 2,147,483,645 frames is defined with the same used arrays.
- Evidence: Independent D1 verdict SHA-256 336d85ee4a67a2426ad99958ea94facd6bd65843f43fa0dc6ded16b5693b935e; approved [used-record contract](../docs/contracts/c-equivalence-acquisition-modes-v1.md); exact supplemental [public regression tests](../tests/test_c_acquisition_boundary.py). Four originally missing rejections and four passing repairs were reproduced before correction.
- Suggested action: Check the complete used signed-width product from metadata. Test the last-fitting and first-overflow declarations through the real consumers without materializing unused phases or introducing a resource limit.
