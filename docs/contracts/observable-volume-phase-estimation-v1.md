# Observable-subspace local volume phase estimation v1

**Version 1.0. October 17, 2026.** The owner's standing roadmap continuation and successor approval authorize one dependency-ready Phase 5 slice above completed PR40. This additive operation removes exactly structurally invisible real nuisance modes from the fixed-transfer local phase fit. It does not complete scalable execution or phases 7–9.

## Public boundary and inherited behavior

```python
from simrecon import ObservableVolumePhaseEstimate, estimate_observable_volume_phases

estimate = estimate_observable_volume_phases(
    images,
    order_otf=orders,
    carrier_bins_yx=(ky, kx),
    initial_phases_rad=nominal_commands,
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen/calibration pairing",
)
```

Only images is positional. All shown keywords are required; numbers are examples, not defaults. Units, single orientation/channel/time, phase/z/y/x array grammar, N>=5, snapshot/ownership/nonmutation rules, VolumeOrderOtf validation, canonical frequencies, integer carrier grammar, controls, source, normalized stored-input model, native phase representation, signed order reflection, Fourier realification, numerical precision, dependency boundaries and stable error codes are exactly those in [fixed-transfer local phase estimation](phase-step-estimation-v1.md), except for the explicit reduced nuisance domain, availability outcomes and result additions below. Signed observations, non-Hermitian zero order, zero/weak transfer, all layouts/endians and huge finite phases/carriers remain permitted. Validate all inputs and all transfer samples before an unavailable outcome. Existing estimate_volume_phases and VolumePhaseEstimate retain their entire prior contract.

The carrier, complex calibration gains, grid, reference gauge and all corrections remain supplied. All exposure phases, including their common offset in that fixed calibration gauge, are locally fitted. Initial commands initialize one continuous solve. No positivity, support guessed from observations, regularization, fitted gain, drift, carrier refinement, global uniqueness or physical accuracy claim applies. Dense execution remains permitted without a practical large-volume guarantee.

## Exact structural support

Use the inherited normalized observation d, normalized signed transfer rows F_m, m=-2,-1,0,1,2, integer carrier ell=(0,ky,kx), unitary negative-exponent discrete Fourier transform U, grid K and voxel count M. Work with modular frequency coordinates on every axis; centered array storage follows the inherited canonical detector bins. Negative frequencies include modular even Nyquist behavior.

For a specimen Fourier coordinate j, define

```text
V(j) = any_m (Re F_m((j+m*ell) mod K) != 0
             or Im F_m((j+m*ell) mod K) != 0)
H(j) = V(j) or V((-j) mod K)
r = count(H)
```

Comparisons use normalized stored binary64 components, including their signed-zero/underflow results. No magnitude, tolerance, physical support inference or SVD threshold defines H. Nonzero weak coefficients remain structurally visible even if the later numerical rank cutoff discards their information. Carrier shifts are reduced for indexing while the original integers remain in the result. F_-m is the inherited conjugated modular reflection of the positive row. Non-Hermitian F0 is retained without symmetrization.

H is invariant under modular negation. The real observable subspace S is all real specimen arrays u for which (Uu)(j)=0 outside H. A conjugate pair contributes two real dimensions; a self-conjugate frequency, including a Nyquist corner, contributes one. Thus dim(S)=r exactly. Let Q have any mathematically orthonormal real columns spanning S. Its signs/order or other orthogonal change of coordinates are not public results. A Fourier cosine/sine orbit basis is one valid construction. Keep every original real/imaginary observation row, including unexplained signal at unsupported modes. Constructing Q by thresholding sampled A(phi), fitting phases, normal equations or a tolerance-based stack of operators is not the selected structural reduction.

Reason: the signed order map sends specimen frequency j only to j+m*ell, with coefficient F_m(j+m*ell). A real specimen ties j and -j by complex conjugation. Its common kernel over all five signed order maps therefore consists precisely of the excluded Hermitian orbits. The five represented basis functions [1,c,s,c*c-s*s,(2*c)*s] span five coefficient dimensions over permitted phase values (for example a nonsingular well-separated five-phase design), so their coefficients remain distinct; this uses neither exact unit-modulus phasors nor a design-rank requirement on initial commands. Cancellation at particular phases does not justify deleting a retained orbit. In exact arithmetic, A(phi) = A(phi) Q transpose(Q) for every phase vector. Consequently the full and reduced residual minima agree; S supplies the minimum Euclidean norm full-space representative of each observable equivalence class. These are algebraic model statements, not guarantees about roundoff-level zeros or physical optical support.

## Reduced objective, derivatives and ranks

Set B(phi)=A(phi)Q, of shape (L,r), L=2*N*M, with the inherited realified data y. Solve

```text
v_star(phi) = argmin_v ||y-B(phi)*v||_2
u_star(phi) = Q*v_star(phi)
residual = y-B(phi)*v_star(phi)
J(phi) = 0.5*||residual||_2**2
```

Use unregularized SVD. Numerical nuisance rank counts singular values strictly greater than eps*max(L,r)*sigma_max; equality is deficient. Since L=2*N*M and r<=M, max(L,r)=L: reduction does not change the inherited cutoff multiplier. Residual normalizations also retain M, never r. For r>0 there are r reported nuisance singular values in descending order. At deficient initial B use the inherited truncated minimum-norm pseudoinverse, compute availability diagnostics, return nuisance_rank_deficient and run no optimizer. Invisible modes no longer force deficiency: the required full numerical nuisance rank is r, not M. If the cutoff discards nonzero singular values, this initial truncated availability result need not minimize the exact stored-input objective; exact reduction equivalence does not change that limitation.

For full numerical rank r use the inherited SciPy least_squares method, controls, analytic residual Jacobian, continuous start and candidate canonical reevaluation exactly. Replace A by B, Aplus by Bplus and A_p by B_p=A_p Q in all formulas:

```text
D[:,p] = B_p*v_star
Pperp = I-B*Bplus
R[:,p] = -Pperp*D[:,p] - transpose(Bplus)*transpose(B_p)*residual
Kphi = Pperp*D
```

The residual-dependent term is required. At an initially deficient point compute the same algebraic diagnostics from the same truncated Bplus and v. This supplies no differentiability or identifiability claim at a rank transition. If a trial or returned canonical reevaluation loses full rank r, return the initial candidate and diagnostics with rank_changed. Otherwise the inherited stationary/evaluation_limit/stagnated classification applies. Phase-information cutoff retains eps*max(L,N)*sigma_max; phase-design rank and global_ambiguity='unassessed' retain their prior meanings. Full reduced nuisance rank or low residual establishes no informative phase rank, minimum, unique basin or physical recovery.

For r=0, report no_observable_specimen and return the canonical initial phases without an optimizer. Define u=0, prediction=0, residual=y, nuisance rank0 and empty nuisance singular values, phase rank0 and N zero phase singular values, gradient0 and imaginary RMS0. Residual normalization, phase-design rank and other ordinary metadata follow their inherited formulas. This explicit unavailable outcome takes precedence over stationary. Actual residual/Jacobian evaluation counts remain observed counts; do not fabricate dependency calls or solver records.

## Numerical accuracy and failures

All inherited input, transform, SVD/optimizer and derived-arithmetic error codes and exception/warning boundaries apply unchanged, including propagation of MemoryError and unrelated errors. The Boolean support construction introduces no new rejection. Reject unusable/nonfinite basis, lifted specimen, fit or diagnostic arithmetic at the inherited appropriate numerical boundary. Finite transfer components whose normalization underflows to zero follow the stored-input support above; no original-value support promise applies.

The inherited arithmetic allowance E retains L=2*N*M and C=M+N+1, using full-space u_star and D. For r>0 its well-conditioned regime now refers to B: cond2(B)<=10 and sigma_min(B)>=1/16, together with E<=1/1024 and safely finite targets. Apply the existing nuisance-vector/singular-value/diagnostic allowances to lifted u, the r singular values of B and the inherited diagnostics. Reduced basis choice affects only floating organization within those allowances. Tight independent analytic checks must still distinguish conjugate reflection, shift direction, pair dimensions, signs/factors, zero versus weak support and profiled derivative errors. No generic phase-error tolerance or new backend theorem is selected.

## Result and compatibility

Return a fresh frozen-binding ObservableVolumePhaseEstimate. It has all fields of VolumePhaseEstimate with inherited types, ownership and meanings, except nuisance_singular_values has shape (r,), nuisance_rank refers to B and termination additionally allows no_observable_specimen. specimen_normalized remains the full z/y/x real signed dimensionless minimum-norm observable representative. It is not the hidden physical specimen; excluded components are unavailable rather than estimated physical zeros.

Additional fields:

| Field | Type and meaning |
|---|---|
| observable_fourier_mask | Independently owned mutable C-contiguous native Boolean ndarray of shape K in the same centered frequency storage as order_otf; exactly H |
| observable_dimension | Python int r |
| unobservable_dimension | Python int M-r |

Structural zero Fourier coefficients describe the exact target; an external floating-point FFT of the returned spatial array need not contain bitwise zeros. No array aliases caller storage, another field or another call. Direct record construction needs no validation. All existing public names/behavior remain unchanged. When H covers the whole grid, the reduced mathematical objective is the prior full nuisance objective; solver trajectory/bit patterns are not promised equal across valid organizations. No public Q, reduced coordinate vector or internal test seam is added.

## Behavioral inventory

Each row groups related obligations; it is not a scenario/example cap. A records distinct outcomes and equivalent examples independently; B challenges legitimate positive cases and omission risks.

| ID | Obligation and risk |
|---|---|
| O01 | Public additive signature, record ownership and unchanged prior interface |
| O02 | Complete inherited input/record validation, stable codes and conversion boundaries before all early returns |
| O03 | Normalized exact component support; zero, signed-zero, weak nonzero and underflow distinction |
| O04 | Carrier shift direction, signed-order conjugate reflection and full-axis Hermitian closure |
| O05 | Odd/even, singleton, self-conjugate Nyquist and conjugate-pair real dimensions |
| O06 | Non-Hermitian F0, one-sided direct visibility and retained complex mismatch |
| O07 | Real orthogonal reduction, full/reduced objective equivalence and minimum-norm lifted representative |
| O08 | Structurally absent modes removed; retained weak or phase-dependent deficiency remains explicit |
| O09 | r=0 unavailable diagnostics with both zero and nonzero data; all inputs still validated |
| O10 | Full/reduced SVD cutoffs, initial deficiency, rank_changed and termination ordering |
| O11 | Residual-dependent profile derivative, projected phase information, design rank and no-information versus nuisance availability |
| O12 | Canonical/huge phases, carrier aliases and order cancellation at particular phases |
| O13 | Scaling/range/error/warning policy, genuine numerical dependency failures and nonmutation |
| O14 | Hidden independent phases and specimen, fixed gauge covariance and full-support compatibility |
| O15 | Existing empirical-calibration/adapter composition and two actual independently generated observation groups |
| O16 | Executed usage and signed comparison separating structural availability, stored estimator/objective error, parameter error and physical/model limits |

## Ownership and delivery

Fresh native Sol/high A owns tests/test_observable_volume_phase_estimation.py and optional tests/observable_volume_phase_estimation_fixture.py plus ignored independent public evidence. Fresh native blind B reviews exact tests/fixtures and sanitized evidence before restricted fresh C. C owns src/simrecon/_observable_volume_phase_estimation.py, narrowly shared private internals in src/simrecon/_volume_phase_estimation.py if necessary to reuse the existing algorithm without altering its public behavior, additive exports in src/simrecon/__init__.py, docs/usage/observable-volume-phase-estimation.md and ignored actual example producers/evidence. Reviewed tests/fixtures, other runtime, dependencies/lock, discovery/coverage/workflows, policy/skills and gate helpers are outside C ownership. Fresh native D independently assesses exact passing candidate. Coordinator owns contract/task/PROJECT/roadmap/report/presentation and unique lessons. Setup infrastructure has separately named bounded ownership and independent acceptance before use.

Inherited task-selected100%Coverage.py native executable-line/branch-destination targets remain binding globally/perpackage/perownedfile for src/simrecon+scripts, including never-imported/relevant subprocesses, zero exclusions, separately local/Ubuntu24.04/macOS15; no platform union. Full-local exact-candidate mode remains. Cheap locked interpreter/platform/install/import/Java-reader/isolated-build prerequisites precede expensive dependent work. Exact clean canonical make verify/all13phases, complete native SQLite/JSON/HTML, same-runM25 and wheel/source/staticversion/environment/executable/lock/check/input/base identity precede fresh D and the owned PR stacked on PR40. Closed successful native CI and independently qualified original platform archives precede final live readback and exactly one started successor while authorized work remains. No human numeric limits are set. Retain all inherited/new attempts, corrections and charges; unknown meters stay unknown.

Sources opened for numerical dependency conventions: [NumPy SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html), [SciPy local least squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html). The reduction/objective/availability choices are project mathematical definitions above, not claims imported from those sources.
