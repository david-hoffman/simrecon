# Preflight local protocol capabilities before a long check

**Version 1.0**

- ID: 20261029T001655Z-tsc01-coordinator-protocol-capability-preflight
- Date: 2026-10-29T00:16:55.295901+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: verification environment
- Status: confirmed
- Observation: A native protocol check on unchanged checkpoint7a99cad03773d4831a24ae12edc6bc92f0f79994 passed737cases and failed77 under restricted execution:14local socket denials and63public-caller failures after process inspection was denied and the preservation fixture retained its authentic cache backup/reservation. The host-permitted, source-free affected-case rerun passed all77 in290.63s after checked reversible cache restoration. No tests, runtime, diagnostic harness or gates changed for that repair. These are separate runs; the overlapping five-row retry is not additional unique coverage.
- Evidence: Retained protocol-lane artifacts/test-consolidation/A2-results/checks.json, cache-recovery-preflight.json, cache-recovery-receipt.json, coordinator-affected-check.json/.log and coordinator-post-recheck-health.json. Exact checkpoint/tree and lane paths are linked from the sole task Current state. Recovery verified full original file inventory/inode/mode, current task process/working-directory/open-handle closure and unchanged journal; displaced objects were retained.
- Suggested action: Where scoped protocol tests need local sockets or process visibility, check those capabilities cheaply before the long run and use the authorized host-permitted invocation. Keep the reservation guard; diagnose any retained state, prove writers closed and original identities intact, and preserve displaced evidence before restoring it. This observation grants no broader access, deletion or gate authority.
