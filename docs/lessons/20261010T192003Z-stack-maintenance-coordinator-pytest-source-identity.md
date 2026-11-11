# Resolve pytest failure paths against the invocation directory

**Version 1.0**

- ID: 20261010T192003Z-stack-maintenance-coordinator-pytest-source-identity
- Date: 2026-10-10T19:20:03Z
- Task: STACK-MAINTENANCE-20261010, PR #21 maintenance
- Role: coordinator, recording the bounded worker's reproduced finding
- Topic: diagnostic test portability
- Status: confirmed for pytest 9.1.1 and Python 3.13.12 on macOS arm64
- Observation: pytest can render a failed test's file path relative to its invocation directory. An absolute-path substring assertion rejected valid diagnostic output after the checkout moved. The exception message, exit status and source identity remained present.
- Evidence: baseline commit `252c6a742639ed03c1ed84be60203214f97109c0`; `tests/test_source_free_check.py`, especially the nested-pytest diagnostic and the added real CLI cases from two invocation directories. The unchanged focused suite produced 37 passes and the pathname assertion failure; the corrected focused suite produced 44 passes. Positive relative/absolute examples and same-basename, different-directory rejection examples preserve the full file-identity obligation.
- Suggested action: resolve the reported node-ID filename against the actual invocation directory and compare the full resolved path. Keep exception, status, location and source-suppression assertions. Do not accept a basename alone.
