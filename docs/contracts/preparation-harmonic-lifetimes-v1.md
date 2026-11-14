# PH118: preparation and harmonic lifetime preservation

**Version 1.0.** Authorized scope is lifetime reduction with the existing public
scientific mapping preserved. This document is an acceptance contract, not a
claim of implementation, verification, baseline readiness or measured benefit.

## Authority, scope and non-goals

The owner authorized issue 118: shorten completed preparation phase/transform
and native harmonic scratch lifetimes. Preserve arithmetic and stage order,
finite checks and reached failure order, exact numerical values including signed
zeros, reflection and stored Nyquist behavior, camera state, equalization,
off-exposure and drift state, caller data, and complete independent full-debug
records. A reusable harmonic workspace, if chosen, must start each harmonic at
the exact required zeros and must have no published alias. This permits no new
backend, precision, representation domain, disk storage, stage fusion, general
streaming, output preallocation or public option.

The preservation sources are the approved
[CE02 preparation contract](c-equivalence-preprocessing-v1.md),
[CE04 known reconstruction contract](c-equivalence-known-parameters-v1.md),
[CE06 acquisition contract](c-equivalence-acquisition-modes-v1.md),
[CE07 workflow contract](c-equivalence-workflow-v1.md) and
[RM84 summary contract](reconstruction-memory-v1.md). Their declared units,
validation, numerical equations, record layouts and operation-time errors apply.
This contract changes none of them. Current Ubuntu-only qualification in
PROJECT supersedes historical mandatory macOS clauses. No historical C binary,
physical recovery or resolution claim follows.

## Public boundaries and expectations

Public signatures come from CE02's Public entry section, CE06 section 2 and
section 9 additions, CE04's Public boundary section, and CE07 section 2.
`reconstruct_summary` has exactly CE07's workflow arguments/defaults, as RM84
section 1 specifies. No signature is inferred from implementation.

Inputs remain explicit arrays/value declarations. Raw preparation axes are
`(T,D,P,Z,Y,X)` and off axes `(T,D,P,Z,N,Y,X)`. Sampling is micrometres,
phases radians, fundamental carriers cycles per micrometre, wavelength nm,
backgrounds detector counts, and drift detector pixels/native sections.
Keep the baseline default float64/complex128 computation and all source/native
representation limits. Actual inherited supported profiles must be reassessed
against the frozen parent and preserved; their nature is not assumed here.
Valid writable, read-only and strided inputs retain their existing domains.

On the same pinned environment, changing only lifetime/ownership preserves
exact values and signed zeros, all discrete decisions, metadata/hash identities,
ordered traces and full-debug snapshots. Same-environment baseline comparisons
supplement independently derived finite-transform/phase/filter expectations;
neither old-code agreement nor summary/full agreement alone is an oracle.
There is no new numerical tolerance. A may derive bounds for independent
mathematical witnesses from approved precision/conditioning information, recording
the derivation before product discrepancies; that does not relax exact
lifetime-only comparisons.

Structural validation stays before numerical work. Data-dependent finite checks
and failures occur when reached, with no speculative transform/sample, suppressed
diagnostic check, fallback or partial result. Existing simultaneous declaration
error precedence remains unspecified where CE07 says so; preservation does not
invent a new precedence rule. Keep the API-specific MemoryError, interruption,
translated operation-error and original-cause rules of the inherited contracts.

## Scenario inventory

Each row is a distinct preservation decision. Examples are coverage choices,
not new domains or an exhaustive Cartesian product. A maps every row to a
meaningful public-entry proof or explicitly retained accepted proof; B audits
that mapping and legitimate positives; D checks actual lifetime/alias risks.

| ID | Observable obligation and concrete qualifying scenario | Expectation source | Equivalent coverage examples / review |
| --- | --- | --- | --- |
| S01 | Original preparation and extended no-off/no-drift preparation keep their raw-to-band values, phase policy, scale and records. | CE02 operation order; CE06 §3 | 3D T2/D2/Z3/P5/O3; uniform versus full-rank supplied/reduced-order phases; independent finite sums |
| S02 | Completed per-section work leaves the full-Z transform unchanged, including the unseparated stored lateral Nyquist slots. | CE02 steps 5–7; CE06 §3 | Z2/Z3; phase-dependent nonzero native Nyquist data; finite negative forward sums |
| S03 | Exact sentinel events and persistent background/slope maps carry through later phases, z, directions and times. | CE02 steps 1–2; CE06 §3 | Sentinel on/off; later ordinary corner samples; maps and signed slopes; compare maps/events and bands |
| S04 | On equalization uses pre-equalization anchors and retains independent z/time sharing recurrences. | CE02 step 4; CE06 §3 | T2/Z2, all sharing flag choices, signed nonzero sums; disabled flags inert |
| S05 | Off loads precede on, sum all corrected exposures, and use preceding-on extra background with initial zero. | CE06 §3 | N1/N2; phase/z/direction/time boundary transitions; distinguish sum from average |
| S06 | Off equalization skips N1 and uses independent anchor state only for N>1. | CE06 §3 | N1 gains one versus N2 enabled; disabled equalization with zero sums permitted |
| S07 | Selected off combination repeatedly changes plane zero; later planes and scalar noise retain their contracted meaning. | CE06 §4 | Z>=2, multiple orders and repeated call_z; independent weights/trace affected_z=0 |
| S08 | Off statistics retain strict outside selection, signal clipping, both-zero replacement and valid one-zero weights. | CE06 §4 | Nonempty inside/outside, positive noise, one-zero and both-zero signal; no noise floor |
| S09 | Between drift runs before camera loading using current state, fixed10 and first-off handling, then corrects only the selected on bands. | CE06 §5 | Ordinary T2/D2/X=Y=10/Z>=2, N1/N2; nonzero and zero correlations; direction0 zero |
| S10 | Unfitted within-2D drift uses prepared on+off and its own estimator, positive correction and selected phase policy. | CE06 §6.1/6.3 | N>0/P3, no clock or linked phases; qualified fast-D1 within-2D alternative |
| S11 | Fitted within-2D keeps cubic timestamp alias mutation and linked phases. | CE06 §6.2/6.3 | P>=4 full rank, phase flag/metadata present; nonzero clock origin; inspect fit events |
| S12 | Ordinary within-3D preserves prepass/fit order, first-block header mutation across time and last-z noise. | CE06 §6.2/6.3 | D>=4/T2/P5, full-rank clock, both metadata arrays, adjust_phases true; with/without between correction |
| S13 | Fast-D1 between-only remains a skipped-prepass zero bypass; structural unsafe drift selections still reject. | CE06 §2/§5/§10 | Y1/dz0 bypass when otherwise valid; pair with ordinary prepass requiring positive dz and safe fixed10 geometry |
| S14 | Every side harmonic starts from exact required zeros; earlier harmonics/directions/times cannot contaminate later values. | CE04 literal traversal | O3/T2/D2, different sparse complex harmonics/supports; zero next harmonic after nonzero predecessor |
| S15 | Filtering preserves all-axis reflected negative partners, recombination and positive native Nyquist endpoint. | CE04 traversal/assembly | Asymmetric complex radial/full transfers and nonzero E/O; independently formed reflected partners |
| S16 | Odd-Y omitted-row values and partial reflected zero writes remain literal; Y1 loops remain empty. | CE04 traversal and claim limits; CE06 §9 | Y3/Y5; Y1 requested zero-cutoff damping permitted when other operations valid |
| S17 | Support, zeroing, denominator order, suppression/damping/omission/taper and signed assembly remain unchanged. | CE04 support/assembly; CE06 §9 | Multiple orders/directions, boundary samples, zero/signed modulation; valid power/overlap/explode variants |
| S18 | 2D/3D geometry, zoom and time-dependent filtering preserve dimensions, coordinates and stage decisions. | CE06 §9.2; CE07 §6 | Z1/dz0, A>1 zero extra planes; safe L=1.5 on compatible even lateral dimensions; T2 Wiener schedule |
| S19 | Full-debug captures remain complete, independently owned and stable after later harmonics/calls or caller mutation. | CE02/04/06 records; CE07; RM84 §1 | Direct preparation/known outputs and full workflow; retain multiple results, inspect earlier snapshots after later work |
| S20 | Summary remains its exact compact projection with identical scientific values, identities, decisions and omissions. | RM84 §§1–3 | Matched full/summary calls, nonzero multifrequency input; ordered trace/build references and no hidden spatial retention |
| S21 | Caller inputs and valid caller-modified stage quadratures/noise remain accepted and unchanged. | CE04 used-field rules; CE06 §10; RM84 §3 | Read-only/strided callers, signed/zero finite used data, post-return mutations; no raw replay |
| S22 | Invalid declarations, superseded invalid arrays and representation limits retain their error category and structural timing. | CE02 errors; CE06 §10; CE07 §10 | Wrong shape/kind, invalid unused supplied phase list, unsafe source/native extents without huge allocation; paired valid endpoints |
| S23 | Selected zero equalization divisor and singular used separation/clock designs reject without fallback or partial result. | CE02 errors; CE06 §10 | Pair zero divisor with disabled equalization zero sums; full-rank duplicate phases where permitted; valid cubic controls |
| S24 | Unsafe actual stencils, singular off statistics and nonfinite reached diagnostics/operations still reject at their existing stage. | CE04 errors; CE06 §10; RM84 §3 | Zero-weight stencil still checked; zero noise/empty sets; later-time nonfinite operation; pair finite zero data where defined |
| S25 | Allocation/backend failure cause handling and interruption semantics remain API-specific, with caller data intact and no partial result. | CE02 errors; CE04 boundary; CE06 §10; RM84 §3 | Use only justified observable public-boundary failure mechanisms; do not add production seams or force impossible states |
| S26 | Lifetime and resource claims distinguish reduced overlap/churn from observed process peak and retained payload. | Owner objective; RM84 §5 measurement method | Matched fresh-process baseline/candidate full and summary; repeated timing/peak/payload records and explicit variation/limits |

## Independent evidence and resource protocol

Freeze deterministic redistributable public fixtures, all generation formulas,
constants, expected results, declarations, hashes and measurement design before
candidate measurements. Use nonzero multifrequency data that actually completes
the intended branches, including meaningful off/drift positive cases. Retain
initially passing compatibility evidence; do not manufacture a product-red test.

The resource baseline is the eventual actual frozen parent, not a historical
issue crop. Compare baseline/candidate at identical workload, retained caller
inputs, locked Python/NumPy/SciPy/FFT/allocator/thread settings and host/cgroup.
Use fresh single-workload processes, no numerical child workers or export.
Report raw peak RSS/native units and conversion (Linux KiB ×1024), pre-call
high-water, call-only monotonic seconds and retained reachable ndarray payload
with shared backing counted once. Peak minus pre-call high-water is not an
isolated stage peak. State Python metadata, backend workspace, allocator,
swap/page-fault and disk-measurement limits.

Use three fresh repetitions per comparison as experimental design, not a human
budget cap. Report every run, failures, median/range and repeat variation. Include
the inherited RM84 native 3D spatial/time/direction series where feasible and
meaningful preparation/off/drift/direct-known comparisons; odd-Y/Y1 may remain
preservation tests without separate tiny-case performance experiments. A/B
must freeze which comparisons establish the present lifetime objective before
C. Do not tune case selection to a favorable candidate. Report resource results
for full and summary separately: retained public payload may intentionally stay
unchanged while temporary overlap improves. No percentage, byte reduction,
latency ratio or numerical threshold is selected. If process-peak benefit cannot
be distinguished from variation, call it unestablished and diagnose; static
lifetime reasoning or allocation churn alone is not a demonstrated peak benefit.

16 GiB is only a workstation feasibility objective with caller/OS headroom to
measure. Grow only after representation/headroom assessment, never deliberate
OOM. The inherited 2048-square historical example remains outside its source
unsigned32 workspace domain and is not an experiment or acceptance target.

## Delivery and acceptance

High risk: fresh blind A authors named public-entry tests and oracle/risk mapping;
fresh blind B independently accepts an exact test/fixture checkpoint; restricted
C implements only named product scope; fresh D independently reviews the exact
candidate, lifetime justification, preserved behavior and evidence. Reviewed
tests/config/gates stay frozen. Missing behavior returns through sanitized A and
fresh B; missing meaning returns to intake. Source-free diagnostics are mandatory
before any future blind probe. No executable work is currently authorized while
the execution hold remains.

Before implementation, the coordinator must bind the actual frozen parent
commit/tree and reassess inherited supported public profiles and shared behavior
against this contract. Reestablish applicability of fixtures/oracles/baseline
comparisons and renew all affected A/B checkpoints; a branch name or an earlier
supplied baseline is insufficient. Changed inputs renew affected review/check
evidence. Nonblind dependency details belong in candidate context, not this
public acceptance contract.

Behavior coverage and independent risk review inherit PROJECT; percentages are
advisory, with required exact native global/package/file/subprocess reports.
Full exact Ubuntu 24.04 `make verify`, all 13 phases, strict outcomes, two-worker
policy, wheel/import/audit and same-run M25 conversion evidence remain binding.
Matched measurements and fresh D acceptance are required; none has occurred in
this static intake. Integration/restack/PR/publication/cleanup belong to the
coordinator. No commit, push, merge or release is authorized for intake or roles.
