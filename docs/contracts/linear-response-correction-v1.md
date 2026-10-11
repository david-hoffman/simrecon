# Declared linear-response correction v1

**Version 1.0.** Authorized partial R2 foundation under the owner's October 10, 2026 continuing-roadmap instruction. Intake selects this explicit supplied model after report-only scientific advice. This does not resolve actual instrument O4/S4, effective reference settings or target calibration. [Task](../tasks/linear-response-correction.md). Prerequisite: completed [R1 declarations](raw-acquisition-declarations-v1.md) at PR24.

## Scientific meaning and public boundary

Export from simrecon:

```python
correct_linear_response(acquisition, *, offset, response, output_unit) -> LinearResponseCorrection
```

The caller declares the complete samplewise forward relation

```text
raw = offset + response * signal
signal = (raw - offset) / response
```

Raw and offset use the declared input intensity unit Uraw. Response means Uraw/Usignal and is strictly positive; it is dimensionless only when the unit labels denote the same unit. Output_unit declares Usignal. Unit labels are opaque strings: the library verifies their presence, not dimensional consistency, calibration, spelling or the truth of the caller's physical model. No automatic unit/exposure conversion or coefficient interpretation is performed.

For raw=110 count, offset=10 count and response=2 count/electron, signal=(110-10)/2=50 electrons. Substitution gives 10+2*50=110 count. This algebra is the independent expectation source; no reference-C output selects it.

This is pure in-memory arithmetic, returning one complete value or raising. There is no I/O, estimation, clipping, background estimation, exposure normalization, bleaching correction, saturation detection, bad-pixel repair, operation grammar or automatic composition. Offsets/responses must be explicitly supplied, including for identity. No selected actual camera or specimen/bead sequence is implied. Saturated/defective samples may be numerically finite; the operation cannot determine whether their physical measurement follows the declared relation. No input dtype maximum is treated as saturation. Physical interpretation remains conditional on model applicability; later invalid-pixel detection/treatment needs a separate contract.

## Input, coefficient alignment and units

Acquisition must be a RawAcquisition record satisfying the public R1 output invariants. A type mismatch is rejected. Manually corrupted metadata/schema outside those invariants has no defined validation outcome; no nested arbitrary-record validation contract is added. Valid sample-value changes that preserve those invariants are acceptable. No promise covers concurrent external mutation. All three R1 kinds and valid ranks/axes are supported. Input data can use any R1 i/u/f width/byte order, striding and writable flag, but this operation additionally requires finite samples representable as finite binary64 after conversion. Signed raw samples are valid. R1's preservation of nonfinite pixels remains unchanged.

Offset and response each independently are either a plain built-in int/float excluding bool, or a plain NumPy ndarray of dtype kind i/u/f. NumPy scalars, ndarray subclasses, masked arrays, lists, complex/bool/object/string/structured/datetime values are outside this boundary. Array coefficients must have exactly acquisition.data.shape, with coordinates in acquisition.axes canonical order. No array broadcasting, named-axis inference or reuse across time/channel/orientation/phase/z is implicit. A scalar is explicitly constant over every sample. All four scalar/array combinations are valid. Zero-dimensional coefficient arrays do not substitute for scalars because a supported acquisition has y/x dimensions.

Normalize pixels and both coefficients once to native binary64. Offset may be positive, zero or negative, including signed zero. Response must be finite and strictly positive after normalization. Any positive represented response, including subnormals, is admissible; no epsilon floor is selected. Nonfinite original coefficients/pixels or conversions yielding infinity are invalid. A response rounded to zero is invalid_response; ordinary pixel/offset values rounded to zero are valid conversion results. Huge built-in integer conversion failure is its corresponding coefficient error. Conversion may lose integer precision or wider-float precision; this arithmetic operation promises no raw pixel bit fidelity.

Acquisition.intensity_unit and output_unit must be nonempty strings. Preserve exact text; whitespace-only strings remain opaque nonempty labels as in R1. None/empty/nonstrings are rejected. Different declared labels are allowed because response supplies the declared relation; no label conversion is inferred.

## Arithmetic representation and range

The defined numerical operation is sequential native binary64 arithmetic: first subtract normalized offset from normalized raw, materialize the binary64 numerator, then divide that numerator by normalized response to a binary64 result. It is not an exact-real fused expression or a promise to recover a finite quotient when the specified subtraction intermediate overflows. If any numerator or final output is nonfinite, the whole call raises linear_response_range and returns no successful partial result.

Subnormal results and underflow to signed zero are accepted; neither causes a warning/error or a positivity clip. Signed finite results, including negative corrected samples, remain signed. Normal rounding/cancellation and loss from input conversion are part of this finite representation, not a separate physical accuracy guarantee. Preserve sign of a nonzero negative quotient that underflows to zero. Finite exact-representable examples support exact assertions; test authors independently justify tolerances for other represented examples from these two operations and input conversion, without inventing an instrument accuracy target.

NumPy documents elementwise [subtraction](https://numpy.org/doc/stable/reference/generated/numpy.subtract.html), [division](https://numpy.org/doc/stable/reference/generated/numpy.divide.html) and temporary [error-state restoration](https://numpy.org/doc/stable/reference/generated/numpy.errstate.html); the explicit supported-domain/range rules here are the task contract rather than defaults inherited from those functions.

Preserve caller NumPy error settings. Handle expected conversion/range/underflow without arithmetic RuntimeWarning or FloatingPointError regardless of those settings. Suppress no unrelated warning categories. Allocation MemoryError and unrelated exceptions propagate unchanged. Input acquisition, metadata and coefficients remain unchanged on success and rejection.

## Result and provenance

LinearResponseCorrection exposes:

- data: independently owned, C-contiguous plain float64 ndarray, same shape/canonical coordinates as input, holding the sequential result.
- axes: tuple equal to acquisition.axes.
- input_unit and output_unit: exact declared strings.
- source_metadata: independent dict snapshot of every public R1 field except data: axes, source_axes, source_shape, acquisition_kind, sampling_um, wavelengths_nm, nominal_phases_rad, nominal_phase_axes, intensity_unit, acquisition_id, calibration_id, original_config, original_metadata and provenance. Nominal phase commands retain their array dtype/shape/values and are not interpreted as known phase truth. Raw sample pixels are not archived in this metadata record; preserve the original acquisition when they are needed.
- provenance: independent dict with model="linear_response_v1", equation="raw=offset+response*signal", input_unit, output_unit, offset and response. Each coefficient entry is a dict with source="supplied", supplied=an independent original-value snapshot and applied=an independent normalized coefficient. No estimated value is created.

For a scalar supplied coefficient, supplied preserves built-in int versus float and the original value; applied is a built-in binary64 float. For an array supplied coefficient, supplied is an owned C-contiguous array preserving shape, dtype/byte order and numeric values, including signed zero; applied is an owned C-contiguous native float64 array. Per-element padding-byte identity is not promised for coefficient snapshots. Output mutable storage does not alias caller storage. Metadata/provenance snapshots retain nested built-in container types/bytes/nonfinite opaque metadata and nominal-command values from R1; they are not newly validated or interpreted. Read-only by convention, mutable buffers; no deep-immutability promise. Aliasing between separate fields within the returned value is unspecified, but no returned mutable storage aliases caller storage.

The operation owns a complete output plus coefficient/metadata snapshots and ordinary arithmetic scratch. No whole-volume memory limit or streaming promise is selected. Missing allocation/non-arithmetic failures cannot yield a success.

## Errors and compatibility

Use SimreconError with stable codes below. Exact prose and simultaneous-error precedence are unspecified. Missing required keyword arguments or unknown keywords retain ordinary Python argument-binding TypeError.

| Obligation | Code |
|---|---|
| Input is not RawAcquisition | invalid_linear_response_acquisition |
| Nonfinite raw sample or raw-to-binary64 conversion not finite | invalid_linear_response_data |
| Unsupported offset form/dtype, nonfinite offset, offset conversion failure | invalid_linear_response_offset |
| Unsupported response form/dtype, nonfinite/nonpositive normalized response, conversion failure | invalid_linear_response_response |
| Offset or response array shape differs from canonical sample shape | invalid_linear_response_shape |
| Missing/invalid input intensity label or output label | invalid_linear_response_unit |
| Nonfinite subtraction numerator or divided result | linear_response_range |

No new change to declare_acquisition, conversion/viewing, separation, PSF preparation, reconstruction, dependency lock, checks or policy. R1 remains bit-preserving for the original raw input. Caller-selected corrected arrays may be passed to existing public numeric operations when those operations' separate shapes/phase/positivity requirements hold. In particular signed corrected data does not waive supplied-PSF positivity requirements. The usage guide must execute a count/electron example and an asymmetric full-map/known-phase separation composition with independently declared expected coefficients; nominal commands are not automatically treated as truth.

## Scenario inventory and ownership

All scenarios describe distinct meaning; equivalent values are examples, not new rules. No scenario/review/repair budget cap is set.

| ID | Observable obligation | Independent expectation / examples |
|---|---|---|
| L01 | Explicit scalar model, declared input/output roles, correct subtraction then division | Forward substitution; count/electron example and a distinguishing wrong-order control |
| L02 | Full-map canonical coordinate correspondence | Independently labeled nonsquare orientation/phase/z/y/x values |
| L03 | Four scalar/map combinations; explicitly shared scalars | Same forward relation with separately chosen arrays/scalars |
| L04 | Identity requires explicit offset=0/response=1 and unit | Float64 conversion of supported raw values |
| L05 | Signed raw, signed corrected values and zero are permitted | Negative/positive offsets and exact negative signals |
| L06 | All R1 kinds/ranks/axes supported; channel/time never flattened | Public declaration composition and shape/axis identity |
| L07 | Supported raw storage widths/orders/strides become owned float64 | Independent represented scalar conversions |
| L08 | Supplied versus applied coefficient values/dtypes preserved independently | Huge precisely represented scalar conversion; endian/read-only/strided maps |
| L09 | Nonrecord acquisition rejected | Stable acquisition error |
| L10 | Nonfinite or out-of-binary64-range raw rejected | NaN/infinity and wider native storage where available |
| L11 | Unsupported coefficient forms/dtypes rejected | Booleans, lists, NumPy scalars, subclasses and unsupported dtype families |
| L12 | Any nonscalar array shape mismatch rejected; no implicit broadcast | Broadcastable y/x-only, singleton, zero-dimensional and wrong-coordinate shape alternatives |
| L13 | Offset finite after conversion, signed finite/zero allowed | Positive/negative/zero versus nonfinite or huge-int conversion |
| L14 | Response finite and strictly positive after conversion | Small positive/subnormal versus negative, ±0, nonfinite or conversion-to-zero |
| L15 | Both nonempty opaque unit labels required; same/different labels valid | Missing input unit, wrong label types, empty and whitespace labels |
| L16 | Normalization/rounding semantics are explicit | int64 values above 2^53 and wider floats where available |
| L17 | Subtraction overflow rejects whole call even with mathematically finite quotient | Opposite binary64 extremes and response>1 |
| L18 | Quotient overflow rejects whole call | Finite numerator divided by tiny positive response |
| L19 | Subnormals and signed underflow accepted without epsilon floor | Small positive response yielding finite result; negative underflow-to-zero |
| L20 | Caller NumPy modes preserved; handled arithmetic emits no RuntimeWarning/FloatingPointError | Nondefault raise/warn/call/print/log/ignore settings; preserve unrelated warning behavior when safely reachable |
| L21 | No caller mutation; result/coefficient/metadata ownership on success/error | Snapshot and mutate outputs/inputs independently |
| L22 | Every named R1 metadata field retained as independent source snapshot | Bytes, nested container types, overrides/provenance and nonfinite opaque metadata |
| L23 | Allocation/unrelated exceptions propagate; no partial success | Safe public production-boundary injection if available; disclose missing portable evidence |
| L24 | Corrected-array composition with existing known-phase separator | Independent DC/harmonic forward samples; caller-selected true phases |
| L25 | Executed usage explains units/model/range/limits and partial R2 status | Two actual public examples and independent mathematical comparison |
| L26 | Finite dtype extrema/flagged samples are arithmetic inputs, not inferred saturation repair | Dtype max and opaque bad-pixel/saturation flags; metadata preserved |
| L27 | Ordinary Python binding errors retained | Omitted required/unknown keyword |
| L28 | Supplied/applied provenance contains no estimate or inferred defaults | Exact public result schema and explicit original/applied values |

A owns tests/test_linear_response_correction.py and optional tests/linear_response_fixture.py only. C owns src/simrecon/_linear_response.py, additive src/simrecon/__init__.py exports and docs/usage/linear-response-correction.md only. Coordinator owns this contract, docs/tasks/linear-response-correction.md and a factual additive docs/PROJECT.md pointer. No A/C tests, source, workflows, dependencies, discovery, coverage, policy or unrelated interfaces outside named scope.

Fresh native Sol/high A/B/C/D; optional memory/delegation disabled where supported. A/B read only narrow public allowlists and use the existing source-free diagnostic harness, never implementation/history/state/coverage maps/LESSONS entries. B independently reviews public oracle/requirements; C receives the exact frozen accepted tests; D starts after exact passing full local verification and forms assessment before implementation lessons. Preserve inherited advisory coverage and complete native global/per-package/per-platform JSON/HTML integrity, never-imported owned runtime and subprocess coverage. Full-local make verify precedes opening/pushing the stacked PR; Ubuntu24.04/macOS15 CI separately repeat it. No merge/release/reference execution/private upload/Superpowers.
