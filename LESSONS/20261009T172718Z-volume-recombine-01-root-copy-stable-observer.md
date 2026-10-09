# Conversion observers must survive permitted scalar snapshots

**Version 1.0**

- ID: 20261009T172718Z-volume-recombine-01-root-copy-stable-observer
- Date: 2026-10-09T17:27:18.584813+00:00
- Task: VOLUME-RECOMBINE-01
- Role: root coordinator
- Topic: supplemental public exception oracles
- Status: confirmed
- Observation: Fresh blind B7 independently challenged the new integer-conversion observer at checkpoint `eace87eb965c387e46fee56177bc966123e8bef7`. The observer rejected 50 compliant independent-snapshot outcomes and accepted 50 swallowed copied-hook failures. It also rejected two unrelated/resource exceptions solely because their identity differed from the caller-owned exception. These were defects in supplemental observer instrumentation, not changes to the approved numerical contract. Accurate extraction that never invokes the failing override remains a permitted alternative.
- Evidence: `docs/contracts/volume-recombination-v1.md`; ignored `artifacts/volume-recombination-execution/b-final-07.txt` and frozen source-free independent challenge stream `b-native-07.jsonl`; B7 test-only hash restoration preserves the accepted B6 mathematical baseline. Python 3.13.12 / NumPy 2.5.3. Eligible blind A7 correction packet `a-correction-07-packet.txt` records the dependency scope; its result and fresh B8 verdict remain pending at creation.
- Suggested action: Observe actual hook invocation and the exception it emits across permitted independent copying. Accept correct field translation or actual unrelated/resource propagation and accurate uninvoked extraction; reject swallowed invoked failures. Challenge an observer with legitimate snapshot alternatives before accepting it. This lesson supplies evidence, not new scope or a review verdict.
