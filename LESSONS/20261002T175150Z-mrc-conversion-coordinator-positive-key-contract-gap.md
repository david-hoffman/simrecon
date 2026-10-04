# Complete branch coverage can miss unapproved positive-input restrictions

**Version 1.0**

- ID: 20261002T175150Z-mrc-conversion-coordinator-positive-key-contract-gap
- Date: 2026-10-02T17:51:50Z
- Task: MRC-CONVERSION-01
- Role: coordinator recording fresh D evidence
- Topic: public-contract regression coverage
- Status: confirmed
- Observation: The 44-scenario candidate passed 377/377 statements and 100/100 branches. Fresh D still reproduced rejection of numeric wavelength channel keys 00 and U+0660, although approved M38 introduces neither restriction. Existing M38 checked only a nonnumeric key. Complete native coverage did not establish every permitted positive-input class.
- Evidence: reviewed candidate `979348bf717caa40a934290117b6b05c18b508e8`; [D finding](../artifacts/mrc-conversion/roles/d-report.txt); [approved M38](../docs/tasks/mrc-conversion-coverage-amendment.md); [exact canonical log](../artifacts/mrc-conversion/roles/coordinator-pre-d-verify.log); [bounded proposed regression contexts](../docs/tasks/mrc-conversion-key-repair.md). Scratch-free public harmonize probe, macOS arm64/pinned task environment.
- Suggested action: Pair rejection cases with evidenced permitted input forms when validation can silently narrow a public contract. Add only explicitly counted/approved contexts; retain native coverage and independent review rather than treating coverage as behavioral acceptance. Further repair needs the owner's extension; this lesson grants none.
