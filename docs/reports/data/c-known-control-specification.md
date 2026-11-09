# CE04 independent numerical presentation preregistration

Frozen before any CE04 product observation. This is a coordinator presentation
control, not A/B/C/D evidence or a new test. The author read only these public
contracts: `c-equivalence-known-parameters-v1.md`,
`c-equivalence-common-v1.md`, `c-equivalence-preprocessing-v1.md`, and
`c-equivalence-optical-transfer-v1.md`. No product code, tests, history, retained
C, task state, coverage, or lessons were read. No product is imported or run by
the independent arithmetic.

## Purpose and claim limits

Show that native filtering followed by centered carrier assembly has a signed
image and spectrum that differ from one explicitly specified interpolation-first
quotient. Verify the selected mathematical mapping using public CE02 preparation,
CE03 `declare_otf`, and CE04 `reconstruct_known` after implementation acceptance.
Do not claim image recovery, resolution, historical executable agreement, or
that the comparison is the only possible interpolation-based algorithm.

No gain fit, registration, truth-based adjustment, clipping, output shift,
scene reuse, or tolerance change is permitted. If the control is uninformative
or the contract changes materially, record that fact and supersede this document
before product observation; do not silently tune it.

## Fixed acquisition and raw samples

Shapes: T=D=1, P=5, Z=4, Y=X=8, O=2; lateral zoom L=2 and axial zoom A=1.
Pitch: dxy=0.5 um, dz=0.75 um. Native frequency steps are dx=dy=0.25
cycles/um and dzf=1/3 cycles/um. Output shape is (1,4,16,16), with
0.25 um lateral and 0.75 um axial spacing. CE02 alpha is exactly 1/1024.

All arrays below are explicit integer sequences, indexed from zero:

```
f = [4, 3, 0, -3, -4, -3, 0, 3]
g = [3, 1, -2, -3, -3, -1, 2, 3]
u = [1, 1, -1, -1]
v = [1, -1, -1, 1]
c = [3, -2, 1, -3, 1]
d = [-1, 3, -2, -1, 1]
fs[x] = f[(x-1) modulo 8]
I[0,0,p,z,y,x] = 128 + 2*f[x]*u[z]
                       + c[p]*g[y]*v[z] + d[p]*fs[x]*u[z]
```

Raw I is stored as float64 but consists only of integers in [99,157], hence
is exactly float32-representable and contains no camera sentinel. Use
`prepare_bands(I, dxy_um=0.5, dz_um=0.75, norders=2, background=128.0,
lateral_zoom=2, axial_zoom=1, flatfield_slope=None,
exposure_background=None, phases_rad=None, edge_pixels=0,
equalize=False, equalize_z=False, equalize_time=False)`.
The phase policy is the uniform P=5 policy; scalar noise factors are one.
The integer phase coefficients are not chosen to require a sign decision at
an exact sine/cosine tie. No supplied-phase inversion is involved.

This is a signed raw-mode control after subtraction of the declared background.
Its spatial modes have kx or ky in {+-1,+-3}, kz in {+-1}; there is no DC,
native lateral Nyquist, or native axial Nyquist signal. It is not an object or
photon-count simulation. Background-corrected zero frame sums are allowed
because equalization is off.

## Fixed complete transfer and reconstruction settings

Declare a radial complex table of shape (2,10,4), dkr=0.25 cycles/um,
dkz=1/3 cycles/um. For j=0..9 and k=0..3, let s=[0,1,0,-1]:

```
samples[0,j,k] = (1-j/16) + i*s[k]*(j+1)/128
samples[1,j,k] = (7/8-j/32) + i*s[k]*(j+2)/64
```

Every component is dyadic and exactly complex64-representable. Use only public
`declare_otf(samples, layout="radial", dkr_cyc_um=0.25,
dkz_cyc_um=1/3)`. The table has no empirical normalization. Its odd imaginary
axial component and nonconstant radial response are intentional. At z=+-1,
all self/eligible-overlap radial queries have radius <=1 cycles/um, hence
radial floor <=4 and next radial vertex <=5; all are inside the 10-row table.
Axial k=-1 wraps once to table index 3, whose next vertex is 0. All actual
vertices are retained, including zero-weight ones.

Use carrier [[0.19,0.11]] cycles/um (0.76 and 0.44 native bins), side
modulation [[0.75+0.25i]], wavelength 500 nm, numerical aperture 0.8,
immersion index 1.4, wiener 0.5, suppress_singularities=False,
suppression_radius_bins=10.0, dampen_order0=False, omit_order0=False,
omit_kz0=False, output_taper="none". No record mutation is used.

The contract gives R=1 cycles/um. The un-clipped c0 is 2; both O=2 cutoffs
clip to 1. The source's two unused asin arguments are inside (-1,1).
The even-Y branch covers all rows. Self support uses <=R and overlap support
uses <R. The nonzero input modes are strictly inside self support. All shape,
allocation, and source integer bounds are small and safely representable.

## Independent finite expectation

Let F_f(k)=sum_x f[x]*exp(-2*pi*i*k*x/8), with F_g and F_fs analogous.
Let U(l)=sum_z u[z]*exp(-2*pi*i*l*z/4), V(l) analogous, and
zc=sum_p c[p]*exp(+2*pi*i*p/5), zd=sum_p d[p]*exp(+2*pi*i*p/5).
These are direct finite sums, not calls to product transforms or helpers.

For full signed native integer frequencies kx,ky,kz, the only nonzero
unfiltered bands are

```
B0 = alpha * 5 * 2 * F_f(kx) * 8*[ky=0] * U(kz)
B+ = alpha * (zc * 8*[kx=0] * F_g(ky) * V(kz)
              + zd * F_fs(kx) * 8*[ky=0] * U(kz))
B-(k) = conj(B+(-k))
```

Here kx or ky is +-1 or +-3 and kz is +-1. Exact zero modes are omitted
algebraically, not inferred by an observed small numerical coefficient.
As a cross-check, F_f(+-1)=8+6*sqrt(2), F_f(+-3)=8-6*sqrt(2).
The independent full sums may also compute E and O separately from the real
and imaginary parts of zc,zd, for comparison to public CE02 quadratures.

At each occupied native coefficient q=(kx*dx,ky*dy), use the public radial
bilinear stencil (including its axial seam) to evaluate Hm(q,kz). Define
a0=1, a+=a, a-=conj(a). For the positive side native sample, K=q+k0;
for order zero K=q. Its denominator is self |am*Hm(q,kz)|^2 plus each
other signed n in {-1,0,1} with |K-n*k0|<R, then w^2. The numerator is
B_m(q,kz)*conj(am*Hm(q,kz)). This is a direct scalar calculation on sparse
independently synthesized modes. Derive the negative filtered band by
all-axis conjugate reflection of the positive filtered band. There is no
fitted phase or scale.

Let j,i=0..15 and h=0..3. Output labels are x=(j-8)/4 um,
y=(i-8)/4 um, z=(h-2)*0.75 um. The expected image is the real native
zero-order finite inverse sum plus twice the real positive-side finite sum
multiplied by exp(+2*pi*i*(0.19*x+0.11*y)). The finite inverse terms use
exp(+2*pi*i*(kz*h/4 + ky*i/16 + kx*j/16)). They are unnormalized.
There is no fftshift/checkerboard and no division by 1024 output voxels.

## Explicit interpolation-first quotient comparison

This is a deliberately different, independently specified comparison, not
an alternate expected CE04 result. It uses the same raw bands, transfer,
carrier, modulation, w, cutoff, centered phase constant, and detector-count
units. It changes the order of relocation/interpolation and quotient.

1. Make full native unfiltered B0,B+,B- lattice arrays from the finite sums
   above. Set all other lattice coefficients to zero. Zero-extend them outside
   the native lattice. Both conceptual +-4 Nyquist endpoints are zero for this
   control, so their duplication has no effect and is not an endpoint rule
   claimed for CE04.
2. At every full output integer frequency (Kx,Ky)=(kx*0.25,ky*0.25), with
   kx,ky in {-7,...,8}, and kz in {-1,0,1,2}, set q_n=K-n*k0. Bilinearly
   interpolate the four zero-extended **unfiltered** native band coefficients
   at q_n/0.25 using floor and standard nonnegative bilinear weights. Axial
   interpolation is unnecessary. For |kz|>1, or |q_n|>R, its numerator is zero.
3. For each remaining n, evaluate the same declared radial Habs(n)(q_n,kz).
   Form N_n = interpolated(B_n)(q_n,kz)*conj(a_n*Habs(n)(q_n,kz)).
   Form one common positive D(K,kz)=w^2 + sum over signed n with |q_n|<R
   of |a_n*Habs(n)(q_n,kz)|^2. For this fixed control, all order-zero data
   numerators at an equality boundary are zero; hence a missing equality-only
   self power does not alter any nonzero numerator. No extrapolated H or
   out-of-support vertex is sampled.
4. Set C(K,kz)=sum_n exp(-2*pi*i*n*(0.19*2+0.11*2))*N_n/D.
   The constant preserves the same centered physical carrier origin, rather
   than introducing an unrelated origin difference.
5. Sum C times the positive unnormalized finite inverse exponential on the
   (4,16,16) output lattice. Take its real part, as CE04 takes a real image.
   Keep the imaginary residual as a diagnostic. Do not renormalize either
   image or match their peak/amplitude.

This explicitly compares interpolating raw bands before quotient with native
quotient before sampled carrier relocation. Linear interpolation also changes
the relocation representation; the caption must disclose that fact. The
figure cannot isolate quotient noncommutation from relocation interpolation.

## Precision budget and preregistered scales

Binary64 unit roundoff eps=2^-53. Use gamma(n)=n*eps/(1-n*eps).
All raw camera subtraction and alpha multiplication are exact dyadic
operations. |I-128|<=29, P=5, and alpha*X*Y*Z=1/4 give the loose unfiltered
coefficient bound 36.25 counts per real quadrature. H<=1.1, |a|<1,
D>=w^2=0.25; no inverse phase design or weak denominator is present.
Allow 2^14 real operations per finite-transform coefficient and a conservative
32*eps absolute envelope per bounded elementary complex phase. This gives
less than 2e-10 counts per prepared complex coefficient after including both
the observer and binary64 product paths. For the complete positive band the
two-quadrature error is <=4e-10 counts. Its weight modulus is <=3.52
(H<=1.1, |a|<0.8, D>=0.25); the zero-order weight modulus is <=4.4.
Allowing 256 operations for each short transfer/three-power quotient and its
denominator sensitivity leaves a conservative 2e-9-count error per complete
filtered band coefficient. The displayed filtered-quadrature budget below is
looser. Even allowing all 256 native coefficients rather than only the sparse
signal, assembly has <=256*(1+2)=768 weighted contributions, hence contributes
<=1.536e-6 counts from those coefficient errors. A further 2^15 assembly
operations on the loose absolute signal bound below 230 counts leave ample
room inside 4e-6 counts. A normalized 2D spectrum has operator norm one from
image max norm to each complex spectral coefficient, with its own short-sum
roundoff included in that slack.
They are practical fixed-branch bounds under the usual stable binary64
arithmetic/libm model, not a universal backend or historical binary guarantee.

```
prepared quadrature absolute tolerance: 2e-10 detector counts
filtered quadrature absolute tolerance: 5e-9 detector counts
image absolute tolerance:              4e-6 detector counts
normalized 2D spectrum tolerance:      4e-6 detector counts
relative tolerance:                   0
```

Normalized spectrum means the 2D negative-exponential finite Fourier sum of
the h=1 image plane divided by 16*16. Its complex values therefore retain
detector-count units. Use an identical operation for expected, product, and
comparison images. Display signed frequency labels in cycles/um; reorder
frequencies for plotting only. Do not shift image samples.

The figure uses the frozen h=1 plane (z=-0.75 um), with the following common
linear scales, selected before product observations:

| Panel kind | Fixed limits | Units |
| --- | --- | --- |
| Native expectation, product, comparison signed image | [-12,12] | detector counts |
| Native minus interpolation-first signed image | [-8,8] | detector counts |
| Expected/product/comparison spectrum magnitude | [0,4] | detector counts |
| Native minus comparison spectrum magnitude | [-2,2] | detector counts |
| Product minus native expected image | [-4e-6,4e-6] | detector counts |
| Product minus expected spectrum magnitude | [-4e-6,4e-6] | detector counts |

Use a diverging color map centered at zero for signed images/differences and
a sequential map for nonnegative magnitudes. Show clipping/overflow marks if
any fixed range is exceeded, with the numeric maximum stated; do not autoscale.
Report max absolute and root-mean-square image differences and max absolute
complex normalized-spectrum differences. The illustrative distinction is useful
only if the independent native/comparison image peak difference exceeds 0.05
counts and spectrum-magnitude peak difference exceeds 0.01 counts. If it does
not, report the control as uninformative; do not retrofit the thresholds.

Suggested caption: "A fixed signed raw-mode control with known parameters.
Native Fourier filtering followed by centered sampled carrier assembly agrees
with an independent finite-sum expectation (accuracy residuals use a separately
fixed micro-count scale). A common-frequency-grid comparison first bilinearly
interpolates unfiltered bands and then forms a quotient. Its signed image and
spectrum differ. The comparison changes relocation interpolation as well as
quotient order. Counts are detector-count units after the declared preparation;
the control makes no recovery, resolution, or historical binary claim."

## Remaining questions, records, and ownership

No material mathematical question is unresolved for this selected branch under
the four documents as read. The CE04 contract is still under source review.
Any accepted change affecting these equations invalidates this preregistration
until an explicit superseding freeze. Public-call signature/data-record details
must be checked by the coordinator against the accepted contract, not inferred
from product internals. Product observations must be separately timestamped and
must name the accepted contract/candidate identities.

Human numeric limits: not set. Model/effort/token/cost metering: unknown.
Author-created files are confined to this `figure` directory: this document,
and optionally an independent standard-library arithmetic script plus generated
JSON expectation/metrics. No product or long-running process is started.
No tracked files or shared environments are changed. Preserve this directory
as numerical presentation evidence until the coordinator decides its durable
destination; it is not disposable author scratch yet.
