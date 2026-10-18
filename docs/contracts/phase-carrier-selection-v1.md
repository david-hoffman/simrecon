# Caller-policy selection of unknown-phase carrier rows v1

**Version 1.0. October 18, 2026.** The standing owner roadmap continuation authorizes this dependency-ready Phase 5 operation above completed PR42. It applies explicit residual and local phase-information policy to the complete unknown-phase finite integer-carrier scan. It supplies no physical-carrier identification criterion.

## Public boundary

```python
from simrecon import VolumePhaseCarrierSelection, select_volume_phase_carrier

selection = select_volume_phase_carrier(
    images,
    order_otf=orders,
    candidate_carriers_yx=[(0, 2), (1, 2), (-1, -2)],
    initial_phases_rad=nominal_commands,
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen/calibration pairing",
    max_relative_residual=0.05,
    min_phase_rank=5,
)
```

Only images is positional. All nine keywords are required; ordinary argument-binding TypeError applies. The seven scan keywords and images inherit the [unknown-phase scan contract](phase-carrier-scan-v1.md), including its normative [observable estimator](observable-volume-phase-estimation-v1.md) and [fixed-transfer parent](phase-step-estimation-v1.md), unchanged. Images have phase/z/y/x axes, phases are radians, integer carriers are detector bins in y/x, and residuals are dimensionless. This operation accepts scan inputs, not caller-constructed records. Existing public interfaces remain unchanged.

## Explicit policy

max_relative_residual is a nonboolean Python or NumPy integer/floating scalar, finite in its source representation and after binary64 conversion, with converted value >=0. There is no upper bound. Both signed zeros and positive finite values that convert to zero are valid and use converted zero. Reject complex, string, array (including zero-dimensional), Fraction, Decimal and other non-integer/non-floating values. Unrepresentably large integers and conversion overflow are invalid.

min_phase_rank is a nonboolean Python or NumPy integer >=0. Extract its exact Python integer without floating conversion or fixed-width wrapping. Arbitrarily large integers are valid, including values greater than the exposure count; such a policy simply cannot pass any row. Reject floats, arrays, strings and other scalar types. Zero permits rank-zero stationary rows; it does not assert that their phases are informative.

Invalid policy raises SimreconError code invalid_volume_phase_carrier_selection_policy. Translate only expected TypeError, ValueError and OverflowError at the named policy extraction/conversion boundaries. MemoryError and unrelated exceptions propagate. Validate both fields before numerical scanning, including all-unavailable scans. No precedence among simultaneously invalid policy/scan inputs is specified. Preserve caller inputs, NumPy floating-error settings and warning selection on success and failure. These limits are caller decisions, not calibrated confidence or noise thresholds.

## Complete scan and eligibility

Perform the complete inherited scan. Row j is eligible exactly when:

```text
termination == "stationary"
AND relative_residual <= converted max_relative_residual
AND phase_rank >= exact min_phase_rank
```

Here phase_rank is the estimator's reported local projected phase-information rank. All comparisons are inclusive and operate on the returned represented fields, with no tolerance, hidden cutoff, recomputed objective, rounding or extra rank test. The existing estimator defines every field, availability outcome and numerical rule. evaluation_limit, stagnated, nuisance_rank_deficient, rank_changed and no_observable_specimen are always ineligible, even if their residuals are small or computed gradients are zero. A stationary row with rank zero and zero observations may pass a caller's zero rank threshold.

Evaluate every candidate from the same nominal commands and fixed calibration. An early passing row cannot hide a later eligible/unavailable row or operation-time failure. Do not sort, rank, minimize residual, prefer higher rank, deduplicate, reduce aliases, warm-start, infer candidates or stop early. Preserve the full scan's ordered carrier provenance, every diagnostic, independent per-row work and ownership guarantees. A genuine inherited validation/transform/solver/derived-arithmetic error fails the whole call with its inherited code; propagate allocation and unrelated exceptions under inherited boundaries. Return no partial result.

Return a frozen-binding VolumePhaseCarrierSelection with exactly four fields:

- candidates: the complete nonempty built-in tuple of ObservableVolumePhaseEstimate records in caller order, retaining all fields and unavailable outcomes. Distinct rows remain distinct records with independently owned mutable arrays, including duplicate/aliased hypotheses and across calls.
- eligible_indices: increasing built-in tuple of Python int zero-based indices passing all three gates.
- selected_index: the sole eligible Python int index when exactly one passes; otherwise None.
- failure_code: None for one; no_acceptable_volume_phase_carrier for none; ambiguous_volume_phase_carrier for two or more.

Result failure codes are values, not raised errors. Duplicates count as separate eligible rows and yield ambiguity. There is no extra winner copy; callers use candidates[selected_index] after checking selected_index. Field rebinding/deletion fails. Direct result construction needs no validation or deep immutability.

## Interpretation and evidence

This is an explicit policy on local diagnostic fits. Stationarity does not prove a minimum. Full phase rank and low residual do not prove global uniqueness, a correct carrier, a correct local basin, physical calibration applicability or uncertainty bounds. Integer detector-period aliases, specimen symmetry, sparse support and candidate-dependent observable dimensions can confound selection. No complexity penalty or physical discriminator is added. Actual carrier inclusion and initial basin reachability remain caller/evaluator limits. Zero rank thresholds deliberately permit uninformative stationary rows. Continuous carrier, drift/gain inference, scalable dense execution, the complete raw workflow and roadmap phases 7–9 remain outside this slice.

Use real public-entry fits and independent generated observations. A policy relation may use returned diagnostics as observations because the rule itself is the expectation; that establishes policy composition, not diagnostic accuracy. Independent Fourier/spatial forward expectations must support numerical claims. Do not mock rows to manufacture production eligibility or re-prove the entire accepted estimator suite. Include distinct sole/none/multiple outcomes, duplicate/alias ambiguity, nonstationary/unavailable rejection, exact inclusive endpoints, huge rank limits and paired permitted scalar representations. Test source-free channels before blind imports/probes.

Two actually executed independently generated observation groups must include hidden unequal phase deviations, all five signed orders, multiple hypotheses and an alias/unavailable or off-model control. At least one actually composes existing raw declaration/correction/bead calibration/transfer adaptation. Nominal commands and policy limits are recorded independently of hidden truth. True object/phases/carrier stay evaluator-only; disclose intentionally included truth as candidate coverage. Retain actual producer argv/status/time, complete before/after scientific/source/test/contract/guide/lock/build/environment/executable inputs, closed output manifests/associations and signed results. Report policy decisions separately from stored-objective/local phase error and physical ambiguity.

## Obligation inventory

| ID | Observable obligation and credible wrong outcome |
|---|---|
| S01 | Additive required signature, exact existing row/new result types and four-field frozen binding |
| S02 | Policy scalar/source-finite/conversion-finite grammar; paired signed-zero/underflow/NumPy positives |
| S03 | Exact nonboolean arbitrary integer rank policy, zero/huge positives and invalid types |
| S04 | Complete policy and inherited scan validation before numerical results, including unavailable data |
| S05 | Stationary-only eligibility; exact inclusive residual/rank conjunction and zero-rank semantics |
| S06 | Sole/none/multiple result values, ordered indices, duplicate and alias ambiguity |
| S07 | Every row retained with inherited fields/counts, independent starts and no early exit/ranking |
| S08 | Inherited genuine failure aborts call; original codes, propagation and no partial result |
| S09 | Owned independent mutable arrays, nonmutation and preserved warning/floating policy |
| S10 | Existing scan/estimator/calibration compatibility and independent hidden-phase observations |
| S11 | Actual usage/comparison and honest physical/global/scalability limits |

A expands every distinct decision/outcome and maps equivalent examples. B independently audits oracles, omissions and permitted positives; these groups are not a scenario cap.

## Ownership and delivery

High-risk scientific/interface route: fresh native gpt-6.1-sol/high blind A, fresh native blind B, restricted fresh native C and fresh native D. A owns tests/test_phase_carrier_selection.py and optional tests/phase_carrier_selection_fixture.py plus ignored independent public evidence. C owns only src/simrecon/_phase_carrier_selection.py, additive exports in src/simrecon/__init__.py, docs/usage/phase-carrier-selection.md and ignored actual producers/evidence. Existing helpers may be reused unchanged. Frozen reviewed tests/fixtures, unrelated runtime, dependencies/lock, checks/workflows/discovery/coverage, skills and policy are outside C ownership. B/D report only. Coordinator owns contract/task/PROJECT/roadmap/report/presentation/unique lessons. Separately named bounded current-root setup requires fresh independent acceptance before use.

Inherit binding 100% native Coverage.py executable-line/branch-destination targets globally/per package/per owned file for src/simrecon+scripts, never-imported/relevant subprocesses, zero exclusions, separately local/Ubuntu24.04/macOS15; no platform union. Advisory default percentages grant no waiver. Cheap current-root locked Python3.13.12/platform/import/reader/isolated-build checks precede expensive dependent work. Exact clean canonical make verify/all13phases, complete rawSQLite/JSON/allHTML, same-runM25 and wheel/source/staticversion0.1.0/environment/executable/lock/check/base/input evidence precede fresh D and the own stacked PR above PR42. Closed native CI with original per-platform archive qualification precedes delivery, final readback and exactly one actually started successor while authorized work remains. Human numeric limits are not set; unknown metering remains unknown. Preserve all inherited/current failed launches, reviews, corrections and charges. No Superpowers, merge/release, earlier-PR edits, owner-reference C execution/build or unrelated messages.
