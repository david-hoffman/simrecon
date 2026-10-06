# Proposed scientific migration roadmap

**Version 1.0** Git versions revisions.

This is a work map for the independently authored Python NumPy/SciPy library. The owner approved the functional architecture and first MRC conversion contract; the conversion library/CLI have been implemented and accepted. Their approvals/evidence remain in [architecture intake](tasks/architecture-intake.md#current-state). Known-phase separation is now integrated through [PR #5](https://github.com/david-hoffman/simrecon/pull/5), with explicit `N >= 3` phases including unequal spacing. Later scientific work follows its own concrete contracts and root operating instructions. The historical setup/conversion allowances are not a total migration estimate. See [project scope](PROJECT.md) and [scientific context](SCIENTIFIC-CONTEXT.md).

Legacy algorithms may be studied, but new code must be written independently. The ignored `SIMrecon_svn/` tree must not be copied, imported, linked, or shipped. The observed programs `sirecon`, `radialft`, `otf2d`, and `wiener2d` are investigation evidence, not intended public interfaces or parity commitments. Their historical outputs do not establish numerical correctness; see [the baseline](setup/BASELINE.md).

## Remaining work checklist

Use this as the entry point for proposed future work. Setup execution history and final evidence remain in [the setup plan](tasks/setup-plan.md#current-state). Checking an item here does not authorize a scientific contract or reset any budget.

- [ ] Review and approve or reject the separate doctor documentation proposal.
- [ ] Resolve PR-creation identity if the owner needs to submit GitHub approvals. Agent commits must use codex as author and committer; commit metadata alone does not change the authenticated PR author.
- [ ] Complete the requested article-text extraction and algorithm notes for later milestones. The 2000 paper's full HTML text/notation/captions have [local Docling evidence and original notes](references/scientific/phase-separation-notes.md); the 2008 record remains citation-only. Paper figure capture was removed from scope by the owner. Record access/redistribution limits honestly.
- [x] Select the functional Python/NumPy library architecture and first legacy-MRC conversion contract. Approval/evidence are linked above; the architecture is reused for the next milestone.
- [x] Implement and independently review first-slice MRC image intake/output with Python and command-line interfaces; it is present in the integrated project baseline. The original task's exact results/limits remain in its own evidence record.
- [x] Deliver [the first numerical milestone](tasks/numerical-foundations-plan.md): conventions/independent expectations and known-phase 2D separation for explicit `N >= 3`, including unequal phases. The final merged/check record is [PR #5](https://github.com/david-hoffman/simrecon/pull/5); the task's tracked Current state is a pre-verification pointer. This supplies phase components, not a reconstructed image.
- [ ] Deliver 2D calibration representation/preparation. The requested [calibration foundations](tasks/otf-calibration-foundations.md) define the [sampled intensity-PSF contract](contracts/otf-calibration-v1.md), independent examples and a Pyotf illustration. The requested [implementation candidate](tasks/otf-calibration-implementation.md) now supplies `prepare_otf` / `Otf2D`, with [usage and signed comparison](usage/otf-calibration.md). Its exact verification/review evidence is external to the candidate tree; delivery and integration remain pending until that evidence and owner merge exist.
- [ ] Repeat for calibration, reconstruction, estimation/drift, 3D, and adapters as approved. Parallelize only independent slices; integrate prerequisites before dependent work.
- [ ] Improve ImageJ X/Y/Z/channel/time interpretation beyond initial MRC reader support through a separately approved adapter or reader integration. Preserve full axis information in the first library/file model and report viewer limitations; do not treat a flattened stack as full five-dimensional support.

Reuse the approved architecture. Scientific intake defines each next milestone before tests or implementation. Each numerical slice follows the current [root operating instructions](../AGENTS.md), with integrated prerequisites and full submission checks. This roadmap is a work map, not an alternate delivery policy.

## Work map and dependencies

| Proposed work | Decisions and reviewable output | Implementation dependency |
|---|---|---|
| Scientific intake using approved architecture | Select a bounded operation, acquisition model, public array interface, and independent evidence. Record the requested slice and concrete contract; resolve material scientific choices before dependent work. | Architecture, MRC conversion and known-phase separation are integrated prerequisites. A roadmap entry alone supplies no request for another numerical feature. |
| Array conventions and numerical oracles | Set axes and ordering, spatial/frequency units, precision, Fourier signs and normalization, band representation, malformed-input behavior, and justified tolerances. Establish small analytic examples and reference-data provenance. | Phase-array conventions are settled by the implemented [v2 contract](contracts/known-phase-separation-v2.md). New calibration/reconstruction conventions belong to their own contracts. |
| Known-phase separation | Independently implement the contracted separation operation through the array interface, using analytic expectations for the selected phase model. | Completed and integrated through PR #5. Reuse its explicit-phase interface; estimation and reconstruction are outside that operation. |
| Calibration representation and preparation | Define the optical transfer function (OTF) representation, sampling, normalization, origin, support interpretation and provenance through the [calibration contract](contracts/otf-calibration-v1.md). Use Pyotf for an optical illustration, with independent mathematical correctness fixtures. | Integrated array/phase foundations and the concrete calibration contract. Its sampled intensity-PSF preparation has a runtime/test candidate, documented in the [implementation record](tasks/otf-calibration-implementation.md). Dependent implementation waits for completed verification/review and integration. |
| Known-parameter 2D reconstruction | Compose contracted separation, band positioning, OTF weighting, regularization/apodization, and output sampling into a public reconstruction operation. | Completed, verified, and integrated separation and required calibration prerequisites; approved synthetic/reference fixtures and reconstruction contract. |
| Parameter estimation and drift | Select estimators, identifiability/conditioning assumptions, parameter units, failure behavior, and independent evaluation data. Add estimation to the established reconstruction path in bounded slices. | Completed, integrated known-parameter reconstruction and any required calibration. Investigation can start earlier; estimator implementation waits for approved prerequisites and its own checkpoint. |
| 3D extension | Decide the acquisition/order model, axial sampling and axes, order-specific calibration, output volume conventions, and 3D oracles. Extend existing components only where the approved model supports it. | Relevant completed 2D/convention/calibration foundations plus approved 3D contracts. Do not assume all 2D choices transfer unchanged. |
| Data adapters | Select needed formats and metadata mappings, with explicit units, ordering, validation, and round-trip expectations. Keep adapters outside the numerical array core. | Approved array and metadata contracts. Independent adapter slices can proceed in parallel once these boundaries are stable; reconstruction-dependent acceptance waits for the integrated numerical path. |

Keep the approved architecture's few responsibilities: array conventions and validation; numerical separation/recombination; calibration and estimation; optional data adapters. New scientific boundaries follow their approved contracts, rather than reproducing the four legacy programs.

## Parallel investigation, sequential delivery

Before scientific implementation, independent investigations can run in parallel: source/paper interpretation, calibration/data availability, candidate analytic oracles, and adapter metadata requirements. Record disagreements and unresolved assumptions. Investigation outputs inform intake; they do not silently select defaults or authorize coding.

After joint slice-plan approval, independent approved slices may use separate worktrees. A calibration slice and a separation slice can run concurrently if neither relies on unfinished behavior from the other. An adapter slice can do the same once its array/metadata boundary is approved. A dependent slice waits until its prerequisites are completed and integrated into its baseline; a promising draft or another worktree's passing result is not an integrated prerequisite.

For each slice, use the current [AGENTS.md](../AGENTS.md) and selected role skills. Delivery rules, actual human-set constraints and cumulative execution evidence live in those records; this roadmap adds no quotas, permission checkpoints, delivery procedure or controller.

## Decisions that block numerical commitments

Intake must resolve the relevant choices before tests derive expected results:

- Acquisition model, phases/orders, axes and band ordering, arithmetic precision, spatial/frequency units, Fourier sign, and normalization/scaling.
- OTF calibration provenance and representation, support boundaries, modulation/brightness interpretation, noise assumptions, regularization and apodization, and output sampling/cropping/padding.
- Available synthetic and experimental data, independent oracle derivation, conditioning assumptions, tolerances, and behavior on malformed or nonfinite inputs.

The [scientific context and primary references](SCIENTIFIC-CONTEXT.md#primary-references) provide investigation starting points. Legacy agreement is useful comparison evidence only after intended behavior and an independent oracle are established. Scope and effort should be reconsidered when those decisions and data are available; no total port estimate is asserted here.
