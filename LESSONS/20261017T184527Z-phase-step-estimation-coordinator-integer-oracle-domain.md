# Exact periodic indices need exact oracle integer arithmetic

**Version 1.0**

- ID: 20261017T184527Z-phase-step-estimation-coordinator-integer-oracle-domain
- Date: 2026-10-17T18:45:27.572154+00:00
- Task: docs/tasks/phase-step-estimation.md
- Role: coordinator
- Topic: numerical test oracle
- Status: confirmed
- Observation: In NumPy 2.5.3, `np.array([0, 2**64 - 1, -7])` has float64 dtype and rounds `2**64 - 1` to `2**64`. On grid `(2,3,4)`, order +1 and output mode `(0,0,0)`, the approved exact modular source index `(0,0,3)` becomes `(0,2,3)`. The shared test observer therefore disagreed with an estimator that correctly preserved huge/reduced carrier aliasing. This was an oracle defect, not scientific product-red. Small-carrier agreement did not validate the oracle over the full permitted integer domain.
- Evidence: C02/examples/carrier-reproduction01.py/log and public-observer-finding01.json; A06/report.json; committed tests/volume_phase_estimation_fixture.py::periodic_carrier and tests/test_volume_phase_estimation.py::test_integer_carrier_oracles_against_exact_finite_matrices at f890902df942a9aec3529444f5c706f5c8def8a2; fresh B05/final.txt. New correction evidence remains postimplementation/supplemental; earlier accepted checkpoints and invalid huge-oracle execution remain historically distinguished.
- Suggested action: For a finite periodic integer-carrier contract, extract Python integers before signed-order multiplication and preserve exact modular indexing before narrowing or floating phase calculations. Keep declared provenance unchanged. Independently challenge the oracle over the public input representations and ranges; a valid small cohort does not establish the wider domain.
