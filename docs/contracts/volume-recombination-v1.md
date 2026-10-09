# VOLUME-RECOMBINE-01: known-parameter five-order volume recombination

**Version 1.0. October 9, 2026.** The owner's continuing instruction, “Keep on stacking in a new task! Continue that pattern until the roadmap is complete,” authorizes this coherent scientific slice above verified, independently accepted PR #18. Intake selects the estimator below before blind test authorship. Report-only Astra/ultra advice replaces no required role.

## Public operation

```python
from simrecon import Reconstruction3D, reconstruct_volume

result = reconstruct_volume(
    images,
    order_otfs=calibrations,
    phases_rad=phases,
    carriers_bins=carriers,
    gains=gains,
    regularization=penalty,
    output_shape_yx=(Ly, Lx),
    apodization=mask,
)
result.volume
result.spectrum
```

Only images is positional; all keywords are required. Ordinary Python binding TypeError applies. This pure array operation separates known phases, relocates five lateral phase orders to an explicit signed output window and combines their full complex effective transfers. No phase/carrier/gain estimation, axial resampling, fractional interpolation, drift inference, acquisition adapter, file access, CLI feature or new dependency is included. Existing APIs and installed gates remain unchanged.

Images is a plain NumPy ndarray `(R,N,Nz,Ny,Nx)`, R>=1, N>=5 and spatial dimensions positive. Phases `(R,N)` and gains `(R,)` are plain ndarrays. All three accept dtype kinds i/u/f at every available width/byte order and strided, Fortran or read-only storage. Reject nonarrays, ndarray subclasses/masked arrays, bool, complex and other kinds. Source and copied native float64 samples must be finite. Signed images/phases are valid; converted gains must be strictly positive, with no upper bound. Conversion rounding and finite underflow define the stored problem. No guarantee covers concurrent external mutation.

Carriers is a plain ndarray `(R,2)` of signed or unsigned integer kind, excluding bool. Values are exact Python integers after snapshot; columns are y/x detector bins. No float-to-integer coercion, principal-period reduction, modulo carrier interpretation or carrier magnitude threshold applies. Negative, opposite, zero and repeated carriers are valid. Each orientation's phase vector is passed unchanged in value to the existing `separate_volume_phases`; its represented basis, rank, least-squares semantics, accuracy and errors propagate. N>5 off-model observations receive that projection.

Regularization lambda is a nonboolean Python or NumPy real scalar, converted to finite float64 >=0. Output shape is an exact built-in tuple or list of two nonboolean Python/NumPy integers, each positive and representable by native `np.intp`. Apodization is a plain real i/u/f ndarray `(Nz,Ly,Lx)`; source and converted float64 values must be finite and in [0,1]. It is an amplitude mask on the centered output spectrum, not a power mask, inferred support or normalization.

Snapshot all accepted array inputs and calibration fields before phase separation or transforms. Preserve caller contents, strides and writable flags on success and every failure. Independent copies define the computation; no persistent side effects occur.

## Effective transfer records

Order OTFs is an exact built-in tuple or list of length R containing `VolumeOrderOtf` instances. Validate every public field even for direct record construction. Values is a plain complex ndarray of complex128 width, either byte order, shape `(3,Nz,Ny,Nx)`, all real/imaginary components finite. Each frequency vector is a plain float64-width ndarray, either byte order, with the corresponding length, all finite, strictly increasing when length>1, zero exactly at index dimension//2, and correct canonical centered bins. Strided/read-only arrays are permitted.

Voxel spacing is an exact built-in tuple/list of three nonboolean Python/NumPy real scalars, converted finite and strictly positive; values are micrometres. Origin is an exact built-in tuple/list of three nonboolean Python/NumPy integers in bounds. Source is a nonblank string, retained only as opaque caller metadata. Every orientation has exactly the same converted spacing. Origins and source labels may differ: origin phase is already in each supplied transfer and must not be applied again.

For dimension K and spacing d, expected frequency is k/(K*d) cycles/µm, k=-floor(K/2)..ceil(K/2)-1. Validate each component against `8*eps*abs(f_exact)+q`, eps=2^-52, q=2^-1074, evaluated without overflow/underflow in the observer. No physical support, E0 normalization, Hermitian symmetry, positive side gain or illumination realizability is inferred. Zero transfers, arbitrary finite complex values and phase gauges are accepted. All records are fully validated even when gains, mask or a side order makes some observations ineffective.

## Signed window and estimator

Let detector modes j=(jz,jy,jx) use the centered canonical bins on `(Nz,Ny,Nx)`. The output modes q use the same convention on `(Nz,Ly,Lx)`. For orientation r, order m=-2,-1,0,+1,+2 relocates its detector bin to

```text
q = (jz, jy-m*carriers[r,0], jx-m*carriers[r,1]).
```

Placement is integer and nonwrapping on the y/x output window. Require `Ly >= Ny+4*max_r(abs(carriers[r,0]))` and `Lx >= Nx+4*max_r(abs(carriers[r,1]))`. These exact integer conditions retain every geometric band, including even-Nyquist endpoints. Reject an insufficient grid irrespective of zero transfers or mask values. Never crop bands, wrap them, infer a size or silently double the grid. Native axial modes and axial sample count remain unchanged.

For each orientation, let dc,c1,c2 be the mathematical unweighted least-squares coordinates of its represented phase matrix and converted observations. Let M=Nz*Ny*Nx. Use negative-exponent discrete Fourier coefficients

```text
D0(j)  = sum_x dc(x)*exp(-2*pi*i*j.x/K)/M
D+m(j) = sum_x cm(x)*exp(-2*pi*i*j.x/K)/M, m=1,2
D-m(j) = sum_x conj(cm(x))*exp(-2*pi*i*j.x/K)/M.
```

Here j.x/K means the sum over z/y/x coordinates divided by their detector dimensions. Transfers E0,E+1,E+2 are the supplied centered values. Define `E-m(j)=conj(E+m((-j) modulo detector dimensions))`; modular negation acts on all three axes and keeps the single even-axis Nyquist bin. Ordinary reversal of centered arrays is incorrect. The negative measurements are determined conjugate bands, not independent acquisitions.

For output q, include exactly the detector bins j=q+m*carrier that lie in the canonical detector window. In intensity units of the converted images and dimensionless transfer/gain units, define

```text
t = gains[r]*Em(j)
U(q) = sum_(r,m available) conj(t)*Dm(j)
V(q) = sum_(r,m available) [t.real**2+t.imag**2]
T(q) = apodization(q)*U(q)/(V(q)+lambda), if V(q)+lambda>0
T(q) = 0, otherwise.
volume(z,y,x) = sum_q T(q)*exp(2*pi*i*[
    qz*z/Nz + qy*y/Ly + qx*x/Lx]).
```

Ridge lambda has squared-transfer units. No additional modulation parameter, factor of two, order DC renormalization, brightness normalization or division by output voxel count is applied. Gain multiplies every order's supplied transfer once. The returned centered spectrum equals T; volume uses origin index (0,0,0). Preserve both real and imaginary components. Do not take a real part, enforce Hermitian symmetry or split/copy a Nyquist coefficient.

For example detector Nx=4, carrier zero, E0=1, side transfers zero and dc=(1,-1,1,-1) give coefficient one at canonical kx=-2. On output Nx=8 the selected lift is exp(-2*pi*i*2*x/8), which is complex. A real interpolation convention would be a different estimator. Integer relocation alone establishes no resolution gain without usable transfers and a valid forward model.

The supplied-order forward model is the finite circular effective-kernel model of VOLUME-ORDER-01, with lateral specimen carrier factors outside those kernels. This estimator can exactly recover appropriately commensurate, alias-free supported modes in unregularized examples. General periodic detector data does not uniquely identify an extended signed object spectrum: aliasing, noise, off-model residual, missing transfer, ridge and mask introduce ambiguity/bias. No general physical recovery or continuous-optics promise is made. The prerequisite focal-plane-relative axial-profile limit and g0=1 remain.

## Output coordinates, record and numerical execution

Preserve field of view. Output spacing is `(dz, Ny*dy/Ly, Nx*dx/Lx)` rounded to Python floats, each finite and strictly positive. Frequency vectors use output canonical bins divided by the original corresponding field length (Nz*dz, Ny*dy, Nx*dx), avoiding overflowing intermediate products where a representable quotient exists. They are finite, strictly increasing/noncollapsed when length>1, zero exactly at the centered DC, and obey the same `8*eps*abs(f_exact)+q` component budget. A nonfinite/zero converted output spacing or nonfinite/collapsed output frequency grid rejects the operation with the grid code. No arbitrary practical dimension cap is imposed; allocation MemoryError propagates.

Return frozen-binding `Reconstruction3D` with exactly six fields: `volume` and `spectrum`, native complex128 C-contiguous independently owned mutable ndarrays `(Nz,Ly,Lx)`; `fz_per_um`, `fy_per_um`, `fx_per_um`, native float64 C-contiguous independently owned mutable vectors; `voxel_size_um`, a Python-float triple of output spacings. Each array owns separate storage, aliases no input/other output and aliases no other call. Field rebinding and deletion fail; contents remain mutable. Direct record construction need not validate.

Use native float64/complex128 arithmetic. Phase solving follows its existing contract. The production transform seams are public `numpy.fft.fftn` for each separated spatial band and `numpy.fft.ifftn` for synthesis, over all three spatial axes without transforming an order/orientation axis. Separate or batched calls, equivalent spatial-axis permutations and equivalent normalization arrangements are permitted. Forward coefficients divide by M; inverse synthesis performs the positive-exponent sum without an extra output normalization. Transform sizes are unchanged from their respective band/output grids. Call counts/private organization are unspecified; exact-zero bands may bypass their forward transform.

Avoid raw-sum overflow in band transforms and synthesis by scaling finite real/imaginary components before transforms, then restoring components separately. A zero scale can use one. No complex magnitude/division overflow may reject a permitted finite input merely while computing such a scale. Forward FFT scaling must occur before an unnormalized sum; a normalized transform or an equivalent safe arrangement is valid. The estimator's arithmetic range is deliberately operational: gain-times-transfer, squares, products, sums, denominator, division/mask and restored coefficients/volume must be finite. A nonfinite estimator stage rejects with the range code, even if a differently scaled mathematical quotient would be finite. No universal acceptance of every exact-real finite answer is selected. Underflow to zero is permitted; no clipping, saturation, partial results or fallback is allowed.

During normalized numerical FFT execution, FloatingPointError, OverflowError, arithmetic RuntimeWarning or nonfinite transform coordinates produce the transform code. The arithmetic-warning rule applies even under a caller ignore filter. A nonfinite restored transform component uses the range code. MemoryError and unrelated exceptions, including transform RuntimeError/TypeError/ValueError, propagate. Expected input conversion TypeError/ValueError/OverflowError translates to its representation error. Preserve caller NumPy floating policy and warning filters; handled conversion/range arithmetic emits no RuntimeWarning. Do not suppress unrelated warning categories.

## Informative accuracy and mandatory success

Let eps=2^-52, q=2^-1074, J=5R, M=Nz*Ny*Nx, P=Nz*Ly*Lx and B=max(abs(converted images)). For the informative regime require: each represented phase matrix has condition number <=10; every gain is in [1/2,2]; every supplied transfer real/imaginary component has absolute value <=1; lambda<=1; every positive exact V+lambda is >=1/4; `65536*J*(N+M+P)*eps <= 2^-10`; and `64*J*P*max(B,q) <= F`, where F is maximum float64. These conditions are sufficient success/accuracy conditions, never input rejection cutoffs. Absent genuine dependency/resource failure, otherwise-valid inputs in this regime must succeed.

Against the exact-real stored-input estimator (including the exact least-squares solution of the represented phase matrix), require each complex output's modulus error to satisfy

```text
beta_S = 65536*J*(N+M)*eps*B + 256*J*(N+M)*q
abs(spectrum_returned - T_exact) <= beta_S
abs(volume_returned - volume_exact)
    <= P*beta_S + 16384*J*P*eps*B + 64*P*q.
```

Evaluate regime inequalities, bounds and independent expectations in sufficient precision. A zero or overflowing observer bound proves nothing. These conservative absolute intensity-unit budgets are project choices, not relative/subnormal-retention guarantees or backend theorems. The inherited informative separator bound, normalized band-transform error and bounded weighted arithmetic motivate the spectrum allowance; summing P coefficients and synthesis roundoff motivate the volume allowance. Independently justified tighter analytic checks must distinguish sign, factor, placement and complex phase. Successful calls with all-zero converted images return exact zero volume/spectrum; in the informative regime such calls must succeed. Outside the regime zero data does not waive an operational transfer/gain range failure. Outside the informative regime the defined estimator still applies with the operational range boundary and no uniform digit guarantee. Unrounded specimen truth and rounded-data estimator truth are separate comparisons.

## Errors

Use existing `SimreconError` (ValueError) with stable string code/message. Message prose and simultaneous-error precedence are unspecified. Prerequisite phase errors propagate unchanged.

| Rejected obligation | Code |
|---|---|
| Plain image ndarray | invalid_volume_reconstruction_images |
| Image i/u/f dtype | invalid_volume_reconstruction_dtype |
| Image `(R>=1,N>=5,positive_z,positive_y,positive_x)` shape | invalid_volume_reconstruction_shape |
| Finite source/converted images | nonfinite_volume_reconstruction_images |
| Plain phases ndarray, i/u/f dtype, `(R,N)` shape | invalid_volume_reconstruction_phases |
| Finite source/converted phases | nonfinite_volume_reconstruction_phases |
| Plain exact-integer carrier ndarray and `(R,2)` shape | invalid_volume_reconstruction_carriers |
| Plain gains ndarray, i/u/f dtype and `(R,)` shape | invalid_volume_reconstruction_gains |
| Finite source/converted, strictly positive converted gains | invalid_volume_reconstruction_gain_values |
| OTF container/count/type or any field/metadata/grid/spacing agreement | invalid_volume_reconstruction_otfs |
| Real nonboolean scalar, finite nonnegative converted lambda | invalid_volume_reconstruction_regularization |
| Shape container/integer/positive/native-index limits or insufficient signed window | invalid_volume_reconstruction_output_shape |
| Plain apodization ndarray, i/u/f dtype and exact output shape | invalid_volume_reconstruction_apodization |
| Source/converted finite mask values in [0,1] | invalid_volume_reconstruction_apodization_values |
| Unrepresentable output spacing/frequency grid | unrepresentable_volume_reconstruction_grid |
| Handled numerical FFT failure/nonfinite normalized transform | volume_reconstruction_transform_failure |
| Nonfinite computed estimator/restoration/output stage | unrepresentable_volume_reconstruction |

## Behavioral inventory and delivery

| ID | Distinct obligation; equivalent examples |
|---|---|
| W01 | Stored-input five-order complex estimator; asymmetric unequal-axis direct-sum oracle |
| W02 | Full complex transfer weighting, unequal positive gains and orientation overlap; no magnitude substitution |
| W03 | Native z, nonwrapping exact signed lateral placement; opposite/repeated/zero carriers |
| W04 | Complete explicit output window and insufficient-grid rejection even for zero transfers/mask |
| W05 | Modular negative-order conjugation on every detector axis, including even Nyquist |
| W06 | Canonical complex Nyquist lifting without Hermitian projection, splitting or real truncation |
| W07 | Forward/inverse normalization, gain once and no extra side factor/modulation |
| W08 | Explicit ridge/mask, zero denominator and zero side orders; shared phase gauge/origin encoded once |
| W09 | Existing volume separator composition, arbitrary known N>=5 phases and off-model projection |
| W10 | Input widths/endian/storage/signed values/finite conversion and snapshots |
| W11 | Image representation/dtype/shape and source/converted finiteness errors |
| W12 | Phase representation/shape/finiteness and prerequisite rank/solver/range errors |
| W13 | Exact carrier representation/integer shape and large unsigned values versus geometry rejection |
| W14 | Gain representation/shape and finite positive converted values |
| W15 | Full directly constructed OTF validation, allowed layouts/metadata alternatives and common spacing |
| W16 | Scalar regularization and paired valid positive/zero values |
| W17 | Output size containers/scalars/native index boundaries and no practical cap |
| W18 | Mask representation/shape and source/converted finite [0,1] bounds |
| W19 | Field of view, output spacings and representable/collapsed/nonfinite frequency grids |
| W20 | Exact record fields, frozen binding/deletion, mutable independent owned arrays |
| W21 | Input preservation and caller error/warning policy on success/rejection |
| W22 | Informative accuracy, safely finite mandatory success, zero/subnormal stored-input cases |
| W23 | Operational arithmetic range rejection and scaled forward/inverse transform restoration |
| W24 | Controlled FFT failures/nonfinite outputs versus unrelated exceptions/MemoryError |
| W25 | Ordinary Python binding, existing APIs/gates/dependencies and no I/O |
| W26 | Executed usage and actual independent arrays/JSON/PNG/SVG signed complex comparison, with physical limits |

A owns `tests/test_volume_reconstruction.py` and `tests/volume_reconstruction_fixture.py`; derives independent finite-sum/stored-input oracles and maps all scenarios/high-risk paths. B independently challenges oracle validity, positive alternatives and omissions before accepting an exact frozen checkpoint. C owns only `src/simrecon/volume_reconstruction.py`, export additions in `src/simrecon/__init__.py`, `docs/usage/volume-recombination.md`, and report/JSON/PNG/SVG files named by its candidate packet. C may not edit reviewed tests, fixtures, gates, workflows, dependencies, skills or unrelated interfaces. Root owns intake/registry/task pointer and ignored execution evidence; scoped setup support changes no tracked gate. Fresh D assesses the exact passing candidate before any current-task lesson payload.

Route is high-risk numerical/custom-oracle: fresh native A/B/C/D, with gpt-6.1-sol/high conservative selection and memory/delegation disabled. Cheap locked environment and source-free Python/pytest/subprocess diagnostics precede blind probes. Initially passing tests are valid; absent API setup failure is not product-red. PROJECT coverage policy remains behavior/risk review plus complete native global/package/file/platform JSON/HTML statement/branch reports; percentages advisory, no threshold/exclusions. Canonical exact clean committed `make verify` passes before D/publication. Audit Ubuntu 24.04/macOS 15 push and PR legs, exact head/base/integration/ordered parents, provider/job/upload/artifact/archive/report/wheel identities separately. Human numeric limits are not set. Merge/release and unrelated external messages are not authorized. Preserve prior ledger chain and every review/repair/failure/exposure; missing metering/cost/served attribution is unknown.

Opened primary references: [NumPy Fourier sign, normalization and Nyquist](https://numpy.org/doc/stable/reference/routines.fft.html), [fftn axes and normalization](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), [ifftn synthesis](https://numpy.org/doc/stable/reference/generated/numpy.fft.ifftn.html), and [Gustafsson et al. equations 5–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). The interface, estimator, budgets and operational domain are project choices. Prerequisites: [volume phases](volume-phase-separation-v1.md), [volume OTF](volume-otf-preparation-v1.md), [effective orders](volume-order-transfers-v1.md).
