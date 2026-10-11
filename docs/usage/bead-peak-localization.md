# Bead grid-peak localization

`locate_bead_peak(volume)` returns the sole positive global maximum of a
real observed volume, in logical z/y/x order. This is the partial C1 integer
origin foundation defined by the [contract](../contracts/bead-peak-localization-v1.md).
The [selected synthetic model](../models/synthetic-3d-acquisition-v1.md) supplies
development assumptions; it supplies no measured instrument settings.

The locator accepts a plain NumPy integer or floating ndarray with three positive
dimensions. It snapshots the volume as native float64 and checks both source and
converted samples for finiteness. It accepts signed samples, positive subnormals,
singleton axes, edge peaks, unequal secondary maxima, read-only and strided arrays.
The frozen `BeadPeak` contains only `index_zyx` (three built-in integers) and `value`
(a built-in float in the supplied intensity unit). It retains no array storage.
Direct record construction is unvalidated.

Selection uses exact converted sample equality. Multiple equal positive global
maxima raise `SimreconError` with code `ambiguous_bead_peak`; a nonpositive maximum
raises `no_positive_bead_peak`. There is no tolerance or prominence threshold.
Unequal near ties are accepted with no stability guarantee. Integer or wider-float
rounding can create ties; finite conversion underflow is allowed. Nonarrays or
array subclasses, unsupported dtypes, invalid shapes and nonfinite samples raise
`invalid_bead_peak_volume`, `invalid_bead_peak_dtype`, `invalid_bead_peak_shape`
and `nonfinite_bead_peak_volume`, respectively. Expected conversion errors use the
last code. Allocation and unrelated failures propagate. Caller samples and NumPy
error modes are preserved; handled arithmetic emits no `RuntimeWarning`.

## Signed asymmetric observation

Run this block with the project environment, for example `.venv/bin/python`.
Samples are explicitly labeled electrons. The second unequal local maximum and
negative background are valid; this operation does not certify bead isolation.
The independently assigned coordinate and value are the comparison truth.

```python
import numpy as np
from simrecon import locate_bead_peak

volume = np.full((3, 5, 4), -6.0)
volume[0, 3, 1] = 8.0
volume[2, 1, 3] = 15.5
volume[1, 0, 0] = volume[1, 4, 2] = 4.0
expected_index = (2, 1, 3)
expected_value = 15.5  # electrons
peak = locate_bead_peak(volume)
assert peak.index_zyx == expected_index
assert peak.value == expected_value
print(peak)
```

Observed result: `BeadPeak(index_zyx=(2, 1, 3), value=15.5)` electrons.
The peak margin is `15.5 - 8 = 7.5` electrons. No approximation budget applies to
this exact converted-sample selection.

## Declared, corrected, known-phase point bead

This independently generated noiseless example uses a finite periodic grid
`(4,5,6)` with spacing `(0.5,0.2,1/6)` µm and periods `(2,1,1)` µm. The
dimensionless detection response is nonnegative and normalized to sum one. Its
asymmetric weights have a unique maximum at zero displacement. This fixes the
detection peak-origin gauge by choice. The on-grid point bead has summed
zero-order brightness `B=318` electrons, not a phase-exposure total or calibrated
photon yield. There is no voxel-volume factor because B is a discrete site weight.

Lateral frequency `q=(0,1)` cycles/µm and axial difference frequency
`kappa=0.5` cycles/µm correspond to integer periodic modes. Equal scalar field
amplitudes give `P=3`. At each output scan site n and bead site b, generate

```text
theta = 2*pi*q·r_b,xy + actual_phase
I = |exp(i*2*pi*kappa*(nz-bz)*dz) + exp(i*theta) + exp(-i*theta)|² / 3
D[n] = B*h[n-b]*I
ideal_dc[n] = B*h[n-b]
raw = offset + response*D
```

All displacements are circular. The axial illumination follows the focal plane
during scanning. The field formula independently generates raw samples; neither
the test fixture nor a product output defines the expected peak.

Actual phases are explicitly supplied generator truth, in radians. Nominal
commands differ by phase and are declaration metadata only. They are never used
as measured truth. A common phase shift preserves DC (zero-order intensity), so
the wrong-command comparison below uses independent step errors.

```python
import numpy as np
from simrecon import (
    correct_linear_response,
    declare_acquisition,
    locate_bead_peak,
    separate_volume_phases,
)

shape = (4, 5, 6)
spacing_zyx = np.array([0.5, 0.2, 1 / 6])  # micrometres
bead_truth = (3, 1, 4)  # generator/comparison only
brightness = 318.0  # summed zero-order electrons
weights = np.ones(shape)
weights[0, 0, 0] = 31.0
weights[2, 1, 4] = 7.0
weights[1, 3, 2] = 4.0
kernel = weights / weights.sum()
coordinates = np.indices(shape)
displacements = tuple((coordinates[a] - bead_truth[a]) % shape[a] for a in range(3))
ideal_dc = brightness * kernel[displacements]

phases = np.array([0.12, 0.91, 1.78, 2.66, 3.55, 4.43, 5.62])
commands = phases + np.array([0.04, -0.06, 0.03, 0.08, -0.02, -0.05, 0.07])
kappa, qx = 0.5, 1.0  # cycles per micrometre
axial_angle = 2 * np.pi * kappa * displacements[0] * spacing_zyx[0]
theta = 2 * np.pi * qx * bead_truth[2] * spacing_zyx[2] + phases[:, None, None, None]
field = np.exp(1j * axial_angle) + np.exp(1j * theta) + np.exp(-1j * theta)
signal = ideal_dc[None] * (np.abs(field) ** 2 / 3)
offset, response = 12.0, 2.5  # counts, counts/electron
raw = (offset + response * signal)[None]  # orientation/phase/z/y/x
config = {
    "version": 1,
    "acquisition_kind": "sim_beads",
    "axes": ["orientation", "phase", "z", "y", "x"],
    "sampling_um": {"z": 0.5, "y": 0.2, "x": 1 / 6},
    "nominal_phases_rad": [commands.tolist()],
    "intensity_unit": "counts",
}
acquisition = declare_acquisition(raw, config=config)
corrected = correct_linear_response(
    acquisition, offset=offset, response=response, output_unit="electrons"
)
group = corrected.data[0]  # caller selects the only orientation; channel/time absent
assert np.array_equal(group, (raw[0] - offset) / response)
observed = separate_volume_phases(group, phases_rad=phases)
peak = locate_bead_peak(observed.dc)  # no truth, kernel, spacing or metadata input
assert peak.index_zyx == bead_truth
assert peak.value == float(observed.dc[bead_truth])
margin = 48.0  # B*(31-7)/159, independently specified kernel weights
budget = 8192 * len(phases) * 2.0**-52 * np.max(np.abs(group), axis=0)
error = float(np.max(np.abs(observed.dc - ideal_dc)))
wrong_dc = separate_volume_phases(group, phases_rad=commands).dc
wrong_error = float(np.max(np.abs(wrong_dc - ideal_dc)))
print(peak)
print("model error, max separator budget, wrong-command error (electrons):",
      error, float(budget.max()), wrong_error)
```

The weight sum is `120 + 30 + 6 + 3 = 159`. Thus the ideal peak is
`318*31/159 = 62` electrons, runner-up is `318*7/159 = 14` electrons, and
margin is `48` electrons. The returned value is the actual observed sample;
separation roundoff need not return exactly 62.

Both blocks were executed from this guide. Local input/expected/output arrays,
SHA-256 file identities, exact scalar results and an independent exact-rational
stored-input comparison are retained in
`artifacts/synthetic-calibration-intake-20261010/C01/`. The comparison solves the
represented five-column least-squares problem independently. At each voxel the
separator budget is `8192*N*2^-52*max_p|group[p]| + 8*2^-1074` electrons, when the
represented phase matrix condition number is at most 10. The artifact computes
that budget in rational arithmetic, retaining the subnormal term. Let delta be
the difference between the exact stored-input fit and the ideal model, and E be
its maximum plus the maximum separator budget. The independent check requires
`48 > 2E`, ensuring the intended grid index survives even opposing sample errors.
The locator adds no fit tolerance. See `comparison.json` for measured errors,
condition number, margin ratio and hashes; these are local numerical evidence,
not physical error bounds.

Observed locally with Python 3.13.12 and NumPy 2.5.3:

| Quantity | Observed value |
|---|---:|
| Selected index z/y/x | `(3,1,4)` |
| Selected sample | `62.00000000000003` electrons |
| Phase-matrix condition number | `1.627994243582887` |
| Maximum separator error against exact rational fit | `9.586e-15` electrons |
| Maximum separator budget | `2.216e-9` electrons |
| Stored-input model discrepancy | `1.173e-14` electrons |
| Margin / twice combined allowance | `1.083e10` |
| Wrong-command DC error against ideal model | `2.035` electrons |

The margin exceeds twice the combined allowance by over ten billion times.
Using nominal commands changes the zero-order fit far beyond rounding error.

## Coordinates and limits

Index z/y/x means sample centers. With an explicitly declared origin and positive
spacing, callers may compute `r_min + index_zyx*spacing_zyx`. For this example,
origin zero gives `(1.5,0.2,2/3)` µm. The last sample centers are `(1.5,0.8,5/6)` µm,
distinct from the periods `(2,1,1)` µm. The locator applies no coordinate conversion,
wrapping, centering, Fourier transform, correction or phase separation.

The kernel's peak at zero is an imposed center gauge, not an inferred physical
point-spread-function center. Asymmetric, off-grid, noisy or multiple-bead images
can have a unique maximum away from an emitter center. Exact positive ties reject;
unequal maxima remain legitimate inputs without isolation or confidence claims.
Camera correction and separation can change ties and peak positions.

This model assumes linear detection, a point bead, known phases, scalar fields,
periodic sampling and a noiseless affine camera. It does not model aberrations,
polarization, finite bead size, drift, fading, saturation, defective pixels or an
unknown background. A finite sampled response implies neither continuous-optics
convergence nor alias-free physical imaging. Partial C1 ends at an observation-
derived integer peak. Empirical signed response formation, transfer calibration,
subvoxel localization, unknown-phase inference, realistic optics, full raw-data
reconstruction and owner-data parity remain separately contracted work.
