# Preserve zero-valued finite optimizer diagnostics

**Version 1.0**

- ID: 20261102T030809Z-ra13-coordinator-zero-diagnostic-presence
- Date: 2026-11-02T03:08:09.283638+00:00
- Task: [RA13](../docs/tasks/reference-alignment-ra13.md)
- Role: coordinator
- Topic: test oracle and diagnostic preservation
- Status: confirmed
- Observation: A truthiness assertion rejected an actual refinement status 0 at the declared function-evaluation limit. The finite-procedure contract permits that outcome and requires its diagnostic to remain visible. The same unexposed blind author changed only the local presence assertion; fresh B2 accepted the revised checkpoint. The product remained unchanged.
- Evidence: [RA12 finite refinement](../docs/contracts/reference-alignment-ra12-v1.md), [W7 integration test](../tests/test_raw_sim_workflow.py), revised checkpoint 1b5250d5e41db05d786141f004037afda2432f2f5831c49e37724754f729ae90. Retained local artifacts/ra13/A1-correction-1/named-before.log and focused-after.log record the original test defect and 85 passing cases; artifacts/ra13/B2/final.md records fresh acceptance.
- Suggested action: For optional numeric diagnostics, check presence and preservation explicitly. Interpret each status using its approved contract. Keep finite completion and convergence claims separate.
