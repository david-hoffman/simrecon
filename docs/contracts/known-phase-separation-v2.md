# Known-phase 2D separation: variable, explicitly supplied phases

**Version 2.0 amendment draft, October 5, 2026.** The owner approved the direction below and instructed the coordinator to update the contract and launch a fresh task on existing PR #5. This is the concrete intake record for that revision. The numerical acceptance policies listed as unresolved are not silently approved. The [milestone Current state](../tasks/numerical-foundations-plan.md#current-state) records authority, evidence and conserved allowances. [Version 1](known-phase-separation-v1.md) remains the historical contract for the currently published implementation.

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

The proposed signature is `separate_phases(images, *, phases_rad)`. It replaces the scalar `phase_offset_rad` interface on the unmerged PR; no implicit equally spaced grid, default phase, scalar-offset alias or metadata-derived angle is supplied.

`images` is a plain NumPy ndarray of shape `(N, y, x)`, with `N >= 3` and positive spatial dimensions. Its dtype is any NumPy signed integer, unsigned integer or real floating dtype (`dtype.kind` in `i`, `u`, `f`), either byte order. Signed intensities, read-only arrays and strided arrays are valid. Bool, complex, object, string, datetime and structured dtypes remain outside this real integer/floating domain. There is no dtype-width whitelist.

`phases_rad` is proposed as a plain real integer/floating NumPy ndarray of shape `(N,)`. Its entry at index `p` is the known angle for image `p`, in radians. The proposal accepts finite angles after float64 conversion without a principal-interval restriction; cosine and sine interpret the converted angle. Angles are periodic, so `0` and `2*pi` are equivalent, not independent observations. Reordering images together with their angles must preserve the result. Inputs are not mutated.

Images and phases convert once to float64 before numerical processing. The mathematical truth is defined for those converted values. Promotion of float16/float32 and integers through 32 bits is exact; int64/uint64 and wider floats may round, and wider finite floating inputs may overflow during conversion. The contract permits ordinary rounding and underflow during conversion, and rejects nonfinite source or converted values. It does not promise lossless conversion of every dtype merely because float64 is used.

## Mathematical meaning

At each spatial pixel, form the `N x 3` real matrix and observation vector:

```text
H[p, :] = [1, cos(phi_p), sin(phi_p)]
I[p] = float64(images[p, y, x])
[A, B, C] = argmin_(a,b,c) sum_p (I[p] - a - b*cos(phi_p) - c*sin(phi_p))**2

dc[y, x] = A
c1[y, x] = (B - i*C)/2
fitted_I[p] = dc + 2*Re(c1*exp(i*phi_p))
```

The least-squares problem is unweighted. For a full-column-rank `H`, its minimizer is unique. Noiseless observations `I_p=A+B*cos(phi_p)+C*sin(phi_p)` recover the declared coefficients within the finalized numerical accuracy policy. A constant signal recovers `dc=A`, `c1=0`. Both returned coefficients retain input intensity units and `(y,x)` sampling/order.

For unequal phases, `dc` is the fitted constant coefficient, not generally the arithmetic mean of the observations. For equally spaced phases spanning the cycle, the orthogonal special case agrees with `dc=sum(I)/N`, `c1=sum(I*exp(-i*phi))/N`. The negative sign and factor of two match version 1. The example `10+4*cos(phi)+2*sin(phi)` has `dc=10`, `c1=2-i` for either equally or unequally spaced identifiable samples.

For `N > 3`, arbitrary stored observations may not lie in the first-harmonic model. The result is their least-squares projection; its fit residual can legitimately be nonzero. A fit residual is distinct from error in the numerical solver or the independently expected coefficients. Do not retain an exact-resynthesis promise for arbitrary off-model data.

Full rank establishes identifiability, not numerical stability. Three distinct phases in part of a cycle can identify this model, while clustered phases can amplify noise and floating-point error. Merely spanning the numerical interval is insufficient: `[0, pi, 2*pi]` has only two distinct phases and cannot identify the sine coefficient.

## Preserved representation and boundaries

Return `PhaseComponents` with independently allocated, mutable, native-endian C-contiguous float64 `dc` and complex128 `c1`, each of shape `(y,x)`. Neither output aliases the input, phase vector or other output. The record binds attributes without freezing arrays or adding direct-construction validation. Existing MRC conversion interfaces and errors remain unchanged.

Retain ordinary argument-binding `TypeError` and allocation `MemoryError`. Keep domain errors in existing `SimreconError` with stable string codes and unspecified precedence when multiple obligations fail. Proposed existing image codes remain `invalid_phase_images`, `invalid_phase_dtype`, `invalid_phase_shape` and `nonfinite_phase_images`. Phase-vector, numerical-rank, coefficient-representation and solver-failure policy must be finalized below before tests; they are not inherited from the scalar-offset rules.

## Numerical acceptance policies still to finalize in fresh intake

1. **Numerical rank and conditioning.** Propose a float64 SVD-based least-squares solve, with the standard NumPy numerical-rank criterion as the starting point: singular values below `eps*max(N,3)*s_max` are treated as zero. Decide the exact boundary comparison, whether additional conditioning rejection is needed, and its observable error/code. Do not invent a minimum angular-span rule or silently reject valid unequal phases. A fixed maximum condition number would be a new scientific acceptance boundary requiring explicit approval.
2. **Accuracy.** Specify an independently defensible error/backward-error bound accounting for `H`, its conditioning, number of observations, converted-value scale, cancellation and subnormals. The version-1 bound `64*eps*M + 8*u` was established for the orthogonal three-phase model and must not be copied unchanged. A/B derive and assess oracle expectations from the approved finalized policy, not from implementation outputs or a second invocation of the selected product solver.
3. **Representation and operation-time failure.** Finite observations under a poorly conditioned full-rank matrix can imply coefficients outside float64 range. Decide exact rejection/propagation behavior for unrepresentable coefficients and nonconvergent solves. Do not silently clip scientific coefficients, return unexplained nonfinite arrays, or promise finite results for every finite input independently of matrix gain.

These are material decisions, not permission to start implementation with guessed tolerances. Fresh intake must complete their concrete read-back and obtain approval of the identified finalized documents and revised checkpoint review window under AGENTS.md. Do not request duplicate approval of the already authorized variable-phase/explicit-angle/broader-dtype direction.

## Independent tests and human comparison

Fresh A owns the revised public tests and fixture; fresh B assesses their exact checkpoint and which prior evidence remains applicable. The accepted version-1 checkpoint is not automatically valid for changed phase, conversion, oracle or rejection meaning. The shared fixture/oracle/observer changes require explicit dependency mapping and fresh review before C.

The revised report uses a deterministic asymmetric analytic phantom with at least one `N > 3` unequally spaced, well-conditioned phase set. A independently authors expected coefficients from the declared forward model and/or an independently justified least-squares oracle. C renders all input phases, independent expected and actual recovered signed components, absolute component-error maps and all fitted-input residuals. Matching panels share fixed scales and all error/residual scales and maxima are explicit. Distinguish noiseless model-consistent examples from off-model least-squares residuals. Record actual phases, matrix/fixture identities, dtype conversion, command, environment and exact-candidate provenance. D checks the real PNG and numeric correspondence. No screenshot oracle or high-resolution reconstruction is introduced.

## Sources and status

The matrix follows directly from the declared sinusoidal signal model. [NumPy least-squares documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html) defines the least-squares objective, singular values and numerical-rank cutoff; [NumPy conversion documentation](https://numpy.org/doc/stable/reference/generated/numpy.ndarray.astype.html) describes conversion versus value preservation. These primary pages were opened during October 5 intake. They inform the proposal, not approval of new project limits or an implementation-derived oracle.

The route remains high risk: fresh blind native A/B, restricted C and fresh native D, with the default full-local exact-candidate gate and complete configured Linux/macOS CI before updating the same PR. One milestone Current state holds accounting. Prior attempts/charges are retained; fresh app context does not restore blindness, reset closed review windows or create repair authority.
