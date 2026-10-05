# Doctor prompt

**Version 1.0** This is the procedure for `delivery doctor`, using the existing `review-work` skill in doctor mode. Before the command is implemented, give this prompt to a fresh coding session. It may write a documentation patch; it must not claim a command ran when it did not.

```text
Run doctor under docs/agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md section 8.
Check the working tree and stop
rather than overwrite unrelated/uncommitted work or interrupt an active delivery task.
Read relevant project instructions, recent entries in LESSONS/, and concrete CI/test
or repository evidence. Search narrowly; do not replay all sessions or recrawl sources.

Classify failures under spec section 4: environment/tooling failure, test defect,
product defect, or unresolved requirement. Then distinguish an instruction gap from
an execution error under an existing rule. Verify lessons before generalizing them.
A green rerun does not prove a previous failure harmless. Hypotheses remain hypotheses.
Use one compact Current state and linked metrics: scenarios/examples, route/model/effort, review windows/rounds, repairs/budget, per-role responses/input-cached-output tokens, launch/check/critical-path/owner-wait time, defects/false findings/exposure and explicit unknowns. Avoid cumulative-counter/child/overlap double counting. An evidenced patch may propose tuning
the default slice size; do not tune it autonomously, reset consumed budgets, or lower
the verification/coverage gate.

For a confirmed spec gap, create a small docs branch and actually edit the existing
docs/agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md plus directly affected
instructions. Replace or remove text before adding more. Keep shared operational
instructions in AGENTS.md and role-specific differences in skills; synchronize their
generation templates. No new framework, skill swarm, or parallel spec. No gap means
no change. With --check, report only and do not write files.

Do not change runtime code, tests, workflows, acceptance thresholds, or repository settings.
Do not rewrite desired behavior to match a bug or silently approve architecture drift.
Those need separate scoped work. Data-loss behavior, including settled overwrite/truncation repairs, stays high risk and is excluded from bounded maintenance. Preserve that boundary in every synchronized instruction. Test a new procedural instruction on one relevant
example when practical. Explain what was and was not verified.

Present exact diff, evidence/lesson IDs and expected improvement. Obtain approval of the identified policy scope when absent; existing explicit authorization is sufficient, no duplicate yes. Require a fresh independent policy review before activation. Commit/push/merge only within actual owner authority; normal Git/PR gates remain. Then
add a new timestamped lesson file in LESSONS/ linking the disposition to that commit
and the earlier entry. Migrate in-flight work only with explicit owner authorization, preserving all historical budget/rounds/repairs; completed work stays charged.
All delivery documents stay version 1.0; Git tracks their revisions.
Stop at the approved budget. The independent policy reviewer is coordinator-launched, never a nested self-review. No autonomous retry loop. Conditional CI-authoritative eligibility is separate evaluated scope, not a way for this patch to approve its own gate.
```
