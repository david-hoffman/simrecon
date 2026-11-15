# Issue 115 blind A test authorship

Status: **prepared for fresh B review; intended baseline product-red retained;
final narrow lint/format/type checks pass; no accepted checkpoint**.
This report is
separate from the final assistant handoff. It records authorship, not a passing
test result, B acceptance, implementation correctness or resource feasibility.

## Boundary and accounting

Role A worked directly in `/workspace/work/issue-115`, assigned branch
`feat/115-wide-allocation-domain`, supplied baseline
`b344e41a8b52de76d7cbbf8450319893904c3b8f`. No Git/source/history inspection was
performed to independently establish that baseline or branch. Scientific input
was the public packet and its explicit allowed public documentation/tests. No
runtime module, harness implementation, candidate packet, intake, task Current
state, coverage map, nonblind report, history or existing lesson was read.

Input SHA256 identities were checked with `sha256sum`:

| Input | SHA256 |
| --- | --- |
| Public packet | `8d81e5ada12f199f047e84f6c8faa32616f8b199867ed391443f38bcd8f940d5` |
| W01–W18 contract | `d42cf0838e73fcaba1aa78c025c96582d246ea6bfef4323ab742323dfd169acb` |
| Interface excerpt | `0939e8956573eb5b7832f2bf80ddee8866c8c6a5a9db6eb1d48e9acfd1cbd180` |
| A preparation addendum | `acf18993dee44db786f3ec4456b39408f29e5bf09348d9d7779b8d63b16f7fcd` |

Requested model/effort: `gpt-6.1-sol`/high, fresh `fork_turns="none"`. Actual
served attribution, tokens, cost and complete elapsed/owner-wait/check time are
unknown. The parent supplied initial A launches 1; B/C/D launches 0; review
rounds 0; test corrections 0. This session launched no roles and ran no failed
launches. Initial four focused check commands exited nonzero. The renewed
preparation ran six further narrow quality commands: one lint attempt failed
import ordering and the other five passed. Thus ten check invocations ran in
total (one pytest, three each lint/format/type), with five nonzero exits.
Preparation used two cosmetic repair batches; semantic test corrections remain
0 and substantive B review rounds remain 0. Initial authoring includes correcting the packet's explicitly
obsolete inherited expectations; it is not a correction of a B-accepted A
checkpoint. Human numeric limits are not set. CLOUD107 policy acceptance was
supplied as policy `b84b178`, integration `be8e447`; it proves launch authority,
not oracle quality. Separate optional memory/delegation/read-only controls were
unavailable. Shared filesystem and prompt restrictions are not engineered
isolation. No implementation source snippet/locals were exposed. The permitted
pytest command emitted four native LAPACK diagnostics; this initially unsupported
channel triggered the required conservative stop described below. Root then
classified these exact fixed messages as source-free in the permitted addendum
and authorized this same still-blind A to resume only narrow preparation. There
was no actual source exposure to undo, and no blanket renderer permission was
granted. The stop and messages remain in the evidence.

Coverage policy inherited from the packet/PROJECT is behavior plus independent
risk review, with percentages advisory. No coverage was measured. Exact native
statement/branch counts globally, per package and per owned file on Ubuntu,
including never-imported files and relevant subprocesses, remain later full-gate
obligations. No discovery, gate, threshold or runtime exclusion was changed.

## Initial behavior-run file identities

| File | SHA256 |
| --- | --- |
| `tests/test_wide_allocation_domain.py` | `a16ec25abc105e48a2352babb221cd3d7eb30aac62f93d4dc4cbcd7d4188a961` |
| `tests/wide_allocation_fixture.py` | `205836da05dbc17d3e22356a6a715e30501ae0b4f955726adb7ae1db4997aaf6` |
| `tests/test_c_known_boundary.py` | `9f17a12b32c70273e63dc87d0f5f28cc577dfa728e52246550a345a6a1cece50` |
| `tests/test_c_acquisition_boundary.py` | `ac66e1fbba22b2b0027556de70b5f47e2512838c1263a9215ffeee38ab760f86` |
| `tests/test_c_workflow_validation.py` | `0ae4005badef392502e310df1cd8bd8b7f47aa06cd9550d1a8b1194969e50052` |
| `tests/test_reconstruction_summary.py` | `aa9d4d23fd3a5efa421d682366bde8c97a971e823dad696f411d81dbd67a00c8` |

The 1118-item behavior run and first quality commands used exactly the six hashes
above. The addendum authorizes retaining that run across cosmetic preparation,
subject to B's independent applicability decision. Final identities are below.

| Final prepared file | SHA256 | Difference from behavior-run identity |
| --- | --- | --- |
| `tests/test_wide_allocation_domain.py` | `016c47bcbdff42b41c90b01a1c2f07af459c09574b0f127b1655e8c327d84360` | Constant `I` renamed `SIGNED_MAX` in import/references/comments; long decorator wrapped. |
| `tests/wide_allocation_fixture.py` | `09c7ac15b02226f986b17f12a244056654b1166b5accbd2c4407a5f7cb3e94c8` | Constant binding renamed `I` to `SIGNED_MAX`, value remains `2**31-1`. |
| `tests/test_c_known_boundary.py` | `1125ff758f2cade00fd007c6dbdb54b31eef4e93cf4f109a97292526e4efd6b9` | New keeper's constant import/reference renamed; original three-row decorator/function signature formatted. |
| `tests/test_c_acquisition_boundary.py` | `590d03ac6370b73294af1783f8e55eed1ffd932a1e50d2b80c7b8a56053b56b0` | New keeper's constant import/reference renamed. |
| `tests/test_c_workflow_validation.py` | `0ae4005badef392502e310df1cd8bd8b7f47aa06cd9550d1a8b1194969e50052` | Unchanged. |
| `tests/test_reconstruction_summary.py` | `aa9d4d23fd3a5efa421d682366bde8c97a971e823dad696f411d81dbd67a00c8` | Unchanged. |

All function names, parameter values, test discovery, comparisons, formulas,
fixtures, observer logic, tolerances, scientific call arguments and required
outcomes are unchanged by preparation. Consequently A proposes retaining all
initial passing/failing behavioral evidence and the W01–W18/keeper mapping for
these final files. This is not a fresh behavioral execution or B acceptance.
The final three quality commands ran against exactly the final six hashes. The
report's own digest belongs in the external handoff, avoiding self-reference.
No executable shared fixture outside the new owned fixture was edited.

## Independent oracle and safe construction

`wide_allocation_fixture.geometry` uses Python integer products and exact
`Fraction(lateral)` products, not a product helper's return value, floating byte
arithmetic or NumPy integer multiplication. Its signed inventory separates
dimensions, volume/plane, native padded/half, phase matrix, order and metadata
counts from five source-size byte expressions. Its native storage inventory
uses actual widths 8 and 16 and `s*product(max(d,1))`; the inventory is a necessary
representation check, not a claim that all arrays are simultaneously allocated.
No target geometry is converted into an array.

`M=2**63-1`, `I=2**31-1`, `U=2**32-1` are independently fixed contract constants;
the final executable fixture spells mathematical I as `SIGNED_MAX` for lint.
For storage widths 4 and 8, neither odd historical cap is an attainable byte
equality. The nearest attainable pair is `s*(cap//s)=cap-(s-1)` and
`s*(cap//s+1)=cap+1`. Scalar `cap-1/cap/cap+1` examples are arithmetic only.
Native tests use exact `M-1`, `M`, `M+1` at width 1, the exact factorization
`7*(M//7)=M`, and products `8*2**60=M+1` and `2**32*2**32=2**64`. Widths 8/16
use nearest attainable native bytes `M-(s-1)` and `M+1`. These distinguish float
rounding, signed wrap and unsigned wrap from exact comparisons.

Reachable output crossings use tiny native shape `(1,1,3,2,2,4)` and axial
neighbors of `2**25` (complex bytes `2**32`) and `2**26` (real bytes `2**32`).
Lookup crossing uses `(1,1,3,1,2,4)` and L=8191/8192/8193; lookup bytes are
`32*L**2`, crossing I at 8192 while plane counts remain signed32. Native complex
crossing uses integer-only `(1,1,3,Z,2,2)`, Z near `2**27`, complex-native bytes
`32*Z`, padded count `8*Z` and volume `4*Z`. All listed counts remain valid.

The signed output endpoint case X=2,Y=Z=1 has even output volume: I cannot be
attained. A=`I//2` gives I-1 and the next A gives I+1. The order byte guard is
dominated: Q<=P, Q=2O-1 and QP<=I imply O<=23170, giving order bytes<=185360,
far below U. No impossible independently valid O crossing is invented. Generic
storage proofs are explicitly not substitutes for direct-stage caller/order
proof; real-caller retention of the validators must be assessed nonblind by D.

Tiny real PreparedBands and AcquisitionBands preparations preserve their
different noise shapes. Newly admitted lateral byte declarations are paired
with invalid Wiener=0 through direct known calls, with valid carrier/modulation
shapes. Acquisition preparation uses invalid dxy=0; full/summary entries pair
wide bytes with invalid mapped dxy=0. These calls cannot complete their enlarged
numerical paths. The invalid field has the same category under ordinary geometry;
no precedence between independently invalid declarations is specified.

Small zero-raw direct/preparation controls have independently zero quadratures/
image, positive finite noise and defined nonzero Wiener denominator. Full
workflow uses the CE07 9.1 analytical fixture: the independently fixed closed
form and `2**-38` absolute image tolerance are unchanged from the accepted
fixture. Its bound covers <=16-term sums, table magnitude<=8, denominator>=2,
and the predeclared trig/FFT residual allowance; no fitted tolerance or product
baseline supplies the expected truth. Existing summary closed-form tests also
retain the `2**-42` modulation tolerance and independent coordinates. Existing
finite-observer cases retain their own unchanged conditional bounds; A did not
rederive or execute their complete science qualification here.

## W01–W18 scenario-to-keeper mapping

Names without a file prefix below are in `test_wide_allocation_domain.py`.
Existing retained tests are applicability proposals for B, not newly observed
passing evidence. Repeated parameters/routes are equivalent examples of these
18 scenarios, not additional scientific decisions.

| ID | Keeper assertions and limits |
| --- | --- |
| W01 | `test_native_byte_bound_is_inclusive_exact_and_does_not_wrap`, `test_actual_itemsize_and_aggregate_native_extents`: exact native bounds and product/wrap errors through both approved metadata validators. Positive/nonpositive scientific count requirements remain the inherited scalar tests; `_extent` is used only with positive shapes. |
| W02 | `test_historical_byte_crossings_use_native_storage_rule`, `test_native_complex_byte_crossing_keeps_native_element_counts`, `test_output_byte_crossings_with_valid_signed_counts`, `test_lookup_byte_crossing_does_not_widen_plane_indices`, `test_order_byte_ceiling_is_dominated_by_retained_phase_matrix_count`; corrected known L6000/L8192 and direct route complements. All five CE04 expressions have independent math; generic native/order extent tests do not alone prove each caller's absence of an obsolete guard. |
| W03 | Output/lookup crossing tests call production `output_extents`; corrected acquisition complex witness and workflow/summary wide witness complement with tiny independently invalid declarations. Signed endpoint/plane errors remain paired. |
| W04 | `test_signed_output_count_endpoint_is_separate_from_wide_bytes`; retained known `test_invalid_scalar_integer_and_taper_declarations`, acquisition `test_invalid_declarations_are_not_inferred_or_truncated`, workflow `test_single_invalid_mapped_value` and summary mapped delegate retain bool/nonintegral/nonpositive errors. Even-X output count reaches I-1/I+1, not impossible exact I. |
| W05 | Signed output endpoint and lookup plane overflow; retained known `test_used_source_products_reject_before_copying_virtual_arrays` (phase/volume/direction-order); acquisition `test_source_signed_extents_reject_before_materialization` and `test_acquisition_declared_on_frame_count_fits_signed32` (last fitting/first overflow T*D*Z*P across both consumers); workflow `source-byte-limit` remains a signed-count witness. Several source-product invalid examples violate multiple signed guards; they do not independently isolate every guard. |
| W06 | Retained known `test_reachable_undefined_derived_operations` cutoff/sampling/asin cases, unsafe stencil tests, acquisition precise-boundary and fixed10/prepass tests. New lookup bytes do not widen actual plane indices. No unverified FFT/backend maximum is added. |
| W07 | Native inclusive/exact, actual itemsize/aggregate tests and `test_supported_empty_diagnostic_shape_still_needs_native_strides`; 1/8/16-byte storage, nonempty positives and supported empty diagnostic strides. Aggregate crossing is explicit although each time slice fits. Empty scientific input success is never asserted. |
| W08 | Retained corrected known output test still has L65536, L16777217 and A=2**31; workflow fractional-extents and summary delegate remain. Acquisition invalid declarations and existing summary fractional scenario retain integral fractional enlargement versus invalid shrinking/nonintegral cases. |
| W09 | `test_invalid_output_geometry_precedes_copy_scan_and_backend` checks workflow and summary declaration-stage signed overflow before observed input copying/finite scans/FFTs, with large allocation interception only as a safety observer. Retained known source-product and acquisition signed-shape cases complement direct early rejection. Observer cannot instrument every possible external implementation; nonblind ordering review remains required. |
| W10 | `test_direct_routes_keep_invalid_field_after_wide_byte_admission`, `test_acquisition_invalid_pitch_category_after_complex_byte_admission`, `test_workflow_invalid_config_category_after_wide_byte_admission`; ordinary-geometry controls and inherited corrections retain exact direct/workflow categories. |
| W11 | Genuine native preparations via both accepted band routes, valid route-specific modulation/noise shapes and expected input_scale; same known invalid-Wiener outcome after wide bytes. Existing acquisition `test_invalid_used_records_both_consumers` and known record-validation tests retain forged-field rejection. This does not claim successful huge direct reconstruction. |
| W12 | Workflow/summary invalid-config and early-geometry tests use both entries; corrected workflow witness and its summary delegate remain linked. Retained summary `test_ce07_independent_closed_form` and `test_full_summary_exact_scientific_and_projection_matrix` check small images, parameters and projection. |
| W13 | `test_motivating_geometry_classification_is_integer_only`: exact contract table, all listed signed counts and illustrative aggregate actual-width extents, production integer validators only. Raw bytes=16106127360, image bytes=4294967296; RAM, timing, backend/stencil feasibility remain unmeasured. |
| W14 | New small-operation tests independently check zero input through direct/preparation routes and CE07 analytical output. Retained summary closed forms/finite-observer scenarios, signed-negative counts, zero/signed known carriers, and acquisition/known permitted type/zero/modulation cases preserve existing computation; no new precision mode. |
| W15 | Retained summary `test_entry_exports_and_signature`, projection matrix, `test_readonly_strided_inputs_and_post_return_isolation`, `test_full_debug_storage_and_mutable_direct_stage_inputs`; new failure tests also assert unchanged input arrays. No new public argument/result/precision/resource mode is requested. |
| W16 | Retained known `test_all_actual_zero_weight_stencil_vertices_are_required`, `test_zero_modulation_does_not_waive_axial_stencil`, opposite/self-overlap tests, `test_safe_flat_cross_axis_stencils_remain_permitted`, `test_only_actual_inside_self_queries_need_safe_stencils`; acquisition `test_k1_sampler_last_vertex_error_and_interior_complex_positive`; workflow unsafe-stencil plus summary delegate. |
| W17 | `test_small_operation_failures_keep_causes_interruptions_and_inputs` adds prepared/acquisition known, acquisition preparation and full workflow controlled small allocation/backend failures. Retained summary `test_summary_external_failure_semantics` covers summary. If an allowed backend/import alternative avoids interception, the test checks the independent small positive output and explicitly supplies no fault-path evidence for that row. Causes are required when intercepted; direct types/workflow allocation propagation are distinct. |
| W18 | Same small-operation test requires the exact injected interruption and unchanged arrays; retained summary external-failure test, late-time failure/error-context cases and `test_discarded_regression_correlation_must_remain_finite` preserve interruption/no-partial/finite-diagnostic requirements. Late failure remains whole-call failure. |

## Inherited declaration ledger and assertion preservation

| ID | Disposition and changed declaration | Keeper / preserved obligation |
| --- | --- | --- |
| A115-K1 | F: known `test_output_source_integer_unsigned_workspace_and_zoom_representation` renamed `test_output_source_integer_and_zoom_representation`; removed L6000/L8192 rejection rows only. | New `test_wide_output_bytes_are_not_a_known_representation_rejection` retains exact signed/native math and invalid-Wiener tiny-public proof; new integer output/lookup/route tests cover W02/W03/W10/W11. L65536 signed count, L16777217 inexact float32 and A=2**31 signed overflow rows remain W04/W05/W08. No unrelated assertion changed. |
| A115-A1 | R with clarified name/math: acquisition `test_unsigned_workspace_and_signed_lookup_representation` becomes `test_signed_output_counts_still_reject`. | Both retained rows have output plane/volume >=2**33 for Y2/X4, regardless of removed byte ceilings; W04/W05. Their rejection assertions remain. |
| A115-A2 | F: `test_complex_workspace_unsigned_limit_is_independently_binding` becomes `test_complex_workspace_crosses_old_unsigned_limit_without_rejection`. | Retains independently computed output volume2**29, complex bytes2**32, real bytes2**31 and signed lookup bytes2**30. Adds all signed/native math, successful integer `output_extents`, direct tiny invalid-pitch category. Removes obsolete byte rejection and its no-MemoryError cause-loop, replacing their early-safety obligation with the invalid declaration and W09/W17 keepers. W02/W03/W10. |
| A115-W1 | F: workflow representation parameter `unsigned-complex-workspace` becomes `wide-complex-workspace`; witness A=2**25 stays. | Exact original shape/native backing, output volume2**29, bytes2**32/2**31, native extents and alpha2**-29 remain. Integer output admission and tiny invalid-dxy workflow_config/declaration replace obsolete workflow_representation. W03/W10/W12. |
| A115-W2 | F: `workspace_limit_counts` changes `signed_counts_and_lookup_bytes` to `signed_counts`; lookup byte entry becomes output-plane count. | Prevents continuing to classify signed lookup bytes as a signed index. New geometry fixture separately reports all five byte expressions; new lookup crossing preserves W02/W03/W05. Original witness lookup bytes=32 is irrelevant to a signed count cap. Only this local witness uses the renamed dictionary key. |
| A115-S1 | F: summary inherited representation parameter updated together to `wide-complex-workspace`. | Same corrected delegate applies W03/W10/W12 through summary's public entry. Changes no shared fixture, schema, tolerance or observer. B must review this dependency with A115-W1/W2. |
| A115-R1 | R: workflow `source-byte-limit` parameter and summary delegate. | Actual padded count2**31+8 and output volume2**31 are signed overflow, so the legacy name is no reason to remove rejection. W04/W05/W09/W12. |
| A115-R2 | R: fractional extents, unsafe stencil and ordinary small positives throughout these files. | W06/W08/W14/W16; byte rule does not supersede scientific zoom or actual address checks. |

No test declaration was deleted without a keeper. The only removed assertions
are byte-only rejection expectations and the cause-loop whose premise was that
obsolete rejection. Non-test callers/history are deliberately not inspected by
blind A. No production/support seam was changed. B's affected review includes
all six exact Python files above, the workflow-summary delegation, and retained
evidence applicability; B decides whether scope must expand.

## Independent risk dispositions

* Fixed-width/float overflow: exact M neighbors, multi-axis wrap examples and
  exact Fraction/integer formulas; itemsize and positive count kept separate.
* Missed native/order/lookup bytes: five-expression inventory plus distinct
  output/lookup/native arithmetic witnesses and the order dominance proof.
  Real-caller reachability of generic validators remains a D obligation.
* Accidentally widened indices/counts: signed element endpoint, count-overflow
  keepers, cutoff/index/stencil controls and exact surviving inherited rows.
* Aggregate native storage and empty strides: explicit per-time-fit/aggregate-
  overflow, conservative empty dimensions, actual widths and target inventory.
* Forged records: genuine tiny preparations in new route tests; inherited used
  record/provenance tests remain. New tests forge no inconsistent record.
* Early copies/scans/backend work: tiny invalid geometry observers plus retained
  signed source cases; observers fail rather than allocate a giant target.
* Full/summary/direct category divergence: named paired invalid field and
  representation examples; no simultaneous-invalid precedence invented.
* Zero-weight stencil weakening: positive safe and invalid actual vertices are
  retained, including zero data/modulation/damping and short-circuited queries.
* Lost external causes/interruption: controlled small dependency failures require
  category/cause/whole-call failure when intercepted; legitimate backend
  alternatives retain positive proof with explicit fault-coverage limits.
* Suppressed finite checks/changed numerical or ownership semantics: inherited
  discarded diagnostic failure, finite observers, closed forms, mutation and
  full/summary debug projection tests remain; no target trial or precision
  selection substitutes for them.

## Commands, evidence status and next action

Authoring commands were source-free text reads (`cat`, `sed`, `rg` on allowed
files), `apply_patch` edits of owned files and `sha256sum` of the three public
inputs and six owned Python files. Execution initially remained held. The
coordinator subsequently explicitly granted the focused resource window after
#112 released it. The four original commands below ran once each against the
initial six file identities; after the source-free routing addendum, only the
six further narrow quality commands described below ran. No material input was edited while any
check was running. No runtime/harness source was opened, no independent probe,
measurement, installation or environment change occurred, and no
commits/pushes/PRs were made. Ruff printed only owned test/fixture snippets;
pytest and Pyright displayed no implementation source or locals.

No manually authored scratch files were created; standard tool-generated caches
were not inventoried by this restricted role. All foreground check processes completed;
no owned process remains active. The six Python files and this report are
durable owned artifacts. Existing shared inputs/environments are required and
were not altered. Coordinator owns cleanup.

The packet-supplied Ubuntu preflight reports Python3.13.12/NumPy2.5.3/SciPy1.18.1;
these were not independently probed by A. Pytest independently reported Linux,
Python3.13.12, pytest9.1.1, pluggy1.6.0, platformdirs4.12.2 and xdist3.8.0. No
broader platform/version claim follows.

The exact shared prefix used for all four commands was:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-115 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  simrecon-campaign-ubuntu
```

Each following command was appended to that prefix:

```text
.venv/bin/python scripts/source_free_check.py --timeout 300 pytest tests/test_wide_allocation_domain.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py
/workspace/.simrecon-tools/uv-env/bin/uv run --locked ruff check tests/test_wide_allocation_domain.py tests/wide_allocation_fixture.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py
/workspace/.simrecon-tools/uv-env/bin/uv run --locked ruff format --check tests/test_wide_allocation_domain.py tests/wide_allocation_fixture.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py
.venv/bin/python scripts/source_free_check.py --timeout 300 python -m pyright tests/test_wide_allocation_domain.py tests/wide_allocation_fixture.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py
```

| Check | Observed result / classification |
| --- | --- |
| Focused pytest | Exit1; 1118 collected, 1099 passed, 19 failed, 16 warnings in 128.26s. All 19 failures report obsolete complex-output/lookup byte ceilings, including intended admission results and corrected inherited witnesses. This is intended baseline product-red evidence for the new contract, limited to the exact six file hashes and command. No test failure was silently treated as success. |
| Ruff lint | Exit1, two author style defects: E501 at new test line296 (101 characters against100) and E741 for fixture constant `I` at line9. No runtime diagnostic/exposure. They were corrected during the separately released preparation below. |
| Ruff format check | Exit1; new test and known-boundary file would reformat, other four files already formatted. No formatter mutation was run. |
| Pyright | Exit1, 15 errors: missing NumPy/pytest/SciPy imports across inherited and new modules, plus a dependent existing optional-member `.copy` diagnostic. This is interpreter/tool-resolution failure, not established type failure in the new tests. Coordinator supplied a corrected project-interpreter invocation after this result; it ran during the separately released preparation below. No environment alteration was attempted. |

The 19 failing rows were: new output crossings A=33554432/33554433/
67108863/67108864/67108865; new lookup L8192/8193; new signed output endpoint
positive; motivating geometry; new direct PreparedBands L6000/L8192;
AcquisitionBands L6000/L8192; new acquisition pitch L4096/A2; inherited known
L6000/L8192; acquisition complex-workspace witness; workflow wide witness;
summary delegated wide witness. New ordinary controls, native integer bounds,
safe surviving count failures, early-work observers and small dependency fault
tests passed in this run. Fault-test conditional interception alternatives are
not individually measured by test output, so a passing row does not distinguish
fault interception from its allowed positive fallback.

Warnings retained categories/messages/locations without source lines. They were
RuntimeWarning/ComplexWarning in the existing public acquisition fixture and one
NumPy diagnostic, and were not suppressed. The exact final native stdout line
below appeared four times (including the double space before `4`):

```text
 ** On entry to DLASCL parameter number  4 had an illegal value
```

These contain
no implementation snippet or locals, but arise from a native diagnostic renderer
not initially supported by the packet's source-free harness guarantee. The packet says
to stop on an unsupported channel. A therefore stopped further checks/affected
blind work, reported it immediately to the coordinator and released the focused
resource window with no active owned process. No attempt to clear context,
broaden the harness, reclassify acceptance or suppress the channel was made.

The coordinator-supplied corrected narrow type command is the same
container prefix followed by:

```text
/workspace/.simrecon-tools/uv-env/bin/uv run --locked python scripts/source_free_check.py --timeout 300 python -m pyright tests/test_wide_allocation_domain.py tests/wide_allocation_fixture.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py
```

## Addendum routing and completed narrow preparation

The coordinator explicitly supplied the allowlisted preparation addendum and
its exact digest above. It classifies only the exact repeated LAPACK message as
source-free, permits the same A to continue, preserves the conservative stop and
requires B to consider any oracle relevance. It authorizes no blanket native
renderer, harness repair or environment modification. A read and verified the
addendum, received a renewed preparation window and made only the cosmetic
changes mapped above. No actual source/locals exposure occurred before or after
the stop.

Each of the two preparation rounds ran the same lint/format commands printed
above plus the corrected `uv run --locked python ...` source-free Pyright
command. The first preparation round passed format (all six files) and corrected
Pyright (0 errors/warnings/informations), but lint reported three I001 import
ordering defects introduced during the constant rename. A then changed only
those three import orderings, waited for checks to finish before editing, and
ran the final three commands once more:

| Final preparation check | Status |
| --- | --- |
| Narrow Ruff lint, same six owned files | Exit0: all checks passed. |
| Narrow Ruff format check, same six owned files | Exit0: six files already formatted. |
| Canonical uv-run source-free Pyright, same six owned files | Exit0: 0 errors, 0 warnings, 0 informations. |

There were no new behavioral semantics and no pytest rerun, as explicitly
directed by the addendum for style/constant-naming/interpreter changes. The
failed invocation and lint attempts remain recorded; they were neither erased
nor called product defects. The exact transient import-order revision was not
hashed and is not proposed as a reviewed artifact; all final checks were repeated
on the final exact hashes. No additional warnings, native messages or source
exposure appeared in preparation diagnostics. No installs, probes, environment
changes, full gate or benchmarks were run.

A immediately notified the coordinator that the renewed resource window was
released after all final checks completed; no owned process remains active.
Only report/hash work followed. Full `make verify`, resource/coverage
measurements and target numerical execution remain outside blind A's focused
scope. Fresh B acceptance of these exact prepared tests, the evidence-retention
decision and native-message oracle relevance remain pending.
