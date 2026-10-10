# Known integer specimen drift

`correct_integer_drift` prepares one orientation's observations and phases for
existing separation and reconstruction. Supply known specimen displacements in
`(y, x)` pixels and the stationary illumination carrier in integer detector
Fourier bins. It rolls pixels by **negative displacement** and adds the
**positive carrier-dot-displacement phase increment**, using circular arithmetic.
The [contract](../contracts/integer-drift-correction-v1.md) defines the domain.

This complete example was executed with `.venv/bin/python`. It moves the specimen
before multiplying stationary illumination, then applies an asymmetric periodic
convolution. Every downstream parameter is explicit.

```python
import numpy as np
from simrecon import correct_integer_drift, prepare_otf, reconstruct, separate_phases

ny, nx = 5, 6
y, x = np.indices((ny, nx))
specimen = (2 + 0.3*np.cos(2*np.pi*y/ny) + 0.2*np.sin(2*np.pi*x/nx)
            + 0.1*np.cos(2*np.pi*(y/ny + x/nx)))
phases = np.array([0.0, 0.7, 2.0, 3.4, 5.2])  # radians, unequal steps
shifts = np.array([[0, 0], [1, -2], [-1, 1], [2, 3], [-3, -2]])
carriers = np.array([[1, 0], [0, 1]])
brightness, modulation = np.array([1.25, 0.75]), np.array([0.6, 0.8])
kernel = np.zeros((ny, nx))
kernel[0, 0], kernel[1, 0], kernel[0, 1] = 4/8, 1/8, 3/8
prepared = []
for r, (ky, kx) in enumerate(carriers):
    frames = []
    for phi, displacement in zip(phases, shifts, strict=True):
        moving_specimen = np.roll(specimen, tuple(displacement), axis=(0, 1))
        illumination = brightness[r]*(1 + modulation[r]*np.cos(
            2*np.pi*(ky*y/ny + kx*x/nx) + phi))
        illuminated = moving_specimen * illumination
        frames.append(4/8*illuminated
                      + 1/8*np.roll(illuminated, 1, axis=0)
                      + 3/8*np.roll(illuminated, 1, axis=1))
    prepared.append(correct_integer_drift(
        np.array(frames), phases_rad=phases, carrier_bins_yx=carriers[r],
        displacements_pixels_yx=shifts))

components = separate_phases(prepared[0].images, phases_rad=prepared[0].phases_rad)
assert components.dc.shape == (ny, nx)
dy_um, dx_um = 0.5, 0.25  # micrometres per detector pixel
otf = prepare_otf(kernel, pixel_size_um=(dy_um, dx_um), origin_yx=(0, 0),
                  source="explicit finite asymmetric kernel")
waves = carriers / np.array([ny*dy_um, nx*dx_um])  # cycles per micrometre
mask = np.zeros((2*ny, 2*nx))
mask[ny-1:ny+2, nx-1:nx+2] = 1
result = reconstruct(
    np.array([p.images for p in prepared]), otf=otf,
    phases_rad=np.array([p.phases_rad for p in prepared]),
    wavevectors_per_um=waves, brightness=brightness, modulation=modulation,
    regularization=0.0, apodization=mask)
yy, xx = np.indices((2*ny, 2*nx))
truth = (2 + 0.3*np.cos(2*np.pi*yy/(2*ny)) + 0.2*np.sin(2*np.pi*xx/(2*nx))
         + 0.1*np.cos(2*np.pi*(yy/(2*ny) + xx/(2*nx))))
error = float(np.max(np.abs(result.image - truth)))
print(result.image.shape, result.pixel_size_um, error < 1e-12)
# (10, 12) (0.25, 0.125) True
```

Both returned arrays independently own mutable native float64 C-contiguous
storage; the `DriftCorrection` record freezes their bindings. Inputs are
preserved. Pixel values are only permuted after conversion: no interpolation,
scaling or clipping. Images and phases accept plain real signed/unsigned integer
or floating NumPy arrays, either endian, strided or read-only. Source and
converted float64 values must be finite; rounding and finite underflow are
allowed. Subclasses, lists, bool and complex inputs are rejected.

The carrier must be a plain integer array `(2,)`; displacements must be a plain
integer array `(N, 2)`. Integer-valued floats are rejected. Integer extrema and
periodic aliases are valid and handled exactly before rational phase rounding.
The required phases have shape `(N,)`, while images have positive shape
`(N, Ny, Nx)`. Invalid inputs raise `SimreconError` with the corresponding code
`invalid_drift_images`, `invalid_drift_phases`, `invalid_drift_carrier` or
`invalid_drift_displacements`. Allocation and unrelated exceptions propagate.
Handled arithmetic preserves NumPy error mode and emits no `RuntimeWarning`.

Phases are returned in `[-pi, pi]` radians. Evaluate phase differences through
sine/cosine or phasors across the branch cut. Huge finite input phases retain
their directly represented trigonometric meaning. Preparation accepts `N=1`,
repeated phases and corrected degeneracy. Separation still requires at least
three frames and numerical phase rank three; correction can destroy that rank.

For pixel spacing `(dy_um, dx_um)`, the carrier becomes
`(ky/(Ny*dy_um), kx/(Nx*dx_um))` cycles/µm. In this example those wavevectors
are `(0.4, 0)` and `(0, 2/3)` cycles/µm. Reconstruction keeps its existing
calibration, conditioning, ridge, mask and interpolation rules. This example
uses integer-bin carriers, alias-free object modes and a caller-selected mask.
Its [measured comparison](../reports/integer-drift-correction-comparison.md)
includes a wrong pixel-only control.

The model requires periodic specimen translation before stationary illumination
and a fixed shift-invariant imaging system. Camera motion, moving illumination,
fractional displacement, nonperiodic edges, changing specimens and independent
phase errors need other models. Supplied shifts carry no confidence guarantee.
`estimate_translation` requires comparable equal-intensity references; it cannot
automatically infer these shifts from different raw illumination phase frames.
