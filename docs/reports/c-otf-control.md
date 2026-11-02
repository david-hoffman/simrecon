# Small complex transfer-sampling control

**Version 1.0. Preregistered before CE03 implementation observations.**

This control checks the public declared-transfer sampler on an asymmetric
complex table. It does not model a pupil, a physical point spread function,
bead recovery or a reconstructed image. Independent empirical bead preparation
and raw-to-transfer-to-sample proofs belong to the accepted CE03 test checkpoint.
No retained C is executed. Binary-output agreement remains untested.

Use two complete full tables, each with `(z,y,x_half)=(4,4,4)`, and unit frequency
increments (1 cycle/um) on all axes. At integer indices define

`F(x,y,z)=1+2*x-3*y+4*z+x*y-2*x*z+3*y*z+0.5*x*y*z`

`+ i*(-2+x+2*y-z+2*x*y+x*z-y*z+0.25*x*y*z)`.

Order0 is F; order1 is F/2. Every table real/imaginary component is exactly
representable in float32. No rescaling or Hermitian repair is applied on
`declare_otf`. Sample order1 on a 41 by41 x/y grid from -0.75 to0.75 cycles/um,
with integer axial index1 and explicit native axial step0.5 cycles/um.

An independent expectation follows from the exact reproduction of multilinear
polynomials by tensor interpolation. For nonnegative x, the source normalized
x coordinate is x; its y coordinate is y if y>=0, otherwise its seam stencil has
weighted mean -3*y. Its z coordinate is0.5. For negative x, all coordinates
reflect: the normalized x is -x; reflected y has weighted mean -y if y<=0,
otherwise3*y; reflected z crosses the last-to-first seam and has weighted mean
1.5. Evaluate the polynomial at these means, divide by2 and conjugate only
for negative x. No runtime interpolation helper supplies this expectation.
The arbitrary table need not have matching values across x=0; a sign-boundary
jump is intentional and is not an optical discontinuity claim.

The fixed absolute complex error bound is **5e-12 transfer units**. The input
coefficients and integer table samples are exact binary numbers; the registered
grid values are evaluated as their binary64 coordinates. Fewer than100 real
floating operations per component, with weighted absolute terms below100,
give a conservative rounding allowance of order100*100*2^-52=2.23e-12;
5e-12 also covers independent polynomial evaluation/grouping error. This is a
control-specific bound, not a universal accuracy promise or a tuned threshold.
No gain, registration, fitting, parameter selection or per-result adjustment
is allowed after observing product output.

The figure will show real and imaginary expectation/result and signed
result-minus-expectation on common coordinate scales. Expected and observed
values share a fixed scale for each component; residuals use the same symmetric
fixed scale of +/-5e-12 transfer units. Pixel density is only display sampling.
All input/query/expected values, the pre-observation specification hash,
observation, maximum error and renderer provenance live in the task evidence.
Final values are recorded outside tracked bytes unless a separate observed
report is prepared before exact-candidate verification.
