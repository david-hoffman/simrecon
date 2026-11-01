# RA12 — model-conditioned predictive calibration handoff

**Version 1.1.** Owner-authorized operational contract. After receiving Astra's
recommendation, the owner instructed **“Do it”**: implement the scoped predictive
estimate, declared finite ambiguity audit and independent predictive validation.
Global operator identification remains **unestablished**. This is not a new
instrument premise, statistical confidence guarantee or universal recovery claim.
The standing RA07–RA15 authorization and all delivery gates remain unchanged.

## Public operations and selected model

The new development module `scripts.image_only_calibration_handoff` exposes:

```python
infer_calibration_handoff(
    central_counts, *, structured_counts, heldout_counts,
    camera_estimate, calibration_origin_um_zyx,
    specimen_detector_shape_zyx, specimen_detector_spacing_um_zyx,
    specimen_origin_um_zyx, sweep_scales, max_refinement_evaluations,
    training_rms_limit, calibration_atol, operator_atol, source,
) -> CalibrationHandoff

audit_calibration_candidate(
    candidate, *, calibration_shape_zyx, calibration_origin_um_zyx,
    specimen_detector_shape_zyx, specimen_detector_spacing_um_zyx,
    specimen_origin_um_zyx, camera_estimate,
    calibration_atol, operator_atol, source,
) -> CalibrationHandoff
```

Only the first argument of each operation is positional. All shown keywords are
required. The second operation is a **supplied-candidate diagnostic**, not
observation-only inference. Its output must remain labeled separately. It also
provides the real candidate-audit boundary used by inference; no test-only seam,
package export, CLI, persistence, generator/evaluator import or raw workflow is
added. Neither operation accepts specimen truth or true calibration parameters.

Use the existing finite physical bead model: three contained nonoverlapping
radius-0.050 µm spheres, calibration spacing `(0.125,0.080,0.080)` µm, source
refinement `(8,8,8)`, excitation/emission `0.488/0.525` µm, refractive index
`1.515`, detection numerical aperture `1.4`, clear matched-index scalar pupil and
pixel midpoint samples `(2,2)`. The new comparison/refinement target is **Q128**.
These are synthetic assumptions, not measured empirical optics.

The selected specimen consumer is the existing physical `fit_specimen` mode:
source shape `(Z,2Y,2X)`, source spacing `(Dz,Dy/2,Dx/2)` and half-cell locations
relative to its known box corner. It accepts raw counts and the same estimated
camera gauge. No periodic RA05 transfer, RA09 overlap objective or unlike-grid
RA10 kernel is silently substituted. Accepted physical harmonic responses and
the existing specimen source refinement supply this direct composition.

## Inputs and validation

The inference operation inherits all original raw-array, camera, origin and
`sweep_scales` grammar from `image-only-bead-calibration-v1.md`, replacing its
origin keyword with `calibration_origin_um_zyx`. Preserve signed observations,
endian/layout/read-only variants and finite conversion rounding. No true bead
positions, phases, carrier, beam powers, camera coefficients, transfer arrays,
noiseless means, seeds, support masks or evaluator choices are inference inputs.

For both operations, consume only camera `means_counts`, `contrast_counts` and
`source`, with the existing bead/specimen consumed-field grammar. Physical gain
availability and unconsumed variance/repeatability fields impose no extra gate.
The common correction is `(C-means_counts[1])/contrast_counts` once. No extra
blank subtraction, exposure equalization, gain conversion or fitted intensity
alignment is allowed.

New metadata grammar:

- Detector shape is a built-in three-tuple of positive built-in nonboolean ints.
  Calibration shape in the diagnostic also obeys the inherited minimum physical
  side length of 0.100 µm on every axis.
- Specimen spacing is a built-in three-tuple of built-in int/float values,
  excluding bool/numeric subclasses, normalizing to finite positive float64.
- Origins are three-tuples under the inherited origin grammar; values are finite
  and may be signed or zero. They are box-corner labels, not inferred registration.
- `max_refinement_evaluations` is a positive built-in nonboolean int. It bounds
  the nonlinear optimizer's declared function-evaluation setting; separately
  count every actual model-objective entry, including finite differences.
- `training_rms_limit` normalizes to finite nonnegative float64.
  `calibration_atol` and `operator_atol` normalize to finite strictly positive
  float64. Use the same plain built-in scalar grammar. These are explicit
  finite-procedure comparison settings, not statistical confidence or owner
  time/cost limits. No hidden denominator floor or percentage threshold is added.
- `source` is a nonblank string, preserved unchanged as an opaque provenance label.

The diagnostic accepts `PilotCandidate` under its public field meanings. Consume
and independently snapshot centers `(3,3)`, relative brightnesses `(3,)`, carriers
`(3,2)`, phases `(3,9)` and amplitudes `(3,)` as plain finite real numeric ndarrays
normalized to float64. Brightnesses are nonnegative; beams are nonnegative and
not all zero; carriers obey the exact physical disk. Rebuild occupied profiles
from centers, requiring containment and nonoverlap. Supplied occupied-count or
stored-mass metadata authenticates nothing and does not replace that calculation.

All input domains are validated before an informational unavailable result.
Simultaneously invalid precedence is unspecified. Ordinary missing/unknown
argument binding raises `TypeError`. Inherited raw/camera validation may preserve
the existing public bead error; new metadata/candidate violations use
`invalid_calibration_handoff`. Huge valid dimensions are not malformed solely
because execution/indexing is impossible; concrete representation obstructions
are operation-time range failures. Actual `MemoryError` propagates.

## Observation-only finite refinement

1. Call the existing `fit_bead_calibration` with raw calibration arrays and the
   estimated camera record. Preserve its result and meaning. Nonpositive contrast
   and failed initialization yield unavailable. A seed numerical failure before
   its frozen candidate and all three training rescores exist remains numerical
   incomplete. A seed-heldout-only range failure may retain that complete frozen
   training state for the new Q128 procedure; its original diagnostic failure
   remains visible. Never fabricate a seed or use nominal truth.
2. Snapshot the seed's frozen candidate and score it afresh at Q128. Its Q256/Q512
   rescores and Q512 held-out results remain **seed diagnostics**, not scores in
   this refinement or certified quadrature errors.
3. Freeze that candidate's occupied profiles/centers during one deterministic
   bound-constrained continuous least-squares refinement of the other 38
   coordinates. Use the inherited decoder: three brightness coordinates relative
   to the seed's original positive brightness scales; two beam angles; three
   physical carrier radius/angle pairs; and 27 phase coordinates. Bounds are the
   inherited `[0,100]`, `[0,1]`, radius `[0,1]`, angle `[-1,1]` and phase `[-1,1]`
   intervals. Do not force the first phase to zero or infer commands are actual.
4. The full objective is

   `F = (sum central residual² + sum all 27 structured residual²)/(2*M)`,
   `M=28*Zc*Yc*Xc`.

   Use every signed corrected pixel. Residuals divided by `sqrt(M)` give the same
   least-squares half-squared norm. No mask, fitted intercept, source-volume
   multiplier, alternate weighting or crop normalization is introduced.
5. Every scored model evaluation has a trace entry. A represented carrier or
   geometry outside the physical domain is infeasible, not a successful optical
   prediction. Optimizer placeholders for infeasible trials are not model scores
   and cannot become candidates. No silent carrier clipping is allowed.
6. Retain the strictly lowest **actually evaluated** finite objective, including
   the seed; ties keep the earlier evaluation. Re-evaluate a proposed optimizer
   result before selection if it was not scored. A function-evaluation limit is
   finite completion, not convergence or physical identification. Record actual
   SciPy version/status/message/reported counts and independent model-entry counts.
7. The seed has its own prior freeze and Q512 held-out diagnostic. The new
   refinement/audit consumes no seed held-out values or summaries and makes no
   parameter/search decision from them. Freeze the newly selected candidate before
   its final Q128 held-out correction/comparison. Compute its complete held-out
   first-five prediction and signed per-exposure residual mean/RMS. Held-out data
   cannot choose parameters, trials, tolerances, stopping or the selected candidate.
   A late held-out failure retains the selected training candidate and trace.

For the new operation, a signed residual is **prediction minus corrected
observation**. Its mean and root-mean-square reduce over all detector z/y/x
sites separately for each orientation/exposure. This defines the subtraction
direction without changing an inherited operation.

`training_rms=sqrt(2*F)` is in reference-flat-relative image units. A value above
the supplied limit makes inference unavailable with `training_misfit`; it does
not trigger another search. Diagnostic candidate audit has no training residual
or optimizer because it receives no raw observations.

## Declared finite ambiguity audit

Audit the selected candidate against each direct alternative below. Retain the
seed's initial and frozen candidates as additional comparison cases in inference.
Transformations are generated from image-derived candidate values, never truth.
Evaluate direct alternatives **before any optional further optimization**; this
contract commissions no additional optimization of them. Do not erase a material
direct alternative by letting it converge back to the reference.

1. Global carrier/phase reversal and side exchange, across all orientations:
   `q'=-q`, `phi'=-phi`, `(a_plus',a_minus')=(a_minus,a_plus)`.
2. Beam-only side exchange, retaining source, carrier and phases.
3. Reflection of all calibration centers about the axial box midpoint, plus
   side exchange. Rebuild profiles; do not assume eight-focus data are invariant.
4. The alternate beam root, and its side exchange, when its represented physical
   domain is valid. With `S=a0²+ap²+am²`, set

   `a0'=(ap+am)/sqrt(S)` and
   `ap',am'=(a0 +/- sqrt(a0²-4*ap*am))/(2*sqrt(S))`.

   This preserves the even-axial coefficients U and W in the expectation seed.
   An inadmissible discriminant is an infeasible alternative, not a range failure.
5. For every bead and axis, center shifts of plus/minus one eighth of the fixed
   calibration detector spacing. Preserve all other physical parameters.
6. For every orientation and lateral axis, carrier shifts of plus/minus one
   calibration-box frequency `1/(N_axis*D_axis)`. Adjust that orientation's phases
   by `-2*pi*delta_q dot c0_yx` using estimated bead 0 as the fixed anchor, and
   recompute kappa. Also test individual carrier-component sign reflections.
7. For each of the 27 phases, individual phase negation and addition of pi.
   Also test each orientation's common shifts `pi/2`, `pi`, `3*pi/2`.

Use stable IDs containing transformation, bead/orientation/phase/axis and sign
where applicable. Retain deterministic order matching the list, then increasing
indices and negative before positive signs. Unchanged represented alternatives
are legitimate and may be harmless. Invalid transformed geometry/carrier/beam
domains are reported as infeasible. A numerical failure is not a passed audit.
Physical phase shifts are reduced with the physical period before storage when
needed; adding pi to an enormous angle must not silently erase the intended
shift through an unreduced float addition. Do not zero an arbitrary fitted phase.

For each feasible alternative, compare its **complete central plus structured
Q128 predictions** with the frozen reference, without alignment or scale fitting:

`calibration_delta = max(abs(prediction_alt - prediction_reference))`.

It is audit-equivalent precisely when the computed delta is at most
`calibration_atol`, in absolute reference-flat-relative image units. This is a
declared finite comparison, not a statistical indistinguishability certificate.
If calibration-distinct, record that outcome; operator comparison is unnecessary.

For an audit-equivalent alternative, transfer its own first-five phases once and
compute

`operator_delta = max |I_alt - I_reference|`

over all three orientations, first-five exposures, every declared specimen
half-cell lateral source site and every source/focus axial displacement. Source
and focus z sites have spacing `Dz`; possible displacements are
`-(Z-1)*Dz,...,0,...,(Z-1)*Dz`. Lateral source sites are
`((j_y+1/2)*Dy/2,(j_x+1/2)*Dx/2)`. Evaluate the full normalized unequal-beam
squared field with source-minus-focus sign. There is no specimen source input.
Do not replace this full finite field with its center, a peak, a slice or calibration
positions. Streaming equivalent evaluation is allowed; no fixed resource promise
is selected.

The difference is dimensionless. For the common nonnegative exact physical pupil
model it gives `|delta_prediction(x)| <= operator_delta*U_x` for nonnegative x,
where `U_x` is that source's unilluminated prediction. Report inverse arithmetic
and source-basis discrepancy separately. The measured finite comparison has
ordinary float64 evaluation limits; it is not an exhaustive/global uncertainty
enclosure. Use bounded trigonometric arguments, preserve the physical transfer
period, and report concrete numerical precision/representation obstruction as
incomplete instead of passing an unevaluated field.

A calibration-equivalent alternative with computed `operator_delta > operator_atol`
is material. It makes the handoff unavailable. Equality is harmless under these
declared settings. Record every case; no material alternative may be relabeled
as harmless merely because a local fit is smooth or another candidate was chosen.
An uncompleted required comparison makes the audit incomplete.

This audit does not enumerate every occupancy class, continuous carrier, phase
branch or shared-nuisance alternative. Record that limitation explicitly.

## Transfer, output and scientific claim

Use the same carrier/side labeling, reference-flat-relative camera gauge and
calibration box-corner phase origin. Transfer the selected first five phases once:

`phi_spec = wrap_physical(phi_cal + 2*pi*q dot (O_spec-O_cal)_yx)`.

Preserve the existing physical-period/endpoint meaning, including stable complete
origin differences. An overflowing unreduced origin product alone is not a range
obstruction. The specimen fit already receives specimen-origin phases and must
not transfer or normalize again. Do not recenter by a bead peak or independently
normalize orders. No calibrated-photon or absolute beam-power claim is made.

Return frozen-binding `CalibrationHandoff` with these fields:

- `status`, `stage`, `reason_code`, `message`, `failure_code`;
- `input_kind`: `observations_only` or `supplied_candidate_diagnostic`;
- `global_operator_identification`: always `unestablished`;
- `candidate`: independent selected/rebuilt `PilotCandidate`, or None;
- `specimen`: `SpecimenIllumination` only for a successful predictive/diagnostic
  result, otherwise None;
- `seed_result`, `refinement`: existing seed result and `RefinementSummary`, or
  None when not reached/not applicable;
- `audit`: ordered tuple of `HandoffAuditCase`; `audit_complete`: bool;
- `training_rms`: finite nonnegative float or None;
- `heldout_prediction`, `heldout_residual_mean`, `heldout_residual_rms`: complete
  Q128 arrays `(3,5,*Nc)`, `(3,5)`, `(3,5)`, or None when unavailable/not reached;
- `provenance`: independent dict recording source, model/Q/optical/source/pixel
  conventions, both origins and specimen grids, consumed camera values, controls,
  versions, actual audited scope and explicit scientific/numerical limits.

`SpecimenIllumination` has `carriers_yx_per_um`,
`phases_at_specimen_origin_rad`, `beam_amplitudes`, `camera_estimate`,
`detector_shape_zyx`, `detector_spacing_um_zyx`, `source_shape_zyx`,
`source_spacing_um_zyx`, `specimen_origin_um_zyx`, `pupil_order` and
`illumination_source`. Its arrays and consumed camera fields are independent
snapshots. The camera record retains unconsumed fields as opaque original values;
no new validation/ownership guarantee applies to them. This is not another camera
estimate. Record phase anchoring at the specimen box corner and Q128 explicitly.

`RefinementSummary` records `status`, `message`, `nfev`, `njev`,
`objective_evaluations`, `successful_evaluations`, `infeasible_evaluations`,
`initial_objective`, `best_objective`, `best_evaluation_index` and `trace`.
Each trace entry is frozen `RefinementScore` with `evaluation_index`, `outcome`
(`scored`, `infeasible`, `numerical_incomplete`) and `objective` (or None for an
unscored/incomplete evaluation). Report unavailable counters as None, not zero.

`HandoffAuditCase` records `case_id`, `outcome`, `candidate`,
`calibration_max_abs_difference`, `operator_max_abs_difference`,
`calibration_equivalent`, `material`, `reason` and `failure_code`.
Outcomes are `calibration_distinct`, `equivalent_harmless`, `material_alternative`,
`infeasible`, `numerical_incomplete`. Distinct cases may omit operator delta;
infeasible cases have no candidate/deltas and no equivalence/material verdict;
incomplete cases retain only completed observations. Missing values are None.

Provenance includes these named keys (additional descriptive entries are allowed):
`model="ra12_clear_pupil_predictive_handoff_v1"`, `source`,
`global_operator_identification="unestablished"`, `confidence_guarantee=None`,
`output_unit="reference_flat_relative"`, `pupil_order=128`,
`calibration_shape_zyx`, `calibration_origin_um_zyx`,
`specimen_detector_shape_zyx`, `specimen_detector_spacing_um_zyx`,
`specimen_source_shape_zyx`, `specimen_source_spacing_um_zyx`,
`specimen_origin_um_zyx`, `camera`, `controls`, `phase_transfer`,
`audit_scope="listed_direct_transformations_only"`, `numpy_version`,
`scipy_version`, and `limitations`.
`camera` holds independent consumed `means_counts`, `contrast_counts`, `source`.
`controls` holds the named numeric controls; inference-only controls are None
for diagnostic audit. `phase_transfer` records origins, first-five indices and
`application_count=1` when specimen outputs exist (0 otherwise).
`limitations` explicitly states finite audit, absent global identification and
confidence guarantee, synthetic optics and separate source/inverse errors.

Statuses are `predictive_estimate` (inference), `diagnostic_candidate` (diagnostic),
`unavailable`, `numerical_incomplete`. Success requires completed necessary fit,
training-limit check, complete audit without a material surviving alternative,
complete transfer, and, for inference, final held-out output. Unavailable reasons
include normalization, seed initialization, training misfit or material audit
alternative. Stages identify `seed`, `refinement`, `training_fit`, `audit`,
`transfer`, `heldout`, `specimen_geometry` or `complete`. A valid unsuccessful
optimizer limit does not imply convergence. No status is `identified` or
`recovery_passed`; no statistical confidence coverage is promised.

Known dependency range codes remain the `failure_code` of numerical incomplete;
own range obstruction uses `calibration_handoff_range`. Invalid-input errors,
unrelated exceptions/warnings and actual `MemoryError` propagate appropriately;
do not broadly suppress or relabel them. Preserve inputs/layout/write flags,
NumPy policies, warnings and global random state. Produced mutable arrays are
owned native writable C-contiguous float64 and do not alias other produced
payloads or consumed input arrays. Direct record construction authenticates nothing.

## Scenarios, ownership and checks

The public obligations include both operations/binding/labels; observed camera
gauge and no double correction; complete finite residual/refinement selection;
seed/limit/information/range outcomes; held-out independence; every declared
audit transformation and its feasible/infeasible cases; harmless global side
gauge; balanced and unequal-side single-focus material alternatives; profile and
carrier branches; whole-field operator comparison; exactly-once nonzero/large
origin transfer; all input/representation/error boundaries; independent mutable
outputs; unchanged legacy interfaces; and actual specimen-consumer composition.
A maps every distinct decision and relevant risk to independent public tests,
including an affordable observation-only positive and unavailable control.

High risk: fresh native blind A/B, restricted fresh C and fresh D. A owns only
`tests/test_image_only_calibration_handoff.py` and optional
`tests/image_only_calibration_handoff_fixture.py`. C owns the new adapter,
`scripts/physical_phase.py`, and only the unchanged extraction/import replacement
of the existing physical-phase helpers in `scripts/full_noisy_study.py`. Existing
private names and study call sites retain behavior. This extraction allows
inference to import numeric phase logic without importing a generator/evaluator.
C cannot change reviewed tests/fixtures, dependencies, workflows, gates or policy.

Inherit PROJECT approved behavior/risk review and advisory percentages, with
complete separate local/Ubuntu24.04/macOS15 native coverage/report evidence.
Focused checks include the four roadmap calibration files, the new tests and
existing `tests/test_full_noisy_study.py` for unchanged phase-helper compatibility.
Exact committed full-local `make verify`, fresh D, figure-bearing presentation,
separate platform qualification and completion cleanup remain binding.

Before adoption, retain actual independent held-out calibration and full-field
specimen prediction evidence with frozen inference/evaluator separation. Derive
arithmetic/control tolerances independently before acceptance. No full27-object
benchmark, empirical optics, global identification, confidence guarantee or
owner-output parity is claimed by finite-control success. Human numeric limits
are not set; scientific finite-procedure controls create no spending cap.
