# Trace caller capabilities before helper parameters

**Version 1.0**

- ID: 20261102T235516Z-ce03-coordinator-caller-before-helper
- Date: 2026-11-02T23:55:16.709319+00:00
- Task: [CE03](../tasks/c-equivalence-optical-transfer.md)
- Role: coordinator
- Topic: source-contract scope
- Status: confirmed
- Observation: The selected radialft caller fixes napodize=10 and exposes no edge selector. A draft had promoted helper-only width/sine/bypass branches into public options. The coordinator corrected this before any test or runtime authorship; independent revised and delta source reviews accepted the final contract.
- Evidence: [CE03 source contract](../contracts/c-equivalence-optical-transfer-v1.md); task evidence source-review-1, source-review-2 and source-review-2-delta via the [task pointer](../tasks/c-equivalence-optical-transfer.md). Source reads only; no retained C execution.
- Suggested action: Trace the actual caller, parser and build branch before exposing a helper option. Keep unused helpers outside the selected public profile unless separately authorized.
