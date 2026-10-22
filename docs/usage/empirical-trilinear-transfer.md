# Empirical transfers on a different Cartesian grid

`adapt_empirical_volume_response_trilinear` interpolates a centered empirical
volume response onto an explicitly declared specimen grid. It interpolates real
and imaginary components with the same trilinear weights. It then removes the
declared bead-location phase and applies the specimen phase reference once.
The result contains orders 0,+1,+2 for `reconstruct_volume`.

The caller assumes that calibration and specimen share the same effective
response at common physical frequencies, axis directions and focal-plane model.
Matching geometry cannot establish that physical assumption. This operation
estimates no carrier, phase, gain, bead size or instrument setting.

## Declare the pairing

All seven keywords are required. Here `calibrated` is a
`PointBeadCalibration` returned by `calibrate_raw_point_bead`:

```python
from simrecon import adapt_empirical_volume_response_trilinear

adapted = adapt_empirical_volume_response_trilinear(
    calibrated.response,
    target_shape_zyx=(3, 3, 3),
    target_voxel_size_um=(1.0, 2.5, 2.5),
    calibration_carrier_bins=(2, 0),
    specimen_carrier_bins=(3, 0),
    coordinate_offset_yx=(1, -1),
    phase_reference_shift_rad=0.625,
    source="declared four-site smooth comparison; known point bead and phases",
)
orders = adapted.orders
```

The executed raw example below uses calibration dimensions `(3,5,5)`, spacing
`(0.5,1,1)` µm and observed bead origin `(1,1,2)`. Its lateral carrier is
`2/(5*1) = 3/(3*2.5) = 0.4` cycles/µm along y and zero along x.
Carrier equality uses exact represented spacings and exact integers, without
wrapping or a floating tolerance. Offsets are in **source calibration samples**:
source index plus offset gives the common illumination coordinate. They describe
neither specimen drift nor a target bead. Target index zero declares common zero.

The phase declaration is specimen minus calibration separation reference.
For this example it is `0.375 - (-0.25) = 0.625` rad. The constant gauge is

```text
rho = 2*(1+1)/5 + 0*(2-1)/5 = 4/5 cycles
F_m = interpolated(E_m) * exp(-i*m*(2*pi*rho + 0.625)), m=1,2.
```

Order zero has no gauge rotation. Source values are already centered; the
adapter adds no frequency-dependent origin phase. It preserves common relative
order scale. The reconstruction gain remains a separate required declaration.
Actual exposure phase schedules must be supplied to calibration/reconstruction;
a reference shift cannot replace them.

## Geometry and numerical limits

Each target dimension must be positive and **odd**. Singleton axes are allowed.
Source dimensions may be even. The odd-target rule makes physical frequency
negation agree with the consumer's modular negative-order construction.
An even target rejects with `unsupported_empirical_interpolation_target_nyquist`.
Existing adapters retain their own even-grid behavior.

Every ideal target coordinate `k/(N*d)`, in cycles/µm, must lie in the closed
source frequency interval on every axis. A singleton source covers only zero;
a singleton target requests only zero at any valid positive spacing. Closed
endpoints need only their endpoint sample. Missing coverage raises
`incomplete_empirical_transfer_coverage`, including for zero-valued transfers.
There is no extrapolation, endpoint bridge, wrapping, clipping or support mask.

Converted binary64 spacings define exact rational geometry. Stored source axes
are validated within the contract's metadata tolerance; their rounding never
selects a bracket or a shared node. Returned axes are correctly rounded binary64
coordinates with positive zero at DC (the zero-frequency component). A frequency
that overflows, collapses or rounds to zero off DC rejects with
`unrepresentable_otf_frequencies`. An overflowing intermediate period alone
cannot reject a representable coordinate.

Arbitrary finite complex source components are valid, including non-Hermitian
responses, negative values, cancellation, zero rows and zero/nonunit order-zero
DC. No magnitude interpolation, radial average, positivity constraint,
normalization, extra side-order factor, voxel-volume factor or transform occurs.
Exact complete source nodes copy order-zero component bits. Integral `rho` and
either signed-zero reference shift copy all orders' component bits at those nodes.
All-zero local stencils give exact complex zero, allowing either zero sign.

The [numerical contract](../contracts/empirical-trilinear-transfer-v1.md) defines
the absolute arithmetic allowance `1024*eps*L + 64*q`, where `eps=2^-52`,
`q=2^-1074`, and `L` is the weighted sum of source absolute real and imaginary
components. This covers numerical computation, independently of interpolation's
approximation to a continuous response. Tiny weights must retain meaningful
weighted contributions. Intermediate complex magnitude or rotation range does
not by itself imply failure; nonfinite computed final components reject with
`unrepresentable_empirical_interpolation`. No practical size or speed guarantee
is made; ordinary allocation failures propagate.

## Executed analytic comparison

The first example uses source dimensions `(4,4,4)` at `(0.5,0.25,1)` µm and target
`(3,5,3)` at `(1,0.5,2)` µm. Let `(z,y,x)` denote physical frequencies in
cycles/µm. For order `m`, it independently declares

```text
Re H_m = (m+1)*(1+2z-3y+x+zy-2zx+3yx+zyx)/16
Im H_m = (m-1+z+2y-4x+2zy-zx+yx+2zyx)/32.
```

These functions are multi-affine: linear in each axis while holding the other
axes fixed. Their source values are exactly representable binary64 components.
Direct rational target evaluation followed by a 90-digit decimal phase
calculation supplies independent expectations. Carriers `(2,-2)` and `(5,-3)`,
source origin `(1,2,1)`, offset `(0,2)` and reference shift `0.37` rad exercise
independent geometry and a nonzero gauge. Maximum complex absolute arithmetic
error was **1.20e-16**, also the error against the analytic target function.
This measures arithmetic on this example, rather than accuracy of an optical model.

## Executed raw bead to specimen comparison

The second example declares the smooth continuous comparison

```text
H(f) = 5/8 + (3/16)*exp(-2*pi*i*fz*0.5 µm)
           + (1/8)*exp(-2*pi*i*fy*1 µm)
           + (1/16)*exp(-2*pi*i*fx*1 µm)
g0 = 1; g1 = 1/8+i/16; g2 = -1/32+3i/64.
```

These four masses define a finite synthetic point-response kernel, not measured
optics. Bead observations use brightness 48 electron, offset 13 count and response
2.5 count/electron. Their seven unequal actual phases differ from the specimen's
eight unequal phases. Both nominal command schedules are deliberately all zero.
The source origin, offsets, carriers, reference difference and grids are those
in the pairing above. Calibration uses `theta_calibration - 0.25` rad; specimen
reconstruction uses `theta_specimen + 0.375` rad.

The public composition is explicit:

```python
import numpy as np
from simrecon import (
    calibrate_raw_point_bead, correct_linear_response,
    declare_acquisition, reconstruct_volume,
)

beads = declare_acquisition(
    bead_raw,  # (1, 7, 3, 5, 5), count; independently synthesized observations
    config={
        "version": 1, "acquisition_kind": "sim_beads",
        "axes": ["orientation", "phase", "z", "y", "x"],
        "intensity_unit": "count", "nominal_phases_rad": [[0.0]*7],
    },
)
calibrated = calibrate_raw_point_bead(
    beads, group={"orientation": 0}, offset=13, response=2.5,
    output_unit="electron", phases_rad=theta_calibration - 0.25,
    voxel_size_um=(0.5, 1.0, 1.0),
)
# Construct adapted from calibrated using the pairing call above.
specimen = declare_acquisition(
    specimen_raw,  # (1, 8, 3, 3, 3), count; a separate synthetic specimen
    config={
        "version": 1, "acquisition_kind": "specimen_sim",
        "axes": ["orientation", "phase", "z", "y", "x"],
        "intensity_unit": "count", "nominal_phases_rad": [[0.0]*8],
    },
)
corrected = correct_linear_response(
    specimen, offset=7, response=1.75, output_unit="electron",
)
result = reconstruct_volume(
    corrected.data, order_otfs=[adapted.orders],
    phases_rad=(theta_specimen + 0.375)[None],
    carriers_bins=np.array([[3, 0]], dtype=np.int64), gains=np.array([1.25]),
    regularization=0.2, output_shape_yx=(15, 3), apodization=np.ones((3, 15, 3)),
)
```

Specimen observations come from separately evaluated continuous transfers and
known supported object coefficients, followed by direct finite Fourier sums.
No production output generates expected values. The comparison independently
contracts decimal cardinal-hat matrices for interpolation and sums all five
signed orders for the ridge estimator. The output window contains every relocated
band; chosen object modes avoid aliasing. Ridge strength is 0.2 in squared-transfer
units, gain is 1.25, and apodization is one.

| Separate measurement | Maximum complex absolute error |
|---|---:|
| Calibration against independent source response | 1.92e-16 |
| Adapter arithmetic on stored calibrated samples | 7.42e-17 |
| Held-out transfer interpolation, 26 target points | 0.1241 |
| Downstream spectrum change due to interpolation model | 0.002049 |
| Ridge bias with the continuous comparison transfer | 0.1551 |

The first two figures above will vary slightly with the platform's numerical
libraries. The retained results file gives the exact observed values. Numerical
agreement with the independently evaluated estimator does not remove interpolation
error or ridge bias. This finite, noiseless development comparison supplies no
experimental parity, finite-bead correction or exact physical recovery claim.

The executed generation script and evidence are retained locally at
`artifacts/independent-otf-offgrid-20261015/C01/examples/generate.py` and
`artifacts/independent-otf-offgrid-20261015/C01/examples/results.json`, with small
raw, calibration, expected and returned arrays, decimal expectations and composition
provenance in the same directory. These are ignored local validation artifacts;
they are not included in a fresh checkout or the repository's GitHub view.
In the retained validation workspace only, rerun from its project root:

```sh
.venv/bin/python artifacts/independent-otf-offgrid-20261015/C01/examples/generate.py
```

## Retain provenance and respect ownership

`adapted` has frozen bindings `orders` and `provenance`. Its arrays and plain
provenance dictionary remain mutable, independently owned and unaliased to caller
storage or another call. Direct record construction performs no validation.
The dictionary contains exactly: `sampling`, `source_shape_zyx`,
`source_voxel_size_um`, `source_origin_zyx`, `calibration_carrier_bins`,
`specimen_carrier_bins`, `coordinate_offset_yx`, `phase_reference_shift_rad`.
The sampling label is `complex_cartesian_trilinear_v1`. `orders.origin_zyx` is
`(0,0,0)` and `orders.source` retains the caller's opaque string unchanged.

Keep upstream raw acquisitions, correction coefficients/units, actual phase
schedules, calibration identities and physical pairing evidence externally.
These declarations prove no physical pairing or absolute throughput. Common
calibration brightness was discarded upstream. Caller inputs, layouts, write
flags and numerical warning/error policy remain unchanged on success or rejection.
