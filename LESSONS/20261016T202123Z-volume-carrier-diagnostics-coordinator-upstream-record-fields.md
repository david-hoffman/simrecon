# Verify upstream record fields before composing a new public operation

**Version 1.0**

- ID: 20261016T202123Z-volume-carrier-diagnostics-coordinator-upstream-record-fields
- Date: 2026-10-16T20:21:23.265136+00:00
- Task: [Volume carrier diagnostics](../docs/tasks/volume-carrier-diagnostics.md)
- Role: coordinator/intake
- Topic: public record composition
- Status: confirmed
- Observation: The initial scan contract required response.source, although the approved EmpiricalVolumeResponse record has six fields and no source label. Blind A identified the mismatch before test acceptance or implementation. Coordinator correction01 moved the opaque label to an explicit required source argument; it did not change the upstream record or numerical objective.
- Evidence: [Upstream public record](../docs/contracts/empirical-volume-response-v1.md); original intake commit6eb55e809b234d7ca512b74f8eaf47be43c56480 and corrected contract commit4285416. Local artifacts/volume-carrier-diagnostics-20261016/contract-clarification01.json retains before/after SHA-256 identities and classified cause. A01 public record inspection used the current-worktree Python3.13.12 source-free channel.
- Suggested action: Check the exact upstream public field list before choosing a new composition boundary. If a consumer needs a label absent from that record, select its explicit input or separate provenance record during intake. This lesson grants no authority to amend an upstream interface.
