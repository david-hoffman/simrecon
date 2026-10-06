# Three-phase 2D separation public contract

**Version 1.0. Proposal 2, owner-approved October 5, 2026.** [NF02](../tasks/known-phase-separation.md) counts the scenarios; [the slice plan](../tasks/numerical-foundations-plan.md#current-state) owns the actual approval and accounting. This specification defines approved scientific behavior; current delivery state and exact-candidate evidence are recorded by the slice plan and its linked PR/conversation.

The owner subsequently requested variable phase count, explicit possibly unequal phase angles and broader real dtypes. The [version-2 amendment draft](known-phase-separation-v2.md) records that direction and remaining numerical decisions. This version describes the tested historical candidate on PR #5, not the intended generalized API.

## Scope and approved public interface

One channel/time point, one orientation, one 2D plane at each of three equally spaced known phases. Callers select the three images and provide the phase offset explicitly. File plane indices are ordinal labels and do not supply phase angles. No phase estimation, OTF handling, spatial Fourier transform, band shifting, reconstruction, file adapter, CLI, brightness correction or metadata mutation is included.

```python
from simrecon import PhaseComponents, separate_phases

components = separate_phases(images, phase_offset_rad=offset)
components.dc
components.c1
```

`separate_phases(images, *, phase_offset_rad)` requires both inputs. `images` is a plain NumPy ndarray with exactly three dimensions and shape `(3, y, x)`, with positive integer `y` and `x`. Its dtype is uint16, float32 or float64, with either byte order. Array subclasses and implicit coercion of lists/other array-like objects are outside scope and rejected as `invalid_phase_images`; no subclass mask or unit meaning is silently interpreted. Noncontiguous and read-only plain arrays are permitted. Floating values must all be finite; signed intensities are permitted and no positivity constraint is inferred from camera data.

`phase_offset_rad` is a Python or NumPy real integer/floating scalar, excluding booleans. It must convert to a finite float64 value in the inclusive interval `[-pi, pi]`. This explicit principal-interval limit avoids a promise about reduction of arbitrarily large phase arguments; callers normalize other equivalent phase offsets themselves. Phase spacing is exactly `2*pi/3` radians in the mathematical model. No default offset is inferred from image indices, filenames or acquisition metadata. Ordinary Python argument-binding errors retain `TypeError`.

## Mathematical meaning and units

For `p=0,1,2`, define `phi_p = phi_0 + 2*pi*p/3`, where `phi_0` is the explicit offset in radians. At every `(y,x)` position:

```text
dc = (I_0 + I_1 + I_2) / 3
c1 = sum_p(I_p * exp(-i * phi_p)) / 3
I_p = dc + 2 * Re(c1 * exp(i * phi_p))
```

The input is real. `dc` is its zero-order phase coefficient; `c1` is the coefficient of `exp(+i*phi)`, with the negative exponential in separation. The conjugate coefficient is implied by real input and need not be returned as another allocated array. These coefficients are still at the acquired spatial sampling. They are phase coefficients in image space, not already shifted spatial-frequency bands or a reconstructed image. No modulation-depth division or background subtraction is performed.

Input and both coefficients have the same intensity units. The operation does not assign physical length/frequency units or multiply by pixel area. It carries no acquisition descriptor and changes no sampling. Future reconstruction/calibration contracts must separately define spatial Fourier axes/sign/normalization, frequencies in inverse micrometres, weighting and output sampling; this contract settles only the phase transform.

## Independent expected results

Let `r = exp(2*pi*i/3)`. The identities `r^3=1` and `1+r+r^2=0` establish separation independently of any implementation. For a declared analytic signal

```text
I_p = A + B*cos(phi_p) + C*sin(phi_p)
dc = A
c1 = (B - i*C)/2
```

Sanity check: `A=10`, `B=4`, `C=2`, `phi_0=0` gives the three observations `14`, `8+sqrt(3)`, `8-sqrt(3)`. Their mean is `(14+8+sqrt(3)+8-sqrt(3))/3=10`; the first coefficient is `2-i`. A constant signal gives `dc=A` and `c1=0`. Nonzero known offsets must recover the same declared `A`, `B` and `C`; they do not introduce a different coefficient convention.

For independently supplied or rounded stored input values, an equivalent closed form is

```text
c1 = exp(-i*phi_0) * (2*I_0 - I_1 - I_2
                         + i*sqrt(3)*(I_2 - I_1)) / 6
```

Expected results use the actual stored values after exact uint16/float32-to-float64 conversion. They do not compare quantized images to an unquantized generating signal as though quantization were an implementation defect. The formulas are mathematical oracle definitions, not permission to use the product implementation to create expected results. Test authors derive independent examples and justified tolerances from these public inputs; historical reconstructed images are not ground truth.

The [Gustafsson 2000 article](https://onlinelibrary.wiley.com/doi/10.1046/j.1365-2818.2000.00710.x), sections “Extended resolving ability,” “Acquisition” and “Processing,” motivates arithmetic separation of phase-varied images and reports three exposures spaced by 120 degrees. It does not prescribe this Python API, dtype/error policy or coefficient normalization. Those are project choices in this proposal. The [FFTW transform definition](https://www.fftw.org/fftw3_doc/The-1d-Discrete-Fourier-Transform-_0028DFT_0029.html) supplies a primary convention comparison: forward negative exponential and unnormalized transforms. The explicit division by three here is our choice, and no FFTW dependency is selected. Both links were opened during October 5 intake. [Local Docling evidence](../references/scientific/gustafsson-2000/full-text-extraction.json) records the article text, inline notation and captions separately from the historical citation-only conversions. Paper figure-pixel capture is outside scope.

## Human visual reference and final comparison

Use a deterministic asymmetric intensity object `A(y,x)` with bright landmarks, bars and a curved feature, under a declared diagonal carrier `theta(y,x)`. For example, set `m=0.8`, `phi_0=pi/6` and

```text
I_p = A * (1 + m*cos(theta + phi_p))
expected dc = A
expected Re(c1) = m*A*cos(theta)/2
expected Im(c1) = m*A*sin(theta)/2
```

Here `B=m*A*cos(theta)` and `C=-m*A*sin(theta)`, so the expected components follow the earlier independent identity directly. These are noiseless analytic intensity images, with no optical-blur or camera model. They test/illustrate phase separation; they do not claim full microscopy reconstruction. Intensities use arbitrary units and carrier frequency is explicitly in cycles per pixel. Shape, carrier, landmarks, modulation and phase values are recorded so orientation/phase/gain errors are visible and reproducible.

[Analytic intake preview](../figures/phase-separation-analytic-preview.png) shows inputs and expected components only. It calls no SIMrecon operation and is not a reviewed fixture or observed recovery result.

The final NF02 human report must contain:

1. Three input phase images with one shared grayscale/intensity range.
2. Expected and actual recovered `dc`, `Re(c1)` and `Im(c1)` with identical expected/recovered scales; signed components use a shared zero-centred diverging scale. Do not show only complex magnitude, which loses sign/phase information.
3. Absolute component-error maps with stated scales, maxima and the declared numeric tolerance. Do not independently rescale each panel or clip errors without an explicit overflow indication.
4. All three forward-resynthesized input residuals, using `dc + 2*Re(c1*exp(i*phi_p))`, with stated maximum errors. This is a consistency check alongside independent component truth, not a substitute for it.
5. The actual candidate identity, command, input/expected-array identities and analytic parameters, plus an explicit status saying this is phase separation rather than a reconstructed high-resolution image. Keep the final candidate's own hash/check results in conversation/PR or a local ignored provenance sidecar outside its tracked tree, linked to the visual report.

A independently authors the analytic fixture and expected arrays, and B reviews them before C. The final panels use real public-API output from the tested candidate; generation may not manufacture a recovery image or modify the frozen ground truth. D checks the report's correspondence. The quantitative tests remain the ground-truth gate; human judgment can prompt investigation but cannot override a numerical failure. No golden-image/screenshot acceptance test is added.

## Output, ownership and numerical limits

Return a `PhaseComponents` record with public attributes `dc` and `c1`. Each has shape `(y,x)` in the input spatial order. `dc` is a native-endian C-contiguous owned float64 ndarray; `c1` is a native-endian C-contiguous owned complex128 ndarray. The two arrays do not share memory with the input or each other. The caller may mutate the returned arrays without altering the original input. Inputs, including their data/shape/dtype/writeability, are not mutated on success or rejection. Record construction is not a separate validating numerical API.

Uint16 and float32 convert to their exact float64 values before separation. Arithmetic uses float64/complex128; there is no integer accumulation or output downcast. No input-value/size ceiling beyond the declared dtype/shape and available allocation is added. For any permitted finite data, the mathematically bounded coefficients must remain finite even near the float64 range limit; avoid intermediate overflow. Allocation failures retain ordinary `MemoryError`. No file I/O or successful partial result occurs.

Let `M=max(abs(I_p[y,x]))` across the input, `eps=2^-52`, and `u=2^-1074`, the smallest positive float64 subnormal. For independently justified expected values, each real `dc` error and each real/imaginary `c1` component error must be no more than `64*eps*M + 8*u`. Evaluate the scale without overflowing. This scale-aware roundoff allowance permits cancellation near zero and subnormal rounding without a fixed intensity-unit floor; it does not allow sign or factor-of-two mistakes. A explains its numerical comparison and B checks legitimate variation against the chosen examples. No throughput, whole-acquisition memory, or reconstruction-quality claim is made. The operation's working set may scale with its three input planes and outputs; it does not read an entire acquisition implicitly.

## Rejections and compatibility

Use the existing public `SimreconError` (`ValueError` subclass with string `code`/`message`) for domain errors. Exact human-readable prose is not contractual.

| Violated obligation | Stable code |
|---|---|
| Input object is not a plain NumPy ndarray | `invalid_phase_images` |
| Dtype is outside uint16/float32/float64 | `invalid_phase_dtype` |
| Shape is outside `(3, positive_y, positive_x)` | `invalid_phase_shape` |
| Any image value is NaN or infinite | `nonfinite_phase_images` |
| Offset is not a permitted real scalar, is not finite or is outside `[-pi,pi]` | `invalid_phase_offset` |

Tests isolate one invalid obligation at a time. When more than one is invalid, rejection is required but validation precedence/message is unspecified. Ordinary unexpected resource failures retain ordinary exception behavior; no generic exception masking. Existing `inspect`, `read`, `harmonize`, `write` and conversion CLI contracts remain unchanged.
