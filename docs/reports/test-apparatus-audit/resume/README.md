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

[CONTINUATION-EVIDENCE.md](CONTINUATION-EVIDENCE.md) records the later attempts,
limits and cumulative accounting. [continuation-files.json](continuation-files.json)
identifies selected source/archive hashes. `manifest.json` covers every portable
file in this directory except the manifest itself, including the coordinator's
`preservation-inputs.json` and `change-accounting.json`. Original discovery and
earlier resumed archives are retained. New gzip files use deterministic mtime 0.

Candidate 1 at `a41b378b10681c83029dd6f27fe3df65d66b22f2` passed all 13 phases
and 3066 cases in 829.59 seconds outer wall (783.316 seconds pytest), missing the
600-second goal. Its native receipt, M25, coverage JSON, time, complete console
and JUnit exports were verified against the preserved same-run originals.
`candidate-1-profile-summary.json.gz` adds compact duration/resource/exec counts
without copying raw traces or repeating full catalogs. This completed gate is
historical evidence for that commit; it does not verify later scientific inputs.

The continuation retains rejected A3/B3 representation findings, the corrected
1062-case A3 proof and B4 acceptance, A4's 465-case workflow proof and B5
acceptance, and A5's 597-case acquisition proof and final B6 acceptance/hash
manifest. A5's focused proof passed in 282.58 seconds with 18 warnings; it used
the disclosed measurement plugin. B6 reconfirmed the author's final report and
admission-summary additions before its final acceptance. Earlier evidence-only
snapshots remain separately labeled. All 26 earlier keeper mappings remain in
the original scientific ledgers. Fourteen known role launches and six completed
B reviews remain cumulatively charged; actual served model/token/cost totals
are unknown. Neither focused proof is a canonical runtime result.

The final guarded workflow timing is `workflow-final-probe`; the older
`workflow-facts-probe` final-checkpoint attribution is explicitly withdrawn.
Its archive is labeled PRE-GUARD. The continuation explains the provenance
correction. Rejected nominal-memo and two-thread Pyright experiments and the
public-only advisor report remain historical evidence, with their failures and
limits intact. `check-round5.log.gz` retains the passing final quality check.

Final exact-candidate canonical verification, same-run native coverage/M25,
600-second outcome, required integrated review/preservation sweep, platform
checks, cleanup and remote results remain coordinator responsibilities. Final
candidate hashes/results stay outside tracked candidate bytes in the PR and
conversation; raw evidence stays in ignored `artifacts/test-apparatus-audit/`.
No intermediate focused result establishes complete readiness.
