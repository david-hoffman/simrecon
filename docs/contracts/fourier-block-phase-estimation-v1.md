# Fourier-block execution for observable volume phase estimation v1

**Version 1.0. October 18, 2026.** Contract ID: FOURIER-BLOCK-PHASE. The owner's standing roadmap continuation authorizes this dependency-ready Phase 5 scalability slice above completed PR43. This changes numerical organization of an existing estimator. It adds no inferred physical quantity or public name.

## Public behavior preserved

`estimate_observable_volume_phases` and `ObservableVolumePhaseEstimate` retain the complete [observable-subspace contract](observable-volume-phase-estimation-v1.md) and inherited [fixed-transfer phase contract](phase-step-estimation-v1.md): required signature; accepted array, transfer, carrier and control representations; snapshots/nonmutation; normalization; represented phases; exact structural support H; full observation residual; minimum-norm real nuisance representative; global numerical rank cutoffs; full residual-dependent profile derivative; projected phase information; optimizer controls; termination precedence; error codes; record fields and independent mutable array ownership. No tolerance, regularization, support cleanup, positivity, command prior, gain fit or discarded observation row is added.

The existing full-space `estimate_volume_phases` remains unchanged. Existing scan and selection operations continue to call the observable estimator and preserve their contracts. Their public policies, independent per-row initialization, duplicates and aliases remain unchanged. Equivalent finite organization can change optimizer trajectories and final roundoff within the existing numerical allowances. There is no cross-backend bitwise or iteration-count equality promise.

The selected change is exact carrier-orbit block decomposition of the observable nuisance solve. Dense *block* algebra remains permitted; constructing the global dense specimen design or global spatial basis is no longer permitted for this observable path. Large coprime lateral orbits can still produce expensive blocks. This is a scalability foundation, not a claim that the full 512 x 512 x 64 raw workflow is ready.

## Partition and orthogonal coordinates

Use inherited K=(Nz,Ny,Nx), M=Nz*Ny*Nx, N exposures, ell=(0,ky,kx), L=2*N*M, normalized signed transfer F_m and observation y. Index frequencies modulo K; conversion to centered storage is only an indexing convention. Partition **all** K frequencies into disjoint smallest sets C_b closed under both maps

```text
j -> (j+ell) mod K
j -> (-j) mod K.
```

Carrier integers retain their original exact provenance; modular reduction is for indexing only. The sets depend on K and the declared carrier, not transfer magnitudes, observed signal, fitted phases, tolerance or numerical rank. A partition refined further by independently proved exact structural zeros is permitted, but it must preserve every coupling and the memory bound below. Merging distinct C_b into a global solve is not the selected execution strategy.

Within C_b retain exactly the inherited Hermitian support H. Let c_b=|C_b| and r_b=count(H in C_b), so sum(c_b)=M and sum(r_b)=r. Construct any real-orthonormal coordinates of its Hermitian Fourier subspace: each retained conjugate pair gives two real coordinates and each retained self-conjugate frequency gives one. For example, a pair can use Fourier coefficients (1,1)/sqrt(2) and (i,-i)/sqrt(2). A self-conjugate coordinate has a real coefficient 1. Basis ordering/signs are private. No full M by r spatial basis is needed. Coordinate transforms preserve the spatial Euclidean norm by the inherited unitary discrete Fourier transform.

Each output Fourier coordinate k receives only specimen coordinates k-m*ell, m=-2..2. Closure under shifts and conjugation puts these coordinates in the same C_b. Therefore row permutation and orthogonal real nuisance-coordinate change make B=AQ block diagonal, with B_b of shape (2*N*c_b,r_b). Each block retains all real and imaginary observation rows of all N exposures, including unsupported or unexplained data. This block identity follows from the contracted model; it is not an empirical support estimate.

## One global objective and cutoff

Factor each nonempty-column B_b with unregularized singular value decomposition (SVD), without normal equations. The full nuisance singular-value list is the descending multiset union of all block singular values, length r. Let sigma_max be its global maximum (zero for an empty/all-zero list). Use the **single global** cutoff

```text
tau = eps * L * sigma_max,   eps = 2**-52
retained singular direction iff sigma > tau.
```

Do not use block row counts, block-local maxima, independent relative cutoffs or local rank decisions. At an initially deficient global nuisance point, apply this same truncated pseudoinverse in every block and return inherited nuisance_rank_deficient diagnostics without an optimizer. One weak block can be discarded because another block sets the global scale. Exact structural support and numerical availability remain distinct.

For r_b=0, prediction is zero and residual is the block's complete observed y_b. It contributes to global residual normalizations and the full objective even though its phase derivative is zero. For r=0 retain the exact no_observable_specimen outcome and validation precedence. Rank-changing trial/final reevaluations return the initial candidate, as before. The required full nuisance rank is r; no requirement that individual phases have a nonsingular five-column design is introduced.

For each block use its same-point B_b, pseudoinverse and nuisance vector in

```text
D_b[:,p] = (B_b)_p v_b
P_b = I - B_b B_bplus
R_b[:,p] = -P_b D_b[:,p] - transpose(B_bplus) transpose((B_b)_p) residual_b
K_b = P_b D_b.
```

Implement these as applications; do not form a global projector. Assemble the full real residual, Jacobian R and projected information Kphi in the inherited observation order. Cross-block phase coupling is retained: there is **one** N-variable local optimizer using the global residual and analytic Jacobian. Do not optimize exposure phases independently per block, sum singular values, average local gradients, replace the off-model term or sum local phase ranks. Phase singular values/rank come from the assembled Kphi with the inherited global phase cutoff. The nuisance specimen is lifted to one full real z/y/x result in the same fixed calibration gauge, with no per-block renormalization or registration.

Native forward and inverse Fourier transforms used by this path share the inherited transform failure boundary: numerical FloatingPointError/OverflowError/arithmetic RuntimeWarning or unusable/nonfinite transform gives volume_phase_estimation_transform_failure. Inverse-transform roundoff must not introduce a physical complex specimen. A mathematically Hermitian lift is real; extract its real spatial representative within the inherited allowance, without projecting non-Hermitian calibration predictions. All other inherited numerical/conversion/unrelated-exception boundaries remain unchanged. This explicitly covers the newly used inverse transform; it does not broaden catches around unrelated code.

## Execution and evidence obligation

Let cmax=max(c_b). Materialized nuisance designs, factors and Fourier coordinate bases must be block-local. No global M by M identity, M by r spatial basis, L by r nuisance design/pseudoinverse or L by L projector may be created merely to partition it afterward. For several blocks, no cross-block dense zero padding is allowed. Block-local storage can be retained for a two-pass global cutoff and derivative assembly. With dense block algebra its leading numeric storage is O(N*M*cmax + N*N*M + M + r), rather than O(N*M*r + M*r) independent of block structure. The L by N residual Jacobian and information matrix remain allowed. Implementing an equivalent lower-memory exact organization is permitted. This is an algorithmic obligation, not a new arbitrary byte/time rejection rule, public test seam, execution cap or memory-error conversion.

Independently check the mathematical block equivalence on small grids against direct Fourier sums or spatial forward matrices built from the public model. Existing product estimator output is a comparison, never the sole expectation. Include multiple unequal block strengths, incomplete structural support, unsupported observed data, non-Hermitian zero-order transfer, off-model residuals, zero/weak transfers, even Nyquist/self-conjugate modes, singleton axes, zero and very large/aliased carriers, and carrier cycles crossing both lateral axes. Global-cutoff cases must distinguish the incorrect local-cutoff solve. Tight independent numerical checks must distinguish conjugate-pair normalization, shifts/signs, lifted minimum norm and the full profiled derivative/projected information. Apply the existing well-conditioned arithmetic envelope; derive tighter case-specific tolerances independently. Initially passing tests are valid. Do not manufacture red or synthetic finite dependency records.

Retain existing tests unchanged. A adds focused complementary public-entry tests; it maps the distinct gap beyond existing public-boundary proof. A/B may observe genuine public numerical dependency failures and real-call factorization arguments only where justified by an approved behavior/resource obligation; no private production seam or fixed call-count oracle is authorized. The existing raw finite-bead/calibration composition and scan/selection checks remain binding. Add a focused complete scan or selection composition witness showing this estimator path still supplies row diagnostics from independent starts.

C executes and records two independently generated observation groups: one small direct-model comparison with hidden specimen/phase evaluator truth and at least one off-model/availability control; one larger multi-block scaling witness. Use nonnegative independent real-space specimens/complex calibration examples where physically compatible, and label algebraic off-model cases. Actual phases and specimen truth stay evaluator-only; nominal commands initialize the fit. Record estimator/objective error separately from phase-truth error. The scaling witness holds lateral shape/carrier and N fixed while increasing axial extent at least twice, includes all five signed orders and nontrivial retained support, and reports actual process wall time and peak resident memory with native units, baseline handling, dtypes, shapes, block dimensions/counts and machine. Report observations without inventing a speedup or whole-volume feasibility claim. No numeric byte/time acceptance threshold is selected. Source-free blind diagnostics need not run resource subprocesses; C/D own their actual execution/assessment.

Retain producer bytes, inputs, expected/output arrays, raw measurements, actual generation timestamps/status/argv, dependencies, environment and candidate/dirty generation identities before/after. Original generation context stays original; a later clean candidate admission is separate. Changed scientific/test/fixture/guide/producer inputs require affected regeneration. Do not replace execution with metadata assertions or rewrite old observations.

## Obligation inventory

Each row groups requirements, not a scenario cap. A records distinct outcomes and equivalent examples; B independently audits omissions and legitimate alternatives.

| ID | Observable obligation and credible risk |
|---|---|
| F01 | Existing signature/records/validation/snapshots/ownership and unaffected full-space estimator |
| F02 | Exact all-axis conjugation and carrier-shift partition, huge/aliased/zero carrier and even/singleton geometry |
| F03 | Hermitian pair/self-conjugate dimensions, orthonormal real coordinates and lifted minimum-norm representative |
| F04 | Exact normalized structural support, weak versus zero/underflow and complete unsupported observation residual |
| F05 | Block-factorization equivalence, one global singular-value multiset and strict global cutoff across unequal blocks |
| F06 | Global deficiency/no-observable/rank-changed behavior and complete validation before early outcomes |
| F07 | Full residual-dependent derivative, global projected information/rank and one common phase optimizer |
| F08 | Non-Hermitian calibration, independent-step/gauge meaning, residual/imaginary/reality diagnostics and no physical-accuracy inference |
| F09 | Inherited scaling/range/warning/exception boundaries, including genuine forward/inverse transform failures |
| F10 | Block-local allocation strategy, no global dense precursor, honest multi-block process measurements without invented resource cap |
| F11 | Unchanged independent scan/selection semantics and raw-calibration public composition |
| F12 | Executed usage/two independent observation groups, signed comparisons, actual generation/input custody and explicit remaining limits |

## Ownership and gates

High-risk numerical/custom-oracle route: fresh native Sol/high A, fresh blind B, restricted fresh C and fresh independent D. Requested settings are not actual serving attribution. A owns only tests/test_fourier_block_phase_estimation.py and optional tests/fourier_block_phase_estimation_fixture.py plus ignored independent evidence. Existing tests/fixtures stay unchanged. C owns src/simrecon/_observable_volume_phase_estimation.py, new private src/simrecon/_fourier_block_phase.py, narrowly shared internals in src/simrecon/_volume_phase_estimation.py as needed without changing the full-space public estimator, docs/usage/fourier-block-phase-estimation.md and ignored actual producers/evidence. No new exports are required. C cannot edit reviewed or existing tests/fixtures, unrelated runtime, dependencies/lock, workflows/discovery/coverage, delivery/policy/skills or gate helpers. B/D are report-only. Coordinator owns contract/task/PROJECT/roadmap/report/presentation and unique lessons. Separately named bounded setup ownership and fresh independent acceptance precede changed harness use.

Inherit selected100%native Coverage.py executable-line/branch-destination targets globally/perpackage/perownedfile across all src/simrecon+scripts, never-imported/relevant subprocesses, zero exclusions/skips, independently local/Ubuntu24.04/macOS15, no union. Advisory project defaults grant no waiver. Exact clean canonical make verify/all13phases, complete native SQLite/JSON/HTML, same-run M25 and wheel/source/staticversion/lock/check/base/environment/executable/ignored-input proof precede fresh D and own stacked PR. Closed successful native CI and independently qualified original platform archives precede final readback and exactly one useful started successor. Human numeric limits are not set. Preserve every inherited/current root, review, correction, failed launch/check and unknown meter; cached/reasoning counters are included subsets. No reference C execution/build, merge/release, earlier-PR edits, unrelated messages or Superpowers.

Primary numerical conventions opened for this intake: [NumPy SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html), [NumPy multidimensional Fourier transform](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), [SciPy local least squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html). The block partition, preserved estimator and execution requirements are project definitions above.
