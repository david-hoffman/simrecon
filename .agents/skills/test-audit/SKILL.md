---
name: test-audit
description: Apply the test-value questions when authoring or reviewing tests; run requested focused or subsystem test audits with evidence, preservation mapping, and role-safe correction routing. Audit discovery is report-only and does not grant edit or publication authority.
---

# Test audit

**Version 1.0.** Follow root AGENTS.md and the narrow packet. This cross-cutting procedure supplements the four delivery role skills; it is not another role or controller. [Specification section 5.3](../../../docs/agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md#53-test-audits-and-preservation) supplies policy. Use the authoring questions in the existing role. A requested focused audit or subsystem campaign also uses the discovery, ledger and preservation workflow below.

## Authoring and review questions

Before adding or changing a test, name:

1. The approved observable behavior, invariant or independent contract it protects.
2. A credible wrong outcome it distinguishes, with an expectation independent of product output.
3. The strongest existing proof at the owning boundary and the distinct gap this test fills. Extend that proof when it can cover the gap; another layer needs a risk it uniquely reaches.
4. Whether it demands a production export, flag, wrapper or injection seam no real caller needs. Exercise a production or real-caller boundary instead; external public library callers count.

A missing answer calls for diagnosis or intake, not invented behavior. A/B answer from permitted public sources and tests only. They do not inspect implementation to establish callers or discover production seams. An uncertain production relationship goes to a nonblind audit lane or D.

Prefer the smallest real composition that reaches the contract. Fixtures may replace uncontrollable external input/output; they must not manufacture the decision, expected value or ordering the production owner should supply. Raw bytes, storage state, ordering and exact payloads are valid when they are themselves an approved observable contract. Record which boundaries a smaller test cannot prove.

Initially passing tests are valid. A claim that a repair fixes a regression needs an intended valid failure on the pre-fix baseline when available, then passing proof on the repaired candidate through the same meaningful harness. Report unavailable baseline proof honestly and narrow the claim; do not manufacture product-red or require mutation testing. Later additions stay supplemental under the delivery rules.

## Read-only discovery

The coordinator records the requested area, contract, baseline, read/write allowlists, route, checks, completion condition and actual human-set limits before launching work. For a subsystem campaign, inventory every owned test file/declaration, parameter rows with different decisions, shared fixtures/helpers, public entry points and required compatibility proof. Record baseline results, failures and missing evidence; unavailable results are unknown, not passing. A focused audit records its narrower inventory and exclusions explicitly.

When the human requests parallel agents, the coordinator launches native read-only lanes by production owner boundary, with a cross-cutting pattern lane where useful. Every declaration has one accountable lane; overlapping observations reference its ledger entry. A launched role does not launch another role. Shared helpers have one correction owner. This is native harness coordination, not a custom swarm platform. Without delegation authorization, perform discovery directly within the assigned packet.

Nonblind discovery may inspect complete tests, production owners, real callers/callees, overlapping proof, relevant dependency source/types, configured routing and history. It reports evidence without editing. These inputs are excluded from blind A/B; neither read-only status nor this skill waives blindness. D forms its assessment before current-task implementation lessons. Keep nonblind reports out of PUBLIC-PACKET.

Look for leads, not automatic deletion candidates:

- execution with no meaningful outcome check; self-comparisons or copied expected values;
- copied inventories, manifests, source/import strings or export lists;
- private predicates or call shapes already proved at a real boundary;
- repeated invocations of the same contract or local replays of shared helpers;
- mocks that implement the assertion, or fixtures supplying the result/ordering the owner should create;
- tests preserving otherwise unused production seams;
- rejection controls failing at a different guard or unreachable path;
- names that promise behavior the input or assertion never exercises.

Retain independent public API, protocol, configuration, migration, storage, security, platform, default, exact-byte, package, release or architecture obligations. Structural inspection can be the cheapest independent guard when it protects an approved key/byte/path and survives identifier-only refactoring. Slowness, static checks, apparent coupling or bare uncovered branches do not justify deletion. A retained baseline failure may be a product defect; diagnose it instead of removing proof. There is no deletion target.

## Declaration ledger and keeper plan

Give each audited declaration a stable ID, exact test name/location, contract/requirement and scenario/example IDs, actual detectable failure, evidence reference and one disposition. Split parameter rows only when their dispositions or meaning differ; do not conceal distinct decisions as equivalent data.

| Mark | Meaning | Required preservation evidence |
|---|---|---|
| R | Retain, including a move | Independent obligation and credible failure it catches |
| F | Retain obligation; repair proof | Defect in assertion/fixture/oracle, approved expected outcome and affected dependents |
| C | Consolidate | Named keeper and assertions/positive/error cases it absorbs before removal |
| D | Delete | Stronger remaining keeper for every obligation, or evidence that no approved obligation exists |

For F/C/D, also record non-test callers (including external API possibility), relevant history/reason, production or support seam affected, risk, named correction owner and focused check. An unresolved field keeps the candidate unready for editing, never presumed deletable. Record retained false positives and reasons. Nonblind caller/history evidence remains in candidate context.

Then inspect the layer as a whole. Map each approved obligation and distinct failure to its keeper suite/test, not merely each old file to a new file. Name assertions/rows carried forward, remaining proof limits, retired layers and any production seam simplification. Review shared oracle/fixture dependents. Deleting a file is no proof that its obligations survived; suspicious tests are no automatic edit list. Removing assertions requires independent review of this mapping under the selected route.

## Diagnose and route coherent corrections

The coordinator classifies each finding and selects impact/uncertainty route before editing. Audit authority alone grants no product/test/infrastructure authority. Use the existing task if its contract and named ownership cover the finding; otherwise intake defines the coherent correction contract. Preserve dependencies and all cumulative charges across batches.

- High-risk test/fixture/oracle correction: sanitized approved public reproduction, prior checkpoint and test/requirement dependency mapping to blind A and fresh B. Strip implementation, history, coverage maps, repair hypotheses and raw audit logs. Shared expectations/observers/parsers/tolerances expand B review; B decides retained evidence applicability and accepts the revised checkpoint before C resumes.
- High-risk product correction or removal of unnecessary implementation: authorized C within named product scope and frozen tests, then exact full verification and fresh D. C cannot remove or change reviewed tests, gates or this policy. If a proposed seam removal changes scientific/binary/interface meaning, resolve that contract before dependent work.
- Bounded conventional test/product/support correction: explicitly named worker ownership and fresh independent review of oracle, obligation mapping and exact passing candidate. Uncertain or high-risk impact returns to intake.
- Measurement/routing/gate defect: named infrastructure ownership and fresh required review; audit cleanup does not authorize changing discovery, exclusions, platforms, thresholds or report integrity.
- New meaning or unclear expectation: intake before dependent correction. Policy amendment: named documentation author and fresh independent policy review before activation.

Diagnose each correction and recurring nonacceptance from concrete evidence. Apply one coherent owner batch, serialize shared-helper edits and retain a reviewed obligation mapping. Keep unrelated discrepancies as named follow-ups. Do not edit material inputs while proof is running; changed inputs invalidate affected evidence. No fixed attempt/scenario/time quota or uncontrolled retry loop applies; actual human-set limits bind.

## Preservation, final sweep and handoff

After each batch, run the smallest meaningful owner/sibling proof and applicable formatting/diff checks, then canonical full local verification of the exact candidate before submission/readiness review. Preserve required native coverage/report integrity, per-platform proof, same-run task measurements, artifact/version evidence and frozen-file checks. Missing proof is a gap. Changed inputs renew affected checks and review; valid unchanged evidence need not be duplicated.

Fresh independent route-required reviewers compare every removed or consolidated obligation against its keeper, challenge vacuous/rejection assertions and permitted positive inputs, and verify that no contract lost its sole proof. Optional mutation experiments need explicit permitted product ownership and restored-input verification; they are never required and cannot run in blind A/B.

After the final correction, obtain a fresh independent read-only sweep over the declared scope and the exact passing candidate. Resolve or reject every actionable finding with evidence and renew affected checks/reviews until the final sweep reports none. This may be included in fresh D or bounded review when its packet covers preservation and the final audit scope. A diagnostic sweep before passing verification is no acceptance verdict. Report unresolved material decisions or external-authority blockers; do not call them clean. “No issues found” is limited to inspected scope and evidence, not a universal correctness claim. No extra sweep phase is required for ordinary authoring alone.

Hand off scope/exclusions, baseline and candidate/checkpoint identities, declaration ledger, obligation-to-keeper mapping, findings/dispositions, retained false positives, production versus test/support changes, intended pre-fix failure evidence or its absence, focused/full commands/results and remaining limits. Link the single Current state and cumulative per-role rounds/corrections/launches/spending; missing metering is unknown and human limits absent are not set. Final hashes/results stay outside tracked candidate bytes. Commit/push/PR/merge/release require their actual authorization and normal gates; audit completion grants no external authority.

Adapted from OpenClaw's pinned test-audit skill, campaign and boundary writing guide; [provenance and adaptation notes](../../../docs/agentic-software-delivery-v1.0/REFERENCES.md#r10--openclaw-test-audit) explain differences. Preserve the [upstream MIT notice](references/openclaw-MIT.txt).
