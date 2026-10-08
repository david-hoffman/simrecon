# Known-reference periodic integer-pixel translation

**Version 1.0. October 7, 2026.** The owner authorized the next coherent unmet roadmap implementation stacked on verified PR #13. This first drift slice estimates translation against an explicit reference under a finite periodic, equal-intensity model. Astra/ultra report-only advice informed scope and replaces no required acceptance role.

## Public boundary and representation

```python
from simrecon import TranslationEstimate, estimate_translation
result = estimate_translation(moving, reference=reference, ambiguity_tolerance=0.001)
```

Only moving is positional. Both keywords are required; ordinary binding TypeError remains. Inputs moving and reference are plain NumPy ndarrays with equal nonempty two-dimensional shape (Ny,Nx). Each dtype is real signed/unsigned integer or real floating, including extended precision, either endian, strided/Fortran/read-only views and signed values. Reject bool, complex, object/string/structured/datetime arrays, ndarray subclasses/masked arrays, lists and other nonarrays. Source values and converted float64 values must be finite. Float64 conversion overflow is invalid; finite conversion underflow to zero and rounding are permitted, with the converted values defining the estimator. Singleton axes and (1,1) are valid. No artificial size cap. Preserve all caller storage on success and failure; snapshot converted input before numerical processing. No promise covers concurrent external mutation.

Rejected image type/dtype/rank/empty/source-or-converted finiteness raises SimreconError code invalid_translation_images. Unequal otherwise-valid shapes raise incompatible_translation_shape. Simultaneous-error precedence and message prose are unspecified.

ambiguity_tolerance is a nonboolean Python/NumPy integer or floating scalar, or plain zero-dimensional ndarray with such a real integer/floating dtype. Reject other arrays/subclasses, containers, complex/bool/object and other values. Source and converted float64 must be finite and nonnegative; finite positive values converting to zero are permitted. Zero, negative zero and values >=2 are permitted. Reject negative source values even if conversion gives negative zero, or finite source values overflowing float64. Rejections raise invalid_translation_tolerance. This validation completes before numerical evaluation; precedence against invalid images is unspecified. Catch only expected conversion TypeError/ValueError/OverflowError as validation errors; allocation MemoryError and unrelated exceptions propagate unchanged.

## Fixed objective and conventions

Let P=Ny*Nx and R,M be the converted reference/moving arrays. B=max(max(abs(R)),max(abs(M))). Coordinates use pixel indices with index-zero origin; displacement is y/x in integer pixels. Canonical signed candidate coordinates on each length L axis are -floor(L/2),...,ceil(L/2)-1. Even half-period uses the negative representative. Evaluate the full Cartesian grid in increasing y then x order. Every candidate uses every pixel and periodic indexing, with no crop, padding, masking, interpolation or changing overlap:

```text
S(dy,dx) = sqrt((1/P) * sum_y,x
  [M((y+dy) mod Ny,(x+dx) mod Nx)/B - R(y,x)/B]^2)
```

For B=0 every score is zero. S is dimensionless normalized root mean square (RMS) mismatch, in [0,2] in exact arithmetic. Common nonzero scaling of both represented inputs preserves the exact objective; no uniform invariance is promised when that scaling changes stored ratios through rounding/underflow. Do not independently normalize images, subtract means, fit brightness/offset, phase-normalize Fourier coefficients or weight/window pixels.

For moving(y,x)=reference((y-dy) mod Ny,(x-dx) mod Nx), the displacement is (dy,dx), up to canonical period equivalence. To align moving, roll it by (-dy,-dx). Displacement is content motion, not the correction sign. The actual objective applies to arbitrary/off-model arrays too; a returned displacement is not proof of physical motion.

Use float64 arithmetic with a stable evaluation of pixel differences after common scaling. Avoid raw subtract/square overflow and near-zero energy-minus-correlation cancellation. An equivalent accelerated method is permitted if it meets this contract. For every returned score, absolute error against the stated stored-input real-arithmetic objective must be <= delta=4096*P*2^-52. This conservative project acceptance budget is not a backend theorem. Derive stronger analytic assertions where justified. No classification stability promise applies when score differences or tolerance boundaries are within numerical error. Tests of independently expected winners require a distinguishing margin; numerical boundary decisions are defined by same-call returned values.

Preserve caller NumPy error mode. Handled conversion/arithmetic must emit no RuntimeWarning. Do not suppress unrelated warning categories. Unrelated numerical/programming exceptions and MemoryError propagate unchanged; no partial result. No backend-specific solver or speculative injected-failure translation is required. The bounded scaled objective has representable scores for valid arrays; do not invent an intensity rejection threshold.

## Result and ambiguity

Return frozen-binding TranslationEstimate with fields:

- normalized_rms: independently owned mutable native float64 C-contiguous ndarray of shape (Ny,Nx), ordered on the canonical signed grid above. It aliases no caller storage or another call's output.
- minimum_normalized_rms: Python float equal to the actual minimum entry of normalized_rms.
- candidate_displacements_pixels_yx: nonempty Python tuple of Python-int pairs in increasing canonical row-major order whose actual float64 score minus the actual minimum is <= converted ambiguity_tolerance. This inclusive subtraction rule uses no hidden rounding/tolerance or deduplication.
- displacement_pixels_yx: the sole candidate tuple if exactly one qualifies, otherwise None.
- failure_code: None for a sole qualifying candidate, otherwise ambiguous_translation. Ambiguity is a result value, not an exception.

No direct-construction validation is required. Do not pick the first minimum or prefer a smaller displacement. Tolerance zero permits exact computed ties; larger tolerance admits near ties and >=2 may admit every shift. Singleton (1,1) has one candidate even for zero or mismatched constant images; no invented information rejection. Repeated patterns/constant inputs may yield ambiguity; approximate ties depend on actual numerical scores. A sole candidate only establishes uniqueness under this finite objective and caller tolerance, not mathematical/physical identification, a calibrated noise threshold, fit acceptance, accuracy confidence or motion bounds.

## Scope, evidence and scenario inventory

This pure array operation adds no file I/O, dependency, automatic reconstruction or changes to existing APIs. It is a correctness-first operation for modest arrays/regions of interest. A direct full surface costs O(P squared) work; no full-frame speed or memory benchmark is promised. Fractional shifts, nonperiodic borders, gain/background estimation, masks, changing specimens, illumination-phase drift, 3D, carrier refinement and automatic image correction remain future contracts. Different raw SIM phases/orientations need not depict translated equal-intensity references; do not apply this operation to them without satisfying its model.

| ID | Observable obligation and relevant risk |
|---|---|
| T01 | Public exports, required binding, frozen result fields/native output precision |
| T02 | Permitted real image representations, copying, conversion rounding/underflow; type/dtype/rank/empty/nonfinite rejection |
| T03 | Matching shape and singleton/odd/even canonical grids |
| T04 | Required tolerance scalar representations, zero/large/tiny positives, source/conversion range rejection |
| T05 | Independent fixed all-pixel periodic RMS oracle, common normalization, signs and even half-period |
| T06 | Full surface/minimum, inclusive same-call tolerance, ordered all-candidate set, sole result/ambiguity and no fallback |
| T07 | Constant/zero/repeated patterns, arbitrary off-model data, no hidden fit/brightness/information rule |
| T08 | Stable maximum/subnormal/mixed safe scales and near-perfect alignment; absolute budget and distinguishing margins |
| T09 | Input/output ownership, failure preservation, NumPy error mode/warnings and unchanged unrelated/MemoryError propagation |
| T10 | Existing APIs/dependencies/gates preserved; executed usage and actual independent comparison with known shifts, ambiguity and off-model limits |

Every distinct guarantee/rejection/outcome is independently mapped by blind A; these headings impose no scenario cap. High-risk numerical/custom-oracle route: fresh native blind A/B, restricted C and fresh D. A derives finite-sum/analytic stored-input oracles without product output; B independently audits legitimate alternatives, positive inputs, numerical margins and omissions. D assesses actual implementation/risks and evidence after exact full local verification. Inherit PROJECT's approved behavior/risk and complete native report-integrity policy: statement/branch percentages advisory, no selected numerical threshold, no exclusions or percentage-driven tests. The exact clean canonical make verify remains binding before publication, with all configured push/PR Ubuntu24.04/macOS15 jobs thereafter.

[NumPy roll documentation](https://numpy.org/doc/stable/reference/generated/numpy.roll.html), opened October 7, 2026, documents periodic array shifting. The estimator, units, canonical grid, explicit tolerance, budget and result/error policy above are project choices, not a cited physical-identification guarantee.
