# Supply the exact permitted skill excerpt to a blind role

**Version 1.0**

- ID: 20261104T045108Z-ce06-coordinator-blind-skill-excerpt
- Date: 2026-11-04T04:51:08.666221+00:00
- Task: [CE06 acquisition modes](../tasks/c-equivalence-acquisition-modes.md)
- Role: coordinator, from disclosed A1 handoff
- Topic: blind packet read scope
- Status: confirmed procedural incident; implementation exposure not reported
- Observation: A1 requested the full test-audit skill although its packet allowed only the authoring questions. It later disclosed the procedural overread and stopped blind authorship. It reported no implementation, source archive, history or nonblind discovery-result exposure. The provisional work and charges were retained; a fresh A2 independently reassessed the checkpoint.
- Evidence: [Authoring-question section](../../.agents/skills/test-audit/SKILL.md#authoring-and-review-questions); durable CE06 A1/report.md SHA256 79b2fc561b8f19a7f912ee320ba262e1a89d42005f2f40bebe7c7e6a824150e5. The exact supplied excerpt used for later blind packets hashes to 212f497ff2fe1ca56f376ef79248f8a35f8c5746f20d00a917fe3554bf45df9d. A2/report.md records the fresh-role scope and explicit remaining proof limits.
- Suggested action: Put a verbatim section excerpt and identity in the public packet when the permitted read is narrower than the skill file. Distinguish diagnostic source suppression from authorization to read a file. This incident adds no new policy or role authority.
