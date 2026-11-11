# Vary the quantity a numerical test intends to distinguish

**Version 1.0**

- ID: 20261102T213329Z-ce02-coordinator-noise-design-invariance
- Date: 2026-11-02T21:33:29.446430+00:00
- Task: [CE02](../tasks/c-equivalence-preprocessing.md)
- Role: coordinator observing independent blind B findings
- Topic: numerical oracle discrimination
- Status: confirmed
- Observation: The first multi-direction phase fixtures used column permutations
  of one separation matrix. A column permutation preserves every squared row
  norm, so those fixtures could not detect broadcasting direction zero's noise
  factors to all directions. A public control mixing uniform and irregular
  full-rank designs now independently expects different variance vectors.
- Evidence: B2's formal finding, A correction2 and B4's accepted content manifest
  are retained through the task's ignored evidence-location pointer. The keeper
  is `test_supplied_noise_uses_each_directions_distinct_design` in
  [the accepted tests](../../tests/test_c_preparation.py); expected vectors are
  `[1,1,1]` and `[5/4,5/4,5/2]`. Contract hash and checkpoint identities are in
  the sole Current state. No runtime observation was used to set the oracle.
- Suggested action: When a test varies inputs, independently check that the
  intended observed quantity actually varies. Preserve separate controls for
  valid invariances and for cross-input differences; this lesson adds no scope,
  test quota or policy authority.
