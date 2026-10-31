# RA10 — exposure phases in a fixed finite calibration gauge

Version 1.0, 31 October 2026. The standing owner instruction authorizes
RA07–RA15. Baseline is RA09 `3dc0b4133827f3da531404c39320197a944d7156`.
This additive phase-inference composition selects a shared-source finite model.
It estimates neither carrier nor responses, motion, pupil, brightness scaling,
camera parameters or calibration. It does not reuse a periodic nuisance model.

## Information premise and public operation

```python
from simrecon import fit_exposure_phases

result = fit_exposure_phases(
    images, order_kernels=kernels, kernel_origin_zyx=origin,
    source_shape_zyx=shape, detector_crop_zyx=crop,
    source_spacing_um_zyx=spacing, carrier_per_um_yx=carrier,
    exposure_covariance=covariance, fit_mask=mask,
    phases_rad=labels, mode=mode, initial_offsets_rad=starts,
    offset_bounds_rad=bounds, difference_step_rad=steps,
    source_rtol=source_rtol, phase_rank_rtol=phase_rtol,
    gradient_tolerance=gtol, max_evaluations=budget,
)
```

Only images is positional; all shown keywords are required. Frozen binding
records are `ExposurePhaseFit` and `ExposurePhaseCandidate`. This is one
orientation. One real source is shared across all exposures. Responses and
carrier must be fixed independently before this fit. Synthetic evaluator truth
cannot supply kernels, starts, bounds, source, masks, gauge or solver selection.
Caller-supplied calibration is a conditional scientific premise, not proof that
raw calibration images alone identify it.

Modes are exactly `known`, `common`, `independent`. In known mode labels are
actual supplied phases, for example independently measured monitor metadata;
there is no phase estimation or claim that commands are actual observations.
Otherwise labels are nominal commands and starts/bounds concern additive phase
offsets. No phase-monitor uncertainty model is inferred.

This boundary takes **explicit finite displacement kernels**, not a
`VolumeOrderOtf` disguised as such. Transforming sampled transfers into finite
kernels requires a separately declared convention; no automatic transform,
centering, interpolation or normalization is selected here. RA09's fixed-support
cross-weighted overlap comparison remains a different estimator. RA06 motivates
raw exposure covariance weighting; no diagonal separated-noise approximation
is substituted.

## Finite raw model and fixed gauge

Let source s have shape S, real entries of either sign, and index-zero positions
`r_s=(sz*dz,sy*dy,sx*dx)` in micrometres. Kernel shape K and its integer origin o
are explicit. Crop selects detector indices d inside S; it does not move source
coordinates. Outside K, all three kernels are zero. Outside S, source is zero.
For lateral carrier k in cycles/µm and fundamental phase phi in radians:

```
theta_s = 2*pi*(ky*sy*dy + kx*sx*dx)
A(phi)[p,d,s] = K0[d-s+o]
  + 2*Re(K1[d-s+o]*exp(i*(theta_s+phi[p])))
  + 2*Re(K2[d-s+o]*exp(2*i*(theta_s+phi[p])))
prediction[p,d] = sum_s A(phi)[p,d,s]*x[s]
```

K0 is exactly real. Complex positive-order kernels are arbitrary, including
zero; conjugate negative contributions appear exactly once in `2*Re`.
No modulo spatial wrapping, integer carrier snapping, Fourier interpolation,
extra factor of two, implicit voxel volume or fitted throughput is permitted.
Fractional, negative and zero carriers and asymmetric/even kernels are valid.
This exterior-zero sampled model is not a continuous-optics likelihood or
inference of the real exterior.

Index zero fixes phase origin before output. Calibration K_m is held fixed.
Changing K_m to `K_m*exp(-i*m*gamma)` together with phi to phi+gamma describes
equivalent predictions in another calibration gauge; the operation never makes
this change or zeros the first fitted phase. Per-exposure phases are modulo
2*pi; absent first order can leave pi aliases. A moved coordinate origin also
requires the corresponding carrier phase adjustment, never post-fit alignment.

In common mode Q=1 and `phi=labels+offset[0]`. In independent mode Q=N and
`phi=labels+offset`. In known mode Q=0 and `phi=labels`. Return these unwrapped
sums, without choosing a modulo representative. For reporting define
`common_offset_rad=offset[0]` and
`independent_deviations_rad=offset-offset[0]` in independent mode. Their first
element is zero; actual phi[0] need not be zero. Common mode deviations are an
N-vector of zeros. Known mode has common offset None and zero deviations.

Evaluate finite represented angles with bounded trigonometric arguments.
Input phase values, converted geometry and offsets denote their binary64
values; at moderate geometry ordinary binary64 arithmetic allowances apply.
Required phase sums/geometry/products that cannot be represented raise a range
error rather than silently changing coordinates. No universal large-angle
relative-accuracy guarantee is made.

## Fixed covariance, mask and profiled source estimator

Images shape is `(N,Dz,Dy,Dx)`, N>=1. Mask has detector spatial shape D and is
shared by all exposures. True selects training detector sites. False sites are
predicted using the same frozen source/phases, without fitting their data.
This common spatial mask prevents covariance whitening from leaking held-out
pixels into training. An all-false mask is valid and explicitly unavailable.

Covariance C is a strictly positive definite real symmetric N-by-N matrix in
the numeric image gauge. If `C=L*L.T` is its Cholesky factorization, whiten each
detector site's exposure vector and the corresponding rows of A by `L^-1`.
Keep every training site; no data-adaptive support or threshold is allowed.
Stack exposure-major whitened rows as B, data as b. Let M=N*count_true(mask).

At each phase candidate compute an SVD of B. Retain precisely singular values
`sigma > source_rtol*sigma_max`; if sigma_max=0 retain none. Use the truncated
Moore–Penrose inverse `x=B_plus*b`, the minimum norm solution in the retained
right-singular subspace. This selected cutoff estimator need not minimize over
discarded directions. There is no positivity constraint or source regularizer.
Return actual raw prediction and residual `prediction-images` over **all** D.
The single objective is `J=||B*x-b||^2/(2*M)` in covariance-weighted squared
signal units; no division by candidate-dependent prediction energy. If M=0,
return source zero, J=0, source rank zero and no phase information.
Source singular values are those of B, before normalization. Full objective
agreement is measured from raw finite sums and covariance, not a separator's
residual or the optimizer's cached loss. Multiplying images by a and C by a^2
(a positive) preserves weighted J and phases while multiplying source by a.

Five unconstrained coefficient images would permit `Y=X(phi)*Ccoef` and, for
any invertible five-frame X(psi), `Ccoef'=X(psi)^-1*Y`. Zero residual then
does not identify phases. This adapter restricts coefficients to the above
**one shared source and fixed kernels**. That restriction can add information,
but five frames, extra frames or full local rank alone prove no uniqueness.
Repeated exposures, absent harmonics and weak specimen/transfer information
remain legitimate cases. Report equivalent alternatives; never auto-select a
physical winner.

## Search, local stationarity and cutoff-conditional sensitivity

Starts shape `(T,Q)`, T>=1; bounds `(2,Q)` lower then upper; steps `(Q,)`.
In known mode require T=1 and empty Q dimensions. Closed equal bounds are
valid; every start is inside. All other modes preserve caller order, duplicates,
aliases and failed local attempts. No implicit truth seed, retry or winner.
Search is deterministic bounded local minimization of the same profiled J.
Each source/objective evaluation used by search counts toward the per-start
positive max_evaluations budget, including its seed. Exact-point caching is
allowed. Retain the lowest visited finite J, first on exact ties. Fixed boxes
and known mode require one search evaluation. Optimizer algorithm/sequence is
not public semantics. No fixed budget promises convergence.

At the retained point evaluate feasible +/- coordinate objective secants, using
the smaller of the supplied step and distance to the bound. Ignore fixed axes
and zero displacement. `projected_gradient` is max(0, negative feasible
directional secants), using positive displacement lengths. Count these as
`diagnostic_evaluations`, outside the search budget, and never use them to
replace the selected search point. `diagnostics_continuous` means every such
neighbor has the retained source rank. Rank agreement is necessary context,
not proof of differentiability. `stationary` is exactly continuity AND
projected_gradient<=gradient_tolerance. Known/no-free cases have metric zero
and continuity true. `search_status` is `known`, `fixed`, `stationary`,
`evaluation_limit` or `stopped`, with known/fixed first, then the independently
measured stationary criterion, budget exhausted, otherwise stopped.

Separately compute the raw phase sensitivity at the retained source:
`dmu/dphi_p = -2*Im(b1*exp(i*phi_p)+2*b2*exp(2i*phi_p))` in exposure p.
Map it to Q offset directions (sum for common), whiten/mask identically and
project away the retained source columns: `E=(I-Uret*Uret.T)*D/sqrt(M)`.
Include only nonfixed offset axes. Phase singular values are all singular
values of E, padded with zeros to free_parameter_count. Numerical phase rank
uses `s > phase_rank_rtol*s_max`, zero if max=0. This is conditional local
data-tangent sensitivity with the retained source subspace frozen at the
candidate; neither a Hessian nor the derivative of the truncated-profile
residual nor a calibrated uncertainty estimate. Discarded nonzero source
directions can still absorb phase changes in the unrestricted scientific
source model. Therefore `full_local_rank` does not establish even local
identifiability for that unrestricted model. The declared SVD cutoff is part
of this diagnostic's conditional meaning, not extra observational information.
Neither local nor global uniqueness follows. No source penalty counts as data.
Very small absolute singular values expose weak information even if relative
rank is full. `information_status` is `known` for known mode,
`no_training_data` if M=0, `no_free_parameters` for Q>0 with all bounds fixed,
otherwise `full_local_rank` or `rank_deficient` by comparison with free count.
`global_ambiguity` is always `unresolved` for inferred modes and `not_inferred`
for known mode, including full-rank/stationary fits.

## Records, validation, precision and failure boundaries

`ExposurePhaseFit` fields: `mode`, `input_phases_rad`, `carrier_per_um_yx`,
`source_spacing_um_zyx`, `fit_mask`, `candidates` (tuple in caller order).
Candidate fields: `initial_offsets_rad`, `offsets_rad`, `phases_rad`,
`common_offset_rad`, `independent_deviations_rad`, `source`, `predicted_images`,
`residual_images`, `objective`, `source_singular_values`, `source_rank`,
`phase_singular_values`, `phase_rank`, `free_parameter_count`,
`information_status`, `projected_gradient`, `diagnostics_continuous`,
`stationary`, `search_status`, `search_evaluations`, `diagnostic_evaluations`,
`global_ambiguity`. All output arrays are independent mutable native
C-contiguous float64 (fit_mask bool), with no aliases between fields, caller
or calls. Bindings are frozen. Scalar diagnostics are finite Python floats,
counts Python ints, flags Python bools. Metadata tuples are immutable.

Images/covariance/labels/starts/bounds/steps/carrier are plain real i/u/f
ndarrays, all available widths/endians/layouts, source and converted values
finite; no bool/object/complex/subclass/masked/nonarray. Kernels are plain
complex128 ndarray either endian `(3,Kz,Ky,Kx)`, all K positive, finite real
and imaginary components, row zero imaginary exactly zero. Zero/signed K0,
zero data, zero kernels and signed source are permitted. Source shape and
kernel origin are plain 3-tuples of nonboolean Python ints; shape positive,
origin within K. Crop is a plain tuple of three plain `(start,stop)` tuples
of Python ints, `0<=start<stop<=Saxis`; D equals stop-start. Spacing is a plain
3-tuple of nonboolean Python int/float, converted finite positive binary64.
Carrier shape `(2,)`; labels `(N,)`; covariance `(N,N)` exactly symmetric
after conversion, with numerically positive Cholesky factor. Mask is plain
bool ndarray of shape D. No practical shape, exposure or seed cap applies.

Bounds are ordered/closed, steps finite positive; each nonfixed axis requires
a representable positive step within the box from both endpoints. Rank
tolerances are nonboolean Python/NumPy real scalars with `0<value<1`;
gradient_tolerance is the same grammar finite >=0. Budget is nonboolean
Python/NumPy positive integer. Expected conversion exceptions map at the
input boundary. Invalid inputs raise `SimreconError` code
`invalid_exposure_phase_input`. Unrepresentable conversion arithmetic,
workspace, model, least-squares, objective or diagnostics use
`exposure_phase_range`; numerical Cholesky failure for invalid covariance is
input error, genuine SVD/optimizer dependency LinAlgError/numerical failures
use `exposure_phase_numerical_failure`. Catch numerical errors only in their
stages. Preserve MemoryError and unrelated exceptions/warnings, caller arrays,
write flags, NumPy error policy and warning filters. Handled arithmetic emits
no RuntimeWarning. Simultaneous-invalid precedence/prose are unspecified.

Float64/complex128 arithmetic is required. Moderate mandatory evaluation:
M<=256, source voxels<=64, N<=12, T<=4, kernel components<=2, image abs<=16,
spacing [1/4,4] µm, absolute carrier*field length<=4, absolute labels/offsets
<=16 rad, covariance eigenvalues [1/16,16], source/phase cutoff separated
from singular values by >=1e-8 times max, finite outputs, budget<=256.
These sufficient conditions are not input rejection caps or recovery promises.
A derives numerical allowances before product observations from epsilon,
finite-sum dimensions/scale, retained condition and cutoff margins. Outside
that regime, finite input does not guarantee representable required arithmetic.
Stored-input agreement is distinct from optimization/recovery accuracy. For
positive inference controls A predeclares a smooth informative basin, legitimate
command-derived initialization, budget and phase/prediction allowance justified
independently of product outputs. These controls establish only their stated
conditional recovery outcome, never convergence for every permitted input.
The predeclared positive-control phase and held-out prediction outcomes are
required for acceptance. Assertions conditional on recovery already happening
do not establish this obligation. Keep the named command-derived start and
budget fixed before product observations, and assert the declared outcome
without using truth to choose a returned candidate or a solver success flag.

## Scenarios, ownership, checks and evidence

| ID | Observable obligation / credible wrong outcome |
|---|---|
| P01 | Additive bindings, frozen records, known/common/independent semantics |
| P02 | Input grammar and paired permitted layouts/types/zeros/signed values |
| P03 | Explicit kernel/source/crop geometry and finite exterior; no wrapping |
| P04 | Fractional/signed carrier, index-zero gauge, complex order signs/factors |
| P05 | Covariance whitening, fixed common spatial mask, held-out isolation |
| P06 | Cutoff minimum-norm shared-source solve and full raw objective |
| P07 | Nominal command starts/bounds, fixed boxes, known monitor control |
| P08 | All starts/duplicates/aliases and bounded best-visited search |
| P09 | Secant metric, rank continuity, exact status and separate counts |
| P10 | Nuisance-projected local phase rank, weak absolute sensitivity/zero cases |
| P11 | Fixed gauge and common/independent offset decomposition; no alignment |
| P12 | Five-band ambiguity; redundant exposure information limits/alternatives |
| P13 | Owned snapshots/outputs and caller/ambient-state preservation |
| P14 | Invalid/range/numerical/unrelated failure classification and moderate success |
| P15 | Independent finite sums: known-phase, common-offset, independent recovery |
| P16 | No truth-selected starts; spatially held-out predictions, noise/mismatch limits |

Fresh native A/B/C/D use configured Sol/high, with supported memory/delegation
disabled. A owns only `tests/test_reference_alignment_ra10.py` and
`tests/reference_alignment_ra10_fixture.py`, plus ignored own evidence. C owns
only new `src/simrecon/exposure_phase.py` and additive exports in
`src/simrecon/__init__.py`. Existing periodic estimators, frozen tests/fixtures,
dependencies, workflows, discovery/coverage/gates and delivery policy are
excluded. Coordinator owns contract/task/PROJECT pointers, usage/report,
independent preparation/observation/render driver, provenance and unique lessons.
No legacy source/executable is used. No Superpowers.

A/B get only approved public inputs and source-free warnings/tracebacks and
subprocess diagnostics, retaining categories/messages/locations/status. No
implementation/history, coordinator handoff/state, coverage maps or existing
lessons. B gets exact A tests and sanitized results; fresh D reviews the exact
fully verified candidate before implementation lessons. Required focused check:
`uv run --locked pytest tests/test_reference_alignment_ra10.py
tests/test_volume_phase_estimation.py tests/test_observable_volume_phase_estimation.py
tests/test_fourier_block_phase_estimation.py`. Full exact-candidate `make verify
UV=/Users/davidhoffman/.local/bin/uv` precedes opening the one RA10 PR, stacked
on `codex/reference-alignment-ra09-overlap`. Ubuntu24.04/macOS15 independently
repeat and qualify full coverage, M25, version/wheel/reader/environment evidence.
Approved behavior and independent risk review apply; native percentages remain
advisory, no new metric threshold/exclusion/gate waiver. Human numeric limits
are not set; missing usage/cost/serving attribution is unknown.

Figures show command versus independently generated actual phases in this
predeclared gauge, known/common/independent prediction comparisons and limits.
For 3D retain fixed XY/XZ maxima and catalogue-center XY/XZ sections, physical
axes/aspect/µm, shared scales/signed differences and separately labelled
shape-normalized profiles. Fit each independent phase on training pixels and
predict disjoint masked pixels with source/phases frozen; a wholly withheld
exposure has no inferable independent phase absent external metadata.

Sole Current state is ignored `artifacts/ra10/current-state.json`. Inherit RA09
final readiness/accounting and ancestral charges without reset/double counting;
preserve originals, environment/Python pins and incoming link referents and
ancestors. Predecessor cleanup authority is consumed; excluded records remain
unread. Coordinator inventories only RA10-owned scratch/processes/dependencies
under `docs/operations/fixture-cleanup.md`; any destructive operation needs its
own route and proof, outside restricted science roles. Verified preservation
can remove zero objects. After all RA10 reviews/gates/figures/accounting/cleanup,
create exactly one authorized RA11 successor in its own managed worktree at
the final head. No merge/release, unrelated messages or RA16 authority.
