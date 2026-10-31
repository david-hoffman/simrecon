# Finite-field reconstruction

The development module `scripts.finite_field_reconstruction` solves a fixed
discrete imaging problem. Supply the sampled kernel, its origin and the
illumination at every source voxel. The source is zero outside the supplied
box. This assumption can be wrong for a real specimen.

```python
import numpy as np
from scripts.finite_field_reconstruction import (
    build_finite_field_operator,
    finite_field_score,
    solve_finite_field,
)

shape = (1, 5, 5)
operator = build_finite_field_operator(
    kernel=np.array([[[0.25, 0.5, 0.25]]]),
    kernel_origin_zyx=(0, 0, 1),
    illumination=np.ones((1, 1, *shape)),
    detector_crop_zyx=((0, 1), (0, 5), (0, 5)),
    input_taper=np.ones((1, 1, *shape)),
    padding_shape_zyx=(1, 5, 7),
    source_spacing_um_zyx=(0.2, 0.1, 0.1),
)
# images must be supplied in this kernel's detector-signal gauge.
fit = solve_finite_field(
    operator, images=images, regularization=0.01, nonnegative=True,
    max_iterations=2000, absolute_tolerance=1e-9, relative_tolerance=1e-7,
    output_taper=np.ones(shape), output_zoom=1,
)
score = finite_field_score(
    operator, fit.source, images=images, regularization=0.01,
)
print(fit.status, fit.optimality_residual, fit.stopping_threshold)
```

The iteration budget above is an example, not a promise of convergence.
Accept mathematical stopping only when `fit.converged` is true and the
reported residual is at most the threshold. `iteration_limit` and `stagnation`
return the last complete candidate with an explicit incomplete stopping result.
An objective that keeps decreasing does not establish stationarity.

The residual taper multiplies both prediction and observation. If A is the
unweighted finite forward map, W the taper, M the detector entry count and P the
source voxel count, the objective is

```
J(x) = ||W(Ax-y)||²/(2M) + alpha ||x||²/(2P).
```

Its gradient is `A.T W²(Ax-y)/M + alpha*x/P`. The adjoint operation itself is
unweighted. As a sanity check, with one source voxel, one detector sample,
unit response, unit weight, no nonnegativity constraint and observation y,
the solution is `x=y/(1+alpha)`. Zero weight instead removes the observation
from the objective. It does not remove that sample from the returned unweighted
prediction or residual.

Kernel values already include any desired throughput or voxel-volume factor.
The solver applies neither normalization nor fitted brightness. Source values
are brightness coefficients per native source voxel. Output display values
retain that native coefficient gauge when zoomed; summing interpolated display
samples does not measure new physical flux.

Cropping selects detector coordinates without shrinking the source box.
Padding supplies enough workspace for linear convolution without adding source
unknowns. Extra valid padding leaves the mathematical map unchanged. Input
taper changes the objective. Output taper and zoom change only the displayed
source: taper first, then nonperiodic trilinear interpolation at spacing divided
by the integer zoom. Neither changes predictions, gradients or stopping.

`nonnegative=False` solves unconstrained least squares or ridge regression.
`nonnegative=True` constrains each source coefficient to be nonnegative.
Active constraints therefore define a different estimator from linear Wiener
filtering. At zero regularization, a nullspace can leave multiple source
solutions with identical predictions. A small detector residual or stationarity
residual does not bound source error.

RA07's periodic spectral estimator uses a different forward boundary and can
have different normal equations. The historical `fit_specimen` records a
float32 finite procedure with its own stopping labels. Neither is silently
replaced by this module. The [RA08 contract](../contracts/reference-alignment-ra08-v1.md)
defines exact units, validation, records and limits. The [comparison report](../reports/reference-alignment-ra08-comparison.md)
retains the actual independently controlled observations.
