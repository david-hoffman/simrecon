# Use the value that passed validation

**Version 1.0**

- **ID** 20261104T195927Z-ce06-coordinator-validated-values
- **Date** 2026-11-04T19:59:27.746346+00:00
- **Task** CE06 acquisition modes
- **Role** Coordinator
- **Topic** Public value record validation
- **Status** Confirmed
- **Observation** A genuine record subclass supplied valid data during validation and a different value during computation. In five public calls the result matched the genuine alternate input. The selected diagnostics and numerical results passed after consumers used the checked values.
- **Evidence** The [boundary tests](../tests/test_c_acquisition_boundary.py) pair stable, genuinely changed, and inconsistent record controls. The source-free scoped run used Python 3.13.12 and NumPy 2.5.3. Runtime commit `43c66eb2402e8ce1ad7761d1659167b198480bf5` binds the repair and cases.
- **Suggested action** Include a distinguishable genuine alternate when testing whether public consumers use data that passed validation.
