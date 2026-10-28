"""Blind A public fixtures/references for full-noisy-study v1.2.

PRE-AUTHORSHIP OBLIGATION LEDGER (written before tests)
====================================================
Authority: canonical full-noisy-study-v1.2 plus adopted schema clarification;
dependency contracts provide only their own public mathematics/record grammar.
Coverage: approved behavior + independent risk review; no percentage target.
No actual owner plan, truth, seed, runtime source or existing test was read.

Each line maps distinct decisions to a keeper family in test_full_noisy_study.
Equivalent scalar/key/path examples share a keeper; they add no new rule.

DS01 cli: generate/infer/evaluate in separate -m processes; all required flags;
 unknown/duplicate/missing/positional/all/overwrite/resume/cleanup/plugin errors;
 help. Keeper cli_grammar. Risk: silent defaults or expanded authority.
DS02 syntax: strict UTF8 single-object JSON; duplicate keys at each depth;
 unknown/missing keys, version, bool/count/real/null kinds, dimensions, finite
 normalization/overflow. Keepers plan_rejections, settings, protocol_rejections.
DS03 payload: exact fixed descriptor paths/order/keys; lowercase SHA/whole closed
 bytes/size; little f8/f4; C header; NPY1/2/3; one full nonobject array/no suffix;
 signed raw/predictions vs nonnegative source/means. Keeper binary_protocol.
DS04 ownership: existing empty dir/file/live/dangling link; missing parent;
 no merge/unlink/truncate/ancestor creation; every leaf exclusive; original
 bytes/type/link text/resolution/referents retained. Keepers output_ownership,
 partial_io. Limit: no malicious concurrency/atomicity/durability claim.
DS05 plan: eight-frame groups, positive shapes >=2 camera pixels, fixed bead
 spacing/size/nonoverlap/tangency/radius, empty specimen, positive unoccupied
 source range vs zero brightness, fixed refinements/optics; signed origins/
 phases/offset/carriers, zero beams, arbitrary seed integers/no cap, 82 unique
 seeds and exact dimensions. Keepers plan_rejections, generation, source_range.
DS06 generation: actual sources/means + per-exposure photon AND read noise;
 central-only zero-q/phase vs training/first-five heldout; heldout independent
 seeds; source row-order rounded weights; signal means exclude camera;
 stationary true origin transfer; mass/storage/zero-reference distinctions.
 Keepers generation, same_seed, source_reference, phase_cases.
DS07 seals: ordered exact21/public +22/private descriptors; original plan hash;
 normalized private plan, private/root identity; full validation, not existence;
 partial JSON/NPY retained; no automatic repair/retry. Keepers generation,
 protocol_rejections, partial_io. Chronological close/order needs D inspection
 beyond final-byte proof; controlled size-limit failure checks no false seal.
DS08 observation-only: standalone bundle works; parent/sibling names, invalid
 private decoys/plan/seed/means cannot affect inference; full preflight first.
 Keepers detached_inference, protocol_rejections, truth_order.
DS09 camera: actual 8-frame estimator; independent within-frame K-1 moments;
 exact source label/paired means and contrast; gain optional; range/nonpositive
 contrast seal, record retained/null correctly. Keepers pipeline, unavailable,
 camera_boundaries. No statistical accuracy threshold.
DS10 bead: complete real47 fit vs Powell; every supplied scale in order, 94S
 sign polls, all traces/candidates/counters/information/unprobed retained;
 Q256/Q512 and heldout after freeze; incomplete not promoted. Keeper pipeline,
 heldout_independence. Public record equality proves wiring, not fit accuracy.
DS11 phase: once-only estimated inputs, physical2*pi not rounded period,
 exact represented expression/range-safe products/endpoint; true transfer only
 in generator. Keepers pipeline, phase_cases; Decimal Machin pi reference.
DS12 specimen: all15 signed actual arrays; same estimated gauge and explicit
 transferred illumination; source geometry/spacing/unit basis; actual fit.
 Keeper pipeline. Live allocations/no second stack require D/resource proof.
DS13 serialization: exact recursive public schemas, tuples/lists/null, all
 attempts/calls/partial records and file refs; no volume archive; estimates
 before prediction and immutable on later failure. Keepers pipeline,
 unavailable, protocol_rejections. Late prediction-fault reachability remains
 a declared limit, not simulated numerical success/failure.
DS14 freeze: fresh cache/three actual orientation forwards on returned source;
 all15 finite signed predictions, ordered closed descriptors; exact public call
 counts; unavailable vs partial. Keeper pipeline. Sequential live lifetime is
 a D/resource obligation, not inferable from final files.
DS15 outcomes: 0 complete,2 domain,3 legitimate unavailable,4 protocol,
 5 I/O/ownership,6 generation range; ordinary information vs original range
 codes; no fake source/fallback/seal for interruption. Keepers all CLI families,
 source_range, partial_io. Unrelated dependency exceptions/MemoryError cannot
 be induced portably here without a forbidden decision-supplying seam.
DS16 evaluation: verify ALL public freeze/prediction/source before private
 open/stat; then full truth identities/geometry; new root only after validation;
 input/frozen bytes unchanged/no feedback. Keepers truth_order,
 evaluation_rejections, pipeline. FIFO detects attempted read, not every stat;
 D must inspect stronger before-any-stat obligation.
DS17 comparisons: evaluator-only gain/contrast, exact axial pairs, separate
 signal/corrected references, signed full residuals, six lexicographic bead
 permutations, TWO GLOBAL side-exchange gauges/no truth-selected output,
 normalized beams and physical wrapped/raw phase differences. Keeper metrics.
DS18 arithmetic: exact count and stable independent reductions; zero reference
 relative=null; per-field unavailable and complete unavailable assessment;
 no epsilon/clipping/threshold. Keepers metrics, extreme_evaluation,
 reference_controls. Complete inference fixtures only come from real CLI;
 altered evaluator-only truth is labeled protocol arithmetic input, not a new
 successful scientific acquisition or recovery proof.
DS19 provenance/preservation: runtime exact keys/nonblank versions or null,
 byteorder/hash grammar; same-version repeatability not cross-version RNG
 bits; caller input bytes, links, and public RNG/warning policies. Keepers
 generation, same_seed, reference_controls. Actual driver-source hash equality
 is reserved for D: A does not open runtime source even to hash it.
DS20 staging: legal small shapes remain accepted; complete noisy and distinct
 honest unavailable workflow; (32,256,256) campaign/resources/CI/full gate are
 coordinator work, not claimed here. Keeper pipeline/unavailable; all scientific
 conclusions conditional on finite models, no convergence/recovery guarantee.

Strongest proof: pipeline uses the real CLI plus accepted public dependencies.
File-only controls reach malformed representations/data-loss/arithmetic cases
that a valid physical run cannot select deterministically. They never supply a
fabricated successful fit. Every numeric accuracy assertion uses independently
specified algebra (Fraction/Decimal), not fitted output as truth. Composition
equalities use returned records ONLY as observations of the prescribed wiring.
No test-only runtime export, callback, optimizer replacement or stub is used.

FIXTURE/SCRATCH AND EXECUTION LEDGER
==================================
All data below are author-created PUBLIC fixtures, not the owner campaign.
Seeds are fixed before any product run; no realization selection/retry loop.
pytest tmp_path/tmp_path_factory own run directories; CLI receipts append to
COMMAND_LEDGER with absolute executable/argv/root/status/timeout, input/output
snapshot hashes. No cleanup is performed here; coordinator owns disposition.
Operational child guard300s, full focused harness1800s; guards are incomplete
evidence on timeout, not human limits. Human numeric limits: not set.
Model requested Sol/high; actual routing/tokens/cost unknown to this role.
Inherited attempts/charges stay in coordinator ledger; no reset implied.
Source binding70d8f36/treee239648, exact pins in activated packet. Environment
health passed with matching five material/harness hashes, Python3.13.12,
NumPy2.5.3/SciPy1.18.1/pytest9.1.1/Ruff0.16.9/Pyright1.1.414. Driver absent.
Reports and final owned-file hashes are returned outside tracked bytes.

AUTHORSHIP EVIDENCE / DISPOSITION (2026-10-26, not B acceptance)
-------------------------------------------------------------
This native role launches/delegates zero other roles. No Superpowers, runtime
source, old tests, existing lessons, raw receipts or actual owner truth read.
Only these two named test/fixture source files were authored. No Git mutation,
install, config/gate change, publication or cleanup was performed.

Narrow commands use .venv/bin/python scripts/source_free_check.py, with
PYTHONDONTWRITEBYTECODE=1, UV_NO_CACHE=1 and inherited root PYTHONPATH plus the
actual source-free sitecustomize/pytest plugin in nested CLI children.
Ruff check, Ruff format --check and Pyright --pythonpath .venv/bin/python on
only these two owned paths passed before the first full run. The final receipt
correction is followed by the same exact narrow checks; final statuses/hashes
are in the role response, outside candidate bytes.

Initial authoring diagnosed seven failed Ruff checks (format/import/line-length
issues in owned code) and one failed Pyright check (Decimal sum/power inferred
unions). These were corrected in owned files. No product defect was inferred.
Additional oracle refinements: use actual stored reduced phase for procedural
optics equality, independently bound its physical reduction separately; allow
ordinary finite ~2e7-turn reduction roundoff; do not demand a positive partial
write length that the I/O promise does not require. No B review/correction or
accepted checkpoint exists. Native turn/token/cost metering remains unknown.

Independent-focused runs, all via actual source-free harness:
  1) reference controls + dyadic public camera: 2 passed in0.03s;
  2) real small source/camera/bead/specimen composition: 1 passed in2.03s;
  3) complete AND honest initialization-unavailable scene qualification:
     2 passed in1.96s. Same predetermined seeds, no selected realization.
The full CLI workflow remains unproved because the selected driver is absent.

First full focused invocation: source_free_check.py --timeout1800 python -,
calling pytest.main on tests/test_full_noisy_study.py with --tb=line,
--no-showlocals, --assert=plain, -q and exclusive --basetemp under the root below.
Installed strict flags/policy plugin remained active; no discovery/gate change.
Observed296collected,4passed,173failed,119setup-errors,0skips/xfails; exit1;
elapsed6.15s.173ordinary subprocess calls returned1 with the explicit absent
module diagnostic. Two external-fault subprocesses closed but their early-exit
status was initially omitted from the receipt; that observer defect was fixed
by retaining final communicate status/stdout/stderr. No scientific CLI call ran.
The failures/errors are driver-unavailable evidence, NOT product-red or proof
that these unexecuted assertions pass. Final full rerun is required after the
receipt correction; its exact results are returned by the role response.

Retained positively identified exclusive PUBLIC fixture root from that run:
  <retained local scratch directory>
Descendant inventory:1302regular files,212directories,25symlinks;
13,096 native512-byte allocated blocks =6,705,152bytes, root itself excluded.
Inventory SHA25674e13a87541b77caede98cc86bd920de4d5fda3560c84290ebbfa2f2065a1b92.
All175owned CLI subprocesses closed. Inputs, original invalid/partial bytes,
symlink texts/referents and ignored checker caches are retained; none removed.
This role did not inspect other scratch. The final rerun has a separate new root:
  <retained local scratch directory>
Its only pytest target is the owned suite; pytest creates the new child 'pytest',
with no reuse/deletion of the first root. Final descendant inventory/process
status is returned in the role response for coordinator-owned cleanup routing.
No full per-call raw receipt file is written outside the two-path authority:
the own in-memory COMMAND_LEDGER retains argv/settings/input-output snapshot
hashes/status while a check runs; compact aggregate evidence is printed.
Original interpreter/venv/lock/source-free pins must remain at activated paths.

Oracle qualification: Machin's alternating atan series uses460decimal digits,
terms below1e-455; the discarded term bounds the series error.440digits for
phase expressions leave >120guard digits at finite float64 magnitudes. The
reduced-phase observer tolerance stays at512eps for huge-phase/endpoint cases;
the ~2e7-turn safe-product case allows128eps*2*pi*max(1,abs(turns)). These are
finite arithmetic controls, not a new whole-expression correct-rounding rule.
Fraction source membership is exact on normalized represented floats; two
half-cell sites exactly tangent to a radius1/4sphere qualify the closed tie.
1000digit metric reductions handle f64 squares/norm ratios independently, with
dyadic and extreme known answers including representable RMS/relative metrics
when unnormalized norms overflow. Camera controls use the contract's stated
moment bounds and exact K-1 dyadic examples. Public-operation equality is solely
wiring/serialization evidence; it proves no numerical accuracy or recovery.

Keeper lookup (test_ prefix omitted; parameter cases supply equivalent examples):
DS01 cli_help/cli_grammar/each_required_flag_duplicate_unknown_and_positionals;
DS02 plan_rejections_before_claim/plan_exact_keys_at_every_object/strict_plan_json/
     algorithm_settings_syntax/observation_protocol_rejections;
DS03 binary_protocol_ordinary_versions_and_noncanonical_json/
     binary_protocol_payload_validation/frozen_payload_domains_and_references;
DS04 output_ownership_preserves_every_existing_root/missing_output_parent_never_created/
     completion_leaf_created_exclusively_at_real_io_boundary;
DS05 empty_catalogue_and_large_integer_seed_are_legal/tangent_beads_and_minimal_camera_are_legal/
     positive_unoccupied_source_is_range_not_domain_or_fake_success;
DS06 generation_real_scientific_call_composition/
generation_protocol_and_independent_source_reference;
DS07 partial_io_retained_unsealed_and_retry_cannot_repair/observation_protocol_rejections;
DS08 detached_inference_ignores_private_decoys_and_path_names;
DS09 camera_boundaries_honest_records/existing_public_camera_control_with_independent_dyadic_oracle;
DS10 pipeline_complete47_paired_gauge_actual_specimen_and_freeze/
heldout_independence_preserves_every_training_decision;
DS11 phase_cases_physical_period_and_safe_complete_expression;
DS12 pipeline_complete47_paired_gauge_actual_specimen_and_freeze;
DS13 recursive_public_record_schema_rejection/real_bead_range_retains_actual_incomplete_record;
DS14 pipeline_complete47_paired_gauge_actual_specimen_and_freeze;
DS15 real_specimen_range_retains_bead_and_no_fabricated_source/
     camera_generation_range_is_unsealed_and_preserved;
DS16 evaluation_public_validation_before_private_read/every_completed_payload_verified_before_truth/
     evaluation_private_protocol_rejections;
DS17 metrics_independent_full_arrays_permutations_and_global_gauges;
DS18 extreme_evaluation_honest_arithmetic_not_new_physical_acquisition/
     signed_frozen_predictions_remain_valid_protocol_input/
reference_controls_exact_membership_metrics_and_physical_period;
DS19 same_seed_same_version_generation_retains_identical_payloads;
DS20 real_noisy_sealed_unavailable_is_not_completed/
public_small_scene_qualifies_dependency_composition.

B/D limits explicitly retained: driver absent prevents CLI pass/protocol/fault
proof; no claim of every dependency exception being reachable here. A stable
deterministic fit followed by identical prediction calls supplies no honest
portable selector for a late recognized prediction range; no injected fitter,
inverse, allocation or warning failure is substituted. Memory lifetime, close/
publication chronology, before-any-private-stat, complete unknown-exception
propagation and actual driver-source hash equality need independent D/resource
assessment beyond these final-file/real-caller observations. FIFO traps detect
private reads, not all stats. No full campaign, recovery, convergence, coverage
percentage, platform gate, cleanup completion or accepted checkpoint is claimed.

CORRECTION1 PRE-EDIT REQUIREMENT / DEPENDENCY MAP
----------------------------------------------
Authority: A1-correction1/correction-inputs.json and sanitized public-findings.md,
only the three named B1 public probes, unchanged original public contracts.
Prior checkpoint389288d31c6453c515d7745335c3a74213b82d364e66be89bc0d15f34413f726
is NOT_ACCEPTED. Its exact files and B1 snapshots stay immutable; these owned
working files are the authorized revision. B1's five findings are test/oracle
defects or concrete missing proofs; no runtime defect or new contract is inferred.

F1/DS14: forward prediction keeper must send plain native f64 carrier/phase
ndarrays, retaining tuple beam settings. Qualify this actual public call on a
real zero cache/source separately from the missing driver. Dependents: pipeline
prediction composition, both baseline/new-geometry workflow cases, new caller
qualification. No inverse boundary broadening or private helper follows.
F2/DS09,DS20: shared independent_camera_moments uses one global normalized A,
exact integer ceil-log2 K/max T for ell, Decimal frame/group mean/variance
bounds and returned-point uncertainty/contrast identities. Qualification accepts
the sanctioned5.000000000001 alternative and a small-frame perturbation allowed
only by global A, and rejects errors beyond those bounds. Preserve exact dyadic
reference values/K-1 distinction without demanding a tighter arithmetic bound;
retain a real constant-frame positive-contrast/unavailable-gain control.
Dependents: baseline/new workflow camera, original dyadic keeper, both original
small-scene qualifiers and new-geometry qualifier. Synthetic changed records
qualify the observer only; none supplies a production estimate or fit decision.
F3/DS05,DS06,DS12,DS17,DS18: preserve original plan/seeds/control keepers. Add a
declared public specimen detector(2,2,2), spacing(0.25,0.1,0.12)um, generator
source(4,4,4), inverse source(2,4,4), inverse spacing(0.25,0.05,0.06)um. Two
contained0.1um-radius sources at z0.115/0.38um with brightness700/1300e give
independently counted fine-plane occupancies8,4,4,8. Distinct represented plane
weights challenge doubling/repeating/omitting/swapping fine or coarse indices.
Keepers: extend four actual CLI scientific owner proofs to both scenes, qualify
new source/geometry and real public dependency composition, use exact-input
Decimal paired reference of shape(sourceZ/2,Y,X). Specimen spacings come from
declared geometry in generator/solver/prediction observers; calibration D stays
fixed. New case proves wiring/mass pairing, never recovery/convergence.
Shared dependents: source observer, generator optics, specimen geometry/forward,
camera-bound pairing observer, source MetricSummary and geometry fixtures.
F4/DS10,DS13,DS15,DS16: retain existing key corruption keepers; add exact-key
invalid inner coordinate/candidate/residual dimensions, nonnegative domains,
trace/score/call identities and counters, paired-camera/illumination identities,
source/detector geometry and completed top/nested status contradictions. Reseal
every changed payload descriptor; evaluator must reject before private FIFO read
and leave original/corrupt bundles intact. Values are negative protocol controls
cloned only from actual CLI completion, never fabricated successful fit records.
Keepers: inner_record_consistency_before_private_read plus original recursive
schema/truth-order keepers. Positive unprobed and unavailable-gain alternatives
remain legal. No obligation requires an old complete gradient to belong to the
latest best candidate or a prediction-stage unavailable freeze to undo fit facts.
F5/DS03,DS07,DS16: shared read_npy must check exact shape/dtype and declared
C header for ordinary v1/v2/v3, independent of coincidentally dual-contiguous
loaded strides. Qualify all three with explicit single-axis headers; real CLI
v3 positive/negative twins use a valid standalone bundle with detector(1,1,2).
Dependents: read_npy/check_descriptors, generation/private/freeze payload checks,
all binary families, new v3 CLI and observer qualification. The test's own byte
reader/writer is no required production backend. The allowed B1 probe is not a
new dependency of the committed tests.

All shared changes expand fresh B scope. Only fresh B decides retained evidence
applicability. No review verdict, usage/cost or human budget is invented. Prior
A1/B1/coordinator accounting stays retained; correction1 new checks/scratch and
final exact file identities are reported separately in the response/ledger.

CORRECTION1 QUALIFICATION / FINAL-CHECK POINTER
---------------------------------------------
The unchanged source-free, interpreter, dependency, lock and original file pins
matched the correction input before edits. The driver was absent by existence
check only. The three permitted B1 probes were read; the corrected reader now
rejects the original v3 Fortran-header payload without changing that artifact.
No runtime/history/Current state/coverage/lessons/private owner data was read.

Correction1 checks so far: Ruff format + scoped check --fix corrected two import
orders and returned0; the first Pyright check failed with37 inferred dictionary
union diagnostics in the synthetic camera observer control. Explicitly typing
that own qualification dictionary as dict[str,Any] corrected the diagnosed
typing defect; the next Pyright returned0 with0errors/warnings. No runtime/API
or numerical behavior was changed for that correction. Subsequent scoped Ruff
check and format --check both returned0. These are additional to, not replacements
for, the prior A1/B1 charges listed above and in the coordinator ledger.

Source-free focused qualification:20passed in5.12s, exit0. The original four
controls remain: exact reference, real dyadic camera, real complete original
scene, and real unavailable original scene. Sixteen added control examples cover
new-geometry actual composition, exact asymmetric pairing, real ndarray forward,
three in-bound/out-of-bound camera alternatives, v1/v2/v3 C-vs-Fortran header twins,
and real completed47-coordinate fitting with all coordinates honestly unprobed.
The latter uses the already-legal smallest-positive scale: every base-step
product underflows to zero; it still runs all94polls and required rescores.
This is not a new stopping/rank rule. The real no-physical-gain constant-frame
control preserves that positive-contrast alternative. Dyadic targets remain
exact independent values while output accuracy uses the explicit camera bounds.

Retained correction1 public control scratch:
  <retained local scratch directory>
Descendants:6regular files,7directories,1symlink;48native512-byte allocated
blocks=24,576bytes, root excluded. Inventory SHA256:
69d264a2fd68ef5789fa7f7821ab8a454ef673ba039955e764090a0bf5c2ad92.
The owned check processes have closed; no fixture/environment/cache was removed.
Old A1 scratch and B1 snapshots were not inspected, moved, deleted or rewritten.

The final full focused run uses a different exclusively created public root:
  <retained local scratch directory>
It invokes actual source_free_check.py --timeout1800 python -, then pytest.main
on only tests/test_full_noisy_study.py with --basetemp ROOT/pytest, -q, --tb=line,
--no-showlocals and --assert=plain. Installed strict flags/policy remain active.
Scoped Ruff check, format --check and Pyright are rerun on these exact two files
before that full check. Final results/file hashes, per-call receipt aggregate,
own scratch inventory and process closure are returned outside tracked bytes in
the role response. No full passing CLI checkpoint can be inferred while the
driver is absent. A timeout would be incomplete, not success or a human budget.

F3 review limits: original constant/zero extreme-source cases remain safe-range
and zero-reference keepers; they do not prove indexing. The new rational source
and two-scene CLI source-metric keeper supply that gap. Specimen outputs remain
relative integrated coefficients, with spacing from the plan, no volume factor
and no required recovery accuracy. F4's37exact-key mutations remain distinct
from the original missing/unknown-key family. Their evaluator truth-read traps
retain the earlier before-any-stat limitation. A new real unprobed CLI positive
case ensures these rejectors cannot justify a blanket unprobed-fit rejection.
All affected shared references, caller, observer, fixture and serializer/schema
dependencies above belong in expanded fresh B review. No checkpoint is accepted
by this author, and C must wait for that fresh verdict.

CORRECTION2 / F6 PRE-EDIT REQUIREMENT AND DEPENDENCY MAP
-----------------------------------------------------
Authority: only correction2's correction-inputs.json, public-findings.md,
public-beam-counterexample.json, prior-checkpoint.json and original allowed
public contracts/infrastructure/own files. Prior checkpoint:
3be8bf795f7c11c7bec2845750e1e65f1f2e9c88559c17695d94aa37ca6d6d12.
B2 confirmed F1-F5 corrected; its NOT_ACCEPTED verdict concerns F6 alone. The
diagnosis is a shallow finite-only extreme comparison, not new scientific
meaning, a product defect or a demonstrated model/reasoning limitation.

F6/DS17,DS18: extend the EXISTING huge_phases_and_beams evaluator branch. For
both as_stored/global_side_exchange, compare all three returned normalized beam
errors against independent exact-input Decimal normalization/differences. Read
the fitted amplitudes from the actual CLI-frozen bead candidate, true amplitudes
from the declared evaluator input; never use B2's sample fitted values as truth.
Exchange only the fitted side amplitudes for the second legitimate global
gauge. Retain its gauge labels/order, phase checks, actual workflow, frozen-byte
preservation, source physics, original seeds and all F1-F5 keepers unchanged.

New beam_error_reference/check_normalized_beam_errors are isolated to that
extreme keeper and synthetic observer qualifications. Existing dec/close_scalar
are reused UNCHANGED: normalized components lie in[0,1], differences in[-1,1],
so scale1 is the actual dimensionless comparison scale, never the raw1e308
amplitude. Normalization scales each positive finite nonnegative three-vector
by its largest component in Decimal, then divides by the Decimal Euclidean
norm;1000decimal digits comfortably resolve normalized float64 inputs, including
the selected huge balanced true vector. No raw float64 squared norm is formed.

Allowance:256*eps plus16minimum-subnormal units, about5.68e-14 dimensionless,
through unchanged close_scalar(scale=1). Each three-component normalization is
a short scaled sum of squares, square root and divisions followed by one
subtraction; normalized intermediates are bounded by3. The conservative256eps
allows ordinary binary64 evaluation/reduction roundoff and cancellation without
a recovery/statistical threshold. Decimal reference error is negligible beside
that finite arithmetic allowance. A raw-amplitude-scaled bound would be vacuous
and is explicitly not used. The finite wrong true-unit-zero result differs by
1/sqrt3 (~0.57735), over10^12times this allowance.

Qualify correct and nearby ordinary-roundoff values using independently
specified fitted(4,2,1)/sqrt21 and true(1,1,1)/sqrt3, plus its side exchange.
Reject a finite omitted-true-normalization error in EACH component of BOTH
gauges. These are observer-only inputs, never a supplied estimator/optimizer
result or a fabricated completed scientific workflow. No product seam, new API
or broad rewrite follows. The ordinary numerical beam keeper remains separate
and unchanged. Fresh B3 assesses the affected extreme keeper/new references and
retained complete scope; this author supplies no acceptance verdict.

Prior accounting remains retained, including initial A1/B1, correction1, B2's
F6 finding and B2's own boolean-versus1 probe-checker correction. This continuation
has no role launch/delegation and no default attempt/budget cap. Requested
Sol/high; actual routing/tokens/cost unknown. Human numeric limits are not set.
Correction2 commands, diagnostics, own public scratch and final candidate/check
identities are recorded separately below/in the response without rewriting any
prior immutable checkpoint/snapshot, logs or coordinator state.

CORRECTION2 QUALIFICATION / FINAL-CHECK POINTER
---------------------------------------------
Health matched prior two-file hashes and all bound interpreter/lock/source-free
pins; actual driver existence check was negative. Initial scoped Ruff --no-cache
check and Pyright both passed after formatting. The first new observer-only
qualification ran10cases:8passed,2failed in0.04s, exit1. Diagnosis: the nearby
roundoff controls used np.finfo().eps and produced np.float64 values; unchanged
close_scalar correctly requires plain JSON-like built-in numeric scalars. The
failure was its scalar-type assertion, not a beam error or allowance failure.
Converting those synthetic control values to built-in float corrected the test
input. No observer formula, tolerance, real result or production API was changed.
The second new qualification ran10cases:10passed in0.04s, exit0. Both actual
source-free pytest processes have closed. This additional check/input correction
is retained separately from all prior charges, including B2's checker correction.

Both new qualification runs used pytest -p no:cacheprovider with different new
basetemp children under the exclusive own public root:
  <retained local scratch directory>
These controls use no filesystem fixtures: the retained root is empty; its
descendant inventory is0entries/0allocated512-byte blocks, root itself excluded.
Empty inventory SHA2564f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945.
No older fixtures, caches, environments, snapshots or scratch were inspected or
deleted. This is own scratch accounting, not cleanup or resource feasibility.

Final scoped Ruff --no-cache check, format --check and Pyright target only these
two owned files. The full focused source-free check follows on these exact bytes:
source_free_check.py --timeout1800 python -, pytest.main on the owned suite with
--tb=line --no-showlocals --assert=plain -p no:cacheprovider and exclusive root:
  <retained local scratch directory>
It preserves strict installed policy flags and all original20 qualification
obligations plus10new F6 qualifications. Final status/counts, canonical checkpoint
hash (same declared identity recipe as prior-checkpoint.json), per-file hashes,
own full-run scratch/process closure are returned outside tracked bytes in the
role response. Missing driver evidence remains UNAVAILABLE, not product-red or
a completed real CLI evaluation. Fresh B3 must decide acceptance; C still waits.

CORRECTION3 / ADDITIONAL F6 REPRESENTATION EXAMPLE
-----------------------------------------------
Authority: correction3/correction-inputs.json, public-proof.json and
prior-checkpoint.json only, plus original allowed contracts/infrastructure/own
files. Prior authored checkpoint59e88eafee93ff815cfd60679deaebcacaad56f818e7ee2b8aa13e2fb7202cf2
is preserved and unaccepted; B3 has not launched. The public proof distinguishes
raw-square overflow from an unrepresentable raw Euclidean norm. Existing true
beams(1e308,1e308,1e308) have finite hypot; largest-finite positive components
instead have infinite unscaled float64 hypot although each input and every unit
component/error target is finite. This is the existing DS17/DS18 safe-complete
normalization obligation, not new science or a product/backend defect verdict.

Exact change/dependency map before edits:
* Existing extreme_evaluation_honest_arithmetic_not_new_physical_acquisition:
  retain huge_phases_and_beams and add maximum_finite_beams. Both mutate only
  declared evaluator-private public test inputs AFTER actual CLI-frozen fitting;
  both keep large-phase assertions, all3component/two-gauge numerical checks and
  frozen-byte preservation. All other acquisition/source/seed/record keepers stay.
* Existing observer acceptance and per-component finite-wrong rejection tests:
  retain their1e308 examples and parameterize maximum-finite component inputs.
  Correct units remain independent(4,2,1)/sqrt21 minus(1,1,1)/sqrt3, with side
  exchange of the fitted vector only. Added rejection examples evaluate the
  actual unscaled stdlib hypot-then-divide counterexample, which gives a finite
  wrong zero true unit vector only at the new boundary. Old rejection examples
  retain raw-square-overflow behavior. These are pure observer arithmetic, never
  returned estimator/fitter decisions or fabricated scientific CLI success.
* beam_error_reference/check_normalized_beam_errors, dec and close_scalar remain
  UNCHANGED. Their domain already includes the largest finite nonnegative input:
  len3, all finite/nonnegative and max>0. Decimal max scaling produces(1,1,1)
  before sum/sqrt; raw unscaled norm representability is not needed. All true
  unit components remain1/sqrt3; unchanged dimensionless256eps allowance applies.
  Qualification uses built-in floats, consistent with the actual JSON grammar.
No normalizer/backend algorithm is mandated on production. These existing
helpers/observers and the above expanded parameter cases are the affected B3
review scope; original F1-F5 and all30prior qualification obligations are retained.

Prior correction2 charge501.598807291s, its qualification type failures and all
A/B/coordinator charges remain retained, not reset or counted as zero. No role
launch/delegation, Superpowers, new approval interview, cleanup or other source
ownership follows. Requested Sol/high; actual routing/tokens/cost unknown. Human
limits are not set;300/1800/7200s guards are engineering limits, not owner budgets.
New commands/results/own scratch and exact final checkpoint are reported below
and outside tracked candidate bytes in the response; C awaits fresh B3 acceptance.

CORRECTION3 QUALIFICATION / FINAL-CHECK POINTER
---------------------------------------------
Cheap health matched the prior authored file hashes and bound interpreter,
dependency/lock/source-free pins. Driver existence was false; no source opened.
Initial scoped Ruff --no-cache and Pyright checks both passed, with no failed
checks or self-corrections in this continuation so far. Formatting was confined
to the owned test file. Source-free beam observer qualification:20passed in0.04s,
exit0, including all10earlier examples and10maximum-finite representation examples.
The actual stdlib wrong-normalization calculations remained pure arithmetic;
no fake fit/output supplied the expected scientific decision. Both gauges and
each corrupted component were independently challenged. The check process closed.

Exclusive retained own control scratch (no filesystem fixtures were needed):
  <retained local scratch directory>
Observed empty:0descendant entries/0allocated512-byte blocks, root excluded.
Empty inventory SHA2564f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945.
No earlier scratch/cache/environment/checkpoint/snapshot was inspected or removed.

Final scoped Ruff --no-cache check, format --check and Pyright use these two
owned files. Then the actual source-free full focused run uses pytest.main on
tests/test_full_noisy_study.py with -p no:cacheprovider --tb=line --no-showlocals
--assert=plain and a new exclusive --basetemp child below:
  <retained local scratch directory>
It retains installed strict policy flags, all30prior qualification obligations
and the10added representation examples. Final exact checkpoint/per-file hashes,
statuses/counts, own scratch/process closure and retained-input inventory are
returned outside tracked bytes in the response. No completed CLI workflow,
product-red, recovery accuracy, full verification or B3 acceptance is claimed.
Any missing-driver failures remain UNAVAILABLE. All prior charges/limits and
unchanged evidence applicability remain for the coordinator and fresh B3.

CORRECTION4 / F7 PRE-EDIT REQUIREMENT AND DEPENDENCY MAP
-----------------------------------------------------
Authority: correction4/correction-inputs.json, public-arithmetic.json and
prior-checkpoint.json only, plus original allowed contracts/interfaces/harness
and own files. No referenced B3 probe source, raw review or snapshot is read.
Prior exact checkpoint22dab42ae14cbc29cddd13a8add5ccad8c45e4b8e9c018e389a39bac070261f0
is unaccepted; fresh B3 accepted F1-F6 design and found F7 only. This is existing
DS17/DS18 safe reference construction/finite descriptive arithmetic, not new
meaning, scientific recovery accuracy, a product defect or a backend mandate.

Extend ONLY the existing real-CLI-frozen evaluator arithmetic keeper with
finite_mean_product_overflow. Its public original true gain2counts/e and declared
private optical means1e308e make the optional gain*mean product overflow float64.
Use the ACTUAL frozen camera contrast/blank, not the sample values from B3, in
independent complete Decimal signal and corrected-mean expressions. Both finite
reference arrays and their seven MetricSummary fields (count plus six real
statistics) must remain available. Change only the15declared evaluator-private
mean payload values, close/reseal their descriptors; preserve plan, observations,
source, seeds, phase/gauge keepers and every frozen inference byte. Explicitly
label these mutated private payloads as protocol arithmetic, not physical truth.

New finite_mean_prediction_references is isolated to this F7 case and pure
observer qualifications: compute g*mu/d and(o+g*(mu+background)-blank)/d in
1000digit Decimal from represented inputs, then round each finite final value
to native float64. Domain: finite nonnegative private means, positive true gain
and estimated contrast, nonnegative background, finite signed offsets/blank;
this selected control additionally checks that the complete targets are finite.
No raw float64 product/square is needed. New check_available_metric wraps the
UNCHANGED independently qualified metric_reference/check_metric/close_scalar:
check exact count, all six values and empty local unavailable declarations for
this known-finite case. Other metric keepers retain legitimate null outcomes.
The two F7 report fields must also have no unavailable_comparisons declaration.
Existing256eps input/result-scale allowance applies; here its physical scale is
~1e305relative units, norm~1e306relative units, with relative_l2 on scale1. It
rejects false zero/reference-null/range outcomes by a wide margin and introduces
no recovery or statistical threshold. Ordinary binary64 reference rounding is
included; the Decimal intermediate and reduction precision error is negligible.

Qualification is pure arithmetic/observer input, never a fabricated successful
fit or CLI result: choose private mean1e308e, true gain2counts/e, contrast1024
counts/relative unit and finite signed blank/offset. Independent signal target
is mean/512; the O(1) affine difference rounds away in the corrected target on
this huge scale. For60zero prediction elements the exact finite targets are
reference_l2=error_l2=reference*sqrt60, relative_l2=1, RMS=max_abs=reference,
mean=-reference, count60. Qualify both signal/corrected summaries, rejecting
null summaries, false unrepresentable declarations and finite zero metrics.
CLI exit0 rejects erroneous range termination; no mock supplies a CLI decision.

Affected fresh B4 scope: this new parameter of the existing arithmetic keeper,
the two new reference/availability helpers and their qualifications. Unchanged
shared metric helpers still serve original source/prediction/zero/unrepresentable
keepers; those obligations and all40prior qualification examples remain intact.
No ordinary workflow/reference/helper rewrite or other source ownership follows.
All prior A/B/root charges, B3's expected unavailable check and checkpoints remain
retained. Requested Sol/high; actual routing/tokens/cost unknown; human limits
not set. Native role launches/delegation0. Engineering guards are not budgets.
Final exact hashes/checkpoint/checks/own scratch/process closure follow below
and in the response; C waits for a fresh independent B4 acceptance verdict.

CORRECTION4 QUALIFICATION / FINAL-CHECK POINTER
---------------------------------------------
Cheap health matched prior owned file hashes and the bound interpreter,
dependency/lock/source-free pins; driver existence remained false. No runtime
source opened. Initial scoped Ruff --no-cache and Pyright both passed after
formatting the two owned files. New source-free pure reference/observer
qualification:8passed in0.05s, exit0. It independently checks both complete
references and all seven finite MetricSummary fields, including exact count,
and rejects null, false unrepresentable and finite-zero summaries. No failed
checks or test-defect self-corrections in this continuation so far. The actual
qualification process closed and produced no filesystem fixture payload.

Retained exclusive own public control root:
  <retained local scratch directory>
Observed empty:0descendant entries/0allocated512-byte blocks, root itself excluded.
Empty inventory SHA2564f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945.
No earlier scratch, caches, environments, snapshots or original evidence were
inspected or removed. This inventory supplies no full-study resource claim.

Final scoped Ruff --no-cache check, format --check and Pyright use these exact
two files. The source-free full focused check then uses pytest.main on only
tests/test_full_noisy_study.py, -p no:cacheprovider --tb=line --no-showlocals
--assert=plain and a new exclusive --basetemp child in:
  <retained local scratch directory>
All installed strict policy flags and40prior passing qualification obligations
remain. The8new F7 qualifications extend that scope; final status/counters,
canonical checkpoint/per-file hashes, own scratch/process closure and inventories
are returned outside candidate bytes in the response. Known absent-driver
failures remain UNAVAILABLE, not product-red or evidence of a completed CLI.
Prior A/B/root/review/correction charges remain retained; no accepted checkpoint
or fresh B4 verdict is supplied by this author. Existing scientific/persistence/
memory/order/private-stat proof limits are unchanged.
Correction5 H1: child diagnostics under ordinary parent environments
-----------------------------------------------------------------
Authorized input: correction5 packet/public-findings/prior-checkpoint/allowlist;
no raw gate evidence, runtime source or other-role history was read. Root's
supplied publication fixture hash741e396a2f017a1ce698c04d75bb86019e0b51cda47c9daf
83475bdc9a76ec49 and unchanged test hashfea6923508e9212c01a6a4cd1f839002b997bdaea
11d61c2286f755953608419 matched before correction. Existing module-docstring
redactions remain. Historical B4 acceptance of7aff3198d62f062a254c0dd4ddc0b662731
e1b5f5ac56c167201ebb06c74a431 is preserved, not applied to these new bytes.

Classification and pre-edit diagnosis: test-harness defect, no product-red.
The approved actual wrapper installed hooks before pytest import; inside that
safe process the probe removed PYTHONPATH and PYTEST_PLUGINS, retained the
already importable diagnostic pytest_plugin via explicit -p, then ran the four
existing cli_help keepers. Exit1:4failed/382deselected, each at the parent's
Run-via-source_free_check.py assertion, before CLI launch. Interpreter3.13.12,
own .venv and initial owned-file identities passed cheap health first.

Requirement/keeper/dependency map, before final verification:
* H1 requires approved source-free hooks in every real CLI child before startup,
  including ordinary canonical/CI parents, preserving inherited instrumentation.
  source_free_environment copies all inherited keys and adds only the existing
  approved site path and pytest_plugin entries when absent; no global parent
  mutation, instrumentation override, gate/discovery/coverage change or new hook.
* Shared cli now uses that environment. Every cli caller (generation/inference/
  evaluation/help/grammar/protocol/domain/ownership/failure/scientific/F1-F7
  keepers and module pipeline fixtures) is an affected harness dependent. The
  separate exclusive completion-leaf Popen path uses the same helper; both
  regular-file and symlink cases retain all real-I/O fault assertions and process
  closure. Only the two parent guards are replaced by child setup, not removed
  without protection. Existing stdout/stderr/status observers remain unchanged.
* Four new pure harness qualifications cover ordinary/already-source-free parents
  crossed with direct/nested children. They verify all other inherited keys
  exactly, retained path/plugin entries, unchanged parent, actual hook identities,
  warning category/message/file/line, both exception categories/messages/locations,
  direct cause and nonzero status, with own-file source lines absent. Real CLI
  help plus all existing shared-cli/exclusive-I/O dependents supply owner-boundary
  proof. No production seam, scientific threshold or fabricated fitter result.
* No scientific/schema/numerical/fixture seed/plan/metric/phase/gauge/frozen-byte
  oracle/helper changed. F1 ndarray, F2 global camera allowance, F3 asymmetric
  axial composition, F4 record relationships, F5 declared NPY order, F6 safe beam
  normalization and F7 finite complete-reference arithmetic keepers are retained.
  Their48 prior independent controls plus all existing386 cases remain; four
  harness controls extend collection. Fresh B5 decides retained applicability
  and expanded review, not this author. No full canonical gate or campaign run.

Self-corrections/accounting: one apply_patch attempted a nonexistent cli_help
context and failed before any edit; the following patch used the actual owned
context. An8pass diagnostic/help qualification overlapped Ruff formatting;
it is explicitly uncredited as exact-candidate evidence and will be rerun after
edits cease. No scientific correction followed. Both facts remain charged.
All prior A1/corrections1-4/B1-B4/C1/gate/diagnosis costs, failures and immutable
checkpoints remain retained. Human numeric limits not set;300/1800/7200seconds
are engineering guards. Requested Sol/high; deployment/metering/cost unknown.

Final-check pointer (prepared before exact-byte verification): actual wrapper,
PYTHONDONTWRITEBYTECODE=1/UV_NO_CACHE=1, narrow Ruff check --no-cache and format
--check plus Pyright only on the two owned files. Full owned-suite pytest.main
runs under both inherited source-free and simulated ordinary parent entries;
ordinary removes only PYTHONPATH/PYTEST_PLUGINS after hooks load, explicitly
retaining -p pytest_plugin. Both use own exclusive basetemp, -p no:cacheprovider,
--assert=plain --tb=line --no-showlocals and all installed gates. No environment
or runtime source is printed. Final commands/counts/status, diagnostic evidence,
file hashes/sizes/canonical identity algorithm, new scratch inventories/reference
pins and owned-process closure are returned outside tracked bytes. The canonical
identity uses the supplied current_candidate_head/tree as this correction's
baseline, original contract/schema/lock/source-free pins, and exact owned bytes;
these Git identities are packet inputs, not independently inspected Git state.
No cleanup, installs, Git actions, runtime edits, delegation or Superpowers.

Correction6 H2: real partial-I/O with authentic subprocess measurement
-------------------------------------------------------------------
Same authorized blind A continuation. Exact activation/allowlist/public H2 proof
were read first; only explicitly allowed live A/common guidance, original public
contract, own tests and pinned diagnostics were consulted. No product source,
coverage maps/DB semantics, raw root gate output or other-role history was read.
Starting accepted B6 checkpoint0fe9133db1c79e8879f799b3a2328ece6cd38c28435533075
c3c72ee445ff719 and all prior checkpoints/charges remain historical scoped
evidence, not acceptance of these revised bytes. New baseline head/tree are the
supplied9fe16e5f00591d5f0556a584fc6b9bcc2e73c5f9 and
0136a96c5fafef226f3c4d34a5c959670f857081; no Git access was used.

Diagnosis: H2 is a test-harness resource-limit/instrumentation interaction, not
scientific product-red. Cheap safe health verified starting test/fixture and
actual harness/policy hashes, lock/config byte hashes, Python3.13.12/macOS arm64
and installed coverage7.16.2. The suggested evidence parent already existed:
one exclusive mkdir attempt failed FileExistsError before writing; its existing
contents were never inspected. A fresh exclusive author child namespace was
created instead; this failed check stays charged. In that namespace an actual
coverage run with branch=True, source=[src/simrecon,scripts], patch=[subprocess]
and parallel=True ran the unchanged actual worktree partial-I/O test. It passed
once in1.61s, but authentic native files were122880,128,167936bytes. Native
combine --keep in a separate -W error process failed1 with CoverageWarning,
DataError and SQLite DatabaseError malformed-data diagnostics. All input bytes
were retained unchanged. The producer's already-imported diagnostic-hook warning
was observed, not globally suppressed or promoted with scientific warnings.
This independently reproduced the supplied sanitized H2 mechanism, no fake DB.

Pre-final requirement/keeper/dependency/preservation map:
* Contract v1.2 persistence and exit5: a real OS file-size write failure must
  retain actual partial output, absent generation/observation/private completion
  leaves, unchanged input bytes, and an exit5 retry that leaves existing partial
  bytes and entries unchanged. The same existing keeper
  test_partial_io_retained_unsealed_and_retry_cannot_repair retains every such
  assertion, SIGXFSZ ignored and a child preexec real RLIMIT_FSIZE soft/hard cap.
* Replace only that keeper's public example: calibration grid[1,2,24] becomes
  [1,2,256], leaving spacings, camera, three contained/nonoverlapping bead rows,
  specimen and all82 public seeds unchanged. Source refinement(8,8,8) gives a
  float64 raw source payload8*16*2048*8=2097152bytes before its NPY header. The
  local file cap1048576bytes therefore forces an incomplete real source write.
  The larger legal box preserves sphere containment and source membership. Its
  local scale is an I/O example, not a science/coverage threshold or owner budget.
  The keeper also checks a nonempty actual bead_source_e.npy whose size is at
  most the cap and strictly below its required raw payload. It does not accept
  fake failure, absent partial output or a sealed/repaired retry. It imposes no
  exact number of successfully written bytes or optional diagnostic prose.
* No shared helper, observer, numerical reference, seed fixture, schema, CLI
  environment, tolerance, scientific/API rule or runtime seam changes. All other
  keepers including F1-F7 and both exclusive completion-leaf cases are retained.
  This fixture change is explanatory module-docstring accounting only. Expanded
  review scope is the changed keeper/example, real resource/caller/persistence
  behavior and native producer/combine integrity; fresh B decides applicability.
* Coverage subprocess patch remains genuine and enabled for the actual CLI child
  and retry. Validation uses an artifact-local config with the supplied source
  scope/branch/patch settings, an exclusive native directory and a separate output
  directory. No canonical output slot, installed config/gate/exclusion or global
  warning policy changes. Public native combine --keep with warnings-as-errors
  only in its process is the validity oracle; opaque size/hash manifests retain
  inputs/output. No SQLite/header surrogate, coverage report/map/line/arc query,
  excluded producer or interpretation of implementation measurement is used.

Final-check pointer prepared before exact-byte checks: retain unchanged before
inputs and perform real instrumented changed-keeper producer/combine, ordinary
focused H2/sibling I/O keepers and the owned390-case focused suite, all after edits
stop. Use actual source_free_check.py, own .venv, exclusive namespaces/basetemps,
PYTHONDONTWRITEBYTECODE=1, UV_NO_CACHE=1, -p no:cacheprovider, --assert=plain,
--tb=line and --no-showlocals. Only combine gets -W error. Narrow Ruff check and
format --check use --no-cache; Pyright gets --pythonpath .venv/bin/python. Final
actual commands/results, sizes/hashes/canonical identity, public evidence and
scratch/reference/process closure are retained in the new exclusive author
evidence namespace and returned outside tracked bytes. No final gate/campaign,
publication, cleanup or review role is run by A. All prior failures/attempts/costs
remain; no reset or blanket inherited acceptance. Human limits not set;
engineering guards are not budgets. Requested Sol/high; actual deployment,
effort/tokens/cost unknown. Root owns final gate5, Current state and cleanup;
fresh independent B must accept the revised checkpoint.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import subprocess
import sys
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COMMAND_LEDGER: list[dict[str, Any]] = []
D = (0.125, 0.080, 0.080)
NOMINAL = [
    0.0,
    2 * math.pi / 5,
    4 * math.pi / 5,
    6 * math.pi / 5,
    8 * math.pi / 5,
    math.pi / 5,
    3 * math.pi / 5,
    7 * math.pi / 5,
    9 * math.pi / 5,
]
RAW_NAMES = [f"specimen_o{o}_p{p}.npy" for o in range(3) for p in range(5)]
PRED_NAMES = [f"prediction_o{o}_p{p}.npy" for o in range(3) for p in range(5)]
OBS_NAMES = [
    "camera_dark.npy",
    "camera_blank.npy",
    "camera_flat.npy",
    "calibration_central.npy",
    "calibration_training.npy",
    "calibration_heldout.npy",
    *RAW_NAMES,
]
PRIVATE_NAMES = [
    "plan.json",
    "generation_summary.json",
    "bead_source_e.npy",
    "specimen_source_e.npy",
    "calibration_central_expected_signal_e.npy",
    "calibration_training_expected_signal_e.npy",
    "calibration_heldout_expected_signal_e.npy",
    *[n.replace(".npy", "_expected_signal_e.npy") for n in RAW_NAMES],
]
LIMITATIONS = [
    "conditional_clear_pupil_model",
    "finite_source_and_pixel_quadrature",
    "paired_axial_mass_aggregation",
    "finite_search_not_convergence",
    "possible_unprobed_or_ambiguous_parameters",
    "estimated_camera_gauge",
    "training_residual_not_heldout_validation",
    "no_recovery_accuracy_threshold",
    "procedural_truth_boundary_only",
]
COMPARISONS = [
    "camera_comparison",
    "source_metrics",
    "signal_prediction_metrics",
    "corrected_mean_prediction_metrics",
    "observed_residual_mean",
    "observed_residual_rms",
    "bead_permutation_comparisons",
    "illumination_gauge_comparisons",
]
SETTINGS = {
    "sweep_scales": [1.0, 0.5],
    "regularization": 0.1,
    "max_iterations": 1,
    "max_backtracking_trials": 2,
    "pupil_order": 2,
}


def plan(*, unavailable: bool = False, empty: bool = False) -> dict[str, Any]:
    """Predetermined contained public scene; no product-derived values."""
    seeds = iter(range(10000, 10082))
    return {
        "format_version": "full_noisy_study_plan_v1",
        "geometry": {
            "camera_shape_yx": [8, 8],
            "calibration_shape_zyx": [1, 2, 24],
            "calibration_spacing_um_zyx": list(D),
            "calibration_origin_um_zyx": [0.0, 0.125, -0.25],
            "specimen_shape_zyx": [1, 2, 2],
            "specimen_spacing_um_zyx": list(D),
            "specimen_origin_um_zyx": [0.5, 1.25, -1.125],
        },
        "camera": {
            "background_e": 0.0 if unavailable else 0.1,
            "read_noise_e": float.fromhex("0x0.0000000000001p-1022") if unavailable else 0.25,
            "gain_counts_per_e": 1.0 if unavailable else 2.0,
            "offset_counts": 0.0 if unavailable else -7.0,
            "flat_signal_e": 500.0,
        },
        "illumination": {
            "carriers_yx_per_um": [[0.3, -0.2], [-0.4, 0.6], [0.7, 0.1]],
            "phases_at_calibration_origin_rad": [
                [v + 0.1 * o + 0.03 * p for p, v in enumerate(NOMINAL)] for o in range(3)
            ],
            "beam_amplitudes": [1.0, 0.6, 0.3],
        },
        "bead_catalogue": [
            [0.0625, 0.08, x, 0.050, 0.0 if unavailable else b]
            for x, b in zip((0.16, 0.88, 1.6), (12000.0, 9000.0, 15000.0), strict=True)
        ],
        "specimen_catalogue": [] if empty or unavailable else [[0.0625, 0.08, 0.08, 0.05, 1000.0]],
        "generator_pupil_order": 2,
        "seeds": {
            **{
                k: [next(seeds) for _ in range(8)]
                for k in ("camera_dark", "camera_blank", "camera_flat")
            },
            "calibration_central": next(seeds),
            "calibration_training": [[next(seeds) for _ in range(9)] for _ in range(3)],
            "calibration_heldout": [[next(seeds) for _ in range(5)] for _ in range(3)],
            "specimen": [[next(seeds) for _ in range(5)] for _ in range(3)],
        },
    }


def multi_axial_plan() -> dict[str, Any]:
    """Declare asymmetric fine pairs and a specimen spacing distinct from beads."""
    value = plan()
    value["geometry"]["specimen_shape_zyx"] = [2, 2, 2]
    value["geometry"]["specimen_spacing_um_zyx"] = [0.25, 0.1, 0.12]
    value["specimen_catalogue"] = [
        [0.115, 0.1, 0.12, 0.1, 700.0],
        [0.38, 0.1, 0.12, 0.1, 1300.0],
    ]
    return value


def encoded(value: Any) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(encoded(value))


def load_json(path: Path, *, canonical: bool = False) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            assert key not in result, (path.name, "duplicate key", key)
            result[key] = value
        return result

    def bad_constant(value: str) -> Any:
        raise AssertionError((path.name, "nonfinite JSON", value))

    data = path.read_bytes()
    result = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad_constant)
    assert type(result) is dict
    finite_json(result)
    if canonical:
        assert data == encoded(result)
    return result


def finite_json(value: Any) -> None:
    if isinstance(value, float):
        assert math.isfinite(value)
    elif isinstance(value, list):
        for item in value:
            finite_json(item)
    elif isinstance(value, dict):
        for item in value.values():
            finite_json(item)


def keys(value: dict[str, Any], names: str) -> None:
    assert set(value) == set(names.split()), (set(value), names)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def descriptor(root: Path, name: str) -> dict[str, Any]:
    path = root / name
    result: dict[str, Any] = {"path": name, "size_bytes": path.stat().st_size, "sha256": sha(path)}
    if name.endswith(".npy"):
        with path.open("rb") as stream:
            array = np.load(stream, allow_pickle=False)
            assert stream.read() == b""
        result.update(dtype=array.dtype.str, shape=list(array.shape))
    return result


def save_npy(path: Path, array: Any, *, version: tuple[int, int] | None = None) -> None:
    with path.open("xb") as stream:
        np.lib.format.write_array(stream, np.asarray(array), version=version, allow_pickle=False)


def read_npy(root: Path, item: dict[str, Any]) -> Any:
    keys(item, "path dtype shape size_bytes sha256")
    path = root / item["path"]
    assert item == descriptor(root, item["path"])
    with path.open("rb") as stream:
        magic = np.lib.format.read_magic(stream)
        assert magic in ((1, 0), (2, 0), (3, 0))
        size_width = 2 if magic == (1, 0) else 4
        size_bytes = stream.read(size_width)
        assert len(size_bytes) == size_width
        size = int.from_bytes(size_bytes, "little")
        header_bytes = stream.read(size)
        assert len(header_bytes) == size
        header = ast.literal_eval(header_bytes.decode("utf-8" if magic == (3, 0) else "latin1"))
        keys(header, "descr fortran_order shape")
        assert header["descr"] == item["dtype"]
        assert type(header["shape"]) is tuple and list(header["shape"]) == item["shape"]
        assert all(type(n) is int for n in header["shape"])
        assert header["fortran_order"] is False
        stream.seek(0)
        array = np.load(stream, allow_pickle=False)
        assert stream.read() == b""
    assert np.all(np.isfinite(array)) and array.flags.c_contiguous
    return array


def save_declared_order_npy(
    path: Path, array: Any, version: tuple[int, int], *, fortran: bool
) -> None:
    """Write explicit ordinary test headers, including a dual-contiguous trap."""
    assert version in ((1, 0), (2, 0), (3, 0))
    values = np.asarray(array)
    width = 2 if version == (1, 0) else 4
    header = repr({"descr": values.dtype.str, "fortran_order": fortran, "shape": values.shape})
    raw = header.encode("utf-8" if version == (3, 0) else "latin1")
    raw += b" " * ((-(8 + width + len(raw) + 1)) % 64) + b"\n"
    with path.open("xb") as stream:
        stream.write(b"\x93NUMPY" + bytes(version))
        stream.write(len(raw).to_bytes(width, "little"))
        stream.write(raw)
        stream.write(values.tobytes(order="F" if fortran else "C"))


def snapshot(root: Path) -> dict[str, Any]:
    """Own fixture contents only; preserve link text and referent identity."""
    result: dict[str, Any] = {}
    if not root.exists() and not root.is_symlink():
        return result

    def visit(path: Path, label: str) -> None:
        mode = path.lstat().st_mode
        if path.is_symlink():
            target = path.resolve(strict=False)
            result[label] = (
                "link",
                mode,
                os.readlink(path),
                str(target),
                sha(target) if target.is_file() else None,
                target.exists(),
            )
        elif path.is_dir():
            result[label] = ("dir", mode)
            for child in sorted(path.iterdir()):
                visit(child, f"{label}/{child.name}")
        elif path.is_file():
            result[label] = ("file", mode, path.stat().st_size, sha(path))
        else:
            result[label] = ("special", mode)

    visit(root, ".")
    return result


def source_free_environment() -> dict[str, str]:
    """Establish approved child diagnostics without requiring a special parent."""
    env = os.environ.copy()
    site = str(ROOT / "scripts/source_free_sitecustomize")
    previous = env.get("PYTHONPATH", "")
    if site not in previous.split(os.pathsep):
        env["PYTHONPATH"] = site + (os.pathsep + previous if previous else "")
    plugins = env.get("PYTEST_PLUGINS", "")
    if "pytest_plugin" not in plugins.split(","):
        env["PYTEST_PLUGINS"] = "pytest_plugin" + ("," + plugins if plugins else "")
    return env


def cli(
    *args: str, timeout: float = 300, preexec_fn: Any = None
) -> subprocess.CompletedProcess[str]:
    """Real module subprocess with the actual source-free hooks before startup."""
    env = source_free_environment()
    argv = [sys.executable, "-m", "scripts.full_noisy_study", *args]
    receipt: dict[str, Any] = {
        "argv": argv,
        "cwd": str(ROOT),
        "timeout_s": timeout,
        "PYTHONPATH": env["PYTHONPATH"],
        "status": "entered",
    }
    # All absolute argv inputs here are the author's positively identified
    # public fixture paths. Relative syntax-error placeholders are never read.
    identities = {}
    for index, flag in enumerate(args[:-1]):
        if flag in ("--plan", "--observations", "--inference", "--private-truth"):
            path = Path(args[index + 1])
            if path.is_absolute():
                contents = snapshot(path)
                identities[str(path)] = {
                    "entries": len(contents),
                    "snapshot_sha256": hashlib.sha256(encoded(contents)).hexdigest(),
                }
    receipt["input_identities"] = identities
    COMMAND_LEDGER.append(receipt)
    try:
        result = subprocess.run(
            argv,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            preexec_fn=preexec_fn,
        )
    except subprocess.TimeoutExpired:
        receipt["status"] = "timeout_incomplete"
        raise
    receipt.update(status=result.returncode, stdout=result.stdout, stderr=result.stderr)
    if "--out" in args:
        output = Path(args[args.index("--out") + 1])
        if output.is_absolute():
            contents = snapshot(output)
            receipt["output"] = {
                "path": str(output),
                "entries": len(contents),
                "snapshot_sha256": hashlib.sha256(encoded(contents)).hexdigest(),
            }
    receipt["process_closed"] = True
    return result


def expect(result: subprocess.CompletedProcess[str], code: int) -> None:
    assert result.returncode == code, (result.returncode, result.stdout, result.stderr)


def infer_args(observations: Path, out: Path, settings: dict[str, Any] | None = None) -> list[str]:
    settings = SETTINGS if settings is None else settings
    return [
        "infer",
        "--observations",
        str(observations),
        "--out",
        str(out),
        "--sweep-scales",
        json.dumps(settings["sweep_scales"]),
        "--regularization",
        str(settings["regularization"]),
        "--max-iterations",
        str(settings["max_iterations"]),
        "--max-backtracking-trials",
        str(settings["max_backtracking_trials"]),
        "--pupil-order",
        str(settings["pupil_order"]),
    ]


def evaluate_args(observations: Path, inference: Path, truth: Path, out: Path) -> list[str]:
    return [
        "evaluate",
        "--observations",
        str(observations),
        "--inference",
        str(inference),
        "--private-truth",
        str(truth),
        "--out",
        str(out),
    ]


def acquisition() -> dict[str, Any]:
    return {
        "camera_law": "scalar_poisson_gaussian",
        "shot_noise": True,
        "stationary_camera": True,
        "common_dose": True,
        "known_registration": True,
        "pupil": "clear_scalar_matched_index",
        "excitation_um": 0.488,
        "emission_um": 0.525,
        "refractive_index": 1.515,
        "detection_na": 1.4,
        "pixel_subsamples_yx": [2, 2],
    }


def observation_bundle(
    root: Path, *, camera_case: str = "zero", version: tuple[int, int] = (1, 0)
) -> Path:
    """Create controlled protocol input, never a fabricated completed fit.

    Constant groups make normalization honestly unavailable; 'range' has
    required variance beyond f64. 'gain_missing' permits positive contrast but
    no physical gain, then actual all-zero central images fail initialization.
    """
    root.mkdir()
    geometry = plan()["geometry"]
    for name in OBS_NAMES:
        if name.startswith("camera_"):
            values = np.zeros((8, 8, 8), dtype="<f8")
            if camera_case == "negative" and name == "camera_flat.npy":
                values.fill(-1)
            if camera_case == "gain_missing" and name == "camera_flat.npy":
                values.fill(1)
            if camera_case == "range":
                values[..., ::2] = 1e308
                values[..., 1::2] = -1e308
        else:
            spatial = tuple(
                geometry["calibration_shape_zyx"]
                if name.startswith("calibration")
                else geometry["specimen_shape_zyx"]
            )
            prefix = (3, 9) if "training" in name else (3, 5) if "heldout" in name else ()
            values = np.zeros((*prefix, *spatial), dtype="<f8")
        save_npy(root / name, values, version=version)
    manifest = {
        "format_version": "full_noisy_study_observations_v1",
        "geometry": geometry,
        "acquisition_model": acquisition(),
        "nominal_phase_commands_rad": NOMINAL,
        "files": [descriptor(root, name) for name in OBS_NAMES],
    }
    write_json(root / "complete.json", manifest)
    return root


def reseal(root: Path, filename: str = "complete.json") -> None:
    manifest = load_json(root / filename)
    manifest["files"] = [descriptor(root, item["path"]) for item in manifest["files"]]
    write_json(root / filename, manifest)


@lru_cache(maxsize=1)
def physical_pi() -> Decimal:
    """Machin identity, >430 reliable decimal places; no rounded f64 period."""
    with localcontext() as ctx:
        ctx.prec = 460

        def atan_inverse(n: int) -> Decimal:
            x = Decimal(1) / n
            power, total, k = x, x, 1
            while True:
                power *= -(x * x)
                term = power / (2 * k + 1)
                total += term
                if abs(term) < Decimal("1e-455"):
                    return total
                k += 1

        return +(16 * atan_inverse(5) - 4 * atan_inverse(239))


def dec(value: Any) -> Decimal:
    return Decimal.from_float(float(value))


def wrap_reference(
    phase: float,
    carrier: Any = (0.0, 0.0),
    origin: Any = (0.0, 0.0, 0.0),
    destination: Any = (0.0, 0.0, 0.0),
) -> float:
    with localcontext() as ctx:
        ctx.prec = 440
        pi = physical_pi()
        displacement = sum(
            (dec(carrier[j]) * (dec(destination[j + 1]) - dec(origin[j + 1])) for j in range(2)),
            Decimal(0),
        )
        expression = dec(phase) + 2 * pi * displacement
        period = 2 * pi
        turns = ((expression + pi) / period).to_integral_value(rounding="ROUND_FLOOR")
        answer = float(expression - turns * period)
    return -math.pi if answer >= math.pi else answer


def transferred(phases: Any, carriers: Any, origin: Any, destination: Any) -> Any:
    return np.asarray(
        [
            [wrap_reference(phases[o][p], carriers[o], origin, destination) for p in range(5)]
            for o in range(3)
        ]
    )


def exact_source(catalogue: Any, shape: Any, spacing: Any, refinement: Any) -> Any:
    """Tiny exact-rational midpoint membership + prescribed per-row RN64."""
    result = np.zeros(
        tuple(n * f for n, f in zip(shape, refinement, strict=True)), dtype=np.float64
    )
    for row in catalogue:
        center = [Fraction(float(v)) for v in row[:3]]
        radius, brightness = Fraction(float(row[3])), Fraction(float(row[4]))
        if not brightness:
            continue
        occupied = []
        for index in np.ndindex(result.shape):
            sites = [
                (Fraction(2 * index[a] + 1, 2) * Fraction(float(spacing[a])) / refinement[a])
                for a in range(3)
            ]
            if sum((sites[a] - center[a]) ** 2 for a in range(3)) <= radius * radius:
                occupied.append(index)
        assert occupied
        weight = float(brightness / len(occupied))
        assert weight > 0
        for index in occupied:
            result[index] = float(result[index]) + weight
    return result


def metric_reference(estimated: Any, reference: Any) -> dict[str, Any]:
    """Independent exact-input high-precision descriptive reductions."""
    with localcontext() as ctx:
        ctx.prec = 1000
        pairs = [
            (dec(x), dec(y)) for x, y in zip(np.ravel(estimated), np.ravel(reference), strict=True)
        ]
        assert pairs
        errors = [x - y for x, y in pairs]
        reference_l2 = sum((y * y for _, y in pairs), Decimal(0)).sqrt()
        error_l2 = sum((e * e for e in errors), Decimal(0)).sqrt()
        values = {
            "reference_l2": reference_l2,
            "error_l2": error_l2,
            "relative_l2": error_l2 / reference_l2 if reference_l2 else None,
            "error_rms": (sum((e * e for e in errors), Decimal(0)) / len(errors)).sqrt(),
            "error_max_abs": max(abs(e) for e in errors),
            "error_mean": sum(errors, Decimal(0)) / len(errors),
        }
        result: dict[str, Any] = {"count": len(pairs), "unavailable_fields": []}
        for name, value in values.items():
            converted = None if value is None else float(value)
            if converted is None or not math.isfinite(converted):
                result[name] = None
                result["unavailable_fields"].append(
                    {
                        "field": name,
                        "reason": "zero_reference" if value is None else "unrepresentable",
                    }
                )
            else:
                result[name] = converted
        return result


def paired_axial_reference(source: Any, gain: float, contrast: float) -> Any:
    """Aggregate fixed adjacent axial cells in the evaluator's relative units."""
    assert source.ndim == 3 and source.shape[0] % 2 == 0 and contrast > 0
    shape = (source.shape[0] // 2, source.shape[1], source.shape[2])
    with localcontext() as ctx:
        ctx.prec = 1000
        values = [
            float(
                (dec(gain) * (dec(source[2 * k, y, x]) + dec(source[2 * k + 1, y, x])))
                / dec(contrast)
            )
            for k, y, x in np.ndindex(shape)
        ]
    assert all(math.isfinite(v) for v in values)
    return np.asarray(values, dtype=np.float64).reshape(shape)


def close_scalar(actual: Any, expected: Any, *, scale: float = 0.0) -> None:
    if expected is None:
        assert actual is None
    else:
        assert type(actual) in (float, int) and type(actual) is not bool
        assert math.isfinite(actual)
        # Tiny observers: 256 eps covers ordinary f64 evaluation/reduction;
        # use physical input scale where cancellation is expected, no fixed floor.
        allowance = 256 * np.finfo(float).eps * max(abs(expected), abs(scale))
        allowance += 16 * float.fromhex("0x0.0000000000001p-1022")
        assert abs(actual - expected) <= allowance, (actual, expected, allowance)


def check_metric(actual: dict[str, Any], estimated: Any, reference: Any) -> None:
    expected = metric_reference(estimated, reference)
    assert set(actual) == set(expected)
    assert actual["count"] == expected["count"]
    assert {tuple(sorted(x.items())) for x in actual["unavailable_fields"]} == {
        tuple(sorted(x.items())) for x in expected["unavailable_fields"]
    }
    scale = max(float(np.max(np.abs(estimated))), float(np.max(np.abs(reference))))
    for name in expected:
        if name not in ("count", "unavailable_fields"):
            close_scalar(
                actual[name], expected[name], scale=scale if name != "relative_l2" else 0.0
            )


def beam_error_reference(fitted: Any, true: Any, *, side_exchange: bool = False) -> list[float]:
    """Subtract independent normalized three-beam vectors with safe Decimal arithmetic."""
    with localcontext() as ctx:
        ctx.prec = 1000

        def unit(values: Any) -> list[Decimal]:
            assert len(values) == 3
            assert all(math.isfinite(float(v)) and float(v) >= 0 for v in values)
            exact = [dec(v) for v in values]
            scale = max(exact)
            assert scale > 0
            scaled = [v / scale for v in exact]
            norm = sum((v * v for v in scaled), Decimal(0)).sqrt()
            return [v / norm for v in scaled]

        fitted_unit, true_unit = unit(fitted), unit(true)
        if side_exchange:
            fitted_unit = [fitted_unit[0], fitted_unit[2], fitted_unit[1]]
        return [float(a - b) for a, b in zip(fitted_unit, true_unit, strict=True)]


def check_normalized_beam_errors(
    actual: Any, fitted: Any, true: Any, *, side_exchange: bool = False
) -> None:
    """Check all dimensionless beam errors against the safe independent reference."""
    expected = beam_error_reference(fitted, true, side_exchange=side_exchange)
    assert len(actual) == 3
    for value, target in zip(actual, expected, strict=True):
        close_scalar(value, target, scale=1.0)


def finite_mean_prediction_references(
    means: Any,
    *,
    true_gain: float,
    true_offset: float,
    true_background: float,
    estimated_blank: float,
    estimated_contrast: float,
) -> tuple[Any, Any]:
    """Evaluate complete signal/corrected references before float64 conversion."""
    values = np.asarray(means, dtype=np.float64)
    assert values.size > 0 and np.all(np.isfinite(values)) and np.all(values >= 0)
    assert all(
        math.isfinite(v)
        for v in (true_gain, true_offset, true_background, estimated_blank, estimated_contrast)
    )
    assert true_gain > 0 and estimated_contrast > 0 and true_background >= 0
    with localcontext() as ctx:
        ctx.prec = 1000
        gain, offset, background, blank, contrast = map(
            dec, (true_gain, true_offset, true_background, estimated_blank, estimated_contrast)
        )
        signal = [float(gain * dec(mu) / contrast) for mu in values.flat]
        corrected = [
            float((offset + gain * (dec(mu) + background) - blank) / contrast) for mu in values.flat
        ]
    assert all(math.isfinite(v) for v in (*signal, *corrected))
    return (
        np.asarray(signal, dtype=np.float64).reshape(values.shape),
        np.asarray(corrected, dtype=np.float64).reshape(values.shape),
    )


def check_available_metric(actual: Any, estimated: Any, reference: Any) -> None:
    """Require all seven known-finite metrics without rejecting legitimate nulls elsewhere."""
    expected = metric_reference(estimated, reference)
    assert expected["unavailable_fields"] == []
    assert all(v is not None for k, v in expected.items() if k != "unavailable_fields")
    assert type(actual) is dict and set(actual) == set(expected)
    assert actual["unavailable_fields"] == []
    check_metric(actual, estimated, reference)
