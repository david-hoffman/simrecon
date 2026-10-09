# Snapshot the whole binding invariant before assignment probes

**Version 1.0**

- ID: 20261009T074358Z-volume-otf-01-root-whole-binding-invariant
- Date: 2026-10-09T07:43:58Z
- Task: VOLUME-OTF-01, [task pointer](../docs/tasks/volume-otf-preparation.md)
- Role: coordinator
- Topic: public record observer
- Status: confirmed
- Observation: The first frozen-binding observer prescribed AttributeError/TypeError despite unspecified assignment errors. After correction, fresh B independently exercised the complete ownership test with a refusal that preserved values but replaced source. The observer passed because it snapshotted each target only when reached, absorbing earlier corruption. This was a test defect, not product-red evidence. An initial whole-record snapshot and checks after every assignment resolved it; fresh B accepted compliant exception/silent-refusal records and rejected ordered cross-field controls. Writable array contents remained permitted.
- Evidence: [U07/U08 contract](../docs/contracts/volume-otf-preparation-v1.md); test-only checkpoint73a493e9c416376875a76187b3edd373c85205e8/testd0a4e7aea43f030ea17af6a75c82d3238eac663ed9a962a62af3f878bde3362f; accepted corrected checkpoint1a1102d9169dc1c1cbc57728592daf4f9350d159/test727a1f219376dc643791232a8ae6e4af21b84b95d2edbf75bab207e9ab43b120. Ignored B9/B10 evidence is linked through the task pointer; Python3.13.12/NumPy2.5.3 on macOS arm64. These are observer diagnostics, not native product execution.
- Suggested action: For an approved whole-record frozen-binding guarantee, capture all bindings before assignment probes and check all afterward. Use distinct valid replacements, admit unspecified refusal forms, and challenge same-field and cross-field corruption. Do not add array-content immutability.
