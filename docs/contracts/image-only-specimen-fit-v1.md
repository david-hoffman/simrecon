# Image-only relative-unit specimen fit v1

**Version1.0, October25,2026.** Coordinator-adopted task contract under the owner's full noisy images-only PR53 request. This specifies necessary scientific behavior; it is not an implementation, test checkpoint or review verdict. Dependent execution waits for a completed independently reviewed camera/inverse baseline.

## Boundary, dependencies and scientific meaning

The one operation is in `scripts/image_only_specimen_fit.py`, with no package export:

```python
fit_specimen(
    raw_counts, *,
    camera_estimate,
    carriers_yx_per_um,
    phases_at_specimen_origin_rad,
    beam_amplitudes,
    illumination_source,
    detector_spacing_um_zyx,
    specimen_origin_um_zyx,
    pupil_order,
    regularization,
    max_iterations,
    max_backtracking_trials,
) -> SpecimenFitResult
```

It is deterministic, pure, in-memory finite optimization. It performs no file I/O, persistence, random sampling, callback, timeout/retry loop, calibration search or truth evaluation. Its scientific dependencies are only the completed public `ScalarCameraEstimate` record and the completed `build_kernel_cache`, `forward` and `adjoint` inverse operations. In particular it neither imports nor calls the calibration pilot, source generator or image generator. It accepts no `CalibrationPilotResult`, cache, optical transfer array, source-support mask, source truth, true gain, true brightness, noiseless mean, seed, fitted intercept or optimization callback.

Fixed conditional model settings are excitation wavelength 0.488 µm, emission wavelength 0.525 µm, refractive index 1.515, detection numerical aperture (NA) 1.4 and the inverse's clear finite-order pupil. The four pixel midpoint samples are unchanged. These are declared synthetic model assumptions, not inferred empirical optics. `pupil_order` selects the existing finite model without an additional refinement search.

For detector shape `(Z,Y,X)`, the source basis has shape `(Z,2*Y,2*X)` and spacing `(Dz,Dy/2,Dx/2)` in µm, with the same box corner. The unchanged inverse defines all half-cell anchors, source-minus-focus signs, pixel-area weights and exterior-zero boundary behavior. The axial basis is an explicit approximation to the independent generator; it is not a scalar unit correction or a resolution claim.

Let `b=float(camera_estimate.means_counts[1])` and `d=float(camera_estimate.contrast_counts)`. When `d>0`, observations are the signed reference-flat-relative values `Y=(C-b)/d`. Subtracting the blank mean retains background shot noise. The inverse's one-electron basis response divided by one electron defines the dimensionless numerical map `K_o`. Passing relative coefficient numbers to its existing `source_e` argument is computational basis scaling, not an assertion that the fit recovered electrons. Source entries are integrated reference-flat-relative weights. Add no source-volume, focus-spacing, electron-gain or true-reference-flux factor.

The supplied phases are **already anchored at the specimen origin**. This operation neither transfers nor wraps them. The driver must transfer the pilot's first five phases exactly once using `wrap(psi_cal + 2*pi*q_hat dot (origin_spec-origin_cal)_yx)`, maintain the same carrier/side-exchange gauge and paired camera gauge, and retain estimator/search/freeze identities. Changing only the origin label while holding supplied phases and other inputs fixed changes only recorded metadata. It is not a request to change the physical phases. The operation cannot authenticate that arrays were estimated or share an acquisition; opaque source strings are provenance labels, not certificates. A supplied-truth diagnostic does not complete the image-only experiment.

## Input grammar and exact validation order

Ordinary Python missing, extra or wrongly bound arguments raise the ordinary `TypeError` before this body runs. Otherwise validate the following groups in the listed order. Within a group, representation precedes shape, which precedes value/domain checks. A failed group raises `SimreconError` with code `invalid_image_only_specimen_fit`; diagnostics identify the field. Exact prose and selection of an offending element within a failed array are not promised. All groups are validated before any informational outcome or inverse call, including when the camera contrast is nonpositive.

1. `raw_counts`: `type(value) is numpy.ndarray`; dtype is native-endian float64, including NumPy's native `=` spelling; rank five; leading shape exactly `(3,5)`; all three spatial dimensions positive; every represented value finite. Reject non-native endian float64, other widths/kinds, subclasses (including memmap/masked arrays), lists and nonarrays. Signed counts and any legal strides, Fortran order, read-only state and zero strides are valid. A plain ndarray view of a mapped array is valid under the ordinary ndarray rule. This creates no separate memmap API.
2. `camera_estimate`: an instance of public `ScalarCameraEstimate`, allowing subclasses under the same consumed-field checks. Validate `means_counts` as a plain native float64 ndarray of shape `(3,)` with all values finite; `contrast_counts` as a plain built-in `int` or `float`, excluding bool and scalar subclasses, whose float64 normalization is finite; and `source` as a plain built-in string with at least one non-whitespace character. Preserve the source string unchanged. These are the actual fields of the adopted camera contract. Do not inspect or require `gain_counts_per_e`, variance fields, information codes, frame arrays or any other unconsumed field. Direct construction provides no provenance authentication. Do not impose a second relation between contrast and means beyond the consumed-field grammar.
3. `carriers_yx_per_um`: plain native float64 ndarray `(3,2)`, all finite. For each row require the exact-real domain of the normalized values, `q_y**2+q_x**2 <= (1.515/0.488)**2`, as in the inverse contract. A square or norm overflow is not an input-domain proof. Zero, signed and repeated carriers are legal; no rank, nominal-orientation or conditioning gate is added.
4. `phases_at_specimen_origin_rad`: plain native float64 ndarray `(3,5)`, all finite. Arbitrary finite phases, duplicates and large reducible angles are legal. No extra magnitude cap or phase-diversity requirement is added.
5. `beam_amplitudes`: plain native float64 ndarray `(3,)`, all finite, nonnegative and with at least one strictly positive entry. The order is `(central,+side,-side)` and the amplitude triple is shared across orientations. The existing inverse normalizes by squared amplitude sum; no exact represented unit-norm check or extra normalization round is required. Unequal sides and a single active beam are legal.
6. `illumination_source`: plain built-in nonblank string, preserved unchanged by the same string rule as camera source.
7. `detector_spacing_um_zyx`: plain built-in length-three tuple of plain built-in `int`/`float` scalars excluding bool/subclasses. Normalize each to finite strictly positive float64, then store Python floats.
8. `specimen_origin_um_zyx`: the same tuple/scalar grammar, but finite values may be signed or zero. It is a known box-corner label. No global-coordinate or minimum-box-size check is added.
9. `pupil_order`: plain built-in strictly positive `int`, excluding bool/subclasses.
10. `regularization`: plain built-in `int`/`float` excluding bool/subclasses, normalizing to finite strictly positive float64. Store it as a Python float.
11. `max_iterations`, then `max_backtracking_trials`: each a plain built-in strictly positive `int`, excluding bool/subclasses. Counts and products of dimensions use exact Python integers; do not impose a float-exactness cap on these settings.

Scalar conversion overflow is an invalid representation, not a numerical fit failure. No arbitrary shape, intensity, pupil-order, iteration, trial, scenario or review cap is selected. Actual indexing/address-space obstructions are operation-time range failures, not malformed-input classifications. Actual allocation `MemoryError` propagates.

Snapshot consumed camera and illumination arrays and all consumed scalar/tuple/string metadata. Returned metadata uses independent owned writable C-contiguous native float64 arrays. The raw count payload may be borrowed for read-only use; do not mutate it or change its flags, and do not make an unconditional full-payload snapshot. Preserve every caller array, layout, write flag, NumPy error policy, warning policy and random state on both return and exception. Concurrent external mutation is outside the promise. No allocation/layout inference is an authenticity check.

`camera_estimate=None` is invalid; it is not an unavailable estimate. If a camera estimate could not be produced, the driver reports that earlier failure and does not invent one. A valid camera record with `d<=0` returns `normalization_unavailable` after all validation, after recording exact-integer source_shape_zyx=(Z,2*Y,2*X), without deriving source half-spacing, checking indexability, building a cache, dividing observations or creating a candidate. Missing or uninformative physical gain does not prevent a fit when `d>0`. The obsolete draft's `calibration_unavailable` status is absent because this API has no optional calibration result.

## Float64 scores, rounded residuals and range-safe arithmetic

Write `M=15*Z*Y*X` and `N=Z*(2*Y)*(2*X)`. For a represented nonnegative float32 source `x`, the intended objective is

```text
J_data(x) = sum_(o,p,k) (K_o(x)[p,k] - Y[o,p,k])**2 / (2*M)
J_penalty(x) = regularization * sum_j x[j]**2 / (2*N)
J(x) = J_data(x) + J_penalty(x).
```

Scores use the actual native float64 outputs of the three public forward calls made for that score. For each orientation compute signed normalized observations with range-safe float64 arithmetic for `(C-b)/d`, then `r64=RN64(prediction64-Y64)`. Here `RN32`/`RN64` mean IEEE round-to-nearest, ties-to-even conversion to the named format. There is no clipping of observations, predictions or residuals. An overflowing temporary `C-b` alone does not establish that the complete normalized observation is unrepresentable.

Compute the two objective components and signed residual means/root-mean-squares using safe float64 reductions. Exact-real expressions of represented inputs define the reduction targets; no particular summation tree or correctly rounded whole reduction is promised. The pointwise residual used for score is float64. A float32-residual score, truncated mask, discarded tail, absolute residual mean, extra fitted scale or replacement objective is forbidden. Ordinary float64 reduction roundoff can affect strict comparisons; there is no bitwise cross-platform search-path promise.

For each orientation/phase, with `L=Z*Y*X`, report `mean=sum(r64)/L` and `rms=sqrt(sum(r64**2)/L)`. Stable scaling must avoid overflow in raw squares, unsigned sums, signed sums, unnormalized norms, a raw `regularization*sum(x*x)`, or count conversions when the required final result is representable. Power-of-two scaling, scaled sums of squares and component-safe summation are permitted. In particular, finite residuals larger than `sqrt(float64_max)` are not automatically a score failure: the *normalized* final score decides range. An intermediate raw-square/sum overflow is never sufficient evidence for numerical incompleteness. A stable alternative must be used when it produces the required finite result. Final underflow to finite zero is allowed; avoid premature scaling/underflow that destroys a representable final result.

A score is complete only when both component objectives, their final float64 sum, and all 15 means and root-mean-squares are available, finite and in their required nonnegative domains (except signed means). Do not return `inf`, `nan`, an infinity sentinel or a partly fabricated score. An unrepresentable required observation, residual, score component or total gives `numerical_incomplete`. This remains a legitimate outcome for finite inputs; raw input finiteness is not an objective-representability guarantee. Required final arithmetic precision/range obstructions must be concrete, not resource/time caps or unavailable implementation. No arbitrary new percentage tolerance is added to the inverse budget.

A gradient pass is separate from scoring. Recompute orientations 0,1,2 at the same represented candidate. For each, form its signed `r64` by the same normalization/residual rule, then explicitly form `r32=RN32(r64)`. Finite conversion underflow is allowed. If any rounded residual is nonfinite, the gradient fails; do not clip, rescale it into a different residual or silently pass float64 to the adjoint. Call the public adjoint on this native float32 residual and accumulate the complete expression safely in float64:

```text
g64 = sum_o adjoint(r32_o)/M + regularization*x/N.
```

Orientations are produced sequentially, but no unsafe raw sum or premature `regularization/N` underflow is required. The complete represented gradient must be finite. It is an approximate gradient of the declared score: explicit residual rounding and the inherited operator approximation are present. It is not the exact derivative of every rounded score evaluation. Recomputed prediction/residual values belong to this gradient pass, not to the earlier score pass. The public diagnostic is the infinity norm `max(abs(g64))`, with its candidate identity. This finite component norm avoids imposing an unnecessary representability obligation on an unnormalized Euclidean norm. No gradient convergence threshold is introduced.

The inverse's builder and application bounds remain separate **0.01% (`1e-4`)** promises against their own unchanged targets. Their stated combined physical norm allowance is `2e-4+1e-8`. Neither that allowance nor either component budget includes residual rounding, iterate rounding, source-grid/continuum approximation, conditioning or optimizer error. This fit adds no reconstruction-accuracy, physical-identification, uniqueness or convergence promise.

## Finite score-first protocol

Record the exact-integer source shape (Z,2*Y,2*X) for every returned result. After validation and the `d<=0` outcome, derive the native float64 source spacing and assess required indexing geometry. A nonpositive/nonfinite represented half-spacing, unrepresentable required indexing geometry or other concrete derived-geometry obstruction fails at `geometry`. Do not pass an invalid derived spacing to the inverse and relabel its domain error. Build exactly one cache with the derived source geometry and fixed model settings. Use the supplied carrier row, supplied phase row and the built-in tuple tuple(float(a) for a in snapshotted_beam_amplitudes) for each orientation, with excitation 0.488 µm.

1. Create owned writable native float32 `x=0`, candidate 0. Score it. During a score, calculate the penalty first, then process orientations 0,1,2; each orientation normalizes its observations before entering its forward call, then forms residuals and scalar summaries. Finalize the data and total score after all three orientations. If the score succeeds, candidate 0 becomes the best scored source immediately. If it fails, no fitted source/score is returned.
2. Compute the initial candidate's gradient in a separate pass, normalizing before each forward, rounding its residual, then entering its adjoint before proceeding to the next orientation. A failure preserves the complete initial source and score. Only a fully completed gradient receives a gradient summary.
3. Form `d0=max(0,-g0)`. If every entry is zero, return `completed_finite_fit` with `no_projected_direction`. This describes the initial approximate-gradient direction, not stationarity of the physical model or an exact derivative.
4. Otherwise form `v=RN32(d0/max(d0))`. It is finite, nonnegative and contains at least one exact one. Make three additional forward calls, orientations 0,1,2, at `v`. Seed the step with the safe complete expression

   ```text
   t0 = sum(v*v) /
        (sum_o sum(forward(v)_o**2)/M
         + regularization*sum(v*v)/N).
   ```

   Its numerator/denominator raw squares and sums need not separately be stored as representable float64 scalars. Only the resulting seed step is a required public scalar; safely evaluate the complete positive ratio. A nonfinite or nonpositive represented seed is `numerical_incomplete` at `curvature_seed`. A raw intermediate overflow is insufficient. This is a curvature heuristic, not a bound on the Hessian, Lipschitz constant or convergence rate.
5. Enter outer iterations numbered 1 through `max_iterations`. Each starts from the current best accepted source and its complete gradient; the first step is `t0`, later carried steps are the last accepted trial's step. There is no step increase. Try up to `max_backtracking_trials`, numbered 1 onward within the iteration.
6. For each entered trial, assign its next candidate ID (1,2,3,... over all entered trials, even unscored or equal trials). Compute the pre-rounding projected-gradient diagnostic

   ```text
   PG_inf(x,g,t) = max_j abs((x_j-max(0,x_j-t*g_j))/t)
   ```

   using the exact-real projection expression and safe float64 evaluation. Equivalently its component magnitude is `abs(g_j)` for negative `g_j`, and `min(g_j,x_j/t)` for nonnegative `g_j`. This avoids overflow and is at most `max(abs(g))`; it is only a diagnostic, not a stopping threshold.
7. Form the projected trial in float64 before conversion: `z=RN32(max(0,x-t*g64))`. Ordinary float64 multiply/subtract rounding precedes the explicit float32 conversion. A negative overflowing preprojection value may project to exact zero; do not reject it solely because the discarded negative value is not finite. A positive preprojection overflow or a float32 conversion that rounds to infinity makes the trial `unrepresentable`, with no score or inverse call. Finite underflow is allowed. Values just above float32 maximum that still round to finite float32 are not rejected by an overly strict preconversion bound. Do not saturate, clip to float32 maximum or select another step silently.
8. If the formed finite float32 `z` equals `x` elementwise, record `stagnated`, make no score/gradient calls and return `float32_stagnation`. Retain the separate `PG_inf`, which can be nonzero. Otherwise score `z` in the same score-only pass used initially. Required score arithmetic or a known inverse range failure terminates with `numerical_incomplete`; it is not converted into an infinite cost or an ordinary rejection.
9. Compare complete **computed** total scores. If `J(z)<J(x)`, mark the trial accepted and promote its source and score immediately. Equality or increase is a rejected trial. A rejected trial receives no gradient. Acceptance never depends on an optimizer status, an unscored source, a gradient tolerance, an Armijo parameter or truth.
10. An accepted trial in the last permitted outer iteration returns `iteration_limit` immediately with its complete score; its now-unused gradient is `not_needed`. Otherwise compute the accepted candidate's gradient in a new orientation-at-a-time pass. If it fails, the promoted candidate remains the returned best and status is `numerical_incomplete`. A previous candidate's complete gradient may remain in diagnostics with its *old* candidate ID; it must never be claimed to belong to the promoted source. A successful new gradient starts the next outer iteration carrying the accepted step.
11. After a rejected or unrepresentable trial, if another trial remains, set `t=RN64(t/2)`. If that required next step is nonpositive/nonfinite, return `numerical_incomplete` at `backtracking_step`; no zero-step trial or false stagnation is recorded. If no trial remains, return `backtracking_limit` without computing an unused halving. There is no gradient or score for the unrepresentable trial.

The best source is the initial source followed only by strictly lower complete scores. A scored accepted candidate is retained even if later gradient/seed/step work fails. A trial's unscored array or partially calculated score cannot replace it. Score-first processing is an explicit refinement of the intake draft: it trades additional forward calls for simple, honest retention and bounded live memory.

Keep one incumbent source and at most one reusable trial source. Transfer/reuse owned buffers when candidates are promoted; do not snapshot a source volume per trace entry or make gratuitous full-volume copies at every trial. Rejected trials have no gradient allocation. Dispose of/reuse the old gradient after promotion when it is no longer needed. Predictions, normalized observations and float32 residuals are processed one orientation at a time; do not archive all 15 predictions or all orientation residual payloads. The final source can transfer ownership directly to the result. These are storage/lifetime requirements, not a portable peak-memory or runtime guarantee. Real allocation failures propagate.

## Exported records and exact field grammar

The script module exposes `fit_specimen` and the six record types below. All record bindings are frozen. Direct record construction adds no validation/authenticity promise. Strings are ordinary Python strings; every count/ID/index is a plain Python int, every reported real scalar a finite Python float unless the field is explicitly `None`. Tuples are built-in tuples. No output scalar uses `nan`/`inf` as missing data.

`SpecimenScore` has exactly:

- `candidate_id`.
- `data_objective`, `penalty_objective`, `total_objective`: finite nonnegative floats; total is the final float64 sum of the two returned components.
- `residual_mean`, `residual_rms`: length-three tuples, each holding length-five tuples of finite floats in orientation/phase order. RMS entries are nonnegative. Tuples avoid retaining prediction/residual arrays or duplicating large arrays.

`SpecimenGradientSummary` has exactly `candidate_id` and `max_abs`, for a fully completed gradient only. `max_abs` is its finite nonnegative infinity norm.

`SpecimenFitAttempt` has exactly:

- `candidate_id`, `iteration`, `trial`: candidate 0 uses iteration/trial 0; other records use entered outer/trial numbers.
- `from_candidate_id`, `gradient_candidate_id`: `None` for candidate 0; otherwise both identify the same current incumbent used to form the trial, even if a new candidate is then accepted.
- `step`, `projected_gradient_max_abs`: `None` for candidate 0; finite positive step and finite nonnegative diagnostic for every other entered trial.
- `outcome`: `initial_scored`, `accepted`, `rejected`, `unrepresentable`, `stagnated` or `score_incomplete`. A completed score that is later followed by gradient failure keeps `initial_scored`/`accepted`; it is not relabeled unscored.
- `score`: a complete `SpecimenScore` for `initial_scored`, `accepted` or `rejected`; otherwise `None`. Its candidate ID matches this entry.
- `gradient_state`: `complete`, `incomplete` or `not_needed`. Initial and nonterminal accepted candidates have complete/incomplete gradient state; rejected/unrepresentable/stagnated/score-incomplete and final-iteration accepted candidates have `not_needed`.
- `gradient`: matching `SpecimenGradientSummary` only when state is complete; otherwise `None`.

Every entered candidate has exactly one finalized attempt record. A failing score's record is `score_incomplete`. Candidate records contain no source array. Failure after a complete score is described by result stage/code and the gradient state, not a fabricated partial gradient. Curvature/step failures do not create fictional trial records.

`SpecimenFitCall` has exactly `call_index`, `operation`, `purpose`, `candidate_id`, `orientation`, `outcome`, `failure_code`:

- `call_index` starts at 1 and follows actual public call entry order.
- `operation` is `build_kernel_cache`, `forward` or `adjoint`.
- `purpose` is `cache`, `score`, `gradient` or `curvature_seed`.
- Cache has candidate ID and orientation `None`. Score/gradient calls identify their actual candidate and orientation 0,1,2. Curvature calls identify candidate 0, from whose gradient their direction was formed, with purpose distinguishing direction `v` from source `x0`.
- `outcome` is `completed` or `range_failure`. Completed means the public call returned; a later own residual/objective failure does not change that count. Range failure means the entered public call raised the recognized inverse range code, which is retained in `failure_code`. Completed entries have failure code `None`.

`SpecimenFitCounts` has exactly these nonnegative integer fields:

```text
cache_attempted, cache_completed, cache_failed,
forward_attempted, forward_completed, forward_failed,
adjoint_attempted, adjoint_completed, adjoint_failed,
score_attempts, scores_completed,
gradient_attempts, gradients_completed,
seed_attempts, seeds_completed,
iterations_started, trials_attempted,
trials_accepted, trials_rejected,
trials_unrepresentable, trials_stagnated,
best_updates
```

Call attempted = completed + failed for each operation in a returned result. Each real public entry, including a failed entry, counts once. Internal inverse transforms/cache validations are not calls. A score attempt starts before its penalty; a gradient attempt starts before its first orientation normalization; a seed attempt starts before its first direction forward. Their completion means their entire required result exists. `iterations_started` increments on entering its first trial; `trials_attempted` counts every noninitial attempt record. Accepted counts include a scored accepted candidate whose later gradient fails. Rejected counts exclude unrepresentable/stagnated/score-incomplete trials. `best_updates` counts the first complete initial score plus every strict accepted improvement, so it is zero before an initial score and otherwise `1+trials_accepted`. Attempt and call traces are authoritative; counters must agree with them and the explicitly recorded seed/gradient state. A complete score uses three forward calls; a complete gradient uses three additional forwards and three adjoints; a complete seed uses three further forwards. Partial attempts count only calls actually entered. There is no private backend call counter.

`SpecimenFitResult` has exactly:

```text
status, stage, stop_reason, message, failure_code, failure_component,
detector_shape_zyx, source_shape_zyx,
detector_spacing_um_zyx, source_spacing_um_zyx, specimen_origin_um_zyx,
excitation_um, emission_um, refractive_index, detection_na,
pixel_samples_yx, pupil_order, regularization,
max_iterations, max_backtracking_trials,
camera_means_counts, blank_counts, contrast_counts, camera_source,
carriers_yx_per_um, phases_at_specimen_origin_rad,
beam_amplitudes, illumination_source,
source_relative, initial_score, best_score, last_complete_gradient,
seed_step, attempt_trace, call_trace, counts
```

Shape fields are length-three positive-int tuples, with source shape computed using exact integers even if subsequent indexing geometry fails. Detector spacing/origin are normalized float tuples. Source spacing is a normalized float tuple after its successful derivation, otherwise `None`; nonpositive contrast does not derive it. Fixed model fields contain the constants above; `pixel_samples_yx` is `(2,2)`. Setting fields retain their normalized inputs. Camera mean, carrier, phase and amplitude arrays preserve the snapshotted represented values; `blank_counts` is the returned camera mean entry 1, `contrast_counts` its normalized contrast. Do not return a reconstructed/fabricated camera estimate.

`source_relative` is `None` until a complete score exists, thereafter the one returned best candidate: owned writable C-contiguous native float32 plain ndarray of source shape, finite and nonnegative. Its ID is `best_score.candidate_id`. `initial_score` is candidate 0's complete score or `None`; `best_score` is the current best complete score or `None`. `last_complete_gradient` identifies the latest fully completed gradient, possibly an older candidate than the returned best source, or is `None`. `seed_step` is the positive finite seed only after it is complete, otherwise `None`. Traces are tuples of the corresponding records; absent traces are empty. `counts` always exists.

All output arrays are independent of callers, other output arrays and other calls. Immutable score/gradient/tuple records may be shared between result fields and trace entries; they contain no mutable arrays. No initial/trial/prediction/gradient volume archive is returned. This avoids contradictory independence promises that would force full-volume snapshots.

## Status, stage, failure and partial-result rules

Status is exactly `completed_finite_fit`, `normalization_unavailable` or `numerical_incomplete`.

- `completed_finite_fit`: a complete best source/score exists. Stage is `complete`. Stop reason is exactly `no_projected_direction`, `float32_stagnation`, `backtracking_limit` or `iteration_limit` according to the protocol. Failure code/component are `None`. This is completion of a finite procedure, not convergence or identified recovery.
- `normalization_unavailable`: stage `normalization`; stop reason, failure code/component, source, initial/best scores, gradient and seed are `None`; traces empty and all counters zero. Valid metadata is retained. This ordinary information outcome is exclusively `contrast_counts<=0`.
- `numerical_incomplete`: stop reason `None`; preserve only complete scored candidates and complete diagnostics actually reached. Stage identifies the first failing required stage in execution order: `geometry`, `kernel_cache`, `initial_score`, `initial_gradient`, `curvature_seed`, `trial_score`, `trial_gradient` or `backtracking_step`. No later stage is attempted after the failure. `source_relative` and `best_score` either both exist or both are `None`.

Own required arithmetic/indexing failures use `image_only_specimen_fit_range`. `failure_component` is one of `source_geometry`, `observations`, `residual`, `penalty_objective`, `data_objective`, `total_objective`, `residual_mean`, `residual_rms`, `residual32`, `gradient`, `seed_step` or `step`, matching the failing obligation. For each orientation, residual computation precedes its mean, which precedes its RMS. After all orientations, data objective precedes total objective. Gradient residual32 conversion precedes that orientation's adjoint; complete gradient assembly/finiteness follows the three orientations. This order resolves competing operation-time failures without hidden recovery attempts.

Catch only `SimreconError` code `simulation_inverse_operator_range` from actual inverse calls. Return `numerical_incomplete` at the surrounding stage with that code unchanged and `failure_component="dependency"`; call trace retains the operation/orientation. Other SimreconError codes, unrelated exceptions or warning categories, actual `MemoryError`, process interruption and external timeout propagate unchanged. A source/pilot/camera range code is not special-cased: those operations are not called. Do not convert an invalid dependency/domain error to this fit's invalid-input code or a numerical status.

Contain only expected own arithmetic overflow/underflow/invalid warnings locally, preserving caller policy. Do not suppress unrelated backend warnings. No record is promised on a propagated exception; an external kill/timeout is incomplete execution, never a successful return. Messages are nonblank explanatory strings identifying the relevant stage; exact prose is not selected.

Partial information is deliberately simple: no incomplete score or incomplete gradient summary is emitted. The call trace and final stage document the attempted work. A lower score promoted immediately before an adjoint failure remains the best. A completely scored *rejected* candidate remains in the trace but cannot become best. A failed candidate's buffer never replaces an earlier scored source. No gradient from another source is relabeled to fill an unavailable field.

## Distinct behavioral decisions and independent proof obligations

These are meaning/scenario categories, not a numerical scenario or test cap. Equivalent values within one category are coverage examples. A/B should map every binding obligation above and challenge omissions rather than impose an arbitrary count.

- The explicit estimated-array boundary, fixed model, local phase anchor and driver-owned once-only phase transfer; no pilot dependency or truth/provenance authentication.
- Accepted native float64 raw/metadata representations, legal storage layouts, strict rejected representations, independent metadata snapshots and borrowed untouched raw payload.
- Ordered validation before ordinary unavailability; valid nonpositive contrast; unavailable physical gain with positive usable contrast; missing camera record as invalid.
- Exact geometry/unit bridge, signed blank subtraction, no intercept/clipping/volume factors, and all pixels/tails contributing to the float64 score.
- Range-safe normalized loss, signed means/RMS and gradient expressions; finite final quantities not rejected due raw-square/sum intermediates; genuine required representability failure.
- Explicit RN32 residual approximate gradient, including finite underflow and nonfinite residual conversion after a complete score.
- Initial zero score and approximate gradient; no projected initial direction as its own normal information stop.
- Curvature direction/ratio and counted extra forwards; genuine unusable seed without a convergence claim or arbitrary step cap.
- Float64 projection followed by RN32; legal underflow, negative overflowing preprojection becoming zero, positive/nonfinite trial as unscored backtracking, and exact finite equality as float32 stagnation with its separate diagnostic.
- Strict measured decrease, ties rejected, first accepted trial, carried step without increase, finite trial exhaustion and finite iteration exhaustion with unused final gradient omitted.
- Required next-step underflow as numerical incompleteness; no unused halving at an exhausted trial bound.
- Score-first immediate promotion, rejected candidates without gradients, and retained best after a later gradient failure with honest candidate identities.
- Initial/late own range versus recognized inverse range versus unrelated error/allocation/warning propagation; exact partial-record and no-fabricated-output grammar.
- Real public-call accounting, partial calls, sequential stages, bounded payload ownership and no per-trial source/prediction archive.

Independent tiny physical/cache matrix controls and legitimate one-variable geometries can establish units, signed complete loss, approximate-gradient rounding, seed, projection and strict selection. Independent constrained solutions may characterize selected small examples but must not turn a general finite-iteration test into a demand for the optimizer or truth. Initial passing controls are valid. No test-only production seam, dense production matrix, manufactured red, arbitrary recovery threshold or percentage-only test follows.

Before full-size fitting, preserve the inverse contract's tiny, moderate and bounded full-orientation resource prerequisites. Measure actual elapsed time, memory/footprint/headroom, swap/disk changes and complete status with no competing heavy phases; a plausible array count is not resource evidence. This operation adds no wall-clock/host-memory success guarantee. The 16 GiB host remains staging context. The later workflow must freeze fitted settings/source/predictions before evaluator truth and separately report acquisition assumptions, scale ambiguity, numerical/source-grid error, scientific errors and all failures.

## Public expectations and delivery

The mathematical expectation sources are this contract and the approved [inverse](simulation-inverse-operator-v1.md), [camera](scalar-camera-calibration-v1.md) and [calibration phase/gauge](image-only-calibration-pilot-v1.md) contracts. No runtime output supplies an independent oracle.

High-risk fresh native blind A/fresh B/restricted C/fresh D. A owns only tests/test_image_only_specimen_fit.py and optional tests/image_only_specimen_fit_fixture.py. C owns only scripts/image_only_specimen_fit.py. Tests/helpers/configuration/dependencies/gates/policy and unrelated interfaces remain frozen for C. Coordinator owns contracts, exact packets, studies/provenance, scientific report and preservation-aware completion cleanup. Inherit the active named full-noisy advisory-percentage migration without weakening behavior/risk review, exact full-local thirteen phases, native reports or required platforms. Human numeric limits are not set; preserve every prior charge.
