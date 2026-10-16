# Known-phase 3D integer-carrier diagnostics v1

**Version 1.0. October 16, 2026.** The owner's standing roadmap continuation and direct successor-launch approval authorize this dependency-ready Phase5 foundation above accepted PR36. This contract selects a finite diagnostic scan. It supplies no automatic physical-carrier identification, independent phase-step inference or continuous refinement.

## Public boundary and fixed calibration meaning

```python
from simrecon import VolumeCarrierCandidate, scan_volume_carriers

rows = scan_volume_carriers(
    images,
    response=response,
    voxel_size_um=(dz, dy, dx),
    phase_steps_rad=actual_steps,
    candidate_carriers_yx=[(ky0, kx0), (ky1, kx1)],
    order=1,
    calibration_carrier_bins=(ky_c, kx_c),
    coordinate_offset_yx=(oy, ox),
    phase_reference_shift_rad=delta,
)
```

Only images is positional. All eight keywords are required; ordinary Python argument-binding TypeError applies. One call handles one orientation/channel/time and one positive order m=1 or2. Images have phase/z/y/x axes. Spacing is z/y/x in micrometres (µm); physical frequencies are cycles/µm; phases are radians. Output gains and fit diagnostics are dimensionless. The result is a built-in tuple of new frozen-binding VolumeCarrierCandidate records in caller order, including duplicates.

The supplied empirical response, calibration carrier, coordinate offset and calibration-to-specimen phase-reference shift stay **fixed across all candidate rows**. They select the already approved phenomenological response and constant gauge in [physical-frequency sampling](empirical-frequency-sampling-v1.md). Calibration carrier sets that gauge; it need not equal any candidate. No physical invariance of an actual optical response under changing illumination geometry is inferred. The caller establishes calibration/specimen compatibility and provides genuinely known actual phases for this intermediate slice. Nominal commands alone are not unknown-step estimates.

The operation separates observed volumes once under the supplied actual phases, computes their finite Fourier coefficients, samples transfers at explicit detector frequencies, and reports a free complex gain fit for each candidate. It does not rank/select candidates, infer a search window, interpolate observations, wrap frequencies, change reconstruction, correct images, infer phases/drift, process files or authenticate provenance. Existing APIs, dependencies and gates remain unchanged.

## Inputs, validation and ownership

Images and phase_steps_rad inherit exactly the public representations, binary64 snapshots, finite checks, represented phase basis, numerical rank rule, SVD least-squares semantics, accuracy/range rules and errors of [volume separation](volume-phase-separation-v1.md). N>=5; every spatial size is positive. Both positive orders select c1/c2 from that same five-column fit; do not double fundamental phase steps for m=2. Signed data, unequal N>5 steps, off-model projection, huge represented angles, every real integer/floating width/endian, singleton axes, strided/Fortran/read-only plain arrays remain valid.

response is an EmpiricalVolumeResponse instance, including ordinary record subclasses. Validate every public field with the source-response rules of [physical-frequency sampling](empirical-frequency-sampling-v1.md#response-and-scalar-validation-ownership), including unused rows/samples, tolerated coordinate metadata, exact canonical source geometry, spacing/origin/source and unrelated getter exceptions. Finite arbitrary complex values, zero/nonunit DC, non-Hermitian zero row and zero side rows are valid. There is no normalization or realizability test. Its opaque nonblank source label supplies each returned row's source.

voxel_size_um is an exact built-in tuple/list of three nonboolean Python/NumPy real integer/floating scalars, individually converted to finite positive binary64. Converted values define the specimen geometry as exact represented rationals. Conversion underflow to zero rejects. Use source-free expected conversion TypeError/ValueError/OverflowError translation at this boundary; unrelated exceptions and MemoryError propagate.

candidate_carriers_yx is either a nonempty exact built-in tuple/list of rows, each an exact built-in tuple/list of length2 nonboolean Python/NumPy integer scalars, or a plain signed/unsigned integer ndarray of shape (C,2), C>=1, excluding bool and subclasses. Layout/endian/read-only alternatives are valid. Extract exact Python ints without floating conversion, numpy.intp limits, magnitude caps or principal-period reduction. Zero, negative, unsigned and arbitrarily huge list/tuple integers are valid. Snapshot caller order and duplicates. A scalar pair alone is not a candidate table. Other iterables, ragged rows and mixed floating/bool entries reject.

order is a nonboolean Python/NumPy integer equal to1 or2. calibration_carrier_bins and coordinate_offset_yx inherit the physical sampler's exact tuple/list integer-pair grammar, including huge integers. phase_reference_shift_rad inherits its real scalar conversion, finite huge/subnormal/signed-zero values and bounded-angle gauge semantics. No separate source keyword is added.

Snapshot all accepted images, phases, response arrays/metadata and scalar/container declarations before phase solving, transforms or interpolation. Validate all input fields even if every candidate has no overlap or lacks coverage. Preserve caller storage/layout/write flags, NumPy floating policy and warning filters on success and failure. Concurrent external mutation is outside the guarantee. Full snapshots, scratch allocations and ordinary MemoryError are allowed; no practical-size, memory or throughput promise is selected.

## Physical queries and full nonwrapping objective

Let spatial sizes be K=(Nz,Ny,Nx), M=Nz*Ny*Nx. On each axis, canonical centered integer bins are -floor(K/2),...,ceil(K/2)-1. Define the stored physical query coordinate independently for each bin:

```text
f_a(p) = RN64(p / (K[a] * d[a]))
```

The expression inside RN64 is exact rational arithmetic on the integer bin/size and converted binary64 spacing; RN64 is correctly rounded binary64, ties to even. Do not first round K*d, a reciprocal or a carrier increment, or construct f(j) by adding rounded f(p) and rounded shift. Every full specimen-axis coordinate vector must be finite, exactly zero at DC, nonzero elsewhere and strictly increasing for nonsingleton axes. Otherwise reject with unrepresentable_otf_frequencies. Avoid rejecting solely for an overflowing intermediate K*d when final coordinates are representable. Both odd/even specimen sizes are permitted.

For candidate k=(ky,kx), form exact integer j=(pz,py+m*ky,px+m*kx) and the full geometric set Q_k of p for which both p and j lie in the canonical specimen window. Multiplication/bounds use exact integers. Its count is

```text
J = Nz * max(Ny-abs(m*ky),0) * max(Nx-abs(m*kx),0).
```

For every p in Q_k query signed order0 at f(p) and positive order m at f(j), using the fixed calibration/gauge above. Each binary64 query means its exact represented value under the sampler. No endpoint snapping follows: even matching source/specimen grids can have a rounded endpoint just outside the exact closed source hull. Any uncovered query makes that candidate incomplete_coverage, with full J retained and no fit. Do not omit uncovered pairs, zero-fill, extrapolate, wrap, substitute an ideal-grid adapter or infer physical zero support. Empty Q gives no_overlap, never a sampling call with an empty point list.

Let dc,cm be the exact-real least-squares coordinates on the represented phase matrix and converted images. Define normalized negative-exponent discrete Fourier coefficients with spatial index-zero origin:

```text
D0(p) = sum_r dc(r)*exp(-2*pi*i*sum_a p[a]*r[a]/K[a]) / M
Dm(j) = sum_r cm(r)*exp(-2*pi*i*sum_a j[a]*r[a]/K[a]) / M
F0(p) = exact selected complex trilinear/gauge transfer at f(p)
Fm(j) = exact selected complex trilinear/gauge transfer at f(j)
x(p) = Fm(j)*D0(p)
y(p) = F0(p)*Dm(j)
beta = sum_Q conj(x)*y / sum_Q abs(x)**2.
```

The exact transfer target uses stored source components, exact represented query coordinates and the selected gauge, rather than returned sampler values as its own oracle. All geometric pairs participate, including DC and zero-transfer pairs. No support threshold, mask, transfer division, extra factor of two/site-count/voxel-volume, ridge or clipping applies. No per-candidate transfer recentering/rephasing applies.

For nonzero predictor/response norms, u=x/norm(x), v=y/norm(y), c=sum(conj(u)*v). Gain is beta=(norm(y)/norm(x))*c; coherence=abs(c) is amplitude correlation; relative_residual=norm(v-c*u), computed directly. Do not subtract nearly equal squared correlations to obtain the residual. Off-model observations receive this same unweighted full-pair complex least-squares projection. These fit diagnostics are not confidence probabilities, likelihoods, identifiability certificates or physical accuracy guarantees.

## Candidate information outcomes and global failures

Apply the following computed scaled-information outcomes in order. Rows with absent fits use None for all three gain/diagnostic fields; zero-valued fits are actual Python scalars.

| Condition | status; gain/residual/coherence |
|---|---|
| J=0 | no_overlap; None/None/None |
| J>0, any F0/Fm physical query uncovered | incomplete_coverage; None/None/None |
| Complete coverage, computed normalized predictor norm zero | zero_predictor; None/None/None |
| Nonzero predictor, computed normalized response norm zero | zero_response; 0j/0.0/0.0 |
| Nonzero norms, computed normalized correlation real/imag both zero | zero_correlation; 0j/1.0/0.0 |
| Otherwise | fitted; finite gain/residual/coherence |

Zero-response diagnostics are an explicit convention where response normalization has no mathematical value. A nonzero correlation with gain underflowed to zero retains fitted status. No hidden small-energy/correlation threshold applies. Exact-real zero classification at subnormal/cancellation boundaries is not promised. Every row retains full overlap_count J, selected order, exact carrier pair and source. Equivalent signed zero components are allowed.

Only geometric absence, missing calibration coverage and computed zero predictor are candidate-local unavailable outcomes. Invalid input, inherited phase failure, handled FFT failure, unrepresentable interpolation or nonfinite fitting/restoration is global: reject the whole call, never return partial rows. A malformed unused response row therefore still fails an all-no_overlap scan. Simultaneous-invalid precedence and global failure ordering across candidates are unspecified.

## Numerical policy

Use binary64/complex128 processing and the inherited SVD separator. Spatial transforms use public numpy.fft.fftn on unchanged three-dimensional bands, with normalization equivalent to division by M. Separate/batched transforms and equivalent axis permutations are allowed; private call counts/organization are unspecified. Scale each band's finite real/imaginary coordinates by its maximum absolute component before an unnormalized transform. Normalize before restoring, or retain the scale separately. A norm='forward' request alone does not protect an internal raw sum. Exact-zero bands may bypass transformation. Do not reject solely for an overflowing complex magnitude.

Use the selected physical sampler's safe component interpolation/gauge policy. Independently scale transfer/spectral operand vectors before forming bounded predictor/response products; retain positive scales as mantissa/exponent factors or equivalent. Use stable scaled norms, unit-vector correlation and direct residual. Restore gain real/imaginary components separately with the correlation component included, avoiding unnecessary raw squared norms, cross-products or overflowing ratios. Finite underflow is permitted; no uniform relative/subnormal-retention guarantee is selected. Computed nonfinite normalized fitting factor, restored gain component or diagnostic rejects with unrepresentable_volume_carrier_fit. No clipping, saturation, hidden energy threshold or fallback applies. Near Fmax, actual computed roundoff governs operational range classification outside the sufficient regime below.

During normalized FFT execution, FloatingPointError, OverflowError, arithmetic RuntimeWarning (even under caller ignore filters) or nonfinite transformed components yields volume_carrier_transform_failure. Unrelated FFT RuntimeError/TypeError/ValueError and MemoryError propagate unchanged. Inherited phase errors and sampler unrepresentable_empirical_interpolation propagate; only missing sampler coverage becomes a local row outcome. Handled conversion/range/underflow emits no arithmetic RuntimeWarning or FloatingPointError; unrelated warning categories/exceptions remain visible. Preserve caller floating and warning policy.

The following **explicit conservative project allowance** combines the stored-input mathematical stages; it is not a NumPy/LAPACK error theorem or physical accuracy claim. All observer calculations use exact/sufficient-precision arithmetic without overflowing/underflowing budgets. Let eps=2^-52, q0=2^-1074, B=max(abs(converted images)), J=full pair count. Assume represented phase-matrix cond2(H)<=10. Set

```text
alpha = 8192*N*eps*B + 8*q0
d = 2*alpha + 4096*M*eps*(10*B + 2*alpha) + 64*q0.
```

alpha is the inherited bound on each separated real coordinate. Two such bounds cover a complex side coordinate; the normalized finite transform does not amplify a uniform absolute error. The 10*B term bounds mean component-L1 separated amplitude in this conditioning regime; 4096*M*eps is this contract's conservative DFT allocation. This allocation is separate from approximation to a continuous scene.

For each selected transfer stencil, L=sum(weights*(abs(Re source)+abs(Im source))) before gauge rotation. Define e0_i=1024*eps*L0_i+64*q0 and em_i analogously from its actual interpolation stencil. The transfer absolute error budget uses L, **not abs(F)**; cancellation can make a small transfer poorly determined relative to its value. Let all D/F in the expressions below mean the exact stored-input targets above, and define over the complete candidate pair set

```text
Sx = max_i(abs(Fm_i)+em_i) * max_i(abs(D0_i)+d)
Sy = max_i(abs(F0_i)+e0_i) * max_i(abs(Dm_i)+d)
nu = 64*eps + 64*q0
eta_x_i = abs(Fm_i)*d + abs(D0_i)*em_i + d*em_i + nu*Sx
eta_y_i = abs(F0_i)*d + abs(Dm_i)*e0_i + d*e0_i + nu*Sy
Ex = norm(eta_x); Ey = norm(eta_y)
X = norm(x); Y = norm(y)
a = Ex/X; b = Ey/Y; h = a+b; R = Y/X
gamma = 4096*J*eps + 128*q0.
```

The normalized product allowances include operand rounding and finite underflow without requiring raw products to be representable. gamma allocates stable scaled norm/correlation/direct-residual/component-restoration arithmetic. For complete coverage, X,Y>0 and h+gamma<=1/64, require

```text
abs(coherence_returned-abs(c_exact)) <= 2*h+gamma
abs(relative_residual_returned-residual_exact) <= 4*h+gamma
Ebeta = R*(h*(2*(1+b)+abs(c_exact)) + (1+b)*gamma)/(1-a) + 8*q0
abs(gain_returned-beta_exact) <= Ebeta.
```

These follow conservative unit-vector and norm-ratio perturbation allocations; a<1 follows from the selected condition. No minimum correlation, nonzero fitted gain or arbitrary gain-magnitude range is required. A weak predictor/response, nearly cancelling correlation or transfer cancellation can remove a useful guarantee; this never becomes an input rejection cutoff.

Absent genuine allocation/dependency failure, otherwise-valid inputs in this informative regime must succeed when every exact separated real coordinate plus alpha is below Fmax in absolute value, every queried transfer's exact real/imaginary component plus its e0/em is below Fmax, and both exact final gain components plus Ebeta are below Fmax in absolute value. No raw x/y, norm, ratio or complex-magnitude representability is required. Informative calls return an actual fit, including computed zero_response/zero_correlation conventions only when consistent with the computed policy and these bounds. Outside the regime, the same estimator and computed outcomes remain binding, but no uniform digit guarantee or universal exact-finite success promise applies. Independent tight analytic checks must still distinguish sign, order, factor, bin and gauge mistakes.

This allowance compares arithmetic to the selected exact interpolant at rounded physical queries. Source measurement/calibration error, interpolation/model mismatch, hidden actual parameters, sampling aliasing and downstream reconstruction bias remain separately reported. A small arithmetic error does not imply accurate physical recovery.

## Result and stable errors

Each VolumeCarrierCandidate has exactly eight fields: gain (Python complex or None), relative_residual and coherence (Python floats or None), overlap_count (Python int), status (one table string), order (Python int), carrier_bins_yx (Python-int tuple), source (unchanged response source string). Field rebinding/deletion fails. Direct construction requires no validation/deep immutability. Repeated candidates produce distinct record instances with equivalent data; scalars/immutable tuples share no mutable caller state. No calibration copy, phase vector, inferred confidence, carrier ranking or automatic correction is returned. Keep raw/correction/calibration identities, spacing, phase schedules and supplied gauge externally.

Use SimreconError with stable code. Message prose and simultaneous-invalid precedence are unspecified.

| Rejected obligation | code |
|---|---|
| Images/steps/rank/solver/component range | Inherited volume-separation codes |
| Any source response public field | invalid_empirical_transfer_response |
| Specimen spacing grammar/conversion/finite positivity | invalid_volume_carrier_voxel_size |
| Specimen physical-axis final finite/nonzero/order representation | unrepresentable_otf_frequencies |
| Candidate table/row/scalar grammar or expected extraction failure | invalid_volume_carrier_candidates |
| Nonboolean integer order1 or2 | invalid_volume_carrier_order |
| Calibration carrier, offset or phase shift | Inherited physical-sampler scalar codes |
| Handled FFT failure/nonfinite normalized transform | volume_carrier_transform_failure |
| Final sampled interpolation nonfiniteness | unrepresentable_empirical_interpolation |
| Nonfinite fitting/restoration/final gain or diagnostic | unrepresentable_volume_carrier_fit |

Expected TypeError/ValueError/OverflowError translate only at their named conversion boundary; MemoryError and unrelated exceptions propagate. There is no artificial dependency-failure seam or source-free diagnostic exception wrapper in production.

## Identifiability and scope limits

A single excited predictor/response pair admits a perfect free-scalar fit. Sparse/periodic objects, different candidate overlap regions and aliases can produce equally good or misleading fits. Sampling aliases illumination k and k+t*K laterally; second-order-only information can additionally alias k and k+K/2 on even axes. Nonwrapping-window differences do not resolve physical aliases. A fixed calibration/phase-gauge mismatch may be absorbed in beta; independent phase-step errors generally cannot. Exactly five exposures fit any invertible five-column trial phase matrix voxelwise, so a separator residual cannot infer unknown steps. Continuous refinement needs a separate observation model. This operation supplies no automatic winner or universal physical identifiability claim.

## Ownership and delivery

The following are obligation groups, not scenario/example totals. A expands each distinct permitted/rejected decision, outcome, interpretation or guarantee into its explicit mapping; equivalent values are coverage examples. No scenario cap applies.

| ID | Observable obligation / credible wrong outcome |
|---|---|
| V01 | Public exports, all required bindings, tuple order/duplicates and exact eight frozen record fields/types |
| V02 | Inherited image and phase representations/finite snapshots; permitted signed/endian/strided/singleton alternatives |
| V03 | Represented five-column actual-phase model, order1/order2 selection, unequal/off-model/huge phases, rank/solver/range propagation |
| V04 | Specimen spacing grammar/converted units, exact rational physical bins and representable frequency boundary |
| V05 | Candidate-table containers/rows/scalars versus exact huge/unsigned/negative/zero integers and duplicate rows |
| V06 | Selected order grammar versus both positive orders; no doubled fundamental phases |
| V07 | Full response validation including unused rows/samples, direct/subclass records and unrelated getter exceptions |
| V08 | Independent anisotropic source/specimen geometries, complex trilinear stencils and fixed calibration/gauge across candidates |
| V09 | Separate correct rounding of f(p)/f(j), no rounded-increment addition, endpoint snapping or grid equality shortcut |
| V10 | Exact full nonwrapping pairs/count on odd/even/singleton axes, no integer overflow/principal-period reduction |
| V11 | Local no_overlap row and all-no-overlap scans while all global inputs are still validated |
| V12 | Local incomplete_coverage for any pair, including zero-valued/nominally matching endpoints; no pair dropping/zero fill |
| V13 | Cross-weighted full-pair complex least squares, spatial Fourier signs/normalization, no factor/ridge/transfer division |
| V14 | Computed zero_predictor versus zero_response versus zero_correlation versus fitted/underflowed-gain statuses |
| V15 | Direct residual/amplitude coherence, arbitrary/off-model projection and no hidden small-energy/correlation threshold |
| V16 | Combined informative allowance and sufficient success including stencil-cancellation envelope and safe component margins |
| V17 | Scaled transforms/products/norms/ratio/component restoration and permitted outside-regime extremes/underflow |
| V18 | Huge carrier/offset/phase gauge once, calibration source-sample origin, no specimen-candidate equality imposed |
| V19 | Snapshots/input preservation before numerical work; warning/floating policy and unrelated/allocation exceptions |
| V20 | Expected transform/interpolation/fitting global failures versus local unavailable rows; no partial result |
| V21 | Joint observation/phase permutation, voxel axes, fixed opaque source and no mutable result aliases |
| V22 | Identifiability/alias/single-excited-pair limits and duplicate diagnostic equality without selecting a winner |
| V23 | Public raw bead calibration to fixed signed response and corrected known-phase specimen scan with independent stored-input expectations |
| V24 | Existing interfaces/checks/dependencies preserved, executed usage and retained numerical/model error separation |

High-risk scientific/numerical/custom-oracle/interface route: fresh native Sol/high A, fresh blind B, restricted fresh C and fresh independent D. Numeric human execution/review/spending limits are not set. A owns only tests/test_volume_carrier_diagnostics.py and optional tests/volume_carrier_diagnostics_fixture.py plus ignored independent evidence. C owns only src/simrecon/_volume_carrier_diagnostics.py, additive exports in src/simrecon/__init__.py and docs/usage/volume-carrier-diagnostics.md plus ignored executed examples. Existing production helpers may be reused without editing their files/contracts. No reviewed tests/fixtures/snapshots, workflow/discovery/coverage settings, dependency/lock, skill/policy or unrelated runtime edits. Coordinator owns contract, task/PROJECT/roadmap pointers, packets/evidence and useful unique root lessons.

The task inherits owner-selected100% native Coverage.py executable statements/branch destinations for all instrumentable owned src/simrecon+scripts, never-imported files/relevant subprocesses, globally/per-package/per-file on local/Ubuntu24.04/macOS15 independently, no exclusions/platform union. Installed advisory thresholds alone do not enforce this selection. Exact clean canonical make verify/all13phases, rawCoverage/JSON/completeHTML, same-runM25, wheel/source/version and actual environment/executable/reader/lock/check/base/input proof precede fresh D and PR. Both configured CI platforms need independent original-artifact qualification before a successor. Coverage measures neither all conditions nor complete behavior. No reference C execution, merge/release, earlier-PR repair or unrelated external messaging.

Opened primary convention references: [NumPy DFT signs, bins and normalization](https://numpy.org/doc/stable/reference/routines.fft.html), [Gustafsson et al. 2008, five lateral orders and overlap fitting](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). They motivate the method; this task selects the exact public objective, representation, failure and accuracy rules.
