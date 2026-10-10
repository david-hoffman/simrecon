# Open all illumination settings in Fiji

`export_imagej` makes one uncompressed, little-endian OME-BigTIFF viewing copy. OME means Open Microscopy Environment. Every orientation/phase pair becomes a separate series. Each series retains the actual time, channel, Z, Y and X dimensions. Settings never become acquired Z planes or time points.

Use a regular, uncompressed Priism spatial-image source with uint16 mode 6 or float32 mode 2, either byte order, and identity spatial mapping. Supply an explicit acquisition configuration through the existing `inspect` and `harmonize` interfaces. Modern MRC files, arrays, reconstruction results, irregular mappings, complex and RGB data are outside this adapter. Export performs no scientific processing and requires no Java or Fiji runtime.

The following configuration is the executed public uint16 fixture: source plane order phase/Z/time/orientation/channel, counts 3/3/2/2/2, and X=5, Y=3. Its source supplies positive direct micrometre sampling. Change these declarations to match your acquisition; they are not scientific defaults.

```json
{
  "version": 1,
  "data_kind": "spatial_image",
  "plane_axes": ["phase", "z", "time", "orientation", "channel"],
  "plane_shape": [3, 3, 2, 2, 2],
  "spatial_fields": "direct_um",
  "extended_header": "opaque",
  "overrides": {}
}
```

Save it as `config.json`, then run:

```sh
simrecon export-imagej independent.priism copy.ome.tif --config config.json --block-planes 2
```

Or use the Python interface:

```python
import json
from pathlib import Path
from simrecon import export_imagej, harmonize, inspect

config = json.loads(Path("config.json").read_text(encoding="utf-8"))
info = harmonize(inspect("independent.priism"), config=config)
report = export_imagej("copy.ome.tif", info, block_planes=2)
print(report.series_count, report.planes_written)  # 6, 72 for this fixture
```

There are 2 × 3 = 6 series and 2 time points × 2 channels × 3 Z planes = 12 planes per series: 6 × 12 = 72 source planes. Series order is orientation slowest, phase fastest. Within each series, channels vary fastest, then Z, then time. The first name is `orientation=0; phase=0`; the last is `orientation=1; phase=2`. Labels are zero-based ordinals, without physical angles or phase offsets. An absent setting axis is labelled `absent`; a declared singleton is labelled `0`.

Success returns `ImagejWriteReport`, including `ImagejSeries` records with shape `(T,C,Z,Y,X)`, provenance and limitations. The command prints the same report as UTF-8 JSON and exits 0. Domain, configuration and usage errors print JSON to stderr and exit 2; operating-system errors use `io_error` and exit 1. Carrier limits use `imagej_unrepresentable`; invalid blocks use `invalid_block_size`. The destination must be new. Existing files, directories, symlinks and the source itself are never replaced.

## Fiji importer options

The measured development path uses Bio-Formats 8.5.0 and ImageJ 1.54p. Choose **Plugins > Bio-Formats > Bio-Formats Importer**, then select the copy. The official loading guide explains why using the explicit importer avoids another TIFF reader. [Bio-Formats loading instructions](https://bio-formats.readthedocs.io/en/v8.5.0/users/imagej/load-images.html).

Select **Open all series**, **Grayscale**, **Hyperstack** and **XYCZT**. Here C is channel, Z is focal plane and T is time point. Keep concatenation, channel/Z/time splitting, cropping, ranges, dimension swapping, file grouping, tile stitching, virtual stacks and autoscaling off. Keep metadata/OME-XML/ROI display off for the tested profile. The development observer also uses Local machine, quiet/windowless operation, isolated preferences, disabled updater, disabled pattern IDs and thumbnails, and ungrouped files. Those observer settings produced separate actual ImagePlus objects for every setting; they do not require running the GUI windowlessly. [Pinned importer options](https://raw.githubusercontent.com/ome/bioformats/v8.5.0/components/bio-formats-plugins/src/loci/plugins/in/ImporterOptions.java).

If options are skipped, use **Bio-Formats Plugins Configuration**, select the applicable reader on **Formats**, and uncheck **Windowless**. [Official plugin configuration guidance](https://bio-formats.readthedocs.io/en/v8.5.0/users/imagej/features.html). Menu and option guidance comes from official documentation and authenticated pinned resources. No graphical user interface was executed. This guide makes no claim about current-branch-only dialog disabling or series-chooser thresholds.

## What the copy preserves and what it omits

The first TIFF directory contains complete OME2016-06 XML, explicit single-file plane mappings and a shared `org.simrecon.imagej-copy` MapAnnotation attached to every image. Its finite JSON preserves complete source/resolved axes and singletons, precise sampling, generic wavelengths, configuration, original file metadata, unresolved representations and every override, including equal-value overrides. It also retains the exact 1024-byte main header as base64, source basename/size/modification time/header digest, and opaque extension length/SHA256. Arbitrary annotations are recoverable from the file; they need not appear as ImagePlus properties.

Opaque extension **content is omitted**. Its digest cannot recover those bytes. Keep the original source to recover opaque metadata; this viewing copy is not a standalone original-metadata archive. An empty extension has the empty-byte digest and no omitted content. Opaque declarations gain no new interpretation or units.

Explicit X/Y sampling, and Z sampling only when Z is declared, use micrometres. Decimal XML preserves supplied binary64 values; JSON retains those values too. An absent Z uses SizeZ=1 without physical Z. Viewer depth defaults establish no acquired or physical Z. Declared singleton axes remain declared. No measured time interval, timestamp, origin, angle, phase offset or wavelength role is invented. Viewer time defaults establish no acquired time when the time axis is absent and no measured timing when it is present.

TIFF and independent raw-reader pixels retain every decoded source bit after endian normalization, including uint16 values above 32767, signed zero, infinities and float32 NaN payloads. ImageJ preserves unsigned/finite values, infinity sign, signed zero and NaN classification. Java Virtual Machine (JVM) float transfer may change NaN payload or signalling details. Display contrast is separate from stored pixels; this profile supplies no floating-point display-range guarantee.

OME dimensions, series and per-series plane counts, and XY plane bytes must fit positive signed32 limits. Physical sizes must round to positive finite float32, without clamping. BigTIFF uses 64-bit offsets even for small files; offsets/counts must fit unsigned64. These limits do not guarantee sufficient viewer memory.

The writer uses one-plane selected public reads, within the positive `block_planes` upper bound, and bounded encoding/hash scratch. It never allocates or maps the full acquisition. TIFF directory and OME metadata memory grows with planes and series. There is no constant-total-memory, viewer heap, latency or throughput promise.

Source size, modification time and main-header digest are checked before payload/extension access and at completion. This is not an atomic snapshot and cannot detect every same-size/same-timestamp concurrent payload edit. Failures return no successful report. A partial newly created file may remain for you to discard; export promises no automatic deletion, atomic publication or crash durability. See the [actual interoperability evidence](../reports/imagej-export-interop.md) for tested inputs and limits.
