# Lexical path normalization can select another script

**Version 1.0**

- ID: 20261018T011644Z-phase-observable-subspace-coordinator-script-path-identity
- Date: 2026-10-18T01:16:44.898867+00:00
- Task: [observable-subspace phase estimation](../docs/tasks/observable-volume-phase-estimation.md)
- Role: coordinator
- Topic: conventional diagnostic entry compatibility
- Status: confirmed
- Observation: H13 compared the same Python 3.13.12 interpreter with native and wrapped script entries. For a relative symlink `link -> other/inner`, native `link/../entry.py` selected `other/entry.py`; the wrapper normalized the path before opening it and selected `entry.py` instead. Normalization also converted invalid trailing-slash or missing-parent paths from native load status 2 into execution status 0. This is observed selected-file and status divergence, not a claimed sandbox boundary.
- Evidence: [H13 full report](../artifacts/phase-observable-subspace-20261018/H13/fullfinal-verbatim.txt), SHA256 `c390d7c9e619a4b9e1766955913413137f640a50aa77ac5fca50cb57f8a4decf`; [retained archive and limits](../artifacts/phase-observable-subspace-20261018/H13/retention01.json). Exact native/wrapped argument arrays, synthetic files, statuses and streams are retained in the archive. macOS arm64, managed Python 3.13.12; no scientific imports.
- Suggested action: Preserve the caller's script argument and actual filesystem traversal separately from display/import paths. Compare lexical paths, invalid components and a symlink-parent case with the same native interpreter. Obtain fresh independent review of the corrected helper before blind use; this lesson supplies no approval.
