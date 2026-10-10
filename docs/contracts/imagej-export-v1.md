# IMAGEJ-EXPORT-01: every illumination setting in a Fiji copy

**Version 1.0.** Git versions revisions. On October 9, 2026 the owner selected “make a fiji friendly copy” and “all settings” under the continuing-roadmap instruction. This concrete record requires no second document-approval checkpoint.

## Outcome and source

Export one single-file, scalar, uncompressed, little-endian OME-BigTIFF containing every orientation/phase pair. Each pair becomes a separate named OME Image/reader series with actual X/Y/Z/channel/time. Never relabel setting axes as acquired Z, channel or time. The pinned all-series ImageJ importer returns one ImagePlus per setting in deterministic order.

Input is the existing harmonized file-source DatasetInfo from [MRC conversion v1](mrc-conversion-v1.md): regular uncompressed Priism spatial images, mode 6 uint16 or mode 2 float32, either source byte order and identity spatial mapping. Reuse public inspect/harmonize/read semantics. Modern MRC input, caller-array/reconstruction-result export, irregular mappings, complex/RGB data, inferred physical angles, custom viewer plugins and numerical correction are separate scope. Existing MRC conversion and its full original-byte retention guarantee remain unchanged.

This is a viewing copy with complete logical/interpreted metadata and source-referenced opaque metadata. The original file remains required to recover opaque extension bytes. Do not describe the copy as a standalone original-metadata archive. Do not modify source or existing destinations.

## Public interface

```python
export_imagej(destination: str | Path, info: DatasetInfo, *, block_planes: int = 1) -> ImagejWriteReport
```

Export these value records from simrecon:

- ImagejSeries: index (int), name (str), orientation_index (int or None), phase_index (int or None), shape (tuple T,C,Z,Y,X). None identifies an absent source axis; a declared singleton has index 0.
- ImagejWriteReport: destination (Path), series (tuple of ImagejSeries), series_count (int), planes_written (int), provenance (tuple of change mappings), limitations (tuple of strings).

Require harmonized info, config present, data_kind spatial_image, canonical resolved axes and supported mode. Preserve documented public argument types/ordinary filesystem exceptions. Do not mutate descriptor, caller config or arrays. Scope handles; create no persistent process/viewer/session. Product export requires Python dependencies, not Java/Fiji.

```text
simrecon export-imagej SOURCE DESTINATION --config CONFIG.json [--block-planes N]
```

Compose exactly export_imagej(destination, harmonize(inspect(source), config=config), block_planes=N). Successful UTF-8 JSON stdout contains all report fields and series records. Domain/config/usage errors retain existing JSON code/message stderr and exit 2; OS I/O uses io_error and exit 1; success exits 0. Expected errors have no source-bearing traceback, telemetry or network call. Existing commands retain behavior.

## Axis and plane mapping

Retain complete original axis declarations/singletons in metadata. For the OME carrier alone define absent T/C/O/P/Z counts as 1; X/Y are columns/rows. An absent Z has SizeZ=1 without physical Z. A declared singleton Z has SizeZ=1 with known physical Z. Retain the distinction even when viewer defaults cannot express it.

For O orientations and P phases, S=O*P series, orientation slowest and phase fastest. Zero-based s=o*P+p. An absent setting axis has record index None and name token absent; declared singleton indices are 0. Exact series name: `orientation=<index-or-absent>; phase=<index-or-absent>`. These ordinals assign no physical angle or phase offset.

Each series has SizeX=X, SizeY=Y, SizeZ=Z, SizeC=C, SizeT=T, DimensionOrder=XYCZT. Scalar channels have SamplesPerPixel=1 and stable names `channel=<c>`. Do not infer wavelength roles/colour calibration; retain generic wavelengths in project metadata.

Each series has N=T*Z*C image planes, with zero-based n=c+C*(z+Z*t). Consecutive nonoverlapping IFD ranges follow series order. Explicit TiffData maps every IFD to its series/z/c/t; no missing, excess, duplicate, thumbnail, pyramid or auxiliary image planes. IFD means Image File Directory.

Canonical source-plane index with absent sizes factored as 1 is `((((t*C+c)*O+o)*P+p)*Z+z)`. Resolve it through approved public read, regardless of source storage order. Every source pixel appears once at corresponding series/t/c/z/y/x. Sanity check: O=2,P=3,T=2,C=2,Z=3 gives S=6,N=12, hence72 planes, equal to source plane-size product. Examples impose no scenario cap.

## Pixels, scale and limits

Emit a real BigTIFF header version43/64-bit offsets at every file size. First IFD ImageDescription contains UTF-8 OME-XML namespace http://www.openmicroscopy.org/Schemas/OME/2016-06, complete all-series metadata and single-file mappings. No companion/external pixels, compression, prediction, quantization, resampling, autoscaling or lossy encoding. TIFF types are unsigned16/IEEE float32; OME Type uint16/float.

File and independent raw-reader pixels preserve every decoded source bit after endian normalization, including unsigned values above32767, float32 signed zero, infinities and NaN payloads. ImageJ primitive pixels preserve unsigned/finite values, infinity sign, signed zero and NaN classification. JVM float transfer may change NaN payload/signalling details; document that viewer limit instead of weakening file/raw preservation. JVM means Java Virtual Machine.

PhysicalSizeX/Y use explicit resolved sampling in micrometres with unit µm. PhysicalSizeZ appears only for actual declared Z. Emit no TimeIncrement, physical timestamp/angle or inferred origin. Sizes are finite/positive, serialized as decimal preserving supplied binary64 values; JSON retains precise resolved floats. Independent raw-reader/unit-normalized ImageJ scale tolerances are derived by A and reviewed by B from binary64 serialization/unit conversion, not an invented scientific accuracy target.

OME dimensions, per-series plane count and series count must be positive signed32 integers. Each uncompressed XY plane byte count must fit signed32 Java reader indexing. Physical sizes must also round to finite positive IEEE float32, because OME PositiveFloat derives from XML Schema float: reject zero-underflow/overflow rather than clamp. Total offsets/counts fit unsigned64 BigTIFF fields. These are format/index limits, not heap-capacity promises. Stable new domain code: imagej_unrepresentable. Full binary64 sampling remains in JSON when representable.

Missing/unresolved config, invalid/unsupported source mode/kind/layout, source change and invalid block sizes retain existing conversion error meanings. block_planes is a positive integer, excluding bool; invalid values use invalid_block_size. Structurally valid unsupported input remains inspectable but cannot export. Opaque fields gain no interpretation/units. Exact error prose is not contractual.

## Recoverable copy metadata

Attach one MapAnnotation to every Image, Namespace org.simrecon.imagej-copy, key metadata_json. Its Value is the same finite UTF-8 JSON object for the complete acquisition, sorted keys/compact separators. Required project object fields are exactly:

- schema=org.simrecon.imagej-copy, integer version=1, data_kind=spatial_image.
- logical_axes/logical_shape: complete canonical resolved source axes/shape including declared singletons/settings.
- source_layout: plane_axes, plane_shape, byte_order, pixel_mode; stored_shape: section/row/column.
- sampling_um, wavelengths_nm, acquisition_config, file_metadata, unresolved, provenance: source/resolved public values with every override, including equal-value overrides; retain existing IEEE-byte/unresolved representations for nonfinite undecoded fields, never JSON NaN/Infinity.
- source_identity: source_name (basename only), source_size, source_mtime_ns, header_sha256; no private absolute path.
- original_header_base64: recoverable exact1024 original main-header bytes.
- original_extension: schema none/opaque, bytes exact length, sha256 of exactly source bytes [1024,1024+length) including empty-byte digest, content_retained false. Hash/length cannot recover omitted bytes.
- series_layout: series_order orientation_phase, plane_order XYCZT, series_count, per_series_shape [T,C,Z,Y,X], orientation_count, phase_count, and booleans orientation_present, phase_present, z_present, channel_present, time_present.

Factored series_layout/names identify all settings without a per-plane acquisition lookup table. Metadata is independently recoverable from the file; no promise arbitrary annotations become visible ImagePlus properties. Every report's limitations explicitly disclose omitted opaque source bytes, absent-Z/time viewer defaults, ordinal setting labels, JVM NaN payload limits and the pinned importer path. No new custom binary metadata container is required.

## Integrity, destinations and resources

Check source size/mtime/main-header SHA256 against descriptor before any payload/extension access and at success. Mismatch yields source_changed with no successful report. Hash opaque extension in bounded chunks. These checks/digest do not guarantee an atomic snapshot or detect same-size/same-timestamp concurrent payload edits.

Create destination exclusively. Never truncate/replace/modify existing paths, including source-equal. Retain ordinary FileExistsError/OSError. Domain validation before creation leaves no destination. A later source/I/O/encoding failure yields no success; a partial newly created destination may remain for the caller to discard. No atomic publication/crash durability or automatic user-file deletion. Clean owned scratch only.

Pixel working memory is O(block_planes*X*Y*itemsize) plus bounded per-plane encoding scratch, independent of acquisition pixel count. No whole-acquisition allocation/mmap. TIFF-directory/OME metadata memory may grow with plane/series count; disclose this rather than claiming constant total memory. Hash opaque bytes in chunks. No throughput, viewer heap or large-volume latency guarantee. Reader acceptance uses finite public fixtures within available memory;64-bit offsets do not guarantee all data fits viewer RAM.

## Route, evidence and ownership

High risk applies: binary representation, metadata interpretation, new public/file interface, overwrite safety and custom interoperability oracles. Fresh native blind A creates independently assembled public source fixtures/formulas. Fresh native B audits legitimate alternatives, permitted positives, missing outcomes and exact oracles before checkpoint acceptance. Restricted C implements named files only. Fresh native D forms independent assessment before author narratives and permanently excludes ALL LESSONS payloads before every read/hash. Prompt restrictions are not engineered access controls.

Pin Bio-Formats8.5.0 and ImageJ1.54p acquired from official versioned locations with authenticated SHA256, Java21.0.7 development runtime with actual vendor/platform recorded. Use independent raw OMETiffReader bytes/OME metadata plus real BF.openImagePlus(ImporterOptions) objects. Explicit all-series/grayscale/Hyperstack/XYCZT; disable concatenation/splitting, crop/ranges/swap/grouping/autoscale/updater; quiet/windowless with isolated recorded preferences. Verify every setting/dimension/coordinate/pixel/scale/name/annotation. An external-writer round trip, startup or metadata-only probe is not product evidence. No private owner data required.

Separate bounded reader/dependency/check setup supplies locked tifffile2026.9.20, exact reader inputs, Java identity, source-free diagnostics and CI maintenance. Fresh independent infrastructure review precedes dependent roles; setup does not pre-approve product oracles. [Environment instructions](../operations/imagej-reader-environment.md) identify executable inputs/commands.

A owns tests/test_imagej_export.py, tests/imagej_export_fixture.py, tests/imagej_export_reader.java; B reports only. C owns src/simrecon/_imagej.py, optional split helpers _imagej_metadata.py/_imagej_write.py, src/simrecon/__init__.py, src/simrecon/_cli.py, docs/usage/imagej-export.md, docs/reports/imagej-export-interop.md. C cannot edit tests/fixtures/snapshots, dependencies, workflows, discovery/coverage, skills/policy or unrelated interfaces. Root owns contract/task/PROJECT/roadmap bookkeeping and native launches. D reports only. Formal roles requested gpt-6.1-sol/high with memory/delegation disabled; served attribution/metering unknown when unavailable.

Inherit PROJECT's approved behavior coverage/independent risk review; native statement/branch percentages advisory, no selected threshold. Preserve full measurement integrity/global/package/platform/subprocess scope and all gates. Full local exact-candidate make verify before any PR (draft included); complete configured CI platform/event and artifact/source/input provenance before a dependent successor. No merge/release. Human numeric limits not set. Timeouts mean incomplete evidence and erase no attempts/charges.

## Scenario inventory

A independently maps obligations/risk to tests/examples; B audits. Equivalent values add coverage, not meaning. Initially passing inherited-code outcomes are valid.

| ID | Distinct outcome/boundary | Expectation/examples |
|---|---|---|
| IJ01 | API/records/CLI composition | Public types/report/error exits; actual file-source entry. |
| IJ02 | Every setting exactly once | Series/count/names; unequal O/P and absent/singleton setting axes. |
| IJ03 | Actual X/Y/C/Z/T | Unequal sizes, nonsquare/asymmetric pixels, differing source orders. |
| IJ04 | Absent versus singleton actual Z | Carrier1, physical Z omitted/present, JSON declarations. |
| IJ05 | Other absent/singleton axes retained | Carrier plus original identity for channel/time/settings. |
| IJ06 | Complete plane/IFD order/coverage | Source/output formulas, no lost/duplicate/extra planes. |
| IJ07 | Unsigned uint16 | Both byte orders, >32767, raw bytes/ImageJ. |
| IJ08 | Float32 bits/viewer meaning | Finite/signedzero/infinities/NaNs and payload limitations. |
| IJ09 | BigTIFF single file | Header43,64-bit structures, full OME, no external data. |
| IJ10 | Explicit physical scale | X/Y/actualZ, units, raw-reader/ImageJ calibration. |
| IJ11 | Unknown time/angles/origin/wavelength role stay unknown | No inferred scientific values. |
| IJ12 | Complete logical/interpreted metadata/provenance | JSON/header bytes/equal overrides, no private absolute path. |
| IJ13 | Opaque identity/failure/resource meaning | none/opaque length/hash, omission disclosure, empty/nonempty. |
| IJ14 | Valid source/block inputs accepted | Regular supported Priism, no new acquisition-count defaults. |
| IJ15 | Invalid/unresolved/unsupported source rejected | Existing codes, paired valid positives, no success. |
| IJ16 | Invalid block size | Zero/negative/noninteger/bool versus valid positive. |
| IJ17 | Dimension/plane/offset representability | Signed32/unsigned64 limits and permitted nearby cases. |
| IJ18 | Scale representability | Float32 positivefinite versus underflow/overflow; no clamp. |
| IJ19 | Source changed before access | Size/mtime/header digest, no success. |
| IJ20 | Source changed before completion | No false report; concurrency limitations disclosed. |
| IJ21 | Existing/source-equal destination preserved | Ordinary I/O failure, exact prior bytes unchanged. |
| IJ22 | Pre-creation domain validation | No new destination. |
| IJ23 | Operation-time I/O/encoding failures | Honest error, partial new file permitted, scratch cleanup. |
| IJ24 | Source/caller/previous public behavior preserved | No mutation/write or unrelated regression. |
| IJ25 | Streamed pixels/chunked opaque hashing | No full pixel allocation/mmap; directory/metadata growth disclosed. |
| IJ26 | Actual pinned raw-reader evidence | Every series/coordinate/bit/metadata and input identities. |
| IJ27 | Actual pinned ImageJ all-settings evidence | Separate objects/profile/names/CZT/calibration/primitive pixels. |
| IJ28 | Metadata survives viewer limitations | JSON/OME facts distinguish absence/defaults; no GUI-property claim. |
| IJ29 | CLI/docs match library | Success/errors/all-series usage and limitations. |

Expected results come from this contract, approved public MRC behavior, [OME mapping](https://ome-model.readthedocs.io/en/stable/ome-tiff/specification.html), [structured annotations](https://ome-model.readthedocs.io/en/stable/developers/structured-annotations.html), [pinned OMETiffReader](https://raw.githubusercontent.com/ome/bioformats/v8.5.0/components/formats-bsd/src/loci/formats/in/OMETiffReader.java), [pinned ImagePlusReader](https://raw.githubusercontent.com/ome/bioformats/v8.5.0/components/bio-formats-plugins/src/loci/plugins/in/ImagePlusReader.java), and independent coordinate/bit invariants. Sources are not executed compatibility. [Task pointer](../tasks/imagej-adapter-intake.md) locates exact outside-tree checkpoint/candidate/results/accounting.
