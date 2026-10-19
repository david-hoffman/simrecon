# Estimate periodic volume translation against a reference

Supply comparable, equal-intensity volumes in z/y/x order. The operation
compares every integer periodic shift using every voxel. It returns content
motion in voxels; alignment uses the negative displacement. Physical voxel
spacing is not an input.

```python
import numpy as np
from simrecon import estimate_volume_translation

reference = np.zeros((3, 4, 5), dtype=np.float64)
reference[0, 1, 2] = 7
reference[2, 3, 1] = 3
moving = np.roll(reference, (1, -1, 2), axis=(0, 1, 2))
result = estimate_volume_translation(
    moving, reference=reference, ambiguity_tolerance=0.0
)
print(result.displacement_voxels_zyx)
print(result.minimum_normalized_rms)
print(result.failure_code)
if result.displacement_voxels_zyx is not None:
    aligned = np.roll(
        moving, tuple(-d for d in result.displacement_voxels_zyx), axis=(0, 1, 2)
    )
    print(np.array_equal(aligned, reference))
```

The expected output is `(1, -1, 2)`, `0.0`, `None`, and `True`, each on its
own line. The synthetic shift constructs this example; the estimator receives
only moving, reference, and tolerance.

For P voxels and common scale B equal to the maximum absolute intensity across
both converted volumes, each score is the square root of the mean squared
difference between periodically shifted moving/B and reference/B. B=0 gives
zero scores. This dimensionless normalized root mean square (RMS) mismatch
retains gain, background, and structural differences. No intensity fit occurs.

`normalized_rms` is an independently owned, mutable native float64 array with
the input shape. Each length D axis is ordered from -floor(D/2) through
ceil(D/2)-1, including the negative representative of an even half-period.
The frozen result also contains its actual minimum and every canonical
candidate whose actual score minus that minimum is less than or equal to the
explicit tolerance. Candidates increase in z, then y, then x. Multiple
candidates give displacement `None` and failure code
`ambiguous_volume_translation`; no preferred tie is selected.

Inputs must be plain nonempty three-dimensional NumPy arrays of equal shape,
with real integer or floating dtypes. Either endian, strided, Fortran, signed,
and read-only arrays are accepted. Values must be finite before and after
float64 conversion; conversion rounding and underflow are allowed. Caller
storage is preserved. Singleton axes are valid, and a single voxel always has
one candidate, even with poor fit. The tolerance must be a nonboolean real
Python/NumPy scalar or plain real zero-dimensional array, finite and
nonnegative before and after conversion. Zero, negative zero, and large
tolerances are valid.

Invalid image representations raise `SimreconError` with code
`invalid_volume_translation_images`; unequal otherwise valid shapes use
`incompatible_volume_translation_shape`; invalid tolerances use
`invalid_volume_translation_tolerance`. Ordinary argument-binding errors remain
`TypeError`. Allocation and unrelated exceptions propagate unchanged.

This direct method costs O(P squared) work and O(P) working storage. Use modest
volumes or regions of interest; no full-frame feasibility is claimed. The
per-score numerical allowance is 4096 P 2**-52 against the stored-input
objective. It is separate from the caller's ambiguity tolerance and supplies
no physical accuracy threshold. Boundary decisions use the actual same-call
scores. A unique optimum can have poor fit and establishes neither physical
motion nor fit acceptance. Fractional/nonperiodic motion, bleaching,
comparable-reference construction, and drift inference from different raw
structured illumination microscopy phases remain outside this operation.

The existing 2D `estimate_translation` operation remains separate. See the
[approved volume contract](../contracts/volume-translation-estimation-v1.md)
for the complete representation, error, and numerical guarantees.
