# SP112 finite precision characterization

This study supports a narrowly staged mixed-precision proposal. It supplies
actual pinned-interface observations and independent sparse/scalar references.
It does **not** implement or qualify an end-to-end single reconstruction, general
search, CE06 single preparation or 16 GiB workstation execution. The proposed
first intake remains stationary 3D known-parameter reconstruction from the new
independently declared `PreparedBands32` record. Proposal acceptance still needs
a fresh independent scientific assessment; the author supplies no self-approval.

## Evidence identity and execution

Scientific/public runtime baseline: `b344e41a8b52de76d7cbbf8450319893904c3b8f`,
tracked tree `01eb11ff48e022469f88fd6553b8cb3771768347`. Study docs/scripts are
untracked/dirty at measurement, not that commit's shipped artifacts. Every raw
run records the actual commit/tree/status, script/source/lock identities,
executable, process arguments, environment, call elapsed time and native RSS.
No earlier observation may be attributed to a later documentation commit.

Only the coordinator-granted Ubuntu Docker interpreter was used for numerical
work, with the exact route below and one-thread controls. No installs, backend
changes, product edits, product tests or full `make verify` were performed by
this role. Root owns full verification and same-run coverage/M25 evidence.

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-112 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  -e NUMEXPR_NUM_THREADS=1 -e VECLIB_MAXIMUM_THREADS=1 \
  simrecon-campaign-ubuntu .venv/bin/python \
  docs/reports/single-precision-study/study.py freeze
bash docs/reports/single-precision-study/run.sh first
bash docs/reports/single-precision-study/run.sh small
```

The shell runners expand to the Docker route, one workload per fresh process,
three repetitions, with `timeout 30s`; every expanded command and process exit
status is in [commands.log](raw/commands.log) and
[process-status.log](raw/process-status.log). A shell exit zero alone is not a
scientific success: scripts retain caught failures as JSON `status="failed"`.
The corrected runner additionally stops on a failed JSON status. A timeout
would be incomplete evidence, never a numeric failure/success.

The first freeze [manifest.json](manifest.json) has SHA256
`5df2545e79e3a16d5f319cead3d79a9741e9469ac6eaefe20fa29e6be839650d`:
16 concrete kernel declarations, 114 planned kernel processes and 12 small-probe
processes. This is a finite list, not a Cartesian product. The separate
[supplement manifest](supplement-manifest.json) freezes 12 workloads/36 planned
processes, including generated search hashes. Immutable original scripts and
manifests are copied under `revisions/preweighted-v1/` and
`revisions/supplement-v1/`; original raw JSON remains unchanged.

[preflight.json](raw/preflight.json) observed Ubuntu 24.04.5 LTS,
Python 3.13.12, NumPy 2.5.3 and SciPy 1.18.1, glibc 2.39 on Linux x86_64.
NumPy configuration reports OpenBLAS 0.3.34.106.0 (ILP64); SciPy reports
0.3.31.dev (LP64). Those are reported BLAS configurations, not proof that BLAS
performs FFT work. FFT internal accumulation/workspace and actual allocator
allocation attribution are unknown. All five requested thread environment
variables are `1`; SciPy prototype FFT calls explicitly use `workers=1`.
Backend internals/effective threads beyond those observations remain unknown.
The lock SHA256 is
`222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b`.

Native Linux `ru_maxrss` is KiB; bytes are raw value times 1024. Pre-call
high-water, call-end high-water (kernel cases), and whole-process high-water
include imports, retained caller inputs, generation and observer allocations.
Peak minus pre-call is not an isolated algorithm peak. Logical retained ndarray
payload counts shared backing once; Python metadata/allocator/backend workspace
are not included in that payload. Shared pages are not separately attributed.
Exclusive campaign scheduling reduces known interference; unrelated host work
remains unknown. These small timings are descriptive and do not predict speed.

Raw overflow probes preserve Python JSON nonfinite literals (`Infinity`/`NaN`)
through `allow_nan=True`; those particular original files are not strict RFC8259
JSON. Their separate finite/status/classification fields identify the intended
domain outcomes. Preserve original bytes and use a reader supporting these
literals; do not interpret a parser-normalized number as a finite value. The
timing/RSS summary artifacts contain finite numeric observations.

## Exact data and independent references

The first-slice fixture is explicitly constructive. For `(T,D,P,Z,Y,X)` with
`P=2O-1`, every half-spectrum coefficient is zero except `(z,x)=(0,0)` and
`y=0,+Y/4,-Y/4`. Slot order is `0,E1,O1,...`. For scale `s=2^power`, direction
sign `(-1)^d`, time index `t`, and positive order `m`:

- Order zero: DC `-s/4`; each conjugate y coefficient `s/2`.
- Side band `B_m=E_m+i O_m`: DC
  `((-1)^d*s*m*(t+1)/8) - i*s*m/16`; each y coefficient
  `((-1)^d*s/(8m)) - i*s/(16m)`.
- Noise `v[t,d,m]=1+d+t`; modulation
  `a[t,d,m]=(-1)^d*(m+t)/2+i/4`; order zero has modulation one.
- Unit transfer, `dxy=dz=1 um`, `R=1/2 cycles/um`, Wiener `w=1/2`, taper none,
  suppression off. Carrier is zero except M03's signed one x-bin
  `kx=+/-1/X cycles/um`. Other-order support uses the CE04 strict inequality.
- M06 instead uses DC-only center `+1`, side `-1/2` (exact cancellation) or
  `-(1-2^-20)/2` (near cancellation), modulation one, noise one.

All listed components are exactly binary32 representable. Therefore `x0=x32`
for these witnesses, and input quantization error is exactly zero. Per-time noise
is independently declared; later modulation differs at T2. Every other bin,
slot, shape and parameter is fixed by [study.py](study.py) `declarations()` and
`modes()` and hashed before trials. No preparation result supplies expected
coefficients. CE alpha is `1/(XYZ L^2 A D)` and describes the already-scaled
band units; CE04 does not multiply alpha again. A corresponding pre-scale
finite coefficient is explicitly the declared coefficient divided by alpha.

The independent reference evaluates CE04 scalar quotients using Python rational
arithmetic, then the sparse unnormalized positive-sign inverse finite sum and
signed side factor two. Integer zoom preserves positive signed lifts. Only
quarter/eighth roots occur. Eighth roots use the rational enclosure
`sqrt(2) in [1414213562373095048801688724209698078569/10^39,
1414213562373095048801688724209698078570/10^39]`, independently checked by
squaring both endpoints around 2. Rational interval operations supply reference
width. There is no transcendental library/double-as-truth oracle here.

For candidate c and reference `[l,u]`, raw metrics retain lower distance
`max(l-c,0,c-u)` and upper absolute error `max(abs(c-l),abs(c-u))`, signed
extrema, RMS to the interval midpoint, declared signal-scale normalization,
`sum(abs(terms))`, and cancellation conditioning. The max-error metrics use exact
fractions of actual returned floating values; their final JSON rendering is
binary64. RMS is a descriptive binary64 observer statistic and may round to
zero for sub-ulp errors; the rational max-error result remains nonzero. Zero
reference scale has no relative error; zero reference samples have infinite
conditioning rather than a hidden pixelwise relative score.

## What the prototype actually measures

The original v1 kernel takes its scalar factor from the rational reference,
rounds that bounded scalar to the chosen complex dtype, multiplies declared
coefficients, pads a sparse spectrum and calls SciPy `ifftn(norm="forward")`.
It uses an explicitly rounded bounded complex64 phase ramp, complex64 bulk
products, a float64 image accumulator, and a float32 final copy. The matched
prototype-double kernel follows the same finite operations in complex128 and
float64. It is a **preweighted sparse FFT/assembly** experiment, not a CE04
filter implementation or a future runtime benchmark.

Two methodology limits were diagnosed after original trials started and remain
attached to every v1 run. Its exact-derived scalar does not characterize binary64
filter-denominator evaluation. Its retained recombination snapshot obtains the
opposite coefficient from exact reference algebra and is **payload-only**;
that snapshot is not consumed to assemble the image. It cannot prove a correct
filtered-quadrature output. A separately frozen supplemental scalar probe
independently evaluates binary64 self/other powers, ordered denominators and
scales against the rational reference; a corrected full-component probe forms
both candidate opposite coefficients before recombination. These separate
observations do not retroactively qualify v1 as full filtering.

Existing public double controls use `prepare_bands` to create valid CE02 history,
then assign the independent complex128 coefficients/noise to documented writable
used fields and call public `reconstruct_known`. They never place complex64 data
in an old schema. Their image reference remains the independent rational finite
sum, not a replay through product helpers. The proposed new constructor is not
implemented or called by these scripts.

## Observed small arithmetic and dtype evidence

The 4-point forward/inverse DFT witnesses were exact for both observed NumPy
and SciPy interfaces. The 8-point forward/rFFT component error was
`4.7503027670911654e-8` with reference width at most `1.25e-39`; normalized
inverse error was `5.937878458863957e-9`. Both APIs returned complex64 for
complex64 FFT and float32 real-forward input in the pinned versions. This
observation must not be generalized to older NumPy versions.

Supplemental dtype probes use the actual multi-axis interfaces: `rfft2` on
`(-2,-1)`, axial `fft(axis=-3)`, `ifftn` on `(-3,-2,-1)` with norm forward,
`fft2`, `irfft`, and `irfftn`. Returned dtypes are raw evidence only; internal
FFT accumulator/workspace precision remains unknown. A complex64 spatial array
times `exp(1j*float64_phase)` promoted the product to complex128. Rounding the
bounded ramp to complex64 before multiplication kept the product complex64.

Selected signed-image maximum absolute error upper bounds, identical across
three repetitions for each profile, are shown below. These are observations,
not adopted universal tolerances.

| Fixture | Mixed preweighted kernel | Public double control |
| --- | ---: | ---: |
| M02 signed, zero carrier | 7.152557373046875e-8 | 4.4408920985006264e-17 |
| M03 zero modulation | 2.384185791015625e-8 | 8.881784197001253e-17 |
| M03 carrier +/- one bin | 4.5299530029296876e-8 | 9.473903143468003e-17 |
| M04 D3/O3 | 1.2548346268503289e-8 | not measured |
| M06 exact cancellation | 0 | 0 |
| M06 near cancellation | 4.584972675030048e-9 | 4.270088556250602e-18 |

M05 scales `2^-100`, `1`, `2^100` produced mixed absolute errors
`5.64237288394698e-38`, `7.152557373046875e-8`, `9.066943647109718e22`.
Each had error divided by summed absolute terms
`7.035302334144467e-8`. Large absolute values at `2^100` illustrate why a
blanket absolute tolerance is inappropriate. M06 near cancellation's small
signed reference is judged in absolute units, never divided by each pixel.

The reduction witness has exact `SX=5, SY=5/2, C=-1/2-i`, so forward modulation
is `-1/10-i/5`, dimensionless. Independent positive unequal-energy orthogonal
fields have `SX=2, SY=8, C=0` and valid forward/reverse/correlation zero; phase
is undefined at zero amplitude. Equal energies and zero energy are separate
undefined-helper rejections, not zero-modulation or weak-signal exclusions.
These are report-kernel domain outcomes, not new public estimator tests.

Promoting a reduction accumulator after binary32 multiplication is too late:
`(2^-100)^2` underflows and `(2^100)^2` overflows in float32, whereas promoting
before multiplication resolves both in float64. The conversion witnesses also
retain binary32 minimum subnormal `2^-149`, half-minimum `2^-150 -> 0`, and
overflow `2^128 -> infinity`. Subnormal absolute half-ulp contribution is
`2^-150`; relative normal `gamma(n,u)` reasoning does not cover those products.

The full P5/O3 represented phase designs use uniform, supplied nonuniform and
near-rank phases `j*2^-p`, p=4,12,20 radians. Their exact rational represented
matrix has a declared dyadic solution; right-hand-side rounding is recorded
separately. Actual trig evaluation is binary64 source construction and is not
certified against an exact transcendental phase design. For p=12, float64
condition estimate was `3.6455e15`, residual `1.51e-17`, but forward error about
`0.02495`; rounded float32 storage gave about `0.99990` forward error despite
`3.51e-17` residual. At p=20 represented solves were singular. Uniform and
supplied well-conditioned designs were stable. This supports retaining float64
solve/design metadata and conditioning evidence; it does not accept all designs
or prescribe a condition-number cutoff.

## Discrete search, transfer and CE06 boundaries

Actual public double seed-0/seed-3 searches completed. Input quadratures are
frozen dyadic PCG64(seed) observations, borrowed only as constructibility
inspiration from current public tests; no test module/tolerance is imported.
Both retained one frozen refinement pair and inherited angle-stage x1/amp1 in
magnitude fitting. Their observed coarse top margins were `324.75510947986686`
and `356.83108923654663` in the captured power units. Those baseline diagnostic
margins have **no certified single-precision enclosure**.

Rounding public double overlap captures to complex64 and using a rounded bounded
ramp changed forward-modulation components by up to `9.28463533833579e-9`
(seed0) and `1.2979484955571996e-8` (seed3); phase changes reached about
`7.46e-8` and `1.12e-7` radians. Carrier coordinates remain the actual public
double search values in cycles/um. These probes do not rerun an independent
single search or establish carrier error. Near-tie scalar maxima include exact
zero margin, representable +/-2^-20 margins, and positive 2^-30 erased by
binary32 input conversion. Exact ties retain first-row-major behavior.

Transfer witnesses use rational complex affine radial/full tables and exact
interior/boundary queries. Every requested stencil vertex is checked by the
actual public sampler, including zero-weight vertices. Radial outer-boundary
sampling rejected an unsafe next vertex; successful affine values have exact
rational references. Full-table flat-address behavior must not be replaced by
an assumed per-row boundary rule. `1+2^-30` is a valid nonexact empirical-style
source value but rounds to one when consumed in complex64; declared-OTF inputs
retain the existing stricter complex64-exact schema. Source precision and
consumed precision are distinct.

The corrected camera control produced exactly the declared rational frame sums
and equalization gains in all three runs; the sentinel left background/slope
corner values at one across later frames. A separate nonuniform on/off fixture
completed its selected plane-zero combinations with both literal cell sets
nonempty. D4 cubic controls recovered independent coefficients (0,0,1) for x
and zero y, with maximum coefficient error `9.098774969432121e-15`; full drift
correction remains a double control. Both literal layouts completed native
Z1/dz0 preparation. None is a c64 CE06 workflow.

Valid reciprocal-scaled search witnesses had exact coarse powers 64 at their
declared maxima (observed maximum error `2.842170943040401e-14`), first-row-major
ties, zero/duplicate-coordinate curvature cases, zero objectives and final zero
carriers. Their first-order modulations scaled by 2^660 were exactly 1/16 and
1/8. Their large/tiny coefficients overflow/underflow on c64 conversion, which
disqualifies these inputs for a c64 profile before arithmetic. They establish
constructible double decisions, not single-search success.

Corrected unchanged double full/summary controls completed three fresh runs each.
Image SHA256 was `391c7426a11066baa93b4d814adda5c67015e64e4b135ec8d31b7c28c5a09065`
for all six; carrier and modulation hashes also matched. Retained ndarray
payload was 8,224 bytes full and 424 bytes summary for this tiny known-carrier
workflow. This is compatibility evidence only, not a single-workflow resource
comparison or an independent physical image oracle.

## Finite matrix status and proposal limits

The original 20 rows remain visible below. A measured subset is not relabeled
as completing every originally proposed variant. Missing single runtime values
remain missing. M12/M17 now have actual public double constructibility controls,
with their independent-reference and precision limits stated explicitly.

| Row | Completed evidence / remaining gap |
| --- | --- |
| M01 | Measured exact-root 4/8-point DFT errors; measured actual multidimensional/real-inverse interface dtypes. FFT internals unknown. |
| M02 | Measured prescribed tiny signed sparse band fixture, zero carrier, complex modulation; rational oracle; mixed preweighted and actual public double controls. |
| M03 | Measured signed +/-native-bin carriers and zero modulation; rational signed oracle. |
| M04 | Measured D3/O3 mixed sparse accumulation with unequal gains/noise and cancellation. Distinct nonzero direction carriers not measured. |
| M05 | Measured three exact power-of-two scales; separate product-under/overflow probe. General filtering range not qualified. |
| M06 | Measured exact/near DC cancellation and public double control; exact correlated-rounding acceptance fixture in acceptance-method.md. |
| M07 | Measured full P5/O3 represented uniform/nonuniform/near-rank designs plus exact rational 2x2 subproblems; true transcendental matrix reference not enclosed. |
| M08 | Measured rational unequal positive energies/nonzero complex cross and promoted reductions; helper kernel, not public estimator qualification. |
| M09 | Measured distinct valid C=0, undefined equal-energy and zero-energy kernel domains. No blanket energy floor. |
| M10 | Smaller actual public O3 search anchors Z3/Y3/X4 with frozen overlaps and rounded-capture sensitivity measured. Original sparse Z4/Y8/X8 search witness not run; no complete c64 search. |
| M11 | Measured exact scalar ties/near-tie representation and valid reciprocal-scaled public double tie/zero-curvature controls. Those reciprocal bands cannot convert finitely to c64. |
| M12 | Actual public seed0/3 traces retain angle-to-magnitude inherited state and branch continuations; constructible reciprocal witnesses produce zero objectives/ties. Independent general transcendental objective enclosures missing; single search unqualified. |
| M13 | Measured public radial/full complex affine interpolation, exact rational query values and radial unsafe zero-weight next vertex. Full unsafe/all reflection variants not qualified. |
| M14 | Measured empirical-style non-c64-exact source rounding and exact declared tables. No empirical calibration workflow precision qualification. |
| M15 | Measured both actual literal layouts and native Z1/dz0 double preparation; resource prototype Z1. Full single CE06/2D excluded from #113. |
| M16 | Measured T2/D3/O3 prototype with distinct time noise/modulation. Reuse on/off search policy not measured. Shared-parameter #113 and per-time workflow composition remain distinct. |
| M17 | Corrected actual camera sentinel/equalization, nonuniform on/off and D4 cubic double witnesses. Exact pre-FFT camera sums/cubic coefficients; no independent general off-combined image or c64 drift oracle. |
| M18 | Measured conversion nonfinite/overflow/subnormal and represented singular solve outcomes; proposed record structural validation remains source/proposal only because constructor does not exist. No product rejection/no-partial-result qualification is claimed. |
| M19 | Frozen Y32/Y64 preweighted mixed/double kernel measurements, subject to recorded admission; no workflow workspace proof. |
| M20 | Frozen D1/T2/native2D kernel scaling, subject to recorded admission; no reuse/drift/CE06 runtime claim. |

The proposed initial profile retains binary64 phase design/solve, scalar weights,
geometry and signed image accumulation. New-record binary32 bands are declared
explicitly; old schemas and default/full/summary double calls stay unchanged.
Every field of the proposed constructor is validated independently at creation
and consumption; strided/read-only positives copy into owned read-only storage,
and original-buffer mutation cannot alter the record. These are proposed
requirements, not executed new-record validation tests. No phase/camera history
is fabricated in that schema. T2 noise is per time, while supplied CE04 known
parameters remain shared per call; changed later modulation belongs to explicit
per-time composition, not a hidden T-shaped parameter extension.

The proposed first-slice rounding order is explicit: sample/interpolate original
complex128 transfer values, evaluate scalar numerator/powers/denominator in
complex128/float64, then cast the resulting bounded filter scale once to
complex64 before bulk band multiplication. Retain the c128 source table without
a required c64 H table or whole-volume c128 product. Unit-transfer witnesses do
not independently discriminate alternative orders, so nonunit complex transfer
implementation evidence remains a #113 requirement. Actual zero-weight stencil
validation precedes every requested sample. Rounding H before the denominator
would be a separately declared profile change. No automatic fallback or weaker
double-compatibility tolerance is authorized.

[acceptance-method.md](acceptance-method.md) gives a priori scalar, product,
signed-sum and final-conversion methods and the concrete exact-DC fixture.
General FFT envelopes, all CE04 literal traversal branches, general complex
transfer rounding, full single search and CE06 modes remain explicit downstream
qualification work. SP-EST must independently enclose maxima/brackets and keep
the frozen pair/stale magnitude state; SP-PREP06 must preserve camera anchors,
off plane-zero recurrence, drift and both layouts; SP-WORKFLOW must compose only
accepted modes and measure actual end-to-end peaks. There is no claim that a
CE02-only conversion establishes workflow memory savings.

| Requirement | Evidence / limit |
| --- | --- |
| R1 | Exact rational/root references, separate representation/reference/candidate/baseline errors; acceptance-method.md; unqualified FFT/search terms explicit. |
| R2 | Contract dtype/opt-in/compatibility/failure policy plus actual promotion/reduction probes; proposed precision has no active runtime. |
| R3 | Complete coefficient/slot/noise/alpha declarations and new-record schema; implementation/validation deferred to separate #113 high-risk intake. |
| R4 | Frozen scripts/manifests, raw repeated Ubuntu runs and resource admission; prototype/full-workflow distinction retained. |
| R5 | Contract stages SP-PREP02/PREP06/EST/TRANSFER/WORKFLOW with mode-specific gaps/dependencies; no implied early workflow qualification. |
| R6 | Author artifacts ready for fresh scientific review; no self-verdict or runtime D/readiness claim. Root owns exact-candidate gate. |

| Scenario | Evidence / classification |
| --- | --- |
| S01 | No runtime edit; existing public double controls and corrected full/summary identity; proposal only. |
| S02 | Instrumented c64 spectrum/inverse/ramp/product versus f64 accumulator/f32 result; preweighted kernel only. |
| S03 | Frozen exact dyadic x0/x32 and separate M14 nonexact conversion. |
| S04 | M01 exact normalization/sign references plus actual-interface dtype probes; workspace unknown. |
| S05 | M04/M07/M08 promoted arithmetic; independent scalar/recombination supplement. |
| S06 | Signed M02/M03/M06 rational intervals and absolute/condition-scaled metrics. |
| S07 | Exact M08 modulation and diagnostic search component/amplitude/phase changes; no single carrier-error result. |
| S08 | M05 range plus explicit subnormal/overflow probes and stage failure policy. |
| S09 | Full represented P5/O3 and rational subproblem conditioning/residual/forward-error distinction. |
| S10 | Unequal positive/C0 valid versus equal/zero-energy undefined domains. |
| S11 | Actual public frozen-overlap/stale-state traces; full single lifecycle unqualified. |
| S12 | Exact scalar margin/ties and reciprocal double zero-objective witnesses; no epsilon rule; general single margins unresolved. |
| S13 | Exact affine radial/full sampler controls and actual unsafe radial stencil; full variant qualification missing. |
| S14 | Separate empirical-style c128 rounding and c64-exact declarations; empirical workflow unqualified. |
| S15 | Complete proposed schema/fixture; new constructor has no runtime validation evidence. |
| S16 | Existing source boundaries unchanged; new ownership/copy/revalidation is proposal only. |
| S17 | #113 stationary3D only; measured double CE06 boundary controls do not expand it. |
| S18 | Explicit stage failures/domain distinctions, retained negative attempts; no new product no-partial-result evidence. |
| S19 | Finite raw logs/repetitions/dtypes/RSS/time/identities with every measured subset/gap retained. |
| S20 | Fresh admission and logical payload including f64 accumulator/f32 result; no workstation extrapolation. |
| S21 | Concrete contract stage dependencies and unresolved acceptance obligations. |
| S22 | Fresh independent scientific review outstanding at author handoff; full gate separate. |

## Resource observations and admission

The largest planned geometry was Y64/X64, never a workstation-sized allocation.
Before each of five resource geometries, a fresh Ubuntu preflight recorded host
MemAvailable, cgroup current/max/swap, CPU and thread controls. A 512 MiB host and
cgroup headroom guard was a conservative scheduling guard, not a scientific
input-size cap. The first post-correction observation had cgroup
838,496,256 / 17,179,869,184 bytes, no current swap, host MemAvailable
17,864,040,448 bytes and all five requested thread variables one. The previous
small-run maximum whole-process RSS was 82,317,312 bytes. The five actual
[admission files](raw/admission_M19-spatial64.json) preserve fresh values for
each geometry; all guards passed. The container swap limit says `max`; host
SwapTotal was zero. These are distinct observations.

At Y64/X64, predicted simultaneously live **mixed logical arrays** were caller
1,013,760 + filtered snapshot1,013,760 + accumulator524,288 + final262,144 +
three complex64 workspaces1,572,864 + ramp1,024 = **4,387,840 bytes**.
The matched double prediction was 8,251,392 bytes. This named-array coexistence
model is not a hard peak bound: Python assignment can temporarily retain an old
and new spectrum/spatial/product, and the weighted real term is a temporary.
Adding one complex output buffer and one real output buffer as a conservative
source-level allowance gives 4,912,128 mixed and 9,299,968 double bytes. This is a
post-run accounting refinement, not a new measurement or changed allocation.
Import/reference/observer/
Python/backend costs are additional. The prediction deliberately counts the
f64 accumulator and f32 final image together; result payload below excludes
freed workspaces. Backend private allocations remain unknown.

All 30 resource processes completed: five geometries, two profiles, three fresh
runs each. [kernel-summary.json](kernel-summary.json) retains exact min/median/
max, pre-call/call-end native RSS, payload and rational-reference error metrics.
The table reports **preweighted prototype kernels**, with the earlier scalar/
recombination limits attached. Seconds include their timed rational scalar
construction, sparse assembly and FFT; they are not isolated FFT or runtime
workflow timings.

| Geometry | Profile | Caller+result ndarray bytes | Whole peak bytes: median [min,max] | Seconds: median [min,max] |
| --- | --- | ---: | ---: | ---: |
| M19 Y32 | mixed | 587776 | 63172608 [63004672,63291392] | .013501 [.010692,.016890] |
| M19 Y32 | double prototype | 1175552 | 63893504 [63856640,63926272] | .013958 [.011633,.026042] |
| M19 Y64 | mixed | 2289664 | 65921024 [65810432,66015232] | .022045 [.015701,.022914] |
| M19 Y64 | double prototype | 4579328 | 68984832 [68771840,69074944] | .020876 [.020233,.037684] |
| M20 D1/Y32 | mixed | 239616 | 62754816 [62689280,63111168] | .003786 [.003135,.004150] |
| M20 D1/Y32 | double prototype | 479232 | 63053824 [62988288,63578112] | .004505 [.003442,.005409] |
| M20 T2/Y32 | mixed | 1175552 | 63590400 [63234048,63963136] | .018100 [.017775,.028878] |
| M20 T2/Y32 | double prototype | 2351104 | 65417216 [64860160,65548288] | .020183 [.019948,.023348] |
| M20 Z1/Y32 | mixed | 146944 | 62423040 [62009344,62697472] | .007967 [.007591,.008905] |
| M20 Z1/Y32 | double prototype | 293888 | 62574592 [62410752,62640128] | .008747 [.008000,.009237] |

Largest matched peaks have disjoint observed ranges and mixed retained payload
is half for these fields, but the byte difference is a small prototype result.
Other small-case RSS ranges overlap. No universal speed ratio or claimed
workspace attribution follows. Spatially repeated sparse signals explain why
Y32/Y64 max absolute errors are both 1.2548346268503289e-8 for mixed and
3.7981314000334304e-17 for double; they do not characterize arbitrary dense
spectra. No actual single workflow exists, and these results prove no 16 GiB
readiness. Source/representation bounds are baseline-scoped; any independently
accepted later size-domain contract must be rechecked by #113 rather than
restoring old limits as an intrinsic float32 constraint.

A separate narrow pinned provenance probe verified imported NumPy
`numpy.fft._pocketfft`/compiled `_pocketfft_umath` and SciPy
`scipy.fft._basic_backend`/`_duccfft` module paths/hashes. SciPy's loaded helper
SHA256 is `0d9c409a6dcf9cdb85cbc67aa203f7b80907036b23735f1fdceb7af1268ee9c5`.
The complete [backend provenance](raw/backend-provenance.json) identifies these
actual installations; it does not infer NumPy internals from SciPy or prove
private accumulation/workspace precision.

## Attempts, corrections and reproducibility

[run-ledger.tsv](run-ledger.tsv) contains **184 JSON workload attempts**:
168 completed and 16 failed. [run-summary.json](run-summary.json) groups actual
revisions separately and retains timing/RSS median and range, including failed
attempts. One additional missing-script launch exited2 without a workload JSON.
There were five manifest-freeze processes, seven environment/admission processes
and one narrow backend provenance process: **198 Docker interpreter invocations**
in this role's bounded study, with no uncontrolled retries. This is process
accounting, not model-token accounting or a human budget. The original 126
planned v1 workload processes all completed. Original supplement attempted35
of36 before coordinator revocation; original workflow-summary repetition3 stays
unattempted. No later correction is relabeled as that missing repetition.

| Attempt/revision | Observation and diagnosed handling |
| --- | --- |
| Preweighted v1,126 workloads | All completed; coordinator diagnosed exact-reference scalar and reference-derived opposite snapshot. Claims narrowed permanently to preweighted FFT/assembly plus snapshot payload. Separate scalar/recombination observer supplied; numerical source/manifest unchanged. |
| Supplement v1,35 workloads | 21 completed; camera3 rejected boolean selectors, cubic3 lacked required header phase metadata, search-tie3 rejected zero coarse carrier, full3/summary2 rejected incomplete transfer identity. These14 are retained fixture/probe failures, not product-red. Transfer unsafe-stencil and singular-design outcomes inside completed probes are intentional domain observations. |
| Window revocation | Already-started bounded child finished; launcher11266 stopped then killed/reaped exit137. Child summary2 JSON complete but shell status not appended. Summary3 never launched. No numerical timeout/OOM occurred. Window returned to root, then explicitly regranted before corrections. |
| Corrections v1,7 workloads | Scalar/recombination3 and camera3 completed. First nonuniform off combination rejected empty outside mask at dxy1; runner stopped on JSON failure. Literal integer truncation analysis identified geometry defect. |
| V2 launch typo,1 launch | Mechanical runner substitution addressed nonexistent `corrections-v2_v2.py`; exit2, no candidate executed. Empty stdout preserved as `.launch-failed.empty`, stderr retained. Corrected runner uses fresh `corrections-v2-fixed_` output names. |
| Corrections v2,10 workloads | dxy changed only for off-combination to .25, with both literal cell sets nonempty. Off3/cubic3/valid reciprocal ties3 completed. First workflow numerical call completed but extraction raised AttributeError: full result stores parameters in `.parameters`, summary has top-level fields. Runner stopped; no product defect inferred. |
| Corrections v3,6 workloads | Only workflow observer extraction changed to actual record schemas. Full3/summary3 completed with exact equal image/carrier/modulation hashes. |

Correction dependency mapping: v1→v2 changes only the off-combination sampling
argument plus version/manifest/case-selection bookkeeping; scalar/camera/cubic/
tie/workflow function bodies otherwise remain byte-identical. V2→v3 changes only
workflow parameter-field extraction plus version/manifest/case selection. Fresh
independent review decides applicability of retained earlier evidence. No runtime,
product test, fixture, dependency, discovery, coverage or delivery policy changed.
Original scripts/manifests and raw failed attempts stay available. The initial
runner snapshot `revisions/preweighted-v1/run-initial.sh` is reconstructed from
the executed shell source after resource admission/JSON guards were added; there
was no contemporaneous initial-runner hash. Every expanded workload command is
still literal in commands.log. The numerical `study.py` bytes never changed.

Historical shell runners write fixed raw paths. **Do not rerun them over retained
evidence.** For independent replay, use a fresh scratch destination and the run
mode directly, reading the existing frozen manifest:

```sh
mkdir -p work/precision-112/study-author/replay
# Run only in a coordinator-granted numerical window.
docker exec --user 1000:1000 -w /workspace/work/issue-112 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 \
  -e NUMEXPR_NUM_THREADS=1 -e VECLIB_MAXIMUM_THREADS=1 \
  simrecon-campaign-ubuntu .venv/bin/python \
  docs/reports/single-precision-study/study.py run \
  --case M02-signed --profile mixed --repeat 1 \
  > work/precision-112/study-author/replay/M02-new.json
```

Other run modes use `supplement.py`, `corrections.py`, `corrections_v2.py` and
`corrections_v3.py` with their frozen case lists and `--case/--repeat`; they emit
JSON stdout. Freeze modes mutate their named manifests and are not required for
replay. Snapshot copies under revisions are byte evidence; original active paths
remain the reproducible import layout. No original run is retagged to a later
commit, script or corrected manifest.

The study author had one role launch and did not delegate. Requested/exposed
model selection and launch IDs belong to the coordinator ledger; actual serving
identity, tokens, cached tokens, monetary cost and separate model/owner-wait
elapsed time are unknown. No human numeric accuracy/review/time budget was set.
This role used only the pinned Ubuntu interpreter for scientific observations.
Source reading/current public fixture inspiration was nonblind and disclosed;
no ignored legacy/private ancestry or unrelated lessons were read. Prompt
restrictions do not prove engineered filesystem isolation or memory disabling.

Own scratch is `work/precision-112/study-author/`: `small-summary.json`,
`artifact-check.log` and `whitespace-check.log`; Python
created report-directory `__pycache__` files. Durable report/manifests/raw are
needed reviewer inputs. No owned live/stopped numerical process or launcher
remained when the exclusive window was released; the killed launcher left an
inert orphan timeout zombie at that observation. Root owns eventual disposable
scratch/cache housekeeping. No commit, push, external message or full verification
was performed by this role. Scientific review and root's exact-candidate
full-local Ubuntu gate remain separate next steps.

Post-study integration: the coordinator advanced this checkout to
`64a752b4642709c539df2079cc3c906acf4cc7b8` before scientific review. Static
`git diff --name-only b344e41a8b52de76d7cbbf8450319893904c3b8f..HEAD --
src/simrecon AGENTS.md docs/PROJECT.md Makefile pyproject.toml uv.lock` returned
no paths. The 11 added/changed paths concern setup/recovery records/tooling,
including appended role-launch recovery guidance, which this author read.
This does not retag or rerun the b344 trials. The independent reviewer must
assess applicability on the new documentation base; root owns the later exact
candidate verification identity outside these tracked bytes.

The derived TSV has a header naming artifact, manifest, case, profile,
repetition, status, seconds, whole-process peak bytes, exception type and
message. Its 184 data rows preserve every workload outcome; absent exception/
message fields use `not-applicable` rather than trailing empty fields. This
formatting correction changes no frozen raw observation. Final author checks
are narrow static/artifact checks, not product-gate evidence. Durable evidence
occupies about 6.6 MiB at handoff; this disk-size observation is rounded and is
not a scientific resource budget.
