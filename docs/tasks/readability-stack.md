# Human-readable codebase: stacked cloud-task handoff

## Authorization and execution model

The owner authorized implementation on November 9, 2026 (America/Los_Angeles):
“let's kick it off, one pr with subsequent ones stacked on each other. Each pr
started in a new cloud task. Go!” This supersedes the earlier analysis-only
restriction for the planned restructuring. It does not authorize merging PRs.

Each PR must begin in a **new Codex cloud task**, with its own checkout and fresh
context. A subagent in the current chat is not a replacement. Do not start the
dependent task until the preceding task has finished its scoped implementation,
required review, and exact-candidate verification, pushed its branch, and opened
its PR. Each successor PR targets the preceding PR's branch, not `main`.

This file is a handoff, not a replacement for AGENTS.md or PROJECT.md. Each task
selects the repository's applicable risk/review route and prepares its narrow
contract. Preserve the owner-approved coverage policy and all existing gates.

## Source and artifact provenance

The analysis was performed at `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`.
The remote `main` head observed at kickoff is
`0ea11a5876549bf26a3a813009b97c09decc806d` (PR #87).
The latter changes verification fixtures and `_pytest_policy.py`; retain those
changes. Recheck source inventory and source links against the actual task base.

Task 01 carries and completes these preparation artifacts:

- [Restructuring specification](../plans/human-readable-restructure.md).
- [Mathematical walkthrough](../architecture/reconstruction-walkthrough.md).
- `docs/figures/readable-reconstruction/phase-separation.svg`.
- `docs/figures/readable-reconstruction/band-relocation.svg`.

The preparation branch is explicitly **incomplete and not PR-ready**. Its purpose
is transporting existing drafts to the first new cloud task. No full `make verify`
result is claimed for it, and no PR is opened from this coordinator session.

## Ordered tasks

The names below are intended new branches; verify absence before creating them.
Use the actual observed predecessor branch/head if a name has changed.

| Task | Proposed branch | PR base | Scope and outcome |
| --- | --- | --- | --- |
| 01 Documentation foundation | `codex/readability-01-docs` | `main` | Finish current reader map, README data-flow diagram and links, reviewed math walkthrough/figures, explicit old-to-new module map, and stack contract. No runtime/test/configuration changes. |
| 02 Tooling separation | `codex/readability-02-devtools` | Task 01 branch | Move doctor launcher and pytest policy to a narrow development-only package in this repository; preserve `delivery doctor` and strict pytest behavior; product wheel excludes harness code. Reconcile owned measurement, tooling, lock and artifact paths explicitly. |
| 03 Package structure and #81 | `codex/readability-03-packages` | Task 02 branch | Move whole modules into the proposed shallow domain packages and remove leading module underscores together. Preserve dunders, public exports, CLI and scientific behavior. Update every static/dynamic consumer and source link once. |
| 04 Preparation readability | `codex/readability-04-preparation` | Task 03 branch | Name meaningful preparation/acquisition operations, improve docstrings/comments, link equations and conventions. Any larger extraction is a separately scoped successor, not an incidental algorithm rewrite. |
| 05 Optical transfer readability | `codex/readability-05-optical-transfer` | Task 04 branch | Clarify declaration, sampling and bead-preparation operations with the same behavioral constraints. |
| 06 Estimation readability | `codex/readability-06-estimation` | Task 05 branch | Clarify overlap construction, finite search and modulation fitting with units, signs and diagnostics. |
| 07 Filtering and assembly readability | `codex/readability-07-reconstruction` | Task 06 branch | Clarify native filtering, quadrature recombination, carrier relocation, inverse normalization and signed output. |
| 08 Workflow and I/O readability | `codex/readability-08-workflow-io` | Task 07 branch | Clarify orchestration/adapters and missing neutral-function docstrings; make names understandable and finish current-source navigation. |
| 09 Standard Serena tooling | `codex/readability-09-serena` | Task 08 branch | Complete issue #86 against settled paths: pinned reproducible setup, read-only navigation, fresh-task/subagent instructions, state outside the product. |

The package-map task explicitly includes issue #81; do not first do a redundant
underscore-only import migration. The tooling task chooses a development-only
package to preserve the installed development command. This supersedes the
earlier proposal's tentative scripts-only default. Avoid a separate repository,
general delivery framework, or product shim importing repository-only tools.

Named scientific operations should use readable ordinary names; preserve the
documented top-level API as the supported compatibility boundary. Do not turn
every newly unprefixed helper into a stable API promise. No scientific feature,
numerical fix, blanket test rewrite, weaker gate or retired API revival is included.

## Per-task completion and successor launch

1. Read AGENTS.md, current PROJECT.md, this packet and the narrow relevant sources.
   Fetch and verify the actual predecessor head and ancestry before editing.
2. Record scope, route, ownership and relevant checks. Use fresh independent
   reviewers and required native scientific roles according to repository rules.
3. Implement only this task. Preserve the 36 documented package exports unless a
   later authorized contract explicitly changes that boundary. Preserve scientific
   signs/scales/order, input domains, errors, ownership and diagnostic information.
4. Run required checks and `make verify` on the clean exact candidate before
   opening any PR (including drafts). Do not reuse a predecessor's passing receipt
   as verification of changed bytes. Diagnose environment failures without changing
   product behavior or lowering a gate.
5. Push the task branch and open one PR against the actual predecessor branch.
   Use the repository's PR template; state the dependency prominently. Do not merge
   or enable auto-merge. If the predecessor changes, reconcile and reverify before
   claiming the child current. Preserve local evidence and cumulative attempts.
6. Return the cloud task URL/ID, PR URL/number, head branch/SHA/tree, base branch/SHA,
   scope, independent review evidence, full verification receipt/command/status,
   unresolved limits, and the next task's exact input baseline.
7. Launch the successor as a genuinely new cloud task only after step 6 is complete.
   Pass a narrow packet containing these identities, this authorization, the next
   scope, and preserved gates. Do not start a second PR in the same task. If task
   launching is unavailable, report that blocker and retain the packet; do not
   silently substitute a local process, subagent or invented task URL.

When a parent is later merged, confirm the actual merge commit and restack/retarget
children deliberately. Squash merges do not preserve parent commit ancestry.
Do not force-push someone else's work or delete branches during this rollout.

## Important migration checks

- Traceback context currently depends on literal module names and local `t`/`d`
  names; preserve time/direction error context during module and variable renames.
- Console scripts, pytest plugin strings and fixture subprocesses require text
  searches in addition to Serena symbol references.
- Preserve current #87 pytest policy/affinity and observer changes. The earlier
  source inventory is historical, not permission to restore old test infrastructure.
- Relocating harness code must preserve measurement of every owned file and
  subprocess. Keep the sole product wheel contract explicit; build development
  package artifacts separately if needed.
- Verify installed product behavior outside the checkout with only runtime
  dependencies. Doctor invocation and pytest plugin loading must still work in
  their actual temporary caller environments.
- Documentation/source links move with symbols. Keep conceptual figures clearly
  distinguished from scientific validation and historical C-executable agreement.

## Task 01 contract and evidence pointer

Route: non-normative documentation with fresh-context mathematical/inventory
advisors and independent final documentation review, required by this task.
This is not scientific implementation or policy activation. The worker owns
`README.md`, the walkthrough, its two SVG figures, the restructuring map and this
handoff. No runtime, tests, dependency, configuration or verification-gate edits.
Preserve current `main` and all 36 exports. No merge or auto-merge.

Checks: source-derived equations and conventions, conceptual figure labels and
rendering, local Markdown targets/anchors and source-line bounds, full module
inventory/map, unchanged non-documentation baseline, whitespace, then the clean
committed candidate's full `make verify`. An independent reviewer checks the
candidate and applicable evidence before submission. Exact final head/tree,
base, verdict and receipt go in the PR/conversation rather than changing verified
tracked bytes. Detailed local evidence is retained in ignored
`artifacts/readability-01/` and `artifacts/verification/`.

## Task 02 launch packet

The completing coordinator must fill the exact Task 01 PR URL, verified pushed
head SHA/tree and observed base SHA into the next-task prompt outside tracked
bytes. Start only from that head in a **new cloud task**, after Task 01 review,
verification, push and PR creation. Fetch and confirm identities before editing.

Create `codex/readability-02-devtools`, targeting `codex/readability-01-docs`.
Read AGENTS.md, PROJECT.md, this handoff and the module map. Implement Task 02
only: move doctor launcher and pytest policy to a development-only local package,
preserve `delivery doctor`, current strict pytest policy/affinity and #87 observer
changes, exclude harness modules from the product wheel, and explicitly reconcile
locked installation, all owned-file/subprocess measurement, tooling roots and
separate artifact paths. Inventory temporary caller environments and dynamic
import strings. Choose the applicable repository route and fresh required roles;
advisors do not replace independent review. No scientific changes or weaker gates.
Commit and fully verify the exact candidate before opening the stacked PR; no
merge or auto-merge. Return evidence and then launch Task 03 in another new cloud
task, or provide its prompt if launching is unavailable. Never implement Task 03
in Task 02's task.

## Current state

Task 01 is executing in a new cloud task on `codex/readability-01-docs`, from
seed `ac2b0d65f239fb5f628792ae58af13ea1da868bf`. Remote fetch/ls-remote confirmed
`main` at `0ea11a5876549bf26a3a813009b97c09decc806d`, already an ancestor of the
seed; PR #87 is preserved. The GitHub connector confirmed repository identity
`david-hoffman/simrecon` (repository ID 1398550280). Task URL is not exposed by
this runtime; do not fabricate one.

Documentation is prepared for candidate review and full verification; exact
completion outcomes are attached to the final PR/conversation. Two fresh Sol/high
advisors checked mathematics and inventory; corrections clarify bead compensation,
interpolation boundaries and phase-slot labels, refresh 7,805 source lines and
reconcile the full 25-module map with the authorized sequence. The 36 exports and
scientific source are unchanged. A separate fresh independent final reviewer is
required; advisor findings are not that verdict.

Environment preflight passed using Python 3.13.12, uv 0.12.19 and existing Temurin
21.0.7+6 via `SIMRECON_JAVA`. Earlier attempts diagnosed default Java 21.0.13 and
sandbox proxy access failures; no gate was weakened. Git operations require the
supported escalation path here. The `gh` API returned 403, but the GitHub connector
works. The official `codex cloud list` failed; an escalated connectivity check
confirmed proxy HTTP 403 for `chatgpt.com`. If that remains unresolved after PR
creation, return the filled Task 02 prompt; do not substitute a subagent or local
process. No successor has been launched.

Cumulative accounting is retained: original analysis had eight fresh-context
agent tasks including two independent document reviews; kickoff had one fresh
read-only packet advisor, two cloud-list attempts and one connectivity probe.
Task 01 adds two report-only documentation advisors, one environment advisor,
one preliminary independent review, and the fresh correction review reported
with the final candidate. The preliminary review found generated SVG trailing
spaces in the full seed-to-main diff; these were removed without changing the
figure geometry. The first full verification was interrupted during tests for
this documentation correction (incomplete, not passing); the corrected committed
candidate requires a fresh full run. Preflight had
two failed attempts (default Java; sandbox fetch) before one passing run. The
initial Git fetch failed in the sandbox; escalated fetch succeeded. One local
SVG-render attempt lacked its delegate and one cached retry hit a read-only cache;
the supported escalated isolated renderer supplied previews
without changing project dependencies. Task 01 cloud discovery/probe attempts:
one each, both failed. Human-set budgets: not set. Per-role token counts, monetary
cost and complete elapsed/wait measurements: unknown. Role settings are requested
Sol/high; actual serving attribution is unavailable.

Cleanup: removed the task-owned temporary editing/check scripts and duplicate
preflight log after preserving the check script and logs under ignored evidence.
Moved the cloud launcher’s generated `error.log` into that evidence directory.
Retained the current checkout, required environment/cache, reader inputs and
durable ignored review/verification evidence. No cleanup error; no unrelated work,
tracked fixtures or predecessor branches were removed. Final verification
artifacts are retained for the next task.
