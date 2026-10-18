# Observed unknown-phase carrier scan comparison

**Version 1.0.** Each listed carrier receives a local unknown-phase fit from the same nominal commands and fixed calibration. A small objective does not identify a unique physical carrier. The [contract](../contracts/phase-carrier-scan-v1.md) and [usage guide](../usage/phase-carrier-scan.md) define the operation. The [machine-readable observation](phase-carrier-scan-comparison.json) preserves displayed values and input identities.

These are two actual generated groups from corrected-code observation `examples02`. Both have seven exposures, hidden unequal phase deviations and all five signed orders. The finite Fourier group uses a 2×3×3 sample grid; the raw spatial group uses a 1×3×4 grid. The second actually composes acquisition declaration, camera correction, raw point-bead calibration and empirical transfer adaptation. Its supplied camera offset is 11 count and response is 1.8 count/signal. Calibration reference +0.24 rad and specimen reference −0.13 rad imply an explicit −0.37 rad adapter shift. Truth is intentionally present in each caller-listed policy; this is no inferred search.

The evaluator constructs a separate spatial convolution operator and solves the full-space nuisance problem independently. It evaluates the returned phase point, without requiring identical optimizer trajectories. Define `J=0.5*||r||²` for the full normalized residual and `ΔJ=J_product−J_independent`; both are dimensionless. Phase root mean square (RMS) error uses wrapped fitted-minus-hidden differences in radians. Residual/Jacobian evaluation counts are reported separately for each row.

| Group | Carrier (y,x), policy role | Independent J | Signed ΔJ | Phase RMS error (rad) | Termination | Residual/Jacobian evaluations |
|---|---|---:|---:|---:|---|---:|
| finite fourier | (0, 0), wrong | 1.58848 | -2.220e-16 | 1.456e+00 | stagnated | 33/28 |
| finite fourier | (1, -1), truth-listed | 5.12439e-29 | -4.662e-29 | 8.971e-16 | stationary | 7/7 |
| finite fourier | (4, 2), period alias | 5.12439e-29 | -4.662e-29 | 8.971e-16 | stationary | 7/7 |
| finite fourier | (1, -1), duplicate | 5.12439e-29 | -4.662e-29 | 8.971e-16 | stationary | 7/7 |
| raw spatial | (0, 0), wrong | 0.599461 | +1.110e-16 | 1.820e+00 | stationary | 34/19 |
| raw spatial | (1, -1), truth-listed | 1.00437e-29 | -4.678e-30 | 9.883e-16 | stationary | 6/6 |
| raw spatial | (4, 3), period alias | 1.00437e-29 | -4.678e-30 | 9.883e-16 | stationary | 6/6 |
| raw spatial | (1, -1), duplicate | 1.00437e-29 | -4.678e-30 | 9.883e-16 | stationary | 6/6 |

Sanity check: `(4,2)` and `(1,−1)` agree modulo the Fourier detector's `(3,3)` grid; `(4,3)` and `(1,−1)` agree modulo the raw detector's `(3,4)` grid. Equal fits for those aliases therefore supply no physical uniqueness. The largest absolute returned-point objective difference is 2.22×10⁻¹⁶. Near-zero objectives have no claimed relative-accuracy bound. The wrong raw carrier still terminates `stationary`, with phase RMS error 1.82 rad: stationarity alone proves no recovery.

A separate intervention sets every transfer component exactly to zero. All four rows remain `no_observable_specimen`, with zero residual/Jacobian evaluations. Their normalized residual RMS is 0.6803650188391814; the signed independent discrepancy is +2.22×10⁻¹⁶. Missing specimen information is retained as unavailability, not certified physical zeros.

The actual producer returned 0 without timeout or stderr. Its original manifest covers 21 members; 15,820 source/input/environment fingerprints agree before and after generation and match the subsequent coordinator endpoint check. Full data, evaluator truth, producers, logs and original dirty Git records remain local evidence. They are not installed entrypoints or complete fresh-clone reproduction assets. The manifest and association hashes in the JSON identify that observation; clean-candidate admission is separate. Hash equality proves no continuous filesystem/process custody, and macOS shared-cache library bytes have an explicit census limit.

These small periodic observations establish numerical agreement at returned points and local error against generated truth. They establish no arbitrary-start recovery, measured instrument accuracy, scalable dense-volume algorithm, automatic winner or complete raw workflow. Full verification and independent candidate review are recorded outside these tracked observation bytes.
