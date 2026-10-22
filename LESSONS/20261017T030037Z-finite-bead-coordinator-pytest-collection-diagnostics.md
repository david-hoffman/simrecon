# Pytest collection diagnostics need their own source-free proof

**Version 1.0**

- ID: 20261017T030037Z-finite-bead-coordinator-pytest-collection-diagnostics
- Date: 2026-10-17T03:00:37.812880+00:00
- Task: docs/tasks/finite-bead-compensation.md
- Role: coordinator
- Topic: blind diagnostic infrastructure
- Status: confirmed
- Observation: An owned draft SyntaxError caused pytest9.1.1 collection to display pytest/importlib source despite the wrapper's --tb=line, --no-showlocals and --assert=plain options. The blind author stopped. No scientific implementation source appeared. The enclosing shell read the log after pytest and masked the exact child integer; that integer remains unknown and the collection failure is retained.
- Evidence: artifacts/finite-bead-compensation-20261016/A01/02-oracle-initial.log, A01/report.md and infrastructure-correction01.json; Python3.13.12/pytest9.1.1 in the locked macOS worktree. scripts/source_free_check.py at intake2a5c9af configured the stated options.
- Suggested action: Prove collection SyntaxError/import failure formatting through the actual wrapper, preserving type/message/location/status and suppressing source; obtain fresh scoped infrastructure review before fresh blind work. Preserve child status explicitly when logging. This observation grants no gate or file-ownership change.
