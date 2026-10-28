# Image-only small calibration pilot v1

Version1.0. Adopted concrete contract under the authorized full noisy simulation and “Images only” choice. This is model-conditioned illumination/source inference with a fixed clear pupil. It supplies no empirical pupil recovery, full-run result, uniqueness, confidence interval or recovery-accuracy promise. Human numeric budgets are not set.

## Boundary and ownership

`scripts/image_only_calibration_pilot.py` exposes:

```python
fit_small_pilot(
    central_counts, *,
    structured_counts, heldout_counts,
    camera_estimate, origin_um_zyx,
) -> CalibrationPilotResult
```

No package export, command-line interface, generator, seed, persistence or full-shape resource probe is added. C owns only this runtime module. A owns `tests/test_image_only_calibration_pilot.py` and optional `tests/image_only_calibration_pilot_fixture.py`. Coordinator owns contracts, packets, acquisition/evaluation, provenance and resource execution. Fresh A/B/C/D, full local verification and inherited 100% gates remain binding.

Inputs are raw counts: central shape N=(Z,Y,X), structured shape (3,9,*N), held-out shape (3,5,*N). N is inferred; axes are nonempty and physical side lengths must each be at least 0.100 µm. The selected acquisition is N=(8,32,32); smaller legal shapes permit public-boundary controls. All three are plain ndarray kinds i/u/f, with finite original and normalized float64 values. Accept signed values, endian/strided/Fortran/read-only storage and conversion rounding; reject bool/complex/object/subclasses/nonarrays. Snapshot normalized inputs.

`camera_estimate` is a public ScalarCameraEstimate. Validate/snapshot its consumed fields: plain native float64 means_counts shape (3,), finite; contrast_counts a finite plain built-in int/float excluding bool; source a nonblank string. Other fields, including estimated physical gain, are not used. Direct construction authenticates nothing. Origin is a length-three tuple of finite plain built-in int/float values excluding bool; it labels the box corner. Fit coordinates are local to that corner.

Fixed known settings: D=(0.125,0.080,0.080) µm, f=(8,8,8), radius a=0.050 µm, excitation/emission 0.488/0.525 µm, n=1.515, detection NA=1.4, clear pupil, pixels=(2,2). Nominal illumination NA=1.2 and orientation angles (0,π/3,2π/3) initialize q=(NA/λex)(sin ω,cos ω). Commands are 2πj/5 for j=0..4, then π/5,3π/5,7π/5,9π/5. All actual carriers/phases/powers remain unknown.

## Gauge, source and objective

Let b=means_counts[1], d=contrast_counts. If d<=0 return normalization_unavailable, without division. Otherwise correct training pixels as Y=(C−b)/d, preserving signed values and background shot noise. Defer held-out correction/residual arithmetic until after freeze. This is exactly the camera contract’s reference-flat-relative affine relation; no true gain, extra scale or fitted intercept enters.

Each candidate has three complete nonoverlapping spheres inside the finite box. Centers obey a<=c<=N*D−a and pair distances >=2a. Call make_sources with one sphere of brightness exactly one electron, using its prescribed closed midpoint membership and rounded 1/K weights. Call expected_images on that electron-valued array. Dividing its electron prediction by one electron defines dimensionless R_l. Predict μ=Σ_l B_l R_l, B_l>=0 in reference-flat-relative units. Record occupied counts and stored one-electron masses; exact stored mass conservation is not promised. Never pass relative-unit brightness under the source_e electron label.

Repeat calls are deterministic for identical normalized inputs and recorded dependency versions; no cross-version bitwise promise. Use the complete approved optics equation, source-minus-focus sign, all source sites, pupil nodes, pixel samples and tails. Central-only illumination uses amplitudes (1,0,0). Structured amplitudes are nonnegative with squared sum one. The optics arithmetic allowance remains unchanged.

At Q=128, minimize F=Σ_training(Y−μ)²/(2M), M=28*Z*Y*X. Accumulate direct float64 residual squares over complete images. No masks, fitting windows, freely fitted response images or clipping. Candidate-derived physical caching is permitted only when it preserves these predictions.

Phases ψ are anchored at origin_um_zyx: θ=2πq·r_local,yx+ψ. Signed continuous q satisfies |q|<=n/λex and updates κ=n/λex−sqrt((n/λex)²−|q|²). No bin rounding/truth-centered bounds. Later transfer uses ψ_spec=wrap(ψ_cal+2π q_hat·(o_spec−o_cal)_yx), first five commands only. Bead permutations, phase wrapping, combined side-exchange/carrier-reversal and occupancy-equivalent centers remain alternatives.

## Exact observation-only initialization

Smooth corrected central Y with scipy.ndimage.gaussian_filter, sigma=(1,1,1), order=0, radius=4, mode="constant", cval=0.0, output=float64; record SciPy version. This selects the normalized finite nine-tap Gaussian per axis and zero exterior for initialization only. No preclipping occurs.

Select three peaks sequentially: highest strictly positive unsuppressed smoothed sample; ties by lexicographic z,y,x. After selection suppress all detector-center locations within <=0.5 µm Euclidean distance of that selected sample. No local-maximum test is added.

At each peak take the unsmoothed central window ±2 z and ±3 y/x indices, clipped to the array. Weights are max(Y,0). Zero total weight fails initialization. Compute its physical detector-center weighted centroid, then componentwise clamp to [a,u], where u is the largest float64 not exceeding the exact normalized-input value N*D−a. This inward rounding preserves make_sources containment; ordinary rounded subtraction must not put a center outside the box. Record window clipping/overlap and centroid clamping. This clamps only an initial guess; no source sphere is clipped. After all three, any overlap fails initialization; no separation repair or further peak search.

For each sphere initialize B_start as the strictly positive maximum unsmoothed Y in its centroid window divided by the strictly positive maximum complete central-only unit-response image. Unusable peaks/responses fail initialization. Start q nominal, ψ equal to command guesses at the calibration origin, and amplitudes (1,1,1)/sqrt(3). No second start or truth fallback.

## Finite search, freeze and validation

There are 47 unknowns: centers 9, brightnesses 3, carriers 6, phases 27, amplitude angles 2. At fixed profiles optimize 38 coordinates in this order: three B/B_start; γ/(π/2),η/(π/2); three pairs ρ/k0,ω/π; row-major ψ/(2π). Bounds respectively [0,100], [0,1], [0,1], ([0,1],[-1,1]) and [-1,1]. Set a0=cos γ,a+=sin γ cos η,a−=sin γ sin η; q=ρ(sin ω,cos ω). Exact angle endpoints denote exact zero beams. Check represented q against the optics exact-real domain before evaluation: an inadmissible represented carrier is an infeasible attempt, optimizer sentinel +infinity, trace value None, never a successful image or silently clipped carrier. Initial γ=acos(1/sqrt(3)),η=π/4.

Score the initial candidate once. Use installed scipy.optimize.minimize(method="Powell"), maxfev=100,maxiter=4,xtol=ftol=1e−3 with these bounds. Independently count objective calls. Keep the strictly best successfully scored candidate, including intermediate calls; an unscored optimizer return is not a candidate. Record status/message/nfev/nit. A limit is budget_limited, not convergence.

Then poll centers once, bead order 1..3 and axes z,y,x, negative then positive D/8 moves. For each coordinate form both trials from its pre-coordinate incumbent. Reject infeasible trials without optics work; score feasible trials with regenerated profiles. Choose a trial only if strictly below the pre-coordinate cost; best-trial ties choose the first. Otherwise retain incumbent. At most 18 attempts. Optical parameters stay fixed during polling.

Freeze the final Q128 incumbent. Rescore that exact candidate at Q256 and Q512, without fitting or selecting another candidate. Then predict held-out first-five commands at Q512 and compute signed residual mean and root-mean-square per orientation/command. Held-out values never enter initialization, search, selection or stopping. At most 121 training scores: 1+100+18+2; infeasible attempts are separately counted.

## Result and failures

Frozen-binding PilotCandidate contains owned writable native float64 arrays: centers_um_zyx (3,3), brightness_relative (3,), carriers_yx_per_um (3,2), phases_rad (3,9), beam_amplitudes (3,), plus occupied_counts tuple and stored_unit_masses_e (3,).

Frozen-binding CalibrationPilotResult contains exactly:
status, stage, message, failure_code; detector_shape_zyx, origin_um_zyx, camera_source, blank_counts, contrast_counts; initial_candidate and frozen_candidate (or None); objective_trace; optimizer_status/message/nfev/nit (or None); center_attempts; training_objectives_q128_q256_q512 (entries float or None); heldout_prediction (shape (3,5,*N) or None); heldout_residual_mean and heldout_residual_rms ((3,5) or None).

Trace entries identify stage, Q, scored candidate, objective or None, and outcome. Center attempts identify bead/axis/sign and infeasible/scored outcome. Trace-derived counts are authoritative; optimizer counts remain separately reported. No raw archive/truth is returned. All output arrays are C-contiguous, independent of callers/other calls; candidate/trace snapshots are independent.

Status is completed_local, completed_budget_limited, normalization_unavailable, initialization_failed or numerical_incomplete. Completed requires both refined scores and held-out output. Incomplete results preserve only actually available scored records; missing fields are None. A failed later refinement never becomes a fabricated successful prediction.

Invalid input raises SimreconError invalid_image_only_calibration_pilot; ordinary binding TypeError remains. Known source/optics range failures return numerical_incomplete with stage and unchanged failure_code; own nonfinite correction/centroid/brightness/loss arithmetic uses image_only_calibration_pilot_range. failure_code is otherwise None. Do not clip or retry. Other dependency/domain errors, unrelated exceptions/warnings and actual MemoryError propagate unchanged. Preserve inputs, global RNG, NumPy and warning policy; locally contain only expected own arithmetic warnings.

The operation has no wall-clock cutoff or resource guarantee. Coordinator may impose the proposed 10-minute external pilot timeout; termination is incomplete execution without a returned successful result. Full-shape cost probes are subsequent separately recorded work.

## Independent proof

Baseline800bf3c9bb9b5d353564bc93fd98dd20f01d773b is complete with local and both-platform evidence; the task record binds named ownership. Known acquisition stationarity, common dose and known registration remain explicit synthetic assumptions. Truth/noiseless means/seeds stay evaluator-only until parameters and held-out predictions are frozen.

Independent tests target finite-sum/unit-response units, whole-image loss and signed tails, exact initialization boundaries/ties/clamping/failure, rerasterized centers, bounds/accounting, phase anchors, held-out independence and truthful incomplete outcomes. Initially passing tests remain valid. No recovery threshold, test-only production seam, relaxed gate or inverse-grid substitution follows.

## Binding representation and outcome details

This section resolves record and numerical details for the adopted boundary. It controls any ambiguous shorthand above. Mean predictions inherit simulation-optics-v1's finite-equation 1e-5 unilluminated-peak allowance. Own corrections, centroid reductions, residuals and objectives use float64 with no prescribed reduction order; ordinary roundoff/underflow is allowed. They do not add a continuum or recovery accuracy guarantee. Independent tests derive meaningful finite-case allowances and distinguish wrong units, signed observations, masks and lost terms. A concrete nonfinite required arithmetic stage is numerical_incomplete. Stored represented amplitudes need not have an exactly unit floating-point sum of squares: use the stated angle parameterization and existing optics' S normalization. Exact angle endpoints map the corresponding beams to exact zero.

All four result records are exported from this script module, with frozen bindings. Direct construction adds no validation promise:
- PilotCandidate has exactly centers_um_zyx, brightness_relative, carriers_yx_per_um, phases_rad, beam_amplitudes, occupied_counts and stored_unit_masses_e, as specified above.
- PilotScore has exactly stage, pupil_order, candidate, objective and outcome. stage is initial, optimizer, center or refinement. outcome is scored, infeasible or numerical_incomplete. candidate is an independent PilotCandidate snapshot for a successful score, otherwise None; objective is a finite nonnegative Python float for scored, otherwise None. Every objective attempt has a record, including infeasible optimizer calls and required failed refinement attempts. These records promise no parameter snapshot for an unsuccessful trial. Record initial and optimizer/center scores at Q128, then refinement scores Q256/Q512.
- PilotCenterAttempt has exactly bead_index (0..2), axis_index (0..2, z/y/x), sign (-1 or +1) and outcome (infeasible or scored or numerical_incomplete). It records each attempted poll in order, including those needing no optics call. Retain both feasible same-coordinate trial scores in negative-then-positive order and decide after both, using their pre-coordinate incumbent.
- CalibrationPilotResult fields are exactly status, stage, message, failure_code, detector_shape_zyx, origin_um_zyx, camera_source, blank_counts, contrast_counts, initial_candidate, frozen_candidate, objective_trace, optimizer_status, optimizer_message, optimizer_nfev, optimizer_nit, center_attempts, training_objectives_q128_q256_q512, heldout_prediction, heldout_residual_mean and heldout_residual_rms.

objective_trace and center_attempts are tuples of their records; training_objectives_q128_q256_q512 is a length-three tuple. The Q128 entry is the frozen incumbent's score, not the initial score. All consumed camera/origin fields are snapshotted. origin_um_zyx stores the normalized float64 values as Python floats. Messages identify the relevant stage; exact diagnostic prose and invalid-input precedence are unspecified. Array ownership includes independence between candidates, trace entries, initial/frozen candidates and all other output arrays, besides independence from callers/other calls.

A successful Powell result continues as completed_local. An evaluation/iteration stop continues through center polling/refinement/held-out prediction and returns completed_budget_limited. Any other unsuccessful Powell termination returns numerical_incomplete at optimizer, code image_only_calibration_pilot_optimizer; preserve only actually scored data and its original status/message. Other stages are input_normalization, normalization, initialization, initial, optimizer, center, refinement_q256, refinement_q512, heldout or complete as applicable. Nonpositive camera contrast returns normalization_unavailable at normalization with no candidate/trace/optimizer/poll/prediction; valid input with missing three positive peaks, zero centroid weight, overlapping initialized centers, or unusable initial central response/brightness returns initialization_failed. These ordinary information outcomes have failure_code None. Required failures retain only available fields; absent arrays/candidates/optimizer fields are None, absent traces/attempts empty tuples, unavailable objective entries None. Do not treat a negative or nonfinite own computed loss as successful. Known source/optics range codes propagate as failure_code of numerical_incomplete; other SimreconError codes and unrelated exceptions propagate unchanged.

No fitted phase/carrier/beam/source value, true camera coefficient, optical transfer array, seed or noiseless observation is an input. The input camera record is explicitly estimated: an estimator cannot authenticate its provenance, so the experiment's separately retained generation/fit boundary supplies that evidence. Changing held-out pixels cannot change initialization, training attempts, selected candidate, refined scores or optimizer metadata; only held-out outputs and a possible late held-out numerical failure may change. Known origin is metadata, not an estimated registration; the local-box fit is invariant to its value except recorded origin and later documented phase transfer. No transfer API is added here.

Opened official expectation documentation on 2026-10-23: [Powell bounds and limits](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-powell.html), [Gaussian radius, boundary and dtype](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html). These render version1.18.0; actual locked version1.18.1 is recorded. The chosen explicit radius4, sigma1, constant-zero and float64 convention avoids unspecified defaults. No dependency update is authorized.
