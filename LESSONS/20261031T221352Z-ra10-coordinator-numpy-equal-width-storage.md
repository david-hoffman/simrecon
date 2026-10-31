# Equal storage width does not ensure a native NumPy scalar type

**Version 1.0**

- ID: 20261031T221352Z-ra10-coordinator-numpy-equal-width-storage
- Date: 2026-10-31T22:13:52.081146+00:00
- Task: [RA10](../docs/tasks/reference-alignment-ra10.md)
- Role: coordinator
- Topic: platform conversion
- Status: confirmed
- Observation: On the observed macOS arm64 NumPy2.5.3 environment, longdouble and float64 had equal storage width. The ordinary array-copy conversion retained a longdouble scalar type rejected by linear algebra. Explicit binary64 allocation repaired the permitted-input operation. This is a measured platform-specific observation, not a claim about every NumPy build.
- Evidence: ../artifacts/ra10/roles/C1/handoff.md; ../artifacts/ra10/roles/C1/commands.json; ../artifacts/ra10/roles/C1/continuation-1/handoff.md. Focused validation passed687 cases with unchanged final source.
- Suggested action: When accepting all real NumPy widths, verify the actual native binary64 representation used by numerical dependencies, including longdouble on required platforms.
