# Finite integer-carrier diagnostics

`scan_carriers` fits phase offset and modulation for each supplied signed integer
carrier. It returns a complete tuple in caller order. It preserves duplicates and
does not select or rank a carrier. See the [contract](../contracts/carrier-scan-v1.md)
and [executed comparison](../reports/carrier-scan-comparison.md).

This executable example uses signed two-pixel images, explicit relative steps in
radians and a full complex optical transfer function (OTF). Intensities are in
arbitrary units; pixel sizes are in micrometres. The detector-bin carrier is `(ky,kx)`.

```python
import numpy as np

from simrecon import Otf2D, scan_carriers

steps = np.array([-0.8, 0.17, 1.6, 3.1, 4.7])
dc = np.array([[1.0, -1.0]])
c1 = np.array([[0.2 + 0.1j, -0.2 - 0.1j]])
images = np.array([
    dc + 2 * (c1.real * np.cos(p) - c1.imag * np.sin(p))
    for p in steps
])
calibration = Otf2D(
    values=np.ones((1, 2), dtype=np.complex128),
    fy_per_um=np.array([0.0]),
    fx_per_um=np.array([-1 / (2 * 0.35), 0.0]),
    pixel_size_um=(0.2, 0.35),
    origin_yx=(0, 0),
    source="explicit unit-transfer two-pixel example",
)
results = scan_carriers(
    images,
    otf=calibration,
    phase_steps_rad=steps,
    candidate_carriers_bins_yx=[(0, 0), (0, 2), (0, 0)],
)
for candidate in results:
    if candidate.estimate is None:
        print(candidate.carrier_bins_yx, candidate.failure_code)
    else:
        fit = candidate.estimate
        print(candidate.carrier_bins_yx, round(fit.modulation, 6),
              round(fit.phase_offset_rad, 6), fit.overlap_count)
```

Observed output:

```text
(0, 0) 0.447214 0.463648 2
(0, 2) no_illumination_overlap
(0, 0) 0.447214 0.463648 2
```

Each success contains an `IlluminationEstimate`. Its modulation is unconstrained;
values above one remain valid diagnostic fits. Corrected `phases_rad` rotates the
represented sine/cosine values into principal-equivalent phases and owns mutable
float64 storage. Duplicate successes have separate arrays. Records have frozen
bindings; that does not freeze their array contents. Inputs remain unchanged.

Candidates may be a nonempty tuple/list of integer pairs or a plain array of shape
`(M,2)`. Each coordinate must be a nonboolean Python or NumPy integer. Arbitrarily
large integers, either endian, strided/read-only integer arrays and object arrays
containing actual integers are permitted. The complete collection is validated
before executing any candidate. There is no candidate-count cap, rounding, wrapping
or deduplication. With fixed phase-step signs, opposite carriers remain distinct.

Only `no_illumination_overlap` and `unidentifiable_illumination` become local failure
records. All-candidate failure returns the full tuple. Common image, phase, rank,
range and calibration validation still applies when none succeeds. Any other domain,
solver, range, allocation or unrelated failure aborts the entire call; no partial
tuple is returned. The [known-carrier estimator](illumination-estimation.md) supplies
the inherited input, precision and error rules.

A smaller residual does not prove the true carrier. Different candidates compare
different overlaps. One informative complex pair admits an exact scalar fit, and
geometric overlap counts include zero-transfer pairs. Noise, weak support, aliases, sparse or periodic specimens and model mismatch can make the landscape ambiguous.
There is no support threshold, confidence score or physical-modulation filter.
Carrier selection, fractional refinement, independent phase-step errors, drift and
brightness estimation require separate contracts. Reconstruction still needs an
explicit carrier and brightness and enforces its own modulation domain.
