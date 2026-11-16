# Source-derived liveness, provisional baseline

This is calculation and source interpretation, not measured memory or a ranking.
Baseline: public main `b344e41a8b52de76d7cbbf8450319893904c3b8f`.
Accepted #112 → #115 must be reread before freezing the experiment. Shapes and
bytes below describe current actual float64/complex128 operations, independent of
float32 detector input. Hypothetical half-sized float32/complex64 payloads remain
predictions; downcasting a returned image proves no end-to-end precision path.

Let `V=Z*Y*X`, `H=Z*Y*(X//2+1)`, `Q=2*O-1`, `Vo=Zo*Yo*Xo`.
For primary rows `P=5,O=3,Q=5,Zo=Z,Yo=2Y,Xo=2X`, hence `Vo=4V`.
Define `Bq=16*T*D*Q*H`, `Bqt=Bq/T`, `I=8*Vo` per-time image.
A view of one time is part of the original Bq backing, not another Bqt backing.
Count root allocations once. Payload excludes metadata, allocator and FFT workspace.

| Family and source | Owned payload / alias | Lifetime and overlapping families |
| --- | --- | --- |
| Caller specimen, fixture `workload` | `4*T*D*P*V` float32 plus declared transfers/maps/off/header arrays | Kept by the child case through result hashing/traversal. Generator indices, object and illumination temporaries affect whole-process high-water before call; they are absent from call liveness after generator returns. |
| Workflow snapshots, `workflow/reconstruct.py:276–296` | Independent same-dtype raw/off copies; metadata/maps/settings copies separately | Created after declaration, live through preparation, explicit `del` after preparation at line352. Caller allocations coexist. Full preparation may publish additional independent result backings. |
| CE06 preparation, `acquisition/modes.py:_prepare_acquisition_bands` | `Bq`; another `Bq` off_q if Noff>0 (independent of Noff), noise `8*T*D*O`, matrices `8*T*D*Z*Q*P`, phase angles `8*T*D*Z*P`, sums/gains and optional off pair `8*T*D*P*Z` each, displacement/maps/metadata | q/off_q allocated before all t/d/z loops. Compact keeps q/noise and scalar/hash projections downstream, but off_q still exists during preparation. Full `_finish_owned` paths/trace snapshots require separate copies/backings; exact finishing-order peak needs observation and review. |
| CE06 on/off plane scratch, same function:834+ | on `8*P*Y*X`, optional off same; on_fft `16*P*Y*(X//2+1)`, optional off_fft same; einsum output `16*Q*Y*(X//2)` plus camera/FFT scratch | These are per-z planes, **not TDPZYX float64 frames**. Camera.load copies/converts and its chained arithmetic has transient planes. Locals survive last use until overwrite/function return: old on/off/FFT may coexist with a replacement allocation at the next z. Axial FFT creates a q slice-sized temporary while q lives. Drift ramps/traces add selected witness allocations. |
| CE02 contextual path, `acquisition/preparation.py:406+` | Direct preparation has full float64 `T*D*P*V` frames | Separate public direct-stage path. **Do not charge this to CE06 workflow preparation.** |
| Estimator source, `parameter_estimation.py:1150+` | Full copies `Bq` from prepared q; compact aliases q | Coexists with bands. Full copy lives through estimation. Carrier/modulation arrays scale T,D,O but are small relative to volumes. Search reuse is carrier-only: later times still build/fill overlaps for current-time modulation. |
| Overlap build, `build_order_overlap:492–570` | fourier `32V` (two complex sides), spatial `32V`, full-only written mask `2V`; inverse unnormalized expression can additionally allocate inverse temporary `32V` during multiply | Fourier and inverse/spatial coexist in build. Compact result keeps spatial and descriptor, fourier/mask are not retained. Full overlap records retain Fourier/spatial/written for every published build. Number of builds is branch/output evidence, not guessed from D*O alone. |
| Search coarse/refinement, `estimate_coarse_carrier:705+`, `search_carrier_and_modulation:790+` | Coarse conjugate/product temporaries scale V; reduction product and correlation are complex YX; power is float64 YX with abs/square temporaries. Refinement working overlap has `32V` spatial | Coarse local dies on return in compact, while full overlap/trace retains its volumes. Do not sum all compact sequential search builds as persistent. Regression temporary arrays/native scalars require inspection on final base. |
| Filtering source/destination, `known_parameters.py:1114–1180` | Compact source aliases prepared time slice but keeps whole Bq backing; filtered `Bqt`. Full original time copy `Bqt`, outer filtered `Bqt`, and `filter_native_quadratures()` return destination `Bqt` | Stable original source is read while destination is written. Full return-copy overlaps both outer destination and source before assignment completes. Original deleted before assembly; prepared bands remain. Full prior time results retain filtered arrays. |
| Native harmonic scratch, `_filter_native_quadratures_into:724+` | One full native plus array `16V` per positive order | Local `plus` has no explicit del. Assigning next positive-order `np.zeros` evaluates RHS before replacing prior plus: potentially **two 16V backings** during replacement. Sequential directions/orders are not all simultaneous. |
| Embedding/inverse, `assemble_signed_image:837–875` | image `I`; padded `16Vo`; spatial inverse `16Vo`; 2d branch zeros_like spatial plus plane inverse output | FFT requires padded and inverse together. `del padded` occurs before phase expression, `del spatial` after addition. Backend workspace remains unknown. Prepared q, filtered and earlier per-time outputs coexist. |
| Phase/exponential/product, same function:879–889 | phase float64 `Yo*Xo` (no Z); `1j*phase` and exp complex YX, product complex Vo, real view shares product backing, scalar-times-real creates float64 Vo | Source predicts full complex spatial and product overlap, with expression temporaries. Phase is **not** explicitly deleted; it survives into next embedding/inverse and can overlap old/new phase construction. Do not claim a new full complex Vo exponential (broadcast is YX). Exact ufunc release order/native workspace are unresolved. |
| Time aggregation, `workflow/reconstruct.py:376–436` | Compact images list retains T images total `T*I`; concatenate creates another `T*I`. Full list retains per-time known result (image and filtered diagnostics); concat creates another `T*I` | Compact bands dropped before result stage. images.clear after concatenate releases compact per-time images. Full reconstructions remain in published result; coordinate copy ownership differs. Do not add dropped bands to compact concatenate just because they existed earlier. |
| Final retained result / caller | Actual backing traversal pending execution | RM84 helper counts NumPy roots once, records arrays and incomplete sys.getsizeof metadata. It rejects foreign backing owners instead of inventing an allocation size. Result hashing/traversal is after call timing but inside final whole-process ru_maxrss. |

At central64, source arithmetic gives `V=32,768`, `H=16,896`,
`Vo=131,072`, caller raw `1,966,080 B`, `Bq=4,055,040 B`,
`Bqt=4,055,040 B`, positive-harmonic plus `524,288 B`, one overlap side
pair `1,048,576 B`, one padded/inverse volume `2,097,152 B`, and per-time
image `1,048,576 B`. These are **individual payload calculations**, not an
aggregate memory estimate or observed process peak. Witness geometries must use
their own dimensions; on/off count N multiplies caller off exposures but does
not multiply the single off_q volume family.

No numerical ranking is supported yet. Candidate mechanisms for investigation:
expression/phase lifetimes, compact filter source/destination/scratch coexistence,
compact working overlap lifetime, per-time output concatenation, and full debug
retention. Prioritize only after measured stage association and matched mode/
search/T contrasts establish relevance. Native FFT, Python/NumPy allocator caches,
fragmentation, shared pages, copy-on-write, finite-check boolean temporaries and
OS sampling/accounting effects can dominate unassigned process RSS. A payload sum
or `peak - pre-call high-water` cannot isolate reconstruction memory.
