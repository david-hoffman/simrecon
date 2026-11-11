# Detached Git maintenance races with fixture byte snapshots

**Version 1.0**

- ID: 20261021T182235Z-ci-pr36-pr39-coordinator-git-maintenance
- Date: 2026-10-21T18:22:35Z
- Task: docs/tasks/ci-pr36-pr39-repair-20261021.md
- Role: coordinator
- Topic: fixture process lifecycle
- Status: confirmed
- Observation: macOS CI in PR36 and PR39 observed an empty `.git/objects/maintenance.lock` disappear between complete Git byte snapshots. A local Git 2.54.0 trace showed the setup commit launching `git maintenance run --auto --quiet --detach`. Command-scoped `maintenance.auto=false` prevented that launch in the same disposable probe. The lock difference alone is not a product mutation witness.
- Evidence: [PR36 failing job](https://github.com/david-hoffman/simrecon/actions/runs/39544407143/job/119039197535), [PR39 failing job](https://github.com/david-hoffman/simrecon/actions/runs/39544405128/job/119039192018); ignored `artifacts/ci-pr36-pr39-repair-20261021/git-maintenance-probe/{trace,disabled-trace}.jsonl` retains the two local setup observations.
- Suggested action: disable automatic maintenance in disposable fixture setup commands before taking a complete byte snapshot. Preserve the full assertion rather than excluding changing Git files.
