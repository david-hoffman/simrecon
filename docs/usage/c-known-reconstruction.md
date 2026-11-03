# Reconstruct with supplied carriers and modulation

`reconstruct_known` consumes accepted native phase bands and optical transfer
tables, then applies the selected retained C filter and real-space assembly.
The caller supplies carriers and complex modulation; this function estimates
neither. It returns signed samples, coordinate vectors and filtered quadratures.
It applies no positivity projection or iterative specimen fit.

```python
import numpy as np
from simrecon import declare_otf, prepare_bands, reconstruct_known

raw = np.full((1, 1, 3, 4, 8, 8), 100, dtype=np.float32)
bands = prepare_bands(
    raw, dxy_um=0.25, dz_um=0.4, norders=2, background=0,
    lateral_zoom=2, axial_zoom=1, edge_pixels=0, equalize=False,
)
transfer = declare_otf(
    np.ones((2, 20, 16), dtype=np.complex64),
    layout="radial", dkr_cyc_um=0.5, dkz_cyc_um=0.625,
)
result = reconstruct_known(
    bands, transfer,
    carriers_cyc_um=np.array([[0.2, 0.0]]),
    modulation=np.array([[1.0 + 0.0j]]),
    wavelength_nm=520, numerical_aperture=1.2, immersion_index=1.33,
    wiener=0.5, suppress_singularities=False, output_taper="none",
)
print(result.image.shape)  # (1, 4, 16, 16)
print(result.x_um[:3])     # [-2.0, -1.875, -1.75] micrometres
```

This is a deliberately artificial unit-transfer example, not an optical
calibration or physical recovery demonstration. Phase-independent raw counts
are not generally reproduced as identical output counts: preparation scale,
phase separation, all eligible signed transfer powers and regularization remain
part of the mapping. No gain is fitted to compensate for them.

Raw axes are time, direction, phase, z, y, x. Accepted `PreparedBands` retain
their declared detector spacing and integer zoom; reconstruction uses that exact
upstream normalization. Carriers have shape `(directions,2)` and units cycles per
micrometre, and specify the fundamental order. Modulation has shape
`(directions,orders-1)` for positive side orders. Order-zero modulation is one.
Negative partners follow all-axis conjugate reflection. Both transfer layouts
accepted by CE03 remain available, including asymmetric complex samples.

The output image axes are time, z, y, x. Output spacing is detector spacing divided
by zoom. Coordinate vectors use centered labels, while the inverse transform is
not shifted. Integer zero padding preserves the positive native Nyquist endpoint
without splitting. Noninteger carrier relocation happens after native filtering.
The inverse sum is unnormalized; no extra voxel-count or direction average is
applied. Negative output values are retained.

Defaults enable physical-radius suppression and the shifted elliptical cosine
taper. `suppression_radius_bins` controls where the source suppression helper
applies; it does not rescale the helper's physical radius. `output_taper="none"`
and `suppress_singularities=False` disable those respective operations. The
order-zero options follow the source precedence, including the distinction
between dampening weights and omitting the final center band. See the
[complete equations and supported domain](../contracts/c-equivalence-known-parameters-v1.md)
before choosing those options.

Source behavior includes an odd-height quirk. Filtering/recombination omits one
stored row for odd y dimensions, with some reflected zero writes still possible
on side orders. This function preserves that behavior; it does not silently fill
the row. The returned `filtered_quadratures` expose the actual result.

`ReconstructionError` reports invalid inputs, unsafe source indices/stencils,
unrepresentable arrays and undefined or failed numerical operations. A table
must contain every actually accessed interpolation vertex, including vertices
with zero interpolation weight. An all-zero band, modulation or transfer does
not waive the stencil checks. Output arrays own read-only storage; inputs stay
unchanged. An accepted writable band's finite quadratures/noise can be supplied
without replaying its raw images.

The supported profile is ordinary stationary single-objective three-dimensional
data with at least two retained orders, accepted integer zoom and explicit positive
Wiener parameter. Drift, carrier/modulation estimation, automatic Wiener selection,
axial input padding, two-objective/Bessel modes, fractional lateral zoom, power or
precise-boundary taper and file composition remain outside this stage.

This establishes a finite source-mathematical mapping within its declared domain.
Historical C executable agreement, physical image recovery and resolution remain
separate, unqualified outcomes. The old `reconstruct`, `reconstruct_volume`,
`prepare_otf` and retired modules remain unavailable. The new transfer APIs are
`prepare_bead_otf`, `declare_otf` and `sample_otf`.
