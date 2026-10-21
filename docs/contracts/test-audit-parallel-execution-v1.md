# Parallel execution during the test audit

**Version 1.0.** Bounded infrastructure maintenance under the owner's October 20,
2026 request for a full suite taking at most 600 seconds. This changes scheduling
and a development dependency. Scientific behavior and test expectations stay
under their existing owners. The [audit task](../tasks/test-audit-linux-ci.md)
retains the exact-candidate local gate and Ubuntu CI measurement requirement.

## Ownership and preserved behavior

One bounded infrastructure worker owns `pyproject.toml`, `uv.lock`, the outer
`Makefile` tests command, `src/simrecon/_pytest_policy.py`, `tests/conftest.py`
and `tests/test_test_run.py`. A fresh independent reviewer assesses the exact
passing candidate and preservation evidence. The reader deadline author owns
its separate frozen checkpoint. No scientific test, coverage configuration,
measurement writer, runtime algorithm or verification validator belongs to this
packet. Coordinator owns task/contract/report records.

Use maintained pytest-xdist 3.8 or later within major version 3, locked with its
resolved dependencies. Invoke four workers and `--dist=loadgroup` only from the
outer Makefile command, with `--max-worker-restart=0`. Keep project-wide pytest options and nested pytest
commands serial. No custom scheduler, daemon, retries, tolerated worker loss,
test deselection or moved checks are authorized.

The pytest session policy must retain the same acceptance predicate: passing
complete execution succeeds; empty discovery, runtime/collection skips,
expected failures, unexpected passes, ordinary failures and collection errors
fail. Recognize an actual xdist worker through its session/configuration, not
an inherited environment variable. The controller receives and enforces the
aggregate outcome. A nested serial invocation inside a worker still enforces
the policy. Do not introduce a generic missing-reporter success path.

## Resource and fixture boundaries

Give each affected item one effective group. All mutators and genuine consumers
of `artifacts/imagej-reader` run in the same group, including the actual reader
callers, authentic infrastructure cases, supplement reader cases and ImageJ
export module. Confirm collection/imports do not mutate that shared cache.
Keep all consumers of the seven immutable verifier outcome fixtures together so
they capture exactly 13 real outcomes, then independently copy observations.
Other tests remain independently scheduled. Multiple overlapping group marks do
not implement mutual exclusion and are not a valid preservation argument.

Preserve canonical M25 as one same-run writer, exact node identity and root run
identifier. Keep disposable repository/output/process/port resources isolated.
Assert shared-reader restoration and owned-child closure in the pilot. Do not
remove reservation, restoration or cleanup assertions to permit concurrency.

## Qualification and completion

Before enabling full parallel verification:

- Exercise the real pytest CLI serially and with four workers for each policy
  outcome above. Distinguish intended collection errors from accidental import
  or internal errors. Include nested serial policy enforcement inside a worker.
  A controlled worker-crash case must fail, positively report disabled
  replacement and show no replacement gateway in its native lifecycle.
- Run the same selected resource-sensitive nodes serially and in parallel, in
  separate nonoverlapping runs. Include all shared immutable-outcome consumers,
  cache reservation plus a genuine ImageJ consumer, M25, source-free nested
  pytest and phase-estimation child reentry. Retain node identities, outcomes,
  worker assignment, exactly-once counts, fixture capture count, run identity,
  cache restoration and process-closure evidence.
- Use separate native coverage destinations. Observe contributions from
  multiple workers and a relevant owned child; do not union serial and parallel
  pilot data or reuse pilot coverage as final gate evidence.

Then run complete exact-candidate `make verify`. Preserve current reports and
the selected 100% native executable-line/branch-destination targets globally,
per package and per file across all owned runtime/delivery tools, including
never-imported files and relevant subprocesses. Preserve all verification
phases, same-run measurements, wheel/import/audit and evidence integrity. A
pilot speedup is not a full-suite timing result. Report complete suite and
verification wall time separately; Ubuntu needs its own observed CI run.

Fresh final review covers policy semantics, resource connectivity, frozen
checkpoints, coverage/report evidence and the exact passing candidate. New
meaning or a weakened acceptance predicate returns to intake. Diagnose failures
before repair and consult a fresh clean-context Astra advisor for issues, as the
owner instructed. All attempts and corrections remain cumulative. No human
total execution, review or spending limit was set.
