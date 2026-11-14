---
name: lessons-doctor
description: Review SIMrecon lessons and dispositions in the current cloud or local session, produce scoped triage, or prepare an authorized documentation policy patch.
---

# Lessons doctor

**Version 1.0.** This is the primary doctor entry for cloud and local sessions.
Follow root AGENTS.md, [PROJECT](../../../docs/PROJECT.md),
[DOCTOR-PROMPT](../../../docs/agentic-software-delivery-v1.0/DOCTOR-PROMPT.md),
specification sections 7–8 and the [lesson format guide](../../../docs/lessons/README.md).
Read only the context needed for the requested scope.

Run directly in the current authorized coordinator or nonblind author session.
This is a cross-cutting procedure, not a new independent delivery role. Do not
launch native Codex or require nested authentication to perform triage. A native
launcher failure establishes a launcher/environment limit, not inability to
inspect available repository evidence here. Use available read tools and existing
authenticated remote access; record missing capabilities without installation or
an automatic retry loop. Never claim an unexecuted command or inaccessible remote
check succeeded.

Any required independent report review, and every policy review before activation,
uses a separate fresh session without author history under
[review-work](../review-work/SKILL.md). The doctor author cannot self-approve.
No extra native launcher is required for policy review. A/B must not run this
nonblind procedure or receive its raw observations, dispositions or reports.

## Select the requested scope

- Check-only (`--check` semantics): inspect and return a report in the conversation;
  write nothing, including reports, dispositions, issues or policy files. A
  coordinator may capture the returned report separately only with actual write
  authority. This session instruction adds no CLI flag or sandbox guarantee.
- Report-only triage: analyze the requested lessons without fixes or policy
  activation. Write report/disposition artifacts only when the human request
  authorizes those named outputs. Publication needs actual external-write
  authority; an existing explicit publication request suffices.
- Documentation patch: only an evidenced gap within human-requested, named
  documentation scope permits edits. Keep affected spec, AGENTS, skills, prompts,
  templates and project notes aligned. Obtain fresh independent policy review
  before activation and preserve normal exact-candidate Git/PR gates.

Ordinary scope is narrow. An explicit full-backlog pass must inventory every lesson
at its stated baseline, including useful observations with no defect; it cannot
be satisfied by only reviewing recent or unresolved records. Reuse prior reports
and dispositions as evidence with their baseline, reviewed scope and current
revalidation limits. Label an incremental reconciliation as incremental. To claim
a full pass, account for the complete baseline inventory and all applicable claims,
even when some analysis reuses still-applicable evidence.

## Inspect, reconcile and hand off

1. State the request, mode, baseline/cutoff, named outputs and access limits.
   In check-only mode, return these in the conversation without writing task state.
   In other modes, update the existing task state only under actual write authority.
   Preserve unrelated work. Inventory the requested source lessons and applicable
   dispositions. Keep immutable source IDs, original
   confidence, scoped lifecycle states and explicit duplicate/supersedes links.
   Conflicting records require reconciliation, not last-timestamp-wins handling.
2. Group observations by meaning, then analyze mechanisms against current approved
   expectations and evidence. Distinguish instruction gaps, execution errors,
   product/test/environment defects, reusable knowledge and unresolved meaning.
   Each bucket may produce zero, one or many findings; missing evidence alone
   proves no defect. Account for each full-pass source once in the inventory and
   map it to every applicable finding or evidenced no-action/deferred/untriaged
   outcome. Preserve hypotheses and contradictory evidence.
3. Reuse stable finding IDs across reports, work items and dispositions. Record
   observed versus expected behavior, expectation source, supporting/contradicting
   evidence, uncertainty, suspected mechanism, work links, completion conditions
   and revisit triggers. Read current remote open/closed issues and relevant PRs
   when available. Inspect linked work and its current diff/check/completion
   evidence against the finding's conditions; issue closure or a PR state alone
   proves no resolution. Record head/merge identity and access/time limits where
   material. Unavailable remote evidence stays a gap, not a completed fix.
4. Before authorized issue creation/update, search remote issues/tasks and PRs by
   stable IDs and mechanism, inspect candidates, reuse matching work and recheck
   before creation. Disclose incomplete deduplication. A request for triage alone
   authorizes no external publication or implementation fix.
5. Return actionable findings to intake with source IDs, evidence, work links,
   uncertainty, proposed route and completion conditions. Intake owns contracts,
   existing risk/ownership routes and sanitized public A/B packets. Reports are
   evidence views, never a second execution state or authority to repair every
   finding. Preserve cumulative attempts/spending and actual human-set limits.

Doctor changes no runtime, tests, workflows, acceptance thresholds or repository
settings and cannot relax coverage or bless architecture drift to obtain a pass.
Route those findings through existing authorized ownership. The optional legacy
`uv run --locked delivery doctor [--check]` launches native Codex and requires a
usable native installation/authentication; it remains available on such hosts.
It is not the cloud entry and is not required for this skill.
