# Known-carrier illumination estimation

**Version 1.0. October 7, 2026.** The owner's request to implement the next roadmap item stacked on PR #9 authorizes this first parameter-estimation slice. Scope selection uses report-only Astra/ultra scientific advice. This contract defines the concrete operation; advisor agreement is not A/B/D acceptance.

## Public boundary

```python
from simrecon import IlluminationEstimate, estimate_illumination

estimate = estimate_illumination(
    images, otf=calibration, phase_steps_rad=steps,
    carrier_bins_yx=(ky_bins, kx_bins),
)
```

Only images is positional; every keyword is required. Ordinary binding `TypeError` remains. One orientation has images `(N, Ny, Nx)`, `N >= 3`, and known relative steps `(N,)`. Their real array, dtype, conversion, finite, shape, rank, solver and error semantics are exactly those of [separate_phases v2](known-phase-separation-v2.md), with phase_steps_rad supplied as its phases_rad. Signed images, all real integer/floating widths and byte orders, strided/read-only arrays and any finite converted angles remain permitted. Separate at the supplied steps directly, without reducing large steps modulo rounded `2*pi`.

The known carrier is a tuple, list or plain one-dimensional length-two ndarray of nonboolean Python/NumPy integers. Coordinates are signed integer detector frequency-bin shifts, ordered y/x. Zero and negative shifts are permitted. Arbitrarily large integers are valid representations; a shift with no closed-grid overlap has the distinct no-overlap failure below. No rounding of fractional carriers, periodic wrapping, fractional interpolation or search is included.

The shared Otf2D is on exactly the detector `(Ny,Nx)` grid. Validate direct constructions as well as prepared records: values is a plain complex128-width ndarray, fy/fx are plain float64-width vectors, shapes and source/converted coordinates are finite; either endian and strided/read-only storage are valid. Pixel sizes, origin and nonblank source follow [reconstruction's supplied-record rules](known-parameter-reconstruction-v1.md#supplied-record-validation-and-placement). Require the same centered physical frequency-axis accuracy/ordering, DC normalization, magnitude and modular Hermitian tolerances. These checks do not authenticate provenance or establish physical optical support. Copy inputs before numerical processing.

This is a pure array operation. Keep all existing interfaces, commands, dependencies and conversion/calibration/reconstruction behavior. Carrier estimation, independent phase-step estimation, brightness estimation, drift, 3D, file adapters and automatic reconstruction remain subsequent slices.

## Model and estimator

The finite periodic first-harmonic model uses the existing negative-sign forward discrete Fourier transform (DFT), centered signed integer bins, index-zero spatial origin and full signed complex optical transfer function (OTF):

```text
I_p = h circular-convolved with a*s*[1+m*cos(2*pi*k dot r+psi_p+theta)]
dc,c1 = unweighted first-harmonic separation at supplied relative steps psi
D0 = F(dc)/(Ny*Nx); Dplus = F(c1)/(Ny*Nx)
Q = {q: q and q+k are both inside the closed signed detector grid}
x(q) = H(q+k)*D0(q)
y(q) = H(q)*Dplus(q+k)
z = sum_Q conjugate(x)*y / sum_Q abs(x)**2
modulation = 2*abs(z)
phase_offset_rad = atan2(z.imag,z.real)
relative_residual = sqrt(sum_Q abs(y-z*x)**2 / sum_Q abs(y)**2)
```

No wrapping, inferred support mask, weak-transfer threshold, OTF division, absolute-value OTF replacement or zero-bin removal. overlap_count is the number of geometric q pairs, including zero-transfer pairs. A singleton axis permits only shift zero along that axis. A nonempty Q is necessary. Nonzero x energy, y energy and fitted cross product are also necessary to identify a nonzero complex gain and its phase. Reject computed zero information; do not impose an undocumented positive cutoff. Extremely weak overlap is accepted when representable and informative, but can amplify noise arbitrarily.

For commensurate, alias-free object modes, y=(m/2)*exp(+i*theta)*x. Thus z cancels the unknown specimen and absolute brightness; neither can be inferred by this fit. The conjugation, positive phase sign and factor of two are normative. This is an unweighted complex least-squares fit, with no noise likelihood or confidence interpretation. Arbitrary/off-model data receives the stated estimator. A residual is a fit diagnostic, never a reliability probability. No unique illumination-recovery guarantee applies to arbitrary specimens, aliased data, model mismatch or noise.

Return the unconstrained fitted modulation, including values above one. Do not clip or silently reject such a fit: it may diagnose model mismatch and the existing reconstruction operation separately enforces its physical modulation domain. A zero fitted gain has no defined phase and is rejected. No sign choice, orientation search or correction for known-step errors is inferred.

## Corrected phases and result

Return frozen-binding IlluminationEstimate with Python floats phase_offset_rad, modulation and relative_residual; independently owned mutable native float64 C-contiguous phases_rad of shape `(N,)`; Python int overlap_count; source retaining the OTF label unchanged. No field rebinding; no direct-construction validation requirement. No output aliases any caller input. Preserve all caller arrays on success and rejection.

Corrected phases are principal-equivalent rotations of the SAME represented float64 sine/cosine entries used for separation. Let c=cos(psi), s=sin(psi), ct=cos(theta), st=sin(theta):

```text
phases_rad = atan2(s*ct+c*st, c*ct-s*st)
```

Angles are in radians, within `[-pi,pi]`; equivalent signs at the branch cut are permitted. Do not return `psi+theta`: adding a small offset to an enormous finite psi can erase it. Do not reduce psi modulo a rounded `2*pi` before trigonometry. The principal-equivalent result feeds the existing reconstruct phases_rad per orientation, subject to its own validation and the estimated modulation being in `(0,1]`. Carrier and brightness remain explicit caller inputs.

## Arithmetic, errors and accuracy

Use float64/complex128 processing. Avoid raw transform, squared-norm, cross-product and restoring-scale overflow/underflow when final gain, modulation and residual are safely representable. A common positive scaling of images with unchanged stored ratios preserves the estimator. Preserve caller NumPy error mode and do not leak arithmetic RuntimeWarning for handled cases. Allocation MemoryError and unrelated exceptions propagate.

No uniform digit guarantee is selected for near-deficient phase separation, weak overlap or cancelling cross products. In the informative regime: represented phase matrix condition <=10; both `norm(x)` and `norm(y) >= B/8`, where B is the maximum absolute converted image value; normalized cross-correlation magnitude >=1/4; `1e-4 <= abs(z) <= 10`; and finite final outputs. Require reconstructed fitted gain `0.5*modulation*exp(i*phase_offset_rad)` absolute error <=delta*max(1,abs(z)) and residual absolute error <=delta, where `delta = 8192*N*(Ny*Nx)*2^-52`. This is a conservative project acceptance budget for the stored-input estimator, not a backend theorem or physical accuracy promise. B independently checks whether fixture conditioning satisfies this regime. Include tighter distinguishing analytic assertions where justified. Compare phases circularly; gain error determines phase/modulation error away from zero. Independent expected values must not call production separation/estimation helpers or use product output as truth.

An equivalent stable formulation uses `u=x/norm(x)`, `v=y/norm(y)`, `c=sum(conjugate(u)*v)`: theta=arg(c), modulation=`2*(norm(y)/norm(x))*abs(c)`, residual=`norm(v-c*u)`. Compute the residual directly; subtracting nearly equal squared correlations can destroy its small-error accuracy. The final modulation, rather than an unnecessarily materialized complex gain or intermediate norm ratio, defines representability. Scaling and exponent-based arithmetic may retain finite output when an intermediate ratio would overflow or underflow.

The information/range decision applies to computed float64 quantities, not exact-real classification at subnormal/maximum boundaries. Computed zero x/y energy or cross product yields unidentifiable_illumination; underflow elsewhere is permitted within the accuracy policy. Computed nonfinite final gain/modulation/residual/phases yields unrepresentable_illumination. No partial, clipped or fallback result. Numerical transform ValueError, FloatingPointError or OverflowError, or nonfinite transform factors, yields illumination_solver_failure; translate only numerical execution, not unrelated validation/programming exceptions. Existing separation errors propagate unchanged.

Use SimreconError code/message; prose and simultaneous-error precedence are unspecified:

| Rejected obligation | Stable code |
|---|---|
| Images/steps or separation rank/solver/range | Existing separate_phases v2 codes |
| Carrier representation | invalid_illumination_carrier |
| OTF record/type/array representation/metadata/transfer invariants | invalid_illumination_otf |
| OTF physical frequency grid mismatch or ordering | incompatible_illumination_otf_grid |
| Empty geometric Q | no_illumination_overlap |
| Computed zero x/y energy or fitted cross product | unidentifiable_illumination |
| Nonfinite computed final outputs | unrepresentable_illumination |
| Handled numerical transform failure/nonfinite factors | illumination_solver_failure |

## Behavioral inventory and evidence

Every listed stable rejection code is a distinct subscenario. Each positive guarantee is likewise mapped separately; group IDs are headings, not a cap. Equivalent values are examples, not new meaning.

| ID | Observable obligation / relevant risk |
|---|---|
| E01 | Public exports, record and required keyword-only binding |
| E02 | Existing images/steps representation, conversion, finite, shape and numerical-rank semantics/codes |
| E03 | Signed/zero integer carrier pairs; fractional/bool/subclass/malformed rejection |
| E04 | Direct OTF record validation and matching grid; complete signed complex transfer |
| E05 | Geometric closed overlap, signed endpoints/even Nyquist, no wrap, singleton and empty overlap |
| E06 | Independent model-consistent phase sign, factor two, specimen/brightness cancellation |
| E07 | Complex weighted least-squares oracle for off-model data and residual distinction |
| E08 | Informative/zero energy and cancelling cross product, no hidden threshold |
| E09 | Unconstrained modulation above one, no clipping or confidence claim |
| E10 | Large-step principal-equivalent corrected phases and circular branch-cut equivalence |
| E11 | Common image gain, tiny/large safe scales, finite final range and underflow policy |
| E12 | Inherited phase failures; transform failure/nonfinite, MemoryError/unrelated exceptions, warnings/error mode |
| E13 | Frozen bindings, independent mutable result storage, preserved inputs on success/failure |
| E14 | Joint phase/observation permutation and unequal N>3 steps |
| E15 | Existing reconstruct integration with estimated phase/modulation and explicit carrier/brightness |
| E16 | Honest usage, actual independent comparison and preserved existing APIs/dependencies |

Blind A authors public-entry tests, independent finite-sum acquisition/DFT/complex-fit expectations and requirement/risk mapping. Fresh blind B independently derives signs, legitimate positive classes, overlap and numerical observers before C. C writes usage and a compact actual-versus-independent numeric comparison report with fixture identity, carrier, steps, OTF source, fitted parameters/residual and reconstruction correspondence. No new plotting dependency is required. D checks correspondence against the exact passing candidate. Ignored evidence holds final identities and detailed role/check accounting.

Inherited [project coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance): approved behavior coverage and independent risk review; native statement/branch percentages are advisory. Full measurement/report integrity and the exact clean canonical local gate remain required; no coverage-policy migration of prior tasks. Primary sources opened October 7, 2026: [NumPy DFT sign/order/normalization](https://numpy.org/doc/stable/reference/routines.fft.html), and [Gustafsson et al., parameter fitting, pages 4963–4964](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). The paper describes OTF cross-weighting and complex regression on overlapping bands; it does not establish noise-optimality. The exact discrete estimator/domain/budget here are explicit project choices derived above.
