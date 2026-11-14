# Matching dependency versions do not establish shared native backing

**Version 1.0**

- ID: 20261114T062504Z-rm84-coordinator-native-backing-comparison
- Date: 2026-11-14T06:25:04.630672+00:00
- Task: [RM84](../tasks/reconstruction-memory.md)
- Role: coordinator
- Topic: memory measurement controls
- Status: confirmed
- Observation: Two isolated environments used the same lock, Python and 29 installed distribution versions, yet all 164 native library paths had different device/inode identities. A shared uv cache with multiple cached layouts did not itself establish shared backing. After retaining the inactive main environment and creating its replacement through ordinary locked hardlink synchronization, all 164 active native paths shared backing with the baseline; all 164 replacement binaries also matched the former environment's SHA256 values. Matching backing removes that particular setup difference; it does not prove equal resident memory or explain the entire earlier approximately13MB residency offset.
- Evidence: Local durable artifacts `artifacts/rm84/rm84-2/setup-baseline/setup-report.md`, `setup-aligned/setup-report.md` and their native inventory/hash manifests; `artifacts/rm84/roles/import-memory-diagnosis.md` retains the earlier attributed limits. Setup used pinned uv0.12.19/Python3.13.12 on the identified Debian13 host; no reconstruction ran during alignment. The accepted test-only source checkpoint was `ddd05c890746dc3ddbfd09a6fe7599bf815b5461`.
- Suggested action: For this matched memory campaign, preserve separate worktree environments and verify actual library backing, import origins and immutable inputs before and after measurements. Retain observed repeat variation and do not subtract precall high-water to claim an isolated workflow peak. No general installation-policy change or automatic repair is implied.
