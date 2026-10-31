# RA09 — continuous specimen overlap and relative complex gains

Version 1.0, 31 October 2026. Standing owner authority covers RA07–RA15.
Prerequisite is completed RA08 commit 02e77fae9a350b35143b0b40d304b980761696cd.
This additive operation fits one orientation of known-phase separated specimen
bands against fixed calibrated responses. It selects a finite comparison
estimator, not a continuous-optics likelihood or the RA08 zero-exterior inverse.

## Public operation

```python
from simrecon import fit_volume_overlap

result = fit_volume_overlap(
    bands, order_otf=calibration,
    initial_carriers_per_um=starts, carrier_bounds_per_um=bounds,
    difference_step_per_um=step, gradient_tolerance=gtol,
    rank_rtol=rank_rtol, max_evaluations=budget,
)
```

Only bands is positional. All keywords are required. Frozen binding records are
`VolumeOverlapFit` and `VolumeOverlapCandidate`. One fit returns every supplied
start in caller order, including duplicates and unsuccessful local attempts.
It never selects a global or physical winner. There is no file I/O, phase-step
fit, brightness fit, pupil fit, motion fit or automatic reconstruction.
Nominal starts and bounds must come from declared acquisition/search metadata;
synthetic truth belongs only to independent evaluation after the fit is frozen.

`bands` is a plain ndarray, complex128 width, either endian, shape `(3,Z,Y,X)`,
all axes nonempty. Rows are spatial dc,c1,c2 from an already known-phase
separation, without an extra factor of two. Row dc must have exactly zero
imaginary components. Strided/Fortran/read-only arrays, signed dc, zero bands,
singleton and even/odd spatial axes are valid. Reject masked/subclass/nonarrays,
other dtype widths, wrong shape, nonfinite components and nonreal dc with
`invalid_volume_overlap_bands`. No Hermitian or physical-realizability check is
imposed on positive harmonics.

`order_otf` is one `VolumeOrderOtf`, validated and snapshotted in all seven fields
under the one-record rules of the public integer volume-recombination contract
on `(Z,Y,X)`. Arbitrary finite complex rows, including zeros and arbitrary
calibration phase gauges, remain valid. Do not normalize or apply origin twice.
Its spacing `(dz,dy,dx)` supplies micrometres; its opaque source is retained.

Starts is a plain real i/u/f ndarray `(T,2)`, T>=1; bounds is the same grammar
with shape `(2,2)`, rows `(lower_y,lower_x)` and `(upper_y,upper_x)`; step has
shape `(2,)`. Convert to owned native binary64 and require finite source and
converted values. Bounds allow equality; every start lies inside their closed
box. Steps are strictly positive, and each nonfixed axis must have a finite
representable positive displacement within its box from each endpoint. Signed,
zero and repeated carriers are valid. Carriers use y/x cycles per micrometre,
with zero axial component. No modulo reduction, snapping or truth initialization.
Invalid carrier/start/bounds grammar uses `invalid_volume_overlap_search`;
invalid step/tolerance/budget grammar uses `invalid_volume_overlap_controls`.
Gradient tolerance is a nonboolean real Python/NumPy scalar, finite and >=0;
rank_rtol is the same scalar grammar with `0<rank_rtol<1`. Budget is a positive
nonboolean Python/NumPy integer. No practical data-size, seed or iteration cap.
Expected conversion errors map at their input boundary; MemoryError propagates.

## Fixed nonwrapping overlap and finite transforms

Use native centered canonical bins `-floor(K/2)..ceil(K/2)-1`. Let M=Z*Y*X,
`L=(Z*dz,Y*dy,X*dx)`, and c=(Y*dy*k_y,X*dx*k_x). Converted binary64 spacings,
bounds and carriers mean their exact represented real numbers. Geometric
membership and interpolation endpoint decisions use those exact products and
rational ideal nodes, without a tolerance. No overflow of rounded field length
may silently change geometric membership.

For m=1,2, Q_m contains every native integer q such that `q+(0,m*c)` lies in the
closed native canonical hull for **every** carrier in the caller's box. Use
the extremal box corners; retain q in z/y/x lexicographic order. Q_m is fixed
throughout all starts and evaluations. It includes zero-transfer samples; no
adaptive support mask, inferred optical cutoff, extrapolation or wrapping.
Empty Q_m is an unavailable order, never an input error. A singleton lateral
axis can therefore make overlap empty for a nonzero search extent.

Let D0(q) be the normalized negative-exponent discrete Fourier transform of dc.
For positive m and any real detector-bin triple t, define the observation value
by the exact finite-window sum over the stored spatial harmonic:

```
Dm(t) = sum_n bands[m,n] * exp(-2*pi*i*sum_a(t_a*n_a/K_a)) / M
```

This finite trigonometric polynomial is the observation interpolation. It is
not Cartesian interpolation of the FFT coefficients. Use index-zero spatial
origin, all three axes, and bounded phase evaluation. At native integer t it
recovers the normalized DFT. Let I_m(t) be Cartesian complex linear
interpolation of the supplied positive transfer row m on its native ideal
nodes. At a node use that stored value; interpolate real/imaginary components
with identical weights. Singleton axes cover only zero. This transfer
interpolant and the observation sum are distinct. No physical reflection or
dependent negative-order duplication is needed: fit only the two positive
orders relative to dc.

At each candidate k and each q in Q_m:

```
t = q + (0,m*c)
X_m(q;k) = I_m(t) * D0(q)
Y_m(q;k) = E0(q) * Dm(t)
```

The fixed calibration gauge, source coordinate origin and relative harmonic
amplitude are retained once. The gain correction multiplies the nominal
positive order. At integer geometry these are the existing nonwrapping
volume-order-gain regression pairs restricted to Q_m. With a fixed integer
box Q_m is exactly that operation's complete overlap.

## One coupled normalized overlap objective

For each nonempty order with computed nonzero predictor and response norms:

```
u = X / norm(X); v = Y / norm(Y); h = sum(conj(u)*v)
gain = (norm(Y)/norm(X))*h
r = v - h*u
J_m = norm(r)**2
```

The complete carrier objective is `J=J_1+J_2`, not an independent carrier score
followed by a differently defined gain. Fit gains analytically at every carrier.
Each order has equal dimensionless weight. This declared normalization avoids
rewarding a candidate solely for reducing sampled response energy. It is not a
noise likelihood: candidate-dependent finite observation energy and errors in
both operands remain model limitations.

Append one marker coordinate to each order's complex r. For an informative
order it is zero. An unavailable order has zero ordinary residual coordinates
and marker 1, hence J_m=1. Empty overlap has `no_overlap`; computed predictor
norm zero has `zero_predictor` and gain None; computed response norm zero has
`zero_response`, gain 0j. In these cases coherence and relative residual are
None. When both norms are nonzero, h=0 is a valid `zero_correlation`, gain 0j,
coherence 0, relative residual 1. Otherwise status is `fitted`, coherence
abs(h), relative residual norm(r). Zero predictor takes precedence over zero
response. Empty overlap takes precedence over norms. There is no hidden
small-energy or fitted-gain cutoff. Unavailable markers prevent disappearing
orders from receiving an artificial perfect score. One informative order can
still constrain a carrier; absent orders remain reported.

## Local search and diagnostics

For each start, perform bounded local minimization of this profiled objective.
The solver algorithm and iteration sequence are not public semantics. Count
each carrier objective evaluation used by search, including seed evaluation,
against max_evaluations; reuse of exactly identical points is permitted. Never
exceed this per-start caller budget or retry automatically. Retain the
lowest-objective visited finite point (first on exact ties). Fixed boxes are
valid and require one evaluation. Return that point even on an iteration,
stagnation or budget stop. Search success alone establishes no stationarity.
Final fixed diagnostic evaluations below are outside the search budget and
are separately counted; they never become new search candidates.

At the retained point compute clipped one-sided secants of J, at distances
`min(step[a],distance_to_bound)` along each available +/- axis direction.
Ignore fixed or unavailable zero-displacement directions. The reported
`projected_gradient` is the maximum of zero and all **negative** feasible
directional secants (use positive displacement length). This is a finite-step
coordinate diagnostic, not an exact derivative or a mathematical/local/global
optimality certificate, especially at transfer interpolation knots.
`stationary` means only this metric <= gradient_tolerance.

Construct a real residual vector by concatenating real then imaginary
coordinates of each order's augmented r, in order 1 then 2. For each free axis,
the residual Jacobian column is the secant between the clipped negative and
positive points divided by their total displacement; use the available side
at a bound. A fixed axis has an exactly zero column. Return both singular
values of this real matrix (pad with zeros if necessary), and rank counted
by strict `s > rank_rtol*s_max`; an all-zero matrix has rank zero. This is
finite-step local carrier information after complex gain elimination, not
statistical confidence. It estimates no gain uncertainty. Real/imaginary
stacking and marker coordinates must match the objective.

Candidate status is `unavailable` when neither order is informative (including
zero_correlation as informative), otherwise `nonsmooth_diagnostics` if the
informative/unavailable classification of any order changes at any diagnostic
point, otherwise `information_deficient` when rank
is below the number of free carrier axes, otherwise
`finite_difference_stationary` when stationary, otherwise `evaluation_limit`
if the search budget was exhausted, otherwise `search_stopped`. Rank/availability
precedence does not discard budget/stop metadata. Fixed boxes have zero free
axes and no inferred carrier information. All candidates carry
`global_ambiguity="unresolved"`; no number of starts proves global uniqueness.
Aliases, duplicate starts and distinct local outcomes remain visible.

`VolumeOverlapFit` fields: candidates (tuple), overlap_bins (tuple of two owned
native int arrays `(len(Q_m),3)`), spacing_um (tuple), source (opaque label),
carrier_bounds_per_um (owned `(2,2)` array).
`VolumeOverlapCandidate` fields: initial_carrier_per_um (tuple), carrier_per_um
(tuple), gains (tuple complex-or-None), order_status (tuple), coherence (tuple
float-or-None), relative_residual (tuple float-or-None), objective (float),
projected_gradient (float), stationary (bool), information_singular_values
(owned float64 `(2,)` array), information_rank (int), status (str),
search_evaluations (int), diagnostic_evaluations (int), budget_exhausted (bool),
diagnostics_continuous (bool), predictor_log2_norm (tuple float-or-None),
response_log2_norm (tuple float-or-None),
global_ambiguity (str). Output arrays are mutable, independently owned snapshots;
record bindings are frozen. No output/call aliases caller buffers or later calls.

The log2 norms report each order's raw cross-weighted X/Y norm using separate
scale factors, without materializing overflowing squared energies. A computed
zero norm or empty overlap has None. These expose weak absolute information;
equal normalized weighting does not certify signal-to-noise. Unit penalties
at zero norms can be discontinuous. If diagnostics_continuous is false,
stationary must be false regardless of the secant metric; the returned
singular values/rank then have no valid local-information interpretation.

## Range, failure and meaningful success

Use float64/complex128 and component-scaled finite transforms, products, norms
and gain restoration. Scale operands before large sums/products; a complex
magnitude overflow is not component nonfiniteness. Restore gain components
separately when a ratio would overflow although the final components fit.
Underflow is permitted. Required converted/intermediate/output components must
be finite. Handled arithmetic/range failures use
`unrepresentable_volume_overlap`; numerical Fourier/linear-algebra/optimizer
dependency failures use `volume_overlap_numerical_failure`. Preserve unrelated
exceptions/warnings, MemoryError, caller arrays/layout/write flags, NumPy
error policy and warning filters. Emit no handled arithmetic RuntimeWarning.
Do not catch unrelated exceptions across the whole operation. Simultaneous
invalid-input precedence and prose are unspecified.

Mandatory moderate evaluation success: M<=125, T<=4, absolute band components
<=16, transfer components<=2, spacing in [1/4,4] micrometres, absolute carrier
bin bounds<=4, step in bin units in [1e-6,1/8], budget<=256, with every nonzero
norm after bounded operand scaling >=1e-8, and final components finite.
These are sufficient conditions, not rejection caps or a recovery promise.
Zero bands/transfers are valid and return unavailable diagnostics.

Independent noiseless identifiable controls use constant positive-order
transfers and pointwise phase-ramped common specimen bands. In that model
the finite DFT at q+m*c_true demodulates exactly; nonzero fixed overlap gives
the matching relative gains. A derives stored-input arithmetic allowances
before product observation from dimensions, eps, conditioning and nonzero norm
lower bounds. Local recovery controls predeclare a smooth informative basin,
nominal metadata starts and field-wide phase-error allowance; stationary
counterexamples and noise are reported without a universal recovery claim.
No post-output input, seed, tolerance, gain, phase or alignment fitting.

For general frequency-varying transfers, truncation/windowing and interpolation
need not commute with modulation. Thus this cross-weighted comparison is not
an exact arbitrary finite convolution likelihood. No claim of physical recovery
follows from zero residual, local rank, stationarity or a sole start. Validate
full-field phase prediction and independently generated/held-out data where
the declared model permits; report a nonconstant-transfer mismatch control.
Never infer finite exterior, raw-phase errors, absolute phase/brightness or
resolution from these diagnostics. The common calibration phase/gain gauge
and carrier-induced field-wide phase slope are different quantities.

## Scenario inventory, ownership and gate

| ID | Distinct observable obligation and credible wrong outcome |
|---|---|
| O01 | Additive required public bindings/records and compatibility |
| O02 | Separated-band grammar, real dc and paired legitimate array layouts |
| O03 | Complete fixed-response validation, arbitrary complex/zero rows and gauge |
| O04 | Search metadata/controls, closed/fixed boxes, duplicate/signed starts |
| O05 | Fixed all-box nonwrapping Q, exact endpoints, singleton/empty support |
| O06 | Normalized finite DFT evaluation, signs/order-two/index-zero origin |
| O07 | Cartesian complex transfer interpolation distinct from observation evaluation |
| O08 | Coupled normalized regression, gains once, no extra two or independent score |
| O09 | No-overlap/zero-predictor/zero-response/orthogonal information outcomes |
| O10 | Per-start bounded budget, best visited/first tie and independent diagnostic counts |
| O11 | Finite-step projected secants, boundary/fixed directions and honest status |
| O12 | Profiled real residual Jacobian, rank cutoff and information limitations |
| O13 | All starts/aliases/local outcomes, global ambiguity always unresolved |
| O14 | Integer-gain baseline, amplitude/phase gauge and zero-gain positives |
| O15 | Caller state, snapshots, output ownership/frozen bindings and repeated calls |
| O16 | Scaled arithmetic, mandatory moderate success, range vs dependency failures |
| O17 | Independent carrier/gain recovery and full-field phase prediction; noise and mismatch |
| O18 | Executed evidence/overlap plots and fixed-field phase maps with honest limits |

High-risk numerical/custom-oracle route: fresh native blind A, fresh blind B,
restricted C, fresh D, Sol/high; supported memory/delegation disabled. A owns
only `tests/test_reference_alignment_ra09.py` and
`tests/reference_alignment_ra09_fixture.py`, plus ignored own evidence. C owns
only `src/simrecon/volume_overlap.py` and additive exports in
`src/simrecon/__init__.py`. Frozen reviewed tests/fixtures, dependencies, gates,
workflows/discovery/coverage, delivery rules and unrelated APIs are excluded.
Coordinator owns this contract, task/PROJECT pointer, usage/report, numerical
figure driver, provenance, role packets, state/accounting and unique lessons.
A/B read only named public inputs and source-free diagnostics. No implementation,
history/conversations/Current state/coverage maps or existing lessons. No legacy
source/build/executable/copy/import/link is authorized. No Superpowers.

Approved behavior coverage and independent risk review apply; percentages are
advisory. Complete native SQLite/JSON/HTML file/package/global measurements,
never-imported/relevant subprocess scope and installed gates remain binding.
Focused RA09 tests plus existing volume-order-gain/carrier-diagnostics/selection
checks precede exact committed full-local 13-phase `make verify`, fresh D and
PR publication. Ubuntu24.04 and macOS15 each repeat the configured gate. Retain
same-run measurements, reader/wheel/source/version/base/lock/check/environment
identity and independently qualify original platform artifacts. Every PR has
actual figures near its plain-English summary and before the technical appendix.
Human numeric limits are not set; unavailable metering/cost is unknown.

One Current state: ignored `artifacts/ra09/current-state.json`; detailed ledger
links RA08/RA07 and ancestor charges without reset or double counting. Preserve
all predecessor evidence, environments/caches/pins and original incoming-link
referents/ancestors. RA08 cleanup authority is permanently consumed and cannot
be copied, replayed, reset, retried or altered. Coordinator inventories RA09's
own scratch/processes/references at completion; actual destructive cleanup
needs its own proper route and preservation proof. Verified preservation may
yield zero removal. Complete required checks/reviews/presentation/cleanup before
one RA10 successor chat in its own exact-baseline worktree. No merge/release,
unrelated external messages or RA16 authority.
