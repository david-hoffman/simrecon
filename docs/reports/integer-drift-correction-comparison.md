# Integer specimen-drift comparison

The new public `correct_integer_drift` operation passed the frozen independent
pixel, phase and finite-model comparisons. With two orientations, downstream
reconstruction differed from the analytic specimen by at most
`1.3323136419103216e-15` intensity units. Correcting pixels while retaining the
original illumination phases instead gave `0.8180860809928696` intensity units
of error. These are measured finite-model results under the
[approved contract](../contracts/integer-drift-correction-v1.md), not physical
microscope accuracy or automatic drift-estimation evidence.

Reproduce from the repository root:

```sh
.venv/bin/python artifacts/integer-drift-execution/C-comparison.py
.venv/bin/python artifacts/integer-drift-execution/C-usage.py
```

The second script is the exact Python block in the
[executed usage example](../usage/integer-drift-correction.md). It printed
`(10, 12) (0.25, 0.125) True`. Both scripts are ignored local evidence.

The comparison writes and reloads
[`drift-comparison-inputs.npz`](../../artifacts/integer-drift-execution/drift-comparison-inputs.npz)
before numerical evaluation. The separate
[`drift-comparison-outputs.npz`](../../artifacts/integer-drift-execution/drift-comparison-outputs.npz)
retains actual aligned images, returned phases and phasors, independent expected
pixels/phasors/stationary images/components, fitted observations, reconstructed
image/spectrum and the deliberately wrong controls. The
[`drift-comparison.json`](../../artifacts/integer-drift-execution/drift-comparison.json)
records every array's dtype, shape and byte hash, archive and source hashes,
command/status, environment, timestamps, budgets and measured maxima. All stored
caller inputs remained unchanged. These ignored artifacts must accompany the
handoff; the Markdown alone is not the complete numerical evidence.

Expected values reuse B2's frozen `tests/integer_drift_fixture.py`, SHA256
`1f0642051492dff8aef8e342acecff2ff82749c9d180d9eddd34ffcae1b56a8f`.
Its acquisition translates the specimen **before illumination**, then evaluates
convolution as explicit finite sums. Literal modular indexing independently
checks every output pixel. A 90-digit Decimal observer forms and normalizes
products of represented NumPy sine/cosine values, using Fraction for independent
rational-cycle reduction. This is reuse of independently authored, B-accepted
references, not another independent review. No production helper supplies truth.

The reference specimen and index-zero asymmetric unit-mass kernel are explicit:

```text
s(y,x) = 2 + 0.3*cos(2*pi*y/Ny) + 0.2*sin(2*pi*x/Nx)
           + 0.1*cos(2*pi*(y/Ny+x/Nx))
h[0,0] = 4/8; h[1,0] = 1/8; h[0,1] = 3/8
```

All finite cases use five unequal phases `[0, 0.7, 2, 3.4, 5.2]` radians and
displacements `[(0,0), (1,-2), (-1,1), (2,3), (-3,-2)]` pixels. Brightness is
`1.25` and modulation `0.6`, except the reconstruction x orientation, which uses
`0.75` and `0.8`. These dimensionless gains are supplied, not estimated.

The scientific sign follows directly from changing the periodic convolution
coordinate. For kernel coordinate `v` and displacement `d`:

```text
J(x) = I(x+d)
     = sum_v h(v)*s(x+d-v-d)*L_phi(x+d-v)
     = sum_v h(v)*s(x-v)*L_(phi+2*pi*k·d)(x-v).
```

Thus negative pixel alignment and positive phase correction are both necessary.
The report compares `J` with the independently convolved constant component
plus twice the real part of the independently convolved harmonic times the
corrected reference phasor. It also checks the seven analytic Fourier-series
coefficients of the specimen: DC `2`, y modes `0.15`, x modes `+0.1i/-0.1i`,
and diagonal modes `0.05`. These visible equations and coefficients provide
scientific checks beyond agreement with a hidden helper.

| Case | Shape `(Ny,Nx)` | Carrier bins `(y,x)` | Finite identity maximum error | DC maximum error | First-harmonic maximum error |
|---|---|---|---:|---:|---:|
| Odd/even | `(5,6)` | `(1,-1)` | `1.77636e-15` | `2.66454e-15` | `1.13899e-15` |
| Even/odd | `(4,5)` | `(-1,1)` | `8.88178e-16` | `2.22045e-15` | `8.32667e-16` |
| Reconstruction y | `(5,6)` | `(1,0)` | `1.77636e-15` | `8.88178e-16` | `1.42422e-15` |
| Reconstruction x | `(5,6)` | `(0,1)` | `1.33227e-15` | `1.11022e-15` | `5.66275e-16` |

All errors in this table are in input intensity units. Every aligned pixel
matches the literal permutation exactly. Across these cases and supplemental
huge-phase/signed-extrema/unsigned-extrema cases, the largest circular phase
error is about `2.49889e-16`, below `512*2^-52 = 1.1368683772161603e-13`.
Unsigned extrema independently reduce to `3/4` turn; signed extrema to `7/12`
turn. Huge inputs include both signs of float64 maximum and `1e200` radians.
These inputs distinguish phasor combination from premature huge-angle addition
or reduction modulo rounded `2*pi`.

The corrected first-harmonic fit residuals range from `1.66533e-15` to
`3.55271e-15` intensity units. The wrong pixel-only controls have fit residuals
from `1.11755` to `1.46101`, and harmonic errors from `0.893089` to `1.08441`.
The small residuals combine stored-input/trigonometric rounding and numerical
solver effects; this experiment does not isolate each contribution. The large
wrong-control residuals reflect inconsistent illumination phases, a model
mismatch rather than numerical drift-correction error.

Reconstruction uses the real public `prepare_otf`, `separate_phases` and
`reconstruct` interfaces. Spacing is `(0.5, 0.25)` µm per detector pixel, hence
wavevectors `(1/(5*0.5), 0) = (0.4, 0)` and
`(0, 1/(6*0.25)) = (0, 2/3)` cycles/µm. The output is `(10,12)` at
`(0.25,0.125)` µm per pixel. Ridge penalty is zero; the explicit mask retains
only the central `3 x 3` modes. Corrected phase-matrix condition numbers are
`6.18898` and `2.31217`; the finite transfer and brightness keep the retained
modes within the existing informative regime.

| Reconstruction quantity | Maximum absolute error |
|---|---:|
| Corrected complex image versus analytic specimen | `1.3323136419103216e-15` intensity units |
| Corrected spectrum versus seven analytic modes | `4.441229991570736e-16` Fourier-series amplitude units |
| Corrected image imaginary residue | `5.981507157853152e-17` intensity units |
| Pixel-only image versus analytic specimen | `0.8180860809928696` intensity units |
| Pixel-only spectrum versus analytic modes | `0.30091332604243703` Fourier-series amplitude units |

The reconstruction allowance against the stored-data estimator is
`8192*2*5*120*2^-52*max(abs(images))/0.75 = 1.3856377409738629e-8`.
A separate `2.9560271807442405e-9` intensity-unit allowance covers comparison
with independently generated object truth rather than the exact stored-data
estimator. The JSON retains the finite-identity and component allowances too.
Measured maxima sit well below these conservative project budgets; no result
here establishes an exact-real trigonometric or bitwise cross-platform promise.

Observed environment: Python 3.13.12, NumPy 2.5.3, SciPy 1.18.1, h5py 3.16.0,
macOS 27.0 arm64. Local `longdouble` is 8 bytes with the same range as float64;
wider-source overflow still needs a capable configured platform. The lock
SHA256 is `e6ff14aa7d6c2108292aaef624d150f48876954ff3989e1bc3955ef2aa1ddb2b`.
The JSON fingerprints every runtime source used and the generator itself.

These are small noiseless finite periodic examples with supplied exact integer
motion, stationary integer-bin illumination and a fixed shift-invariant kernel.
They establish no physical shift confidence, camera-motion correction,
fractional interpolation, nonperiodic-edge recovery, noise robustness or
automatic parameter acceptance. Preparation can produce a phase-rank-deficient
set that downstream separation rejects. Fresh implementation review, canonical
exact-candidate `make verify`, complete native coverage reports and configured
Ubuntu 24.04/macOS 15 jobs remain separate binding obligations.
