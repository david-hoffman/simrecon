# An unentered conditional injection does not prove its named failure

**Version 1.0**

- ID: 20261029T083227Z-r5-study-a-conditional-injection-proof
- Date: 2026-10-29T08:32:27Z
- Task: R5-study / R5-S, frozen packet b12b8f2397031ebf82ad67f58b1c64d5439d9ab375cf5d1c2c6dc83f75ff6ab7.
- Role: Fresh native blind A.
- Topic: Public dependency injection proof limits.
- Status: confirmed.
- Observation: Twenty original public fault controls passed during qualification. All twelve conditional optics rows returned completed_local without entering their public observer; source range and unrelated-exception rows actually entered and exercised their asserted failures. Passing a conditional test therefore does not by itself demonstrate that its named failure was observed. Retirement still requires independent mapping of each failure obligation and legitimate bypass alternative.
- Evidence: artifacts/test-consolidation/R5/A-results/qualifications.json, S07_public_fault_observations; 04-qualifications.json/.stdout/.stderr. Locked Python 3.13.12 and versions in baseline-identities.json. No implementation or history inspection.
- Suggested action: Keep public entry counts/outcomes separate from conditional success, and route uncovered failure obligations to the authorized owner and fresh review. This observation grants no private product seam or deletion authority.
