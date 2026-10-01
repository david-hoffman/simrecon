# MRC conversion public contract — proposal 1

**Version 1.0**. Proposal 1 approved at `a3808d545659556a024b70dca2dae1dc6238a32b`; actual approval and execution accounting are recorded in [the single Current state](../tasks/architecture-intake.md#current-state). [Task and scenario table](../tasks/mrc-conversion.md) govern execution. This contract proposes the missing architecture choices together with one bounded first conversion task. It approves no scientific processing.

## Architecture and scope

Functional Python with NumPy, using the installed Python 3.13/uv environment. Retain SciPy for later approved work. Independently author the bounded legacy and modern codecs from this contract and applicable format references; do not import, link, wrap, copy or ship the legacy implementation. Use pinned `mrcfile==1.5.4` as a development-only modern-reader/validator reference and `h5py==3.16.0` for a genuine HDF5 metadata container inside the MRC extended header. HDF5 here stores metadata only; pixel blocks remain ordinary MRC data. Native HDF5/h5py internals are external dependencies, not owned code; all new Python wrappers remain measured owned runtime.

The first task supports uncompressed, rectangular Priism-style spatial images with identifier -16224, modes 6 (unsigned 16-bit) and 2 (IEEE 32-bit float), both byte orders, identity column/row/section mapping, and exact declared payload length. The owner examples establish a little-endian mode-6 raw file and big-endian mode-2 processed companion. Independent byte fixtures establish the other two combinations. It does not claim every historical Priism/IVE dialect. Other modes, spatial-axis permutations, complex/frequency-domain calibration, irregular acquisition mappings, scientific metadata decoding from extensions, compressed files and modern-input decoding are later tasks. Modern output is documented and independently readable from this task.

The architecture retains separate responsibilities for image intake, metadata intake, future algorithm-parameter intake and output. OTF calibration remains a distinct future frequency-domain category; ordinary conversion does not require it. The separate reconstruction placeholder remains outside this task and is never called by conversion. The public records are values; file handles and scratch buffers remain scoped resources within calls. No scheduler, plugin registry or processing-session class.

## Acquisition configuration

Phase/orientation counts and plane ordering come from explicit configuration, never a filename or algorithm defaults. Stored sections alone do not establish physical Z. The owner confirms that the representative raw file is 2D, single channel, with three phases per orientation. Nine planes therefore describe three orientations. Read the answer to the ordering question as consecutive groups of three phases; record that interpretation in the proposed config for approval.

Canonical JSON config for the owner raw sample:

```json
{
  "version": 1,
  "data_kind": "spatial_image",
  "plane_axes": ["orientation", "phase"],
  "plane_shape": [3, 3],
  "spatial_fields": "direct_um",
  "extended_header": "none",
  "overrides": {}
}
```

`plane_axes` is slowest-to-fastest source-plane order. The final listed axis varies fastest. Axis names are unique members of time/channel/orientation/phase/z; x/y are the within-plane axes and cannot appear here. Counts are positive integers and their product must equal stored section count. Empty plane axes/shape describe one 2D plane. Explicitly declared singleton axes remain named; undeclared singleton channel/time values are retained as acquisition metadata. Counts have no acquisition-specific fixed maximum; MRC signed-32-bit storage fields and actual file length bound representability.

Phase and orientation indices are ordinal labels; this conversion assigns no phase angles, physical orientation angles or reconstruction defaults. Canonical internal/output axis order is time/channel/orientation/phase/z/y/x, retaining only declared plane axes and the spatial y/x axes. A source with phase/orientation order can be reordered to orientation/phase without changing any pixel value. The first config is a regular rectangular mapping; irregular mappings require a later contract.

`spatial_fields: direct_um` explicitly interprets legacy fields at zero-based offsets 40/44/48 as micrometre sampling values, not MRC2014 cell lengths. This is a proposed profile convention for owner approval, not a guessed unit. Other conventions require explicit canonical sampling overrides or a later profile; do not infer them from value magnitudes. X/Y sampling must resolve to finite positive values. Z sampling is required only when an actual z axis is declared; for 2D it is null.

`extended_header` is `none` when the actual extension length is zero, or explicitly `opaque` to preserve nonzero bytes without interpreting fields. Omitting this declaration for nonzero extension bytes blocks harmonization. Neither integer/float record counts nor plausible values identify an extension schema. Zero extension length takes precedence over stale record-count fields.

Optional `overrides` accepts `sampling_um` (x/y/z values in micrometres) and `wavelengths_nm` (channel-index string to wavelength in nanometres). Explicit values win over file metadata and every supplied override is recorded, including a supplied value equal to the file value. Unknown wavelength semantics remain generic wavelength metadata; do not replace a header wavelength using an illumination wavelength parsed from a filename. Unknown fields, invalid JSON, unsupported config versions and invalid shapes are errors. Unknown spatial-field conventions may be used only when all required sampling values are supplied as explicit canonical overrides. No scientific algorithm parameters are introduced in this conversion config.

No input changes the pixel dimensions or repairs truncated bytes. The header channel/time declarations are retained; configured counts take precedence when those axes are explicitly declared, with recorded old/new provenance and payload-product validation.

## Public Python responsibilities

Exports from `simrecon`:

```python
inspect(source: str | Path) -> DatasetInfo
harmonize(info: DatasetInfo, *, config: Mapping[str, object]) -> DatasetInfo
read(info: DatasetInfo, *, plane_start: int, plane_stop: int) -> DataBlock
write(destination: str | Path, info: DatasetInfo, *, block_planes: int = 1) -> WriteReport
```

Returned value-record fields are public:

- `DatasetInfo`: `source` (Path), `source_size` (int), `source_mtime_ns` (int), `header_sha256` (str), `original_header` (bytes), `stored_shape` ((section,row,column)), `pixel_mode` (int), `stored_dtype` (uint16/float32 or None for unsupported modes), `data_kind` (spatial_image after config, otherwise None), `byte_order` (little/big), `extended_header_bytes` (int), `file_metadata` (mapping), `unresolved` (tuple of strings), `axes` (tuple of names), `shape` (tuple of counts), `config` (mapping or None), `sampling_um` (x/y/z mapping, float or None), `wavelengths_nm` (sparse channel-index mapping), `provenance` (tuple of change mappings). Inspected axes are section/y/x until resolved; harmonized axes/shape follow the canonical logical layout. `config is None` identifies an unresolved descriptor; no open handles or processing cache.
- `file_metadata` includes `grid`, `spatial_fields`, `map_axes`, `time_count`, `image_sequence`, `channel_count`, `wavelength_slots`, `extension_integer_fields`, and `extension_float_fields`. Original bytes retain other fields. Nonfinite undecoded values are represented with their IEEE bytes/unresolved status when serialized; no nonstandard JSON NaN/Infinity metadata.
- `DataBlock`: `data` (NumPy ndarray), `info` (resolved DatasetInfo), `plane_indices` (range), `coordinates` (tuple of mappings from declared plane-axis names to ordinal indices). No physical angles are inferred from those indices.
- `WriteReport`: `destination` (Path), `stored_shape` (tuple), `pixel_mode` (int), `planes_written` (int), `provenance` (tuple of change mappings), `limitations` (tuple of strings).

Export the three record types alongside the functions and error type. Functions treat metadata as values and snapshot caller-supplied config/overrides; caller-owned arrays/config are never mutated. Returned metadata is read-only by convention; no deep-immutability claim for NumPy buffers. Public Python arguments follow the documented types; arbitrary object protocols/cyclic configuration are outside this task. CLI configuration is finite, acyclic JSON.

`inspect` reads the 1024-byte header and checks the file description without reading pixel payload or materializing opaque extensions. It reports source byte order, pixel mode, stored shape (section,row,column), file values, extension length, unknown acquisition order/schema and source identity (path, size, modification time in nanoseconds, header digest). A valid but unsupported mode can be inspected; selected reads/conversion reject it. Invalid or truncated structural headers fail explicitly. No modern-input reader is promised in this task.

`harmonize` is pure: it validates configuration against the description, resolves named axes/shape and sampling, applies explicit overrides, and returns a new descriptor with provenance. It does not open files, mutate the input record/config, decode pixels or apply image correction. Unresolved required ordering or extension policy blocks harmonization. The original main-header bytes and file metadata are retained.

`read` requires a harmonized descriptor and an explicit nonempty half-open canonical-plane interval `[plane_start, plane_stop)`, with `0 <= start < stop <= section_count`. It reads only those planes, applying the factored source mapping. Its `DataBlock.data` is an owned C-contiguous native-endian NumPy array with shape (selected planes, y, x) and dtype uint16 or float32. `plane_indices` and per-plane named coordinates identify every pixel's logical position; the full resolved descriptor accompanies the block. Flat block storage does not erase logical axes. A returned array remains valid after file closure. Caller selection controls its allocation; there is no default full-acquisition read.

`write` streams the full resolved dataset to a new destination, in canonical plane order. It returns output location, dimensions, mode, planes written, changes and reader limitations. `block_planes` is a positive integer controlling the working set, not acquisition dimensions. Python callers can inspect/read selected data independently; array-source output adapters are a subsequent contract. That does not introduce a stateful engine or change the future common model.

Source size, modification time and header digest must match the inspection descriptor before reads/writes, and at write completion. A mismatch is `source_changed`; no successful report is returned. These checks do not guarantee detection of concurrent same-size/same-timestamp payload edits. Pixel values are not modified, filtered, rescaled or reconstructed. Uint16 values above 32767 stay unsigned. Float32 bit patterns, including signed zero and nonfinite values, survive byte-order changes exactly; no floating-point arithmetic is performed on pixels.

Conversion retains at most the chosen block plus bounded encoding/reordering scratch: pixel working memory is O(block_planes × x × y × itemsize), independent of total acquisition count. Opaque metadata is copied in bounded byte chunks; the logical-plane mapping is factored by axes/counts, not an all-plane lookup table. A source with large acquisition counts must not trigger a whole acquisition allocation or mmap resident-set growth. No throughput or whole-volume reconstruction memory promise.

## Command-line interface

```text
simrecon inspect SOURCE
simrecon convert SOURCE DESTINATION --config CONFIG.json [--block-planes N]
```

The inspect result and successful conversion report are UTF-8 JSON on stdout. Inspection may report unknown layout/schema. Conversion follows precisely `write(destination, harmonize(inspect(source), config=config), block_planes=N)`. No implicit reconstruction, calibration input or acquisition defaults. CLI reports the same stable domain error code/message to stderr as JSON and exits 2 for domain/config/usage errors, 1 for operating-system I/O errors, 0 on success. Ordinary expected failures have no source-bearing traceback. Config files are local inputs; no network calls or telemetry.

`SimreconError` derives from `ValueError` and exposes string `code` and human-readable `message`. Stable codes: invalid_header, unsupported_format, unsupported_mode, unsupported_axes, payload_size, config_required, config_invalid, layout_mismatch, schema_required, sampling_required, invalid_selection, invalid_block_size, source_changed, header_unrepresentable. Exact prose is not contractual. Filesystem failures retain ordinary `OSError` subclasses for Python callers; the CLI wraps their text with code `io_error`. An existing destination is never overwritten, including when it is the source. Write failures produce no successful result; a partial newly created destination may remain for the caller to discard. No atomic-publication or crash-durability guarantee.

## Legacy subset: byte expectations

All offsets below are zero based. The main header is 1024 bytes. Select byte order by the signed 16-bit identifier -16224 at offset 96; no matching interpretation is unsupported_format. Structural fields use the selected order: int32 columns/rows/sections/mode at 0/4/8/12; int32 grid at 28/32/36; float32 spatial fields at 40/44/48; int32 spatial mapping at 64/68/72; int32 extension byte length at 92; int16 time/sequence/channel fields at 180/182/196; five int16 wavelength slots at 198 through 206. Remaining bytes are preserved verbatim, not silently assigned new meanings.

Positive stored dimensions, nonnegative extension size and exact total length are required. Payload begins at 1024 + extension size. Mode 6 uses two-byte unsigned pixels and mode 2 four-byte IEEE floats. File length must equal header + extension + x × y × sections × itemsize. No trailers or truncated payload are accepted. Spatial mapping must be 1/2/3. Source image sequence is retained but does not supply SIM ordering. Interpretation derives from the reviewed config and [owner observations](../architecture/owner-mrc-observations.md), with the [publisher's republished Priism table](https://pypi.org/project/mrc/) marked secondary historical evidence. No claim that header declarations alone establish other dialects.

## Modern output and extension v1

Use little-endian MRC2014 version 20141, mode 6 or 2 matching decoded pixels, identity MAPC/MAPR/MAPS and `MAP ` signature. NX/NY are pixel dimensions; NZ is the canonical stored-plane count. Write an image stack with ISPG 0, MX=NX, MY=NY, MZ=1, orthogonal angles and zero start/origin fields. Original start/origin fields remain in retained source bytes; no independently verified world-coordinate interpretation is asserted.

`CELLA.x = NX × sampling_x_um × 10000`, and similarly for Y, rounded once to float32. One micrometre is 10000 angstroms. For the supplied raw file this encodes approximately 97.5 nm/pixel. Resolved JSON metadata retains the original precise decoded sampling; independent reader header-derived lateral scale must agree within relative tolerance 1e-6. If a header value cannot be represented as a positive finite float32, fail with header_unrepresentable. Pixel comparisons have zero tolerance.

Set CELLA.z to zero, explicitly unknown/nonphysical axial scale for the flattened image-stack view. Declare it in one main-header label and the extension; never label the raw nine sections as acquired Z. The pinned validator source accepts zero cell dimensions, although its prose documentation describes them as positive; [compatibility evidence](../architecture/mrc-output-compatibility.md) records that discrepancy. An actual logical z axis and its sampling, when configured, live in the extension; generic readers still see flattened sections. Density statistics are marked undetermined using DMIN=0, DMAX=-1, DMEAN=-2, RMS=-1; do not carry forward stale source statistics or scan pixels during inspection. The output header has little-endian machine stamp 44 44 00 00, one contiguous ASCII label `SIMrecon stack; axial scale unknown; see HDF5 metadata`, and otherwise zero unused fields.

The source is [CCP-EM MRC2014](https://www.ccpem.ac.uk/mrc-format/mrc2014/); independent validation uses [mrcfile 1.5.4](https://mrcfile.readthedocs.io/en/stable/source/mrcfile.html). These references establish base-format fields, not automatic recognition of our acquisition metadata.

EXTTYP is `HDF5`, an agreed base-format extension type, and the actual extension is a valid HDF5 file image. Our project schema inside it remains project-defined; registration of the container type does not standardize the acquisition schema. A private four-letter tag would fail the pinned validator's known-type check, so do not emit it or mislabel arbitrary bytes with an agreed type.

The single HDF5 container has exactly these datasets:

- `/simrecon/metadata_json`: one-dimensional uint8 bytes encoding UTF-8 JSON, with no terminator or BOM.
- `/simrecon/original_header`: one-dimensional uint8, exactly 1024 bytes, original main header verbatim.
- `/simrecon/original_extended_header`: one-dimensional uint8, original extension bytes verbatim; length zero when absent. Large opaque content is copied through bounded chunks, not loaded as one array.

Use a standalone HDF5 file image with its signature at byte zero, no external links/storage/filters, and no dependencies on files outside the output. Stage the container in a scoped temporary disk file; stream it into the MRC extension. Clean up scoped scratch resources. Zero-pad to a multiple of four bytes when needed; NSYMBT includes the complete container plus padding and must fit its signed-32-bit storage field. Independent h5py extraction of exactly the MRC extended bytes must recover all datasets. No deterministic HDF5 file-byte identity is promised across library/platform versions; dataset contents/schema are contractual.

Preserve opaque source extension bytes in source-plane order. The JSON source/output factored layout describes correspondence after pixel reordering. Neither opaque fields nor their units are reinterpreted. [HDF5-backed files](https://docs.h5py.org/en/stable/high/file.html) and [chunked dataset access](https://docs.h5py.org/en/stable/high/dataset.html) establish the container/storage mechanisms; the three dataset names and metadata schema above are our proposed contract.

JSON object fields: `schema` = `org.simrecon.mrc-metadata`; `version` = 1; `data_kind` = `spatial_image`; `logical_axes`; `logical_shape`; `source_layout` (plane_axes, plane_shape, byte_order, pixel_mode); `output_layout` (canonical plane_axes/plane_shape, section_count); `sampling_um` (x/y/z); `wavelengths_nm` (sparse channel-index mapping); `acquisition_config`; `provenance`; `main_header_axial_scale` = `unknown_flattened_stack_zero_angstrom`; `original_extension_schema` = none/opaque. Serialize as finite JSON with sorted keys, compact separators and no BOM. The config plus interpreted source metadata are O(number of axes + explicitly supplied metadata); preserving opaque bytes is streamed. Every provenance entry identifies field, old value or unresolved state, new value and source (`config` or `override`). Original bytes retain otherwise unrepresentable values exactly. The HDF5 extension is documented storage; a generic reader skipping it sees pixels but cannot recover named acquisition axes by itself.

## Expected results and interoperability

Synthetic fixtures are independently assembled from the byte offsets above and a declared coordinate-to-pixel formula, with nonsquare planes, unsigned values above 32767, both endiannesses, and explicit differing source orders. Never generate their expected bytes using the new codec. A/B receive this public contract, not implementation or implementation-bearing status.

Canonical tests use these shareable fixtures. Owner-file checks additionally compare every decoded pixel and saved original header/extension against the untouched local input; do not commit, upload or require private owner files in CI. The processed companion is conversion evidence, not reconstruction ground truth.

First demonstrated current-reader support is pinned mrcfile 1.5.4: pixels, row/column order, plane count, lateral scale and strict base-format validity. ImageJ/Bio-Formats recognition is a later integration check: the local Java launcher presently has no runtime, and no owner ImageJ reader/version has been established. [Bio-Formats format support](https://bio-formats.readthedocs.io/en/stable/formats/mrc.html) documents vendor-extension limits, but source documentation is not a tested installed-reader result. Approval of this contract explicitly accepts this initial reader boundary; do not claim ImageJ has been tested. Full ImageJ X/Y/Z/channel/time interpretation and phase/orientation display remain planned adapter/integration work.
