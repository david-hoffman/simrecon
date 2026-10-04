# Owner MRC observations for conversion intake

**Version 1.0**. Read-only local inspection on September 30, 2026 (America/Los_Angeles). This is evidence, not an approved dialect contract or an executable product test. The owner supplied the local paths in the intake conversation; files and private labels are not copied into this repository or sent to external services.

## Raw acquisition

Owner confirmed: two-dimensional only, no Z acquisition and one channel. The owner subsequently confirmed three phases per orientation in response to the consecutive-group ordering question. Nine stored sections imply three orientations: 9 / 3 = 3. The owner then instructed that this information must come from configuration in the new version, not inferred by the reader. The proposed config records orientation/phase with phase varying fastest for approval. Do not identify the nine stored sections as nine physical Z planes.

| Field | Observed value |
|---|---|
| File SHA-256 | `f733b05673efbaca84ed4beb4974ca7ec504702bb64f71ff26fc1bb712f60666` |
| Main-header SHA-256 | `f61237f952966f5bc9c194d4f290689bfdf1f8f59d889045ec72c5697b9cb6d5` |
| Byte order | Little endian; opposite-endian decoding produces inconsistent dimensions and mode |
| Stored columns/rows/sections | 1024 / 1024 / 9 |
| Pixel mode | 6, interpreted as unsigned 16-bit |
| Legacy identifier | Signed 16-bit -16224 at zero-based offset 96 |
| Main-header size | 1024 bytes |
| Extended-header size | 0 bytes |
| Physical file size | 18,875,392 bytes |
| Interval/grid fields | 1 / 1 / 1 |
| Spatial fields at offsets 40–51 | 0.09749999642372131 / 0.09749999642372131 / 0 |
| Spatial axis mapping | 1 / 2 / 3 |
| Channel/time counts | 1 / 1 |
| Header image sequence | 0; this does not identify phase/orientation ordering |
| First wavelength field | 520; semantic role not established by the filename's illumination wavelength |
| Header density statistics | 0 / 0 / 0; inconsistent with decoded pixels |
| Integer/float extension-record fields | 0 / 2, despite zero actual extension bytes |
| Minimum/maximum over decoded planes | 141 / 35843 |

Payload sanity check: `1024 × 1024 × 9 × 2 = 18,874,368 bytes`; plus the 1024-byte header equals the actual file size exactly. Each selected unsigned plane is 2 MiB. There are no trailing bytes. Pixels above 32767 demonstrate that signed-16 decoding would be wrong. Extension-record descriptors alone must not invent an extension when its actual length is zero.

Plane evidence from independent standard-library decoding (`struct.iter_unpack('<H', ...)`) in 64 KiB blocks:

| Stored plane | Minimum | Maximum | Integer pixel sum | Payload SHA-256 |
|---|---:|---:|---:|---|
| 0 | 141 | 26423 | 2127195538 | `9396355c6dacf9aa1cae3462132aabbd042cbf0b49c1b1d3b4be8cb252b04533` |
| 1 | 211 | 28690 | 2137549710 | `9d8388eafb755f8e2c50d05b26414af32d35c4d99adb333bef5666910c45920b` |
| 2 | 204 | 26691 | 2108021698 | `33d05587131361f08669ba61c520136a3d2e6917fd986860ec9786dbc09ef739` |
| 3 | 250 | 35843 | 2514542513 | `433e073181cbfc731ac3d8fb78c7a7beb0df03185020bf5fedf2e586899f7d01` |
| 4 | 233 | 34563 | 2479814181 | `df2297f739c9e4b829a57d76bbcc85f7fa683edfd417a73f08763c98731ae883` |
| 5 | 235 | 34249 | 2447874927 | `5205126944abbf46dda324063d5526e7aeeee86c1e2210e6ccd2e6c5624d3fdd` |
| 6 | 214 | 35294 | 2494700032 | `c4139dfb97c5f6a3b8762c5dd07975d5ff46ba88c95f703f5de8f79a605bcd5c` |
| 7 | 210 | 35311 | 2497410130 | `dfa4045ab9c21f2db794166772619eb11d8a82f9e0c973af6d464a18e6c26a09` |
| 8 | 216 | 34411 | 2463994448 | `e29e4981d1d9cdb0dade1050fb97dd255e01842e78cad26c44d1a2a566b548a3` |

Each plane contains 1,048,576 pixels. File size and modification timestamp were unchanged across the read. This is inspection evidence; stat checks are not an engineered protection against concurrent modification.

## Processed example

The owner first supplied a processed companion, then accepted the processed-versus-raw distinction and supplied the raw path. The processed file remains useful for conversion of legacy floating-point output, not as reconstruction truth.

- SHA-256: `9c1a726a57591d3f27af30c761a73bc2907e409d5bb66e246626dfacaccc9de3`.
- Main-header SHA-256: `ddf7862a9ff1fd63db9b426254a8429cdee872552c6ac4d1bc052be91a59506a`.
- Big-endian mode 2; 2048 × 2048 × 1 stored plane; one channel and time; legacy identifier -16224; no extended header.
- File size 16,778,240 bytes = `1024 + 2048 × 2048 × 4`; 4,194,304 decoded floats, all finite; range -406.0350646972656 to 9767.46484375.
- Spatial fields: 0.04874999821186066 / 0.04874999821186066 / 0; grid 1 / 1 / 1; mapping 1 / 2 / 3.
- Private labels contain a processing command with three phases, three directions and a twofold zoom. These are provenance observations; they do not independently define raw plane ordering.
- Read using standard-library `struct.iter_unpack('>f', ...)` in 64 KiB blocks. File size and modification timestamp were unchanged.

## Consequences for the proposed contract

Demonstrated input candidates are legacy identifier -16224, modes 6 and 2, both byte orders, identity spatial mapping and no actual extended header. This does not establish other modes, axis permutations, compression, arbitrary Priism variants or extended-header semantics. Keep independently constructed asymmetric byte fixtures alongside owner-file conservation checks; successful round trips alone cannot establish correctness.

No Z acquisition means the raw logical axes should be orientation/phase/y/x under explicit orientation/phase configuration, with one channel declared separately. A stored MRC section count is not a physical Z count. Spatial metadata units still require an explicitly documented profile or owner confirmation. Both examples have grid values one, so neither distinguishes direct-spacing from cell-length-divided-by-grid conventions. Axial sampling is absent, not zero distance between acquired Z planes.

Proposed modern output must define the missing-axial-scale policy visibly. Although [mrcfile documentation](https://mrcfile.readthedocs.io/en/stable/source/mrcfile.html) describes positive dimensions, [inspection of the pinned validator source](mrc-output-compatibility.md) establishes that it accepts zero cell dimensions. The revised proposal keeps zero/unknown axial scale and explicitly preserves no-Z acquisition metadata. Actual output compatibility still requires reviewed tests; no measured axial sampling is invented.

Header/image sequence describes channel/time interleaving, not SIM phase/orientation order, as already observed in [legacy study](legacy-mrc-observations.md). Require that ordering in acquisition configuration before harmonization, even for this known sample. The [MRC2014 specification](https://www.ccpem.ac.uk/mrc-format/mrc2014/) defines modern modes and main-header scaling; preserve original header bytes and metadata in the project's eventual extension rather than reusing incompatible legacy fields unchanged.
