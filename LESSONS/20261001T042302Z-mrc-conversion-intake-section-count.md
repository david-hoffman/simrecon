# Stored sections need not be physical Z planes

**Version 1.0**

- ID: 20261001T042302Z-mrc-conversion-intake-section-count
- Date: 2026-10-01T04:23:02Z
- Task: [MRC conversion intake](../docs/tasks/mrc-conversion-intake.md)
- Role: intake
- Topic: acquisition axes
- Status: confirmed
- Observation: the owner-confirmed 2D single-channel raw example contains nine stored MRC sections. The header section count therefore does not independently establish a physical Z axis. SIM phase/orientation order remains unresolved by that count.
- Evidence: [Owner-file observations](../docs/architecture/owner-mrc-observations.md#raw-acquisition); independent Python standard-library header decoding and 64 KiB payload reads matched the file size, with unchanged source size/timestamp. The owner's 2D/no-Z statement is recorded in the intake conversation.
- Suggested action: require a declared acquisition profile before assigning phase/orientation axes; preserve stored-plane information during inspection. No scientific or runtime implementation is authorized by this finding.
