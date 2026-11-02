# Independent post-freeze reductions — observed run 1

The authorized checker ran once against `evaluation-2`, exited 0, and wrote
`independent-reductions-1.json`. Native `/usr/bin/time -p` reported real/user/system
2.48/1.73/0.68 seconds; observer elapsed was 2.378007042 seconds. These durations
overlap and are not additive. No fitter, optics, metric module or FFT was invoked.

All three inference seals, the evaluation seal and matched-generation seal bound
1700 verified payload files, plus 46 original generation files checked against the
public inventory. Seal hashes remained unchanged during the observer. The checker
reported 807 arithmetic-envelope comparisons, 68 metric count comparisons and no
recorded inconsistency. These are descriptive observer checks, not acceptance gates.

## Numerical results

The known/noiseless arm retained candidate12 and stopped at the iteration limit.
Independent source relative L2 error was 0.9458071585131514; all15 signal prediction
relative L2 error was 0.6485574794021475. Counts were 8388608 source coefficients
and 31457280 image values. Independent objective components were data
0.008450775273186913 and penalty 5.012699509269444e-9, total
0.008450780285886422. Difference from the frozen total was 1.734723475976807e-18.

The maximum aggregate norm discrepancy from the published evaluation was
1.1368683772161603e-13. Source relative-error discrepancy was
2.220446049250313e-16. These are ordinary reduction-roundoff differences, not a
change in scientific outcome or an inferred share of any reconstruction error.

The supplied-known-source forward diagnostic independently reduced to relative
L2 error 8.086578785369908e-8 and maximum absolute error
2.2722199943814303e-6 relative image units. This checks reductions of existing
arrays; it is not an independent full-grid optical certification.

Both estimated arms genuinely returned unavailable/training_misfit, with training
RMS 0.10234992496705284 (noiseless) and 0.10425718684959008 (noisy), against the
frozen 0.05 limit. Neither has a scored source, predictions, fit metrics or image
spectra. Truth is available to evaluation, but there is no corresponding estimated
specimen output to compare. No missing output was replaced with a truth result.

## Gauge, representation and presentation checks

Known-arm blank/contrast match the frozen camera at 20.2/1700 counts. Physical
gain is unavailable for deterministic camera frames, as expected. Corrected mean
and signal differ only by the expected constant plus at most
3.552713678800501e-15 sequential arithmetic deviation.

Axial pairing, pre-round gauge, float32 rounding and electron backconversion each
had zero prescribed-equation mismatches. Relative source rounding error was
2.9139712798981465e-8; signed mass change was 2.4139881068419022e-5 relative
source units; no nonzero coefficients were lost. Recorded roundtrip backconversion
error was exactly zero for these stored arrays. Deterministic camera
creation/correction relative error was 1.1459620779213052e-16.

All75 image-spectrum records satisfy the independently reduced energy identities
within observed roundoff: largest absolute energy difference 1.6007106751203537e-10,
largest relative difference 2.4367930346468733e-15. Three source-spectrum records
also agree; their largest absolute energy difference is 2.7284841053187847e-12.
All checked frequency values matched the independent signed-integer construction.

All27 catalogue rows/81 quantitative profile lines matched the original arrays,
coordinates and nearest-center indices exactly. First-center source indices were
(5,101,96), at (0.6875,4.0600000000000005,3.86) micrometres. The checker records
full-line peaks and intended shape windows, but did not inspect rendered pixels,
color ranges, crop displays or projection-difference images.

## Limits

`longdouble` has the same epsilon as float64 on this machine
(2.220446049250313e-16), so no extra-precision claim is made. Chunked scaled norms,
math.hypot and math.fsum provide an independent reduction path. The predeclared
arithmetic envelopes are conservative and sometimes much larger than the observed
metric or disagreement; actual differences above are the informative evidence.
They are not recovery or scientific alignment tolerances. Full-grid optical
accuracy, source recovery, convergence, resolution and formal acceptance remain
unestablished by this observer.
