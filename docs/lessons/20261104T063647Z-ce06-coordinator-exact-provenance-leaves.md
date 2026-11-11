# Compare provenance values after checking their exact types

**Version 1.0**

- ID: 20261104T063647Z-ce06-coordinator-exact-provenance-leaves
- Date: 2026-11-04T06:36:47.741823+00:00
- Task: [CE06 acquisition modes](../tasks/c-equivalence-acquisition-modes.md)
- Role: coordinator, from the independent D1 reproduction
- Topic: public record validation
- Status: confirmed
- Observation: A mutable UserString with the approved digest compared equal to the exact ten-file tuple. Both public consumers accepted it, and the estimator stored the mutable object in its returned settings. Existing wrong-order and wrong-hash tests did not distinguish this case.
- Evidence: Independent D1 verdict SHA-256 336d85ee4a67a2426ad99958ea94facd6bd65843f43fa0dc6ded16b5693b935e; approved [used-record contract](../contracts/c-equivalence-acquisition-modes-v1.md); exact supplemental [public regression tests](../../tests/test_c_acquisition_boundary.py). Four originally missing rejections and four passing repairs were reproduced before correction.
- Suggested action: Check the exact immutable tuple, pair and string schema before relying on value equality. Pair the malformed input with a real success using the approved tuple. Valid immutable values do not require different object identity.
