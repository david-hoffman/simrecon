# Unavailable-Git fixtures need a temporary root outside a real repository

**Version 1.0**

- ID: 20261102T175152Z-ce01-coordinator-git-fixture-temp-root
- Date: 2026-11-02T17:51:52.871607+00:00
- Task: [CE01](../tasks/c-equivalence-reset.md)
- Role: coordinator, confirming bounded-worker evidence
- Topic: fixture environment
- Status: confirmed
- Observation: Two unchanged unavailable-identity tests failed when their generated repositories lived below this checkout. After their synthetic `.git/HEAD` was removed, Git discovered the real ancestor checkout. Both tests passed with temporary roots outside it; the complete 107-case measurement-export file also passed there. This diagnoses those failures, not every possible fixture failure.
- Evidence: [bounded results](../../artifacts/c-equivalence-reset/asd-worker-results.json), `asd-bounded-checks/measurement-environment-diagnosis.json`, `receipt-environment-diagnosis.json`, and the qualified external measurement/receipt check records. Python 3.13.12 and the unchanged locked tests were used. Original failures remain recorded.
- Suggested action: Use an external pytest temporary root for checks whose contract requires unavailable Git identity. Record the selected uv executable and current-worktree interpreter explicitly. This observation grants no test or gate changes.
