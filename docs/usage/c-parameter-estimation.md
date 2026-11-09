# Estimate fundamental carriers and complex modulation

`estimate_parameters` uses prepared specimen bands and declared optical transfer
tables to estimate illumination carriers and complex side-order modulation.
It follows the selected retained C finite search. The original profile described here is ordinary stationary single-objective
three-dimensional data, one explicit wavelength/channel, with no drift or
input padding. [CE06 acquisition modes](c-acquisition-modes.md) additionally
accept `AcquisitionBands`, true 2D estimation and the contracted extended
preparation modes. The equations and slicing example below describe original
`PreparedBands`; the complete CE06 contract defines its extended records and
different 2D pair/product rules. This is an array stage;
raw-file workflow composition remains separate.

```python
estimate_parameters(
    bands, transfer, *, initial_carriers_cyc_um,
    wavelength_nm, numerical_aperture, immersion_index,
    search_carriers=True, use_time0_carriers=True,
    amplitude_floors=None, fit_all_phases=True, omit_kz0=False,
) -> EstimatedParameters
```

`bands` is an accepted `PreparedBands` from `prepare_bands`. Its raw input shape
is `(T,D,P,Z,Y,X)`: time, direction, phase, z, y, x. Let O include order zero
and Q=2*O-1 be the quadrature count. T,D>=1, Z>=2, Y>=1, X>=2 even, and Q<=P.
Searching requires O>=3; known-carrier fitting requires O>=2. The native
quadratures have shape `(T,D,Q,Z,Y,X//2+1)`. Detector spacings and integer output
zooms remain those in the supplied record; no additional scale is fitted.

`transfer` is an accepted `OpticalTransfer` from `declare_otf` or
`prepare_bead_otf(...).transfer`, with at least O complete orders. Both accepted
radial and full complex layouts are supported. The table must contain every
interpolation vertex actually requested during overlap construction, including
vertices with zero interpolation weight. A source threshold can skip a later
request; zero band data alone does not waive an actual request.

Supply fundamental carriers as a real NumPy array `(D,2)`, in `(kx,ky)` order,
in cycles per micrometre (cycles/um). Do not supply highest-order vectors or
divide these values by the order count again. Signed components and unequal
direction magnitudes are permitted. These are resolved vector inputs; unequal
magnitudes need not be expressible by the historical caller's single line
spacing. Arrays may be strided or read-only. Real standard integer/float16/32/64
kinds are accepted; booleans, complex, object, string and extended precision
kinds are not. Values must be finite and within float32 component magnitude.

Wavelength is a Python/NumPy integer in nanometres, 1..32767, never a boolean.
Numerical aperture (NA) and immersion index are explicit finite real scalars,
with `1<=immersion_index<=2` and `0<NA<=min(2,immersion_index)`. Flags must be
actual booleans. See the [full contract](../contracts/c-equivalence-carrier-modulation-v1.md)
for used-record, scalar, source-index and array-representation limits.

With the defaults, each direction's carrier is searched at time zero and reused
at later times. Modulation is freshly fitted from each time's own bands; it is
never copied from time zero. Set `use_time0_carriers=False` to search every time,
always starting from the supplied initial vector. Set `search_carriers=False`
to keep the supplied carriers and fit only modulation at all times; the reuse
flag then has no numerical effect.

Search first correlates orders 0 and 2, then refines angle and magnitude once,
in that order. It preserves strict improvements/ties and the source's carried
bracket state. Overlaps are rebuilt at refinement entry and frozen throughout
that pair's search and final order-2 fit. Other positive orders get their own
overlaps at the final carrier. This procedure is not a converged optimizer or
a normalized-correlation fit. Known-carrier fitting instead builds a fresh
order-(0,b) overlap for each positive order b.

`amplitude_floors=None` disables floors. Otherwise supply a strictly positive
finite real array `(O-1,)`; no zero-as-disable element or broadcasting is
supported, and this option requires O<=25. Each floor raises only smaller
fitted magnitudes, preserving phase. Floors are applied after all fits and do
not affect the search objective. `fit_all_phases=False` then replaces each
order-b phase for b>=2 by b times the fitted order-1 phase, retaining magnitudes.
`omit_kz0=True` skips the zero axial-frequency plane during fitting.

The frozen `EstimatedParameters` record includes:

| Field | Meaning |
| --- | --- |
| `carriers_cyc_um` | read-only float64 `(T,D,2)` fitted, reused or supplied fundamental vectors |
| `modulation` | read-only complex128 `(T,D,O-1)` final factors, after floors and phase policy; order zero is implicitly one |
| `raw_modulation` | same shape, forward factors before those adjustments |
| `branches` | T-by-D immutable strings: `searched`, `known`, `time0-reused` |
| `overlaps` | separate immutable records for every build: masked Fourier arrays, spatial arrays and write masks |
| `trace` | immutable coarse peaks, regression evaluations, bracket decisions, parabolas, reuse and adjustment events |

The record also retains initial vectors, cutoffs, resolved settings and pinned
source identities. Every output array owns read-only storage. Inputs stay
unchanged, including accepted writable CE02 quadratures/noise. The operation
does not replay the raw images or make the original PreparedBands arrays
read-only.

In each regression, SX and SY are the sums of squared overlap magnitudes and
C is the sum of `conj(lower)*phase_shifted_higher`. The fitted factor is C/SX.
Trace evaluations also expose raw reverse/combined factors and the uncentered
correlation. Search evaluates `abs(C/SX)**2`; direct known-carrier fits,
including later time-zero reuse, record `objective=None` without evaluating
that square. Reverse is `conj(C)/SY`, not its reciprocal display amplitude.

Every actual regression needs finite SX>0, SY>0 and SX!=SY because the selected
source helper also evaluates a combined-factor diagnostic. Equal-energy
overlaps, including exact equal-energy unit-gain cases, are outside this domain
even when the forward factor alone is defined. No weak-signal floor or limiting
repair is added. With positive unequal energies, C=0 is permitted: the factors
and correlation are zero. A positive requested floor on a zero fitted factor
rejects. A zero order-1 factor also rejects when `fit_all_phases=False`, including
O=2, because the source evaluates its base phase before the higher-order loop.

A supplied known carrier `(0,0)` can be valid. An exactly zero coarse search
vector rejects at its undefined polar-angle conversion. A later zero/negative
magnitude returned by the defined refinement parabola is retained literally.
Failures raise `ParameterEstimationError`, a `SimreconError`/ValueError subclass,
with the offending input or operation identified. Unsafe stencils, undefined or
nonfinite arithmetic, unrepresentable source indices/arrays and allocation or
backend failures reject the whole call. There is no partial direction/time
result, silent initial-guess fallback or alternate optimizer.

Snapshots retain substantial explicit data. For native voxel count V=X*Y*Z,
one overlap build stores two complex128 arrays of shape `(2,Z,Y,X)` plus a
boolean write mask of that shape:
`(2*2*16 + 2*1)*V = 66*V bytes` of array payload. A searched time/direction
builds O records; a known or reused time/direction builds O-1. This excludes
record overhead, trace/coarse maps, other outputs and working arrays. It is
neither total memory nor a measured peak or allocation guarantee.

## Pass time-specific estimates to known-parameter reconstruction

`reconstruct_known` continues to accept `(D,2)` carriers and `(D,O-1)`
modulation, shared by all times in one call. Compose the stages one time at a
time. The following caller-side example assumes that `bands`, `transfer`,
`initial_carriers`, declared optical scalars and a valid positive `wiener` are
already available. It supplies no synthetic data or observed numerical result.

```python
import numpy as np
from simrecon import PreparedBands, estimate_parameters, reconstruct_known

optics = dict(
    wavelength_nm=wavelength_nm,
    numerical_aperture=numerical_aperture,
    immersion_index=immersion_index,
)
estimate = estimate_parameters(
    bands, transfer,
    initial_carriers_cyc_um=initial_carriers,
    **optics,
)

reconstructions = []
for t in range(bands.input_shape[0]):
    one_time = PreparedBands(
        quadratures=bands.quadratures[t:t + 1].copy(),
        noise_variance_factors=bands.noise_variance_factors.copy(),
        separation_matrices=bands.separation_matrices.copy(),
        phase_angles_rad=bands.phase_angles_rad.copy(),
        frame_sums=bands.frame_sums[t:t + 1].copy(),
        equalization_gains=bands.equalization_gains[t:t + 1].copy(),
        background_after=bands.background_after.copy(),
        slope_after=bands.slope_after.copy(),
        sentinel_frames=tuple(
            (0, d, z, p)
            for old_t, d, z, p in bands.sentinel_frames
            if old_t == t
        ),
        input_shape=(1, *bands.input_shape[1:]),
        input_scale=bands.input_scale,
        dxy_um=bands.dxy_um,
        dz_um=bands.dz_um,
        lateral_zoom=bands.lateral_zoom,
        axial_zoom=bands.axial_zoom,
        edge_pixels=bands.edge_pixels,
        equalize=bands.equalize,
        equalize_z=bands.equalize_z,
        equalize_time=bands.equalize_time,
        phase_policy=bands.phase_policy,
        source_revision=bands.source_revision,
        reference_sha256=bands.reference_sha256,
    )
    reconstructions.append(reconstruct_known(
        one_time, transfer,
        carriers_cyc_um=estimate.carriers_cyc_um[t],
        modulation=estimate.modulation[t],
        wiener=wiener,
        **optics,
    ))

image = np.concatenate([r.image for r in reconstructions], axis=0)
```

This constructs public value records from the contracted fields. It does not
assume a dataclass-specific replacement protocol. Only time-dependent arrays
are sliced; sentinel events select the original time and relabel it zero.
The upstream scale remains `1/(X*Y*Z*L**2*A*D)`, where L and A are lateral
and axial zoom. It is independent of T. Slicing must not rerun equalization,
rescale bands or change the time-zero equalization reference already used.

Each reconstruction image has shape `(1,A*Z,L*Y,L*X)`; the concatenated array
has shape `(T,A*Z,L*Y,L*X)`. Coordinates come from each reconstruction's
`x_um`, `y_um`, `z_um` fields, with spacings dxy/L, dxy/L, dz/A. Images retain
signed samples. Concatenation creates an ordinary new NumPy array; the individual
reconstruction output arrays retain their read-only contract.

Successful estimation does not guarantee reconstruction acceptance. The result
must also satisfy [CE04's parameter, optical-angle, filtering, representation
and actual-stencil domain](../contracts/c-equivalence-known-parameters-v1.md).
Do not clip, refit or rescale estimates to force acceptance. The example uses
default estimator and filter flags; choose any nondefault options explicitly
at the appropriate stage. Neither this stage nor its composition establishes
historical executable agreement, physical image recovery or recovered
resolution. Retired scientific APIs remain unavailable.
