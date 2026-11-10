# Inventory and accounting audit

Baseline: `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`, tree `0fa2edf2df263fa08110daa26ceb22c847b2900b`. Report-only discovery; no source edits, tests, installations, builds, or scientific execution. Root instructions and the test-audit procedure were read. No Superpowers or delegation. Selected capability: Sol/high per assigned model guide; actual served model and token/cost metering are unknown.

## Reconciled declaration ownership

| Accountable lane | Test files | Declarations | Parameter-expanded examples established by source | Test LOC | Support/data files | Support/data LOC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| scientific | 28 | 413 | 2078 + one unresolved generated family | 15073 | 19 | 13067 |
| neutral | 5 | 113 | 386 | 3311 | 5 | 1478 |
| infrastructure | 19 | 197 | 563 | 9481 | 15 | 3680 |
| Total | 52 | 723 | 3027 + one unresolved generated family | 27865 | 39 | 18225 |

Each of the 723 declaration IDs occurs exactly once in [inventory.json.gz](inventory.json.gz). Scientific owns `test_c_*`, `c_*` and `ce08_*` helpers/data. Neutral owns `test_mrc*`, `test_raw_acquisition*`, `test_imagej_export` and their fixtures. Infrastructure owns all remaining files, including ImageJ reader setup/timeout and shared-node tests. These are accountability assignments, not semantic retain/delete verdicts; primary lane ledgers own the obligation and disposition decisions.

388 declarations have explicit parametrization, across 458 parameter axes; eight declarations additionally consume the two-choice `acquisition_record_consumer` fixture. There are 335 declarations without explicit parametrization. Examples are executions of declarations, **not a count of distinct decisions**. A dtype/layout/value row may be an equivalent example or an independent representation/branch guarantee. Row expressions, dimensions and names are retained verbatim in the JSON so the accountable lane can distinguish them. Test counts provide no authority to remove proof.

The unresolved generated family is `test_c_workflow_numerical.py::test_complete_actual_workflow_against_raw_finite_observer`: `CASES` combines five constructors. Source comments and constructor structure indicate 56 original controls + 2 literal metadata + 6 B1 + 2 B2 + 2 B3 = 68 rows, implying 3095 cases overall. This is a source-derived estimate pending reconciliation with the coordinator's actual collection/JUnit; no collection was launched here. Native metadata-only inventory helpers were extracted and executed in isolation: local accepted optics scalar representations = 4, decoded native storage representations = 2. No test module was imported and no scientific constructor was called.

## Size and support inventory

Physical text LOC is a reproducible scale measure, not executable statements or coverage. All lines in files count, including comments, strings, Java and JSON. Tests contain 86 Python files (45032 LOC), one Java file and four JSON files (1058 LOC together), totaling 91 files / 46090 LOC. Owned measured runtime contains 30 Python files / 9091 LOC: 25 `src/simrecon/` files / 7754 LOC and five `scripts/` files / 1337 LOC. The test/support Python-to-runtime physical LOC ratio is 4.95. Coverage statements/branches must come from the actual canonical run; they are unknown in this lane.

Shared support is assigned once:

- **scientific**: `tests/c_acquisition_fixture.py`, `tests/c_equivalence_retirement_fixture.py`, `tests/c_estimation_fixture.py`, `tests/c_known_fixture.py`, `tests/c_preparation_fixture.py`, `tests/c_workflow_oracle.py`, `tests/c_workflow_support.py`, `tests/ce08_error_budget.py`, `tests/ce08_finite_math.py`, `tests/ce08_finite_search.py`, `tests/ce08_recovery_budget.py`, `tests/ce08_recovery_freeze.py`, `tests/ce08_recovery_large_budget.py`, `tests/ce08_recovery_large_freeze.py`, `tests/ce08_recovery_large_model.py`, `tests/ce08_recovery_model.py`, `tests/data/ce08-large-recovery-v1.json`, `tests/data/ce08-matched-recovery-v1.json`, `tests/data/ce08-small-controls-v1.json`.
- **neutral**: `tests/imagej_export_fixture.py`, `tests/imagej_export_reader.java`, `tests/mrc_fixture_conversion.py`, `tests/mrc_fixture_events.py`, `tests/mrc_fixture_memory.py`.
- **infrastructure**: `tests/data/reader-public-input-context.json`, `tests/measurement_fixture_export.py`, `tests/measurements_fixture_commands.py`, `tests/parallel_runner_fixture.py`, `tests/reader_timeout_fixture.py`, `tests/shared_node_baseline_diagnostic_metadata_fixture.py`, `tests/shared_node_baseline_external_native_evidence_fixture.py`, `tests/shared_node_baseline_fixture.py`, `tests/shared_node_baseline_infrastructure_fixture.py`, `tests/shared_node_baseline_infrastructure_supplement_fixture.py`, `tests/shared_node_baseline_public_callers_fixture.py`, `tests/shared_node_baseline_public_failures_fixture.py`, `tests/verification_fixture_dispatch.py`, `tests/verification_fixture_tools.py`, `tests/verification_output_fixture.py`.

22 `pytest.fixture` declarations are inventoried with scope, autouse and parameter metadata. The JSON also lists every runtime file, direct subprocess site, lexical subprocess site and source import. Cross-boundary support: neutral M25 (`test_mrc_conversion.py:18`) imports infrastructure-owned `measurement_fixture_export`; its measurement exports and the enclosing verifier remain infrastructure obligations. Infrastructure shared-node/reader tests exercise the same ImageJ reader/setup/cache and real deadlines used by neutral export, even though their declarations stay infrastructure-owned. `reader_timeout_fixture.py` stays infrastructure-owned. Serialized correction ownership is required for any shared helper.

## Quantified repeated-work leads

1. **All files currently share one worker group.** `src/simrecon/_pytest_policy.py:8` declares an empty `PARALLEL_GROUPS`; line 18 assigns every unknown path to `serial-rest`. Canonical Make already requests exactly two loadgroup workers. Thus all 52 files / all current cases belong to one serial group despite two worker processes. `test_parallel_runner.py:17` also has an empty `SCIENCE` inventory. This is a bounded routing investigation, not evidence for changing worker count or weakening crash/omission/coverage checks.
2. **Whole scientific fixture catalogs are rebuilt for one selected row.** `test_c_workflow_numerical.py:51` rebuilds the five case dictionaries per `CASES` row and later calls B2/B3 constructors again for membership. `literal_metadata_cases` (`c_workflow_oracle.py:4122`) and `b1_cases` (`:4154`) each rebuild all `control_cases`. Therefore each selected row constructs the control catalog at least three times. At the source-estimated 68 rows and documented 56 controls, that is at least 204 complete control-catalog builds / 11424 control entries for 68 selected observations, before other constructors. Independent finite-oracle equations, distinct raw inputs, mutation isolation and returned-array ownership must survive any reuse. Scientific lane owns the preservation decision; this count is a construction lead, not a runtime profile.
3. **Verifier callers repeatedly create isolated repositories and phase evidence.** There are 79 syntactic direct `invoke` sites inside 74 test declarations; weighting by static parameter rows gives 247 potential direct sites (not dynamic execution counts: loops/branches/helper calls may change actual totals). By file: receipt 78; measurements 65; evidence outputs 47; output protection 35; external native evidence 13; public callers 9. Function-scoped fixtures directly serve 78 receipt examples, 60 measurement examples, 45 evidence-output examples and seven wheel-hash examples. These figures identify setup/observation-sharing candidates; live output-collision challenges, fresh identities, mutation isolation and distinct failure decisions must remain real.
4. **Subprocess surface is substantial and partly generated.** 52 direct AST subprocess invocation sites exist in tests/support (scientific 1, neutral 8, infrastructure 43); seven additional direct runtime sites give 59 total. Eleven further lexical call sites are embedded in generated Python strings, for 70 visible call sites overall. These are source locations, not process launches. Their exact paths/lines/commands are in the JSON. Imported aliases, dynamic command dispatch, subprocesses generated by dependency internals and Java process internals may add runtime launches; dynamic process counts remain unknown.

The strongest apparent lead is making existing two-worker routing effective, then measuring repeated verifier acquisitions and scientific case/oracle construction. No unsupported estimate of saved seconds follows. The genuine 180-second reader parent timeout and 15-second socket timeout, public compatibility, positive/rejection/operation-time cases and all 13 verifier phases remain binding.

## Historical PR83 accounting only

[PR83](https://github.com/david-hoffman/simrecon/pull/83) was recovered through the GitHub read tool; its body/metadata are retained in [pr83-history.json](pr83-history.json). The PR is closed, unmerged and draft; tested head `d9b2d9e108b9b23c087a9daadfbeb54b17b4d17e`, tested baseline `8f6b35ceda362944f00de44acbf7098989f157e4`, target main observed `edcf53b5d5c0f494c388944d3cfda5c04b9fda97`. It reports unresolved 17-path integration conflicts. No patch was applied, fetched into a branch, cherry-picked or treated as current preservation evidence.

| Historical measurement/charge | Retained fact |
| --- | --- |
| Old complete gates | 3666.65 s baseline; 1229.67 s old candidate |
| Old pytest | 3392.25 s baseline; 1185.32 s old candidate |
| Old cases | 11299 baseline; 11225 old candidate |
| Old declarations | 1902 original: 1843 retain, 57 consolidate, 2 repair; 3 supplemental cache declarations |
| Old fixed-profile acquisitions | Claimed 260 to 97 (163 removed) |
| Prior reviews/corrections | Fresh blind checkpoints, restricted C, fresh scientific D, separate bounded review reported; exact cumulative rounds/elapsed not published |
| Abandoned work | Low-value phase cache retained in historical accounting; focused ~3.03 s to ~1.08 s comparison did not justify machinery |
| Historical cleanup | Two operations; 1407 disposable units; 2346082304 allocated bytes; recovered free space unmeasured |
| Actual served model, tokens, money | Unknown |
| Local detailed PR83 artifacts | Not present in this checkout; PR says they were ignored local artifacts |
| PR83 comments/reviews through discussion endpoint | Empty returned list; no extra charge data recovered |

The 61-minute and 20-minute observations belong only to PR83 and its pre-C-equivalence scientific baseline. Neither is the current baseline or candidate. Its numerical coverage and memory figures likewise do not establish current evidence. Previous rounds, repairs, launches and spending are retained as unknown where unavailable; missing data is not zero.

## Current accounting and limits

User target: canonical verify under 600 seconds; pytest reported separately. No total execution/review/scenario/token/money budget was set. Coordinator owns the fresh baseline profile; no parallel test run or installation was launched by this lane. Baseline/candidate duration, pass count, coverage and memory results remain unknown until that profile supplies them.

Lane charges: one read-only inventory lane; no subagents; one successful AST inventory script plus refinements; two isolated NumPy-metadata helper inventories; one inefficient optional repeated AST query was stopped after approximately 33 seconds and replaced with a per-file parse query completing in 0.43 seconds. This diagnosis remains counted. No test/support/runtime source changes and no tests executed by this lane. Report artifacts and scratch only. Metering is unknown. Scratch retained for coordinator cleanup: `/workspace/work/test-apparatus-inventory/` (no owned process remains running).

## Per-file declaration reconciliation

| Lane | File | Declarations | Established expanded examples | Physical LOC |
| --- | --- | ---: | ---: | ---: |
| scientific | `tests/test_c_acquisition_2d.py` | 12 | 40 | 678 |
| scientific | `tests/test_c_acquisition_boundary.py` | 73 | 321 | 3007 |
| scientific | `tests/test_c_acquisition_composition.py` | 7 | 18 | 446 |
| scientific | `tests/test_c_acquisition_drift.py` | 8 | 37 | 349 |
| scientific | `tests/test_c_acquisition_filter.py` | 8 | 49 | 279 |
| scientific | `tests/test_c_acquisition_fitted_drift.py` | 5 | 14 | 260 |
| scientific | `tests/test_c_acquisition_preparation.py` | 10 | 88 | 403 |
| scientific | `tests/test_c_acquisition_transfer.py` | 9 | 38 | 493 |
| scientific | `tests/test_c_equivalence_retirement.py` | 11 | 49 | 232 |
| scientific | `tests/test_c_estimation_boundary.py` | 22 | 123 | 516 |
| scientific | `tests/test_c_estimation_composition.py` | 2 | 4 | 135 |
| scientific | `tests/test_c_estimation_overlap.py` | 13 | 31 | 266 |
| scientific | `tests/test_c_estimation_search.py` | 9 | 17 | 642 |
| scientific | `tests/test_c_independent_large_recovery.py` | 1 | 1 | 206 |
| scientific | `tests/test_c_independent_matched_recovery.py` | 1 | 1 | 237 |
| scientific | `tests/test_c_independent_small_controls.py` | 1 | 1 | 309 |
| scientific | `tests/test_c_known_assembly.py` | 13 | 20 | 312 |
| scientific | `tests/test_c_known_boundary.py` | 28 | 263 | 712 |
| scientific | `tests/test_c_known_filter.py` | 17 | 49 | 310 |
| scientific | `tests/test_c_otf.py` | 26 | 63 | 786 |
| scientific | `tests/test_c_otf_validation.py` | 27 | 201 | 532 |
| scientific | `tests/test_c_preparation.py` | 54 | 232 | 965 |
| scientific | `tests/test_c_workflow_00_known.py` | 2 | 5 | 145 |
| scientific | `tests/test_c_workflow_compatibility.py` | 5 | 6 | 208 |
| scientific | `tests/test_c_workflow_failures.py` | 2 | 3 | 133 |
| scientific | `tests/test_c_workflow_numerical.py` | 9 | 18 + CASES unresolved | 565 |
| scientific | `tests/test_c_workflow_records.py` | 19 | 101 | 1270 |
| scientific | `tests/test_c_workflow_validation.py` | 19 | 285 | 677 |
| infrastructure | `tests/test_coverage_combine_integrity.py` | 2 | 2 | 79 |
| infrastructure | `tests/test_delivery.py` | 5 | 5 | 291 |
| infrastructure | `tests/test_delivery_preflight.py` | 3 | 11 | 213 |
| neutral | `tests/test_imagej_export.py` | 16 | 55 | 1162 |
| infrastructure | `tests/test_imagej_reader_setup.py` | 13 | 23 | 318 |
| infrastructure | `tests/test_measurements_export.py` | 23 | 107 | 865 |
| neutral | `tests/test_mrc_conversion.py` | 26 | 26 | 563 |
| neutral | `tests/test_mrc_conversion_coverage.py` | 18 | 18 | 233 |
| neutral | `tests/test_mrc_conversion_keys.py` | 4 | 4 | 290 |
| infrastructure | `tests/test_parallel_runner.py` | 3 | 4 | 125 |
| neutral | `tests/test_raw_acquisition_declarations.py` | 49 | 283 | 1063 |
| infrastructure | `tests/test_shared_node_baseline_compatibility.py` | 13 | 22 | 637 |
| infrastructure | `tests/test_shared_node_baseline_diagnostic_metadata.py` | 2 | 44 | 152 |
| infrastructure | `tests/test_shared_node_baseline_external_native_evidence.py` | 4 | 13 | 385 |
| infrastructure | `tests/test_shared_node_baseline_infrastructure.py` | 10 | 39 | 492 |
| infrastructure | `tests/test_shared_node_baseline_infrastructure_supplement.py` | 9 | 15 | 318 |
| infrastructure | `tests/test_shared_node_baseline_public_callers.py` | 22 | 43 | 1272 |
| infrastructure | `tests/test_shared_node_baseline_public_failures.py` | 2 | 2 | 159 |
| infrastructure | `tests/test_source_free_check.py` | 24 | 65 | 625 |
| infrastructure | `tests/test_test_run.py` | 5 | 5 | 99 |
| infrastructure | `tests/test_verification_evidence_outputs.py` | 17 | 46 | 1563 |
| infrastructure | `tests/test_verification_output_protection.py` | 11 | 31 | 713 |
| infrastructure | `tests/test_verification_receipt.py` | 25 | 79 | 897 |
| infrastructure | `tests/test_verification_wheel_hashes.py` | 4 | 7 | 278 |
