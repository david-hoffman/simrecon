# Qualify diagnostics for the selected interpreter

**Version 1.0**

- ID: 20261029T140143Z-TSC01-coordinator-alternate-interpreter-diagnostics
- Date: 2026-10-29T14:01:43.208842Z
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator, recording verified author/reviewer observations
- Topic: diagnostic startup
- Status: confirmed for the observed environment
- Observation: The locked Python 3.13.12 interpreter was qualified, while the selected system Python 3.9.6 could not load the inherited diagnostic helper because StackSummary.format_frame_summary was absent. A nonblind coordinator separately ran the unchanged compatibility case in the ordinary verification environment and inspected its original output. That passing case did not repair or qualify the older diagnostic environment.
- Evidence: R6 protocols A 015-system-qualification and the separate coordinator-system-entry receipt; the fresh B2 verdict accepts the ordinary case as distinct evidence. These are bound by the accepted checkpoint map. Local checkpoint pointer: `artifacts/test-consolidation/R6-accepted-checkpoints.json`; exact source evidence is indexed locally in `artifacts/test-consolidation/R6-lessons-evidence.json`.
- Suggested action: Qualify each actual interpreter before promising a dependent blind check. Keep failed diagnostic qualification and ordinary verification evidence separate; use the existing role routing rather than weakening the test or relabeling the environment. This lesson grants no additional edit, gate or execution authority.
