# Synthetic record checks missed actual launch formats

**Version 1.0**

- ID: 20261018T042213Z-observable-phase-coordinator-record-dialects
- Date: 2026-10-18T04:22:13.111834+00:00
- Task: PHASE-OBSERVABLE-SUBSPACE
- Role: coordinator
- Topic: evidence-record compatibility
- Status: confirmed
- Observation: The operative input binder rejected retained coordinator launch records because five of fourteen invocation tuples used a full nested packet pin rather than a flat digest. The nested pins matched their actual packet files. Two named continuations also used explicit stage/predecessor-directory fields and recorded the requested thread in argv. Earlier synthetic checks did not exercise those actual association formats. A separate native CLI web-search serialization had two distinct ID fields; its original bytes also needed preservation.
- Evidence: `artifacts/phase-observable-subspace-20261018/native-record-shape-diagnosis01.json`, `S10/baseline-replay.json`, `S10/candidate-replay01.json`, and `H19/REPORT.json`. The baseline association replay rejected exactly five tuples; the corrected candidate replay passed all fourteen. These are opaque metadata/parser checks, not scientific or full-gate evidence.
- Suggested action: Use a single explicit launch-record grammar for future launches. Before expensive dependent work, check recorded native lifecycle and request/completion associations against the actual supported producer formats, alongside malformed controls. Preserve originals and missing-field limits when adapting an already recorded format. This lesson grants no edit scope, historical observation or gate waiver.
