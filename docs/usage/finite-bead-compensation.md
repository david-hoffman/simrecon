# Known-profile raw finite-bead calibration

`calibrate_raw_finite_bead` removes a supplied discrete emission profile before
locating the response origin. It corrects the whole raw acquisition, selects one
explicit group and separates supplied actual phases. It then uses the original
exact observed dc mass once for all three orders. The [contract](../contracts/finite-bead-compensation-v1.md)
defines the numerical domains and budgets; the [synthetic model](../models/synthetic-3d-acquisition-v1.md)
defines the finite periodic interpretation.

This runnable example generates sampled real-space circular detection of a
finite bead. The asymmetric detection kernel has its sole peak at zero. The
profile's dominant site is displaced from its declared anchor. Complex field
amplitudes give complex first and second orders. Kernel, brightness and anchor
are generator truth; calibration receives only raw observations and the named
legitimate declarations. Spacing is in micrometres (µm); phases are in radians.

```python
import numpy as np
from simrecon import calibrate_raw_finite_bead, declare_acquisition

shape = (2, 3, 4)  # z, y, x: mixed even/odd, nonsquare
spacing = (0.5, 0.25, 0.125)  # µm
actual = np.array([0.13, 0.84, 1.91, 2.76, 3.69, 4.82, 5.63])
carrier = (1, -1)  # known calibration y/x integer bins
profile = np.zeros(shape, dtype=np.float64)
profile[0, 0, 0], profile[0, 0, 1], profile[0, 2, 0] = 1, 4, 0.5
h = np.full(shape, 1/128)
h[0, 2, 1] += 1/16
h[0, 0, 0] = 0
h[0, 0, 0] = 1 - h.sum()
fields = (1 + 0.2j, 0.47 - 0.31j, -0.26 + 0.39j)
anchor = (1, 2, 1)
brightness = 16.0  # expected-electron zero-order mass

def exposures(specimen, phases):
    result = np.zeros((len(phases), *shape))
    power = sum(abs(a)**2 for a in fields)
    for n in np.ndindex(shape):
        for j in np.ndindex(shape):
            u = tuple((na-ja) % size for na, ja, size in zip(n, j, shape))
            theta = 2*np.pi*(carrier[0]*j[1]/shape[1]
                             + carrier[1]*j[2]/shape[2]) + phases
            axial = 2*np.pi*u[0]/shape[0]
            field = (fields[0]*np.exp(1j*axial) + fields[1]*np.exp(1j*theta)
                     + fields[2]*np.exp(-1j*theta))
            result[(slice(None), *n)] += specimen[j]*h[u]*abs(field)**2/power
    return result

specimen = brightness*np.roll(profile/profile.sum(), anchor, axis=(0, 1, 2))
signals = exposures(specimen, actual)
canonical = np.stack((signals, 1.25*signals))  # orientation/phase/z/y/x
index = np.arange(canonical.size).reshape(canonical.shape)
commands = actual + np.array([0, 0.03, -0.02, 0.05, -0.04, 0.08, -0.06])
config = {
    "version": 1, "acquisition_kind": "sim_beads",
    "axes": ["orientation", "phase", "z", "y", "x"],
    "intensity_unit": "count", "sampling_um": {"z": 9, "y": None, "x": 7},
    "nominal_phases_rad": np.broadcast_to(commands, canonical.shape[:2]).tolist(),
    "acquisition_id": "synthetic-finite-profile", "calibration_id": "example-only",
}
results, inputs = {}, {}
for name, offset, response in (
    ("scalar", 10.0, 2.0),
    ("maps", 7 + (index % 11)/8, 1.5 + (index % 7)/4),
):
    raw = offset + response*canonical  # counts; response in counts/electron
    acquisition = declare_acquisition(raw, config=config,
                                      original_metadata={"purpose": "synthetic example"})
    result = calibrate_raw_finite_bead(
        acquisition, group={"orientation": 0}, offset=offset, response=response,
        output_unit="electron", phases_rad=actual, voxel_size_um=spacing,
        bead_profile=profile, calibration_carrier_bins=carrier,
        min_profile_transfer=0.1,
    )
    results[name] = result
    inputs[name] = (acquisition, offset, response)
    print(name, result.response.values.shape, result.response.origin_zyx)
```

Both cases produce `(3, 2, 3, 4)` responses and compensated origin `(1, 2, 1)`.
The blurred dc peak is `(1, 2, 2)`. Complete correction maps have the canonical
acquisition shape; nonselected invalid samples still reject. Nominal phases and
source sampling remain metadata. Supplied actual phases and spacing control the
calculation. Stored camera rounding and the represented phase matrix define
the numerical fit; model truth is a separate comparison.

For order `m=0,1,2`, the native divisor is `P[k-m*carrier]`, with zero axial
carrier. `P` is the discrete Fourier transform (DFT) of exact-mass-normalized
site weights, not a continuous sphere formula. Every computed native profile
node must certify `abs(P) >= minimum + eta`, with exact represented-component
magnitude and exact addition. Here `eta=128*M*2^-52+4*M*2^-1074`, where `M` is
the number of voxels; dc has zero allowance. The origin-point profile has exact
all-ones transfer and zero allowance everywhere. Translated points still need
phase compensation. Weak or uncertifiable profiles reject with
`unstable_finite_bead_transfer`; there is no regularization or partial inverse.

The real inverse of compensated dc supplies the sole positive grid peak.
Negative localization samples are allowed. The diagnostic does not replace the
original mass or normalize another time. All three complex spectra use one
origin phase. Zero-order dc is exactly one. Side gains, side dc, complex
zero-order bins and the common separation phase gauge remain. Signed negative
orders follow modular reflection and conjugation, including even Nyquist bins.

`FiniteBeadCalibration` has exactly `components`, `response` and `provenance`.
Bindings are frozen; owned arrays and the plain metadata dict remain mutable.
Provenance retains complete source metadata, explicit group, supplied/applied
camera coefficients, actual phases, spacing and relative profile weights,
unreduced carrier integers, minimum, centered profile transfer and native real
`compensated_dc`. Model is `discrete_finite_bead_v1`; response gauge is
`compensated_dc_peak_with_supplied_phase_origin`. No returned array aliases a
caller buffer. The library performs no file I/O or hashing.

For existing transfer consumers, pass `result.response` to
`adapt_empirical_volume_response` with explicit `carrier_bins`,
`coordinate_offset_yx`, `phase_reference_shift_rad` and `source`. Physically
moving a bead changes its illumination phase; rolling stored volumes changes
coordinates. Those controls need their respective declared gauge corrections.
Changing supplied phases by a common `alpha` multiplies order `m` by
`exp(-i*m*alpha)`. Independent phase-step errors generally change the fit.
Compensate the native response nodes before using the existing complex
interpolation adapters. The existing closed physical frequency coverage and
negative-order reflection rules still apply.

The actual local example cohort is generated by
`artifacts/finite-bead-compensation-20261016/C03/examples/generate.py` in observer
mode. It executes this code block once, retains raw/expected/returned arrays,
and compares stored-input fits and direct DFT sums with the reviewed independent
110-digit observer. Its second group compares calibration → existing transfer
adapter → known-parameter volume reconstruction with the independent signed
finite ridge estimator, preserving gains and normalization once. Separate
reports record profile certificates, origin margins, phase/input/arithmetic
error, interpolation error and reconstruction bias. The manifest and generation
association preserve actual inputs, executable and child interval; later clean
candidate admission and verification are separate coordinator observations.

These are noiseless finite periodic sampled examples. Supplied profile, known
carrier, fixed detection and actual phases are assumptions, not instrument
estimates. The profile certificate is a numerical conditioning policy; the
observed peak does not certify physical isolation, bead geometry or a continuous
center. Common normalization discards brightness scale. Reconstruction targets
the declared masked finite ridge estimator and need not recover the specimen
exactly. Continuous optics, unknown phases/carriers/drift, realistic noise,
owner-data/reference parity and the complete truth-hidden workflow remain
unresolved. Allocation and unrelated dependency errors propagate. Focused
examples supply no local, independent-review or CI qualification verdict.
