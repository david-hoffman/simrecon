# PR53: orthogonal views and bead-center image-quality checks

The owner requested XY and XZ maximum-intensity projections (MIPs), followed by XY and XZ sections through one bead center. These figures replace single middle-plane presentation as the main views. They render the same frozen data from software source `0aa541d6e1483f03d6d800c6d06289fa0073327f`; no generation, inference, fit, seeds, settings, official metric or test changed.

## View definitions and selection

XY is the maximum over every z sample. XZ is the maximum over every y sample, displayed as rows z and columns x. Physical micrometre aspect ratios are equal on all axes; XZ is not stretched into a square. The right-hand MIP column is **MIP(estimate) minus MIP(reference/observation)**, not the maximum of signed residuals. Maxima can come from different depths, so the projection difference is a display comparison rather than a three-dimensional error map.

For sections, choose the first listed calibration bead and the first listed specimen bead before examining reconstructed peaks/errors. Catalogue centers are local to their known box corners. Take the nearest stored sample-center planes, with the first index on a tie. Do not interpolate, align or recenter to a fitted maximum. Cyan crosses show the nominal bead center. Main image pairs retain one common quantitative linear scale; signed differences use symmetric scales. Only the clearly labeled shape profiles normalize each line by its own maximum. They compare shape, not absolute amplitude, resolution certification or the official source error.

The calibration bead center is local (z,y,x)=(0.3125,0.6000,0.7000) µm. XY uses z=0.3125 µm; XZ uses y=0.6000 µm. The full 2.56×2.56×1 µm calibration field is shown.

The specimen bead center is local (z,y,x)=(0.6500,4.0500,3.8500) µm. Source sections use z=0.6875 µm and y=4.0600 µm on the source grid; image sections use z=0.6875 µm and y=4.0400 µm on the detector grid. Crops use the bead-centered ±1 µm lateral and ±0.65 µm axial requested windows, rounded out to existing voxel edges and clipped at z=0. Exact extents and indices are in the provenance. This is a predetermined bead, not the best-looking reconstruction.

## Reconstruction stages

1. [All 15 noisy exposures, XY/XZ MIPs](01-noisy-orthogonal-mips.png) ([PDF](01-noisy-orthogonal-mips.pdf)). Full 20.48×20.48×4 µm field; rows identify orientation and projection, columns exposure index. One shared linear detector-count scale across all30panels.
2. [Camera correction, XY/XZ MIPs](02-camera-orthogonal-mips.png) ([PDF](02-camera-orthogonal-mips.pdf)). Fixed orientation0/exposure0 before and after `(counts−20.1973062)/1700.0256947`. Count and relative-unit scales correspond exactly; the image changes units, not spatial blur. Original eight-frame dark/blank/flat summaries remain in [the earlier camera figure](02-camera-correction.png).
3. [Held-out bead MIPs](03-bead-orthogonal-mips.png) ([PDF](03-bead-orthogonal-mips.pdf)) and [bead-center XY/XZ sections with shape profiles](03b-bead-center-sections.png) ([PDF](03b-bead-center-sections.pdf)). Fixed orientation0/exposure0, corrected observed versus frozen prediction. Shared linear relative-image scales; signed differences symmetric. All15whole-volume held-out root-mean-square residuals remain in [the original diagnostic](03-bead-calibration.png). This is distinct from specimen training fit.
4. [Original recorded objective progression](04-specimen-fit-progress.png) ([PDF](04-specimen-fit-progress.pdf)). Initial score plus all12accepted iterations. No intermediate reconstructed volumes were stored or invented.
5. [Frozen source MIPs](05-source-orthogonal-mips.png) ([PDF](05-source-orthogonal-mips.pdf)) and [source bead-center sections with shape profiles](05b-source-bead-sections.png) ([PDF](05b-source-bead-sections.pdf)). Paired fine-grid reference versus frozen estimate, in the declared camera-contrast relative source-coefficient gauge. The common quantitative scale preserves the large amplitude mismatch: reference peak5.714199 versus estimate0.218990. No post-hoc scalar is applied.
6. [Frozen image-prediction MIPs](06-prediction-orthogonal-mips.png) ([PDF](06-prediction-orthogonal-mips.pdf)) and [prediction bead-center sections with shape profiles](06b-prediction-bead-sections.png) ([PDF](06b-prediction-bead-sections.pdf)). Corrected observed versus frozen predicted images, same predetermined specimen bead and exposure. These are training-data comparisons.

[Orthogonal provenance, exact input/output hashes, planes, crops and profile data](orthogonal-provenance.json). [Original single-plane stage presentation](README-before-orthogonal.md) and [PR text before this revision](PR-before-orthogonal-views.md) are retained. All earlier assets and [the complete original detailed delivery appendix](delivery-evidence-before-stage-figures.md) remain intact.

## Report-only investigation and recommendation

An explicitly requested Astra/ultra advisor inspected the frozen traces, source and calibration records; a separate lane searched primary literature. This is investigation, not a new product acceptance or causal ablation. Actual served model/effort/metering remain unknown.

The strongest current explanations are unfinished finite optimization and illumination-calibration error over the wider specimen field. Every specimen step was accepted, and the last step still lowered the objective2.79%. The zero start and12recorded step/gradient maxima bound every coefficient to about0.219045 (including conservative roundoff allowance), versus reference peak5.714199. Even ideal placement under that coefficient cap leaves at least89.11%relative source error. The actual error remains95.31%.

Carrier errors evaluated at all27catalogue centers and5phases give wrapped fundamental phase RMS1.43,0.83,2.00radians for the three orientations. These are phase mismatches, not fractions of attributed reconstruction error. The2.56µm calibration field is8times narrower than the20.48µm specimen; a fixed spatial-frequency error accumulates proportionally with distance. Axial fine-source62.5nm versus inverse125nm mass-pairing mismatch is real but has not been isolated.

Sparsity makes the voxel metric demanding: only0.01935%of reference coefficients are nonzero. The estimate has113.55%of reference total intensity but only13.10%of its Euclidean norm, indicating spreading rather than a missing single gain. A hypothetical truth-chosen scalar would still leave90.99%error and was never applied. This does not establish a fundamental95%floor, exact nullspace, or that sparsity is the root cause. The66.4%prediction error also needs explanation beyond unobserved fine source detail.

Recommended order: (1)measure the representation/model floor by forward-projecting the paired reference with true illumination against frozen noiseless generator images; (2)on the same scene, compare genuine convergence with estimated versus true illumination as separately labeled diagnostic controls; (3)then improve calibration scope/estimation or run a controlled density comparison. Do not replace the sparse specimen just to lower the metric. No recommended new experiment has been executed.

Primary literature: [Qian et al., PCA-SIM,2023](https://link.springer.com/article/10.1186/s43593-022-00035-x) isolates reconstruction degradation from parameter-estimation errors in2D simulations; [Qian et al., PCA-3DSIM,2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12402504/) discusses3D parameter accuracy and the information/noise penalty of small local regions. Its experimental spatial-aberration rationale does not establish aberrations in this globally prescribed synthetic model. [Smith et al.,2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7611169/) shows noise and sample-density dependence of reconstruction/parameter estimates. [Zhao et al.,2022,online2021](https://pubmed.ncbi.nlm.nih.gov/34782739/) exploits sparsity and continuity as priors; its different algorithm is not a guarantee here. These papers support diagnostics, not a quantitative causal allocation for this run.

[Exact descriptive calculations, confidence, sources and proposed diagnostic sequence](diagnostic-summary.json). High confidence in unfinished searches and measured phase mismatch; their relative causal contributions remain unmeasured. Camera contrast error15.1parts per million and the current penalty/data ratio5.36×10^-7 rank those explanations lower; no new forward/adjoint defect is demonstrated.

## Reproduce

Use the unchanged original software checkout, retained archive SHA256`4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0`, and Python3.13.12/NumPy2.5.1/Matplotlib3.11.0. Use new absent output directories:

```sh
python prepare_orthogonal.py --repo /path/to/source-checkout --archive /path/to/study-and-evidence.tar.gz --out ./verified-orthogonal-inputs
MPLCONFIGDIR=./plot-cache python render_orthogonal.py --inputs ./verified-orthogonal-inputs --out ./orthogonal-figures
```

Preparation checks the whole archive and all23selected regular input member hashes (454,961,219bytes), reads in memory, retains compact display reductions and explicitly named frozen diagnostic volumes, and never extracts archive paths. Rendering does not run inference. Source truth is used only after the freeze for evaluation and predetermined nominal bead-plane selection. Nearest-neighbor display and equal physical aspect are explicit. One fixed noisy synthetic case, finite scalar clear-pupil optics, source/pixel/pupil sampling, estimated camera gauge, possible ambiguities and the paired axial representation limit interpretation. Maxima and normalized profiles are presentation transforms, not replacement recovery metrics.
