# Full256 searched r1: source worksheet

**SOURCE ONLY; no searched admission or helper.** Exact proposed entry is
`simrecon.reconstruct_workflow`, `(T,D,Z,Y,X)=(1,3,8,256,256)`, native3D,
P5/O3/lateral2/axial1, analytic fixture with **search_carriers:true**, uniform
phases, no off/drift/layout, repetition1, unprofiled. The fixture's detector
is float32; bulk q/overlap/filter storage is complex128 and images float64.
All35 named EA source/fixture/tooling file hashes match the frozen material
basis; HEAD/tree values are recorded source identity, not a new git/status
or runtime check. No active supplied R2/R3 data or outcome was read.

## Actual searched branch and retained data

Fixture source sets linespacing4um, searchtrue, use_time0_carrierstrue. Full
workflow derives initial declaration/linkage before preparation. Acquisition
phase linkage is not recalculated using a later fitted carrier. At T1/time0,
all three directions must use `searched`; no `time0-reused` or `known` branch
is acceptable. Defaults are amplitude_floorsNone, fit_all_phasestrue and
omit_kz0false. Filtering consumes the searched carrier/modulation result.

The searched3D O3 path builds **three** overlaps per direction:

1. Coarse `(0,2)` at declared initial carrier. A spatial product is summed
   over Z, transformed by fft2, and its power is scanned with strict first
   maximum ordering. Wrapped-neighbor fits and the source's ordered alias
   adjustments produce coarse carrier.
2. Refinement `(0,2)` at coarse carrier. Angle steps0.001rad then magnitude
   steps `0.1/(max(Y,X)*dxy)` run strict-improvement walks followed by three-point
   fits and final evaluation. These trials reuse ONE frozen refinement
   overlap; the `remake_overlaps` flag does not allocate an overlap each trial.
3. Later-order `(0,1)` at fitted carrier for the remaining positive order.

Thus a successful T1/D3 full searched path retains **nine overlap records**.
Full build_order_overlap appends each record with owned carrier copy and
Fourier/spatial/write-mask arrays to estimator.overlaps; the returned full
parameters retain the entire tuple. `del other` does not free the retained
record. Supplied mode instead builds two known overlaps per direction: six.
Search trial/evaluation counts, scalar/container extent and convergence result
remain UNKNOWN; zero carrier/energy, singularity, nonfinite and stagnant or
overflowing coordinates may fail. This finite procedure promises no global
optimum or runtime bound.

Full record_event makes independent read-only array copies. Each direction's
coarse event retains complex `[Y,X]` correlation, real `[Y,X]` power,
float64 x/y neighbor triples, before/after alias pairs and carrier pair.
Every evaluation event additionally retains a copied float64 carrier pair,
plus scalar/tuple SX/SY/cross/forward/reverse/combined/correlation/objective
and polar/stage/index/remake details. Bracket/parabola and final adjustments
retain their scalar details. All remain in parameters.trace and the full
public result through observations. The number of these search records is
not a known constant. Compact summary omits coarse correlation arrays and
uses overlap descriptors; its retention cannot be copied onto full mode.

Coarse local product/correlation/power and neighbor/alias arrays remain live
through event capture while copies are created. Coarse originals die when
that call returns; captured copies persist. Refinement fit temporaries include
x/y coordinates, realYX phase, lower spatial view, ramped complexZYX higher,
exponential/multiply/conjugate/abs-square/reduction arrays and unknown FFT/native
workspace. Local phase/higher live through capture until fit returns; those
whole temporaries are not stored in evaluation events. The refinement build
also remains live while the later-order build is made.

## Units, representation and lifetime boundaries

| Named storage | Elements | Dtype | Existing logical bytes |
| --- | ---: | --- | ---: |
| Caller raw `[1,3,5,8,256,256]` | 7,864,320 | float32 | 31,457,280 |
| Each prepared/private full q `[1,3,5,8,256,129]` | 3,962,880 | complex128 | 63,406,080 |
| One overlap Fourier or spatial `[2,8,256,256]` | 1,048,576 | complex128 | 16,777,216 |
| One overlap write mask, same shape | 1,048,576 | bool | 1,048,576 |
| Each stage/final image `[1,8,512,512]` | 2,097,152 | float64 | 16,777,216 |
| One padded/inverse output volume | 2,097,152 | complex128 | 33,554,432 |

The207,618,048B supplied-six overlap aggregate spans18 backings and is **not
one allocation or the searched total**. The frozen searched table instead
lists311,427,072B for nine overlap records/27 backings. That is also an
aggregate, despite the historical `maximum_listed_allocation_bytes` label.
The largest named single backing remains63,406,080B; no bound on all dynamic
native/container/trace allocations follows. Coarse named trace payload is
symbolically `D*(16YX+8YX+(3+3+2+2+2)*8)` bytes, excluding headers/scalars;
no calculation program or total was produced.

Source integer geometry gives largest listed7,864,320 elements below signed32
limit2,147,483,647, native V524,288/H264,192 and output V2,097,152. Actual shape/
dtype/itemsize/stride/native and signed extent guards remain required. Fitting
64-bit nativeintp is not a RAM-fit proof. Optical support masks enclose lateral
radius0.5/u<=4; clipped axial magnitude3, native/tabledkz0.125, K16 yields
all four vertices<=95<1024 per order with one negative-z wrap. This source
enclosure applies after shifted searched-candidate support masks; it is not
a numerical query trace or proof that a fitted candidate succeeds.

Caller inputs stay through observation; workflow raw snapshot dies after
preparation. Full prepared all-T q, preparation diagnostics/phase snapshots
and event copies persist into the full result. Estimation snapshots q once;
that private estimator input dies on return, while all overlaps/search trace
remain. Per-time selection slices alias prepared arrays. Full filtering has
stable q copy, destination and helper-return q together during assignment;
native `plus` scratch old/new Python locals may overlap. Stable original is
explicitly deleted before assembly. Padded/inverse may coexist in FFT, then
padding is explicitly deleted; inverse is deleted per order, but phase local
can persist across orders/directions. Known image/filteredq are marked read-only
in place, final concatenation allocates a separate image even T1, and coordinates
are independently copied. Prepared q/overlaps and both images remain in full
result. Arithmetic last use alone does not free Python locals.

The table's searched filtering606,011,088B and concatenation504,364,752B, and
the other JSON-listed subsets, are copied partial logical inventories. Do
not sum them or call them RSS/peaks/strict bounds. Search correlation captures,
dynamic evaluation/container/scalar/header bytes, finite-check temporaries,
allocator fragmentation/cache and FFT/BLAS/native workspaces remain unclosed.

## Observer and admission boundary

Profilefalse selects nullcontext: child stages[] does not remove product
search diagnostics. Caller/result stay alive through bounded finite/hash/
retention/context observations. Three self snapshots are cumulative and end
before JSON/teardown; complete terminal wait4 is separate kernel direct-child
usage through exit, with inherited/pre-exec/exec-transition retention UNKNOWN.
No subtraction, aggregate, causal benefit or supplied-mode native extrapolation
is made. Full/summary same-repetition checks are input/common/branches only;
their public retained graphs differ. Closed summary and future full physical/
cache/event contexts are not identical controls.

Original ROOT selection0f795 establishes completed summary size256 only. Its
next_proposed_stage says SUPPLIED, so it supplies no searched-stage authority.
Before any prospective searched preparer, ROOT must supply a new explicit
searched-stage decision, actual completed supplied-full triple eligibility,
closed full-supplied stage/owner/controller/window evidence and primary plus
independent analysis JSON references. ALL remain UNKNOWN/null here. Known
a4c2/0aff/79a prior closures are immutable; the additional supplied-full closure
slot is null. Source/static same-rep searched summary control references can
be bound, but their raw data is not reread now.

Unchanged proposal: P4GiB/native2/stop8/reserve4/ancestor15/host>12GiB,
deadline3600s/horizon3720s/disk2965897216B. It is not a measured fit or timing
prediction. Future actual source/case/limits/disk/schedule/owner/resource/event/
swap/window authority and per-row original-proof/end guards remain mandatory;
all dynamic packet fields are disabled/null. No helper, new framework, method,
private baseline, code execution/import/AST/lint/test/probe/calculator or live
data read was commissioned. Prep29/exec9,total38; costs/tokens/attribution
UNKNOWN. SOURCE READY, then HOLD for scientific-source inspection.

Exact source paths/line references, all35 hashes, extra searched diagnostics,
literal table fields and unknowns are in the companion JSON.
