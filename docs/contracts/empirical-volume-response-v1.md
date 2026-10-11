# Empirical bead-referenced volume response v1

**Version 1.0.** Authorized October 10, 2026 by the owner's continuing-roadmap instruction and selected documented synthetic 3D model. This coherent C2 foundation follows observation-derived grid localization. It forms relative signed responses from already separated observations. It does not complete raw empirical calibration, infer instrument settings or add an unknown-phase/carrier estimator.

## Public boundary and meaning

```python
from simrecon import EmpiricalVolumeResponse, prepare_empirical_volume_response

response = prepare_empirical_volume_response(
    dc, c1=c1, c2=c2, voxel_size_um=(dz, dy, dx)
)
```

Only dc is positional; all three keywords are required. Ordinary Python argument-binding TypeError applies. Inputs are the real zero-order and complex positive first/second phase harmonics of one selected orientation/channel/time, in z/y/x order and the same intensity unit. The caller applies its declared correction and known-phase separation explicitly. The primitive accepts no true bead center, supplied detection kernel, axial profiles, lateral carrier, origin override, phase commands or acquisition composition grammar.

Let a0,a1,a2 be independent native float64/complex128 snapshots. Locate the unique positive maximum of a0 with the public locate_bead_peak estimator; its returned index b_hat is the sole origin. Signed dc, unequal multiple peaks, near ties, edge peaks and singleton axes remain allowed under that estimator. Its exact converted-value positive-tie and no-positive errors remain binding. This operation adds no isolation, subvoxel, model-validity or confidence test.

Define S as the **exact real sum of the converted binary64 dc samples**, not an ordinary rounded reduction. Require S>0. Positive peak alone does not imply positive mass: [2,-3] has a unique positive peak but rejects normalization; [2,-1] is valid and can have a transfer larger than one. S may exceed maximum binary64 and may be as small as the minimum positive subnormal. No mass-to-absolute-mass threshold, epsilon floor or sign clipping applies. Exact dyadic accumulation is one possible implementation, not a public method requirement.

For m in {0,1,2}, the mathematical response is

```text
M = Nz*Ny*Nx
R_m[u] = a_m[(u+b_hat) mod (Nz,Ny,Nx)] / S
E_m[k] = sum_u R_m[u] * exp(-2*pi*i*sum_a k_a*u_a/N_a)
```

Center every order with the same observed origin and divide every order by the same S. There is no extra factor of two and no per-order DC, peak or magnitude normalization. Retain signed real/imaginary components, zero side-order DC and zero side rows. Do not take magnitude, conjugate positive orders, project real, clip, radial-average, clean support, crop, pad or interpolate. Zero-order DC is the exact mathematical identity one and is returned exactly as 1+0i. Every other zero-order sample retains the measured combined shape. This DC identity does not set an axial envelope g0 to one or replace the zero-order volume with a supplied PSF.

The selected point-bead model explicitly has g0=1 and identity bead-size compensation. With b_hat=b and S=B, E_m=exp(i*2*pi*m*q·r_b,xy)*DFT(h*g_m). The retained bead lateral phase and declared separation phase gauge are not separately identifiable from these observations. A mathematical common phase-origin change phi'=phi+alpha rephases c_m and E_m by exp(-i*m*alpha); it is not an error. Jointly rolling supplied components preserves the centered response. Physically moving the synthetic bead also rephases side orders through its lateral illumination factor. Do not silently remove that factor or feed generator q/b/h truth into this primitive.

Spatial negative orders satisfy R_-m=conj(R_m), hence E_-m(k)=conj(E_m(-k)) with modular negation on every axis, including even Nyquist bins. Simple array reversal or same-frequency conjugation is generally wrong. Store only 0,+1,+2 in this operation; negative orders follow that documented identity. A later consumer needs a compatible bead-referenced illumination gauge. No direct interchangeability with supplied-profile VolumeOrderOtf or reconstruction guarantee is selected.

The response is dimensionless and loses common measured intensity scale. It identifies neither absolute bead brightness nor detection throughput, nor detection h separately from a measured axial envelope. An arbitrary observed volume is accepted within the numeric domain; that is no evidence for another physical forward model. The selected synthetic model remains phenomenological, finite, periodic and on-grid. General measured envelopes, finite beads, unknown phases/drift, independent grids, full calibration/reconstruction and experimental parity remain separate work.

## Representation and native sampling

Each input is a plain NumPy ndarray of shape (Nz,Ny,Nx), all dimensions positive and all three shapes equal. dc accepts dtype kinds i/u/f; c1/c2 accept i/u/f/c at every available width/byte order. Reject nonarrays/subclasses/masked arrays and bool/object/string/structured/datetime kinds. Read-only, strided/reversed, Fortran, nonsquare and singleton storage are valid. Check every source real/imaginary component for finiteness before conversion; check every converted component too. Conversion rounding and finite underflow define the stored problem. Complex magnitudes that overflow despite finite real/imaginary components are permitted. Preserve input storage on success and rejection; snapshot all three before numerical processing. Concurrent external mutation is outside the promise.

voxel_size_um accepts tuple, list or plain one-dimensional ndarray of length three. Elements are nonboolean Python/NumPy real integer/floating scalars, converted individually to binary64, finite and strictly positive in micrometres (µm). No inferred sampling. Each axis uses increasing signed integer modes -floor(N/2),...,ceil(N/2)-1 and physical frequencies k/(N*d) in cycles/µm, on the native calibration grid. Values have matching full fftshift order on all spatial axes; DC is (Nz//2,Ny//2,Nx//2). Even axes have a negative Nyquist endpoint without a positive duplicate. No leading-order transform.

Each frequency must obey abs(f_returned-f_exact)<=8*eps*abs(f_exact)+q, with eps=2^-52, q=2^-1074 and exact converted d. Zero modes return exact zero. All coordinates must be finite and strictly increasing on nonsingleton axes; nonzero modes must stay nonzero. Avoid intermediate N*d overflow when the final quotient is representable. Singleton axes accept every finite positive converted spacing, including q and maximum float64.

## Numerical execution, accuracy and failure

Use float64/complex128 transform arithmetic. For each order set G_m=max_n(max(abs(Re a_m[n]),abs(Im a_m[n]))), with G_m=1 for an all-zero order and zero imaginary dc. Form r=RN64(a_m/G_m) separately for each real/imaginary component, where RN64 means correctly rounded binary64. The production transform boundary is public numpy.fft.fftn, default/backward forward normalization, on origin-rolled r and all three spatial axes. Separate or batched calls, equivalent spatial-axis permutations, real or zero-imaginary complex dc and zero-side-row bypass are legitimate. Call counts/private organization are unspecified. Do not change transform sizes. Restore each transformed real/imaginary component as the single correctly rounded rational operation y=RN64(T_component*G_m/S); no floating-point S, G_m/S or T_component*G_m intermediate is required. An overflowing mass, complex magnitude or intermediate scale alone cannot reject finite final components.

S is exact; rescaling may use exact dyadic ratios to avoid intermediate overflow/underflow. It need not use a particular private accumulator. Validate the entire scaled FFT result for finiteness/failures, then assign zero-order DC to its exact known identity one before rescaling/range checks, without rescaling that bin. Other computed nonfinite final components reject the whole call. This is an operational computed-range boundary, not an exact-real overflow classifier; roundoff near maximum binary64 may decide acceptance. Do not saturate or return partial success.

For sufficiently precise independent expectations define Lambda_m=sum_n(abs(Re a_m[n])+abs(Im a_m[n]))/S, Delta_m=512*M*eps*Lambda_m+16*M*q. Every successfully returned sample must obey abs(E_returned-E_exact)<=Delta_m. Zero side rows return exact zero. Budgets are absolute dimensionless project acceptance choices, not backend theorems, relative digit guarantees, physical accuracy or promises to preserve all subnormals. Signed cancellation can make Lambda and this budget arbitrarily large; no hidden conditioning rejection applies. Evaluate expectations/budgets without observer overflow/underflow.

Define U_m=DFT(a_m/G_m) with exact quotients of stored inputs, distinct from the rounded FFT input r. The finite scaled transform T must obey abs(T-U_m)<=128*M*eps*L_m+4*M*q, where L_m=sum_n(abs(Re a_m[n])+abs(Im a_m[n]))/G_m. Input division rounding is included in this project budget. Apart from an actual dependency/allocation failure, inputs with abs(Re E_exact)+Delta_m<F and abs(Im E_exact)+Delta_m<F at every output sample must succeed, where F is maximum binary64. This sufficient condition is not exhaustive: otherwise the operation still attempts the computation and cannot reject merely because the inequality fails. It is not an input cutoff or exact classification claim at the boundary.

During transforms, FloatingPointError, OverflowError, arithmetic RuntimeWarning or nonfinite computed scaled transform values translate to empirical_response_transform_failure. MemoryError and unrelated transform exceptions including RuntimeError/TypeError/ValueError propagate unchanged. Expected conversion TypeError/ValueError/OverflowError translate only in conversion. Handled conversion/range/underflow emits no arithmetic RuntimeWarning/FloatingPointError under caller NumPy modes; restore modes and suppress no unrelated warning category. No successful partial result or fallback. Ordinary allocation MemoryError/unrelated exceptions elsewhere propagate. The operation owns full snapshots/output/scratch and exact-sum bookkeeping; no streaming, working-set, practical-size or performance guarantee is selected.

## Result and errors

Return frozen-binding EmpiricalVolumeResponse with exactly six public fields:

- values: independent owned mutable native complex128 C-contiguous ndarray (3,Nz,Ny,Nx), fixed order 0,+1,+2.
- fz_per_um, fy_per_um, fx_per_um: independent owned mutable native float64 C-contiguous one-dimensional arrays of matching lengths.
- voxel_size_um: converted Python-float triple.
- origin_zyx: observed Python-int triple.

All four arrays alias neither input, one another nor another call. Slices of values may share that array's storage. Contents remain mutable; bindings are frozen; direct record construction needs no validation. No mass, source-label or throughput field is returned. Caller provenance records observation/correction/phase identities, spacing, chosen model, returned origin and software externally. This operation performs no file I/O, hashing/authentication or persistence.

Use existing SimreconError with stable code; prose and simultaneous-invalid precedence unspecified.

| Rejected obligation | Code |
|---|---|
| Any component not plain ndarray | invalid_empirical_response_array |
| Unsupported dc or side-order kind | invalid_empirical_response_dtype |
| Nonpositive/wrong-rank or unequal component shapes | invalid_empirical_response_shape |
| Source/converted nonfinite components or expected conversion failure | nonfinite_empirical_response_array |
| No positive maximum / exact positive dc tie | no_positive_bead_peak / ambiguous_bead_peak |
| Exact converted dc mass <=0 | nonpositive_empirical_response_mass |
| Invalid finite-positive spacing triple | invalid_otf_voxel_size |
| Nonfinite/collapsed/unordered final frequencies | unrepresentable_otf_frequencies |
| Handled transform failure/nonfinite scaled T | empirical_response_transform_failure |
| Nonfinite final rescaled component | unrepresentable_empirical_response |

Existing APIs/dependencies/CLI/workflows/discovery/coverage/policy remain unchanged. Reuse public locator and existing frequency behavior within approved boundaries; no supplied-profile preparation substitution.

## Scenarios, ownership and evidence

| ID | Distinct obligation / concrete risk; equivalent examples |
|---|---|
| E01 | Public binding/exports and exact six-field frozen record with owned native arrays |
| E02 | Signed full-complex three-order direct sum and common exact mass; asymmetric nonseparable odd/even grids |
| E03 | Observation-derived sole positive peak, no truth/origin input; signed dc, secondary peaks, near ties |
| E04 | No positive peak and exact positive ties retain locator errors; lower ties remain valid |
| E05 | Exact positive mass after cancellation, nonpositive mass rejection despite positive peak |
| E06 | Common mass may exceed F or equal q; no intermediate mass/gain/magnitude rejection |
| E07 | Same periodic centering for all orders; joint roll invariance, boundary/corner/singleton origin |
| E08 | Preserve relative complex gain, side zero DC/zero rows and full zero-order shape; exact unit zero DC |
| E09 | Retain bead/phase gauge; physical bead movement differs from joint array translation |
| E10 | Modular negative-order identity with even Nyquist, no reversal/same-bin conjugate mistake |
| E11 | Native signed physical frequency axes/fftshift; anisotropic spacing, odd/even/singleton |
| E12 | All allowed widths/endian/storage and converted-value meaning; wider native capability explicitly reported |
| E13 | Nonarray/subclass rejection with paired plain ndarray positives |
| E14 | Kind restrictions differ for dc versus c1/c2; real sides valid, complex dc invalid |
| E15 | Rank/empty/mismatched shapes rejected; equal singleton/nonsquare accepted |
| E16 | Source and converted component finiteness; finite complex component extrema valid |
| E17 | Spacing container/scalar grammar, finite-positive conversion versus valid extrema |
| E18 | Final frequency range/order/collapse, avoid intermediate period overflow |
| E19 | Signed-cancellation/scaled transform accuracy and safely finite output success; real/imag independent ranges |
| E20 | Whole-call final computed-range rejection; explicit boundary uncertainty |
| E21 | Public transform arithmetic/nonfinite failure translation versus unrelated/allocation propagation |
| E22 | Snapshots/input preservation/result ownership, caller NumPy modes and unrelated warnings preserved |
| E23 | Corrected declared known-phase synthetic point-bead composition; commanded phases remain distinct |
| E24 | Existing compatibility/gates; executed public usage and independent measured response/gauge evidence |

No numeric scenario/review/repair/execution limit is set. A independently maps decisions/examples/risks and derives sufficiently precise direct-sum or exact-root oracles; do not transform product output as an oracle. B independently recalculates and audits legitimate positives/omissions before C. Unsupported portable failure/storage capabilities are explicit gaps, never skips/xfails or fabricated internal states. Accuracy constants and operational boundaries are this contract's choices.

A owns tests/test_empirical_volume_response.py and optional tests/empirical_response_fixture.py only. C owns src/simrecon/_empirical_response.py, additive src/simrecon/__init__.py exports and docs/usage/empirical-volume-response.md only. C executes two public examples: signed asymmetric separated arrays and a declared count/electron synthetic point bead through R1/R2/known-phase separation/this primitive. Independently derive expected arrays and retain inputs/expected/outputs, identities, signed errors/budgets, observed origin and phase-gauge evidence in ignored artifacts. True b/h/q/B remain generator/comparison truth, never primitive inputs. Explain model/finite-grid/throughput/phase limitations. Coordinator owns contract, task/PROJECT pointers, packets/accounting and useful unique root lesson.

High-risk scientific/custom-oracle route: fresh native Sol/high A/B/C/D, optional memory/delegation disabled; A/B narrow public allowlists and installed source-free diagnostics; frozen B-accepted tests before restricted C. D assesses after exact clean canonical make verify and before implementation lessons. Inherit owner-selected advisory percentages and required complete native global/package/owned-file JSON/HTML integrity, never-imported files and relevant subprocesses. Full-local exact gate precedes stacked PR; configured Ubuntu24.04/macOS15 push/PR CI are separately reconciled. No gate/dependency/policy edits, Superpowers, legacy execution, private upload, merge or release.

Opened primary references: [NumPy DFT sign/normalization/symmetry](https://numpy.org/doc/stable/reference/routines.fft.html), [fftn](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftn.html), [native frequency bins](https://numpy.org/doc/stable/reference/generated/numpy.fft.fftfreq.html). The finite model and estimator/representation/gauge/range/accuracy policies above are explicit project choices.
