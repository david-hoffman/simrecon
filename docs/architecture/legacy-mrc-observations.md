# Legacy MRC observations for architecture intake

**Version 1.0**. Read-only source study on September 30, 2026. These observations describe the legacy program; they neither specify new behavior nor approve scientific defaults.

## Evidence and limits

The ignored legacy tree is absent from the architecture worktree. The study used `SIMrecon_svn/` in the original checkout. SHA-256 hashes of `sirecon.c`, `sirecon.h`, `helpers.c`, and `IVE/win64/INCLUDE/IWApiConstants.h` matched the [recorded snapshot manifest](../setup/evidence/legacy/snapshot-sha256.json). Source was read, not executed or copied into new runtime code. The [baseline](../setup/BASELINE.md) still applies: no working legacy build or independent product fixture was established. A filename search in the original checkout found no `.mrc`, `.MRC`, or `.dv` examples; this is a search result, not evidence that the owner has no data.

Source locators below identify that snapshot. The installed Priism header is a C declaration, not an independently verified on-disk specification. Reading its fields does not establish byte packing, byte-order handling, or all file variants supported by the external IVE library.

## Observed responsibilities

| Responsibility | Observation | Source locator |
|---|---|---|
| Image/header intake | Reads X/Y dimensions, total section count, channel and time counts, and up to five wavelength fields. Computes logical Z using phase/orientation counts and switch-off exposure counts supplied elsewhere. | `sirecon.c:185–196` |
| Spatial sampling | Treats raw-image `ylen` as lateral sampling and `zlen` as axial sampling, in micrometres. It does not establish that X and Y sampling are always equal. | `sirecon.c:194–196` |
| Parameters | Phase count, orientation count, phase list, layout mode, and many processing settings come from command-line parsing/defaults rather than solely from the image header. Help advertises five phases, while initialized defaults use three. | `sirecon.c:105–120`; `helpers.c:68–104,166–194,503–559` |
| Section ordering | Header carries channel/time interleaving. Separate processing options distinguish Z/orientation/phase versus orientation/Z/phase acquisition order. | `IWApiConstants.h:150–156,276–279`; `sirecon.c:596–603`; `helpers.c:667–668` |
| Extended metadata | The phase-correction path reads timestamp, phase correction in degrees, exposure dose, and X/Y drift. Another path interprets the third extended-header float as background intensity. These are distinct acquisition conventions. Timestamp, dose, and drift units need independent confirmation. | `sirecon.h:97–99`; `sirecon.c:224–269,624–630` |
| Calibration intake | An optical transfer function (OTF) is a separate file. Its spacing fields represent frequency sampling in reciprocal micrometres, with layout dependent on 2D/3D and radial averaging. | `helpers.c:747–809` |
| Image output | Reuses the raw header, changes dimensions/sampling, writes floating-point data, and discards the extended header. This is observed historical behavior, not the requested preservation policy. | `sirecon.c:304–314` |
| Numerical responsibilities | Separates phase components, completes axial transforms for 3D data, estimates/fits pattern parameters, weights bands using OTFs, and assembles output. Some fitted parameters are reused from time point zero. | `sirecon.c:740–759,783–811,944–958` |

## Architectural consequences proposed for approval

Keep file decoding, metadata resolution, and scientific processing separate. Metadata resolution must record original values, explicit overrides, and unresolved fields. A generic MRC decoder does not establish a SIM acquisition layout. Extended-header interpretation needs an identified schema; it must not infer dose versus background from a shared field position. Spatial image data and frequency-domain calibration need distinct semantic contracts.

Harmonization should reorder axes and convert metadata units without applying legacy background subtraction, flat-field correction, camera fixes, rescaling, or reconstruction. Those are scientific operations requiring separate approval. The legacy helper combines reading with those operations (`helpers.c:658–686`); the new boundary should separate them.

For new output, [CCP-EM's MRC specification](https://www.ccpem.ac.uk/mrc-format/mrc2014/) defines a 1024-byte main header, a variable-length extended header, and a data block. Modern `CELLA` fields represent cell dimensions in angstroms; they must not receive legacy micrometre pixel-spacing values unchanged. The owner's selected single-file output therefore needs explicit unit conversion, frame/axis mapping, and a documented extended-metadata schema. A project-specific schema is not automatically an officially registered MRC extension.

The [mrcfile usage guide](https://mrcfile.readthedocs.io/en/stable/usage_guide.html) documents standard header/data access and memory mapping. It is a candidate for modern output, not verified evidence of legacy Priism compatibility. Choose the legacy decoder only after the selected dialect and reference fixtures establish applicability. First-slice contracts must settle supported modes, byte order, metadata mapping, and independent expected results before tests or implementation.
