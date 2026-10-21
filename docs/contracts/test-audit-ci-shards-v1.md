# CI-SHARDS-01: standard jobs and a narrow evidence gate

**Superseded before implementation.** The independently reviewed
[standard workflow contract](test-audit-standard-ci-v1.md) retires this proposed
generic protocol. No B checkpoint was accepted and no production module was
implemented. Preserve its historical tests, reports and charges; this file is
not the active CI contract.

**Version 1.0.** The owner requests Ubuntu-only continuous integration (CI)
below 300 seconds, with valuable end-to-end/public-entry proof preserved. The
owner first prioritized test fixture disk use; that prerequisite has passed its
exact full local gate and fresh independent review. This is a continuation of
the same test-audit task, with every prior attempt and charge retained.

This contract authorizes blind test design and named implementation only after
the required checkpoints. The new workflow activates after independent review
of this CI-only scheduling contract and the exact passing implementation. The
local gate remains binding. No Superpowers or paid runner/token expansion.

## Behavior and ownership

Use ordinary GitHub Actions prepare, matrix and finalizer jobs. Pin every
checkout to the exact event SHA. Keep Ubuntu24.04, Python3.13.12, uv0.12.19,
Java21.0.7, pytest9.1.1, xdist3.8.0 and Coverage7.16.2. Add only pinned
pytest-split0.11.0 and pytest-reportlog1.0.0 plus their required resolved locks.
Use least_duration, one immutable timing file (initially{}), explicit complementary
groups1..N, four local loadgroup workers and max-worker-restart=0. The initial
workflow candidate uses 12 groups; this configuration still needs measurement. Queue before the first required job is separate; all later
waits, setup, transfer, finalization and post-job completion enter the measured
interval max(required completed_at)-min(required started_at), strictly<300s.

Local make verify/scripts/verify.py and its v1 arguments, 13 phases, receipt and
behavior remain unchanged. For CI only, amend the old parallel contract's
no-deselection/no-moved-check wording: complementary item partitions execute
the full reference exactly once collectively; logical checks can have truthful
different job origins. Existing resource groups stay within each VM; separate
VMs have independent mutable caches/locks/scratch. Existing seven baseline
fixtures remain unchanged and may recapture in another independent pytest
session. Never claim13global captures across the workflow. No A05 capture
observer, worker collection barrier, M25 protocol wrapper or custom scheduler.

Every job first bootstraps the exact locked environment, then records its
before snapshot. This initial sync is explicitly additional bootstrap. Prepare
then runs genuine sync, coverage-clean, lint, format, types in order, followed by
complete unsharded serial collect-only. Finalization also coverage-cleans its
new local output root before admission; it never cleans downloaded originals.
Every shard uses that locked environment and runs its actual selected tests under branch/subprocess coverage.
Finalizer first requires successful prepare and all matrix jobs, admits tests
evidence, combines all explicitly admitted native files with
--keep, and runs JSON, completeHTML, terminal coverage, wheel, isolated import
and locked audit in order. Additional bootstrap syncs are recorded as such.
No successful downstream phases run after known failed prerequisite/admission.
Native workflow steps/logs supply authentic command outcomes; no invented
single-process13phase receipt is emitted. Retain the existing required check
name on finalization where applicable. An always() finalizer must first reject
unsuccessful dependencies.

This is HIGH RISK: the recurring distributed completeness/evidence predicate is
a new custom oracle. Fresh native blind A/B, restricted C and fresh D apply.
A owns new tests/test_ci_evidence.py and tests/ci_evidence_fixture.py. C owns
new scripts/ci_nodeids.py and scripts/ci_evidence.py, plus ONLY replacing the
final unconditional sys.exit(main()) in scripts/verify.py with an ordinary
if __name__=="__main__" guard. All existing validator bodies, imports/constants,
CLI and local behavior remain unchanged. No extraction, monkeypatching or copied
gate implementation. Coordinator separately owns workflow/dependency wiring,
task/contracts and named infrastructure. C cannot edit tests/fixtures/workflows,
discovery/coverage settings, locks, skills or delivery policy. Scientific code,
oracles, frozen checkpoints and existing test assertions remain read-only.

## Small public interfaces

The opt-in public plugin is scripts.ci_nodeids. Existing invocations without its
options remain unchanged. --ci-inventory PATH requests complete semantic
collection output for collect-only; it is incompatible with execution annotation
mode. --ci-run-id UUID and --ci-shard-id ID enable execution annotation and must
be supplied together. Namespaced Item.user_properties keys are exactly
simrecon.ci.semantic_id, simrecon.ci.run_id and simrecon.ci.shard_id. Capture each
original Item.nodeid at the public pytest_itemcollected boundary, before
ordinary collection modifiers. Annotate only the required user_properties; do
not change node IDs, selections or marks. Store one value per
key; reject preexisting conflicting/duplicate namespace entries. TestReports
and standard reportlog carry actual semantic identity plus unchanged transport
identity. Literal @, Unicode and parameter punctuation are permitted; never
strip suffixes or inspect/mutate private _nodeid. The original pre-modifier
inventory is unique, ordered and nonempty. Inventory output is a JSON list of
exact strings. It uses a fresh exclusive file, retains existing bytes on error,
does not overwrite tracked/Git/private metadata or outside aliases, and belongs
to the admitted new job output lifetime. Failed collection/unsupported options
cannot produce admitted successful inventory evidence.

The companion CLI is:

    python3 scripts/ci_evidence.py snapshot --run-id UUID --stage STAGE
        --point before|after
    python3 scripts/ci_evidence.py tests --root PATH --run-id UUID --shards N
    python3 scripts/ci_evidence.py complete --root PATH --run-id UUID --shards N
        --admission PATH

STAGE is prepare, shard-ID or finalize. N is a positive integer; shard IDs
are canonical positive decimal strings 1..N without sign or leading zero.
UUID is a lowercase hyphenated canonical UUID string (the standard str(UUID)
representation); no additional UUID-version restriction is imposed. Snapshot
only reads current identity/tools/members. Successful snapshot and tests each
emit exactly one JSON value on stdout; successful complete emits a concise JSON
result, with diagnostics on stderr. Tests/complete read original inputs and
return0only on their specified successful predicate. Invalid arguments2; unavailable executable127;
evidence/operation failure1. Preserve authentic failures; no retry or silent
repair. Shell redirection and artifact transport remain workflow ownership.
No helper writes a passed full-verification receipt or executes phase commands.

Snapshot JSON has schema org.simrecon.ci-snapshot, nativeinteger version1,
run_id, stage, point, identity, source_root, github, environment, members.
point is exactly before or after. identity is the unchanged existing identity() structure: commit and tree Git
hex strings, dirty Boolean, untracked path list, and complete tracked manifest
(relative path -> lowercase SHA256). source_root is actual resolved cwd.
github contains repository, run_id, run_attempt, sha, workflow_ref, workflow_sha,
mapped respectively to actual GITHUB_REPOSITORY, GITHUB_RUN_ID,
GITHUB_RUN_ATTEMPT, GITHUB_SHA, GITHUB_WORKFLOW_REF and GITHUB_WORKFLOW_SHA.
Each value is its actual allowlisted string or null when absent locally. It
never serializes tokens, arbitrary environment or user data. environment
contains platform (actual platform.system()), machine (actual platform.machine()),
python, uv, java and packages. Each executable
record has exactly path, sha256 and version, holding the actual selected path,
lowercase SHA256 and actual version string; packages is a sorted
distribution-name/version mapping. Distribution names use standard canonical
normalization; conflicting duplicate identities fail. Python version and hash
come from actual selected interpreter; uv from selected executable; Java from
SIMRECON_JAVA, JAVA_HOME/bin/java or actual PATH selection, preserving real
nonzero/version/tool failures. No installed-package mutation occurs.

Native snapshots before/after all participating phases must have clean,
unchanged complete Git commit/tree/manifest and no untracked candidate input.
Compare each snapshot to current finalizer identity and common run/context.
Executable role/version/hash and package identities match; actual executable
paths may differ with equal identity. All native source roots must equal the
current checkout for this standard-runner scope; unsupported differing roots
fail instead of broad remapping or SQLite edits. Local same-platform genuine
integration is permitted with consistently absent GitHub context. In CI compare
every named context field to the current actual finalizer environment, including
null; absence is not a wildcard. When GITHUB_SHA is present, identity.commit
must equal it. Local genuine child fixtures may consistently clear the entire
allowlist. External GitHub qualification still binds head/base/integration/
workflow/attempt. Compare Git/tool/context across points, not output member maps,
which legitimately change. after snapshots occur only after participating command
processes close. Finalizer snapshots live in current-checkout artifacts/ci/
before.json and after.json, disjoint from downloaded bundles; tests requires
before, complete requires both.

## Evidence layout and recurring admission

--root contains exactly prepare and shard-1..shard-N stage bundle directories.
Each bundle retains repository-relative paths, with artifacts/ci/before.json
and after.json holding original snapshot bytes. Prepare also retains
artifacts/ci/inventory.json. Each shard retains original root .coverage* native
files, artifacts/coverage/pytest-reportlog.jsonl, actual reader inputs, any
original artifacts/verification/measurements.json and all ImageJ interop files.
Bundles remain separate, never merged into a live checkout. Standard pinned
artifact actions retain hidden/native files, reject missing required bundles,
disable overwrite, and use download9000827... digest-mismatch:error. Gate
validation must independently fingerprint actual admitted member bytes;
transport success alone supplies no completeness proof.

The producer members map is {relative_posix_path: {size_bytes, sha256}}, with
nonnegative native integer sizes (not Booleans) and lowercase SHA256 strings.
It enumerates every regular file in the exact retained roots/leaves declared
here: root .coverage and .coverage.* files; artifacts/ci/inventory.json;
artifacts/ci/durations.json; artifacts/imagej-reader/inputs.json;
artifacts/coverage/pytest-reportlog.jsonl;
artifacts/verification/measurements.json; and every file recursively below
artifacts/verification/imagej-interop/. Finalizer additionally inventories
artifacts/coverage/coverage.json, all artifacts/coverage/html/ files and dist/
files. Exclude before.json/after.json themselves to avoid self-reference.
Transferred prepare/shard bundles contain only their declared members plus the
two snapshots; command logs remain separate native workflow/artifact evidence.
The timing leaf artifacts/ci/durations.json contains the same immutable UTF-8
{} followed by LF in prepare and every shard. Prepare produces its nonempty
inventory; shards do not invent replacement reference inventories. Reader-input
bytes must match across all producer stages and the current finalizer. This
names the actual reader leaf artifacts/imagej-reader/inputs.json without moving
or editing its established schema/cache lifetime.
A shard before snapshot must contain no existing native, reportlog, M25 or
interop output; pinned reader inputs and immutable timings may already exist.
Prepare/finalizer use their actual stage lifetimes; no stale output may impersonate
new phase evidence. Each producer after snapshot records exact membership and
bytes after command closure, before transfer. Admission independently enumerates
each transferred bundle and requires exact declared membership and bytes,
including every admitted native filename. This catches a native file omitted
before admission. The admission ledger then additionally fingerprints both
original snapshot files to protect all transferred originals through complete.
Member files must be regular non-symlink files beneath their stage bundle;
symlink members, escapes and one member path resolving to another protected
original fail. Safe aliases for the root itself or separately supplied output
paths are permitted when they preserve the same resolved boundary and all
tracked files, Git metadata and retained external evidence. No blanket alias
ban, filesystem deletion or repair is authorized.

Tests admission requires all and only expected stage identities, snapshots,
nonempty reference inventory and native input sets, valid original standard
reportlog sessions, actual successful setup/call/teardown exactly once for
each selected semantic ID, and one unambiguous semantic/transport/worker binding
within its shard. Worker identity is the actual standard xdist worker_id field
on the native TestReport (gw0 etc.), not a guessed PID or suffix. Unrelated
JSON-compatible user_properties remain permitted. Native user_properties is an
array of pairs with exactly one occurrence of each reserved string key. If
native serialization loses this structure, reject it; never parse a display
string as recovered evidence. Require exactly
one standard SessionStart/SessionFinish and native0finish; phase reports must
belong to this closed session, while ordinary warnings may precede its start
or follow its finish. Reject skipped/failed/xfail/xpass, missing/duplicate/replayed stages, conflicting
properties, unsupported events used as substitutes, crash/interruption and
unexpected execution. Preserve ordinary warning/collection informational events
without mistaking them for call success. Cross-shard selected semantic sets are
nonempty, pairwise disjoint and their union equals the complete reference. Never
replace equality with counts, predictions, report text or green jobs alone.

All original native databases are admitted. Distinct paths may have identical
bytes; duplicate digests alone are not replay. Accept legitimate individual
empty contributions according to pinned official Coverage.py behavior; impose
no minimum file size, row count or per-file execution. Arbitrary malformed bytes
do not become valid merely by being empty. Reject absent,
malformed, changed or unsupported evidence. Retain original databases and
supported native combination, no exclusions/arc substitution/platform union.
Tests admission JSON has schema org.simrecon.ci-admission, nativeinteger version1,
run_id, shards (the exact positive integer N), identity (the common complete Git
identity), members (stage -> relative member -> {size_bytes, sha256}, including
both snapshots), and executions (stage -> semantic ID -> {transport_id, worker_id}).
Values are the exact observed strings; no inferred transport or worker identity.
The same per-item association must hold across successful setup/call/teardown.
No duplicate keys, missing/extra stages or unaccounted reference IDs are accepted.
It is an admission record, never a full passed receipt. Caller retains these exact bytes separately from input bundles.
Complete reads --admission and revalidates original membership/bytes and tests;
no own writes may invalidate the earlier admitted evidence. JSON duplicate keys,
invalid primitive types/Booleans as integers, nonfinite values, traversal,
unsafe member aliases, symlink escapes, unsupported schema and stale run/context
cannot pass. No invented byte/count/correction cap.

The exact M25 semantic identity is
tests/test_mrc_conversion.py::test_m25_native_memory. Export both
SIMRECON_MEASUREMENTS_PATH=artifacts/verification/measurements.json and
SIMRECON_MEASUREMENTS_RUN_ID=<common canonical CI UUID> to every outer worker in
every isolated shard. Match M25 ownership by exact semantic identity, never a
substring. These are the existing public export pair/output from
measurements-export-v1.md, with the exact unchanged caller identity made explicit. Exactly one actual semantic M25 test call and
exactly one original report must occur, in that same owning shard. Nonowners
have no report. Existing absent/partial pair rules, fixed output path, nested
isolation, native units, exact integer arithmetic and33554432B limit remain.
Reuse unchanged measurements(run_id) against the original owning bundle.
Do not rerun M25 to retrieve data or infer pixel/opaque assertions from JSON;
the actual passing frozen parent/child tests provide those assertions.

Complete also reuses unchanged metrics(problems) and artifact(), rejects every
reported problem, verifies the complete current owned inventory and both exact
covered==total metrics globally/perpackage/perfile, no missing/excluded/partial
scope. Every new helper is owned measured code. Fresh official Coverage.py
native JSON/HTML generation must correspond to explicitly admitted originals;
native/JSON counters/destinations and complete HTML source pages/indexes/assets/
local references must agree. Reuse supported official native reporting on an
owned disposable COPY for reconciliation; never mutate originals or silently
auto-combine/delete them. Small fresh owned scratch may be used and cleaned by
standard dependency lifetimes; keep all originals/external evidence unchanged.
The sole current wheel must pass unchanged format/RECORD/tag/hash validation
and match current packaged Python sources. Actual isolated import/audit/build
success remains a workflow prerequisite, not invented by this read-only gate.

## Expectation sources and scenario ledger

The owner-authorized CI behavior above is normative for this slice. Existing
public contracts measurements-export-v1.md, verification-receipt-v1.md and
test-audit-parallel-execution-v1.md supply unchanged resource/local obligations;
the CI-only scheduling amendment above supersedes conflicting parallel wording
only in this slice. Primary pinned API references establish representation:

- [pytest collection order](https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/hookspec.py#L233),
  [Item.user_properties](https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/nodes.py#L678)
  and [phase report properties](https://github.com/pytest-dev/pytest/blob/9.1.1/src/_pytest/reports.py#L441).
- [xdist actual worker_id](https://github.com/pytest-dev/pytest-xdist/blob/v3.8.0/docs/how-to.rst#L27)
  and [native report transmission](https://github.com/pytest-dev/pytest-xdist/blob/v3.8.0/src/xdist/remote.py#L281).
- [reportlog controller writer and event serialization](https://github.com/pytest-dev/pytest-reportlog/blob/v1.0.0/src/pytest_reportlog/plugin.py#L26).

The source inspection establishes API expectations; it is not an executed
compatibility result. Actual pinned four-worker integration remains required.
A maps every stated decision and permitted-positive class; B independently audits
omissions. The ledger is not a test-count cap or a license to invent rejections.

| ID | Observable decision and credible failure to distinguish |
|---|---|
| CS01 | Opt-in semantic annotations preserve original special IDs, native transport and actual worker identity across genuine collection/reporting. |
| CS02 | No-option compatibility, paired annotation options and exclusive collect-only inventory mode retain their distinct behavior. |
| CS03 | Complete original inventory is unique/nonempty and cannot be admitted after failed collection. |
| CS04 | Snapshot faithfully records actual clean identity, selected tools/packages and exact allowlisted context; differing safe executable paths may share identity. |
| CS05 | Producer before/after lifetime and pre-transfer member inventory distinguish fresh complete outputs from stale, changed or omitted members. |
| CS06 | Exactly expected stages and one closed successful native session per shard are required; ordinary warnings outside the session remain permitted. |
| CS07 | Exactly one successful setup/call/teardown association per semantic item is required; any skip/fail/xfail/xpass/crash/replay blocks. |
| CS08 | Selected sets are nonempty, disjoint and exactly cover the reference; equal counts cannot substitute for equality. |
| CS09 | Namespace pairs remain structured/unique; unrelated JSON-compatible properties and literal parameter punctuation remain legitimate. |
| CS10 | Native inputs retain every original path, accept official empty contributions/identical bytes at distinct paths, and reject malformed or changed evidence. |
| CS11 | Common Git/source/tool/package/context identity binds all stages and current finalizer; local all-absent context is legitimate. |
| CS12 | One exact M25 owner/call/original export binds same-run identity, native integer arithmetic/units and existing resource limit. |
| CS13 | Admission records fingerprint all transferred originals; complete revalidates that exact record and bytes. |
| CS14 | Official combined native data and current complete source/JSON scope agree at exact selected 100% globally/per package/per file. |
| CS15 | Complete HTML source pages/indexes/assets/local references correspond to current source/native reports; partial evidence fails. |
| CS16 | Sole current wheel satisfies unchanged validation and packaged-source correspondence; build/import/audit outcomes remain real workflow prerequisites. |
| CS17 | Strict JSON/schema/type/path/member rules reject unsupported evidence while safe root/output aliases preserve protected originals. |
| CS18 | Argument, missing executable, evidence/operation failures preserve specified exit status and original bytes without silent repair. |
| CS19 | Existing local v1 CLI/13 phases stay unchanged and importing its public validators does not execute main. |
| CS20 | Ordinary workflow dependencies, exact event checkout and closed-run timing remain independently qualified; incomplete runs never achieve the speed goal. |

## Scenarios and qualification

Inventory all decisions coherently: authentic complete distributed success;
legitimate special IDs/branchless files/empty individual native inputs/path-role
equivalence/local context absence; missing/duplicate/unexpected execution or
stage/session; strict outcomes/worker failure; stale/dirty/changed identity,
tools/native/member bytes; malformed JSON/types/namespace/report representations;
one M25 owner and valid versus stale/duplicate/invalid resource evidence;
native/report/scope/threshold/complete-HTML defects; current wheel and source
integrity; preservation and producer failure/aliases; unchanged local CLI/guarded
import; truthful docs and final closed workflow timing. Equivalent values are
examples, not new semantics or a deletion/test-count target.

Prefer genuine subprocess/public-command tests with small real pytest/xdist/
split/reportlog and Coverage outputs. Synthetic wheel/metadata fixtures must be
identified as controlled boundary data, never claimed as production full-run
proof. New fixture workspaces belong to outer pytest lifetimes; diagnostics,
native originals and required reports stay outside disposable child scratch.
Blind A/B receive only approved contract/interfaces/primary expectation sources
and sanitized diagnostics; no implementation/history/coverage maps/current
lessons. Fresh B audits legitimate positives, independent oracle and omission
risks. Fresh C cannot fix reviewed tests. Fresh D reviews passing exact candidate
and final declared audit preservation scope.

Before dependent work, cheap interpreter/platform/lock/install/import/tool checks.
Any blocker gets fresh clean Astra advice. Prove pinned hook/property propagation
and actual complete multi-shard union before full CI adoption. Require exact
clean candidate LOCALmakeverify/all13/native100/nativeJSON/fullHTML/M25/wheel/
import/audit/interop qualification before push; configured Ubuntu independently
repeats complete distributed proof with qualified originals. No CI-authoritative
waiver. Actual complete closed successful workflow must be<300s; forecast and
aborted/partial runs are not achievement. All earlier/draft/probe/role/check/
correction charges persist, total human execution/review/spending limits unset,
missing metering unknown. No PR-body messaging, merge, release or daemon.
