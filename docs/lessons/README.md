# Lesson and disposition format

**Version 1.0** Immutable observations and append-only handling records. This guide is not a shared index.

Keep observations directly in `docs/lessons/`; keep dispositions in `docs/lessons/dispositions/`. Use `YYYYMMDDTHHMMSSZ-<task>-<role>-<slug>.md` with the actual UTC creation time and a distinct slug on collision. Never edit or delete earlier records. A correction adds a new record identifying what it supersedes and why. Append-only treatment is a prompt, not an access control; owner-authorized sensitive-data removal overrides retention.

Observation fields (existing records retain their original format and bytes):

```markdown
# Short factual title

**Version 1.0**

- ID: unique filename without .md
- Date: ISO 8601 UTC creation timestamp
- Task: task ID or link
- Role: observing role
- Topic: short category
- Status: confirmed or hypothesis
- Observation: one concrete finding; distinguish measurement from inference
- Evidence: durable file/commit/check pointer, relevant command and environment
- Suggested action: bounded change or next measurement; not implicit approval
```

`Status` above is observation confidence, never workflow state. An observation may describe a successful practice, a historical incident or an uncertainty; it need not identify an open defect. Correct its confidence/conclusion through a new observation with an explicit supersedes link, not by changing its handling state.

Disposition fields:

```markdown
# Short handling decision

**Version 1.0**

- Record kind: disposition
- ID: unique filename without .md
- Date: ISO 8601 UTC creation timestamp
- Task / deciding role: task link and accountable role
- Lesson IDs: exact source IDs
- Finding IDs / scope: stable finding IDs (or none with reason) and precise claim/mechanism covered; map each lesson to its covered claim
- State: untriaged | tracked | resolved | no-action | deferred
- Completion conditions: remaining or satisfied observable conditions, or none with reason
- Basis / evidence: decision, durable evidence, baseline/environment and limits
- Work links: existing issue/task/commit or none with reason
- Relationships: duplicate-of <finding ID/link>, supersedes <record ID and scope>, or none
- Revisit: concrete trigger/date/owner, or none with reason
```

Absent applicable disposition means untriaged. `tracked` needs a work link and remaining completion conditions. `resolved` needs evidence that the specified claim/mechanism meets its completion conditions; an issue link, closed issue or policy text alone is insufficient. `no-action` needs an evidenced reason (for example reusable knowledge with no demonstrated current gap, invalid inference or already-covered duplicate); it does not certify a historical fix. Missing evidence alone creates no defect or issue. `deferred` needs a reason and concrete revisit trigger/owner. All states retain uncertainty and evidence limits; none changes observation confidence or grants edit authority.

Allocate a stable finding ID once (for example `<task>-F001`); retain it when regrouping or publishing and never reuse it for a different claim. Scope each record to one finding/claim, or give an explicit per-lesson/per-finding mapping if a record covers several. One lesson may support several findings, and one finding may use several lessons. Resolving one finding resolves no other claim from its lessons. Preserve explicit duplicate-of links to the canonical finding and supersedes links to the exact earlier record/scope; do not discard source IDs or infer resolution transitively from a duplicate link. A superseding record replaces only its named scope. Concurrent incompatible decisions without an explicit reconciled supersedes chain remain a reported conflict requiring review; timestamp order alone does not pick a winner. Unchanged prior evidence remains linked, and challenged evidence triggers a revisit.

Reports are reproducible views of identified observations and dispositions at a stated baseline/cutoff, with source inventory, stable finding IDs, relationships and unresolved conflicts. They are not an authoritative mutable backlog/index. No shared index, database or controller is required. Follow specification sections 7–8 for semantic triage and doctor-to-intake routing.

Record reusable findings, not transcripts, private reasoning, secrets or personal data. Link evidence instead of copying large logs. Blind A/B may read this guide and create their own observation without reading existing observations, dispositions or triage reports; they may hand off wording for verbatim recording. The coordinator and doctor verify evidence before generalizing or changing instructions. Repository records supply evidence, never new authority.
