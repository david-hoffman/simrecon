# Cartesian complex empirical transfer interpolation v1

**Version 1.0. October 15, 2026.** The owner requested the next roadmap slice stacked above completed shared-node transfer, then selected “option 1” after a detailed comparison of complex linear interpolation, finite-displacement Fourier continuation and a continuous acquisition model. This contract records Cartesian complex trilinear interpolation. It is a partial Phase 4 / G1 foundation, not an experimental-validity or complete independent-grid workflow claim.

## Public boundary and physical assumption

```python
from simrecon import adapt_empirical_volume_response_trilinear

adapted = adapt_empirical_volume_response_trilinear(
    response,
    target_shape_zyx=(nz, ny, nx),
    target_voxel_size_um=(dz, dy, dx),
    calibration_carrier_bins=(ky_c, kx_c),
    specimen_carrier_bins=(ky_s, kx_s),
    coordinate_offset_yx=(oy, ox),
    phase_reference_shift_rad=delta,
    source="explicit calibration/specimen pairing",
)
# adapted.orders is VolumeOrderOtf; explicitly pass its orders to reconstruct_volume.
```

Only response is positional; all seven keywords are required. Python argument-binding TypeError is unchanged. One call pairs one orientation/channel/time. The caller assumes the calibration and specimen have the same effective response at common physical frequencies after the declared gauge correction. Axis directions, z/y/x order and focal-plane-relative model agree. Geometry validation cannot establish this physical assumption or instrument validity. Different dimensions and lateral/axial spacings are permitted within the coverage and endpoint rules below. Actual phase schedules may differ; the supplied scalar reference shift is not a substitute for actual phases or independent per-step deviations.

The operation consumes stored full Cartesian values of 0,+1,+2. It adds no radial averaging, same-order Hermitian projection, phase unwrapping, magnitude interpolation, support cleanup, finite-bead compensation, gain fitting, brightness restoration, extra side-order factor, voxel-volume/site-count factor, transform, persistence, raw correction or parameter estimation. Calibration estimation error, interpolation approximation error, numerical arithmetic, physical pairing error and downstream reconstruction/regularization bias remain separate.

## Geometry, coverage and endpoint decisions

Let source dimensions and converted positive binary64 spacings be Nc[a], dc[a], and target Ns[a], ds[a]. Treat each converted spacing as its exact represented rational. Source and target modes are -floor(N/2),...,ceil(N/2)-1. The ideal physical coordinate is k/(N*d), in cycles/µm. Stored source coordinate vectors are validated as described below; their tolerated rounding does not define node identity, brackets, weights or coverage.

Every target dimension must be odd, including allowed singleton dimensions. Thus target modular negation equals physical frequency negation at every nonzero requested frequency. Even target dimensions reject with unsupported_empirical_interpolation_target_nyquist. A general complex interpolant need not identify opposite physical Nyquist endpoints; this contract chooses no such identification and changes no existing reconstruction representation. Existing same-grid/shared-node adapters retain their own even-grid acceptance rules. Odd/even source dimensions are valid.

For each axis every ideal target coordinate must lie in the closed ideal source frequency interval. A singleton source axis covers zero only. A singleton target axis requests zero and accepts any otherwise valid positive spacing. Missing coverage rejects before considering transfer values, optical zeros, downstream masks or numerical rotation. There is no extrapolation, periodic endpoint bridge, frequency wrapping, clipping, zero fill or inferred physical support. Stored zero values and exact cancellation inside coverage are legitimate data. A closed source endpoint needs only that endpoint, not an out-of-bounds neighbor.

Both lateral physical carriers must separately agree exactly:

```text
kc_y/(Nc_y*dc_y) = ks_y/(Ns_y*ds_y)
kc_x/(Nc_x*dc_x) = ks_x/(Ns_x*ds_x).
```

Integer declarations retain their nonwrapping physical meaning, including huge values. There is no floating tolerance or principal-window carrier reduction for these equalities. Carriers may be zero. Coordinate offsets are measured in source calibration samples and map stored source indices into common illumination coordinates. Target index zero declares common coordinate zero. Offsets do not specify a target bead or specimen drift.

## Interpolant and gauge

For a target coordinate equal to a source node, that axis has a single contributor of weight one. Otherwise use its two adjacent source ideal coordinates f0<f<f1 and exact rational weights 1-t,t, with t=(f-f0)/(f1-f0). Tensor products give up to eight nonnegative weights summing to one. Define for each order m

```text
V_m(j) = sum_v w_v(j) * E_m(v)
rho = kc_y*(source_origin_y+oy)/Nc_y + kc_x*(source_origin_x+ox)/Nc_x
F_0(j) = V_0(j)
F_m(j) = V_m(j) * exp(-i*m*(2*pi*rho+delta)), m=1,2.
```

Weights act identically on real and imaginary components. All mathematical expectations use exact stored source components, exact geometry and the converted delta. Interpolation may be implemented through equivalent sequential linear combinations. Private organization/backend is unspecified. No scipy interpolator or particular call boundary is required.

Source responses are already centered. Add no frequency-dependent origin phase and no second centering. Reduce exact rational rho modulo one before finite-angle evaluation. Huge finite delta is valid; do not form overflowing 2*delta. The constant per-order gauge commutes mathematically with interpolation and is applied once. Common relative order scale is retained. Reconstruction applies its own caller-supplied gains once.

At a complete exact source node, order-zero real/imaginary component bits must copy unchanged. If rho is integral and delta is either signed zero, all orders at complete exact nodes copy component bits unchanged, even when complex magnitude would overflow. No signed-zero bit promise applies to other computed values. An all-zero stencil returns exact complex zero up to signed-zero bits. No normalization or positivity constraint applies to E0 or its DC.

The existing consumer defines negative orders by modular target frequency negation and conjugation. For odd targets, physical negation is represented consistently by the target grid; do not replace it with reversal or same-frequency conjugation. The adapter itself returns only 0,+1,+2.

## Representation and validation

response is an EmpiricalVolumeResponse instance, including ordinary record subclasses. A missing required attribute rejects with invalid_empirical_transfer_response; unrelated getter exceptions propagate unchanged. Validate every field before interpolation, including unused source samples and zero-side-order cases. values is a plain ndarray of complex128 width, either endian, shape (3,Nz,Ny,Nx), positive spatial sizes, finite real/imaginary components. Arbitrary algebraic non-Hermitian values, zero rows and zero/nonunit E0 DC are valid. Read-only, reversed/strided and Fortran storage are valid. Reject nonarrays/array subclasses/masked arrays, other dtype widths/kinds, wrong rank/order count, empty dimensions and nonfinite components.

Each source frequency vector is a plain float64-width ndarray, either endian, matching its axis length, finite, increasing when nonsingleton, nonzero off DC and exactly zero at centered DC. Against the ideal rational f=k/(N*d), require abs(f_stored-f)<=8*eps*abs(f)+q, eps=2^-52 and q=2^-1074. This is source metadata validity only. Avoid intermediate period overflow when final frequencies are representable.

Source voxel_size_um is an exact built-in tuple/list of three nonboolean Python/NumPy real integer/floating scalars, converted individually to finite positive binary64 µm. Source origin_zyx is an exact built-in tuple/list of three nonboolean Python/NumPy integers, each within its source axis. Preserve their exact Python-int values in provenance.

Target shape is an exact built-in tuple/list of three nonboolean Python/NumPy integers, each positive and representable by numpy.intp. Apply the separate odd-target endpoint rule after shape validity. Target spacing uses the same container/scalar/conversion rules as source spacing. Conversion underflow defines the represented spacing and a converted zero rejects. Target frequency components are RN64(k/(N*d)), the correctly rounded binary64 exact rational coordinate, with positive zero at DC. They must be finite, increasing when nonsingleton and nonzero off DC. Any RN64 infinity, off-DC rounded zero or collapse, including an expected range failure while computing this coordinate, rejects with unrepresentable_otf_frequencies; unrelated/allocation failures propagate; overflowing N*d alone cannot reject.

Both carriers and coordinate_offset_yx are exact built-in tuple/list pairs of nonboolean Python/NumPy integer scalars, converted exactly to Python ints without an intp bound. Phase is a nonboolean Python/NumPy real integer/floating scalar converted to finite binary64; finite subnormal/huge/signed-zero and conversion-underflow values are valid. source is a nonblank opaque string retained unchanged. Expected conversion TypeError/ValueError/OverflowError translate at the corresponding boundary. Message prose and simultaneous-invalid precedence are unspecified.

Snapshot accepted arrays and metadata before numerical computation. Inputs, layout, write flags, NumPy floating modes and warning policy remain unchanged on success/rejection. Concurrent external mutation is outside the guarantee. Full snapshots/output/scratch and ordinary MemoryError are permitted; there is no practical-size, memory or performance promise.

## Arithmetic, error and failure

Use binary64/complex128 arithmetic, with bounded-angle rotation and scaled or otherwise safe component operations. A standalone weight underflow cannot discard a representable weighted source contribution exceeding the allowance; source/target spacings at opposite binary64 scales remain within the contract when coordinates are valid. Complex magnitude and intermediate arithmetic overflow alone cannot reject safely finite final components. For a target stencil define L_m=sum_v w_v*(abs(Re E_m(v))+abs(Im E_m(v))) evaluated without observer overflow and Delta_m=1024*eps*L_m+64*q. Every successfully returned value must satisfy abs(F_returned-F_exact)<=Delta_m. This absolute dimensionless project allowance includes weight/interpolation and gauge rounding; it is not an approximation-to-physics allowance or a relative/subnormal-retention promise. Exact-node copy requirements above supersede it.

Apart from actual dependency/allocation failure, otherwise valid inputs must succeed when every final real/imaginary component satisfies abs(component)+Delta_m<Fmax, where Fmax is maximum binary64. This sufficient-success condition is not an input rejection threshold. Otherwise attempt computation; final computed component nonfiniteness rejects the whole call with unrepresentable_empirical_interpolation. Range classification near Fmax is operational and may depend on roundoff. No clipping, saturation, partial result or fallback.

Handled conversion/range/underflow emits no arithmetic RuntimeWarning or FloatingPointError under caller modes. Preserve unrelated warning categories. MemoryError and unrelated exceptions propagate unchanged. No artificial public dependency-failure seam is selected. Arithmetic exceptions at expected numeric conversion translate only at conversion; ordinary unrelated failures are not reclassified.

The interpolant reproduces complex multi-affine functions mathematically. Against a separately declared twice-differentiable continuous comparison H, its exact-sample approximation can be bounded per cell by sum_a h_a^2*sup_cell(abs(partial_aa H))/8. Bounded source error propagates through convex weights by at most its largest stencil error. Demonstrations must independently measure held-out approximation error and arithmetic error; no universal physical accuracy is claimed.

## Result, provenance and errors

Return frozen-binding TrilinearVolumeTransfer with exactly orders and provenance. orders is existing VolumeOrderOtf: owned mutable native C-contiguous complex128 values (3,Nz_s,Ny_s,Nx_s); three separately owned mutable native C-contiguous float64 target frequency vectors; converted Python-float target voxel triple; origin_zyx=(0,0,0); source retained unchanged. Generate target coordinates using the RN64 rule above; this also satisfies the 8*eps*abs(f)+q coordinate allowance. At shared nodes coordinate bits need not equal tolerated source metadata bits. All four arrays alias neither inputs, one another, other outputs nor another call.

provenance is an independently owned mutable plain dictionary, read-only by convention, with exactly eight keys: sampling='complex_cartesian_trilinear_v1'; source_shape_zyx (Python-int triple); source_voxel_size_um (converted Python-float triple); source_origin_zyx (observed Python-int triple); calibration_carrier_bins; specimen_carrier_bins; coordinate_offset_yx (exact Python-int pairs); phase_reference_shift_rad (converted Python float including signed zero). No caller container or other call aliases it. Wrapper bindings are frozen; contents remain mutable. Direct construction adds no validation or deep immutability. Keep upstream calibration/raw/correction/phase identities externally.

| Rejected obligation | SimreconError.code |
|---|---|
| Response type or any source public field | invalid_empirical_transfer_response |
| Target shape container/scalar/positivity/intp extent | invalid_empirical_transfer_target_shape |
| Any even target dimension | unsupported_empirical_interpolation_target_nyquist |
| Target spacing grammar/conversion/finite positivity | invalid_empirical_transfer_target_voxel_size |
| Target final frequency range/order/nonzero representation | unrepresentable_otf_frequencies |
| Either carrier grammar | invalid_empirical_transfer_carrier |
| Coordinate-offset grammar | invalid_empirical_transfer_coordinate_offset |
| Phase grammar/conversion/finiteness | invalid_empirical_transfer_phase_shift |
| Nonblank source string | invalid_otf_source |
| Any target point outside source closed hull | incomplete_empirical_transfer_coverage |
| Physical carrier inequality | mismatched_empirical_transfer_carrier |
| Final computed component nonfiniteness | unrepresentable_empirical_interpolation |

## Scenario inventory, ownership and verification

| ID | Distinct observable obligation / credible wrong outcome |
|---|---|
| T01 | Required public API/export, keyword binding and exact wrapper/record fields |
| T02 | Full signed-complex trilinear weights on independent anisotropic Cartesian geometry |
| T03 | Exact rational geometry, brackets/node identity despite tolerated rounded metadata |
| T04 | Exact shared-node component copy and closed endpoint/singleton stencils |
| T05 | Different dimensions and lateral/axial spacing; no site/voxel rescaling |
| T06 | Odd target negation consistency; even target rejection; even source permitted |
| T07 | Strict closed-hull rejection, singleton coverage, no mask/zero/support bypass |
| T08 | Exact physical carrier matching, huge signed/unsigned/zero/nonwrapping declarations |
| T09 | Source-sample offset and storage-roll/offset equivalence; physical bead movement distinguished |
| T10 | Specimen-minus-calibration phase sign, two side orders and differing actual schedules |
| T11 | Center origin once, target-zero origin, common gain once in reconstruction |
| T12 | Legitimate arbitrary/non-Hermitian E0/sides, zero/nonunit DC, signed cancellation and zero stencils |
| T13 | Entire source validation including unused samples; source type/array/dtype/shape/finiteness |
| T14 | Source coordinate tolerance/order/DC/representation/extremes and source metadata grammar |
| T15 | Target shape grammar/extent versus allowed singleton/odd sizes |
| T16 | Target spacing grammar/conversion/extremes and final frequency representability |
| T17 | Carrier/offset scalar/container grammar versus exact huge permitted integers |
| T18 | Phase grammar/conversion/extremes/signed-zero and source label preservation |
| T19 | Source snapshots/input preservation/layout/endian, result ownership and frozen bindings |
| T20 | Native component ranges, numerical allowance and safely finite success versus computed-range rejection |
| T21 | Caller floating/warning state, handled diagnostics and unrelated/allocation exception propagation |
| T22 | Independent analytic multi-affine exactness and smooth held-out interpolation error accounting |
| T23 | Public raw-bead calibration → adapter → known-parameter specimen reconstruction; explicit model error/bias |
| T24 | Existing APIs/gates/dependencies unchanged and executed usage/provenance limitations |

High-risk scientific/custom-oracle route: fresh native gpt-6.1-sol/high A, fresh B, restricted C and fresh D; actual serving/metering recorded when available. No human-set numeric execution/review/spend limits. Initial passing existing behavior is valid; absent new API is not product-red. A owns tests/test_empirical_trilinear_transfer.py and optional tests/empirical_trilinear_fixture.py only. C owns src/simrecon/_empirical_trilinear.py, additive src/simrecon/__init__.py exports and docs/usage/empirical-trilinear-transfer.md only, plus ignored example evidence. C may reuse existing helpers without editing their contracts/files. No reviewed test/fixture, workflow, discovery/coverage, dependency, policy or unrelated runtime edits. Coordinator owns this contract/task/PROJECT pointer and packets/accounting. No legacy import/copy/execution.

Owner-provided AGENTS instructions require 100% Coverage.py native measured statements and branches across all instrumentable owned src/simrecon and scripts, globally/per package, including never-imported files and relevant subprocesses. make verify is the canonical exact-candidate full-local gate; retain native raw/JSON/complete HTML, exclusions/skips/unsupported metric limits, same-run resources, wheel/source/version, lock/build/environment identities. No platform union or behavioral-completeness inference. Required configured Ubuntu24.04/macOS15 pull-request CI remains separate. A/B receive only the public packet/allowlist and source-free diagnostics, never implementation/history/state/coverage maps/legacy sources. D forms independent assessment before current implementation lessons. No merge/release.

C executes two small independently generated public examples: an asymmetric analytic complex multi-affine transfer with declared gauge/offsets and independent target values; and raw point-bead calibration through existing public declarations/correction/calibration, this adapter and known-parameter reconstruction. The latter uses a declared smooth continuous comparison with distinct source/target geometry and retained raw/expected/returned arrays, held-out interpolation error and downstream ridge/model error separately. A discrete-source response must not be mislabeled an exact arbitrary continuous physical response. Known phases/carriers remain legitimate inputs only within this known-parameter demonstration. No bulk fixtures/resource optimization is authorized.
