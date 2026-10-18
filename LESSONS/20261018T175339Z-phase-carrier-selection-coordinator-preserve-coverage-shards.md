# Preserve raw coverage shards during report export

**Version 1.0**

- ID: 20261018T175339Z-phase-carrier-selection-coordinator-preserve-coverage-shards
- Date: 2026-10-18T17:53:39.169308+00:00
- Task: PHASE-CARRIER-SELECTION
- Role: coordinator
- Topic: coverage evidence preservation
- Status: confirmed
- Observation: Focused support attempt01 combined Coverage.py 7.16.2 parallel data with `combine --keep`, but subsequent JSON/HTML reporting consumed the original shard during automatic combination. Attempt02 retained a raw snapshot and used `--keep-combined` for each export. Both executed the same 150 passing cases and produced identical native coverage counts. This observation concerns this installed version and command context.
- Evidence: `artifacts/phase-carrier-selection-20261018/Q02/report.md`, `result.json`, `diagnosis-attempt01.md` and attempt02 execution/raw/export pins. Original unavailable shard remains an explicit attempt01 gap; combined data does not replace it.
- Suggested action: For an authorized standalone evidence run, preserve raw bytes before reporting and verify original shard pins after all exports. Do not change installed canonical gates or coverage policy from this lesson.
