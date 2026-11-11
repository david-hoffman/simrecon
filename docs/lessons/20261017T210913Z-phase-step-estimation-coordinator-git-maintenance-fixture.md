# Detached Git maintenance can race a byte-preservation fixture

**Version 1.0**

- ID: 20261017T210913Z-phase-step-estimation-coordinator-git-maintenance-fixture
- Date: 2026-10-17T21:09:13.583206+00:00
- Task: phase-step-estimation
- Role: coordinator
- Topic: test-fixture isolation
- Status: confirmed
- Observation: macOS15 CI run39065744455/attempt1 failed two directory-redirection preservation cases because an empty .git/objects/maintenance.lock existed in the initial snapshot and disappeared afterward; all32 other Git entries matched. Fresh blind A08 traced the unchanged real fixture on local Git2.54.0 and observed its commit launch `git maintenance run --auto --quiet --detach`. Repository-local maintenance.auto=false before add/commit removed that child launch, and both unchanged/corrected focused14-row suites passed. Exact CI Git2.55.0 lock timing was not reproduced. The mechanism supports a fixture race and establishes no scientific product defect or universal absence of concurrent writers.
- Evidence: artifacts/phase-step-estimation-20261016/ci/failure-diagnosis01/failed-job-log.txt and original archive-downloads.json; artifacts/infrastructure-supplement-A08/baseline-git-trace.jsonl, candidate-git-trace.jsonl and handoff.md; official opened https://git-scm.com/docs/git-config . A08 raw final SHA2567566278460eac6163745e96de38d5442da7a5592e8f63aa6a3d068d6f51394d4. Fresh independent B review and exact-candidate gates remain required.
- Suggested action: Before measuring all Git bytes in a caller-owned synthetic repository, make its own setup quiescent through documented repository/command-local configuration. Preserve exact byte assertions, including locks; do not discard the failing run or infer readiness from a later rerun. This lesson grants no global Git configuration, oracle, runtime, gate or policy edit authority.
