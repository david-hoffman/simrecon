# Empirical transfer at exact shared native nodes

`adapt_empirical_volume_response_shared_nodes` selects stored calibration
responses at the specimen's exact physical frequency nodes and applies a
declared phase gauge. One call handles one orientation, channel and time pairing.
It returns `SharedNodeVolumeTransfer`; pass its `.orders` to
`reconstruct_volume`.

Physical use requires the caller to assume that the paired effective transfers
agree at the selected nodes after gauge correction. Both acquisitions must use
the same axis directions, z/y/x order and focal-plane-relative model. The
adapter checks geometry and declarations. It cannot establish this physical
assumption, axial illumination-profile equality or experimental validity.

## Explicit composition

Start with a public `EmpiricalVolumeResponse`, for example the actual `.response`
returned by `calibrate_raw_point_bead`. Calibration uses the raw observation,
declared camera correction and actual phase schedule. True bead location,
brightness, detection kernel and a desired transfer are not estimator inputs.

The following fragment assumes `calibration_acquisition` and
`specimen_acquisition` have already been created with `declare_acquisition`, with
explicit orientation/phase/z/y/x axes and one selected orientation. The phase
vectors contain actual known phases in exposure order; nominal command metadata
does not supply phase truth. The illustrated camera relation is
`raw = 10 counts + (2 counts/electron) * signal`.

```python
import numpy as np
from simrecon import (
    adapt_empirical_volume_response_shared_nodes,
    calibrate_raw_point_bead,
    correct_linear_response,
    reconstruct_volume,
)

# Source shape (21, 27, 33), source spacing in micrometres.
calibrated = calibrate_raw_point_bead(
    calibration_acquisition,
    group={"orientation": 0},
    offset=10,
    response=2,
    output_unit="electrons",
    phases_rad=actual_calibration_phases + 0.25,
    voxel_size_um=(0.125, 0.0625, 0.03125),
)
adapted = adapt_empirical_volume_response_shared_nodes(
    calibrated.response,
    target_shape_zyx=(7, 9, 11),
    target_voxel_size_um=(0.375, 0.1875, 0.09375),
    calibration_carrier_bins=(0, 1),
    specimen_carrier_bins=(0, 1),
    coordinate_offset_yx=(2, -3),
    phase_reference_shift_rad=-0.375,  # -0.125 - 0.25 radians
    source="explicit calibration/specimen orientation 0 pairing",
)
corrected = correct_linear_response(
    specimen_acquisition, offset=10, response=2, output_unit="electrons"
)
result = reconstruct_volume(
    corrected.data,
    order_otfs=(adapted.orders,),
    phases_rad=(actual_specimen_phases - 0.125)[None, :],
    carriers_bins=np.array([[0, 1]]),
    gains=np.array([1.0]),
    regularization=0.25,
    output_shape_yx=(9, 15),
    apodization=np.ones((7, 9, 15)),
)
```

These are explicit example declarations, not defaults or evidence that an
arbitrary pair has matching transfers. The source and target periods both equal
`(2.625, 1.6875, 1.03125)` µm: for example `21 * 0.125 = 7 * 0.375` µm.
Their odd canonical windows share the requested nodes and commute with
modular negation. Reconstruction applies the declared gain once and retains its
own output-window, ridge, mask and arithmetic-range rules. Ridge can bias the
result even with an exactly paired forward model. Adapter acceptance alone
guarantees neither reconstruction acceptance nor specimen recovery.

## Exact geometry and signed gauge

Dimensions and spacings use z/y/x order. Spacings are individually converted to
binary64 micrometres (µm), then treated as exact represented rationals. For one
axis with source dimension/spacing `Nc, dc` and target `Ns, ds`, canonical target
modes run from `-floor(Ns/2)` through `ceil(Ns/2)-1`. Each mode `j` must map to
an integer source mode `i = j*(Nc*dc)/(Ns*ds)` inside the source window. Source
array index is `i + floor(Nc/2)`. Rounded coordinate equality or tolerance cannot
establish a shared node. A singleton target axis requests only source zero and
permits any valid positive spacing.

The map must commute with modular negation on every axis, including the single
fixed negative Nyquist node of an even dimension. Source 12 to target 4 with
identical spacing maps `(-2,-1,0,1)` to `(-6,-3,0,3)` and qualifies. Source 9 to
target 4 with equal periods has complete nodes but fails negation at target
mode `-2`. Missing nodes and noncommuting maps reject regardless of optical
zeros or downstream masks. Both lateral carriers must separately satisfy exact
physical equality `kc/(Nc*dc) = ks/(Ns*ds)`. Huge integers retain their
nonwrapping meaning.

`coordinate_offset_yx` is measured in **source calibration samples**. Together
with the observed source peak it determines common lateral illumination
coordinates. A source storage roll by `t` needs offset `o-t` to preserve them.
This offset does not correct specimen translation or specify a target bead.
Target index zero declares common coordinate zero.

`phase_reference_shift_rad` is the specimen-minus-calibration separation phase
origin, in radians. With supplied phases physical-plus-`alpha_c` and
physical-plus-`alpha_s`, use `delta = alpha_s-alpha_c`. Actual schedules may
differ. Independent per-step phase errors cannot be represented by this scalar.
For source origin `(bz,by,bx)` and source carriers `(ky,kx)`, the selected orders
obey

```text
rho = ky*(by+oy)/Ny_c + kx*(bx+ox)/Nx_c
F_0(j) = E_0(P(j))
F_m(j) = E_m(P(j)) * exp(-i*m*(2*pi*rho+delta)), m=1,2.
```

Integer arithmetic and rational phase reduction are exact before bounded-angle
rotation. Huge finite phase shifts remain valid without forming overflowing
`2*delta`. Order zero copies real/imaginary component bits at every gauge.
Integral `rho` and either signed-zero `delta` copy all selected component bits.
Arbitrary finite algebraic/non-Hermitian values, zero rows and nonunit or zero
zero-order DC remain valid. Negative orders use modular frequency negation and
complex conjugation in the existing reconstruction consumer.

## Validation, ownership and provenance

Only `response` is positional; all seven keywords are required. The complete
source record is validated and snapshotted before selection and rotation.
Source values must be plain complex128-width arrays of shape `(3,Nz,Ny,Nx)`;
frequency vectors must be plain float64-width arrays at matching lengths.
Either endian, read-only, strided, reversed and Fortran storage are accepted.
Components must be finite. Coordinates must increase, be nonzero off DC and
have exact zero at centered DC. Their tolerance is
`8*2^-52*abs(k/(N*d)) + 2^-1074` against the exact rational ideal frequency,
in cycles/µm. This validity tolerance does not define node matching.

Metadata containers must be exact built-in tuples/lists of the declared lengths.
Source origin and both carriers/offset use nonboolean Python/NumPy integer
scalars. Target dimensions are positive integers representable by `numpy.intp`.
Spacing and phase accept nonboolean Python/NumPy real integer/floating scalars;
converted spacings must be finite positive and phase finite. Conversion
underflow defines the represented problem. `source` is a nonblank opaque string,
retained unchanged. Expected conversion errors translate at their corresponding
boundary; allocation failures and unrelated exceptions propagate.

`adapted.orders` has mutable, independent, native C-contiguous arrays:
complex128 `values` in order 0,+1,+2 and three float64 frequency vectors.
Mapped source frequency components are copied bit for bit, including DC signed
zero and valid extreme finite coordinates. Exact ideal-node equality carries
their source tolerance to the target. No frequency vector is regenerated.
Target spacing is the converted Python-float triple; `origin_zyx` is `(0,0,0)`
because these transfers are already centered. All four arrays own separate
storage and alias no inputs, other outputs or other calls.

The frozen-binding wrapper has exactly `orders` and `provenance`. Its mutable
plain provenance dictionary is read-only by convention and has exactly these
nine keys:

| Key | Meaning |
|---|---|
| `sampling` | `exact_shared_native_nodes_v1` |
| `source_shape_zyx` | Source Python-int spatial triple |
| `source_voxel_size_um` | Converted source Python-float triple |
| `source_origin_zyx` | Observed source Python-int triple, unreduced even outside target bounds |
| `source_indices_zyx` | Three tuples of source array indices in target canonical order |
| `calibration_carrier_bins` | Exact source y/x Python-int tuple |
| `specimen_carrier_bins` | Exact target y/x Python-int tuple |
| `coordinate_offset_yx` | Exact source-sample y/x Python-int tuple |
| `phase_reference_shift_rad` | Converted finite Python float, including signed zero |

Provenance aliases no caller containers or other calls. Bindings are frozen;
array/dictionary contents remain mutable. Direct construction adds no validation
or deep immutability. Keep upstream raw identities, correction and actual-phase
provenance externally; this record does not authenticate them.

## Errors and numerical limits

`SimreconError.code` identifies the rejected obligation. Message prose and
simultaneous-invalid precedence are unspecified.

| Code | Rejected obligation |
|---|---|
| `invalid_empirical_transfer_response` | Response type or any source field |
| `invalid_empirical_transfer_target_shape` | Target shape grammar, positivity or native index extent |
| `invalid_empirical_transfer_target_voxel_size` | Target spacing grammar, conversion, finiteness or positivity |
| `invalid_empirical_transfer_carrier` | Either carrier's container/scalar grammar |
| `invalid_empirical_transfer_coordinate_offset` | Offset container/scalar grammar |
| `invalid_empirical_transfer_phase_shift` | Phase scalar, conversion or finiteness |
| `invalid_otf_source` | Nonblank source string |
| `incomplete_empirical_transfer_coverage` | Any requested node missing |
| `incompatible_empirical_transfer_negation` | Map fails modular negation commutation |
| `mismatched_empirical_transfer_carrier` | Either physical carrier differs |
| `unrepresentable_empirical_transfer` | Selected computed final side component nonfinite |

All source samples are validated, but only selected side samples rotate and
undergo computed-range checks. An unselected finite sample that would overflow
under rotation cannot cause rejection. No clipping or partial result occurs.
NumPy floating modes, warning policies and caller storage are preserved;
handled conversion/range/underflow emits no arithmetic diagnostic and unrelated
warning categories remain observable. Concurrent external mutation is outside
the guarantee. Full snapshots and ordinary allocation failures are permitted;
there is no working-set, performance or practical-size promise.

Lookup adds zero interpolation error. For each selected side value the absolute
dimensionless rotation allowance is
`Delta = 128*2^-52*(abs(Re E)+abs(Im E)) + 16*2^-1074`. Apart from genuine
dependency/allocation failure, success is required when every exact final
component satisfies `abs(component)+Delta < maximum_binary64`. This is a
sufficient-success condition, not a rejection cutoff. Identity accepts finite
extreme components even when complex magnitude overflows. Otherwise the
adapter attempts rotation and rejects computed nonfiniteness; roundoff near
maximum binary64 can affect the outcome.

Calibration estimation error, rotation allowance, physical pairing/model error
and reconstruction error or regularization bias are separate. No universal
physical accuracy follows. Existing same-grid consumption remains available.
This operation adds no interpolation, transforms, resampling, normalization,
voxel-volume/site-count gain, brightness fitting, hidden conjugation, finite-bead
compensation, unknown-parameter workflow, persistence or experimental-parity
claim.
