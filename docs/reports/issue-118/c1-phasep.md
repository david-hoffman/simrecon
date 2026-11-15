# PH118 C1 — unpublished provisional PhaseP implementation

## Scope and binding

Fresh restricted HIGH-RISK C1 implemented only completed acquisition preparation
and native positive-harmonic scratch lifetimes. This is an implementation and
ordinary-check report, not scientific acceptance, a final candidate receipt or
a measured process-peak claim. No product/test defect or unresolved requirement
was found in this provisional scope.

The clean launch was commit `87feeb5a93f4e2bcba73b3229329eb7ee115bf6e`, tree
`4650b31e10466101ab4e11a06247e6e218045ff9`, branch
`perf/118-preparation-harmonic-lifetimes`, worktree `/workspace/work/issue-118`.
The entire launch packet was read and its SHA256 verified as
`115b1635fb58668fc939260eea350a1755e32d00b43caee86630aefde10c2221`.
Launch src tree `cda612549559974ee4246dec40e049cd8ed158a5` exactly matched
public `64a752b4642709c539df2079cc3c906acf4cc7b8`. This is the actual
PROVISIONAL baseline, not accepted future117 or inherited113 profile qualification.

The exact accepted scheduling addendum SHA256
`b172e019edb8235d31380553068b706ad883516dfb6c49cc07de0be41241e653`
and its explicit application were read. The supplied joint review identity is
`0ad4312fdc9d8dc60551f06ac75dcfbd98bf008c68d51db416d9d8a18072e34c`;
this is one scheduling applicability event owned117, not another PH118 B/D.
It supersedes the parent117-before-ANY-C scheduling hold only for this PhaseP.
Scientific ownership, reviewed inputs and final gates remain binding.

Accepted B2 checkpoint is `badf155abbc2f345e013556be12fd2bc13107fd0`, tree
`6b1bd83d9cc56909eed40964f0bd39b85215f864`. Its report and accepted pointer
were read. Manifest SHA256 is
`90d5a02fcb5a83c1b6dae4ff047c37a452c36b9ab6f760915635d910f3eebb5f`.
Every entry passed `sha256sum -c` at entry. Initial owned-source hashes matched:

| File | Initial SHA256 |
| --- | --- |
| modes.py | `4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1` |
| known_parameters.py | `34fbc93aa5ac9a1f4eb24b1f39ce576a1bb7770238c62cab72412de120722295` |

AGENTS, `docs/PROJECT.md` and `.agents/skills/implement-work/SKILL.md` were read;
the latter was applied in HIGH-RISK C mode. Only packet-permitted current source,
public contracts, accepted checkpoint and frozen test inputs were consulted.
No history/private RM84/archive/lesson/coordinator implementation plan was read.
No delegation occurred. Requested model/effort was Sol/high through the supplied
fresh no-history tool route; actual serving identity/effort and usage costs are
unknown. Prompt restrictions and shared filesystem prove no engineered isolation;
separate optional memory/read-only/delegation controls were not exposed.

## Implementation and exact last-use reasoning

There are six added product lines: four `del` statements and two explanatory
comments, in the two owned files only. No numerical expression, allocation call,
loop range, branch condition, transform/backend, precision, public interface,
capture, validation or exception handler changed. No workspace reuse was added.

### Real on/off section frames

`on` is a newly allocated float64 `(P,Y,X)` section; `off` is either a newly
zeroed float64 section or None. Camera loads create independent corrected
frames and copy them into those arrays. Edge treatment and on/off equalization
finish before the existing lateral FFT calls. Sums and gains are values copied
into independent persistent histories; they are not frame views. Camera state
owns maps, alpha, the preceding-on extra scalar and sentinel indices, not on/off
arrays. The equalization helper returns None and its local references expire.

The final read of `on` is `np.fft.rfft2(on, axes=(-2,-1))`; release now follows
that successful call, before the off FFT. The final read of `off`, when present,
is its existing rfft2 call; release follows the existing conditional expression.
Deleting None in the no-off case is safe. The ordinary pinned FFT calls produce
complex transform storage independent of these real inputs. They are not in-place
transforms or retained closures. No frame view is stored in a record/event.

All prior camera, edge, sum and selected equalization checks remain in place.
The on transform, off transform, on finite check and off finite check remain in
their original order. Only completed real inputs die earlier. Both complex
results remain alive for those checks and all later within-drift/separation work.

### Per-z complex transforms

`on_fft` and `off_fft` remain alive through their existing finite checks,
within-2D reference/correlations and fitted or unfitted exposure correction,
linked phase design, separation and raw Nyquist copies. The reference
`(on_fft[0]+off_fft[0])[None]` owns the independent addition result; it is not a
view of either FFT. Correlation helpers finish synchronously and retain owned
diagnostic copies or compact scalar representations, not their FFT arguments.
Ramp and displacement locals do not own the spectra. There is no closure/default
argument/cache retaining these section arrays in the inspected call chain.

The last on-spectrum reads are the einsum and raw phase-slot Nyquist assignment;
the last off-spectrum reads are the corresponding off assignments. Assignments
copy values into the pre-existing independent `quadratures`/`off_q` arrays.
The unconditional release occurs after the existing optional off-combination
block, preserving that block's position. Combination reads the persistent output
arrays, repeatedly addresses plane0 and retains its required captures; it does
not consume the released spectra. `off_fft` is always assigned, including None.

The full-Z axial FFT still executes after every section has been separated and
stored. It operates on persistent quadratures, including raw Nyquist slots, and
never needs the section FFT arrays. Off quadratures still receive no axial FFT.
Between correction remains after the on axial transform. No camera map, prior-on
extra, independent equalization anchor, clock/header prefix, drift displacement,
last-z noise value, phase history, trace or off-plane0 state is released/reset.

### Native positive harmonic scratch

`plus` remains a fresh zero-initialized complex128 `(Z,Y,X)` array for every
side order; order zero retains None. Its final reads are the literal
recombination scalar loads `p=F(z,y,x)` and `n=conj(F(-z,-y,-x))`. Every required
recombination assignment completes before the new unconditional `del plus`.
Indexing produces NumPy complex scalar values; surviving `p`/`n` locals do not
own array views. Neither `filtered`, `original`, `_Filter`, transfer sampling,
mode events nor a closure receives a `plus` reference. Filtering writes scalar
results into its independent destination, never publishes the workspace.

Allocation of the next harmonic therefore cannot overlap a prior local `plus`
owner. Allocation frequency/churn is unchanged. There is no fill/reset/reuse
whose signed-zero or unvisited-cell semantics need a new premise: every future
side order still executes the same np.zeros. The inclusive self support, strict
other support, denominator accumulation, all-axis reflection, positive Nyquist
endpoint, zero writes and E/O recombination arithmetic are untouched.

For odd Y the literal omitted row and partial reflected writes still use the
same original copy. Y1 leaves both traversal/recombination loops empty; the
unused zero workspace is simply released. Order zero's None is safe to delete.
The final `_finite(filtered, "filtered quadrature result")` remains after all
orders; deleting scratch does not remove any result or diagnostic finite check.

### Captures, callers and exceptional paths

Full capture's `event` uses `owned` to check and independently copy arrays.
`_finish_owned` transfers only independently allocated final arrays after their
last writes; these are persistent outputs, not the removed section/scratch
locals. Phase rows/angles/noise and full off/drift snapshots remain untouched.
Compact capture still performs the existing extent/finite checks, then freezes
scalar values or records identities. The summary projector retains no source
object. The workflow event closure holds workflow trace/declaration values and
does not enclose the stage function's on/off/FFT/plus locals. Full composition
keeps all stage records; summary composition follows the unchanged projection
and omission paths. No required full snapshot is replaced by an identity.

Input copies, validation and result fields/mutability remain unchanged. Real,
read-only/strided callers and caller-modified valid bands/noise gain no ownership
requirement. Every numerical expression and copy retains its value/sign-bit
behavior. Passing exact snapshot/projection tests below is relational evidence;
the independent finite-transform/filter/closed witnesses remain distinct.

Each deletion is reached only after the relevant successful computation. If
camera/edge/equalization/FFT/design/correlation/filter/recombination/capture fails,
the existing handler and traceback operate as before; a later deletion is not
executed. Already completed buffers can be absent from later traceback locals,
which is intentional and not a public result. The t/d locals used by workflow
stage-context extraction remain intact. No try/finally/catch or evaluation order
was added. API-specific allocation/backend cause translation and interruption
remain unchanged; no partial result, fallback or speculative sample was added.

## Ordinary checks

The granted environment is the existing pinned campaign Docker Ubuntu24.04.5
container `simrecon-campaign-ubuntu`, issue118 `.venv`, lock SHA256
`222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b`.
Python test output identifies Linux/Python3.13.12, pytest9.1.1, pluggy1.6.0,
platformdirs4.12.2 and xdist3.8.0. Existing accepted pinned-environment health
evidence is reused; no sync/install/environment repair/probe was performed.
This is not new backend, package-version/wheel or future-profile qualification.

Every executable qualification command used the following exact prefix, then
the arguments in the table; all commands were sequential with no workers:

```sh
docker exec --user 1000:1000 -w /workspace/work/issue-118 -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin simrecon-campaign-ubuntu
```

Logs are unique under `c1-phasep-evidence/`. Host `tee` retained ordinary
source-free output with pipefail preserving failure status; the committed
source-free Python/pytest harness was unchanged.

| Log | Arguments after prefix | Status |
| --- | --- | --- |
| 01-ruff-check.log | `uv run --locked --no-sync ruff check src/simrecon/acquisition/modes.py src/simrecon/reconstruction/known_parameters.py` | exit0, all checks passed |
| 02-ruff-format.log | `uv run --locked --no-sync ruff format --check src/simrecon/acquisition/modes.py src/simrecon/reconstruction/known_parameters.py` | exit0, 2 files already formatted |
| 03-pyright.log | `uv run --locked --no-sync pyright src/simrecon/acquisition/modes.py src/simrecon/reconstruction/known_parameters.py` | exit0, 0 errors/warnings/informations |
| 04-owned-pytest.log | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_preparation_harmonic_lifetimes.py` | exit0, 28 passed in13.55s; all9 dependency controls intercepted/calls1 |
| 05-acquisition-keepers.log | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_c_acquisition_preparation.py tests/test_c_acquisition_drift.py tests/test_c_acquisition_fitted_drift.py` | exit0, 139 passed, 2 warnings in35.36s |
| 06-known-keepers.log | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_c_known_filter.py tests/test_c_known_assembly.py` | exit0, 69 passed in6.82s |
| 07-acquisition-filter-keepers.log | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_c_acquisition_filter.py` | exit0, 49 passed in41.15s |
| 08-summary-keepers.log | `uv run --locked --no-sync python scripts/source_free_check.py pytest -rP tests/test_reconstruction_summary.py::test_full_summary_exact_scientific_and_projection_matrix tests/test_reconstruction_summary.py::test_summary_external_failure_semantics tests/test_reconstruction_summary.py::test_discarded_regression_correlation_must_remain_finite` | exit0, 28 passed in110.25s |

The two retained warnings are `RuntimeWarning: invalid value encountered in
divide` at frozen observer `tests/c_acquisition_fixture.py:2563`, in the
selected-zero-divisor on/off examples. The fixture's NumPy ufunc evaluates the
independent model on these intentional zero-divisor inputs; the tests assert the
product's selected rejection and finite disabled/N1 positives. They are warnings,
not failed checks or evidence of a product failure. No warning suppression or
test/fixture repair was made. One initial static `cat PROJECT.md` attempt returned
exit1 because the instructed project document is `docs/PROJECT.md`; corrected by
reading that path, with no qualification/environment failure or scope expansion.

All eight granted qualification commands passed on the unchanged source pair;
the five pytest commands total313 passing examples. No timeout, check failure,
repair or suspension occurred. This is focused evidence, not a full-suite or
native-coverage claim. All command sessions completed; no C-owned process remains
in flight.

## Evidence limits and next barrier

Explicit local ownership ends earlier, reducing potential live-array overlap
with later section/harmonic allocations, later stages and result finishing.
This is static lifetime reasoning. It is NOT an observed process-peak or timing
benefit. Test runtimes above are test output, not speed comparisons. Backend
workspaces, allocator retention, caches and required full-debug outputs can
dominate RSS. Result payload is intentionally unchanged. No memory ceiling,
reduction percentage, latency ratio, 16GiB feasibility guarantee or profile
coverage is claimed. No adapter import/help/CLI/dry-run/benchmark/resource
execution, full gate, full native coverage/report, wheel/import/audit/M25 or D
was performed. Known launch/setsid and sampled/group RSS/post-sample JSON-tail
limits remain unresolved for future qualification.

PhaseI remains BLOCKED. Root must freeze ACTUAL ACCEPTED117 including113
profiles/shared helpers and the real material environment; integrate this
provisional source; reassess contracts/interfaces/source/tests/fixtures/oracles/
budgets/observers/profiles/helpers/versions/lock/tools/environment; renew affected
author/check evidence and obtain FRESH affected B BEFORE any integrated C
repair/continuation, resource qualification/execution, final measurement/full
gate/D/publication. Retained evidence needs explicit unchanged-material reasons.
Conflict/parent/version changes create a new candidate. These checks keep their
actual public64a provisional label. New meaning/outside ownership returns to root.

C1 is the first C launch, D0. All supplied intake/A/B failures, corrections,
launches and costs remain retained, including nonaccepted B1 and accepted B2.
No caps/budgets were human-set; actual serving/tokens/cache/money/total elapsed/
owner-wait/check cost metrics are unknown. No commit/rebase/integration/push/PR/
cleanup occurred. Own durable artifacts are this report and its evidence directory;
no scratch, fixture or resource process was created. Final channel is separate.

## Final identities and compliance

Final product SHA256s are:

| File | SHA256 |
| --- | --- |
| src/simrecon/acquisition/modes.py | `85b3655ed25ed3664b954271e31a9a491ff6326c792e816e3b232d9135f24178` |
| src/simrecon/reconstruction/known_parameters.py | `46de99f88782c8b96215d9699fcdd1fe9f1ed5edfabf2426416fc2ae1e0bd0fd` |

`git diff --check` passed. Product diff is exactly +4/-0 and +2/-0 lines.
Final `sha256sum -c docs/packets/issue-118-b2-inputs.sha256` passed every entry,
exit0, retained as `09-final-frozen-manifest.log`. The behavior test, adapter,
protocol and PH118 hashes remain respectively
`22bd0543da0c268b718e3ab1969411344996eddc1da9cd33b2ee60a27fc7ac08`,
`ece8f0c660be2dc1713d6eae1c1e73843912ad4621fe0fb147c099c64a0eea59`,
`2ce88a336d3fc45bd42f82f29ac9f15c5b2bb5a9c5061ee55d8457be49a135dc`,
`d217c186ae2e736fb6fbfe29a432b84d5e34e6490679a422835253742bbcf3e5`.
B2 report/accepted pointer/addendum/application/lock/packet also match supplied
identities; `10-final-identities.log` retains those checks and source hashes.

HEAD/tree remain the launch identity. The final worktree is intentionally dirty:
the two owned product changes and this report/evidence are uncommitted. Status
also shows coordinator changes in `docs/reports/issue-118/role-launches.md` and
`docs/tasks/preparation-harmonic-lifetimes.md`; this C did not edit either.
No reviewed test/fixture/adapter/protocol/contract/infrastructure/gate/dependency/
lock/helper byte was changed by C. No own acceptance or integrated qualification
is inferred from these passing provisional checks.
