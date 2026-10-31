# Git inspection can change directory timestamps

**Version 1.0**

- ID: 20261031T141049Z-ra09-coordinator-git-directory-observation
- Date: 2026-10-31T14:10:49.218866+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator
- Topic: environment and preservation proof
- Status: confirmed directory observations; exact temporary-file syscall mechanism not traced
- Observation: C's initial git describe --dirty observation changed the retained verification checkout's .git directory mtime/ctime within its recorded command interval. All namespace entries and regular-file hashes still matched. The corrected describe --tags --always query, with tracked dirty state observed separately, left the three inspected Git-directory metadata records unchanged. Older external Git-directory mtime differences were recorded separately with their causes unknown.
- Evidence: artifacts/ra09/cleanup1/C1/preflight-diagnosis-1.json; author-correction-1/diagnosis-and-corrected-probe.json; author-correction-1/external-pin-differences.json; cleanup1/inventory-support-2/public-delta-ledger-v2.json. Native macOS 27.0.1 arm64, Python 3.13.12.
- Suggested action: Check the side effects of Git queries used during fingerprinting. Keep original observations; route changed proof for fresh review instead of restoring timestamps or bypassing guards.
