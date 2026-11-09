# Resumed measurements

The sole task state is [the task record](../../../tasks/test-apparatus-optimization.md).
Original discovery ledgers and accounting remain in the parent directory.

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

## Candidate pointer

The resumed role exports preserve both scientific rounds and fresh B verdicts,
all 26 consolidation keeper mappings, bounded group/native/reader qualification,
quality failure and repaired pass. Final canonical run/review/hash/cleanup/remote
results are kept outside tracked candidate bytes in the PR and conversation,
with raw evidence under ignored `artifacts/test-apparatus-audit/`. No intermediate
focused result establishes the 600-second complete-gate goal.
