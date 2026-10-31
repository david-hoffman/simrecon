# Fit continuous specimen carriers and relative order gains

`fit_volume_overlap` consumes known-phase separated dc,c1,c2 for one specimen
orientation and one fixed `VolumeOrderOtf`. It fits a continuous lateral carrier
and two relative complex gain corrections under the
[declared finite overlap objective](../contracts/reference-alignment-ra09-v1.md).
Carrier units are cycles per micrometre; coordinates are y,x. The calibration
phase gauge and spatial index-zero origin remain fixed.

```python
import numpy as np
from simrecon import fit_volume_overlap

# separated is the result of the existing known-phase volume separator.
bands = np.stack((separated.dc, separated.c1, separated.c2)).astype(np.complex128)
fit = fit_volume_overlap(
    bands,
    order_otf=calibration,
    initial_carriers_per_um=nominal_carriers,
    carrier_bounds_per_um=metadata_search_box,
    difference_step_per_um=np.array([1e-5, 1e-5]),
    gradient_tolerance=1e-6,
    rank_rtol=1e-6,
    max_evaluations=256,
)
for candidate in fit.candidates:
    print(candidate.carrier_per_um, candidate.gains, candidate.status)
```

Every keyword is required. `nominal_carriers` is a real `(T,2)` array of caller
starts. `metadata_search_box` is a real `(2,2)` array with lower and upper y,x
rows. Use acquisition metadata to choose starts and bounds. A simulator's true
carrier is an evaluation value, never a substitute for an estimate. One result
record corresponds to every supplied start, including duplicate and failed
local attempts. The operation chooses no global winner.

Both positive orders share one carrier objective. Each order's complex gain is
its conditional regression against dc on fixed, nonwrapping overlap valid over
the entire search box. The score uses normalized residuals with equal order
weight; it is dimensionless and is not a noise likelihood. A wide search box
can reduce overlap before search begins. Inspect `fit.overlap_bins`, per-order
status and the reported cross-weighted norm scales. Tiny nonzero signals can
receive the same normalized weight as strong signals.

Empty overlap and zero predictors are unavailable. A zero response can return
a gain of zero while providing no carrier information. Fixed carrier boxes are
valid controls and establish no carrier information. Rank and finite-step
stationarity are diagnostics with caller-selected scales. Changes between
informative and unavailable orders at diagnostic points make those diagnostics
nonsmooth; they do not certify stationarity. Every result explicitly retains
unresolved global ambiguity.

The observation uses the finite Fourier sum over all stored spatial samples.
The transfer uses Cartesian complex linear interpolation. Neither supplies a
continuous exterior. For frequency-varying responses these operations need not
commute with finite-window modulation, so a low overlap residual can coexist
with physical prediction error. Validate predicted phase across the fixed
field and held-out observations where the model permits. Keep carrier slope
error separate from a common complex-gain phase offset. This operation estimates
no exposure-phase errors, drift, pupil, absolute throughput or resolution.

The [executed comparison](../reports/reference-alignment-ra09-comparison.md)
records independent inputs, expected values, measured outputs and the scope
of the actual evidence.
