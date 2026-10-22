# Unknown-phase finite integer-carrier scan v1

**Version 1.0. October 17, 2026.** The standing owner roadmap continuation authorizes this dependency-ready Phase 5 composition above completed PR41. It evaluates independently unknown exposure phases for each caller-listed integer-carrier hypothesis using the accepted observable-subspace local estimator. It selects no physical winner.

## Public boundary

```python
from simrecon import scan_volume_phase_carriers

rows = scan_volume_phase_carriers(
    images,
    order_otf=orders,
    candidate_carriers_yx=[(ky0, kx0), (ky1, kx1)],
    initial_phases_rad=nominal_commands,
    max_nfev=200,
    gradient_tolerance=1e-9,
    step_tolerance=1e-10,
    source="declared specimen/calibration pairing",
)
```

Only images is positional. Every shown keyword is required; control values are examples, not defaults. One call handles one orientation/channel/time. Images have phase/z/y/x axes, N>=5 and positive spatial sizes. Phases are radians and carriers are integer detector bins in y/x. Transfer and normalized fit diagnostics are dimensionless. Return a built-in tuple of fresh ObservableVolumePhaseEstimate records, one per candidate in caller order, including duplicates. No new result-record type is introduced.

This combines roadmap Phase5 carrier hypotheses and independent phase deviations. The existing [observable phase estimator](observable-volume-phase-estimation-v1.md), including its [fixed-transfer parent contract](phase-step-estimation-v1.md), supplies the entire per-row mathematical model, exact structural support, local solve, accuracy, diagnostics, termination, representation and error rules. Those contracts are normative dependencies, not implementation suggestions. Existing APIs remain unchanged.

## Shared inputs and candidate grammar

Images, order_otf, initial_phases_rad, max_nfev, gradient_tolerance, step_tolerance and source inherit exactly the observable estimator's accepted representations, complete validation, independent snapshots, nonmutation, warning/floating policy and exception boundaries. In particular, signed observations, arbitrary complex/non-Hermitian or zero transfers, repeated initial commands, huge finite initial phases, endian/layout/read-only alternatives and ordinary VolumeOrderOtf subclasses remain permitted. All shared inputs remain fixed across hypotheses. Calibration already encodes origin, relative gains and the declared reference gauge; never apply them twice or fit a new gain.

candidate_carriers_yx inherits the candidate-table grammar of [known-phase carrier diagnostics](volume-carrier-diagnostics-v1.md): a nonempty exact built-in tuple/list of exact built-in tuple/list rows of length2, containing nonboolean Python/NumPy integers, or a plain signed/unsigned integer ndarray of shape(C,2), C>=1. Reject ndarray subclasses/masked arrays, bool/floating/object kinds, empty/ragged tables, scalar pairs, generators and other containers. Layout, endian and read-only alternatives are permitted. Extract exact Python ints without floating conversion, numpy.intp limits, magnitude caps or principal-period reduction. Huge, unsigned, zero and negative integers are valid. Snapshot the complete candidate table before numerical work and preserve declared values/order/duplicates.

Validate every shared field/sample and the complete candidate table before returning any numerical result, including when every row has no observable specimen or deficient information. Simultaneous-invalid precedence is unspecified. Concurrent external mutation is outside the guarantee. No intermediate candidate result escapes on a failed call.

## Per-hypothesis meaning

For each declared carrier ell=(0,ky,kx), evaluate the observable estimator with the same shared accepted inputs and the same initial phase commands. Each row is one independent continuous local start. Never warm-start from another candidate, use supplied phases as actual measurements, freeze their common offset, fit only a common phase, or replace the shared-specimen objective with a voxelwise separator residual.

The inherited finite periodic model uses every original real/imaginary observation row, all five signed orders, modular frequency placement and full complex fixed calibration. It is distinct from the existing known-phase scanner's nonwrapping overlap/free-gain objective. Do not borrow that scanner's overlap window, transfer interpolation or local missing-coverage outcomes. No new transfer queries are made. All candidates use the same observation and transfer component scales; carrier-dependent exact structural masks, observable dimensions, nuisance ranks and phase-information diagnostics retain their accepted meanings.

Retain every estimator field without replacing unavailable outcomes with a scalar sentinel or discarding a row. The row carrier_bins_yx is the original Python-int pair; source is unchanged. The allowed terminations remain stationary, evaluation_limit, stagnated, nuisance_rank_deficient, rank_changed and no_observable_specimen. Each row's nfev/njev records actual work for that row; there is no new aggregate evaluation counter or hidden total cap. max_nfev applies independently to each candidate's local solve. Equivalent finite organization of inherited arithmetic is permitted; solver trajectory/iteration bit patterns are not a cross-platform promise.

Unavailable estimator outcomes are ordinary returned rows and do not stop later candidates. A genuine inherited validation, transform, solver or derived-arithmetic error fails the whole call; it is not converted into an unavailable row or swallowed to continue. MemoryError and unrelated errors propagate under the inherited boundaries. Retain no partial public tuple. The implementation may share carrier-independent preparation, but public semantics and each result's work accounting must remain truthful.

Repeated carriers produce distinct records and independent mutable arrays. Every result array aliases neither caller storage, another field nor any other row/call, including duplicate and modulo-aliased hypotheses. Records keep the existing frozen-binding/mutable-owned-array semantics. An implementation that reuses cached row objects/arrays is invalid.

## Errors and interpretation limits

Use SimreconError code invalid_volume_phase_carrier_candidates for malformed candidate tables or expected TypeError/ValueError/OverflowError during their extraction. This is the only new stable code. Shared-input and numerical failures retain the fixed-transfer estimator's existing codes. Expected extraction exceptions translate only at that named boundary; MemoryError and unrelated exceptions propagate. Ordinary Python argument-binding TypeError remains ordinary. Message prose and simultaneous-invalid precedence are unspecified.

The tuple is a diagnostic scan, with no sorting, deduplication, ranking, selection, inferred search range or hidden acceptance threshold. A small residual, stationary solve, full phase-information rank or sole visually promising row establishes no unique physical carrier or global phase solution. Candidates related by detector-period aliases can fit the same model; sparse objects, symmetries and different observable dimensions can also confound comparisons. No complexity penalty corrects those comparisons. A fixed phenomenological calibration is used across candidates; the caller establishes its physical applicability. The operation supplies no guarantee that the actual carrier is listed or that its local basin is reached.

Continuous/fractional carriers, drift, unknown gains/calibration, positivity, noise likelihoods, automated physical acceptance, scalable large-volume execution, the complete raw workflow and roadmap phases7–9 remain outside this slice. Dense per-row execution and ordinary allocation failure retain the inherited limits. A candidate list length supplies no practical-memory/time guarantee.

## Behavioral inventory and independent evidence

These are obligation groups, not a scenario cap. A expands distinct decisions/outcomes and maps equivalent examples; B independently audits oracles, omissions and legitimate positives.

| ID | Observable obligation / credible wrong outcome |
|---|---|
| U01 | Additive required public binding; built-in ordered tuple of the existing result type |
| U02 | Exact table/container/row/scalar grammar, complete early validation and paired permitted huge/unsigned/layout cases |
| U03 | Full inherited shared-input validation, snapshots, nonmutation and original error codes, including unavailable rows |
| U04 | One same-command independent local fit per carrier; no phase/gain sharing or candidate warm start |
| U05 | Inherited five-order periodic objective, signs, normalization, modular negative reflection and structural support |
| U06 | All inherited phase/nuisance/design/availability diagnostics and actual per-row counts retained |
| U07 | No-observable/initial-deficiency/rank-change rows retained and later candidates still evaluated |
| U08 | Genuine operation-time failure aborts the call under inherited codes; unrelated/allocation exceptions propagate |
| U09 | Duplicates/order/original huge provenance; modulo aliasing is not deduplicated or presented as physical discrimination |
| U10 | Independent mutable arrays/frozen records across rows, fields, inputs and calls |
| U11 | Hidden nonuniform exposure phases and carrier hypotheses assessed against independently generated observations/objective |
| U12 | Fixed calibration/gauge/origin once; explicit compatibility with empirical calibration/adaptation and existing estimators |
| U13 | Executed usage and measured comparison separate stored-objective error, local phase error and carrier/physical ambiguity |

Prefer real public-entry observations with independently written finite Fourier sums or spatial convolution and independent nuisance/objective expectations. Agreement with another product call alone is no scientific oracle. Public estimator composition may provide a compatibility check alongside the independent oracle. Do not re-prove the complete accepted estimator test suite through this new wrapper; fill its distinct composition, candidate handling and isolation risks.

Two actually executed independently generated groups must include unknown unequal phase deviations, more than one carrier hypothesis, all five orders and an unavailable/aliased or off-model control. Keep true specimen, phases and carrier in evaluator evidence, separate from scan inputs. At least one group actually composes existing raw declaration/correction/bead calibration/transfer adaptation before the scan. Initial commands and candidate policy must be recorded independently of hidden truth; disclose intentionally included truth as candidate coverage, never as inferred search. Retain producer argv/status/time and complete before/after input/source/fixture/contract/guide/lock/build/environment/executable fingerprints, closed manifests/associations and signed measured results.

## Ownership and gates

High-risk scientific/numerical/interface route: fresh native Sol/high blind A, fresh native blind B, restricted fresh native C and fresh native D. A owns tests/test_phase_carrier_scan.py and optional tests/phase_carrier_scan_fixture.py plus ignored public/oracle evidence. C owns only src/simrecon/_phase_carrier_scan.py, additive exports in src/simrecon/__init__.py and docs/usage/phase-carrier-scan.md plus ignored actual producers/evidence. Existing helpers may be reused unchanged. Reviewed tests/fixtures, unrelated runtime, dependencies/locks, gates/workflows/discovery/coverage, skills and delivery rules are outside C ownership. B/D report only. Coordinator owns contract/task/PROJECT/roadmap/comparison/presentation/lessons. Separately scoped bounded setup requires fresh independent acceptance of current-root changes before use.

Inherit binding100% Coverage.py native executable-line/branch-destination targets globally/perpackage/perownedfile for src/simrecon+scripts, never-imported/relevant subprocesses, zero exclusions, independently local/Ubuntu24.04/macOS15, no platform union. Installed advisory percentages grant no waiver. Cheap locked environment/platform/import/reader/build prerequisites precede dependent work. Exact clean canonical make verify/all13phases, complete rawSQLite/JSON/HTML, same-runM25 and wheel/source/staticversion/environment/executable/lock/check/base/input proof precede fresh D and the own stacked PR above PR41. Original closed native CI/platform qualification precedes final readback and exactly one actually started successor while authorized work remains. Human numeric limits are not set; retain all inherited/current attempts and unknown metering. No Superpowers, merge/release, earlier-PR edits, unrelated messages or owner-reference C execution/build.
