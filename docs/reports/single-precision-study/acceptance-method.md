# Independently intakeable first-slice acceptance method

This is a proposed computational method for #113, not acceptance of an
implementation or a physical-recovery threshold. It distinguishes what can be
bounded before observing a candidate from the present observed-only FFT term.
The separate high-risk intake must freeze operation order, public diagnostics,
exact fixtures and backend assumptions before product tests.

For each declared fixture, retain four references: exact declared data x0,
exact rounded input x32, exact mathematical finite CE04 F(x32), and the actual
candidate. Keep F(x32)-F(x0) separate. A baseline double result is only a
compatibility control. For the supplied sparse dyadic coefficients this input
term is exactly zero; transfer examples such as 1+2^-30 have a nonzero separate
term. A zero/undefined helper has no reference value.

1. **Scalar filtering.** Evaluate every positive self/eligible-other power and
   denominator independently with rational interval arithmetic, respecting the
   exact strict support mask and order. For the frozen dyadic unit-transfer
   witnesses no transcendental scalar is needed. At each prescribed binary64
   operation enclose round-to-nearest with half an ulp in that bin (ties retain
   even). Enclose division only if its denominator excludes zero. This gives an
   a priori interval for the actual scalar operation sequence and a separate
   interval around the exact rational CE04 scalar. Finite subnormal bounds use
   half-minimum spacing, not relative gamma; overflow makes the selected
   precision unqualified for that input. The supplemental gamma(32n,u64)
   envelopes are deliberately conservative finite-normal diagnostics, not a
   substitute for freezing and reviewing the downstream operation sequence.
2. **Scalar-to-bulk and coefficient arithmetic.** Round each bounded consumed
   scalar/transfer value explicitly to complex64, recording that error. Promote
   bounded chunks before powers/cross-products. For a real component of a complex
   product, use its two separate product errors plus addition error; under finite
   normal arithmetic an envelope is gamma(3,u32) times the sum of absolute real
   products, with input/scalar rounding added separately. Include up to three
   half-subnormal spacing terms where necessary. Apply the same rule to the
   imaginary component. Form both actual candidate +/- coefficients, then
   independently enclose E=(p+conj(n))/2 and O=(p-conj(n))/(2i). The independent
   observer never supplies n to the candidate. Compare public filtered fields
   against these component intervals. Addressing, untouched-row and native
   Nyquist scenarios need their own fixtures; these sparse data do not cover them.
3. **FFT term.** Independently enclose the tiny DFT with exact roots/rational
   intervals. For the general pinned FFT the current study provides observed
   component errors at its frozen finite inputs, not a proved internal FFT
   error multiplier. Denote the still-unqualified stage term eFFT; do not insert
   gamma(N,u) for an undocumented FFT implementation or set eFFT to an observed
   maximum and call that a theorem. A scientific acceptance verdict for a new
   FFT-dependent witness must declare/review a justified fixture-specific FFT
   envelope (or explicitly leave its accuracy unqualified). Semantic checks on
   axes, sign, normalization and signed scale still apply independently.
4. **Assembly/conditioning.** Propagate coefficient/ramp/reference/FFT interval
   errors with absolute weights through each order and direction, retaining
   signs and the original accumulation order. For K finite normal accumulator
   additions, add gamma(K,u64)*sum(abs(actual terms)); add absolute subnormal
   contributions separately. Report cancellation condition sum(abs(terms)) /
   abs(exact signed sum), infinite at zero, rather than dividing error by each
   image pixel. Do not use a small residual to prove a conditioned solve's
   forward accuracy. Phase zero has no meaningful phase-error metric.
5. **Final conversion and verdict.** Add the actual binary64-to-binary32 rounding
   interval; a simple finite bound is u32*abs(accumulator)+2^-150, and a local
   half-ulp bin gives a tighter bound. Reject nonfinite/overflow at the declared
   stage, with no partial result. A candidate fails a fixture if it leaves an
   independently frozen interval at a qualified stage or changes a certified
   discrete decision. An interval overlapping a decision boundary is unresolved,
   not pass. Record measured errors even when all bounded stages pass. A missing
   eFFT qualification leaves general FFT accuracy explicitly unqualified.

A fully concrete first fixture is M06 DC-only: w=1/2, v=1, modulation1 give
exact denominator13/4 and scale4/13. Center coefficient1 and side coefficient
-1/2 give exact cancellation; a single DC inverse is the constant coefficient
and needs no nontrivial root evaluation. The correlated exact rounding equations
are `s64=RN64(4/13)`, `s32=RN32(s64)`, `p0=s32`, `p1=-s32/2`, signed assembly
`p0+2*p1=0`; both the accumulator and final conversion are exactly zero. This
supplies a meaningful **zero-error constant-transform witness**, separately from
any general FFT bound. It does not prove arbitrary FFTs are exact.

For near cancellation replace side coefficient by -(1-2^-20)/2. The exact signed
reference is 4/(13*2^20), condition2097151. Before any candidate is observed,
`|s64-4/13|<=2^-55`, `|s32-s64|<=2^-26`; the real side product's rounding error
is at most2^-27 in its known bin. Thus a conservative independent absolute
pre-conversion assembly bound is

```
(2^-55+2^-26) * (1 + 2*(1-2^-20)/2) + 2*2^-27
```

plus any declared nonzero FFT term and final local half-ulp. This is below
`3*2^-26+2^-54` before final conversion. It is derived from the fixture's
coefficient/scalar bins, not tuned to its observed4.58497e-9 error. Exact
rounding interval evaluation supplies tighter per-stage bounds. This witness
and the exact cancellation case preserve signed weak outputs without an energy
floor, positivity projection or arbitrary global tolerance.

For M02/M03 and eighth-root resource witnesses, the reference-interval width and
all candidate errors are available, but the general FFT-dependent envelope is
observed-only. #113 can use the exact DC/scalar fixtures and this interval
construction as a starting checkpoint; its scientific A/B review must resolve
additional FFT witnesses and literal CE04 branches before a broader numerical
qualification claim. Record the accepted computational claim and its remaining
FFT/physical limits explicitly. Application noise/model mismatch accuracy,
workstation peak memory and any later default migration are separate decisions.
