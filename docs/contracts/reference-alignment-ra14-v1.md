# RA14 — frozen full-scene evaluation v1

Version 1.0. Authorized by the owner's continuing RA12–RA15 request, amended by
“stop at RA15 and we can discuss there.” Finish RA13 readiness before scientific
execution. RA14 produces a separate PR stacked on RA13. No merge, release,
reference executable, component repair, estimator substitution or tuning is authorized.

This is a high-risk experimental/evaluation slice. A owns only
`tests/test_reference_alignment_ra14_comparison.py` and
`tests/reference_alignment_ra14_fixture.py`; fresh blind B reviews its exact
checkpoint. Restricted C owns only `scripts/reference_alignment_ra14_comparison.py`.
Fresh D reviews the exact passing candidate and measured experiment/claims.
Coordinator owns the frozen protocol, source-identified generation/inference/
evaluation commands, records, report, figures and PR presentation. Advisors are
advisory. The approved advisory-percentage behavior/risk policy and exact-candidate
full local/both-platform gates remain binding. Human numeric limits are not set.

## Scientific verdicts

RA01 deliberately adopted no numerical full-scene recovery or universal resolution
threshold (reference-alignment-benchmark.md). RA14's roadmap success criterion
must not be weakened to “files produced.” Distinguish experiment delivery,
independently checked named noiseless finite controls, and full scientific alignment.
Record actual failures/unavailability. If the latter is unestablished, say so and
retain the unfinished recovery/resolution obligation for owner discussion before
RA15. Noisy fits are diagnostics; certify only named noiseless finite-model controls.
No calibration residual, local rank, held-out replay, decreasing objective, finite
iteration stop, 40 nm grid or PR readiness certifies source recovery or resolution.

## Minimal development evaluation boundary

The new module supplies only these pure, in-memory operations:

```python
replay_source(source_relative, *, source_spacing_um_zyx,
              carriers_yx_per_um, phases_at_specimen_origin_rad,
              beam_amplitudes, pupil_order) -> numpy.ndarray
compare_arrays(estimated, reference) -> MetricSummary
```

`replay_source` composes existing `build_kernel_cache` and `forward`. Source values
are integrated reference-flat-relative weights, passed unchanged as the existing
float32 source operand. Source shape/spacing and pupil order inherit the public
inverse grammar; outer carriers/phases/beams are plain native float64 arrays with
shapes (3,2)/(3,5)/(3,), respectively, finite and satisfying the public inverse's
carrier/amplitude domains. Validate all supplied inputs before numerical work.
Reject malformed composition inputs with `invalid_reference_alignment_ra14` and a
field-identifying message. Source follows the inverse's float32-width layout/endian
rule. Build one cache using excitation/emission 0.488/0.525 µm, refractive index
1.515 and numerical aperture 1.4. Call forward for orientations 0,1,2, preserving
unequal beams and every supplied phase. Return complete owned writable C-contiguous
native float64 shape (3,5,Z,Y,X). No camera correction, phase transfer, truth,
normalization, origin shift or rescale occurs. No independent-optical-reference
claim follows: this is a production-operator replay. All dependency errors,
MemoryError and unrelated warnings/exceptions propagate unchanged. No partial
prediction payload is fabricated. Do not mutate any input/global warning, NumPy
error or random policy. A scored retained partial fit may be replayed; the external
report must preserve its original status and candidate identity.

`compare_arrays` consumes same-shaped nonempty plain native float32/float64 arrays,
including signed/strided/read-only/zero-stride positive representations. All values
must be finite; both arrays may have different accepted widths. Reject malformed
inputs using the same code and field diagnostics. MetricSummary is a frozen record
with exactly count, reference_l2, error_l2, relative_l2, error_rms, error_max_abs,
error_mean, unavailable_fields. Each nullable metric has type float | None; count
is a Python int. The last is a tuple of `UnavailableMetric` frozen records with exactly
field/reason strings. One entry names each unavailable field; ordering is not promised.
Same-shaped 0-dimensional arrays have count one and are valid; empty arrays are not. Errors are estimated minus reference, count is exact integer
size, and summaries use full-array arithmetic. Stable reductions preserve each
independently representable final statistic despite overflowing raw subtraction,
squares/sums or reference norms. Relative L2 is the exact-real ratio of norms and
may be available even when a norm is unrepresentable. Exactly zero reference makes
only relative_l2 unavailable with zero_reference. Other genuinely unrepresentable
final floats are None with unrepresentable. No nonfinite sentinel, epsilon floor,
clipping, fitted scaling, per-frame-ratio averaging or acceptance threshold. Preserve
input arrays/flags and caller policies on success/failure. No file/CLI/wheel API,
new simulator or changes to existing component/metric specifications.

## Frozen actual experiment

Use the unchanged original full 27-object catalogue/plan/seeds and original raw
camera/calibration/specimen arrays. Restore only identified archive members and
verify original public seals/digests. Keep private truth in separate generation/
evaluation paths. Observations and exact controls are sealed before inference;
close and hash all inference outputs before evaluation reads truth. Observation-only
processes receive only raw arrays and allowed metadata/controls. Known-input control
is explicitly labeled and calls existing fit_specimen directly; estimated arms call
reconstruct_raw_sim directly, without new runner wrappers.

Three mandatory arms share full scene and detector box (32,256,256), inverse source
basis (32,512,512), detector spacing (0.125,0.08,0.08) µm and original origin/physical
phases/unequal beams. Predeclare controls once: sweep_scales=(1.0,), 40 refinement
evaluations, training RMS limit 0.05, calibration comparison 1e-8, operator comparison
1e-6, Q128 handoff/fitter, regularization .001, 12 specimen iterations and eight
backtracking trials. These are the original RA12 controls plus historical specimen
controls; historical PR53 Q256 and ten sweep scales remain distinct. Do not use
RA13's permissive central-only small wiring settings as scientific defaults.

1. Known/noiseless: a matched Q128 paired source/control with explicitly supplied
   true nuisance parameters in fit_specimen. Camera estimated from deterministic
   groups; supplied illumination is labeled known, not image-only inference.
2. Estimated/noiseless: those matched noiseless camera/calibration/specimen counts
   through RA13, no truth inputs.
3. Estimated/noisy: unchanged original full observations and acquisition settings,
   through RA13 using the separately frozen RA14 inference controls. Actual complete full calibration is mandatory; small RA12 failure
   is not a substitute. An actual scientific unavailable outcome is recorded.

For matched construction pair the archived fine axial source masses into the inverse
basis, use deterministic camera contrast d_hat and true gain g=1.7 to form
x32=float32((g/d_hat)*s_pair), where s_pair is paired electron mass. The generator
consumes s_matched=(d_hat/g)*float64(x32) electrons, not relative coefficients;
float64(x32) is the matched relative coefficient reference. Record conversion and
rounding effects. Inference receives none of these source/true-camera quantities. Generate Q128 specimen means with the same four lateral pixel
samples (source refinement (1,2,2)); generate finite-sphere calibration Q128 from the
original catalogue with original refinement (8,8,8). Use original central-only
calibration group and full unequal-side training/held-out commands. Deterministic
camera acquisition uses existing sample_camera with shot_noise=False and
read_noise_e=0. Original gain/offset/background/flat signal remain 1.7/10/6/1000.
Held-out noiseless repeats provide no independent noise information. Preserve all
original Q256/finer-source means as separate model-mismatch references; pairing is
not an innocuous unit conversion or optical equivalence.

The existing generator bound 1e-5*T and inverse combined bound
(2e-4+1e-8)*L*Cr(B_Q)*maxabs(x), plus independently justified observer precision,
apply only to corresponding matched forward controls. They are not source-recovery
tolerances. A/B independently justify a meaningful tiny direct-pupil matrix control,
including off-center source, nonzero phase/origin, unequal beams and all15 frames.
Tiny direct matrix/objective evidence is independent; production replay agreement
alone is not. Do not hide a loose/vacuous full-scene norm bound or claim an unmeasured
one. No dense global optical matrix is required for the full run. Full-scene agreement is
measured with no independently qualified full-grid numerical bound. Report paired-source
float64-to-float32 absolute/relative error, signed mass change and lost nonzeros. Axial
pairing moves original sites by +/-0.03125 µm. Fixed full-frame prediction and signed
residual Fourier powers use declared normalization/physical axes, no fitted scale,
taper or error-selected region. These are not optical transfer/resolution estimates.
Do not divide image by source spectra to invent a transfer function.

## Reports and feasible execution

Before full work, use existing accepted tiny/moderate controls, bounded full-size
cache/one-orientation forward+adjoint pilot and actual headroom/swap/disk evidence,
with no simultaneous heavy phase. Keep complete time/native resident-memory units,
status and inputs. Timeout/resource termination is incomplete evidence, never a
scientifically meaningful unavailable result. No automatic retry/downsize/tuning.

For every arm preserve component statuses, calibration/audit diagnostics, fit score,
all entered trials and stop/candidate/partial identities. Whenever a source exists,
freeze it and all15 replay predictions before evaluation. Compare to signal and
corrected-mean references separately using the actual camera gauge, and preserve
all15 observed residual means/RMS, absolute/reference/error norms, maximum absolute error, signed mean error
and coefficient error. Keep original PR53 poor-recovery baseline and source pairing
limits explicit. Fourier transfer/source spectra are descriptive unless a justified
finite information analysis supports an observable-mode claim.

Deliver reproducible JSON/array/hash manifests and measured report, all15 frame
residual/spectrum summaries, objective/trial/stopping traces (convergence remains
unestablished) and per-stage time/memory; physical
XY/XZ views, signed differences, fixed original catalogue-center slices and quantitative
profiles. No fitted registration, brightness adjustment, best seed or truth-tuned λ.
A matched conventional/photon-budget/resolvability criterion is absent: resolution
improvement and full-scene scientific alignment remain unestablished unless separately
justified evidence actually establishes them. Stop before RA15 for owner discussion.

Ordinary simplified housekeeping only: existing commands for known disposable
scratch after processes close; preserve original evidence, runtime pins and uncertain
paths. No cleanup code/tests/review pipeline.
