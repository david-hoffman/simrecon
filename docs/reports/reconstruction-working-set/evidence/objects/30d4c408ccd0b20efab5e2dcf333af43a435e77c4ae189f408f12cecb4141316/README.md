# Historical Q0/Q1 v1 preparation; current method5 driver correction

The original v1 source/inputs below were preserved before correction under
`/workspace/work/campaign/evidence/116/source-qdriver-before-method5/`. Actual v1
Q0 passed and Q1 failed with unsupported posix_spawn setsid; their original
grants/results are unchanged. The active driver now uses the shared fixed
bootstrap helper and `WS116-Q0-Q1-method5-v1` scope. Old source maps and old Q0
receipts cannot satisfy its changed prerequisites. See the new method5 template
and METHOD REVIEW5 input. No integrated-route execution is granted yet.

The following command/template narrative is historical v1 evidence, not a
current release. Current method5 requires renewed source/command/bounds freeze,
fresh root proof and a fresh source-matched Q0 prerequisite for Q1. Existing
NumPy2.5.3/SciPy1.18.1/Python3.13.12 facts remain useful version context only.

Q0-ready for coordinator inspection/freeze and root's fresh correspondence
capture. No driver import, syntax/lint check, lifecycle probe, scientific module
import or case execution occurred while authoring this new driver. This is a
reviewable proposal; templates have approved=false, unresolved ownership, empty
thresholds and pending proof fields so they cannot be treated as released grants.

Root's latest scheduling instruction prioritizes small Q0-context/Q1-normal
before broader Q2-Q5 work. Active method_qualification.py exposes exactly those
two cases. The broader unexecuted draft and inventory are retained as inert
fixtures/deferred-*.txt/json; synthetic-record.json is future synthetic schema
metadata, not data. None of those deferred bodies are read, imported or executed
by this slice. They are not frozen/released later-phase implementations.
Accepted observer.py/run_attempt.py/workload_child.py and all twelve accepted
method targets remain unchanged. The driver reuses reviewed helpers, never
run_attempt.main/workload_child.execute or any product workflow/fixture generator.
No separate prerequisite-review chain is requested solely for this driver.

## Freeze and proposed exact commands

Coordinator first inspects this driver, active inventory, stdlib-child.txt,
commands and grant templates, then freezes exact driver/fixture/method bytes.
Root captures fresh proof with its prepared capture-resource-domain.py only
when this inspection is complete. Do not reuse resource-domain-preliminary.md.
Root fills the proof path/hash/observed timestamp, expected exposed namespace/
mount/membership/limit map, actual ancestor thresholds, conditional rationale and
ownership disposition in new Q0-released.json and Q1-released.json. Preserve
original templates. Include additional accepted-target identities in source_sha256
if needed; existing required keys may not be omitted. Verify interpreter/candidate
identities rather than treating the template's past checkpoint as a new candidate.

The proposed bound for each ancestor is chosen from actual current/max with
ample reserve: it must exceed current + 256 MiB process stop + 256 MiB reserve,
and remain strictly below each finite limit. A conservative proposed choice is
min(finite_max - 256 MiB, current + 768 MiB), admitted only if all inequalities
hold and root accepts current competing work/uncertainty. For an unlimited
visible ancestor use a conservative finite threshold based on actual current;
at least one finite exposed bound is still required. These are internal design
settings, not a product memory cap or human total budget. Missing headroom is a
refusal, never permission to raise thresholds automatically.

After exact release, proposed Q0 command (NOT EXECUTED):

```sh
docker exec -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e PYTHONDONTWRITEBYTECODE=1 -w /workspace/work/issue-116 simrecon-campaign-ubuntu /workspace/.simrecon-tools/uv-env/bin/uv run --locked --no-sync python docs/reports/reconstruction-working-set/method_qualification.py --case Q0-context --grant docs/reports/reconstruction-working-set/qualification/grants/Q0-released.json --attempt-id q0-context-a1
```

Q0 records actual interpreter/NumPy/SciPy/backend/default FFT workers and OS/
thread/domain facts only; NumPy/SciPy imports are explicit in this later release,
with no numerical operation or product import. Exact source/hash/domain matching
and root's proof freshness are required first. Root inspects the Q0 receipt and
actual observations. Only a successful scoped Q0 receipt, with unchanged source
and exposed domain, can fill Q1's prerequisite path/hash.

After that separate Q1 release (NOT EXECUTED):

```sh
docker exec -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e PYTHONDONTWRITEBYTECODE=1 -w /workspace/work/issue-116 simrecon-campaign-ubuntu /workspace/.simrecon-tools/uv-env/bin/uv run --locked --no-sync python docs/reports/reconstruction-working-set/method_qualification.py --case Q1-normal --grant docs/reports/reconstruction-working-set/qualification/grants/Q1-released.json --attempt-id q1-normal-a1
```

No --all/batch flag, retry or growth loop exists. Fresh attempt IDs/directories
preserve refusals/failures. Root must diagnose failure before authorizing another
attempt; old failures and changed-source applicability remain recorded.

## Concrete finite safety settings

- Driver case soft deadline 20 s; normal child deadline 5 s.
- Sampling request 10 ms, TERM grace 0.2 s, KILL/reap bound 2 s.
- Child handshake parse bound 1,048,576 bytes. The frozen stdlib-only body emits
  one tiny JSON ready/session record and exits zero; it never holds, ignores TERM,
  creates children or performs numerical work in this active slice.
- Process stop 268,435,456 B; host MemAvailable minimum 536,870,912 B.
- Conservative predicted tiny-child envelope 67,108,864 B plus native/allocator
  allowance 67,108,864 B; extra reserve 268,435,456 B. These are source-design
  allowances, not observed peaks. Q0 module-import/observer costs consume exposed
  headroom too; actual preflight and root reserve judgement remain necessary.
- Correspondence proof maximum proposed age 300 s; current/host facts are read
  anew by admission/monitor. Unknown physical-host ancestors stay unknown.

Filesystem/import/provenance operations and scheduler delays are not made hard
real-time by these elapsed checks. Q0 is environment collection, without a child
RSS monitor during imports. Do not claim zero OOM risk or a comparative envelope;
ordinary #117/#118 checks may overlap qualification.

## Wait, cleanup and unexercised scope

Q1 uses os.posix_spawn(...setsid=True), one reviewed WaitOwner for the exact PID,
reviewed cleanup, bounded live-child RSS/host/ancestor monitoring and a terminal
cache-identity check. It confirms normal exit/session handshake/native Linux
KiB-to-byte conversion. Terminal rusage includes this tiny child through JSON/
teardown, not observer+child aggregation or numerical-only memory. Inherited/
pre-exec high-water remains a limit. Sampled RSS and terminal high-water differ.

Unexpected failure/cancellation enters owned cleanup where Python finally runs.
Lost ownership or missing terminal evidence is failure and blocks another case.
The spawn-to-owner/marker gap, abrupt observer death, repeated interruption,
blocked filesystem work and nonparent terminal-usage loss remain unexercised.
Root reports PID1=sleep with no init reaper: deliberately killing the wait owner
could leave an unreapable orphan/zombie. This slice never does that. Q3 real
observer-loss recovery remains HELD. A later exact-owned Linux subreaper scaffold
would need coordinator inspection, prctl capability checks before subtree spawn,
bounded adoptive reaping and explicit disclosure that adoptive cleanup neither
restores the original observer receipt nor proves general operational recovery.
If unavailable, hold that path; never knowingly leak an orphan.

No Q2-Q5, Q6/workflow or scientific corpus is released by success here. All raw
qualification attempts/receipts stay under qualification/attempts, separate from
original RM84 and WS116 scientific raw/. File inventories precede receipt creation
and exclude receipt bytes; root captures final disk/hash externally. No actual
qualification scratch/process exists yet. Earlier drafts, reviews and accounting
remain; actual model/token/cost metering is unknown.

## Method5 proposed commands and grant binding (NOT EXECUTED)

Only after fresh METHOD REVIEW5 and coordinator/root exact release, propose:

```sh
docker exec --user 1000:1000 -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e PYTHONDONTWRITEBYTECODE=1 -w /workspace/work/issue-116 simrecon-campaign-ubuntu .venv/bin/python docs/reports/reconstruction-working-set/method_qualification.py --case Q0-context --grant docs/reports/reconstruction-working-set/qualification/grants/Q0-method5-released.json --attempt-id q0-method5-a1
```

A later Q1 command would use `--case Q1-normal`, a separate
`Q1-method5-released.json` and `--attempt-id q1-method5-a1`, bound to the actual
successful source-matched method5 Q0 receipt/hash, never the old v1 receipt.
Root must inspect/freeze the final code/commands/grants/bounds and fresh actual
proof; these proposed names grant nothing. `grants/method5-template.json` remains
unapproved with pending resource/ownership/proof. Its nonce is explicit and the
inventory pins the integrated bootstrap digest. All old template/released grant
bytes remain unchanged; old source-freeze is historical and intentionally does
not match the changed method5 helpers. A new external source manifest binds the
reviewed candidate without self-hashing the record.

For actual reconstruction (still ungranted), the existing per-attempt admission
fields additionally require `launch_nonce`, `startup_timeout_seconds:5.0` and
`startup_pipe_bytes:1024`, matching manifest. Spec/receipt bind route/body digest/
target argv/nonce and observed FD/PID/session facts. Target science is unchanged.
Native terminal field is `kernel_reported_direct_child_high_water_bytes` with
raw Linux KiB retained. It is kernel-reported direct-child usage through final
exit; inherited/pre-exec/exec-transition high-water retention is unresolved.
Same PID does not guarantee every bootstrap/startup peak survives exec; no
subtraction/aggregate/benefit claim. Target self snapshots remain separate.
