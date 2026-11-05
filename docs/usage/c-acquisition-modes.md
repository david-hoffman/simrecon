# Prepare declared acquisition modes

`prepare_acquisition_bands` prepares declared two-dimensional (2D) or
three-dimensional (3D) specimen exposures. It adds source-defined phase,
equalization, off-exposure and drift modes to the accepted preparation,
parameter-estimation and known-parameter reconstruction stages. It opens no
files. The [complete contract](../contracts/c-equivalence-acquisition-modes-v1.md)
fixes each selected branch, safe domain, diagnostic and error.

`prepare_bands` retains its original 3D contract and integer zooms. Choose the
new entry explicitly for the extended modes; a transfer table with one axial
sample does not declare specimen dimensionality.

Raw axes are `(time,direction,phase,z,y,x)`. Supply `acquisition_mode="2d"`
with z length 1, or `"3d"` with z length at least 2. The x length is even.
Raw values must be finite and exactly representable as float32. Input arrays
and camera metadata stay unchanged. The result's quadratures and order-noise
variance factors are owned writable arrays; diagnostic arrays own read-only
storage. Noise axes are `(time,direction,order)`.

```python
import numpy as np
from simrecon import prepare_acquisition_bands, declare_otf, reconstruct_known

# Artificial constant-count and unit-transfer control. No fitted or physical
# recovery claim follows from it.
raw = np.full((1, 3, 5, 1, 10, 10), 100, dtype=np.float32)
bands = prepare_acquisition_bands(
    raw, acquisition_mode="2d", dxy_um=0.25, dz_um=0.0,
    norders=3, background=0, lateral_zoom=1.5, axial_zoom=1,
    edge_pixels=0, equalize=False,
)
transfer = declare_otf(
    np.ones((3, 20, 1), dtype=np.complex64),
    layout="radial", dkr_cyc_um=1.0, dkz_cyc_um=1.0,
)
result = reconstruct_known(
    bands, transfer,
    carriers_cyc_um=np.zeros((3, 2)),
    modulation=np.ones((3, 2), dtype=np.complex128),
    wavelength_nm=500, numerical_aperture=1.0, immersion_index=1.0,
    wiener=0.5, suppress_singularities=False, output_taper="none",
)
print(result.image.shape)  # (1, 1, 15, 15)
```

Detector spacings and line spacing use micrometres (um); wavelength uses
nanometres (nm); phases use radians. A zero axial pitch is permitted only for
the selected 2D domain. Its downstream calculations use the actual transfer's
axial step. An active between-direction drift prepass still requires positive
axial pitch because it evaluates a separate reciprocal. Lateral zoom must be
exactly float32-representable, at least 1, and produce integral output x/y
lengths. Axial zoom remains a positive integer. With 2D input and axial zoom
above 1, only output plane zero receives the source 2D inverse; the others are
zero. This is not axial interpolation.

Supply explicit phase rows with `phases_rad`, or direction-specific phase
increments with `phase_steps_rad`. Steps take precedence after input
validation. The historical step parser supports at most three directions;
explicit phase rows have no corresponding three-direction restriction.
Equalization retains the independent time/z reference choices. Disabled
equalization flags are inert. A zero selected divisor raises an error;
there is no epsilon repair.

Off-exposure axes are `(time,direction,phase,z,off,y,x)`. Supply the individual
off frames along the `off` axis. Preparation applies the source camera-state
corrections in order and sums the corrected frames. It preserves the N=1
equalization exception and repeated first-plane combination.
Choose `combine_off_orders` explicitly; this procedure is not a general
background or noise estimator. The contract defines the selected statistics
and their finite/undefined domains.

Drift flags select two different actual estimators. Between-direction drift
uses a fixed 10-pixel specimen edge operation and a quarter-power weighted
cross spectrum; within-exposure 2D drift uses prepared on-plus-off frames and
a half-power weighting. Their measured vectors, finite peak/parabola/wrap
decisions and positive Fourier corrections appear in `ModeEvent` diagnostics.
Specimen/prepass fixed10 needs x,y at least 10. Fitted drift and linked phase
adjustment have flag-dependent timestamp, phase-allocation, direction and
phase-count prerequisites. Read the complete contract before selecting them;
missing required metadata raises `AcquisitionModeError` rather than inventing
clock values or a different estimator. Fast storage does not automatically
make every drift path safe.

Both `estimate_parameters` and `reconstruct_known` consume the actual
`AcquisitionBands` record. Estimation needs at least two orders; 3D searching
needs at least three. Within `estimate_parameters`, 2D searching uses the source's order pair 0/1.
Both searched and known/reused 2D paths form cumulative modulation products.
Known or reused carriers still fit fresh modulation from the current data.
`reconstruct_known` consumes the supplied modulation without fitting it. The accepted regression energy and stencil
conditions remain mandatory; a successful preparation does not guarantee
estimation or filtering success. Constant phase-independent data in the
example are a known-parameter control, not suitable evidence for a fit.

For multiple times, slice time-dependent arrays and relabel events in public
value records as specified by the contract. Pass each time's actual returned
carriers and modulation to its reconstruction. For a time-varying Wiener
schedule, first compute the full-series effective value
`w_t = wiener + (t + 1) * wiener_increment / T`. Pass that value to the
one-time call with `wiener_increment=0`. Do not rescale bands, replay
raw equalization or substitute true parameters to claim fitted composition.
`reinterpret_2d_planes` performs the separately specified literal section
regrouping; it neither decodes files nor infers a nominal-plane permutation.
The complete file workflow remains CE07 scope.

Known reconstruction also accepts the contracted Wiener increment, power
taper exponent, precise taper, overlap-filter and explode options. Select them
explicitly. A positive initial Wiener value remains required, and the
single-channel schedule increments before the first time. Some nominally
selectable source branches are undefined on their executed data: active 2D
precise taper at DC is one example. Rejection preserves the source domain;
this port supplies no repaired optics, optimizer or automatic Wiener model.

Empirical bead preparation separately admits z length 1 and rectangular
planes with even x>=8, y>=10 and y<=x+2, subject to every executed-operation
condition. Its literal edge helper writes initialized padding and differs
from the specimen helper. The x8/y10 family is defined; square x8/y8 is not.
Single-plane default repairs can still be unsafe. Prepared transfer values
compose directly with sampling, fitting and filtering in complex128. Do not
redeclare them through complex64 or rebind their axial increment. Raw
`declare_otf` samples retain their existing exact-complex64 input domain.

The estimator result preserves CE05's six-file source identity. Acquisition
input provenance uses ten files and travels separately in the exact two-key
settings suffix after the original thirteen settings. Original
`PreparedBands` results retain their original metadata. Arrays remain caller
parameters, not a favored phantom or hidden raw replay.

These entries implement the selected source mathematics. They establish no
historical C executable agreement, complete-file workflow, physical recovery
or resolution by themselves. Retired scientific entries remain unavailable.

See the [fixed between-direction drift control](../reports/c-acquisition-control.md)
for a numerical example with known carriers and modulation.
