# SP113 — finite default-FFT method for cardinal dimensions only

This is a public primary-method source for independent A/B derivation, not a
review verdict or a universal FFT theorem. It contains no SIMrecon implementation,
prototype, prior numerical run or role conclusion. All checks remain held. The
method is usable only after the material source/binary/RNE assumptions below
are established; missing applicability is a blocking qualification gap.

## Scope and primary algorithm facts

Qualify only actual complex64 default-SciPy inverse calls with each transformed
axis length in {1,2,4}, axes(0,1,2), norm="forward", workers1, no overwrite and
plain NumPy arrays. This includes non-DC/nontrivial signed modes and enlarged
Nyquist fixtures with cardinal output sizes. It is not restricted to DC.
It does not apply to lengths6/8/20/32/64 or to an arbitrary custom backend.

Pinned SciPy1.18.1's NumPy default route is its vendored DUCC FFT, not an inferred
backend from output dtype. Public v1.18.1 sources identify these facts:

- The Python n-D wrapper resolves inverse norm="forward" to normalization mode0.
- Its c64 binding dispatches the C++ float specialization and mode0 gives exact
  factor1. The inverse direction is the positive-exponential transform.
- The source plan for length1 returns the input; length2 uses a single pairwise
  sum/difference; length4 uses two pairwise sum/difference levels plus exact
  quarter-turn component swaps/sign changes. Length2/4 single-factor plans have
  no consumed noncardinal twiddles. Their complex addition/subtraction operates
  componentwise. SIMD batching changes independent lanes, not these equations.
- N-D execution composes the one-axis plans. It may permute the axis order for
  contiguous storage. The level total below is invariant to that permutation.
  Normalization factor1 is not an extra rounded multiplication.

These facts are independently inspectable in the cited external numeric-library
sources; no raw code or link expansion is needed/authorized to A by this file.
They say nothing universal about other workspaces, algorithms or FFT internals.
The code's type specialization alone does not qualify arbitrary transform error.

## Derived finite enclosure, to be recalculated for each witness

Let the cardinal transformed shape be (n0,n1,n2), N=n0*n1*n2 and
`d=log2(n0)+log2(n1)+log2(n2)` (d<=6). A length1 path has0 rounded additions,
length2 has1, length4 has2. Each final real/imaginary component is an exact
signed sum of selected input components, with at most d rounded add/subtract
levels along a source-defined path; quarter rotations are exact. For
u=2^-24 and h=2^-150 use the valid elementary bound

```
|RN32(a+b)-(a+b)| <= u*|a+b| + h
```

for finite nearest-even addition without overflow. Let Sbar be an independent
pretrial upper bound on sum_k(|Re z[k]|+|Im z[k]|) for the actual c64 FFT input.
It comes from the declared coefficients/scalar/local arithmetic enclosures,
not observed candidate errors or a measured FFT multiplier. Then a conservative
per-component transform arithmetic enclosure is

```
eFFT <= gamma(d,u)*Sbar + (N-1)*h/(1-d*u)
gamma(d,u) = d*u/(1-d*u)
```

The first term follows the d-level sum error induction. A single output's
addition tree has at most N-1 nodes; local h contributions acquire at most d
remaining (1+u) factors, bounded conservatively by1/(1-d*u). When d=0,N=1 both
terms are zero. Verify d*u<1 and prove no overflow from the witness's independent
Sbar and local absolute-rounding bound. If a witness has only exact-zero/normal
intermediates, that stronger fact may simplify the absolute term, but do not
omit subnormal reasoning by assumption.

The exact reference is an independently enclosed positive direct DFT with
literal roots1,i,-1,-i. For coefficient input enclosures, propagate their
uncertainty separately through this finite linear sum, then add eFFT for
arithmetic on the actual represented inputs. Continue with independent
consumed-ramp/product, f64 accumulation and final f32 conversion terms. These
terms may not be merged into a blanket image tolerance. Record the fixture's
reference width, Sbar,d,N, normal/range conditions and complete resulting bound
before any candidate trial. A/B independently challenge the operation count,
source applicability, permitted alternatives, interval arithmetic and witnesses.

This justifies a finite source-based envelope; finite observed R/outputdtype
alone does not. Exact representable small sums can support a tighter zero-error
argument only after each relevant intermediate, not just the final DFT, is
proved representable under the actual selected plan.

## Material assumptions and remaining limits

Before reusing this method, record the actual locked SciPy wheel/module/version,
source correspondence, selected default backend/namespace, integer shape/axes,
norm, thread controls, IEEE round-to-nearest/gradual-underflow or a justified
normal-only witness, and absence of unqualified arithmetic reassociation.
The inspected installed version.py declares git revision
`e4e854eaa8f18d807cd3496028e257e36caa93cc`; this static text is provenance input,
not a runtime/binary proof. The pinned public source must correspond to the
actual binary path, with applicability challenged by B/D and necessary
root-granted dependency qualification. No rebuild/backend swap is authorized.
If a required assumption is unknown, retain the gap rather than inserting
this bound anyway. Higher precision at an internal elementary operation does
not enlarge the u32 bound if its final rounding still satisfies the elementary
inequality; this is not a universal claim about workspace/accumulator precision.

Controlled exact-transform substitution remains useful for mapping/axis/sign/
embedding semantics but is not the default-backend accuracy proof. Actual
nontrivial default calls must exercise the qualified finite shape/assumptions.
Do not extend the bound to unsupported sizes/twiddles, merely observed errors,
other backends or every positive input. Filter-stage-only fixtures at other
sizes must label their image-FFT accuracy unqualified, and any required intended
claim at such sizes remains blocking until independently justified. Do not drop
required carrier/taper/transfer/positive modes to fit this narrow method.

## Opened primary identities (read-only mathematical references)

All SciPy URLs below use public tag v1.18.1; Git blob SHA identifies the opened
file content, not a SIMrecon stage source identity:

- scipy/fft/_duccfft/basic.py: blob8b80a03e075f1847a1df070aea2861ca2edd2bcf.
- scipy/fft/_duccfft/pyduccfft.cxx: blob3f4b2f9ec72b8f5293ccf26bc98047ff28cf2b4a;
  c64 dispatch and normalization/c2c binding.
- subprojects/duccfft/ducc0/fft/fft.h: blob74dd837086b1be6bd7ccb527a8a7307bf2204987;
  factorization, plan and factor1 handling.
- subprojects/duccfft/ducc0/fft/fft1d_impl.h:
  blob04afdf2567379ce989a3f6717c0c0a6de202edd3; length1/2/4 passes and quarter rotation.
- subprojects/duccfft/ducc0/fft/fftnd_impl.h:
  blobbc3dcf87ad8781838b0e7580cda96f602f35a030; N-D composition/order.
- subprojects/duccfft/ducc0/math/cmplx.h:
  blob522a3bdda1111de23284fdb3ca9f9de0eda548ae; component arithmetic.

Canonical URL form is https://github.com/scipy/scipy/blob/v1.18.1/<path>.
These are external library algorithm facts and finite error algebra, not an
instruction to read unlisted source. The whole-file permission is only for this
sanitized public method. No runtime or numerical experiment has been performed
to manufacture the envelope, and no numerical acceptance follows from this page.
