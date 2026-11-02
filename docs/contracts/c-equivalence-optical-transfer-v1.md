# CE03: empirical bead transfer preparation and complex sampling

**Version 1.0. Source-contract review precedes blind A.**

This expands the authorized CE03 slice of the [ordered rebuild](c-equivalence-rebuild-v1.md#ce03-optical-transfer-preparation-and-sampling)
and inherits the [common contract](c-equivalence-common-v1.md). The target is
retained SVN307 real-arithmetic operations and finite decisions, not bitwise C
output. No C is built, run, linked or imported. Historical effective external
FFTW/IVE headers/libraries are not qualified. Source buffers declare float pixels;
Python independently evaluates the equations in binary64. Matching owner C
outputs have not been supplied. No recovered-image or resolution claim follows.

## Source selection and units

The selected preparation caller is ordinary single-objective `radialft` in
`mainfile.c:76–340`, without I2M, ACCURATE_PEAK, or alternate physical fitting.
Sampling is the non-TIFF reconstruction caller's `otfinterpolate` in
`small_math_funcs.c:396–483`; `helpers.c:747–842` defines the declared table
layout. The source manifest in the CE03 task evidence pins mainfile, helpers,
small_math_funcs, sirecon, sirecon.h, Makefile and relevant transform headers.

| Source | SHA-256 |
| --- | --- |
| `mainfile.c` | `b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8` |
| `small_math_funcs.c` | `a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e` |
| `helpers.c` | `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206` |
| `sirecon.c` | `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567` |
| `sirecon.h` | `f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629` |
| `Makefile` | `1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4` |
| `usr_local/include/sfftw.h` | `72e8b913d58e599faa0057c664c202acc7883906638e8ab5bcc11b21b310f138` |
| `usr_local/include/srfftw.h` | `d7bf4dc6f7a392ae7b36a30375c467269e56471ede148531a8f1bf09b0e8883a` |
| `usr_local/include/fftw3.h` | `8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d` |

Wavelength is required explicit acquisition metadata; the source reads it from
the bead header. No arbitrary example wavelength is a default.
Spatial pitch and bead diameter/line spacing use micrometres (um). Wavelength
uses integer nanometres (nm); multiply by 0.001 for um. Frequencies and table
increments use cycles/um. Angles use radians. Array indices are zero based.
Equations use mathematical pi; the source PI literal and source floating-point
rounding contribute to representation/decision sensitivity, not a bitwise claim.
Source integer limits are signed 32-bit; byte/index/shape products and all
actually calculated intermediate addresses must fit. Positive even Nyquist
indices are retained: q(i,N)=i for i<=floor(N/2), otherwise i-N.

## Public entries and value records

```python
prepare_otf(raw, *, dxy_um, dz_um, linespacing_um, wavelength_nm,
            bead_diameter_um=0.12, carrier_angle_rad=0.0,
            background_counts=None, background_map=None, slope_map=None,
            exposure_background_counts=None,
            compensate_bead=True, fix_axial_axis=True, fix_radial_from=0,
            cleanup_axial_bins=(0, 0, 0),
            numerical_aperture=1.4, immersion_index=1.515,
            origin_fit_bins=None, rescale_each=False,
            forced_pi_shift=False, conjugate=False) -> PreparedOtf

declare_otf(samples, *, layout, dkr_cyc_um, dkz_cyc_um) -> OpticalTransfer

sample_otf(transfer, kx_cyc_um, ky_cyc_um, kz_index, *,
           dkz_cyc_um, order=0) -> numpy.ndarray
```

These functions and `OpticalTransfer`, `PreparedOtf`, `OtfError` are public from
`simrecon`. `OtfError` subclasses ValueError. Every rejected input/unsupported
operation or unresolved numerical operation raises it with nonempty informative
text. Unsupported capabilities name the branch. Allocation/backend failures
are translated with cause retained. No fallback, regularizer or zero fill hides
a failed operation. No exact incidental diagnostic vocabulary is required.

Raw axes are `(phase,z,y,x)` with odd P in {1,3,5,7,9}, Z>=2, square even lateral
N>=10. P=1 requires compensation off (source order/(norders-1) is undefined).
The initial useful profile P=5/orders=3 is included. Non-square empirical input
and odd x storage are unsupported here: the former has a defined `ny-1-k`
horizontal-edge quirk plus unequal physical-frequency indexing, while the
latter conflicts with the source's nx+2 real-transform stride. Non-square
source-defined modes remain a CE06 ledger item, not silently corrected.

Raw values are finite real numeric, never booleans/object/string/complex, exactly
representable as float32 after decoding. Returned arithmetic/storage use
float64/complex128. Scalar settings/maps are finite real numeric and within
float32 magnitude, never booleans. Integer settings accept Python/NumPy integral
values, never booleans; no truncation. Flags are actual booleans. dxy,dz,
linespacing,immersion,wavelength,NA are positive; NA<=immersion. Diameter>=0,
and >0 with compensation enabled. These optics constraints hold even when
cleanup is off, so resolved records always contain a physical declared setting.

`background_counts` is None for source auto-border policy or a nonnegative
scalar. Both camera maps must be supplied together, real `(N,N)`; slope may
have any finite sign including zero. `exposure_background_counts` is None or
real `(Z,P)` (may be signed). Precedence is exposure backgrounds, then camera
maps, then declared scalar, then automatic border. All supplied inputs are
validated even when a higher-priority policy supersedes them. Metadata records
the selected policy. Caller inputs are never changed.

The selected caller hardcodes the 10-pixel edge operation. There is no public
edge option: the unused helper's sine/bypass/other-width branches are not selected
caller capabilities. N>=10 makes both strips address valid image rows/columns,
including overlapping strips when N<20. `fix_radial_from` is a nonnegative
signed32 integer; zero disables and values>N/2 perform the source no-op. `cleanup_axial_bins` is a
length-three sequence of nonnegative integers `(l11,l12,l2)`; l11=0 bypasses,
otherwise the source cleanup executes. `origin_fit_bins` is None or integer
pair `1<=a<b<=N/2`. No singular one-bin regression is admitted.

`OpticalTransfer` is a frozen value record with owned complex128 `samples`,
`layout` (`radial` or `full`), float `dkr_cyc_um`, `dkz_cyc_um`, integer `norders`,
`source_revision='SVN307'`, and `reference_sha256` tuple of the source-name/hash
pairs below. Samples are read-only. Radial shape is `(O,R,K)` with O>=1,R>=1,
K>=1 (axial fastest); full shape is `(O,K,Y,X)` with O>=1,K>=1,Y>=1,X>=1
(x-half fastest). Increments are positive finite float32-magnitude real scalars.
Declared complete samples are finite real/complex numeric values exactly
representable as complex64; no normalization, symmetry enforcement, conjugation
or missing-order duplication is applied. Complete order-major samples already
express the selected source table declaration. Five-quadrature files are not
implicitly accepted as three combined orders. File reading is deferred to CE07.

`PreparedOtf` is frozen and contains `transfer`, float64 `center_pixels_xyz`
shape(3), float64 `background_counts` shape(Z,P), float64 `phase_angles_rad`
shape(P), complex128 `quadratures` shape(P,N/2+1,Z), float64
`normalization_factors` shape(P), float64 `quadrature_angles_rad` shape(O-1),
and `resolved_settings`, an immutable tuple of (name,value) pairs for all scalar/
flag/bin options plus `background_policy`. Array outputs are owned and read-only.
Quadratures are captured after scaling and before combination/conjugation.
The transfer uses common dkr=1/(N*dxy), dkz=1/(Z*dz), O=(P+1)//2. A direct
record produced by preparation need not be rounded to complex64 to be sampled.
Returned transfer samples are the combined/conjugated tables. These diagnostics
expose the real empirical stages, not a new fit or alternate public algorithm.

Sampling requires an actual valid OpticalTransfer; forged/mutated invalid fields
reject. Lateral coordinates are finite real scalars/arrays, axial indices are
integral scalars/arrays (nonboolean), and order is a scalar integer 0..O-1.
Coordinates broadcast to one shape; incompatible shapes reject. Empty query
arrays are allowed and return an empty owned complex128 array of that shape.
The scalar case returns a zero-dimensional array. `dkz_cyc_um` is positive;
physical z frequency is kz_index*dkz_cyc_um. All source index calculations and
actual stencils must fit the selected signed-int/allocation domain below.

## Preparation operation map

1. Visit z then phase. Decode the plane. If its bottom-right value is **<0**,
replace that pixel by its left neighbor (different from specimen exact -1).
For exposure policy use supplied b[z,p] with no camera correction; for maps
replace each pixel by `(pixel-background_map)*slope_map` and set b=0; otherwise
use the declared scalar b or estimate b from the *raw corrected-corner plane*.
Automatic border20 selects y<20 or y>N-20 AND x<20 or x>N-20, with strict > at
the high edge; average the selected pixels. This is four corner regions, not
the union of a perimeter. Small arrays may select the whole plane.

2. Apply the fixed width w=10 edge operation before subtracting b. For each x compute
`diff=(I[N-1,x]-I[0,x])/2`; in increasing l=0..w-1 add diff*f_l at (l,x) and
subtract it at (N-1-l,x), `f_l=1-sin((l+0.5)*pi/(2*w))`. Then for each y compute
the now-current right-left diff/2 and perform the same increasing k updates
at (y,k),(y,N-1-k). Endpoints may overlap; retain update order. The ordinary caller fixes w=10;
helper-only sine/bypass/other-width operations are not exposed here.

3. Before background subtraction, average edge-treated images over P to A.
Scan z,y,x with maxval initially0 and location(0,0,0); replace only for strictly
greater values. Thus ties select the first maximum and nonpositive data keep
the initial location/maxval0. For each axis use periodic nearest neighbors
(vminus,vplus) around this location and the selected maxval v0. Let
`s=(vplus-vminus)/2`, `c=vplus+vminus-2*v0`; offset=-s/c unless c==0 or offset
is outside [-1.5,1.5], in which case offset=0. Return integer location+offset,
without wrapping a fractional negative result to the opposite edge.
The source also computes an unused background diagnostic at floor(zc), for
integer y satisfying y<yc-20. It never supplies the preparation background.
Reject when its accesses would leave the allocation, or yc==20 gives singular
arithmetic; do not reinterpret that unused diagnostic as a background estimator.

4. Subtract each b[z,p] from the edge-treated raw pixels. For phi_p=2*pi*p/P,
form spatial quadratures Q0=sum_p I_p/P, C_m=sum_p I_p*cos(m*phi_p)/P,
S_m=sum_p I_p*sin(m*phi_p)/P, m=1..O-1. Every pixel is separated, including
later lateral Nyquist. There is no specimen alpha, frame equalization or
additional 2/P factor. Q slots are [0,C1,S1,C2,S2,...].

5. Apply the unnormalized forward 3D finite Fourier sum with negative
exponential, stored x>=0 half. Multiply each quadrature at indices(kx,iy,iz)
by `exp(+2*pi*i*(kx*xc/N+q(iy,N)*yc/N+q(iz,Z)*zc/Z))`. All three phase signs
are positive; source comments suggesting a negative z sign are not executed.

6. If compensation is selected, for each order m and both side quadratures
use shifted physical frequencies `(kx*dkr+m*cos(theta)/(M*L),
q(iy,N)*dkr+m*sin(theta)/(M*L),q(iz,Z)*dkz)`, M=O-1, L=linespacing.
For rho=their Euclidean norm, R=diameter/2, u=2*pi*R*rho, divide by
`S_R=3*(sin(u)-u*cos(u))/u**3`, with limit1 at rho=0 (order0 origin is1).
This is a continuum fluorescent sphere, not the Fourier transform of a sampled
sphere mask. Zero/unresolved divisors and nonfinite arithmetic reject; no floor
or regularization is added. Stable evaluation of the same analytic expression
near zero is allowed. No new arbitrary small-positive cutoff is a domain rule.

7. For each quadrature accumulate the half-spectrum into radial bin
`r=rint(sqrt(kx**2+q(iy,N)**2))`, nearest integer with ties-to-even, only when
r<N/2+1. Average each (r,iz) by its actual count; empty bins stay zero.
Then force imag(r,0)=0. For increasing j=1..floor(Z/2) replace
`v=(H[r,j]+conj(H[r,Z-j]))/2`, set H[r,j]=v,H[r,Z-j]=conj(v).
The self-paired even axial Nyquist becomes real. Nonself pairs may have
nonzero imaginary odd components. No all-real or full-plane weighting replaces
this procedure.

8. For each Q slot (order=(slot+1)//2), repair r=0 from r=1 for every z except
order0,z0 when fix_axial_axis=True. Only source ifixz[0] is effective; there
are no separate per-order fixes. If fix_radial_from=f>0, for r=f..N/2 replace
H[r,0] by `(H[r,1]+H[r,Z-1])/2`. The axial repair runs first.

9. Optional support cleanup follows repairs. For m=0 use A=NA; for m>0 use
A=0.92*NA (also orders>2). Let lambda=0.001*wavelength_nm,
alpha=asin(A/nimm), kr=r*dkr, krmax=2*A/lambda. If kr>krmax zero the whole
axial row. Otherwise beta=asin((A-kr*lambda)/nimm),
e=(nimm/lambda)*(cos(beta)-cos(alpha))/dkz. For order0 set
j0=rint(e+1), and zero every j0<=j<=Z-j0 (inclusive). For order1 let
h=rint(e+0.999), end=l11-h. If end>=0, zero j=0..end and the partners Z-j
for j>0. Then start=l12+h, zero j=start+1..floor(Z/2) and partners Z-j.
For orders>=2 let start=l2+rint(e+0.999); zero j=start..floor(Z/2) and Z-j.
These are literal source bounds, executed radial row by radial row in ascending
order on the flat in-place allocation. Every actually computed flat write
`r*Z+j` or `r*Z+(Z-j)` must be in [0,(N/2+1)*Z); source-safe cross-row writes
are preserved and can affect later rows. A conceptual j outside its nominal
row does not by itself justify rejection. Reject an out-of-allocation write
even if a later operation would overwrite it. No clipped repair changes the mask.

10. For order-zero slot only, optional origin repair fits real axial sums.
Let v0=Re(H[0,0]), vr=sum_z Re(H[r,z]) for r>0. On a..b, mu=(a+b)/2,
mean=sum vr/(b-a+1), slope=sum((r-mu)*vr)/sum((r-mu)**2).
For r<a replace Re(H[r,0]) by Re(H[r,0])-vr+mean+(r-mu)*slope.
Imaginary components and all other entries remain unchanged.

11. In slot order, compute inverse max modulus on order0 or on every slot if
rescale_each=True. Multiply each slot by that factor; default reuses the one
order0 factor on all slots, preserving relative amplitude. A zero/nonfinite
maximum or nonfinite factor/output rejects. This is not DC normalization,
per-plane normalization, or per-order default normalization.

12. Combine side C,S after repairs/cleanup/origin/scaling. Let a=sum|C|,
b=sum|S| over all radial/axial cells. phi=atan(b/a). a=0 rejects as a singular source division, including b>0; no pi/2 extension
is substituted. At (r=floor(N/8),z0), let c=Re(C),
s=Re(S). If c<0,s>0 add pi; if c<0,s<0 use pi-phi; if c>0,s>0 use -phi;
otherwise leave phi unchanged, including zero-sign cases. If m==1 and
forced_pi_shift=True replace phi by pi-phi. Output H_m=C*cos(phi)-S*sin(phi),
with H0=Q0. This is not C+i*S. Finally conjugate all output orders if selected.
No five-quadrature public output substitutes for combined transfer samples.

## Sampling operation map and actual stencils

The source caller supplies kx,ky in cycles/um, integer kz and positive native
axial step. Set t=kz*(native_dkz/table_dkz). All mathematics below applies to
complex values, including imaginary-odd radial values and asymmetric full tables.

Radial: u=hypot(kx,ky)/dkr. If t<0 add K **once**, not modulo repeatedly.
i=floor(u),j=floor(t), ar=u-i,az=t-j. j1=0 if j==K-1, otherwise j+1.
Read flat offsets `i*K+j`, `i*K+j1`, `(i+1)*K+j`, `(i+1)*K+j1` from the
selected order's row-major flat allocation, including all four at zero weights.
Return `(1-ar)*((1-az)*v00+az*v01)+ar*((1-az)*v10+az*v11)`.
All four actual offsets must be in [0,R*K). No imaginary projection occurs.

Full: u=kx/dkr,v=ky/dkr,t as above. If u<0, negate u,v,t and mark conjugation.
If v<0 add Y once; if t<0 add K once. i=floor(u),j=floor(v),l=floor(t),
a=u-i,b=v-j,c=t-l. j1=(j+1)%Y,l1=(l+1)%K using C signed remainder (truncate
division toward zero, so negative remainders stay negative). Read all eight
flat offsets `lz*(Y*X)+jy*X+ix` for lz in(l,l1),jy in(j,j1),ix in(i,i+1).
Return trilinear weighted sum with x weights(1-a,a), y(1-b,b), z(1-c,c).
Conjugate the result iff u was originally negative. Reflect all three
coordinates, not just x. x=0 and negative zero do not trigger reflection.

For both layouts every calculated index/product must fit signed32 and every
actually dereferenced flat offset must lie inside that order's allocation.
Do not reject a deterministic cross-row alias merely because a conceptual
axis index exceeds that axis; the source uses these flat addresses. Such
in-allocation cases remain literal source quirks. An out-of-allocation vertex
rejects even if its interpolation weight is zero. Thus the final lateral sample
often cannot be queried; there is no clamped endpoint or skipped zero term.
Failure in any query rejects the whole call; no partial output is returned.

## Boundary, compatibility and scenario inventory

All supplied fields are validated before numerical preparation or sampling.
Operation-time failures include arithmetic overflow/nonfinite output, unresolved
sphere evaluation, unsafe source diagnostic/support/stencil indices, zero scale,
undefined quadrature angle and allocation/transform backend failures. These are
classified separately from unsupported dimensional modes. No all-positive
intensity or nonnegative-transfer restriction is invented. Direct tables may
have zero support or even all-zero data; only empirical scaling/combination
requires the corresponding nonzero norms. Existing neutral I/O and
prepare_bands behavior remain. CE04 must consume these actual records/sampler;
CE07 must compose declared calibration arrays through this preparation path.

| ID | Distinct observable obligation or outcome |
| --- | --- |
| O01 | Raw-bead-to-combined-transfer-to-public-sample composition from independent observations |
| O02 | Corner pixel replacement for every negative value, and nonnegative preservation |
| O03 | Exposure-background precedence, no camera map correction on that branch |
| O04 | Camera-map correction and zero subtraction background |
| O05 | Explicit scalar background branch |
| O06 | Auto corner-intersection border with strict high edge and small-plane behavior |
| O07 | Fixed10-pixel sequential vertical then horizontal edge updates, overlapping strips |
| O08 | Center from pre-background phase mean; first-strict ties and nonpositive fallback |
| O09 | Periodic parabola neighbors, zero curvature, rejected outlying offsets, fractional unwrapped centers |
| O10 | Uniform bead phase rows divide by P; no specimen alpha; full Nyquist separation |
| O11 | Unnormalized negative forward FFT followed by positive centering on all axes |
| O12 | Order-shifted continuum sphere division of both quadratures, zero-frequency limit and off branch |
| O13 | Rounded radius bins, half-plane counts, excluded diagonal support and empty bins |
| O14 | Radial conjugate axial symmetry with imaginary odd part and real self endpoints |
| O15 | Effective axial repair including order0 DC exception |
| O16 | Optional radial repair following axial repair, large nonnegative start no-op |
| O17 | Cleanup order-dependent NA, radial inequality and literal integer axial masks |
| O18 | Cleanup bypass and unsafe prescribed support writes rejection |
| O19 | Origin real-sum linear regression and unchanged imaginary/non-DC entries |
| O20 | Shared default order0 maximum scale preserves unequal amplitudes |
| O21 | Optional each-quadrature rescale with traversal-order factors |
| O22 | Magnitude-sum phase/sign quadrants and zero-sign fallthrough |
| O23 | Forced pi change applies only first order; final optional conjugation |
| O24 | Declared radial and full complete table layouts preserve complex samples and scale |
| O25 | Radial complex bilinear interpolation, one-time wrap, axial seam |
| O26 | Full trilinear interpolation with y/z seams |
| O27 | Full negative-x all-coordinate reflection plus conjugation, zero-x distinction |
| O28 | Every actual stencil vertex required at zero weights, last lateral boundary |
| O29 | Memory-safe cross-axis flat aliases and unsafe flat accesses distinguished |
| O30 | Broadcasting/scalar/empty query shapes, integer axial indices and order selection |
| O31 | Output dtypes/shape/metadata/source identity, owned read-only arrays, no caller mutation |
| O32 | Invalid raw/table/query numeric kinds, shapes, nonfinite/unsafe representation reject |
| O33 | Invalid scalar/integer/flag/paired-map/optional sequence declarations reject |
| O34 | Unsupported rectangular/odd-x/even-phase/P1 compensation modes reject explicitly |
| O35 | Unsafe unused source diagnostic access/singularity rejects |
| O36 | Sphere zero/unresolved divisor, overflow and backend/allocation operation failure reject |
| O37 | Zero empirical normalization or zero-cosine quadrature angle (including positive sine) rejects; valid direct zeros remain |
| O38 | Invalid/forged transfer records and unsafe source int arithmetic reject |
| O39 | Existing public compatibility and reconstruction-unavailable boundary remain |
| O40 | Documentation/usage distinguishes empirical bead preparation from arbitrary PSF transform, mathematical vs binary proof |

A must map these obligations and distinct error subcases to tests and derive
oracle tolerances before observing product discrepancies, with credible wrong
outcomes and distinct gaps in public-entry proof. Smaller tests fill real gaps;
no test-only seam or percentage-driven impossible state is authorized. Independent
algebraic/finite-sum expectations must distinguish continuum/discrete sphere,
C+iS/angle combination, phase-factor/sign/normalization, per-order/common scale,
all-real/imaginary-odd transfer, and partial/all-axis reflection. Use permitted
positive inputs paired with rejections. No C executable or production helper is
an oracle. Passing existing behavior is valid; no manufactured product-red.

Coverage inherits approved behavior plus independent risk review. Percentages
are advisory; no percentage target is selected. Full native executable-line and
branch-destination reports remain mandatory globally/per package/per owned file
and separately per platform, including never-imported files/subprocesses. No
coverage exclusions or installed gate changes occur. Fresh native A/B/C/D,
exact-candidate full local make verify, fixed two workers, all 13 phases,
wheel/import/audit, same-run M25<=33,554,432 bytes and original Ubuntu24.04/macOS15
proof precede ready PR. No merge/release is authorized. Source review and D must
challenge omissions against the end-to-end common contract, not only this table.

## Source-mode ledger and limits

Implemented here: ordinary single-objective stationary 3D square bead arrays,
uniform odd phases, declared/map/exposure/auto backgrounds, fixed10-pixel edges and all safe
repair/cleanup/origin/scale/combination options above; complete radial/full
transfer value declarations and exact complex source sampling. Table axes of
length1 are permitted where the actual stencil is safe; this does not implement
2D specimen reconstruction.

Deferred defined modes: non-square empirical branches with their literal quirks;
I2M/two-objective preparation; five-quadrature file output and source missing-order
duplication; external-header/file composition; ACCURATE_PEAK alternate build;
2D empirical preparation, supplied bead-phase policy (not present in selected
uniform path), alternative source tools and drift. CE06/CE07 must select and
prove any needed defined route explicitly. No old three-bead optimizer returns.
Even-phase uninitialized separation row, odd-x storage mismatch, P1 compensation
0/0, unsafe accesses and unresolved historical TIFF/header values are not numeric
oracles. A separately needed undefined reference branch returns to owner intake.
The CE02 later-filter odd-y source quirk remains deferred to CE04/CE06 and is not
silently repaired by these transfer operations.
