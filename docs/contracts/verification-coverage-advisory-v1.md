# VERIFICATION-COVERAGE-ADVISORY-01: measurement without a percentage gate

**Version 1.0** Git versions revisions.

The owner's “Switch percentages to advisory” instruction authorizes this narrow amendment to [VERIFICATION-RECEIPT-01](verification-receipt-v1.md). [ASD-COVERAGE-01](../tasks/asd-coverage-policy.md) records scope, ownership, independent reviews and activation. It supersedes the original V1/V3 requirement that every measured statement/branch execute; it changes no scientific behavior or receipt schema/version.

## Public behavior

The existing `make verify` and `python3 scripts/verify.py` entry points, arguments and all 13 phase commands remain. Coverage.py continues native branch/subprocess measurement, JSON/HTML/terminal reporting and every owned file under `src/simrecon/` and `scripts/`, including never-imported files. The [project policy](../PROJECT.md#coverage-policy-and-adoption-provenance) selects no numerical coverage threshold. [Coverage.py's fail_under setting](https://coverage.readthedocs.io/en/latest/config.html#report-fail-under) is zero; covered/total counts stay visible without imposing a percentage failure.

G1: When every phase succeeds and the other existing evidence guarantees hold, valid partial or zero execution may yield exit 0 and a passed receipt. Preserve the existing exact integer `statements`/`branches` covered/total objects for every owned file, package and global sum. Partial statements, branches or both are allowed. A never-imported file records zero covered with its measured total; a branchless file records branches 0/0. No display-rounded percentage substitutes for the native counts. The successful helper says that configured checks and evidence validation passed; the independent behavior/risk audit remains separately required and is not certified by this receipt.

G2: Measurement integrity still binds. JSON and HTML must be current; every owned file and required native branch/counter/destination evidence must exist. Counters must be nonnegative integers, covered counts cannot exceed totals, and native executed/missing counters and destinations must agree. Unapproved owned-file exclusions remain failures. Missing/malformed/inconsistent evidence cannot pass merely because percentages are advisory. Valid negative native branch exit destinations remain permitted. A phase command failure still fails and stops later phases, retaining any valid current partial native counts as diagnostics.

All other V1–V5 obligations remain: complete successful phase execution; clean unchanged candidate/input identities; output/Git protection; sole valid wheel and digest/version evidence; honest context/environment fields; failure statuses; no retries, Git mutation or publication by the helper. [Same-run M25 export](measurements-export-v1.md) remains mandatory for this repository's `make verify`, with the unchanged 33,554,432 B (32 MiB) limit. No scientific tests, discovery, subprocess instrumentation, platform jobs or dependencies are removed or changed.

## Review and migration

The original full-percentage requirement in VERIFICATION-RECEIPT-01 is retained as historical context; this amendment governs the two superseded coverage conditions for the adopted candidate and future tasks. A policy edit alone changes no installed executable gate or previous result. Fresh independent policy review and fresh bounded review of the exact full-local-passing candidate are required before publication. No other in-flight task is migrated, and all historical checkpoints, attempts and spending remain intact.

Meaningful tests use the public helper in disposable repositories and real Coverage.py reporting commands. Preserve missing-report/file/native-evidence and malformed/excluded-data rejection tests. Reclassifying valid partial execution from failure to success retains its measured-evidence assertions; it does not remove an obligation. Full exact-candidate local verification and configured CI platforms remain required.
