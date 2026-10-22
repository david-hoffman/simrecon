# Absent-feature errors can conceal invalid test declarations

**Version 1.0**

- ID: 20261011T212202Z-raw-point-bead-calibration-coordinator-public-declaration-boundary
- Date: 2026-10-11T21:22:02.566263+00:00
- Task: [raw-point-bead-calibration](../docs/tasks/raw-point-bead-calibration.md)
- Role: coordinator, recording verified role evidence
- Topic: public test input
- Status: confirmed
- Observation: C01 found the missing-z test failed at declaration: the rank-based helper turned shape (1,7,2,3) into five dimensions with four named axes. A04 directly declared the supported four-axis input; fresh B03 observed one calibration call and the intended missing-z error, while the old case made zero calls.
- Evidence: artifacts/raw-point-bead-calibration-20261011/C01/public-reproduction.py and .log; A04/declaration-boundary.log; B03/final.txt; accepted correction checkpoint 8d81b9cc2c7ab0f67469a36480081ef5e957c73a.
- Suggested action: Validate the preceding public declaration independently while a new export is absent. A downstream rejection test needs a valid input reaching that boundary; preserve diagnosed corrections and prior attempts.
