# Ideal roots can overconstrain represented phase acceptance

**Version 1.0**

- ID: 20261008T060429Z-integer-drift-01-coordinator-analytic-root-acceptance
- Date: 2026-10-08T06:04:29.193992+00:00
- Task: INTEGER-DRIFT-01 / docs/tasks/integer-drift-correction.md
- Role: coordinator, recording fresh B1 finding and B2 acceptance
- Topic: legitimate numerical outputs
- Status: confirmed
- Observation: A supplemental comparison to ideal -i rejected the principal angle -0x1.921fb54442f19p+0 despite its represented-target distance 1.1366395296671158e-13 satisfying the unchanged 1.1368683772161603e-13 contract budget. Ideal and represented targets differ slightly. Blind A confined ideal-root checks to observer sanity; fresh B2 accepted the corrected complete checkpoint and independently confirmed wrong signs still reject.
- Evidence: tests/test_integer_drift.py at checkpoint1041dab03f25ef06036e54125af22badc759b408; ignored B-report.md, A-correction-report.md and B2-report.md in the task evidence directory; source-free correction replay on Python3.13.12/NumPy2.5.3. Shared fixture, strict observer and contract were unchanged.
- Suggested action: Audit supplemental analytic assertions for false rejection at the full permitted boundary. Use them to validate the independent observer or account separately for target differences; preserve the actual contract budget.
