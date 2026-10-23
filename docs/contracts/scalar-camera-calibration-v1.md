# Scalar camera calibration from primary-camera images v1

Version1.0. Adopted task contract under the owner's full noisy simulation request and explicit images-only choice. This is a synthetic scalar ensemble model, not measured instrument calibration or a proof of phase/carrier identifiability. It adds no extra sensor, known flux, true camera coefficient, bead profile or emitter position input.

## One public operation and its purpose

Export the additive library operation from simrecon:

~~~python
estimate_scalar_camera(
    dark_counts,
    *,
    blank_counts,
    flat_counts,
    source,
) -> ScalarCameraEstimate
~~~

Only dark_counts is positional. All keywords are required. Each input is a raw repeated stack with axes (frame,y,x), in the same detector-count unit. No known illumination level, physical gain, offset, noise standard deviation, electron calibration, seed or truth record is accepted. The operation is deterministic, pure in-memory estimation of the finite statistics below. It performs no simulation, phase/carrier inference, correction of a specimen, optical calibration, persistence or file I/O.

The primary downstream normalization is reference-flat-relative counts. It does not require a successful physical electron-gain estimate. The physical gain statistic is reported separately when informative.

## Explicit acquisition and distribution assumptions

The selected model is the approved NS01 law C=o+g*(P+R), with independent P~Poisson(lambda) and R~Normal(0,sigma_e^2), g>0. Counts may be negative because read noise is not clipped. The same unknown scalar o, g and sigma_e apply to every calibration group and the later paired bead/specimen run. No spatial gain/offset map, bad-pixel handling, quantization, saturation, bleaching, temporal correlation or exposure rescaling is inferred.

Acquire these three explicitly labeled, stationary ensembles:

- Dark D: shutter/illumination closed, lambda_D=0. This is a zero-light acquisition condition, not a supplied numerical offset or measured phase.
- Blank B: no fluorescent specimen/bead signal, with the same stationary photon background b>=0 as the paired optical run; lambda_B=b.
- Flat F: spatially uniform, steady unstructured illumination, with the same b and an unknown added level s_ref>=0; lambda_F=b+s_ref.

Within each group the expected level is constant across frames and pixels; draws are independent under NS01. Its value is unknown to the estimator. No expected per-frame or per-pixel electron array is supplied. Spatial texture, intensity flicker, different background/exposure conditions, correlated pixels and fixed-pattern effects violate this selected ensemble model; the operation does not certify their absence from finite data. Frame summaries expose variation, but no uncontracted stationarity test or hidden rejection threshold is added.

Dark/blank/flat groups are explicit additional primary-camera acquisitions within the images-only route. They are distinct from prohibited phase/carrier metrology. The labels assert acquisition conditions, not true nuisance values. If a future run cannot supply these conditions, this contract is inapplicable; do not fill its inputs with simulator coefficients.

### Selected first synthetic acquisition

Use 8 independent two-dimensional exposures in each group, shape (8,512,512), with no z/orientation/phase repetitions. Store native float64 counts. There are 24 frames total and exactly 24*512*512*8=50,331,648 bytes=48 MiB of raw array payload. Small metadata, seed manifests and compact reports are additional; no compression ratio is assumed. No writer is included here. Stage smaller frames first; the operation itself permits other legal sizes.

Generate these images with the existing scripts/simulation_camera.py sample_camera interface. Dark uses zero expected signal and zero optical background. Blank uses zero expected specimen signal and the selected background trial. Flat uses a fixed, spatially uniform positive expected signal for that group plus the same background. Use separate predetermined streams. All actual camera coefficients and electron illumination levels stay in evaluator-only records. A practical initial generator-only flat level is 1000 expected signal electrons per pixel per exposure; it is not an estimator argument or inverse metadata. The existing background/read-noise trial cases may each have their own separately paired calibration groups.

No 3D calibration array, duplicate full workflow, external sensor or new hardware model is required. The 48 MiB plan is an explicit synthetic acquisition choice, not a human-set resource limit or general memory guarantee.

## Input representation

Each group is a plain NumPy ndarray, dtype kind i/u/f, rank three, at least two frames, positive y/x, and K=Ny*Nx>=2. All groups have the same y/x dimensions; frame counts may differ. Signed raw counts, supported widths/endian variants, strided/Fortran/read-only arrays and conversion rounding/finite underflow are permitted. Reject bool/complex/object and other kinds, subclasses/masked arrays, nonarrays and nonfinite original values or values not representable as finite float64.

Normalize independently to native float64 and snapshot all three groups before moment computation. Converted values define the finite estimator. Preserve caller contents/layout/write flags and NumPy error/warning policies. No concurrent external mutation guarantee is selected. Source is an unchanged nonblank opaque string; it authenticates no acquisition condition. No arbitrary shape/count/intensity cap is selected.

These stacks are accepted directly. Do not mislabel dark/blank/flat repeats as phase, z or SIM orientation merely to fit RawAcquisition's present kind/axis grammar. Later paired specimen/bead acquisitions continue to use declare_acquisition normally.

## Exact finite-sample estimator

Let groups be ordered (D,B,F). Let T_G be frame count and K be pixels per frame. Interpret normalized float64 samples C_Gti as exact real numbers for the expectation source. Define:

~~~text
m_Gt = (1/K) * sum_i C_Gti
v_Gt = (1/(K-1)) * sum_i (C_Gti-m_Gt)^2
M_G  = (1/T_G) * sum_t m_Gt
V_G  = (1/T_G) * sum_t v_Gt
Delta_M = M_F-M_B
Delta_V = V_F-V_B
background_counts = M_B-M_D
~~~

The variance is within each frame and has divisor K-1. Do not substitute variance across frame means, variance of all pixels after mixing group means, or divisor K. No clipping, robust trimming, pixel mask, frame normalization, frame selection or covariance subtraction is implicit. Frame/pixel pooling is valid only under the declared scalar stationary model.

Offset estimate is M_D counts; mean photon-background estimate is M_B-M_D counts. The latter may be negative in a finite sample; retain it signed with an information code. The affine offset used for background-subtracted specimen processing is M_B, not M_D alone.

For stationary NS01 populations, mu_G=E[C_G] and nu_G=Var(C_G) obey:

~~~text
mu_D=o;             nu_D=g^2*sigma_e^2
mu_B=o+g*b;         nu_B=g^2*(b+sigma_e^2)
mu_F=o+g*(b+s_ref); nu_F=g^2*(b+s_ref+sigma_e^2)
(nu_F-nu_B)/(mu_F-mu_B)=g, when s_ref>0.
~~~

Thus actual gain is identifiable from these independent mean/variance contrasts under the selected Poisson law. Mean images alone retain the gain-times-brightness scale ambiguity. Neither statement makes a finite-sample ratio unbiased or accurate.

Compute the reported contrast as one native float64 subtraction of the returned group means: dM=RN64(M_F_returned-M_B_returned). Likewise dV=RN64(V_F_returned-V_B_returned), and dB=RN64(M_B_returned-M_D_returned). All decisions below use these returned-point statistics, not latent population values.

If dM>0 and dV>0, attempt g_hat=RN64(dV/dM). Report it as gain_counts_per_e only if finite and strictly positive. Otherwise report None with the corresponding information code. Physical electron-gain availability does not control counts-relative normalization.

## Relative-count gauge and actual existing correction interface

If dM>0, define one reference-flat-relative signal unit as that calibration's observed excess flat mean. For any paired raw pixel C:

~~~text
Y=(C-M_B_returned)/dM.
~~~

The reference flat mean maps to one and the blank mean maps to zero in this declared finite-sample gauge. Do not claim exact per-pixel values or exact true-photon recovery. When dM<=0, this normalization is unavailable; do not divide by it or silently use one.

Use the real public interfaces as follows after a successful camera estimate:

~~~python
corrected = correct_linear_response(
    paired_raw_acquisition,
    offset=float(estimate.means_counts[1]),
    response=estimate.contrast_counts,
    output_unit="reference_flat_relative",
)
~~~

The supplied response here has units counts per reference-flat-relative unit. It is not mislabeled true counts/electron. Keep the camera-estimator identity and estimated status in workflow provenance; correct_linear_response correctly records that its arguments were supplied by its caller. It does not itself infer them.

Subtracting the blank mean removes estimated mean background, not its photon noise. A descriptive count-noise predictor for nonnegative relative mean u is V_B+dV*u, with relative variance (V_B+dV*u)/dM^2. Use it as a nonnegative Poisson-like linear noise predictor only when dV>=0. A negative observed dV is retained and reported; do not clip it into a valid noise law. This prediction is a plug-in diagnostic, not an uncertainty guarantee or a mandatory reconstruction weighting rule.

Downstream phase/carrier estimation and specimen reconstruction may operate in this relative-count gauge. They need no true electron gain merely to obtain linear signal units. Absolute emitter brightness/electron comparisons require the separately estimated physical scale and its uncertainty, or an explicitly reported evaluator-only scale comparison. No true gain or reference flux may flow back into the inverse to fix this scale.

## Result, information and failures

Return a frozen-binding ScalarCameraEstimate with exactly:

- means_counts: owned native float64 vector (3,), order D,B,F.
- variances_counts2: owned native float64 vector (3,), group mean within-frame variances.
- frame_means_counts: three separately owned native float64 vectors of lengths T_D,T_B,T_F.
- frame_variances_counts2: three separately owned native float64 vectors of those lengths.
- empirical_mean_se_counts: owned native float64 vector (3,), defined below.
- contrast_counts: Python float dM, including nonpositive values.
- gain_counts_per_e: Python float g_hat or None.
- information_codes: tuple of strings in the following fixed order when applicable.
- source: unchanged opaque string.

All arrays are writable C-contiguous and share no storage with callers, other output arrays or another call. No raw pixel archive, actual illumination means, true camera values, seed, mask or coefficient map is returned. Direct record construction has no additional validation promise.

Information codes, returned as values rather than raised errors:

1. nonpositive_flat_contrast if dM<=0: relative normalization and gain are unavailable.
2. nonpositive_variance_contrast if dV<=0: photon-transfer gain is unavailable. Counts normalization remains available when dM>0. Zero variance contrast is legitimate for a deterministic/constant-noise observation but carries no positive Poisson-gain estimate.
3. unrepresentable_gain if dM>0 and dV>0 but their specified quotient is nonfinite or rounds to nonpositive: gain is unavailable; counts normalization can remain available.
4. negative_background_estimate if dB<0: retain the estimate signed; this does not by itself forbid blank subtraction or relative normalization.

No information code certifies the acquisition model, instrument accuracy, statistical significance or population positivity. An unlucky noisy realization can produce an unavailable outcome although the population is informative. No repeated acquisition/retry loop is part of the operation.

Use SimreconError code invalid_scalar_camera_calibration for the named input/source domain violations, and scalar_camera_calibration_range for nonfinite required moment, mean/variance contrast, background-difference or uncertainty stages. The optional gain quotient has the explicit unavailable outcome above. Ordinary Python argument-binding TypeError, actual allocation MemoryError and unrelated exceptions propagate. No partial record is returned after a required-stage range failure. Handle expected arithmetic overflow/underflow without leaking arithmetic RuntimeWarning/FloatingPointError; preserve caller modes and suppress no unrelated warning category.

## Numerical versus sampling uncertainty

Use native float64 statistics and separately component-safe arithmetic. The exact moments above define the numerical targets; private reduction order/backend is not selected. Let eps=2^-52, q0=2^-1074, A=max(abs(normalized samples)) over all groups, and ell=ceil(log2 K)+max_G ceil(log2 T_G)+8, evaluated using exact integer counts. Each returned frame/group mean must satisfy absolute error <=256*ell*eps*A+16*ell*q0 counts. Each returned frame/group variance must satisfy absolute error <=4096*ell*eps*A^2+128*ell*q0 counts^2. Evaluate observer bounds in sufficient precision; an overflowing/vacuous observer proves no accuracy. Constant frames have exactly zero within-frame variance. Signed zero has no separate bitwise promise. A=0 gives exact zero statistics. Input count scale A alone is not a new rejection cap.

These are selected conservative arithmetic allowances for independent review, not camera accuracy promises. Required-stage range behavior remains operational; no universal success for every exact-real finite moment is asserted. Ordinary bounded detector-count cases must not fail merely because the operation lacks an implementation or because physical gain is uninformative. Exact dyadic/small independent controls should distinguish divisors, order and grouping more sharply than the conservative envelope.

For descriptive repeatability, for each group use the returned frame means and their returned group mean:

~~~text
S_G = sqrt(sum_t (m_Gt_returned-M_G_returned)^2 / (T_G*(T_G-1))).
~~~

Report empirical_mean_se_counts as this nonnegative native float64 statistic, with stable float64 evaluation. Its exact target is this expression of the returned frame/group means, with the same mean-scale absolute allowance stated above. It is the usual estimated standard error of the group mean under the selected independent stationary frame model; it is not a confidence interval or a population standard deviation. Illumination flicker/model mismatch can inflate or invalidate that interpretation. Return frame moments so repeatability and variance contrasts remain inspectable. No exact finite-sample Gaussianity, fixed percentage accuracy, bias correction, coverage probability or confidence interval is promised for g_hat or normalized specimen values. A ratio can be biased and unstable near zero mean contrast.

Independent statistical assessment uses predetermined seeds and repeated whole calibration ensembles, retaining unavailable outcomes and estimating bias/scatter/coverage where justified. It must not cherry-pick seeds or import true parameters into the estimator. Exact numerical tests use independent finite sums/small rational cases; distribution checks use the NS01 moments, not a duplicate RNG recipe. Monte Carlo truth remains evaluator-only.

## Invariances, limits and implementation scope

In exact statistical arithmetic, frame permutation within a group and pixel permutation within each frame leave group estimates unchanged. No permutation that mixes acquisition groups is invariant. Floating-point results follow the stated allowances, not a bitwise cross-platform promise.

For a common positive affine count relabeling C'=a*C+c, means become a*M+c, variances a^2*V, dM becomes a*dM, g_hat becomes a*g_hat, and normalized Y is invariant. This is a count-unit/offset equivariance, not permission to change acquisitions or fit scale to hidden truth. A negative a is outside the physical positive-gain model. Multiplying emitter brightness and changing camera gain can preserve mean signals, but the selected photon-noise contrast can distinguish them; do not claim global nonidentifiability of the complete stochastic law.

This contract selects one scalar stationary ensemble. It does not authorize spatial calibration maps, per-frame exposure correction, phase monitors, sphere/center truth, optical calibration, physical motion, a writer, overwrite/cleanup behavior or any existing API/gate change. Existing raw declaration, linear correction and reconstruction contracts remain intact. Public code/test implementation would follow the existing high-risk fresh A/B/C/D route, exact full-local gate, inherited numerical-chain coverage/platform requirements and preserved accounting. No role is launched and no formal acceptance is claimed by this draft.

Named ownership: A tests/test_scalar_camera_calibration.py and optional tests/scalar_camera_calibration_fixture.py; C src/simrecon/_scalar_camera_calibration.py and additive src/simrecon/__init__.py exports only. Coordinator owns usage, this contract, task/PROJECT, packets, acquisition/evaluation evidence and provenance. The task record supplies the inherited gates and role boundaries. No implementation role may alter reviewed tests/fixtures or unrelated interfaces.

## Observable decision inventory

A maps every input/representation, arithmetic/information, ownership, failure and compatibility obligation above to meaningful public-boundary tests; B independently audits omissions/oracle validity. Include finite frame-versus-group grouping and K-1 divisor, three signed moment groups and contrasts, unavailable gain with still-available relative normalization, the ordered information codes, range versus invalid domains, constant/all-zero data, legitimate storage/conversion layouts, unchanged caller/NumPy/warning state, direct real correction composition and affine/permutation relations within numerical limits. This is no test/scenario quota. Initially passing tests remain valid; no manufactured product-red or percentage-only tests.

Public expectation sources: the exact equations in this contract and the approved simulation-camera-v1 and linear-response-correction-v1 contracts. Existing simulator/runtime output is not an independent oracle. Finite synthetic statistical validation retains predetermined seeds and all unavailable outcomes; truth stays evaluator-only.
