# Qualify nested pytest outside the repository

**Version 1.0**

- ID: 20261021T052805Z-test-audit-coordinator-collection-path-portability
- Date: 2026-10-21T05:28:05Z
- Task: [test audit and Ubuntu CI](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: test diagnostic portability
- Status: confirmed
- Observation: policy qualification with temporary suites inside the repository passed, but the exact full gate failed two collection-error banner assertions with external temporary suites. Pytest reported the external initial-path module as `test_case.py`, without the assumed `suite/` prefix. Both native failure statuses, error counts and exception sentinels were correct. An unchanged external-path reproduction confirmed the cause; no product defect was established.
- Evidence: exact candidate `2f2fb4e860b61c42d19fc635e7c6da03be729868`; preserved [failed gate](../artifacts/test-audit-ci/full-gate-round1-failed/preservation-receipt.json), its original test log and same-run measurement; [unchanged external reproduction](../artifacts/test-audit-ci/parallel-worker/nested-policy-diagnostic-865e084e-a519-449f-8312-9d0129ccfab4/observed-diagnostics.json). The run completed 8,782 cases in 528.82 seconds, with two assertion failures; it is not passing full verification. Fresh Astra advice distinguished native node-ID normalization from unsupported long-title truncation.
- Suggested action: require the exact collected basename and diagnostic semantics while permitting native relative-directory forms. Qualify nested execution with external temporary paths before repeating the canonical gate. Preserve failed attempts and raw evidence; focused success cannot replace exact-candidate full verification or fresh independent review.
