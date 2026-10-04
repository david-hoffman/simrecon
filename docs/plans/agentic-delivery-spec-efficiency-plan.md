# Plan: make the generic delivery specification more efficient

**Version 1.0. Proposed October 3, 2026.**

Status: proposal only. Writing this plan does not amend the specification or authorize its adoption. The current [delivery specification](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md) remains authoritative. This plan concerns the reusable system; the [SIMrecon plan](agentic-delivery-repo-efficiency-plan.md) concerns its installation.

The proposed change is to scale session overhead to risk, preserve accepted evidence where it still applies, and make corrections smaller. Keep independent review where a wrong oracle or interpretation could validate the wrong product. Keep the 100% measured statement/branch coverage gate and full verification of the exact candidate.

## Evidence and confidence

The current system requires four fresh root sessions per task, fresh A/B after test corrections, and a five-scenario default ([specification §§3–4](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#3-step-0-clarify-and-approve-each-task)). It already permits narrow packets, unchanged-scenario redistribution, and applicable check reuse ([§9](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#9-cost-and-completion)). Improve those rules before adding machinery.

The [SIMrecon plan](agentic-delivery-repo-efficiency-plan.md) records local observations: one completed conversion grew from 26 to 44 to 46 scenarios across three A/B review windows. B found four oracle/test defects; D found an unjustified wavelength-key input restriction. That supports preserving independent high-risk review. It does not establish an optimal slice size or measured savings. See that companion plan for token-accounting limits; historical checks were not rerun here.

Confidence is high that narrower corrections and fewer repeated reads can reduce avoidable work. Confidence is moderate in the tier boundaries and low in any numerical savings estimate. A pilot that misses defects or shifts costs into owner review would change the recommendation.

## 1. Approve risk before selecting sessions

Amend the role table and opening paragraphs of [§4](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#4-four-fresh-delivery-sessions), and the normal-path sentence in §9, to use this decision table. Record the selected tier and reason in the approved task.

| Proposed tier | Eligibility | Session route and acceptance |
|---|---|---|
| Mechanical or documentation | Non-normative prose, formatting, links, or deterministic edits with a reviewable diff; no changed executable behavior, dependency, verification rule, permission, or policy | One worker. Review the diff and relevant deterministic checks. Owner acceptance is sufficient; an independent reviewer is optional unless the approved contract requires one. |
| Bounded existing behavior | A small repair/refactor within an approved conventional public contract; established expected results; no new scientific meaning, binary representation, custom numerical oracle, security boundary, or ambiguous interface | One worker may inspect implementation and author tests. A fresh independent reviewer checks the tests, behavior, scope, and exact passing candidate. The worker cannot approve their own repair. |
| High risk | Scientific/numerical behavior, binary formats, new custom oracles, security/permissions, substantial new interfaces, unresolved semantics, or uncertain impact | Retain fresh blind A test author, fresh blind B test reviewer, C implementer, and fresh D final reviewer. Preserve source-free A/B diagnostics and restricted-file rules. |

Risk determines the route, never changed-line count alone. Uncertainty promotes a task. A mixed task takes the highest tier unless independently scoped contracts justify a split. A failed lower-tier check does not itself authorize a scientific or interface repair. Policy edits, including adoption of this plan, require explicit owner approval and independent review. Dependency, workflow, gate, authentication, and permission changes always require independent review even when called mechanical. Changed tests/fixtures always receive independent review; high-risk changes use A/B. Coverage, discovery, fixtures, and delivery-rule edits require their own authorized scope. Tiering never permits silently weakening checks.

Tradeoff: the middle tier loses blind test construction. Limit it to established expectations; require the reviewer to challenge the oracle against the approved contract. Promote it if that review exposes an uncertain expectation. The conversion observations support retaining the high-risk route.

## 2. Separate task approval from routine execution

Amend [§3](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#3-step-0-clarify-and-approve-each-task) to say that explicit approval authorizes the named scope, tier, checks, budget, and routine role transitions. No repeat approval is needed to launch an already specified role, run authorized checks, fix an in-scope product defect within the remaining repair allowance, or make the approved unchanged-scenario redistribution.

For the first two tiers, a complete, explicit owner instruction may itself authorize the task. Record the actual instruction, scope, tier and inherited constraints; send a concise read-back without requiring a second “yes” merely because the record was written afterward. Missing material behavior or a new budget still needs an answer. High-risk contracts and changes to delivery policy retain explicit approval of the identified proposal. This is a proposed exception to the current universal read-back gate, not permission to infer approval from silence.

Renew approval for changed behavior, interfaces, permissions, data sharing, tier downgrade, budget extension, or exhausted repair allowance. Material unanswered questions still block dependent work. Architecture approval still does not approve a scientific feature. Silence remains no approval.

In the [task template](../agentic-software-delivery-v1.0/templates/TASK.md), add an “Authorized execution” line containing tier, role route, edit scope, checks, escalation triggers, and allowances. Update the [intake prompt](../agentic-software-delivery-v1.0/INTAKE-PROMPT.md) to ask for this once in the read-back.

## 3. Separate behavioral scenarios from coverage examples

Clarify §3's scenario-count paragraph and [§5](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#5-end-to-end-first-not-end-to-end-only): a scenario is a distinct approved decision and observable outcome. Multiple values that exercise that same decision may be coverage examples. A distinct rejection rule, interpretation, output guarantee, or boundary outcome is a separate scenario. Do not combine unrelated cases merely to evade the limit.

Keep five behavioral scenarios as an initial planning heuristic for distinct behavioral obligations. Approve a larger coherent contract once. Additional equivalent data or coverage examples within accepted behavior and budget do not trigger fresh approval. Add an optional coverage-example mapping under each scenario; B checks that the values introduce no unapproved meaning. Neither a branch count nor a parameterized test count decides the contract size. Coverage remains a separate measured gate. The 26→44→46 growth is a reason to audit classifications, not evidence that approved behavior can be deleted.

## 4. Review corrections as deltas, independently

Replace the blanket test-defect routing in §4 with a scoped correction rule. For high-risk work, blind A corrects the affected tests and fresh blind B reviews the changed oracle/tests plus every dependent case. Supply the prior accepted checkpoint, approved public contract, finding, diff, and dependency mapping. Exclude C's implementation and conversation. Unchanged accepted portions retain their review evidence.

B may accept a revised checkpoint after a delta review only when independence of the retained portions is justified. A shared parser, observer, fixture, tolerance, schema, or expectation change expands the review scope. A changed public meaning or inadequate dependency mapping requires a fresh complete review of affected behavior. The reviewer may expand scope; the author may not declare their own correction safe.

Amend §9 to count each completed correction review as a round in its recorded window. Preserve previous windows, spending, and C repairs. Keep diagnosis after two nonacceptances. A new session, renamed task, or narrower review does not replenish allowances. Lower-tier corrections retain fresh independent final review whenever that tier requires it.

Clarify that independence requires separation between authors and reviewers, not mandatory loss of an author's own context. Initial high-risk roles remain fresh roots. A may continue its own test-author session within the same approved work while blindness remains intact; C may continue its own implementation session for an authorized repair. Use a fresh author when exposure, changed scope, or excessive context warrants it. B/D correction verdicts still use fresh independent review sessions and never inherit implementation conversation. Continuing an author session grants no new editing scope, budget or repair. This continuation exception requires owner approval along with the tier policy.

## 5. Make evidence validity explicit

Expand §9's reuse paragraph and §4's handoff paragraph. Use a compact evidence record: tested revision/tree; test revision; canonical command; dependency-lock identity; relevant environment/tool versions and platform; integration base; exact result and coverage; unresolved limits. A single normal JSON/file receipt may link command output or discussions. Do not build a controller, state store, or evidence database.

Reuse a result only while every relevant input remains unchanged and no new failure challenges it. A changed environment invalidates affected results even if the commit is unchanged. Incremental checks guide edits; they do not replace canonical full verification of the exact submission candidate or required continuous integration (CI) platforms ([§6](../agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#6-ordinary-github-ci)). Retain 100% measured statements and branches across instrumentable owned runtime, globally and per package, including never-imported files and applicable subprocesses. Disclose exclusions and unsupported measurement.

Keep one Current state. Each handoff should contain only decision, revision, classified findings, evidence links, next role, and remaining allowances. A/B receive a public-contract packet separate from implementation-bearing status. Link earlier accepted reports instead of recopying them.

## 6. Roll out with measurable acceptance

Adoption order matters:

1. Owner approves tier boundaries, correction scope, and a bounded pilot budget. Prepare one proposed spec patch; retain Version 1.0 and Git revision history.
2. Independently review the patch. Update directly affected AGENTS generation template, TASK template, intake prompt, role procedures, and workflow examples together. Check for contradictions. Do not activate only a permissive sentence while retaining incompatible restrictions elsewhere.
3. Pilot one documentation task, one conventional bounded repair, and one high-risk task. Keep in-flight tasks on their original approved rules unless the owner explicitly approves migration. Migration cannot erase earlier attempts or reset spent budgets/allowances. Use the existing system if a pilot exposes an unresolved safety gap.
4. Compare results, then approve wider adoption or revise the proposal. Do not merge/release automatically.

Acceptance checks: correct tier recorded before execution; unchanged approved behavior preserved; independent reviewers used where required; a shared-oracle correction expands review scope; invalidated evidence reruns; full exact-candidate verification and coverage pass; no concealed failure, scope expansion, self-approval, or multiplied allowance; one concise status and usable handoff.

Amend §9 metrics to record per-role model responses, input/cached/output tokens, available monetary cost, elapsed and owner-wait minutes, check wall time, scenarios versus coverage examples, review windows/rounds, repairs, and detected defects. Missing role metering is “unknown,” not zero. Compare like risk tiers and task sizes. Report totals and attribution separately so cheaper coordination cannot hide more expensive roles. Set savings targets after the pilot establishes a complete baseline.

Owner decisions remain: accept the middle tier's loss of blindness; approve tier boundaries and promotion triggers; accept complete-request authorization for lower tiers; approve scoped correction review and author-session continuation; choose pilot budget and acceptable overhead/defect criteria. This document authorizes none of those changes.
