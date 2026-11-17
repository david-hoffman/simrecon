# Actual K01–K04 numerical kernels

Completed primary observations under measured source2468/c439. Full raw run/array identities and immutable source scopes are in the evidence archives and primary-attempt-index.json. This is finite descriptive evidence; full-grid/upstream science remains UNRESOLVED/noactivation. The separate CPU summary-only result and H3 limits are in study.md/backend.md.

## K01: binary16 range, paired encoding and signed zero

The16 retained real binary64 words match the prescribed inputs, including +0/-0,
±2^-25, ±2^-24, ±2^-14, ±1, ±65504, ±65520 and ±70000. Independent integer/rational
nearest-even conversion matches every retained half word and promoted binary64
component. The paired encoding has shape(16,2), real component then imaginary,
little-endian binary16. Its promoted representation is complex128, not a native
complex32 ndarray or a half transform operand.

| Input magnitude | Actual binary16 conversion |
| --- | --- |
| 2^-25 | Signed zero: halfway tie rounds to even zero |
| 2^-24 | Smallest positive/negative subnormal retained |
| 2^-14 | Smallest normal retained |
| 1,65504 | Finite signed values retained |
| 65520,70000 | Signed infinity; intentional finite-to-nonfinite conversion |

For the real vector, four components become nonfinite and two source-nonzero
components become zero; promoted output has four zeros, two negative. For the
32 paired components, eight become nonfinite and four source-nonzero components
become zero; two promoted component zeros are negative. The actual constructed
original complex vector has different zero signs from the nominal reversed-real
vector because complex construction can affect zeros. Comparisons use its retained
actual original component bits, not a nominal sign assumption.

Source error results explicitly classify nonfinite conversion:12 finite real
pairs and8 finite complex pairs. A whole-vector finite max/RMS/relative error is
not supplied or invented. Three RuntimeWarnings at study.py753/746/747 retain
“overflow encountered in cast.” No clipped value, rescaling or successful pipeline
continuation replaces these intentional outcomes. Reported limits65504,2^-14,
2^-24 and epsilon2^-10 agree with the fixed binary16 representation; unit roundoff
near one is epsilon/2, not a selected scientific tolerance.

## K02: normalization of tiny vectors

Each actual case holds only eight values, with factors
`[+0,-0,-128,-1,-2^-12,2^-12,1,128]` times its recorded binary64 alpha.
Independent denominator arithmetic, retained original components and nearest-even
packed words agree. No large-volume data were generated or measured by the
metadata-only row.

| Alpha label and exact denominator | Source max absolute error | Source RMS | Source relative L2 | Nonzero-to-zero |
| --- | ---: | ---: | ---: | ---: |
| W02:12288 | 2.5431315104160884e-6 | 1.2716433630542642e-6 | 2.441480750117083e-4 | 2 |
| W05:49152 | 6.357828776040221e-7 | 3.180563177495188e-7 | 2.44259797927459e-4 | 2 |
| metadata-only:100663296 | 1.9868214925130138e-8 | 1.110666985724264e-8 | 1.746874808256023e-2 | 4 |

These errors are in the declared normalized scalar-vector units, not observed
image-recovery error. Exact Fraction squared errors/reference energies and their
derived metrics are retained in file-arithmetic-results.json. Independently
derived W02 relative L2 is0.00024414807501170824, while source reports
0.0002441480750117083: final rounding/evaluation differs, so no bitwise equality
or new tolerance is asserted. Other displayed independent max/RMS values agree
as recorded. Zero/reference semantics remain explicit rather than inferred.

W02/W05 promoted vectors each have four zeros, two negative; metadata-only has
six zeros, three negative. Remaining binary16-subnormal-range counts are0,2,2.
No warnings occurred. The large metadata shape fixes alpha only; it does not
establish full-volume underflow counts, allocation, runtime, RAM fit or a16GiB
workstation result.

## K03: dyadic operands, wider operations and explicit half operations

All16 retained cases cover n16/4096 × magnitudes2^-12/1/256/1024 × constant/
alternating patterns. Independent Fraction formulas verify the exact/original/
quantized-operands-wider scalar results and all retained packed/promoted operand
components. For magnitude a, energy is n·a²·65/64; constant complex cross is
n·a²·(95/128−5i/32); alternating cross is zero. These finite operands are exactly
representable in half, so these particular wider reductions suffer no operand
quantization error; that is not a general complex-data theorem.

| Magnitude | Explicit half energy, both n | Explicit half real-cross sum |
| --- | --- | --- |
| 2^-12 | n·2^-24, losing the smaller squared term | constant n·2^-24; alternating0; the rounded product differs from exact cross |
| 1 | n·65/64:16.25 or4160 | constant n·95/128:11.875 or3040; alternating0 |
| 256 | +Inf from product/energy overflow | constant+Inf from reduction; alternating0 from finite signed products |
| 1024 | +Inf | constant+Inf; alternatingNaN from opposite infinities |

The fixed-case explicit-half scalar results were checked against these expected
representability/overflow/cancellation contrasts. Source product statistics and
all scalar wire words remain retained. This does not establish a universal NumPy
reduction association, multiplier/accumulator implementation or pipeline support.
The separate M01 [2048,1,−2048] cancellation control is method evidence, not an
additional primary K03 sample or a replacement for these16 cases.

Sixteen RuntimeWarnings are preserved: overflow in multiply at study.py1674/1668,
overflow in reduce and invalid value in reduce at NumPy fromnumeric.py83. Their
full order/messages/categories/locations are retained in the original record and
derived provenance. No warning is suppressed or converted into scientific success.

## K04: limited scalar and phase-design witnesses

The retained constant16-element spectrum1024−256i has unnormalized inverse origin
16384−4096i and numerically zero other entries, matching the fixed finite-sum
expectation. Original component words remain in the inventory; numerical-zero
agreement is not a universal signed-zero or FFT-accuracy theorem.

| Equal-power scalar witness | Wider result | Quantized operands, wider formula |
| --- | --- | --- |
| [1,4,3] | offset0.25,fitted | offset0.25,fitted |
| [1,2,3] | offset0,zero-curvature | offset0,zero-curvature |
| [1,2,3+2^-12] | offset0,outside-range | offset0,zero-curvature |
| [1,1+2^-12,1] | offset0,fitted | offset0,zero-curvature |

The general three-point witnesses give1.25/fitted,0/duplicate-coordinate and
0/zero-curvature. Ordered objective [1,1+2^-12,1] changes first maximum index1→0
and strict improvement true→false when quantized to[1,1,1]. These fixed scalar
dispositions were inspected/checked. The outside1.5-bin fit is not demonstrated
reachable from a coarse global peak; scalar formula results establish no public
combined-fit branch coverage or full estimator behavior.

The equal-energy pair remains sx=sy=4 in both representations. With gain1+2^-12,
wider sy=4.001953363418579 differs from sx4; quantized sy becomes4 and equality
changes false→true. This is an explicit singularity-risk witness, not a public
fit that was invoked or accepted.

For each of three retained3×3 designs, exact Fraction determinant/cofactor
arithmetic was applied to the actual saved binary64 entries and saved quantized
entries; no trigonometric design was regenerated. Uniform designs remain
nonsingular, with source-observed condition1.414213562373095. Repeated-zero-angle
design is singular in both representations, with source-observed infinite
condition. Near-conditioned wider design is nonsingular with source-observed
condition695109.4772197384, while its quantized design is exactly singular.
Both singular outcomes retain StopIteration and
`intentional-singular-formula-witness`, not a product exception diagnosis.

For the three nonsingular actual matrices, retained inverse entries match rounded
exact adjugate/determinant values. Source-observed maximum residuals are
1.2952601953960168e-16(uniform wider),1.1102230246251565e-16(uniform quantized),
and6.0632610043853674e-12(near-conditioned wider). These residuals/condition
estimates are source observations, not an independent SVD or public phase-solve
qualification. Public guards and residual criteria are unchanged; no favorable
conditioning cutoff or modified phase/noise rule is proposed. No K04 warning
occurred.

## Diagnostic native and timing scope

| Primary observation | Source pre/before-export/after-export KiB | GNU terminal KiB / bytes | Source whole-kernel operation seconds | GNU broad elapsed seconds |
| --- | --- | --- | ---: | ---: |
| K01 | 80276/80932/80932 | 80940 /82882560 | 0.000996876 | 1.00 |
| K02 | 79716/80516/80516 | 80528 /82460672 | 0.001413231 | 0.69 |
| K03 | 79820/81508/81508 | 81600 /83558400 | 0.022679762 | 0.71 |
| K04 | 79596/81472/81472 | 81472 /83427328 | 0.001845108 | 1.60 |

Native Linux KiB×1024 conversion, source endpoint bytes, source clock endpoint
order/seconds arithmetic and terminal≥source cumulative observations were checked
for these actual cases. Direct Python/time argv/parent association, unique absent
destinations and original PID/start identities absent after close are retained.
This uses the previously qualified finite ordinary GNU time route with current
case evidence, not a new native/cleanup review or all-process census.

Source operation spans the whole kernel function and its observers; it is not
per-transform call latency. Source cumulative snapshots precede final JSON/
teardown; external GNU time is through-exit direct-Python native usage, distinct
from broad formatted elapsed and local monotonic scopes. One deterministic pass
of these tiny kernels is not a benchmark, speed result or stable latency estimate.
No high-water subtraction, causal late-allocation claim, observer/tree sum,
workspace/native-half precision theorem or RAM-fit extrapolation follows.

These kernels demonstrate named finite range/quantization/decision effects only.
They neither certify W reference validity/common projections nor decide physical
usefulness, a product activation boundary or the final numerical-acceptance
proposal. The scoped matrix update and CPU/backend section accompany this draft;
final independent SCI must assess the completed exact whole report later.
