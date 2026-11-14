# SP113: opt-in single-precision known reconstruction

**Version 1.0. Representation-dependent intake draft until accepted115
reconciliation; no runtime qualification yet.** The settled terms below are
normative for this authorized slice, subject to the explicit representation gate.
Issue [113](https://github.com/david-hoffman/simrecon/issues/113) authorizes one
stationary 3D known-parameter stage. The task in
`docs/tasks/single-known-reconstruction.md` owns execution state. This contract
adopts the accepted SP112 first-slice proposal and mathematical acceptance method;
prototype observations supply no implementation qualification. CE04 supplies the
finite mathematical procedure, CE03 supplies transfer validity/sampling, and the
rules below supply the new representation, rounding and interface contract.

## 1. Selection, compatibility and public interfaces

The exact keyword-only interface is the existing interface with `precision`
appended. There is no workflow/summary option, implicit adapter or dtype inference.

```python
declare_prepared_bands32(
    quadratures, noise_variance_factors, *, input_shape,
    dxy_um, dz_um, lateral_zoom, axial_zoom,
    mapping_revision="ce04-svn307-v1", provenance=(),
) -> PreparedBands32

reconstruct_known(
    bands, transfer, *, carriers_cyc_um, modulation,
    wavelength_nm, numerical_aperture, immersion_index, wiener,
    suppress_singularities=True, suppression_radius_bins=10.0,
    dampen_order0=False, omit_order0=False, omit_kz0=False,
    output_taper="cosine", wiener_increment=0.0,
    power_taper_exponent=None, precise_taper=False,
    filter_overlaps=True, explode_factor=1.0, precision="double",
) -> KnownReconstruction | KnownReconstruction32
```

`precision` must be an ordinary Python `str`, exactly `"double"` or
`"single-mixed-v1"`; None, aliases, other strings, booleans and nonstrings reject.
Omission is exactly explicit `"double"`. Double accepts the previously supported
PreparedBands/AcquisitionBands and returns the original KnownReconstruction.
It preserves same-environment array bytes/values, field order, settings, source
identities, mode traces, validation and failures of all old calls. The new keyword
adds no settings/provenance fields to old records. PreparedBands32 plus double,
and either old record plus single, reject; no full-array conversion is an adapter.

Single accepts only actual PreparedBands32 and valid existing OpticalTransfer.
It permits CE04 cosine/none taper and its suppression/order-zero options. Of the
existing CE06 options it requires `wiener_increment` a valid finite nonboolean
real numerically equal to zero (either signed zero), `power_taper_exponent is
None`, actual boolean `precise_taper=False`, actual boolean
`filter_overlaps=True`, and valid finite nonboolean real `explode_factor==1`.
Explicit default-equivalent values are accepted. Power taper, nondefault options,
AcquisitionBands, native Z1/2D, fractional zoom and every unqualified mode reject
with the option/mode named. Unsupported options are checked even for zero bands,
zero modulation or final order-zero omission. Old double calls keep all their
existing CE06 choices.

Root `simrecon` exports the constructor and both new types in `__all__`, alongside
unchanged `reconstruct_known` and ReconstructionError. The canonical new types
and constructor live in `simrecon.reconstruction.single_known`; the existing
entry/error/old result remain in `simrecon.reconstruction.known_parameters`.
Do not add retired namespace aliases. Public annotations/overloads must preserve
old statically typed callers: omitted or Literal["double"] plus old bands returns
KnownReconstruction; Literal["single-mixed-v1"] plus PreparedBands32 returns
KnownReconstruction32. A runtime-selected valid string may return their union;
type tests also exercise facade imports, dataclass fields and old call signatures.
The single profile is explicit even when bands already have dtype complex64.

## 2. PreparedBands32: declaration without preparation

This frozen dataclass has exactly these fields, in order:

| Field | Exact stored value/type |
| --- | --- |
| quadratures | ordinary owned C-contiguous read-only native complex64 ndarray `(T,D,Q,Z,Y,X//2+1)` |
| noise_variance_factors | independent ordinary owned C-contiguous read-only native float64 ndarray `(T,D,O)` |
| input_shape | tuple of six nonboolean Python ints `(T,D,P,Z,Y,X)` |
| input_scale | Python float, RN64 `1/(X*Y*Z*L**2*A*D)` computed using exact integer product then binary64 division |
| dxy_um, dz_um | positive finite Python floats, validated original real values then converted to binary64 |
| lateral_zoom, axial_zoom | positive nonboolean Python ints L,A |
| mapping_revision | exact ordinary string `"ce04-svn307-v1"` |
| precision_profile | exact ordinary string `"single-mixed-v1"` |
| provenance | immutable tuple of `(nonempty ordinary str, ordinary str)` pairs; unique keys, order preserved |

T,D>=1, Z>=2, Y>=1, even X>=2. Q is odd, Q<=P and
O=(Q+1)//2>=2. Both inputs must be ordinary ndarrays of the exact native dtypes;
reject subclasses, foreign byte order, bool/object/string/other dtypes and
nonfinite components. Noise is strictly positive. Shapes are exact with no
broadcast. Strided and read-only inputs are accepted and copied to the owned
layout. Original-value/structural/extent validation precedes copy/numerical work;
there is no implicit complex128-to-complex64 band rounding. Input bands may be
zero, signed or arbitrary finite complex coefficients; no physical-real symmetry
or acquisition history is demanded. Provenance describes declared formulas,
input identity and any caller conversion; it authenticates no claim.

Constructor and consumer validate every listed field. Consumer requires the
stored canonical Python metadata types, exact scale, profile/revision,
provenance and owned/read-only/C-contiguous native arrays, full finiteness and
positive per-time noise. A forged dataclass, altered write flag, shared view,
foreign dtype or false scale does not bypass validation. There are no phase
matrices, camera maps, sentinel/drift/off histories or discarded diagnostics.
A valid direct dataclass with all exact fields is permitted. Constructor copies
are independent of inputs and each other; later original-buffer mutation has no
effect. There is no new shared writable state or concurrency guarantee.

Representation is the latest accepted inherited geometry/representation policy,
with native shape/stride/byte checks for the actual c64/f64/f32 target allocations
and all aggregate axes, before allocation. Scalar magnitude and lateral-zoom
representability rules inherit the applicable approved boundary. This task adds
no size-domain expansion or arbitrary smaller cap. The current SP112/CE04 text
is not permission to restore a superseded bound. **Before formal A, the
coordinator must reconcile independently accepted 115 into exact effective
representation rules, retaining latest geometry compatibility. Before C, accepted
and frozen parent 116 is required and inherited rules must be rechecked.** The
public preparation is not launch-ready until the 115 reconciliation replaces this
paragraph. No formal A or final checkpoint may select the missing representation
meaning. No assertion that those parent rules are settled is made. Scientific prerequisite 112 is independently accepted;
incidental stack ancestry is not another scientific prerequisite.

## 3. Inputs, source identity and result schema

Transfer remains existing c128 OpticalTransfer, with complete-table validation,
its accepted source-name/hash tuple, radial/full layout and at least O orders.
Extra orders are validated and unused. Empirical prepared c128 values need not
be c64-exact; declared tables retain their own accepted domain. Preserve source
storage and metadata; no redeclaration/downcast of a prepared table. Validate
and snapshot caller inputs without mutation. Carriers are real `(D,2)` in
cycles/um, modulation real/complex `(D,O-1)` shared across times, using the
existing CE04 standard numeric dtype/domain and f64/c128 conversion. Zero
carrier, signed/complex/zero modulation and signed zero are permitted.
Wavelength, optics, Wiener, radius, flags and taper retain CE04 units and domains:
integer nm wavelength 1..32767; immersion in [1,2],
0<NA<=min(2,immersion), positive Wiener, signed radius, actual booleans.
No signal, modulation or noise floor beyond strictly positive noise is added.

KnownReconstruction32 is a separate frozen dataclass, not a subclass/downcast of
an old record. Its exact field order is:

1. `image`: owned C-contiguous read-only native float32 `(T,A*Z,L*Y,L*X)`.
2. `filtered_quadratures`: owned C-contiguous read-only native complex64, same shape as input.
3. `x_um`, `y_um`, `z_um`: independent owned read-only float64 vectors.
4. `carriers_cyc_um`: independent owned read-only float64 `(D,2)`.
5. `modulation`: independent owned read-only complex128 `(D,O-1)`.
6. `radial_cutoff_cyc_um`: Python float.
7. `axial_cutoffs_bins`: owned read-only native int64 `(O,)`.
8. `resolved_settings`: immutable ordered pairs below.
9. `mode_trace`: exactly empty tuple `()`; retained in the current CE04 result position, with no invented CE06 history.
10. `source_revision`: exactly `"SVN307"`.
11. `reference_sha256`: exactly CE04's six source-name/hash pairs in CE04 table order.
12. `precision_profile`: exactly `"single-mixed-v1"`.
13. `precision_provenance`: immutable ordered `(str,str)` pairs below.

The grouped vector names above expand individually in that order. No returned
array aliases an input or another returned array. Preserve supplied parameters
at validated binary64/complex128 values. Coordinates use CE04 centered labels;
the inverse itself stays unshifted. Image remains signed detector-count-scale
output, with no clipping, gain fitting, positivity or mass/resolution assertion.

`resolved_settings` has exactly the 15 CE04 keys in this order:
`wavelength_nm` (Python int), `numerical_aperture` (float), `immersion_index`
(float), `wiener` (float), `suppress_singularities` (bool),
`suppression_radius_bins` (float), `dampen_order0` (bool), `omit_order0` (bool),
`omit_kz0` (bool), `output_taper` (str), `dxy_um` (float), `dz_um` (float),
`lateral_zoom` (int), `axial_zoom` (int), `input_scale` (float).
Do not append CE06 defaults or precision keys here.

`precision_provenance` has exactly these keys in order; every value is an
ordinary string:

| Key | Value |
| --- | --- |
| requested_profile | `single-mixed-v1` |
| resolved_profile | `single-mixed-v1` |
| mapping_revision | `ce04-svn307-v1` |
| band_storage_dtype | `complex64` |
| noise_dtype | `float64` |
| parameter_dtypes | `float64/complex128` |
| transfer_source_dtype | `complex128` |
| transfer_query_dtype | `float64/int64` |
| transfer_interpolation_dtype | `complex128` |
| scalar_filter_dtypes | `float64/complex128` |
| consumed_scale_dtype | `complex64` |
| local_bulk_dtype | `complex64` |
| fft_input_dtype | `complex64` |
| fft_output_dtype | `complex64` |
| fft_interface | `scipy.fft.ifftn` |
| fft_axes | `0,1,2` |
| fft_norm | `forward` |
| fft_workers | `1` |
| fft_backend | actual identified default SciPy FFT backend, or `unknown` if attribution unavailable |
| fft_backend_version | actual independently exposed backend version, or `unknown` |
| scipy_version | actual installed SciPy version |
| numpy_version | actual installed NumPy version |
| fft_internal_precision | `unknown` unless backend evidence identifies it; report exact evidence separately |
| fft_workspace | `unknown` unless actual attribution exists; never infer from output dtype |
| phase_query_dtype | `float64` |
| consumed_phase_dtype | `complex64` |
| accumulation_dtype | `float64` |
| image_dtype | `float32` |
| transfer_rounding | `sample-c128;scalar-c128/f64;scale-once-c64` |
| input_identity_encoding | `sp113-framed-v1` |
| bands_sha256 | validated input identity below, lowercase hex |
| transfer_sha256 | validated original c128 transfer identity below, lowercase hex |
| parameters_sha256 | validated supplied parameter/settings identity below, lowercase hex |

No precision failure record is returned. Failure messages name profile and stage;
the external execution report retains failed inputs/stage/cause and precision.

For reproducible identities define `H(domain,metadata,arrays)` as SHA256 of framed
byte strings. Each frame is uint64 little-endian byte length followed by payload.
First frame is ASCII `sp113-framed-v1/` plus domain. Second is UTF-8 canonical JSON
of metadata (`ensure_ascii=True`, `sort_keys=True`, separators comma/colon,
`allow_nan=False`); tuples become JSON arrays. For each array in the named order,
frame canonical JSON `[name,dtype,shape]`, then frame logical C-order little-endian
bytes, retaining signed zeros. Stream bytes in bounded blocks; no promoted volume
is needed. Dtype strings are `<c8`, `<f8`, `<c16` as appropriate. Bands metadata
is an object of all nonarray PreparedBands32 fields including caller provenance;
arrays are quadratures, noise_variance_factors. Transfer metadata is layout,
dkr_cyc_um, dkz_cyc_um, norders, source_revision, reference_sha256; its sole array
is original `samples` as `<c16`. Parameters metadata is `resolved_settings` and
`precision`; arrays are validated carriers_cyc_um `<f8` then modulation `<c16`.
These identify validated declared bytes/metadata, not allocation pointers or raw
camera lineage. Caller provenance remains distinct from measured identities.

## 4. Fixed arithmetic and storage procedure

CE04's literal traversal, support, branches, integer cutoffs, partner indexing,
zeroing and operation order apply. Use v[t,d,m] from the new per-time noise;
there is no accidental time-zero reuse. Evaluate coordinates, source sampling,
support/asin/cutoff/phase decisions, positive Wiener square, inverse noise,
powers, denominator and complete filter scale in f64/c128.

Freeze scalar order as follows: sample H1 through CE03 first, evaluate g,
initialize denominator with `((abs(H1)**2)*(abs(a)**2))*g`, then add eligible
other powers in direction-major, ascending signed-order order, skipping only
the exact self pair; add w*w last. Each real scalar operation is binary64,
`abs(complex)` is binary64 hypot, and multiplication is left-associated. Compute
`(g*conj(H1))/denominator` componentwise, then multiply taper if selected, then
multiply conj(a) for side orders. Use componentwise real binary64 complex
products/additions; no fused/compensated alternative changes this sequence.
Taper uses the CE04 binary64 hypot/cos sequence and pi represented in binary64.
Transcendental/library uncertainty must be included in fixture envelopes.
Require positive finite resolved square/denominator and finite intermediates;
zero weights do not skip transfer samples or an evaluated singular damping.

Round the *complete consumed scale* once to native complex64, componentwise
round-to-nearest ties-to-even (RN32), after all c128 scalar operations. Do not
round H before interpolation/powers, downcast the full table, multiply c64 bands
by c128 scales, or downcast only the final filtered array.

All native center/side coefficient work and full spectral storage use c64.
For side coefficients form `E+i*O` by exact component rotation then RN32 component
addition; multiply by rounded scale using separate RN32 real products followed
by RN32 component sums/differences (no FMA). For recombination obtain p and
n=conj(F(-z,-y,-x)), form RN32 p+n and p-n, then scale/rotate by exact 1/2
with RN32 outputs. Center multiplication uses the same complex product rule.
Check intermediate finiteness before a later cancellation can conceal overflow.
Do not supply a reference-derived opposite coefficient to the candidate.

Preserve Y1 empty loops and odd-Y untouched rows bit-for-bit, except CE04's
explicit reflected outside-support/axial-zero writes; those writes use positive
complex zero. Positive native Nyquist is embedded once at the positive signed
lift without endpoint splitting. Initialize padded spectra with c64 zeros.
Use `scipy.fft.ifftn` on a c64 3D array, axes `(0,1,2)`, `norm="forward"`,
`workers=1`, `overwrite_x=False`, default backend; input and returned spectrum
must actually be c64. No new backend selection or promise about internal FFT
accumulators/workspaces is made. Retain unnormalized positive inverse, alpha
already in supplied bands, native filtering before carrier relocation, centered
positive carrier phase and original direction/order accumulation sequence.

Evaluate the phase argument and complex unit ramp in f64/c128 in bounded
blocks; round the complete consumed ramp once to c64. Multiply inverse c64
samples by that ramp in c64 using the same product rule. Widen the real product
to f64, multiply side contribution by 2 in f64, then add to f64 image accumulator;
center inverse real components widen directly. Check each contribution and each
accumulator update. Finally RN32 the signed image with finite check. No
image-sized f32 accumulation, magnitude conversion or hidden scale is allowed.

“Bounded” here is an execution rule, not a scientific size cap: any derived
c128 transfer/scale/phase scratch array has at most 65,536 elements, and each
purpose has at most one such live buffer; f64 phase scratch uses the same
maximum. Larger domains iterate blocks. Existing original transfer storage,
small parameter/metadata arrays and coordinates keep their stated dtypes.
There is no volume-sized c128 band copy, padded spectrum, filtered diagnostic,
transform output or bulk product. A small permitted volume can fit within a
block, but the rule never allows processing a larger volume as one c128 bulk
product followed by downcast. No whole-volume promoted reductions are needed.
D must inspect dtype/promotion and allocation paths; actual transitions must
also be observed in the real implementation. The bounds do not set a process
memory ceiling; f64 image accumulator plus f32 final image coexist, and backend
workspace remains separately unknown unless identified.

Finite subnormal/zero rounding is permitted and reported, including signed-zero
behavior. No arbitrary weak-signal floor, epsilon tie, clipping or silent double
fallback is allowed. Distinguish input conversion, consumed-scale/ramp conversion,
local arithmetic, FFT, f64 accumulation and final rounding. An exact mathematical
nonzero rounded to finite zero is not automatically a domain failure; disclose
its absolute error. Nonfinite/overflow and a required positive quantity rounded
to zero reject explicitly at their stage, even for a double-valid input.

## 5. Validation and failure precedence

Ordinary missing/duplicate/unknown Python arguments raise TypeError. All new
constructor/profile/domain/operation rejections use existing ReconstructionError
(code exactly `reconstruction-domain`, subclass SimreconError/ValueError), with
nonempty message identifying argument or `single-mixed-v1` stage. No new error
class/category and no punctuation contract. Allocation, FFT and OtfError causes
are retained with `raise ... from ...`; caller interruption remains interruption.
No failure returns partial records or changes caller inputs.

For new-profile dispatch freeze this order, stopping at the first failed phase:

1. Precision kind/value, then record/profile compatibility.
2. Complete bands metadata/container kinds and tuple/array shapes/dtypes;
   metadata domains/geometry/representation and scale/profile/revision/provenance;
   array ownership/layout flags; original array finiteness, then positive noise.
3. Complete transfer record validity/source identity/representation and order count.
4. Scalar declarations in signature order (wavelength, NA, immersion with joint
   optics bound, Wiener, suppression flag/radius, dampen, omit, omit-kz0, taper,
   increment, exponent, precise, overlaps, explode), including unsupported-option
   checks. Within a field check kind, finite/domain, then supported value.
5. Carriers then modulation: kind/shape/dtype, original finite/component domain,
   then owned f64/c128 conversion. Validate all original values before conversion.
6. Derived sampling/support/cutoffs, reciprocal-noise, squared Wiener, taper and
   coordinate domains, then bulk allocation/filter/FFT/assembly/final conversion.
   At use, actual-stencil safety precedes returned H; evaluate self sample before
   g, eligible other sample before its g, and ordered denominator before scale.

Constructor uses phase 2 in the same order, computing scale instead of accepting
it, then copies. Within a phase, field order is record declaration order, except
shape/Q consistency follows input_shape inspection. Wrong input arrays reject
before reading their values. No allocation/transform occurs before all static
validation; small validation metadata is allowed. A/B must cover multi-invalid
precedence at phase boundaries and pair rejections with allowed positives.
Default double validation/order remains untouched by these new-profile phases.

Every actual CE03 stencil vertex remains required, including zero weights,
zero-data/zero-modulation/zero-damping cases, source flat cross-row aliases and
one-time negative wrapping. No endpoint clamp/skip is permitted. Undefined asin,
evaluated c0=0 damping, unsafe addresses/cutoffs, overflow/nonfinite coefficient,
transform, phase, accumulation or result, allocation/backend failure all reject.
Y1 empty loops do not evaluate damping/stencils and remain valid when other
operations are defined. No hidden positivity/minimum transfer or modulation is
introduced. Untouched-row and signed-zero facts must remain observable publicly.

## 6. Independent scientific and execution acceptance

A independently declares each half-spectrum coefficient (slots 0,E1,O1,...),
positive rational per-time noise, alpha units, transfer, carriers and modulation.
Fixtures use no preparation, product helper, double-output downcast or unfinished
stage. Include distinct T2 noise, nonunit complex radial/full transfer, a valid
c128 empirical-style source with components such as 1+2^-30 where accepted,
unequal directions/orders, strict support/stencil boundaries, untouched rows,
signed Nyquist, zoom, normalization, cancellation, zero/signed/complex modulation,
subnormal/overflow and failure precedence. Old-product compatibility controls
supplement, never supply, scientific expectations.

For each fixture freeze x0, exactly represented x32, exact finite-procedure
F(x32), scalar order, reference enclosure and qualified stage envelopes before
candidate trials. Report F(x32)-F(x0) separately. Use exact rational/sparse Fourier
algebra and independent direct DFT (exact roots for sizes 2/4, outward rational
or high-precision transcendental intervals with analytic tails otherwise).
Precision doubling alone is no proof. Enclose binary64 scalar operations and
once-rounded consumed scales/ramps separately. For finite normal complex products
use componentwise gamma(3,u32) sum-of-absolute-products plus input conversion;
handle subnormals with absolute half-spacing terms and detect overflow. Enclose
actual +/- recombination independently. No product oracle supplies candidate data.

There is no universal FFT multiplier. A/B must derive and freeze a justified
fixture-specific FFT envelope for each accuracy-qualified FFT-dependent fixture,
including pinned interface assumptions, or mark that fixture's accuracy
unqualified and retain a blocking gap in the intended qualification. Observed
maxima and double/single agreement cannot choose the tolerance. Exact DC constant
and cancellation transforms can have separately justified zero FFT error; that
claim does not extend to arbitrary FFTs. Tiny DFT semantic proofs still cover
axes/sign/normalization/embedding independently of the general backend question.

Propagate reference/scale/local/phase/FFT error with signed absolute weights;
for K f64 accumulator additions use gamma(K,u64)*sum(abs(actual terms)) only
under finite-normal assumptions and K*u64<1, plus absolute subnormal errors.
Add local final f64-to-f32 half-ulp (or u32*abs(accumulator)+2^-150) separately.
Report reference width, candidate interval distance/upper bound, signed extrema,
maximum absolute/RMS error and error relative to a declared nonzero signal scale;
no division by each near-zero pixel. Report cancellation condition, infinite at
exact zero. Certified strict decisions require disjoint enclosures with the
correct equality rule; overlapping boundary intervals are unresolved, not pass.
Physical recovery under noise/model mismatch remains unknown; no owner image
accuracy threshold is invented.

Before acceptance require matched real execution evidence from the resulting
runtime, not standalone kernels. A coordinator-owned nonblind evidence author,
separate from restricted C, owns the later driver
`docs/reports/single-known-reconstruction/execution-driver.py`, raw
`execution-runs.json` and `execution-report.md`. That later assignment authorizes
those files; this intake creates none of them. The driver may observe/interpose
existing numerical allocation/FFT interfaces externally without adding product
instrumentation seams; observations and their coverage limits accompany D's
source audit. C owns product code only and cannot author/modify A/B fixtures,
checks, measurement assertions or gates.

Freeze identical declared Fourier data/transfer/parameters, hashes, retained
original buffers, process commands, warmup/call protocol and environment before
matched double/single runs. For the double comparator use independently supplied
equivalent valid old records, not masquerading c64 records; no preparation time
is charged to one mode's call only. Account for all fixture setup and retained
original/source arrays in both modes: preparatory work must not contaminate
whole-process high-water asymmetrically without explicit disclosure. Use three fresh single-workload processes per
mode/case, fixed seeds if used, all failures retained, one call per measured
process after equal import/setup protocol, no in-process mode sequence. Keep
original inputs alive through measurement. Set supported OMP/BLAS numerical
threads to one and FFT workers=1; record effective controls and shared interference.
Report raw runs/median/range, call-only monotonic time, native peak RSS in KiB and
bytes, pre-call high-water (its difference is not pure algorithm peak), reachable
owned retained payload with shared backing once, original/copy/result dtypes and
actual stage transitions, and concurrently live original/result/workspace arrays.
Unknown internal FFT workspace is included in RSS without invented attribution.
Start tiny; any spatial increase requires coordinator headroom/exclusive resource
approval within a declared finite measurement plan. No 16 GiB run or guarantee,
fixed peak ceiling, speed ratio or unsupported extrapolation is authorized.

Record actual Ubuntu 24.04.5 container/host/cgroup/CPU/swap/allocator, Python,
NumPy/SciPy/uv/backend/thread versions, lock/wheel/input/generator identities,
commit/tree/dirty state, process status and limitations. Host Debian is not
qualification. The execution hold forbids setup/probes/tests/measurements until
the root resource/environment grant. After grant and frozen B checkpoint, C's
focused checks, complete exact-candidate Ubuntu `make verify` (all 13 phases,
strict no-skip outcomes, two workers, current global/package/file native coverage,
wheel/import/audit and same-run M25 evidence), then fresh D acceptance remain
required. Percentages are advisory; missing required evidence is blocking.

No preparation/search/half/disk/native2D/workflow expansion, dependency/backend
change, gate/policy migration, new memory ceiling, default migration or physical
accuracy promise follows. Root owns restacks/integration/push/PR and final
publication parent 116; the issue coordinator may commit authorized static prep.
This intake author does not commit. These documents need no second authorization checkpoint.
