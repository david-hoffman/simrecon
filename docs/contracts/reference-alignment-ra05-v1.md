# RA05 — Calibrate and consume matched complex order transfers

Version 1.0, revision 1. Owner-authorized RA05 of the RA01–RA15 chain. Accepted prerequisite RA04: 08c344e2fff6bec1532e3fbcee112e7442e75082. High risk: scientific calibration, custom numerical oracles and physical-frequency interpretation. This is a known-phase, known-integer-calibration-carrier finite-model adapter. It does not infer unknown instrument settings.

## Public boundary

Export `AlignmentBeadCalibration`, `calibrate_alignment_bead` and `sample_alignment_order_transfer` from `simrecon`:

```python
calibration = calibrate_alignment_bead(
    pair, *, group, phases_rad, voxel_size_um, calibration_carrier_bins,
    bead_mode, bead_profile, min_profile_transfer, source,
)
sampled = sample_alignment_order_transfer(
    calibration, *, order, frequencies_zyx_per_um, coordinate_offset_yx,
    phase_reference_shift_rad, source,
)
```

Only the first argument is positional; every listed keyword is required. Ordinary argument-binding TypeError applies. `pair` is an `AlignmentCameraPair` returned by `correct_alignment_pair`. Require status `corrected` and both corrected members. A complete unavailable pair rejects with `alignment_bead_correction_unavailable`; it supplies no calibration or identity fallback. Wrong type rejects with `invalid_alignment_bead_calibration`. Existing record subclasses are accepted. Manual corruption of output-record invariants has no newly defined behavior; valid mutable array changes preserving those invariants remain supported.

Consume the corrected bead member's signed native float64 data directly. Apply no further offset, response, exposure, blank/flat or image-sum normalization. Do not synthesize a raw declaration and invoke a raw fitter, or use a second hidden correction through identity coefficients. Snapshot accepted declarations/metadata/data; select one named group; then separate known actual phases once. Pair metadata explicitly links specimen and bead to one caller-declared output unit/gauge, but authenticates neither instrument compatibility nor calibration IDs. Specimen and calibration grids/shapes may differ. No data-derived pairing or per-order normalization is selected.

Require an explicit z axis in the corrected bead. Present orientation/time/channel group axes follow exactly the plain built-in dict and plain nonboolean in-range built-in int rules of raw-point-bead calibration. A present singleton axis still requires index zero. No automatic first group or averaging. Wrong axes/group use `invalid_alignment_bead_axes` / `invalid_alignment_bead_group`. After selection the array is phase,z,y,x. Group validity and phase counts are determined by the bead, never by the specimen's different grid or group counts.

`phases_rad` and `voxel_size_um` inherit the complete known-phase volume-separation and empirical-response public grammar, converted-value problem, rank/numerical/frequency boundaries and errors. Actual supplied phases, not nominal commands, control separation. Supplied z/y/x spacing in micrometres (µm) is authoritative and retained alongside source metadata, even if source sampling differs or is unknown. Spacing and phase snapshots retain supplied/applied values under the raw-point-bead snapshot rules. `calibration_carrier_bins` inherits the exact built-in tuple/list pair of nonboolean Python/NumPy integer scalars, arbitrary magnitude, signed/unsigned, retained unreduced as Python ints. Use `invalid_empirical_transfer_carrier` for invalid declarations. This is the calibration carrier; specimen query coordinates do not infer it. `source` is a nonblank opaque string, retained unchanged; invalid labels use `invalid_otf_source`.

`bead_mode` is exactly `point` or `discrete_profile`. Point requires both `bead_profile` and `min_profile_transfer` to be None. Point compensation is identity and uses the existing empirical response from the separated arrays, including its observed positive peak and sole common exact dc mass normalization. Discrete profile requires the explicit profile/threshold and uses the complete finite-bead model and numerical rules below. Unknown mode or incompatible union arguments use `invalid_alignment_bead_calibration`. No continuous-sphere interpretation is selected: no owner mode supplies its geometry/sampling meaning here. Radial averaging and support cleanup are disabled in both selected modes. These operations are not inferred from sampled data.

## Mathematical interpretation and numerical stages

The selected synthetic finite periodic model uses z/y/x index grid N and per-grid-site emission weights, not a continuous density. There is no voxel-volume multiplier or extra pixel integration. h is a nonnegative unit-mass detection kernel with unique peak at zero; K_m=h*g_m, g0=1 and complex supplied physical-model profiles g1/g2 for independent generation. Unequal beam powers may produce genuinely complex axial profiles. The adapter does not receive h, g, bead brightness B or true anchor b. Those are evaluator/generator truth only.

For a discrete profile, supplied nonnegative finite plain float64-width weights have the selected bead volume shape. All layouts/endian/read-only and singleton/non-square grids, asymmetric/wrapped profiles and translated deltas are valid under the finite-bead contract. Normalize by exact mass W and form P=DFT(profile/W) with the contract's represented normalization and public transform allowance. The supplied profile anchor is at index zero; no profile-peak/centroid assumption applies. The specimen bead is B*p[j-b]. For known carrier kc=(0,ky,kx), exact ideal separated spectra have

```
C_m(k) = B*DFT(h*g_m)(k)
         * exp(-2*pi*i*(k-m*kc) dot b/N) * P(k-m*kc), m=0,1,2.
```

A calibration phase reference alpha_c adds exp(-i*m*alpha_c). Use the original exact converted observed dc mass S>0 once for every order: A_m=DFT(a_m)/S. Remove P(k-m*kc) on the native calibration grid before any interpolation or centering. The three divisors differ by signed order shifts; axial carrier is zero. Every native profile node must certify the finite-bead contract's exact `abs(P_computed)>=minimum+eta_node` rule, including nodes where the numerator is zero. Failure is `unstable_finite_bead_transfer`, never epsilon fill, masking, partial compensation or regularization. Inherit all profile/carrier/threshold grammar, exact mass/point identities, certificate equality and transform/range errors from finite-bead compensation.

Let Q_m=A_m/P(k-m*kc), v0=Re(IDFT(Q0)), and b_hat be v0's unique positive grid maximum. Locate after compensation. Raw dc may have a different or tied peak and must not be prematurely rejected. Return E_m=Q_m*exp(+2*pi*i*k dot b_hat/N) with the same origin for all orders. Inherit compensated peak failures, original S normalization, finite required intermediates, safe component arithmetic, allowances, sufficient-success regime and public-FFT failure translation from the finite-bead contract. Do not renormalize using the inverse array mass. For point mode inherit the empirical response accuracy/range rules and unique observed dc peak. Retain exact E0 DC=1, full signed complex side rows and relative amplitude/phase; no magnitude projection, conjugation of positive rows, side factor, replacement with a supplied PSF, pupil inference, deconvolution of a second pixel aperture or independent order normalization.

The returned response is dimensionless. Common normalization deliberately discards B/throughput from E, while original separated components and exact S remain available in output/provenance. A positive common input scale changes components and S together and leaves E invariant, apart from permitted arithmetic. Specimen corrected amplitudes remain in the common pair output unit. No absolute photon yield or physically verified response is inferred. Different grids require caller-declared physical pairing and sufficient measured frequency coverage.

## Output and provenance

`AlignmentBeadCalibration` is a frozen-binding record with exactly `components`, `response`, `provenance`. Components are original observed `VolumePhaseComponents` in pair.output_unit; response is `EmpiricalVolumeResponse`; provenance is an independent mutable plain dict. Existing embedded record fields/dtypes/shapes/frozen bindings remain. Arrays are independently owned mutable native C-contiguous arrays; they alias neither inputs, another output array, nor another call. Metadata is read-only by convention, not deeply immutable. Direct construction adds no validation.

Provenance has exactly these keys:

- `model`: `alignment_bead_calibration_v1`; `source`: supplied calibration label; `bead_mode`, `group`, `output_unit`, `gauge_source`: selected declarations.
- `calibration_carrier_bins`: unreduced Python-int pair.
- `correction`: independent dict with keys `mode`, `reference_sum_equalization`, `camera_estimate`, `bead`, `specimen`. Each member dict has exactly its RA04 frame fields except `data`: `axes`, `input_unit`, `output_unit`, `source_metadata`, `provenance`. Retain original correction/source/exposure/estimate/noise declarations, including opaque IDs, without corrected-pixel archives in metadata or reinterpretation as new-sample uncertainty.
- `phases_rad`, `voxel_size_um`: supplied/applied snapshot dicts exactly as raw-point-bead calibration.
- `dc_mass`: dict with exact Python-int `numerator`, positive Python-int `denominator` of reduced rational S, and `unit` equal to pair.output_unit. It describes an exact sum of converted dc samples, not an estimated precision or absolute physical brightness. An overflowing ordinary float sum is not itself rejection.
- `bead_profile`, `min_profile_transfer`, `profile_transfer`, `compensated_dc`: for point, all None; for discrete_profile, the existing finite-bead supplied/applied profile snapshot, converted threshold, computed fftshift profile transfer and real native localization diagnostic.
- `response_gauge`: `observed_dc_peak_with_supplied_phase_origin` for point, `compensated_dc_peak_with_supplied_phase_origin` for discrete_profile.

All mutable provenance is independent of caller data/containers and output arrays; phase/profile supplied/applied arrays are independent. No separate mass normalization or amplitude inference is encoded by those diagnostics.

## Consumption on declared specimen frequencies

`sample_alignment_order_transfer` requires an `AlignmentBeadCalibration` output and returns the existing `EmpiricalFrequencySamples` unchanged. Wrong record type uses `invalid_alignment_bead_calibration`. Direct corruption of wrapper provenance is outside this new boundary. Response validation, including valid mutable edits/invalid source fields, remains the full existing sampler contract. Pass the retained calibration carrier and the six explicit consumer declarations to `sample_empirical_volume_transfer` once. Its returned provenance retains the existing exact seven-key schema; keep the calibration object/source/pair provenance externally with sampled outputs.

Each query is an explicit z/y/x physical detector frequency in cycles/µm, with exact represented binary64 coordinate meaning. To consume an object frequency f in signed order m with specimen lateral carrier q_s, the caller supplies detector query f+m*q_s (zero axial carrier). The calibration carrier defines only the bead gauge. It need not have the same integer bins as specimen carrier on a different grid; physical compatibility is an explicit caller premise, not inferred from bins. `coordinate_offset_yx` is in calibration samples, not specimen samples. `phase_reference_shift_rad=alpha_s-alpha_c` in radians. All declarations, source labels, huge exact integers, bounded-angle phase/range rules, ownership, errors and arithmetic/interpolation budgets inherit the physical-frequency sampler contract.

With exact rho=kc_y*(b_hat_y+oy)/Ny+kc_x*(b_hat_x+ox)/Nx, positive signed orders remove exp(i*m*(2*pi*rho+delta)) once from the interpolated E_m. Order zero is unchanged; F_-m(f)=conj(F_m(-f)), reflecting all three physical axes. No second centering or frequency ramp occurs. Exact rational ideal source nodes k/(N*d), not rounded metadata, define the closed hull; singletons cover exactly zero. Any out-of-hull evaluated coordinate rejects the whole call with `incomplete_empirical_transfer_coverage`, including zero data. Even-grid negative endpoint has no stored positive duplicate; negative-order domain reflects the hull. No wrapping, tolerance snapping, clipping, extrapolation or zero fill. Existing modular integer-grid reconstruction semantics are unchanged; no new reconstruction estimator or automatic substitution is authorized.

## Caller preservation, failures and compatibility

Preserve buffers/layout/write flags, NumPy error modes and warning filters across success/rejection. Expected handled conversion/arithmetic failures emit no arithmetic RuntimeWarning/FloatingPointError; unrelated exceptions/warnings and actual MemoryError propagate. Do not add artificial dependency injection seams or practical-size/memory/throughput guarantees. Simultaneous invalid precedence and prose are unspecified. Existing raw calibration, empirical preparation, frequency sampler and reconstruction interfaces/contracts remain compatible. Refactoring may share the numerical separated-array finite-profile core; it must not broaden or weaken any existing public boundary.

## Scenarios, ownership and evidence

| ID | Distinct obligation / concrete failure risk |
|---|---|
| M01 | Public required bindings, exports, frozen three-field record and existing sampled record |
| M02 | Corrected pair required; unavailable pair has information failure; wrong record rejects |
| M03 | Direct corrected-array consumption with exactly zero additional camera/exposure/blank/flat operations |
| M04 | Explicit bead z/group selection and singleton/optional axis rules, differing specimen grid/group counts |
| M05 | Actual known phases versus nominal metadata; full represented/rank/numerical separator domain |
| M06 | Authoritative explicit anisotropic calibration spacing versus source metadata; native frequency/range rules |
| M07 | Point/discrete mode union; no inferred continuous sphere, support cleanup or radial averaging |
| M08 | Full profile grammar, exact mass normalization, asymmetric/wrapped/translated anchor and origin-point limit |
| M09 | Full-grid certificate, equality/weak/zero/uncertifiable transfer; zero numerator never bypasses failure |
| M10 | Correct distinct P(k-m*kc) divisors, order-two and zero axial shift |
| M11 | Compensated localization before centering, changed/tied raw peak accepted, compensated peak failures |
| M12 | Sole original exact positive S, shared center/common scale, exact dc identity and signed complex relative orders |
| M13 | Common amplitude scaling preserved in components/S and explicitly removed from dimensionless response |
| M14 | Bead movement versus storage roll/offset; phase-reference difference sign and order-two gauge |
| M15 | Known unequal-beam complex axial effective kernels independently predict separated/exposure data |
| M16 | Native profile compensation before interpolation, separate calibration/specimen grids and f+m*q_s queries |
| M17 | Physical negative-order reflection in all axes; even endpoint asymmetry, closed hull/singletons/no snapping |
| M18 | All wrapper/sampler declaration grammars and inherited errors with paired legitimate positive inputs |
| M19 | Safe arithmetic/transform/component range and operation-time exception behavior inherited from primitives |
| M20 | Complete original/applied correction/calibration/mass/gauge provenance, units and no aliasing |
| M21 | Caller state preservation and repeated-call independence across outcomes |
| M22 | Existing point/finite/adapter/sampler/reconstruction compatibility and public composition limits |
| M23 | Actual order-plane amplitude/phase figures and bead-correction/sampling provenance with measured bounds |

A expands inherited distinct boundaries in its mapping; no scenario cap or artificial product-red. Independently specify exposures via finite real-space effective kernels h*g_m, profiles and arbitrary off-center asymmetric beads, plus independent DFT/interpolation/gauge expectations. Do not use product outputs for numerical truth; use returned diagnostics only for explicitly conditional policy checks. Apply test-audit questions: observable obligation, credible wrong result, strongest existing public-boundary proof and distinct gap, no test-only seam. B independently recalculates and audits legitimate positives/omissions before freezing the checkpoint. Source-independent profiles/OTFs are A's ownership.

A owns only `tests/test_reference_alignment_ra05.py` and `tests/reference_alignment_ra05_fixture.py`. C owns `src/simrecon/_alignment_bead.py` and additive exports in `src/simrecon/__init__.py`; diagnosed changes may share core code in `_point_bead_calibration.py`, `_finite_bead_calibration.py`, `_empirical_response.py`, `_empirical_transfer.py`, `_empirical_frequency.py`, `_empirical_shared_nodes.py`, `_empirical_trilinear.py` only after coordinator scope record. No reviewed tests/fixtures/snapshots/checks/workflows/discovery/coverage/dependency/skills/policy edits by C. Coordinator owns this contract, usage/report/figures, task/PROJECT pointers, packets, accounting and useful unique root lesson. Fresh native A/B/C/D use Sol/high; fresh report-only Astra/ultra math advice replaces no role. Optional memory/delegation disabled. Actual served attribution/money unknown unless observed; human numeric limits not set and all ancestral charges persist by reference.

Inherit PROJECT approved behavior plus independent risk review; percentages advisory, no selected percentage threshold, complete native JSON/HTML global/per-package/per-owned-file reports with never-imported files/relevant subprocesses, no runtime exclusions, separately local/Ubuntu24.04/macOS15. Historical percentage paragraphs in prerequisite contracts do not override this owner-set policy. Exact-candidate full local `make verify` plus fresh D precede PR submission or push to open PR; both configured hosted proofs and preservation-aware completion cleanup precede RA06. Focused required checks: `uv run --locked pytest tests/test_volume_order_otf.py tests/test_raw_point_bead_calibration.py tests/test_finite_bead_compensation.py tests/test_empirical_transfer_adapter.py tests/test_empirical_frequency_sampling.py tests/test_reference_alignment_ra05.py`, then full gate. No CI-authoritative substitution.

Coordinator delivers actual complex order-plane/phase plots, amplitude/common-scale controls, pre/post centering/profile compensation and distinct-grid sampling with units/scales, independent comparison source, arrays/hashes and arithmetic/discretization/model limits. Retain original observations/settings/seeds; no regeneration to manufacture comparison. Existing supplied numeric C intermediates may be used only as narrowly identified data with hashes; none are a required invented input. Do not inspect/extract the source archive or build/run/import/link/copy legacy C. No Superpowers, merge/release or unrelated messages. One task per managed worktree. Completion cleanup inventories only this task's positively identified scratch/processes, preserves original evidence/link texts/referents/ancestors/environment/Python/cache pins at required paths, routes any actual data-loss operation through its own required roles, and records exact removed/preserved/blocked scope/counts/native allocated bytes/verification limits. Verified zero removal is permitted; no reusable destructive helper or predecessor cleanup is authorized.

## Current state

The sole current state is the ignored `artifacts/ra05/current-state.json`, with `evidence-accounting-detail.json` retaining all role/check/repair/failed-launch charges and ancestral pointers. Final candidate hashes/results live outside tracked bytes. Blind A/B receive only the named public packet, never state/accounting/history/coverage maps/old lessons.
