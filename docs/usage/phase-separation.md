# Separate images at known phases

`separate_phases(images, *, phases_rad)` fits the unweighted first-harmonic
model to `N >= 3` images with explicitly supplied phases in radians. Unequal
spacing is accepted. Supply plain NumPy arrays with shapes `(N, y, x)` and
`(N,)`; spatial dimensions must be positive.

```python
import numpy as np
from simrecon import separate_phases

phases = np.array([-0.43, 0.21, 1.34, 2.57, 3.18, 4.73, 5.81])
images = (10 + 4*np.cos(phases) + 2*np.sin(phases))[:, None, None]
components = separate_phases(images, phases_rad=phases)
# dc is approximately [[10.0]]; c1 is approximately [[2.0 - 1.0j]].
```

The calculation uses the supplied float64 angles directly, without rounded
modulo reduction. At each pixel it solves

```text
H[p,:] = [1, np.cos(phases[p]), np.sin(phases[p])]
[A,B,C] = argmin ||H @ [A,B,C] - images[:,y,x]||_2
dc = A
c1 = (B-i*C)/2
fitted[p] = dc + 2*c1.real*H[p,1] - 2*c1.imag*H[p,2]
```

The example gives `B/2=2` and `-C/2=-1`, hence `c1=2-i`. Both coefficients
retain input intensity units and `(y,x)` sampling. With unequal phases, `dc`
is the fitted constant and generally differs from the arithmetic image mean.
For `N > 3`, off-model observations can have a nonzero fitted-input residual.
That residual measures the first-harmonic projection; it is separate from
numerical solver error. Ideal equally spaced full-cycle samples recover the
usual mean and negative-exponential sum divided by `N`.

Both inputs accept any real signed integer, unsigned integer or floating
NumPy dtype, either byte order, including signed intensities, read-only arrays
and strided storage. Bool, complex and other dtype kinds, lists and ndarray
subclasses are rejected. Source and converted values must be finite. Ordinary
float64 conversion defines the fitted problem: float16/float32 and integers
through 32 bits promote exactly; int64/uint64 and wider floating values can
round. Conversion underflow is permitted; conversion overflow is rejected.
Finite phases outside a principal interval are valid. Adding a represented
`2*pi` need not preserve trigonometric entries bit for bit.

Float64 singular value decomposition (SVD) supplies the solve and numerical
rank. Each computed singular value must strictly exceed
`eps*N*s_max`, where `eps=2^-52` and `s_max` is the largest singular value.
Rank below three is rejected. There is no additional angular-span or condition
cutoff, weighting or regularization. `[0, pi, 2*pi]` is numerically deficient;
three distinct clustered phases can be accepted. Full rank establishes
identifiability, but clustered phases can amplify noise and floating-point
error severely. Near the cutoff, useful coefficient digits and identical
rank decisions across backends or row reorderings are not guaranteed.

The [approved accuracy policy](../contracts/known-phase-separation-v2.md#independently-checkable-accuracy)
uses the represented NumPy float64 sine/cosine entries as exact matrix truth.
In returned coordinates, `K=H @ diag(1,2,-2)` and `z=[dc, Re(c1), Im(c1)]`.
The budget is normwise least-squares backward error `eta=128*N*eps`, with
per-coordinate final subnormal quantization up to `2^-1075`. This is a project
acceptance budget, not a fixed absolute error or a guarantee of useful digits.
Its finite forward-error consequence depends on conditioning and the fit
residual. It supplies no finite digit guarantee when the permitted matrix
perturbation reaches the smallest singular value. Rounded generated images
are compared with the minimizer for their stored values.

`PhaseComponents.dc` and `.c1` have native float64 and complex128 dtypes and
shape `(y,x)`. Each owns independently allocated, C-contiguous, mutable
storage. Neither input changes. The record binds attributes without freezing
arrays or validating direct construction.

Per-pixel power-of-two scaling protects the solve, and harmonic coefficients
are halved before restoring scale. Only the final `dc`, `Re(c1)` and `Im(c1)`
coordinates determine output range; an overflowing internal doubled harmonic
or complex magnitude alone is not a rejection. Final-coordinate overflow
rejects the whole call without clipping. Final rounding can overflow even
when the exact minimizer lies just inside float64 range; the contract does
not promise an exact-real range classifier. Subnormal/zero output is allowed
within the accuracy policy. Handled arithmetic preserves the caller's NumPy
floating-error mode and emits no arithmetic RuntimeWarning.

Domain errors use `SimreconError`, a `ValueError` subclass with string `code`
and `message`. Exact message prose and precedence between simultaneous
violations are unspecified.

| Obligation | Error code |
|---|---|
| Plain image ndarray | `invalid_phase_images` |
| Real integer/floating image dtype | `invalid_phase_dtype` |
| Image shape/count | `invalid_phase_shape` |
| Finite source/converted images | `nonfinite_phase_images` |
| Plain phase ndarray | `invalid_phase_angles` |
| Real integer/floating phase dtype | `invalid_phase_angles_dtype` |
| Phase shape/count | `invalid_phase_angles_shape` |
| Finite source/converted phases | `nonfinite_phase_angles` |
| Numerical rank three | `rank_deficient_phases` |
| SVD nonconvergence or nonfinite factors | `phase_solver_failure` |
| Finite final coordinates | `unrepresentable_phase_components` |

Missing, positional or extra arguments retain ordinary binding `TypeError`.
The previous `phase_offset_rad` keyword is removed; there is no alias or
implicit phase grid. Allocation failure retains `MemoryError`; unrelated
programming exceptions propagate. Existing MRC conversion interfaces remain
unchanged. This operation adds no phase estimation, higher harmonics, optical
simulation, file adapter or reconstruction.

See the [actual seven-phase comparison](../reports/phase-separation-comparison.md)
for independent expected components, actual outputs and all residuals.
