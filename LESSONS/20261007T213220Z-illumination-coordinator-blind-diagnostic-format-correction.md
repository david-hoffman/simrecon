# Protect blind startup and scratch diagnostics

**Version 1.0**

- ID: 20261007T213220Z-illumination-coordinator-blind-diagnostic-format-correction
- Date: 2026-10-07T21:32:20.871325+00:00
- Task: ILLUMINATION-01; [task pointer](../docs/tasks/illumination-estimation.md).
- Role: coordinator.
- Topic: blind-review diagnostic setup.
- Status: confirmed.
- Observation: read-only pytest startup failed when default file-descriptor capture required temporary files. The next fresh reviewer left an allowed scratch file handle open and an unraisable ResourceWarning escaped that channel. Both stopped with no accepted checkpoint and no SIMrecon implementation exposure. This supersedes the nonconforming field layout in `20261007T213156Z-illumination-coordinator-blind-startup-diagnostics.md`; its observations and attempt accounting are retained.
- Evidence: ignored local `artifacts/illumination-execution/B-final.txt`, `B2-final.txt`, and `execution-record.json` retain both attempts. Python3.13.12 protected `blind_pytest.py` selected in-memory sys capture/no cache. Controlled denied-temp collection passed; deliberately unclosed-file and startup-failure probes emitted category/message/location with status3 and no source snippets. Closed-read probe returned0.
- Suggested action: protect startup, warnings, unraisable and scratch/subprocess channels before blind work; use closed reads. Keep incomplete attempts and launch a fresh required reviewer. Missing-API baseline is product absence, not oracle proof. The one-off ignored helper changes no shipped oracle/gate/coverage configuration and proves no universal containment.
