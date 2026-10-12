# Scientific migration roadmap: raw acquisitions to reference parity

**Version 1.0.** Git versions revisions. Baseline updated after owner integration on October 10, 2026, 22:01 UTC.

The endpoint is one independently written Python pipeline: the owner supplies raw structured illumination microscopy (SIM) specimen data and raw point spread function (PSF)/bead calibration acquisitions, with metadata and settings; the pipeline calibrates, estimates, corrects and reconstructs them. Its output is compared with the owner's corresponding SIMrecon_svn C-reference outputs. Matching those supplied outputs is a delivery objective; independent scientific correctness needs its own evidence.

This amendment plans the remaining work. It implements no scientific feature, chooses no unresolved numerical contract and changes no delivery rule. Reuse the [approved architecture](PROJECT.md). Every new scientific slice needs concrete intake, independent expectations and the existing high-risk reviews. A planned dependency becomes usable only when completed and integrated in its execution baseline. Merge/release remains an owner action.

Study the ignored `SIMrecon_svn/` source as read-only algorithm/format evidence. Write Python independently; do not copy, import, link or ship that tree. **Do not compile, build, invoke or execute any reference C program or bundled executable, in this task or these planned phases.** Comparisons use owner-provided reference outputs. Missing owner datasets do not block this plan.

<a id="integrated-work-open-stack-and-genuine-gaps"></a>

## Merged execution baseline, stack history and genuine gaps

The earlier live GitHub read on October 10 found fourteen open, unmerged pull requests (PRs) in the rebased dependency chain below. That is a historical snapshot: the owner merged all fourteen on October 10, 22:01 UTC. Their descriptions report independent review and local verification; this roadmap is not a fresh audit of all historical scientific evidence. The local maintenance record is `artifacts/stack-maintenance-20261010/CURRENT.md`; it gives context, not permission to modify those candidates. Exact observed heads/bases are retained in this amendment's [task evidence](tasks/scientific-migration-roadmap.md#current-state).

The owner initially requested this amendment and phase 1 above PR #21, `codex/imagej-adapter-intake` at `d3ba7639ebec99dd67026332771fad99cf452d51`, then reported that the stack was merged. The execution baseline is now merged `main`, `8f7148d405ade2a71da554b881a7153a2a66d6c9`; its tree exactly equals the PR #21 candidate tree, `88e46436701c5b634ec2fb9aa49a3596a2e0a934`. All fourteen completed component candidates are present. The owner used squash merges, so the roadmap commit is replayed onto merged main to preserve a documentation-only PR diff. The continuation is **merged main → roadmap PR #22 → phase 1**. Preserve the old PR branches and records; the coordinator performs no old-stack rewrite or merge. Inspect applicable accepted evidence before reuse. Further merge/release remains an owner action.

For this continuation, the owner explicitly retained PR #21’s reviewed advisory coverage policy. Full exact-candidate local verification and complete native measurement/report integrity remain required; this amendment changes no gate.

Before this stack integration, `main` at `a44e9d0c67403d5a001340b65ba04ea2f559256a` included [MRC conversion, PR #2](https://github.com/david-hoffman/simrecon/pull/2), [explicit known-phase 2D separation, PR #5](https://github.com/david-hoffman/simrecon/pull/5), and [2D PSF/OTF calibration contracts and fixtures, PR #6](https://github.com/david-hoffman/simrecon/pull/6). MRC denotes the microscopy volume file format; OTF means optical transfer function. PR #6 supplies foundations, not calibration runtime.

| Completed stack, now merged, in dependency order | What it adds | Remaining boundary |
|---|---|---|
| [#7](https://github.com/david-hoffman/simrecon/pull/7) → [#8](https://github.com/david-hoffman/simrecon/pull/8) | Supplied intensity-PSF 2D OTF preparation; known-parameter 2D reconstruction, including fractional wavevectors with bilinear spectral interpolation. | Supplied corrected PSF, origin and parameters; detector-matched calibration grid. Fractional 2D interpolation has documented approximation limits. |
| [#9](https://github.com/david-hoffman/simrecon/pull/9) | Reviewed delivery policy with advisory coverage percentages, inherited in this execution baseline. | Policy work, not a scientific capability. The owner retained it for this continuation; this roadmap alters no gate. |
| [#11](https://github.com/david-hoffman/simrecon/pull/11) → [#12](https://github.com/david-hoffman/simrecon/pull/12) → [#13](https://github.com/david-hoffman/simrecon/pull/13) | Known-integer-carrier phase/modulation fit, caller-listed carrier scan and sole-candidate selection with caller limits. | First-harmonic 2D model, supplied relative phase steps; no continuous carrier refinement or independent step estimation. |
| [#14](https://github.com/david-hoffman/simrecon/pull/14) → [#15](https://github.com/david-hoffman/simrecon/pull/15) | Periodic equal-intensity reference translation; known integer specimen-drift preparation with phase correction. | No automatic motion inference from differing raw SIM phases; no fractional/3D physical drift model. |
| [#16](https://github.com/david-hoffman/simrecon/pull/16) → [#17](https://github.com/david-hoffman/simrecon/pull/17) | Known-phase five-order volume separation; supplied 3D intensity-PSF OTF preparation. | Calibration preprocessing, origins, phase knowledge and measured instrument response remain external. |
| [#18](https://github.com/david-hoffman/simrecon/pull/18) → [#19](https://github.com/david-hoffman/simrecon/pull/19) → [#20](https://github.com/david-hoffman/simrecon/pull/20) | Effective order transfers from supplied axial profiles; known-parameter volume recombination; relative complex gain fit for order 1 or 2. | Finite periodic model, integer lateral carriers, native axial sampling and detector-matched OTF grids. Supplied profiles are not empirical bead calibration. |
| [#21](https://github.com/david-hoffman/simrecon/pull/21) | Fiji viewing export retaining illumination settings. | Viewing adapter, not reconstruction-result persistence or a complete raw pipeline. |

The [2D calibration contract](contracts/otf-calibration-v1.md) starts from an already corrected nonnegative intensity PSF with a supplied origin. The stacked [effective-order contract](https://github.com/david-hoffman/simrecon/blob/d3ba7639ebec99dd67026332771fad99cf452d51/docs/contracts/volume-order-transfers-v1.md) starts from a detection PSF and supplied axial profiles, with an axial zero-order profile fixed to one. Neither implements empirical phase-resolved SIM bead calibration.

Read-only source locators are relative to the local ignored `SIMrecon_svn/` tree:

| Observation | Evidence and interpretation |
|---|---|
| Empirical 3D `radialft` calibration | `mainfile.c:23,84,346–358`: five default phases and equally spaced separation weights. `176–321`: raw background/camera correction, localization, separation, centering, finite-bead compensation, radial averaging, support/cleanup and scaling. The general Python separator's unequal-phase support does not change this source assumption. |
| Scientific choices inside that calibration | `mainfile.c:412–517` uses peak/parabolic bead localization; `705–758` compensates a finite sphere; `805–969` averages/enforces symmetry and cleans support. `1114–1130` normally scales from the maximum magnitude of order zero, not necessarily its zero-frequency value. These are investigation targets, not automatically adopted defaults. |
| Independent calibration grids | `mainfile.c:147–148,1009–1035` derives/writes its own sampling. `helpers.c:747–786` reads separate OTF dimensions/frequency increments. `sirecon.c:1410–1414` computes the specimen/OTF axial frequency-spacing ratio; `small_math_funcs.c:396–480` interpolates radial/axial or Cartesian complex OTFs. |
| Current consumption gap | The stacked [volume recombination contract](https://github.com/david-hoffman/simrecon/blob/d3ba7639ebec99dd67026332771fad99cf452d51/docs/contracts/volume-recombination-v1.md) requires detector-sized canonical OTF grids and excludes fractional placement/axial resampling. Calibration and specimen grids therefore need an additional contract. |

## Ordered phases

Phases 1–7 close and integrate the component gaps. **Phase 8 is the penultimate full simulation. Phase 9 is the final real-data/reference validation.** Small analytic examples support earlier phases and cannot replace phase 8.

### 1. Reconcile prerequisites and identify the target acquisition

This turns the useful component stack into a precise execution baseline and identifies the reference mode to reproduce.

The [phase-1 reconciliation manifest](plans/scientific-phase1-baseline.md), [acquisition/settings matrix](plans/scientific-phase1-acquisition.md), [decision register](plans/scientific-phase1-decisions.md) and [ordered planning packets](plans/scientific-phase1-packets.md) record the merged baseline above final PR #22. These documentation deliverables do not settle target settings or the new scientific contracts; full phase-1 exit remains pending. [Task/authority and evidence pointer](tasks/scientific-phase1-intake.md).

1. Record merged main’s exact baseline, the corresponding completed component contracts and applicable accepted evidence. Retain historical PR candidate identities separately from squash-merge identities. Use the present prerequisites; identify genuinely missing dependencies without reopening completed components. Preserve old branches and historical accounting. Future merge/release remains an owner action.
2. Make a target-mode/settings matrix from source text and available owner provenance: raw section ordering, channels/time, phases/orientations, illumination orders, calibration type, corrections and output geometry.
3. Create a decision register for phases 2–9. Complete relevant source/paper method notes where needed; full-paper extraction and viewing polish are not independent prerequisites for every slice.

**Dependencies:** approved architecture and merged main’s completed components/public contracts. **Deliverables:** baseline manifest, capability/gap matrix, source locators and ordered slice packets. **Exit:** each dependent slice has completed prerequisites and a concrete behavior contract; unprovided settings remain pending, never guessed. Missing experimental files permit planning to continue.

### 2. Raw specimen/calibration intake and correction provenance

This adds the information required to interpret acquisitions, beyond preserving pixels in a conversion or viewing copy.

1. Define one public array/metadata boundary for specimen and calibration. Declare orientation/phase/z/y/x plus channel/time handling, acquisition order, physical units, wavelengths, nominal phase commands and calibration identity. Preserve original metadata and overrides.
2. Connect existing MRC intake where applicable. Map sections explicitly; distinguish a raw detection-PSF stack from a raw phase-resolved SIM bead stack. Never silently infer phase ordering or flatten dimensions.
3. Inventory constant/per-plane background, dark/flat-field/gain maps, exposure differences, saturation/bad pixels, bleaching and timestamps. Contract required corrections, ordering and absent/invalid metadata outcomes for the target mode. Simulator and pipeline camera inputs need the same declared units.

**Dependencies:** phase 1; stable conversion interfaces. **Deliverables:** raw-input/metadata contract, format mapping and provenance report, public-entry valid/invalid examples. **Exit:** raw specimen and raw calibration arrays have unambiguous physical interpretation; no estimated quantity masquerades as known metadata.

### 3. Empirical 3D SIM bead calibration

This replaces caller-prepared response with response measured from raw calibration exposures.

1. Specify the raw calibration acquisition and bead properties. Trace background/camera corrections, bead selection/localization, phase/orientation order and origin compensation.
2. Define zero-, first- and second-order separation and signed complex order-specific 3D OTF formation. Resolve radial averaging, bead-size compensation, support cleanup, phase gauge/conjugation and relative normalization for the target reference settings. Address any axial zero-order profile excluded by the current `g0=1` model.
3. For the `radialft` compatibility path, record equally spaced phases, five by default. Decide supported counts, deviations from commanded phases and rejection or alternate-path behavior before tests. Unequal-phase empirical calibration needs its own justified contract.
4. Retain ordinary detection-PSF-to-OTF preparation where separately needed. It cannot substitute for raw SIM calibration or recovery of unknown axial order profiles.

**Dependencies:** phase 2 and integrated separation/calibration foundations. **Deliverables:** empirical calibration contract and public operation, independent bead/order fixtures, diagnostics and provenance. **Exit:** raw bead arrays produce documented order transfers with independent sign, origin, scaling and order checks; questionable source behavior is an explicit compatibility decision or remains unresolved.

### 4. Independent OTF sampling and interpolation

This allows calibration and specimen acquisitions to have different grids.

1. Define radial/axial or full 3D complex coordinates in cycles/µm, order/orientation mapping, origin/gauge and negative-order representation.
2. Contract interpolation onto reconstruction/overlap coordinates, including complex phase, support, Nyquist endpoints and out-of-grid outcomes. Distinguish physical zero support from missing calibration coverage.
3. Demonstrate different dimensions, lateral spacing and axial spacing with analytic complex transfers and held-out cases. Apply origin phase and relative order gain exactly once.

**Dependencies:** phase 3's transfer meaning and phase 1's target representation. **Deliverables:** transfer-consumption/interpolation contract, integration and independent grid tests. **Exit:** calibration dimensions/spacing need not equal specimen inputs; interpolation error is separately measured and justified.

### 5. Specimen parameter estimation, drift and corrections

This supplies quantities the current known-parameter volume path requires from its caller.

1. Extend estimation to the selected 3D model: carrier direction/magnitude with continuous refinement as needed, per-orientation phase offsets, order-specific complex gains and independently unknown phase-step deviations.
2. Establish identifiability, aliasing and weak-overlap diagnostics. Coherence or a low residual alone proves no physical parameter accuracy. Resolve estimator objectives and ambiguous/no-information outcomes before tests.
3. Establish comparable references for drift; contract required fractional lateral/axial and between-phase/orientation/time corrections. Track their interaction with illumination phase and axial profiles. Periodic integer 2D helpers remain narrow prerequisites.
4. Integrate phase-2 corrections, including rescaling/bleaching or instrument maps only where target settings require them. Record supplied, estimated and applied values separately.

**Dependencies:** phases 2–4 and integrated estimation/reconstruction foundations. **Deliverables:** estimator/correction contracts, diagnostics, independent synthetic observations and correction provenance. **Exit:** required nuisance quantities are estimated without supplied truth; ambiguous inputs get contracted outcomes; signs, units and correction order are independently checked.

### 6. Reference-compatible 3D reconstruction and output

This closes the difference between finite-grid known-parameter recombination and the selected experimental mode.

1. Specify fractional 3D band positioning, OTF interpolation, weighting and noise treatment. Resolve generalized Wiener/regularization and apodization conventions. Ridge and explicit masks already exist; they do not establish equivalence to every legacy setting.
2. Contract lateral/axial output sampling, padding, zoom, cropping, boundaries and intensity normalization. Decide real/complex output, imaginary residue, negative values and enabled legacy options from source/owner evidence.
3. Validate composition with independent small forward cases: order/sign/gauge, overlap, missing frequencies, weak/zero transfer, boundaries, aliasing and regularization bias. Preserve existing narrow APIs or explicitly contract compatibility changes.
4. Define result arrays and needed file/metadata adapters separately. Reuse conversion/viewing components where applicable; existing Fiji acquisition export does not accept reconstruction arrays. Record settings, calibration and estimates with every result.

**Dependencies:** phases 3–5 and integrated volume recombination. **Deliverables:** selected-mode reconstruction/output contracts, operation, independent geometry/numerical evidence and signed comparisons. **Exit:** the requested mode has no hidden caller-required scientific quantity; numerical estimator accuracy is distinguished from physical recovery and reference parity.

### 7. One public raw-input workflow and small complete demonstrations

This composes calibration and reconstruction into the route experimental data will use.

1. Expose a stable public workflow accepting raw specimen arrays, raw bead arrays, legitimate metadata and explicit settings. Invoke empirical calibration, estimation/corrections and reconstruction; file entry points use the same numerical route.
2. Add complete independent analytic cases: constant/point objects, supported Fourier modes, translated beads/order phases and zero/no-information cases. Include mismatched calibration grids, off-model input and declared failure paths.
3. Define input identities, intermediate diagnostics and output provenance. Establish an allocation strategy before the large run from measured needs, without inventing a memory limit.

**Dependencies:** phases 2–6 completed and integrated. **Deliverables:** public workflow contract/usage, end-to-end fixtures, reproducible report and resource plan. **Exit:** both raw acquisitions run through the public entry point without precomputed OTFs or manually supplied estimates.

### 8. PENULTIMATE — full end-to-end 3D simulation

This demonstrates the complete workflow on a realistic volume after the small mathematics works.

**Required specimen:** approximately **512 × 512 × 64 voxels (x/y/z)**, NumPy **`(64, 512, 512)`**. Include nonnegative curved filaments, membranes/shells, puncta and diffuse fluorescence at varied depths, orientations and intensities. Document feature dimensions and boundary guards.

The following is a **candidate simulation design for later intake, not an approved numerical contract or a claim about the owner's instrument**:

| Quantity | Proposed starting value / documentation |
|---|---|
| Phantom and nominal detector spacing | `(dz,dy,dx)=(0.125,0.080,0.080) µm`; field dimensions `8.0 × 40.96 × 40.96 µm` in z/y/x. Record sample-center extent separately. |
| Optics | Excitation 488 nm, emission 525 nm, numerical aperture (NA) 1.40, immersion/sample index 1.515 for an initial matched-index model. Record pupil, polarization, aberrations and PSF truncation; later mismatch cases are explicit. |
| Illumination/acquisition | Three mutually coherent beams with documented amplitudes/polarization; candidate outer-beam illumination NA 1.20. Three orientations nominally 0°, 60°, 120°; five equally spaced commanded phases each. Unknown offsets/gains/drift stay hidden from estimation. |
| Raw bead calibration | Separate finite fluorescent beads, e.g. 100 nm diameter, with documented emission model/pixel integration. Generate phase/orientation/z exposures under the same relevant structured illumination/detection model. Use sufficient extent and sampled bead offsets; include an independently sampled calibration grid. |
| Signal/background/noise | Noiseless baseline; candidate peaks 100/1000 detected photoelectrons per pixel per exposure, background 10/100 photoelectrons, read-noise standard deviation 1/3 electrons. Model photon shot noise and detector read noise, and record gain/offset, quantization, seeds and saturation. These are trial cases, not measured instrument parameters. |

Use physically consistent focal-plane-relative axial illumination. Equations 5–9 of the 2008 paper explain why axial order profiles multiply the detection displacement kernel during a focus scan; a single specimen-fixed 3D pattern followed by convolution models a different experiment. [Gustafsson et al., 2008](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf)

For this candidate, lateral detection cutoff is `2*NA/λem = 2*1.40/0.525 ≈ 5.33 cycles/µm`, below detector Nyquist `1/(2*0.080)=6.25 cycles/µm`. The second-order lateral illumination shift can reach `2*1.20/0.488 ≈ 4.92 cycles/µm`; extended support reaches about `10.25 cycles/µm`. Proposed 40 nm output sampling has Nyquist `12.5 cycles/µm`. This is a sampling sanity check, not a resolution guarantee. Check axial support and forward-model convergence independently; document oversampling/downsampling, pixel integration and the phantom/detector/output coordinate relationship.

1. Independently generate **both raw specimen SIM exposures and raw SIM bead calibration exposures**, retaining phase/orientation/z resolution. Arrays suffice; no MRC manufacture is required. Use padded/oversampled forward calculations or quantify discretization/window error; do not validate the inverse only against itself.
2. Feed those raw arrays and legitimate metadata through the **same phase-7 public calibration/reconstruction workflow**. Do not replace beads with ready-made OTFs, supplied axial profiles, true bead centers, carriers, offsets, gains, drift or privileged intermediates. Nominal commands/measurable metadata are legitimate; unknown simulator truth stays in evaluator artifacts.
3. Assess noiseless analytic cases, then realistic signal/background/noise, drift and calibration perturbations. Check simulator optics against analytic limits/convergence. Separately report calibration error, parameter error, stored-estimator error and reconstruction error versus phantom; account for missing frequencies and regularization bias.
4. Retain seeds, raw-array digests, parameter/metadata manifests, simulator/pipeline commits, resolved optical-tool versions, truth-access separation, signed slices/profiles, residual spectra and failure diagnostics.
5. Measure wall time and peak resident memory separately for generation, calibration, estimation and reconstruction on a named machine. Record dtypes/shapes, intermediates, concurrency and scratch/output size. One float32 volume is `64*512*512*4 = 67,108,864 bytes = 64 MiB`; fifteen specimen exposures alone occupy `960 MiB`. Float64 doubles that before calibration and transform/output buffers. These are lower bounds, not measured peaks or a new gate.

**Dependencies:** phase 7 and a separately contracted independent simulator/acceptance design. **Deliverables:** full-size phantom, both raw acquisitions, public workflow run and reproducible scientific/resource report. **Exit:** full-volume simulation satisfies independently reviewed criteria through the experimental public route, with analytic/noise cases and practical measurements complete. Small fixtures or ready-OTF reconstruction cannot satisfy this exit.

### 9. FINAL — real-data integration and owner-reference parity

This tests the simulated workflow against the owner's experiment and supplied C outputs.

Obtain at phase entry:

- Original raw specimen files/arrays and headers/metadata, section order, channels/time, orientation/phase commands, wavelengths, spacing, exposures/timestamps and acquisition corrections.
- Corresponding raw bead/PSF acquisitions, bead properties/selection and calibration metadata. Identify detection-only versus phase-resolved calibration. Obtain derived reference OTF artifacts where available, including grids/order conventions and calibration settings, for diagnosis; they do not replace raw Python calibration.
- Exact calibration/reconstruction configurations and already-used command/config transcripts, enabled flags/defaults/overrides, camera/dark/flat-field files and other referenced inputs.
- Owner-provided outputs, geometry/type/units, reference source revision/build/version/platform if known, input/output digests and existing logs/intermediate estimates. Report unknown provenance. Resolve sharing/storage constraints before putting private data in tracked or external artifacts.

Run the same public pipeline. Reconcile metadata/geometry, compare unadjusted outputs, then diagnose intake, calibration, interpolation, estimation/correction, reconstruction and representation disagreements. Scoped fixes use the existing scientific route; do not silently tune tests to observed outputs.

**Resolve parity acceptance before its acceptance run:**

| Decision | Evidence and reporting |
|---|---|
| Metrics/tolerances | Report shape/dtype/finite status, voxel differences, maximum absolute and root mean square error, a declared relative-error denominator/zero case, profiles and frequency-band discrepancies. Select tolerances from precision, algorithms, interpolation, noise and supplied cases. No threshold is chosen here. |
| Scaling/offsets | Report unscaled differences and intensity interpretation first. Decide whether reference normalization requires a declared deterministic conversion or a fitted diagnostic. Fitting cannot silently turn failure into parity. |
| Registration/cropping | Verify axes, origin, sampling, padding and region correspondence. Report unregistered differences first. Any alignment/resampling, crop/mask or boundary exclusion requires explicit rationale/parameters and a separately reported result. |
| Legacy mode/output meaning | Decide required conventions/settings: support cleanup, bead compensation, regularization, apodization, real/complex projection and negative values. Keep compatibility separate from independent scientific validity. |
| Dataset scope | Manifest calibration/specimen pairings/configurations and challenging cases. State passed and unsupported supplied cases; one matching volume proves no universal parity. |

**Dependencies:** successful phase 8; supplied datasets/settings and resolved comparison decisions. **Deliverables:** private-data-safe reproducible manifest, Python outputs, owner-reference comparison report, discrepancy records and supported-mode usage. **Exit:** agreed owner cases satisfy the evidence-driven parity contract under matching recorded settings, with provenance and limitations. No reference program is run, rebuilt or invoked.

## Execution boundaries and next action

This work map supplies no estimator default, tolerance, resource cap, alternate gate or authority to change existing candidates. Use [AGENTS.md](../AGENTS.md), [intake](../.agents/skills/intake/SKILL.md) and each concrete contract. New numerical work retains fresh blind test author/reviewer, restricted implementation and fresh final review. Preserve full local exact-candidate verification and required platform evidence under the policy integrated in the slice's baseline. PR #9’s merged advisory-coverage policy and the owner-retained continuation choice preserve full checks and native measurement/report integrity. The maintenance task’s scoped restack resolution remains historical; it supplies no additional gate authority. Preserve historical attempts; human numeric limits for this amendment are not set.

Independent source/metadata/oracle investigations may run in parallel. Dependent numerical work waits for completed integrated prerequisites; real-data acceptance waits for full simulation. Confidence is high in the calibration/grid/estimation gaps, from source and explicit contracts. Exact compatibility/tolerance choices remain uncertain until target artifacts/settings and independent evidence are available.

**Next: phase 1**, reconcile the accepted stack into an execution baseline and prepare raw-acquisition/empirical-calibration intake packets. The owner requires this amendment task to finish before the existing phase-1 task restarts: publish/read back the verified, independently accepted PR #22 candidate first. The [introductory README](../README.md) summarizes current capabilities and remaining phases for new visitors. This task does not merge that stack or start scientific implementation.
