# Quiesce each disposable Git builder before snapshotting

**Version 1.0**

- ID: 20261022T045737Z-stack-maintenance-bounded-worker-quiesce-repository-builders
- Date: 2026-10-22T04:57:37.338201+00:00
- Task: [Stack maintenance follow-up](../docs/tasks/stack-ci-maintenance-race-20261022.md)
- Role: bounded worker
- Topic: disposable repository setup
- Status: confirmed
- Observation: The public-caller and output-protection builders still committed without a repository-local maintenance override after a different fixture had been repaired. The reported CI failures named a disappearing `.git/objects/maintenance.lock`; complete metadata observers require their own fixture producers to be quiescent. A later passing run alone does not remove this reachable race. No scientific defect follows from those fixture failures.
- Evidence: PR39 baseline `cca7314b87e3c8a9a7479f4530e26ab3eaa5a461`; macOS CI run `39701681543`; prior evidence-output CI run `39701509376`. Setup and snapshot origins are commits `62429b4984aa6b43e82fbd86f8614ebf5bdac07b` and `4ec8609f25aec530a5391d679e9381432f6854e4`. Targeted source-free checks and isolated global-maintenance configuration evidence are retained under `artifacts/stack-rebase-20261022/maintenance-race-followup/worker-checkpoint01/`; final results and candidate identities stay outside tracked bytes.
- Suggested action: Set the local maintenance override before the first commit in every affected owned disposable builder, then challenge it with global maintenance enabled while retaining complete snapshots and their assertions.
