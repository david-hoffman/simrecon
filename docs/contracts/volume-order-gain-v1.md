# VOLUME-GAIN-01: known-carrier relative complex volume-order gain

**Version 1.0. October 9, 2026.** The owner's standing instruction, “Keep on stacking in a new task! Continue that pattern until the roadmap is complete,” authorizes this coherent scientific slice above published and fully verified PR #19. This contract resolves the proposed fit before blind tests. Advice supplies no role verdict.

## Public operation and meaning

```python
from simrecon import VolumeOrderGainEstimate, estimate_volume_order_gain

fit = estimate_volume_order_gain(
    images,
    order_otf=calibration,
    phase_steps_rad=steps,
    carrier_bins_yx=(ky, kx),
    order=2,
)
fit.gain
fit.relative_residual
fit.coherence
fit.status
```

Only images is positional. All four keywords are required; ordinary Python argument-binding TypeError applies. One call fits one caller-selected positive order, m=1 or m=2, for one orientation. It returns a dimensionless complex correction relative to the supplied nominal effective transfer. It estimates no carrier, independent phase steps, brightness, absolute throughput, measured instrument profile or full physical calibration. Existing APIs, dependencies, command-line behavior and gates remain unchanged. The operation performs no files or automatic reconstruction/correction.

Images `(N,Nz,Ny,Nx)` and fundamental phase steps `(N,)` inherit exactly the representations, float64 snapshots, finite checks, phase basis, rank, least-squares semantics and stable errors of [volume separation](volume-phase-separation-v1.md). N>=5. Pass the supplied fundamental steps unchanged to the five-column fit and then select c1 or c2; do not double the steps for order two, reduce huge steps modulo rounded 2*pi, or infer a coupled phase model. Signed data, unequal N>5 steps, off-model projections, every real integer/floating width/endian, singleton axes and strided/read-only plain arrays remain permitted.

Order is a nonboolean Python or NumPy integer equal to 1 or 2. Carrier is an exact built-in tuple/list of two nonboolean Python/NumPy integers, or a plain one-dimensional length-two signed/unsigned integer ndarray, excluding bool and subclasses. Values are snapshotted as exact Python integers, ordered y/x detector frequency bins. Zero, opposite, negative and arbitrarily large carriers are valid representations. No floating conversion, principal-period reduction, wrapping or fractional interpolation applies. Expected TypeError/ValueError/OverflowError in integer extraction becomes the corresponding representation error; MemoryError and unrelated exceptions propagate.

Order OTF is one VolumeOrderOtf instance. Validate **all seven public fields**, including directly constructed records and the unused positive row, using exactly the one-record rules of [volume recombination](volume-recombination-v1.md#effective-transfer-records), on the image `(Nz,Ny,Nx)` grid. Values must be plain complex128-width `(3,Nz,Ny,Nx)`; frequencies plain float64-width vectors; either endian, strided and read-only arrays are valid. Spacing, origin, source and canonical physical frequency accuracy/ordering follow those rules. Arbitrary finite complex values, zero rows and arbitrary phase gauges are valid; no E0 normalization, Hermitian/magnitude/support/realizability or provenance claim is inferred. Its opaque source label is retained unchanged. One record requires no cross-orientation spacing comparison.

Snapshot all accepted arrays and calibration fields before phase solving or transforms. Preserve caller contents, strides, writable flags and metadata on success and failure. Concurrent external mutation is outside the promise. No output aliases or mutates calibration; the result stores only immutable scalar metadata.

## Overlap and stored-input estimator

Detector modes use canonical centered signed bins `-floor(K/2)..ceil(K/2)-1` on each dimension K. Let M=Nz*Ny*Nx, and dc,cm be the exact-real least-squares coordinates on the represented phase matrix and converted observations. Use the negative-exponent discrete Fourier transform (DFT), spatial index-zero origin and normalized Fourier coefficients:

```text
D0(j) = sum_r dc(r)*exp(-2*pi*i*j.r/K)/M
Dm(j) = sum_r cm(r)*exp(-2*pi*i*j.r/K)/M
j = (qz, qy+m*ky, qx+m*kx)
Q = {q: q and j both lie in the canonical detector window}
x(q) = Em(j)*D0(q)
y(q) = E0(q)*Dm(j)
gain = z = sum_Q conj(x)*y / sum_Q abs(x)**2
```

The product j.r/K sums z/y/x coordinate fractions. Transfers are the supplied centered values; the selected order's origin phase is already encoded and used once. All geometric pairs participate, including DC and zero-transfer pairs. The overlap count is the exact integer `Nz*max(Ny-abs(m*ky),0)*max(Nx-abs(m*kx),0)`. Carrier multiplication and bounds use exact integer arithmetic. No wrapping, threshold, inferred support mask, transfer division, extra factor of two, ridge, clipping or fitted-gain magnitude limit applies.

For nonzero predictor/response norms define

```text
u = x / norm(x); v = y / norm(y)
c = sum_Q conj(u)*v
z = (norm(y)/norm(x))*c
coherence = abs(c)                 # amplitude correlation, not its square
relative_residual = norm(v-c*u)   # computed directly
```

Do not obtain the residual by subtracting nearly equal squared correlations. The diagnostics use the same geometric samples and cross-weighting as the fit. They are dimensionless fit diagnostics, not confidence probabilities, physical-identifiability certificates or likelihoods. No hidden small-energy/correlation threshold applies.

In a matching finite circular model, `D0(q)=a*E0(q)*S(q)` and `Dm(q+m*k)=a*z_true*Em(q+m*k)*S(q)` give y=z_true*x. The correction cancels the specimen and common positive brightness a where this relation holds. There is no factor of two because the phase separator and order transfers already share harmonic amplitude conventions. Order two returns its own correction; it establishes no unique fundamental phase and need not equal the square of the order-one correction. The discrete periodic identity itself does not require an extended alias-free specimen. Physical sampling of extended/continuous spectra may mix different transfer weights and break it. High coherence alone proves neither alias freedom nor true calibration outside excited overlap modes.

Arbitrary/off-model data receives the stated unweighted complex least-squares projection. Stored-input estimator agreement, unrounded specimen truth, physical calibration and later regularized reconstruction are separate comparisons.

## Distinct information outcomes

| Condition, after the scaled computation below | Outcome |
|---|---|
| Empty geometric Q | no_volume_order_gain_overlap error |
| Nonempty Q, computed predictor norm zero | unidentifiable_volume_order_gain error; gain is unconstrained |
| Nonzero predictor, computed response norm zero | gain=0j, residual=0, coherence=0, status="zero_response" |
| Nonzero predictor/response, computed correlation real and imaginary components both zero | gain=0j, residual=1, coherence=0, status="zero_correlation" |
| Otherwise | finite fitted gain and diagnostics, status="fitted" |

Zero-response residual/coherence are an explicit diagnostic convention: normalization by zero response energy has no mathematical value. Cancellation instead has a nonzero response orthogonal to the predictor and a relative residual of one. Both zero-gain outcomes are valid least-squares fits and identify no phase. Status tests occur before gain restoration; a nonzero correlation whose restored gain underflows to zero retains status="fitted". Signed zero components are equivalent. Error precedence for simultaneous invalid inputs is unspecified.

## Scaled numerical policy and informative accuracy

Use native float64/complex128 numerical processing. The inherited phase separator is SVD-based and retains its rank/accuracy/range policy. Forward spatial transforms use public `numpy.fft.fftn` over all three spatial axes and unchanged band sizes, with normalization equivalent to dividing the negative-exponent sum by M. Separate/batched transforms and equivalent spatial-axis permutations are permitted; call counts/private organization are unspecified. Exact-zero bands may bypass transformation.

Scale each band's finite real/imaginary coordinates by its maximum absolute component **before** any unnormalized transform. Normalize the transform before restoring the band's components, or retain the band scale separately for the fit. A request for norm="forward" alone does not protect an internal raw sum. Use separate component scaling: an overflowing complex magnitude is not input nonfiniteness.

For overlap fitting, independently scale each operand vector E0(q), Em(j), D0(q), Dm(j) by its maximum absolute real/imaginary component; all-zero scales can use one. Form predictor/response products from these bounded operands. Compute stable scaled norms and unit-vector correlation. Retain positive operand/norm scales as mantissa/exponent factors or an equivalent representation. Do not materialize overflowing raw squared norms/cross-products or norm ratios. Restore gain.real and gain.imag separately, including the correlation component in the scaling, so an unnecessary intermediate ratio/magnitude cannot reject safely representable final components. In particular, finite gain components F+iF are not rejected merely because their complex magnitude overflows, where F is maximum float64. Computed zero normalized predictor/response/correlation follows the table above; no exact-real zero classifier at subnormal boundaries is promised. Finite underflow is permitted.

Any nonfinite normalized fitting factor, restored gain component or diagnostic rejects the complete operation with unrepresentable_volume_order_gain. Never clip, saturate, return a partial result or substitute a fallback. Near float64 maximum, computed rounding decides the operational final range boundary. The contract selects no universal success guarantee for every exact-real finite result outside the informative regime.

Let eps=2^-52, q0=2^-1074, B=max(abs(converted images)), A0=max(abs(real/imaginary components of E0 over Q)) and Am=max(abs(real/imaginary components of Em over shifted Q)). For the **exact-real stored-input estimator**, the informative regime is:

- represented phase matrix condition number <=10;
- A0>0, Am>0, norm(x)>=Am*B/8 and norm(y)>=A0*B/8;
- normalized amplitude correlation >=1/4;
- 1e-4<=abs(z)<=10;
- delta=65536*N*M*eps<=2^-10.

These are sufficient success/accuracy conditions, never input rejection cutoffs. Absent genuine dependency/resource failure, otherwise-valid informative inputs must succeed. Require

```text
abs(gain_returned-z_exact) <= delta*max(1,abs(z_exact)) + 8*q0
abs(relative_residual_returned-residual_exact) <= delta
abs(coherence_returned-coherence_exact) <= delta
```

The budgets are dimensionless project choices, not backend theorems, relative/subnormal-retention promises or physical accuracy claims. Evaluate bounds, norms, condition/regime checks and independent oracles in sufficient precision; an underflowed/overflowed observer budget proves nothing. Include tighter justified distinguishing analytic checks for phase sign, order selection, transfer weighting and factor. Outside this regime the estimator remains binding with the stated computed information/range policy, but no uniform digit guarantee applies to near-rank-deficient phases, weak predictor, nearly cancelling correlation or extreme ratios. Diagnostic rounding may slightly exceed the ideal [0,1] interval; no clipping is required. Common positive image scaling that preserves represented ratios leaves the mathematical gain/diagnostics unchanged.

During normalized FFT execution, FloatingPointError, OverflowError, arithmetic RuntimeWarning or nonfinite transform components yields volume_order_gain_transform_failure, even under a caller ignore warning filter. Nonfinite restored band coordinates use the range code. Unrelated FFT RuntimeError/TypeError/ValueError and MemoryError propagate unchanged. Expected input-conversion exceptions follow their representation code and numerical phase errors propagate unchanged. Preserve caller NumPy floating policy and warning filters. Handled conversion/range arithmetic emits no RuntimeWarning; unrelated warning categories are not suppressed. No practical-size, throughput or working-set promise is selected.

## Record, errors and explicit caller composition

Return frozen-binding VolumeOrderGainEstimate with exactly eight public fields: gain (Python complex); relative_residual and coherence (Python floats); overlap_count (Python int); status (the strings above); order (Python int); carrier_bins_yx (Python-int tuple); source (unchanged calibration label). Field rebinding/deletion fails. Direct record construction needs no validation. No corrected phase vector, amplitude/modulation decomposition or calibration copy is returned.

Use existing SimreconError (ValueError) with stable code/message. Message prose and simultaneous-error precedence are unspecified.

| Rejected obligation | Stable code |
|---|---|
| Images/steps, phase rank/solver/range | Inherited volume-separation codes |
| Nonboolean integer order 1 or 2 | invalid_volume_order_gain_order |
| Exact integer y/x carrier representation | invalid_volume_order_gain_carrier |
| Record/type or any calibration field/metadata/grid | invalid_volume_order_gain_otf |
| Empty geometric overlap | no_volume_order_gain_overlap |
| Computed zero predictor norm | unidentifiable_volume_order_gain |
| Handled FFT failure/nonfinite normalized transform | volume_order_gain_transform_failure |
| Nonfinite fitting/restoration/final coordinate | unrepresentable_volume_order_gain |

Explicit caller composition may independently copy all calibration arrays/metadata, multiply **only** values[m] by fit.gain, construct a new VolumeOrderOtf and pass it to reconstruct_volume with the original supplied steps and explicit carrier/gain/ridge/mask/output window. The caller checks multiplied transfer components for finite range. The matching negative correction follows modular conjugation; no stored negative row is added. Preserve E0 and the unselected positive row. Do not also rephase exposures, force an order-two half-angle, infer z2=z1**2, mutate calibration or apply correction automatically. A zero fitted correction can deliberately disable that selected order; this is an explicit caller decision.

## Inventory, ownership and delivery

Group IDs do not count distinct scenarios. A separately maps each outcome/rejection/guarantee and equivalent examples.

| ID | Observable obligations and risks |
|---|---|
| G01 | Exports, required keyword binding, eight fields/types, frozen binding/deletion |
| G02 | Inherited image representation/dtype/shape/source/converted finiteness and permitted alternatives |
| G03 | Inherited step representation/rank/solver/range, represented huge-angle basis and N>5 projection |
| G04 | Order integer validation versus both selected orders, no doubled fundamental steps |
| G05 | Exact carrier containers/scalars/unsigned extrema, no coercion/wrap/magnitude threshold |
| G06 | Complete directly constructed OTF validation including unused row and matching canonical grid |
| G07 | Canonical nonwrapping overlap/count, odd/even Nyquist, singleton, zero/negative/empty carriers |
| G08 | Full complex cross-weighted LS; order selection, sign, normalization, no factor/ridge |
| G09 | Distinct empty/no-predictor/zero-response/zero-correlation outcomes and no hidden cutoff |
| G10 | Off-model fit, direct residual/coherence, no confidence or physical-identification promise |
| G11 | Informative stored-input accuracy and mandatory success; independent observer conditioning |
| G12 | Scaled transform/products/norms/ratio/component restoration, common gain, subnormal/extreme range |
| G13 | Input/calibration snapshots and preservation before numerical work; caller warning/error policy |
| G14 | Expected conversion/FFT failures versus unrelated exceptions/MemoryError; nonfinite final range |
| G15 | Joint observation/step permutation and independent voxel axes; source retained without authentication |
| G16 | Real separator-to-fit-to-recombination composition with independently generated alias-free bands |
| G17 | Explicit selected-row correction, negative conjugation and no double application/coupled phase model |
| G18 | Existing APIs/dependencies/gates preserved; executed usage and actual independent measured comparison |

A owns tests/test_volume_order_gain.py and tests/volume_order_gain_fixture.py. Derive independent sufficient-precision represented-phase LS, finite sums, geometric overlap and complex-regression expectations. Test actual public separator/fit/recombination composition from independently generated alias-free extended bands. Separate specimen truth, stored-data estimator, later ridge bias and deliberately aliased limits. Prerequisite tests need not be duplicated without a composition gap. Fresh B independently recalculates expectations and audits positive alternatives and omissions before an exact frozen checkpoint.

C owns only src/simrecon/volume_order_gain.py, necessary export additions in src/simrecon/__init__.py, docs/usage/volume-order-gain.md, docs/reports/volume-order-gain-comparison.md and .json. No new plotting dependency is needed; a figure may be rendered solely from retained numeric JSON by separately scoped support. C cannot change tests/fixtures/snapshots, gates, workflows, dependencies, skills/policy or unrelated interfaces. Root owns this contract, project/roadmap/task pointer and ignored coordination/setup evidence. Report numerical inputs/expected/actual arrays, hashes, error/regime budgets, both orders, zero outcomes, alias-free correction composition and separate ridge/alias limits. Fresh D assesses exact candidate, actual arrays and composition before current-task implementation narratives; ALL LESSONS payloads remain excluded from every D read/hash.

Route: high-risk scientific/numerical/custom-oracle, fresh native A/B/C/D using gpt-6.1-sol/high conservative guidance, memories/delegation disabled. Cheap locked preflight and proved source-free diagnostics precede blind probes. Missing API is a setup observation, not product-red; initially passing tests are valid. Inherit PROJECT behavior/risk review and complete native global/package/file/platform JSON/HTML statement/branch report integrity, advisory percentages, no selected threshold/exclusions. Canonical clean exact-candidate make verify passes before D/publication. Audit all configured Ubuntu24.04/macOS15 push/PR legs with exact head/base/ordered integration and artifact/source/wheel/measurement identities before the dependent successor. Numeric human limits are not set. Merge/release and unrelated external messages are unauthorized. Preserve every inherited/role/support attempt, correction, failure, exposure and charge; unavailable served attribution/tokens/cost/elapsed remains unknown.

Opened primary references on October 9, 2026: [NumPy DFT signs/normalization](https://numpy.org/doc/stable/reference/routines.fft.html), [fftn spatial axes](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), and [Gustafsson et al., equations 5–9 and overlapping-band fitting](https://scian.cl/scientific-image-analysis/wp-content/uploads/2018/09/2008_Gustafsson_BPJ-1.pdf). These motivate conventions and cross-weighted regression; exact API, zero outcomes, arithmetic domain and budgets above are project choices.
