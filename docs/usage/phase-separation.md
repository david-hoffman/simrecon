# Separate three known phases

`separate_phases` accepts three equally spaced phase images in a plain NumPy
array with axes `(phase, y, x)`. Supply the first phase explicitly in radians;
the next two phases are separated by `2*pi/3` rad.

```python
import numpy as np
from simrecon import separate_phases

# A=10, B=4, C=2 in I_p=A+B*cos(phi_p)+C*sin(phi_p).
images = np.array([14, 8 + np.sqrt(3), 8 - np.sqrt(3)])[:, None, None]
components = separate_phases(images, phase_offset_rad=0.0)
# components.dc is approximately [[10.0]].
# components.c1 is approximately [[2.0 - 1.0j]].
```

For `phi_p = phase_offset_rad + 2*pi*p/3`, the coefficients are

```text
dc = (I_0 + I_1 + I_2)/3
c1 = sum_p(I_p * exp(-i*phi_p))/3
I_p = dc + 2*Re(c1 * exp(i*phi_p))
```

The negative exponential defines the phase sign. For
`I_p=A+B*cos(phi_p)+C*sin(phi_p)`, the result is `dc=A`, `c1=(B-i*C)/2`.
The sanity example has mean `(14+8+sqrt(3)+8-sqrt(3))/3=10`.
Both coefficients retain the input intensity units and spatial sampling.
This operation separates phase coefficients in image space. It performs no
modulation-depth correction, optical blur correction or high-resolution reconstruction.

The array must have shape `(3, positive_y, positive_x)` and dtype uint16,
float32 or float64. Either byte order, noncontiguous storage, read-only storage
and signed finite intensities are accepted. Lists and ndarray subclasses are
rejected without coercion. Integer and float32 values convert exactly to
float64 before arithmetic.

The required keyword-only offset accepts Python and NumPy integer/floating
scalars, excluding booleans. Its float64 conversion must be finite and in
`[-pi, pi]`, including both endpoints. Normalize other equivalent angles
before calling; separation does not estimate or infer a phase.

`PhaseComponents` exposes `dc` and `c1`. Their shape is `(y, x)`; their dtypes
are native float64 and complex128. Both arrays own independently allocated,
C-contiguous, mutable storage. The input is unchanged. The record binds the
attributes but does not freeze the arrays or validate direct record construction.

Per-pixel power-of-two scaling keeps finite near-limit inputs from overflowing
intermediate arithmetic and preserves small pixels alongside bright pixels.
The mean is confined to the input range before restoring the exponent.
There is no extra intensity or image-size ceiling. For
`M=max(abs(images))`, each real component error is bounded by
`T=64*2^-52*M+8*2^-1074`, using independently derived truth for the stored values.
The subnormal term has no fixed intensity-unit floor. Allocation failures
retain normal `MemoryError` behavior.

Domain errors use the existing `SimreconError`, a `ValueError` subclass with
string `code` and `message`. Invalid objects, dtypes, shapes, nonfinite images
and invalid offsets respectively use `invalid_phase_images`,
`invalid_phase_dtype`, `invalid_phase_shape`, `nonfinite_phase_images` and
`invalid_phase_offset`. Validation precedence for multiple invalid obligations
is unspecified. Missing or positional offsets retain ordinary argument-binding
`TypeError` behavior.

See the [approved contract](../contracts/known-phase-separation-v1.md) and the
[actual analytic comparison](../reports/phase-separation-comparison.md) for
the signed component panels, errors, resynthesis residuals and provenance.
