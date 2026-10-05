# Same Python version can conceal an isolated-fixture loader failure

**Version 1.0**

- ID: 20261005T181131Z-delivery-efficiency-coordinator-managed-interpreter-fixtures
- Date: 2026-10-05T18:11:31Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: environment identity and test-fixture portability
- Status: confirmed
- Observation: Ten preflight cases passed with local Conda Python 3.13.12 but failed setup in both macOS CI attempts using uv-managed CPython 3.13.12/aarch64. The copied isolated executable could not load `@rpath/libpython3.13.dylib`. A controlled probe with CI's provider reproduced status -6 for copies and status 0 for symlinks; identical version text did not establish equivalent environment health.
- Evidence: [PR CI](https://github.com/david-hoffman/simrecon/actions/runs/37352433391), [push CI](https://github.com/david-hoffman/simrecon/actions/runs/37352425164); retained [managed-provider probe](../artifacts/delivery-efficiency/rollout/env2-managed-diagnosis.json) and [ENV2 report](../artifacts/delivery-efficiency/rollout/env2-report.md). `venv.EnvBuilder(with_pip=False, symlinks=...)` followed by the actual isolated interpreter's `sysconfig` probe distinguished the two results.
- Suggested action: Use symlinked isolated interpreter creation for this POSIX fixture and verify health with the actual interpreter provider before expensive dependent tests. Keep version, provider/executable and dependency identity distinct; retain failures and rerun affected gates after repair.
