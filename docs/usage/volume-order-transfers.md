# Known axial-profile volume transfers

`prepare_volume_order_otfs` returns orders 0, +1 and +2 on the full centered z/y/x frequency grid. Detection mass is normalized once. Side-order gain, phase and zero DC remain. The leading array axis identifies phase order.

This standalone example was executed in the locked local environment:

```python
import numpy as np
from simrecon import prepare_volume_order_otfs

psf = np.arange(1, 25, dtype=float).reshape(3, 2, 4)
psf[1, 0, 2] = 0.0
origin = (2, 1, 3)
spacing_um = (0.45, 0.16, 0.11)
displacement_z_um = (np.arange(3) - origin[0]) * spacing_um[0]
g1 = 0.8 * np.exp(2j * np.pi * displacement_z_um / (3 * spacing_um[0]))
g2 = 0.2 * np.cos(2 * np.pi * displacement_z_um / (3 * spacing_um[0]))
orders = prepare_volume_order_otfs(
    psf,
    axial_coefficients=np.stack([g1, g2]),
    voxel_size_um=spacing_um,
    origin_zyx=origin,
    source="finite demonstration PSF and caller-known axial profiles",
)
print(orders.values.shape)
print(orders.values[:, 1, 1, 2])  # DC for all three orders
print(orders.fz_per_um)
```

The recorded output appears below. These numbers demonstrate execution; the [independent comparison](../reports/volume-order-transfers-comparison.md) supplies numerical evidence.

```text
(3, 3, 2, 4)
[1.        +0.j         0.28096886-0.12705701j 0.07024221+0.j        ]
[-0.74074074  0.          0.74074074]
```

Coefficients must be a plain numeric NumPy ndarray `(2,Nz)`. They describe axial **displacement**, `(z-oz)*dz`, in the supplied PSF's frame. Both snapshots use stored float64/complex128 values. The PSF must be finite, real and nonnegative with positive converted mass. Sampling, origin and source are required. Origins are explicit in-bounds integers. Sampling is in micrometres; frequency axes use cycles per micrometre. Signed coefficients, arbitrary phases, zero rows and finite complex components with overflowing magnitude are valid.

The result's seven bindings are frozen. Its independently owned arrays remain writable. Calls preserve inputs and caller NumPy error/warning policies. `SimreconError.code` distinguishes validation, normalized FFT (fast Fourier transform) failure and nonfinite final rescaling. Memory errors and unrelated dependency exceptions propagate. The [contract](../contracts/volume-order-transfers-v1.md) lists codes and absolute numerical budgets. Subnormal contributions can round away within those budgets; near maximum float64, native computed range determines acceptance.

The mathematical kernel is `K_m=p*g_m`, with `g0=1`, and its transform uses a negative forward sign. No factor of two or per-order DC normalization is added. A zero side DC need not mean a zero side transfer. Negative orders, if needed, obey modular frequency negation with conjugation; reversing centered arrays fails at even-axis Nyquist bins.

An effective physical kernel requires axial illumination fixed relative to the objective focal plane during scanning. A specimen-fixed field has a different model. This operation estimates no calibration and supplies no lateral relocation or three-dimensional reconstruction. The finite periodic grid implies no continuous or infinite-field convergence. Detection throughput is discarded; gains are relative to normalized detection. Arbitrary tables need not represent realizable or nonnegative illumination. See [Gustafsson et al., equations 5–9](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf) and the [project contract](../contracts/volume-order-transfers-v1.md).
