# One selected alternative launch-route probe — source ready, not executed

The named source is launch_route_probe.py. It is unparsed/unimported/unexecuted
in this preparation. Coordinator must inspect/freeze its code, both embedded
bodies, actual argv/FD derivation, inventory, command, grant and finite settings;
root captures fresh correspondence proof only afterward. A released grant is a
new file. This template has approved=false and pending proof/ownership fields.
No old accepted method, Q0/Q1 driver, grant, raw receipt or unknown terminal
measurement is changed. Q2-Q6 and any scientific workflow remain held.

## Diagnosis retained, with limits

Q0 passed pinned configuration. Original Q1 failed with posix_spawn setsid
NotImplementedError before PID return; its terminal usage remains unknown.
Coordinator diagnostic attempt1.json reports actual CPython3.13.12/glibc2.39,
HAVE_POSIX_SPAWN=1 and HAVE_SETSID=1. Matching upstream v3.13.12 source has the
unsupported setsid-flag guard before the libc spawn call. This is source/version
correlation, not proof of every installed binary compile-time detail, nor a
claim that runtime libc lacks setsid. Coordinator's scope-limited argv/time-window
scan found no matching child/orphan candidates or unread PIDs. That snapshot
plus the pre-spawn source guard supports current owned-resource disposition;
PID absence/null alone does not prove no spawn. Original evidence remains:

- Diagnostic: `0f3e3b69cff042e1802c3e229c3b1e7e1648f06084a0f7de65aeb8e6d23745cf`.
- Matching upstream source: `b5cc39c677fca677ee9890dffa7d535ca43ae0cf4a2e8c164595daedacef3417`.
- Q1 scoped disposition: `481b3b12096fd112aa30716c189430910fb5ad51cc3bb18df10c095311e00b2e`.
- Failed Q1 receipt: `f1aa18a0cf4f1afe0ec399cc141226330c447dbd59e499b7ec84c70ce340c70a`.

One initial disposition read used the wrong directory and returned missing-file
status; the exact file was then found under build-diagnostics/ and hashed/read.
No new runtime diagnosis or fallback capability probe ran during authoring.

## Selected route and exact proposed command

Plain os.posix_spawn has no setsid/setpgroup attribute. Its one pinned-Python
bootstrap calls os.setsid, writes a bounded readiness JSON line, closes that
pipe, then os.execve's the pinned normal target in the same PID. The target
prints PID/PPID/PGID/session/nonce/executable/mapped-namespace and exits zero.
Neither body imports scientific/product modules or creates descendants. No
fork route, fallback matrix or retry exists.

Proposed command AFTER coordinator freeze, fresh root proof and exact release
(NOT EXECUTED):

```sh
docker exec --user 1000:1000 -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e PYTHONDONTWRITEBYTECODE=1 -w /workspace/work/issue-116 simrecon-campaign-ubuntu .venv/bin/python docs/reports/reconstruction-working-set/qualification/launch_route_probe.py --grant docs/reports/reconstruction-working-set/qualification/grants/launch-route-released.json --attempt-id launch-selected-a1
```

Bootstrap argv is exactly `[sys.executable, '-c', BOOTSTRAP, str(ready_dst),
nonce, sys.executable, TARGET]`. Target exec argv is exactly
`[sys.executable, '-c', TARGET, nonce]`, with inherited controlled environment.
The only runtime-derived argv slot is ready_dst from the frozen FD allocation
algorithm. Intent records preserve its actual numeric FD/action list before
spawn; receipt preserves observer and child argv. Frozen body hashes:

- Bootstrap: `3353b2cedc9d17eace4ce5ebc5651799e2bc432e493107a64b924ae2cdf6be37`.
- Target: `85e5394feb08a8eef86a783e88c1c86bbeddc901da0ab8ee10d0943ac27f9010`.

These are source-byte digests, not executed fixture hashes or probe results.

## FD/readiness/ownership invariants to inspect

Pipe originals are CLOEXEC; both pipe ends, stdout/stderr sources and a distinct
readiness destination are reserved with F_DUPFD_CLOEXEC at64+. Each reservation
uses an unused descriptor. Thus source/destination/stdio collisions are avoided
even if lower descriptors are occupied or absent. Insufficient descriptor limit
is a failure before spawn, not permission to change routes. Child actions dup
stdout/stderr to1/2, dup the write source to the distinct readiness destination
(clearing CLOEXEC there), then close the other sources/read end. Parent closes
all its write aliases immediately after successful spawn. Bootstrap closes its
readiness FD before exec; target retains no intended writer.

Parent reads nonblocking in bounded chunks, validates one readiness line, and
drains buffered bytes even if exact wait4 has already cached terminal exit.
EOF without valid readiness is failure, never success. Returned PID must equal
bootstrap and target PID; both PGID/session must equal it and nonce/executable
must match the released grant. Target namespace must match exposed mapping.
Normal exit, terminal cache identity and Linux native-unit conversion are also
required. No sampled RSS can substitute for missing terminal evidence.

One reviewed WaitOwner alone calls exact-PID wait4. Probe cleanup never calls
its group-send or reviewed group-cleanup helper. Until and after readiness,
only a still-owned, unreaped direct PID may receive TERM/KILL; ownership loss
blocks signals. Reap status is checked first, preventing PID reuse through that
owner. Finally closes all retained parent descriptors and records terminal usage
or explicit missing/cleanup gap. Intent precedes spawn and owned marker follows
PID return. Spawn-to-owner/marker and abrupt-parent-death gaps remain. PID1=sleep
is no general reaper; this probe never deliberately kills the wait owner or
creates an orphan. Any unresolved ownership blocks another attempt.

## Finite bounds and outcome scope

Inventory fixes 5s overall/readiness, 0.2s TERM grace, 2s KILL/reap, 10ms polling,
1,024-byte readiness validation cap (bootstrap write capped512B), target record
2,048B, process stop256MiB, host minimum512MiB, predicted tiny-child64MiB plus
native allowance64MiB and extra reserve256MiB. Actual ancestor thresholds and
proof remain root decisions from fresh exposed correspondence; no stale record
is admission. External ancestors remain unknown. Deadlines do not hard-bound
all filesystem/kernel/scheduler stalls; sampling/signals can race or overshoot.

Every failure preserves artifacts under qualification/launch-route-attempts and
stops. Even success means only selected_tiny_route_observed_only: terminal wait4
is kernel-reported direct-child usage through final exit. Inherited/pre-exec/
exec-transition high-water retention remains unresolved; same PID does not
guarantee every bootstrap/startup peak survives exec. No subtraction/aggregate/
benefit claim follows. It qualifies neither the scientific
method nor arbitrary recovery. Root assesses actual route evidence before a
minimal method rewrite and fresh affected review5. No source correction to the
accepted method is made here. Actual model/tokens/cost remain unknown; earlier
attempts/charges persist. No execution process or disposable scratch exists yet.
