# Confine inherited measurement variables in nested verification

**Version 1.0**

- ID: 20261005T171551Z-delivery-efficiency-coordinator-confine-inherited-export-environment
- Date: 2026-10-05T17:15:51Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: measurement evidence and environment confinement
- Status: confirmed by the controlled public command probe
- Observation: The initial opted-in helper supplied a fresh measurement ID to phases, but forwarded an inherited outer measurement pair to metadata commands. Its disabled legacy invocation also forwarded that pair to metadata and phases. Both helper invocations returned status zero; the independent confinement probe failed. Setting a fresh phase pair alone does not establish phase-only behavior when verification runs inside an already opted-in tests phase.
- Evidence: [retained initial confinement probe](../artifacts/delivery-efficiency/rollout/c-initial-incomplete-checkpoint/inherited-pair-probe.json), bound to the initial helper SHA-256; [approved E1 environment boundary](../docs/contracts/measurements-export-v1.md). These are synthetic disposable caller inputs, not owner data or a second scientific memory run.
- Suggested action: Exercise nested public callers with a complete inherited export pair before the full gate. Metadata and disabled collectors must retain their declared behavior; opted-in phases need their own fresh identity. Validate environment observations as well as return status, retain failures, and route product corrections without changing reviewed tests.
