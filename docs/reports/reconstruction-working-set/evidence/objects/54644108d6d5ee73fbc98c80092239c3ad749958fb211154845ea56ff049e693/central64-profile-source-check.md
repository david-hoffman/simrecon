# Central64 profiles: source meaning and disabled first row

**SOURCE ONLY; no profile observation, helper or runtime admission.** Stage
`central64-profiles` has exactly summary searched profile repetitions1-3,
then full searched profile repetitions1-3. Only
`ws116-gp-c64-summary-searched-r1-p` is proposed first. Crucially,
`selected_largest_size` stays **NULL**: frozen8190 explicitly requires None
for this central-only stage. No largest256 next-stage assertion is copied.

The analytic fixture is native3D `[T,D,Z,Y,X]=[1,3,8,64,64]`, P5/O3,
lateral2/axial1, searchtrue/use_time0true, no off/drift/layout. T1/time0 must
produce searched3, not known or time0-reused. Caller raw is float32, real
math/image float64 and bulk q/overlap/filter complex128. Inputs, numerical
algorithms, tolerances and worker fixture do not change with profiletrue.

## What the hook actually observes and retains

Child imports simrecon (which imports workflow.reconstruct), generates the
case and computes input hashes/retention in both profile and unprofiled runs.
Profiletrue creates stage_observer; unprofiled uses nullcontext. On entry the
hook performs importlib module lookup, saves the module's imported
workflow_stage name and replaces that name with a generator context manager.
It restores the original in finally before post-call output observation.
Other modules' independently imported contexts are not patched. In particular,
transfer resolution outside these source contexts is inside the workflow
call but has no independent stage event.

Each successful native T1 call has the source mask declaration, preparation,
estimation, reconstruction(time0), result, each enter then exit. The qualified
runner owns the exact paired/ordered mask, legal fields/time indices, timestamps
inside the call and cumulative high-water ordering. Generic validator allows
optional layout when present; this native fixture does not enter layout.
No actual stage timestamp, RSS or allocation value is authored here.

The hook records `stage`, `time_index`, `edge`, Linux monotonic_ns and target
resource.getrusage(RUSAGE_SELF).ru_maxrss in native Linux KiB. Enter is recorded
before original(stage,kwargs) is entered; exit is recorded in finally after
it exits. Timestamp expression runs before the usage query/dictionary append.
High-water is cumulative, not current RSS or a private stage allocation;
stage differences cannot isolate contributor bytes. Intervals include hook
work, and uninstrumented gaps remain, so they are not pure math timing or an
additive decomposition.

Events retain scalar dictionaries; actual stage arguments are strings and a
scalar time index. The hook neither inspects numerical caller frames nor
stores ndarrays. It still creates contextmanager/generator frames, closure
cells, kwargs, dictionaries and list-growth allocations while contexts are
active. The original workflow_stage, present in both modes, DOES inspect
traceback frames/f_locals t/d and causes when translating failures; exception
chains and extra profile frames can temporarily retain numerical locals.
Thus this is not a frame-free/allocation-free experiment. Ordinary exit finally
can append a failure-side exit, but child `stages=events` assignment occurs
only after a successful call. Failed calls bypass it and emit workflow_exception/
exit1; no complete or synthetic partial mask is assumed.

Caller case and result are intentionally retained through post-call work in
both modes. public_value_sha256 recursion/memoryviews/iterators temporarily
reference arrays; retained_payload walks dataclass fields, caches, dicts,
slots and base arrays, with transient item/child/base references. Its returned
metadata stores IDs/byte counts/shapes/dtypes/paths, not arrays. That does not
erase stack/buffer/metadata cost while traversing an already-retained graph.
Identity/finite chunks and65536-element public-hash conversion are separately
bounded; conversion and tobytes/finite temporaries can coexist. No total process
scratch ceiling follows. These observations are not unique to profiling.

There is no per-stage file write/flush: the in-memory event list survives to
the final child JSON and teardown. Parent sample logging/flush at the declared
interval occurs in both modes. Profile JSON adds potential serialization,
pipe/disk/collection/cache effects. Neither source shape nor scalar events
establish a known profile cost or isolated causal observer overhead.

## Measurement boundaries and comparisons

Both modes take pre_call after input hashes/retention (and profile setup),
call_end after the call timestamp, and post_observation after context/hash/
retention/finite/identity work but before JSON/teardown. All are cumulative
self high-water, with fault/I/O/CPU counters. Call time contains hook events
but excludes setup and later traversals/JSON. Terminal sole wait4 is separate
kernel-reported direct-child usage through final exit; inherited/pre-exec/exec
retention remains unknown. Parent self snapshots and sampled VmRSS are other
scopes. No subtraction, stage-allocation claim or aggregate is made.

Six small CLOSED initial60 boundary/config controls are pinned, without raw/
sample/proof rereads. Pair each profile with the SAME mode/search/repetition
unprofiled control. Existing8190 requires input/common/branches **and public
result fingerprint** equality for profile versus same-mode control. Hook
events are child metadata outside the product result graph. Summary/full
graphs differ: cross-mode comparisons use only input/common/branches, retaining
both public hashes separately. Keep profile and unprofiled observations in
separate groups, never pooled. Software/workload matching does not establish
identical physical/cache/event context (initial60 event0 is historical), and
any timing/RSS contrast remains observational.

## Numerical lifetimes and source representation

Frozen integer/byte literals are copied without a calculator:

| Named quantity | Elements | Existing bytes |
| --- | ---: | ---: |
| Caller float32 raw `[1,3,5,8,64,64]` | 491,520 | 1,966,080 |
| Prepared complex128 q `[1,3,5,8,64,33]` | 253,440 | 4,055,040 |
| Native volume / half volume | 32,768 / 16,896 | — |
| Output float64 image `[1,8,128,128]` | 131,072 | 1,048,576 |
| Padded or inverse complex output volume | 131,072 | 2,097,152 |
| Full nine-overlap aggregate,27backings | — | 19,464,192 |

The full overlap table field is an aggregate, not one allocation. Listed
counts fit signed32 and actual dtype/itemsize/shape/stride/native-intp guards;
dynamic trace/container counts and backend allocations remain runtime unknowns.
Support-before-sampling masks enclose radius0.5/u<=4, clipped |z|<=3,
native/tabledkz0.125, K16 and all four vertices<=95<1024 with one negative-z
wrap. This is source enclosure, not a query/numerical/RSS/RAM-fit proof.

Both modes prepare all-T q and retain it through the entire reconstruction
loop. Summary compact capture borrows private read-only q, retains nine overlap
descriptors/small scalar tuples and omits stored coarse correlation arrays;
actual search math still allocates coarse/refinement/fit temporaries. A frozen
refinement working spatial pair can coexist with later-order work. Compact
known intermediates are dropped per time after projection, but images/coordinates
remain; bands=None only AFTER the whole loop, then separate final concatenation
and images.clear. A slice/view is not another q allocation.

Full capture snapshots q for estimation and retains nine Fourier/spatial/mask
records plus coarse correlation/power/vector and dynamic trial captures through
result observation. Full filtering stable copy/destination/helper q can coexist;
Python plus old/new scratch locals may overlap. original is explicitly deleted
before assembly. Padded/inverse can coexist, then padding is deleted; inverse
is deleted per order but phase local can persist. Full result retains bands,
overlaps/trace, filtered q, stage image and separate final image/coordinates.
The scalar profile hook does not close these transient/native/allocator/
header/container costs, nor make arithmetic last use free Python locals.

## Exact caps and pending admission

| Profile condition | P / native allowance | Process stop / reserve | HOST minimum | Ancestor stop |
| --- | --- | --- | --- | --- |
| central64 summary searched | 536870912 / 268435456B | 1073741824 / 1073741824B | **2147483648B (2GiB)** | **8589934592B (8GiB)** |
| central64 full searched | 805306368 / 402653184B | 1610612736 / 1073741824B | **2684354560B (2.5GiB)** | **8589934592B (8GiB)** |

Only per-row deadline doubles480->960s. Horizon becomes960+120=1080s;
disk uses exact8190 `max(67108864, deadline_seconds*100*8192+16777216)`, with
existing frozen profile literal803209216B. Other caps, fixture, tolerances,
startup/grace/reap/record/sample settings are unchanged. These are operating
proposals, not measured peaks/times or feasibility promises. Named ROOT
reconciliation0e9ca901 corrects old compacted prose labels only;0058/8190/
configs/executed guards always had summary HOST2GiB/full2.5GiB/ancestor8GiB.
There was no executed failure or cap change from that correction.

Actual searched-full triple/whole-stage closure,940primary/independent8triplets/
ROOT acceptance and a NEW ROOT central-profile-stage decision remain UNKNOWN.
Known initial/192/256summary/fullsupplied41a closures can be referenced; the
additional searched-full whole-stage closure slot is NULL. New-stage owners,
metadata/maps/events/swap/window/authority/suspension remain NULL/disabled,
prefix[] is only the proposed new-stage declaration, selected None. Future
batch under central64-profiles-first-readiness is neither created nor checked
now. ROOTAUTHORITY evidence must never be an ACK. No helper/preflight/grant/
intent/program/profile is authored or executed. Source/runtime unvalidated;
scientific review/final acceptance pending. Prep32/exec9,total41; original1
launch/all prior bytes/errors/attempts/unknown charges preserved. HOLD.
