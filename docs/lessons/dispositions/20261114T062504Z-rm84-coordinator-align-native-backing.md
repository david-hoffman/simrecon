# RM84 comparison environments have matching native backing

**Version 1.0**

- Record kind: disposition
- ID: 20261114T062504Z-rm84-coordinator-align-native-backing
- Date: 2026-11-14T06:25:04.630672+00:00
- Task / deciding role: [RM84](../../tasks/reconstruction-memory.md), coordinator
- Lesson IDs: 20261114T062504Z-rm84-coordinator-native-backing-comparison
- Finding IDs / scope: RM84-F003, the native dependency backing mismatch between the two active RM84-2 measurement environments; excludes the precise cause of historical residency variation and all scientific/resource acceptance claims.
- State: resolved
- Completion conditions: Both active environments have separate correct prefixes/editable origins, matching pinned versions and native file inventories; all164 native files share device/inode identities; replacement binary content matches former main; post-setup narrow observer checks pass. Observed conditions are satisfied.
- Basis / evidence: `artifacts/rm84/rm84-2/setup-aligned/setup-report.md`, `native-backing-and-hashes.json` and coordinator `evidence/initial-dry-run.json`. All164 hashes/inodes match, all29 distribution versions match and15 narrow checks pass. No resource reduction is inferred; formal measurements and independent candidate review remain required.
- Work links: [Authorized RM84 task](../../tasks/reconstruction-memory.md). No new external issue is needed for this completed local setup correction.
- Relationships: none; RM84-F001 cloud role readiness and RM84-F002 diagnostic isolation have different mechanisms and remain separately handled.
- Revisit: Coordinator rechecks after any environment reinstall/replacement or native dependency identity change before further matched measurements.
