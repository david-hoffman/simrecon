# IE113 infrastructure exports — source-only handoff

Status: **UNVERIFIED; execution HOLD.** This report records one fresh bounded
infrastructure source attempt, not an installed proof or acceptance verdict.
Only `scripts/check_installed_wheels.py` and this report were written.

## Assignment and immutable entry

- Worktree: `/workspace/work/issue-113`; branch:
  `feat/113-single-known-reconstruction`.
- Entry HEAD: `1f718efedd7455d0815cd5203350c57b23ad31d8`;
  tree: `c8669e6470633bb885c5c95fa9f2f59094373eaa`; tracked/untracked status was clean.
  This is the supplied UNVERIFIED C5 source checkpoint, not a passing candidate.
- Actual assignment:
  `/workspace/work/campaign/evidence/113/ie113-source-assignment-1.md`, SHA256
  `bceb7c508f3a18abd7b8222f1631df1e4e3a7eb7fc1180af9a391d2409bd6400`.
- Applied launch preparation:
  `/workspace/work/campaign/evidence/113/ie113-source-launch-prep-1.md`, SHA256
  `ac72407605ba2910951f755af43d841a00384cef14ce9655d8f34348c0c329b2`.
- Mode: selected `.agents/skills/implement-work/SKILL.md`, bounded worker;
  no delegation. Tool-assigned task identity: `/root/issue_113/ie113_source`.
  An opaque launch/session ID and served model/effort were not exposed to this
  worker. Requested route is fresh, no inherited conversation,
  gpt-6.1-sol/high, as supplied in the assignment. Optional engineered memory,
  read-only and delegation controls were unavailable; shared filesystem and
  prompt restrictions establish no engineered isolation.

The operative route is first unpublished scientific Phase P parent accepted 115,
`ace06c861b974b6251a092567c253ae4eb0f56c8`, tree
`2247d3909f43bc4764beb5c748caa917aaa1d707`, with accepted 112 science,
inherited 115 representation and own B5. Final publication parent is actual
accepted 120. The old ownership packet's 116/active-A scheduling sentence is
historical and superseded by this assignment and applied preparation. No 116
truth, tolerance or resource conclusion was borrowed.

## Input identities and frozen ownership

All 18 entries in
`/workspace/work/campaign/evidence/113/ie113-source-inputs-1.sha256`
matched before the write. That manifest's SHA256 is
`4f98cde5061ba728530e9f93077ed5f39a478ae85834cb83ea45aa39451bf4a3`.
The checker is the sole deliberately changed manifest entry; the other 17 remain
unchanged. The assignment and preparation hashes above also matched.

Whole B5 accepted test checkpoint:
`d2a7bcc0a344b962b8480b84cf3ad71699d5730a`, tree
`1d0d765849f74463a77aee7f2105fc8e52c1af74`.
All 27 entries of
`/workspace/work/campaign/evidence/113/b5-accepted-inputs.sha256`
matched before and after the checker edit. Manifest SHA256:
`45767afb41e02d4535d66b732ff74a56f3a6494ae825535049a789b454a5c7a6`.
These are file-identity observations, not renewed B or execution evidence.

The two read-only compatibility expectation dependencies remain:

| File | SHA256 |
| --- | --- |
| `tests/test_module_migration.py` | `a44ec49fa55971fdf9c799774432ff5cd51e5929ab3bac0ca4fe0579f3e48804` |
| `tests/test_installed_wheels.py` | `ee7cb892b5dffaca29e4ac56fee69ad64a01343fb2f2d1c3bd83c2f7dfd1602e` |

All four scientific source identities matched before and after the checker edit.
The source-freeze manifest is
`/workspace/work/campaign/evidence/113/c1-source-freeze-5/product-inputs.sha256`,
SHA256 `8dcc2c24fd99df63d1c0bc4a481f0775c272d52b478eb5ae67a6a27dfc8bca86`:

| File | SHA256 |
| --- | --- |
| `src/simrecon/reconstruction/single_known.py` | `30d20b0538b2b5ac6a905e879d83831a5399a21024c51dc77bbc15ac12a84ff7` |
| `src/simrecon/reconstruction/known_parameters.py` | `339be4e67634ebc331d297b3c5cbc31e857d8925987933d5dcfb910af2370ba4` |
| `src/simrecon/__init__.py` | `20913571369110931c19e556afa9557584102f1a948c4e2f2a5dd63f8dcfd5c6` |
| `src/simrecon/reconstruction/__init__.py` | `2f4e01724bd661b53ba189c7ad1eb1529a3d2f73c7fe270b293d08b0578182e0` |

Only the expressly permitted root facade was opened from these four files;
the other three received hash-only inspection. No tests, scientific source,
helpers, renderer, commands, flags, dependencies, lock, configuration, policy,
skills or gates were edited. The contract's 293 scientific rows are unchanged.

## Minimal checker change and independent expectation

Baseline checker SHA256:
`4c52720f67cb47d91b7a1b3e59010aafaae0f3ab6b5dc4a3bdba5ec211f82d70`.
Resulting checker SHA256:
`fedfcdc2ad4c850ece75b6eb860111ed0dfa2a8d240f18227f2c681abd60b6a6`.

The complete checker was manually read and its entire diff manually inspected.
Its only delta is 4 inserted lines and 2 removed lines in two hunks:

1. Append exactly `declare_prepared_bands32`, `PreparedBands32` and
   `KnownReconstruction32` to the existing literal 38-name expected set.
2. Change the exact `__all__` cardinality assertion from 38 to 41 while retaining
   exact set equality and the original callable assertion.
3. Add `assert all(getattr(simrecon, name).__name__ == name for name in expected)`.
   ROOT explicitly authorized this installed identity guard under public §1.
4. Change the fixed product success message from 38 to 41 exports.

The independent oracle is approved
`docs/contracts/single-known-reconstruction-v1.md` §1 and S37.1, contract SHA256
`9f9feb707891be636190c5e9a22a66ad5d41f0b509c7e13007b68450a4e7c9eb`.
The expected set is literal, never derived from the product or facade. Its 41
distinct names are all original 38 followed by exactly the approved three:

```text
AcquisitionBands AcquisitionModeError ModeEvent TwoDPlaneInputs
prepare_acquisition_bands reinterpret_2d_planes DataBlock DatasetInfo
EstimatedParameters ImagejSeries ImagejWriteReport KnownReconstruction
OpticalTransfer OtfError ParameterEstimationError PreparedBands PreparedOtf
RawAcquisition ReconstructionError ReconstructionSummary SimreconError
WriteReport WorkflowError WorkflowReconstruction declare_acquisition declare_otf
estimate_parameters export_imagej harmonize inspect prepare_bands prepare_bead_otf
read reconstruct_known reconstruct_summary reconstruct_workflow sample_otf write
declare_prepared_bands32 PreparedBands32 KnownReconstruction32
```

Manual text comparison found no deleted old name, subset/count relaxation,
product call, fallback, new helper or stub. The existing doctor fixture is intact.
No import, parser or other semantic check was used to make these observations.

## Preserved checker behavior

Every other checker statement is unchanged, including:

- Product import-prefix assertion; absence of `simrecon_devtools`, `_delivery`,
  `_pytest_policy`, pytest, coverage, Ruff and Pyright; loaded-module absence;
  distribution-file utility-leakage rejection.
- Exact sole `simrecon = simrecon.cli:main` entry point; existing help commands;
  missing-input `inspect` status 1, empty stdout and JSON `io_error`; 30-second
  inner CLI timeouts and diagnostic capture.
- Sole product and separate devtools wheel checks; zip contamination rejection
  before installation; both wheel SHA256 prints; caller-outside-checkout check.
- Locked all-groups constraint export with unchanged arguments; separate
  product/devtools prefixes and installs; original interpreter selection;
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; unchanged PATH handling, temporary caller,
  subprocess commands, environments, checked status and 180-second run timeout.
- Isolated `-I` product/devtools probes and nested pytest callers; devtools
  installed-prefix assertions and product absence; doctor caller status 23,
  exact stdout and recorded caller/read-only/report-only requirements.
- Original codex fixture, strict pytest configuration/plugin and pass, skip,
  xfail, xpass status/output expectations; success/failure handling and return.

The two frozen compatibility tests were read in full and remain untouched.
The checkout test independently expects exact 41 names, callable/name identity,
removed paths and exception hierarchy. The installed test still builds separate
wheels, requires the 41-export message, both digest prints and real checker
success, and rejects a contaminated product with status 2. Their real execution
has not been established by this source-only attempt.

## Work performed, exposure and remaining gates

Runtime/quality/build/install/native/test/probe checks performed: **0**.
No Python, imports, AST/compile, Ruff/format, Pyright, pytest/collection, uv,
Docker, builds, installs, native calls or product/checker/helper execution ran.
Only permitted plain-file/manual text operations, SHA256 identity checks and
Git status/rev-parse/diff operations were used. The manual edit used
`apply_patch`. Hash verification is source-identity evidence, not a runtime pass.
All such command invocations completed; no runtime failure/repair attempt occurred.

This is source attempt 1 for this fresh IE worker, with one checker mutation and
one report creation. No commit, stage, push, restack, cleanup or external message
was performed. Exposure was limited to the assignment, applied preparation,
named ownership/project/skill/templates, contract §1/S37.1, routing record,
checker, two compatibility tests, facade and named packaging/Make files; the
lock and remaining manifested inputs received hash/status-only inspection.
No linked records, raw science, role history or other-role reports were opened.
An oversized initial combined read was display-truncated; required project,
skill and template content was subsequently read in full in smaller reads.

No scratch file, fixture, environment, background job, persistent shell session,
owned child process or retained file descriptor was created. All shell calls
returned completion, with no session ID requiring polling. No process/FD
inventory or engineered descendant/descriptor-closure proof was attempted;
shared host state is outside this worker's claim. Retain both durable files.

All historical A/B/C, quality, finite, native, init, G1, setup, source, review and
correction charges remain cumulative. Inherited root facts are static 10 checks /
3 failures plus first source Pyright 1 / 1 failure, totaling 11 / 4 failures,
with a separate expected-status-1 import diagnostic. They are not this worker's
checks. No human numeric cap is set; actual served attribution/effort,
input/cached/output tokens, verified monetary cost and elapsed/wait/check meters
remain unknown, never zero.

The coordinator must freeze this exact UNVERIFIED source delta. Actual installed
proof and artifact/version/constraints/caller identities remain missing. Future
cheap/type checks and real separate-wheel execution need a specific ROOT release
and qualified process/material environment. ROOT's accepted-120 integration/new
candidate requires fresh affected B/material/profile/helper/oracle/native/
environment renewal before integrated work/resources/fullgate/D/publication.
Full Ubuntu 13-phase verification, strict outcomes, native global/package/file/
never-imported/subprocess reports, same-run M25 and audit remain binding;
percentages remain advisory. Fresh independent D must explicitly assess the
independent 41-name oracle, both frozen compatibility expectation dependencies,
the full checker diff and preserved guards, and actual isolated proof/artifacts;
otherwise a separate fresh bounded infrastructure reviewer is required.
No acceptance/publication claim is made. Source-only handoff, then HOLD.

Final report SHA256 and final dirty-status/hash confirmation are supplied outside
this report so the report does not attempt to contain its own final digest.
