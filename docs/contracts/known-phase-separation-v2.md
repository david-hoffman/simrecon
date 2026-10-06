# Known-phase 2D separation: variable, explicitly supplied phases

**Version 2.0, amendment Proposal 3, October 5, 2026; owner-approved October 5, 2026.** The owner approved the direction below and instructed the coordinator to update the contract and launch a fresh task on existing PR #5. This is the concrete intake record for that revision. The owner explicitly approved Proposal 3 and its identified documents/scenario inventory/execution window; the milestone Current state records that authority. The [milestone Current state](../tasks/numerical-foundations-plan.md#current-state) records authority, evidence and conserved allowances. [Version 1](known-phase-separation-v1.md) remains the historical contract for the currently published implementation.

## Owner-approved direction

Support more than three images, their actual known phase angles, and broader real input dtypes. Equal spacing is not required. Phase coverage around the cycle is useful for conditioning; the scientific identifiability criterion is the rank of the separation matrix, not an angular-span check. The owner said, “ok let's do this, update the contract and then launch it in a new task (fresh context) but working on the same PR”.

This amendment retains the first-harmonic 2D model and the `dc`/`c1` result. Supporting additional illumination orders requires a separate output/interface contract. It is not introduced by accepting additional observations. No phase estimator, optical simulation, OTF handling, spatial Fourier transform, band shifting, reconstruction, file adapter, CLI or camera model is added. Pyotf remains the owner's choice for later PSF/OTF simulation.

## Revised public interface and inputs

```python
from simrecon import PhaseComponents, separate_phases

components = separate_phases(images, phases_rad=phases)
components.dc
components.c1
```

The signature is `separate_phases(images, *, phases_rad)`. It replaces the scalar `phase_offset_rad` interface on the unmerged PR; no implicit equally spaced grid, default phase, scalar-offset alias or metadata-derived angle is supplied.

`images` is a plain NumPy ndarray of shape `(N, y, x)`, with `N >= 3` and positive spatial dimensions. Its dtype is any NumPy signed integer, unsigned integer or real floating dtype (`dtype.kind` in `i`, `u`, `f`), either byte order. Signed intensities, read-only arrays and strided arrays are valid. Bool, complex, object, string, datetime and structured dtypes remain outside this real integer/floating domain. There is no dtype-width whitelist.

`phases_rad` is a plain real integer/floating NumPy ndarray of shape `(N,)`. Its entry at index `p` is the known angle for image `p`, in radians. The proposal accepts finite angles after float64 conversion without a principal-interval restriction; cosine and sine interpret the converted angle. The ideal trigonometric model is periodic. Represented angles separated by a represented `2*pi` need not produce bitwise identical trigonometric values. In particular, `[0, pi, 2*pi]` is numerically rank deficient under the cutoff below. Jointly reordering images and angles preserves the mathematical fit; returned arrays agree within the accuracy policy, not necessarily bitwise. Inputs are not mutated.

Images and phases convert once to float64 before numerical processing. The mathematical truth is defined for those converted values. Promotion of float16/float32 and integers through 32 bits is exact; int64/uint64 and wider floats may round, and wider finite floating inputs may overflow during conversion. The contract permits ordinary rounding and underflow during conversion, and rejects nonfinite source or converted values. It does not promise lossless conversion of every dtype merely because float64 is used.

## Mathematical meaning

At each spatial pixel, form the `N x 3` real matrix and observation vector:

```text
H[p, :] = [1, float64(np.cos(phi_p)), float64(np.sin(phi_p))]
I[p] = float64(images[p, y, x])
[A, B, C] = argmin_(a,b,c) ||I - H @ [a,b,c]||_2

dc[y, x] = A
c1[y, x] = (B - i*C)/2
fitted_I[p] = dc + 2*c1.real*H[p,1] - 2*c1.imag*H[p,2]
```

Here `phi_p` is the converted float64 angle. The supported NumPy float64 sine/cosine values are the represented matrix entries and are treated as exact real numbers when defining the solver-accuracy oracle. This separates solver error from trigonometric-library variation. No exact-real trigonometric accuracy or bitwise cross-platform guarantee is added. Evaluate the supplied angles directly; do not first reduce them modulo a rounded `2*pi`, which defines a different problem for large angles.

The least-squares problem is unweighted. For a full-column-rank `H`, its minimizer is unique. Exactly model-consistent converted observations recover the declared coefficients within the accuracy policy below. Rounded forward-generated observations are compared with the minimizer for their actual stored values, rather than with an unrounded generating signal. A constant signal recovers `dc=A`, `c1=0`. Both returned coefficients retain input intensity units and `(y,x)` sampling/order.

For unequal phases, `dc` is the fitted constant coefficient, not generally the arithmetic mean of the observations. For ideal equally spaced phases spanning the cycle, the orthogonal special case agrees with `dc=sum(I)/N`, `c1=sum(I*exp(-i*phi))/N`. The negative sign and factor of two match version 1. The ideal example `10+4*cos(phi)+2*sin(phi)` has `dc=10`, `c1=2-i` for either equally or unequally spaced identifiable samples; represented/rounded examples follow the stored-matrix accuracy rule.

For `N > 3`, arbitrary stored observations may not lie in the first-harmonic model. The result is their least-squares projection; its fit residual can legitimately be nonzero. A fit residual is distinct from error in the numerical solver or the independently expected coefficients. Do not retain an exact-resynthesis promise for arbitrary off-model data.

Full rank establishes identifiability, not numerical stability. Three distinct phases in part of a cycle can identify this model, while clustered phases can amplify noise and floating-point error. Merely spanning the numerical interval is insufficient: `[0, pi, 2*pi]` is numerically rank deficient under the stated cutoff. The represented matrix can have tiny nonzero trigonometric roundoff entries; those do not make its sine coefficient numerically identifiable.

## Preserved representation and boundaries

Return `PhaseComponents` with independently allocated, mutable, native-endian C-contiguous float64 `dc` and complex128 `c1`, each of shape `(y,x)`. Neither output aliases the input, phase vector or other output. The record binds attributes without freezing arrays or adding direct-construction validation. Existing MRC conversion interfaces and errors remain unchanged.

Retain ordinary argument-binding `TypeError` and allocation `MemoryError`. Keep domain errors in existing `SimreconError` with stable string codes and unspecified precedence when multiple obligations fail. Exact message prose is unspecified. No partial result is returned on failure.

| Violated obligation | Stable code |
|---|---|
| Images are not a plain ndarray | `invalid_phase_images` |
| Image dtype kind is outside `i`, `u`, `f` | `invalid_phase_dtype` |
| Image shape is outside `(N >= 3, positive_y, positive_x)` | `invalid_phase_shape` |
| Image source or converted values are nonfinite | `nonfinite_phase_images` |
| Phases are not a plain ndarray | `invalid_phase_angles` |
| Phase dtype kind is outside `i`, `u`, `f` | `invalid_phase_angles_dtype` |
| Phase shape is not `(N,)`, including a count mismatch | `invalid_phase_angles_shape` |
| Phase source or converted values are nonfinite | `nonfinite_phase_angles` |
| Numerical rank of `H` is below three | `rank_deficient_phases` |
| SVD/least-squares computation raises `numpy.linalg.LinAlgError` or returns unusable nonfinite numerical factors | `phase_solver_failure` |
| Computed final output coordinates cannot be stored as finite float64 values | `unrepresentable_phase_components` |

Only the stated numerical failure is translated; do not mask unrelated programming exceptions or `MemoryError`. Conversion/underflow/range handling has the declared outcomes independently of the caller's NumPy floating-error mode, without changing that mode or leaking arithmetic `RuntimeWarning` diagnostics for these handled cases.

## Proposed numerical rank, accuracy and range policy

The owner approved Proposal 3, including this contract, the linked 29-scenario task inventory and the amendment execution window, on October 5, 2026. The already authorized generalization and prior charged windows/repairs remain conserved.

### Numerical rank

Use float64 singular value decomposition (SVD) for `H` and a float64 SVD-based least-squares method; do not use normal equations as the product solver. Let `eps = 2^-52`, `s_max` be the largest computed singular value and `tau = eps * max(N, 3) * s_max`. Numerical rank counts computed singular values **strictly greater** than `tau`; equality is rejected. Reject rank below three with `rank_deficient_phases`. This adopts NumPy's standard rank scale with an explicit equality rule. Do not add an angular-span check, a fixed maximum condition number, regularization, weighting or a minimum-norm answer for deficient inputs. Values so close to the threshold that computed SVD variation changes their classification have no identical-classification promise across backends, platforms or row reorderings. Permutation invariance applies to the mathematical fit and to returned results when both calls are accepted; it is not a promise that roundoff-ambiguous rank decisions agree.

A full numerical rank permits the fit; it does not guarantee useful coefficient digits or resistance to phase/noise uncertainty. The known angles are taken as supplied, with no measurement-uncertainty model. The usage guide must explain this limitation.

### Independently checkable accuracy

Work in the returned coordinates, at each pixel, in exact real arithmetic for the oracle:

```text
z_hat = [returned dc, returned c1.real, returned c1.imag]
K = H @ diag(1, 2, -2)
z_star = argmin_z ||K*z - b||_2       # b = converted observations
q = 2^-1074                          # smallest float64 subnormal
eta = 128 * max(N, 3) * eps
```

Require perturbations `E`, `f` and final quantization `d` to exist such that `K+E` remains full-column-rank and

```text
z_hat-d = argmin_z ||(K+E)*z - (b+f)||_2
||E||_2 <= eta * ||K||_2
||f||_2 <= eta * ||b||_2
abs(d[j]) <= q/2 for each of the three returned coordinates
```

`||K||_2` is the spectral norm; vector norms are Euclidean. This is the proposed **normwise least-squares backward-error requirement**. The factor `128*max(N,3)` is an explicit project acceptance budget, not a universal LAPACK theorem. LAPACK documents a modest dimension-dependent factor without supplying this constant. Its feasibility on the supported environments remains unverified until blind A/B assess the independently derived tests. Evidence that it is infeasible or too weak returns to intake rather than changing the constant after seeing product outputs.

The requirement has no fixed intensity-unit floor or division by a possibly zero coefficient. It scales with observations and the represented matrix. The `d` allowance permits final subnormal quantization; ordinary relative rounding falls within the main budget. Evaluate the oracle using independently justified scaling or higher precision. Overflowed norms or rounded-to-zero allowances are not evidence.

A/B establish the requirement using independent perturbation certificates or a justified normwise backward-error observer. An upper bound from an explicitly constructed certificate is sufficient when it meets the budget; failure of one conservative certificate is not proof that no permitted certificate exists. Supplemental forward/optimality comparisons may fill gaps, but an unproved stationarity-only comparison cannot stand in for this backward-error requirement. The oracle must not invoke the product solver again to manufacture expected answers. Its observer precision, approximation/certificate error and legitimate alternatives receive independent B review. A perturbation that makes `K+E` singular is not a valid witness: certify full rank explicitly when the norm bound does not imply it. In the informative regime `eta*||K||_2 < sigma_min(K)`, the norm bound itself guarantees full rank.

An exact finite forward-error consequence is available when conditioning permits it. Let `a=||K||_2`, `s=sigma_min(K)` for the exact represented matrix, `alpha=eta*a`, `beta=eta*||b||_2`, and `r_star=b-K*z_star`. When `alpha < s`,

```text
||z_hat-z_star||_2 <= (beta + alpha*||z_star||_2)/(s-alpha)
                       + alpha*||r_star||_2/(s-alpha)**2
                       + sqrt(3)*q/2
```

To derive it, put `K_tilde=K+E`, `z_tilde=z_hat-d`. The perturbed normal equations and `K.T*r_star=0` give

```text
z_tilde-z_star = K_tilde^+*(f-E*z_star)
                 + (K_tilde.T*K_tilde)^-1 * E.T*r_star
sigma_min(K_tilde) >= s-alpha
```

Taking norms gives the displayed bound. Each coordinate error is no larger than the vector-norm bound. This derivation is independent of the implementation. Exactly model-consistent observations have `r_star=0`, so the leading amplification is proportional to the condition number. Off-model observations add the residual-dependent squared-condition term. Their fit residual is not a solver error.

When `alpha >= s`, this bound supplies **no coefficient-digit guarantee**; the backward-error requirement still applies. No tighter cutoff, regularization or fabricated finite forward bound is inferred. Stationarity may be reported as supplemental evidence: `K.T*K*(z_hat-z_star)=K.T*(K*z_hat-b)`, but its condition-squared bound alone is too weak near deficiency to certify the promised backward error.

Sanity check in the ideal four-quadrature example: `H` has singular values `2, sqrt(2), sqrt(2)`, and `K` has `sqrt(8), sqrt(8), 2`. Thus `eta=512*eps` and `alpha/s=eta*sqrt(2)`, safely below one. `10+4*cos(phi)+2*sin(phi)` gives `z_star=(10,2,-1)`, hence `c1=2-i`. Constants are exactly in the represented model through its first column. Zero observations need absolute/subnormal comparison, not relative error divided by zero.

These definitions are owner-approved numerical meaning under Proposal 3. Independent oracle construction is owned by blind A and assessed by fresh B before C. It adds no shipped tolerance/reporting API or dependency.

### Output range and operation failure

The range boundary is the three returned real coordinates `dc`, `c1.real` and `c1.imag`. Do not reject merely because internal `B=2*Re(c1)`, `C=-2*Im(c1)`, a vector norm, or complex magnitude overflows. Use safe scaling through the solve and form the halved outputs before restoring image scale, or an independently justified equivalent. Underflow to subnormal/zero is permitted within the accuracy rule. There is no automatic clipping, regularization or partial result.

If computed final coordinates cannot be restored/stored finitely, raise `unrepresentable_phase_components` for the whole call. This is a computed-output range policy, not an exact-real classifier of whether the mathematical minimizer lies just above or below float64 maximum. A computed finite result must satisfy the accuracy rule. A result whose final rounding reaches overflow may produce the range error even when the exact minimizer is just inside the range. The contract makes that range-edge uncertainty explicit; it does not promise finite output for every finite observation under arbitrary inverse gain. Inputs with safely representable results must not fail because of avoidable intermediate overflow. A/B include independently justified interior-range, subnormal and genuine final-range-failure examples; do not set contradictory expectations inside the roundoff uncertainty band.

Translate numerical nonconvergence (`numpy.linalg.LinAlgError`) and unusable nonfinite factors to `phase_solver_failure`, separately from output range. Ordinary allocation failure remains `MemoryError`. New failure semantics or a tighter conditioning/digit requirement require renewed intake approval.

## Independent tests and human comparison

Fresh A owns the revised public tests and fixture; fresh B assesses their exact checkpoint and which prior evidence remains applicable. The accepted version-1 checkpoint is not automatically valid for changed phase, conversion, oracle or rejection meaning. The shared fixture/oracle/observer changes require explicit dependency mapping and fresh review before C.

The revised report uses a deterministic asymmetric analytic phantom with at least one `N > 3` unequally spaced, well-conditioned phase set. A independently authors expected coefficients from the declared forward model and/or an independently justified least-squares oracle. C renders all input phases, independent expected and actual recovered signed components, absolute component-error maps and all fitted-input residuals. Matching panels share fixed scales and all error/residual scales and maxima are explicit. The required figure may use the noiseless analytic example alone; an additional off-model figure is optional. The numeric tests must cover off-model projection. Explain stored-value roundoff residuals and distinguish them from off-model fit residuals and solver error. Record actual phases, matrix/fixture identities, dtype conversion, command, environment and exact-candidate provenance. D checks the real PNG and numeric correspondence. No screenshot oracle or high-resolution reconstruction is introduced.

## Sources and status

The matrix follows directly from the declared sinusoidal signal model. [NumPy least-squares documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) defines the least-squares objective, singular values and numerical-rank cutoff; [NumPy conversion documentation](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html) describes conversion versus value preservation. These primary pages were opened during October 5 intake and reopened for Proposal 3. [NumPy matrix-rank documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html) supports the rank scale and strict comparison; [LAPACK DGELSD parameters](https://www.netlib.org/lapack/explore-html/d9/d67/group__gelsd_ga0bee7e1b9e7e43f59ecf2419b2759c42.html) explicitly treat equality as zero. [NumPy floating limits](https://numpy.org/doc/stable/reference/generated/numpy.finfo.html) defines epsilon, per-component complex limits and subnormals. [LAPACK least-squares error analysis](https://netlib.org/lapack/lug/node83.html) distinguishes small backward error from condition-sensitive coefficient error; it supplies no universal `128*N` theorem. The [normwise backward-error discussion in LAPACK Working Note 299, Appendix B.2.3](https://www.netlib.org/lapack/lawnspdf/lawn299.pdf) describes independent least-squares perturbation constructions. These sources were opened for Proposal 3. They inform the proposal; the explicit budget and exact finite forward-error consequence are project choices/derivations requiring approval.

The route remains high risk: fresh blind native A/B, restricted C and fresh native D, with the default full-local exact-candidate gate and complete configured Linux/macOS CI before updating the same PR. One milestone Current state holds accounting. Prior attempts/charges are retained; fresh app context does not restore blindness, reset closed review windows or create repair authority.
