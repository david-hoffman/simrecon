# Replay a finite source and describe its errors

The development module `scripts.reference_alignment_ra14_comparison` supplies two
in-memory operations. `replay_source` applies the existing physical inverse
operator to a supplied source. `compare_arrays` reports signed, full-array errors.
Neither operation estimates camera or illumination parameters or fits a source.
The [contract](../contracts/reference-alignment-ra14-v1.md) defines their boundaries.

Run this example from the locked development checkout using `.venv/bin/python`:

```python
import dataclasses

import numpy as np

from scripts.reference_alignment_ra14_comparison import compare_arrays, replay_source

source = np.zeros((1, 2, 2), dtype=np.float32)
source[0, 0, 0] = 1.0
prediction = replay_source(
    source,
    source_spacing_um_zyx=(0.125, 0.04, 0.04),
    carriers_yx_per_um=np.zeros((3, 2), dtype=np.float64),
    phases_at_specimen_origin_rad=np.zeros((3, 5), dtype=np.float64),
    beam_amplitudes=np.array([1.0, 0.0, 0.0], dtype=np.float64),
    pupil_order=1,
)
print(prediction.shape, prediction.dtype)

metrics = compare_arrays(
    np.array([0.0, 0.0, -2.0, -1.0], dtype=np.float32),
    np.array([3.0, -4.0, 0.0, 0.0], dtype=np.float64),
)
print(dataclasses.asdict(metrics))
```

The executed example returns native float64 shape `(3, 5, 1, 1, 1)`, with all
15 values equal to approximately `0.1279016193298208`. This central-only Q1
example demonstrates argument wiring; it establishes no reconstruction accuracy.

For the four-element metric example, error means estimate minus reference:
`[-3, 4, -2, -1]`. Thus the reference L2 norm is 5, error L2 norm is √30,
relative L2 error is √30/5 ≈ 1.09544511501, root-mean-square error is √30/2,
maximum absolute error is 4 and signed mean error is −0.5. Count is exactly 4.
These are descriptive metrics, with no acceptance threshold or fitted scaling.

Source values are integrated reference-flat-relative weights. Replay passes them
unchanged through one existing clear-pupil cache and all three orientation calls,
using every supplied phase and beam amplitude. Output axes are
orientation/phase/z/y/x. Carrier units are cycles/µm; phases are radians at the
specimen origin. Replay applies no camera correction, origin transfer or intensity
normalization. Preserve the original fit status when replaying a retained partial
source; producing predictions does not promote that source to a completed fit.

Metrics accept nonempty, same-shaped finite native float32/float64 arrays,
including mixed widths, strided/read-only inputs and scalars. Each representable
final statistic remains available even when intermediate subtraction or sums would
overflow. Exactly zero reference makes only relative L2 unavailable, with reason
`zero_reference`; other genuinely unrepresentable final statistics use
`unrepresentable`. Missing statistics are `None`, never nonfinite sentinels or
epsilon-adjusted values. The frozen record names every unavailable field.

Invalid composition inputs raise `invalid_reference_alignment_ra14` with a field
diagnostic. Existing operator errors and unrelated exceptions propagate unchanged.
Inputs and caller warning, NumPy error and random policies are preserved. This
development module adds no file format, command-line operation or installed-wheel
API. The [full-scene report](../reports/reference-alignment-ra14.md) distinguishes
finite procedure outcomes from source recovery and resolution evidence.
