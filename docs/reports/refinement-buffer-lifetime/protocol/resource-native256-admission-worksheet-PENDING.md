# RB117 native256 live-payload and admission worksheet — PENDING

FILE/SOURCE ONLY, no target/control/helper execution or new framework. This is a
conservative inventory of explicit allocations and missing allowances, NOT a
complete process peak bound, admission, memory budget, measured saving or universal
FFT/allocator guarantee. ROOT separately admits each revision/mode/profile from
fresh actual resources after the central/2d/profile prefix. No old116 thresholds
or measured peaks become new caps. The original larger2048 target remains outside
this256 worksheet and allocation-unadmitted.

## Exact sources and literal shape

Parent158776ade28079276304d49a6b973eccbf4109c9 estimatorf9a924d277518cdb0717c7fe82961f3d36a480109bcbef9f8d19b42fdae7d7e8;
candidatee6945817850cfdaa3ebbfe21e7a23784964208d6 estimator527bb3459e295a5cec0a776a464d82723e32b0b6f64e3d47f3eb514529e19b38.
Shared exact source: workflow/reconstruct.py50a4ce199f0cceca6ba9147a1ee218441b1b5588c03beabecef95828802e28fa;
known_parameters.pyedb87b64e1691b7f437194aabc0df8d4ab22e3e67b6b05639dbd3bad26e2c645;
acquisition/modes.py4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1.
Same fixture271335a5…d20f/value929106da…b8f and external eacf/6f34/5249/56c1/1854
measurement overlay; old116 sources and data immutable. Inherited source worksheet
analysis/liveness-draft.md337ae76c…b5c was checked against named current allocation
sites, with only the candidate refinement lifetime delta reconciled below.

Declared native workload omits case key: workload((1,3,8,256,256),search=True),
T1,D3,P5,O3,Q5,Z8,Y256,X256,L2,A1; full or summary, profilefalse ortrue.
V=Z*Y*X=524288; H=Z*Y*(X//2+1)=264192; Vo=8*512*512=2097152.
No precision change: callerfloat32, mathematical bulkfloat64/complex128.
Required outputs image[1,8,512,512]float64, x/y[512],z[8]float64,
carriers[1,3,2]float64, modulation/raw[1,3,2]complex128; T1/D3 searched branches.
Profile adds the unchanged10 paired scalar enter/exit events for nativeT1 stages,
not numerical calls or stored volume references. Hook/list/serialization overhead
and timing perturbation remain real and separately observed, not assumed free.

## Explicit payload families and timing of owners

Bytes below are source arithmetic, not RSS; ndarray views do not add backings.
Do not sum different stages or every sequential scratch as simultaneous.

| Family | Literal payload at256 | Owners / overlap obligation |
| --- | --- | --- |
| Caller raw float32 | 4*T*D*P*V=31457280B | Child retains case through final observation; generation indices/object/illumination have earlier whole-process effects. |
| Caller radial transfer | 16*3*64*16=49152B | Held with case; declared exact dyadic input, no empirical/off/drift arrays in this selected fixture. |
| Workflow raw snapshot | 31457280B | Independent same-dtype copy at reconstruct.py278; coexists with caller during preparation, explicitly deleted352 before estimation. Do not charge it into later stages after deletion. |
| Prepared q | Bq=16*T*D*Q*H=63406080B | modes allocates all-T q; compact aliases downstream, full retains diagnostic q. No off_q in this fixture. Compact bands remain through time loop, dropped425 before concatenation. |
| CE06 per-z on plane | 8*P*Y*X=2621440B | Per-z scratch, not a full float64TDPZYX volume. Replacement old/new may overlap. Camera arithmetic and finite-check planes are additional. |
| CE06 on_fft / separation result | 16*P*Y*(X//2+1)=2641920B; 16*Q*Y*(X//2)=2621440B | q remains; axial FFT may allocate a q-slice temporary. Full event-owned captures add copies. Unknown FFT workspace not included. |
| Full estimator source copy | 63406080B | Full/direct copies prepared q at estimator1166; compact uses same prepared backing, no extra Bq. Copy remains through estimation. |
| One Fourier OR spatial overlap pair | 32*V=16777216B | Build allocates Fourier, then inverse temporary and scaled spatial; up to3 explicit pairs can coexist during RHS evaluation, plus backend workspace. |
| Full written mask per build | 2*V=1048576B | Full only; no compact mask allocation. Carrier arrays/metadata additional. |
| Full searched9-build Fourier+spatial+mask aggregate | 9*(64*V+2*V)=311427072B across27 volume backings | Successful nativeT1/D3/O3 searches publish coarse/refinement/later-order per direction. Persistent full diagnostics, not one allocation or candidate saving. Coarse/event copies and small records are additional. |
| Refinement fit | frozen spatialpair16777216B; higher complexV8388608B; energy abs/power floatV4194304B each; conjugate/product complexV8388608B each; phaseYX524288B, complexYX1048576B | Source fit625–630 uses lower view, higher*phase, abs-squared reductions, conjugate*product. RHS temporaries/finite bool arrays can overlap; scalar outputs do not retain them. Do not label all expressions simultaneous or ignore native workspace. |
| Compact stable filtering / destination | prepared alias Bq plus one filteredBqt63406080B (T1) | Full source copyBqt, outer filteredBqt and returned filter helperBqt can coexist, in addition to prepared q. Helper676–704 copies original then returns it; outer assignment awaits return. |
| Positive harmonic scratch | 16*V=8388608B; old/new replacement can be16777216B | Same known_parameters scratch on both117 roots, not repaired by117. |
| Enlarged image per time | I=8*Vo=16777216B | Retained through accumulation; full has additional published one-time image plus workflow image/concat ownership. |
| Padded / inverse complex volume | each16*Vo=33554432B | Both coexist for FFT; padded deleted before phase expression, spatial deleted after addition. Backend workspaces remain unknown. |
| Assembly expression | phasefloatYX2097152B; complexYX4194304B intermediates; spatialcomplexVo33554432B plus productcomplexVo33554432B and real view; scalar-times-real floatVo16777216B | Phase local can persist into next loop/replacement. No fullVo exponential: phase exp is YX broadcast. Exact ufunc release order/allocator effect unresolved. |
| Final concatenate / public graph | T1 compact list image16777216B plus concat16777216B temporarily; full keeps all required records/filtered arrays | Compact clears images after concatenate and bands before it. Result hashes/traversal after timed call still contribute whole-process RSS. |

Conservative admission MUST account for at least these real coexistences and
additional trace/metadata/backend owners; the table is not an upper bound:
- Full filtering can hold callerraw31457280 +preparedBq +stable fullsourceBq
  +outerfilteredBq +returnfilteredBq +persistent9overlap311427072 =596508672B,
  before transfer, full coarse/event captures, native scratch, FFT/allocator or
  observer/OS overhead. Therefore the central64 process512MiB setting cannot be
  reused blindly for full256; explicit source payload subset already exceeds it.
- Compact estimation/reconstruction uses different maxima. Caller remains; prepared
  q aliases, filtered q and later enlarged arrays coexist. It is invalid to add
  the deleted raw snapshot or all sequential overlap builds as persistent compact
  allocations. Add actual native/allocator/generation/hash/finite/copy allowances
  separately; these source bytes alone do not predict a resident peak.

## Actual117 change and mode/profile-specific uncertainty

Parent search keeps its frozen refinement build through the later-order loop.
Candidate _refine_frozen_pair805–899 returns only carrier and scalars, terminating
its acyclic build/objective/bracket scope before outer later-order build799.
In compact mode this removes one identified spatialpair16777216B owner interval
at256. Later build can still co-live with Fourier/inverse/spatial and q; temporary
regression work may have a different maximum. This is allocated-payload lifetime
reasoning, not a16MiB terminal saving or allocator-release guarantee.

Full mode self.overlaps retains the very same refinement record intentionally;
its spatial/Fourier/mask backings survive helper return. Full311427072B diagnostic
aggregate is preserved, no promised full saving. Same literal search arithmetic,
strict state/brackets/frozen pair/build counts/trace identities/error ordering
remain required. Neither profiletrue scalar observations nor finite parity alone
proves that temporal last-use obligation; C/static proof and later independent
review cover it. Accepted115 wide-domain/shared-helper material remains; scientific precision stays
double, and113single is absent.

## Representation and fresh admission premises

Selected counts are positive and modest relative to inherited signed/native limits:
raw7864320 elements; preparedq3962880 complex elements; image2097152 elements;
one overlap pair1048576 complex elements. Individual byte/stride extents above
are within64-bit intp and counts/dimensions within signed32. This is source shape
arithmetic, not an allocation/backend call or waiver of actual native aggregates,
wrapped indices, cutoff casts or real transfer stencils. Existing actual positive
256116 runs support historical fixture compatibility only. Parent/C candidate
retain identical signed/native/stencil guards; any runtime rejection remains data.
Accepted115 removes obsolete byte-only ceilings, supplies no RAM-fit guarantee.

Before EACH256 row ROOT still needs actual clean selectedHEAD/tree/material/import/
fixture/environment identity; unchanged source and necessary smaller-case evidence;
explicit separate256 growth/profile/mode declaration; actual expected input/schema/
branches and paired3rep order; process ownership/exclusive window and current
visible cgroup namespace/membership/mount/max/current/swap/events, host/disk/rlimits,
time-bound domain correspondence/proof horizon and unknown external actors/ancestors.
Choose mode-specific predicted co-live payload/native/allocator/observer allowance,
process stop and separate reserve with real conditional margin. No existing512MiB,
16GiB maximum, old116 cap or observed peak is new admission. Caller/result retention,
post-JSON/terminal/exec-prehistory scopes and RSS-gap limitations remain explicit.
ROOT must consider interruption overshoot/reap/FD cleanup and stop on any actual
failure. Candidate real process peak remains unmeasured at256; profile may perturb.

## Historical256 context only and smaller current evidence

Accepted116 canonical table context, not copied thresholds or new numeric truth:
searched summary unprofiled terminal314888/319052/319220KiB, call
1721.99578851/1818.263636516/1820.79672742s; full unprofiled
665384/666316/667476KiB, call1521.354077427/1545.913683616/1586.09627256s.
Summary profiles326288/327132/329700KiB, call1335.172755667/1470.766478159/1550.452105608s;
full profiles677652/678956/679808KiB, call1424.11516996/1720.852829409/1790.373879817s.
Recorded stage association places largest summary high-water after estimation,
not evidence that removing an estimator owner reduces terminal peak. Values are
historicalEA observed scopes on original environment, not relabeled117 results.
The native256 workflow calls themselves exceeded20minutes; current240s central64
choice cannot simply transfer. ROOT must freeze justified finite whole-child and
outer-wait/time-proof allowances before its separately admitted future rows.

Current assessed smaller rows:4tiny2d pass plus6central64summary pass (cumulative
assessmentc09c0350…9260b); one60s operating timeout preserved/diagnosedbe5ae13f…ca55d7.
Central summary candidates show no terminalpeak reduction; their caller/result
payloads equal parents. Current full/centralprofiles and remaining2d must be
collected separately before corresponding256 admissions. No largest/profile gate
or current margins are supplied by this worksheet. Final117D and post118 affected
SCI applicability remain required before downstream119/120 reliance. No runtime,
threshold/helper/source change or acceptance follows; unknown costs/meters retained.
