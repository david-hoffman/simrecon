# Known-phase five-order volume separation

**Version 1.0. October 7, 2026.** The owner authorized the next coherent unmet roadmap implementation stacked above verified PR #15, including contract intake, required independent roles, full verification, publication and successor creation. This slice begins the roadmap's 3D extension with known-phase separation. Report-only Astra/ultra advice informed selection and replaces no required acceptance.

## Public operation and scope

```python
from simrecon import VolumePhaseComponents, separate_volume_phases
components = separate_volume_phases(images, phases_rad=phases)
components.dc
components.c1
components.c2
```

Only images is positional; phases_rad is required keyword-only. Ordinary argument-binding TypeError remains. One orientation has images `(N,Nz,Ny,Nx)`, N>=5 and every spatial dimension positive. Phases `(N,)` are known fundamental illumination phases in radians, common across the volume for each exposure. Axis order is phase, z, y, x. No spacing metadata, spatial transform, resampling or intensity normalization is involved. Every voxel is fitted independently with the same phase matrix; output axes and intensity units remain z/y/x and those of the converted input.

This pure array operation returns phase harmonics of the observed volume. It does not recover a specimen or separately identify the seven three-beam spatial illumination components. The negative lateral orders follow by complex conjugation in this spatial representation. No axial order-specific optical transfer function (OTF), calibration, frequency relocation, reconstruction, phase estimator, drift correction, adapter or automatic composition is added. Existing 2D separate_phases and every other public interface remain unchanged. A volume with Nz=1 is valid but still requires a four-dimensional acquisition array.

## Input representation and errors

Images and phases are plain NumPy ndarrays, dtype kind i/u/f, any integer/floating width and byte order. Signed values, strided/Fortran/read-only storage and singleton spatial axes are valid. Reject lists/nonarrays, ndarray subclasses/masked arrays, bool, complex, object, strings, structured and datetime dtypes. Source and copied native float64 values must be finite. Conversion rounding and finite underflow to zero are permitted; converted snapshots define the fitted problem. No promise covers concurrent external mutation. Snapshot both arrays before trigonometric/numerical processing. Preserve all caller storage on success and rejection.

Use SimreconError with stable code; message prose and simultaneous-error precedence are unspecified:

| Rejected obligation | Stable code |
|---|---|
| Images are not a plain ndarray | invalid_volume_phase_images |
| Image dtype kind outside i/u/f | invalid_volume_phase_dtype |
| Image shape outside `(N>=5,positive_z,positive_y,positive_x)` | invalid_volume_phase_shape |
| Source or converted images nonfinite | nonfinite_volume_phase_images |
| Phases are not a plain ndarray | invalid_volume_phase_angles |
| Phase dtype kind outside i/u/f | invalid_volume_phase_angles_dtype |
| Phases shape/count outside `(N,)` | invalid_volume_phase_angles_shape |
| Source or converted phases nonfinite | nonfinite_volume_phase_angles |
| Numerical matrix rank below five | rank_deficient_volume_phases |
| Numerical SVD/least-squares LinAlgError or unusable nonfinite numerical factors | volume_phase_solver_failure |
| Computed final returned real coordinates nonfinite | unrepresentable_volume_phase_components |

Catch only expected conversion TypeError/ValueError/OverflowError as corresponding representation errors. Allocation MemoryError and unrelated exceptions propagate unchanged. No partial result, fallback, regularization, clipping or hidden intensity/phase-span threshold. Numerical failure translation is confined to the numerical execution, not unrelated programming exceptions. Preserve caller NumPy error mode and emit no arithmetic RuntimeWarning for handled conversion/range cases; do not suppress unrelated warning categories.

## Represented phase model and sign

Let phi be the converted phase vector. Compute native float64 NumPy entries with the indicated operations, without reducing phi modulo rounded 2*pi or multiplying phi by two:

```text
c = np.cos(phi); s = np.sin(phi)
c2 = (c*c) - (s*s)
s2 = (2*c)*s
H[p,:] = [1,c[p],s[p],c2[p],s2[p]]
```

Each multiplication and subtraction above rounds in float64 in the shown order. These represented entries are treated as exact real numbers by the mathematical oracle. This explicit phasor-squaring convention retains a finite basis for every finite converted angle, including values whose doubled angle overflows. It is a project choice; it need not be bitwise identical to NumPy cos(2*phi)/sin(2*phi), even where those expressions are finite. No exact-real trigonometric or bitwise cross-platform promise is selected.

At each voxel with converted observation vector b, fit the unweighted full-rank least-squares problem:

```text
(A,B1,C1,B2,C2) = argmin ||b-H*(A,B1,C1,B2,C2)||_2
dc = A
c1 = (B1-i*C1)/2
c2 = (B2-i*C2)/2
fitted_b = dc + 2*c1.real*c - 2*c1.imag*s
              + 2*c2.real*c2_basis - 2*c2.imag*s2_basis
```

Here c2_basis/s2_basis denote the fourth/fifth columns of H, rather than the returned c2 coefficient. In the ideal model this is `I(phi)=dc+2*Re(c1*exp(i*phi)+c2*exp(2*i*phi))`. For example `10+4*cos(phi)+2*sin(phi)+6*cos(2*phi)-8*sin(2*phi)` gives dc=10, c1=2-i, c2=3+4i; represented/rounded observations follow the stated stored-input fit. Coefficient sign and factor of two are normative. For unequal phases dc is generally not the arithmetic mean. N>5 off-model observations receive their least-squares projection; a nonzero fit residual is permitted and is distinct from solver error. Joint permutation of phases and observations preserves the mathematical fit, subject to accuracy and rank-boundary limits below.

## Rank, accuracy and range

Use float64/complex128 arithmetic and singular value decomposition (SVD)-based least squares, never normal equations as the product solver. For computed float64 singular values of H, set `tau=2^-52*max(N,5)*s_max`. Count values strictly greater than tau; equality is deficient. Require rank five. There is no condition-number rejection beyond this numerical rank rule. Repeated phases can be valid when enough remaining rows identify all five columns. Five nominal angles alone do not imply rank. Boundary classifications can differ with backend/platform/permutation roundoff.

For independent oracle coordinates `z=(dc,c1.real,c1.imag,c2.real,c2.imag)`, let `K=H*diag(1,2,-2,2,-2)` and z_star be the unique exact-real least-squares minimizer on the represented matrix and converted observations. In the informative regime `cond_2(H)<=10` and safely finite returned coordinates, require every returned real coordinate to obey

```text
abs(z_hat[j]-z_star[j]) <= 8192*N*2^-52*B + 8*2^-1074
B = max_p abs(b[p]) at that voxel
```

Evaluate the budget and oracle in sufficient precision/scaling; zero/underflowed float64 budgets are not evidence. This conservative absolute intensity-unit budget is a project acceptance choice, not a LAPACK theorem or physical accuracy promise. Independently justified tighter analytic checks should distinguish sign, factor and cross-order leakage. Beyond the informative regime no uniform digit guarantee is selected; full numerical rank still permits the fit and the unweighted SVD estimator remains binding. Weakly identified phase sets may amplify measurement and arithmetic errors without limit.

Avoid avoidable internal overflow in raw observations, norms, doubled coefficients and restoring scales for safely representable final coordinates. Range is defined separately for dc, c1.real, c1.imag, c2.real and c2.imag; overflowing complex magnitude or unhalved B/C is not a reason to reject. Underflow is permitted within the accuracy policy. Computed nonfinite final coordinates reject the entire call; computed boundary uncertainty near float64 maximum has no exact-real classification promise. A finite answer must satisfy the applicable accuracy requirement.

## Result and evidence

Return frozen-binding VolumePhaseComponents with exactly the public fields dc,c1,c2. dc is an independently owned mutable native float64 C-contiguous ndarray; c1/c2 are likewise native complex128. All have `(Nz,Ny,Nx)` shape. They alias neither caller storage, one another nor another call's output. No direct-construction validation is required. Negative-order arrays are not separately stored; callers may form conjugates.

| ID | Observable obligations and concrete risks |
|---|---|
| V01 | Public exports, required binding, frozen fields, native independent result storage |
| V02 | Every image type/dtype/shape/finiteness rejection and paired permitted representations |
| V03 | Every phase type/dtype/count/finiteness rejection and paired permitted representations |
| V04 | Five-column represented model, signs/factors, direct huge-angle phasor semantics |
| V05 | Unequal/overdetermined phases, genuine off-model projection and joint permutations |
| V06 | Rank-five strict cutoff, deficient sets, valid repeated rows, no angular-span or conditioning cap |
| V07 | Independent intensity-scaled accuracy, zero/subnormal/max-safe results, genuine output-range error |
| V08 | Input snapshots/preservation, warning/error-mode handling, solver/unrelated/MemoryError propagation |
| V09 | z/y/x axes, voxel independence, singleton and nonsquare volumes, no spatial mixing |
| V10 | Existing APIs/gates/dependencies preserved, executed usage and measured independent comparison |

These groups impose no scenario cap; blind A maps each distinct outcome/guarantee/rejection. A owns independent analytic volume fixtures and high-precision stored-input least-squares expectations; normal equations in sufficient independent observer precision are permitted, production solver/output is not an oracle. Fresh B independently challenges legitimate alternatives, margins, high-impact omissions and oracle validity before C. Preimplementation test limitations remain explicit and binding to D. C supplies an executed usage example and actual measured report with stored input/expected/output identities, unequal N>5 phases, nonzero first/second harmonics across all spatial axes, fit/error maxima and an off-model projection comparison. No plotting dependency or screenshot oracle is required. D checks actual arrays and candidate correspondence.

High-risk scientific/custom-oracle route: fresh native blind A, fresh native blind B, restricted fresh native C and fresh native D after clean exact-candidate canonical make verify. Inherit PROJECT's approved behavior/risk review and complete native JSON/HTML report-integrity policy; percentages advisory, no selected threshold/exclusions. All configured push/PR Ubuntu24.04/macOS15 legs remain binding. No numeric scenario/review/repair/time/execution limits were set. The task pointer links coordinator evidence and prior chain accounting outside tracked candidate bytes.

Opened primary references: [Gustafsson et al., equations 8–10 and five lateral orders, pages 4959–4960](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf), [NumPy least-squares objective](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html), [NumPy SVD rank convention](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html). The paper motivates five phase orders; the exact representation, API, failure and accuracy choices above are this task's contract.
