# LESSONS-UNRAISABLE-01 correction evidence

**Version 1.0.** Scope: issue #99 / `LESSONS-DOCTOR-01-F001` only. The
[task](../tasks/lessons-unraisable-diagnostics.md) owns the sole Current state.

Destructor exceptions can print source lines even when Python exits successfully.
The correction installs an unraisable hook that uses the existing source-free
exception renderer. It retains the exception type/message and available traceback
location, omits arbitrary object representations, and changes no warning filter
or native exit status. Pytest installs its own interception, so promoted singular
unraisable warnings also need the existing source-free traceback formatter in the
pytest report plugin. That path is limited to `PytestUnraisableExceptionWarning`
test reports; unrelated test reports and the launcher are unchanged.

## Inputs and qualification

- Human authorization: `/intake 99`, then **“Start implementing”**. Bounded
  infrastructure route and named ownership are unchanged.
- Execution baseline: `8ee8776352422e629b7701d7660006573ae298e6`, tree
  `3c394baca58d58449230602040fb04a32e740a25`; initially clean tracked state.
- Linux x86-64, glibc 2.41; checkout-local CPython 3.13.12, uv 0.12.19,
  pytest 9.1.1, pluggy 1.6.0 and Temurin 21.0.7+6. Existing activation file:
  `/workspace/.simrecon-tools/activate.sh`. No dependency or policy pins changed.
- `make preflight` passed, including locked all-group sync, reader preparation,
  interpreter/import identity and isolated hatchling 1.32.4. Durable ignored log:
  `artifacts/verification/issue-99/preflight.log`. Input metadata is in the adjacent
  `baseline-inputs.json`; it distinguishes baseline Git blobs from observed
  working-file hashes captured after test authoring started.
- Lock SHA256:
  `222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b`.
- Frozen runtime/test inputs below were recorded after the formatting-only repair.
  Initial draft test bytes were not separately checkpointed; baseline logs and
  the unchanged synthetic semantics are retained. Final exact candidate identity
  and full-gate/reviewer evidence are recorded outside tracked candidate bytes.

| File | Frozen SHA256 |
|---|---|
| `scripts/source_free_sitecustomize/sitecustomize.py` | `5c2992da3a882201fb15e5e8cc2a9cdbbbab6f2d6ea7a3db8a4eda4d5d73fc6f` |
| `scripts/source_free_sitecustomize/pytest_plugin.py` | `d0c962f75b396169fb30288990dc6e12443b6b7f3f877c977101c3b402a3e3bf` |
| `tests/test_source_free_check.py` | `8accf902adf32c53edff1c002a6be99daed8d43a0f861ed561a50caf49b88b3b` |

## Requirement and risk evidence

All additions use the public launcher and real subprocesses. Source/comment and
local markers differ from the deliberately retained authored messages. No existing
test or assertion was removed, and no test-only runtime seam was added.

| Scenarios / requirements | Public-entry proof in `test_source_free_check.py` | Cases |
|---|---|---:|
| S1/S2/S4; R1–R3 | `test_python_finalization_preserves_diagnostic_and_native_status_without_source`: explicit deletion and shutdown, native statuses 0 and 7, retained original location/message and absent markers | 4 |
| S3/S4; R3 | `test_python_child_inherits_unraisable_renderer_and_preserves_failure`: ordinary inherited child and parent retain status 7 and original diagnostic | 1 |
| S5/S6; R4 | `test_python_resource_warning_filters_preserve_meaning_location_and_status`: explicit warning and real unclosed file, ignore/always/error; ordinary promotion exits 1, finalization promotion exits 0 | 6 |
| S6; R2/R4 | `test_python_warning_promoted_during_finalization_retains_authored_message`: warning-as-error inside a destructor retains its authored message/location without source/locals | 1 |
| S7; R2/R5 | `test_pytest_unraisable_interception_preserves_selected_warning_policy`: both launcher modes, explicit warning/error/ignore settings, original message/location when emitted, native counts/status/test identity | 6 |
| S7/S8; R5/R6 | `test_pytest_grouped_unraisable_errors_preserve_each_cause_without_source`: two failing finalizers, both original messages/locations and one failed test through each mode | 2 |
| S8; R6 | All 65 existing diagnostic/launcher regression cases retained | 65 |

The 20 additions cover eight contract scenarios; parameter values are equivalent
examples, not new semantics. The grouped pytest cases already passed on baseline:
its group renderer uses the existing patched traceback path. No group detector or
unrelated report rewrite was needed. Shutdown also already omitted the source in
the measured baseline, so shutdown alone would not witness the explicit-deletion
defect. Independent review must challenge suppression masquerading as success,
incorrect observer parsing, missing inherited behavior, warning-policy changes,
status changes and broad pytest-report side effects.

## Checks and diagnosed corrections

Worker logs and its detailed mapping are retained in ignored
`artifacts/verification/issue-99-worker/`.

| Check | Observed result / classification | Log |
|---|---|---|
| Initial unchanged-runtime focused suite | Exit 1: 6 failed, 77 passed, 17.08 s; intended source-rendering defects | `baseline-focused.log` |
| Strengthened unchanged-runtime pytest cases | Exit 1: 2 failed, 6 passed, 77 deselected, 2.44 s; both promoted singular reports need original diagnostic fields | `baseline-pytest-strengthened.log` |
| Native synthetic reference probes, two invocations | Both outer commands exit 0; individual native outcomes and pytest warning/count/status oracles recorded separately | `native-oracles.log`, `native-group-oracle.log` |
| Corrected complete focused suite | Exit 0: 85 passed, 13.80 s | `post-repair-focused.log` |
| Initial named-file Ruff lint / format check | Both exit 1; three long lines and test formatting, classified author style defects | `lint.initial.log`, `format.initial.log` |
| One Ruff formatting repair; final lint / format check | Repair exit 0, one file reformatted; both final checks exit 0 | `format-repair.log`, `lint.log`, `format.log` |
| Named-file Pyright | Exit 0, zero errors/warnings/informations; subsequent edits were formatting only | `types.log` |

The focused command was
`uv run --locked python -m pytest tests/test_source_free_check.py` after activating
the pinned environment. The strengthened baseline used
`-k 'pytest_unraisable_interception or pytest_grouped_unraisable'`. S7 assertions
were strengthened and the two group examples added before runtime implementation.
The corrected focused run preceded the formatting-only repair; exact formatted
candidate validation belongs to the full gate, not that earlier focused result.

## Final gate, review and limits

The coordinator prepares this report/task pointer before committing the candidate.
Canonical full verification uses `make verify` with contract `LESSONS-UNRAISABLE-01`
and the execution base above. Its exact commit/tree, command/status, all 13 phases,
native coverage integers, same-run M25, wheels/version/build identities and fresh
independent reviewer verdict belong in the final conversation and ignored
`artifacts/verification/issue-99/` records. The normal full-gate receipt and logs
remain under `artifacts/verification/`. This report does not predict their result.

Coverage percentages are advisory under PROJECT. Native report integrity,
never-imported/subprocess/package/global scope, the 33,554,432-byte M25 limit and
all other existing gates remain binding. Only local Linux qualification is
available here; Ubuntu/macOS CI remains required for submission. No Python 3.12,
general message redaction, engineered isolation or universal diagnostic
certification is claimed. The missing original doctor probe/accounting remains
an initial-intake access limitation: PR #101 subsequently restored the original
probe/source records and the parent accounting. Their helper hashes match the
recorded baseline. See the task's provenance links; the recovered historical
observations do not supply another product-qualification run. No actual
blind-session product-source exposure is established, and
this disposition supplies no closure of other source-free findings.

## Publication integration

The owner subsequently requested the PR. Main had advanced through documentation
PRs #101/#102 to `02bb2c95aada93057186d6efcde0050ffb7d597e`, adding the original
22-line doctor intake at this task's path. The coordinator resolves that add/add
conflict by preserving R1–R6/S1–S8, the implementation authorization and sole
execution state, and restoring original finding/source/disposition/parent links.
No incoming or reconciled change touches diagnostic runtime/tests, dependencies,
Makefile or workflow settings. Existing observations/dispositions remain immutable.

The first correction candidate `8e71a6b76e7b584b0a14f2c0274301ee5f512667` passed
full verification (3120 tests, all 13 phases) and one fresh independent review.
Its two gate attempts, including the interrupted technical-timeout correction,
remain under ignored `artifacts/verification/issue-99/`. Frozen runtime/test hashes
above remain unchanged. The merged publication candidate gets a new exact full
gate and a fresh independent reviewer before push/PR; the new identities, results,
additional attempts and PR URL belong outside tracked bytes in
`artifacts/verification/issue-99-pr/` and the PR/conversation. No old receipt is
relabeled as the new candidate. Parent doctor charges remain separate and linked.

Historical intake accounting: one discovery helper launch plus one continued
sanity-check turn; optional helper `gh` reread forbidden, coordinator connector
read successful. Execution accounting through candidate preparation: one bounded
worker launch; two valid failing baseline rounds; two native reference probe
invocations; one runtime correction; one passing focused suite; one formatting
repair after two failed style checks; passing final style/types checks. The
worker's initial path inventory exited 2 because its scratch path did not yet
exist, with no dependent check run. Final full-gate/review attempts are accounted
outside this candidate. Prior doctor counts and per-role served-model attribution,
tokens, cached tokens, verified money and complete elapsed totals are unknown.
Worker requested `gpt-6.1-sol`/high; fresh reviewer uses the same project default.
Human-set limits are not set. Fresh roles or corrections erase no prior attempts.
