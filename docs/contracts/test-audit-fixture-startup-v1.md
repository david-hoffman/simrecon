# Controlled command startup during the test audit

**Version 1.0.** Bounded test maintenance within the owner's
[test-audit request](../tasks/test-audit-linux-ci.md). The full-suite objective
remains 600 seconds. Full local verification, independent review and observed
Ubuntu timing remain required.

## Ownership and expectations

The bounded worker owns a new `tests/fixture_command_launcher.py` helper and
only the executable builders/imports in `test_verification_receipt.py`,
`test_measurements_export.py`, `test_verification_output_protection.py` and
`test_verification_wheel_hashes.py`. Preserve every case, assertion and original
Python producer body. The real verifier CLI, its child producers and native
subprocess coverage remain active. Do not change evidence-output producers,
scientific code, gates, discovery, coverage configuration or dependencies.

Use a same-file POSIX shell/Python launcher for controlled external command
stand-ins. The shell may answer exact existing version queries and existing
no-op phases. It must retain the original argument ledger, mode handling,
status and output. Actual producing, rejecting and output-protection phases
execute the original Python body with the original interpreter and arguments.
Whitelist only demonstrated no-op phases and exact command forms. Inputs
requiring JSON escaping, unusual command forms or nonordinary ledger targets
take the existing Python path. Preserve missing versus empty environment
values and measurement-before-command ledger order. Propagate write failures.
Do not add an alternate general JSON encoder, disable instrumentation or
substitute prerecorded verifier observations.

The same worker separately owns only
`test_shared_node_baseline_public_callers.py::test_source_free_live_path_subprocess_fields`'s
controlled timeout input and matching duration expectations. A 150 ms child
deadline can expire before Python prints the required prelude. The merged
fixture inherits the approved upstream readiness gate after both streams are
flushed, then uses `Popen.communicate(timeout=1.0)` with an event-blocked child
and bounded kill/drain cleanup. Status cases exit immediately through
`run(check=True)` with their 6-second timeout. Retain exact native exception
fields, both Path forms and all four rows. Check the exact float `1.0` timeout
and rendered phrase `timed out after 1.0 seconds`. This inherited readiness and
cleanup replaces the former 3-second-sleep and no-observer implementation
prescriptions for this merged fixture only. Add no observer beyond that
inherited gate; preserve capture, redaction, runtime and exception rendering
semantics. All other helper, reader, scientific and gate restrictions remain.

This correction supersedes the former containing-module hash. It does not
supersede the independently reviewed reader test's function bytes, its helper,
shared fixture, imports, production defaults or deadline/closure expectations.
Record those identities separately. The pre-existing direct-Path executable
rendering placeholder question is outside this timing correction; no claim of
complete executable-identity rendering follows from it.

Coordinator owns this contract, the task/report record, unique lessons and
ignored evidence. A fresh independent reviewer challenges the complete passing
candidate, including shell eligibility/fallback, ledger/oracle preservation,
timeout type and duration meaning, checkpoint identity and coverage evidence.
These are conventional fixture changes. New scientific, binary, security,
data-loss, custom-oracle or unresolved interface meaning returns to intake.

## Qualification and completion

Retain original-versus-candidate command comparisons for actual status,
streams, ledgers, artifacts and links. Record source identities and all failed
diagnostics; copied-test path adapters must preserve the original expectations.
Run all cases in the four affected modules and the four exact timeout cases.
Compare a fixed, order-balanced public-CLI timing cohort, preserving actual
worker identities and exact owned native file/line/arc/context sets. Fewer
Python stand-ins must not suppress measurement of owned child/grandchild work.
Keep original native databases separate; do not union diagnostic runs into a
gate or claim complete coverage from the cohort.

Run cheap quality checks, then complete exact-candidate `make verify`. The
selected native 100% executable-line/branch-destination targets, all owned
files, no-skips policy, 13 phases, same-run measurement, wheel import and audit
remain binding. Report suite and full verification time separately. A fixture
microbenchmark is no Ubuntu result. Consult a fresh clean-context Astra adviser
for issues. All attempts/corrections remain cumulative; no total execution,
review or spending cap was set by the owner.
