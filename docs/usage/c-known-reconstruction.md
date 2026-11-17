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
print(result.x_um[:3])     # [-1.0, -0.875, -0.75] micrometres
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

The [wide allocation-byte rule](../contracts/wide-allocation-domain-v1.md)
admits bytes above the historical unsigned32 workspace and signed32 lookup
ceilings when exact integer bytes and actual-width aggregate arrays fit native
`intp`. Signed element counts, indices and actual stencil checks still apply.
Known invalid geometry rejects before array-sized work. Representation validity
does not promise available RAM or backend execution; allocation/backend failures
remain operation errors with their causes, and interruption propagates.

The original profile described here is ordinary stationary single-objective
three-dimensional data with at least two retained orders, integer zoom and an
explicit positive Wiener parameter. Its original calls retain their behavior.
[CE06 acquisition modes](c-acquisition-modes.md) add `AcquisitionBands`, true
2D, safe fractional enlargement and contracted power/precise/filter/debug
options, with their actual finite-domain restrictions. Automatic Wiener
selection, axial input padding, two-objective/Bessel paths and complete file
composition remain outside the selected support. This entry continues to
consume supplied parameters; actual estimation is the separate accepted stage.

This establishes a finite source-mathematical mapping within its declared domain.
Historical C executable agreement, physical image recovery and resolution remain
separate, unqualified outcomes. The old `reconstruct`, `reconstruct_volume`,
`prepare_otf` and retired modules remain unavailable. The new transfer APIs are
`prepare_bead_otf`, `declare_otf` and `sample_otf`.

The [fixed numerical control](../reports/c-known-control.md) provides registered
inputs, independent finite-sum expectations, observed signed images and normalized
spectra on fixed scales. It distinguishes mathematical agreement from recovery
and historical executable agreement.

## Opt-in single-storage known reconstruction

Pass `precision="single-mixed-v1"` to `reconstruct_known` with a
`PreparedBands32` created by `declare_prepared_bands32`. The constructor accepts
explicit native complex64 quadratures with axes `(T,D,Q,Z,Y,X//2+1)` and
float64 noise factors with axes `(T,D,O)`, plus the declared input shape,
spacing, integer zoom and provenance. It snapshots independent, owned,
read-only arrays. It performs no acquisition preparation or parameter search;
callers must supply valid bands and their normalization metadata.

The result is `KnownReconstruction32`: complex64 filtered quadratures and a
signed float32 image. The image accumulator and coordinates remain float64;
small parameter calculations retain the precision specified by the
[single-profile contract](../contracts/single-known-reconstruction-v1.md).
FFT input/output dtype does not establish every internal backend arithmetic or
workspace dtype. Double remains the default. Passing single bands to double,
or existing double bands to the single profile, raises `ReconstructionError`
instead of implicitly converting them.

This profile supports the contracted stationary 3D known-parameter slice.
Native 2D/Z1, fractional zoom and nondefault CE06 modes are outside it. There
is no precision option on acquisition preparation, estimation, workflow or
summary. See the contract for exact options, rounding, finite-domain and
failure rules, and the [execution report](../reports/single-known-reconstruction/execution-report.md)
for workload-specific observations and limits. No process-memory ceiling,
speed ratio, physical recovery or 16 GiB feasibility follows from the profile.
