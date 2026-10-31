# A literal excerpt makes the blind read boundary concrete

**Version 1.0**

- ID: 20261031T115128Z-ra09-coordinator-literal-public-skill-excerpt
- Date: 2026-10-31T11:51:28.985769+00:00
- Task: RA09, docs/tasks/reference-alignment-ra09.md
- Role: coordinator
- Topic: role packet
- Status: confirmed observed diagnostic/packet facts; stated cause limits remain unknown
- Observation: Fresh native A1 displayed the complete test-audit skill although its packet allowed only public authoring questions. It stopped before imports, probes or tests, with no product implementation exposure. A fresh A2 received a standalone public excerpt and explicitly excluded the complete linked skill. The original attempt and its measured usage remain charged.
- Evidence: artifacts/ra09/roles/A1/report.md; artifacts/ra09/roles/A1/launch-receipt.json; artifacts/ra09/public-test-value-questions-v1.md; artifacts/ra09/roles/A2/packet.md.
- Suggested action: Supply exact standalone public text when a blind role may read only part of a linked source. Keep the full original as coordinator context; do not rely on a context reset to restore eligibility.
