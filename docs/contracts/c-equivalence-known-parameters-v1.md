# CE04: known-parameter native filtering and sampled assembly

**Version 1.0. Source-contract review precedes blind tests.**

This expands CE04 of [the stage contract](c-equivalence-rebuild-v1.md) under
[the common contract](c-equivalence-common-v1.md). The owner authorized this
known-parameter stage, fresh native source review and A/B/C/D, full exact local
verification, original Ubuntu 24.04/macOS 15 qualification and a ready stacked
pull request. No merge, release or CE05 execution is authorized.

## Source and selected branch

The target is retained SVN307, read statically, ignored and unshipped. The source
pins below are content identities, not evidence of an effective historical binary
runtime. Retained C is never built, run, linked or imported. Historical external
Fourier-transform and image-header libraries remain unqualified.

| Source | SHA-256 | Selected operation |
| --- | --- | --- |
| `sirecon.c` | `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567` | Caller 919–958; order-zero damping 1987–1995; filter 2005–2323; assembly/move 2334–2493 |
| `small_math_funcs.c` | `a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e` | Suppression 381–394; transfer sampling 396–483 |
| `helpers.c` | `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206` | Parser and default filtering parameters |
| `sirecon.h` | `f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629` | Source parameter/index representations |
| `Makefile` | `1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4` | Ordinary non-TIFF build routing |
| `usr_local/include/fftw3.h` | `8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d` | Backward transform sign and unnormalized convention |

Selected: ordinary stationary single-objective 3D, accepted CE02 preparation,
accepted CE03 radial/full transfers shared across directions, supplied carriers
and complex side-order modulation, positive explicit Wiener parameter, integer
output zoom, all signed overlap weights, suppression on/off with declared radius,
cosine/no output taper and the source order-zero options below. Time points are
independent with shared supplied parameters. No nuisance estimation, drift,
axial input padding, exploded view, precise 2D boundary, power taper, two-objective
or Bessel path is selected. The source caller's normal overlap flag is true and
normal explode factor is one. No arbitrary mask or iterative specimen solver
substitutes for these branches.

## Public boundary and records

```python
reconstruct_known(
    bands, transfer, *, carriers_cyc_um, modulation,
    wavelength_nm, numerical_aperture, immersion_index, wiener,
    suppress_singularities=True, suppression_radius_bins=10.0,
    dampen_order0=False, omit_order0=False, omit_kz0=False,
    output_taper="cosine",
) -> KnownReconstruction
```

These are new names; the old `reconstruct`, `reconstruct_volume`,
`simrecon._reconstruction`, `prepare_otf` and `simrecon._otf` remain retired.
Implementation belongs in new `simrecon.reconstruction.known_parameters` and public
bindings. No retirement gate is changed.

`bands` is an actual `PreparedBands` with the CE02 public record layout. Let
its input shape be `(T,D,P,Z,Y,X)`, Q=2*O-1 and O>=2. Z>=2, X>=2 even,
Y>=1, T,D>=1, Q<=P. Its used fields are `quadratures` complex128
`(T,D,Q,Z,Y,X//2+1)`, `noise_variance_factors` float64 `(D,O)`, input shape,
`input_scale`, dxy/dz and both integer zooms. They must have valid CE02 kinds,
shapes, finite values, positive noise factors/sampling/scale and source identity.
Unused CE02 stage diagnostics are not recomputed or checked against raw images.
The record's documented writable quadratures/noise may be changed by callers;
finite values satisfying the used-field domain remain valid. No raw-data replay
or hidden consistency checksum is required. Reconstruction copies used arrays
and never changes the record or any input. CE02's original normalization is
retained: alpha=1/(X*Y*Z*L²*A*D), where L is lateral zoom and A axial zoom.
The scale field must agree with this declared normalization. No additional
rescale, direction average or phase division is applied.

`transfer` is an actual valid `OpticalTransfer`, produced by `declare_otf` or
`prepare_bead_otf(...).transfer`, with at least O orders. It inherits the CE03
complete-table, metadata, dtype, actual-stencil and representation rules. Extra
orders are unused; the table is neither normalized nor made real here. Sampling
must compose through the accepted CE03 operation with native axial step below.
All actual sampling requests, including zero-data/zero-modulation/zero-damping
requests, retain every source interpolation vertex and source safety rule.

`carriers_cyc_um` is a finite real NumPy array `(D,2)` of supplied fundamental
carrier (kx,ky), in cycles per micrometre (cycles/um). A highest-order carrier
is not supplied instead. Zero carriers and unequal directions are allowed.
`modulation` is a finite real/complex NumPy array `(D,O-1)` for positive side
orders 1..O-1; a[d,0]=1 is implicit. Zero and signed/complex modulations are
allowed. No phase fit, amplitude floor or inverse-modulation substitute occurs.
Both arrays accept standard integer/float16/32/64 or complex64/128 kinds as
appropriate, never bool/object/string/extended precision; values must fit
finite float32 component magnitude but need not be exactly float32-representable.
This is the declared real mathematical input domain, evaluated in binary64.

Wavelength is a positive integer in nanometres, <=32767 (the selected source
signed-short declaration). Numerical aperture (NA), immersion index, Wiener
parameter w and radius are finite real scalars within float32 magnitude, never
booleans. The selected caller requires 1<=immersion<=2 and
0<NA<=min(2,immersion); w>0. Radius may be signed: a negative
radius selects no suppressed sample. All flags are actual booleans. Taper is
exactly `"cosine"` or `"none"`; no caller mask or arbitrary callable. Python
signature errors remain TypeError; domain/operation failures raise new
`ReconstructionError`, a subclass of existing `SimreconError` (ValueError), naming
the offending argument or failed operation. Exact punctuation is not fixed.
No partial result or changed input escapes. Allocation/transform/backend failures
are translated with their original cause. No arbitrary tiny-positive floor or
fixture-size cap is added.

`KnownReconstruction` is frozen and contains:

| Field | Shape/type and meaning |
| --- | --- |
| `image` | owned read-only float64 `(T,A*Z,L*Y,L*X)`, signed sampled output |
| `filtered_quadratures` | owned read-only complex128 with the input quadrature shape, after source filtering/recombination including untouched-row quirks |
| `x_um`, `y_um`, `z_um` | owned read-only float64 coordinate vectors of output axis lengths |
| `carriers_cyc_um` | owned read-only float64 `(D,2)` supplied parameters |
| `modulation` | owned read-only complex128 `(D,O-1)` supplied side parameters |
| `radial_cutoff_cyc_um` | scalar R below |
| `axial_cutoffs_bins` | owned read-only integer `(O,)` C cutoffs c below |
| `resolved_settings` | immutable tuple of (name,value) pairs with the exact keys below |
| `source_revision`, `reference_sha256` | `"SVN307"` and the six source-name/hash pairs above in table order |

The resolved-setting keys, in order, are `wavelength_nm`, `numerical_aperture`,
`immersion_index`, `wiener`, `suppress_singularities`, `suppression_radius_bins`,
`dampen_order0`, `omit_order0`, `omit_kz0`, `output_taper`, `dxy_um`, `dz_um`,
`lateral_zoom`, `axial_zoom`, `input_scale`. Values are the validated supplied
or inherited scalars/flags/string, without inferred or fitted parameters.

Output spacing is dxy/L laterally and dz/A axially. Physical coordinate labels
are `(j-floor(L*X/2))*dxy/L`, `(i-floor(L*Y/2))*dxy/L`,
`(h-floor(A*Z/2))*dz/A`. Assembly uses these centered lateral labels. The inverse
array itself is not shifted: unshifted inverse indices h,i,j are used below.
Its origin convention is inherited from CE02, not repaired by a checkerboard or
fftshift. Intensities are in input detector-count units after the declared camera,
equalization, phase and C scale operations. They are not calibrated specimen mass.
Negative image values are retained.

## Support, weights and taper

Let dx=1/(X*dxy), dy=1/(Y*dxy), dzf=1/(Z*dz), b=|k0[0]|,
le=(wavelength_nm/immersion_index)/1000 um and lx=0.88*le.
Let theta=asin(NA/immersion_index) and
R=min(2*NA/(wavelength_nm/1000),1/(2*dxy)) cycles/um.
The source also evaluates beta=asin(b*lx/2) and
betamin=asin(b*lx/2-0.1*sin(theta)). Require both arguments in [-1,1] even
though the ordinary branch does not use the resulting angles. No nonfinite
source intermediate supplies an oracle.

First set c0=ceil(((1-cos(theta))/le)/dzf), c[O-1]=trunc(1.3*c0),
and c[m]=trunc((1+le/lx)*c0) for 1<=m<O-1. c[0]=c0.
Then independently for every order, if c[m]>=floor(Z/2), replace it by
max(floor(Z/2)-1,0). Ceil precedes integer truncation and clipping. There is
no common axial cutoff. With O=2 the only side cutoff is the 1.3 high-order
case. O=1 would access source c[1] outside allocation and is unsupported here.

Let sr=suppression_radius_bins*min(dx,dy), Rp=R+b*(O-1), Zp=c[1].
The suppression factor at native physical radius r is
s(r)=1/(1+1000/(r²+0.2)); its radius argument is unused inside the helper.
The radius parameter still controls the outer r<=sr application condition.
Do not replace physical r by the bin radius or normalize r by sr.

For noise variance v[d,m]>0 define g[d,m](r,z) initially 1/v[d,m].
Apply the following ordered branches:

1. If suppression is on, m!=0 and r<=sr, multiply by s(r).
2. Else if m==0, suppression is on, neither dampen nor omit order zero is on,
   and r<=sr, multiply by s(r).
3. Else if m==0 and dampen_order0 is on, multiply by
   `(r/R)²+abs(z/c[0])³`. Whenever this expression is actually evaluated it
   requires c[0]>0. For Y=1 the empty filter traversal evaluates no damping.
4. Else if m==0 and omit_order0 is on, set g=0.
5. After those branches, if m==0,z==0 and omit_kz0 is on, set g=0.

Dampening takes precedence over omission in the weight branch when both are
true; final assembly still omits order zero. Other-order damping is evaluated
at the self sample's z, without imposing that other order's axial cutoff.

At self direction/order (d,m), native k=(x*dx,y*dy,z*dzf), set
Kxy=(x*dx,y*dy)+m*k0[d]. H1 is CE03 sample of order m at the native coordinates
and integer z, using dkz_cyc_um=dzf. Its self power is
`|H1|²*|a[d,m]|²*g[d,m](r,z)`, with a[d,0]=1.
Initialize denominator to that self power. In direction order e=0..D-1 and
signed order n=-(O-1)..O-1, skip only (e,n)=(d,m). For each remaining term set
qxy=Kxy-n*k0[e] and q=|qxy|. Include it iff q<R (strict). Sample
H2=H[abs(n)](qxy,z) through CE03 and add
`|H2|²*|a[e,abs(n)]|²*g[e,abs(n)](q,z)`.
There is no other-order axial test, no negative-order complex conjugation of
this power, and no covariance matrix. Add w² last. The selected overlap flag
is always true. Nonfinite/zero denominator or nonfinite scale/result rejects.

For taper none, T=1. For cosine taper, let rabs=|Kxy| and
rho=sqrt((rabs/Rp)²+(abs(z)/Zp)²) if Zp>0, otherwise rho=rabs/Rp.
Clip rho above at one and set T=cos(pi*rho/2). Use the shifted object frequency
and self integer axial bin; this taper multiplies the numerator after division.
There is no idealized hard-zero substitution at rho=1, and no precise 2D petal
boundary in this branch.

The applied native scale is
`T*g[d,m](r,z)*conj(H1)/denominator`, additionally multiplied by
conj(a[d,m]) for m>0. Both numerator and every eligible denominator power carry
the damping factor, once each; w is squared. Locally one eligible unit term,
unit data/transfer, no taper/suppression and w=0.5 gives 1/1.25=0.8.
With damping 0.1 and w=1 it gives 0.1/1.1=1/11, not 0.05. These checks
do not replace complete signed-band-to-image expectations.

## Literal native traversal, conjugate partners and odd-height quirk

For each time and direction, copy the original half-space quadratures. Let
xc=floor(X/2), yc=floor(Y/2), and VY={-(yc-1),...,yc}; this set is empty
when Y=1. For each order m visit y in VY then x in {-(xc-1),...,xc}.
For x>=0 use half-space (y modulo Y,x), conjugation flag false; for x<0 use
(-y modulo Y,-x), conjugation flag true. Order zero skips x<0 entirely.

At r=sqrt((x*dx)²+(y*dy)²)<=R (inclusive) visit
z=-c[m]..c[m]. Read the half-space quadratures at axial bin z modulo Z if
unreflected and -z modulo Z if reflected. Conjugate each read quadrature in
the reflected case. For m=0 multiply that stored complex coefficient by its
native scale. For m>0 form Bplus=E+i*O from the two complex quadratures,
multiply by the native scale, and put the value in a zero-initialized full
temporary F at (z modulo Z,y modulo Y,x modulo X).

If r>R, zero the addressed stored half-space quadrature(s) at every
z=-c[m]..c[m], using z modulo Z (the source's outside-support branch).
For every visited x,y, also zero stored axial indices c[m]+1..Z-c[m]-1.
Those writes operate on the half-space address chosen above. Preserve them
even on reflected side visits. No sampling occurs in the outside-self branch.

After all side-order visits, recombine at y in VY and x=0..xc,
z=-c[m]..c[m]. Let p=F(z,y,x), n=conj(F(-z,-y,-x)), with all array indices
wrapped to the native full dimensions. Replace stored E=(p+n)/2 and
O=(p-n)/(2*i). The negative filtered partner is recovered by all-axis
conjugate reflection, not by reusing conj(p) at the same frequency. F starts
zero for every order. Source filtering occurs before relocation of carriers.

For even Y, VY covers every row. For odd Y=2*yc+1 it omits y=-yc, and the
source does not filter/recombine that row normally. Center-order values there
remain exactly as prepared. For side orders, reflected outside-support and
axial-zero writes can still touch parts of that omitted half-space row, while
recombination never visits it. Its remaining E/O values stay as prepared.
For Y=1 all filter/recombination loops are empty. This literal behavior is the
CE02 deferred odd-y quirk; do not fill, average or globally zero the omitted
row. Likewise positive x Nyquist has no duplicate negative-x visit; retain
the source partner indexing instead of splitting that endpoint.

## Zero padding, inverse scale and real assembly

For each direction/order initialize a zero full complex output Fourier array
of shape (A*Z,L*Y,L*X). Visit every native full index k,i,j in increasing order.
Its signed lift is q(n,N)=n if n<=floor(N/2), otherwise n-N, with the even
Nyquist endpoint positive. Put the coefficient at that lift modulo the enlarged
output dimensions. No endpoint splitting, carrier rounding, checkerboard,
interpolation or fftshift occurs.

To read the coefficient from filtered half storage, if lifted x<0 reflect all
three lifted coordinates and conjugate each quadrature read; otherwise use the
stored coordinates. Order zero supplies its single coefficient. For side m
combine the read quadratures as E+i*O after the possible conjugations.
Positive native Nyquist is placed only at the positive output lift. At L=A=1
the modulo locations are the original locations.

Apply the unnormalized backward finite sum with positive exponential:
`u[h,i,j]=sum_(l,v,w) C[l,v,w]*exp(2*pi*i*(l*h/(A*Z)+v*i/(L*Y)+w*j/(L*X)))`.
There is no division by output voxel count; using a normalized inverse requires
multiplication by that exact count. Start the real output at zero. In direction
order add Re(u0), unless omit_order0; then for side orders in ascending order add
`2*Re(um*exp(2*pi*i*m*(k0x*x_um[j]+k0y*y_um[i])))` at every h,i,j.
The phase has positive sign and centered lateral coordinates, is independent
of axial position, and uses subpixel carriers without resampling a quotient.

This is the public CE02-to-CE03-to-image composition. Independently synthesized
raw modes, finite transforms, declared complex transfers and supplied parameters
must exercise that path. A self-replay through production helpers is no oracle.

## Representation, failures and scenario inventory

Validate all used input fields before filtering. Validate the full declared
transfer by its accepted public rules. Before each sample retain every actual
source stencil check, including zero weights; an unsafe request rejects the
whole operation. Dimensions, output dimensions, signed lifts, source integer
products/flat offsets and cutoff integers must fit signed32. In particular
X*Y*Z, (X//2+1)*Y*Z, (L*X)*(L*Y), (L*X)*(L*Y)*(A*Z), D*O and Q*P fit.
Source allocation expressions converted to unsigned bytes must fit uint32 for
the complex workspace and real image (8 and 4 source bytes per element), while
the source lookup allocation's explicit signed-int byte count must fit signed32.
Each owned binary64/complex128 output or used copied array must also have shape,
strides and byte extent representable in platform intp, including aggregate
record axes. These are representation limits, not empirically measured external
application-binary-interface claims or a new memory budget. Integer lateral
zoom retains CE02's exact float32 representation rule. Actual allocation failure
within the representable domain is an operation error. No arbitrary smaller
byte cap applies.

Derived support/sampling/phase/taper/weights and inverse/assembly arithmetic
must be finite and defined. Reject unresolved positive square w², overflow,
unsafe cutoffs or addresses, source asin outside its real domain, zero axial
cutoff when a visited sample actually evaluates dampening, forged invalid records and allocation or
transform failures. Finite zero data, zero transfers, zero modulation and signed
outputs remain valid when the operations and stencils are defined. No positivity,
minimum modulation, common cutoff, hidden regularizer or truth-conditioned fit
is introduced. Near cancellation/decision boundaries no universal forward-error
or historical binary-decision guarantee is claimed.

| ID | Distinct observable obligation/outcome |
| --- | --- |
| K01 | Public independent raw preparation-to-declared/prepared transfer-to-known image composition |
| K02 | Finite supported time/direction/order/shape domain and shared supplied parameters |
| K03 | Native self support includes equality; outside support zeroing |
| K04 | Other signed direction/order support excludes equality; exact self exclusion |
| K05 | Other powers have no own axial cutoff, including zero-weight sampling |
| K06 | Order-dependent ceil/truncation/clip axial cutoffs, O2 distinction and small Z |
| K07 | Scalar inverse variance in numerator and denominator; unequal direction/order variance |
| K08 | Wiener square, positive parameter and no automatic estimator |
| K09 | Complex self conjugation and modulation conjugation; signed/zero gains allowed |
| K10 | Suppression physical radius, inclusive radius test, signed radius bypass and on/off |
| K11 | Order-zero default, dampening/omission branch precedence and final omission |
| K12 | Omit-kz0 affects only order-zero weights and coefficients |
| K13 | Shifted elliptical cosine taper after quotient; none and zero-Zp fallback |
| K14 | Positive filtered sideband, reflected negative partner and quadrature recombination |
| K15 | All-axis half-space reflection, native unseparated lateral Nyquist consumption |
| K16 | Odd-y omitted row and partial reflected zeroing, including Y1 empty loops with requested zero-cutoff damping |
| K17 | Positive Nyquist embedding without splitting and zero-filled integer zoom |
| K18 | Unnormalized inverse and preserved upstream scale; constant/displaced amplitude |
| K19 | Centered positive noninteger carrier phase, anisotropic axial/lateral spacing |
| K20 | Native filtering before relocation distinguished from interpolation-first quotient |
| K21 | Real signed image and exact output coordinate/diagnostic/source metadata |
| K22 | Owned read-only outputs, input immutability, accepted writable bands |
| K23 | Invalid used records, arrays, kinds/shapes, nonfinite components and noise reject |
| K24 | Invalid scalar/integer/flag/taper declarations; caller immersion lower/upper bounds and NA upper bound, with permitted endpoints |
| K25 | Transfer completeness, extra orders, complex radial/full layouts and actual stencil errors |
| K26 | Source signed/unsigned and native shape/stride/byte representation limits |
| K27 | Undefined derived domain/overflow, unresolved square/denominator and backend/allocation errors |
| K28 | Explicit unsupported O1, modes and original retired namespace remain unavailable |
| K29 | Documentation distinguishes fixed-parameter math, binary agreement, image recovery and resolution |

A expands distinct error subcases and maps obligations/high-risk paths, credible
wrong outcomes, independent oracle/tolerance derivations and permitted positives
before product discrepancies. Equivalent input values are examples, not new
meaning. Real public-entry/end-to-end proofs lead; smaller tests fill distinct
gaps without production seams. B audits omissions and legitimate alternatives.
Initially passing compatibility evidence is valid; missing entries prove absence,
not an observed numerical product red. Supplemental tests remain labeled.

Coverage inherits approved behavior plus independent risk review; percentages
are advisory. Complete dynamic owned native/JSON/HTML reports remain required
globally/per package/per file and separately per platform, including never-imported
runtime/tools and relevant subprocesses. No dependency, gate, policy, test-discovery
or coverage change is authorized. All 13 canonical `make verify` phases, strict
outcomes, exactly two workers, wheel/import/audit, same-run M25 conversion increment
<=33,554,432 bytes, original Ubuntu24.04/macOS15 proof and fresh D remain gates.

## Mode ledger and claim limits

Implemented/proved only after role acceptance: selected ordinary 3D filtering
and assembly, radial/full accepted transfers, supplied parameters, integer zoom,
cosine/no taper, suppression and listed order-zero flags, literal odd-y behavior.
Deferred defined modes: CE05 carrier/modulation estimation; CE06 remaining 2D,
drift, precise/power taper, overlap-debug/exploded branches, fractional lateral zoom
and other acquisition modes; CE07 file/workflow composition; CE08 recovery study.
Undefined/unsafe reference paths remain excluded: O1 c[1] access, unsafe table
vertices, singular dampening, automatic Wiener and axial padding beyond original
workspace, uninitialized/aborting Bessel/two-objective cases. New required meaning
returns to intake; no silent repaired reference is installed.

Singular dampening means an evaluated division by c[0]==0. With Y>=2 the
visited origin evaluates it before the later omit-kz0 override, even if final
assembly omits order zero. Y=1 has no filter/recombination visits and remains
permitted when all other fields/operations are valid, including c[0]==0 with
dampening requested. For T=D=1,P=3,O=2,Z=X=2,Y=1,L=A=1, unit raw images,
background0, edges0 and equalization off, alpha=1/4 and the ideal-arithmetic
order-zero coefficient is3. With zero carrier and modulation, ideal bands
assemble to constant3; no damping or transfer stencil is evaluated. Actual
binary64 CE02 side residuals remain part of the supplied quadratures and are
consumed by the declared finite assembly. No rounding or residual removal is
authorized to force the ideal constant.

A small numerical presentation will use independent fixed expectations, common
image/spectrum units and preregistered scales. It will show signed image and
spectrum differences from an explicitly defined interpolation-first comparison.
No old full-scene rerun, gain fitting, registration, truth/tolerance tuning or
resolution claim follows from this stage. Mathematical agreement, useful recovery
and historical C executable agreement are separate outcomes.
