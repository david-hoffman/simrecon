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
Use one compact Current state and linked metrics: scenarios/examples, route/model/effort, cumulative full/delta review rounds, repairs/spending, actual human-set limits, per-role responses/input-cached-output tokens, launch/check/critical-path/owner-wait time, defects/false findings/exposure and explicit unknowns. Avoid cumulative-counter/child/overlap double counting. There is no default scenario/review/repair cap or execution budget. Diagnose recurring
failures and each correction with evidence. Preserve cumulative attempts/spending and
actual human-set limits; do not silently lower the verification/coverage gate.

Use the task's inherited approved coverage policy under spec section 5.1 and classify
coverage friction under section 5.2 before correction. State the missing approved outcome
or concrete reachable risk, evidence and why tests miss it. Test gaps belong to the
authorized test owner, needless implementation to its author, unresolved semantics to
intake and measurement faults to authorized infrastructure. A bare uncovered branch
does not justify a new requirement or another A/B cycle. Keep blind corrections
source-free; preserve role ownership, supplemental-test labels and prior accounting.
Behavior/risk evidence always applies; selected target failures and missing required
measurement block acceptance, while unselected metrics are advisory. The full exact-
candidate local gate and required CI remain in force under the approved policy.

Ordinary doctor cannot select an easier policy or activate a relaxation through a failing
task's repair. A separately authorized coverage-policy adoption records the explicit
owner choice and requires fresh independent policy review before activation. Reconcile
affected instructions and authorize any executable gate changes to their named
infrastructure owner; explicitly migrate active tasks before applying changed gates.
An irreducible selected-target conflict needs an explicit owner policy decision or remains
blocked. This distinction adds no approval checkpoint for a record that restates the
human request and replenishes no attempts or spending.

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

Present exact diff, evidence/lesson IDs and expected improvement. The human request authorizes its intended policy scope; record the concrete contract and proceed without another document approval. Ask only for missing material decisions, unclear/outside-request objectives or human-required external authority. Require a fresh independent policy review before activation. Commit/push/merge only within actual owner authority; normal Git/PR gates remain. Then
add a new timestamped lesson file in LESSONS/ linking the disposition to that commit
and the earlier entry. Migrate in-flight work only with explicit owner authorization, preserving every historical attempt/round/repair/expenditure and actual human-set limit; leave historical records intact.
All delivery documents stay version 1.0; Git tracks their revisions.
Honor actual human-set limits; absent limits are not set and missing measurements are unknown. The independent policy reviewer is coordinator-launched, never a nested self-review. No daemon or uncontrolled automatic repair loop; diagnosed in-scope corrections continue without default-quota approval stops. Conditional CI-authoritative eligibility is separate evaluated scope, not a way for this patch to approve its own gate.
```
