# VOLUME-OTF-01: sampled 3D intensity PSF preparation

**Version 1.0.** Authorized October 8, 2026 by the owner's request to implement the next coherent roadmap slice above verified PR #16. This contract records that scope; no additional approval checkpoint applies.

## Scope and public interface

Prepare a caller-supplied, finite sampled nonnegative intensity point spread function (PSF) for a linear shift-invariant three-dimensional imaging model. Return its normalized full complex optical transfer function (OTF). This is a discrete preparation primitive, not estimation of instrument calibration or physical order-specific structured illumination microscopy (SIM) transfer functions. No background, origin, sampling or illumination parameter is inferred.

```python
from simrecon import Otf3D, prepare_volume_otf

calibration = prepare_volume_otf(
    psf,
    voxel_size_um=(dz, dy, dx),
    origin_zyx=(oz, oy, ox),
    source="caller-supplied calibration identity",
)
```

Only `psf` is positional. All keywords are required; ordinary Python `TypeError` applies to missing, positional or extra keywords.

`psf` must be a plain NumPy ndarray of shape `(Nz,Ny,Nx)` with three positive dimensions. Accept real signed integer, unsigned integer and floating dtype kinds, all available widths and byte orders. Reject bool, complex, object and other kinds, nonarrays and ndarray subclasses. Read-only arrays, strided/reversed views, odd/even or unequal dimensions and singleton axes are permitted.

Check source samples for finiteness and nonnegativity before making an independent native float64 copy. Converted samples must be finite, with at least one strictly positive value. Conversion rounding/underflow defines the stored problem, including int64/uint64 and wider floating values. Source negatives that would become negative zero remain invalid. Signed zero is nonnegative; all-zero converted mass rejects. No mutation of inputs is permitted on success or failure.

Each triple accepts tuple, list or plain one-dimensional ndarray of length three. Spacings are non-boolean Python/NumPy real integer/floating scalars converted individually to float64, finite and strictly positive in micrometres (µm). Origins are non-boolean Python/NumPy integer scalars within the corresponding axis bounds; never round, wrap or infer an origin. Source is a Python string containing a non-whitespace character; retain its supplied text unchanged. It is an opaque label, not verified provenance.

## Mathematical meaning

For exact real values `a[z,y,x]` of the converted float64 samples, define

```text
M = Nz*Ny*Nx
S = sum(z,y,x) a[z,y,x] > 0
p[z,y,x] = a[z,y,x]/S
H[kz,ky,kx] = sum(z,y,x) p[z,y,x] * exp(-2*pi*i*[
    kz*(z-oz)/Nz + ky*(y-oy)/Ny + kx*(x-ox)/Nx])
```

The forward sign is negative. No `1/M` factor follows the sum; unit discrete mass gives DC one. Uniform voxel volume cancels; p is mass per sample, not density in µm^-3. Absolute throughput is deliberately discarded. Positive common gain preserves H only if converted samples remain exactly proportional. Keep signed real and imaginary parts, including negative transfer values. Do not take magnitude, square, conjugate, force real, infer phase centering or normalize a peak.

Each axis uses integer modes `-floor(N/2),...,ceil(N/2)-1` in increasing order, with frequencies `k/(N*d)` in cycles/µm for exact converted spacing d. The values array uses the matching full `fftshift` order on all three axes; DC is at `(Nz//2,Ny//2,Nx//2)`. Even axes have a negative Nyquist endpoint with no positive duplicate. Positive z/y/x indices correspond to increasing spatial coordinates. Roll the explicitly declared origin to zero, apply the unnormalized forward transform and shift frequencies to obtain the stated formula. Preserve every supplied axis and grid; no padding, cropping, interpolation, support inference, clipping, radial averaging or optical model occurs.

This is a finite discrete periodic kernel. It supplies no infinite-field or continuous-optics convergence guarantee. Mathematical checks include `abs(H)<=1` and modular Hermitian symmetry; they are not clipping rules. In physical 3D SIM, effective order transfers may involve the detection PSF multiplied by order-dependent axial illumination factors. Those factors and relative gains are absent here. One Otf3D cannot be substituted for that calibration merely because the observed phase components are volumes. Later order-specific calibration and recombination require separate contracts.

## Numerical, range and failure boundaries

Use float64/complex128 arithmetic. The production transform boundary is NumPy's public `numpy.fft.fftn`, applied to the normalized volume with the declared origin rolled to zero and all three spatial axes transformed, using default forward normalization. This named dependency supplies a real-caller seam for controlled U25 failure tests without reading implementation. The origin roll and final full-spectrum shift remain as defined above. Avoid raw-sum overflow and loss of all-subnormal positive mass: all-maximum and all-positive-subnormal kernels are valid. Let eps=2^-52 and q=2^-1074. For every complex transfer sample require

```text
abs(H_returned-H_exact) <= 128*M*eps + 4*M*q
```

This is a conservative absolute dimensionless project budget, not a backend theorem or relative/subnormal-retention promise. Use independent sufficiently precise/scaled expectations. Tiny contributions may disappear within this absolute budget; mathematical support is not thresholded.

Each returned frequency coordinate must obey `abs(f_returned-f_exact)<=8*eps*abs(f_exact)+q`. Zero modes return exact zero. All coordinates must be finite and strictly increasing on nonsingleton axes; each nonzero mode must remain nonzero. Reject nonfinite, collapsed or unordered final grids. Avoid intermediate `N*d` overflow when the final quotient is representable. A singleton axis has only zero and accepts every converted finite positive spacing, including q and maximum float64.

Scoped arithmetic preserves the caller's NumPy floating-error policy and emits no arithmetic RuntimeWarning for handled cases. During the numerical transform, FloatingPointError, OverflowError or arithmetic RuntimeWarning, and nonfinite computed transfer values, reject the entire operation with `otf_transform_failure`. MemoryError and unrelated exceptions (including RuntimeError, TypeError and ValueError from a transform) propagate. Do not return partial outputs or silently replace the model. No throughput, working-set or practical-size promise is selected. Output-allocation MemoryError propagates.

## Result, errors and compatibility

Return frozen-binding `Otf3D` with exactly these public fields:

| Field | Representation |
|---|---|
| values | `(Nz,Ny,Nx)` native complex128 C-contiguous independently owned mutable ndarray |
| fz_per_um, fy_per_um, fx_per_um | Corresponding `(Nz,)`, `(Ny,)`, `(Nx,)` native float64 C-contiguous independently owned mutable ndarrays |
| voxel_size_um | Converted `(dz,dy,dx)` Python-float tuple |
| origin_zyx | Validated `(oz,oy,ox)` Python-int tuple |
| source | Caller string unchanged |

All four arrays own separate storage, alias no input or one another, and alias no other call's output. Frozen bindings do not freeze contents. Direct record construction needs no validation. Preparation performs no file access, hashing, authentication or persistence. Caller provenance should record source identity, preprocessing, spacing, origin and resolved software; the label alone proves none of these.

Use existing `SimreconError` (ValueError) with string code/message. Exact prose and precedence for simultaneous violations are unspecified.

| Rejected obligation | Code |
|---|---|
| Plain PSF ndarray | invalid_psf |
| Real integer/floating PSF dtype | invalid_psf_dtype |
| Three positive dimensions | invalid_psf_shape |
| Finite source and converted samples | nonfinite_psf |
| Nonnegative source | negative_psf |
| Positive converted mass | zero_psf_mass |
| Valid finite positive spacing triple | invalid_otf_voxel_size |
| Valid integer origin triple in bounds | invalid_otf_origin |
| Nonblank string source | invalid_otf_source |
| Representable ordered final frequency grids | unrepresentable_otf_frequencies |
| Handled numerical transform failure/nonfinite result | otf_transform_failure |

Existing APIs, dependencies, CLI, workflow, discovery, verification and coverage gates remain unchanged. No runtime Pyotf, bead fitting, coherent-field PSF, order-specific effective transfer, specimen reconstruction, unknown phase fit, fractional drift or acquisition adapter is included.

## Behavioral inventory and independent evidence

| ID | Distinct obligation and paired coverage examples |
|---|---|
| U01 | Full signed complex normalized 3D DFT; asymmetric mass across all three axes versus magnitude/conjugation/axis errors |
| U02 | Explicit origin phase and joint periodic translation invariance; off-center odd/even origins |
| U03 | Matching full signed physical frequency grids; anisotropic spacing and unequal odd/even/singleton axes |
| U04 | Unit discrete mass and exact-proportional gain invariance; delta/constant kernels, no voxel-density or peak scaling |
| U05 | Preserve supplied grid/complex/negative transfer; no support clipping, radial average or resampling |
| U06 | Permitted real widths/byte orders and converted-value meaning; int64/uint64 and available wider floats |
| U07 | Exact result fields/dtypes/shapes/C storage/frozen bindings; direct construction permitted |
| U08 | Input preservation/snapshots and four mutually independent arrays and independent calls |
| U09 | Nonarray/subclass rejection versus ordinary ndarray |
| U10 | Nonreal/bool dtype rejection versus every permitted real kind |
| U11 | Rank/empty-dimension rejection versus valid singleton/nonsquare volumes |
| U12 | Source nonfinite rejection versus finite extrema |
| U13 | Converted overflow rejection versus representable wider samples where available |
| U14 | Source negative rejection including underflow-to-negative-zero versus signed zero |
| U15 | Zero converted mass rejection versus positive subnormal mass |
| U16 | Malformed/nonreal/bool spacing triples reject versus all permitted containers/scalars |
| U17 | Converted nonfinite/nonpositive spacing rejects versus representable finite positives |
| U18 | Malformed/noninteger/bool origin triples reject versus Python/NumPy integers |
| U19 | Out-of-bounds origins reject versus all legal indices; no wrapping |
| U20 | Nonstring/blank source rejects versus unchanged surrounding whitespace with content |
| U21 | Extreme positive mass normalization; all-max, all-subnormal and mixed magnitudes |
| U22 | Absolute complex transfer accuracy near cancellation, independent stored-input oracle |
| U23 | Representable extreme frequency grids; avoid intermediate product overflow, singleton q/max |
| U24 | Nonfinite/collapsed/unordered frequency grids reject despite valid positive spacing |
| U25 | Handled transform failure and nonfinite result reject; unrelated/MemoryError propagate |
| U26 | Preserve caller floating policy; source-free arithmetic-warning handling under supported error modes |
| U27 | Ordinary Python argument binding |
| U28 | Existing APIs/gates/dependencies preserved; no file or simulator side effects |
| U29 | Executed standalone usage and measured independent signed comparison with honest physical limits |

These rows impose no cap; A maps distinct outcomes/rejections/guarantees and equivalent examples. A independently derives small direct-sum or exact-root 3D expectations, origin/gain checks and sufficiently precise frequency/range observers. Product FFT/output and legacy code are not oracles. B independently recalculates expectations and challenges permitted inputs/omissions before C. C supplies actual public-entry comparison arrays, input/expected/output hashes and a signed real/imaginary plot or table on shared scales with maximum errors/budgets. Include asymmetric nonseparable input, anisotropic odd/even axes, origin translation and range cases. D checks arrays and correspondence; illustrations are not correctness evidence.

High-risk scientific/custom-oracle route: fresh native blind A, fresh native blind B, restricted fresh native C, exact-candidate canonical `make verify`, fresh native D. Inherit PROJECT's behavior/risk policy and complete native JSON/HTML report integrity on all configured Ubuntu 24.04/macOS 15 push/PR legs; percentages advisory, no selected threshold or exclusions. No numeric scenario/review/repair/time/execution limits were set. The task pointer links accounting and prior chain outside tracked candidate bytes.

Opened primary references: [NumPy multidimensional DFT convention](https://numpy.org/doc/stable/reference/routines.fft.html), [N-dimensional transform](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), [full centered order](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftshift.html), and [Gustafsson et al., equations 5–9 and Transfer functions](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) for the distinction between a detection PSF and order-specific effective transfers. Exact acceptance budgets and API/error choices are this project's contract.
