# CE05: finite carrier search and complex modulation estimation

**Version 1.0. Independent source-contract acceptance precedes A.**

This expands CE05 of `c-equivalence-rebuild-v1.md` under
`c-equivalence-common-v1.md`. It depends on accepted CE02 preparation, CE03
complex transfer sampling and CE04 known-parameter reconstruction. It defines
only the selected ordinary stationary three-dimensional (3D) C estimation
mapping. No different optimizer, specimen solver, calibration fit, raw/file
workflow wrapper, drift correction or unselected acquisition mode is added.
Fresh native source-contract acceptance must precede blind A. Implementation,
tests and final review remain high risk A/B/C/D. All existing verification gates
and the full-local exact-candidate submission gate remain binding.

## Source identity and selected caller

The reference is retained SVN307, read statically, ignored and unshipped. The
following actual retained bytes were hashed on 2026-11-03. No retained C or
retired Python was executed, built, linked or imported. Mathematical mapping
and finite decisions are the target; bitwise or historical binary agreement is
unqualified. Effective historical external image/Fourier libraries and the
floating-point implementation of signed-zero math remain unqualified.

| Source | SHA-256 | Selected use |
| --- | --- | --- |
| `sirecon.c` | `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567` | Resolved guesses 386–415; caller 778–882; coarse search 1286–1369; overlaps 1382–1597; finite refinement 1609–1713; objective 1724–1743; regression 1849–1985 |
| `small_math_funcs.c` | `a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e` | `mag2` 7–12; periodic peak 285–318; clipped parabola 327–344; general parabola 351–375; accepted transfer sampler 396–483 |
| `helpers.c` | `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206` | Optics parser 145–166; recalc/floor/search options 251–300; phase/kz flags 336–358; defaults 505–540 |
| `sirecon.h` | `f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629` | Float vectors, parameter fields, `MAXPHASES=25`, warning constant 2 |
| `Makefile` | `1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4` | Ordinary non-TIFF source route, single-precision FFTW3 linkage |
| `usr_local/include/fftw3.h` | `8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d` | Forward sign -1, backward sign +1 |

Selected: one explicit wavelength/channel, ordinary stationary single-objective
3D, no input padding or drift, actual accepted CE02 quadratures, actual accepted
CE03 radial/full complex tables shared by directions, C's search/time-zero reuse
switches, optional positive modulation floors, fitted/all-order-derived phases
and omission of kz=0 during fitting. Direction and order counts are parameters
within the domain below. The initial useful case D=3,P=5,O=3 is included.

The source caller builds a common fundamental initial magnitude
`g=1/(linespacing_um*(nordersIn-1))` in 3D, and vectors
`g*(cos(theta_d),sin(theta_d))`. Angles are supplied or
`theta_start + sign*pi*d/D`. This boundary accepts those **resolved fundamental
vectors**, rather than inferring a line spacing or dividing a supplied vector
again. Separate resolved direction vectors may have different magnitudes: the
per-direction called mathematics has no cross-direction constraint on those
values. That general array boundary does not claim that every such collection
can be expressed by the historical main program's single line-spacing option.
The textual main-program percentage warning is outside the numerical result;
on the caller-reachable common-magnitude subset it compares
`norm(kfit-kguess)/g > 2`, literally, not a two-pixel criterion. The nested
time-zero fallback at source 818–832 is unreachable under its enclosing search
guard and is never a second fitting/recovery branch here.

## Public boundary, inputs and errors

```python
estimate_parameters(
    bands, transfer, *, initial_carriers_cyc_um,
    wavelength_nm, numerical_aperture, immersion_index,
    search_carriers=True, use_time0_carriers=True,
    amplitude_floors=None, fit_all_phases=True, omit_kz0=False,
) -> EstimatedParameters
```

New public names are `estimate_parameters`, `EstimatedParameters` and
`ParameterEstimationError`. The error subclasses existing `SimreconError`
(ValueError). Existing retired scientific functions/modules remain unavailable.
Python signature errors remain TypeError. Invalid domain, unsafe source
representation/stencil and undefined/nonfinite operation errors raise
ParameterEstimationError with nonempty text identifying the field/operation;
exact punctuation is not fixed. Allocation/backend errors retain their cause.
No partial result or input mutation escapes a failure.

| Input | Complete selected domain |
| --- | --- |
| `bands` | Actual valid `PreparedBands`, input shape `(T,D,P,Z,Y,X)`, Q=2*O-1<=P; T,D>=1, Z>=2, Y>=1, X>=2 even. O>=3 when search is on; O>=2 when it is off. Search always fits order pair (0,2), even if more than three orders are retained. Known fitting uses (0,b), b=1..O-1. |
| Used CE02 fields | `quadratures` complex128 `(T,D,Q,Z,Y,X//2+1)`, finite; `noise_variance_factors` float64 `(D,O)`, finite positive; valid input shape, sampling, integer zoom, source identities and `input_scale=1/(X*Y*Z*L**2*A*D)`. Noise factors/zoom/scale are retained for composition; the estimator applies no extra noise weighting or renormalization. Writable valid CE02 quadratures/noise are permitted. Other stage diagnostics are neither recomputed nor checked against raw inputs. |
| `transfer` | Actual valid accepted CE03 `OpticalTransfer`, at least O complete orders, radial or full, inherited complete-sample/metadata/source/dtype rules. Extra orders are unused; do not normalize/make real/duplicate orders. All actual samples use CE03 semantics with `dkz_cyc_um=1/(Z*dz_um)`. |
| `initial_carriers_cyc_um` | Real NumPy array `(D,2)` of finite fundamental (kx,ky), cycles per micrometre (cycles/um). Standard integer, float16/32/64 numeric kinds; no boolean/object/string/complex/extended kind. Components fit finite float32 magnitude but need not be exactly float32 representable. Strided/read-only arrays are accepted and copied. Negative components and unequal directions/magnitudes are permitted. Zero supplied known carriers are permitted when subsequent operations are defined. |
| Optics | Wavelength is an integer scalar (Python int or NumPy integer, never boolean), in nanometres, 1..32767. Numerical aperture (NA) and immersion index are finite nonboolean real scalars within float32 magnitude, `1<=immersion_index<=2`, `0<NA<=min(2,immersion_index)`. Endpoints are allowed. |
| Flags | Actual booleans. Defaults match selected C defaults: search on, reuse time-zero carrier on, all fitted phases on, omit-kz0 off. No `recalcarrays` control is exposed: the actual caller forces 1. |
| `amplitude_floors` | None disables floors exactly as source `forceamp[1]=0`. Otherwise a real numeric NumPy array `(O-1,)`, finite strictly positive components within float32 magnitude, same real kinds as initial carriers. No broadcasting or zero-as-disable elements. O<=25 when supplied because actual source `forceamp[1..O-1]` must fit its 25-element allocation. Do not read source uninitialized later floor entries when floors are disabled. |

All copied used input arrays remain unchanged. All outputs below use independently
owned binary64/complex128/read-only arrays; nested records and sequences are
immutable. This is a real-arithmetic contract evaluated in binary64, not a demand
to round intermediate estimates to C float32. Near support, threshold or strict
search decisions, finite-precision sensitivity remains explicit; tolerances may
not hide a changed decision procedure.

## Output and complete diagnostic observability

`EstimatedParameters` is frozen. At minimum it has these exact fields:

| Field | Shape/type and meaning |
| --- | --- |
| `carriers_cyc_um` | read-only float64 `(T,D,2)`, resolved fitted/reused/supplied fundamental carriers |
| `modulation` | read-only complex128 `(T,D,O-1)`, final factors after floors then phase policy; order zero is implicit 1 |
| `raw_modulation` | read-only complex128 `(T,D,O-1)`, forward factors before caller floor/phase operations |
| `initial_carriers_cyc_um` | read-only float64 `(D,2)`, exact validated supplied values |
| `branches` | immutable T-by-D tuple of strings `searched`, `known`, or `time0-reused`; search off always records `known` |
| `overlaps` | immutable tuple of the build records described below, in actual build order |
| `trace` | immutable tuple of finite-operation event records described below, in actual time/direction/operation order |
| `radial_cutoff_cyc_um`, `axial_cutoff_bins` | scalar R and integer c defined below |
| `resolved_settings` | immutable ordered `(name,value)` tuple: wavelength_nm, numerical_aperture, immersion_index, search_carriers, use_time0_carriers, amplitude_floors (None or immutable tuple), fit_all_phases, omit_kz0, dxy_um, dz_um, lateral_zoom, axial_zoom, input_scale |
| `source_revision`, `reference_sha256` | `SVN307` and the six source-name/hash pairs above in table order |

Each frozen overlap build record exposes `index`, `time_index`,
`direction_index`, `purpose` (`coarse`, `refinement`, `later-order`, `known`),
`orders`=(a,b), read-only float64 `carrier_cyc_um` shape(2), complex128
`fourier` shape `(2,Z,Y,X)` and `spatial` shape `(2,Z,Y,X)`. Fourier arrays are
the final zero/masked arrays immediately before unnormalized inverse; spatial
arrays are immediately after it. Its read-only boolean `written` of that same
shape records whether any successful threshold branch wrote each output address.
Repeated axial endpoint visits are resolved by the literal sequential writes,
not collapsed. Each build is retained separately, even if equal to an earlier
build. No later fitting mutates captured overlaps.

All three index fields are nonnegative Python integers; `orders` is a pair of
Python integers. The fixed purpose enumeration and array dtypes/shapes above
are part of the boundary. Record indices start at zero and refer to positions
in `overlaps`; no pointer/object-identity convention is used.

Each frozen trace event exposes `kind`, `time_index`, `direction_index`, and
`details`, an immutable ordered tuple of `(name,value)` pairs. Arrays in details
are owned/read-only. Required event types/keys are:

- `coarse`: overlap_index, correlation_complex `(Y,X)`, correlation_power
  `(Y,X)`, integer_peak_xy, x_neighbors, y_neighbors, x_offset, y_offset,
  x_offset_status, y_offset_status, peak_before_alias_xy,
  alias_decisions (four booleans in source order),
  peak_after_alias_xy, carrier_cyc_um. Neighbor arrays have three values in
  (-1,0,+1) order. The x/y fallback statuses distinguish zero curvature,
  outside-1.5 clipping and accepted offsets, using exactly `zero-curvature`,
  `outside-range`, `fitted`.
- `evaluation`: stage (`angle`, `magnitude`, `final`, `later-order`, `known`),
  orders, overlap_index, remake_overlaps, angle_rad/magnitude_cyc_um (None for
  direct known-vector evaluation), carrier_cyc_um, SX, SY, cross, forward,
  reverse, combined, correlation, objective. An evaluation is retained even
  when the carrier repeats. Raw reverse is C*/SY, not its display reciprocal.
  For direct known-vector fits, including time-zero reuse, objective is None
  and its square is not evaluated. Other evaluation stages pass through
  getmodamp and retain the finite squared-forward objective.
- `bracket`: stage, branch (`initial`, `positive`, `negative-swap`, `shift`, `stop`),
  x1,amp1,x2,amp2,x3,amp3 after that mutation, plus the strict comparison
  outcome. Include initial state, initial direction choice, every shift and
  terminal state; carry x1/amp1 into the magnitude initial state.
- `parabola`: stage, x1,y1,x2,y2,x3,y3, result, status (`duplicate-coordinate`,
  `zero-curvature`, `fitted`). Include no-curvature return-zero cases.
- `reuse`: source_time=0, carrier_cyc_um, with no coarse/refinement events.
- `adjustment`: order, raw_forward, floor (None or supplied value),
  floor_applied, after_floor, phase_replaced, final. One per positive order
  after fitting all orders, in ascending order.

`details` keys appear in the order listed for their event. Omitted/inapplicable
optional fields are explicitly None, not absent. Index/order fields are Python
integers, branch/status/stage values are the exact strings above, booleans are
actual bool, every real scalar is Python float representing binary64, and every
complex scalar is Python complex representing complex128. `correlation_complex`
is complex128; `correlation_power` is float64. Peak coordinates and carriers are
read-only float64 arrays shape(2), except `integer_peak_xy`, which is an immutable
pair of Python integers. Neighbor arrays are read-only float64 shape(3).
`alias_decisions` is a four-bool tuple. `orders` is a two-int tuple. All numeric
scalars in successful trace events are finite. A bracket stage is exactly
`angle` or `magnitude`; its six coordinate/objective scalars are floats and
its comparison key is exactly `strict_improvement` (bool). Emit `initial`
after both stage-start evaluations, direction-choice state after the initial
comparison/swap, `shift` after each full loop body/new evaluation, and `stop`
after the terminal false comparison. Repeated tests of the same true condition
need no duplicate event. The parabola `stage` is `angle` or `magnitude` and its
listed x/y/result fields are floats. Known-vector evaluation has both polar
fields None; search-based later-order evaluation retains its fitted angle and
magnitude. The reuse carrier and every evaluation carrier use shape(2) above.
Adjustment factors are complex, `floor` is float or None, and `order` is an
integer. No event schema or choice of diagnostic type is left to implementation.

Trace formatting adds no numerical branch. Raw numerical diagnostics below
are required. The external C printf reciprocal of reverse amplitude and spacing
`1/magnitude` are not estimator outputs. When zero makes such a *display*
quantity unavailable, do not invent a finite limit or reject otherwise defined
helper results merely to produce that text. The equal-energy helper singularity
below is different: it occurs inside the selected numerical helper and rejects.

## Exact overlaps and sampling short circuit

Write X,Y,Z for native dimensions, h=floor(X/2), v=floor(Y/2),
dx=1/(X*dxy), dy=1/(Y*dxy), dzf=1/(Z*dz). Signed lateral lift is
`q(j,N)=j if j<=floor(N/2), else j-N`; the even Nyquist lift is positive.
Let `lambda=(wavelength_nm/immersion_index)/1000` um,
`alpha=asin(NA/immersion_index)`,
`R=min(2*NA/(wavelength_nm/1000),1/(2*dxy))` cycles/um and
`c=ceil(((1-cos(alpha))/lambda)/dzf)`, converted to signed source integer.
If **c>floor(Z/2)** replace c by `max(floor(Z/2)-1,0)`. Equality does not
clip. This differs deliberately from CE04's cutoff clipping and is not a common
order-dependent cutoff scheme. For Z=2 or a cutoff exactly at an even axial
Nyquist, this distinction changes actual requests and writes.

For order pair (a,b), here always a=0, set
`delta=(b-a)*carrier` in cycles/um. Initialize both full Fourier overlap arrays
to zero. For each lateral array row i=0..Y-1, column j=0..X-1, let
`qxy=(q(j,X)*dx,q(i,Y)*dy)`, r=|qxy|, qminus=qxy-delta,
qplus=qxy+delta. Do nothing if r>R. Otherwise independently execute lower
branch then higher branch when their shifted radius is <=R. This is an
inclusive theoretical mask, with strict sampled-amplitude masks below.

The half-space read at (z,i,j) uses stored (z modulo Z,i,j) when j<=h.
For j>h, read ((-z) modulo Z,(-i) modulo Y,X-j) and conjugate **each
quadrature** before any transfer multiplication. For a positive order m form
`B_m=E_m+i*O_m` after that possible conjugation; order zero is its single
quadrature. Never conjugate Bplus as a whole instead of the quadratures.
Do not repair the CE02 unseparated lateral Nyquist slots.

For each selected branch loop integer z=-c..c in increasing order, skipping
z=0 entirely when omit_kz0. CE03 sample requests use the physical lateral
coordinates below and integer z with dkz=dzf. Let threshold tau=0.006 and
ordinary-3D scale F=5. The exact source short circuit is:

1. **Lower overlap:** only if |qminus|<=R, sample Ha(qxy,z). Only if
   `abs(Ha)>tau` sample Hb(qminus,z). Only if `F*abs(Hb)>tau` read the
   lower band and write
   `F_a[z%Z,i,j] = B_a(qxy,z)*Hb(qminus,z)/sqrt(abs(Ha)**2+abs(Hb)**2)`.
2. **Higher overlap:** only if |qplus|<=R, sample Hb(qxy,z). Only if
   `F*abs(Hb)>tau` sample Ha(qplus,z). Only if `abs(Ha)>tau` read the
   higher band and write
   `F_b[z%Z,i,j] = B_b(qxy,z)*Ha(qplus,z)/sqrt(abs(Hb)**2+abs(Ha)**2)`.

Factor 5 is only a **threshold** scale of the higher-order transfer, not an
extra overlap multiplication or denominator weight. Threshold equality rejects.
Weights contain the complex other transfer itself: no magnitude, conjugate or
cross-power replacement. No sample request is made in a failed earlier
theoretical/threshold/omit-kz0 branch. Conversely every requested interpolation
vertex is required by CE03 even if band data are zero. An unsafe request
rejects instead of substituting zero or extending a table.

At c=Z/2 for even Z, -Z/2 and +Z/2 map to the same output plane. Keep both
requests, in that order. A later *successful* write replaces the earlier value;
a later failed threshold leaves the earlier value. This also applies to the
diagnostic written mask. Source positive x/y Nyquist choices remain independent
of this axial visitation rule.

Transform each F by the full complex unnormalized backward sum
`O[h,i,j]=sum_(z,y,x) F[z,y,x]*exp(+2*pi*i*(z*h/Z+y*i/Y+x*j/X))`.
A normalized library inverse must be multiplied by X*Y*Z. No fftshift,
checkerboard, gain normalization, order-noise factor or overlap whitening occurs.

## Regression, objective and defined-helper domain

At candidate fundamental k, retain the chosen overlap pair X=Oa and set
`Y[z,i,j]=Ob[z,i,j]*exp(+2*pi*i*(b-a)*dxy*((j-floor(Xdim/2))*kx+(i-floor(Ydim/2))*ky))`.
The phase has positive sign and centered lateral coordinates. It is independent
of z. To avoid symbol ambiguity below, SX/SY sum over all native voxels.

```
SX = sum abs(X)**2
SY = sum abs(Y)**2
C  = sum conj(X)*Y
forward = C/SX
reverse = conj(C)/SY
objective = abs(forward)**2  # only through getmodamp; direct known fit: None
t = 2*abs(C)/(SX-SY)
beta = 0.5*atan(t)
if beta < 0: beta += pi/2
combined = tan(beta)*exp(i*arg(C))
correlation = sqrt(abs(C)**2/(SX*SY))
```

The last correlation is uncentered. Source calculates means and then does not
subtract them; do not install a centered Pearson correlation. Its correlation
reduction is performed again in the source but is the same finite sum in real
arithmetic. Preserve the positive square root, not correlation power. The
search uses only `objective` from **forward**, never reverse, combined,
correlation, a residual norm, normalized correlation or an amplitude floor.
Direct known-vector callers do not compute this objective; a finite forward
factor is not rejected merely because its unused square would overflow.
The signed SX-SY division and atan branch must not be replaced by atan2 or a
symmetric principal-component formula.

The selected numerical helper always evaluates reverse, combined and correlation,
including search probes whose caller discards them. At each actual evaluation
require finite SX>0, SY>0 and SX!=SY, and finite defined resulting arithmetic.
Thus entirely absent overlap/one zero band rejects; so does equal-energy
overlap, including an exact unit-gain equal-energy case. This explicit source
singularity is not a weak-signal floor and gives no numeric reference on that
excluded domain. Arbitrarily small positive nonzero unequal energies remain
admissible when binary64 operations resolve finitely. No epsilon-based exclusion
or regularizer is permitted.

With SX,SY positive unequal and C=0, forward=reverse=correlation=0.
The objective is zero when getmodamp computes it; it remains None for direct
known-vector fits, including time-zero reuse, without evaluating the square.
The combined factor is also zero, independently of an irrelevant phase assigned
to its zero magnitude. Represent combined as exact complex zero. The helper's
zero factor is distinguished from its external printf's undefined reciprocal
amplitude display. A positive requested amplitude floor on a final zero forward
factor is a separate actual source division by zero and rejects at that later
caller operation. No nonzero phase or finite reciprocal is invented.

Known-vector k=(0,0) has a defined zero phase ramp and may succeed. Search takes
a polar angle of the coarse result; if that vector is exactly zero, reject at
that actual polar conversion as an undefined real-arithmetic atan2(0,0), rather
than inventing an angle. The historical signed-zero/libm result is not qualified.
Zero/negative magnitudes returned later by the *defined* general parabola are
retained; the Cartesian conversion and final phase ramp use that value literally.
No magnitude clipping or extra angular iteration occurs.

## Coarse carrier search

For every searched (t,d), build (0,2) overlaps at the supplied initial carrier.
Let
`V[i,j]=sum_z O0[z,i,j]*conj(O2[z,i,j])`, and calculate the unnormalized
2D forward transform `Ccorr[u,v]=sum_(i,j) V[i,j]*exp(-2*pi*i*(u*i/Y+v*j/X))`.
Let W=abs(Ccorr)**2. Scan i increasing then j increasing, initialized maximum
-1e11; replace only when W[i,j] is strictly greater. For finite nonnegative W,
this chooses the first row-major maximum, including all-zero/tied maps.

At integer peak (j0,i0), obtain periodic immediate x neighbors on row i0 and
periodic immediate y neighbors on column j0. Refine each independently with
`s=(a_plus-a_minus)/2`, `curv=a_plus+a_minus-2*a_center`. If curv==0 return
offset 0. Otherwise p=-s/curv; if p>1.5 or p<-1.5 return 0; otherwise retain
p, including exactly +/-1.5. No clipping to +/-0.5, 2D joint parabola or log
power fit occurs. Set px=j0+p_x, py=i0+p_y before alias handling.

The outside-1.5 helper fallback and accepted +/-1.5 endpoints are unreachable
after selection of a finite global maximum in this real-arithmetic mapping.
Write u=a_center-a_minus>=0 and v=a_center-a_plus>=0. If u+v=0, curvature
is zero. Otherwise the offset is `(u-v)/(2*(u+v))`, whose absolute value is
at most 0.5. Preserve the literal helper rule, but discharge its unreachable
coarse branches by this proof, without a test-only helper seam. This proof
does not establish reachability of later general-parabola outcomes.

Retain these four literal tests, sequentially, with changed px/py visible to
later tests:

```
if initial_kx*dx < px - floor(X/2): px -= X
if initial_kx*dx > px + floor(X/2): px += X
if initial_ky*dy < py - floor(Y/2): py -= Y
if initial_ky*dy > py + floor(Y/2): py += Y
coarse_k = (px*dx/2, py*dy/2)
```

This deliberately preserves the source `old_k0*dk` multiplication. old_k0 and
dk both have cycles/um units, so the comparison's left side has squared
frequency units while px/py are pixel-bin coordinates. It is a defined numerical
quirk, not a dimensionally corrected nearest-alias rule. The half dimensions
are C **integer division**; preserve odd-Y floor behavior and strict equality.
Do not divide old_k0 by dk or multiply by fitorder2 before comparing. The final
division by fitorder2=2 converts the coarse pair separation to a fundamental.

## Literal angle-then-magnitude refinement

At the coarse carrier, obtain mag0=norm(coarse_k) and
angle0=atan2(coarse_ky,coarse_kx), with the real principal angle in (-pi,pi]
(negative x axis at zero y gives +pi). Main forces recalcarrays=1 immediately
before this refinement. First angle evaluation **remakes** (0,2) overlaps at
the coarse carrier; freeze that pair for every remaining angle probe,
magnitude probe and final selected evaluation. Do not reuse the initial coarse
overlap or remake it at each candidate or at the final carrier. Other-order
fits later each remake their own overlap at the final carrier.

Use step da=0.001 radians, dm=0.1/(max(X,Y)*dxy) cycles/um.
Initialize x1=0 and amp1=0 **once**, before angle search. At fixed mag0 set
x2=angle0, amp2=objective(angle0,mag0), x3=angle0+da,
amp3=objective(x3,mag0). The exact direction/bracket procedure is:

```
if amp3 > amp2:
    candidate = angle0 + da
    while amp3 > amp2:
        amp1,x1 = amp2,x2
        amp2,x2 = amp3,x3
        candidate += da
        x3 = candidate
        amp3 = objective(candidate,mag0)
else:
    candidate = angle0
    swap(amp2,amp3); swap(x2,x3)
    while amp3 > amp2:
        amp1,x1 = amp2,x2
        amp2,x2 = amp3,x3
        candidate -= da
        x3 = candidate
        amp3 = objective(candidate,mag0)
angle = general_parabola(x1,amp1,x2,amp2,x3,amp3)
```

Every branch/continuation uses strict >. On an **initial tie**, take else,
swap the two pairs, perform no loop iteration, and use the still-initial
(x1,amp1)=(0,0) in the parabola. Do not evaluate the negative neighbor merely
to make a symmetric bracket. On a subsequent tie, stop at that comparison.

Now search magnitude at fixed fitted angle. **Do not reset x1 or amp1.**
Set x2=mag0, amp2=objective(angle,mag0), x3=mag0+dm,
amp3=objective(angle,x3). Apply the identical procedure with candidate=mag0+dm
and increments +dm in its positive branch; candidate=mag0, swap, then
increments -dm in its else branch. In the initial magnitude tie case, the
parabola consumes the x1/amp1 left by the angle stage (including zero if the
angle initial tie never shifted). These stale values may have angle units but
are used literally as a magnitude coordinate/value pair. This source quirk
must not be repaired by constructing a new bracket or isolating a clean generic
maximizer. Finally `mag=general_parabola(x1,amp1,x2,amp2,x3,amp3)`.

The general parabola has the following exact finite procedure. For
(x1,y1),(x2,y2),(x3,y3), return 0 immediately if any coordinates are equal.
Otherwise set b1=(x1+x2)/2, b2=(x2+x3)/2,
s1=(y2-y1)/(x2-x1), s2=(y3-y2)/(x3-x2),
curv=(s2-s1)/(b2-b1). If curv==0 return 0. Otherwise return
`b2-s2/curv`. There is no clipping to the bracket, maximum-curvature-sign
check or fallback to the sampled best point. A fitted zero is a source result.
All actually evaluated divisions/intermediates must be finite and defined.

Evaluate objective and all regression diagnostics once more at (angle,mag),
using the same frozen (0,2) overlap. Assign that forward factor to order 2.
Set final carrier `(mag*cos(angle),mag*sin(angle))`. In ascending order
b=1..O-1 excluding 2, remake (0,b) overlaps at that final carrier and evaluate
their forward factors there. Do not replace the final order-2 factor with one
computed from newly built final-carrier overlaps.

The loops have no extra convergence tolerance, optimizer or task-invented
evaluation quota. A representationally stagnant candidate increment, nonfinite
candidate/intermediate, impossible trace/output representation or backend
failure is an operation error, never a successful truncation. Tests must choose
source-domain finite paths; an external timeout is incomplete evidence.

## Time policy, known carriers and caller modulation adjustments

Traverse t then d. With search enabled, search every time/direction unless
t>0 and use_time0_carriers. At t=0 retain each final searched carrier. For a
reused later time, use that exact t=0 carrier and perform **fresh** known-vector
(0,b) overlap builds and fits for every b=1..O-1 at that time's data. No coarse
or refinement search occurs and no time-zero amplitudes are reused. With reuse
off, each time's search starts at the declared initial vector, not the preceding
time's fitted result. With search off, all times use supplied initial vectors
and known (0,b) fits; use_time0_carriers has no numerical effect.

At every time/direction, finish all raw order fits first. Then for b ascending,
if floors enabled and `abs(raw_b)<floor_b`, apply the literal positive-real
scale `floor_b/abs(raw_b)` to the complex factor. Equality leaves it unchanged.
If abs(raw_b)==0 this selected division is undefined and rejects; no phase is
invented. Larger magnitudes are preserved. Record both raw and final factors.

After floors, if fit_all_phases is false, set phi=arg(order1 factor) and for
b>=2 replace the factor by `abs(after_floor_b)*exp(i*b*phi)`. Preserve each
magnitude and order1 factor. There is no extra pi*(b-1), wrapped-parameter fit
or dependence on an already replaced higher order. If order1 is zero, phase is
undefined at this **actually selected** phase-replacement operation and rejects.
The source evaluates this base phase before the higher-order loop, so this
rejection also applies with O=2 and fit_all_phases false even though that loop
is empty. No restriction applies merely because fit_all_phases false when
order1 is nonzero.
With all phases fitted, zero factors with floors disabled remain permitted.
The 2D adjacent-pair product conversion at source 855–857 is unselected and
must not be applied to 3D factors.

## Representation and operation failures

Validate complete used records and declared arrays before numerical work. For
every actual source signed-int expression, require signed32 representability:
dimensions, Q/P/order products, native X*Y, X*Y*Z,
`(X//2+1)*Y*Z`, all flattened input/output offsets, axial cutoff before cast,
sampler grid products/indices and reflected/wrapped sums such as z+Z. Source
malloc byte expressions use sizeof and unsigned size_t; they do not introduce
an invented signed32 byte cap. Required 64-bit platforms still require all
such byte extents and each target NumPy float64/complex128/bool shape/stride to
fit platform intp, including aggregate T/D diagnostics and finite trace arrays.
Use nonoverflowing arithmetic for these checks. No fixture-size, total trace,
minimum signal or smaller arbitrary memory cap is introduced. Actual allocation
failure within this domain is an operation error.

Reject derived nonfinite dx/dy/dzf, optical asin/cutoff arithmetic, unsafe CE03
requests, undefined regression arithmetic, undefined polar/selected phase
conversion, singular floor scaling, unresolved finite-search step or
parabola arithmetic, overflow and allocation/transform/backend failure. Preserve
distinct informative reasons for no lower energy, no higher energy,
equal-energy combined-fit singularity, unsafe stencil and other failures.
None is converted to zero, an initial-guess fallback, omitted direction/order,
unavailable whole result or an alternate optimizer. A failure in any time/order
rejects the entire call. Printed-display quantities alone are not numerical
helper domain failures, as distinguished above.

## Public composition into CE04

The CE04 signature intentionally accepts `(D,2)` carriers and `(D,O-1)`
modulations shared across the time axis of one call. CE05 does **not** silently
extend that accepted signature. Public composition makes one accepted
PreparedBands record per time: replace its quadratures with an owned copy of
`original.quadratures[t:t+1]`, input_shape time dimension with 1, and time-indexed
stage diagnostics with matching slices (sentinel events select t and relabel
time to zero). Preserve all direction/phase/order/spatial axes, camera state,
noise, source metadata, sampling, zoom and **the same alpha**, since alpha is
independent of T. No raw preparation replay or rescale occurs. CE04 checks used
fields as its own contract specifies. An ordinary public value-record
construction/replacement suffices; no new scientific wrapper is needed.

Call `reconstruct_known(one_time_bands, transfer,
carriers_cyc_um=estimate.carriers_cyc_um[t],
modulation=estimate.modulation[t], ...)` with explicit accepted CE04 filtering
configuration and the same optics. The accepted returned image has leading
time length 1. Compare/stack those per-time images for the public composition
proof; this is test/caller composition, not a new runtime workflow feature.
In particular, later reused-time carrier fits still use their own newly fitted
modulation. CE07 will later own the raw/file end-to-end entry.

This proof uses the intersection of both stages' domains. Successful CE05
estimation does not guarantee that CE04 accepts every resulting parameter or
sampling request. CE04 retains its own parameter-magnitude, optical-angle,
extent, filtering and interpolation checks. Do not clip, refit or rescale an
estimate to force reconstruction acceptance.

## Distinct scenarios and acceptance obligations

| ID | Observable obligation or outcome |
| --- | --- |
| E01 | Independent public raw preparation -> accepted transfer -> estimation -> per-time CE04 composition; consumes actual estimated values |
| E02 | Known-vector path, including signed/zero carriers and positive/zero raw factors where actual arithmetic is defined |
| E03 | Search fixed (0,2) pair, O>=3 and later-order ascending (0,b) fits; reject insufficient O only in searching mode |
| E04 | Search defaults/time0 reuse: per-time modulation refits; search-all resets to initial; no unreachable fallback |
| E05 | Common-magnitude historical guess conversion versus explicitly resolved fundamental vector input; no extra factor2 |
| E06 | Inclusive theoretical radial masks and independent lower/higher shifted overlaps; no one-common-mask substitution |
| E07 | Strict threshold equality, factor5 only on higher transfer, first-threshold short circuit before second sample |
| E08 | Omit-kz0 skips both overlap branches before sampling; known fits reject absent energy in regression, while search can reject earlier at zero coarse-vector polar conversion; no invented carrier |
| E09 | Shared ceil cutoff with strict > clipping, small Z, exact even axial endpoint and last-successful-write semantics |
| E10 | Complex cross-transfer weights and no conjugate/magnitude replacement; denominator unscaled by factor5 |
| E11 | Full-complex overlap, all-axis half-space reflection of each quadrature, native positive lateral Nyquist and CE02 unseparated endpoint |
| E12 | Unnormalized 3D backward sum and 2D forward coarse sum; no averaging over z or transform-size normalization |
| E13 | Coarse first-strict row-major maximum, periodic neighbors, zero curvature and fitted offsets within [-0.5,0.5]; outside-1.5 fallback and +/-1.5 endpoints are unreachable by the stated global-maximum proof |
| E14 | Literal old_k0*dk alias sequence, strict comparison equality, source integer floor half sizes including odd Y |
| E15 | Positive centered phase ramp and pair separation factor; anisotropic dz versus lateral dxy |
| E16 | Forward complex regression and actual getmodamp objective distinguished from reverse, combined, uncentered correlation and residual/normalized substitutes; direct known fits do not compute the objective |
| E17 | Angle positive and negative searches, initial tie swap/no loop, later tie stop, exact bracket state |
| E18 | Magnitude search after one angle pass, literal steps, stale cross-stage x1/amp1 including initial magnitude tie |
| E19 | General parabola duplicate-coordinate/zero-curvature return0 and unbounded extrapolation without clipping |
| E20 | Caller recalc=1: remade coarse-carrier entry overlaps then frozen probes/final order2; final-carrier overlaps only for other orders |
| E21 | Positive floor below/equal/above branches; zero-floor rejection and no silent phase invention |
| E22 | Higher-order phase replacement after floors, order1 multiplier, preserved magnitudes and no saturation pi shift |
| E23 | Whole-call no-energy/equal-energy/selected-zero-phase errors versus valid weak unequal energies and zero cross |
| E24 | Zero coarse vector rejection only at actual polar conversion; valid known zero vector; no signed-zero ABI claim |
| E25 | Complete immutable trace, preserved separate builds/raw factors, owned read-only output and input immutability |
| E26 | Valid strided/read-only/mutated-allowed CE02 inputs, radial/full complex tables, extra unused transfer orders and no hidden raw replay |
| E27 | Invalid used record/shape/kind/finite/source/scale/sampling/noise fields; explicit optics/carrier/floor/flag domains |
| E28 | Actual unsafe interpolation stencil, signed32 address/cutoff and intp shape/stride/byte limits; positive domain/backend failures |
| E29 | All retired functions stay retired; documentation separates finite math, singular exclusions, binary agreement, recovery and resolution |

A maps each obligation/high-risk path, credible wrong outcome, distinct gap in
stronger public proof, independent oracle and predeclared tolerance. Independent
finite sums/algebra and finite trace expectations lead. Production helper reuse,
retired source execution, fitted gains/registration, tolerance tuning or replay
through a shared forward model do not qualify. Initially passing current-code
tests remain valid; no red test is manufactured. B challenges omissions, legitimate
positive inputs and whether a proposed discriminator is actually reachable in
this public domain. Duplicate/zero-curvature refinement returns require valid
public paths or explicit evidence that source-domain rejection makes that path
unreachable; no test-only objective/helper seam is authorized.

Coverage remains approved behavior plus independent risk review, with unselected
percentages advisory. All installed complete reports/platform gates remain.
Canonical `make verify` includes its 13 existing phases, strict outcomes,
two workers, wheel/import/audit and same-run M25 conversion memory evidence
<=33,554,432 bytes. The exact candidate must pass full local verification before any PR opening
(draft included) or push to an open PR. Required original Ubuntu 24.04/macOS 15
evidence and fresh D precede readiness. No dependency,
test-discovery, coverage, infrastructure or delivery-policy change follows.

Defined deferred modes: 2D and adjacent-order products; Bessel/two-objective;
drift and input padding; CE06 remaining options; CE07 workflow/files and CE08
physical recovery. Unsafe/undefined source branches stay explicitly excluded.
No binary-output equivalence or recovered-resolution claim follows from this
contract. Human numeric execution/review/scenario limits are not set. Scientific roles request gpt-6.1-sol/high under project calibration; actual
served identity/effort and unavailable metering remain unknown.
