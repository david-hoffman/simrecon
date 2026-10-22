# Test fixture disk lifecycle

**Version 1.0.** The owner requests reducing test disk use and fixing fixture
cleanup before continuing CI speed work. This is high risk because earlier
deletion changes persisted-data lifetimes. The request authorizes the scope
and fresh A/B/C/D transitions without another acceptance interview.

## Approved behavior

Use the locked pytest9.1.1 implementation's `tmp_path_retention_policy = "failed"`.
Keep its existing retention count3; do not select `none` or count0. Preserve
strict pytest outcome policy, four-worker loadgroup/zero restart scheduling,
all existing test assertions/oracles, current coverage gates and public runtime.

For newly created function `tmp_path` scratch, cleanup is dependency-provided
and best effort, with these exact observable meanings under the locked version:

1. A passing call is eligible for immediate fixture-teardown cleanup, before
   later tests finish. No function payload is needed after its consumers close.
2. Setup failure/skip after `tmp_path` construction but before the call also
   allows cleanup. A passing call followed by teardown failure does not promise
   preservation. Required failure diagnostics must remain outside scratch.
3. A failed call retains its directory in an unsuccessful session, subject to
   the existing count3 retention. Call-time skips/expected failures may also
   retain it; this project still rejects skipped/xfail/xpass outcomes.
4. Successful default numbered-session completion removes its session base,
   including factory/module/session scratch after all consumers have finished.
   In real four-worker execution, retain local resource groups and close workers
   before controller cleanup. Module factory data must stay live for all its
   consumers; do not delete it after the first function using it.
5. An explicit `--basetemp` does not receive this final whole-session removal.
   Per-function eligible cleanup still operates. Do not claim this setting
   cleans arbitrary custom roots, crashed processes, coverage artifacts or
   historical fixture repositories.
6. Cleanup must preserve distinct neighbors, external retained evidence and
   external symlink targets. Required reports/logs/native coverage/M25 exports,
   canonical reader cache/inputs, existing original links and their dependencies
   remain outside disposable new session directories. Existing reservation,
   restoration, child-closure and original-byte assertions stay binding.

The source meaning above is narrower than the stable documentation's broad
error-retention wording. There is no promise that every failing test's fixture
survives, or that ignored removal errors mean successful reclamation.

## Scope and proof

Fresh blind A owns new `tests/test_fixture_lifecycle.py` and
`tests/fixture_lifecycle_fixture.py`. Use genuine public pytest subprocesses,
small generated payloads, native filesystem observations and outside sentinels.
No implementation-source inspection, private-state test, synthetic product-red,
new runtime cleanup seam, generic pruner or data mutation is required. Shipped
test-generated child workspaces belong to the outer pytest fixture lifetime;
normal successful runs must not add permanent audit scratch. Keep canonical
coverage instrumentation and its inherited outside-scratch destination intact.
One-off blind-role diagnostics retain their original evidence separately.

Fresh blind B independently reviews all lifecycle outcomes, legitimate metadata
and failure alternatives, preserved gates and observable filesystem oracles.
C owns only adding the named retention key in `pyproject.toml`; no other key,
dependency, workflow, discovery/coverage setting, test, fixture, scientific
runtime or public interface is writable. The retention setting is not a change
to discovery or coverage. Coordinator owns this contract/task documentation and
diagnostic execution setup. Fresh D assesses the exact passing integrated
candidate and actual disk/evidence results before submission.

Focused acceptance covers passing-call deletion while the session is still
live; call-failure retention; setup-error and late-teardown behavior; default
whole-session/factory cleanup; real four-worker execution; explicit-base limits;
and unchanged external bytes/symlink targets. Prefer coherent real CLI cases
over repeated unit examples. The baseline may legitimately fail these new
assertions because its configured retention is `all`; record actual status and
classify it rather than manufacture a failure.

Every test/probe uses newly created owned paths. Child subprocesses use a fresh
private `TMPDIR`, clear inherited `PYTEST_DEBUG_TEMPROOT` (which otherwise wins),
and normally omit `--basetemp` so real numbered-session behavior is exercised.
An explicit-base compatibility case uses its own unique fresh path. Outer
focused role checks use a unique role-owned explicit base; no shared historical
root or repeated existing `--basetemp` is permitted. Source-free diagnostics
apply before blind runtime checks and to their children.

Measure retained native allocated bytes separately from live peak allocation.
Qualify representative genuine large-fixture cases twice under distinct owned
numbered roots, retaining command/status, fixture/report/coverage identities and
before/after measurements. Show both independent runs complete and whether
payloads accumulate; do not infer a result from the configuration alone. Keep
module fixtures until their real consumers finish. A live roughly2GiB HDF5
staging allocation is a separate issue; neither change its representation-limit
test nor claim teardown removes a still-needed stage.

Do not continue the old profiling launcher that repeatedly makes unique custom
`--basetemp` roots with no cleanup. Future diagnostics use isolated owned
numbered namespaces and preserve required evidence outside them; failed runs
keep honest diagnostics and their stated retention limits. No historical
deletion is part of this change. Existing formerly planned cleanup leaves now
absent are recorded as externally missing, with actor/time unknown.

Full exact-candidate local `make verify` and the existing selected100% native
executable-line/branch-destination gates for every owned runtime/delivery file
remain mandatory before push or PR submission. Required M25, wheel, import,
audit, coverage JSON/complete HTML and original evidence must qualify from the
same accepted run. No CI-authoritative gate waiver or new numeric test target.
The CI<300s goal remains subsequent work; no local300s requirement is invented.
Record every launch/check/correction cumulatively, models/effort and actual
metering or unknown. Human total execution/review/spending caps are not set.
