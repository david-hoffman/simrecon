# Fourier-block observable phase comparison

**Version 1.0.** This report records the coordinator's assessment of C01's original postimplementation examples for the [approved contract](../contracts/fourier-block-phase-estimation-v1.md). Exact final candidate, regenerated evidence, full checks and independent review belong in the [task evidence](../tasks/fourier-block-phase-estimation.md). The observations below are scientific supplements, not blind-test or delivery acceptance.

The observable volume phase estimator now solves the nuisance specimen in exact Fourier carrier-orbit blocks. It keeps one common phase fit, the complete observation residual and one global numerical rank cutoff at every phase trial. The full-space estimator keeps its existing path. Dense nuisance storage falls when carrier orbits are small. Long carrier cycles can still produce expensive blocks.

## Independent arithmetic and hidden truth

C01 generated observations using finite real-space illumination and circular convolution. Hidden specimen and exposure phases remained evaluator-only. A separate direct Fourier model checked the fitted specimen, residual, nuisance singular values, derivative and projected information. The specimen target below is the independent direct-model least-squares result at the returned phases; it is not the hidden physical specimen. Values use the estimator's declared observation normalization.

| Control | Termination | Relative residual | Maximum specimen-minus-target difference | Maximum wrapped phase-minus-truth difference (rad) |
|---|---|---:|---:|---:|
| Compatible small specimen | stationary | 7.104403694e-12 | 4.440892099e-16 | 6.543021680e-11 |
| Algebraic off-model input | stationary | 0.00563226 | 2.220446049e-16 | 0.00482804 |
| Zero transfer | no_observable_specimen | 1 | 0 | 0.13 |

The zero-transfer fit retained nominal phases and rank zero. Its unavailable specimen and unchanged phases recover no hidden truth. For the off-model control, close agreement with the arithmetic target coexists with a much larger phase-truth discrepancy. A low residual or `stationary` result alone establishes neither physical accuracy nor uniqueness.

In the compatible small comparison, maximum absolute direct-global versus block differences were 1.776356839e-15 for residuals, 3.552713679e-15 for nuisance singular values and 8.881784197e-16 for the spatial specimen. The central-difference/profile-Jacobian discrepancy was 4.9191e-10 with a 2e-6 rad step. The comparison allowances, 2e-8 and 2e-7 for the relevant scalar checks, are arithmetic checks rather than phase-accuracy thresholds. Signed arrays and per-check bounds are retained in the original evidence.

The complete carrier scan retained `(0,2), (0,6), (1,1), (0,2)` in order, including the alias and duplicate. Every row matched a fresh public fit from the same nominal commands. The `(1,1)` row stagnated with relative residual 0.223043 and maximum phase discrepancy 2.95327 rad. No row was warm-started, removed or selected.

## Observed resource scaling

The witness used six exposures, lateral shape 8 × 16, carrier `(0,8)`, all five signed orders, float64 observations and complex128 calibration/operators. Maximum block size was four frequencies. The largest real nuisance design was 48 × 4. Each axial extent ran in a separate process.

| Axial planes | Voxels | Blocks | Fit time (s) | Whole child time (s) | Pre-fit peak (bytes) | Post-fit peak (bytes) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 256 | 68 | 0.024077708 | 0.832083250 | 139329536 | 139329536 |
| 4 | 512 | 132 | 0.045212625 | 0.883142792 | 139427840 | 142409728 |
| 8 | 1024 | 260 | 0.086086125 | 0.946651583 | 145244160 | 154468352 |

These are arm64 macOS 27.0.1 observations. Memory is Darwin `ru_maxrss`, the cumulative whole-process high-water mark including interpreter, imports and generation baseline. It is not baseline-subtracted estimator memory. The equal first-row peaks do not establish zero allocation. The three observations provide no old-backend speedup comparison, required-platform equivalence or proof that a complete 512 × 512 × 64 workflow is feasible. No time or memory acceptance cap was imposed.

## Provenance and limits

Original local records are `artifacts/fourier-block-phase-20261018/C01/report.md` and `C01/evidence/examples01/{manifest,association}.json`. Generation succeeded once in 4.432608 s, with 70 closed members and 15,584 equal before/after input pins. Its original Git context was dirty `bbbce410819434a9a4222f1f150ad7eb9047db5b`; it is preserved as such. Subsequent reviewed test/fixture changes require affected regeneration. A separate clean-candidate admission may establish unchanged material inputs; it does not turn the original run into a clean generation.

C01 recorded 1,051 focused passing tests and passing owned lint, format and type checks. A later inverse-transform supplement checks unusable/nonfinite results, arithmetic warnings and legitimate positive results through the public estimator. It is postimplementation evidence and has no pre-fix failure claim. Exact blind checkpoint acceptance, full 13-phase `make verify`, selected native coverage, fresh D review and independent Ubuntu 24.04/macOS 15 archive qualifications are separate requirements recorded outside candidate bytes.

Fixed calibration, a supplied integer carrier, periodic boundaries and local initialization remain assumptions. `stationary` means the specified local gradient condition, not a minimum or global uniqueness. Continuous carrier, drift and gain inference, complete raw workflow integration, realistic truth-hidden simulation and owner-reference parity remain unfinished. See the [usage guide](../usage/fourier-block-phase-estimation.md).
