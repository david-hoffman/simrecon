# EA full256 supplied r1 — primary-source check

Source-only check of full `reconstruct_workflow`, `(T,D,Z,Y,X)=(1,3,8,256,256)`, supplied carriers, repetition1, profilefalse. EA35 hashes for all11 read primary files match. No full run, product import, probe or current resource observation occurred.

| Storage | Elements | Dtype | Logical bytes |
| --- | ---: | --- | ---: |
| Caller detector `[1,3,5,8,256,256]` | 7,864,320 | float32 | 31,457,280 |
| Private workflow detector snapshot (same shape) | 7,864,320 | float32 | 31,457,280 |
| Caller transfer `[3,64,16]`; separate workflow transfer copy each | 3,072 | complex128 | 49,152 each |
| Prepared q `[1,3,5,8,256,129]`; each full q snapshot/filter buffer | 3,962,880 | complex128 | 63,406,080 each |
| Each overlap Fourier/spatial `[2,8,256,256]` | 1,048,576 | complex128 | 16,777,216 each |
| Each overlap write mask (same shape) | 1,048,576 | bool | 1,048,576 |
| Stage/final image `[1,8,512,512]` each | 2,097,152 | float64 | 16,777,216 each |
| Each padded/inverse output volume | 2,097,152 | complex128 | 33,554,432 each |

**Full lifetimes.** The child retains caller inputs and the result through observation. Workflow raw snapshot dies after preparation; correction promotes one plane at a time to float64, not the whole raw volume. Full bands keep q/noise, preparation diagnostics and phase-design captures. Private `_finish_owned` finalizers transfer buffers, whereas event captures copy arrays. Supplied estimation builds **six**, not nine, overlap records (three directions × orders1/2): Fourier+spatial+masks total207,618,048B across18 backings. Its private q snapshot dies on return; overlaps/traces and preparedq remain. Each per-time band slice aliases prepared storage.

Full filtering keeps a stable q copy, separate destination and the helper-return q copy during assignment; forT1 each is63,406,080B, in addition to preparedq and retained overlaps. The stable original is deleted before assembly. Padded/inverse FFT volumes may coexist, then padding is deleted; carrier phase/product temporaries remain relevant. `_readonly` only marks known-stage image/filteredq readonly. Full result retains bands, parameters/overlaps and known reconstructions; concatenation allocates a separate final image evenT1. Coordinate copies are small separate storage; no alias is counted as another fullq.

**Representation/stencils.** Largest listed element count7,864,320 fits signed32. Largest named single backing63,406,080B fits supported64-bit nativeintp. Existing table207,618,048B field is a conservative retained-overlap **aggregate**, not one allocation; preserve the original table but label it correctly. Each actual dimension/itemsize/byte product still passes runtime source guards. Native volume524,288; half volume264,192; output volume2,097,152 elements. Source support-before-sample checks enclose lateral radius0.5, `u<=4`; actual optics/axial clipping gives`|z|<=3`, native/tabledkz0.125, K16. All four signed flat vertices are bounded by95<1024 perorder, including the single negative-axis wrap. This is source enclosure, not a query trace or numerical adequacy guarantee.

**Inventory limits.** Existing filtering subset502,202,064B and concatenation subset400,555,728B are partial logical co-live inventories. Do not sum them or call them RSS, peaks, upper bounds or RAM feasibility. They omit/cannot close all transfer snapshots, trace/container/scalar bytes, finite-check temporaries, native FFT/BLAS workspace/cache, allocator metadata/fragmentation and scheduling/sampling overshoot. Full named preparation diagnostics+phase trace are1,064,656B; off/drift large capture payload iszero for this exactcase. Native/backend and complete measured retention remain unknown until actual full observation.

The source-fixed proposal remains P4GiB/native2GiB/stop8GiB/reserve4GiB/ancestor15GiB/hostminimum12GiB,3600sdeadline/3720shorizon. These are operational proposals, not measured bounds or time predictions. Summary RSS does not qualify full mode. ROOT must independently admit fresh source/case/scheduler/domain/current/headroom/rlimits/disk/events/swap/window/authority; this check grants no runtime or16GiB promise.

Exact source hashes, line references, source table and unit/lifetime fields are in `full-supplied-r1-source-check.json`; no original source, proposal or frozen packet was changed.
