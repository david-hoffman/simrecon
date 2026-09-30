# A controlled harness accepted an invalid native option combination

**Version 1.0**

- ID: 20260930T201435Z-setup-coordinator-native-boundary-compatibility
- Date: 2026-09-30T20:14:35.116167+00:00
- Task: SETUP-DOCTOR in [setup plan](../docs/tasks/setup-plan.md)
- Role: setup coordinator observing the required live demonstration
- Topic: external command compatibility
- Status: confirmed
- Observation: The controlled process tests, full local gate, fresh D, and both CI platforms passed the initial wrapper. Its real default invocation then exited 2 before a model session because native Codex rejects combining `--sandbox` with `--approve-for-me`. The real read-only check invocation succeeded. Passing a controlled external executable did not establish compatibility with the installed native command parser.
- Evidence: [native demonstration](../docs/setup/evidence/doctor-initial.json) and [initial submission receipt](../docs/setup/evidence/submission-initial.json), candidate `9c11c1164f6bb1c0aecf90f474d38bc62a4c5598`, Codex 0.155.0-alpha.16.4. Public command `uv run --locked delivery doctor` returned native argument error 2. No instruction change is implied by this product/test finding.
- Suggested action: Refine the existing option oracle through fresh A/B and use the allocated C repair; repeat real default/check demonstrations after the exact-candidate gate. Preserve the failed demonstration and earlier green results. Existing real-entry-point and failure-routing rules already cover this case; do not replace them with a controller or weaken readiness.
