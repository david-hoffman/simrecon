# Why the full study did not recover the specimen

PR53 is retained as a completed experiment with poor recovery: **95.3% source error and 66.4% signal-prediction error**. Neither completion nor the finer output grid establishes a resolution improvement. This follow-up investigates the result without changing the original images, fit or evaluation. [Original report](../studies/full-noisy-study-2026-10-26/README.md), [investigation scope](../tasks/pr53-recovery-investigation.md).

## Reading the figures

**Camera correction changes the zero level and intensity units.** For this run,

```text
relative signal = (raw camera counts − 20.1973062) / 1700.0256947.
```

The subtracted value is the image-estimated blank level, including camera offset and background. The divisor is the estimated flat-minus-blank contrast. The result is in reference-flat-relative signal units, not calibrated photons. This global linear transformation does not remove random noise, deconvolve optical blur or improve resolution. [Recorded camera estimates](../studies/full-noisy-study-2026-10-26/evidence/full-parameter-estimates.json), [correction contract](../contracts/image-only-specimen-fit-v1.md).

**The calibration-bead panels test prediction of the camera image.** The model's predicted image should retain the optical blur present in the observation. Agreement there does not demonstrate a sharpened bead. The specimen-source panels compare the recovered object with the known source and expose the poor recovery. Use the shared quantitative intensity scales for amplitude and the separately labeled peak-normalized profiles only for shape. A 40 nm lateral output spacing, versus 80 nm detector sampling, is a sampling choice, not a measured resolution gain. The separate XY/XZ projections and bead-center sections remain in the [preserved figure collection](https://github.com/david-hoffman/simrecon/blob/666b73ff97180998406dc66ac79be14d67687c64/README.md).

**A specimen iteration updates the estimated fluorescent object.** The current object is used to predict the 15 exposures. The difference from the camera-corrected observations determines a proposed nonnegative object update. The solver accepts it if its objective decreases; rejected trials reduce the step. Camera and illumination estimates remain fixed. This run started from zero, accepted 12 updates, and stopped at the declared iteration limit. It did not establish convergence. [Solver contract](../contracts/image-only-specimen-fit-v1.md), [implementation](../../scripts/image_only_specimen_fit.py).

## Hypotheses in plain language

1. **The reconstruction stopped too early.** The last update still lowered the objective by 2.79%. The highest reconstructed coefficient was 0.219, compared with 5.714 in the reference. The recorded steps bound every final coefficient below approximately 0.219045; even ideal placement under that bound leaves at least 89.11% source error. This is a bound for this short trajectory, not a universal limit of the algorithm or an attribution of 89% of the observed error.
2. **The estimated stripes drift out of place across the larger image.** A small error in stripe spacing or direction accumulates with distance. Calibration spans 2.56 µm laterally; the specimen spans 20.48 µm. At the catalogue bead positions, the measured fundamental-phase root-mean-square errors are 1.43, 0.83 and 2.00 radians for the three orientations. This unweighted lateral-phase statistic covers all 27 centers and five exposures and excludes the separate axial term. Those mismatches are established; how much reconstruction error they cause needs controlled comparisons.
3. **The model puts emission at slightly different depths.** Simulation uses 62.5 nm axial source cells; reconstruction uses 125 nm cells. Adding pairs of fine-cell masses preserves their total brightness, but moves that brightness to the coarse cell centers and need not preserve the predicted images. A forward projection of the paired reference measures this discrepancy without requiring optimization.
4. **Sparse beads make a voxel-by-voxel comparison demanding.** Spreading a small bright bead over nearby voxels can retain total brightness while producing a large source error. Here the reconstruction has 113.55% of the reference's total intensity but only 13.10% of its Euclidean norm, consistent with dispersed intensity. This does not establish that sparsity caused the failure, nor explain away the large image-prediction error. Keep the sparse scene while isolating the other factors.

These numbers and their calculation limits are retained in the [reviewed diagnostic record](https://github.com/david-hoffman/simrecon/blob/666b73ff97180998406dc66ac79be14d67687c64/diagnostic-summary.json). No fitted alignment, truth-selected global rescaling or replacement metric was applied to the original result.

## Comparison with the reference C implementation

**The full study is a different reconstruction algorithm, not a demonstrated port of the reference.** The historical [adoption inspection](../setup/BASELINE.md) established source identity and build limitations; it did not establish scientific reconstruction parity. The requested Astra advisor has now inspected the actual legacy source for this investigation. It was not compiled or run, and no legacy code was copied into the product.

| Stage | Legacy reference | Full noisy study |
| --- | --- | --- |
| Illumination | Can estimate/refine carrier and complex order amplitudes from overlapping specimen frequency bands. | Estimates illumination from three calibration beads, then freezes those estimates for specimen fitting. |
| Reconstruction | Separates bands, applies optical-transfer and noise weighting, relocates bands and combines them. | Fits a nonnegative object volume directly against all exposures with projected gradient updates. |
| Optical model | Loads order-specific complex optical transfer functions, which describe how each order passes through the imaging system. | Uses the declared clear-pupil synthetic model and a discrete source approximation. |
| Regularization | Generalized Wiener frequency weighting, with optional suppression and tapering. | A quadratic source penalty and the practical restriction imposed by early stopping. |

The inspected snapshot is local Subversion revision 307. Its `sirecon.c` SHA-256 is `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567`, matching the adoption inventory. Relevant locations in that unchanged local file are band separation at line 740, carrier/modulation fitting at 787, phase-matrix construction at 1155, complex regression at 1849, frequency weighting at 2134, and relocation/assembly at 2371. The study's actual bead-to-specimen path is in [`full_noisy_study.py`](../../scripts/full_noisy_study.py); its harmonic forward model is in [`simulation_inverse_operator.py`](../../scripts/simulation_inverse_operator.py). Ignored legacy sources remain unshipped reference material.

The absence of an explicit band-separation step is **not by itself a missing physical effect**: the direct forward operator contains the zero, first and second illumination harmonics and their axial factors. Adding separate relocation to this direct model could double-count the same effect. Conversely, a correct forward model does not guarantee that a short iterative solve recovers its source.

The reference's phase handling also needs care. Separation uses ideal or supplied phase steps, optionally modified by drift information; overlap regression fits complex order amplitudes and phase offsets. That is not automatically an estimator for every independently unknown exposure phase used in this study. Nor is its numerical Wiener setting interchangeable with this solver's quadratic-penalty value.

## First controlled measurement

The unchanged public forward operator was evaluated on the original full field for **orientation 0, phase 0**. The paired reference object was held fixed while only the illumination parameters changed. All comparisons use the same original noiseless signal and its Euclidean norm as denominator.

| Object supplied to the forward model | Illumination | Relative image-prediction error |
| --- | --- | ---: |
| Known paired reference | True | **1.70%** |
| Same known paired reference | Frozen estimated | **45.64%** |
| Original reconstructed object, original frozen prediction | Frozen estimated | **66.31%** |

This is direct evidence that the estimated illumination is a substantial mismatch for this exposure, even when the object is supplied correctly. The known-illumination discrepancy is much smaller. It includes the axial representation difference and finite numerical/model effects; it does not isolate each one. These errors are not additive causal shares, and this one exposure is not the original 15-exposure aggregate of 66.4%.

The source was explicitly rounded to float32 for the public operator; its relative rounding error was `2.976e-8`, with no nonzero coefficient rounded to zero. The source geometry was Z/Y/X `(32, 512, 512)` at `(0.125, 0.04, 0.04)` µm, using the original optical settings and pupil quadrature order 256. One cache and two single-phase forward calls took 49.24 s including validation and output recording. No source fit or illumination refinement was performed. [Machine-readable results, hashes and limitations](evidence/pr53-recovery-forward-diagnostic.json).

To reproduce the numerical comparison after preparing the hash-identified frozen input bundle using the [preserved preparation code](https://github.com/david-hoffman/simrecon/blob/666b73ff97180998406dc66ac79be14d67687c64/prepare_orthogonal.py), run the unchanged operations below from the recorded source baseline. `inputs` denotes that prepared bundle. `record` is the machine-readable result linked above; each arm already records the correctly transferred specimen-origin phase. Do not transfer it again.

```python
import json
from pathlib import Path
import numpy as np
from scripts.simulation_inverse_operator import build_kernel_cache, forward

inputs = Path("verified-orthogonal-inputs")
record = json.loads(Path(
    "docs/reports/evidence/pr53-recovery-forward-diagnostic.json"
).read_text())
source = np.load(inputs / "source_reference.npy", allow_pickle=False)
signal = np.load(inputs / "example_expected_signal_relative.npy", allow_pickle=False)
source32 = source.astype(np.float32)
cache = build_kernel_cache(
    source_shape_zyx=(32, 512, 512), source_spacing_um_zyx=(0.125, 0.04, 0.04),
    emission_um=0.525, refractive_index=1.515, detection_na=1.4, pupil_order=256,
)
for name, arm in record["arms"].items():
    prediction = forward(
        source32, kernel_cache=cache,
        carrier_yx_per_um=np.array(arm["carrier_yx_per_um"]),
        phases_rad=np.array(arm["phases_rad"]),
        beam_amplitudes=tuple(arm["beam_amplitudes"]), excitation_um=0.488,
    )[0]
    print(name, np.linalg.norm((prediction - signal).ravel())
          / np.linalg.norm(signal.ravel()))
```

These ordinary reductions are safe for the finite, moderate values of this recorded diagnostic; the snippet makes no general extreme-range metric promise. Exact execution logs, the full orchestration script and output volumes are retained locally. The derived inputs were hash-checked and their original preparation formulas inspected, but were not regenerated from the archive in this diagnostic. The outer resource-timing wrapper returned 1 because a sandbox denied its `kern.clockrate` query after the Python calculation sealed its results; its peak resource measurement is unavailable. Python recorded a self-process maximum resident set of 1,050,148,864 native macOS bytes. This wrapper failure is retained and is not reported as a successful full verification run.

## Next comparisons

Extend the controlled illumination comparison to the remaining exposures before generalizing its magnitude. Test conventions on a tiny matched problem: axis ordering, first versus second harmonic, phase origin/sign, complex conjugation, Fourier normalization, pixel integration, axial source–focus sign and boundaries. Start with known phases and an integer carrier, then challenge fractional carriers and unequal beams.

Next compare a fully converged small direct solve with an independently written spectral reconstruction under matched assumptions. Only after those controls should full-field source solves and specimen-informed illumination estimation be compared. The sparse scene stays fixed. Any new numerical implementation requires the scientific delivery route; this report does not implement one.

Confidence is high in the observed early stopping, illumination mismatch in the controlled exposure and algorithm differences. Their relative contributions to the full reconstruction, achievable resolution and final attainable source error remain unmeasured. No reference execution, numerical parity or repaired reconstruction is claimed.
