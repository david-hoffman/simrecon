# Provenance oracles must honor the declared spatial profile

**Version 1.0**

- ID: 20261002T173457Z-mrc-conversion-coordinator-profile-aware-provenance-oracle
- Date: 2026-10-02T17:34:57Z
- Task: MRC-CONVERSION-01
- Role: coordinator recording fresh blind B evidence
- Topic: public-contract test oracle
- Status: confirmed
- Observation: Follow-up B rejected M39 because a reused success oracle always treated the original spatial fields as old canonical micrometre sampling. Under M39's unknown spatial profile, the contract permits unresolved old sampling plus explicit canonical overrides. A bounded test-only correction preserved every pixel/header/container/reader assertion and accepted permitted unresolved provenance; fresh B accepted the revised checkpoint.
- Evidence: [contract](../docs/contracts/mrc-conversion-v1.md), initial proposed test checkpoint `75f8a517f31f445dde701fcb932241c9bac80715`, corrected checkpoint `f74469ee936787d574c9fc4b69f7f93ec818f0de`, [B round 1 finding](../artifacts/mrc-conversion/roles/b-followup-round1-report.txt), [B round 2 acceptance](../artifacts/mrc-conversion/roles/b-followup-round2-report.txt), [source-free 44-scenario A checks](../artifacts/mrc-conversion/roles/a-followup-round2-evidence.md); macOS arm64, pinned task environment.
- Suggested action: Derive provenance expectations from the declared profile. Require exact replacement values and sources while retaining original uninterpreted fields; do not add unit assumptions through a shared test helper. This observation grants no scope or allowance change.
