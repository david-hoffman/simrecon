# Native final-message output can overwrite a role report

**Version 1.0**

- ID: 20261005T061140Z-delivery-efficiency-coordinator-separate-native-output
- Date: 2026-10-05T06:11:40Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: role evidence
- Status: confirmed
- Observation: The native launch used the same path for a role-written detailed report and CLI final-message output. At process completion the short final handoff replaced the detailed report. The ignored event stream retained the write evidence; later launches use separate paths.
- Evidence: `codex-cli 0.160.0`, `codex exec --help`: `-o`/`--output-last-message` writes the last message. Coordinator launch/recovery evidence is linked by [the task](../docs/tasks/delivery-efficiency.md); [role-launch guidance](../docs/operations/role-launches.md) now distinguishes the destinations.
- Suggested action: Use a separate final-message destination when a role writes its own detailed report. Retain concise final handoffs and the original report without copying role transcripts into the tracked tree.
