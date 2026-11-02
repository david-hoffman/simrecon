# A Pyright entry point does not identify the analysis interpreter

**Version 1.0**

- ID: 20261030T073110Z-ra05-coordinator-scoped-pyright-interpreter
- Date: 2026-10-30T07:31:10Z
- Task: [RA05](../docs/tasks/reference-alignment-ra05.md)
- Role: coordinator
- Topic: Blind test preparation
- Status: confirmed
- Observation: The owned Pyright executable, called on only the two RA05 test files, initially could not resolve NumPy/pytest and produced six inconclusive diagnostics. Adding --pythonpath pointing to this worktree's locked .venv/bin/python made the same scoped analysis pass. No dependency, type-check configuration or gate was changed for that repair.
- Evidence: [Project environment](../docs/operations/environment.md). Retained local artifacts/ra05/A4/pyright-v1.json and pyright-v2.json; the A4 report separates this tooling failure from the 22 earlier test-preparation defects. Python3.13.12, Pyright1.1.414.
- Suggested action: Name the locked interpreter in scoped author/reviewer type checks. Keep blind diagnostics confined to permitted test files and source-free messages. Diagnose interpreter selection before treating missing-import output as a source defect. This lesson supplies no new authority or gate change.
