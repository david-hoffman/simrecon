# SP113 — selected scalar-library enclosure method, not a general ULP promise

This whole public method supplies primary algorithm facts for independent A/B
point-specific derivation. It is NOT an acceptance verdict, generic libm guarantee
or a license to read external source. No numerical run/candidate data selects
an allowance. All execution stays held. Use only for frozen finite witnesses
whose actual primitive/source/binary/RNE/branch conditions are established;
otherwise retain G3 explicitly. Do not grow a general transcendental framework.

## Independent references and finite rounding boxes

Use exact rational stored inputs/constants. For an interval I define
R64(I)=hull(I,[RN64(lower(I)),RN64(upper(I))]); RN64 is the independent integer
nearest-even reference, not a library under test. Interval add/subtract/multiply/
divide are outward exact rational operations (division requires zero exclusion).
Applying R64 after each expression node includes both separate rounded evaluation
and any omitted intermediate rounding in a fused operation; verify the actual
source expression/no unsafe reassociation assumption rather than guessing it.
No underflow/overflow occurs in the moderate selected paths below; tiny-tail
operations remain normal until their harmless final rounding.

Enclose sqrt(t) independently: for positive rational t and B=2**p, take
k=isqrt(floor(t*B**2)), l=k/B,u=(k+1)/B and verify l*l<=t<u*u.
Monotonic endpoint application encloses interval sqrt; then apply R64 for an
IEEE correctly rounded sqrt. Precision p160 is ample for these selected values,
but the squared inequalities, not precision alone, certify the endpoints.

For sin/cos of the exact rational binary arguments below, alternating rational
Taylor sums with the next-term bound give a reference independent of libm/table
values. For ideal eighth-root values one may also use independently enclosed
sqrt(2)/2. Keep binary64 pi-constant/phase evaluation error separate from ideal
mathematical-pi references; a Machin arctangent identity with rational alternating
remainders can certify pi if needed. No observed library value or Decimal
precision doubling supplies these references.

## One non-c64-exact transfer point: H=(1+2^-30)+i/2

At an exact table node the source H is the declared c128 dyadic value; no
interpolation arithmetic or premature c64 rounding changes it. Python built-in
complex absolute uses the platform hypot. On identified glibc2.39, the finite
compatibility hypot wrapper forwards the current finite kernel. The following
source expressions are mathematical primary facts, not a SIMrecon helper.

Set a=1+2^-30,b=1/2, a>=b>0. These are far from scale/tiny/ratio exits, so only
the moderate kernel applies. Cover its selected source variants by a union of
outward round-box evaluations:

- FMA variant: t1=R64(b+b),t2=R64(a-b). Here t1<a is certified, so
  h=R64(sqrt(R64(a*a+R64(b*b)))); the a*a+... fused node has one final rounding.
  If considering a different frozen moderate pair, certify its branch or include
  the other formula sqrt(R64(t1*a+R64(t2*t2))) explicitly.
- Non-FMA variant: h0=R64(sqrt(R64(R64(a*a)+R64(b*b)))). Here h0>2*b is certified.
  delta=R64(h0-a), t1=R64(2*delta*R64(a-2*b)),
  t2=R64(R64(R64(4*delta-b)*b)+R64(delta*delta)),
  h=R64(h0-R64(R64(t1+t2)/R64(2*h0))). Apply outward round boxes also at each
  interior multiply/add indicated by the expression; no factor/order is inferred
  from a candidate result. A source FMA contraction is contained by R64 hulls.

In exact arithmetic t1+t2=h0*h0-a*a-b*b, so the correction is a Newton sqrt
correction. Independent sqrt(a*a+b*b) reference and the above finite-program
union yield an a priori signed library-error interval/upper bound. Derive the
actual interval and branch margins for this point before a trial; the source's
approximate ~0.792/~0.948ULP comments are NOT the bound. Input and intermediate
range checks/denominator exclusion are part of the proof. A moderate alternative
pair needs its own verified conditions, never a blanket extension.

Propagate this uncertainty through the prescribed f64/c128 powers/ordered
quotient and once-rounded consumed c64 scale. Report original source conversion
separately: this H was never rounded to c64 at the transfer boundary. A zero-
carrier DC fixture can isolate scalar/local/accumulation behavior from nontrivial
FFT and phase errors. If a final consumed-scale enclosure crosses a rounding
boundary, report the interval/uncertainty or choose a justified pretrial fixture;
do not tune it after observing a candidate. Other interpolation witnesses still
need their own exact-node/affine-weight reference and local rounding analysis.

## Selected taper/ramp arguments: 0, +/-P/4, +/-P/2

P is the exact binary64 pi constant 0x1.921fb54442d18p+1. A derives from each
fixture why the actual evaluated argument equals one of these or lies in a
certified small interval with the same source branch/table index. Choosing these
points is finite witness design, not permission to drop shifted-ellipse,
zero-c[1],rho1, nonzero/subpixel/signed-carrier requirements. Other required
arguments remain unqualified until independently enclosed.

On glibc2.39 the relevant standalone sin/cos and combined sincos paths share
these finite formulas, including the x86 FMA specialization. For |x|<2^-27,
sin(x)=x and cos(x)=1 in the source; at exact0 this is exact (signed sin zero is
preserved). For x=+/-P/2, source reduction is y=hp0-|x|,a=y+hp1,
da=(y-a)+hp1 with hp0=P/2 and hp1=0x1.1a62633145c07p-54. Thus y=0,a=hp1,da=0.
The tiny sine polynomial correction is far below half an ulp of hp1; the cosine
correction is far below half an ulp of1. Prove these inequalities with the exact
constants/ranges. This gives cos(+/-P/2)=hp1>0 and sin(+/-P/2)=+/-1 for this
identified path, not an ideal hard-zero substitution. Relate hp1 to the ideal
pi/2 residual with independent pi/reference intervals, not decimal trust.

For x=+/-P/4, rounding big+abs(x) with big=0x1.8p45 selects the unique knot
q=101/128 (certify its midpoint margin). The reduced t=abs(x)-q lies strictly
within [-1/256,1/256]. The exact table bit patterns at that knot are:

```text
sn  = 0x3fe6b5ce50b7821a
ssn = 0xbc65d5158f702e0f
cs  = 0x3fe68b5a92eb6253
ccs = 0xbc89a91ad985f89c
```

They encode binary64 sin/cos high/low values, not a candidate observation.
Interpret bits exactly as rationals. The source decimal coefficients are
rounded to binary64; include that conversion in outward boxes:

```text
sn3 = -1.66666666666664880952546298448555e-1
sn5 =  8.33333214285722277379541354343671e-3
cs2 =  4.99999999999999999999950396842453e-1
cs4 = -4.16666666666664434524222570944589e-2
cs6 =  1.38888874007937613028114285595617e-3
```

Outward-evaluate xx=t*t, s=t+t*xx*(sn3+xx*sn5),
c=xx*(cs2+xx*(cs4+xx*cs6)). Source cosine is
cs+((ccs-s*ssn-cs*c)-sn*s); source sine at positive x is
sn+((ssn+s*ccs-sn*c)+cs*s), with odd/even sign handling for negative x.
Apply R64 at every elementary node, retaining source expression grouping and
covering fused/nonfused forms. Compare those program enclosures with independent
rational Taylor references at x, then separately with ideal pi eighth roots.
The resulting point-specific interval, not the ~0.55ULP source comment, is the
library term. Verify no branch/index boundary is overlapped. RN32 hulls may
collapse to a unique consumed ramp/scale component; prove that bin separation.

For a unit complex exponential at finite pure imaginary argument, the inspected
NumPy scalar complex-exp route calls cexp, or its configured fallback calls
exp(real)*cos(imag),exp(real)*sin(imag). The inspected glibc pure-imaginary cexp
uses sincos and exp(+/-0)=1, so these finite point formulas apply only after the
actual binary/primitive route is identified. Do not infer that route merely
from a symbol import or outputdtype. A different candidate primitive/dispatch
needs applicable independent justification; no source inspection by A is granted.
Positive/negative quarter/eighth turns permit nonzero, signed and noninteger-
carrier controls with finite cardinal FFT shapes. Preserve full complex-product/
f64 contribution/final conversion propagation, not a sign-only accuracy claim.

## Material applicability and opened primary identities

The actual root-selected Ubuntu build, glibc/SciPy/NumPy/CPython binaries and
selected primitive path must correspond to these source facts, with IEEE RNE,
normal/range checks and valid source expression/rounding assumptions. Static
ELF imports/provenance are evidence inputs, not proof every dispatch uses this
path. Root-granted finite dependency qualification and fresh B/D challenge remain
necessary. If material correspondence/point enclosure is unresolved, G3 stays
blocking for that witness. No numerical run/acceptance has occurred here.

Primary Git blob identifiers opened by the coordinator:

- glibc2.39 e_hypot.c:4a2a8793126ecfe3c665a2f3f8f79fb5603a232d;
  math/w_hypot_compat.c:ec983a4ab8df61fb9d71b9d019147357ad57d8dd.
- glibc2.39 s_sin.c:ad3175001fad5e1376ff9fc0442b43853b6d6bbe;
  s_sincos.c:adbc57af2827bb801c3497d6716c41109cb1eafa;
  usncs.h:b220f079b6f904c1d21be78f04aabe6634f65526;
  sincostab.c:1459368bc73dcd2bd5cbb53500a992a101076b9d.
- glibc2.39 math/s_cexp_template.c:5247cf49d2b83a13f4c85a9b75103fd6fcb174b4;
  x86 FMA s_sin source:15f3c394d5c0a3a96c5fd12d45c2699f8409e0eb.
- CPython3.13.12 Objects/complexobject.c:502b4a9a96119e7e995df82b89f28d63faa12b1c.
- NumPy2.5.3 funcs.inc.src:d1b0b5522927786055e3a0dae8d507d2a4af2072;
  npy_math_complex.c.src:72a7ae9b3f4ea7c5edccb9e64efd970214071bde.

Canonical primary repositories/tags are bminor/glibc glibc-2.39, python/cpython
v3.13.12 and numpy/numpy v2.5.3 on GitHub. These references are not link/source
read permissions. Only this sanitized whole public method is newly supplied;
no raw library code, SIMrecon source,112 prototype/report, coordinator diagnosis
or sibling/advisor conclusion is an A input. Independent author/reviewer must
recalculate every used interval and its applicability; this method is no verdict.
