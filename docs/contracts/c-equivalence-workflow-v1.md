# CE07: one explicit C reconstruction workflow

**Version 1.0. Proposed public contract. Independent complete source-contract
review is required before blind A. This source document proves no runtime.**

## 1. Authority and boundary

The owner requests CE07 on completed CE06 commit
`00ac7697231cee022dc40a1ecf2301bbb92a6490`, tree
`f687f0589ab7ce41f5cf3ec51196845cc5f75ebf`. Earlier documents' proposed
headings do not reopen the accepted CE02–CE06 baseline. This contract inherits
the [common mathematical requirement](c-equivalence-common-v1.md),
[CE07/CE08 separation](c-equivalence-rebuild-v1.md#ce07-public-workflow), and
the [complete CE06 ledger](c-equivalence-acquisition-modes-ledger-v1.md).
The companion [source map and scenario inventory](c-equivalence-workflow-map-v1.md)
is normative. Its content hashes, not SVN307 alone, identify retained source.

One new public entry composes the accepted empirical-transfer, acquisition,
parameter-estimation and known-filter/assembly stages. It returns the actual
signed image and complete stage records. Calibration is either explicitly
selected raw bead observations or an actual accepted transfer. There is no
second camera preparation, calibration fit, phase solver, optimizer, source
solver, seed search, truth input, fallback, per-result gain, registration or
rescale. A failed stage fails the whole call. Scientific choices below are
settled before implementation; source review must challenge them independently.

The reconstruction caller is ordinary single-objective, non-TIFF `sirecon`.
Empirical calibration is the separately invoked ordinary `radialft` value
mapping, not a calibration routine inside `sirecon`. The workflow explicitly
performs that preparation once when requested, then uses its transfer as the
caller-loaded table. No C executable is built, run, linked or imported. No new
decoder, reconstruction CLI, image writer, or retired API is introduced.
`reconstruct`, `reconstruct_volume`, `_otf`, `_reconstruction`, `_drift` and all
other retired scientific paths remain retired. Active drift remains the accepted
`_acquisition_drift` path. These are workflow wiring requirements, not permission
to transplant old implementations.

The supported specimen arrays remain general. Ordinary three-direction,
five-phase, three-order (D3/P5/O3) 3D and declared true 2D are required. Every
accepted CE06 phase, off-exposure, drift, equalization, fractional zoom and
filter option within its finite domain is carried through. No new count,
scenario, trace-length, fixture-size or execution budget is selected. Recovery,
resolution and historical executable agreement remain separate, unqualified
CE08 outcomes.

## 2. Exact entry and value types

Public exports from `simrecon` are:

```python
reconstruct_workflow(
    specimen, *, acquisition, optics, carrier, filtering, specimen_identity,
    transfer=None, calibration=None, transfer_identity=None,
    off_exposures=None, exposure_background=None,
    header_timestamps=None, header_timestamp_unit=None, header_phases_rad=None,
    channel_index=None, plane_policy="native",
) -> WorkflowReconstruction
```

`specimen` is a plain NumPy ndarray in `(T,D,P,Z,Y,X)` order or an actual
`RawAcquisition` with `acquisition_kind="specimen_sim"`. No path, DatasetInfo,
ImageJ file, arbitrary array protocol, masked/subclass array or prepared bands
are accepted in its place. Mappings below are finite, acyclic mappings with
string keys. Values are the documented built-in scalar/sequences/None or
explicitly named NumPy arrays/records, not callbacks or arbitrary protocols.
Each mapping has **exactly** its required and optional keys; every unlisted key
raises workflow_config, regardless of its spelling or suggested function.
There is no permissive `**stage_options` passthrough. Missing required keys
raise workflow_config. Missing required top-level arguments and unknown top-level
keywords remain ordinary Python binding TypeError. Omitted optional keys select
the stated accepted defaults and all resolved values are returned.

`WorkflowError` is public, subclasses `SimreconError` (ValueError), and has
`code`, `message`, `stage`, `time_index`, `direction_index`. The last two are
Python int or None; they identify the actual known failing context, never a
fabricated index. `stage` is one of `declaration`, `layout`, `transfer`,
`calibration`, `preparation`, `estimation`, `reconstruction`, `result`.
Exact prose and simultaneous-error precedence are unspecified. Section 10
fixes error categories and cause handling.

### 2.1 Specimen and single-channel selection

For ndarray input, the six axes above are an explicit declaration, not an
inference. `channel_index` must be None. T,D,P,Y>=1, X>=2 even. Let O be the
declared acquisition.norders, Q=2*O-1<=P. O>=2; searching 3D requires O>=3.
For native `3d`, Z>=2; native `2d` requires Z=1. Section 5 defines a separate
explicit literal stack reinterpretation. No Z or transfer-axis heuristic
selects dimensionality.

For RawAcquisition, validate its used public data/axes/kind fields. Require
explicit orientation, phase, y,x; axis names/order and shape follow the
[neutral declaration contract](raw-acquisition-declarations-v1.md#explicit-array-layout-and-kind).
Missing time inserts T=1. Missing z inserts Z=1 only for declared true2D.
Preserve an explicitly declared singleton z in provenance. Missing channel
requires channel_index=None. A present channel axis, **including C=1**, requires
an explicit integral channel_index in [0,C); select that channel once, without
averaging, summing, automatic wavelength choice or shared scientific state.
After selection, move named axes to `(T,D,P,Z,Y,X)` and insert only these
documented absent singleton axes. This is an invertible selected-coordinate
layout adapter; it performs no pixel arithmetic.

Required acquisition pitches remain explicit even with RawAcquisition. Known
x/y sampling in the selected record must equal dxy_um, both laterally; known
z sampling must equal dz_um when z is present. Unknown values impose no
comparison and do not supply a default. In particular absent z with true2D
dz_um=0 is permitted; positive 2D dz_um is an explicit workflow declaration,
not newly inferred axial sampling. Unequal known x/y pitches reject because
the selected C caller uses one dxy. Generic wavelengths and nominal phase
commands stay provenance; they are not adopted as optics or measured phases.
The workflow neither estimates them nor silently substitutes them for the
required optics/selected phase policy.

`off_exposures` is None or a plain real array `(T,D,P,Z,N,Y,X)`, N>=1, aligned
with the selected channel's canonical specimen BEFORE plane reinterpretation.
There is no extra channel axis, broadcast or implicit split of phase planes.
`exposure_background` is None or finite real `(T,D,P,Z)` detector counts in the
same original labels. Metadata vectors have the exact CE06 physical exposure
stream shape/units in section 5. All arrays follow CE06 raw/mathematical kinds,
ownership, finite-float32 raw representability and source-index limits. The
neutral declaration may preserve NaNs or wider raw floats, but science rejects
those outside its accepted input domain. This does not weaken neutral I/O.

### 2.2 Acquisition configuration: complete whitelist

These keys bind `prepare_acquisition_bands` without alternate preprocessing.
The exact domains/defaults/equations are incorporated from CE06
[section 2](c-equivalence-acquisition-modes-v1.md#2-public-entries-types-and-complete-records),
[section 3](c-equivalence-acquisition-modes-v1.md#3-exact-preparation-and-off-exposure-sequence),
[sections 4–6](c-equivalence-acquisition-modes-v1.md#4-actual-offon-fourier-combination)
and [section 10](c-equivalence-acquisition-modes-v1.md#10-validation-representation-and-operation-time-failures).

| Required key | Value |
| --- | --- |
| acquisition_mode | exactly `3d` or `2d`, explicit |
| dxy_um, dz_um | real micrometre pitches; dxy>0, 3D dz>0, 2D dz>=0 |
| norders | integral O including order0, Q<=P; no automatic output-order truncation |
| background | finite scalar or `(Y,X)` counts, signed allowed |
| lateral_zoom, axial_zoom | CE06 safe source-float L>=1 and positive integer A |
| phase_policy | exactly `uniform`, `supplied`, `steps` or `drift`, below |

| Optional key | Default / direct binding |
| --- | --- |
| flatfield_slope | None, else `(Y,X)` dimensionless multiplicative map |
| phases_rad, phase_steps_rad | None, else `(D,P)` radians / `(D,)` radians per step |
| edge_pixels | 10; safe integer width, -1 sine, below -1 bypass |
| equalize, equalize_z, equalize_time | True, False, False |
| storage_order | `direction-major`, alternatively `z-major` |
| combine_off_orders | None, alternatively CE06 integer `(O,)` selectors |
| drift_between, drift_within, fit_drift, adjust_phases | False each |
| drift_filter_fraction | 0.0; finite signed source-float selector |

Pass the top-level off/exposure/metadata arrays directly. The workflow-only
header_timestamp_unit is recorded without being passed as a new CE06 keyword.
Pass the same optics
and carrier linespacing, phase_start_angle_rad and negative_angle_step to the
accepted acquisition entry. There are no independent shadow copies of optics,
zoom, order count or phase linkage settings.

`phase_policy` is a required assertion of the ACTUAL matrix route. Resolve base
policy as steps if steps exist, else supplied if a list exists, else uniform.
If drift_within AND adjust_phases, actual policy is drift; otherwise it is base.
The asserted policy must match. Both supplied list and steps are structurally
validated even when superseded; used matrices alone need full column rank.
Steps take precedence over a list and retain the accepted D<=3 source limit;
arbitrary D explicit lists remain available. Uniform-valued supplied lists are
still supplied policy. Adjust_phases without within-drift remains inert and
recorded; it does not implicitly estimate phases. No absent phase_policy is
filled from nominal commands or a filename. The explicit value `uniform` is
the source's equally spaced matrix declaration and needs no supplied list.

### 2.3 Optics, initial carrier and estimator configuration

`optics` has exactly the required keys wavelength_nm, numerical_aperture,
immersion_index. The wavelength is the declared **detection wavelength** in
integer nm, 1..32767; 1<=index<=2 and 0<NA<=min(2,index). These are CE04/05
domains, not guesses from generic header wavelength slots. The source's
0.88 excitation/detection approximation inside filter cutoff calculation
remains unchanged. No excitation wavelength input or fitted optics is added.

`carrier` has required linespacing_um>0 in um and optional keys:

| Key | Default / meaning |
| --- | --- |
| phase_start_angle_rad | 1.57193 radians; C k0startangle |
| negative_angle_step | False; actual bool, delta=+pi/D or -pi/D |
| angles_rad | None or finite real `(D,)`; C k0angles, used for initialization only |
| search_carriers, use_time0_carriers | True, True |
| amplitude_floors | None or CE05 positive real `(O-1,)` |
| fit_all_phases | True |

The first three initial-guess fields are finite within float32 component
magnitude; linespacing's reciprocal and all derived vectors must be finite
and satisfy downstream accepted component domains. These are mathematical
binary64 evaluations, with no intermediate float32 quantization.
Compute norders_in=floor(P/2)+1 from the ACTUAL P, before any output-order
reduction. Set

`b_guess = 1/linespacing_um` for true2D, otherwise
`b_guess = 1/(linespacing_um*(norders_in-1))`.

Set theta_d=angles_rad[d] when supplied, otherwise
phase_start_angle_rad+d*delta. Initial fundamental carriers are
`b_guess*(cos(theta_d),sin(theta_d))` cycles/um. With P5/O2 in 3D the divisor
is2, not1. P7/O3 has divisor3. Do not divide a resolved vector a second time.
There is no top-level true/supplied modulation or arbitrary-vector override:
the historical main caller resolves common-magnitude guesses this way.
The lower-level CE05 arbitrary-vector and CE04 known-modulation domains remain
unchanged and supply independent known controls. This workflow always runs
the accepted estimator, including search=False's actual modulation fits.

Phase linkage uses a DISTINCT guess:
`(cos(phase_start_angle_rad+d*delta),sin(...))/linespacing_um`.
It ignores angles_rad and the 3D norders_in divisor, exactly as CE06 section6.3.
Report both vectors; never substitute estimator guesses in linked phases.

Pass initial vectors, same optics, search/reuse/floors/fit flags and filtering's
omit_kz0 to `estimate_parameters` ONCE on the complete actual bands. All CE05
[overlap/search/regression equations](c-equivalence-carrier-modulation-v1.md#exact-overlaps-and-sampling-short-circuit)
and [CE06 section7 substitutions](c-equivalence-acquisition-modes-v1.md#7-true-2d-parameter-estimation-and-public-composition)
bind. The caller forces recalcarrays=1; no exposed switch changes it.

### 2.4 Filtering configuration: complete whitelist

Required wiener is finite positive, within float32 magnitude. Optional keys
are exactly the following accepted CE04/CE06 settings:

| Key | Default |
| --- | --- |
| wiener_increment | 0.0, finite signed |
| suppress_singularities | True |
| suppression_radius_bins | 10.0, finite signed |
| dampen_order0, omit_order0, omit_kz0 | False each |
| output_taper | `cosine`; alternatives `none`, `power` |
| power_taper_exponent | None; required finite signed exponent for power |
| precise_taper | False |
| filter_overlaps | True |
| explode_factor | 1.0, finite signed |

All flags/scalars/used operations retain CE04 and CE06 section9 domains. There
is ONE omit_kz0 declaration, passed to both estimator and reconstruction. It
cannot be set differently in hidden stages. Power exponent0 is the accepted
constant1 convention, including base0; negative-at-zero is an operation error.
Precise flag precomputation is retained even with taper none; active precise
DC has no new portable convention. Finite inactive/3D/empty traversal cases
remain permitted, not a blanket precise-mode rejection.

No automatic Wiener selector exists. Compute effective full-series values
`w_t = wiener+(t+1)*wiener_increment/T_eff`, all finite and >0, BEFORE filtering.
In source order this is a preincrement, including t0. For T_eff2,wiener0.2,
increment0.2 the values are (0.3,0.4). Pass w_t to each one-time reconstruction
with wiener_increment=0; do not restart/double-step the schedule. Signed negative
increments remain allowed if every used value is positive. No time endpoint
linspace, per-channel global schedule, new noise estimate or epsilon is used.

## 3. Calibration selection and transfer declaration

Exactly ONE of transfer and calibration is non-None. Neither or both rejects
before any numerical preparation. No automatic choice of calibration id,
brightest bead, direction, time, wavelength or best result is allowed. An
accepted complete transfer is used as supplied; no renormalization or symmetry
repair is applied. It must have at least O orders, with extra orders permitted
and unused. True2D requires K=1; K=1 does NOT establish specimen true2D.
Successful calibration does not guarantee later sample stencils/fit domains.

### 3.1 Raw empirical calibration

`calibration` has exactly required raw, settings, identity. raw is a plain
real `(P_b,Z_b,Y_b,X_b)` array, explicitly one selected direction/channel/time.
settings has required dxy_um,dz_um,linespacing_um,wavelength_nm,
numerical_aperture,immersion_index, and the optional keys/defaults of
`prepare_bead_otf` ONLY: bead_diameter_um=0.12, carrier_angle_rad=0.0,
background_counts=None, background_map=None, slope_map=None,
exposure_background_counts=None, compensate_bead=True, fix_axial_axis=True,
fix_radial_from=0, cleanup_axial_bins=(0,0,0), origin_fit_bins=None,
rescale_each=False, forced_pi_shift=False, conjugate=False.

Their exact domains and operations are
[CE03 Public entries](c-equivalence-optical-transfer-v1.md#public-entries-and-value-records),
[CE03 Preparation operation map](c-equivalence-optical-transfer-v1.md#preparation-operation-map)
with [CE06 section8](c-equivalence-acquisition-modes-v1.md#8-safe-rectangular-and-z1-empirical-radialft-preparation).
All supplied settings validate, including superseded background inputs. The
selected background priority is exposure offsets, paired camera maps, scalar,
auto corners. No bead phase-list or specimen alpha is introduced.

Geometry includes even X_b>=8,Y_b>=10,Y_b<=X_b+2,Z_b>=1, odd P_b in
{1,3,5,7,9}; the tight X8/Y10 family remains valid. Specimen/prepass fixed10
still needs X,Y>=10. P_b1 requires compensation off and cannot supply O>=2
without a different actual complete transfer; missing empirical orders reject,
not duplicate. Calibration may have different pitches/shape/phase count from
the specimen. Different sampling is handled only by the accepted sampler.
Its detection wavelength, NA and index must equal the declared workflow optics
exactly; incompatible declared optics reject rather than imply physical reuse.
Linespacing/angle are explicitly the calibration acquisition's own values and
need not equal the specimen guess. Matching optics labels do not prove that
an experimental calibration is physically appropriate.

Call `prepare_bead_otf(raw, **resolved_settings)` once. Use the ACTUAL
PreparedOtf.transfer directly in preparation consumers, estimation and every
known reconstruction. Preserve all complex128 coefficients, original dkr/dkz,
order amplitudes and separate transfer provenance. NO declare_otf round trip,
complex64 conversion, axial-step rebinding, inferred single-plane header,
arbitrary PSF normalization, or old three-bead physical optimizer is allowed.
The computed value need not be exactly complex64-representable. This is CE06's
accepted direct-consumption domain, not a declaration-domain extension.

### 3.2 Accepted transfer values

`transfer` may be an actual accepted OpticalTransfer, an actual PreparedOtf,
or the explicit decoded-section declaration in section3.3. Snapshot supplied
value records into independently owned arrays with unchanged values, dtypes,
metadata and provenance, without declare_otf or quantization. A PreparedOtf is
then unwrapped without recomputation; retain its snapshot calibration diagnostics.
The SAME snapshot transfer is consumed by all stages and returned, and can also
be the snapshot calibration.transfer. This preserves input ownership without
changing the accepted computed-transfer domain. Both value
record types retain CE03/CE06 used-field validation and original source tuples.
`transfer_identity` is required for these paths, identifies the selected table
or upstream calibration, and is None on the raw calibration path. A precomputed
PreparedOtf's settings for wavelength/NA/index must match workflow optics under
the same rule as raw calibration. An OpticalTransfer has no embedded optics;
transfer_identity declares that pairing under section4.

The original `declare_otf` remains exact-complex64-representable for raw
declared samples; that rule is never imposed on a valid computed transfer.
No all-real radial assumption, forced conjugation or order0 DC normalization
is added. Zero/signed/asymmetric complex accepted tables stay permitted where
actual estimator/filter arithmetic succeeds.

### 3.3 Explicit decoded historical-section declaration

This is a VALUE adapter inside the workflow, not a binary file reader.
Its exact mapping has keys kind=`decoded-sections`, layout (`radial` or `full`),
samples, dkr_cyc_um, dkz_cyc_um, order_encoding=`combined-orders`.
samples is a finite real/complex NumPy array of shape `(S,V,U)` in physical
section,row,column order, each sample exactly complex64-representable, S,V,U>=1.
All kinds, finite/source-index/byte bounds and positive increments follow
declare_otf. The declaration asserts COMPLEX samples with real then imaginary
components, no magnitude/phase encoding or intensity conversion. It carries no
implied spatial-image meaning. Five-quadrature and incomplete/corrupt encodings
reject; no combination angle is fitted from these already-combined tables.

Resolve using EFFECTIVE specimen mode and O:

| Effective mode/layout | Exact declared binding and used order indices |
| --- | --- |
| 3d/radial | V=R,U=K; H[m,r,k]=samples[j_m,r,k] |
| 2d/radial | require V=1,U=R; H[m,r,0]=samples[j_m,0,r]; dkz must be exactly1 cycles/um |
| 2d/full | V=Y_table,U=X_half; H[m,0,y,x]=samples[j_m,y,x]; dkz must be exactly1 |
| 3d/full | K=floor(S/O)>=1; H[m,k,y,x]=samples[m*K+k,y,x]; consume O*K sections, no duplication |

In the first THREE branches j_m=m if m<S, else0, m=0..O-1. That duplicates
only absent later orders, always order0, never the last available order.
For O3,S2 the map is (0,1,0); for O3,S1 it is (0,0,0). S>O leaves later
sections unused in these branches and reported as such. In full3D the caller
divides the total sections by requested O using integer division. It consumes
sections0 through O*K-1 and leaves the remainder O*K through S-1 unused; report
those original section indices explicitly. No divisibility restriction applies.
For S7/O3, K2 gives section_map=((0,1),(2,3),(4,5)), unused_sections=(6,).
S6/O3 has the same consumed blocks and unused_sections=(). S2/O3 gives K0:
reject with workflow_representation because no axial sample exists for any
declared order, the accepted transfer requires K>=1, and the sampler cannot
form a finite in-allocation axial stencil from zero-length order storage.
Do not duplicate order0, borrow remainder sections, pad, or invent samples to
repair K0. Do not apply radial duplication to the full3D branch. An unused
declared trailing section is not a corrupt payload; actual malformed payloads
and a missing first section still supply no invented values.

For radial2D, V>1 would make an IMRdSec plane larger than the caller's R-cell
allocation; reject that decoded historical-loader profile, even if only one
conceptual row seems useful. General safe complete radial K1 value records
remain supported through section3.2 without any file-binding claim. A radialft
Z_b1 file has header (nx,ny)=(1,R), unlike the 2D loader's required (R,1).
It cannot be fed unchanged through this branch. The accepted computed transfer
route avoids that file discrepancy entirely; explicitly transposed decoded
declarations are a new asserted layout, never described as unchanged parity.

dkr/dkz are explicit decoded numbers in cycles/um. The 3D radial caller reads
header.ylen/header.xlen respectively; full3D uses xlen/zlen; 2D uses xlen/1.
No spatial MRC cell-length conversion is applied. After this exact mapping,
call declare_otf once and use the resulting record directly. Record section
map, original shape, ignored sections, declared increments and identities.
This selected adapter is the only missing-order duplication in CE07; complete
OpticalTransfer and empirical preparation never silently duplicate orders.

## 4. Source, pixel and metadata identities

`specimen_identity`, `transfer_identity` and calibration.identity share the
following exact mapping schema. Required id and intensity_unit are nonempty
strings, opaque labels. For transfer identities intensity_unit is exactly
`dimensionless-transfer`; calibration/specimen raw identity labels describe
their decoded count units. Optional files defaults to empty tuple. Each file
entry has exactly name (basename, no directory components), bytes (nonnegative
int), sha256 (64 lowercase hex characters), role (nonempty string). These are
caller-supplied content claims, not filesystem accesses/authentication. No
private absolute path is returned. Optional optics is None except a direct
OpticalTransfer identity MUST declare an optics mapping equal to section2.3.
Other paths may supply it and it must agree. No unknown identity keys.

For RawAcquisition, a known non-None intensity_unit must equal specimen_identity's
label. Its acquisition_id/calibration_id/nominal commands/original metadata and
provenance are snapshot as metadata, never interpreted as permission to choose
a calibration. Missing intensity_unit in that record is supplied explicitly by
specimen_identity. No detector-count/photoelectron conversion follows from a
unit label. Output reports that same label with processing semantics below.

Additionally compute identities of every numerical input actually supplied,
including superseded arrays. An ArrayIdentity frozen record has exact fields
name, shape, dtype, sha256. name is the argument path, shape the original tuple,
dtype is NumPy dtype.str normalized to LITTLE endian for multi-byte kinds,
and sha256 hashes C-order per-element bytes after endian normalization ONLY.
The hash excludes shape/type; those independent fields jointly identify data.
Preserve signed zero, and real/imaginary complex component order. Never round
to float32/complex64 to hash. Canonical selected specimen and optional off arrays
also receive identities named selected_specimen and selected_off_exposures.
Canonical preparation bands and returned transfers receive separate stage
identities named prepared_quadratures and consumed_transfer. These output
hashes are diagnostics, never an oracle or a raw-consistency condition on
accepted mutable stage records. Bind names in lexicographic order.

For RawAcquisition hash original record data before channel selection as
specimen.data and selected canonical data separately. For ndarray use name
specimen. Background/slope/phase/floor/angle/map/raw/offset/header arrays use
their full argument paths (e.g. acquisition.phases_rad, calibration.raw).
Precomputed transfer samples use transfer.samples or transfer.transfer.samples.
Every other supplied numerical ndarray in a public record is hashed under its
full field path as well, including specimen.nominal_phases_rad when present
and a supplied PreparedOtf's transfer.center_pixels_xyz,
transfer.background_counts, transfer.phase_angles_rad, transfer.quadratures,
transfer.normalization_factors and transfer.quadrature_angles_rad. In these
paths transfer denotes the top-level supplied PreparedOtf; its table samples
are transfer.transfer.samples. Opaque built-in original_metadata has no ndarray
leaves under its accepted neutral schema and is retained as a snapshot.
Scalar/sequences and source claims live in resolved_settings rather than an
implicit platform-dependent hash. No experimental authenticity or atomic
snapshot under concurrent mutation is promised. Inputs are copied/snapshot
before processing; no external mutable cache or later replay is read.

## 5. Layout, true2D and literal -2D semantics

plane_policy is exactly `native` or `literal-2d-stack`. Native follows
section2.1. literal-2d-stack requires acquisition_mode=2d, original Zstack>=1,
and calls the actual accepted `reinterpret_2d_planes` on selected arrays with
declared storage_order, off data and exposure background. Its returned arrays
are the ONLY raw inputs to preparation. Do not apply the helper twice.

CE06 [section3.1](c-equivalence-acquisition-modes-v1.md#31-literal--2d-regrouping-and-the-public-layout-helper)
binds the full mapping. For original (t,d,p,z,e), E=N+1, physical indices within
t are ((d*Zstack+z)*P+p)*E+e in direction-major and
((z*D+d)*P+p)*E+e in z-major. New time t_eff=t*Zstack+q reads
q*D*P*E+(d_new*P+p)*E+e. Thus original (d,z) is (d_new,q) for z-major,
or with h=q*D+d_new is (h//Zstack,h%Zstack) for direction-major.
All on/off/background identities use that same mapping. No corrected nominal
plane reorder is silently substituted. Steps/lists/angles and optics describe
NEW direction labels. Time0 reuse, equalize_time, and the Wiener denominator
use T_eff=T*Zstack; alpha uses Z_eff=1. No original-Z alpha survives.

Header vectors, when present, contain exactly
F=T*D*Zstack*P*(N+1)=T_eff*D*1*P*(N+1) entries, one selected channel, in the
declared PHYSICAL exposure stream. They are not reshuffled by this helper.
When header_timestamps is supplied, header_timestamp_unit is REQUIRED as one
Python string label with len(label.strip())>0. Preserve the exact supplied text,
including any surrounding whitespace when other characters remain; do not trim,
canonicalize or look up a conversion. Example labels are `seconds`,
`milliseconds`, `acquisition-clock-ticks` and ` ms `; this is an open label
domain, not a conversion registry. Missing/None, nonstring, empty or wholly
whitespace labels with supplied timestamp data raise workflow_metadata.
When header_timestamps=None, header_timestamp_unit MUST be None. A label without
data raises workflow_metadata even if no selected fit needs clocks. Conversely,
both None are permitted when no selected operation requires timestamps. When
an actual selected operation requires clock data, absent data still raises
workflow_metadata; a label or opaque source metadata cannot supply that data.
Supplied timestamp/phase arrays must satisfy the CE06 kind/shape/finite domains
even when unused; violations raise workflow_metadata.

Timestamps retain their decoded numerical values in that single DECLARED unit;
there is NO automatic numeric conversion. The label is workflow-only provenance,
returned as the final resolved_settings key header_timestamp_unit with its exact
str or None value. It is not inferred from RawAcquisition/original metadata,
file extension contents or header field names. The same unchanged numeric clocks
with labels `seconds` and `milliseconds` therefore give identical numerical
stage results but different explicit unit declarations. A caller meaning to
convert a clock must explicitly supply different decoded values and a matching
label; the workflow neither performs nor authenticates that conversion.

For cubic Bfit=B0+c1*eta+c2*eta**2+c3*eta**3, B0 and evaluated x/y drift
have detector-pixel units, eta and all before/after timestamp diagnostics have
the declared clock unit, and coefficient c_j has units
detector-pixels/(declared-clock-unit**j), j=1,2,3. No free intercept is fitted;
the fixed B0 and source subtraction/alias conventions remain CE06. Read the
existing coefficient matrix rows in powers1,2,3 and columns x,y under these
units, without adding unit fields to CE06 ModeEvent/AcquisitionBands or changing
their source tuples/settings. The top-level label applies to all retained
header_timestamps_after and cubic-fit sample/evaluation timestamp diagnostics.
Phases are radians already decoded from any original degrees.
CE06's first-block accesses, actual cubic
fit, alias/mutation, 2D first-OFF absolute phase base and 3D uniform base remain
literal. Do not advance metadata by t to repair the source. Missing clocks or
phase lists for a selected operation are meaningful errors; fake timestamps,
acquisition displacement estimates and dose do not supply an alternate fit.

This resolves the value mapping without claiming all original IVE file
semantics. Inspected retained headers declare ZTW=0, WZT=1 and describe their
axis precedence, and expose IMAlZWT/IMPosnZWT prototypes. They do not establish
the effective linked library's conversion, seek, extension-schema or header
rewrite implementation. Historical byte-for-byte -2D file routing through
those external routines remains unsupported. Explicit decoded layouts above
are supported; their non-nominal direction-major regrouping must be visible
in output mapping and documentation.

## 6. Exact scientific order and consumption

After complete structural validation, snapshot/resolve declarations and initial
vectors, map optional literal2D layout, and resolve the one selected transfer.
This is static/value work; raw calibration, when selected, completes ONCE before
specimen preparation, as an explicit radialft->sirecon composition.

The scientific caller order for each effective time is:

1. Establish positive effective Wiener; perform requested drift prepass on RAW
   selected data and current camera state, then the actual selected 3D cubic
   within fit. Prepass uses background only, fixed10, middle substack, and its
   literal first-OFF handling. No standalone generic shift replaces it.
2. In d,z,p traversal load each off frame before on, applying sentinel and
   persistent maps to EACH frame, sum off (never average), use preceding ON
   extra background on off loads, then current ON extra background. Edge on
   SUMMED off and on; selected equalization with independent anchors (off
   only N>1); unnormalized negative lateral transforms.
3. Actual within2D estimation/fit where selected; positive Fourier translation
   on both on/off; linked phases if selected, then used separation matrices,
   scalar variance factors and separation except the stored raw Nyquist pair.
   Selected Fourier off combination repeatedly addresses plane0. No variance
   update or alternate real-space combine. Only on bands get the 3D axial
   forward transform and subsequent selected between-direction correction.
4. Consume those ACTUAL bands/noise in the estimator, source t,d order. Searching
   ordinary3D uses pair02, true2D01; coarse strict peak/parabolas then one
   angle and magnitude search with literal tie/stale bracket/frozen overlaps.
   Known/reused carriers fit (0,b) at every current time. 2D searched later
   fits use adjacent pairs; both 2D branches apply cumulative products before
   floors/phase policy. 3D never applies those products. No time0 modulation
   replay or true-parameter bypass.
5. After all directions' parameters are resolved for this time, precompute
   requested precise sector boundaries; native filter uses ALL directions'
   current carriers/modulations, current noise factors and w_t squared.
   Filter each native band before zero-filled embedding/inverse/assembly.
   Apply accepted self/other inequalities, masks, taper/suppression, reflected
   partners and positive Nyquist, then assemble signed real output.

An accepted stage API may batch preparation across all times, then estimation
across all times, because their state recurrences are internal and filtering
does not feed back into either recurrence. This is a dependency-preserving
evaluation of the caller, not permission to reorder edges/equalization/drift/
separation or to refit. On any failure the workflow returns no result; no
partial time success becomes public. The explicit workflow event ordering below
records the actual PUBLIC stage calls, while retained stage traces carry the
source-operation order within each stage. It must not pretend batched calls
were interleaved C executions.

The actual accepted calls are: optional reinterpret_2d_planes; optional
prepare_bead_otf or declare_otf; ONE prepare_acquisition_bands; ONE
estimate_parameters; and ONE reconstruct_known per effective time. No unused
equivalent primitive discharges a public-output obligation.

For each t form a one-time AcquisitionBands value using CE06 section7's
prescribed slicing: quadratures/noise and ALL time-indexed diagnostics t:t+1,
input_shape T->1, trace/sentinel events select t and relabel to0, retain the
first D*Z_eff*P*E header entries where needed for shape and unchanged final maps,
sampling, alpha, source identity and resolved preprocessing. Do not replay raw
data or run preprocessing again. The helper value's declared header vectors
do not trigger new drift. Call reconstruct_known with ESTIMATE.carriers[t],
ESTIMATE.modulation[t], the SAME actual transfer and optics and w_t with
increment0; all other filter options are exactly section2.4. Stack its image
and filtered quadratures without additional arithmetic. The complete original
AcquisitionBands and EstimatedParameters remain in the result. Per-time known
records retain their own one-time labels/settings; the top-level result maps
each record explicitly to original effective t.

Estimator output provenance remains the CE05 six-file tuple and EXACT thirteen
keys plus two acquisition settings in CE06 section7. AcquisitionBands retains
the ten-file identity. No workflow union, extra key, ten-file substitution or
new dtype repair changes either. Transfer and KnownReconstruction keep their
own accepted source tuples. Original-square/standalone inputs keep historical
qualifications; CE06-specific dtype repairs are not generalized here.

## 7. Output, coordinates, units and diagnostics

`WorkflowReconstruction` is a frozen value record with EXACT fields:

| Field | Meaning |
| --- | --- |
| image | owned read-only float64 `(T_eff,A*Z_eff,L*Y,L*X)`, actual signed stacked image |
| x_um,y_um,z_um | independent owned read-only float64 coordinate vectors |
| intensity_unit | Python str, exact declared specimen count-unit label |
| intensity_semantics | exact string `C-scaled-camera-corrected-equalized-phase-reconstruction` |
| bands | actual complete AcquisitionBands returned by the one preparation call |
| parameters | actual complete EstimatedParameters returned by the one estimator call |
| transfer | actual consumed OpticalTransfer, preserving its accepted samples/metadata |
| calibration | PreparedOtf on raw/precomputed empirical path, else None |
| layout | TwoDPlaneInputs on literal2D path, else None |
| reconstructions | immutable tuple of T_eff actual one-time KnownReconstruction records, order t |
| initial_carriers_cyc_um | owned read-only float64 `(D,2)`, actual source-resolved fundamental guess |
| phase_linkage_carriers_cyc_um | owned read-only float64 `(D,2)`, section2.3 distinct phase guesses |
| effective_wiener | owned read-only float64 `(T_eff,)`, full-series schedule |
| input_identities | immutable tuple of ArrayIdentity records, lexicographic name order |
| source_declarations | immutable named-value tuple specified below |
| resolved_settings | immutable named-value tuple specified below |
| trace | immutable tuple of WorkflowEvent records below |
| limitations | immutable tuple of fixed claim-limit strings below |
| source_revision, reference_sha256 | `SVN307`, ten-file CE06 tuple in ledger order |

The top-level source tuple identifies composed mathematics; extra static header
pins belong to the source map and are not appended to inherited stage tuples.
Output arrays do not alias caller inputs. Top-level image/coordinates/initial
vectors/schedule do not alias stage arrays or each other. Stage records retain
their accepted ownership: bands.quadratures/noise stay writable, stage diagnostics
stay read-only, no duplicate recomputation or deep-freeze changes them. The
top-level transfer is the same accepted value consumed by all numerical stages;
it can also be calibration.transfer. Explicit nesting of the same immutable
transfer is permitted. Input descriptors/metadata/config remain unchanged.

Xo=L*X,Yo=L*Y,Zo=A*Z_eff. Coordinates are exactly
x[j]=(j-floor(Xo/2))*dxy/L, y[i]=(i-floor(Yo/2))*dxy/L,
z[h]=(h-floor(Zo/2))*dz/A, in um. No fftshift/checkerboard changes image indices.
Positive lateral phase uses these centered x/y labels; transforms retain
first-sample origins. True2D with A>1 transforms ONLY plane0; later planes stay
zero, including when z labels are positive-pitch values. True2D dz0 gives all
zero z labels and claims no physical axial sampling. No smaller-pixel resolution
claim, origin registration or plane replication follows.

Scale is alpha=1/(X*Y*Z_eff*L^2*A*D) BEFORE specimen transforms. Uniform specimen
separation has no 1/P; bead separation does. The inverse is unnormalized and
side orders contribute 2*Re(u_m*exp(+2*pi*i*explode*m*k0 dot r)). Filtering uses
w_t^2, conjugated transfer/modulation, scalar inverse variance in numerator and
powers, native masks and taper before relocation. No subsequent phase/direction
division, gain matching, positivity or mass calibration occurs. `intensity_unit`
is a traceable input count-unit label under these operations, not object mass
or an assertion that image voxel sums equal raw counts.

source_declarations keys, in order: specimen_identity, transfer_identity,
calibration_identity, selected_channel, raw_acquisition_metadata,
decoded_transfer_binding. Absent alternatives are None. selected_channel is
None or the selected original integer; raw_acquisition_metadata snapshots all
public RawAcquisition non-data fields (array nominal phases become immutable
nested floats); absent for ndarray. Identity mappings and remaining nested
metadata are independent value snapshots, with built-in mappings/sequences
converted recursively to immutable tuples (mapping keys sorted); bytes/string/
None/numeric leaves retain type. decoded_transfer_binding is None or the tuple
of keys original_shape, layout, effective_mode, section_map, unused_sections,
dkr_cyc_um, dkz_cyc_um in that order. For full3D section_map is O tuples of
K original section indices; other branches O original integer section indices.

resolved_settings keys, in order: acquisition, optics, carrier, filtering,
plane_policy, original_shape, effective_shape, norders_in, phase_policy,
calibration_selection, header_timestamp_unit. The final value is the exact
declared string or None from section5; it labels clocks and fitted coefficient
units without modifying any inherited stage schema. The four configuration
values are immutable tuples of keys in the tables' listed order, required keys
first then optional keys.
All defaults appear. acquisition arrays become nested immutable numeric tuples,
including map background/slope; None stays None. Optics uses wavelength,NA,index
order. Carrier uses linespacing then its listed optional order. Filtering uses
wiener then its listed optional order. Types are Python float/int/bool/str/complex
as appropriate, not repr strings or memory addresses. original/effective_shape
are six-int tuples AFTER selected-channel canonicalization/before and after
layout. norders_in=P//2+1; phase_policy is actual section2.2 policy;
calibration_selection is `raw-beads`, `prepared-otf`, `accepted-transfer` or
`decoded-sections`. Actual per-section phases/matrices, fitted carriers/gains,
camera state and final consumed filtering settings remain in the stage records,
never replaced by declared guesses in these diagnostics.

WorkflowEvent is frozen with fields kind, stage, time_index, details. details
is an immutable ordered tuple of named values; time is None for whole-stage
calls and effective t for reconstruction calls. Event kinds, in actual call
order, are declaration (selected_channel,original_shape), layout (plane_policy,
effective_shape), transfer (selection,consumed_transfer_sha256), preparation
(input_scale,phase_policy), estimation (branches), reconstruction per t
(effective_wiener,parameter_time_index), result (output_shape). stage matches
the named stage (declaration/layout/transfer/preparation/estimation/
reconstruction/result). Emit an event only after that operation succeeds.
On failure no partial trace/result escapes. Stage records retain every accepted
ModeEvent/overlap/search/filtered-array diagnostic, finite values and source
ordering; no text logs or extra fitting operation substitutes for them.

limitations always contains these strings in order:
`mathematical-source-target-only`, `historical-binary-agreement-unqualified`,
`recovery-and-resolution-unqualified`, `selected-channel-independent-state`,
`external-IVE-file-binding-unqualified`, `input-unit-label-not-specimen-mass`.
Append `literal-2d-stream-regrouping` for that policy, then
`true2d-extra-axial-planes-zero` for true2D A>1, then
`true2d-axial-pitch-undeclared` for true2D dz0, as applicable. These are honest
claim limits on a fully finite success, not unavailable numeric outcomes.

## 8. Neutral file/value adapters and unsupported file outcomes

No extra file decoder is necessary for this workflow. The existing
[MRC conversion contract](mrc-conversion-v1.md#public-python-responsibilities)
already supplies explicit decoded uint16/float32 spatial-image planes and named
coordinates. A caller composes inspect -> harmonize(explicit config) -> read
with an explicit full plane interval, reshapes according to the descriptor,
then declare_acquisition with explicit specimen kind/axes/sampling/count-unit
declarations -> reconstruct_workflow. Existing adapters do not initiate an
automatic full read. The workflow pure-array memory promise is separate from
streaming conversion's bound.

For a no-off acquisition, canonical neutral planes have index
((((t*C+c)*D+d)*P+p)*Z+z); their pixels are exactly the selected specimen
at [t,d,p,z,y,x]. Source plane_axes/shape can differ; public read owns that
declared reordering. Original source order must still be declared separately
as acquisition.storage_order for source drift/metadata semantics and literal2D.
Off data/metadata must be explicitly decoded/selected/split under CE06's
physical stream formula; RawAcquisition does not gain a switch-off axis.
An opaque extension is never reinterpreted as clocks/background/phases or a
clock unit. Explicit decoded clocks require the separate top-level unit label;
pixel and numeric timestamp values receive no unit-dependent conversion here.

File identity claims can include a caller-computed complete file hash plus
basename/size. DatasetInfo's size/mtime/header hash remain its weaker public
source checks, not a complete payload hash. Include its original header/config/
provenance in RawAcquisition.original_metadata when desired, preserving opaque
values without new interpretation. Reading errors/source_changed remain the
neutral adapter's errors; they occur before this pure-array operation. A
provided complete file digest is a declaration, not an added file access.

Complex legacy OTF mode4 is outside the neutral spatial reader; it cannot be
read as intensity or made supported by overriding data_kind. CE07 accepts an
explicit already-decoded section declaration or accepted transfer value, with
section3's exact units/layout/identities. It does not certify original binary
complex packing, IMAlCon semantics, extension decoding, source file swapping,
or unobserved external IVE library behavior. The inspected headers' struct and
complex type declarations alone cannot prove that ABI/codec. A request to feed
such a path directly is an unsupported-input declaration with this reason,
not an invitation to install a new decoder or silently call another tool.

Camera correction files' caller meaning is first background plane then
multiplicative slope plane of matching X/Y (helpers.c:822–854); this workflow
accepts the explicit decoded maps only. Exposure-background extension field3,
five-float drift headers and degrees->radians are explicit decoded declarations,
not a schema inferred from extension byte counts. The source fallback creates
timestamps but no phaseAbs; it remains unsafe and is not adopted.

Historical multichannel shared-state execution is unsupported as one workflow
call. Source loops time then wave, increments a global Wiener per wave/time,
shares k0 between waves at later reuse times, and camera/metadata state across
waves; equivalent independent per-channel calls are NOT promised. CE07 selects
one declared channel and starts one state recurrence. Multiple explicit calls
remain possible with independently declared calibration/settings/identities;
their outputs cannot be labeled shared-multiwave parity. No implicit channel
mixing, transfer reuse or wavelength substitution occurs.

[ImageJ export](imagej-export-v1.md#public-interface) remains an all-settings
viewing copy of a harmonized original spatial source. It does not accept this
reconstruction result or transfer arrays. Existing modern MRC writing likewise
remains its file-source neutral contract. No output file/report is fabricated.
The public result arrays/coordinates/units are the CE07 output.

Save-aligned/save-separated/save-overlap source flags exit before final
reconstruction (sirecon.c:891–913). They are not success modes here. Existing
returned stage diagnostics supply observability. Filenames/debug-early-exit
keys are NOT in any public mapping schema and therefore raise workflow_config,
just like every other unlisted key. No reserved unsupported-key vocabulary or
new debug/source-flag API is added. Model replacement, padding to a different Z,
Bessel, two-objective/I2M, standalone otf2d/wiener2d and alternate TIFF builds
keep their documented ledger outside-support/unsafe reasons; a key purporting
to request one is still an unlisted-key configuration error. Recognized public
inputs/options that actually select an unavailable/unsafe existing branch use
workflow_unsupported as section10 specifies.
No old fullscene/RA15 run or unrequested feature is authorized.

## 9. Independent public-output proof

The [source map](c-equivalence-workflow-map-v1.md#3-equation-and-caller-map)
binds each operation to independent proof. Stage equations are reused by exact
section reference, but the NEW selection/layout/initialization/time consumption
and metadata rules above require independent end-to-end assertions.

First freeze independent known-parameter controls through accepted preparation,
transfer sampling and reconstruct_known. Use finite raw observations and exact
small linear systems/finite Fourier sums to establish signs, scale, support,
centering and filtering. Then invoke reconstruct_workflow, and independently
derive its ACTUAL finite estimator outputs and final image. Passing true
modulation around the estimator, asserting mocks/call counts, or comparing only
to a hand-composition of production stages supplies no scientific oracle.
Public-stage composition comparisons can supplement independent algebra.

Required controls include general D3/P5/O3 with nontrivial camera/unequal-sum/
phase effects; actual empirical raw->transfer->specimen->fit->image with a
computed non-complex64-exact coefficient; declared complex radial/full tables;
true2D; noninteger carriers; asymmetric signed modes/displaced points and
positive Nyquist; actual selected drift/off/phase composition; multiple times
with reused carrier but DIFFERENT freshly fitted modulation and Wiener; literal
direction-major regrouping versus z-major nominal planes; source initialization
under reduced O; native filtering before relocation, rather than an
interpolation-first quotient.

Full3D decoded-section composition must include S7/O3 and S6/O3 inputs whose
first six explicitly labeled sections agree. Both resolve K2 and identical
consumed transfers/images under the same finite specimen/settings; S7 reports
unused(6,), and its original samples identity still includes that supplied
trailing section. Altering its finite values leaves consumed math unchanged.
Keep full3D S2/O3 K0 rejection separate from radial/2D S2/O3 duplication and
from complete/empirical records' missing-order errors. All supplied decoded
samples still receive the declared input-domain validation; unused-section
status is not permission to fabricate missing bytes or skip that validation.

Clock-dependent public compositions must declare a unit and independently check
that first-block reuse/alias/mutation and polynomial coefficients retain their
unchanged numerical meaning. Compare equal numeric clocks under two different
nonblank labels: values, coefficients, fitted displacements, prepared bands,
parameter fits, image and numeric array identities agree, while the final
workflow unit label differs verbatim. Include seconds, milliseconds and custom
labels without adding a conversion algorithm. Section10's single-invalid
clock/data/key examples and WF101–WF111 bind alongside these positive proofs.

The historical hidden-fit-path counterexample must be identifiable from PUBLIC
inputs and predeclared mathematics: choose independently specified asymmetric
calibration observations and unequal complex order response, valid CE06
conditioning/support, nontrivial specimen camera/phase state, and a finite
noninteger carrier case. The expected transfer and finite search are computed
without a physical bead/pupil optimizer. Show a signed spatial or Fourier
coefficient on which replacing the empirical table, using a hidden source fit,
ignoring estimator modulation, or relocating before filtering gives a different
answer beyond the independently derived bound. Do not execute retired code to
get that counterexample. It tests the documented failure CLASS; claiming a
measured comparison to a particular historical executable needs separate data.

Tolerances are conditional and predeclared BEFORE product discrepancies.
Inherit CE06 [section12](c-equivalence-acquisition-modes-v1.md#12-independent-numerical-obligations-and-bounds-before-implementation)
and CE05 finite decisions. For every concrete control record input representation
error, operation counts, reduction absolute sums, transform/observer bounds,
matrix/regression conditioning, safe stencil/support/threshold margins, peak/
strict-improvement gaps and phase-ramp sensitivity. For u=2^-53 use
gamma_n=n*u/(1-n*u) where n*u<1 to bound scalar sums, plus separately justified
complex/transcendental/backend errors. Propagate transfer/fit errors through
native denominator and unnormalized assembly; don't reuse an intermediate
epsilon for the final image. Positive Wiener gives a denominator lower bound
w_t^2 when weights are nonnegative. Include observer error and cancellation;
use absolute bounds near zero and independently justified relative bounds
elsewhere. Exact layout/hash/type/error assertions need no numeric tolerance.

Near decision boundaries characterize sensitivity explicitly; no universal
binary32/binary64 decision equivalence is asserted. A different finite search
cannot pass by a loose image tolerance. Preserve unsuccessful recovery cases;
do not choose favorable seeds, alter data, refit per-result gain/registration,
change tolerances after observing errors or relax source domains to pass.

### 9.1 Explicit finite raw-to-fit-to-image controls

These two source-derived examples fix an end-to-end expectation without running
a product or a historical executable. They supplement general empirical/search/
drift controls, rather than restricting supported arrays to one fixture.

Take T=D=1,P=3,O=2,Z=2,Y=2,X=4, 3d, dxy=dz=1um,L=A=1,
background0, no slope/offset/off/drift, edge0, equalize=False, phase_policy
uniform. Every voxel of raw phases0,1,2 has respectively counts (6,3,3), all
exact float32 values. Optics wavelength500nm,NA=index1. Carrier linespacing8um,
start angle0, search=False, fit_all_phases=True, no floors. Filtering wiener1,
increment0, suppression/dampening/omission off, overlaps on, taper none,
precise=False, explode1. Declare radial transfer shape(2,8,2), dkr=0.25cycles/um,
dkz=0.5cycles/um. In the first example every sample is1.

Alpha=1/16. Corrected raw DCs after the finite transform are (6,3,3), so
separated B0=12,E1=3,O1=0 in ideal real arithmetic, with all other frequencies
zero, including the unseparated x-Nyquist. P//2=1 gives kguess=(1/8,0).
The overlap axial cutoff clips to0, and lateral overlap nonzero values are
only DC. Its spatial arrays are constant Oa=12/sqrt(2), Ob=3/sqrt(2).
Let A0=1+sqrt(2), and

`mu = (exp(-i*pi/2)+exp(-i*pi/4)+1+exp(i*pi/4))/4
    = (A0-i)/4`.

The known-vector regression has SX=1152,SY=72,C=288*mu, so the ACTUAL fitted
forward modulation is `a=mu/4=(A0-i)/16`, not the raw harmonic ratio1/4.
All auxiliary regression quantities have finite defined unequal-energy
denominators. No floor/phase replacement occurs. At native DC center/side
filter denominators both equal `h=2+2*abs(a)^2`, since all signed partner
distances0,1/8,1/4 are strictly inside R=1/2. Filtered center is12/h and
filtered positive side is3*conj(a)/h. Axial filter cutoffs are0.
With output x labels(-2,-1,0,1)um, the image is independent of y,z and equals

`f = (12 + (3/8)*[1,A0,A0,1]) / (2+(2+sqrt(2))/64)`.

This checks raw correction/alpha, specimen phase factor, native unnormalized
transforms, ACTUAL modulation regression, denominator powers and centered
assembly in one public result. It does not require a fitted-carrier search
to be well conditioned on a constant spatial field. Floating residuals from
trigonometric separation remain covered by a predeclared propagated bound;
the runtime must not zero them to force the ideal equations.

For a discriminating complex-table variant, keep every input above but set
H1[r,k]=1+i*r at BOTH axial cells, r=0..7; H0 remains1. These are accepted exact
complex64-representable declared samples, with no imposed realness or radial
symmetry repair. The actual samples H1(1/8)=1+i/2 and H1(1/4)=1+i differ.
The independent overlaps are Oa=8+4i, Ob=3/sqrt(2), with SX=1280,SY=72 and

`a = 3*(2-i)*mu/(20*sqrt(2))`.

Center denominator is `h0=2+(5/2)*abs(a)^2`; side denominator is
`h1=2+3*abs(a)^2`. Thus at each of those centered x labels the image is

`f(x) = 12/h0 + 6*Re(conj(a)*exp(i*pi*x/4))/h1`.

The two different denominators follow from native transfer powers at0,1/8,
1/4, not a common idealized quotient. Replacing this table by its magnitude,
a fitted all-real response or a normalized unit response changes overlaps,
fitted phase and final image; substituting the raw1/4 factor also changes it.
Record the signed coefficient/image difference and a conditional bound derived
from these finite values before a product run. This is an explicit hidden-fit/
transfer-substitution discriminator on public inputs; a separate raw empirical
calibration version is still required by WF006/WF009/WF096. These two controls
are NOT CE08 physical specimen recovery or resolution experiments.

## 10. Validation, finite failures and representation

Complete schema/type/shape/scalar/selector/source checks precede numerical
preparation. Detect structural unsafe mode combinations before reaching their
source operations. Every supplied array validates, including superseded phase/
calibration options. Validate each actual transfer stencil at execution, all
zero-weight vertices included; no speculative all-frequency stencil restriction
rejects a valid short-circuited path. No arbitrary condition-number/noise floor
or minimum signal is added. Full-rank but unresolved arithmetic is an operation
error. Finite diagnostics required by the accepted numeric contracts must be
finite even when the main caller discards their values; undefined printf-only
reciprocals remain outside numerical acceptance as CE05 specifies.

All CE06 section10 signed32 products/casts/indices, explicit unsigned32 main
workspace bytes, signed32 lookup bytes and required 64-bit native intp shape/
stride/byte bounds bind, including new aggregate image/identity/metadata/trace
representations. Counts are integral, not bool; flags actual bool. Raw values
are standard integer/float16/32/64 exactly finite-float32 representable. Maps/
phases/clocks/angles/other mathematical inputs use binary64 within inherited
source-float magnitude domains. No extended-precision/object/boolean/complex
raw samples. No task-level memory cap, out-of-core promise or latency bound.
Hashing may stream bytes but scientific operations own full arrays. Preserve
caller NumPy error settings; handled errors must not produce a successful
nonfinite result or suppress unrelated warnings. Interruption propagates.

| WorkflowError code | Distinct rejected outcome |
| --- | --- |
| workflow_config | missing/unlisted mapping key, wrong mapping/schema, invalid mapped scalar/array type, shape or finite value, flag/policy/enum/domain constraint; includes missing optics keys and all debug/filename/source-flag keys absent from the exact schemas |
| workflow_input | invalid specimen/RawAcquisition/accepted record, axis/kind/base shape or raw sample domain; invalid top-level off/correction-offset array or channel selection; invalid calibration.raw/decoded samples or inherited record provenance |
| workflow_metadata | conflicting otherwise-valid declared pitches/count units/optics; missing/invalid selected clock/phase data, supplied clock/phase array kind/shape/finite domain or clock-unit declaration |
| workflow_selection | neither/both transfer alternatives, transfer_identity absent when required or supplied on raw calibration, insufficient complete/empirical orders or incompatible positive K with true2D |
| workflow_unsupported | explicitly recognized path/file-descriptor input requiring unavailable decoding, or recognized public option combination selecting a structurally unavailable/unsafe source branch; never a category inferred from an unlisted key's spelling |
| workflow_representation | unrepresentable source/native extent/index/cast/byte count, unsafe table vertex/decoded plane allocation, or full3D decoded quotient K0 with no axial sample/stencil |
| workflow_operation | zero divisor, used singular matrix/cubic/regression, undefined polar/phase/floor, nonfinite correction/FFT/fit/filter/assembly/diagnostic, stagnant/nonfinite search, unresolved numerical backend |

These are rules for SINGLE-invalid inputs. Unspecified simultaneous-error
precedence does not permit choosing a different code for any of these cases.
Apply the following schema distinctions throughout sections2–8, including
their inherited scientific-domain checks:

- Python binding first: omit a required top-level optics argument or pass an
  unknown top-level filename keyword -> TypeError. Passing optics={} instead
  reaches the mapping schema and gives workflow_config for its missing keys.
  No WorkflowError code replaces ordinary signature errors.
- All missing/unlisted keys in acquisition, optics, carrier, filtering,
  specimen_identity, transfer_identity, calibration, calibration.settings,
  calibration.identity, decoded-transfer declarations and nested identity/file/
  optics mappings are workflow_config. This includes conditionally required
  identity optics for a direct OpticalTransfer. Wrong mapped scalar kinds,
  semantic domain/range (such as positivity), flags, enums, mapped numerical-array
  kind/shape/nonfinite value,
  identity fields and phase-policy assertion also use workflow_config.
  For example missing optics.wavelength_nm, filtering.save_separated=True,
  specimen_identity.filename="x", transfer.order_encoding="five-quadratures", and
  acquisition.phases_rad of wrong shape each give workflow_config. No reserved
  source/debug key is recognized. A complete valid mapping with all other
  inputs in domain is the positive counterpart.
- A required field that exists with a syntactically/domain-valid value can
  conflict with another valid declaration: unequal known RawAcquisition x/y
  pitches versus dxy, unequal known count-unit labels, or calibration/identity
  optics versus workflow optics -> workflow_metadata. A malformed optics scalar
  or absent optics mapping key is workflow_config, not a metadata conflict.
  A missing/invalid header_timestamp_unit or clock/phase array is ALWAYS
  workflow_metadata under section5, even when the array is supplied but unused.
  This top-level metadata rule does not classify acquisition.phases_rad as a
  decoded header vector: that mapped phase-design array follows workflow_config.
- Wrong base shape/kind/dtype/nonfinite or inexact-float32 raw samples for
  specimen, off_exposures or calibration.raw -> workflow_input. RawAcquisition
  invalid used fields/provenance, unsupported scientific raw representations,
  odd raw X, wrong native mode/Z pairing, empirical geometry outside its
  accepted envelope, bad channel_index and top-level exposure_background
  array validation also use workflow_input. Wrong decoded transfer.samples
  array rank/kind/finite/complex64-exact sample domain is workflow_input;
  its mapped layout/kind/order_encoding/increment fields follow workflow_config.
  This samples exception is the explicit pixel/table input, not a configurable
  phase/floor/map parameter. Accepted records with invalid inherited used
  fields/source tuples give workflow_input, not an identity-mapping schema code.
- None/both transfer alternatives or wrong transfer_identity PRESENCE selects
  workflow_selection. Once an identity mapping is present, malformed/missing
  keys are workflow_config and valid conflicting optics are workflow_metadata.
  Complete/empirical Otable<O and true2D positive K!=1 are workflow_selection.
  Full3D decoded S<O instead gives workflow_representation for quotient K0;
  it is not a complete-table missing-order rule. Radial/2D decoded S<O remains
  its permitted order0 duplication. Wrong order_encoding is workflow_config.
- Field domains still bind even if a source CLI might route the invalid value
  elsewhere: filtering.wiener=0 or a declared effective sequence with w_t<=0
  gives workflow_config, not an automatic-Wiener mode. An overflowing arithmetic
  step while forming an otherwise valid declared sequence is workflow_operation.
  Similarly O<2 or searching3D O<3 gives workflow_config; an invalid enum such as
  acquisition_mode="1d" or an inconsistent literal2D/3d policy declaration is
  workflow_config, not an unsupported new scientific mode.
- Recognized path strings/Path values or actual DatasetInfo supplied as specimen,
  transfer or calibration.raw would require a decoder outside this pure-array
  entry and give workflow_unsupported. Arbitrary other wrong object types use
  workflow_input. A valid public drift option combination that reaches source
  uninitialized-reference/underallocated/null-allocation routing, such as fast
  D>1 drift, 3D-within D<=3, or within2D N0, gives workflow_unsupported with the
  exact ledger reason. Missing required clock/phase DATA is workflow_metadata;
  source fit/phase flag allocation conflicts are workflow_unsupported even if
  clock arrays are present. Merely supplying a multi-channel RawAcquisition
  without channel_index is workflow_input. There is no public shared-wave option;
  an invented shared_wave key is workflow_config, not workflow_unsupported.
- Source/native integer/byte/index representation bounds after valid basic
  types/shapes, actual unsafe sampler/empirical diagnostic accesses, radial2D
  decoded V>1 plane-allocation mismatch and full3D decoded K0 use
  workflow_representation. A used singular phase/cubic design or its unresolved
  factorization, data-dependent zero sums/energies, actual precise zero-polar
  query, selected negative-power-at-zero taper, or finite-operation failure
  uses workflow_operation. A valid repeated-phase full-rank design or inactive
  precise mode is not rejected merely to avoid that distinction.

Concrete clock positive/error controls use valid CE06-sized arrays and all
other arguments in domain: timestamps with `seconds`, `milliseconds`, custom
`acquisition-clock-ticks`, or exact ` ms ` labels are accepted declarations;
the numerical data are unchanged and the label is returned verbatim. Supplied
timestamps with unit None, integer1, empty string or whitespace-only string
give workflow_metadata. No timestamps with unit `seconds` also gives that code.
Both absent is a permitted no-clock path; selected fitted drift with absent
timestamps gives workflow_metadata even if a neutral opaque field names a unit.
In a cubic control use relative clocks(0,1,2,3) and one coordinate drift
(0,1,8,27): coefficients(0,0,1) retain pixels/unit, pixels/unit^2,
pixels/unit^3 and fixed B0=0pixels. Renaming the label leaves those numerical
coefficients unchanged. Retain CE06's alias/index/mutation operation order;
this algebraic units example creates no extra public fit or converted clock.

If a stage raises its accepted domain/operation error, wrap with WorkflowError
using the corresponding category above, stage/context and original exception
as `__cause__`. Do not change the stage's own public exception behavior when
called directly. Backend failures retain cause. MemoryError propagates as
MemoryError (including a stage cause chain identifying allocation); no numeric
result or partial metadata escapes. Ordinary Python argument-binding errors
remain TypeError. Arbitrary malformed object protocols/concurrent mutation are
outside supported value inputs, not a new exception-safety guarantee.

Failures at any later time/order reject the whole workflow. No None/zero image,
initial-guess substitution, omitted time, unavailable-success record, fallback
or silent mode disable is returned. A successful finite image with explicit
unqualified binary/recovery claims is different from a failed numeric operation.
The companion scenario inventory requires permitted positives paired with each
meaningful boundary, not blanket rejection of weak/negative/zero valid inputs.

## 11. Execution ownership, evidence and readiness

This is high risk: new scientific composition, finite decision semantics,
input representation and public interfaces. This source author owns only this
contract and companion map; no product/tests/fixture/workflow/dependency/policy/
other-document/Git mutation is authorized to this role. Fresh independent
COMPLETE source-contract review follows, before fresh native blind A authors
the complete public workflow checkpoint. Fresh blind B reviews its independent
oracles and complete scenario mapping; restricted C owns only coordinator-named
runtime files; fresh D reviews the exact passing complete candidate. The
coordinator supplies narrow ownership packets and performs launches; this role
does not launch or delegate. New interface names above are settled here;
runtime/test file placement does not grant unlisted edit authority.

Coverage inherits PROJECT's approved behavior coverage plus independent risk
review; percentages advisory. No percentage target or relaxed exclusion/gate is
selected. Preserve exact native statement/branch integers and all owned file/
package/global/subprocess/platform JSON/HTML integrity. Before PR opening,
reopening or pushing to an open PR, exact clean local
`make verify PYTHON=.venv/bin/python` must pass all 13 phases with fixed two
workers, strict outcomes, pinned reader, wheel/source/RECORD checks, isolated
imports and audit. Same-run M25 CONVERSION increment must be <=33,554,432 bytes.
Original independent Ubuntu24.04/macOS15 qualification and fresh D are required
before readiness; a source document supplies none of that evidence. A missing
report/reader/platform or timeout is incomplete, not success. No conditional
CI-only mode, dependency relaxation, old fullscene or RA15 is authorized.

Owner numeric limits are not set. Requested role model/effort is
gpt-6.1-sol/high; actual serving/billing/effort and unavailable token/cost
measurements remain unknown. Preserve all prior cumulative charges externally;
this source pass supplies no reset or self-approval. The ready stacked PR remains
coordinator-owned. CE08 is a later separate task. No merge/release/external
message is authorized. Only this role's scratch/process facts are reported;
durable source-pin evidence is kept, and no product verification is run by this
static-only author.
