# Lesson format

**Version 1.0** One lesson per new Markdown file. This is a format guide, not a shared index.

Name files `YYYYMMDDTHHMMSSZ-<task>-<role>-<slug>.md` using the actual UTC creation time. Add a distinguishing slug if needed; never overwrite an existing name. Do not edit or delete earlier entries. A correction is a new file identifying the superseded entry and the evidence that changed the conclusion. Git retains history; append-only treatment is a prompt, not an access control.

Use these fields:

```markdown
# Short factual title

**Version 1.0**

- ID: unique filename without .md
- Date: ISO 8601 UTC creation timestamp
- Task: task ID or link
- Role: observing role
- Topic: short category
- Status: confirmed or hypothesis
- Observation: one concrete finding; distinguish what was measured from inference
- Evidence: durable file/commit/check pointer, relevant command and environment
- Suggested action: bounded change or next measurement; not an implicit approval
```

Record non-obvious reusable findings, not transcripts, private reasoning, secrets, or personal data. Link evidence instead of copying large logs. Blind roles A/B may read this guide and create their own lesson without reading existing entries; they may hand off wording for verbatim recording. The coordinator and doctor verify evidence before generalizing a lesson or changing instructions. A lesson grants no new editing scope or budget.
