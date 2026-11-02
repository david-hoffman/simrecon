# RA13 fixed small workflow controls

These public synthetic observations demonstrate the integrated raw-array boundary.
They are separate from the original noisy RA12 benchmark and from RA14's full
27-object scene. Settings were fixed before running the new workflow.

- `noiseless/observations.npz` contains only seven observed arrays; its
  `parameters.json` contains allowed geometry, labels and finite-procedure controls.
- `noisy-diagnostic/` adds fixed normal perturbations with seed 20261102 and
  standard deviation 0.001 detector counts to the calibration/specimen images,
  preserving the constant camera observations. Its training limit is 0.
- `evaluation-reference.npz` is a separate generator/evaluator reference. The
  workflow neither loads it nor accepts its true source/illumination fields.

The supplied camera groups are constants: dark −2, blank 7 and flat 11 detector counts,
with two 2×2 frames each. Image counts are 7+4 times the declared optical prediction.
The camera physical-gain diagnostic may be unavailable; the relative gauge remains
usable. Calibration shape is 1×3×24, spacing 0.125/0.080/0.080 µm in z/y/x, with three
radius 0.050 µm spheres from the independent public RA12 fixture. Specimen detector
shape is 3×2×3 with spacing 0.21/0.17/0.11 µm. Its source shape is 3×4×6; two integrated
relative weights, 0.6 and 0.3, occupy cells (0,0,2) and (0,1,0). Local source cell centers
use half-cell coordinates. The first center is local z/y/x (0.105,0.0425,0.1375) µm;
add specimen origin (0.12,−0.19,0.43) µm for global coordinates.

The noiseless generator uses central-only illumination. Training limit 100 and
operator comparison setting 1e6 are explicitly permissive procedure controls.
Calibration comparison setting is 1e−8; one refinement-function-evaluation setting,
one specimen update and regularization 0.01 are fixed. This is a degenerate finite
execution control, not physical calibration identification, demonstrated structured
illumination resolution, source recovery or convergence. Noisy outputs are diagnostic.

The [executed usage](../../usage/reference-alignment-ra13.md),
[scientific report](../../reports/reference-alignment-ra13.md) and its evidence
record distinguish observations, composition agreement, descriptive differences
and unsupported claims. No reference executable is invoked.
