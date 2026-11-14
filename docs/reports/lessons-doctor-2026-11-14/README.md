# Lessons reconciliation — November 14, 2026

**Version 1.0**

208 observations are inventoried in 11 semantic buckets. This is an incremental
coordinator reconciliation: the 203 source hashes in the independently reviewed
[prior inventory](../lessons-doctor-2026-11-11/inventory.json) still match, and all five
new observations were read. Two arrived in the first main integration and one
in merged PR109. It is not a fresh full-backlog mechanism review.
The native doctor was attempted but could not complete because of authentication.

Initial baseline: `4dcc50dd70da2f93b4a3360e0a4160144656b35a`, initially clean.
Initial publication baseline: `87163657dd4e43e98adbc64ef8eca268c033084c`.
Current reconciliation baseline: `836ec790aac55fb7fcdff8d51da1547091952b6e`,
the actual PR109 merge integrated into this branch. Inventory cutoff follows
the latest scoped disposition reconciliation; [integration evidence](integration-109.md)
preserves its separate provenance and limits.
[Inventory](inventory.json) preserves exact source IDs, hashes, scoped inherited
states, findings and evidence. [Remote snapshot](remote-issues.json) captures
three open and five closed issues returned through GitHub, plus targeted searches.
No issue closure is treated as proof of resolution. No current conflicting
disposition was identified; the newer reader-parent record explicitly supersedes
only F002's earlier handling. Completion dispositions resolve F001/F002 after
reconciling merged remedies, exact-candidate checks/reviews and CI. PR109's
incoming disposition explicitly supersedes RM84-F001's original investigation
tracking only; native authentication remains unrepaired.

| Bucket | Lessons | Issue handling |
| --- | ---: | --- |
| B01 Scientific meaning and claim limits | 17 | Prior no-action decisions retained; historical PR53 comparison remains deferred |
| B02 Finite arithmetic and accuracy | 27 | Prior decisions retained; no new issue |
| B03 Contract-based test oracles | 35 | Prior decisions retained; no new issue |
| B04 Validated domains and public behavior | 24 | Prior decisions retained; no new issue |
| B05 Source-free diagnostics | 16 | Resolved: [#99](https://github.com/david-hoffman/simrecon/issues/99), completed by merged PR103 |
| B06 Review packets and role boundaries | 14 | New naming observation is covered by current section 4.2 and PR104; no new issue |
| B07 Candidate and environment identity | 16 | Existing RM84 native-backing resolution retained; setup obstacle relates to closed #105 |
| B08 Evidence custody and filesystem lifecycle | 22 | Prior decisions retained; no new issue |
| B09 Measurement integrity | 14 | Prior decisions retained; no new issue |
| B10 Verification prerequisites and cost | 10 | Resolved: [#100](https://github.com/david-hoffman/simrecon/issues/100), completed by merged PR102; reuse completed [PR87](https://github.com/david-hoffman/simrecon/pull/87); old 300-second continuation superseded |
| B11 External and native capabilities | 13 | RM84-F001 investigation resolved by merged [PR109](https://github.com/david-hoffman/simrecon/pull/109); CLOUD107-F001 knowledge remains no-action; native authentication remains unrepaired |

Primary per-source handling counts: 194 no-action, 13 narrowly resolved,
0 tracked, 1 deferred. Each observation is counted once; additional finding
scopes are mapped separately, without adding sources or summing claim counts.
These carry forward the prior evidence limits; no-action is not a fix certificate.
The new-observation no-action decisions cover qualification knowledge for #99,
the already-added naming grammar and CLOUD107's launch-evidence distinction.
F001/F002 are resolved against [completion evidence](completion-evidence.json)
from merged PR103/PR102: exact-candidate full gates, independent acceptance and
successful Verify runs. Private historical raw artifacts were not reopened.
The source correction report and current prerequisite documentation were read;
those closure decisions did not rerun product checks or synthetic probes. The
later PR submission gate and the renewed integration gate are separate evidence.

F003 retains its stable ID, but its old continuation requirement is superseded.
The [current PR87 body](apparatus-pr.json) records a 600.76-second passing gate,
fresh final reviews and the owner's acceptance/stop instruction. The 300-second
goal was explicitly superseded for that submission; no new performance issue or
restart is warranted. This is no-action on further work under the retired goal,
not a claim that 300 seconds was achieved. Its prior tracked disposition is
superseded only for that scope. The task remains the historical execution record.

RM84-F001 is resolved only for the original #107 investigation conditions:
separate failure classification and a supported fresh author/independent reviewer
path with observable identities, failure handling and unchanged gates. The
[merged PR109 evidence](integration-109-evidence.json), report and exact pilot
support that scope. Native authentication, the native doctor path and scientific
qualification remain unresolved or unproved. The new CLOUD107 source retains
no-action for CLOUD107-F001 and separately supports the RM84-F001 resolution;
neither disposition replaces the other's claim. No new issue is needed.
#99/#100 retain their scoped resolutions. The earlier #107 recurrence update was
published and read back; this reconciliation adds no external issue write or
implementation commission. Raw lessons are not blind packets.

## Doctor attempt and limits

Five invocations were diagnosed, without changing source or dependency pins:

1. `uv run --locked delivery doctor --check`: default uv cache was read-only.
2. The same command with task-local `UV_CACHE_DIR`: locked build dependency
   retrieval failed because sandbox network access was unavailable.
3. The same command with `--no-sync`: the stale installed entry point imports
   missing `simrecon._delivery`.
4. Directly invoke the current `simrecon_devtools.delivery.main` using the
   existing interpreter and `PYTHONPATH=devtools/src`: native initialization
   failed on the read-only filesystem.
5. Approved outer-sandbox retry, preserving the native doctor's read-only
   sandbox: initialization reached Codex 0.167.0-alpha.4, then failed with HTTP
   401/token-refresh failure; MCP also reported HTTP 451. Exit 1, no doctor report.

These are environment/tooling failures, not product-red evidence. #107 already
describes the same native failure mechanism. The stale entry point and dependency
availability need setup recovery; they do not establish a new product defect.
GitHub CLI networking failed, but the GitHub connector successfully provided
open/closed and mechanism searches. Search results are a dated snapshot, not a
claim about inaccessible repositories or future issues.

## Cloud doctor and PR contract

The owner requested a PR for these dispositions, then requested a cloud-capable
doctor, preferably a skill. The coordinator owns report/disposition/publication;
the policy author owns the new lessons-doctor skill and nine directly affected
instruction/template files. Route: human-requested policy amendment with fresh
independent policy review, plus report reconciliation. No runtime, tests,
workflows, dependencies or gate settings are changed by this PR.

The primary entry becomes `$lessons-doctor` in the current authorized cloud or
local session. It performs check-only, report-only or named documentation-patch
scope without a nested native CLI. Check-only writes nothing; issue publication
still needs actual authority, and independent review remains a separate fresh
session. The optional existing native CLI remains available on supported hosts.
This does not repair native authentication or qualify scientific-role reasoning.
PR109 separately supplies the qualified fresh tool-session policy for new roles;
its acceptance and route requirements remain distinct from current-session doctor
authoring and from the legacy native CLI.

Acceptance evidence: scoped cloud check-only exercise, independent policy and
closure review, complete inventory/hashes/links, then canonical `make verify` on
the clean committed candidate before push/PR. The skill is procedural guidance,
not an engineered sandbox or a deterministic checker. The owner subsequently
authorized merging PR111 after PR109 had actually merged, with conflicts resolved
first. That prerequisite is met; fresh integration review, renewed exact-candidate
verification and required CI still bind. Release is outside this request.
Human numeric limits are not set.

## Current state

208 observations have primary scoped dispositions: 194 no-action, 13 resolved,
0 tracked and 1 deferred. #99/#100 retain their resolutions against merged
PR103/102 and exact-candidate checks/reviews/CI. PR109's existing disposition now
resolves RM84-F001's investigation conditions, while native authentication remains
unrepaired. Its new observation separately retains CLOUD107-F001 no-action.
All original observations and append-only disposition records are preserved.
The earlier 207-source reconciliation was independently reviewed; the added
PR109 reconciliation awaits fresh integration review. Neither is a newly rerun
full mechanism analysis.

Initial native doctor execution failed authentication. The scoped skill change
removes that dependency from doctor authoring; it grants no new native-role
fallback. [Independent report reviews](review.md) cover the inventory/closure
work at their recorded baselines. [Policy review](policy-review.json) accepted
the ten exact instruction files after one check-only wording correction. The
[cloud check-only exercise](cloud-exercise.md)
completed three representative findings without nested authentication or writes.
Those historical exercise/verdict bytes are unchanged. The pre-PR109 candidate
`9f8d17a84e1e56005a1191dfca7fe48360cb13bb` passed the 13-phase local gate with
3,369 tests and received final independent acceptance before PR111 publication.
That result does not verify the changed integration candidate. Renewed exact
candidate, preflight, full-gate, fresh review, CI and merge outcomes belong in the
existing ignored `artifacts/lessons-doctor-pr/status.json` and gate receipts, plus
the PR/conversation, outside verified tracked bytes. No later result is predicted.

The initial [remote snapshot](remote-issues.json) belongs to its original cutoff,
not the current repository-wide issue count. [Publication receipt](publication.json)
records the exact #107 recurrence update/readback; zero new issues were created.
The first main integration added the RM84 cloud readiness/native backing
observations. The later PR109 integration adds the CLOUD107 observation and its
two scoped dispositions; all were read. Reconciliation baseline is `836ec79`,
retaining the approved platform/gate policy. Its [remote evidence snapshot](integration-109-evidence.json)
records PR109's actual head/merge identities and successful Verify341; those
results belong to PR109, not the integrated PR111 candidate.

Accounting preserves five failed doctor invocations, one failed CLI issue query,
one corrected connector argument call, one withdrawn F003 issue draft after
PR87 evidence, and the later F001/F002 stale-status correction. The original
report review plus a fresh closure review are two independent report rounds;
closure corrections fixed cutoff and integrated method wording. Skill author,
cloud exercise and fresh policy reviewer are three additional launches (five
known delegated launches for this task in total before final readiness review).
Two pinned preflights and the first full gate passed; the sixth delegated role
completed final readiness review with acceptance. This integration adds one
reused adviser session, initially read-only and then explicitly assigned report
authorship; it supplies no independent verdict. The coordinator owns conflict
resolution.
Later preflight/gate/review attempts follow the external completion pointer,
including the fresh integration reviewer still required. Prior task accounting
is not reset. Actual served attribution, tokens, cost and complete elapsed
measurements remain unknown.

Removed the task-created temporary uv cache and confirmed absence. No owned
fixture/reader cache was changed by triage, and no cleanup errors occurred.
Preserve current checkout, existing environment, unrelated work and durable
reports/dispositions/verification evidence. No disposable worktree was created.
The branch is `docs/lessons-doctor-2026-11-14`, published as PR111. Next action is
renewed exact-candidate verification and fresh integration review, then an
authorized push and merge after required CI and merge conditions pass.
