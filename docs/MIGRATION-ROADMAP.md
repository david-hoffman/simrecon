# Proposed scientific migration roadmap

**Version 1.0** Git versions revisions.

This is a proposed work map for a pristine Python NumPy/SciPy library. It is not an approved task contract, scientific specification, or implementation authorization. The completed setup installed a Python/NumPy/SciPy scaffold and delivery tooling. The owner subsequently clarified, “We never decided on architecture.” The scientific library architecture remains provisional and needs explicit approval. The original eight-hour setup cap is not an estimate for the scientific migration; a defensible estimate needs agreed behavior, data, and numerical oracles. See [project scope](PROJECT.md) and [scientific context](SCIENTIFIC-CONTEXT.md).

Legacy algorithms may be studied, but new code must be written independently. The ignored `SIMrecon_svn/` tree must not be copied, imported, linked, or shipped. The observed programs `sirecon`, `radialft`, `otf2d`, and `wiener2d` are investigation evidence, not intended public interfaces or parity commitments. Their historical outputs do not establish numerical correctness; see [the baseline](setup/BASELINE.md).

## Remaining work checklist

Use this as the entry point for proposed future work. Setup execution history and final evidence remain in [the setup plan](tasks/setup-plan.md#current-state). Checking an item here does not authorize a scientific contract or reset any budget.

- [ ] Review and approve or reject the separate doctor documentation proposal.
- [ ] Resolve PR-creation identity if the owner needs to submit GitHub approvals. Agent commits must use codex as author and committer; commit metadata alone does not change the authenticated PR author.
- [ ] Complete the requested paper extraction and algorithm notes; current Docling records are citation-only. Record access/redistribution limits honestly.
- [ ] Decide and approve the library architecture: compare practical options for public interfaces, data model, numerical pipeline, module boundaries, dependencies, and performance needs. Record the decision in `docs/PROJECT.md`.
- [ ] Approve the first bounded product slice, conventions, independent expected results, and its own budget. The architecture interview selected legacy MRC image intake/output as the first requested slice, including Python and command-line interfaces; its detailed contract remains unapproved. Known-phase separation and reconstruction follow separate scientific intake.
- [ ] Deliver that slice through fresh A/B/C/D roles, passing full verification and measured statement/branch coverage, then a normal PR.
- [ ] Repeat for calibration, reconstruction, estimation/drift, 3D, and adapters as approved. Parallelize only independent slices; integrate prerequisites before dependent work.
- [ ] Improve ImageJ X/Y/Z/channel/time interpretation beyond initial MRC reader support through a separately approved adapter or reader integration. Preserve full axis information in the first library/file model and report viewer limitations; do not treat a flattened stack as full five-dimensional support.

Start architecture intake in a fresh local thread in the existing `simrecon` project. Read the project/scientific records and this roadmap; use the owner's latest architecture clarification when reconciling older approval wording. Obtain architecture approval before scientific implementation.

## Work map and dependencies

| Proposed work | Decisions and reviewable output | Implementation dependency |
|---|---|---|
| Architecture and scientific intake | Select a bounded operation, acquisition model, public array interface, and independent evidence. Prepare one joint slice plan and its contracts for owner approval. | Library architecture and scientific contracts remain unapproved. Compare architecture options and record owner approval before dependent scientific tests or implementation. |
| Array conventions and numerical oracles | Set axes and ordering, spatial/frequency units, precision, Fourier signs and normalization, band representation, malformed-input behavior, and justified tolerances. Establish small analytic examples and reference-data provenance. | Must be approved before dependent scientific contracts can supply test expectations. The phase-separation formula in scientific context is a candidate, not a settled convention. |
| Known-phase separation | Independently implement the contracted separation operation through the array interface, using analytic expectations for the selected phase model. | Approved conventions, oracle, and contract; then the required independent test/review checkpoint. Complete and integrate this prerequisite before dependent reconstruction work. |
| Calibration representation and preparation | Define the optical transfer function (OTF) representation, sampling, support, scaling, and calibration provenance; select only the preparation operations needed by the first reconstruction contract. | Approved array/metadata conventions and calibration contract. It can proceed alongside separation only when the slices are independent and each has its own approved inputs. |
| Known-parameter 2D reconstruction | Compose contracted separation, band positioning, OTF weighting, regularization/apodization, and output sampling into a public reconstruction operation. | Completed, verified, and integrated separation and required calibration prerequisites; approved synthetic/reference fixtures and reconstruction contract. |
| Parameter estimation and drift | Select estimators, identifiability/conditioning assumptions, parameter units, failure behavior, and independent evaluation data. Add estimation to the established reconstruction path in bounded slices. | Completed, integrated known-parameter reconstruction and any required calibration. Investigation can start earlier; estimator implementation waits for approved prerequisites and its own checkpoint. |
| 3D extension | Decide the acquisition/order model, axial sampling and axes, order-specific calibration, output volume conventions, and 3D oracles. Extend existing components only where the approved model supports it. | Relevant completed 2D/convention/calibration foundations plus approved 3D contracts. Do not assume all 2D choices transfer unchanged. |
| Data adapters | Select needed formats and metadata mappings, with explicit units, ordering, validation, and round-trip expectations. Keep adapters outside the numerical array core. | Approved array and metadata contracts. Independent adapter slices can proceed in parallel once these boundaries are stable; reconstruction-dependent acceptance waits for the integrated numerical path. |

Keep the design to a few responsibilities: array conventions and validation; numerical separation/recombination; calibration and estimation; optional data adapters. The installed NumPy/SciPy scaffold is a starting point for that decision, not evidence of approved library architecture. Concrete boundaries should follow the approved architecture and contracts, rather than reproducing the four legacy programs.

## Parallel investigation, sequential delivery

Before scientific implementation, independent investigations can run in parallel: source/paper interpretation, calibration/data availability, candidate analytic oracles, and adapter metadata requirements. Record disagreements and unresolved assumptions. Investigation outputs inform intake; they do not silently select defaults or authorize coding.

After joint slice-plan approval, independent approved slices may use separate worktrees. A calibration slice and a separation slice can run concurrently if neither relies on unfinished behavior from the other. An adapter slice can do the same once its array/metadata boundary is approved. A dependent slice waits until its prerequisites are completed and integrated into its baseline; a promising draft or another worktree's passing result is not an integrated prerequisite.

For each slice, use the existing [AGENTS.md](../AGENTS.md) practices and role skills: default at most five honestly counted contract scenarios, explicit approval for a larger slice, one task per worktree, and fresh independent A/B/C/D role sessions. Preserve agreed budgets and remaining review/repair allowances. This roadmap adds no delivery procedure or controller.

## Decisions that block numerical commitments

Intake must resolve the relevant choices before tests derive expected results:

- Acquisition model, phases/orders, axes and band ordering, arithmetic precision, spatial/frequency units, Fourier sign, and normalization/scaling.
- OTF calibration provenance and representation, support boundaries, modulation/brightness interpretation, noise assumptions, regularization and apodization, and output sampling/cropping/padding.
- Available synthetic and experimental data, independent oracle derivation, conditioning assumptions, tolerances, and behavior on malformed or nonfinite inputs.

The [scientific context and primary references](SCIENTIFIC-CONTEXT.md#primary-references) provide investigation starting points. Legacy agreement is useful comparison evidence only after intended behavior and an independent oracle are established. Scope and effort should be reconsidered when those decisions and data are available; no total port estimate is asserted here.
