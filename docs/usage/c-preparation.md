# Prepare native specimen quadratures

CE02 adds `prepare_bands` for declared three-dimensional specimen exposures.
It corrects camera counts, applies the selected lateral edge operation and
sum equalization, then performs lateral transforms, phase separation and an
axial transform. It returns native Fourier quadratures and scalar order-noise
variance factors. The [transfer stage](c-optical-transfer.md) supplies accepted
optical responses, and [known-parameter reconstruction](c-known-reconstruction.md)
consumes these actual bands with supplied carriers and complex modulation.

The [public contract](../contracts/c-equivalence-preprocessing-v1.md) fixes
shapes, source identity, normalization, supported modes and errors. Inputs have
explicit axes `(time,direction,phase,z,y,x)`. The x length must be even and at
least 2; the z length must be at least 2. Raw samples must be exactly representable
as finite float32 values. No raw values, correction maps or caller arrays change.

```python
import numpy as np
from simrecon import prepare_bands

raw = np.full((1, 3, 5, 3, 12, 16), 20, dtype=np.float32)
prepared = prepare_bands(
    raw,
    dxy_um=0.1,
    dz_um=0.25,
    norders=3,
    background=3.0,
    lateral_zoom=2,
    axial_zoom=1,
    edge_pixels=0,
    equalize=False,
)
print(prepared.quadratures.shape)  # (1, 3, 5, 3, 12, 9)
print(prepared.noise_variance_factors)  # one per direction/order
```

Pixel spacings are in micrometres. Background and per-exposure background are
in detector counts. The flat-field slope multiplies background-subtracted
counts. It is never a divisor or an inferred calibration. For X columns, Y
rows, Z planes and D directions, the upstream scale is
`1/(X*Y*Z*lateral_zoom**2*axial_zoom*D)`. Zoom changes this scale but leaves the
native preparation grid unchanged.

Uniform phases use unnormalized specimen separation. A supplied `(D,P)` phase
array selects the inverse or unweighted left inverse of the declared forward
matrix. It must have full column rank. Supplied repeated phases can be valid
in an overdetermined design. A full-rank clustered design can still be
unresolved in finite precision; numerical-operation failures raise
`SimreconError` without regularization or a lower-rank fallback.
Noise values are variance factors, not their
printed square roots and not a full covariance model.

Quadrature slots are `0,E1,O1,E2,O2,...`. Each slot is a complex array with
unshifted `(kz,ky,kx)` indices and a stored nonnegative x half-spectrum. The
stored lateral Nyquist column deliberately retains its raw phase-slot values
through the axial transform, matching the selected C path. At other samples,
the positive harmonic is `E+i*O` and its negative partner is `E-i*O`; E and O
are already complex Fourier arrays.

The camera's exact bottom-right raw `-1` sentinel copies that frame's left
neighbour and changes the owned corner background/slope for later exposures.
The traversal is time, direction, z, phase. Sentinel locations and final camera
maps are exposed in the result. Other negative samples are ordinary data.

The default edge width is 10, so smaller controls must select an explicit safe
width. Width 0 and integers below -1 bypass edge modification; -1 selects the
half-sample sine window. Other allowed widths apply the source's additive
opposite-edge operation. Equalization uses the direction-zero/phase-zero sum,
with explicit z/time sharing flags. Zero divisors raise `SimreconError`;
negative nonzero sums are valid. Disable equalization explicitly for zero-sum
inputs. There is no epsilon replacement or automatic fallback.

CE02 proves raw-to-band mathematical behavior on the declared domain. It claims
no binary C-output agreement, final image recovery or resolution. Odd y lengths are defined in preparation.
[Known-parameter filtering](c-known-reconstruction.md) preserves the separately
contracted source index behavior, including the omitted-row quirk. Padding, drift, off-exposures,
2D, multichannel file binding and other deferred modes are not supported here.
