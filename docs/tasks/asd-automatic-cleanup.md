# Simple fixture and worktree cleanup

**Version 1.0.** Owner-requested delivery-policy amendment, in a separate PR from RA12.

The owner asked: “Update the cleanup policy and all conflicting references. Keep it simple—no cleanup tools or tests.” The amendment replaces the former cleanup development pipeline with coordinator housekeeping for exact disposable fixture, scratch and worktree paths. Custom deletion software remains separately authorized high-risk work. The canonical rules are [specification section 9.1](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#91-automatic-cleanup-at-task-completion) and [the housekeeping workflow](../operations/fixture-cleanup.md).

Scope: root instructions, specification, workflow, role skills, templates and conflicting task references. The coordinator owns documentation edits; a fresh independent policy reviewer assesses the complete diff before activation. No runtime, scripts, tests, fixtures, dependencies or executable workflows change. This migration applies to current and future housekeeping, including tasks with older cleanup-only requirements. Historical incidents, completed reviews and cumulative spending remain facts.

For this owner-requested documentation-only PR, validation is diff/whitespace and reference/link inspection plus independent policy review. No cleanup tools or tests are added or run; no full product test run is performed for this amendment. This task-specific instruction does not waive other tasks' product verification or submission requirements.

The sole local Current state is `artifacts/cleanup-policy/current-state.md`; exact candidate, review, check and PR results belong there and in the PR, outside tracked candidate bytes. The prior adoption record is preserved in Git history. No human numeric execution limit was set; unavailable model/token/cost measurements remain unknown.
