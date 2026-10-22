# Synthetic camera sampling v1

**Version 1.0.** NS01 of the owner's October 22, 2026 full noisy simulation. This is a synthetic camera model, not a measured camera claim. It creates no reconstruction/calibration estimator, file writer, clipping, quantization, saturation, bad-pixel, motion or bleaching behavior.

## Public tool boundary and equations

The in-repository module scripts/simulation_camera.py exposes:

```python
sample_camera(
    expected_signal_e,
    *,
    background_e,
    read_noise_e,
    gain_counts_per_e,
    offset_counts,
    seed,
    shot_noise=True,
) -> numpy.ndarray
```

For each sample, normalize inputs to native binary64 and define lambda = expected_signal_e + background_e in electrons per pixel per exposure. If shot_noise=True, independently draw P from Poisson(lambda); otherwise set P=lambda. Independently draw R from Normal(mean=0, standard deviation=read_noise_e), also in electrons. Return C=offset_counts + gain_counts_per_e*(P+R), using sequential native binary64 arithmetic: form P+R, multiply by gain, then add offset. No clipping, magnitude, positivity constraint, quantization, saturation or output normalization is allowed. Negative finite raw values from Gaussian noise are legitimate.

Thus E[C]=offset+gain*lambda. With photon noise Var(C)=gain²*(lambda+read_noise_e²); without photon noise Var(C)=gain²*read_noise_e². These mathematical moments and deterministic limits are independent expectation sources. Background participates in photon shot noise. Noise draws are independent across samples and sources within the model.

The reference distributions are [NumPy Poisson](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.poisson.html) and [NumPy normal](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html), opened October 22, 2026. The contract selects the physical combination and boundaries; product output supplies no oracle. Statistical tests derive and disclose appropriate finite-sample uncertainty/multiple-comparison controls, use predetermined seeds and do not cherry-pick passing realizations. No instrument accuracy threshold is selected here.

## Input domain

expected_signal_e is a plain NumPy ndarray, rank at least one, every axis nonempty, dtype kind i/u/f, with finite nonnegative samples after native float64 normalization. Strided, Fortran-order, big-endian and read-only arrays are permitted. Boolean/complex/object/string/datetime/structured arrays, ndarray subclasses/masked arrays, lists, scalar values, rank-zero and empty arrays are rejected. Conversion can round integers/wider floats; pixel-bit fidelity is not promised. Values rounded to finite zero are valid. Samples that are originally nonfinite or cannot normalize to finite binary64 are invalid.

The four numeric keyword coefficients are plain built-in int/float excluding bool. They must normalize to finite binary64. background_e and read_noise_e are nonnegative, including signed zero; gain_counts_per_e is strictly positive; offset_counts may be any signed finite value. No implicit array broadcasting or NumPy-scalar coefficient boundary is selected.

seed is a plain built-in nonnegative int, excluding bool; there is no arbitrary maximum. shot_noise is a plain built-in bool. All coefficients, seed and noise mode are explicit except the documented True default for shot_noise. Ordinary missing/unknown argument binding remains Python TypeError. Simultaneous invalid-input precedence and exact diagnostic prose are unspecified.

## Ownership, reproducibility and failure

Return one complete independently owned, C-contiguous, native float64 plain ndarray with the input shape. Inputs remain unchanged on success and rejection. Mutable output must not alias caller input. Use a per-call seeded local random stream; never consume or reseed NumPy's legacy/global RNG. The same normalized inputs, seed, mode and recorded NumPy/bit-generator implementation reproduce the same result; no cross-version bitstream guarantee, exact draw-order oracle or distinct-seed difference for a zero-noise case is selected. A seeded call is repeatable without imposing its arrays on another seed.

Use a local NumPy Generator with PCG64. The stochastic law, moments, independence and repeatability are promised; a particular array from one internal call order is not a frozen public fixture. Statistical behavior and exact zero-noise limits must be assessed independently of a duplicate production RNG recipe.

Use the existing public SimreconError with these codes:

| Outcome | Code |
|---|---|
| Unsupported/invalid signal array, coefficient, seed or noise-mode domain above | invalid_simulation_camera |
| Finite normalized signal/background whose specified lambda addition is nonfinite; unsupported Poisson draw range for finite lambda; nonfinite P+R, gain product or offset sum | simulation_camera_range |

NumPy documents Poisson's finite integer-output range. A finite lambda not drawable by its Poisson implementation is an operation-range failure when shot_noise=True; that same finite lambda remains permitted in the shot_noise=False deterministic mode if the defined intermediates stay finite. Do not impose a hidden common lambda cap or substitute a Gaussian approximation. A random draw range ValueError is translated to simulation_camera_range; allocation MemoryError and unrelated exceptions propagate unchanged. No successful partial output is returned.

Preserve caller numpy error settings. Expected normalization/arithmetic overflow/underflow and selected draw-range handling emit no arithmetic RuntimeWarning or FloatingPointError, regardless of caller settings. Finite subnormal/underflow-to-zero results are allowed. Suppress no unrelated warning categories. No concurrent external mutation guarantee is selected.

The operation owns its output and ordinary O(number of samples) scratch. It promises no whole-workflow memory cap. Full generator callers may invoke it on deterministic, recorded exposure chunks; chunk-boundary invariance is not selected. Each chunk needs its own recorded deterministic seed/stream identity, with independence assessed at the caller boundary later.

## Observable scenario inventory

| ID | Distinct obligation / plausible wrong outcome to distinguish |
|---|---|
| N01 | Zero photon/read noise yields exact sequential mean camera relation, retaining units, shape and signed offset |
| N02 | Photon-only sampling has Poisson signal-plus-background mean/variance; background is not a noiseless offset |
| N03 | Read-only sampling has declared Gaussian standard deviation, independent sample draws and signed values |
| N04 | Combined independent noise has variance lambda+sigma² before gain; gain squares in variance and offset changes only mean |
| N05 | Predetermined seeded repeatability/local stream leaves global RNG untouched; deterministic cases need not differ by seed |
| N06 | Supported layout/dtype normalization, finite precision and independent owned output; inputs unchanged on success/failure |
| N07 | Invalid signal type/rank/emptiness/dtype, negative/nonfinite/unrepresentable values rejected |
| N08 | Explicit coefficient domains and legitimate zero/background/noise, subnormal positive gain and signed offsets |
| N09 | Exact seed/bool-mode domain; Python binding errors remain ordinary TypeError |
| N10 | Lambda sum overflow and Poisson-range failure; paired large finite deterministic mode remains admissible |
| N11 | Sequential electron-sum/gain-product/offset-add range failures reject whole call; ordinary underflow is accepted |
| N12 | Caller NumPy error policy restored, expected arithmetic warnings contained and unrelated/allocation failures unaltered |
| N13 | Real simulator-use composition with independent photon-budget/camera correction arithmetic; no truth-calibration or reconstruction claim |

Equivalent shapes, values and seeds are coverage examples, not new rules. A maps these obligations and risk paths to public-entry tests and independently justified oracles; B audits missing cases and permitted positives. No tests solely to force percentages. This contract preserves the task's binding native coverage/report/gate choice and all unrelated interfaces, locks, tests and policy. It does not complete the full simulation.
