# FA120: qualify one lower-memory Fourier assembly strategy

**Version 1.0. Design-study contract; no runtime change is activated.**
[Issue #120](https://github.com/david-hoffman/simrecon/issues/120) commissions a
finite assembly-kernel investigation and one implementation handoff, or an
evidence-backed no-go. The [task](../tasks/fourier-assembly-design.md) owns
the sole Current state. This intake records the experiment; it reports no result.

## Authority, dependency and candidate

The campaign owner explicitly authorized issues #112–#120, their actual intake,
scoped studies, verification, independent acceptance and root-owned stacked PRs.
The operative issue body supplied at `/workspace/work/campaign/issue-120.md`
is authoritative. No private RM84 evidence or ancestry is used.

Execution waits for independently accepted #116 and the affected working-set
refresh after #117/#118 with required independent review. Root then binds this
study to its actual accepted #119 publication parent. Intake checkout
`ace06c861b974b6251a092567c253ae4eb0f56c8` is provisional accepted #115;
it establishes neither #116 acceptance nor applicability of memory evidence.
The root-applied stack is main → #112 → #115 → #116 → #117 → #118 → #119 →
#120 → #113 → #114. #113 is optional scientific reuse, absent from this baseline;
the initial assessment is existing double precision only. Its pending work is
not evidence or authority for this study.

The single primary strategy to qualify is **a destructive inverse of the
disposable padded spectrum on the existing pinned SciPy FFT interface**, using
its input-overwrite capability only if actual supported behavior warrants it.
No persistent reusable padding is proposed. A retained-padding negative control
may expose a longer lifetime and a higher peak. It is evidence, not a second
implementation recommendation. A no-go is valid if the overwrite capability is
absent, changes exact results, or supplies no supported saving at the relevant
peak. Inspect phase-expression temporaries and last uses to explain the live
floor; do not silently replace their arithmetic to improve the candidate.

## Preserved mathematical and compatibility boundary

Expectation sources are active
[CE04](c-equivalence-known-parameters-v1.md#zero-padding-inverse-scale-and-real-assembly),
[CE06 §9.2](c-equivalence-acquisition-modes-v1.md),
[RM84](reconstruction-memory-v1.md), and
[wide allocation](wide-allocation-domain-v1.md), as present at the frozen parent.
The study must check their exact revisions after integration. Preserve:

- Full enlarged-grid positive-exponential inverse sum, with `norm="forward"`
  leaving the inverse unnormalized and retaining the upstream preparation scale.
- Native integer embedding, conjugate partners and positive native Nyquist
  without splitting or coordinate-induced shifts.
- Native 2D: transform plane zero only, including axial enlargement; all later
  output planes stay initialized zero. 3D uses the full inverse.
- Center contribution `Re(u)` and side contribution
  `2*Re(u*exp(+2*pi*i*explode*m*(kx*x+ky*y)))`, with coordinates in micrometres
  and carriers in cycles per micrometre. Preserve signed, zero, fractional and
  negative explode where finite; no clipping, absolute value or gain fit.
- Time/direction/order traversal, omit-center selection, phase evaluation and
  signed accumulation order. Preserve the finite checks and whole-call failure
  boundary; no caller mutation, partial result or expanded rejection domain.
- Existing float64/complex128 storage, public schemas and summary/full-debug
  compatibility. A pure lifetime change must retain exact same-environment
  results, including signed-zero bits where observed. Backend/algorithm/order
  changes and new precision profiles require a separate scientific contract.

## Observed source facts and unresolved capability

At the provisional checkout, `assemble_signed_image` in
`src/simrecon/reconstruction/known_parameters.py` creates `image`, then per
time/direction/order creates `padded`, checks it, calls the imported SciPy
`ifftn`, deletes `padded`, checks `spatial`, accumulates, checks the image and
deletes `spatial`. The 2D branch additionally creates `zeros_like(padded)` and
assigns the inverse of plane zero. Side orders create a lateral real `phase`,
an imaginary phase expression, exponential, complex product and scaled real
contribution. Python reachability, array bases/views and backend allocation
intervals must be checked; syntactic last use alone is no memory measurement.

`uv.lock` pins the dependencies, not the resolved backend internals or workspace
size. At intake no installed interface signature, documentation, allocator,
destruction/sharing behavior, native thread count or internal precision has been
probed. These remain **unknown**. An overwrite keyword is a permission/hint to
verify, not proof of in-place execution or zero workspace. Same output pointer
or `shares_memory` is not proof that no temporary was allocated. Output dtype
is not proof of internal arithmetic precision. Distinguish supported documented
capability, observed ownership, native allocation evidence and measurement limits.

## Finite evidence protocol after root authorization to execute

Freeze a manifest before trials: actual parent/candidate/tree, source/contract/
lock/script hashes, Ubuntu identity, Python/NumPy/SciPy and resolved FFT backend,
thread settings, input hashes/shapes/dtypes/layouts, exact commands and the
root-exclusive resource interval. Cheap environment/import/backend checks precede
dependent work. Do not install or alter shared environments under this packet.

1. Derive tiny independent finite inverse sums from explicit sparse Fourier
   coefficients, constants, displaced impulses and positive-Nyquist modes.
   Cover native 2D with axial enlargement and full 3D; side and center terms,
   negative signed output, cancellation, omit-center and multiple directions/
   orders. Use CE equations, not production helpers, for mathematical oracles.
   Keep analytic-oracle error distinct from the stronger bitwise lifetime check.
   No blanket numerical tolerance is introduced.
2. Reproduce the existing kernel and the one overwrite prototype in report-only
   artifacts, without replacing product code. Compare shape/dtype and complete
   result bytes for each finite witness in the same pinned environment; retain
   mismatches, signed zeros, nonfinite or raised failures. Preserve before/after
   caller-input hashes, view/base/ownership observations and finite/failure
   ordering. A fixture must be constructible through the permitted public record
   domain; include a small public `reconstruct_known` compatibility witness so
   a local prototype cannot redefine the actual workload.
3. Freeze one small and one medium public-compatible shape, chosen after the
   accepted #116 peak and available headroom are known. These names describe
   measured workload sizes, not a claim about full-volume feasibility. Include
   a multi-harmonic run to expose retained buffers at the next iteration.
   Run baseline/prototype/retained-padding control as separate fresh processes,
   at least three repetitions per workload/variant, with matched inputs,
   environment, thread settings, setup, timer boundaries and monitor. Alternate
   variant order. Repetition count is a protocol choice, not a human budget cap.
4. Report absolute native process high-water memory in bytes with native units
   retained, pre-operation current resident memory where available, monitored
   operation peak, and wall latency from the same child. State whether setup is
   included. Subtracting two process high-water marks is not an operation peak.
   Report every repeat, range and median; monitor sampling interval, baseline
   high-water contamination, native allocator/copy visibility, thread/workspace
   limits and failed/incomplete rows. No monitor failure becomes an accepted row.
5. Account for actual live intervals of filtered inputs, output image, full
   complex padding, inverse, 2D zero volume, lateral phase, exponential, product,
   real views/scaling and any backend workspace. Give dtype/shape/itemsize bytes
   separately from measured resident memory. Explain overlap across iterations
   and which arrays outlive their syntactic last use. Match the #116 affected
   peak; a smaller isolated kernel peak alone is no workflow-saving claim.

Keep arithmetic/ownership experiments separate from matched measurement children
when instrumentation would alter allocations. Store raw manifests and results,
including negative findings, under `docs/reports/lower-memory-fourier-assembly/`.
Study scripts are finite report artifacts, not shipped runtime or product tests.

## Decision and handoff

Recommend this one bounded destructive-inverse implementation only if exact
compatibility, supported backend behavior and relevant repeat measurements support
it. Name exact product edit boundaries, dependencies/API change (including none),
expected live-set reduction and observed latency/variation, failure behavior and
independent future oracles. A statistical or memory threshold is not invented;
state what the finite evidence establishes and leave ambiguous benefit unresolved.
Otherwise issue one justified no-go for this strategy, identifying the measured
floor and the precise reason. No silent substitution of a different algorithm.

If evidence shows an out-of-core inverse is required, identify one exact future
algorithm and specify its full-grid equivalence obligations, storage/residency
bound, I/O schedule and volume, failure/cleanup/ownership and API requirements
for a separate contract. Do not implement it. Independent spatial tiles and a
memmap alone establish neither equivalence nor bounded memory. Unmeasured full
volumes and the 16 GiB workstation objective remain explicitly unqualified.

A fresh independent scientific reviewer must challenge equations, ownership,
equivalence, precision/workspace limits, matched-process claim and recommendation.
Report-only scope uses no fabricated product-red tests or A/B/C/D checkpoint.
Any subsequent product implementation requires its own fresh high-risk A/B/C/D
route. Final exact-parent clean Ubuntu `make verify`, required review and root
publication rules remain binding for this design PR.
