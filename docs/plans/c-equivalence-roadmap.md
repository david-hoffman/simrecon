# Rebuild the reference C mathematics before changing it

**Version 1.0 — 2 November 2026. Replacement for the RA roadmap.**

The owner requires the same mathematical algorithm as the retained C implementation, not bitwise output. The first corrective pull request removes incompatible scientific components. The next pull request begins rebuilding. A different objective, more general noise model, positivity constraint, boundary model, calibration estimator or stopping rule is not an equivalent port, even if it is scientifically defensible or passes its own tests.

## Baseline and integration

[PR #7](https://github.com/david-hoffman/simrecon/pull/7), merged as `1fd3c7e7b76cfd303f7850c8542e2d70da88f58a`, is the last foundation before the first demonstrably different reconstruction estimator in [PR #8](https://github.com/david-hoffman/simrecon/pull/8). It is **not** a certified C-equivalent implementation. It contains conversion, known-phase separation and a supplied-PSF Fourier preparation primitive, but no reconstruction algorithm. [Baseline audit](../reports/c-equivalence-baseline.md).

Use that scientific boundary, rather than inheriting the RA implementations. The corrective branch is based on the current merged target, PR #54 commit `8f6b35ceda362944f00de44acbf7098989f157e4`, so its removal diff actually removes later code when integrated. Preserve neutral conversion/delivery infrastructure. Do not reset main, replay the old scientific chain, or assume an ancestral branch automatically deletes newer target files.

The stricter retirement decision also removes the remaining old phase/OTF public APIs. Their limited algebraic identities are useful evidence, but no unchanged operation-level C equivalence has been established. Rebuild them under the C contract. PR #7 is a historical boundary, not a blanket retention exception.

Existing branches, commits, source C, original datasets and failed PR53/RA14 evidence remain intact. RA14 `0939754aaaf560ca554139d50084f9f0ccc296d8` is retained evidence, not a prerequisite implementation. The old RA chain is superseded as an execution plan; its historical records and charges remain. Do not continue RA15 or quietly merge the old scientific stack into this branch.

## One ordered stack

The roadmap and contracts belong in the first removal PR; do not insert a separate feature or roadmap-only PR before it. Each later PR depends on the exact accepted predecessor. No reconstruction improvements are mixed into this stack.

The owner now authorizes execution in **one new task per PR**. Each successor PR targets the previous completed step's branch (or its integrated descendant if already merged). After the current PR is fully ready for review with required independent review and local/platform evidence, its coordinator automatically creates the next task and passes the exact predecessor identity, contracts, evidence and cumulative accounting. Completion for this handoff does not require or authorize merging. Do not start dependent work from an incomplete candidate or run two coordinators for the same step.

The **first operational phase of every task is predecessor cleanup**: identify and remove that preceding PR's confirmed disposable fixtures and obsolete worktree with existing filesystem/Git commands after its writers close and required evidence/commits are retained. Preserve active work, original data/C source, durable evidence and still-required paths/environments; report protected or uncertain targets and continue with clear ones. Use the newer simplified cleanup policy retained in the ASD preservation contract. No cleanup software, mandatory cleanup-only tests or global reference-proof project is introduced. For CE01, inspect the last completed RA14 PR's recorded cleanup scope; the current correction worktree and RA14/other worktrees still supplying evidence or ASD source are protected until their dependency is resolved.

Preserve **all accepted Agentic Software Delivery (ASD) improvements since PR #7**, including those present in later completed work but absent from the merged PR #54 base. PR #7 is only a scientific historical boundary. The [ASD preservation contract](../contracts/c-equivalence-asd-preservation-v1.md) owns the explicit carry-forward and test-manifest reconciliation; this is part of CE01, not a separate PR before removal.

| PR | Contract and observable result | Depends on |
|---|---|---|
| CE01 | [Retire incompatible science](../contracts/c-equivalence-retirement-v1.md). Neutral I/O remains. Remove old estimators, public bindings, development entry points, stale tests and their exclusively used fixtures/helpers in this same first PR. Preserve tests for retained behavior. | Current merged target; PR #7 historical boundary |
| CE02 | [C preprocessing and separation](../contracts/c-equivalence-rebuild-v1.md#ce02-preprocessing-and-separation). First rebuild PR: the same correction, scaling, equalization, edge handling, transform and phase separation. | CE01 |
| CE03 | [C optical transfer preparation and sampling](../contracts/c-equivalence-rebuild-v1.md#ce03-optical-transfer-preparation-and-sampling). Same empirical bead operations, normalization, symmetries, support and interpolation. | CE02 |
| CE04 | [Known-parameter C reconstruction](../contracts/c-equivalence-rebuild-v1.md#ce04-known-parameter-filter-and-assembly). The same bandwise Wiener filtering and signed Fourier assembly, with no iterative specimen fit. | CE03 |
| CE05 | [C carrier and modulation fitting](../contracts/c-equivalence-rebuild-v1.md#ce05-carrier-and-modulation-estimation). The same overlap arrays, regression objective and finite search procedure. | CE04 |
| CE06 | [Remaining defined C acquisition modes](../contracts/c-equivalence-rebuild-v1.md#ce06-defined-acquisition-modes). Source-defined phase/drift, time/z equalization, alternative transfer/layout and dimensional modes are either ported with proof or explicitly listed as unsupported. | CE05 |
| CE07 | [One C-equivalent public workflow](../contracts/c-equivalence-rebuild-v1.md#ce07-public-workflow). Wire only accepted C stages; record every resolved scientific option and units. | CE06 |
| CE08 | [Independent reconstruction acceptance](../contracts/c-equivalence-rebuild-v1.md#ce08-independent-reconstruction-acceptance). Demonstrate mathematical agreement and useful recoverable spatial information, then characterize noise and limits. | CE07 |

CE06 cannot silently shrink a requested domain to make the final claim pass. The initial useful profile and the remaining mode ledger are specified in the [common contract](../contracts/c-equivalence-common-v1.md). An unsupported optional mode is a visible limit, not an implemented equivalent. Undefined C behavior cannot be promoted into a numerical oracle. Any repair of the reference itself requires a separately named change after the equivalent baseline, or an explicit owner decision if it blocks the required use case.

## Gates that prevent another drift

Each slice must discharge a row of the same C-equation/operation map. The map records C source revision/function/branch, mathematical inputs and outputs, signs, units, scale, coordinates, support, normalization, decision rules, Python public entry point and independent proof. It is required before blind test authoring. A local contract cannot replace the governing equivalence requirement. An unresolved mathematical choice stops that slice at intake; it does not become an implementer's default.

For every numerical slice, require independent mathematical expectations, discriminating counterexamples and the public composition test that uses the new component. Tests must distinguish the known wrong operation from the C operation. Testing a second copy of the Python formula or a forward/inverse pair sharing the same assumptions is insufficient. A fresh reviewer explicitly assesses the slice against the common contract and the end-to-end objective, not only its local tests.

Scientific retirement and rebuilding follow fresh native A/B/C/D ownership. Planning documents receive fresh independent review. Preserve full-local `make verify`, independent Ubuntu/macOS verification, coverage/report integrity and all applicable selected gates. M25 is the retained MRC conversion memory measurement, so its mandatory export and limit remain. No gate, dependency, test-discovery policy or delivery authority changes. Settled current-main coverage percentages remain advisory; required complete reports still bind.

Every PR has a useful figure. CE01 uses a clearly labeled conceptual architecture/removal figure. Numerical PRs use independently specified small observations, common units/scales, source/configuration provenance and signed differences. Figures are evidence, not substitutes for equations or acceptance tests. Do not rerun the expensive old full scene to produce progress pictures.

No optimization, more general estimator, positivity, alternative optics, tolerance relaxation or truth-based parameter adjustment enters this stack. Only after CE08 passes may a separately requested experiment compare a proposed improvement with the established reference baseline. Record disagreement honestly if C's own estimator does not meet the recovery goal; never tune the port away from C and call that equivalence.

## Status and ownership

This is an intake deliverable, not evidence of repaired runtime. [Task/current-state pointer](../tasks/c-equivalence-reset.md) identifies the exact document candidate, independent reviews, source pins and remaining execution work. Detailed rebuild contracts below are stage contracts: each requires its complete source-derived public packet before A starts; they are not permission to invent missing equations or interface decisions during implementation. The first executable work is CE01, followed by CE02. Merge, release and external messaging remain owner actions.
