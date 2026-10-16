# Explicit signed physical-frequency empirical transfer sampling v1

**Version 1.0. October 16, 2026.** The owner authorized the next dependency-ready scientific roadmap slice above accepted PR35 and successive slices until actual roadmap exit. This concrete G1 contract selects explicit point evaluation of the already selected complex Cartesian trilinear interpolant. It supplies a transfer query primitive; estimation and a changed reconstruction estimator remain dependent work.

## Public boundary and consumer meaning

```python
from simrecon import EmpiricalFrequencySamples, sample_empirical_volume_transfer

sampled = sample_empirical_volume_transfer(
    response,
    order=-1,
    frequencies_zyx_per_um=points,
    calibration_carrier_bins=(ky_c, kx_c),
    coordinate_offset_yx=(oy, ox),
    phase_reference_shift_rad=delta,
    source="explicit physical pairing",
)
```

Only response is positional. All six keywords are required. Ordinary Python argument-binding TypeError applies. Each call samples one signed order in {-2,-1,0,1,2} for one selected orientation/channel/time. Queries use z/y/x and cycles per micrometre (cycles/µm). Response values and returned transfer values are dimensionless under their upstream normalization. Order is a nonboolean Python/NumPy integer scalar, converted exactly to Python int; bool, floating and other scalar types reject.

The overlap consumer needs order zero at object frequency f and order m at detector frequency f+m*q, with lateral physical carrier q and zero axial component. Reconstruction similarly needs order m at f+m*q where its corresponding detector observation exists. The caller constructs each coordinate list. This operation performs no coordinate shifting, observation interpolation, carrier/phase/gain estimation, transfer division, inferred support, reconstruction, transform or file I/O. It does not alter the current integer-carrier detector-grid consumers. A continuous carrier estimator also needs its own observation and identifiability contract.

Calibration carrier is used only for the gauge below. No specimen-carrier equality can be inferred from arbitrary query points, and there is no specimen-carrier input. The caller separately establishes physical calibration/specimen compatibility and candidate-carrier meaning. Declared delta maps to the caller's chosen phase reference; unknown phase cannot be supplied from hidden simulator truth. The operation authenticates no instrument or provenance.

## Query geometry and physical endpoints

frequencies_zyx_per_um is a plain ndarray of float64 width, either endian, shape (P,3), P>=1, with finite components. Strided, reversed, Fortran and read-only arrays are valid. Reject nonarrays, array subclasses/masked arrays, wrong width/kind/rank/last dimension, empty lists of points and nonfinite components. Preserve order, duplicates and signed-zero coordinate bits in the returned native float64 snapshot. Queries need not form a Cartesian grid, be sorted, have uniform steps or correspond to any detector grid.

Each supplied binary64 component means its **exact represented real value**. There is no snapping tolerance. Source dimensions Nc and converted spacings dc define exact ideal nodes k/(Nc[a]*dc[a]), where k=-floor(Nc[a]/2),...,ceil(Nc[a]/2)-1, and each dc is its exact represented rational. Tolerated source coordinate metadata does not define the lattice. Consequently a correctly rounded source coordinate exported as binary64 need not be an exact source node and may lie just outside an exact endpoint. Callers needing an ideal lattice-node request must use the existing ideal-grid adapter or explicitly select an in-hull representable point; this API makes no bitwise equivalence promise between rounded coordinate requests and ideal-grid requests. Do not add an endpoint tolerance to conceal that difference.

For order m>=0, evaluate the source row m at query f. For m<0 evaluate row abs(m) at **-f in all three axes**, then conjugate the gauge-corrected positive-order result. Check only the actually evaluated coordinates against the closed ideal source hull on every axis. A singleton source axis covers exactly zero. Any missing point rejects the whole call with incomplete_empirical_transfer_coverage, even for zero values, an unused downstream mask or supposed physical support. Valid in-hull zeros and exact cancellation remain data. Closed endpoints use only the endpoint, with no nonexistent neighbor. No wrapping, periodic bridge, clipping, extrapolation or zero fill applies.

Even and odd source dimensions are valid. Physical positive and negative Nyquist endpoints remain distinct: for an even axis only its canonical negative endpoint is stored. A positive-order query at the missing positive endpoint rejects; the same physical query for a negative order can succeed by reflecting to the stored negative endpoint. The negative-order domain is the reflected positive-order hull. The existing reconstruction uses modular negation at even Nyquist; do not change it or claim this sampler can be substituted there without a separately contracted representation change. No target-grid shape or odd/even restriction exists here.

## Interpolation, gauge and exact-node behavior

On each evaluated axis coordinate equal to an exact ideal source node, use that node with weight one. Otherwise use its adjacent ideal nodes f0<f<f1 with exact rational t=(f-f0)/(f1-f0) and weights (1-t,t). Tensor products give up to eight nonnegative weights summing to one. Apply identical weights to real and imaginary components; equivalent sequential linear combinations are permitted. No backend, private call layout or SciPy interpolation routine is required.

Let I_m(f)=sum_v w_v(f)*E_m(v), where source E contains stored positive rows 0,1,2. Define exact rational

```text
rho = kc_y*(source_origin_y+oy)/Nc_y
    + kc_x*(source_origin_x+ox)/Nc_x
F_0(f) = I_0(f)
F_m(f) = I_m(f) * exp(-i*m*(2*pi*rho+delta)), m=1,2
F_-m(f) = conj(F_m(-f)), m=1,2.
```

Offsets are in source calibration samples; the common coordinate origin and specimen-minus-calibration phase-reference shift have the meaning selected in the existing transfer contracts. Response arrays are already centered. No second centering or frequency-dependent origin phase applies. Reduce exact rho modulo one before finite-angle evaluation; huge finite delta is valid without forming overflowing 2*delta. Apply this constant gauge exactly once. There is no magnitude/phase interpolation, unwrapping, Hermitian projection, radial averaging, normalization, cleanup, bead compensation, order gain, extra side factor, site-count or voxel-volume factor.

At complete exact source nodes, order-zero real/imaginary component bits copy unchanged. When rho is integral and delta is either signed zero, positive-order component bits at complete exact nodes copy unchanged even if complex magnitude overflows. For negative order under that identity gauge, the reflected exact-node result is exact componentwise conjugation: real bits retained and imaginary sign bit toggled. No signed-zero value promise applies to other computed values. An all-zero stencil gives exact complex zero up to signed-zero bits. Arbitrary algebraic non-Hermitian E0/sides and zero/nonunit E0 DC remain valid.

## Response and scalar validation, ownership

response is an EmpiricalVolumeResponse instance, including ordinary record subclasses. Validate every public field, including unused rows and source samples, with exactly the source-response rules in [the trilinear contract](empirical-trilinear-transfer-v1.md#representation-and-validation). In particular: plain finite complex128-width values (3,Nz,Ny,Nx), positive sizes; plain finite float64-width source frequency vectors matching each axis, strictly increasing when nonsingleton, exactly zero at centered DC and nonzero elsewhere; each vector within 8*eps*abs(f_ideal)+q0 of its exact ideal rational coordinate, eps=2^-52 and q0=2^-1074. Avoid rejecting solely for overflowing intermediate Nc*dc when final coordinates are representable. Source spacing is an exact built-in tuple/list of three nonboolean Python/NumPy real integer/floating scalars converted to finite positive binary64 µm; source origin is an exact built-in tuple/list of three nonboolean Python/NumPy integer scalars in bounds. Finite arbitrary signed complex values, either endian and read-only/strided/Fortran storage are accepted. Missing required fields reject with invalid_empirical_transfer_response; unrelated getter exceptions propagate unchanged. Every field is validated regardless of selected order, gauge or zeros.

calibration_carrier_bins and coordinate_offset_yx are exact built-in tuple/list pairs of nonboolean Python/NumPy integer scalars. Extract exact Python ints, no numpy.intp bound, floating coercion, principal-window reduction or magnitude cutoff. Signed/unsigned/zero and huge declarations are valid. Phase is a nonboolean Python/NumPy real integer/floating scalar individually converted to finite binary64; subnormal/huge/signed-zero and conversion underflow are valid. source is a nonblank opaque string retained unchanged. Expected TypeError/ValueError/OverflowError during numeric conversion translate at their corresponding boundary; MemoryError and unrelated exceptions propagate. Message prose and simultaneous-invalid precedence are unspecified.

Snapshot all accepted response arrays/metadata, query coordinates and scalar declarations before numerical interpolation. Preserve input contents/layout/write flags and caller NumPy floating/warning policy on success/rejection. Concurrent external mutation is outside the guarantee. Full snapshots, scratch/output allocations and ordinary MemoryError are permitted; no practical-size, memory or throughput promise is selected.

Return frozen-binding EmpiricalFrequencySamples with exactly five fields: values (owned mutable native C-contiguous complex128 vector (P,)); frequencies_zyx_per_um (owned mutable native C-contiguous float64 array (P,3)); order (Python int); source (unchanged label); provenance (independently owned mutable plain dict, read-only by convention). Arrays alias no input, one another, other outputs or another call. Wrapper field rebinding/deletion fails; direct construction adds no validation/deep immutability.

provenance has exactly seven keys: sampling='complex_cartesian_trilinear_points_v1'; source_shape_zyx (Python-int triple); source_voxel_size_um (converted Python-float triple); source_origin_zyx (observed Python-int triple); calibration_carrier_bins; coordinate_offset_yx (exact Python-int pairs); phase_reference_shift_rad (converted Python float including signed zero). No caller container or other call aliases it. Keep upstream raw/correction/calibration identities and physical specimen pairing externally.

## Numerical and operation-time obligations

Use binary64/complex128 processing with bounded-angle gauge rotation and safe component operations. All expectations use exact stored source components, exact represented query coordinates and geometry, and converted delta. For the selected/reflected stencil define L=sum_v w_v*(abs(Re E_abs(m)(v))+abs(Im E_abs(m)(v))) using an observer that does not overflow/underflow. Let Delta=1024*eps*L+64*q0. Successful values satisfy abs(returned-F_exact)<=Delta. This dimensionless project allowance is inherited from the selected interpolant and includes interpolation/gauge arithmetic; it is not an allowance for approximation to physical truth. Exact-node requirements supersede it. Negative conjugation is exact and preserves this modulus budget.

Apart from actual dependency/allocation failure, otherwise-valid calls must succeed when every exact final real/imaginary component satisfies abs(component)+Delta<Fmax. This is a sufficient-success condition, never a rejection threshold. Otherwise attempt computation; final computed component nonfiniteness rejects the whole call with unrepresentable_empirical_interpolation. Safely finite weighted contributions cannot be dropped merely because a standalone weight underflows; intermediate complex magnitude, unrotated sum or rotation-product overflow alone cannot reject safely finite final components. No clipping, saturation, partial return or fallback. Range classification near Fmax may depend on roundoff.

Handled conversion/range/underflow emits no arithmetic RuntimeWarning or FloatingPointError under caller modes. Preserve unrelated warning categories and unrelated exceptions. Ordinary MemoryError propagates. No artificial public dependency-failure seam is introduced. Expected numeric conversion exceptions translate only at conversion; unrelated failures are not reclassified.

The exact interpolant reproduces multi-affine complex functions. For a separately declared twice-differentiable continuous comparison, its exact-sample approximation can be bounded per cell by sum_a h_a**2 * sup_cell(abs(partial_aa H))/8; convex interpolation amplifies bounded source error by no more than its largest stencil error. Arithmetic, interpolation/model error, calibration error, physical mismatch and downstream estimator bias must be reported separately. No universal physical accuracy is claimed.

| Rejected obligation | SimreconError.code |
|---|---|
| Response instance or any source public field | invalid_empirical_transfer_response |
| Signed order grammar/value | invalid_empirical_transfer_order |
| Query ndarray/dtype/shape/finite components | invalid_empirical_transfer_frequencies |
| Calibration carrier grammar/conversion | invalid_empirical_transfer_carrier |
| Coordinate-offset grammar/conversion | invalid_empirical_transfer_coordinate_offset |
| Phase grammar/conversion/finiteness | invalid_empirical_transfer_phase_shift |
| Nonblank supplied source label | invalid_otf_source |
| Any evaluated coordinate outside closed source hull | incomplete_empirical_transfer_coverage |
| Final computed component nonfiniteness | unrepresentable_empirical_interpolation |

## Scenario inventory, ownership and delivery

| ID | Distinct obligation / credible wrong outcome |
|---|---|
| Q01 | Public API/export, six required keyword bindings, five exact record fields/types/frozen bindings |
| Q02 | One signed integer order -2..2; legitimate scalar widths versus bool/float/invalid values |
| Q03 | Plain finite float64-width nonempty (P,3) queries; layouts/endian/signed-zero bits/order/duplicates |
| Q04 | Exact represented-coordinate geometry, no snapping to tolerated metadata or rounded ideal nodes |
| Q05 | Full complex anisotropic off-grid tensor weights and multi-affine reproduction |
| Q06 | Closed endpoints/singletons/exact-node copy and all-zero/cancellation outcomes |
| Q07 | Signed negative orders reflect all axes then conjugate; zero row remains arbitrary |
| Q08 | Even-source physical endpoint asymmetry, reflected negative-order domain; existing modular consumer unchanged |
| Q09 | Strict whole-call missing-coverage rejection independent of zeros/masks/physical-support guesses |
| Q10 | Source-sample offsets, moved bead versus storage roll, centering once and two-order phase sign |
| Q11 | Huge exact carriers/offsets and finite huge/subnormal phase; no specimen-carrier equality inferred |
| Q12 | Full source validation including unused rows/points and ordinary record subclasses/getter exceptions |
| Q13 | Source frequency tolerance/canonical geometry/DC/representation and spacing/origin grammar/extremes |
| Q14 | Source label and scalar conversion boundaries versus allowed signed/unsigned/extreme declarations |
| Q15 | Snapshots/input preservation/owned native arrays/provenance independence and repeated calls |
| Q16 | Component-safe arithmetic/allowance/sufficient success, tiny weights with finite contributions and range rejection |
| Q17 | Floating/warning policy preservation and handled diagnostics versus unrelated/allocation failures |
| Q18 | Independent held-out smooth-transfer error separated from arithmetic/model error |
| Q19 | Explicit overlap query coordinates f and f+m*q, sign/gauge/scale once; no observation interpolation implied |
| Q20 | Public raw bead calibration to signed physical queries; compatibility, executed usage and honest downstream limits |

High-risk scientific/custom-oracle route: fresh native Sol/high A, fresh B, restricted C and fresh D. No human numerical execution/review/spending limits were set. A owns tests/test_empirical_frequency_sampling.py and optional tests/empirical_frequency_fixture.py only. C owns src/simrecon/_empirical_frequency.py, additive src/simrecon/__init__.py exports and docs/usage/empirical-frequency-sampling.md only, plus ignored example evidence. Existing helpers may be reused without changing their files/contracts. No reviewed tests/fixtures/snapshots, workflows, discovery/coverage settings, dependencies, skills/policy or unrelated runtime changes. Coordinator owns this contract, task/PROJECT/roadmap pointers, packets/accounting and useful unique root lessons.

A independently derives exact rational bracketing/weights and sufficient-precision gauge expectations from public definitions, not product output or legacy source. B independently recalculates and audits both permitted-positive classes and omissions before a frozen checkpoint. Absent API is setup evidence, not product-red; initially passing prerequisites remain valid. Before blind probes use installed scripts/source_free_check.py, retaining categories/messages/locations/status without source/locals for Python/pytest/subprocesses. Blind A/B receive a public allowlist only; no implementation/history/state/coverage maps or lesson entries. D assesses independently before current implementation lessons.

C executes two small retained examples: (1) asymmetric complex analytic multi-affine responses on anisotropic source geometry, non-Cartesian/repeated queries, signed rows/gauge and explicit overlap points; (2) independent raw point-bead calibration through public declaration/correction/calibration to this sampler, with a declared smooth held-out comparison and distinct physical coordinates. Retain raw/expected/returned arrays, hashes and justified arithmetic/interpolation budgets. Known phases/calibration carrier are legitimate within this narrow known-parameter demonstration only. Do not claim truth-hidden estimation, changed reconstruction or continuous-optics validity. A figure is optional when measured tables/equations already explain the operation.

The standing owner task selects 100% Coverage.py native measured statements and branches across all instrumentable owned src/simrecon and scripts globally/per package/per file, including never-imported files/relevant subprocesses. This task does not adopt the installed advisory percentage policy. Canonical exact-candidate make verify and raw/JSON/complete HTML/measurement/build/version/environment proof are required before fresh D/publication; Ubuntu24.04 and macOS15 CI are reconciled independently. No platform union or coverage-completeness inference. No reference C execution, merge/release or unrelated external messaging. The accepted PR baseline and inherited charges remain in the task evidence pointer.

Opened primary convention references: [NumPy DFT and conjugate symmetry](https://numpy.org/doc/stable/reference/routines.fft.html); [SciPy rectilinear interpolation documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.RegularGridInterpolator.html). These describe general conventions, not the exact-rational query domain or this project's numerical guarantees; all API/error/gauge/budget choices above are explicit contract selections.
