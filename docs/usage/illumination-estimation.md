# Known-carrier illumination estimation

`estimate_illumination` fits one common phase offset and modulation for one
orientation from known relative phase steps, an integer carrier and a supplied
full complex optical transfer function (OTF). It returns corrected phases for
the existing `reconstruct` operation. See the [public contract](../contracts/illumination-estimation-v1.md)
for exact validation, arithmetic and accuracy rules, and the
[measured comparison](../reports/illumination-estimation-comparison.md) for independent evidence.

This complete example constructs a finite periodic acquisition. For measured
data, supply your acquired arrays and independently prepared calibration.

```python
import numpy as np
from simrecon import estimate_illumination, prepare_otf, reconstruct

ny, nx = 5, 7
dy, dx = 0.2, 0.35  # detector spacing, micrometres
carrier_bins_yx = (1, -1)  # signed detector frequency bins, y then x
brightness = np.array([1.7])  # explicit acquisition gain for this orientation
steps = np.array([-2.4, -0.8, 0.25, 1.1, 2.5, 3.7])  # radians
y, x = np.indices((ny, nx))
a, b = 2 * np.pi * y / ny, 2 * np.pi * x / nx
specimen = 3 + 0.35 * np.cos(b) + 0.2 * np.sin(a) + 0.17 * np.cos(a + b)
carrier_angle = 2 * np.pi * (y / ny - x / nx)
kernel = np.zeros((ny, nx))
kernel[0, 0], kernel[1, 0], kernel[0, 1] = 3, 1, 4
otf = prepare_otf(kernel, pixel_size_um=(dy, dx), origin_yx=(0, 0),
                  source="synthetic asymmetric kernel, masses 3:1:4")

# The synthetic generating offset and modulation are 0.7 rad and 0.9.
frames = []
for step in steps:
    illuminated = brightness[0] * specimen * (
        1 + 0.9 * np.cos(carrier_angle + step + 0.7)
    )
    frames.append(3 * illuminated / 8
                  + np.roll(illuminated, 1, axis=0) / 8
                  + np.roll(illuminated, 1, axis=1) / 2)
images = np.array(frames)[None]  # (orientations, phases, y, x)
relative_steps = steps[None]
carriers = [carrier_bins_yx]
estimates = [
    estimate_illumination(frames, otf=otf, phase_steps_rad=relative,
                          carrier_bins_yx=carrier)
    for frames, relative, carrier in zip(images, relative_steps, carriers, strict=True)
]
modulation = np.array([estimate.modulation for estimate in estimates])
if np.any((modulation <= 0) | (modulation > 1)):
    raise ValueError("Fitted modulation is outside reconstruct's physical domain")
wavevectors = np.array([[ky / (ny * dy), kx / (nx * dx)] for ky, kx in carriers])
result = reconstruct(
    images, otf=otf,
    phases_rad=np.stack([estimate.phases_rad for estimate in estimates]),
    wavevectors_per_um=wavevectors,  # cycles per micrometre, y then x
    modulation=modulation, brightness=brightness,
    regularization=0.0, apodization=np.ones((2 * ny, 2 * nx)),
)
print(estimates[0].phase_offset_rad, estimates[0].modulation)
print(result.image.shape)  # (10, 14), spacings (0.1, 0.175) micrometres
```

Images for each estimate have shape `(N, Ny, Nx)`, with `N >= 3`; steps have
shape `(N,)`. Both must be plain real integer or floating NumPy arrays, finite
before and after float64 conversion. Unequal steps and signed intensities are
allowed. The represented phase matrix must have numerical rank three, using
the existing [phase-separation rules](phase-separation.md). The OTF must match
the detector grid and satisfy the supplied-record invariants. Read-only and
strided inputs are accepted. Inputs remain unchanged; the frozen result record
contains an independently owned, mutable native float64 corrected phase array.

The forward discrete Fourier transform (DFT) has a negative exponential sign.
Spatial origin is index zero; increasing rows/columns give positive y/x. The
carrier is a signed integer shift in centered detector bins, including the
negative Nyquist endpoint on even axes. Frequencies for reconstruction are
`(ky/(Ny*dy), kx/(Nx*dx))` in cycles per micrometre, rather than radians per
micrometre. The OTF's declared kernel origin is already encoded in its phase.

At each closed-grid pair `q, q+k`, the fit uses `x=H(q+k)*D0(q)` and
`y=H(q)*Dplus(q+k)`. It fits `y=z*x`, returning `arg(z)` and `2*abs(z)`.
The complete signed complex OTF matters. There is no division by the OTF,
wrapping, support threshold or removal of the zero-frequency bin.
`overlap_count` includes geometric pairs with zero transfer.

Corrected phases rotate the represented sine/cosine entries and return
principal-equivalent angles in `[-pi, pi]`. This remains meaningful for arbitrary
huge finite steps: adding a small offset to such a step can erase it, and
reducing it modulo rounded `2*pi` changes the represented problem.

The estimator accepts unconstrained modulation, including values above one.
Such a value can diagnose model mismatch; `reconstruct` separately requires
`0 < modulation <= 1`. Brightness and carrier wavevectors remain explicit caller
inputs. Estimation performs no automatic reconstruction, carrier search, drift
correction, brightness estimation or independent phase-step estimation.

Empty geometric overlap and computed zero band energy or cross product are
rejected. Extremely weak nonzero information is accepted without a positive
cutoff; it can amplify noise arbitrarily. `relative_residual` measures the
complex fit discrepancy and is not confidence or a reliability probability.
This closed-grid integer fit supplies no alias-free recovery promise for
arbitrary specimens, aliased data, noise or model mismatch. Safely representable
extreme scales use protected arithmetic, but near-deficient or weak fits carry
no uniform digit guarantee. Domain failures use `SimreconError`; existing
separation error codes propagate, and allocation or unrelated failures propagate.
