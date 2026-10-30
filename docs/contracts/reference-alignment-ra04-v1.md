# RA04 — Preserve camera and intensity meaning

Version 1.0, contract revision 2. Concrete task contract under the owner's authorized 15-step reference-alignment roadmap. Baseline: accepted RA03 commit 6329259ca2e58db41579e9a235ac8a436e0236c6. High risk. This contract adds a narrow paired correction adapter. It selects no new estimator or reconstruction algorithm.

## Public operation

Export `correct_alignment_pair`, `AlignmentCameraPair` and `AlignmentCameraFrames` from `simrecon`:

```python
correct_alignment_pair(
    specimen, *, bead, mode, output_unit, gauge_source,
    specimen_exposure_factor, bead_exposure_factor,
    reference_sum_equalization,
    specimen_offset=None, specimen_response=None,
    bead_offset=None, bead_response=None, camera_estimate=None,
) -> AlignmentCameraPair
```

`specimen` and `bead` are public `RawAcquisition` outputs. Require kinds `specimen_sim` and `sim_beads`, respectively. Shapes may differ. Each resolved intensity unit must be a nonempty string. In declared mode the two input-unit labels may differ: each corresponding response explicitly means that member's raw unit per common output signal unit. In estimated mode both input-unit labels must be the same exact string, expressing the caller's declaration that one affine count calibration applies to both. The ScalarCameraEstimate itself has no input-unit field, so the adapter cannot independently verify that count scale. Calibration IDs are opaque provenance in both modes: unequal, equal or missing IDs are all retained without being interpreted as compatibility evidence. No arbitrary interpretation of original metadata, unit spelling or IDs authenticates the physical pairing. Other valid RawAcquisition metadata and coordinates remain unchanged. Passing an already corrected result instead of a RawAcquisition is invalid; no implicit second correction.

`mode` is exactly `declared` or `estimated`. `output_unit` and `gauge_source` are nonblank strings retained exactly. Units are opaque labels. All supplied coefficients assert a common output signal gauge; the adapter verifies structural declarations, not physical truth. It never matches image sums or fits hidden scale to specimen/bead data.

In declared mode all four offset/response arguments are required and `camera_estimate` must be None. Coefficients have exactly the existing `correct_linear_response` domain: built-in int/float except bool, or plain i/u/f ndarray with exactly the corresponding canonical full data shape. No broadcasting, NumPy scalar or coefficient protocol is added. Each offset is the applicable effective sensor-plus-optical subtraction baseline O=o+r*t*B in input counts at that member's actual acquisition conditions; each positive response is input counts per output signal unit at the declared reference exposure. Distinct member coefficients/maps are legal if they express the same declared output gauge. Values are supplied, never inferred.

In estimated mode the four supplied coefficients must all be None, and camera_estimate must be a `ScalarCameraEstimate` returned by the public estimator. Its public invariants apply; arbitrary manual corruption is outside this boundary. Require output_unit exactly `reference_flat_relative`. Take offset M_B and response dM from this single camera record for both members. Preserve its source, information codes, mean/variance and repeatability statistics, and optional physical gain separately from output-unit meaning. `gauge_source` remains the caller's opaque composition label. An unavailable physical gain does not prevent correction with positive dM. Nonpositive dM gives a complete unavailable result, never division by zero or identity substitution.

## Explicit exposure and arithmetic

Each exposure factor is required, dimensionless and relative to the one declared reference exposure. Accept a built-in int/float except bool or plain i/u/f ndarray with exactly the corresponding full canonical data shape. Convert once to native float64; require original and converted finite values and strictly positive represented factors, including positive subnormal values. A scalar explicitly applies everywhere. Arrays must already include any time/channel/orientation/phase/z expansion; no broadcasting or axis inference is allowed.

Declared forward relation for each sample:

```
C = offset + response * exposure_factor * S_ref
A = RN64(RN64(C64 - offset64) / response64)
S_ref = RN64(A / exposure_factor64)
```

Use the existing public linear correction first, then a distinct binary64 exposure division. Do not combine response*factor: its intermediate range/rounding differs. Signed finite samples, subnormal results and signed underflow zero are valid. Reject any nonfinite subtraction, linear quotient or final exposure quotient as specified below. The contract promises these sequential finite operations, not a fused exact-real quotient.

Estimated mode inherits the scalar estimator's matched stationary acquisition conditions. Every exposure factor must be exactly one after conversion. Any other otherwise-valid factor makes this mode unavailable: the public estimate asserts matched stationary conditions, not the extra acquisition law for a new condition. The dark mean M_D does estimate sensor offset. Under an additionally declared exposure-scaling background law, ((C-M_D)/t-(M_B-M_D))/dM could correct the mean, but that law and its operation order are not selected in this mode. This is an explicitly unsupported mode, not a claim of mathematical nonidentifiability. Do not scale M_B or infer a new acquisition law. Declared mode with independently supplied applicable offsets/responses can express exposure correction. No recorded factor is treated as seconds or inferred from a frame sum.

`reference_sum_equalization` is required. `disabled` performs no image-sum normalization. `per_frame_sum` returns unavailable for this target mode. An unknown selector is invalid. Sparse carrier-rich signal provides a direct counterexample: for a point of amplitude a at x0 under 1+m*cos(k*x+phi), frame total is a*(1+m*cos(k*x0+phi)); changing phi changes a legitimate total. Sum division erases signal information. No arbitrary conservation assumption or C-camera pixel heuristic is enabled.

## Complete output and provenance

AlignmentCameraPair is a frozen-binding record with:

- status: `corrected` or `unavailable`.
- information_codes: tuple in fixed order: `reference_sum_equalization_unavailable`, `estimated_exposure_unavailable`, `nonpositive_flat_contrast`, including all applicable conditions. These are value outcomes; they do not certify instrument applicability.
- specimen and bead: each an `AlignmentCameraFrames` in final output units when corrected, otherwise both None. Its fields are `data`, `axes`, `input_unit`, `output_unit`, `source_metadata` and `provenance`. Data contains S_ref, not pre-exposure A. Preserve axes, input/output units and the independent source metadata snapshot from the public linear correction. Its data is independently owned C-contiguous plain native float64. A caller-supplied factor of one is still recorded once.
- mode, output_unit, gauge_source, reference_sum_equalization: exact selected strings.
- specimen_exposure_factor and bead_exposure_factor: independently owned normalized float64 scalar values or exact-fullshape C-contiguous plain float64 arrays.
- camera_estimate: independent deep snapshot of the supplied estimated record, or None for declared mode. Retain every original public statistic and source, never reuse its mutable arrays. This is uncertainty/provenance input, not an automatic reconstruction weight or calibrated photon claim.

Each corrected member's provenance has these exact keys: `model="alignment_camera_v1"`; `equation="raw=offset+response*exposure_factor*signal"`; `gauge_source`; `coefficient_origin` equal to mode; `camera_source` equal to estimate.source or None; `linear_response` equal to an independent snapshot of the unchanged public linear-correction provenance; `operations=("subtract_offset", "divide_response", "divide_exposure")`; and `exposure_factor={"supplied": independent_original_factor, "applied": independent_normalized_factor}`. This records exactly one offset application, one response division and one exposure division in order. Do not rewrite the nested primitive equation as if its output were already exposure corrected. Existing `correct_linear_response` applied offset/response records retain their public meaning (its arguments are supplied by the adapter); the paired provenance must make the estimator origin explicit. Snapshot all metadata and arrays without aliases with callers, either member, camera statistics, coefficient/exposure records or another call. Preserve source acquisition metadata separately from corrected unit labels. Outputs mutable by convention despite frozen bindings.

Unavailable outcomes contain no partial corrected member. Valid declared coefficients, exposure factors and raw pixels still undergo domain validation before unavailable selection. Original/nonfinite pixels follow existing linear-response rejection semantics. Arithmetic subtraction/division/range stages are evaluated only on an available correction path; unavailability does not manufacture arithmetic-stage errors. In estimated mode nonpositive contrast is a value outcome rather than an invalid-response error. Simultaneous error precedence and exact error prose are unspecified.

Blank subtraction removes estimated mean background, not its photon noise. Preserve V_B and dV=V_F-V_B ingredients through the full snapshot, including negative observed variance contrast. Under the existing matched scalar law only, a descriptive relative mean u>=0 has plug-in variance (V_B+dV*u)/dM^2 when dV>=0. This remains a diagnostic, not a guaranteed uncertainty bound. With changed exposure or declared maps there is no automatic noise model. Empirical mean standard errors describe calibration repeatability; they are not standard deviations of a new corrected sample. Unknown absolute gain never changes relative units to electrons/photons. No new uncertainty formula is a product output in this slice.

## Validation and compatibility

Use existing SimreconError codes for raw pixel/coefficient/linear-stage domain and range failures from correct_linear_response. New codes:

| Code | Outcome |
|---|---|
| invalid_alignment_camera | wrong acquisition/record/kind, mode/selector/string/union arguments, missing/invalid input unit or mismatched estimated-mode count-unit labels |
| invalid_alignment_exposure | unsupported scalar/array, wrong shape/dtype, nonfinite/unrepresentable/nonpositive converted factor |
| alignment_camera_range | nonfinite final exposure quotient |

Ordinary argument-binding TypeError, actual MemoryError and unrelated exceptions propagate. Preserve all inputs, caller NumPy error settings and warning filters on success/rejection/unavailable. Handle expected conversion/range/underflow without arithmetic RuntimeWarning/FloatingPointError. Suppress no unrelated categories. No arbitrary array/intensity/timing cap; no concurrent external mutation promise or full-volume memory guarantee.

The existing linear correction, scalar estimator, bead/specimen fitting and reconstruction contracts remain unchanged. This additive adapter prepares explicit arrays for their real public callers. Do not pass its corrected arrays into an existing fitter that performs its own blank/dM normalization: that would correct twice. Use direct reconstruction composition and document the boundary; no fitter API migration is authorized without an actual need. Test signed constant and point controls through existing reconstruction with fixed transfer and fixed regularization convention. Point checks target reconstructed coefficient amplitude or integrated intensity on a fixed field of view with the existing sampling/transfer normalization, not invariant peak pixels under blur/interpolation/cropping. A common positive scale must survive the linear reconstruction when other settings are fixed; this is no general recovered-source claim.

## Scenario inventory and ownership

| ID | Distinct observable obligation |
|---|---|
| R01 | Declared pair corrects known offset/response into one common gauge, distinct shapes/kinds |
| R02 | Scalar/full-shape coefficient combinations follow each member's canonical coordinates |
| R03 | Explicit scalar/full-shape exposure divides once in declared mode |
| R04 | Sequential binary64 order/range is preserved rather than combining response*exposure |
| R05 | Signed samples, negative offsets, subnormals and signed underflow remain valid |
| R06 | Estimated single-record MB/dM gauge corrects both members, physical gain availability independent |
| R07 | Nonpositive estimated contrast yields complete unavailable result |
| R08 | Estimated changed exposure yields unavailable without invented blank scaling |
| R09 | Disabled sum equalization preserves legitimate phase-dependent sparse-object sums |
| R10 | Requested per-frame sum mode unavailable, unknown selector invalid |
| R11 | Wrong type/kind/union mode arguments and invalid strings rejected |
| R12 | Estimated-mode count-unit labels must match; missing/invalid input units rejected in both modes |
| R13 | Coefficient shape/bad response/nonfinite pixel domain uses existing explicit outcomes |
| R14 | Exposure type/shape/nonfinite/range/zero/negative domain rejected, positive extremes accepted within arithmetic limits |
| R15 | Linear-stage and final exposure-stage range failures are distinct and complete |
| R16 | Provenance separates supplied/estimated origin and records each operation once |
| R17 | No mutable aliases or input/error/warning-policy changes across all outcomes |
| R18 | All estimated noise/repeatability/gain statistics retained; blank variance not removed |
| R19 | Real signed constant and point reconstruction preserve applicable scale with fixed transfer/convention |
| R20 | Existing interfaces remain compatible; corrected results cannot be implicitly corrected twice |
| R21 | Required unit-chain documentation and measured known/estimated gauge/sum-control figures state limits |
| R22 | Declared different input-unit labels accepted through separate declared responses into common output unit |
| R23 | Equal/different/missing calibration IDs retained as opaque provenance in both modes; no inferred pairing |

All boundaries/branches are behavior obligations, not a scenario cap or test quota. A owns `tests/test_reference_alignment_ra04.py` and `tests/reference_alignment_ra04_fixture.py`; tests supply independent known/estimated camera/exposure controls usable by coordinator figures. C owns `src/simrecon/_alignment_camera.py` and additive exports in `src/simrecon/__init__.py`. Diagnosed primitive changes in `_linear_response.py` or `_scalar_camera_calibration.py` require coordinator scope record; do not self-expand. C cannot edit reviewed tests/fixtures/snapshots/checks/workflows/discovery/coverage/skills/policy. Coordinator owns this contract, task pointer, usage/report/figures and ignored evidence. Fresh native A/B/C/D are Sol/high; report-only Astra/ultra mathematics replaces no role. Actual served attribution/cost unknown unless observed; cumulative charges retained; human numeric limits not set.

Inherited approved coverage policy: behavior coverage plus independent risk review; percentages advisory with no selected percentage threshold. Native Coverage.py reports globally/per owned package on Ubuntu24.04/macOS15 include never-imported owned runtime/delivery files and relevant subprocesses; no runtime exclusions. Missing/malformed required reports block; percentages alone do not. Blind A/B receive this contract, named public dependencies, source-free diagnostic harness and no implementation/history/state/coverage maps/lessons. A maps observable obligations, credible failures and distinct proof gaps; B independently challenges omissions, legitimate positives, oracles/tolerances. Exact full local `make verify` and fresh D precede any PR; both hosted platforms and completion cleanup precede new RA05. Focused checks include existing linear/scalar/image-only-specimen tests and new adapter tests. No legacy C build/run/import/link/copy, no Superpowers/merge/release/unrelated messages.
