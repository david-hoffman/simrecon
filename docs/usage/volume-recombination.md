# Known five-order volume recombination

`reconstruct_volume` combines known phase orders on an explicit signed output window. It returns complex volume samples and a centered complex spectrum. All keywords are required. The [contract](../contracts/volume-recombination-v1.md) defines validation, numerical range and errors; the [measured comparison](../reports/volume-recombination-comparison.md) separates agreement with the stored-data estimator from agreement with a specimen.

This standalone example prepares effective optical transfer functions (OTFs), creates finite circular measurements, separates their phases and reconstructs them. The uniform detection point spread function (PSF) passes only DC in the ideal model. Its second axial illumination row makes object mode `(1,0,4)` observable through detector mode `(1,0,0)` with lateral carrier `(0,-2)`. The chosen ridge biases the coefficient.

Run with the locked product interpreter, `.venv/bin/python`:

```python
import numpy as np
from simrecon import (
    prepare_volume_order_otfs, reconstruct_volume, separate_volume_phases,
)

nz, nx = 3, 5
psf = np.ones((nz, 1, nx))
axial = np.zeros((2, nz), dtype=np.complex128)
axial[1] = 0.8 * np.exp(2j * np.pi * np.arange(nz) / nz)
orders = prepare_volume_order_otfs(
    psf, axial_coefficients=axial, voxel_size_um=(0.7, 1.3, 0.4),
    origin_zyx=(0, 0, 0), source="example finite circular kernel",
)
phases = np.array([0.05, 0.82, 1.9, 2.71, 3.48, 4.65, 5.61])
z, x = np.indices((nz, nx))
specimen = 1 + 0.2 * np.cos(2 * np.pi * (z / nz + 4 * x / nx) + 0.3)
kernels = [psf / psf.sum(),
           psf / psf.sum() * axial[0, :, None, None],
           psf / psf.sum() * axial[1, :, None, None]]
components = []
for m, kernel in enumerate(kernels):
    modulated = specimen[:, None, :] * np.exp(
        2j * np.pi * m * (-2) * x[:, None, :] / nx
    )
    filtered = np.zeros_like(modulated, dtype=np.complex128)
    for displacement in np.ndindex(psf.shape):
        filtered += kernel[displacement] * np.roll(
            modulated, displacement, axis=(0, 1, 2)
        )
    components.append(filtered)
c, s = np.cos(phases), np.sin(phases)
basis = np.column_stack((np.ones(len(phases)), c, s, c*c-s*s, (2*c)*s))
images = (components[0].real[None]
          + 2 * components[1].real[None] * basis[:, 1, None, None, None]
          - 2 * components[1].imag[None] * basis[:, 2, None, None, None]
          + 2 * components[2].real[None] * basis[:, 3, None, None, None]
          - 2 * components[2].imag[None] * basis[:, 4, None, None, None])
phase_components = separate_volume_phases(images, phases_rad=phases)
result = reconstruct_volume(
    images[None], order_otfs=[orders], phases_rad=phases[None],
    carriers_bins=np.array([[0, -2]]), gains=np.ones(1),
    regularization=0.25, output_shape_yx=(1, 13),
    apodization=np.ones((3, 1, 13)),
)
print(result.volume.shape)
print(result.voxel_size_um)
print(result.spectrum[2, 0, 10])  # centered object mode (1,0,4)
```

Executed output, rounded for display:

```text
(3, 1, 13)
(0.7, 1.3, 0.15384615384615385)
(0.06869835427420087+0.021250891265534543j)
```

For detector shape `(Nz,Ny,Nx)` and exact integer carriers `(cy,cx)`, supply `Ly >= Ny + 4*max(abs(cy))` and `Lx >= Nx + 4*max(abs(cx))`. These conditions apply even with zero transfers or a zero mask. Each order `m` moves detector bin `(jz,jy,jx)` to `(jz,jy-m*cy,jx-m*cx)`. There is no wrapping, cropping or axial resampling. Output spacings preserve the original field of view, in micrometres.

The estimator uses `U = sum(conj(gain*E)*D)`, `V = sum(|gain*E|²)`, then `spectrum = mask*U/(V+ridge)` where the denominator is positive; otherwise the coefficient is zero. Gain enters once. The amplitude mask acts after the unmasked quotient passes finite-range checks. The inverse transform is the positive-exponent sum, with no extra output-count division. Origin phases already present in the supplied transfers are used once.

Negative transfers use modular negation on all detector axes. An even detector Nyquist bin has one signed lift. For input `Nx=4`, output `Lx=8`, DC transfer one and data `(1,-1,1,-1)`, the volume is `exp(-2*pi*i*2*x/8)`: its imaginary part reaches ±1. Preserve it. Taking `.real` would change the estimator.

Images, phases, gains and mask must be plain real integer/floating NumPy arrays. Carriers must be plain integer arrays. All calibration fields are validated, including directly constructed records. Converted float64 observations define the stored problem. Outputs have frozen field bindings and separate owned mutable arrays; callers can edit array contents. Inputs and caller floating/warning policies are preserved. No file access occurs inside the operation.

The example establishes finite-model information, not general physical super-resolution. Periodic acquisition can alias different extended object modes. Missing transfers, ridge, masking, noise and off-model phase residuals also limit recovery. The physical effective-kernel interpretation requires an axial illumination profile fixed relative to the focal plane and zero-order profile `g0=1`. Source strings remain opaque, unverified labels.
