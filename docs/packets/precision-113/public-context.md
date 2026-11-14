# SP113: permitted public preparation for blind A/B

**Version 1.0. NOT LAUNCH-READY.** This is source-free preparation, not an A/B
launch packet or accepted test checkpoint. No formal A may start until the
coordinator reconciles accepted 115 representation rules into the complete
public contract and replaces its pending paragraph. Accepted/frozen 116 is also
required before C. Before A the coordinator also freezes explicit scenario IDs/
subrows for every validation/mode/failure decision; the behavior-family source
inventory is not the final scenario ledger. Tests cannot choose missing meaning. The
coordinator authors the final actual PUBLIC-PACKET with exact identities,
requested role, write scope, diagnostic commands and resource grant.

## Public objective and interfaces

The authorized outcome is explicit opt-in stationary 3D known-parameter
reconstruction with genuine c64 filtering/FFT input-output/storage, f64 scalar
calculations/coordinates/image accumulation, f32 signed image and c64 filtered
diagnostics. The selected parameters are supplied, never fitted. The public
contract is `docs/contracts/single-known-reconstruction-v1.md`: its settled
signature, selection, record, rounding, validation, failure and provenance terms
are binding after the representation reconciliation. It requires
`declare_prepared_bands32`, PreparedBands32, KnownReconstruction32 and
`reconstruct_known(..., precision="single-mixed-v1")`. Default precision is
exactly `"double"`; all old calls/records retain exact same-environment behavior.
Only new bands work with single; only old supported bands work with double.
No workflow/summary precision entry or implicit adapter is authorized.

Independent fixtures declare every half-spectrum coefficient directly in slots
0,E1,O1,..., positive per-time noise and exact CE alpha units. Preparation is
unnecessary and may not supply expected arrays. Use existing valid complex128
transfers, preserving original empirical information until complete f64/c128
sampling/filter evaluation; round consumed scale once to c64. Preserve literal
CE04 native traversal/odd-Y/Y1 behavior, signed positive Nyquist, conjugate
reflection, unnormalized positive inverse and centered positive carrier phase.
Zero carrier, signed/zero/complex modulation, zero data/transfer, signed outputs
and finite subnormal/zero rounding are legitimate when required operations and
stencils are defined. No weak-signal floor, epsilon replacement, clipping or
final-array-only downcast supplies the mode.

The new result's exact fields/settings/provenance, empty mode_trace and source
identities are specified by the contract; public facade and typed return
selection must be checked alongside numerical behavior. Existing PreparedBands
and AcquisitionBands remain c128; no c64 masquerading in old records. Existing
extended options stay supported in double. Single requires default-equivalent
CE06 options exactly as listed in the public contract, and rejects all unsupported
modes explicitly even with zero data. ReconstructionError keeps code
`reconstruction-domain`, signature errors stay TypeError, causes survive, no
input mutation or partial result. Failure phase precedence is public behavior.

No preparation, estimation/search, native2D, fractional-zoom, workflow/summary,
half/disk/backend/size-domain expansion, default migration, numeric image-accuracy
requirement, fixed peak-memory ceiling, speed ratio or 16 GiB guarantee is selected.
Computational agreement is distinct from physical recovery or historical binary
agreement. Current runtime qualification and measurements are not supplied here.

## Whole-file public read allowlist and exclusions

The prospective actual packet may allow only these whole existing public files
(no link expansion), plus the exact tests/fixtures it names:

- `AGENTS.md`.
- A: `.agents/skills/test-work/SKILL.md`; B: `.agents/skills/review-work/SKILL.md` (use B mode only).
- `docs/contracts/single-known-reconstruction-v1.md`, after complete representation reconciliation.
- `docs/contracts/c-equivalence-known-parameters-v1.md` (CE04 finite equations/interfaces).
- `docs/contracts/c-equivalence-optical-transfer-v1.md` (CE03 accepted transfers and actual stencils).
- `docs/contracts/c-equivalence-preprocessing-v1.md` (CE02 existing record/normalization compatibility only).
- `docs/packets/precision-113/public-context.md` (this entire sanitized file).

These are whole-file permissions, not permissions for linked tasks/reports/source.
The final coordinator packet supplies its own whole public filename/digest and
exact A test/fixture/report filenames. B additionally gets exact A tests/fixtures,
their requirement mapping and sanitized evidence only. A may read/edit its named
new tests/fixture; B reads them and writes only its named report.

Explicitly EXCLUDE whole `docs/PROJECT.md` and whole
`.agents/skills/test-audit/SKILL.md`: relevant approved project facts and public
authoring questions are copied below instead. Also exclude implementation
(including every `src/` file and runtime introspection/source printing), source
archives, history/git show/log/blame/diffs of implementation, conversations,
nonblind task/Current state/intake report/handoffs, prototype scripts/raw study
reports/manifests, coverage maps, lessons/triage/dispositions and coordinator
nonblind discussions. The accepted numerical-method facts below stand alone;
no study-report access or linked material is needed. Do not follow links from
AGENTS, selected role skill or allowed contracts into excluded files. If a selected
skill points to test-audit, use only the questions copied here.

`source_free_check.py` and its inherited warning/traceback/subprocess renderer are
permitted **execution-only**, not internal reading: `scripts/source_free_check.py`
and its existing `scripts/source_free_sitecustomize/` support package. No source
imports/probes outside that renderer; no disabling inheritance with Python
-I/-S/-E or stripping its diagnostic environment in children. Allowed product
imports are public facade/declared defining-module interfaces through the renderer,
not implementation inspection. If diagnostics expose source through any unsupported
channel, disclose it and stop blind work for coordinator routing. Pytest --tb=no
alone is insufficient. Clearing context or a later clean run restores no blindness.

## Approved architecture, platform and verification facts

SIMrecon is a functional Python/NumPy/SciPy library with explicit array/value
boundaries. Owned runtime is `src/simrecon/`; owned verification tools are
`scripts/` and `devtools/src/simrecon_devtools/`. Retired scientific aliases remain
unavailable. Ignored C material is never copied/built/run/imported/linked. Public
source hashes identify the mathematical mapping, not a qualified historical
binary. Existing direct/full-debug/summary results keep their guarantees.

The pinned project interpreter is Python 3.13.12, uv 0.12.19 and `uv.lock` with
locked NumPy/SciPy. Root reports a successful isolated Ubuntu preflight with
CPython3.13.12/NumPy2.5.3/SciPy1.18.1 and ready per-worktree .venv; this is
environment evidence only, not a scientific/test grant. Reuse it only while
material interpreter/container/lock/environment inputs remain unchanged. No dependency/backend/configuration
change is authorized. Use the per-worktree environment. Required platform is
Ubuntu 24.04; the coordinator's granted resource window for this task must use
Ubuntu 24.04.5. Host Debian is not qualification and macOS is optional evidence.

The canonical full-local exact-candidate gate is `make verify` with all 13 phases:
sync, coverage-clean, lint, format, types, tests, coverage-combine, coverage-json,
coverage-html, coverage-report, wheel, wheel-import, audit. It includes locked
setup, both wheels/installed imports, audit, strict discovery/outcomes and exactly
two workers via `pytest -n 2 --dist=loadgroup --max-worker-restart=0`. No empty
collection, skips, expected failures, unexpected passes, collection/internal
errors or omitted required evidence can pass. New files stay in the inherited
serial-rest whole-file affinity group; no config changes or new xdist grouping.
Same-run M25 **MRC conversion** increment <=33,554,432 bytes remains an independent
mandatory gate; it is not a reconstruction memory promise. Do not rerun solely
to retrieve missing values. Full verification belongs to nonblind candidate work,
not blind source-revealing exploration.

Passing full-local evidence for the exact unchanged candidate is required before
PR submission/push to an open PR and before fresh D. No CI-authoritative exception
is active. CI repeats configured Ubuntu checks. Missing artifact/report/native
measurement, stale evidence, known failure or changed material inputs remain
blocking; a timeout is incomplete evidence. Final hashes/results live outside
verified tracked bytes. This public preparation conveys no publication/merge/
release/external-message authority and does not change gates.

## Inherited coverage and public audit-authoring questions

The approved policy is behavior coverage with independent risk review. No line,
statement, branch or combined percentage threshold is selected. Percentages are
advisory; measurement integrity/report completeness remain binding. Coverage.py
measures executable source lines (native statements) and line-to-line branches;
it does not provide a distinct language-level statement instrument. Required
Ubuntu reports include exact covered/total native integers globally, per package
and per owned file across all three roots, including never-imported files and
relevant subprocesses, with current consistent JSON/HTML. External dependencies
and ignored study code are outside ownership; no handwritten runtime exclusions
are authorized. Unsupported metrics and missing required reports are disclosed.
A bare uncovered branch supplies no new meaning or automatic test commission.

For every test/assertion A answers, and B independently challenges:

- What approved public obligation does it observe, and what credible wrong result would it detect?
- What is the strongest existing permitted public-boundary proof, and what distinct gap remains?
- Does it use a real caller/public interface with independent expected values, rather than a test-only production seam or internal state?
- Are units, normalization, selection/profile, signed outputs, errors and allowed positives covered without invented restrictions?
- Does an observer/parser/fixture/serializer/envelope create shared assumptions or vacuous success? Which requirement/test dependents change with it?
- If an assertion is removed/consolidated under later authority, which retained assertion keeps every obligation and legitimate positive/error case?
- Is intended valid pre-fix failure actually observed? Otherwise record unavailable baseline or initially passing evidence; do not manufacture red or require mutation testing.

A supplies requirement/scenario/example mapping and a short risk disposition.
B recalculates oracles and audits omissions and legitimate alternatives before
accepting the exact test/fixture checkpoint. Coverage corrections require a
classified missing approved outcome or concrete reachable risk with public
reproduction and why current tests miss it; new meaning returns to intake,
implementation simplification to its owner, measurement defect to infrastructure.
Classification grants no new edits. Shared fixture/oracle/serializer/tolerance/
expectation changes expand fresh B review, and B alone decides retained evidence
applicability. Post-implementation additions are supplemental, not recreated
original test-first evidence. No numeric scenario/review/repair cap is selected.

## Independent mathematical acceptance requirements

For each witness declare exact data x0, specified represented input x32 and
finite mathematical procedure F before candidate trials. Keep input
representation F(x32)-F(x0), candidate arithmetic candidate(x32)-F(x32), double
reference arithmetic double(x32)-F(x32), and end-to-end mode difference separate.
The last comparison is compatibility evidence only. Undefined F has no invented
reference. Directly specify every coefficient and slot, positive rational
v[t,d,m], CE alpha, transfer nodes/metadata, carrier and modulation, and freeze
formulas/constants/input hashes before observing candidate results.

Use independent rational sparse Fourier algebra/direct DFT, exact roots of unity
where possible (length 2/4), otherwise outward enclosures of sine/cosine with
analytic series tails. Standard-library Decimal or already-locked adequate
precision may be used after grant. Doubling precision from 80 to 160 digits alone
is a stability observation, not certification. No product preparation/filter/
assembly helper or downcast of product output supplies an oracle. Include nonunit
complex radial/full transfer and accepted c128 source values not c64-exact, not
only unit/real transfer controls.

Freeze the public scalar order and enclose binary64 self/eligible-other powers,
ordered denominator, division/taper/modulation and complete consumed scale.
At each finite operation use a justified local rounding interval; division
requires denominator excluding zero. Enclose once-rounded c64 consumed scale
separately from source interpolation and binary64 arithmetic. For componentwise
normal c64 complex products, gamma(3,u32)*sum(abs(real products)) can bound the
two products plus addition; add conversion errors separately. u32=2^-24,
u64=2^-53 and gamma(n,u)=n*u/(1-n*u) apply only with n*u<1 and their finite-normal
operation assumptions. Subnormal contributions use absolute half-spacing
(e.g. 2^-150 for binary32), and possible overflow must be detected. Enclose actual
candidate p and reflected n independently, then (p+n)/2 and (p-n)/(2i); the oracle
must never supply the candidate's n.

A/B must derive a justified **fixture-specific FFT envelope** before accepting
accuracy for a new FFT witness. Independently enclose tiny DFT roots/sums and
preserve axes/sign/normalization/Nyquist semantics. No observed maximum, double/
single agreement, generic gamma(N,u), or undocumented backend multiplier proves
FFT accuracy. Missing FFT qualification remains an explicit blocking gap in the
intended claim; output dtype proves no internal precision/workspace. Constant DC
and exact cancellation can have a separately justified zero-error transform,
without asserting general FFT exactness.

Propagate reference/scale/local/phase/FFT errors with absolute signed assembly
weights. For K f64 additions, add gamma(K,u64)*sum(abs(actual terms)) only under
its valid assumptions plus absolute subnormal error. Add final f64-to-f32 local
half-ulp or finite bound u32*abs(accumulator)+2^-150 separately. Preserve negative
and near-zero values. Report max absolute/RMS error, reference width, interval
distance and far-endpoint upper bound, signed extrema and error relative to an
explicit nonzero signal scale. Cancellation condition is sum(abs(terms)) divided
by abs(exact signed sum), infinite at zero; no per-pixel relative-error masking.
Phase error is undefined at zero amplitude. Physical/model/noise accuracy is a
distinct unknown, with no new owner threshold.

For discrete comparisons enclose both sides: strict a>b is certified true only
if lower(a)>upper(b), false if upper(a)<=lower(b); overlapping intervals are
unresolved, never pass. Exact analytic ties retain the public strict/equality
rule, no epsilon tie. Apply the correct inclusive self/strict other support,
cutoff rounding and actual-stencil decisions. Include unsafe zero-weight vertices
and no-partial/no-mutation failures paired with legitimate zero/sign/endpoint
positives. Finite tiny/zero values need no arbitrary energy floor.

A concrete analytic starting witness is DC-only with w=1/2, v=1, unit transfer
and modulation1: exact denominator13/4, scale4/13, center1 and side-1/2 give
exact cancellation. Let s64=RN64(4/13), s32=RN32(s64), p0=s32,p1=-s32/2;
p0+2*p1=0 supplies a correlated zero-error constant-transform witness. For side
-(1-2^-20)/2, reference is 4/(13*2^20), cancellation condition2097151. An a priori
pre-final bound is
`(2^-55+2^-26)*(1+2*(1-2^-20)/2)+2*2^-27`, plus any declared nonzero FFT term
and final local half-ulp. This follows known coefficient/scalar bins, never a
candidate-observed discrepancy. These examples supplement required addressing,
untouched-row, Nyquist, complex transfer, time-noise and nontrivial DFT coverage;
they do not qualify missing scenarios by themselves.

## Tools, checks, route and accounting for the eventual packet

**Execution remains held.** No install, Python, import/probe, test, lint/type,
benchmark or measurement until the coordinator grants the pinned environment/
resource window. The shared-resource grant must come from root; the issue
coordinator may relay that grant but cannot invent one. Shell permitted-file reads/search and named edits are
not an environment grant. No A now; the coordinator supplies the complete public
contract and actual packet only after representation reconciliation.

After grant, the eventual packet may name the following existing source-free
forms, with the exact six owned test/fixture files listed explicitly. These
are planned commands, not an authorization to execute during preparation:

```sh
uv run --locked --no-sync python scripts/source_free_check.py pytest -q tests/test_single_known_boundary.py tests/test_single_known_filter.py tests/test_single_known_assembly.py tests/test_single_known_precision.py tests/test_single_known_typing.py
uv run --locked --no-sync python scripts/source_free_check.py python -m ruff check --output-format concise tests/single_known_fixture.py tests/test_single_known_boundary.py tests/test_single_known_filter.py tests/test_single_known_assembly.py tests/test_single_known_precision.py tests/test_single_known_typing.py
uv run --locked --no-sync python scripts/source_free_check.py python -m ruff format --check tests/single_known_fixture.py tests/test_single_known_boundary.py tests/test_single_known_filter.py tests/test_single_known_assembly.py tests/test_single_known_precision.py tests/test_single_known_typing.py
uv run --locked --no-sync python scripts/source_free_check.py python -m pyright --outputjson tests/single_known_fixture.py tests/test_single_known_boundary.py tests/test_single_known_filter.py tests/test_single_known_assembly.py tests/test_single_known_precision.py tests/test_single_known_typing.py
```

These forms use the root-prepared environment with `--no-sync`, so a later
test-only grant does not authorize environment synchronization/installation.
The final packet supplies root's selected container/executable prefix and exact
commands. The suite above has five test files plus one shared fixture, not a coverage cap.
A/B may create no extra probes outside named tests/fixture without a coordinator
packet update. The renderer preserves categories/messages/locations/status and
subprocess inheritance while suppressing source snippets/locals; no broad
source-revealing checks, coverage inspection or product introspection. Public
entry absence is absence, not an observed numerical product failure. Stop on
missing required tool/capability; classify environment/tooling, test defect,
product defect or unresolved meaning before scoped correction.

High-risk route is fresh blind A → fresh blind B → frozen tests → fresh restricted
C → exact full Ubuntu gate → fresh D. D also assesses separate actual execution
evidence: three matched fresh processes per mode/case with identical coefficient
values/declarations/setup protocol, retained original/source arrays, all failures,
actual c64 FFT/padded/product transitions, peak/pre-call-high-water/native RSS,
retained bytes and runtime. Setup must not contaminate whole-process peak
asymmetrically without disclosure. A public result dtype alone proves no execution
path or backend workspace. Backend internals remain unknown unless identified.
Measurements are coordinator-controlled nonblind work under exclusive resource
window and do not give C test/gate ownership. No arbitrary memory/speed requirement.

Requested A/B/C/D model is gpt-6.1-sol/high, conservative for numerical/custom
oracles; broader quality equivalence is unmeasured. Actual served attribution/
metering may be unknown. Diagnose a concrete reasoning limitation before scoped
coordinator escalation; new meaning returns to intake. Fresh tool route is
eligible under independently accepted CLOUD107 policy b84b178/integration
be8e447. Every role is a fresh no-conversation-inheritance session; no nested
delegation. Optional separate memory-disable/read-only/delegation controls are
unavailable in the exposed route; shared filesystem/permissions and prompt
allowlists are limitations, not engineered isolation. Coordinator records packet
digest/absolute worktree/base/checkpoint, task/session ID, actual tool arguments,
separate report/final-message destinations and completion/verdict artifacts.
A/B do not follow nonblind policy evidence links or need native credentials for
the supported tool-only route.

Every launch/failure/diagnosis/review/repair and cost is cumulative. A model swap,
new session/checkpoint or corrected public packet erases none. Actual human
numeric limits are not set; the explicit execution hold and prerequisite schedule
bind. Missing input/cached/output tokens, served model, money, elapsed/check/wait
time are unknown, never zero. The final actual packet supplies sanitized cumulative
counters and exact accepted checkpoint or none. Fresh B correction verdicts
remain required; continuing A is allowed only while its blindness/scope hold.
