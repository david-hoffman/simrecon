# Full fixed noisy case: 256×256×32

## Source comparison

**Full fixed noisy case: 256×256×32 — source coefficients.** The geometric middle plane is z index16 of32 (local z2.0625µm); XYspacing0.04µm and Zspacing0.125µm, with the whole20.48×20.48µm field shown. Reference and inferred coefficients share a linear color range0–5.7142 relative source units; signed(inferred−reference) uses±5.57245. Relative units use the estimated flat contrast d_hat (flat mean minus blank mean). Reference coefficients are exactly `(true_gain/d_hat)*(fine[2k]+fine[2k+1])`: paired fine axial cells on the coarser inverse basis, with no voxel-volume/beam factor, alignment, crop or fitted scale. Axial profiles sum the whole XY field at every z. Full-volume coefficient relative L2 error0.953147 shows poor recovery; finite-fit completion is not convergence or good-recovery evidence. This is one fixed noisy case, and re-rendering is not independent noise.

## Prediction and residual

**Full fixed noisy case: 256×256×32 — frozen prediction and signed training residual.** Fixed orientation0, phase0 and geometric middle z index16 (2.0625µm), with the whole20.48×20.48µm field shown. Corrected raw counts `(counts−estimated blank mean)/d_hat` and frozen prediction share linear range-0.0146111–27.4361; prediction-minus-corrected-raw uses±24.4706. d_hat is the estimated flat contrast (flat mean minus blank mean), defining relative image units. These are training residuals, not held-out validation. Full15-exposure relative L2 errors are0.664298 against the noiseless signal reference and0.664296 against the corrected mean, showing poor prediction recovery. Global metrics use all31,457,280 values, not just the displayed slice. One fixed case and finite completion do not establish convergence or independent-repeat evidence.

## Data identities

- Paired-reference input `specimen_source_e.npy` SHA-256 `875140c3ade832645bc9156e1812adee02afdd51ec383da103dcb86cda1777e4`.
- Inferred `specimen_source_relative.npy` SHA-256 `a12cc505f87acf4f62814b8a21702a67e386eb064e5547d7718551dd0ef904c6`.
- Raw fixed panel `specimen_o0_p0.npy` SHA-256 `993ded020eb318f73bd35b1e7561ed8ef008017c41254f34eecce7153e6436d0`.
- Frozen fixed panel `prediction_o0_p0.npy` SHA-256 `f17b4451ba70b46c4000c8397be7e5297a5fb3fc85791e2c531c8a95bbc000b6`.
- Observation manifest SHA-256 `1aeae458173155d0609020d25b299e087e16ffa6e31453f744e8b048584ebd5c`.
- Inference freeze SHA-256 `919068b950240adb2f122c12a903efe83537bf4b3430691c8bbf6a912d64fdad`.
- Evaluation SHA-256 `2e6e5afaed797b4fc8feaa2dc6272488899071834fa88e45c0cc082fd0ac2ceb`.

Exact file/display/transformation/environment/global-norm records are in `public-figure-provenance.json`. These public captions contain no local filesystem paths.
