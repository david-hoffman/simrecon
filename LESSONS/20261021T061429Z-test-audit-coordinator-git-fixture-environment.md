# Isolate Git fixture maintenance and discovery

**Version 1.0**

- ID: 20261021T061429Z-test-audit-coordinator-git-fixture-environment
- Date: 2026-10-21T06:14:29.141301+00:00
- Task: [test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: test environment
- Status: confirmed
- Observation: Ubuntu Git 2.55 detached maintenance removed its own lock between metadata snapshots. Repository-local maintenance.auto=false before the first fixture commit suppresses that launcher; isolated global true settings still yield local false. A separate standalone unavailable-Git check used a basetemp inside the real checkout, so deleting its fixture HEAD caused Git to select the enclosing repository instead of failing identity discovery.
- Evidence: Failed Ubuntu run39550943696 original artifact; preservation-fixture-correction/measurement-file-git-trace2.jsonl records171commit sessions with local false and no maintenance child. Its later unavailable-Git failure records the selected parent repository. Fresh ubuntu_git_maintenance_advisor and measurement_missing_git_advisor diagnosed these distinct environment causes.
- Suggested action: Disable automatic maintenance only in disposable fixture repositories, retain metadata equality, and place tests that deliberately destroy Git identity outside any enclosing repository. Preserve failed runs and recheck unchanged tests after environment repair; no product-red claim follows from either setup defect.
