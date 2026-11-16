# SP112: single-precision reconstruction study proposal

**Version 1.0. Proposed scientific decisions, not an activated runtime contract.**
Issue [#112](https://github.com/david-hoffman/simrecon/issues/112) requests
characterization, numerical acceptance methods and a finite implementation plan.
The [task](../tasks/single-precision-study.md) is the sole execution state. This
The [study report](../reports/single-precision-study/report.md) records bounded
experiments, raw attempts and the limits of each measured operation. No single
runtime is implemented or qualified. Independent scientific review must precede
acceptance of this proposal; later implementation requires its own high-risk intake.

## Existing boundary and purpose

The public-main baseline is `b344e41a8b52de76d7cbbf8450319893904c3b8f`.
[CE02](c-equivalence-preprocessing-v1.md),
[CE03](c-equivalence-optical-transfer-v1.md),
[CE04](c-equivalence-known-parameters-v1.md),
[CE05](c-equivalence-carrier-modulation-v1.md),
[CE06](c-equivalence-acquisition-modes-v1.md) and
[CE07](c-equivalence-workflow-v1.md) define the selected scientific mapping.
[RM84](reconstruction-memory-v1.md) preserves float64/complex128 and exact
same-environment values for summary/full-debug compatibility. That requirement
continues for existing calls. Retired scientific contracts and memory studies
are historical context, not acceptance criteria for this study.

The desired new path would use float32/complex64 bulk computation, with explicit
mixed precision where justified. A returned-array downcast alone is insufficient.
The 16 GiB workstation is a feasibility objective, with caller/operating-system
headroom still to measure. No peak-memory ceiling, speed ratio, image-error
threshold, carrier-error threshold or human execution budget has been selected.
This study must not manufacture one or claim physical recovery qualification.

## 1. Proposed dtype and compatibility policy

The following is a candidate to assess, not permission to change existing APIs.
`single-mixed-v1` is a proposed opt-in profile name. Existing default calls remain
double, including both summary and full-debug entries. No automatic fallback,
silent lower precision, inferred selection from raw dtype or default migration.

| Boundary | Existing baseline | Proposed single-mixed-v1 | Required evidence / unresolved choice |
| --- | --- | --- | --- |
| Input storage | Retain caller dtype, validate original values | Same; copy/convert only after structural and original-value validation | Separate source-to-f32 conversion error from arithmetic error; existing float32-exact camera domain remains unless separately amended |
| Camera-corrected frames, real bulk workspaces | float64 | float32 | Range and cancellation witnesses; persistent camera state is separately qualified in CE06 task |
| Separated bands, overlap buffers, padded spectra | complex128 | complex64 | Actual intermediate dtypes and memory; no hidden full complex128 copy |
| Forward/inverse FFT input and output | float64/complex128 | float32/complex64 | Probe both NumPy and SciPy used interfaces, axes, norm and shape; output dtype alone proves no internal accumulator dtype |
| Band products and filtering | complex128 | complex64 bulk, binary64 scalar weights and denominators | Assess multiplication rounding and scalar-to-array promotion explicitly |
| Image accumulation across signed orders/directions | float64 | float64 accumulator initially; float32 final image | Explicit mixed precision cost retained in memory model; assess f32 accumulation as a distinct future alternative, never silently switch |
| Spectral energies, cross products, frame sums | float64/complex128 reductions | float64/complex128 accumulation, promoting before square/product | `sum(dtype=...)` alone does not prevent f32 product underflow/overflow; avoid a whole-volume promoted temporary through bounded reductions |
| Coordinates, carrier queries, fitted scalars, phases, geometry | float64/complex128 | float64/complex128 | Preserve sampling/index decisions and fitted-parameter information; no promise of bitwise identical fits |
| Phase design / small linear solve | float64 | float64 solve, float64 matrix/noise metadata; apply to float32 frames with explicit result policy | Condition/residual/backward-error evidence; solve precision is independent of bulk storage |
| Transfer storage / sampling | complex128 | Existing source complex128 retained; sample/query/interpolation and scalar filter powers/numerator/denominator complex128/float64; cast the resulting bounded filter scale once to complex64 before band multiplication | Empirical values need not be c64-exact; quantify scale conversion separately; no whole-table forced downcast or required c64 H table |
| Prepared/returned records | Existing schemas require f64/c128 | New profile-specific records; image f32, bulk diagnostics c64, coordinates/noise/scalars f64/c128, integer cutoffs unchanged | Exact field/provenance schema belongs to each implementation intake; first slice below is concrete |

Use original CE scaling, signed images and prescribed operation order. No magnitude,
clipping, positivity projection, transfer normalization, new optimizer or extra
convergence epsilon is proposed. Underflow is measured, including subnormal/zero
transitions; it is not assumed harmless. Overflow/nonfinite/undefined intermediate,
singular solve or unsafe stencil yields the operation's domain failure with cause
and stage context. No partial result and no caller mutation. A lower-precision
failure on a baseline-valid input must be reported explicitly; qualification may
select a narrower opt-in domain only through later intake, with paired valid
cases and documented reasons. No arbitrary weak-signal exclusion is authorized.

Proposed #113 selection is an explicit `precision="single-mixed-v1"` keyword
on `reconstruct_known`, with omitted/default selection preserving existing
double calls and behavior. No signature changes occur during this issue.
A future workflow intake chooses its exact public signature. Provenance must identify requested
and resolved profile, every storage/compute/reduction/result dtype, FFT interface
and backend/version, mapping revision, transfer conversion, source input identities
and any precision failure. It must distinguish original bytes from converted
values. Claims about internal FFT workspaces remain unknown unless observed or
documented by the pinned backend.

## 2. Independent numerical acceptance methods

For each witness, define exact input data first. Let `x0` denote the declared
mathematical input, `x32` its precisely specified binary32 representation, and
`F` the CE mathematical finite procedure. Report separately:

1. Input representation: `F(x32)-F(x0)` where both are defined.
2. Candidate arithmetic: `candidate(x32)-F(x32)`.
3. Double reference arithmetic: `double(x32)-F(x32)`.
4. End-to-end change: `candidate(x32)-double(x0)` as a compatibility observation.

Agreement of the last pair alone is never scientific acceptance. If `x0` or the
finite procedure is undefined, do not assign a reference value. Arbitrary input
rounding that changes a decision is reported as representation sensitivity.

Independently construct sparse Fourier witnesses from rational coefficients,
signed constants and commensurate carrier bins. Tiny direct DFT sums use exact
roots of unity where possible (size 2/4), otherwise independent interval sine/
cosine evaluation with documented series remainder. Scalar filtering, complex
transfer interpolation and assembly follow contract equations, never production
helpers. For transcendental witnesses use Python standard-library Decimal or an
already-locked adequate-precision method; no new dependency. Decimal precision
doubled from 80 to 160 digits is a stability check, not a certified bound by
itself: give outward rounding/error envelopes and analytic series tails. Freeze
oracle formulas/constants and generated input hashes before candidate trials.

For a reference enclosure `[l,u]`, report its width as reference uncertainty;
candidate distance is `max(l-c,0,c-u)` componentwise, plus an upper error bound
using the far endpoint. Reject an unresolved oracle instead of rounding it to
double and declaring agreement. Signed-image metrics include maximum absolute
error, RMS, error relative to a nonzero declared signal scale, and signed extrema;
do not divide by each pixel or conceal negative/near-zero values in relative error.
Report carriers in cycles/um and modulation complex-component error, amplitude
and phase (phase undefined at zero amplitude). Physical reconstruction accuracy
under noise/model mismatch remains a different question from this procedure.

Derive stage error envelopes using `u32=2^-24`, `u64=2^-53` and
`gamma(n,u)=n*u/(1-n*u)` only when `n*u<1` and the assumed operations are finite
normal arithmetic. For a sum use `gamma(n,u)*sum(abs(terms))`, with separate
product/conversion error; for cancellation report both absolute envelope and
condition measure `sum(abs(terms))/abs(sum(terms))`. Include explicit subnormal
absolute-rounding contributions and detect possible overflow. These expressions
do not certify undocumented FFT internals. FFT results require independent tiny
DFT checks and observed errors at the finite matrix sizes; do not extrapolate
a measured multiplier as a universal theorem. For a phase solve report matrix
condition estimate, normalized residual and an independent inverse/solution for
small analytic designs. A small residual alone is insufficient for ill-conditioned
forward accuracy. No blanket image/carrier tolerance is selected here.

Discrete comparisons have their own acceptance rule. Independently enclose both
sides: a strict `a>b` decision is certified true only if `lower(a)>upper(b)`, and
false if `upper(a)<=lower(b)`. Otherwise it is unresolved at that precision.
An exact analytic tie follows the existing first-row-major maximum / strict-else
rule, not an epsilon tie rule. Cover maxima, angle/magnitude bracket continuations,
zero curvature, floor/ceil/trunc, strict support inclusion and interpolation stencil
addresses. Report margin and error-envelope width at every decision. Frozen-overlap
search must retain the same pair through refinement and preserve stale angle-stage
state in magnitude fitting. Near-tie instability can disqualify a proposed mode;
it cannot authorize changing the CE search. A study outcome may be “do not yet
qualify search in single precision.”

Failure oracles are mathematical domains: positive unequal spectral energies,
defined divisors, full finite intermediates, rank, representable extents and safe
actual stencils (including zero-weight vertices). Test exact equal-energy, zero
energy, zero cross-correlation with unequal positive energies, unsafe sampling,
nonfinite conversion and overflow separately. Preserve permitted zero carrier /
zero or signed modulation for known reconstruction. No energy floor substitutes
for these distinctions.

## 3. Finite representative matrix and bounded measurements

This is a finite characterization design, not the supported runtime domain or
a Cartesian product. Each case has frozen analytic generator/declarations and
an independently stated expected result/decision before any candidate comparison.
Case labels are coverage examples for the scenario ledger in the task.

| Case | Fixture and smallest declared dimensions | Principal evidence |
| --- | --- | --- |
| M01 | Direct real/complex DFT, lengths 4 and 8; axes/norm used by NumPy/SciPy | Actual dtype transitions, transform normalization and oracle error |
| M02 | Prepared 3D T1 D1 P3 O2 Z2 Y4 X4; signed DC plus one conjugate frequency pair, zero carrier, nonzero complex modulation | Signed image and absolute scale; permitted zero carrier |
| M03 | Same, signed carrier one native bin and separate zero modulation case | Relocation/sign, zero-side positive case |
| M04 | T1 D3 P5 O3 Z4 Y8 X8, distinct directions and unequal complex order gains | Cross-direction cancellation and prescribed accumulation |
| M05 | M02 scaled by exact powers of two: 2^-100, 1, 2^100, with bounded reference algebra | Range/normalization; explicit product underflow/overflow assessment |
| M06 | M02 coefficients +1 and -(1-2^-20), then exact cancellation | Absolute error with small/zero expected signed samples |
| M07 | Uniform P5 O3 and supplied nonuniform P5 O3 phase designs; near-rank design separation parameter 2^-4, 2^-12, 2^-20 radians | Solve conditioning and representation sensitivity; no assumed acceptance of all designs |
| M08 | Analytic overlap fields X,Y with rational unequal energies and nonzero complex cross term | Energy/cross reduction and modulation oracle |
| M09 | Positive unequal-energy orthogonal fields; exact equal-energy and zero-energy variants | Permitted C=0 versus distinct undefined helper rejections |
| M10 | Sparse 3D O3 search, T1 D1 Z4 Y8 X8 with isolated row-major coarse maximum | Frozen-overlap search, carrier/modulation oracle and decision margins |
| M11 | Exact tied coarse maxima, zero curvature and representable near-tie perturbations ±2^-20 | Strict tie behavior, sensitive/rejected qualification outcomes |
| M12 | Analytic search objective bracket giving initial tie, positive/else continuations and inherited magnitude bracket state, from an actual constructible band pair | Trace/branch procedure; if public witness cannot be constructed, record missing evidence rather than a helper-only substitute |
| M13 | Radial and full complex affine transfer tables with rational nodes; interior, boundary and actual unsafe stencil queries | Exact interpolation, strict safety and query rounding |
| M14 | Empirical-style c128 samples containing `1+2^-30`, plus declared c64-exact table | Source-to-consumed conversion error and distinction between source schemas |
| M15 | Native 2D T1 D1 P3 O2 Z1 Y8 X8; dz=0 allowed; two literal layout declarations | CE06 downstream needs; characterization only, not #113 support |
| M16 | T2 D3 P5 O3 Z4 Y8 X8 with later modulation changed; carrier reuse on/off | Time-specific parameters, noise and provenance |
| M17 | Small CE06 camera sentinel, equalization anchor, on/off combination and D4 cubic-drift witnesses, separately generated | Workflow-only state and reduction risks; do not claim a CE02 optimization covers these |
| M18 | Shape-only invalid metadata/extents and finite/nonfinite/overflow/singular variants | Rejection, validation-before-allocation, no partial result |
| M19 | Prepared known 3D T1 D3 P5 O3 Z4 Y32 X32, L2 A1; same geometry Y64 X64 | Fresh-process dtype/error/retained bytes/RSS/timing, spatial scaling |
| M20 | M19 central Y32 X32 at D1, then T2 D3, plus native 2D Z1 | Direction/time/2D scaling, no workstation extrapolation |

M12/M17 are constructibility obligations, not a claim that constants are already
qualified. Freeze their complete parameters before running them. If no valid
finite public witness results, document the gap and exclude the corresponding
mode from proposed qualification. A resource stop or timeout is incomplete
evidence, never a successful finite search or a numeric rejection.

The coordinator grants the actual shared environment/resource window. Until then
no installs, probes, tests or experiments. Required platform is Ubuntu 24.04 per
[PROJECT](../PROJECT.md#required-verification-platform); actual Python/NumPy/SciPy,
uv, wheel/backend/allocator/thread versions must be observed, not inferred from
the issue's tiny NumPy 2.5.3/SciPy 1.18.1 FFT observation. Use locked dependencies;
no backend swap during a comparison. Set supported BLAS/OMP numerical threads to
one and report effective controls, host/container/cgroup memory, CPU, swap and
shared-workload interference. Missing attribution remains unknown.

Measurements start with M01–M03, then small numerical matrix, then M19/M20 only
after prerequisite success and coordinator headroom review. Precompute logical
array payloads for declared extents and record expected concurrent arrays; include
caller-retained inputs, oracle allocations and full-debug retention. No 16 GiB
volume or unbounded growth experiment. The finite largest spatial sample above
is Y64 X64; a later size increase needs an explicit amended experiment plan and
resource grant, not an invented scientific domain cap.

For each comparison use three fresh single-workload processes, fixed synthetic
seed (if any), identical declarations and retained caller inputs; include every
failure. Report raw runs, median and range, call-only monotonic seconds and whole
process peak RSS. On Linux retain native `ru_maxrss` KiB and multiply by 1024;
report pre-call high-water and raw peak, never label their difference a pure
algorithm peak. Report owned reachable array payload with shared backing counted
once and metadata limitations. Record input/result dtypes and instrumented stage
transitions, conversion/copy points, input hashes, generator/oracle revision,
commit/tree/dirty state, lock hash, process command, environment and limits.
Unknown backend workspace is part of observed RSS, without attribution to a
particular allocation. Timing is descriptive; shared-host noise and small case
scale preclude a universal speed ratio.

Compare existing double full/summary behavior as compatibility controls. Since
this issue changes no runtime, standalone single arithmetic prototypes characterize
operations only; they must be labeled prototypes and cannot establish end-to-end
single workflow memory, timing, branch correctness or implementation readiness.
State exactly which matrix rows are measured, analytic-only, blocked or omitted.
Preserve reproducible commands/formulas and raw measurements in durable report
artifacts. A missing single runtime result must remain missing.

## 4. Independently constructible first-slice record / fixture proposal

The first downstream slice is [#113](https://github.com/david-hoffman/simrecon/issues/113).
Propose new root-facade exports `declare_prepared_bands32`, `PreparedBands32`,
`KnownReconstruction32`, and explicit `precision="single-mixed-v1"` selection
on `reconstruct_known`. Names/signatures are proposed
interfaces for its intake; none becomes available in #112. This deliberately
does not reuse/downcast an existing dataclass or require unfinished preparation.

Proposed constructor:

```python
declare_prepared_bands32(
    quadratures, noise_variance_factors, *, input_shape,
    dxy_um, dz_um, lateral_zoom, axial_zoom,
    mapping_revision="ce04-svn307-v1", provenance=(),
) -> PreparedBands32
```

The frozen record has exactly `quadratures`, `noise_variance_factors`,
`input_shape`, `input_scale`, `dxy_um`, `dz_um`, `lateral_zoom`, `axial_zoom`,
`mapping_revision`, `precision_profile`, `provenance`. Constructor outputs
independent C-contiguous owned read-only arrays: complex64 quadratures
`(T,D,Q,Z,Y,X//2+1)`, float64 noise `(T,D,O)`. No broadcast is implicit.
Both inputs must be ordinary NumPy arrays of exactly these native dtypes;
read-only/strided inputs are copied and accepted. Reject bool/object, subclass,
wrong byte order/dtype/shape or nonfinite values before numerical work. The
constructor never silently rounds complex128 bands. A caller explicitly creates
binary32 bands, and records that conversion in its fixture provenance. Noise is
strictly positive; quadratures may be zero/signed/complex and need not satisfy
a physical-real symmetry beyond the inherited reconstruction mapping.

`input_shape` is a tuple of six nonboolean Python integers `(T,D,P,Z,Y,X)` with
T,D>=1, Z>=2, Y>=1 and even X>=2. Q is odd, Q<=P and O=(Q+1)//2>=2.
Lateral and axial zoom are positive nonboolean Python integers; retain exact
float32 representability of lateral zoom and all inherited signed32/unsigned32/
native-intp extent/address limits. dxy/dz are finite positive nonboolean real
scalars within the inherited component magnitude domain, converted to binary64.
Compute `input_scale=1/(X*Y*Z*L**2*A*D)` in binary64 in the constructor; require
finite positive result. It is not caller-supplied, guessed from band amplitudes
or recomputed with float32. `precision_profile` is exactly `single-mixed-v1`;
`mapping_revision` is exactly `ce04-svn307-v1`, referring to the CE04 equations
and source identities above, not an assertion of raw acquisition lineage.
`provenance` is an immutable tuple of `(nonempty str, str)` pairs with unique
keys, supplied by the caller and preserved; no large arrays/opaque objects.
It describes fixture/formula/input identity and cannot authenticate its truth.

Downstream consumer revalidates every field, including provenance shape/types,
computed scale, array dtype/shape/ownership/read-only state, finite values,
metadata and representation bounds. Directly constructing the dataclass does
not bypass validation. No phase matrices, phase angles, frame histories,
camera maps, sentinel records, off/drift traces or unused diagnostics exist in
this new schema. There are therefore no discarded fields to validate and no
fabricated preparation history. Actual transfer stencils and operation-time
failures are still checked at use. Consumer never mutates inputs; mutation after
construction of original buffers has no effect. Concurrency guarantees are
unchanged; no shared writable state is introduced.

Independent fixtures construct tiny quadratures directly from the sparse
Fourier formulas in M02–M06, with every half-spectrum coefficient and slot
0,E1,O1,... specified, and independent positive rational per-time noise. They
specify unnormalized negative-sign forward-sum units and CE alpha explicitly;
do not obtain expected arrays by calling preparation, importing private helpers,
or downcasting production results. Include a second fixture with T2 distinct
noise to prove time indexing. The record provides declared mathematical band
inputs; it does not certify that raw camera data produces those bands.

Existing `PreparedBands` stays complex128 with noise `(D,O)` and its original
diagnostics/source tuple. Existing `AcquisitionBands` stays complex128 with
noise `(T,D,O)`. Existing consumers continue rejecting c64 masquerading as those
records. No implicit adapter/coercion broadens old APIs. An optional explicit
future adapter would need its own source-field validation, conversion-error,
ownership and provenance contract. #113 initially accepts only the new record,
existing validated OpticalTransfer and CE04's stationary 3D known-parameter
options. It does not add 2D, CE06 drift/off/layout, parameter search or workflow.

Proposed `KnownReconstruction32` mirrors CE04 fields in the same order, using
float32 signed image and complex64 filtered quadratures; coordinates/carriers
are float64, modulation complex128, axial cutoffs integer, immutable settings
and read-only independently owned output arrays. Append `precision_profile`
and `precision_provenance` (ordered immutable pairs identifying the table in
section 1 and mapping/backend information). Preserve supplied parameters at
their binary64/complex128 values. #113 intake must freeze exact settings keys,
error class/category, public signature, finite failure precedence and high-risk
test checkpoint before implementation. This study supplies no product test code.

## 5. Separately intakeable implementation stages

| Task | Public outcome and interface boundary | Prerequisite / independent acceptance |
| --- | --- | --- |
| SP113 / existing #113 | Declare narrow PreparedBands32 and opt-in `reconstruct_known(..., precision="single-mixed-v1")` for stationary 3D bands; genuine c64 FFT/filter work, f64 image accumulator, f32 result; exact new-record validation above | Accepted #112 proposal; separate high-risk intake, fresh blind A/B frozen fixtures/oracles, restricted C, fresh D and full gate |
| SP-PREP02 | Optional CE02-only float32 frame/phase preparation returning the new record with f64 solve/noise | SP113 schema; numerical range/solve study; explicitly a direct-stage improvement, no workflow-memory claim |
| SP-PREP06 | Workflow-facing CE06 preparation for native 2D/3D, persistent camera/sentinel state, equalization, off combinations, supplied/linked phases, drift and both literal layouts | Accepted precision schema plus CE06 mode-by-mode matrix; output noise `(T,D,O)` and compact/full capture ownership; preserve state across staging |
| SP-EST | CE05 overlap/search/modulation with c64 overlaps and promoted reductions; new parameter/trace record policy | Independent margin/oracle evidence for known fit and search separately; freeze literal maxima/brackets/overlap lifecycle; search may remain double pending qualification |
| SP-TRANSFER | Mixed transfer consumption and empirical calibration policy; original c128 source retained, f64 queries/interpolation, bounded c64 consumed blocks | Preserve CE03 source/safety domains, empirical precision and actual zero-weight stencil checks; state calibration-storage precision separately |
| SP-WORKFLOW | Explicit opt-in workflow/summary integration and profile provenance; compose only qualified stage modes | SP113, required SP-PREP06/SP-EST/SP-TRANSFER contracts accepted; end-to-end signed outputs/decisions/error/peak evidence; default/full-debug compatibility independent controls |

Each task has its own scenarios, fixtures, named files, baseline, high-risk
A/B/C/D, full-local Ubuntu gate and cumulative accounting. Dependent work waits
for accepted prerequisite interfaces. Unqualified stage/mode selections must be
explicitly rejected by the new opt-in entry or deliberately remain double under
a separately declared mixed profile; do not silently present them as single.
No default migration follows from these tasks. Proposed default migration,
workstation-scale feasibility or physical-recovery requirements need separate
evidence and intake. Independent size-domain/half-precision studies are not
prerequisites and inherit no claims from this study.

## 6. Acceptance and unresolved scientific decisions

Representation limits here are inherited from the identified public baseline,
not intrinsic binary32 limits. This issue changes none. If an independently
accepted size-domain change such as #115 precedes #113, that intake rechecks the
then-current approved representation contract rather than restoring superseded
bounds from this characterization.

Issue checkbox mapping: numerical acceptance methods are section 2; dtype,
supported modes, failures and compatibility are sections 1/4/5; independently
constructible first-slice fixtures are section 4; bounded reproducible actual
measurements are section 3 plus the completed finite report; separately intakeable
CE06/estimation/transfer/summary tasks are section 5; independent scientific
review is required before study acceptance. An experiment plan alone does not
satisfy the actual-measurements checkbox.

The report measures finite FFT interfaces/errors, sparse mixed storage/peaks,
scalar/reduction/conditioning risks, public search sensitivity and constructible
M12/M17 double controls. The proposed first mode is stationary 3D known-parameter
intake; search, CE06 single preparation and workflow remain unqualified. Open
for independent review/later qualification are general FFT error envelopes,
single search decision enclosures, nonunit complex transfer implementation
evidence, actual future runtime workspace and acceptance of the new-record/API
proposal. No human
image/carrier accuracy threshold is selected. The study may justify computational
error envelopes and disclose physical-accuracy uncertainty, or identify a material
owner decision if application-level accuracy becomes necessary. It must not
invent acceptance because no numeric budget was supplied.

## 7. Interpretation of the finite characterization

The report and its frozen manifests distinguish public double controls,
report-only preweighted sparse FFT/assembly kernels, independently evaluated
scalar-filter/recombination probes, and source/rounded-capture diagnostics.
None is an end-to-end single reconstruction. In particular, the first kernel
revision obtains its scalar filter from exact rational reference algebra and
rounds it; it does not measure binary64 denominator evaluation. Its retained
recombination snapshot also uses a reference-derived opposite coefficient and
is payload-only evidence. These limits remain attached to its original runs;
the separate scalar probe evaluates the candidate denominator and opposite
coefficient independently. No earlier run is relabeled as a corrected candidate.

For the sparse first-slice fixtures, all omitted half-spectrum bins are zero,
the only occupied axial bin is zero, and lateral x is zero. The complete
coefficients, slot mapping, per-time positive noise, supplied modulation and
carrier declarations live in the frozen manifest and `modes()` generator in
the report directory. The exact CE alpha is metadata describing the supplied
band units; filtering does not multiply alpha again. The mathematical reference
uses rational CE04 filtering and roots of unity, with a checked rational
enclosure of sqrt(2) for eighth roots. It does not call preparation or product
filtering helpers. The public double control creates valid CE02 history only
to obtain an existing record, then assigns independently declared writable
complex128 used coefficients. This is not the proposed constructor, and no
complex64 data is placed in an old double-only record.

Measured FFT interface dtypes do not identify internal accumulators/workspace.
The pinned NumPy and SciPy observations, including their actual axes/norms,
belong to the report; they do not justify an unconditional backend-independent
error multiplier. Keep binary64 scalar denominator/solve/coordinate arithmetic
and image accumulation in the proposed initial profile. Before a bulk complex64
product, explicitly round a bounded phase ramp/consumed scalar to complex64;
otherwise a binary64 phase exponential may promote the entire product to
complex128. Promote bounded reduction chunks *before* squares/cross-products;
`sum(dtype=float64)` alone does not repair binary32 product under/overflow.
Include the simultaneously live binary64 image accumulator and final float32
image in any memory claim.

Search remains unqualified in single precision. Actual double finite search
traces and rounded-overlap capture probes assess constructibility and sensitivity,
but do not independently enclose all single-precision comparisons or reproduce
a complete complex64 search. Exact scalar ties, represented near ties and
valid double underflow-objective witnesses expose separate representation,
decision and range risks. SP-EST must freeze full overlap/search witnesses,
independent objective/decision enclosures and the unchanged inherited magnitude
state before qualifying any search mode. There is no epsilon tie substitution.

CE06 native 2D, layouts, persistent camera/equalization, on/off and cubic drift
controls characterize downstream obligations only. They do not qualify single
CE06 preparation or workflow composition. SP-PREP06 and SP-WORKFLOW retain
their separately reviewed mode-by-mode requirements. #113 remains stationary
3D known-parameter intake using the new independently declared record. It must
freeze the exact scalar-to-bulk/transfer rounding order, local arithmetic
envelopes, actual failure precedence and all output fields before product tests.
No human physical-accuracy threshold or 16 GiB feasibility conclusion follows
from the finite computational characterization.
