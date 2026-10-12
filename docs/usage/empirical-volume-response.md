# Empirical bead-referenced volume responses

`prepare_empirical_volume_response` takes already separated observations for one
orientation/channel/time. It finds the sole positive maximum of converted `dc`,
rolls all three volumes by that observed origin, and divides their signed discrete
Fourier transforms (DFTs) by the **exact sum of converted dc samples**. See the
[binding contract](../contracts/empirical-volume-response-v1.md).

The result contains dimensionless complex `values` in order `0,+1,+2`, followed by
full centered z/y/x frequency axes. Frequencies are in cycles/µm. Only zero-order
DC is fixed to exactly `1+0j`; the rest of that volume retains its measured shape.
Side orders keep their relative complex gain, including zero DC and zero rows.
Bindings are frozen; the four independently owned arrays remain writable.

Run each example from the repository root with the existing environment:

```sh
.venv/bin/python example.py
```

Save either block below as `example.py`. No files are written by the primitive.

## Signed asymmetric observations

```python
import numpy as np
from simrecon import prepare_empirical_volume_response

j = np.arange(24, dtype=np.float64).reshape(2, 3, 4)
dc = (j % 5 - 2) / 8
dc[-1, 0, -1] = 8
c1 = (j - 7) / 16 + 1j * ((j * 3 % 11) - 5) / 8
c2 = ((j * 7 % 13) - 6) / 4 + 1j * (j - 12) / 32
response = prepare_empirical_volume_response(
    dc, c1=c1, c2=c2, voxel_size_um=(0.25, 0.125, 0.5)
)
print(response.origin_zyx)              # (1, 0, 3), observed from dc
print(response.values.shape)           # (3, 2, 3, 4)
print(response.values[0, 1, 1, 2])      # (1+0j), zero-order DC
print(response.fx_per_um)              # [-1.  -0.5  0.   0.5]
```

The exact stored dc mass is `S=8`. Independently enumerate signed modes
`k_a=j_a-floor(N_a/2)` and sum
`(a_m[n]/S)*exp(-2πi*sum_a k_a*(n_a-b_hat_a)/N_a)` over every sample.
For this example the full-array maximum complex errors and project budgets were:

| Order | Maximum error | Absolute budget |
|---|---:|---:|
| 0 | 7.39 × 10⁻¹⁸ | 3.84 × 10⁻¹² |
| +1 | 3.42 × 10⁻¹⁷ | 6.35 × 10⁻¹² |
| +2 | 1.41 × 10⁻¹⁶ | 8.19 × 10⁻¹² |

Expectations used exact binary64 sample ratios and 120-digit roots, independently
of production transforms. The budget is
`512*M*2^-52*sum(abs(real(a))+abs(imag(a)))/S + 16*M*2^-1074`, with `M=24`.
It is an absolute numerical acceptance bound, not a physical accuracy claim.

## Declared counts through correction and known-phase separation

This is an on-grid point bead in the
[selected finite periodic synthetic model](../models/synthetic-3d-acquisition-v1.md).
The asymmetric detection weights sum to `512`; `h=weights/512` has unit mass
and a unique peak at zero displacement. Brightness `B=64 electrons` gives
`sum(dc)=64 electrons`. The declared camera relation is
`raw=10 counts+(2 counts/electron)*signal`.

```python
import numpy as np
from simrecon import (
    correct_linear_response,
    declare_acquisition,
    prepare_empirical_volume_response,
    separate_volume_phases,
)

spacing = (0.25, 0.125, 0.5)  # dz, dy, dx in µm
h = np.arange(1, 25, dtype=np.float64).reshape(2, 3, 4)
h[0, 0, 0] = 213
h /= 512
bead = (1, 2, 1)  # generator/comparison truth only
g1 = (2 / 3) * np.array([1, -1])[:, None, None]
g2 = 1 / 3
# Integer lateral mode qx=1/(4*dx); illumination at this bead has phase π/2.
gauge = (1 + 0j, 1j, -1 + 0j, -1j)[bead[2]]
dc = 64 * np.roll(h, bead, axis=(0, 1, 2))
c1 = 64 * np.roll(h * g1, bead, axis=(0, 1, 2)) * gauge
c2 = 64 * np.roll(h * g2, bead, axis=(0, 1, 2)) * gauge**2
actual_phases = 2 * np.pi * np.arange(7) / 7
c, s = np.cos(actual_phases), np.sin(actual_phases)
signal = np.stack([
    dc + 2 * c1.real * cp - 2 * c1.imag * sp
    + 2 * c2.real * (cp * cp - sp * sp)
    - 2 * c2.imag * ((2 * cp) * sp)
    for cp, sp in zip(c, s, strict=True)
])
nominal_commands = actual_phases + np.array([0, .2, -.1, .3, -.2, .1, -.15])
raw = 10 + 2 * signal
acquisition = declare_acquisition(raw[None], config={
    "version": 1,
    "acquisition_kind": "sim_beads",
    "axes": ["orientation", "phase", "z", "y", "x"],
    "sampling_um": dict(zip(("z", "y", "x"), spacing, strict=True)),
    "intensity_unit": "count",
    "nominal_phases_rad": [nominal_commands.tolist()],
})
corrected = correct_linear_response(
    acquisition, offset=10, response=2, output_unit="electron"
)
observed = separate_volume_phases(corrected.data[0], phases_rad=actual_phases)
response = prepare_empirical_volume_response(
    observed.dc, c1=observed.c1, c2=observed.c2, voxel_size_um=spacing
)
print(response.origin_zyx)         # (1, 2, 1), from observed dc
print(response.values[0, 1, 1, 2]) # (1+0j)
```

Raw declaration (R1) preserves explicit layout and commands. Supplied linear
response correction (R2) produces electrons. The separator receives the **actual
known phases**, independently of nominal commands. None of `b`, `h`, `g`, `q` or
`B` is a response input. They generate and independently assess this example.

Exact rational normal equations on the represented phase matrix independently
check the separated observations. The maximum coordinate error was
`3.15 × 10^-15 electrons`, below `9.83 × 10^-10 electrons`. The generator peak
margin was `23.625 electrons`, exceeding twice the bounded zero-order perturbation.
Complete signed response errors for orders `0,+1,+2` were respectively
`1.12 × 10^-16`, `8.10 × 10^-17`, `8.80 × 10^-17`. Conservative propagated budgets
were `7.41 × 10^-10`, `7.70 × 10^-10`, `6.46 × 10^-10` (rounded upward).
Using commands as phases instead changed `c1` by up to `1.238 electrons`.

For propagation, let `e0` bound each zero-order sample error and `em` each complex
order sample error. Then `dS=M*e0<S`, and the normalized response perturbation is
bounded by `(M*em+abs(E_m)*dS)/(S-dS)`. Add the primitive budget using an upper
bound on observed absolute sample mass. Retained comparisons check each bin,
not only the maxima reported here.

## Gauge and interpretation

Jointly rolling all supplied components shifts the observed origin and preserves
the centered responses. Physically moving the synthetic bead from `(1,2,1)` to
`(0,0,2)` changes its lateral illumination phase: first order multiplies by `i`,
second order by `-1`; zero order is preserved. The executed comparison confirmed
those relations within propagated budgets. A separation phase-origin change
`phi'=phi+alpha` instead multiplies order `m` by `exp(-i*m*alpha)`.
The `alpha=π/2` comparison used gains `1,-i,-1`.

Negative orders obey `E_-m(k)=conj(E_m(-k))`, with modular frequency negation on
all three axes. Even negative Nyquist bins negate to themselves. Array reversal
and same-bin conjugation do not implement this identity generally.

The finite periodic native grid, point bead, identity bead-size compensation and
`g0=1` are model assumptions. The full zero-order response still contains the
measured detection shape. Common intensity normalization discards brightness
scale; absolute bead brightness and throughput cannot be identified separately.
The retained bead and separation phase gauge is also inseparable from measured
side responses. This record provides no direct interchangeability with a
supplied-profile optical transfer function (OTF) or reconstruction guarantee.
Finite beads, unknown phases/drift, other grids and instrument calibration need
separate contracts.

Execution evidence is retained locally under ignored
`artifacts/empirical-signed-response-20261010/C01/`: `examples.py` reproduces both
examples, physical movement, joint roll and phase-origin comparisons;
`example-manifest.json` hashes complete input/output arrays, 120-digit signed
expectations/errors/budgets and gauge evidence. The observations, declarations,
software identity and model choice are caller evidence. The runtime adds no
I/O, hashing, persistence or provenance promise. It owns full snapshots, scratch,
outputs and exact arithmetic bookkeeping, with no streaming or resource bound.
