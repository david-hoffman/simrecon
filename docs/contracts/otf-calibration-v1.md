# OTF-CALIBRATION v1: sampled 2D intensity PSF preparation

**Version 1.1.** Approved numerical contract, October 6, 2026. The owner requested implementation of `prepare_otf` and `Otf2D` after the calibration foundations in PR #6 integrated. This document defines that authorized operation; it creates no extra document-approval checkpoint. K01–K29 and their numerical meaning remain unchanged.

## Scientific scope and public interface

A point spread function (PSF) here is a finite, sampled, nonnegative intensity kernel for a linear, shift-invariant, incoherent 2D imaging model. The optical transfer function (OTF) is its normalized discrete Fourier transform (DFT). This is a preparation boundary, not estimation of an instrument's calibration or a complete reconstruction model. The caller supplies a background-corrected kernel and its spatial origin; the operation does not estimate either.

The intended public interface is:

```python
from simrecon import Otf2D, prepare_otf

calibration = prepare_otf(
    psf,
    pixel_size_um=(dy, dx),
    origin_yx=(oy, ox),
    source="caller-supplied calibration identity",
)
```

Only `psf` is positional. All three keywords are required. A missing, positional or extra keyword keeps ordinary Python `TypeError` behavior. No implicit pixel size, geometric center, peak center, optical model or source is selected.

`psf` is a plain NumPy ndarray with shape `(Ny, Nx)`, both dimensions positive. Accept real signed integer, unsigned integer and floating dtype kinds, all available widths and either byte order. Bool, complex, object and other kinds are rejected, as are nonarrays and ndarray subclasses. Read-only arrays, strided/reversed views, singleton axes, odd/even dimensions and nonsquare kernels remain permitted.

All source samples must be finite and nonnegative before conversion. Make an independent ordinary float64 copy; converted samples must also be finite. Conversion rounding and underflow define the stored problem. This includes rounding int64/uint64 and wider floats; overflow during conversion is rejected. A wider negative value that would convert to negative zero remains invalid at the source check. At least one converted sample must be strictly positive. Signed zero is nonnegative, but an all-zero converted kernel has no normalization and is rejected.

Each pair argument accepts a tuple, list or plain one-dimensional ndarray of length two. Pixel sizes are non-boolean Python/NumPy real integer/floating scalars, converted individually to float64. Both converted values must be finite and strictly positive, in micrometres (µm). `origin_yx` contains two non-boolean Python/NumPy integer scalars with `0 <= oy < Ny` and `0 <= ox < Nx`; fractional coordinates, negative indices and out-of-range origins are rejected, not rounded or wrapped. The source is a Python string containing at least one non-whitespace character. Retain its supplied text; it is an opaque caller label, not verified provenance or a content hash.

## Mathematical conventions

Let `a[y,x]` be the exact real value of each converted float64 sample. Define normalization in real arithmetic:

```text
M = Ny * Nx
S = sum(y,x) a[y,x] > 0
p[y,x] = a[y,x] / S
H[ky,kx] = sum(y,x) p[y,x] *
    exp(-2*pi*i*(ky*(y-oy)/Ny + kx*(x-ox)/Nx))
```

The forward sign is negative. No factor `1/M` follows the sum: unit discrete mass already gives `H[0,0] = 1`. Uniform pixel area cancels in this normalization; `p` is probability mass per sample, not a PSF density in µm^-2. The source's absolute throughput/brightness is discarded deliberately and is not recoverable from this calibration. Positive common gain preserves H only when the converted arrays remain exactly proportional; conversion rounding/underflow can change those ratios.

Return the complete complex transfer, including negative real values and phase. Taking absolute value, squaring, forcing a real result, conjugating, phase recentering or normalizing the peak is a different operation. Exact transfer obeys `abs(H) <= 1` and modular Hermitian symmetry because the input is real. These are mathematical sanity checks, not additional clipping rules.

The ordered integer modes for an axis of length `N` are
`[-floor(N/2), ..., ceil(N/2)-1]`. Array values and frequency vectors use that same order. Thus zero frequency is at `(Ny//2, Nx//2)`, even axes have a negative Nyquist bin and no duplicate positive endpoint, and odd axes have both extreme signed bins. In FFT terminology this is the full `fftshift` order. Rolling the explicit spatial origin to `(0,0)`, applying the default unnormalized forward transform and shifting its output gives the stated formula. Do not replace the origin with an inferred half-array shift.

Frequency coordinates are `fy = ky/(Ny*dy)` and `fx = kx/(Nx*dx)`, in cycles/µm, using the exact real values of the converted spacings. Increasing spatial rows/columns correspond to increasing physical y/x. The operation does not swap axes, introduce a `2*pi` frequency unit, interpolate, pad, crop or resample. These sign/normalization/order definitions follow the chosen project convention; NumPy documents the corresponding [DFT](https://numpy.org/doc/stable/reference/routines.fft.html), [frequency bins](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftfreq.html) and [shift](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftshift.html).

This is a discrete periodic kernel on the supplied grid. It is not a guarantee that the finite sampled data reproduce an infinite-field continuous optical response. Array boundaries define the available grid, not a physical numerical-aperture cutoff. Preserve zero, small and out-of-ideal-support transfer values. Do not infer a support mask, threshold or radial average. Later reconstruction must specify any support treatment and its acquisition/optical assumptions separately.

## Precision and representation boundaries

Normalize without avoidable raw-sum overflow. For example, all-max-float input is valid: divide by the maximum before summing scaled nonnegative values. All-subnormal positive input is also valid. That example is a permitted implementation strategy, not the test oracle; expectations come from the exact converted values and equations above.

Let `eps = 2^-52` and `q = 2^-1074`. For each returned complex sample, require

```text
abs(H_returned - H_exact) <= tau
tau = 128 * M * eps + 4 * M * q
```

This is an explicit, conservative project acceptance budget for combined normalization/transform/final rounding, not a theorem about every FFT backend. Its dimensionless absolute form applies near zeros and cancellation; it promises neither relative digits there nor retention of every subnormal component. Evaluate the oracle/budget with enough independent precision that rounded expectations and the `q` term cannot manufacture failures. A must derive its own reference and B must assess the budget's use. The rounded JSON examples below are not a tight-error oracle.

Each frequency coordinate must differ from its exact formula by at most `8*eps*abs(f_exact) + q`. Zero modes return exact zero. Returned coordinates must be finite and strictly increasing on each nonsingleton axis, and every nonzero mode must remain nonzero. Reject a final nonfinite/collapsed/unordered grid as `unrepresentable_otf_frequencies`, even when the positive spacing itself is valid. Avoid intermediate `N*d` overflow when the final quotient is representable. A singleton axis returns only zero and accepts every finite positive converted spacing, including the smallest subnormal and largest float64 value.

No throughput, peak memory or practical-size promise is selected. Allocation failure propagates as `MemoryError`. Nonfinite transform results or handled numerical transform failures reject the whole call; do not return partial arrays or fall back to another physical model. Unrelated programming exceptions propagate. Scoped arithmetic must preserve the caller's NumPy floating-error policy and must not emit arithmetic `RuntimeWarning` for handled cases.

## Return record, ownership and provenance

`Otf2D` binds these attributes without rebinding:

| Attribute | Meaning / representation |
|---|---|
| `values` | `(Ny,Nx)` native complex128, C-contiguous, independently owned mutable array |
| `fy_per_um` | `(Ny,)` native float64, C-contiguous, independently owned mutable array |
| `fx_per_um` | `(Nx,)` native float64, C-contiguous, independently owned mutable array |
| `pixel_size_um` | Converted `(dy,dx)` Python-float tuple |
| `origin_yx` | Validated `(oy,ox)` Python-int tuple |
| `source` | Supplied caller string, unchanged |

Inputs stay unchanged on success or rejection. All three returned arrays own separate storage and alias neither each other nor any input. Frozen record bindings do not freeze array contents. Direct construction of the record does not validate its values; consumers must not treat arbitrary construction as proof of this preparation contract.

The source label identifies the caller's provenance record. That external record should contain source-array identity, instrument/model parameters, preprocessing, units, origin choice and resolved software versions. Preparation performs no file access, authentication, hashing, metadata inference or persistence. The reproducible intake example supplies its own manifest; a later measured-calibration/file-adapter contract must define its richer provenance obligations.

## Errors and compatibility

Use the existing `SimreconError` (`ValueError`) with string `code` and `message`. Exact prose and precedence among simultaneous violations are unspecified.

| Rejected obligation | Error code |
|---|---|
| Plain PSF ndarray | `invalid_psf` |
| Real integer/floating PSF dtype | `invalid_psf_dtype` |
| Two positive spatial dimensions | `invalid_psf_shape` |
| Finite source and converted samples | `nonfinite_psf` |
| Nonnegative source samples | `negative_psf` |
| Positive converted mass | `zero_psf_mass` |
| Pair of finite positive converted pixel sizes | `invalid_otf_pixel_size` |
| Pair of in-range integer origin coordinates | `invalid_otf_origin` |
| Nonblank source string | `invalid_otf_source` |
| Representable, ordered final frequency vectors | `unrepresentable_otf_frequencies` |
| Handled numerical failure/nonfinite transfer result | `otf_transform_failure` |

Existing MRC conversion and `separate_phases` interfaces remain unchanged. No CLI command, runtime Pyotf dependency, coherent-field PSF conversion, background correction, bead fitting, optical simulation API, order-specific 3D calibration, regularization, apodization or reconstruction is included. The optical example uses Pyotf outside the product environment as the owner directed.

## Independent reference fixtures

The [fixture notes](../references/scientific/otf-calibration-fixture-notes.md) and [JSON examples](../references/scientific/otf-calibration-fixtures-v1.json) contain six small mathematical cases. Delta and constant kernels use root-sum identities; a separable `(3,4)` kernel has exact real output in `{0,1/4,1}`; a signed asymmetric `(4,6)` case gives phase and axis checks. Translating both the kernel and declared origin must preserve its transfer.

For the asymmetric case, masses `3,1,4` lie at `(oy, ox)`, `(oy+1, ox)` and `(oy, ox+1)`, respectively. Increasing row index is positive y; their sum is 8:

```text
H(ky,kx) = 3/8 + exp(-2*pi*i*ky/4)/8 + exp(-2*pi*i*kx/6)/2
H(0,0) = 1
H(0,1) = 3/4 - i*sqrt(3)/4
H(1,0) = 7/8 - i/8
H(1,1) = 5/8 - i*(1/8 + sqrt(3)/4)
H(-2,-3) = -1/4
```

An independently specified [Pyotf example](../references/scientific/otf-calibration-pyotf-notes.md) supplies an optical preview with exact source/environment/parameter identities. It is not an instrument measurement, continuous-optics convergence result or independent mathematical correctness oracle. Its DFT is only an intake illustration. The [preview](../figures/otf-calibration-intake-preview.png) contains no SIMrecon outputs.

Fresh blind A derives executable public-entry expectations from this contract and independently checks the examples; fresh blind B reviews their meaning, legitimate positive inputs and tolerances before C. Intake examples are not an A-authored/B-reviewed checkpoint and supply no product-red evidence. A later candidate's human report must compare actual public-entry outputs with accepted independent expectations on shared real/imaginary scales, with errors, signs, units and exact provenance; D assesses that correspondence.

## Behavioral scenario inventory

Each row is a distinct meaning/boundary; listed values are coverage examples. Test mapping belongs to future A and independent B, not this intake.

| ID | Observable obligation | Independent expectation / paired examples |
|---|---|---|
| K01 | Recover the complete signed complex normalized DFT for a permitted kernel. | Asymmetric formula and separable exact root identities; no magnitude-only oracle. |
| K02 | Explicit origin determines phase, including off-center/even-grid origins. | Delta away from declared origin yields the negative-exponential phase; translating both origin and samples preserves H. |
| K03 | Return matching physical frequency vectors and centered full-spectrum order. | Integer signed-bin formula; odd/even nonsquare, anisotropic sampling, singleton axes. |
| K04 | Normalize unit discrete mass, removing input gain without peak normalization or pixel-area density scaling. | Delta gives all ones; constant gives only DC one; exact positive common gains. |
| K05 | Preserve supplied sampling/grid without interpolation, support clipping or radial averaging. | Asymmetric negative real / complex bins and tiny positive tails retained within declared absolute accuracy. |
| K06 | Convert all permitted real integer/floating widths/byte orders once to float64 and compute for those stored values. | int64/uint64 rounding, float16/32, available wider floats; independently converted-value reference. |
| K07 | Return specified dtypes, shapes, order and immutable record bindings. | Public attributes; C-contiguous complex128/float64; direct construction is not validation. |
| K08 | Leave inputs unchanged and allocate three independent output arrays. | Read-only/strided input, caller mutation of each output; no input/mutual aliasing. |
| K09 | Reject nonarray/subclass PSFs. | List/scalar/subclass versus ordinary ndarray. |
| K10 | Reject nonreal/bool PSF dtypes. | Complex, bool, object versus every permitted real dtype kind. |
| K11 | Reject wrong-rank/empty spatial PSFs. | 1D/3D/empty versus `(1,1)` and nonsquare valid planes. |
| K12 | Reject nonfinite source samples. | NaN/either infinity versus finite extrema. |
| K13 | Reject conversion overflow/nonfinite converted PSF samples. | Available wider-float overflow versus representable wider samples; do not invent that capability on platforms without it. |
| K14 | Reject negative source samples before conversion. | Negative integer/float/wider underflow-to-zero versus signed zero and nonnegative samples. |
| K15 | Reject zero converted mass. | All-zero and all-underflow-to-zero versus positive subnormal mass. |
| K16 | Reject malformed/nonreal/bool pixel-size pairs. | Bad container/length/rank/scalar types versus permitted tuple/list/plain ndarray pairs. |
| K17 | Reject nonfinite/nonpositive converted pixel sizes. | NaN, infinity, zero, negative, conversion overflow/underflow-to-zero versus finite positives. |
| K18 | Reject malformed/noninteger/bool origins. | Fractional/bool/wrong pair versus Python/NumPy integers. |
| K19 | Reject out-of-bounds origin coordinates. | Negative/end index versus every in-bounds index; no wrapping. |
| K20 | Reject nonstring/blank source labels and retain permitted labels unchanged. | Empty/whitespace versus labels with surrounding whitespace and content. |
| K21 | Handle positive PSF range extremes without raw-sum overflow or losing normalization of all-subnormal mass. | `[max,max]` gives DC one/Nyquist zero; `[q,3q]` gives DC one/Nyquist -1/2. |
| K22 | Meet absolute transfer accuracy through cancellation and disparate input magnitudes. | `[max,q]` and `[1,q,0,0]`; no invented relative/subnormal-retention promise. |
| K23 | Handle representable extreme frequency grids without avoidable intermediate overflow. | Huge spacing with finite nonzero bins; singleton accepts both `q` and `max`. |
| K24 | Reject nonfinite/collapsed/unordered final frequency grids. | Extremely tiny spacing on nonsingleton axes versus representable grids; valid spacing alone supplies no guarantee. |
| K25 | Reject handled numerical transform failure without partial output. | Public controlled transform failure/nonfinite output; unrelated exceptions/MemoryError propagate. |
| K26 | Preserve caller arithmetic policy and suppress handled arithmetic RuntimeWarnings. | All supported NumPy error modes across valid extremes/rejections. |
| K27 | Keep ordinary argument binding behavior. | Missing/positional/extra keyword TypeError versus valid explicit call. |
| K28 | Preserve existing conversion/separation behavior and avoid file/simulator side effects. | Full existing suite and public imports; no product dependency/CLI changes. |
| K29 | Document limitations and compare the future actual candidate against independent expectations. | Shared signed scales/error maps, exact source/candidate identities; intake preview cannot substitute for numerical acceptance. |
