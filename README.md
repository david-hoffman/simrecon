# SIMrecon

**A Python library for structured illumination microscopy (SIM) files and explicit numerical stages.**

`reconstruct_workflow` reconstructs explicit specimen arrays or declared
acquisitions with raw bead calibration or accepted complex transfer tables.
It composes acquisition preparation, finite carrier/modulation fitting and
per-time native filtering/assembly. The result contains the signed image,
coordinates in micrometres, resolved settings and actual stage records. Callers supply
the required acquisition and optical metadata. Neutral file reading and
declaration remain explicit.

The individual numerical stages remain available for callers who need direct
control. They follow the selected retained C mathematics: preparation/separation,
empirical transfers, complex sampling, finite parameter search and image assembly.
The earlier scientific APIs remain retired. The
[C-equivalence roadmap](docs/plans/c-equivalence-roadmap.md) defines the sequence;
historical C executable agreement and physical image recovery remain unqualified.

## What you can use today

| Capability | Public entry points | Limits |
|---|---|---|
| Inspect and read acquisition files | `inspect`, `read` | Supported Priism-style MRC sources and selected blocks; explicit layout configuration. |
| Resolve metadata and convert files | `harmonize`, `write`; `simrecon inspect`, `simrecon convert` | Preserve pixels and declared metadata in modern MRC output. No scientific correction, reconstruction or modern-MRC input decoding. |
| Declare an acquisition array | `declare_acquisition` | Own a bit-preserving array and explicit acquisition metadata. Declaration estimates no scientific parameters. |
| View all illumination settings in Fiji | `export_imagej`; `simrecon export-imagej` | A supported Priism acquisition becomes an OME-BigTIFF viewing copy. OME means Open Microscopy Environment. Keep the original for opaque metadata recovery. |
| Prepare specimen phase bands | `prepare_bands` | Explicit camera/phase settings and the selected C preprocessing map. Feeds estimation and filtering. |
| Prepare empirical bead transfers | `prepare_bead_otf` | Explicit bead/acquisition settings, accepted safe geometries and the selected C preparation path. |
| Declare and sample complex transfers | `declare_otf`, `sample_otf` | Complete radial/full tables, explicit frequency sampling and actual safe interpolation stencils. |
| Estimate carriers and modulation | `estimate_parameters` | Accepted declared 2D/3D bands, explicit initial vectors and optics. Finite source procedure, per-time factors and full immutable diagnostics. |
| Filter and assemble with supplied parameters | `reconstruct_known` | Accepted bands/transfers, supplied carriers/modulation, explicit optics and positive Wiener parameter. Signed image and coordinates; no parameter fitting. |
| Prepare selected acquisition modes | `prepare_acquisition_bands`, `reinterpret_2d_planes` | Explicit 2D/3D, phase and drift policies, off exposures and literal plane-stream adaptation within their contracts. |
| Reconstruct an explicit acquisition | `reconstruct_workflow` | Explicit raw/calibration declarations and supported transfer inputs; signed image, coordinates, settings and diagnostics. |
| Develop and verify the package | `delivery doctor`, Make commands below | Delivery tools and their verification gates remain installed. |

The retained library functions are `inspect`, `read`, `harmonize`, `write`,
`declare_acquisition` and `export_imagej`, with their required records and errors.
The new scientific entries are described in the [specimen preparation guide](docs/usage/c-preparation.md),
[empirical transfer guide](docs/usage/c-optical-transfer.md),
[carrier/modulation guide](docs/usage/c-parameter-estimation.md),
[known-parameter guide](docs/usage/c-known-reconstruction.md),
[acquisition-mode contract](docs/contracts/c-equivalence-acquisition-modes-v1.md), and
[public workflow guide](docs/usage/c-workflow.md). The retired
`prepare_otf` name and old private module remain unavailable.
Historical scientific guides and comparison reports remain evidence of their
original models and observed failures. Their old commands do not run in the
current package; a historical passing result is not proof of C equivalence.

## Software boundaries

This is a **conceptual CE02–CE07 boundary diagram**, not a numerical result:

```mermaid
flowchart TD
    Source["Supported Priism source"] --> Read["Explicit read and declare_acquisition"]
    Read --> Values["Specimen arrays or RawAcquisition"]
    Values --> Workflow["reconstruct_workflow with explicit configuration"]
    Beads["Explicit raw bead calibration"] --> Workflow
    Tables["Accepted or explicitly decoded complex transfer"] --> Workflow
    Workflow --> Transfer["Select actual transfer; prepare beads when selected"]
    Workflow --> Bands["prepare_acquisition_bands"]
    Bands --> Estimate["estimate_parameters: finite carrier/modulation procedure"]
    Transfer --> Estimate
    Estimate --> Known["reconstruct_known once per effective time"]
    Bands --> Known
    Transfer --> Known
    Known --> Image["Signed image, coordinates and actual stage records"]
    Source --> Neutral["inspect / harmonize / write / export_imagej"]
    CLI["Neutral file CLI"] --> Neutral
    Neutral --> Copies["Selected pixels / modern MRC / OME-BigTIFF"]
```

`inspect` describes a source without loading its pixels. `read` loads selected
blocks. `harmonize` resolves metadata and layout from explicit configuration.
`declare_acquisition` copies and labels caller arrays. The file writers stream a
described source into a conversion or viewing copy. These file and metadata operations perform no
scientific image correction or reconstruction. The separate scientific array
stages follow their own explicit contracts. Estimated parameters have a time
axis. The workflow performs the accepted per-time composition; callers can also
construct one-time bands explicitly as shown in the carrier/modulation guide. Records hold values rather than
open file handles; NumPy buffers are not deeply immutable.

The [project record](docs/PROJECT.md), [library design](docs/architecture/library-design.md)
and [data flow](docs/architecture/data-flow.md) describe the active boundaries.
Concrete behavior comes from the public contracts, beginning with
[MRC conversion](docs/contracts/mrc-conversion-v1.md).

## Get started

The project targets **Python 3.13**. Its development environment uses
**Python 3.13.12** and **uv 0.12.19**, with dependencies pinned by `uv.lock` and
one isolated `.venv` per worktree.

```sh
git clone https://github.com/david-hoffman/simrecon.git
cd simrecon
uv sync --locked --all-groups
uv run --locked simrecon --help
```

Use the [conversion contract and configuration examples](docs/contracts/mrc-conversion-v1.md),
[acquisition declaration guide](docs/usage/raw-acquisition-declarations.md) and
[Fiji export guide](docs/usage/imagej-export.md). Do not infer phase, orientation
or Z ordering from a flattened stack. The [environment guide](docs/operations/environment.md)
covers development setup and prerequisite checks.

## Rebuild sequence

The [replacement roadmap](docs/plans/c-equivalence-roadmap.md) supersedes the old
RA scientific execution plan. CE01 removes incompatible scientific components
and their stale tests while retaining neutral I/O, historical evidence and all
accepted Agentic Software Delivery (ASD) improvements. CE02 supplies specimen
preprocessing/separation; CE03 supplies empirical transfer preparation/sampling.
CE04 supplies known-parameter filtering and assembly. CE05 supplies the finite
carrier/modulation procedure and explicit per-time composition. CE06 supplies the selected acquisition modes, layout and geometry/filter
extensions. CE07 composes them through the explicit public workflow. Independent
recovery acceptance follows in CE08.

Mathematical equivalence permits declared invertible representation and unit
conversions. It does not permit a different estimator or data-dependent fitted
normalization to conceal disagreement. Bitwise agreement is not required.
The [common contract](docs/contracts/c-equivalence-common-v1.md) governs each stage.
No replacement stage is available merely because it appears in the roadmap.

## Development and verification

From the repository root:

```sh
make preflight  # Locked setup, interpreter/import and build-tool health
make check      # Locked setup, lint, formatting and type checks
make verify     # Full tests, coverage reports, wheel/import checks and audit
```

`make verify` remains the full local exact-candidate gate. It runs pytest with
exactly two workers using pinned pytest-xdist 3.8.0 and execnet 2.1.2, deterministic
whole-file grouping and no automatic worker restart. Nested fixture tests retain
their serial commands. Every required phase, test omission guard, report, wheel,
import and vulnerability audit remains required. The retained MRC conversion
measurement M25 must export same-run evidence and satisfy its unchanged
**33,554,432-byte (32 MiB)** memory-increment limit.

Full checks include Fiji reader interoperability tests. They require a Java
Development Kit (JDK) **21.0.7** with source-file launching; `SIMRECON_JAVA` selects
the executable. Setup authenticates and caches pinned ImageJ/Bio-Formats jars.
See the [reader environment guide](docs/operations/imagej-reader-environment.md).
The library's file conversion and Fiji export do not require Java.

Continuous integration repeats full verification independently on Ubuntu 24.04
and macOS 15. Native statement and branch coverage are measured globally and per
owned package; percentages are advisory. Complete current reports and exact
native integers remain required. See the [project policy](docs/PROJECT.md),
[verification guide](docs/operations/verification.md) and [AGENTS.md](AGENTS.md).

## Historical context

The [migration history](docs/MIGRATION-ROADMAP.md) and
[scientific context](docs/SCIENTIFIC-CONTEXT.md) preserve earlier claims and limits.
The Python implementation is independently written. Local legacy source under
`SIMrecon_svn/` is ignored, unshipped study material. Source study and comparison
with owner-provided outputs are permitted; building, running, linking or importing
the C reference or bundled executables remains prohibited.
