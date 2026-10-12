# An identity check cannot undo an earlier protected overwrite

**Version 1.0**

- ID: 20261012T030103Z-empirical-transfer-coordinator-protected-output-before-identity
- Date: 2026-10-12T03:01:03.610675+00:00
- Task: [Empirical transfer consumption](../docs/tasks/empirical-transfer-consumption.md)
- Role: coordinator
- Topic: test oracle and delivery preservation
- Status: confirmed
- Observation: Disposable source-free public CLI probes demonstrated verifier-owned writes changing tracked/Git bytes after a phase redirected an ignored output. A later identity failure did not undo the overwrite; writing a receipt after the identity snapshot could even leave a passed result. Fresh authored preservation cases independently distinguish phase-time actions from verifier-time target changes.
- Evidence: [Contract](../docs/contracts/verification-output-protection-v1.md); local audit-discovery-original/delivery.md and output-protection-correction/A02 public ledger/handoff, fresh B03 review and C01/implementation-handoff.md under artifacts/empirical-calibration-consumption-20261011. Source-free public verifier probes and focused pytest on Python 3.13.12, macOS arm64; 302 final focused rows passed. Historical proof remains archived.
- Suggested action: Protect each verifier-owned persistence boundary and collect truthful final identity/evidence. Preserve linked metadata and legitimate safe output alternatives; this lesson supplies no arbitrary-concurrency sandbox guarantee.
