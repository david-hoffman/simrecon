# Human-readable codebase: readability-stack handoff

## Authorization and execution model

The owner authorized implementation on November 9, 2026 (America/Los_Angeles):
“let's kick it off, one pr with subsequent ones stacked on each other. Each pr
started in a new cloud task. Go!” This supersedes the earlier analysis-only
restriction for the planned restructuring. It does not authorize merging PRs.

On November 10, 2026 the owner explicitly replaced only the execution-location
requirement: one cloud session coordinates the remaining stack, launching one
fresh-context per-PR coordinator at a time with `fork_turns="none"`. Each coordinator
owns one PR, one worktree and an isolated development environment and runs the
applicable repository ASD process. Earlier new-cloud-task instructions below and
in the roadmap are retained historical instructions superseded only on this point.
The stack coordinator owns sequencing, remote checks, handoffs and cumulative
accounting. No general orchestration framework is authorized.

On November 11, 2026 the owner clarified execution again: the stack root spins
up fresh per-PR subcoordinators, each runs ASD and opens its one PR before the
next starts, using subagents and worktrees as needed. For this authorized stack,
fresh collaboration subagents with `fork_turns="none"` carry A/B/C/D roles;
this narrowly supersedes native-launcher requirements, not the selected route,
independence, blind public packets, separate ownership, verification or accounting.
Role workers/reviewers work directly and do not delegate. Native CLI
authentication repair and cloud-task launcher retries are no longer prerequisites.
Do not begin the next PR until its predecessor is committed, fully verified,
independently accepted, pushed and opened. Successors target that verified
predecessor branch. Pending CI is not passing. No merge or auto-merge.

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

## Task 01 retained execution accounting

Historical pre-verification pointer (completion evidence is PR #88). Task 01 is executing in a new cloud task on `codex/readability-01-docs`, from
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

## Task 02 contract and evidence pointer

Authorized route: bounded conventional infrastructure maintenance, with one named
code/test/infrastructure worker and a fresh independent final bounded reviewer.
A fresh report-only tooling advisor checks consumer inventory and route; advice
is not acceptance. Launcher arguments, doctor permissions, strict pytest outcomes,
#87 affinity/observers, science and all 36 public exports retain their behavior.
No new scientific, binary, security or delivery-policy meaning is authorized.

Code ownership: the two relocated harness modules and new local `devtools/`
package metadata; root `pyproject.toml`, `uv.lock`, `Makefile`; owned measurement
inventory in `scripts/verify.py`; narrow installed-artifact checking and its
infrastructure tests/fixtures; CI artifact retention only. Documentation ownership:
this handoff, current PROJECT/environment/verification guidance, live module-map
links and a unique evidence-linked lesson if useful. No scientific source/test
rewrite, new thresholds, reduced discovery, product shim or general framework.

Concrete obligations and checks:

- Locked all-groups install provides `delivery` and the explicit pytest plugin
  in temporary caller environments, without a product dependency on devtools.
- Keep doctor arguments/output/status/missing-executable behavior; retain public
  console tests and strict serial/two-worker runner tests, #87 affinity and child
  shard preservation. Move the two implementation bodies intact.
- Include every development source in lint/format/types and native per-file,
  per-package/global coverage. Check never-imported and missing/excluded report
  cases as well as relevant subprocesses. Percentages remain advisory.
- Keep one product wheel in `dist/`; build/check the development wheel separately
  in `artifacts/devtools/dist/`. Inspect installed product exports, CLI and absence
  of harness imports/dependencies outside the checkout with only runtime packages.
  Check development console/plugin installation separately.
- Preserve all 13 full verification phases, report protections, same-run M25 and
  supported-platform CI. Commit first, then run full `make verify`, then obtain
  fresh exact-candidate independent acceptance before submission.

Final identities, complete commands/results and review verdict belong in the
PR/conversation, outside verified tracked bytes. Durable ignored evidence lives
in `artifacts/readability-02/` and the usual coverage/verification directories.
Task 03 may start only in another genuinely new cloud task from the exact pushed,
verified Task 02 head, targeting `codex/readability-02-devtools`.

## Task 02 retained pre-verification state

Task 02 is executing in a new cloud task on `codex/readability-02-devtools`.
Predecessor PR #88 is open, unmerged, at verified pushed commit
`d4ae74785460039eef911dec02ac98be6394c922`, tree
`abae50021f597fcb549398d9080e9c50cfc57c3f`; remote main remains
`0ea11a5876549bf26a3a813009b97c09decc806d`, its ancestor. Explicit remote
refs confirm these identities; no restacking was needed and no newer changes
were discarded. The remote Task 02 branch was absent at intake. Predecessor CI run 42884406794 completed successfully on both configured
platforms; final remote state is rechecked before submission.
The cloud CLI discovery attempt returned HTTP 401 (authentication token could
not be parsed). No successor launch is claimed; supply a filled next-task prompt
if this remains blocked. Task URL/ID is not exposed; environment identity is not a cloud task identity.

Pinned Python 3.13.12, uv 0.12.19 and Temurin 21.0.7+6 were checked in this
new environment. `SIMRECON_JAVA` selects the pinned Java executable. No earlier
filesystem path was accepted without probing it. The initial sandbox Git fetch
failed on proxy connectivity; an escalated fetch succeeded but did not create
the intended tracking ref under the checkout’s fetch configuration. An explicit
refspec then confirmed the predecessor. No verification gate was changed.

Cumulative prior analysis/kickoff/Task 01 accounting above remains retained.
Task 02 adds one fresh report-only tooling advisor, one bounded implementation
worker, coordinator setup/documentation and the fresh independent final review
reported with completion. The worker recorded 11 failed commands: six environment
(offline lock once, sandbox builds three times, sandbox Pyright twice including
its diagnostic), three lint/format commands, one nonexistent-test invocation and
one authored test-expectation defect. Three author correction batches fixed
formatting twice and the protection test expectation once. Focused runs passed
28 and 263 tests plus three final targeted cases (overlap, not a distinct-test
sum); `make check preflight`, both builds and actual `make wheel-import` passed.
Coordinator setup adds one failed sandbox fetch, one tracking-ref resolution
failure after a successful fetch, and one failed cloud discovery (HTTP 401).
Full-run attempts and final review/launch outcomes are reported with completion. Human-set budgets: not
set. Token/cost and actual served-model attribution: unknown; fresh role requests
use Sol/high. A reviewer is not the advisor or worker and inherits no author chat.

Cleanup retains the current checkout, required environment/cache/reader inputs
and durable ignored evidence. Task-created temporary caller/install environments
use scoped temporary directories; any remaining uncertain scratch is preserved.
Final cleanup details and errors are reported outside verified tracked bytes.
No second PR, merge or auto-merge is authorized in this task.


## Task 02 completion retained at stack resumption

PR #89: `codex/readability-02-devtools`, head
`6627f33cc718b1da1cb7b35a620d22655848ae91`, tree
`13e8a10462cf2eea4e16ab703dd0a2d188b234aa`; base Task 01 head
`d4ae74785460039eef911dec02ac98be6394c922`, tree
`abae50021f597fcb549398d9080e9c50cfc57c3f`. First full verification passed all
13 phases: 3,071 tests, 47 warnings, all 32 owned files measured, both installed
wheel checks passed, same-run M25 increment 0 bytes against 33,554,432 bytes.
Receipt SHA256: `96a3440933dacde340caff8395793386cab3d73c1e1250a15dd28f76ac6494af`.
Fresh independent final acceptance required no corrections. PR #89 retains exact
command, coverage integers, artifacts and review provenance. Earlier ignored
artifacts are not presumed present or reusable in this session.

Task 02 totals: one tooling advisor, one bounded worker, one independent final
reviewer; eleven worker failed commands resolved by three author correction
batches plus environment repairs; two coordinator Git failures, one cloud
discovery authentication failure; one reviewer optional absent-file read; one
passed full run, zero failed full runs; one accepted final review, zero requested
corrections. Earlier analysis/kickoff/Task 01 charges above remain intact. No human
numeric budgets were set; unavailable token/cost/served-model data stays unknown.

## Task 03 contract and evidence pointer

Authorized scope is Task 03 and issue #81 together: move whole product modules
according to the [approved shallow module map](../plans/human-readable-restructure.md#explicit-old-to-new-module-map),
remove leading module underscores, and add minimal package initializers without
eager aggregate imports. Preserve dunders, all 36 facade exports, neutral CLI,
scientific input domains/signs/scales/order, array ownership, exception hierarchy
and time/direction diagnostic information. No algorithm extraction,
simplification, compatibility shims, public API expansion or Task 04 work.
Update static and dynamic consumers, console strings, fixture subprocesses and
all live documentation/source links once. Historical accounting and scientific
claim limits remain intact.

Route: **high risk**, because this whole-product migration changes substantial
module interfaces and qualified identities across scientific domains, including
literal traceback-module matching. Keeping numerical bodies unchanged reduces
implementation scope but does not remove those risks. Required sequence is fresh
blind A, fresh blind B, restricted C, committed exact-candidate `make verify`,
then fresh independent D, using owner-authorized collaboration role subagents
with `fork_turns="none"` under the November 11 execution clarification. Requested model/effort is `gpt-6.1-sol`/high for those
roles under current project calibration; actual attribution/metering is recorded
only when observed. A/B use only public packets, approved interface/expectation
sources, exact permitted tests and source-free diagnostics. Shared filesystem
restrictions are prompts, not engineered blindness. Each role works directly,
with supported memory/delegation disabled and no further roles.

Planned ownership: A owns the named migration tests/fixtures and requirement
mapping; B reviews that checkpoint independently. C owns only the mapped product
modules, facade imports and minimal package initializers, preserving frozen
tests/fixtures and all delivery/configuration boundaries. Static/dynamic
test-consumer changes stay with A and require B acceptance. Any necessary console,
script or installed-artifact infrastructure edits require a separately named
bounded owner and fresh independent assessment, preserving the highest-risk
candidate route; C gains no infrastructure ownership. The coordinator owns this
contract/state, live documentation links and PR presentation. Exact role packets,
frozen identities and consumer inventory are recorded in the role evidence.

| ID | Observable obligation / expected boundary | Expectation source | Required evidence |
| --- | --- | --- | --- |
| T03-1 | Approved whole-module destinations and minimal initializers load without circular imports; 36 facade exports and dunders survive. | Owner request, approved module map and PROJECT public boundary. | A mapping/B audit; static inventory; installed product checks; D review. |
| T03-2 | Neutral file APIs and CLI retain normal, invalid-input, representation-limit and operation-time failure outcomes. | Existing neutral public contracts and retained tests. | A/B preservation mapping; full suite; runtime-only installed CLI/API proof. |
| T03-3 | Scientific preparation, transfer, estimation, reconstruction and workflow retain accepted domains, units, signs, scaling, order and ownership. | Existing CE02–CE07 contracts and retained tests. | A/B mapping of retained scientific obligations; unchanged algorithm-body review; full suite; D risk audit. |
| T03-4 | Exception hierarchy and workflow time/direction context survive qualified module changes, retaining local `t`/`d` semantics. | PROJECT and roadmap migration hazards. | Public failure outcomes and literal-context consumer inventory; B/D review. |
| T03-5 | Every actual static/dynamic consumer, console entry and fixture subprocess resolves the new module paths. | Owner request and retained caller contracts. | Text/import inventory, actual caller execution, A/B test-consumer checkpoint and named infrastructure review. |
| T03-6 | Development-only doctor/plugin, locked install, #87 policy/affinity/observers and product/dev wheel separation retain behavior. | Task 02 contract, PROJECT and PR #87 baseline. | Existing runner/installed-artifact checks; full gate; fresh D review. |
| T03-7 | Every owned file and relevant subprocess remains measured with fresh consistent per-file/package/global reports and same-run M25. | PROJECT coverage/verification policy. | All 13 phases, receipt, exact native integers, installed wheel proof and M25 ≤33,554,432 bytes. |
| T03-8 | Live documentation/source links follow moved files while supported API and scientific claim limits stay clear. | Owner request and roadmap. | Link/anchor/source-location checks; whole diff and D review. |

Equivalent examples and exact test mapping are pending A/B, not invented at
intake. Coverage remains approved behavior coverage plus independent risk review;
no percentage target is selected. Mandatory native statement/branch measurement,
never-imported files, subprocesses, report integrity and independent Ubuntu 24.04
and macOS 15 reports remain binding; percentages are advisory. No platform union,
weaker gate or reused predecessor receipt certifies the changed candidate.

Before dependent work, establish fresh role availability and the isolated pinned
locked environment. Before submission, prepare the sole state pointer, commit the
candidate, pass full `make verify`, obtain fresh D acceptance, recheck remote
base/head/ancestry, push and open the stacked PR using the repository template.
Exact final hashes/results belong outside tracked bytes. The PR will describe
the navigable package structure and preserved behavior in plain language, with
technical evidence in the template appendix; no new figure is needed for file
moves. No merge/auto-merge, release or next-task implementation is authorized.
Human-set numeric limits: not set. Missing tokens/cost/served attribution remain
unknown. Preserve this checkout/environment and durable ignored evidence; no
confirmed disposable task scratch exists at intake.

## Task 03 historical intake evidence

At the original Task 03 intake in the owner-authorized single-session stack model. Worktree:
`/workspace/simrecon-readability-03`, branch `codex/readability-03-packages`, from
confirmed Task 02 head above, targeting `codex/readability-02-devtools`.
Remote checks on November 10 confirmed PR #88 and #89 open/unmerged and matching
heads/trees; main remains `0ea11a5876549bf26a3a813009b97c09decc806d`.
Main → Task 01 → Task 02 ancestry verified. Task 03 remote branch absent.
Task 01 CI run 42884406794 and Task 02 CI run 42889880212 succeeded; Task 02
Ubuntu 24.04 and macOS 15 jobs both passed. No restacking or newer-change loss.

Historical blocker, superseded by the November 11 owner execution clarification: required native-role authentication failed before authoring.
The high-risk route and Task 03 contract above remain selected. Native CLI is
`/opt/codex/bin/codex`, version 0.167.0-alpha.4; help/version and supported launch
controls were rechecked. The minimal non-review capability probe used
`--ignore-user-config --disable memories --disable multi_agent --ephemeral
--sandbox read-only --model gpt-6.1-sol -c 'model_reasoning_effort="high"'
--json -C /tmp --skip-git-repo-check`, with a no-tools/no-files/no-delegation
prompt. The first attempt failed local initialization with read-only filesystem
status 1. After diagnosing the read-only session home, the supported escalated
retry reached the service and failed with HTTP 401, “Could not parse your
authentication token”; the turn failed because the access token could not be
refreshed after logout/account change. Ancillary MCP startup returned HTTP 451
`no_biscuit_no_service`. This is a request-level native `codex exec` failure,
distinct from the earlier cloud-task launcher 401. No model response or native
role verdict exists; actual served model and metering are unknown. Do not retry,
repair credentials. Fresh collaboration A/B/C/D roles are now authorized by the owner clarification above.

Durable ignored evidence is `artifacts/readability-03/`: remote metadata in
`stack-intake-remote.json`; probe stdout/stderr in `native-capability.jsonl`,
`native-capability.stderr`, `native-capability-escalated.jsonl` and
`native-capability-escalated.stderr`; setup logs in `preflight-sync.log`,
`preflight-sync-escalated.log` and `preflight.log`. Environment status was current,
connected and running with network policy enforced; no configured secret,
runtime-variable or outbound-identity binding was reported. This does not prove
native CLI authentication. No credential values were inspected or changed.

Pinned uv 0.12.19 and Python 3.13.12 were actually probed through
`/workspace/.simrecon-tools/activate.sh`. A new worktree `.venv` was created.
The initial locked all-groups sync failed at the sandbox proxy; the supported
escalated retry passed and installed the two local distributions plus their locked
dependencies. Cheap canonical preflight passed with status 0:
`source /workspace/.simrecon-tools/activate.sh` then
`make preflight UV=/workspace/.simrecon-tools/uv-env/bin/uv`, through the supported
escalated execution path. It verified the current-worktree Python 3.13.12 `.venv`,
editable product import, NumPy 2.5.3, h5py 3.16.0, pinned ImageJ reader preparation
and isolated hatchling 1.32.4 build environment. It is prerequisite health, never
full-candidate acceptance. No Task 03 receipt, coverage integers, M25 measurement,
wheel acceptance, independent review or CI result exists.

Stack intake charges so far: one failed sandbox Git fetch (proxy unreachable;
escalated fetch succeeded); one failed default uv inventory (read-only cache);
two file-inventory commands returned nonzero for absent/optional paths. Native CLI
help/version emitted read-only PATH-alias warnings but returned successfully.
Task 03 coordinator adds two optional/absent-path command failures (a misspelled
role-skill path and the initially absent `.venv` inventory), two failed native
capability attempts (local initialization; external authentication), one failed
sandbox locked sync, one successful escalated locked sync and one passed
canonical cheap preflight. Help/version
read-only PATH-alias warnings did not fail those commands. All prior analysis,
kickoff, Task 01, Task 02 and stack-intake charges above remain intact. At that historical handoff no A/B/C/D
author/reviewer had been launched; no native model response, review, implementation
correction or full verification run exists for Task 03. Budgets: not set.
Per-role tokens/cost, actual served-model attribution and complete elapsed/wait
measurements: unknown. At that handoff no product/tests/configuration had been edited and no commit,
push, Task 03 PR, merge or auto-merge was performed.


## Task 03 resumed execution accounting

The November 11 owner clarification authorizes fresh collaboration role agents,
with `fork_turns="none"`, requested Sol/high, and no nested delegation. This
replaces only the native launcher prerequisite. Two failed native capability
attempts above remain charged; authentication was not retried or repaired.
The coordinator rechecked PR #88/#89 open/unmerged identities, fetched the exact
stack, verified ancestry and observed Task 03 remote branch absent. Python
3.13.12 and all 36 facade exports load in the existing isolated environment.

Fresh blind A added 29 migration cases across two files: 22 approved module
moves, exact exports, four error-hierarchy cases and two actual preparation/
estimation failures at time 1/direction 1, each after a positive public workflow
call. All previous scientific oracles/fixtures remain unchanged. No active old
module consumers existed in tests; retired-module absence assertions remain.
A's initial run had 22 intended new-path failures plus one unapproved version
attribute assertion; A removed that test defect. Corrected behavior subset:
10 passed, 22 structural cases deselected. Narrow Ruff lint/format passed.
Three narrow Pyright invocations failed dependency import resolution in the
sandbox. Coordinator's supported escalated pinned locked Pyright command passed
with zero errors/warnings and no edits. A accounting: one author, four failed
checks, one authored test correction and two diagnosed type-command adjustments;
no product correction or implementation exposure. Exact hashes, risk mapping,
commands and limits: ignored `artifacts/readability-03/a-report.md`.

Fresh blind B independently reproduced the 10-case subset and found one concrete
oracle defect before C: equalizing phasewise-constant positive-control frames
removes true side-band energy, leaving roundoff-only positive overlap energy.
The baseline pass therefore did not robustly establish a permitted-positive
control across legitimate arithmetic/platforms. A corrected only the preparation
input with an exact zero-sum spatial stripe that survives equalization, preserving
real time/direction failure expectations. All five workflow-failure cases, narrow
Ruff and supported pinned Pyright passed. Two A authored defects/corrections
remain charged; no new failed check in this correction. Fresh B2 correction
review accepted the exact revised checkpoint and retained unchanged evidence
applicability. Its independent analytic control has actual finite energy, not
roundoff, and its source-free selected run passed 10 cases (22 structural rows
still expected to fail before C). Reports: `b-review.md` and `b2-review.md` under
`artifacts/readability-03/`. B totals: two fresh reviews, one nonacceptance and
one accepted correction, one concrete oracle finding, one absent-path read,
no B edits or exposure. Structural/export/hierarchy assertions
align with the approved contract. This finding is a test defect, not a product
failure or new requirement; implementation had not begun at that finding.

A separate bounded infrastructure author changed exactly two path literals:
the console entry point and installed-wheel expectation. Lock check, narrow
Ruff, syntax/probe compilation and whitespace checks passed; lock and all gates
remain unchanged. One author attempt, no corrections or failed checks. Report:
`artifacts/readability-03/infra-author.md`. Installed acceptance and fresh
independent infrastructure review remain pending the passing full candidate.
The coordinator owns live source links, current package navigation and this
handoff; one optional absent-glob inventory command returned status 2 during
coordination. All prior charges remain. Human budgets: not set. Requested role
configuration is Sol/high; actual served attribution, tokens, money and complete
elapsed/wait totals are unknown. The first B audit requested a concrete oracle correction; fresh B2 accepted it
before C. No Task 03 full verification or PR exists yet.

C completed 22 whole-module moves, the root facade import update and four minimal
initializers. Two qualified context literals changed; all algorithms, signatures,
helper/local names and existing docstrings were preserved. Existing Ruff rules
required 27 new concise docs (23 functions/methods, four classes) after underscore
removal; imports were sorted. Independent normalized AST/import comparison matches
all 23 original files, preserving 203 definitions, 36 classes and 1,902 per-definition
local store/delete occurrences. The 27-module/89-edge dependency graph is acyclic.
C focused checks: 494 migration/workflow cases and 25 neutral conversion cases
passed, with M25 deliberately left for the mandatory same-run full gate. Product
lint/format/types passed; 91 other test/fixture files, lock and frozen hashes
remain exact. C accounting: one attempt, one diagnosed lint correction batch,
one failed initial lint check, no failed tests/types or numerical corrections.
Reports: `c-report.md`, `c-ast-check.py`, `c-ast-preservation.json` in durable
`artifacts/readability-03/`.

Coordinator verified 113 local documentation targets and 38 source-line links
against byte-identical baseline source lines, refreshing the sole changed anchor.
Current module examples and two active contract implementation-path references
follow the moved modules; scientific contract meaning is unchanged. No decorative
figure is needed for these file moves. C's three confirmed disposable scripts
(`/tmp/task03-c-move.py`, `/tmp/task03-c-docstrings.py`,
`/tmp/task03-c-ast-check.py`) were removed with existing commands after its owned
processes exited; absence confirmed, no errors. Durable checker copy, evidence,
current checkout, environment, shared inputs and uncertain pytest scratch retained.

## Task 03 completed evidence and retained charges

Task 03 completed as PR [#90](https://github.com/david-hoffman/simrecon/pull/90),
head `d3bbef6c8cac8dd528198a1fdb84b0b59c0d44d8`, tree
`b5a0504e1e9cc8fc2a216560955d0d45798cc5b1`, against Task 02
`6627f33cc718b1da1cb7b35a620d22655848ae91`. Fresh B2, D and infrastructure
review ACCEPT. First full committed-candidate `make verify` passed all 13 phases:
3,100 tests, 47 warnings, 783.90 s; all 1,167 tracked manifest hashes unchanged,
all 36 owned Python files measured. Receipt SHA256
`944bfc6b052b7e269ce5417fb6c3d67c8340e0c8ca931dd2bfa1651f3f95ec87`.
Native covered/total statements and branches: global 4,834/4,972 and 1,854/1,964;
product 3,993/4,128 and 1,534/1,640; development 39/39 and 8/8; scripts
802/805 and 312/316. Same-run M25 increment 0 bytes (limit 33,554,432);
both installed wheels and audit passed. This is predecessor evidence, never a
changed Task 04 pass. Detailed completion and review evidence remain in the
Task 03 worktree's ignored `artifacts/readability-03/completion.json`, reports,
verification receipt and coverage; PR #90 retains its remotely readable summary.
Task 03 CI run 42937791643 was pending at Task 04 intake. The stack root then
confirmed completed SUCCESS for Ubuntu 24.04 job 130252044602 and macOS 15
job 130252045099 on the exact Task 03 head. This remains predecessor evidence.

Retained Task 03 totals, adding final reviews to the detailed attempts above:
A one author/two test corrections/four failed narrow checks; B two fresh reviews,
one nonacceptance/one accepted correction/one oracle finding/one absent-path read;
C one author/one lint correction/one failed initial lint check; infrastructure
one author/no correction or failure. D one ACCEPT/one nonblocking presentation
finding/two failed optional probes corrected/no target edits. Infrastructure
review one ACCEPT/one successful offline installed check/one absent-path lookup/
one corrected optional manifest display key. Coordinator one optional absent-glob
failure/one incidental doc replacement correction/one full gate pass/none failed;
three confirmed disposable C scripts removed. No post-verification candidate
changes. All older analysis/kickoff/Task 01/02/native-launch/setup charges remain
above. Human budgets not set; actual served model/tokens/cost/complete elapsed
unknown. No merge or auto-merge.

## Task 04 contract and evidence pointer

Task 04 alone names meaningful preparation/acquisition operations and improves
accurate docstrings/comments linking the walkthrough equations and conventions.
Ownership is the five existing `src/simrecon/acquisition/` modules and necessary
import/call-only consumers of renamed helpers. Prefer meaningful scientific
operations over blanket validator renames. No larger extraction or numerical
rewrite, new scientific behavior, public API expansion, compatibility aliases,
local-variable renames, retired API revival, test rewrite, dependency or gate change.
Preserve exact expressions, signs, scales, evaluation/traversal order, accepted
input domains, error hierarchy/messages, array ownership and diagnostic/provenance
records. Preserve the 36 documented root exports, dunders and neutral CLI.
Literal module and local `t`/`d` traceback context must survive. Tasks 05–09 remain
outside scope except necessary consumers of renamed acquisition helpers.

Route **high risk**: helper identities cross scientific consumers, so narrow
readability edits retain fresh blind A, fresh blind B, restricted C, committed
exact-candidate full `make verify`, then fresh independent D. November 11 owner
clarification permits direct fresh collaboration roles (`fork_turns="none"`),
not nested delegation or native authentication/cloud-launcher retries. Requested
roles use Sol/high under repository calibration; observed served attribution and
usage are unknown. A owns only `tests/test_preparation_readability.py` if a concrete
uncovered public risk justifies it; existing independently accepted public tests
and fixtures are retained by default. No artificial red or new oracle solely to
prove a rename. B audits retained oracle applicability/omissions and freezes exact
test identities. C owns only product scope, no tests/fixtures/configuration,
workflow, delivery, gate or policy edits. Coordinator owns this handoff, current
navigation/source links and PR presentation. New required infrastructure work
returns to separately named ownership and review, never implicitly to C.

| ID | Preserved observable obligation | Evidence and authority |
| --- | --- | --- |
| T04-1 | Camera/sentinel correction and ordered edge apodization retain values, accepted domains and mutation boundaries. | CE02/CE06 public contracts, retained public tests, A/B mapping and D comparison. |
| T04-2 | Equalization anchors, FFT half-spectrum normalization/signs, phase-separation policies and noise factors retain exact computation/order. | CE02/CE06 contracts, independently accepted tests and alpha-renamed AST comparison. |
| T04-3 | On/off composition, 2D layout, drift correlation/translation/cubic fitting and event traversal preserve results, record ownership and provenance. | CE06/plane/declaration contracts, retained public controls, full gate and D. |
| T04-4 | Invalid, representation-limit and operation-time failures plus permitted positive boundaries retain errors and workflow nonzero time/direction context. | Existing contracts/tests including real workflow failures; no renamed locals or literal modules. |
| T04-5 | All 36 exports, neutral APIs/CLI, devtools installed command/strict plugin, #87 affinity/observers, locked install and separate wheels remain intact. | Existing public interfaces and installed-product/full verification checks. |
| T04-6 | Ordinary scientific operation names/docstrings/comments explain actual equations, axes, units, signs, policies and ownership, without expanding the supported API. | Executing source and approved reader map, text/dynamic-name inventory, live link checks and D. |

Coverage inherits behavior coverage with independent risk review; no percentage
target is selected. Mandatory native statement/branch file/package/global reports,
never-imported and subprocess measurement, independent Ubuntu/macOS CI reports,
all 13 phases, separate installed wheels, audit and same-run M25 limit 33,554,432
bytes remain. Pending CI is not passing. The predecessor receipt certifies only
its unchanged predecessor. No smaller route or weaker gate is selected.

Before editing, GitHub confirmed PR #90 open/unmerged at the pinned head/base;
new isolated Task 04 worktree and locked environment were created. Python 3.13.12,
uv 0.12.19 and pinned Temurin 21.0.7+6 via `SIMRECON_JAVA`; `uv sync --locked
--all-groups` and canonical `make preflight` passed on supported escalation path.
Durable evidence/packets/checkpoint/reports live in ignored
`artifacts/readability-04/`; full receipt/coverage in their usual directories.
Prepare the tracked handoff before commit; exact final hashes/results, reviews
and PR/CI go outside tracked bytes. PR summary will explain named preparation
steps and preserved behavior, with technical appendix; no decorative figure needed.
Cleanup preserves active worktree/environment, predecessor/shared inputs and
all durable evidence; remove only confirmed disposable owned scratch using the
existing housekeeping workflow. Numeric budgets not set; missing metering unknown.

## Task 04 execution accounting and retained checkpoint

Fresh blind A retained existing science tests/fixtures without edits, artificial
red or new oracle. Its sampled independently checked controls map T04-1–6 to
specific keepers; source-free execution passed 78 cases in 6.20 s. Fresh blind B
independently checked analytic phase/noise/Fourier/cubic/on-off/layout controls,
permitted positives and concrete omission risks; all 17 input hashes match and
its independent source-free run passed 48 cases in 17.76 s. B **ACCEPT** applies
to the unchanged retained checkpoint, not unseen implementation/full historical
oracle derivation. Neither blind role reports implementation/history/coverage
exposure. A: one author/no test correction/no failed check; B: one accepted review,
no test correction or failed test, one permitted-doc path lookup failure corrected.
Detailed mapping, limits and exact hashes: `a-report.md`, `b-review.md` and
`accepted-checkpoint.json` under ignored `artifacts/readability-04/`.

Restricted C made 11 meaningful helper/class renames across preparation, drift
and mode composition, retaining mathematical locals and truly local validators.
Five acquisition modules gained accurate physical/array/domain/ownership docs,
with walkthrough equation/convention pointers. Only two reconstruction modules
needed import/call-only updates for downstream-band validation. No scientific
algorithm extraction, argument/local/field/event-keyword/literal change survives.
An initial mechanical edit accidentally touched the diagnostic `correlation`
keyword; C caught and restored it before verification. Current names explain phase
separation, ordered edge updates, signed bins, positive drift ramps, displacement
correlation, between-direction drift, in-place cubic timestamp fitting, carried
camera state, equalization and literal on/off order combination.

Entire-source AST preservation passes for all 27 source files, including all
seven changed runtime files, stripping only docstrings and normalizing exact
module-bound approved helper identities and affected import alias ordering.
The checker rejects selected local/argument/nested-definition shadowing and keeps
keywords, constants, fields, operators and control flow exact. Root facade and
36 exports are byte-identical; all 93 test files and all 324 baseline tracked
non-source/non-doc inputs are unchanged; all 17 B inputs match. The new append-only
coordinator lesson records the corrected keyword collision, not new policy.
Evidence: `c-rename-map.json`, `c-preservation-check.py`, `c-preservation.json`,
`c-line-map.json` and `c-report.md`.

C focused lint/format and pinned escalated Pyright pass (zero type errors);
704 representative retained cases pass in 180.41 s with two existing test-owned
observer divide warnings. An initial Pyright lookup failed to resolve NumPy in
the sandbox, causing 121 cascading diagnostics; the supported pinned interpreter
execution resolved them without source/config changes. C also corrected one
initial long-line/import-order lint failure and one supplemental checker
copy/node-identity error while strengthening shadow detection; no product-red,
test correction, numerical fix or gate relaxation. Same-line doc precision fixes
retain line positions. Detailed C accounting/commands remain in its report.

Coordinator updated the walkthrough's actual operation names, 55 explicit source
locations and seven shorthand endpoints, using retained AST statement identity
or exact unchanged source blocks. All 129 local paths/anchors and 38 retained
source positions pass; plan rows explicitly label the earlier preparation names
as transitions. Source/dynamic-consumer scan has no stale live consumers; historical
map rows remain labeled. Re-ran C preservation and document checks successfully.
Coordinator failures retained: one GitHub workflow-call schema mismatch corrected,
one premature absent A-report probe, and three auxiliary document-location mapping
attempts corrected after identifying decorator/keyword/comment lines without AST
statement positions. These are five ancillary failures, not product/test/full-gate
failures. No tracked source changed during those document-tool corrections.

All role-owned check sessions exited. C identified exactly four disposable
authoring scripts under `artifacts/readability-04/`: `c-edit.py`, `c-docs.py`,
`c-mode-docs.py`, `c-links.py`. Coordinator removed those paths with existing
commands and confirmed absence, no errors. Preserve the durable checker/reports,
current checkout/.venv, predecessor worktrees, shared inputs and uncertain runner
scratch. No disposable fixture or worktree was identified. All historical charges above remain;
human numeric budgets not set, requested Sol/high roles, observed served model,
tokens/cost and complete elapsed unknown. No merge or auto-merge.

## Task 04 completed evidence retained at Task 05 intake

Task 04 PR [#91](https://github.com/david-hoffman/simrecon/pull/91) is open and
unmerged at `c7bea91a4c07068e7662be1f5ca5aed24e369f18`, tree
`ccb7ef698f1ec26f8953ad3144fea0676f67001b`, based on Task 03
`d3bbef6c8cac8dd528198a1fdb84b0b59c0d44d8`, tree
`b5a0504e1e9cc8fc2a216560955d0d45798cc5b1`. Fresh B and D ACCEPT;
all 13 full local phases passed: 3,100 tests, 47 warnings, unchanged 1,168-file
manifest and 36 owned Python files. Receipt SHA256
`f263a02790d968b6f5d04e851fc623a3807881782014c9bdbbfac7b22dd8cc96`.
Global statements 4,834/4,972 and branches 1,854/1,964; product 3,993/4,128,
1,534/1,640; devtools 39/39, 8/8; scripts 802/805, 312/316. Same-run M25
increment 0 bytes, limit 33,554,432 bytes; separate product/development installed
wheels and audit passed. This proves only Task 04's candidate, not Task 05.

Completion and complete detailed charges remain at
`/workspace/simrecon-readability-04/artifacts/readability-04/completion.json` and
its sibling reports. Final Task 04 coordinator counts: one setup/preflight pass,
one candidate commit, one full verify pass/no full failure, six ancillary failures
(the five documented above plus a premature tests-log lookup), no change after
the full gate, four disposable scripts removed/no cleanup errors. D: one fresh
ACCEPT/no correction/actionable findings, three optional probes (one older-system-
Python API failure, two pinned passes), no suite repeats or target edits. Earlier
A/B/C and stack charges above remain unchanged; unknown metering is not zero.
Task 04 CI run 42942992919 was pending at its handoff. Ubuntu subsequently passed;
initial macOS job 130268993418 failed one unchanged verifier-fixture test when
only the empty `objects/maintenance.lock` disappeared (3,100 other cases passed,
46 warnings). A report-only root advisor diagnosed a strongly supported Git
2.56 detached-auto-maintenance race; actual removing process was not traced.
The unchanged focused test passed locally once (4.49 s, Git 2.52), with zero
diagnostic failures/edits. Root requested one unchanged macOS rerun; the latest
configured jobs both completed SUCCESS (macOS 130274284681, Ubuntu 130274286631).
Retain one failed CI job/test, one diagnostic advisor/check and one requested
successful retry as additional Task 04 charges; no gate or product/test change. Detail:
`/workspace/simrecon-readability-04/artifacts/readability-04/ci-diagnosis.md`.
Task 05 rechecks before submission; pending is not passing.

## Task 05 contract and evidence pointer

Task 05 alone clarifies declaration, sampling and empirical bead-preparation
operations in `src/simrecon/optical_transfer.py`, with readable meaningful helper
names, accurate NumPy docstrings and comments linked to equations/conventions.
Keep this module intact: any larger optics extraction is a separate successor.
Only necessary import/call consumers may change in acquisition, reconstruction or
workflow; no incidental later-task readability work. Preserve exact numerical
expressions, order/sign/scale, all accepted input domains/errors, array ownership,
record fields/payloads, 36 documented root exports, Python dunders, neutral CLI
and literal module/local `t`/`d` traceback context. No scientific feature/fix,
API expansion/alias, retired API, blanket test rewrite, dependencies or weaker gate.

Route **high risk**, selected for actual numerical-operation/cross-domain impact:
fresh blind A maps retained public tests; fresh blind B audits applicability,
oracles and concrete omissions; restricted C owns only product source; committed
exact-candidate full `make verify`; fresh independent D. Owner November 11
clarification permits fresh collaboration roles `fork_turns="none"`, Sol/high,
without native launcher/cloud retries or nested delegation. No weaker route.
A owns only `tests/test_optical_transfer_readability.py` if a concrete missing
approved public risk is diagnosed and routed; existing accepted tests/fixtures
are retained by default, with no artificial red/new oracle merely for names.
C cannot edit tests/fixtures/config/workflows/coverage/skills/policy. Coordinator
owns this handoff and necessary live navigation/source links and PR presentation.

| ID | Preserved observable obligation | Authority and evidence |
| --- | --- | --- |
| T05-1 | Declared radial/full tables, positive increments, exact representation, owned records and downstream selection keep existing domains/payloads. | CE03 and relevant CE06/CE07 contracts; retained public tests; D. |
| T05-2 | Complex radial/full interpolation, negative-x conjugation, once-adjusted negative coordinates, literal safe flat vertices and axial scaling keep values/errors. | CE03 equations and retained analytic controls; AST preservation; D. |
| T05-3 | Camera/background/edges, centering, normalized bead phase separation, shifted sphere compensation, radial averaging/support/axis/origin/normalization keep ordered mathematics. | CE03 contract and retained independent public controls; full suite; D. |
| T05-4 | Valid boundaries, invalid/representation/operation-time failures and workflow time/direction context keep errors/outcomes. | Existing public contracts/tests; unchanged literals/locals; D. |
| T05-5 | Root exports, neutral CLI, Task02 tooling separation, locked install, strict plugin/#87 observers/affinity, separate wheels and all-owned/subprocess reporting remain. | Frozen files, installed-artifact checks, full gate. |
| T05-6 | Names/docstrings/comments accurately explain current axes, units, signs, domains and mutation/ownership without a stable helper API or extraction. | Actual source, live walkthrough links and independent D. |

Coverage inherits approved behavior coverage and independent risk review; no
percentage threshold selected. Mandatory native statement/branch file/package/
global measurement, never-imported files/relevant subprocesses, independent
Ubuntu/macOS CI, all 13 phases, same-run M25 limit 33,554,432 bytes, both separate
installed wheels and audit remain binding. Pending CI is not passing. No physical
recovery, historical C-executable agreement or performance claim follows.

Remote identities and PR #91 were checked before worktree creation; the Task 05
branch was absent and main remained `0ea11a5876549bf26a3a813009b97c09decc806d`.
Own isolated locked preflight passed Python 3.13.12, uv 0.12.19 and Temurin
21.0.7+6 through `SIMRECON_JAVA`. One sandbox Git ref lookup and one initial
sandbox preflight failed proxy access; supported escalated retries passed.
No native launcher/authentication retry. Human numeric budgets not set; actual
served attribution, role tokens/cached tokens/cost and complete elapsed unknown.
All predecessor attempts/spending remain retained without double counting.

Detailed ignored evidence: `artifacts/readability-05/`, plus usual verification
and coverage directories. Prepare this sole Current state before final commit;
exact head/tree/results/receipt/PR/CI go outside tracked bytes in completion JSON
and PR/conversation. Plain-English PR summary explains optical-transfer reading
steps with technical appendix; no decorative figure is needed. Coordinator
housekeeping removes only confirmed disposable task-owned scripts after process
closure, retains active checkout/environment, predecessor/shared inputs, durable
evidence and uncertain scratch. No merge, auto-merge or release.

## Task 05 execution accounting and retained checkpoint

Fresh blind A retained existing tests/fixtures without edits, artificial red or
new oracle; its two source-free runs passed 334+42 selected cases. Fresh blind B
independently checked representative interpolation/phase/compensation/geometry/
ownership/representation/context expectations and omission risks, then ACCEPTED
the unchanged checkpoint. Its two source-free runs passed 334+51 selected cases;
all 24 public/test/fixture/packet input hashes matched. Both reported no source
exposure, failures, corrections, disposable scratch or remaining owned processes.
These are retained applicability checks, not a new derivation of every historical
oracle. Detailed limits/mapping/hashes: `a-report.md`, `b-review.md` and
`accepted-checkpoint.json` in ignored `artifacts/readability-05/`.

Restricted C made 11 meaningful helper renames in the intact optical-transfer
module and updated only the shared validation import/call in three consumers.
NumPy docs cover records/declaration, literal complex stencils, positive centering
ramps, 1/P bead separation, shifted continuum sphere, radial projection/support
and ordered normalization/combination. Local mathematical names and validators
remain. Decorated `_sample_transfer` keeps its name because translated failures
use `function.__name__`; the coordinator's new append-only lesson records this
source-observed diagnostic dependency without a new backend-failure claim.

C structural preservation passes all 27 product ASTs after removing docstrings
and reversing only approved module-bound helper definitions/references/imports.
It rejects selected shadowing and preserves every constant/keyword/field/local/
parameter/operator/expression/control-flow statement and order. Only the affected
workflow import aliases are order-normalized. All 325 baseline tracked files
outside source/docs are byte-identical, including 93 test files and all tooling,
locks, settings, CI and delivery rules. All 24 B checkpoint entries plus B report
hash match; root facade and 36 exports are byte-identical. C's exact hashes,
normalization limits and complete source/decorator/location maps are retained in
`c-preservation.json`, `c-rename-map.json`, `c-line-map.json` and `c-report.md`.

C focused checks passed 334 optical/acquisition/failure/migration cases (68.06 s)
and 142 selected direct-consumer cases (9.26 s, 695 deselected), with no failed
case; pinned Pyright reports zero errors/warnings. Final lint/format pass. Full C
accounting: one author, five lint attempts (four pass, one fail: 15 long-link plus
one import-order finding), four format checks (three pass, one blank-line fail),
two formatter mutations, three preservation passes, one type pass and two test
passes; one ancillary missing-relative-artifact search. Two coordinator-requested
same-line doc wording corrections were applied and rechecked; no numerical,
test/oracle, type or preservation failure and no native launch/retry.

Coordinator relocated 60 affected-source endpoints (21 moved), retained all 38
previous source anchors, added bead-reader rows and library navigation, and
checked 154 local paths/anchors including root-relative docstring pointers.
Coordinator reran structural preservation after integration successfully. Two
ancillary mapper-schema assumptions failed (nested map/list shape), were diagnosed
and corrected without product changes; one initial predecessor-doc path lookup
was also corrected. Environment charges remain one failed sandbox Git ref check
and one failed sandbox preflight, followed by supported successful retries and
one pinned isolated preflight pass. No full gate has yet run for Task 05.

C's Pyright/test sessions exited; coordinator removed only the confirmed
`/tmp/task05-author.py` disposable authoring script and confirmed absence, no
cleanup errors. Retain the current checkout/environment, predecessor/shared
inputs, durable checkers/reports/maps and uncertain ordinary runner scratch.
All earlier stack/predecessor/CI diagnosis charges above remain retained without
reset/double counting. Human numeric budgets not set; requested roles Sol/high,
actual served attribution/tokens/cached tokens/cost/complete elapsed unknown.

## Task 05 retained pre-verification pointer

Task 05 high-risk optical-transfer readability is prepared in
`/workspace/simrecon-readability-05`, branch `codex/readability-05-optical-transfer`,
from Task 04 `c7bea91a4c07068e7662be1f5ca5aed24e369f18`, tree
`ccb7ef698f1ec26f8953ad3144fea0676f67001b`, targeting predecessor branch
`codex/readability-04-preparation` PR #91. That PR remains open/unmerged at the
recorded head/base; latest configured Ubuntu/macOS jobs passed after one unchanged
rerun, with the original failure/diagnosis/charges retained above. This certifies
only the predecessor. A/B retained checkpoint accepted; restricted C/focused and
coordinator source/navigation checks pass. No scientific/test/config/gate change.

Next: commit this candidate, canonical all-13-phase full `make verify` with
same-run mandatory M25 and explicit ignored public/checkpoint/reader input
fingerprints, then fresh exact-candidate independent D, remote recheck and push/
open one stacked PR. Exact final head/tree/full results/receipt/native counts/
M25/wheels/review/PR/CI and additional gate/review charges will be recorded outside
these verified tracked bytes in `artifacts/readability-05/completion.json`, retained
verification evidence and PR/conversation. No Task 05 full acceptance is yet
claimed by this pointer. No successor, native launcher detour, merge, auto-merge
or release. Cleanup keeps active/shared/durable inputs; one confirmed disposable
C script removed without error.

## Task 06 contract and evidence pointer

Authorized high-risk estimation readability only, from Task05 PR #92 exact pushed
`24e53bc2a7a792498950d83107ee382e599dc0cb`, tree
`ee6dfadaf2aab323d2b6a0b736b1a555ffb3ecd5`, targeting
`codex/readability-05-optical-transfer`. Preserve the numerical expressions,
evaluation order, signs/scaling, units/domains, validation/errors, ownership,
record fields/payloads, 36 exports, dunders/CLI, and literal module/local `t`/`d`
workflow context. Clarify overlap construction, finite carrier search and
modulation fitting in the intact `reconstruction/parameter_estimation.py` with
meaningful helper names, NumPy docs/reason comments and equation/convention links.
No numerical fix, new feature/API/alias, test rewrite or unrelated later-stage
readability. Larger extraction is separately scoped.

Fresh blind A maps existing public proof, fresh blind B audits its oracles,
permitted positives and omissions, restricted C owns only the named source and
necessary direct consumers, and fresh D reviews the exact committed passing
candidate. A/B receive only approved public sources/exact permitted tests and
source-free diagnostics; no implementation/history/state/coverage/lessons.
November11 direct collaboration roles supersede launch location alone. No native
launcher/auth detour. The coordinator owns live source navigation, handoff and
PR presentation. The existing walkthrough supplies useful math; an extra figure
would not clarify this name/documentation change.

Preserve Task02 development tooling, explicit strict plugin, locked install,
separate installed product/development wheels, all-owned/subprocess measurement,
PR87 affinity/observers, and all 13 full verification phases. Coverage percentages
remain advisory; mandatory exact native counts/reports and behavior/risk audit
remain. Commit before canonical full `make verify`, same-run M25 limit33,554,432
bytes and ignored public/checkpoint/reader input fingerprints. Fresh D follows
PASS; remote identity/ancestry recheck precedes normal push/one stacked PR.
No merge or auto-merge. Task07 belongs to the root's next fresh coordinator.

Predecessor completion is retained outside tracked bytes at
`/workspace/simrecon-readability-05/artifacts/readability-05/completion.json`.
Task05 A/B/D ACCEPT, one complete 13-phase local PASS, 3,100 tests/47 warnings,
1,169-file manifest unchanged, 36 measured owned files, M25 increment0 within
33,554,432 bytes, separate installed wheels/audit PASS. Receipt SHA256
`4acdfa676ad34478ce004ac380501d4e98a9aaecfd01ffad71792135de0e869b`.
These facts do not accept Task06. Root confirmed predecessor run42949769406 completed SUCCESS on both Ubuntu
job130291082328 and macOS job130291082466 after intake; pending was never treated
as passing. All earlier stack charges, Task04 macOS maintenance-lock
failure/one advisor/one focused pass/unchanged successful rerun remain above and
in predecessor completions; no reset/double counting.

## Task 06 retained pre-verification accounting

Fresh blind A retained public proof and26 exact input hashes, with no test edits
or exposure. Its single focused invocation lost the orchestration session handle;
status is incomplete/unknown, never counted passing, and no duplicate rerun was
launched. One A missing-path read and one lost-status incident remain charged.
Fresh blind B independently rehashed all26 inputs, audited representative
oracles/omissions/permitted positives, ACCEPTED, and observed207 focused
source-free tests PASS in5.58s/exit0. B checkpoint freezes31 inputs plus its report;
no oracle/test correction or scientific source exposure. Exact identities and
proof limits are in ignored `artifacts/readability-06/accepted-checkpoint.json`
and A/B reports. Initially passing retained tests are valid; no artificial red.

Restricted C edited only estimation source: four helper globals, one internal
operation class and seven meaningful method names; NumPy docs/reason comments
explain units/signs/overlap/search/regression/diagnostics. Record classes, local
variables/parameters, strings/keywords/fields/payloads/errors and numerical
expressions/order remain. Structural proof pairs all27 product ASTs and literal
NUMBER/STRING spellings,40 allowed binding edits,1,165 frozen files including93
test files,32 checkpoint inputs including B report, and exact root facade/36exports.
Coordinator live navigation relocates16 source-reference endpoints with zero
fallbacks;139 local paths/anchors and44 retained source positions pass.

C observed658 focused public tests PASS97.20s, lint/format PASS. Charges: one
fresh C, one implementation plus prose refinement and formatting, one lint,
one formatter write/one format check, five preservation invocations (one narrow
checker-scope defect/four passes), four failed focused type invocations and one
ancillary filename read. The checker was corrected only for the existing nested
closures, then tightened to require every intended method call and literal
spelling; product/tests unchanged during checker corrections. Type failures were
missing installed NumPy paths in sandbox discovery, despite Python importing
NumPy from this own environment. Coordinator's unchanged canonical locked full
Pyright failed with497 cascades in sandbox, then PASS0errors/0warnings through
the supported escalated path. Specific mechanism untraced; no code/config/gate
or environment repair was made. Full gate uses supported path.

Coordinator retained one passing isolated locked preflight, one sandbox canonical
type failure/one supported canonical PASS, one preservation integration PASS,
and seven ancillary nonzero documentation/evidence/filename/tool-path probes;
none was a product-test/full-gate failure. Detailed exact commands/statuses remain
in ignored coordinator accounting, C report and logs. Prior stack, setup/native
launch and Task04CI failure/diagnosis/rerun charges remain retained above and in
predecessor completions; no reset/double counting. Requested roles Sol/high;
actual served attribution/tokens/cost/complete elapsed unknown; human numeric
budgets not set. No native CLI/auth/cloud launch attempt added.

Cleanup: no confirmed disposable external task scratch was created; all own
ignored authoring/review/check outputs are durable evidence. C/A/B own processes
closed. Retain current checkout/.venv, predecessor/shared reader inputs/caches
and uncertain ordinary runner scratch. No removal or cleanup error.

## Task 06 retained completion pointer

Task06 completed at pushed head `7023bc69d8c7e07cc1c8ba93d6c0c7ef8e345a61`,
tree `e6825d8bbe7ce33990b4e008e674cf59afec9330`, PR #93 open/unmerged,
targeting Task05. Fresh B/D ACCEPT; exact clean committed full13phase PASS,
3,100 tests/47warnings,1,169-file manifest unchanged,all3 input fingerprints
matched,36 measured owned files,M25 increment0 within33,554,432bytes,both
installed wheels/audit PASS. Receipt SHA256
`15eb175510988a1242c28fc7dee952e53ace05b89e9954302e24f37af87b051e`.
Native counts: global4,834/4,972 statements and1,854/1,964 branches;
product3,993/4,128 and1,534/1,640;devtools39/39 and8/8;
scripts802/805 and312/316. Detailed completion/accounting/evidence remain at
`/workspace/simrecon-readability-06/artifacts/readability-06/completion.json`.
Task06 CI was pending at launch and never counted passing then. Root subsequently
confirmed run42954992027 completed SUCCESS on both macOS130307856907 and
Ubuntu130307857235.
All historical charges and Task06 incomplete A invocation/type/tool/checker
failures/corrections remain retained above and in that completion; no reset.
Predecessor PASS does not accept Task07 changed candidate.

## Task 07 contract and evidence pointer

Authorized high-risk filtering/assembly readability only, from exact Task06
head/tree above, target `codex/readability-06-estimation` PR93. Keep the intact
`reconstruction/known_parameters.py` and its algorithms. Meaningful helper names,
NumPy docs/reason comments and equation/convention links clarify native filtering,
quadrature recombination, carrier relocation, inverse normalization and signed
output. Preserve numerical expressions/evaluation order/sign/scale/domain/errors,
ownership/record fields/payloads/local names,36exports/dunders/CLI and literal
module/local t/d traceback context. No larger extraction, numericalfix, feature,
APIexpansion,alias,blankettests or later workflow/I/O/Serena changes except
necessary direct consumers. Coordinator owns live source links,handoff and PR
presentation. Existing walkthrough supplies useful math; no extra figure needed.

Fresh blind A maps retained public proof; fresh blind B independently audits
oracles,permitted positives/omissions and accepts checkpoint; restricted C owns
only named product source/necessary direct consumers; fresh exact-candidate D
follows commit/full gate PASS. Public inputs/source-free diagnostics only for A/B;
no implementation/history/state/coverage/lessons. November11 fresh collaboration
roles supersede launch location alone, no nativeCLI/auth/cloud detours.

Preserve Task02 devtools/delivery/strict explicit plugin/locked install/separate
installed wheels/all-owned-subprocess measurement/PR87affinity-observers and all
13phases. Coverage percentages advisory; exact native reports/counts and behavior
risk review required. Full-local committed make verify uses supported canonical
path, mandatory same-run M25 limit33,554,432bytes and public/checkpoint/reader
input fingerprints. Recheck remote head/base/ancestry before submission; normal
push/open exactly one stacked PR,no merge/auto-merge. Root owns successor08.

## Task 07 retained pre-verification accounting

Fresh blind A mapped existing public proof,31input hashes matched,369source-free
focused tests PASS12.23s,zero edits/exposure. The initial packet named two absent
mode-test paths; actual acquisition boundary/filter/2D files were explicitly
allowed after inventory. Fresh blind B independently checked all35inputs,
recalculated closed numerical expectations/permitted positives/omissions and
ACCEPTED. It retained A's unchanged369PASS and ran10previously-unexecuted
compatibility cases PASS1.90s,one sanitized test-observer negative-power warning.
No test/oracle correction or artificial red. Accepted ignored checkpoint freezes
36inputs plus B report; SHA256
`bca4e4065e855e869773e3124505da27ada89508317658f90be654ddc029305a`.
Retained test limits are explicit: tolerance proof cannot establish literal
expressions/order/names/docs,backend interceptions are not exhaustive and direct
nonzero reconstruction-stage t/d error assertions are not established by A/B.
Restricted C/fresh D inspect those unchanged structural obligations.

C names six helper globals,one precise-taper operation class and five methods;
records/classes/fields,all locals/parameters,expressions/control flow/order and
non-docstring literals remain. No other production helper consumer needed edits.
Structural pairing compares all27product ASTs and NUMBER/STRING/f-string lexemes,
allows32explicit scoped binding edits,rejects shadowing and verifies1,165frozen
files including93testfiles,37checkpoint/report paths and exact facade/36exports.
Coordinator integration of that proof PASS. Existing421focused public cases
PASS67.18s with one expected fixture warning;lint/format PASS. Coordinator
unchanged canonical locked make types PASS0errors/0warnings on supported path,
without repeating known sandbox-discovery failures or changing configuration.

Coordinator relocated26walkthrough source-reference endpoints with0fallbacks;
141localpaths/anchors and44retained source positions PASS. Final exact source,
rename map,line map,author checks,commands/charges and preservation limits are
retained in ignored `artifacts/readability-07/c-report.md` and adjacent evidence.
C's initial broad method token edit touched3record.scale reads; immediate
inventory caught/restored all3 before checks/tests,one charged edit correction.
Two diagnosed lint failures/two line-length cleanup iterations,one prose refinement requested by coordinator
(exact equation anchors/explode multiplier),and C's2initial absent-path reads
remain charged; no product-test failure or test/config repair. Coordinator adds
2ancillary path/timing read errors,one locked preflight PASS,one typePASS,
one structural integrationPASS and two navigationPASS checks. All prior stack and
Task06 incomplete-result/type/checker/environment/CI charges remain retained
above and in predecessor completions; no reset/doublecounting. Requested
rolesSol/high;actual serving/tokens/cost/full elapsedunknown;human numeric
budgetsnotset. No nativeCLI/auth/cloud-launcher attempts.

Cleanup: no confirmed disposable external task scratch created; ignored author,
review and check outputs are durable evidence. Closed completed own role/check
processes; preserve current checkout/.venv,predecessor/shared reader inputs/caches
and uncertain ordinary runner scratch. No removal or cleanup error.

## Task 07 retained completion pointer

Task07 completed at pushed head `14561e5d280ed90405002a9afe8133799e9ed597`,
tree `310c50c13804c7da6c3897f83512179dfc40a104`, PR #94 open/unmerged,
targeting Task06. Fresh B/D ACCEPT; exact clean committed full 13-phase PASS,
3,100 tests/47 warnings, 1,169-file manifest unchanged, all three input
fingerprints matched, 36 measured owned files, M25 increment 0 within
33,554,432 bytes, both installed wheels/audit PASS. Receipt SHA256
`585e1c0e6f55a84fa59c446ed5abb5dcf3afd314796c4f73840273df490a5ae1`.
Native global counts: 4,834/4,972 statements, 1,854/1,964 branches;
product 3,993/4,128 and 1,534/1,640; development tools 39/39 and 8/8;
scripts 802/805 and 312/316. Detailed completion/accounting/evidence remain at
`/workspace/simrecon-readability-07/artifacts/readability-07/completion.json`.
Task07 CI42960555856 was pending at Task08 launch and was not counted passing.
Root subsequently confirmed both macOS130325807567 and Ubuntu130325807889
completed SUCCESS. All Task06 and earlier required CI also passed both platforms.

Task07 preserves two full attempts: the first was incomplete on an environment
restart. Its 605 archived files/551 coverage shards, absent receipt and absent
live process are retained. Recovery preflight/unchanged-input checks passed,
then a fresh same-candidate complete gate passed with no product/config repair,
partial reuse or post-commit tracked change. D accepted independently after that
PASS; all ancillary commands/corrections and unknown metering remain charged.
Task04's diagnosed macOS Git2.56 maintenance-fixture lock race, one failed CI
job/test, advisor/focused pass and unchanged successful rerun also stay retained.
No predecessor PASS accepts Task08's changed candidate.

## Task 08 contract and evidence pointer

Authorized high-risk workflow/I/O readability only, from Task07 exact head/tree
above, targeting `codex/readability-07-reconstruction` PR94. Clarify meaningful
orchestration/adapters, actual neutral-function docstring gaps and current-source
navigation. Preserve exact expressions/control flow/evaluation order, numerical
scales/signs, supported domains/errors/payloads, record classes/fields, ownership,
ordering, all 36 exports, dunders and neutral CLI. Preserve literal-module and
local `t`/`d` error-context semantics. No algorithm extraction, numerical rewrite,
new decoder/writer/reconstruction CLI, API expansion/aliases, test rewrite,
weaker gates or unrelated prior-stage/Serena work.

Fresh blind A maps retained public proof; fresh blind B audits oracles, permitted
positives and omissions and accepts the frozen checkpoint. Restricted C owns
named workflow/I/O source and useful narrow CLI/models docs. Coordinator owns
necessary live links, handoff and PR presentation. Explicit scoped local mapping
in `reconstruct_workflow` may replace `a/o/c/f` with readable configuration names;
all other locals/parameters stay exact. Supplemental binding/AST/literal proof
and fresh D inspect exact source preservation beyond tolerance-based tests.
November11 fresh collaboration `fork_turns="none"` roles supersede launch
location only. No nativeCLI/auth/cloud-launcher detours or nested roles.

Preserve Task02 devtools/delivery, strict explicit pytest plugin, locked isolated
install, separate installed wheels, all-owned/subprocess measurement and PR87
affinity/observers. Coverage percentages remain advisory; mandatory exact native
reports and behavior/risk review remain. Commit before all 13 canonical phases
of full `make verify`, with same-run M25 limit 33,554,432 bytes and explicit
public/checkpoint/reader fingerprints; fresh exact-candidate D follows PASS.
Remote head/base/ancestry are rechecked before normal push/opening one stacked
PR. No merge/auto-merge; root alone starts Task09 after completion.

## Task 08 retained preparation accounting

Fresh blind A mapped six obligation groups to 183 retained test functions and
39 permitted input hashes. Useful source-free selections passed 43 and 150
cases (193 distinct). Its three invocations total 338 expanded passes and five
environment failures: the second selection lacked `.venv/bin` on PATH for bare
`simrecon` subprocesses. After diagnosis, the identical selection passed with
PATH corrected. No product-red, test change or new oracle was manufactured.
The corrected selection reported 22 source-free external NumPy warnings.
Fresh blind B independently recalculated representative workflow/format
expectations, checked permitted positives and omissions, reverified all 39
hashes before/after, and ACCEPTED. A distinct source-free selection passed 23
cases with two external NumPy warnings. No concrete public defect/omission or
test correction. The accepted checkpoint freezes 44 inputs including B report;
SHA256 `bd23585f7f4b148f96d7995c70126690d8264254115106082c43355e5b922e3c`.
Exact error prose, dunders, literal module/local t/d extraction and useful new
docs remain explicit C/D source-comparison duties beyond behavioral tolerances.

B initially fetched full role/audit procedure text before narrowing to permitted
sections. It disclosed the procedural overread; those sections contained no
current implementation/history/state, and coordinator directed continuation.
No nonblind discovery/excluded links or implementation exposure occurred. All
attempts remain charged. A/B report no live owned processes or manual disposable
scratch; retained reader/test artifacts are durable evidence.

C names 16 meaningful workflow helpers and four configuration aliases scoped
to `reconstruct_workflow`. All other locals/parameters, record classes/fields,
body expressions/control flow/evaluation order and non-docstring literal
spellings remain exact. Five existing same-module from-import name lists receive
Ruff-required permutations; statements/module imports stay in place and all
retrieved names are ordinary defined globals without dynamic module lookup.
The explicit map records each permutation. No scientific stage, neutral public
function name, CLI/models source, facade/export, test/fixture/config/gate change.
Eleven source modules change: six workflow modules and five neutral I/O modules.
Twenty-five useful function docstrings fill real workflow gaps; expanded neutral
and workflow docs explain actual shapes/units, provenance/ownership, validation,
exclusive creation, non-atomic checks and partial-new-file limitations.

Supplemental proof pairs all 27 product ASTs and significant raw tokens with
only explicit binding changes, formatting parentheses/trailing commas and those
five import-name permutations. It verifies 1,146 frozen unowned paths, all 93
test/fixture files and all 44 accepted inputs; helpers reject shadowing/collisions
and four local aliases are nonparameter bindings with no nested shadowing.
Restricted C passed 494 focused workflow/compatibility cases and 59 I/O cases;
M25 was intentionally deselected for the full gate, not duplicated. The I/O
selection reported 28 external NumPy warnings. No product/test failure.
Lint/format, coordinator canonical types (0 errors/warnings), structural
integration and whitespace checks PASS. Navigation checked 155 local paths/anchors,
44 retained source positions (two moved) and ten inline references including
shorthand ranges, with no guessed endpoints. A manually caught shorthand range
was corrected and added to the ignored navigation checker before final PASS.

C cumulative diagnostics: eight supplemental checker invocations (six PASS,
two pre-edit/format harness mismatches, including the final strict-input
rerun); six Ruff lint invocations (two initial finding runs, targeted D209/import
corrections and two clean confirmations); five format invocations. Eighteen
closing-quote layouts and two import blocks/five name lists were corrected.
An initial optional-key summary displayed zero until corrected to the actual
1,146-path key before edits. The checker later rejected formatting punctuation,
was reconciled with exact AST/token proof, then tightened to remove an unused
accepted-doc hash exception; actual 44 inputs remained unchanged throughout.
No product/test failure, checkpoint correction, full-gate attempt or hidden retry.
Coordinator preparation adds one locked preflight PASS, one canonical types PASS,
two structural-integration PASS runs and four navigation PASS runs/refinements.
One absent role-skill read was corrected using actual inventory; two expected
pending-report probes returned nonzero. All ancillary findings remain charged;
no runtime/config/test repair followed. No nativeCLI/auth/cloud-launch attempt.

## Current state
Task08 high-risk workflow/I/O readability is prepared in
`/workspace/simrecon-readability-08`, branch `codex/readability-08-workflow-io`,
from verified pushed Task07 head `14561e5d280ed90405002a9afe8133799e9ed597`,
tree `310c50c13804c7da6c3897f83512179dfc40a104`, targeting PR94 branch
`codex/readability-07-reconstruction`. Predecessor open/unmerged exact head/base,
remote main/ancestry and absent new remote branch confirmed. No newer changes
discarded. Root confirmed Task07 CI42960555856 both configured platforms SUCCESS.
Own locked isolated preflight PASS using Python3.13.12, uv0.12.19 and
Temurin21.0.7+6 via SIMRECON_JAVA. Fresh blind A/B retained proof/checkpoint ACCEPT;
restricted C/focused checks and coordinator preservation/types/navigation PASS.

Next: commit this candidate, run all 13 canonical full `make verify` phases with
same-run mandatory M25 and public/checkpoint/reader fingerprints, obtain fresh
exact-candidate D, recheck remote identities and normal-push/open one stacked PR.
This pointer claims no Task08 full acceptance yet. Final hash/results, receipt,
native counts, M25/wheels, D/PR/CI and post-commit charges stay outside verified
tracked bytes in ignored `artifacts/readability-08/completion.json`, verification
evidence and PR/conversation. No successor/merge/auto-merge; root alone starts09.
All analysis/kickoff/native-failure/Task01–07 and current role/check charges remain
retained above and in predecessor completions. Requested roles Sol/high; actual
serving/tokens/cost/full elapsed unknown; human numeric budgets not set.

Cleanup: removed C-confirmed disposable `artifacts/readability-08/c-edit.py`,
`c-docs.py`, its checker `.pyc` and empty `__pycache__` directory after all own
processes closed. Keep current checkout/.venv, packets/preservation/navigation
scripts, source maps, reports and reader/test observations as durable evidence;
retain predecessor/shared reader inputs/caches and uncertain ordinary runner
scratch. No removal or cleanup error; no unrelated worktree deletion.
