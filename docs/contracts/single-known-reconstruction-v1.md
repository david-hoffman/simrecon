# SP113: opt-in single-precision known reconstruction

**Version 1.0. Normative intake contract, including accepted wide-allocation
representation rules. No runtime qualification yet.** Public-source preparation
is ready for the coordinator's actual hashed static-only A packet. This file is
not that launch packet; all execution still needs root's explicit resource grant.
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

Single accepts only actual PreparedBands32 instances (including subclasses that
satisfy every canonical field check) and valid existing OpticalTransfer.
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

For every new single-mode flag, “actual boolean” means type exactly `bool` or
`numpy.bool_`, both accepted and canonicalized to Python bool in settings. No
integer/truthiness substitute. Taper accepts Python str and str subclasses;
resolve underlying string content with `str.__str__` to canonical Python str,
then require cosine/none. A subclass cannot provide custom comparison semantics.
This deliberately differs from precision, which requires type exactly str.
Scalar real arguments use the inherited `numbers.Real` domain excluding bool
and np.bool_: original finite value/magnitude checks precede binary64 conversion.
Wavelength uses inherited `numbers.Integral`, excluding both boolean types,
with the stated integer range. Accepted NumPy scalar real/integer kinds remain
valid; this does not give array arguments extended-precision dtype support.

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

### Exact facade and installed-distribution compatibility

The existing 38 public exports remain, and exactly these three approved names
are added: `declare_prepared_bands32`, `PreparedBands32`, `KnownReconstruction32`.
The final checkout and installed product wheel expose exactly the same 41-name
inventory below. This is a set/cardinality contract, not a new ordering rule;
duplicate, missing, renamed or unapproved exports fail. Every exported object
remains callable and its `__name__` equals its public name. Existing module-
migration, removed-alias and exception-hierarchy checks remain substantive.

```text
AcquisitionBands AcquisitionModeError ModeEvent TwoDPlaneInputs
prepare_acquisition_bands reinterpret_2d_planes DataBlock DatasetInfo
EstimatedParameters ImagejSeries ImagejWriteReport KnownReconstruction
OpticalTransfer OtfError ParameterEstimationError PreparedBands PreparedOtf
RawAcquisition ReconstructionError ReconstructionSummary SimreconError
WriteReport WorkflowError WorkflowReconstruction declare_acquisition declare_otf
estimate_parameters export_imagej harmonize inspect prepare_bands prepare_bead_otf
read reconstruct_known reconstruct_summary reconstruct_workflow sample_otf write
declare_prepared_bands32 PreparedBands32 KnownReconstruction32
```

Installed-product verification continues to prove import from the installed
runtime-only environment, absence of development/verification packages and
utility leakage, the sole `simrecon = simrecon.cli:main` console entry, existing
`inspect`, `convert` and `export-imagej` help commands, and the missing-input
`inspect` error behavior (status 1, no stdout, JSON code `io_error`). No scientific
CLI or new console entry is added. Separate product/development wheels, sole-wheel
and digest checks, development doctor/strict-pytest outcomes and contamination
rejection retain their existing guarantees. The product success message reports
`installed product: 41 exports, console CLI, runtime-only environment`; its count
must agree with the independently declared exact inventory.

Blind A owns only the corresponding approved expectation updates in the whole
public test files `tests/test_module_migration.py` and
`tests/test_installed_wheels.py`, in addition to its six new files. Preserve all
38 original names and every other substantive assertion/fixture/CLI/isolation/
failure check; no subset/count relaxation, source-derived expected inventory or
checker repair by A. Fresh B reviews the complete changed expectation set before
the final test checkpoint. Installed/build tests remain execution-held for blind
roles unless a separate explicit grant qualifies every diagnostic channel.

The actual installed-wheel checker belongs to a separately named infrastructure
owner, never scientific C. Its conventional inventory alignment preserves every
gate and receives explicit independent infrastructure assessment within fresh D
of the exact full-passing combined candidate, satisfying bounded-review
requirements; use a separate fresh bounded reviewer only if that assessment
cannot meet those requirements. Real installed checks must pass before acceptance.

## 2. PreparedBands32: declaration without preparation

This frozen dataclass has exactly these fields, in order:

| Field | Exact stored value/type |
| --- | --- |
| quadratures | ordinary owned C-contiguous read-only native complex64 ndarray `(T,D,Q,Z,Y,X//2+1)` |
| noise_variance_factors | independent ordinary owned C-contiguous read-only native float64 ndarray `(T,D,O)` |
| input_shape | exact built-in tuple of six exact built-in nonboolean Python ints `(T,D,P,Z,Y,X)` |
| input_scale | Python float, RN64 `1/(X*Y*Z*L**2*A*D)` computed using exact integer product then binary64 division |
| dxy_um, dz_um | positive finite Python floats, validated original real values then converted to binary64 |
| lateral_zoom, axial_zoom | positive exact built-in nonboolean Python ints L,A |
| mapping_revision | exact ordinary string `"ce04-svn307-v1"` |
| precision_profile | exact ordinary string `"single-mixed-v1"` |
| provenance | exact built-in tuple of exact built-in two-element tuples `(nonempty ordinary str, ordinary str)`; unique keys, order preserved |

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

“Exact built-in” and “ordinary” mean `type(value) is` the named built-in:
tuple/int/str/float subclasses are not canonical stored metadata. Constructor
dxy/dz inputs use the inherited nonboolean numbers.Real rule (NumPy real scalar
kinds included) and are stored as exact built-in floats; consumer dxy/dz/scale
must already be exact built-in floats. Mapping/profile/provenance strings are
exact built-in str, unlike the reconstruct taper's accepted str subclasses.

### Effective representation and declaration order

The accepted `docs/contracts/wide-allocation-domain-v1.md` supersedes the five
legacy byte-only ceilings. Let I=2**31-1, M=2**63-1 on required native64 Ubuntu,
Xo=L*X, Yo=L*Y, Zo=A*Z. Resolve all declarations, products, offsets and comparisons
as exact Python integers before narrowing, copying or allocation. No fixed-width
NumPy multiplication, floating byte calculation, unsigned wrap or saturation.

Retain signed32 positive dimensions/counts T,D,P,Z,Y,X,Q,O,L,A and resolved
Xo,Yo,Zo, plus the following exact CE04 positive signed element/count products:

| Count | Inclusive upper bound / reason |
| --- | --- |
| X*Y*Z | I, native full-volume indices |
| (X//2+1)*Y*Z | I, native half-volume indices |
| Xo*Yo | I, output plane/lookup element indices |
| Xo*Yo*Zo | I, output full-volume indices |
| D*O | I, inherited direction/order count |
| Q*P | I, inherited quadrature/declared-phase count, retained even though declaration does not run separation |

Actual signed lifts, wrap/reflection sums, loop/count intermediates, cutoff
ceil/truncation conversions and flat lookup/stencil indices retain signed32
validity before use. Negative signed values use [-2**31,I] where the finite
procedure permits them; positive allocation/count declarations use [1,I].
L must have exact finite float32 integer representation, and L,A>=1 are Python
integers, giving integral nonshrinking enlarged extents. These are declaration
rules, not a fractional-zoom mode. Physical scalars retain their existing finite
float32-component-magnitude domains and binary64 evaluation; widening bytes does
not widen scalar, transfer, coordinate or numerical domains.

The five historical byte expressions `8*X*Y*Z`, `8*Xo*Yo*Zo`,
`4*Xo*Yo*Zo`, `8*O`, `4*Xo*Yo` require exact positive byte counts <=M.
Their unsigned32/signed32 byte caps are gone, including the signed-byte lookup
limit. Retained signed element/offset checks still bind. A dominating actual-width
native check may prove a historical expression; do not add a redundant narrow
guard or invent an isolated public rejection for an unreachable bound.

For every owned/copied/used target shape d with actual positive integer itemsize s,
check each dimension 0<=d_i<=M and `s*product(max(d_i,1))<=M`, before array-sized
copying, hashing, finite scans, broadcasting, numerical work or allocation.
All scientific arrays here are nonempty; the general stride rule authorizes no
empty scientific input. It bounds contiguous shape/stride/bytes, not merely
nbytes, and includes aggregate T/D/Q/O axes. Constructor strided/read-only inputs
remain accepted; checks describe their required canonical copied target, not a
new ban on negative/noncontiguous caller strides.

| Actual allocation family | Shape / actual bytes per element to check |
| --- | --- |
| Declared/snapshotted/filtered bands | `(T,D,Q,Z,Y,X//2+1)`, c64=8, including each independent copy |
| Per-time noise and optional reciprocal copy | `(T,D,O)`, f64=8; used per-time slices remain validated |
| Full native side workspace and native harmonic storage | `(Z,Y,X)`, c64=8 |
| Padded spectrum and inverse result | `(Zo,Yo,Xo)`, c64=8 each; no assumed c128 copy |
| Image accumulator and final image | `(T,Zo,Yo,Xo)`, f64=8 and f32=4 independently |
| Phase/ramp/consumed-scale blocks | actual block shape; f64=8, c128=16 or c64=8 as specified in section4, with its block bound |
| Supplied carriers/modulation and order metadata | `(D,2)` f64=8, `(D,O-1)` c128=16, any implicit `(D,O)` c128=16, `(O,)` int64=8 |
| Coordinates and any plane/lookup buffers | `(Xo,)`, `(Yo,)`, `(Zo,)` f64=8; any actually allocated plane/lookup uses its actual shape/dtype/itemsize, with signed element indices retained |
| Precision/provenance identity storage | actual aggregate shape/pointer/native extent, streamed array hashes; no hidden whole-volume conversion |

Any additional actual temporary needs the same actual-width native checks; this
table supplies no allocation requirement or total-memory limit. Existing original
c128 transfer arrays retain CE03 per-order signed `R*K` or `K*Yh*Xh`, sampler
plane/index/offset constraints and aggregate native c128=16 extents. Existing
c128 parameter arrays retain their accepted component/domain/native checks.
There is no new signed32 bound on aggregate T*D*Q or T*D*O storage solely because
the native arrays have those axes; their actual byte/stride rule still binds.

No preparation runs at this boundary. CE02's padded-camera `(X+2)*Y*Z`,
camera-frame `D*P*Z` and raw/phase-design/map/solve arrays, and CE06 off/exposure/
drift/trace count products are absent operations/storage, not extra admission
constraints on independently declared bands. The explicit inherited Q*P and D*O
constraints above remain; absence of preparation does not remove them. Old
PreparedBands/AcquisitionBands routes keep their own complete approved checks.

Reject known invalid geometry using metadata before array-sized work, even when
an independently invalid value could fail later. Inspect array type/dtype/shape
metadata only as needed to determine Q/O and shape consistency. Positive scale
is then computed/checked in binary64 without running preparation. Representable
geometry supplies no RAM admission, backend-success or 16GiB claim. Allocation/
backend failures within the domain remain explicit operation failures with cause.

For safe integer-only native evidence, the existing approved production interface
is `simrecon.reconstruction.known_parameters._extent(shape: tuple[int, ...],
itemsize: int) -> None`, for positive Python-integer shapes and positive integer
item sizes only. It must remain on a real production caller path, including new
profile actual-width validation; no new test-only validator is commissioned.
The exact signature/domain above is sufficient public interface permission;
it grants no implementation reading or access to other metadata helpers.
Use exact integer metadata boundaries, tiny genuine constructor/consumer calls
for ordering/categories and D's actual-path audit together. A local arithmetic
calculation alone, or this validator alone, is insufficient proof of public
ordering/removal of every legacy guard. Redundant bounds get implication evidence,
not an impossible isolated public case. Never allocate a huge successful fixture
or run the wide contract's motivating geometry merely to classify it.

Accepted115 representation meaning is reconciled; scientific prerequisite112
remains independently accepted. **The first unpublished PhaseP C product parent
is accepted/frozen115 ace06c861b974b6251a092567c253ae4eb0f56c8,
tree2247d3909f43bc4764beb5c748caa917aaa1d707. Before C, complete actual pre-C
fixture/reference/source-free/process/tool qualifications, fresh complete B
acceptance/frozen inputs and inherited material reconciliation.** Root explicitly
applied this task-local routing change after independent review; it supersedes
the former parent116 prerequisite only for first unpublished C. No unaccepted116
measurement may supply truth, tolerance or resource conclusions. Incidental
stack ancestry is not another scientific prerequisite and no owner decision is missing.

## 3. Inputs, source identity and result schema

Transfer remains existing c128 OpticalTransfer, with complete-table validation,
its accepted source-name/hash tuple, radial/full layout and at least O orders.
Extra orders are validated and unused. Empirical prepared c128 values need not
be c64-exact; declared tables retain their own accepted domain. Preserve source
storage and metadata; no redeclaration/downcast of a prepared table. Validate
and snapshot caller inputs without mutation. Carriers are real `(D,2)` in
cycles/um, modulation real/complex `(D,O-1)` shared across times, using the
existing CE04 standard numeric dtype/domain and f64/c128 conversion. Specifically,
these parameter arrays accept ndarray subclasses, strided/read-only arrays and
either byte order, standard signed/unsigned integers of1/2/4/8 bytes and real
float16/32/64; modulation also accepts complex64/128. Carriers reject complex,
both reject bool/object/string/extended-precision arrays. No new native-endian or
ordinary-array restriction applies to parameters, in contrast to PreparedBands32
quadrature/noise arrays. Zero
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
First frame is ASCII `sp113-framed-v1/` plus the exact lowercase domain suffix:
`bands` for bands_sha256, `transfer` for transfer_sha256, `parameters` for
parameters_sha256. Thus the three complete first-frame payloads are exactly
`sp113-framed-v1/bands`, `sp113-framed-v1/transfer` and
`sp113-framed-v1/parameters`, with no trailing separator or NUL. The domain is
fixed by the identity kind, never caller-selected. Second is UTF-8 canonical JSON
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
accuracy promise follows. Root owns restacks/integration/push/PR and the
final publication parent actual accepted120. Root integration/new candidate
requires fresh affected B and material/profile/helper/oracle/native/environment
renewal BEFORE further integrated C, resources, fullgate, D or publication.
The issue coordinator may commit authorized static prep.
This intake author does not commit. These documents need no second authorization checkpoint.

## 7. Explicit public scenario ledger

This is the single normative scenario source: **293 explicit scenario IDs/subrows**.
Each ID is a distinct approved
success/rejection/interpretation/guarantee, not a test quota. One rule applied to
several equivalent values remains one row. Constructor/consumer obligations
apply at both boundaries where the field exists; direct dataclass construction
never bypasses them. New representation rules are section2 above. A derives
fixtures/assertions and justified envelopes, never the expected meaning. B audits
the complete mapping; D audits actual paths beyond the accepted test checkpoint.
The task maps these IDs to named ownership without maintaining a second ledger.

Rows state required outcomes, not a demand to fabricate an isolated failure.
Where retained bounds or earlier finite checks make a rejection unreachable,
independent mathematical implication plus tiny real public controls and D's
path audit are valid evidence. For example finite c64 inverse/products and
D*O<=I bound absolute f64 accumulation by at most `2*I*finfo(float32).max`,
far below binary64 overflow: no mandatory artificial f64-accumulator-overflow
test follows from S32.15. The required finite outcome remains. The same rule
applies to redundant half-volume/order-byte/final-image extent constraints;
never bypass a real guard or introduce a test-only seam to reach a row.

Mapping keys: **B**=`tests/test_single_known_boundary.py`,
**F**=`tests/test_single_known_filter.py`, **A**=`tests/test_single_known_assembly.py`,
**P**=`tests/test_single_known_precision.py`, **Y**=`tests/test_single_known_typing.py`,
**J**=`tests/single_known_fixture.py`; **M**=`tests/test_module_migration.py`,
**W**=`tests/test_installed_wheels.py` (approved facade expectation updates only);
**X**=separate nonblind execution evidence, reviewed within fresh D.
Test author owns only its named tests/fixture. All rows
require fresh B requirement/oracle/positive-input review; X rows additionally
require D's independent protocol/observation audit. Rejection rows inherit section5
category, precedence, cause retention and no-partial/no-mutation guarantees.

| ID | Fixed observable requirement / rejection rule | Expectation source; equivalent examples | Planned mapping |
| --- | --- | --- | --- |
| S01.1 | Omitted precision preserves old exact same-environment values/bytes/records/errors | §1; CE04/CE06 existing calls | P,Y |
| S01.2 | Explicit double is exactly the omitted selection, including trace/settings/source fields | §1; stationary and extended old calls | P,Y |
| S01.3 | Old PreparedBands and AcquisitionBands remain c128-only; c64 masquerading rejects | §1; both old schemas | B,P |
| S01.4 | Existing full-debug/summary composition keeps its inherited projection/retention guarantees | §1,6; existing default composed controls | P; D |
| S02.1 | Explicit single plus valid new record returns KnownReconstruction32 | §1,3; root facade call | B,Y |
| S02.2 | Single fixtures are directly constructible from declared coefficients without preparation history | §2,6; sparse slots with rational noise | J,B |
| S03.1 | Precision requires ordinary str; other kinds/subclasses reject first | §1,5; None/bool/nonstring/subclass | B |
| S03.2 | Unsupported precision strings reject first; no aliases/fallback | §1,5; empty/unknown/profile alias | B |
| S04.1 | PreparedBands32 with omitted/explicit double rejects, proving no dtype inference | §1; same new record, both selections | B,Y |
| S04.2 | PreparedBands with single rejects without conversion | §1; valid old record | B,Y |
| S04.3 | AcquisitionBands with single rejects even for otherwise stationary values | §1; valid old acquisition record | B,Y |
| S04.4 | An unrelated/nonrecord bands object rejects under single | §1,5; ordinary object/array | B |
| S05.1 | Constructor accepts strided and read-only exact-dtype inputs and copies logical values | §2; noncontiguous/negative-stride/read-only examples | B |
| S05.2 | Constructor arrays are independent owned C-contiguous read-only snapshots | §2; original-buffer mutation after declaration | B |
| S05.3 | Frozen metadata/provenance preserve caller pair order without authenticating lineage | §2; independently declared formulas/conversion notes | B |
| S05.4 | A directly constructed dataclass satisfying every canonical field is valid | §2; no hidden constructor token/history | B |
| S06.1 | Quadratures require ordinary ndarray, not array-like/subclass | §2,5; list/subclass | B |
| S06.2 | Quadratures require exact complex64 dtype, never implicit rounding | §2; c128/bool/object/other numeric examples | B |
| S06.3 | Quadrature byte order must be native | §2; foreign endian versus native | B |
| S06.4 | Noise requires ordinary ndarray | §2; list/subclass | B |
| S06.5 | Noise requires exact float64 dtype | §2; f32/integer/complex/bool examples | B |
| S06.6 | Noise byte order must be native | §2; foreign endian versus native | B |
| S07.1 | input_shape is an exact six-element tuple | §2; wrong container/arity | B |
| S07.2 | Each declared dimension is a nonboolean Python int | §2; float/NumPy scalar/bool examples | B |
| S07.3 | T,D,P,Y are positive | §2; zero/negative, ordinary endpoint1 | B |
| S07.4 | Z>=2, with Z1 unsupported in this schema | §2; Z2 permitted | B |
| S07.5 | X is even and >=2 | §2; odd/zero/negative, X2 permitted | B |
| S07.6 | Quadratures have exactly six axes | §2; squeezed/extra axes | B |
| S07.7 | Q is odd | §2; even slots versus odd | B |
| S07.8 | Q<=P | §2; reduced-order P allowed | B |
| S07.9 | O=(Q+1)//2>=2 | §2; O1 rejects | B |
| S07.10 | Quadrature shape matches all declared axes and half-X extent | §2; mismatched T/D/Z/Y/X axes | B |
| S07.11 | Noise shape is exactly (T,D,O), no broadcast | §2; old (D,O) and unequal axes reject | B |
| S07.12 | dxy_um is a nonboolean real scalar | §2,3; bool/complex/nonreal reject | B |
| S07.13 | dxy_um is finite before conversion | §2; NaN/infinity | B |
| S07.14 | dxy_um is strictly positive | §2; zero/negative versus positive | B |
| S07.15 | dxy_um original magnitude stays in inherited f32-component domain | §2; excessive finite magnitude | B |
| S07.16 | dz_um is a nonboolean real scalar | §2; bool/complex/nonreal reject | B |
| S07.17 | dz_um is finite before conversion | §2; NaN/infinity | B |
| S07.18 | dz_um is strictly positive | §2; dz0 unsupported, positive valid | B |
| S07.19 | dz_um original magnitude stays in inherited f32-component domain | §2; excessive finite magnitude | B |
| S07.20 | L and A are nonboolean Python ints | §2; float/NumPy scalar/bool reject | B |
| S07.21 | L,A>=1; no shrinking zoom | §2; zero/negative reject | B |
| S07.22.1 | mapping_revision requires ordinary str | §2; nonstring/subclass rejects | B |
| S07.22.2 | mapping_revision content is exactly ce04-svn307-v1 | §2; wrong revision rejects | B |
| S07.23.1 | Stored precision_profile requires ordinary str | §2; forged nonstring/subclass rejects | B |
| S07.23.2 | Stored precision_profile content is exactly single-mixed-v1 | §2; forged profile rejects | B |
| S07.24 | Provenance outer container is an immutable tuple | §2; list rejects | B |
| S07.25 | Each provenance entry is a two-element tuple | §2; wrong container/arity | B |
| S07.26.1 | Provenance keys are ordinary strings | §2; nonstring/subclass rejects | B |
| S07.26.2 | Provenance keys are nonempty | §2; empty rejects | B |
| S07.27 | Provenance values are ordinary strings | §2; opaque/nonstring/subclass rejects | B |
| S07.28 | Provenance keys are unique; caller order preserved | §2; duplicate keys reject | B |
| S07.29 | Consumer input_scale is a canonical Python float | §2; forged nonfloat rejects | B |
| S07.30.1 | Computed/consumed scale is finite | §2; nonfinite rejects | B |
| S07.30.2 | Computed/consumed scale is positive | §2; underflowed zero/nonpositive rejects | B |
| S07.31 | Consumer scale exactly equals prescribed RN64 alpha | §2; false scale rejects, not amplitude inference | B |
| S08.1 | Consumer quadratures own their storage | §2; forged shared view rejects | B |
| S08.2 | Consumer quadratures are read-only | §2; changed write flag rejects | B |
| S08.3 | Consumer quadratures are C-contiguous | §2; directly forged strided field rejects | B |
| S08.4 | Consumer noise owns its storage | §2; shared view rejects | B |
| S08.5 | Consumer noise is read-only | §2; changed write flag rejects | B |
| S08.6 | Consumer noise is C-contiguous | §2; forged strided field rejects | B |
| S08.7 | Every original quadrature component is finite | §2,5; NaN/infinity rejects before work | B |
| S08.8 | Every original noise element is finite | §2,5; NaN/infinity | B |
| S08.9 | Every noise element is strictly positive, with no extra floor | §2; zero/negative reject, finite tiny positive permitted if later operations defined | B,F |
| S09.1 | All representation arithmetic is exact Python integer arithmetic | §2; boundary products without float/fixed-width wrap | B,P |
| S09.2 | Positive declared dimensions/counts/zooms retain signed32 bound I | §2; valid neighbors where structurally reachable | B |
| S09.3 | Native X*Y*Z retains signed32 element bound | §2; byte rule cannot waive count overflow | B |
| S09.4 | Native half-volume retains signed32 element bound | §2; distinct half-storage address domain | B |
| S09.5 | Each resolved Xo,Yo,Zo retains signed32 bound | §2; exact integer enlargement | B |
| S09.6 | Output plane Xo*Yo retains signed32 element bound | §2; distinct from lookup bytes | B |
| S09.7 | Output volume Xo*Yo*Zo retains signed32 element bound | §2; independent of dtype bytes | B |
| S09.8 | D*O retains inherited signed32 count bound | §2; orders/directions | B |
| S09.9 | Q*P retains inherited signed32 count bound despite no separation | §2; declared phase count | B |
| S09.10 | Signed lifts/wrap/reflection/loop arithmetic remains representable before use | §2,4; permitted negative signed values | B,A |
| S09.11 | Cutoff ceil/truncation integers remain signed32-safe | §2,4; unsafe conversions reject | B,F |
| S09.12 | Actual flattened lookup/stencil offsets remain checked | §2,5; wide bytes never widen indices | B,F |
| S09.13 | L must be exactly f32-representable; integer nonshrinking enlarged extents remain exact | §2; nonexact integer rejects, exact L allowed | B |
| S09.14 | Aggregate c64 band copies/diagnostics satisfy actual8-byte native shape/stride extent | §2; T/D/Q axes included, no huge allocation | B,P |
| S09.15 | Aggregate per-time f64 noise satisfies actual8-byte native extent | §2; T/D/O included | B,P |
| S09.16 | Full native c64 workspace satisfies actual8-byte native extent | §2; positive shape | B,P |
| S09.17 | Each padded/inverse c64 array satisfies actual8-byte native extent | §2; actual output dimensions | B,P |
| S09.18 | Aggregate f64 image accumulator satisfies actual8-byte native extent | §2; T included | B,P |
| S09.19 | Aggregate f32 final image independently satisfies actual4-byte native extent | §2; do not infer from nominal result nbytes alone | B,P |
| S09.20 | Parameter/order arrays satisfy actual f64/c128/int64 native extents | §2; D/O axes and implicit a[d,0] storage | B,P |
| S09.21 | Coordinates and any actual plane/lookup array satisfy actual native extents | §2; actual itemsize, not historical signed bytes | B,P |
| S09.22 | Each permitted conversion/phase block satisfies actual-width native extent and block bound | §2,4; no volume promotion | P,X |
| S09.23 | Identity/provenance aggregate storage satisfies native extents with streamed hashing | §2,3; no promoted whole-array hash copy | P; D |
| S09.24 | Historical native-workspace8-byte expression uses positive <=M, no u32 byte cap | §2; crossing old cap is not itself rejection | B,P; D |
| S09.25 | Historical output-workspace8-byte expression uses positive <=M, no u32 byte cap | §2; signed output count retained | B,P; D |
| S09.26 | Historical real-output4-byte expression uses positive <=M, no u32 byte cap | §2; actual accumulator extent separately binds | B,P; D |
| S09.27 | Historical order8-byte expression uses positive <=M, no u32 byte cap | §2; prove redundancy where retained counts dominate | B,P; D |
| S09.28 | Historical lookup4-byte expression uses positive <=M, no signed32 byte cap | §2; signed plane elements/offsets retained | B,P; D |
| S09.29 | No extra signed32 aggregate T*D*Q or T*D*O storage cap is invented | §2; native aggregate bound still binds | B,P; D |
| S09.30 | Absent preparation-only padded-camera/frame/solve/off/drift counts impose no new schema restriction | §2; Q*P and D*O expressly retained | B; D |
| S09.31 | Known invalid geometry rejects before array-sized copy/hash/scan/broadcast/numerics/allocation | §2,5; tiny public backing/metadata ordering proof | B |
| S09.32 | Representation-valid geometry is not RAM/backend admission; no invented backend size cap | §2; actual operation failures retained | B,X; D |
| S09.33 | Native boundary evidence uses approved real-caller _extent plus tiny public calls and D audit | §2; positive Python-int shapes/itemsize, no new seam | B,P; D |
| S09.34 | Large-target classification/byte implication evidence never invokes huge successful fixture | §2,6; safe integer-only proof, no16GiB claim | J,B; D |
| S10.1 | Noise v[t,d,m] is indexed separately for every time | §4; T2 unequal per-time noise | F,J |
| S10.2 | Direction/order noise uses its own supplied value | §4; unequal D/O rational noise | F,J |
| S11.1 | Transfer must be actual valid OpticalTransfer | §3,5; unrelated/forged record rejects | B |
| S11.2 | Complete original table is validated, including unused extra orders | §3; nonfinite extra-order value rejects | B,F |
| S11.3.1 | Transfer source revision/hash identity obeys accepted CE03 schema | §3; forged identity rejects | B |
| S11.3.2 | Transfer layout is accepted radial/full | §3; unknown layout rejects | B |
| S11.3.3 | dkr obeys CE03 positive finite scalar/magnitude domain | §3; invalid increment rejects | B |
| S11.3.4 | dkz obeys CE03 positive finite scalar/magnitude domain | §3; invalid increment rejects | B |
| S11.3.5 | Transfer order/axis metadata agrees with the complete sample shape | §3; forged count/shape rejects | B |
| S11.3.6 | Transfer sample array retains its existing c128/ownership/read-only schema | CE03,§3; invalid used field rejects | B |
| S11.4 | At least O transfer orders required; valid extra orders unused | §3; insufficient count rejects | B,F |
| S11.5 | Complex radial tables retain complex interpolation and source values | §3,4; nonunit affine complex table | F,J |
| S11.6 | Full tables retain all-coordinate negative-x reflection/conjugation | §3,4; asymmetric complex table | F,J |
| S11.7 | Valid empirical c128 samples need not be c64-exact and are never redeclared/downcast | §3,4; accepted component1+2^-30 | F,P,J |
| S11.8.1 | CE03 radial per-order R*K retains signed32 bound | §2,3; actual source indices | B; D |
| S11.8.2 | CE03 full per-order K*Yh*Xh retains signed32 bound | §2,3; actual source indices | B; D |
| S11.8.3 | CE03 sampler plane/index/offset intermediates retain signed32 bound | §2,3; no widening from bytes | B; D |
| S11.8.4 | Transfer aggregate native c128 extents bind, without new total-order signed cap | §2,3; actual16-byte storage | B; D |
| S12.1 | All actual interpolation vertices are checked even at zero interpolation weight | §5; unsafe last lateral vertex rejects | B,F |
| S12.2 | Zero bands/modulation/damping never skips a required actual transfer sample | §4,5; paired safe and unsafe tables | B,F |
| S12.3 | Safe flattened cross-row aliases remain literal, not axis-clamped | CE03; within-allocation offsets | F |
| S12.4 | Negative wrapping occurs once with source signed-remainder/address rules | CE03; safe versus actual out-of-range | B,F |
| S12.5 | Actual stencil failure rejects whole call with ReconstructionError and OtfError cause | §5; late unsafe request | B,F |
| S13.1 | Self support is inclusive at r=R | CE04,§4; exact boundary | F |
| S13.2 | Outside-self support performs literal zero writes without sampling | CE04,§4; outside radius | F |
| S14.1 | Other signed-order support uses strict q<R | CE04,§4; equality excluded | F |
| S14.2 | Skip only the exact self direction/order pair | CE04,§4; same order other direction remains | F |
| S14.3 | Other powers retain direction-major ascending signed-order addition | §4; cancellation-sensitive unequal terms | F,P |
| S14.4 | Eligible other power has no own axial-cutoff test | CE04,§4; self z outside other cutoff | F |
| S15.1 | c0 uses ceil before inherited clipping | CE04; independently enclosed cutoff decision | F |
| S15.2 | Highest-order cutoff uses trunc(1.3*c0), including O2 | CE04; O2 distinguishing case | F |
| S15.3 | Intermediate cutoff uses trunc((1+le/lx)*c0) | CE04; O>=3 | F |
| S15.4 | Each order clips independently at floor(Z/2) | CE04; small Z/unequal cuts | F |
| S15.5 | Y1 empty traversal permits requested c0=0 damping when other operations defined | CE04,§5; no invented damping/stencil evaluation | F,B |
| S16.1 | Native inverse variance appears once in numerator and each matching power | CE04,§4; rational noise | F |
| S16.2 | Wiener is squared, added after all signed powers, with no estimator | §4; w² versus w oracle | F |
| S16.3 | Scalar sampling/powers/denominator/quotient/taper/modulation retain frozen f64/c128 order | §4; nonunit complex H/a | F,P |
| S16.4 | Round complete consumed scale once to c64 after scalar work | §4; non-c64-exact H versus early-rounding trap | F,P |
| S16.5 | Self numerator and side modulation use complex conjugates, never inverse-modulation | CE04,§4; signed/complex/zero a | F |
| S17.1 | Suppression uses physical radius in the specified helper formula | CE04; bin-normalization trap | F |
| S17.2 | Suppression radius inclusion is <= and signed negative radius bypasses | CE04; boundary/negative examples | F |
| S17.3 | Suppression off bypasses helper; default center condition remains literal | CE04; on/off and order-zero flags | F |
| S18.1 | Center damping precedes weight omission when both flags true | CE04; both flags | F |
| S18.2 | Final assembly still omits center whenever omit_order0 true | CE04; damping+omission | F,A |
| S18.3 | omit_kz0 overrides center z0 weight only, after prior branch | CE04; side order/nonzero z unaffected | F |
| S18.4 | Actually visited c0=0 damping rejects before later zero-weight/final-omission override | §4,5; origin with omit flags | B,F |
| S19.1 | Cosine taper uses shifted object radius and c[1] ellipse | CE04; unequal carrier/order | F |
| S19.2 | c[1]=0 taper uses lateral fallback | CE04; no axial division | F |
| S19.3 | rho clips only above1; rho1 uses actual cos, no hard-zero substitute | CE04; boundary | F |
| S19.4 | Taper none is exactly1 and no caller mask/callable | §1,4; accepted none | F,B |
| S20.1 | Native center multiplication follows componentwise RN32 complex product sequence | §4; nonunit complex scale | F,P |
| S20.2 | Side E+iO uses rotation then RN32 addition/product, no c128 promotion/FMA | §4; cancellation/overflow-sensitive coefficients | F,P |
| S20.3 | Reflected reads conjugate each quadrature over all three axes | CE04,§4; asymmetric z/y/x modes | F,A |
| S20.4 | Recombination uses actual reflected opposite F partner and specified RN32 half/rotation | §4; n distinct from conj(p) at same index | F,P |
| S21.1 | Odd-Y omitted center row remains bit-exact | CE04,§4; negative/signed-zero sentinel | F |
| S21.2 | Odd-Y side rows preserve untouched values except literal reflected/axial zero writes | CE04,§4; partial-row distinction | F |
| S21.3 | Y1 has no filter/recombination visits and preserves quadrature bits | CE04,§4; valid signed coefficients | F,A |
| S21.4 | Explicit zero writes use positive complex zero; untouched signed zeros are not canonicalized | §4; zero-sign observations | F,P |
| S22.1 | Positive native Nyquist lifts once to positive enlarged bin without endpoint splitting | CE04,§4; each spatial axis | A,J |
| S22.2 | Negative-x half storage reflects/conjugates all lifted coordinates | CE04,§4; side harmonic | A |
| S22.3 | Integer zoom embeds native coefficients into c64 zero padding without fftshift/checkerboard | CE04,§4; unequal L/A | A,P |
| S23.1 | Inverse is positive exponential and unnormalized, alpha consumed exactly once | CE04,§4; independent DC scale | A,J |
| S23.2 | Supplied bands use declared unnormalized forward-sum units, no phase/direction re-average | §2,4; displaced sparse modes | A,J |
| S24.1 | Carrier phase has positive sign and centered physical lateral labels | CE04,§4; negative/noninteger carrier | A,J |
| S24.2 | Carrier ramp is independent of axial position | CE04,§4; axial modes | A |
| S24.3 | Native filtering precedes carrier relocation; no interpolation-first quotient | CE04,§4; distinguishing nonunit transfer | F,A |
| S24.4 | f64/c128 complete phase ramp rounds once to c64 in bounded blocks | §4; subpixel phase/conversion error | A,P,X |
| S25.1 | c64 side product widens real part before f64 factor2 and accumulation | §4; scalar-promotion trap | A,P,X |
| S25.2 | f64 accumulator follows original direction/order addition order | §4; cross-direction cancellation | A,P |
| S25.3 | Final signed image RN32 preserves negatives, exact/near cancellation and weak signals | §4,6; no floor/clip/magnitude | A,P,J |
| S26.1 | FFT actually receives/returns c64 with fixed axes/norm/workers/default interface | §4; axes0,1,2/norm forward/workers1 | P,X; D |
| S26.2 | Band/native/padded/filtered/product storage actually remains c64 | §4; returned dtype alone insufficient | P,X; D |
| S26.3 | Derived c128/f64 phase/scale scratch respects per-purpose65,536-element limit | §4; execution block, not domain cap | P,X; D |
| S26.4 | No whole-volume c128 bulk copy/product followed by downcast or silent double fallback | §4; actual transitions and source audit | P,X; D |
| S26.5 | FFT internal precision/workspace remain unknown absent evidence | §3,4,6; I/O dtype supplies no attribution | X; D |
| S27.1 | Finite subnormal and finite-to-zero conversion/arithmetic are allowed with absolute error | §4,6; no weak-signal floor | P,J |
| S27.2 | Nonfinite/overflow at any required local primitive rejects even if later cancellation would hide it | §4,5; overflow before recombination | B,P |
| S28.1.1 | Carrier argument requires ndarray; ndarray subclasses accepted | §3; nonarray rejects; no new ordinary-array restriction | B |
| S28.1.2 | Carrier shape is exactly(D,2), without broadcast | §3; wrong shape rejects | B |
| S28.1.3 | Carrier dtype is an accepted standard real kind; byte order/strides/read-only do not narrow it | §3; bool/object/complex/extended reject | B |
| S28.2.1 | Original carrier values must be finite before f64 conversion | §3,5; NaN/infinity rejects | B |
| S28.2.2 | Original carrier components stay within f32 magnitude; nonexact/zero/negative values allowed | §3,5; no exact-f32 carrier restriction | B,A |
| S28.3.1 | Modulation requires ndarray; ndarray subclasses accepted | §3; nonarray rejects | B |
| S28.3.2 | Modulation shape is exactly(D,O-1), without broadcast | §3; wrong shape rejects | B |
| S28.3.3 | Modulation dtype is accepted standard real/complex; either byte order/strides/read-only accepted | §3; bool/object/extended rejects | B |
| S28.4.1 | Original modulation components are finite before c128 conversion | §3,5; NaN/infinity rejects | B |
| S28.4.2 | Original modulation stays within f32 component magnitude; zero/signed/complex allowed without floor | §3,5; no exact-c64 parameter restriction | B,F |
| S28.5 | wavelength_nm requires nonboolean integral kind, without truncation | §3; Python/accepted NumPy integer versus float/bool | B |
| S28.6 | Wavelength lies in1..32767 | §3; endpoints valid, outside rejects | B |
| S28.7.1 | NA requires inherited nonboolean numbers.Real kind | §1,3; valid NumPy real scalars paired | B |
| S28.7.2 | NA must be finite before conversion | §3; NaN/infinity rejects | B |
| S28.7.3 | Original NA magnitude obeys inherited f32-component limit | §3; above-limit rejects, possibly redundant with physical bound | B; D |
| S28.8.1 | NA is strictly positive | §3; zero/negative rejects | B |
| S28.8.2 | NA<=min(2,immersion), equality permitted | §3; physical upper-domain rejection | B |
| S28.9.1 | Immersion requires inherited nonboolean numbers.Real kind | §1,3; valid NumPy real scalars paired | B |
| S28.9.2 | Immersion must be finite before conversion | §3; NaN/infinity rejects | B |
| S28.9.3 | Original immersion magnitude obeys inherited f32 limit | §3; above-limit rejects, redundant bounds need no isolated case | B; D |
| S28.10 | Immersion lies in[1,2], endpoints permitted | §3; outside rejects | B |
| S28.11.1 | Wiener requires inherited nonboolean numbers.Real kind | §1,3; valid NumPy real scalar paired | B |
| S28.11.2 | Wiener must be finite before conversion | §3; NaN/infinity rejects | B |
| S28.11.3 | Original Wiener magnitude obeys inherited f32 limit | §3; excess finite declaration rejects | B |
| S28.12 | Wiener is strictly positive with no arbitrary tiny-positive floor | §3,5; w0/negative reject, small positive subject to square validity | B,F |
| S28.13 | suppress_singularities accepts bool/np.bool_, canonical bool; other kinds reject | §1,3,5; no truthiness even with zero bands | B |
| S28.14.1 | Radius requires inherited nonboolean numbers.Real kind | §1,3; valid NumPy real scalars paired | B |
| S28.14.2 | Radius must be finite before conversion | §3; NaN/infinity rejects | B |
| S28.14.3 | Original radius magnitude obeys inherited f32 limit; either sign/zero allowed | §3; negative radius is legitimate | B,F |
| S28.15 | dampen_order0 accepts bool/np.bool_, canonical bool; other kinds reject | §1,3,5; no truthiness coercion | B |
| S28.16 | omit_order0 accepts bool/np.bool_, canonical bool; other kinds reject | §1,3,5; no truthiness coercion | B |
| S28.17 | omit_kz0 accepts bool/np.bool_, canonical bool; other kinds reject | §1,3,5; no truthiness coercion | B |
| S28.18.1 | Taper accepts str/subclasses, resolves underlying content to canonical str; nonstrings reject | §1; differs from precision ordinary-str rule | B |
| S28.18.2 | Unknown taper string rejects; cosine/none accepted, power separately unsupported | §1,3; no callable/mask | B,F |
| S28.19.1 | Increment requires inherited nonboolean numbers.Real kind | §1,5; valid scalar kinds paired | B |
| S28.19.2 | Increment must be finite | §1,5; NaN/infinity rejects before mode check | B |
| S28.19.3 | Increment magnitude obeys inherited f32 limit before mode check | §1,5; excess finite declaration rejects | B |
| S28.20 | precise_taper accepts bool/np.bool_ before supported-value check | §1,5; canonical bool, nonbool rejects | B |
| S28.21 | filter_overlaps accepts bool/np.bool_ before supported-value check | §1,5; canonical bool, nonbool rejects | B |
| S28.22.1 | Explode requires inherited nonboolean numbers.Real kind | §1,5; valid scalar kinds paired | B |
| S28.22.2 | Explode must be finite | §1,5; NaN/infinity rejects before mode check | B |
| S28.22.3 | Explode magnitude obeys inherited f32 limit before mode check | §1,5; excess finite declaration rejects | B |
| S29.1 | Explicit zero increment, including signed zero, is accepted and no schedule added | §1; valid numeric ±0 | B |
| S29.2 | Exponent None is accepted | §1; no unused CE06 provenance appended | B |
| S29.3 | precise_taper False is accepted | §1; valid default-equivalent flag | B |
| S29.4 | filter_overlaps True is accepted | §1; overlap procedure unchanged | B |
| S29.5 | Explode numeric1 is accepted | §1; no exploded phase mode | B |
| S30.1 | Nonzero valid increment is unsupported in single | §1; either sign, zero bands cannot bypass | B |
| S30.2 | Any non-None exponent is unsupported in single | §1; no power/unused-exponent option | B |
| S30.3 | precise_taper True is unsupported in single | §1; even taper none cannot bypass | B |
| S30.4 | filter_overlaps False is unsupported in single | §1; no self-only alternate | B |
| S30.5 | Valid nonunit explode factor is unsupported in single | §1; zero/negative examples | B |
| S30.6 | Power taper is unsupported in single | §1; exponent cannot enable it | B |
| S30.7 | No single native2D/acquisition/drift/off/search/preparation/workflow/summary mode is silently exposed | §1,6; rejection through actual available boundary, no invented keywords | B,Y; D |
| S31.1 | Ordinary missing/duplicate/unknown Python arguments remain TypeError | §5; signature binding before domain validation | B,Y |
| S31.2 | Invalid precision precedes incompatible record/domain failures | §5 phase1; multi-invalid pair | B |
| S31.3 | Record/profile incompatibility precedes field validation | §5 phase1; incompatible malformed record | B |
| S31.4 | Bands phase precedes transfer phase | §5 phases2/3; multi-invalid pair | B |
| S31.5 | Transfer phase precedes scalar/option phase | §5 phases3/4; multi-invalid pair | B |
| S31.6 | Scalar/option fields follow fixed signature order and precede parameter arrays | §5 phase4; paired invalid declarations | B |
| S31.7 | Carriers precede modulation; originals validated before conversion | §5 phase5; mixed invalid arrays | B |
| S31.8 | All static validation precedes derived/bulk work; actual samples retain prescribed local order | §5 phase6; safe public operation-failure witness | B,F |
| S32.1 | Nonfinite/undefined derived sampling steps reject | §5; reciprocal/spacing domain | B |
| S32.2 | Source beta/betamin asin arguments outside[-1,1] reject even though unused later | CE04,§5; valid endpoints paired | B,F |
| S32.3 | Derived cutoff conversion/address failure rejects before use | §2,5; no unsafe indexing | B,F |
| S32.4 | Reciprocal noise must remain finite | §4,5; tiny positive supplied noise may fail at operation | B,F |
| S32.5 | Required Wiener square must remain finite and positive, including underflow-to-zero rejection | §4,5; valid small/large neighbor paired | B,F |
| S32.6.1 | Derived taper radius must be finite and positive | §4,5; no numeric fallback | B,F |
| S32.6.2 | Derived suppression radius must be finite | §4,5; finite signed radius retained | B,F |
| S32.6.3 | Every coordinate vector value must be finite | §3,5; no relabeling/shift substitute | B,A |
| S32.7 | Actual evaluated damping singularity rejects even if later branches/data would zero it | §5; c0=0 visited origin | B,F |
| S32.8 | Ordered powers/denominator must remain finite and denominator positive | §4,5; zero/nonfinite unresolved arithmetic | B,F |
| S32.9 | Complete scalar filter scale must remain finite before c64 conversion | §4,5; nonfinite quotient/numerator | B,F |
| S32.10 | Consumed-scale c64 overflow/nonfinite conversion rejects at conversion stage | §4,5; finite c128 does not guarantee c64 | B,P |
| S32.11 | Native coefficient multiplication/recombination intermediate must remain finite | §4,5; cancellation cannot hide overflow | B,P |
| S32.12 | Embedded c64 coefficients must remain finite before FFT | §4,5; supplied finite values with invalid derived coefficient | B,A |
| S32.13 | FFT nonfinite output rejects | §4,5; small actual transform-interface witness | B,P |
| S32.14 | Derived phase/ramp must remain finite before/after consumed rounding | §4,5; no magnitude/phase substitute | B,A |
| S32.15 | Each signed contribution and each f64 accumulator update must remain finite | §4,5; operation-stage failure | B,A |
| S32.16 | Final f64-to-f32 image overflow/nonfinite rejects | §4,5; no partial image/downcast infinity | B,P |
| S32.17 | Actual allocation failure within representable domain becomes ReconstructionError with original cause | §5; controlled tiny real allocation interface | B; D |
| S32.18 | Actual FFT/backend exception becomes ReconstructionError with original cause | §5; controlled existing transform interface | B; D |
| S32.19 | Caller interruption propagates unchanged | §5; small actual interface interruption | B |
| S32.20 | Every new domain/operation rejection retains reconstruction-domain and informative argument/profile-stage message | §5; no punctuation assertion | B |
| S33.1 | Constructor/reconstruction never mutate any caller arrays/records on success | §2,5; byte snapshots of bands/noise/transfer/parameters | B |
| S33.2 | Structural/geometry/value failure leaves all inputs unchanged and no partial result | §2,5; early failures | B |
| S33.3 | Stencil/numerical/backend/late failure leaves all inputs unchanged and no partial result | §5; operation-time failures | B |
| S34.1 | New result dataclass exact field order includes empty mode_trace before source identities then precision fields | §3; expanded x/y/z fields individually | B,Y |
| S34.2 | Image/filtered arrays have exact shapes/dtypes/layout/owned read-only independent storage | §3; f32/c64, no alias | B,P |
| S34.3 | Coordinates/parameters retain exact f64/c128 shapes and validated supplied values | §3; no fitted/rounded carrier/modulation | B,Y |
| S34.4 | Cutoff/radial metadata retain prescribed int64/Python-float types | §3; order-specific cutoffs | B,Y |
| S34.5 | Settings have exactly15 ordered keys and prescribed Python value kinds | §3; no appended CE06/precision keys | B,Y |
| S34.6 | Result source revision and six source-name/hash pairs exactly match CE04 order | §3; no acquisition history assertion | B |
| S34.7 | Result precision_profile is exactly single-mixed-v1 | §3; distinct result type | B,Y |
| S35.1 | Precision provenance has exact ordered keys and ordinary-string value schema | §3; requested/resolved/dtypes/interface/backend facts | B,P |
| S35.2 | Bands identity hashes exact validated bytes/metadata/provenance with framed-v1 encoding | §3; signed-zero/caller-provenance perturbations | J,P |
| S35.3 | Transfer identity hashes original c128 bytes/metadata, distinct from consumed scales | §3; sub-c64 perturbation changes identity | J,P |
| S35.4 | Parameters identity hashes validated carriers/modulation/settings/selection | §3; independent framed serializer | J,P |
| S35.5 | No failure precision record is fabricated; external report retains failed profile/input/stage/cause | §3,6; failed executions included | X; D |
| S36.1 | x0/input-representation error is separate from candidate arithmetic and compatibility change | §6; c64-exact coefficients/nonexact transfer examples | J,P |
| S36.2 | Sparse rational/direct-DFT references are independently enclosed before candidate trials | §6; exact roots or outward transcendental bounds | J,A,F; B |
| S36.3 | Scalar/interpolation uncertainty and once-rounded scale/ramp conversion are separate terms | §6; nonunit complex transfer | J,F,P; B |
| S36.4 | Local RN32 coefficient/recombination error uses justified component intervals including subnormal absolute terms | §6; independently formed p/n | J,F,P; B |
| S36.5 | Each accuracy-qualified FFT witness has justified fixture-specific envelope; unresolved FFT gap cannot pass | §6; no universal measured multiplier | J,A,P; B/D |
| S36.6 | f64 accumulation/final f32 rounding and cancellation condition are reported separately | §6; exact/near-zero signed output | J,A,P; B |
| S36.7 | Discrete support/index decisions need certified enclosure/equality rule; overlap is unresolved | §6; no epsilon tie substitute | J,F; B |
| S36.8 | Signed metrics/reference width/interval distance use declared nonzero signal scale, never per-pixel masking | §6; negative/near-zero samples | J,P; B/D |
| S37.1 | Exact 41-name checkout/installed facade retains all 38 original names plus constructor/new types, canonical object names and no retired aliases | §1; public import, __all__, existing migration/installed expectations | B,Y,M,W; D infrastructure assessment |
| S37.2 | Overloads preserve omitted/double old-result and literal single new-result typing; runtime string yields union | §1; old/new facade callers | Y; B/D |
| S38.1 | Real execution records matched3 fresh single-workload processes per mode/case and all failures | §6; raw/median/range | X; D |
| S38.2 | Identical declared values/setup/retained original inputs prevent asymmetric setup contamination without disclosure | §6; equivalent old-schema comparator setup accounted | X; D |
| S38.3 | Actual peak/pre-call high-water/native RSS/retained payload/runtime and live dtype transitions are reported | §6; high-water difference is not pure algorithm peak | X; D |
| S38.4 | Effective thread/backend/environment/commit/lock/generator/input identities and interference limits are recorded | §6; one numerical thread/FFTworker1 | X; D |
| S38.5 | Root grants exclusive resource/headroom window; size increases need declared finite plan, no huge success/16GiB trial | §6; unknown workspace disclosed | X; D |
| S39.1 | Documentation distinguishes finite computational qualification from physical accuracy/historical binary agreement | §1,6; no universal numeric tolerance | B; D |
| S39.2 | Unsupported stages/default migration/new ceilings or speed ratios are not claimed or silently enabled | §1,6; workflow/search/half/disk/native2D excluded | B,Y; D |

A may use public double preparation only to build a separate old-schema
omitted-versus-explicit-double compatibility control. No prepared product array
may supply single fixtures or scientific expected values. Initially passing
controls are valid; no manufactured product-red, mutation requirement, numeric
scenario cap, speculative impossible state or redundant isolated-bound case is
commissioned. A/B must report any concrete missing approved decision back to
intake rather than choosing meaning; acceptance still requires independent risk
review and the named exact checkpoint.
