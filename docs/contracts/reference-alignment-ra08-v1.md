# RA08 — finite-field objective and mathematical stopping

Version 1.0, 30 October 2026. The owner authorized RA07–RA15 without routine
approval requests. RA08 starts at completed RA07 commit
46e475fd33b2305b2d3856bedaf86a7488956e47. This is an additive, explicitly
discrete finite-field mode. Existing periodic spectral estimators and the
historical float32 finite-procedure fitter retain their interfaces and meaning.

## Public boundary

The development module `scripts.finite_field_reconstruction` supplies:

```python
operator = build_finite_field_operator(
    kernel=kernel, kernel_origin_zyx=origin,
    illumination=illumination, detector_crop_zyx=crop,
    input_taper=input_taper, padding_shape_zyx=padding,
    source_spacing_um_zyx=spacing,
)
prediction = finite_field_forward(operator, source)
backprojection = finite_field_adjoint(operator, detector)
score = finite_field_score(operator, source, images=images, regularization=alpha)
fit = solve_finite_field(
    operator, images=images, regularization=alpha, nonnegative=True,
    max_iterations=budget, absolute_tolerance=atol, relative_tolerance=rtol,
    output_taper=output_taper, output_zoom=zoom,
)
```

All builder/solver keywords shown are required; forward/adjoint take two
positional arguments; score takes operator/source positional. Return frozen
binding records `FiniteFieldOperator`, `FiniteFieldScore`, `FiniteFieldFit`.
Record direct construction is not an authenticated/validated public boundary.
No new package-root export, command-line workflow, camera calibration, pupil
model, illumination inference or automatic coupling to other fitters is added.
Caller-supplied sampled kernel and illumination are the complete forward model.
This isolates the declared boundary/objective from optical quadrature error.

## Discrete model, units and geometry

Kernel is a nonempty real 3D ndarray; its explicitly supplied integer origin is
inside its shape. Illumination is real `(R,N,Sz,Sy,Sx)` with all dimensions
positive. It supplies dimensionless signed multipliers (nonnegative physical
examples are preferred; signed algebraic controls remain valid). Source x has
shape S and is brightness per source voxel in a declared reference-flat-relative
signal gauge. Kernel values are detector signal per unit source brightness;
there is **no** implicit kernel normalization, voxel-volume factor, exposure
factor, throughput fit or sum/peak equalization. Spacing is positive finite
binary64 micrometres in z/y/x. Index zero fixes the common source/detector origin.

Crop is exactly three `(start,stop)` integer pairs with `0<=start<stop<=Saxis`.
It selects detector locations in this fixed box; it does not move or truncate
the source. For detector coordinate d in crop, exposure (r,n), and source s:

```
A(x)[r,n,d] = sum_s kernel[d-s+kernel_origin] * illumination[r,n,s] * x[s]
```

Kernel indices outside its declared support and all source indices outside S
are zero. The real adjoint is the transpose of this sum with the crop embedded
back at its original coordinates. Forward and adjoint are **unweighted**.
Real physical exterior outside a measured specimen field remains unknown;
zero exterior is an explicit model assumption, not inferred truth.

Padding is a triple of positive Python integers, each at least
`Saxis+Kaxis-1`. It is numerical workspace for full linear convolution and
cannot change the exact map. Extra padding introduces no source unknowns or
detector samples. Insufficient padding is invalid, including for zero kernels.
No scene enlargement, fitted alignment, modulo wrapping or kernel-origin shift
is permitted. Kernel may have even or singleton axes and asymmetric signed lags.

Input taper has exactly detector shape `(R,N,Dz,Dy,Dx)` and values in [0,1].
It weights the **residual**, including observed images. Zero weights omit those
observations from the objective, while the reported unweighted predictions and
residuals still contain them. Output taper has source shape S, values in [0,1],
and affects display only. Padding, crop, residual weighting and output display
are four separate operations.

Output zoom is a positive Python integer q. Apply output taper to x, then
trilinearly interpolate at source coordinates `i/q`,
`i=0..q*(Saxis-1)` on each axis. Singleton axes remain singleton. Return spacing
`source_spacing/q`; index zero stays fixed. This is nonperiodic interpolation
of the solved discrete source, with unchanged pointwise brightness and no sum
normalization. It creates no new unknowns or resolution evidence. q=1 returns
the tapered source. Predictions/objective/gradient/history use untapered x only.

## Objective, precision and estimator choices

Let M be the number of detector entries including zero-weight entries, P the
number of source voxels, W the diagonal input taper, y the supplied images.
For finite scalar alpha>=0 select precisely:

```
J(x) = ||W*(A*x-y)||2**2/(2*M) + alpha*||x||2**2/(2*P)
g(x) = A.T*(W**2*(A*x-y))/M + alpha*x/P
```

Alpha is a caller-declared ridge penalty in this numeric brightness gauge;
it is never inferred from truth/noise/residuals. `nonnegative=False` selects a
linear unconstrained ridge/least-squares estimator. True selects x>=0, a
different estimator when constraints are active, not linear Wiener recovery.
For alpha=0 a stationary least-squares minimizer is accepted; no numerical-rank,
unique-source or minimum-norm certificate is promised. At alpha>0 the objective
is strictly convex. Nullspace/source ambiguity and discretization floors remain
separate from observed residual, source error and stopping evidence.

Use float64 arithmetic and real finite convolution/adjoint, with FFT workspace
or equivalent finite sums. Do not round the iterate/gradient to float32. Begin
at exactly zero; no truth-derived warm start. The implementation may choose a
standard stable deterministic solver, without unbounded retry, but must retain
the actual accepted iterate history and independently observable g/J.

For unconstrained fits define optimality residual `rho=||g||inf`. For x>=0,
define k_i=g_i when x_i>0 and k_i=min(g_i,0) when x_i=0, and rho=||k||inf.
This is the Karush–Kuhn–Tucker stationarity condition for the declared convex
problem. Record rho0 at x=0 and stopping threshold `atol+rtol*rho0`. Tolerances
are finite nonnegative numeric scalars, at least one positive. The absolute
tolerance has gradient units in this declared numeric gauge; relative tolerance
is dimensionless. Convergence means rho<=threshold, including the zero initial
case. Objective decrease alone, solver library success flags, float stagnation,
or resource exhaustion never substitutes for that comparison.

max_iterations is a nonnegative Python integer: maximum accepted source updates,
not a convergence claim. The result has status exactly `converged`,
`iteration_limit` or `stagnation`; converged is true exactly for the first
status and only when the residual criterion holds. Check the criterion before
resource stops. A stagnating candidate above threshold is incomplete evidence.
No promise that any fixed budget suffices. Numerical failures are errors, not
converged fits. MemoryError and unrelated failures propagate.

## Records, validation and failures

`FiniteFieldOperator` fields: `kernel`, `kernel_origin_zyx`, `illumination`,
`detector_crop_zyx`, `input_taper`, `padding_shape_zyx`,
`source_spacing_um_zyx`. Builder arrays are copied native C-contiguous float64,
independent of caller, marked read-only; tuple metadata is immutable. Operations
do not mutate caller inputs/operator/state.

`FiniteFieldScore` fields: `predicted_images`, `residual_images`, `gradient`,
`data_objective`, `penalty_objective`, `total_objective`. Residual means Ax-y.

`FiniteFieldFit` fields: `source`, `output`, `output_spacing_um_zyx`,
`predicted_images`, `residual_images`, `gradient`, `data_objective`,
`penalty_objective`, `total_objective`, `objective_history`,
`optimality_history`, `optimality_residual`, `stopping_threshold`, `iterations`,
`status`, `converged`, `nonnegative`, `regularization`.
Histories are native float64 vectors, initial point plus each accepted update;
last values correspond to returned source. Scalar objectives/residual/threshold
are finite Python floats; flags bool, iterations int. All returned score/fit
arrays are independent mutable native C-contiguous float64, with no aliases
between fields/caller/calls. Forward/adjoint likewise return owned arrays.

Arrays at these boundaries are plain ndarray real i/u/f kinds, all available
widths/endians/layouts; source and converted values finite. Reject bool/complex,
masked/subclass/object/nonarray, incorrect shape or zero dimensions. Source,
images and adjoint detector allow either sign. Builder taper is nonnegative;
source supplied to score can be either sign regardless of a separate fit mode.
Tuple metadata require plain tuple, Python int components (not bool); spacing
components and scalar alpha/tolerances are nonboolean Python int/float converted
to float64, finite, with the bounds above. nonnegative must be Python bool.
Address-unrepresentable dimensions/arrays are arithmetic range failures; no
arbitrary practical-size cap. Positive strides, negative strides, read-only
inputs and exact-zero kernels/illumination/weights/data are valid.

Invalid declared inputs raise `SimreconError` code `invalid_finite_field_input`.
Unrepresentable required arithmetic/diagnostics/workspace raise
`finite_field_range`. Genuine numerical solver failure raises
`finite_field_solver_failure`. Catch numerical exceptions only at their actual
stage; do not swallow arbitrary exceptions or MemoryError. Handled arithmetic
must not emit RuntimeWarning. Preserve ambient NumPy error mode, warning filters,
inputs and write flags on both success and failure. Simultaneous-invalid
precedence and message prose are unspecified. Directly forged operator records
are outside this builder-authenticated contract.

Moderate controls (source/data counts <=256, kernel abs<=1, illumination abs<=2,
images abs<=16, spacing in [0.01,10] um, alpha in [0,1], and representable
required results) must evaluate correctly absent genuine dependency/resource
failure. This is an evaluation precision regime, not an input cap or finite
iteration guarantee. A independently derives tolerances from binary64 epsilon,
finite-sum dimensions/scale and conditioning before observing product results.
Use exactly solved well-conditioned tiny systems and ridge/constrained controls
for solution comparisons, with a chosen sufficient finite budget and observable
stationarity. Do not retune thresholds from observations.

## Scenario inventory and ownership

| ID | Distinct obligation / credible wrong outcome |
|---|---|
| F01 | Additive module/records; old periodic and historical finite APIs retained |
| F02 | Exterior-zero finite sum, asymmetric/even origins and real crop adjoint |
| F03 | Corner/boundary emitters versus interior; periodic prediction differs for same source |
| F04 | Fixed source box/crop and padding independence, no wrap/scene enlargement |
| F05 | Input residual taper weights both data/model and appears squared in gradient |
| F06 | Declared brightness/kernel/illumination scaling and no hidden normalization |
| F07 | Observable objective/gradient and finite-difference/direct normal-system controls |
| F08 | Exact unconstrained/ridge tiny systems, alpha zero/rank/null/zero-map outcomes |
| F09 | Exact active/nonactive nonnegativity systems and estimator difference |
| F10 | Stationarity threshold/history/initial zero and independently observed residual |
| F11 | Iteration/stagnation stops are not mathematical convergence; finite resource bounds |
| F12 | Output-only taper/trilinear zoom/spacing and fixed-center coordinates |
| F13 | Array grammar/layout/ownership/state preservation and paired permitted positives |
| F14 | Geometry/index/crop/padding/scalar/shape rejection boundaries and positive controls |
| F15 | Operational nonfinite/range/failure distinctions and unrelated failures |
| F16 | Native float64 precision; independent source/null/discretization reporting limits |

A owns `tests/test_reference_alignment_ra08.py` and
`tests/reference_alignment_ra08_fixture.py`, plus independent pre-observation
comparison inputs/expected outputs under `artifacts/ra08/figure-reference-1`.
No legacy oracle. B independently reviews exact tests/fixtures/oracles and
omissions, including legitimate positive inputs and history/convergence claims.
Read only this contract, AGENTS, narrow PROJECT architecture/environment/
coverage/model paragraphs, named role/test-audit skills and lesson format guide.
Do not read implementation, predecessor states/reviews, histories/conversations,
coverage maps or existing lessons. Source-free diagnostics must qualify first.

C owns only new `scripts/finite_field_reconstruction.py`. No frozen tests,
fixtures, expected arrays, snapshots, checks/dependencies/discovery/coverage,
skills/policy or other runtime edits. Coordinator owns contract/task/PROJECT,
usage/report/figure observation/render driver, evidence/accounting, packets and
unique lessons. Fresh native A/B/C/D use gpt-6.1-sol/high, optional memories and
multi_agent disabled. Coordinator launches; roles do not delegate.

Coverage inherits PROJECT approved behavior and independent risk review, with
percentages advisory and no selected threshold. Complete same-run native owned
src/scripts, never-imported and subprocess global/package/file integers and
JSON/HTML on local/Ubuntu24.04/macOS15 remain binding; no exclusions/gate changes.
Focused: accepted RA08 tests plus `tests/test_simulation_inverse_operator.py`,
`tests/test_image_only_specimen_fit.py`,
`tests/test_simulation_reconstruction_resources.py`.
Exact clean candidate canonical `make verify` and fresh D precede regular PR
against `codex/reference-alignment-ra07-fractional`; both original hosted proofs,
actual preservation-aware cleanup and fresh readiness acceptance precede the
single RA09 own-worktree successor. No merge, release, RA16 or unrelated message.

All failed launches/checks, diagnoses, reviews/corrections and prior ancestry
charges remain in sole ignored `artifacts/ra08/evidence-accounting-detail.json`;
Current state is `artifacts/ra08/current-state.json`. Numeric human limits are
not set. Unknown coordinator/provider/served/cost measurements stay unknown.
Coordinator inventories only RA08-created scratch, preserves original evidence,
links/referents/ancestors, environments/Python pins and real caches at required
paths, and closes owned processes. Actual destructive scope receives its own
high-risk contract/roles/checks; no predecessor cleanup or replay follows.
