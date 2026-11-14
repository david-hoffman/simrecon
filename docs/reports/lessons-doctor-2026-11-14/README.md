# Lessons reconciliation — November 14, 2026

**Version 1.0**

207 observations are inventoried in 11 semantic buckets. This is an incremental
coordinator reconciliation: the 203 source hashes in the independently reviewed
[prior inventory](../lessons-doctor-2026-11-11/inventory.json) still match, and all four
new observations were read (two arrived when main was integrated for publication). It is not a fresh full-backlog mechanism review.
The native doctor was attempted but could not complete because of authentication.

Initial baseline: `4dcc50dd70da2f93b4a3360e0a4160144656b35a`, initially clean.
Publication baseline: `87163657dd4e43e98adbc64ef8eca268c033084c` after
fast-forward integration of current main. Inventory cutoff follows final disposition reconciliation.
[Inventory](inventory.json) preserves exact source IDs, hashes, scoped inherited
states, findings and evidence. [Remote snapshot](remote-issues.json) captures
three open and five closed issues returned through GitHub, plus targeted searches.
No issue closure is treated as proof of resolution. No current conflicting
disposition was identified; the newer reader-parent record explicitly supersedes
only F002's earlier handling. New completion dispositions now resolve F001/F002
after reconciling merged remedies, exact-candidate checks/reviews and CI.

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
| B11 External and native capabilities | 12 | Prior decisions retained; current native launch failure duplicates open [#107](https://github.com/david-hoffman/simrecon/issues/107) |

Handling counts: 193 no-action, 12 narrowly resolved, 1 tracked, 1 deferred.
These carry forward the prior evidence limits; no-action is not a fix certificate.
The new-observation no-action decisions cover qualification knowledge for #99 and the
already-added naming grammar. F001/F002 are resolved against [completion evidence](completion-evidence.json)
from merged PR103/PR102: exact-candidate full gates, independent acceptance and
successful Verify runs. Private historical raw artifacts were not reopened.
The source correction report and current prerequisite documentation were read;
no product checks, synthetic probes or full verification were rerun.

F003 retains its stable ID, but its old continuation requirement is superseded.
The [current PR87 body](apparatus-pr.json) records a 600.76-second passing gate,
fresh final reviews and the owner's acceptance/stop instruction. The 300-second
goal was explicitly superseded for that submission; no new performance issue or
restart is warranted. This is no-action on further work under the retired goal,
not a claim that 300 seconds was achieved. Its prior tracked disposition is
superseded only for that scope. The task remains the historical execution record.

#107 is the remaining tracked lesson finding (RM84-F001). No new issue is needed. #99 and #100 are closed/completed and their scoped findings are resolved; #107 already covers this run's native launch
failure. The two new lessons add qualification knowledge and a naming gap already
addressed by PR104. A narrowly appended recurrence section was published and read back for #107; other issue bodies
remain unchanged. No implementation
is commissioned and raw lessons are not blind packets.

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
This does not resolve #107's broader fresh native scientific-role capability.

Acceptance evidence: scoped cloud check-only exercise, independent policy and
closure review, complete inventory/hashes/links, then canonical `make verify` on
the clean committed candidate before push/PR. The skill is procedural guidance,
not an engineered sandbox or a deterministic checker. No merge/release is
requested. Human numeric limits are not set.

## Current state

207 observations have scoped dispositions: 193 no-action, 12 resolved, 1 tracked
and 1 deferred. #99/#100 are closed/completed; their findings are now resolved
against merged PR103/102 and exact-candidate checks/reviews/CI. #107 remains the
only tracked lesson issue. Four new immutable disposition records preserve all
prior records and original observation bytes. This is a reviewed incremental
reconciliation, not a freshly rerun full mechanism analysis.

Initial native doctor execution failed authentication. The scoped skill change
removes that dependency from doctor authoring; it grants no new native-role
fallback. [Independent report reviews](review.md) cover the inventory/closure
work. [Policy review](policy-review.json) accepted the ten exact instruction files
after one check-only wording correction. The [cloud check-only exercise](cloud-exercise.md)
completed the three representative findings without nested authentication or writes; final exact candidate, full-gate/readiness results and
PR URL belong in ignored `artifacts/lessons-doctor-pr/` and the PR/conversation,
outside verified tracked bytes. Both initial and integrated pinned preflight
passed using the existing activation. No check result is predicted.

The initial [remote snapshot](remote-issues.json) belongs to its original cutoff,
not the current repository-wide issue count. [Publication receipt](publication.json)
records the exact #107 recurrence update/readback; zero new issues were created.
Current main integration adds the RM84 cloud readiness/native backing observations;
both and their existing scoped dispositions were read. Publication baseline is
8716365 and retains its approved platform/gate policy.

Accounting preserves five failed doctor invocations, one failed CLI issue query,
one corrected connector argument call, one withdrawn F003 issue draft after
PR87 evidence, and the later F001/F002 stale-status correction. The original
report review plus a fresh closure review are two independent report rounds;
closure corrections fixed cutoff and integrated method wording. Skill author,
cloud exercise and fresh policy reviewer are three additional launches (five
known delegated launches for this task in total before final readiness review).
Two pinned preflights passed; later gate/review attempts follow the external
completion pointer. Prior task accounting is not reset. Actual served attribution,
tokens, cost and complete elapsed measurements remain unknown.

Removed the task-created temporary uv cache and confirmed absence. No owned
fixture/reader cache was changed by triage, and no cleanup errors occurred.
Preserve current checkout, existing environment, unrelated work and durable
reports/dispositions/verification evidence. No disposable worktree was created.
The branch is `docs/lessons-doctor-2026-11-14`; next action is candidate verification
and authorized push/PR after independent policy acceptance.
