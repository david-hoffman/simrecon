# Diagnose known-phase volume carriers

`scan_volume_carriers` reports a free complex gain, direct normalized residual
and amplitude correlation for each caller-listed integer carrier. It preserves
caller order and duplicates. It does not select a physical carrier.

Supply one orientation/channel/time as `(phase,z,y,x)` images, actual known
fundamental phases in radians, a fixed `EmpiricalVolumeResponse`, specimen
z/y/x spacing in micrometres (µm), and all nine keyword declarations. The
response has six fields; the separate required `source` label is opaque caller
provenance. The caller establishes calibration/specimen compatibility.

This complete algebraic example runs from the repository environment:

```python
import numpy as np
from simrecon import EmpiricalVolumeResponse, scan_volume_carriers

phases = np.array([0.0, 0.37, 1.2, 2.4, 3.6, 4.7, 5.9])
c, s = np.cos(phases), np.sin(phases)
h = np.column_stack((np.ones(7), c, s, c*c-s*s, (2*c)*s))
grid = np.arange(6.0).reshape(1, 2, 3)
coefficients = np.stack((2+grid/8, 1+grid/17, -grid/13,
                         grid/19, 0.2+grid/23))
images = (h @ coefficients.reshape(5, -1)).reshape(7, 1, 2, 3)
z_axis = np.array([0.0])
lateral_axis = np.array([-2.0, 0.0, 2.0])
z, y, x = np.meshgrid(z_axis, lateral_axis, lateral_axis, indexing="ij")
values = np.stack([(1+m/4+y/16+x/32) + 1j*(m/8+y*x/64)
                   for m in range(3)])
response = EmpiricalVolumeResponse(values, z_axis, lateral_axis.copy(),
                                   lateral_axis.copy(), (1.0, 1/6, 1/6), (0, 1, 1))
for order in (1, 2):
    rows = scan_volume_carriers(
        images, response=response, voxel_size_um=(2.0, 1.0, 0.5),
        phase_steps_rad=phases,
        candidate_carriers_yx=[(0, 0), (0, 1), (0, 0), (0, 30)],
        order=order, calibration_carrier_bins=(1, -1),
        coordinate_offset_yx=(1, 0), phase_reference_shift_rad=0.23,
        source="declared algebraic pairing",
    )
    for row in rows:
        print(order, row.carrier_bins_yx, row.status, row.overlap_count,
              row.gain, row.relative_residual, row.coherence)
```

The response and calibration gauge stay fixed across every row. The calibration
carrier need not equal any trial carrier. Offsets use source calibration
samples. The phase shift is specimen separation reference minus calibration
reference. Apply that constant gauge once. Second-order fits use the same
fundamental phase schedule, not doubled steps.

For a trial `k=(ky,kx)` and selected order `m`, include every canonical specimen
frequency pair `p,j=p+(0,m*ky,m*kx)` inside the finite window. There is no wrap.
The pair count is `Nz*max(Ny-abs(m*ky),0)*max(Nx-abs(m*kx),0)`. Each physical
coordinate is separately correctly rounded from exact `bin/(N*d)`; adding
rounded carrier increments can give a different query. Source metadata rounding
does not move the exact interpolation hull. Even a matching grid can have a
rounded endpoint just outside that hull.

Using normalized negative-exponent discrete Fourier coefficients, the fit is

\[
x_p=F_m(f(j))D_0(p),\quad y_p=F_0(f(p))D_m(j),\quad
\beta=\frac{\sum_p\overline{x_p}y_p}{\sum_p|x_p|^2}.
\]

All pairs enter, including DC and zero weights. No transfer division, optical
support inference, extra side factor or voxel-volume factor applies. Scaled
arithmetic retains separate operand scales. It computes correlation from unit
vectors and residual directly as `norm(v-c*u)`. Raw product or norm-ratio
overflow alone does not justify rejecting safely finite final gain components.

| Status | Meaning | Gain / residual / coherence |
|---|---|---|
| `no_overlap` | No geometric pairs | All `None` |
| `incomplete_coverage` | At least one required physical query is uncovered | All `None` |
| `zero_predictor` | Complete coverage, computed predictor norm zero | All `None` |
| `zero_response` | Nonzero predictor, computed response norm zero | `0j / 0.0 / 0.0` |
| `zero_correlation` | Nonzero norms, computed complex correlation zero | `0j / 1.0 / 0.0` |
| `fitted` | Nonzero computed correlation | Finite scalars; gain may underflow to zero |

Every row retains the full pair count. Missing coverage never drops pairs.
Invalid inputs, inherited phase errors, FFT failures, unrepresentable
interpolation and nonfinite fitting reject the whole call. All fields are
validated even for an all-absent candidate table. Input snapshots preserve
caller storage and floating/warning policy. Result bindings are frozen;
direct construction performs no validation. There is no practical-size or
throughput guarantee.

The [public contract](../contracts/volume-carrier-diagnostics-v1.md) defines
stable error codes and the combined stored-input arithmetic allowances. Its
informative conditions and sufficient-success margins are guarantees, not
energy, conditioning or gain rejection thresholds. Calibration uncertainty,
query/interpolation/model mismatch, physical mismatch and sampling aliases
remain separate from arithmetic error.

Two retained C01 examples exercise asymmetric multi-affine source responses on
distinct anisotropic grids and public raw declaration/correction/known-phase
point-bead calibration followed by a corrected specimen scan. Their independent
stored-input least-squares, finite Fourier, rational interpolation and regression
expectations, raw/expected/returned arrays, budgets and measured errors live in
`artifacts/volume-carrier-diagnostics-20261016/C01/examples/`. The closed manifest
and generation association identify the actual dirty generation inputs; later
candidate admission belongs to the coordinator. The guide's exact code block
is also executed separately there.

A one-pair fit can have perfect correlation for multiple distinct candidates.
Sparse objects and different overlap regions can mislead. Sampled illumination
aliases `k` and `k+t*N`; second-order-only data on even axes can also alias
`k` and `k+N/2`. This diagnostic does not resolve them. Known actual phases and
calibration declarations are legitimate only within this intermediate model;
this is not a complete truth-hidden workflow, physical recovery, continuous
optics validation, reconstruction or experimental/reference parity claim.
