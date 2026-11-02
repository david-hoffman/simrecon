# CE01: remove incompatible scientific components

**Version 1.0. First corrective PR. High-risk public scientific removal.**

## Baseline and outcome

Apply to merged PR #54 `8f6b35ceda362944f00de44acbf7098989f157e4`. PR #7 is the historical scientific boundary; no full C-equivalent runtime exists to revert to. Preserve current neutral I/O and delivery infrastructure. Remove all active scientific implementations without a complete C mapping, including old phase and OTF APIs. The next PR, CE02, begins rebuilding. This PR adds no replacement reconstruction or simulation algorithm.

The [baseline-specific file manifest](c-equivalence-retirement-files.json) records the PR #54 inventory, with input hashes: 32 runtime files (including the orphan scientific validation helper), 9 scripts, 49 dedicated scientific test files and 46 dedicated scientific fixture/helpers. Six mixed test/helper files receive selective edits. The owner's later requirement to preserve all post-PR7 ASD improvements requires the [ASD carry-forward](c-equivalence-asd-preservation-v1.md) and exact manifest reconciliation **before this inventory becomes an executable deletion checkpoint**. New neutral tests/helpers and accepted consolidations must be reflected; counts are observations, not deletion quotas. No future glob is authorized. RA scientific additions absent from this base must not be introduced just to delete them.

Retain `inspect`, `read`, `harmonize`, `write`, `declare_acquisition`, `export_imagej`, their required public records/errors, neutral CLI and delivery commands. Remove scientific imports and exports from `src/simrecon/__init__.py`; retain the exact neutral closure. No lazy alias, forwarding module, callable historical solver, fallback or development entry point may bypass retirement. The installed wheel must satisfy this boundary as well as the source checkout.

## Evidence and documentation

Preserve old scientific contracts, task accounting, reports, figures, source manifests and observed failed-study records as historical evidence. Preserve all original external arrays and the ignored C tree. Active README/PROJECT/usage and navigation must state that reconstruction is temporarily unavailable during the rebuild and identify the replacement roadmap. Historical pages retain original scientific claims in context, with a retirement notice where they could be mistaken for active instructions. Do not rewrite failures into successes or delete evidence to simplify verification.

Archive provenance is the immutable commits and retained artifact paths, not a promise that retired scripts remain installed. The manifest does not authorize deleting tracked historical evidence or any user's images. Retained evidence that needs an old environment keeps its original environment/path. Do not claim that current-package execution can reproduce a removed historical algorithm.

## Tests and preserved obligations

The owner's explicit follow-up requires stale tests to be removed **in CE01, the first corrective PR**, together with the retired code. This is a completion requirement, not deferred cleanup. Stale means the test's obligation belongs exclusively to a removed API, estimator, scientific convention or associated error behavior. Remove its obsolete expected outputs, snapshots, fixtures, generators and helpers when no retained obligation uses them. Do not leave stale tests disabled, skipped, marked expected-failure or disconnected from discovery.

A owns removal of the manifest's obsolete scientific tests/fixtures, narrowly editing mixed tests and authoring public retirement tests. This includes both successful-operation and rejection/failure tests for retired behavior. B independently reviews the old-obligation-to-keeper mapping and retirement oracle. The coordinator's implementation-bearing discovery inventory is not a blind A/B input; supply the public removal/retention obligations and exact allowed test paths. A/B must not inspect production to rediscover the deletion closure.

The six mixed files contain conversion/ImageJ, acquisition declarations, diagnostic and verifier obligations as well as science. Retain their neutral cases, fixtures and subprocess controls. Specifically preserve source-change/shortening rejection, opaque metadata export, required acquisition keyword binding, ImageJ layout/CLI, source-free diagnostics, verifier output/evidence protection, reader and process lifecycle. Remove only the scientific callers and associated constants/observers. No wholesale deletion of a mixed file or shared infrastructure helper is allowed.

| ID | Observable obligation | Independent acceptance |
|---|---|---|
| R01 | Only neutral public API remains; removed attributes/modules/scripts are unavailable. | Public imports, installed-wheel inspection and explicit absence checks; no source-text-only proof. |
| R02 | Neutral conversion, declarations, ImageJ and CLI behavior remain. | Existing real public I/O tests and retained mixed keeper mapping. |
| R03 | No active command, example, generator or dynamic import still runs retired science. | Entry-point/dependency inventory, relevant public subprocess controls and fresh independent final sweep. |
| R04 | Historical evidence, C source and original user data remain unchanged. | Exact named preservation checks against the retained source/evidence pins; no global cleanup project. |
| R05 | Stale scientific tests and their exclusively used expectations/fixtures/helpers are removed in CE01; mixed-file neutral assertions are preserved. | Exact file/declaration/obligation mapping accepted by B; no disabled stale tests, dangling test imports or deferred stale-test cleanup. No deletion quota or percentage-driven pruning. |
| R06 | Complete exact-candidate verification succeeds with every installed gate preserved. | Canonical full run, M25, required native reports, wheel/import/audit and configured platforms. |

## Retained measurement gate

The Makefile passes `--measurements-required` to `scripts/verify.py`. M25 is the retained **MRC conversion** resource measurement: `tests/test_mrc_conversion.py::test_m25_native_memory`, `tests/mrc_fixture_memory.py` and `tests/measurement_fixture_export.py`. Its requirement, actual same-run emission and 33,554,432-byte memory-increment limit remain unchanged. The scientific reconstruction resource tests are separate and do not own M25.

Preserve measurement-validation/export tests, the verifier and every verification phase, report requirement, coverage setting, workflow/platform and test policy. Carry forward the already accepted Makefile executable quoting and two-worker test execution under the separately named ASD ownership; do not freeze the older PR #54 Makefile and lose those improvements. No gate weakening or M25 migration is authorized or needed. A discovered concrete dependency failure must be diagnosed and routed through its existing ownership, not solved by removing a gate.

## Ownership and completion

- Coordinator: contracts, archive notices, active project/README/usage presentation, exact source/evidence pins and role launches; conceptual deletion figure.
- Named bounded ASD worker plus fresh reviewer: carry forward accepted neutral delivery infrastructure and its tests under the preservation contract; coordinator owns policy/documentation reconciliation with fresh independent policy review. This grants the scientific C role no infrastructure/test/policy ownership.
- Fresh native A/B: manifest's test/fixture removal/corrections and independent retirement assertions. A owns tests only. Preserve applicable initially passing evidence and all correction charges.
- Restricted fresh native C: manifest runtime/script deletions plus scientific import/export removal in `__init__.py`; no test/fixture/infrastructure edits.
- Fresh native D: exact integrated full-passing candidate; challenge missing neutral obligations, remaining executable science, evidence loss and gate preservation.

All [common-contract](c-equivalence-common-v1.md) boundaries apply. `make verify` precedes publication; configured platform proof remains required. Completion leaves the neutral product usable and scientific reconstruction explicitly unavailable, with no hidden alternate path. No destructive data cleanup, merge, release, closing old PRs or rewriting Git history is part of CE01.
