# naming-conventions: Consistent branch, issue and PR names

**Version 1.0** Git versions revisions.

## Contract

- Human request: “we need to codify branch and issue and PR naming formats”.
  The attached repository is `david-hoffman/simrecon`; baseline
  `d48e0e4`. This authorizes the documentation convention and its review.
- Follow-up request: “get the pr up” authorizes committing, pushing this branch
  and opening its PR after the existing exact-candidate full verification gate.
  Submission is rebased onto `02bb2c9`, which adds reader-environment documentation.
- Route: policy amendment. Coordinator owns the specification section, shared
  AGENTS instructions and template, project/GitHub guidance, task/PR templates,
  this task record and a scoped lesson. A fresh independent policy reviewer
  assesses the complete documentation diff before activation.
- Outcome: one canonical grammar, shared purpose types, optional title scopes,
  concrete examples, issue linkage and compatibility/transition rules.
- Scope excludes runtime, tests, workflows, settings, commit-message/release
  automation, existing remote-item renaming, merge and release. Publication is
  limited to this PR under the follow-up request. Existing scientific contracts,
  coverage policy, role boundaries and exact-candidate gates remain binding.
- Checks: whitespace/diff checks; local Markdown target/anchor checks for changed
  references; exercise documented branch examples with `git check-ref-format`;
  independently review grammar, examples, authority and cross-document agreement.
  Product tests are not evidence for naming prose. Full `make verify` remains
  required before any future PR submission under the existing gate.
- Branch: `docs/naming-conventions`. No issue opened or required. Proposed PR
  title: `docs(delivery): Define branch, issue and PR naming conventions`.
- PR presentation: explain inconsistent naming and the resulting formats in
  plain English; a format/example table suffices, so no figure is needed.
- Policy reviewer selection: `gpt-6.1-sol`, high, per project model guidance;
  fresh session without author history. Actual served attribution and unavailable
  token/cost/time measurements remain unknown. Author uses the current session.
- Human-set review, time and spend limits: not set. Retain all attempts.

| Scenario | Required documentary outcome |
|---|---|
| Local issue or none | Valid branch syntax without inventing an ID or requiring issue creation |
| Typed/scoped titles | Shared vocabulary, optional scope, problem/outcome versus implemented-change wording |
| Partial, stacked or multiple-issue work | Stable primary branch ID, distinct slice slugs, explicit references/closure |
| Breaking change | PR marker plus migration explanation, preserving substantive review |
| Adoption and enforcement | Existing names retained; manual convention accurately distinguished from installed gates |

## Current state

Documentation formats and entry-point reminders are implemented. Final diff
identity, required independent acceptance verdict and check results are reported
in the conversation rather than written into the candidate after verification;
use that receipt for acceptance status. Discovery found mixed `codex/`
and `intake/` branches and plain titles in recent PRs 96, 98, 101–103; these are
examples of prior practice, not items authorized for renaming.

Accounting: one coordinator author session and one preliminary naming advisor
(not an acceptance reviewer). Policy review 1 rejected the missing template
installation rewrite for the new naming link; one correction adds the third
root-relative rewrite. Fresh independent review 2 accepted the corrected diff.
Publication adds one presentation advisor and a fresh independent review 3 of
the final candidate, including this authorization record and updated base;
its verdict belongs in the conversation/PR receipt. Metering, monetary cost and detailed
elapsed/owner-wait time are unknown. These counts retain the first review and
correction. One overbroad whole-template equality probe failed on pre-existing
test-audit guidance differences; the corrected check verifies the three documented
link rewrites and the new naming paragraph, preserving unrelated baseline text.
Publication requires fresh review acceptance and full verification of the clean
exact commit. Final hashes, full-check attempts/results and remote PR state go
in the conversation/PR receipt without modifying the verified candidate.

Completion housekeeping: keep the current checkout containing the deliverable.
No additional worktree or task fixture is needed. Retain canonical verification
receipts and phase logs as evidence; remove only confirmed disposable task scratch
after publication. Shared environments and unrelated files are retained. Final
cleanup results belong in the conversation/PR receipt.
