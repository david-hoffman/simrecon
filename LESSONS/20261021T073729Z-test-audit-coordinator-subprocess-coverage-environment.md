# Preserve fixture-owned coverage namespaces in diagnostics

**Version 1.0**

- ID: 20261021T073729Z-test-audit-coordinator-subprocess-coverage-environment
- Date: 2026-10-21T07:37:29Z
- Task: [Test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: diagnostic environment
- Status: confirmed
- Observation: A supplemental profile set global `COVERAGE_FILE` and a noncanonical M25 export path. Fixture-owned explicit Coverage.py sessions then shared the diagnostic namespace, while the existing M25 export rejected the alternate path. The unchanged canonical gate had neither condition. Using Coverage.py's CLI `--data-file` with the global variable absent preserved automatic child tracing and independent fixture sessions. Leaving both optional M25 export keys absent kept diagnostic measurement assertions active without fabricating a canonical export.
- Evidence: Candidate `791531e2312bbee1106b56267ec37603cad6535f`; `artifacts/test-audit-ci/full-suite-profile/05d0499b-7364-4bec-b4e8-6706422de4da` retains the interrupted environment failure. The corrected six-case preflights, `corrected-preflight-native-scope.json`, and full profile `54a17172-6d2e-4a15-9206-90c1dd8a61ad` distinguish namespace repair from its separate timeout-test failure. Native canonical receipt, coverage, M25 and wheel hashes remained unchanged.
- Suggested action: Before profiling nested verification fixtures, distinguish automatic subprocess tracing configuration from explicit fixture Coverage.py sessions. Qualify a small fixture-owned positive/negative cohort first. Do not infer a canonical bottleneck from instrumentation introduced only by the diagnostic.

