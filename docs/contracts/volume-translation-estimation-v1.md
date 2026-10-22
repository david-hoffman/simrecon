# Known-reference periodic integer-voxel volume translation v1

**Version 1.0. October 18, 2026.** Contract ID: VOLUME-REFERENCE-TRANSLATION. The owner's standing roadmap continuation authorizes this dependency-ready Phase 5 comparable-reference drift foundation above completed PR44. It extends the settled [2D translation objective](translation-estimation-v1.md) to z/y/x volumes through an additive operation. It does not establish comparable references from different raw structured illumination microscopy (SIM) phase exposures.

## Public boundary and representation

```python
from simrecon import VolumeTranslationEstimate, estimate_volume_translation

result = estimate_volume_translation(
    moving, reference=reference, ambiguity_tolerance=0.001
)
```

Only moving is positional. Both keywords are required; ordinary binding TypeError remains. moving and reference are plain NumPy ndarrays with equal nonempty three-dimensional shape (Nz,Ny,Nx). Each dtype is real signed/unsigned integer or real floating, including extended precision, either endian, strided/Fortran/read-only views and signed values. Reject bool, complex, object/string/structured/datetime arrays, ndarray subclasses/masked arrays, lists and other nonarrays. Source values and converted float64 values must be finite. Float64 conversion overflow is invalid; finite conversion underflow to zero and rounding are permitted. Converted values define the estimator. Singleton axes and (1,1,1) are valid. There is no artificial size cap. Snapshot converted inputs before numerical processing; preserve all caller storage on success and failure. Concurrent external mutation is outside the promise.

Rejected image type/dtype/rank/empty/source-or-converted finiteness raises SimreconError code invalid_volume_translation_images. Unequal otherwise-valid shapes raise incompatible_volume_translation_shape. Simultaneous-error precedence and message prose are unspecified.

ambiguity_tolerance is a nonboolean Python/NumPy integer or floating scalar, or plain zero-dimensional ndarray with such a real integer/floating dtype. Reject other arrays/subclasses, containers, complex/bool/object and other values. Source and converted float64 must be finite and nonnegative. Finite positive source values converting to zero are permitted; negative source values converting to negative zero are invalid. Zero, negative zero and values >=2 are permitted. Finite source values overflowing float64 are invalid. Rejections raise invalid_volume_translation_tolerance. Complete this validation before numerical evaluation; precedence against invalid images is unspecified. Catch only expected conversion TypeError/ValueError/OverflowError as validation errors. Allocation MemoryError and unrelated exceptions propagate unchanged.

## Objective, coordinates and numerical meaning

Let P=Nz*Ny*Nx. R and M are the converted reference and moving arrays, and B=max(max(abs(R)),max(abs(M))). Coordinates have index-zero origin. Displacement is content motion in integer voxels, ordered z/y/x; no physical spacing or isotropic-voxel assumption is needed. Canonical signed candidates on each axis of length D are -floor(D/2),...,ceil(D/2)-1, with the negative representative for an even half-period. Evaluate the full Cartesian grid in increasing z, then y, then x order. Every candidate uses every voxel and periodic indexing:

```text
S(dz,dy,dx) = sqrt((1/P) * sum_z,y,x [
  M((z+dz) mod Nz,(y+dy) mod Ny,(x+dx) mod Nx)/B - R(z,y,x)/B
]**2)
```

The square applies to each bracketed voxel difference before summation. For B=0 every score is zero. S is dimensionless normalized root mean square (RMS) mismatch, in [0,2] in exact arithmetic. Common nonzero scaling preserves the exact objective only when the stored ratios are preserved; rounding/underflow may change them. Do not independently normalize volumes, subtract means, fit gain/background, phase-normalize Fourier coefficients, mask/window voxels, crop, pad or change overlap.

If moving(z,y,x)=reference((z-dz) mod Nz,(y-dy) mod Ny,(x-dx) mod Nx), displacement is (dz,dy,dx) up to canonical period equivalence. Alignment rolls moving by (-dz,-dy,-dx). The actual objective also applies to arbitrary/off-model inputs. Its unique optimum is no proof of physical specimen, focus or camera motion.

Use float64 arithmetic and stable common-scaled voxel differences. Avoid raw subtraction/squaring overflow and near-zero energy-minus-correlation cancellation. An equivalent accelerated method is permitted. Every returned score must have absolute error <=delta=4096*P*2**-52 against the stated stored-input real-arithmetic objective. This inherited conservative project allowance is not a backend theorem or a physical accuracy threshold. Derive stronger analytic assertions where justified. There is no classification stability promise within numerical error of a score/tolerance boundary. Independently expected winners require a distinguishing margin; boundary classification uses the actual same-call scores.

Preserve caller NumPy error mode. Handled conversion/arithmetic emits no RuntimeWarning; do not suppress unrelated categories. Unrelated numerical/programming exceptions and MemoryError propagate unchanged, with no partial result. No backend-specific solver, private seam or speculative injected-failure translation is required. Valid finite arrays have bounded scores; no intensity rejection threshold is authorized.

## Result and ambiguity

Return a fresh frozen-binding VolumeTranslationEstimate with exactly these public fields. Direct construction requires no validation.

| Field | Type and meaning |
|---|---|
| normalized_rms | Independently owned mutable native float64 C-contiguous ndarray of shape (Nz,Ny,Nx), ordered on the canonical signed grid; aliases neither inputs nor another call |
| minimum_normalized_rms | Python float equal to the actual minimum entry of normalized_rms |
| candidate_displacements_voxels_zyx | Nonempty Python tuple of Python-int triples in increasing canonical z/y/x order, containing exactly scores whose actual float64 score minus actual minimum is <=converted ambiguity_tolerance |
| displacement_voxels_zyx | Sole candidate triple when exactly one qualifies, otherwise None |
| failure_code | None for a sole candidate; otherwise ambiguous_volume_translation |

Ambiguity is a result value, not an exception. Do not prefer the first minimum or a smaller displacement, impose a hidden tolerance or deduplicate different canonical candidates. Tolerance zero admits exact computed ties. Larger tolerance admits near ties; >=2 can admit every shift. A (1,1,1) volume always has one candidate, including zero or mismatched constant inputs; no hidden information rejection. Constant/repeated volumes may be ambiguous. A sole candidate establishes only uniqueness under this finite objective and caller tolerance, not fit acceptance, noise calibration, confidence, physical accuracy or motion bounds.

## Evidence, compatibility and limits

The existing estimate_translation/TranslationEstimate and every other public operation retain their behavior. This pure array operation adds no file I/O, command-line interface, dependency, automatic correction or automatic raw-workflow integration. It is a correctness-first operation for modest volumes or regions of interest. Direct full-surface evaluation costs O(P**2) work; no full-frame or 512x512x64 feasibility claim is selected. Fractional/nonperiodic motion, illumination-phase correction, rescaling/bleaching, comparable-reference construction, specimen/focus/camera interpretation and axial-order-profile motion remain separate contracts.

A derives independent finite sums/analytic fixtures from this public model, with tight justified tolerances and permitted-positive counterexamples. B audits legitimate alternatives, omissions, units, signs, boundaries and oracle validity. Initially passing existing behavior is valid; no manufactured red is required. C records two independently generated observation groups: a nonnegative asymmetric 3D comparable-reference group with known evaluator-only shifts across all axes, and ambiguity/off-model controls including changed intensity or structure. The reference is a legitimate estimator input; hidden shift truth is evaluator-only. Retain producer/input/output bytes, exact generation argv/status/timestamps, environment and original candidate/dirty identity. Report full score-surface agreement separately from displacement truth, and computed uniqueness separately from physical meaning. Execute the usage example and retain its actual output. Changed material inputs require affected regeneration; later clean admission never rewrites original generation context.

## Behavioral inventory

These are distinct decisions/boundaries, not a test/example cap. A maps each obligation to meaningful public tests and explains any smaller test's gap beyond stronger boundary proof.

| ID | Observable obligation / credible wrong outcome |
|---|---|
| V01 | Additive exports and required positional/keyword binding |
| V02 | Frozen result, exact field types and independently owned mutable native score array |
| V03 | All permitted real dtype/endian/layout/read-only/signed input representations |
| V04 | Image nonarray/subclass/dtype/rank/empty rejection |
| V05 | Source/conversion finiteness and overflow rejection versus permitted rounding/underflow |
| V06 | Equal shape requirement; singleton/odd/even axis acceptance |
| V07 | Tolerance permitted scalar/zero-dimensional grammar |
| V08 | Tolerance invalid grammar, source negativity, nonfiniteness and conversion overflow |
| V09 | Zero/negative-zero/large/tiny-positive tolerance acceptance and validation before evaluation |
| V10 | Full all-voxel periodic score surface with one common intensity scale |
| V11 | z/y/x content-motion sign and negative-roll alignment on all axes |
| V12 | Canonical signed grid, even half-period and complete ordered candidate triples |
| V13 | Actual minimum, inclusive same-call subtraction rule, sole/ambiguous outcomes and no tie preference |
| V14 | Zero/constant/repeated-pattern inputs and singleton sole-candidate behavior |
| V15 | Off-model/gain/background differences retained without hidden fitted nuisance quantities |
| V16 | Stable huge/subnormal/mixed scales and near-perfect alignment within the numerical allowance |
| V17 | Input preservation on success/failure, output nonaliasing across calls and snapshots |
| V18 | NumPy error mode, RuntimeWarning/category policy and unchanged unrelated/MemoryError propagation |
| V19 | Existing 2D and other interfaces, dependencies, checks and gates preserved |
| V20 | Two actual independent observation groups, executed usage, signed comparison and generation/input custody |

## Ownership and gates

Scientific/custom-oracle work is high risk: fresh native Sol/high A, fresh blind B, restricted fresh C and fresh independent D. Requested settings are not serving attribution. A owns tests/test_volume_translation_estimation.py and optional tests/volume_translation_estimation_fixture.py plus ignored independent public evidence. Existing tests/fixtures stay unchanged. C owns src/simrecon/_volume_translation_estimation.py, additive exports in src/simrecon/__init__.py, narrowly shared internals in src/simrecon/_translation.py if necessary to reuse validation/scoring while preserving the complete existing 2D contract, docs/usage/volume-translation-estimation.md and ignored actual example producers/evidence. Reviewed/existing tests/fixtures, unrelated runtime, dependencies/lock, workflows/discovery/coverage, policy/skills and gate helpers are outside C ownership. B/D report only. Coordinator owns contract/task/PROJECT/roadmap/report/presentation and unique lessons. Separately named bounded setup ownership and fresh independent acceptance precede changed harness use.

Inherit binding100%Coverage.py native executable-line/branch-destination targets globally/perpackage/perownedfile across all src/simrecon+scripts, never-imported/relevant subprocesses, zero exclusions/skips, separately local/Ubuntu24.04/macOS15, no union. Advisory project defaults grant no waiver. Exact clean canonical make verify/all13phases with complete SQLite/JSON/HTML, same-run M25 and wheel/source/staticversion/lock/check/base/environment/executable/ignored-input proof precedes fresh D and own PR stacked on PR44. Closed successful native CI and independently qualified original platform archives precede final readback and exactly one useful started successor. Human numeric limits are not set. Preserve all historical/current attempts and unknown meters. No reference C execution/build, merge/release, previous-PR edits, unrelated messaging or Superpowers.
