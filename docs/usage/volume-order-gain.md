# Relative complex volume-order gain

`estimate_volume_order_gain` fits one dimensionless complex correction to a
supplied nominal effective optical transfer function (OTF). Supply the known
fundamental phase steps, exact y/x carrier bins and selected order, one or two.
Images have shape `(N, Nz, Ny, Nx)`, with `N >= 5`.

This standalone example generates a finite matching model, fits both orders,
copies the calibration, applies each correction once and reconstructs it.
Spacing is in micrometres (µm); phases are in radians.

```python
import numpy as np
from simrecon import (
    VolumeOrderOtf,
    estimate_volume_order_gain,
    reconstruct_volume,
)

shape = (1, 2, 6)
steps = np.array([0.07, 0.81, 1.93, 2.87, 3.72, 4.81, 5.69])
spacing = (0.7, 0.9, 1.1)
axes = tuple(np.fft.fftshift(np.fft.fftfreq(n, d)) for n, d in zip(shape, spacing))
values = np.empty((3, *shape), dtype=np.complex128)
values[0] = 1
values[1] = 0.6 + 0.1j
values[2] = 0.4 - 0.2j
nominal = VolumeOrderOtf(values, *axes, spacing, (0, 0, 0), "synthetic nominal")

carrier = np.exp(2j * np.pi * np.arange(shape[2]) / shape[2])[None, None, :]
dc = np.full(shape, 2.0)
c1 = np.broadcast_to(2 * (0.8 + 0.35j) * values[1] * carrier, shape)
c2 = np.broadcast_to(2 * (-0.45 + 0.7j) * values[2] * carrier**2, shape)
c, s = np.cos(steps), np.sin(steps)
h = np.column_stack((np.ones(len(steps)), c, s, c*c-s*s, (2*c)*s))
coordinates = np.stack((dc, 2*c1.real, -2*c1.imag, 2*c2.real, -2*c2.imag))
images = (h @ coordinates.reshape(5, -1)).reshape((len(steps), *shape))

nominal_before = nominal.values.copy()
fits = [
    estimate_volume_order_gain(
        images,
        order_otf=nominal,
        phase_steps_rad=steps,
        carrier_bins_yx=(0, 1),
        order=m,
    )
    for m in (1, 2)
]
assert abs(fits[0].gain - (0.8 + 0.35j)) < 1e-12
assert abs(fits[1].gain - (-0.45 + 0.7j)) < 1e-12

corrected_values = nominal.values.copy()
for m, fit in zip((1, 2), fits):
    before = corrected_values.copy()
    corrected_values[m] *= fit.gain
    if not np.isfinite(corrected_values[m]).all():
        raise ValueError("corrected transfer components exceed finite range")
    for other in set((0, 1, 2)) - {m}:
        assert np.array_equal(corrected_values[other], before[other])
corrected = VolumeOrderOtf(
    corrected_values,
    nominal.fz_per_um.copy(),
    nominal.fy_per_um.copy(),
    nominal.fx_per_um.copy(),
    tuple(nominal.voxel_size_um),
    tuple(nominal.origin_zyx),
    nominal.source,
)
result = reconstruct_volume(
    images[None],
    order_otfs=(corrected,),
    phases_rad=steps[None],
    carriers_bins=np.array([[0, 1]]),
    gains=np.ones(1),
    regularization=0.0,
    output_shape_yx=(2, 10),
    apodization=np.ones((1, 2, 10)),
)
assert np.max(np.abs(result.volume - 2)) < 1e-12
assert np.array_equal(nominal.values, nominal_before)
print([fit.gain for fit in fits])
print(float(np.max(np.abs(result.volume - 2))))
```

The supplied fundamental steps stay unchanged for both fits and recombination.
Each correction multiplies only its selected positive transfer row. The
recombiner supplies the matching modular conjugate negative transfer. Order two
has its own correction; it need not equal the square of order one's correction.

Every geometric overlap pair participates. The fit cross-weights the DC band
by the selected transfer and the selected band by the DC transfer. It performs
no support thresholding, transfer division, ridge or automatic correction.
`coherence` is amplitude correlation; `relative_residual` is computed directly
from normalized vectors. Both are dimensionless diagnostics.

A zero predictor raises `unidentifiable_volume_order_gain`; empty overlap raises
`no_volume_order_gain_overlap`. A zero response returns gain zero, residual zero,
coherence zero and `status="zero_response"`. Nonzero orthogonal response returns
gain zero, residual one, coherence zero and `status="zero_correlation"`. These
zero gains identify no phase. Finite restoration underflow can also return a
zero gain with `status="fitted"`.

The estimator snapshots its inputs and preserves caller floating and warning
policies. It validates all calibration fields, including the unused order.
Gain components must remain finite. It returns scalar metadata and leaves
correction and reconstruction to the caller.

High coherence alone does not prove alias freedom or measured physical
calibration. Stored-input fit accuracy, unrounded specimen truth and later
ridge bias are separate comparisons. See the [contract](../contracts/volume-order-gain-v1.md)
and [measured comparison](../reports/volume-order-gain-comparison.md).
