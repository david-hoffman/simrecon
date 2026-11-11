# SIMrecon project

**Version 1.0.** Git versions revisions. Active product status: CE02 preparation,
CE03 optical transfers, CE04 known-parameter filtering/assembly, CE05 finite
carrier/modulation estimation, CE06 selected acquisition modes and CE07 explicit
workflow composition.

## Approved architecture and current public boundary

SIMrecon is a functional Python/NumPy library for structured illumination microscopy
(SIM). The owner approved the functional architecture and first MRC conversion
contract on October 1, 2026, then two bounded amendments.
[Architecture approval and historical accounting](tasks/architecture-intake.md#current-state)
remain evidence; architecture alone authorizes no additional scientific behavior.

**The former scientific APIs remain retired during the mathematical C-equivalence
rebuild.** The new
[CE02 preparation contract](contracts/c-equivalence-preprocessing-v1.md) defines
`prepare_bands` / `PreparedBands` for the selected C camera, edge, equalization,
transform and phase-separation mapping. [Usage](usage/c-preparation.md) describes
the pure array boundary and its limits. Its
[task pointer](tasks/c-equivalence-preprocessing.md) owns current execution and
acceptance evidence. The [CE03 optical-transfer contract](contracts/c-equivalence-optical-transfer-v1.md)
defines `prepare_bead_otf`, `declare_otf`, `sample_otf`, `PreparedOtf`,
`OpticalTransfer` and `OtfError` for empirical bead preparation and complex
radial/full transfer sampling. [Usage](usage/c-optical-transfer.md) describes
explicit units, selected modes and safe stencil boundaries; its
[task pointer](tasks/c-equivalence-optical-transfer.md) owns current CE03 evidence.
The [CE04 known-parameter contract](contracts/c-equivalence-known-parameters-v1.md)
defines `reconstruct_known`, `KnownReconstruction` and `ReconstructionError`: native
bandwise filtering followed by signed Fourier assembly with supplied carriers and
complex modulation. [Usage](usage/c-known-reconstruction.md) specifies units,
coordinates and limits; its [task pointer](tasks/c-equivalence-known-parameters.md)
locates execution and acceptance evidence. The
[CE05 carrier/modulation contract](contracts/c-equivalence-carrier-modulation-v1.md)
defines `estimate_parameters`, `EstimatedParameters` and `ParameterEstimationError`.
It preserves the selected finite search and its ordered diagnostics, with
time-specific factors and optional time-zero carrier reuse.
[Usage](usage/c-parameter-estimation.md) shows explicit per-time composition into
the unchanged known-parameter operation; its
[task pointer](tasks/c-equivalence-carrier-modulation.md) locates execution and
acceptance evidence. The [CE06 acquisition-mode contract](contracts/c-equivalence-acquisition-modes-v1.md)
defines `prepare_acquisition_bands` and `reinterpret_2d_planes` for selected
2D/3D, phase, drift, off-exposure, geometry and filtering behavior. Its
[mode ledger](contracts/c-equivalence-acquisition-modes-ledger-v1.md) records
supported and excluded branches. The [CE07 workflow contract](contracts/c-equivalence-workflow-v1.md)
defines `reconstruct_workflow`, `WorkflowReconstruction` and `WorkflowError`.
It composes explicit calibration/transfer selection, acquisition preparation,
finite parameter estimation and per-time filtering/assembly. Its
[usage guide](usage/c-workflow.md) explains explicit metadata and units; its
[task pointer](tasks/c-equivalence-workflow.md) locates exact acceptance evidence.
Independent physical recovery acceptance remains CE08. Historical C executable agreement is
unqualified. The old `prepare_otf`, `reconstruct`, `reconstruct_volume` and retired
modules remain unavailable. The [retirement contract](contracts/c-equivalence-retirement-v1.md)
removes the old scientific stack, including phase/OTF preparation, correction,
calibration, estimation, simulation and reconstruction. The
[replacement roadmap](plans/c-equivalence-roadmap.md) supersedes the RA execution
plan. Its [common contract](contracts/c-equivalence-common-v1.md) requires the same
mathematical mapping and finite decision procedure as the selected retained C
call path; it does not claim bitwise agreement or a completed equivalent runtime.
The [CE01 task pointer](tasks/c-equivalence-reset.md) retains predecessor
candidate, role/check/review and execution evidence. Documentation status alone is
no readiness or acceptance verdict.

The neutral public functions are `inspect`, `read`, `harmonize`, `write`,
`declare_acquisition` and `export_imagej`, with their required records/errors.
The scientific entries are `prepare_bands`, `prepare_bead_otf`, `declare_otf`,
`sample_otf`, `prepare_acquisition_bands`, `reinterpret_2d_planes`,
`estimate_parameters`, `reconstruct_known` and `reconstruct_workflow`, with
their declared records/errors. They remain explicit array/value boundaries.
Callers may compose neutral reads and declarations before the workflow; the
workflow adds no file decoder, result writer or reconstruction CLI.
The neutral CLI remains in the product. The delivery command is installed by
the local development package during locked all-groups synchronization.

- The [MRC conversion contract](contracts/mrc-conversion-v1.md) defines metadata
  inspection, selected-block reads, pure metadata/layout resolution, streamed
  modern MRC writing and `simrecon inspect` / `simrecon convert`. Explicit
  configuration controls interpretation. Output preserves pixel bits, original
  metadata and override provenance in embedded HDF5 metadata. Conversion performs
  no scientific image correction or reconstruction. Modern MRC input decoding
  remains outside this boundary; mrcfile 1.5.4 is the development reference.
- The [acquisition declaration contract](contracts/raw-acquisition-declarations-v1.md)
  defines `declare_acquisition` / `RawAcquisition`. [Current usage](usage/raw-acquisition-declarations.md)
  covers owned bit-preserving arrays, explicit declarations and caller-selected
  MRC composition. Declaration estimates no phases, calibration or instrument settings.
- The [ImageJ contract](contracts/imagej-export-v1.md) defines `export_imagej`,
  `ImagejSeries`, `ImagejWriteReport` and `simrecon export-imagej`. One OME-BigTIFF
  contains an X/Y/Z/channel/time series for every orientation/phase pair.
  [Current usage](usage/imagej-export.md) and [retained interoperability evidence](reports/imagej-export-interop.md)
  describe pinned-reader results and limits. Original sources remain necessary for
  opaque-byte recovery; arrays, reconstruction results and modern MRC input are
  outside this export adapter.

[Library boundaries](architecture/library-design.md) and [data flow](architecture/data-flow.md)
describe the active file and array routes. [Scientific context](SCIENTIFIC-CONTEXT.md)
and [old migration history](MIGRATION-ROADMAP.md) preserve earlier scientific
designs and results. Historical scientific contracts, task records, reports
and usage examples retain their original claims, failed studies and cumulative
accounting. Retired commands are not current-package reproduction instructions. PR #7 is a
historical boundary, not a certified C-equivalent implementation. All old phase
and OTF APIs are also retired. No hidden alias or alternate development entry
point supplies retired science.

The owner permits studying legacy algorithms but requires independently written
Python. `SIMrecon_svn/` remains ignored, unshipped reference material. Do not copy,
ship, build, run, link or import it or its bundled executables. Comparisons use
independently supplied matching owner C outputs/configurations. The
[adoption baseline](setup/BASELINE.md) records historical compiler/test-discovery
limitations, not current product verification.

## Stack and structure

- Python 3.13.12, uv 0.12.19, locked `uv.lock`, one isolated `.venv` per worktree.
  NumPy/SciPy remain the locked numerical dependencies; h5py 3.16.0 is runtime,
  tifffile 2026.9.20 supports export and mrcfile 1.5.4 is a development reference.
  Their presence does not reactivate a retired scientific function.
- Owned library/runtime code lives in `src/simrecon/`; owned verification tools
  live in `scripts/` and `devtools/src/simrecon_devtools/`. The local
  `simrecon-devtools` distribution owns the doctor launcher and explicit pytest
  policy plugin; it is a development-group dependency, not a product dependency.
  Native statement/branch measurement includes all three roots,
  never-imported files and relevant subprocesses.
- Root [AGENTS.md](../AGENTS.md) holds shared rules; four `.agents/skills/`
  procedures hold role differences and [test-audit](../.agents/skills/test-audit/SKILL.md)
  supplies the cross-cutting audit procedure. The
  [delivery specification](agentic-software-delivery-v1.0/DELIVERY-SYSTEM-SPEC.md)
  defines policy. Root [LESSONS/](../LESSONS/README.md) is the append-only lesson home.
- Git and GitHub Actions run ordinary configured checks. Prompted role/file
  restrictions are not engineered access controls. No controller, daemon or
  scheduled model loop is installed.

## Commands and evidence

From a worktree root, synchronize with `uv sync --locked --all-groups`. This
workstation uses `/Users/davidhoffman/.local/bin/uv`; CI installs pinned uv/Python.
[Environment setup](operations/environment.md) separates current checks from
historical incidents.

```sh
make preflight UV=/Users/davidhoffman/.local/bin/uv
make check UV=/Users/davidhoffman/.local/bin/uv
make verify UV=/Users/davidhoffman/.local/bin/uv
```

`make preflight` performs locked setup, interpreter/import and isolated build-tool
health checks; it replaces no full-check phase. `make check` runs locked sync,
Ruff lint/format and Pyright through shared quality targets. `make verify` is the
canonical full gate and preserves all 13 phases in order: `sync`, `coverage-clean`,
`lint`, `format`, `types`, `tests`, `coverage-combine`, `coverage-json`,
`coverage-html`, `coverage-report`, `wheel`, `wheel-import`, `audit`. Selected uv
executables remain quoted in Make recipes. Full sync prepares the authenticated
pinned ImageJ reader; interoperability checks require JDK 21.0.7 and accept
`SIMRECON_JAVA`. [Reader environment](operations/imagej-reader-environment.md)
records exact dependencies. Conversion/export itself requires no Java runtime.

Pytest runs under native statement/branch and subprocess coverage. Strict config
and markers remain; test policy rejects empty discovery, skips, expected failures,
unexpected passes and collection/internal errors. CI repeats the full suite
independently on Ubuntu 24.04 and macOS 15. Default submission mode is full-local
exact-candidate verification: any known check failure, missing required evidence
or unmet explicitly selected coverage target blocks submission, including draft
PRs and pushes to an open PR. Conditional CI-authoritative mode is not enabled;
its separate protection/check/head/base/artifact-version prerequisites remain
required and high-risk work is excluded. A legacy protection-endpoint absence
alone does not establish that native rulesets are absent.

[Verification evidence](operations/verification.md) describes ignored phase logs,
receipt/input identities and same-run evidence. Coverage JSON/HTML live in
`artifacts/coverage/`, receipts/logs in `artifacts/verification/`, the sole product
wheel in `dist/`, and the separate development wheel in
`artifacts/devtools/dist/`. The wheel phases build and check both distributions;
installed checks run outside the checkout with separate product/development
environments. The product environment has only runtime dependencies.
Prepare the task pointer before verification. Record final commit/tree,
command/environment/results outside verified tracked bytes and confirm they stay
unchanged. Passing requires a clean tracked start, unchanged candidate/input
identities and one valid wheel. Failed/partial checks cannot pass using stale
artifacts; output and evidence protection remain binding.

M25 is retained **MRC conversion** resource evidence, not retired reconstruction
measurement. `make verify` passes `--measurements-required`; the actual same-run
`test_m25_native_memory` subprocess exports baseline/peak/native units and its
byte increment to `artifacts/verification/measurements.json` under the fresh run
identity. The limit remains **33,554,432 bytes = 32 MiB**. Missing, stale, malformed
or over-limit mandatory evidence fails verification. Do not run M25 again solely
to retrieve numbers. The accepted strengthened fixture payload remains above its
historical memory high-water; retirement does not weaken its witness.

## Accepted fixed two-worker verification

The accepted delivery carry-forward uses development pins `pytest-xdist==3.8.0`
and `execnet==2.1.2` with their locked inputs. The top-level Make tests recipe is:

```sh
uv run --locked coverage run -m pytest -n 2 --dist=loadgroup --max-worker-restart=0
```

Exactly two workers run deterministic whole-file affinity groups assigned by the
measured `simrecon_devtools.pytest_policy` module. Every file outside the explicit
allowlist, including a new file, belongs to `serial-rest`; that group is internally
serial and can run alongside another group. CE01 removes affinity entries only
with their retired subjects under named infrastructure ownership. Historical
18-file/58-source counts describe the earlier qualification, not the neutral
candidate's inventory. Every current owned source still requires measurement.
No parallel flags enter shared pytest addopts, environment or nested fixture
commands, and automatic worker restart remains disabled. The omission guard,
case identities, strict config/markers and failure outcomes remain binding.

Accepted fast runner regressions and recorded one-time worker/native-shard
qualification retain their material-input limits. Changed dependencies, runner,
groups, policy, coverage, fixtures or environment require affected diagnosis and
requalification. Completed worker/child shards must survive real fixture
cleanup/combine paths; current JSON/HTML and same-run M25 remain required for
every full gate. No blanket coverage-environment stripping, pytest-cov substitute,
platform union or stale-report reuse is authorized. Two workers imply no elapsed
time claim. Provenance is commit `d62aa2e2e2bf95ebfaaf6d0b6476a323980fd722`,
retained in RA14 `0939754aaaf560ca554139d50084f9f0ccc296d8`, notably its `Makefile`
and `docs/tasks/test-suite-consolidation.md`; the
[ASD preservation contract](contracts/c-equivalence-asd-preservation-v1.md) owns
CE01 reconciliation. That source pin imports no RA scientific architecture.

## Coverage policy and adoption provenance

The [coverage-policy adoption task](tasks/asd-coverage-policy.md) records the
focused change from dstack PR #7, head
`94f8b856ae708d062fc6054adff9a9ce02af0614`, merged as
`f55af3b18eff1d43d4d0e89ea21ca688ffce1f5c`. This is a local amendment to the
Version 1.0 delivery package. No-default-caps, direct-request authorization,
role separation, blindness and full-local submission rules remain.

The owner selected “Switch percentages to advisory.” The project policy is
approved behavior coverage with independent risk review; no line, statement,
branch or combined percentage threshold is selected. Tasks inherit this choice
and identify high-risk paths. A/B and bounded reviewers independently audit
requirements/oracles; D checks concrete implementation omissions. A low percentage
alone neither reopens tests nor blocks acceptance. Measurement proves no complete
behavior coverage. Historical task-selected thresholds and accounting retain
their original scope; no unrelated task receives an implicit waiver.

Coverage.py measures executable source lines (called native statements here) and
possible line-to-line branch destinations. It supplies no separate language-level
statement instrument or distinct line target. Report exact covered/total integers
and unsupported measurements. Native statement/branch reports remain required
globally, per package (`src/simrecon/`, `scripts/`,
`devtools/src/simrecon_devtools/`) and per owned file, independently
on Ubuntu 24.04 and macOS 15, including never-imported files and relevant
subprocesses. No platform union supplies a platform's missing evidence.
`make verify` requires current JSON/HTML reports and internally consistent exact
file/package/global counts. Partial or zero execution is valid measurement;
missing files/reports, malformed/inconsistent counters and unsupported required
native measurement remain failures. No handwritten runtime exclusions are
approved. External dependencies and ignored study code are outside ownership.
Make, YAML, native dependency internals and model behavior have no owned-Python
coverage claim; their command paths require actual exercised evidence.
`fail_under = 0` removes percentage enforcement; receipt validation checks report
integrity rather than covered/total equality. The
[receipt amendment](contracts/verification-coverage-advisory-v1.md) preserves all
other full-check obligations. Earlier passing evidence proves no changed candidate.

Install generic Ruff hooks with
`uv run --locked pre-commit install --hook-type pre-commit --hook-type pre-push`.
NumPy-style docstring lint applies to runtime; tests/fixtures may omit
function/method docstrings. Hooks provide feedback and never replace full
verification. [Lint scope](tasks/numpy-docstring-lint.md) records setup.

## Role entry points and delivery continuity

Coordinators select impact/uncertainty in the authorized contract: mechanical
worker; bounded worker plus fresh reviewer; or fresh blind A/B, restricted C and
fresh D for high risk. Data-loss behavior, even conventional overwrite/truncation
repair, is high risk. Policy adoption has human-requested documentation scope and
fresh independent policy review before activation; restating a request needs no
extra approval checkpoint. Use [native role launches](operations/role-launches.md),
[public A/B packets](agentic-software-delivery-v1.0/templates/PUBLIC-PACKET.md),
[candidate packets](agentic-software-delivery-v1.0/templates/CANDIDATE-PACKET.md)
and [handoffs](agentic-software-delivery-v1.0/templates/HANDOFF.md).
[Model selection/calibration](operations/model-selection.md) records conservative
defaults, qualified scope and lower-cost/effort candidates still lacking evidence.
Advisors replace no required independent role. Launched roles do their work
directly without nested launches. Reviewers never inherit author history; context
reset restores no blindness. A/B follow their public-input allowlist rather than
implementation-bearing task/history/coverage/lesson links. Before blind probes,
arrange [source-free warnings, tracebacks and subprocess diagnostics](operations/role-launches.md)
that retain categories, messages, locations and failure status. Disclose exposure
and stop blind work for routing.

Installed doctor commands remain `uv run --locked delivery doctor --check`
(report only) and `uv run --locked delivery doctor` (bounded documentation patch
within named human-requested scope and fresh independent policy review before
activation). [Doctor scope](tasks/setup-doctor.md) and
[procedure](agentic-software-delivery-v1.0/DOCTOR-PROMPT.md) bind. No check authorizes
merge, release or external messaging.

The [test-audit adoption](tasks/asd-test-audit.md) preserves report-only discovery,
obligation-to-keeper mapping, routed corrections and fresh independent final
review under the [test-audit skill](../.agents/skills/test-audit/SKILL.md). Cleanup
uses the accepted [fixture/worktree procedure](operations/fixture-cleanup.md):
identify owned disposable scratch, close writers and preserve original data,
C source, durable evidence, active work and required environments/paths.
[CE01 ASD preservation](contracts/c-equivalence-asd-preservation-v1.md) retains all
accepted post-PR7 improvements, accepted consolidation and historical charges.
It authorizes no global pruner or scientific rollback of delivery infrastructure.

Historical deadlines, interviews, environment flags and attempts remain in
[setup accounting](tasks/setup-plan.md), [architecture intake](tasks/architecture-intake.md)
and linked evidence. Old quota records impose no new default cap. One Current
state records request/constraints/route/gate, exact candidate/checkpoint,
role/check evidence, classified blockers, next action and cumulative accounting.
Record actual human-set limits or “not set,” and missing measurements as unknown.
Preserve previous rounds, repairs, launches and spending. The
[no-allowances amendment](tasks/delivery-without-allowances.md#current-state),
[repository rollout](plans/agentic-delivery-repo-efficiency-plan.md) and
[generic policy history](plans/agentic-delivery-spec-efficiency-plan.md) retain
provenance. Profile before any optional cache/shard/launcher change.
