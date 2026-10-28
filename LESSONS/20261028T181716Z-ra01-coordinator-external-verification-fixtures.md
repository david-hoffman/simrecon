# Keep verification fixture roots outside the worktree

**Version 1.0**

- ID: 20261028T181716Z-ra01-coordinator-external-verification-fixtures
- Date: 2026-10-28T18:17:16.356185+00:00
- Task: [RA01](../docs/tasks/RA01.md)
- Role: coordinator
- Topic: verification environment
- Status: confirmed
- Observation: RA01's first full check used a temporary root inside the worktree. The verifier's recursive evidence scan reached an intentional fixture file-link cycle and raised ELOOP. Its test phase also failed with the reader suite's explicit SIMRECON_JAVA setting absent. All 19 cached failing cases passed in 13.13 seconds with an external temporary root and the retained Java executable selected explicitly; this is environment-repair evidence, not a retroactive pass of the first run.
- Evidence: scripts/verify.py evidence_files; tests/test_shared_node_baseline_infrastructure.py test_real_local_verifier_output_failure_preserves_marker and test_authentic_cached_reader_with_real_selected_java; local RA01 Current state links the failed receipt, original cached test IDs, preserved native evidence and focused-environment-recheck.log. The outer verifier failed before persisting test stdout, which remains unavailable. No runtime/test/gate change.
- Suggested action: Declare an external task-owned temporary root and explicit retained SIMRECON_JAVA before full checks. Inventory retained incoming links before trimming generated fixtures; preserve referenced roots at their original paths.
