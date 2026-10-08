# Known-phase volume separation

`separate_volume_phases` fits five real coordinates independently at each voxel:
DC, and the real and imaginary parts of two phase harmonics. Supply one
orientation as `(N, Nz, Ny, Nx)` with `N >= 5`, positive spatial dimensions and
known fundamental phases in radians. Outputs retain `(Nz, Ny, Nx)` axes and input
intensity units. A singleton z axis is valid.

This example uses eight unequal phases and distinct coefficients along all three
spatial axes. The second-harmonic basis follows the represented operations in
the [contract](../contracts/volume-phase-separation-v1.md).

```python
import numpy as np
from simrecon import VolumePhaseComponents, separate_volume_phases

phases = np.array([-0.2, 0.43, 1.21, 2.04, 2.9, 3.63, 4.57, 5.38])
z, y, x = np.indices((2, 3, 4), dtype=np.float64)
dc = 10 + z / 8 + y / 4 + x / 2
c1 = (2 + z / 4 - y / 8 + x / 16) + 1j * (-1 + z / 8 + y / 4 - x / 16)
c2 = (3 - z / 8 + y / 16 + x / 4) + 1j * (4 + z / 4 - y / 16 - x / 8)
c = np.cos(phases)[:, None, None, None]
s = np.sin(phases)[:, None, None, None]
images = dc + 2 * c1.real * c - 2 * c1.imag * s
images += 2 * c2.real * (c * c - s * s) - 2 * c2.imag * ((2 * c) * s)
components = separate_volume_phases(images, phases_rad=phases)
assert isinstance(components, VolumePhaseComponents)
assert components.dc.shape == (2, 3, 4)
np.testing.assert_allclose(components.dc, dc, rtol=0, atol=1e-12)
np.testing.assert_allclose(components.c1, c1, rtol=0, atol=1e-12)
np.testing.assert_allclose(components.c2, c2, rtol=0, atol=1e-12)
print(components.dc[0, 0, 0], components.c1[0, 0, 0], components.c2[0, 0, 0])
```

The executed example returns approximately `10`, `2-1j`, and `3+4j` at the first
voxel. Its execution and a separate high-precision stored-input comparison are
recorded in the [measured report](../reports/volume-phase-separation-comparison.md).

Only `images` is positional; `phases_rad` is required and keyword-only. Both
inputs must be plain NumPy arrays with integer or floating dtype, finite before
and after float64 conversion. Signed data, either byte order, strided and
read-only inputs work. Lists, subclasses, masked arrays, bool and complex data
are rejected. Inputs are copied before trigonometric or numerical processing.
Returned bindings are frozen, but each independently owned array is mutable:
native float64 `dc`, and native complex128 `c1` and `c2`.

The unweighted float64 singular value decomposition (SVD) fit accepts full
numerical rank five with no extra conditioning cap. Unequal phases generally
make fitted DC differ from the arithmetic mean. Overdetermined off-model data
receive a least-squares projection with a possible nonzero residual. Negative
phase orders can be formed with `components.c1.conj()` and
`components.c2.conj()`.

Angles are evaluated directly, without rounded-period reduction or doubling;
the second harmonic uses `c*c-s*s` and `(2*c)*s`. Finite huge phases are valid,
subject to numerical rank. The contract defines accuracy on the represented
matrix for `cond_2(H) <= 10`; weakly identified full-rank sets have no uniform
digit guarantee. Range applies separately to all five returned real coordinates.
Underflow is allowed; a nonfinite final coordinate rejects the whole call with
`SimreconError`. Stable rejection codes are listed in the contract. Allocation
failures and unrelated exceptions propagate; the caller's NumPy error mode is
preserved.

These are phase components of the observed volume. The operation does not
recover a specimen, separate seven three-beam spatial components, calibrate
axial orders or perform 3D reconstruction. It adds no spatial transform,
normalization, phase estimation or drift correction. Existing 2D
`separate_phases` remains a separate operation.
