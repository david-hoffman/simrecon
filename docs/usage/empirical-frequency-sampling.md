# Sample empirical transfer at physical frequencies

`sample_empirical_volume_transfer` evaluates one signed order of a calibrated
complex response at caller-supplied z/y/x frequency triples, in cycles per
micrometre (cycles/µm). Use it when you already know which physical transfer
coordinates you need. It preserves relative complex amplitudes and phase.

Supply an `EmpiricalVolumeResponse` for one orientation, channel and time. The
[raw point-bead calibration guide](raw-point-bead-calibration.md) explains the
upstream declaration, supplied camera correction and known-phase calibration.
The caller must establish matching effective response, axis directions and
focal-plane model for calibration and specimen. Labels and valid geometry do
not establish that physical match.

This complete algebraic example can be run as Python. It uses a deliberately
asymmetric response to show the coordinate and signed-order conventions; it
makes no optical calibration claim.

```python
import numpy as np
from simrecon import EmpiricalVolumeResponse, sample_empirical_volume_transfer

# Two samples per axis, spaced by 0.5 µm: ideal frequency nodes are -1 and 0.
axis = np.array([-1.0, 0.0], dtype=np.float64)
z, y, x = np.meshgrid(axis, axis, axis, indexing="ij")
real = 1.0 + z / 8 + y / 4 + x / 2
values = np.stack([real + 1j * (m / 8 + z * y / 16) for m in range(3)])
response = EmpiricalVolumeResponse(
    values=values,
    fz_per_um=axis.copy(),
    fy_per_um=axis.copy(),
    fx_per_um=axis.copy(),
    voxel_size_um=(0.5, 0.5, 0.5),
    origin_zyx=(0, 1, 0),
)
points = np.array(
    [[0.25, 0.5, 0.75], [0.0, -0.0, 0.0], [0.25, 0.5, 0.75]],
    dtype=np.float64,
)
sampled = sample_empirical_volume_transfer(
    response,
    order=-1,
    frequencies_zyx_per_um=points,
    calibration_carrier_bins=(1, 0),
    coordinate_offset_yx=(0, 0),
    phase_reference_shift_rad=0.2,
    source="declared algebraic coordinate pairing",
)
print(sampled.values)
print(sampled.frequencies_zyx_per_um)
```

All six keyword arguments are required. Orders are nonboolean Python or NumPy
integers from −2 to +2. Queries must be a plain finite float64-width NumPy array
of shape `(P,3)`, with at least one point. Either byte order, strided, reversed,
Fortran and read-only arrays are accepted. Queries can be non-Cartesian,
unsorted or repeated. Point order and signed-zero coordinate bits are retained.

## Exact coordinates and closed coverage

Every binary64 query component means its exact represented real value. Source
nodes are the exact rationals `k/(N*d)`, using the converted binary64 spacing
`d` in µm and centered modes `k = -floor(N/2), …, ceil(N/2)-1`. Tolerated rounding
in the response's frequency metadata does not move those nodes. There is no
snapping tolerance.

For example, with `N=3` and `d=1 µm`, binary64 rounding of `1/3 cycles/µm` lies
slightly inside the upper endpoint. It is interpolated, not copied as an exact
node. With `N=5`, binary64 rounding of `2/5 cycles/µm` lies slightly outside the
upper endpoint and rejects. Moving that positive value one representable step
toward zero produces an in-hull request. For arbitrary endpoints, establish the
side of rounding using exact rational geometry; moving outward rejects. The
[ideal-grid adapter](empirical-trilinear-transfer.md) accepts ideal target-grid
geometry directly when that is the intended request. Rounded coordinate lists
and ideal-grid requests carry different meanings and have no general bitwise
equivalence guarantee.

Order `m >= 0` evaluates row `m` at `f`. A negative order evaluates row `abs(m)`
at `-f` on **all three axes**, applies the positive-order gauge, then conjugates.
Only those evaluated coordinates must lie in the closed source hull. A
singleton source axis covers exactly zero. Endpoints use their endpoint sample
without a nonexistent neighbor. One uncovered coordinate rejects the entire
call with `incomplete_empirical_transfer_coverage`, including when source
values are zero. Coverage describes available interpolation data; it supplies
no optical support mask. In-hull zeros and cancellation remain data.

On an even axis the stored canonical negative Nyquist endpoint has no positive
duplicate. A positive physical endpoint may therefore reject for a positive
order and succeed for a negative order after reflection. The negative-order
domain is the reflected positive-order hull. Existing reconstruction consumers
use modular negation at even Nyquist. This point sampler does not change that
representation or provide a direct substitute there.

## Interpolation and phase declarations

Real and imaginary components share the same trilinear weights. Within a cell,
those nonnegative tensor weights sum to one. This interpolates complex
Cartesian components, retaining arbitrary signed and non-Hermitian source
values. There is no magnitude/phase interpolation, second centering,
normalization, gain, extra side-order factor, bead correction or voxel-volume
factor.

For positive order `m`, the gauge is

\[
\rho= k_{c,y}(b_y+o_y)/N_y + k_{c,x}(b_x+o_x)/N_x,
\qquad F_m(f)=I_m(f)\exp[-i m(2\pi\rho+\delta)].
\]

Here `I` is the interpolant, `b` is the observed source origin, `o` is
`coordinate_offset_yx` in source calibration samples, and `delta` is
`phase_reference_shift_rad` in radians: specimen separation reference minus
calibration separation reference. Integer carriers and offsets retain exact
Python integer meaning, including huge declarations. Rational `rho` is reduced
modulo one before angle evaluation. Huge finite phase shifts are valid.

Declare the gauge once. The response is already centered. A joint storage roll
requires the opposite change in the coordinate offset when illumination
coordinates stay fixed. A physical bead move has its own illumination phase.
The common normalization and relative gains remain; upstream common brightness
scale is already discarded. A downstream gain belongs to its own operation and
must also be applied once.

For overlap calculations, construct order-zero queries at object frequency
`f` and signed-order queries at detector frequency `f + m*q`, with lateral
physical carrier `q` and zero axial carrier. The calibration carrier above
selects only the gauge. It imposes no equality to a specimen carrier inferred
from query points. Detector observations at the corresponding coordinates need
their own sampling contract. This function supplies neither observation
interpolation nor a carrier, phase, gain or drift estimator.

## Ownership, errors and precision

The returned `EmpiricalFrequencySamples` has five frozen bindings: `values`,
`frequencies_zyx_per_um`, `order`, `source` and `provenance`. Values are an owned
mutable native C-contiguous complex128 vector; coordinates are an independently
owned mutable native C-contiguous float64 `(P,3)` snapshot. Inputs, other outputs
and other calls share no array storage. Direct record construction performs no
validation or deep freeze. Concurrent input mutation is outside the guarantee.

`provenance` is an independent mutable plain dictionary, read-only by
convention. Its seven entries record the sampling method, source shape,
converted source spacing, observed source origin, calibration carrier,
coordinate offset and converted phase shift. Keep raw acquisition, correction,
calibration identities and the physical pairing externally. `source` is an
unchanged nonblank opaque label, without authentication.

Every source field and sample is validated, including unused rows and points.
Invalid input raises `SimreconError` with the boundary-specific codes in the
[public contract](../contracts/empirical-frequency-sampling-v1.md). Computed
nonfinite final components reject the whole call with
`unrepresentable_empirical_interpolation`. Allocation failures and unrelated
exceptions propagate. Caller arrays, NumPy error settings and warning policy
are preserved. There is no practical-size or throughput guarantee.

At complete exact source nodes, order-zero components copy bit for bit. When
`rho` is integral and converted `delta` is either signed zero, positive orders
also copy bits; negative orders retain real bits and toggle the imaginary sign
bit. Other computed values have no signed-zero promise. Safe component
arithmetic handles overflowing complex magnitudes and tiny weights without
rejecting safely finite final components solely because of those intermediates.
Range decisions close to maximum binary64 can depend on roundoff.

The absolute dimensionless arithmetic allowance is
`Delta = 1024*2^-52*L + 64*2^-1074`, where `L` is the weighted sum of source
`abs(real)+abs(imag)` evaluated without observer overflow or underflow. It is
separate from interpolation/model error, upstream calibration error, physical
mismatch and downstream estimator bias. Barring actual dependency/allocation
failure, success is required when every exact final component satisfies
`abs(component) + Delta < Fmax`, where `Fmax` is maximum binary64. This is a
sufficient-success condition, not an input rejection threshold; other valid
calls still attempt computation. Multi-affine functions are reproduced
by the exact interpolant. For a declared twice-differentiable comparison `H`,
a cell bound is `sum_a h_a^2 * sup(abs(partial_aa H))/8`. Convex interpolation
amplifies bounded source error by at most the largest stencil source error.
Neither bound establishes physical truth.

Two small examples were executed and retained locally with generators, arrays,
identities and error budgets. They are ignored evaluator artifacts, not shipped
example programs. Twenty asymmetric multi-affine comparisons had maximum
arithmetic error `1.04e-16`, with zero model/calibration error. Twenty raw-bead
comparisons used a declared smooth finite Fourier polynomial, distinct physical
queries and known phases/carrier. Maximum arithmetic error was `9.51e-17`;
maximum calibration contribution at the queries was `2.30e-16` against a
`1.83e-9` conservative upstream budget. Maximum interpolation/model error was
`0.140`; every point met its per-order cell bound, at most `0.489`. These are
measured dimensionless results for those examples. Finite discrete calibration
is not an exact arbitrary continuous physical response. No experimental
validity or unknown-parameter recovery follows.
