# Fractional finite-window volume relocation

`reconstruct_volume_fractional` adds known physical carriers to the existing
known-phase volume fusion interface. The [contract](../contracts/reference-alignment-ra07-v1.md)
defines its finite filter-before-shift estimator and numerical domain.

```python
from simrecon import reconstruct_volume_fractional

result = reconstruct_volume_fractional(
    images,
    order_otfs=calibrations,
    phases_rad=phases,
    carriers_per_um=carriers,
    gains=gains,
    regularization=0.05,
    output_shape_yx=(11, 12),
    apodization=taper,
)
```

Supply real images shaped `(orientation, phase, z, y, x)`, actual known phases,
dimensionless complex order-transfer records and a physical y/x carrier pair
per orientation in cycles per micrometre. Every argument is explicit. This
operation estimates no carrier, phase, transfer or noise quantity.

For detector `(z,y,x)=(1,5,6)` with spacing `(0.5,0.25,0.25)` µm, the lateral
field lengths are `5*0.25=1.25` µm and `6*0.25=1.5` µm. A supplied carrier
`(0.5,-0.5)` cycles/µm is therefore `(0.625,-0.75)` detector bins. These values
are exact for the represented inputs. The first positive order's native DC
anchor moves to object frequency `(fz,fy,fx)=(0,-0.5,+0.5)` cycles/µm.
Output `(1,11,12)` keeps the field of view and index-zero origin, with spacing
`(0.5,1.25/11,1.5/12)` µm. It changes sample density, which alone proves no
resolution gain.

Filtering occurs on native bands. Its common power denominator queries the
signed native transfer interpolants at each order's shifted physical detector
frequency. Unavailable queries contribute no observation. Native filtered
coefficients are embedded without cropping, synthesized on the output grid,
and multiplied by a fractional phase ramp. A final normalized discrete Fourier
transform gives the output spectrum before the caller's amplitude taper.

The phase ramp generally produces tails on every output bin. This is the
declared periodic finite-window representation. The complete-window guard
retains translated native anchors; it does not make fractional tails compact.
Observation relocation uses a finite Fourier kernel. Transfer queries use
Cartesian complex linear interpolation. They are different operations.

At even Nyquist the signed transfer interpolants retain the existing integer
operation's modular reflection and single complex endpoint. The physical
RA05 sampler has different endpoint domains and is not a substitute here.
The exact integer-bin limit recovers `reconstruct_volume` with identical
support, gain, regularization and taper. RA06's real covariance inverse solves
a different problem and is not the fractional operation's limit.

Return values use the existing `Reconstruction3D` record. Both volume and
spectrum retain complex amplitudes. No hidden real projection, brightness
normalization, exterior model, automatic bandwidth extension or continuum
resolution guarantee applies. See the [comparison](../reports/reference-alignment-ra07-comparison.md)
for retained direct-sum observations and a filter-order counterexample.

The executed example above returns spacing
`(0.5,0.11363636363636363,0.125)` µm. Its full complex spectrum and volume agree
with independently fixed finite sums within `8.34e-16` and `4.90e-15` input
intensity units, respectively. The report links the complete reproducible
input construction and retained measurement hashes. These are arithmetic
observations on this synthetic example, not an instrument-accuracy guarantee.
