# Exact frequency expressions prevent extra oracle slack

**Version 1.0**

- ID: 20261011T212202Z-raw-point-bead-calibration-coordinator-frequency-bound
- Date: 2026-10-11T21:22:02.566263+00:00
- Task: [raw-point-bead-calibration](../docs/tasks/raw-point-bead-calibration.md)
- Role: coordinator, recording verified role evidence
- Topic: numerical oracle
- Status: confirmed
- Observation: The old frequency observer rounded its expected value before a relative-error assertion. B01 found a returned value outside the exact inherited bound that the assertion accepted: error/bound 1.0308333333 for N=4, converted d=0.09 micrometres, k=-2. A03 used exact rational arithmetic for both expected expression and bound; fresh B02 accepted it.
- Evidence: artifacts/raw-point-bead-calibration-20261011/B01/final.txt; A03/math-probe-final.txt; accepted test checkpoint cefc04d713edd91fdf188045afc5b3627c39c2ca. Python3.13.12/NumPy2.5.3, Darwin arm64.
- Suggested action: For an exact converted-spacing expression, compare returned binary64 values and the stated bound with exact rational arithmetic in the observer. This grants no runtime or policy edit.
