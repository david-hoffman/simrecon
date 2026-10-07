# Reconstruct at known parameters

`reconstruct` composes known-phase separation and a full complex optical transfer
function (OTF) into a first-harmonic two-dimensional estimator. This is a stacked
implementation candidate above the verified, unmerged calibration prerequisite.
Candidate acceptance and owner integration remain pending. The
[approved contract](../contracts/known-parameter-reconstruction-v1.md) defines the
operation; the historical three-object placeholder signature is superseded.

```python
import numpy as np
from simrecon import prepare_otf, reconstruct

phases = np.array([[-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81]])
calibration = prepare_otf(
    np.ones((1, 1)), pixel_size_um=(0.5, 0.25),
    origin_yx=(0, 0), source="unit sampled kernel",
)
images = (-2 * (1 + 0.5 * np.cos(phases)))[:, :, None, None]
result = reconstruct(
    images, otf=calibration, phases_rad=phases,
    wavevectors_per_um=np.zeros((1, 2)),
    modulation=np.array([0.5]), brightness=np.array([1.0]),
    regularization=0.0, apodization=np.ones((2, 2)),
)
# result.image is approximately -2 everywhere, including its signed intensity.
# result.spectrum[1, 1] is approximately -2; other modes are exactly unsupported.
# Output spacing is (0.25, 0.125) µm; the field remains (0.5, 0.25) µm.
```

Only `images` is positional. Every keyword is required. Images have shape
`(R, N, Ny, Nx)`, with `R >= 1`, `N >= 3` and positive spatial dimensions.
The six acquisition arrays must be plain NumPy arrays with real integer or
floating dtypes. Either byte order, all real widths, strided and read-only storage
work. Source and converted float64 entries must be finite. Conversion rounding
and underflow define the stored problem; arrays remain unchanged.

| Input | Shape / units / range |
|---|---|
| `images` | `(R,N,Ny,Nx)`, signed arbitrary intensity units |
| `phases_rad` | `(R,N)`, radians, finite signed angles without principal-interval restriction |
| `wavevectors_per_um` | `(R,2)`, signed `(ky,kx)` in cycles/µm |
| `modulation` | `(R,)`, converted `0 < m <= 1` |
| `brightness` | `(R,)`, converted `a > 0`, absolute acquisition gain |
| `regularization` | Nonboolean Python/NumPy real scalar, converted finite `lambda >= 0` |
| `apodization` | `(2*Ny,2*Nx)`, source and converted amplitude mask in `[0,1]` |

Supply one `Otf2D` for all orientations, on the matching detector grid. Direct
construction is validated at consumption: complex128-width transfer, float64-width
frequency vectors, compatible ordered physical axes, positive spacing, in-bounds
integer kernel origin, and nonblank source. Width checks permit either endian and
strided/read-only storage. Transfer checks require DC near one, bounded magnitude
and modular Hermitian symmetry within the contract's tolerances. These checks do
not prove a nonnegative physical point spread function (PSF) or authenticate the
caller label. Use the full signed complex transfer, including its encoded origin;
do not replace it with magnitude or shift its origin again.

Spatial coordinates are `(y*dy, x*dx)` from index `(0,0)`. Increasing rows and
columns mean positive y and x. Per orientation, public
[`separate_phases`](phase-separation.md) fits
`I[p] = dc + 2*Re(c1*exp(i*phase[p]))`. Its rank decisions, direct-angle evaluation,
off-model projection and errors propagate. For `N > 3`, projection residual is
distinct from numerical reconstruction error. No phase, wave, contrast or gain
estimation occurs.

Detector transforms use the negative Fourier sign and divide by `Ny*Nx` to obtain
Fourier-series amplitudes. The three bands are transforms of `dc`, `c1` and
`conjugate(c1)`. At each output signed mode `q`, query DC at `q`, plus at
`q + (ky*Ny*dy, kx*Nx*dx)` and minus at `q - shift`. Data and transfer use identical
complex bilinear weights. Both signed detector endpoints are included. Outside
either closed axis interval returns exact zero, without wrapping, extrapolation
or a partial edge stencil. A singleton detector axis admits only coordinate zero.
Computed float64 coordinates determine boundaries without a snapping tolerance.

With `t0=a*H`, `tplus=tminus=(a*m/2)*H` at their respective query positions:

```text
U = sum(conjugate(t)*d)       V = sum(abs(t)**2)
E = U/(V+lambda) when V+lambda > 0, otherwise exactly zero
T = apodization*E
image = sum_q T[q]*exp(2*pi*i*q dot output_index/output_shape)
```

These are equal weights in separated-band coordinates, a diagonal least-squares
heuristic. The ridge penalty has squared effective-transfer units. The supplied
mask multiplies amplitude. There is no automatic noise inference, denominator
floor, transfer threshold or hidden radial window. Synthesis adds no division by
output size: a recoverable constant retains its amplitude with zero ridge and a
unit mask.

`Reconstruction2D` has frozen bindings and four independently owned, mutable,
C-contiguous arrays. `image` and centered `spectrum` are native complex128 with
shape `(2*Ny,2*Nx)`; `fy_per_um` and `fx_per_um` are native float64 vectors.
`pixel_size_um` is a Python-float pair `(dy/2,dx/2)`; `source` retains the calibration
label verbatim. None of the four arrays aliases an input or another result array.
Signed real intensity and imaginary residue are retained. Asymmetric masks or
coverage can produce complex images; the operation does not force real values,
symmetrize, take magnitude, clip negatives or renormalize.

Doubled sampling preserves the field `Ny*dy` by `Nx*dx`. It is additional synthesis
sampling, not a general measured-optics resolution claim. Exact physical recovery
requires commensurate illumination and alias-free recoverable object modes in the
finite periodic circular-convolution model. Fractional shifts deliberately use a
bilinear approximation to sampled spectra and do not exactly invert
noncommensurate illumination. Noise, aliasing and model mismatch can change the
physical interpretation. The [actual comparison](../reports/reconstruction-comparison.md)
separates rounded-data solver error from this physical model bias.

Binary scaling protects transforms, reductions, squared gains and synthesis from
avoidable overflow when final coordinates are representable. Underflow is allowed.
Zero inputs, zero masks and unsupported denominators give exact zeros. Final
nonfinite spectrum/image coordinates reject the whole call with
`unrepresentable_reconstruction`; grid failure uses
`unrepresentable_reconstruction_grid`. Numerical transform `ValueError`,
`FloatingPointError`, `OverflowError` and nonfinite transform results use
`reconstruction_solver_failure`. `MemoryError` and unrelated errors propagate.
Scoped arithmetic preserves the caller's NumPy error modes and callback and emits
no handled arithmetic RuntimeWarning. Binding errors retain ordinary `TypeError`;
all domain codes are listed in the contract on `SimreconError`.

The informative coordinate budget is
`8192*R*N*(4*Ny*Nx)*2^-52*B + 8*(4*Ny*Nx)*2^-1074`, where
`B=max(abs(converted_images))/min(brightness)`. It applies separately to real and
imaginary coordinates when phase condition numbers are at most 10, brightness is
in `[0.1,10]`, and positive denominators are at least
`1e-6*max(1,max(V),lambda)`. The complex-modulus conservative bound is `sqrt(2)`
times this budget. This is a project acceptance envelope, not a backend theorem or
a guarantee outside that regime. Weak transfer and ill-conditioning can amplify
error; bitwise agreement across platforms is not promised.

The numerical call performs no file access. Conversion and the command-line
interface remain separate; reconstruction adds no adapter, three-dimensional
operation or dependency.
