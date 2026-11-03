# CE06: remaining defined acquisition modes

**Version 1.0. Proposed source-derived public contract. Fresh independent source
review must accept it before blind A/B. This document proves no runtime.**

This completes CE06's public mathematical packet under the
[common contract](c-equivalence-common-v1.md), [ordered stage contract](c-equivalence-rebuild-v1.md#ce06-defined-acquisition-modes)
and [complete source-mode ledger](c-equivalence-acquisition-modes-ledger-v1.md).
Its source hashes, caller routing, P/D/U
classifications and exact unsafe-path dispositions are normative inputs here.
All source references below use those pinned retained-root-relative files.
Retained C is never executed, built, linked or imported.

CE06 requires implementation and proof of the remaining defined supported
branches. The completed CE02–CE05 baseline is head a87f3ffc8c95877e8fbb159a44b6ab7527a879b3/tree
1375fb4ee38004cfdd9dcfd2889a7491ec406c80. No source reading grants authority to
remove accepted tests, change science or lower a gate.

## 1. Scope, dependencies and compatibility

The selected caller is ordinary single-objective non-TIFF sirecon, with explicit
decoded camera exposures, phases, optics, transfers and positive Wiener values.
The selected empirical caller remains ordinary radialft in mainfile.c, now
including its safe rectangular/length-one axial domains. The separate otf2d and
wiener2d tools, alternative builds, two-objective/I2M, file writing/reading and
multichannel shared-state orchestration remain explicitly outside this selected
value boundary. Their ledger dispositions are retained. No optional defined
mode within the selected caller is silently discarded.

CE06 is ONE integrated high-risk contract/candidate and one ready stacked PR
on that completed CE05 baseline. The following labels are logical obligation
groups inside the aggregate, not separate tasks, completed baselines, PRs or
native-role chains:

| Group | Internal mathematical dependency | Complete objective |
| --- | --- | --- |
| CE06a | Common dimensional/record conventions | True 2D preparation, estimation and known reconstruction; steps; literal -2D layout regrouping and qualified nominal-plane composition; safe rectangular/Z1 empirical preparation; radial/full K1 composition; unchanged useful 3D |
| CE06b | Shared CE06a records/coordinates inside the implementation | Safe fractional lateral zoom, 2D axial-zoom quirk, power/precise taper domain, overlap-disabled/exploded views and explicit positive Wiener schedule |
| CE06c | Shared preparation, separation and scale conventions | Off-exposure loading/sums/equalization and repeated-plane Fourier combination, all finite statistics/source quirks |
| CE06d | Combined dimensional, off-exposure and reconstruction conventions | Active between estimator/correction, defined raw/fitted within drift and linked phases/metadata/state, actual intermode raw-to-estimator-to-known composition |

These are implementation dependencies, not acceptance checkpoints or deferred
phases. All groups share AcquisitionBands and must compose in the final public
candidate. No group may be left unsupported merely because another group passes.
No additional contract file or internal completed prerequisite baseline is
required. The coordinator pins named runtime/test ownership and exact complete
checkpoint/candidate/check identities in the role packets.

Fresh independent COMPLETE source-contract review precedes one fresh native
blind A authoring ALL aggregate obligations, then one fresh native B reviewing
the COMPLETE test checkpoint. Restricted C implements only named runtime against
that reviewed aggregate. Full exact aggregate verification and original
Ubuntu/macOS qualification then fresh D assess the ENTIRE integrated candidate.
Corrections still receive the required fresh independent review; this creates
no scenario/review/repair cap and waives no gate. CE07 is a separately started
next task only after fully completed CE06.

The existing prepare_bands and PreparedBands contract stays EXACTLY CE02,
including Z>=2, integer zoom, writable owned outputs and original errors.
No reinterpretation of its phase-policy default occurs. Existing declared
transfer/sample behavior stays CE03. Existing estimate_parameters and
reconstruct_known on original PreparedBands with original/default arguments
stay CE05/CE04, including their accepted errors, record fields, used-field
validation, time parameter shapes and odd-Y behavior. No old API/module is
revived. New domains use a distinct AcquisitionBands record/entry so that a
Z1 specimen is never passed off as an already valid CE02 PreparedBands.

Only the explicitly stated additive input/option extensions below apply.
prepare_bead_otf broadens its raw shape domain as section 8 states; every old
valid call and default retains its mapping. Existing public tests cannot be
deleted merely because a new path is available. Compatibility is an independent
public-entry obligation throughout the aggregate, including ordinary D=3,P=5,O=3 3D
with explicit camera/optics/phases/transfers and positive Wiener.

## 2. Public entries, types and complete records

The new pure array entry, public from simrecon, is:

~~~python
prepare_acquisition_bands(
    images, *, acquisition_mode, dxy_um, dz_um, norders, background,
    lateral_zoom, axial_zoom,
    flatfield_slope=None, exposure_background=None,
    phases_rad=None, phase_steps_rad=None, edge_pixels=10,
    equalize=True, equalize_z=False, equalize_time=False,
    off_exposures=None, combine_off_orders=None,
    storage_order="direction-major",
    drift_between=False, drift_within=False, fit_drift=False,
    adjust_phases=False, drift_filter_fraction=0.0,
    wavelength_nm=None, numerical_aperture=None, immersion_index=None,
    header_timestamps=None, header_phases_rad=None,
    linespacing_um=None, phase_start_angle_rad=1.57193,
    negative_angle_step=False,
) -> AcquisitionBands
~~~

acquisition_mode is exactly "3d" or "2d"; no inference from a transfer axis.
images has real shape (T,D,P,Z,Y,X). For "3d", Z>=2; for "2d", Z=1.
T,D,P,Y>=1; X>=2 is even. O=norders>=1; Q=2*O-1<=P.
The downstream estimation/reconstruction domain is O>=2, with searching 3D
requiring O>=3. Preparation O1 remains permitted without downstream promises.

All original CE02 raw dtypes/exact finite-float32 representability, map and
exposure-offset kinds, scalar rules, count bounds and finite validation apply.
No axis is squeezed, permuted, broadcast or guessed. Background is scalar or
(Y,X); slope is None or (Y,X); exposure_background is None or (T,D,P,Z), counts.
Off images use the SAME rules and maps, shape (T,D,P,Z,N,Y,X), integer N>=1.
None means N=0. Off axes are not silently broadcast. These arrays remain inputs,
not fitted parameters. Native phases and directions remain count parameters.

dxy_um>0, and dz_um>0 in 3D. In 2D dz_um>=0 is permitted: zero means no declared
axial pitch and selects the source table-step fallback in downstream overlap/
filter calculations. The actual source condition is dz<=0
(sirecon.c:1410–1414,2021–2026), so negative dz also takes that mathematical
branch; negative physical pitch is outside this selected public domain and
rejects as an unsupported declaration, not as an undefined sampler.
No original 3D or empirical positive-pitch domain changes.
Between-direction pre-estimation actually evaluates
1/(Z*dz_um), even for Z1, so its selected prepass requires dz_um>0.
lateral_zoom=L is an exactly finite-float32-representable real scalar, L>=1,
with Xo=L*X and Yo=L*Y exactly integral. Integer inputs are included. axial_zoom=A
is a positive integer. All source extents/byte rules in section 10 apply.
A Z1 record with A>1 records the source 2D-plan quirk, not axial interpolation.

phases_rad is None or real (D,P), phase_steps_rad None or real (D,).
Values are finite mathematical radians, no wrapping/merging. If steps exist,
they take precedence and selected phases are p*step[d]. All supplied arrays
receive kind/shape/finite validation even if superseded. Only USED designs
require full column rank. The historical step option allocates exactly three
floats (helpers.c:180–186), so this caller-qualified shorthand permits D<=3;
D>3 steps reject with that reason. Any D remains available through explicit
lists. Neither limitation restricts existing CE02 lists. A list/steps selects
the supplied-matrix policy even when evenly spaced.

storage_order is "direction-major" or "z-major". It declares the source section
lookup, not an array-axis permutation: canonical input values remain in the
axes above. With no drift this is a recorded layout declaration for CE07.
Fast/z-major drift with D>1 is unsafe and rejects before numerical work:
main skips the estimator but reads uninitialized between-direction vectors.
Fast D1 BETWEEN-ONLY is a defined skipped-prepass zero-displacement case.
Fast within-3D is unsafe for EVERY D, including1: main allocates driftlist,
executes an empty fast branch instead of filling it, then reads it in
fixdrift_2D (sirecon.c:528–536,705–708; drift_n_phasestep.c:425–427).
Reject this branch before applying ordinary-order cubic-fit prerequisites.
Within-2D at fast D1 is a different, independently initialized path: its active
estimator fills the x/y displacements at sirecon.c:675–697. It can be selected
only under ALL its own reference/fit/phase prerequisites; it never inherits
safety from the between-only bypass.

combine_off_orders is None (all skip) or an integer NumPy array (O,), signed32
entries; positive means combine that order, <=0 means skip. A supplied table
requires O<=25, matching the fixed source field. At least one positive entry
requires N>0. An all-skip declaration with N=0 is permitted. The scalar noise
factors are NOT updated by combination. No photon/noise calibration is inferred.

All flags are actual booleans. drift_filter_fraction is a finite signed real
scalar within float32 magnitude; <=0 disables its high-pass multiplication,
>0 selects it. fit_drift has numerical effect only for within-drift in 2D;
3D within always fits. adjust_phases has numerical effect only with within-drift.
No request is silently downgraded when its used branch is unsafe.

Optics are required when either drift flag selects the ordinary prepass,
when within-2D drift actually estimates its correlation (including fast D1),
OR when any off-combination selector is positive:
integer wavelength_nm in 1..32767 nm; 1<=immersion_index<=2 and
0<NA<=min(2,immersion_index), same finite scalar kinds as CE04/05.
Optional supplied optics still validate these domains when unused. No defaults
are inferred from data. phase_start_angle_rad is finite, and linespacing_um,
when supplied, is finite positive micrometres (um); it is required for actually
adjusted phases. negative_angle_step selects sign of pi/D. These are phase
linkage settings, distinct from supplied estimation initial vectors.

header_timestamps and header_phases_rad are None or finite real NumPy vectors
of length F=T*D*Z*P*(N+1), representing the COMPLETE source extended-header
exposure stream in the declared storage order, one channel. Timestamps use
one consistent declared time unit; only differences/powers enter. Phase values
are radians after the source degrees-to-radians conversion. No acquisition-
reported displacement or dose enters the selected mathematics. No time offset
is silently added to source metadata accesses. Their first-block indexing and
timestamp mutation are literal in section 6.

Used 3D within-drift requires adjust_phases=True, both metadata arrays, D>=4
and a full-rank cubic design. This follows actual allocation/routing, not a
new constraint on between-only drift. Fitted 2D within-drift requires P>=4,
adjust_phases=True and both metadata arrays. With fit_drift=True but
adjust_phases=False, timestamps is never allocated by main and its extraction
dereferences null BEFORE the fit (sirecon.c:227–270,684–690); a declared clock
alone cannot bypass this actual phase-flag prerequisite. Unfitted 2D within
with adjust_phases=False permits smaller P and requires NO clock/phase
metadata, subject to N>0/default-reference and actual prepass prerequisites.
Actually adjusted phases always require header_phases_rad: even in 3D the
source unconditional diagnostic dereferences it. Missing metadata cannot select
the source's unsafe fake-timestamp/null-phase path.

AcquisitionModeError is public and subclasses SimreconError (ValueError).
Preparation input/domain/unsupported/unsafe/operation failures raise it with
nonempty informative text identifying the field or operation. TypeError remains
ordinary Python signature failure. Allocation/factorization/transform/backend
failures retain their cause; no partial result escapes. Caller interruption
remains interruption. Existing original-entry error contracts are unchanged.
estimate_parameters continues to raise ParameterEstimationError and
reconstruct_known ReconstructionError for their own new-domain failures;
prepare_bead_otf retains OtfError.

AcquisitionBands is a frozen value record with the following exact fields.
All numerical output uses binary64/complex128, except integer/bool fields.
quadratures and noise_variance_factors own writable storage, permitting valid
caller modifications as in CE02; diagnostic arrays are owned and read-only.
Nothing aliases an input or another returned array. No hidden raw checksum or
replay is required when downstream validates used fields.

| Field | Type/shape/meaning |
| --- | --- |
| quadratures | complex128 (T,D,Q,Z,Y,X//2+1), final bands after section operations, axial transform where selected, then selected between correction |
| noise_variance_factors | float64 (T,D,O), final per-direction matrix factors used by filtering at that time, from LAST processed z; no off-combination update |
| separation_matrices | float64 (T,D,Z,Q,P), actual used matrix for every section |
| phase_angles_rad | float64 (T,D,Z,P), actual used phases, unwrapped |
| phase_policies | immutable T-by-D-by-Z tuple: "uniform", "steps", "supplied" or "drift" |
| frame_sums, equalization_gains | float64 (T,D,P,Z), on pre-equalization sums and applied gains |
| off_frame_sums, off_equalization_gains | None if N0; otherwise float64 (T,D,P,Z), after summed-off edge, before off equalization, and actual off gains |
| off_quadratures | None if N0; otherwise complex128 (T,D,Q,Z,Y,X//2+1), after per-section separation/correction, with no axial FFT or between correction |
| background_after, slope_after | float64 (Y,X), final persistent camera maps |
| sentinel_frames | tuple of (t,d,z,p,e) int events; e=0..N-1 for off, e=N for on |
| between_displacements_pixels | float64 (T,D,3), x/y detector pixels and z native sections; zero when inactive/skipped, direction0 zero |
| exposure_displacements_pixels | float64 (T,D,Z,P,2), actual x/y correction, zero when inactive; no invented estimated z |
| header_timestamps_after | None if absent, otherwise float64 (F,), literal post-fit mutable-header values |
| trace | immutable tuple of ModeEvent records specified below |
| input_shape | original (T,D,P,Z,Y,X) tuple of Python integers |
| input_scale | alpha=1/(X*Y*Z*L**2*A*D), finite positive |
| acquisition_mode, storage_order | exact declared strings |
| dxy_um,dz_um,lateral_zoom,axial_zoom | exact resolved sampling and zoom |
| resolved_settings | immutable ordered tuple, in the keyword order of this entry, excluding images/maps/raw arrays/metadata vectors; declared array settings become immutable tuples, None retained |
| source_revision, reference_sha256 | "SVN307", ten original ledger source-name/hash pairs in ledger order (excluding the two extra alternative-tool pins) |

The resolved-settings array exclusions are flatfield_slope, exposure_background,
off_exposures, header_timestamps, header_phases_rad and background when it is a
map. A background map is recorded as the string "map"; scalar background stays
its scalar. phases_rad/steps and combine_off_orders are retained as nested
tuples. Record N as the additional final key n_off_exposures. No object identity
or pointer convention forms metadata. Actual copied maps/offsets need not be
retained a second time; final maps/sums/trace describe their selected effects.

ModeEvent is frozen with fields kind (string), time_index, direction_index,
z_index (Python int or None), phase_index (int or None), details (immutable
ordered tuple of named values). Real/complex scalars are finite Python floats/
complex, integers are Python ints and decisions bool. Arrays own read-only
float64/complex128/bool storage as appropriate. Events appear in actual
time/direction/z/phase/operation order, with prepasses before direction work.
Required schemas are:

| kind | Ordered details keys |
| --- | --- |
| between-build | subz, first_z, centers (D,subz,Y,X), fourier (D,subz,Y,X//2+1), optical_radial_cutoff, unused_axial_cutoff |
| drift-correlation | scope ("between" or "within"), moving_index, exponent, cross_spectrum, correlation, absolute_correlation, integer_peak_xyz, neighbors_xyz, offsets_xyz, offset_status_xyz, wrapped_displacement_xyz |
| cubic-fit | scope, sample_timestamps_before, sample_timestamps_after, evaluation_timestamps_before, evaluation_timestamps_after, sample_displacements_xy, matrix, coefficients, evaluated_xy |
| exposure-correction | displacement_xy, phase_multiplier (Y,X//2+1) |
| phase-design | policy, phases_rad (P,), separation_matrix (Q,P), noise_variance_factors (O,) |
| off-combination | call_z, affected_z (always0), order, cutoff_integer, inside_count, outside_count, on_noise, off_noise, on_signal2_before_clip, off_signal2_before_clip, both_zero_replaced, on_scale, off_scale, denominator, on_fraction, off_fraction, quadratures_after |
| between-correction | displacement_xyz, phase_multiplier (Z,Y,X//2+1) |

cross_spectrum shape is (subz,Y,X//2+1) for between and (1,Y,X//2+1)
for within; correlation/absolute shape (subz,Y,X) or (1,Y,X). Integer peaks
are three-int tuples (x,y,z). Neighbor/offset arrays use xyz order, neighbors
shape (3,3) ordered minus/center/plus. For within/subz1, axial offset/displacement
is0, axial neighbors repeat center and status is "not-fitted".
Other statuses match CE05 fitparabola: "zero-curvature", "outside-range",
"fitted". Wrapped displacements are float64 (3,). Within z is a diagnostic
zero, never read from source's uninitialized struct member.
Between-build is omitted on the fast-D1 skipped prepass (between-only, or
the independently qualified 2D-within path; never fast within-3D). No events are emitted
for unused drift/fit branches. phase-design occurs for every used section
even when matrix values repeat. Off-combination emits one per selected order
per caller invocation; quadratures_after is complex128 (1,Y,X//2+1) for order0
or (2,Y,X//2+1) for side order, the affected first plane only.

Fit design shape is (nPoints-1,3), coefficients (3,2), displacement arrays
(nPoints,2)/(nEvalPoints,2), timestamp arrays their respective lengths.
This trace adds observability, no numerical branch/extra fit/extra sample.

## 3. Exact preparation and off-exposure sequence

CE02 equations are incorporated as normative mathematics: sentinel, persistent
camera maps, alpha, vertical-then-horizontal additive edges/sine/bypass,
pre-equalization anchors, negative-sign unnormalized lateral Fourier sum,
uniform or supplied inverse/left inverse, scalar row-norm noise and the
UNSEPARATED stored lateral Nyquist pair. New operation order follows
sirecon.c:488–785 exactly, not independent reordered helpers.

Initialize camera maps and optional metadata once. Traverse t, then d,z,p.
At each t, do the selected between prepass and 3D within fit BEFORE normal
camera loading. The prepass sees current background maps, including earlier
time sentinel changes, but does not change them itself. Within every (t,d,z):

1. For p ascending, load each of N off exposures in ascending e before on.
   Apply the CE02 exact -1 bottom-right sentinel and persistent map update to
   EACH load, then J=alpha*s*(I-b-bextra). Sum the corrected off frames,
   never average. Edge treatment is applied once to that SUM.
2. Then load/correct/edge on. If exposure_background is supplied, the on
   load uses its current value; off loads instead use the previously loaded
   ON value, including across phase/z/direction/time boundaries, initial0.
   When no extra backgrounds are selected, all use0. This is main's
   backgroundExtra carry at sirecon.c:608–633, not an off-specific new offset.
3. Compute on sums and equalize by the CE02 selected t/z reference when on.
   Off sums use their own direction0/phase0 anchor history and same flags,
   BUT equalization is executed only for N>1. For N1 its gains remain1 even
   when on equalization is enabled. With equalization disabled, zero sums
   remain legal. Every actually selected zero divisor rejects.
4. Forward lateral transform all on and summed-off frames, unnormalized,
   negative exponential, origin first detector sample.
5. When within-drift is on, estimate/fetch the actual section displacement
   using section 6. Multiply on and off half-spectra by the SAME positive
   per-exposure phase ramp. If adjust_phases is on, construct the linked
   phase list and its supplied separation matrix AFTER correction and
   BEFORE separation. Otherwise use declared steps/list/uniform policy.
6. Separate on and off independently with that matrix at kx<X/2.
   At kx=X/2, slot q keeps the corrected raw phase q half-spectrum, including
   its phase-specific shift. Do not separate the endpoint or impose a
   Hermitian projection after fractional translation.
7. If any off-combination selector is positive, call section 4's combination
   now. It addresses plane0, even when current z>0. Capture that literal
   sequence. It does not update scalar noise factors.
8. After all z for a direction: for "3d" transform every retained slot through
   z by the unnormalized negative forward sum. For "2d" there is no axial
   transform. Off images receive NO axial FFT in main. Selected between
   correction follows on bands only for d>0 and drift_between=True.
   Fitting then consumes these actual corrected bands.

The selected matrix/noise for a (t,d) filter is the last z's matrix factor;
there is no average over z or matrix recomputation during filtering. Other
phase diagnostics retain their actual section-specific values. Normal
preparation without off/drift is exactly CE02's mapping on its shared domain,
apart from the distinct record shape for time-specific noise.

### 3.1 Literal -2D regrouping and the public layout helper

sirecon.c:207–215 changes header interpretation, multiplies time by Zstack
and sets nz=1; it does NOT permute image data. The numerical array analogue
must therefore distinguish physical exposure-stream order from nominal planes.
The helper and TwoDPlaneInputs record are public from simrecon:

~~~python
reinterpret_2d_planes(
    images, *, storage_order, off_exposures=None,
    exposure_background=None,
) -> TwoDPlaneInputs
~~~

images is a canonical raw array (T,D,P,Zstack,Y,X), Zstack>=1, with the same
real raw representation/copy rules as preparation; T,D,P,Y>=1, X>=2 even.
Off data is None or (T,D,P,Zstack,N,Y,X), N>=1; exposure_background is None
or finite real (T,D,P,Zstack). storage_order is exactly "direction-major" or
"z-major". Invalid kinds/shapes/nonfinite values, unsafe source/intp extents
or allocation failure follow AcquisitionModeError/no-partial-result rules.
No camera operation, phase design, equalization or estimation occurs here.
The helper preserves raw pixel bits and does not alter its inputs.

Let E=N+1. The resolved physical stream index within original t is
s_dir=((d*Zstack+z)*P+p)*E+e for direction-major and
s_z=((z*D+d)*P+p)*E+e for z-major, e=0..N-1 off, e=N on.
Literal effective time e_t=t*Zstack+q, q=0..Zstack-1, reads physical positions
q*(D*P*E)+(d_new*P+p)*E+e. These positions retain stream order; no transpose
is smuggled into the header reinterpretation.

Equivalently, the source original (d,z) for each (q,d_new) is:

- z-major: d=d_new,z=q;
- direction-major: h=q*D+d_new, d=h//Zstack,z=h%Zstack.

Return result.images[e_t,d_new,p,0]=images[t,d,p,z] under that mapping; apply the
SAME mapping to each off e and the on exposure_background value. This produces
shape (T*Zstack,D,P,1,Y,X). A nominal-plane equation
images2d[t*Zstack+z,d,p,0]=images[t,d,p,z] is therefore valid for a z-major
physical stream, or when D=1 or Zstack=1; it is NOT generally the ordinary
direction-major -2D mapping.

For D=2,Zstack=2,P=3,N=0, ordinary phase groups are
d0/z0,d0/z1,d1/z0,d1/z1. Literal new groups at effective q0 are old d0/z0
and old d0/z1; at q1 they are old d1/z0 and old d1/z1. Original d1/z0
phase0 is physical section6, not section3. A plane-major arrangement would
need z0/d0,z0/d1,z1/d0,z1/d1; header rewriting alone does not produce it.
The helper must expose this distinction with unique exposure labels.

TwoDPlaneInputs is frozen with fields images (owned read-only raw array in
the input dtype), off_exposures (None or owned read-only
(T*Zstack,D,P,1,N,Y,X) in its OWN input dtype), exposure_background (None or owned read-only float64
(T*Zstack,D,P,1)), source_direction_z (owned read-only int64 (Zstack,D,2)
in original d,z order), original_shape (six-int input tuple), storage_order
(exact declared string), source_revision and reference_sha256 (ten-file
AcquisitionBands identity). All source and aggregate target extents must fit
section10. No axis/array shares storage with caller data or another output.

Pass returned arrays to prepare_acquisition_bands(acquisition_mode="2d",
storage_order=result.storage_order,...). Keep actual storage_order: although
the Z1 ordinary/fast section formulas coincide, bFastSIM still controls drift
routing. Phase lists/steps, carrier directions and linked phase vectors index
the NEW d_new, not an automatically substituted original direction.
Header metadata vectors retain their physical stream values/order; their
literal first-block indexing in section6 is not “fixed” by this helper.
Equalize-time and time0 carrier reuse apply to NEW effective time0; ordinary
direction-major regrouping can mix nominal original planes/directions and must
be documented rather than interpreted as scientific plane recovery.

Required public composition uses this actual helper output, then preparation,
estimation and per-time known reconstruction, for both layout declarations.
External IMAlZWT/IMPosnZWT header-library semantics and file binding remain
unqualified until CE07. This is a resolved source-index/value mapping,
not a new file adapter or a claim that the unknown external library physically
reorders bytes. A caller wanting nominal-plane behavior must explicitly supply
the appropriate stream/layout; no reference repair or automatic reordering.

## 4. Actual off/on Fourier combination

Source: sirecon.c:743–746 and small_math_funcs.c:115–229. Every invocation uses
base pointers, NO z offset. All reads/writes below refer to plane0 at that
moment. At z0 this is the newly separated first section; at later z it is the
previously combined first section, while off plane0 remains its separated value.
A new direction/time resets these from its own newly loaded images.

Set C=trunc(2*NA/(wavelength_nm/1000)) if combination is selected.
This is the MAIN optical cutoff without the Nyquist clamp, converted to the
helper's integer argument. Thus combination requires explicit optics even
without drift. Set c2=C*C using checked source signed-int multiplication.
For iy=0..Y-1, ix=0..X/2, set
ky=trunc(q(iy,Y)/(Y*dxy)), kx=trunc(ix/(X*dxy)),
where q is the accepted positive-Nyquist signed lift.
These kx/ky are INTEGERS, because source declarations/compound assignment
truncate scaled frequencies. Set kr2=kx*kx+ky*ky. Outside iff kr2>c2; equality
is inside. Counts count stored half-plane CELLS once each, with no reflected
multiplicity and no doubled count for two side quadratures.

In order m ascending, skip if selector<=0. For m0, cell power is |B0|**2;
for side m it is |E_m|**2+|O_m|**2. Separately for on and off:
n=mean(outside power); s2=mean(inside power)-n; clip s2 below0 to0.
If BOTH resulting s2 are0, replace both by1. No such replacement when only
one is zero. signal=sqrt(s2), u=signal_on/n_on, v=signal_off/n_off,
den=u+v. Require nonempty inside/outside sets, positive finite n_on/n_off,
finite defined u,v,den>0 and finite ratios. No epsilon or arbitrary noise floor.

Let a=u/den,b=v/den. For m0 write on=a*on+b*off. For each side quadrature
write on=a*on-b*off. This applies to all half-plane complex samples INCLUDING
native Nyquist, regardless of which samples supplied the statistics.
Off stays unchanged; scalar separation noise stays unchanged. A zero signal
in one input can validly give a=0 or b=0. Both-zero replacement gives finite
relative inverse-noise weights. Zero noise is singular even if the corresponding
estimated signal is zero.

The public trace records raw preclip signal2, replacement decision, each
weight and affected plane after every order/call. Correcting the integer
frequency/cutoff units, averaging N off frames, combining each current z
instead, updating noise factors, using variance rather than standard deviation
in u/v, or a modern generalized least-squares combination is a different method.

## 5. Active between-direction estimator and correction

This is determinedrift_bt_dirs in the LINKED drift_n_phasestep.c:10–209,
called at sirecon.c:515–517 before ordinary loading. It is not a stationary
band-overlap fit, generic shift identity or the later within-exposure estimator.

Let S=max(floor(Z/2),1), zstart=floor((Z-S)/2), V=X*Y*Z.
For each direction d, average the selected raw on exposures over phase,
subtracting the current background map, and divide by V:
C_d[h,y,x]=sum_p (I[t,d,p,zstart+h,y,x]-background[y,x])/(P*V).
Before this subtraction, independently replace a raw bottom-right exact -1
by its left neighbor. This prepass sentinel DOES NOT change maps or use slope,
extra exposure background, normal alpha, selected normal input edge width or
sum equalization. Use the background state existing at this prepass.

When N>0 the actual reused i loop variable at drift_n_phasestep.c:85–94
reads the FIRST off exposure once, adds it with the SAME subtraction/(P*V),
then skips forward by N before on. It does not accumulate all N.
This terminates for N<=Y+1. For N>Y+1 reject the nonterminating source branch
before prepass. The ordinary loading sum of all N remains section 3.
This limit belongs to the selected prepass, not off exposures without it.

For each selected h, apply CE02's additive edge equation with FIXED width10,
vertical then horizontal, on the summed C_d plane. X,Y>=10 is required for this
prepass. In particular Y1 with ordinary prepass is unsafe even if normal
edge_pixels=0: negative opposite-edge rows and rows through9 are accessed.
X=Y=10 is safe and its strips overlap; no 20-pixel minimum applies.
No-drift Y1 remains valid. The skipped fast-D1 between-only prepass does not
evaluate these accesses. Then take its unnormalized negative forward Fourier
sum over
(S,Y,X), storing nonnegative kx. For S1 it is a 2D transform.
Let dx=1/(X*dxy),dy=1/(Y*dxy) and
Rd=2*NA/(wavelength_nm/1000), WITHOUT the normal Nyquist clamp.
The source ALSO calculates dkz=1/(Z*dz), aperture a=asin(NA/nimm),
lambda=(wavelength_nm/nimm)/1000, and
cz=min(ceil(((1-cos(a))/lambda)/dkz),floor(Z/2)).
All that arithmetic must be defined/representable even though cz is not used
to mask any spectrum. Axial transform length S does not change that unused
calculation or require rescaling the estimated axial shift.

For every d>0, initialize half cross spectrum W=0. At every axial index h,
row iy and stored ix, set r=hypot(ix*dx,q(iy,Y)*dy). Only when r<Rd:
c=conj(F_0[h,iy,ix])*F_d[h,iy,ix].
Let f_a(c)=|c|**a*exp(i*arg(c)), a=1/4.
For c=0 this product is exactly0, independent of its irrelevant phase;
no phase is retained or used separately. This is the unique continuous zero
of the composite, as in CE05 zero combined modulation. It does not license
inventing a polar angle later used independently in a search/sector.
Set W=f_a(c). If drift_filter_fraction=hpf>0, multiply by
(1-exp(-(r/(hpf*Rd))**2))**2. With hpf<=0 do not evaluate that division.
At r=Rd leave0; no axial support mask, deconvolution or unit-power
normalization occurs.

Reconstruct the full spectrum from half storage by all-axis conjugate reflection
and take the unnormalized positive-exponential backward sum. The real correlation
is the real output of that real inverse transform; ordinary input ensures the
source real-transform symmetry. Do not take modulus of a complex inverse as
a different correlation statistic. Then use ABSOLUTE VALUE of the real array
for peak selection and all neighbor values.

Peak selection starts maxval=0 and (x,y,z)=(floor(X/2),floor(Y/2),floor(S/2)).
Scan z,y,x increasing; replace only if abs(corr)>maxval. Nonzero equal peaks
choose first scan maximum. An all-zero correlation keeps the INITIAL CENTER,
not (0,0,0), and is a defined estimator outcome. Do not reject it as no energy.

For each axis, use periodic immediate neighbors about the SELECTED integer
peak on the unchanged other coordinates. Given a-,a0,a+ (all absolute values),
s=(a+-a-)/2, c=a++a--2*a0. If c=0 offset0; else offset=-s/c,
unless outside [-1.5,1.5], in which case0. Source refinement order is z,y,x.
For S1 the z offset/shift is forced0 instead of fitting.
For each fitted coordinate v=integer_peak+offset, if v>floor(Naxis/2)
subtract Naxis ONCE. Equality stays positive; a negative fractional v is not
wrapped upward. Return displacements in x detector pixels, y detector pixels,
z native sections of pitch dz, NOT S-bin frequencies, um, output pixels,
or output-zoom units. No extra factor Z/S applies. Direction0 is exactly0.

This fitparabola is the accepted CE05 helper rule. Because a0 is a finite
global maximum of a nonnegative absolute map, its nonzero-curvature offset
lies in [-1/2,1/2]; outside-1.5 branches cannot be forced via a fake helper seam.
The all-zero initialized-center case has zero curvature. Endpoint wrapping,
including strict comparison after fractional refinement, still needs proof.

At the end of a direction's ordinary preparation, iff drift_between and d>0,
multiply EVERY retained half-space quadrature by
exp(+2*pi*i*(displacement_x*ix/X
             +displacement_y*q(iy,Y)/Y
             +displacement_z*q(iz,Z)/Z)).
This is exp(+2*pi*i*k dot displacement) in consistent pixel-frequency units.
In physical units use displacement_um=(dxpix*dxy,dypix*dxy,dzpix*dz)
and frequencies in cycles/um. Origin is the first sample, not the centered
assembly labels. The positive sign corrects moving data shifted in the positive
detector direction: if g[n]=f[n-d], Fg=Ff*exp(-2*pi*i*k*d), so this factor
restores Ff. Preserve positive even native Nyquist labels, all-axis reflection
rules and any non-Hermitian endpoint quirk; no projection or new interpolation.

With only drift_within selected, the prepass still runs, but main applies NO
between correction. Its measured vectors can supply the 3D within fit.
With fast order D1 BETWEEN-ONLY the prepass is skipped and vector0 remains0;
it supplies no fictional prepass/optical values in trace. A qualified fast-D1
within-2D path also skips this prepass but runs its OWN correlation/phase/fit
sequence; fast within-3D never qualifies because driftlist is uninitialized.

## 6. Within-exposure drift, cubic fit and linked phases

### 6.1 True 2D within-direction estimator

At each (t,d), after on/off preparation, equalization and forward FFT, but
BEFORE exposure translation/separation, the active default reference is
Ref=On_phase0+Off_phase0 in Fourier space (calcRefImage type0).
N>0 is required because the actual source returns without filling Ref otherwise,
and main ignores that status. The contract does not select the unused or
uninitialized reference types1/2/3. No reference is estimated across directions.

For each p, Moving=On_p+Off_p. Use section 5's cross-correlation operation with
c=conj(Ref)*Moving, exponent a=1/2, axial length1, the SAME strict Rd and
high-pass rule. This estimator uses the normally prepared/equalized images,
unlike the between prepass. Its inverse real output is contiguous (Y,X);
the between prepass's real row stride X+2 is storage only and supplies the
same physical finite sum. Scan y,x increasing, initial center/max0, periodic
absolute neighbors, refine y then x and wrap by the same strict half rule.
Raw x/y displacements for every phase are retained in the drift-correlation
events, including phase0. No invented source z value is exposed.

If fit_drift=False, use those displacements directly; with adjust_phases=False
this active branch requires no timestamps or phase clock. If fit_drift=True,
the caller's adjust_phases/bFixPhaseStep allocation route and usable metadata
are mandatory BEFORE extracting timestamps, independent of P>=4/full rank.
Otherwise the actual source reads a null timestamp pointer before fitting.
For a qualified fitted call form the P timestamp samples from the prefix
of the header vector at
d*P*(N+1)+p*(N+1)+N, the ON exposures, without a t offset.
Pass one owned sample vector as BOTH sample and evaluation argument to the
fit below (the source aliases them). Use its fitted x/y values for correction.
No fit or new timestamp origin is imposed on the unfitted branch.

### 6.2 Actual cubic fit, including mutation/alias rules

fitXYdrift hardcodes nPolyTerms=4 and bForceZero=1
(drift_n_phasestep.c:269–326). It is not a line or quadratic and it does not
estimate an independent constant. Let n=nPoints, B_i=(x_i,y_i), tau the MUTABLE
sample timestamp vector and eta the MUTABLE evaluation vector. They may alias.

Execute these steps in order, using current values at each statement:

1. For i=1..n-1: tau[i] -= tau[0]. Leave tau[0] unchanged.
2. Build A[i-1,j-1]=tau[i]**j for i=1..n-1,j=1,2,3 and
   RHS[i-1]=B_i-B_0. Solve the unweighted least-squares problem
   min sum_i |A_i*c-(B_i-B0)|**2 separately for x/y. For n4 square this
   is an inverse; for larger n it is the unweighted overdetermined fit.
3. For i=0..nEval-1: eta[i] -= tau[0], evaluating tau[0] at EACH statement.
4. Evaluate Bfit(eta)=B0+c1*eta+c2*eta**2+c3*eta**3.

The coefficient/output buffers require n-1>=3. Full column rank is required:
at least three distinct NONZERO relative sample times suffice and are necessary
for this three-column power design. Duplicates are permitted when that condition
holds. No arbitrary condition-number cutoff or weighted/smoothed regression.
Factorization failure, unresolved rank/precision or nonfinite arithmetic rejects;
source ignored status does not supply a finite successful result.

In the 2D alias case step3 i0 sets tau[0] to0; subsequent evaluation samples
therefore subtract0. Their values were already shifted ONCE in step1, not twice.
This mutation is local to the extracted timestamp vector, not the full header.

In ordinary-order 3D the sample vector and evaluation prefix are distinct
arrays. Fast-order 3D skips this entire fit and leaves driftlist unreadied;
it is unsafe even at D1, not a zero fitted curve. At every t,
before per-direction normal preparation, take samples
tau[d]=header_timestamps[d*Z*P+floor(Z*P/2)], d=0..D-1.
This indexing literally IGNORES N off exposures and any t offset.
B_d is the just-estimated between-direction x/y drift (B0=0).
Use D>=4. Evaluate at the mutable first D*Z*P entries of header_timestamps,
again ignoring off stride. The sample vector is shifted by its first entry;
the global evaluation prefix is shifted by the UNCHANGED sample tau[0].
Keep that mutation for later time iterations. Do not restore the metadata or
substitute each later time's timestamp block.

Reshape the D*Z*P fitted x/y vectors in (d,z,p) order. For d>0 subtract
the MEASURED between-direction x/y vector B_d from every fitted value
in that direction. Do not subtract its fitted midpoint, direction0 or any
axial drift. These are actual per-exposure correction displacements.
This fit is unconditional for 3D within mode, independent of fit_drift.
Main allocates timestamps only when adjust_phases/bFixPhaseStep is selected;
3D within without that route is an unsafe null-pointer source branch.

### 6.3 Exposure correction and phase linkage

For each on/off phase spectrum in its current section, multiply by
exp(+2*pi*i*(dxpix*ix/X+dypix*q(iy,Y)/Y)).
This is translate2D at drift_n_phasestep.c:374–428. It acts BEFORE separation,
has no 1/(X*Y) normalization, includes stored x Nyquist, and uses detector-pixel
displacement, independent of L or A. Do not correct an image in real space with
a new interpolation kernel.

When adjust_phases AND drift_within, calculate, for d in source order:
delta=sign*pi/D, sign=-1 if negative_angle_step else+1;
theta_d=phase_start_angle_rad+d*delta,
kguess_phase[d]=(cos(theta_d),sin(theta_d))/linespacing_um.
This is the actual calcPhaseList caller. It ignores supplied k0angles used by
main's estimation initialization and does not divide by nordersIn-1 in 3D.
It is not automatically the fitted carrier or even the supplied CE05 initial
carrier. Exposing these separate settings prevents a hidden sign/factor change.

For section z and phase p set
phi_drift=+2*pi*dxy*(dxpix*kguess_phase_x+dypix*kguess_phase_y).
If Z1 use
base=header_phases_rad[d*P*(N+1)+p*(N+1)]
(the FIRST off phase; with N0 it would be on). If Z>1 use base=p*2*pi/P,
even though phaseAbs must still exist for the source diagnostic dereference.
Actual phi=base+phi_drift. No subtraction of recorded absolute phase, no
independent exposure-phase optimization and no phase wrapping occurs.
This list supersedes supplied steps/list/uniform policy; construct its
supplied inverse/left inverse and noise by CE02. Drift without phase adjustment
still translates the frames and retains selected declared phases.

For 3D the final direction noise comes from the LAST section, while previous
sections retain their own actual separation rows. Every used design must have
full column rank. A zero/weak drift correlation can be defined, yet its linked
phases can produce a singular design or later CE05 no-energy error; success
of one stage is not a promise that later stages accept it.

calcPhaseList's unconditional phaseAbs diagnostic dereference is part of source
safety even for 3D. The fake-timestamp-only header fallback has no reference
here. Diagnostic text itself supplies no numerical oracle.

## 7. True 2D parameter estimation and public composition

estimate_parameters accepts either an original PreparedBands, unchanged, or a
valid AcquisitionBands. Its public signature/defaults and EstimatedParameters
field names/types remain CE05. On AcquisitionBands it validates that record's
used quadratures, time-specific noise, shape, alpha/sampling/zooms and ten-file
source identity. It neither replays raw preparation nor rejects permitted
finite caller changes to writable bands/noise. Other stage diagnostics are
not cross-checked against imaginary raw data. With O1 it rejects before work.
search requires O>=2 in 2D and O>=3 in 3D. Inputs/floors/flags/optics and
regression failure reasons remain CE05.

For Z1 the transfer must have K=1; radial shape (Otable,R,1), full shape
(Otable,1,Ytable,Xtable), with at least the used O orders. Both an accepted
declared OpticalTransfer and the ACTUAL PreparedOtf.transfer from empirical
preparation are valid transfer inputs. Preserve that record's complex128
samples, layout, order count, source identity and positive dkr/dkz metadata.
A computed transfer need not be exactly complex64-representable; no declaration
call, complex64 cast, quantization or metadata rebinding occurs before sampling,
estimation or known filtering.

Use native dkz=1/(Z*dz) when specimen dz>0, otherwise native dkz=transfer.dkz.
As source, the latter condition is dz<=0; this public Z1 domain permits zero,
not negative pitch. At K1 every visited z is0 and its axial sampler coordinate
is0*(native_dkz/transfer.dkz)=0. Both radial axial vertices address that same
sole plane; full-table axial neighbors also wrap to it. Preserve ALL lateral
and axial stencil vertices, even zero-weight/duplicate ones.
Compute all actual ratios/cutoffs and perform their finite/representation checks
before sampling; this algebra does not waive an intermediate operation failure.

The value1 cycles/um is only the literal source 2D FILE loader assignment
(helpers.c:765). It is not a required replacement for a prepared value record's
positive dkz=1/(Zbead*dz_bead). In particular a Zbead1 prepared transfer can be
used directly for a Zspecimen1 acquisition with its original positive metadata,
whether specimen dz is positive or the supported zero fallback. Do not reset
dkz to1 to mimic a file reader. Negative pitch remains outside public support;
there is no axial inference, squeezing, rescale or table normalization.
Extra orders remain permitted and unused.

The complete CE05 overlap/regression/search equations are incorporated with
the following EXACT substitutions, not a new estimator:

- Native Z=1, no axial preparation transform; overlap inverse is the
  unnormalized 2D backward sum. Its initial ordinary optical c is computed
  using native dkz, then the strict c>floor(Z/2) clip gives0.
- Threshold multiplier on the HIGHER transfer is1, not5. Both transfer
  thresholds remain strict >0.006, with exact short circuit. The theoretical
  self and shifted masks remain inclusive <=R; R is Nyquist-clamped here.
- Search coarse/refinement pair is (0,1). Coarse carrier after literal
  old_k0*dk alias decisions divides by1, not2. Default source line-spacing
  conversion is 1/linespacing in 2D; a supplied resolved initial vector is
  never divided again.
- General pair (a,b) uses delta=(b-a)*carrier. For a>0 read lower E_a,O_a
  separately, reflect/conjugate EACH if needed, and form E_a+i*O_a before
  multiplying the complex cross-transfer weight. Thus for q, lower overlap
  is B_a(q)*H_b(q-delta)/sqrt(|H_a(q)|**2+|H_b(q-delta)|**2);
  higher is B_b(q)*H_a(q+delta)/sqrt(|H_b(q)|**2+|H_a(q+delta)|**2).
  Thresholds, samples and written masks are the CE05 ordered branches,
  now with multiplier1. No scalar conjugation of Bplus substitutes.
- After the final searched pair (0,1) evaluation, assign its factor to order1.
  For b=2..O-1, REMAKE overlaps for (b-1,b) at final carrier and fit there.
  Those later getmodamp evaluations retain the squared-forward objective.
  The same CE05 finite angle/magnitude search, stale x1/amp1, strict ties,
  general parabola, final frozen overlap and exact trace remain binding.
- KNOWN-vector mode, including t>0 time0 reuse, follows main's actual
  (0,b) fits for every b, with objective=None. It does NOT use adjacent
  fits merely because the comment says it should.
- After all fits, in BOTH 2D paths, for b=2..O-1 ascending execute
  factor[b] *= factor[b-1] using the ALREADY UPDATED previous factor.
  If direct known fits gave (a1,a2,a3), outputs before floors become
  (a1,a2*a1,a3*a2*a1). This defined known-path quirk must remain.
  No such product applies in 3D.
- Apply CE05 floors to these products, then its higher-order phase replacement,
  in the same order. Positive floor on zero and selected zero order1 phase
  remain failures. Modulation can be finite zero when no later selected
  operation needs its phase or reciprocal.

EstimatedParameters.raw_modulation for AcquisitionBands retains the direct
forward fits BEFORE 2D products. Its modulation contains products/floors/phase
policy as stated. Extend the existing trace with one "cumulative-product"
event per b>=2 BEFORE adjustment events: details keys order, direct_forward,
previous_cumulative, product (int then complex scalars), in that order.
The existing "adjustment" raw_forward is the factor ENTERING floors (cumulative
in 2D, direct in 3D). This explicit distinction preserves diagnostics without
renaming accepted fields or changing original 3D trace.

EstimatedParameters.source_revision is the Python string "SVN307" for BOTH
input record types. Its reference_sha256 is an immutable tuple of six
two-tuples of Python strings, ALWAYS the exact CE05 estimator-source tuple
in CE05 order, regardless of input type:

| Position | Source-name string | SHA-256 string |
| --- | --- | --- |
| 0 | sirecon.c | 3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567 |
| 1 | small_math_funcs.c | a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e |
| 2 | helpers.c | b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206 |
| 3 | sirecon.h | f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629 |
| 4 | Makefile | 1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4 |
| 5 | usr_local/include/fftw3.h | 8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d |

The public settings field is resolved_settings, exactly as CE05. For an
AcquisitionBands result it is an immutable tuple of EXACTLY15 ordered
(key,value) pairs. Keys are Python strings. The first13 CE05 keys retain their
existing order and resolved meanings; their values come from validated call
arguments or the actual bands record, with no rescale or new inference:

| Position | Key | Exact value kind and meaning for AcquisitionBands |
| --- | --- | --- |
| 0 | wavelength_nm | Python int, validated supplied nm |
| 1 | numerical_aperture | Python float, validated supplied NA |
| 2 | immersion_index | Python float, validated supplied index |
| 3 | search_carriers | Python bool, selected flag |
| 4 | use_time0_carriers | Python bool, selected flag |
| 5 | amplitude_floors | None or immutable tuple of O-1 Python floats, supplied positive floors |
| 6 | fit_all_phases | Python bool, selected flag |
| 7 | omit_kz0 | Python bool, selected flag |
| 8 | dxy_um | Python float, bands.dxy_um |
| 9 | dz_um | Python float, bands.dz_um, including supported 2D zero |
| 10 | lateral_zoom | Python float, bands.lateral_zoom, including supported fractional L without integer coercion |
| 11 | axial_zoom | Python int, bands.axial_zoom |
| 12 | input_scale | Python float, bands.input_scale |
| 13 | acquisition_mode | Python string, EXACT bands.acquisition_mode ("2d" or "3d") |
| 14 | acquisition_reference_sha256 | Immutable tuple of EXACT ten two-tuples of (Python str,Python str), losslessly equal to bands.reference_sha256 in its approved order |

Thus resolved_settings consists of the original CE05 ordered prefix followed
by EXACTLY ("acquisition_mode", bands.acquisition_mode) and
("acquisition_reference_sha256", bands.reference_sha256), in that order.
The ten-file input tuple order is mainfile.c, small_math_funcs.c, helpers.c,
sirecon.c, sirecon.h, Makefile, usr_local/include/sfftw.h,
usr_local/include/srfftw.h, usr_local/include/fftw3.h, drift_n_phasestep.c,
with their exact ledger hashes. It is retained as the tuple of name/hash pairs,
not a digest, concatenation, flattened string, sixteen-file union or replacement
of the result's six-file reference_sha256. The input ten-file tuple and result
six-file tuple therefore have DIFFERENT lengths/order and declared purposes.
An empirical transfer retains its separate CE03 provenance without being
rewritten to either tuple.

For original PreparedBands, EVERY source field and resolved_settings key,
value kind/value and order stays exactly CE05: the original13-key tuple
receives NO acquisition keys or other metadata changes. All other result
fields and trace extensions remain as already specified above. No unlisted
provenance key is added to EstimatedParameters.

Input validation still requires the actual approved ten-file tuple on an
AcquisitionBands INPUT, even though the successful estimator RESULT has six.
A forged/malformed/wrong-order/wrong-hash AcquisitionBands provenance tuple or
invalid acquisition_mode raises ParameterEstimationError before estimation,
as a used-record validation error; no partial result or fallback schema.
This does not change original PreparedBands validation or its errors.

CE05's entire numerical helper domain still applies: SX>0,SY>0,SX!=SY,
finite forward/reverse/combined/correlation, no replacement optimizer, no
minimum signal or arbitrary iteration cap. omit_kz0 in true 2D removes all
overlap samples; estimation then rejects at the actually reached CE05 operation
(search zero-coarse polar conversion or known no-energy fit). It is not a
silently ignored flag. Known zero carrier can remain valid. Search zero coarse
carrier still rejects, and general-parabola zero/negative results are retained
where actually defined.

For each time t, construct a one-time AcquisitionBands value by slicing
quadratures/noise, input_shape T->1 and all time-indexed diagnostics consistently.
Preserve alpha (independent of T), modes, sampling, camera state/source and
the resolved preprocessing results. Slice/relabel sentinel and ModeEvent time
indices to zero. A retained header vector uses its first D*Z*P*(N+1) entries
for the one-time metadata shape; it is not re-estimated or consumed numerically
by known reconstruction. No raw replay/rescale occurs. Pass the
ACTUAL estimated carriers[t] and modulation[t] to reconstruct_known on that
record and the same optics/transfer, with explicit filtering parameters.
For a time-varying Wiener schedule compute the effective full-series w_t first
and call with that value and wiener_increment=0. Stack the returned time1
images. This public raw->bands->estimator->known composition is required,
with 3D/2D, radial/full, irregular phases, off/drift as selected.
Successful estimation does not guarantee every later filter stencil/domain.
No clipping/refitting to force a known reconstruction is authorized.

## 8. Safe rectangular and Z1 empirical radialft preparation

prepare_bead_otf retains its existing signature, OtfError, PreparedOtf and
OpticalTransfer records, defaults and CE03 operation order. Its raw axes
broaden from (P,Z,N,N) to (P,Z,Y,X), X even, X,Y>=10, Z>=1;
P remains odd in {1,3,5,7,9}. Maps broaden to (Y,X), exposure backgrounds to
(Z,P). All original dtype/finite/optics/sphere/phase/rank/normalization safety
rules persist. P1 still requires bead compensation off. No supplied bead phase
estimator/list is invented; selected mainfile.c uses uniform rows divided by P.

Every CE03 preparation equation applies with these explicit substitutions:

- Actual Fourier transform, peak scan, periodic neighbors and centering factors
  use their true X,Y,Z. The centering ramp is
  exp(+2*pi*i*(ix*xc/X+q(iy,Y)*yc/Y+q(iz,Z)*zc/Z)).
  At Z1 the axial forward sum is the identity; no 3D specimen claim follows.
- The fixed10 vertical edge operation is unchanged. In the horizontal step,
  for each y snapshot diff=(right-left)/2, then k=0..9:
  add diff*f_k at flat address y*(X+2)+k, subtract diff*f_k at
  y*(X+2)+Y-1-k, with f_k=1-sin(pi*(k+1/2)/20).
  This literal Y in the x address is mainfile.c:625. Do not substitute X.
  Keep the source padded real allocation (Z,Y,X+2), initialized0, and every
  sequential write. Padding writes are not detector samples or new Fourier
  inputs. Any actual negative/out-of-allocation address rejects even when
  diff=0. All in-allocation writes are retained. With X,Y>=10 the simple
  last-row bound requires Y<=X+2; no square-only restriction remains.
- Both lateral increments for bead compensation are dkr=1/(Y*dxy),
  even though the x transform used X. dkz=1/(Z*dz).
  Shifted continuum-sphere rho uses
  (ix*dkr+m*cos(theta)/(M*linespacing),
   q(iy,Y)*dkr+m*sin(theta)/(M*linespacing),q(iz,Z)*dkz).
  No “physical correction” to 1/(X*dxy) is authorized.
- Radial bin index is rint(hypot(ix,q(iy,Y))), not scaled physical radius.
  Include only bin<X//2+1; average actual stored half-plane counts.
  All CE03 symmetry, axial/radial repair, cleanup and origin-fit operations
  follow with R=X//2+1,K=Z. At Z1 the axial symmetry loop is empty and
  the radial values are made real at their sole axial sample.
- Repair/cleanup accesses retain literal FLAT-allocation checks and write order.
  In particular positive fix_radial_from<=X//2 at K1 eventually reads the
  last row's ind0+1 outside allocation; it rejects. Zero disables; larger
  than X//2 is the defined no-op. Do not mask this by duplicating K1 cells.
  The unused center/background diagnostic still rejects yc=20 or unsafe
  floor(zc) reads, even if its numerical value is discarded.

PreparedOtf.quadratures is (P,R,Z), background_counts (Z,P), centers xyz and
all other diagnostics remain CE03. The returned transfer is radial (O,R,Z),
dkr=1/(Y*dxy), dkz=1/(Z*dz), preserving common/default order0 maximum scale.
Signed/zero slopes, complex intermediate quadratures and every valid original
square call stay accepted. Direct declared zero transfers remain distinct from
empirical zero normalization failure.

This is the mainfile radialft VALUE mapping. Its output file header axes
(K,R) are not sirecon's 2D reader's (R,1) declaration. For Z1 composition,
use the ACTUAL prepare_bead_otf(...).transfer record directly as the transfer
argument to sample_otf, estimate_parameters and reconstruct_known. Its
complex128 (O,R,1) values and original positive sampling metadata are already
the accepted public value layout; no transpose, redeclaration, quantization
or metadata rebinding is numerically required. The general K1/dkz resolution
in section7 and section9 applies, not the legacy file loader's fixed dkz1.

declare_otf retains its ORIGINAL exact-complex64-representable declared-sample
domain, dtype rules and OtfError behavior. It is not a coercion path for
computed empirical values. A valid empirical coefficient that is not exactly
complex64-representable remains valid in PreparedOtf.transfer and its direct
sampling/estimation/filtering; passing that same raw coefficient array to
declare_otf must reject that out-of-domain input under CE03. Do not silently round it,
weaken that declaration domain or prefer a favorable exactly representable
computed table to avoid the composition obligation.

The required public composition begins at general permitted raw bead arrays,
calls prepare_bead_otf, then supplies that returned transfer to estimation of
actual prepared specimen bands and to per-time known reconstruction using the
ACTUAL estimates. It also includes independently calculated known-parameter/
sample controls before fitted composition. Both positive specimen dz and
supported dz0 consume the original prepared transfer metadata. All real/
imaginary sample values, unequal order amplitudes, finite rank/fit/stencil
limits and readonly input behavior remain binding; a valid empirical table
does not guarantee every later optical/sample request or regression is defined.

A finite representability discriminator is P3,Zbead1,X=Y32, compensation off,
background0, cleanup/origin/radial repair off, phase weights w=(1,2,3), and
raw phase p counts3*w[p] at (16,16), w[p] at (16,18), all else0.
Edges are unchanged and the center is (16,16,0). The center-order transform
after centering is 6+2*exp(-2*pi*i*kx/16); radial bin1 has the five cells
(1,0),(0,1),(1,1),(0,-1),(1,-1). Common order0 maximum8 gives
H0[1,0]=(17+3*cos(pi/8))/20, which is not binary32-exact.
These finite cells give an independent algebraic check, not a fixture-only
exception to direct consumption. Product agreement must retain the computed
complex128 coefficient under the predeclared error budget, never replace it
with its nearest complex64 value.

No unchanged legacy file chain is claimed. The separate radialft2d_Hesper.c
tool has another algorithm and remains ledger M41, outside this selected
empirical reference. It cannot be substituted as an oracle.

## 9. Known reconstruction: dimensions, filter variants, zoom and taper

Add these keyword-only options to reconstruct_known, preserving every old
default and existing argument:

~~~python
wiener_increment=0.0,
power_taper_exponent=None,
precise_taper=False,
filter_overlaps=True,
explode_factor=1.0
~~~

output_taper additionally permits "power". For power, exponent is required
finite signed real within float32 magnitude. Otherwise a supplied exponent is
validated finite and retained but not numerically used. The three flags keep
their actual bool domains. Increment and explode factor are finite signed real
scalars within float32 magnitude; explode may be zero/negative. They describe
defined source debug views, not an improved reconstruction algorithm.

Accepted bands may be original PreparedBands (unchanged validation) or
AcquisitionBands (new used-field domains). The latter permits Z1/dz0/safe
fractional L and noise (T,D,O). It requires O>=2. Use v[t,d,m] in the
same CE04 inverse-variance weights. All CE04 filtering/support/traversal,
conjugation, transfer interpolation, integer representation and error rules
are incorporated unchanged except explicit substitutions below.

For Z1, native dkz=1/dz if dz>0, else transfer.dkz. The source else is dz<=0;
public support selects dz=0 only, with negative pitch outside the declared
physical domain. This is not the drift prepass, which has no such fallback.
Require K=1 and use the ACTUAL declared or prepared OpticalTransfer directly,
including computed complex128 values not exactly representable as complex64.
Keep the transfer's original positive dkz; no dkz1 rebinding or declaration
round trip is required. Section7 defines zero-index/duplicate-vertex sampling;
all actually evaluated ratios, cutoff casts and stencil checks remain binding.
CE04 cutoff construction is evaluated then its >=floor(Z/2) clipping sets
EVERY cutoff to0. c[1] is still accessed, so O1 is not supported.
Axial sample is0. Damping when c0=0 is still singular if actually visited;
it is not repaired to a 2D radial-only damping. Y1 empty filter loops remain
a permitted positive paired case. Native Nyquist/odd-Y omitted-row and reflected
zero-write quirks apply exactly as CE04, including untouched values.

With filter_overlaps=False, retain self power and w². In CE04's ordered
other-direction/signed-order loops, skip a term UNLESS self m=0 and other n=0.
The exact self exclusion is still first. Thus center orders of OTHER directions
still share denominator powers; side orders keep their self-only denominator.
No relocation or taper parameter is changed by this flag.

For a one-channel T-time call, start w=wiener>0 and before each time execute
w += wiener_increment/T. The effective mathematical sequence is
w_t=wiener+(t+1)*wiener_increment/T, t=0..T-1.
Require every effective w_t finite and strictly positive under the owner's
selected positive-Wiener scope. This is the source pre-increment at
sirecon.c:508, not linspace(wiener,wiener+increment,T).
Use w_t**2 in filtering. Automatic-Wiener/zero-Wiener is not selected or repaired.
Negative increment is permitted when every effective value stays positive.
No multichannel schedule or double increment in per-time composition.

For nonprecise taper, CE04 defines rho from shifted object frequency Kxy,
global apocutoff R+|carrier[0]|*(O-1) and zapocutoff c[1].
If zapocutoff>0, rho=sqrt((|Kxy|/apocutoff)**2+(abs(z)/zapocutoff)**2);
otherwise rho=|Kxy|/apocutoff. Clip rho ABOVE at1 only.
Taper none=1; cosine=cos(pi*rho/2); power=(1-rho)**gamma.
For positive base, any finite gamma with finite result is allowed; no invented
positive-gamma-only cutoff. At base0, gamma>0 gives0. The gamma0 case uses
the exponent-zero constant convention T=1, including base0; this convention
must be specifically challenged in source review against source pow and
the unqualified historical math library. Negative gamma at base0 is singular
and rejects, not infinity, an epsilon or a clipped exponent.
No arbitrary output mask replaces this source function.

### 9.1 Complete precise-boundary procedure and unsafe origin disposition

When precise_taper=True, main precomputes sector boundaries BEFORE filtering,
even if output_taper="none" or the filter will use its 3D ellipse.
Each carrier must support a defined nonzero polar angle. In direction order:

a_d=atan2(ky_d,kx_d) in (-pi,pi],
b_d=a_d-pi/(2*D), b_(d+D)=b_d+pi.
Independently wrap EACH once into [-pi,pi] by >pi subtract2*pi or <-pi add2*pi.
Do not sort boundary entries or infer a different polygon.

A next-start query for direction d sets target=b_d+pi/D,
best_distance=2*pi, saved=d. Scan j=0..2*D-1:
diff=target-b_j; if diff>pi subtract2*pi, else if diff<-pi add2*pi.
On strictly smaller abs(diff) replace best and saved. Ties retain earlier
scan entry. Return b_saved. No repeated modular wrap or angle sorting.

The predicate between(arg,a,b) sets lo=min(a,b),hi=max(a,b).
If hi-lo<pi/2, return arg>lo AND arg<=hi.
Otherwise return
(arg>0 AND arg>hi AND arg-2*pi<=lo)
OR (arg<0 AND arg<=lo AND arg+2*pi>hi).
Equality at pi/2 selects the SECOND branch. Its zero-angle exclusion in that
branch is literal, not repaired.

Only when a taper is on AND zapocutoff<=0, calculate arg=atan2(Ky,Kx).
For each d ascending, let hi=next_start(d); hi2=hi+pi wrapped once.
If between(arg,b_d,hi) OR between(arg,b_(d+D),hi2), select d and stop.
If none matched, the source uses uninitialized intersection vectors; reject.
Let x0=(O-1)*kx_d,y0=(O-1)*ky_d,k=tan(arg),
v=x0+k*y0, disc=v*v-(1+k*k)*(x0*x0+y0*y0-R*R),
den=1+k*k. For finite defined disc>=0 compute
xs_plus=(v+sqrt(disc))/den, xs_minus=(v-sqrt(disc))/den;
intersections=(xs_plus,k*xs_plus),(xs_minus,k*xs_minus).
The limit is the larger Euclidean distance; a tie returns the second.
Require finite positive limit. Set rho=|Kxy|/limit and apply the ordinary
upper clip/taper. Do not replace this with geometric radial intersections
that avoid tan or choose a different sector.

Undefined atan2(0,0) is excluded consistently with accepted CE05 real-arithmetic
domain. Active precise 2D filtering visits order0's DC when Y>=2, even when
order0 is ultimately omitted or its damping is0. Therefore that ordinary
active precise-2D call has NO qualified numeric result here: reject at the
zero polar conversion; do not invent a DC angle or silently switch to ordinary
taper. Other sector gaps, negative discriminants, singular/nonfinite tangent
or zero limits also reject. A nonzero-carrier precise flag can remain finite
when taper is off, zapocutoff>0 (the 3D ellipse is used), or filter traversal
is empty at Y1. Those permitted-positive paths must not be rejected merely
because the flag exists. This is a visible unsafe subdomain, not an implemented
claim for the absent portable active-DC reference. If essential, coordinator
intake must name and independently review that reference decision before A;
this contract does not authorize a repair.

### 9.2 Exact zoom embedding, inverse dimensionality and exploded phase

Let Xo=L*X,Yo=L*Y,Zo=A*Z, exact integer extents. Safe L may be fractional,
for example L=3/2 on X=Y=10 gives15-by15 output. Same alpha uses L².
Do not round L itself to an integer. At each native full index lift
x=q(j,X),y=q(i,Y),z=q(k,Z), with positive even Nyquist as CE04.
Read/conjugate half quadratures by CE04 all-axis rules; put into the zero full
output array at (z if z>=0 else z+Zo, y if y>=0 else y+Yo,
x if x>=0 else x+Xo). No endpoint splitting or coefficient interpolation.
For L>=1 the lifts are injective. Fractional Xo/Yo is rejected before work:
source lookup fill uses truncated bounds while final assembly loops use
untruncated comparisons and can read uninitialized/out-of-allocation entries.
Shrinking/colliding grids are not a defined deterministic decimator.

For "3d" the inverse is the CE04 unnormalized positive full backward sum
over (Zo,Yo,Xo). For Z1 source creates only a 2D plan, regardless of A.
Transform ONLY output plane0 by that backward 2D sum; other planes remain
the initialized zero arrays. Do NOT apply a 3D inverse or replicate the plane
for A>1. This distinct dimensional result is required at the public image,
not a helper-only test.

Coordinates remain CE04:
x_um=(j-floor(Xo/2))*dxy/L, y_um=(i-floor(Yo/2))*dxy/L,
z_um=(h-floor(Zo/2))*dz/A. At Z1/dz0 these are labels with zero axial pitch;
no physical axial interpolation/resolution is promised. The inverse array
indices stay unshifted, with centered labels used ONLY in the lateral phase.
No checkerboard, fftshift or output registration.

For side m assembly, use
2*Re(u_m[h,i,j]*exp(+2*pi*i*explode_factor*m*
                   (carrier_x*x_um[j]+carrier_y*y_um[i]))).
Order0 is unchanged and follows its omission flag. Filtering, optical support,
transfer lookup and taper use UNEXPLODED carriers; explode only multiplies
the final assembly ramp. L/A affect spacing and upstream alpha as declared.
Signed output is retained, with no gain fit/positivity normalization.

KnownReconstruction keeps all existing fields and dtypes. For new mode/options,
resolved_settings additionally records acquisition_mode, wiener_increment,
effective_wiener (immutable T-tuple), power_taper_exponent, precise_taper,
filter_overlaps, explode_factor, in that order. Original calls retain their
original resolved-settings keys. Add mode_trace (immutable tuple, default empty
for the unchanged path) with ModeEvent records:
"wiener-step" at each t (direction_index=0,z/phase=None), details
previous,increment,effective (increment is the actual per-time step
wiener_increment/T, not the full-series increment);
"sector-boundaries" before each time's filtering, details
carrier_angles_rad (D,), boundary_angles_rad (2*D,);
"precise-query" for each actually visited query, details object_frequency_xy,
angle_rad,next_boundaries (D,), selected_direction, discriminant, limit,rho.
Do not emit a success event for an unsafe query; the whole call rejects.
Original fields x/y/z, image, filtered bands, radial/axial cutoff and source
metadata continue their declared meanings. Extra fields introduce no new
scientific fallback, extra numerical fit or array ownership exception.

## 10. Validation, representation and operation-time failures

Input/record validation precedes copies, transforms and numerical preparation.
Unsafe branch selectors with known structural causes reject before numerical
work; data-dependent failures reject when reached, returning no partial result.
A failure in any time/direction/order/query rejects the WHOLE public call.
There is no unavailable-but-successful result, fallback, omitted requested mode,
zero-filled failure, added epsilon, fitted gain or alternate optimizer.

For the new entry and new records, standard NumPy integer/float16/32/64 real
arrays are permitted under the stated raw representation rules; maps, phase/
timestamp/scalar mathematical inputs use binary64. No bool, object, string,
complex real input or extended-precision real kind. Raw on/off values must be
exact finite float32 representations; they are not silently rounded across the
sentinel branch. Non-raw source-float inputs must be finite and within float32
component magnitude; existing CE02 original-entry domain is not narrowed.
Counts/indices/selectors are integral and never booleans; no truncation of
public count declarations. Only explicitly source-truncated frequency/cutoff
and coordinate operations above truncate.

A downstream AcquisitionBands used-field check requires actual record type,
valid shape/counts/mode, complex128 finite quadratures, float64 finite POSITIVE
noise (T,D,O), valid dxy/dz/L/A, alpha matching 1/(X*Y*Z*L²*A*D), and correct
ten-file INPUT source identity. EstimatedParameters result provenance is the
separate exact CE05 six-file tuple plus the specified resolved_settings suffix
(section7), not a ten-file result tuple. Valid prepared OpticalTransfer records
retain CE03 complex128 samples without an exact-complex64 declaration check;
declare_otf itself retains that exact representability check. Both writable
and read-only/strided valid numerical
inputs are accepted and copied. No mandatory owning/contiguous input restriction.
Stage diagnostics unused by estimation/filtering are not reconstructed or
checked for raw consistency. This retains CE02–05's public value-record model.
New record validity does not require accepting arbitrary invalid original
PreparedBands fields.

Use nonoverflowing arithmetic to check all actual source signed32 expressions,
casts, offsets, products and loops before they can overflow: X/Y/Z/P/Q/D,
T/F metadata counts, (X+2)*Y*Z, (X//2+1)*Y*Z, X*Y*Z,
D*Z*P, D*P*(N+1), Q*P, D*O, O table sizes, peak wrap/reflection sums,
S and middle-section offsets, cubic matrix/RHS extents, rdistcutoff² and
integer kx²+ky², native/output products and every flattened index.
Include finite ceil/floor/pow-to-integer cutoff/index conversions BEFORE casts.
No arbitrary signed32 byte limit is inferred from size_t multiplications.
Use source unsigned32 byte constraints at explicit unsigned main workspace
casts and signed32 at the explicit lookup allocation cast, as already CE04:
8*Xo*Yo*Zo and 4*Xo*Yo*Zo fit unsigned32, lookup 4*Xo*Yo fits signed32.
All source size_t byte extents must be representable on the declared platform.

Every owned target float64/complex128/bool array, copied used input, diagnostic,
aggregate time/order trace and coefficient array must have shape, strides and
bytes representable in native intp on the required 64-bit platforms. For shape
dims d and item size s, require all d nonnegative<=INTP_MAX and
s*product(max(d,1))<=INTP_MAX, including empty shapes. Source allocations
separated per phase/order do not introduce an invented aggregate signed32
volume bound; native aggregate output/diagnostic arrays still need intp
representation. There is no fixture-size, trace-length or smaller arbitrary
memory budget. Actual allocation failure within this representable domain is
an operation error with cause retained.

The signed finite source mathematical domain is preserved: negative corrected
counts/sums, signed/zero slopes, nonpositive high-pass selector, signed suppression
radius, zero/signed modulation and signed outputs can succeed wherever the
ACTUAL selected operations are defined. No extra positivity/minimum-signal
condition is introduced. The positive Wiener and physical optics restrictions
remain the explicitly selected public scope, not an assertion that every
source real-number branch was implemented.

Operation errors include all inherited CE02–05 failures and these additional
specific causes:

- zero selected on/off equalization sum, rank-deficient used separation design,
  unresolved finite full-rank factorization, zero/underflowed alpha or nonfinite
  correction/edges/sums/transforms;
- unsafe partial metadata/null reference, unsupported active reference type,
  underallocated cubic design, singular actual cubic fit, nonfinite polynomial
  powers/coefficients/evaluation or unsafe source timestamp accesses;
- nonfinite unused optical cutoff arithmetic when the source actually calculates
  it; unsafe fixed10 edges; a nonterminating off loop in the selected prepass;
- empty inside/outside off-combination set, zero/nonfinite noise or denominator,
  overflow in signal/statistic/ratio/weighted array result;
- unsafe transfer stencil, including every zero-weight vertex; unsafe empirical
  repair/cleanup/unused diagnostic read, zero empirical scale/sphere divisor;
- selected search coarse-zero polar conversion, no/equal regression energy,
  positive floor on zero, undefined selected base phase and nonterminating/
  stagnant/nonfinite search progression, as CE05;
- unsafe nonintegral/shrinking output representation, source allocated-buffer
  mismatch, undefined precise polar/sector/intersection arithmetic, negative
  power at zero taper base, zero c0 when damping is actually evaluated,
  unresolved Wiener square/denominator or backend failure.

For each error identify its category/operation in informative text, retaining
the original cause for backend/allocation failures. Do not collapse all of
these into “unsupported 2D” or invent a numeric value for singular arithmetic.
An external timeout is incomplete evidence, never successful convergence.

Padding with nz0!=nz, Bessel O>=2's uninitialized highest cutoff,
two-objective paths that actually call the aborting overlap, automatic-Wiener's
always-empty midfrequency set and model replacement from uninitialized carriers
stay ledger U, excluded. Narrow O1/no-search Bessel and two-objective callers
can skip positive-order fits and use an initialized special c[0] taper cutoff;
with fit-all-phases on, safe initial-guess conversion and otherwise defined
arithmetic they are ledger D OUTSIDE selected support, not blanket U.
In 3D, P1 still makes the initial nordersIn-1 division singular; reducing
output orders to1 with P>=3 avoids that particular division. No O1 special-mode
feature or numerical oracle is introduced.
Their absence from signatures is not hidden implementation; unknown keywords
give TypeError and documentation names their exclusions. Explicit padding-to-
same-Z is a mathematical no-op, represented by selecting no padding, without
a new padding feature. A required correction of an unsafe reference returns
to coordinator intake with a separately named reference, not runtime repair.

## 11. Scenario and permitted-positive inventory

Each row is an observable decision/outcome obligation, not a test count.
Inherited CE02 C01–C22, CE03 O01–O41, CE04 K01–K29 and CE05 E01–E29
stay mapped to keepers. New-domain rows supplement them; they authorize no
test deletion or synthetic product-red requirement. A maps each obligation,
credible failure, independent oracle, stronger boundary proof and legitimate
positive alternative before product observations. B independently challenges
reachability, omissions, oracles and rejected positives.

| ID | Required observation, including paired positive/error distinction |
| --- | --- |
| A01 | Original D3/P5/O3 public 3D chain and default arguments unchanged; original records/errors/retired boundaries retained |
| A02 | True Z1 2D raw->bands->estimated parameters->known image, distinguished from a K1 transfer with Z>=2 specimen |
| A03 | Public reinterpret_2d_planes literal section mapping for BOTH layouts; nominal-plane equivalence only for z-major/D1/Zstack1, direction-major counterexample, aligned off/background provenance; actual helper->bands->estimate->known composition and effective-time flags |
| A04 | Uniform, explicit uniform-valued supplied list, irregular square/left inverse and reduced-order designs; actual Nyquist raw-slot retention |
| A05 | Step list p*step precedence over supplied list, scalar noise; D1/D2/D3 positive cases versus D>3 fixed-step allocation rejection; arbitrary-D explicit list positive |
| A06 | All on equalize/z/time policies, disabled flags inert; signed nonzero sums valid versus selected zero divisors |
| A07 | Source overlap/filter dz<=0 fallback inventoried; selected Z1 dz0 positive versus negative physical pitch outside support; ordinary prepass dz0 fails without fallback, positive-dz 3D unchanged |
| A08 | Radial/full complex K1 reconstruction and estimation with all CE03 stencil vertices; unsafe last lateral request versus slightly interior positive |
| A09 | 2D threshold multiplier1 versus ordinary3D5, equality/short-circuit masks and shifted complex cross transfers |
| A10 | 2D searched pair01, coarse divide1, finite ordered angle/magnitude trace including initial/subsequent ties and stale bracket state |
| A11 | Adjacent later SEARCH fits versus (0,b) KNOWN/reused fits; cumulative product applied to both, consumes updated previous factor |
| A12 | Products precede floors/phase replacement; raw direct diagnostics distinguished; zero factors permitted versus selected zero-floor/base-phase failure |
| A13 | 2D omit-kz0 removes all overlap samples, failure at actual search/known operation; known zero vector and weak unequal positive energies remain permitted |
| A14 | Per-time reuse fits fresh modulation from actual time data, no time0 amplitude replay; 3D no cumulative product |
| A15 | Safe rectangular empirical phase/FFT/center/compensation/radial normalization composition; square controls retained General raw-bead->actual PreparedOtf.transfer->sample/estimate/filter composition consumes complex128 values directly, without redeclaration, quantization or metadata rebinding; preserve CE03 declared-table domain. |
| A16 | Literal Y-based horizontal bead edge, including in-allocation padding writes, versus out-of-allocation writes; no “corrected” X substitution |
| A17 | 2D empirical K1 preparation with safe settings; active radial repair final-row failure versus zero/large-start no-op Direct consumption retains original positive prepared dkz for positive/zero specimen dz; no fixed-dkz1 value-record requirement. |
| A18 | Common empirical scale versus optional per-slot; continuum sphere, uniform bead phase/P and no specimen alpha remain distinct Computed non-complex64-exact coefficients are preserved in actual prepared transfers; raw declared samples still require exact complex64 representability. |
| A19 | Fractional L=3/2 integral lateral extents and L1/integer positives; nonintegral extents/shrinking unsafe reject |
| A20 | Alpha/L²/output pitch/center use actual fractional L, positive Nyquist lift with no split, no post-gain correction |
| A21 | 2D A>1 only plane0 transformed and later planes zero; 3D A>1 full inverse; no plane replication substitute |
| A22 | Cosine/none/power use same rho/upper clip after native filtering; fractional/signed/zero gamma on finite branches, negative-at-zero singularity; gamma0 explicitly constant1 |
| A23 | Precise boundary precompute ordering/one-time wrap/strict tie, including no-taper/3D/empty-loop finite positives |
| A24 | Active precise DC undefined polar, unmatched-sector uninitialized access, negative discriminant/zero limit reject; no circular fallback or invented DC angle |
| A25 | Suppression on/off, radius outer inequality/unused helper radius, dampen/omit precedence retained; c0=0 visited damping failure versus Y1 empty-loop positive |
| A26 | No-overlap filtering retains other order0 powers only for center, self always retained; normal filter untouched |
| A27 | Explode zero/negative/noninteger changes assembly phase only; support/taper/filter diagnostics unchanged, signed output retained |
| A28 | Wiener preincrement before t0 and signed increment/effective positivity; fixed increment0 old behavior; no automatic estimator fallback |
| A29 | N1 and N>1 off camera sums, never average; shared sentinel state and carried on extra background, traversal across times/directions |
| A30 | Edge on SUM of off frames and off rescale only N>1; separate off anchors; N1 zero off sum allowed where no later statistic divides it |
| A31 | Fourier off-combine integer cutoff AND integer scaled kx/ky; strict outside/equality-inside and correct cell counts |
| A32 | Negative signal2 clamp, one-zero branch, both-zero->1, positive noise weights; empty set/zero noise singular reject with valid nonempty positive-noise paired case |
| A33 | Order0 plus/side minus off weighting, variance factors unchanged; repeated BASE PLANE0 combination at later z, other planes uncombined |
| A34 | Off-combination skipped orders/nonpositive selector do not evaluate statistics; positive selector needs N>0; fixed selector-array representation |
| A35 | Actual raw middle-substack prepass, background only and fixed10 edge; small X/Y out-of-allocation rejection despite normal edge0/zero differences, X=Y10 overlapping-strip positive, no-drift Y1 preserved |
| A36 | Drift prepass first off ONLY for N<=Y+1 versus normal sum of N; N>Y+1 nontermination reject only when that prepass selected |
| A37 | Drift strict UNCLAMPED optical radial cutoff; unused axial cutoff still defined, no axial mask; exponent1/4 versus within1/2 |
| A38 | Positive/zero/negative high-pass selection and squared Gaussian factor; zero cross composite0; all-zero correlation retains initialized center |
| A39 | Absolute-real correlation (including negative peak), first-strict scan tie and periodic parabola/wrap with positive half endpoint; subz1 z forced0 |
| A40 | Between correction after separation/axial transform, all retained quadratures, first-sample origin/pixels and positive Fourier sign |
| A41 | Within2D default on0+off0 reference, per-phase moving on+off; N0 uninitialized-reference rejection versus N>=1 finite positive |
| A42 | Fitted 2D requires phase flag/allocation, usable metadata, P>=4/full-rank cubic; phase flag off fails BEFORE fit despite declared clock/P>=4; unfit/no-phase-clock positive with its actual estimator prerequisites |
| A43 | Ordinary 3D within cubic D>=4 and literal metadata indices; D3 underallocation, fast 3D uninitialized driftlist at EVERY D including1; no quadratic or initialized-zero substitute |
| A44 | 2D sample/evaluation alias mutation versus 3D distinct-vector/global-prefix mutation, first metadata block reused at later t |
| A45 | 3D within subtracts MEASURED between-dir x/y for d>0; within-only does not apply between correction, both-flags sequence does |
| A46 | Before-separation exposure correction applied identically to on/off including Nyquist, no inverse normalization or interpolation |
| A47 | Linked phases use +2*pi*dxy*drift dot phase kguess, 2D absolute FIRST off phase versus 3D p*2*pi/P; k0angles and 3D carrier divisor do not replace phase kguess |
| A48 | Linked-phase design supersedes steps/list; final noise from LAST z, full phase/matrix diagnostics per section; used full-rank versus singular design |
| A49 | Missing phase metadata/null diagnostic and fitted-drift null-clock errors; unselected flags add no work, unfitted 2D with adjust_phases=False needs no clock; fake timestamps do not qualify linked phase |
| A50 | Fast no-drift same canonical values; fast D>1 drift unsafe, D1 BETWEEN-ONLY initialized-zero bypass; fast within-3D D1 unsafe, fast within-2D D1 separately qualified by active estimator/fit/phase path |
| A51 | Read-only/strided input ownership/immutability and valid caller-mutated bands; no hidden raw replay; all trace schemas and time slices complete Actual complex128 prepared transfer consumption has no quantization seam; estimator result uses exact CE05 six-file provenance, with input ten-file acquisition tuple retained losslessly in the exact two-key ordered settings suffix. |
| A52 | All shape/type/finite/scalar/flag/record/source/alpha failures paired with endpoint/negative/zero positives actually allowed Distinguish invalid ten-file input provenance from the successful six-file result; preserve prepared complex128 versus declared exact-complex64 domains and exact resolved_settings keys/value kinds/order. |
| A53 | Source signed/unsigned/intp representation and actual stencil/address checks, including zero weights and diagnostic extents; allocation/backend operation failure with no partial result |
| A54 | Docs distinguish math/unsafe subdomains/outside-support modes (including otherwise-defined O1 no-search Bessel/two-objective), alternative tools, literal header regrouping/file limits, binary agreement and physical recovery Freeze six-file estimator result versus ten-file input/settings provenance and unchanged original CE05 metadata; require direct empirical-transfer consumption without quantization/rebinding. |

The caller-composition proof for A02/A40/A45/A47 must start at independently
specified RAW on/off exposures and explicit metadata/camera/transfers, traverse
preparation, consume actual estimated carriers/modulations and compare the
final signed reconstruction to an independent finite expectation. Asserting a
standalone translation identity or passing true parameters around the estimator
does not discharge these obligations. Include known-parameter controls FIRST
to isolate preparation/filter behavior, then actual fitted-parameter composition.
Useful ordinary three-direction/five-phase/three-order 3D remains a required
public control throughout. No hardcoded phantom replaces parameterized arrays.

## 12. Independent numerical obligations and bounds before implementation

A derives finite/algebraic expectations and predeclares bounds BEFORE seeing
product discrepancies. This document fixes the algorithm, not a universal
accuracy epsilon. Use source equations, independent direct sums, analytic modes,
exact small linear systems/polynomials, and independent observations. Never
import production helpers, execute retained C, replay a shared forward model
as the only oracle, fit registration/gain, tune truth, tune tolerances or
discard an unsuccessful finite case.

Let u be binary64 unit roundoff and gamma_n=n*u/(1-n*u) for n*u<1.
An n-term scalar reduction with known input absolute errors e_j has an
absolute budget sum(e_j)+gamma_n*sum(|term_j|), with additional operation/
transcendental representation bounds stated separately. Complex reductions
bound real/imag components and multiplication errors; do not pretend an FFT
has the same operation count as a direct sum without evidence. An independent
higher-precision or algebraic observer bounds its own error separately.
These formulas are derivation tools, not a fixed task-wide tolerance.

Required conditioning/decision obligations:

1. **Transforms, scale and camera.** Independently sum the finite negative/
   positive exponentials with declared origins. Bound scalar correction, alpha,
   P/voxel reductions, unnormalized inverse and assembly separately. Constant
   and displaced-impulse controls distinguish missing P, missing direction/zoom
   normalization, phase sign and centered assembly labels. At Z1,A2, zero
   later planes are a dimensional discriminator independent of output gain.
   A native Nyquist mode distinguishes endpoint retention/lift from splitting.
2. **Separation and cubic fits.** Use analytic/exact inverse cases and an
   independent coefficient construction. For cubic controls choose
   B_i=B0+c1*tau_i+c2*tau_i²+c3*tau_i³ with at least three distinct nonzero
   relative timestamps; expected coefficients/evaluations are algebraic.
   An overdetermined perturbation orthogonal to the three design columns
   distinguishes unweighted least squares. Derive matrix perturbation bounds
   using an independently bounded inverse/pseudoinverse norm, e.g. for a square
   system require ||A^-1||*||deltaA||<1 and bound coefficient error by
   ||A^-1||*(||deltab||+||deltaA||*||c||)/
   (1-||A^-1||*||deltaA||), plus solve/observer error.
   No fixed condition cutoff rejects legitimate near-collision phases/times;
   unresolved finite precision is reported honestly as an operation error.
3. **Drift power and peak.** Independently form middle-section phase sums and
   the real inverse correlation. Translation controls use independent shifted
   raw patterns, not only a phase-ramp helper. For f_a(c)=|c|^(a-1)*c,
   c0=0 with perturbation <=e has output <=e^a. If |c|>e, a local norm bound
   e*(|c|-e)^(a-1) applies for 0<a<=1; for |c|<=e a safe bound is
   (|c|+e)^a+|c|^a. Include high-pass, Fourier-sum and absolute-value errors.
   Compare integer peak decisions only when an independent gap exceeds twice
   the correlation error bound, or prove the exact constructed tie/symmetry.
   Zero-map initialized-center behavior is separate, not evidence of a unique
   physical drift.
4. **Subpixel decision.** For s,c in the parabola, known errors es,ec and
   |c|>ec, a bound for offset error is
   (es*|c|+|s|*ec)/(|c|*(|c|-ec)), plus observer arithmetic.
   Propagate to strict half-dimension wrap. A global absolute maximum gives
   |offset|<=1/2; use that proof for unreachable clipping branches, not a
   test-only estimator seam. Exact zero curvature is a declared branch,
   not any tolerance-based “nearly flat” substitution.
5. **Linked correction.** Independently use displacement in detector pixels,
   dxy in um/pixel and phase kguess in cycles/um:
   dxy*(pixels)*(cycles/um) is cycles, times2*pi radians. Fourier correction
   uses index/X so its phase is dimensionless too. A displacement error delta
   contributes <=2*pi*sum(|frequency|*|delta displacement|) to the unit-ramp
   absolute error, using |exp(i*a)-exp(i*b)|<=|a-b|.
   Include declared phase/design and polynomial conditioning. Contrasting
   supplied estimation vectors/angles with phase kguess must expose their
   actual caller distinction.
6. **Off statistics/products.** Independent cell enumeration uses integer
   cutoff/frequency bins, half-plane counts and repeated plane0 state.
   Derive absolute sum/power errors, divide by declared counts, and propagate
   subtraction/noise denominators before square roots and weight fractions.
   Bound sqrt near zero separately; do not smuggle in a signal floor.
   A positive margin from each noise/weight divisor supplies conditioning.
   Products of 2D factors use cumulative product error, not independent
   per-order tolerance after floors. Frozen CE05 finite-search decisions retain
   their own threshold/strict-improvement margins and full trace expectations.
7. **Filter/taper/assembly.** Positive w_t provides a denominator lower bound
   w_t² when weights are nonnegative. Propagate complex transfer, modulation,
   scalar noise and support decisions before relocation. For base b>0,
   power derivative gamma*b^(gamma-1) gives local conditioning; at b0,
   positive gamma may need a Holder rather than Lipschitz bound. Exponent0
   is the separately declared constant branch. For precise geometry, no bound
   can justify an uninitialized sector, zero polar input, negative discriminant
   or zero limit; those reject. Compare native-filter-before-relocation and
   unnormalized centered assembly independently.

Sanity controls supplement, never replace, complete public proofs:
unit self term with w=0.5,no taper/suppression gives0.8; damped weight0.1,w1
gives1/11; 2D direct fitted (2,3,5) produces cumulative (2,6,30) before floors;
one-channel T2,w_initial0.2,increment0.2 yields effective (0.3,0.4), not
(0.2,0.4); L1.5,X=Y10 gives15-by15 labels spaced dxy/1.5.
For cubic times (0,1,2,3), displacements (0,1,8,27) in one coordinate give
c=(0,0,1); a shifted absolute origin must retain that same relative fit under
the specified mutation, not a re-fit with a free constant. Off noise values
n_on=4,n_off=1 and signal magnitudes2,1 give u=1/2,v=1,
on_fraction1/3,off_fraction2/3, with opposite side-order sign.
None of these controls authorizes replacing an actual source branch.

## 13. Integrated acceptance and claim limits

Coverage remains approved behavior plus independent risk review; percentages
advisory, no selected percentage target. All installed complete native
statement/branch JSON/HTML/global/package/file/platform reports remain required,
including never-imported files and relevant subprocesses. No gate/dependency/
policy, test discovery or coverage exclusion change is authorized.

CE06 acceptance is for ONE exact integrated candidate on the completed CE05
baseline. Independent complete source-contract review precedes one fresh native
blind A covering ALL aggregate obligations and intermode compositions, then one
fresh native B reviewing the complete checkpoint. Restricted C owns only the
named runtime; no reviewed-test/fixture/workflow/dependency/policy authority
follows. The exact aggregate must pass full local make verify and original
Ubuntu24.04/macOS15 qualification, then fresh D assesses the ENTIRE passing
candidate before readiness. All 13 phases, strict outcomes, fixed two workers,
complete reports, wheel/RECORD/import/audit and same-run M25 CONVERSION increment
<=33,554,432 bytes remain. Missing/failed evidence blocks readiness.

The default exact-candidate full-local gate applies before opening/reopening
the single stacked PR (draft included) or pushing to an open PR. Logical
CE06a–d groups are not partial passing baselines, separate role chains, PRs
or follow-on user tasks. Their phases/off/drift/zoom/filter domains must actually
compose through AcquisitionBands in this one candidate. No internal group is
deferred to CE07 or accepted solely as an unused primitive. A/B/C/D corrections
keep their required fresh reviews and cumulative accounting; there is no human
scenario/review/repair cap. CE07 starts as the separate next task ONLY after
fully completed CE06. No merge, release or external message is authorized.

The useful ordinary 3D domain and all accepted CE02–05 behavior remain binding.
Outside selected support remain alternative otf2d/wiener2d, I2M/two-objective
bead, alternate builds, file-order duplication/diagnostics and multichannel
orchestration. Narrow otherwise-defined O1/no-search Bessel/two-objective
callers stay explicitly D outside scope; multi-order Bessel's missing cutoff
and actually reached two-objective overlap abort remain U. Negative physical
pitch remains outside public support despite source overlap/filter fallback.
Unsafe padding and automatic Wiener remain excluded.

If active precise-2D DC is essential, coordinator intake must name and
independently review a portable convention/corrected reference; no implementation
author chooses one. No other scientific choice is delegated to C. Historical
C binary agreement, recovery and physical resolution remain distinct outcomes.
