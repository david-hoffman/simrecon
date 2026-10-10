# Raw acquisition declarations

`declare_acquisition` prepares an owned array and explicit metadata in memory.
It preserves every sample's storage bytes while ordering only the declared
axes as time/channel/orientation/phase/z/y/x. It adds no absent dimensions.
The [authorized contract](../contracts/raw-acquisition-declarations-v1.md)
defines the supported declarations and stable error codes.

This is a declaration foundation for structured illumination microscopy (SIM).
It does not establish experimental correctness or reconstruction readiness.
Actual target 3D acquisition settings remain unresolved; this boundary does not
close full phase 2. Physical correction, calibration, phase estimation and
scientific parameter selection require their own approved inputs and operations.
The numbers below are synthetic labels, not proposed instrument settings or
scientific tolerances.

## Declare a synthetic array

This executable example labels coordinates before declaration. Its source order
is z/orientation/phase/y/x; its result order is orientation/phase/z/y/x.

```python
import numpy as np
from simrecon import declare_acquisition

source_axes = ("z", "orientation", "phase", "y", "x")
source = np.empty((2, 2, 3, 2, 5), dtype=">i4")
for z, orientation, phase, y, x in np.ndindex(source.shape):
    source[z, orientation, phase, y, x] = (
        1000 * z + 100 * orientation + 10 * phase + 5 * y + x
    )

config = {
    "version": 1,
    "acquisition_kind": "specimen_sim",
    "axes": list(source_axes),
    "sampling_um": {"x": 0.125, "y": 0.25, "z": 0.5},
    "wavelengths_nm": {"0": 520},
    "nominal_phases_rad": [[0, 1, 2], [0, 1, 2]],
    "intensity_unit": "synthetic counts",
}
raw = declare_acquisition(
    source, config=config, original_metadata={"note": ["synthetic", b"opaque"]}
)
assert raw.axes == ("orientation", "phase", "z", "y", "x")
assert raw.source_axes == source_axes
assert raw.source_shape == (2, 2, 3, 2, 5)
assert raw.data.shape == (2, 3, 2, 2, 5)
for orientation, phase, z, y, x in np.ndindex(raw.data.shape):
    assert raw.data[orientation, phase, z, y, x] == (
        1000 * z + 100 * orientation + 10 * phase + 5 * y + x
    )
assert raw.data.dtype == source.dtype
assert raw.data.flags.c_contiguous and raw.data.flags.writeable
assert raw.data.flags.owndata and not np.shares_memory(raw.data, source)
assert raw.nominal_phase_axes == ("orientation", "phase")
assert raw.nominal_phases_rad.tolist() == [[0, 1, 2], [0, 1, 2]]
source.fill(-1)
assert raw.data[1, 2, 1, 1, 4] == 1129
print("synthetic declaration OK")
```

Supported kinds are `specimen_sim`, `sim_beads` and `detection_psf` (detection
point-spread function). The two SIM kinds require explicit orientation and phase
axes, even for singleton counts. Detection PSF forbids those axes. Every positive
count is valid at this boundary; downstream numerical kernels retain their own
identifiability requirements. Extra switch-off/I2M exposure axes and ragged
layouts are unsupported. A declaration cannot detect falsely labeled exposures.

Samples must be a plain NumPy array of integer or floating dtype. Signed and
nonfinite samples, arbitrary strides, reversed/read-only/Fortran storage and
either byte order are supported. Samples undergo no floating conversion or
intensity arithmetic, including when storage contains wider-float padding.

Sampling is explicitly in micrometres, with unknown x/y/z entries left as `None`.
Non-`None` z sampling requires a declared z axis. Wavelengths are sparse positive
binary64 values in nanometres, indexed by canonical decimal channel strings;
without a channel axis only `"0"` is valid. Generic wavelengths identify no
excitation/emission role. Nominal phases are complete finite binary64 command
tensors in source group-axis order, excluding z/y/x. They are not measured
phases or known optical truth, are not reduced modulo a period, and are not
automatically passed to a separator. Partial commands can remain opaque metadata.

Optional unit and acquisition/calibration IDs are opaque nonempty strings or
`None`. IDs prove no calibration pairing. Opaque metadata never supplies missing
declarations. Config uses an acyclic mapping root with built-in dict/list/tuple
and scalar values; original metadata also allows bytes and nonfinite floats.
Custom nested objects and NumPy metadata arrays are outside the supported domain.

## Explicitly compose an MRC read

The separate [MRC conversion API](../contracts/mrc-conversion-v1.md) inspects,
harmonizes and reads caller-selected planes. The following self-contained example
creates an asymmetric synthetic Priism-style MRC file (microscopy image file
format), with independently labeled pixels, then explicitly requests all twelve
planes. It supplies acquisition kind and physical metadata separately to the
declaration. Header/file/provenance values remain opaque snapshots.

```python
import itertools
import struct
import tempfile
from pathlib import Path

import numpy as np
from simrecon import declare_acquisition, harmonize, inspect, read

header = bytearray(1024)
for offset, value in (
    (0, 5), (4, 2), (8, 12), (12, 6),
    (28, 5), (32, 2), (36, 2),
    (64, 1), (68, 2), (72, 3), (92, 0),
):
    struct.pack_into("<i", header, offset, value)
for offset, value in ((40, 0.125), (44, 0.25), (48, 0.5)):
    struct.pack_into("<f", header, offset, value)
for offset, value in ((96, -16224), (180, 1), (182, 0), (196, 1), (198, 520)):
    struct.pack_into("<h", header, offset, value)

payload = bytearray()
expected = {}
for z, orientation, phase, y, x in itertools.product(
    range(2), range(2), range(3), range(2), range(5)
):
    value = 40000 + 1000 * z + 100 * orientation + 10 * phase + 5 * y + x
    payload.extend(struct.pack("<H", value))
    expected[orientation, phase, z, y, x] = value

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "synthetic.mrc"
    original_file = bytes(header) + bytes(payload)
    path.write_bytes(original_file)
    info = harmonize(inspect(path), config={
        "version": 1,
        "data_kind": "spatial_image",
        "plane_axes": ["z", "orientation", "phase"],
        "plane_shape": [2, 2, 3],
        "spatial_fields": "direct_um",
        "extended_header": "none",
    })
    block = read(info, plane_start=0, plane_stop=12)
    raw = declare_acquisition(block.data.reshape(info.shape), config={
        "version": 1,
        "acquisition_kind": "specimen_sim",
        "axes": list(info.axes),
        "sampling_um": {"x": 0.125, "y": 0.25, "z": 0.5},
        "wavelengths_nm": {"0": 520},
    }, original_metadata={
        "header": info.original_header,
        "file": dict(info.file_metadata),
        "provenance": info.provenance,
    })
    assert raw.axes == ("orientation", "phase", "z", "y", "x")
    for coordinate, value in expected.items():
        assert raw.data[coordinate] == value
    assert raw.original_metadata["header"] == bytes(header)
    assert path.read_bytes() == original_file
    assert raw.nominal_phases_rad is None
    saved = raw.data.tobytes()
    block.data.fill(0)
    assert raw.data.tobytes() == saved
    assert raw.data.flags.owndata and not np.shares_memory(raw.data, block.data)
print("explicit MRC composition OK")
```

The synthetic file has `12 × 2 × 5 = 120` samples and `240 bytes` of payload.
Its total size is `1024 + 240 = 1264 bytes`. Real callers must supply their own
resolved ordering and declarations; header magnitudes and filenames establish no
physical settings. Header wavelengths may be explicitly copied as generic
metadata without assigning an optical role. Preservation covers the supplied
metadata, not complete archival capture or opaque extension decoding.

The streaming file API's pixel memory bound depends on the selected block size.
An explicit full read allocates the full block. Declaration then owns a separate
full sample copy plus metadata/scratch; it has no whole-volume memory bound.
It performs no automatic MRC read or composition.

## Overrides, snapshots and failures

`overrides` replaces whole optional fields. For example, replacing
`sampling_um={"x": 1, "y": 2}` with `{"x": 3}` resolves y to unknown, rather
than merging it. An invalid original declaration may be replaced with a valid
one within the supported built-in domain. Version/kind/axes cannot be overridden.

`original_config`, `original_metadata` and each provenance old/new value have
independent mutable-container snapshots. Provenance records raw supplied values
before normalization, including equal-value and absent-to-`None` overrides.
Initial declarations appear in lexicographic field order, followed by overrides
in lexicographic field order. List/tuple distinctions survive snapshots.

Records and metadata are read-only by convention; returned sample and command
arrays remain mutable. Caller storage is preserved on success and rejection.
No promise covers concurrent external mutation. Invalid declarations raise
`SimreconError` with the contract's field-specific code; prose and simultaneous
error precedence are unspecified. Allocation `MemoryError` and unrelated
exceptions propagate. No successful partial record is returned. NumPy error
mode and unrelated warning channels remain unchanged.
