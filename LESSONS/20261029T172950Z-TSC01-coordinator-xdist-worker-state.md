# Qualify the worker's actual grouping options

**Version 1.0**

- ID: 20261029T172950Z-TSC01-coordinator-xdist-worker-state
- Date: 2026-10-29T17:29:50.374691+00:00
- Task: [TSC01](../docs/tasks/test-suite-consolidation.md)
- Role: coordinator
- Topic: parallel test runner
- Status: confirmed for pytest-xdist 3.8.0, execnet 2.1.2 and pytest 9.1.1
- Observation: With loadgroup selected, xdist resets a worker's dist option to no while preserving its loadgroup flag. Testing dist alone therefore failed to assign the intended groups. The qualified hook uses actual worker state before xdist adds node-name suffixes. Other modes remain unchanged. Both full worker catalogs subsequently matched the independent serial catalog; the controlled collection stop was incomplete execution, not a full-suite pass.
- Evidence: Source candidate 660ff685c773c34acd5c0298e929cf96ce7315ea; [qualified policy](../src/simrecon/_pytest_policy.py), [original qualification ledger](../artifacts/test-consolidation/R7-parallel/qualification/worker-20261029/qualification-ledger.json), and [independent bounded review](../artifacts/test-consolidation/R7-parallel/review/independent-20261029/REVIEW.md). Review verdict SHA-256 be0e82dcc9ad5e2b46227dc03f07af78d1f83c57123e7917e9269810b6643270. The actual two-worker command used -n 2 --dist=loadgroup --max-worker-restart=0 on Python 3.13.12.
- Suggested action: Requalify actual worker options, hook ordering and native node identities when changing the runner or grouping policy. A serial collect-only listing does not establish distributed execution or worker state. This finding grants no new editing authority.
