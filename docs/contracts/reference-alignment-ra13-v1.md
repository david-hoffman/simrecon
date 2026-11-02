# RA13 — raw-array scientific workflow

**Version 1.0.** Authorized composition of accepted camera, RA12 calibration
handoff and physical specimen fitting. This adds no estimator, optical premise,
convergence guarantee or recovery criterion. Later owner clarification governs:
**“Keep noisy fits diagnostic; certify only noiseless finite-model controls.”**
Noisy controls can pass by correctly reporting unavailable. Original RA12 noisy
misfit is preserved. RA14 evaluates the full scene; stop before RA15 for discussion.

## Public boundary and composition

The development module `scripts.raw_sim_workflow` exposes one operation and one
frozen-binding result. It is an in-memory public workflow, not a wheel export,
file adapter or command-line interface.

```python
reconstruct_raw_sim(
    specimen_counts, *, dark_counts, blank_counts, flat_counts,
    central_counts, structured_counts, heldout_counts,
    calibration_id, specimen_calibration_id,
    calibration_origin_um_zyx, specimen_detector_spacing_um_zyx,
    specimen_origin_um_zyx, sweep_scales, max_refinement_evaluations,
    training_rms_limit, calibration_atol, operator_atol,
    regularization, max_iterations, max_backtracking_trials, source,
) -> RawSIMWorkflowResult
```

All shown keywords are required. Ordinary binding errors raise `TypeError`.
No supplied true camera, illumination, bead position, specimen source, noiseless
mean, support mask, optimizer callback or transfer array is accepted. No fallback
mode, automatic retuning or truth evaluation exists in this operation.

After complete caller-input validation and provenance construction:

1. Call public `estimate_scalar_camera(dark_counts, blank_counts=...,
   flat_counts=..., source=source)` once.
2. Call public `infer_calibration_handoff` with the original three calibration
   arrays, that camera record and the declared existing controls/geometry/source.
   Derive specimen detector shape from `specimen_counts.shape[2:]`.
3. Only a `predictive_estimate` handoff with its actual specimen descriptor
   permits `fit_specimen`. Pass original raw specimen counts and all descriptor
   fields directly, plus the explicit specimen-fit controls. The descriptor fixes
   Q128, source half-cell geometry, common gauge and specimen-origin phases.
4. Return every reached component record and complete provenance. Preserve all
   finite stopping diagnostics, including iteration limits and partial fits.

Neither wrapper nor caller correction is inserted before these stages. Each
owning component corrects its raw counts once. The handoff transfers first-five
physical phases to the specimen origin once; the fitter consumes them directly.
Do not wrap/transfer phases again, normalize beams/orders, equalize exposures,
rescale output or substitute RA05/RA08/RA09/RA10 models/objectives.

The inherited model is the RA12 finite clear-pupil three-beam synthetic model:
excitation/emission 0.488/0.525 µm, refractive index 1.515, detection numerical
aperture 1.4 and 2×2 pixel midpoint sampling. Calibration spacing is fixed at
(0.125,0.080,0.080) µm with three radius-0.050 µm spheres. Specimen source shape
is `(Z,2Y,2X)`, spacing `(Dz,Dy/2,Dx/2)` and half-cell coordinates. This is not an
empirical instrument calibration or a claim that physical source modes are identified.

## Complete validation before estimation

Validate every supplied array, pairing label, origin, spacing and control before
camera estimation. An unavailable calibration or camera range failure must not
hide malformed specimen counts or fit controls. Simultaneously invalid precedence
is unspecified. Wrapper validation raises `SimreconError` with code
`invalid_raw_sim_workflow` and identifies the offending field; exact prose is not
promised. Do not call a numerical component just to validate it or extract private
component validators. Small local grammar checks are allowed.

- `specimen_counts`: exact plain ndarray, native float64, rank five and leading
  shape `(3,5)`; all spatial dimensions positive and all values finite. Signed,
  strided, reversed, Fortran, read-only and zero-stride storage remain legal.
  Non-native endian/other dtype kinds or widths, subclasses, lists and nonarrays
  are invalid, as in the selected specimen consumer.
- Camera groups inherit the [camera grammar](scalar-camera-calibration-v1.md#input-representation):
  plain integer/unsigned/floating ndarrays, rank three, >=2 frames per group,
  common positive y/x dimensions with >=2 pixels per frame. Counts may be signed;
  endian, width and layout variants are allowed. Every original value and its
  float64 normalization must be finite. Reject bool/complex/object and subclasses.
- Calibration groups inherit [bead grammar](image-only-bead-calibration-v1.md#3-inputs-validation-and-snapshots):
  central shape `(Zc,Yc,Xc)`, structured `(3,9,Zc,Yc,Xc)`, held-out
  `(3,5,Zc,Yc,Xc)`, positive dimensions and each calibration physical side >=0.100 µm.
  All are plain real i/u/f ndarrays with finite original and float64-normalized
  values; signed/endian/layout/read-only variants and finite conversion rounding
  remain legal. The calibration and specimen grids may differ.
- `calibration_id`, `specimen_calibration_id`, `source`: nonblank built-in strings,
  preserved unchanged. The two IDs must be exactly equal. The ID asserts intended
  pairing of camera, calibration and specimen; it authenticates no acquisition.
- Calibration origin inherits the RA12 tuple grammar, including tuple subclasses.
  Specimen origin and spacing use the stricter fit grammar: built-in length-three
  tuples of built-in int/float scalars excluding booleans/subclasses, normalized to
  finite float64; spacing is strictly positive, origins may be signed/zero.
- `sweep_scales`: nonempty built-in tuple, each built-in int/float excluding
  bool/subclasses, normalized finite strictly positive float64; preserve order and
  duplicates. `max_refinement_evaluations`, `max_iterations` and
  `max_backtracking_trials`: positive built-in int, excluding bool/subclasses.
- `training_rms_limit`: built-in int/float excluding bool/subclasses, normalized
  finite nonnegative float64. `calibration_atol`, `operator_atol`, `regularization`
  use the same grammar but are strictly positive. No hidden default or cap exists.

Validate supplied domains only. Concrete derived spacing/indexing/model range
obstructions remain their owning components' operation-time outcomes. Actual
`MemoryError`, unrelated exceptions and unrelated warning categories propagate.
Preserve caller data, flags/layout, NumPy error policy, warning policy and random
state on return or exception. Concurrent external mutation is outside the promise.
Borrow specimen data read-only; do not unconditionally duplicate its full payload.
The component snapshot guarantees remain unchanged.

## Result and operation-time outcomes

`RawSIMWorkflowResult` has exactly these bindings:

```text
status, stage, reason_code, failure_code, message,
camera_estimate, handoff, specimen_fit, provenance
```

- Recognized camera `scalar_camera_calibration_range` errors return
  `status="numerical_incomplete"`, `stage="camera"`, `reason_code=None`, original
  failure code/message and all three component records `None`. No partial camera
  record is fabricated. Other camera exceptions propagate.
- Handoff `unavailable` or `numerical_incomplete` returns that status and
  `stage="handoff"`, copying its reason code, failure code and message. Keep camera
  and complete handoff records; `specimen_fit=None`. A retained candidate is not
  consumed as successful illumination. Nonpositive camera contrast reaches the
  ordinary handoff outcome with its diagnostics.
- After an accepted handoff, preserve the actual fit result. A numerical-incomplete
  fit returns `stage="specimen"`, `reason_code=fit.stop_reason`, its original
  failure code/message, and all reached records including any partial source.
- A completed finite fit returns `status="completed_finite_fit"`, `stage="complete"`,
  top-level reason/failure codes `None`, and a truthful message. Its stopping reason
  remains in the fit record. This asserts finite execution, not convergence.
- A fit's `normalization_unavailable`, if reached, maps to `unavailable` at
  `specimen`, preserving its stop reason/failure/message and records. The normal
  successful handoff supplies positive contrast; this mapping adds no retry.

Reconstruction is `result.specimen_fit.source_relative` when present. Do not add
a second top-level copied/aliased reconstruction. Component record/array meanings,
ownership and limitations stay unchanged; direct result construction authenticates
nothing. New provenance contains no borrowed caller arrays.

## In-memory provenance

Before estimation, record all seven original arrays (`specimen_counts`, three
camera groups, three calibration groups). Each entry contains `shape` as a tuple,
`dtype` as original `dtype.str`, `nbytes` as logical byte count, `sha256` of original
logical element bytes in C index order and `axes` (specimen/structured/held-out:
`orientation,phase,z,y,x`; central: `z,y,x`; camera: `frame,y,x`). No normalization,
byte swap, correction or pixel reordering precedes hashing. Layout-equivalent
arrays have identical hashes; different endian/signed-zero/padding bytes may differ.
This identifies supplied representation, not physical equivalence or authenticity.
Use bounded traversal for noncontiguous specimen hashing rather than a full payload
snapshot. Input arrays are not archived by the operation.

The independent provenance dict has `schema="ra13.raw_sim_workflow.v1"`, `source`,
both pairing IDs, `inputs` keyed by the seven argument names, `geometry`, `controls`,
`units`, `model`, `versions` and `limits`. Geometry records both origins and fixed
calibration spacing, derived specimen detector shape, declared specimen spacing and
selected source shape. Controls record every normalized explicit numerical control.
Units record detector counts and integrated reference-flat-relative source weights.
Model identifies RA12 v1.1 plus specimen-fit v1 and the fixed optical/pixel/source
assumptions above. Versions record Python, NumPy and SciPy versions; exact source,
lock, command and execution identity belongs to the external run manifest. Limits
state finite procedure only, global identification unestablished, no convergence,
statistical confidence, instrument accuracy or resolution/recovery guarantee.

No runtime Git command, filesystem discovery, timestamp, persistence, random
sampling, generator/evaluator import or automatic repair loop is added.

## Behavioral inventory and acceptance

| ID | Observable obligation / credible failure |
| --- | --- |
| W1 | Real noiseless observation-only workflow agrees with explicit accepted component composition; wrong ordering, double correction or wrong model differs. |
| W2 | Nonzero origins, unequal beam sides and first-five actual phase reuse reach the real specimen consumer once; a second coordinate transfer differs. |
| W3 | Unavailable or numerical-incomplete handoff, including the fixed noisy diagnostic, propagates actual status and complete diagnostics; retained candidates never substitute for missing illumination. A noisy handoff that succeeds remains diagnostic and may proceed to finite fitting. |
| W4 | Camera arithmetic range returns numerical-incomplete with no fabricated component; unrelated exceptions retain meaning. |
| W5 | All malformed supplied inputs, mismatch and fit controls reject before estimation, even on otherwise unavailable inputs. |
| W6 | Legal signed/layout/read-only and inherited camera/calibration representations remain accepted; grids may differ. |
| W7 | All reached component records/stops/partial outcomes remain visible; no limit becomes convergence/recovery. |
| W8 | Complete input/geometry/control/unit/version provenance matches original representation, with owned metadata and unchanged caller state. |
| W9 | Public API accepts no private truth or tuning fallback; binding and purity hold through real public boundary. |
| W10 | Executed small noiseless finite control and fixed noisy diagnostic have truthful separate claims and informative fixed-center figures. |

A independently authors the integration tests/fixtures. Accepted components already
own their numerical algorithms; repeat arithmetic only for an independently
justified integrated obligation. Public composition comparisons prove wiring, not
independent optical accuracy. Noiseless finite controls validate named arithmetic,
gauge, prediction and finite-fit behavior; noisy controls validate diagnostics and
failure propagation only. Do not require noisy recovery. Derived tolerances need
independent operation/precision/component-budget justification. No manufactured
red test, mutation requirement or percentage-driven cases.

Full local exact-candidate verification, fresh blind A/B, restricted C, fresh D,
required Ubuntu/macOS CI, executed usage and figure-bearing PR precede readiness.
Coverage percentages are advisory; complete native report integrity remains binding.
