# VOLUME-ORDER-01: known axial-profile effective transfers

**Version 1.0.** October 9, 2026. The owner's continuing instruction, “Keep on stacking in a new task! Continue that pattern until the roadmap is complete,” authorizes this coherent slice above verified, independently accepted PR #17. This contract records that scope before test authorship.

## Operation and scientific meaning

Prepare three finite periodic effective optical transfer functions (OTFs) from a supplied nonnegative detection intensity point spread function (PSF) and two supplied complex axial coefficient rows. Structured illumination microscopy (SIM) phase orders are fixed at 0, +1, +2. The operation estimates no coefficients, instrument parameters, origin or sampling.

```python
from simrecon import VolumeOrderOtf, prepare_volume_order_otfs

orders = prepare_volume_order_otfs(
    psf,
    axial_coefficients=coefficients,
    voxel_size_um=(dz, dy, dx),
    origin_zyx=(oz, oy, ox),
    source="caller PSF and axial-profile identity",
)
```

Only `psf` is positional. Every keyword is required. Ordinary Python argument-binding TypeError applies. Axes are z/y/x; the leading output axis is order 0, +1, +2, never an orientation or spatial axis.

PSF, voxel spacing, origin and source accept precisely the representations and validation rules of [VOLUME-OTF-01](volume-otf-preparation-v1.md): plain ndarray, three positive dimensions, real i/u/f kinds at all available widths/byte orders, finite nonnegative source and finite converted float64 samples, positive converted mass; explicit finite positive spacing in micrometres; integer in-bounds origin; nonblank unchanged string source. Signed zero, singleton axes, noncontiguous/read-only arrays and finite conversion underflow are permitted. Negative source values remain invalid even if conversion would produce negative zero. Preserve all inputs on success and failure.

`axial_coefficients` is a plain NumPy ndarray of shape `(2,Nz)`. Row 0 supplies g1; row 1 supplies g2. Accept dtype kinds i/u/f/c at every available width and byte order; reject bool, object and other kinds, nonarrays and subclasses. Every source real and imaginary component must be finite before an independent native complex128 snapshot. Every converted real and imaginary component must also be finite. Conversion rounding and finite underflow define the stored problem, including wider complex types. Zero rows, signed values, arbitrary phases, coefficients greater than one and complex values whose magnitude would overflow despite finite components are permitted. No sign, magnitude, support, DC or physical-realizability threshold applies. Snapshot both arrays before numerical transforms. Concurrent caller mutation is outside the promise.

Let a and g1/g2 denote exact values of these converted snapshots, M=Nz*Ny*Nx, S=sum(a)>0, p=a/S and g0[z]=1. Define, for m in {0,1,2},

```text
K_m[z,y,x] = p[z,y,x] * g_m[z]
E_m[kz,ky,kx] = sum(z,y,x) K_m[z,y,x] * exp(-2*pi*i*[
  kz*(z-oz)/Nz + ky*(y-oy)/Ny + kx*(x-ox)/Nx])
```

These equations use exact real arithmetic on stored inputs as the expectation. Normalize detection mass once. Do not normalize individual orders by DC, peak or magnitude. E0 equals the normalized detection transfer within its stated accuracy; Em at DC is the complex weighted mean of gm, which may be zero. Relative side-order gains and phases remain. Keep signed real and imaginary values; no clipping, conjugation, real projection, padding, cropping, support inference or interpolation.

Coefficients are sampled on axial **displacement** coordinates `(z-oz)*dz`, in the same frame as the PSF. The caller supplies values in this frame; the operation does not rephase or resample a table. For an integer axial mode l, `g[z]=c*exp(2*pi*i*l*(z-oz)/Nz)` gives `E(k)=c*H(kz-l,ky,kx)` with modular mode indexing. A cosine gives the corresponding half-sum of shifted H. Jointly rolling PSF and coefficient rows and changing origin by the same periodic shift preserves this mathematical transfer.

For real detection p and the convention g_-m=conj(g_m), `E_-m(k)=conj(E_m(-k))`. Negation is modular on every axis, including the single even-axis Nyquist bin; simple reversal of centered arrays is generally wrong. Only nonnegative orders are returned. Side orders are generally not Hermitian individually. Multiplying a coefficient row by exp(i*theta) multiplies its transfer by that phase; no phase gauge is inferred.

The finite circular forward model is `c_m=K_m*u_m`, where * is circular convolution in declared displacement coordinates. Raw phase volumes then have `dc + 2*Re(c1*exp(i*phi)+c2*exp(2*i*phi))`, matching the existing volume-separation convention. With lateral carrier q and real specimen s, u_m can be `s*exp(2*pi*i*m*q.r_xy)`; carrier factors are outside this operation. No factor of two is folded into E1/E2.

The physical interpretation requires the axial illumination profile to remain fixed relative to the objective focal plane during scanning, so its axial factor shares the PSF's displacement frame (Gustafsson et al., equations 5–9). A general specimen-fixed axial illumination field multiplies the specimen instead and is not represented by this effective kernel. Arbitrary tables remain valid algebraic inputs; they need not describe a nonnegative illumination intensity, realizable optics or a measured instrument. The selected g0=1 excludes an axial zero-order profile. Detection throughput is discarded; side gains are relative to that normalized detection convention. No infinite-field, continuous-optics convergence, acquisition validity, support recovery or reconstruction guarantee is made.

## Numerical and range boundary

Use float64/complex128 arithmetic. For each side row set G_m=max_z(max(abs(Re(g_m[z])),abs(Im(g_m[z])))); use G_m=1 for an all-zero row; G0=1. Scale real and imaginary components separately, so complex division/magnitude overflow cannot exclude permitted finite inputs. Normalize p without raw-sum overflow or loss of all-subnormal positive mass.

The production transform boundary is public `numpy.fft.fftn`, with default/backward forward normalization and all three spatial axes, applied to the origin-rolled normalized kernels `p*(g_m/G_m)` (g0=1). Separate calls or a batched call are permitted; do not transform the leading order axis. Real or zero-imaginary complex detection kernels, equivalent spatial-axis permutations and unchanged transform sizes are legitimate. The public seam supports controlled operation-time failure tests; call counts and private organization are unspecified. A zero side row may bypass its transform.

Rescale each transformed real/imaginary component by G_m in native float64 arithmetic. Return only if all normalized-transform and rescaled components are finite. A nonfinite rescaled result rejects the entire operation with `unrepresentable_volume_order_otf`. This is an operational computed-range boundary, not an exact-real overflow classifier: roundoff near maximum float64 may decide the outcome. No promise requires acceptance or rejection based only on exact-real representability at that boundary. Do not saturate, clip or return a partial result.

Let eps=2^-52 and q=2^-1074. For every successfully returned complex sample require

```text
abs(E_returned - E_exact) <= 256*M*eps*G_m + 8*M*q
```

Evaluate this bound and independent expectations without overflow/underflow in the observer. It is an absolute dimensionless project budget, not a relative accuracy or subnormal-retention guarantee. The additive q term covers final subnormal rounding: exact q/2 cannot be represented. Tiny contributions may disappear within this budget. For m=0 retain the tighter inherited detection-transfer budget `128*M*eps + 4*M*q`. Neither budget proves a backend error theorem.

The finite normalized transform T also obeys `abs(T-E_exact/G_m)<=delta`, where `delta=128*M*eps+4*M*q`. This is a new project accuracy obligation, not inherited proof from detection preparation. Let F be maximum float64. Absent genuine dependency/resource failure, otherwise-valid inputs must succeed whenever every exact output component satisfies `abs(E_exact_component)+G_m*delta<=F`. The simpler input condition `G_m*(sqrt(2)+delta)<=F` is sufficient. These are success guarantees, never input rejection cutoffs. Exact expectations and these inequalities use sufficient precision. Source mass-sum or complex-magnitude overflow alone must not reject such inputs. At an origin delta, finite components F+iF remain valid despite overflowing magnitude.

Frequency grids, centered order, finite/increasing/noncollapsed rejection and coordinate accuracy inherit VOLUME-OTF-01 exactly: integer modes `-floor(N/2)..ceil(N/2)-1`, frequency k/(N*d) cycles/µm, DC index N//2, negative even Nyquist without duplicate, zero exact, error `8*eps*abs(f_exact)+q`. Avoid overflowing intermediate N*d where the quotient is representable. Singleton spacing q or maximum float64 is valid.

Preserve caller NumPy floating policy and warning filters. Handled conversion/range operations emit no arithmetic RuntimeWarning. During numerical transform, FloatingPointError, OverflowError, arithmetic RuntimeWarning or nonfinite normalized-transform values reject with `volume_order_transform_failure`. Nonfinite final rescaling uses the range code above. MemoryError and unrelated exceptions, including transform RuntimeError/TypeError/ValueError, propagate unchanged. Do not suppress unrelated warning categories. No practical-size, throughput or working-set promise is selected; output allocation MemoryError propagates.

## Record, errors and compatibility

Return frozen-binding `VolumeOrderOtf` with exactly seven public fields: `values` native complex128 C-contiguous independently owned mutable ndarray `(3,Nz,Ny,Nx)`; `fz_per_um`, `fy_per_um`, `fx_per_um` corresponding native float64 C-contiguous independently owned mutable one-dimensional arrays; `voxel_size_um` Python-float triple; `origin_zyx` Python-int triple; `source` unchanged caller string. All four arrays own separate storage, alias no input/other output and alias no other call's arrays. The binding is frozen; array contents remain mutable. Direct record construction needs no validation. Slices of values may share its own storage. Preparation does no files, hashing, authentication or persistence; source is an opaque label, not verified provenance.

Use existing `SimreconError` (ValueError) with string code/message. Prose and simultaneous-error precedence are unspecified. Inherited PSF/spacing/origin/source/frequency errors keep their exact VOLUME-OTF-01 codes. New errors are:

| Rejected obligation | Code |
|---|---|
| Plain coefficient ndarray | invalid_volume_order_coefficients |
| Coefficient dtype kind i/u/f/c | invalid_volume_order_coefficients_dtype |
| Coefficient shape `(2,Nz)` | invalid_volume_order_coefficients_shape |
| Finite source and converted coefficient components | nonfinite_volume_order_coefficients |
| Handled transform failure/nonfinite normalized transform | volume_order_transform_failure |
| Nonfinite final rescaled transfer | unrepresentable_volume_order_otf |

Expected conversion TypeError/ValueError/OverflowError translate to their corresponding representation code; unrelated exceptions and MemoryError propagate. Existing APIs, CLI, dependencies, workflows, discovery and verification/coverage gates remain unchanged. No estimator, negative-order return API, lateral relocation, physical profile fitting, measured-instrument calibration, recombination or adapter is included.

## Behavioral inventory and evidence

| ID | Distinct obligation; equivalent examples |
|---|---|
| V01 | Full signed complex three-order direct sum; asymmetric nonseparable PSF and unequal axes |
| V02 | Normalize detection once, E0 consistency, preserve relative gains/phases and zero DC/zero side rows |
| V03 | Origin/displacement convention and joint translation invariance; off-center odd/even origins |
| V04 | Axial phasor shifted transfer and cosine half-sum; no lateral shift or extra phase |
| V05 | Nonnegative order layout and modular negative-order conjugation; even Nyquist versus array reversal |
| V06 | Frequency coordinates and preserved grid; anisotropic odd/even/singleton axes |
| V07 | Permitted coefficient kinds/widths/endian/storage and converted-value meaning; real and complex, wider where native |
| V08 | Exact record fields/storage/frozen bindings/direct construction; content remains mutable |
| V09 | Independent snapshots, input preservation and mutually independent outputs/calls |
| V10 | Coefficient nonarray/subclass rejection versus plain ndarray |
| V11 | Invalid coefficient kind rejection versus all permitted kinds |
| V12 | Invalid coefficient rank/rows/z length versus valid singleton z |
| V13 | Source nonfinite coefficients versus finite component extrema |
| V14 | Converted nonfinite coefficients versus finite wider conversion/underflow where native |
| V15 | Inherited PSF representation/finiteness/negative/zero-mass rules and positive extrema |
| V16 | Inherited spacing/origin/source validation with paired permitted containers/scalars |
| V17 | Extreme detection normalization and extreme component gains without magnitude overflow |
| V18 | Cancellation/subnormal accuracy with independent stored-input bounds; no relative promise |
| V19 | Representable extreme frequency grids versus nonfinite/collapsed grids |
| V20 | Nonfinite final rescaling rejects; safely finite scaled results succeed; boundary uncertainty explicit |
| V21 | Controlled transform failures/nonfinite values reject; unrelated exceptions/MemoryError propagate |
| V22 | Caller floating/warning policy preservation on success and failure |
| V23 | Ordinary Python argument binding |
| V24 | Circular forward-model/real volume-separator composition with caller-known coefficients and phase signs |
| V25 | Existing APIs/gates/dependencies remain; no persistent side effects |
| V26 | Executed standalone usage and actual independent signed comparison/figure with physical limits |

No scenario cap applies. A maps distinct outcomes and coverage examples to public-entry tests and independently derives direct-sum/exact-root expectations and sufficient-precision bounds. Existing reviewed prerequisite tests need not be duplicated. B independently recalculates oracles and audits permitted alternatives and omissions. C supplies measured input/expected/output arrays and hashes, all-order signed real/imaginary comparison on shared scales, absolute errors/budgets and explicit gain-scaled range cases. D checks actual arrays/figure correspondence and composition; a visual is not a correctness oracle.

Route: high-risk scientific/numerical/custom-oracle; fresh native blind A, fresh native blind B, restricted fresh native C, exact-candidate canonical `make verify`, fresh native D. PROJECT's selected policy is behavior/risk review and complete native JSON/HTML statement/branch report integrity per owned package/platform; percentages advisory, no threshold or exclusions. Audit all configured Ubuntu 24.04/macOS 15 push/PR legs separately. Human numeric limits are not set. No merge/release authority applies.

Opened primary references: [NumPy FFT convention](https://numpy.org/doc/stable/reference/routines.fft.html), [fftn](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), and [Gustafsson et al. equations 5–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). API choices and numerical budgets are this project's contract.
