The full noisy three-dimensional structured illumination microscopy (SIM) workflow now runs from recorded images through camera estimation, bead/illumination calibration, nonnegative specimen fitting, frozen predictions and truth evaluation. **The fixed 27-object study reconstructs poorly: 95.3% source error and 66.4% signal-prediction error.** The specimen solver reached its declared 12-iteration limit. Completion does not establish convergence, accurate recovery or resolution gain.

The figures below follow the **same recorded 256 × 256 × 32 X/Y/Z detector case**, spanning **20.48 × 20.48 × 4 µm**, with three orientations and five exposures each. They use the original frozen data; no simulation, fit, seed, parameter or setting was changed. The new stage plots do not expose truth to inference. [Scientific report and reproduction commands](https://github.com/david-hoffman/simrecon/blob/0aa541d6e1483f03d6d800c6d06289fa0073327f/docs/studies/full-noisy-study-2026-10-26/README.md).

**1. Acquire the noisy specimen images**

![All 15 recorded noisy specimen exposures](https://raw.githubusercontent.com/david-hoffman/simrecon/fea3ffea30b96a046b99145bcf8a3f938792edcd/01-noisy-exposures.png)

All 15 exposures at the fixed middle plane, local z = 2.0625 µm. Rows are orientations; columns are exposure indices, not inferred true phases. Every panel shows the whole 20.48 × 20.48 µm field on one shared linear detector-count scale. The simulation includes photon/background and read noise.

**2. Estimate and apply the camera correction**

![Camera estimates and the same specimen pixels before and after correction](https://raw.githubusercontent.com/david-hoffman/simrecon/fea3ffea30b96a046b99145bcf8a3f938792edcd/02-camera-correction.png)

Left: eight frame means per dark, blank and flat group, on a logarithmic count axis; short bars mark group means. Right: the same fixed specimen image before and after `(counts − 20.1973062) / 1700.0256947`. Correction expresses the image in estimated reference-flat-relative units. Corresponding color scales give the same appearance: this step rescales pixels and subtracts background; it does not deblur them.

**3. Calibrate from bead images and check held-out predictions**

![Held-out bead observation, frozen prediction, signed residual and residual summaries](https://raw.githubusercontent.com/david-hoffman/simrecon/fea3ffea30b96a046b99145bcf8a3f938792edcd/03-bead-calibration.png)

The 47-coordinate bead/illumination fit completed ten sweeps and 940 finite polls. Top: corrected held-out observation and frozen prediction, fixed orientation 1/exposure 1/local z = 0.5625 µm, with one shared linear scale and the full 2.56 × 2.56 µm field. Bottom: prediction minus observation on a symmetric scale, and root mean square (RMS) residuals across all 15 complete held-out 8 × 32 × 32 volumes. Image and residual units use the estimated flat contrast. These are calibration checks, not proof that the optical model is physically correct or uniquely identified.

**4. Fit the nonnegative specimen with calibration frozen**

![Recorded objective through all 12 accepted specimen iterations](https://raw.githubusercontent.com/david-hoffman/simrecon/fea3ffea30b96a046b99145bcf8a3f938792edcd/04-specimen-fit-progress.png)

Recorded initial score and all 12 accepted iterations. The dimensionless training objective falls from 0.0203274 to 0.00898537, then execution stops at the iteration limit. The plotted objective is the normalized image residual sum of squares plus the declared source penalty, with regularization 0.001. Intermediate reconstruction volumes were not stored; this is the actual score trace, not an invented image sequence. Objective decrease does not establish convergence or accurate recovery.

**5. Freeze the reconstructed source, then compare with simulation truth**

![Observed full-case source reference, estimate, signed error and axial profiles](https://raw.githubusercontent.com/david-hoffman/simrecon/0aa541d6e1483f03d6d800c6d06289fa0073327f/docs/studies/full-noisy-study-2026-10-26/figures/source-comparison.png)

Original observed rendering: middle plane z = 2.0625 µm and full field. Reference and estimate share a linear 0–5.7142 relative-coefficient scale; signed difference uses ±5.57245. Whole-field axial profiles show the mismatch. Evaluation pairs fine axial source cells in the estimated camera-contrast gauge, with no fitted scale, alignment or crop. Full-volume source norm error is 95.3%; this is coefficient error on the declared basis, not continuum-source or absolute-electron recovery.

**6. Check the frozen image prediction and signed residual**

![Frozen specimen prediction and signed training residual](https://raw.githubusercontent.com/david-hoffman/simrecon/0aa541d6e1483f03d6d800c6d06289fa0073327f/docs/studies/full-noisy-study-2026-10-26/figures/prediction-residuals.png)

Original observed rendering: fixed orientation 1/exposure 1/middle plane. Corrected raw image and frozen prediction share the linear range −0.0146111–27.4361 relative image units; prediction-minus-corrected-raw uses ±24.4706. These specimen residuals are training residuals. Across all 15 exposures, signal-prediction error is 66.4%. The result remains poor despite the falling training objective.

[New figures, PDFs, exact input/output hashes, display transforms, captions and rendering code](https://github.com/david-hoffman/simrecon/blob/fea3ffea30b96a046b99145bcf8a3f938792edcd/README.md). [Original final-figure provenance](https://github.com/david-hoffman/simrecon/blob/0aa541d6e1483f03d6d800c6d06289fa0073327f/docs/studies/full-noisy-study-2026-10-26/figures/public-figure-provenance.json). The original final figures remain unchanged; the four new stage figures only render existing frozen inputs. One fixed synthetic realization, finite scalar clear-pupil optics, finite source/pixel/pupil sampling, paired axial basis mismatch, estimated camera gauge and possible parameter ambiguities limit the claims.

<details>
<summary>Technical appendix: exact source, verification, figure provenance and retained history</summary>

The software source remains **`0aa541d6e1483f03d6d800c6d06289fa0073327f`**, tree **`73c1ffb702c04dc68cb4d53f01b3a937d0860ec1`**: 725 tracked files and 58 owned Python runtime/tool files. Figure assets live in a separate presentation commit; no source, test, dependency, check, gate, numerical contract, fit or seed changed. Existing scientific D2 acceptance applies to the unchanged software. The added figures receive a separate presentation/data-provenance check.

| Exact-source check | Retained result |
| --- | --- |
| G7 canonical full local `make verify` | All 13 phases passed; 11,299 tests passed, 29 warnings; no skips, expected failures or unexpected passes. Receipt SHA-256 `54e54816ff64b51556c7e1e49503e42f02adadb0ec0f2875bb1ed604b9dd234e`. |
| Fresh independent scientific D2 and final added-test audit | ACCEPT, no findings, including the admitted completed cleanup and its stated scope/limits. |
| Required-platform CI | [Verify 40499966338, attempt 1](https://github.com/david-hoffman/simrecon/actions/runs/40499966338): Ubuntu 24.04 passed 11,458 tests/28 warnings; macOS 15 passed 11,299 tests/29 warnings. Each passed all 13 phases; no skips/expected failures/unexpected passes. Exact head/base/integration, original artifacts and provider bindings retained. |
| Native coverage, per platform | 58 files/zero exclusions. Local and macOS: 7,710/7,996 executable lines and 2,222/2,370 branch destinations; Ubuntu: 7,711/7,996 and 2,223/2,370. The `simrecon` package is 3,520/3,520 lines and 978/978 destinations on both platforms. Percentages are advisory; separate language-statement/per-test-process attribution is unsupported. |
| Correction and study identities | Original generation/inference: `1c209a4769c0caab0fb173287efbcac952ed01b1`. Evaluation-only correction: `51c1975eab072a29f0a820fd2493eec5663ec9a7`. Corrected driver SHA-256 `b610f6c7e8f5b35e8ba126e34c2b760214256fb5cef2b9a0b61220e2ac9ce00f`. Re-evaluating the same 130 frozen inputs changed the six relative errors by at most 2^-53; no refit. Full current source/signal/corrected-mean errors: 0.9531472567471974 / 0.664297594260943 / 0.6642963723733037. |

The new plots use 20 exact hash-verified regular members (256,354,510 bytes) of the retained original archive, SHA-256 `4de84ac559e2fcf93a2e038eea571366af54207d368cfb2f0bd50e78129257f0`. They read data and render figures without importing or running inference. Camera statistics and all held-out RMS values agree with the original records. [Stage provenance and output hashes](https://github.com/david-hoffman/simrecon/blob/fea3ffea30b96a046b99145bcf8a3f938792edcd/stage-provenance.json) bind the plot code, numerical inputs, scales and limitations.

**All prior detailed evidence is retained publicly:** [the complete previous PR description and technical appendix, byte-for-byte](https://github.com/david-hoffman/simrecon/blob/fea3ffea30b96a046b99145bcf8a3f938792edcd/delivery-evidence-before-stage-figures.md). This includes exact local/CI/test/review checkpoints, original resource and wheel/import/audit records, complete native scope/report limits, prior failed launches/checks/repairs, historical source applicability, cleanup/preservation/custody limits and cumulative accounting. Reformatting the PR removes no gate or unresolved scientific limitation and restamps no historical evidence. No merge or release is performed.

</details>
