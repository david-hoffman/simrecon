# Check the represented phase matrix before applying an accuracy budget

**Version 1.0**

- ID: 20261011T201525Z-raw-point-bead-calibration-coordinator-phase-domain
- Date: 2026-10-11T20:15:25.636805+00:00
- Task: [Raw point-bead calibration](../docs/tasks/raw-point-bead-calibration.md)
- Role: coordinator observing blind A evidence
- Topic: numerical fixture conditioning
- Status: confirmed
- Observation: Blind A's first finite huge-angle phase fixture had represented matrix condition number about 19.68, outside the inherited informative accuracy regime of at most 10. A replaced it with an independently checked finite huge-angle set whose condition number was about 9.03. Finite angles alone do not establish the regime needed by this particular forward-error budget.
- Evidence: The task pointer indexes source-free A01/phase-capability.txt (SHA256 3f82f30407791e419a23b02d74a30317299a9da1b14bff3c04cc737b89a3f7f8), A01/report.md and the [independent fixture](../tests/raw_point_bead_fixture.py). The probe used the normative represented phasor matrix with Python3.13.12/NumPy2.5.3 on macOS arm64; no product source selected the expectation. The reported values are native floating observations, not exact condition numbers or a physical accuracy claim.
- Suggested action: Check the represented matrix's applicable numerical regime before applying a contract's informative error budget. This does not authorize an extra runtime condition-number rejection.
