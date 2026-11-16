# WS116 independent source-only delta static method review 2

Verdict: request a narrow further F2 source correction before scheduled runtime qualification. F1's live-child RSS-loss correction is statically satisfactory. C1 now has an explicit, scope-limited cancellation/recovery disposition. F2 rejects the original null-snapshot/omitted-field counterexample but still permits structurally incomplete or unusable evidence to receive complete-observation status.

This is source diagnosis only. It is not experiment admission, scientific report acceptance, product D review, verification readiness, gate acceptance or execution authority. No implementation or counterexample was executed.

## Exact identities and scope

Observed worktree `/workspace/work/issue-116`, HEAD `701b56d349adaf5e719510a158b51402876f9c30`, with uncommitted report-method changes. Review packet SHA256 independently matched `7fb98d36ec7be6591579613dca6aa6fc4d7472ca770f222c99c270665b13f9df`. Prior review SHA256 independently matched `9a4452afddd4e4d53e47f2b4990f0a268bd3f7c3216e60ae54a739ed99b4b81c`.

All six working-source hashes matched the packet, matched the corrected snapshot at `/workspace/work/campaign/evidence/116/source-method-v2-corrected-review2/`, and matched on the final pre-report reread:

| File under `docs/reports/reconstruction-working-set/` | SHA256 |
| --- | --- |
| README.md | `42eaf8fc9267aa58463e5958316460feeace0ff0fa4f1fb748eb1a4171b6ff5c` |
| manifest.json | `af618fc22fe231f7ea881446e717fbca5804d1c0ac14c10770664efda709d629` |
| observer.py | `678e37cde5e8be514277c188dcd1332bb2c64a706a836e8a9dab652461741c3a` |
| workload_child.py | `349f5d687f4fa94363a041d72b86c89199db28018b23c6c0802946a837747531` |
| run_attempt.py | `1d8a10f8a6a8fc7571b15a1ea6d1e50aa6df9e2ff665629ef315c8845d885020` |
| method-review-input.md | `139922ffb145130351847e4b34e69e3a1d8a34ca842dc90324527998b30a421a` |

Read AGENTS.md, docs/PROJECT.md, `.agents/skills/review-work/SKILL.md`, method-review-input.md including its correction mapping, method-refinement-packet.md, the prior review and permitted prior source snapshot. Compared the changed runner/observer/README/manifest with that snapshot; independently hashed all six prior snapshot files against the identities in review 1. The child is byte-identical. Read W01/W03/W05/W06/W09 and related observer/stopping portions of the contract, the frozen fingerprint/retention/array-identity helpers and the workflow stage call sites needed to challenge the new stage validator. No lessons, private branch ancestry, other issue worktree, author conversation or task/launch contents were inspected.

Supporting identities remain identical to those reported in review 1:

| Supporting source | SHA256 |
| --- | --- |
| docs/contracts/reconstruction-working-set-v1.md | `be7bc7ce0d8cb94a7e9ac168c834290293bbcb346456b17a5e44a56133829202` |
| tests/reconstruction_summary_fixture.py | `271335a5065791a986de239cdf89e4d15eb0f2e5df80943d6cb084167516d20f` |
| tests/reconstruction_memory_benchmark.py | `929106da36b47bcd03ed785d1a7f6b941d04299403b6c0ffe7df9846f3809b8f` |
| src/simrecon/workflow/reconstruct.py | `50a4ce199f0cceca6ba9147a1ee218441b1b5588c03beabecef95828802e28fa` |
| report-directory method-refinement-packet.md | `51f2169b7f6977e77c3616f6d5db1a7083f62aa1329ee2fd71a4a9d25ff504e7` |

The new packet reports accepted/published #115 PR122 at `ace06c861b974b6251a092567c253ae4eb0f56c8`, tree `2247d3909f43bc4764beb5c748caa917aaa1d707`, with full Ubuntu gate and fresh D acceptance; CI122 was in progress. Those are coordinator-supplied context, not independently checked here. This worktree has not integrated that parent. Older gate-in-progress wording in the method documents is historical and supplies no release.

## F1 disposition: statically corrected

`observer.py:101–118` initializes required RSS to null, checks native field shape, unit and nonnegative integer conversion, and emits readability/error diagnostics rather than inventing a zero. An unreadable status has `process_status_readable=false`; a readable status lacking RSS retains null with no successful measurement; an unusable RSS field retains null plus a field error. The actual sample is serialized/flushed before the second exact-PID terminal check (`run_attempt.py:360–367`). Only a still-live child reaches the stop decision. Missing, noninteger, boolean or negative RSS selects `required_process_RSS_observation_lost` (`:374–375`), unless an earlier cgroup/deadline stop already applies. Every such live path still stops; integer zero stays distinct and proceeds to the ordinary thresholds.

The existing TERM, grace, KILL and reap-deadline logic is preserved. The terminal race does not fabricate a monitor stop, and stop-reason precedence cannot convert a monitor stop into nominal success. Raw samples, diagnostics, last sample and eventual terminal status remain evidence. The diagnostics do not retain the entire original `/proc/status` text; this review claims preservation of the emitted null/readability/error sample, not a full raw status-file archive. No new F1 source defect found. Actual missing/unusable/zero RSS and exit-race behavior remain unexercised.

## F2 disposition: original counterexample closed; concrete completeness defects remain

The explicit validator (`run_attempt.py:157–260`) now rejects null snapshots and omitted required identity/timing/environment/retention fields. It checks exact material maps, integer/native units and byte conversions, call ordering/derived duration, cumulative high-water ordering, input/output identity names and branch shape/labels. The original review-1 null-snapshot record now fails at `:193`; omitting required hashes fails at `:209`. This is a substantial correction, but the following independent source-derived counterexamples remain. Each starts with an otherwise complete matching finite record, leaving PID/spec/material maps, exit zero, terminal wait4 and parent applicability checks intact. None was constructed or run.

### F2a — A truncated profile stream passes completeness

For any admitted profiled condition, replace `stages` with:

```json
[{"stage":"declaration","edge":"enter","monotonic_ns":0,"ru_maxrss_native_KiB":0,"time_index":null}]
```

`:255` requires only a nonempty list for profiling; `:257–260` accepts this single event. There is no exit pairing, required-stage presence, reconstruction time-index coverage, event order or timestamp alignment check. Thus the record omits preparation, estimation, all per-time reconstruction and result observations, yet passes the new complete-record validator. Even the zero timestamp is accepted here, although snapshot timestamps must be positive.

This is known protocol completeness, not a scientific tolerance question: the child installs the wrapper around the workflow (`workload_child.py:49–61`), and the permitted workflow source contains declaration, preparation, estimation, one reconstruction stage per time and result, with optional layout (`src/simrecon/workflow/reconstruct.py:211,312,336,359,384,426`). The wrapper emits enter/exit in `observer.py:153–163`. A single unmatched event cannot represent that declared complete stream.

### F2b — Required resource values may be unusable text

Replace one visible ancestor's `memory.current` with `"unknown"`. `run_attempt.py:242` checks only nonempty text for both current and limit, so the required numeric current observation is accepted. The same check accepts an unusable limit such as `"unknown"`. This is distinct from explicitly nullable optional peak/events/swap observations at `:243–244`, and distinct from the legitimate `"max"` limit spelling. Snapshot scopes are similarly only nonempty text (`:199`): replacing every named snapshot's scope with `"unknown"` passes despite losing the protocol's known temporal scope labels.

### F2c — The array-identity dtype check accepts invalid encodings

Replace `output_hashes.image[2]` with `"<f1"`. The regular expression at `:179` accepts it, and the identity check at `:183` has no further dtype check. It is not a usable NumPy floating dtype representation emitted by this child's identity helper. The same expression also permits invalid kind/size combinations such as `|b16`. These are unusable identity metadata, not a request to qualify any numerical result or enforce a new precision policy.

All three routes return the finite outcome at `:279` and, with the unchanged normal conditions above, reach `complete_child_observed_pending_scientific_qualification` at `:422` and return zero at `:456`. That status still makes no scientific claim, but it does incorrectly claim complete observation.

Requested correction: tighten the existing small, explicit child-v2 checks for usable native resource values and the known snapshot scopes, legal supported dtype encodings, and a complete/ordered/paired declared stage stream with applicable per-time indices and time bounds. Retain intentional unknown/nullable observations where the protocol declares them, and keep branch/scientific-output qualification separate. No generic schema framework, numerical tolerance, product edit or new experiment is needed to diagnose these source defects. A fresh delta review should challenge these specific bypasses and normal unprofiled/profiled records after correction.

## C1 disposition and operational limits

The default Python SIGINT-handler requirement is explicit (`run_attempt.py:309–310`). During ordinary owned-child observation, one SIGINT raises KeyboardInterrupt, produces `observer_cancelled` (`:423–426`) and enters the existing bounded KILL/reap cleanup (`:427–432`). No custom signal handler or unrelated process authority is introduced.

`spawn-intent.json` is written before spawn; `owned-child.json` follows PID ownership and precedes monitoring (`:339–353`). The marker facts include boot/start/PID/PPID/PGID/session/executable where readable, argv and spec/grant hashes. The `/proc/stat` indexing in `observer.py:129–131` matches fields 4, 5, 6 and 22 after removing the parenthesized comm field. Read failures remain unknown. An already-exited child can therefore leave incomplete live identity without making that marker a signal authorization.

README.md:258–303 now binds concrete coordinator recovery: verify the launched observer; send one SIGINT; inspect terminal evidence and resource release; freeze the numerical window after TERM/abrupt death/interruption; correlate current identity rather than trusting a stale PID; act only on verified owned sessions; record lost wait4 evidence as incomplete; block another trial while ownership/resources remain unresolved. The procedure explicitly covers intent-only, missing, partial and malformed markers. A signal/spawn race before `owner = WaitOwner(pid)` can still leave no in-memory owner, and direct TERM still bypasses finally; those are disclosed recovery paths rather than solved Python-handler guarantees. Marker writes are ordinary files, not an atomic/fsync crash-proof journal, and host death has no proven durable-recovery guarantee here.

I find the C1 operational disposition sufficient for the packet's source-only purpose, subject to later qualification. It is neither an engineered cross-attempt lock nor demonstrated recovery. No statement that observer death proves child death or preserves terminal rusage is justified. Repeated SIGINT and interruption of cleanup/receipt work remain explicitly unsupported/gap paths requiring recovery.

## Retained evidence and affected normal paths

- The child, canonical hashing algorithms and frozen helpers are unchanged. Observer changes add sampling/recovery facts and correct scratch prose; the stage wrapper and hash implementations are unchanged. Independent rereading supports retaining review 1's static assessment of single-case/one-result lifetime, no reference reconstruction, C-order/little-endian/empty-array intent, bounded conversion/finite chunks and scalar-only stage closure. This retains no runtime qualification. Conversion buffer and tobytes chunk may coexist; 1 MiB is a per-buffer/chunk parameter, not total scratch. Frozen public-value hashing retains its separate 65,536-element conversion protocol and costs.
- WaitOwner remains the sole exact-PID workload wait4 owner. Cached terminal data avoids reaping twice; nonterminal notifications are not terminal usage; ownership loss prevents subsequent group signaling through that owner. Git subprocess waits are provenance work. There is no nominal-success path with missing `owner.terminal`. Bounded stop/exception loops leave explicit cleanup gaps rather than successful returns; they do not hard-bound filesystem operations or scheduler delay.
- Terminal wait4 is direct-child maximum-process RSS through exit including serialization/teardown, excluding the parent observer and concurrent process-tree aggregation. Named child snapshots stop at their query; post-observation precedes JSON. Inherited/pre-exec accounting is unresolved and never subtracted. No numerical grandchildren are commissioned.
- Normal child fields match the validator's expected tuple-to-JSON-list forms, timing formula, snapshot order, environment/resource structures, retention keys and stage scalar names. I found no separate source regression preventing an otherwise valid ordinary record, but no such record has been executed. The F2 findings concern incomplete evidence escaping those checks.
- Admission, spawn/observation failure, monitor stop, signal, nonfinite, child exception, missing/malformed/oversized output and identity-change branches remain distinct. Raw stdout survives parse refusal. A final material change or postflight failure downgrades nominal success. Before/after hashes are applicability observations, not immutable input snapshots, protection against transient mutation or a security boundary.
- Manifest changes are annotations/protocol revision only; 20 initial conditions, three repeats and separate profile controls remain. Receipt inventory precedes receipt creation and excludes itself; external final receipt hash and logical/allocated directory accounting remain required. No circular self-hash claim is introduced.

The unchanged static conclusions remain limited by this review's scope and the new F2 finding. Later integrated-parent/source identity refresh, scheduled runtime qualification, observer perturbation/scientific matching, final Ubuntu full verification and fresh scientific/readiness review remain separate. None is inferred from source review or a future complete-child status.

## Actual commands, exposure, accounting and scratch/process facts

Only read-only shell/source/hash/diff inspection ran: `cat`, `sed`, `nl`, `rg`, `wc`, `sha256sum`, `diff -u`, `diff -q`, `git status --short` and `git rev-parse HEAD`, followed by the one authorized report write. All inspection calls completed. Diffs that found differences returned their normal status 1; the child equality check and final hash reads returned 0. Initial combined documentation/source outputs were truncated; the relevant documents/source were reread in smaller ranges. No failed runtime capability probe or hidden execution is claimed.

No Python, imports, probes, lint/types/tests, install, new-tool execution, numerical/benchmark execution, rebase, commit, push, publication, merge or release occurred. The source examples above are reasoning-only counterexamples. This is one fresh independent delta static review, following the preserved review 1; all prior rounds/corrections/charges remain intact. No delegation or inherited author conversation occurred. Requested model/effort is Sol/high; actual served attribution, tokens, elapsed metering and monetary cost are unknown unless separately exposed by the host. Human numeric cap is not set.

Status output exposed filenames of other modified/untracked report/task/launch files in the same worktree; their contents were not read or edited. Shared filesystem/parent permissions and named prompt restrictions prove no engineered isolation. Optional per-role memory/sandbox controls are unavailable. The only created artifact is this durable report at `/workspace/work/campaign/evidence/116/static-method-review-2.md`. No scratch file, fixture, numerical process, daemon or persistent owned process was created. All inspection shell processes completed. No cleanup or deletion was performed.
