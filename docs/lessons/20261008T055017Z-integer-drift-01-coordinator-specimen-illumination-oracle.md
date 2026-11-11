# Build specimen drift before stationary illumination

**Version 1.0**

- ID: 20261008T055017Z-integer-drift-01-coordinator-specimen-illumination-oracle
- Date: 2026-10-08T05:50:17.263378+00:00
- Task: INTEGER-DRIFT-01 / docs/tasks/integer-drift-correction.md
- Role: coordinator, recording blind A's supplied fixture evidence
- Topic: independent scientific composition oracle
- Status: confirmed fixture control; candidate implementation not yet assessed
- Observation: An independent moving-specimen finite circular-convolution fixture with an asymmetric kernel distinguished correct phase preparation from pixel-only alignment by 0.818 intensity units in the public reconstruction control, while the independent object comparison error was 8.89e-16. Rolling a complete stationary acquisition also moves its illumination and models different motion.
- Evidence: tests/integer_drift_fixture.py; docs/contracts/integer-drift-correction-v1.md; checkpoint 84363e000e3f5243f348519cc09d35da69f304d3; ignored A-oracle-control.py/.txt and A-report.md in the task evidence directory. Command: .venv/bin/python artifacts/integer-drift-execution/blind_pytest.py --scratch-stdin < artifacts/integer-drift-execution/A-oracle-control.py; Python3.13.12/NumPy2.5.3. This is fixture-control evidence, not yet drift-candidate evidence.
- Suggested action: Retain explicit specimen-before-illumination construction and separate physical/model roundoff allowances when reviewing composition oracles.
