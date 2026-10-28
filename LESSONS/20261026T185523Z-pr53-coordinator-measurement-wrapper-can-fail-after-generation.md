# A resource wrapper failed after sealing valid generation

**Version 1.0**

- ID: 20261026T185523Z-pr53-coordinator-measurement-wrapper-can-fail-after-generation
- Date: 2026-10-26T18:55:23.935761+00:00
- Task: [FULL-NOISY-SIMULATION](../docs/tasks/full-noisy-simulation.md)
- Role: coordinator
- Topic: measurement tooling
- Status: confirmed
- Observation: The first small generation sealed 46 valid files, then its restricted native-time resource query failed. Wrapper exit was 1; direct driver exit and peak resident memory were not observed. After a bounded measurement-context smoke passed, a fixed-input repeat in new output roots returned 0 and all 46 files were byte-identical. This was one noise realization, not an independent trial.
- Evidence: [Resources and retained attempts](../docs/studies/full-noisy-study-2026-10-26/README.md#resources-and-retained-attempts) and [resource observations](../docs/studies/full-noisy-study-2026-10-26/evidence/resources.json); actual trial source `1c209a4769c0caab0fb173287efbcac952ed01b1` on macOS 27.0.1, native time resource fields. Original artifacts and the failed observation remain local.
- Suggested action: Probe the exact measurement context cheaply before a long run. Keep scientific completion, wrapper status and missing resource fields distinct; retain original evidence and use a new output root for a diagnosed fixed-input repeat. Do not invent a missing worker exit or memory value.
