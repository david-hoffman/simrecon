# External protocol evidence does not prepare the fixed reader lock parent

**Version 1.0**

- ID: 20261103T020523Z-ce03-coordinator-external-protocol-lock-parent
- Date: 2026-11-03T02:05:23.616951+00:00
- Task: CE03, [task pointer](../docs/tasks/c-equivalence-optical-transfer.md)
- Role: coordinator
- Topic: verification environment
- Status: confirmed
- Observation: A fresh worktree using external SIMRECON_PROTOCOLS_EVIDENCE lacked the ignored fixed reader-reservation parent. All15 affected tests failed at lock.mkdir before cache rename; the other1479 cases passed. ReaderReservation creates its RUN under the override but keeps its exclusive lock under artifacts/baseline-compatibility-20261013/A09. Creating that empty parent, without touching the lock/cache or any tracked code, made all15 unchanged regressions pass in37.84s. The predecessor's successful environment record already preserved this parent.
- Evidence: tests/shared_node_baseline_public_callers_fixture.py:26,29,332,361; /private/tmp/simrecon-ce03-evidence-20261102/full-verify-1/environment-diagnosis.json and original failed receipt/logs; full-verify-2/focused-reader-completion.json and focused-reader-regressions.log. Candidate/runtime/tests and all26 optional fingerprints stayed unchanged during diagnosis and repair. Full verification remains a separate required check.
- Suggested action: Before local verification with external protocol evidence, prepare the ignored fixed reservation parent with the existing mkdir command. Never create/remove a live reservation lock or bypass cache preservation. This records environment preparation, not permission to change fixture/gate behavior or waive a failed run.
