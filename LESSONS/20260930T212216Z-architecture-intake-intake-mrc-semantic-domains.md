# MRC spacing fields need a declared semantic domain

**Version 1.0**

- ID: 20260930T212216Z-architecture-intake-intake-mrc-semantic-domains
- Date: 2026-09-30T21:22:16Z
- Task: [ARCHITECTURE-INTAKE](../docs/tasks/architecture-intake.md)
- Role: intake
- Topic: file-format metadata semantics
- Status: confirmed
- Observation: The studied legacy program interprets image spacing fields as micrometres and OTF spacing fields as reciprocal micrometres. A file extension and shared header field names do not establish the data's semantic domain. This is source-study evidence, not a verified on-disk decoding contract.
- Evidence: [Read-only study and source locators](../docs/architecture/legacy-mrc-observations.md), particularly `sirecon.c:194–196` and `helpers.c:747–781`; the four studied files matched the retained snapshot SHA-256 manifest on September 30, 2026. [Modern MRC specification](https://www.ccpem.ac.uk/mrc-format/mrc2014/) assigns angstrom cell dimensions to modern spatial headers.
- Suggested action: Give images and frequency-domain calibration distinct metadata contracts. Require an explicit domain/profile before unit conversion; preserve unresolved source values. Obtain independent format fixtures before claiming legacy compatibility.
