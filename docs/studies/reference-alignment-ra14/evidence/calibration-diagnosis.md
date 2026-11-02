**The evidence supports a calibration-procedure limitation with unresolved cause, not a demonstrated implementation defect. Full scientific alignment remains unestablished.**

| Frozen fact | Matched noiseless | Original noisy |
|---|---:|---:|
| Training RMS, relative units | 0.102349925 | 0.104257187 |
| Fixed limit | 0.05 | 0.05 |
| Best objective | 0.005237754 | 0.005434781 |
| Optimizer stop | `ftol` satisfied | `ftol` satisfied |
| Reported function/Jacobian evaluations | 6 / 6 | 6 / 6 |
| Actual scored model entries | 235 | 235 |
| Infeasible entries | 0 | 0 |

Both seed procedures completed the prescribed single sweep: 94 scored polls, without initialization clipping, overlap or centroid clamping. Both refinements lowered the objective, then returned `training_misfit` exactly as contracted. There was no recorded numerical-range failure. [Noiseless record](runs/estimated-noiseless/result.json), [noisy record](runs/estimated-noisy/result.json)

The defensible causal conclusions are:

- **Noise alone cannot explain failure:** the matched noiseless calibration also fails.
- **The 40-evaluation cap was not exhausted.** Raising that cap alone does not address the observed `ftol` stop. That stop establishes neither stationarity nor a global minimum.
- **The ambiguity audit did not reject these inputs.** Both audits are empty because the earlier training gate failed. No handoff-held-out prediction or specimen descriptor exists.
- **Specimen fitting and phase-origin transfer did not cause this training rejection.** They occur later. The full specimen’s source pairing and 12-iteration reconstruction limit therefore cannot explain this calibration gate.
- **Frozen center/profile error is a plausible bottleneck.** The noiseless seed’s centers differ from the corresponding catalogue centers; the largest coordinate difference is approximately **14.47 nm**. RA12 deliberately freezes those centers and occupied profiles while refining the other 38 coordinates. That removes center correction from this refinement. It does **not** establish how much residual those differences cause. [Frozen-center contract](../../../contracts/reference-alignment-ra12-v1.md)
- **Quadrature is not supported as the leading explanation by the seed diagnostics.** The frozen seeds’ Q128/Q256/Q512 objectives agree to roughly `10⁻¹⁶` absolute. That is a shared-model diagnostic at those seeds, not an independent error certificate for every candidate.

Other possibilities—local optimization, coupled carrier/phase/brightness errors, fixed-profile mismatch or an unrecognized implementation discrepancy—remain unresolved. Similar noisy/noiseless RMS values do not quantify their causal shares.

**Routing recommendation:** preserve both outcomes and continue truthful experimental reporting. I found no concrete contract violation warranting an in-scope product correction. A causal investigation would need a separately frozen diagnostic comparison, such as evaluating supplied true parameters versus the fixed estimated profiles, without changing or relabeling these runs. It would be supplemental known-input evidence, not a repaired observation-only result.

Confidence is high in the recorded stopping-stage conclusions; confidence in any specific root cause is low without that discriminating evidence.

This is read-only advisory diagnosis, not formal acceptance. No root cause or implementation defect has been proved. No retuning, additional fit, product edit or test edit was performed or authorized by this advice.

Public-copy links are relative; the verbatim local advisory original remains in `artifacts/ra14/advice/calibration-diagnosis.md`.
