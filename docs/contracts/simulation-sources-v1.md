# Pure finite-sphere source catalogue v1

**Version 1.0, October 22, 2026.** The coordinator adopts this concrete numerical contract under the owner's full noisy simulation request. This narrow prerequisite belongs to the already authorized full noisy simulation. It constructs a deterministic finite source model; it does not implement optical expectations, camera noise, calibration, reconstruction, persistence or an exact sphere–cell intersection integrator. It can be developed independently of optics and camera implementation baselines. The coordinator selects and records scene constants separately.

## Public boundary

The in-repository module `scripts/simulation_sources.py` exposes:

```python
make_sources(
    catalogue,
    *,
    detector_shape_zyx,
    detector_spacing_um_zyx,
    source_refinement_zyx,
) -> numpy.ndarray
```

All arguments are explicit and required. Coordinates, radii and spacing use micrometres (µm). Brightness is integrated electrons per object per exposure before structured illumination. It is a source weight, not a sampled density. No source-cell-volume or focus-spacing multiplier is applied.

The catalogue is a plain NumPy ndarray of shape `(M,5)`, `M>=0`. Columns are center z, center y, center x, radius and total brightness B. Each row denotes one sphere. Overlapping spheres contribute additively; no union, occlusion or replacement operation is implied. Catalogue order is meaningful for the prescribed floating-point accumulation.

## Normalized input domain

Catalogue dtype kind is `i`, `u` or `f`. Original values and values normalized to native float64 must be finite. Numeric conversion may round. Plain integer and real floating arrays, either endian, strided/reversed layouts, Fortran order and read-only storage are permitted. Boolean, complex, object and other dtype kinds, lists, ndarray subclasses and masked arrays are rejected. Empty `(0,5)` is valid; other ranks/column counts are invalid. Normalized values supply the exact real geometric and brightness inputs below.

Each normalized radius is strictly positive. Each normalized B is nonnegative; signed zero is valid. Centers may have either sign before the containment check. Every row must satisfy the radius, brightness and containment domains, including zero-brightness rows.

`detector_shape_zyx` and `source_refinement_zyx` are three-element tuples of plain built-in positive ints. Bool, integer subclasses, NumPy integers, floats, lists and nonpositive values are excluded. No arbitrary maximum is selected. Let their components be N and f; the returned source shape is S=N*f componentwise, using exact integer products.

`detector_spacing_um_zyx` is a three-element tuple of plain built-in int/float values, excluding bool and numeric subclasses. Each must normalize to a finite strictly positive float64 value D. Integers whose float conversion overflows are invalid. There are no implicit defaults or array broadcasting rules.

The finite box has corner `(0,0,0)` µm and side lengths L=N*D. Each sphere must be wholly contained: for every axis, `0 <= center-radius` and `center+radius <= L`, interpreted as exact real inequalities of normalized inputs and exact N. Tangency to a box face is permitted. A partly or wholly exterior sphere is invalid; it is not clipped, wrapped or renormalized onto the box.

## Finite source model and prescribed arithmetic

For source index j, the exact site coordinate is

`r[j]=(j+1/2)*D/f`, componentwise.

For catalogue row b with center c_b and radius a_b, its occupied-site set is

`J_b = {j : sum_axis((r[j,axis]-c_b[axis])**2) <= a_b**2}`.

This is a Euclidean sphere. Membership is closed, including exact ties. The equation uses exact real interpretations of normalized floats and the declared integer indices/refinements. Rounded centers, rounded squared distances, bounding boxes, componentwise distances or a tolerance-expanded sphere do not redefine membership. Faithful exact, higher-precision or otherwise justified implementations are permitted; this contract mandates no private algorithm or backend.

Initialize the output to positive float64 zero. Visit catalogue rows in the supplied order. A row with B=0 contributes zero and requires no occupied-site evaluation. For each row with B>0, let K be the exact integer size of J_b:

1. K=0 is a range failure: this finite midpoint model cannot place that positive object on the requested source grid.
2. Otherwise compute `w_b=RN64(B_b/K)`, one correctly rounded float64 value with round-to-nearest, ties-to-even. If w_b=0, report a range failure. Nonzero finite subnormal weights are permitted.
3. At each site in J_b, replace its current value v by `RN64(v+w_b)`, in catalogue order, with a separate float64 addition for that row. Reject nonfinite addition results. Different sites have no prescribed traversal order because they do not depend on one another.

Do not replace this left-fold rule by a single final rounding of the exact combined brightness, or by a different catalogue order. The output is deterministic for normalized inputs under these rules. Repeated rows add normally. Positive increments that round away during an otherwise finite addition are permitted outcomes of the declared arithmetic.

This is a total-normalized midpoint membership model. It is not exact integration of a continuous uniform sphere over source cells. B/K may not be representable, and subsequent overlap additions also round. Exact conservation of B, or of the sum of all catalogue brightnesses, is therefore not promised.

The generation report must identify this model and report the actual stored-array mass discrepancy relative to the exact sum of normalized B values, using a sum method that does not mistake ordinary reduction error/overflow for model error. Per-object raw occupied-volume discrepancy `K*product(D/f)/((4*pi/3)*a**3) - 1` is useful approximation evidence. This reporting duty does not change the array-only return type or add a persistence interface.

## Ownership, errors and process state

Return one complete independently owned, writable, C-contiguous, native float64 plain ndarray of shape S, containing finite nonnegative weights. It must not alias caller storage. Inputs remain unchanged on success or rejection. An empty catalogue or a catalogue containing only valid zero-brightness rows returns exact zeros of the declared shape. Ordinary missing/unknown argument binding remains Python TypeError. Invalid-input precedence and exact diagnostic prose are unspecified.

Use public `SimreconError` codes:

| Outcome | Code |
|---|---|
| Invalid catalogue/type/shape/dtype, original or normalized nonfinite value, coefficient/count domain, radius/brightness domain, or sphere containment | `invalid_simulation_source` |
| Positive object has no occupied site, positive B/K rounds to zero, or an overlap addition becomes nonfinite | `simulation_source_range` |
| Requested ndarray shape or required storage size cannot be represented by the platform's NumPy array/addressing representation | `simulation_source_range` |

No arbitrary radius, extent, brightness, shape, refinement or catalogue-count cap is selected. A large value alone is not a range obstruction. For finite normalized geometric values, exact site coordinates, containment and squared-distance comparisons are rationally definable even when intermediate float64 products would overflow, underflow or lose a boundary distinction. Float64 intermediate failure by itself is not proof that the promised geometry is unrepresentable. Use a faithful alternative when required; ordinary unimplemented work or unavailable time does not authorize a range refusal. No general-purpose exact geometry engine or sphere–cell integration follows from this requirement.

A concrete inability to represent the requested ndarray is distinct from actual allocation failure. Actual MemoryError propagates unchanged. Do not broadly translate unrelated ValueError, exceptions or numerical-dependency failures into a domain/range result. No successful partial array is returned. Diagnostic messages should identify the obstructed operation; their exact wording is not frozen.

Preserve the caller's NumPy error policy. Expected normalization/underflow/overflow handling must not emit arithmetic RuntimeWarning or FloatingPointError, including under a caller's raise policy. Suppress no unrelated warning category. Unrelated exceptions and warnings remain observable. No concurrent external mutation guarantee is selected.

The function has no seed, noise, persistence, filesystem or process-global-state interface. It must not consume/reseed a global random stream or depend on camera/optical evaluation. It promises no fixed whole-workflow memory/time bound. Output representation failures, actual allocation failures and incomplete execution are not successful source generation.

## Observable obligations and independent evidence

These are behavioral scenarios, not a test-count commission or implementation-path map.

| ID | Observable obligation / credible wrong outcome |
|---|---|
| S01 | Empty catalogue and valid zero-brightness rows yield exact zero arrays; zero rows still undergo domain/containment validation but do not fail for K=0. |
| S02 | True three-dimensional spherical membership uses physical z/y/x coordinates, anisotropic spacing, half-cell sites, independent refinements, off-grid centers and exact closed ties. |
| S03 | One positive object assigns correctly rounded B/K to every occupied site, with no volume/focus multiplier or falsely exact mass promise; non-power-of-two K is meaningful. |
| S04 | Overlaps, duplicates and unequal brightnesses add in declared row order, including legitimate rounded-away increments; there is no union or reordered/exact-sum substitution. |
| S05 | Wholly contained near-edge and tangent spheres remain permitted; partly exterior spheres reject without clipping, wrap or mass restoration. |
| S06 | Positive brightness with K=0 reports range; the same geometry with B=0 remains permitted after domain/containment validation. |
| S07 | Positive B/K rounding to zero reports range, while representable nonzero subnormal weights remain supported. |
| S08 | Overlap-addition overflow rejects the complete call; large but finite representable positives remain supported. |
| S09 | Dtype/layout/endian/read-only normalization and ownership preserve inputs, including allowed conversion rounding; original and normalized nonfiniteness remain distinct validation obligations. |
| S10 | Catalogue, shape/refinement/spacing, radius/brightness and containment invalid domains reject with the specified code; ordinary binding errors remain TypeError. |
| S11 | Extreme finite geometry retains exact normalized-input decisions without arbitrary magnitude caps; demonstrably unrepresentable output shapes/storage report range. |
| S12 | Actual allocation and unrelated dependency exceptions/warnings propagate; expected arithmetic handling preserves caller NumPy settings and warning behavior on success and rejection. |
| S13 | Output is complete, owned, native float64, writable and C-contiguous; repeat calls are deterministic and leave inputs/global random state untouched. |
| S14 | Documentation and later evidence distinguish this finite midpoint model, normalization/storage mass error, geometric/source refinement, finite field and optical/pixel discretization; no continuum accuracy threshold is inferred. |

Fresh independent A/B derive small integer/rational sphere-membership cases, including a closed-boundary equality and nearby strict alternatives, rather than using runtime output as expected truth. Independently count occupied sites and derive the prescribed rounded weights/additions, including legitimate positive layouts and domains. Do not require a private helper, particular numerical library call, search strategy or duplicate production algorithm. Report platform-limited examples honestly; do not fabricate a wider-float conversion failure on a platform without a wider native floating format.

Later scientific evidence compares at least three declared source refinements while holding physical objects, detector box and other discretizations fixed. It reports actual mass/shape/image sensitivity and the displacement domain; the finest sampled model is an empirical reference, not exact continuous-sphere truth. The next contract may be accepted as a faithful implementation of this finite model even if later calibration or reconstruction is inaccurate, unstable or unsuccessful. No numerical continuum-accuracy threshold, scene catalogue, inverse information channel, artifact writer or composition runtime is adopted here.

## Intake decision

The coordinator selects strictly positive radii for every row, including zero-brightness rows. The authorized trial uses finite 100 nm diameter beads; a point-emitter extension is outside this slice. Zero-brightness rows skip membership/range work only after domain/containment validation. No owner approval checkpoint is added to restate the existing simulation request.
