# CE common contract: mathematical identity to retained C

**Version 1.0. Governs every slice of the replacement roadmap.**

## Requirement and target

For every supported input and explicit resolved configuration, Python must perform the same mathematical mapping and finite decision procedure as the selected retained C call path. Equality is after a declared, invertible representation/unit/sign/origin conversion, if any. No data-dependent post-hoc gain, phase, registration or normalization may hide a mismatch. Bitwise agreement is not required. Finite-precision error is assessed separately from changes of estimator, domain or decision rule.

The source target is retained SVN revision 307: `sirecon.c`, `helpers.c`, `small_math_funcs.c`, `drift_n_phasestep.c` for reconstruction, and `mainfile.c` for `radialft` preparation, with selected headers/build routing pinned before execution. The local evidence records content hashes, not just a revision label. Source C stays ignored and unshipped; Python is independently written. Existing prohibition on building/running/linking/importing C remains. No binary-output parity is claimed without an independently supplied matching C output/configuration bundle.

Initial useful profile: ordinary stationary 3D, three directions, five phases and orders 0/1/2; supplied detector spacing, optics, background/flat field, phase policy, order-transfer arrays and positive finite Wiener parameter; explicit zoom and taper/suppression options. Lateral dimensions use the C real-transform storage constraints; valid dimensions, table coverage, interpolation stencils and all index ranges must be specified in CE02/03 public packets. Do not guess missing metadata or silently turn requested features off. Arrays remain parameters, not one chosen phantom. Full parameter/domain matrices precede tests.

Default C camera scaling, sum equalization and edge processing are part of the mapping when selected. Ordinary reconstruction is not the historical pupil/integrated-source forward model. A simulated test dataset must be independently specified in the C acquisition coordinates. Source masses, output intensities and detector counts must not be silently equated.

## Defined quirks versus undefined targets

Preserve deterministic, mathematically defined source behavior even when surprising: sign/scale conventions; support inequalities; finite search ordering/ties; self-conjugate/Nyquist treatment; taper placement; scalar order-noise factors. For example, C's separation loop leaves the stored lateral Nyquist pair unseparated, and its embedding chooses a positive Nyquist lift. Neither may be silently replaced by a cleaner full-plane separation or split endpoint.

Do not use undefined memory contents, invalid interpolation accesses, singular arithmetic or nonfinite output as a numeric reference. The initial profile excludes axial padding that exceeds the allocated Fourier workspace (`bigbuffer` uses original `nz`, while its transform/assembly use padded `nz0`), Bessel/two-objective paths with uninitialized/aborting behavior, and the automatic Wiener branch whose source accumulates an empty midfrequency set. An explicit positive `w` selects an existing defined C branch; it is not a replacement estimator. Evidence: `sirecon.c:919–957,2046–2070`; `small_math_funcs.c:580–609`. Public rejection must name the unsupported branch before numerical execution. These source findings are static, not observed executable failures.

Maintain a complete mode ledger for 2D/3D, radial/nonradial transfer layouts, phase options, time/z equalization, drift, zoom, taper/suppression, padding, Bessel/two-objective and Wiener selection. For each: implemented and proved; not yet implemented; or undefined/unsafe reference path with the exact reason. CE06 owns remaining defined modes; no blanket all-C claim follows from the initial 3D profile. An essential undefined branch requires an owner decision about a separately named corrected reference, never a silent local repair.

## Mathematical acceptance

Before A starts a numerical slice, its public packet must contain:

1. Exact source identity and selected C control-flow branch, with a complete equation/operation map from input to output. Trace the caller, not merely a convenient helper.
2. Explicit public Python inputs/outputs/errors, dimensions, units, coordinate origins, phase/order naming, transforms/normalization, boundary/Nyquist rules, valid/invalid representation and operation-time failures. No unresolved scientific choice is delegated to C.
3. Every distinct supported decision/outcome and meaningful counterexample. The independent test author derives tolerances from input representation, precision, operation counts, conditioning and observer error **before** observing product discrepancies.
4. Independent algebraic/finite-sum expectations and public-entry composition. Source-derived mathematics is legitimate; importing production helpers or copying the runtime formula as the only oracle is not.
5. A cross-stage obligation linking the slice to the actual final reconstruction path. Separate equivalent primitives left unused do not discharge the workflow requirement.

On a fixed, well-conditioned branch, compare intermediate values and final outputs under predeclared meaningful absolute/relative error bounds. No blanket epsilon, adjusted threshold, favorable-only parameter sweep or arbitrary accuracy guarantee. Near numerical decision boundaries, explicitly characterize sensitivity; do not certify a different finite algorithm merely because it shares an asymptotic optimum. Full cross-order covariance weighting, an iterative constrained inverse or a new calibration objective fail equivalence even if they appear more accurate.

At minimum independent discriminators cover: phase signs/factors; complex transfer conjugation; normalization/DC/constant and displaced-point amplitude; unequal phase designs and variance factors; negative orders and all-axis reflection; origin conversion; weak/zero support; self/other support boundary inequalities; even Nyquist; noninteger carrier; native-filter-before-relocation; `w²`; taper/suppression placement; finite carrier-search order and stops; data-dependent equalization; and the end-to-end selected call chain. Cases are requirements, not a test-count quota.

Known-parameter checks precede nuisance estimation. Full workflow acceptance must use independently generated observations; self-replay through a shared forward model is insufficient. Recovery, mathematical equivalence and agreement with supplied owner C outputs remain separate reported outcomes. No resolution claim follows from smaller output pixels. A failed recovery case is preserved and diagnosed without changing the equivalence target.

## Ownership, validation and continuity

Scientific slices, including retirement of public scientific APIs, use fresh native A (tests), B (blind oracle review), restricted C (named runtime only) and D (fresh exact-candidate review). Blind packets contain public expectations, never old implementation/history, discovery inventories, coverage maps or current-task implementation lessons. Planning/advisory source audits do not supply A/B/D acceptance.

Coordinator owns roadmap/contracts, historical archive status, active usage, source maps, figures, task state and role launches. Scientific C cannot change reviewed tests/fixtures, workflows, check/coverage settings, dependencies, policies or unowned interfaces. Removing obsolete positive tests is separately named A ownership and reviewed by B, with retained neutral obligations mapped to keepers. No tests are deleted just to get green.

Inherit installed exact-candidate `make verify` and configured platform/report gates. Required scientific review and all check failures remain blocking for publication. Each stage has its own worktree and depends on completed prerequisites. No merge, release or external message is authorized by this contract. Preserve original RA evidence and cumulative role/review/correction charges. Numeric budgets are not set; unavailable model/metering/cost measurements are unknown. Routine supported housekeeping applies only to positively identified task-created disposable scratch.
