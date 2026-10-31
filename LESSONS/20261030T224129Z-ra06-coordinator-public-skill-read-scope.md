# Separate public instruction reading from blind discovery authority

**Version 1.0**

- ID: 20261030T224129Z-ra06-coordinator-public-skill-read-scope
- Date: 2026-10-30T22:41:29.029866+00:00
- Task: [RA06](../docs/tasks/reference-alignment-ra06.md)
- Role: coordinator
- Topic: blind-role packet scope
- Status: confirmed for this launch
- Observation: A1 stopped without editing after a search displayed public test-audit procedure sections beyond the packet's narrow reading range. It reported no implementation, history, existing oracle or coordinator-state exposure. A fresh A2 packet allowed reading the public skill while limiting its application to blind authoring questions. A2 completed its independent fixture handoff under that permission. This distinguishes a public-instruction scope mismatch from scientific implementation exposure; it does not claim stronger access controls.
- Evidence: retained `artifacts/ra06/roles/A1/final.txt`, `roles/A1/launch.json`, `artifacts/ra06/packets/A2.txt` and `artifacts/ra06/roles/A2/report.md`; native Sol/high, memories and delegation disabled. A1's launch and all charges remain in the sole evidence ledger.
- Suggested action: State the public skill read permission separately from permitted discovery/application. Keep actual implementation/history/oracle/state exclusions explicit. Route a reported mismatch before continuing; do not infer that clearing context restores blindness. This lesson authorizes no policy change or broader source access.
