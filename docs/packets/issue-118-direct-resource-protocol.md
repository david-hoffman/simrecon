# PH118 direct-stage resource protocol v1

Frozen public design for independent B2 review before implementation. It is not
an execution grant or measured benefit. The new adapter is STATIC ONLY: no
import, CLI/help, dry-run, timing/RSS/payload measurement until the actual
accepted parent117 and root's exclusive resource grant. Ordinary Ruff/format/
Pyright may inspect its source. Scientific meaning remains PH118 S01–S26.

## Exact inventory

All rows use one retained caller set, one fresh process and ONE public target
call. Both actual parent and candidate run every row three times; raw outcomes,
including failures/preflight rejections, are retained. No candidate-driven shape
or case substitution. "64"/"128" are lateral native lengths, not output labels.

| Fixed case ID | Target entry / classification | T,D,P,Z,Y,X / O,L,A | Explicit branch/settings |
| --- | --- | --- | --- |
| acquisition-64 | DIRECT `prepare_acquisition_bands`, core | 1,3,5,8,64,64 /3,2,1 | 3d, uniform, dxy=dz=1um, background0, edge0, equalize=False; no off/drift |
| acquisition-128 | DIRECT `prepare_acquisition_bands`, core | 1,3,5,8,128,128 /3,2,1 | Identical declarations; only lateral native extent differs |
| acquisition-off | DIRECT `prepare_acquisition_bands`, core off/state | 2,2,5,2,10,10 /3,1,1 | 3d,dxy=.1um,dz=1um; scalar background3; sine edge-1; equalize/z/time=True; N2; selectors(1,1,1); varying on extra background; one off sentinel; optics below |
| acquisition-drift | DIRECT `prepare_acquisition_bands`, core stateful drift | 2,3,5,2,10,12 /3,1,1 | 3d,dxy=dz=1um; mapped background/slope below; N2; between=True,highpass=.2; edge0/equalize=False; ordinary direction-major; within/fit/adjust=False |
| known-64 | DIRECT `reconstruct_known`, core | 2,2,5,8,64,64 /3,2,1 | Genuine AcquisitionBands prepared BEFORE target timer; caller-supplied carriers/modulations and radial transfer below |
| known-128 | DIRECT `reconstruct_known`, core | 2,2,5,8,128,128 /3,2,1 | Same direct-known declarations; only lateral extent differs |
| preparation-context-64 | DIRECT `prepare_bands`, contextual compatibility CONTROL | 1,3,5,8,64,64 /3,2,1 | Same no-off values as acquisition-64 on CE02; NOT the claimed changed preparation path or a CE06 replacement |

The adapter offers exactly these seven IDs, not arbitrary shapes/entry names.
All scalar quantities/flags not overridden above have the inherited public
defaults: no supplied phase list/steps, no timestamps/header phases, no phase
adjustment/within fit, no off combination unless selected, ordinary layout.
Optics where selected: wavelength500nm, NA1, immersion1. Known filtering:
w=.5, increment0, suppression=False, radius10 recorded but inactive,
dampen/omit/kz-omit=False, overlaps=True, taper none, precise=False,
explode1, no power exponent. No estimator or search is called by this adapter.

## Generators, values and declarations

The new named adapter contains every direct-case generator; its final byte hash
binds formulas AND constants/settings/dispatch/liveness. No random seed or
candidate-dependent pattern is used.

No-off/core-known raw generator is the already frozen RM84 analytic formula.
For integer voxel indices x,y,z, object counts are
30+3*cos(2*pi*(x/X+y/Y))+2*sin(2*pi*(2*x/X-y/Y))
+cos(2*pi*(z/Z+3*x/X))+.75*cos(2*pi*(3*y/Y+x/X)).
At direction d use angle=d*pi/D and spatial=2*pi*(x*cos(angle)+y*sin(angle))/8.
At phase p, phi=2*pi*p/5; illumination is
1+(.31+t/64)*cos(spatial+phi)+(.13+t/128)*cos(2*spatial+2*phi+.3).
Raw=obj*illumination+d/4+t/8, explicitly cast ONCE to float32 detector samples.
Generator arithmetic uses float64; its object/illumination/index temporaries
end when the generator returns, before target timing. Their earlier high-water
remains part of the whole-process peak; no subtraction erases it.

Off/drift use the approved CE07 T2/P5/Z2 patterned-case formula, copied exactly:
raw=80+7*t+3*d+2*p+z+((x*x+3*y+p*x+2*d*y)%17)
+9*(x==(2+p)%X)+5*(y==(3+d)%Y), stored float64 exact integers.

Off: off exposures stack(raw/2,raw/4) on axis4, float64 dyadics; set
off[0,0,0,0,0,-1,-1]=-1. Exposure background is arange(40).reshape(2,2,5,2)/8,
float64. Selectors int32(1,1,1). This is the approved off-sum-offset-plane0
control, not averaged off data or an inferred noise model. Caller slope/phases/
clocks remain None. Background is scalar3.

Drift: for each t,d replace raw[t,d] by roll(raw[t,0],(d,-d),axes=(-2,-1)).
Background float64 map is3 everywhere, corner5 and left neighbor3.5. Slope map
float64 is.75. Set raw[0,0,0,0,-1,-1]=-1; off is stack(roll(raw/4,(1,2)),
roll(raw/2,(-2,-1))) on axis4, spatial rolls on the last two axes.
This exactly matches the stateful first-off/persistent-sentinel public fixture.
Normal time0 loading changes the corner camera map; time1 prepass must consume
the current map. No fake clock or fitted constant input is substituted.

Known: setup DIRECT `prepare_acquisition_bands` uses the no-off declarations and
multifrequency raw(T2,D2,P5,Z8). Keep the real returned record, raw and settings
alive. Declare radial samples complex128(3,64,16), computed dyadically as
1+m/16+r/128+i*(m+r+k)/256, dkr=dkz=.125cycles/um. All samples are exactly
complex64 representable, while the declaration returns the accepted transfer.
Retain the original declared sample array AND transfer record.
Carriers float64(D2,2) are ((.125,.03125),(-.0625,.125))cycles/um.
Modulation complex128(D2,2) is
((.5+.125i,-.25+.0625i),(.375-.125i,.25+.1875i)). Both side harmonics are
nonzero across time/direction. They are explicit caller values, never fit truth
replayed from candidate output. No PreparedBands/AcquisitionBands is fabricated.

Known support at Z8 gives clipped cutoffs(3,3,3), R=.5cycles/um. Actual self
queries r<=.5 and eligible other queries r<.5 use radial coordinate<=4, so the
next radial vertex<=5 is inside64. Native dzf=.125, dkz=.125 gives z coordinates
-3..3; one-time periodic wrapping and next-vertex wrap are inside K16. Thus
all actually requested zero-weight stencils remain present. w^2=.25 is a
positive denominator lower bound. No nonnegative-image or resolution claim.

## Public qualification witnesses and interpretation

Every case must qualify on the actual frozen parent before candidate execution;
record failures without replacing cases. The adapter asserts basic public
shapes/dtypes/finite values, exact uniform noise1, expected event counts and
preserved callers, not a new accuracy threshold. Acquisition no-off has24 phase
designs. Off has8 phase designs and24 repeated-plane0 combination events plus
one sentinel. Drift has12 designs,2 builds,4 correlations, one sentinel and final
corner background3.5/slope1. Known has image(T2,Z8,2Y,2X), supplied parameter
bytes, cutoffs(3,3,3) and nonzero prepared first/second harmonic operands.

Independent scientific acceptance comes from approved raw finite/phase/filter/
drift tests and the RC1 debug-capture witness, not fingerprints or these resource
predicates alone. Complete input/result public-value fingerprints include dtype,
shape, ordering, float/complex bits and signed zeros via unchanged
`RM84-public-values-v1`. Matched parent/candidate fingerprints must be exact;
no gain fit, tolerance relaxation or favorable numerical output selection.
Retained full-debug payload may stay identical while temporary overlap changes.

## Caller/result liveness and observation timing

The adapter retains raw, all off/maps/offset/selectors/parameters, settings,
original declared samples/transfer and any setup AcquisitionBands through target
execution AND all post-target observation. args/kwargs alias these same caller
objects; union payload counts their shared backing once. No caller deletion,
garbage collection, output preallocation, streaming or value rewrite is a
precondition. No spatial export/disk array/numerical child worker is created.

For known cases, setup preparation and transfer declaration finish before the
target timer. Generator/index/roll/setup local temporaries then expire naturally;
no hidden prep replay occurs during target known timing. Their allocation
high-water remains visible. Input hashing and caller-payload observation precede
the pre-target sample and are included in process accounting. All returned
result records remain alive while public fingerprints/result/caller-union payload
are observed. Qualifying predicates run AFTER the target-return sample.

Report separately native ru_maxrss at pre-target, immediately after target return,
and after result/hash/payload observation, with Linux KiB*1024 byte conversion.
Record call-only monotonic seconds. Peak minus pre-target is NOT an isolated
stage peak; payload is NOT RSS. Record caller/result/union backing-aware payload,
Python metadata estimates/foreign-owner limitations, host/cgroup/swap/page faults,
allocator and backend/thread information. Retain every raw observation, then
median/range/variation across3 fresh processes, separately by entry/case/role.
Actual backend workspace, allocator sharing and swap attribution can remain
unknown; say so. Redirected artifacts/log disk use is measured externally when
resource execution is granted. No latency/byte/percentage ceiling is selected.
If peak reduction cannot be separated from variation, report it unestablished.

## Frozen provenance and future invocation boundary

Reuse unchanged `reconstruction_memory_benchmark.py` public-value fingerprint,
retained_payload, rss_bytes, host_context and THREAD_CONTROLS. Its SHA256 is
`929106da36b47bcd03ed785d1a7f6b941d04299403b6c0ffe7df9846f3809b8f`.
The inherited RM84 generator/design file SHA256 is
`271335a5065791a986de239cdf89e4d15eb0f2e5df80943d6cb084167516d20f`.
The adapter's final reviewed hash is supplied outside its bytes and recorded in
the A revision2 report/B2 packet; this protocol's final hash is likewise external.

Future exclusive execution uses the pinned Ubuntu, locked `uv --no-sync`,
unchanged source-free wrapper and thread variables OMP_NUM_THREADS,
OPENBLAS_NUM_THREADS,MKL_NUM_THREADS,NUMEXPR_NUM_THREADS=1 BEFORE process startup.
Invoke the same frozen adapter bytes once with --case one of the seven IDs,
--role parent/candidate, --repetition1/2/3, --worktree, --expected-python,
--expected-module-root, --revision, --tree, --dirty true/false, and expected
--adapter-sha256/--shared-observer-sha256/--lock-sha256. No execution/help/import
is authorized by this document.

Stage byte-identical reviewed adapter/shared observer into each selected actual
revision's tests directory, without changing product/lock/environment. Record
that staging, paths, hashes and Git dirty identity. The adapter validates cwd,
explicit interpreter path and selected .venv prefix, Python3.13.12, HEAD/tree/
tracked dirty identity, its own/shared observer/lock hashes, and package import
origin beneath the selected worktree module root BEFORE importing the target
package, then checks its actual imported origin again. Package distribution version,
public version and direct_url editable origin are recorded; a conflicting
worktree origin rejects. Tracked dirty runtime/tool/lock inputs reject: only
the named reviewed owned tests/protocol/report paths may differ. No source/diff/
history content is read for these metadata checks. Git identity/status children
are non-numerical provenance work before target timing.

Freeze actual accepted parent/candidate Git/package/input/profile/environment
identities before comparing; names here are not a substitute. Host/cgroup and
locked NumPy/SciPy/FFT/allocator/thread settings must match per comparison; never
pool hosts. Preflight representation/headroom rejection is recorded for BOTH
sides and routed before changing the inventory. Dimensions here are modest
representable examples, not a workstation feasibility promise or a deliberate
OOM experiment. No adapter execution/qualification has occurred in this revision.

## Separately retained workflow experiments

Keep the unchanged RM84 CLI's six primary(T,D,Z,Y,X) shapes:
(1,3,8,32,32),(1,3,8,64,64),(1,3,8,128,128),(1,1,8,64,64),
(2,3,8,64,64),(4,3,8,64,64). Both existing full and summary entries, both roles,
three fresh repetitions; supplied/no-search variants are core workflow series,
their already-frozen searched counterparts are contextual search-cost series.
Retain its native2D/off1/off2/between/within cases as separately labelled workflow
mode context under the existing design. Do not call its 'known' workflow case a
direct known reconstruction measurement. This direct adapter neither replaces
nor modifies the inherited observer/series. No numerical/performance threshold,
full-gate waiver or accepted checkpoint follows; fresh B2 reviews all affected
fixtures/observers/protocol before C and resource execution.
