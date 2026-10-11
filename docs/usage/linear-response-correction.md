# Declared linear-response correction

Use `correct_linear_response` when you supply the complete samplewise relation
`raw = offset + response * signal`. Raw and offset have the input intensity unit.
Response has input units per output unit and must be strictly positive. The
library retains unit labels exactly, including whitespace, without checking
dimensional consistency or interpreting their spelling.

This implements a partial R2 foundation. It supplies no measured instrument
calibration, specimen/bead settings, exposure normalization, background estimate,
saturation detection or bad-pixel repair. Finite flagged pixels and dtype maxima
still participate in the arithmetic. Physical usefulness depends on the declared
relation applying to those measurements.

## Count to electron

Here the caller declares offset = 10 count and response = 2 count/electron.
The independent expectation is `(110 - 10) / 2 = 50 electron`. Substituting
back gives `10 + 2 * 50 = 110 count`. Run this complete example in the project
environment:

```python
import numpy as np
from simrecon import correct_linear_response, declare_acquisition

raw = declare_acquisition(
    np.array([[110, 6, 10], [-2, 12, 14]], dtype=">i2"),
    config={
        "version": 1,
        "acquisition_kind": "detection_psf",
        "axes": ["y", "x"],
        "intensity_unit": "count",
    },
)
corrected = correct_linear_response(
    raw, offset=10, response=2, output_unit="electron"
)
expected = np.array([[50, -2, 0], [-6, 1, 2]], dtype=np.float64)
np.testing.assert_array_equal(corrected.data, expected)
np.testing.assert_array_equal(10 + 2 * corrected.data, raw.data)
assert corrected.input_unit == "count" and corrected.output_unit == "electron"
assert corrected.provenance["offset"]["supplied"] == 10
assert corrected.provenance["offset"]["applied"] == 10.0
assert "data" not in corrected.source_metadata
print("count/electron maximum error:", np.max(np.abs(corrected.data - expected)))
```

Negative corrected values remain negative. Identity also requires explicit
`offset=0`, `response=1` and an output label. Both coefficients independently
accept a plain built-in integer/float or a plain NumPy integer/floating array.
Every array must match the entire canonical sample shape; there is no implicit
broadcasting or axis inference. Maps may use either byte order and arbitrary
strides. NumPy scalars, array subclasses and lists are outside this interface.

## Full maps followed by known-phase volume separation

This synthetic example labels a nonsquare volume independently across two
orientations, seven unequal phases, two z planes, three y rows and four x columns.
For each voxel the independently selected coefficients are
`dc = 24 + 7*orientation + 3*z + 2*y + x`,
`c1 = (1 + x/4) - i*(2 + y/4)` and
`c2 = (3 + z/2) + i*(4 + orientation/2)`, in electron units.
The forward signal is `dc + 2*Re(c1*exp(i*phi) + c2*exp(2*i*phi))`.
The code uses the separator contract's represented phasor-squared basis.

The declaration starts in z/orientation/phase/y/x order. Coefficient maps use
the resulting canonical orientation/phase/z/y/x coordinates. All nominal
commands are deliberately zero. The caller supplies the independent true phase
vector to the separator explicitly.

```python
from fractions import Fraction

import numpy as np
from simrecon import (
    correct_linear_response,
    declare_acquisition,
    separate_volume_phases,
)

phases = np.array([0.1, 0.8, 1.7, 2.5, 3.6, 4.4, 5.8])
c, s = np.cos(phases), np.sin(phases)
H = np.column_stack((np.ones(7), c, s, c*c - s*s, (2*c)*s))
K = H * np.array([1, 2, -2, 2, -2])
assert np.linalg.cond(H) < 10
o, z, y, x = np.indices((2, 2, 3, 4))
expected = np.stack((
    24 + 7*o + 3*z + 2*y + x,
    1 + x/4,
    -2 - y/4,
    3 + z/2,
    4 + o/2,
), axis=1)
signal = np.empty((2, 7, 2, 3, 4))
for orientation in range(2):
    for p in range(7):
        signal[orientation, p] = sum(
            K[p, j] * expected[orientation, j] for j in range(5)
        )
o, p, z, y, x = np.indices(signal.shape)
offset = (1 + 2*o + 4*p + 8*z + y + x).astype(">i2")
response = (2.0 ** ((o + p + z + y + x) % 3)).astype(">f8")
raw_samples = offset + response * signal
acquisition = declare_acquisition(
    raw_samples.transpose(2, 0, 1, 3, 4),
    config={
        "version": 1,
        "acquisition_kind": "specimen_sim",
        "axes": ["z", "orientation", "phase", "y", "x"],
        "intensity_unit": "count",
        "nominal_phases_rad": [[0.0]*7, [0.0]*7],
    },
)
assert acquisition.axes == ("orientation", "phase", "z", "y", "x")
corrected = correct_linear_response(
    acquisition, offset=offset, response=response, output_unit="electron"
)

# Independent observer: exact rational subtraction and division, each rounded
# separately to Python binary64. It does not use corrected product values.
reference = np.empty(signal.shape)
for index in np.ndindex(signal.shape):
    numerator = float(
        Fraction.from_float(float(raw_samples[index]))
        - Fraction.from_float(float(offset[index]))
    )
    reference[index] = float(
        Fraction.from_float(numerator)
        / Fraction.from_float(float(response[index]))
    )
np.testing.assert_array_equal(corrected.data, reference)
np.testing.assert_array_equal(
    corrected.source_metadata["nominal_phases_rad"], np.zeros((2, 7))
)

# Bound forward storage/rounding error independently against the selected
# coefficients. A residual r perturbs the full-rank least-squares coordinates
# by at most ||r||_2 / sigma_min(K). Factor 2 allows numerical norm rounding.
smallest = float(np.linalg.svd(K, compute_uv=False)[-1])
eps = 2.0**-52
maximum_error = 0.0
maximum_budget_fraction = 0.0
for orientation in range(2):
    parts = separate_volume_phases(corrected.data[orientation], phases_rad=phases)
    actual = np.stack((
        parts.dc, parts.c1.real, parts.c1.imag, parts.c2.real, parts.c2.imag
    ))
    forward_budget = np.empty((2, 3, 4))
    for index in np.ndindex(forward_budget.shape):
        residuals = []
        for p in range(7):
            exact_forward = sum(
                Fraction.from_float(float(K[p, j]))
                * Fraction.from_float(float(expected[(orientation, j, *index)]))
                for j in range(5)
            )
            stored = Fraction.from_float(float(reference[(orientation, p, *index)]))
            residuals.append(abs(stored - exact_forward))
        forward_budget[index] = 2*np.sqrt(7)*float(max(residuals))/smallest
    fit_budget = 8192*7*eps*np.max(np.abs(reference[orientation]), axis=0)
    # Observer rounding allowance plus the separator's informative-regime budget.
    budget = forward_budget + fit_budget + 2*eps*np.max(np.abs(expected[orientation]), axis=0)
    error = np.abs(actual - expected[orientation])
    assert np.all(error <= budget)
    maximum_error = max(maximum_error, float(error.max()))
    maximum_budget_fraction = max(maximum_budget_fraction, float((error/budget).max()))
print("map correction maximum error:", np.max(np.abs(corrected.data - reference)))
print("harmonic coordinate maximum error (electron):", maximum_error)
print("maximum fraction of independent error budget:", maximum_budget_fraction)
```

The analytic coefficients are the independent reference; the residual bound
accounts for rounded forward samples and correction. The separator returns the
least-squares harmonics of the observed corrected volume. It does not reconstruct
a specimen or identify axial optical orders. Sampling and spatial axes do not
change. Other numeric operations retain their own input requirements; signed
corrected samples do not waive a point-spread function's positivity requirement.

## Representation, provenance and limits

Pixels, offset and response normalize once to native binary64. Subtraction
materializes a binary64 numerator before division. A nonfinite source or
conversion is rejected; a nonfinite numerator or quotient raises
`SimreconError` with code `linear_response_range`. An overflowing subtraction
rejects even if an exact-real combined quotient would fit. Positive subnormal
responses are valid. Subnormal results and signed underflow to zero are valid.
Caller NumPy error modes and unrelated warning channels remain intact.

The result owns float64 samples, complete source metadata except raw pixels,
and supplied/applied coefficient snapshots. Supplied map shape, dtype, byte
order and values are retained; applied maps are native float64. Scalar supplied
values retain built-in int versus float. Metadata, IDs, opaque flags and nominal
commands remain declarations, without new interpretation. Keep the original
acquisition when raw samples are needed. Buffers are mutable and independently
owned from caller storage; metadata is read-only by convention.

The operation holds a complete output, coefficient and metadata snapshots, and
arithmetic scratch. It has no streaming or whole-volume memory bound. Allocation
failures and unrelated exceptions propagate. Input rounding is part of the
specified arithmetic; it is not an instrument accuracy guarantee. See the
[linear-response contract](../contracts/linear-response-correction-v1.md),
[raw declarations](../contracts/raw-acquisition-declarations-v1.md) and
[known-phase volume contract](../contracts/volume-phase-separation-v1.md).
