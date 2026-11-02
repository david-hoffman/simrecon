# Match residual support when comparing inverse estimators

**Version 1.0**

- ID: 20261029T233124Z-ra02-coordinator-matched-source-subspace
- Date: 2026-10-29T23:31:24.392499+00:00
- Task: [RA02](../docs/tasks/RA02.md)
- Role: coordinator recording independently reviewed A/B evidence
- Topic: mathematical comparison oracle
- Status: confirmed
- Observation: The first tiny 2D comparison's public spectral formula agreed with independent expectations near 1e-16, while comparison with a restricted real source basis differed by 6.6669e-4. Its arbitrary spatial residual generated modes outside that basis. Replacing it with a predeclared spatially constant phase residual restored the matching premise without changing tolerance or runtime. Fresh blind B independently accepted the corrected whole checkpoint and verified the mathematical cause. This was a fixture-premise defect, not evidence of a reconstruction bug.
- Evidence: `tests/test_reference_alignment_ra02.py` SHA256 `1b09183b3113448c3fef960e1ab98baff5a2cc8255a3eb227a124370375a7cc0`; fixture SHA256 `b26dd26518b70f04d3ad3f50fec5d04c7671ecbe01fd22b170a65363d4f59b20`; local A REPORT/diagnose-01.txt and fresh B verdict linked from the sole task Current state. Final A narrow run 18 passes; B capture-disabled run 18 passes. Full candidate verification remains separate.
- Suggested action: Before interpreting a spectral/raw inverse discrepancy, check the full observation-generated support, metric, source Gram penalty and signed lifts, including deliberately added residuals. Keep own-estimator correctness distinct from conditional physical/source equivalence.
