# Full noisy study command and file protocol v1.2

**Version1.2, October26,2026.** Coordinator-adopted necessary scientific/persistence contract under the owner's full noisy images-only PR53 request. This authorizes its intended scope through the existing high-risk route; it supplies no implementation, test checkpoint or independent acceptance. Dependent role execution waits for completed independently reviewed exact scientific prerequisites. Actual scene, seeds and finite settings are coordinator experiment choices recorded before generation, not hidden defaults.

**Owner campaign-size revision, October26,2026.** The owner asked, "Can we reduce the simulation size to 256x256x32?" The coordinator interprets that as `(z,y,x) = (32,256,256)` while retaining the voxel spacing `(0.125,0.080,0.080)` µm and origins. The physical box is `(4,20.48,20.48)` µm in ZYX order. The predeclared layout assumption halves every specimen local centre coordinate and preserves all catalogue radii, brightnesses and row order; private plan revision v3 records that experiment setting before generation. This changes the required campaign size only. It adds no API restriction, gate or policy change and does not reduce the fixed O16 reference, canonical tests, required platforms or full scientific workflow. Larger resource observations remain historical; payload arithmetic is not a measured resource result.

## One module, three separate processes

`scripts/full_noisy_study.py` supplies exactly these study commands:

```text
python -m scripts.full_noisy_study generate --plan PRIVATE_PLAN.json --out NEW_RUN

python -m scripts.full_noisy_study infer --observations OBSERVATIONS_DIR --out NEW_INFERENCE \
    --sweep-scales '[1,0.5]' --regularization FLOAT \
    --max-iterations INT --max-backtracking-trials INT --pupil-order INT

python -m scripts.full_noisy_study evaluate --observations OBSERVATIONS_DIR \
    --inference INFERENCE_DIR --private-truth PRIVATE_TRUTH_DIR --out NEW_EVALUATION
```

The values shown for sweep scales are syntax examples, not scientific defaults. All shown arguments are required; unknown/duplicate options, positionals and omitted values are errors. Ordinary `--help` is permitted. No `all`, resume, overwrite, retry, cleanup, plotting, remote transport, arbitrary callback, arbitrary metadata, plugin or general pipeline interface is added. No public Python API beyond this module CLI is selected.

`generate`, `infer` and `evaluate` run as separate Python processes. Inference receives only the observation directory, a new output path and the five finite algorithm settings. It receives no plan, seed, truth path, true camera coefficient, true phase/carrier/beam, noiseless observation or source-volume input. It must not discover/read parent/sibling generation manifests, search for private truth or infer values from run-directory names. This is a procedural/data-flow boundary, **not** an engineered filesystem sandbox or authentication guarantee.

Scientific dependencies are the approved public source, optics, camera and scalar-camera-estimator operations, the adopted complete 47-coordinate `fit_bead_calibration`, the adopted `fit_specimen`, and the approved inverse cache/forward operations. The old limited Powell pilot is not the study's calibration fitter. Exact completed prerequisite identities must be added to the implementation packet before any dependent role launch. C owns only this new driver; A owns its named public CLI tests/optional fixture; the coordinator owns concrete plans, staged runs, studies, presentation and cleanup. No module split or reusable framework is implied.

## Common types, files and output ownership

All JSON is UTF-8, contains one object and uses strict JSON numbers. Reject duplicate object keys, NaN, infinities, numeric overflow on required float64 normalization, wrong scalar kinds, unknown keys and missing keys at every schema level. Bool is never an integer/real setting. Counts/seeds are JSON integers; real fields accept JSON integers or numbers that normalize to finite float64. Array-shaped JSON fields are nested lists of their exact declared dimensions. An empty catalogue has JSON value `[]` and is normalized explicitly to shape `(0,5)`.

Every JSON object below has **exactly** its listed keys. Named public-record schemas inherit their exact public field sets recursively, not arbitrary object attributes. JSON null is used only where stated. Protocol version strings are literal: `full_noisy_study_plan_v1`, `full_noisy_study_observations_v1`, `full_noisy_study_truth_v1`, `full_noisy_study_generation_v1`, `full_noisy_study_estimates_v1`, `full_noisy_study_freeze_v1`, `full_noisy_study_evaluation_v1` and `full_noisy_study_evaluation_complete_v1` in the corresponding `format_version` fields.

Writers use deterministic JSON formatting: sorted object keys, UTF-8, `ensure_ascii=False`, compact comma/colon separators, `allow_nan=False`, and one trailing newline. Readers do not require that whitespace/key order, but hashes always cover the exact stored bytes. No pickle, object deserialization, executable metadata or arbitrary class name is allowed.

NPY payloads are ordinary non-object arrays written with `numpy.save` to an already exclusively opened binary file and `allow_pickle=False`. On-disk dtype is little-endian float64 (`<f8`), except the inferred source, which is little-endian float32 (`<f4`). Headers declare C order. Supported ordinary NPY versions emitted for these headers are accepted; an exact dtype, shape, one complete array payload and no trailing payload are required. All loaded numerical values must be finite; private electron sources/means and inferred sources are nonnegative. Counts and inverse predictions may be signed. Convert to native dtype in memory where the scientific API requires it. Honor each actual public scalar/tuple/array grammar at its call boundary. In particular, public optics/inverse beam settings use built-in tuples of built-in numeric scalars; JSON lists and NumPy scalar members do not broaden those interfaces. The specimen fit consumes its explicitly declared plain ndarray illumination metadata. Read with `allow_pickle=False`; read-only mapping is permitted for streaming verification/evaluation, but not as an excuse to pass a memmap subclass to a plain-ndarray-only API.

An NPY file descriptor has exactly `path`, `dtype`, `shape`, `size_bytes`, `sha256`. `dtype` is the literal string above; `shape` is an integer list; `size_bytes` is a nonnegative integer; SHA-256 is 64 lowercase hexadecimal characters over the whole closed file, including its header. A JSON file descriptor has exactly `path`, `size_bytes`, `sha256`. Paths must equal the fixed relative names specified below. Absolute names, `..`, alternate separators, extra filenames and path-derived scientific settings are invalid. Readers open only their declared fixed protocol files; unrelated unlisted filesystem entries are not inputs and are never searched for metadata.

Each `--out` parent must already exist as a directory. Create the requested output root exclusively. Any existing entry at that path—including an empty directory, ordinary file or dangling symlink—is an error with no mutation. Create each owned subdirectory and file exclusively. Never replace, truncate, unlink, merge with or reuse an existing entry. Do not create missing ancestors. Exclusive creation is required for every JSON/NPY/completion file, not only the root.

Close every payload writer, then compute its complete byte count/digest, before beginning the completion manifest that references it. A completion manifest is valid only when its full strict JSON and every referenced payload validate. A header, existing directory, partial manifest or partially written NPY is not completion. This selects no atomic-directory, malicious-concurrency or crash-durability guarantee. Filesystem errors preserve the actual partial directories/files. Retries require a new output root. There is no automatic cleanup, failure-file rewrite, repair loop or deletion helper.

`Runtime` is a small JSON object with exactly `python_version`, `numpy_version`, `scipy_version`, `simrecon_version`, `platform`, `byteorder`, `driver_sha256`. Values are nonblank strings; byteorder is `little` or `big`; the hash identifies the actual driver source bytes. If a package version cannot be obtained, its value is null rather than invented. This is limited runtime provenance, not a complete build/environment or exact-candidate gate certificate. The coordinator retains the latter separately under existing policy.

## Private generation plan

The input plan has exactly:

```text
format_version, geometry, camera, illumination,
bead_catalogue, specimen_catalogue, generator_pupil_order, seeds
```

`Geometry` has exactly:

```text
camera_shape_yx,
calibration_shape_zyx, calibration_spacing_um_zyx, calibration_origin_um_zyx,
specimen_shape_zyx, specimen_spacing_um_zyx, specimen_origin_um_zyx
```

Shapes contain positive integers. Camera pixels per frame must be at least two. Calibration spacing is exactly the represented constants `(0.125,0.080,0.080)` µm required by the bead contract; each calibration physical side length is at least 0.100 µm. Specimen spacing consists of finite positive values. Origins are finite real three-vectors, known box-corner labels; catalogue coordinates are local to their corresponding corners. Every camera group has **eight** frames. The selected full trial uses camera shape `(256,256)`, calibration shape `(8,32,32)` and specimen shape `(32,256,256)` with the declared spacings. Smaller legal shapes are allowed for complete workflow proof; they are not evidence of full-size completion.

`camera` has exactly `background_e`, `read_noise_e`, `gain_counts_per_e`, `offset_counts`, `flat_signal_e`. Background is nonnegative; read-noise standard deviation, gain and flat added signal are strictly positive; offset is signed finite. Units are electrons per pixel per exposure, electrons standard deviation, counts/electron, counts and electrons per pixel per exposure respectively. Shot noise is always enabled. These narrower study choices require real photon and read noise; the public camera primitive's noiseless mode remains unchanged but is not an option of this workflow.

`illumination` has exactly `carriers_yx_per_um` `(3,2)`, `phases_at_calibration_origin_rad` `(3,9)` and `beam_amplitudes` `(3,)`. These are private true generator settings. They obey the approved optics finite/domain rules: signed continuous carriers within `|q|<=1.515/0.488`, arbitrary finite phases, and nonnegative amplitudes with at least one positive. They are shared stationary illumination parameters, with phases transferred to the known specimen origin as defined below. No separately chosen specimen phase array can break that stationarity assumption.

`bead_catalogue` is exactly three source rows `(z,y,x,radius,total_electrons)`. All radii equal represented 0.050 µm; brightnesses are nonnegative; spheres are wholly contained and nonoverlapping, with tangency allowed. `specimen_catalogue` has any finite number of source rows, including zero, with positive radii, nonnegative brightness and complete containment. Its overlaps and row order retain the public source contract's meaning. There is no hidden scene, center, support or brightness default. Positive objects without represented occupied cells remain legitimate source-range failures, not silently repaired geometry.

Generator source refinements are fixed `(8,8,8)` for beads and `(2,2,2)` for specimen. Pixel midpoint samples are `(2,2)`. Fixed optics are excitation/emission 0.488/0.525 µm, index 1.515, detection NA 1.4 and the clear matched-index scalar pupil. `generator_pupil_order` is a positive integer selected before generation; it remains private numerical provenance and is not an inference setting.

`seeds` has exactly `camera_dark`, `camera_blank`, `camera_flat`, `calibration_central`, `calibration_training`, `calibration_heldout`, `specimen`. The camera entries are length-eight integer lists; central is one integer; training is `(3,9)`; held-out and specimen are `(3,5)`. All 82 seed values are nonnegative and pairwise distinct. There is no maximum seed or trial-selection loop. Each identifies one public camera call: a 2D camera frame or one 3D bead/specimen exposure. This selects the chunk boundaries and records independent predetermined local streams; it does not claim distinct seeds prove statistical independence or cross-version bitstreams. Global RNG state is untouched by the public sampler.

## Generation and its two manifests

Validate plan syntax/domains and output-parent requirements before claiming the new root. Create only `observations/` and `private_truth/` beneath it. Persist the normalized plan as `private_truth/plan.json`; retain the SHA-256 of the original input plan bytes in the private generation summary. No plan field containing truth/seed is copied into observations.

Call `make_sources` on the two actual catalogues at their declared grids. Save `bead_source_e.npy` and `specimen_source_e.npy` in private truth. Use `expected_images` for the actual complete finite optical means. For bead central images use central-only amplitudes `(1,0,0)` and canonical zero carrier/phase. For bead training use all true carriers and nine true phases. Held-out means are the same actual first-five-command means; draws use separate held-out seeds. Do not fit a freely chosen response image or pass expected means into inference.

For origin transfer, define the principal phase using the **physical period 2*pi** and exact-real interpretations of the normalized represented inputs. Reduce the complete expression into [-pi,pi), then store a native-float64 representative with ordinary float64 reduction roundoff. The stored endpoint convention is [-pi64,pi64), where pi64 is nearest float64 to pi: if final rounding would produce +pi64, use -pi64. Rounded pi64 sets this stored endpoint convention, never the physical reduction period. Apply once, using true inputs only in generation:

```text
psi_spec[o,p] = wrap_physical(psi_cal[o,p]
                             + 2*pi*q[o] dot (origin_spec-origin_cal)_yx), p=0..4.
```

Use range-safe modular evaluation of the complete normalized-input expression, including arbitrary finite input phases and origin differences. An overflowing unreduced coordinate product alone does not justify a failure when the wrapped value is representable. Reducing a huge phase modulo rounded 2*pi64 is not a faithful substitute. No particular reduction backend or correctly rounded whole-expression result is required. Independent controls must distinguish the physical period with meaningful finite-case roundoff allowances. Store the resulting finite float64 phases in private summary. The same mathematical transfer later acts on *estimated* inputs in inference. Neither fit itself transfers phases. An identified required numerical obstruction is a range failure, never a truth/nominal fallback.

Produce specimen means one orientation at a time; a five-phase orientation result may be retained, but not all orientations together. Save each 3D expected signal mean separately, then call `sample_camera` separately for its raw exposure using that exposure's seed. Expected means contain optical signal electrons only; background/read noise/gain/offset enter the public sampler. There is no 2 GiB writable-mapped raw stack. The output raw files are separate complete 3D NPY arrays.

For dark frames, pass zero expected signal and zero background. For blank, pass zero expected signal and the common background. For flat, pass a spatially uniform array of `flat_signal_e` and the common background. All groups use the same true gain, offset and read-noise standard deviation as bead/specimen images, with shot noise enabled. Collect each group into its eight-frame stack. The full camera payload is `3*8*256*256*8=12,582,912` bytes; this is payload arithmetic, not measured peak memory.

The **21 observation payload names** are exactly:

- `camera_dark.npy`, `camera_blank.npy`, `camera_flat.npy`, each `(8,Hc,Wc)`.
- `calibration_central.npy`, shape `Nc`; `calibration_training.npy`, `(3,9,*Nc)`; `calibration_heldout.npy`, `(3,5,*Nc)`.
- `specimen_o0_p0.npy` through `specimen_o2_p4.npy`, generated by the literal index ranges `o=0,1,2`, `p=0,1,2,3,4`, each specimen detector shape. Descriptor order is orientation-major then phase-major.

`observations/complete.json` has exactly `format_version`, `geometry`, `acquisition_model`, `nominal_phase_commands_rad`, `files`. Geometry is the public Geometry above. Acquisition model has exactly:

```text
camera_law, shot_noise, stationary_camera, common_dose, known_registration,
pupil, excitation_um, emission_um, refractive_index, detection_na,
pixel_subsamples_yx
```

The string/boolean values are respectively `scalar_poisson_gaussian`, true, true, true, true, `clear_scalar_matched_index`; numeric optics equal the fixed constants and pixels `[2,2]`. These are assumptions/acquisition labels, not certification inferred from data. `nominal_phase_commands_rad` is the nine command guesses `(0,2*pi64/5,4*pi64/5,6*pi64/5,8*pi64/5,pi64/5,3*pi64/5,7*pi64/5,9*pi64/5)` in the declared order. It is not the actual phase array. `files` is the ordered list of the 21 exact NPY descriptors above. No source, actual illumination, camera coefficient, flat level, noise coefficient, seed, plan digest, private path or noiseless metadata is permitted.

The **private payload names** are exactly `plan.json`, `generation_summary.json`, `bead_source_e.npy`, `specimen_source_e.npy`, `calibration_central_expected_signal_e.npy`, `calibration_training_expected_signal_e.npy`, `calibration_heldout_expected_signal_e.npy`, and `specimen_o0_p0_expected_signal_e.npy` through `specimen_o2_p4_expected_signal_e.npy`. Source shapes follow the fixed refinements; mean shapes match their corresponding observations. The private summary has exactly `format_version`, `runtime`, `plan_input_sha256`, `specimen_phases_at_specimen_origin_rad`, `source_model`, `source_mass`. Its format version is `full_noisy_study_truth_v1`; source model is literal `closed_midpoint_total_normalized_catalogue_order`.

`source_mass` has exactly `bead` and `specimen`; each has exactly `catalogue_total_e`, `stored_total_e`, `difference_e`, `relative_difference`, `unavailable_fields`. Targets are the exact sum of normalized catalogue brightnesses, sum of represented source cells, stored minus catalogue mass and that difference divided by catalogue mass. Use safe reductions. Values are finite floats or null; relative difference is null for zero catalogue mass. `unavailable_fields` is a list of objects with exactly `field` and `reason`, where field names one of these four scalars and reason is `zero_reference` or `unrepresentable`. Missing values never become zero. This reports the source contract's mass/storage limitation without changing its array API or asserting exact conservation.

Only after **all observation and private payloads** are closed/hashed, publish observation `complete.json`. Then publish `private_truth/complete.json`, with exactly `format_version`, `observation_manifest_sha256`, `files`; its files list is the exact private descriptors above, in the listed order. Finally publish root `generation.complete.json`, with exactly `format_version`, `status`, `observation_manifest_sha256`, `private_truth_manifest_sha256`; status is `generated`. The top-level marker distinguishes a completed generation command. A standalone complete observation bundle can be consumed without opening the top-level marker or private truth. Missing private/root markers never authorize repair/overwrite of earlier artifacts.

## Inference and freeze

Parse the five settings: `sweep_scales` is a strict JSON nonempty list of finite positive numbers, converted to the bead operation's built-in tuple without sorting/deduplication; regularization is finite positive; iteration/trial/pupil settings are positive integers. No implicit numerical defaults or optional truth-bearing arguments are selected. Verify observation manifest, exact descriptors, shapes/dtypes, payload completion, byte hashes and finiteness before scientific calls. Observation geometry/model/nominal commands must match this protocol. The actual manifest-byte SHA-256 is the observation identity.

Claim a new inference root. Estimate the scalar camera from the three actual eight-frame images using public `estimate_scalar_camera`. Its source label is exactly `full_noisy_study:<observation_sha256>:camera`. Preserve the complete returned record. A known estimator range failure produces a sealed unavailable outcome with no fabricated camera record. A valid nonpositive contrast likewise seals unavailable, preserving the camera record. Unavailable physical electron gain alone does not block reference-flat-relative inference.

For positive contrast, call the **complete** `fit_bead_calibration` with actual central/training/held-out images, that same camera record, known calibration origin and all supplied sweep scales. Its completed schedule includes all 47 coordinates, required Q256/Q512 rescores and held-out prediction/summaries. Preserve every returned trace, counter, information code, unprobed-coordinate declaration and partial record. Any status other than `completed_finite_fit` seals unavailable; do not use its partially frozen candidate to claim a completed fit. A completed schedule may honestly report unprobed/structurally limited coordinates; this is retained, not repaired by truth or a new rank threshold.

From its completed frozen candidate, take the estimated carriers, first-five phases and beam amplitudes. Verify the returned camera source, blank and contrast equal the paired camera gauge used by this invocation. Transfer phases exactly once by the preceding wrap formula using estimated carriers and known origins. The illumination label is `full_noisy_study:<observation_sha256>:bead_finite47`. No true registration/carrier/phase/brightness is consulted.

Allocate one plain native float64 specimen array `(3,5,*Ns)` and fill it from the 15 verified raw files. There is no unconditional second full-stack snapshot. Call `fit_specimen` with that raw array, the same actual camera estimate, explicit estimated illumination arrays already at specimen origin, known detector spacing/origin and the four specimen algorithm settings. No bead source/brightness/support or physical gain transfers into this fit. Preserve its actual returned status, source if present, complete scores, trace, call counters and diagnostics. A status other than `completed_finite_fit` seals unavailable without fabricating missing source/predictions.

Write any actually available bead held-out prediction to `bead_heldout_prediction.npy` and any actually returned specimen best source to `specimen_source_relative.npy`. These may be real partial-result payloads; their presence alone does not imply a complete inference. Serialize estimates to `estimates.json` **before** prediction export. It has exactly:

```text
format_version, observation_manifest_sha256, algorithm_settings, runtime,
fit_status, fit_stage, message, failure_code,
camera_estimate, bead_calibration, specimen_fit,
transferred_phases_at_specimen_origin_rad
```

Algorithm settings have exactly `sweep_scales`, `regularization`, `max_iterations`, `max_backtracking_trials`, `pupil_order`. Fit status is `completed_finite_fit` or `unavailable`. Fit stage is `complete`, `camera`, `camera_normalization`, `bead`, `phase_transfer` or `specimen`. Failure code is the original numerical range code, `full_noisy_study_range` for a concrete own arithmetic obstruction, or null for ordinary information outcomes. Message is a nonblank explanatory string. The transferred phases are `(3,5)` lists after successful transfer, otherwise null. A later prediction failure does not rewrite these earlier fit facts.

Serialization of scientific records is explicit and lossless for their public represented fields:

- Camera has exactly the nine public `ScalarCameraEstimate` keys: `means_counts`, `variances_counts2`, `frame_means_counts`, `frame_variances_counts2`, `empirical_mean_se_counts`, `contrast_counts`, `gain_counts_per_e`, `information_codes`, `source`. Small arrays/tuples become their dimension-preserving JSON lists; finite scalars and null follow the camera contract.
- Bead has exactly the `BeadCalibrationResult` field set and recursively the exact `PilotCandidate`, `BeadCalibrationScore`, `BeadCalibrationAttempt`, `BeadCoordinateEvidence` and `BeadCalibrationCounts` sets in the bead contract. All arrays are small nested lists except `heldout_prediction`, which is null or exactly `{"file":"bead_heldout_prediction.npy"}`. Do not omit failed attempts, unchanged-coordinate information, unresolved selections or candidate snapshots.
- Specimen has exactly the `SpecimenFitResult` field set and recursively its exact score, gradient, attempt, call and counts record sets in the specimen contract. All metadata arrays are small lists. `source_relative` is null or exactly `{"file":"specimen_source_relative.npy"}`. No per-trial source/gradient/prediction volumes are serialized.
- An operation never entered, or a camera operation that raised its known range error before returning, has its record field null. A returned unavailable/incomplete record is serialized as returned; it is not replaced by null. Each public tuple becomes a list; every other scalar type/domain/null meaning remains binding. Unexpected record fields, nonfinite scalars or inconsistent payload references are not silently serialized.

After a complete specimen fit, build one prediction cache using that result's exact source geometry/fixed optics/pupil order. For orientations 0,1,2, call the public forward map on the frozen returned source and exact estimated settings. Write its five finite signed float64 prediction volumes to `prediction_o0_p0.npy` through `prediction_o2_p4.npy`. Process one orientation at a time and discard/reuse its prediction payload after all five files close. No refit, best selection, intercept, clipping or truth-dependent step is allowed during prediction. Driver prediction calls are separate from the specimen solver's own counters.

`freeze.json` is the final inference manifest and has exactly:

```text
format_version, status, stage, message, failure_code,
observation_manifest_sha256, files, prediction_call_counts
```

Its status is `completed_finite_fit` only when estimates report that status and all 15 predictions exist, close, hash and validate. Its stage is then `complete`, and failure code is null. Otherwise a recognized scientific information/range outcome gives status `unavailable`, with stage from estimates or `prediction`; retain the original range code or null for ordinary unavailability. The files list includes, in order, `estimates.json`, the available bead prediction, the available specimen source, then only actually completed prediction files in orientation/phase order. No missing file receives a descriptor. A known prediction range failure can therefore retain prior complete orientation files and the genuine fitted source while declaring the pipeline unavailable. I/O/allocation/interruption does **not** receive a successful or unavailable completion seal.

Prediction counts have exactly `cache_attempted`, `cache_completed`, `cache_failed`, `forward_attempted`, `forward_completed`, `forward_failed`. Count each actual public call entered once; a completed call followed by failed file writing remains a completed call, but that writing failure leaves the command unsealed. Failed here means the recognized inverse range exception; actual allocation/unrelated exceptions propagate. Completed prediction export has counts `(1,1,0,3,3,0)`. Unentered work has zero counts. There are no private transform counts or invented timings. All freeze references and counts must agree with actual work and records.

## Evaluation order and fixed comparisons

The evaluator first validates **only** the observation bundle and inference freeze: exact schemas/file identities, all stored byte counts/hashes, required arrays and public-record shape/value consistency, exact matching observation-manifest hashes, and completed-versus-unavailable requirements. It validates every present frozen prediction/source payload before touching private truth. It must not open or inspect any private-truth path, even its manifest, before this succeeds.

Then open and validate private `complete.json`, its full listed payload identities, plan/summary schema and geometry agreement with observations; its observation hash must match. These digests establish content identity, not scientific authenticity against a malicious writer. Do not regenerate observations, change estimates, select a new seed or feed evaluation back to inference. Claim a new evaluation root only for the validated attempt.

For a sealed unavailable inference, produce a complete failure assessment with status `reported_unavailable`: identify the preserved fit/freeze stage, code/message and record statuses; scientific comparison fields below are null. Retain all actual upstream partial artifacts by reference. No invented zero source, partial prediction treated as complete, fallback estimate or recovery metric is produced.

For a completed finite inference, use the estimated contrast `d_hat>0` and estimated blank `b_hat` from the paired camera record. Define evaluator-only `a=true_gain/d_hat`, evaluated safely. There is **no fitted post-hoc scale, spatial registration, translation, crop or source-support alignment**.

Compare source coefficients by pairing generator axial cells at fixed indices:

```text
x_reference[k,y,x] = a * (source_e[2*k,y,x] + source_e[2*k+1,y,x]).
```

The generator lateral grid already equals the inverse lateral grid. This is mass aggregation of two fine axial cells into the coarse basis, not a statement that their centers or complete optical predictions are preserved. Evaluate the complete weighted expression safely; an overflowing unscaled intermediate sum alone is not the final relative-reference range test. Report the grid/source-model mismatch explicitly.

For each specimen exposure, with private optical signal mean `mu_e` and true camera coefficients, form two distinct prediction references:

```text
signal_reference = true_gain/d_hat * mu_e
corrected_mean_reference =
    (true_offset + true_gain*(mu_e + true_background) - b_hat) / d_hat.
```

Compare frozen predictions with each reference separately. The second exposes camera-gauge/blank-estimation error; it is not a fitted intercept. Also report signed observed residuals `prediction - (raw-b_hat)/d_hat`, with per-orientation/phase mean and root-mean-square over all specimen voxels. Training specimen residuals are not held-out validation. Bead held-out summaries remain the ones already produced after its own freeze.

`MetricSummary` has exactly `count`, `reference_l2`, `error_l2`, `relative_l2`, `error_rms`, `error_max_abs`, `error_mean`, `unavailable_fields`. Errors are estimated minus reference; count is the exact number of compared elements. Euclidean norms, full means/RMS and max absolute error use stable reductions. Relative L2 is error L2 divided by reference L2; it is null when the reference norm is exactly zero, even if the numerator is also zero. Other values are finite floats or null for an actually unrepresentable required statistic. Unavailable entries have exactly `field`, `reason`, where reason is `zero_reference` or `unrepresentable`. Compute independently available statistics rather than treating a raw norm/square overflow as loss of every metric. No epsilon denominator floor, clipping or zero substitution is allowed. This is descriptive finite arithmetic, not a recovery threshold.

Camera comparison has exactly `means_error_counts`, `contrast_error_counts`, `gain_error_counts_per_e`, `unavailable_fields`. Compare estimated means to true expectations `(offset, offset+gain*background, offset+gain*(background+flat_signal))`; compare contrast to `gain*flat_signal`; compare physical gain only if that estimate exists. Means error is a length-three list of finite floats or nulls; the other two errors are finite floats or null. Each unavailable-field object has exactly `field` and `reason`. Its field is `means_error_counts[0]`, `means_error_counts[1]`, `means_error_counts[2]`, `contrast_error_counts` or `gain_error_counts_per_e`; reason is `unrepresentable` or, for absent physical gain, `estimate_unavailable`. The same safe-arithmetic rule applies.

Bead-parameter comparison enumerates all six center/brightness permutations in lexicographic order, without moving any coordinate. Each entry has exactly `permutation`, `center_error_um_zyx`, `brightness_error_relative`; permutation maps fitted row `i` to true row `permutation[i]`. Brightness reference is `a*true_bead_brightness`. This reports legitimate bead labeling alternatives, not a fitted spatial alignment.

Illumination comparison contains exactly two entries, gauges `as_stored` and `global_side_exchange`. For the second transform the fitted candidate by `q -> -q`, `psi -> -psi`, `(a0,a+,a-) -> (a0,a-,a+)`; transform all orientations together because beam ratios are shared. Each entry has exactly `gauge`, `carrier_error_yx_per_um`, `phase_error_rad`, `wrapped_phase_error_rad`, `normalized_beam_error`. Compare calibration-origin nine phases to the private true phases, preserving raw differences and physical-period wrapped differences with the same stored endpoint convention `[-pi64,pi64)` defined above. Do not reduce arbitrary represented phases by rounded 2*pi64. Beam vectors are each normalized by their Euclidean norm before subtraction, using safe complete normalization even when a raw norm overflows; their common scale is not identified. The first entry exposes raw labeling; the second exposes this legitimate physical alternative. Do not choose a truth-aligned variant for any frozen source/prediction or alter inference output. If any required element of either parameter-comparison group is unrepresentable, that entire report field (`bead_permutation_comparisons` or `illumination_gauge_comparisons`) is null and is identified in the report's unavailable comparisons list. Otherwise every element in all its listed entries is finite; no nested nonfinite value or partially omitted alternative is emitted.

Write `evaluation.json` with exactly:

```text
format_version, status, message, runtime,
observation_manifest_sha256, inference_freeze_sha256, private_truth_manifest_sha256,
inference_status, inference_stage, inference_failure_code,
camera_comparison, source_metrics,
signal_prediction_metrics, corrected_mean_prediction_metrics,
observed_residual_mean, observed_residual_rms,
bead_permutation_comparisons, illumination_gauge_comparisons,
unavailable_comparisons, limitations
```

Evaluation status is `evaluated`, `evaluated_with_unavailable_metrics` or `reported_unavailable`. The middle status means the inference was complete but at least one requested descriptive statistic/comparison was unrepresentable or unavailable, including an unavailable physical gain or zero-reference relative metric. This is not success at a recovery threshold. The two prediction MetricSummary fields cover all 15 exposure payloads; observed residual summaries are `(3,5)` finite lists or null when unrepresentable. Unavailable comparisons is a list of exact `field`/`reason` objects; its fields name one of the report comparison fields and its reason is `inference_unavailable`, `estimate_unavailable`, `zero_reference` or `unrepresentable`. Per-scalar metric details remain in their local unavailable lists. On reported-unavailable outcomes all comparison fields are null, with corresponding `inference_unavailable` declarations.

Limitations is the fixed ordered string list `conditional_clear_pupil_model`, `finite_source_and_pixel_quadrature`, `paired_axial_mass_aggregation`, `finite_search_not_convergence`, `possible_unprobed_or_ambiguous_parameters`, `estimated_camera_gauge`, `training_residual_not_heldout_validation`, `no_recovery_accuracy_threshold`, `procedural_truth_boundary_only`. It supplies no new acceptance rule. Actual coordinate information and numerical sensitivity remain in the retained detailed records.

After closing/hashing that report, publish evaluation `complete.json` with exactly `format_version`, `status`, `observation_manifest_sha256`, `inference_freeze_sha256`, `private_truth_manifest_sha256`, `files`. Status matches the report; files is the one JSON descriptor for `evaluation.json`. Figures, optical/source/pixel/finite-field sensitivity studies and resource reports belong to later coordinator work using these identified artifacts. This driver adds no visualization framework or numerical study threshold.

## Errors, exit codes and partial states

The command's exit codes are:

| Code | Meaning |
|---|---|
| 0 | Generate completed; infer published a completed-finite freeze; or evaluate published an evaluated/evaluated-with-unavailable-metrics report. |
| 2 | CLI/algorithm-setting/private-plan syntax or domain error. |
| 3 | Infer published a valid unavailable freeze, or evaluate published reported_unavailable. This is a sealed scientific outcome, not completed reconstruction. |
| 4 | Missing/incomplete/malformed input protocol, bad expected filename/schema/payload, mismatched identity or failed byte digest. |
| 5 | Output ownership/exclusive-creation conflict or ordinary filesystem I/O failure. Existing and partial data remain intact. |
| 6 | Recognized generation scientific range failure, or other recognized required arithmetic failure before a legitimate inference unavailable seal can be produced. No completion is claimed. |

Known failures may emit one stderr JSON object with exactly `command`, `status`, `stage`, `error_code`, `cause_code`, `message`, `output_dir`. Status is `error`; command is one of the three names; code is `invalid_full_noisy_study`, `full_noisy_study_input_incomplete`, `full_noisy_study_input_invalid`, `full_noisy_study_integrity`, `full_noisy_study_output_exists`, `full_noisy_study_io` or `full_noisy_study_range`. Cause code preserves a known public SimreconError range code, otherwise null. Exact prose and generic argument-parser help/usage prose are not frozen. This diagnostic is not a completion artifact or a reason to modify an existing file.

Catch only the named scientific range codes at their real public boundaries: `simulation_source_range`, `simulation_optics_range`, `simulation_camera_range`, `scalar_camera_calibration_range`, `image_only_bead_calibration_range`, `image_only_calibration_pilot_range` when legitimately returned as the bead operation's documented dependency failure, `image_only_specimen_fit_range`, and `simulation_inverse_operator_range`. Returned public unavailable/incomplete records use their declared handling above. Other dependency errors and unrelated exceptions/warnings propagate; `MemoryError`, interruption and external timeout are never translated into a successful or unavailable seal. Their native process status is nonzero, not specified more narrowly. A write failure while preparing a seal is an unsealed I/O failure, not exit 3.

Expected own numerical warning handling is locally scoped and preserves NumPy/warning policies. No broad warning suppression, daemon, silent retry, automatic smaller case, approximation substitution or resource-to-success conversion is permitted. There is no command wall-clock cap or portable memory guarantee. Preserve actual partial files after every failure, including a partial final JSON file; readers reject it. No second invocation can overwrite it.

## Independent proof, staging and limits

Future fresh A/B proof must use real public commands and actual scientific composition. It must distinguish a real complete small noisy camera → complete 47-coordinate bead fit → specimen finite fit → prediction freeze → evaluation run from an honest sealed unavailable small case. Keep held-out data out of training decisions, maintain the paired estimated gauge, transfer phase once and prove all configured finite-coordinate polls actually run under the bead contract. A small successful case is not a full-trial substitute.

File/data-flow proof covers strict keys and fixed names; non-pickle exact NPY payloads and hashes; exclusive creation including existing empty directories/symlinks; unchanged inputs; partial writes and absent/invalid completion markers; retained actual partial results; prediction completion before freeze; public verification before opening truth; and unchanged inference outputs when evaluator-only plan/truth/seed/mean files change while observation bytes/settings/runtime remain fixed. Controlled external filesystem faults are permitted at the real CLI/I/O boundary; no production test-only seam or fabricated successful numerical result is authorized.

Only after completed scientific prerequisites, real small workflow evidence and the required inverse/generator resource stages should the coordinator execute the full `(32,256,256)`, three-orientation/five-phase case. Fifteen float64 raw volumes contain 251,658,240 bytes; separate private means, frozen predictions, sources, file cache and solver work add to this. Measure actual time, footprint/headroom, swap/disk and status under the existing 16 GiB-host staging context; do not infer a guarantee from payload arithmetic. Keep missing measurements unknown. Full photon/read-noise acquisition, actual image-derived camera/illumination estimates, complete source fit and frozen evaluation remain required by the owner's original task.

No material scientific objective or accuracy threshold is added. No new unresolved scientific choice is intentionally left in this protocol: plan/settings values are explicit later coordinator experiment choices, not missing API semantics. Full-size feasibility and recovery remain unestablished. Adoption still requires coordinator assessment and exact completed prerequisite identities.

## Public expectations and delivery

Expected scientific behavior comes from this contract, [finite bead calibration](image-only-bead-calibration-v1.md), [specimen fit](image-only-specimen-fit-v1.md), [source](simulation-sources-v1.md), [optics](simulation-optics-v1.md), [camera sampling](simulation-camera-v1.md), [camera estimation](scalar-camera-calibration-v1.md) and [inverse](simulation-inverse-operator-v1.md) contracts. Runtime output is not an independent numerical oracle.

Fresh native blind A/fresh B/restricted C/fresh D. A owns only tests/test_full_noisy_study.py and optional tests/full_noisy_study_fixture.py. C owns only scripts/full_noisy_study.py. Scientific/binary/persistence behavior remains high risk; C cannot alter reviewed tests/helpers, dependencies/configuration/gates/policy or unrelated interfaces. Coordinator owns concrete plans, execution, scientific studies/reports/figures and preservation-aware completion cleanup. Inherit the active named full-noisy advisory-percentage migration without weakening behavior/risk review, exact thirteen full-local phases, native reports or required platforms. Human numeric limits are not set; all previous charges remain retained.
