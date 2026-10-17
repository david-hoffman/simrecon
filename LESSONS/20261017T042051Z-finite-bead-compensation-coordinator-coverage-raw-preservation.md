# Native report export can consume kept coverage inputs

**Version 1.0**

- ID: 20261017T042051Z-finite-bead-compensation-coordinator-coverage-raw-preservation
- Date: 2026-10-17T04:20:51.484603+00:00
- Task: [Finite-bead compensation](../docs/tasks/finite-bead-compensation.md)
- Role: coordinator
- Topic: measurement evidence preservation
- Status: confirmed
- Observation: With installed Coverage.py 7.16.2, `coverage combine --keep` preserved parallel raw inputs, but the following CLI `coverage json` automatically combined and removed them. All three child commands returned zero and 259 focused tests passed; the outer preservation assertion then failed. The original parallel input and its pre-export fingerprint were unavailable. The retained combined database supported a same-run API JSON export without changing raw bytes; native report contents matched apart from the report timestamp. Source and Git identities stayed unchanged. This was a measurement-observer defect, not a product failure or full-gate result.
- Evidence: Local retained `artifacts/finite-bead-compensation-20261016/focused-product-coverage01/summary.json`, same-run CLI/API JSON and combined SQLite; installed Coverage.py CLI report implementation. The diagnostic measured a focused test subset under the configured owned runtime/delivery scope and is not global acceptance evidence.
- Suggested action: For another authorized CLI report export with this version, pass `--keep-combined` and fingerprint all raw inputs before and after export. Preserve missing evidence as a gap. A report-only correction does not justify rerunning science or declaring the lost raw input retained.
