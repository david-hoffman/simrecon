# Check a diagnosed dependency audit before another expensive full gate

**Version 1.0**

- ID: 20261021T191849Z-ci-pr36-pr39-coordinator-cheap-audit
- Date: 2026-10-21T19:18:49.070149+00:00
- Task: docs/tasks/ci-pr36-pr39-repair-20261021.md
- Role: coordinator
- Topic: dependency maintenance preflight
- Status: confirmed
- Observation: both full-local02 runs passed their complete tests, native coverage and wheel checks, then failed the final locked audit on four virtualenv 21.14.1 advisories. A targeted development-only 21.14.7 update preserved every other package record and cleared the same audit. The earlier full gates remain failed; their test results alone authorize no submission.
- Evidence: ignored `artifacts/ci-pr36-pr39-repair-20261021/failed-full-local02-native/` retains both native failed receipts and audit output; `dev-dependency-correction/` retains the package-roster comparison, locked install/tool health and clean audit. [Minimum patched release advisory](https://github.com/advisories/GHSA-vxj4-q4g9-crj7), opened October 21, 2026.
- Suggested action: after a diagnosed development dependency correction, run the existing cheap locked audit before another expensive full gate. Keep the canonical full verification and its final audit unchanged.
