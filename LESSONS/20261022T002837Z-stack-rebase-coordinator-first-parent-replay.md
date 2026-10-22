# Exclude duplicate side-branch history when restacking

**Version 1.0**

- ID: 20261022T002837Z-stack-rebase-coordinator-first-parent-replay
- Date: 2026-10-22T00:28:37.740797+00:00
- Task: [stack-rebase-20261022](../docs/tasks/stack-rebase-20261022.md)
- Role: coordinator
- Topic: Git replay boundaries
- Status: confirmed
- Observation: PR39's broad old-base-to-head graph range included 17 upstream side-branch commits in addition to its own changes. Its integration merge had exactly its first parent's tree; three later repair commits matched the upstream repairs by stable patch ID and seven file contents. Replaying only its seven original own commits onto the repaired predecessor reproduced its complete original final tree.
- Evidence: ignored `artifacts/stack-rebase-20261022/candidate-map-worker-checkpoint.json`, `worker-command-log.jsonl` and `worker-summary.json`; original ancestry merge `79c045da70820d217c06ecf1aa0c71d5a3e4304a`; Git 2.54.0. The map retains exact old/new commits, patch IDs, replay ranges and the PR39 tree-equality assertion.
- Suggested action: inspect first-parent ownership, side-branch ancestry and exact tree/patch equivalence before selecting replay boundaries. Do not infer duplicate commits or safe omission from commit subjects alone.
