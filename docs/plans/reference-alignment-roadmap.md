# Reference-alignment roadmap: one task and one PR per step

**Version 1.0. 28 October 2026. Proposed execution plan.**

Start with matched, noiseless, known-parameter problems. Establish which differences are changes of coordinates and which change the estimator. Then add calibrated optics, noise, fractional carriers and finite boundaries before estimating nuisance parameters and running the full scene. Finish with the owner's corresponding C outputs. A successful program run, a lower training residual or smaller output voxels does not establish resolution improvement.

This roadmap plans work; it does not authorize execution of its proposed scientific steps, change existing contracts or replace the [migration roadmap](../MIGRATION-ROADMAP.md). Each numbered row below is exactly **one Agentic Software Delivery (ASD) task and one pull request (PR)**. Its detailed packet gives one coherent outcome. Intake will turn that packet into its exact authorized public contract before implementation. The [task record](../tasks/reference-alignment-roadmap.md) owns this documentation task's state.

## Baseline and evidence

- Execution baseline inspected: merged PR53, commit `3b4fe0239823febe9a878d3e838b416319f104bd`, tree `73c1ffb702c04dc68cb4d53f01b3a937d0860ec1`. The roadmap branch starts there. It does not stack on or modify PR54.
- Investigation read at `1211f453360ff1143feed6998225039482b55ef5`: [report](https://github.com/david-hoffman/simrecon/blob/1211f453360ff1143feed6998225039482b55ef5/docs/reports/pr53-recovery-investigation.md) and [frozen diagnostic](https://github.com/david-hoffman/simrecon/blob/1211f453360ff1143feed6998225039482b55ef5/docs/reports/evidence/pr53-recovery-forward-diagnostic.json). These are observations, not a repaired algorithm or demonstrated C/Python parity.
- Full scene: [report](../studies/full-noisy-study-2026-10-26/README.md), [full plan](../studies/full-noisy-study-2026-10-26/full-plan.json), [parameter estimates](../studies/full-noisy-study-2026-10-26/evidence/full-parameter-estimates.json). Preserve the 27-object sparse specimen, calibration data and seeds for diagnostic comparisons. Density changes are a later, separate experiment.
- Reference: ignored `SIMrecon_svn/`, local Subversion revision 307; [adoption record](../setup/BASELINE.md). Rechecked `sirecon.c` SHA-256: `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567`. Source locations below refer to this file identity and the corresponding local snapshot, not a newly executed C result.
- Inherited restriction: [migration roadmap](../MIGRATION-ROADMAP.md), opening boundary. Do not copy, ship, import or link the legacy tree, and **do not compile, build, invoke or execute any reference C program or bundled executable in these planned steps**. Numerical C comparisons consume owner-provided outputs and provenance. Missing inputs block the applicable comparison, not this plan or independent mathematical controls.

The published 3D SIM methods describe five-order separation, order-dependent transfer calibration, overlap parameter fitting and generalized Wiener assembly. They also warn that noninteger relocation interacts with filtering order. That motivates independent checks; it does not make every C option a scientific requirement. [Gustafsson et al. (2008), Methods: Transfer functions, Parameter fitting and Reconstruction](https://pmc.ncbi.nlm.nih.gov/articles/PMC2397368/).

## What the source comparison establishes

The table covers the library and study, rather than treating the latest driver as the whole implementation. OTF means optical transfer function; PSF means point spread function. DC denotes the phase-independent component. The Fourier transform uses spatial frequency in cycles/µm unless explicitly converted to radians/µm.

| Stage | Reference source observation | Existing Python operations | Full noisy study and disposition |
|---|---|---|---|
| Camera/background/intensity | `helpers.c:658–714` subtracts backgrounds and applies correction slopes/scaling. `sirecon.c:623–656,1093–1150` tapers and can equalize sums between exposures. Equalization assumes little specimen signal at the carrier. | [`declare_acquisition`](../../src/simrecon/_acquisition.py), [`correct_linear_response`](../../src/simrecon/_linear_response.py), [`estimate_scalar_camera`](../../src/simrecon/_scalar_camera_calibration.py). Supplied correction and estimated scalar gauge are distinct contracts. | [`full_noisy_study.py`](../../scripts/full_noisy_study.py), `_infer`, uses image-estimated blank and flat contrast. `(counts−blank)/contrast` is a relative-unit signal, not photons. Constant correction exists; reference equalization/bleaching policy is not integrated. Do not enable it blindly on sparse beads. |
| Phase separation | `sirecon.c:658–752,1155–1283`: lateral transform, phase matrix and axial transform; ideal/supplied steps and optional drift changes. | [`separate_phases`](../../src/simrecon/_phase.py) and [`separate_volume_phases`](../../src/simrecon/_volume_phase.py) already fit explicit phase designs; the latter yields DC, complex c1 and c2. | Study direct operator contains the same harmonic families. Missing an explicit separation call is **not** missing harmonic physics. Its estimator/objective still differs. |
| Carrier/phase/overlap | `sirecon.c:1286–2013`: OTF-weighted specimen overlaps, cross-correlation, local carrier refinement and complex regression. Ordinary 3D fitting principally uses 0↔2 overlap. | [`estimate_illumination`/2D scans](../../src/simrecon/_illumination.py); [`estimate_volume_order_gain`](../../src/simrecon/volume_order_gain.py); volume carrier diagnostics/selection; fixed-transfer phase estimators including [`Fourier-block execution`](../../src/simrecon/_fourier_block_phase.py). | Study's [`bead calibration`](../../scripts/image_only_bead_calibration.py) fits a finite three-beam model and freezes it for specimen fitting. It does not use specimen overlap to refine it. Existing integer scans and caller policy do not provide continuous physical-carrier identification. Independent exposure phases are broader than a common starting-phase fit. |
| Order OTFs/calibration/beads | `helpers.c:747–843`, `small_math_funcs.c:396–480`: separate grids, radial/Cartesian complex OTF interpolation. `mainfile.c:176–321,705–969,1114–1130`: bead processing, continuous-sphere correction, radial/support cleanup and common scale choices. | [`prepare_volume_otf`](../../src/simrecon/_volume_otf.py), [`prepare_volume_order_otfs`](../../src/simrecon/_volume_order_otf.py), raw point/finite-bead calibration, empirical responses, grid adapters and [`physical-frequency sampler`](../../src/simrecon/_empirical_frequency.py). Relative complex orders are preserved. | Study uses declared clear-pupil optics and beam parameters, not the complete empirical-transfer chain. Discrete periodic profile division is not automatically continuous-sphere compensation. Source-free empirical optics and unknown-phase self-calibration remain conditional. |
| Relocation/recombination | `sirecon.c:2016–2465` filters native bands, expands Fourier storage, inverse transforms and applies real-space phase ramps to shift fractional bands; conjugate pairs contribute to a real output. | [`reconstruct`](../../src/simrecon/_reconstruction.py) supports fractional 2D interpolation with documented limits. [`reconstruct_volume`](../../src/simrecon/volume_reconstruction.py) already fuses five signed orders on a complete nonwrapping output window, with integer lateral shifts and native z. | Study directly solves for a source using all exposures. Adding another band relocation inside that physical forward model could count the same mixing twice. Missing integration is between models/estimators, not necessarily an absent operation. |
| Noise/Wiener | `sirecon.c:1248–1283,2133–2240`: phase noise factors, complex conjugate weighting, denominator summed over directions/orders plus Wiener parameter squared; optional suppression/damping/apodization. | Volume fusion forms `sum(conj(T)*D)/(sum(abs(T)^2)+regularization)` with an explicit output mask. This supplies a ridge-style special case; it does not propagate arbitrary separation covariance. | [`fit_specimen`](../../scripts/image_only_specimen_fit.py) uses unweighted exposure residuals plus a source penalty and nonnegativity. A parameter named regularization is not numerically interchangeable with C's Wiener parameter. |
| Boundaries/padding/taper | `sirecon.c:1051–1090,2039–2110,2334–2465`: input edge mixing/windows, output support taper, padded Fourier assembly and zoom. | Public spectral operations have explicit finite-periodic/native-grid contracts. Explicit output apodization is not input edge taper. | [`simulation_inverse_operator.py`](../../scripts/simulation_inverse_operator.py) uses exterior-zero finite convolution, lateral embedding/crop, half-cell anchors and four detector subpixel midpoint samples. [`simulation_optics.py`](../../scripts/simulation_optics.py) independently generates refined source/pixel means. Axial basis aggregation changes locations even when it preserves mass. |
| Drift | `drift_n_phasestep.c:213` and reconstruction call sites support conditional between-direction and within-direction adjustments; drift is optional, disabled by default. | [`estimate_translation`](../../src/simrecon/_translation.py), [`estimate_volume_translation`](../../src/simrecon/_volume_translation_estimation.py), [`correct_integer_drift`](../../src/simrecon/_drift.py) cover supplied comparable periodic references or known integer motion. | Retained study is stationary. Raw phase-frame cross-correlation is not automatically a motion estimator because illumination changes. Motion is an applicability branch for owner data, not a demonstrated PR53 cause. |

### Conventions that must be translated, not guessed

| Quantity | Observed distinction and required check |
|---|---|
| Axes/storage | Python physical arrays use z/y/x, carriers y/x; C carrier structs use x/y. C uses x half-spectra, padded real rows and acquisition section ordering. Test nonsquare sizes, unequal Python lateral sampling and nonzero axial coordinates. C uses one lateral spacing `dxy`; unequal x/y sampling is outside that observed mode. |
| Units/harmonic carrier | C wavelengths are commonly nm; Python synthetic wavelengths are µm. Both use cycles/µm for physical carriers. C `sirecon.c:388–396` divides reciprocal line spacing by `nordersIn−1` in 3D: configured spacing can describe the highest lateral harmonic. A Python fundamental q then has order-two carrier 2q. A factor-of-two disagreement is unresolved until this mapping is applied. |
| Phase sign/origin | Python reconstructs `I_p=dc+2 Re(c1 exp(iφ_p)+c2 exp(2iφ_p))`, so cosine/sine coefficients give `(B−iC)/2`. C stores cosine+i·sine with associated positive assembly ramps and a centered lateral origin. Derive the full mapping, including scale, before comparing bands; a conjugation in isolation proves no defect. The study anchors samples at half-cells and transfers calibration-origin phases to specimen origin once. |
| Complex reflection | Physical negative orders require conjugation **and frequency reflection on all axes**. Python native periodic even-Nyquist reflection and explicit physical positive/negative endpoints are different representations. Test asymmetric complex transfers so magnitude-only agreement cannot hide a sign error. |
| Fourier scale/intensity | Python volume spectra use normalized forward and unnormalized inverse transforms; PSF/empirical preparation has its own mass convention. C pre-scales loading and uses unnormalized transforms/separation. First/second harmonic phases are related, but the order-two optical response is not generally the square of order one. Trace the complete phase-count, direction-count, output zoom, pixel area and common OTF scale once. Constant and displaced point controls must agree without fitted rescaling. |
| Pixel integration | Study source entries are integrated emission weights; pixel-area quadrature occurs in observation, with no extra source voxel-volume multiplier. No explicit detector integration correction was found in the inspected C paths; measured C OTFs may already contain detector response. Never apply a pixel factor twice or assume measured and ideal optical OTFs mean the same thing. |
| Axial source–focus relation | Public effective kernels require axial profiles fixed relative to focus; the direct model uses source-minus-focus displacement and unequal-side axial factors. Compare a displaced point above and below focus with known unequal beam amplitudes. Native z retention is not absence of axial SIM physics, and axial mass pairing is not forward equivalence. |

**Classification.** Equivalent formulations are possible for harmonic separation, conjugate-band representation and matched linear least squares. Justified existing differences include explicit unequal-phase least squares, complex outputs and finite-model domains that avoid C heuristics. Missing integration includes calibrated transfer consumption, specimen-informed continuous carrier fitting, separation-noise weighting, fractional 3D assembly and the full raw path. Established poor-recovery observations are the short nonconverged trajectory and measured illumination/model discrepancies; no C/Python numerical mismatch has yet been demonstrated. Whether any discrepancy violates an approved contract still needs an independent expected result.

C is a comparator, not an unquestionable oracle. One concrete source warning: `small_math_funcs.c:580–609` iterates z only within a region excluded by the condition that increments its mid-frequency signal counter, then divides by that counter in automatic Wiener estimation. This was inspected, **not executed**; the impact for supplied data/settings is unmeasured. Optional padding and Nyquist paths also need independent checks. Do not reproduce a suspected defect to obtain agreement. Report compatibility and scientific correctness separately.

## When direct inversion can equal spectral reconstruction

Let y contain raw corrected exposures, A the matched linear imaging map, W the declared inverse observation covariance, L the regularization operator, and λ the declared penalty scale. The unconstrained estimator minimizes

`J(x) = (Ax−y)* W (Ax−y) + λ ||Lx||²`.

Its normal equations are

`(A* W A + λ L*L)x = A* W y`.

Here `*` denotes the adjoint; in a real-coordinate problem it is the corresponding transpose. Under a common periodic, shift-invariant representation with integer-bin carriers, known phase design, compatible Fourier basis and diagonal separated-band covariance, the equations reduce at each represented specimen frequency to

`x_hat(k) = sum_j(conj(T_j(k))*d_j(k)/v_j(k)) / (sum_j(abs(T_j(k))²/v_j(k)) + λ ell(k))`,

where j indexes the relocated direction/order observation, v is its variance and ell is the spectral penalty. This is a weighted spectral inverse. Unsupported modes require an explicit nullspace convention. An output taper multiplies this result afterward unless the contract puts it inside the objective. This is a proposed comparison derivation, not a claim that the existing implementations already satisfy all premises.

For the retained study, `J=||Ax−Y||²/(2M)+λ||x||²/(2N)`, where M counts all detector observations and N counts source coefficients. Multiplying by M gives an ordinary least-squares penalty `μ=λM/N`. Here `M/N=15/4`, so `λ=0.001` gives `μ=0.00375` before any Fourier/noise conversion. This dimensional sanity check alone rules out copying the numerical setting between formulas.

Separation is a coordinate change only if the transformed objective is preserved. Unequal phases, correlated noise, duplicated DC/negative-band observations, real-source constraints and detector aliasing require the correct metric and multiplicities; independently treating every stored band as a new observation can change the estimator. A diagonal Wiener formula is not a universal solution for arbitrary phase designs.

Exterior-zero boundaries, cropped observations, fractional-carrier finite-window mixing, nonlinear noise objectives, active nonnegativity, different basis supports or early stopping can break that frequency-wise reduction. If nonnegativity is inactive and the linear solution is unique, a converged constrained solve can agree; otherwise it solves a different problem. To establish equivalence, compare an independently assembled tiny real observation matrix, its adjoint, full normal equations, separated covariance and objective/stationarity residuals against public outputs. Then add each broken premise separately and label intentional divergence. Do not infer equivalence from similar pictures or optimizer success.

## Dependency and order table

Each ID is one task/one PR. Dependencies mean **completed, reviewed and present in the execution baseline**; a planned or draft PR is not a prerequisite. The linear order is a safe launch order; independent branches may run in separate worktrees once their listed dependencies pass.

| Order/task | Single scientific outcome | Dependencies | One proposed PR title |
|---|---|---|---|
| RA01 | Freeze modes, comparison inputs and acceptance derivation | merged baseline; PR54 observations as external evidence | Define the reference alignment benchmark and comparison manifest |
| RA02 | Prove matched known-parameter periodic conventions and inverse equivalence | RA01 | Verify five-order conventions and matched spectral inverse controls |
| RA03 | Measure physical forward/basis discrepancies on every exposure | RA02 | Isolate source sampling and illumination errors across all study exposures |
| RA04 | Compose declared camera/intensity handling in one gauge | RA01–RA03 | Preserve camera and intensity units through the alignment path |
| RA05 | Align known-phase order-transfer calibration and consumption | RA02–RA04 | Calibrate and consume matched complex order transfer functions |
| RA06 | Define and implement known-parameter noise-weighted spectral fusion | RA05 | Add covariance-aware weighting and explicit Wiener units |
| RA07 | Support known fractional 3D band relocation in the selected finite model | RA06 | Recombine fractional volume bands with verified filter ordering |
| RA08 | Resolve finite boundaries, padding/taper/crop and source-solve objective | RA03, RA07 | Make finite-field reconstruction boundaries and convergence explicit |
| RA09 | Estimate continuous specimen carrier and relative order gains | RA05, RA07–RA08 | Refine specimen carriers and complex gains from spectral overlap |
| RA10 | Handle independently imperfect exposure phases in a fixed gauge | RA06, RA09 | Estimate exposure phases without changing the calibration gauge |
| RA11 | Supply the applicable drift mode or certify stationary applicability | RA08, RA10 | Validate comparable-reference drift and illumination phase correction |
| RA12 | Produce a predictive images-only calibration-to-specimen handoff | RA04–RA05, RA09–RA11 | Transfer identifiable calibration responses into specimen reconstruction |
| RA13 | Integrate one raw observation-only reconstruction entry point | RA06–RA12 | Integrate calibrated raw SIM reconstruction with full provenance |
| RA14 | Demonstrate alignment on the frozen full synthetic scene | RA13 | Demonstrate full-scene recovery and reference-method alignment |
| RA15 | Demonstrate parity on supplied owner C cases with independent adjudication | RA14 plus owner inputs/settings | Validate owner-data reference parity and document supported differences |

RA11 has a bounded applicability: the current stationary study needs a documented no-motion control. Implement motion only for a concrete supplied acquisition mechanism and comparable references. If no such target exists, RA11 is a report-only applicability PR, not an invented drift feature. RA15 remains blocked if owner reference files or material comparison decisions are missing. RA14 can demonstrate independent method alignment without claiming an unobserved C execution.

## Rules inherited by every execution packet

These are references to existing rules, not new policy. Numerical behavior, scientific estimators, custom oracles and their integration use the **high-risk route**: fresh native blind A tests/fixtures, fresh native blind B oracle/scope review, restricted C implementation, fresh native D exact-candidate review. Discovery in this roadmap is nonblind and must not be handed to A/B. The coordinator extracts approved equations, interfaces, cases and independent expectation sources into their public packets; source maps, implementation/history and coverage findings stay out. Role launches belong to the future coordinator. C owns only named runtime files and cannot edit frozen tests/fixtures, gates or delivery policy.

RA01 is report-only intake documentation. A purely stationary RA11 applicability report also adds no runtime. Their documentation ownership belongs to intake/coordinator; substantive scientific proof/custom oracle work retains high-risk review. No policy amendment is proposed. No report-only label permits shipping numerical behavior without the numerical route.

For each numbered step, the scope below is the proposed ownership boundary: A owns its new or corrected tests/fixtures; C owns only the named relevant runtime modules after checkpoint acceptance; the coordinator owns reports/figures/provenance. Existing filenames are anchors, not permission to modify unrelated interfaces. New module/API names and exact error grammar must be fixed at that step's intake. Public operations remain backward compatible unless an explicit contract says otherwise.

All steps inherit [PROJECT coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance): approved behavior coverage and independent risk review, **advisory percentages**, valid complete native statement/branch reports globally/per owned package on required platforms. Historical contracts with earlier gates are not silently migrated. Full local `make verify UV=/Users/davidhoffman/.local/bin/uv` on the exact candidate precedes opening/reopening a PR or pushing to an open PR; CI repeats Ubuntu 24.04 and macOS 15. Focused commands below are additional evidence, not substitutes. First run cheap environment checks (`make preflight` with that UV path); diagnose environment failures before dependent work. No new scenario, iteration, review, cost or time cap is imposed.

Before formal tests, each task expands its boundary inventory into distinct observable operation, invalid-input, representation-limit, operation-failure, compatibility and documentation scenarios. Use finite signed controls, permitted zero/absent-order cases, ambiguous/weak-information outcomes and paired legitimate positive inputs where applicable. Derive tolerances from independently bounded arithmetic/conditioning, discretization or a predeclared statistical uncertainty model. **No numerical recovery tolerance is selected by this roadmap.** An unresolved material acceptance decision blocks that acceptance run rather than being chosen after observing its result.

Every numerical step delivers exact inputs/outputs, versions/hashes, native counts and uncertainty/unsupported-case limits. When numerical figures help, retain XY and XZ maximum-intensity projections **and** XY/XZ slices through one bead center selected from the frozen input catalogue before fitting. Record its identity, physical center and deterministic slice-index rule once. Use common physical axes, units and quantitative intensity scales; label any shape-only normalization. Preserve signed residuals, spectra/line profiles and both axial/lateral controls. Do not pick a brighter recovered peak or a more favorable slice after seeing results. Finer output spacing alone proves no resolution gain.

### RA01 — Freeze the benchmark and comparison contract

**PR:** Define the reference alignment benchmark and comparison manifest.

**Outcome/public contract.** One versioned, non-executable manifest defines selected ordinary single-objective linear 3D mode, five phases/three orientations, explicit optional flags and paired raw/calibration/reference artifacts. Start with the existing stationary synthetic model as a labeled assumption. Define algorithm alignment, stored-input numerical agreement, physical recovery and owner-output compatibility as distinct claims. The historical source/build record is not numerical evidence.

**Scope/non-goals and baseline.** Merged baseline plus immutable PR54 report; no product code, C invocation, gate/default changes or proof that owner settings are known. Inventory supplied C outputs and stage artifacts; mark absent items explicitly. Do not invent them or wait for them to complete independent controls. Report-only intake ownership of a new manifest/report.

**Comparison/inputs.** Full/small plans, raw camera/calibration/specimen manifests, original source/mean/evaluator identities, source snapshot, owner-provided raw inputs, OTFs, settings/logs and outputs where available. Require C source/build/platform identity if known; retain unknowns. Identify whether symmetry, sum equalization, Wiener estimation, padding and drift were enabled.

**Acceptance.** Every stage has an observed/proposed/unresolved status, units, phase/origin conventions and an independent expectation source. Comparison metrics, deterministic conversions, support/crop and tolerance derivation are specified before runs. Every missing input has an affected dependency. Preserve original PR53 errors without reclassification as a fixed result.

**Checks/deliverables/limits.** `git diff --check`; validate manifest references/hashes and frozen-plan geometry with read-only commands; exact-candidate full gate before a PR. Deliver mode matrix, convention dictionary, input manifest and decision register. No numerical figures needed. Unprovided real instrument settings and data remain external dependencies, not assumed defaults.

### RA02 — Match periodic known-parameter conventions and linear inverses

**PR:** Verify five-order conventions and matched spectral inverse controls.

**Outcome/public contract.** One tiny finite-periodic benchmark connects known phase separation, complex signed effective transfers, integer carriers and the resulting linear inverse. It compares the existing 2D and five-order 3D public operations with independently assembled real-coordinate observation equations and a solved tiny normal system. It must state when the current fusion is the same estimator and when phase/noise/alias multiplicities prevent that statement.

**Scope/non-goals and baseline.** RA01; high risk. A owns new independent alignment fixtures/tests. C may make only diagnosed in-contract corrections to `_phase.py`, `_volume_phase.py`, `_reconstruction.py`, `volume_reconstruction.py`; no fractional 3D, noise estimator, empirical optical inference or study optimization. An initially passing benchmark is valid and needs no manufactured defect.

**Comparison/inputs.** Hand-defined constant, displaced point, signed Fourier modes and asymmetric complex-transfer controls, exact finite DFT sums and a separately built matrix with declared units/origins. Include zero side orders, unequal nondegenerate phases, even Nyquist and known unequal order gains. Owner C intermediate bands are supplemental comparison data after a complete convention conversion, never the sole expected result.

**Acceptance.** Re-synthesis reproduces the declared observations; axis, first/second harmonic, phase gauge, conjugate reflection, DC/point amplitude and forward/adjoint identities hold under justified arithmetic budgets. Compare objectives, normal residuals and observable subspaces, not just output pixels. Include active/nonactive positivity and rank-deficient examples to demonstrate the boundary of equivalence, with explicit unsupported-mode meaning.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_phase_separation.py tests/test_volume_phases.py tests/test_reconstruction.py tests/test_volume_reconstruction.py`, new checkpoint tests and full gate. Deliver equations, conversion table, independently reproducible comparison and a frequency-placement figure if useful. This establishes only the matched periodic problem.

### RA03 — Isolate full-field forward and representation errors

**PR:** Isolate source sampling and illumination errors across all study exposures.

**Outcome/public contract.** One evaluator-only controlled comparison on the frozen sparse scene predicts all 15 noiseless exposures with a fixed known source while changing declared inputs one factor at a time. Separate the paired coarse source approximation from illumination error; no new source or nuisance fit occurs.

**Scope/non-goals and baseline.** RA02; high-risk custom comparison oracle. A owns expectations/fixture manifests; C owns only a new controlled evaluator and any separately diagnosed inverse-contract correction in `simulation_inverse_operator.py`. Original archived observations, fits and metrics remain immutable. No density change, post-hoc rescale/alignment or C parity claim.

**Comparison/inputs.** Original fine-source/mean archives, independently regenerated/hash-verified where available, known optical parameters, frozen estimated illumination, and current operator. Required arms include fine generator versus matched inverse basis at true illumination; paired source at true versus estimated illumination; original fitted source/prediction; then explicitly labeled carrier-only and phase-only substitutions where scientifically meaningful. Preserve unequal beams and origin transfer. Report unavailable original archives as a limit rather than silently substituting derived bundles.

**Acceptance.** Every exposure and one common-denominator aggregate are reported; source rounding, axial aggregation, pixel quadrature, kernel rounding and numerical application are distinguished. Extend the o0p0 observation without treating its errors as additive shares or an error floor. A displaced axial point and source-refinement controls establish source-minus-focus and half-cell signs; source/pixel/quadrature refinement changes are labeled discretization evidence, not resolution.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_simulation_inverse_operator.py tests/test_simulation_optics_coordinates.py tests/test_simulation_sources_cross_sections.py`, new evaluator tests and full gate. Deliver arm manifest, per-frame/aggregate metrics, rounding/representation ledger and fixed-center four-panel figures. No convergence/recovery promise follows from a forward match.

### RA04 — Preserve camera and intensity meaning

**PR:** Preserve camera and intensity units through the alignment path.

**Outcome/public contract.** One raw-correction composition gives specimen and bead frames a declared common gauge and propagates offset/response/exposure provenance exactly once. Connect existing acquisition, linear-response and scalar-camera operations; explicitly select or disable any reference sum equalization for the target mode.

**Scope/non-goals and baseline.** RA01–RA03; high risk. C owns the narrow correction/composition adapter and only diagnosed changes to `_linear_response.py`, `_scalar_camera_calibration.py` or study handoff. A owns camera/exposure fixtures. No automatic saturation repair, bleaching model, clipping, calibrated-photon claim or noise removal is added. Enable no C camera-specific pixel heuristic without its own applicable public case.

**Comparison/inputs.** Independently stated `counts=offset+gain*signal` controls; supplied dark/blank/flat arrays or estimated records; explicit exposure factors and corrected-count units. Use known metadata first, then image estimates. Test carrier-rich sparse objects against any proposed sum normalization assumption.

**Acceptance.** Constant/point intensity and common signal scale survive correction and reconstruction; signed corrected samples remain valid. Blank shot noise is retained in uncertainty, and unknown absolute gain does not masquerade as photons. Scalar/map shape, bad response, nonfinite/range and metadata contradictions have explicit outcomes. If exposure equalization is unsupported or scientifically invalid for the chosen inputs, report that mode as unavailable.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_linear_response_correction.py tests/test_scalar_camera_calibration.py tests/test_image_only_specimen_fit.py`, adapter tests and full gate. Deliver unit-chain table and known/estimated gauge comparison; figures only if they explain a measured effect. No real instrument calibration is established by synthetic moments.

### RA05 — Calibrate and consume matched order transfers

**PR:** Calibrate and consume matched complex order transfer functions.

**Outcome/public contract.** One known-phase, known-carrier calibration path converts corrected bead data into common-scale signed order responses and samples them on declared specimen frequencies. Retain order-zero/one/two amplitude, phase, bead anchor and phase gauge. Reuse existing empirical and physical-frequency primitives rather than redesigning them.

**Scope/non-goals and baseline.** RA02–RA04; high risk. C owns a calibration/consumption adapter plus diagnosed corrections to `_point_bead_calibration.py`, `_finite_bead_calibration.py` and empirical transfer modules. A owns independent profiles/OTFs. Start with point and declared discrete profile controls; select continuous-sphere compatibility only when the owner mode supplies the profile/sampling interpretation. Radial averaging/support cleanup are explicit mode choices; no arbitrary pupil or unknown-phase self-calibration here.

**Comparison/inputs.** Independent finite-sum effective kernels `h*g_m`, off-center asymmetric beads, point-profile limit and supplied C calibration intermediates/settings where available. Compare pre/post centering, bead division at order-shifted object frequencies, common normalization and separate calibration/specimen grids. Challenge weak/zero profile transfer and endpoint coverage.

**Acceptance.** Known synthetic order transfers and their predicted exposures agree within propagated discretization/arithmetic bounds. No independent per-order normalization, magnitude-only projection or second pixel integration is hidden. Preserve unequal beams, complex axial profiles and explicit physical-frequency negative reflection. Near profile zeros or out-of-grid queries give declared information failures, not epsilon-filled data.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_volume_order_otf.py tests/test_raw_point_bead_calibration.py tests/test_finite_bead_compensation.py tests/test_empirical_transfer_adapter.py tests/test_empirical_frequency_sampling.py`, adapter tests and full gate. Deliver complex order-plane/phase plots, bead correction and sampling provenance. Known phase/profile premises are limits, not inferred instrument facts.

### RA06 — Weight separated noise and define Wiener units

**PR:** Add covariance-aware weighting and explicit Wiener units.

**Outcome/public contract.** One additive known-parameter reconstruction estimator propagates a declared exposure covariance through separation and implements the resulting weighted linear inverse. Define the diagonal generalized Wiener special case and relation between its denominator penalty and the raw-exposure objective; specify output taper separately.

**Scope/non-goals and baseline.** RA05; high risk. A owns independent covariance/normal-system fixtures. C owns a new weighted fusion module or narrowly additive `volume_reconstruction.py` boundary, preserving the original public estimator. No copied automatic Wiener heuristic, truth-selected λ, generic Poisson likelihood or optimality claim under undeclared noise. An empirically selected C setting is compatibility metadata.

**Comparison/inputs.** RA02 real matrix, exact phase-design covariance transformation and analytic diagonal cases. Include unequal phases, correlated separated components, real/negative-band dependence and differing exposure variances. Compare C noise factors only after deriving their convention.

**Acceptance.** Unweighted/diagonal limits and complete weighted normal equations agree on observable modes; scaling gains/covariance/λ has the declared effect. Invalid covariance, singular-information outcomes and zero regularization have specified behavior. A noise realization cannot choose its own acceptance threshold or exploit hidden truth. Distinguish stored-input estimator agreement from expected reconstruction risk.

**Checks/deliverables/limits.** Existing `tests/test_volume_reconstruction.py`, new weighted/covariance checkpoint tests via `uv run --locked pytest <checkpoint-files>`, full gate. Deliver covariance derivation, penalty conversion and residual/noise spectra. The placeholder denotes exact files named at intake; no new command currently exists. Signal-dependent photon noise may require a later explicitly selected approximation; do not imply a constant Wiener parameter is its exact optimum.

### RA07 — Relocate fractional 3D bands

**PR:** Recombine fractional volume bands with verified filter ordering.

**Outcome/public contract.** One additive volume recombination operation accepts known physical noninteger carriers with a declared finite-window interpolation/phase-ramp representation, OTF queries, output origin and normalization. Define whether it reproduces the reference's filter-before-shift estimator or another justified estimator.

**Scope/non-goals and baseline.** RA06; high risk. A owns fractional Fourier/phase-ramp fixtures; C owns the new fractional fusion adapter and necessary physical-frequency sampling use. No carrier estimation, finite-exterior assumption or silent reinterpretation of existing integer-bin APIs. Fractional observation interpolation is distinct from existing transfer interpolation.

**Comparison/inputs.** Direct finite DFT sums, analytic off-bin waves and independent tiny dense synthesis, including negative carriers, odd/even sizes, Nyquist boundaries and asymmetric complex OTFs. Compare filter-before/after-shift only under their stated models; off-bin window smearing can make them differ.

**Acceptance.** Integer limit recovers the accepted integer operation under identical normalization/support; general fractional cases satisfy the chosen finite model and adjoint. No wrap/crop losses, duplicated negative bands or phase-origin ramps are hidden. Demonstrate full complex and amplitude agreement, not only magnitudes. Declared out-of-support cases fail or remain unavailable explicitly.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_volume_reconstruction.py tests/test_empirical_frequency_sampling.py`, new fractional checkpoint tests and full gate. Deliver a fractional-frequency placement/smearing comparison and physical-coordinate example. Finite-window correctness is not a continuum bandwidth or resolution guarantee.

### RA08 — Match finite boundaries and solve the declared objective

**PR:** Make finite-field reconstruction boundaries and convergence explicit.

**Outcome/public contract.** One finite-field reconstruction mode declares exterior, source box, detector crop, input taper, padding, output taper/zoom and brightness convention, then solves its corresponding objective with a recorded convergence criterion. Preserve the periodic spectral estimator as a separate documented mode when its normal equations differ.

**Scope/non-goals and baseline.** RA03 and RA07; high risk. A owns finite-boundary/optimization fixtures. C owns a finite-field adapter and scoped solver change in `simulation_inverse_operator.py` / `image_only_specimen_fit.py` or a new named solver. No automatic bigger scene, fitted output alignment or unbounded retry. Choose precision, regularization, positivity and mathematical stopping criteria at intake; do not simply increase the historical 12-step limit and call it alignment.

**Comparison/inputs.** Independently summed exterior-zero tiny matrix and its real adjoint, boundary/corner emitters, interior controls, declared windows and exactly solved small constrained/unconstrained systems. Compare periodic and zero-exterior predictions with the same fixed source. Test padding versus crop and input window versus final apodization separately.

**Acceptance.** Finite convolution, observable objective and gradient/optimality residual match their independent controls. Report solver convergence versus resource/iteration stops; active nonnegativity is labeled estimator divergence from linear Wiener. Known-source nullspace and discretization floors are reported independently of source error. A still-decreasing objective or a finer grid is never a convergence/resolution certificate.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_simulation_inverse_operator.py tests/test_image_only_specimen_fit.py tests/test_simulation_reconstruction_resources.py`, new boundary/convergence tests and full gate. Deliver matched-boundary figure, fixed-center sections and objective/stationarity histories. Physical exterior outside the supplied specimen field remains unknown for real data.

### RA09 — Fit specimen carrier and complex overlap gains

**PR:** Refine specimen carriers and complex gains from spectral overlap.

**Outcome/public contract.** One continuous physical-carrier/relative-order-gain fit consumes known-phase separated specimen bands and fixed calibrated responses. It reports carrier, complex corrections, overlap/information diagnostics and ambiguity. Carrier search and gains share one declared specimen-overlap objective; do not split their coupled meaning into inconsistent baselines.

**Scope/non-goals and baseline.** RA05 and RA07–RA08; high risk. A owns oracle/overlap scenes. C owns a new continuous overlap estimator, composing `volume_order_gain.py` and physical-frequency sampling where valid. No arbitrary unknown phase-step, pupil, brightness or raw-motion fit. Nominal carriers and search policy must be observation metadata, not supplied truth masquerading as an estimate.

**Comparison/inputs.** Analytic paired Fourier modes and independent finite-model likelihood/complex regression. Begin with noiseless known phases and informative overlap; then noise. Compare integer-gain baseline, C's order-pair choice and field-wide phase drift from calibration-fitted q. Include aliases, insufficient support, zero predictor and non-global/local outcomes.

**Acceptance.** Recover or correctly mark unavailable the declared identifiable cases; verify full-field phase prediction, not only a small bead-window residual. Separate carrier error from common phase/gain ambiguity. Report search/stationarity diagnostics without treating a sole candidate or local optimum as physical uniqueness. Validate against independently generated frames or held-out overlap regions where the model permits.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_volume_order_gain.py tests/test_volume_carrier_diagnostics.py tests/test_volume_carrier_selection.py`, new continuous tests and full gate. Deliver overlap/support plots and phase-error maps over the fixed field. No universal carrier guarantee outside declared information/search conditions.

### RA10 — Resolve exposure phase errors in the fixed calibration gauge

**PR:** Estimate exposure phases without changing the calibration gauge.

**Outcome/public contract.** One phase-inference composition handles actual exposure phases with the carrier/transfer representation now fixed. Compare a common starting offset with independent phase deviations and expose the information/gauge requirements. Known phases remain the mandatory positive control.

**Scope/non-goals and baseline.** RA06, RA09; high risk. A owns independently generated phase cases; C owns an additive compatible phase adapter and scoped changes to `_volume_phase_estimation.py`, `_observable_volume_phase_estimation.py` or `_fourier_block_phase.py`. Existing native periodic nuisance models cannot silently be used for the larger nonwrapping/fractional model. No joint unconstrained pupil or motion inference.

**Comparison/inputs.** Independent raw finite-sum data, actual phase monitor metadata if supplied, nominal command-only initializations and independently fixed calibration gauge. Include five-frame ambiguities, redundant exposures and weak/strong informative cases. Existing [raw calibration identifiability](../reports/raw-calibration-identifiability.md) results are coordinator context, not a claim that all images-only inputs are identifiable.

**Acceptance.** Show which independent per-exposure errors the estimator can resolve, full objective agreement and phase information/rank behavior. Do not infer phases from a square five-band fit with arbitrary unknown order responses. Report equivalent phase/beam gauges and unavailable cases; validate predicted held-out exposures before declaring corrected illumination. No hidden truth selects initialization, gauge or solver success.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_volume_phase_estimation.py tests/test_observable_volume_phase_estimation.py tests/test_fourier_block_phase_estimation.py`, adapter tests and full gate. Deliver actual-vs-commanded phase diagnostics in a predeclared gauge and prediction comparisons. Local rank/stationarity is not global uniqueness.

### RA11 — Validate the applicable motion boundary

**PR:** Validate comparable-reference drift and illumination phase correction.

**Outcome/public contract.** For stationary synthetic inputs, document and demonstrate the no-motion branch. For a supplied owner mode that requires drift, one concrete motion mechanism and comparable reference construction determine displacement and the corresponding illumination/axial correction. A later different motion mechanism is outside this task.

**Scope/non-goals and baseline.** RA08, RA10. Stationary applicability only: report-only intake. Numerical motion estimator/correction: high-risk A/B/C/D; C owns its named adapter plus scoped `_translation.py`, `_volume_translation_estimation.py` or `_drift.py` changes; A owns reference/motion fixtures. No arbitrary optical flow, within-stack nonrigid motion or drift claim for PR53.

**Comparison/inputs.** Known displacements of a finite phantom and independent raw synthesis under the selected specimen/camera/focus mechanism; acquisition timing and comparable references. Existing periodic integer helpers supply limit controls. A phase sum is comparable only when its illumination cancellation and intensity assumptions hold.

**Acceptance.** No-motion inputs receive no physical correction; known motion aligns the declared specimen and correctly changes illumination phase, without confusing moving specimen and moving camera. Low-information or changing-intensity references return ambiguity/unavailability. Raw unlike-phase cross-correlation alone is insufficient. Unsupported required owner motion blocks that owner mode.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_translation.py tests/test_volume_translation_estimation.py tests/test_integer_drift.py`, applicable new motion tests and full gate; stationary report uses reference/diff checks plus gate. Deliver applicability matrix and motion/phase comparison when numerical. No fractional/axial motion is implied by an integer lateral result.

### RA12 — Establish the images-only calibration handoff

**PR:** Transfer identifiable calibration responses into specimen reconstruction.

**Outcome/public contract.** One observation-only handoff yields the relative transfer/illumination quantities needed by the selected specimen mode, with phase origin, carrier sign/side exchange, common intensity scale and calibration-to-specimen coordinate transfer fixed exactly once. The current clear-pupil finite three-beam model is the initial labeled synthetic assumption; measured empirical optics need their own supplied calibration information.

**Scope/non-goals and baseline.** RA04–RA05, RA09–RA11; high risk. A owns public observation bundles and independent predictive cases. C owns one calibration/handoff adapter, composing `image_only_bead_calibration.py`, the accepted order-response path and specimen refinements. No true bead positions, phases, camera coefficients or OTF arrays enter the observation-only inference path. A known-input diagnostic is labeled separately.

**Comparison/inputs.** Calibration raw frames, real declared metadata, independently acquired/held-out phase or bead data, and the accepted finite-model controls. Test predictive alternatives that fit calibration equally well but differ on specimen exposures. Resolve material nonidentifiability with available independent information or report the handoff unavailable; a smooth fit is not an answer.

**Acceptance.** The same physical illumination predicts both calibration and specimen coordinate systems, preserving common gauge/scale and uncertainty. Test side exchange, nonzero origin, unequal beam powers and actual step errors. Held-out calibration performance and field-wide specimen predictions are separate. Observationally equivalent but specimen-changing alternatives prevent a claim of identified calibration. Do not add an unsupported instrument premise to force success.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_image_only_calibration_pilot.py tests/test_image_only_bead_calibration.py tests/test_raw_point_bead_calibration.py tests/test_finite_bead_compensation.py`, new handoff tests and full gate. Deliver provenance/uncertainty record, held-out predictions and calibration-to-specimen phase maps. Missing informative observations can block this step's image-only mode; they do not invalidate known-parameter alignment controls.

### RA13 — Integrate the raw pipeline at its public boundary

**PR:** Integrate calibrated raw SIM reconstruction with full provenance.

**Outcome/public contract.** One documented public workflow consumes raw specimen/calibration arrays or explicit existing file declarations plus allowed metadata and produces reconstruction, nuisance diagnostics and complete provenance. It composes the accepted stages without new estimator meaning. Start with the small fixed case; run the full expensive benchmark in RA14.

**Scope/non-goals and baseline.** RA06–RA12 completed in one exact baseline; high risk because composition changes scientific behavior/interfaces. A owns end-to-end observation-only acceptance fixtures and truth-access checks. C owns the named workflow/CLI adapter and records, using `full_noisy_study.py`'s separation of generate/infer/evaluate as applicable. No imported private truth, silent fallback, output rescale or new tuning search.

**Comparison/inputs.** RA02–RA12 independent control bundles and small raw synthetic acquisitions; old driver remains a historical comparison arm. Truth lives in a separate evaluator. Require declared calibration/specimen pairing, axis/order, spatial units and supplied-versus-estimated labels.

**Acceptance.** Public-entry output matches accepted component composition, phase and gain corrections occur once, no stage receives hidden truth, and unavailable/ambiguous inputs propagate explicitly. Complete known-parameter noiseless and observation-only noisy small controls must pass before the full run. Malformed metadata, incompatible grids, calibration coverage and operation failures have documented behavior.

**Checks/deliverables/limits.** `uv run --locked pytest tests/test_full_noisy_study.py` plus new public-workflow checkpoint tests and full gate. Deliver executed usage, exact small-case outputs and stage diagnostics; retain fixed-center figures when informative. Component acceptance does not itself prove the integrated workflow or improve physical resolution.

### RA14 — Demonstrate full-scene method alignment

**PR:** Demonstrate full-scene recovery and reference-method alignment.

**Outcome/public contract.** One predeclared controlled full-scene experiment evaluates the frozen 27-object specimen using the integrated pipeline and accepted matched-model reference method. Report known-parameter/noiseless, estimated-parameter/noiseless and estimated-parameter/noisy arms on the same scene before claiming the calibration/estimation/noise gaps are closed. Keep the PR53 result as the poor-recovery baseline.

**Scope/non-goals and baseline.** RA13; high-risk custom evaluation/oracle and any new scientific orchestration. A owns predeclared evaluation expectations/manifests; C owns only a named experiment/evaluator wrapper, not component repairs; diagnosed defects return to their owners. No density experiment, truth-tuned λ, best-seed selection, new convergence claim from a hard stop or C parity without corresponding supplied output.

**Comparison/inputs.** Original full plan/seeds and raw archives; matched synthetic controls, separate private truth and frozen estimator settings. Compute all 15 exposure predictions. Keep original source and image metrics alongside observable-mode/source-basis-aware diagnostics. Match wide-field conventional controls, photon/exposure budget, grid and optical assumptions before comparing resolution.

**Acceptance.** All mandatory arms produce complete reproducible stage metrics or an explicit scientifically meaningful failure; success requires meeting RA01's predeclared justified accuracy/uncertainty criteria, not merely producing files. Distinguish training residual, held-out predictive evidence, coefficient error, observable-spectrum recovery and resolution evidence. Demonstrate recovery of known transferred spatial information or predeclared resolvability controls against the matched conventional baseline; do not infer resolution from 40 nm output spacing. If criteria fail, report failure and route diagnosed corrections before labeling alignment complete.

**Checks/deliverables/limits.** Full gate plus the exact frozen generate/infer/evaluate commands recorded by RA13/RA14 intake; existing historical syntax is in the [study report](../studies/full-noisy-study-2026-10-26/README.md#reproduction-and-evidence). Do not invent flags for future operations. Deliver full JSON/array manifests, per-frame residual/transfer spectra, XY/XZ projections and fixed bead-center slices, quantitative profiles, convergence and per-stage time/memory. One sparse scene and one realization establish no universal noise robustness or empirical instrument accuracy.

### RA15 — Demonstrate owner-output parity and adjudicate differences

**PR:** Validate owner-data reference parity and document supported differences.

**Outcome/public contract.** One exact set of owner-provided raw calibration/specimen cases, settings and corresponding C outputs is processed through the accepted Python workflow. Compare complete volumes and stage artifacts after only declared deterministic convention/unit conversions. Report compatibility and independent scientific accuracy separately.

**Scope/non-goals and baseline.** RA14 plus paired owner inputs and resolved acceptance choices; high-risk custom comparison/oracle. A owns independent comparisons and public-safe/authorized fixtures; C owns only the comparison adapter and scoped format mappings. No C invocation, rebuild or bundled executable use; no silent reproduction of suspected C defects, fitted registration/brightness/crop for acceptance or generalization beyond supplied cases. Private data stays local unless separately authorized.

**Comparison/inputs.** Raw specimen and raw bead/PSF frames, acquisition metadata, bead geometry, camera corrections, exact C option/config/log records, C output arrays/grids/types/units, source/build identity where known and intermediate OTF/carrier/phase artifacts if available. Output-only files with unknown raw/settings provenance can support a limited comparison, not full pipeline parity.

**Acceptance.** Before acceptance runs, settle supported modes, alignment origin, intensity conversion, support/crop, expected real/complex output, negative values and empirically justified tolerances. For every discrepancy identify first differing stage and classify equivalent coordinates, justified model/estimator difference, Python defect, suspected C defect or missing requirement. Unsupported modes and missing evidence stay explicit. A failed comparison returns to a diagnosed owned task; compatibility is not obtained by truth-fitting away disagreement.

**Checks/deliverables/limits.** Exact-candidate full gate, RA13 workflow commands and the frozen owner-case comparison command defined at intake. Deliver private-safe provenance manifest, per-case/stage metrics and fixed-center four-panel figures where a known reference center exists, unresolved-difference ledger and supported-mode usage. Completion requires the agreed owner cases to meet their contract. Until the owner inputs exist, final C/Python numerical parity remains unproven.

## What would change the sequence or conclusion

Confidence is high that the current library contains the principal harmonic/transfer/recombination foundations and that the full noisy study uses a different finite model and estimator. Confidence is high in the retained o0p0 measurements: **1.6988%** known-source/true-illumination image error, **45.6367%** at the same source with frozen estimated illumination, and **66.3078%** for the original fitted-source prediction on that denominator. They do not identify the causal shares of the full 15-exposure **66.4%** error; the original source error remains **95.3%**. Twelve accepted source updates ended at the preset limit, not established convergence.

Matched known-parameter controls could show that a suspected convention discrepancy is only a coordinate transformation, eliminating a proposed correction while retaining the comparison task. Full15 controls could shift emphasis from illumination toward source representation, boundaries or solver precision. Supplied C settings could make radial calibration, exposure normalization or motion necessary, or show that those paths are outside the requested mode. Independently demonstrated nonidentifiability could require an actual phase/calibration measurement before RA12. None of these possibilities authorizes inventing a new scientific premise, lowering a gate or replacing failed evidence with more iterations.
