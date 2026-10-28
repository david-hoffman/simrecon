# Image-only finite bead calibration v1

**Version1.0, October25,2026.** Coordinator-adopted task contract under the owner's full noisy images-only PR53 request. Dependent execution waits for a completed independently reviewed pilot/optical/camera baseline. This document is scientific behavior, not a test checkpoint, implementation or review verdict.

## 1. Documentary basis and preserved scope

The approved public expectation source is [Image-only small calibration pilot v1](image-only-calibration-pilot-v1.md), version 1.0, SHA-256 **3b3c5a50d2f735ff973496c7c1d74d0d3d8249275d8a3a2456588b79267311ff** (17,255 UTF-8 bytes). Its referenced approved camera, finite-source and optical contracts remain the underlying mathematical expectations. This contract inherits those meanings; it does not substitute implementation output as an oracle.

The existing fit_small_pilot operation, public records, contract, tests and runtime definitions remain unchanged. The new operation performs image-conditioned finite fitting of three beads and illumination under a fixed clear pupil. It supplies no empirical pupil recovery, global optimization, unique physical identification, confidence interval, statistical uncertainty certificate, recovery threshold, continuum-accuracy claim or full-workflow completion claim.

Known stationarity, common dose and known registration remain explicit synthetic assumptions. The camera record is estimated from primary-camera observations. No true source, phase, carrier, beam, camera coefficient, noiseless image, seed, independent phase sensor or evaluator value is an input. Truth stays evaluator-only until the fitted candidate and held-out predictions are frozen.

## 2. Operation, ownership and dependencies

The new in-repository module scripts/image_only_bead_calibration.py exports:

~~~python
fit_bead_calibration(
    central_counts,
    *,
    structured_counts,
    heldout_counts,
    camera_estimate,
    origin_um_zyx,
    sweep_scales,
) -> BeadCalibrationResult
~~~

All keywords are required. No command-line interface, package-level export, acquisition, random stream, persistence, cleanup, transfer operation or full-shape resource probe is added.

C owns only the new runtime module. A owns tests/test_image_only_bead_calibration.py and optional tests/image_only_bead_calibration_fixture.py. Fresh B/D assess under the inherited route. Coordinator owns adoption, packets, dependency identities, studies, provenance, resource execution and presentation. This public contract requires no private helper, backend or cache layout.

Return candidates using the existing public PilotCandidate type, with exactly the fields and ownership rules in the pinned pilot contract. Do not extend or reinterpret that record. Export five new frozen-binding record types: BeadCalibrationScore, BeadCalibrationAttempt, BeadCoordinateEvidence, BeadCalibrationCounts and BeadCalibrationResult. Direct construction of any record authenticates nothing and adds no validation promise.

## 3. Inputs, validation and snapshots

Let detector shape N=(Nz,Ny,Nx).

- central_counts has shape N; each axis is nonempty and each exact physical side length N[a]*D[a] is at least 0.100 micrometres.
- structured_counts has shape (3,9,*N).
- heldout_counts has shape (3,5,*N).
- Each raw input is a plain numpy.ndarray, dtype kind i/u/f, with finite original values and finite values after native-float64 normalization. Signed values, conversion rounding and finite underflow, either endian, strided/reversed, Fortran-order and read-only storage are allowed. Bool, complex, object/other kinds, subclasses/masked arrays and nonarrays are invalid.
- Normalize and independently snapshot all three raw inputs before any correction or fitting. Held-out validation/snapshotting is permitted at this stage; held-out correction, summaries and value-dependent fitting decisions are not.
- camera_estimate is an instance of ScalarCameraEstimate; subclasses are accepted subject to the same consumed-field rules. Validate/snapshot means_counts as a plain finite native-float64 ndarray of shape (3,). contrast_counts is a plain built-in int/float, excluding bool and numeric subclasses, normalizing to finite float64. source is a nonblank string; copy its value as a Python str. Other fields, including physical gain and information codes, are not consumed and impose no new fit gate.
- origin_um_zyx is a length-three tuple; tuple subclasses are accepted. Its members are plain built-in int/float values, excluding bool/numeric subclasses, normalizing to finite float64. Store the three normalized values as Python floats. The origin labels the box corner; fitted centers remain local to it.
- sweep_scales is a nonempty **built-in tuple**, excluding tuple subclasses. Each member is a plain built-in int/float, excluding bool/numeric subclasses, normalizing to finite strictly positive float64. Store normalized values as a tuple of Python floats. Repeated, increasing or decreasing scales are legal; do not sort, deduplicate, clamp or silently append scales. These are finite algorithm settings, not owner time/cost limits.

An integer that cannot normalize to finite float64 is invalid. No arbitrary array-size, sweep-count, scale, intensity or resource cap is introduced. Actual allocation failures remain MemoryError. Snapshotting supplies no atomic guarantee against concurrent external mutation.

Validate all input domains, including held-out data and sweep_scales, before deciding that normalization is unavailable. Simultaneous-invalid-input precedence and exact diagnostic prose are unspecified. Ordinary Python missing/unknown-argument binding remains TypeError.

## 4. Model, units, objective and gauges

Inherit the pilot's fixed settings:

~~~text
D = (0.125, 0.080, 0.080) micrometres
source refinement = (8,8,8)
sphere radius = 0.050 micrometres
excitation/emission = 0.488/0.525 micrometres
refractive index = 1.515
detection numerical aperture = 1.4
clear matched-index scalar pupil
pixel midpoint samples = (2,2)
~~~

All three spheres must be complete, contained and nonoverlapping. Tangency is permitted. Geometry uses exact-real interpretations of normalized represented centers, radius, spacing and integer counts. No clipped sphere, support window or overlap repair is introduced.

Let b be snapshotted means_counts[1] and d be snapshotted contrast_counts. If d<=0, return normalization_unavailable without division. Otherwise correct training data as Y=(C-b)/d, preserving signed observations and background shot noise.

For each sphere, use the approved closed-midpoint source model with brightness exactly one electron and its prescribed rounded 1/K cell weights. Divide its electron-valued optical response by one electron to define the dimensionless unit response R_l. Predict the camera-relative mean as sum_l B_l*R_l. B_l is a nonnegative integrated reference-flat-relative brightness; never pass it under an electron label. Record occupied counts and stored unit masses through PilotCandidate. No exact stored mass conservation is promised.

At Q=128, the full-image training objective is

~~~text
F = (sum central residual^2 + sum all 27 structured residual^2) / (2*M)
M = 28*Nz*Ny*Nx
~~~

Use direct float64 residual squares and complete images. No masks, clipping, fitted intercept, freely fitted response images, weighting rule or held-out term is added. The unchanged finite source/pupil/pixel equation, all tails, source-minus-focus sign, continuous signed carriers and pupil normalization apply. Candidate-derived caching is allowed only when it preserves these targets and the records of completed work.

Phases are anchored at the supplied origin. The existing first-five-command transfer rule remains documentary context:

~~~text
psi_spec = wrap(psi_cal + 2*pi*q_hat dot (origin_spec-origin_cal)_yx)
~~~

No transfer is performed here. Bead permutation, phase wrapping, consistent side-beam exchange/carrier reversal and occupancy-equivalent centers remain alternatives. A local-box fit is invariant to origin value except for its recorded metadata and later transfer.

## 5. Observation-only initialization

Use the pinned pilot's initializer, without calling its Powell search:

1. Smooth signed corrected central data with Gaussian sigma=(1,1,1), radius=4, order=0, constant-zero boundary and float64 output. Record the actual SciPy version.
2. Select three strictly positive peaks sequentially; ties use lexicographic z/y/x order. Suppress detector-center locations within <=0.5 micrometres of each chosen sample. Add no local-maximum condition.
3. At each peak use the clipped unsmoothed window +/-2 z and +/-3 y/x samples, with weights max(Y,0), to compute its physical detector-center weighted centroid. Zero total weight fails initialization.
4. Clamp only that initial centroid to [a,u] on each axis, where u is the largest float64 not exceeding exact N[a]*D[a]-a. Record clipped-window, overlapping-window-pair and clamped-coordinate counts. Reject overlapping initialized spheres without repair or another peak search.
5. For each initial sphere, divide the strictly positive maximum unsmoothed central value in its centroid window by the strictly positive maximum complete Q128 central-only unit-response image. These three finite strictly positive values are B_start and remain fixed brightness-coordinate scales throughout the call.

Missing positive peaks, zero centroid weight, overlapping initialized centers, or a finite unusable initial response/brightness are initialization_failed. A known numerical range failure during the required calculations is numerical_incomplete, not initialization_failed.

Store initialization_notes only once the centroid procedure has produced its complete geometry/accounting; it contains the actual SciPy version and the three counts above. Its prose format is unspecified. It may remain available if a later unit-response calculation fails.

## 6. The 47-coordinate state and decoder

The authoritative coordinate array z is owned native float64, shape (47,). Center entries are stored in micrometres to preserve the initialized centroids without a c/D then D round trip. Their normalized polling displacement is one eighth of detector spacing. The remaining entries are dimensionless normalized coordinates.

| Index | Meaning | Allowed interval | Base step |
|---|---|---|---|
| 0..8 | Centers, bead-major then z/y/x, in micrometres | Exact containment and nonoverlap below | D[axis]/8 |
| 9..11 | B_l/B_start_l | [0,100] | 0.1 |
| 12 | gamma/(pi/2) | [0,1] | 0.05 |
| 13 | eta/(pi/2) | [0,1] | 0.05 |
| 14,16,18 | rho_o/k0, orientations 0..2 | [0,1] | 0.01 |
| 15,17,19 | omega_o/pi, orientations 0..2 | [-1,1] | 0.01 |
| 20..46 | psi_op/(2*pi), orientation-major then nine commands | [-1,1] | 0.05 |

Let pi64 be nearest native float64 to pi and k0_float the native-float64 quotient 1.515/0.488. Decode using ordinary float64 arithmetic:

~~~text
B_l = z[9+l] * B_start_l
gamma = z[12]*(pi64/2)
eta = z[13]*(pi64/2)
a0 = cos(gamma)
a_plus = sin(gamma)*cos(eta)
a_minus = sin(gamma)*sin(eta)

rho_o = z[14+2*o]*k0_float
omega_o = z[15+2*o]*pi64
q_o = rho_o*(sin(omega_o),cos(omega_o))

psi_op = z[20+9*o+p]*(2*pi64)
~~~

Use exact endpoint zeros: gamma-coordinate 0 makes both side amplitudes exactly zero; gamma-coordinate 1 makes a0 exactly zero; eta-coordinate 0 makes a_minus exactly zero; eta-coordinate 1 makes a_plus exactly zero. Stored amplitudes need not have an exactly unit floating sum of squares; use the approved optical S normalization. Preserve ordinary positive underflow-to-zero in decoded brightness; a nonfinite required decoded value is numerical_incomplete.

Check each represented carrier against the exact-real domain |q|<=1.515/0.488, using the normalized represented q components. An inadmissible represented carrier is an infeasible trial, never clipped. Recompute kappa from every changed carrier under the approved formula. Do not round carriers to Fourier bins.

The initial coordinate state consists of the retained centroids, three brightness coordinates equal to 1, gamma-coordinate acos(1/sqrt(3))/(pi64/2), eta-coordinate 1/2, three radius coordinates 1.2/1.515, angle coordinates (0,1/3,2/3), and three copies of the normalized command sequence:

~~~text
(0, 1/5, 2/5, 3/5, 4/5, 1/10, 3/10, 7/10, 9/10)
~~~

Decode this state once to obtain the initial candidate, then score it once at Q128. The physical initial settings match the pilot to ordinary float64 roundoff; no bitwise equality to its separately assembled initial candidate is promised. Keep B_start fixed; do not rebase brightness coordinates after improvements. Retain the coordinate state rather than recovering angles or brightness ratios from fitted arrays between polls.

## 7. Complete deterministic paired polling

For each supplied scale, in supplied order, visit coordinate indices 0 through 46. There is no early stopping after nonimprovement, small improvement or small displacement.

At each coordinate:

1. Save the pre-coordinate incumbent coordinate state, successful Q128 score and candidate.
2. Compute step=RN64(base_step*scale). Form negative then positive trials by changing only this coordinate to RN64(old_value+sign*step). Both trials use the same pre-coordinate state. Finite step underflow or addition rounding may leave the coordinate unchanged; this is recorded, not repaired.
3. Check scalar-coordinate bounds for indices 9..46; then exact center containment/nonoverlap; then the represented carrier domain. These ordered checks select infeasibility_reason as coordinate_bounds, center_geometry or carrier_domain. Infeasible trials require no optical prediction. They still receive attempt records.
4. Score every feasible trial at Q128, including unchanged represented trials. Changed centers use their newly generated prescribed source profiles. A successful score means the complete objective target was evaluated; faithful candidate-derived reuse is permitted and creates no backend call-count obligation.
5. Decide only after both attempts finish. Among successfully scored trials strictly below the pre-coordinate objective, select the lowest objective. Equal improving scores select the negative trial. Otherwise retain the pre-coordinate incumbent. Set both attempt selection fields only after this decision.
6. Continue with the resulting incumbent and the next coordinate.

No clamping, step shrinking, angle wrapping, replacement direction, retry, second start or hidden evaluation cap is part of this operation. A known numerical failure stops the call at that stage; do not continue to the other sign or next coordinate.

Maintain a separate best actually scored Q128 candidate, updating only on strict improvement in chronological score order. Ordinarily it equals the incumbent after each complete pair. If a pair stops after a scored improvement but before selection, preserve that best scored candidate while leaving the pair's selection unresolved. Do not pretend the paired decision or sweep completed.

For S scales, a completed protocol attempts exactly 94*S polls. It has at most 94*S+3 score attempts including initialization and Q256/Q512 rescoring. Infeasible polls do not enter the objective trace. These are algorithm counts, not review/scenario quotas or owner spending limits.

The intake's proposed substantive schedule (1,0.5,0.25,0.125,0.0625,0.03125) means 564 signed attempts and at most 567 score attempts. It is an experiment setting to be recorded before that fit, not an accuracy threshold or mandatory API default.

## 8. Freeze, quadrature rescores and held-out observations

After every prescribed pair has completed, freeze the final Q128 incumbent. Rescore that exact represented candidate, with unchanged source profiles and coordinate state, first at Q256 and then Q512. Do not fit or select using those scores.

Next compute its complete first-five-command prediction at Q512, shape (3,5,*N), and retain an independent snapshot. Only after that prediction is fixed may the function correct held-out observations and calculate signed residual mean and root-mean-square over z/y/x for each orientation/command.

Validate both residual-summary arrays before publishing either. If this late stage fails, retain the completed prediction and earlier scores, with both summaries None. A failed prediction supplies no successful partial prediction array.

Changing valid held-out pixels cannot change initialization, attempted training coordinates, candidate selection, training scores, sweep completion or search diagnostics. It may change only held-out summaries and a late held-out numerical outcome. Invalid held-out representation is still an input error before fitting.

## 9. Exact public record grammar

All output scalar counts/indices are Python ints, not bool or NumPy scalar types. Scalar coordinates/objectives are Python floats where applicable. All described tuples are built-in tuples. All returned arrays are plain writable C-contiguous native-float64 ndarrays, finite unless a field is None. Arrays are independently owned across callers, calls, records, trace entries and candidate fields. No raw observation archive is returned.

PilotCandidate remains exactly the existing public type, with its existing shapes: centers (3,3), brightness (3,), carriers (3,2), phases (3,9), amplitudes (3,), three occupied counts and stored unit masses (3,).

### BeadCalibrationScore

Exactly these fields:

| Field | Meaning |
|---|---|
| stage | initial, poll or refinement |
| pupil_order | 128 for initial/poll; 256 or 512 for refinement |
| coordinates | Independent (47,) coordinate snapshot, or None if not yet representable |
| candidate | Independent PilotCandidate for a successful score; otherwise None |
| objective | Finite nonnegative Python float for scored; otherwise None |
| outcome | scored or numerical_incomplete |
| failure_code | None for scored; the recorded range code for numerical_incomplete |

A score attempt begins after a poll's cheap feasibility checks and includes required profile construction, prediction and objective arithmetic. A failure within that attempt appends one numerical_incomplete score. A failure while forming a poll coordinate, before scoring begins, has an attempt record but no score record. Initial and refinement failures likewise have a failed score record once their scoring stage begins.

Scores are in actual chronological order. Higher-Q rescores are never eligible for Q128 best-candidate selection. There is no fabricated score for an infeasible trial or unexecuted stage.

### BeadCalibrationAttempt

Exactly these fields:

| Field | Meaning |
|---|---|
| sweep_index | Zero-based supplied scale index |
| coordinate_index | 0..46 |
| sign | -1 or +1 |
| base_score_index | Index of the successful Q128 pre-coordinate incumbent in objective_trace |
| trial_coordinates | Independent finite (47,) proposed coordinate vector, including finite infeasible values; None only if formation failed |
| coordinate_changed | Numerical inequality of the proposed scalar and its pre-coordinate scalar; None if formation failed |
| parameter_changed | For scored trials only, the physical-parameter comparison defined below; otherwise None |
| outcome | infeasible, scored or numerical_incomplete |
| infeasibility_reason | coordinate_bounds, center_geometry or carrier_domain for infeasible; otherwise None |
| score_index | Matching objective_trace index if scoring began; otherwise None |
| selected | True/False after the pair's decision; None while a pair remains incomplete |
| information_codes | Ordered tuple defined in section 10; empty for unscored attempts |
| failure_code | Range code for numerical_incomplete; otherwise None |

For scored trials, parameter_changed compares the relevant represented physical parameter with the pre-coordinate candidate, using exact elementwise numerical equality without a tolerance: one center component, one relative brightness, all three beam amplitudes, the selected two-component carrier, or the selected phase. Signed zero is not a distinct value. Coordinates and physical parameters are distinct concepts; changing an angle can leave a zero carrier unchanged.

At most one attempt in each completed pair is selected. Both selected fields are False if the incumbent remains. In an incomplete pair, all attempts from that pair have selected=None, even if a scored trial improved the global best.

### BeadCoordinateEvidence

The result contains exactly 47 of these records, in coordinate-index order. Each has exactly:

- coordinate_index
- attempt_count
- scored_count
- distinct_coordinate_scored_count
- distinct_parameter_scored_count
- selected_count
- information_codes

The counts are derived from poll_attempts for that coordinate. The two distinct counts require outcome=scored and the corresponding change flag True. selected_count counts selected=True. information_codes is the ordered union of codes from that coordinate's scored attempts.

A coordinate is unprobed precisely when distinct_parameter_scored_count is zero. This definition reports missing represented-parameter exploration; it is not an identifiability test. Known structural limits remain visible separately through information_codes.

### BeadCalibrationCounts

Exactly these fields, all derived from the declarations and ledgers:

- planned_poll_attempts: 94*len(sweep_scales)
- attempted_polls: len(poll_attempts)
- scored_polls: attempts with outcome=scored
- infeasible_polls: attempts with outcome=infeasible
- numerical_incomplete_polls: attempts with outcome=numerical_incomplete
- completed_pairs: pairs with both signs present and both selected fields resolved
- completed_sweeps: completed_pairs // 47, using the prescribed prefix order
- score_attempts: len(objective_trace)
- successful_scores: objective_trace entries with outcome=scored

No backend call counts, inferred timings, missing-as-zero metering or optimizer statistics are returned. The ledgers are authoritative; the counts must agree with them.

### BeadCalibrationResult

Exactly these fields:

- status, stage, message, failure_code
- detector_shape_zyx, origin_um_zyx, scipy_version
- camera_source, blank_counts, contrast_counts, sweep_scales
- initialization_notes
- initial_candidate, initial_coordinates
- best_candidate, best_coordinates, best_score_index
- incumbent_score_index
- frozen_candidate, frozen_coordinates
- objective_trace, poll_attempts
- coordinate_evidence, unprobed_coordinates, counts
- training_objectives_q128_q256_q512
- heldout_prediction, heldout_residual_mean, heldout_residual_rms

Metadata uses the normalized/snapshotted values. scipy_version is the nonblank Python str naming the actually loaded SciPy version and is present in every returned result, including unavailable outcomes. Shapes and origins are length-three tuples. Candidate/coordinate fields are independent snapshots or None. Index fields are Python ints or None. Trace/attempt/evidence fields are tuples of their named records. unprobed_coordinates is the increasing tuple of indices defined above.

initial_candidate/initial_coordinates become available once the initialized candidate is fully constructed, even if its first score later fails. best_candidate/best_coordinates/best_score_index exist only after a successful Q128 score. incumbent_score_index identifies the initial score or the result of the last completed paired decision. It can differ from best_score_index during an incomplete pair.

frozen_candidate/frozen_coordinates become available only after all prescribed pairs complete, before Q256 rescoring. They remain available if a later required stage fails.

training_objectives_q128_q256_q512 is a three-element tuple of finite nonnegative floats or None. Its Q128 element is the best actually completed Q128 score even during an incomplete search; it is not evidence of freezing. Its other elements are only the actually completed frozen-candidate rescores.

heldout_prediction has shape (3,5,*N), or None. Both residual summaries have shape (3,5), or are None together. Messages identify the relevant stage; exact prose is unspecified.

## 10. Bounded information-limit reporting

For each successfully scored poll, use the following fixed code order and exact conditions. They describe that comparison, not the final candidate or a global uncertainty certificate.

1. unchanged_coordinate: coordinate_changed is False.
2. unchanged_parameter: parameter_changed is False.
3. occupancy_equivalent_center: a center poll has exactly the same occupied-site set as its pre-coordinate one-electron sphere under the prescribed closed midpoint source model. Equal occupied counts alone are insufficient.
4. zero_brightness_center: a center poll concerns a bead with zero represented brightness in both candidates.
5. zero_carrier_angle: an angular carrier poll (indices 15,17,19) has an all-zero represented carrier before and after.
6. single_beam_illumination: a carrier or phase poll has exactly one nonzero represented beam amplitude. Its illumination is independent of those coordinates under the stated model.
7. zero_total_brightness: a center, beam, carrier or phase poll has all three represented brightnesses zero in both candidates.
8. equal_computed_objective: its completed objective equals the pre-coordinate objective as a floating-point value.

No tolerance is used for these code decisions. Profile equivalence is a statement about the full prescribed source profile, not rounded centroid distance or equal mass/count alone. The last code is only a computed-score observation: it does not prove equal predicted images, lack of information or physical equivalence.

A completed schedule can still have unprobed coordinates or observed structural limits. completed_finite_fit means that the declared procedure completed; it does not turn those coordinates into inferred quantities. A downstream report must not cite an unprobed coordinate as image-explored. A value remaining nominal after distinct scored comparisons may be a finite-fit estimate. No requirement forces it to move.

Do not add an uncontracted rank threshold, statistical significance test, confidence interval, ambiguity detector or truth-selected fallback.

## 11. Outcomes, failures and partial records

status is exactly one of:

- completed_finite_fit: all prescribed polls/pair decisions, both required rescores, complete held-out prediction and both residual summaries succeeded.
- normalization_unavailable: valid inputs but d<=0.
- initialization_failed: one of the finite information failures in section 5.
- numerical_incomplete: a required numerical stage failed with one of the known range codes below.

There is no converged, globally_identified or recovery_passed status. There is no internal time/evaluation interruption or resume interface. Finite-schedule exhaustion is ordinary completed_finite_fit when the required subsequent stages succeed. External timeout/termination is incomplete execution, not a returned success.

stage is exactly one of normalization, initialization, initial, poll, refinement_q256, refinement_q512, heldout_prediction, heldout_residual or complete. Invalid input raises before a result is returned. completed_finite_fit uses complete; normalization_unavailable uses normalization; initialization_failed uses initialization. Numerical failure reports the stage actually reached.

Invalid input raises SimreconError code invalid_image_only_bead_calibration. Own concrete nonfinite/negative-required-objective or otherwise unrepresentable required arithmetic uses image_only_bead_calibration_range. Known dependency ranges are simulation_source_range, simulation_optics_range and image_only_calibration_pilot_range; preserve the originating code in failure_code. The last is an existing public pilot range code, not permission to call its optimizer. Other SimreconError codes, unrelated exceptions/warnings and actual MemoryError propagate unchanged. Never relabel a dependency domain error as an infeasible optimizer point or silently suppress an unrelated failure.

Numerical range failures stop immediately without retry. Cheap domain infeasibility of a proposed coordinate is instead the explicitly recorded ordinary poll outcome. failure_code is None for all non-numerical statuses and successful/infeasible records.

Partial-state rules:

- All valid normalized metadata, supplied scales, zero/partial ledgers and derived counts remain available in a returned result.
- normalization_unavailable has no candidates, coordinates, score indices, initialization notes, scores or predictions. All 47 coordinate evidence records have zero counts and empty codes; all coordinates are unprobed. Planned attempts remain the declared 94*S.
- initialization_failed retains initialization_notes only if its complete centroid accounting was already available. It has no scored candidate or prediction. No partially assembled candidate is fabricated.
- A numerical failure before initial candidate construction retains no candidate. A failure during its initial score may retain initial_candidate/initial_coordinates but has no best successful score.
- A poll failure preserves all prior successful scores, the best scored candidate, the prior incumbent and the unresolved pair records. It does not freeze the candidate.
- A refinement failure retains the frozen candidate and completed lower-Q scores.
- A heldout_prediction failure retains earlier training/frozen records but no partial prediction array.
- A heldout_residual failure retains the complete frozen prediction; both residual summaries remain None.
- Missing arrays/candidates/indices/notes are None. Missing ledgers are empty tuples. Missing objective entries are None. Do not substitute zeros for missing measurements.

Preserve caller inputs, global random state and caller NumPy/warning policies on success and rejection. Locally contain only expected owned arithmetic warnings. No successful partial image or partial summary is returned.

## 12. Floating arithmetic and scientific uncertainty

The prediction target is the inherited finite normalized-input source/pupil/pixel equation. In the relative-unit composition, define U as the same candidate's unilluminated mean image and T=max(U). Preserve the inherited entrywise arithmetic allowance 1e-5*T in relative units, with exact zero when T=0. Account for all component/assembly errors; separately allowed component errors cannot simply be ignored when forming the total. No absolute floor, crop normalization, relative-L2 substitution or special-case brightness relaxation is introduced.

Coordinate decoding, corrections, centroid reductions, residuals, objectives and summary calculations use float64 with the ordinary-roundoff/underflow meaning of the pilot contract. No reduction order or cross-version bitwise equality is prescribed. Comparisons and ties use the actually returned finite computed objective values, without an added tolerance. Record actual numerical dependency versions in study provenance. Repeat calls with identical normalized inputs and fixed recorded numerical dependencies are deterministic.

These arithmetic rules are not statistical uncertainty bounds. Source midpoint discretization, pupil/pixel quadrature, finite field, camera-estimation error, source-model mismatch, local-search limitations and observational nonidentifiability remain distinct. Q256/Q512 differences are measured sensitivity, not a continuum certificate or a new pass threshold.

Independent public-boundary expectations come from the pinned public mathematics. Any numerical reference must state its finite domain and account for node/weight, special-function, phase, summation and reference-T uncertainty. No guessed special-function margin or product-produced expected array is an independent oracle. This clause creates no new uncertainty certificate or mandatory recovery tolerance.

## 13. Completion evidence and limits

The public proof inventory includes all inherited input/representation/units/initialization obligations; all 47 coordinates and their exact order; paired signs/ties; no early sweep termination; domain infeasibility versus numerical failure; represented-coordinate versus parameter change; profile regeneration and carrier-dependent axial frequency; complete-image scoring; partial best/incumbent/frozen distinctions; record ownership/counters; held-out independence; deterministic repeated finite execution; and preservation of the old operation.

Fresh native A/B/C/D, full local verification, required platform/report/resource evidence and the active project gate remain governed by coordinator intake and existing policy. This contract changes none of them. Model/effort and missing cost/token measurements are not inferred from this document.

No inverse-operator or specimen source-basis change is included. The new calibration operation does not depend on a specimen solver. A specimen solver may accept explicit estimated illumination arrays and provenance without importing these result types; the end-to-end driver must still pass actual image-derived estimates, transfer the origin exactly once and preserve truth separation. That dependency split is not completion of a supplied-truth study.

The active named full-noisy advisory-percentage migration applies without weakening behavior/risk review, exact thirteen full-local phases, native reports or required platforms. Human numeric limits are not set; all prior attempts, corrections, failures, exposure and spending remain retained.
