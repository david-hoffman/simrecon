# Fixed-transfer local volume phase estimation v1

**Version 1.0. October 17, 2026.** The standing owner roadmap continuation, direct successor approval and current native-session approval authorize this dependency-ready Phase 5 slice above completed PR39. This contract selects a local variable-projection estimator. It does not promise global uniqueness, arbitrary-start recovery or physical instrument accuracy.

## Public boundary

```python
from simrecon import VolumePhaseEstimate, estimate_volume_phases

estimate = estimate_volume_phases(
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

Only images is positional. Every keyword is required; the values above are examples, not defaults. One call handles one orientation/channel/time, with images axes phase/z/y/x, N>=5 and positive spatial dimensions. Input signal units are those of the corrected observations. Phases and deviations are radians; transfers and normalized fit diagnostics are dimensionless. The carrier is supplied in integer specimen detector bins, y/x. The operation estimates every exposure phase, including the common offset in the **fixed supplied calibration gauge**. Initial commands initialize the solver; they are not actual phase measurements, a penalty or a search list.

`order_otf` is one already prepared VolumeOrderOtf, such as the orders returned by the existing empirical adapter. Calibration, grid adaptation, finite-bead correction and phase-reference declarations are composed before this call through existing public interfaces. Their origin/gauge and full complex relative order gains are used once, as stored. No gain, carrier, exposure scale, drift, background, support, specimen position or calibration parameter is fitted. The source is an opaque caller label, not authenticated provenance. Existing interfaces, dependencies, policies and gates remain unchanged.

This is a finite **periodic** observation model. It is distinct from the carrier scanner's nonwrapping overlap objective and from reconstruction's enlarged nonwrapping output window. It adds no continuous carrier model, raw workflow, realistic large simulation or owner-reference parity.

## Input grammar, snapshots and controls

Images and initial_phases_rad are plain NumPy ndarrays, real dtype kinds i/u/f at any available width/endian. Reject nonarrays, subclasses/masked arrays, bool, complex and other kinds. Images shape is (N>=5,Nz>0,Ny>0,Nx>0); initial phases shape is exactly (N,). Every source component and independent native float64 snapshot must be finite. Signed observations, finite underflow/conversion rounding, unequal/repeated commands, singleton axes, odd/even grids, strided/Fortran/read-only storage and huge finite phases are permitted. There is no phase-design-rank input requirement. Snapshot accepted arrays and calibration before numerical work. Preserve caller bytes, layout, write flags, NumPy error mode and warning filters. Concurrent external mutation is outside the guarantee.

Validate every field of a VolumeOrderOtf instance, including ordinary subclasses, with the single-record rules of [volume recombination](volume-recombination-v1.md#effective-transfer-records): plain complex128-width values of shape (3,Nz,Ny,Nx), finite real/imaginary components; plain float64-width finite canonical frequency vectors of matching length; converted positive finite z/y/x spacing; in-bounds exact integer origin; nonblank source. Both endian forms and noncontiguous/read-only storage are valid. Frequency tolerance is the inherited 8*eps*abs(f_exact)+q, eps=2^-52, q=2^-1074; expected coordinates use exact represented spacings without overflowing an intermediate period. All fields/samples are validated even when observationally ineffective. Missing required attributes reject; unrelated getter exceptions propagate. No normalization, Hermitian, nonnegative, realizability or nonzero-transfer test applies. Origin is already encoded; do not apply it again. Only the new operation's error code changes at this validation boundary.

carrier_bins_yx is an exact built-in tuple/list of two nonboolean Python/NumPy integers, extracted exactly to Python ints. Huge/unsigned/negative/zero values are valid. Preserve the declared integers in the result; reduce only for periodic indexing. max_nfev is a nonboolean Python/NumPy integer >=1, with no arbitrary upper cap. gradient_tolerance and step_tolerance are nonboolean Python/NumPy real integer/floating scalars converted individually to binary64, each strictly between eps and 1. source is a nonblank string, retained unchanged. Expected TypeError/ValueError/OverflowError at conversion translate at that named boundary; MemoryError and unrelated exceptions propagate.

There is no practical-size or working-set promise. Dense real linear algebra is permitted in this first estimator. Ordinary allocation failure propagates. This does not establish feasibility of the later 512x512x64 workflow; a measured scalable implementation is a remaining integration dependency.

## Stored-input periodic model and normalization

Let K=(Nz,Ny,Nx), M=Nz*Ny*Nx, and ell=(0,ky,kx). Let U be the unitary negative-exponent spatial discrete Fourier transform (DFT); centered storage uses the existing canonical detector bins. Modular negation acts on **all** axes and retains the single even Nyquist bin. From the stored positive rows T0,T1,T2 define T_-m(k)=conj(T_m((-k) mod K)), m=1,2. Never substitute same-frequency conjugation, ordinary reversal or physical-frequency extrapolation. Carrier indexing is (k-m*ell) mod K, for signed m=-2,-1,0,1,2.

Use a single maximum-component observation scale b=max(abs(images)); choose b=1 if all observations are zero. Use one common transfer component scale t=max(abs(Re values),abs(Im values)) across all rows; choose t=1 for all-zero transfers. Divide real components by these positive scales in binary64, retaining their resulting values as the normalized stored inputs d and F. Do not normalize orders individually, take complex magnitudes to select t or change relative complex gains. Subnormal loss in these normalizations is permitted; it supplies no physical or relative-accuracy promise.

Canonicalize initial finite angles by native NumPy cos/sin followed by atan2, mapping a returned +pi to -pi. Do not reduce huge angles modulo rounded 2*pi or double them. At each finite trial phase phi compute native float64 c=cos(phi), s=sin(phi), z=c+i*s and z2=(c*c-s*s)+i*((2*c)*s), with the shown rounded operations. Negative phase powers are conjugates. These represented phasors, not exact-real trigonometry, define the phase basis. At a returned candidate canonicalize again and recompute all fit/diagnostic fields at those returned angles. Returned phasors are cos(returned phi)+i*sin(returned phi); their represented norms need not be bitwise one.

Let u be a **real, signed**, dimensionless nuisance specimen, with z/y/x indexing. It is unknown and inferred; there is no positivity/support constraint. In exact arithmetic on normalized stored inputs and represented phase powers, the Fourier prediction is

```text
Y_p(k) = U d_p(k)
prediction_p(k;phi,u) = sum_m z_p^m * F_m(k) * (Uu)((k-m*ell) mod K)
```

The five-signed-order sum contains no extra factor of two. The equivalent real-compatible spatial form groups side orders as 2*Re. Arbitrary non-Hermitian F0 remains algebraically valid: retain its complex prediction and its disagreement with real observations; never silently symmetrize/project the calibration. This is off-model calibration, not physical illumination certification.

Realify the prediction by stacking all real Fourier coordinates followed by all imaginary coordinates, in phase/z/y/x C order. This defines A(phi) of shape (2*N*M,M), and y of length 2*N*M. The unitary transform preserves the unweighted spatial least-squares meaning for real-compatible calibration. No likelihood, noise weights, window, mask, ridge or omitted frequencies apply.

For each phase vector, solve the unregularized real least-squares problem

```text
u_star(phi) = argmin_u ||y-A(phi)*u||_2
r(phi) = y-A(phi)*u_star(phi)
J(phi) = 0.5*||r(phi)||_2**2.
```

Use singular value decomposition (SVD), never normal equations for the product solve. For computed singular values sigma, tau=eps*max(2*N*M,M)*sigma_max and numerical nuisance rank counts sigma>tau; equality is deficient, all-zero rank is zero. The minimum-norm truncated SVD coordinates define the **availability diagnostic** at a deficient initial point. Such a point is returned with nuisance_rank_deficient; no optimizer is run and no phase estimate is certified. In full-rank regions this selects the ordinary unique real least-squares nuisance solution. No ridge or accepted rank truncation is silently substituted during optimization. Numerical cutoff boundary behavior is operational and can vary with backend roundoff.

The first implementation deliberately reports unresolved availability when any nuisance direction is numerically unobserved, including permanently invisible specimen modes. It does not claim those modes necessarily prevent phase recovery. Reduction of permanent nullspaces and positivity-constrained inference remain later contracts. Permitted weak/zero/off-model inputs are not malformed merely because estimation is unavailable.

## Local optimization, derivatives and termination

Use scipy.optimize.least_squares with the profiled real residual, analytic Jacobian, method='trf', bounds=(-inf,inf), loss='linear', x_scale=1, tr_solver='exact', ftol=None, gtol=gradient_tolerance, xtol=step_tolerance, max_nfev=the supplied integer, no callback/workers/sparsity or extra prior. Initial optimizer phases are the canonicalized commands. There is one continuous local start. Equivalent finite organization of A and its SVD is permitted; optimizer trajectory/iteration bit patterns are not a cross-platform promise.

At a full-rank point, let A_p=partial A/partial phi_p, D[:,p]=A_p*u_star, Pperp=I-A*Aplus. The selected profile residual Jacobian is

```text
R[:,p] = -Pperp*D[:,p] - transpose(Aplus)*transpose(A_p)*r.
```

Use the represented fundamental/second harmonic model's analytic derivatives, with first derivative i*m times its represented signed phase factor. They are the smooth trigonometric model derivatives to binary64 accuracy, not derivatives of the discrete rounding map. The residual-dependent second term is required for off-model observations. The fixed-calibration projected information matrix is Kphi=Pperp*D. Kphi is not R or a profile Hessian when the residual is nonzero. Report gradient_inf_norm=norm(transpose(R)*r,inf).

At an initially deficient point, define Aplus explicitly from only the retained sigma>tau SVD directions and u=Aplus*y. Compute r, D, Pperp, Kphi, the displayed R expression and its reported gradient norm **algebraically with this same truncated Aplus/u**. These are finite availability diagnostics. This R/gradient is not necessarily a derivative of the exact profiled objective at a rank transition or of an exact full-rank solve discarded by the numerical cutoff. No optimizer or phase-identifiability certification follows from them. This convention also defines all-zero A diagnostics without division by discarded zero singular values.

If a trial or final canonical reevaluation changes nuisance rank from full M, stop the solve and return the **initial** candidate and its diagnostics with rank_changed. No unstable trial is returned as accepted. This is a non-success local execution outcome, not an invalid-input rule. Record observed residual/Jacobian evaluation counts; do not fabricate a solver nfev after an interrupted solve.

Otherwise recompute final fields and classify in this order: stationary if computed gradient_inf_norm<=gradient_tolerance; evaluation_limit if SciPy status=0; otherwise stagnated for a positive solver termination that does not meet the final gradient criterion. A negative or unusable solver status is a numerical failure. Stationary means only small computed first derivative. It proves neither a minimum nor informative/accurate phases. No hidden residual or information threshold applies. SciPy numerical failure or unusable/nonfinite output is a numerical error, not an accepted finite fit. Only actual finite operation and dependency results may justify classification; artificial finite solver records are not a test oracle.

Report nuisance and Kphi singular values. Phase rank uses sigma>eps*max(2*N*M,N)*sigma_max; zero rank is zero. Absolute singular values describe strength in **normalized** observation units per radian; rank/conditioning is not a statistical confidence interval. Report separately the returned five-column phase-design rank using the existing separator's represented basis and strict cutoff. A local full-forward fit can yield phases unusable by the existing separator. Global ambiguity is always unassessed.

## Numerical accuracy, range and failures

Use binary64/complex128. Scale before transforms/products/norms; overflowing complex magnitudes or raw observation sums alone must not reject valid finite component inputs. Public numpy.fft.fftn is the observation transform boundary, with unitary normalization or mathematically equivalent normalized processing of bounded data. Preserve warning/error policy. Handled conversion, underflow and range cases emit no arithmetic RuntimeWarning or FloatingPointError; unrelated warnings/exceptions remain visible.

This contract selects the local objective and the numerical rank/optimizer procedure; it promises no universal phase error in radians. Phase recovery depends on a locally resolved basin, nuisance-rank stability, information strength and model validity. At a strongly convex independently established local objective with curvature lower bound mu>0, an independent objective-gap eta implies local estimator distance <=sqrt(2*eta/mu). Gradient/curvature or perturbation bounds require separately established local remainder and conditioning; no ratio is a confidence interval or physical truth guarantee.

For independently checked returned full-rank points, set L=2*N*M, C=M+N+1, and let exact normalized stored-input targets be y, u_star, D, r and Kphi as above. A conservative **project arithmetic allowance**, not a backend theorem, is

```text
E = 2**20 * L*C*eps * (1+norm(y)+norm(u_star)+norm(D))**2 + 256*L*C*q.
```

When cond2(A)<=10, sigma_min(A)>=1/16, E<=1/1024 and all target coordinates/norms are safely finite, require: norm(u_returned-u_star)<=E; each returned singular value differs from its exact target by <=E; each normalized RMS, relative residual, calibration reality defect and gradient norm differs from its target by <=E. Phase-design rank uses singular values from its separate stated basis/cutoff, with no classification guarantee at a cutoff boundary. Norms are Euclidean/Frobenius as appropriate. Observer calculations must not overflow, underflow or use product outputs as expectations. Tight independently justified analytic checks must additionally distinguish signs, factors, order mixing, modular indexing and objective/Jacobian mistakes; the conservative envelope is no license for a different estimator. Outside this regime the specified procedure and computed finite/range rules remain binding, without a uniform digit guarantee.

Absent genuine allocation/dependency failure, benign informative inputs whose initial and visited points satisfy this regime, have stable full nuisance rank and safely finite normalized intermediate/final components must yield finite results with the selected termination. This is not a convergence or arbitrary-start guarantee. Nonfinite computed transform, SVD, optimizer, fit/restoration or diagnostic coordinates reject the whole call; no partial result, clipping, saturation or alternative estimator is returned.

Use SimreconError with stable string code. Message prose and simultaneous-invalid precedence are unspecified.

| Obligation/failure | code |
|---|---|
| Images nonarray/subclass, invalid kind/shape | invalid_volume_phase_estimation_images |
| Source/converted images nonfinite | nonfinite_volume_phase_estimation_images |
| Initial phases representation/kind/shape | invalid_volume_phase_estimation_initial_phases |
| Source/converted initial phases nonfinite | nonfinite_volume_phase_estimation_initial_phases |
| OTF instance/field/grid/metadata validation | invalid_volume_phase_estimation_otf |
| Carrier grammar/extraction | invalid_volume_phase_estimation_carrier |
| max_nfev or tolerance grammar/conversion/range | invalid_volume_phase_estimation_controls |
| Nonblank source string | invalid_otf_source |
| FFT FloatingPointError/OverflowError/arithmetic RuntimeWarning or nonfinite transform | volume_phase_estimation_transform_failure |
| SVD LinAlgError; SciPy LinAlgError or numerical FloatingPointError/OverflowError/arithmetic RuntimeWarning; unusable/nonfinite numerical factors/result | volume_phase_estimation_solver_failure |
| Nonfinite fit/derived diagnostic arithmetic outside the numerical dependency execution | unrepresentable_volume_phase_estimation |

Unrelated RuntimeError/TypeError/ValueError and MemoryError propagate. Catch expected conversion exceptions only at their named conversion boundary; do not relabel arbitrary programming errors. No test-only dependency seam or fabricated finite scientific dependency state is authorized.

## Result

Return a fresh frozen-binding VolumePhaseEstimate with exactly these fields:

| Field | Meaning/type |
|---|---|
| phases_rad; phasors; phase_deviations_rad | Independently owned mutable C-contiguous native float64/complex128/float64 arrays (N,); canonical angles [-pi,pi), represented phasors and wrapped final-minus-canonical-initial deviations |
| specimen_normalized | Owned mutable native float64 C-contiguous z/y/x nuisance array u; signed and dimensionless, not calibrated physical specimen truth |
| image_scale; transfer_scale | Python floats b,t selected above; original-unit nuisance would be u*b/t where representable, without a physical intensity calibration claim |
| relative_residual | Python float norm(r)/norm(y), with exact-zero data convention0 |
| normalized_residual_rms; normalized_imaginary_rms | Python floats norm(r)/sqrt(N*M), norm(Im prediction)/sqrt(N*M); imaginary residual is retained for algebraic non-real calibration |
| calibration_reality_defect | Python float norm(F0-conj(F0(-k mod K)))/sqrt(M), on normalized transfer values |
| nuisance_rank; nuisance_singular_values | Python int and separately owned mutable native float64 C array (M,) |
| phase_rank; phase_singular_values | Python int and separately owned mutable native float64 C array (N,) for Kphi |
| phase_design_rank | Python int, returned known-phase separator design rank |
| gradient_inf_norm | Python float from the full profile Jacobian |
| termination | stationary, evaluation_limit, stagnated, nuisance_rank_deficient or rank_changed |
| nfev; njev | Python ints counting actual residual and analytic-Jacobian evaluations observed by this call, including initial/final reevaluation if they use those evaluators; report counts, not a claimed total-time limit |
| carrier_bins_yx; source; global_ambiguity | Original Python-int pair, unchanged source string, literal unassessed |

Array fields alias neither caller storage, one another nor another call. Direct record construction requires no validation. At nuisance_rank_deficient return the canonical initial candidate with minimum-norm numerical SVD nuisance and its same-point projected diagnostics, explicitly unavailable as a phase-identifiability certificate. At rank_changed return that initial candidate as specified. All other fields keep their definitions; all-zero images permit exact-zero nuisance/residual/information diagnostics. Estimated and supplied quantities remain distinct.

## Identifiability and assessment

Fixed complete complex gains remove the automatic common phase/gain gauge. The phases still refer to declared calibration coordinates, not absolute instrument phases. With free gains g_m the transformation phi_p->phi_p+a, g_m->g_m*exp(-i*m*a) is an exact ambiguity; this operation fits no such gains. Translating specimen by integer t while subtracting 2*pi*ell.t/K from phases translates predicted images, rather than preserving arbitrary fixed observations. Do not silently register or fit a centroid.

Zero side signal, weak overlap, specimen/transfer symmetries, even-only illumination (independent pi ambiguities) and proportional-kernel point specimens can leave phases unidentifiable. A uniform specimen can contain phase information. Full local differential rank does not exclude discrete/global alternatives. Calibration, carrier, drift or camera mismatch can bias a very good local fit. Separation residual alone cannot infer five unknown phases, since an invertible five-column phase matrix fits five values at each voxel; this estimator's shared-specimen/fixed-transfer constraint supplies additional information.

Independent assessment must distinguish (a) arithmetic/objective agreement on stored inputs, (b) local optimizer behavior and (c) phase recovery against hidden synthetic truth. Small observers construct the real matrix directly from Fourier sums or independent spatial convolution, solve nuisance expectations independently and verify projected information/full off-model Jacobian. A real-space forward generator supplies independent corrected/raw specimen and separately generated calibration observations; actual specimen phases, object, kernels and true bead locations remain evaluator-only. Nominal commands are fixed independently of hidden step errors. Retain input/expected/output/generator/executable/dependency identities, actual generation chronology and signed numerical results. Two independently generated example groups must include unequal independent deviations with all five orders, fixed-calibration gauge/origin checks, and at least one off-model/availability control. Report normalized estimator error separately from physical-phase error and any downstream regularization bias.

The following are requirement groups, not scenario totals or limits. A maps each distinct permitted/rejected outcome, interpretation and guarantee; equivalent data are coverage examples.

| ID | Observable obligation / credible wrong outcome |
|---|---|
| P01 | Additive public exports, required bindings, exact frozen record fields/types and independent mutable storage |
| P02 | Full image/initial-angle representation grammar, finite source/conversion, preserved snapshots and permitted widths/layouts/signed values |
| P03 | Every OTF field, unused sample, arbitrary complex/zero/non-Hermitian values, inherited canonical physical grid and getter exception handling |
| P04 | Exact huge/unsigned/negative/zero carrier provenance versus modular periodic aliasing; no nonwrapping scanner objective |
| P05 | Explicit positive max_nfev and separate tolerance grammar; opaque source and no hidden execution/scenario cap |
| P06 | One common component transfer scale and observation scale, zero conventions, extreme finite components and permitted underflow |
| P07 | Represented fundamental/squared second phases, direct huge-angle initialization, branch cuts and wrapped deviations |
| P08 | Independent all-sample five-order forward model, unitary DFT, signs/no extra factor and real shared nuisance |
| P09 | Odd/even/singleton/nonsquare geometry, all-axis modular negative orders including Nyquist, stored origin/gauge once |
| P10 | Unweighted unregularized minimum-norm SVD objective, strict nuisance rank, no positivity/support/ridge/free-gain fitting |
| P11 | Initial deficient nuisance availability, zero transfers, permanently invisible modes and no false physical impossibility claim |
| P12 | Analytic full profile Jacobian including off-model residual term versus projected information Kphi |
| P13 | Fixed local SciPy procedure/initialization and independently evaluated objective, no truth-listed schedule or command prior |
| P14 | Real stationary/evaluation-limit/stagnation outcomes and actual work counts; no stationary==minimum/inference claim |
| P15 | Trial/final nuisance-rank change returns initial candidate with non-success; stable numerical cutoff boundaries |
| P16 | Separate nuisance/phase/design rank and absolute singular values; phase weakness versus arbitrary noise threshold |
| P17 | Residual/imaginary/reality diagnostics on arbitrary algebraic/off-model calibration, no Hermitian projection |
| P18 | Conservative informative arithmetic/sufficient finite-success conditions and independently tighter sign/factor/index checks |
| P19 | Range/normalization/transform/SVD/optimizer failures, input preservation and caller warning/floating policy |
| P20 | Genuine public dependency failure exceptions versus unrelated/allocation propagation; no fake finite dependency oracle |
| P21 | Common calibration-gauge covariance, fixed-coordinate translation relation and no silent normalization/registration |
| P22 | Zero/even-only/point/sparse/weak information and global ambiguity limits; uniform positive informative case |
| P23 | Genuine five/N>5 independent-step inference from nominal initialization with hidden specimen/phase truth and independent stored-objective comparison |
| P24 | Existing raw finite-bead/empirical adapter composition, executed usage/two independently generated groups and scientific error separation |

## Ownership and gates

Scientific/numerical/custom-oracle/interface work uses fresh native Sol/high blind A, fresh blind B, restricted fresh C and fresh D. Actual serving remains unknown unless observed. A owns only tests/test_volume_phase_estimation.py and optional tests/volume_phase_estimation_fixture.py plus ignored independent evidence. C owns only src/simrecon/_volume_phase_estimation.py, additive src/simrecon/__init__.py exports and docs/usage/phase-step-estimation.md plus ignored actual example producers/evidence. Existing production helpers may be reused unchanged. C may not edit reviewed tests/fixtures, unrelated runtime, locks/dependencies, workflows, discovery/coverage, skills/policy or gate helpers. Coordinator owns contract/task/PROJECT/roadmap/report/presentation and evidence-linked new lessons. B/D are report-only; corrections retain proper ownership and fresh required review. No numeric human limits are set.

Inherit owner-selected100%Coverage.py native executable-line/branch-destination targets globally/perpackage/perownedfile across src/simrecon+scripts, neverimported/relevantsubprocesses, zeroexclusions, separately local/Ubuntu24.04/macOS15. No platform union or percentage-only tests. Exact clean canonical make verify/all13phases, rawSQLite/nativeJSON/completeHTML, same-runM25 and wheel/source/staticversion/environment/executable/lock/check/input/base proof precede fresh D and owned stacked PR. One native CI run and independently qualified original platform archives precede exactly one started successor. Default full-local gate remains; no CI-authoritative fallback. No reference C execution, merge/release, earlier PR edits or unrelated external messages.

Primary convention references opened for this intake: [Gustafsson et al. 2008, focal-plane-relative five-order model](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf), [NumPy least-squares meaning](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html), [SciPy local nonlinear least-squares controls](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html). The exact objective, gauge, representation, numerical policy and public outcomes are project choices here, not claims imported from those references.
