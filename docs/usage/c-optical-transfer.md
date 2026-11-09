# Prepare and sample empirical optical transfers

CE03 adds empirical bead preparation and complex optical transfer function
(OTF) sampling. A point spread function (PSF) is the spatial response. This
entry follows the selected retained-C bead procedure; passing an arbitrary
normalized PSF through a Fourier transform does not supply that procedure.
Reconstruction remains unavailable until the later rebuild stages.

Use decoded arrays and explicit acquisition settings. This stage opens no
files and estimates no physical bead parameters through the retired optimizer.
The [public contract](../contracts/c-equivalence-optical-transfer-v1.md) defines
all units, branches and failures. The [task pointer](../tasks/c-equivalence-optical-transfer.md)
links the sole live acceptance/evidence record; documentation alone is no verdict.

A raw bead array has axes `(phase,z,y,x)`. The selected ordinary 3D profile
requires odd phase count1,3,5,7 or9, at least two axial planes, and square even
lateral dimensions of at least10 pixels. Compensation requires more than one
phase. Raw samples must be finite and exactly representable as float32.
Arithmetic uses binary64. Spacings, bead diameter and line spacing use
micrometres (um); wavelength is required acquisition metadata in nanometres
(nm), and angles are radians.

```python
import numpy as np
from simrecon import prepare_bead_otf, sample_otf

# A small declared detector-count control, not a physical recovery claim.
raw = np.full((5, 5, 24, 24), 2, dtype=np.float32)
raw[:, 2, 12, 9] += np.array([12, 8, 5, 9, 15], dtype=np.float32)
prepared = prepare_bead_otf(
    raw,
    dxy_um=0.1,
    dz_um=0.2,
    linespacing_um=0.20365,
    wavelength_nm=520,
    bead_diameter_um=0.08,
    background_counts=2,
)
value = sample_otf(
    prepared.transfer,
    0.3, -0.2, 1,
    dkz_cyc_um=1.0,
    order=1,
)
```

`prepared.transfer.samples` has axes `(order,radius,axial)`; the example gives
shape `(3,13,5)`. Table increments are `1/(24*0.1)` cycles/um laterally and
`1/(5*0.2)` cycles/um axially. `center_pixels_xyz` reports the peak/parabola
center in x,y,z pixel coordinates. `background_counts`, phase angles,
pre-combination quadratures, scaling factors, combination angles and resolved
settings retain the preparation provenance. Returned records are frozen and
arrays are owned/read-only. Caller arrays are unchanged.

The caller applies its fixed10-pixel sequential edge operation, even when
opposite strips overlap. It chooses backgrounds before that operation and
locates the bead center before background subtraction. Exposure backgrounds
have precedence over paired camera maps; maps have precedence over a declared
scalar; otherwise the source estimates the four corner-intersection regions.
The negative last-pixel camera rule and unused center-background diagnostic
remain part of the declared safe domain. No specimen intensity equalization
or specimen normalization enters this bead stage.

Default bead compensation divides by the continuum-sphere transform at each
order-shifted frequency. A transform zero is unsupported; no regularizer hides
it. Radial averaging retains conjugate axial symmetry, including imaginary-odd
values. Default normalization reuses one inverse maximum modulus from order
zero across all quadratures. The side quadratures combine by the source's
magnitude/sign angle, rather than `C+i*S`. Optional axis/origin repairs,
support cleanup, each-quadrature normalization, forced first-order phase and
final conjugation follow the contract's exact ordering.

Complete supplied transfer samples can instead be declared directly. Radial
layout is `(order,radius,axial)`; full layout is `(order,axial,y,x_half)`.
The origins lie at index0, and full x stores the nonnegative half. Samples
must be finite and exactly representable as complex64. Declaration copies the
values into owned complex128 storage; it applies no normalization or symmetry
repair. All orders must be supplied explicitly.

```python
from simrecon import declare_otf

r, z = np.indices((5, 4))
first = 1 + 2*r + 3*z + 1j*(r-z)
tables = np.stack([first, first/2])
transfer = declare_otf(
    tables, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.5
)
value = sample_otf(transfer, 0.2, 0.0, -1, dkz_cyc_um=0.25, order=1)
# Algebraic expectation: 3.55 - 0.35j transfer units.
```

The sampler takes physical x/y frequencies in cycles/um, a signed integer
native axial index, and the native axial frequency increment in cycles/um.
It broadcasts queries, returns complex128 arrays (a zero-dimensional array
for scalars), and preserves complex bilinear/trilinear interpolation.
Negative x in a full table reflects x,y,z before interpolation and conjugates
the result. Wrapping adds one period; it is not general modulo reduction.

Every source stencil vertex must exist, including neighbors with zero weight.
The final lateral sample therefore is not always queryable. Actual safe flat
aliases are preserved; unsafe addresses raise `OtfError` rather than clipping,
zero filling or silently returning a partial result. Invalid declarations,
unsupported modes and unresolved numerical operations also raise `OtfError`,
a ValueError subclass. Near cancellation or a transform zero, finite arithmetic
can be sensitive; no universal forward-error guarantee is made.

Non-square empirical modes, odd-x packing, 2D empirical preparation, I2M/
two-objective paths and file adapters remain outside this selected profile.
Complete declared layouts and their safe sampling do not restore a 2D or 3D
reconstruction workflow. Historical effective external FFT headers/libraries
remain unqualified. This work proves the declared source mathematics; it makes
no bitwise C-output, image recovery or resolution claim. The
[small sampling control](../reports/c-otf-control.md) explains the independent
numerical figure and its limited accuracy bound.
