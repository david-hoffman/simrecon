# Known-parameter first-harmonic 2D reconstruction

**Version 1.0.** October 6, 2026. Intake for the owner's authorized next roadmap milestone. Trusted original request: source chat 01a111ea-e45f-7170-a22e-b9b1f77acb0f, user message 01a11397-a2de-7783-806d-aa78fee1eb2d: “open up a new task that's branched off PR number seven and have it do the next thing on the roadmap. Give it an auto approval so that it just kind of continues and tries to go for full implementation.” The owner also requested stacked GitHub PRs, or a PR pointing at #7. This is scientific task intake, not a delivery-policy amendment or product acceptance. Required independent A/B/D review remains ahead.

## Public acquisition boundary

```python
from simrecon import Reconstruction2D, reconstruct
result = reconstruct(images, otf=calibration, phases_rad=phases,
    wavevectors_per_um=wavevectors, modulation=modulation,
    brightness=brightness, regularization=regularization,
    apodization=apodization)
```

Only images is positional; all keywords required. Binding TypeError remains. Historical unimplemented three-object placeholder supplies no numerical signature and is superseded, without alias. Pure numerical processing; no file access, estimation/drift, 3D, adapter, CLI reconstruction, new dependencies or legacy copying. Preserve conversion/separation/calibration behavior.

images: plain NumPy ndarray `(R,N,Ny,Nx)`, R>=1,N>=3,Ny,Nx>=1. phases `(R,N)`, waves `(R,2)`, modulation/brightness `(R,)`, apodization `(2*Ny,2*Nx)` are also plain ndarrays. All accept dtype kinds i/u/f, all widths/byte orders, strided/readonly storage; reject subclasses/lists/bool/complex/other kinds. Source and converted float64 entries must be finite; rounding/underflow defines stored problem. Signed images/phases/waves permitted. Converted brightness a>0; converted modulation 0<m<=1. Apodization source and converted values in [0,1]. regularization lambda is nonboolean Python/NumPy real scalar converted finite float64 >=0. Finite known phases are radians, passed directly per orientation to existing separate_phases; its rank/projection/accuracy semantics and errors propagate. N>3 off-model data projects into the first harmonic; residual is not solver error. No implicit phases, angular-span cutoff, orientation/modulation/brightness estimate or principal-interval restriction.

## Forward model and Fourier conventions

Let r=(y*dy,x*dx) with spatial origin index (0,0), wave k=(ky,kx) in cycles/µm, increasing rows/columns positive y/x. The selected finite periodic model is

```text
L_rp = a_r*[1+m_r*cos(2*pi*k_r dot r + phi_rp)]
I_rp = h circular-convolved with (s*L_rp)
I_rp = dc_r + 2*Re(c1_r*exp(i*phi_rp))
F(u)[j,l] = sum_yx u[y,x]*exp(-2*pi*i*(j*y/Ny+l*x/Nx))
D0=F(dc)/(Ny*Nx); Dplus=F(c1)/(Ny*Nx)
Dminus=F(conjugate(c1))/(Ny*Nx)
D0(f)=a*H(f)*S(f)
Dplus(f)=(a*m/2)*H(f)*S(f-k)
Dminus(f)=(a*m/2)*H(f)*S(f+k)
```

The last three equalities describe commensurate, alias-free object modes. k sign means sample Dplus at q+k and Dminus at q-k to estimate object q. H is the complete signed complex unit-mass OTF; its explicit kernel origin is already encoded, never reapplied. H supplies no absolute brightness or physical support mask. No magnitude/squared-magnitude substitution. Arrays use centered signed integer modes [-floor(N/2),...,ceil(N/2)-1]. FFT forward sign is negative. No geometric-center transform origin.

Finite detector acquisition is periodic circular convolution, not infinite-field optics. Exact physical recovery needs commensurate illumination and alias-free recoverable modes. General accepted data receives the defined estimator, not a claim of exact recovery from aliasing/noise/model mismatch.

## Supplied record validation and placement

One Otf2D shared by all orientations, with plain ndarray complex128-width values `(Ny,Nx)` and float64-width fy `(Ny,)`, fx `(Nx,)`, all finite; either endian, strided/readonly permitted. Validate Otf2D type and each field even when directly constructed. pixel_size_um pair accepts tuple/list/plain 1D length-two ndarray of nonboolean real scalars converting finite positive dy,dx. origin_yx pair accepts nonboolean integers inside detector shape. source is nonblank str retained unchanged. Copy before processing. These necessary representation checks certify neither a physical PSF nor authenticated provenance.

Set eps=2^-52, qsmall=2^-1074, tau=128*Ny*Nx*eps+4*Ny*Nx*qsmall. Require H_DC within tau of 1, magnitude <=1+tau, modular Hermitian difference <=2*tau. Frequency j/(Ny*dy),l/(Nx*dx) must match within 8*eps*abs(exact)+qsmall; axes finite, strictly increasing and nonzero for nonzero modes. Do not infer cutoff/threshold, discard zeros/small transfer or resample incompatible calibration.

Output `(2*Ny,2*Nx)` at `(dy/2,dx/2)`, same field of view Ny*dy by Nx*dx and index-zero origin. Output signed modes extend the detector modes with unchanged physical frequency increments. Halved spacing, output frequencies and shifts/interpolation coordinates must be finite, positive where required, ordered and noncollapsed; no alternate grid. Detector BIN shifts are (ky*Ny*dy,kx*Nx*dx). At output integer q=(j,l), query DC at q, plus at q+shift, minus at q-shift. Exact integer coordinates select stored bins; otherwise separable bilinear interpolation of complex band data and H using identical weights. Both signed detector endpoints are included. Outside either closed axis interval returns exactly zero for data and transfer, with no wrap, extrapolation or partial edge stencil. A singleton axis permits only coordinate zero. Computed float64 coordinates select boundaries without hidden snapping tolerance.

Integer shifts relocate exactly. Fractional shifts are a deliberate bilinear approximation to sampled spectra and do not exactly invert noncommensurate circular illumination. This limitation must be visible in usage and evidence. No calibration-grid resampling, acquisition padding/cropping or separate resampling API. Extended output is additional synthesis modes, not additional measured samples or a larger field.

## Estimator and output

For each q,orientation and band:

```text
d0=interp(D0,q); t0=a*interp(H,q)
dplus=interp(Dplus,q+k); tplus=(a*m/2)*interp(H,q+k)
dminus=interp(Dminus,q-k); tminus=(a*m/2)*interp(H,q-k)
U=sum(conjugate(t)*d); V=sum(abs(t)**2)
E=U/(V+lambda) if V+lambda>0 else 0
T=A*E
image[y,x]=sum_q T(q)*exp(2*pi*i*(q_y*y/(2*Ny)+q_x*x/(2*Nx)))
```

No extra 1/(4*Ny*Nx) after synthesis: T holds Fourier-series amplitudes. This is inverse transform with forward normalization. A recoverable constant keeps amplitude with lambda=0,unit mask. lambda is caller-specified ridge penalty in squared effective-transfer units. Equal weighting is in separated-band coordinates; this diagonal least-squares heuristic is not a Poisson likelihood or assertion of independent conjugate bands. No automatic noise estimate, Wiener parameter, denominator floor or support threshold. lambda=0/all t=0 gives exact zero for the mode. Explicit A in [0,1] is an amplitude mask; zero suppresses a mode. No hidden radial window.

Return frozen-binding Reconstruction2D(image,spectrum,fy_per_um,fx_per_um,pixel_size_um,source). image and spectrum are native complex128 output-shape arrays; spectrum=T centered. fy/fx are native float64 output vectors. pixel_size_um is converted Python-float tuple; source retained. All four arrays independently own mutable C-contiguous storage, alias neither inputs nor each other. Preserve signed real values and imaginary residues; do not force real, symmetrize, take magnitude, clip negatives or renormalize. A physical real result needs consistent symmetric coverage/data/mask. The comparison plots signed real intensity and reports imaginary residue. Caller arrays unchanged on success/rejection.

## Range, errors and accuracy

Exact estimator truth is equations above on converted inputs and represented NumPy sin/cos entries. Independent A/B expectations must not reuse production helpers/product solver or legacy output. Float64/complex128 arithmetic, no bitwise cross-platform promise. For phase matrix condition<=10, positive denominators >=1e-6*max(1,max V,lambda), and brightness in [0.1,10], require image and spectrum coordinate absolute error <=8192*R*N*(4*Ny*Nx)*eps*B + 8*(4*Ny*Nx)*qsmall, B=max(abs(converted images))/min(brightness). Calculate budget in adequate precision, include tight distinguishing analytic assertions and challenge independently. This conservative project acceptance budget is not a backend theorem. Zero inputs give zero outputs. Else no uniform digit guarantee: conditioning/weak transfer/interpolation/ridge matter.

Avoid avoidable raw transform/reduction/squared-gain overflow for safely representable results, using scaling as needed. Final computed nonfinite output coordinates yield unrepresentable_reconstruction for whole call, no clipping/partial/fallback. This computed-range rule is not exact-real classification at float64 maximum. Underflow permitted. Numerical transform ValueError/FloatingPointError/OverflowError or nonfinite transform results yield reconstruction_solver_failure; translation applies only to numerical execution. Allocation MemoryError and unrelated exceptions propagate. Preserve caller NumPy error mode and suppress arithmetic RuntimeWarning for handled cases.

Domain errors use SimreconError code/message; exact prose and simultaneous-failure precedence unspecified. Every distinct error code listed below is its own rejection subscenario (parent ID plus code); each separate positive guarantee is likewise mapped separately. Group rows are inventory headings, not a scenario cap. Equivalent values remain coverage examples:

| ID | Observable obligation / error |
|---|---|
| R01 | Public exports, required keyword-only binding, no old scaffold alias; TypeError |
| R02 | Plain real acquisition and valid shape: invalid_reconstruction_images / invalid_reconstruction_dtype / invalid_reconstruction_shape |
| R03 | Source/converted images finite: nonfinite_reconstruction_images; signed/underflow permitted |
| R04 | Plain real matching phases finite: invalid_reconstruction_phases / invalid_reconstruction_phases_dtype / invalid_reconstruction_phases_shape / nonfinite_reconstruction_phases |
| R05 | Existing phase rank/projection/angle/failure semantics and codes |
| R06 | Plain real finite waves shape/units/zero/signed: invalid_reconstruction_wavevectors / invalid_reconstruction_wavevectors_dtype / invalid_reconstruction_wavevectors_shape / nonfinite_reconstruction_wavevectors |
| R07 | Plain real modulation 0<m<=1: invalid_reconstruction_modulation / invalid_reconstruction_modulation_dtype / invalid_reconstruction_modulation_shape / nonfinite_reconstruction_modulation / invalid_reconstruction_modulation_range |
| R08 | Plain real brightness a>0: invalid_reconstruction_brightness / invalid_reconstruction_brightness_dtype / invalid_reconstruction_brightness_shape / nonfinite_reconstruction_brightness / invalid_reconstruction_brightness_range |
| R09 | Scalar finite lambda>=0: invalid_reconstruction_regularization |
| R10 | Plain real finite output mask/source and converted [0,1]: invalid_reconstruction_apodization / invalid_reconstruction_apodization_dtype / invalid_reconstruction_apodization_shape / nonfinite_reconstruction_apodization / invalid_reconstruction_apodization_range |
| R11 | Otf2D type and all arrays/shape/dtype/finite: invalid_reconstruction_otf |
| R12 | OTF spacing/origin/source metadata: invalid_reconstruction_otf |
| R13 | Matching physical frequency grid and ordering: incompatible_reconstruction_otf_grid |
| R14 | Signed complex normalized/Hermitian bounded transfer: invalid_reconstruction_otf |
| R15 | Independent synthetic forward-to-output recovery beyond DC support, signs/gains |
| R16 | Fourier normalization and spatial/PSF origins, odd/even/nonsquare |
| R17 | Integer relocation and exact boundaries; no wrap |
| R18 | Fractional bilinear interpolation estimator and approximation limits |
| R19 | Out-of-grid and singleton rules |
| R20 | Joint phase/orientation reorderings and multiple orientations |
| R21 | Ridge, zero denominator, no support inference |
| R22 | Explicit mask suppression/asymmetry and signed complex result |
| R23 | Doubled sampling/same field/brightness |
| R24 | Output grid/spacing/shifts representable: unrepresentable_reconstruction_grid |
| R25 | Independent mutable result storage; input preservation success/rejection |
| R26 | Informative accuracy/zero/subnormal cases |
| R27 | Safe interior and genuine output range: unrepresentable_reconstruction |
| R28 | Numerical failure/nonfinite transform: reconstruction_solver_failure |
| R29 | MemoryError/unrelated exceptions; caller error mode/warnings |
| R30 | Existing APIs/CLI/conversion intact; no I/O/legacy use |
| R31 | Human comparison and parameter/provenance/error/limitation evidence |

## Acceptance evidence and primary references

A independently authors asymmetric real analytic Fourier phantom, PSF/OTF and finite-sum forward acquisitions with multiple orientations and unequal N>3 phases, including recoverable mode beyond DC transfer support. Distinguish unrounded object truth, rounded-data estimator truth and physical regularization/interpolation bias. Separate fractional estimator fixture. B independently derives signs/scaling/interpolation/oracles/tolerances, challenges legitimate positives and complete mapping. No duplicate product implementation as sole oracle.

C provides PNG/report/JSON: shared-scale truth, conventional unilluminated observation, reconstructed signed real intensity, imaginary residue, absolute errors and representative signed phase components/input phases. Include maxima, actual phases/waves/gains/penalty/mask, independent fixture identities, source/lock/environment/commands. D inspects real pixels and correspondence. Ignored one-off generators are local evidence, not shipped runtime.

Opened primary references: [NumPy transform sign/normalization](https://numpy.org/doc/stable/reference/routines.fft.html), [SciPy complex rectilinear interpolation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RegularGridInterpolator.html). Equations/boundaries/budget are explicit project choices, not library-default authority. Reuse public known-phase-separation-v2.md and otf-calibration-v1.md; neither independently authorizes these reconstruction semantics.
