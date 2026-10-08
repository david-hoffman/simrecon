# Threshold-based finite integer-carrier selection

**Version 1.0. October 7, 2026.** The owner requested the next coherent roadmap implementation stacked on verified PR #12. This is a pure array convenience operation that applies explicit caller acceptance limits to the existing finite scan. Report-only Astra/ultra advice informed intake; it replaces no independent role. Robust physical-carrier identification/refinement remains future work.

## Public boundary

```python
from simrecon import CarrierSelection, select_carrier

selection = select_carrier(
    images, otf=calibration, phase_steps_rad=steps,
    candidate_carriers_bins_yx=[(0, 2), (1, 2), (-1, -2)],
    max_relative_residual=0.05, min_overlap_count=12,
    modulation_bounds=(0.1, 1.0),
)
```

Only images is positional. Every keyword is required; ordinary binding TypeError remains. Images, OTF, relative steps, candidate representation, complete candidate prevalidation, numerical equations/accuracy and errors inherit the [finite integer-carrier scan contract](carrier-scan-v1.md) and its referenced public numerical contracts unchanged. No file I/O, dependency, reconstruction change or legacy use. This new operation accepts scan inputs, not directly constructed candidate records; no new candidate-record validation interface is introduced.

Required policy inputs:

- max_relative_residual is a nonboolean Python or NumPy integer/floating scalar, finite before and after float64 conversion, with converted value >=0. No upper bound. Zero and negative zero are permitted. Reject complex, strings, arrays (including zero-dimensional), fractions/Decimal/custom numeric objects, and other types. Unrepresentably large integers and values that overflow conversion are invalid. A finite positive value that converts to zero is permitted, using converted zero.
- min_overlap_count is a nonboolean Python or NumPy integer >=1. Convert to Python int without float rounding or fixed-width wrapping. Arbitrarily large integers are permitted, even above every possible geometric count. Reject floats (including integral floats), arrays, strings and other types.
- modulation_bounds is a tuple/list of length two, or a plain one-dimensional ndarray of length two. Each entry obeys the same nonboolean integer/floating scalar and source/converted-finite rules as max_relative_residual. Require converted 0 <= lower <= upper. Equal bounds are permitted. There is no upper bound of one: a caller may deliberately accept diagnostic fits above one. Reject generators, sets, malformed shapes, ndarray subclasses, bool/complex/string entries and other invalid scalar entries. Integer/floating arrays of either endian, strided/read-only arrays, and object arrays holding actual permitted scalar entries are valid. Zero bounds and finite positive bounds that convert to zero are permitted, using converted zero.

Any rejected policy obligation raises SimreconError code invalid_carrier_selection_policy. Translate only expected conversion range/type errors for this validation; MemoryError or unrelated exceptions propagate unchanged. Policy validation completes before numerical scanning. Simultaneous-error precedence among policy fields or inherited invalid inputs is unspecified. Do not mutate any input on success or rejection. Comparisons use converted float64 scalar values and actual computed scan diagnostics, inclusively, with no hidden tolerance, rounding or positive cutoff. The limits are explicit caller policy, not calibrated noise thresholds.

## Selection and result

Perform the complete existing scan. For each caller-ordered row j, let E_j be its successful IlluminationEstimate if any. Eligibility is exactly:

```text
successful estimate exists
AND E_j.relative_residual <= max_relative_residual
AND E_j.overlap_count >= min_overlap_count
AND lower_modulation <= E_j.modulation <= upper_modulation
```

Failed scan rows are ineligible. Evaluate every row; an early acceptable row cannot hide a later local failure, acceptable row or whole-call failure. Do not rank candidates, minimize residual, apply a residual-gap rule, prefer a larger overlap, enforce physical modulation <=1, deduplicate, or stop scanning early. Caller order, signed/zero/huge carriers and duplicates remain exactly as supplied. Repeating an acceptable row creates multiple eligible rows and thus ambiguity, even when their represented carriers are identical. Ambiguity is a property of policy-passing rows, not a claim that multiple physical carriers exist.

Return a frozen-binding CarrierSelection with these fields:

- candidates: the complete nonempty Python tuple of CarrierCandidate records in caller order, preserving each full successful estimate or candidate-local failure. Arrays satisfy all scan ownership/precision guarantees and remain mutable; no output aliases caller storage or another candidate output, including duplicates.
- eligible_indices: an increasing Python tuple of Python int zero-based row indices satisfying all gates, including all duplicates.
- selected_index: the sole eligible Python int index if exactly one row is eligible; otherwise None.
- failure_code: None if exactly one row is eligible; no_acceptable_carrier if none; ambiguous_carrier if two or more.

No direct-construction validation is required for CarrierSelection. No winner record or separately copied estimate is required: callers use candidates[selected_index] after checking selected_index is not None. The two selection failure codes are result values, not thrown errors. An all-local-failure scan still returns a complete selection with empty eligible_indices and no_acceptable_carrier. Every other inherited scan error, numerical/range failure, MemoryError or unrelated exception aborts the whole operation and propagates unchanged, with no partial selection. Preserve caller NumPy error mode and warning behavior inherited from scan.

Threshold boundaries refer to actual computed diagnostics. Two independently executed fits need not be bitwise identical; a fixture at a mathematical limit must justify how floating-point uncertainty affects its expected decision. No promise applies to classification stability when changing inputs or limits by a roundoff-sized amount.

## Interpretation and limitations

This selects the unique row passing a caller policy. It does not establish the correct physical carrier, uniqueness over unexamined candidates, a noise-optimal estimator, confidence, or robustness. In particular, relative residuals on different overlaps compare different data; geometric overlap_count includes zero-transfer pairs and is not informative support. One informative complex pair can fit exactly, and weak/noisy/aliased/sparse/model-mismatched data may pass the policy. Omitted true carriers remain omitted. A restrictive policy can reject every row; a permissive policy can leave ambiguity. Keeping diagnostics lets the caller inspect those outcomes without an invented fallback winner.

Existing reconstruction still independently validates physical modulation and explicit carrier/brightness inputs. This helper performs no automatic reconstruction, continuous/fractional refinement, grid generation, independent phase-step estimation, drift, brightness estimation, 3D or adapter operation.

## Behavioral inventory and evidence

Each distinct positive, rejection, interpretation or propagation obligation is independently mapped by blind A; group IDs are headings, not a scenario cap.

| ID | Observable obligation / relevant high-risk path |
|---|---|
| S01 | Public exports, required keyword-only binding and frozen result structure |
| S02 | Residual-policy scalar representations, source/conversion finiteness/range, exact zero and inclusive gate |
| S03 | Arbitrary-precision positive integer overlap threshold, representation rejection and inclusive gate |
| S04 | Modulation-bound container/scalars, conversion/range/order/equality, above-one policy and inclusive gates |
| S05 | Complete policy validation before scan; stable invalid_carrier_selection_policy; preservation on rejection |
| S06 | Independently expected full complex scan and exact all-gates conjunction; each isolated rejection |
| S07 | Sole eligible row at any position; no acceptable row; multiple eligible rows; no ranking/tie preference |
| S08 | Duplicate rows, caller order/signs and complete retained local failures including all-failed scans |
| S09 | Inherited common-input/candidate validation even without success, whole-call failure after an earlier eligible row, unchanged error identity |
| S10 | Frozen bindings, independent mutable estimate arrays, source preservation and caller warning/error mode |
| S11 | Existing API/dependency/gate behavior retained; representative numerical/representation compatibility |
| S12 | Executed usage and actual independent comparison showing accepted, no-match, ambiguous/duplicate and misleading sparse landscapes |

High risk: numerical interpretation and custom oracle. Fresh native blind A/B, restricted C and fresh D apply. A owns only named new tests/fixtures; independent expected scans come from analytic/finite-sum or independently justified stored-input calculations, never product output as truth. Public scan compatibility comparisons may supplement, not replace, the oracle. Exact decision boundaries can use genuinely produced diagnostic values through a justified public operation, explicitly separated from numerical truth assertions. B independently audits legitimate positive classes, oracle applicability, boundary decisions and omissions. C owns only named runtime/usage/comparison outputs. D challenges actual behavior and evidence after exact canonical full local verification.

Inherit [approved project coverage policy](../PROJECT.md#coverage-policy-and-adoption-provenance): behavior/risk review and full native measurement/report integrity; native percentages advisory. No percentage-driven internal-state tests. The [NumPy Fourier reference](https://numpy.org/doc/stable/reference/routines.fft.html), opened October 7, 2026, supports inherited DFT signs/order/normalization. Selection gates, representation/error/result semantics and limits above are explicit project choices.
