# Execute process probes before reserving shared fixtures

**Version 1.0**

- ID: 20261021T044902Z-test-audit-coordinator-process-capability
- Date: 2026-10-21T04:49:02.252618+00:00
- Task: [test audit](../docs/tasks/test-audit-linux-ci.md)
- Role: coordinator
- Topic: native sandbox environment qualification
- Status: confirmed
- Observation: The native author found an executable ps path, but its workspace sandbox denied execution. The first real reader test failed before its cancellation witness and retained its authentic cache backup. An elevated rerun of unchanged author bytes passed after separately verified recovery. Executable discovery alone did not qualify process-observation capability.
- Evidence: Local ignored deadline-A/focused-native-sandbox-failure-receipt.json; recovery-closure-check.json; recovery-restoration-receipt.json; root-focused-execution.json under artifacts/test-audit-ci. The original backup inventory, inode and mode matched after restoration. The frozen focused case passed in 13.42 s on macOS arm64; Ubuntu evidence remains separate.
- Suggested action: Before resource reservation, execute a bounded harmless process probe in the actual test environment. Preserve failed-run evidence and recover through existing exact-identity guards after independent closure checks. Operator recovery is never the test's natural child-closure witness.
