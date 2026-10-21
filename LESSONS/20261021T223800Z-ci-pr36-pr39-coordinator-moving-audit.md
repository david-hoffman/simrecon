# An unchanged lock can fail a later live dependency audit

**Version 1.0**

- ID: 20261021T223800Z-ci-pr36-pr39-coordinator-moving-audit
- Date: 2026-10-21T22:38:00+00:00
- Task: docs/tasks/ci-pr36-pr39-repair-20261021.md
- Role: coordinator
- Topic: changing external audit evidence
- Status: confirmed
- Observation: PR39 full-local04 passed its final audit at virtualenv 21.14.7. The later Ubuntu CI job passed all 8,009 tests, native coverage and wheel checks, then its audit reported three additional advisories at the same version. A fresh no-cache local audit reproduced them. Their exact feed/cache transition time is unknown. A targeted 21.14.9 patch preserved the other 26 package records and cleared fresh audits in both worktrees. Earlier passing observations remain historical evidence; they do not waive this newer failure.
- Evidence: [failed Ubuntu job](https://github.com/david-hoffman/simrecon/actions/runs/39682105712/job/119506902681), audit at 2026-10-21T22:29:32Z; ignored `artifacts/ci-pr36-pr39-repair-20261021/full-local04-proof/` in PR39 preserves its earlier local receipt. `dev-dependency-correction02/` in both worktrees records original/final no-cache audits, exact package comparisons, sync and import health. Opened primary advisories: [deletion recovery](https://github.com/advisories/GHSA-43mp-35q3-x3fq), [linked environment directories](https://github.com/advisories/GHSA-cw65-gx24-rc82), [POSIX console launchers](https://github.com/advisories/GHSA-c978-59m8-c77v); each lists 21.14.9 as patched. This supplements `20261021T191849Z-ci-pr36-pr39-coordinator-cheap-audit.md` without changing its historical observations.
- Suggested action: retain cheap audit preflight and the final audit. When a new external finding challenges earlier evidence, diagnose it, apply the narrow authorized dependency correction and repeat exact-candidate full verification and fresh review. Never ignore a vulnerability to reuse an earlier passing gate.
