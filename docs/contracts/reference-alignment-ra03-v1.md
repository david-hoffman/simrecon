# RA03: source representation and illumination controls

**Version 1.0. Authorized 29 October 2026.** High-risk scientific evaluator, stacked on accepted RA02 e994e131b5506fe4291d7dcbc817e91150d3933f. The owner authorized every RA01–RA15 step, a separate chat/stacked PR per step, actual figures and automatic successor creation; RA03 neither merges nor executes legacy C.

## Public evaluator boundary

New module `scripts/reference_alignment_ra03.py` exposes:

```python
evaluate_orientation(
    fine_source_e, reference_signal_e, original_source_relative,
    original_prediction_relative, *, detector_spacing_um_zyx,
    true_carrier_yx_per_um, estimated_carrier_yx_per_um,
    true_phases_at_calibration_origin_rad,
    estimated_phases_at_calibration_origin_rad,
    true_beam_amplitudes, estimated_beam_amplitudes,
    calibration_origin_um_zyx, specimen_origin_um_zyx,
    source_to_relative, excitation_um, emission_um, refractive_index,
    detection_na, pupil_order,
) -> dict

summarize_errors(reference, predictions) -> dict

fixed_center_views(volume, *, spacing_um_zyx, origin_um_zyx,
                   center_um_zyx) -> dict
```

This is an in-repository evaluator, not an inference/public-library extension. All inputs are explicit; no truth lookup, file access, fit, random choice, clipping or normalization. Existing generator and inverse contracts retain their numerical and input/error semantics. No product correction is presumed.

### Geometry, inputs and gauge

For this evaluator the detector is `(Nz,Ny,Nx)` with spacing D in µm. Fine source is native-width float64, shape `(2Nz,2Ny,2Nx)`, with refinement `(2,2,2)`; source weights are integrated electrons. Reference is float64 `(P,Nz,Ny,Nx)` with P>=1. Original source is float32 `(Nz,2Ny,2Nx)` in reference-flat-relative units; original prediction is float64 and has reference shape. Plain ndarrays only, any byte order/layout/read-only variant; all finite, fine source and reference nonnegative. The original source and prediction may be signed. Scalar coefficient grammar and physical domains inherit the generator/inverse contracts. Both carrier arrays have shape `(2,)`; both phase arrays shape `(P,)`. Origins are three finite ordinary numerical coordinates; no axial origin phase correction is inserted into the focal-relative illumination model. source_to_relative is a finite strictly positive ordinary scalar representing known gain/estimated flat-minus-blank contrast. It is a predeclared camera-gauge conversion, never a fitted image/source scale. Wrong evaluator array shape/kind, invalid origins/scale and incompatible phase counts raise ValueError identifying the input; ordinary missing/unknown arguments raise TypeError. Existing delegated numerical/domain exceptions and MemoryError propagate. No partial successful result after an operation fails. No arbitrary shape/time cap or promise of universal extreme-range metric arithmetic. Concrete nonfinite derived evaluator arrays/reductions report ValueError; unrelated exceptions propagate.

Paired source64 is `source_to_relative * (fine_source_e[0::2]+fine_source_e[1::2])`, with float64 addition then multiplication, at half-cell sites `(k+1/2)*D_z`, lateral spacing `(D_y/2,D_x/2)`. Paired32 explicitly rounds that result once to float32. Report source rounding separately, including nonzero coefficients lost and mass change. Pairing moves fine weights by +/-D_z/4 and is not a forward equivalence or density conversion; it is not a fresh coarse-grid sphere catalogue. The full-study representation ledger independently records pair-sum rounding and gauge-multiplication rounding before the cast32 ledger, using exact dyadic totals or an equivalent justified observer.

For each carrier q, transfer calibration-origin phase once:
`phi_spec = phi_cal + 2*pi*q dot (origin_spec_yx-origin_cal_yx)`.
Only equivalent wrapping modulo 2*pi is permitted. Hybrid interventions are defined in this calibration-origin gauge: carrier-only uses estimated q with true calibration-origin phases and true beams, recomputing both origin transfer and physical kappa(q); phase-only uses true q, estimated calibration-origin phases and true beams; beam-only uses true q/phases and estimated beams. Estimated uses all estimated quantities. Origin transfer is recomputed from the carrier of each arm, never added to already transferred phases. Unequal plus/minus beams remain ordered. These are controlled interventions in a declared gauge, not unique causal attribution.

### Required arrays and manifest

The return dictionary has `arrays`, `sources`, `arms`, `metrics`, `rounding`.
`arrays` maps these exact names to independent owned writable float64 arrays of reference shape:
- `fine_reference`: archived reference_signal_e times source_to_relative, explicitly labeled archived fine-generator result, not regenerated;
- `paired_generator64_true`: expected_images at paired source64, refinement `(1,2,2)`, pixels `(2,2)`, true illumination;
- `paired_generator32_true`: same generator evaluated on the exact represented paired32 values (converted to float64 without change), keeping all settings fixed;
- `paired_inverse_true`, `paired_inverse_estimated`, `paired_inverse_carrier_only`, `paired_inverse_phase_only`, `paired_inverse_beam_only`: current forward at paired32, source spacing `(D_z,D_y/2,D_x/2)`, supplied fixed optics and arm illumination;
- `original_prediction`: unmodified archived prediction values, already in relative gauge;
- `original_fit_reapplied`: current forward applied to original float32 source with estimated illumination; no refit.

`sources` contains independent owned writable native `paired64` and `paired32` arrays. All source/data inputs, caller numerical settings and global random state remain unchanged. One shared cache may be used within a call; no cross-call hidden state. `arms` is a mapping for the five paired inverse names and original_fit_reapplied, each containing `carrier_yx_per_um`, `phases_at_calibration_origin_rad`, `phases_at_specimen_origin_rad`, `beam_amplitudes` plus plain-English `source`/`interpretation`. Numeric manifest arrays/lists equal the settings actually applied. Per-call cache metadata and array hashes may be included as supplemental provenance; no private backend/call count is prescribed.

`metrics` equals summarize_errors(arrays['fine_reference'], every other named array). `rounding` contains `relative_l2`, `max_abs`, `sum_change`, `nonzero_lost`, `changed_coefficients`, computed on paired32 versus paired64 with no added scale; denominator-zero semantics below apply. The full field comparison of paired generator32 with inverse true combines physical-to-represented cache error and numerical application. It must not be mislabeled isolated kernel rounding or arithmetic. Separate independent tiny controls are required for those quantities. The matched generator32/inverse contrast uses the identical four pixel midpoint target, so it has no pixel-model mismatch. Pixel-count changes are a separate discretization intervention. Archived fine versus paired generator64 includes axial relocation, pair/gauge arithmetic and generator arithmetic; report those limits.

### Metrics and deterministic views

summarize_errors accepts finite plain real ndarrays with shape `(O,P,Z,Y,X)` or `(P,Z,Y,X)`, all dimensions nonempty, and a nonempty plain dict of nonempty string arm names to same-shape arrays. Signed values are valid. Dtype kinds i/u/f are accepted and normalized to float64; no broadcasts, complex/bool/subclass/object data. Invalid inputs and nonfinite derived reductions raise ValueError. It returns each named arm as `{frames: [...], aggregate: {...}}`. Frames are orientation-major/phase-minor, with orientation index 0 for rank4. Every row contains `orientation`, `phase`, `count`, `error_l2`, `reference_l2`, `relative_l2`, `max_abs`, `mean_difference`, `rms_difference`. Aggregate contains the same numeric fields except indices, with sums/norms over all elements. Relative L2 is `sqrt(sum((pred-ref)^2))/sqrt(sum(ref^2))`; aggregate is the ratio of global norms, never a mean of frame ratios. All arms use the identical fine-reference denominator. If a reference norm is zero, relative_l2 is None even for zero error; absolute values remain reported. No fitted amplitude/intercept, favorable crop, registration or denominator floor. Report signed prediction-minus-reference differences.

fixed_center_views accepts a finite plain rank3 real array, positive finite spacing, finite origin and center triples (µm). Each axis's stored physical centers are `origin+(index+1/2)*spacing`; choose the nearest center to the predeclared catalogue center independently, first index on exact ties. Centers within the finite field including its faces are valid; outside centers reject ValueError. Return `indices_zyx`, `coordinates_um_zyx` (the selected stored plane centers), `xy_mip`=max over z, `xz_mip`=max over y, `xy_slice` at selected z and `xz_slice` at selected y. Views are independent owned writable float64 arrays, no normalization. Physical image-edge extents/aspect and common intensity/difference scales belong to the renderer and report. Signed differences use differences of corresponding shown products, not a max of signed differences mislabeled projection difference. No recovered-peak recentering.

## Scientific expectations and scenario inventory

Existing exact equations in simulation-optics-v1, simulation-inverse-operator-v1 and simulation-sources-v1 are approved expectation sources. Independent tiny finite sums, not legacy implementation or returned production values, supply expected results. The fine/paired full-field discrepancies have no required numerical success threshold beyond faithful computation/reporting. Derive numerical test budgets before observed outputs from the selected generator/inverse tolerances and finite reference quantities. Do not invent a continuum accuracy or resolution target.

| ID | Distinct obligation / credible wrong result |
|---|---|
| R01 | Fixed axial pair sum, gauge conversion, explicit float32 rounding and separate rounding ledger; no volume multiplier or hidden rescale |
| R02 | Fine archived reference retains every supplied exposure and exact known gauge; no regeneration/availability substitution claim |
| R03 | Matched paired generator64 and generator32 change only source rounding; independent expected finite sums |
| R04 | Paired inverse true matches its represented finite-map promise; matched physical-generator discrepancy labeled jointly |
| R05 | Same paired32 with estimated illumination, unchanged source/cache/geometry; no fit |
| R06 | Carrier-only q substitution in fixed calibration-origin gauge, associated kappa and origin recomputed once |
| R07 | Phase-only substitution leaves true q/beams and origin transfer based on true q |
| R08 | Beam-only keeps true q/phases and preserves ordered unequal side amplitudes |
| R09 | Frozen source/prediction retained; current original-fit reapplication distinctly labeled and compared |
| R10 | Per-exposure metrics and one common-denominator aggregate, unequal frame norm control and zero-denominator None |
| R11 | Metric domain/shape/type/reduction failures; signed legitimate inputs, dtype/layout positives and no mutation |
| R12 | Nearest half-cell planes, first tie, nonzero origin/anisotropy, four unnormalized independent views; bounds/errors |
| R13 | Independent displaced source above/below focus with unequal sides establishes source-minus-focus and half-cell signs |
| R14 | Separate physical-Q versus represented-kernel control and represented-kernel versus application control; no single joint discrepancy attribution |
| R15 | Three source refinements at same physical object/box with mass/shape/image changes; fixed pixel/Q refinement distinguished; no resolution inference |
| R16 | Evaluator grammar, preserved state/ownership/operation errors and valid zero source/one phase/zero carrier cases |
| R17 | Original input custody/hash/availability and exact reproducible arm manifest, immutable archives/fits/metrics |
| R18 | All15 frozen exposures plus global aggregate/representation ledger and fixed-center physical four-panel figures, claim limits |

R01–R16: A-owned blind public-entry tests/fixtures and independently justified controls. R17–R18: coordinator full-study evidence, with A fixture/protocol expectations and fresh D assessment; no large archive duplication in tests. Existing prerequisite suites retain their original proof. Source refinement reports at least three source refinements and pixel quadrature at least three counts with others held fixed in tiny controls; actual same-object convergence may be nonmonotonic. Kernel/application controls label their tested domain and cannot certify full-field independent separation. No additive causal shares/error floor from o0p0, convergence, resolution, physical instrument accuracy or C parity claim follows.

## Ownership, gate, boundaries and next step

A owns only tests/test_reference_alignment_ra03.py and tests/reference_alignment_ra03_fixture.py plus own artifacts. A may independently test existing public inverse/generator/source interfaces but changes no existing tests. Fresh B reviews exact tests/fixtures and sanitized evidence. C owns only scripts/reference_alignment_ra03.py; simulation_inverse_operator.py becomes owned only after a separately diagnosed approved-contract defect and coordinator correction packet. No tests/checks/dependency/workflow/policy edits by C. D independently checks exact candidate, all scientific oracles/controls/manifests/figures and resource/report limits. Roles launch as fresh native roots, gpt-6.1-sol/high; report-only Astra/ultra advisor supplements and replaces no role. Scope/role exposure and unavailable served attribution/cost stay explicit.

Inherit PROJECT's approved behavior/risk coverage with advisory percentages and complete native global/per-owned-package reports on Ubuntu24.04/macOS15; no selected percentage targets/exclusions or gate migration. Canonical exact-candidate `make verify UV=/Users/davidhoffman/.local/bin/uv` passes before PR or push. Focused checks include tests/test_simulation_inverse_operator.py, tests/test_simulation_optics_coordinates.py, tests/test_simulation_sources_cross_sections.py and new evaluator tests. No numeric owner limits set. Environment Python3.13.12,uv0.12.19 and worktree-owned .venv; Java21.0.7 reader pinned input. Preflight before roles. Source-free harness before blind imports/probes; use -s -p no:cacheprovider for read-only pytest. Runtime failures classify environment/test/product/requirement before correction, preserving every attempt.

Full-study plan/catalogue/settings/seeds frozen. Predeclare catalogue row0 center `(0.65,4.05,3.85)` µm and o0p0 for detailed four-panel figure; show all15 metrics without selection. Figure/report ownership coordinator, actual numerical figures and retained provenance, summary first then appendix. Original 38 copied archive members and native manifest/hash identities retained, never replaced by derived inputs. Task-only scratch/run inventories and preservation-aware cleanup are coordinator duties; protected predecessors/caches/environment/original referents remain. Actual destructive cleanup, if needed, follows its own high-risk route. Retain original evidence and close task writers before final inventory. Exact final hash/check/review/CI/cleanup results stay outside tracked bytes in artifacts/ra03/current-state.json, with prior RA02 state/accounting pointers. Create NEW RA04 only after complete RA03 readiness; do not wait for merge or create RA16.
