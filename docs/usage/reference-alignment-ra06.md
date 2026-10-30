# Covariance-weighted known-parameter volume inversion

`reconstruct_volume_weighted` estimates a real periodic specimen under explicitly
supplied phases, carrier bins, gains, complex order transfers and exposure
covariance. It returns the untapered inverse and its raw predictions, residuals
and objective, then applies an independent output amplitude taper.
The current implementation uses a dense real observation matrix and can be
expensive on large grids. It provides no large-volume execution guarantee.

```python
import numpy as np
from simrecon import VolumeOrderOtf, reconstruct_volume_weighted

values = np.zeros((3, 1, 1, 1), dtype=np.complex128)
values[0] = 1
otf = VolumeOrderOtf(
    values=values,
    fz_per_um=np.zeros(1), fy_per_um=np.zeros(1), fx_per_um=np.zeros(1),
    voxel_size_um=(0.2, 0.1, 0.1), origin_zyx=(0, 0, 0), source="declared unit DC",
)
images = np.array([2.1, 1.8, 2.05, 1.9, 2.2]).reshape(1, 5, 1, 1, 1)
variances = np.array([0.01, 0.04, 0.02, 0.09, 0.03])
result = reconstruct_volume_weighted(
    images,
    order_otfs=[otf],
    phases_rad=np.array([[0.0, 0.8, 2.0, 3.4, 5.1]]),
    carriers_bins=np.zeros((1, 2), dtype=np.int64),
    gains=np.ones(1),
    exposure_covariance=np.diag(variances)[None],
    regularization=0.4,
    output_shape_yx=(1, 1),
    apodization=np.ones((1, 1, 1)),
)
print(result.untapered_volume, result.information_rank, result.data_objective)
```

Here the only unknown is one real intensity. The independent scalar inverse is
`sum(images/variances)/(sum(1/variances)+0.4)`. The unequal variances determine
the raw-exposure metric. Even with only one specimen unknown, the five separated
coordinates can have correlated uncertainty; they are diagnostics, not five
independent specimen observations.

This executed example returns `2.05574649` intensity units, rank 1 and data
objective `2.79580282`. Computed before calling the product, the scalar inverse
gives `2.055746487415344`; the observed difference is `4.44e-16` intensity units.
Here `M=P=1` and the only forward column is one, so the covariance and alpha
appear in the same inverse-intensity-squared denominator.

Covariance has squared input-intensity units and shape `(R,N,N)`. The declared
model permits exposure correlation but assumes independent detector voxels and
orientations, with the same covariance at every voxel. It does not include
uncertainty in calibration or estimated noise parameters. Generalized
least-squares separation preserves the information relevant to the known phase
model, including when more than five exposures contain an off-model residual.

`regularization` is alpha in the whitened raw objective, with inverse squared
intensity units. It is not automatically the squared-transfer denominator
penalty of ordinary spectral fusion. For the decoupled generalized Wiener case,
with separated signed-band variances v and normalized weights `v_ref/v`, that
denominator penalty is `alpha*v_ref`. Under ideal orthogonal phases and equal
independent exposure variance sigma², `v_ref=sigma²/N`; equivalently an
unweighted raw ridge beta gives denominator penalty `beta/N`. Represented
float64 phases require their actual covariance transformation.

At alpha zero, the operation returns the minimum-norm solution using its
documented singular-value cutoff. Rank-deficient information succeeds and reports
its rank; unobserved directions remain zero by convention. Singular or
numerically indefinite covariance is rejected instead of replaced by a noise
floor. At positive alpha, ridge acts on real specimen values before taper.

Predictions, residuals, objective and information rank refer to the untapered
real inverse. An asymmetric amplitude taper can make the final complex volume
nonreal. The [public contract](../contracts/reference-alignment-ra06-v1.md)
defines the real observation map, its explicit real-DC convention for arbitrary
complex records, even endpoints, validation and operational limits. The original
`reconstruct_volume` estimator retains its own complex fusion semantics.

The [measured comparison](../reports/reference-alignment-ra06.md) retains the
fixed design and scientific observations. Agreement with a stored-input inverse
establishes an estimator convention; it does not establish physical accuracy or
optimal reconstruction risk under an undeclared noise model.
