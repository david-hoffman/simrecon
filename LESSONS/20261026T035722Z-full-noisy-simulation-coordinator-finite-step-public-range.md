# A finite optimizer step does not prove public prediction range

**Version 1.0**

- ID: 20261026T035722Z-full-noisy-simulation-coordinator-finite-step-public-range
- Date: 2026-10-26T03:57:22.127453+00:00
- Task: FULL-NOISY-SIMULATION / PR53
- Role: coordinator
- Topic: numerical test oracle qualification
- Status: confirmed public diagnostic; independent correction review remains separately required
- Observation: A tiny-curvature input has a finite seed near 2^1002 and a finite float32 trial, but its exact public inverse prediction cannot meet the unchanged float64 output allowance. The target is about 124.7713 times the smallest positive float64 value. Its nearest representable distance is about 0.2287 such units; the allowance is about 0.01248 units. Requiring completed fitting from seed finiteness alone was an invalid test oracle.
- Evidence: The revised `test_tiny_curvature_seed_range_and_finite_ratio` and `tiny_cache_exact_reference` in the two specimen-fit test files; proposed corrected checkpoint `6103a54bbf0e445780afbfeff4f8bc6ddbe4a660b529d82f36e9a7e752d95b14`. The coordinator reproduced `simulation_inverse_operator_range` through the public inverse API without importing fit code on Python 3.13.12 / macOS arm64. The prior checkpoint and failure stay retained; the separate 2^-1010 example is supplemental post-implementation evidence.
- Suggested action: Qualify downstream public-call representability separately from seed range. Preserve recognized failures and partial ledgers. Route invalid numerical expectations through blind author correction and fresh independent review rather than changing a valid precision gate.
