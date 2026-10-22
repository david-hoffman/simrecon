# Known-phase raw point-bead calibration composition v1

**Version 1.0.** October 11, 2026. The owner's continuing roadmap authorization covers this coherent slice through fresh A/B/C/D, implementation, full verification and a stacked pull request (PR). Baseline is completed empirical-response PR28 at a9f4d6b325994cbe96eb29467e1c567fd23d045b. The selected [synthetic model](../models/synthetic-3d-acquisition-v1.md) supplies the point-bead interpretation; actual instrument settings remain unresolved. No invented roadmap stage number is assigned.

## Public boundary

```python
from simrecon import PointBeadCalibration, calibrate_raw_point_bead
result = calibrate_raw_point_bead(
    acquisition, group=group, offset=offset, response=response,
    output_unit=output_unit, phases_rad=actual_phases,
    voxel_size_um=(dz, dy, dx),
)
result.components  # VolumePhaseComponents: observed dc, c1, c2
result.response    # EmpiricalVolumeResponse: full orders 0,+1,+2
result.provenance  # independent caller/applied declarations
```

Only acquisition is positional; every other argument is required keyword-only. Acquisition is a valid public RawAcquisition from [raw declarations](raw-acquisition-declarations-v1.md), with acquisition_kind=sim_beads and explicit orientation, phase, z, y, x axes. Optional channel/time axes retain their declared meaning. Explicit singleton z is valid; absent z is rejected rather than inserted. Manually corrupted record invariants have no newly defined validation outcome. Valid pixel changes preserving R1 invariants remain supported. The record's declaration cannot prove physical bead isolation or experimental correctness.

Group is a plain built-in dict with exactly the names of present time/channel/orientation axes. Each value is a plain built-in int, excluding bool, satisfying 0<=index<declared count. Orientation is always required. A present singleton axis still requires explicit index zero. Absent channel/time must not be supplied. No negative indexing, automatic first-group choice, group averaging, flattening, multi-group batching or inferred group reuse occurs. No group selector is inferred from metadata.

Offset, response and output_unit obey the existing [linear-response contract](linear-response-correction-v1.md), including all scalar/full-map combinations, units, sequential float64 subtraction then division, representation/range/errors and supplied/applied provenance. Full maps have the entire acquisition's canonical shape, not its source shape or the selected group's shape. This composition applies and validates the declared correction over the entire supplied acquisition, then extracts exactly the explicit group; nonselected invalid pixels/maps or arithmetic range failures still reject. This settled full-array behavior follows the existing correction boundary and makes no selected-only memory/performance guarantee. Callers who need correction of only one group may first declare an acquisition containing that group, explicitly retaining required singleton group axes.

After correction, selecting fixed named group indices leaves phase,z,y,x in that order. Pass that four-dimensional array and the supplied actual phases to [known-phase volume separation](volume-phase-separation-v1.md), then pass the returned dc/c1/c2 and supplied spacing to [empirical volume response](empirical-volume-response-v1.md). Those existing represented numerical models, strict rank rule, accuracy budgets, signed domains, frequency semantics, peak/mass decisions, range boundaries and exceptions remain binding. Compose each stage exactly once. No extra intensity normalization, clipping, support cleaning, radial averaging, resampling, conjugation, transfer substitution or finite-bead division is permitted.

Phases_rad is the required plain ndarray `(N,)` of ACTUAL known fundamental phases, in exposure order and radians, with the separator's complete representation/finite/rank domain. It remains distinct from nominal_phases_rad command metadata; absent commands are valid, arbitrary finite commands need not identify the actual model, and commands are never automatically substituted. Spacing accepts the empirical primitive's tuple, list or plain one-dimensional ndarray of length three, ordered `(dz,dy,dx)` in micrometres. Elements use its nonboolean Python/NumPy real integer/floating scalar grammar and complete representation/frequency boundaries. Supplied spacing is authoritative even if R1 sampling is unknown or different; retain both declarations without inferring an override, checking equality or silently borrowing metadata values. This is an explicit calibration sampling declaration, not instrument inference.

True bead location, detection kernel, brightness, axial profiles, carrier and precomputed transfer are not estimator inputs. They may appear only in synthetic generation and independent comparison. Point-bead size compensation is identity. The response retains the observed bead-location and supplied separation phase gauge, all Cartesian signed complex bins and the sole common converted-dc mass normalization. A sole observed peak gives a grid origin, not proof of an isolated physical emitter. Common normalization discards brightness scale and supplies no absolute throughput. The output is not silently interchangeable with a supplied-profile optical transfer function (OTF) or a reconstruction guarantee.

## Result and provenance

Return frozen-binding PointBeadCalibration with exactly three public fields: components (VolumePhaseComponents), response (EmpiricalVolumeResponse), provenance (plain dict). The embedded public records retain their original exact fields/dtypes/shapes/frozen bindings/mutable owned arrays. Outputs alias no caller storage, other calls or one another's arrays. No direct-construction validation or deep immutability promise is added. Metadata is read-only by convention. No raw sample archive, file I/O, hashing/authentication, persistence, streaming, whole-volume memory limit or concurrency guarantee is added.

Provenance has exactly these keys:

- model: `point_bead_identity_v1`.
- group: independent plain dict of supplied explicit indices.
- source_metadata: the complete independent linear-correction source_metadata snapshot, retaining every R1 public field except pixels, original config/metadata/overrides/provenance, kind/axes/group counts, nominal commands and declared sampling/units/IDs.
- linear_response: independent correction provenance with its existing supplied/applied full-map or scalar values and exact unit labels.
- phases_rad: dict with source=`supplied_actual`, supplied=independent C-contiguous plain ndarray retaining original dtype/byte order/shape/numeric values, applied=independent native C-contiguous float64 ndarray of converted angles. Supplied/applied arrays do not alias each other. Numeric coefficient/phase snapshots promise no padding-byte fidelity beyond their existing contracts.
- voxel_size_um: dict with source=`supplied`, supplied=independent original list/tuple retaining supported scalar values/container kind, or an independent C-contiguous plain ndarray retaining original dtype/byte order/shape/numeric values; applied=converted Python-float triple equal to response.voxel_size_um. Supplied ndarray snapshots promise numeric values, not padding-byte fidelity.
- bead_compensation: `identity`.
- response_gauge: `observed_dc_peak_with_supplied_phase_origin`.

All mutable snapshots are independent of caller buffers/containers. Aliasing among separate metadata fields is unspecified, except phase supplied/applied independence. No estimated correction, inferred phases, true origin or inferred optical facts are inserted. Applied origin remains response.origin_zyx. Inputs, declared acquisition metadata, group, coefficients, phases and spacing remain unchanged on success and rejection. Preserve NumPy error mode and unrelated warning categories; inherited handled failures emit no arithmetic RuntimeWarning. Allocation MemoryError and unrelated exceptions propagate; no successful partial result.

## Errors, mathematical assessment and compatibility

Use SimreconError stable codes; prose and simultaneous-invalid precedence are unspecified. New composition errors are invalid_point_bead_acquisition (non-RawAcquisition), invalid_point_bead_kind (valid other acquisition kind), invalid_point_bead_axes (absent explicit z), invalid_point_bead_group (selector type/key/value/count). Existing correction, separation and empirical error codes propagate unchanged, including invalid unit/map/finite/range errors, deficient phases, no positive peak, positive peak tie, nonpositive exact mass and frequency/transform/final-range failures. Python argument-binding TypeError remains. Do not broadly catch exceptions or translate unrelated/allocation failure into a domain error.

The estimator meaning is the exact existing sequence. Independent tests use forward substitution for represented correction, sufficiently precise least-squares derivation on the represented phase matrix, observed peak comparisons and signed direct Fourier sums with exact converted-dc common mass. Production output must not manufacture expectations. For informative phase matrices the inherited separator per-real-coordinate bound is e=8192*N*2^-52*max(abs(converted images))+8*2^-1074. This is numerical acceptance, not physical accuracy. For a stable independent origin/mass comparison with M voxels, exact expected S>0 and M*e0<S, propagate an order sample bound em using `(M*em + abs(E_m)*M*e0)/(S-M*e0)` and add the inherited empirical primitive bound. Peak margin greater than twice e0 establishes unchanged origin. A/B independently justify arithmetic/observer precision and conservative bounds; ambiguous numerical boundaries retain inherited limitations. No new universal composite physical accuracy threshold is selected.

Existing APIs, CLI, dependencies, gates, workflow/discovery/coverage and policy remain unchanged. C executes a public synthetic example through declare_acquisition -> this operation, with unequal N>5 actual phases, independently differing nominal commands, at least two orientations and optional channel/time selection, asymmetric nonseparable kernel and nonzero complex first/second orders. Retain complete inputs/independent expected/output arrays, signed errors/budgets, group/phase/correction/spacing provenance and gauge comparisons in ignored artifacts. Include scalar and full-map corrections. Joint array roll preserves centered response; physical bead translation can rephase side orders; common separation phase-origin shift rephases order m by exp(-i*m*alpha), within inherited represented-phase numerical limits. Explain units, full-array correction, point-model/gauge/intensity-scale/finite-grid limits. No plot is required.

## Scenarios and ownership

| ID | Distinct observable obligation / risk; equivalent examples |
|---|---|
| P01 | Public exports, binding and exact three-field frozen result |
| P02 | Correct declare/correct/select/separate/response order exactly once; independent all-bin signed expectations |
| P03 | Explicit named single-group selection; varying source layouts, orientation/time/channel distinct |
| P04 | All required present group axes including singleton supplied; absent axes forbidden |
| P05 | Selector plain dict/key grammar and complete exact key set |
| P06 | Selector plain int/nonbool and nonnegative in-range; extrema/singleton valid |
| P07 | sim_beads-only kind; nonrecord and other valid kinds rejected |
| P08 | Explicit 3D z required, positive/singleton z accepted |
| P09 | Entire canonical acquisition corrected with full maps; scalar/map combinations and source-shape distinction |
| P10 | Nonselected invalid correction pixels/maps/range still reject; independently declared selected-only positive |
| P11 | Actual angles supplied independently of nominal commands; absent/different/unidentifiable commands valid |
| P12 | Actual phase representation/count/finite/rank errors and legitimate repeated/unequal/overdetermined positives inherited |
| P13 | Supplied spacing authoritative despite unknown/different source sampling; supplied/applied provenance retained |
| P14 | Spacing representation/frequency errors and anisotropic/odd/even/singleton positives inherited |
| P15 | Observed positive sole peak, ties/no positive outcomes; no truth input or extra isolation rule |
| P16 | Exact common positive mass and nonpositive cancellation outcome; full zero-order/relative side gain retained |
| P17 | Identity bead compensation, full signed Cartesian response, no duplicate normalization/support edits |
| P18 | Bead/phase gauge; joint roll versus physical movement and phase-origin shift |
| P19 | Complete source/correction snapshot, supplied/applied phase/spacing/units/group model schema |
| P20 | Caller preservation on success/rejection, independent output/snapshot storage across calls |
| P21 | Inherited supported widths/endian/strides/read-only/signed/zero/subnormal numerical domains |
| P22 | Inherited computed-range/numerical failure translation, allocation/unrelated propagation, no partial result |
| P23 | Caller NumPy error mode/unrelated warnings preserved; handled arithmetic diagnostics suppressed |
| P24 | Public executed usage, independent retained numerical/provenance evidence and unchanged existing interfaces/gates |

Each inherited rejection code remains a separate decision in A's expanded mapping, not hidden by this compact inventory. Equivalent values are examples, not new meaning. No scenario/review/repair/time/cost cap is set. Inherited native percentages are advisory; full installed checks, native report integrity globally/per package/owned file/never-imported/subprocess, same-run M25 and each configured platform/event set remain binding. No coverage union or reporting-only measurement rerun.

A owns tests/test_raw_point_bead_calibration.py and optional tests/raw_point_bead_fixture.py only. C owns src/simrecon/_point_bead_calibration.py, additive exports in src/simrecon/__init__.py and docs/usage/raw-point-bead-calibration.md only. Coordinator owns this contract, docs/tasks/raw-point-bead-calibration.md, factual PROJECT pointer and unique timestamped root lesson. No reviewed test/fixture/infrastructure/policy edits by C. Fresh native Sol/high A/B/C/D with memory/delegation disabled; A/B use narrow public allowlists and source-free diagnostics. D follows exact full-local passing candidate and assesses before current implementation lessons. Stack above codex/empirical-signed-response, reconcile local and Ubuntu24.04/macOS15 push/PR sets separately. No Superpowers, legacy binary execution, private upload, merge/release or unsolicited external messages. Experimental parity requires real target/reference input later; finite-bead compensation requires a separate model, carrier/order factor and stability contract.
