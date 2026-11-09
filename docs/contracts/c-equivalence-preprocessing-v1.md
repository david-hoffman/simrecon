# CE02: camera preparation and native phase quadratures

**Version 1.0. Independent source-contract acceptance precedes A.**

This slice expands CE02 of `c-equivalence-rebuild-v1.md` under the common
mathematical-equivalence contract. The owner authorized its execution, fresh
native A/B/C/D, full local and both platform qualifications, a stacked pull
request, then a new CE03 task. There is no bitwise-output requirement.
This document supplies public mathematics, not an implementation prescription.

## Selected source and capability

The reference is retained SVN revision 307. Source is read only, ignored and
unshipped. No retained C is built, run, linked or imported. Source-derived
equations below describe its real arithmetic; finite precision is a separate
error budget. Matching owner executable outputs have not been supplied.

| Source | SHA-256 | Relevant operation |
| --- | --- | --- |
| `helpers.c` | `b6893620163141746d4c869b373a4e52cd53fdeca6293512541f2b9561a5c206` | Camera loading, lines 658–687 |
| `sirecon.c` | `3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567` | Caller, normalization, edges, sums, matrices, transforms |
| `small_math_funcs.c` | `a2d277683f03d38bf924b15e21496cad5595524bc1210c7b1f62c7b851826e3e` | Stored-component separation, lines 85–109 |
| `sirecon.h` | `f493fb31f18423cdc1ae8c7b630bd65777fcf938d0ef580bc963885ddd25a629` | Parameter representations |
| `Makefile` | `1dbf51496c6159acf0c00054197c53f57ba93ddc1a1440145a4ed6dc8d13d9a4` | Ordinary non-TIFF source routing |
| `usr_local/include/fftw3.h` | `8065447638c2cc8451c415248a89c74de4c5f2d1abbac9966454d7aef1b6839d` | Forward transform sign |

The selected build route has no `__SIRECON_USE_TIFF__` macro. External IVE and
FFTW binaries/build inputs were not resolved or run; this is a source target,
not observed binary qualification.

Supported here: one explicitly declared wavelength/channel, stationary 3D
exposures, no axial padding or drift, uniform or supplied per-direction phases,
ordinary on-exposures, declared camera correction, all selected lateral edge
modes and sum-equalization combinations. Time points share camera state and
may share the sum reference. The initial application profile is three
directions, five phases, three retained orders including order zero.
Direction, phase and order counts remain parameters within the domain below.
There is no optical transfer preparation, carrier fit, filter or reconstruction
in CE02. CE07 must consume these actual quadratures, not a second hidden
preparation procedure.

## Public entry and representation

The new public entry is:

```python
prepare_bands(
    images, *, dxy_um, dz_um, norders, background,
    lateral_zoom, axial_zoom,
    flatfield_slope=None, exposure_background=None,
    phases_rad=None, edge_pixels=10,
    equalize=True, equalize_z=False, equalize_time=False,
) -> PreparedBands
```

`images` is a real NumPy array with shape `(T,D,P,Z,Y,X)`. All lengths are
positive; `Z >= 2`, `X >= 2` and X is even. No axis is inferred, squeezed,
reordered or broadcast. Indices start at zero. `norders = M+1 >= 1` includes
order zero; `Q = 2*M+1 <= P`. This includes reduced-order even-phase designs;
it excludes the unsafe even-P default with Q greater than P.

The spatial origin for the forward transforms is the first detector sample.
`dxy_um` is the common x/y detector pitch in micrometres (um); `dz_um` is the
axial detector pitch in um. Both are positive finite scalars. The native grid
is unchanged by zoom. Positive integer `lateral_zoom` and `axial_zoom` specify
the later output sampling scale and affect the upstream C normalization now.
No interpolation, resampling or Fourier shift occurs here.

`background` is a finite scalar or real array `(Y,X)`, in detector counts.
`flatfield_slope` is None or a finite real array `(Y,X)`, dimensionless and
multiplicative, never a divisor. None means an all-one slope. A background
array or supplied slope selects declared correction maps; otherwise scalar
background selects C's no-correction branch. Slopes may be zero or signed;
no positivity requirement is invented. `exposure_background` is None (zeros)
or finite real array `(T,D,P,Z)`, in counts, subtracted before the slope.
No other broadcasting applies. Supplied arrays are copied before use.

`phases_rad` is None for the distinct uniform matrix policy, or a finite real
array `(D,P)` in radians. A supplied list selects the inverse/left-inverse
policy even if its values happen to be uniformly spaced. It is shared across
time and z; no phase estimation or drift adjustment occurs.

`edge_pixels` is an integer no greater than min(X,Y); -1 selects the sine
window, values below -1 select the source's defined bypass, and nonnegative
values select the finite-width edge operation.
The booleans must be actual booleans. With equalization disabled the z/time
flags have no numerical effect and remain recorded. No clipping of negative
counts, automatic parameter estimation or omitted-metadata inference occurs.

The result record exposes these fields:

| Field | Shape/type and meaning |
| --- | --- |
| `quadratures` | complex128 `(T,D,Q,Z,Y,X//2+1)`, slot order `0,E1,O1,E2,O2,...` |
| `noise_variance_factors` | float64 `(D,norders)`, dimensionless scalar per direction/order |
| `separation_matrices` | float64 `(D,Q,P)`, exact selected separation-row convention |
| `phase_angles_rad` | float64 `(D,P)`, resolved uniform or supplied list |
| `frame_sums` | float64 `(T,D,P,Z)`, sums after correction/edge, before equalization |
| `equalization_gains` | float64 `(T,D,P,Z)`, applied ratios, ones when disabled |
| `background_after`, `slope_after` | float64 `(Y,X)`, final owned correction maps after sentinel traversal |
| `sentinel_frames` | tuple of `(t,d,z,p)` events in actual traversal order |
| `input_shape` | original six positive dimensions |
| `input_scale` | positive finite alpha below |
| `dxy_um`, `dz_um`, `lateral_zoom`, `axial_zoom` | exact resolved sampling and zoom values |
| `edge_pixels`, `equalize`, `equalize_z`, `equalize_time` | exact selected edge and equalization settings |
| `phase_policy` | `"uniform"` or `"supplied"` |
| `source_revision`, `reference_sha256` | `"SVN307"` and tuple of the six source-name/hash pairs above, in table order |

Every returned array owns independent storage, shares no memory with caller
inputs, and is writable. The record does not promise to prevent caller mutation.
Inputs, including views, strided arrays and read-only arrays, remain unchanged.
Quadratures have detector-count units after dimensionless camera slope,
equalization, alpha and unnormalized finite Fourier sums. They are not object
mass, normalized PSF samples or final reconstruction intensities.

## Complete selected operation order

Let `I[t,d,p,z,y,x]` be the supplied samples. Process frames in the nested order
time, direction, z, phase. There is one channel; the C wave loop is therefore
trivial. Initialize owned background/slope maps once before all frames.

1. **Camera sentinel, before subtraction.** If the current raw bottom-right
   sample equals exactly -1, replace that raw sample with its left neighbour,
   set the bottom-right slope to 1 and copy the left-neighbour background into
   the bottom-right background. Map changes persist across all later phases,
   z sections, directions and time points in this call. A non-sentinel later
   frame uses its own raw bottom-right value with the changed maps. Other -1
   samples are ordinary data. Caller arrays never change.
2. **Correction and C scale.** With no padding, `Nz0=Z` and
   `alpha = 1/(X*Y*Z*lateral_zoom**2*axial_zoom*D)`. For every physical pixel,
   `J = alpha*s*(I-b-b_exposure)`. With no correction, s=1. The C physical
   row has two extra storage floats, both initially zero; they are storage,
   not additional detector pixels. Source: `sirecon.c:316–327,432,574–638`;
   `helpers.c:658–687`.
3. **Lateral edge operation.** For edge width n>=0, process every x column
   first. Snapshot `delta=(J[Y-1,x]-J[0,x])/2` for that column. For l from
   0 through n-1, let `h_l=1-sin(pi*(l+1/2)/(2*n))`; add `delta*h_l` to
   `J[l,x]`, then subtract it from `J[Y-1-l,x]`. The two writes are sequential,
   including when ranges overlap. Next, for every y row, compute its delta
   from the now modified right and left edge, and apply the analogous x
   updates in increasing k. For n=0 the inner loops are empty, with no division
   by n. n may exceed half a dimension while staying within both dimensions.
   For n=-1 multiply each pixel by
   `sin(pi*(x+1/2)/X)*sin(pi*(y+1/2)/Y)`. Source: `sirecon.c:1051–1096`.
   For n<-1 the caller invokes neither edge helper; values pass unchanged.
4. **Sum equalization.** After the edge operation for all phases of this
   `(t,d,z)`, let `S[t,d,p,z]=sum_yx J[t,d,p,z,y,x]`, over physical pixels only.
   If equalize is true, the reference is
   `R[t,z]=S[0 if equalize_time else t,0,0,0 if equalize_z else z]`.
   Apply `g[t,d,p,z]=R[t,z]/S[t,d,p,z]` to the entire physical frame. References
   use pre-equalization sums, never an already equalized plane. This compact
   expression equals the C reference updates in traversal order. Signed
   nonzero sums are permitted if the resulting arithmetic is finite.
   A zero anchor is itself a zero divisor in its own frame and rejects the
   complete call. With equalize false no division occurs,
   and zero frame sums are permitted. Source: `sirecon.c:651–658,1110–1157`.
5. **Lateral forward transform.** For each prepared real frame, calculate the
   unnormalized sum
   `G[p,z,ky,kx]=sum_yx (g*J)*exp(-2*pi*i*(kx*x/X+ky*y/Y))`.
   Store kx=0,...,X/2 and ky=0,...,Y-1 without shifting. Source:
   `sirecon.c:376–385,661–666`.
6. **Phase separation.** At each z,ky and each kx strictly less than X/2,
   `C[q,z,ky,kx]=sum_p L[d,q,p]*G[p,z,ky,kx]`. The stored lateral Nyquist
   complex pair is deliberately not separated: at kx=X/2, slot q retains
   `G[p=q,z,ky,X/2]`. Both real/imaginary components of that pair remain
   untouched. This rule also applies to order-zero-only and reduced-order
   designs. Source: `small_math_funcs.c:85–109`.
7. **Axial forward transform, after all z sections are separated.** For each
   stored slot/ky/kx, return
   `quadratures[...,kz,ky,kx]=sum_z C[...,z,ky,kx]*exp(-2*pi*i*kz*z/Z)`.
   This includes the untouched lateral Nyquist slots. There is no shift or
   inverse normalization. Source: `sirecon.c:382–384,741,753–755`.

All phase and spatial Fourier signs are fixed by these equations. The omitted
negative kx storage is obtainable for each real quadrature by all-axis conjugate
reflection. At non-Nyquist samples define the positive complex harmonic as
`Bplus_m=E_m+i*O_m` and negative partner `Bminus_m=E_m-i*O_m`; E and O are
themselves complex Fourier arrays. Bminus is not generally conj(Bplus) at the
same index. Native frequency coordinates in cycles/um use signed unshifted
ky/kz indices: j for j<=floor(N/2), otherwise j-N, divided by N*pitch. The
even endpoint is labeled positive; kx has the stored nonnegative labels.

## Selected phase matrices and scalar noise

For uniform policy, `phi_p=2*pi*p/P`,
`L[0,p]=1`, `L[2*m-1,p]=cos(m*phi_p)`, `L[2*m,p]=sin(m*phi_p)`.
The specimen has no 1/P separation normalization. Initialized scalar noise
factors remain exactly one for every order and direction.

For supplied phases build the real P-by-Q matrix A with columns
`A[p,0]=1/P`, `A[p,2*m-1]=2*cos(m*phi_p)/P`,
`A[p,2*m]=2*sin(m*phi_p)/P`. The design must have full column rank.
For Q=P select the inverse `L=A^-1`; for Q<P select the unweighted left inverse
`L=(A.T*A)^-1*A.T`. It is not a weighted inverse, covariance whitening or phase
fit. The reference's factorization failure warnings do not define valid output.
Supplied angles are their declared finite real values, with no tolerance-based
wrapping or merging. The harmonic design has full column rank exactly when
there are at least Q distinct points exp(i*phi_p): multiplying a null Laurent
polynomial by z**M gives degree at most 2*M, which cannot have Q distinct roots
unless it is zero. Exact repeated angles are therefore permitted if enough
distinct points remain. Do not reject all repeated phases or use a numerical
rank/conditioning cutoff as a new domain rule. Near-colliding phase points can
make a finite-precision factorization unresolved; report failure explicitly.
Per direction, `v0=sum_p L[0,p]**2/P` and
`vm=sum_p (L[2*m-1,p]**2+L[2*m,p]**2)/P`. Return v, not its square root and
not the separate quadrature variances. Source: `sirecon.c:426–430,582–595,1173–1274`.

## Public errors and representation limits

Explicit validation failures raise existing `SimreconError` (a ValueError).
They identify the offending argument/domain; exact punctuation is not fixed.
Ordinary Python signature errors remain TypeError. No input changes or partial
result escapes on failure. Validation precedes image correction/transforms.

- Reject nonarrays for array arguments, complex/object/string/bool dtypes,
  nonfinite values, wrong shapes, empty axes, Z=1, odd X and Q>P.
- Raw exposures are already decoded detector samples in the source's float32
  representation. Standard NumPy integer and float16/32/64 arrays are accepted
  only when every raw sample is exactly finite-float32 representable. Conversion
  on this subset is invertible. For example float64 -1+1e-10 rejects rather
  than silently taking a different sentinel branch; exact -1 triggers repair.
  This restriction is on raw input, not intermediate arithmetic. Maps,
  exposure offsets and phases are declared real mathematical inputs evaluated
  in binary64. The source uses float32/complex64 pixels, maps, matrices and
  spectra, double sums but float reference/gains; their finite rounding is not
  a bitwise target. A records predeclared precision/conditioning limits, and
  no near-boundary binary decision parity is claimed. Extended precision
  floats reject. Scalar numerical parameters are
  real finite scalars, never booleans; count/zoom/edge parameters are integer
  scalars, never booleans. Dimensions, counts, zooms and source integer
  intermediates must fit a signed 32-bit index domain; array sizes must also
  fit platform `intp`. In particular X*Y*Z, (X+2)*Y*Z, D*P*Z, Q*P and D*norders
  must fit. Integer lateral zoom must be exactly float32-representable, as the
  source stores it in float. This conservative source-representation domain
  is not a measured external ABI. No additional fixture-size or byte cap is
  selected. Later output-workspace constraints belong to CE04.
- Reject nonpositive sampling/zoom/counts, invalid edge widths, incorrect map,
  exposure or phase shapes and nonboolean flags. The default edge width still
  requires dimensions at least 10; callers of smaller controls select an
  explicit safe width. Do not clamp it silently.
- Reject rank-deficient supplied phase designs. Backend factorization failure,
  nonfinite matrices/noise factors, overflow/nonfinite correction/sums/gains/
  transforms or zero/underflowed alpha are explicit numerical-operation errors
  via SimreconError, without a partially returned result. No arbitrary
  condition-number cutoff defines a different scientific input domain.
- A zero equalization divisor is an explicit sum-domain error. Negative finite
  divisors remain permitted. Do not replace zero sums,
  add epsilons or disable requested equalization.
- Memory allocation failure remains MemoryError; it supplies no successful
  numeric result. There is no out-of-core/memory-limit promise for this pure
  array stage. Caller interruption remains interruption.

Unsupported modes are visible in the capability ledger below, not silently
performed. They are absent from this entry's signature; requests for unknown
options fail as ordinary signature errors. No retired scientific API returns.

| Mode | CE02 status and reason |
| --- | --- |
| Ordinary 3D, supplied camera values, native x half-spectrum | Implement and prove here |
| Uniform phases, supplied full-rank inverse/left inverse | Implement and prove here |
| No edges (0 or below -1), finite edge widths, half-sample sine window | Implement and prove here |
| Equalization off/on, independent/shared z/time reference | Implement and prove here |
| Positive integer zoom factors; no resampling in this stage | Implement upstream scale and metadata here |
| Odd Y | Defined and supported in CE02; downstream filter visits only 2*floor(Y/2) rows (`sirecon.c:2103`) and omits one row for odd Y; CE04 must explicitly preserve/prove that quirk or select a narrower whole-workflow domain |
| 2D, multichannel in one call, fast-file layouts, off-exposures | Defined source modes deferred to CE06/file binding |
| Supplied step shorthand, inferred/drift-adjusted phases, drift correction | Defined source modes deferred to CE06; explicit lists already supported |
| Noninteger zoom, transfer layouts, taper/suppression variants | Defined source branches deferred to CE04/CE06 |
| Axial padding beyond original workspace | Unsafe reference; excluded under common contract |
| Bessel/two-objective, automatic Wiener selection | Undefined/unsafe reference described in common contract; excluded |
| Singular supplied matrix; zero equalization divisor | No defined finite reference value; reject |

## Independent expectations and composition obligations

Before product observations, A derives conditioning/operation/representation
error bounds from these equations. Direct finite Fourier sums and independent
algebraic synthesis supply expected results. Runtime helpers and old scientific
implementations are forbidden as oracles. Small constants, displaced samples,
signed harmonics, irregular square phases and overdetermined residuals must
distinguish signs, missing P, inverse versus transpose, unweighted inverse,
noise squares, alpha, edge/equalization order and the Nyquist exception.

The principal public composition assertion starts with declared raw exposures
and camera/background maps, invokes only `simrecon.prepare_bands`, and compares
the returned final 3D quadratures plus data-dependent gains/metadata with an
independent finite expectation. Include combined nontrivial correction, unequal
sums, edge handling and irregular phases; independent primitive tests alone do
not discharge composition. Include the useful ordinary D=3/P=5/order-0/1/2
profile, signed frequency endpoints and optical-support-reachable lateral
Nyquist. Optical support does not remove any samples in this stage.

Independent source-derived controls, to be used with finite-representation
bounds rather than exact equality for transcendental values:

- X=4,Y=2,Z=3,D=3,lateral_zoom=2,axial_zoom=2 gives alpha=1/576.
  I=20,b=3,exposure background=2,s=4 gives corrected pixel 5/48.
  With P=5 identical constant frames, no edge/equalization, the final
  order-zero DC is 25/2 and ordinary side quadratures are zero.
- At the same geometry, raw baseline 5 and one added 144 at (x,y,z)=(1,1,1),
  with the same b,extra,s, makes a corrected unit impulse in every phase.
  At (kx,ky,kz)=(1,0,1), final zero-order coefficient is
  `-5*sqrt(3)/2 + (5/2)*i`. At (2,0,1) each retained slot instead contains
  `1/2+i*sqrt(3)/2`, the unseparated raw-phase endpoint after axial transform.
- With X=2,Y=1,Z=2,D=3 and unit zooms, alpha=1/12. Camera maps b=[3,7],
  s=[2,4], raw first frame [10,-1] and extra=1 give corrected [1,1/2].
  A later raw frame [12,20],extra=2 gives [7/6,5/4] using the changed maps.
  Resetting maps would incorrectly give bottom-right 11/3.
- For edge width1, input rows [0,2,4,6] and [8,10,12,14], let
  c=1-sqrt(2)/2. The edged rows are [7c,2+4c,4+4c,6+c] and
  [8-c,10-4c,12-4c,14-7c], with total56. The half-sample sine window
  maps an all-one 2-by-2 plane to all1/2, unlike a zero-endpoint window.
- Pre-equalization reference-phase sums at (t,z)=(0,0),(0,1),(1,0),(1,1)
  of 6,10,9,15 give equalized sums at (t,z)=(1,1) of respectively 15,9,10,6
  for (equalize_z,equalize_time)=(false,false),(true,false),(false,true),
  (true,true). The phase-1 original sum30 has gains 1/2,3/10,1/3,1/5.
- For P=5,norders=3 supplied phases [0,pi/2,pi,3pi/2,pi/4], let t=sqrt(2)/2.
  The direct equations for raw phase vector g are
  B0=5*(g0+g1+g2+g3)/4; E1=5*(g0-g2)/4; O1=5*(g1-g3)/4;
  E2=5*(g0-g1+g2-g3)/8; O2=5*g4/2-B0/2-t*E1-t*O1.
  Noise variance factors are [5/4,5/4,5/2]. These independently derived rows
  distinguish the row/column layout, omitted quadrature and printed square root.
- For P=4,norders=2, phases [0,pi/2,pi,pi] are overdetermined and full rank.
  Put h=(g2+g3)/2. B0=2*(g0+h), E1=g0-h, O1=2*g1-(g0+h), and noise factors
  [3/2,7/4]. Opposite perturbations of g2,g3 leave the output fixed. This
  distinguishes unweighted least squares from choosing or weighting a sample.

Cross-stage contract: CE04/CE05 and final CE07 must consume this returned slot,
noise and scale convention with its Nyquist contents and selected settings.
CE02 can prove its public raw-to-band composition, not future integration,
binary-output agreement, reconstruction recovery or resolution.

## Behavioral scenario inventory

These IDs describe distinct obligations, not a test-count quota. A maps every
ID to public assertions or an explicit proof limit; B audits the mapping and
credible wrong results independently. Numerical values within one decision
are coverage examples.

| ID | Observable obligation / credible wrong result |
| --- | --- |
| C01 | Raw-to-final-quadrature composition with nontrivial correction, edges, unequal sums and supplied phases |
| C02 | Multiplicative slope, scalar/map background and extra offset in the stated order; signed/zero slopes and counts |
| C03 | Source alpha includes Z, both zooms and D, with no specimen phase-count division |
| C04 | Sentinel applies only at exact decoded bottom-right -1; source traversal and persistent camera state |
| C05 | Additive finite edge operation, y then x, including overlap and width0 |
| C06 | Half-sample sine edge window; correction and edge precede sums |
| C07 | Defined edge bypass below -1 retains requested selector |
| C08 | Equalization disabled permits zero sums and ignores but records z/time flags |
| C09 | Enabled equalization uses each frame's own sum and direction-zero/phase-zero anchor |
| C10 | z/time flags choose the four distinct anchor outcomes |
| C11 | Zero/cancelled sum rejects; negative nonzero sums remain valid |
| C12 | Uniform phase rows/sign/harmonic/slot scale, with noise exactly1 |
| C13 | Supplied square inverse including direction-specific rows and unequal noise |
| C14 | Supplied overdetermined unweighted inverse, valid repeated phases and residual projection |
| C15 | Rank-deficient designs reject; finite full-rank designs get no arbitrary conditioning cutoff |
| C16 | Both floats of stored lateral Nyquist skip separation, retain raw slot identity and undergo axial transform |
| C17 | Unnormalized forward signs, origin, wrapped coordinates and signed/full-axis representation identities |
| C18 | Exact output shapes/dtypes/metadata/source identity; caller arrays unchanged and result storage owned |
| C19 | Shape/type/finite/scalar/flag/domain validation, with legitimate strided/read-only input |
| C20 | Safe source/index representation domain; inexact raw float32 values and unsafe dimensions reject |
| C21 | Numerical/factorization/overflow/nonfinite failure is explicit, with no fallback/partial result |
| C22 | Unsupported capabilities and future composition limits are explicit; neutral and retired boundaries persist |
