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

## Current state

Task 03: high-risk whole-module/package migration and issue #81 under the
November 11 owner clarification authorizing fresh collaboration A/B/C/D agents.
Worktree `/workspace/simrecon-readability-03`, branch
`codex/readability-03-packages`, from Task 02
`6627f33cc718b1da1cb7b35a620d22655848ae91`, targeting
`codex/readability-02-devtools` (PR #89). Remote PR #88/#89 remain open/unmerged
at exact recorded heads; ancestry/main unchanged, Task 03 branch absent at intake.
Predecessor Ubuntu/macOS CI is not changed-candidate verification.

A's 29-case migration checkpoint received fresh B2 ACCEPT after one B1 oracle
finding and scoped blind correction. Restricted C completed the preserved whole-
module moves; separate infrastructure owner made exactly two path literals;
coordinator updated live source navigation. Frozen test identities, role/risk
reports, checks and all cumulative charges are retained above and under
`artifacts/readability-03/`. Product/focused checks pass. Final candidate is
prepared for commit and the canonical exact-candidate full gate; full receipt,
fresh D/infrastructure verdicts, hashes and PR/CI outcomes will be recorded outside
these verified tracked bytes, in the durable evidence and PR/conversation.
No claim of full-candidate acceptance is made by this pointer. Submission requires
passing all phases and fresh exact-candidate reviews, then remote recheck, push
and one PR. No native CLI retry, merge, auto-merge, release or Task 04 work.

Totals retained: A one author/two authored test corrections/four failed checks;
B two fresh reviews/one nonacceptance/one accepted correction/one oracle finding;
C one author/one lint correction/one failed lint; infrastructure one author/no
correction. Prior historical launch/setup/check failures remain above. Human
numeric limits not set; tokens/cost/served attribution/complete elapsed unknown.
Three confirmed C scripts removed; no cleanup errors. All role commands exited;
keep current checkout, `.venv`, shared pinned tools, predecessors, durable evidence
and uncertain pytest scratch. Active final verification/review inputs are retained.
