# PH118 A3 focused checks

Current status: the corrected exact owned test passed Ruff, format-check,
Pyright and27 pytest cases; approved keeper groups A/B/C/D passed1/21/49/34
cases. The earlier CE02 FFT expectation was resolved as a test-scope defect,
preserved below and corrected to its explicit factorization guarantee. No
accepted checkpoint or readiness verdict is claimed. No command remains running.

## Binding and scope

Same still-blind A3 continuation, under
`docs/packets/issue-118-a3-focused-check-grant.md`, supplied SHA256
`457dfae9aa275e90893b7e9a3a5e7294c27832250e87d2e7d4ac485d0963ed23`.
Coordinator-bound committed HEAD `32d9c9651f9ca884cbec31793cb80d47571e0645`, tree
`ee654eec7598c3d3fe8702aca73cd6ecffa467a1`; uncommitted initial test SHA256
`0ddf8f02cd9a3c303c3447405c0beedeb21490794498611fb8ada647e21e4fe7`.
PH118 contract remains supplied SHA256
`d217c186ae2e736fb6fbfe29a432b84d5e34e6490679a422835253742bbcf3e5`.
No Git/history/source/task-state inspection was used to rederive these bindings.

Root granted sequential ordinary focused checks only, with no install/sync,
benchmark, measurement, runtime/shared-tool change, C, integration or push.
All executable checks below used the exact pinned Ubuntu container command:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-118 -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin simrecon-campaign-ubuntu
```

Append each command in the ledger below after that prefix. Host shell capture
used `set -o pipefail` and `2>&1 | tee` to a unique per-command log, retaining the
actual nonzero pipeline status. No earlier log was overwritten. No workers or
parallel test flag was used. Python/test outcomes used the committed unchanged
`scripts/source_free_check.py` wrapper; its source was not read. Ruff/formatter/
Pyright diagnostics rendered only the owned test path/text. Pytest failures
rendered category/message/owned assertion locations, not product source.

Observed test environment: Linux, Python3.13.12, pytest9.1.1, pluggy1.6.0,
platformdirs4.12.2 and xdist3.8.0 installed plugin. The commands did not select
workers. Locked uv with `--no-sync` was used throughout; there was no environment
repair or installation. Effective backend/allocator/profile qualification and
resource evidence were not probed or inferred from these outcomes.

No excluded source/history/PROJECT/mixed-audit/task-state/coverage/lesson read
occurred. No source exposure or unsupported custom diagnostic route occurred.
Original `a3.md` and `a3-static-proof-gap-preparation.md` were not changed.
The only correction scope is the owned test. No scratch process remains.

## Exact command/status ledger

Logs are under `docs/reports/issue-118/focused-a3/`. Each filename is unique.

| # / log | Arguments after the Docker prefix | Status and observed result |
| --- | --- | --- |
| 01 `01-ruff-check-initial.log` | `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py` | exit1; two E501 long lines at original owned lines330/384. Style defect, no science result. |
| 02 `02-ruff-format-check-initial.log` | `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py` | exit1; one file would be reformatted. Full formatter diff retained in log; only owned text. |
| 03 `03-ruff-format-repair.log` | `uv run --locked --no-sync ruff format tests/test_preparation_harmonic_lifetimes.py` | exit0; one file reformatted under explicit failed-format repair grant. |
| 04 `04-ruff-check-formatted.log` | `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py` | exit0; all checks passed. |
| 05 `05-ruff-format-check-formatted.log` | `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py` | exit0; one file already formatted. |
| 06 `06-pyright-formatted.log` | `uv run --locked --no-sync pyright tests/test_preparation_harmonic_lifetimes.py` | exit0;0errors,0warnings,0informations. Yielded terminal session69566 completed. |
| 07 `07-owned-pytest-formatted.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest tests/test_preparation_harmonic_lifetimes.py` | exit1;27collected,26passed/1failed in11.63s. Failure at direct backend/prepare_bands exception-type assertion, owned line637. Yielded session85813 completed. |
| 08 `08-owned-backend-ce02-diagnostic.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest 'tests/test_preparation_harmonic_lifetimes.py::test_direct_entry_external_failure_semantics[backend-prepare_bands]'` | exit1;1collected/1failed in.47s. Added diagnostic observes RuntimeError sentinel, not the expected SimreconError. |
| 09 `09-ruff-check-diagnostic.log` | `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py` | exit0; all checks passed. |
| 10 `10-ruff-format-check-diagnostic.log` | `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py` | exit1; formatter requests joining the two owned diagnostic f-string lines. |
| 11 `11-pyright-diagnostic.log` | `uv run --locked --no-sync pyright tests/test_preparation_harmonic_lifetimes.py` | exit0;0errors,0warnings,0informations. Yielded session54294 completed. |
| 12 `12-ruff-format-diagnostic-repair.log` | `uv run --locked --no-sync ruff format tests/test_preparation_harmonic_lifetimes.py` | exit0; one file reformatted, diagnostic layout only. |

Style and type evidence in04/05/06 applies to the formatted initial test hash
below.09/11 apply to the diagnostic edit before its final whitespace formatting.
There is no claim that all narrow checks or full pytest passed for the current
exact test bytes. No timeouts, installs, environment failures or product edits
occurred. Tool/pytest durations are not added to infer total elapsed/cost.

## Corrections, hashes and failure diagnosis

1. Initial static input
   `0ddf8f02cd9a3c303c3447405c0beedeb21490794498611fb8ada647e21e4fe7`
   failed two Ruff long-line findings and format-check. Authorized formatter-only
   repair produced
   `515d37b3b2d6206543306a44fe14381a0e11d89e9658436330f4860daf201919`.
   No generator, expected value, tolerance, schema, test selection or assertion
   meaning changed.
2. Its owned pytest reported26passes and one failure in
   `test_direct_entry_external_failure_semantics[backend-prepare_bands]`.
   The original source-free failure showed only an AssertionError/owned location.
   Added an assertion message containing expected category and observed captured
   category/message, with no product inspection or altered expectation. Hash:
   `32f2cb3412fb667b5562ac8d648aa2f605d6e70683074ed49acf22367d421ec4`.
3. Single-case rerun observed:
   `prepare_bands backend: expected SimreconError; observed RuntimeError: PH118 unavailable external array/transform dependency`.
   This is actual external backend interception, not the permitted
   no-interception positive branch. The caller snapshot check preceding the type
   assertion passed; no result had returned. This diagnoses the failed assertion,
   not the normative error category by itself.
4. Diagnostic-only format-check requested an f-string layout join. Formatter
   repair produced current hash
   `5df2ac664b0550998aa88345ad156e81155ce9542eba99fa14eb8770a442b88e`.
   No expectation or tolerance changed. All failed command logs remain.

The classification is unresolved expectation/test scope, not certified product
red. CE02 explicitly says backend **factorization** failures, nonfinite matrices/
noise and overflow/nonfinite transforms are numerical-operation errors through
SimreconError. In contrast CE04/CE06 explicitly state allocation/transform/backend
translation/cause rules. My static S25 addition generalized CE02's paragraph to
an arbitrary externally injected FFT RuntimeError; that generalization needs
coordinator/intake resolution before it is used as an acceptance obligation.
The packet authorizes no new meaning, mandatory backend binding or relaxing an
assertion to obtain a pass. I sent the exact distinction/result to the coordinator
and left the assertion unchanged. No runtime repair or waiver is attempted.

The diagnostic edit affects only S25's failure rendering. Original P/H/D/G/W/V/X
fixtures, mathematical values, independent oracles, snapshot format and numeric
budgets remain unchanged. The formatter touched layout throughout the owned file
but did not commission new scientific claims. Fresh B must still review the
entire eventual exact checkpoint; accepted checkpoint remains NONE.

## Observed evidence and remaining limits

The27-item run had26passes. The numerical/ownership/compatibility witnesses
other than this one row completed in that run; no result is called a baseline
versus candidate fingerprint, full-gate acceptance or scientific completeness.
Eight remaining direct-fault rows passed, but their ordinary pytest output does
not identify whether their conditional interception or valid alternative branch
ran. Do not advertise eight observed fault paths from these pass counts. Only
the failing CE02 backend row's interception is directly identified by the
diagnostic evidence above. No fault observer counter or backend binding is
inferred from implementation.

The approved selected keeper groups A/B/C/D have NOT run, because the grant
orders them after the owned-file checks pass. This includes the T2 persistent
sentinel/prepass scientific keeper, structural/representation group, acquisition
filter file, and summary projection/fault/discarded-diagnostic/unsafe-path group.
Their prior static delta mappings remain conditional; none gained execution
evidence from this continuation yet.

Next action: coordinator resolves the direct CE02 arbitrary-FFT error expectation
within approved public meaning or routes it back to intake. Then only authorized
owned-test correction, all affected narrow checks and owned pytest may proceed.
No selected keeper group should be started before the prerequisite passes.
Root may suspend ordinary execution before exclusive116 measurements; no current
process must be interrupted at this revision. No benchmark/resource work was
performed or newly scheduled by A.

Still required later: final actual parent117 freeze and inherited supported
profile/shared-helper reassessment; exact fixture/contract applicability; fresh
B acceptance; C only after its prerequisites; complete exact Ubuntu verification,
required coverage/wheel/import/audit/M25 reports, matched resource comparisons
and fresh D. Numeric tolerances were not inflated. No source-free output supplies
missing parent/profile/resource evidence.

## Preservation and accounting

Original report expected SHA256:
`bc0443f17502bafb6d2c56a671057c2caed21af93519246b3eacae5181270ef7`.
Static delta report expected SHA256:
`6f5099e4b698601fbe4b78b469ee5e2b6eaff1ccaa8fbc768c5eab6fd31ca86c`.
They were not edited. This new report and source-free unique command logs are
authorized outputs. Final content hashes will be supplied outside their bytes.

Cumulative intake1, A launches3, original static continuation and this same-session
focused continuation remain counted. A1/A2 prior stops/unknown charges remain;
no fresh A4/B/C/D launch or acceptance is implied. Requested Sol/high unchanged;
actual model serving, token/cache/response counts, monetary cost and total
elapsed/wait/repair/check costs remain unknown beyond individual surfaced command
outcomes. Human numeric limits remain not set. Shared filesystem/prompt scopes
prove no engineered isolation. No commit/integration/push occurred.

## CE02 public-scope correction continuation — frozen before its probe

This dated-in-sequence section supersedes the unresolved disposition above;
the preceding command/failure history remains intact. Root/coordinator's whole
public correction packet, SHA256
`7c06722897fab82a8b73ec0ab61682743143b4ef3bc08e6273b4786a6e3804d5`,
classifies the arbitrary CE02 FFT RuntimeError translation assertion as a
TEST-SCOPE DEFECT. CE02 selects backend factorization-failure translation and
selected nonfinite/overflow results; it does not commission a universal FFT
exception wrapper. The observed RuntimeError is not adopted as a new numerical
or compatibility guarantee, and no product-red is waived.

Before semantic correction, exact failed bytes were copied to
`focused-a3/failed-test-5df2ac66-before-ce02-factorization.txt` and both source and
snapshot hashes verified as
`5df2ac664b0550998aa88345ad156e81155ce9542eba99fa14eb8770a442b88e`.
All12 earlier command logs remain unchanged. Original a3/static-delta reports
remain unchanged.

The corrected row is explicitly named
`test_direct_entry_external_failure_semantics[factorization-prepare_bands]`.
Only this CE02 backend witness changes meaning: selected public factorization
unavailability now uses a valid supplied full-column-rank P4/Q3 design with
phases(0,pi/2,pi,pi), O2, the first4 phases of the existing `_raw(2)` fixture,
T2/D2/Z2/Y3/X4 and existing L2/A2 geometry. Three distinct phase points prove
rank3; the duplicate pi point is legitimate overdetermined input. CE02's
independently derived left inverse is
L=((2,0,1,1),(1,0,-.5,-.5),(-1,2,-.5,-.5)), with noise(1.5,1.75).
The positive expected quadratures use this fixed L and already-approved
`c_preparation_fixture.expected` direct spatial sums, including the unchanged
raw-phase Nyquist endpoint. No factorization/product output supplies truth.

Pre-probe conditioning/bound derivation: ideal A has rows
(.25,.5,0),(.25,0,.5),(.25,-.5,0),(.25,-.5,0).
Its infinity norm is.75, A-transpose norm1.5 and L norm4. G=A-transpose*A is
((.25,-.125,.125),(-.125,.75,0),(.125,0,.25)), with inverse
((6,1,-3),(1,1.5,-.5),(-3,-.5,5.5)); inverse infinity norm10 and
G norm.875 give condition bound8.75. With the original binary64/elementary
model, represented-pi/trig errors give deltaA infinity norm<=8u and
deltaA-transpose<=16u; hence deltaG<=24u plus its four-term multiplication
error. The small well-conditioned solve is allowed the original conservative
gamma(4096) conditional primitive/solve reserve, not a changed tolerance.
Its coefficient perturbation uses
10*(delta_rhs+deltaG*coefficient_norm)/(1-10*deltaG), with positive margin.
All raw values<=41 and alpha1/384 give a per-phase Fourier absolute budget<=2.5625;
L's row norm4 gives coefficient budget<=10.25. G backward error under the reserve
is below5e-13, RHS reserve below2e-12, so this solve perturbation is below8e-11.
The direct-transform/phase-combination observer and original P envelope add less
than2e-11. Thus the unchanged rtol/atol2e-10 bounds the combined absolute
comparison (no near-zero relative claim). These are predeclared conditional
arithmetic/provider-stability assumptions, not installed backend certification.
If no provider interception occurs, a finite result must still meet this fixed
independent expectation; inability to qualify it is reported, never tuned away.

The control patches public NumPy/SciPy inv/solve/lstsq/pinv/svd/qr/cholesky and
SciPy LU/Cholesky factor/solve operations to raise an external LinAlgError.
It names no product call/binding. A legitimate pre-bound or other provider may
avoid interception; then only independent finite-positive evidence follows.
If selected factorization is intercepted, existing explicit SimreconError,
nonempty text, no partial result and unchanged callers are required. CE02 does
not gain a new original-cause rule. CE02 allocation/interruption and CE04/CE06
FFT/cause controls are unchanged, as are all original tolerances.

The parametrization now names the factorization row explicitly; other eight
API/fault rows retain their identities. The helper's optional factorization
branch and approved `c_preparation_fixture.expected` import are the only new
numerical dependencies; existing P/H/D/G/W/V/X helpers and expectations do not
change. A safe owned print now records API/fault, intercepted versus valid
alternative and call count. Future owned pytest capture reporting will expose
these labels; it supplies no product internals or mandatory interception rule.
The entire revised checkpoint still requires fresh B.

## Correction and keeper execution results

Semantic correction before formatting produced test SHA256
`aa851350318c9c830a0fbc9f33d4f46ef6ddee5933cdbc4676aadeb4807886bb`.
Ruff accepted it; format-check requested only joining the fixed L construction.
The authorized formatter produced final exact test SHA256
`ce63d3b83ba5257d821cf71076a42a745fc636ae8b40450c26527f15a61ac3ca`.
This hash remained unchanged through all following checks/keeper groups. No
tolerance, new input rejection, runtime, shared observer or original test
assertion was changed to obtain a passing result. The unsupported CE02 universal
FFT wrapper hypothesis was removed only through the root-approved public-scope
correction, with its failed bytes/logs retained.

All commands below use the identical Docker prefix and pipefail/unique log
capture protocol above. The `-rP` flag only displays captured passing-test
diagnostics from the owned safe branch observer; it changes no selected test,
scientific operation or source-free wrapper.

| # / log | Arguments after the Docker prefix | Status/result |
| --- | --- | --- |
| 13 `13-ruff-check-factorization.log` | `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py` | exit0; all checks passed on aa851350. |
| 14 `14-ruff-format-check-factorization.log` | `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py` | exit1; one fixed-matrix construction would be reformatted, owned text only. |
| 15 `15-ruff-format-factorization-repair.log` | `uv run --locked --no-sync ruff format tests/test_preparation_harmonic_lifetimes.py` | exit0; one file reformatted to ce63d3b8. |
| 16 `16-ruff-check-factorization-formatted.log` | `uv run --locked --no-sync ruff check tests/test_preparation_harmonic_lifetimes.py` | exit0; all checks passed on final bytes. |
| 17 `17-ruff-format-check-factorization-formatted.log` | `uv run --locked --no-sync ruff format --check tests/test_preparation_harmonic_lifetimes.py` | exit0; one file already formatted on final bytes. |
| 18 `18-pyright-factorization-formatted.log` | `uv run --locked --no-sync pyright tests/test_preparation_harmonic_lifetimes.py` | exit0;0errors/0warnings/0informations on final bytes; yielded session96632 completed. |
| 19 `19-owned-ce02-factorization-targeted.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP 'tests/test_preparation_harmonic_lifetimes.py::test_direct_entry_external_failure_semantics[factorization-prepare_bands]'` | exit0;1passed in.49s; actual factorization interception, calls1; yielded session75303 completed. |
| 20 `20-owned-pytest-factorization.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_preparation_harmonic_lifetimes.py` | exit0;27passed in11.72s; all9 direct fault rows report actual interception, calls1 each; yielded session95690 completed. |
| 21 `21-keeper-group-a.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest 'tests/test_c_workflow_numerical.py::test_complete_actual_workflow_against_raw_finite_observer[between-first-off-and-persistent-sentinel]'` | exit0;1passed in2.18s; yielded session75958 completed. |
| 22 `22-keeper-group-b.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest tests/test_c_acquisition_boundary.py::test_structural_unsafe_branch_rejects_before_numeric_work tests/test_c_acquisition_boundary.py::test_selected_fixed10_prepass_small_dimension_is_unsafe tests/test_c_acquisition_boundary.py::test_prepass_off_loop_limit_not_a_normal_off_count_limit tests/test_c_acquisition_boundary.py::test_prepass_off_loop_exact_y_plus_one_endpoint_positive tests/test_c_workflow_validation.py::test_recognized_unsafe_branches_are_unsupported tests/test_c_workflow_validation.py::test_representation_limits_with_real_small_backing` | exit0;21passed in1.13s; yielded session29713 completed. |
| 23 `23-keeper-group-c.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest tests/test_c_acquisition_filter.py` | exit0;49passed in38.60s; yielded session72417 completed. |
| 24 `24-keeper-group-d.log` | `uv run --locked --no-sync python scripts/source_free_check.py pytest tests/test_reconstruction_summary.py::test_full_summary_exact_scientific_and_projection_matrix tests/test_reconstruction_summary.py::test_summary_external_failure_semantics tests/test_reconstruction_summary.py::test_discarded_regression_correlation_must_remain_finite tests/test_reconstruction_summary.py::test_summary_inherited_structurally_unsafe_paths` | exit0;34passed in101.01s; yielded session32286 completed. |

All approved ordinary focused work completed sequentially. No timeout, worker
flag, extra keeper group, environment repair, benchmark or full verification
was run. No suspension arrived during an in-flight command. Every yielded
terminal session above completed with its stated status; none remains running.
The surfaced pytest durations are check output only, not performance claims or
an additive estimate of campaign elapsed/cost.

### New versus retained proof and actual interception

For final owned bytes, the27 passing cases are author evidence for the original
P/H/D/G/W/V/X assertions and corrected S25 direct API controls. The new safe
captured labels identify actual external interception for CE02 allocation,
interruption and factorization, CE06 allocation/interruption/FFT backend and
CE04 allocation/interruption/FFT backend. Each selected check also verified its
promised category/cause where applicable, informative operation text where
applicable, unchanged public caller snapshot and no returned partial result.
This does not identify which internal allocation/transform site intercepted,
prove every possible backend binding or add a universal CE02 FFT-error promise.
The independently checked no-interception finite branch remains a legitimate
alternative in the test; it was not taken by these9 final rows.

The earlier26-pass initial run is not retroactively relabeled as9 observed fault
hooks, nor are its failing arbitrary-FFT outcomes erased. The corrected positive
factorization fixture/design and its conditional bounds were frozen before the
new probes. Its actual selected external-fault path intercepted; the no-hook
finite provider alternative was not exercised by that row here. Underlying
mathematical full rank and independent expected sums are not inferred from a
passing exception test.

Keeper group A supplies observed author evidence for the specific T2
persistent-camera-state/raw-prepass-to-fit-to-image keeper in the static delta
ledger. It does not independently check every T2 preparation trace numeric
member. Group B supplies observed structural reason/category and selected
representation-limit evidence with the explicit normal/no-prepass/N endpoint
alternatives. Group C supplies observed native filter/fractional/2D/time/signed
power/precise-positive keepers. Group D supplies observed exact full/summary
projection matrix, summary external semantics, discarded-regression finite
failure and inherited unsafe categories. Those retained fault controls allow
no-interception positives and do not print their branches, so group D's pass
count is NOT claimed to prove actual interception in every inherited summary
external row. Their stronger static obligation mapping remains as recorded in
the unchanged static delta report.

### Remaining gates and limits

No approved narrow command remains unrun for the final owned bytes, and no
selected keeper group remains unrun. This is still A author evidence, not fresh
B adequacy/acceptance or a frozen accepted checkpoint. B must review the exact
entire revised test/fixture dependency checkpoint, including the corrected
factorization expectation/provider controls and predeclared conditioning model.

The final actual parent117 freeze, inherited supported profiles/shared-helper
applicability and any changed-fixture/check evidence remain coordinator gates.
No same-environment parent/candidate public fingerprint comparison or exact
baseline sign-bit comparison was made. Full/summary exact relations and retained
old-result byte snapshots remain compatibility witnesses, supplemented by their
independent mathematical controls; they are not process-peak or lifetime-benefit
measurements. No full Ubuntu13-phase verification, full native coverage report,
wheel/import/audit/M25, matched resources or fresh D was performed by A.

Unlisted decoded/metadata fixture bodies were never read, so their independent
fixture construction is still outside this author's audited scope. The selected
group D visible projection assertions executed, without granting permission to
follow those imports statically. S26 direct-stage observer integration and
resource inventory/scheduling remain unresolved future work, not infrastructure
commissioned or performed here. No new percentage target or numeric cap follows.

Only the owned test, this focused report,24 unique command logs and the explicit
failed-input .txt snapshot were written. Original a3/static-delta reports remain
unchanged; their final verification hashes and this report's final hash are
supplied separately. No source exposure, delegated role, runtime/shared-tool
edit, integration, commit, push or benchmark occurred. Same A3 accounting,
prior failed attempts/repairs and unknown actual serving/usage/cost remain.

### Final continuation log identities

SHA256 values below bind the new command logs; numbers01–12 retain their
previously captured bytes/hashes and all earlier failure history above.

| Log # | SHA256 |
| --- | --- |
| 13 | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| 14 | `376fedfc00638cb02fed96856dbbda706b7528cc1f27dc17da98b4adbb7bdedf` |
| 15 | `413a709001976657cb743636fd34e48fc41d8d302d665460d3f874b3313da127` |
| 16 | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| 17 | `fd2299c9f1c6dc869070883e281051bfe93aacf66c1a3b0069f45b4aa410ca50` |
| 18 | `6d88a1b220adb7a3d62092b6e38431f0b3fe8babe9864fab90e5849766260332` |
| 19 | `f3c71bf933ec7862326b9410d29671ea45b43865b09fa3fbfeb2e7893d25b1be` |
| 20 | `249358cf88898ebf16b8808fff914c7dd183bdd6eac66d344fe90f5f3b15f787` |
| 21 | `8a4add6d6aede6498531f4e15e44dc547889787bc42a9424e703586289c45bc1` |
| 22 | `5a0277697c7b4440ba434182c0055dca353707cafaa3a7e891896e4d6fd8c785` |
| 23 | `f0607b1b9e205a88fb952dd9c157579eab11973bf524fb221f44512b28db18c6` |
| 24 | `f098ef2f7c7bc2d2f8b5d6601c0c97b595bc47e3c2b3a03ee194a6ba977d6c81` |
