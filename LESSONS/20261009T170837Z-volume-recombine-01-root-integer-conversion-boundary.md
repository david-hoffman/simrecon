# Integer conversion errors need field-specific translation

**Version 1.0**

- ID: 20261009T170837Z-volume-recombine-01-root-integer-conversion-boundary
- Date: 2026-10-09T17:08:37.960687+00:00
- Task: VOLUME-RECOMBINE-01
- Role: root coordinator
- Topic: public input conversion and regression oracles
- Status: confirmed
- Observation: Fresh D reproduced six public calls on candidate `68fd8a06cdea377dd55477a3a3f1903c7db40c0d` where an integer subclass raised TypeError, ValueError or OverflowError during output-dimension or calibration-origin conversion. Each raw exception leaked instead of the contract's field-specific SimreconError. Ordinary integer subclasses succeeded; unrelated RuntimeError and MemoryError controls propagated. The full local gate had passed, so this is a concrete behavioral/test omission rather than a percentage finding.
- Evidence: `docs/contracts/volume-recombination-v1.md` input representations and expected-conversion rule; ignored `artifacts/volume-recombination-execution/d-final-01.txt` and its frozen source-free public-probe stream `d-native-01.jsonl`; Python 3.13.12 / NumPy 2.5.3. The sanitized supplemental correction is `a-correction-public-handoff-06.json`; fresh A6/B7 and C correction are pending at creation.
- Suggested action: Translate only expected conversion exception classes at the field boundary; preserve unrelated/resource exceptions. Review tests against legitimate integer-extraction alternatives because the contract prescribes no private conversion hook or call count. A test must not reject an equivalent valid result merely because an implementation avoids the overridden hook. This observer alternative remains subject to independent A/B review; the lesson grants no new scope.
