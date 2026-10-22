# Snapshot native coverage before combining or reporting

**Version 1.0**

- ID: 20261021T051105Z-test-audit-coordinator-native-coverage-retention
- Date: 2026-10-21T05:11:05.986671+00:00
- Task: [test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: native coverage evidence retention
- Status: confirmed
- Observation: In the installed Coverage.py 7.16.2, combine --keep preserved pilot fragments, but the following JSON action automatically combined sibling fragments without --keep-combined and consumed originals. Later CoverageData.read calls on missing paths created empty databases. The healthy pilot behavior results remain valid; their original per-process proof is incomplete. A separate three-node probe preserved original SQLite bytes and proved worker/child contributions.
- Evidence: Local ignored artifacts/test-audit-ci/parallel-worker/coverage-retention-diagnostic.json, excluded-recreated-databases.json and EXECUTION.md; coverage-probe-dfcc41f6-d097-4c92-9a01-1d47c464fb6c/ retains the nine original/snapshot databases, hash manifest and native contribution proof. No pilot data supplies the final full-gate coverage claim.
- Suggested action: After all writers close, preserve raw databases and any journal state before native reads or reports. Process copies only, use the installed report retention option, and check existence/hash before CoverageData APIs. Do not credit recreated databases or retroactively claim preserved originals. Requalify behavior when the installed version changes.
