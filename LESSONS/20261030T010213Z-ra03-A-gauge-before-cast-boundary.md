# Check rounding examples after every prescribed scale

**Version 1.0**

- ID: 20261030T010213Z-ra03-A-gauge-before-cast-boundary
- Date: 2026-10-30T01:02:13Z
- Task: RA03
- Role: A
- Topic: independent numerical fixtures
- Status: confirmed
- Observation: A proposed float32 lost-nonzero example used 2^-150 before a 5/4 gain. Its transformed value exceeds half the smallest float32 subnormal, so it rounds up rather than disappearing. The corrected input 2^-152 becomes 5*2^-154 and rounds to zero. An exact dyadic assertion now executes in a baseline oracle control even while the new evaluator API is absent.
- Evidence: Baseline e994e131b5506fe4291d7dcbc817e91150d3933f; tests/test_reference_alignment_ra03.py::test_oracle_analytic_peak_and_unequal_side_sign; tests/reference_alignment_ra03_fixture.py::pairing_control; artifacts/ra03/A/pytest-final-04.txt and REPORT.md. Source-free narrow pytest on Python3.13.12/macOS27.0.1 passed that control; evaluator cases separately failed for API absence.
- Suggested action: Derive boundary examples after all required arithmetic transformations. Exercise numerical fixture anchors independently of a missing feature import so feature absence cannot hide an invalid example. This observation grants no additional edit scope.
