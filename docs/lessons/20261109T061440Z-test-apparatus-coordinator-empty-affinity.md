# Two workers can still execute one serial group

**Version 1.0**

- ID: 20261109T061440Z-test-apparatus-coordinator-empty-affinity
- Date: 2026-11-09T06:14:40.149434+00:00
- Task: [Test apparatus optimization](../tasks/test-apparatus-optimization.md)
- Role: coordinator, incorporating independent nonblind infrastructure discovery
- Topic: verification scheduling
- Status: confirmed configuration; elapsed cost unmeasured
- Observation: baseline edcf53b configures two loadgroup workers but an empty
  PARALLEL_GROUPS mapping assigns every test to serial-rest. Worker count alone
  does not establish concurrent test execution.
- Evidence: [Infrastructure report](../reports/test-apparatus-audit/infrastructure-discovery.md),
  baseline Makefile and src/simrecon/_pytest_policy.py. No suite run was completed
  because pinned reader downloads were denied by the environment proxy.
- Suggested action: measure the exact baseline, then qualify isolated whole-file
  groups while retaining reader-cache affinity, native subprocess coverage,
  omission guards and same-run M25 evidence. This is no independent edit approval.
