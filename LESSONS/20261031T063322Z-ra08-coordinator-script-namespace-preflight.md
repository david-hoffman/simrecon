# Qualify the public script namespace as well as the installed package

**Version 1.0**

- ID: 20261031T063322Z-ra08-coordinator-script-namespace-preflight
- Date: 2026-10-31T06:33:22.028207+00:00
- Task: [RA08 finite-field objective](../docs/tasks/reference-alignment-ra08.md)
- Role: coordinator
- Topic: blind diagnostic environment
- Status: confirmed
- Observation: The source-free runner imported the installed package but initially omitted the repository root from Python's import path. The public `scripts` namespace was therefore unavailable. This was an environment failure before the intended absent RA08 entry could be observed. Adding the actual worktree root restored the existing public script import, and the source-free channels requalified. The author retained the earlier attempts separately from the actual missing-module baseline.
- Evidence: [Author import-path diagnosis](../artifacts/ra08/roles/A1/import-path-diagnosis-1.log), [corrected qualification](../artifacts/ra08/checks/diagnostics-2/receipt.json), [existing script import](../artifacts/ra08/checks/diagnostics-2/script-import.stdout), [feature-absence baseline](../artifacts/ra08/roles/A1/pytest-baseline-3.log). Locked Python 3.13.12. Corrected runner SHA-256 `69e458954549b31a88a6bdbe226b1f40794665da74848522e54783cd956b0b13`. The sole ledger retains the failed qualification and interpreter-selection charges.
- Suggested action: For a future script-boundary blind packet, qualify one existing public script import through the exact diagnostic entry point before the dependent probe. This is a bounded suggested check, not authority to change project gates or diagnostic behavior.
