# HP114: half-storage and half-compute feasibility

**Version 1.0. Study contract; no product precision mode is authorized.**
The authority is [issue #114](https://github.com/david-hoffman/simrecon/issues/114),
retained locally at `/workspace/work/campaign/issue-114.md`. The one-task outcome
is a completed finite study, a supported/unsupported matrix, and one bounded next
implementation recommendation or an evidence-backed negative result. There is no
selected numerical tolerance, process-memory ceiling or latency ratio. A 16 GiB
workstation is an objective to evaluate with caller and operating-system headroom,
not a promised result. [The task](../tasks/half-precision-study.md) owns execution
state and accounting. This contract changes no existing scientific semantics.

## 1. Starting evidence and interpretation

Baseline public main is `b344e41a8b52de76d7cbbf8450319893904c3b8f`.
The issue reports pinned NumPy 2.5.3 rejects `dtype("complex32")`, float16 occupies
2 bytes and complex64 8 bytes, and tiny NumPy/SciPy transforms promoted float16
to complex64 / inverse-real float32; SciPy 1.18.1's helper promoted half to single.
These are inherited observations, not HP114 reruns, full-pipeline measurements,
or proof of native-half transform arithmetic. Actual environment versions and
transform routes must be recorded when execution is granted.

Source inspection on the baseline establishes:

- [Preparation](../../src/simrecon/acquisition/preparation.py) accepts float16/32/64
  arrays at `_array_metadata` and copies them to float64 at `_array`. Input dtype
  acceptance is distinct from quantization quality, workspace dtype and compute.
- [Acquisition](../../src/simrecon/acquisition/modes.py) uses float64 camera frames,
  frame sums and the scale `alpha = 1/(X*Y*Z*L**2*A*D)`; quadratures are complex128.
  Counts, background subtraction and normalization can expose different ranges.
- Preparation phase inverses use inverse/QR/solve and a binary64 residual envelope.
  A half-storage experiment must not silently replace that acceptance criterion.
- [Parameter estimation](../../src/simrecon/reconstruction/parameter_estimation.py)
  uses squared energies, complex cross sums, ratios, ordered maxima, strict
  improvement and three-point fits. Error can change a branch before image error
  becomes conspicuous. Equal-energy singularities remain explicit failures.
- [Assembly](../../src/simrecon/reconstruction/known_parameters.py) uses an
  unnormalized inverse (`norm="forward"`), wider phases and signed float64
  accumulation. Small normalized inputs do not bound inverse-transform range.

The [memory contract](reconstruction-memory-v1.md) preserves float64/complex128,
scientific order and full-debug/summary compatibility. HP114 studies alternatives;
it does not weaken that boundary. The accepted public #112 evidence may be reused
only when supplied by the coordinator with exact identities and applicability.
Private RM84 ancestry, retained C execution and retired APIs are excluded.

## 2. Representation and compatibility boundaries

Report three separate strategies; no strategy's result establishes another:

| Strategy | What is evaluated | Required qualification |
| --- | --- | --- |
| H1: half input storage | Caller holds float16 real samples; existing public entry promotes for existing wider work | Count caller original, packed input and promoted copy whenever simultaneously live; compare same quantized values promoted to wider input separately from unquantized values |
| H2: half intermediate storage, wider compute | Pack selected real arrays or real/imaginary components, unpack into float64/complex128 for a specified operation | Explicit storage site, conversion location and lifetime; isolated snapshot replay is not an end-to-end product result |
| H3: genuine half transforms | Backend explicitly documents and demonstrates half transform arithmetic for the exact shape/layout/device | Output dtype alone is insufficient; distinguish storage, multiplier, accumulator and workspace precision; unknown internal precision stays unknown |

Two float16 components may be stored in an explicit `(…,2)` real array or two
real arrays, with component order and byte order declared. This is a 4-byte
complex *storage encoding*, not a standard NumPy complex32 dtype or a transform
operand. Packing/unpacking may allocate a wider complex array plus real/imaginary
temporaries; a view, alias or in-place conversion is not assumed. Record actual
strides, alignment, copy ownership and peak simultaneous lifetimes. Real half
storage is 2 bytes/value; paired half is 4; the current real/complex working
representations are 8/16. These payload ratios are not RSS-saving predictions.

Use IEEE binary16 limits as explicit analytical anchors, verifying actual runtime
properties after release of the hold: maximum finite 65504, minimum positive
normal `2**-14`, minimum positive subnormal `2**-24`, round-to-nearest unit
roundoff `2**-11` near one. Declare actual conversion rounding, subnormal/flush
behavior and signed-zero behavior. Finite source values may overflow on casting;
nonzero values may become zero. Record these events before continuing rather
than clipping, renormalizing, hiding warnings or substituting successful output.
Power-of-two scaling is a separately labeled experiment, not a silent repair or
an authorized change to physical units or preparation/assembly normalization.

Keep reductions (frame sums, norms, energies and cross products), phase generation
and solves, carrier/refinement fits, transfer denominators/ratios, modulation
products and final signed accumulation wider by default in H2. Test the effect
of quantized operands even when accumulation is wider. Report separately any
site proven unsuitable and any site whose benefit remains unmeasured. No half
fit, lower condition cutoff, new regularization, arithmetic reassociation,
negative-value clipping, changed threshold or altered error precedence is adopted.

## 3. Finite representative matrix

Freeze one deterministic redistributable analytic generator, constants, phase and
transfer declarations, seeds if any, units and hashes **before candidate runs**.
Reuse a qualified public #112 generator if available; otherwise derive a small
multifrequency specimen and known phase/carrier witnesses independently. The
reference image is the existing signed count-unit mapping, not a normalized
photograph. Analytical Fourier coefficients and finite sums independently check
sign, scale and coordinates; existing-code agreement alone is not an oracle.
Baseline qualification must confirm intended successful/search/error branches.
A fixture that fails to express its intended case is a diagnosed study-fixture
problem, not evidence against half precision. Do not tune cases after results.

Default full-workflow rows use `(T,D,P,Z,Y,X)`, orders O3, lateral zoom L2, axial
zoom A1, declared complex transfer and uniform phases; W01 uses native 2D/O2/P3.
For each applicable row compare the same wider baseline, H1, and one-site-at-a-time
H2 packing at corrected frames, prepared quadratures, filtered quadratures and
embedded Fourier coefficients. Retain wider reductions/fits/phase/accumulation.
H2 sites unavailable through public stage composition may use isolated captured
snapshot replay with an explicit source/formula identity and limited claim; do
not monkeypatch product code or advertise a composed half pipeline. H3 is bounded
transform-only feasibility; no H3 full-workflow claim without actual evidence.

| ID | Declared workload or kernel | Distinct question |
| --- | --- | --- |
| W01 | `(1,1,3,1,16,16)`, supplied carriers, O2 | Native 2D signed image and H1 public-input path |
| W02 | `(1,3,5,4,16,16)`, supplied carriers | Native 3D stage storage and unnormalized assembly |
| W03 | W02 geometry, searched carriers and modulation | Ordered maxima, alias/refinement/fit/floor decisions and parameter error |
| W04 | `(2,3,5,4,16,16)`, search at time zero/reuse, later modulation changed | Reuse boundary versus per-time fitted quantities |
| W05 | `(1,3,5,4,32,32)`, supplied carriers | Spatial resource step against W02, varying only Y/X |
| W06 | W02 geometry, nonuniform full-rank phases, signed background-subtracted samples and near cancellation | Phase solve/residual, quantized inputs and signed output preservation |
| K01 | At most 4096 real/complex samples; values `0`, `-0`, `±2**-25`, `±2**-24`, `±2**-14`, `±1`, `±65504`, `±65520`, `±70000` | Representability, subnormal/zero loss, finite-to-infinite conversion and paired encoding |
| K02 | Small vectors scaled by alpha from W02/W05, plus alpha from source-valid metadata `(D,Z,Y,X,L,A)=(3,32,512,512,2,1)` without allocating that volume | Normalization underflow before wider transforms; metadata-only extrapolation clearly separated |
| K03 | Lengths 16 and 4096, constant/alternating complex operands; magnitudes `2**-12`, `1`, `256`, `1024` | Product/squared-energy/reduction overflow, cancellation and quantized-operand error with wider reduction |
| K04 | Tiny deterministic spectra and left-inverse/three-point-fit witnesses; equal/near-equal objectives, singular and paired nonsingular cases | Unnormalized inverse growth, phase conditioning, ties/strict improvement and failure/decision changes |

These ten rows are the finite study matrix, not a product support enumeration or
Cartesian product. K04 constants and formulas must be frozen with the manifest
before running; state exactly which contract branch each witnesses. Include
finite noncontiguous/read-only paired input examples in W01, and nonfinite input
plus unsupported shape/backend diagnostics as nonallocating boundary checks.
Do not turn deliberately singular or overflowing cases into successful runs.
No full-volume allocation, open-ended search, automatic growth series or new
hardware purchase is authorized. Failed or unsafe rows remain visible.

## 4. Numerical evidence and recommendation

For every completed comparison record stage dtype, shape, value range, nonfinite
counts, source-nonzero-to-zero counts, subnormal counts and quantization error.
For image/array comparisons report maximum absolute error in declared units,
RMS error and relative L2 error with an explicit zero-reference rule; retain signed
minima, negative-count and sign-change counts, signed zeros separately. Report
carrier error in cycles/um and Fourier bins; modulation complex absolute/relative
error, amplitude error and wrapped phase error in radians (undefined at zero).
Record noise/gain/phase-matrix error, inverse residual and condition diagnostics
without imposing a new admission cutoff. For all ordered discrete decisions
compare branch, maximum index/tie ordering, alias changes, walk/fit status,
floor/reuse/phase-replacement and finite/failure status. Preserve stage and
operation context and exception categories. Report unavailable metrics as unknown.

Separate (a) analytical/reference validity, (b) deviations from the existing wider
mapping, and (c) physical usefulness. This study supplies no new physical-recovery
certification. A numerical-acceptance **proposal** must be tied to the observed
matrix, units, precision/error analysis and intended future use, with exceptions
and decision policy stated. No guessed tolerance, zero-error demand for all half
experiments, fitted favorable cutoff or forced positive result is allowed. If
meaning cannot be justified, recommend no activation and name the missing evidence.

The final matrix must label each strategy/site/backend as demonstrated for named
cases, technically unavailable in the pinned environment, scientifically unsuitable
for a named case, unmeasured, or unresolved. Do not conflate unavailable hardware
with an algorithmic impossibility or a documentary claim with a benchmark.

## 5. Backends, resources and execution protocol

The pinned NumPy/SciPy CPU route is mandatory baseline. NVIDIA cuFFT Xt half
transforms are one named optional documentary feasibility candidate. Check current
vendor documentation for exact API/version, supported GPU architecture, transform
size/layout/stride, precision, workspace, GPU-memory and portability restrictions;
record CUDA/toolkit/driver and redistribution/licensing constraints. No GPU,
CUDA package, CuPy/PyTorch adapter, dependency change or accelerator is adopted or
installed here. If the provisioned environment cannot execute it, report runtime
and peak GPU memory unmeasured, identify required hardware and avoid a speed claim.
Any later backend experiment needs a coordinator-provisioned explicitly authorized
study environment and frozen protocol; absent that, documentary analysis suffices
only for a conditional feasibility statement. CPU promotion is not native half.

A hard root resource hold currently prohibits Python, imports/probes, setup,
installation, lint/types/tests, benchmarks and measurements. Source/manifest
preparation may proceed; no cheap preflight exception applies. After explicit
root grant use the pinned per-worktree `.venv` provisioned by root in Ubuntu
24.04.5 container `simrecon-campaign-ubuntu`; host Debian is not qualification.
Record exact interpreter, lock, NumPy/SciPy, transform implementation, CPU/GPU,
thread/allocator configuration and material environment values. Root schedules
numerical work; do not overlap another lane's exclusive window.

After granted cheap environment checks, run each comparison in a fresh process
with caller inputs retained and the same effective thread configuration. Use
three fresh repetitions for successful W01–W06 comparisons, reporting every run,
median and range. This is an experimental design, not a human-set limit. Kernels
need one deterministic numerical pass; time them only if timer resolution and
workload make the measurement meaningful, otherwise report it unresolved. Separate
cold/setup and call-only monotonic seconds; include pack/unpack in end-to-end time.
Report whole-process native peak RSS, Linux KiB-to-byte conversion, pre-call
high-water, raw peak bytes and retained reachable array payload with shared backing
counted once. Peak minus baseline is not an isolated call peak. Include generator,
hashes, caller originals, conversions, result and backend workspace in lifecycle
accounting; disclose allocator/Python metadata and unavailable workspace limits.
GPU evidence, if authorized, must include host RSS, device allocation/reservation,
workspace, transfer costs and synchronization; asynchronous dispatch is not elapsed
compute time.

Before each resource step, make a conservative simultaneous-buffer ledger using
wider workspaces, conversion temporaries and retained callers/results, compare with
current physical/available/cgroup limits and swap pressure, and record why headroom
is adequate. Unknown backend workspace prevents a confident large allocation.
Stop before unsafe allocation, record the skipped row/reason, and return to root;
never deliberately OOM, disable failures or treat a timeout as success. Record
16 GiB (`17,179,869,184` bytes) total-memory objective separately from measured
container limits and caller/OS/background reserves. There is no invented fixed
reserve percentage or numeric acceptance ceiling. Payload arithmetic or crop
extrapolation is not measured workstation feasibility. Preserve source integer
representation/stencil limits independently of RAM.

Completion requires reproducible evidence identities, all matrix dispositions,
independent scientific review and the exact full local gate under the task.
Recommend one bounded next slice with site/API, wider operations, expected benefit,
proposed acceptance evidence, exclusions and uncertainties, or a supported negative
outcome. Any future product precision/backend change returns to a separately
scoped high-risk intake and its appropriate fresh A/B/C/D route.
