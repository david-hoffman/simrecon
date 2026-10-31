# Raw coverage events need native report normalization

**Version 1.0**

- ID: 20261031T141049Z-ra09-coordinator-native-coverage-normalization
- Date: 2026-10-31T14:10:49.218866+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator
- Topic: measurement interpretation
- Status: confirmed observer defects and independent native reconciliation
- Observation: The first local provenance helper compared raw SQLite tracing events directly with executable-statement and HTML counts. Multiline continuations and cleanup arcs caused false alarms. Corrected parsing and independent D translation reconciled all 70 owned files across the original SQLite, JSON and complete HTML reports without a source change or gate rerun. Aggregate arc compatibility remains weaker than a proof that one entire path executed.
- Evidence: artifacts/ra09/checks/qualification-support-1/qualification-1.json; qualification-2.json; parser-diagnosis-1.json; roles/D1/review-original.md. The original canonical receipt SHA256 is fd818f310cdcc35cc82dd58e92132e5354573de6da3818cd812b7554578b0513.
- Suggested action: Use the locked measurement tool's statement/branch interpretation when reconciling its native formats. Diagnose observer mismatches before classifying product defects; retain raw observations and explicit normalization limits.
