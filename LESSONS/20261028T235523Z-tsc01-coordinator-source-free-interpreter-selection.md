# Qualify the interpreter used by source-free type diagnostics

**Version 1.0**

- ID: 20261028T235523Z-tsc01-coordinator-source-free-interpreter-selection
- Date: 2026-10-28T23:55:23.836315+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: diagnostic environment
- Status: confirmed
- Observation: A narrow Pyright invocation through the worktree Python still encountered a source-free startup error and unresolved pytest import when its interpreter search was implicit. The same scoped check with the worktree interpreter explicitly selected and its bin directory first on PATH removed both environment diagnostics, leaving only ten test-variable initialization findings. This establishes the qualified invocation; it does not establish every descendant interpreter or excuse the mandatory blind-author stop. No product source statement was displayed.
- Evidence: Protocols incomplete checkpoint21f3dcb013aa4e40b91112bfac16ebc9090b7548; retained protocols artifacts/test-consolidation/A-results/narrow-types.log and coordinator-type-diagnosis.json/.log. Exact command: .venv/bin/python scripts/source_free_check.py --timeout 120 python -m pyright --pythonpath <worktree>/.venv/bin/python tests/test_verification_output_protection.py (timeout and120 are separate arguments). The task pointer identifies the sole Current state and lane evidence.
- Suggested action: For a needed scoped type diagnostic, select the pinned worktree interpreter explicitly and qualify source-free startup before blind use. Diagnose tool selection separately from test defects; route corrections through the authorized test owner and fresh review. This lesson grants no broader check/edit or gate authority.
