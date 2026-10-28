# Investigate the poor recovery recorded in PR53

The owner requested preserving and merging PR53, then continuing the investigation in a new PR on October 28, 2026. PR53 was merged as `3b4fe0239823febe9a878d3e838b416319f104bd`; its software tree is unchanged from the tested final candidate. Its original observations, estimates, figures, errors and limitations remain the historical result.

This first follow-up is **report-only**. It explains the figures and finite specimen iterations, compares the ignored reference C algorithm with the actual study path, and measures a controlled forward-model discrepancy using existing public operations. It does not change scientific runtime, tests, fixtures, dependencies, gates or policy. An observed discrepancy is not a new accuracy requirement or proof of a product defect.

The coordinator owns the report and publication. The requested Astra advisor studies the reference implementation without copying, importing, compiling or shipping it. A separate diagnostic worker may invoke the unchanged public `build_kernel_cache` and `forward` operations and retain its commands, exact inputs and outputs. A fresh independent reviewer checks the final report, controls, arithmetic, provenance and claim limits. This report review does not replace scientific A/B/C/D for any later numerical implementation change.

## Controlled measurement

Use the existing paired reference source and frozen noiseless signal for orientation 0, phase 0, on the original full field. Keep the source, geometry, optical settings, pupil order and intensity gauge fixed. Compare true illumination with frozen estimated illumination; apply the documented calibration-to-specimen phase-origin transfer once. Explicitly round the source to the public operator's float32 input and report the rounding discrepancy. Use the original frozen prediction as a third comparison on the same exposure and denominator.

This uses truth only in evaluation after the original inference was frozen. It is neither a refit nor an images-only result. It measures discrepancy at one specified source; it does not compute the minimum attainable model error. One exposure does not explain the aggregate error across all 15 exposures. No seed selection, spatial alignment, fitted scale, extra source-volume factor or replacement of the original metrics is allowed.

Record interpreter/library versions, source identity, input/output hashes, physical units, actual commands/status and timing. Validate imports, geometry and recorded settings before expensive calls. Preserve operation failures and diagnose before retrying. No numerical time, review or repair cap was imposed by the owner. Operational timeouts mean incomplete evidence, not success.

## Checks and continuation

Before publishing, run the unchanged full-local `make verify` gate on the clean exact candidate and obtain fresh independent report review. Required CI platforms remain Ubuntu 24.04 and macOS 15; percentages remain advisory, while native coverage reports and every configured gate remain required. Final candidate/check results belong in the PR and retained evidence, not a tracked status rewrite after verification. No authority to merge the new PR is inferred.

The sole live state and cumulative accounting remain under `artifacts/pr53-retained/`, with new experiment and publication evidence under `artifacts/pr53-recovery-investigation-20261028/`. Preserve the original archive, frozen arrays, figure asset references, legacy source and environments. Retain new diagnostic scripts, outputs and receipts as reproduction evidence. Inventory any task-created scratch and owned processes at completion; do not delete evidence or unrelated material.

Subsequent convergence comparisons, specimen-informed illumination estimation or reconstruction changes require a concrete scope and the applicable scientific route. This report supplies evidence for that decision; it claims no repaired reconstruction or resolution gain.
