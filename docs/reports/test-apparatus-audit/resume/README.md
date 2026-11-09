# Resumed measurements

The sole task state is [the task record](../../../tasks/test-apparatus-optimization.md).
Original discovery ledgers and accounting remain in the parent directory. This
combined archive is nonblind evidence; do not provide it to blind scientific roles.

`baseline-measurements.json` is the compact native-run export. Compressed files
retain the original receipt, M25 export, coverage JSON, complete console timing
rows and JUnit cases. `baseline-summary.json.gz` includes the complete parsed
catalog, native integer measurements and successful-exec counts. `manifest.json`
records the compressed evidence bytes. Raw execve trace, native database/HTML,
wheel and phase logs remain in ignored `artifacts/test-apparatus-audit/baseline/`.
Raw traces are local because they contain temporary execution paths. The parser
and external uv wrapper remain in ignored `artifacts/test-apparatus-audit/resume/`;
the unchanged wrapper is also preserved in the original parent report.

The baseline was clean detached commit `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`,
tree `0fa2edf2df263fa08110daa26ceb22c847b2900b`. Pinned preflight passed with uv
0.12.19, Python 3.13.12, Temurin 21.0.7+6 and isolated Hatchling 1.32.4.
The actual full verification began at 2026-11-09 06:23:21 UTC and finished at
07:01:28 UTC. Its outer GNU-time wall measurement was 2287.89 seconds; JUnit's
pytest wall measurement was 2243.177 seconds. All 13 phases and 3087 cases passed.
The measured setup/call/teardown totals use pytest's printed precision and are
sums across workers, not elapsed time. The 723 declarations all have native
cases. `inventory-native-reconciliation.json` explains the eight-case static
estimate overcount; the generated workflow family has the estimated 68 cases.

Coverage.py reported 4783/4919 native statements and 1845/1952 branch destinations
across all 30 owned Python files, with no exclusions. Package counters are in the
JSON; complete native file counters are in its compressed source report. These
percentages are advisory; all-file report integrity remains mandatory. There is
no separate language-level statement metric or platform union. This is Linux
local evidence; Ubuntu/macOS CI must run the configured full checks on the PR.

Same-run M25 observed baseline=peak=134084 KiB and increment=0 bytes against the
unchanged 33554432-byte limit. Zero observed increment is a high-water resource
observation, not a claim that conversion allocates no memory. The fresh run ID,
raw export and receipt match. No second M25 run was used to retrieve numbers.

The external wrapper adds durations/JUnit only to the exact top-level Make tests
argv; nested argv are unchanged. `strace 6.13 --seccomp-bpf` recorded successful
execve events, not every process creation or shell builtin: 15328 successful
execs, including 76 real pinned-JDK execs. The broader executable-name Java count
also includes synthetic Java inputs, so it is not a genuine-reader count. Actual
reader assertions/JVM observations are retained. GNU time came from the official
Debian `time_1.9-0.2_amd64.deb`, extracted under the existing shared tools root
because system GNU time and sudo were absent. Its path differs from the original
plan's `/usr/bin/time`; baseline/final use the same extracted executable.

This is one observed run after pinned reader preparation. Candidate checks have
warmer shared package/filesystem caches and useful worker concurrency. Identical
instrumentation does not remove host/load/cache uncertainty or establish a
statistical performance guarantee. Historical PR83 performance is not used.

## Continued attempts and candidate evidence

[CONTINUATION-EVIDENCE.md](CONTINUATION-EVIDENCE.md) records every retained
continuation, rejection, correction and limit. [continuation-files.json](continuation-files.json)
identifies selected source/archive hashes. `manifest.json` covers every portable
file here except itself, including the coordinator's `preservation-inputs.json`
and `change-accounting.json`. Original discovery and earlier resumed archives
remain intact. Added gzip files use deterministic mtime 0. The combined packet
is nonblind; only separately selected sanitized test costs go to blind roles.

Candidate 1 at `a41b378b10681c83029dd6f27fe3df65d66b22f2` passed all 13 phases
and 3066 cases in 829.59 seconds outer wall (783.316 JUnit pytest wall).
Candidate 2 at `8b9c39f7ea458a21c5feed39775005dc8cf487bd` passed the same phases
and case count in 611.04 seconds (564.184 JUnit pytest wall), missing the strict
600-second goal by 11.04 seconds. Both runs' preserved native receipt/M25,
coverage, time, complete console and JUnit exports are retained. Candidate 2's
complete parsed summary and compact reconciliation/resource/test-cost exports
are also retained. Neither run verifies later A7 bytes.

Candidate 2 reconciles exactly 26 old node identities removed, five clock
keepers added and 3061 unchanged. Only final @group suffixes are normalized;
spaces and internal @ remain. All eight native integer counters match baseline
across all 30 files. Same-run receipt/input/M25, all 30 HTML pages and combined
native database consistency were checked. Reader child evidence is filtered by
exact run ID. Canonical combine consumes raw shards without --keep; child data
retains its combined union, with no claim that raw shards survive post-combine.
The independent final bounded reviewer still assesses these gates and evidence.

The archive retains all A3/B3 representation failures, corrected A3/B4 acceptance,
A4/B5 workflow acceptance, A5/B6 acquisition acceptance, and the later A7/B7 edge
checkpoint. A6 regression factoring was measured, rejected and fully restored
before A7. Source-based archive-repacking diagnosis and genuine four-run JVM C1
measurements were rejected without source adoption; the initial missing-time
failure/resumption, actual Java JSON records and paired outputs remain charged.
The public-only advisor continued in its existing launch. Full comparison arrays,
raw traces and pstats stay untouched locally; concise numerical summaries and
hashes preserve their relationship without huge duplicate payloads.

A7's exact fixture is `ea32ed4fb891b18af81dcc557ef0ad1fa6ac958068406a8b20032b7acdfac7dc`.
Its 270 warn/raise comparisons match, completed acquisition proof passes 597
cases/18 warnings in 246.24 seconds (379.665 summed JUnit seconds), and all 13
source pins match afterward. Root make check passes all 116 lint/format files
and full Pyright. Final B7 accepts that exact checkpoint, with independent
closed/ownership, exact-comparison and factor-reuse controls. Compact qualifier
and independent B7 probe sources are retained. Focused proof uses the disclosed
artifact measurement plugin; it is not a canonical runtime result.

Earlier PRE-FORMAT timings remain separate from final ea32 observations; component
variance is explicit. The older workflow-facts-probe final-checkpoint attribution
also remains withdrawn and labeled PRE-GUARD; workflow-final-probe supplies the
correct guarded observation. Fourteen launches through B6 and fifteen through
B7, seven completed B reviews, all failed/partial/rejected work and reviewer
input corrections remain cumulative. Actual served model/token/cost totals are
unknown. Coordinator physical net line accounting is product 0, runtime harness
+38, tests/support +1238; these are not behavior or coverage statement counts.

Next exact-candidate canonical verification, same-run native coverage/M25,
under-600-second outcome, fresh integrated D/bounded review and preservation
sweep, platform checks and authorized publication remain coordinator obligations.
Final candidate hashes/results stay outside tracked candidate bytes in the PR
and conversation; raw evidence stays in ignored `artifacts/test-apparatus-audit/`.
No intermediate focused result establishes complete readiness.
