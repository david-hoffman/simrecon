# RM84: lightweight reconstruction and measured memory use

**Version 1.0. Intake specification, not implemented capability.** The owner
requested `/intake 84` on 2026-11-13, then selected a new lightweight entry point
with existing APIs preserved, and measurement of reductions/the feasible envelope
without a fixed ceiling. [Task and execution status](../tasks/reconstruction-memory.md)
record that authority and the dependent delivery plan. This specification creates
no claim that the new entry exists or that the motivating volume is supported.

## 1. Scientific and compatibility boundary

Add `reconstruct_summary` returning `ReconstructionSummary`, exported from
`simrecon` and `simrecon.workflow.reconstruct`. Its arguments, defaults,
accepted input domain, configuration schemas and error class are exactly those
of `reconstruct_workflow` in [CE07](c-equivalence-workflow-v1.md). There is no
diagnostics selector, output filename, cache, disk destination or precision flag.
Calling existing `reconstruct_workflow` remains the explicit full-debug path.
No deprecation, default change or silent replacement of an existing record occurs.

Preserve existing `reconstruct_workflow`, direct stage APIs and record schemas,
including full ordered snapshots, repeated equal-valued overlap builds, trace
references, writable acquisition bands/noise and independent top-level/stage
images. New summary records are not accepted as existing stage input records.
Existing invalid-input categories and Python signature TypeErrors remain.

The new entry inherits the mathematical mapping, selected modes, validation,
units, thresholds, masks, source ordering, finite decisions and error semantics
of [CE02](c-equivalence-preprocessing-v1.md),
[CE03](c-equivalence-optical-transfer-v1.md),
[CE04](c-equivalence-known-parameters-v1.md),
[CE05](c-equivalence-carrier-modulation-v1.md),
[CE06](c-equivalence-acquisition-modes-v1.md) and CE07. Their public-call-count
and full-array-retention requirements continue to bind their existing entries;
the new entry may use internal operations without constructing those public
records. It must perform the same scientific operations in the same order.
No duplicate fit, raw replay, speculative unsafe transfer sample or changed
failure precedence is permitted. Independent time/direction staging cannot reset
camera state, equalization anchors, drift prepasses or time-zero carrier state.

Keep float64/complex128. On the same pinned environment, changing only retention,
ownership or buffer lifetime must preserve exact numerical values, including
signed zeros, and all discrete decisions. Baseline comparisons supplement the
independent contract-derived scientific oracle; neither mode-to-mode agreement
nor agreement with existing code alone establishes correctness. No relaxed
tolerance, changed FFT backend, arithmetic reassociation, reduced precision,
spatial tiling, approximate transform or changed optimizer is authorized.
Any proposed transform decomposition that cannot preserve these constraints
returns to intake before dependent tests or implementation.

## 2. Exact lightweight result

`ReconstructionSummary` is a frozen record with exactly the fields below.
Arrays are independently owned and read-only, do not alias caller storage or
one another, and retain the corresponding full result's values/dtypes/shapes.
Nested sequences and records are immutable. No lazy closure, cached stage,
array base, hidden record or other reachable object may retain discarded arrays.
Read-only/strided callers and mutation of caller buffers after return remain valid.

| Field | Meaning |
| --- | --- |
| image; x_um; y_um; z_um | CE07 signed float64 image `(T_eff,A*Z_eff,L*Y,L*X)` and independent physical coordinate vectors |
| intensity_unit; intensity_semantics | Exact CE07 strings, including caller count-unit label; no new mass/resolution claim |
| carriers_cyc_um | float64 `(T_eff,D,2)`, actual fitted, known or reused fundamental carriers |
| modulation; raw_modulation | complex128 `(T_eff,D,O-1)`, actual final and pre-floor/pre-phase factors |
| initial_carriers_cyc_um; phase_linkage_carriers_cyc_um | Separate CE07 float64 `(D,2)` guesses; neither replaces fitted carriers |
| effective_wiener | CE07 float64 `(T_eff,)`, actual full-series schedule |
| branches | CE05/06 immutable time-by-direction branch strings |
| input_identities | Complete CE07 lexicographically ordered input ArrayIdentity records, with the same pre-conversion content hashes |
| source_declarations; resolved_settings | CE07 ordered declarations/settings with the compact array projection below |
| preparation | Ordered compact projection of AcquisitionBands fields other than quadratures, off_quadratures and trace; includes actual noise, phases, separators, gains, displacements and timestamps |
| estimation | Ordered compact projection of EstimatedParameters fields other than overlaps and trace; scientific parameter arrays may be represented by identities here because their values are explicit top-level fields |
| filtering | Tuple in effective-time order of compact KnownReconstruction fields other than image, filtered_quadratures, x_um, y_um, z_um and mode_trace; includes actual cutoffs and resolved per-time settings |
| transfer | Compact OpticalTransfer fields, including the consumed samples' identity; never an OpticalTransfer record or a retained sample array |
| calibration | None on nonempirical paths; otherwise compact PreparedOtf fields, recursively including compact transfer, with actual calibration scalar metadata and array identities |
| layout | None on native path; otherwise compact TwoDPlaneInputs fields excluding images, off_exposures and exposure_background; source-direction/z mapping is represented by its identity |
| overlap_builds | Immutable descriptors defined below, preserving every build and index |
| search_trace; preparation_trace; filtering_trace | Compact events defined below, in original operation order; filtering_trace is a tuple of per-time event tuples |
| trace | Exact CE07 workflow event values/order; stage labels describe logical scientific stages, not a promise of public wrapper calls |
| diagnostics | Exact string `summary` |
| omitted_diagnostics | Exact tuple `("stage-images", "quadratures", "overlap-arrays", "correlation-arrays", "camera-maps", "transfer-samples", "calibration-arrays", "layout-pixels", "precise-query-events")` |
| source_revision; reference_sha256; limitations | Exact CE07 values, with no upgrade of historical-binary or physical-recovery qualifications |

Each compact record projection is concretely an immutable ordered tuple of
`(field_name, value)` pairs, not a dictionary, stage record or new record class.
Nested record projections use the same representation. Named settings/declarations
remain ordered `(key, value)` tuples; ordinary sequences remain tuples of values.
Access is by these named pairs, for example `dict(result.transfer)["samples"]`
is an ArrayIdentity, with `.name`, `.shape`, `.dtype` and `.sha256` attributes.
ArrayIdentity is a frozen value record with exactly those four fields and the
CE07 field types. Its concrete Python class need not be exported.

For compact projections, record fields follow the order in the referenced public
contract tables; configuration/event keys retain their defined order. Each numeric
array is replaced, regardless of size, by an immutable ArrayIdentity record with
fields `name`, `shape`, `dtype`, `sha256`, using CE07's contiguous little-endian
byte identity convention. Names start at the summary field and append `.field`,
`.key` or `.index` for each nested record, named pair/mapping or ordinary sequence
step. Named pairs traverse by their logical key, never by their tuple position:
an acquisition background map has name `resolved_settings.acquisition.background`,
and consumed transfer samples have name `transfer.samples`. An ordinary sequence
uses its zero-based decimal index. Projection
occurs before any array-to-list conversion: a camera map must not become a large
Python tuple. Non-array scalars and already-declared sequences retain their values
and types; metadata mapping keys remain sorted under CE07. Non-array metadata
can itself be large, so this is no constant-size metadata or total-memory promise.
Array identities expose provenance, not recoverable numeric array contents.

The projection boundary is the declared value at each public field. Stage
`resolved_settings` sequences that CE05/CE06 explicitly define as tuples remain
tuples: acquisition phases, phase steps and off-order selectors, and estimator
amplitude floors, for example. They are not converted back into arrays or hashed
based on the type of an earlier caller input. In contrast, summary's top-level
workflow `resolved_settings` and `source_declarations` project original array-valued
declarations before CE07's array-to-list snapshot conversion; those values become
ArrayIdentity records. Thus the same declared parameter can have an identity in
the workflow settings and an inherited scalar tuple in stage settings without
ambiguity or a hidden retained ndarray.

`overlap_builds` retains one frozen descriptor per actual build with exactly
index, time_index, direction_index, purpose, orders and carrier_cyc_um. The first
five fields retain CE05 meanings; carrier is an immutable pair of Python floats.
Indices still refer to positions in this tuple. Equal-valued repeated builds
remain distinct; no dangling index, equality-based deduplication or reference to
a nonexistent full overlap record is permitted.

Compact search events are frozen records with exactly `kind`, `time_index`,
`direction_index` and `details`, with the same scalar field types as CE05.
Preparation/filtering events are frozen records with the CE06 ModeEvent fields
and scalar types. Their concrete Python classes need not be exported. Details
remain ordered `(name, value)` tuples. Compact search events retain all CE05/06
kind/time/direction/detail keys except
`correlation_complex` and `correlation_power` in coarse events. Their small
arrays (carriers, neighbor samples, peaks) become immutable nested tuples of
Python scalars of the same values; all scalar fit/objective/bracket/parabola/
reuse/adjustment/cumulative-product decisions remain. Overlap references target
`overlap_builds`. Missing correlation arrays are declared by omitted_diagnostics,
not represented as fabricated zeros, None, or trace targets.

Compact preparation events retain CE06 event kinds/indices/order and detail keys
except these explicit spatial captures:

| Event | Omitted detail keys |
| --- | --- |
| between-build | centers, fourier |
| drift-correlation | cross_spectrum, correlation, absolute_correlation |
| exposure-correction; between-correction | phase_multiplier |
| off-combination | quadratures_after |

All remaining event arrays use immutable nested scalar tuples, preserving actual
phase designs, cubic fits, measured shifts, scalar off-combination diagnostics
and decisions. Filtering retains wiener-step and sector-boundaries events with
the same tuple conversion. Each maximal consecutive run of precise-query events
becomes one `precise-query-count` event with the same ModeEvent indices and
details `(("count", n),)`; split runs whenever any index changes. Its positive
Python integer n is the number of successful queries in that run. Numerical
query computations, finite/representation checks and failures still occur.

## 3. Computation, ownership and failure preservation

Summary operation must avoid building full histories and discarding them at
return. Keep live computational state, notably the frozen spatial overlap pair
through refinement; release it only after its last numerical use. Preserve all
finite checks, even for discarded correlation arrays, reverse regression,
precise queries and other numeric diagnostics. Diagnostic-only snapshots may be
omitted; omission of the underlying numerical operations/checks is not authorized.
Compute required identity hashes without retaining full additional snapshots.

Transfer an already private allocation into an owned result where appropriate;
never borrow writable caller memory or overwrite a published full-debug snapshot.
The caller may retain every input during the operation. No caller deletion,
garbage collection, environment setting or absence of concurrent unrelated
references is a precondition for correctness. Concurrent caller mutation during
an operation gains no new guarantee.

Complete input and structural validation precedes numerical work as in CE07.
Preserve signed32/unsigned32/native-intp limits and actual transfer-stencil checks,
including zero-weight vertices. MemoryError and interruption propagate; translated
backend/operation errors retain their cause and available stage/time/direction
context. Failure late in any time/direction yields no partial result/trace and
does not mutate inputs. Do not turn numerical failure into success by disabling
retention. Allocation-dependent success may differ because the new path needs
less memory; this does not waive numerical/representation failures.

## 4. Required scenario and qualification inventory

All currently supported CE07 domains remain supported; these representative
qualification rows are not a new restriction or a Cartesian-product claim.
Each scenario must map to an existing retained proof or new independently
reviewed public-entry proof. A identifies concrete omissions; B audits them.

| ID | Distinct obligation and qualifying examples |
| --- | --- |
| R01 | New entry/record/exports; unchanged old workflow and direct signatures, full records, field values, mutability, independent image/stage storage and duplicate build references |
| R02 | Exact summary fields/projections/availability, ordered build descriptors, valid search references, count-only precise-query runs and no hidden spatial retention |
| R03 | Exact image/coordinates/units/raw and final modulation/carriers/decisions; independently derived scientific witnesses and same-environment baseline comparisons |
| R04 | Searched 3D D3/P5/O3, T2 with reuse on and off; reused carrier with changed later-time modulation; supplied carriers including permitted zero/signed values where defined |
| R05 | Native 2D Z1, pair01 search/cumulative products, supplied/nonuniform reduced-order phases; A>1 zero extra planes and permitted dz0 coordinate behavior |
| R06 | Complex radial/full transfers; raw empirical, prepared empirical and decoded-section routes; preserve prepared non-complex64-exact values and reject insufficient/unsafe samples |
| R07 | Scalar/map/exposure background precedence, sentinel persistent camera changes, equalize-z/equalize-time anchors; N0 all-skip and N1/N2 selected off combinations including recurring plane0 effects |
| R08 | Qualified within/between drift and linked phases, ordinary 3D cubic with D>=4 and valid fit inputs; permitted fast D1 bypass versus unsafe fast combinations |
| R09 | Both literal-2D layouts with multiple effective times; native rectangular geometry, admissible fractional lateral zoom and nonunit axial zoom; physical units and indexing preserved |
| R10 | Cross-direction overlap filtering, suppress/dampen/omit settings, no/cosine/power/precise taper, exploded assembly and time-dependent Wiener schedule with original accumulation order |
| R11 | Caller preservation and post-return lifetime isolation; read-only/strided inputs and valid caller-mutated direct-stage bands/noise remain accepted |
| R12 | All inherited invalid declarations/selection/metadata/unsupported cases and paired valid alternatives; superseded invalid arrays still reject; no new rejection or error-priority rule |
| R13 | Source/native representation and actual safe/unsafe stencils; malformed extents rejected without full allocation; no memory-driven domain cap |
| R14 | Nonfinite discarded diagnostics, singular/undefined fits and late-time failure still reject; allocation/backend/interruption semantics and no partial results |
| R15 | Measured execution peak and retained-result reduction, spatial/direction/time scaling, exact identities and explicit unmeasured cases under section 5 |
| R16 | Usage/migration documents distinguish summary identity from full numeric data, in-memory full-debug costs, inherited scientific limits and measured envelope |

## 5. Resource experiment contract

Baseline is the checkout pinned in the task, not the historical issue crop.
Use deterministic redistributable synthetic public-entry inputs authored by A
and reviewed by B: analytic nonzero multifrequency specimen/phase data, explicit
optics and complex transfer declarations, positive and signed permitted cases.
Use existing approved analytical witnesses when applicable. Freeze generator,
all constants/formulas, declarations, expected results, shapes/dtypes and hashes
before candidate measurements; do not select a favorable case from candidate
results or treat physical truth as a fitting input. Baseline qualification must
show the searched cases actually complete the intended branches. An undefined
fixture is a test defect, not a product memory failure.

Use fresh single-workload processes for baseline full, candidate full and candidate
summary. Primary resource cases are native 3D P5/O3/L2/A1 with supplied and searched
carriers: `(T,D,Z,Y,X)` = `(1,3,8,32,32)`, `(1,3,8,64,64)`,
`(1,3,8,128,128)`, `(1,1,8,64,64)`, `(2,3,8,64,64)`,
`(4,3,8,64,64)`. The spatial series varies only Y/X; the direction/time comparisons
vary one dimension against the central case. Add native 2D Z1, drift and
off-exposure witnesses from R05/R07/R08 at their smallest meaningful dimensions.
These are experiments, never automatic routine-test full-volume allocations.

Run baseline and candidate on the same identified 64-bit host, locked Python,
NumPy/SciPy/FFT backend, allocator and thread configuration. Set the relevant
OMP/OpenBLAS/MKL/NumExpr thread controls to 1 and report effective backend/thread
information and unsupported controls. Required platform behavior verification
uses Ubuntu 24.04 under the owner-authorized
[current platform policy](../PROJECT.md#required-verification-platform); macOS
qualification is optional. Memory comparisons are per host, never pooled.
Record container/cgroup memory limits as well as host memory; this cloud host
does not stand in for the motivating workstation.

Measure whole-process peak RSS, including imports, caller-retained inputs,
generation, hashing, result and numerical/backend workspaces; no image export
or child numerical worker is in this experiment. Record native ru_maxrss and
conversion (Linux KiB times 1024; macOS bytes), baseline high-water before the
call, raw peak bytes and call-only monotonic elapsed seconds. Do not label
peak-minus-baseline as an isolated workflow peak. Record retained reachable
array payload bytes with shared backing counted once; separately report Python
metadata limitations. Capture input/output shapes/dtypes, commit/tree/dirty and
fixture/lock hashes, process/platform versions, physical/available/cgroup limits,
swap/page-fault context and actual disk use. Shared pages/allocator overhead are
included by process RSS accounting but not separately attributable; unavailable
swap or backend workspace measurements are explicitly unknown.

Use three fresh repetitions per declared comparison as an experimental design,
not a human-set execution/review cap. Report every run, range and median; retain
failures and explain noise. Acceptance requires lower retained payload and a
demonstrated execution-peak reduction on the largest feasible matched searched
case, with repeat variation disclosed. No fixed reduction percentage, absolute
ceiling, latency ratio or disk allowance is selected. If the reduction is not
distinguishable from variation, the resource claim remains unestablished and
requires diagnosis, not a success label. Report elapsed regressions without
silently changing numerical operations to meet a nonexistent speed target.

Larger trials require representation preflight and measured smaller cases plus
current available-memory/cgroup headroom. Stop growth before unsafe allocation;
do not deliberately OOM a baseline to manufacture failure. Report the largest
demonstrated case, the unevaluated next size and reason. The historical full target
`(1,3,5,32,2048,2048)`, L2/A1, is a feasibility reference, not an acceptance gate:
output `(1,32,4096,4096)` has 536,870,912 voxels and CE06's required
`8*Xo*Yo*Zo = 4,294,967,296 > 2**32-1`. It is outside the unchanged explicit
unsigned32 source-workspace domain, irrespective of RAM. Do not run it or relax
that check under RM84; supporting it needs a separately resolved domain change.
No crop scaling is a measured full-volume result or a 16 GiB guarantee.

## 6. Dependent slices and exclusions

RM84-1 establishes the frozen benchmark, summary interface/retention and full-debug
compatibility. RM84-2 follows an accepted RM84-1 baseline and removes redundant
private copies, aggregation temporaries and completed-stage lifetimes without
changing arithmetic. RM84-3 follows RM84-2 and investigates in-memory staged
preparation/filtering/assembly and reusable buffers, preserving all dependencies
and exact transforms. Its first outcome is a dependency/lifetime report; only
demonstrably equivalent changes within this contract proceed through A/B/C/D.
An impossible remaining working set is a reportable limitation, not permission
to add disk storage or alter science. Measurements accompany every accepted slice.

No disk-backed execution, persistent scratch arrays, selective capture API, new
file/CLI route, dependency/gate/policy change, precision reduction, domain
expansion, retained-C execution, retired Python resurrection or physical-recovery
claim is included. This intake authors no executable tests or runtime code.
