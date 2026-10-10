# Known-reference integer translation

`estimate_translation` compares a moving image with an explicit reference on
the complete periodic integer-pixel grid. Supply comparable equal-intensity
images and an explicit dimensionless ambiguity tolerance. The
[approved contract](../contracts/translation-estimation-v1.md) defines the
objective and accepted representations.

This compact example was executed with the worktree environment:

```python
import numpy as np
from simrecon import estimate_translation

reference = np.array([[3, -2, 0, 7, 1], [8, 4, -5, 2, 6], [-1, 9, 5, -3, 10]])
moving = np.roll(reference, (1, -2), axis=(0, 1))
result = estimate_translation(moving, reference=reference, ambiguity_tolerance=0.001)
print(result.displacement_pixels_yx, result.minimum_normalized_rms, result.failure_code)
# (1, -2) 0.0 None
assert result.displacement_pixels_yx == (1, -2)
aligned = np.roll(moving, tuple(-v for v in result.displacement_pixels_yx), axis=(0, 1))
assert np.array_equal(aligned, reference)

ambiguous = estimate_translation(moving, reference=reference, ambiguity_tolerance=3)
print(ambiguous.displacement_pixels_yx, ambiguous.failure_code,
      len(ambiguous.candidate_displacements_pixels_yx))
# None ambiguous_translation 15
```

The displacement describes content motion in `(y, x)` pixels. Alignment uses
its negative. For an axis of length `L`, candidates run from `-floor(L/2)`
through `ceil(L/2)-1`. A half-period shift on a length-6 axis is `-3`, including
when the image was constructed by rolling `+3`.

`normalized_rms` is the full mutable native float64 surface with the input
shape. Its rows and columns follow that signed grid, so index `(0, 0)` is
usually the most negative shift. Both images are copied to float64 and divided
by one common maximum absolute intensity. Each score is the root mean square
of all periodic pixel differences. Zero images give a zero surface.

Every candidate whose returned score minus the returned minimum is **at most**
the converted tolerance qualifies. Zero permits exact computed ties. Multiple
candidates give `displacement_pixels_yx=None` and
`failure_code="ambiguous_translation"`; the estimator never chooses among
them. Record bindings are frozen, while the independently owned surface remains
mutable. Mutating it does not recompute the other fields. Inputs are preserved.

Use plain nonempty two-dimensional NumPy arrays of real integer or floating
dtype. Strided, read-only, either-endian and extended-precision inputs are
accepted when their source and converted float64 values are finite. Conversion
rounding and underflow are allowed. Tolerance accepts a nonboolean real
Python/NumPy scalar or plain real zero-dimensional array; source and converted
values must be finite and nonnegative. Invalid images, unequal valid shapes
and invalid tolerance raise `SimreconError` with codes
`invalid_translation_images`, `incompatible_translation_shape` and
`invalid_translation_tolerance`, respectively. Both keyword arguments are
required. NumPy error mode is preserved, handled numerical operations emit no
`RuntimeWarning`, and allocation or unrelated exceptions propagate unchanged.

A sole candidate establishes uniqueness under this objective and tolerance.
It supplies no physical confidence or fit-acceptance threshold. Gain changes,
background changes, nonperiodic edges and changing specimens can produce a
unique candidate with a large residual. Different raw structured illumination
microscopy (SIM) phase frames generally change illumination intensities rather
than translate the entire image; see the
[executed comparison](../reports/translation-estimation-comparison.md).

This direct method evaluates `P` shifts using `P` pixels each: `O(P squared)`
work and `O(P)` working storage. Use modest arrays or regions of interest.
Doubling both side lengths multiplies pixels by four and direct work by sixteen.
There is no artificial size cutoff, large-image speed promise, fractional-shift
estimate, crop, mask, brightness fitting or automatic correction.
