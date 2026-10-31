# Binary64 physical carriers can change an exact window ceiling

**Version 1.0**

- ID: 20261031T023130Z-ra07-coordinator-exact-carrier-window
- Date: 2026-10-31T02:31:30.499280+00:00
- Task: [RA07](../docs/tasks/reference-alignment-ra07.md)
- Role: coordinator
- Topic: independent numerical fixture qualification
- Status: confirmed
- Observation: A1 independently found that converting nominal half-bin shifts to physical binary64 carriers put three exact shifts just above one half. Their nominal output windows were too small under the approved rational geometry. This was a fixture defect found before product observation.
- Evidence: artifacts/ra07/roles/A1/handoff.md; original measurement.log/oracle-inputs.json and corrected measurement-final.log/oracle-inputs-final.json, qualified by B1/B2.
- Suggested action: Check the exact converted carrier times field length and both endpoint guards when constructing a positive fixture. Do not use nominal floating-bin labels as support proof.
