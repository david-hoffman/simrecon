# Correct the native CLI identity for the live doctor failure

**Version 1.0**

- ID: 20260930T201856Z-setup-coordinator-correct-native-cli-identity
- Date: 2026-09-30T20:18:56.339267+00:00
- Task: SETUP-DOCTOR in [setup plan](../docs/tasks/setup-plan.md)
- Role: setup coordinator after B's environment observation
- Topic: evidence identity correction
- Status: confirmed
- Observation: This supersedes only the version attribution in [the earlier native-boundary lesson](20260930T201435Z-setup-coordinator-native-boundary-compatibility.md). The actual doctor check header and current executable identify Codex 0.159.2, not the historical 0.155.0-alpha.16.4 launch probe. The native flag conflict and failure classification remain confirmed. The reason the available executable changed has not been established.
- Evidence: [corrected identity and repeated parser rejection](../docs/setup/evidence/doctor-initial.json). `codex --version` reports 0.159.2; the repeated conflicting-flag command exits 2 before a session. B also independently observed 0.159.2. No previous lesson was edited.
- Suggested action: Attribute live evidence to the executable actually used, retain the earlier probe as historical, and renew relevant native checks after the repair. Do not infer an updater cause without evidence.
