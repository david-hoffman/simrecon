# Estimate a scalar camera response from images

The [camera calibration contract](../contracts/scalar-camera-calibration-v1.md) estimates finite image statistics from three repeated primary-camera acquisitions:

- Dark: zero-light exposures.
- Blank: no fluorescent object signal, with the background used for the paired experiment.
- Flat: spatially uniform illumination added to that same background.

The model assumes one stationary scalar offset, gain and read noise, independent pixels/frames, and a constant expected intensity within each group. Labels assert acquisition conditions; the estimator cannot certify those conditions from the data. Illumination levels and camera coefficients are not inputs.

## Estimate and inspect

Each group has axes (frame,y,x), at least two frames and at least two pixels per frame. Groups share y/x dimensions; frame counts may differ. Negative raw counts are permitted.

This small synthetic example creates observations first. Only the resulting count arrays enter the estimator; generation settings are not estimator arguments.

~~~python
import numpy as np
from simrecon import estimate_scalar_camera

rng = np.random.default_rng(20261023)
shape = (8, 64, 64)

dark = 100.0 + 2.0 * rng.normal(size=shape)
blank = 100.0 + 2.0 * (
    rng.poisson(10.0, size=shape) + rng.normal(size=shape)
)
flat = 100.0 + 2.0 * (
    rng.poisson(1010.0, size=shape) + rng.normal(size=shape)
)

estimate = estimate_scalar_camera(
    dark,
    blank_counts=blank,
    flat_counts=flat,
    source="synthetic camera illustration",
)
print(estimate.means_counts)       # dark, blank, flat; counts
print(estimate.variances_counts2)  # mean within-frame variances; counts²
print(estimate.contrast_counts)
print(estimate.gain_counts_per_e)
print(estimate.information_codes)
~~~

For each group, the operation averages frame means and the within-frame sample variances with divisor K−1, where K is pixels per frame. It does not pool different frames before computing variance.

Let M and V denote the returned group means and variances. The finite gain statistic is

~~~text
gain = (V_flat - V_blank) / (M_flat - M_blank).
~~~

It is available only when both returned contrasts are positive and the quotient is representable and positive. This is a finite-sample ratio, with no unbiasedness or instrument-accuracy guarantee. Frame moments and an empirical standard error of each group mean remain available for inspection.

## Correct in reference-flat-relative units

A positive mean contrast supports linear normalization even when physical electron gain is unavailable:

~~~text
relative_signal = (raw_counts - M_blank) / (M_flat - M_blank).
~~~

The blank mean maps to zero and the reference flat mean maps to one in this calibration's observed gauge. Use the blank mean as the offset; subtracting only the dark mean would retain mean photon background. Background shot noise remains after subtraction.

For an already [declared raw acquisition](raw-acquisition-declarations.md), use the existing [linear correction](linear-response-correction.md):

~~~python
from simrecon import correct_linear_response

if estimate.contrast_counts > 0.0:
    corrected = correct_linear_response(
        acquisition,
        offset=float(estimate.means_counts[1]),
        response=estimate.contrast_counts,
        output_unit="reference_flat_relative",
    )
~~~

Here response has units counts per reference-flat-relative unit. It is not supplied as a true counts/electron calibration. Preserve the estimator identity and image-acquisition provenance alongside the corrected data.

Nonpositive mean or variance contrasts, an unrepresentable gain, and a negative estimated background are explicit information codes. They do not automatically make every other returned statistic unusable. A nonpositive mean contrast makes the stated normalization unavailable. Inspect the codes rather than substituting true simulator values.

This operation estimates no phase, carrier, optical response, drift or spatial camera map. Its scalar stationary assumptions and the later optical calibration must be checked separately. Binding fields are frozen; returned arrays are independently owned and writable. Retain original raw observations for reproducibility.
