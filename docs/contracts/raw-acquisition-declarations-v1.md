# Raw acquisition declarations v1

**Version 1.0.** Authorized R1 declaration foundation under the October 10, 2026 roadmap continuation. The coordinator selects this independent structural foundation within the requested raw array/metadata work. Actual target 3D acquisition settings remain unresolved; this contract neither requires nor supplies them. It does not close full phase 2 or authorize scientific correction/calibration. [Task](../tasks/raw-acquisition-declarations.md).

## Public boundary

Export from simrecon:

```python
declare_acquisition(data, *, config, original_metadata=None) -> RawAcquisition
```

The operation is pure in-memory layout/declaration preparation. It returns one complete value record or raises. It performs no file I/O, phase estimation, correction, calibration, reconstruction, intensity arithmetic, resampling or automatic composition. Existing conversion/separation/viewing interfaces are unchanged.

Public RawAcquisition fields:

- data: owned C-contiguous plain NumPy ndarray in canonical axis order; same dtype including byte order and exactly preserved per-element storage bytes.
- axes: tuple of canonical names; source_axes and source_shape: tuples retaining the input declaration and shape.
- acquisition_kind: specimen_sim, detection_psf or sim_beads.
- sampling_um: dict with x/y/z keys, each binary64 float or None.
- wavelengths_nm: sparse dict from canonical decimal channel-index strings to positive binary64 floats; wavelength roles remain unspecified.
- nominal_phases_rad: owned C-contiguous float64 ndarray in nominal_phase_axes order, or None; nominal_phase_axes is a tuple, empty when commands are absent.
- intensity_unit, acquisition_id, calibration_id: declared strings or None.
- original_config and original_metadata: independent snapshots of the supplied values; original_metadata defaults to an empty dict.
- provenance: tuple of independent dicts with field, old, new and source entries.

Records/metadata are read-only by convention. Returned buffers are mutable; no deep-immutability promise. Input/config/metadata storage is preserved on success and rejection. Outputs and their metadata snapshots do not share mutable storage with callers. No promise covers concurrent external mutation. There is no whole-volume memory bound: this array operation owns one full sample copy plus ordinary metadata/scratch. The streaming MRC memory guarantee remains attached to its separate file API.

## Explicit array layout and kind

Data must be a plain ndarray, not a subclass/masked array/list. Dtype kind is i/u/f, any width and either byte order. Bool/complex/object/string/structured/datetime are rejected. Signed values, all floating bit patterns including NaNs/infinities/signed zero, read-only/strided/Fortran arrays and singleton dimensions are valid raw samples. There is no scientific float64 conversion of samples. Exact per-element storage bytes include wider floating storage/padding; do not perform floating assignment/arithmetic that changes those bytes.

Config axes is a list of unique names, one per data dimension. All dimensions are positive; at least y/x exist. The last two names must be y,x in that order; preceding names are unique members of time/channel/orientation/phase/z in any order. Source axes denote increasing ndarray dimension order, slowest-to-fastest for C-order indexing. Canonical result retains only declared axes, ordered time/channel/orientation/phase/z/y/x. No omitted dimension is inserted. In particular absent z differs from an explicitly declared singleton z; channel/time never become phase/z.

Specimen_sim and sim_beads require explicit orientation and phase axes, including when their counts are one. Detection_psf forbids orientation/phase and permits only time/channel/z before y/x. These are supported declaration profiles, not proof of correct labeling or valid experimental pairing. Any positive declared phase/orientation count is valid here, including counts or repeated commands that cannot identify a downstream numerical model. Known-phase numerical kernels retain their own rank/count requirements and are never invoked here.

Irregular/ragged layouts and extra switch-off/I2M exposure axes are unsupported. A caller must not silently label extra exposures as phase/z. The operation cannot detect false caller declarations; it makes no experimental validation claim. Ordinary no-extra orientation/z/phase and z/orientation/phase layouts are both supported explicitly.

For canonical coordinates c, the matching source element is data at indices c[source_axes[0]],...,c[source_axes[-1]]. The result element has identical stored bytes. This named-coordinate identity is the independent mapping expectation, not a reference-C algorithm. Nonsquare independently labeled coordinate arrays distinguish transposed/flattened outcomes; comparisons are exact.

## Config and metadata schema

Config is an acyclic Mapping[str, object] with version=1 (plain integer, bool excluded), acquisition_kind and axes required. Unknown top-level keys are errors. Optional fields are sampling_um, wavelengths_nm, nominal_phases_rad, intensity_unit, acquisition_id, calibration_id, overrides. Config declarations use built-in dict/list/tuple/string/bool/int/float/None values (original numeric values may be nonfinite when a valid explicit override replaces them); no arbitrary object protocols, cyclic graphs or NumPy arrays. Snapshot original_config before applying overrides. Source metadata supplies no implicit config values.

Sampling_um is absent/None or a mapping containing only x/y/z. Missing entries/None remain unknown. Present numbers are plain int/float excluding bool; convert once to binary64 and require finite positive represented values. No source unit/magnitude inference or cell-length conversion. Supplied values explicitly mean micrometres. If z is absent from axes, a non-None z sampling is contradictory and rejected; declared z may have unknown sampling. Canonical unknown x/y/z values are None, never zero/default distances.

Wavelengths_nm is absent/None or a mapping. Missing/None means empty sparse metadata. Keys are canonical decimal strings 0,1,... without signs/leading zeros, within the declared channel axis count; when channel is absent, the single unindexed group uses key0. Values are plain int/float excluding bool, converted once to finite positive binary64. No excitation/emission/color assignment is inferred. Unknown roles remain unknown. Generic header wavelengths may be supplied explicitly without adopting a scientific role.

Nominal_phases_rad is absent/None or a rectangular nested built-in list/tuple of numeric leaves. For a SIM kind, its source dimension order is source_axes excluding z,y,x, with exactly the matching time/channel/orientation/phase dimensions. Every leaf is a plain int/float excluding bool, converted once to finite binary64 without modulo reduction/principal interval restriction. All group dimensions are required: there is no implicit broadcasting/sharing across orientation/channel/time. Reorder to canonical group-axis order and own the float64 result; nominal_phase_axes reports that order. Detection_psf requires commands absent/None. These are commanded values, never measured phases/known truth or automatic inputs to a separator. Partial/unknown commands may instead remain opaque in original_metadata; a partially supplied resolved command tensor is rejected.

Intensity_unit, acquisition_id and calibration_id are absent/None or nonempty strings (preserve text exactly; whitespace-only strings are allowed opaque text). Units are declared labels; no detector-count/photoelectron conversion. IDs are opaque labels, not validation of calibration pairing/reuse, bead properties or reference settings.

Original_metadata is absent/None or an acyclic Mapping with string keys and nested built-in dict/list/tuple/str/bool/int/float/bytes/None values. Nonfinite floats and opaque bytes are preserved as supplied values and never interpreted. Snapshot recursively, preserving list versus tuple and bytes. NumPy arrays/custom objects are outside this supported metadata domain and rejected. Cyclic graphs/arbitrary protocols are outside this contract. File metadata/header bytes may be supplied here explicitly; preservation covers supplied metadata only, not a claim of complete archive or decoding opaque extensions.

## Overrides and provenance

Overrides is absent or a mapping whose keys are only sampling_um, wavelengths_nm, nominal_phases_rad, intensity_unit, acquisition_id, calibration_id. It cannot change version/kind/axes. Each supplied field replaces that whole field; nested mappings are not merged. Overrides may replace None or even an invalid original declaration with a valid resolved value; validation of these fields applies to the final effective value. Original structural version/kind/axes and overall config/override schema are always validated. Invalid effective fields are rejected.

For every explicitly supplied top-level declaration except version/overrides, append a provenance entry with field=name, old=None (unresolved), new=the independent supplied value snapshot, source=config. For axes/kind this is the original source declaration. For every explicit override append field=name, old=the original supplied value or None when absent, new=the override supplied value, source=override. Preserve equal-value overrides and absent-to-None overrides. Record supplied values before binary64 normalization/canonicalization; normalized resolved fields live separately in the returned record. Order entries deterministically: initial declarations in lexicographic field-name order, then overrides in lexicographic field-name order. Snapshots within provenance, original_config and resolved metadata are independently owned. Nothing interprets opaque original metadata or infers a missing declaration.

## Failures and representation

Use SimreconError stable codes below; exact prose and simultaneous-error precedence are unspecified. Ordinary argument-binding TypeError remains.

| Obligation rejected | Code |
|---|---|
| Data is not a plain ndarray | invalid_acquisition_data |
| Sample dtype outside i/u/f | invalid_acquisition_dtype |
| Rank/count mismatch or nonpositive shape | invalid_acquisition_shape |
| Invalid/duplicate/unknown axes, missing/nonterminal y/x | invalid_acquisition_axes |
| Unknown acquisition kind or incompatible kind-axis profile | invalid_acquisition_kind |
| Missing/invalid version/config/schema/override key/optional string | invalid_acquisition_config |
| Invalid effective sampling or z contradiction | invalid_acquisition_sampling |
| Invalid effective wavelength key/count/value | invalid_acquisition_wavelengths |
| Invalid effective command tensor shape/type/value or PSF commands | invalid_acquisition_phase_commands |
| Original metadata outside supported built-in domain | invalid_acquisition_metadata |

Unrepresentable binary64 metadata values, including huge-int conversion overflow or positive values rounded to zero, receive their corresponding field error. Do not reject nonfinite pixel samples. Allocation MemoryError and unrelated exceptions propagate unchanged, with no successful partial result. Preserve caller NumPy error mode; metadata conversions emit no arithmetic RuntimeWarning for handled range errors and suppress no unrelated warning categories. No numeric solver or solver tolerance is involved.

## Compatibility and execution scope

Existing MRC inspect/harmonize/read produce explicitly resolved named axes and owned canonical flat-plane blocks. A full explicitly requested read can be reshaped using its descriptor shape and passed with descriptor axes to this operation; that read remains caller-selected, with no new default full-volume I/O. The caller supplies acquisition kind and declared physical metadata independently; generic header wavelengths remain generic. Supply original header bytes/file metadata/provenance as original_metadata if desired. No conversion schema/codec/CLI change or modern-input decoder is added. A synthetic asymmetric file example must independently label coordinates before passing through the existing public conversion API and this new public declaration API. Private data/paths are not needed in tests, CI or published usage.

A owns tests/test_raw_acquisition_declarations.py and optional tests/raw_acquisition_fixture.py only. C owns src/simrecon/_acquisition.py, src/simrecon/__init__.py additive exports, docs/usage/raw-acquisition-declarations.md only. C cannot edit frozen tests/fixtures, dependencies, workflows/discovery/coverage, skills/policy or unrelated interfaces. Coordinator owns this contract and docs/tasks/raw-acquisition-declarations.md. Fresh native A/B/C/D use Sol/high, with memory/delegation disabled; A/B use source-free diagnostics and public-input allowlists. Astra advice replaces no role. Inherited percentages remain advisory, native report integrity and make verify exact candidate remain mandatory. Actual target O1–O4/S2 and later correction/calibration meaning remain pending. No Superpowers/legacy execution/private upload/merge/release.
