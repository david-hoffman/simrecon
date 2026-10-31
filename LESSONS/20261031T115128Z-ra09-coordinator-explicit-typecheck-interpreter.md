# Explicit interpreter restores the narrow diagnostic channel

**Version 1.0**

- ID: 20261031T115128Z-ra09-coordinator-explicit-typecheck-interpreter
- Date: 2026-10-31T11:51:28.985769+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator
- Topic: environment
- Status: confirmed observed diagnostic/packet facts; stated cause limits remain unknown
- Observation: The first blind A2 narrow Pyright command reported a sitecustomize StackSummary.format_frame_summary AttributeError and missing current-environment imports. The same narrow command with --pythonpath .venv/bin/python removed those diagnostics. It exposed ten remaining owned-test type errors, which stayed assigned to A. The original child executable was not captured; its identity and exact cause remain unknown.
- Evidence: artifacts/ra09/roles/A2/logs/pyright-1.log; artifacts/ra09/checks/a2-type-diagnosis-1.log; artifacts/ra09/checks/a2-type-diagnosis-summary-1.json. Current worktree Python3.13.12, Pyright1.1.414.
- Suggested action: For standalone narrow type checks outside uv run, select the current-worktree interpreter explicitly and retain the actual status. Do not treat removal of an environment diagnostic as passing test evidence.
