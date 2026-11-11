# Helper identifiers can also name diagnostic fields

**Version 1.0**

- ID: 20261111T013821Z-readability-04-coordinator-helper-payload-collision
- Date: 2026-11-11T01:38:21.202488+00:00
- Task: [Readability Task 04](../tasks/readability-stack.md#task-04-contract-and-evidence-pointer)
- Role: coordinator observing restricted C
- Topic: rename preservation
- Status: confirmed
- Observation: C caught a mechanical helper rename also changing the `correlation` event keyword and restored that field before verification. The final preservation comparison keeps keyword names, constants, arguments, fields and locals exact; only approved module-bound helper definitions/imports/references are normalized.
- Evidence: Task 04 `artifacts/readability-04/c-report.md`, `c-rename-map.json` and `c-preservation-check.py`/`c-preservation.json` in the retained task worktree; baseline `d3bbef6c8cac8dd528198a1fdb84b0b59c0d44d8`. The checker passed for all 27 source files. This records a corrected editing mistake, not an observed product regression or a new scientific oracle.
- Suggested action: For subsequent authorized renames, inspect keyword/record payloads separately from symbol references and keep them outside identifier normalization. A matching token alone does not establish the same binding.
