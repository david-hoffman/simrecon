# Empirical point-bead transfer consumption v1

**Version 1.0. October 11, 2026.** The owner's continuing instruction authorizes coherent scientific slices, implementation, fresh A/B/C/D, full local verification, stacked PRs and successor chats until the simulated raw-specimen/raw-bead objective is complete or a material decision/input blocks it. This additive bridge follows completed raw point-bead PR29 at d1fcb0e80e407598fe7d1178465e293d5c77a726. It consumes the selected finite point-bead model without silently substituting a nonnegative PSF. Actual experimental settings, independent grids and unknown parameter inference remain future contracts.

## Public boundary and declarations

```python
from simrecon import adapt_empirical_volume_response

orders = adapt_empirical_volume_response(
    response,
    carrier_bins=(ky, kx),
    coordinate_offset_yx=(oy, ox),
    phase_reference_shift_rad=delta,
    source="caller calibration/specimen pairing and declarations",
)
# orders is the existing VolumeOrderOtf. Explicitly compose with reconstruct_volume.
```

Only response is positional. All four keywords are required. Ordinary Python binding TypeError applies. One call adapts one explicitly matched orientation/channel/time response. It estimates no phase reference, carrier, coordinate offset, gain, bead size or calibration validity. No batching, raw correction/separation, transform, file I/O, hashing/persistence, new dependency or CLI behavior is added.

The caller declares that calibration and specimen use the same finite grid, spacing, axis directions, instrument response and focal-plane-relative model. Actual phase schedules may differ, but their reference relationship is supplied. Nominal commands cannot stand in for actual phases. The selected point-bead interpretation assumes the observed peak equals the emitter index under the model's unique-zero-peak detection gauge. The operation does not certify that assumption. Arbitrary algebraic records within the domain remain valid inputs; they carry no physical reconstruction promise.

coordinate_offset_yx maps the response's stored index to the fixed illumination coordinates: b_y=origin_zyx[1]+oy and b_x=origin_zyx[2]+ox, in detector samples. Zero is an explicit declaration of aligned origins, never an inferred default. A joint storage roll by t requires offset to change by -t if the illumination coordinates are unchanged. Offsets are not subvoxel localization or specimen translation corrections.

phase_reference_shift_rad=delta is the specimen separation phase-origin offset minus the calibration separation phase-origin offset, in radians. If calibration uses actual physical phases plus alpha_c and specimen uses actual physical phases plus alpha_s, delta=alpha_s-alpha_c. This parameter is supplied metadata/settings; unknown simulator truth must not become pipeline input in the eventual unknown-parameter workflow. Zero explicitly declares a common phase reference. Independent per-step errors are outside this scalar relationship.

## Exact meaning and common normalization

Let E_m be the stored centered calibration response for m=0,+1,+2, native dimensions (Nz,Ny,Nx), observed origin b_hat, and exact integer carrier (ky,kx) in detector bins. Define the exact rational number of cycles

```text
rho = ky*(b_hat_y+oy)/Ny + kx*(b_hat_x+ox)/Nx
F_0(j) = E_0(j)
F_m(j) = E_m(j) * exp(-i*m*(2*pi*rho + delta)), m=1,2.
```

The mathematical expectation uses exact stored binary64 real/imaginary components and delta. Integer products/sums and rho's reduction modulo one are exact before conversion to a bounded angle; huge signed/unsigned integers must not lose their modular meaning. Do not form an overflowing doubled delta before argument reduction. An implementation may form a fundamental phasor and square it for order two. Private organization and trigonometric backend are unspecified.

If rho is an exact integer and converted delta is zero (either sign), all values are copied bit for bit. F0 is always copied bit for bit, including signed zeros and a nonunit DC. Zero side arrays remain exact zero. At other angles signed-zero bit patterns are unspecified.

Do not shift/transform already centered E, take magnitudes, conjugate positive orders, project real, renormalize orders, replace E0, infer Hermitian symmetry, mask support, multiply by voxel volume, restore bead brightness, add a side factor of two, interpolate or compensate finite beads. Retain the common empirical normalization and relative gains/phases. Negative orders continue to satisfy F_-m(j)=conj(F_m((-j) modulo native dimensions)) on all spatial axes, including even Nyquist bins; the adapter stores only 0,+1,+2.

For the selected model, calibration separation gives E_m=exp(i*m*(2*pi*q.r_b-alpha_c))*DFT(h*g_m). Thus the operation gives F_m=exp(-i*m*alpha_s)*DFT(h*g_m), matching specimen separation. This is an explicit forward-model bridge to the existing algebraic VolumeOrderOtf and reconstruct_volume contract. It does not call prepare_volume_order_otfs or interpret signed responses as nonnegative detection PSFs. The bridge itself does not assume a positive E0 or replace a measured zero-order envelope, although the selected physical demonstration retains g0=1. A broader physical model needs its own contract.

The reconstruction caller supplies the same physical integer carriers, actual specimen phases, positive gains, ridge, mask and complete signed output window. Reconstruction uses the supplied transfer exactly once; its existing modular negative-order construction, gain placement, complex Nyquist lift, finite-grid aliasing, range and accuracy limits remain. No absolute throughput, continuous-optics recovery, experimental parity or arbitrary-input physical validity is claimed.

## Input representation and validation

response must be an EmpiricalVolumeResponse instance (ordinary subclasses of that frozen record are permitted). Validate every field even for direct construction and even if carriers/side rows are zero. Its values must be a plain ndarray of complex128 width (16 bytes), either endian, shape (3,Nz,Ny,Nx) with positive spatial sizes; all real/imaginary components finite. Strided, reversed, Fortran and read-only arrays are valid. Bool, complex64/wider complex widths, real arrays, subclasses/masked arrays, nonarrays, wrong rank/order count/empty dimensions and nonfinite values reject.

Each frequency vector is a plain float64-width ndarray, either endian, shape matching its axis, finite, strictly increasing for nonsingleton axes, nonzero off DC and exactly zero at index K//2. For k=-floor(K/2)..ceil(K/2)-1 require abs(f-k/(K*d)) <= 8*eps*abs(k/(K*d))+q, eps=2^-52 and q=2^-1074, evaluated without observer overflow/underflow against converted d. No rewritten/resampled frequencies are returned. Validate representable extreme/singleton grids without rejecting an overflowing intermediate K*d alone.

voxel_size_um is an exact built-in tuple/list of three nonboolean Python/NumPy real integer/floating scalars, converted to finite strictly positive binary64 micrometres. origin_zyx is an exact tuple/list of three nonboolean Python/NumPy integers, each in bounds. Equivalent valid direct records need not come from empirical preparation: arbitrary signed complex arrays, zero rows, zero/nonunit E0 DC and different origins remain allowed. No positivity, mass or physical-realizability check is added.

carrier_bins and coordinate_offset_yx each accept an exact built-in tuple/list of two nonboolean Python/NumPy integer scalars, converted exactly to Python ints. No ndarray container, float coercion, principal-window or intp limit. Negative, zero, repeated-period, huge arbitrary-precision and available unsigned integers are valid. These declarations select phase modulo one only; reconstruction still treats physical carriers nonwrapping and may require a large output grid.

phase_reference_shift_rad is a nonboolean Python/NumPy real integer/floating scalar, converted individually to finite binary64; signed, huge finite, subnormal and signed-zero values are valid. Finite conversion underflow defines the stored problem. Expected conversion TypeError/ValueError/OverflowError rejects. source is a nonblank string, retained unchanged as opaque caller provenance; no parsing or verification.

Snapshot all accepted arrays and metadata before numerical rotation. Preserve input contents, storage layout and writable flags on success and every rejection. Concurrent external mutation is outside the promise. Validate all records/declarations before rotation; snapshots and output allocation can raise ordinary MemoryError.

## Accuracy, range and output

Use native float64/complex128 arithmetic. For every successfully returned side sample let L=abs(Re E)+abs(Im E), computed without observer overflow, and Delta=128*eps*L+16*q. Require abs(F_returned-F_exact)<=Delta. The exact phasor uses mathematical pi and the exact rational carrier phase plus converted delta. These are absolute dimensionless project choices, not backend theorems, physical accuracy or relative/subnormal-retention promises. Order zero and the declared identity case have the exact copy requirement above.

Complex magnitude or intermediate phase/product overflow alone cannot reject safely finite final components. Avoid complex-magnitude scaling and intermediate 2*delta overflow. Apart from genuine dependency/allocation failure, an otherwise valid input must succeed if every side sample satisfies abs(Re F_exact)+Delta<Fmax and abs(Im F_exact)+Delta<Fmax, where Fmax is maximum binary64. This sufficient condition is never an input rejection cutoff; otherwise still attempt computation. A finite input such as Fmax+i*Fmax at identity remains valid despite its overflowing magnitude.

Whole-call final computed component nonfiniteness rejects with unrepresentable_empirical_transfer. This is an operational computed-range boundary, not exact-real overflow classification: roundoff near Fmax can decide acceptance. No saturation, clipping, partial success or fallback. Expected handled conversion/range/underflow emits no arithmetic RuntimeWarning/FloatingPointError under caller NumPy modes. Restore floating/warning modes and suppress no unrelated warning category. Unrelated exceptions and MemoryError propagate unchanged. No new artificial public dependency-failure seam or practical-size/working-set/performance guarantee is selected.

Return the existing frozen-binding VolumeOrderOtf with its seven fields: values, fz_per_um, fy_per_um, fx_per_um, voxel_size_um, origin_zyx, source. Arrays are native complex128/float64 C-contiguous, independently owned and mutable, aliasing no input, one another or another call. Copy frequency values without numeric modification, convert spacing to a Python-float triple, origin to a Python-int triple, and retain the source string. Keep observed origin as provenance; no consumer should apply centering again. This operation adds no new record type or record validation on construction.

Use existing SimreconError with stable code. Prose and simultaneous-invalid precedence are unspecified.

| Obligation | Code |
|---|---|
| Response type or any invalid public field/grid/metadata | invalid_empirical_transfer_response |
| Carrier container/count/noninteger scalar | invalid_empirical_transfer_carrier |
| Coordinate offset container/count/noninteger scalar | invalid_empirical_transfer_coordinate_offset |
| Phase-shift scalar/conversion/finiteness | invalid_empirical_transfer_phase_shift |
| Nonblank source string | invalid_otf_source |
| Nonfinite final computed side component | unrepresentable_empirical_transfer |

## Behavioral inventory and ownership

| ID | Distinct decision/guarantee and concrete risks; examples do not add meaning |
|---|---|
| C01 | Public binding/export and existing seven-field frozen record; no hidden defaults |
| C02 | Full signed-complex rotation and order-two phase; exact rational carrier convention |
| C03 | Same-origin/common-reference identity and zero carrier, preserving signed zeros exactly |
| C04 | Full order-zero bitwise copy and side-zero preservation; no renormalization or extra factor |
| C05 | Physical bead movement compensation versus storage roll plus coordinate-offset correction |
| C06 | Calibration/specimen phase-reference sign and independently varied actual schedules |
| C07 | Existing reconstruction composition and modular negative orders/even Nyquist; supplied gain once |
| C08 | Full response field validation versus legitimate arbitrary algebraic records |
| C09 | Response type/nonarray/subclass/dtype/rank/order-count/empty/nonfinite rejection |
| C10 | Canonical frequency accuracy/order/DC/range; odd/even/anisotropic/singleton and extremes |
| C11 | Spacing container/scalar conversion/finite-positive and origin exact integer/in-bounds rules |
| C12 | Carrier exact integer grammar, signed/unsigned/huge/period multiples and no float loss |
| C13 | Coordinate-offset exact integer grammar and large periodic shifts |
| C14 | Phase-shift real grammar, source/converted finiteness and huge finite/underflow acceptance |
| C15 | Source label rejection and unchanged permitted text |
| C16 | Snapshot/ownership/layout/endian/mutability and input preservation on success/failure |
| C17 | Independent numerical accuracy and safe-success obligation for cancellation/extreme components |
| C18 | Whole-call final range rejection versus identity Fmax+iFmax; caller modes/exception preservation |
| C19 | Existing APIs/dependencies/gates unchanged; no I/O, transforms or physical certificate |
| C20 | Executed raw-bead-to-known-parameter-specimen example with independent signed comparison |

No numeric scenario/review/repair/time/execution limit is set. A derives independent direct phasor/high-precision finite-sum oracles and audits the legitimate positive classes. B independently recalculates expectations and omissions before accepting a frozen checkpoint. Initially passing prerequisites are valid; absent adapter is not product-red. Post-implementation probes remain supplemental.

A owns tests/test_empirical_transfer_adapter.py and optional tests/empirical_transfer_fixture.py only. C owns src/simrecon/_empirical_transfer.py, additive src/simrecon/__init__.py exports and docs/usage/empirical-transfer-consumption.md only, plus ignored examples/evidence. No edits to prerequisite runtime, reviewed tests, fixtures, dependencies, workflow/discovery/coverage/skills/policy. Reuse existing helpers if appropriate without changing their contracts. Coordinator owns this contract, task/PROJECT pointers, packets/accounting and a useful new unique root lesson.

C executes two public examples: direct signed asymmetric algebraic responses with declared offsets/phase shift; and independently generated raw point-bead calibration through public declarations/correction/calibration, this adapter, and known-parameter specimen reconstruction. Include a moved bead and storage-roll/offset control, phase-reference change, zero side transfer, ridge/mask and odd/even grids. Independent generator and sufficient-precision stored-input expectations are evaluator artifacts, never private kernel/true bead input to calibration. This narrow demonstration may supply known phases/carriers as explicitly authorized prerequisites; it does not satisfy the eventual truth-hidden workflow. Retain raw/expected/output arrays, hashes, signed spectra/volumes/errors, derived budgets and gauge/normalization limits. An honest useful figure can illustrate the signed difference/gauge cancellation; it is no oracle.

High-risk scientific/custom-oracle route: fresh native Sol/high A/B/C/D, memories/delegation disabled where supported. A/B use narrow public allowlists and installed source-free diagnostics. C receives exact B-accepted frozen tests; D forms independent assessment after exact clean canonical make verify and before current implementation lessons. Inherit owner-selected advisory percentages with required complete same-run native global/package/owned-file JSON/HTML report integrity, never-imported files and relevant subprocesses, M25 resource export, and separate configured Ubuntu24.04/macOS15 push/PR CI reconciliation. Default full-local gate precedes submission. No gate weakening, Superpowers, legacy execution, private upload, merge or release.

Opened primary convention reference: [NumPy DFT normalization and conjugate symmetry](https://numpy.org/doc/stable/reference/routines.fft.html). API/gauge/range/budget rules here are explicit project choices; public finite-model/recombination contracts are their expectation sources.
