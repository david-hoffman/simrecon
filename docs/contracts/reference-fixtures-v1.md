# On-demand scientific reference fixtures

**Version 1.0.** The owner requires the two current documentary reference datasets to be generated on demand. This contract authorizes exactly that slice. Historical comparison, verification, model-calibration and optical illustration evidence stays outside its retirement scope.

Baseline: `1fb5afb3661bdb80614c68d6a79fa04a83cd9774`, tree `056e31b2b86c2ffec59726e0c88dea746ecf22cf`, independent main. The four frozen helper/dataset hashes and both historical blob hashes were directly verified on this baseline. The task has no runtime dependency on empirical-transfer consumption. Route: high risk because the exporter must preserve independent scientific calculations and custom-oracle meaning. Fresh native A/B/C/D are required. No human numerical limit is set.

## Proposed public command and lifecycle

Add one development command, invoked with the locked project interpreter:

```sh
.venv/bin/python scripts/generate_reference_fixtures.py otf
.venv/bin/python scripts/generate_reference_fixtures.py reconstruction
```

Exactly one required selector chooses one complete JSON document on stdout. The two selectors are the only requested dataset families. The exporter accepts no caller scientific arrays, settings or tolerance knobs. It creates no files or directories and has no persistent/default output path. The caller creates a standard `TemporaryDirectory`, redirects stdout to a JSON file there, checks process success, consumes/renders it while the context exists, and lets the context clean it up. Documentation must show this full lifecycle, not a redirection into tracked docs. Compute the document before emitting JSON; any generation or output failure is non-success. No transaction, recovery, daemon or automatic repair promise is introduced.

Fresh generation provenance remains separate from the historical compatibility document. The caller/coordinator records actual generator/helper/lock/config/interpreter/version/platform hashes, command, selector, candidate commit/tag/dirty version inputs and generated-output digests in its generation evidence. Do not inject current provenance into historical checkpoint fields or claim that rerunning a generator recreates an original role's acceptance. No fresh-provenance schema or persistent evidence writer is required from the exporter.

## Observable requirements and preserved meaning

R1. Both JSON documents are generated deterministically for unchanged material inputs, using compact source formulas and the existing frozen scientific helpers. Do not embed or encode a copy of either retired JSON payload, generated arrays, base64 data or a compressed replacement fixture in source/tests/docs. Small case definitions, formulas, scalar parameters, historical identity strings and digest constants are permitted.

R2. Preserve all historical scientific fields exactly: schemas, field/case ordering, IDs, shape, acquisition order, dtype labels, C-order representation, real/imaginary complex layout, axis ordering, origins, source text including whitespace, units, parameters, accuracy/eligibility fields, expectation values and physical limitations. Preserve parsed numerical values bit for bit at binary64 representation and preserve exact integers. Before retirement, compare every scientific field and reconstruct acquisition bytes as C-order little-endian float64. Required historical digests are:

- OTF dataset: `ba2dcd790738cf950b184995e1c12935266ddaa1738c9f874b46a6dd442c9dcf`.
- Reconstruction dataset: `64decad0389d332100bee202a02a8bafacd1c942e324dff992babccb8ca88541`.
- Commensurate acquisition: shape `(2,7,7,9)`, 7,056 bytes, SHA-256 `83281edcbaf738af9f78b025630a27ed50f8270349114fb7b7bbca427ffc97e2`.
- Fractional acquisition: same shape/bytes, SHA-256 `bb1f007740ae091fdae2037bf83cae210147c6d5e0bf3d343fc682e14520bcc5`.

The acquisition digests were independently recomputed from the existing JSON during intake by little-endian binary64 packing; both matched their recorded values. This was parsing/hashing, not generator or product execution. Full JSON byte equality is checked and reported only if historical serialization is reproduced; a whitespace-only difference is not a numerical failure, and exact serialization is never claimed without observed equality. A numerical/dtype/digest mismatch blocks retirement and requires diagnosis; do not normalize it away or substitute a tolerance.

R3. Frozen helpers remain byte-identical:

- `tests/otf_calibration_fixture.py`: `ec4edf3874ed2ebf91afae4e6f8ea2d0469381fc35382725150c10ceda010f27`.
- `tests/reconstruction_fixture.py`: `12af3e75c815e38edbd2e1d8de0c3ddf64911117a074e0bd783ac518e02a01cd`.

Do not extract, refactor, share or alter these reviewed sources. OTF uses the existing six analytic cases, signed modes and normalized negative-exponential formula. Preserve its historical binary64 `sqrt(3)` display rounding; the helper's high-precision rational roots are not an interchangeable rounded table. Preserve the `uint8` documentary label for separable-mixed without changing the helper's platform-integer construction.

Reconstruction uses `phantom(False/True)`, its 85-digit roots/finite convolution, analytic full complex transfer, object truth, stored-data estimator, budget and denominator measurements. Add only the missing export adapter: independent PSF and native 7x9 unit-brightness unilluminated observation from the already approved object/kernel formulas, Generate kernel and real object samples with the frozen 85-digit Decimal formulas, then round each scalar to binary64 before conventional convolution. For each output (y,x), initialize a binary64 total to 0.0; visit kernel hy=0..6 outer and hx=0..8 inner and left-fold `total += float(kernel[hy][hx]) * float(object[(y-hy)%7][(x-hx)%9])`, using separate binary64 multiplication and addition. Store total. This explicit order reproduces all 63 historical conventional-plane bit patterns in both cases. Preserve PSF scalar final rounding and all historical values under R2. The matching recipe is sufficient reproduction evidence, not proof of the unavailable historical wrapper source. Conventional observation is not a phase average. Never call product numerical operations as an expectation oracle. Constructing public `Otf2D` through the frozen helper is representation, not scientific validation. Preserve its source-free diagnostic import behavior.

R4. Keep historical observation/provenance claims historical. OTF FFT consistency residuals and original intake generator/environment/manifest digests are original observations, not newly calculated mathematical truth. Reconstruction's `independent_input_hashes`, historical creation label, B4 checkpoint `B4:82bcbfe1a41cc5d0439e89d0dbb0bebf7e5b315b37801617cf7b57ed04c8602b`, and verdict digest `fa131979cdab582d43e5b637593706b397ba4fb40062ec676b741034f2045cdd` remain facts about the original checkpoint. Neither generated file is product output or new independent acceptance. Fractional estimator/object bias stays an example limitation, not a rejection threshold or universal bound.

R5. Retire exactly the two named current datasets only after equality/provenance evidence and required review. Replace live convenience links in the OTF contract, fixture notes and reconstruction report with the recipe/case descriptions and explicit historical-resolution guidance. Keep accepted packets, hash allowlists, historical task ownership and retained comparison/manifests unchanged. A historical reference must resolve to its exact Git revision/path/hash, not to a rewritten current convenience file. Before retirement, verify the historical blobs at OTF integrated commit `a44e9d0c67403d5a001340b65ba04ea2f559256a` and reconstruction integrated commit `5e231d3d27dfd843de776de5ac80d3d46c0c5727` resolve to the named dataset hashes. Do not require CI to fetch Git history as its sole oracle: permanent tests can retain compact digests and independently generated mathematical checks without retaining payloads.

R6. Preserve product APIs, dependencies, frozen tests/helpers, all gates/discovery/coverage configuration, retained evidence and unrelated documentation. No optical simulation, plotting dependency, estimator, formula, scientific tolerance or public library feature is authorized.

## Route, ownership and required roles

Use **high risk** for the combined slice. Pure serialization of an already exposed complete document could be bounded, but this exporter includes auxiliary scientific calculations and exact preservation/custom-oracle reasoning. OTF display-root rounding also needs independent assessment. The small code size does not lower that impact. One combined high-risk contract avoids duplicate worktree/check/review overhead while keeping the scientific boundary honest. A later split is justified only by independent complete contracts, never to loosen C restrictions.

Fresh native blind A owns only new `tests/test_reference_fixture_export.py` and, if justified, `tests/reference_fixture_export_oracle.py`. A independently maps the contract, historical preservation hashes and mathematical anchors. A may read the approved contracts/notes, exact named historical datasets and frozen independent helpers as explicit public expectation inputs. It may not read exporter/product source or implementation-bearing current-state/history. Fresh blind B receives those public inputs, exact new tests and sanitized evidence; it independently audits meaning, legitimate outputs, numerical preservation and oracles before checkpoint acceptance.

Restricted C owns new `scripts/generate_reference_fixtures.py`, new `docs/usage/reference-fixtures.md`, and narrowly scoped live-link/recipe text in `docs/contracts/otf-calibration-v1.md`, `docs/references/scientific/otf-calibration-fixture-notes.md`, and `docs/reports/reconstruction-comparison.md`. C cannot edit frozen helpers, any accepted test/fixture, gates, workflows, config, policy or unrelated runtime.

The coordinator or one explicitly named mechanical retirement worker owns deletion of exactly the two documentary JSON files after equality is observed; C does not gain permission to delete frozen fixtures. The coordinator owns contract/task/packets and outside-tree evidence pointers. Fresh D forms its own assessment of the complete final candidate, including the actual retirement/docs changes, preserved sources, equality evidence and exact passing gate. Do not launch a role from this intake session; the coordinator owns launches. High-risk corrections follow blind A/fresh B and preserved checkpoints as required; scientific meaning changes return to intake.

## Scenario inventory and checks

| ID | Distinct observable outcome | Meaningful check and review source |
|---|---|---|
| S01 | `otf` selects exactly one valid six-case JSON document. | Public subprocess command, JSON schema/order and all scientific fields; B audits case/formula coverage. |
| S02 | `reconstruction` selects exactly the two historical cases. | Public subprocess command, shape/dtype/layout and complete parsed-field equality. |
| S03 | OTF origins/signs/frequencies/rounded display values stay exact. | Independent analytic anchors, all six entries, no tight product oracle from rounded tables. |
| S04 | Reconstruction acquisitions and parameter/order/source representations stay exact. | Both C-order `<f8` digest checks plus all scientific fields and dtype metadata. |
| S05 | Auxiliary PSF and conventional observation retain the approved finite convolution and rounding order. | Independent mathematical checks and exact historical arrays; distinguish a phase average. |
| S06 | Object/rounded-data estimator and eligibility/physical-limit fields stay distinct and exact. | Both integer and fractional cases, complex layouts, budgets/denominators, no new accuracy policy. |
| S07 | Repeated generation with unchanged material inputs is deterministic. | Two separate invocations per selector; compare output and scientific/provenance evidence identities. |
| S08 | Missing/unsupported selector rejects with nonzero status and no JSON success output. | Public subprocess argument checks, valid selectors paired with rejections. |
| S09 | Scientific/import/output failure reports non-success without fallback or a success claim. | Source-free diagnostics; meaningful public failure injection/closed stdout where feasible, no manufactured product-red requirement. |
| S10 | The exporter creates no files; caller temp lifecycle removes its own captured outputs. | Empty isolated working-directory observation and the documented TemporaryDirectory recipe exercised end to end. |
| S11 | Historical provenance remains immutable and fresh generation provenance is separate. | Compare historic metadata/checkpoint identities and inspect actual current generation evidence. |
| S12 | Only the two authorized datasets retire; live recipe links work and historical blobs resolve by pin. | Exact scoped diff, read-only historical hash checks, dataset/reference inventory and independent D review. |
| S13 | Frozen source, product behavior, config and verification gates stay unchanged. | Source SHA guards, scoped diff and existing full suite; D checks named ownership. |

Examples under S03 are the six OTF cases; S02/S04/S05/S06 include commensurate and fractional cases. These values are examples, not hidden extra behavior. Representation limits are the fixed documented small grids and binary64 layouts; no general large-array/input family is commissioned. Failure handling has no recovery/transaction promise. The command's normal argparse binding remains conventional. No new security/permission or deletion API is introduced by stdout export.

Run cheap locked interpreter/platform/install/import checks before dependent roles. Then focused new public command/tests, frozen-source guards and semantic/digest comparison. Exact-candidate canonical full gate is `make verify UV=/Users/davidhoffman/.local/bin/uv`, followed by configured Ubuntu/macOS CI without weakening any check. Owned exporter Python under `scripts/` remains in native global/per-package/never-imported/subprocess statement and branch measurement, with current JSON/HTML reports and exact counters. No runtime exclusions, skips or missing reports. The owner-approved installed coverage-policy amendment applies to this new main-baseline task: percentages are advisory; complete authentic native statement/branch measurements and current reports remain required. The authority and integrity rules are recorded in docs/PROJECT.md and docs/contracts/verification-coverage-advisory-v1.md. No gate or coverage configuration changes are commissioned.

Known failure, unverified required equality, incomplete selected coverage or missing independent acceptance blocks publication, draft PR included. No merge/release/external message is authorized. Final candidate/results belong outside tracked candidate bytes; prepare the task pointer before final verification. Do not alter frozen historical receipts/ledgers to claim current acceptance.

