# Issue 115 — restricted C implementation

## Status and identity

Authoring, static review and the authorized focused checks are complete. All
1118 focused tests and the three narrow source-quality checks passed. This is
not a passing full gate, independent D verdict or publication permission. The
coordinator owns the later exact clean integrated candidate and full gate.

C began on clean branch `feat/115-wide-allocation-domain` in
`/workspace/work/issue-115`, commit
`43ebeb466fa12ec6fc8c3fdabc54d9bf9f5790e2`, tree
`89d8de2be63157a6443cfd8b3e5b6f36dab7540d`. The frozen integrated parent is
`d9a0ba924817772fdb5550c7d055bf31bcf70388`, independently resolved tree
`836abd6603e28ea69c611429443c0684ba2f8441`.

Read current AGENTS, `docs/PROJECT.md`, implement-work skill in high-risk C mode,
C launch/candidate packets, the controlling W01–W18 contract, approved interface
excerpt, B2 report, focused wide tests and relevant inherited boundary/failure
sections. Relevant production callers were read narrowly; no legacy source or
private RM84 ancestry was opened. File restrictions are prompt boundaries on a
shared filesystem, not engineered isolation.

| Frozen input | SHA256 independently read by C |
| --- | --- |
| C launch packet | `4400f9891a15b5c0d12a3383fa48503b2328e3b375bc6546e275d0e52025efdd` |
| Wide contract | `d42cf0838e73fcaba1aa78c025c96582d246ea6bfef4323ab742323dfd169acb` |
| Interface excerpt | `0939e8956573eb5b7832f2bf80ddee8866c8c6a5a9db6eb1d48e9acfd1cbd180` |
| B2 report | `67e9ffbe0efa451b458432ddbf8565c7dc305561a33d4d174fb67bca4c599a7f` |
| Integrated 100-file test/fixture manifest | `3e4d18a1f9a96ae537eeac12bc126012b1d93c3d4613ed76b72da9b740302528` |
| uv.lock | `222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b` |
| pyproject.toml | `96a30134cc00103853913cfccaf673373b97760549467035082e71532c245abb` |
| scripts/source_free_check.py | `cdf5894e916c9445a1627da9e654d853b8f772fba9f376cee80680fed9701564` |

`sha256sum -c docs/reports/issue-115/tests-integrated-checkpoint.sha256`
returned 0: all 100 entries matched. No test, fixture, snapshot, configuration,
policy, packet, infrastructure, dependency or unrelated source was edited by C.
Coordinator-owned task/role-log/PROJECT edits may coexist in this shared worktree;
they are outside C's authorship and are not rolled back or claimed here.

## Owned diff and arithmetic argument

Only two of the five permitted runtime files require edits:

* `reconstruction/known_parameters.py`: remove the unsigned32 constant and four
  byte-only comparisons; remove signed32 lookup-byte comparison. Retain all
  signed dimensions/native/half/output plane/output volume/phase/order products
  and all native actual-array checks. Explain why actual widths dominate.
* `acquisition/layout.py`: remove the unsigned32 complex/real output comparisons
  and signed32 lookup-byte comparison in `output_extents`. Retain signed output
  counts, complex128 per-output volume and binary64 aggregate image extents.

`acquisition/modes.py`, `acquisition/preparation.py` and `workflow/config.py`
remain unchanged. No helper, public signature, parameter, dtype mode, result
field, test seam, backend maximum or memory-admission mode was added.

For M=native signed intp maximum and positive dimensions, existing `_extent`
uses exact Python-integer multiplication and inclusive `<=M` comparisons before
any narrowing/allocation. Production dimensions come from native ndarray shape
integers or the existing scalar integer resolvers, which return Python `int`.
The acquisition validator similarly uses `max(d,1)`, preserving conservative
stride validity for supported empty diagnostics; CE04 requires positive axes.
The checked actual arrays imply the five historical byte expressions as follows:

| Historical expression | Retained actual extent implying `0<B<=M` |
| --- | --- |
| `8*X*Y*Z` | `16*X*Y*Z <= M` for complex128 native workspace |
| `8*Xo*Yo*Zo` | `16*Xo*Yo*Zo <= M` for complex128 output workspace |
| `4*Xo*Yo*Zo` | complex128 extent above, plus `8*T*Xo*Yo*Zo <= M` for actual aggregate image |
| `8*O` | actual `(O,)` storage checked with item size 8; also Q<=P and Q*P<=I imply O<=23170 |
| `4*Xo*Yo` | actual CE04 `(Yo,Xo)` complex128 plane checked with item size 16; shared acquisition output complex128 volume also dominates since Zo>=1 |

These cover five CE04 and three shared CE06/workflow/summary obligations without
retaining obsolete caps or adding redundant byte branches. Lateral zoom still
uses inherited exact-float32/integral signed output-dimension validation; the
resulting byte products use resolved integer dimensions, not floating bytes.
Signed element/index/count restrictions and actual stencil/cutoff arithmetic
were not widened. No numerical filtering, transform, traversal, normalization,
phase, fit, ownership or projection code was changed.

All eight named product docs were aligned. CE04/CE06/CE07 describe native wide
byte validity separately from signed counts/indices. RM84 contract/summary guide
retain the historical exclusion as historical and describe the separately
commissioned extension. Target `(1,3,5,32,2048,2048)`, O3/L2/A1 is classified only
by integer geometry: output `(32,4096,4096)`, volume 536870912, historical complex
output bytes 4294967296. Its binary64 image alone is 4 GiB and binary64 raw array
15 GiB. Actual target allocation, backend execution and full-volume feasibility
are unmeasured; no 16 GiB/RAM guarantee follows. Historical scientific/resource
reports retain their original domain and were not rewritten.

## Production wiring, ordering and aggregate storage

CE04 `_reconstruct_known` calls `_validate_bands` before transfer validation,
parameter-array scans/copies, native filtering or assembly. PreparedBands metadata
is checked for scalar kind/shape/zoom/counts and every listed native extent
before `_finite(q)` or `_finite(noise)`. Its q extent includes T,D,Q,Z,Y,half-X
at 16 bytes; noise includes D,O at 8; carrier/amplitude tables, native full
workspace, output complex volume, aggregate T-output image, lookup/phase plane,
coordinate vectors and order storage have their respective actual widths.
This covers immutable result views and transient copies of those same shapes;
no additive live-RAM claim is inferred from per-array addressability.

AcquisitionBands takes the actual `validate_downstream_bands` route in
`acquisition/modes.py`. It strips ndarray subclasses through `np.asarray` views,
checks identity/scalars and retained signed counts, then calls the production
`output_extents` and actual q/noise extents before finite/value scans. Additional
known-stage native/carrier table extents are retained. Their sizes are already
dominated on the supported 64-bit platform by signed native volume and D*O
counts, so their placement after the downstream finite checks cannot hide known
native-invalid geometry. The separate dimensionality/noise-shape conventions
of PreparedBands and AcquisitionBands remain intact.

Acquisition preparation calls `raw_images` (native/padded/half/signed aggregate
frame counts and raw binary64 extent), resolves orders and zoom, then calls
`output_extents` before pixel inspection. `raw_off` checks off/on counts and
actual aggregate off storage. Before `array_metadata(images)` reads pixels,
the core also checks the actual aggregate complex128 quadratures and binary64
separator/phase/noise/frame/displacement diagnostics and metadata frame count.
Later real-array copies/owned/event captures retain extent checks with actual
widths, including conservative empty axes. Dynamic trace containers retain
native pointer extent checks. The unchanged CE02 `prepare_bands` path retains
its own `_index_domain` checks before reading raw samples; CE04 validates its
output record before reconstruction. No output allocation is commissioned by
CE02's stored zoom declaration.

Both public workflow entries call the same `_reconstruct_workflow` with only
the context-local capture policy differing. Settings/source-claim resolution is
scalar/container metadata work. Plain ndarray selection returns the backing;
RawAcquisition selection uses metadata-only axis/channel views/transposes and
checks full original data native extent without snapshotting array metadata.
`validate_workflow_geometry` then runs before backing scans, transfer numerical
preparation, hashes, snapshots or numerical work. It checks original/effective
signed geometry, delegates shared `output_extents`, and retains actual-width
aggregate raw, q, separator, phase, noise, displacement, output scratch and
layout-label extents. `validate_workflow_arrays_and_routes` checks aligned off
extent/exposure counts before its first raw scan. Raw metadata snapshots,
identity hashes and independent array copies occur only after these checks.
Thus the source review goes beyond the finite observer surfaces in the tests.
Array-valued declaration identities retain their own actual-width extent checks.

## Operation failure and compatibility preservation

The direct known `_operation` and acquisition `operation` context managers
retain existing direct-stage categories and `raise ... from error` causes for
operation exceptions, including MemoryError. They catch `Exception`, so
KeyboardInterrupt/SystemExit propagate. New allocation-valid declarations can
reach these ordinary operation failures; no representation or RAM rejection
is substituted. The full and summary workflow's `workflow_stage` rethrows direct
MemoryError and detects MemoryError in wrapped stage causes before translating
other failures to contextual WorkflowError. No partial result is returned.
The capture-policy context restores its token even on failures.

Known reconstruction snapshots mutable source quadratures, then filters into
private buffers; acquisition correction/preparation owns its arrays. Only private
compact preparation buffers may bypass a redundant snapshot. Full workflow
retains its writable band/noise debugging records; summary uses the same core
and arithmetic while compact projection omits full diagnostics. These mechanisms,
finite checks, actual transfer vertices (including zero weights), late-time
failures and result/caller ownership code remain unchanged.

Fault-hook limitations remain explicit. The frozen tests may accept a successful
independent positive branch when no external hook fires. Static inspection shows
the known-stage `ifftn` is imported directly, so patching `scipy.fft.ifftn` later
does not intercept that alias. No dynamic hook-hit claim follows for direct-known
backend cases. Its actual call is still inside `_operation`; preparation uses
module-qualified NumPy FFT calls and workflow/summary share that preparation.
Allocation hooks target actual `np.array`/allocation calls used by these paths.
The focused run passed every case, but its aggregate output exposes no hook-hit
counter. Static source inspection establishes the directly imported known-stage
backend alias limitation above; green tests are not represented as universal
fault interception or backend qualification.

## Commands, checks and remaining evidence

Administrative/static commands used `pwd`, Git status/branch/rev-parse/diff,
`sha256sum`, `cat`, `sed`, `rg`, and `wc`. Initial combined reads had three
path-resolution nonzero statuses: missing root `PROJECT.md` (actual file is
`docs/PROJECT.md`), singular interface filename (actual plural `interfaces`),
and guessed workflow/layout module (actual `workflow/adapters.py`). Corrected
reads succeeded. Some long displays truncated; pertinent sections were reread
in bounded calls. These were read-navigation mistakes, not product checks or
scientific failures. `git diff --check` returned 0 and all frozen manifest
entries matched. Patches were applied only within named product ownership.

Initial execution was held until the coordinator explicitly relayed root's
ordinary focused-window grant. Only the following authorized commands then ran,
with this exact prefix (no installs, benchmarks or full gate):

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-115 \
  -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  simrecon-campaign-ubuntu
```

| Suffix appended to that prefix | Result |
| --- | --- |
| `.venv/bin/python scripts/source_free_check.py --timeout 300 pytest tests/test_wide_allocation_domain.py tests/test_c_known_boundary.py tests/test_c_acquisition_boundary.py tests/test_c_workflow_validation.py tests/test_reconstruction_summary.py` | exit 0; 1118 collected/passed, 16 warnings, 131.23 s |
| `/workspace/.simrecon-tools/uv-env/bin/uv run --locked ruff check src/simrecon/reconstruction/known_parameters.py src/simrecon/acquisition/layout.py` | exit 0; all checks passed |
| `/workspace/.simrecon-tools/uv-env/bin/uv run --locked ruff format --check src/simrecon/reconstruction/known_parameters.py src/simrecon/acquisition/layout.py` | exit 0; 2 files already formatted |
| `/workspace/.simrecon-tools/uv-env/bin/uv run --locked pyright src/simrecon/reconstruction/known_parameters.py src/simrecon/acquisition/layout.py` | exit 0; 0 errors, 0 warnings, 0 informations |

The focused run identified Linux, Python 3.13.12, pytest 9.1.1, pluggy 1.6.0,
platformdirs 4.12.2 and xdist 3.8.0, using current pyproject.toml. This ordinary
focused run was not the full two-worker native-coverage gate. No file was edited
while a dependent check ran. The three independent narrow quality commands ran
after the focused behavior run, without source changes between them.

The 16 warnings came from invalid-input fixture arithmetic or coercion and one
NumPy dot warning under the infinity case, as shown by the source-free output;
they are not numerical acceptance values. The run also emitted exactly these
four previously recorded native lines:

```text
 ** On entry to DLASCL parameter number  4 had an illegal value
 ** On entry to DLASCL parameter number  4 had an illegal value
 ** On entry to DLASCL parameter number  4 had an illegal value
 ** On entry to DLASCL parameter number  4 had an illegal value
```

No different native diagnostic was observed. B2's exact-message disposition
applies; their provenance remains unlocalized and they establish no successful
factorization, universal harmlessness or new scientific claim. No intentional
large allocation or motivating-target execution occurred.

No installation, resource measurement, full gate, commit, push, restack, PR,
merge, release, closure, external message or nested agent launch occurred.
Coordinator was notified when checks were ready and promptly when the granted
window ended. Canonical exact clean Ubuntu 24.04
`make verify`, all 13 phases/two workers/strict discovery, current coverage
integers/reports including subprocesses/never-imported files, wheels/imports,
audit, same-run M25 and fresh D remain mandatory coordinator-owned later proof.
The focused successes above are current C evidence; no current native coverage,
wheel, audit, M25 or full-gate claim follows.

## Process and retained inputs

This is C launch/implementation session 1; D remains 0. Supplied cumulative
intake1, A1 plus continuation1, B1+B2 (two independent completed reviews),
cosmetic rounds2, semantic test corrections0, historical A10 checks/five nonzero
including product-red, environment/tool invocation diagnosis1, conservative
diagnostic stop1 and resolved missing-evidence request1 remain charged. No
counter is reset and no historical run is relabeled as integrated C evidence.
This C session adds four scientific/quality check commands, all exit 0, with no
behavioral repair or test correction after them. Administrative read-navigation
errors above remain separately disclosed and are not erased by those successes.
Actual human numeric limits are not set. Requested route is fresh
`gpt-6.1-sol`/high, `fork_turns=none`; served-model attribution, tokens, cost and
overall elapsed are unknown. Optional separate memory/delegation/read-only
controls were unavailable. C performed no delegation.

C created no scratch file, temporary fixture, background process or private
reference copy. The durable C report is this file. Required retained inputs are
the active worktree, frozen tests/fixtures, accepted packets/reports/contract,
locked environment/dependencies and shared pinned container. Coordinator owns
cleanup; no fixture or environment deletion was performed.
