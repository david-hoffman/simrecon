# Reader deadline preservation during the test audit

**Version 1.0.** Contract: AUDIT-READER-DEADLINE. Test-only high-risk correction
within the owner's October 20, 2026 test-audit/runtime request. No product
behavior, timeout default, download endpoint, dependency or gate changes.

## Preserved obligations

The real reader preparation CLI retains its production 180-second parent fetch
deadline and 15-second socket timeout. A continuously active but incomplete
download must reach the parent deadline, fail honestly, stop its owned fetch
child, remove the partial download and stale input manifest, and preserve the
other authenticated jar. An outer test-harness timeout or rescue kill is not
evidence of product cancellation. Successful authenticated download and cached
reader/JDK loading remain covered by their existing real CLI tests.

The existing `test_missing_input_is_verified_before_publish` in
`tests/test_imagej_reader_setup.py` retains the independent 180-second default
argument check. The audit may replace the old physical three-minute witness
with a controlled composition: a fresh Python driver loads the reader module,
sets only the parent module's `FETCH_TIMEOUT_SECONDS` to a short test value, and calls its
entry operation. The genuine fetch subprocess loads the unchanged script with
its original cooperative and socket deadlines. This is test instrumentation;
it creates no supported script-as-library or configurable-timeout API.

Use real authenticated fixture bytes and an active local TLS transport with
distinct partial deliveries. The test must establish incomplete transfer and
continued activity, distinguish parent cancellation from socket/cooperative or
outer timeout, assert the parent-specific failure and nonzero status, and
observe child closure before any harness rescue action. Record whether rescue
signals were sent. Preserve all original cache/temp/manifest assertions. Do not
fake `TimeoutExpired`, replace the worker with a mock, manufacture an artifact
digest, or infer success from elapsed time alone. Choose timing bounds from the
controlled transfer and actual scheduling, with bounded outer waits and clear
nonwitness failures. No new performance acceptance threshold applies to the
production operation.

## Roles and allowed scope

Fresh blind A authors the test correction; fresh blind B independently reviews
the exact revision, observer reachability, retained proof and positive/failure
alternatives. Restricted C makes no product change unless a valid approved
product failure is diagnosed and separately scoped. Full exact-candidate local
verification and fresh D follow integration. The audit's bounded worker cannot
edit this checkpoint. All attempts and corrections remain cumulative.

A may read root AGENTS, test-work/test-audit skills, this contract, public reader
environment documentation, the original deadline test, relevant test fixtures
and existing reader tests. Implementation, implementation history, coverage
maps, coordinator state, discovery/advisor reports and existing lessons remain
excluded. Source-free diagnostics precede execution. The old observer's cleanup
ordering is a public test defect: its empty-child assertion observes state after
the harness has had an opportunity to kill descendants. This establishes no
actual product leak.

A owns the original deadline declaration in
`tests/test_shared_node_baseline_public_callers.py`, plus a narrowly scoped
observer addition in `tests/shared_node_baseline_public_callers_fixture.py` or
a new test-local deadline helper. Shared observer changes require B to assess
all affected test callers. All other declarations and shared numerical fixtures
are frozen. A separate new deadline test file is permitted if the old
declaration is retired with an explicit preservation mapping. No source,
workflow, dependency, coverage, policy or unrelated test edits.

Keep original actual-phase/reference/scientific checkpoints unchanged. Inherit
100% native executable-line/branch-destination coverage, current report
integrity, same-run measurement and full local verification. Required remote
platform is Ubuntu under the owner's explicit macOS CI removal. The full-suite
600-second objective is not permission to drop a behavioral obligation. Human
total execution/review/spending limits are not set.
