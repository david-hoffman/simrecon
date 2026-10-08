# Explicit finite-carrier selection

`select_carrier` returns the unique row passing your explicit acceptance policy.
It keeps the complete scan, including failed rows and duplicates. See the
[contract](../contracts/carrier-selection-v1.md) and
[measured independent comparison](../reports/carrier-selection-comparison.md).

This complete example synthesizes an alias-free periodic first-harmonic acquisition.
Intensities use arbitrary units. Relative phases and the common offset use radians.
The optical transfer function (OTF) is explicitly unity on a 5 by 7 pixel detector,
with (dy, dx) = (0.7, 1.3) micrometres. Carrier coordinates are signed (y, x)
detector-frequency bins. The limits below are an illustrative caller policy:
residual at most 0.05, at least 12 geometric pairs, and modulation in [0.6, 1.0].
They are not calibrated noise or accuracy thresholds.

```python
import numpy as np

from simrecon import Otf2D, select_carrier

ny, nx = 5, 7
steps = np.array([-0.4, 0.7, 1.9, 3.4, 5.2])
y, x = np.indices((ny, nx))
specimen = 2 + 0.6 * np.cos(2 * np.pi * x / nx + 0.3)
specimen += 0.4 * np.cos(2 * np.pi * y / ny - 0.2)
c1 = 0.4 * np.exp(0.63j) * specimen * np.exp(2j * np.pi * x / nx)
images = np.array([
    specimen + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p))
    for p in steps
])
calibration = Otf2D(
    values=np.ones((ny, nx), dtype=np.complex128),
    fy_per_um=np.arange(-2, 3, dtype=float) / (ny * 0.7),
    fx_per_um=np.arange(-3, 4, dtype=float) / (nx * 1.3),
    pixel_size_um=(0.7, 1.3),
    origin_yx=(0, 0),
    source="explicit unit-transfer periodic example",
)
selection = select_carrier(
    images,
    otf=calibration,
    phase_steps_rad=steps,
    candidate_carriers_bins_yx=[(0, 0), (0, 1), (0, 2), (100, 0)],
    max_relative_residual=0.05,
    min_overlap_count=12,
    modulation_bounds=(0.6, 1.0),
)
for index, row in enumerate(selection.candidates):
    if row.estimate is None:
        print(index, row.carrier_bins_yx, row.failure_code)
    else:
        fit = row.estimate
        print(index, row.carrier_bins_yx, round(fit.modulation, 6),
              round(fit.relative_residual, 6), fit.overlap_count)
print("eligible", selection.eligible_indices)
if selection.selected_index is None:
    if selection.failure_code == "no_acceptable_carrier":
        print("No row passes this policy; inspect the retained diagnostics.")
    else:
        print("Multiple rows pass; inspect candidates and policy assumptions.")
else:
    chosen = selection.candidates[selection.selected_index]
    fit = chosen.estimate
    assert fit is not None
    print("selected", chosen.carrier_bins_yx,
          "phase offset", round(fit.phase_offset_rad, 6))
    # fit.phases_rad and fit.modulation are available to the caller.
    # Reconstruction still needs explicit carrier, brightness and other inputs.
assert selection.eligible_indices == (1,)
assert selection.selected_index == 1
assert selection.failure_code is None
```

Observed output:

```text
0 (0, 0) 0.225352 0.959505 35
1 (0, 1) 0.8 0.0 30
2 (0, 2) 0.225352 0.959505 25
3 (100, 0) no_illumination_overlap
eligible (1,)
selected (0, 1) phase offset 0.63
```

Only `images` is positional. All keywords are required. Residual and modulation
limits accept nonboolean Python/NumPy integer or floating scalars that are finite
before and after float64 conversion. Converted limits must be nonnegative;
modulation bounds must be ordered. Bounds may be equal, zero or above one.
Bounds containers are tuple/list pairs or plain one-dimensional length-two arrays;
object arrays containing permitted scalars, either endian and strided/read-only
arrays are supported. Arrays as individual scalar limits are rejected.
`min_overlap_count` accepts a nonboolean Python/NumPy integer at least one,
including arbitrarily large integers; integral floats are rejected. Invalid policy
raises `SimreconError` with code `invalid_carrier_selection_policy` before scanning.
Conversion rounding and underflow define the limits actually used. Comparisons
are inclusive against computed diagnostics, with no tolerance or hidden cutoff.
A roundoff-sized change can change a boundary decision.

The [scan input and error rules](carrier-scan.md) apply unchanged. Every candidate
is scanned before selection. Successful rows pass only when residual, geometric
count and both modulation bounds all pass. Failed rows are ineligible. Zero passing
rows return `no_acceptable_carrier`; multiple passing rows return
`ambiguous_carrier`. These are result values, with `selected_index=None`, rather
than exceptions. Two copies of a passing candidate create ambiguity. A permissive
policy does not choose the smallest residual or largest overlap. There is no
ranking, candidate cap, deduplication or fallback winner.

`CarrierSelection` has frozen bindings. Its candidates retain complete estimates
and independent mutable float64 corrected-phase arrays, including for duplicates.
No output aliases caller storage. Inputs and NumPy error mode remain unchanged.
The two scan-local information failures remain rows; every other inherited domain,
solver, range, allocation or unrelated failure aborts the whole operation unchanged.

A unique passing row does not identify the physical carrier or establish confidence,
robustness, informative support or uniqueness outside the supplied candidates.
Residuals on different overlaps compare different data. Geometric counts include
zero-transfer pairs; one informative complex pair can fit exactly. Sparse data,
noise, weak support, aliases and model mismatch can pass these gates. An omitted
carrier stays omitted. The comparison demonstrates both sparse and one-pair limits.
This helper performs no reconstruction, fractional refinement, grid generation,
phase-step estimation, drift or brightness estimation. Existing reconstruction
independently requires physical modulation in (0, 1] and its other explicit inputs.
