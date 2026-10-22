# Caller-policy selection of volume carrier rows v1

**Version 1.0. October 16, 2026.** The standing owner roadmap continuation authorizes this dependency-ready Phase 5 convenience operation above accepted PR37. It applies explicit caller policy to the complete known-actual-phase volume scan. It selects no noise model or physical identifiability criterion.

## Public boundary

```python
from simrecon import VolumeCarrierSelection, select_volume_carrier

selection = select_volume_carrier(
    images,
    response=response,
    voxel_size_um=(dz, dy, dx),
    phase_steps_rad=actual_steps,
    candidate_carriers_yx=[(0, 2), (1, 2), (-1, -2)],
    order=1,
    calibration_carrier_bins=(ky_c, kx_c),
    coordinate_offset_yx=(oy, ox),
    phase_reference_shift_rad=delta,
    source="declared calibration/specimen pairing",
    max_relative_residual=0.05,
    min_overlap_count=12,
    gain_magnitude_bounds=(0.1, 3.0),
)
```

Only images is positional. All twelve keywords are required; ordinary argument-binding TypeError applies. The nine scan arguments inherit the [volume carrier diagnostics contract](volume-carrier-diagnostics-v1.md) unchanged: phase/z/y/x observations, z/y/x spacing in micrometres, known actual phases in radians, one positive order 1 or 2, fixed empirical response/calibration gauge, exact integer caller candidates, complete nonwrapping pairing, physical-frequency sampling, numerical rules, snapshots, six statuses and global failures. Gains, residuals and policy bounds are dimensionless. No file I/O, dependency, reconstruction change or reference-program use is introduced.

This operation accepts scan inputs, not caller-constructed rows. It exposes no new row-validation interface. Existing APIs remain compatible.

## Required caller policy and validation

- max_relative_residual is a nonboolean Python or NumPy integer/floating scalar, finite in its source representation and after binary64 conversion, with converted value >=0. There is no upper bound. Positive and negative zero are valid. Finite positive values that convert to zero are valid and use converted zero. Reject complex, string, array (including zero-dimensional), Fraction, Decimal and other non-integer/non-floating objects. Unrepresentably large integers and conversion overflow are invalid.
- min_overlap_count is a nonboolean Python or NumPy integer >=1. Extract its exact Python integer value without floating rounding or fixed-width wrapping. Arbitrarily large integers are valid, even above every possible geometric overlap. Reject floats (including integral floats), arrays, strings and other types.
- gain_magnitude_bounds is an exact built-in tuple/list of length two, or a plain one-dimensional ndarray of length two. Each entry obeys the residual scalar representation/source-finite/conversion-finite rules. Require converted 0 <= lower <= upper; equal bounds are valid. There is no upper bound of one and no physical modulation interpretation. Zero and positive values converting to zero are valid. Reject other iterables, malformed shapes, ndarray subclasses and invalid scalar entries. Either-endian integer/floating arrays, strided/read-only arrays and object arrays containing actual permitted scalar entries are valid.

Rejected policy raises SimreconError code invalid_volume_carrier_selection_policy. Translate only expected TypeError, ValueError and OverflowError at the named policy extraction/conversion boundaries. MemoryError and unrelated exceptions propagate unchanged. Validate all three policy fields before numerical scanning; no precedence among simultaneous invalid fields or inherited invalid inputs is specified. Preserve all caller inputs and NumPy/warning policy on success and rejection. Policy limits are caller decisions, not calibrated confidence or noise thresholds.

## Eligibility, magnitude comparison and result

Perform the complete inherited scan. For each returned row j, eligibility is exactly:

```text
gain is not None
AND relative_residual <= converted max_relative_residual
AND overlap_count >= exact min_overlap_count
AND converted lower <= Euclidean magnitude of gain <= converted upper
```

All comparisons are inclusive with no tolerance, clipping, hidden energy cutoff or rounding of diagnostic fields. The gain gate compares the exact real Euclidean magnitude of the returned gain's represented binary64 real/imaginary components against the converted binary64 limits. Equivalently compare lower**2 <= real**2 + imag**2 <= upper**2 in exact real arithmetic. Intermediate overflow/underflow must not change this decision or reject an otherwise valid scan. A magnitude larger than the largest finite binary64 value simply exceeds every allowed upper bound. No square root result needs to be representable. This comparison is a project policy choice on already computed diagnostics, not an extra numerical-accuracy guarantee for the fit.

Rows with no_overlap, incomplete_coverage or zero_predictor have absent gains and are ineligible. zero_response and zero_correlation have actual zero-valued gain/diagnostics under their inherited conventions and are eligible exactly when all gates pass. A fitted gain that underflowed to zero remains fitted and follows the same rule. Do not require a nonzero gain, coherence threshold, fitted-only status or gain <=1.

Evaluate every candidate. An earlier passing row cannot hide a later local outcome, passing row or global failure. Do not rank, minimize residual, prefer overlap/coherence, infer a search range, reduce periodic aliases, deduplicate or stop early. Caller order, signs, zero/huge carriers and duplicates retain their inherited meaning. Duplicate eligible rows produce ambiguity even when their carrier pairs and diagnostics are equal.

Return a frozen-binding VolumeCarrierSelection with exactly four fields:

- candidates: the complete nonempty built-in tuple of VolumeCarrierCandidate records in caller order, retaining every field and local outcome. Distinct rows remain distinct record instances, including duplicates, with inherited ownership guarantees.
- eligible_indices: increasing built-in tuple of Python int zero-based indices satisfying every gate.
- selected_index: sole eligible Python int index when exactly one is eligible; otherwise None.
- failure_code: None for exactly one eligible row; no_acceptable_volume_carrier for none; ambiguous_volume_carrier for two or more.

Field rebinding/deletion fails. Direct result construction needs no validation/deep immutability. There is no extra winner copy: after checking selected_index, use candidates[selected_index]. Selection failure codes are result values, not thrown errors. An all-unavailable scan returns all rows with empty eligible_indices and no_acceptable_volume_carrier. Every inherited invalid input, phase/numerical/FFT/sampler failure and unrelated exception aborts the entire operation and propagates unchanged; return no partial selection.

## Interpretation, evidence and limits

Thresholds apply to actual returned diagnostics. Fits on different overlaps compare different data. overlap_count includes zero-transfer pairs and measures geometry, not informative support. A single informative complex pair can fit exactly; sparse/periodic/aliased/off-model observations can pass a permissive policy. Small residual and sole acceptance do not establish a physical carrier, uniqueness beyond the finite list, a confidence probability or robustness. Fixed calibration/gauge and known actual phases remain required. Changing inputs by roundoff can change the returned gain and therefore a boundary decision; no classification-stability promise is made. Exact magnitude comparison removes additional comparison ambiguity, not uncertainty in those inputs or fits.

No independent phase-step/carrier/gain/drift inference, continuous refinement, observation interpolation, automatic correction/reconstruction or complete raw workflow is added. The remaining roadmap exits, separately contracted full approximately 512 x 512 x 64 simulation through the public raw workflow, and owner-data/reference parity remain unmet.

Required executed usage and an actual independently calculated comparison must show sole acceptance, no match, ambiguity including duplicates, unavailable rows, gains above one and a misleading sparse landscape. Record observed versus independent diagnostic error separately from policy correctness and physical truth. Do not rerun measurement-only scientific examples to retrieve missing reporting numbers.

| Group | Observable obligation / high-risk path |
|---|---|
| VS01 | Required public binding, exports, exact four-field frozen result and scalar/index types |
| VS02 | Residual scalar grammar, source/conversion finiteness/range, zeros and inclusive decision |
| VS03 | Exact arbitrary-precision positive-integer overlap policy and rejection boundaries |
| VS04 | Gain-bound container/scalar grammar, finite conversion, order/equality/zero and above-one acceptance |
| VS05 | Complete policy validation before scan, stable error, preservation and exception boundaries |
| VS06 | Exact represented-component magnitude gate, inclusive boundaries and finite extreme/subnormal comparisons |
| VS07 | Full real scan composition and all-gates conjunction; each gate can exclude a row |
| VS08 | Sole passing row anywhere, no passing rows, multiple passing rows, no ranking or deduplication |
| VS09 | All six inherited row statuses, zero-valued fits, complete retained rows/source/order/caller order/duplicates |
| VS10 | Global scan failures after earlier eligible rows, inherited validation even for unavailable scans, unchanged exception identity |
| VS11 | Snapshots, source preservation, floating/warning policy, compatibility and no new mutable aliasing |
| VS12 | Executed usage, independent comparison, sparse/alias limits and actual phase/calibration requirements |

These groups are not scenario totals or a cap. Blind A maps each distinct decision/rejection/interpretation/guarantee/boundary and distinguishes equivalent examples. High-risk fresh native A/B, restricted C and fresh D apply. Independent analytic/finite-sum truth supports numerical claims. Conditional policy checks may use genuine returned diagnostics as observations; that proves the selection relation only and does not replace independent numerical truth. Real production/public-library failure boundaries may be exercised; no test-only production seam is authorized.

Inherit the standing task-selected 100% native Coverage.py executable statements/branch destinations globally/per-package/per-file, all owned src/simrecon and scripts including never-imported files/relevant subprocesses, separately local/Ubuntu 24.04/macOS 15, zero exclusions/no platform union. Behavior coverage and independent risk review always apply. Installed advisory percentages do not waive this selected target. The mathematical policy and representation/error/result meanings above are explicit project choices; the inherited contracts supply numerical expectations.
