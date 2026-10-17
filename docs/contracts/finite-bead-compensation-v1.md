# Known-profile raw finite-bead calibration v1

**Version 1.0. October 16, 2026.** The owner's standing scientific-roadmap instruction authorizes this next dependency-ready contract above completed PR38. This selects finite-bead compensation in the existing discrete periodic development model. Actual instrument bead geometry, unknown phases/carriers/drift, continuous-optics accuracy and reference parity remain unresolved.

## Selected model and observable purpose

Use the [selected synthetic acquisition model](../models/synthetic-3d-acquisition-v1.md), replacing its point emitter by a declared finite nonnegative emission profile on the same periodic calibration grid. This is a model choice, never an instrument fact. A profile contains per-grid-site weights, not a density; no voxel-volume factor occurs. A continuous homogeneous sphere's Fourier amplitude is not silently substituted for this discrete profile.

For native shape N=(Nz,Ny,Nx), let p[j] be the supplied profile divided by its exact mass, with its declared anchor at index zero. It can be asymmetric, wrap across the periodic boundary or have no emission at its anchor. The profile need not have a unique maximum. A calibration specimen is s[j]=B*p[(j-b) mod N], B>0. The detection kernel h retains the selected model's nonnegative unit mass and sole largest sample at zero. Neither h, B nor anchor location b is an operation input.

The lateral fundamental is the supplied exact integer pair kc=(ky,kx), with q=(ky/(Ny*dy),kx/(Nx*dx)) cycles/µm. It is known calibration metadata for this slice. It is not inferred from phase commands, an estimator score or hidden specimen truth. The axial carrier is zero. Let P[k]=DFT(p)[k] using the negative-exponential forward discrete Fourier transform (DFT). With K_m=h*g_m and H_m=DFT(K_m), known separation phases in the aligned calibration phase reference give

```text
C_m[k] = B*H_m[k]*exp(-2*pi*i*(k-m*kc)·b/N)*P[k-m*kc]
S = exact sum of the converted observed a0 samples, S>0
A_m[k] = C_m[k]/S
Q_m[k] = A_m[k]/P[k-m*kc], m=0,1,2
v0[n] = Re(inverse_DFT(Q_0))[n]
ideal model: S=B and v0[n]=h[n-b]
b_star = unique positive grid maximum of the computed v0
E_comp_m[k] = Q_m[k]*exp(2*pi*i*k·b_star/N), m=0,1,2.
```

All index arithmetic is modular on the native grid; kc has zero axial component. A common separation phase-origin offset alpha_c multiplies order m by exp(-i*m*alpha_c), retained in the returned gauge. Removing P before locating the origin recovers the profile anchor from v0's observed peak in this model. Locating the blurred dc peak first and dividing only an already centered response can leave an unknown spatial phase ramp. No true-center input or fitted center correction is selected here.

Return the existing EmpiricalVolumeResponse representation by centering all three compensated spectra at the one deconvolved observed peak. Use the original exact converted observed dc mass S once. Do not recompute a new mass from an inverse-transformed array or call empirical preparation on deconvolved arrays. The resulting response has the same bead/phase gauge as the existing point-bead result and can use the existing empirical transfer consumers. Its mathematical signed negative orders follow modular reflection and conjugation, including even Nyquist indices. This is the discrete periodic model; physical positive and negative endpoints in the separate point sampler still have their existing meaning.

Profile knowledge, fixed shift-invariant h, correct phases and the chosen carrier are prerequisites to that interpretation. On arbitrary valid stored data the operation is the contracted deconvolution/localization estimator, not a certificate that these assumptions hold. A finite profile with missing spectral information cannot determine h; reject rather than fill, clip or regularize it.

## Public boundary and inherited acquisition stages

```python
from simrecon import FiniteBeadCalibration, calibrate_raw_finite_bead

calibration = calibrate_raw_finite_bead(
    acquisition,
    group=group,
    offset=offset,
    response=response,
    output_unit=output_unit,
    phases_rad=actual_phases,
    voxel_size_um=(dz, dy, dx),
    bead_profile=profile,
    calibration_carrier_bins=(ky, kx),
    min_profile_transfer=minimum,
)
```

Only acquisition is positional; all keywords are required. Ordinary Python argument-binding TypeError applies. The acquisition, single-group declaration, complete-array camera correction, actual phase separation and supplied spacing have exactly the supported meaning of the [raw point-bead composition](raw-point-bead-calibration-v1.md), except that finite compensation is added before empirical response formation. Reuse those stages once each. This new operation does not call the point-bead operation and then divide its already centered response.

In particular: require RawAcquisition, acquisition_kind='sim_beads', explicit orientation/phase/z/y/x and optional named channel/time. A present singleton group axis still requires its explicit selector. Group is a plain dict with exactly present time/channel/orientation names and plain nonboolean int indices in range. Corrupted direct record invariants remain outside the newly defined domain. All scalar/full-map corrections use the complete canonical acquisition shape. Nonselected invalid correction samples/maps/range still reject. Correct then select then separate with the supplied actual phases, not nominal commands. The [linear correction](linear-response-correction-v1.md), [volume separator](volume-phase-separation-v1.md) and [empirical response](empirical-volume-response-v1.md) keep their represented numerical domains, binding, units, errors and caller preservation. Supplied spacing remains authoritative and its original declaration remains in provenance.

After separation, compute the original exact positive dc mass, normalized spectra, profile division and compensated-origin localization in that order. Real projection is used only for the inverse zero-order localization observable; it does not project any returned spectral row. Negative localization samples remain valid. Only the compensated dc supplies the peak decision; an original raw/separated dc tie or no positive maximum is not itself a rejection if the original exact mass is positive and compensated localization succeeds. Never run the old peak locator before compensation. The observed mass S, not the mass of the computed localization array, supplies the single common normalization. No source-background inference, support cleanup, radial averaging, interpolation, learned profile or carrier/phase estimator is added.

## Profile, carrier and threshold representation

bead_profile is a plain NumPy ndarray of float64 width (8 bytes), either endian, shape (Nz,Ny,Nx), exactly matching the selected volume. Read-only, strided/reversed, Fortran, nonsquare and singleton storage are valid. Reject nonarrays, ndarray subclasses/masked arrays, other dtype widths/kinds, wrong rank/shape/empty axes, nonfinite values, negative samples and nonpositive exact mass. Signed zeros are valid. No positivity at index zero, symmetry, diameter, isolation or connected-support restriction is imposed. The exact real mass of the represented weights may exceed Fmax or be as small as the least positive subnormal. Scaling all weights changes no exact normalized profile; finite representation/rounding can change a supplied discrete profile.

calibration_carrier_bins is an exact built-in tuple/list pair of nonboolean Python/NumPy integer scalars. Convert exactly to Python ints. Signed, unsigned, zero, repeated periods and arbitrarily large integers are valid; reduce modulo dimensions only for discrete profile indexing. Do not coerce floats or enforce an intp/principal-window limit. Retain the unreduced declaration in provenance. Physical carrier/gauge declarations passed later to an existing consumer remain the caller's responsibility.

min_profile_transfer is a nonboolean Python/NumPy integer/floating scalar, source finite and individually converted to finite binary64 with 0<minimum<=1. Reject bool, complex, strings, arrays (including 0D), other numeric classes, conversion failures and positive source values converting to zero. It is an explicit dimensionless conditioning policy, with no default, hidden epsilon or noise interpretation.

Snapshot accepted input arrays/declarations before numerical processing. Preserve caller buffers, layout/write flags, NumPy floating modes and unrelated warning categories on success/rejection. Concurrent external mutation is outside the promise. Allocation MemoryError and unrelated exceptions propagate unchanged.

## Numerical procedure, diagnostics and range

Let M=Nz*Ny*Nx, eps=2^-52, q0=2^-1074 and Fmax be the largest finite binary64 value. All mathematical sums, allowances and comparisons below use exact represented source values and observers that avoid overflow/underflow. The constants are project acceptance choices for numerical review, not universal backend theorems or physical accuracy.

Compute the exact profile mass W, then r[j]=RN64(profile[j]/W), with correctly rounded binary64 division. Form the profile transform with public numpy.fft.fftn, default/backward forward normalization, on the real normalized profile over all three spatial axes. Separate equivalent spatial-axis permutations are allowed; private call counts/layout are unspecified. Restore full fftshift order in the retained diagnostic. Its mathematical target is P=DFT(profile/W), not the transform of a rounded ordinary mass normalization. At each node require absolute error <=eta=128*M*eps+4*M*q0. Set normalized DC exactly to 1+0i, with eta_DC=0. An origin-point profile (its only positive entry at index zero) has exact P=1 everywhere; return exact all-ones profile transfer with eta=0 everywhere. Other profiles use eta at every non-DC node, including translated point profiles. Do not manufacture exact identities at other nodes.

The returned profile-transfer diagnostic is independently owned native complex128 C-contiguous in full fftshift z/y/x order. Define mu=abs(P_computed) in exact real arithmetic on its represented real/imaginary components. Certify a node only when mu>=minimum+eta_node. The sum and magnitude comparison are exact; a rounded hypot result or overflowing/underflowing square must not change the decision. Equality is accepted. All native nodes must certify, including those used by a zero component. The shifted factors are permutations of this complete set, so this decision is carrier-independent. Failure is unstable_finite_bead_transfer. This outcome includes true weakness and an uncertifiable margin near the minimum; it is not exact detection of a mathematical spectral zero. No mask, partial compensation, epsilon division, regularized inverse, zero fill or fallback applies.

For each observed order a_m, set G_m to the maximum absolute real/imaginary component (1 for an all-zero order). Transform RN64(a_m/G_m) with public numpy.fft.fftn on the unchanged uncentered volume and all spatial axes, default/backward forward normalization, and restore G_m/S componentwise using exact/scaled ratios. No raw sum, complex magnitude or standalone G_m/S ratio must be representable. The normalized spectrum targets A_m=DFT(a_m)/S. Require its absolute sample error <=dA_m=512*M*eps*Lambda_m+16*M*q0, where Lambda_m=sum_j(abs(Re a_m[j])+abs(Im a_m[j]))/S. Zero-order DC is the exact identity 1+0i and is assigned before restoration/range checks after validating the entire scaled transform. Zero side orders may bypass their transforms and return exact zero, but never bypass profile validation/certification. No origin shift occurs yet.

Divide each normalized spectrum by the computed profile factor at k-m*kc, with exact modular integer shifts. Q is a required finite complex128 intermediate. Do not form a denominator square or reciprocal that unnecessarily overflows/underflows. To locate the origin, transform Q0 with public numpy.fft.ifftn, default/backward inverse normalization, scaling by its maximum absolute component beforehand and restoring only the real localization array afterwards. Validate every component of the scaled inverse transform for transform failure. Only the restored real localization array v0 is a required finite result; an unused unscaled imaginary array is not required. Apply the existing unique-positive-grid-maximum rule to computed v0, with exact converted positive ties, no tolerance/confidence cutoff. Retain v0 as a diagnostic. Its exact target is real for the real observations/profile. No positivity clipping occurs.

Finally multiply every Q row by the same exact-origin phase exp(2*pi*i*sum_a k_a*b_star_a/N_a). Use bounded-angle evaluation of the exact rational cycles and safe component rotation. Equivalently implemented integer recentering is permitted if it preserves the same spectrum and budgets; do not transform an inverse side volume merely to introduce another normalization. Assign returned zero-order DC exactly 1+0i; all-zero side rows return exact zero. Retain full complex E0/side values, relative gains, side DC and common scale. No per-order norm, extra factor of two, magnitude, conjugation of positive orders, Hermitian projection or second origin/phase correction applies.

For every successfully returned nonidentity sample define ideal P at its shifted node, exact A as above, and F=A/P times the centering phase at the **computed** b_star. Let mu be that node's computed profile magnitude and eta_node its allowance. Define

```text
dQ = dA_m/mu + abs(A)*eta_node/(minimum*mu)
     + 128*eps*(abs(A)+dA_m)/mu + 16*q0
Delta = dQ + 128*eps*(abs(A/P)+dQ) + 16*q0.
```

Require abs(E_returned-F)<=Delta. The retained compensated-dc diagnostic targets Re(IDFT(A0/P)); its uniform absolute error allowance is mean_k(dQ0[k])+512*M*eps*mean_k(abs(Re Q_computed0[k])+abs(Im Q_computed0[k]))+16*M*q0. The unreturned Q in this last allowance is the actual required intermediate. These formulas propagate numerator/profile/division/rotation/inverse arithmetic separately. A stable exact compensated peak margin greater than twice the spatial allowance establishes unchanged origin. Otherwise the computed peak decision remains binding without a physical-center certificate. Separation/raw-observation error must be propagated separately from these stored-input budgets, using the existing separator bounds and original-mass perturbation formula. Do not derive expected scientific truth from returned diagnostic fields; conditional policy checks on those observations prove only that policy.

An origin-point profile must reduce to the existing point-bead mathematical response, common normalization and observed-peak rule within the existing empirical-response allowance. The new provenance still identifies the explicitly declared profile mode. Calling existing public point preparation for this identity branch is allowed after the new operation's declarations validate; the general finite-profile route must not introduce its raw-peak guard. A translated delta is a nonidentity legitimate profile whose frequency phase is removed.

Required finite stages are the scaled forward/inverse transform results, normalized A, compensated Q, real localization array v0 and final centered response components. Each real/imaginary component is assessed separately; an overflowing complex magnitude alone is not failure. A conservative sufficient range regime is R=max_m(Lambda_m/minimum), D=max_m(dA_m/minimum), and 64*(R+D)<Fmax. Apart from actual allocation/dependency failure, calls in this regime must reach the stated profile/peak decisions and return when those decisions accept; the inequality is not an input rejection cutoff. Outside it attempt the computation and report actual required-stage or final component nonfiniteness as unrepresentable_finite_bead_response. No universal guarantee follows merely from a finite final exact value when a required intermediate is unrepresentable. Exact W/S overflow or underflow alone never rejects; normalized ratios must remain safe. Boundary classification outside the sufficient regime can depend on roundoff.

During public FFT execution, FloatingPointError, OverflowError, arithmetic RuntimeWarning (including under caller ignore filters), or nonfinite scaled transform components gives finite_bead_transform_failure. MemoryError and unrelated FFT RuntimeError/TypeError/ValueError propagate unchanged. Required-stage/final nonfiniteness after finite scaled transforms gives unrepresentable_finite_bead_response. Handled numeric conversion/range/underflow emits no arithmetic RuntimeWarning/FloatingPointError and preserves caller modes/filters. Suppress no unrelated warning category. No artificial test-only dependency seam, streaming, allocation-size, throughput or memory promise is introduced.

## Result and provenance

Return frozen-binding FiniteBeadCalibration with exactly three fields: components (the original observed VolumePhaseComponents), response (the compensated/recentered EmpiricalVolumeResponse), provenance (plain mutable independently owned dict, read-only by convention). Embedded records keep their existing exact fields, native owned mutable arrays and frozen bindings. No arrays alias caller storage, another output array or another call. Direct construction adds no validation or deep immutability. All output arrays are native C-contiguous. The response's frequency vectors use exactly the existing empirical native frequency convention, accuracy/range and converted supplied spacing; origin_zyx is b_star.

Provenance has exactly the existing point-composition keys model, group, source_metadata, linear_response, phases_rad, voxel_size_um, bead_compensation and response_gauge, plus bead_profile, calibration_carrier_bins, min_profile_transfer, profile_transfer and compensated_dc:

- model='discrete_finite_bead_v1'; bead_compensation='native_periodic_profile_division_v1'; response_gauge='compensated_dc_peak_with_supplied_phase_origin'.
- group/source_metadata/linear_response/phases_rad/voxel_size_um have exactly the point-composition supplied/applied snapshot schemas. Every inherited R1 public field except pixels remains in source_metadata, including different/unknown source sampling and nominal commands. Never label a supplied phase/carrier/profile as estimated.
- bead_profile is exactly a dict with source='supplied_relative_site_weights', supplied=independent C-contiguous plain ndarray retaining dtype/endian/shape/value bits, applied=independent native float64 C-contiguous RN64(profile/W) array, normalization='exact_converted_sum'. Supplied/applied arrays do not alias; no padding-byte promise applies.
- calibration_carrier_bins is the original unreduced Python-int pair. min_profile_transfer is the converted Python float.
- profile_transfer is the independently owned computed complex128 native diagnostic defined above, in full fftshift order. Its certificate allowance is the contract's exact eta/identity rule, not an estimated noise floor.
- compensated_dc is the independently owned real float64 v0 diagnostic in native spatial indexing. response.origin_zyx is its unique positive peak, with no inferred physical-isolation claim.

Provenance arrays alias neither caller arrays, embedded output arrays, each other nor another call. Other metadata aliasing among internal snapshot fields has the existing point-composition limits. No runtime file hashing/archive, I/O, instrument authentication or private-data upload occurs.

Use SimreconError stable codes; prose and simultaneous-invalid precedence unspecified. New raw-boundary codes are invalid_finite_bead_acquisition, invalid_finite_bead_kind, invalid_finite_bead_axes and invalid_finite_bead_group, for the corresponding point-composition rejection rules. Invalid profile uses invalid_finite_bead_profile; carrier grammar uses existing invalid_empirical_transfer_carrier; threshold grammar/conversion/domain uses invalid_finite_bead_transfer_threshold; failed all-node certificate uses unstable_finite_bead_transfer. Nonpositive original exact observed dc mass uses nonpositive_empirical_response_mass. Compensated no-positive/tie uses no_positive_bead_peak/ambiguous_bead_peak. Transform and required-stage range codes are defined above. Inherited correction/separation/spacing/frequency errors propagate without being recast. Ordinary binding TypeError, MemoryError and unrelated exceptions retain normal behavior.

## Scenarios, ownership and completion

| ID | Distinct approved outcome / credible wrong result |
|---|---|
| F01 | Public exports, all required bindings, exact three-field frozen result and existing embedded records |
| F02 | Valid raw SIM-bead kind and explicit z; nonrecord/kind/axes rejection with singleton alternatives |
| F03 | Exact named single-group dict/key/index decisions, source-layout independence and present singleton axes |
| F04 | Complete canonical-array camera correction before selection, all scalar/map combinations and nonselected failures |
| F05 | Supplied actual unequal/overdetermined/repeated identifiable phases versus nominal commands; inherited rank/domain failures |
| F06 | Supplied spacing authoritative, complete grammar/native grid/frequency range and extreme/singleton alternatives |
| F07 | Plain float64-width profile shape/endian/layout/finite/nonnegative/positive-exact-mass domain |
| F08 | Profile anchor at zero, asymmetric/wrapped/translated emission; no profile-peak/centroid/symmetry restriction |
| F09 | Exact profile normalization, scale invariance within represented inputs, overflowing/subnormal mass and point identity |
| F10 | Exact signed/unsigned/huge carrier pair and unreduced provenance; modular shift only in profile indexing |
| F11 | Explicit scalar minimum (0,1], conversion/source finiteness and rejected underflow-to-zero |
| F12 | Full complex profile DFT target, exact DC/origin-point identities and per-node eta |
| F13 | All-node conservative certificate, exact squared-magnitude boundary including equality; weak/zero/uncertifiable outcomes |
| F14 | Zero numerator/side row does not bypass profile gate; carrier-independent full-grid decision |
| F15 | Three distinct divisors P(k-m*kc), minus sign, order-two shift and no axial carrier shift |
| F16 | Original exact observed dc mass S once; nonpositive mass rejected without preliminary raw peak requirement |
| F17 | Safely scaled uncentered normalized FFTs, finite signed cancellation and component-safe normalization/division |
| F18 | Compensated real inverse observable and unique positive grid peak; changed/tied raw peak allowed |
| F19 | Compensated no-positive/exact positive ties; numerical boundary/peak-margin limits explicit |
| F20 | Same observation-derived recentering phase for all orders; full E0/relative gains/zero-side/DC preservation |
| F21 | No second normalization from inverse-array mass; original mass/throughput meaning retained |
| F22 | Bead movement, profile translation, storage-roll/coordinate-offset control and phase-reference sign |
| F23 | Native modular negative orders/even Nyquist and separate physical reflected-hull consumer domains |
| F24 | Stored-input response/profile/localization accuracy and conditional sufficient range success |
| F25 | Computed required-stage/final range failure versus finite extreme components/mass/complex magnitudes |
| F26 | Public FFT handled arithmetic failures versus unrelated/allocation propagation, no private injection seam |
| F27 | Caller floating/warning policy preservation, unrelated warnings visible and whole-call rejection |
| F28 | Complete exact provenance schema, original/applied declarations, independent native arrays and repeated-call ownership |
| F29 | Existing point API unchanged; origin-point limit and new model provenance honest |
| F30 | Public raw finite-bead calibration through existing adapter/reconstruction with independent signed estimator evidence |
| F31 | Compensate native nodes before interpolation; existing interpolation/physical-coverage semantics preserved |
| F32 | Executed documented usage, retained actual generation/input/array proof and explicit finite-model/known-parameter limits |

A expands inherited rejection/interpretation/guarantee decisions in its mapping; this compact table is no scenario cap. Apply test-audit authoring questions to each proof: approved observable obligation, credible wrong outcome, distinct gap in stronger owner-boundary proof and no test-only production seam. A independently derives finite real-space raw exposures, exact/sufficient-precision profile/phase/DFT/division/centering expectations, arithmetic budgets and legitimate-positive controls. B independently recalculates and audits omissions/oracles before the frozen checkpoint. Absent new API is setup evidence, never product-red; initially passing prerequisites remain valid. Blind A/B read only named public contracts/interfaces, permitted harnesses and exact A tests/fixtures, with source-free diagnostics before probes. No implementation/history/conversations/state/coverage maps/LESSONS entries; only LESSONS format guide is permitted.

C executes a closed cohort with two coherent public examples: (1) independent asymmetric finite-profile raw exposures whose blurred dc peak differs from the compensated anchor, plus point/translated profile and weak-transfer controls, including anisotropic odd/even geometry and differing nominal/actual phases; (2) raw finite-bead calibration -> existing empirical adapter -> known-parameter specimen reconstruction, with independently generated direct real-space illumination/convolution and an independent finite estimator comparison. Include common phase-origin and physical bead-movement/storage-roll controls, relative signed orders, all-node certificate outcome, complete declared camera/group/phase/spacing/profile/carrier provenance and separate arithmetic/localization/reconstruction-bias limits. True anchor/h/B/specimen remain generator/evaluator-only. Profile and known calibration carrier are legitimate declared inputs for this slice, not a truth-hidden full-workflow claim. Do not require a figure when measured signed tables/equations explain the result.

Retain actual raw/expected/returned arrays and complete closed source/input/dependency/executable census before and after actual generation. Successful argv must name the actual listed generator; start/end observations must bracket generation itself. Envelopes remain separate from closed members. Final clean coordinator admission comes after actual candidate commit, without replacing original generation observations. Complete exact-AST structural grammar preflight precedes the expensive gate and is not qualification.

High-risk scientific/custom-oracle/interface route: fresh native blind A, fresh blind B, restricted C and fresh D. Requested model/effort gpt-6.1-sol/high per project conservative calibration; actual serving unknown unless observed. Optional memory/delegation disabled where supported. A owns tests/test_finite_bead_compensation.py and tests/finite_bead_compensation_fixture.py only. C owns src/simrecon/_finite_bead_calibration.py, additive src/simrecon/__init__.py exports and docs/usage/finite-bead-compensation.md only, plus ignored actual example evidence. No reviewed test/fixture edits by C; no workflow/discovery/coverage/dependency/skill/policy changes. Coordinator owns this contract, task/PROJECT/roadmap pointers, packets/accounting, PR presentation and useful unique timestamped root lessons. Existing helpers may be reused without modifying their contracts/files.

The standing owner requirement binds 100% Coverage.py native executable statements and branch destinations globally/per owned package/per file across all src/simrecon and scripts, never-imported files/relevant subprocesses, independently local/Ubuntu24.04/macOS15, zero exclusions and no platform union. Advisory percentages in older contracts are no waiver. Exact clean canonical make verify/all13 phases, raw SQLite/JSON/complete HTML, same-run M25, wheel/source/version/environment/input/base evidence, fresh D, owned stacked PR and separate qualification of both original native CI archives are required. No CI-authoritative fallback, reporting-only science/gate/example/M25 reruns, reference C execution, merge/release or unrelated external messages. All predecessor failed attempts/charges remain retained by reference; human numeric limits are not set and absent measurements are unknown.

Public convention reference opened during intake: [NumPy DFT sign, normalization and periodic frequency ordering](https://numpy.org/doc/stable/reference/routines.fft.html). The discrete profile and conditioning/gauge policies are explicit project choices. The [uniform-sphere amplitude formula](https://www.sasview.org/docs/user/models/sphere.html) was inspected only to distinguish a continuous model that this contract does not select.
