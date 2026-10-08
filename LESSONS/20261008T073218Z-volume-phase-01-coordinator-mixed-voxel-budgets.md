# Test local accuracy with mixed intensities in one call

**Version 1.0**

- ID: 20261008T073218Z-volume-phase-01-coordinator-mixed-voxel-budgets
- Date: 2026-10-08T07:32:18.960119+00:00
- Task: VOLUME-PHASE-01; docs/tasks/volume-phase-separation.md
- Role: coordinator
- Topic: independent numerical test coverage
- Status: confirmed
- Observation: Blind B1 found that uniform per-call intensity scales did not challenge the approved per-voxel accuracy budget. A added one mixed-intensity public test; fresh B2 verified all prior test definitions, observer and contract unchanged and independently accepted the revised checkpoint. An erased tiny normal-scale voxel differs from its stored-input target by more than 3e10 local budgets, while the subnormal allowance still permits zero for four harmonic coordinates in that example.
- Evidence: tests/test_volume_phases.py mixed-voxel test; docs/contracts/volume-phase-separation-v1.md V07/V09; accepted checkpoint4753ba70f5d2cf1b2ffd69afc878fd8e1421f38e; local A-correction-report.md and B2-report.md in the task execution artifacts. Independent Decimal/Fraction observers, Python3.13.12/NumPy2.5.3. C later passed all183 frozen cases; this lesson supplies no independent product acceptance.
- Suggested action: When an array operation promises local scaled accuracy, include simultaneous extreme local scales in public tests and compare each location against its own budget.
