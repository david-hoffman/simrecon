# Accepted public scenarios can leave the runtime coverage gate unmet

**Version 1.0**

- ID: 20261001T161038Z-mrc-conversion-coordinator-scenario-coverage-gap
- Date: 2026-10-01T16:10:38.869321+00:00
- Task: MRC-CONVERSION-01
- Role: coordinator observing initial C evidence
- Topic: scenario planning and measured coverage
- Status: confirmed
- Observation: the accepted 26 public scenarios and 10 infrastructure tests all pass, while the exact initial C candidate measures 358/376 statements and 88/104 branches (zero exclusions). B acceptance establishes test quality for the identified scenarios; it does not establish implementation coverage completeness. The missing contexts are mainly documented validation/storage/source-change boundaries. A native-host conditional also needs honest support-scope/simplification diagnosis.
- Evidence: candidate `9bae104f01c4d7f37cb47115092b1f704b128920`; reviewed tests `0db9ef102f7c3328b7b4aba871e4ddbf3e9cc8e9`; `UV_CACHE_DIR=/private/tmp/mrc-c-uv-cache make verify UV=/Users/davidhoffman/.local/bin/uv` on macOS arm64 / CPython 3.13.12 / uv 0.12.19 exits 2 at unchanged coverage gate. [C evidence](../artifacts/mrc-conversion/roles/c-initial-report.md) and [native report](../artifacts/coverage/coverage.json).
- Suggested action: inventory distinct public boundary contexts before requesting the scenario exception; route evidenced additional contexts through owner-approved intake and fresh blind A/B rather than weakening checks, manufacturing failures or passing implementation coverage maps to blind roles. This lesson grants no new scenario, round, repair or spending authority.
