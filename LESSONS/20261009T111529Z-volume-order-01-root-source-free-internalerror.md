# Source-free diagnostics must cover pytest internal errors

**Version 1.0**

- ID: 20261009T111529Z-volume-order-01-root-source-free-internalerror
- Date: 2026-10-09T11:15:29.149867+00:00
- Task: [VOLUME-ORDER-01](../docs/tasks/volume-order-transfers.md)
- Role: root
- Topic: source-free-internalerror
- Status: confirmed
- Observation: A reviewer-owned marker audit used iterator truthiness and triggered pytest internalerror source rendering. Blind work stopped and the next verdict came from a fresh B root. An ignored diagnostic renderer then covered normal assertion failures, explicit and implicit exception chains, and internal errors; five native control processes returned 0,1,1,3,0 without source snippets.
- Evidence: B3 incomplete attempt and root source-free diagnostic proof b-public-diagnostics-proof.json, independent support-root-diagnostics-audit-01.json, and fresh accepted B4 are preserved in artifacts/axial-order-execution/. The tracked public test checkpoint stayed unchanged during diagnostic repair.
- Suggested action: Probe the actual subprocess diagnostic renderer for internal failures before blind checks; context clearing does not restore blindness. This observation grants no test/gate edit authority.
